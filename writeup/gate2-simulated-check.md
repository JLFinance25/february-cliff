# Gate 2 code: simulated-data check

Run by `src/gate2_simcheck.py` on 2026-10-18 (Claude, Sonnet 5.5). **Simulated data only.** No real shed-permit row and no real repair duration was opened.
The real facade file was not used in this script at all. Planted effects are in log-hazard units per wave unit (400 UNSAFE filings in 90 days).

## 1. Workload code against a brute-force count
Largest difference over 1643 dates and look-backs of 30, 90 and 180 days: **0.00e+00** (must be 0).

## 2. Hand-written numpy fit against statsmodels (the M5 design on simulated data)
187,290 rows, 47 columns. Largest coefficient difference **3.9e-10** (must be below 5e-5 to agree at 4 decimals). Ratio of the hand-written clustered SE to statsmodels': min 0.9942, max 1.0011.

## 3. Planted effect and null (one simulated data set each; seed 11 and 12)
| Scenario | Test | Planted HR | Estimate (95% t interval, K-1 df) | Quarters K | Events |
|---|---|---|---|---|---|
| planted | C5 | 0.75 | 0.872 (0.698 to 1.090) | 43 | 2,638 |
| planted | C6 | 0.75 | 0.621 (0.389 to 0.991) | 36 | 898 |
|  | Holm | | C6: p=0.0461 sig=False, C5: p=0.2223 sig=False | | |
|  | placebo PL1 | 1.00 expected | 1.077 (0.874 to 1.328) | | |
|  | placebo PL2 | 1.00 expected | 1.356 (1.034 to 1.779) | | |
| null | C5 | 1.00 | 1.072 (0.879 to 1.307) | 43 | 2,855 |
| null | C6 | 1.00 | 0.977 (0.645 to 1.481) | 36 | 884 |
|  | Holm | | C5: p=0.4828 sig=False, C6: p=0.9121 sig=False | | |
|  | placebo PL1 | 1.00 expected | 0.992 (0.817 to 1.205) | | |
|  | placebo PL2 | 1.00 expected | 1.206 (0.992 to 1.466) | | |

## 4. Repeated simulations (20 data sets per row): bias and coverage of the 95% interval
Coverage = how often the interval contains the planted value. With few replicates it is rough; it is a sanity check, not a measurement.
| Scenario | Estimator | Planted HR | Mean estimate | Mean log-HR error | Coverage | Mean interval half-width (log) |
|---|---|---|---|---|---|---|
| no shared shock | C5 quarter | 0.75 | 0.742 | -0.010 | 0.95 | 0.229 |
| no shared shock | C5 block (V11c) | 0.75 | 0.742 | -0.010 | 0.95 | 0.241 |
| no shared shock | C6 quarter | 0.75 | 0.751 | +0.002 | 0.95 | 0.410 |
| no shared shock | C5 quarter | 1.00 | 0.983 | -0.017 | 1.00 | 0.213 |
| no shared shock | C5 block (V11c) | 1.00 | 0.983 | -0.017 | 1.00 | 0.228 |
| no shared shock | C6 quarter | 1.00 | 0.997 | -0.003 | 1.00 | 0.401 |
| shared quarter shock tau=0.15 | C5 quarter | 0.75 | 0.730 | -0.027 | 0.90 | 0.253 |
| shared quarter shock tau=0.15 | C5 block (V11c) | 0.75 | 0.730 | -0.027 | 0.90 | 0.241 |
| shared quarter shock tau=0.15 | C6 quarter | 0.75 | 0.746 | -0.005 | 0.85 | 0.425 |
| shared quarter shock tau=0.15 | C5 quarter | 1.00 | 0.975 | -0.025 | 0.90 | 0.237 |
| shared quarter shock tau=0.15 | C5 block (V11c) | 1.00 | 0.975 | -0.025 | 0.90 | 0.228 |
| shared quarter shock tau=0.15 | C6 quarter | 1.00 | 1.023 | +0.023 | 0.90 | 0.399 |

## 5. The slow-owner trap: late filers are slow, workload does nothing (planted workload HR = 1.00, late-filer log hazard -0.5)
- Crude estimate (no filing-timing terms, E5): 0.850 (0.667 to 1.085). Late filers crowd into busy periods, so the crude estimate is pulled below 1.
- C5 (with filing-timing terms): 0.901 (0.705 to 1.152).
- C6 (early filers only): 0.870 (0.555 to 1.362).

