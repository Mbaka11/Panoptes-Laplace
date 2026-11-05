# Result: transfer package lifecycle, synthetic

- **Cases:** XFR-S1 to S5, S7 to S10, S12, S13 (partial); ISO-S1/S2 (partial); DEL-S1/S5 (partial)
- **Execution status:** executed (Windows, Python standard library, `python -m unittest discover -s tests -v`)
- **Evidence class:** synthetic only. No simulator, no physical device, no Mac.
- **Outcome:** 41 new tests pass; full suite 139 passes.
- **Spike:** `spikes/transfer_package.py`; notes in `spikes/transfer-package.md`.

**The payload is NOT encrypted. HMAC-SHA256 is a stand-in for authenticated integrity. No ciphersuite is selected (D-031 selects none).** Nothing here shows confidentiality or that any real design is secure.

## What the tests showed

| Case | Result |
|---|---|
| XFR-S1/S2 scope | Only selected sources and the window (from inclusive, to exclusive) were packaged and imported; out-of-scope records in an authenticated package are rejected |
| XFR-S3/S4 tamper | Payload bit flip rejected; payload edit with recomputed file digest rejected by the keyed tag; manifest, header and tag edits rejected; wrong-key forger with an enrolled ID rejected |
| XFR-S5 completeness | Missing file, extra file, and file swapped from another package rejected |
| XFR-S7 / ISO-S2 | Wrong workspace and wrong recipient rejected; editing the manifest to match is an integrity failure |
| XFR-S8 | Unknown sender rejected. Limitation: with a symmetric stand-in this is enrollment lookup, not real sender authentication |
| XFR-S9 | Future version, validly tagged old version (downgrade), rewritten header version, and unknown algorithm rejected |
| XFR-S10 | Exact re-import returns `duplicate`, no state change |
| XFR-S12 | Replay of an old package: known ID is a duplicate; unseen ID with a stale sequence is rejected; deleted record not resurrected (tombstone also blocks a newer package) |
| XFR-S13 | Generic messages; no record values in exceptions, audit text, ledger or tombstones |
| ISO-S1 (partial) | Colliding source IDs in two workspaces stay separate; deletion in one leaves the other |
| DEL-S1/S5 (partial) | Sender and Mac temp dirs deleted on success and on failure with absence checked; retained and unverified locations listed |

## Chosen replay policy

R1 package-ID ledger plus R3 per-sender monotonic sequence, with ID-only tombstones and upsert. Known costs: out-of-order legitimate packages are rejected; a phone counter reset needs re-enrollment (not modeled).

## Not covered

Confidentiality, AEAD, real signatures or pairing, key storage and rotation, chunk ordering and nonce uniqueness (XFR-S14), crash sweep (DEL-S2), key retirement (DEL-S3), derived-data cascade (DEL-S4), aggregate overlap (XFR-S11), ISO-S3 to S5, and all device or Mac behavior (XFR-D1). In-process cleanup checks do not establish erasure on real storage.
