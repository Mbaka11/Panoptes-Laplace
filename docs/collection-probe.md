# Collection feasibility protocol

## Purpose and status

Turn the collection assumptions into reproducible evidence before choosing an application stack or building the full explorer. This extends the original Sensor Probe without assuming that native sensors expose the participant's entire digital life.

**Status:** test specification with a limited [synthetic App Privacy Report inspector](../spikes/app-privacy-report.md) now implemented under D-028. Its [run record](results/app-privacy-report-synthetic.md) covers a documented subset, not an on-device result or production importer. Native collection and real-data cases remain pending. Source targets remain provisional under D-026; deployment targets, signing, storage, cryptography, and canonical schemas are unselected.

Related documents:

- [Decision log](decisions.md), especially D-023 through D-027
- [Reference-checked collection boundaries](review-and-next-steps.md#4-reference-checked-collection-boundaries)
- [Architecture](architecture.md) and [trust requirements](trust-and-data-governance.md)
- [Blank result template](templates/collection-probe-result.md)

## 1. Current configuration and work boundaries

The owner reports an iPhone 15 Pro running iOS 26.6.1, located in Canada, and access to a Mac with Xcode. Exact Mac versions, paid membership, export entitlements, Apple Account region, and Health data producers have not been independently established. Canadian device location alone prevents assuming EU customer eligibility for the newer activity export.

### Can prepare now, without Mac commands

- Maintain the capability matrix, test cases, and expected semantic boundaries.
- Design synthetic importer cases using invented app identifiers, domains, timestamps, and measurements.
- Prepare isolated synthetic workspace, correction, and deletion tests.
- Specify result reporting and distinguish unknown/blocked results from verified support.
- Review source documentation without transmitting participant data to external services.

This protocol and template specify the work; the linked run record states what was actually executed. The synthetic inspector covers interval/aggregate parsing, some validation semantics, and an opt-in source-coverage report with timestamp/line provenance and explicit unknowns. It does not measure actual collection completeness or cover Health, calendar, transfer, workspace isolation, or deletion.

### Can inspect on the phone if the owner chooses

- Check which Health categories have records and which apps/devices produced them, without uploading those records.
- Inspect whether App Privacy Report is enabled. It only starts recording when enabled; enabling it is the participant's choice, not a prerequisite for this documentation work.
- Check which relevant services offer an account export. Do not assume its contents before inspection.

### Native-build gate — intentionally pending

Run on the Mac when available:

```bash
sw_vers
xcodebuild -version
```

Record the results in a sanitized configuration note, verify Xcode/device compatibility, and only then select a deployment target and scaffold the native probe. Record exact build/install commands after a project and scheme actually exist; do not publish fictional commands or claim a Windows Xcode build.

### Real-data gate — separate from the build gate

Before a probe writes persistent sensitive samples or a real export is transferred/imported:

1. Explain source scope, collection mode, retention, and operator access; obtain explicit participant authorization.
2. Select and test protected storage/staging, encrypted transfer, key handling, and export integrity/authenticity appropriate to the workflow.
3. Decide where raw files, logs, temporary copies, caches, and derived results live, outside the source repository.
4. Define pause, revocation, copy inventory, and deletion behavior, including what cannot be recalled from a recipient.
5. Prepare synthetic/redacted repository fixtures and verify that real data, signing material, and secrets cannot enter commits accidentally.

Do not use this checklist as a substitute for a concrete security decision. A source's own NDJSON/CSV export is not automatically an encrypted Panoptes package. No security mechanism is selected by this document. Real-data cases remain blocked until their required controls exist; synthetic specification work may proceed.

## 2. Result vocabulary and evidence rules

Use the [result template](templates/collection-probe-result.md) for each executed case and configuration. Keep these dimensions separate:

| Dimension | Record |
|---|---|
| Execution | Not run, blocked, or completed; include the blocker rather than an invented outcome |
| Test outcome | Not evaluated, expected behavior confirmed, unexpected behavior, or inconclusive |
| Capability conclusion | Unknown, documented-only, observed within stated limits, or observed unavailable in this configuration |
| Authorization | OS-exposed state and participant scope, or explicitly unknown/not exposed; read and write permissions are distinct |
| Data availability | Unknown until queried; measured count may be zero without proving denial or lack of activity |
| Export | Not applicable, not tested, blocked, failed, or verified within a specified scope; display success does not imply export success |
| Evidence class | Owner-reported configuration, first-party documentation, synthetic test, simulator result, or physical-device observation |

For every result, record:

- case ID, procedure version, run time and time zone, build/version if applicable;
- OS/device class, provisioning/installation mode, required capability and authorization scope;
- source type and producer, query window, source semantics and units;
- record count, latest applicable timestamp, event time versus import/report time;
- point/interval/aggregate granularity, known gaps, overlap policy, and quality indicators;
- storage/transfer controls in scope, export evidence, and cleanup outcome;
- supporting and contradicting observations, limitations, and the next decision it informs.

Do not paste private values, complete domain lists, routes, account IDs, secrets, or raw exports into the repository result. Keep raw evidence in the protected workspace and refer to it through a safe evidence ID. Use unknown rather than zero for unmeasured values. Do not compress all of these fields into a single confidence percentage.

A failed or unavailable capability is a useful completed investigation when the procedure and evidence are clear; it is not a reason to fabricate a successful source. A simulator test does not prove physical-device background behavior.

## 3. Test case catalogue

**Current execution:** APR-02 has limited documented-subset synthetic coverage; see the run record. All physical-device/real-data cases and the other runtime systems below remain untested. Gate abbreviations: **M** = Mac/build preflight plus any case-specific provisioning; **R** = real-data controls above; **S** = synthetic-only implementation can proceed without M/R. Documentation inspection is not runtime execution.

| ID | Case | Gates | Expected evidence |
|---|---|---|---|
| ENV-01 | Confirm build/device/provisioning context | M | Actual tool versions, device compatibility, install mode, available entitlements; no credentials |
| CTL-01 | Collection controls and source scope | M, R | Per-source explanation, pause/resume, permission-revocation response, and accurate status |
| LOC-01 | Location collection | M, R | Foreground and locked/background samples, quality, gaps, history limitations, export |
| MOT-01 | Motion/activity query | M, R | Available signal types/history, timestamps and source confidence semantics, permission behavior |
| HLT-01 | Health reads and source availability | M, R | Actual producer/type inventory, units and overlap, empty-query interpretation, export |
| EVT-01 | Calendar/reminder context | M, R | Permitted read scope, time zones/recurrence, minimized fields, exported provenance |
| APR-01 | Participant App Privacy Report export | R | Actual file structure/window and resource/domain metadata; no custom native app required |
| APR-02 | Import privacy-report semantics | S; R for real files | Interval/aggregate preservation, validation and overlapping-export behavior |
| ACC-01 | Inspect one relevant service export | R; S for a synthetic example | Present/absent fields and source meanings, especially consumption and interaction coverage |
| SCT-01 | Standard Device Activity report | M, R, required membership/entitlement | Authorized presentation behavior; explicit boundary against exporting restricted report content |
| SCT-02 | Official activity-data export | M, R, its own entitlement/authorization | API availability and legitimate export in the exact development/customer and regional context |
| BAT-01 | Background reliability and battery comparison | M, R | Comparable control/probe sessions, collection gaps and energy observations with confounders |
| XFR-01 | Package selection and transfer | S; M/R as applicable | Scope selection, validation, integrity/authentication checks under the chosen design, round-trip evidence |
| ISO-01 | Workspace separation | S | No cross-workspace reads, links, correction effects, or export leakage in adversarial cases |
| DEL-01 | Corrections and deletion | S; R for real copies | Derived-data invalidation/removal, cache/export inventory, other-workspace preservation |

### ENV-01 and CTL-01 — installation and control

Record the actual signing mode rather than merely saying "sideloaded." Confirm that the installed build has the required capabilities. Do not purchase membership or request managed capabilities on the owner's behalf without authorization.

Explain sources before permission prompts. For each enabled source, pause collection, perform a small participant-controlled activity, then resume and inspect the result. Define whether resume may import historical records from the paused interval; do not silently backfill a pause period contrary to the participant's selection. Test OS revocation separately from the app's own pause control.

Control success means behavior matches the stated scope, not that all sources return records. Errors must not expose sensitive sample values in logs.

### LOC-01 and MOT-01 — mobility

Use participant-chosen short observations such as stationary and walking periods. Record sampling strategy, requested/observed authorization, timestamps, accuracy/quality, and any accessible historical window. Do not request broader permissions simply to hide a failed test.

Compare foreground, background, and locked-device behavior. Treat explicit force-quit/relaunch as a separate condition; do not promise continuous execution where the OS does not provide it. Record what happened rather than interpreting gaps as stationary behavior. Export and re-read a bounded sample only after the transfer controls are defined.

### HLT-01 — Health records

Inventory the categories and actual producers available before selecting an analysis. Steps may come from the phone; heart-rate or sleep data requires actual records from a suitable producer. No Apple Watch is assumed.

Test a narrow authorized query and record units, start/end times, producer identity at a safe abstraction level, and potential duplicates across sources. Empty results cannot establish read denial, absence of the real-world activity, or a zero measurement. Do not use write-authorization status as a proxy for read access.

### EVT-01 — calendar and reminders

Use a synthetic test entry owned by the participant to examine timed/all-day behavior, recurrence, and time-zone handling. Request only the required scope. Exclude unnecessary attendee details, contacts, descriptions, meeting links, and other third-party fields from test exports. Planned events are intentions/context, not proof that an activity happened.

### APR-01 and APR-02 — App Privacy Report

Use the participant's Settings share flow where available. Record when recording was enabled and the actual reporting window; do not assume history exists before enablement. Verify the current device's exported format rather than merely relying on the documented NDJSON example.

The importer specification must preserve:

- access interval boundaries, including missing or unmatched endpoints;
- domain-contact aggregates and their first/most-recent timestamps and hit counts;
- source export window and generation/import time where available;
- the distinction between an app's resource access, a network connection, and unobserved payload content;
- known exclusions, including browser private-browsing network activity;
- overlapping rolling-window snapshots without summing them into fictitious totals.

A contacted domain may serve many purposes. Neither contact nor sensor access proves that data reached the developer or that an algorithm used it. These imports are not a route to reconstruct exact taps, feed views, or scrolling.

### ACC-01 — one account-export coverage audit

Select a service the participant actually uses; Google is a candidate, not an irrevocable connector choice. Record the exporter/version or retrieval context, format, time range, and documented field meanings.

List separately whether the export contains viewed content, searches, interactions, timestamps, duration, or no relevant field. Do not infer dwell time from the gap between two unrelated events or infer scroll depth from a viewed-content record. Exclude unnecessary third-party content. Reuse the synthetic equivalents of useful shapes in tests; do not commit the participant's export.

### SCT-01 and SCT-02 — Screen Time feasibility

For SCT-01, document membership, entitlement, owner authorization, and whether the report renders. The report extension's restricted address space is not an export mechanism; no network/shared-container workaround should be used to move sensitive report data across that boundary.

For SCT-02, verify the installed SDK and runtime support, dedicated App and Website Usage entitlement, and `approvedWithDataAccess` status before attempting the documented export API. Record the precise provisioning/installation mode. A result in a developer-installed build in Canada does not establish customer availability there. Do not generalize from a report-view success to export success, from `.approved` to `.approvedWithDataAccess`, or from one entitlement to another.

Keep both cases independently reportable. Other sources can proceed if either spike is blocked. A manual participant screenshot/annotation, if later chosen, is partial input and must not be labeled raw API telemetry.

### BAT-01 — battery and background reliability

Before running, specify session duration, sampling settings, an initial acceptable-overhead target, and comparable conditions. Observe collector-off/control and collector-on sessions, recording battery start/end, charging state, foreground use, network conditions, and elapsed time. Avoid driving or other unsafe activity during observation.

Repeat comparable sessions before attributing a drain difference to the collector. A short or unmatched comparison is exploratory, not evidence of acceptable all-day behavior. Record collection coverage alongside energy use; apparent efficiency caused by no background samples is not a success.

### XFR-01, ISO-01, and DEL-01 — boundaries and lifecycle

Start with synthetic data only. After a concrete package/security design exists, test source/date selection, tamper rejection, wrong-recipient/workspace handling, duplicate import behavior, and the chosen replay/idempotency policy. A hash is not a substitute for encryption or sender/recipient authentication.

Use two synthetic workspaces with deliberately colliding source IDs. Test reads, relationships, imports, exports, corrections, and deletion against the wrong workspace; no cross-boundary record should become accessible.

For a corrected interpretation, preserve the original observation and version history while updating/invalidation-marking dependent findings. For deletion, remove or invalidate dependent data under the chosen policy without retaining sensitive values in audit text, caches, temporary files, or insight packages. Track exported copies separately. Record unverified recipient/backups rather than claiming universal erasure.

## 4. Synthetic semantic cases and current coverage

These are test inputs/expectations, not a final canonical schema. The current inspector exercises the documented subset of SYN-01 through SYN-06; SYN-04 covers byte-identical repeats within one call, not persistent import idempotency. SYN-07 through SYN-10 remain pending. Use fictitious identifiers such as `com.example.synthetic` and reserved example domains. See [the spike's coverage table](../spikes/app-privacy-report.md#coverage-against-the-collection-protocol) for exact limits.

| ID | Input condition | Required behavior |
|---|---|---|
| SYN-01 | Matching access begin/end plus an unmatched begin | Preserve the complete interval; keep the unmatched endpoint explicitly incomplete, not an invented duration |
| SYN-02 | One domain record with five hits and first/last timestamps | Preserve one aggregate with five hits; do not synthesize five page views or exact request times |
| SYN-03 | Overlapping rolling exports with totals five and eight | Preserve snapshot/window provenance; neither sum to thirteen nor assume a three-event delta without justified source semantics |
| SYN-04 | Same file imported twice | Show idempotent/duplicate behavior without increasing underlying activity |
| SYN-05 | Malformed NDJSON line, unknown field, or unsupported record type | Report validation/coverage explicitly; do not silently discard errors or misclassify unknown data |
| SYN-06 | Time-zone offsets, reversed interval, or missing timestamp | Preserve time context; flag invalid/unknown timing instead of silently changing it |
| SYN-07 | Empty Health query with a write-permission status | Preserve read-access uncertainty; do not emit a zero health measurement or claim denial |
| SYN-08 | Planned calendar event with no confirming observation | Treat it as scheduled context, not an observed activity |
| SYN-09 | Same source ID in two participant workspaces | Keep records, links, exports, and corrections isolated |
| SYN-10 | Delete a source feeding a feature, finding, cache, and export | Apply the declared derivative/copy policy and expose any unverified copy; preserve the other workspace |

## 5. Provisional exit and handoff

A useful completed lab produces a source-by-source results summary, not a promise that all sources worked. Include blockers and unavailable capabilities alongside successes.

Before advancing to the connected explorer:

- Demonstrate useful, legitimate, exportable coverage from at least three categories across two domains, including digital-behavior or app-metadata data. Do not split one source's fields into artificial categories merely to hit the target.
- Identify at least one verified live native path and useful imports; document missing detailed interactions explicitly.
- Confirm storage/transfer and participant-control requirements for real data in the selected slice.
- Identify what remains test-only or region/provisioning-limited, especially Screen Time.
- Specify which source semantics, duplicates, temporal gaps, and quality limits the explorer must preserve.
- Record any explicit scope revision if the target is not feasible; do not quietly reduce the product to wellness metrics.

Analysis comes after coverage is understood. This lab need not find a positive relationship, issue a notification, or forecast Monday. Keep the concrete framework, schema, security, and subsequent analytical-method decisions separate from a report of what the phone and exports can supply.
