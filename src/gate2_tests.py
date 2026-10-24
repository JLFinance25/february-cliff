# Unit tests for the Gate 2 code, on small hand-built tables (no real data). Each test checks one rule of PREREG.md
# (locked Oct 17, 2026). Run: .venv/bin/python -I src/gate2_tests.py   (prints PASS/FAIL per test, exits 1 on any failure)
# Drafted by Claude (AI); directed and approved by Jayden Ling.
import itertools
import pathlib
import sys
import traceback

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gate2_link as L
import gate2_model as M

T = pd.Timestamp
DL8A = T("2017-02-21")      # cycle 8, group A deadline


def frow(tr6, ftype, cycle, bin_, status, fdate, sub=None, group="A", block="4", borough="Manhattan", lot="1", prior=None,
         cur=None, wall="MASONRY"):
    return dict(tr6_no=tr6, filing_type=ftype, cycle=cycle, bin=bin_, filing_status=status,
                filing_date=T(fdate) if fdate else pd.NaT, submitted_on=T(sub) if sub else (T(fdate) if fdate else pd.NaT),
                group=group, block=block, borough=borough, lot=lot, prior_status=prior, current_status=cur or status,
                exterior_wall_material_s_=wall)


def facades(*rows):
    return pd.DataFrame(list(rows))


# ---- helpers -------------------------------------------------------------------------------------------------
def test_clean_bin():
    assert L.clean_bin("1019150") == "1019150" and L.clean_bin(1019150) == "1019150" and L.clean_bin("1019150.0") == "1019150"
    assert L.clean_bin("19150") == "0019150" and L.clean_bin(None) is None and L.clean_bin("abc") is None
    assert L.clean_bin("12345678") is None and L.clean_bin(float("nan")) is None


def test_filing_date_fallback():
    d = facades(frow("a", "Initial", 8, "1000001", "UNSAFE", "2016-01-05"), frow("b", "Initial", 8, "1000002", "UNSAFE", None, sub="2016-02-02"),
                frow("c", "Initial", 8, "1000003", "UNSAFE", None))
    F = L.filing_date_F(d)
    assert F[0] == T("2016-01-05") and F[1] == T("2016-02-02") and pd.isna(F[2])


def test_timing_boundaries():
    cases = {-181: "Early", -180: "Middle", -29: "Middle", -28: "Last-minute", 0: "Last-minute", 1: "Past-deadline"}
    F = pd.Series([DL8A + pd.Timedelta(days=k) for k in cases])
    cat, before, _ = L.timing_category(F, np.array([8] * len(F)), np.array(["A"] * len(F)))
    assert list(cat) == list(cases.values()), list(cat)
    # window opens Feb 21, 2015: a filing before that is flagged
    F2 = pd.Series([T("2015-02-20"), T("2015-02-21")])
    _, bw, _ = L.timing_category(F2, np.array([8, 8]), np.array(["A", "A"]))
    assert list(bw) == [True, False]


def test_stories_band():
    s = L.stories_band(pd.Series([None, 0, 5, 9, 9.5, 10, 14, 14.5, 15, 24, 24.5, 25, 80]))
    assert list(s) == ["missing", "missing", "le9", "le9", "le9", "10_14", "10_14", "10_14", "15_24", "15_24", "15_24", "ge25", "ge25"], list(s)


# ---- frame ---------------------------------------------------------------------------------------------------
def test_frame_rules():
    d = facades(
        frow("T1", "Initial", 8, "1000001", "UNSAFE", "2016-05-01"),
        frow("T0", "Initial", 8, "1000001", "UNSAFE", "2016-05-01"),               # same earliest F: smallest tr6_no wins
        frow("T2", "Initial", 8, "1000001", "UNSAFE", "2016-09-01"),               # later repeat dropped
        frow("T3", "Initial", 9, "1000001", "UNSAFE", "2022-01-05"),               # same BIN, another cycle: kept
        frow("T4", "Initial", 8, "2000000", "UNSAFE", "2016-05-01"),               # BIN ending 000000: dropped
        frow("T5", "Initial", 8, None, "UNSAFE", "2016-05-01"),                     # no BIN: dropped
        frow("T6", "Initial", 8, "1000006", "SAFE", "2016-05-01"),                  # not UNSAFE: dropped
        frow("T7", "Amended", 8, "1000007", "UNSAFE", "2016-05-01"),                # not Initial: dropped
        frow("T8", "Initial", 7, "1000008", "UNSAFE", "2012-05-01"),                # cycle 7: dropped
        frow("T9", "Initial", 8, "1000009", "UNSAFE", "2025-02-01"),                # F after the end: dropped
        frow("T10", "Initial", 8, "1000010", "UNSAFE", None),                       # no F: dropped
        frow("T11", "Initial", 8, "1000011", "UNSAFE", "2016-05-01", group=None),   # no group: dropped
        frow("T12", "Initial", 8, "1000012", "UNSAFE", None, sub="2016-06-01"),     # submitted_on fallback: kept
    )
    f = L.build_frame(d, f_end=T("2024-12-31"))
    assert sorted(f["tr6_no"]) == ["T0", "T12", "T3"], sorted(f["tr6_no"])
    assert f.attrs["counts"]["dropped_repeats"] == 2


