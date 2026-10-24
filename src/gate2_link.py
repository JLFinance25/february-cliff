# Gate 2 building blocks: the UNSAFE frame, filing timing, the city's repair workload, shed-permit cleaning, shed
# spells, the filing-to-shed link, decision points, and the outcome-free structure check.
# Implements PREREG.md (locked Oct 17, 2026, commit 0140a58) sections 4 and 6. Written and tested on SIMULATED data
# only (src/gate2_simcheck.py) before any shed-permit row or repair duration was opened. Drafted by Claude (AI);
# directed and approved by Jayden Ling.
#
# Nothing in this file looks at repair durations. The outcome for Family 1 (time to a clearing filing) lives in
# gate2_model.py. Every rule carries the PREREG section it comes from. Where the PREREG left a small detail open, the
# choice is written next to the code as "CHOICE:" so it can be reviewed and, if needed, logged as a deviation.
#
# Run with: .venv/bin/python -I (pass the path to this folder on sys.path, as gate2_model.py does).
import datetime as dt
import numpy as np
import pandas as pd

from facade_common import WINDOWS

# ---------------------------------------------------------------------------------------------------------------
# Fixed dates and constants (PREREG 3.1, 4.0, 4.1, 6.2, 6.5)
# ---------------------------------------------------------------------------------------------------------------
E_FAMILY2 = pd.Timestamp("2025-12-31")           # 4.0: Family 2 end
F_END_FAMILY1 = pd.Timestamp("2024-12-31")       # 3.1: last F for Family 1
FOLLOW_END_FAMILY1 = pd.Timestamp("2025-04-16")  # 3.1: Family 1 follow-up end
GAP_G = 30                                       # 4.1 step 3: days between permits inside one spell
LINK_WINDOW = (-90, 180)                         # 4.1 step 4: S in [F - 90, F + 180]
WAVE_UNIT = 400.0                                # 6.2: one wave unit = 400 UNSAFE filings in the look-back
LOOKBACK = 90                                    # 6.2
FRAME_CYCLES = (8, 9, 10)
PUBLIC_OWNER_TYPES = ("C", "M", "O")             # 4.1 step 1: excluded; X gets an indicator
BOROUGH_CODE = {"Manhattan": 1, "Bronx": 2, "Brooklyn": 3, "Queens": 4, "Staten Island": 5}

# 6.5 policy steps (0 before, 1 from the date). Family 1 stops before Apr 17, 2025, so that date is used only by V1.
POLICY_STEPS_MAIN = {
    "step_2019_12_17": pd.Timestamp("2019-12-17"),
    "step_2020_02_21": pd.Timestamp("2020-02-21"),
    "step_2023_07_24": pd.Timestamp("2023-07-24"),
}
POLICY_STEP_2025 = {"step_2025_04_17": pd.Timestamp("2025-04-17")}
POLICY_STEPS_S17 = {"step_2026_01_26": pd.Timestamp("2026-01-26"), "step_2026_08_20": pd.Timestamp("2026-08-20")}
COVID_START, COVID_END = pd.Timestamp("2020-03-01"), pd.Timestamp("2020-09-30")   # 6.5
DEADLINE_YEARS = sorted({WINDOWS[c][g][1].year for c in (8, 9, 10) for g in "ABC"})   # 2017-19, 2022-24, 2027-29
CYCLE_END_YEARS = (2015, 2020, 2025)             # 6.1: Feb 20 cycle ends


# ---------------------------------------------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------------------------------------------
def clean_bin(value):
    """BIN cleaned to 7 digits (4.1). Returns None if missing, not numeric or longer than 7 digits."""
    if value is None or (isinstance(value, float) and np.isnan(value)) or value is pd.NA:
        return None
    s = str(value).strip()
    if s.endswith(".0"):
        s = s[:-2]
    if not s.isdigit() or len(s) > 7:
        return None
    return s.zfill(7)


def clean_bin_series(s):
    return s.map(clean_bin)


def as_day(s):
    """Dates as pandas datetime64 normalized to midnight (no time of day)."""
    return pd.to_datetime(s, errors="coerce").dt.normalize()


