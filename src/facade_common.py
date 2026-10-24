# Shared constants for the facade-calendar project: the three FISP deadline groups and each group's filing windows.
#
# Digit groups (DOB's own statements, all read Oct 17, 2026):
#   1 RCNY §103-04(c)(4)(v), https://www.nyc.gov/assets/buildings/rules/1_RCNY_103-04.pdf (PDF dated Feb 3, 2026):
#     A = blocks ending 4, 5, 6, 9;  B = 0, 7, 8;  C = 1, 2, 3. The staggered cycle begins Feb 21, 2010 (Cycle 7).
#   The same digits appear in each DOB document below.
# Windows, one DOB document per cycle:
#   Cycle 7:  DOB "Tool Kit - Facades" (PDF created Jun 30, 2011), https://www.nyc.gov/assets/buildings/pdf/tool_kit_facades.pdf
#             A 2/21/2010-2/21/2012, B 2/21/2011-8/21/2012, C 2/21/2012-2/21/2013. Cycle 7 was a shorter transition
#             schedule: B and C had 18 and 12 months, and the deadlines sit 6 and 12 months after A's, not 12 and 24.
#             The rule's general formula does NOT reproduce this, so do not use a formula for Cycle 7.
#   Cycle 8:  DOB "TR6 Instructions" Rev. 12/16 (PDF Dec 28, 2016), https://www.nyc.gov/assets/buildings/pdf/tr6instr.pdf
#   Cycle 9:  DOB "FISP Cycle 9" sub-cycle diagram (PDF May 21, 2020), https://www.nyc.gov/assets/buildings/pdf/subcycle_9.pdf
#   Cycle 10: DOB service notice (Feb 24, 2025), https://nyc.gov/assets/buildings/pdf/facadecycle-sn.pdf
# Cycle 6 (before the stagger) is not in this table: the data show one shared spike in Feb 2007 for all three
# digit groups, but no DOB document for Cycle 6 was read, so its deadline is UNVERIFIED.
import datetime as dt

GROUP_DIGITS = {"A": "4569", "B": "078", "C": "123"}
DIGIT_TO_GROUP = {d: g for g, digits in GROUP_DIGITS.items() for d in digits}


def _d(y, m=2, d=21):
    return dt.date(y, m, d)


# (window opens, deadline). Every window closes on the deadline date.
WINDOWS = {
    7:  {"A": (_d(2010), _d(2012)), "B": (_d(2011), _d(2012, 8)), "C": (_d(2012), _d(2013))},
    8:  {"A": (_d(2015), _d(2017)), "B": (_d(2016), _d(2018)),    "C": (_d(2017), _d(2019))},
    9:  {"A": (_d(2020), _d(2022)), "B": (_d(2021), _d(2023)),    "C": (_d(2022), _d(2024))},
    10: {"A": (_d(2025), _d(2027)), "B": (_d(2026), _d(2028)),    "C": (_d(2027), _d(2029))},
}


def group_of_block(block):
    """Deadline group (A/B/C) from the last digit of the tax block, or None if the block is missing or not digits."""
    if block is None or not str(block).isdigit():
        return None
    return DIGIT_TO_GROUP[str(block)[-1]]


def window(cycle, group):
    """(opens, deadline) as dates for cycles 7 to 10."""
    return WINDOWS[cycle][group]
