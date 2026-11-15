# The February cliff: do NYC's facade-inspection deadline waves slow repairs?

**Status: results final; not peer-reviewed.**

A pre-registered test on public NYC Open Data.

NYC buildings over six stories must have their facades inspected once per five-year cycle, in three deadline groups
whose filing windows all end on Feb 21. Engineers' reports pile up around those dates. My question is whether that
pile-up ("a wave") slows the repairs that follow. The test was written down before any repair duration was looked at.

## What was found

- **Repair clearance (the main test).** Across 4,828 UNSAFE facade filings from cycles 8 and 9, a busier city was not
  linked to slower repair clearance. Hazard ratio 0.991 per wave unit of workload, 95% interval 0.856 to 1.148. The
  whole interval sits inside the pre-registered "no meaningful effect" band of 0.80 to 1.25.
- **The check meant to tell a shared bottleneck from slow last-minute owners (early filers only) was inconclusive**
  (1.235, 0.797 to 1.914). So the study does not separate those two explanations.
- **Sidewalk-shed permits (the secondary, weaker test).** 0.971 (0.748 to 1.259), inconclusive. It cannot rule out a
  20% to 25% slowdown, because pre-2026 shed permits ran about a year and blur when a shed came down.
- No test was significant. No result here is a statement about the safety of any building, owner or inspector, and
  nothing is reported at building level.

Read the full report: [`writeup/REPORT.md`](writeup/REPORT.md).

## Things a careful reader should know first

- **Gate 1 was exploratory and ran before pre-registration.** The check that deadline waves exist (Oct 16, 2026) came
  first. Several design choices were informed by facade filing counts, never by repair durations. The report lists them.
- **The headline outcome was switched from sheds to repair clearance before any outcome data was opened.** The reason
  and the record are in the report (section 7, point 4) and in `PREREG.md` section 1.
- **Four deviations (D1 to D4) were logged after the lock and before any real analysis.** D4 widened the error bars
  (a delete-one-quarter jackknife replaced the quarter-clustered estimator) after a simulation showed the original
  intervals were too narrow.
- **Verification status.** The report's numbers were checked against the runner's own output files by Claude (30
  numbers re-checked on Oct 24, 2026), not by me or any other person. Treat that as UNVERIFIED until stated otherwise
  here.
- **I have not read the full pre-registration.** It was drafted and locked by Claude. Before the first real run
  (Oct 22, 2026) I read a plain-English summary of it. The header of `PREREG.md` says "Not yet reviewed" as of the lock.
- **Some copied files carry older wording.** The AI-use line inside `PREREG.md` (locked, so unchanged) and inside the
  frozen code's output template reads "directed, checked and approved". That wording is out of date. The statement
  that applies to this repository is the "Acknowledgments and AI use" section at the end of this page.
- **"Main session" and "code session" in the logs and notes** mean the Claude chats that directed the work and wrote the
  code.

## Repository contents

| Path | What |
|---|---|
| `writeup/REPORT.md` | The report (Family 1 repair clearance, Family 2 sheds, limits) |
| `PREREG.md` | The pre-registration with the deviations D1 to D4 added at the end |
| `PREREG-as-locked-2026-10-17.md` | The pre-registration text exactly as it was locked on Oct 17, 2026 |
| `PLAN.md` | The project plan (the "Who gets it" section of the private working copy is left out) |
| `src/` | The analysis code, frozen before any real run |
| `writeup/gate2-family1-results.md`, `writeup/gate2-family2-results.md` | The runner's own output (aggregates only) |
| `writeup/gate0-dob-fisp-study.md`, `writeup/gate2-calibration.md`, `writeup/gate2-simulated-check*.md` | Prior-work check and simulated-data checks |
| `figures/` | February-cliff charts and the aggregate tables behind every result |
| `data/raw/SOURCES.md` | Where each dataset came from, when, the terms, and file hashes |
| `WORKLOG.md` | Who did what and when |

## Reproducing it