def quarter_id(dates):
    d = pd.to_datetime(dates)
    return (d.dt.year * 4 + (d.dt.month - 1) // 3).astype(int)


def month_id(dates):
    d = pd.to_datetime(dates)
    return (d.dt.year * 12 + d.dt.month - 1).astype(int)


def filing_date_F(df):
    """F = filing_date; if missing, submitted_on (4.1 step 1). NaT if both are missing."""
    return as_day(df["filing_date"]).fillna(as_day(df["submitted_on"]))


# ---------------------------------------------------------------------------------------------------------------
# Step 1: the UNSAFE frame (PREREG 4.1 step 1, 3.1)
# ---------------------------------------------------------------------------------------------------------------
def deadline_of(cycle, group):
    return pd.Timestamp(WINDOWS[int(cycle)][group][1])


def window_open_of(cycle, group):
    return pd.Timestamp(WINDOWS[int(cycle)][group][0])


def timing_category(F, cycle, group):
    """Filing timing against the filing's own deadline (section 1): Early 181+ days before, Middle 29 to 180,
    Last-minute 0 to 28, Past-deadline after. Also returns whether F fell before the window opened."""
    dl = np.array([deadline_of(c, g) for c, g in zip(cycle, group)], dtype="datetime64[ns]")
    op = np.array([window_open_of(c, g) for c, g in zip(cycle, group)], dtype="datetime64[ns]")
    days_before = (dl - F.values.astype("datetime64[ns]")) / np.timedelta64(1, "D")
    cat = np.where(days_before >= 181, "Early",
          np.where(days_before >= 29, "Middle",
          np.where(days_before >= 0, "Last-minute", "Past-deadline")))
    before_window = F.values.astype("datetime64[ns]") < op
    return pd.Series(cat, index=F.index), pd.Series(before_window, index=F.index), pd.Series(days_before, index=F.index)


def stories_band(num_floors):
    """PLUTO NumFloors bands (7.1): up to 9, 10-14, 15-24, 25 and over, missing (NaN or 0 = unavailable)."""
    n = pd.to_numeric(num_floors, errors="coerce")
    out = pd.Series("missing", index=num_floors.index)
    ok = n.notna() & (n > 0)
    out[ok & (n < 10)] = "le9"             # "up to 9" (NumFloors can hold halves, so < 10 leaves no gap)
    out[ok & (n >= 10) & (n < 15)] = "10_14"
    out[ok & (n >= 15) & (n < 25)] = "15_24"
    out[ok & (n >= 25)] = "ge25"
    return out


def bbl_key(borough, block, lot):
    """Integer borough*10^9 + block*10^4 + lot from the facade file's text columns (None if not computable)."""
    b = borough.map(BOROUGH_CODE)
    bl = pd.to_numeric(block, errors="coerce")
    lo = pd.to_numeric(lot, errors="coerce")
    key = b * 10**9 + bl * 10**4 + lo
    return key.astype("Float64")


def pluto_prepare(pluto):
    """PLUTO table with columns borough/block/lot/bbl, OwnerType, NumFloors -> one row per BBL key.
    CHOICE: the key is the numeric BBL (the Socrata BBL text such as '1000010010.00000000' parses to a float). A
    duplicated BBL keeps its first row. Only the owner CATEGORY is ever used, never a name (PREREG 4.1)."""
    p = pluto.copy()
    p["bbl_key"] = pd.to_numeric(p["bbl"], errors="coerce").round().astype("Float64")
    p = p.dropna(subset=["bbl_key"]).drop_duplicates("bbl_key")
    keep = p[["bbl_key", "ownertype", "numfloors"]].rename(columns={"ownertype": "owner_type", "numfloors": "num_floors"})
    keep["owner_type"] = keep["owner_type"].astype("string").str.strip().str.upper()
    return keep


def build_frame(facades, f_end, pluto=None, statuses=("UNSAFE",), include_public=False):
    """Step 1 frame (shared by both families).

    Keep filing_type Initial, filing_status in `statuses` (main: UNSAFE only; S14 adds SWARMP), cycle in 8..10.
    F per 4.1. Drop: no F, no BIN or BIN ending 000000, no group, F after f_end. Repeats of (BIN, cycle) keep the
    earliest F (ties: smallest tr6_no). Public owners (PLUTO OwnerType C, M, O) are excluded unless include_public
    (variants S16, V9, which add a public_owner indicator). Unmatched lots stay in with no_pluto_match = 1.
    Returns one row per filing with the controls of 7.1. `frame.attrs["counts"]` records how many rows each rule dropped.
    """
    d = facades.copy()
    counts = {}
    d = d[(d["filing_type"] == "Initial") & d["filing_status"].isin(statuses) & d["cycle"].isin(FRAME_CYCLES)].copy()
    counts["initial_rows_in_status_and_cycles"] = len(d)
    d["cycle"] = d["cycle"].astype(int)
    d["F"] = filing_date_F(d)
    d["bin"] = clean_bin_series(d["bin"])
    n = len(d); d = d[d["F"].notna()]; counts["dropped_no_F"] = n - len(d)
    n = len(d); d = d[d["bin"].notna() & ~d["bin"].fillna("").str.endswith("000000")]; counts["dropped_bad_bin"] = n - len(d)
    n = len(d); d = d[d["group"].notna()]; counts["dropped_no_group"] = n - len(d)
    n = len(d); d = d[d["F"] <= pd.Timestamp(f_end)]; counts["dropped_F_after_end"] = n - len(d)
    d = d.sort_values(["bin", "cycle", "F", "tr6_no"], kind="mergesort")
    n = len(d); d = d.drop_duplicates(["bin", "cycle"], keep="first"); counts["dropped_repeats"] = n - len(d)
    counts["before_public_exclusion"] = len(d)

    d["bbl_key"] = bbl_key(d["borough"], d["block"], d["lot"])
    if pluto is not None:
        d = d.merge(pluto_prepare(pluto), on="bbl_key", how="left", indicator="_pl")
        d["no_pluto_match"] = (d["_pl"] == "left_only").astype(int)
        d = d.drop(columns="_pl")
    else:
        d["owner_type"] = pd.NA
        d["num_floors"] = np.nan
        d["no_pluto_match"] = 1
    d["owner_type"] = d["owner_type"].astype("string")
    d["public_owner"] = d["owner_type"].isin(PUBLIC_OWNER_TYPES).astype(int)
    d["owner_X"] = (d["owner_type"] == "X").fillna(False).astype(int)
    if not include_public:
        counts["public_owner_excluded"] = int(d["public_owner"].sum())
        d = d[d["public_owner"] == 0]
    d["timing"], d["before_window"], d["days_before_deadline"] = timing_category(d["F"], d["cycle"].values, d["group"].values)
    d["carried_over"] = d["prior_status"].isin(["SWARMP", "UNSAFE"]).astype(int)
    d["stories"] = stories_band(d["num_floors"])
    wall = d["exterior_wall_material_s_"].astype("string").str.upper()
    d["wall_missing"] = (wall.isna() | (wall.str.strip() == "")).astype(int)
    d["wall_masonry"] = wall.str.contains("MASONRY", na=False).astype(int)
    d["wall_terracotta"] = wall.str.contains("TERRA COTTA", na=False).astype(int)
    d["rating_swarmp"] = (d["filing_status"] == "SWARMP").astype(int)
    d["block_key"] = d["borough"].astype(str) + "-" + d["block"].astype(str)
    d["quarter"] = quarter_id(d["F"])
    d["month"] = month_id(d["F"])
    d = d.reset_index(drop=True)
    d["fid"] = np.arange(len(d))      # unique filing id used for linking (tr6_no is only a tie-break, never assumed unique)
    d.attrs["counts"] = counts
    return d


# ---------------------------------------------------------------------------------------------------------------
# The city's repair workload (PREREG 6.2) and the calendar alternative (6.4)
# ---------------------------------------------------------------------------------------------------------------
class Workload:
    """Daily UNSAFE Initial filing counts citywide (any cycle, any group), dated by F, and the trailing sums built from
    them. x on day t = (UNSAFE Initial filings dated t-lookback+1 .. t) / 400.

    CHOICE: "the 90 days ending on t" includes day t itself. Counts use every UNSAFE Initial row with a date,
    including repeats of a (BIN, cycle) pair and rows without a group (those count toward the total and toward
    'other'). x_own counts only filings in the building's own group; x_other is total minus own.
    """

    def __init__(self, facades, start="2004-01-01", end="2030-12-31"):
        d = facades[(facades["filing_type"] == "Initial") & (facades["filing_status"] == "UNSAFE")].copy()
        d["F"] = filing_date_F(d)
        d = d[d["F"].notna()]
        self.origin = pd.Timestamp(start)
        self.n_days = (pd.Timestamp(end) - self.origin).days + 1
        idx = (d["F"] - self.origin).dt.days.values
        ok = (idx >= 0) & (idx < self.n_days)
        self.total = np.bincount(idx[ok], minlength=self.n_days).astype(float)
        self.by_group = {}
        for g in "ABC":
            m = ok & (d["group"].values == g)
            self.by_group[g] = np.bincount(idx[m], minlength=self.n_days).astype(float)
        self.dates = pd.date_range(self.origin, periods=self.n_days)

    def _series(self, kind, group):
        if kind == "total":
            return self.total
        own = self.by_group[group]
        return own if kind == "own" else self.total - own

    def _csum(self, arr):
        return np.concatenate([[0.0], np.cumsum(arr)])

    def _offs(self, dates):
        return (pd.to_datetime(pd.Series(dates)).dt.normalize() - self.origin).dt.days.values

    def trailing(self, dates, lookback=LOOKBACK, kind="total", groups=None):
        """Workload on each date: sum of counts over days t-lookback+1..t, divided by 400."""
        o = self._offs(dates)
        if kind == "total":
            c = self._csum(self.total)
            return (c[o + 1] - c[np.maximum(o + 1 - lookback, 0)]) / WAVE_UNIT
        out = np.zeros(len(o))
        for g in "ABC":
            m = np.asarray(groups) == g
            if m.any():
                c = self._csum(self._series(kind, g))
                out[m] = (c[o[m] + 1] - c[np.maximum(o[m] + 1 - lookback, 0)]) / WAVE_UNIT
        return out

    def forward(self, dates, lookback=LOOKBACK):
        """PL2: workload of the `lookback` days AFTER each date (t+1 .. t+lookback)."""
        o = self._offs(dates)
        c = self._csum(self.total)
        hi = np.minimum(o + 1 + lookback, self.n_days)
        return (c[hi] - c[np.minimum(o + 1, self.n_days)]) / WAVE_UNIT

    def term_mean(self, starts_excl, ends_incl, lookback=LOOKBACK, kind="total", groups=None):
        """Branch A: daily workload averaged over the days (start, end]. CHOICE: the term's first day is the day
        after the previous decision point (or after the spell start for the first term); the last is the expiry day."""
        so, eo = self._offs(starts_excl), self._offs(ends_incl)
        out = np.zeros(len(so))
        series = {"total": [(None, self.total)]}
        if kind == "total":
            c = self._csum(self.total)
            trail = (c[1:] - c[np.maximum(np.arange(1, len(c)) - lookback, 0)]) / WAVE_UNIT   # trail[t] = workload on day t
            ct = self._csum(trail)
            n = np.maximum(eo - so, 1)
            return (ct[eo + 1] - ct[so + 1]) / n
        for g in "ABC":
            m = np.asarray(groups) == g
            if not m.any():
                continue
            c = self._csum(self._series(kind, g))
            trail = (c[1:] - c[np.maximum(np.arange(1, len(c)) - lookback, 0)]) / WAVE_UNIT
            ct = self._csum(trail)
            n = np.maximum(eo[m] - so[m], 1)
            out[m] = (ct[eo[m] + 1] - ct[so[m] + 1]) / n
        return out

    def monthly_counts(self):
        s = pd.Series(self.total, index=self.dates)
        return s.groupby([s.index.year, s.index.month]).sum()


def deadline_window_days(origin, n_days):
    """Boolean per day: inside any group's Feb 1 to Apr 30 deadline window (6.4), for deadline years of cycles 8 to 10."""
    days = pd.date_range(origin, periods=n_days)
    return np.asarray((days.month.isin([2, 3, 4])) & days.year.isin(DEADLINE_YEARS))


def cycle_end_window_days(origin, n_days):
    days = pd.date_range(origin, periods=n_days)
    return np.asarray((days.month.isin([2, 3, 4])) & days.year.isin(CYCLE_END_YEARS))


def nuisance_window_days(wl, threshold=99):
    """6.4 nuisance indicator per day: cycle-end Feb to Apr windows, plus the 3-month windows starting in any other
    month (outside the deadline-year and cycle-end Feb to Apr windows) with at least `threshold` citywide UNSAFE
    filings. Expected to give Jun to Aug 2015 and Aug to Oct 2016 plus the cycle-end windows."""
    days = wl.dates
    flag = cycle_end_window_days(wl.origin, wl.n_days).copy()
    cal = deadline_window_days(wl.origin, wl.n_days)
    mc = wl.monthly_counts()
    for (y, m), n in mc.items():
        if n < threshold:
            continue
        first = pd.Timestamp(year=int(y), month=int(m), day=1)
        month_days = (days >= first) & (days < first + pd.DateOffset(months=1))
        in_cal = month_days.any() and (cal[month_days].any() or cycle_end_window_days(wl.origin, wl.n_days)[month_days].any())
        if in_cal:
            continue
        flag |= (days >= first) & (days < first + pd.DateOffset(months=3))
    return flag


def window_share(flag_days, origin, starts_excl, ends_incl):
    """Share of days in (start, end] with the flag set (for the calendar variants S12, V8)."""
    c = np.concatenate([[0.0], np.cumsum(flag_days.astype(float))])
    so = (pd.to_datetime(pd.Series(starts_excl)).dt.normalize() - origin).dt.days.values
    eo = (pd.to_datetime(pd.Series(ends_incl)).dt.normalize() - origin).dt.days.values
    n = np.maximum(eo - so, 1)
    return (c[eo + 1] - c[so + 1]) / n


# ---------------------------------------------------------------------------------------------------------------
# Step 2: shed permits (PREREG 4.1 step 2)
# ---------------------------------------------------------------------------------------------------------------
BAD_STATUS_WORDS = ("withdrawn", "revoked", "cancelled", "canceled", "denied", "rejected", "disapproved")

DOBNOW_COLS = ["bin", "block", "lot", "work_type", "permit_status", "filing_reason", "work_permit", "sequence_number",
               "approved_date", "issued_date", "expired_date"]                       # allowlist (main session, Oct 17)
LEGACY_COLS = ["bin__", "permit_type", "permit_subtype", "permit_status", "filing_date", "issuance_date", "expiration_date"]


def date_shape_counts(series):
    """Format-only look at a text date column: digits replaced by 9, letters by a. Used to choose the one stated
    parse format 'from the format only' (4.1). Shows no real dates."""
    shape = series.dropna().astype(str).str.replace(r"\d", "9", regex=True).str.replace(r"[A-Za-z]", "a", regex=True)
    return shape.value_counts()


def code_list(dobnow=None, legacy=None, max_values=200):
    """The code-list step (4.1 step 2): distinct values of the code columns only. No counts, dates or BINs."""
    out = {}
    if dobnow is not None:
        for c in ("work_type", "permit_status", "filing_reason"):
            out[f"dobnow.{c}"] = sorted(dobnow[c].dropna().astype(str).unique())[:max_values]
    if legacy is not None:
        for c in ("permit_type", "permit_subtype", "permit_status"):
            out[f"legacy.{c}"] = sorted(legacy[c].dropna().astype(str).unique())[:max_values]
    return out


def _bad_status(s):
    low = s.astype("string").str.lower().fillna("")
    pat = "|".join(BAD_STATUS_WORDS)
    return low.str.contains(pat, regex=True)


def clean_dobnow(df, shed_work_types):
    """DOB NOW rows -> intervals (bin, start, end, source). start = issued_date (blank: approved_date); end = expired_date.
    `shed_work_types`: the exact work_type strings chosen in the code-list step (case-insensitive match).
    Returns (intervals, quality) where quality counts the rows dropped for each reason."""
    q = {"rows_in": len(df)}
    keep_types = {str(v).lower() for v in shed_work_types}
    d = df[df["work_type"].astype("string").str.lower().isin(keep_types)].copy()
    q["shed_rows"] = len(d)
    bad = _bad_status(d["permit_status"])
    q["dropped_status_never_took_effect"] = int(bad.sum())
    d = d[~bad]
    d["bin"] = clean_bin_series(d["bin"])
    d["start"] = as_day(d["issued_date"]).fillna(as_day(d["approved_date"]))
    d["end"] = as_day(d["expired_date"])
    return _finish_intervals(d, q, "dobnow")


def clean_legacy(df, shed_permit_types, shed_permit_subtypes=None, date_format="%m/%d/%Y"):
    """Legacy BIS rows -> intervals. start = issuance_date; end = expiration_date, parsed with the ONE stated format
    `date_format` (chosen from date_shape_counts only); unparseable dates are dropped and counted (4.1).
    A row is a shed if permit_type is in `shed_permit_types` (or, when given, permit_subtype is in `shed_permit_subtypes`)."""
    q = {"rows_in": len(df)}
    types = {str(v).lower() for v in shed_permit_types}
    m = df["permit_type"].astype("string").str.lower().isin(types)
    if shed_permit_subtypes:
        subs = {str(v).lower() for v in shed_permit_subtypes}
        m = m | df["permit_subtype"].astype("string").str.lower().isin(subs)
    d = df[m].copy()
    q["shed_rows"] = len(d)
    bad = _bad_status(d["permit_status"])
    q["dropped_status_never_took_effect"] = int(bad.sum())
    d = d[~bad]
    d["bin"] = clean_bin_series(d["bin__"])
    d["start"] = pd.to_datetime(d["issuance_date"], format=date_format, errors="coerce").dt.normalize()
    d["end"] = pd.to_datetime(d["expiration_date"], format=date_format, errors="coerce").dt.normalize()
    q["unparseable_start"] = int((d["start"].isna() & d["issuance_date"].notna()).sum())
    q["unparseable_end"] = int((d["end"].isna() & d["expiration_date"].notna()).sum())
    return _finish_intervals(d, q, "legacy")


def _finish_intervals(d, q, source):
    n0 = len(d)
    no_bin = d["bin"].isna()
    no_dates = d["start"].isna() | d["end"].isna()
    inverted = (~no_dates) & (d["end"] < d["start"])
    q["dropped_no_bin"] = int(no_bin.sum())
    q["dropped_no_start_or_end"] = int(no_dates.sum())
    q["dropped_end_before_start"] = int(inverted.sum())
    d = d[~no_bin & ~no_dates & ~inverted]
    before = len(d)
    d = d.drop_duplicates(["bin", "start", "end"])
    q["collapsed_duplicates"] = before - len(d)
    q["rows_out"] = len(d)
    # 4.1: report if more than 10% of shed rows are dropped for dates. The rule is not loosened.
    date_drops = q["dropped_no_start_or_end"] + q["dropped_end_before_start"]
    q["share_dropped_for_dates"] = date_drops / q["shed_rows"] if q["shed_rows"] else float("nan")
    q["date_drop_over_10pct"] = bool(q["share_dropped_for_dates"] > 0.10) if q["shed_rows"] else False
    out = d[["bin", "start", "end"]].copy()
    out["source"] = source
    return out.reset_index(drop=True), q


def combine_intervals(*parts):
    """Pool DOB NOW and legacy intervals and collapse identical (BIN, start, end) rows across the two files."""
    d = pd.concat(parts, ignore_index=True)
    return d.drop_duplicates(["bin", "start", "end"]).reset_index(drop=True)


# ---------------------------------------------------------------------------------------------------------------
# Step 3: spells (PREREG 4.1 step 3)
# ---------------------------------------------------------------------------------------------------------------
def build_spells(intervals, gap=GAP_G):
    """Chain permit intervals into spells per BIN. A permit joins the running spell if it starts no more than `gap`
    days after the running latest end (concurrent permits merge). Returns one row per spell with start (earliest start),
    end (latest end) and `expiries` (sorted distinct expiry dates of every permit in the spell)."""
    d = intervals.sort_values(["bin", "start", "end"], kind="mergesort").reset_index(drop=True)
    d["run_end"] = d.groupby("bin")["end"].cummax()
    prev_run_end = d.groupby("bin")["run_end"].shift(1)
    new_spell = prev_run_end.isna() | (d["start"] > prev_run_end + pd.Timedelta(days=gap))
    d["spell_id"] = new_spell.cumsum() - 1
    g = d.groupby("spell_id")
    spells = g.agg(bin=("bin", "first"), start=("start", "min"), end=("end", "max")).reset_index()
    ex = g["end"].apply(lambda s: np.array(sorted(s.unique()), dtype="datetime64[ns]"))
    spells["expiries"] = spells["spell_id"].map(ex)
    return spells


def standing_on(spells, date):
    """Number of spells standing on `date` (start <= date <= end). For the Aug 17, 2026 sanity check (4.5)."""
    date = pd.Timestamp(date)
    return int(((spells["start"] <= date) & (spells["end"] >= date)).sum())


# ---------------------------------------------------------------------------------------------------------------
# Step 4: link (PREREG 4.1 step 4)
# ---------------------------------------------------------------------------------------------------------------
def link_filings(frame, spells, window=LINK_WINDOW, include_standing=False):
    """Link each frame filing (F, BIN b) to the earliest spell at b with start S in [F + window[0], F + window[1]].

    Shed already standing: if b had a spell standing on F + window[0] (spell start strictly before that day and end on or
    after it) the filing is excluded (S13, include_standing=True, links it to that spell instead and marks standing=1).
    One filing per spell: if two filings compete for a spell it goes to the filing whose F is closest to S (ties: the
    later F); the loser is left unlinked (CHOICE: no re-link to a later spell, "first spell only").
    Returns (linked, report). `linked` has one row per linked filing: fid, spell_id, S, spell end, expiries, standing."""
    lo, hi = window
    f = frame[["fid", "bin", "F"]].copy()
    f["lo_day"] = f["F"] + pd.Timedelta(days=lo)
    f["hi_day"] = f["F"] + pd.Timedelta(days=hi)
    m = f.merge(spells.rename(columns={"start": "S", "end": "S_end"}), on="bin", how="inner")
    standing = m[(m["S"] < m["lo_day"]) & (m["S_end"] >= m["lo_day"])]
    stand_ids = set(standing["fid"])
    inwin = m[(m["S"] >= m["lo_day"]) & (m["S"] <= m["hi_day"])]
    if include_standing:
        st = standing.sort_values(["fid", "S"]).drop_duplicates("fid", keep="first").copy()
        st["standing"] = 1
        pick = inwin[~inwin["fid"].isin(set(st["fid"]))].sort_values(["fid", "S", "spell_id"]).drop_duplicates("fid", keep="first").copy()
        pick["standing"] = 0
        cand = pd.concat([st, pick], ignore_index=True)
    else:
        pick = inwin[~inwin["fid"].isin(stand_ids)].sort_values(["fid", "S", "spell_id"]).drop_duplicates("fid", keep="first").copy()
        pick["standing"] = 0
        cand = pick
    cand["dist"] = (cand["S"] - cand["F"]).abs().dt.days
    cand = cand.sort_values(["spell_id", "dist", "F"], ascending=[True, True, False], kind="mergesort")
    won = cand.drop_duplicates("spell_id", keep="first")
    linked = won[["fid", "spell_id", "S", "S_end", "expiries", "standing", "F"]].reset_index(drop=True)
    report = {"frame": len(frame), "excluded_standing": 0 if include_standing else len(stand_ids),
              "candidates": len(cand), "lost_competition": len(cand) - len(won), "linked": len(linked)}
    return linked, report


def link_share_report(frame, linked):
    """Share of the frame with a linked spell, overall and by filing timing (4.1 step 4 'Report')."""
    ok = frame["fid"].isin(set(linked["fid"]))
    out = {"overall": float(ok.mean()) if len(frame) else float("nan")}
    for t, g in frame.groupby("timing"):
        out[t] = float(ok[g.index].mean())
    return out


# ---------------------------------------------------------------------------------------------------------------
# Step 5: decision points (PREREG 4.1 step 5)
# ---------------------------------------------------------------------------------------------------------------
def decision_points(linked, E=E_FAMILY2, D=None, gap=GAP_G, covid="drop_expiry", window_floor_days=None):
    """One row per distinct expiry date of a linked spell. At e_1..e_{k-1} outcome 0 (renewed); at e_k outcome 1
    (ended) if e_k + gap <= D, else that row is dropped. Rows with e after E are left out. Term runs from the previous
    decision point (or spell start) to e.

    covid: 'drop_expiry' (main: drop e in Mar 1 to Sep 30, 2020), 'keep' (S8), 'drop_overlap' (S19: drop any row whose
    term overlaps that period).
    window_floor_days: for S13 (standing sheds) keep only e on or after F - 90 (pass F + lo per filing via `floor` col)."""
    D = pd.Timestamp(D) if D is not None else None
    rows = []
    for r in linked.itertuples(index=False):
        ex = [pd.Timestamp(x) for x in r.expiries]
        prev = pd.Timestamp(r.S)
        for i, e in enumerate(ex):
            last = i == len(ex) - 1
            rows.append((r.fid, r.spell_id, pd.Timestamp(r.S), prev, e, int(last), r.standing, r.F))
            prev = e
    dp = pd.DataFrame(rows, columns=["fid", "spell_id", "spell_start", "term_start", "e", "is_last", "standing", "F"])
    if dp.empty:
        return dp.assign(ended=pd.Series(dtype=int))
    if D is None:
        raise ValueError("D (shed pull date) is required")
    dp["ended"] = 0
    last_ended = dp["is_last"].eq(1) & ((dp["e"] + pd.Timedelta(days=gap)) <= D)
    dp.loc[last_ended, "ended"] = 1
    drop_unobserved_last = dp["is_last"].eq(1) & ~last_ended
    dp = dp[~drop_unobserved_last]
    dp = dp[dp["e"] <= pd.Timestamp(E)]
    if window_floor_days is not None:
        dp = dp[dp["e"] >= dp["F"] + pd.Timedelta(days=window_floor_days)]
    if covid == "drop_expiry":
        dp = dp[~((dp["e"] >= COVID_START) & (dp["e"] <= COVID_END))]
    elif covid == "drop_overlap":
        # term is the days (term_start, e]; it overlaps the pause if term_start < COVID_END and e >= COVID_START
        dp = dp[~((dp["term_start"] < COVID_END) & (dp["e"] >= COVID_START))]
    dp["term_days"] = (dp["e"] - dp["term_start"]).dt.days
    dp["spell_age_months"] = (dp["e"] - dp["spell_start"]).dt.days / 30.4375
    dp["winter_start"] = dp["spell_start"].dt.month.isin([12, 1, 2]).astype(int)
    return dp.reset_index(drop=True)


def spell_age_band(months):
    return pd.cut(months, [-np.inf, 6, 12, 24, np.inf], labels=["le6", "6_12", "12_24", "gt24"]).astype(str)


def term_band(days):
    return pd.cut(days, [-np.inf, 100, 200, 400, np.inf], labels=["le100", "101_200", "201_400", "gt400"]).astype(str)


# ---------------------------------------------------------------------------------------------------------------
# The outcome-free structure check and its branches (PREREG 4.6)
# ---------------------------------------------------------------------------------------------------------------
def structure_check(intervals, start="2015-02-21", end="2025-12-31"):
    """Right after the code-list step, before any linking. Pool = all shed rows (both files) whose start falls in
    [start, end]. Computes ONLY: the share of rows with term (end - start) of 120 days or less and the median term, and
    the renewal visibility = share of rows that start 0 to 30 days after ANOTHER row at the same BIN ends.
    No linking, no workload, no outcomes."""
    d = intervals[(intervals["start"] >= pd.Timestamp(start)) & (intervals["start"] <= pd.Timestamp(end))]
    d = d.reset_index(drop=True)
    d["i"] = np.arange(len(d))
    term = (d["end"] - d["start"]).dt.days
    m = d[["bin", "i", "start"]].merge(d[["bin", "i", "end"]], on="bin", suffixes=("", "_other"))
    m = m[m["i"] != m["i_other"]]
    gap = (m["start"] - m["end"]).dt.days
    visible = m.loc[(gap >= 0) & (gap <= 30), "i"].nunique()
    # NOT used by the branch rule: the same count if a row that starts BEFORE another row's end (an early renewal or an
    # overlapping permit) also counted, i.e. the other row started earlier and this row starts no later than its end + 30.
    start_other = m["i_other"].map(d.set_index("i")["start"])
    visible_alt = m.loc[(start_other < m["start"]) & (gap <= 30), "i"].nunique()
    return {"rows": len(d), "renewal_visibility_incl_overlap_NOT_USED": visible_alt / len(d) if len(d) else float("nan"),
            "share_term_le_120": float((term <= 120).mean()) if len(d) else float("nan"),
            "median_term_days": float(term.median()) if len(d) else float("nan"),
            "renewal_visibility": visible / len(d) if len(d) else float("nan")}


def choose_branch(check):
    """4.6 table, in the order fixed by deviation D1 (main session, Oct 17, 2026, before any shed data existed):
    C first, then A, then B. C: renewal visibility below 10%, or median term 730 days or more. A: 60% or more of rows
    have terms of 120 days or less. B: fewer than 60% short, visibility at least 10%, median term under 730 days.
    Any input those conditions do not cover (for example a missing number) returns 'UNDEFINED'."""
    short, vis, med = check["share_term_le_120"], check["renewal_visibility"], check["median_term_days"]
    if any(pd.isna(v) for v in (short, vis, med)):
        return "UNDEFINED"
    if vis < 0.10 or med >= 730:
        return "C"
    if short >= 0.60:
        return "A"
    if short < 0.60 and vis >= 0.10 and med < 730:
        return "B"
    return "UNDEFINED"
