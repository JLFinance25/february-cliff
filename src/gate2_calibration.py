# CALIBRATION of the Gate 2 standard errors on SIMULATED data (job B from the main session, Oct 18, 2026). No real
# filing-level data, no real shed rows and no repair durations are used. Imports the frozen modules unchanged
# (gate2_link.py, gate2_model.py, gate2_sim.py) and adds only new code here.
#
# Question: do 95% intervals for the workload effect really cover the truth 95% of the time, and do tests reject a true
# null 5% of the time, when the data have a shared shock in each calendar quarter (tau) and a workload series as rough as
# the real one? Three ways to get the interval are compared, for C5 and C6 (Family 1) and C1 (Family 2, annual terms):
#   (i)   pre-registered: statsmodels cloglog fit, quarter clusters, small-sample correction, t on K-1 df (PREREG 7.4);
#   (ii)  delete-one-quarter jackknife variance (CR3 type), computed with a one-step update per deleted quarter, t on K-1 df;
#   (iii) wild cluster score bootstrap-t by quarter (Kline and Santos 2012 type: restricted at the tested value, Rademacher
#         weights on the quarters' score vectors, B = 499). This is a fast approximation to the refitting wild cluster
#         bootstrap-t; --selftest compares it with a refitting bootstrap on one data set.
# "Coverage" = share of 95% intervals (for (iii): of tests at the 5% level of the true value) that contain the truth.
# "Reject 1" = share with p below 0.05 against HR = 1 (size when the truth is 1.00, power when it is 0.75).
#
# The simulated workload is as rough as the real one because the simulated filing dates are drawn from the real DAILY
# COUNT series of UNSAFE Initial filings (an aggregate, never filing-level detail); each simulated filing gets a random
# building, a deadline group and cycle weighted by closeness to that group's deadline, so busy periods are mostly last-
# minute filers (the confounding the identifiability rule is about).
#
# Run: .venv/bin/python -I src/gate2_calibration.py [--reps 120] [--workers 8] [--quick] [--selftest]
# Output: writeup/gate2-calibration.md, figures/gate2_calibration_reps.csv. Drafted by Claude (AI); directed and approved
# by Jayden Ling.
import os
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ[_v] = "1"
import argparse
import multiprocessing as mp
import pathlib
import sys
import time

import numpy as np
import pandas as pd
import scipy.stats as st

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gate2_link as L
import gate2_model as M
import gate2_sim as S

ROOT = pathlib.Path(__file__).resolve().parent.parent
D_PULL = pd.Timestamp("2026-10-17")
B_BOOT = 499
GROUP_DIGITS = {"A": [4, 5, 6, 9], "B": [0, 7, 8], "C": [1, 2, 3]}
_DAILY = None      # (origin, daily count array) set in each worker


# ---------------------------------------------------------------------------------------------------------------
# Simulated data with a real-shaped workload
# ---------------------------------------------------------------------------------------------------------------
def real_daily_counts():
    """Daily counts of UNSAFE Initial filings (any cycle), from the real processed file: dates only, aggregated."""
    df = pd.read_parquet(ROOT / "data" / "processed" / "facades_clean.parquet",
                         columns=["filing_type", "filing_status", "filing_date", "submitted_on", "group"])
    wl = L.Workload(df)
    return wl.origin, wl.total.copy()


