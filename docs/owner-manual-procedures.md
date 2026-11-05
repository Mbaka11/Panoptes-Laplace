# Owner manual procedures (no Mac, no custom app)

## Purpose and status

**Status:** procedure specification. Nothing here has been executed; no result is recorded. Menu paths marked **[UNVERIFIED on iOS 26.6.1]** come from memory of earlier iOS versions or Apple documentation and must be checked on the device. If a menu differs, record the actual path rather than forcing the instruction to fit.

These are steps the owner can take on the iPhone (iOS 26.6.1, Canada) now, using only built-in Settings, the Health app, and a web browser. They support the cases ENV-01 context, HLT-01 (inventory only), APR-01, and ACC-01 in [the collection protocol](collection-probe.md), and define BAT-01 for later use once a collector exists. They do not replace the Mac/Xcode preflight and do not select a deployment target.

Related: [collection protocol](collection-probe.md), [reference-checked boundaries](review-and-next-steps.md#4-reference-checked-collection-boundaries), [result template](templates/collection-probe-result.md).

## Rules that apply to every procedure

1. **Record only safe summaries**: category present/absent, producer type, rough date range, counts as orders of magnitude. Never record values, domain lists, routes, account IDs, device identifiers, or personal content in notes meant for Git or chat.
2. **Never paste raw data into chat or Git.** This includes screenshots of Health data, App Privacy Report contents, and export files. Describe them instead.
3. **Unknown is not zero.** If you did not check, write "unchecked". If a Health category looks empty in the Health app, write "no records visible in the Health app UI", not "access denied" and not "no activity". Empty display never proves the absence of the real-world activity, and it says nothing about whether a future app would be allowed to read it.
4. **Observing is not exporting.** Seeing data in Settings or Health does not show it can be exported; record export success separately.
5. **Raw files stay outside the repository** (and outside synced folders you do not control). Keep at most one copy, in a location you can later delete, and write down where it is in a private note, not in Git.
6. **Do not enable anything just to complete a table.** Enabling App Privacy Report is your choice; leaving it off is a valid recorded result.

## 1. Phone inventory checklist

Goal: learn what the phone can plausibly supply before any app is built. This is an owner report (evidence class: owner-reported configuration), not a device-verified capability.

### 1.1 Health categories and producers

For each category, open Health > Browse (or Summary), open the category, and check whether any data exists and, if so, where it came from. [UNVERIFIED on iOS 26.6.1: the source list is typically under the category > Data Sources & Access, or under the profile picture > Privacy > Apps and Services / Devices; navigation has changed between iOS versions.]

Record, per category: present or absent, producer type (iPhone itself, third-party app, Bluetooth/wearable device, manual entry, other), and rough date range (for example "last 6 months" or "since 2023"). Do not record values.

Categories to check, matching the probe's priorities:

- Steps and walking/running distance (the iPhone itself is the expected producer)
- Activity or exercise minutes, workouts
- Heart rate (requires an actual producer such as a watch, band, or app; none is assumed)
- Sleep (requires an actual producer or manual entry; do not assume)
- Anything else you notice that a connected app or device wrote

Notes:

- Seeing a producer listed under Data Sources & Access can mean it reads, writes, or both. Do not treat a listing as proof of records, or of read permission for a future app.
- Several producers writing the same category may overlap (for example phone and watch steps). Note "multiple producers" without trying to merge them.
- Health sharing permissions you grant later to a test app are separate; the Health app's display is not an authorization record for that app. Never conclude read denial from an empty result in an app.

### 1.2 App Privacy Report status

[UNVERIFIED on iOS 26.6.1] Settings > Privacy & Security > App Privacy Report. Record:

- On or off (or "section not found").
- If on, the approximate date recording started, if the screen shows or you remember it. If unknown, write "unknown", not "7 days".

Only recording after enablement exists; there is no history before it. Apple documents the shareable report as covering up to the last seven days. Browser private-browsing network activity is excluded, so absence of an entry is not proof of no activity.

### 1.3 Services with an account export

List the services you actually use regularly (not services you could imagine using), and for each, whether an export or "download your data" option exists. Check the provider's own help page or settings, but do not start the export yet unless you are also doing section 3.

Candidate to check first: Google Takeout (a candidate, not a committed connector choice). Others depend on what you use.

Record only: service type (search/video/social/shopping/other), export option exists (yes / no / unknown), and format if the provider states it (JSON, CSV, HTML, other). Do not assume the export contains consumption or interaction data; that is what ACC-01 is for.

### 1.4 Fill-in table (safe summaries only)

Copy this table into a private note. Do not commit a filled version containing anything beyond these coarse entries.

| Item | Present / absent / unchecked | Producer type | Rough date range | Notes (no values) |
|---|---|---|---|---|
| Health: steps/distance | | | | |
| Health: workouts/exercise | | | | |
| Health: heart rate | | | | |
| Health: sleep | | | | |
| Health: other category (name type only) | | | | |
| App Privacy Report | on / off / not found | n/a | enabled since: | |
| Service A export offered | yes / no / unknown | service type | n/a | format if stated |
| Service B export offered | yes / no / unknown | service type | n/a | format if stated |
| Google Takeout available to your account | yes / no / unknown | n/a | n/a | |

## 2. APR-01: participant App Privacy Report export

Maps to APR-01 in the protocol. No custom app is required. Evidence class: physical-device observation by the owner.

### 2.1 Enable (optional, your choice)

1. [UNVERIFIED on iOS 26.6.1] Settings > Privacy & Security > App Privacy Report (scroll toward the bottom).
2. If recording is off, there is a "Turn On App Privacy Report" option. Turning it on starts recording from that moment; nothing earlier is available.
3. Write down the date and time you enabled it and your time zone. This is needed to interpret the window.
4. Wait for meaningful use. Apple documents a seven-day report window, so a useful first export is around a week after enabling.

### 2.2 Export (share) the report

1. [UNVERIFIED on iOS 26.6.1] On the App Privacy Report screen, look for "Save App Activity" (earlier iOS versions) or a Share/export control at the bottom.
2. Choose a save location outside any repository and outside shared or synced folders you do not control. [UNVERIFIED: the saved file is expected to be a newline-delimited JSON file; Apple documents NDJSON, but the actual file type must be verified, not assumed.]
3. Do not open the file in a way that uploads it (for example into a cloud AI chat). Do not paste it anywhere.

### 2.3 What to record (safe summary only)

| Field | Record |
|---|---|
| Date/time recording enabled, time zone | |
| Export date/time, time zone | |
| Report window (how far back the data actually goes) | observed, not assumed |
| Export success | succeeded / failed / not attempted; failure message wording if any, with no personal content |
| File type as saved (extension, and whether it opens as text) | |
| File size, order of magnitude | KB / MB / tens of MB |
| Approximate number of lines, order of magnitude | optional; unknown is acceptable |
| Record kinds seen (for example resource-access, network) | kinds only, no names |
| Anything unexpected | |

Do not record app names, domain lists, or timestamps of specific events. Apple-documented semantics to keep in mind when you look: resource-access records can describe intervals, and network records are aggregates with hit counts and first/most-recent times. A contacted domain does not prove what data was sent, and the report does not expose payload content or a company's inference.

### 2.4 Storage and import rule

- The real file must stay outside the repository. It must not be imported into the synthetic spike (`spikes/app_privacy_report.py`) or any other tool until the **real-data gate** in the [protocol](collection-probe.md#real-data-gate--separate-from-the-build-gate) is satisfied: protected storage, tested encrypted transfer, key handling, and deletion of test copies.
- Recommendation: **do not transfer the real file anywhere yet.** Exporting it on the phone and noting the safe summary is enough for APR-01 at this stage. If you keep a copy, treat it as sensitive and plan its deletion.
- Delete test copies when the check is done, and note whether any cloud backup or sync could have captured them (unknown is an acceptable answer).

## 3. ACC-01: request one account export

Maps to ACC-01. Choose ONE service you actually use. Google Takeout is a candidate, not an irrevocable choice. Evidence class: physical observation by the owner.

### 3.1 Choosing the minimal scope

1. Pick the one service whose export is most likely to contain consumption or interaction metadata relevant to the probe (for example watch or search history), not the broadest export.
2. In the provider's export tool, select only the minimal product or product-subset needed. For Google Takeout this means deselecting everything and selecting a single product. [UNVERIFIED: current Takeout UI and per-product options; check on the day.]
3. If a date range or format choice is offered, prefer a short recent range and a machine-readable format (JSON or CSV) over HTML; record what was offered and what you chose. If no range is offered, note that.
4. Prefer a one-time export over recurring exports. Do not enable scheduled exports.
5. Avoid products that mostly contain third-party content (other people's messages, shared photos, contact lists). Exclude them.
6. Record the provider, request date, and the format chosen. Do not record the account identifier.

### 3.2 What to record when it arrives

| Field | Record |
|---|---|
| Provider type and product(s) selected | product names only |
| Request date, arrival date, time zone | |
| Export success | succeeded / failed / partial; reason if known |
| File type (archive, JSON, CSV, HTML) and size order of magnitude | |
| Provider-stated time range vs. range actually present | observed; unknown if unchecked |
| Fields present (yes / no / unknown each) | viewed content, searches, interactions, timestamps, duration, stable identifiers |
| Missingness you noticed | for example "no duration field"; no content |
| Anything surprising about scope | for example unexpected categories included |

Do not infer dwell time from the gap between two unrelated events, or scroll depth from a viewed-content record. A watch or search record is not a complete interaction trace.

### 3.3 Storage rule

Same as for APR-01: the downloaded archive stays outside the repository, is not pasted into chat, and is not imported or transferred until the real-data gate is satisfied. Do not commit it, even partially. Extract it, if at all, only into a private folder you will delete; remember that archive extraction creates additional copies. Delete the provider-side download link or copy when no longer needed, and note whether you did (provider-side deletion of the original data is a separate matter and not claimed).

## 4. BAT-01 session protocol (for later)

**Do not run this until a collector exists** (the native probe is gated on the Mac preflight). BAT-01 compares a collector-off control with collector-on sessions. It also needs the real-data controls where the collector writes persistent samples. Specify all parameters below before the first session and write them down; do not adjust them after seeing results.

### 4.1 Predeclared parameters

- **Session duration:** propose 2 hours per session as a starting value, long enough for a measurable change and short enough to repeat; fix one duration for all sessions. A separate all-day trial is a later, distinct test.
- **Sampling settings:** the collector's configuration (for example location accuracy mode and sampling policy), recorded exactly and unchanged between collector sessions.
- **Acceptable-overhead target:** to be set by the owner before running, expressed as extra battery percentage points per hour relative to control. No target is chosen here.
- **Matched conditions:** same device, same start window of day, similar battery band (for example start between 80 and 100 percent), same Wi-Fi vs. cellular setting, same screen-brightness setting, same background apps, same location of use, and no charging during the session.

### 4.2 Sessions

- Alternate **control** (collector off or not installed state, as defined beforehand) and **collector** sessions, ideally on separate but similar days, with matched time of day.
- Do not run in an unusual state (travel, software update, hot environment).
- Repeat at least three control and three collector sessions before attributing a drain difference to the collector. Fewer is exploratory only.
- Treat a force-quit/relaunch as a separate labelled condition; do not combine it with normal sessions.

### 4.3 What to record per session

| Field | Record |
|---|---|
| Session ID, type (control / collector), date, time zone | |
| Start and end time | |
| Battery % at start and end | |
| Charging state during session | none expected; note any plug-in |
| Screen-on time, and whether foreground use of other apps occurred | approximate minutes |
| Network | Wi-Fi / cellular / mixed; airplane mode if used |
| Low Power Mode | on / off, unchanged across sessions |
| Temperature notes | warm/hot device, hot environment, case, direct sun |
| Device state | locked most of the time? any restart? |
| Collector coverage in the same window | samples collected and gaps, as reported by the collector (unknown if not available) |
| Other confounders | updates, downloads, calls, hotspot, navigation |

Battery percentage is coarse (whole percent) and the "Battery" screen in Settings may offer per-app usage that is approximate and apportioned; treat all as rough. [UNVERIFIED on iOS 26.6.1: location and layout of the Battery screen usage details.]

### 4.4 Safety

- No driving or other unsafe activity during observation. Do not hold the phone or look at it while in motion for any unsafe purpose.
- Do not leave a hot phone in direct sun or a closed car.
- If the device gets unusually hot or the battery swells or behaves oddly, stop the session.

### 4.5 Interpretation

- Results are **exploratory**. Differences of a few percentage points over a few sessions are within the range of ordinary variation from usage and temperature; do not claim a collector cost without repetition.
- Always report energy next to collection coverage. A collector that records few or no background samples may use little battery because it did little; that is not a success.
- A short or unmatched comparison does not establish acceptable all-day behavior. Do not generalize from one device, one OS build, or one collector configuration.
- Record the OS version and collector build with each batch of sessions. An OS update between sessions breaks comparability.
- Use the [result template](templates/collection-probe-result.md) section 6 for the sanitized write-up.

## 5. Putting results into the project

After completing any of the above, create a short owner-reported note (evidence class: owner report) using the [result template](templates/collection-probe-result.md), with all unknown fields left as unknown. Do not mark a case "verified" on the basis of an owner report alone; the capability conclusion for these items stays "unknown" or "observed within stated limits" with the limits written out. Any change to a recorded decision goes through [the decision log](decisions.md).