def test_frame_pluto_exclusion():
    d = facades(*[frow(f"P{i}", "Initial", 8, f"100000{i}", "UNSAFE", "2016-05-01", block=str(i), lot="7") for i in range(1, 7)])
    # BBL = 1 * 10^9 + block * 10^4 + lot ; Manhattan
    pl = pd.DataFrame({"bbl": [f"{10**9 + i * 10**4 + 7}.00000000" for i in range(1, 6)],
                       "ownertype": ["C", "M", "O", "X", "P"], "numfloors": [5, 12, 0, 30, 18]})   # block 6 has no PLUTO row
    f = L.build_frame(d, f_end=T("2024-12-31"), pluto=pl)
    assert sorted(f["tr6_no"]) == ["P4", "P5", "P6"], sorted(f["tr6_no"])      # C, M, O removed
    r = f.set_index("tr6_no")
    assert r.loc["P4", "owner_X"] == 1 and r.loc["P5", "owner_X"] == 0 and r.loc["P6", "no_pluto_match"] == 1 and r.loc["P5", "no_pluto_match"] == 0
    assert r.loc["P4", "stories"] == "ge25" and r.loc["P5", "stories"] == "15_24" and r.loc["P6", "stories"] == "missing"
    f2 = L.build_frame(d, f_end=T("2024-12-31"), pluto=pl, include_public=True)
    assert len(f2) == 6 and f2["public_owner"].sum() == 3


def test_frame_controls():
    d = facades(frow("W1", "Initial", 8, "1000001", "UNSAFE", "2016-05-01", prior="SWARMP", wall="MASONRY; TERRA COTTA"),
                frow("W2", "Initial", 8, "1000002", "UNSAFE", "2016-05-01", prior="SAFE", wall=None))
    f = L.build_frame(d, f_end=T("2024-12-31")).set_index("tr6_no")
    assert f.loc["W1", "carried_over"] == 1 and f.loc["W2", "carried_over"] == 0
    assert f.loc["W1", "wall_masonry"] == 1 and f.loc["W1", "wall_terracotta"] == 1 and f.loc["W2", "wall_missing"] == 1


# ---- workload ------------------------------------------------------------------------------------------------
def _wl_fixture():
    rows = []
    for k, (day, grp, n) in enumerate([("2016-01-01", "A", 3), ("2016-01-31", "B", 2), ("2016-03-30", "A", 4), ("2016-04-01", "C", 5)]):
        for j in range(n):
            rows.append(frow(f"w{k}-{j}", "Initial", 8, f"{1000000 + k * 10 + j}", "UNSAFE", day, group=grp))
    rows.append(frow("safe", "Initial", 8, "1999999", "SAFE", "2016-03-30"))     # not UNSAFE: not counted
    rows.append(frow("amend", "Amended", 8, "1999998", "UNSAFE", "2016-03-30"))   # not Initial: not counted
    return facades(*rows)


def test_workload_window_and_scale():
    wl = L.Workload(_wl_fixture())
    # 90 days ending 2016-03-30 covers Jan 1 (90 days earlier is Dec 31 -> window is Jan 1 .. Mar 30 inclusive)
    x = wl.trailing(pd.Series([T("2016-03-30")]))[0]
    assert abs(x - (3 + 2 + 4) / 400) < 1e-12, x
    # one day later, Jan 1 drops out
    assert abs(wl.trailing(pd.Series([T("2016-03-31")]))[0] - (2 + 4) / 400) < 1e-12
    assert abs(wl.trailing(pd.Series([T("2016-04-01")]))[0] - (2 + 4 + 5) / 400) < 1e-12
    assert abs(wl.trailing(pd.Series([T("2015-12-31")]))[0]) < 1e-12              # before any filing
    # forward: the 90 days AFTER 2016-01-01 (Jan 2 .. Mar 31): B 2, A 4
    assert abs(wl.forward(pd.Series([T("2016-01-01")]))[0] - 6 / 400) < 1e-12
    # lookback option
    assert abs(wl.trailing(pd.Series([T("2016-04-01")]), lookback=30)[0] - (4 + 5) / 400) < 1e-12


def test_workload_own_other_and_term_mean():
    wl = L.Workload(_wl_fixture())
    d = pd.Series([T("2016-04-01")] * 3)
    g = np.array(["A", "B", "C"])
    own = wl.trailing(d, kind="own", groups=g); oth = wl.trailing(d, kind="other", groups=g)
    tot = wl.trailing(d)
    assert np.allclose(own + oth, tot)
    assert np.allclose(own, np.array([4, 2, 5]) / 400)           # A: Mar 30's 4; B: Jan 31's 2; C: Apr 1's 5
    # term mean over (Mar 29, Apr 1]: daily workload Mar 30 = 9/400, Mar 31 = 6/400... compute by brute force
    days = pd.date_range("2016-03-30", "2016-04-01")
    expected = np.mean([wl.trailing(pd.Series([t]))[0] for t in days])
    got = wl.term_mean(pd.Series([T("2016-03-29")]), pd.Series([T("2016-04-01")]))[0]
    assert abs(got - expected) < 1e-12, (got, expected)


def test_calendar_windows_and_nuisance():
    rows = []
    # 120 UNSAFE filings in Jun 2015 (>= 99) and 50 in Sep 2016 (< 99); Feb 2017 (a deadline month) has 200
    for j in range(120):
        rows.append(frow(f"j{j}", "Initial", 8, f"{1100000 + j}", "UNSAFE", "2015-06-15"))
    for j in range(50):
        rows.append(frow(f"s{j}", "Initial", 8, f"{1200000 + j}", "UNSAFE", "2016-09-15"))
    for j in range(200):
        rows.append(frow(f"f{j}", "Initial", 8, f"{1300000 + j}", "UNSAFE", "2017-02-15"))
    wl = L.Workload(facades(*rows))
    nui = L.nuisance_window_days(wl); cal = L.deadline_window_days(wl.origin, wl.n_days)
    at = lambda arr, s: bool(arr[(T(s) - wl.origin).days])
    assert at(nui, "2015-07-20") and at(nui, "2015-08-30") and not at(nui, "2015-09-05")      # Jun to Aug 2015
    assert not at(nui, "2016-10-01")                                                           # 50 < 99: no window
    assert at(nui, "2015-03-10") and at(nui, "2020-04-01") and at(nui, "2025-02-02")           # cycle-end Feb to Apr
    assert not at(nui, "2017-03-01")                                                           # the deadline month 200 >= 99, but deadline windows are not 'other'
    assert at(cal, "2017-02-01") and at(cal, "2017-04-30") and not at(cal, "2017-05-01") and not at(cal, "2016-03-01")


