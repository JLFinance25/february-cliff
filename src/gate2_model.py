# Gate 2 models: the Family 1 outcome (time to a clearing filing), discrete-time hazard models for both families,
# stop rules, the identifiability rule, Holm, placebos, and every sensitivity variant (V1 to V11, S1 to S20) as one
# option set. Implements PREREG.md (locked Oct 17, 2026, commit 0140a58) sections 3, 5, 6, 7 and 9.
# Written and tested on SIMULATED data only (src/gate2_simcheck.py) before any repair duration or shed row was opened.
# Drafted by Claude (AI); directed and approved by Jayden Ling.
#
# Models are fitted with statsmodels GLM (binomial family, complementary log-log link) as PREREG 5 says; a hand-written
# numpy fit (`cloglog_irls`) must agree with it to 4 decimals (checked in gate2_simcheck.py). Standard errors are
# clustered by calendar quarter with the usual small-sample correction, and intervals and p-values use a t distribution
# with K - 1 degrees of freedom (7.4). "CHOICE:" marks a small detail the PREREG left open.
import dataclasses
import pathlib
import sys
import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
import scipy.stats as st
import statsmodels.api as sm

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gate2_link as L

HR_MEANINGFUL_LOW, HR_MEANINGFUL_HIGH = 0.80, 1.25      # 7.5
QUIET_PCT, BUSY_PCT = 0.40, 0.70                         # 7.7: quiet = bottom 40% of x, busy = top 30%
CELL_MIN_ROWS, CELL_MIN_EVENTS = 50, 20                  # 7.7
MIN_QUARTERS = 24                                        # 7.7
AVAILABILITY_MIN = 0.50                                  # 3.1
STEP_BANDS = [(1, 1), (2, 2), (3, 3), (4, 6), (7, 12), (13, 24), (25, 10**6)]   # 7.1 time since filing, in steps


# ---------------------------------------------------------------------------------------------------------------
# Family 1 outcome R (PREREG 3.2)
# ---------------------------------------------------------------------------------------------------------------
def _dated(df):
    out = df.copy()
    out["bin"] = L.clean_bin_series(out["bin"])
    out["date"] = L.filing_date_F(out)
    return out[out["bin"].notna() & out["date"].notna()]


def family1_outcome(frame, facades, follow_end=L.FOLLOW_END_FAMILY1, include_subsequent=False, v10=False):
    """Adds to the frame: clear_date (first clearing filing dated on or after F, any date), censor_date, event, R, c.

    Clearing filing = first filing in the same (BIN, cycle), dated on or after F, filing_type 'Amended' (V2 also
    'Subsequent') with filing_status SAFE or SWARMP; date = filing_date, or submitted_on if blank (3.2).
    Censoring at the earlier of `follow_end` and the date of the BIN's next Initial filing in a LATER cycle (3.2 a, d).
    V10 (v10=True): a next-cycle Initial filing rated SAFE or SWARMP also counts as a clearance on its date.
    event = clear_date on or before censor_date. R = clear_date - F in days (0 for a same-day clearing filing).
    CHOICE: a clearing filing dated exactly on the censor date counts as an event."""
    types = ["Amended", "Subsequent"] if include_subsequent else ["Amended"]
    cl = _dated(facades[facades["filing_type"].isin(types) & facades["filing_status"].isin(["SAFE", "SWARMP"])])
    cl = cl[["bin", "cycle", "date"]]
    f = frame.copy()
    m = f[["fid", "bin", "cycle", "F"]].merge(cl, on=["bin", "cycle"], how="inner")
    m = m[m["date"] >= m["F"]]
    first = m.groupby("fid")["date"].min()
    ini = _dated(facades[facades["filing_type"] == "Initial"])[["bin", "cycle", "date", "filing_status"]]
    n = f[["fid", "bin", "cycle"]].merge(ini, on="bin", how="inner", suffixes=("", "_next"))
    n = n[n["cycle_next"] > n["cycle"]]
    next_ini = n.groupby("fid")["date"].min()
    f["clear_date"] = f["fid"].map(first)
    f["has_clear_any_date"] = f["clear_date"].notna()
    if v10:
        nc = n[n["filing_status"].isin(["SAFE", "SWARMP"])].groupby("fid")["date"].min()
        f["clear_date"] = pd.concat([f["clear_date"], f["fid"].map(nc)], axis=1).min(axis=1)
    f["next_initial"] = f["fid"].map(next_ini)
    f["censor_date"] = pd.concat([f["next_initial"], pd.Series(pd.Timestamp(follow_end), index=f.index)], axis=1).min(axis=1)
    f["event"] = f["clear_date"].notna() & (f["clear_date"] <= f["censor_date"])
    f["R"] = (f["clear_date"] - f["F"]).dt.days
    f["c"] = (f["censor_date"] - f["F"]).dt.days
    return f


def availability_by_cycle(f1):
    """Share of frame filings with a clearing filing at ANY date, by cycle and overall; and among Early filers (3.1 b)."""
    out = {"overall": float(f1["has_clear_any_date"].mean()) if len(f1) else float("nan"),
           "early": float(f1.loc[f1["timing"] == "Early", "has_clear_any_date"].mean()) if (f1["timing"] == "Early").any() else float("nan")}
    out["by_cycle"] = {int(c): float(g["has_clear_any_date"].mean()) for c, g in f1.groupby("cycle")}
    return out


