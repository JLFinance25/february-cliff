# SIMULATED data for testing the Gate 2 code (PREREG section 5: "tested on simulated data before any shed row or any
# repair duration is opened"). Nothing here reads a real file. The simulated facade table has the same columns as
# data/processed/facades_clean.parquet (the ones the Gate 2 code uses); the simulated shed tables have the same columns
# as the allowlisted DOB NOW and legacy shed-permit pulls, with the legacy dates as text.
#
# The planted effect enters through the hazard: log hazard of clearing (Family 1) or of the shed ending (Family 2)
# = baseline(step) + log(planted HR) * workload + other effects. Workload here is computed by a brute-force method that
# shares no code with gate2_link.Workload, so agreement between the two is a real check.
# Drafted by Claude (AI); directed and approved by Jayden Ling.
import numpy as np
import pandas as pd

from facade_common import WINDOWS

BOROUGHS = ["Manhattan", "Brooklyn", "Bronx", "Queens", "Staten Island"]
BASE_LOG_HAZ = {1: np.log(0.03), 2: np.log(0.05), 3: np.log(0.05), 4: np.log(0.05), 5: np.log(0.05), 6: np.log(0.05)}
WALLS = ["MASONRY", "MASONRY; TERRA COTTA", "OTHER", "CONCRETE; MASONRY", None]


def brute_workload(dates, query_dates, lookback=90, scale=400.0):
    """Count of `dates` in (q - lookback, q], by sorted search; independent of gate2_link.Workload."""
    d = np.sort(np.asarray(dates, dtype="datetime64[D]").astype("int64"))
    q = np.asarray(query_dates, dtype="datetime64[D]").astype("int64")
    return (np.searchsorted(d, q, side="right") - np.searchsorted(d, q - lookback, side="right")) / scale


def brute_daily(dates, start, end, lookback=90, scale=400.0):
    days = np.arange(np.datetime64(start, "D"), np.datetime64(end, "D") + 1)
    return days, brute_workload(dates, days, lookback, scale)


