# Explorer export synthetic result

## Execution scope

- **Date:** 2026-11-10.
- **Case:** D-040, mapping parser-spike results to the provisional explorer contract.
- **Environment observed:** Windows / Git Bash, Python 3.10, stdlib only.
- **Evidence class:** synthetic test execution on bundled fixtures; no device, export, or participant data.
- **Outcome:** 229 tests passed (200 before plus 29 new in `tests/test_explorer_export.py`); `python -m tools.precommit_guard --all` exited 0.
- **Limits:** fixture shapes are invented; this shows the mapping preserves parser semantics, not that real iPhone or provider exports will map this way.

## Reproduce

```bash
python -m unittest discover -s tests -v
python -m spikes.explorer_export --fixtures
python -m spikes.explorer_export --fixtures --out prototypes/explorer-cinematic/data/fixtures-workspace.json
python -m tools.precommit_guard --all
```

## Observed results

| Observation | Result |
|---|---|
| Workspace / flags | `ws-demo-02`, `synthetic: true`, fixture-derived notice |
| Type counts | Source 2, App 1, Domain 3, ImportBatch 5, ResourceAccess 3, NetworkAggregate 2, AccountActivity 10, Link 6 |
| Access intervals | 1 complete (600 s), 1 `missing_end` (end and duration `unknown`), 1 `missing_begin` (start and duration `unknown`); none joined across snapshots |
| Network aggregates | hits 5 and 8 kept separate, `summable: false`; one `CONTACTED` link, `combine: latest_snapshot_only_never_sum`, latest observed `net-s2-01`; no 13 and no delta |
| Duplicates | the repeated APR snapshot and the reformatted account export each become a `duplicate_skipped` batch with `records_added: 0` and a `DUPLICATE_OF` link; no activities duplicated |
| Account activities | 10 (the non-object element is only an issue code); all durations `unknown`; one invalid time kept with `event_time: unknown`; negative duration not converted |
| Sources | `coverage_status` unknown, no declared missing periods; APR latest event `2026-01-03T09:00:00Z` |
| Validator | Clean on the output; each violation class (duplicate id, dangling reference, bad class, second workspace, zero for unknown, invented end, missing synthetic flag, bad time, summable aggregate, duplicate without link, count mismatch) is detected in tests |
| `persona.json` | Passes `validate_contract` unchanged |
| Determinism | Two builds are byte-identical and match the checked-in file; about 22 KB, below the 240 KiB test bound |
| CLI | Summary by default; repo paths (including `prototypes/x.json` and non-data folders under a prototype) refused with exit 2; outside-repo and `prototypes/*/data/` accepted; no raw-input argument |

## Contract gaps

Fixtures cannot supply Place, LocationSample, Visit, Trip, ActivityInterval, DailyHealthAggregate, CalendarEvent, Finding, or Correction records, nor `meta.city`/`bounding_box`. APR carries no endpoint or app display name, so those are `unknown`. Import time exists only for APR (fixed fixture time via the in-memory ledger); account batches use `unknown`. The persona's `window_start`/`window_end` on batches and `Source.snapshots` windows are replaced by `observed_extent`/`snapshot_extents`, because contact times are not collection windows.