# ---- Family 1 outcome ----------------------------------------------------------------------------------------
def _f1_fixture():
    r = []
    # filing A: UNSAFE F=2016-06-01 cycle 8; clearing Amended SAFE on the same day (R=0)
    r += [frow("A", "Initial", 8, "1000001", "UNSAFE", "2016-06-01"), frow("A1", "Amended", 8, "1000001", "SAFE", "2016-06-01")]
    # B: clearing at day 29 (still step 1) ; C: clearing at day 30 (step 2)
    r += [frow("B", "Initial", 8, "1000002", "UNSAFE", "2016-06-01"), frow("B1", "Amended", 8, "1000002", "SWARMP", "2016-06-30")]
    r += [frow("C", "Initial", 8, "1000003", "UNSAFE", "2016-06-01"), frow("C1", "Amended", 8, "1000003", "SAFE", "2016-07-01")]
    # D: decoys only (Amended UNSAFE, Subsequent SAFE, Amended SAFE in another cycle, Amended SAFE dated before F): never clears
    r += [frow("D", "Initial", 8, "1000004", "UNSAFE", "2016-06-01"), frow("D1", "Amended", 8, "1000004", "UNSAFE", "2016-07-01"),
          frow("D2", "Subsequent", 8, "1000004", "SAFE", "2016-08-01"), frow("D3", "Amended", 9, "1000004", "SAFE", "2016-08-01"),
          frow("D4", "Amended", 8, "1000004", "SAFE", "2016-05-01")]
    # E: next-cycle Initial (UNSAFE) on 2017-01-01; clearing on 2017-01-01 counts; clearing later does not
    r += [frow("E", "Initial", 8, "1000005", "UNSAFE", "2016-06-01"), frow("E0", "Initial", 9, "1000005", "UNSAFE", "2017-01-01"),
          frow("E1", "Amended", 8, "1000005", "SAFE", "2017-01-01")]
    r += [frow("G", "Initial", 8, "1000006", "UNSAFE", "2016-06-01"), frow("G0", "Initial", 9, "1000006", "UNSAFE", "2017-01-01"),
          frow("G1", "Amended", 8, "1000006", "SAFE", "2017-01-02")]
    # H: next-cycle Initial rated SAFE (V10 counts it as a clearance); I: clearing after the follow-up end
    r += [frow("H", "Initial", 8, "1000007", "UNSAFE", "2016-06-01"), frow("H0", "Initial", 9, "1000007", "SAFE", "2017-03-01")]
    r += [frow("I", "Initial", 9, "1000008", "UNSAFE", "2024-06-01"), frow("I1", "Amended", 9, "1000008", "SAFE", "2025-04-16"),
          frow("I2", "Initial", 9, "1000009", "UNSAFE", "2024-06-01"), frow("I3", "Amended", 9, "1000009", "SAFE", "2025-04-17")]
    # J: only a Subsequent SAFE (V2); K: clearing filing with no filing_date, only submitted_on
    r += [frow("J", "Initial", 8, "1000010", "UNSAFE", "2016-06-01"), frow("J1", "Subsequent", 8, "1000010", "SAFE", "2016-09-01")]
    r += [frow("K", "Initial", 8, "1000011", "UNSAFE", "2016-06-01"), frow("K1", "Amended", 8, "1000011", "SAFE", None, sub="2016-08-01")]
    return facades(*r)


def test_family1_outcome():
    fac = _f1_fixture()
    frame = L.build_frame(fac, f_end=T("2024-12-31"))
    o = M.family1_outcome(frame, fac).set_index("tr6_no")
    assert o.loc["A", "event"] and o.loc["A", "R"] == 0
    assert o.loc["B", "event"] and o.loc["B", "R"] == 29
    assert o.loc["C", "event"] and o.loc["C", "R"] == 30
    assert not o.loc["D", "event"] and not o.loc["D", "has_clear_any_date"]
    assert o.loc["E", "event"] and o.loc["E", "R"] == (T("2017-01-01") - T("2016-06-01")).days      # on the censor date: counts
    assert not o.loc["G", "event"] and o.loc["G", "has_clear_any_date"]                               # after the next-cycle Initial
    assert o.loc["G", "c"] == (T("2017-01-01") - T("2016-06-01")).days
    assert not o.loc["H", "event"]
    assert o.loc["I", "event"] and not o.loc["I2", "event"] and o.loc["I2", "has_clear_any_date"]      # Apr 16, 2025 counts; Apr 17 does not
    assert not o.loc["J", "event"] and not o.loc["J", "has_clear_any_date"]                           # Subsequent not counted
    assert o.loc["K", "event"] and o.loc["K", "R"] == (T("2016-08-01") - T("2016-06-01")).days      # submitted_on fallback
    o2 = M.family1_outcome(frame, fac, include_subsequent=True).set_index("tr6_no")                    # V2
    assert o2.loc["J", "event"] and o2.loc["J", "R"] == (T("2016-09-01") - T("2016-06-01")).days
    o3 = M.family1_outcome(frame, fac, v10=True).set_index("tr6_no")                                   # V10
    assert o3.loc["H", "event"] and o3.loc["H", "R"] == (T("2017-03-01") - T("2016-06-01")).days
    assert o.loc["I", "c"] == (T("2025-04-16") - T("2024-06-01")).days


