# The simulated-data check required by PREREG section 5 before any repair duration or shed row is opened:
#   1. the workload code matches a brute-force count;
#   2. the hand-written numpy cloglog fit and the statsmodels fit agree to 4 decimals;
#   3. a planted hazard ratio is recovered and a planted null stays null (Family 1: C5 and C6; Family 2: C1 to C4);
#   4. quarter clustering gives honest intervals when a shared per-quarter shock is planted (block clustering does not);
#   5. the slow-owner story (late filers slow, workload does nothing) is not mistaken for a workload effect;
#   6. every variant (V1 to V11, S1 to S20) and both placebos run;
#   7. stop rules, the identifiability rule and the branch choice behave on simulated tables.
# Uses ONLY simulated data (src/gate2_sim.py). Run: .venv/bin/python -I src/gate2_simcheck.py [--quick]
# Writes writeup/gate2-simulated-check.md and figures/gate2_simcheck_results.csv. Drafted by Claude (AI); directed and
# approved by Jayden Ling.
import dataclasses
import pathlib
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gate2_link as L
import gate2_model as M
import gate2_sim as S

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUICK = "--quick" in sys.argv
N_REP = 4 if QUICK else 20
D_PULL = pd.Timestamp("2026-10-17")
lines, rows = [], []


def say(s=""):
    print(s, flush=True)
    lines.append(s)


def rec(section, name, **kw):
    rows.append(dict(section=section, name=name, **kw))


def fmt(h):
    return f"{h['hr']:.3f} ({h['lo']:.3f} to {h['hi']:.3f})"


def f1_run(fac, wl, cfg, f1=None):
    r = M.run_family1(fac, None, wl, cfg, f1=f1)
    return r, M.hr_of(r)


# ------------------------------------------------------------------------------------------------------------
say("# Gate 2 code: simulated-data check")
say()
say(f"Run by `src/gate2_simcheck.py` on {pd.Timestamp.now().date()} (Claude, Sonnet 5.5). **Simulated data only.** No real shed-permit row and no real repair duration was opened.")
say("The real facade file was not used in this script at all. Planted effects are in log-hazard units per wave unit (400 UNSAFE filings in 90 days).")
say()

# 1 ---- workload vs brute force ---------------------------------------------------------------------------
fac, truth = S.sim_facades(seed=11, planted_hr=0.75)
wl = L.Workload(fac)
uns = fac[(fac.filing_type == "Initial") & (fac.filing_status == "UNSAFE")]
qd = pd.Series(pd.date_range("2013-01-01", "2026-06-30", freq="3D"))
mx = max(np.abs(S.brute_workload(uns.filing_date.values, qd.values, lb) - wl.trailing(qd, lb)).max() for lb in (30, 90, 180))
say("## 1. Workload code against a brute-force count")
say(f"Largest difference over {len(qd)} dates and look-backs of 30, 90 and 180 days: **{mx:.2e}** (must be 0).")
assert mx < 1e-12
rec("1", "workload_vs_bruteforce", value=mx)
say()

# 2 ---- hand-written fit vs statsmodels on the real design matrix ------------------------------------------
cfg = M.F1Config()
f1 = M.prepare_family1(fac, None, cfg)
X, y, groups, r, notes = M.design_family1(f1, wl, cfg)
res = M.fit_cloglog(X, y, groups)
b_np, cov_np = M.cloglog_irls(X.values, y, groups=groups)
dmax = float(np.max(np.abs(b_np - np.asarray(res.params))))
ratio = np.sqrt(np.diag(cov_np)) / np.asarray(res.bse)
say("## 2. Hand-written numpy fit against statsmodels (the M5 design on simulated data)")
say(f"{X.shape[0]:,} rows, {X.shape[1]} columns. Largest coefficient difference **{dmax:.1e}** (must be below 5e-5 to agree at 4 decimals). Ratio of the hand-written clustered SE to statsmodels': min {ratio.min():.4f}, max {ratio.max():.4f}.")
assert dmax < 5e-5, dmax
rec("2", "numpy_vs_statsmodels_max_coef_diff", value=dmax)
say()

