# PREREG: Gate 2, "Does a deadline wave slow down repairs and shed removal?"

**STATUS: LOCKED on Oct 17, 2026** (git tag `prereg-locked`). From here on, any change to a rule is a deviation (section 9.1), written in this file and the report, never made quietly.

| | |
|---|---|
| Drafted by | Claude (Anthropic AI). First drafted on Sonnet 5.5 (`claude-sonnet-5-5`); critical pass and revisions on Opus 5.5 (`claude-opus-5-5`), at the main session's request |
| Draft dates | Oct 17, 2026 (first draft; Gate 0 revision; critical-pass revision; two-family revision) |
| Lock date | Oct 17, 2026 (locked by Claude, Opus 5.5, on the main session's instruction, before any shed data or repair duration was seen) |
| Seen or approved by Jayden | **Not yet reviewed by Jayden.** Date seen: *(blank)*. Date approved: *(blank)* |
| Gate 0 (DOB's own Dec 2025 FISP study) | **Recorded** in `writeup/gate0-dob-fisp-study.md` (read Oct 17, 2026 by another Claude session, commit `2eacf96`). A keyword search of the study's full text, plus reading the passages found (not every page), turned up nothing on deadline bunching, filing timing or contractor capacity. That is "not found by that search," not "proven absent." Its two leads (carried-over UNSAFE filings, public owners) are built in. All revisions so far were made before lock and before any shed data was seen, so none is a deviation. |
| AI-use line | Drafted with Claude (AI); directed, checked and approved by Jayden Ling. *(Approval is not yet given. Drop this line's last clause if he rejects the file.)* |

---

## 0. The whole thing in eleven sentences
1. NYC splits buildings into three deadline groups (A, B, C), and each group's facade-inspection window ends on Feb 21 in a different year, so surges of UNSAFE filings, and the repair work they trigger, land on the city in some winters and not others. Cycle ends and a few off-season surges add more.
2. We ask whether repairs, and the sidewalk sheds that wait on them, take longer when the city's repair **workload** is high. Workload means UNSAFE filings citywide in the last 90 days.
3. **Primary evidence (Family 1)** comes from the facade file alone: the time from an UNSAFE filing to the engineer's later filing that records the condition as cleared. It is dated to the day and needs no shed data.
4. **Secondary evidence (Family 2)** comes from shed permits. Before 2026, shed permits ran about a year and were auto-renewed, so a permit's expiry may be months after the shed came down. That is the likely case, and it makes the shed outcome the **weaker** evidence. A structure check right after lock decides whether Family 2 can be run at all (section 4.6).
5. The obvious trap: owners who file at the last minute may just be slow owners, which would make busy periods look harmful even if contractors have plenty of capacity.
6. The **falsification arm** is the way out. If the cause is a shared bottleneck, buildings that filed *early* must also slow down when the city is busy. In Family 1 that test (C6) has real data, about 1,350 early filings; in Family 2 its counterpart (C2) is too weak to expect much.
7. A pre-registered identifiability rule (7.7) says when workload cannot be told apart from filing timing. The headline is then "cannot separate," not a result.
8. The workload contrast rests on about 11 years and about 40 calendar quarters of variation, however many buildings and events there are. Standard errors are therefore clustered by quarter (7.4).
9. Shed laws signed on Apr 17, 2025 aim directly at repair speed, so Family 1 stops following filings on Apr 16, 2025. Family 2 stops on Dec 31, 2025.
10. Placebo tests check that the method finds nothing where nothing should be.
11. Everything below is fixed *before* anyone opens shed-permit data, and before anyone computes repair durations from the facade file, so the results cannot be tuned. (For the facade outcome, only the *order* of the filing date and the clearing date was checked; no gap sizes and no time-to-clearance figures were computed.)

---

## 1. What was already seen before locking, and what was not

### Exactly which facade data has been looked at, and by whom
So a reader can check that no repair durations were seen:
- **Oct 16 exploratory test** (`src/spike_bunching_2026-10-16.py`, live API, nothing saved): monthly counts of **Initial** filings by `filing_date`, by group, cycles 8 and 9. The deadline-month shares of inspections and of UNSAFE ratings in `PLAN.md`'s Gate 1 table came from summary queries the same day; those queries were not kept in the script (UNVERIFIED exactly which).
- **Cliff charts** (`src/february_cliff.py`, cycles 7 to 10): weekly counts of four series, all from **Initial** filings only:
  - Initial filings by `filing_date`;
  - inspections by `field_inspection_completed_date`;
  - Initial filings rated UNSAFE by `filing_date`;
  - Initial filings rated SWARMP by `filing_date`.
  It uses no Subsequent or Amended filings and no status changes over time.
- **Claude, while drafting this file (Oct 17, 2026), all from the processed facade file:**
  - Row counts by cycle × filing type, filing status and current status.
  - Gaps *within one Initial filing*: inspection date to filing date (above), and submission to filing date.
  - Wall-type and borough value lists.
  - The frame, timing and prior-status counts above.
  - Citywide monthly UNSAFE counts, the trailing 90-day workload, its spread, rank cut-offs and corner-cell filing counts.
  - The surge-day breakdowns.
  - The clearance **availability** counts in this section: filing-type × status combinations; whether a clearing filing exists; whether a next-cycle Initial filing exists, and its rating.
  - For clearing filings, only the **order** of the two dates was checked (on or after F; none before; 12 on the same day). The size of any gap was not computed, and no distribution of gaps or of time to clearance was computed.
- **Main session (Oct 17, 2026), counts only.** It looked at no dates or gaps in those rows.
  - Rows by cycle and filing type:
    - Cycle 8: Initial 13,320, Subsequent 442, Amended 2,319, Auto-Generated 5,860.
    - Cycle 9: Initial 13,548, Subsequent 2,892, Amended 2,416, Auto-Generated 11,830.
    - Cycle 10: Initial 2,885, Subsequent 74, Amended 209, Auto-Generated 8.
  - Of 7,025 distinct (BIN, cycle) pairs with an UNSAFE Initial filing in cycles 8 to 10, 6,159 have at least one non-Initial row in the same BIN and cycle. That includes Auto-Generated rows, so it is not a clearance rate.

### Seen (the facade-filings file only)
Source: NYC Open Data "DOB NOW: Safety – Facades Compliance Filings" (`xubg-57si`), pulled Oct 17, 2026 (`data/raw/SOURCES.md`, section 3), or the Oct 16 exploratory test in `PLAN.md`. All counts were computed by Claude on Oct 17, 2026 from `data/processed/facades_clean.parquet` and re-checked against it. Monthly counts include the few rows with no cycle value.
- **The cliff charts.** Weekly filings, inspections, UNSAFE and SWARMP findings for cycles 7 to 10 by group (`figures/february_cliff_summary.csv`, `figures/february_cliff_weekly.csv`, two PNGs). **Gate 1:** in Cycle 9, 33% to 37% of each group's initial filings fell in its deadline month (about 4% if spread evenly); exploratory, run before any pre-registration.
- **The UNSAFE frame** (UNSAFE *Initial* filings, cycles 8 to 10):
  - 3,055, 3,370 and 733 filings (7,158). 3 have no date. 133 repeat a (building, cycle) pair. None lacks a BIN or group.
  - 2,560 tax blocks; 5,631 BINs.
  - Inspection-to-filing gap: median 16 days, 90th percentile 52, 99th percentile 201, 1st percentile −142.
  - 3% have no wall-material entry.
- **Filing timing against own deadline** (7,155 dated):
  - 2,125 Early (181+ days before; 953 of them before their window opened: 332, 281, 340 in cycles 8 to 10)
  - 457 Middle (29 to 180 days before)
  - 2,229 Last-minute (0 to 28 days before)
  - 2,344 Past-deadline
- **Prior-cycle status:** SWARMP 2,828; UNSAFE 1,595; SAFE 2,144; No Report Filed 28; blank 560. So 4,423 (62%) are "carried over" (prior SWARMP or UNSAFE). Among the 2,732 others: 359 Early in-window, 343 before-window, 215 Middle, 850 Last-minute, 965 Past-deadline.
- **Citywide monthly UNSAFE Initial filings:**
  - **Group-deadline Februaries:** 408, 266, 305 (2017 to 2019); 660, 405, 394 (2022 to 2024).
  - **Other Februaries:** 83 (2015), 26 (2016), **230 (2020)**, 25 (2021), 103 (2025), 46 (2026).
  - **Other surges:** Jun 2015, 198 (mostly Jun 29 to 30; DOB's Cycle 7 amnesty ran to Jul 17, 2015, per `WORKLOG.md`); Aug 2016, 155; Oct 2020, 92 (mostly Oct 29 to 31).
  - **Quiet months:** monthly median (Feb 2015 to Sep 2026) 32.5.
  - **Trailing 90-day counts on Mar 1:** 115, 132, 486, 330, 395, **385**, 42, 732, 515, 471, 182 (2015 to 2025). Over all days, Feb 2015 to Dec 2025: median 106, 90th percentile 397.
- **Facts used for Family 1, looked at Oct 17, 2026 (two-family revision).** Only field values, filing-type and status combinations, and availability counts were looked at. **Only the order of each clearing filing's date relative to F was checked. No gap sizes, no distribution of gaps or time to clearance, and no relation between clearance and workload or filing timing were computed or looked at.**
  - **Cycles 8 to 10, filing type × status:** Amended filings are SAFE 3,611, SWARMP 1,332, UNSAFE 1. Subsequent filings are SAFE 780, SWARMP 436, UNSAFE 2,192.
  - **Dates:** every Amended and Subsequent filing has a date.
  - **Clearing filings:** of the 7,155 dated UNSAFE frame filings, 4,724 have an Amended filing in the same (BIN, cycle), dated on or after F, with status SAFE or SWARMP (4,712 strictly later). About 72 more have only a later Subsequent SAFE or SWARMP filing. None has a clearing filing dated before itself; 12 are dated the same day as F; 1 clearing filing has no date.
  - **Clearing-filing share by cycle** (Amended, on or after F, any date): cycle 6 89% (2,409 of 2,717), cycle 7 74% (1,976 of 2,674), cycle 8 72% (2,213 of 3,055), cycle 9 69% (2,310 of 3,367), cycle 10 27% (201 of 733; cycle under way). Older cycles have *more* clearance records, not fewer, so the move into DOB NOW does not appear to have dropped them.
  - **Next cycle's Initial filing:** of the 1,899 cycle 8 and 9 frame filings with no clearing filing, 761 have an Initial filing in the next cycle. 755 of those are rated UNSAFE again, and only 6 SAFE or SWARMP.
  - **Family 1 frame** (6,174 filings, section 3.1): 4,396 (71.2%) have a clearing filing at some date. That is cycle 8, 2,147 of 2,961 (72.5%); cycle 9, 2,249 of 3,213 (70.0%).
  - **Mismatches:** 378 frame filings without a clearing filing have `current_status` SAFE, and 89 have SWARMP (cleared by some route the file does not show as a filing). 244 with a clearing filing are `current_status` UNSAFE again.
- **Exposure only, for power and identifiability.** Workload at the filing date (x at F, section 6.2), among the 6,174 frame filings (cycles 8 and 9, F on or before Dec 31, 2024, one per BIN and cycle, before public-owner exclusion):
  - **Spread:** standard deviation 0.462 raw; 0.293 after removing year and month-of-year averages; 0.292 after also removing filing timing.
  - **Early filers** (1,350): 0.374 raw; 0.267 after year and month.
  - **Rank cut-offs:** the 40th percentile is 0.33 and the 70th percentile 0.84.
  - **Filings per corner cell** (quiet = bottom 40%, busy = top 30%): Early-quiet 864, Early-busy 126, Late-quiet 1,259, Late-busy 1,734.
  - **Permit-family exposure:** the trailing 90-day workload on a calendar day has a standard deviation of 0.259 after year and month averages (Feb 2015 to Dec 2025, COVID months out).
- **Gate 0 notes** (`writeup/gate0-dob-fisp-study.md`): the keyword search found nothing on bunching or capacity. The report says unrepaired SWARMP conditions are reclassified UNSAFE (p. 43), and that public owners' repairs follow budgets and procurement "without any connection to the schedule" (p. 40). Page numbers are that note's.
- **Data dictionaries.** The facade dictionary only says `prior_status`, `filing_status` and `current_status` take the values SAFE, UNSAFE and SWARMP. The PLUTO dictionary (May 2022, 22v1, https://www.nyc.gov/assets/planning/download/pdf/data-maps/open-data/pluto_datadictionary.pdf):
  - `OwnerType` C = City, M = mixed City/private, O = other public, P = private, X = fully tax-exempt (public or a private institution), blank = unknown.
  - `NumFloors` = stories of the tallest building on the lot; 0 means unavailable.

### Consequence for honesty
**The exposure (measured workload), its 90-day look-back, the filing-timing cutoffs, the rank bands, the placebo windows and the definition of the Family 1 outcome were all informed by the facade data.**
- The monthly counts above moved the exposure from a calendar rule to measured workload.
- The corner-cell counts set "busy" at the top 30%, not 20%: at 20% the Early-busy cell had 99 filings.
- None of this came from shed data or from repair durations.

### Not seen
- **Any shed-permit data:** no row, count, sample or date range from `rbx6-tga4` or `ipu4-2q9a`.
- **Repair durations** (any time from an UNSAFE filing to its clearing filing).
- **PLUTO data.**

### Shed datasets: field metadata only
On Oct 17, 2026 I read each dataset's field list via `api/views/<id>.json`, extracting in code only `name`, `fieldName`, `dataTypeName` and `description` (plus the dataset title and description). Cached summary statistics were never read; no rows were requested.
- **`rbx6-tga4`:** has `bin`, `block`, `lot`, `work_type`, `permit_status`, `filing_reason`, `work_permit`, `sequence_number`, and three date fields: `approved_date`, `issued_date`, `expired_date`. Personal and free-text columns (applicant, owner, `job_description`, `estimated_job_costs`) are dropped at read time.
- **`ipu4-2q9a`:** has `bin__`, `permit_type`, `permit_subtype`, `permit_status`, and dates `filing_date`, `issuance_date`, `expiration_date`, all **typed as text**. It covers only permits issued in the older BIS system. Personal columns are dropped at read time.
- **Missing fields:** neither list has a sign-off or removal date (UNVERIFIED that none exists elsewhere).
- **The "sidewalk shed" code is UNVERIFIED.** DOB's code-list PDF (`bisjobstatus.pdf`) returned 404. A search hint suggests "SH."

### Other documents read (Oct 17, 2026)
- **1 RCNY §103-04** (PDF dated Feb 3, 2026), https://www.nyc.gov/assets/buildings/rules/1_RCNY_103-04.pdf:
  1. The engineer must "immediately notify" DOB of an unsafe condition, so sheds can start before the filing.
  2. Unsafe conditions "must be corrected within ninety (90) days from the submission" of the report, extensions possible.
  3. Within two weeks after repairs the engineer must inspect and file an amended report with the revised status.
  4. A shed stays up until an amended report is accepted, unless DOB grants removal permission.
- **Pre-2026 shed permits were annual and auto-renewed:**
  - Apr 17, 2025 Mayor's Office release: the bill "reduces the duration of a sidewalk shed permit from one year to three months" (wording confirmed by the main session).
  - DOB service notice of Jan 8, 2026: permits "will not be automatically renewed," and "All permits issued before February 2, 2026, will expire as they would have prior to the launch."
  - Links are in 6.5.
- **The shed-policy timeline:** section 6.5.

---

## 2. Hypotheses and predictions (each could fail)

**Plain terms.** A *hazard* is the chance something ends in a given step, given it has lasted so far. A *hazard ratio* (HR) compares that chance in two situations: HR 0.80 means 20% less likely to end, so things last longer. One **wave unit** of workload is 400 UNSAFE filings in 90 days, about one deadline wave above normal (6.2).

- **H1, primary: shared bottleneck (workload).** When many repairs are demanded at once, the repair pipeline gets congested, so repairs, and the sheds waiting on them, take longer *for everyone*. "Pipeline" means contractors, but also the engineers who certify repairs and permit sign-offs. This study cannot tell those apart.
- **H2, rival: owner behavior.** Owners who file at the last minute or late are slow for their own reasons (money, boards, lawsuits). There is no capacity limit; busy periods only *look* harmful because late filers crowd into them.
- **Rival 3, cold weather.** The claim that winter slows facade repair is a hypothesis, not a checked fact (UNVERIFIED). Month-of-year effects, off-season surges and C4 address it.

| Test | Family | H1 predicts | H2 predicts |
|---|---|---|---|
| **C5** All filings: workload at filing date vs time to clearance | 1 (primary) | HR below 1; 0.80 or lower per wave unit = meaningful | HR near 1 once filing timing is accounted for |
| **C6** Early filers only: same | 1 (primary) | HR below 1 | HR near 1 |
| C1 All linked sheds: workload vs shed removal | 2 | HR below 1 | HR near 1 |
| C2 Early filers only: same | 2 | HR below 1 | HR near 1 |
| C3 Workload from other groups' filings vs shed removal | 2 | HR below 1 | HR near 1 |
| C4 Sheds started Dec to Feb vs removal (cold weather) | 2 | either | either |
| Filing-timing penalty in quiet periods (exploratory E3) | both | not needed | late filers slow even when quiet |

**How cleanly each test breaks the late-filer link.** C6 and C2 compare early filers with early filers, so they break it cleanly. C6 is the one with enough data to matter (7.6). C3 breaks it only partly. The hypotheses are not exclusive; section 8 covers mixed results.

---

## 3. Family 1: time to repair clearance (facade file only)

### 3.1 Sample
- **Frame:** the Step 1 frame of section 4.1, the same facade rows and rules, including the public-owner exclusion and the carried-over flag, restricted to **F on or before Dec 31, 2024**. Before the public-owner exclusion this is 6,174 filings, all from cycles 8 and 9 (section 1).
- **(c) Which cycles.** Cycles 8 and 9 both enter. The choice was made from availability counts only: 72.5% and 70.0% of their frame filings have a clearing filing at some date. Cycle 10 has no filings before Dec 31, 2024 in the frame.
- **(b) Availability rule**, checked on counts only, on the final frame (after the public-owner exclusion), before any model is fit:
  - A cycle enters only if at least **50%** of its frame filings have a clearing filing at any date.
  - C5 and C6 are run only if at least 50% do overall. For C6, the rule is applied to Early filers.
  - Otherwise they are reported as "not testable."
  - A cycle that fails is dropped. If both fail, Family 1 is not run.
- **Follow-up end:** **Apr 16, 2025**, the day before the five shed and facade bills were signed. One of them (Intro 661-A) penalizes missed facade-repair milestones, aiming straight at this outcome. Its effective date is UNVERIFIED, so follow-up stops before the signing. F stops at Dec 31, 2024 so that every filing has at least about 3.5 months of follow-up.
- **No shed data is used.**

### 3.2 Outcome R
- **The event** is the first filing in the same (BIN, cycle) dated on or after F with `filing_type = "Amended"` and `filing_status` SAFE or SWARMP: the engineer's amended report recording that the unsafe condition was repaired. Its date is its `filing_date` (if blank, `submitted_on`). **R** = that date minus F, in days. A same-day clearing filing gives R = 0.
- **(a) Censoring** (meaning the clock stops with no event, because we cannot see further) happens at the earliest of:
  - Apr 16, 2025 (follow-up end);
  - the date of the BIN's next Initial filing in a *later* cycle.
  There is no separate cut at the cycle's end: DOB labels an Amended filing with the cycle of the report it amends, so a late clearing filing still counts. (UNVERIFIED; only the order of dates was checked, not gaps.)
- **(d) The next cycle's Initial filing is a censoring point, not a clearance.** It records a new inspection, not the date of the repair. In the availability counts only 6 such filings were SAFE or SWARMP, against 755 UNSAFE again (section 1), so this choice cannot move the result.
- **Later re-ratings ignored:** later re-ratings to UNSAFE (244 filings, section 1) do not undo the first clearance.
- **What R measures:** repair work plus up to two weeks for the engineer's inspection plus filing delay (rule text, section 1). DOB's *acceptance* date of the amended report is not in the file (UNVERIFIED that filing implies acceptance).
- **Known blind spot:** 467 filings in the whole UNSAFE frame (fewer in the Family 1 frame) show a cleared `current_status` with no clearing filing in the file. They count as censored (never seen cleared) in the main analysis, which makes repairs look slower *across the board*. Variant V5 drops them.

### 3.3 Steps
- **Rows:** each filing contributes one row per **30-day step** from F (days 0 to 29, 30 to 59, …) until its event or censoring.
- *Why 30 days:* DOB's repair clock is 90 days, so 30-day steps give three steps inside the legal window and three more inside a standard extension. That is enough detail to see the clock without making thousands of near-empty steps.
- Ties within a step are expected and are what the discrete model is built for. V6 uses 14-day steps.

---

## 4. Family 2: shed sample and the shed-to-filing link rule

Code (written and tested on **simulated** data before any shed row or any repair duration is opened, then frozen): `src/gate2_link.py`, `src/gate2_model.py`.

### 4.0 Fixed dates
- **Facade snapshot:** the Oct 17, 2026 pull (hashes in `SOURCES.md`). It will not be re-downloaded.
- **Family 2 end E = Dec 31, 2025.** Decision points with expiry after E are not used. *Why:* the 2026 permit rules start inside Feb to Apr 2026, where year effects cannot absorb them (6.5).
- **Shed pull date D:** logged in `SOURCES.md`. S17 runs to the earlier of D and Oct 16, 2026.

### 4.1 Step by step

**Step 1. UNSAFE frame** (shared with Family 1).
- **Keep:** `filing_type = "Initial"`, `filing_status = "UNSAFE"`, `cycle` in {8, 9, 10}.
- **F** = `filing_date` as a date; if missing, `submitted_on`; if both are missing, drop.
- **Drop:** no BIN; a BIN ending `000000`; no group; F after E.
- **Repeats:** for repeated (BIN, cycle) keep the earliest F (ties: smallest `tr6_no`). BINs are cleaned to 7 digits.
- **Public owners excluded:** PLUTO `OwnerType` C, M or O, joined by borough-block-lot (BBL). Only the category is used, never a name.
  - X gets an indicator.
  - Unmatched lots stay in with a "no PLUTO match" indicator.
  - Public lots are described separately (E7). The PLUTO release and date go in `SOURCES.md`.
- **Carried over** (prior status SWARMP or UNSAFE): kept and flagged. They are 62% of the frame, and what `prior_status` means is undocumented (UNVERIFIED).
- **Cycle 7 excluded:** shorter transition schedule, legacy permits only, a different era.

**Step 2. Shed permits.** One interval [start, end] per row.
- **DOB NOW:** BIN = `bin`; start = `issued_date` (blank: `approved_date`); end = `expired_date`.
- **Legacy:** BIN = `bin__`; start = `issuance_date`; end = `expiration_date`, parsed with one stated format chosen from the *format only*. Unparseable rows are dropped and counted.
- **Keep only sidewalk-shed rows** (DOB NOW `work_type`; legacy `permit_type` or `permit_subtype`). Drop rows with no start or end, end before start, or a `permit_status` meaning the permit never took effect (withdrawn, revoked, cancelled, denied, rejected, disapproved).
- **Duplicates:** collapse identical (BIN, start, end) rows.
- **Data quality:** report if more than 10% of rows are dropped for dates. The rule is not loosened.
- **Code-list step** (after lock, before anything else): print the distinct values of `work_type`, `permit_type`, `permit_subtype`, `permit_status` and `filing_reason`. No counts, dates or BINs. Choose the matching strings and log them in `WORKLOG.md`. This picks strings; it changes no rule.

**Step 3. Spells.** For each BIN, pool both files.
- **Same spell:** a permit joins the spell if it starts no more than **G = 30 days** after the running latest end. Concurrent sheds merge.
- **Spell start** = earliest start. **Spell end** = latest end, an approximate removal date (4.4).

**Step 4. Link.**
- **The linked spell:** for a frame filing (F, BIN b), the earliest spell at b with start S in **[F − 90, F + 180] days**. The look-back covers the inspection-to-filing gap for 98% of the frame.
- **Shed already standing:** if b had a spell standing on F − 90, the filing is excluded (S13 includes it).
- **One filing per spell:** if two filings compete, the spell goes to the closest F (ties: the later one).
- **First spell only.**
- **Report:** the share of the frame with a linked spell, overall and by filing timing.

**Step 5. Decision points.**
- **Rows:** each distinct expiry date e₁ < … < e_k of a linked spell is one row. At e₁ … e_{k−1} the outcome is "renewed" (0).
- **Final row:** at e_k the outcome is "ended" (1) if e_k + G is on or before D; otherwise the row is dropped (censored).
- **End date:** rows with e after E are left out.
- **Term:** each row's term runs from the previous decision point (or spell start) to e.

### 4.2 Plain-English picture
A permit issued in January, renewed in April and July, and nothing after October gives three rows: kept, kept, ended. The model asks whether "ended" was less likely when the city's workload was high.

### 4.3 Family 2 sensitivity variants (one at a time; not tests)
| ID | What changes |
|---|---|
| S1, S2 | Gap G = 0 days; G = 90 days |
| S3, S4 | Link window F − 30 to F + 90; F − 180 to F + 365 |
| S5, S6 | Workload look-back 30 days; 180 days |
| S7 | Drop all decision points in 2020 and 2021 |
| S8 | Keep the Mar to Sep 2020 decision points the main analysis drops |
| S9 | Straight-line year trend instead of year effects |
| S10 | Cluster by month; two-way by block and quarter; by block only (each run separately) |
| S11 | Only decision points whose term was 120 days or shorter |
| S12 | Calendar rule instead of measured workload (6.4) |
| S13 | Include filings whose shed was already standing (decision points from F − 90 on) |
| S14 | Add sheds linked to SWARMP filings, with a rating control |
| S15 | Only filings not carried over (2,732 of 7,155; may fail the stop rule) |
| S16 | Include public-owned lots, with an indicator |
| S17 | End at the earlier of D and Oct 16, 2026, with steps at Jan 26 and Aug 20, 2026 |
| S18 | Drop the policy-step indicators |
| S19 | Drop decision points whose term overlaps Mar 1 to Sep 30, 2020 |
| S20 | (Branch B only) the term-average exposure instead of the 90 days before expiry |

### 4.4 Errors in the end date
- **Size:** the last expiry approximates removal, probably late, by up to one permit term. With annual auto-renewed permits that can be most of a year.
- **Effect:** this blurs the workload contrast and pushes Family 2 toward "no effect." A Family 2 null is weak evidence.
- **Wording:** shed "delays" are always described as "approximate, from permit dates."

### 4.5 Limits of the shed sample
- **Selection and cause:** sheds enter only if a permit starts in the link window, and a link is a matching rule, not proof of cause.
- **Excluded sheds:** sheds already standing are excluded (S13 tests this).
- **Group assignment:** groups are assumed close to random with respect to building traits (untested).
- **Stories:** PLUTO stories are per lot.
- **Sanity check, not a target:** spells standing on Aug 17, 2026 (all BINs) are compared with the 7,427 permitted sheds in the Mayor's Office release of Aug 20, 2026 (read Oct 17, 2026; link in 6.5).

### 4.6 Structure check after lock (outcome-free), with branches fixed now
**When:** right after the code-list step, before any linking.

**Pool:** all shed rows from both files whose start falls Feb 21, 2015 to Dec 31, 2025.

**Compute only these two things:**
1. **Term length** of each row (end minus start): the share of rows at 120 days or less, and the median.
2. **Renewal visibility:** the share of rows that start within 30 days after another shed row *at the same BIN* ends (so renewals appear as separate rows).

No linking to filings, no workload, no outcomes. Results are logged in `WORKLOG.md`. Then exactly one branch applies:

| Branch | Condition | Family 2 design |
|---|---|---|
| **A** | 60% or more of rows have terms of 120 days or less | As written (exposure = workload averaged over the term) |
| **B** | Fewer than 60% short, renewal visibility at least 10%, and median term under 730 days | Exposure = trailing 90-day workload ending on each expiry date (e); term average is variant S20. The write-up states up front that annual terms blur removal timing and that Family 2 can see only very large effects (7.6) |
| **C** | Renewal visibility below 10%, **or** median term 730 days or more (one row stretched over the whole spell) | Family 2 is declared **"not testable on permit data"** and C1 to C4 are not run. Spell counts are described only; the study stands on Family 1 |

**The likely case** is B or C, given the primary statements that pre-2026 permits were annual and auto-renewed (section 1).

---

## 5. Software
- **Interpreter:** `.venv/bin/python` (lifelines 0.30.3, statsmodels 0.15.0, installed on Jayden's yes; pandas 2.3.3 inside, 3.0.2 outside; Cycle 9 shares matched both, per `WORKLOG.md`).
- **Models:** statsmodels GLM, binomial family, cloglog link, standard errors clustered by calendar quarter (7.4).
- **Required before any shed row or repair duration is opened:** a hand-written numpy/scipy fit and the statsmodels fit must agree to 4 decimals on simulated data and recover a planted hazard ratio. A first statsmodels check (Oct 17, 2026) recovered a planted 0.75 as 0.80 (interval 0.72 to 0.88).
- **lifelines:** its time-varying Cox model may serve as an extra check only, labelled so.

---

## 6. Exposure: the city's repair workload

### 6.1 The deadline table
Explicit table in `src/facade_common.py`:
- Cycle 8: A Feb 21, 2017; B 2018; C 2019.
- Cycle 9: A 2022; B 2023; C 2024.
- Cycle 10: A 2027; B 2028; C 2029.

Cycles also end on Feb 20 of years ending in 0 and 5 (2015, 2020, 2025; Gate 0 note p. 63 for Cycle 10). Late filers from all groups pile up there.

### 6.2 Measured workload (primary exposure, both families)
- **Daily workload** on day t = UNSAFE Initial filings citywide (any cycle or group, facade snapshot, dated by F) in the 90 days ending on t, divided by **400** (one wave unit). 400 is about how far a typical deadline wave sits above normal: the Mar 1 median in the six deadline years was about 478, against a median of 106 over all days.
- **Family 1:** x = daily workload on the filing date F (fixed per filing). x_own and x_other split it by the building's own group vs the other two groups.
- **Family 2, Branch A:** x = daily workload averaged over the term. **Branch B:** x = daily workload on the expiry date. x_own and x_other as above.
- *Why 90 days:* DOB's 90-day repair clock. S5 and S6, and V7, try other look-backs.

### 6.3 Why measured workload, not a calendar rule
A yes/no rule (Feb to Apr of deadline years = wave) mislabels real surges.
- **Mislabelled surges:** Feb 2020 (cycle end) reached 385 on Mar 1, above the 2018 deadline wave's 330. Feb 2015, Feb 2025, Jun 2015 and Aug 2016 were also high.
- **Too few controls:** taking those out would leave two clean comparison winters, 2016 and 2021.
- **What measured workload adds:** it uses the real dose in almost every month (COVID months excepted) and includes surges outside winter.
- **Its cost:** counts include owners' choices about when to file. But each building's workload is almost entirely *other* owners' filings, and filing timing is in the model.
- **The calendar rule** is variant S12 (Family 2) and V8 (Family 1).

**Separating workload from winter, year and policy:**
- **Controls:** month-of-year effects, calendar-year effects, and policy-step indicators (6.5).
- **The question this answers:** *is it slower when workload is above what is normal for that month and that year?* That is a difference in differences: comparing a change with the change in a comparison group.

### 6.4 The calendar alternative (S12, V8)
- **w** = the share of days (Family 2) inside any group's Feb 1 to Apr 30 deadline window, or for Family 1, whether F falls in one.
- **Nuisance indicator:** cycle-end windows (Feb to Apr of 2015, 2020, 2025), plus the 3-month windows starting in any other month with at least 99 citywide UNSAFE filings (3 × the rounded median of 33). Those are Jun to Aug 2015 and Aug to Oct 2016.

### 6.5 Shed-policy changes and COVID
Year effects absorb Jan 1 changes. A mid-year change gets a **policy-step indicator** (0 before, 1 from that date). In Family 1 the steps are evaluated at each 30-day step's date; in Family 2 at the expiry date.

| Date | What | Source (read Oct 17, 2026) | Handling |
|---|---|---|---|
| Dec 17 to 30, 2019 | After a pedestrian death, DOB swept 1,331 facades (220 needed protection); 90-day follow-ups, more inspectors, higher penalties | DOB release Dec 30, 2019, https://www.nyc.gov/site/buildings/dob/pr-facade-inspections.page | Step from Dec 17, 2019 |
| about Feb 20 to 21, 2020 | Amended FISP rule for Cycle 9 | Secondary only (engineering firm news, Jan 23, 2020, https://www.wje.com/news/detail/new-york-city-revises-rules-for-facade-inspection-safety-program-fisp); **date UNVERIFIED** | Step from Feb 21, 2020 |
| Mar to Jun 2020 | COVID pause on non-essential construction (from memory, **UNVERIFIED**: Mar 22 to June 2020) | none | Family 2: rows expiring Mar 1 to Sep 30, 2020 dropped; S7, S8, S19. Longer terms that straddle the pause stay in, year effects only partly absorb this, and their workload includes the high Mar 2020 level, so the likely bias is toward a false positive; read S7 and S19 next to C1. Family 1: a time-varying COVID indicator for steps overlapping Mar 1 to Sep 30, 2020; V3 drops filings with F from Dec 1, 2019 to Sep 30, 2020 (same false-positive risk: the Feb 2020 surge met the pause) |
| Jul 24, 2023 | "Get Sheds Down" plan announced | Mayor's Office release, https://www.nyc.gov/mayors-office/news/2023/07/mayor-adams-dob-commissioner-oddo-plan-remove-unsightly-sheds-scaffolding-nyc | Step from Jul 24, 2023 |
| Apr 17, 2025 | Five bills signed (Local Laws 48 and 51 of 2025 among them): shed permits "from one year to three months," penalties for missed facade-repair milestones | Mayor's Office release, https://www.nyc.gov/mayors-office/news/2025/04/mayor-adams-signs-historic-legislation-get-sheds-down-remove-unsightly-scaffolding-across | Family 1: follow-up ends Apr 16, 2025. Family 2: step from Apr 17, 2025 |
| about Jan 12, 2026 | Local Law 48 takes effect "270 days after it becomes law" | https://www.nyc.gov/assets/buildings/local_laws/ll48of2025.pdf; Jan 12 assumes it became law Apr 17, 2025 (**UNVERIFIED**) | After both ends |
| Jan 26 or Feb 2, 2026 | 90-day shed permits, no auto-renewal; permits issued earlier "expire as they would have" | DOB notice Jan 8, 2026, https://www.nyc.gov/assets/buildings/pdf/sidewalk_shed26-sn.pdf (gives both dates) | After both ends; step in S17 |
| Jan 1 / Mar 6 / Aug 20, 2026 | New administration; shed push (proposed rules); final rules 1 RCNY 102-07 in effect, 7,427 sheds as of Aug 17, 2026 | Aug 20, 2026 release, https://www.nyc.gov/mayors-office/news/2026/08/mamdani-administration-taking-down-sidewalk-sheds-and-improving-; Mar 6 release cited in `PLAN.md` | After both ends; S17 |

My searches found no other change in the wave years 2022 to 2024 (a search is not proof; UNVERIFIED).

---

## 7. The tests

### 7.1 Models
All are **discrete-time hazard models**: one row per step, outcome "event or not," fitted as **complementary log-log (cloglog) regressions**, the grouped-time counterpart of the Cox hazard-ratio model (Prentice and Gloeckler, *Biometrics*, 1978, from memory). Exponentiated coefficients are hazard ratios. *Survival analysis* means studying how long things last, allowing for cases still going at the cutoff (censored).

**Shared controls:**
- **Filing timing** (Early baseline, Middle, Last-minute, Past-deadline).
- **Deadline group, cycle, borough.**
- **Stories** (PLUTO `NumFloors` bands: up to 9, 10 to 14, 15 to 24, 25 and over, missing).
- **Wall:** contains "MASONRY"; contains "TERRA COTTA"; missing.
- **Indicators:** carried over; OwnerType X; no PLUTO match.

**Family 1:**
- **M5** (gives C5). Event: clearance in the step. Terms: x at F; the shared controls; year and month-of-year of F; time since filing (steps 1, 2, 3, 4 to 6, 7 to 12, 13 to 24, 25 and over); time-varying COVID and policy-step indicators.
- **M6** (gives C6): M5 on Early filers only, filing-timing terms removed.

**Family 2** (under Branch A or B):
- **M1** (gives C1, C4). Event: shed ended at the decision point. Terms: x (6.2), WinterStart (spell started Dec to Feb), the shared controls, spell age (up to 6, 6 to 12, 12 to 24, over 24 months), term length (up to 100, 101 to 200, 201 to 400, over 400 days), month-of-year and year of expiry, policy steps.
- **M2** (gives C3): M1 with x split into x_own and x_other.
- **M3** (gives C2): M1 on Early filers, timing terms removed.

### 7.2 Confirmatory tests, in two families
| Family | # | Number reported |
|---|---|---|
| **1 (primary, headline)** | **C5** | HR per wave unit of x in M5 |
| | **C6** | HR per wave unit of x in M6 |
| 2 (secondary, run only under Branch A or B) | C1 | HR per wave unit of x in M1 |
| | C2 | HR per wave unit of x in M3 |
| | C3 | HR per wave unit of x_other in M2 |
| | C4 | HR on WinterStart in M1 |

Each is reported with a two-sided 95% confidence interval.

### 7.3 Many tests
- **Holm within each family:** sort the p-values; require the smallest below 0.05/n, the next below 0.05/(n − 1), and so on; stop at the first failure. That is n = 2 in Family 1 and n = 4 in Family 2.
- **No adjustment across families.**
- **The headline comes from Family 1.** Family 2 is always reported next to it, or reported as "not testable."
- **Not run:** a test marked "not run," "not testable" or "not separable" (7.7) leaves the Holm count for the rest.
- **No significance claims elsewhere:** variants (V1 to V11, S1 to S20), placebos and exploratory items get estimates and intervals only.

### 7.4 Clustering
- **Primary: cluster by calendar quarter**: of F in Family 1, and of the expiry date in Family 2.
- *Why:* workload x is a citywide calendar variable. Every filing made on the same day has the same x (Family 1), and so does every decision point expiring the same day (Family 2). A shock to repair speed shared by a whole period (weather, DOB staffing, a rule not in 6.5) hits every building at once. Clustering by block cannot see that. Quarters match the 90-day look-back.
- **So the workload contrast rests on about 11 years and about 40 quarters**, not on thousands of events. Family 1 has 40 quarters with filings (Feb 2015 to Dec 2024) and 30 with Early filings, counted from filing dates.
- **Few-clusters correction:** with so few clusters, intervals and p-values use a t distribution with K − 1 degrees of freedom (K = number of quarters) and the usual small-sample correction to the clustered errors.
- **Variants (not tests):** clustering by month; two-way by block and quarter; by block only (the earlier draft's choice). These are S10 (Family 2) and V11 (Family 1).

### 7.5 Meaningful effect
- **Meaningful:** HR 0.80 or lower per wave unit, or 1.25 or higher. At 0.80, a typical deadline wave makes the chance of the event in each step a fifth lower, so waiting time is about 25% longer while it lasts.
- **"No meaningful effect":** the whole 95% interval lies inside 0.80 to 1.25.
- **Inconclusive:** anything else.

### 7.6 Power, by reasoning (exposure spreads from section 1; event counts are guesses, UNVERIFIED)
- **Rule of thumb with a quarter term:** SE² ≈ τ² / (K × V) + 1 / (events × V).
  - **V** is the residual variance of x (section 1).
  - **K** is the number of quarters in the frame.
  - **τ** (tau) is the standard deviation of a shared per-quarter shift in the log hazard: how much repair speed jumps around from quarter to quarter for reasons that hit everyone.
  - **τ values of 0.05, 0.10 and 0.20 are assumptions, not estimates.**
- **Detection and nulls:** an effect is detected with 80% power at 2.8 × SE. Showing "no meaningful effect" needs an SE of 0.114 or less.
- **K values:** K = 40 for C5 and 30 for C6, counted from filing dates. For Family 2, K = 42 is assumed: the quarters of 2015 to 2025, less the two COVID quarters dropped. Expiry dates are not known yet.
- **Family 1 event counts** are capped by the 4,396 frame filings with a clearing filing at any date. How many fall before censoring is unknown and was not looked at.

| Test | SD of x (V = SD²) | K | Events assumed | Smallest HR detected at τ = 0.05 / 0.10 / 0.20 | SE at τ = 0.10 | Clean null possible? |
|---|---|---|---|---|---|---|
| C5 | 0.292 | 40 | 2,000 | 0.80 / 0.77 / 0.69 | 0.094 | Yes if τ ≤ 0.10 |
| C5 | 0.292 | 40 | 3,000 | 0.83 / 0.79 / 0.70 | 0.083 | Yes if τ ≤ 0.10 |
| C5 | 0.292 | 40 | 4,000 | 0.84 / 0.81 / 0.71 | 0.077 | Yes if τ ≤ 0.10; no at τ = 0.20 (SE 0.12) |
| C6 | 0.267 | 30 | 600 / 800 / 1,000 | 0.64–0.71 / 0.63–0.68 / 0.56–0.60 (range across event counts) | 0.14 to 0.17 | No |
| C6 if only cycle 9 qualified | 0.292 | 15 | 300 / 450 / 600 | 0.57–0.66 / 0.55–0.63 / 0.48–0.53 | 0.17 to 0.22 | No; and 15 quarters fails the 24-quarter stop rule |
| C1, Branch A (90-day terms) | 0.259 | 42 (assumed) | 500 / 1,000 / 2,000 | 0.61–0.77 / 0.60–0.75 / 0.56–0.66 | 0.11 to 0.18 | Only near 2,000 events and τ ≤ 0.10 |
| C1, Branch B (365-day terms) | 0.259 | 42 (assumed) | same | same observed values, but see below | — | No |

- **C5 is reasonably powered:** it can detect an effect near the meaningful line (0.77 to 0.81 at τ = 0.10). It could show a clean null unless quarter-to-quarter shocks are large (τ = 0.20).
- **C6, the clean arm, can see only fairly large effects:** HR about 0.63 to 0.68 per wave unit at τ = 0.10, and 0.56 to 0.60 at τ = 0.20. It cannot prove a null. It is still far better than C2. If availability ever limited it to cycle 9's early filers, it would have 15 quarters and fail the stop rule.
- **Branch B (365-day terms):** a shed may have come down any time in the year before expiry, so the 90 days before expiry catch only part of the period that mattered. That dilutes a true effect roughly two to four times on the log scale (rough reasoning, UNVERIFIED). To be seen at the observed 0.68 (1,000 events, τ = 0.10), a true HR near 0.46 down to 0.21 would be needed. **Under Branch B, Family 2 can find only very large effects.**
- **Optimism caveat:** the filing-timing terms barely reduce x's spread in Family 1 (0.293 to 0.292). That is not checked for Family 2 rows.

### 7.7 Stop rules and the identifiability rule (counts only, checked before any model is fit)
- **Stop rules.** Below these, the test is "not testable" and only counts are described.
  - **C5:** at least 1,000 filings and 400 clearances, and the availability rule in 3.1.
  - **C6:** at least 300 Early filings and 100 clearances, and the availability rule.
  - **Quarters:** C5 needs at least **24 quarters containing filings**; C6 needs 24 quarters containing Early filings; C1 to C4 need 24 quarters containing decision points. With fewer, the few-clusters correction cannot be trusted.
  - **C1 to C4:** at least 600 linked spells and 400 ended events. C2 also needs at least 100 Early ended events. C3 also needs at least 60 ended events among rows in the top 30% of x_other.
- **Identifiability rule (rank-based bands).** Within each family's analysis rows (filings for Family 1, decision points for Family 2):
  - **Bands:** **quiet** = bottom 40% of x, **busy** = top 30% of x. Filing timing: **Early** vs **Late** (Last-minute plus Past-deadline).
  - **Corner cells:** each of the four (Early-quiet, Early-busy, Late-quiet, Late-busy) needs at least **50 rows and 20 events**.
  - **If one falls short:** C5 (or C1) is reported as **"not separable from filer type,"** not as a result. C6 (or C2) needs both Early cells to pass.
  - **Also reported:** the residual SD of x after year, month and filing timing, divided by the SD after year and month, as a description of separability.
  - *Why:* workload can be told apart from filing timing only if early filers are seen in busy periods and late filers in quiet ones.
  - *Exposure-only check now:* in Family 1 the Early-busy cell has 126 filings before the public-owner exclusion (section 1). How many of those clear is not known.
- **No rescue:** no rule is loosened to rescue a failed check. Doing so would be a deviation, and results would be labelled exploratory.

### 7.8 Placebos (not confirmatory)
- **PL1: quiet months of wave years.**
  - **What it adds:** to M5, an indicator for F in Aug 1 to Oct 31 of a deadline year (2017 to 2019, 2022 to 2024); to M1, for expiry in those months. Every such month had fewer than 60 citywide UNSAFE filings.
  - **Expected:** HR near 1.
  - **If its interval excludes 1 and the HR is outside 0.80 to 1.25:** wave years differ in some way the controls miss. The family's workload test is then reported with that warning and may not be called confirmatory.
- **PL2: future workload.**
  - **What it adds:** the workload of the 90 days after F (M5) or after the expiry (M1).
  - **Expected:** HR near 1.
  - **If it is non-null:** it may mean anticipation (contractors booking ahead), so it is reported but is not decisive.

### 7.9 Family 1 variants (one at a time; not tests)
| ID | What changes |
|---|---|
| V1 | F to Dec 31, 2025 and follow-up to Dec 31, 2025, with a step at Apr 17, 2025 |
| V2 | A later Subsequent SAFE or SWARMP filing also counts as clearance (72 more) |
| V3 | Drop filings with F from Dec 1, 2019 to Sep 30, 2020 |
| V4 | Workload re-measured at each step (time-varying) instead of fixed at F |
| V5 | Drop filings whose current status is cleared but have no clearing filing (467 in the whole UNSAFE frame) |
| V6 | 14-day steps |
| V7 | Workload look-back 30 days; 180 days |
| V8 | Calendar rule (6.4) instead of measured workload |
| V9 | Straight-line year trend instead of year effects; include public lots (each run separately) |
| V10 | Count a next-cycle Initial filing rated SAFE or SWARMP as a clearance on its date (at most 6 cases) |
| V11 | Cluster by month; two-way by block and quarter; by block only (each run separately) |

---

## 8. What each result means

No result is a statement about the safety of any building, about any owner, or about any inspector. UNSAFE and SAFE are ratings on filings; the study says "filed as UNSAFE" or "filed as cleared" and nothing more. Nothing is reported at building level.

**Read the table with these in mind:**
- **Family 1 gives the headline.** Family 2 is weaker evidence, because pre-2026 permits were probably annual (4.6).
- **C6 is the only well-powered clean test of bottleneck vs owner behavior,** and it can see only fairly large effects.
- **The workload contrast rests on about 11 years and about 40 quarters of variation**, however many events there are, so the intervals are wide by design.

**Definitions:** "Clearly slower" = HR below 1 and Holm-significant within its family. "Not slowed" = the whole 95% interval inside 0.80 to 1.25.

| Result | What we would say | What we would NOT say |
|---|---|---|
| **C5 not separable** | "Busy periods and late filers overlap too much to tell apart." | Any C5 HR as a finding |
| **C5 and C6 clearly slower, PL1 near 1** | "Repairs clear more slowly when citywide workload is high, including at buildings that filed early. That fits a shared bottleneck." Size it in Step 5 as a range | That contractors are overloaded (not observed), or which part of the pipeline it is |
| **C5 clearly slower, C6 not slowed** | "The slowdown travels with late filers, not with workload. It points to owner behavior." | That deadline waves do nothing (they still pile up filings) |
| **C5 clearly slower, C6 inconclusive** | "Repairs are slower when workload is high. We cannot tell whether that is a bottleneck or the owners who file last." | "Proven bottleneck" or "proven owner behavior" |
| **C5 and C6 both near 1 ("not slowed")** | "No slowdown in repair clearance larger than about 20% per wave unit fits the data. The calendar creates filing waves, not repair delays." | That workload can never matter |
| **C5 near 1, C6 inconclusive** | "No overall slowdown; the early-filer check is too small to add anything." | A bottleneck claim |
| **Family 1 and Family 2 disagree** | Report both. The headline follows Family 1, with Family 2's weakness (annual terms, end-date blur) stated next to it | That sheds and repairs "show opposite things" without that caveat |
| **Family 2 Branch C** | "Shed permits before 2026 cannot time removals well enough to test this." | Any shed-removal finding |
| **C1 clearly slower, C2 or C3 not slowed** | "Shed removal slows with late filers, not workload" (secondary) | A headline on this alone |
| **Any family: inconclusive** | "The data cannot say." Report intervals | Absence of significance as absence of effect |
| **PL1 non-null** | "That family failed a placebo; its workload result is exploratory." | It as confirmatory |
| **HR 1.25 or higher** | "Faster when workload is high," with an untested guess that deadlines bring attention | A policy recommendation |
| **C4 clearly below 1 and meaningful** | "Sheds started Dec to Feb last longer, beyond workload," consistent with, not proof of, weather | That cold causes it |
| **Stop rule triggered** | "Too few cases to test." Counts only | Any HR claim |

**Robustness note:** a headline result is "robust" only if its estimate and at least three-quarters of its family's variants that could be run point the same way, and its interval excludes 1. Otherwise it is "fragile."

---

## 9. Deviations and exploratory analyses

### 9.1 Deviation policy
- **After data is seen:** after any shed row or any repair duration is seen, every rule change is a dated **deviation** in this file and the report, never made quietly.
- **Between lock and first look:** only the code-list strings (4.1) and the branch choice (4.6) are filled in, and both are logged.
- **Approval:** changing a pre-registration after data has been seen is a Level B post for Jayden (`../CLAUDE.md`).
- **Code freeze:** the analysis code is committed before any data is opened (5); later edits are logged.

### 9.2 Exploratory (no significance claims)
- **E1:** Cycle 7, including Group B's Aug 2012 deadline (a wave outside winter), described only.
- **E2:** whether the Dec to Feb start effect differs between high- and low-workload years.
- **E3:** the filing-timing penalty among rows in the quiet band (the H2 check), in both families.
- **E4:** filing timing × x interactions.
- **E5:** "crude" HRs for x without filing-timing terms, next to C5 and C1, showing the size of the late-filer trap.
- **E6:** live replication after Group A's Feb 21, 2027 deadline, with fresh pulls about Jul 31, 2027. Prediction now: if H1 is supported, x again shows HR below 1 in Family 1.
- **E7:** public-owned lots, described and fitted on their own.
- **E8:** C6 and C2 re-run on in-window Early filers only (leaving out the 953 before-window filers).
- **E9:** carried-over vs not-carried-over filings fitted separately (S15 is one half).
- **E10:** x_own vs x_other in Family 1.
- Anything else is exploratory and labelled so.

### 9.3 Reporting rules
- **AI-use line** on every public file.
- **Figures** name the dataset, its ID and pull date, plus "aggregated and charted by us."
- **No owner or inspector names** are ever used.

---

## 10. Before locking (checklist)
- [x] Gate 0 recorded (`writeup/gate0-dob-fisp-study.md`, commit `2eacf96`); leads built in.
- [x] Critical pass on Opus (Oct 17, 2026); two-family revision (Oct 17, 2026), logged in `WORKLOG.md`.
- [x] Final re-read for wording that could be read as a safety judgment about a building, owner or inspector (Oct 17, 2026).
- [x] Every number cites a source and date, or is labelled UNVERIFIED (Oct 17, 2026).
- [ ] Jayden has seen the file, or the main session has posted the summary on the Research Desk. (Not confirmed by this session; Jayden has not yet reviewed it.)
- [x] Lock date entered and committed as "Lock PREREG"; the tag `prereg-locked` marks that commit (push recorded in `WORKLOG.md`).
- *(Before any data is opened, not a lock condition:)* simulated-data code check passed and code committed (5).

## 11. UNVERIFIED list
1. The shed code strings (settled by the code-list step).
2. Whether any shed sign-off or removal date exists.
3. **Pre-2026 permits being annual and auto-renewed rests on two primary statements (Apr 17, 2025 release; Jan 8, 2026 DOB notice). Whether DOB NOW lists renewals as separate rows is unknown** (the structure check settles it).
4. Whether 90-day permits began Jan 26 or Feb 2, 2026 (the notice says both).
5. The COVID pause dates.
6. The 2020 FISP rule's exact date.
7. Local Law 48's "became law" date; Intro 661-A's effective date.
8. That no other policy change happened in 2015 to 2025 beyond 6.5.
9. Event counts for every family, the spread of x across Family 2 rows, Family 2's number of quarters, the size of shared quarter-to-quarter shocks (τ), and the 2 to 4 times dilution under Branch B. All power numbers rest on these.
10. That deadline group is close to random with respect to building traits.
11. Prentice and Gloeckler (1978), cited from memory.
12. The Cycle 6 deadline (not used).
13. What `prior_status` means (the dictionary lists values only).
14. Current PLUTO `OwnerType` codes, and how many filings the public exclusion removes.
15. The Gate 0 note's page numbers.
16. The causes of the Jun 2015, Aug 2016 and Oct 2020 surges.
17. That an Amended SAFE or SWARMP filing means DOB accepted it. And how the 467 "cleared without a clearing filing" were cleared.
18. That a clearing filing made after its cycle ended still carries the original cycle label (only the order of dates was checked).

## 12. Glossary
- **FISP:** NYC's facade inspection program.
- **BIN:** the city's building number.
- **UNSAFE / SWARMP / SAFE:** an engineer's filing ratings. SWARMP means safe with a repair and maintenance program.
- **Clearing filing:** an Amended filing rated SAFE or SWARMP after an UNSAFE one.
- **Workload / wave unit:** UNSAFE filings citywide in the last 90 days / 400 such filings.
- **Survival analysis:** statistics for how long things last.
- **Hazard / hazard ratio:** the chance something ends in a step, given it lasted so far / the ratio of that chance in two situations.
- **Censored:** still going at the cutoff, so its end is unknown.
- **Cloglog regression:** the discrete-time hazard-ratio model.
- **Year and month-of-year effects:** separate baselines per year and per calendar month.
- **Policy-step indicator:** 0 before a rule's start date, 1 after.
- **Difference in differences:** comparing a change with the change in a comparison group.
- **Clustered standard errors:** uncertainty widened because related rows move together. Here, rows in the same calendar quarter.
- **Holm method:** keeps the chance of any false alarm within a family at 5%.
- **Placebo:** a test where the method should find nothing.
- **PLUTO:** the city's tax-lot file.

## Deviations
Dated entries made after the lock. Neither entry below involves any shed row or any repair duration; none has been seen. The locked text above is left as it was, and the tag `prereg-locked` still marks it.

**D1. Oct 17, 2026 (evening): precedence between branches in 4.6. A clarification of a contradiction, not a change to any test, threshold or design.**
- **The problem.** As locked, Branch A (60% or more of rows have terms of 120 days or less) and Branch C (renewal visibility below 10%) can both be true at once, while the text says exactly one branch applies. B cannot overlap A or C, because its conditions are the opposite of theirs. Found by the code session while writing the branch function; it declined to choose.
- **The resolution.** Check **C first, then A, then B.** If C's condition holds, Branch C applies even when most rows are short.
- **Why.** If renewals do not show up as separate rows, almost every spell has one decision point, and its outcome is always "ended." The outcome then has nothing to vary and no hazard model can be fitted. That is exactly the case Branch C exists for, so it must win.
- **Who and when.** Made by the main session on Oct 17, 2026, before the code freeze and before any shed data was downloaded or opened. Also logged in `WORKLOG.md`; the final report must mention it.

**D2. Oct 18, 2026: what "renewal visibility" counts in 4.6. A clarification, not a change to any threshold.**
- **The problem.** 4.6 defines renewal visibility as the share of rows that start within 30 days *after* another shed row at the same BIN ends. Read literally, that misses a renewal issued *before* the old permit runs out, or an overlapping permit. But Step 3 of 4.1 chains permits by "no more than 30 days after the running latest end" and says overlaps and back-to-back renewals are always the same spell, and the model's decision points (Step 5) exist whenever a spell has two or more expiry dates, whether or not the permits overlap. So the literal wording would count too few renewals and could tip Branch C for the wrong reason. Found by the code session, which coded the literal wording and also returned the inclusive number, labelled "NOT USED."
- **The resolution.** The branch rule in 4.6 uses the **inclusive** number: the share of rows that are not the first row of their spell under the Step 3 chaining rule (G = 30 days, overlaps and early renewals counted), which is the code's `renewal_visibility_incl_overlap_NOT_USED`. The 10% threshold and every other threshold are unchanged. The literal number is reported next to it in `WORKLOG.md`. No code change: `choose_branch` is called with the inclusive number in place of the literal one, and that call is logged.
- **Direction.** The inclusive number is never smaller than the literal one, so this can only move a case out of Branch C, never into it. It is a pre-data choice made without seeing either number.
- **Who and when.** Main session, Oct 18, 2026, after the code freeze (`gate2-code-frozen`, eb5c6dc) and after the downloads began, but before any shed row was printed, counted or inspected.

**D3. Oct 18, 2026: implementation choices where the PREREG was silent, accepted as written in the frozen code.** Each is marked CHOICE in `src/gate2_link.py` or `src/gate2_model.py` and listed in `WORKLOG.md`.
- The workload window includes day t itself.
- A Family 1 filing keeps only fully observed 30-day steps; an event in a partly observed step counts as censoring. This avoids an upward bias in the last step before the follow-up end.
- Policy-step and COVID indicators are evaluated at each step's first day.
- In variants S3 and S4 the "already standing" test day moves with the link window.
- A filing that loses a spell to a closer filing stays unlinked.
- The 50% availability rule is also applied inside every variant (so V1 drops cycle 10).
- Filings are linked by an internal unique id, not `tr6_no`; `tr6_no` is still the tie-breaker for the earliest filing of a repeated (BIN, cycle).
- **Who and when.** Main session, Oct 18, 2026, before any shed row or repair duration was seen. No rule, threshold or test was changed.

**D4. Oct 18, 2026: the confirmatory standard errors are a delete-one-quarter jackknife, not the quarter-clustered estimator of 7.4. This makes inference more conservative, never looser.**
- **What the calibration showed.** `writeup/gate2-calibration.md`, `figures/gate2_calibration_reps.csv`, `src/gate2_calibration.py`: simulated data only (150 repeats in each of 18 cells; the real file contributed only the daily count series of UNSAFE Initial filings, which sets how rough the simulated workload is). Over all 2,700 replicates the pre-registered 95% interval contained the true value **90.2%** of the time (Monte Carlo SE 0.006), and with no true effect it called a result significant 7.8% (C5), 9.6% (C6) and 10.4% (C1) of the time instead of 5%. The delete-one-quarter jackknife covered **96.5%** (false alarms about 4%). The wild cluster bootstrap-t covered 95.1%, but it is random and was only a fast approximation.
- **The rule I fixed before the run, and how I read it.** The pre-registered estimator was to stay primary unless, at tau = 0.10, its coverage in C5 or C1 was below 0.92 and an alternative reached 0.93 or more. At tau = 0.10 the pooled figures (C5 0.923, C1 0.920) did not trigger it; the planted-effect cells did (C5 0.893 and C1 0.913, against jackknife 0.993 and 0.980). The wording did not say whether "its coverage" was pooled or per cell. I took the stricter, per-cell reading, because the true effect is unknown, and because the shortfall shows in nearly every cell of the table, not only at tau = 0.10. The decision rests on simulated data and was made before any real analysis, so it cannot be tuned to a result.
- **The resolution.** Intervals and p-values for the confirmatory tests (C1 to C6, and the Holm step) use the delete-one-quarter jackknife variance (CR3 type, a one-step update for each deleted quarter, as coded in `src/gate2_calibration.py`), with t on K - 1 degrees of freedom. The pre-registered estimator is reported as variant **V12** (Family 1) and **S21** (Family 2); the wild cluster bootstrap-t (B = 499, fixed seed) as **V13** and **S22**. Clustering by calendar quarter and everything else in 7.4 stay.
- **The cost, stated now.** Jackknife standard errors were on average 1.34 times the pre-registered ones (range 0.77 to 2.08). So the detectable-effect figures in 7.6 are optimistic by about that factor on the log scale, a clean null is harder still, and in the simulation the early-filer test (C6) lost power (0.67 to 0.46 at hazard ratio 0.75, tau 0.10).
- **Who and when.** Main session, Oct 18, 2026, after the code freeze and before any real analysis. No shed row and no repair duration had been looked at; the only shed-file contact was the code-list step's list of distinct category values.