def test_family1_followup_end_censors():
    fac = _f1_fixture()
    frame = L.build_frame(fac, f_end=T("2024-12-31"))
    o = M.family1_outcome(frame, fac)
    bins = o.set_index("bin")
    assert bins.loc["1000008", "event"] and not bins.loc["1000009", "event"] and bins.loc["1000009", "has_clear_any_date"]


def test_person_period():
    f1 = pd.DataFrame({"event": [True, True, False, False, True], "R": [0, 59, np.nan, np.nan, 61], "c": [400, 400, 95, 29, 400]})
    pp = M.expand_person_period(f1, 30)
    cnt = pp.groupby("idx").size().to_dict()
    # R=0 -> 1 row (event in step 1); R=59 -> 2 rows; censored at day 95 -> floor(96/30)=3 full steps; censored at day 29 -> 1 full step
    # (days 0..29 observed means step 1 is complete); R=61 -> 3 rows
    assert cnt == {0: 1, 1: 2, 2: 3, 3: 1, 4: 3}, cnt
    assert pp.groupby("idx")["y"].sum().to_dict() == {0: 1, 1: 1, 2: 0, 3: 0, 4: 1}
    last = pp.groupby("idx").tail(1)
    assert list(last.loc[last["idx"].isin([0, 1, 4]), "y"]) == [1, 1, 1]
    pp14 = M.expand_person_period(f1, 14)
    assert pp14[pp14["idx"] == 1].shape[0] == 59 // 14 + 1


def test_availability():
    f1 = pd.DataFrame({"cycle": [8, 8, 8, 9, 9], "has_clear_any_date": [True, True, False, False, False], "timing": ["Early"] * 5})
    a = M.availability_by_cycle(f1)
    assert abs(a["by_cycle"][8] - 2 / 3) < 1e-12 and a["by_cycle"][9] == 0 and abs(a["overall"] - 0.4) < 1e-12


# ---- spells, link, decision points ---------------------------------------------------------------------------
def iv(*rows):
    return pd.DataFrame([dict(bin=b, start=T(s), end=T(e), source="x") for b, s, e in rows])


def test_spells_gap_rule():
    base = ("2016-01-01", "2016-04-01")
    for gap, joined in [(30, True), (31, False)]:
        nxt = T("2016-04-01") + pd.Timedelta(days=gap)
        s = L.build_spells(iv(("1", *base), ("1", str(nxt.date()), str((nxt + pd.Timedelta(days=90)).date()))), gap=30)
        assert (len(s) == 1) == joined, (gap, len(s))
    s = L.build_spells(iv(("1", "2016-01-01", "2016-12-31"), ("1", "2016-03-01", "2016-06-30"), ("2", "2016-01-01", "2016-02-01")))
    assert len(s) == 2                                                  # concurrent permits merge; other BIN is its own spell
    sp = s[s["bin"] == "1"].iloc[0]
    assert sp["start"] == T("2016-01-01") and sp["end"] == T("2016-12-31")
    assert [T(x) for x in sp["expiries"]] == [T("2016-06-30"), T("2016-12-31")]
    # gap parameter: with G = 0 a permit starting one day after the end is a new spell
    assert len(L.build_spells(iv(("1", "2016-01-01", "2016-04-01"), ("1", "2016-04-02", "2016-07-01")), gap=0)) == 2
    assert len(L.build_spells(iv(("1", "2016-01-01", "2016-04-01"), ("1", "2016-04-01", "2016-07-01")), gap=0)) == 1


def test_standing_count():
    s = L.build_spells(iv(("1", "2026-01-01", "2026-12-31"), ("2", "2026-08-18", "2026-12-31"), ("3", "2026-01-01", "2026-08-16")))
    assert L.standing_on(s, "2026-08-17") == 1


def _fr(rows):
    return pd.DataFrame([dict(fid=t, bin=b, F=T(f)) for t, b, f in rows])


def test_link_window_edges():
    F = T("2016-06-01")
    for off, ok in [(-91, False), (-90, True), (180, True), (181, False)]:
        s = L.build_spells(iv(("1", str((F + pd.Timedelta(days=off)).date()), str((F + pd.Timedelta(days=off + 400)).date()))))
        linked, rep = L.link_filings(_fr([("a", "1", "2016-06-01")]), s)
        if off == -91:
            assert len(linked) == 0 and rep["excluded_standing"] == 1      # started before F-90 and still standing: excluded
        else:
            assert (len(linked) == 1) == ok, (off, len(linked))


def test_link_standing_exclusion_and_s13():
    F = "2016-06-01"
    s = L.build_spells(iv(("1", "2015-01-01", "2016-02-01"), ("1", "2016-02-15", "2016-12-01")))     # one chained spell standing at F-90 (Mar 3)
    assert len(s) == 1
    linked, rep = L.link_filings(_fr([("a", "1", F)]), s)
    assert len(linked) == 0 and rep["excluded_standing"] == 1
    linked2, rep2 = L.link_filings(_fr([("a", "1", F)]), s, include_standing=True)                    # S13
    assert len(linked2) == 1 and linked2.iloc[0]["standing"] == 1
    # a spell that ended before F-90 does not stand: a later in-window spell links
    s2 = L.build_spells(iv(("1", "2015-01-01", "2016-01-01"), ("1", "2016-07-01", "2017-01-01")))
    linked3, rep3 = L.link_filings(_fr([("a", "1", F)]), s2)
    assert len(linked3) == 1 and linked3.iloc[0]["S"] == T("2016-07-01") and rep3["excluded_standing"] == 0