# 3 ---- planted effect and null: one run each -------------------------------------------------------------
say("## 3. Planted effect and null (one simulated data set each; seed 11 and 12)")
say("| Scenario | Test | Planted HR | Estimate (95% t interval, K-1 df) | Quarters K | Events |")
say("|---|---|---|---|---|---|")
for label, hr_, seed in [("planted", 0.75, 11), ("null", 1.00, 12)]:
    fac_, tr_ = S.sim_facades(seed=seed, planted_hr=hr_)
    wl_ = L.Workload(fac_)
    out = M.run_family1_confirmatory(fac_, None, wl_)
    for k in ("C5", "C6"):
        if k in out:
            h = M.hr_of(out[k])
            say(f"| {label} | {k} | {hr_:.2f} | {fmt(h)} | {h['K']} | {h['events']:,} |")
            rec("3", f"{label}_{k}", planted=hr_, hr=h["hr"], lo=h["lo"], hi=h["hi"], p=h["p"], K=h["K"], events=h["events"])
        else:
            say(f"| {label} | {k} | {hr_:.2f} | not run: {out['gates'][k]['why']} | | |")
    say(f"|  | Holm | | {', '.join(f'{k}: p={v['p']:.4f} sig={v['significant']}' for k, v in out['holm'].items())} | | |")
    for k in ("PL1_M5", "PL2_M5"):
        if k in out:
            t = out[k]["table"].loc[k.split("_")[0].lower()]
            say(f"|  | placebo {k.split('_')[0]} | 1.00 expected | {t['hr']:.3f} ({t['hr_lo']:.3f} to {t['hr_hi']:.3f}) | | |")
            rec("3", f"{label}_{k}", hr=t["hr"], lo=t["hr_lo"], hi=t["hr_hi"])
    if label == "planted":
        planted_out = out
say()

# 4 ---- Monte Carlo: bias and coverage; quarter vs block clustering -------------------------------------------
say(f"## 4. Repeated simulations ({N_REP} data sets per row): bias and coverage of the 95% interval")
say("Coverage = how often the interval contains the planted value. With few replicates it is rough; it is a sanity check, not a measurement.")
say("| Scenario | Estimator | Planted HR | Mean estimate | Mean log-HR error | Coverage | Mean interval half-width (log) |")
say("|---|---|---|---|---|---|---|")
mc_summary = {}
for scen, kw in [("no shared shock", dict(tau=0.0)), ("shared quarter shock tau=0.15", dict(tau=0.15))]:
    for hr_ in (0.75, 1.0):
        store = {"C5 quarter": [], "C5 block (V11c)": [], "C6 quarter": []}
        for rep in range(N_REP):
            fac_, _ = S.sim_facades(seed=100 + rep, planted_hr=hr_, **kw)
            wl_ = L.Workload(fac_)
            f1_ = M.prepare_family1(fac_, None, M.F1Config())
            store["C5 quarter"].append(f1_run(fac_, wl_, M.F1Config(), f1_)[1])
            store["C5 block (V11c)"].append(f1_run(fac_, wl_, M.F1Config(cluster="block"), f1_)[1])
            store["C6 quarter"].append(f1_run(fac_, wl_, M.F1Config(model="M6"), f1_)[1])
        for est, hs in store.items():
            lh = np.log([h["hr"] for h in hs])
            cov = np.mean([(h["lo"] <= hr_ <= h["hi"]) for h in hs])
            hw = np.mean([(np.log(h["hi"]) - np.log(h["lo"])) / 2 for h in hs])
            say(f"| {scen} | {est} | {hr_:.2f} | {np.exp(lh.mean()):.3f} | {lh.mean() - np.log(hr_):+.3f} | {cov:.2f} | {hw:.3f} |")
            rec("4", f"{scen}|{est}|{hr_}", mean_hr=float(np.exp(lh.mean())), bias_log=float(lh.mean() - np.log(hr_)), coverage=float(cov), half_width_log=float(hw))
            mc_summary[(scen, est, hr_)] = (lh.mean() - np.log(hr_), cov)