def sim_rough_facades(seed, hr, tau, daily):
    """Simulated facade table whose daily UNSAFE counts equal the real ones (from 2013-01-01 to the pull date).
    Returns (facades, W) with W the brute-force trailing-90 workload by day (days since 2000-01-01)."""
    rng = np.random.default_rng(seed)
    origin, counts = daily
    days = pd.date_range(origin, periods=len(counts))
    keep = (days >= "2013-01-01") & (days <= D_PULL)
    dates = np.repeat(days[keep].values.astype("datetime64[D]"), counts[keep].astype(int))
    n = len(dates)
    in_frame_range = (dates >= np.datetime64("2015-02-21")) & (dates <= np.datetime64("2025-12-31"))
    # cycle and group by closeness to each (cycle, group) deadline
    combos = [(c, g) for c in (8, 9, 10) for g in "ABC"]
    dl = np.array([np.datetime64(str(L.deadline_of(c, g).date())) for c, g in combos])
    op = np.array([np.datetime64(str(L.window_open_of(c, g).date())) for c, g in combos])
    dist = np.abs((dates[:, None] - dl[None, :]).astype(int))
    inwin = (dates[:, None] >= op[None, :] - 240) & (dates[:, None] <= dl[None, :] + 400)
    w = (np.exp(-dist / 200.0) + 0.02) * inwin
    w[w.sum(axis=1) == 0] = 1e-9
    w = w / w.sum(axis=1, keepdims=True)
    pick = (rng.random(n)[:, None] > np.cumsum(w, axis=1)).sum(axis=1).clip(0, len(combos) - 1)
    cyc = np.array([combos[i][0] for i in pick]); grp = np.array([combos[i][1] for i in pick])
    cyc = np.where(in_frame_range, cyc, np.where(dates < np.datetime64("2015-02-21"), 7, 10))
    digit = np.array([rng.choice(GROUP_DIGITS[g]) for g in grp])
    block = rng.integers(1, 9000, n) * 10 + digit
    fac = pd.DataFrame({
        "tr6_no": [f"SIM-{i}" for i in range(n)], "control_no": "x", "filing_type": "Initial", "cycle": cyc,
        "bin": (1000000 + rng.permutation(5_000_000)[:n]).astype(str), "borough": rng.choice(S.BOROUGHS, n),
        "block": block.astype(str), "lot": rng.integers(1, 200, n).astype(str),
        "filing_date": pd.to_datetime(dates), "submitted_on": pd.to_datetime(dates), "filing_status": "UNSAFE",
        "current_status": "UNSAFE", "prior_status": rng.choice(["SWARMP", "UNSAFE", "SAFE", None], n, p=[0.35, 0.2, 0.3, 0.15]),
        "exterior_wall_material_s_": rng.choice(np.array(S.WALLS, dtype=object), n), "group": grp})
    all_days, W = S.brute_daily(dates, "2000-01-01", "2030-12-31")
    # ---- Family 1 clearing filings: discrete-time hazard with the planted workload effect and quarter shocks ----
    fm = fac["cycle"].isin([8, 9]).values & (fac["filing_date"] <= "2024-12-31").values
    x = np.where(fm, W[(dates - all_days[0]).astype(int)], 0.0)
    q = L.quarter_id(fac["filing_date"]).values
    shock = {qq: (rng.normal(0, tau) if tau > 0 else 0.0) for qq in np.unique(q)}
    sh = np.array([shock[v] for v in q])
    carried = fac["prior_status"].isin(["SWARMP", "UNSAFE"]).values
    nsteps = 160
    ks = np.arange(1, nsteps + 1)
    base = np.array([S.BASE_LOG_HAZ.get(k, np.log(0.03) if k <= 12 else (np.log(0.015) if k <= 24 else np.log(0.005))) for k in ks])
    idx = np.where(fm)[0]
    eta = base[None, :] + (np.log(hr) * x[idx] + carried[idx] * (-0.15) + sh[idx])[:, None]
    hit = rng.random((len(idx), nsteps)) < (1 - np.exp(-np.exp(eta)))
    ek = np.where(hit.any(axis=1), hit.argmax(axis=1) + 1, 0)
    ok = ek > 0
    cd = pd.to_datetime(dates[idx][ok]) + pd.to_timedelta((ek[ok] - 1) * 30 + rng.integers(0, 30, ok.sum()), unit="D")
    am = fac.iloc[idx[ok]].copy()
    am["tr6_no"] = am["tr6_no"] + "-A"; am["filing_type"] = "Amended"; am["filing_status"] = "SAFE"; am["current_status"] = "SAFE"
    am["filing_date"] = cd; am["submitted_on"] = cd; am["prior_status"] = None
    fac = pd.concat([fac, am], ignore_index=True)
    return fac, (all_days, W)


