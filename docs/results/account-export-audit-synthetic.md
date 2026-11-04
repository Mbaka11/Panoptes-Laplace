# ACC-01 synthetic result: account-export field-coverage audit

Date: 2026-11-04. Scope: synthetic fixtures only (`spikes/fixtures/account_export/`). This
does not show what any real service exports; real provider schema is unverified and no
participant export was inspected.

## Outcome on the bundled fixture (11 list elements)

| Item | Result |
| --- | --- |
| Records counted (objects) | 10; one non-object element reported, not counted |
| Viewed content / searches / interactions | present (4 / 3 / 1 records) |
| Timestamps | present (9 valid); 1 invalid or missing counted as missing |
| Duration | absent (no valid explicit field); not inferred |
| Timestamp range (UTC) | 2026-01-01T08:00:00+00:00 to 2026-01-06T08:00:00+00:00 |
| Reported issues | invalid_time, missing_title, unclassified_title, invalid_products, invalid_duration, unknown_fields, record_not_object |
| Reformatted copy | detected as duplicate_import; activity counts unchanged |
| Collection window / completeness | unknown |

## Tests

14 new tests in `tests/test_account_export_audit.py` (98 total in the repository, all passing):
statuses, missingness, extrema, line provenance, time-zone normalization, no dwell or
scroll inference, explicit duration, unknown vs absent, duplicate vs changed import,
malformed and truncated input, size limit, no echo of source values, CLI.

## Limitations

- Category detection is a synthetic title-prefix heuristic, not a source-defined meaning.
- Parsing stops at the first malformed element; later records are unknown.
- Overlapping non-identical exports and in-file duplicate records are not merged.
- Time-zone handling assumes explicit offsets; local-time strings are rejected.
- Real validation (ACC-01 on a participant-owned export: exporter version, format, window,
  documented field meanings) remains pending and requires the protected-transfer gates.
