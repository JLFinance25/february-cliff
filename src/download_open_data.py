# Download PLUTO and the two shed-permit datasets from NYC Open Data through the free Socrata API (no key, token or
# account). Same gentle pattern as download_xubg_57si.py: 50,000 rows per request, 2-second pause, stable order.
# DATA MINIMIZATION: only the allowlisted columns are requested with $select, so owner, applicant, permittee,
# inspector and superintendent names, addresses, phone numbers, job descriptions and cost columns are never downloaded.
# The whole dataset is downloaded (no filter on work type: the shed code strings are chosen later in the code-list step).
# Raw pages are saved byte for byte to data/raw/ (gitignored) and never edited; a meta file records counts, hashes and
# the metadata. A download is not an analysis: this script prints only file names, sizes and the whole-dataset row count.
# Terms: data/raw/SOURCES.md section 2 (NYC Open Data Law) and the per-dataset entries. Run after the code freeze:
#   .venv/bin/python -I src/download_open_data.py pluto|rbx6-tga4|ipu4-2q9a
import datetime as dt
import hashlib
import json
import pathlib
import sys
import time
import urllib.parse
import urllib.request

HOST = "https://data.cityofnewyork.us"
PAGE = 50000
PAUSE = 2
UA = {"User-Agent": "facade-calendar research script (private GitHub repo JLFinance25/facade-calendar)"}
RAW = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw"

# Allowlists (main session, Oct 17, 2026; field names confirmed against each dataset's own field list before the pull).
DATASETS = {
    "rbx6-tga4": ["bin", "block", "lot", "work_type", "permit_status", "filing_reason", "work_permit", "sequence_number",
                  "approved_date", "issued_date", "expired_date"],
    "ipu4-2q9a": ["bin__", "permit_type", "permit_subtype", "permit_status", "filing_date", "issuance_date", "expiration_date"],
    "64uk-42ks": ["borough", "block", "lot", "bbl", "ownertype", "numfloors"],     # PLUTO
}
ALIASES = {"pluto": "64uk-42ks"}


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r:
        return r.read()


def main(arg):
    dataset = ALIASES.get(arg, arg)
    cols = DATASETS[dataset]
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    meta_before = json.loads(get(f"{HOST}/api/views/{dataset}.json"))
    fields = {c["fieldName"] for c in meta_before["columns"]}
    missing = [c for c in cols if c not in fields]
    if missing:
        raise SystemExit(f"Columns not in the dataset's field list: {missing}")
    n_before = int(json.loads(get(f"{HOST}/resource/{dataset}.json?$select=count(*)"))[0]["count"])
    print(f"{dataset}: {n_before} rows in the whole dataset; rowsUpdatedAt {meta_before['rowsUpdatedAt']}")
    select = urllib.parse.quote(",".join(cols))

    pages, offset = [], 0
    while offset < n_before:
        url = f"{HOST}/resource/{dataset}.json?$select={select}&$order=:id&$limit={PAGE}&$offset={offset}"
        body = get(url)
        n_rows = len(json.loads(body))
        out = RAW / f"{dataset}_{today}_page{len(pages):02d}.json"
        out.write_bytes(body)
        pages.append({"file": out.name, "rows": n_rows, "offset": offset, "bytes": len(body),
                      "sha256": hashlib.sha256(body).hexdigest()})
        print(f"page {len(pages) - 1}: {n_rows} rows, {len(body):,} bytes -> {out.name}")
        offset += PAGE
        if n_rows < PAGE:
            break
        time.sleep(PAUSE)

    meta_after = json.loads(get(f"{HOST}/api/views/{dataset}.json"))
    n_after = int(json.loads(get(f"{HOST}/resource/{dataset}.json?$select=count(*)"))[0]["count"])
    saved = sum(p["rows"] for p in pages)
    record = {
        "dataset": dataset, "name": meta_before.get("name"), "pulled_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "columns_requested": cols, "count_before": n_before, "count_after": n_after, "rows_saved": saved,
        "rowsUpdatedAt_before": meta_before["rowsUpdatedAt"], "rowsUpdatedAt_after": meta_after["rowsUpdatedAt"],
        "license_in_metadata": meta_before.get("license"), "attribution": meta_before.get("attribution"),
        "description_first_300_chars": (meta_before.get("description") or "")[:300],
        "pages": pages,
    }
    (RAW / f"{dataset}_{today}_meta.json").write_text(json.dumps(record, indent=1))
    ok = saved == n_before == n_after and meta_before["rowsUpdatedAt"] == meta_after["rowsUpdatedAt"]
    print(f"saved {saved} rows in {len(pages)} file(s), {sum(p['bytes'] for p in pages):,} bytes; count before/after {n_before}/{n_after}; same snapshot: {ok}")
    if not ok:
        raise SystemExit("Row counts or update time changed during the download; re-run before using the files.")


if __name__ == "__main__":
    main(sys.argv[1])