def sim_intervals(facades, all_days, W, hr, tau, seed, link_prob=0.75):
    """Annual-term (Branch B world) shed permit intervals for the simulated frame; the shed ends at an expiry with the
    cloglog hazard exp(a + log(hr) * workload at expiry + quarter shock). No cleaning step (that is unit-tested)."""
    rng = np.random.default_rng(seed + 17)
    frame = L.build_frame(facades, f_end=L.E_FAMILY2)
    keep = rng.random(len(frame)) < link_prob
    bins = frame["bin"].values[keep]
    F = frame["F"].values.astype("datetime64[D]")[keep]
    cur = F + rng.integers(-60, 120, keep.sum()).astype("timedelta64[D]")
    d0 = all_days[0]
    qs = {qq: (rng.normal(0, tau) if tau > 0 else 0.0) for qq in range(2013 * 4, 2028 * 4)}
    out = []
    for _ in range(40):
        if len(cur) == 0:
            break
        end = cur + rng.integers(300, 401, len(cur)).astype("timedelta64[D]")
        out.append(pd.DataFrame({"bin": bins, "start": pd.to_datetime(cur), "end": pd.to_datetime(end), "source": "sim"}))
        e_idx = (end - d0).astype(int)
        endq = L.quarter_id(pd.Series(pd.to_datetime(end))).values
        eta = np.log(0.30) + np.log(hr) * W[e_idx] + np.array([qs[v] for v in endq])
        ended = rng.random(len(cur)) < (1 - np.exp(-np.exp(eta)))
        cont = (~ended) & (end <= np.datetime64("2026-06-30"))
        cur = (end + rng.integers(0, 16, len(cur)).astype("timedelta64[D]"))[cont]
        bins = bins[cont]
    return pd.concat(out, ignore_index=True)


# ---------------------------------------------------------------------------------------------------------------
# Fitting pieces for the alternatives
# ---------------------------------------------------------------------------------------------------------------
def irls(X, y, offset=None, beta0=None, tol=1e-10, maxit=100):
    """cloglog IRLS with an optional offset (used for the restricted fits)."""
    X = np.asarray(X, float); y = np.asarray(y, float)
    off = np.zeros(len(y)) if offset is None else np.asarray(offset, float)
    beta = np.zeros(X.shape[1]) if beta0 is None else beta0.copy()
    if beta0 is None:
        mu0 = np.clip((y + y.mean()) / 2, 1e-6, 1 - 1e-6)
        beta = np.linalg.lstsq(X, np.log(-np.log1p(-mu0)) - off, rcond=None)[0]

    def parts(b):
        eta = np.clip(X @ b + off, -30, 6)
        ee = np.exp(eta)
        mu = np.clip(-np.expm1(-ee), 1e-12, 1 - 1e-12)
        return eta, mu, ee * np.exp(-ee)

    def dev(mu):
        return -2 * np.sum(y * np.log(mu) + (1 - y) * np.log1p(-mu))

    eta, mu, dmu = parts(beta); d_old = dev(mu)
    for _ in range(maxit):
        wgt = dmu**2 / (mu * (1 - mu))
        z = eta - off + (y - mu) / dmu
        new = np.linalg.solve((X.T * wgt) @ X, (X.T * wgt) @ z)
        step = 1.0
        while True:
            cand = beta + step * (new - beta)
            e2, m2, dm2 = parts(cand); d_new = dev(m2)
            if d_new <= d_old + 1e-10 or step < 1e-4:
                break
            step /= 2
        delta = np.max(np.abs(cand - beta))
        beta, eta, mu, dmu, d_old = cand, e2, m2, dm2, d_new
        if delta < tol:
            break
    return beta


