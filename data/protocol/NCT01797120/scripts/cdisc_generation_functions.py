import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

STUDYID = "SYNTH-ONC-001"

# Progression parameters empirically calibrated (n=50k simulation) to match
# FHIR-published KM medians with U(60,600) censoring:
#   Treatment target: 10.3 months (314 days)  → p=0.85, exp scale=350 days
#   Placebo   target:  5.1 months (155 days)  → p=0.90, exp scale=195 days
_PROG = {
    "Treatment": {"prob": 0.85, "scale": 350},
    "Placebo": {"prob": 0.90, "scale": 195},
}

# Tumour dynamics: responder/non-responder model calibrated (n=30k simulation) to match
# FHIR-published ORR values (Trt 18.2% CI 9.8-29.6%, Pbo 12.3% CI 5.5-22.8%):
#   Responders:     strong shrinkage (-12 mm/visit) → reliable PR within 2-3 assessments
#   Non-responders: slow growth      (+2  mm/visit) → no PR expected
#   Noise σ=8mm both types. Responder fractions: Trt=0.22, Pbo=0.14
_TUMOUR = {
    "Treatment": {
        "resp_frac": 0.21,
        "drift_resp": -12.0,
        "drift_nonresp": +2.0,
        "noise": 8.0,
    },
    "Placebo": {
        "resp_frac": 0.20,
        "drift_resp": -12.0,
        "drift_nonresp": +2.0,
        "noise": 8.0,
    },
}

_ENROLL_START = datetime(2021, 1, 1)
_STUDY_END = datetime(2026, 12, 31)


def _fmt(d):
    """Format a date-like value as ISO-8601 string, or empty string if missing."""
    if d is None or (hasattr(d, "__class__") and d.__class__.__name__ in ("NaTType",)):
        return ""
    try:
        return pd.Timestamp(d).strftime("%Y-%m-%d")
    except Exception:
        return str(d)[:10]