## 6. Every Family 1 variant and both placebos run (planted HR 0.75, seed 11)
| Variant | HR for workload (95% interval) | Rows | Events | Dropped columns |
|---|---|---|---|---|
| main | 0.872 (0.698 to 1.090) | 187,290 | 2,638 | stories=missing, owner_X, no_pluto_match |
| V1 | 0.835 (0.671 to 1.039) | 204,525 | 2,777 | stories=missing, owner_X, no_pluto_match |
| V2 | 0.924 (0.744 to 1.147) | 179,550 | 2,813 | stories=missing, owner_X, no_pluto_match |
| V3 | 0.906 (0.724 to 1.135) | 179,909 | 2,551 | stories=missing, owner_X, no_pluto_match |
| V4 | 1.072 (0.963 to 1.194) | 187,290 | 2,638 | stories=missing, owner_X, no_pluto_match |
| V5 | 0.872 (0.698 to 1.090) | 187,290 | 2,638 | stories=missing, owner_X, no_pluto_match |
| V6 | 0.863 (0.690 to 1.078) | 401,714 | 2,645 | stories=missing, owner_X, no_pluto_match |
| V7a | 0.919 (0.696 to 1.215) | 187,290 | 2,638 | stories=missing, owner_X, no_pluto_match |
| V7b | 1.037 (0.902 to 1.193) | 187,290 | 2,638 | stories=missing, owner_X, no_pluto_match |
| V8 | 0.913 (0.758 to 1.101) | 187,290 | 2,638 | stories=missing, owner_X, no_pluto_match |
| V9a | 0.812 (0.674 to 0.978) | 187,290 | 2,638 | stories=missing, owner_X, no_pluto_match |
| V9b | 0.872 (0.698 to 1.090) | 187,290 | 2,638 | stories=missing, owner_X, no_pluto_match |
| V10 | 0.891 (0.713 to 1.114) | 187,290 | 2,654 | stories=missing, owner_X, no_pluto_match |
| V11a | 0.872 (0.711 to 1.069) | 187,290 | 2,638 | stories=missing, owner_X, no_pluto_match |
| V11b | 0.872 (0.698 to 1.090) | 187,290 | 2,638 | stories=missing, owner_X, no_pluto_match |
| V11c | 0.872 (0.703 to 1.082) | 187,290 | 2,638 | stories=missing, owner_X, no_pluto_match |
| placebo PL1 | 1.077 (0.874 to 1.328) | 187,290 | 2,638 | |
| placebo PL2 | 1.356 (1.034 to 1.779) | 187,290 | 2,638 | |
| E10 own / other | own 0.894, other 0.849 | 187,290 | 2,638 | |

## 7. Stop rules, availability rule and identifiability rule on simulated tables
- Planted data set: availability by cycle {8: 0.644, 9: 0.651}; C5 run = True, C6 run = True; separable (all four cells) = True.
  Corner cells (rows / events): Early-quiet 1052/543, Early-busy 297/115, Late-quiet 1191/465, Late-busy 1536/597
- A 400-filing sample: C5 run = False (stop rule).
- No clearing filings at all: C5 run = False (availability rule failed).
- Early filers removed from busy periods: C5 run = False (not separable from filer type); C6 run = False (Early cells too thin).

## 8. Family 2 (shed permits), simulated
**World: annual terms, workload HR planted 0.75, winter-start HR planted 0.80.** Cleaning: DOB NOW 13,444 -> 11,694 rows, legacy 4,974 -> 4,742. Structure check: terms of 120 days or less 0.00, median term 349, renewal visibility 0.68 -> branch B.
  Link share 0.69; spells linked 3,904; ended events 2,474; quarters with decision points 42.
  | Test | Planted | Estimate (95% t interval) | Run? |
  |---|---|---|---|
  | C1 | 0.75 | 0.856 (0.701 to 1.045) | yes |
  | C2 | 0.75 | 0.946 (0.630 to 1.421) | yes |
  | C3 | 0.75 | 0.854 (0.689 to 1.059) | yes |
  | C4 | 0.80 | 0.807 (0.733 to 0.888) | yes |
  Holm: C4: p=0.0000 sig=True, C1: p=0.1230 sig=False, C3: p=0.1472 sig=False, C2: p=0.7831 sig=False

