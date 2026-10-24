# Tests for the Gate 2 runner (src/gate2_run.py). SIMULATED data only: nothing here reads the real facade, PLUTO or shed files.
# Run: .venv/bin/python -I src/gate2_run_tests.py   (prints PASS/FAIL per test, exits 1 on any failure; takes a few minutes)
# Drafted by Claude (AI); directed and approved by Jayden Ling.
import pathlib
import sys
import tempfile
import traceback

import numpy as np
import pandas as pd
import scipy.stats as st

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gate2_calibration as CAL
import gate2_link as L
import gate2_model as M
import gate2_run as R
import gate2_sim as S

T = pd.Timestamp
_CACHE = {}


def sim():
    if "sim" not in _CACHE:
        fac, _ = S.sim_facades(seed=77, planted_hr=0.75)
        _CACHE["sim"] = (fac, S.sim_pluto(fac))
    return _CACHE["sim"]


def full_run():
    """The whole Family 1 runner on the simulated tables, once (log lines captured)."""
    if "run" not in _CACHE:
        fac, pl = sim()
        log = []
        out = tempfile.mkdtemp(prefix="gate2run_")
        res = R.run_family1(fac, pl, out_dir=out, log=lambda *a: log.append(" ".join(str(x) for x in a)))
        _CACHE["run"] = (res, log, pathlib.Path(out))
    return _CACHE["run"]


# ---- BBL builder -----------------------------------------------------------------------------------------------
def test_make_bbl_names_and_padding():
    assert R.make_bbl("Manhattan", "1", "1") == "1000010001"
    assert R.make_bbl("Bronx", "12345", "678") == "2123450678"
    assert R.make_bbl("Brooklyn", "894", "52") == "3008940052"
    assert R.make_bbl("Queens", "99999", "9999") == "4999999999"
    assert R.make_bbl("Staten Island", "7", "7502") == "5000077502"
    assert R.make_bbl(" Manhattan ", " 3576 ", " 1 ") == "1035760001"          # stray spaces
    for bad in [("Narnia", "1", "1"), (None, "1", "1"), ("Bronx", "x", "1"), ("Bronx", "1", None), ("Bronx", "100000", "1"), ("Bronx", "1", "10000")]:
        assert R.make_bbl(*bad) is None, bad


def test_make_bbl_agrees_with_frozen_key():
    fac, _ = sim()
    d = fac[fac["borough"].notna()].drop_duplicates(["borough", "block", "lot"]).head(3000)
    mine = pd.to_numeric(R.make_bbl_series(d["borough"], d["block"], d["lot"]))
    frozen = L.bbl_key(d["borough"], d["block"], d["lot"]).astype(float)
    assert (mine.astype(float).values == frozen.values).all()


def test_pluto_text_bbl_joins_the_right_lot():
    d = pd.DataFrame([dict(tr6_no="A", filing_type="Initial", cycle=8, bin="1000001", filing_status="UNSAFE", filing_date=T("2016-05-01"), submitted_on=T("2016-05-01"),
                           group="A", block="1", borough="Manhattan", lot="1", prior_status=None, current_status="UNSAFE", exterior_wall_material_s_="MASONRY"),
                      dict(tr6_no="B", filing_type="Initial", cycle=8, bin="1000002", filing_status="UNSAFE", filing_date=T("2016-05-01"), submitted_on=T("2016-05-01"),
                           group="A", block="12345", borough="Bronx", lot="678", prior_status=None, current_status="UNSAFE", exterior_wall_material_s_="MASONRY")])
    pl = pd.DataFrame({"borough": ["MN", "BX"], "block": ["1", "12345"], "lot": ["1", "678"],
                       "bbl": ["1000010001.00000000", "2123450678.00000000"], "ownertype": ["C", "P"], "numfloors": ["5", "20.5"]})
    f = L.build_frame(d, f_end=T("2024-12-31"), pluto=pl, include_public=True).set_index("tr6_no")
    assert f.loc["A", "owner_type"] == "C" and f.loc["A", "no_pluto_match"] == 0 and f.loc["B", "owner_type"] == "P" and f.loc["B", "stories"] == "15_24"
    rep = R.pluto_consistency(pl)
    assert rep == {"pluto_rows": 2, "bbl_matches_own_fields": 2, "duplicate_bbl": 0}, rep
    bad = pl.copy(); bad.loc[1, "lot"] = "679"
    assert R.pluto_consistency(bad)["bbl_matches_own_fields"] == 1


