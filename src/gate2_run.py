# The Gate 2 analysis runner (job E2 from the main session, Oct 18, 2026). Family 1 (time to repair clearance, facade file
# only) is the real analysis; a Family 2 mode (shed permits) exists but refuses to run on real data until the main session
# creates the Family 2 go file. Built and tested on SIMULATED data only (src/gate2_run_tests.py).
#
# What it does, in order (PREREG.md sections 3, 7 and 9, deviations D1 to D4):
#   1. reads the facade file and the six allowlisted PLUTO columns, builds each filing's BBL, reports the PLUTO match rate as a count;
#   2. builds the frame (cycles 8 and 9, F on or before Dec 31, 2024, one filing per BIN and cycle, public owners out, X and
#      no-match indicators, carried-over flag) with the frozen gate2_link / gate2_model code;
#   3. prints the counts-only gates BEFORE any model is fit (availability, stop rules, identifiability corner cells, residual-SD
#      ratio, quarter counts) and stops with the PREREG "not testable" / "not separable" wording if the primary test fails a gate;
#   4. fits M5 (C5) and M6 (C6) with the D4 delete-one-quarter jackknife as the primary standard error (t on K - 1 df), Holm within
#      the family, placebos PL1 and PL2, variants V1 to V13 (V12 = the pre-registered quarter-clustered estimator, V13 = wild cluster
#      score bootstrap-t, B = 499, fixed seed) and the exploratory items E3, E4, E5, E7, E8, E9, E10;
#   5. writes only aggregated results (hazard ratios, intervals, counts) to writeup/gate2-family1-results.md and
#      figures/gate2_family1_*.csv. No BIN, block, lot, BBL or address is ever printed or written.
#
# Run on simulated data:  .venv/bin/python -I src/gate2_run.py --sim [--family 1|2] [--out DIR]
# Run on real data:       .venv/bin/python -I src/gate2_run.py --real --family 1   (needs data/GO_family1.txt, created by the main session)
#                         .venv/bin/python -I src/gate2_run.py --real --family 2   (needs data/GO_family2.txt)
# Drafted by Claude (AI); directed, checked and approved by Jayden Ling.
import argparse
import dataclasses
import glob
import json
import pathlib
import sys
import time

import numpy as np
import pandas as pd
import scipy.stats as st

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gate2_calibration as CAL      # ClusterFit, irls, boot_p (committed in 199086b, used for the D4 jackknife and V13)
import gate2_link as L
import gate2_model as M

ROOT = pathlib.Path(__file__).resolve().parent.parent
GO_FILES = {1: ROOT / "data" / "GO_family1.txt", 2: ROOT / "data" / "GO_family2.txt"}
AI_LINE = "Drafted with Claude (AI); directed, checked and approved by Jayden Ling. *(Approval of this file is pending until he has read it.)*"
SEED = 20261018
B_BOOT = 499
BOROUGH_DIGIT = {"Manhattan": "1", "Bronx": "2", "Brooklyn": "3", "Queens": "4", "Staten Island": "5"}
PLUTO_BORO_CODE = {"MN": "1", "BX": "2", "BK": "3", "QN": "4", "SI": "5", **BOROUGH_DIGIT}   # PLUTO uses two-letter codes; the simulated table uses names
IDENTIFIER_WORDS = ("bin", "block", "lot", "bbl", "tr6", "fid", "control_no", "address", "street", "house")
SHED_WORK_TYPES = ["Sidewalk Shed"]          # main session, Oct 18, 2026
SHED_LEGACY_SUBTYPES = ["SH"]
LEGACY_DATE_FORMAT = "%m/%d/%Y"


class GateFailure(Exception):
    """A counts-only gate failed for the primary test; the run stops with the PREREG wording."""


# ---------------------------------------------------------------------------------------------------------------
# Reading data and building the BBL
# ---------------------------------------------------------------------------------------------------------------
def make_bbl(borough, block, lot):
    """10-digit BBL string from borough name, tax block and tax lot: borough digit + block zero-padded to 5 + lot
    zero-padded to 4. None if the borough is not one of the five names or block / lot are not whole numbers."""
    b = BOROUGH_DIGIT.get(str(borough).strip()) if borough is not None else None
    try:
        bl, lo = int(str(block).strip()), int(str(lot).strip())
    except (ValueError, TypeError):
        return None
    if b is None or not (0 <= bl <= 99999) or not (0 <= lo <= 9999):
        return None
    return f"{b}{bl:05d}{lo:04d}"


def make_bbl_series(borough, block, lot):
    return pd.Series([make_bbl(a, b, c) for a, b, c in zip(borough, block, lot)], index=borough.index, dtype="object")


def pluto_consistency(pluto):
    """Counts only: PLUTO rows, rows whose own borough/block/lot fields rebuild the same BBL as the bbl field, duplicates."""
    p = pluto.copy()
    code = p["borough"].map(PLUTO_BORO_CODE)
    rebuilt = [f"{c}{int(float(b)):05d}{int(float(l)):04d}" if isinstance(c, str) and pd.notna(b) and pd.notna(l) else None
               for c, b, l in zip(code, p["block"], p["lot"])]
    own = pd.to_numeric(p["bbl"], errors="coerce").round().astype("Int64").astype("string").str.zfill(10)
    return {"pluto_rows": int(len(p)), "bbl_matches_own_fields": int((pd.Series(rebuilt, index=p.index).astype("string") == own).sum()),
            "duplicate_bbl": int(own.duplicated().sum())}