say()

# 5 ---- slow owners, no workload effect ----------------------------------------------------------------------
say("## 5. The slow-owner trap: late filers are slow, workload does nothing (planted workload HR = 1.00, late-filer log hazard -0.5)")
fac_, _ = S.sim_facades(seed=21, planted_hr=1.0, late_penalty=-0.5)
wl_ = L.Workload(fac_)
f1_ = M.prepare_family1(fac_, None, M.F1Config())
crude = f1_run(fac_, wl_, M.F1Config(timing_terms=False), f1_)[1]
c5 = f1_run(fac_, wl_, M.F1Config(), f1_)[1]
c6 = f1_run(fac_, wl_, M.F1Config(model="M6"), f1_)[1]
say(f"- Crude estimate (no filing-timing terms, E5): {fmt(crude)}. Late filers crowd into busy periods, so the crude estimate is pulled below 1.")
say(f"- C5 (with filing-timing terms): {fmt(c5)}.")
say(f"- C6 (early filers only): {fmt(c6)}.")
rec("5", "crude", **{k: crude[k] for k in ("hr", "lo", "hi")}); rec("5", "C5", **{k: c5[k] for k in ("hr", "lo", "hi")}); rec("5", "C6", **{k: c6[k] for k in ("hr", "lo", "hi")})
say()

# 6 ---- all Family 1 variants and placebos -------------------------------------------------------------------
say("## 6. Every Family 1 variant and both placebos run (planted HR 0.75, seed 11)")
say("| Variant | HR for workload (95% interval) | Rows | Events | Dropped columns |")
say("|---|---|---|---|---|")
f1_base = M.prepare_family1(fac, None, M.F1Config())
for name in ["main"] + list(M.F1_VARIANTS):
    ov = {} if name == "main" else M.F1_VARIANTS[name]
    c = dataclasses.replace(M.F1Config(), **ov)
    r_, h = f1_run(fac, wl, c, None if ov else f1_base)
    assert np.isfinite(h["hr"]) and r_["converged"], name
    say(f"| {name} | {fmt(h)} | {r_['n_rows']:,} | {r_['n_events']:,} | {', '.join(r_['dropped_columns']) or 'none'} |")
    rec("6", name, hr=h["hr"], lo=h["lo"], hi=h["hi"], rows=r_["n_rows"], events=r_["n_events"])
for pl in ("pl1", "pl2"):
    r_ = M.run_family1(fac, None, wl, M.F1Config(placebo=pl), f1=f1_base)
    t = r_["table"].loc[pl]
    say(f"| placebo {pl.upper()} | {t['hr']:.3f} ({t['hr_lo']:.3f} to {t['hr_hi']:.3f}) | {r_['n_rows']:,} | {r_['n_events']:,} | |")
    rec("6", pl, hr=t["hr"], lo=t["hr_lo"], hi=t["hr_hi"])
r_ = M.run_family1(fac, None, wl, M.F1Config(split_own_other=True), f1=f1_base)
say(f"| E10 own / other | own {r_['table'].loc['x_own','hr']:.3f}, other {r_['table'].loc['x_other','hr']:.3f} | {r_['n_rows']:,} | {r_['n_events']:,} | |")
say()

