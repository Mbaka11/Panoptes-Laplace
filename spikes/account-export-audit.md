# ACC-01 synthetic account-export audit spike

Status: synthetic preparation only. The record shape is INVENTED to resemble a
Takeout-style activity list (JSON list; `title`, `time`, `products`, optional
`titleUrl`, `details`, `durationSeconds`). The real provider schema, field meanings,
retention window, and completeness are unverified. This is not a production schema or
connector.

## Run (repository root)

    python -m unittest discover -s tests -v
    python -m spikes.account_export_audit --demo
    python -m spikes.account_export_audit --demo --provenance

The CLI reads only the bundled fixtures in `spikes/fixtures/account_export/`.

## What it reports

- Field status for viewed content, searches, interactions, timestamps, duration:
  `present`, `absent`, or `unknown` (no usable records, or unclassified records could hide it).
- Category assignment uses a synthetic title-prefix heuristic ("Searched for", "Watched",
  "Liked", ...). Real exports need documented field meanings instead.
- Missingness counts for title, time, products, titleUrl, durationSeconds
  (an unparseable time counts as missing).
- UTC timestamp minimum and maximum over valid timestamps.
- Provenance: 0-based record index and 1-based physical line per issue.
- Malformed, non-object, or unknown-field records are reported with fixed issue codes
  and never silently dropped. Untrusted values are not echoed (unknown field names pass a
  safe-name filter else `<redacted>`). Parsing stops at the first malformed element and
  marks the parse incomplete; later records are then unknown, not absent.
- Repeated import: a canonical-content hash (formatting and key order independent)
  flags a later identical import as `duplicate_import`; its records are excluded from
  counts. Overlapping but non-identical exports are NOT deduplicated.

## Boundaries

- Duration is counted only from an explicit `durationSeconds`. Gaps between events never
  produce dwell time. A viewed-content record never implies scroll depth. Output carries
  `dwell_time_inferred: false`, `scroll_depth_inferred: false`.
- Collection window and export completeness are always `unknown`.
- Not an anonymization or security boundary; no persistence, transfer, or ontology import.
- Limits: 4 MiB input, 10,000 records.