def test_link_earliest_spell_and_competition():
    s = L.build_spells(iv(("1", "2016-05-01", "2016-06-01"), ("1", "2016-09-01", "2016-12-01")))        # two spells (gap > 30)
    linked, _ = L.link_filings(_fr([("a", "1", "2016-06-01")]), s)
    assert len(linked) == 1 and linked.iloc[0]["S"] == T("2016-05-01")                                   # earliest spell only
    # two filings, one spell: the one whose F is closest to S wins; a tie goes to the later F
    s = L.build_spells(iv(("1", "2016-06-01", "2016-12-01")))
    linked, rep = L.link_filings(_fr([("far", "1", "2016-03-15"), ("near", "1", "2016-05-20")]), s)
    assert list(linked["fid"]) == ["near"] and rep["lost_competition"] == 1
    linked, _ = L.link_filings(_fr([("early", "1", "2016-05-02"), ("late", "1", "2016-06-30")]), s)      # tie: 30 days both sides
    assert list(linked["fid"]) == ["late"], list(linked["fid"])
    linked, rep = L.link_filings(_fr([("a", "9", "2016-06-01")]), s)
    assert len(linked) == 0                                                                              # other BIN: no link


def test_link_share_report():
    frame = pd.DataFrame({"fid": ["a", "b", "c"], "timing": ["Early", "Early", "Past-deadline"]})
    linked = pd.DataFrame({"fid": ["a", "c"]})
    r = L.link_share_report(frame, linked)
    assert abs(r["overall"] - 2 / 3) < 1e-12 and r["Early"] == 0.5 and r["Past-deadline"] == 1.0


def test_decision_points_example_4_2():
    # PREREG 4.2: a permit issued in January, renewed in April and July, nothing after October -> kept, kept, ended
    s = L.build_spells(iv(("1", "2016-01-10", "2016-04-10"), ("1", "2016-04-10", "2016-07-10"), ("1", "2016-07-10", "2016-10-10")))
    linked, _ = L.link_filings(_fr([("a", "1", "2016-01-15")]), s)
    dp = L.decision_points(linked, E=T("2025-12-31"), D=T("2026-10-17"))
    assert list(dp["ended"]) == [0, 0, 1] and list(dp["term_days"]) == [91, 91, 92]
    assert list(dp["term_start"]) == [T("2016-01-10"), T("2016-04-10"), T("2016-07-10")]
    # the last row is dropped (censored) if its expiry + G is after D
    dpc = L.decision_points(linked, E=T("2025-12-31"), D=T("2016-10-20"))
    assert len(dpc) == 2 and list(dpc["ended"]) == [0, 0]
    dpc2 = L.decision_points(linked, E=T("2025-12-31"), D=T("2016-11-09"))     # e_k + 30 = Nov 9: on or before D -> ended
    assert list(dpc2["ended"]) == [0, 0, 1]
    # rows with e after E are left out (and the spell's final row too, so it does not appear as 'ended')
    dpe = L.decision_points(linked, E=T("2016-08-01"), D=T("2026-10-17"))
    assert list(dpe["ended"]) == [0, 0]


def test_decision_points_covid_modes():
    s = L.build_spells(iv(("1", "2019-12-01", "2020-03-15"), ("1", "2020-03-15", "2020-08-01"), ("1", "2020-08-01", "2021-02-01")))
    linked, _ = L.link_filings(_fr([("a", "1", "2020-01-01")]), s)
    base = dict(E=T("2025-12-31"), D=T("2026-10-17"))
    assert list(L.decision_points(linked, covid="keep", **base)["e"]) == [T("2020-03-15"), T("2020-08-01"), T("2021-02-01")]
    assert list(L.decision_points(linked, covid="drop_expiry", **base)["e"]) == [T("2021-02-01")]       # Mar 15 and Aug 1 expiries fall in the pause
    # S19: any term overlapping Mar 1 to Sep 30: term 1 (Dec 1 to Mar 15) overlaps, term 2 overlaps, term 3 (Aug 1 to Feb 1) overlaps
    assert len(L.decision_points(linked, covid="drop_overlap", **base)) == 0
    # S13 floor: only expiries on or after F - 90
    flo = L.decision_points(linked, covid="keep", window_floor_days=-90, **base)
    assert len(flo) == 3                                                                               # all after Oct 3, 2019


def test_covid_boundaries():
    # expiries on Feb 29, Mar 1, Sep 30 and Oct 1, 2020: only the middle two fall in the pause (Mar 1 to Sep 30 inclusive)
    s = L.build_spells(iv(("1", "2019-06-01", "2020-02-29"), ("1", "2020-02-29", "2020-03-01"), ("1", "2020-03-01", "2020-09-30"),
                          ("1", "2020-09-30", "2020-10-01")))
    linked, _ = L.link_filings(_fr([("a", "1", "2019-07-01")]), s)
    kept = L.decision_points(linked, E=T("2025-12-31"), D=T("2026-10-17"), covid="drop_expiry")
    assert list(kept["e"]) == [T("2020-02-29"), T("2020-10-01")], list(kept["e"])


def test_decision_point_attributes():
    s = L.build_spells(iv(("1", "2016-01-10", "2016-04-10"), ("1", "2016-04-10", "2017-04-10")))
    linked, _ = L.link_filings(_fr([("a", "1", "2016-01-15")]), s)
    dp = L.decision_points(linked, E=T("2025-12-31"), D=T("2026-10-17"))
    assert list(dp["winter_start"]) == [1, 1]                       # spell started January
    assert abs(dp["spell_age_months"].iloc[1] - 15.0) < 0.2
    assert list(L.spell_age_band(pd.Series([3, 6, 6.01, 12, 24, 30]))) == ["le6", "le6", "6_12", "6_12", "12_24", "gt24"]
    assert list(L.term_band(pd.Series([90, 100, 101, 200, 201, 400, 401]))) == ["le100", "le100", "101_200", "101_200", "201_400", "201_400", "gt400"]


