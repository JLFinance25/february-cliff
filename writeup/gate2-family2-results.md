# Family 2 results: shed permits

Drafted with Claude (AI); directed by Jayden Ling.

Aggregated results only. Pre-2026 shed permits were annual and auto-renewed, so shed removal dates are approximate (4.4); a null here is weak evidence.

Structure check (4.6, deviation D2 inclusive visibility): {'rows': 125016, 'renewal_visibility_incl_overlap_NOT_USED': 0.46240481218404045, 'share_term_le_120': 0.07572630703269981, 'median_term_days': 365.0, 'renewal_visibility': 0.14852498880143342} -> branch **B**.

## Gates (counts only)

- Link report: {'frame': 5134, 'excluded_standing': 2107, 'candidates': 2454, 'lost_competition': 2, 'linked': 2452}; link share by filing timing: {'overall': 0.47760031164783795, 'Early': 0.4167385677308024, 'Last-minute': 0.50093808630394, 'Middle': 0.5081967213114754, 'Past-deadline': 0.4850455136540962}
- Linked spells 2,452; ended events 1,762; quarters 38.
- Corner cells: Early-quiet 586/191 (pass), Early-busy 290/88 (pass), Late-quiet 1660/500 (pass), Late-busy 1482/431 (pass)
- C1 {'run': True, 'why': None}; C2 {'run': True, 'early_events': 357}; C3 {'run': True, 'events_in_top30_x_other': 559}; C4 {'run': True}
- Sanity count, spells standing on Aug 17, 2026 (compare 7,427 permitted sheds, Mayor's Office release Aug 20, 2026): 7,932

## Confirmatory tests (jackknife by quarter of expiry, t on K - 1 df; D4)

| Test | HR (95% interval) | p | Holm |
|---|---|---|---|
| C1 | 0.971 (0.748 to 1.259) | 0.8175 | not significant |
| C2 | 0.755 (0.396 to 1.439) | 0.3833 | not significant |
| C3 | 0.948 (0.699 to 1.285) | 0.7235 | not significant |
| C4 | 1.114 (0.959 to 1.294) | 0.1543 | not significant |

## Variants for C1 (estimates and intervals only)

| Variant | HR (95% interval) | Events |
|---|---|---|
| S1 | 0.872 (0.645 to 1.179) | 1,936 |
| S2 | 1.004 (0.742 to 1.360) | 1,683 |
| S3 | 0.960 (0.725 to 1.272) | 1,205 |
| S4 | 1.029 (0.828 to 1.279) | 2,245 |
| S5 | 0.990 (0.734 to 1.336) | 1,762 |
| S6 | 1.049 (0.777 to 1.417) | 1,762 |
| S7 | 0.851 (0.573 to 1.264) | 1,428 |
| S8 | 1.017 (0.771 to 1.341) | 1,831 |
| S9 | 0.888 (0.702 to 1.123) | 1,762 |
| S10a | 0.971 (0.755 to 1.247) | 1,762 |
| S10b | 0.971 (0.783 to 1.203) | 1,762 |
| S10c | 0.971 (0.784 to 1.201) | 1,762 |
| S11 | 1.426 (0.597 to 3.406) | 170 |
| S12 | 1.034 (0.547 to 1.954) | 1,762 |
| S13 | 1.063 (0.883 to 1.281) | 3,137 |
| S14 | 1.111 (0.879 to 1.405) | 2,429 |
| S15 | 0.987 (0.757 to 1.287) | 890 |
| S16 | 0.999 (0.727 to 1.374) | 2,014 |
| S17 | 0.903 (0.679 to 1.202) | 1,949 |
| S18 | 0.981 (0.772 to 1.246) | 1,762 |
| S19 | 0.934 (0.666 to 1.310) | 1,567 |
| S20 | 0.998 (0.499 to 1.997) | 1,762 |
| S21 (pre-registered quarter-clustered estimator) | 0.971 (0.786 to 1.199) | 1,762 |
| S22 (wild cluster score bootstrap-t) | 0.971 (0.729 to 1.219) | 1,762 |

Placebo PL1: HR 0.915 (0.666 to 1.256)

Placebo PL2: HR 1.035 (0.661 to 1.620)

No result is a statement about the safety of any building, owner or inspector.
