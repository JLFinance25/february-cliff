# Work log

A short record of who did what and when. Claude (AI) drafted the code, analysis and write-ups; Jayden Ling directed the project and approved the steps marked below.

## 2026-10-16
- Claude ran an exploratory test (Gate 1) on NYC Open Data file `xubg-57si`, using summary counts only, nothing saved. In Cycle 9, 33% to 37% of each deadline group's initial filings and 18% to 23% of its inspections fell in the deadline month.
- This was run before any pre-registration, so it is exploratory. The write-up must say so. Script: `src/spike_bunching_2026-10-16.py`.

## 2026-10-17 (project start and data)
- Jayden decided to make this a project.
- Claude created the project files and a private repo, and scanned the files to be committed for personal details (no real hits).
- Terms check (Claude): the NYC Open Data Law (Local Law 11 of 2012, amended by Local Law 251 of 2017) lets public datasets be reused with one condition: name the source, the version and any changes. Two gaps are UNVERIFIED: the live code library could not be opened to rule out a later amendment, and the old portal terms page returns 404. Claude chose to proceed. Whether to email the Open Data Team to confirm is Jayden's call and had not been decided.
- Claude downloaded all 87,455 rows of `xubg-57si` through the free API (no key). `src/process_facades.py` keeps an allowlist of 19 columns and drops every owner and inspector field, the street address and the free-text comments at read time. Claude checked afterwards that none of the dropped columns is in the output.
- Claude made "February cliff" charts for cycles 7 to 10 (`src/february_cliff.py`). They are descriptive, with no test. Claude checked two plotted numbers against a separate live query (both matched), and rechecked the Cycle 9 shares from the processed file (37.0%, 35.5%, 33.1%).
- Gate 0 (Claude): read DOB's December 2025 FISP recommendations report by keyword search plus the passages found, not page by page. Its 11 recommendations were not found to address the sub-cycle calendar, filing timing or contractor capacity. Claude also installed survival-analysis add-ons at Jayden's typed request.

## 2026-10-17 (pre-registration)
- Claude drafted `PREREG.md` with the shed link rule, the exposure definition, the tests and what each result would mean. At that point Claude had looked only at the column names of the shed files, not at any shed rows.
- Critical pass (Claude): checked the draft's assumptions against facade data already seen. It found that the "no-wave" control Februaries were not wave-free, that policy changes needed step terms, and that exposure and filing timing were nearly the same variable. Claude added a measured-workload exposure, an identifiability rule and two placebo checks.
- Headline switch: Claude found that before 2026 shed permits ran about a year with automatic renewal, so a permit-based design could not show when a shed came down. Claude decided to make a facade-file-only repair-clearance outcome the primary family and keep the shed tests as a second family. This was Claude's call, made before any shed row or repair duration was seen. Jayden was not asked beforehand.
- A later review also changed the standard errors to cluster by calendar quarter instead of tax block, because workload is a citywide date variable.
- Locked at commit 0140a58 (tag `prereg-locked`). The file records that Jayden had not yet reviewed it.

## 2026-10-17 to 2026-10-18 (Gate 2 code, simulated checks, freeze)
- Claude wrote the Gate 2 linking and model code and 44 unit tests, and checked them on simulated data only. No repair durations were computed from the real facade file. The only real-data contact was the workload series, which reproduced the counts already in the PREREG.
- Simulated checks: a planted hazard ratio of 0.75 was recovered, and the hand-written fit and statsmodels agreed. Twelve deliberate code breaks were each caught by the tests. An independent read by a helper found one real bug (month-of-year controls were never created), which was fixed.
- Code frozen at tag `gate2-code-frozen` (eb5c6dc). Claude ran the 44 tests again and all passed.
- Deviations logged in `PREREG.md`, all by Claude: D1 (Oct 17, branch order for the permit structure check was ambiguous, so check C first, then A, then B); D2 (Oct 18, renewal visibility counts overlaps and early renewals); D3 (Oct 18, small code implementation choices accepted); D4 (Oct 18, confirmatory standard errors switched to a delete-one-quarter jackknife).
- D4 reason: 2,700 simulated replicates the pre-registered interval covered the truth 90.2% of the time against 95% intended, while the jackknife covered 96.5%. Cost: jackknife errors are about 1.34 times larger.