def load_real_facades():
    return pd.read_parquet(ROOT / "data" / "processed" / "facades_clean.parquet")


def load_pages(dataset, cols):
    files = sorted(glob.glob(str(ROOT / "data" / "raw" / f"{dataset}_*_page*.json")))
    return pd.concat([pd.DataFrame(json.load(open(f)), columns=cols) for f in files], ignore_index=True)


def load_real_pluto():
    return load_pages("64uk-42ks", ["borough", "block", "lot", "bbl", "ownertype", "numfloors"])


def load_real_shed_intervals():
    dn, qa = L.clean_dobnow(load_pages("rbx6-tga4", L.DOBNOW_COLS), SHED_WORK_TYPES)
    lg, qb = L.clean_legacy(load_pages("ipu4-2q9a", L.LEGACY_COLS), [], shed_permit_subtypes=SHED_LEGACY_SUBTYPES, date_format=LEGACY_DATE_FORMAT)
    return L.combine_intervals(dn, lg), {"dobnow": qa, "legacy": qb}


# ---------------------------------------------------------------------------------------------------------------
# Inference: D4 jackknife as primary
# ---------------------------------------------------------------------------------------------------------------
def jackknife_cov(ci):
    """Delete-one-quarter jackknife covariance of all coefficients (CR3 type, one-step update per deleted quarter:
    beta_(g) = beta - (A - A_g)^-1 S_g; V = (K - 1)/K * sum_g (beta_(g) - beta)(beta_(g) - beta)')."""
    dev = np.empty((ci.K, ci.k))
    for g in range(ci.K):
        dev[g] = -np.linalg.lstsq(ci.A - ci.Ag[g], ci.S[g], rcond=1e-10)[0]
    return (ci.K - 1) / ci.K * dev.T @ dev


def jackknife_table(beta, names, X, y, gidx):
    """Coefficient table with jackknife SE and t on K - 1 df. Columns: coef, se, hr, hr_lo, hr_hi, p, df."""
    ci = CAL.ClusterFit(np.asarray(X, float), np.asarray(y, float), np.asarray(beta, float), gidx)
    se = np.sqrt(np.clip(np.diag(jackknife_cov(ci)), 0, None))
    df = max(ci.K - 1, 1)
    tcrit = st.t.ppf(0.975, df)
    with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
        t = np.asarray(beta) / se
        tab = pd.DataFrame({"coef": beta, "se": se, "hr": np.exp(beta), "hr_lo": np.exp(beta - tcrit * se), "hr_hi": np.exp(beta + tcrit * se),
                            "p": 2 * st.t.sf(np.abs(t), df), "df": df}, index=names)
    return tab, ci.K


def infer(X, y, groups):
    """Fit the cloglog model (statsmodels, the model of record) and attach the primary (jackknife) intervals. A two-way
    clustering (variant V11b) cannot be jackknifed by quarter, so it keeps the statsmodels two-way cluster-robust errors."""
    res = M.fit_cloglog(X, y, groups)
    beta = np.asarray(res.params)
    groups = np.asarray(groups)
    if groups.ndim == 2:
        tab = M.coef_table(res, M.n_clusters(groups))
        method, K = "two-way cluster-robust (statsmodels), not jackknife", M.n_clusters(groups)
    else:
        gidx = pd.factorize(groups)[0]
        tab, K = jackknife_table(beta, list(X.columns), X.values, y, gidx)
        method = "delete-one-cluster jackknife"
    pre = M.coef_table(res, M.n_clusters(groups))
    return {"table": tab, "pre": pre, "beta": beta, "K": K, "rows": int(len(y)), "events": int(np.sum(y)), "method": method,
            "converged": bool(getattr(res, "converged", True)), "X": X, "y": np.asarray(y), "groups": groups}


def summarize(res, term="x"):
    t = res["table"].loc[term]
    return {"hr": float(t["hr"]), "lo": float(t["hr_lo"]), "hi": float(t["hr_hi"]), "p": float(t["p"]), "K": res["K"], "events": res["events"], "rows": res["rows"]}


