# Larger Family 2 repeat check (job D): 24 repeats per world (annual-term and 90-day-term permits, planted workload HR
# 0.75 and 1.00), clean permit tables (no quirks), on the corrected simulator. Replaces the 8-repeat rows in section 8 of
# gate2_simulated_check.md, whose 90-day-term row (-0.116, coverage 0.62) came from too few repeats and a simulator that
# was fixed before the freeze but run again with only 8 repeats. Simulated data only.
# Run: .venv/bin/python -I src/gate2_simcheck_f2_mc.py   -> writeup/gate2-simulated-check-f2-mc.md
import os
for _v in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"
import multiprocessing as mp
import pathlib
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import gate2_link as L
import gate2_model as M
import gate2_sim as S

ROOT = pathlib.Path(__file__).resolve().parent.parent
D = pd.Timestamp("2026-10-17")
N = 24


def one(job):
    branch, hr, rep = job
    fa, _ = S.sim_facades(seed=700 + rep, planted_hr=0.75)
    wa = L.Workload(fa)
    dn, lg, _ = S.sim_sheds(fa, seed=800 + rep, branch=branch, planted_hr=hr, winter_hr=1.0, quirks=False)
    a, _q = L.clean_dobnow(dn, ["Sidewalk Shed"]); b, _q = L.clean_legacy(lg, ["SH"], date_format="%m/%d/%Y")
    cfg = M.F2Config(branch=branch, D=D)
    dp, _p = M.prepare_family2(fa, None, L.combine_intervals(a, b), cfg)
    h = M.hr_of(M.run_family2(dp, wa, cfg), "x")
    return branch, hr, h["hr"], h["lo"], h["hi"]


if __name__ == "__main__":
    jobs = [(b, h, r) for b in "BA" for h in (0.75, 1.0) for r in range(N)]
    with mp.get_context("spawn").Pool(4) as pool:
        res = pool.map(one, jobs, chunksize=1)
    df = pd.DataFrame(res, columns=["branch", "hr", "est", "lo", "hi"])
    lines = ["# Family 2 repeat check (simulated), 24 repeats per world", "",
             "Replaces the 8-repeat table in section 8 of `gate2-simulated-check.md`. Clean permit tables, corrected simulator (permit chains no longer capped at 14, which had created fake 'ended' rows in the 90-day-term world).", "",
             "| World | Planted HR | Repeats | Mean estimate | Mean log-HR error | Coverage | SD of log estimate |", "|---|---|---|---|---|---|---|"]
    for (b, h), g in df.groupby(["branch", "hr"]):
        lh = np.log(g["est"])
        lines.append(f"| {'annual terms' if b == 'B' else '90-day terms'} | {h:.2f} | {len(g)} | {np.exp(lh.mean()):.3f} | {lh.mean() - np.log(h):+.3f} | {((g['lo'] <= h) & (g['hi'] >= h)).mean():.2f} | {lh.std():.3f} |")
    (ROOT / "writeup" / "gate2-simulated-check-f2-mc.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
