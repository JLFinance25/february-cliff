# Family 1 results: time to repair clearance (facade file only)

Drafted with Claude (AI); directed by Jayden Ling.

Aggregated results only: hazard ratios, intervals and counts. No building identifier appears in this file or in any table written with it.

## 1. Frame and PLUTO match (counts)

| Item | Count |
|---|---|
| frame before public exclusion | 6,174 |
| pluto matched | 6,071 |
| pluto not matched | 103 |
| public owner lots | 1,346 |
| owner type X | 698 |
| carried over | 3,708 |
| stories missing | 177 |
| initial rows in status and cycles | 7,158 |
| dropped no F | 3 |
| dropped bad bin | 0 |
| dropped no group | 0 |
| dropped F after end | 855 |
| dropped repeats | 126 |
| before public exclusion | 6,174 |
| pluto rows | 858,284 |
| bbl matches own fields | 858,284 |
| duplicate bbl | 0 |

## 2. Counts-only gates (before any model is fit)

- Clearing-filing availability (3.1 b): overall 0.782, Early filers 0.839, by cycle cycle 8: 0.840, cycle 9: 0.738. Cycles kept: [8, 9].
- C5: {'run': True, 'filings': 4828, 'events': 3207, 'quarters': 40, 'why': None}
- C6: {'run': True, 'filings': 931, 'events': 722, 'quarters': 30, 'early_availability': 0.8388829215896885, 'why': None}
- Quiet cut-off (40th percentile of workload) 0.362; busy cut-off (70th) 0.927.
- Corner cells (rows / events; each needs 50 and 20): Early-quiet 649/499 (pass), Early-busy 82/53 (pass), Late-quiet 996/562 (pass), Late-busy 1369/861 (pass)
- Residual SD of workload after year and month 0.309, after filing timing too 0.307, ratio 0.995.

## 3. Confirmatory tests (primary interval: delete-one-quarter jackknife, t on K - 1 df; deviation D4)

Hazard ratio per wave unit (400 UNSAFE filings in 90 days). Below 1 = repairs clear more slowly when the city is busy.

| Test | Sample | Quarters K | Events | HR (95% interval) | p | Holm | Effect size (7.5) |
|---|---|---|---|---|---|---|---|
| C5 | all filings (M5) | 40 | 3,207 | 0.991 (0.856 to 1.148) | 0.9033 | not significant (threshold 0.050) | no meaningful effect |
| C6 | early filers (M6) | 30 | 722 | 1.235 (0.797 to 1.914) | 0.3322 | not significant (threshold 0.025) | inconclusive |

Placebos (on M5): PL1 (quiet months of wave years) HR 0.944 (0.660 to 1.350); PL2 (workload of the 90 days after F) HR 0.988 (0.672 to 1.451). PL1 warning: **no**.

Reading by the pre-registered table (section 8), applied mechanically:

- C5 reads 'not slowed', C6 reads 'inconclusive': No overall slowdown; the early-filer check is too small to add anything. (Not: a bottleneck claim.)

## 4. Variants (one change at a time; estimates and intervals only, no significance claims)

| Model | Variant | HR (95% interval) | Events | Method |
|---|---|---|---|---|
| C5 | V1 | 1.008 (0.875 to 1.161) | 3,535 | delete-one-cluster jackknife |
| C5 | V2 | 0.991 (0.856 to 1.148) | 3,207 | delete-one-cluster jackknife |
| C5 | V3 | 0.997 (0.846 to 1.174) | 2,993 | delete-one-cluster jackknife |
| C5 | V4 | 0.899 (0.806 to 1.003) | 3,207 | delete-one-cluster jackknife |
| C5 | V5 | 0.973 (0.812 to 1.166) | 3,207 | delete-one-cluster jackknife |
| C5 | V6 | 0.990 (0.854 to 1.147) | 3,229 | delete-one-cluster jackknife |
| C5 | V7a | 0.999 (0.870 to 1.147) | 3,207 | delete-one-cluster jackknife |
| C5 | V7b | 0.962 (0.777 to 1.190) | 3,207 | delete-one-cluster jackknife |
| C5 | V8 | 1.090 (0.614 to 1.934) | 3,207 | delete-one-cluster jackknife |
| C5 | V9a | 0.974 (0.842 to 1.127) | 3,207 | delete-one-cluster jackknife |
| C5 | V9b | 1.010 (0.865 to 1.179) | 3,723 | delete-one-cluster jackknife |
| C5 | V10 | 0.991 (0.856 to 1.148) | 3,207 | delete-one-cluster jackknife |
| C5 | V11a | 0.991 (0.871 to 1.129) | 3,207 | delete-one-cluster jackknife |
| C5 | V11b | 0.991 (0.864 to 1.138) | 3,207 | two-way cluster-robust (statsmodels), not jackknife |
| C5 | V11c | 0.991 (0.872 to 1.127) | 3,207 | delete-one-cluster jackknife |
| C5 | V12 (pre-registered quarter-clustered estimator) | 0.991 (0.863 to 1.138) | 3,207 | quarter-clustered, small-sample correction, t on K-1 df |
| C5 | V13 (wild cluster score bootstrap-t, B=499, seed fixed) | 0.991 (nan to 1.130) | 3,207 | interval by inverting the bootstrap test on a 21-point grid |
| C6 | V1 | 1.179 (0.808 to 1.719) | 758 | delete-one-cluster jackknife |
| C6 | V2 | 1.235 (0.797 to 1.914) | 722 | delete-one-cluster jackknife |
| C6 | V3 | 1.213 (0.742 to 1.982) | 610 | delete-one-cluster jackknife |
| C6 | V4 | 1.073 (0.828 to 1.391) | 722 | delete-one-cluster jackknife |
| C6 | V5 | 1.226 (0.792 to 1.899) | 722 | delete-one-cluster jackknife |
| C6 | V6 | 1.240 (0.797 to 1.929) | 724 | delete-one-cluster jackknife |
| C6 | V7a | 1.483 (0.860 to 2.559) | 722 | delete-one-cluster jackknife |
| C6 | V7b | 1.386 (0.888 to 2.165) | 722 | delete-one-cluster jackknife |
| C6 | V8 | 1.174 (0.542 to 2.542) | 722 | delete-one-cluster jackknife |
| C6 | V9a | 1.155 (0.828 to 1.611) | 722 | delete-one-cluster jackknife |
| C6 | V9b | 1.253 (0.912 to 1.722) | 1,003 | delete-one-cluster jackknife |
| C6 | V10 | 1.235 (0.797 to 1.914) | 722 | delete-one-cluster jackknife |
| C6 | V11a | 1.235 (0.823 to 1.853) | 722 | delete-one-cluster jackknife |
| C6 | V11b | 1.235 (0.916 to 1.665) | 722 | two-way cluster-robust (statsmodels), not jackknife |
| C6 | V11c | 1.235 (0.889 to 1.717) | 722 | delete-one-cluster jackknife |
| C6 | V12 (pre-registered quarter-clustered estimator) | 1.235 (0.908 to 1.680) | 722 | quarter-clustered, small-sample correction, t on K-1 df |
| C6 | V13 (wild cluster score bootstrap-t, B=499, seed fixed) | 1.235 (0.862 to 1.831) | 722 | interval by inverting the bootstrap test on a 21-point grid |