def bootstrap_interval(res, term="x", seed=SEED, B=B_BOOT, grid_points=21):
    """V13: wild cluster score bootstrap-t by quarter. Returns p for H0: HR = 1 and an approximate 95% interval by inverting
    the test on a grid (linear interpolation of the p-value curve)."""
    cols = list(res["X"].columns)
    j = cols.index(term)
    Xv, y = res["X"].values.astype(float), res["y"].astype(float)
    gidx = pd.factorize(res["groups"])[0]
    beta = res["beta"]
    ci = CAL.ClusterFit(Xv, y, beta, gidx)
    se1 = ci.cr1_se(j)

    def p_at(b0):
        return CAL.boot_p(Xv, y, gidx, j, b0, beta, (beta[j] - b0) / se1, np.random.default_rng(seed), B=B)

    p0 = p_at(0.0)
    half = 3.5 * float(res["table"].loc[term, "se"])
    grid = np.linspace(beta[j] - half, beta[j] + half, grid_points)
    ps = np.array([p_at(b) for b in grid])
    mid = int(np.argmin(np.abs(grid - beta[j])))

    def cross(side):
        idx = range(mid, grid_points) if side > 0 else range(mid, -1, -1)
        prev = None
        for i in idx:
            if ps[i] < 0.05:
                if prev is None:
                    return grid[i]
                i0 = prev
                return grid[i0] + (grid[i] - grid[i0]) * (ps[i0] - 0.05) / (ps[i0] - ps[i])
            prev = i
        return np.nan

    lo_b, hi_b = cross(-1), cross(+1)
    return {"p": p0, "lo": float(np.exp(lo_b)) if np.isfinite(lo_b) else np.nan, "hi": float(np.exp(hi_b)) if np.isfinite(hi_b) else np.nan}


# ---------------------------------------------------------------------------------------------------------------
# Family 1
# ---------------------------------------------------------------------------------------------------------------
def fit_f1(facades, pluto, wl, cfg, f1=None, extra=None):
    f1 = f1 if f1 is not None else M.prepare_family1(facades, pluto, cfg)
    X, y, groups, r, notes = M.design_family1(f1, wl, cfg)
    if extra is not None:
        X = extra(X)
    res = infer(X, y, groups)
    res["dropped_columns"] = notes["dropped_columns"]
    return res


def gate_text(gates):
    """The PREREG wording for a gate that failed (sections 3.1, 7.7 and 8)."""
    out = []
    for k in ("C5", "C6"):
        g = gates.get(k, {})
        if g.get("run"):
            continue
        why = g.get("why")
        if why == "not separable from filer type" or why == "Early cells too thin":
            out.append(f"{k}: NOT SEPARABLE FROM FILER TYPE. 'Busy periods and late filers overlap too much to tell apart.' No {k} hazard ratio is reported as a finding.")
        else:
            out.append(f"{k}: NOT TESTABLE ({why}). 'Too few cases to test.' Counts only; no {k} hazard ratio is reported.")
    return out


def p_text(p):
    return "<0.0001" if p < 1e-4 else f"{p:.4f}"


def fmt_hr(h):
    return f"{h['hr']:.3f} ({h['lo']:.3f} to {h['hi']:.3f})"


def interpret(c5, c6, holm, pl1_warn, gates):
    """The 'what we would say' sentence from PREREG section 8, chosen by rule. The main session writes the actual
    interpretation; this is the pre-registered mapping, applied mechanically."""
    notes = []
    if not gates["C5"]["run"]:
        return ["C5 not run: see the gate wording above."]
    def kind(h, name):
        if h is None:
            return "not run"
        slower = h["hr"] < 1 and holm.get(name, {}).get("significant", False)
        inside = (h["lo"] >= M.HR_MEANINGFUL_LOW) and (h["hi"] <= M.HR_MEANINGFUL_HIGH)
        if h["lo"] >= M.HR_MEANINGFUL_HIGH or (h["hr"] >= M.HR_MEANINGFUL_HIGH and h["lo"] > 1):
            return "faster"
        return "slower" if slower else ("not slowed" if inside else "inconclusive")
    k5, k6 = kind(c5, "C5"), kind(c6, "C6")
    if k5 == "slower" and k6 == "slower":
        s = "Repairs clear more slowly when citywide workload is high, including at buildings that filed early. That fits a shared bottleneck. (Not: that contractors are overloaded, or which part of the pipeline it is.)"
    elif k5 == "slower" and k6 == "not slowed":
        s = "The slowdown travels with late filers, not with workload. It points to owner behavior. (Not: that deadline waves do nothing.)"
    elif k5 == "slower":
        s = "Repairs are slower when workload is high. We cannot tell whether that is a bottleneck or the owners who file last. (Not: proven bottleneck or proven owner behavior.)"
    elif k5 == "not slowed" and k6 in ("not slowed",):
        s = "No slowdown in repair clearance larger than about 20% per wave unit fits the data. The calendar creates filing waves, not repair delays."
    elif k5 == "not slowed":
        s = "No overall slowdown; the early-filer check is too small to add anything. (Not: a bottleneck claim.)"
    elif k5 == "faster":
        s = "Faster when workload is high, with an untested guess that deadlines bring attention. (Not: a policy recommendation.)"
    else:
        s = "The data cannot say. (Absence of significance is not absence of effect.)"
    notes.append(f"C5 reads '{k5}', C6 reads '{k6}': {s}")
    if pl1_warn:
        notes.append("PL1 FAILED its placebo: the workload result is exploratory, not confirmatory.")
    return notes


