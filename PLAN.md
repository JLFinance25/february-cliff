# Plan: the February cliff

Drafted by Claude (AI) on Oct 17, 2026, from a draft of Oct 16. Jayden Ling decided to start the project on
Oct 17, 2026; he had not reviewed the plan's details at that time. Changes after approval go in a dated list at the end.

## The question
NYC's Facade Inspection and Safety Program (FISP, Local Law 11) requires buildings over six stories to have their
facades inspected and to file a report once per cycle. Buildings are split into three deadline groups by the last
digit of their tax block, and each group gets a two-year filing window. All three windows end on Feb 21.

1. Inside each group, do inspections, filings and repairs pile up near the deadline?
2. Does the pile-up keep sidewalk sheds up longer?
3. Which calendar for the next cycle would cut total shed-days, with every building inspected as often as today?

## Why now
- On Mar 6, 2026 the Mayor's Office said DOB will move the inspection interval from five to six years, with 12
  years for lower-risk buildings. As of Oct 16, 2026 no rule text had been published: DOB's Apr 10, 2026
  newsletter says it "is working on" FISP rules.
  https://www.nyc.gov/mayors-office/news/2026/03/mayor-mamdani-launches-new-efforts-to-take-sidewalk-sheds-down--.html
- A final shed rule (announced Aug 20, 2026) requires 90-day permit renewals and penalties after 180 days, expected
  from early 2027. There were 7,427 permitted sheds as of Aug 17, 2026.
  https://www.nyc.gov/mayors-office/news/2026/08/mamdani-administration-taking-down-sidewalk-sheds-and-improving-
- Group A's Cycle 10 deadline is Feb 21, 2027, so a real deadline wave happens during the project.

## What is already known (exploratory, run Oct 16, 2026, before any pre-registration)
Source: NYC Open Data "DOB NOW: Safety – Facades Compliance Filings" (`xubg-57si`), summary counts through the API.
Script: `src/spike_bunching_2026-10-16.py`. Groups by last digit of block: A = 4, 5, 6, 9; B = 0, 7, 8; C = 1, 2, 3.

| Cycle 9, initial filings | Filings | Filed in the deadline month | Inspections in the deadline month | Rated UNSAFE |
|---|---|---|---|---|
| A (deadline Feb 2022) | 5,321 | 37% | 21% | 26% |
| B (deadline Feb 2023) | 4,195 | 35% | 23% | 24% |
| C (deadline Feb 2024) | 4,029 | 33% | 18% | 24% |

- An even spread would put about 4% in each month of a 24-month window.
- Cycle 8 shows the same filing cliffs: 30%, 24% and 29% in the deadline months of 2017, 2018 and 2019.
- Group A is about 27% larger than B or C, because it covers four block digits instead of three.
- The three-group stagger itself dates from a 2007 change, made after about 12,000 buildings faced a single deadline
  (Habitat magazine, Oct 2007; secondary source).

**Gate 1 (do deadline waves exist?) passed.** Not known: whether the waves make sheds last longer.

## Method
**Step 0. Gate 0: prior work.**
- Read DOB's Dec 2025 FISP study (https://www.nyc.gov/assets/buildings/pdf/fisp.pdf). It is over 10 MB and the
  server blocks automated downloads, so open it in a browser and search for "sub-cycle", "deadline" and "contractor".
- If the study already measured these waves, narrow this project to what it left out.

**Step 1. Measure the waves.** Weekly inspections, filings and UNSAFE and SWARMP findings for cycles 7 to 10, by group.
- SWARMP means safe with a repair and maintenance program.
- Output: the "February cliff" chart.

**Step 2. Pre-register Gate 2.** Before opening any shed-permit data, lock `PREREG.md` with:
- the rule linking a shed to a filing;
- the definition of a wave month;
- the test;
- what each result would mean.

**Step 3. Link buildings to sheds.**
- Join filings to sidewalk-shed permits by building ID (BIN) and date: DOB NOW approved permits (`rbx6-tga4`, work
  type Sidewalk Shed) and legacy permits (`ipu4-2q9a`).