## 2026-10-18 (downloads)
- After the code freeze, Claude downloaded PLUTO (`64uk-42ks`, 858,284 rows), DOB NOW permits (`rbx6-tga4`, 1,016,520 rows) and the legacy permit file (`ipu4-2q9a`, 3,990,985 rows) through the free API, requesting only allowlisted columns. No names, addresses or phone numbers were requested.
- Claude checked that the freeze tag came before the first download file, that the saved file hashes matched the log, and that the row counts matched. No rows were read at this stage.

## 2026-10-18 (cleaning, structure check, runner)
- Cleaning, DOB NOW: 106,941 shed rows kept, 0.03% dropped for unusable dates. Legacy: 172,480 kept, 2.87% dropped. About 2.2% of legacy dates were in a second text format that the single stated format cannot read. They were dropped and counted, as the PREREG says; parsing both formats was not done. Pooled: 279,420 rows, 125,016 in the analysis window (starts Feb 21, 2015 to Dec 31, 2025).
- Claude chose the shed codes from DOB's own permit-code list: "Sidewalk Shed" in DOB NOW, and subtype "SH" in the legacy file.
- Structure check: 7.57% of permit terms were 120 days or less, the median term was 365 days, and renewal visibility was 14.85% (literal) or 46.24% (D2). Both numbers select Branch B, so annual terms blur removal timing and the shed family can see only very large effects.
- Public-owner exclusion: this removes about 22% of the Family 1 frame (about 4,828 filings left), more than the plan assumed. Statistical power is therefore lower than the PREREG says (UNVERIFIED until the run).
- Runner frozen at tag `gate2-run-frozen` (87759a8), with 16 tests on simulated data. Claude ran both test suites and read the whole runner.
- Claude chose to hold the first real run, because Jayden had not read the PREREG and the headline had been changed without asking him. Claude wrote a one-page plain-English guide so he could review it quickly.

## 2026-10-22 (the two real runs)
- Family 1 (repair clearance). Jayden wrote in chat that he had read the plain-English guide and said to run it. Claude ran the frozen runner; no frozen file was edited. All gates passed. Per wave unit: C5 (all filings) HR 0.991 (0.856 to 1.148), p 0.90; C6 (early filers) HR 1.235 (0.797 to 1.914), p 0.33. Neither is significant after Holm correction. The mechanical reading is no meaningful overall slowdown and an inconclusive early-filer check.
- Family 2 (sheds). Jayden wrote in chat to run the shed test. Claude ran the frozen runner; no frozen file was edited. 2,452 filings were linked (47.8%) with 1,762 ended events. C1 HR 0.971 (0.748 to 1.259); C2 0.755 (0.396 to 1.439); C3 0.948 (0.699 to 1.285); C4 1.114 (0.959 to 1.294). None is significant after Holm correction. C1's upper end sits just above 1.25, so it is inconclusive, not "no meaningful effect". The "inconclusive" labels are Claude's reading of PREREG 7.5, not runner output.
- Cautions (Claude): 41% of the Family 2 frame was dropped because a shed was already standing, so a null there is weak evidence. The runner's bootstrap interval had an unresolved lower bound in Family 1, a limit of its search grid and not a finding. Counted shed spells (7,932) ran 7% above a city press-release figure (7,427); that release's counting basis is UNVERIFIED.
- Jayden has not reviewed the PREREG itself or these results beyond the go-aheads above.

## 2026-10-22 (report draft)
- Claude wrote a private paper-style draft of the Family 1 result, taking its numbers only from the runner output. The first version left the shed section unfilled because Claude had been told the shed run had not happened; it had, so Claude then filled that section from the Family 2 output.
- The draft carries an AI-use line. Jayden has not read the draft and has not approved it.

## 2026-10-24 (polished report and public copy)
- Claude (Opus 5.5) did a clarity pass on the report draft and re-checked its numbers against the results files. No number, test or finding was changed.
- Claude (Sonnet 5.5) assembled this public copy: report, PREREG, frozen code, aggregated results only and this log. It re-checked 30 report numbers against the results files and scanned the files and the commit for personal data. The edits it made to copied files are listed in `README.md`.
- Jayden Ling has not yet read the report or approved publishing it. This line is to be updated when he does.
