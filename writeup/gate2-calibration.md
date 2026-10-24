# Calibration of the Gate 2 standard errors (simulated data)

Run by `src/gate2_calibration.py`, 150 repeats per cell, 1100 s on 8 workers. **Simulated data only**; the real file contributed only the daily COUNT series of UNSAFE Initial filings (an aggregate) that sets the roughness of the simulated workload.

Cells: planted workload HR 1.00 and 0.75; shared per-quarter shock tau 0, 0.10, 0.20; Family 1 C5 (all filings) and C6 (Early filers), Family 2 C1 (annual terms). Numbers in the table are shares with the Monte Carlo standard error in brackets. **Coverage** = how often the 95% interval (for the bootstrap: the 5% test of the true value) contains the truth; intended 0.95. **Reject 1** = share with p below 0.05 against HR = 1: the false-alarm rate when the planted HR is 1.00 (intended 0.05) and the power when it is 0.75. **Half-width** = average half-width of the interval on the log scale.

Failed replicates (errors): 0 {}

| Family | Test | Planted HR | tau | Reps | Mean log-HR error | Pre-registered: coverage | Reject 1 | Half-width | Jackknife: coverage | Reject 1 | Half-width | Bootstrap-t: coverage | Reject 1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| F1 | C5 | 0.75 | 0.00 | 150 | -0.006 | 0.91 (0.02) | 1.00 (0.00) | 0.117 | 0.95 (0.02) | 0.98 (0.01) | 0.147 | 0.97 (0.01) | 0.97 (0.01) |
| F1 | C5 | 0.75 | 0.10 | 150 | -0.006 | 0.89 (0.03) | 1.00 (0.00) | 0.123 | 0.99 (0.01) | 0.95 (0.02) | 0.160 | 0.95 (0.02) | 0.93 (0.02) |
| F1 | C5 | 0.75 | 0.20 | 150 | +0.012 | 0.91 (0.02) | 0.97 (0.01) | 0.135 | 0.99 (0.01) | 0.87 (0.03) | 0.185 | 0.98 (0.01) | 0.87 (0.03) |
| F1 | C5 | 1.00 | 0.00 | 150 | +0.009 | 0.89 (0.03) | 0.11 (0.03) | 0.103 | 0.93 (0.02) | 0.07 (0.02) | 0.131 | 0.97 (0.01) | 0.03 (0.01) |
| F1 | C5 | 1.00 | 0.10 | 150 | +0.008 | 0.95 (0.02) | 0.05 (0.02) | 0.110 | 0.98 (0.01) | 0.02 (0.01) | 0.144 | 0.98 (0.01) | 0.02 (0.01) |
| F1 | C5 | 1.00 | 0.20 | 150 | -0.002 | 0.92 (0.02) | 0.08 (0.02) | 0.123 | 0.97 (0.01) | 0.03 (0.01) | 0.168 | 0.95 (0.02) | 0.05 (0.02) |
| F1 | C6 | 0.75 | 0.00 | 150 | -0.008 | 0.91 (0.02) | 0.72 (0.04) | 0.230 | 0.97 (0.01) | 0.46 (0.04) | 0.305 | 0.96 (0.02) | 0.51 (0.04) |
| F1 | C6 | 0.75 | 0.10 | 150 | -0.013 | 0.89 (0.03) | 0.67 (0.04) | 0.234 | 0.97 (0.01) | 0.46 (0.04) | 0.317 | 0.96 (0.02) | 0.52 (0.04) |
| F1 | C6 | 0.75 | 0.20 | 150 | +0.016 | 0.89 (0.03) | 0.54 (0.04) | 0.246 | 0.97 (0.01) | 0.31 (0.04) | 0.347 | 0.93 (0.02) | 0.40 (0.04) |
| F1 | C6 | 1.00 | 0.00 | 150 | +0.035 | 0.89 (0.03) | 0.11 (0.03) | 0.211 | 0.97 (0.01) | 0.03 (0.01) | 0.282 | 0.95 (0.02) | 0.05 (0.02) |
| F1 | C6 | 1.00 | 0.10 | 150 | +0.022 | 0.89 (0.03) | 0.11 (0.03) | 0.213 | 0.95 (0.02) | 0.05 (0.02) | 0.292 | 0.92 (0.02) | 0.08 (0.02) |
| F1 | C6 | 1.00 | 0.20 | 150 | +0.005 | 0.93 (0.02) | 0.07 (0.02) | 0.231 | 0.97 (0.01) | 0.03 (0.01) | 0.325 | 0.98 (0.01) | 0.02 (0.01) |
| F2 | C1 | 0.75 | 0.00 | 150 | +0.006 | 0.86 (0.03) | 0.91 (0.02) | 0.143 | 0.94 (0.02) | 0.85 (0.03) | 0.180 | 0.93 (0.02) | 0.83 (0.03) |
| F2 | C1 | 0.75 | 0.10 | 150 | +0.005 | 0.91 (0.02) | 0.95 (0.02) | 0.149 | 0.98 (0.01) | 0.83 (0.03) | 0.199 | 0.96 (0.02) | 0.83 (0.03) |
| F2 | C1 | 0.75 | 0.20 | 150 | -0.016 | 0.89 (0.03) | 0.87 (0.03) | 0.177 | 0.95 (0.02) | 0.66 (0.04) | 0.251 | 0.91 (0.02) | 0.74 (0.04) |
| F2 | C1 | 1.00 | 0.00 | 150 | +0.003 | 0.87 (0.03) | 0.13 (0.03) | 0.129 | 0.94 (0.02) | 0.06 (0.02) | 0.165 | 0.94 (0.02) | 0.06 (0.02) |
| F2 | C1 | 1.00 | 0.10 | 150 | +0.002 | 0.93 (0.02) | 0.07 (0.02) | 0.143 | 0.96 (0.02) | 0.04 (0.02) | 0.193 | 0.94 (0.02) | 0.06 (0.02) |
| F2 | C1 | 1.00 | 0.20 | 150 | +0.009 | 0.89 (0.03) | 0.11 (0.03) | 0.171 | 0.98 (0.01) | 0.02 (0.01) | 0.247 | 0.93 (0.02) | 0.07 (0.02) |