def run_family1(facades, pluto, out_dir=None, log=print, bootstrap=True, write=True):
    """The whole Family 1 analysis. Raises GateFailure (after writing the gates-only report) if the primary test fails a gate."""
    t0 = time.time()
    out_dir = pathlib.Path(out_dir) if out_dir else ROOT
    (out_dir / "writeup").mkdir(parents=True, exist_ok=True)
    (out_dir / "figures").mkdir(parents=True, exist_ok=True)
    md = ["# Family 1 results: time to repair clearance (facade file only)", "", AI_LINE, "",
          "Aggregated results only: hazard ratios, intervals and counts. No building identifier appears in this file or in any table written with it.", ""]
    tables = {}
    cfg = M.F1Config()
    wl = L.Workload(facades)

    # ---- 1. PLUTO and the frame ----------------------------------------------------------------------------
    pc = pluto_consistency(pluto)
    frame_all = L.build_frame(facades, f_end=cfg.f_end, pluto=pluto, include_public=True)
    n_all = len(frame_all)
    counts = dict(frame_all.attrs["counts"])
    matched = int((frame_all["no_pluto_match"] == 0).sum())
    frame_info = {"frame_before_public_exclusion": n_all, "pluto_matched": matched, "pluto_not_matched": n_all - matched,
                  "public_owner_lots": int(frame_all["public_owner"].sum()), "owner_type_X": int(frame_all["owner_X"].sum()),
                  "carried_over": int(frame_all["carried_over"].sum()), "stories_missing": int((frame_all["stories"] == "missing").sum()), **counts, **pc}
    log("FRAME / PLUTO (counts):", frame_info)
    md += ["## 1. Frame and PLUTO match (counts)", "", "| Item | Count |", "|---|---|"] + [f"| {k.replace('_', ' ')} | {v:,} |" for k, v in frame_info.items()] + [""]
    tables["frame_counts"] = pd.DataFrame({"item": list(frame_info), "count": list(frame_info.values())})

    f1 = M.prepare_family1(facades, pluto, cfg, apply_availability=False)

    # ---- 2. gates, before any model ------------------------------------------------------------------------
    gates = M.family1_gates(f1, wl)
    av = gates["availability"]
    log("GATES:", {k: v for k, v in gates.items() if k not in ("identifiability",)})
    md += ["## 2. Counts-only gates (before any model is fit)", "",
           f"- Clearing-filing availability (3.1 b): overall {av['overall']:.3f}, Early filers {av['early']:.3f}, by cycle " + ", ".join(f"cycle {c}: {v:.3f}" for c, v in av["by_cycle"].items()) + f". Cycles kept: {gates['cycles_kept']}.",
           f"- C5: {gates['C5']}", f"- C6: {gates['C6']}"]
    if "identifiability" in gates:
        ident = gates["identifiability"]
        md += [f"- Quiet cut-off (40th percentile of workload) {ident['cutoffs']['quiet_le']:.3f}; busy cut-off (70th) {ident['cutoffs']['busy_ge']:.3f}.",
               "- Corner cells (rows / events; each needs 50 and 20): " + ", ".join(f"{k} {v['rows']}/{v['events']} ({'pass' if v['pass'] else 'FAIL'})" for k, v in ident["cells"].items()),
               f"- Residual SD of workload after year and month {gates['x_residual_sd']['sd_after_year_month']:.3f}, after filing timing too {gates['x_residual_sd']['sd_after_year_month_timing']:.3f}, ratio {gates['x_residual_sd']['ratio']:.3f}."]
        tables["gate_cells"] = pd.DataFrame([{"cell": k, **{kk: vv for kk, vv in v.items()}} for k, v in ident["cells"].items()])
    md.append("")
    wording = gate_text(gates)
    if not gates["C5"]["run"]:
        md += ["## STOPPED at a gate", ""] + [f"- {w}" for w in wording] + ["", "No model was fitted."]
        if write:
            (out_dir / "writeup" / "gate2-family1-results.md").write_text("\n".join(md) + "\n")
            pd.DataFrame([{"test": k, "run": gates[k].get("run"), "why": gates[k].get("why")} for k in ("C5", "C6")]).to_csv(out_dir / "figures" / "gate2_family1_gates.csv", index=False)
        raise GateFailure(" | ".join(wording))
    if wording:
        md += ["Gate wording for tests that will not be run:", ""] + [f"- {w}" for w in wording] + [""]

    f1k = f1[f1["cycle"].isin(gates["cycles_kept"])].reset_index(drop=True)
    ncyc = f1k["cycle"].nunique()

    # ---- 3. headline: C5, C6, Holm ---------------------------------------------------------------------------
    log("fitting M5 / M6 ...")
    r5 = fit_f1(facades, pluto, wl, dataclasses.replace(cfg, model="M5"), f1=f1k)
    r6 = fit_f1(facades, pluto, wl, dataclasses.replace(cfg, model="M6"), f1=f1k) if gates["C6"]["run"] else None
    c5 = summarize(r5); c6 = summarize(r6) if r6 else None
    ps = {"C5": c5["p"]}
    if c6:
        ps["C6"] = c6["p"]
    hm = M.holm(ps)
    pl1 = fit_f1(facades, pluto, wl, dataclasses.replace(cfg, model="M5", placebo="pl1"), f1=f1k)
    pl2 = fit_f1(facades, pluto, wl, dataclasses.replace(cfg, model="M5", placebo="pl2"), f1=f1k)
    h1, h2 = summarize(pl1, "pl1"), summarize(pl2, "pl2")
    pl1_warn = bool((h1["lo"] > 1 or h1["hi"] < 1) and (h1["hr"] < M.HR_MEANINGFUL_LOW or h1["hr"] > M.HR_MEANINGFUL_HIGH))
    md += ["## 3. Confirmatory tests (primary interval: delete-one-quarter jackknife, t on K - 1 df; deviation D4)", "",
           "Hazard ratio per wave unit (400 UNSAFE filings in 90 days). Below 1 = repairs clear more slowly when the city is busy.", "",
           "| Test | Sample | Quarters K | Events | HR (95% interval) | p | Holm | Effect size (7.5) |", "|---|---|---|---|---|---|---|---|"]
    rows = []
    for name, h, desc in (("C5", c5, "all filings (M5)"), ("C6", c6, "early filers (M6)")):
        if h is None:
            md.append(f"| {name} | {desc} | | | not run | | | |"); continue
        eff = M.classify_effect(h["hr"], h["lo"], h["hi"])
        md.append(f"| {name} | {desc} | {h['K']} | {h['events']:,} | {fmt_hr(h)} | {p_text(h['p'])} | {'significant' if hm[name]['significant'] else 'not significant'} (threshold {hm[name]['threshold']:.3f}) | {eff['label']} |")
        rows.append({"test": name, **h, "holm_threshold": hm[name]["threshold"], "holm_significant": hm[name]["significant"], "effect": eff["label"]})
    tables["confirmatory"] = pd.DataFrame(rows)
    md += ["", f"Placebos (on M5): PL1 (quiet months of wave years) HR {fmt_hr(h1)}; PL2 (workload of the 90 days after F) HR {fmt_hr(h2)}. PL1 warning: **{'YES, the workload test may not be called confirmatory' if pl1_warn else 'no'}**.", ""]
    tables["placebos"] = pd.DataFrame([{"placebo": "PL1", **h1}, {"placebo": "PL2", **h2}])
    md += ["Reading by the pre-registered table (section 8), applied mechanically:", ""] + [f"- {s}" for s in interpret(c5, c6, hm, pl1_warn, gates)] + [""]

    # ---- 4. variants -------------------------------------------------------------------------------------------
    log("variants ...")
    vrows = []
    def run_variants(model, label):
        base = dataclasses.replace(cfg, model=model)
        for name, ov in M.F1_VARIANTS.items():
            try:
                r = fit_f1(facades, pluto, wl, dataclasses.replace(base, **ov))
                h = summarize(r)
                vrows.append({"model": label, "variant": name, **h, "method": r["method"]})
            except Exception as e:
                vrows.append({"model": label, "variant": name, "hr": np.nan, "error": f"{type(e).__name__}: {e}"[:100]})
        main_res = r5 if model == "M5" else r6
        pre = main_res["pre"].loc["x"]
        vrows.append({"model": label, "variant": "V12 (pre-registered quarter-clustered estimator)", "hr": float(pre["hr"]), "lo": float(pre["hr_lo"]), "hi": float(pre["hr_hi"]),
                      "p": float(pre["p"]), "K": main_res["K"], "events": main_res["events"], "rows": main_res["rows"], "method": "quarter-clustered, small-sample correction, t on K-1 df"})
        if bootstrap:
            b = bootstrap_interval(main_res)
            vrows.append({"model": label, "variant": "V13 (wild cluster score bootstrap-t, B=499, seed fixed)", "hr": float(np.exp(main_res["beta"][list(main_res["X"].columns).index('x')])),
                          "lo": b["lo"], "hi": b["hi"], "p": b["p"], "K": main_res["K"], "events": main_res["events"], "rows": main_res["rows"], "method": "interval by inverting the bootstrap test on a 21-point grid"})
    run_variants("M5", "C5")
    if r6:
        run_variants("M6", "C6")
    vt = pd.DataFrame(vrows)
    tables["variants"] = vt
    md += ["## 4. Variants (one change at a time; estimates and intervals only, no significance claims)", "",
           "| Model | Variant | HR (95% interval) | Events | Method |", "|---|---|---|---|---|"]
    for r in vt.itertuples():
        if np.isfinite(r.hr):
            md.append(f"| {r.model} | {r.variant} | {r.hr:.3f} ({r.lo:.3f} to {r.hi:.3f}) | {int(r.events):,} | {r.method} |")
        else:
            md.append(f"| {r.model} | {r.variant} | not run: {getattr(r, 'error', '')} | | |")
    md.append("")
    rob = {}
    for label, h in (("C5", c5), ("C6", c6)):
        if h is None:
            continue
        sub = vt[(vt.model == label) & ~vt.variant.str.startswith(("V12", "V13"))]
        rob[label] = M.robustness(h["hr"], bool(h["lo"] > 1 or h["hi"] < 1), list(sub["hr"]))
    md += ["Robustness label (section 8; V12 and V13 share the main point estimate so are left out of the count): " + ", ".join(f"{k}: **{v}**" for k, v in rob.items()), ""]

    # ---- 5. exploratory ------------------------------------------------------------------------------------------
    log("exploratory ...")
    md += ["## 5. Exploratory items (labelled as such: estimates and intervals only; nothing here is a test)", ""]
    ex = []
    def add(item, desc, res, terms):
        for t_ in terms:
            if t_ in res["table"].index:
                h = res["table"].loc[t_]
                ex.append({"item": item, "description": desc, "term": t_, "hr": float(h["hr"]), "lo": float(h["hr_lo"]), "hi": float(h["hr_hi"]), "K": res["K"], "events": res["events"], "rows": res["rows"]})
    x_f = wl.trailing(f1k["F"], cfg.lookback)
    quiet = f1k[x_f <= np.quantile(x_f, M.QUIET_PCT)].reset_index(drop=True)
    if quiet["event"].sum() >= 100:
        e3 = fit_f1(facades, pluto, wl, cfg, f1=quiet)
        add("E3", "filing-timing penalty among filings in the quiet workload band (H2 check)", e3, [c for c in e3["table"].index if c.startswith("timing=")])
    def e4(X):
        X = X.copy()
        for c in [c for c in X.columns if c.startswith("timing=")]:
            X[f"x*{c}"] = X["x"] * X[c]
        return X
    e4r = fit_f1(facades, pluto, wl, cfg, f1=f1k, extra=e4)
    add("E4", "workload x filing-timing interactions (x = effect for Early filers; x*timing = extra for that group)", e4r, ["x"] + [c for c in e4r["table"].index if c.startswith("x*")])
    e5 = fit_f1(facades, pluto, wl, dataclasses.replace(cfg, timing_terms=False), f1=f1k)
    add("E5", "crude workload HR without filing-timing terms, next to C5 (size of the late-filer trap)", e5, ["x"])
    fp = M.prepare_family1(facades, pluto, dataclasses.replace(cfg, include_public=True), apply_availability=False)
    fp = fp[fp["cycle"].isin(gates["cycles_kept"]) & (fp["public_owner"] == 1)].reset_index(drop=True)
    if fp["event"].sum() >= 100 and fp["quarter"].nunique() >= 12:
        e7 = fit_f1(facades, pluto, wl, dataclasses.replace(cfg, include_public=True), f1=fp)
        add("E7", "public-owned lots on their own (PLUTO OwnerType C, M, O)", e7, ["x"])
    else:
        ex.append({"item": "E7", "description": f"public-owned lots: too few to fit ({len(fp)} filings, {int(fp['event'].sum())} clearances); counts only", "term": "-", "hr": np.nan})
    e8 = fit_f1(facades, pluto, wl, dataclasses.replace(cfg, model="M6", in_window_only=True), f1=f1k) if gates["C6"]["run"] else None
    if e8 is not None:
        add("E8", "C6 on early filers that were inside their own window (leaves out those who filed before it opened)", e8, ["x"])
    for flag, lab in ((1, "carried over (prior SWARMP or UNSAFE)"), (0, "not carried over")):
        sub = f1k[f1k["carried_over"] == flag].reset_index(drop=True)
        if sub["event"].sum() >= 100 and sub["quarter"].nunique() >= 12:
            add("E9", f"filings {lab}, fitted separately", fit_f1(facades, pluto, wl, cfg, f1=sub), ["x"])
        else:
            ex.append({"item": "E9", "description": f"{lab}: too few to fit; counts only", "term": "-", "hr": np.nan})
    e10 = fit_f1(facades, pluto, wl, dataclasses.replace(cfg, split_own_other=True), f1=f1k)
    add("E10", "workload from the building's own deadline group (x_own) versus the other two groups (x_other)", e10, ["x_own", "x_other"])
    et = pd.DataFrame(ex)
    tables["exploratory"] = et
    md += ["| Item | What | Term | HR (95% interval) |", "|---|---|---|---|"]
    for r in et.itertuples():
        md.append(f"| {r.item} | {r.description} | {r.term} | " + (f"{r.hr:.3f} ({r.lo:.3f} to {r.hi:.3f})" if np.isfinite(r.hr) else "not fitted") + " |")
    md += ["", "E1, E2 and E6 of section 9.2 are not Family 1 items. E6 (the live replication after Feb 21, 2027) is a later job.", ""]

    md += ["## 6. Data and method notes", "",
           "- Facade file: NYC Open Data `xubg-57si`, DOB NOW Safety - Facades Compliance Filings, pulled Oct 17, 2026 (`data/raw/SOURCES.md` section 3); PLUTO 26v2 (`64uk-42ks`), pulled Oct 18, 2026 (section 4). Aggregated and charted by us. Owner and inspector names were dropped in the first processing step and never used.",
           f"- Cycles in the analysis: {sorted(f1k['cycle'].unique().tolist())}; filings {len(f1k):,}; quarters with filings {f1k['quarter'].nunique()}.",
           "- Primary standard errors: delete-one-quarter jackknife (deviation D4), t distribution with K - 1 degrees of freedom. The pre-registered quarter-clustered estimator is V12; the wild cluster bootstrap-t is V13.",
           "- No result here is a statement about the safety of any building, owner or inspector. Nothing is reported at building level.", "",
           f"Run time {time.time() - t0:.0f} s."]
    if write:
        (out_dir / "writeup" / "gate2-family1-results.md").write_text("\n".join(md) + "\n")
        for k, df in tables.items():
            df.to_csv(out_dir / "figures" / f"gate2_family1_{k}.csv", index=False)
    return {"c5": c5, "c6": c6, "holm": hm, "pl1": h1, "pl2": h2, "pl1_warning": pl1_warn, "gates": gates, "tables": tables, "markdown": md,
            "r5": r5, "robustness": rob}


