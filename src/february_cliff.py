# February cliff chart, cycles 7 to 10. DESCRIPTIVE AND EXPLORATORY: no hypothesis test, made before any
# pre-registration. Weekly counts, by deadline group, of four things from the DOB NOW facade-filings file:
#   filings      Initial filings, by filing date
#   inspections  inspections completed (Initial filings), by inspection-completed date
#   unsafe       Initial filings rated UNSAFE, by filing date   (rating = filing_status)
#   swarmp       Initial filings rated SWARMP, by filing date   (SWARMP = safe with a repair and maintenance program)
# Groups: last digit of the tax block (A = 4,5,6,9; B = 0,7,8; C = 1,2,3), deadlines from DOB: see facade_common.py.
# Input:  data/processed/facades_clean.parquet (made by src/process_facades.py)
# Output: figures/february_cliff_counts.png, figures/february_cliff_shares.png,
#         figures/february_cliff_weekly.csv (every plotted number), figures/february_cliff_summary.csv,
#         figures/february_cliff_data_quality.csv (rows not drawn, and why)
# Run: python3 src/february_cliff.py
import json, pathlib, sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from facade_common import WINDOWS

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIG = ROOT / "figures"
CYCLES = [7, 8, 9, 10]
GROUPS = ["A", "B", "C"]
COLORS = {"A": "#2a78d6", "B": "#eb6834", "C": "#1baf7a"}   # dataviz reference palette slots 1 to 3 (validated, light)
INK, INK2, GRID, SURFACE, NOT_YET = "#0b0b0b", "#52514e", "#e3e2de", "#fcfcfb", "#ecebe7"
MEASURES = {   # key: (row title, date column, rating filter or None)
    "filings":     ("Initial filings\n(by filing date)", "filing_date", None),
    "inspections": ("Inspections completed\n(by inspection date)", "field_inspection_completed_date", None),
    "unsafe":      ("Filings rated UNSAFE\n(by filing date)", "filing_date", "UNSAFE"),
    "swarmp":      ("Filings rated SWARMP\n(by filing date)", "filing_date", "SWARMP"),
}


def plot_range(cycle):
    # From 3 months before group A's window opens to 30 months after group C's deadline (12 months for Cycle 10, which
    # is still under way). 30 months is needed because Cycle 7 has late filings up to mid-2015 (see CYCLE7_MARKS).
    start = pd.Timestamp(WINDOWS[cycle]["A"][0]) - pd.DateOffset(months=3)
    end = pd.Timestamp(WINDOWS[cycle]["C"][1]) + pd.DateOffset(months=12 if cycle == 10 else 30)
    return start - pd.Timedelta(days=start.weekday()), end


# DOB service update, July 2015 (https://www.nyc.gov/assets/buildings/pdf/fisp_amnesty_program.pdf, read Oct 17, 2026):
# the Cycle 7 reporting period ended Feb 20, 2015, and an amnesty for owners who never filed ran to Jul 17, 2015.
CYCLE7_MARKS = [(pd.Timestamp("2015-02-20"), "cycle 7\nends"), (pd.Timestamp("2015-07-17"), "amnesty\nends")]


