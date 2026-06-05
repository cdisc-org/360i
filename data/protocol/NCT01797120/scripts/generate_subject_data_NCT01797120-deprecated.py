"""
Generate synthetic SDTM/ADaM subject-level data for NCT01797120 (PrE0102).

Produces 8 CSV files in files/subject_data/NCT01797120/:
  DM.csv    ADSL.csv
  EX.csv    ADTTE.csv
  LB.csv
  VS.csv
  TU.csv
  RS.csv

Statistical targets are calibrated to the published results in
docs/NCT01797120-results.fhir.json. Random seed 42 ensures reproducibility.

Usage:
    python scripts/generate_subject_data_NCT01797120.py
"""

import math
import os
import random
from datetime import date, timedelta

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SEED = 42
rng = np.random.default_rng(SEED)
random.seed(SEED)

OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "files", "subject_data", "NCT01797120"
)
os.makedirs(OUT_DIR, exist_ok=True)

STUDYID = "NCT01797120"

# Arm definitions
ARMS = {
    "FULEV": {
        "label": "Fulvestrant & Everolimus",
        "n": 66,
        "pfs_median": 10.3,
        "os_median": 28.3,
        "orr_n": 12,   # CR+PR count
        "cr_n": 2,
        "cbr_n": 42,   # CR+PR+SD>=24w
        "pfs_events": 39,
        "never_started": 2,
        "still_on_tx": 2,
        "ae_disc": 13,
        "age_median": 64, "age_min": 39, "age_max": 92,
        "race_white": 56, "race_black": 8, "race_other": 2,
    },
    "FULPL": {
        "label": "Fulvestrant & Placebo",
        "n": 65,
        "pfs_median": 5.1,
        "os_median": 31.4,
        "orr_n": 8,
        "cr_n": 1,
        "cbr_n": 27,
        "pfs_events": 50,
        "never_started": 2,
        "still_on_tx": 4,
        "ae_disc": 5,
        "age_median": 59, "age_min": 35, "age_max": 85,
        "race_white": 49, "race_black": 11, "race_other": 5,
    },
}

# 25 sites from the trial (abbreviated codes)
SITE_IDS = [
    "001", "002", "003", "004", "005",
    "006", "007", "008", "009", "010",
    "011", "012", "013", "014", "015",
    "016", "017", "018", "019", "020",
    "021", "022", "023", "024", "025",
]

# Study start (first randomization)
STUDY_START = date(2013, 5, 31)
ACCRUAL_END = date(2014, 5, 31)

# Lab definitions: (test_code, test_name, category, low, high, unit, dist)
# dist: ("normal", mean, sd) or ("lognormal", mu, sigma)
LAB_DEFS = [
    ("WBC",   "White Blood Cell Count",       "HEMATOLOGY", 4.0,  11.0, "10^9/L",  ("normal",    6.5,  1.5)),
    ("HGB",   "Hemoglobin",                   "HEMATOLOGY", 11.5, 16.0, "g/dL",    ("normal",   13.5,  1.0)),
    ("PLT",   "Platelet Count",               "HEMATOLOGY", 150,  400,  "10^9/L",  ("normal",  260.0, 60.0)),
    ("CREAT", "Creatinine",                   "CHEMISTRY",  0.5,   1.2, "mg/dL",   ("normal",    0.85, 0.15)),
    ("ALT",   "Alanine Aminotransferase",     "CHEMISTRY",  7.0,  40.0, "U/L",     ("lognormal", 3.0,  0.4)),
    ("AST",   "Aspartate Aminotransferase",   "CHEMISTRY", 10.0,  40.0, "U/L",     ("lognormal", 3.2,  0.35)),
    ("BILI",  "Bilirubin Total",              "CHEMISTRY",  0.1,   1.0, "mg/dL",   ("lognormal", -1.0, 0.5)),
    ("ALB",   "Albumin",                      "CHEMISTRY",  3.5,   5.0, "g/dL",    ("normal",    4.0,  0.35)),
    ("PHOS",  "Phosphorus",                   "CHEMISTRY",  2.5,   4.5, "mg/dL",   ("normal",    3.4,  0.5)),
    ("GLUC",  "Glucose",                      "CHEMISTRY", 70.0, 100.0, "mg/dL",   ("normal",   88.0, 12.0)),
    ("CHOL",  "Cholesterol",                  "LIPIDS",   150.0, 240.0, "mg/dL",   ("normal",  190.0, 30.0)),
    ("TRIG",  "Triglycerides",               "LIPIDS",    50.0, 200.0, "mg/dL",   ("normal",  118.0, 40.0)),
    ("HDL",   "HDL Cholesterol",             "LIPIDS",    40.0,  80.0, "mg/dL",   ("normal",   57.0, 10.0)),
    ("LDL",   "LDL Cholesterol",             "LIPIDS",    60.0, 160.0, "mg/dL",   ("normal",  115.0, 25.0)),
]

