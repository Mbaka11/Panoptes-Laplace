# Synthetic App Privacy Report inspection spike

## Status

An isolated, dependency-free Python experiment. It exercises the documented shapes of Apple's `access` and `networkActivity` records using invented fixtures. It is **not** a native collector, production importer, canonical event schema, database, encrypted transfer system, or participant-workspace security boundary.

No participant data has been used. The CLI accepts no input-file paths: `--demo` reads only [the bundled synthetic fixtures](fixtures/app_privacy_report/README.md). The Python functions accept bytes for synthetic tests; that interface is not authorization to process real exports before [the real-data gate](../docs/collection-probe.md#real-data-gate--separate-from-the-build-gate) is satisfied.

## Run on Windows or the Mac later

Python 3.10 or newer, standard library only. No installation or external service is needed. From the repository root:

```bash
python -m unittest discover -s tests -v
python -m spikes.app_privacy_report --demo
python -m spikes.app_privacy_report --demo --coverage
```

On a Mac where the interpreter is named `python3`, use `python3` instead. This is independent of the still-pending `sw_vers` / `xcodebuild -version` preflight. Test execution on Windows is not a Mac or iPhone validation claim.

The demo returns two distinct snapshots and identifies the third input as a byte-identical repeat of the first. It contains one complete ten-minute interval and two independently incomplete interval fragments. The network aggregates retain their original five and eight hit counts in memory; the summary does not add them or produce an invented three-hit delta.

Exit codes: `0` for a demo without error-severity diagnostics (warnings can remain); `1` for reported error-severity diagnostics; `2` for CLI usage or fixture-loading/bounds errors. Warnings and supported-subset status are not proof of complete source-schema support.

## What the experiment does

- Retains original bytes, a content digest, record line numbers, raw lines, and parsed dictionaries in memory.
- Requires known record types to satisfy a small documented-field validation subset.
- Preserves unknown fields and record types with visible diagnostics rather than silently dropping them.
- Keeps malformed/non-object lines in line accounting; rejects duplicate JSON keys, nonfinite numeric values, unsupported numeric sizes, and invalid input encoding.
- Pairs resource boundaries only inside one snapshot when the ID, actor/category context, and endpoints are unambiguous.
- Leaves incomplete, reversed, or ambiguous intervals without an invented duration.
- Preserves network records as aggregates, not individual requests, browsing events, or viewed content.
- Preserves each distinct snapshot and its original input position. Exact repeated bytes are compared directly, not deduplicated solely on a content hash; there is no persistent import state.
- Never infers a report's full collection window or generation time from contact first/last timestamps or file metadata.
- Emits a summary containing counts, line references, and fixed diagnostic codes, not source identifiers, domains, raw lines, or content hashes.

`summary()` is a reduced diagnostic view, not a proven anonymization method. In-memory `Snapshot`/`Record` objects deliberately contain the source values; do not log or serialize them as though sanitized. The raw bytes are authoritative for exact representation, including numeric text; parsed dictionaries use Python numeric types and are not a lossless production numeric model.

## Opt-in synthetic coverage report

`--demo --coverage` emits `Inspection.coverage_report()` as JSON instead of the default summary. `--coverage` requires `--demo`; neither mode accepts participant files. The `synthetic-coverage-v1` marker versions this experimental report, **not** an approved production schema. The synthetic evidence label describes the allowed scope of this spike, not an input-authenticity check.

For each distinct artifact, it reports:

- Supported, invalid, and unsupported source-line references, with data availability and diagnostics kept separate. No nonblank records, no supported records, and a supported subset are distinct states; none establishes full source compatibility.
- Access-boundary and network-aggregate record counts with explicit counting units. They are not counts of user actions, page views, or unique requests.
- Earliest/latest supported timestamps separately for access boundaries and network contact aggregates, normalized to UTC. Every tied endpoint retains its source line and field; original offset strings remain in the source records.
- Complete, incomplete, ambiguous, and reversed interval groups with source lines. Only complete intervals have a duration. Supported endpoints can contribute to timestamp extrema even when their interval group is ambiguous or reversed; extrema do not establish a valid activity duration.
- A one-based unique snapshot index and the first original input position. Duplicate pairs also use original input positions, so interleaved repeats cannot shift a source reference to the wrong artifact.

Device support, provisioning, OS authorization, and actual source-export success remain untested/not observed. Recording enablement, the full collection window, source generation time, and missing periods remain unknown; freshness is not evaluated. Blank inputs do not establish denial or zero real-world activity. Timestamp extrema are **not** the export window, uninterrupted coverage, foreground app usage, or evidence of attention. No wall-clock or file-mtime inference, completeness percentage, total network hits, or cross-snapshot delta is produced. This one source does not establish the collection lab's multi-domain coverage target.

Unlike the default summary, this opt-in report discloses source timestamps and interval durations. It still omits domains, app identifiers, raw lines, and content hashes. **Neither output is an anonymization or safe-sharing guarantee.** Reporting uses only in-memory values and stdout; no report files are written by the CLI.

## Conservative parsing bounds

- Up to 16 input snapshots per call.
- Up to 4 MiB per snapshot and 16 MiB total, including duplicate inputs.
- Up to 10,000 physical lines per snapshot and 64 KiB per line.
- Integer literals limited to 64 decimal digits; nonfinite floats are rejected.
- UTF-8, optional initial BOM, LF or CRLF lines; JSON whitespace-only lines are counted separately.
- Timestamps require a date/time, explicit `Z` or numeric offset, and no more than six fractional digits. Both the local value and its UTC instant must fit Python's year 1–9999 range. Unknown `-00:00` offsets, naive times, leap seconds, finer precision, and UTC overflow are not accepted by this spike.

A diagnostic means a value is outside this experiment's supported subset; it does not establish that every possible Apple export uses only this subset. Size/encoding limits fail the call with fixed errors. Unknown but valid objects remain inspectable. The source's real format still needs device validation.

This is bounded synthetic-test code, not a hardened parser for arbitrary untrusted archives. There is no archive extraction, HTML rendering, dynamic execution, network I/O, credential handling, or raw-data persistence. Python may create ordinary ignored bytecode caches.

## Coverage against the collection protocol

| Case | Demonstrated scope | Not demonstrated |
|---|---|---|
| APR-02 | Documented subset validation, source semantics, and source-line/timestamp coverage reporting using synthetic inputs | Real export compatibility, measured collection completeness, or production import |
| SYN-01 | Complete/incomplete/ambiguous intervals within a snapshot | Exact activity duration from incomplete or cross-snapshot boundaries |
| SYN-02 | One network aggregate stays one record | Unique requests, page views, or payload contents |
| SYN-03 | Overlapping snapshots remain separate | Reconciliation of rolling totals into unique traffic counts |
| SYN-04 | Repeated byte-identical artifacts identified within one call | Persistent import idempotency or cross-participant deduplication |
| SYN-05 | Malformed JSON, unknown data, strict numeric types, and visible diagnostics | Full forward-compatible validation of all Apple record variants |
| SYN-06 | Offset-aware time comparison, missing/reversed/unsupported times | A final canonical temporal schema |

SYN-07 through SYN-10 are covered separately by [workspace semantics](workspace-semantics.md); native capability tests, real-data transfer, and the local explorer remain unimplemented/untested by this spike. See [the synthetic run record](../docs/results/app-privacy-report-synthetic.md).

## Inspiration and next evidence

This experiment borrows Foundry's **lineage principle**, not its implementation: a derived interval can point back to its source lines, and unsupported data remains visible. See [the inspiration review](../docs/inspirations-and-collection-patterns.md).

The coverage report extends the existing D-028 experiment without selecting another collector or a UI/storage framework. The next source evidence is a participant-controlled export inspected under a separately chosen protection/transfer procedure. Until then, do not claim compatibility with the reported iOS 26.6.1 device or extend this parser into a broad surveillance collector.

Reference: Apple, [Inspecting app activity data](https://developer.apple.com/documentation/network/inspecting-app-activity-data), checked through its public [DocC representation](https://developer.apple.com/tutorials/data/documentation/network/inspecting-app-activity-data.json). No Apple SDK or third-party code is included.
