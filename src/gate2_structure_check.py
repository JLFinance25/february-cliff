# Structure check (PREREG 4.6, job E1 from the main session, Oct 18, 2026). Shed files only, outcome-free: no linking to
# filings, no workload, no outcomes; no BIN is printed. Cleans both files with the frozen functions and the shed strings the main
# session chose (DOB NOW work_type "Sidewalk Shed"; legacy permit_subtype "SH" with no permit_type list), pools rows whose start
# falls in [Feb 21, 2015, Dec 31, 2025], and prints the cleaning counts, the share of terms of 120 days or less, the median term,
# both renewal-visibility numbers, and the branch from choose_branch called with the INCLUSIVE number (deviation D2).
# Run: .venv/bin/python -I src/gate2_structure_check.py
import glob
import json
import pathlib
import sys

import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gate2_link as L

ROOT = pathlib.Path(__file__).resolve().parent.parent


def load(dataset, cols):
    parts = [pd.DataFrame(json.load(open(f)), columns=cols) for f in sorted(glob.glob(str(ROOT / "data" / "raw" / f"{dataset}_*_page*.json")))]
    return pd.concat(parts, ignore_index=True)


def main():
    dn = load("rbx6-tga4", L.DOBNOW_COLS)
    lg = load("ipu4-2q9a", L.LEGACY_COLS)
    print(f"rows read: DOB NOW {len(dn):,}, legacy {len(lg):,}")
    # the one stated legacy date format, chosen from the FORMAT ONLY (digits shown as 9, letters as a)
    for c in ("filing_date", "issuance_date", "expiration_date"):
        sh = L.date_shape_counts(lg[c])
        print(f"legacy {c} shapes:", {k: int(v) for k, v in sh.head(4).items()}, f"(+{max(len(sh) - 4, 0)} more shapes)")
    a, qa = L.clean_dobnow(dn, ["Sidewalk Shed"])
    fmt = "%m/%d/%Y"
    b, qb = L.clean_legacy(lg, [], shed_permit_subtypes=["SH"], date_format=fmt)
    print("DOB NOW cleaning:", qa)
    print("legacy cleaning:", qb)
    both = L.combine_intervals(a, b)
    pool = both[(both["start"] >= "2015-02-21") & (both["start"] <= "2025-12-31")]
    chk = L.structure_check(both)
    print("rows after pooling both files and collapsing identical rows:", len(both))
    print("structure check (pool: start Feb 21, 2015 to Dec 31, 2025):", chk)
    inc = dict(chk); inc["renewal_visibility"] = chk["renewal_visibility_incl_overlap_NOT_USED"]
    print("branch (D2, inclusive number):", L.choose_branch(inc), "| for reference, literal number:", L.choose_branch(chk))
    return chk, qa, qb


if __name__ == "__main__":
    main()
