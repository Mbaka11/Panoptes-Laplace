# Transfer package design options

**Status:** PROVISIONAL design-options document. It selects nothing final: no cryptographic scheme, package format, key store, deployment target, or transport is adopted. It is recorded as provisional D-031 and informs the XFR-01, ISO-01, and DEL-01 cases in [the collection protocol](collection-probe.md). Nothing here has been implemented, built, or tested; the Mac preflight (D-027) is still pending.

**Scope:** the participant-initiated encrypted batch export from the iPhone to a local Mac workbench (D-008). Account exports and App Privacy Report files enter through a separate import/staging path (see section 7) but share the same Mac-side protections.

**Verification convention:** every statement tagged **[UNVERIFIED]** concerns an Apple API, platform behavior, or version availability that must be checked against the installed SDK, current first-party documentation, and a physical device before reliance. Documentation inspection is not runtime evidence. Cryptographic primitives named below are standard and public; the project must not invent its own constructions.

## 1. Inputs from existing documents

| Source | Requirement carried into this design |
|---|---|
| D-008 | Participant-controlled encrypted batch export in V1; no continuous sync, no cloud participant database. |
| Trust doc, V1 posture | Native NDJSON/CSV exports may be unencrypted. Before real transfer: protected staging, encrypted packaging/transport, key handling, retention, deletion of temporary copies. A share button establishes none of these. |
| Trust doc, isolation | A workspace identifier is not a security boundary. Packages identify exactly one workspace. Cryptographic separation and key management are undesigned. |
| Trust doc, sharing | A copy already decrypted by a recipient cannot be clawed back; communicate that limit and track deletion requests. |
| Architecture, export package | Manifest and schema version, workspace identifier, selected range and categories, consent/purpose metadata, events, provenance, integrity hashes, encryption metadata. |
| Probe, real-data gate | Protected storage/staging, tested encrypted transfer, key handling, integrity/authenticity, copy inventory, deletion including what cannot be recalled, and a guard against real data or secrets entering commits. |
| XFR-01 | Scope selection, validation, integrity/authentication, round-trip evidence. Tamper rejection, wrong-recipient/workspace handling, duplicate import, chosen replay/idempotency policy. A hash is not encryption or authentication. |
| ISO-01 / SYN-09 | Colliding source IDs across two workspaces must not leak. |
| DEL-01 / SYN-10 | Derived-data invalidation, cache/export inventory, unverified copies recorded, no sensitive values in audit text. |
| SYN-04 | Same file imported twice must not inflate activity; the inspector now has an opt-in digest ledger for cross-call repeats (D-034); near-duplicate re-exports are not detected. |

## 2. Threat model

### Assets

Identifiable raw records (location, motion, health, calendar, privacy-report metadata, account exports); the manifest itself (category names, date ranges, and sizes are sensitive); keys and passphrases; enrollment state and replay/tombstone ledgers; the mapping between a package and a workspace or person.

### Adversaries and failure modes in scope

