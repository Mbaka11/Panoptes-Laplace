# Workspace semantics synthetic result (SYN-07 to SYN-10)

## Execution scope

- **Date:** 2026-11-04 (local clock, not independently witnessed).
- **Cases:** SYN-07, SYN-08, SYN-09, SYN-10, synthetic in-memory semantics only.
- **Environment:** Windows, Python 3.10+ standard library.
- **Outcome:** full suite `python -m unittest discover -s tests` reported 84 tests, all passed (61 existing plus 23 new in `tests/test_workspace_semantics.py`).
- **Evidence class:** synthetic test execution, not simulator or physical-device evidence.
- **Participant data, credentials, devices, external services:** none.
- **Method version:** uncommitted working-tree spike; not a production schema version. No file hashes recorded.

## Reproduce

```bash
python -m unittest discover -s tests -v
```

Implementation and limits: [the spike guide](../../spikes/workspace-semantics.md).

## Observed results

| Case | Observation |
|---|---|
| SYN-07 | Empty query with write status `sharingAuthorized` or `sharingDenied`: 0 rows, measured value and read authorization both `unknown`, write status preserved separately, no denial wording. Missing write status is `unknown`. Rows, when present, are copied and read authorization is still not asserted. |
| SYN-08 | Planned event without a confirming link is `scheduled_context`; overlapping observation is only a possible overlap; explicit link yields `observed_activity`; observed duration remains `unknown` in all cases. Events lacking times do not error. |
| SYN-09 | Same source ID returned different content per workspace; unknown workspace or ID raises; mutation of returned content does not affect the store; cross-workspace parent links rejected; corrections and exports did not leak across workspaces. |
| SYN-10 | Deleting a source applied the declared policy through source, feature, finding, cache, and export; removed nodes become unreadable, invalidated ones return only a status; the delivered export was listed as an unverified copy and an undelivered one was not; invalid or incomplete policy changed nothing; an unrelated source survived; a multi-parent finding was invalidated when either parent was deleted; the other workspace's full state was identical before and after. |

## What was not covered

- No real HealthKit, EventKit, or iOS behavior; the Health and calendar inputs are hand-written dictionaries.
- No persistence, encryption, key handling, file or backup deletion, concurrency, or authorization checks; isolation is logical within one Python object only.
- No verification or recall of external copies; "unverified" is a reporting state, not a deletion mechanism.
- No recomputation of findings after deletion, no real-world matching of observations to events, and no choice of the default deletion policy.
- No workspace-isolation claim for any future implementation. Native/device cases and the real-data gate remain pending; the collection lab is not complete.

## Cleanup

No data was written outside Python's ignored bytecode caches. No commit was made by this work.