def observed_event(f1, step):
    """True where the clearing event falls in a step that was observed in full. CHOICE (reviewer finding 6): an event in
    a step the filing was only partly observed for (censored mid-step) is treated as censoring at that step's start,
    so events and non-events are treated alike; otherwise the last step before the censor date would see its events
    but not its non-events and its hazard would be pushed up."""
    ev = f1["event"].values.astype(bool)
    R = np.where(ev, f1["R"].fillna(0).values, 0).astype(int)
    c = f1["c"].fillna(-1).values.astype(int)
    return ev & ((R // step + 1) * step - 1 <= c)


def expand_person_period(f1, step):
    """One row per `step`-day step from F until the event or censoring (3.3).

    Step k covers days (k-1)*step .. k*step - 1. An event at R falls in step R // step + 1 (outcome 1 there) if that
    step was observed in full (see observed_event). A censored filing contributes only the steps it was observed for in
    full, (c + 1) // step of them."""
    ev = observed_event(f1, step)
    R = np.where(ev, f1["R"].fillna(0).values, 0).astype(int)
    c = f1["c"].fillna(-1).values.astype(int)
    n = np.where(ev, R // step + 1, (c + 1) // step)
    n = np.maximum(n, 0)
    idx = np.repeat(np.arange(len(f1)), n)
    start = np.cumsum(n) - n
    k = np.arange(n.sum()) - np.repeat(start, n) + 1
    y = (ev[idx] & (k == n[idx])).astype(int)
    return pd.DataFrame({"idx": idx, "step": k, "y": y})


# ---------------------------------------------------------------------------------------------------------------
# Design-matrix helpers
# ---------------------------------------------------------------------------------------------------------------
def cat_dummies(values, prefix, baseline=None, levels=None):
    """0/1 columns for each level except the baseline (default: the first level in sorted order, or in `levels`).
    Values, levels and baseline are all compared as strings, so integer levels (months 1..12) work."""
    v = pd.Series(np.asarray(values)).astype(str)
    lv = [str(x) for x in levels] if levels is not None else sorted(v.unique())
    base = str(baseline) if baseline is not None else lv[0]
    cols = {f"{prefix}={x}": (v == x).astype(float).values for x in lv if x != base and (v == x).any()}
    return pd.DataFrame(cols)


def drop_dependent(X, protect=("const", "x"), tol=1e-9):
    """Drop constant columns and columns that are linear combinations of earlier ones (Gram-Schmidt), keeping the order
    given. Protected columns (const, then x) come first so they are never the ones dropped. Returns (X, dropped)."""
    cols = list(X.columns)
    order = [c for c in cols if c in protect] + [c for c in cols if c not in protect]
    A = X[order].values.astype(float)
    basis, keep, dropped = [], [], []
    for j, c in enumerate(order):
        v = A[:, j].copy()
        n0 = np.linalg.norm(v)
        if n0 == 0:
            dropped.append(c); continue
        for _ in range(2):
            for b in basis:
                v -= (b @ v) * b
        if np.linalg.norm(v) <= tol * max(n0, 1.0):
            dropped.append(c); continue
        basis.append(v / np.linalg.norm(v)); keep.append(c)
    return X[keep], dropped


def band_labels(step, bands=STEP_BANDS):
    out = np.empty(len(step), dtype=object)
    for lo, hi in bands:
        out[(step >= lo) & (step <= hi)] = f"{lo}-{hi}"
    return out


def shared_controls(d, timing_terms=True):
    """Shared controls of 7.1: filing timing (Early baseline), deadline group, cycle, borough, stories band, wall
    indicators, and the carried-over, OwnerType X and no-PLUTO-match indicators."""
    parts = []
    if timing_terms:
        parts.append(cat_dummies(d["timing"].values, "timing", baseline="Early", levels=["Early", "Middle", "Last-minute", "Past-deadline"]))
    parts.append(cat_dummies(d["group"].values, "group", baseline="A", levels=["A", "B", "C"]))
    parts.append(cat_dummies(d["cycle"].values, "cycle"))
    parts.append(cat_dummies(d["borough"].values, "borough"))
    parts.append(cat_dummies(d["stories"].values, "stories", baseline="le9", levels=["le9", "10_14", "15_24", "ge25", "missing"]))
    ind = pd.DataFrame({k: d[k].values.astype(float) for k in ["wall_masonry", "wall_terracotta", "wall_missing", "carried_over", "owner_X", "no_pluto_match"]})
    parts.append(ind)
    if "public_owner" in d and d["public_owner"].nunique() > 1:
        parts.append(pd.DataFrame({"public_owner": d["public_owner"].values.astype(float)}))
    if "rating_swarmp" in d and d["rating_swarmp"].nunique() > 1:
        parts.append(pd.DataFrame({"rating_swarmp": d["rating_swarmp"].values.astype(float)}))
    return pd.concat(parts, axis=1)


def policy_columns(dates, names_to_dates):
    return pd.DataFrame({k: (pd.to_datetime(pd.Series(dates)).values >= np.datetime64(v)).astype(float) for k, v in names_to_dates.items()})


# ---------------------------------------------------------------------------------------------------------------
# Fitting: statsmodels (the model of record) and a hand-written numpy fit (the check)
# ---------------------------------------------------------------------------------------------------------------
def cluster_ids(kind, d):
    """Cluster labels for the variance. 'quarter' (primary), 'month', 'block', or 'twoway' (block and quarter)."""
    if kind == "quarter":
        return d["quarter_cl"].values
    if kind == "month":
        return d["month_cl"].values
    block = pd.factorize(d["block_key"])[0]
    if kind == "block":
        return block
    if kind == "twoway":
        return np.column_stack([block, pd.factorize(d["quarter_cl"])[0]])
    raise ValueError(kind)


def n_clusters(groups):
    g = np.asarray(groups)
    if g.ndim == 1:
        return int(len(np.unique(g)))
    return int(min(len(np.unique(g[:, 0])), len(np.unique(g[:, 1]))))


def fit_cloglog(X, y, groups):
    """statsmodels GLM, binomial, cloglog link, cluster-robust covariance with the small-sample correction.
    Returns the result object; use `coef_table` for t-based intervals."""
    link = sm.families.links.CLogLog()
    model = sm.GLM(np.asarray(y, float), X, family=sm.families.Binomial(link=link))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = model.fit(maxiter=200, cov_type="cluster", cov_kwds={"groups": groups, "use_correction": True, "df_correction": True})
    return res


def coef_table(res, K):
    """Coefficients with a t distribution on K - 1 degrees of freedom (7.4). hr = exp(coef)."""
    names = list(res.params.index) if hasattr(res.params, "index") else list(range(len(res.params)))
    beta, se = np.asarray(res.params), np.asarray(res.bse)
    df = max(K - 1, 1)
    tcrit = st.t.ppf(0.975, df)
    t = beta / se
    p = 2 * st.t.sf(np.abs(t), df)
    with np.errstate(over="ignore"):
        return pd.DataFrame({"coef": beta, "se": se, "hr": np.exp(beta), "hr_lo": np.exp(beta - tcrit * se),
                             "hr_hi": np.exp(beta + tcrit * se), "p": p, "df": df}, index=names)


def cloglog_irls(X, y, groups=None, tol=1e-11, maxit=200):
    """Hand-written cloglog fit (Fisher scoring), the check on statsmodels. Returns beta, and if `groups` is given the
    one-way cluster covariance with correction G/(G-1) * (N-1)/(N-k) and the expected-information bread."""
    X = np.asarray(X, float); y = np.asarray(y, float)
    n, k = X.shape
    mu0 = (y + y.mean()) / 2
    beta = np.linalg.lstsq(X, np.log(-np.log1p(-np.clip(mu0, 1e-6, 1 - 1e-6))), rcond=None)[0]

    def parts(b):
        eta = np.clip(X @ b, -30, 6)
        ee = np.exp(eta)
        mu = np.clip(-np.expm1(-ee), 1e-12, 1 - 1e-12)
        dmu = ee * np.exp(-ee)
        return eta, mu, dmu

    def dev(mu):
        return -2 * np.sum(y * np.log(mu) + (1 - y) * np.log1p(-mu))

    eta, mu, dmu = parts(beta)
    d_old = dev(mu)
    for _ in range(maxit):
        w = dmu**2 / (mu * (1 - mu))
        z = eta + (y - mu) / dmu
        A = (X.T * w) @ X
        new = np.linalg.solve(A, (X.T * w) @ z)
        step = 1.0
        while True:
            cand = beta + step * (new - beta)
            e2, m2, dm2 = parts(cand)
            d_new = dev(m2)
            if d_new <= d_old + 1e-10 or step < 1e-4:
                break
            step /= 2
        delta = np.max(np.abs(cand - beta))
        beta, eta, mu, dmu, d_old = cand, e2, m2, dm2, d_new
        if delta < tol:
            break
    if groups is None:
        return beta
    w = dmu**2 / (mu * (1 - mu))
    bread = np.linalg.inv((X.T * w) @ X)
    s = X * (((y - mu) / (mu * (1 - mu))) * dmu)[:, None]
    g = pd.factorize(np.asarray(groups))[0]
    G = g.max() + 1
    sg = np.zeros((G, k)); np.add.at(sg, g, s)
    cov = (G / (G - 1)) * ((n - 1) / (n - k)) * bread @ (sg.T @ sg) @ bread
    return beta, cov


# ---------------------------------------------------------------------------------------------------------------
# Many tests, effect size, robustness (PREREG 7.3, 7.5, 8)
# ---------------------------------------------------------------------------------------------------------------
def holm(pvals, alpha=0.05):
    """Holm within one family: sort the p-values; the smallest must be below alpha/n, the next below alpha/(n-1), and
    so on; stop at the first failure. `pvals` is {name: p}; tests marked not run are simply left out."""
    items = sorted(pvals.items(), key=lambda kv: kv[1])
    n = len(items)
    out, failed = {}, False
    for i, (k, p) in enumerate(items):
        thr = alpha / (n - i)
        ok = (not failed) and (p < thr)
        if not ok:
            failed = True
        out[k] = {"p": p, "threshold": thr, "significant": bool(ok)}
    return out


def classify_effect(hr, lo, hi):
    """7.5: 'meaningful' = HR 0.80 or lower, or 1.25 or higher; 'no meaningful effect' = the whole 95% interval inside
    0.80 to 1.25; otherwise 'inconclusive'. Reported alongside whether the interval excludes 1."""
    inside = (lo >= HR_MEANINGFUL_LOW) and (hi <= HR_MEANINGFUL_HIGH)
    big = (hr <= HR_MEANINGFUL_LOW) or (hr >= HR_MEANINGFUL_HIGH)
    if inside:
        label = "no meaningful effect"
    elif big:
        label = "meaningful (point estimate)"
    else:
        label = "inconclusive"
    return {"label": label, "excludes_1": bool((lo > 1) or (hi < 1)), "inside_0.80_1.25": bool(inside)}


def robustness(main_hr, main_excludes_1, variant_hrs):
    """8: 'robust' only if the estimate and at least three-quarters of the family's variants that could be run point the
    same way and the interval excludes 1; otherwise 'fragile'."""
    direction = np.sign(np.log(main_hr))
    ran = [h for h in variant_hrs if h is not None and np.isfinite(h)]
    if not ran:
        return "fragile"
    same = np.mean([np.sign(np.log(h)) == direction for h in ran])
    return "robust" if (main_excludes_1 and same >= 0.75) else "fragile"


# ---------------------------------------------------------------------------------------------------------------
# Identifiability rule and stop rules (PREREG 7.7), checked on counts before any model is fit
# ---------------------------------------------------------------------------------------------------------------
def identifiability(x_all, timing_all, event_all, subset=None):
    """Rank-based bands from the family's analysis rows: quiet = bottom 40% of x (x <= its 40th percentile), busy = top
    30% (x >= its 70th percentile). Filing timing: Early vs Late (Last-minute plus Past-deadline); Middle belongs to no
    corner. Each of the four corner cells needs at least 50 rows and 20 events.
    `subset` is an optional boolean mask of rows to count in the cells (C6 / C2: Early rows) with bands still taken from
    all rows. Returns the cells, which pass, and whether C5/C1 (all four) and C6/C2 (both Early) are separable."""
    x = np.asarray(x_all, float); ev = np.asarray(event_all, bool); t = np.asarray(timing_all)
    q_hi, b_lo = np.quantile(x, QUIET_PCT), np.quantile(x, BUSY_PCT)
    band = np.where(x <= q_hi, "quiet", np.where(x >= b_lo, "busy", "mid"))
    early = t == "Early"
    late = np.isin(t, ["Last-minute", "Past-deadline"])
    cells = {}
    for name, m in {"Early-quiet": early & (band == "quiet"), "Early-busy": early & (band == "busy"),
                    "Late-quiet": late & (band == "quiet"), "Late-busy": late & (band == "busy")}.items():
        cells[name] = {"rows": int(m.sum()), "events": int((m & ev).sum()),
                       "pass": bool(m.sum() >= CELL_MIN_ROWS and (m & ev).sum() >= CELL_MIN_EVENTS)}
    return {"cutoffs": {"quiet_le": float(q_hi), "busy_ge": float(b_lo)}, "cells": cells,
            "separable_all": all(c["pass"] for c in cells.values()),
            "separable_early": cells["Early-quiet"]["pass"] and cells["Early-busy"]["pass"]}


def residual_sd_ratio(x, year, month, timing):
    """Residual SD of x after year, month and filing timing, divided by the SD after year and month (7.7 'Also
    reported'); also the two SDs."""
    def resid(cols):
        A = np.column_stack([np.ones(len(x))] + cols)
        b = np.linalg.lstsq(A, x, rcond=None)[0]
        return np.std(x - A @ b, ddof=0)
    ym = [cat_dummies(year, "y").values, cat_dummies(month, "m").values]
    ymt = ym + [cat_dummies(timing, "t").values]
    s1, s2 = resid(ym), resid(ymt)
    return {"sd_after_year_month": float(s1), "sd_after_year_month_timing": float(s2), "ratio": float(s2 / s1) if s1 > 0 else float("nan")}


# ---------------------------------------------------------------------------------------------------------------
# Family 1: configuration, run, confirmatory wrapper
# ---------------------------------------------------------------------------------------------------------------
@dataclass
class F1Config:
    model: str = "M5"                     # 'M5' (all filings, gives C5) or 'M6' (Early filers only, gives C6)
    step_days: int = 30
    lookback: int = L.LOOKBACK
    f_end: pd.Timestamp = L.F_END_FAMILY1
    follow_end: pd.Timestamp = L.FOLLOW_END_FAMILY1
    include_subsequent: bool = False      # V2
    v10: bool = False                     # V10
    tv_workload: bool = False             # V4: workload re-measured at each step
    calendar_rule: bool = False           # V8
    year_trend: bool = False              # V9a
    include_public: bool = False          # V9b
    drop_cleared_nolink: bool = False     # V5
    drop_covid_filings: bool = False      # V3
    extra_steps: tuple = ()               # V1 adds 'step_2025_04_17'
    cluster: str = "quarter"              # V11: 'month', 'twoway', 'block'
    split_own_other: bool = False         # E10
    timing_terms: bool = None             # None: on for M5, off for M6. False on M5 gives the crude estimate (E5)
    in_window_only: bool = False          # E8: Early filers that were inside their own window
    placebo: str = None                   # 'pl1' or 'pl2' adds that term to the model


F1_VARIANTS = {
    "V1": dict(f_end=pd.Timestamp("2025-12-31"), follow_end=pd.Timestamp("2025-12-31"), extra_steps=("step_2025_04_17",)),
    "V2": dict(include_subsequent=True),
    "V3": dict(drop_covid_filings=True),
    "V4": dict(tv_workload=True),
    "V5": dict(drop_cleared_nolink=True),
    "V6": dict(step_days=14),
    "V7a": dict(lookback=30), "V7b": dict(lookback=180),
    "V8": dict(calendar_rule=True),
    "V9a": dict(year_trend=True), "V9b": dict(include_public=True),
    "V10": dict(v10=True),
    "V11a": dict(cluster="month"), "V11b": dict(cluster="twoway"), "V11c": dict(cluster="block"),
}


def prepare_family1(facades, pluto, cfg, apply_availability=True):
    """Frame (4.1 step 1 limited to F on or before cfg.f_end) with the outcome attached, after the variant filters.
    apply_availability: also drop any cycle with fewer than 50% of its filings having a clearing filing (3.1 b). The
    confirmatory wrapper passes False so it can report the shares first, then drops the cycles itself."""
    frame = L.build_frame(facades, f_end=cfg.f_end, pluto=pluto, include_public=cfg.include_public)
    f1 = family1_outcome(frame, facades, follow_end=cfg.follow_end, include_subsequent=cfg.include_subsequent, v10=cfg.v10)
    if cfg.drop_covid_filings:
        f1 = f1[~((f1["F"] >= pd.Timestamp("2019-12-01")) & (f1["F"] <= pd.Timestamp("2020-09-30")))]
    if cfg.drop_cleared_nolink:
        f1 = f1[~(f1["current_status"].isin(["SAFE", "SWARMP"]) & ~f1["has_clear_any_date"])]
    f1 = f1.reset_index(drop=True)
    if apply_availability and len(f1):
        by_cycle = f1.groupby("cycle")["has_clear_any_date"].mean()
        f1 = f1[f1["cycle"].isin(by_cycle[by_cycle >= AVAILABILITY_MIN].index)].reset_index(drop=True)
    f1.attrs["counts"] = frame.attrs["counts"]
    return f1


def _f1_workload(f1, wl, cfg):
    x = wl.trailing(f1["F"], cfg.lookback)
    own = wl.trailing(f1["F"], cfg.lookback, kind="own", groups=f1["group"].values)
    oth = wl.trailing(f1["F"], cfg.lookback, kind="other", groups=f1["group"].values)
    return x, own, oth


def design_family1(f1, wl, cfg):
    """Person-step design matrix for M5 / M6 (7.1). Returns X, y, cluster groups, rows (the expanded filings), notes."""
    model_m6 = cfg.model == "M6"
    d = f1[f1["timing"].eq("Early")] if model_m6 else f1
    if model_m6 and cfg.in_window_only:
        d = d[~d["before_window"]]
    d = d.reset_index(drop=True)
    pp = expand_person_period(d, cfg.step_days)
    r = d.iloc[pp["idx"].values].reset_index(drop=True)
    step_start = r["F"] + pd.to_timedelta((pp["step"].values - 1) * cfg.step_days, unit="D")
    timing_terms = (not model_m6) if cfg.timing_terms is None else cfg.timing_terms
    if model_m6:
        timing_terms = False

    # --- exposure -----------------------------------------------------------------------------------------------
    if cfg.calendar_rule:   # V8: calendar rule w (F inside a deadline window) plus the nuisance indicator
        cal = L.deadline_window_days(wl.origin, wl.n_days)
        nui = L.nuisance_window_days(wl)
        off = (pd.to_datetime(r["F"]).dt.normalize() - wl.origin).dt.days.values
        expo = pd.DataFrame({"x": cal[off].astype(float), "nuisance": nui[off].astype(float)})
    elif cfg.split_own_other:
        _, own, oth = _f1_workload(d, wl, cfg)
        expo = pd.DataFrame({"x_own": own[pp["idx"].values], "x_other": oth[pp["idx"].values]})
    elif cfg.tv_workload:
        expo = pd.DataFrame({"x": wl.trailing(step_start, cfg.lookback)})
    else:
        x_f = wl.trailing(d["F"], cfg.lookback)
        expo = pd.DataFrame({"x": x_f[pp["idx"].values]})

    parts = [expo]
    if cfg.placebo == "pl1":
        in_window = r["F"].dt.year.isin(L.DEADLINE_YEARS) & r["F"].dt.month.isin([8, 9, 10])
        parts.append(pd.DataFrame({"pl1": in_window.astype(float).values}))
    if cfg.placebo == "pl2":
        parts.append(pd.DataFrame({"pl2": wl.forward(r["F"], cfg.lookback)}))
    parts.append(shared_controls(r, timing_terms=timing_terms))
    if cfg.year_trend:
        parts.append(pd.DataFrame({"year_trend": (r["F"].dt.year - 2015).astype(float).values}))
    else:
        parts.append(cat_dummies(r["F"].dt.year.values, "year"))
    parts.append(cat_dummies(r["F"].dt.month.values, "month", levels=list(range(1, 13))))
    parts.append(cat_dummies(band_labels(pp["step"].values), "since", baseline="1-1", levels=[f"{a}-{b}" for a, b in STEP_BANDS]))
    covid = ((step_start <= L.COVID_END) & (step_start + pd.Timedelta(days=cfg.step_days - 1) >= L.COVID_START)).astype(float)
    parts.append(pd.DataFrame({"covid": covid.values}))
    steps = dict(L.POLICY_STEPS_MAIN)
    for nm in cfg.extra_steps:
        steps[nm] = L.POLICY_STEP_2025["step_2025_04_17"] if nm == "step_2025_04_17" else L.POLICY_STEPS_S17[nm]
    parts.append(policy_columns(step_start, steps))
    X = pd.concat([p.reset_index(drop=True) for p in parts], axis=1)
    X.insert(0, "const", 1.0)
    X, dropped = drop_dependent(X, protect=("const", "x", "x_other", "x_own", "pl1", "pl2"))
    r["quarter_cl"] = L.quarter_id(r["F"]).values
    r["month_cl"] = L.month_id(r["F"]).values
    groups = cluster_ids(cfg.cluster, r)
    return X, pp["y"].values, groups, r, {"dropped_columns": dropped, "n_filings": len(d)}


def run_family1(facades, pluto, wl, cfg=None, f1=None):
    """Fit one Family 1 model and return its coefficient table with t-based intervals on K - 1 degrees of freedom."""
    cfg = cfg or F1Config()
    f1 = f1 if f1 is not None else prepare_family1(facades, pluto, cfg)
    X, y, groups, r, notes = design_family1(f1, wl, cfg)
    res = fit_cloglog(X, y, groups)
    K = n_clusters(groups)
    tab = coef_table(res, K)
    return {"table": tab, "K": K, "n_rows": int(len(y)), "n_events": int(y.sum()), "n_filings": notes["n_filings"],
            "dropped_columns": notes["dropped_columns"], "converged": bool(getattr(res, "converged", True)), "cfg": cfg}


def hr_of(result, term="x"):
    t = result["table"].loc[term]
    return {"hr": float(t["hr"]), "lo": float(t["hr_lo"]), "hi": float(t["hr_hi"]), "p": float(t["p"]), "K": result["K"],
            "events": result["n_events"], "rows": result["n_rows"]}


def family1_gates(f1, wl):
    """Counts-only checks before any model (3.1 b, 7.7): availability, stop rules and identifiability for C5 and C6.
    Returns what runs: {'cycles_kept', 'C5': {...}, 'C6': {...}}."""
    avail = availability_by_cycle(f1)
    keep_cycles = [c for c, v in avail["by_cycle"].items() if v >= AVAILABILITY_MIN]
    f = f1[f1["cycle"].isin(keep_cycles)]
    out = {"availability": avail, "cycles_kept": keep_cycles}
    if len(f) == 0 or f["has_clear_any_date"].mean() < AVAILABILITY_MIN:
        out["C5"] = out["C6"] = {"run": False, "why": "availability rule failed"}
        return out
    x = wl.trailing(f["F"], L.LOOKBACK)
    out["frame_after_availability"] = len(f)
    q_all = f["quarter"].nunique()
    f = f.assign(event_obs=observed_event(f, F1Config.step_days))
    ev = f["event_obs"].values
    out["x_residual_sd"] = residual_sd_ratio(x, f["F"].dt.year.values, f["F"].dt.month.values, f["timing"].values)
    c5_ok = (len(f) >= 1000) and (ev.sum() >= 400) and (q_all >= MIN_QUARTERS)
    ident = identifiability(x, f["timing"].values, ev)
    out["identifiability"] = ident
    out["C5"] = {"run": bool(c5_ok and ident["separable_all"]), "filings": len(f), "events": int(ev.sum()), "quarters": int(q_all),
                 "why": None if (c5_ok and ident["separable_all"]) else ("stop rule" if not c5_ok else "not separable from filer type")}
    e = f[f["timing"] == "Early"]
    early_av = float(e["has_clear_any_date"].mean()) if len(e) else float("nan")
    c6_ok = (len(e) >= 300) and (e["event_obs"].sum() >= 100) and (e["quarter"].nunique() >= MIN_QUARTERS) and (early_av >= AVAILABILITY_MIN)
    out["C6"] = {"run": bool(c6_ok and ident["separable_early"]), "filings": len(e), "events": int(e["event_obs"].sum()),
                 "quarters": int(e["quarter"].nunique()), "early_availability": early_av,
                 "why": None if (c6_ok and ident["separable_early"]) else ("stop rule" if not c6_ok else "Early cells too thin")}
    return out


def pl1_warning(placebo_result):
    """7.8: if the PL1 interval excludes 1 and its HR is outside 0.80 to 1.25, the family's workload test is reported with
    a warning and may not be called confirmatory."""
    t = placebo_result["table"].loc["pl1"]
    return bool((t["hr_lo"] > 1 or t["hr_hi"] < 1) and (t["hr"] < HR_MEANINGFUL_LOW or t["hr"] > HR_MEANINGFUL_HIGH))


def run_family1_confirmatory(facades, pluto, wl):
    """C5 and C6 (7.2): availability rule, stop rules, identifiability rule, then M5 and M6 with Holm over what ran.
    Placebos PL1 and PL2 for M5 and M6 are run only if their test ran. Returns everything needed to report."""
    cfg = F1Config()
    f1 = prepare_family1(facades, pluto, cfg, apply_availability=False)
    gates = family1_gates(f1, wl)
    f1k = f1[f1["cycle"].isin(gates["cycles_kept"])].reset_index(drop=True)
    out = {"gates": gates, "frame_counts": f1.attrs.get("counts", {})}
    ps = {}
    if gates["C5"]["run"]:
        out["C5"] = run_family1(facades, pluto, wl, dataclasses.replace(cfg, model="M5"), f1=f1k)
        ps["C5"] = out["C5"]["table"].loc["x", "p"]
        out["PL1_M5"] = run_family1(facades, pluto, wl, dataclasses.replace(cfg, model="M5", placebo="pl1"), f1=f1k)
        out["PL2_M5"] = run_family1(facades, pluto, wl, dataclasses.replace(cfg, model="M5", placebo="pl2"), f1=f1k)
        out["PL1_warning"] = pl1_warning(out["PL1_M5"])
    if gates["C6"]["run"]:
        out["C6"] = run_family1(facades, pluto, wl, dataclasses.replace(cfg, model="M6"), f1=f1k)
        ps["C6"] = out["C6"]["table"].loc["x", "p"]
    out["holm"] = holm(ps) if ps else {}
    out["effects"] = {k: classify_effect(*[out[k]["table"].loc["x", c] for c in ("hr", "hr_lo", "hr_hi")]) for k in ("C5", "C6") if k in out}
    return out


def run_family1_variants(facades, pluto, wl, base_cfg=None, names=None):
    """Run every Family 1 variant (one option at a time, estimates and intervals only, no significance claims) and the
    robustness label of 8 for the main estimate. Returns (table, robustness)."""
    base_cfg = base_cfg or F1Config()
    main = run_family1(facades, pluto, wl, base_cfg, f1=prepare_family1(facades, pluto, base_cfg))
    mh = hr_of(main)
    rows = []
    for name in (names or F1_VARIANTS):
        try:
            r = run_family1(facades, pluto, wl, dataclasses.replace(base_cfg, **F1_VARIANTS[name]))
            h = hr_of(r)
            rows.append({"variant": name, **h})
        except Exception as e:     # a variant that cannot be run is reported as such, never skipped quietly
            rows.append({"variant": name, "hr": np.nan, "error": f"{type(e).__name__}: {e}"})
    tab = pd.DataFrame(rows)
    return tab, robustness(mh["hr"], mh["lo"] > 1 or mh["hi"] < 1, list(tab["hr"]))


# ---------------------------------------------------------------------------------------------------------------
# Family 2
# ---------------------------------------------------------------------------------------------------------------
@dataclass
class F2Config:
    model: str = "M1"                     # 'M1' (C1, C4), 'M2' (C3: x split), 'M3' (C2: Early filers only)
    branch: str = "B"                     # 'A' term-average exposure, 'B' trailing workload ending on the expiry date
    D: pd.Timestamp = None                # shed pull date (required; logged in SOURCES.md)
    E: pd.Timestamp = L.E_FAMILY2
    gap: int = L.GAP_G                    # S1, S2
    link_window: tuple = L.LINK_WINDOW    # S3, S4
    lookback: int = L.LOOKBACK            # S5, S6
    covid: str = "drop_expiry"            # S8 'keep', S19 'drop_overlap'
    drop_2020_21: bool = False            # S7
    year_trend: bool = False              # S9
    cluster: str = "quarter"              # S10
    max_term: int = None                  # S11 (120)
    calendar_rule: bool = False           # S12
    include_standing: bool = False        # S13
    include_swarmp: bool = False          # S14
    only_not_carried: bool = False        # S15
    include_public: bool = False          # S16
    extra_steps: tuple = ()               # S17 adds the 2026 steps
    policy_steps: bool = True             # S18 False
    term_average_B: bool = False          # S20
    in_window_only: bool = False          # E8 for C2
    placebo: str = None                   # 'pl1' / 'pl2'


F2_VARIANTS = {
    "S1": dict(gap=0), "S2": dict(gap=90),
    "S3": dict(link_window=(-30, 90)), "S4": dict(link_window=(-180, 365)),
    "S5": dict(lookback=30), "S6": dict(lookback=180),
    "S7": dict(drop_2020_21=True), "S8": dict(covid="keep"), "S9": dict(year_trend=True),
    "S10a": dict(cluster="month"), "S10b": dict(cluster="twoway"), "S10c": dict(cluster="block"),
    "S11": dict(max_term=120), "S12": dict(calendar_rule=True), "S13": dict(include_standing=True),
    "S14": dict(include_swarmp=True), "S15": dict(only_not_carried=True), "S16": dict(include_public=True),
    "S17": dict(E=pd.Timestamp("2026-10-16"), extra_steps=("step_2026_01_26", "step_2026_08_20")),
    "S18": dict(policy_steps=False), "S19": dict(covid="drop_overlap"), "S20": dict(term_average_B=True),
}


def prepare_family2(facades, pluto, intervals, cfg):
    """Frame -> spells -> link -> decision points, with the filing attributes attached. Returns (dp, parts)."""
    if cfg.D is None:
        raise ValueError("cfg.D (the shed pull date) is required")
    statuses = ("UNSAFE", "SWARMP") if cfg.include_swarmp else ("UNSAFE",)
    E = pd.Timestamp(cfg.E)
    if cfg.E != L.E_FAMILY2:     # S17: end at the earlier of D and Oct 16, 2026
        E = min(pd.Timestamp(cfg.D), pd.Timestamp(cfg.E))
    frame = L.build_frame(facades, f_end=E, pluto=pluto, statuses=statuses, include_public=cfg.include_public)
    if cfg.only_not_carried:
        frame = frame[frame["carried_over"] == 0].reset_index(drop=True)
    spells = L.build_spells(intervals, gap=cfg.gap)
    linked, rep = L.link_filings(frame, spells, window=cfg.link_window, include_standing=cfg.include_standing)
    dp = L.decision_points(linked, E=E, D=cfg.D, gap=cfg.gap, covid=cfg.covid,
                           window_floor_days=cfg.link_window[0] if cfg.include_standing else None)
    keep = ["fid", "timing", "before_window", "group", "cycle", "borough", "stories", "wall_masonry", "wall_terracotta",
            "wall_missing", "carried_over", "owner_X", "no_pluto_match", "public_owner", "rating_swarmp", "block_key", "bin"]
    dp = dp.merge(frame[keep], on="fid", how="left")
    if cfg.drop_2020_21:
        dp = dp[~dp["e"].dt.year.isin([2020, 2021])]
    if cfg.max_term is not None:
        dp = dp[dp["term_days"] <= cfg.max_term]
    dp = dp.reset_index(drop=True)
    return dp, {"frame": frame, "spells": spells, "linked": linked, "link_report": rep}


def f2_exposure(dp, wl, cfg):
    """x (and x_own, x_other) for each decision point (6.2): Branch A the daily workload averaged over the term; Branch B
    the trailing workload ending on the expiry date (S20: term average instead). S12: calendar rule instead."""
    avg = (cfg.branch == "A") or cfg.term_average_B
    if cfg.calendar_rule:
        cal, nui = L.deadline_window_days(wl.origin, wl.n_days), L.nuisance_window_days(wl)
        if avg:
            w = L.window_share(cal, wl.origin, dp["term_start"], dp["e"]); nu = L.window_share(nui, wl.origin, dp["term_start"], dp["e"])
        else:
            lo = dp["e"] - pd.Timedelta(days=cfg.lookback)
            w = L.window_share(cal, wl.origin, lo, dp["e"]); nu = L.window_share(nui, wl.origin, lo, dp["e"])
        return pd.DataFrame({"x": w, "nuisance": nu})
    g = dp["group"].values
    if avg:
        tot = wl.term_mean(dp["term_start"], dp["e"], cfg.lookback)
        own = wl.term_mean(dp["term_start"], dp["e"], cfg.lookback, kind="own", groups=g)
        oth = wl.term_mean(dp["term_start"], dp["e"], cfg.lookback, kind="other", groups=g)
    else:
        tot = wl.trailing(dp["e"], cfg.lookback)
        own = wl.trailing(dp["e"], cfg.lookback, kind="own", groups=g)
        oth = wl.trailing(dp["e"], cfg.lookback, kind="other", groups=g)
    return pd.DataFrame({"x": tot, "x_own": own, "x_other": oth})


def design_family2(dp, wl, cfg):
    d = dp
    if cfg.model == "M3":
        d = d[d["timing"] == "Early"]
        if cfg.in_window_only:
            d = d[~d["before_window"]]
    d = d.reset_index(drop=True)
    ex = f2_exposure(d, wl, cfg)
    timing_terms = cfg.model != "M3"
    if cfg.model == "M2":
        parts = [ex[["x_own", "x_other"]]]
    elif cfg.calendar_rule:
        parts = [ex[["x", "nuisance"]]]
    else:
        parts = [ex[["x"]]]
    if cfg.placebo == "pl1":
        parts.append(pd.DataFrame({"pl1": (d["e"].dt.year.isin(L.DEADLINE_YEARS) & d["e"].dt.month.isin([8, 9, 10])).astype(float).values}))
    if cfg.placebo == "pl2":
        parts.append(pd.DataFrame({"pl2": wl.forward(d["e"], cfg.lookback)}))
    parts.append(pd.DataFrame({"winter_start": d["winter_start"].astype(float).values}))
    parts.append(shared_controls(d, timing_terms=timing_terms))
    parts.append(cat_dummies(L.spell_age_band(d["spell_age_months"]).values, "age", baseline="le6", levels=["le6", "6_12", "12_24", "gt24"]))
    parts.append(cat_dummies(L.term_band(d["term_days"]).values, "term", baseline="le100", levels=["le100", "101_200", "201_400", "gt400"]))
    parts.append(cat_dummies(d["e"].dt.month.values, "month", levels=list(range(1, 13))))
    if cfg.year_trend:
        parts.append(pd.DataFrame({"year_trend": (d["e"].dt.year - 2015).astype(float).values}))
    else:
        parts.append(cat_dummies(d["e"].dt.year.values, "year"))
    if cfg.policy_steps:
        steps = {"step_2019_12_17": L.POLICY_STEPS_MAIN["step_2019_12_17"], "step_2020_02_21": L.POLICY_STEPS_MAIN["step_2020_02_21"],
                 "step_2023_07_24": L.POLICY_STEPS_MAIN["step_2023_07_24"], "step_2025_04_17": L.POLICY_STEP_2025["step_2025_04_17"]}
        for nm in cfg.extra_steps:
            steps[nm] = L.POLICY_STEPS_S17[nm]
        parts.append(policy_columns(d["e"], steps))
    X = pd.concat([p.reset_index(drop=True) for p in parts], axis=1)
    X.insert(0, "const", 1.0)
    X, dropped = drop_dependent(X, protect=("const", "x", "x_other", "x_own", "pl1", "pl2", "winter_start"))
    d["quarter_cl"] = L.quarter_id(d["e"]).values
    d["month_cl"] = L.month_id(d["e"]).values
    groups = cluster_ids(cfg.cluster, d)
    return X, d["ended"].values, groups, d, {"dropped_columns": dropped}


def run_family2(dp, wl, cfg):
    X, y, groups, d, notes = design_family2(dp, wl, cfg)
    res = fit_cloglog(X, y, groups)
    K = n_clusters(groups)
    return {"table": coef_table(res, K), "K": K, "n_rows": int(len(y)), "n_events": int(y.sum()),
            "dropped_columns": notes["dropped_columns"], "converged": bool(getattr(res, "converged", True)), "cfg": cfg}


def family2_gates(dp, wl, cfg, linked_spells):
    """Stop rules and identifiability for C1 to C4 (7.7), on counts only."""
    ex = f2_exposure(dp, wl, cfg)
    x = ex["x"].values
    ev = dp["ended"].values.astype(bool)
    q = L.quarter_id(dp["e"])
    base_ok = (linked_spells >= 600) and (ev.sum() >= 400) and (q.nunique() >= MIN_QUARTERS)
    ident = identifiability(x, dp["timing"].values, ev)
    out = {"x_residual_sd": residual_sd_ratio(x, dp["e"].dt.year.values, dp["e"].dt.month.values, dp["timing"].values),
           "linked_spells": int(linked_spells), "ended_events": int(ev.sum()), "quarters": int(q.nunique()), "identifiability": ident}
    out["C1"] = {"run": bool(base_ok and ident["separable_all"]), "why": None if (base_ok and ident["separable_all"]) else ("stop rule" if not base_ok else "not separable from filer type")}
    early_events = int((ev & (dp["timing"].values == "Early")).sum())
    out["C2"] = {"run": bool(base_ok and early_events >= 100 and ident["separable_early"]), "early_events": early_events}
    x_other = ex["x_other"].values
    top = x_other >= np.quantile(x_other, BUSY_PCT)
    out["C3"] = {"run": bool(base_ok and int((ev & top).sum()) >= 60), "events_in_top30_x_other": int((ev & top).sum())}
    out["C4"] = {"run": bool(base_ok)}
    return out


def run_family2_confirmatory(facades, pluto, intervals, wl, branch, D):
    """C1 to C4 (7.2) under Branch A or B; Branch C means 'not testable on permit data' and nothing is run.
    Holm across the C1 to C4 that ran (n = 4 if all four)."""
    if branch not in ("A", "B"):
        return {"branch": branch, "note": "Family 2 not run (Branch C or undefined): not testable on permit data"}
    cfg = F2Config(branch=branch, D=pd.Timestamp(D))
    dp, parts = prepare_family2(facades, pluto, intervals, cfg)
    gates = family2_gates(dp, wl, cfg, parts["link_report"]["linked"])
    out = {"branch": branch, "gates": gates, "link_report": parts["link_report"], "link_share": L.link_share_report(parts["frame"], parts["linked"])}
    ps = {}
    if gates["C1"]["run"] or gates["C4"]["run"]:
        m1 = run_family2(dp, wl, dataclasses.replace(cfg, model="M1"))
        out["M1"] = m1
        out["PL1_M1"] = run_family2(dp, wl, dataclasses.replace(cfg, model="M1", placebo="pl1"))
        out["PL2_M1"] = run_family2(dp, wl, dataclasses.replace(cfg, model="M1", placebo="pl2"))
        out["PL1_warning"] = pl1_warning(out["PL1_M1"])
        if gates["C1"]["run"]:
            ps["C1"] = m1["table"].loc["x", "p"]
        if gates["C4"]["run"]:
            ps["C4"] = m1["table"].loc["winter_start", "p"]
    if gates["C2"]["run"]:
        out["M3"] = run_family2(dp, wl, dataclasses.replace(cfg, model="M3"))
        ps["C2"] = out["M3"]["table"].loc["x", "p"]
    if gates["C3"]["run"]:
        out["M2"] = run_family2(dp, wl, dataclasses.replace(cfg, model="M2"))
        ps["C3"] = out["M2"]["table"].loc["x_other", "p"]
    out["holm"] = holm(ps) if ps else {}
    return out


def run_family2_variants(facades, pluto, intervals, wl, branch, D, names=None):
    """Run every Family 2 variant for C1 (the HR on x in M1), one option at a time, and the robustness label of 8."""
    base = F2Config(branch=branch, D=pd.Timestamp(D))
    dp, _ = prepare_family2(facades, pluto, intervals, base)
    mh = hr_of(run_family2(dp, wl, base), "x")
    rows = []
    for name in (names or F2_VARIANTS):
        ov = dict(F2_VARIANTS[name])
        if branch == "A" and name == "S20":
            continue                       # S20 exists only under Branch B
        try:
            c = dataclasses.replace(base, **ov)
            d2, _ = prepare_family2(facades, pluto, intervals, c)
            rows.append({"variant": name, **hr_of(run_family2(d2, wl, c), "x")})
        except Exception as e:
            rows.append({"variant": name, "hr": np.nan, "error": f"{type(e).__name__}: {e}"})
    tab = pd.DataFrame(rows)
    return tab, robustness(mh["hr"], mh["lo"] > 1 or mh["hi"] < 1, list(tab["hr"]))