| ID | Threat | Notes |
|---|---|---|
| T1 | Passive observer of the transfer channel (shared Wi-Fi, a cloud sync folder, a mail attachment, a misdirected share) | Ciphertext must reveal no content. Metadata leakage should be limited to size, a package ID, and the timestamp of the file. |
| T2 | Wrong recipient (AirDrop to a neighbor's device, a wrong Mac, or a wrong workspace on the right Mac) | Only the intended recipient key can decrypt; the importer must also verify the package targets the workspace it is imported into. |
| T3 | Tampering or substitution in transit or at rest (modified manifest, swapped chunks, truncated file, mixed chunks from two packages) | Authenticated encryption over all content and the manifest, with ordering and completeness binding. |
| T4 | Forged package (someone injects fabricated data pretending to be the participant's phone) | Requires sender authentication, not only confidentiality. Matters because fabricated data would poison analysis and findings. |
| T5 | Replay or duplicate import (the same or an older package imported again or out of order) | Must not inflate counts or resurrect deleted data. |
| T6 | Leftover plaintext: native NDJSON/CSV before packaging, decrypted temporaries, thumbnails, indexes, logs, crash reports, backups, cloud-synced folders | Often the weakest link. |
| T7 | Lost or stolen unlocked/locked device or Mac | Keys must not be extractable from a locked device; at-rest protection is separate from transfer encryption. |
| T8 | Weak passphrase (design A) subject to offline guessing against a captured package | Applies only where a human-memorable secret is the sole key source. |
| T9 | Cross-workspace confusion or leakage on a multi-participant Mac | Handled with ISO-01; package design should supply per-workspace keys. |
| T10 | Repository or support-channel leakage (committed exports, keys, logs with values) | Process and tooling, not cryptography. |

### Out of scope or accepted limits (state them to the participant)

- A recipient who legitimately decrypts a package can copy it; deletion cannot recall it (section 8).
- A compromised iPhone or Mac (malware, hostile administrator, physical coercion). The design reduces exposure windows but does not defend a fully compromised endpoint.
- Traffic-analysis of the fact that a transfer occurred.
- Participant error, such as choosing the wrong recipient with a verification step skipped.
- Hardware, OS, and Apple framework vulnerabilities **[UNVERIFIED]** beyond what the project can assess.
- Legal compulsion.
- Nonparticipant data inside provider exports (handled by minimization in the trust doc, not by package cryptography).

## 3. Cross-cutting design principles

1. Use only standard, peer-reviewed primitives through platform libraries; no custom cipher, mode, or key-exchange construction. Name algorithms and parameters in the final decision so they can be reviewed.
2. Use authenticated encryption (AEAD) so confidentiality and integrity are one primitive. A standalone hash or checksum is for corruption detection only. It gives no confidentiality and, unkeyed, no authentication.
3. Separate three properties and test each: confidentiality (recipient only), integrity (not modified), authenticity (from the participant's enrolled phone). Design A delivers confidentiality and integrity only if the passphrase resists offline guessing; it is never stronger than the passphrase. It delivers authenticity only to the extent that the passphrase is a shared secret known to few parties.
4. Bind the context into the authenticated data: format version, package ID, workspace ID, recipient key identifier, sender key identifier, chunk index and chunk count, range and categories digest. A package must fail to open in any other context.
5. Encrypt the manifest too, with only a minimal cleartext header (format version, package ID, key identifiers, algorithm identifiers).
6. Never roll back or silently downgrade: unknown algorithm or version identifiers cause rejection.
7. Plaintext staging is a first-class risk: minimize its lifetime, location, and visibility, and inventory it (section 7).
8. Keep keys out of Git, logs, and the shared data volume; keep fixtures synthetic.

## 4. Candidate designs

All three assume the same logical package: one header, an encrypted manifest, and chunked encrypted payload sections, each a separate AEAD message with a fresh nonce under a per-package content key. They differ in how that key is established and who authenticates whom. The final byte format (containers such as a single file versus a directory, serialization, chunk size) is deliberately not chosen here.

### Design A. Passphrase-derived key; AirDrop or Files of an encrypted archive

- **Mechanism:** the phone derives a key from a participant-chosen passphrase with a deliberately slow password-based KDF and a random salt, then AEAD-encrypts the package. The file is moved by AirDrop, a Files share, or a cable-connected transfer to the Mac, where the same passphrase is entered.
- **Standard primitives:** scrypt (RFC 7914) or Argon2id (RFC 9106), or PBKDF2 (RFC 8018) as a weaker fallback; AES-256-GCM or ChaCha20-Poly1305 (RFC 8439).
- **Platform availability [UNVERIFIED]:** CryptoKit provides AEAD (`AES.GCM`, `ChaChaPoly`), HKDF, and symmetric keys. Whether it includes a password-based KDF, and which one CommonCrypto/Security exposes on iOS and macOS in the installed SDK, must be checked. Argon2id and scrypt may require a third-party library, which would then need its own supply-chain review. Do not assume either exists.
- **Pros:** simple; no key enrollment; works with any Mac and any transport; easy to implement and test early with synthetic data; usable as a researcher-handoff fallback when a recipient key is not yet exchanged.
- **Cons:** security depends on passphrase strength (T8); the passphrase must be shared out of band, creating its own leakage and reuse risk; no sender authentication, since anyone who knows the passphrase can forge a package (T4); no per-recipient or per-workspace cryptographic separation; replay protection requires separate package-ID bookkeeping; the passphrase UX burden on every export invites weak choices.
- **Fit:** acceptable as a quick synthetic-format exploration and a low-assurance fallback. Weak against T4 and T8. Not recommended as the primary V1 path for real data.

### Design B. Public-key encryption to a Mac-held key (recipient-only), CryptoKit-style

- **Mechanism:** the Mac workbench generates a long-lived recipient key pair per workspace (or per researcher) and exposes the public key and fingerprint, for example as a QR code or text file. The phone creates a fresh ephemeral key pair per package, performs key agreement with the recipient public key, derives a content key by KDF, and AEAD-encrypts. Only the recipient's private key can decrypt.
- **Standard primitives:** HPKE (RFC 9180, base mode) or an ephemeral-static Diffie-Hellman using X25519 or P-256 (RFC 7748, NIST SP 800-56A) with HKDF (RFC 5869), then an AEAD.
- **Platform availability [UNVERIFIED]:** CryptoKit exposes Curve25519 and NIST P-curve key agreement, HKDF, AEAD, and (on recent OS versions) an HPKE API. Which OS versions provide HPKE and which ciphersuites are supported must be confirmed in the installed SDK before choosing a deployment target. Secure Enclave key storage is documented for P-256 only **[UNVERIFIED for the current SDK]**, which influences curve choice if the Mac-held key should be hardware-backed. Whether a given Mac has a Secure Enclave depends on the Mac model **[UNVERIFIED]**.
- **Pros:** no passphrase; confidentiality does not depend on a human-chosen secret; private key never travels; forward secrecy with respect to the sender's ephemeral key; per-workspace recipient keys give cryptographic separation (supports ISO-01 and T9); wrong recipient cannot decrypt (T2); suits both self-use and an authorized researcher key.
- **Cons:** recipient-only encryption gives no sender authentication; anyone with the public key can build a valid package (T4). Anyone obtaining the Mac public key can also mount a fabrication attack. Key distribution to the phone must be authentic (a substituted public key defeats confidentiality): verify the fingerprint visually or via a short authentication string. Losing the Mac private key makes existing packages unreadable. Key rotation needs a defined procedure (section 6).
- **Fit:** strong for confidentiality; needs an authenticity layer for the participant's own phone (Design C).

### Design C. Paired static keys with mutual authentication (recommended direction)

- **Mechanism:** a one-time pairing ceremony enrolls two public keys with each other: the Mac's recipient key (as in B) and a phone signing/agreement key, created on the iPhone and bound to the app. The participant verifies both fingerprints on both screens, or scans a QR code in each direction, in person. Each package is then encrypted to the recipient (as in B) and authenticated by the sender, either through HPKE auth mode (RFC 9180; requires a DHKEM, with the sender's static key in the key schedule) or a digital signature over a transcript that includes the header, the encrypted manifest, and every chunk tag. A signature over only the header and manifest digest does not bind the chunk ciphertexts. Neither option provides non-repudiation, and none is needed. The Mac importer refuses packages whose sender key is not enrolled for that workspace.
- **Standard primitives:** HPKE (RFC 9180) base or auth mode, or ECDH plus HKDF plus AEAD, combined with Ed25519 (RFC 8032) or ECDSA P-256 signatures; AEAD as in B.
- **Platform availability [UNVERIFIED]:** CryptoKit signing for Curve25519 and P-256, Keychain storage with access control flags, optional Secure Enclave for P-256 keys, and the available QR/camera pairing UI are all to be verified. If the phone key is a Keychain item rather than Secure Enclave-held, the extractability, the backup/migration behavior, and the interaction with iCloud Keychain and device-to-device restore must be checked and the item explicitly marked device-only **[UNVERIFIED]**.
- **Pros:** confidentiality, integrity, sender and recipient authentication, and workspace binding in one design; closes T4; allows revocation by removing an enrolled key; enrolled key identifiers support clear audit entries without sensitive values; matches the project's "participant-controlled" stance because enrollment requires the participant's physical presence.
- **Cons:** the most moving parts (pairing UX, enrollment state, fingerprint comparison, rotation/revocation, loss recovery); more surface to test; reliance on signature and key-agreement API details that must be verified; researcher-assisted mode needs an additional enrollment path for a researcher's key and a clear statement of what that researcher can read.
- **Fit:** best match to the documented requirements, but also the most work. A staged approach is plausible: use Design A with synthetic data to exercise the package, manifest, and import logic, then add C before any real-data transfer. The staged use of A with real data is not recommended.

### Summary comparison

| Property | A passphrase | B recipient key | C paired keys |
|---|---|---|---|
| Confidentiality independent of human secret | No | Yes | Yes |
| Sender authenticity | No | No | Yes (if enrollment verified) |
| Per-workspace cryptographic separation | No | Yes | Yes |
| Replay resistance | Bookkeeping only | Bookkeeping only | Bookkeeping plus enrolled sender and counters; old validly signed packages still need a tombstone ledger or key retirement (section 6) |
| Setup effort | Low | Medium | High |
| Key loss impact | Passphrase forgotten means data loss | Mac key loss means data loss | Either key loss; requires re-enrollment |
| Matches D-008 and the real-data gate | Weakly | Partly | Best |

## 5. Integrity, authentication, and binding

Requirements for any selected design:

- **Encryption is not authentication; a hash is neither.** A SHA-256 manifest digest or file checksum detects accidental corruption. It does not hide content, and an attacker who can modify the file can recompute it. Hashes inside the manifest are acceptable only because the manifest itself is AEAD-protected and bound to the sender.
- **AEAD authentication tags** cover each chunk. The associated data must include package ID, chunk index, total chunk count, format version, workspace ID, recipient key ID, and sender key ID. This defeats chunk reordering, truncation, cross-package mixing, and wrong-workspace import.
- **Completeness:** the manifest lists the chunk count and a digest of each chunk (or a Merkle-style summary). The importer rejects a package with missing, extra, or reordered chunks.
- **Sender authentication (T4):** a signature or authenticated-HPKE mode under a pre-enrolled sender key (Design C), covering the entire package (header, encrypted manifest, every chunk). A sender key ID in the header or AAD is a label only; it authenticates nothing unless the key schedule or signature binds it. With ephemeral-static encryption alone (Design B), that ID is attacker-writable. Without sender authentication, state plainly in the participant and operator documentation that the package proves only that someone with the recipient public key (or passphrase) built it.
- **Verification before use:** decrypt and fully validate in an isolated temporary location before any record reaches the workspace; on any failure, import nothing and delete the temporary output. Failure messages must not echo record values.
- **No oracle leakage:** report generic failure classes (unreadable, not for this workspace, not an enrolled sender, integrity failure) without exposing which byte or field differed, if the distinction would aid an attacker. Provisional leaning for the local single-user V1: show generic failure classes only and put detail, without record values, in a local debug log.
- **Algorithm agility:** carry explicit algorithm and version identifiers in the cleartext header; reject unknown or downgraded combinations.
- **Nonce and key discipline:** use a fresh random content key per package. In Designs B and C, it comes from HKDF over a fresh ephemeral key agreement. In Design A, it comes from the password KDF with a fresh random salt of at least 16 bytes per package, never reused; a reused passphrase-plus-salt would reuse the key and therefore risk nonce reuse. Within a package, use a deterministic counter nonce (chunk index), or a 96-bit random nonce, so that reuse under one key is impossible by construction. HKDF `info` must include the format version, package ID, and a purpose label (domain separation). For Design A, the cleartext salt, KDF identifier, and cost parameters must be bound as AAD and checked against a minimum floor. The exact nonce construction must follow the primitive's specification and be reviewed **[UNVERIFIED against the chosen API's nonce handling]**.

## 6. Replay, idempotency, key handling, and rotation

### Replay and idempotency (policy options; none selected)

| Option | Behavior | Trade-off |
|---|---|---|
| R1 Package-ID ledger | The Mac records imported package IDs per workspace; a repeat is recognized and reported as already imported with no state change. | Simple. Does not detect a content-identical re-export under a new ID. The ledger entry must not hold sensitive values. |
| R2 Content-level dedup | Records carry stable source keys; import upserts and reports unchanged versus new versus changed. | Needed anyway for overlapping rolling exports (SYN-03); must keep aggregates distinct from events. |
| R3 Sender sequence counter | Each package carries a monotonic per-sender counter in authenticated data; the importer rejects counters at or below the last accepted one. | Defends against replay of older packages after a deletion (T5). A lost or restored phone can reset the counter, so a reset needs an explicit re-enrollment step. |

A provisional leaning is R1 plus R2 for ordinary idempotency, with R3 evaluated for the case where a deleted record could otherwise be resurrected by importing an old package. A deletion tombstone ledger (IDs only, not values) may be needed so that re-import of an old package does not silently restore deleted data; this must be reconciled with the deletion policy and with the "no sensitive values in audit text" rule.

Resurrection defense needs one of the following: (a) a per-workspace tombstone ledger of package IDs and source keys (IDs only), checked before promotion; or (b) retiring the recipient key that the old packages were encrypted to (see Rotation). R1 and R3 alone do not provide it. A restored phone, or an old ciphertext recovered from a backup, Time Machine, or iCloud, can present a validly authenticated older package. A bare package-ID ledger also does not stop a re-exported package under a new ID.

### Key handling

- **Generation:** on-device or on-Mac, through the platform's secure random source and key generation APIs. No keys derived from predictable data.
- **Storage (phone, Mac):** Keychain items with the strictest availability class workable, device-only (not synchronized, not included in backups), and Secure Enclave for private keys where the algorithm allows. These properties are the intended settings; every attribute name, flag, and behavior is **[UNVERIFIED]** against the installed SDK and must be tested on a physical device and on the Mac. A Mac without a Secure Enclave or a signed-out keychain may behave differently **[UNVERIFIED]**.
- **No keys in Git, logs, crash reports, screenshots, or the shared workspace.** Fingerprints (short digests of public keys) may be shown to the participant and recorded in audit entries.
- **Fingerprint verification:** pairing is only as strong as the human comparison. Provisional rule: fingerprint = SHA-256 over (algorithm ID || canonical public-key encoding), displayed with at least 128 bits, grouped for reading. A short authentication string is acceptable only with a commit-then-reveal exchange, because a short string can be ground by an attacker. A QR scan in each direction is acceptable because it carries the full key or full digest. A mismatch aborts pairing and stores nothing.
- **Per-workspace separation:** one recipient key per workspace (and a separate key for an authorized researcher grant) so compromise or deletion of one workspace does not expose another. Whether to additionally derive at-rest storage keys from the same hierarchy is a separate decision.
- **Rotation:** define triggers (suspected compromise, researcher grant ended, device replacement, periodic) and mechanics: generate a new recipient key, enroll its public half on the phone, mark the old key retired (decrypt-only), and re-encrypt or purge old packages according to the retention policy. Rotation does not protect packages already captured under the old key; their lifetime is the old key's lifetime, which is a reason to delete packages and retire the key together.
- **Revocation:** removing an enrolled sender or recipient from the Mac and phone, and rejecting subsequent packages. This is a future-sharing control, not a recall of earlier copies.
- **Loss and recovery:** lost Mac key means encrypted packages cannot be read; decide whether that is acceptable (it supports "delete means delete") or whether an escrow is allowed (it would add a new copy of key material). Provisional leaning: no escrow in V1.
- **Passphrase use (Design A):** if used, store no passphrase; derive a key in memory, wipe after use, show strength guidance, and choose a KDF cost calibrated on the oldest supported device **[UNVERIFIED]**.

## 7. Staging, temporary copies, and test-copy deletion

Native exports from sources (Health export, App Privacy Report NDJSON, calendar dumps, account exports) are commonly unencrypted. Handling them is a controlled step, not an incidental one.

### Inventory of places plaintext can exist

| Location | Concern | Control to design and test |
|---|---|---|
| iPhone app container: generated export file before encryption | Readable by backups or file-sharing features if misplaced | Write to a protected location with the strongest practical data protection class **[UNVERIFIED]**, exclude from backup **[UNVERIFIED]**, encrypt then delete the plaintext immediately, delete on app-launch recovery if a crash left one. |
| Files app, shared folders, iCloud Drive, AirDrop received-file location **[UNVERIFIED]** | Cloud-synced or user-visible copies | Never place plaintext there. Ciphertext only. Treat cloud-synced folders as uncontrolled for ciphertext retention. |
| Participant-provided source exports (App Privacy Report, account export) as received | They arrive as plaintext | Import through a staging area on the Mac or phone with a stated lifetime; delete or re-encrypt after parsing; record that the original in the Files app or downloads folder **[UNVERIFIED received-file location]** is outside the project's control until the participant removes it. |
| Mac temporary decryption output | Left behind after failure | Isolated temp directory, validation before promotion, wipe on both success and failure, with startup sweep. |
| Mac workspace store, indexes, caches, search indexes, thumbnails, Spotlight, Time Machine and other backups, swap | Derived or copied plaintext | Out of scope of the package design but must be listed in the at-rest design and the deletion inventory. Spotlight, swap, Time Machine scope, and backup exclusion are **[UNVERIFIED]** behaviors. |
| Logs, crash reports, analytics, clipboard, screenshots | Accidental value capture | No record values in logs; redaction tests. |
| Repository | Committed real data or keys | Synthetic fixtures only; ignore rules and a pre-commit scan for key and export patterns. Outside this document's authority but a precondition. |
| Test copies of real data used during development | Forgotten copies | A named inventory entry per test copy, with owner, location, creation time, and verified deletion. |

### Single-owner V1 requirements (most probable leaks)

For one owner on one Mac, backups, sync, and a lost phone are the likeliest exposures, so they are requirements rather than footnotes:

- Place staging and workspace directories outside iCloud Drive's Desktop and Documents sync and outside any Time Machine-included path. Otherwise, list the backup copy as an uncontrolled copy in the DEL-S5 inventory. Exact exclusion mechanics are **[UNVERIFIED]**.
- Require FileVault on the Mac and record whether it is enabled.
- Lost phone: the app's data sits behind the device passcode, and the phone key is non-exportable **[UNVERIFIED attributes]**. The documented response is Find My remote erase plus Mac-side revocation of the enrolled phone key. Record a lost-phone drill as a test (DEL-S7, SEC-S1).

### Deletion of test copies and staging files

- Assign each staged file or package a package/evidence ID and a deletion deadline when created.
- Delete plaintext immediately after successful encryption or parse; delete ciphertext after confirmed import according to the participant's retention choice.
- Secure-erase semantics on modern flash storage and APFS are not reliable by overwriting alone **[UNVERIFIED]**. The more dependable strategy is to keep staging data under a key that is then destroyed (crypto-erase), ideally with encryption at rest on the volume. Whether file-level data protection or volume encryption yields effective erasure on the exact devices must be verified and recorded as such, not assumed. Crypto-erase counts as deletion only if the key has been verified never to have existed outside the controlled device: no backup, no iCloud Keychain, no escrow. Otherwise record the data as unverified.
- Record each deletion as an event (ID, time, location class) without sensitive values; record any copy that could not be verified as unverified.
- A deletion check is a test (DEL-01), not a statement of intent: list expected locations, check they are empty or unreadable, and keep the result as evidence.

## 8. What deletion cannot recall

State these to the participant and the researcher explicitly:

- A recipient who decrypted a package, including the participant's own Mac, may have made copies, screenshots, derived summaries, or backups. Revocation of future access does not recall them.
- Copies in third-party systems the project does not control: AirDrop recipients' devices if mis-sent and then accepted, email or cloud storage if used, iCloud or Time Machine backups **[UNVERIFIED whether excluded]**, Apple's or a carrier's retained metadata.
- Derived insights, notes, or model outputs that were shared or exported by the recipient.
- Memory in a human recipient.
- Previously captured ciphertext whose key is later destroyed is unreadable but still exists; the claim is "unreadable if the key is gone and the algorithm holds", not "erased".
- Source data in the originating service (for example the account provider) is untouched by Panoptes deletion.

Deletion confirmation should list controlled copies deleted and an explicit list of unverified or uncontrollable copies.

## 9. Recommendation (provisional) and open questions

### Provisional recommendation

1. Treat Design C as the target for any real-data transfer: recipient-key encryption per workspace, authenticated sender, AEAD with bound context, device-only keys, in-person fingerprint pairing. Select concrete ciphersuites only after the SDK verification list below.
2. Use Design A, with synthetic data only, if an earlier proof of the package layout, manifest, chunking, and importer is wanted before pairing UX exists. This keeps XFR-01 progress possible without lowering the real-data gate.
3. Treat plaintext staging deletion, replay policy, and the at-rest design as co-equal parts of the transfer decision, not later polish.
4. Revisit this document after the Mac preflight (D-027) and the SDK verification below. If a required API is missing, record the substitute (for instance a vetted third-party library) and its review as a new decision.

### Open questions

1. Which OS versions will the project target (D-027 gate), and therefore which of CryptoKit's HPKE, signature, and Secure Enclave capabilities are available? **[UNVERIFIED]**
2. Is a password-based KDF available in system libraries, or is a dependency acceptable for Design A?
3. Single file versus directory package; chunk size; serialization; compression before encryption (compression of secret and attacker-influenced data can leak information; decide deliberately).
4. How is the Mac public key delivered to the phone with enough authenticity: QR code, cable, nearby verification, or manual fingerprint compare? How will the participant be protected from skipping the check?
5. Are phone keys device-only and non-migrating? What is the recovery path after phone replacement?
6. Researcher-assisted mode: how is a researcher's recipient key enrolled and scoped, how is the purpose and retention shown in the cleartext header (if at all), and how are expiry and revocation recorded?
7. Which replay policy (R1, R2, R3) and how does a deletion tombstone ledger avoid retaining sensitive values?
8. Does the package carry a per-package consent/purpose record, and is that record itself sensitive?
9. What is the minimum acceptable metadata in the cleartext header?
10. Which backup, Spotlight, and indexing exclusions are effective on the exact Mac and iPhone configuration? **[UNVERIFIED]**
11. Should the at-rest workspace keys be derived from, or independent of, the transfer recipient keys?
12. Is an independent security review required before the first external participant? (Likely yes; not planned yet.)

### SDK and platform verification checklist (all currently UNVERIFIED)

- CryptoKit availability by OS version: AEAD, HKDF, Curve25519 and P-curve key agreement, signing, HPKE.
- Password-based KDF options in system libraries and their parameters.
- Keychain accessibility classes, device-only and non-backup flags, access control, and Secure Enclave key generation and algorithm support on the iPhone and on the specific Mac.
- Data protection classes for files created by the app and their behavior when the device is locked.
- Backup exclusion and Spotlight exclusion behavior for staging and workspace locations.
- AirDrop and Files behavior for received files (location of the received copy, retention, user-visibility), and whether any received copy is synchronized.
- Nonce and counter handling in the chosen API; maximum message sizes; streaming or chunking support.
- Behavior of keys across iPhone backup, restore, and device replacement.

## 10. Test plan (synthetic data only)

All cases use fictitious identifiers and reserved example domains, never real exports. They assume a package prototype exists; before then, they remain specifications. Unless noted, they map to the synthetic (S) gate. Cases requiring the Apple SDK or hardware are additionally gated on M.

### XFR-01 mapping

| Case | Setup | Expected result |
|---|---|---|
| XFR-S1 Round trip | Synthetic multi-category data, selected date range and categories | Importer yields exactly the selected scope; manifest matches; counts and aggregate/event distinctions preserved. |
| XFR-S2 Scope selection | Two category subsets and two date windows | Records outside the selection never appear in the package (inspected after decrypt); boundaries inclusive or exclusive as documented. |
| XFR-S3 Tamper: bit flip in ciphertext | Alter one chunk | Import rejected; nothing written to the workspace; temporary output removed. |
| XFR-S4 Tamper: manifest edit with recomputed hash | Edit the manifest and fix up any hash | Rejected; demonstrates the hash alone is not authentication. |
| XFR-S5 Truncation, reorder, chunk swap from another package | Remove, reorder, or substitute chunks | Rejected via chunk index, count, and package binding. |
| XFR-S6 Wrong recipient | Decrypt with a different recipient key | Fails without partial plaintext. |
| XFR-S7 Wrong workspace | Correct recipient key, importing into another workspace | Rejected based on bound workspace ID. |
| XFR-S8 Unenrolled or forged sender (Design C) | Build a validly encrypted package with a non-enrolled key | Rejected as not from an enrolled sender; for Design A/B, document that it is accepted, to show the limitation. |
| XFR-S9 Downgrade or unknown algorithm | Change header algorithm or version | Rejected. |
| XFR-S9b KDF parameter downgrade (Design A) | Lower the cleartext KDF cost or salt length | Rejected below the minimum floor. |
| XFR-S10 Duplicate import | Import the same package twice (relates to SYN-04) | Second import reports duplicate; no change in counts. |
| XFR-S11 Overlapping packages | Two packages with overlapping windows (SYN-03) | Aggregates are not summed; snapshot provenance preserved. |
| XFR-S12 Replay after deletion | Delete a record, then import an older package that contains it | Behavior matches the chosen policy (reject or tombstone-respect); documented. |
| XFR-S13 Failure messaging | Trigger each failure above | No record values in messages or logs. |
| XFR-S14 Nonce and key uniqueness | Generate many packages and chunks | Deterministic-nonce assertion within a package; no two packages share a content key; no nonce reuse under a key. |
| XFR-S15 Cleartext header contents | Inspect the header of packages with distinct scopes | Header holds only the allowed fields; no category names, date ranges, or record counts appear in cleartext. |
| XFR-S16 Atomic promotion | Interrupt the importer between validation and promotion | Workspace holds all or none of the package; leftovers removed by the startup sweep. |
| XFR-S17 Compression decision | Only if compression is selected (open question 3) | Documented rationale; tests for size-based leakage where secret and attacker-influenced data mix. |
| XFR-S18 Fingerprint mismatch at pairing | Present a substituted public key during enrollment | Pairing aborted; nothing stored. |
| XFR-D1 Device round trip | Synthetic payload exported on a physical iPhone, moved by the chosen transport, imported on the Mac | Gate M; records transport, location of intermediate copies, and cleanup. Evidence class: physical-device observation. |

### ISO-01 mapping

| Case | Expected result |
|---|---|
| ISO-S1 Two workspaces with colliding source IDs (SYN-09) | Imports into each keep records separate; no cross-links. |
| ISO-S2 Package for workspace A offered to workspace B | Rejected (see XFR-S7). |
| ISO-S3 Key separation | A recipient key for workspace A cannot decrypt a package for B. |
| ISO-S4 Correction and export isolation | A correction in A does not change B; an export from A contains no B record. |
| ISO-S5 Cache, index, and temp isolation | No shared cache or temp path leaks values between workspaces. |

### DEL-01 mapping

| Case | Expected result |
|---|---|
| DEL-S1 Staging cleanup on success | Plaintext and temp outputs absent after import; inventory shows each deletion. |
| DEL-S2 Staging cleanup on failure or crash | Startup sweep removes leftovers; test with simulated interruption. |
| DEL-S3 Package deletion and key retirement | Ciphertext removed; retired key cannot decrypt anything remaining; unverified copies listed. |
| DEL-S4 Source deletion cascade (SYN-10) | Dependent features, findings, caches, and export copies removed or invalidated per policy; other workspace intact; audit text contains no values. |
| DEL-S5 Copy inventory | Every copy location in section 7 appears as deleted, verified-empty, or explicitly unverified. |
| DEL-S6 Test-copy register | Every real-data test copy (once permitted) has an owner, a deadline, and a verified deletion record. |
| DEL-S7 Backup and sync inventory | Workspace and staging paths checked against Time Machine and iCloud settings; each recorded as included, excluded, or unverified. Gate M. |

### Revocation mapping

| Case | Expected result |
|---|---|
| SEC-S1 Lost-phone revocation | After the enrolled phone key is revoked on the Mac, a package signed with that key is rejected. |
| SEC-S2 Retired recipient key | After key retirement, packages encrypted to the retired key are not promoted into the workspace. |

### Evidence conventions

Record each case using the existing [result template](templates/collection-probe-result.md): execution status, outcome, evidence class (synthetic, simulator, physical device), and limits. A synthetic or simulator pass does not prove Keychain, Secure Enclave, data-protection, or AirDrop behavior on a physical device. A pass confirms only that the tested mechanism rejected the tested adversarial inputs, not that the design is secure. Real-data transfer remains blocked until the real-data gate in the collection protocol is satisfied.

## 11. Non-goals

- Selecting final primitives, byte formats, or APIs.
- Continuous synchronization, cloud relay, or server-held keys (deferred by D-008).
- Anonymization or de-identification guarantees.
- Claims of universal erasure or of resistance to a compromised endpoint.
- Legal or compliance conclusions.