Robustness label (section 8; V12 and V13 share the main point estimate so are left out of the count): C5: **fragile**, C6: **fragile**

## 5. Exploratory items (labelled as such: estimates and intervals only; nothing here is a test)

| Item | What | Term | HR (95% interval) |
|---|---|---|---|
| E3 | filing-timing penalty among filings in the quiet workload band (H2 check) | timing=Middle | 0.903 (0.665 to 1.226) |
| E3 | filing-timing penalty among filings in the quiet workload band (H2 check) | timing=Last-minute | 1.535 (0.987 to 2.388) |
| E3 | filing-timing penalty among filings in the quiet workload band (H2 check) | timing=Past-deadline | 1.076 (0.679 to 1.706) |
| E4 | workload x filing-timing interactions (x = effect for Early filers; x*timing = extra for that group) | x | 1.146 (0.841 to 1.563) |
| E4 | workload x filing-timing interactions (x = effect for Early filers; x*timing = extra for that group) | x*timing=Middle | 1.094 (0.093 to 12.818) |
| E4 | workload x filing-timing interactions (x = effect for Early filers; x*timing = extra for that group) | x*timing=Last-minute | 0.839 (0.631 to 1.115) |
| E4 | workload x filing-timing interactions (x = effect for Early filers; x*timing = extra for that group) | x*timing=Past-deadline | 0.874 (0.588 to 1.298) |
| E5 | crude workload HR without filing-timing terms, next to C5 (size of the late-filer trap) | x | 0.992 (0.866 to 1.137) |
| E7 | public-owned lots on their own (PLUTO OwnerType C, M, O) | x | 1.735 (0.959 to 3.139) |
| E8 | C6 on early filers that were inside their own window (leaves out those who filed before it opened) | x | 1.104 (0.709 to 1.717) |
| E9 | filings carried over (prior SWARMP or UNSAFE), fitted separately | x | 0.956 (0.820 to 1.114) |
| E9 | filings not carried over, fitted separately | x | 1.079 (0.829 to 1.404) |
| E10 | workload from the building's own deadline group (x_own) versus the other two groups (x_other) | x_own | 0.975 (0.847 to 1.122) |
| E10 | workload from the building's own deadline group (x_own) versus the other two groups (x_other) | x_other | 1.077 (0.780 to 1.487) |

E1, E2 and E6 of section 9.2 are not Family 1 items. E6 (the live replication after Feb 21, 2027) is a later job.

## 6. Data and method notes

- Facade file: NYC Open Data `xubg-57si`, DOB NOW Safety - Facades Compliance Filings, pulled Oct 17, 2026 (`data/raw/SOURCES.md` section 3); PLUTO 26v2 (`64uk-42ks`), pulled Oct 18, 2026 (section 4). Aggregated and charted by us. Owner and inspector names were dropped in the first processing step and never used.
- Cycles in the analysis: [8, 9]; filings 4,828; quarters with filings 40.
- Primary standard errors: delete-one-quarter jackknife (deviation D4), t distribution with K - 1 degrees of freedom. The pre-registered quarter-clustered estimator is V12; the wild cluster bootstrap-t is V13.
- No result here is a statement about the safety of any building, owner or inspector. Nothing is reported at building level.

Run time 52 s.