# ---- permit cleaning -----------------------------------------------------------------------------------------
def test_clean_dobnow():
    df = pd.DataFrame({
        "bin": ["1000001", "1000002", "1000003", "1000004", "1000005", "1000006", "1000007"],
        "work_type": ["Sidewalk Shed", "Sidewalk Shed", "Sidewalk Shed", "Sidewalk Shed", "Plumbing", "Sidewalk Shed", "sidewalk shed"],
        "permit_status": ["Permit Issued", "Permit Withdrawn", "Permit Issued", "Permit Issued", "Permit Issued", "Permit Issued", "Permit Issued"],
        "approved_date": ["2020-01-01"] * 7,
        "issued_date": ["2020-01-05", "2020-01-05", None, "2020-01-05", "2020-01-05", "2020-01-05", "2020-01-05"],
        "expired_date": ["2021-01-05", "2021-01-05", "2021-01-05", "2019-01-05", "2021-01-05", "2021-01-05", "2021-01-05"]})
    out, q = L.clean_dobnow(df, ["Sidewalk Shed"])
    # row 2 withdrawn, row 5 not a shed, row 4 end before start; row 3 has no issued_date -> falls back to approved_date (kept)
    assert sorted(out["bin"]) == ["1000001", "1000003", "1000006", "1000007"], sorted(out["bin"])
    assert out.loc[out["bin"] == "1000003", "start"].iloc[0] == T("2020-01-01")
    assert q["dropped_status_never_took_effect"] == 1 and q["dropped_end_before_start"] == 1 and q["shed_rows"] == 6
    assert abs(q["share_dropped_for_dates"] - 1 / 6) < 1e-12 and q["date_drop_over_10pct"] is True


def test_clean_legacy():
    df = pd.DataFrame({"bin__": ["1000001", "1000002", "1000003", "1000004"], "permit_type": ["SH", "SH", "EW", "SH"], "permit_subtype": ["NA"] * 4,
                       "permit_status": ["ISSUED", "ISSUED", "ISSUED", "ISSUED"],
                       "issuance_date": ["03/15/2012", "13/45/2012", "03/15/2012", "03/15/2012"],
                       "expiration_date": ["03/15/2013", "03/15/2013", "03/15/2013", None]})
    out, q = L.clean_legacy(df, ["SH"], date_format="%m/%d/%Y")
    assert list(out["bin"]) == ["1000001"] and q["unparseable_start"] == 1 and q["dropped_no_start_or_end"] == 2
    both = L.combine_intervals(out, out)
    assert len(both) == 1


def test_code_list_and_shape():
    dn = pd.DataFrame({"work_type": ["A", "B", "A", None], "permit_status": ["x", "y", "x", "z"], "filing_reason": ["r", "r", "s", "s"]})
    cl = L.code_list(dobnow=dn)
    assert cl["dobnow.work_type"] == ["A", "B"] and "dobnow.filing_reason" in cl
    assert set(L.date_shape_counts(pd.Series(["03/15/2012", "12/01/2013", "2013-01-01"])).index) == {"99/99/9999", "9999-99-99"}


# ---- structure check and branches ----------------------------------------------------------------------------
def test_structure_check():
    # row A: 100-day term; row B starts 10 days after A ends (a renewal); row C: 400-day term, alone on its BIN
    d = iv(("1", "2016-01-01", "2016-04-10"), ("1", "2016-04-20", "2016-07-30"), ("2", "2016-01-01", "2017-02-04"),
           ("3", "2014-01-01", "2014-02-01"))                                     # last row starts before Feb 21, 2015: outside the pool
    c = L.structure_check(d)
    assert c["rows"] == 3
    assert abs(c["share_term_le_120"] - 2 / 3) < 1e-12 and c["median_term_days"] == 101
    assert abs(c["renewal_visibility"] - 1 / 3) < 1e-12
    # a row does not count as its own renewal, even with a zero-length term
    assert L.structure_check(iv(("1", "2016-01-01", "2016-01-01")))["renewal_visibility"] == 0.0


def test_choose_branch_table_and_d1():
    mk = lambda s, v, m: {"share_term_le_120": s, "renewal_visibility": v, "median_term_days": m}
    assert L.choose_branch(mk(0.7, 0.5, 90)) == "A"
    assert L.choose_branch(mk(0.3, 0.5, 365)) == "B"
    assert L.choose_branch(mk(0.3, 0.05, 365)) == "C"
    assert L.choose_branch(mk(0.3, 0.5, 730)) == "C" and L.choose_branch(mk(0.3, 0.5, 729)) == "B"
    assert L.choose_branch(mk(0.7, 0.05, 90)) == "C"        # D1: short terms but visibility under 10% -> C (C wins over A)
    assert L.choose_branch(mk(0.7, 0.5, 800)) == "C"
    assert L.choose_branch(mk(0.6, 0.1, 100)) == "A" and L.choose_branch(mk(0.5999, 0.1, 729.9)) == "B"
    assert L.choose_branch(mk(float("nan"), 0.5, 90)) == "UNDEFINED"
    # no finite input falls through to UNDEFINED
    for s, v, m in itertools.product(np.linspace(0, 1, 21), np.linspace(0, 1, 21), [0, 50, 119, 120, 365, 729, 730, 900, 2000]):
        assert L.choose_branch(mk(s, v, m)) in ("A", "B", "C"), (s, v, m)