# 7 ---- gates ------------------------------------------------------------------------------------------------
say("## 7. Stop rules, availability rule and identifiability rule on simulated tables")
g = M.family1_gates(f1_base, wl)
say(f"- Planted data set: availability by cycle {({k: round(v, 3) for k, v in g['availability']['by_cycle'].items()})}; C5 run = {g['C5']['run']}, C6 run = {g['C6']['run']}; separable (all four cells) = {g['identifiability']['separable_all']}.")
cells = g["identifiability"]["cells"]
say("  Corner cells (rows / events): " + ", ".join(f"{k} {v['rows']}/{v['events']}" for k, v in cells.items()))
small = f1_base.sample(400, random_state=1)
g2 = M.family1_gates(small, wl)
say(f"- A 400-filing sample: C5 run = {g2['C5']['run']} ({g2['C5']['why']}).")
bad = f1_base.copy(); bad["has_clear_any_date"] = False
g3 = M.family1_gates(bad, wl)
say(f"- No clearing filings at all: C5 run = {g3['C5']['run']} ({g3['C5']['why']}).")
tight = f1_base.copy()
xx = wl.trailing(tight["F"])
tight.loc[(xx >= np.quantile(xx, 0.7)), "timing"] = "Past-deadline"          # nobody early in a busy period
g4 = M.family1_gates(tight, wl)
say(f"- Early filers removed from busy periods: C5 run = {g4['C5']['run']} ({g4['C5']['why']}); C6 run = {g4['C6']['run']} ({g4['C6']['why']}).")
assert g["C5"]["run"] and (not g2["C5"]["run"]) and (not g3["C5"]["run"]) and (not g4["C5"]["run"])
say()

# 8 ---- Family 2 -----------------------------------------------------------------------------------------------
say("## 8. Family 2 (shed permits), simulated")
fac2, _ = S.sim_facades(seed=31, planted_hr=0.75)
wl2 = L.Workload(fac2)
pluto = S.sim_pluto(fac2)
for branch, hr_ in [("B", 0.75), ("B", 1.0), ("A", 0.75)]:
    dobnow, legacy, tr = S.sim_sheds(fac2, seed=41, branch=branch, planted_hr=hr_, winter_hr=0.80 if hr_ < 1 else 1.0)
    a, qa = L.clean_dobnow(dobnow, ["Sidewalk Shed"])
    b, qb = L.clean_legacy(legacy, ["SH"], date_format="%m/%d/%Y")
    iv = L.combine_intervals(a, b)
    chk = L.structure_check(iv)
    br = L.choose_branch(chk)
    say(f"**World: {'annual' if branch == 'B' else '90-day'} terms, workload HR planted {hr_:.2f}, winter-start HR planted {0.8 if hr_ < 1 else 1.0:.2f}.** "
        f"Cleaning: DOB NOW {qa['rows_in']:,} -> {qa['rows_out']:,} rows, legacy {qb['rows_in']:,} -> {qb['rows_out']:,}. "
        f"Structure check: terms of 120 days or less {chk['share_term_le_120']:.2f}, median term {chk['median_term_days']:.0f}, renewal visibility {chk['renewal_visibility']:.2f} -> branch {br}.")
    assert br == branch, (br, branch)
    out = M.run_family2_confirmatory(fac2, pluto, iv, wl2, br, D_PULL)
    ls = out["link_share"]
    say(f"  Link share {ls['overall']:.2f}; spells linked {out['link_report']['linked']:,}; ended events {out['gates']['ended_events']:,}; quarters with decision points {out['gates']['quarters']}.")
    say("  | Test | Planted | Estimate (95% t interval) | Run? |")
    say("  |---|---|---|---|")
    for k, key, tab, term, pl in [("C1", "M1", None, "x", hr_), ("C2", "M3", None, "x", hr_), ("C3", "M2", None, "x_other", hr_), ("C4", "M1", None, "winter_start", 0.8 if hr_ < 1 else 1.0)]:
        if key in out and out["gates"][k]["run"]:
            t = out[key]["table"].loc[term]
            say(f"  | {k} | {pl:.2f} | {t['hr']:.3f} ({t['hr_lo']:.3f} to {t['hr_hi']:.3f}) | yes |")
            rec("8", f"{branch}_{hr_}_{k}", planted=pl, hr=t["hr"], lo=t["hr_lo"], hi=t["hr_hi"], p=t["p"])
        else:
            say(f"  | {k} | {pl:.2f} | | no: {out['gates'][k]} |")
    say(f"  Holm: {', '.join(f'{k}: p={v['p']:.4f} sig={v['significant']}' for k, v in out['holm'].items())}")
    say()
    if branch == "B" and hr_ == 0.75:
        keep_world = (iv, qa, qb)

