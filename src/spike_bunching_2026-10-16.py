# Throwaway spike: monthly counts of initial FISP filings by sub-cycle group (last digit of block).
# Exploratory test run Oct 16, 2026, BEFORE any pre-registration. Kept as the record of how Gate 1 was checked.
# Aggregates only, nothing saved. Sub-cycle groups are UNVERIFIED (A: 4,5,6,9; B: 0,7,8; C: 1,2,3).
import json, urllib.parse, urllib.request
B = "https://data.cityofnewyork.us/resource/xubg-57si.json"
GROUPS = {"A(4569)": "4569", "B(078)": "078", "C(123)": "123"}
def q(params):
    url = B + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=90) as r:
        return json.load(r)
for cyc in ["8", "9"]:
    print(f"=== Cycle {cyc}, Initial filings, by month of filing_date ===")
    for g, digits in GROUPS.items():
        like = " OR ".join(f"block like '%{d}'" for d in digits)
        rows = q({"$select": "date_trunc_ym(filing_date) as m, count(*) as n",
                  "$where": f"cycle='{cyc}' AND filing_type='Initial' AND ({like})",
                  "$group": "m", "$order": "m", "$limit": "500"})
        nodate = sum(int(r["n"]) for r in rows if "m" not in r)
        rows = [r for r in rows if "m" in r]
        tot = sum(int(r["n"]) for r in rows)
        top = sorted(rows, key=lambda r: -int(r["n"]))[:4]
        print(f"{g}: total {tot} (no date {nodate}); first {rows[0]['m'][:7]} last {rows[-1]['m'][:7]}")
        print("   busiest months:", ", ".join(f"{r['m'][:7]}={r['n']}" for r in top))
        # by quarter, compact
        qs = {}
        for r in rows:
            y, mo = int(r["m"][:4]), int(r["m"][5:7])
            k = f"{y}Q{(mo-1)//3+1}"
            qs[k] = qs.get(k, 0) + int(r["n"])
        print("   by quarter:", " ".join(f"{k}:{v}" for k, v in qs.items()))
