#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Generate a single combined CSV of synthetic CGM data for all subjects
using a CDISC SDTM SV.xpt (SV domain) as visit boundaries.

Key behaviors
-------------
- Reads SV.xpt and finds a visit window defined by two VISITNUMs: --visit-start, --visit-end.
- For each subject:
  * Picks the visit window [SVSTDTC at start-visit, SVENDTC at end-visit].
  * Chooses the first CGM timestamp at a random time of day in [09:00, 17:00] when feasible.
  * Generates a time series (default 72 hours) at 5-minute intervals, truncated to fit the visit window.
  * Simulates "Historic Glucose" for every timestamp, and "Scan Glucose" at sparse points.
- Writes ONE combined CSV for all subjects.
- The first two rows are a preface row and a header row, exactly as requested.

Simulation model overview
-------------------------
We synthesize realistic CGM-like behavior by combining:
1) Subject-specific baseline (around 100 mg/dL).
2) Circadian modulation (24-hour sinusoid).
3) Meal-related spikes (Gaussian bumps near breakfast, lunch, dinner).
4) Low-amplitude random walk (slow drift) + white noise (short-term variability).
5) Sparse scan points (about 6 per day) where "Scan Glucose" is populated. Elsewhere, only "Historic Glucose" is populated.
6) Clamping to physiologically plausible bounds [60, 260] mg/dL.