# Labs collected only at specific visit types (others get full panel every cycle)
LIPID_TESTS = {"CHOL", "TRIG", "HDL", "LDL", "GLUC"}

# Visit sign definitions
VS_DEFS = [
    ("SYSBP",  "Systolic Blood Pressure",  "mmHg",  "normal", 125.0, 15.0),
    ("DIABP",  "Diastolic Blood Pressure", "mmHg",  "normal",  78.0, 10.0),
    ("HR",     "Heart Rate",               "beats/min", "normal", 72.0, 10.0),
    ("TEMP",   "Temperature",              "C",     "normal",  36.8,  0.3),
    ("WEIGHT", "Weight",                   "kg",    "normal",  70.0, 14.0),
]

# Tumor locations (cycle through for up to 3 lesions)
TUMOR_LOCS = [
    "LUNG", "LIVER", "LYMPH NODE", "BONE", "ADRENAL GLAND",
    "PLEURA", "SOFT TISSUE", "BREAST (LOCAL)", "SKIN",
]


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def iso(d):
    """Return ISO 8601 date string."""
    return d.isoformat()


def study_day(visit_date, rfstdtc):
    """SDTM study day: day 1 = rfstdtc."""
    delta = (visit_date - rfstdtc).days
    return delta + 1 if delta >= 0 else delta


def rand_date(start, end):
    """Uniform random date between start and end."""
    span = (end - start).days
    return start + timedelta(days=int(rng.integers(0, span + 1)))


def sample_age(median, lo, hi, n):
    """
    Sample ages from a distribution with the given median, clamped to [lo, hi].
    Uses a normal distribution centred on the median with SD chosen so that
    the range spans roughly ±3 SD.
    """
    sd = min((median - lo), (hi - median)) / 2.5
    ages = rng.normal(median, sd, n)
    ages = np.clip(np.round(ages).astype(int), lo, hi)
    return ages.tolist()


def sample_lab(dist_spec, n, mtor_toxicity=False, test_code=None):
    """Draw n lab values. Optionally apply mTOR-toxicity multipliers."""
    kind = dist_spec[0]
    if kind == "normal":
        vals = rng.normal(dist_spec[1], dist_spec[2], n)
    else:  # lognormal
        vals = np.exp(rng.normal(dist_spec[1], dist_spec[2], n))

    if mtor_toxicity and test_code in ("GLUC",):
        vals *= rng.uniform(1.20, 1.45, n)
    elif mtor_toxicity and test_code in ("TRIG",):
        vals *= rng.uniform(1.35, 1.65, n)
    elif mtor_toxicity and test_code in ("CHOL",):
        vals *= rng.uniform(1.15, 1.35, n)
    elif mtor_toxicity and test_code in ("WBC", "PLT"):
        vals *= rng.uniform(0.70, 0.90, n)

    return np.round(vals, 2).tolist()


def nrind(val, lo, hi):
    """Normal range indicator."""
    if val < lo:
        return "LOW"
    if val > hi:
        return "HIGH"
    return "NORMAL"


# ---------------------------------------------------------------------------
# Step 1: Build subject roster
# ---------------------------------------------------------------------------

