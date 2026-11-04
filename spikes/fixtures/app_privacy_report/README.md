# Synthetic App Privacy Report fixtures

These files are hand-authored examples using Apple's documented `access` and
`networkActivity` record shapes. They contain **no participant data** and were
not captured from an iPhone.

- `snapshot-a.ndjson`: one complete location-access interval, one incomplete
  photos-access interval, and one domain-contact aggregate with five hits. An
  invented `futureMetadata` field exercises preservation of unknown fields.
- `snapshot-b.ndjson`: an end-only photos-access boundary and a second aggregate
  with eight hits, whose contact timestamps overlap the first snapshot's.

The inspector must not join access boundaries across snapshots, report thirteen
unique network requests, or infer a three-request delta. Contact first/last times
are not the export's generation time or full collection window. Repeating an
identical file exercises artifact deduplication only, not persistent import
idempotency or participant isolation.

Identifiers are invented, `example.com` is a reserved example domain, and dates
are illustrative. See [the spike documentation](../../app-privacy-report.md) for
scope and run commands.