## Decision rule fixed by the main session

The pre-registered estimator stays primary unless, at tau = 0.10, its coverage in Family 1 (C5) or Family 2 (C1) is below 0.92 AND an alternative reaches 0.93 or more. Values at tau = 0.10 (pooled over the two planted HRs, then each):

| Test | HR cell | Pre-registered | Jackknife | Bootstrap-t | Rule triggered? |
|---|---|---|---|---|---|
| C5 | pooled (n=300) | 0.923 | 0.987 | 0.967 | no |
| C5 | HR 1.00 (n=150) | 0.953 | 0.980 | 0.980 | no |
| C5 | HR 0.75 (n=150) | 0.893 | 0.993 | 0.953 | YES |
| C1 | pooled (n=300) | 0.920 | 0.970 | 0.950 | no |
| C1 | HR 1.00 (n=150) | 0.927 | 0.960 | 0.940 | no |
| C1 | HR 0.75 (n=150) | 0.913 | 0.980 | 0.960 | YES |

The main session decides; this file only reports.

## Checks of the approximations

- My cluster SE for the workload term over statsmodels': 0.9988 (expected about 1).
- One-step against exact (refit) deletion of the first 15 quarters: largest difference in the workload coefficient 1.26e-03 (typical size 1.68e-02).
- Test of beta_x = 0 on one data set (t = -6.10): score bootstrap p = 0.002; refitting wild bootstrap (B = 99, outcome redrawn) p = 0.010. These are two different bootstraps; they should agree roughly, not exactly.