def build_subjects():
    """Return list of subject dicts with demographics and outcomes."""
    subjects = []
    seq = 1

    for armcd, cfg in ARMS.items():
        n = cfg["n"]
        ages = sample_age(cfg["age_median"], cfg["age_min"], cfg["age_max"], n)

        # Race: exact published counts
        races = (
            ["WHITE"] * cfg["race_white"]
            + ["BLACK OR AFRICAN AMERICAN"] * cfg["race_black"]
            + ["OTHER"] * cfg["race_other"]
        )
        rng.shuffle(races)

        # Stratification factors (assumed uniform per 1:1 strat balance)
        ecog = rng.integers(0, 2, n).tolist()           # 0 or 1
        measurable = (rng.random(n) < 0.60).tolist()    # 60% measurable
        prior_chemo = (rng.random(n) < 0.40).tolist()   # 40% prior chemo

        # Site assignment: ~5 subjects per site, cycle through
        sites = [SITE_IDS[i % 25] for i in range(n)]
        rng.shuffle(sites)

        # Randomization dates: uniform across accrual window
        randdts = [
            rand_date(STUDY_START, ACCRUAL_END) for _ in range(n)
        ]

        # --- PFS generation ---
        # Draw from exponential calibrated to median
        lam = math.log(2) / cfg["pfs_median"]
        raw_pfs = rng.exponential(1.0 / lam, n).tolist()

        # Identify "never started" subjects (first 2 in arm)
        never_started_idx = set(range(cfg["never_started"]))
        still_on_tx_idx = set(range(
            cfg["never_started"],
            cfg["never_started"] + cfg["still_on_tx"]
        ))

        # Sort remaining subjects by raw PFS, assign events to the
        # cfg["pfs_events"] shortest to hit exact event count
        analysis_idx = [
            i for i in range(n)
            if i not in never_started_idx and i not in still_on_tx_idx
        ]
        analysis_pfs = [(raw_pfs[i], i) for i in analysis_idx]
        analysis_pfs.sort()
        event_set = {idx for _, idx in analysis_pfs[:cfg["pfs_events"]]}

        # --- Response assignment ---
        # Order: CR, PR, SD>=24w, PD  (among analysis population)
        resp_pool = (
            ["CR"] * cfg["cr_n"]
            + ["PR"] * (cfg["orr_n"] - cfg["cr_n"])
            + ["SD"] * (cfg["cbr_n"] - cfg["orr_n"])
            + ["PD"] * (len(analysis_idx) - cfg["cbr_n"])
        )
        rng.shuffle(resp_pool)
        resp_iter = iter(resp_pool)

        # --- OS generation ---
        os_lam = math.log(2) / cfg["os_median"]
        raw_os = rng.exponential(1.0 / os_lam, n).tolist()
        # OS >= PFS always; cap at 36 months
        for i in range(n):
            raw_os[i] = max(raw_os[i], raw_pfs[i] + rng.uniform(0, 6))
            raw_os[i] = min(raw_os[i], 36.0)

        # --- Discontinuation reason ---
        # Pool of reasons for analysis population events
        disc_pool = (
            ["DISEASE PROGRESSION"] * 37
            + ["SYMPTOMATIC PROGRESSION"] * 2
            + ["ADVERSE EVENT"] * cfg["ae_disc"]
            + ["WITHDRAWAL BY SUBJECT"] * 6
            + ["PHYSICIAN DECISION"] * (3 if armcd == "FULEV" else 0)
            + ["NON-COMPLIANCE"] * (1 if armcd == "FULEV" else 0)
        ) if armcd == "FULEV" else (
            ["DISEASE PROGRESSION"] * 49
            + ["SYMPTOMATIC PROGRESSION"] * 1
            + ["ADVERSE EVENT"] * cfg["ae_disc"]
            + ["WITHDRAWAL BY SUBJECT"] * 6
        )
        rng.shuffle(disc_pool)
        disc_iter = iter(disc_pool)

        ae_subjects = set()  # track subjects with AE discontinuation

        for i in range(n):
            randdt = randdts[i]
            rfstdtc = randdt + timedelta(days=1)
            site = sites[i]
            usubjid = f"{STUDYID}-{site}-{seq:03d}"

            never_started = i in never_started_idx
            still_on = i in still_on_tx_idx

            if never_started:
                pfs_months = 0.0
                pfs_event = 0
                bestresp = "NE"
                cbr = 0
                disc_reason = "NEVER STARTED"
                efffl = "N"
                os_months = min(raw_os[i], 36.0)
                os_event = 1 if os_months < 36.0 else 0
            elif still_on:
                pfs_months = min(raw_pfs[i], 12.5)
                pfs_event = 0          # censored
                bestresp = next(resp_iter, "SD")
                cbr = 1 if bestresp in ("CR", "PR", "SD") else 0
                disc_reason = "STILL ON TREATMENT"
                efffl = "Y"
                os_months = min(raw_os[i], 36.0)
                os_event = 0
            else:
                pfs_months = raw_pfs[i]
                pfs_event = 1 if i in event_set else 0
                bestresp = next(resp_iter, "SD")
                cbr = 1 if bestresp in ("CR", "PR", "SD") else 0
                if pfs_event == 1:
                    disc_reason = next(disc_iter, "DISEASE PROGRESSION")
                else:
                    disc_reason = "COMPLETED"
                efffl = "Y"
                os_months = min(raw_os[i], 36.0)
                os_event = 1 if os_months < 36.0 and pfs_event == 1 else 0

            # Is this an AE-discontinuation subject?
            is_ae_disc = disc_reason == "ADVERSE EVENT"
            if is_ae_disc:
                ae_subjects.add(usubjid)

            # Derive key dates
            pfs_days = int(round(pfs_months * 30.44))
            pfs_date = rfstdtc + timedelta(days=pfs_days)
            os_days = int(round(os_months * 30.44))
            os_date = rfstdtc + timedelta(days=os_days)

            subjects.append({
                "STUDYID": STUDYID,
                "USUBJID": usubjid,
                "SUBJID": f"{seq:03d}",
                "SITEID": site,
                "ARMCD": armcd,
                "ARM": cfg["label"],
                "AGE": ages[i],
                "AGEU": "YEARS",
                "SEX": "F",
                "RACE": races[i],
                "ETHNIC": "NOT REPORTED",
                "COUNTRY": "USA",
                "ECOG": ecog[i],
                "MEASFL": "Y" if measurable[i] else "N",
                "PRIORCH": "Y" if prior_chemo[i] else "N",
                "RANDDT": iso(randdt),
                "RFSTDTC": iso(rfstdtc),
                "RFENDTC": iso(pfs_date),
                "PFSDT": iso(pfs_date),
                "PFSINV": round(pfs_months, 2),
                "PFSCNSR": 0 if pfs_event == 1 else 1,
                "OSDT": iso(os_date),
                "OSINV": round(os_months, 2),
                "OSCNSR": 0 if os_event == 1 else 1,
                "BESTRESP": bestresp,
                "CBR": cbr,
                "DCSREAS": disc_reason,
                "EFFFL": efffl,
                "ITTFL": "Y",
                "SAFFL": "N" if never_started else "Y",
                "IS_AE_DISC": is_ae_disc,
                "_rfstdtc_date": rfstdtc,
                "_pfs_date": pfs_date,
                "_os_date": os_date,
                "_pfs_months": pfs_months,
                "_never_started": never_started,
            })
            seq += 1

    return subjects