# ---- statistics ----------------------------------------------------------------------------------------------
def test_holm():
    r = M.holm({"a": 0.01, "b": 0.04, "c": 0.03})
    assert r["a"]["significant"] and not r["c"]["significant"] and not r["b"]["significant"]     # 0.01<0.0167; 0.03>0.025 -> stop
    r = M.holm({"C5": 0.004, "C6": 0.03})
    assert r["C5"]["significant"] and r["C6"]["significant"]                                        # 0.004 < 0.025, 0.03 < 0.05
    r = M.holm({"C5": 0.03, "C6": 0.04})
    assert not r["C5"]["significant"] and not r["C6"]["significant"]                                # 0.03 > 0.025: stop
    r = M.holm({"C5": 0.001, "C6": 0.06})
    assert r["C5"]["significant"] and not r["C6"]["significant"]
    assert M.holm({}) == {}


def test_classify_effect():
    assert M.classify_effect(1.0, 0.85, 1.2)["label"] == "no meaningful effect"
    assert M.classify_effect(0.7, 0.55, 0.9)["label"].startswith("meaningful") and M.classify_effect(0.7, 0.55, 0.9)["excludes_1"]
    assert M.classify_effect(0.9, 0.6, 1.3)["label"] == "inconclusive" and not M.classify_effect(0.9, 0.6, 1.3)["excludes_1"]
    assert M.classify_effect(1.3, 1.1, 1.5)["label"].startswith("meaningful")
    assert M.robustness(0.7, True, [0.7, 0.75, 0.8, 1.1]) == "robust"            # 3 of 4 point the same way
    assert M.robustness(0.7, True, [0.7, 1.1, 1.2, 0.9]) == "fragile"
    assert M.robustness(0.7, False, [0.7, 0.75]) == "fragile"


def test_identifiability_cells():
    rng = np.random.default_rng(0)
    n = 4000
    x = rng.random(n)
    timing = rng.choice(["Early", "Middle", "Last-minute", "Past-deadline"], n)
    ev = rng.random(n) < 0.5
    r = M.identifiability(x, timing, ev)
    assert r["separable_all"] and r["separable_early"]
    assert abs(r["cutoffs"]["quiet_le"] - np.quantile(x, 0.4)) < 1e-12 and abs(r["cutoffs"]["busy_ge"] - np.quantile(x, 0.7)) < 1e-12
    # Early filers never in busy periods: Early-busy fails, so C5/C6 are not separable
    timing2 = np.where(x >= np.quantile(x, 0.7), "Past-deadline", timing)
    r2 = M.identifiability(x, timing2, ev)
    assert (not r2["separable_all"]) and (not r2["separable_early"]) and not r2["cells"]["Early-busy"]["pass"]
    # a cell with plenty of rows but under 20 events fails
    ev3 = ev & ~((timing == "Early") & (x <= np.quantile(x, 0.4)))
    r3 = M.identifiability(x, timing, ev3)
    assert not r3["cells"]["Early-quiet"]["pass"] and r3["cells"]["Early-quiet"]["rows"] > 50


def test_residual_sd_ratio():
    rng = np.random.default_rng(1)
    n = 3000
    year = rng.integers(2015, 2025, n); month = rng.integers(1, 13, n)
    timing = rng.choice(["Early", "Last-minute"], n)
    x = (year - 2015) * 0.1 + (timing == "Last-minute") * 0.5 + rng.normal(0, 0.3, n)
    r = M.residual_sd_ratio(x, year, month, timing)
    assert r["ratio"] < 0.9 and r["sd_after_year_month_timing"] < r["sd_after_year_month"]


def test_drop_dependent():
    X = pd.DataFrame({"const": 1.0, "x": [1, 2, 3, 4.0], "a": [1, 0, 1, 0.0], "b": [0, 1, 0, 1.0], "c": [2, 4, 6, 8.0], "z": 0.0})
    out, dropped = M.drop_dependent(X)
    assert list(out.columns) == ["const", "x", "a"] and set(dropped) == {"b", "c", "z"}, (list(out.columns), dropped)


def test_cat_dummies():
    d = M.cat_dummies(["A", "B", "C", "B"], "g", baseline="A", levels=["A", "B", "C"])
    assert list(d.columns) == ["g=B", "g=C"] and list(d["g=B"]) == [0, 1, 0, 1]


def test_cloglog_irls_recovers_and_matches_statsmodels():
    rng = np.random.default_rng(3)
    n = 20000
    X = np.column_stack([np.ones(n), rng.normal(size=n), rng.integers(0, 2, n)])
    beta = np.array([-2.0, -0.3, 0.5])
    p = 1 - np.exp(-np.exp(X @ beta))
    y = (rng.random(n) < p).astype(float)
    g = rng.integers(0, 40, n)
    b_np, cov_np = M.cloglog_irls(X, y, groups=g)
    res = M.fit_cloglog(pd.DataFrame(X, columns=["const", "x", "z"]), y, g)
    assert np.allclose(b_np, np.asarray(res.params), atol=1e-4), (b_np, np.asarray(res.params))
    assert np.allclose(b_np, beta, atol=0.12)
    se_sm = np.asarray(res.bse)
    assert np.allclose(np.sqrt(np.diag(cov_np)), se_sm, rtol=0.02), (np.sqrt(np.diag(cov_np)), se_sm)


def test_coef_table_uses_t_with_k_minus_1():
    rng = np.random.default_rng(4)
    n = 4000
    X = pd.DataFrame({"const": 1.0, "x": rng.normal(size=n)})
    y = (rng.random(n) < 1 - np.exp(-np.exp(-2 + 0.2 * X["x"]))).astype(float)
    g = rng.integers(0, 12, n)
    res = M.fit_cloglog(X, y, g)
    tab = M.coef_table(res, 12)
    from scipy import stats
    t = tab.loc["x", "coef"] / tab.loc["x", "se"]
    assert abs(tab.loc["x", "p"] - 2 * stats.t.sf(abs(t), 11)) < 1e-12 and tab.loc["x", "df"] == 11
    assert abs(np.log(tab.loc["x", "hr_hi"]) - (tab.loc["x", "coef"] + stats.t.ppf(0.975, 11) * tab.loc["x", "se"])) < 1e-12


