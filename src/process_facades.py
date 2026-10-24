# First processing step for the DOB NOW facade-filings file (xubg-57si).
# Reads the raw API pages in data/raw/ (never edited) and writes data/processed/facades_clean.parquet.
#
# ALLOWLIST: only the columns below are kept. Every other column is dropped the moment each row is read, so
# it never reaches a table, a printout or a chart. Dropped on purpose (personal or free text):
#   inspector (qewi_*): name, business name, street, city, state, zip, license number
#   owner (owner_*): name, business name, street, city, state, zip
#   house_no, street_name (street address), comments (free text; can hold names, phones, emails)
#   the three penalty amounts (not needed yet), the two "other description" free-text wall columns
# There is no height or stories column in this dataset.
KEEP = [
    "tr6_no",            # DOB filing number; its letter (A/B/C) is DOB's own sub-cycle label (used only as a check)
    "control_no",        # DOB control number (one per building-cycle report series)
    "filing_type",       # Initial / Amended / Subsequent / Auto-Generated
    "cycle",             # 6 to 10
    "bin", "borough", "block", "lot",   # building ID and tax block/lot (lot kept so PLUTO can be joined later)
    "sequence_no",
    "submitted_on", "filing_date", "prior_cycle_filing_date", "field_inspection_completed_date", "qewi_signed_date",
    "filing_status",     # rating on this filing: SAFE / SWARMP / UNSAFE / No Report Filed
    "current_status",    # building's latest status (UNSAFE falls to SAFE after an accepted amended report)
    "prior_status",      # status in the prior cycle
    "exterior_wall_type_s_", "exterior_wall_material_s_",
]
DATE_COLS = ["submitted_on", "filing_date", "prior_cycle_filing_date", "field_inspection_completed_date",
             "qewi_signed_date"]

import json, pathlib, sys
import pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from facade_common import group_of_block

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW, OUT = ROOT / "data" / "raw", ROOT / "data" / "processed"


def main():
    meta = json.loads(next(RAW.glob("xubg-57si_*_meta.json")).read_text())
    rows = []
    for page in meta["pages"]:
        for r in json.loads((RAW / page["file"]).read_text()):
            rows.append({k: r.get(k) for k in KEEP})        # allowlist applied here, row by row
    df = pd.DataFrame(rows, columns=KEEP)
    assert len(df) == meta["rows_saved"], "row count differs from the download record"

    for c in DATE_COLS:
        parsed = pd.to_datetime(df[c], errors="coerce")
        assert parsed.notna().sum() == df[c].notna().sum(), f"{c}: some dates did not parse"
        df[c] = parsed
    df["cycle"] = pd.to_numeric(df["cycle"], errors="coerce").astype("Int64")
    # sequence_no has 7 typos in the raw file ("0.7" x4, "O4" x3); they are not repaired, "O4" becomes blank.
    df["sequence_no"] = pd.to_numeric(df["sequence_no"], errors="coerce")

    # Deadline group from the last digit of the block (DOB's rule, see facade_common.py).
    df["block_digit"] = df["block"].str[-1]
    df["group"] = df["block"].map(group_of_block)
    # DOB's own sub-cycle letter inside the filing number, e.g. "...-7C-..." (Cycle 6 shows "NA": no groups).
    df["tr6_letter"] = df["tr6_no"].str.extract(r"^TR6-\d+-(?:\d+|NA)([A-Za-z]?)-")[0].replace("", pd.NA)
    df["group_matches_tr6"] = (df["group"] == df["tr6_letter"]).where(df["tr6_letter"].notna())

    OUT.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUT / "facades_clean.parquet", index=False)
    print(f"wrote {OUT / 'facades_clean.parquet'}: {len(df)} rows x {df.shape[1]} columns")
    print("columns:", ", ".join(df.columns))
    print("rows by cycle:", df["cycle"].value_counts(dropna=False).sort_index().to_dict())
    print("rows with no group (block missing/odd):", int(df["group"].isna().sum()))
    chk = df[df["tr6_letter"].notna()]
    print(f"DOB filing-number letter agrees with block-digit group: {int(chk['group_matches_tr6'].sum())} of {len(chk)}")


if __name__ == "__main__":
    main()