Note: This is a **heuristic** model intended for *synthetic demo data*, not a clinical simulator.
"""

import argparse
import csv
import math
import os
import random
import sys
from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

# -----------------------------
# Constants & column definitions
# -----------------------------

DEVICE_NAME = "FreeStyle Libre 3"
SERIAL_PREFIX = "DB14687X-1D25-4A84-8967-"

# Column headers (must match the user's requested schema exactly)
OUTPUT_COLUMNS = [
    "Device",
    "Serial Number",
    "Device Timestamp",
    "Record Type",
    "Historic Glucose",
    "Scan Glucose",
    "Non-numeric Rapid-Acting Insulin",
    "Rapid-Acting Insulin (units)",
    "Non-numeric Food",
    "Carbohydrates (grams)",
    "Carbohydrates (servings)",
    "Non-numeric Long-Acting Insulin",
    "Long-Acting Insulin Value (units)",
    "Notes",
    "Strip Glucose mg/dL",
    "Ketone mmol/L",
    "Meal Insulin (units)",
    "Correction Insulin (units)",
    "User Change Insulin (units)",
]


# -----------------------------
# Utility functions (formatting, parsing, serials)
# -----------------------------

def now_utc_header_string() -> str:
    """Return 'dd-mm-yyyy hh:mm AM/PM UTC' for header row 1, column 3."""
    now_utc = datetime.now(timezone.utc)
    hour12 = now_utc.strftime("%I").lstrip("0") or "12"
    ampm = now_utc.strftime("%p")
    return f"{now_utc.strftime('%d-%m-%Y')} {hour12}:{now_utc.strftime('%M')} {ampm} UTC"


def format_device_timestamp(dt: datetime) -> str:
    """Format timestamps as 'm/d/yyyy h:mm' (no leading zeros for M/D/H)."""
    return f"{dt.month}/{dt.day}/{dt.year} {dt.hour}:{dt.minute:02d}"


def parse_sdtm_datetime(value: str, *, is_start: bool) -> datetime | None:
    """
    Parse SV.SVSTDTC / SV.SVENDTC which can be date-only or full datetime.
    - If date-only:
      * start → assume 00:00:00
      * end   → assume 23:59:59 (common SDTM convention for date-only end)
    - Returns NAIVE datetime (no timezone).
    """
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    s = str(value).strip()
    if not s:
        return None

    dt = pd.to_datetime(s, errors="coerce", utc=False)
    if pd.isna(dt):
        return None

    # Normalize: remove timezone info if present; ensure seconds precision
    if isinstance(dt, pd.Timestamp):
        if dt.tz is not None:
            dt = dt.tz_convert(None)
        # If source was date-only (no "T" or space), set end-of-day for end
        if is_start:
            return dt.to_pydatetime().replace(microsecond=0)
        else:
            if dt.hour == 0 and dt.minute == 0 and dt.second == 0 and ("T" not in s and " " not in s):
                dt = dt + timedelta(hours=23, minutes=59, seconds=59)
            return dt.to_pydatetime().replace(microsecond=0)

    return None


def extract_serial_from_usubjid(usubjid: str) -> str:
    """
    Build the device Serial Number from USUBJID:
      - Take substring after the first hyphen (if no hyphen, use whole string).
      - Strip all hyphens, keep digits only.
      - Left-pad to 12 digits (or keep rightmost 12 if longer).
      - Prefix with 'DB14687X-1D25-4A84-8967-'.
    Example:
      USUBJID = '01-716-1044' → numeric tail '7161044' → '000007161044'
      → 'DB14687X-1D25-4A84-8967-000007161044'
    """
    if usubjid is None:
        usubjid = ""
    s = str(usubjid)
    parts = s.split("-", 1)
    tail = parts[1] if len(parts) > 1 else parts[0]
    digits = "".join(ch for ch in tail if ch.isdigit())
    digits12 = digits.zfill(12)[-12:]
    return SERIAL_PREFIX + digits12


def clamp(x: float, lo: float, hi: float) -> float:
    """Clamp x into [lo, hi]."""
    return max(lo, min(hi, x))


# -----------------------------
# Visit window & start-time selection
# -----------------------------

def pick_start_between_9_and_17(window_start: datetime,
                                window_end: datetime,
                                duration: timedelta):
    """
    Choose a start datetime within [window_start, window_end - duration]
    such that the *time-of-day* is within [09:00, 17:00].

    If the requested duration doesn't fit in the visit window:
      - We shorten the duration to the max possible.
    If we cannot place a start in the 09:00–17:00 band within the window:
      - We fall back to the earliest feasible start and emit a warning.

    Returns: (start_dt, final_duration, warnings_list)
    """
    warns = []

    if window_end <= window_start:
        warns.append("Visit window has non-positive length; using single point at window start.")
        return (window_start, timedelta(minutes=0), warns)

    # Ensure we can fit the full duration; otherwise, reduce it.
    max_duration = window_end - window_start
    if duration > max_duration:
        warns.append(
            f"Requested duration {duration} exceeds visit window {max_duration}. Shortening to fit."
        )
        duration = max_duration

    latest_start = window_end - duration
    if latest_start < window_start:
        latest_start = window_start

    # Enumerate calendar days intersecting the feasible start range, and check
    # whether the 09:00–17:00 band overlaps with that per-day intersection.
    candidates = []
    day_cursor = window_start.replace(hour=0, minute=0, second=0, microsecond=0)
    while day_cursor <= latest_start:
        day_start = day_cursor
        day_end = day_cursor + timedelta(days=1) - timedelta(seconds=1)

        # Intersection with feasible [window_start, latest_start] range
        lo = max(window_start, day_start)
        hi = min(latest_start, day_end)
        if lo <= hi:
            # Reduce to within the 09:00–17:00 band on that day
            tod_lo = max(timedelta(hours=9), lo - day_start)
            tod_hi = min(timedelta(hours=17), hi - day_start)
            if tod_lo <= tod_hi:
                candidates.append((day_start, tod_lo, tod_hi))
        day_cursor += timedelta(days=1)

    if candidates:
        # Randomly choose a calendar day and a random minute in that day's allowed band
        day_start, tod_lo, tod_hi = random.choice(candidates)
        span_minutes = int((tod_hi - tod_lo).total_seconds() // 60)
        offset_minutes = random.randint(0, span_minutes) if span_minutes > 0 else 0
        start_dt = day_start + tod_lo + timedelta(minutes=offset_minutes)
        return (start_dt, duration, warns)

    # Fallback when 09:00–17:00 isn't possible within the window
    warns.append("Could not place start 09:00–17:00 within visit window. Using earliest feasible start.")
    start_dt = min(window_start, latest_start)
    return (start_dt, duration, warns)


# -----------------------------
# Glucose simulation
# -----------------------------

def simulate_glucose_series(timestamps, seed=None):
    """
    Generate synthetic glucose values for the provided timestamps.

    Output:
      - historic_glucose: np.ndarray of floats (mg/dL) for *every* timestamp.
      - scan_glucose:     np.ndarray with NaN for most points, and values only
                          at sparsely chosen "scan" times.

    Model components (additive):
      A) Baseline: subject-specific mean around ~100 mg/dL.
         - Drawn from N(102, 4), which yields subject-level variability.
      B) Circadian rhythm: smooth 24-hour sine wave (amplitude 6–14 mg/dL).
         - Captures lower nocturnal levels and mild daytime elevation.
      C) Meals: 3 Gaussian "bumps" per day near breakfast/lunch/dinner.
         - Centers: ~08:00, ~12:30, ~19:00 with small jitter.
         - Width:    40–70 minutes (spread of post-prandial response).
         - Peak:     +20 to +45 mg/dL above baseline (varied by RNG).
      D) Random walk (drift): small cumulative noise simulates slow sensor/physiology drift.
      E) White noise: short-term variability (sensor noise + physiology).
      F) Clamping: enforce plausible bounds [60, 260] mg/dL.

    Scan points:
      - We mark ~6 scans per day (e.g., user scanning with the phone).
      - "Scan Glucose" at those indices ≈ Historic Glucose ± small noise (σ=1.2).
      - Record Type is 1 when a "Scan Glucose" exists; else 0 (historic).
    """
    rng = np.random.default_rng(seed)
    n = len(timestamps)
    if n == 0:
        return np.array([]), np.array([])

    # Convert to minutes since the first timestamp for continuous-time functions
    t0 = timestamps[0]
    minutes = np.array([(ts - t0).total_seconds() / 60.0 for ts in timestamps])

    # ---- A) Subject baseline ----
    # Mean level around 100 mg/dL with a small between-subject spread.
    baseline = rng.normal(102.0, 4.0)

    # ---- B) Circadian modulation ----
    # 24-hour period sinusoid, amplitude 6–14 mg/dL; phase shift gives lower early-morning.
    circ_amp = rng.uniform(6.0, 14.0)
    circadian = circ_amp * np.sin(2 * np.pi * minutes / 1440.0 - np.pi / 3)

    # ---- C) Meals as Gaussian bumps ----
    # For each day, synthesize three meals with slight timing jitter.
    # We compute the number of days spanned and create centers in minute-space.
    def meal_bump(mins, center_min, width_min=55, peak=35):
        # Gaussian centered at "center_min" with SD ~ width_min, amplitude "peak".
        return peak * np.exp(-0.5 * ((mins - center_min) / width_min) ** 2)

    days_spanned = int(np.ceil(minutes[-1] / 1440.0)) + 1
    meal_centers = []
    for d in range(days_spanned):
        day_offset = d * 1440  # minutes per day
        breakfast = day_offset + 8 * 60 + rng.integers(-20, 20)      # ~08:00 ±20 min
        lunch     = day_offset + 12 * 60 + 30 + rng.integers(-25, 25) # ~12:30 ±25 min
        dinner    = day_offset + 19 * 60 + rng.integers(-30, 30)      # ~19:00 ±30 min
        meal_centers.extend([breakfast, lunch, dinner])

    # Sum up meal bumps—each meal is a Gaussian with randomized width & peak.
    meals = np.zeros_like(minutes)
    for c in meal_centers:
        width = rng.uniform(40, 70)   # minutes: post-prandial spread
        peak  = rng.uniform(20, 45)   # mg/dL: post-prandial amplitude
        meals += meal_bump(minutes, c, width_min=width, peak=peak)

    # ---- D) Random walk (slow drift) ----
    # Very small per-step noise accumulated over time creates a drift behavior.
    rw = np.cumsum(rng.normal(0, 0.06, size=n))

    # ---- E) White noise (short-term variability) ----
    noise = rng.normal(0, 2.2, size=n)

    # Combine all terms to form the "historic" trace
    historic = baseline + circadian + meals + rw + noise

    # ---- F) Clamp to plausible range ----
    historic = np.clip(historic, 60, 260)

    # ---- Scan points selection ----
    # Choose ~6 indices per day spaced across the day.
    # We map 'target minute of day' → nearest 5-minute index (since cadence=5 min).
    minutes_per_day = 1440
    total_days = max(1, int(round(minutes[-1] / minutes_per_day)))
    scans_per_day = 6

    scan_indices = set()
    for d in range(total_days + 1):
        day_start_min = d * minutes_per_day
        for k in range(scans_per_day):
            target = day_start_min + (k + 0.5) * (minutes_per_day / scans_per_day)
            # Index in 5-minute grid (approx). If cadence changes, this approximation
            # still works as long as freq-min divides 1440; otherwise, adjust rounding.
            idx = int(round(target / 5.0))
            if 0 <= idx < n:
                scan_indices.add(idx)

    scan_indices = sorted(scan_indices)

    # Initialize scan array with NaNs (non-scan points remain empty in CSV).
    scan_glucose = np.full(n, np.nan)
    for idx in scan_indices:
        # Scan is "historic ± small noise" to reflect slightly different measurement behavior.
        scan_glucose[idx] = clamp(historic[idx] + rng.normal(0, 1.2), 60, 260)

    return historic, scan_glucose


# -----------------------------
# Row construction per subject
# -----------------------------

def build_rows_for_subject(usubjid: str,
                           window_start: datetime,
                           window_end: datetime,
                           duration_hours: float,
                           freq_minutes: int,
                           seed: int | None = None):
    """
    Build CSV rows for a single subject:
      - Determine feasible start time (preference 09:00–17:00).
      - Generate a timestamp grid (every 'freq_minutes') for up to 'duration_hours',
        truncated to stay within the visit window.
      - Compute synthetic glucose values and map to Record Type:
          * 1 for scan rows (Scan Glucose populated),
          * 0 for historic-only rows.
    """
    # Target duration; may be shortened if the visit window is too small
    duration = timedelta(hours=duration_hours)
    start_dt, final_duration, warns = pick_start_between_9_and_17(window_start, window_end, duration)

    # Build the time grid (inclusive). If final_duration is 0, emit a single timestamp.
    step = timedelta(minutes=freq_minutes)
    if final_duration <= timedelta(0):
        timestamps = [start_dt]
    else:
        n_steps = int(final_duration.total_seconds() // step.total_seconds()) + 1
        timestamps = [start_dt + i * step for i in range(n_steps)]
        # Guard: ensure we do not leak beyond window_end due to rounding
        while timestamps and timestamps[-1] > window_end:
            timestamps.pop()

    # Simulate glucose dynamics for these timestamps
    his, scan = simulate_glucose_series(timestamps, seed=seed)

    # Compute subject's device serial from USUBJID
    serial = extract_serial_from_usubjid(usubjid)

    # Map arrays to CSV rows
    rows = []
    for i, ts in enumerate(timestamps):
        record_type = 1 if (not math.isnan(scan[i])) else 0  # 1=Scan Glucose, 0=Historic

        row = {
            "Device": DEVICE_NAME,
            "Serial Number": serial,
            "Device Timestamp": format_device_timestamp(ts),
            "Record Type": record_type,
            "Historic Glucose": round(float(his[i]), 1) if not math.isnan(his[i]) else "",
            "Scan Glucose": round(float(scan[i]), 1) if not math.isnan(scan[i]) else "",
            # The rest of the columns are intentionally left blank per requirements.
            "Non-numeric Rapid-Acting Insulin": "",
            "Rapid-Acting Insulin (units)": "",
            "Non-numeric Food": "",
            "Carbohydrates (grams)": "",
            "Carbohydrates (servings)": "",
            "Non-numeric Long-Acting Insulin": "",
            "Long-Acting Insulin Value (units)": "",
            "Notes": "",
            "Strip Glucose mg/dL": "",
            "Ketone mmol/L": "",
            "Meal Insulin (units)": "",
            "Correction Insulin (units)": "",
            "User Change Insulin (units)": "",
        }
        rows.append(row)

    return rows, warns


# -----------------------------
# Main routine
# -----------------------------

def main():
    parser = argparse.ArgumentParser(description="Generate a combined CGM CSV using SV.xpt visit windows.")
    parser.add_argument("--sv", default="./360i/data/source/LZZT/sdtm/sv.xpt", help="Path to SV.xpt (SDTM SV domain, SAS XPORT).")
    parser.add_argument("--outfile", default="./360i/data/source/DHT/synthetic_cgm.csv", help="Path to combined output CSV file.")
    parser.add_argument("--visit-start", type=float, default = 1.0, help="Start VISITNUM (e.g., 1.0).")
    parser.add_argument("--visit-end", type=float, default = 2.0, help="End VISITNUM (e.g., 2.0).")
    parser.add_argument("--duration-hours", type=float, default=72.0, help="Series duration in hours (default 72).")
    parser.add_argument("--freq-min", type=int, default=5, help="Measurement frequency in minutes (default 5).")
    parser.add_argument("--seed", type=int, default=None, help="Random seed (optional, for reproducibility).")
    args = parser.parse_args()

    # Initialize RNGs for reproducibility when --seed is set
    random.seed(args.seed)
    np.random.seed(args.seed if args.seed is not None else None)

    # Read SV.xpt (SAS XPORT). Pandas handles typical SDTM SV files.
    try:
        sv = pd.read_sas(args.sv, format="xport", encoding="utf-8")
    except Exception as e:
        print(f"ERROR: Failed to read SV.xpt at {args.sv}: {e}", file=sys.stderr)
        sys.exit(1)

    # Normalize column names and validate required ones
    sv.columns = [str(c).upper() for c in sv.columns]
    required_cols = ["USUBJID", "VISITNUM", "SVSTDTC", "SVENDTC"]
    for c in required_cols:
        if c not in sv.columns:
            print(f"ERROR: SV.xpt missing required column: {c}", file=sys.stderr)
            sys.exit(1)

    # Ensure VISITNUM is numeric to compare against --visit-start/--visit-end
    sv["VISITNUM"] = pd.to_numeric(sv["VISITNUM"], errors="coerce")

    # Unique subject list (string USUBJID)
    subjects = sorted(sv["USUBJID"].dropna().astype(str).unique().tolist())

    # Preface row (Row 1), padded to match header width
    header_row1 = ["Glucose Data", "Generated on", now_utc_header_string(), "Generated by", "XX-XXXXX"]
    if len(header_row1) < len(OUTPUT_COLUMNS):
        header_row1 = header_row1 + [""] * (len(OUTPUT_COLUMNS) - len(header_row1))

    all_rows = []
    total_subjects = 0
    total_records = 0

    # Iterate subjects and generate sequences conditioned on the chosen visits
    for usubjid in subjects:
        sub = sv[sv["USUBJID"].astype(str) == usubjid]

        # Select the first matching rows for start/end visits
        start_row = sub[np.isclose(sub["VISITNUM"], args.visit_start, equal_nan=False)]
        end_row   = sub[np.isclose(sub["VISITNUM"], args.visit_end,   equal_nan=False)]

        if start_row.empty or end_row.empty:
            print(f"WARNING: {usubjid}: Missing start or end visit (VISITNUM={args.visit_start} / {args.visit_end}). Skipping.", file=sys.stderr)
            continue

        start_row = start_row.iloc[0]
        end_row   = end_row.iloc[0]

        # Parse visit window boundaries (support date-only values)
        start_dt = parse_sdtm_datetime(start_row.get("SVSTDTC", None), is_start=True)
        end_dt   = parse_sdtm_datetime(end_row.get("SVENDTC", None), is_start=False)

        if start_dt is None or end_dt is None:
            print(f"WARNING: {usubjid}: Could not parse SVSTDTC/SVENDTC; skipping subject.", file=sys.stderr)
            continue
        if end_dt <= start_dt:
            print(f"WARNING: {usubjid}: Visit window end <= start; skipping subject.", file=sys.stderr)
            continue

        # Build simulated rows
        rows, warns = build_rows_for_subject(
            usubjid=usubjid,
            window_start=start_dt,
            window_end=end_dt,
            duration_hours=args.duration_hours,
            freq_minutes=args.freq_min,
            seed=args.seed
        )
        for w in warns:
            print(f"INFO: {usubjid}: {w}", file=sys.stderr)

        if not rows:
            print(f"WARNING: {usubjid}: No data rows generated.", file=sys.stderr)
            continue

        all_rows.extend(rows)
        total_subjects += 1
        total_records += len(rows)

    if total_subjects == 0:
        print("No subject data generated. Check warnings above.", file=sys.stderr)
        sys.exit(2)

    # Ensure output directory exists
    outdir = os.path.dirname(os.path.abspath(args.outfile))
    if outdir and not os.path.exists(outdir):
        os.makedirs(outdir, exist_ok=True)

    # Write combined CSV:
    #   - Row 1: Preface (includes generation timestamp)
    #   - Row 2: Column headers
    #   - Row 3+: Data rows for all subjects
    with open(args.outfile, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header_row1)
        w.writerow(OUTPUT_COLUMNS)
        for r in all_rows:
            w.writerow([r.get(col, "") for col in OUTPUT_COLUMNS])

    print(f"Done. Wrote {total_records} records for {total_subjects} subject(s) to: {args.outfile}", file=sys.stderr)


if __name__ == "__main__":
    main()