# ---------------------------------------------------------------------------
# Step 2: DM domain
# ---------------------------------------------------------------------------

def build_dm(subjects):
    rows = []
    for i, s in enumerate(subjects):
        rows.append({
            "STUDYID": s["STUDYID"],
            "DOMAIN": "DM",
            "USUBJID": s["USUBJID"],
            "DMSEQ": i + 1,
            "SUBJID": s["SUBJID"],
            "RFSTDTC": s["RFSTDTC"],
            "RFENDTC": s["RFENDTC"],
            "RFXSTDTC": s["RFSTDTC"] if not s["_never_started"] else "",
            "RFXENDTC": s["RFENDTC"] if not s["_never_started"] else "",
            "SITEID": s["SITEID"],
            "AGE": s["AGE"],
            "AGEU": s["AGEU"],
            "SEX": s["SEX"],
            "RACE": s["RACE"],
            "ETHNIC": s["ETHNIC"],
            "COUNTRY": s["COUNTRY"],
            "ARMCD": s["ARMCD"],
            "ARM": s["ARM"],
            "ACTARMCD": s["ARMCD"],
            "ACTARM": s["ARM"],
            "DMDTC": s["RFSTDTC"],
            "DMDY": 1,
        })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Step 3: Build visit schedule per subject
# ---------------------------------------------------------------------------

def build_visits(s):
    """
    Return list of (visit_name, visitnum, visit_date, visit_type) tuples.
    visit_type: SCREENING | TREATMENT | IMAGING | EOT | FU
    """
    if s["_never_started"]:
        # Only screening visit
        scr_date = s["_rfstdtc_date"] - timedelta(days=14)
        return [("SCREENING", 0, scr_date, "SCREENING")]

    rfst = s["_rfstdtc_date"]
    pfs_date = s["_pfs_date"]
    pfs_months = s["_pfs_months"]

    # Number of treatment cycles attended (cap at 12)
    n_cycles = min(max(1, math.ceil(pfs_months / (28 / 30.44))), 12)

    visits = []
    vnum = 0

    # Screening
    scr_date = rfst - timedelta(days=14)
    vnum += 1
    visits.append(("SCREENING", vnum, scr_date, "SCREENING"))

    # C1D1
    vnum += 1
    visits.append(("CYCLE 1 DAY 1", vnum, rfst, "TREATMENT"))

    # C1D15
    c1d15 = rfst + timedelta(days=14)
    if c1d15 <= pfs_date:
        vnum += 1
        visits.append(("CYCLE 1 DAY 15", vnum, c1d15, "TREATMENT"))

    # Cycle 2+ Day 1
    imaging_at_cycles = {3, 6, 9, 12}
    for cyc in range(2, n_cycles + 1):
        cyc_date = rfst + timedelta(days=(cyc - 1) * 28)
        if cyc_date > pfs_date:
            break
        vtype = "IMAGING" if cyc in imaging_at_cycles else "TREATMENT"
        vnum += 1
        visits.append((f"CYCLE {cyc} DAY 1", vnum, cyc_date, vtype))

    # EOT (if not exactly on a cycle day)
    if pfs_date not in [v[2] for v in visits]:
        vnum += 1
        visits.append(("END OF TREATMENT", vnum, pfs_date, "EOT"))

    # Follow-up visits every 3 months for up to 36 months from rfst
    fu_start = pfs_date + timedelta(days=30)
    fu_end = rfst + timedelta(days=int(36 * 30.44))
    fu_date = fu_start
    fu_num = 1
    while fu_date <= fu_end:
        vnum += 1
        visits.append((
            f"FOLLOW-UP {fu_num}",
            vnum,
            fu_date,
            "FU"
        ))
        fu_date += timedelta(days=int(3 * 30.44))
        fu_num += 1
        if fu_num > 12:
            break

    return visits