# ---- inference ---------------------------------------------------------------------------------------------------
def _design(n_buildings=1800, seed=5):
    fac, _ = S.sim_facades(seed=seed, n_buildings=n_buildings, planted_hr=0.75)
    wl = L.Workload(fac)
    f1 = M.prepare_family1(fac, None, M.F1Config())
    return M.design_family1(f1, wl, M.F1Config())


def test_jackknife_matches_exact_deletion():
    X, y, groups, _r, _n = _design()
    res = R.infer(X, y, groups)
    beta = res["beta"]; j = list(X.columns).index("x")
    Xv, yv = X.values.astype(float), np.asarray(y, float)
    gidx = pd.factorize(groups)[0]
    exact = np.array([CAL.irls(Xv[gidx != g], yv[gidx != g], beta0=beta) - beta for g in np.unique(gidx)])
    K = len(exact)
    se_exact = np.sqrt((K - 1) / K * np.sum(exact**2, axis=0))
    se_mine = res["table"]["se"].values
    rel = np.abs(se_mine[j] / se_exact[j] - 1)
    med = np.median(np.abs(se_mine / se_exact - 1))
    assert rel < 0.10, f"workload SE: one-step jackknife {se_mine[j]:.4f} vs exact deletion {se_exact[j]:.4f}"       # stated tolerance: 10%
    assert med < 0.10, med
    # and equals the formula applied to the one-step deviations by hand
    ci = CAL.ClusterFit(Xv, yv, beta, gidx)
    dev = np.array([-np.linalg.lstsq(ci.A - ci.Ag[g], ci.S[g], rcond=1e-10)[0][j] for g in range(ci.K)])
    assert abs(np.sqrt((ci.K - 1) / ci.K * np.sum(dev**2)) - se_mine[j]) < 1e-9


def test_intervals_use_t_on_k_minus_1():
    X, y, groups, _r, _n = _design(n_buildings=1200, seed=6)
    res = R.infer(X, y, groups)
    K = res["K"]
    assert K == len(np.unique(groups)) and (res["table"]["df"] == K - 1).all()
    t = res["table"].loc["x"]
    tcrit = st.t.ppf(0.975, K - 1)
    assert abs(np.log(t["hr_hi"]) - (t["coef"] + tcrit * t["se"])) < 1e-12 and abs(np.log(t["hr_lo"]) - (t["coef"] - tcrit * t["se"])) < 1e-12
    assert abs(t["p"] - 2 * st.t.sf(abs(t["coef"] / t["se"]), K - 1)) < 1e-12
    # the primary (jackknife) interval is not the pre-registered one
    assert abs(res["pre"].loc["x", "se"] - t["se"]) > 1e-6


def test_holm_and_gate_wording():
    g = {"C5": {"run": False, "why": "not separable from filer type"}, "C6": {"run": False, "why": "stop rule"}}
    w = R.gate_text(g)
    assert "NOT SEPARABLE FROM FILER TYPE" in w[0] and "overlap too much" in w[0] and "NOT TESTABLE" in w[1]
    g2 = {"C5": {"run": True}, "C6": {"run": False, "why": "Early cells too thin"}}
    assert len(R.gate_text(g2)) == 1 and "C6" in R.gate_text(g2)[0]


def test_failed_gate_aborts_the_run():
    fac, _ = S.sim_facades(seed=9, n_buildings=250, planted_hr=0.75)      # about 500 frame filings: under the 1,000 stop rule
    pl = S.sim_pluto(fac)
    out = tempfile.mkdtemp(prefix="gate2gate_")
    try:
        R.run_family1(fac, pl, out_dir=out, log=lambda *a: None)
    except R.GateFailure as e:
        assert "NOT TESTABLE" in str(e) or "NOT SEPARABLE" in str(e), str(e)
    else:
        raise AssertionError("the run did not abort")
    txt = (pathlib.Path(out) / "writeup" / "gate2-family1-results.md").read_text()
    assert "STOPPED at a gate" in txt and "No model was fitted" in txt and "Confirmatory tests" not in txt
    assert not (pathlib.Path(out) / "figures" / "gate2_family1_confirmatory.csv").exists()