class ClusterFit:
    """Per-quarter score vectors S_g, information blocks A_g and total A at a given coefficient vector."""

    def __init__(self, X, y, beta, gidx):
        order = np.argsort(gidx, kind="stable")
        self.X, self.y, self.g = X[order], y[order], gidx[order]
        self.N, self.k = self.X.shape
        eta = np.clip(self.X @ beta, -30, 6)
        ee = np.exp(eta)
        mu = np.clip(-np.expm1(-ee), 1e-12, 1 - 1e-12)
        dmu = ee * np.exp(-ee)
        w = dmu**2 / (mu * (1 - mu))
        s = self.X * (((self.y - mu) / (mu * (1 - mu))) * dmu)[:, None]
        starts = np.r_[0, np.flatnonzero(np.diff(self.g)) + 1]
        self.K = len(starts)
        self.S = np.add.reduceat(s, starts, axis=0)
        ends = np.r_[starts[1:], self.N]
        self.Ag = np.stack([(self.X[a:b].T * w[a:b]) @ self.X[a:b] for a, b in zip(starts, ends)])
        self.A = self.Ag.sum(axis=0)
        self.Binv = np.linalg.pinv(self.A)
        self.c = (self.K / (self.K - 1)) * ((self.N - 1) / (self.N - self.k))

    def cr1_se(self, j):
        """Pre-registered style cluster-robust SE (with the small-sample factor) for coefficient j."""
        a = self.Binv[j]
        return float(np.sqrt(self.c * np.sum((self.S @ a) ** 2)))


def jackknife_se(cf, j):
    """CR3-type delete-one-quarter jackknife SE, using one-step updates: beta_(g) = beta - (A - A_g)^-1 S_g."""
    dev = np.empty(cf.K)
    for g in range(cf.K):
        dev[g] = -(np.linalg.lstsq(cf.A - cf.Ag[g], cf.S[g], rcond=1e-10)[0])[j]    # minimum-norm solve if a dummy is lost with the quarter
    return float(np.sqrt((cf.K - 1) / cf.K * np.sum(dev**2)))


def boot_p(X, y, gidx, j, b0, beta_hat, t_obs, rng, B=B_BOOT):
    """Wild cluster score bootstrap-t p-value for H0: beta_j = b0 (restricted fit, Rademacher weights over quarters)."""
    keep = [i for i in range(X.shape[1]) if i != j]
    beta_r = np.zeros(X.shape[1])
    beta_r[keep] = irls(X[:, keep], y, offset=X[:, j] * b0, beta0=beta_hat[keep])
    beta_r[j] = b0
    cf = ClusterFit(X, y, beta_r, gidx)
    Wt = rng.choice([-1.0, 1.0], size=(B, cf.K))
    Dl = (Wt @ cf.S) @ cf.Binv.T                                    # B x k  : approximates beta* - beta_r
    U = Wt[:, :, None] * cf.S[None, :, :] - np.einsum("gij,bj->bgi", cf.Ag, Dl)
    a = cf.Binv[j]
    v = (U @ a)                                                     # B x K
    se = np.sqrt(cf.c * np.sum(v**2, axis=1))
    tb = Dl[:, j] / se
    return float((np.sum(np.abs(tb) >= abs(t_obs)) + 1) / (B + 1))