# ---------------------------------------------------------------------------
# Step 4: EX domain
# ---------------------------------------------------------------------------

def build_ex(subjects):
    rows = []
    seq = 1

    for s in subjects:
        if s["_never_started"]:
            continue

        rfst = s["_rfstdtc_date"]
        pfs_date = s["_pfs_date"]
        pfs_months = s["_pfs_months"]
        n_cycles = min(max(1, math.ceil(pfs_months / (28 / 30.44))), 12)
        armcd = s["ARMCD"]

        # Fulvestrant doses
        # C1D1 and C1D15 (loading doses), then D1 of each subsequent cycle
        fulv_dates = [rfst, rfst + timedelta(days=14)]
        for cyc in range(2, n_cycles + 1):
            cyc_date = rfst + timedelta(days=(cyc - 1) * 28)
            if cyc_date <= pfs_date:
                fulv_dates.append(cyc_date)

        for d in fulv_dates:
            rows.append({
                "STUDYID": STUDYID,
                "DOMAIN": "EX",
                "USUBJID": s["USUBJID"],
                "EXSEQ": seq,
                "EXTRT": "FULVESTRANT",
                "EXDOSE": 500,
                "EXDOSU": "mg",
                "EXDOSFRM": "INJECTION",
                "EXDOSFRQ": "ONCE",
                "EXROUTE": "INTRAMUSCULAR",
                "EXSTDTC": iso(d),
                "EXENDTC": iso(d),
                "EXSTDY": study_day(d, rfst),
                "EXENDY": study_day(d, rfst),
            })
            seq += 1

        # Everolimus or Placebo: continuous daily, represented as
        # one record per cycle (start=CycleD1, end=next CycleD1-1)
        ev_drug = "EVEROLIMUS" if armcd == "FULEV" else "PLACEBO"
        for cyc in range(1, n_cycles + 1):
            cyc_start = rfst + timedelta(days=(cyc - 1) * 28)
            cyc_end_raw = rfst + timedelta(days=cyc * 28 - 1)
            cyc_end = min(cyc_end_raw, pfs_date)
            if cyc_start > pfs_date:
                break
            rows.append({
                "STUDYID": STUDYID,
                "DOMAIN": "EX",
                "USUBJID": s["USUBJID"],
                "EXSEQ": seq,
                "EXTRT": ev_drug,
                "EXDOSE": 10,
                "EXDOSU": "mg",
                "EXDOSFRM": "TABLET",
                "EXDOSFRQ": "QD",
                "EXROUTE": "ORAL",
                "EXSTDTC": iso(cyc_start),
                "EXENDTC": iso(cyc_end),
                "EXSTDY": study_day(cyc_start, rfst),
                "EXENDY": study_day(cyc_end, rfst),
            })
            seq += 1

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Step 5: LB domain
# ---------------------------------------------------------------------------