def test_availability_failure_aborts():
    fac, pl = sim()
    bad = fac[~((fac["filing_type"] == "Amended"))].copy()               # no clearing filings at all
    out = tempfile.mkdtemp(prefix="gate2av_")
    try:
        R.run_family1(bad, pl, out_dir=out, log=lambda *a: None)
    except R.GateFailure as e:
        assert "availability" in str(e)
    else:
        raise AssertionError("the run did not abort")


# ---- the full run on simulated data -----------------------------------------------------------------------------
def test_full_run_writes_expected_files_and_sections():
    res, log, out = full_run()
    md = (out / "writeup" / "gate2-family1-results.md").read_text()
    for part in ["## 1. Frame and PLUTO match", "## 2. Counts-only gates", "## 3. Confirmatory tests", "## 4. Variants", "## 5. Exploratory items", "Drafted with Claude (AI)"]:
        assert part in md, part
    for k in ["frame_counts", "confirmatory", "placebos", "variants", "exploratory", "gate_cells"]:
        assert (out / "figures" / f"gate2_family1_{k}.csv").exists(), k
    v = res["tables"]["variants"]
    names = set(v["variant"])
    for need in ["V1", "V2", "V3", "V4", "V5", "V6", "V7a", "V7b", "V8", "V9a", "V9b", "V10", "V11a", "V11b", "V11c"]:
        assert need in names, need
    assert any(n.startswith("V12") for n in names) and any(n.startswith("V13") for n in names)
    ex = set(res["tables"]["exploratory"]["item"])
    assert {"E3", "E4", "E5", "E8", "E9", "E10"} <= ex, ex
    # gates are printed in the log BEFORE the models are fitted
    li = [i for i, s in enumerate(log) if s.startswith("GATES")][0]
    mi = [i for i, s in enumerate(log) if s.startswith("fitting M5")][0]
    assert li < mi


def test_no_identifiers_in_outputs():
    res, log, out = full_run()
    R.check_no_identifiers(res["tables"])
    fac, pl = sim()
    bins = set(fac["bin"].astype(str))
    texts = [(out / "writeup" / "gate2-family1-results.md").read_text()] + [p.read_text() for p in (out / "figures").glob("*.csv")] + ["\n".join(log)]
    blob = "\n".join(texts)
    import re
    seven = set(re.findall(r"(?<!\d)\d{7}(?!\d)", blob))
    assert not (seven & bins), "a BIN appears in an output or log"
    ten = set(re.findall(r"(?<!\d)\d{10}(?!\d)", blob))
    assert not ten, "a 10-digit number (BBL) appears in an output or log"
    for df in res["tables"].values():
        assert not any(any(w in str(c).lower() for w in R.IDENTIFIER_WORDS) for c in df.columns)
    # the checker itself catches a bad table
    try:
        R.check_no_identifiers({"x": pd.DataFrame({"bin": [1]})})
    except AssertionError:
        pass
    else:
        raise AssertionError("check_no_identifiers missed a bin column")


def test_d4_wiring_primary_v12_v13():
    res, log, out = full_run()
    fac, pl = sim()
    r5 = res["r5"]
    prim = res["tables"]["confirmatory"].set_index("test").loc["C5"]
    jk = r5["table"].loc["x"]
    assert abs(prim["hr"] - jk["hr"]) < 1e-12 and abs(prim["lo"] - jk["hr_lo"]) < 1e-12 and abs(prim["hi"] - jk["hr_hi"]) < 1e-12 and abs(prim["p"] - jk["p"]) < 1e-12
    # V12 equals the frozen pre-registered estimator
    cfg = M.F1Config()
    wl = L.Workload(fac)
    f1 = M.prepare_family1(fac, pl, cfg)
    f1 = f1[f1["cycle"].isin(res["gates"]["cycles_kept"])].reset_index(drop=True)
    frozen = M.hr_of(M.run_family1(fac, pl, wl, cfg, f1=f1))
    v = res["tables"]["variants"]
    v12 = v[(v.model == "C5") & v.variant.str.startswith("V12")].iloc[0]
    assert abs(v12["hr"] - frozen["hr"]) < 1e-9 and abs(v12["lo"] - frozen["lo"]) < 1e-9 and abs(v12["hi"] - frozen["hi"]) < 1e-9
    assert abs(v12["lo"] - prim["lo"]) > 1e-6          # primary is not V12
    v13 = v[(v.model == "C5") & v.variant.str.startswith("V13")].iloc[0]
    assert 0 < v13["p"] <= 1 and v13["lo"] < v13["hr"] < v13["hi"]
    # Holm is applied to the jackknife p-values of the tests that ran
    assert set(res["holm"]) == {"C5", "C6"} and abs(res["holm"]["C5"]["p"] - prim["p"]) < 1e-12
    assert res["pl1_warning"] in (True, False)
    # the variants' other rows are jackknife unless two-way clustering
    assert set(v[(v.model == "C5") & v.variant.isin(["V1", "V2"])]["method"]) == {"delete-one-cluster jackknife"}
    assert v[(v.model == "C5") & (v.variant == "V11b")]["method"].iloc[0].startswith("two-way")


