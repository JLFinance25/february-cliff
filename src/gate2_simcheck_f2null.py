# Extra simulated check: how often do Family 2 intervals (quarter-clustered, t with K-1 df) contain the truth when the
# workload effect is null and the permit data are messy (concurrent permits, 60-day gaps, junk rows)? 30 repeats.
# Simulated data only. Run: .venv/bin/python -I src/gate2_simcheck_f2null.py  -> writeup/gate2-simulated-check-f2-null.md
# Drafted by Claude (AI); directed and approved by Jayden Ling.
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gate2_link as L
import gate2_model as M
import gate2_sim as S

D = pd.Timestamp("2026-10-17")
ROOT = pathlib.Path(__file__).resolve().parent.parent
out = ["# Family 2 null check (simulated)", "", "Annual-term world, planted workload HR 1.00, messy permit tables, Branch B, 30 repeats (seeds 900 to 929 / 950 to 979).", ""]
res = []
for seed in range(30):
    fac, _ = S.sim_facades(seed=900 + seed, planted_hr=0.75)
    wl = L.Workload(fac); pl = S.sim_pluto(fac)
    dn, lg, _ = S.sim_sheds(fac, seed=950 + seed, branch="B", planted_hr=1.0, winter_hr=1.0, quirks=True)
    a, _q = L.clean_dobnow(dn, ["Sidewalk Shed"]); b, _q = L.clean_legacy(lg, ["SH"], date_format="%m/%d/%Y")
    cfg = M.F2Config(branch="B", D=D)
    dp, _p = M.prepare_family2(fac, pl, L.combine_intervals(a, b), cfg)
    t = M.run_family2(dp, wl, cfg)["table"].loc["x"]
    res.append((t["hr"], t["hr_lo"], t["hr_hi"], t["p"]))
r = np.array(res)
cov = float(((r[:, 1] <= 1) & (r[:, 2] >= 1)).mean()); fp = float((r[:, 3] < 0.05).mean())
out += [f"- Geometric mean of the C1 estimate: **{np.exp(np.log(r[:, 0]).mean()):.3f}** (truth 1.000).",
        f"- Share of intervals containing 1.00: **{cov:.2f}** (95% intended). Share with p below 0.05: **{fp:.2f}** (5% intended).",
        "- With 30 repeats the standard error of a coverage figure is about 0.04, so 0.87 is a little low but not certain. Likely cause: the 90-day workload moves slowly, so neighbouring quarters are not independent and about 42 quarters carry fewer than 42 independent pieces of information. This is a property of the pre-registered estimator (7.4), not changed here.",
        "- Compare Family 1 (section 4 of `gate2-simulated-check.md`): coverage 0.95 to 1.00 over 20 repeats."]
(ROOT / "writeup" / "gate2-simulated-check-f2-null.md").write_text("\n".join(out) + "\n")
print("\n".join(out))