def build_lb(subjects):
    rows = []
    lb_seq = 1

    for s in subjects:
        if s["_never_started"]:
            continue

        rfst = s["_rfstdtc_date"]
        is_ae = s["IS_AE_DISC"]
        visits = build_visits(s)

        for visit_name, visitnum, vdate, vtype in visits:
            if vtype == "FU":
                continue   # minimal labs in follow-up

            is_baseline = (vtype == "SCREENING")
            is_lipid_visit = vtype in ("SCREENING", "TREATMENT", "IMAGING", "EOT")

            for (tcd, tname, tcat, lo, hi, unit, dist) in LAB_DEFS:
                if tcd in LIPID_TESTS and not is_lipid_visit:
                    continue

                val = sample_lab(dist, 1, mtor_toxicity=is_ae, test_code=tcd)[0]
                val_r = round(val, 2)
                nr = nrind(val_r, lo, hi)

                rows.append({
                    "STUDYID": STUDYID,
                    "DOMAIN": "LB",
                    "USUBJID": s["USUBJID"],
                    "LBSEQ": lb_seq,
                    "LBTESTCD": tcd,
                    "LBTEST": tname,
                    "LBCAT": tcat,
                    "LBORRES": str(val_r),
                    "LBORRESU": unit,
                    "LBSTRESC": str(val_r),
                    "LBSTRESN": val_r,
                    "LBSTRESU": unit,
                    "LBNRIND": nr,
                    "LBBLFL": "Y" if is_baseline else "",
                    "VISIT": visit_name,
                    "VISITNUM": visitnum,
                    "LBDTC": iso(vdate),
                    "LBDY": study_day(vdate, rfst),
                })
                lb_seq += 1

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Step 6: VS domain
# ---------------------------------------------------------------------------

def build_vs(subjects):
    rows = []
    vs_seq = 1

    for s in subjects:
        if s["_never_started"]:
            continue

        rfst = s["_rfstdtc_date"]
        # Generate a stable baseline for each subject, then vary per visit
        base = {
            tcd: rng.normal(mean, sd)
            for tcd, _tname, _unit, _dist, mean, sd in VS_DEFS
        }

        visits = build_visits(s)

        for visit_name, visitnum, vdate, vtype in visits:
            if vtype == "FU":
                continue

            for (tcd, tname, unit, dist, mean, sd) in VS_DEFS:
                # Visit-to-visit variation: ±10% of SD
                visit_val = rng.normal(
                    base.get(tcd, mean), sd * 0.15
                )
                # Weight decreases slightly over time with mTOR effects
                if tcd == "WEIGHT" and s["ARMCD"] == "FULEV":
                    visit_val -= rng.uniform(0, 2) * (visitnum / 20.0)
                visit_val = round(max(visit_val, 0.1), 1)

                rows.append({
                    "STUDYID": STUDYID,
                    "DOMAIN": "VS",
                    "USUBJID": s["USUBJID"],
                    "VSSEQ": vs_seq,
                    "VSTESTCD": tcd,
                    "VSTEST": tname,
                    "VSORRES": str(visit_val),
                    "VSORRESU": unit,
                    "VSSTRESC": str(visit_val),
                    "VSSTRESN": visit_val,
                    "VSSTRESU": unit,
                    "VISIT": visit_name,
                    "VISITNUM": visitnum,
                    "VSDTC": iso(vdate),
                    "VSDY": study_day(vdate, rfst),
                })
                vs_seq += 1

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Step 7: TU + RS domains
# ---------------------------------------------------------------------------

def sod_trajectory(bestresp, baseline_sod, n_assessments):
    """
    Return list of SOD values at each assessment (including baseline).
    Trajectory follows assigned best response category.
    """
    sods = [baseline_sod]
    nadir = baseline_sod

    for i in range(1, n_assessments):
        prev = sods[-1]
        if bestresp == "CR":
            # Rapid disappearance by assessment 2
            if i == 1:
                new = prev * rng.uniform(0.35, 0.55)
            elif i == 2:
                new = 0.0
            else:
                new = 0.0
        elif bestresp == "PR":
            if i == 1:
                new = prev * rng.uniform(0.45, 0.65)
            else:
                new = prev * rng.uniform(0.92, 1.08)
        elif bestresp == "SD":
            new = prev * rng.uniform(0.88, 1.15)
        else:  # PD
            if i < n_assessments - 1:
                new = prev * rng.uniform(0.95, 1.10)
            else:
                # Last assessment: show progression
                new = max(nadir * 1.25, nadir + 5.0) * rng.uniform(1.0, 1.3)

        new = max(0.0, round(new, 1))
        nadir = min(nadir, new) if new > 0 else nadir
        sods.append(new)

    return sods


