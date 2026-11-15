# Do deadline waves slow facade repairs and sidewalk-shed removal? A pre-registered test on NYC Open Data

Drafted Oct 22, 2026. Final writing pass Oct 24, 2026 (clarity and flow only; no number, test or finding changed).

Jayden Ling. Code and draft text by Claude (Anthropic's AI assistant) under my direction; I read and approved sections 1 and 7 on Oct 26, 2026.

## Abstract

**Objective.** NYC's facade program (FISP) gives three groups of tall buildings deadlines that all fall on Feb 21, so UNSAFE facade reports arrive in waves. We tested whether those waves slow the repairs that follow. **Data.** Public NYC Open Data: 87,455 facade filings (`xubg-57si`, pulled Oct 17, 2026), two shed-permit files (about 5 million rows) and PLUTO. The headline sample is 4,828 privately owned UNSAFE filings from cycles 8 and 9. **Method.** A pre-registered discrete-time hazard model (locked before any repair time was seen) related time to repair clearance to citywide workload, with jackknife intervals over 40 quarters. **Findings.** Workload was not linked to slower repair clearance: hazard ratio 0.991 per wave unit (95% interval 0.856 to 1.148). That rules out a slowdown of 20% or more per 30-day step; roughly, waits change by 13% shorter to 17% longer per wave unit. The early-filer check (1.235, 0.797 to 1.914) and the shed test (0.971, 0.748 to 1.259) were inconclusive. **What is new.** A keyword search of DOB's December 2025 FISP study found no earlier test of whether the deadline calendar slows repairs; no wider literature search was done. **Practical use.** For DOB rule writers and the City Council, repair clearance gives no reason to spread out the Feb 21 deadline; the shed question stays open.

**Status of this file.** Every Family 1 number below comes from `writeup/gate2-family1-results.md` (the runner's own output; `figures/gate2_family1_*.csv` holds the same tables) or from `PREREG.md`, and is cited there. Every Family 2 number comes from `writeup/gate2-family2-results.md` unless another source is named. Anything not checked against a source is marked **UNVERIFIED**. Family 1 (repair clearance, the headline) is sections 3 to 7. Family 2 (sidewalk-shed permits, secondary and weaker evidence) is section 8; it ran after Family 1.

---

## Key terms (each is also explained where it first appears)

- **FISP.** NYC's Facade Inspection and Safety Program. Buildings over six stories must have an engineer inspect the facade and file a report once per five-year cycle (`PLAN.md`; the "over six stories" scope was not re-checked against the law in this pass, UNVERIFIED). Buildings are split into three deadline groups (A, B and C) by the last digit of their tax block, and each group's filing window ends on Feb 21 of a different year (`PLAN.md`; `writeup/gate0-dob-fisp-study.md`).
- **UNSAFE filing.** An engineer's FISP report that rates a facade condition UNSAFE. The other ratings are SAFE and SWARMP ("safe with a repair and maintenance program"). These are ratings written on filings. This report makes no safety judgment of its own about any building. The city's rule says an unsafe condition must be corrected within 90 days of the report, with extensions possible (1 RCNY §103-04, as summarized in `PREREG.md` section 1). This study uses UNSAFE *Initial* filings, meaning the first report a building files in a cycle.
- **Repair clearance.** The engineer's later *Amended* filing, for the same building and cycle, rated SAFE or SWARMP: the report that records the condition as repaired. "Time to repair clearance" is the number of days from the UNSAFE filing to that clearing filing. It is a filing date, not the day the work ended.
- **Wave and wave unit.** A deadline wave is the surge of UNSAFE filings that lands around a group's Feb 21 deadline. **Workload** on a given day is the number of UNSAFE Initial filings citywide in the 90 days ending that day. One **wave unit** is 400 such filings, roughly how far a typical deadline wave sits above normal.
- **Hazard ratio (HR).** The *hazard* is the chance that something ends in a given time step (a repair clears, a shed comes down), given it has not ended yet. The hazard ratio compares that chance at one more wave unit of workload. HR 1 means no difference. Below 1 means things end more slowly when the city is busy. HR 0.80 means the chance of ending in each step is a fifth lower, which makes waiting about 25% longer while the wave lasts (`PREREG.md` section 7.5).
- **95% interval.** The range of hazard ratios the data are consistent with. The plan's size rule (`PREREG.md` section 7.5): if the whole interval sits inside 0.80 to 1.25, the reading is "no meaningful effect." Anything else that is not a clear effect is "inconclusive," meaning the data cannot say.
- **Family 1 and Family 2.** The two pre-registered sets of tests. Family 1 (primary, gives the headline) is time to repair clearance, using the facade file alone. Family 2 (secondary, weaker) is how long sidewalk-shed permits last.

---

## 1. Summary

NYC's facade program (FISP) splits tall buildings into three deadline groups, and each group's filing window ends on Feb 21 in a different year. UNSAFE filings (engineers' reports that a facade condition needs repair) pile up around those dates. We asked whether those pile-ups, or "waves," slow down the repairs that follow.

We measured the days from each UNSAFE filing to the engineer's later filing that records the condition as repaired (the "repair clearance"). Then we compared filings made when the city's repair workload was high with filings made when it was low. Workload means UNSAFE filings citywide in the last 90 days.

**Result.** Across all 4,828 filings, a busier city was not linked to slower repair clearance. The hazard ratio was 0.991 per wave unit of workload (400 UNSAFE filings in 90 days), with a 95% interval of 0.856 to 1.148. In plain words: when workload rises by one wave, the data fit anything from a chance of clearing in each 30-day step about 14% lower to about 15% higher, and the best estimate is almost no change. That whole interval sits inside the pre-registered "no meaningful effect" band of 0.80 to 1.25, so for this sample the data rule out a slowdown bigger than about 20% (a 20% drop in the chance of clearing per step, HR 0.80). The check on early filers, which is the test meant to tell a shared bottleneck apart from slow last-minute owners, was too wide to say anything: 1.235 (0.797 to 1.914). Both placebo tests (checks where the method should find nothing) came out clean.

**Shed test (secondary, weaker evidence).** Asking the same question of sidewalk-shed permits gave a similar estimate with much less precision. Across 1,762 shed-permit endings linked to UNSAFE filings, the hazard ratio per wave unit was 0.971 (0.748 to 1.259), p 0.82. Under the plan's size rule (`PREREG.md` section 7.5) that reading is **inconclusive**, not "no meaningful effect." Unlike Family 1, the interval does **not** rule out a 20% to 25% slowdown: its lower end, 0.748, is below 0.80, and its upper end reaches just past 1.25. No Family 2 test was significant. Before 2026, shed permits ran about a year, so removal dates are only approximate and a null result here is weak evidence (section 8).

**What this does and does not show.** It shows no sign of a workload slowdown in repair clearance, measured with the facade file alone. It does not show that contractors have spare capacity, because contractors are not observed. And because the early-filer check is inconclusive, it does not fully separate the two rival explanations below. Section 7 lists the limits.

## 2. Question and hypotheses

Does the pile-up of repair demand around facade deadlines make repairs take longer? Two explanations were set against each other before any data was analysed (`PREREG.md` section 2):

- **H1, shared bottleneck.** When many repairs are demanded at once, the repair pipeline (contractors, certifying engineers, permit sign-offs) gets congested, so repairs take longer for everyone. This predicts a hazard ratio below 1 per wave unit, with 0.80 or lower treated as meaningful.
- **H2, owner behavior.** Owners who file at the last minute are slow for their own reasons (money, boards, lawsuits). Busy periods only *look* harmful because late filers crowd into them. This predicts a hazard ratio near 1 once filing timing is accounted for.

The test that separates them is **C6, early filers only**. If the cause is a shared bottleneck, buildings that filed early must also slow down when the city is busy. If only late filers slow down, that points to owner behavior.

The shed-permit tests (Family 2, secondary) ask the same question about shed removal: C1 (all linked sheds), C2 (early filers only), C3 (workload from the other deadline groups' filings) and C4 (sheds started December to February, a cold-weather check; the idea that winter slows facade repair is a hypothesis, not a checked fact, UNVERIFIED).

**Why we assumed waves exist (Gate 1, exploratory).** Gate 1 was an early check, run on Oct 16, 2026, **before any pre-registration**. In Cycle 9, 33% to 37% of each group's initial filings fell in its deadline month, against about 4% if filings were spread evenly (`PREREG.md` section 1). That is why deadline waves are assumed to exist. It is background, not a result of this report.

**Prior work (Gate 0).** A keyword search of DOB's December 2025 FISP study by Thornton Tomasetti (https://www.nyc.gov/assets/buildings/pdf/fisp.pdf, read Oct 17, 2026), plus reading the passages it found, turned up nothing on deadline bunching, filing timing or contractor capacity. That means "not found by that search," not "proven absent." Not every page was read (`writeup/gate0-dob-fisp-study.md`).

## 3. Data

All data are public NYC Open Data. Only aggregated results appear in this report. No building identifier, owner name or inspector name is reported.

| Source | What | Pulled |
|---|---|---|
| DOB NOW: Safety - Facades Compliance Filings, dataset `xubg-57si` (https://data.cityofnewyork.us/d/xubg-57si), Department of Buildings | 87,455 rows, one snapshot, about 79.8 MB as downloaded (two JSON pages); filing type, rating, dates, cycle, building number, tax block | Oct 17, 2026 |
| DOB NOW: Build - Approved Permits, dataset `rbx6-tga4` (https://data.cityofnewyork.us/d/rbx6-tga4), Department of Buildings (Family 2 only) | 1,016,520 rows, one snapshot, 324,735,974 bytes as downloaded (selected columns only); permit type, status, dates, building number | Oct 18, 2026 |
| DOB Permit Issuance, older BIS system, dataset `ipu4-2q9a` (https://data.cityofnewyork.us/d/ipu4-2q9a), Department of Buildings (Family 2 only) | 3,990,985 rows, one snapshot, 658,543,732 bytes as downloaded (selected columns only); permit type, status, dates, building number | Oct 18, 2026 |
| Primary Land Use Tax Lot Output (PLUTO, the city's tax-lot file) release 26v2, dataset `64uk-42ks` (https://data.cityofnewyork.us/d/64uk-42ks), Department of City Planning | 858,284 tax lots, 81,989,193 bytes as downloaded (selected columns only); only owner category and number of floors were used | Oct 18, 2026 |

Sizes are from `data/raw/SOURCES.md` sections 3 to 6.

**Terms of use.** None of these datasets lists a license. NYC's Open Data Law (Administrative Code 23-502(d), https://intro.nyc/local-laws/2012-11 and https://intro.nyc/local-laws/2017-251, read Oct 17, 2026) allows reuse as long as the source, version and changes are stated. The datasets are provided without warranty, so no figure here is an official DOB or DCP statistic. Downloads and file hashes are logged in `data/raw/SOURCES.md`.

**Privacy.** The raw facade file contains owner and inspector names, business names, addresses and a free-text comments column. These were dropped in the first processing step (`src/process_facades.py`) and never used. From PLUTO, only the owner category was used, never a name.

All results here are "aggregated and charted by us" from those datasets.

## 4. Pre-registered method

### 4.1 What was locked, and when
The plan (`PREREG.md`) was locked on Oct 17, 2026 (tag `prereg-locked`, commit 0140a58), before any shed-permit data was opened and before any repair duration was computed. The analysis code was frozen on Oct 18, 2026 (tag `gate2-code-frozen`, commit eb5c6dc). The runner that produced these results was frozen the same day (tag `gate2-run-frozen`, commit 87759a8) and was not edited before the real run on Oct 22, 2026. The Family 1 results commit is 38381d9. Before the real run, the code was tested on simulated data only.

### 4.2 Sample
- **Frame:** UNSAFE Initial filings in cycles 8 and 9 filed on or before Dec 31, 2024, one per building and cycle. That is 6,174 filings.
- **Public owners excluded:** lots whose PLUTO owner type is City, mixed City/private, or other public (1,346 filings), because their repairs follow budgets and procurement, not the calendar (Gate 0 note; page numbers UNVERIFIED). That leaves 4,828 filings for the all-filings test. Fully tax-exempt lots (698) stay in, marked with an indicator (a yes/no column the model controls for).
- **Unmatched lots:** 103 of the 6,174 did not match PLUTO. They stay in with an indicator.
- **Carried over:** 3,708 filings were rated SWARMP or UNSAFE in the prior cycle. They stay in, flagged.
- **Early filers (used in C6):** filed 181 or more days before their own deadline. 931 filings after the public-owner exclusion.

### 4.3 Outcome
The event is the first Amended filing in the same building and cycle, dated on or after the UNSAFE filing and rated SAFE or SWARMP: the engineer's amended report recording the condition as repaired. Time is counted in 30-day steps, so three steps fit inside DOB's 90-day repair clock. A filing is **censored** (its clock stops without an event, because we cannot see further) on Apr 16, 2025, the day before five shed and facade bills were signed, or at the building's next-cycle Initial filing, whichever comes first. A cycle enters only if at least 50% of its filings have a clearing filing at any date. Both cycles passed (78.2% overall).

### 4.4 Exposure
Workload on the filing date = UNSAFE Initial filings citywide in the 90 days ending that day, divided by 400. One wave unit (400) is about how far a typical deadline wave sits above normal: the median 90-day count on Mar 1 in the six deadline years was about 478, against a median of 106 over all days (`PREREG.md` section 6.2).

### 4.5 Model and tests
- **Model:** a discrete-time hazard model (a cloglog regression fitted with the `statsmodels` GLM tool; it estimates hazard ratios when time is counted in steps). M5 uses all filings. M6 uses early filers only.
- **Controls** (things held fixed so they are not mistaken for workload): filing timing relative to the deadline, deadline group, cycle, borough, stories (PLUTO bands), wall material, the carried-over, tax-exempt and no-PLUTO-match indicators, year and month-of-year, time since filing, and time-varying COVID and policy-step indicators.
- **Confirmatory tests:** C5 (workload, all filings, model M5) and C6 (workload, early filers, model M6). A Holm correction (a standard way to keep the chance of a false alarm at 5% across several tests) is applied within this family of two tests.
- **Effect size bands:** "no meaningful effect" if the whole 95% interval is inside 0.80 to 1.25; "meaningful" at 0.80 or lower, or 1.25 or higher; otherwise "inconclusive."
- **Placebos** (tests where the method should find nothing): PL1 (quiet months of deadline years, expected near 1) and PL2 (workload in the 90 days *after* the filing, expected near 1).
- **Stop rules and the separability rule** (all checked on counts before any model was fit): minimum numbers of filings, events and quarters; and each of four corner cells (early or late filer, crossed with quiet or busy workload) needs at least 50 filings and 20 events. Without enough early filers in busy times and late filers in quiet times, workload could not be told apart from filing timing.
- **Variants:** V1 to V13, each changing one thing at a time. They report estimates and intervals only, with no significance claims.

### 4.6 Changes after the lock (deviations D1 to D4)
A **deviation** is any change to a locked rule, written down with its date. All four were made before any real analysis. Only D3 and D4 touch Family 1.

- **D1 (Oct 17):** which shed-permit branch wins when two apply (Branch C first, then A, then B). Shed test only.
- **D2 (Oct 18):** what counts as a visible permit renewal (overlaps and early renewals count). Shed test only.
- **D3 (Oct 18):** small implementation choices where the plan was silent, accepted as written in the frozen code. In Family 1 these include: a filing keeps only fully observed 30-day steps (an event in a partly observed step counts as censoring); indicators are evaluated at each step's first day; and the workload window includes the filing day.
- **D4 (Oct 18):** the confirmatory error bars use a **delete-one-quarter jackknife** (drop one calendar quarter at a time, refit, and measure how much the answer moves; t distribution with K - 1 degrees of freedom, where K is the number of quarters), not the quarter-clustered estimator written in section 7.4 of the plan. The reason: a simulation (`writeup/gate2-calibration.md`; simulated data only, apart from the real daily count of UNSAFE filings, which sets how bumpy the simulated workload is) showed that the pre-registered 95% interval contained the true value only 90.2% of the time. A 95% interval should do so 95% of the time, so the original intervals were too narrow, meaning overconfident. The jackknife covered the true value 96.5% of the time. The decision rule for this switch was written before the run, but its wording did not say whether "its coverage" meant pooled across the simulation or per simulation cell; the stricter, per-cell reading was taken. Jackknife standard errors were on average 1.34 times the pre-registered ones, so D4 makes intervals wider and a clean null harder to reach, not easier. The pre-registered estimator is still reported, as variant V12, and a wild cluster bootstrap-t as V13.

## 5. Gates before any model was fit (counts only)

| Item | Value |
|---|---|
| Frame before public-owner exclusion | 6,174 |
| Matched to PLUTO / not matched | 6,071 / 103 |
| Public-owner lots excluded | 1,346 |
| Filings in C5 / events / quarters | 4,828 / 3,207 / 40 |
| Filings in C6 (early filers) / events / quarters | 931 / 722 / 30 |
| Clearing filing available, overall / early filers | 0.782 / 0.839 |
| By cycle: cycle 8 / cycle 9 | 0.840 / 0.738 |
| Quiet cut-off (40th percentile of workload) / busy cut-off (70th) | 0.362 / 0.927 |
| Residual spread of workload after year and month / also after filing timing / ratio | 0.309 / 0.307 / 0.995 |

Corner cells (filings / events; each needs 50 and 20): Early-quiet 649/499, Early-busy 82/53, Late-quiet 996/562, Late-busy 1,369/861. All passed, so workload could be told apart from filing timing, and both tests ran. The last table row says the same thing another way: knowing a filing's timing removes almost none of the variation in workload (ratio 0.995). Source: `writeup/gate2-family1-results.md` sections 1 and 2.

## 6. Results

Hazard ratio (HR) per wave unit of workload. Below 1 means repairs clear more slowly when the city is busy. Intervals are 95%, delete-one-quarter jackknife (D4). Source: `writeup/gate2-family1-results.md` section 3; `figures/gate2_family1_confirmatory.csv`.

| Test | Sample | Quarters | Events | HR (95% interval) | p | Holm | Reading |
|---|---|---|---|---|---|---|---|
| C5 | all filings | 40 | 3,207 | 0.991 (0.856 to 1.148) | 0.9033 | not significant (threshold 0.050) | no meaningful effect |
| C6 | early filers | 30 | 722 | 1.235 (0.797 to 1.914) | 0.3322 | not significant (threshold 0.025) | inconclusive |

**In words.** For all filings, the data fit anything from a chance of clearing about 14% lower per step to about 15% higher per step when workload rises by one wave unit. The 0.80 line (the pre-registered "meaningful slowdown") is outside the interval, so a slowdown that big is ruled out. For early filers, the interval runs from 0.797 to 1.914: too wide to rule a slowdown in or out. The estimate above 1 is not evidence that repairs go faster.

**In real units.** Of the 4,828 filings in C5, 3,207 (66%) reached a repair-clearance filing before follow-up ended. If the hazard is steady over time, waiting time scales roughly with 1 / HR (the same rule `PREREG.md` section 7.5 uses to turn HR 0.80 into "about 25% longer"). So C5's interval means one extra wave unit changes the wait by somewhere between about 13% shorter (1/1.148) and about 17% longer (1/0.856), best estimate under 1%. Against DOB's 90-day repair clock, 17% would be about 15 days. This is an illustration, not a measured number: the median wait in days was not computed in the frozen run, and getting it would need a new run.

**Placebos** (on M5; source: results file section 3). PL1, quiet months of deadline years: HR 0.944 (0.660 to 1.350). PL2, workload in the 90 days after filing: HR 0.988 (0.672 to 1.451). Both intervals include 1, as expected, and the PL1 warning did not trigger.

**The pre-registered reading (`PREREG.md` section 8), applied mechanically.** C5 reads "not slowed" and C6 reads "inconclusive." That maps to: "No overall slowdown; the early-filer check is too small to add anything." The stronger pre-registered sentence, "the calendar creates filing waves, not repair delays," needs both tests to sit inside 0.80 to 1.25. C6 does not, so that sentence is **not earned** and is not claimed.

### 6.1 Variants (estimates and intervals only; `figures/gate2_family1_variants.csv`)
- **C5:** every variant except two gives a point estimate between 0.962 and 1.010. The two exceptions: V4 (workload re-measured at each step instead of fixed at the filing date), 0.899 (0.806 to 1.003), the one variant leaning toward a slowdown, with a lower bound just above the 0.80 line; and V8 (a calendar rule instead of measured workload), 1.090 (0.614 to 1.934), very wide.
- **Pre-registered estimator (V12):** C5 0.991 (0.863 to 1.138); C6 1.235 (0.908 to 1.680).
- **C6:** variants run from 1.073 to 1.483, all with intervals that include 1.
- **Bootstrap (V13):** the C5 lower bound printed "nan" (no number). This is a limit of the runner's 21-point search grid (it never crossed p = 0.05 on the low side within 3.5 standard errors), not a finding. The upper bound was 1.130. Fixing it would need a new file, not an edit of the frozen runner.
- **Automatic robustness label:** "fragile" for both C5 and C6. The label requires the interval to exclude 1, so for a null result it is automatic and does not mean the result is unreliable.

### 6.2 Exploratory items (no claims; results file section 5)
- Crude C5 without filing-timing terms (E5): 0.992 (0.866 to 1.137), the same as the adjusted 0.991. So the late-filer trap is not visible in this sample.
- Filing-timing penalty in the quiet band (E3), last-minute filers: 1.535 (0.987 to 2.388).
- Public-owned lots alone (E7): 1.735 (0.959 to 3.139).
- Carried-over filings (E9): 0.956 (0.820 to 1.114); not carried over: 1.079 (0.829 to 1.404).
- Workload from the building's own deadline group versus the other two groups (E10): 0.975 (0.847 to 1.122) versus 1.077 (0.780 to 1.487).

No estimate in this subsection is a test, and none changes the headline.

## 7. Limitations

1. **About 40 independent periods.** Workload is a citywide calendar number: every filing on the same day shares it. So the comparison rests on about 11 years and 40 calendar quarters (30 for early filers), however many filings there are. Thousands of events do not add independent years. The intervals are wide by design.
2. **Wider error bars than first planned.** The simulation showed the pre-registered intervals were too narrow (D4), so the jackknife was used, at a known cost in power (standard errors on average 1.34 times larger; the early-filer test lost power in simulation). The choice between two readings of the decision rule was a judgment made before the real run.
3. **The early-filer check is inconclusive.** C6 cannot tell a shared bottleneck from slow last-minute owners, and it was never expected to prove a null (`PREREG.md` section 7.6). So the study does not fully separate H1 from H2.
4. **The headline outcome was switched from sheds to repair clearance before any outcome data was opened.** On Oct 17, 2026, before the lock, the plan was changed because pre-2026 shed permits ran about a year and were auto-renewed, which makes permit expiry a poor stand-in for when a shed came down. The sources are the Mayor's Office release of Apr 17, 2025 and DOB's service notice of Jan 8, 2026 (`PREREG.md` section 1). Jayden was not asked beforehand; Claude made that call and flagged it to him afterward. A reader may fairly ask whether the switch was a way to get a cleaner answer. The record shows it was based on shed-permit term lengths from public notices, made before any repair duration or shed-permit row had been seen. (Facade filing counts had been seen; see point 5.)
5. **Gate 1 was exploratory and ran before pre-registration.** The deadline-month shares in section 2 were seen first, and several design choices were informed by facade counts (never by repair durations): measured workload instead of a calendar rule, the 90-day look-back, the filing-timing cut-offs, and setting "busy" at the top 30% of workload instead of 20%. `PREREG.md` section 1 lists exactly what was looked at.
6. **The outcome is a filing date.** It is the date of the engineer's amended report, not the day repairs finished, and not DOB's acceptance date (UNVERIFIED that filing implies acceptance). Another 467 filings in the full UNSAFE frame show a cleared status with no clearing filing. They count as censored, which makes repairs look slower across the board. Variant V5 drops them.
7. **Workload is not contractor capacity.** The exposure counts UNSAFE filings. Contractors, engineers and permit sign-offs are not observed, and a null result for workload is not evidence that no bottleneck exists in some other form.
8. **Public owners removed.** The exclusion removed 1,346 of 6,174 filings (about 22%), more than the plan assumed (`WORKLOG.md`, Oct 18). That lowers power. Public lots looked at alone (E7) gave an estimate of 1.735 with a wide interval; it is exploratory only.
9. **Time frame.** Follow-up ends Apr 16, 2025, before the 2025 shed and facade laws, and cycle 10 is not in the sample. The results say nothing about repairs under the new rules. The planned live replication around Group A's Feb 21, 2027 deadline (E6) is a later job and has not been done.
10. **Deadline group is assumed close to random with respect to building traits.** This is untested (UNVERIFIED).
11. **First look.** Oct 22, 2026 was the first time repair durations were seen. Any further rule change is a logged deviation.
12. **No safety judgments.** UNSAFE and SAFE are ratings on filings. No result is a statement about the safety of any building, owner or inspector, and nothing is reported at building level.

## 8. Shed-permit test (Family 2, secondary)

**Status.** Run on Oct 22, 2026, after Family 1, with the same frozen runner (`gate2-run-frozen`, 87759a8), on Jayden's typed go-ahead (`WORKLOG.md`, Oct 22 entry). The plan calls this the weaker evidence and requires it to be reported next to Family 1. Every number in this section is from `writeup/gate2-family2-results.md` unless another source is named. This section was added after the rest of the draft, after reading that file.

### 8.1 Data and design
- **Data:** DOB NOW approved permits (`rbx6-tga4`, 1,016,520 rows, pulled Oct 18, 2026 at 04:43 UTC) and the older DOB Permit Issuance file (`ipu4-2q9a`, 3,990,985 rows, pulled Oct 18, 2026 at 04:53 UTC). Only permit type, status, date and building-number fields were downloaded; no name or address columns (`data/raw/SOURCES.md` sections 5 and 6). The shed pull date used is Oct 18, 2026. Neither dataset lists a license; reuse terms are as in section 3.
- **Which rows are sheds:** DOB NOW work type "Sidewalk Shed" and legacy permit subtype "SH," chosen from lists of category values only. That these are the only sidewalk-shed codes is UNVERIFIED (`PREREG.md` section 11).
- **Cleaning** (`WORKLOG.md`, Oct 18): 106,941 DOB NOW and 172,480 legacy shed rows kept; 0.03% and 2.87% dropped for unusable dates. About 2.2% of legacy dates are in a second text format that the plan's single stated format cannot read. Those rows were dropped and counted, as the plan says. Pooling both files gave 279,420 distinct rows, of which 125,016 start between Feb 21, 2015 and Dec 31, 2025.
- **Structure check, before any linking** (Oct 18): 7.57% of permit terms are 120 days or less, the median term is 365 days, and renewal visibility (how often a renewal shows up as its own row) is 14.85% under the plan's literal wording, or 46.24% when overlaps are included (deviation D2). That selects **Branch B** of the plan: exposure is the 90-day workload ending on each permit's expiry date, and the plan says up front that annual terms blur removal timing, so only very large effects can be seen.
- **Link rule:** permits at one building are chained into a **spell** (one continuous stretch of shed permits, allowing gaps of up to 30 days). A spell is linked to an UNSAFE filing if it starts between 90 days before and 180 days after the filing. Filings whose shed was already standing 90 days before are left out of the main analysis. Each permit expiry is a **decision point**: the spell is either "renewed" or "ended" (the last expiry). Filings run to Dec 31, 2025, cycles 8 to 10. Public-owner lots are excluded as in Family 1. Deviations D1 (which branch wins when two apply) and D2 belong to this family.
- **Model and tests:** the same kind of discrete hazard model as Family 1, jackknife by quarter of expiry (D4), Holm over the four tests. C1 all linked sheds; C2 early filers; C3 workload from other groups' filings; C4 sheds started December to February. The hazard here is the chance that a shed ends at a decision point, so below 1 means sheds last longer when the city is busy.

### 8.2 Gates (counts only)

| Item | Value |
|---|---|
| UNSAFE frame (cycles 8 to 10, filed to Dec 31, 2025, after public-owner exclusion) | 5,134 |
| Left out because a shed was already standing 90 days before the filing | 2,107 (41%) |
| Candidates / lost a spell to a closer filing / linked | 2,454 / 2 / 2,452 |
| Linked share, overall | 47.8% |
| Linked share by filing timing: Early / Middle / Last-minute / Past-deadline | 41.7% / 50.8% / 50.1% / 48.5% |
| Ended events / quarters | 1,762 / 38 |
| Early-filer ended events (C2) / events at top-30% other-group workload (C3) | 357 / 559 |
| Corner cells (filings / events): Early-quiet, Early-busy, Late-quiet, Late-busy | 586/191, 290/88, 1,660/500, 1,482/431 |

All four corner cells passed, and C1 to C4 were allowed to run.

**Sanity count.** 7,932 shed spells were standing on Aug 17, 2026, against 7,427 permitted sheds in the Mayor's Office release of Aug 20, 2026 (https://www.nyc.gov/mayors-office/news/2026/08/mamdani-administration-taking-down-sidewalk-sheds-and-improving-, read Oct 17, 2026). Ours is about 7% higher. The release's counting basis is UNVERIFIED, and the cause of the gap is unknown (UNVERIFIED). One possibility, not checked, is that our spells overcount sheds that are no longer up.

### 8.3 Confirmatory results

Jackknife by quarter of expiry, t on K - 1 degrees of freedom (D4). Source: results file, "Confirmatory tests."

| Test | HR (95% interval) | p | Holm | Reading under the plan's size rule (section 7.5) |
|---|---|---|---|---|
| C1 all linked sheds | 0.971 (0.748 to 1.259) | 0.8175 | not significant | inconclusive (lower end below 0.80, upper end above 1.25) |
| C2 early filers | 0.755 (0.396 to 1.439) | 0.3833 | not significant | inconclusive (very wide) |
| C3 other groups' workload | 0.948 (0.699 to 1.285) | 0.7235 | not significant | inconclusive |
| C4 sheds started Dec to Feb | 1.114 (0.959 to 1.294) | 0.1543 | not significant | inconclusive |

The "reading" column was filled in by Claude while drafting this report, by applying `PREREG.md` section 7.5 to the printed intervals; the results file does not print it. (The code session's log makes the same reading for C1.)

**In words.** No test was significant. For C1, the data fit anything from sheds ending about 25% less often per decision point to about 26% more often when workload rises by one wave unit. A 20% slowdown (0.80) is inside that range, so, unlike Family 1, the shed data **cannot rule out a 20% to 25% slowdown.** For C4, a hazard ratio below 1 would mean December-to-February sheds last longer. The estimate is above 1 and the interval includes 1, so there is no sign of that, but the range is too wide to rule it out.

**Placebos** (results file): PL1 0.915 (0.666 to 1.256); PL2 1.035 (0.661 to 1.620). PL1's interval includes 1, so by the plan's rule (section 7.8) no warning applies. That reading is Claude's; the results file does not print a warning line.

### 8.4 Variants for C1 (estimates and intervals only)
- Point estimates run from 0.851 (S7, drop 2020 and 2021 decision points: 0.851 (0.573 to 1.264)) to 1.111 (S14, add sheds linked to SWARMP filings: 1.111 (0.879 to 1.405)). All of those intervals include 1.
- One outlier: S11, only decision points with terms of 120 days or less, 1.426 (0.597 to 3.406) on 170 events.
- Pre-registered estimator (S21): 0.971 (0.786 to 1.199). Wild cluster bootstrap-t (S22): 0.971 (0.729 to 1.219).
- Term-average exposure instead of the 90 days before expiry (S20): 0.998 (0.499 to 1.997). Calendar rule instead of measured workload (S12): 1.034 (0.547 to 1.954). Including filings whose shed was already standing (S13): 1.063 (0.883 to 1.281) on 3,137 events.
- The estimates that lean below 1 (S1 0.872, S7 0.851, S9 0.888, S17 0.903) all have intervals that include 1. The plan warned that COVID-era permit terms could push results toward a false positive, which is why S7 and S19 (0.934 (0.666 to 1.310)) are read next to C1.

### 8.5 Why this is weaker evidence
1. **Removal dates are approximate.** Before 2026, permits ran about a year and were auto-renewed, per the Mayor's Office release of Apr 17, 2025 and DOB's notice of Jan 8, 2026. The last expiry stands in for removal and is probably late by up to one permit term. The plan expects this to push results toward "no effect" (`PREREG.md` section 4.4), so a null here is weak evidence. The plan's rough guess that annual terms dilute a true effect two to four times is UNVERIFIED.
2. **41% of the frame was dropped** because a shed was already standing before the filing. Those sheds are left out of the main analysis (variant S13 includes them).
3. **Only 47.8% of filings linked** to a shed, and fewer early filers (41.7%) than others. A link is a matching rule, not proof that the filing caused the shed. Many sheds are not from facade filings at all.
4. **Our shed count does not match the city's** (7,932 against 7,427), and the cause is unknown (UNVERIFIED).
5. **Fewer, noisier clusters** (38 quarters) and the same shared-calendar problem as Family 1 (section 7, point 1).
6. **Family 1 and Family 2 do not disagree.** Neither finds a workload slowdown. Family 1 is far more precise, and the headline follows Family 1, as the plan requires.

## 9. Conclusion

In 4,828 repair-clearance records from cycles 8 and 9, a busier city (more UNSAFE filings in the last 90 days) was not linked to slower repair clearance: 0.991 per wave unit (0.856 to 1.148). For this pooled sample, that rules out a slowdown bigger than about 20%, the size the plan called meaningful. The shed-permit test points the same way (0.971 per wave unit) but is far less precise. It is inconclusive and cannot rule out a 20% to 25% slowdown, because pre-2026 permit terms blur when sheds came down. Neither family can say whether early filers behave the same way, so the study cannot yet separate a shared bottleneck from owner behavior. What would settle more: the Feb 2027 deadline wave as a live replication (E6). Shed permits now last 90 days, which should make removal dates sharper (a guess, UNVERIFIED).

**Who could use this.** The intended readers are the Department of Buildings staff who write the FISP rules and the City Council members who oversee them. The decision it bears on is whether the three groups' shared Feb 21 deadline should be spread out to protect repair times. On this evidence, repair clearance gives no reason to do so; the shed question stays open. Anyone can rerun it: it needs only the public files in section 3, and the frozen runner, which took 52 seconds on the machine used (section 10), and it can be repeated after each deadline wave.

## 10. Reproducibility
- Code: `src/` at tags `gate2-code-frozen` (eb5c6dc) and `gate2-run-frozen` (87759a8). Run command: `.venv/bin/python -I src/gate2_run.py --real --family 1` (needs `data/GO_family1.txt`). Run time was 52 seconds.
- Outputs: `writeup/gate2-family1-results.md`, `figures/gate2_family1_*.csv` (aggregates only).
- Family 2: `.venv/bin/python -I src/gate2_run.py --real --family 2` (needs `data/GO_family2.txt`); outputs `writeup/gate2-family2-results.md`, `figures/gate2_family2_*.csv`.
- Plan and changes: `PREREG.md` (locked at 0140a58; deviations D1 to D4 at the end); log: `WORKLOG.md`.
- Commit IDs and tags in this report (0140a58, eb5c6dc, 87759a8, 38381d9) refer to the authors' private working repository. This public repository is a clean single-commit copy, so those IDs do not exist here; `README.md` lists the SHA-256 of the PREREG text as locked.
- Raw data are not in the repository. They can be re-downloaded by code (`src/download_xubg_57si.py`, `src/download_open_data.py`), and file hashes are in `data/raw/SOURCES.md`.

---
Who did what: see "Acknowledgments and AI use" in the README. AI tools used: Claude Sonnet 5.5 and Claude Opus 5.5 (Anthropic), run in Claude Code, Oct 16 to Nov 15, 2026, for code, analysis and writing. No teacher, mentor or other adult helped with this work; all help came from the AI tools named above.