N_REP2 = 2 if QUICK else 8
say(f"Repeated Family 2 simulations ({N_REP2} data sets per row; clean permit worlds, no quirks): bias and coverage of C1.")
say()
say("| World | Planted HR | Mean estimate | Mean log-HR error | Coverage |")
say("|---|---|---|---|---|")
f2_mc = {}
for branch, hr_ in [("B", 0.75), ("B", 1.0), ("A", 0.75), ("A", 1.0)]:
    est = []
    for rep in range(N_REP2):
        fa, _ = S.sim_facades(seed=500 + rep, planted_hr=0.75)
        wa = L.Workload(fa); pa = S.sim_pluto(fa)
        dn, lg, _ = S.sim_sheds(fa, seed=600 + rep, branch=branch, planted_hr=hr_, winter_hr=1.0, quirks=False)
        a_, _q = L.clean_dobnow(dn, ["Sidewalk Shed"]); b_, _q = L.clean_legacy(lg, ["SH"], date_format="%m/%d/%Y")
        ivx = L.combine_intervals(a_, b_)
        cfgx = M.F2Config(branch=branch, D=D_PULL)
        dpx, _p = M.prepare_family2(fa, pa, ivx, cfgx)
        h = M.hr_of(M.run_family2(dpx, wa, cfgx), "x")
        est.append(h)
    lh = np.log([h["hr"] for h in est]); cov = np.mean([h["lo"] <= hr_ <= h["hi"] for h in est])
    say(f"| {'annual' if branch == 'B' else '90-day'} terms | {hr_:.2f} | {np.exp(lh.mean()):.3f} | {lh.mean() - np.log(hr_):+.3f} | {cov:.2f} |")
    rec("8", f"mc_{branch}_{hr_}", mean_hr=float(np.exp(lh.mean())), bias_log=float(lh.mean() - np.log(hr_)), coverage=float(cov))
    f2_mc[(branch, hr_)] = lh.mean() - np.log(hr_)
say()
say("Every Family 2 variant (S1 to S20) and both placebos, annual-terms world with planted 0.75:")
say()
say("| Variant | C1 HR (95% interval) | Decision points | Ended | Dropped columns |")
say("|---|---|---|---|---|")
iv = keep_world[0]
base_cfg = M.F2Config(branch="B", D=D_PULL)
for name in ["main"] + list(M.F2_VARIANTS):
    ov = {} if name == "main" else dict(M.F2_VARIANTS[name])
    if "E" in ov:
        ov["E"] = pd.Timestamp(ov["E"])
    c = dataclasses.replace(base_cfg, **ov)
    dp, parts = M.prepare_family2(fac2, pluto, iv, c)
    r_ = M.run_family2(dp, wl2, c)
    t = r_["table"].loc["x"]
    assert np.isfinite(t["hr"]) and r_["converged"], name
    say(f"| {name} | {t['hr']:.3f} ({t['hr_lo']:.3f} to {t['hr_hi']:.3f}) | {r_['n_rows']:,} | {r_['n_events']:,} | {', '.join(r_['dropped_columns']) or 'none'} |")
    rec("8", f"variant_{name}", hr=t["hr"], lo=t["hr_lo"], hi=t["hr_hi"], rows=r_["n_rows"], events=r_["n_events"])
dp, parts = M.prepare_family2(fac2, pluto, iv, base_cfg)
for pl in ("pl1", "pl2"):
    r_ = M.run_family2(dp, wl2, dataclasses.replace(base_cfg, placebo=pl))
    t = r_["table"].loc[pl]
    say(f"| placebo {pl.upper()} | {t['hr']:.3f} ({t['hr_lo']:.3f} to {t['hr_hi']:.3f}) | {r_['n_rows']:,} | {r_['n_events']:,} | |")
