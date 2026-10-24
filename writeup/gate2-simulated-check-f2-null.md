# Family 2 null check (simulated)

Annual-term world, planted workload HR 1.00, messy permit tables, Branch B, 30 repeats (seeds 900 to 929 / 950 to 979).

- Geometric mean of the C1 estimate: **0.995** (truth 1.000).
- Share of intervals containing 1.00: **0.87** (95% intended). Share with p below 0.05: **0.13** (5% intended).
- With 30 repeats the standard error of a coverage figure is about 0.04, so 0.87 is a little low but not certain. Likely cause: the 90-day workload moves slowly, so neighbouring quarters are not independent and about 42 quarters carry fewer than 42 independent pieces of information. This is a property of the pre-registered estimator (7.4), not changed here.
- Compare Family 1 (section 4 of `gate2-simulated-check.md`): coverage 0.95 to 1.00 over 20 repeats.