Raw data are **not** in this repository (they are large, and the DOB facade file names building owners and inspectors).
Re-download them with `src/download_xubg_57si.py` and `src/download_open_data.py`; dataset IDs, pull dates and file
hashes are in `data/raw/SOURCES.md`. The datasets are updated daily, so a new pull will not match the Oct 2026
snapshots exactly. The first processing step (`src/process_facades.py`) drops every owner and inspector field.

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
```

The real runs need a go-file (`data/GO_family1.txt`, `data/GO_family2.txt`) and then
`.venv/bin/python -I src/gate2_run.py --real --family 1` (or `--family 2`). Family 1 took 52 seconds.

## Locked and frozen versions

This repository is a clean single-commit copy, so the commit IDs and tags quoted in the report belong to the authors'
private working repository and are not present here. What can be checked here:

- `PREREG-as-locked-2026-10-17.md` has SHA-256 `913117bca0587728085d71466a0c824b59df3123037d648dfa9077ff5a02ed6f`.
  Private commit 0140a58, tag `prereg-locked`, dated Oct 17, 2026.
- `PREREG.md` (with deviations added) has SHA-256 `1818c54bf9cd06ac6a4dcf3079964d6bbd5b9c8961696d78861d9951919b23d9`.
  It differs from the locked text only by the "Deviations" section at the end.
- `src/` is byte-identical to the private tags `gate2-code-frozen` (eb5c6dc, Oct 18, 2026) and `gate2-run-frozen`
  (87759a8, Oct 18, 2026) for the code files; the real runs on Oct 22, 2026 used `gate2-run-frozen` unchanged.

These dates and IDs cannot be proven from this repository alone. The private history exists and can be shown on request.

## Edits made to copied files for this public copy

- Nov 15, 2026 update: `writeup/REPORT.md` gained an abstract, download sizes in the data table, an "In real units" paragraph (an approximation, labelled), a "Who could use this" paragraph and the AI-tools and no-adult-help line; this README gained the same AI line and an intended-reader line. No number, test or finding changed.
- `writeup/REPORT.md`: removed the "PRIVATE DRAFT" line, the note that Jayden Ling had not checked the draft, and the
  editor's notes at the end; changed two phrases that named private files or sessions (limitation 4 and the start of
  section 8); added one line in section 10 about commit IDs. No number, test or finding was changed.
- `writeup/gate2-family1-results.md` and `writeup/gate2-family2-results.md`: the AI-use line was changed to an earlier
  short wording ("Drafted with Claude (AI); directed by Jayden Ling"). The "Acknowledgments and AI use" section below
  supersedes it. Nothing else was changed.
- `PLAN.md`: one header sentence reworded and the "Who gets it" section removed.
- `data/raw/SOURCES.md`: two phrases referring to private notes and internal approval levels reworded.
- `WORKLOG.md` is a new, shorter log written from the private one.

## Data and licenses

Data: NYC Department of Buildings and Department of City Planning via NYC Open Data (datasets `xubg-57si`, `rbx6-tga4`,
`ipu4-2q9a`, `64uk-42ks`), pulled Oct 17 and 18, 2026; aggregated and charted by the code in `src/`. The datasets list no license. The
terms check is in `data/raw/SOURCES.md` (two gaps are marked UNVERIFIED there). The data are provided without warranty,
so no figure here is an official DOB or DCP statistic.

Code (`src/`): MIT License, see `LICENSE`. Text and figures: CC BY 4.0, see `LICENSE-TEXT-CC-BY-4.0.txt`.

## Acknowledgments and AI use

I chose the question and directed the study. I decided to make it a project (Oct 17, 2026) and approved
the first real run on repair clearance and the run on shed permits (both Oct 22). Claude (Anthropic's AI assistant) wrote
the code and drafted the pre-registration, the report and this text under my direction. On Oct 26, 2026 I read and approved
this README and sections 1 and 7 of the report. Before the first real run I read only a plain-English summary of the pre-registration. The numbers were
checked against the result files by Claude, not by me.

AI tools used: Claude Sonnet 5.5 and Claude Opus 5.5 (Anthropic), run in Claude Code, Oct 16 to Nov 15, 2026. No teacher, mentor or other adult helped with this work; all help came from the AI tools named above.

Intended reader: the Department of Buildings staff who write the FISP rules and the City Council members who oversee them, when they decide whether the shared Feb 21 deadline needs to be spread out to protect repair times.