def evaluate(X, y, groups, hr_true, seed):
    """One data set, one test: the three estimators. Returns a flat dict."""
    cols = list(X.columns)
    j = cols.index("x")
    Xv = X.values.astype(float)
    res = M.fit_cloglog(X, y, groups)
    beta = np.asarray(res.params)
    K = M.n_clusters(groups)
    gidx = pd.factorize(np.asarray(groups))[0]
    tab = M.coef_table(res, K).iloc[j]
    b_true = float(np.log(hr_true))
    tcrit = st.t.ppf(0.975, K - 1)
    cf = ClusterFit(Xv, np.asarray(y, float), beta, gidx)
    se_j = jackknife_se(cf, j)
    se1 = cf.cr1_se(j)
    rng = np.random.default_rng(seed)
    out = dict(K=K, events=int(np.sum(y)), rows=len(y), log_err=float(beta[j] - b_true),
               pre_cover=bool(tab["hr_lo"] <= hr_true <= tab["hr_hi"]), pre_reject1=bool(tab["p"] < 0.05),
               pre_halfw=float(np.log(tab["hr_hi"] / tab["hr_lo"]) / 2),
               jack_cover=bool(abs(beta[j] - b_true) <= tcrit * se_j), jack_reject1=bool(abs(beta[j]) > tcrit * se_j),
               jack_halfw=float(tcrit * se_j), se_ratio_jack_pre=float(se_j / tab["se"]), se_mine_over_sm=float(se1 / tab["se"]))
    p_true = boot_p(Xv, np.asarray(y, float), gidx, j, b_true, beta, (beta[j] - b_true) / se1, rng)
    out["boot_cover"] = bool(p_true >= 0.05)
    if abs(b_true) < 1e-12:
        out["boot_reject1"] = bool(p_true < 0.05)
    else:
        out["boot_reject1"] = bool(boot_p(Xv, np.asarray(y, float), gidx, j, 0.0, beta, beta[j] / se1, rng) < 0.05)
    return out


# ---------------------------------------------------------------------------------------------------------------
# One replicate
# ---------------------------------------------------------------------------------------------------------------
def init_worker(daily):
    global _DAILY
    _DAILY = daily


def one_rep(job):
    try:
        return _one_rep(job)
    except Exception as e:      # recorded and counted in the report, never dropped quietly
        hr, tau, rep = job
        return [dict(family="ERR", test=f"{type(e).__name__}: {e}"[:80], hr=hr, tau=tau, rep=rep)]


def _one_rep(job):
    hr, tau, rep = job
    seed = 10_000 * rep + int(round(hr * 100)) * 7 + int(round(tau * 100)) * 131
    t0 = time.time()
    fac, (days, W) = sim_rough_facades(seed, hr, tau, _DAILY)
    wl = L.Workload(fac)
    rows = []
    cfg1 = M.F1Config()
    f1 = M.prepare_family1(fac, None, cfg1)
    for test, cfg in (("C5", cfg1), ("C6", M.F1Config(model="M6"))):
        X, y, groups, _r, _n = M.design_family1(f1, wl, cfg)
        rows.append(dict(family="F1", test=test, hr=hr, tau=tau, rep=rep, **evaluate(X, y, groups, hr, seed + 1)))
    iv = sim_intervals(fac, days, W, hr, tau, seed)
    cfg2 = M.F2Config(branch="B", D=D_PULL)
    dp, _p = M.prepare_family2(fac, None, iv, cfg2)
    X, y, groups, _d, _n = M.design_family2(dp, wl, cfg2)
    rows.append(dict(family="F2", test="C1", hr=hr, tau=tau, rep=rep, **evaluate(X, y, groups, hr, seed + 2)))
    for r in rows:
        r["secs"] = time.time() - t0
    return rows


