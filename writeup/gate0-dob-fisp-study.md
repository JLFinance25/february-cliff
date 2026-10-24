# Gate 0: what DOB's Dec 2025 FISP study says about the deadline calendar

Read by Claude (AI) on Oct 17, 2026, at Jayden Ling's request ("you read the study").

**Source:** Thornton Tomasetti for NYC DOB, "FISP Recommendations Report: A Review of the New York City Façade
Inspection & Safety Program," December 10, 2025, 110 pages. https://www.nyc.gov/assets/buildings/pdf/fisp.pdf

**How it was read:**
- nyc.gov blocks automated downloads of this file, and its 29 MB size is too big for the page reader.
- So Claude opened it in the desktop app's built-in browser from a DOB page, extracted the text in memory with
  pdf.js, and searched it. No copy was saved to disk.
- This was a keyword search of the full text plus reading the passages it found. **Not every page was read.**

## Finding: Gate 0 passes. The study does not measure or address deadline bunching.
- **Words that never appear** in the extracted text: "peak", "surge", "backlog", "bunch", "last minute",
  "workload".
- **The 11 recommendations:**
  1. New UNSAFE and SWARMP definitions
  2. Separating "administrative UNSAFE"
  3. A six-year cycle
  4. An abbreviated visual-only filing program
  5. An enhanced inspection option
  6. Reduced hands-on inspection
  7. A drone study
  8. Neighbor access agreements
  9. A better DOB help desk
  10. Clearer "Failure to Maintain" notices
  11. A guide for QEWIs (the licensed facade inspectors)
- **None of them** is about the sub-cycle calendar, filing timing or contractor capacity.
- **Its data work is about conditions, not timing:** filing status by building age and height. For example, it
  reports that 14% of buildings built within 40 years of the filing deadline file UNSAFE, against 28% of older ones
  (p. 70).

## Useful facts it confirms (VERIFIED, from the report)
- **The official deadline groups** (rule 1 RCNY 103-04, reprinted in Appendix E, pp. 101 to 102). Each window is
  two years and opens and closes on Feb 21:

  | Group | Block ends in | Window opens Feb 21 of years ending in | Window closes Feb 21 of years ending in |
  |---|---|---|---|
  | A | 4, 5, 6 or 9 | 0 and 5 | 2 and 7 |
  | B | 0, 7 or 8 | 1 and 6 | 3 and 8 |
  | C | 1, 2 or 3 | 2 and 7 | 4 and 9 |

  This confirms the grouping used in `PLAN.md` and the Oct 16 test.
- **Cycle structure:** "Within each five-year cycle, all covered buildings are grouped into one of three two-year
  sub-cycle windows (A, B and C), based on the last digit of the building's block number. The sub-cycle windows
  currently overlap by one year" (p. 63). Cycle 10 runs Feb 21, 2025 to Feb 20, 2030.
- **New in Cycle 10:** owners whose last status is "No Report Filed" may file before their window opens, if they pay
  their penalties (Appendix E, p. 102).
- **Other cities:** Philadelphia staggers its 5-year cycle by decade of construction, and San Francisco staggers by
  date of construction (Appendix comparison table, p. 88). NYC staggers by block number.

## Two leads for the pre-registration (Claude's reading, not yet tested)
1. **A second cliff, at cycle end.**
   - What the study says: SWARMP conditions (safe but needing repair) that are not repaired within the cycle are
     reclassified UNSAFE. Some owners, especially public agencies, then keep sheds up under "Administrative UNSAFE"
     (p. 43; Recommendation 2).
   - Why it matters: new sheds may also spike at each group's next deadline, from reclassification rather than new
     damage.
   - What PREREG.md should do: separate first-time UNSAFE from SWARMP carried over into UNSAFE.
2. **Public agencies don't follow the calendar.**
   - What the study says: public owners' repairs run on capital budgets and procurement "without any connection to
     the schedule mandated in the FISP regulations." Years can pass between a shed going up and a contractor arriving
     (p. 40).
   - What PREREG.md should do: analyze public and private buildings separately, or exclude public owners from the
     main test, because their sheds measure procurement rather than contractor capacity.