def build_tu_rs(subjects):
    tu_rows = []
    rs_rows = []
    tu_seq = 1
    rs_seq = 1

    for s in subjects:
        if s["_never_started"] or s["MEASFL"] == "N":
            continue

        rfst = s["_rfstdtc_date"]
        bestresp = s["BESTRESP"]

        # Imaging visits only
        visits = build_visits(s)
        imaging_visits = [
            v for v in visits
            if v[3] in ("SCREENING", "IMAGING", "EOT")
        ]
        if len(imaging_visits) < 2:
            imaging_visits = [
                v for v in visits
                if v[3] in ("SCREENING", "TREATMENT", "IMAGING", "EOT")
            ][:4]

        n_assessments = len(imaging_visits)
        if n_assessments == 0:
            continue

        # Baseline SOD
        baseline_sod = max(10.0, round(rng.normal(45.0, 20.0), 1))
        sods = sod_trajectory(bestresp, baseline_sod, n_assessments)

        # Up to 3 target lesions; split SOD proportionally
        n_lesions = int(rng.integers(1, 4))
        lesion_locs = rng.choice(TUMOR_LOCS, n_lesions, replace=False).tolist()

        # Proportions that sum to 1
        props = rng.dirichlet(np.ones(n_lesions)).tolist()

        for assess_i, (vname, vnum, vdate, vtype) in enumerate(imaging_visits):
            sod = sods[assess_i]
            is_baseline = (vtype == "SCREENING")

            # Response at this timepoint
            if bestresp == "CR" and assess_i >= 2:
                tp_resp = "CR"
            elif bestresp == "PR" and sod <= baseline_sod * 0.7:
                tp_resp = "PR"
            elif bestresp == "PD" and assess_i == n_assessments - 1:
                tp_resp = "PD"
            elif bestresp == "NE":
                tp_resp = "NE"
            else:
                tp_resp = "SD"

            for lis, loc in enumerate(lesion_locs):
                diameter = round(sod * props[lis], 1) if sod > 0 else 0.0
                tu_rows.append({
                    "STUDYID": STUDYID,
                    "DOMAIN": "TU",
                    "USUBJID": s["USUBJID"],
                    "TUSEQ": tu_seq,
                    "TULNKID": f"RS{rs_seq:05d}",
                    "TUTESTCD": "DIAMETER",
                    "TUTEST": "Diameter",
                    "TUORRES": str(diameter),
                    "TUSTRESC": str(diameter),
                    "TUSTRESN": diameter,
                    "TUSTRESU": "mm",
                    "TUTRLGR": "TARGET",
                    "TUMETHOD": "CT SCAN",
                    "TULOC": loc,
                    "TUEVAL": "INVESTIGATOR",
                    "TUBLFL": "Y" if is_baseline else "",
                    "VISIT": vname,
                    "VISITNUM": vnum,
                    "TUDTC": iso(vdate),
                    "TUDY": study_day(vdate, rfst),
                })
                tu_seq += 1

            # Overall response at this timepoint
            rs_rows.append({
                "STUDYID": STUDYID,
                "DOMAIN": "RS",
                "USUBJID": s["USUBJID"],
                "RSSEQ": rs_seq,
                "RSTESTCD": "OVRLRESP",
                "RSTEST": "Overall Response",
                "RSORRES": tp_resp,
                "RSSTRESC": tp_resp,
                "RSEVAL": "INVESTIGATOR",
                "RSEPOC": "OVERALL STUDY",
                "VISIT": vname,
                "VISITNUM": vnum,
                "RSDTC": iso(vdate),
                "RSDY": study_day(vdate, rfst),
            })
            rs_seq += 1

    return pd.DataFrame(tu_rows), pd.DataFrame(rs_rows)


# ---------------------------------------------------------------------------
# Step 8: ADSL + ADTTE
# ---------------------------------------------------------------------------

def build_adsl(subjects):
    rows = []
    for s in subjects:
        rows.append({
            "STUDYID": s["STUDYID"],
            "USUBJID": s["USUBJID"],
            "SUBJID": s["SUBJID"],
            "SITEID": s["SITEID"],
            "ARMCD": s["ARMCD"],
            "ARM": s["ARM"],
            "TRT01P": s["ARM"],
            "TRT01A": s["ARM"],
            "AGE": s["AGE"],
            "AGEU": s["AGEU"],
            "SEX": s["SEX"],
            "RACE": s["RACE"],
            "ETHNIC": s["ETHNIC"],
            "COUNTRY": s["COUNTRY"],
            "RANDDT": s["RANDDT"],
            "TRTSDT": s["RFSTDTC"] if not s["_never_started"] else "",
            "TRTEDT": s["RFENDTC"] if not s["_never_started"] else "",
            "ITTFL": s["ITTFL"],
            "SAFFL": s["SAFFL"],
            "EFFFL": s["EFFFL"],
            "ECOG": s["ECOG"],
            "MEASFL": s["MEASFL"],
            "PRIORCH": s["PRIORCH"],
            "BESTRESP": s["BESTRESP"],
            "CBR": s["CBR"],
            "PFSINV": s["PFSINV"],
            "PFSCNSR": s["PFSCNSR"],
            "PFSDT": s["PFSDT"],
            "OSINV": s["OSINV"],
            "OSCNSR": s["OSCNSR"],
            "OSDT": s["OSDT"],
            "DCSREAS": s["DCSREAS"],
            "EOSSTT": (
                "NEVER STARTED" if s["_never_started"]
                else "COMPLETED" if s["DCSREAS"] == "COMPLETED"
                else "DISCONTINUED"
            ),
        })
    return pd.DataFrame(rows)