**World: annual terms, workload HR planted 1.00, winter-start HR planted 1.00.** Cleaning: DOB NOW 12,010 -> 10,445 rows, legacy 4,616 -> 4,408. Structure check: terms of 120 days or less 0.00, median term 350, renewal visibility 0.65 -> branch B.
  Link share 0.70; spells linked 3,979; ended events 2,662; quarters with decision points 42.
  | Test | Planted | Estimate (95% t interval) | Run? |
  |---|---|---|---|
  | C1 | 1.00 | 1.197 (1.069 to 1.341) | yes |
  | C2 | 1.00 | 1.085 (0.792 to 1.486) | yes |
  | C3 | 1.00 | 1.264 (1.105 to 1.446) | yes |
  | C4 | 1.00 | 0.974 (0.883 to 1.074) | yes |
  Holm: C3: p=0.0011 sig=True, C1: p=0.0027 sig=True, C4: p=0.5867 sig=False, C2: p=0.6048 sig=False

**World: 90-day terms, workload HR planted 0.75, winter-start HR planted 0.80.** Cleaning: DOB NOW 20,252 -> 17,608 rows, legacy 10,415 -> 10,061. Structure check: terms of 120 days or less 1.00, median term 90, renewal visibility 0.80 -> branch A.
  Link share 0.74; spells linked 4,195; ended events 3,644; quarters with decision points 44.
  | Test | Planted | Estimate (95% t interval) | Run? |
  |---|---|---|---|
  | C1 | 0.75 | 0.676 (0.543 to 0.841) | yes |
  | C2 | 0.75 | 0.611 (0.402 to 0.928) | yes |
  | C3 | 0.75 | 0.700 (0.560 to 0.875) | yes |
  | C4 | 0.80 | 0.823 (0.754 to 0.899) | yes |
  Holm: C4: p=0.0001 sig=True, C1: p=0.0008 sig=True, C3: p=0.0024 sig=True, C2: p=0.0219 sig=True

Repeated Family 2 simulations (24 data sets per row; clean permit worlds, no quirks): bias and coverage of C1. **Corrected Oct 18, 2026** (see "What changed" below); source `src/gate2_simcheck_f2_mc.py`, full text in `gate2-simulated-check-f2-mc.md`.

| World | Planted HR | Repeats | Mean estimate | Mean log-HR error | Coverage | SD of log estimate |
|---|---|---|---|---|---|---|
| 90-day terms | 0.75 | 24 | 0.735 | -0.020 | 0.92 | 0.111 |
| 90-day terms | 1.00 | 24 | 1.078 | +0.075 | 0.79 | 0.142 |
| annual terms | 0.75 | 24 | 0.744 | -0.008 | 0.83 | 0.135 |
| annual terms | 1.00 | 24 | 1.017 | +0.017 | 0.92 | 0.137 |

**What changed.** The first version of this file (commit eb5c6dc) showed an 8-repeat table whose 90-day-terms row with planted 0.75 read: mean log-HR error -0.116, coverage 0.62. That row came from the corrected simulator (an earlier simulator bug, permit chains capped at 14 renewals, which created fake "ended" rows in the 90-day world, had been fixed before that run) but from only 8 repeats and one set of seeds. Rerunning with 24 repeats on a different set of seeds (the committed script `src/gate2_simcheck_f2_mc.py`) gives -0.020 (table above). Pooled over all 32 repeats the mean error in that world is about -0.044, roughly 2 standard errors from zero: small and possibly chance, not shown to be a real bias. The other three worlds are within 0.02 of the planted value, apart from the 90-day null at +0.075 (also about 2 standard errors; opposite sign to the planted-0.75 row, so it reads as noise). **Coverage is the weak spot:** 0.79 to 0.92 with 24 repeats (standard error about 0.08 each), which agrees with the 30-repeat null check in `gate2-simulated-check-f2-null.md` (0.87). The calibration job (`gate2-calibration.md`) measures it with more repeats.

Every Family 2 variant (S1 to S20) and both placebos, annual-terms world with planted 0.75:

| Variant | C1 HR (95% interval) | Decision points | Ended | Dropped columns |
|---|---|---|---|---|
| main | 0.856 (0.701 to 1.045) | 11,478 | 2,474 | age=gt24 |
| S1 | 1.133 (0.887 to 1.446) | 3,939 | 3,531 | age=gt24 |
| S2 | 0.854 (0.693 to 1.053) | 12,103 | 2,343 | age=gt24 |
| S3 | 0.877 (0.679 to 1.133) | 7,887 | 1,675 | age=gt24 |
| S4 | 0.846 (0.693 to 1.034) | 11,409 | 2,463 | age=gt24 |
| S5 | 1.074 (0.743 to 1.552) | 11,478 | 2,474 | age=gt24 |
| S6 | 0.924 (0.782 to 1.092) | 11,478 | 2,474 | age=gt24 |
| S7 | 0.904 (0.697 to 1.173) | 9,397 | 2,013 | age=gt24, step_2020_02_21 |
| S8 | 0.837 (0.697 to 1.006) | 12,406 | 2,726 | age=gt24 |
| S9 | 0.734 (0.626 to 0.861) | 11,478 | 2,474 | age=gt24 |
| S10a | 0.856 (0.713 to 1.028) | 11,478 | 2,474 | age=gt24 |
| S10b | 0.856 (0.704 to 1.041) | 11,478 | 2,474 | age=gt24 |
| S10c | 0.856 (0.670 to 1.093) | 11,478 | 2,474 | age=gt24 |
| S11 | 7.132 (0.127 to 399.408) | 637 | 25 | age=gt24, step_2019_12_17 |
| S12 | 0.951 (0.738 to 1.227) | 11,478 | 2,474 | age=gt24 |
| S13 | 0.854 (0.703 to 1.038) | 11,666 | 2,494 | age=gt24 |
| S14 | 0.855 (0.700 to 1.045) | 11,478 | 2,474 | age=gt24 |
| S15 | 0.722 (0.502 to 1.040) | 5,267 | 1,140 | carried_over, age=gt24 |
| S16 | 0.855 (0.694 to 1.054) | 12,417 | 2,666 | age=gt24 |
| S17 | 1.141 (0.663 to 1.961) | 12,446 | 2,838 | age=gt24 |
| S18 | 0.808 (0.669 to 0.976) | 11,478 | 2,474 | age=gt24 |
| S19 | 0.956 (0.748 to 1.222) | 10,215 | 2,184 | age=gt24 |
| S20 | 1.167 (0.779 to 1.749) | 11,478 | 2,474 | age=gt24 |
| placebo PL1 | 0.950 (0.802 to 1.125) | 11,478 | 2,474 | |
| placebo PL2 | 1.025 (0.841 to 1.250) | 11,478 | 2,474 | |
| Branch A exposure on annual-term data (not a variant) | 1.167 | 11,478 | 2,474 | |

Sanity count: spells standing on a simulated Aug 17, 2026 date: 1107 of 4,575 spells (the code path for the check in 4.5).

## 9. Variant runners, robustness label and placebo warning
- Family 1 runner on 5 variants: all ran = True; robustness label for the main estimate = **fragile**.
- Family 2 runner on 4 variants: all ran = True; robustness label = **fragile**.
- Planted-data PL1 warning flag (Family 1): False (False expected).
- Residual SD of x after year and month, then after filing timing too (Family 1 planted data): {'sd_after_year_month': 0.17813637649417816, 'sd_after_year_month_timing': 0.17691460059629072, 'ratio': 0.9931413452887464}

## Summary of what was and was not shown
- Planted 0.75 recovered by C5 at 0.872 (0.698 to 1.090).
- Across 20 repeats the mean log-HR error of C5 (quarter clustering, no shared shock) was within 0.06 of zero for both planted values: **True**.
- C6 mean log-HR errors (no shared shock): [np.float64(0.002), np.float64(-0.003)]. C6 has about a third of C5's events, so its interval is about twice as wide and its mean error needs more repeats to settle.
- Family 2 (C1) mean log-HR errors over 24 repeats per world (corrected Oct 18, 2026, see section 8): annual 0.75: -0.008, annual 1.00: +0.017, 90-day 0.75: -0.020, 90-day 1.00: +0.075. The estimates are close to the planted values (the one 2-standard-error miss is described in section 8); the intervals look somewhat too narrow (coverage 0.79 to 0.92).
- Single-run Family 2 null worlds (section 8): 4 tests, 2 with an interval that excludes 1 (B_1.0_C1, B_1.0_C3). At a 5% level one in twenty is expected by chance; the repeated runs above are the better guide.
- Not shown by simulation: whether real data behave like these tables. Simulated workload is much smoother than the real surges; the planted shocks are the only source of shared quarter-to-quarter noise.
- Known simplifications in the simulation: no COVID pause, no change in policy, permit renewals always follow the exact hazard model, shed-link rules are never violated by real-world data quirks.