# ---------------------------------------------------------------------------------------------------------------
# Family 2 mode (exists; must not run on real data until the main session says so)
# ---------------------------------------------------------------------------------------------------------------
def run_family2(facades, pluto, intervals, D, out_dir=None, log=print, bootstrap=True, write=True, check_branch=True):
    out_dir = pathlib.Path(out_dir) if out_dir else ROOT
    (out_dir / "writeup").mkdir(parents=True, exist_ok=True)
    (out_dir / "figures").mkdir(parents=True, exist_ok=True)
    wl = L.Workload(facades)
    chk = L.structure_check(intervals)
    inc = dict(chk); inc["renewal_visibility"] = chk["renewal_visibility_incl_overlap_NOT_USED"]
    branch = L.choose_branch(inc)
    md = ["# Family 2 results: shed permits", "", AI_LINE, "", "Aggregated results only. Pre-2026 shed permits were annual and auto-renewed, so shed removal dates are approximate (4.4); a null here is weak evidence.", "",
          f"Structure check (4.6, deviation D2 inclusive visibility): {chk} -> branch **{branch}**.", ""]
    tables = {}
    if branch not in ("A", "B"):
        md += ["Branch C or undefined: 'Shed permits before 2026 cannot time removals well enough to test this.' Nothing was run."]
        if write:
            (out_dir / "writeup" / "gate2-family2-results.md").write_text("\n".join(md) + "\n")
        raise GateFailure("Family 2 not testable on permit data (branch " + branch + ")")
    cfg = M.F2Config(branch=branch, D=pd.Timestamp(D))
    dp, parts = M.prepare_family2(facades, pluto, intervals, cfg)
    gates = M.family2_gates(dp, wl, cfg, parts["link_report"]["linked"])
    md += [f"## Gates (counts only)", "", f"- Link report: {parts['link_report']}; link share by filing timing: {L.link_share_report(parts['frame'], parts['linked'])}",
           f"- Linked spells {gates['linked_spells']:,}; ended events {gates['ended_events']:,}; quarters {gates['quarters']}.",
           "- Corner cells: " + ", ".join(f"{k} {v['rows']}/{v['events']} ({'pass' if v['pass'] else 'FAIL'})" for k, v in gates["identifiability"]["cells"].items()),
           f"- C1 {gates['C1']}; C2 {gates['C2']}; C3 {gates['C3']}; C4 {gates['C4']}", f"- Sanity count, spells standing on Aug 17, 2026 (compare 7,427 permitted sheds, Mayor's Office release Aug 20, 2026): {L.standing_on(parts['spells'], '2026-08-17'):,}", ""]
    if not (gates["C1"]["run"] or gates["C4"]["run"]):
        md += ["Stopped at a gate: " + str(gates["C1"])]
        if write:
            (out_dir / "writeup" / "gate2-family2-results.md").write_text("\n".join(md) + "\n")
        raise GateFailure("Family 2 stopped at a gate: " + str(gates["C1"]))

    def fit2(model, c=cfg, dp_=dp):
        X, y, groups, d, notes = M.design_family2(dp_, wl, dataclasses.replace(c, model=model))
        r = infer(X, y, groups); r["dropped_columns"] = notes["dropped_columns"]
        return r
    res = {}
    ps = {}
    if gates["C1"]["run"] or gates["C4"]["run"]:
        res["M1"] = fit2("M1")
        if gates["C1"]["run"]:
            ps["C1"] = res["M1"]["table"].loc["x", "p"]
        if gates["C4"]["run"]:
            ps["C4"] = res["M1"]["table"].loc["winter_start", "p"]
    if gates["C2"]["run"]:
        res["M3"] = fit2("M3"); ps["C2"] = res["M3"]["table"].loc["x", "p"]
    if gates["C3"]["run"]:
        res["M2"] = fit2("M2"); ps["C3"] = res["M2"]["table"].loc["x_other", "p"]
    hm = M.holm(ps)
    md += ["## Confirmatory tests (jackknife by quarter of expiry, t on K - 1 df; D4)", "", "| Test | HR (95% interval) | p | Holm |", "|---|---|---|---|"]
    rows = []
    for name, key, term in (("C1", "M1", "x"), ("C2", "M3", "x"), ("C3", "M2", "x_other"), ("C4", "M1", "winter_start")):
        if name in hm:
            h = summarize(res[key], term)
            md.append(f"| {name} | {fmt_hr(h)} | {p_text(h['p'])} | {'significant' if hm[name]['significant'] else 'not significant'} |")
            rows.append({"test": name, **h, "holm_significant": hm[name]["significant"]})
        else:
            md.append(f"| {name} | not run | | |")
    tables["confirmatory"] = pd.DataFrame(rows)
    log("family 2 variants ...")
    vrows = []
    for name, ov in M.F2_VARIANTS.items():
        if branch == "A" and name == "S20":
            continue
        ov = dict(ov)
        try:
            c2 = dataclasses.replace(cfg, **ov)
            d2, _p = M.prepare_family2(facades, pluto, intervals, c2)
            X, y, groups, d, notes = M.design_family2(d2, wl, c2)
            r = infer(X, y, groups)
            vrows.append({"variant": name, **summarize(r), "method": r["method"]})
        except Exception as e:
            vrows.append({"variant": name, "hr": np.nan, "error": f"{type(e).__name__}: {e}"[:100]})
    pre = res["M1"]["pre"].loc["x"] if "M1" in res else None
    if pre is not None:
        vrows.append({"variant": "S21 (pre-registered quarter-clustered estimator)", "hr": float(pre["hr"]), "lo": float(pre["hr_lo"]), "hi": float(pre["hr_hi"]), "p": float(pre["p"]), "K": res["M1"]["K"], "events": res["M1"]["events"], "rows": res["M1"]["rows"]})
        if bootstrap:
            b = bootstrap_interval(res["M1"])
            vrows.append({"variant": "S22 (wild cluster score bootstrap-t)", "hr": float(np.exp(res["M1"]["beta"][list(res["M1"]["X"].columns).index("x")])), "lo": b["lo"], "hi": b["hi"], "p": b["p"], "K": res["M1"]["K"], "events": res["M1"]["events"], "rows": res["M1"]["rows"]})
    vt = pd.DataFrame(vrows)
    tables["variants"] = vt
    md += ["", "## Variants for C1 (estimates and intervals only)", "", "| Variant | HR (95% interval) | Events |", "|---|---|---|"]
    for r in vt.itertuples():
        md.append(f"| {r.variant} | " + (f"{r.hr:.3f} ({r.lo:.3f} to {r.hi:.3f}) | {int(r.events):,} |" if np.isfinite(r.hr) else f"not run: {getattr(r, 'error', '')} | |"))
    for pl in ("pl1", "pl2"):
        X, y, groups, d, notes = M.design_family2(dp, wl, dataclasses.replace(cfg, model="M1", placebo=pl))
        r = infer(X, y, groups)
        md.append(f"\nPlacebo {pl.upper()}: HR {fmt_hr(summarize(r, pl))}")
    md += ["", "No result is a statement about the safety of any building, owner or inspector."]
    if write:
        (out_dir / "writeup" / "gate2-family2-results.md").write_text("\n".join(md) + "\n")
        for k, df in tables.items():
            df.to_csv(out_dir / "figures" / f"gate2_family2_{k}.csv", index=False)
    return {"gates": gates, "holm": hm, "tables": tables, "branch": branch, "markdown": md}