def sim_facades(seed=1, n_buildings=5600, planted_hr=0.75, late_penalty=0.0, tau=0.0, n_surges=10, p_unsafe=0.55,
                workload_hr_early_only=None):
    """Simulated facade-filings table (processed-file columns). Returns (facades, truth).

    planted_hr: hazard ratio of clearing per wave unit of workload on the filing date (1.0 = null).
    late_penalty: extra log hazard for Last-minute and Past-deadline filers (the 'slow owners' story, H2).
    tau: SD of a shared per-quarter shock to the log hazard (a shock that hits every building at once).
    workload_hr_early_only: if given, the planted HR applies to Early filers only (others get HR 1).
    """
    rng = np.random.default_rng(seed)
    nb = n_buildings
    bins = rng.choice(np.arange(1000000, 5900000), size=nb, replace=False)
    block = rng.integers(1, 9999, size=nb)
    lot = rng.integers(1, 200, size=nb)
    boro = rng.choice(BOROUGHS, size=nb, p=[0.5, 0.15, 0.13, 0.2, 0.02])
    wall = rng.choice(np.array(WALLS, dtype=object), size=nb)
    group_digit = {d: g for g, ds in {"A": "4569", "B": "078", "C": "123"}.items() for d in ds}
    grp = np.array([group_digit[str(b)[-1]] for b in block])
    surge_days = pd.to_datetime("2015-03-01") + pd.to_timedelta(rng.integers(0, 3600, size=n_surges), unit="D")

    rows = []
    for cycle in (8, 9):
        unsafe = rng.random(nb) < p_unsafe
        dl = np.array([pd.Timestamp(WINDOWS[cycle][g][1]) for g in grp], dtype="datetime64[D]")
        u = rng.random(nb)
        off = np.where(u < 0.05, -730 - rng.integers(1, 300, nb),
              np.where(u < 0.30, -rng.integers(29, 730, nb),
              np.where(u < 0.62, -rng.integers(0, 29, nb), rng.integers(1, 400, nb))))
        fdate = dl + off.astype("timedelta64[D]")
        surge = rng.random(nb) < 0.12
        sd = surge_days.values[rng.integers(0, n_surges, nb)] + rng.integers(-7, 8, nb).astype("timedelta64[D]")
        fdate = np.where(surge, sd.astype("datetime64[D]"), fdate).astype("datetime64[D]")
        for i in range(nb):
            if unsafe[i]:
                status = "UNSAFE"
            else:
                status = rng.choice(["SAFE", "SWARMP"])
            if (not unsafe[i]) and rng.random() < 0.4:
                continue    # no Initial filing at all for this building in this cycle
            prior = rng.choice(["SWARMP", "UNSAFE", "SAFE", None], p=[0.35, 0.2, 0.3, 0.15])
            rows.append(dict(tr6_no=f"TR6-{cycle}{grp[i]}-{i:05d}", control_no=f"C{cycle}-{i}", filing_type="Initial", cycle=cycle,
                             bin=str(bins[i]), borough=boro[i], block=str(block[i]), lot=str(lot[i]),
                             filing_date=pd.Timestamp(fdate[i]), submitted_on=pd.Timestamp(fdate[i]) - pd.Timedelta(days=int(rng.integers(0, 3))),
                             filing_status=status, current_status=status, prior_status=prior,
                             exterior_wall_material_s_=wall[i], group=grp[i], _bidx=i))
    fac = pd.DataFrame(rows)
    # extra repeats and cycle 7 history (UNSAFE Initial rows that count toward workload but are not in the frame)
    rep = fac[(fac.filing_status == "UNSAFE")].sample(frac=0.02, random_state=seed).copy()
    rep["tr6_no"] = rep["tr6_no"] + "-R"
    rep["filing_date"] = rep["filing_date"] + pd.Timedelta(days=5)
    c7 = pd.DataFrame(dict(
        tr6_no=[f"TR6-7X-{j}" for j in range(500)], filing_type="Initial", cycle=7, bin=[str(7000000 + j) for j in range(500)],
        borough="Queens", block="100", lot="1", filing_date=pd.Timestamp("2013-06-01") + pd.to_timedelta(rng.integers(0, 1000, 500), unit="D"),
        filing_status="UNSAFE", current_status="UNSAFE", prior_status=None, exterior_wall_material_s_="MASONRY", group="B"))
    c7["submitted_on"] = c7["filing_date"]
    fac = pd.concat([fac, rep, c7], ignore_index=True)

    # ---- Family 1 outcome: discrete-time hazard, then write the clearing filings ----
    frame = fac[(fac.filing_type == "Initial") & (fac.filing_status == "UNSAFE") & fac.cycle.isin([8, 9]) & ~fac.tr6_no.str.endswith("-R")].copy()
    unsafe_dates = fac[(fac.filing_type == "Initial") & (fac.filing_status == "UNSAFE")]["filing_date"].values
    x = brute_workload(unsafe_dates, frame["filing_date"].values)
    dl_f = np.array([pd.Timestamp(WINDOWS[c][g][1]) for c, g in zip(frame.cycle, frame.group)], dtype="datetime64[D]")
    days_before = (dl_f - frame["filing_date"].values.astype("datetime64[D]")).astype(int)
    late = days_before < 29
    early = days_before >= 181
    carried = frame["prior_status"].isin(["SWARMP", "UNSAFE"]).values
    b = np.log(planted_hr)
    eff = b * x
    if workload_hr_early_only is not None:
        eff = np.where(early, np.log(workload_hr_early_only) * x, 0.0)
    qid = (frame["filing_date"].dt.year * 4 + (frame["filing_date"].dt.month - 1) // 3).values
    uq = np.unique(qid)
    shock = dict(zip(uq, rng.normal(0, tau, len(uq)))) if tau > 0 else {q: 0.0 for q in uq}
    shock_row = np.array([shock[q] for q in qid])
    n = len(frame)
    nsteps = 160
    ks = np.arange(1, nsteps + 1)
    base = np.array([BASE_LOG_HAZ.get(k, np.log(0.03) if k <= 12 else (np.log(0.015) if k <= 24 else np.log(0.005))) for k in ks])
    eta = base[None, :] + (eff + late * late_penalty + carried * (-0.15) + shock_row)[:, None]
    haz = 1 - np.exp(-np.exp(eta))
    U = rng.random((n, nsteps))
    hit = U < haz
    event_k = np.where(hit.any(axis=1), hit.argmax(axis=1) + 1, 0)
    clear_day = np.where(event_k > 0, (event_k - 1) * 30 + rng.integers(0, 30, n), -1)
    out_rows = []
    f_dates = frame["filing_date"].values.astype("datetime64[D]")
    for j, (idx, r) in enumerate(frame.iterrows()):
        if clear_day[j] >= 0:
            cd = pd.Timestamp(f_dates[j]) + pd.Timedelta(days=int(clear_day[j]))
            has_fd = rng.random() > 0.05
            out_rows.append(dict(tr6_no=r.tr6_no + "-A1", filing_type="Amended", cycle=r.cycle, bin=r.bin, borough=r.borough, block=r.block,
                                 lot=r.lot, filing_date=cd if has_fd else pd.NaT, submitted_on=cd,
                                 filing_status=rng.choice(["SAFE", "SWARMP"], p=[0.7, 0.3]), current_status="SAFE", prior_status=None,
                                 exterior_wall_material_s_=None, group=r.group))
        elif rng.random() < 0.08:    # a Subsequent clearing filing only (for V2)
            sd_ = pd.Timestamp(f_dates[j]) + pd.Timedelta(days=int(rng.integers(60, 400)))
            out_rows.append(dict(tr6_no=r.tr6_no + "-S1", filing_type="Subsequent", cycle=r.cycle, bin=r.bin, borough=r.borough, block=r.block,
                                 lot=r.lot, filing_date=sd_, submitted_on=sd_, filing_status="SAFE", current_status="SAFE", prior_status=None,
                                 exterior_wall_material_s_=None, group=r.group))
        if rng.random() < 0.15:      # decoy: an Amended UNSAFE filing (not a clearance)
            dd = pd.Timestamp(f_dates[j]) + pd.Timedelta(days=int(rng.integers(20, 100)))
            out_rows.append(dict(tr6_no=r.tr6_no + "-A0", filing_type="Amended", cycle=r.cycle, bin=r.bin, borough=r.borough, block=r.block,
                                 lot=r.lot, filing_date=dd, submitted_on=dd, filing_status="UNSAFE", current_status="UNSAFE", prior_status=None,
                                 exterior_wall_material_s_=None, group=r.group))
        if rng.random() < 0.03:      # decoy: a clearing-looking Amended filing in ANOTHER cycle (must be ignored)
            dd = pd.Timestamp(f_dates[j]) + pd.Timedelta(days=int(rng.integers(20, 100)))
            out_rows.append(dict(tr6_no=r.tr6_no + "-AX", filing_type="Amended", cycle=7 if r.cycle == 8 else 8, bin=r.bin, borough=r.borough,
                                 block=r.block, lot=r.lot, filing_date=dd, submitted_on=dd, filing_status="SAFE", current_status="SAFE",
                                 prior_status=None, exterior_wall_material_s_=None, group=r.group))
    extra = pd.DataFrame(out_rows)
    fac = pd.concat([fac, extra], ignore_index=True).drop(columns="_bidx")
    fac["cycle"] = fac["cycle"].astype("Int64").astype(int)
    for c in ("filing_date", "submitted_on"):
        fac[c] = pd.to_datetime(fac[c])
    truth = {"planted_hr": planted_hr, "late_penalty": late_penalty, "tau": tau, "frame_rows": int(len(frame)),
             "cleared_any": int((event_k > 0).sum())}
    return fac.reset_index(drop=True), truth


def sim_pluto(facades, seed=1):
    """Simulated PLUTO table (columns: bbl, ownertype, numfloors) for the BBLs in the facade table. About 8% public
    owners, a few tax-exempt, 5% unmatched (left out of the table)."""
    rng = np.random.default_rng(seed + 100)
    code = {"Manhattan": 1, "Bronx": 2, "Brooklyn": 3, "Queens": 4, "Staten Island": 5}
    d = facades[["borough", "block", "lot"]].drop_duplicates()
    d = d[d["borough"].isin(code)]
    bbl = d["borough"].map(code) * 10**9 + d["block"].astype(int) * 10**4 + d["lot"].astype(int)
    keep = rng.random(len(bbl)) > 0.05
    own = rng.choice(["P", "C", "M", "O", "X", ""], size=len(bbl), p=[0.80, 0.04, 0.02, 0.02, 0.07, 0.05])
    floors = np.where(rng.random(len(bbl)) < 0.04, 0, rng.integers(3, 45, len(bbl)))
    p = pd.DataFrame({"borough": d["borough"].values, "block": d["block"].values, "lot": d["lot"].values,
                      "bbl": [f"{int(v)}.00000000" for v in bbl.values], "ownertype": own, "numfloors": floors})
    return p[keep].drop_duplicates("bbl").reset_index(drop=True)


def sim_sheds(facades, seed=1, branch="B", planted_hr=0.75, winter_hr=0.80, link_prob=0.75, D="2026-10-17", quirks=True):
    """Simulated shed permits for the simulated frame. Returns (dobnow_raw, legacy_raw, truth).

    Each linked building gets a shed from S = F + U(-60, 120). Permits chain: a permit of `term` days ends at e; at e the
    shed ends with the cloglog hazard exp(a + log(planted_hr) * x + log(winter_hr) * winter_start), else a renewal
    permit starts at e (0 to 15 days later). Branch B: annual terms (300 to 400 days), x = trailing workload at e.
    Branch A: 90-day terms, x = workload averaged over the term. The last permit's end is the (blurred) removal."""
    rng = np.random.default_rng(seed + 7)
    unsafe = facades[(facades.filing_type == "Initial") & (facades.filing_status == "UNSAFE")]
    days, W = brute_daily(unsafe["filing_date"].values, "2000-01-01", "2030-12-31")
    d0 = days[0].astype("int64")
    cs = np.concatenate([[0.0], np.cumsum(W)])

    def x_at(e):
        return W[int(np.datetime64(e, "D").astype("int64") - d0)]

    def x_mean(s, e):
        i0, i1 = int(np.datetime64(s, "D").astype("int64") - d0), int(np.datetime64(e, "D").astype("int64") - d0)
        return (cs[i1 + 1] - cs[i0 + 1]) / max(i1 - i0, 1)

    frame = facades[(facades.filing_type == "Initial") & (facades.filing_status == "UNSAFE") & facades.cycle.isin([8, 9]) & ~facades.tr6_no.str.endswith("-R")]
    permits = []
    ended_n = 0
    for r in frame.itertuples():
        if rng.random() > link_prob:
            continue
        F = pd.Timestamp(r.filing_date)
        S = F + pd.Timedelta(days=int(rng.integers(-60, 120)))
        winter = S.month in (12, 1, 2)
        start = S
        for _ in range(200):
            term = int(rng.integers(300, 401)) if branch == "B" else 90
            end = start + pd.Timedelta(days=term)
            permits.append((r.bin, start, end))
            if end > pd.Timestamp("2026-06-30"):
                break
            xv = x_at(end.to_datetime64()) if branch == "B" else x_mean(start.to_datetime64(), end.to_datetime64())
            a = np.log(0.30) if branch == "B" else np.log(0.22)
            h = 1 - np.exp(-np.exp(a + np.log(planted_hr) * xv + (np.log(winter_hr) if winter else 0.0)))
            if rng.random() < h:
                ended_n += 1
                break
            # a small share of renewals start 60 days later (a NEW spell), a few add a concurrent permit
            gap = 60 if (quirks and rng.random() < 0.03) else int(rng.integers(0, 16))
            if quirks and rng.random() < 0.04:
                permits.append((r.bin, start + pd.Timedelta(days=5), end - pd.Timedelta(days=20)))
            start = end + pd.Timedelta(days=gap)
    p = pd.DataFrame(permits, columns=["bin", "start", "end"])
    legacy_mask = p["start"] < pd.Timestamp("2020-01-01")
    dn = p[~legacy_mask]
    lg = p[legacy_mask]
    dobnow = pd.DataFrame({"bin": dn["bin"].values, "block": "1", "lot": "1", "work_type": "Sidewalk Shed", "permit_status": "Permit Issued",
                           "filing_reason": "Initial Permit", "work_permit": "x", "sequence_number": "1",
                           "approved_date": (dn["start"] - pd.Timedelta(days=3)).dt.strftime("%Y-%m-%dT00:00:00.000").values,
                           "issued_date": dn["start"].dt.strftime("%Y-%m-%dT00:00:00.000").values,
                           "expired_date": dn["end"].dt.strftime("%Y-%m-%dT00:00:00.000").values})
    legacy = pd.DataFrame({"bin__": lg["bin"].values, "permit_type": "SH", "permit_subtype": "NA", "permit_status": "ISSUED",
                           "filing_date": (lg["start"] - pd.Timedelta(days=9)).dt.strftime("%m/%d/%Y").values,
                           "issuance_date": lg["start"].dt.strftime("%m/%d/%Y").values,
                           "expiration_date": lg["end"].dt.strftime("%m/%d/%Y").values})
    # junk rows the cleaning rules must drop or collapse
    junk_n = max(5, int(0.03 * len(dobnow))) if quirks else 3
    j = dobnow.sample(junk_n, random_state=seed).copy()
    j["work_type"] = "Plumbing"
    w = dobnow.sample(junk_n, random_state=seed + 1).copy(); w["permit_status"] = "Permit Withdrawn"
    m = dobnow.sample(junk_n, random_state=seed + 2).copy(); m["expired_date"] = None
    inv = dobnow.sample(junk_n, random_state=seed + 3).copy(); inv["expired_date"] = inv["approved_date"].str.replace("20", "19", n=1)
    dup = dobnow.sample(junk_n, random_state=seed + 4).copy()
    dobnow = pd.concat([dobnow, j, w, m, inv, dup], ignore_index=True)
    lj = legacy.sample(max(3, junk_n // 3), random_state=seed).copy(); lj["permit_type"] = "EW"
    lbad = legacy.sample(max(3, junk_n // 3), random_state=seed + 5).copy(); lbad["expiration_date"] = "99/99/9999"
    legacy = pd.concat([legacy, lj, lbad], ignore_index=True)
    return dobnow, legacy, {"branch": branch, "planted_hr": planted_hr, "winter_hr": winter_hr, "n_permits": len(p), "n_ended": ended_n}
