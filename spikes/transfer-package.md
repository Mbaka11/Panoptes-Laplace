# Transfer package lifecycle spike (synthetic)

**NOT ENCRYPTED. NOT A SECURITY DESIGN.** The payload is plaintext. Python's standard library has no AEAD, so HMAC-SHA256 stands in for "authenticated integrity" only. It is not the selected ciphersuite (D-031 selects none), gives no confidentiality, and, being symmetric, only imitates sender authentication. This spike tests package *lifecycle logic* (binding, rejection, replay, scope, staging inventory) for XFR-01, ISO-01 and DEL-01. It does not test confidentiality, key storage, or any Apple API.

Files: `spikes/transfer_package.py`, `tests/test_transfer_package.py`. Demo: `python -m spikes.transfer_package --demo` (synthetic `com.example.*` data; key generated in memory, never written).

## What it models

- **Manifest** binds format version, package ID, sender ID, recipient ID, workspace ID, sender sequence number, source/date scope (from inclusive, to exclusive) and a SHA-256 digest and size per file. A cleartext header (version, algorithm, package ID, sender ID) is also covered by the tag. Tag = HMAC-SHA256 over header plus manifest under the enrolled sender's key.
- **Import order:** version/algorithm, enrolled sender, tag, context agreement, workspace, recipient, exact file set, per-file digests (in an isolated temp dir), record scope check, replay policy, then atomic commit. Any failure commits nothing and does not advance the ledger.
- **Failures** are generic classes (`malformed`, `unsupported_version`, `unknown_sender`, `integrity_failure`, `wrong_workspace`, `wrong_recipient`, `file_set_mismatch`, `scope_violation`, `replay_rejected`) with fixed messages; audit text holds IDs and class names, never record values.
- **Scope selection:** only selected sources and the date window enter the package; the importer also rejects any record outside the declared scope.

## Replay and idempotency policy: R1 + R3

Chosen from design doc section 6: **R1 package-ID ledger plus R3 per-sender monotonic sequence**, with ID-only deletion tombstones and key-based upsert for overlap.

- R1: a repeated package ID returns `duplicate` with no state change (exact re-import is idempotent).
- R3: an unseen package ID whose sequence is at or below the sender's last accepted one is rejected, so an old package cannot be replayed after newer data or a deletion.
- Tombstones (source and record ID only) stop even a newer overlapping package from resurrecting a deleted record.
- Upsert by (source, record ID) reports new/unchanged/changed so overlapping packages do not inflate counts (a minimal stand-in for R2, not a full SYN-03 solution; aggregate versus event handling is not modeled).

Why: R1 alone misses a re-export under a new ID and cannot stop stale-package replay; R3 closes that gap and is the only option that addresses T5 after deletion. Trade-offs, tested and documented: legitimate out-of-order delivery is rejected, and a restored or replaced phone that resets its counter needs an explicit re-enrollment step (not modeled). Ledger entries hold no sensitive values.

## Staging / plaintext inventory (for DEL-01)

`StagingLog` records each copy this spike creates: sender-side plaintext export temp dir (deleted, absence checked with `os.path.exists`), the package file itself (plaintext, retained until the participant deletes it), Mac validation temp dir (deleted on success and on failure, absence checked), and the workspace store (retained pending a deletion policy). `inventory()` also appends locations the spike cannot observe, each marked `unverified`: transport channel, Files/Downloads copy, backups, Spotlight/indexes, swap/crash reports, recipient-derived copies. This lists copies; it does not prove erasure on flash storage or APFS.

## Limitations

- No confidentiality; no AEAD; no key agreement; no real signatures (a shared HMAC key per enrolled sender is the stand-in, so a compromised importer could forge packages).
- No nonce, chunking, ordering or compression concerns; the file set is a dict, not a byte format.
- No key rotation, revocation, pairing, or lost-phone sequence reset.
- Failure classes are distinguishable; whether an oracle matters locally is open.
- Cleanup is checked in-process only; no crash-sweep simulation (DEL-S2), no persistence, no device or Mac evidence. Mac preflight (D-027) remains pending.
- Does not touch SYN-03 aggregates, ISO-S4/S5, or DEL-S4 cascade beyond a small cross-workspace collision check.
