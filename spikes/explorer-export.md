# Explorer export: parser results to the explorer contract (provisional)

## Status

`spikes/explorer_export.py` maps the **output of the existing parser spikes**
(`app_privacy_report`, `account_export_audit`) into the provisional
`persona-contract-0.1-provisional` document (`{meta, records}`) that the explorer
prototypes read, and validates any such document. It never re-parses raw files. It is
demonstration code and **not a production schema** (D-040); the contract will change when
real exports arrive. Synthetic only: stdlib, no network, no persistence beyond one JSON file.

```bash
python -m spikes.explorer_export --fixtures
python -m spikes.explorer_export --fixtures --out prototypes/explorer-cinematic/data/fixtures-workspace.json
python -m unittest discover -s tests -v
```

The default prints a short summary (counts per type, validation result), not the document.

## What is mapped

| Parser output | Contract records |
|---|---|
| APR `Inspection`/`ImportResult` + `ImportLedger` | `ImportBatch` (digest, ledger counts, fixed fixture import time, observed extent, issue codes), `ResourceAccess`, `NetworkAggregate`, `App`, `Domain`, `Source` |
| APR duplicate inputs / ledger matches | `ImportBatch` with `status` `duplicate_skipped` or `already_imported_ledger`, plus `DUPLICATE_OF` link |
| APR `reconcile_network_aggregates` | `CONTACTED` link (app to domain) with evidence ids, `reconciliation_flags`, `consistent`, `latest_observed_id` |
| Account `Audit` list | `ImportBatch`, `AccountActivity`, `Domain` (host of `titleUrl`), `Source` |

Invariants kept: `evidence_class` is one of five; every non-link record has
`provenance {source, method, method_version, line_or_record}` (source file and line); unknown
values use the token `"unknown"`, never 0; `NetworkAggregate.summable` is `false` and
aggregates are never summed or differenced; incomplete access intervals keep an `unknown`
start or end and an `unknown` duration; a duplicate import adds no records and gets a
`DUPLICATE_OF` link. Source records say `coverage_status: "unknown"`, `missing_periods: []`
with `missing_periods_status: "unknown"` (nothing is declared), and `latest_event_time` is the
latest observed record time, not freshness. `meta.window` is the observed record extent
(`basis` says so), not a collection window. Times are normalized to UTC.

## Validator

`validate_contract(doc) -> list[str]` checks: unique ids; every reference field
(`*_id`, `from`, `to`, `duplicate_of`, evidence lists) resolves or is `unknown`; evidence
class allowed; one `workspace_id`, equal to `meta.workspace_id`; `meta.synthetic` boolean;
time strings parse or are `unknown`; no number where a sibling `*_status` says
unknown/missing/invalid/not_reported; no numeric duration or invented end/start on incomplete
intervals; network aggregates not summable; duplicate batches have their link;
`type_counts` match. Problems name record ids only, not source values. It passes on the
existing `prototypes/explorer-concept/data/persona.json` (tested, file unchanged).

## Output location

`--out` refuses any path inside the repository except `prototypes/<name>/data/`, mirroring
the repo-path refusal of `ImportLedger`; an invalid document or one over 240 KiB is not
written (the write is atomic). Checked-in output:
`prototypes/explorer-cinematic/data/fixtures-workspace.json` (about 22 KB; the guard limit is 256 KiB).

## UI consumption

The UI loads the file as it loads `persona.json` and reads `meta.type_counts` and `records`.
Fields it must treat as optional because fixtures cannot provide them: Place, location,
health, calendar, finding and correction records; `meta.city`/`bounding_box`; Source
`missing_periods` content; `ImportBatch.window_start/window_end` (here `observed_extent`
and `collection_window: "unknown"`); `ResourceAccess.endpoint_domain_id` and `App.display_name`
(`unknown`). Time fields may hold the string `unknown` and must not be parsed blindly.

## Gating a future real-data path (not implemented)

There is intentionally no raw-participant-file argument. A real path would need a new
decision plus: protected storage and encrypted transfer (transfer package spike) established
first; the ledger and output outside the repository; a workspace id issued by the workspace
layer, with one workspace per document; `synthetic: false` set only by that path; participant
inspection and deletion; and the pre-commit guard still blocking real data in Git.
