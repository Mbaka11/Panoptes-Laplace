# Sensor Probe specification (native iPhone collector)

## Purpose and status

Platform-independent specification of the native iPhone Sensor Probe that implements the on-device cases of the [collection feasibility protocol](collection-probe.md). It says what the probe must request, explain, record, and refuse to do. It does not say how to build it.

**Status: PROVISIONAL.** Nothing here has been executed or compiled. The Mac preflight is incomplete: macOS 15.7.9 (build 24G830) is reported, but `xcodebuild -version` failed because the active developer directory is Command Line Tools ([reported environment](review-and-next-steps.md#2-reported-test-environment)). Therefore this document deliberately selects **no** deployment target, Xcode version, project or module structure, bundle identifier, signing mode, storage engine, cryptography, or build command (D-027). Those are filled in by the ENV-01 result and a later decision.

**Tagging rule.** Any statement about an Apple API, Info.plist key, entitlement, authorization enumeration, or OS behavior that could not be verified in this repository is tagged **[UNVERIFIED]**. It comes from general knowledge, not from an SDK header, installed documentation, or a device run. An untagged Apple-related statement is taken from the cited repository documents. An [UNVERIFIED] tag is not an accusation of error; it means "check against the installed SDK and a device before relying on it."

Related documents: [collection protocol](collection-probe.md), [result template](templates/collection-probe-result.md), [architecture](architecture.md), [trust and data governance](trust-and-data-governance.md), [reference-checked boundaries](review-and-next-steps.md#4-reference-checked-collection-boundaries), [decision log](decisions.md).

## 1. Goals and non-goals

### Goals

1. Produce evidence for LOC-01, MOT-01, HLT-01, EVT-01, CTL-01, BAT-01, and (separately gated) SCT-01/SCT-02, in the vocabulary of the result template.
2. For each source record: support, provisioning context, observable authorization, record count, latest timestamp, granularity, missingness, and export success. Unknown stays unknown, never zero.
3. Show the participant, before any OS prompt, what each source is, how it is collected, how to pause it, and how to delete it.
4. Keep point, interval, and aggregate records distinct, and keep event time distinct from query/import time.
5. Be a bounded, inspectable feasibility instrument, not a product. Findings may be "unavailable" and still be successes.

### Non-goals

- No ontology UI, analytics, ML, forecasts, notifications, or interpretation of what a trace means.
- No continuous synchronization, cloud service, account system, or external model call.
- No App Privacy Report or account-export import in the native app (those are importer cases APR-01/02, ACC-01 on the Mac side).
- No encrypted-package format, key exchange, or transfer protocol. Those follow [transfer-package-design.md](transfer-package-design.md) and a later decision. The probe may only produce a clearly labeled **unprotected local test artifact** for synthetic or gate-cleared data.
- No hidden collection, permission bypassing, sandbox escape, credential capture, screen recording, network interception, or deceptive status. Sideloading does not remove OS permission or sandbox rules.
- No collection of nonparticipants' content (attendee details, contacts, event notes, meeting links).
- No attempt to move Screen Time report content out of its restricted extension.
- No App Store readiness, no analytics SDKs, no crash-reporting services, no third-party dependencies that transmit data.

## 2. Gates the probe must respect

| Gate | Meaning for the probe |
|---|---|
| M (Mac/build) | The probe cannot be scaffolded until ENV-01 records real `sw_vers` and `xcodebuild -version` output and device compatibility. |
| R (real data) | Until protected storage, key handling, and deletion of test copies are decided (collection-probe, "Real-data gate"), the probe runs only against synthetic or participant-created throwaway data, and must display a "TEST BUILD: not cleared for real data" banner. Whether any source may be switched on in a real-data configuration is a build-time-visible flag, not a hidden setting. |
| Screen Time | Separately gated and independently reportable; blocking it must not block other modules. |

## 3. Common model (applies to every module)

### 3.1 Authorization and availability state model

The probe reports one **Availability** value and one **Authorization** value per source and per requested data type. They are different dimensions. Do not collapse them.

| State | Meaning | Notes |
|---|---|---|
| `unsupported` | The capability or data type is not available on this device/OS/provisioning. | Also used when a required entitlement is missing (record which one, not credentials). |
| `not_determined` | The OS reports the participant has not been asked. | Only where the OS exposes this. |
| `denied` | The OS reports an explicit denial. | Only where the OS exposes it. Never inferred from an empty result. |
| `restricted` | The OS reports a system or parental restriction. | Only where the OS exposes it. |
| `authorized` | The OS reports access granted. Record the scope (for example while-in-use versus always, full versus limited, full versus write-only) as a separate field. | Scope names come from the SDK. [UNVERIFIED] |
| `unknown_not_exposed` | The OS deliberately does not reveal the answer. | Required value for **HealthKit read** authorization (below). |

Rules:

- Each source declares which of these states its API can actually produce. Declaring a state the API cannot produce is a spec error. The mapping from SDK enumerations to these states is to be written during implementation against the real SDK. [UNVERIFIED]
- The probe stores the *OS-reported* value and the *time it was observed*. A displayed state older than the last app foreground is marked stale.
- Authorization is re-read on every return to foreground, because the participant can revoke in system Settings at any time.
- **Empty result is data availability, not authorization.** A query that returns zero records is logged as `record_count = 0, authorization = <whatever was observable>`, never as `denied`.
- Read and write permissions are distinct. The probe requests no write permission for any source.

### 3.2 Collection state (the probe's own, separate from the OS)

Per source, the probe maintains one participant-controlled state:

| State | Meaning |
|---|---|
| `off` | Never enabled, or disabled by the participant. No collection and no OS prompt has been triggered by the probe for this source. |
| `on` | Participant enabled; probe collects within the stated scope. |
| `paused` | Participant paused. No new collection. No silent backfill of the paused interval (see 3.3). |
| `blocked_by_os` | Participant wants `on` but the OS state forbids it (`denied`, `restricted`, `unsupported`, or revoked). The probe does not retry prompts in a loop and does not hide this state. |

The two state layers are shown side by side in the UI. "Collecting" is displayed only when probe state is `on` **and** the OS state permits it.

### 3.3 Pause, resume, revocation, and backfill

- **Pause** stops requesting new samples/queries and stops any background delivery registration for that source. It does not delete data.
- **Resume** begins collection from the resume time. For sources with OS-held history (Motion, HealthKit, EventKit), the participant is asked separately whether to import records covering the paused interval. The default is **no**. If yes, imported records carry `acquisition = backfill_after_pause` so the gap is not mistaken for live observation. The default must never be changed silently.
- **OS revocation** is detected on next foreground (and, where the OS delivers a callback, sooner [UNVERIFIED]). The probe records a `revocation_observed` control event with the time observed (not the time revoked, which it does not know), moves to `blocked_by_os`, and stops. Already-stored records remain until the participant deletes them; the UI says so.
- **Probe pause versus OS revocation** are tested separately (CTL-01) and logged as different control events.
- **Delete** is per source and per date range, with a confirmation that states what will be removed and that exported copies elsewhere are not recalled.

### 3.4 Participant-facing text conventions

Pre-prompt explanations are shown by the probe **before** it triggers any OS permission dialog, with two choices: "Continue to the system prompt" and "Not now". "Not now" leaves the source `off` and does not trigger the OS dialog. Every explanation states: what is read, how often/when, where it is stored, that it stays on the phone until the participant exports, how to pause, how to delete, and what is *not* collected. Wording below is draft and needs a plain-language review with the owner.

Draft Info.plist purpose strings are the OS-prompt text. They must be short, factually match the pre-prompt, and must not promise more than the probe does. **All key names below must be verified against the installed SDK and Apple documentation before use.** Keys whose names I believe but cannot confirm here are tagged [UNVERIFIED], which is every key in this document. Where the name is more doubtful, a second note says so.

## 4. Module: Location (LOC-01)

### 4.1 What it requests

- Location while the app is in use. [UNVERIFIED: authorization levels]
- Optionally, in a separate participant step, background/continuous location for locked-device observation. The probe requests the higher level only after the participant has seen results from the lower one and opted in. It does not request broader permission to hide a failed test.
- Approximate versus precise location: record whichever the OS grants; do not require precise. [UNVERIFIED]
- Sampling strategy is a **predeclared, recorded parameter** (for example continuous standard updates versus significant-change monitoring versus visits). Which strategies exist and their background behavior are [UNVERIFIED]; BAT-01 chooses among them, so LOC-01 may run more than one strategy in separate labeled sessions.

### 4.2 Pre-prompt explanation (draft)

> **Location.** This test records where this phone reports it is, so we can see how well location can be collected and how much battery it uses. It reads the phone's position at a rate shown on the next screen. Records are stored only on this phone until you choose to export them. They are not sent anywhere. You can pause at any time here, or turn it off in iPhone Settings, and you can delete what was recorded. We are not collecting names of places, contacts, or anyone else's location. Choosing "Continue" will show an iPhone permission question.

Second-step text before requesting background location (draft):

> **Keep recording when the screen is locked?** This lets the test run while the phone is locked or this app is not on screen so we can see how complete the record is and what it costs in battery. A system indicator may appear while this is active. It is optional; the foreground-only test is still useful.

### 4.3 Info.plist purpose strings (draft, all [UNVERIFIED] names)

| Key (verify) | Draft text |
|---|---|
| `NSLocationWhenInUseUsageDescription` [UNVERIFIED] | "Panoptes Sensor Probe records this phone's location while the app is open so you can see how well location collection works. Data stays on this phone until you export it." |
| `NSLocationAlwaysAndWhenInUseUsageDescription` [UNVERIFIED; may differ by SDK] | "Allows the test to keep recording location when the screen is locked, so the probe can measure completeness and battery use. You can pause or stop it at any time." |
| Background location capability declaration (a background-modes entry) [UNVERIFIED name and requirement] | Not a text string. Declared only if the background test is built; recorded in ENV-01. |

### 4.4 Pause/resume and revocation

- Pause stops location updates. A paused interval is a gap, recorded as `gap_reason = participant_paused`.
- Revocation moves the module to `blocked_by_os`; a downgrade from "always" to "while in use" is recorded as a scope change, not as revocation. [UNVERIFIED that the OS distinguishes these]
- Force-quit/relaunch is a separate labeled condition (`condition = force_quit_relaunch`). The probe does not promise continuous execution and does not infer movement or stillness from a gap.

### 4.5 Fields recorded for LOC-01

Per **session** (result-level):

- case ID, procedure version, session ID, condition (`foreground`, `background`, `locked`, `paused`, `revoked`, `force_quit_relaunch`, `resumed`), sampling strategy and parameters, start/end time with time-zone context.
- OS-reported availability/authorization/precision scope and when observed.
- sample count; first and latest sample timestamps; count of observed gaps and longest gap; accessible history window (if the API offers any, otherwise `unknown`).
- battery start/end and charging state links to BAT-01 session ID (not a duplicate).
- export attempted/succeeded (see section 11), scope of export, bounded re-read check result.

Per **sample** (device-local, never in logs):

- event timestamp (source time), receive time, granularity = `point`.
- latitude/longitude, horizontal accuracy and any provided speed/course/altitude quality fields; whether the sample was delivered live, batched, or after relaunch. [UNVERIFIED field availability]
- source flag if the OS marks a sample as simulated or produced by an accessory. [UNVERIFIED]

Sample-level coordinates are sensitive. The spec forbids placing them in logs, screenshots committed to Git, or the repository result file (section 10).

## 5. Module: Motion (MOT-01)

### 5.1 What it requests

- Motion and activity access for (a) a bounded historical activity query, (b) live activity updates, (c) pedometer data, treated as three separable capabilities that may differ in availability and history window. [UNVERIFIED: all three, and their history limits]
- Authorization status is queryable for this API family on the OS in question. [UNVERIFIED]

### 5.2 Pre-prompt explanation (draft)

> **Motion.** This test asks the iPhone for the movement types it has already detected (for example walking, stationary, or in a vehicle) and step counts, and optionally listens for them live. It does not read raw accelerometer data and does not see where you are. Records stay on this phone until you export. You can pause, turn it off in Settings, or delete what was recorded. If the phone has no history available, the screen will say so rather than showing zero.

### 5.3 Info.plist purpose string (draft)

| Key (verify) | Draft text |
|---|---|
| `NSMotionUsageDescription` [UNVERIFIED] | "Panoptes Sensor Probe reads the phone's motion and activity classifications and step counts to test what movement information can be collected. Data stays on this phone until you export it." |

### 5.4 Pause/resume and revocation

- Pause stops live updates and stops historical queries. Resume asks about backfill per 3.3. Historical OS-held data for the paused period can be queried later; whether to do so is the participant's choice.
- Revocation is observed on next foreground; behavior of in-flight queries is recorded as observed. [UNVERIFIED]

### 5.5 Fields recorded for MOT-01

Per session: case ID, procedure version, condition, query window (start/end, time zone), which of the three capabilities ran, OS-reported availability/authorization and observation time, record count per capability, earliest and latest record timestamps, the **oldest history actually returned** versus oldest requested (to expose history limits), count of gaps, export result.

Per record: start/end timestamps (granularity = `interval` for classified activity; `aggregate` for pedometer counts over a window), classification label as delivered, source-reported confidence level (as an ordinal, not converted to a percentage), unit for counts. Classifications are labeled as device-reported labels, not as observed behavior.

## 6. Module: HealthKit (HLT-01)

### 6.1 What it requests

- **Read** access only, for a short, explicit list of data types chosen by the participant from an on-screen list (candidates: step count, walking/running distance; heart rate and sleep only if records from a real producer exist). Producer availability determines usefulness; no Apple Watch is assumed. [UNVERIFIED: type identifiers]
- No write (share) access of any kind.
- Health data is available only on supported devices. [UNVERIFIED]

### 6.2 Authorization model (special case)

- HealthKit deliberately does **not** expose whether *read* access was granted to a given type. [UNVERIFIED: this is believed to be true and is the reason the repository forbids inferring denial from emptiness]
- The probe therefore reports, for every requested type: `availability` (device supports HealthKit and the type), `request_shown` (the probe called the request flow: yes/no), and `read_authorization = unknown_not_exposed`.
- **Write** authorization status, if it were read, is a different thing and must never be used as a proxy for read access (SYN-07). The probe does not request or show it.
- An empty query result is reported as `record_count = 0`, with the interpretation field fixed to: "zero records returned; cannot distinguish no data, no permission, or no recorded activity." It must never emit a zero measurement.
- A non-empty result is evidence that read access exists *for that type and window*, and may be recorded as an observed fact (`read_evidenced_by_data = true`). It does not generalize to other types.

### 6.3 Pre-prompt explanation (draft)

> **Health.** This test looks at which kinds of Health records already exist on this phone and which apps or devices recorded them, to learn what could be collected. You choose the types. The probe only reads; it never writes to Health. The iPhone will not tell this app whether you allowed each type, so the screen will show records if they exist and will say "unknown" otherwise. Having no records does not mean access was refused. Records stay on this phone until you export them. Health data is sensitive: this test is not medical analysis. You can stop and delete anytime, and change access in the Health settings.

### 6.4 Info.plist purpose string (draft)

| Key (verify) | Draft text |
|---|---|
| `NSHealthShareUsageDescription` [UNVERIFIED] | "Panoptes Sensor Probe reads the Health data types you choose to test what health and activity information can be collected. Nothing is written to Health, and data stays on this phone until you export it." |
| `NSHealthUpdateUsageDescription` [UNVERIFIED] | Not used: no write access is requested. If the SDK requires it for any build, record that as a finding rather than adding write access. |
| HealthKit entitlement / capability [UNVERIFIED] | The free-account column lists HealthKit per Apple's membership table cited in the review; the actual provisioning behavior for this account and device is a ENV-01 observation. |

### 6.5 Pause/resume and revocation

- Pause stops queries and any observer/background-delivery registration. [UNVERIFIED names]
- Revocation of read access is **not directly observable**. The probe can only observe that subsequent queries return nothing or fewer records. It records that as an unexplained change in availability, not as "revoked".
- Resume asks about backfill per 3.3.

### 6.6 Fields recorded for HLT-01

Per session: case ID, procedure version, query window and time zone, type list requested, `request_shown`, `read_authorization = unknown_not_exposed`, per-type `record_count` (unit stated, for example samples), earliest and latest start/end timestamps, granularity per type (`point`, `interval`, or `aggregate`), unit, **producer inventory at a safe abstraction** (for example counts by producer class "this iPhone / another app / external device / manual entry / unknown" rather than names), duplicate-or-overlap indicator across producers (observed overlap in time for the same type; the probe does not deduplicate or sum), gap indicators, export result.

Per record: start/end timestamps, value and unit as delivered, producer class, whether the value was user-entered if exposed. [UNVERIFIED] Quantities that the OS provides as statistics over an interval remain `aggregate`; individual samples remain `point` or `interval`; they are never mixed in one count.

## 7. Module: EventKit (EVT-01)

### 7.1 What it requests

- Calendar read access, and optionally reminders read access, requested as separate steps. The probe requests the narrowest available scope that allows reading event times; if only a broader "full access" scope is available for reading, that fact is recorded as a finding and the participant sees the broader scope named in plain language. [UNVERIFIED: scope names, including whether a write-only scope exists and that it cannot read]
- A **synthetic test entry created by the participant** is the default test input (SYN-08). Reading the participant's real calendar is allowed only in real-data-cleared configurations.

### 7.2 Pre-prompt explanation (draft)

> **Calendar and reminders.** This test reads event times and titles' *existence* (not attendees, notes, or links) to learn how scheduled context can be collected. A scheduled event shows what was planned, not what you actually did. The iPhone permission may be broader than what this test uses. This test intentionally ignores attendee names, contacts, descriptions, and meeting links, and does not save them. Records stay on this phone until you export. You can pause, change access in Settings, or delete what was recorded.

The title field is minimized by default (see 7.5): the probe records a title hash or a participant-selected label only if the test needs it; free-text titles are off by default because they often name other people.

### 7.3 Info.plist purpose strings (draft, [UNVERIFIED] key names)

| Key (verify) | Draft text |
|---|---|
| `NSCalendarsFullAccessUsageDescription` [UNVERIFIED; older SDKs used `NSCalendarsUsageDescription`] | "Panoptes Sensor Probe reads event times from your calendar to test how scheduled context can be collected. It does not save attendees, notes, or links, and data stays on this phone until you export it." |
| `NSRemindersFullAccessUsageDescription` [UNVERIFIED; older SDKs used `NSRemindersUsageDescription`] | "Panoptes Sensor Probe reads reminder due dates to test how scheduled context can be collected. Data stays on this phone until you export it." |

### 7.4 Pause/resume and revocation

- Pause stops reading. Resume asks about backfill (events in the paused interval remain in the calendar and can be read later).
- Revocation is detected on next foreground via the OS-reported state; change notifications from the event store, if any, are an optimization not a guarantee. [UNVERIFIED]

### 7.5 Fields recorded for EVT-01

Per session: case ID, procedure version, scope requested and scope granted (as reported), OS availability/authorization and observation time, query window and time zone, counts (timed events, all-day events, recurring-event occurrences, reminders), earliest and latest start timestamps, field inventory (which fields were *read*; which were *excluded by policy*), export result.

Per record: start, end, all-day flag, time-zone identifier of the event (distinct from the device's current zone), recurrence flag and occurrence index if expanded, calendar source class (for example local / account-hosted / subscribed) at a safe abstraction, status (confirmed/tentative/cancelled if exposed). Excluded by policy: attendees, organizer, contacts, notes, URLs, location text, free-text title (unless explicitly enabled for a synthetic test). Granularity is `interval` for timed events; all-day events are marked as dates, not midnight timestamps. Records are labeled `scheduled_context`, never `observed_activity`.

## 8. Controls and status (CTL-01)

This is a cross-cutting module, not a source. It owns the participant-facing control surface and a **control event log**.

Fields recorded per CTL-01 observation:

- source, control action (`explained`, `enabled`, `paused`, `resumed`, `backfill_chosen_yes/no`, `revocation_observed`, `deleted_range`, `exported`, `export_cancelled`), probe state before/after, OS state observed at that moment (per 3.1), time with time zone, and whether the action was taken by the participant or inferred by the probe (for example `revocation_observed`).
- whether the status shown to the participant matched the actual state (a recorded check, not an assumption).
- No sample values, coordinates, titles, or health values appear in control events.

Success criterion (from the protocol): behavior matches the stated scope. It is not "all sources returned records."

## 9. Battery and background reliability (BAT-01)

Not a source; a measurement protocol that the probe supports.

Probe support requirements:

- A **session** concept with a predeclared duration, sampling settings, and an initial acceptable-overhead target, written before the session starts and stored with it.
- Support for a **control session** (collector off) and a **collector-on session** under comparable conditions, with the ability to run repeats.
- Recorded per session: battery level and charging state at start and end (as the OS exposes them [UNVERIFIED]), elapsed time, foreground-use indicator, network type at start/end if observable, low-power mode state if observable [UNVERIFIED], and **collection coverage in the same window** (sample count, expected-versus-observed gap analysis against the sampling strategy).
- The probe reports coverage next to energy; a low-drain session with no background samples is reported as low coverage, not as success.
- Instructions shown to the participant: do not operate the phone unsafely during sessions (no driving to "test location").
- The probe does not attempt to infer cause of drain beyond the declared confounders; a single short or unmatched comparison is labeled exploratory.

## 10. Screen Time module (SCT-01, SCT-02) — separately gated

This module is **not part of the baseline probe build**. It is a separate spike that may be built, blocked, or skipped without affecting any other module. Its blocked state is a valid result.

### 10.1 Entry conditions (all must be recorded before attempting)

- Membership status and the provisioning path for the required capabilities (Family Controls, and for SCT-02 the App and Website Usage entitlement). Per the repository's cited reference, Family Controls (development) is listed under the paid program. Do not purchase membership without owner authorization. [UNVERIFIED current table]
- Installed SDK and runtime support for the newer activity-data API, documented in the review as iOS/iPadOS 26.4+. [UNVERIFIED on the installed SDK]
- Owner's authorization to attempt the authorization request, and the regional/customer-eligibility caveat acknowledged: development success in Canada does not establish customer eligibility.

### 10.2 What it requests

- **SCT-01:** Family Controls authorization at the lowest level that allows presenting a Device Activity report. Reported state recorded as in 3.1 where exposed. [UNVERIFIED enumeration names]
- **SCT-02:** the stronger "approved with data access" authorization state, per the repository's reference (`approvedWithDataAccess`) and the documented export API. `.approved` must not be treated as `.approvedWithDataAccess`.

### 10.3 Pre-prompt explanation (draft)

> **Screen Time (experimental).** This is a separate test of whether Apple lets an app that you install on this phone show or export your app and website usage. It may not be possible for your account or region, and a failure is a useful result. If it works in the standard view, the report is shown inside the app but cannot be copied out; a separate official export path may exist only for certain regions. The iPhone will ask for permission separately and may describe it as managing Screen Time. This test does not block apps or change any limits. You can stop and remove access in Settings.

### 10.4 Info.plist and entitlement notes

- Family Controls capability and, for SCT-02, the App and Website Usage entitlement. The names and provisioning path are [UNVERIFIED]. No purpose string for these authorization flows is assumed; if the SDK requires one, record the finding. [UNVERIFIED]
- The report extension is a separate process with a restricted address space. The spec forbids using any network or shared-container route to carry sensitive report content out of it. [Repository boundary, review 4.2.]

### 10.5 State model

As 3.1, plus a result dimension per case:

| Outcome | Meaning |
|---|---|
| `blocked_prerequisite` | Membership, entitlement, SDK, or region precondition not met; list which. |
| `authorization_not_granted` | Participant declined or OS state not `approved`/`approvedWithDataAccess` as applicable. |
| `report_rendered_no_export` | SCT-01 shows a report; export is not claimed. |
| `export_returned_data` | SCT-02 returned records; scope and provisioning mode recorded. |
| `export_failed` | Error class recorded, no sensitive values. |

### 10.6 Fields recorded (SCT-01 / SCT-02)

Both: case ID, procedure version, run time/time zone, device/OS class (not unique identifiers), exact provisioning and installation mode, entitlements actually present (names only), authorization state observed, region-condition note (minimum necessary), outcome per 10.5.

SCT-01 additionally: whether the standard report rendered, and an explicit "no export attempted across the extension boundary" statement.

SCT-02 additionally: API availability result, query window, record count and counting unit, granularity (`interval` vs `aggregate`), latest timestamp, units, missingness, and the export result. Do not generalize from SCT-01 rendering to SCT-02 export, or from one entitlement to another.

## 11. Local export artifact (test only)

The probe's export is a **local test artifact**, not a Panoptes package.

- Participant-initiated only; the participant chooses sources and a date range; the screen lists exactly what will be in it and its size.
- It is labeled in the UI and in its own metadata as `UNPROTECTED_TEST_ARTIFACT` unless and until the transfer design (D-031 direction, [transfer-package-design.md](transfer-package-design.md)) selects protection and this spec is revised.
- Real-data export is blocked by the real-data gate. A synthetic or throwaway-data export may proceed.
- After export the probe shows an inventory of copies it knows it created (staging file, share-sheet destination if known) and a deletion action for those it controls. Copies made by other apps/destinations are listed as **unverified**, not as deleted.
- The Mac-side import and a bounded re-read of a sample are part of the "export success" evidence, recorded as such; "the share sheet appeared" is not export success.

## 12. Screens and flows (text wireframes)

Layout is illustrative; no UI framework is implied.

### 12.1 Home / status

```text
+--------------------------------------------+
| Sensor Probe                  [TEST BUILD] |
| Not cleared for real data  (gate R: open)  |
+--------------------------------------------+
| Source      Probe      System       Last   |
| Location    paused     authorized*  10:42  |
| Motion      on         authorized   10:44  |
| Health      off        unknown      --     |
| Calendar    blocked    denied       --     |
| Screen Time (not built)                    |
+--------------------------------------------+
| * = scope noted on detail screen           |
| [Explain & enable]  [Run a session]        |
| [Export test data]  [Delete data]          |
+--------------------------------------------+
```

"System" shows the OS-reported state from section 3.1 or `unknown (not exposed)`. "Last" shows the latest record timestamp or `none yet`, never `0`.

### 12.2 Per-source explanation (before the OS prompt)

```text
+--------------------------------------------+
| < Location                                 |
| What this reads:  ...                      |
| How often / when: ...                      |
| Where it is stored: on this phone only     |
| What it does NOT collect: ...              |
| How to pause / delete: ...                 |
|                                            |
| [Continue to system prompt]   [Not now]    |
+--------------------------------------------+
```

"Not now" leaves the source `off`, with no OS prompt triggered.

### 12.3 Source detail

```text
+--------------------------------------------+
| < Health                                   |
| Probe state:   [on | paused | off]         |
| System state:  unknown (not exposed)       |
| Types:         [x] steps  [ ] heart rate   |
| Records found: 128  (latest 2026-.. 09:12) |
|   or: "0 returned; cannot tell why"        |
| Granularity:   aggregate 120 / point 8     |
| Producers:     this phone 120 / other 8    |
| Gaps:          see timeline                |
| [Pause]  [Resume...]  [Delete range...]    |
+--------------------------------------------+
```

### 12.4 Resume choice

```text
+--------------------------------------------+
| Resume Motion                              |
| It was paused 2026-.. 09:00 - 11:30.       |
| Also import records from that period?      |
|   ( ) No (default)  ( ) Yes, mark as       |
|       "backfilled after pause"             |
| [Resume]                                   |
+--------------------------------------------+
```

### 12.5 Session (BAT-01 / LOC-01)

```text
+--------------------------------------------+
| New session                                |
| Type: [control | collector on]             |
| Planned duration:   ____ min               |
| Sampling setting:   ________               |
| Acceptable overhead target: ____           |
| Conditions to note: [ ] charging [ ] wifi  |
| Do not use while driving.                  |
| [Start]   (settings are locked once begun) |
+--------------------------------------------+
```

### 12.6 Export

```text
+--------------------------------------------+
| Export test data                           |
| Sources: [x] Motion  [ ] Location ...      |
| Dates:   from ____ to ____                 |
| Will contain: N records (summary list)     |
| Protection: NONE - test artifact only      |
| Real data blocked until gates are met.     |
| [Create]  [Cancel]                         |
+--------------------------------------------+
```

### 12.7 Copies and deletion

```text
+--------------------------------------------+
| Data and copies                            |
| On this phone:  per-source counts          |
| Export files created by this app: 2        |
|   [Delete]                                 |
| Copies elsewhere (unverified):             |
|   "Shared via ...", not recallable         |
| [Delete all data from this phone]          |
+--------------------------------------------+
```

## 13. On-device result record (provisional shape)

This is a **mapping to the [result template](templates/collection-probe-result.md), not a schema**. It exists so that the Mac side can fill the template without re-deriving fields. It must not be promoted to a production schema without a separate decision (see the D-028 caution in AGENTS.md). Field names are illustrative.

| Result-template section | On-device content | Notes |
|---|---|---|
| 1. Identity and evidence class | `case_id`, `procedure_version`, `run_label` (non-identifying), `run_start`, `run_end`, `time_zone`, `execution` (not_run / blocked / completed), `blocker` (coded), `evidence_class = physical_device` (or `simulator`), `operator_role` | The probe never sets `test_outcome` or `capability_conclusion`; a reviewer does. It supplies observations only. |
| 2. Configuration | `device_class` (model class, no serial), `os_version_build`, `probe_build_version` (no format chosen), `provisioning_mode` (as recorded), `entitlements_present` (names), `authorization_by_type` per 3.1, `participant_scope_ref`, `storage_transfer_design_ref` | Mac versions come from ENV-01, not the device. |
| 3. Procedure | `question`, `expected_behavior_predeclared`, `actions_log` (control events, section 8), `deviations` | Predeclared items are written before the run starts and stored read-only afterwards. |
| 4. Observed data | `query_window`, `source_class`, `granularity_counts` {point, interval, aggregate}, `units`, `record_count` (+ counting unit), `latest_timestamp`, `gaps` (count, longest, reason), `overlap_duplicates_observed`, `empty_result_interpretation`, `validation_errors` (class only) | `record_count` may be `unknown`; `0` means measured zero. |
| 5. Control, export, lifecycle | the checklist from the template, one entry per row, each `not_tested` / `not_applicable(reason)` / observed result | Includes OS-revocation response and backfill behavior. |
| 6. Battery/background | `bat_session_ids`, predeclared parameters, start/end battery, charging, confounders, coverage in the same window | Per section 9. |
| 7. Conclusion and next decision | Not produced on-device | Human-authored on the Mac. |
| 8. Cleanup | `copies_created` (kinds, not paths), `cleanup_done`, `outstanding_unverified` | Paths and recipients are kept in the private inventory. |

Common value rules: unknown is `unknown`, never `0`, `false`, or empty string; every timestamp carries its time-zone context; every count states its unit; records are labeled `observation` (what the OS returned), never `normalized_event`, `hypothesis`, or `inference` (AGENTS.md distinction).

Each sample-level record carries: `source`, `case_id`, `session_id`, `source_event_time` (or interval start/end), `acquisition_time`, `acquisition` (`live` / `backfill_after_pause` / `historical_query`), `granularity`, source-specific fields as described per module, and a local `record_id`. Sample-level data is not part of the repository-bound result.

## 14. Local storage requirements (no store chosen)

The probe's storage engine, file format, and cryptography are **not selected**. The following are requirements any later choice must satisfy; each is verified in ENV-01/CTL-01 or by a later decision before real data:

1. **Local only.** Sample data is written only to app-private local storage. No network egress of participant data, including by dependencies. (A network entitlement not being requested is a build-time check.)
2. **Protection while locked.** An explicit data-protection policy states what the probe can read/write while the device is locked, because background location may need to write while locked. This tension is recorded and tested, not assumed. [UNVERIFIED mechanisms]
3. **Append-oriented**, with source-specific checkpoints, event time and acquisition time stored separately, and a deduplication key per source. (Architecture "Local event store".)
4. **Deletion** by source and date range, removing derived/cached/staged copies the app controls, and recording what could not be removed.
5. **No participant values in** logs, crash reports, analytics, backups the participant did not choose, screenshots, pasteboard, or the repository.
6. **Device backup behavior** (whether the store is included in device backups) is a decision to be made and documented; until then it is recorded as `unknown`. [UNVERIFIED]
7. **Export staging** files are treated as sensitive and tracked for deletion (collection protocol "Real-data gate").
8. **Isolation.** The probe holds one participant's data only; there is no multi-workspace logic on the phone.
9. **Integrity.** Records are written so that a partial write or crash cannot silently look like a complete session (a session has an explicit `closed_normally` marker; a missing marker is reported as `incomplete`).

## 15. Logging rules

Logs are for diagnosing the probe, not for observing the participant.

- **Allowed:** case ID, session ID, source name, state transitions (`off` -> `on`), error class/code, counts, durations, timestamps of control events, OS-state values from 3.1, API availability results.
- **Forbidden:** coordinates, place names, route data, health values and units paired with a time, calendar titles/attendees/notes/URLs, reminder text, device or account identifiers, Apple Account details, tokens or keys, file contents, full file paths containing participant names, and any raw sample.
- Error messages from the OS are logged by **class/code only** if they might embed values; the free-text message is dropped unless reviewed as safe.
- Logs are local, rotated, bounded, and deletable with "Delete all data". They are not transmitted. A debug build must not add a looser logging mode.
- Counts that could re-identify a single event (for example `record_count = 1` for a sensitive type) are acceptable in private evidence but are reviewed before inclusion in any repository-bound summary.
- Sanitized summaries destined for the repository follow the result template: no private values, no complete domain lists, no routes, no raw exports.

## 16. Acceptance checklist

A box is checked only with evidence recorded through the result template. An empty or unchecked box is not a pass.

### Preconditions
- [ ] ENV-01 complete: real `sw_vers` and `xcodebuild -version` recorded; device compatibility confirmed; deployment target selected in a recorded decision (not by this document).
- [ ] Provisioning mode and available entitlements recorded without credentials.
- [ ] Real-data gate status stated on the home screen; real-data flags default off.

### Common
- [ ] Every source has a pre-prompt explanation shown before any OS dialog; "Not now" triggers no OS prompt.
- [ ] Purpose strings match the pre-prompt text and promise nothing the probe does not do; each key verified against the installed SDK.
- [ ] Availability and authorization are shown separately; each source shows only states its API can produce; unknown is displayed as unknown.
- [ ] Zero records are never displayed as denial or as a zero measurement.
- [ ] Pause, resume, backfill choice (default no), and per-source/date-range deletion work and are logged as control events.
- [ ] OS revocation is detected and reflected within the stated observation rule, tested separately from probe pause.
- [ ] Probe never requests write access for any source.

### Per case
- [ ] LOC-01: foreground, locked/background (if attempted), and force-quit/relaunch conditions recorded separately; gaps reported, not interpreted; accessible history stated or `unknown`.
- [ ] MOT-01: capability-by-capability availability and oldest returned history; labels and confidence kept as source-delivered.
- [ ] HLT-01: read authorization shown as unknown/not exposed; producer inventory recorded; overlap shown, not summed; empty-query text matches 6.2.
- [ ] EVT-01: synthetic entry tested for timed/all-day/recurrence/time zone; excluded third-party fields verified absent from storage and export; records labeled scheduled context.
- [ ] CTL-01: status shown matches actual state in each tested condition.
- [ ] BAT-01: predeclared parameters, control and collector-on sessions, repeats, and coverage reported with energy.
- [ ] SCT-01/02 (if attempted): entry conditions recorded; outcomes per 10.5; no report data moved across the extension boundary; no generalization from rendering to export or between entitlements.

### Export, logs, repository
- [ ] Export is participant-initiated, scoped, labeled `UNPROTECTED_TEST_ARTIFACT`, and blocked for real data until gates are met.
- [ ] Export success evidenced by Mac-side import plus bounded re-read, not by display.
- [ ] Copy inventory distinguishes deleted copies from unverified ones.
- [ ] Log review confirms no forbidden values (section 15).
- [ ] No participant data, signing material, or secrets in Git; only a sanitized, reviewed result summary is committed.
- [ ] Results state unavailable capabilities and blockers explicitly alongside successes.

## 17. Open questions

1. Deployment target, Xcode version, and project structure: pending ENV-01 (D-027).
2. Which Info.plist keys and authorization scopes exist in the installed SDK, and which prompts they produce [UNVERIFIED throughout].
3. Which location sampling strategies to compare, and whether background location is attempted in the first trial.
4. Whether HealthKit, Location, and Motion function under the free development account on this device [UNVERIFIED]; whether Family Controls requires the paid program in practice.
5. Whether any Health producer beyond the phone exists (heart rate, sleep), and if no Apple Watch, whether those types are dropped from the slice.
6. Local protection policy while locked versus background writes; device-backup inclusion.
7. Whether the export artifact may exist at all before the transfer design is chosen, or whether the first export is synthetic only.
8. Title handling for EVT-01 (hash, participant label, or excluded).
9. Plain-language review of draft participant text with the owner, including French-language need in Canada (not assessed).
10. Whether SCT-01 and SCT-02 are built in the first round or deferred until the baseline probe has produced results.