# ---------------- DM ----------------
def create_dm(n=200):
    # Balanced 1:1 randomisation via permutation, matching trial design
    arms = np.random.permutation(["Treatment"] * (n // 2) + ["Placebo"] * (n // 2))

    # Spread enrollment over a 24-month window (2021-01-01 to 2022-12-31)
    enroll_offsets = np.random.randint(0, 730, size=n)
    rfstdtc = [
        (_ENROLL_START + timedelta(days=int(d))).strftime("%Y-%m-%d")
        for d in enroll_offsets
    ]

    dm = pd.DataFrame(
        {
            "SUBJID": [f"{i:04d}" for i in range(1, n + 1)],
            "DMSEQ": range(1, n + 1),
            "AGE": np.clip(np.random.normal(55, 10, n), 20, 80).astype(int),
            "SEX": "F",
            "RFSTDTC": rfstdtc,
            # TRT01A kept as internal helper for derive_events / create_tr;
            # not included in the final SDTM DM column list
            "TRT01A": arms,
            "ARMCD": ["TRT" if a == "Treatment" else "PLC" for a in arms],
            "ARM": [
                (
                    "Fulvestrant + Everolimus"
                    if a == "Treatment"
                    else "Fulvestrant + Placebo"
                )
                for a in arms
            ],
        }
    )
    dm["STUDYID"] = STUDYID
    dm["DOMAIN"] = "DM"
    dm["USUBJID"] = STUDYID + "-" + dm["SUBJID"]
    dm["ACTARMCD"] = dm["ARMCD"]
    dm["ACTARM"] = dm["ARM"]

    # DTHFL / DTHDTC and RFXSTDTC / RFXENDTC added later by finalize_dm
    return dm


def finalize_dm(dm, ex, events):
    """Add DTHFL/DTHDTC (from events) and RFXSTDTC/RFXENDTC (from EX) to DM."""
    # Subject-level first/last exposure dates
    rfx = (
        ex.groupby("USUBJID")
        .agg(
            RFXSTDTC=("EXSTDTC", "min"),
            RFXENDTC=("EXENDTC", "max"),
        )
        .reset_index()
    )

    death_info = events[["USUBJID", "DIED", "DTHDT"]].copy()

    dm = dm.merge(rfx, on="USUBJID", how="left")
    dm = dm.merge(death_info, on="USUBJID", how="left")

    dm["DTHFL"] = dm["DIED"].map({True: "Y", False: "N"}).fillna("N")
    dm["DTHDTC"] = dm["DTHDT"].apply(_fmt)
    dm = dm.drop(columns=["DIED", "DTHDT"])

    return dm[
        [
            "STUDYID",
            "DOMAIN",
            "USUBJID",
            "SUBJID",
            "DMSEQ",
            "AGE",
            "SEX",
            "RFSTDTC",
            "RFXSTDTC",
            "RFXENDTC",
            "ARMCD",
            "ARM",
            "ACTARMCD",
            "ACTARM",
            "DTHFL",
            "DTHDTC",
            # TRT01A retained as internal helper column (not SDTM) for create_tr
            "TRT01A",
        ]
    ]


# ---------------- EX ----------------
def create_ex(dm):
    """
    Two drug records per subject:
      FULVESTRANT  500 mg IM — one record per injection (C1D1, C1D15, then Q28D)
      EVEROLIMUS / PLACEBO 10 mg oral — one record spanning the full treatment period
    """
    records = []

    for _, row in dm.iterrows():
        usubjid = row["USUBJID"]
        arm = row["TRT01A"]
        start = datetime.strptime(str(row["RFSTDTC"])[:10], "%Y-%m-%d")
        dur = int(np.random.uniform(60, 600))
        end = start + timedelta(days=dur)

        # Fulvestrant injection schedule
        inj_offsets = [0, 14]  # C1D1, C1D15
        cycle_day = 28  # C2D1, then +28 per cycle
        while start + timedelta(days=cycle_day) <= end:
            inj_offsets.append(cycle_day)
            cycle_day += 28

        seq = 1
        for offset in inj_offsets:
            inj_date = start + timedelta(days=offset)
            records.append(
                {
                    "STUDYID": STUDYID,
                    "DOMAIN": "EX",
                    "USUBJID": usubjid,
                    "EXSEQ": seq,
                    "EXTRT": "FULVESTRANT",
                    "EXDOSE": 500,
                    "EXDOSU": "mg",
                    "EXROUTE": "INTRAMUSCULAR",
                    "EXFREQ": "ONCE",
                    "EXSTDTC": inj_date.strftime("%Y-%m-%d"),
                    "EXENDTC": inj_date.strftime("%Y-%m-%d"),
                }
            )
            seq += 1

        # Everolimus (treatment arm) or Placebo (control arm)
        second_drug = "EVEROLIMUS" if arm == "Treatment" else "PLACEBO"
        records.append(
            {
                "STUDYID": STUDYID,
                "DOMAIN": "EX",
                "USUBJID": usubjid,
                "EXSEQ": seq,
                "EXTRT": second_drug,
                "EXDOSE": 10,
                "EXDOSU": "mg",
                "EXROUTE": "ORAL",
                "EXFREQ": "QD",
                "EXSTDTC": start.strftime("%Y-%m-%d"),
                "EXENDTC": end.strftime("%Y-%m-%d"),
            }
        )

    return pd.DataFrame(records)


# ---------------- EVENTS (internal) ----------------
def derive_events(ex, dm):
    """
    One row per subject: PROGDT (datetime | None), WITHDRAWAL (bool),
    RESPONDER (bool), DIED (bool), DTHDT (datetime | None).
    """
    ex_start = ex.groupby("USUBJID")["EXSTDTC"].min().reset_index()
    ex_end = ex.groupby("USUBJID")["EXENDTC"].max().reset_index()

    merged = ex_start.merge(dm[["USUBJID", "TRT01A"]])

    records = []
    for _, row in merged.iterrows():
        start = datetime.strptime(str(row["EXSTDTC"])[:10], "%Y-%m-%d")
        arm = row["TRT01A"]
        params = _PROG[arm]
        if np.random.rand() < params["prob"]:
            days = max(84, int(np.random.exponential(params["scale"])))
            progdt = start + timedelta(days=days)
        else:
            progdt = None
        responder = np.random.rand() < _TUMOUR[arm]["resp_frac"]
        records.append(
            {"USUBJID": row["USUBJID"], "PROGDT": progdt, "RESPONDER": responder}
        )

    events = pd.DataFrame(records)
    no_prog = events["PROGDT"].isna()
    events["WITHDRAWAL"] = no_prog & (np.random.rand(len(events)) < 0.20)

    # Death simulation
    events = events.merge(ex_end, on="USUBJID", how="left")
    died_list = []
    dthdt_list = []
    for _, row in events.iterrows():
        progdt = row["PROGDT"]
        withdrawal = bool(row["WITHDRAWAL"])
        exendtc = datetime.strptime(str(row["EXENDTC"])[:10], "%Y-%m-%d")

        if pd.notna(progdt):
            # ~75% of progressors die during follow-up
            if np.random.rand() < 0.75:
                days = max(1, int(np.random.exponential(180)))
                dt = min(progdt + timedelta(days=days), _STUDY_END)
                died_list.append(True)
                dthdt_list.append(dt)
            else:
                died_list.append(False)
                dthdt_list.append(None)
        elif withdrawal:
            # ~15% of withdrawers die during follow-up
            if np.random.rand() < 0.15:
                days = max(1, int(np.random.exponential(365)))
                dt = min(exendtc + timedelta(days=days), _STUDY_END)
                died_list.append(True)
                dthdt_list.append(dt)
            else:
                died_list.append(False)
                dthdt_list.append(None)
        else:
            died_list.append(False)
            dthdt_list.append(None)

    events["DIED"] = died_list
    events["DTHDT"] = dthdt_list
    events = events.drop(columns=["EXENDTC"])
    return events


# ---------------- TR ----------------
def create_tr(ex, events, dm):
    """
    Adds a BASELINE record (TRDY=1, ABLFL=Y) anchored to the pre-treatment
    tumour size, then post-baseline assessments every 12 weeks (84 days).
    VISITNUM follows TV: BASELINE=2, WEEK 12=3, WEEK 24=4, …

    Tumour dynamics use a responder/non-responder model (see _TUMOUR) so that
    arm-level ORR approximates FHIR-published values.
    """
    tr = []
    seq = 1

    # One treatment-start row per subject
    ex_starts = ex.groupby("USUBJID")["EXSTDTC"].min().reset_index()
    ex_starts["EXSTDTC"] = pd.to_datetime(ex_starts["EXSTDTC"])
    merged = ex_starts.merge(events[["USUBJID", "PROGDT", "RESPONDER"]])
    merged = merged.merge(dm[["USUBJID", "TRT01A"]])

    for _, row in merged.iterrows():
        arm = row["TRT01A"]
        tp = _TUMOUR[arm]
        drift = tp["drift_resp"] if row["RESPONDER"] else tp["drift_nonresp"]
        noise = tp["noise"]

        base = np.random.normal(50, 10)
        tumor = base

        # Baseline record
        baseline_date = row["EXSTDTC"] + timedelta(days=1)
        tr.append(
            {
                "STUDYID": STUDYID,
                "DOMAIN": "TR",
                "USUBJID": row["USUBJID"],
                "TRSEQ": seq,
                "TRTESTCD": "DIAM",
                "TRTEST": "Diameter",
                "TRSTRESN": round(base, 2),
                "TRSTRESU": "mm",
                "TRDTC": baseline_date.strftime("%Y-%m-%d"),
                "VISITNUM": 2,
                "VISIT": "BASELINE",
                "TRDY": 1,
                "ABLFL": "Y",
            }
        )
        seq += 1

        progdt = row["PROGDT"]
        for v, day in enumerate(range(85, 800, 84), start=1):
            date = row["EXSTDTC"] + timedelta(days=day)
            if progdt is not None and pd.notna(progdt) and date > progdt:
                break
            tumor = max(1, tumor + np.random.normal(drift, noise))
            tr.append(
                {
                    "STUDYID": STUDYID,
                    "DOMAIN": "TR",
                    "USUBJID": row["USUBJID"],
                    "TRSEQ": seq,
                    "TRTESTCD": "DIAM",
                    "TRTEST": "Diameter",
                    "TRSTRESN": round(tumor, 2),
                    "TRSTRESU": "mm",
                    "TRDTC": date.strftime("%Y-%m-%d"),
                    "VISITNUM": v + 2,
                    "VISIT": f"WEEK {v * 12}",
                    "TRDY": day,
                    "ABLFL": "",
                }
            )
            seq += 1

    return pd.DataFrame(tr)


# ---------------- RS ----------------
def derive_rs(tr):
    """RECIST response derived as % change from the ABLFL (day-1) baseline."""
    rs = []
    seq = 1
    # Build baseline map from day-1 measurements
    base_map = tr[tr["ABLFL"] == "Y"].set_index("USUBJID")["TRSTRESN"]

    # Only score post-baseline assessments
    for _, row in tr[tr["ABLFL"] != "Y"].iterrows():
        base = base_map.get(row["USUBJID"], row["TRSTRESN"])
        pct = (row["TRSTRESN"] - base) / base * 100
        if pct <= -30:
            resp = "PR"
        elif pct >= 20:
            resp = "PD"
        else:
            resp = "SD"
        rs.append(
            {
                "STUDYID": STUDYID,
                "DOMAIN": "RS",
                "USUBJID": row["USUBJID"],
                "RSSEQ": seq,
                "RSTESTCD": "OVRLRESP",
                "RSTEST": "Overall Response",
                "RSSTRESC": resp,
                "RSDTC": row["TRDTC"],
                "VISITNUM": row["VISITNUM"],
                "VISIT": row["VISIT"],
                "RSDY": row["TRDY"],
            }
        )
        seq += 1

    return pd.DataFrame(rs)


# ---------------- DS ----------------
def create_ds(dm, ex, events):
    """
    DS records per subject:
      1. PROTOCOL MILESTONE / RANDOMIZED      (EPOCH=SCREENING)
      2. DISPOSITION EVENT / <reason> / FULVESTRANT  (EPOCH=TREATMENT)
      3. DISPOSITION EVENT / <reason> / EVEROLIMUS or PLACEBO (EPOCH=TREATMENT)
      4. DISPOSITION EVENT / DEATH / STUDY    (EPOCH=FOLLOW-UP) — only if died
    """
    # Max treatment end per subject (Everolimus/Placebo record spans the full period)
    ex_end = ex.groupby("USUBJID")["EXENDTC"].max().reset_index()

    core = (
        dm[["USUBJID", "RFSTDTC", "ARMCD"]]
        .merge(ex_end, on="USUBJID")
        .merge(
            events[["USUBJID", "PROGDT", "WITHDRAWAL", "DIED", "DTHDT"]],
            on="USUBJID",
            how="left",
        )
    )

    ds = []
    for _, row in core.iterrows():
        progdt = row["PROGDT"]
        has_prog = pd.notna(progdt)
        is_withdrawal = bool(row["WITHDRAWAL"])
        did_die = bool(row["DIED"])
        arm = row["ARMCD"]

        if has_prog:
            stop_reason = "PROGRESSIVE DISEASE"
            stop_dtc = _fmt(progdt)
        elif is_withdrawal:
            stop_reason = "WITHDRAWAL BY SUBJECT"
            stop_dtc = str(row["EXENDTC"])[:10]
        else:
            stop_reason = "COMPLETED"
            stop_dtc = str(row["EXENDTC"])[:10]

        secondary_drug = "EVEROLIMUS" if arm == "TRT" else "PLACEBO"
        seq = 1

        # Record 1: protocol milestone — randomization
        ds.append(
            {
                "STUDYID": STUDYID,
                "DOMAIN": "DS",
                "USUBJID": row["USUBJID"],
                "DSSEQ": seq,
                "DSCAT": "PROTOCOL MILESTONE",
                "DSSCAT": "",
                "DSDECOD": "RANDOMIZED",
                "DSDTC": str(row["RFSTDTC"])[:10],
                "EPOCH": "SCREENING",
            }
        )
        seq += 1

        # Record 2: Fulvestrant stopping
        ds.append(
            {
                "STUDYID": STUDYID,
                "DOMAIN": "DS",
                "USUBJID": row["USUBJID"],
                "DSSEQ": seq,
                "DSCAT": "DISPOSITION EVENT",
                "DSSCAT": "FULVESTRANT",
                "DSDECOD": stop_reason,
                "DSDTC": stop_dtc,
                "EPOCH": "TREATMENT",
            }
        )
        seq += 1

        # Record 3: Everolimus / Placebo stopping
        ds.append(
            {
                "STUDYID": STUDYID,
                "DOMAIN": "DS",
                "USUBJID": row["USUBJID"],
                "DSSEQ": seq,
                "DSCAT": "DISPOSITION EVENT",
                "DSSCAT": secondary_drug,
                "DSDECOD": stop_reason,
                "DSDTC": stop_dtc,
                "EPOCH": "TREATMENT",
            }
        )
        seq += 1

        # Record 4: death (only if subject died during follow-up)
        if did_die and pd.notna(row["DTHDT"]):
            ds.append(
                {
                    "STUDYID": STUDYID,
                    "DOMAIN": "DS",
                    "USUBJID": row["USUBJID"],
                    "DSSEQ": seq,
                    "DSCAT": "DISPOSITION EVENT",
                    "DSSCAT": "STUDY",
                    "DSDECOD": "DEATH",
                    "DSDTC": _fmt(row["DTHDT"]),
                    "EPOCH": "FOLLOW-UP",
                }
            )

    return pd.DataFrame(ds)


# ---------------- ADSL ----------------
def _best_response(responses):
    for r in ("PR", "SD", "PD"):
        if r in responses.values:
            return r
    return ""


def create_adsl(dm, ex, rs, events):
    # Subject-level treatment dates (earliest start, latest end across all EX records)
    ex_dates = (
        ex.groupby("USUBJID")
        .agg(
            EXSTDTC=("EXSTDTC", "min"),
            EXENDTC=("EXENDTC", "max"),
        )
        .reset_index()
    )
    ex_dates["EXSTDTC"] = pd.to_datetime(ex_dates["EXSTDTC"])
    ex_dates["EXENDTC"] = pd.to_datetime(ex_dates["EXENDTC"])

    bestresp_map = rs.groupby("USUBJID")["RSSTRESC"].apply(_best_response).to_dict()

    # Derive ADaM TRT01A from ARMCD
    dm_copy = dm.copy()
    dm_copy["TRT01A"] = dm_copy["ARMCD"].map({"TRT": "Treatment", "PLC": "Placebo"})

    core = (
        dm_copy[["USUBJID", "TRT01A", "AGE"]]
        .merge(ex_dates[["USUBJID", "EXSTDTC", "EXENDTC"]])
        .merge(events[["USUBJID", "PROGDT", "WITHDRAWAL"]], on="USUBJID", how="left")
    )

    records = []
    for _, row in core.iterrows():
        progdt = row["PROGDT"]
        if pd.notna(progdt):
            pfs = (progdt - row["EXSTDTC"]).days
            cnsr = 0
            dcsreas = "PROGRESSIVE DISEASE"
        else:
            pfs = (row["EXENDTC"] - row["EXSTDTC"]).days
            cnsr = 1
            dcsreas = "WITHDRAWAL BY SUBJECT" if row["WITHDRAWAL"] else "COMPLETED"

        records.append(
            {
                "STUDYID": STUDYID,
                "USUBJID": row["USUBJID"],
                "TRT01A": row["TRT01A"],
                "AGE": row["AGE"],
                "PFS": pfs,
                "CNSR": cnsr,
                "BESTRESP": bestresp_map.get(row["USUBJID"], ""),
                "DCSREAS": dcsreas,
            }
        )

    return pd.DataFrame(records)


# ---------------- ADTTE ----------------
def create_adtte(adsl):
    return pd.DataFrame(
        [
            {
                "STUDYID": STUDYID,
                "USUBJID": row["USUBJID"],
                "PARAMCD": "PFS",
                "PARAM": "Progression-Free Survival",
                "AVAL": float(row["PFS"]),
                "CNSR": row["CNSR"],
                "TRT01A": row["TRT01A"],
            }
            for _, row in adsl.iterrows()
        ]
    )


# ---------------- TV ----------------
def create_tv():
    visits = [
        (1, "SCREENING", -14, 0, "SCREENING"),
        (2, "BASELINE", 1, 1, "TREATMENT"),
    ]
    # Tumour assessment visits matching TR VISITNUM scheme (3 = Week 12, etc.)
    for v, day in enumerate(range(85, 800, 84), start=1):
        visits.append((v + 2, f"WEEK {v * 12}", day, day, "TREATMENT"))
    visits.append((len(visits) + 1, "END OF TREATMENT", "", "", "FOLLOW-UP"))

    rows = []
    for visitnum, visit, tvstrl, tvenrl, epoch in visits:
        rows.append(
            {
                "STUDYID": STUDYID,
                "DOMAIN": "TV",
                "VISITNUM": visitnum,
                "VISIT": visit,
                "TVSTRL": tvstrl,
                "TVENRL": tvenrl,
                "EPOCH": epoch,
            }
        )
    return pd.DataFrame(rows)


# ---------------- TA ----------------
def create_ta():
    return pd.DataFrame(
        {
            "STUDYID": STUDYID,
            "DOMAIN": "TA",
            "ARMCD": ["TRT", "PLC"],
            "ARM": ["Fulvestrant + Everolimus", "Fulvestrant + Placebo"],
            "TAETORD": [1, 1],
            "EPOCH": ["TREATMENT", "TREATMENT"],
        }
    )


# ---------------- MAIN ----------------
if __name__ == "__main__":
    np.random.seed(42)

    out_dir = os.path.join(os.path.dirname(__file__), "..", "datasets")
    os.makedirs(out_dir, exist_ok=True)

    dm = create_dm(n=200)
    ex = create_ex(dm)
    events = derive_events(ex, dm)
    tr = create_tr(ex, events, dm)  # needs TRT01A; run before finalize_dm
    rs = derive_rs(tr)
    dm = finalize_dm(dm, ex, events)
    ds = create_ds(dm, ex, events)
    adsl = create_adsl(dm, ex, rs, events)
    adtte = create_adtte(adsl)
    tv = create_tv()
    ta = create_ta()

    for name, df in [
        ("DM", dm),
        ("EX", ex),
        ("TR", tr),
        ("RS", rs),
        ("DS", ds),
        ("ADSL", adsl),
        ("ADTTE", adtte),
        ("TV", tv),
        ("TA", ta),
    ]:
        # Exclude internal helper column TRT01A from SDTM DM output
        out_df = df.drop(columns=["TRT01A"], errors="ignore") if name == "DM" else df
        path = os.path.join(out_dir, f"{name.lower()}.csv")
        out_df.to_csv(path, index=False)
        print(f"Wrote {name.lower()}.csv  ({len(out_df)} rows)")