- Chain renewals into one shed spell per building. The last expiration approximates removal.
- Keep sheds that start after an UNSAFE filing as the main sample.
- Check the totals against DOB's published counts.

**Step 4. Gate 2: does a wave slow repairs?**
- **The trap:** owners who file at the last minute may also be slow to repair. That would make waves look harmful
  even if contractors are not the bottleneck.
- **The test:** if contractors are swamped, every repair underway during a wave should slow down, including
  buildings that filed early and buildings in other groups.
- **How:** compare shed-removal rates in wave months with other months, using survival analysis (statistics for
  how long something lasts). Control for building height, wall type, borough and condition.
- **Why the groups compare fairly:** a block's last digit is close to random with respect to the building.
- **Second test:** whether sheds put up from December to February last longer. The claim that cold weather slows
  facade repair is a hypothesis, not yet checked.

**Step 5. Simulate calendars.**
- A queue (waiting-line) model: repair jobs arrive from UNSAFE and SWARMP findings, and contractors finish a limited
  number per month. That capacity comes from step 4 and is reported as a range.
- Compare total shed-days and the busiest month under six calendars:
  - (a) today's calendar;
  - (b) DOB's six-year cycle with today's groups;
  - (c) equal-size groups;
  - (d) deadlines moved out of winter;
  - (e) ten groups, one per digit, with deadlines in different months;
  - (f) a rolling deadline on each building's own anniversary.
- Inspection frequency is held equal across all six.
- Baselines: (a) and (b).

## Data
All from NYC Open Data. Each download is logged in `data/raw/SOURCES.md`. The dataset pages list no license, so
check the nyc.gov terms of use before the first full download.
- `xubg-57si` facade filings. Only building, date, cycle and status fields are kept; owner and inspector names are
  dropped in the first processing step and never used.
- `rbx6-tga4` DOB NOW approved permits, and `ipu4-2q9a` legacy permits.
- PLUTO, for building traits (height, year built).

## Schedule (target dates)
| Week | Dates | Work |
|---|---|---|
| 1 | Oct 17 to 23 | Gate 0, terms check, `xubg-57si` download, February cliff chart for cycles 7 to 10, PREREG locked |
| 2 | Oct 24 to 30 | Shed-permit downloads, shed spells, checks against DOB counts |
| 3 | Oct 31 to Nov 6 | Gate 2 test |
| 4 | Nov 7 to 13 | Calendar simulation |
| 5 | Nov 14 to 20 | Two-page memo, one public chart, write-up |

## Possible results and what each means
- **Waves slow repairs:** a memo to DOB with calendar options and a range of shed-days saved.
- **Waves exist but do not slow repairs:** "the calendar creates inspection waves, not shed delays." DOB can still use
  this for staffing. The follow-on becomes which sheds DOB should chase first under the 90-day renewals.
- **DOB's study already covers it:** narrow to what it left out, for example the winter timing or the unequal groups.

## Risks and limits
- Contractor capacity is not observed directly; it is inferred and reported as a range.
- Long-lived sheds also come from owner financing, board votes, lawsuits and permit delays, and many sheds are not
  from facade inspections at all. The main sample is limited to sheds linked to UNSAFE filings.
- A permit's expiration date is not the day the shed comes down, so shed lifetimes are approximate.
- No safety judgments about any building.

## How it could expand
1. A live check of Group A's Feb 2027 wave as it happens.
2. Which sheds DOB should chase first once 90-day renewals start (2027 data).
3. Other cities with facade laws: Chicago, Boston, Philadelphia, Pittsburgh, Cincinnati, Milwaukee, St. Louis,
   Detroit, Columbus and Cleveland, per a trade table not yet checked against the laws themselves. Jersey City
   reportedly uses one shared Dec 31 deadline, a clean contrast.

## Changes after approval
(none yet)