r_ = M.run_family2(dp, wl2, dataclasses.replace(base_cfg, branch="A"))
say(f"| Branch A exposure on annual-term data (not a variant) | {r_['table'].loc['x', 'hr']:.3f} | {r_['n_rows']:,} | {r_['n_events']:,} | |")
say()
sp = parts["spells"]
say(f"Sanity count: spells standing on a simulated Aug 17, 2026 date: {L.standing_on(sp, '2026-08-17')} of {len(sp):,} spells (the code path for the check in 4.5).")
say()

# 9 ---- variant runners and the placebo warning --------------------------------------------------------------
say("## 9. Variant runners, robustness label and placebo warning")
tab, lab = M.run_family1_variants(fac, None, wl, names=["V1", "V2", "V3", "V6", "V9a"])
say(f"- Family 1 runner on 5 variants: all ran = {bool(tab['hr'].notna().all())}; robustness label for the main estimate = **{lab}**.")
tab2, lab2 = M.run_family2_variants(fac2, pluto, iv, wl2, "B", D_PULL, names=["S2", "S9", "S10a", "S19"])
say(f"- Family 2 runner on 4 variants: all ran = {bool(tab2['hr'].notna().all())}; robustness label = **{lab2}**.")
say(f"- Planted-data PL1 warning flag (Family 1): {planted_out.get('PL1_warning')} (False expected).")
say(f"- Residual SD of x after year and month, then after filing timing too (Family 1 planted data): {g['x_residual_sd']}")
say()

# summary ----------------------------------------------------------------------------------------------------
say("## Summary of what was and was not shown")
planted_c5 = [r for r in rows if r["section"] == "3" and r["name"] == "planted_C5"][0]
say(f"- Planted 0.75 recovered by C5 at {planted_c5['hr']:.3f} ({planted_c5['lo']:.3f} to {planted_c5['hi']:.3f}).")
mc_ok = all(abs(v[0]) < 0.06 for k, v in mc_summary.items() if k[1] == "C5 quarter" and k[0] == "no shared shock")
say(f"- Across {N_REP} repeats the mean log-HR error of C5 (quarter clustering, no shared shock) was within 0.06 of zero for both planted values: **{mc_ok}**.")
mc6 = [round(v[0], 3) for k, v in mc_summary.items() if k[1] == "C6 quarter" and k[0] == "no shared shock"]
say(f"- C6 mean log-HR errors (no shared shock): {mc6}. C6 has about a third of C5's events, so its interval is about twice as wide and its mean error needs more repeats to settle.")
say(f"- Family 2 (C1) mean log-HR errors over {N_REP2} repeats per world: " + ", ".join(f"{b} {h}: {v:+.3f}" for (b, h), v in f2_mc.items()) + ".")
nulls = [r for r in rows if r["section"] == "8" and r["name"].endswith(("_C1", "_C2", "_C3", "_C4")) and abs(r.get("planted", 0) - 1.0) < 1e-9]
bad = [r["name"] for r in nulls if (r["lo"] > 1 or r["hi"] < 1)]
say(f"- Single-run Family 2 null worlds (section 8): {len(nulls)} tests, {len(bad)} with an interval that excludes 1 ({', '.join(bad) or 'none'}). At a 5% level one in twenty is expected by chance; the repeated runs above are the better guide.")
say("- Not shown by simulation: whether real data behave like these tables. Simulated workload is much smoother than the real surges; the planted shocks are the only source of shared quarter-to-quarter noise.")
say("- Known simplifications in the simulation: no COVID pause, no change in policy, permit renewals always follow the exact hazard model, shed-link rules are never violated by real-world data quirks.")

(ROOT / "writeup").mkdir(exist_ok=True)
(ROOT / "figures").mkdir(exist_ok=True)
(ROOT / "writeup" / ("gate2-simulated-check-quick.md" if QUICK else "gate2-simulated-check.md")).write_text("\n".join(lines) + "\n")
pd.DataFrame(rows).to_csv(ROOT / "figures" / ("gate2_simcheck_results_quick.csv" if QUICK else "gate2_simcheck_results.csv"), index=False)
print("done")
