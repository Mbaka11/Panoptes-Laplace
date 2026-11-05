# Synthetic demo persona and provisional explorer data contract

## Status

`spikes/synthetic_persona.py` deterministically generates **Subject EX-01**, a fictitious adult living 28 days (2026-03-02 to 2026-03-29, fixed UTC-05:00 as `Etc/GMT+5`) in the fictional city **Port Meridian**. Output: `prototypes/explorer-concept/data/persona.json`, for a future explorer UI concept prototype.

```bash
python -m spikes.synthetic_persona --out prototypes/explorer-concept/data/persona.json
python -m unittest discover -s tests -v
```

This is **demonstration data and a PROVISIONAL contract. It is not a production schema**, storage design, ontology decision, or evidence about any real person, device, or export format. Every name, coordinate, identifier, and number is invented. Coordinates lie in a bounding box over open ocean (lat 30.00 to 30.06, lon -40.06 to -40.00) and are fictitious; apps are `com.example.*`, hosts are `*.example`. The seeded generator (`SEED = 20260302`) yields byte-identical output; the file is compact JSON, under 240 KiB (the repository data-file guard limit is 256 KiB), enforced by a test. Density was thinned to meet that limit, so Location sampling is deliberately sparse.

Built-in dependencies in the data (for example, steps and evening activity) are generator choices, so findings illustrate presentation, not discovery.

## File layout

`{ "meta": {...}, "records": [ ...flat list... ] }`. `meta` carries contract version, status, window, bounding box, seed, `type_counts`, and the `unknown` token. All records share one workspace (`ws-demo-01`).

## Common envelope

`id`, `type`, `workspace_id`, `source_id`, `evidence_class` (observation | normalized_event | hypothesis | inference | prediction). Time-bearing types also carry `granularity` (point | interval | aggregate), `timezone`, `import_batch_id` (the `ImportBatch` holds `import_time`, kept separate from event time), and either `event_time` or `event_start`/`event_end`. `granularity` is omitted for entities, findings, and links. Non-link records carry `provenance {source, method, method_version, line_or_record}`.

## Object types

| Type | Class | Granularity | Notable fields |
|---|---|---|---|
| Source (7) | observation | n/a | support, provisioning, coverage_status, missing_periods[], record_count, latest_event_time, export_success, source-specific state (HealthKit `read_authorization: unknown`, `last_probe`) |
| ImportBatch (9) | observation | n/a | import_time, content_digest_sha256, status (`imported`/`duplicate_skipped`), duplicate_of, records_added |
| Place (6) | inference | n/a | label, lat, lon, radius_m, confidence |
| LocationSample | observation | point | lat, lon, accuracy_m |
| Visit | normalized_event | interval | place_id, interrupted_by_gap, match_confidence; bounds are first and last sample, not true arrival/departure |
| Trip | normalized_event | interval | from_place_id, to_place_id, mode, mode_confidence; evidenced by adjacent Visit samples and a Motion interval |
| ActivityInterval | observation | interval | activity_type, confidence |
| DailyHealthAggregate | observation | aggregate | steps (or `unknown`, `steps_status`), `heart_rate_resting` and `sleep_duration` = `unknown`, read_authorization `unknown` |
| CalendarEvent | observation | interval | role (`scheduled_context` or `observed_activity`), confirmed_by[], possible_overlap_with[], observed_duration `unknown` |
| App, Domain | observation | n/a | bundle_id (`com.example.*`), host (`*.example`) |
| ResourceAccess | observation | interval | app_id, category, endpoint_domain_id, endpoint_match (`matched`/`unmatched`), also_seen_in_snapshots |
| NetworkAggregate | observation | aggregate | app_id, domain_id, hits, snapshot_id, summable `false` |
| AccountActivity | observation | point | activity_kind (search/watch/like), title, duration_seconds `unknown` |
| Finding (4) | inference or hypothesis | n/a | finding_kind, statement, input_window, method, method_version, statistic, supporting_evidence_ids, contradicting_evidence_ids, uncertainty, confidence, status, causal_claim `false`, participant_correction, participant_review_status |
| Correction (1) | observation | n/a | target_id, correction_kind, participant_text, status |
| Link | varies | n/a | link_type, from, to, evidence_ids[] |

Finding kinds: `descriptive_pattern`, `correlation` (statement starts "CORRELATION, not causation", carries n and an approximate interval), `hypothesis` (awaiting evidence, no supporting ids), `null_or_insufficient` (reports numbers, a minimum-n rule, and no conclusion). For the null result, supporting ids are the evidence examined.

## Link types

VISITED (Visit to Place; evidence: samples), CORROBORATED_BY (Trip to ActivityInterval; evidence: trip, motion, neighbouring samples), CONFIRMS (Visit to CalendarEvent, explicit), ACCESSED_BY (ResourceAccess to App), CONTACTED (App to Domain; evidence: per-snapshot aggregates, `combine: latest_snapshot_only_never_sum`), SUPPORTED_BY / CONTRADICTED_BY (Finding to evidence; mirror the Finding id lists), CORRECTS (Correction to Finding), DUPLICATE_OF (ImportBatch to ImportBatch). Some relations (Trip endpoints, NetworkAggregate app/domain) are inline id fields rather than links.

## Invariants (tested)

- Output is deterministic; ids are unique; every link endpoint, evidence id, and inline reference resolves.
- A Finding never cites hypothesis, prediction, or inference records as evidence; an inference-class Finding cites at least one observation or normalized event; a hypothesis cites none.
- Absent measurements are `unknown`, never 0; an empty Health read leaves `read_authorization` unknown.
- Calendar events are `scheduled_context` unless an explicit CONFIRMS link exists; time overlap is only `possible_overlap_with`.
- NetworkAggregate snapshot windows overlap, are flagged `summable: false`, and are never summed; no total field exists.
- Deliberate gaps: no location on day 9; a locked-phone gap on day 17 (13:00 to 16:30) interrupting a Work visit; no step record on day 20; no APR snapshot for days 18 and 19. Motion continues on day 9.
- One duplicate APR snapshot import (same digest, `records_added: 0`, no records attributed).
- AccountActivity has no duration; viewed-content depth, dwell, and scroll are never inferred.
- All coordinates inside the fictitious box; only `com.example.*` and `.example` identifiers; no URLs or emails.

## Limits

Visits and trips are generated from a ground-truth plan, not recovered from noisy data. Sampling is sparse, motion confidence is categorical, and no sleep or heart-rate data exists by design. Nothing here verifies real Core Location, HealthKit, EventKit, App Privacy Report, or export behavior.