# ---------------------------------------------------------------------------------------------------------------
# Self-test of the approximations (small, one data set)
# ---------------------------------------------------------------------------------------------------------------
def selftest(daily):
    lines = []
    fac, _ = sim_rough_facades(4242, 0.75, 0.10, daily)
    wl = L.Workload(fac)
    f1 = M.prepare_family1(fac, None, M.F1Config())
    X, y, groups, _r, _n = M.design_family1(f1, wl, M.F1Config())
    j = list(X.columns).index("x")
    Xv = X.values.astype(float); yv = np.asarray(y, float)
    res = M.fit_cloglog(X, y, groups); beta = np.asarray(res.params)
    gidx = pd.factorize(np.asarray(groups))[0]
    cf = ClusterFit(Xv, yv, beta, gidx)
    lines.append(f"- My cluster SE for the workload term over statsmodels': {cf.cr1_se(j) / res.bse.iloc[j]:.4f} (expected about 1).")
    # exact delete-one-quarter jackknife (refit) against the one-step version
    ids = np.unique(gidx)
    exact = []
    for g in ids[:15]:
        m = gidx != g
        exact.append(irls(Xv[m], yv[m], beta0=beta)[j] - beta[j])
    one = [-(np.linalg.lstsq(cf.A - cf.Ag[i], cf.S[i], rcond=1e-10)[0])[j] for i in range(len(ids))]
    # ClusterFit sorts by cluster label; ids are sorted labels so index i matches label ids[i]
    lines.append(f"- One-step against exact (refit) deletion of the first 15 quarters: largest difference in the workload coefficient {np.max(np.abs(np.array(exact) - np.array(one[:15]))):.2e} (typical size {np.mean(np.abs(exact)):.2e}).")
    # refitting wild bootstrap-t against the score bootstrap, H0: beta_x = 0
    rng = np.random.default_rng(7)
    t_obs = beta[j] / cf.cr1_se(j)
    p_score = boot_p(Xv, yv, gidx, j, 0.0, beta, t_obs, rng, B=499)
    keep = [i for i in range(Xv.shape[1]) if i != j]
    beta_r = irls(Xv[:, keep], yv, beta0=beta[keep])
    eta_r = Xv[:, keep] @ beta_r
    mu_r = -np.expm1(-np.exp(np.clip(eta_r, -30, 6)))
    # a wild bootstrap for a binary outcome: flip the sign of each quarter's residual (y - mu), add to mu, redraw as 0/1 by clipping
    resid = yv - mu_r
    tb = []
    for b in range(99):
        wq = rng.choice([-1.0, 1.0], size=len(ids))[gidx]
        ystar = np.clip(mu_r + wq * resid, 0, 1)
        ystar = (rng.random(len(yv)) < ystar).astype(float)
        bs = irls(Xv, ystar, beta0=beta)
        cfb = ClusterFit(Xv, ystar, bs, gidx)
        tb.append(bs[j] / cfb.cr1_se(j))
    p_refit = (np.sum(np.abs(tb) >= abs(t_obs)) + 1) / (len(tb) + 1)
    lines.append(f"- Test of beta_x = 0 on one data set (t = {t_obs:.2f}): score bootstrap p = {p_score:.3f}; refitting wild bootstrap (B = 99, outcome redrawn) p = {p_refit:.3f}. These are two different bootstraps; they should agree roughly, not exactly.")
    return lines


