# Download the full DOB NOW facade-filings file (NYC Open Data xubg-57si) through the free Socrata API.
# No key, token or account. Terms check: data/raw/SOURCES.md section 2.
# Raw API responses are saved byte for byte, never edited, to data/raw/ (gitignored: the file names owners
# and inspectors). Cleaning happens in src/process_facades.py, which writes to data/processed/.
# Run: python3 src/download_xubg_57si.py
import datetime as dt, json, pathlib, time, urllib.request

DATASET = "xubg-57si"
HOST = "https://data.cityofnewyork.us"
PAGE = 50000          # rows per request; the API's usual maximum
PAUSE = 2             # seconds between requests, to stay gentle on the server
UA = {"User-Agent": "facade-calendar research script (private GitHub repo JLFinance25/facade-calendar)"}
RAW = pathlib.Path(__file__).resolve().parent.parent / "data" / "raw"


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=180) as r:
        return r.read()


def main():
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    meta_before = json.loads(get(f"{HOST}/api/views/{DATASET}.json"))
    n_before = int(json.loads(get(f"{HOST}/resource/{DATASET}.json?$select=count(*)"))[0]["count"])
    print(f"API says {n_before} rows; rowsUpdatedAt {meta_before['rowsUpdatedAt']}")

    pages = []
    offset = 0
    while offset < n_before:
        # :id is the portal's internal row id; ordering by it makes paging stable.
        url = f"{HOST}/resource/{DATASET}.json?$order=:id&$limit={PAGE}&$offset={offset}"
        body = get(url)
        rows = json.loads(body)
        out = RAW / f"{DATASET}_{today}_page{len(pages):02d}.json"
        out.write_bytes(body)
        pages.append({"file": out.name, "rows": len(rows), "offset": offset, "bytes": len(body)})
        print(f"page {len(pages)-1}: {len(rows)} rows -> {out.name}")
        offset += PAGE
        if len(rows) < PAGE:
            break
        time.sleep(PAUSE)

    meta_after = json.loads(get(f"{HOST}/api/views/{DATASET}.json"))
    n_after = int(json.loads(get(f"{HOST}/resource/{DATASET}.json?$select=count(*)"))[0]["count"])
    saved = sum(p["rows"] for p in pages)
    record = {
        "dataset": DATASET,
        "pulled_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "count_before": n_before, "count_after": n_after, "rows_saved": saved,
        "rowsUpdatedAt_before": meta_before["rowsUpdatedAt"], "rowsUpdatedAt_after": meta_after["rowsUpdatedAt"],
        "license_in_metadata": meta_before.get("license"), "attribution": meta_before.get("attribution"),
        "columns_in_metadata": [{"field": c["fieldName"], "type": c["dataTypeName"]} for c in meta_before["columns"]],
        "pages": pages,
    }
    (RAW / f"{DATASET}_{today}_meta.json").write_text(json.dumps(record, indent=1))
    ok = saved == n_before == n_after and meta_before["rowsUpdatedAt"] == meta_after["rowsUpdatedAt"]
    print(f"saved {saved} rows; count before/after {n_before}/{n_after}; same snapshot: {ok}")
    if not ok:
        raise SystemExit("Row counts or update time changed during the download; re-run before using the file.")


if __name__ == "__main__":
    main()