def main():
    meta = json.loads(next((ROOT / "data" / "raw").glob("xubg-57si_*_meta.json")).read_text())
    pulled = pd.Timestamp(meta["pulled_utc"][:10])                      # Oct 17, 2026
    df = pd.read_parquet(ROOT / "data" / "processed" / "facades_clean.parquet")
    ini = df[(df["filing_type"] == "Initial") & df["cycle"].isin(CYCLES) & df["group"].notna()].copy()
    ini["cycle"] = ini["cycle"].astype(int)

    weekly_rows, summary_rows, dq_rows = [], [], []
    for mkey, (_, dcol, rating) in MEASURES.items():
        base = ini if rating is None else ini[ini["filing_status"] == rating]
        for c in CYCLES:
            start, end = plot_range(c)
            weeks = pd.date_range(start, end, freq="7D")
            sub_c = base[base["cycle"] == c]
            dated = sub_c[sub_c[dcol].notna()]
            dq_rows.append(dict(measure=mkey, cycle=c, rows_in_scope=len(sub_c), rows_missing_date=len(sub_c) - len(dated),
                                rows_before_plot_range=int((dated[dcol] < start).sum()),
                                rows_after_plot_range=int((dated[dcol] >= end + pd.Timedelta(days=7)).sum()),
                                plot_range_start=start.date(), plot_range_end=end.date()))
            for g in GROUPS:
                opens, deadline = (pd.Timestamp(x) for x in WINDOWS[c][g])
                d = dated.loc[dated["group"] == g, dcol]
                wk = d.dt.normalize() - pd.to_timedelta(d.dt.weekday, unit="D")
                counts = wk.value_counts().reindex(weeks, fill_value=0).sort_index()   # weeks inside the plot range only
                total = len(d)
                for w, n in counts.items():
                    weekly_rows.append(dict(measure=mkey, cycle=c, group=g, week_start=w.date(), count=int(n),
                                            share_of_group_cycle_total=(n / total if total else np.nan)))
                dm_start = deadline.replace(day=1)
                dm_end = dm_start + pd.offsets.MonthBegin(1)
                n_dm = int(((d >= dm_start) & (d < dm_end)).sum())
                n_last28 = int(((d >= deadline - pd.Timedelta(days=27)) & (d <= deadline)).sum())
                n_before = int((d < opens).sum())
                n_after = int((d >= dm_end).sum())
                months = round((deadline - opens).days / 30.44)
                pk = counts.idxmax() if counts.sum() else pd.NaT
                summary_rows.append(dict(
                    measure=mkey, cycle=c, group=g, window_opens=opens.date(), deadline=deadline.date(),
                    deadline_passed=bool(deadline < pulled), window_months=months, n_total=total,
                    n_before_window_opens=n_before,
                    n_in_window_before_deadline_month=total - n_before - n_dm - n_after,
                    n_deadline_month=n_dm, n_after_deadline_month=n_after,
                    share_deadline_month=(n_dm / total if total else np.nan),
                    share_if_spread_evenly_over_window=1 / months,
                    n_last_28_days_to_deadline=n_last28,
                    share_last_28_days_to_deadline=(n_last28 / total if total else np.nan),
                    peak_week_start=(pk.date() if pd.notna(pk) else None),
                    peak_week_count=int(counts.max()) if counts.sum() else 0))
    weekly = pd.DataFrame(weekly_rows)
    summary = pd.DataFrame(summary_rows)
    dq = pd.DataFrame(dq_rows)
    FIG.mkdir(exist_ok=True)
    weekly.to_csv(FIG / "february_cliff_weekly.csv", index=False, float_format="%.6f")
    summary.to_csv(FIG / "february_cliff_summary.csv", index=False, float_format="%.4f")
    dq.to_csv(FIG / "february_cliff_data_quality.csv", index=False)

    draw(weekly, summary, "count", "february_cliff_counts.png", pulled)
    draw(weekly, summary, "share", "february_cliff_shares.png", pulled)
    report(ini, summary, dq)


