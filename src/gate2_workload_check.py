# Check of the workload series on the REAL facade file, allowed before the code freeze by the main session's rule: only
# daily counts of UNSAFE Initial filings by filing date are used (no repair duration, no gap between filings, no shed data).
# Compares the trailing-90-day counts on Mar 1 of 2015 to 2025 with the values listed in PREREG.md section 1
# (115, 132, 486, 330, 395, 385, 42, 732, 515, 471, 182) and reports a few exposure-only summaries.
# Run: .venv/bin/python -I src/gate2_workload_check.py
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gate2_link as L

ROOT = pathlib.Path(__file__).resolve().parent.parent
EXPECTED = [115, 132, 486, 330, 395, 385, 42, 732, 515, 471, 182]   # PREREG section 1, Mar 1 of 2015 to 2025


def main():
    df = pd.read_parquet(ROOT / "data" / "processed" / "facades_clean.parquet",
                         columns=["filing_type", "filing_status", "filing_date", "submitted_on", "group"])
    wl = L.Workload(df)
    dates = pd.Series([pd.Timestamp(f"{y}-03-01") for y in range(2015, 2026)])
    got = np.rint(wl.trailing(dates) * L.WAVE_UNIT).astype(int)
    print("Mar 1 trailing-90 counts, 2015 to 2025")
    print("  code    :", got.tolist())
    print("  PREREG  :", EXPECTED)
    print("  match   :", list(got) == EXPECTED)
    allx = wl.trailing(pd.Series(pd.date_range("2015-02-01", "2025-12-31"))) * L.WAVE_UNIT
    print(f"  all days Feb 2015 to Dec 2025: median {np.median(allx):.0f} (PREREG 106), 90th percentile {np.quantile(allx, 0.9):.0f} (PREREG 397)")
    mc = wl.monthly_counts()
    feb = {y: int(mc.get((y, 2), 0)) for y in range(2015, 2027)}
    print("  citywide UNSAFE Initial filings in February:", feb)
    print("  (PREREG section 1 lists: 408, 266, 305, 660, 405, 394 for the group-deadline Februaries; 83, 26, 230, 25, 103, 46 for the others)")
    return got.tolist() == EXPECTED


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