def test_bootstrap_is_reproducible_with_fixed_seed():
    res, log, out = full_run()
    a = R.bootstrap_interval(res["r5"], B=99, grid_points=5)
    b = R.bootstrap_interval(res["r5"], B=99, grid_points=5)
    assert a == b


def test_planted_effect_recovered_by_primary_interval():
    res, log, out = full_run()
    c5 = res["c5"]
    assert c5["lo"] < 0.75 < c5["hi"] and c5["K"] >= 24


# ---- guards ------------------------------------------------------------------------------------------------------
def test_real_runs_are_refused_without_the_go_file():
    for fam in (1, 2):
        if R.GO_FILES[fam].exists():
            print(f"  (skipped family {fam}: go file exists)")
            continue
        try:
            R.main(["--real", "--family", str(fam)])
        except SystemExit as e:
            assert "REFUSED" in str(e) and f"GO_family{fam}" in str(e), str(e)
        else:
            raise AssertionError("real run was not refused")
    try:
        R.main(["--real", "--sim"])
    except SystemExit:
        pass
    else:
        raise AssertionError("conflicting flags accepted")


def test_family2_mode_runs_on_simulated_sheds():
    fac, pl = sim()
    dn, lg, _ = S.sim_sheds(fac, seed=78, branch="B", planted_hr=0.75, winter_hr=0.8)
    lg = R.to_legacy_subtype_convention(lg)
    a, _q = L.clean_dobnow(dn, R.SHED_WORK_TYPES)
    b, _q = L.clean_legacy(lg, [], shed_permit_subtypes=R.SHED_LEGACY_SUBTYPES, date_format=R.LEGACY_DATE_FORMAT)
    out = tempfile.mkdtemp(prefix="gate2f2_")
    res = R.run_family2(fac, pl, L.combine_intervals(a, b), pd.Timestamp("2026-10-17"), out_dir=out, log=lambda *x: None)
    assert res["branch"] == "B" and set(res["holm"]) >= {"C1", "C4"}
    R.check_no_identifiers(res["tables"])
    v = res["tables"]["variants"]["variant"]
    assert any(n.startswith("S21") for n in v) and any(n.startswith("S22") for n in v) and "S19" in set(v)
    md = (pathlib.Path(out) / "writeup" / "gate2-family2-results.md").read_text()
    assert "branch **B**" in md and "Sanity count" in md


def test_family2_branch_c_aborts():
    fac, pl = sim()
    iv = pd.DataFrame({"bin": [f"{1000000 + i}" for i in range(500)], "start": T("2016-01-01"), "end": T("2016-04-01"), "source": "x"})     # no renewals at all
    out = tempfile.mkdtemp(prefix="gate2f2c_")
    try:
        R.run_family2(fac, pl, iv, pd.Timestamp("2026-10-17"), out_dir=out, log=lambda *a: None)
    except R.GateFailure as e:
        assert "not testable" in str(e)
    else:
        raise AssertionError("Branch C did not abort")


def main():
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, f in tests:
        try:
            f()
            print(f"PASS  {name}", flush=True)
        except Exception:
            failed += 1
            print(f"FAIL  {name}", flush=True)
            traceback.print_exc()
    print(f"\n{len(tests) - failed} of {len(tests)} tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
