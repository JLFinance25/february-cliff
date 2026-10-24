# Family 2 repeat check (simulated), 24 repeats per world

Replaces the 8-repeat table in section 8 of `gate2-simulated-check.md`. Clean permit tables, corrected simulator (permit chains no longer capped at 14, which had created fake 'ended' rows in the 90-day-term world).

| World | Planted HR | Repeats | Mean estimate | Mean log-HR error | Coverage | SD of log estimate |
|---|---|---|---|---|---|---|
| 90-day terms | 0.75 | 24 | 0.735 | -0.020 | 0.92 | 0.111 |
| 90-day terms | 1.00 | 24 | 1.078 | +0.075 | 0.79 | 0.142 |
| annual terms | 0.75 | 24 | 0.744 | -0.008 | 0.83 | 0.135 |
| annual terms | 1.00 | 24 | 1.017 | +0.017 | 0.92 | 0.137 |