def draw(weekly, summary, kind, fname, pulled):
    plt.rcParams.update({"font.family": "DejaVu Sans", "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                         "xtick.color": INK2, "ytick.color": INK2, "text.color": INK})
    fig, axes = plt.subplots(len(MEASURES), len(CYCLES), figsize=(17, 13.2), sharey="row", facecolor=SURFACE)
    col = "count" if kind == "count" else "share_of_group_cycle_total"
    for i, (mkey, (rtitle, _, _)) in enumerate(MEASURES.items()):
        rowmax = 0.0
        for j, c in enumerate(CYCLES):
            ax = axes[i, j]
            ax.set_facecolor(SURFACE)
            start, end = plot_range(c)
            ax.axvspan(max(pulled, start), end, color=NOT_YET, lw=0, zorder=0)      # not yet happened
            for g in GROUPS:
                w = weekly[(weekly["measure"] == mkey) & (weekly["cycle"] == c) & (weekly["group"] == g)]
                y = w[col] * (100 if kind == "share" else 1)
                x = pd.to_datetime(w["week_start"])
                m = x < pulled
                ax.plot(x[m], y[m], color=COLORS[g], lw=1.5, solid_joinstyle="round", zorder=3)
                rowmax = max(rowmax, float(y[m].max()))
                opens, deadline = (pd.Timestamp(v) for v in WINDOWS[c][g])
                ax.axvline(deadline, color=COLORS[g], lw=1.0, ls=(0, (2, 2)), zorder=2)
                ax.annotate(g, (deadline, 1.0), xycoords=("data", "axes fraction"), xytext=(0, 2),
                            textcoords="offset points", ha="center", va="bottom", fontsize=8, color=INK, fontweight="bold")
                near = (x >= deadline - pd.Timedelta(days=35)) & (x <= deadline + pd.Timedelta(days=35)) & m
                if deadline < pulled and near.any() and y[near].max() > 0:
                    k = y[near].idxmax()
                    txt = f"{y[k]:,.0f}" if kind == "count" else f"{y[k]:.0f}%"
                    ax.annotate(txt, (x[k], y[k]), xytext=(4, -1), textcoords="offset points", ha="left", va="center",
                                fontsize=7.5, color=INK2)
            if c == 7:
                for (dmark, lab), ypos in zip(CYCLE7_MARKS, (0.97, 0.84)):
                    ax.axvline(dmark, color=INK2, lw=0.8, ls=(0, (1, 2)), zorder=2)
                    if i == 0:
                        ax.annotate(lab, (dmark, ypos), xycoords=("data", "axes fraction"), xytext=(-3, 0),
                                    textcoords="offset points", ha="right", va="top", fontsize=7, color=INK2)
            ax.set_xlim(start, end)
            ax.xaxis.set_major_locator(mdates.YearLocator())
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
            ax.tick_params(axis="x", labelsize=8, length=3)
            ax.tick_params(axis="y", labelsize=8, length=0)
            ax.grid(axis="y", color=GRID, lw=0.6, zorder=1)
            for sp in ("top", "right", "left"):
                ax.spines[sp].set_visible(False)
            fmt = (lambda v, _: f"{v:.0f}%") if kind == "share" else (lambda v, _: f"{v:,.0f}")
            ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(fmt))
            if i == 0:
                ax.set_title(f"Cycle {c}" + ("  (still under way)" if c == 10 else ""), fontsize=11, fontweight="bold",
                             color=INK, pad=16)
            if j == 0:
                ax.set_ylabel(rtitle + ("\nper week" if kind == "count" else "\n% of group's cycle total, per week"),
                              fontsize=9, color=INK2)
        axes[i, 0].set_ylim(0, rowmax * 1.12)     # one shared scale per row, set from the real maximum
    handles = [Line2D([0], [0], color=COLORS["A"], lw=2), Line2D([0], [0], color=COLORS["B"], lw=2),
               Line2D([0], [0], color=COLORS["C"], lw=2), Line2D([0], [0], color=INK2, lw=1, ls=(0, (2, 2))),
               Patch(facecolor=NOT_YET, edgecolor="none")]
    labels = ["Group A: blocks ending 4, 5, 6, 9", "Group B: blocks ending 0, 7, 8", "Group C: blocks ending 1, 2, 3",
              "that group's deadline (Cycle 7 group B: Aug 21, 2012; all others Feb 21)",
              "not yet happened (data pulled Oct 17, 2026)"]
    fig.legend(handles, labels, loc="upper center", ncol=5, frameon=False, fontsize=8.8, bbox_to_anchor=(0.5, 0.947),
               labelcolor=INK2, columnspacing=1.6, handlelength=1.8)
    what = "weekly counts" if kind == "count" else "weekly shares of each group's own cycle total"
    fig.suptitle(f"The February cliff, cycles 7 to 10: {what} by deadline group  |  DESCRIPTIVE AND EXPLORATORY",
                 x=0.06, ha="left", y=0.985, fontsize=14, fontweight="bold", color=INK)
    cap = ("Descriptive and exploratory: no hypothesis test, made before any pre-registration. Says nothing about the safety of any building.\n"
           "Data: NYC Department of Buildings via NYC Open Data, \"DOB NOW: Safety – Facades Compliance Filings\" (xubg-57si), pulled Oct 17, 2026; "
           "Initial filings only; weeks start on Monday; aggregated and charted by us.\n"
           "Groups: last digit of the tax block, per DOB (1 RCNY §103-04(c)(4)(v)). Deadlines per DOB: Cycle 7 Tool Kit - Façades (2011), Cycle 8 TR6 instructions (2016),\n"
           "Cycle 9 sub-cycle diagram (2020), Cycle 10 service notice (Feb 24, 2025). Cycle 7 had shorter windows (B 18 months, C 12 months).\n"
           "Grey dotted lines in Cycle 7: its reporting period ended Feb 20, 2015, and DOB's amnesty for owners who never filed ended Jul 17, 2015 (DOB service update, July 2015).\n"
           "Group A covers 4 of the 10 block digits and B and C cover 3, so A is larger; the shares chart removes that. Dates outside a panel's range are not drawn\n"
           "(counts in february_cliff_data_quality.csv); every plotted number is in february_cliff_weekly.csv. Drafted with Claude (AI); not yet reviewed by Jayden Ling.")
    if kind == "share":
        cap = cap.replace("Group A covers 4 of the 10", "Cycle 10 shares are of the filings received so far; they will shrink as more arrive. Group A covers 4 of the 10")
    fig.text(0.06, 0.010, cap, ha="left", va="bottom", fontsize=8, color=INK2, linespacing=1.5)
    fig.subplots_adjust(left=0.09, right=0.985, top=0.885, bottom=0.145, hspace=0.34, wspace=0.07)
    fig.savefig(FIG / fname, dpi=130, facecolor=SURFACE)
    plt.close(fig)
    print("wrote", FIG / fname)


def report(ini, summary, dq):
    pd.set_option("display.width", 250, "display.max_columns", 30)
    print("\n=== Initial filings per group per cycle (rows with a filing date) ===")
    f = summary[summary.measure == "filings"].pivot(index="cycle", columns="group", values="n_total")
    f["A/B"] = (f["A"] / f["B"]).round(2); f["A/C"] = (f["A"] / f["C"]).round(2)
    print(f.to_string())
    for m in ["filings", "inspections", "unsafe", "swarmp"]:
        s = summary[summary.measure == m]
        print(f"\n=== {m}: share of group's cycle total in the deadline month (deadline passed only) ===")
        t = s[s.deadline_passed].pivot(index="cycle", columns="group", values="share_deadline_month").mul(100).round(1)
        n = s[s.deadline_passed].pivot(index="cycle", columns="group", values="n_deadline_month")
        print(t.to_string()); print("counts in deadline month:"); print(n.to_string())
    print("\n=== data quality ==="); print(dq.to_string(index=False))


if __name__ == "__main__":
    main()