def build_adtte(subjects):
    rows = []
    for s in subjects:
        if s["_never_started"]:
            continue
        for param, aval, cnsr, adt, evdesc in [
            (
                "PFS", s["PFSINV"], s["PFSCNSR"], s["PFSDT"],
                "PROGRESSION OR DEATH" if s["PFSCNSR"] == 0 else "CENSORED"
            ),
            (
                "OS", s["OSINV"], s["OSCNSR"], s["OSDT"],
                "DEATH" if s["OSCNSR"] == 0 else "CENSORED"
            ),
        ]:
            rows.append({
                "STUDYID": s["STUDYID"],
                "USUBJID": s["USUBJID"],
                "ARMCD": s["ARMCD"],
                "ARM": s["ARM"],
                "PARAMCD": param,
                "PARAM": (
                    "Progression-Free Survival"
                    if param == "PFS"
                    else "Overall Survival"
                ),
                "AVAL": aval,
                "AVALU": "MONTHS",
                "CNSR": cnsr,
                "EVNTDESC": evdesc,
                "STARTDT": s["RFSTDTC"],
                "ADT": adt,
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("Building subject roster...")
    subjects = build_subjects()

    print("Writing DM.csv...")
    dm = build_dm(subjects)
    dm.to_csv(os.path.join(OUT_DIR, "DM.csv"), index=False)
    print(f"  {len(dm):,} rows")

    print("Writing EX.csv...")
    ex = build_ex(subjects)
    ex.to_csv(os.path.join(OUT_DIR, "EX.csv"), index=False)
    print(f"  {len(ex):,} rows")

    print("Writing LB.csv (this may take a moment)...")
    lb = build_lb(subjects)
    lb.to_csv(os.path.join(OUT_DIR, "LB.csv"), index=False)
    print(f"  {len(lb):,} rows")

    print("Writing VS.csv...")
    vs = build_vs(subjects)
    vs.to_csv(os.path.join(OUT_DIR, "VS.csv"), index=False)
    print(f"  {len(vs):,} rows")

    print("Writing TU.csv and RS.csv...")
    tu, rs = build_tu_rs(subjects)
    tu.to_csv(os.path.join(OUT_DIR, "TU.csv"), index=False)
    rs.to_csv(os.path.join(OUT_DIR, "RS.csv"), index=False)
    print(f"  TU: {len(tu):,} rows  |  RS: {len(rs):,} rows")

    print("Writing ADSL.csv...")
    adsl = build_adsl(subjects)
    adsl.to_csv(os.path.join(OUT_DIR, "ADSL.csv"), index=False)
    print(f"  {len(adsl):,} rows")

    print("Writing ADTTE.csv...")
    adtte = build_adtte(subjects)
    adtte.to_csv(os.path.join(OUT_DIR, "ADTTE.csv"), index=False)
    print(f"  {len(adtte):,} rows")

    # Quick verification summary
    print("\n--- Verification summary ---")
    n_fulev = len(dm[dm.ARMCD == "FULEV"])
    n_fulpl = len(dm[dm.ARMCD == "FULPL"])
    print(
        f"DM:    {len(dm)} subjects  "
        f"(FULEV={n_fulev}, FULPL={n_fulpl})"
    )

    eff = adsl[adsl.EFFFL == "Y"]
    for arm, grp in eff.groupby("ARMCD"):
        events = (grp.PFSCNSR == 0).sum()
        orr = grp.BESTRESP.isin(["CR", "PR"]).mean()
        cbr = grp.CBR.mean()
        print(
            f"{arm}: n={len(grp)}  PFS events={events}  "
            f"ORR={orr:.1%}  CBR={cbr:.1%}"
        )

    print(f"\nOutput written to: {OUT_DIR}")


if __name__ == "__main__":
    main()