def test_cluster_ids_and_counts():
    d = pd.DataFrame({"quarter_cl": [1, 1, 2, 3], "month_cl": [1, 2, 3, 4], "block_key": ["a", "a", "b", "c"]})
    assert M.n_clusters(M.cluster_ids("quarter", d)) == 3 and M.n_clusters(M.cluster_ids("month", d)) == 4
    assert M.n_clusters(M.cluster_ids("block", d)) == 3 and M.n_clusters(M.cluster_ids("twoway", d)) == 3


def test_variant_registries_cover_prereg():
    assert set(M.F1_VARIANTS) >= {"V1", "V2", "V3", "V4", "V5", "V6", "V7a", "V7b", "V8", "V9a", "V9b", "V10", "V11a", "V11b", "V11c"}
    need = {f"S{i}" for i in range(1, 10)} | {"S10a", "S10b", "S10c"} | {f"S{i}" for i in range(11, 21)}
    assert set(M.F2_VARIANTS) >= need, need - set(M.F2_VARIANTS)


def test_filing_ids_unique_even_if_tr6_repeats():
    d = facades(frow("DUP", "Initial", 8, "1000001", "UNSAFE", "2016-05-01"), frow("DUP", "Initial", 8, "1000002", "UNSAFE", "2016-05-01"))
    f = L.build_frame(d, f_end=T("2024-12-31"))
    assert f["fid"].is_unique and len(f) == 2
    o = M.family1_outcome(f, d)
    assert len(o) == 2


def test_partial_step_events_are_censoring():
    # step 2 covers days 30..59. Censored at day 50: an event at day 45 is in a partly observed step -> treated as censored
    f1 = pd.DataFrame({"event": [True, True, True], "R": [45, 45, 59], "c": [50, 59, 59]})
    obs = M.observed_event(f1, 30)
    assert list(obs) == [False, True, True], list(obs)
    pp = M.expand_person_period(f1, 30)
    cnt = pp.groupby("idx").size().to_dict()
    assert cnt == {0: 1, 1: 2, 2: 2}, cnt                  # (50+1)//30 = 1 full step with no event
    assert pp.groupby("idx")["y"].sum().to_dict() == {0: 0, 1: 1, 2: 1}


def test_availability_rule_in_variants():
    fac = _f1_fixture()
    # in the fixture cycle 9 filings I and I2 clear (1 of 2 = 50%) -> kept; with an extra uncleared cycle 9 filing it is dropped
    extra = facades(frow("Z1", "Initial", 9, "1000050", "UNSAFE", "2022-01-05"), frow("Z2", "Initial", 9, "1000051", "UNSAFE", "2022-01-06"))
    fac2 = pd.concat([fac, extra], ignore_index=True)
    f1 = M.prepare_family1(fac2, None, M.F1Config())
    assert 9 not in set(f1["cycle"]) and 8 in set(f1["cycle"])
    f1b = M.prepare_family1(fac2, None, M.F1Config(), apply_availability=False)
    assert 9 in set(f1b["cycle"])


def test_design_has_month_and_year_controls():
    import gate2_sim as S
    fac, _ = S.sim_facades(seed=3, n_buildings=900, planted_hr=0.75)
    wl = L.Workload(fac)
    f1 = M.prepare_family1(fac, None, M.F1Config())
    X, y, g, r, notes = M.design_family1(f1, wl, M.F1Config())
    cols = list(X.columns)
    assert sum(c.startswith("month=") for c in cols) == 11, [c for c in cols if c.startswith("month")]
    assert sum(c.startswith("year=") for c in cols) >= 8 and sum(c.startswith("since=") for c in cols) == 6
    assert "x" in cols and "covid" in cols and "step_2019_12_17" in cols and "timing=Last-minute" in cols
    # M6 has no timing terms
    X6 = M.design_family1(f1, wl, M.F1Config(model="M6"))[0]
    assert not any(c.startswith("timing=") for c in X6.columns)
    # Family 2 design: month and year of expiry
    dn, lg, _t = S.sim_sheds(fac, seed=5, branch="B", planted_hr=0.75)
    a, _ = L.clean_dobnow(dn, ["Sidewalk Shed"]); b, _ = L.clean_legacy(lg, ["SH"])
    cfg = M.F2Config(branch="B", D=T("2026-10-17"))
    dp, _p = M.prepare_family2(fac, None, L.combine_intervals(a, b), cfg)
    X2 = M.design_family2(dp, wl, cfg)[0]
    assert sum(c.startswith("month=") for c in X2.columns) == 11 and "winter_start" in X2.columns and any(c.startswith("age=") for c in X2.columns)


def test_structure_check_alt_number_is_reported_but_separate():
    d = iv(("1", "2016-01-01", "2016-12-31"), ("1", "2016-11-20", "2017-05-01"), ("2", "2016-01-01", "2016-04-01"))
    c = L.structure_check(d)
    assert c["renewal_visibility"] == 0.0 and abs(c["renewal_visibility_incl_overlap_NOT_USED"] - 1 / 3) < 1e-12


def main():
    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    failed = 0
    for name, f in tests:
        try:
            f()
            print(f"PASS  {name}")
        except Exception:
            failed += 1
            print(f"FAIL  {name}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed} of {len(tests)} tests passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
