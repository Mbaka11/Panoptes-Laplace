# Synthetic workspace-semantics spike (SYN-07 to SYN-10)

## Status

An isolated, dependency-free Python experiment in `spikes/workspace_semantics.py`. It encodes expected behavior for four semantic cases from [the collection probe](../docs/collection-probe.md#4-synthetic-semantic-cases-and-current-coverage) using invented data (`com.example.*`, `ws-a`, `ws-b`). It is **not** a production schema, storage design, encryption or access-control mechanism, or a security boundary. Record shapes (`rows_returned`, `role`, node kinds, policy values) are test vocabulary only and must not be adopted as a schema without a separate decision. Nothing touches a device, HealthKit, EventKit, disk, or the network.

Run from the repository root (Python 3.10+, standard library only):

```bash
python -m unittest discover -s tests -v
```

## Cases

| Case | Behavior encoded | Where |
|---|---|---|
| SYN-07 | An empty Health query returns zero rows, a `measured_value` of `unknown` (never 0), and `read_authorization` of `unknown`. A write status (for example `sharingDenied`) is kept as its own field and never converted into a read-denial claim or a read grant. Returned rows are kept as observations without aggregation. | `health_query_observation` |
| SYN-08 | A calendar event is `scheduled_context` unless an observation explicitly names it via `confirms_event_id`. Time overlap alone is reported as `possible_overlap_with`, not confirmation. Observed duration stays `unknown` even when confirmed. | `classify_calendar_events` |
| SYN-09 | Every operation names a workspace; the same source ID holds different content in two workspaces. Reads, derivation links, corrections, and exports are per workspace; cross-workspace links are rejected; returned content is a copy. | `WorkspaceStore` |
| SYN-10 | `delete_source` requires an explicit policy declaring `remove` or `invalidate` for each derived kind (feature, finding, cache, export); incomplete policies are rejected without change. Dependents are found by transitive parent links (any deleted parent suffices). Exports marked delivered are listed as `unverified_copies`. Corrections on removed targets are dropped; corrections on tombstones are kept and listed as orphaned. The other workspace is compared by deep-copy snapshot before and after. | `WorkspaceStore.delete_source` |

## Limits

- Isolation here is a logical property of one in-memory object, not process, storage, or cryptographic isolation. It demonstrates intended semantics for later implementations.
- The store cannot verify, recall, or delete copies outside itself. A `delivered` export is only a flag supplied by the test; the report states these copies are unverified, not that they were deleted.
- No secure erasure, backup, log, OS cache, or file-system remnant handling is modeled.
- Retaining a tombstone for `invalidate` is a policy option, not a recommendation; it reveals that an item once existed. The policy choice is open.
- Statistical derivations and finding recomputation after deletion are not modeled.
- Health authorization semantics are paraphrased from the project documents, not verified against a device or current Apple documentation here.
- Calendar confirmation is an explicit link in test data; how a real observation would be matched to an event is not decided.

See [the synthetic run record](../docs/results/workspace-semantics-synthetic.md).