# ---------------------------------------------------------------------------------------------------------------
def to_legacy_subtype_convention(lg):
    """The simulated legacy table marks sheds as permit_type SH; the real file marks them as permit_subtype SH (under another
    permit_type). Rewrite the simulated rows to the real convention so the real cleaning strings can be tested."""
    lg = lg.copy()
    is_shed = lg["permit_type"] == "SH"
    lg.loc[is_shed, "permit_subtype"] = "SH"
    lg.loc[is_shed, "permit_type"] = "EQ"
    return lg


def check_no_identifiers(tables):
    """Raises if any output table has an identifier-like column name."""
    bad = [(k, c) for k, df in tables.items() for c in df.columns if any(w in str(c).lower() for w in IDENTIFIER_WORDS)]
    if bad:
        raise AssertionError(f"identifier-like columns in output tables: {bad}")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", type=int, default=1, choices=[1, 2])
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--sim", action="store_true")
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    if a.real == a.sim:
        raise SystemExit("choose exactly one of --real or --sim")
    if a.real:
        go = GO_FILES[a.family]
        if not go.exists():
            raise SystemExit(f"REFUSED: the real Family {a.family} analysis starts only after the main session creates {go.relative_to(ROOT)}. Nothing was read.")
        facades, pluto = load_real_facades(), load_real_pluto()
        out_dir = a.out
        if a.family == 1:
            res = run_family1(facades, pluto, out_dir)
        else:
            iv, _q = load_real_shed_intervals()
            res = run_family2(facades, pluto, iv, pd.Timestamp("2026-10-18"), out_dir)
    else:
        import gate2_sim as S
        facades, _t = S.sim_facades(seed=77, planted_hr=0.75)
        pluto = S.sim_pluto(facades)
        out_dir = a.out or str(ROOT / "figures" / "_sim_run")
        if a.family == 1:
            res = run_family1(facades, pluto, out_dir)
        else:
            dn, lg, _ = S.sim_sheds(facades, seed=78, branch="B", planted_hr=0.75, winter_hr=0.8)
            lg = to_legacy_subtype_convention(lg)
            x, _q = L.clean_dobnow(dn, ["Sidewalk Shed"]); y, _q = L.clean_legacy(lg, [], shed_permit_subtypes=["SH"], date_format=LEGACY_DATE_FORMAT)
            res = run_family2(facades, pluto, L.combine_intervals(x, y), pd.Timestamp("2026-10-17"), out_dir)
    check_no_identifiers(res["tables"])
    print("\n".join(res["markdown"][:12]))


if __name__ == "__main__":
    main()