# ---------------------------------------------------------------------------------------------------------------
def summarize(df):
    out = ["| Family | Test | Planted HR | tau | Reps | Mean log-HR error | Pre-registered: coverage | Reject 1 | Half-width | Jackknife: coverage | Reject 1 | Half-width | Bootstrap-t: coverage | Reject 1 |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    def pm(p, n):
        return f"{p:.2f} ({np.sqrt(max(p * (1 - p), 1e-9) / n):.2f})"
    for (fam, test, hr, tau), g in df.groupby(["family", "test", "hr", "tau"]):
        n = len(g)
        out.append(f"| {fam} | {test} | {hr:.2f} | {tau:.2f} | {n} | {g['log_err'].mean():+.3f} | {pm(g['pre_cover'].mean(), n)} | {pm(g['pre_reject1'].mean(), n)} | {g['pre_halfw'].mean():.3f} | "
                   f"{pm(g['jack_cover'].mean(), n)} | {pm(g['jack_reject1'].mean(), n)} | {g['jack_halfw'].mean():.3f} | {pm(g['boot_cover'].mean(), n)} | {pm(g['boot_reject1'].mean(), n)} |")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=120)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    daily = real_daily_counts()
    if a.selftest:
        print("\n".join(selftest(daily)))
        return
    reps = 2 if a.quick else a.reps
    jobs = [(hr, tau, r) for hr in (1.0, 0.75) for tau in (0.0, 0.10, 0.20) for r in range(reps)]
    t0 = time.time()
    res = []
    with mp.get_context("spawn").Pool(a.workers, initializer=init_worker, initargs=(daily,)) as pool:
        for i, rows in enumerate(pool.imap_unordered(one_rep, jobs, chunksize=1)):
            res.extend(rows)
            if (i + 1) % 20 == 0:
                print(f"{i + 1}/{len(jobs)} replicates, {time.time() - t0:.0f}s", flush=True)
    df = pd.DataFrame(res)
    n_err = int((df["family"] == "ERR").sum())
    err_txt = df.loc[df["family"] == "ERR", "test"].value_counts().to_dict() if n_err else {}
    df = df[df["family"] != "ERR"]
    suffix = "_quick" if a.quick else ""
    (ROOT / "figures").mkdir(exist_ok=True)
    df.to_csv(ROOT / "figures" / f"gate2_calibration_reps{suffix}.csv", index=False)
    lines = ["# Calibration of the Gate 2 standard errors (simulated data)", "",
             f"Run by `src/gate2_calibration.py`, {reps} repeats per cell, {time.time() - t0:.0f} s on {a.workers} workers. **Simulated data only**; the real file contributed only the daily COUNT series of UNSAFE Initial filings (an aggregate) that sets the roughness of the simulated workload.", "",
             "Cells: planted workload HR 1.00 and 0.75; shared per-quarter shock tau 0, 0.10, 0.20; Family 1 C5 (all filings) and C6 (Early filers), Family 2 C1 (annual terms). Numbers in the table are shares with the Monte Carlo standard error in brackets. **Coverage** = how often the 95% interval (for the bootstrap: the 5% test of the true value) contains the truth; intended 0.95. **Reject 1** = share with p below 0.05 against HR = 1: the false-alarm rate when the planted HR is 1.00 (intended 0.05) and the power when it is 0.75. **Half-width** = average half-width of the interval on the log scale.", ""]
    lines += [f"Failed replicates (errors): {n_err} {err_txt}", ""]
    lines += summarize(df)
    lines += ["", "## Decision rule fixed by the main session", "",
              "The pre-registered estimator stays primary unless, at tau = 0.10, its coverage in Family 1 (C5) or Family 2 (C1) is below 0.92 AND an alternative reaches 0.93 or more. Values at tau = 0.10 (pooled over the two planted HRs, then each):", "",
              "| Test | HR cell | Pre-registered | Jackknife | Bootstrap-t | Rule triggered? |", "|---|---|---|---|---|---|"]
    for test in ("C5", "C1"):
        for label, sel in (("pooled", df[(df.test == test) & (df.tau == 0.10)]), ("HR 1.00", df[(df.test == test) & (df.tau == 0.10) & (df.hr == 1.0)]), ("HR 0.75", df[(df.test == test) & (df.tau == 0.10) & (df.hr == 0.75)])):
            p, j, b = sel.pre_cover.mean(), sel.jack_cover.mean(), sel.boot_cover.mean()
            trig = (p < 0.92) and (max(j, b) >= 0.93)
            lines.append(f"| {test} | {label} (n={len(sel)}) | {p:.3f} | {j:.3f} | {b:.3f} | {'YES' if trig else 'no'} |")
    lines += ["", "The main session decides; this file only reports.", "",
              "## Checks of the approximations", ""]
    try:
        lines += selftest(daily)
    except Exception as e:      # reported, never skipped quietly
        lines.append(f"- self-test failed: {type(e).__name__}: {e}")
    (ROOT / "writeup" / f"gate2-calibration{suffix}.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
