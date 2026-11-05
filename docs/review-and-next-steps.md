# Vision review and next steps

## Status and scope

**Status: product clarification recorded; platform-independent preparation in progress. Collection scope and technical choices remain provisional.**

Prepared on 2026-10-05 after reading all 11 original repository documents, clarifying the project with its owner, and checking the first-party references below. No application has been scaffolded and no iPhone capability has been tested in this session.

The original proposed amendments have now been explicitly reconciled in [D-023 through D-027](decisions.md#review-2026-10-05) and the affected product documents. The owner authorized continuing with available information while deferring the Mac commands. Technical recommendations and collection exit criteria remain provisional, not already-selected frameworks or verified capabilities.

Current handoff: product-document alignment is complete, and a [synthetic App Privacy Report inspector](../spikes/app-privacy-report.md) has [recorded unit-test results](results/app-privacy-report-synthetic.md). Its opt-in coverage report now exposes supported record counts, timestamp extrema with source-line provenance, and explicit unmeasured capability states; it does not establish actual collection completeness. Use [the collection protocol](collection-probe.md) for the remaining cases. The [inspiration study](inspirations-and-collection-patterns.md) compares Foundry, analytics, and spyware capabilities without adopting invasive collection methods. Mac preflight, Xcode scaffolding, device tests, real-data transfer, and the local explorer are not complete.

## 1. Confirmed product intent

> Panoptes Laplace connects personal data into an explorable intelligence system, revealing what those traces can say about a person's life.

The useful analogy is a **personal Foundry**: heterogeneous observations become connected objects, relationships, timelines, and inspectable analytical findings. The dashboard is the main surface for understanding this information; the ontology supplies its meaning and evidence structure. This does not require copying Palantir's interface, choosing a graph database, or simulating an entire person.

The owner clarified that:

- Understanding patterns is itself a useful outcome. Not every insight needs a recommendation, notification, or intervention.
- Profiles, ad/offer analysis, pricing investigations, and forecasts are possible applications, not the defining purpose or compulsory first demonstration.
- Both self-operated and explicitly authorized researcher-assisted use are central. A separate researcher must not be a prerequisite for self-use.
- The relevant digital life is primarily in iPhone apps, not a desktop browser.
- Analysis should run on the owner's local computer; classification and clustering are candidate methods, not prerequisites for every finding.
- The ambition includes interaction and consumption metadata, where it can legitimately be obtained, as well as physical activity and other life domains.

The product must distinguish what available traces **could reveal** from what a particular company demonstrably collected or concluded. A combined personal dataset is not evidence that every outside observer has access to all of its sources.

## 2. Reported test environment

| Item | Current knowledge |
|---|---|
| Test phone | iPhone 15 Pro, reported by the owner |
| Installed iOS | 26.6.1, reported by the owner; not inspected here |
| Device location | Canada |
| Apple Account country/region | Not separately established; Canadian device location already prevents assuming EU customer eligibility |
| Development Mac | Available with Xcode, reported by the owner |
| Exact macOS and Xcode versions | macOS 15.7.9 (build 24G830), owner-pasted 2026-11-04. `xcodebuild -version` failed: the active developer directory is Command Line Tools, so Xcode is either not installed or not selected. Xcode version unknown; deployment target still unselected (D-027) |
| Apple Developer Program membership | Not yet established |
| Apple Watch / other Health data producers | Not yet established |
| Current agent environment | Windows; `xcodebuild` is unavailable here |

Before selecting an iOS deployment target or scaffolding an Xcode project, collect on the Mac:

```bash
sw_vers
xcodebuild -version
```

Confirm that the installed Xcode supports the test device. Do not interpret the availability of one API in iOS 26.4 as a decision to make 26.4 the entire application's minimum version.

## 3. Decision reconciliation

This table retains the review's rationale and identifies the recorded treatment of the original baseline.

| Existing direction | Recorded treatment | Reason |
|---|---|---|
| Historical imports plus authorized live iPhone collection (D-001) | Retain | The combination supports breadth and longitudinal understanding. |
| Privacy revelation plus personal utility (D-002) | Replaced by D-023 | Understanding is utility; an action is not mandatory for every finding. |
| Researcher raw-data access (D-007) | Replaced by D-024 | It is an explicitly authorized operating mode, not a requirement for the owner to analyze their own data. |
| Participant-controlled encrypted batch transfer (D-008) | Retain for the first prototype | It supports local analysis without adding a continuous service. Clearly expose data freshness and manual-transfer limits. |
| Local Mac workbench and Swift/Python direction (D-009/D-010) | Mac retained through D-024; D-010 remains provisional | A Mac is available, native iOS access is relevant, and local analytics fits the request. Exact versions, storage, and UI frameworks remain unselected. |
| Researcher workbench and participant experience (D-011) | Replaced by D-024 | The same analytical capabilities should serve the self-operator and the authorized researcher, with different access boundaries. |
| Statistical/ML evidence, not fluent prose as proof (D-012) | Retain | Evaluate analytical methods by measurable evidence. A language model may assist without becoming an authority merely because it is newer. |
| Mandatory profile + Monday forecast + useful association (D-014) | Replaced by D-025 | First prove connected personal exploration and honest analysis. Forecasting becomes an optional later benchmark; a positive association cannot be guaranteed. |
| Temporal ontology and isolated workspaces (D-015/D-016) | Retain, implement minimally | Preserve meaning, provenance, and isolation without building every conceptual object or view at once. |
| Free developer account until justified otherwise (D-006) | Retain with a capability-specific gate | Do not promise free-account support for capabilities Apple restricts to paid membership. Do not purchase membership automatically. |

The documentation-alignment pass preserved the superseded entries and added replacements in the decision log. Active guidance, the README, product vision, MVP, architecture, ontology, inference, trust, and branding text now reflect the clarification. D-026 records the provisional collection-lab expansion, and D-027 records the Mac preflight gate. Naming, license selection, continuous sync, external models, and cross-participant research remain separate open/deferred matters.

## 4. Reference-checked collection boundaries

These are **documented paths to test**, not on-device results. Distinguish API availability, entitlement/provisioning, authorization, actual records, and exportability.

### 4.1 A useful omitted source: App Privacy Report

Apple documents a participant-initiated share/export of App Privacy Report as newline-delimited JSON. It covers the last seven days after recording is enabled and includes sensitive-resource access records and network-domain activity. [A1, A2]

This could support questions such as which apps accessed a resource or contacted the same domain. It does **not** expose transmitted payloads, the exact content consumed, or the company's resulting inference.

Preserve the native semantics:

- Resource-access records can describe interval starts and ends.
- Network records include aggregated hit counts and first/most-recent timestamps. Do not manufacture individual request events or page views from those aggregates.
- Contacting a domain is not, by itself, proof of surveillance, profiling, or a particular data transfer. Resource access also does not prove that the app's developer received the data.
- Apple excludes browser private-browsing network activity from this report; absence of a record is not proof of no activity.
- Repeated seven-day exports overlap; do not sum overlapping totals as independent observations.

This is an import candidate, not an automatic background API available to Panoptes.

### 4.2 Screen Time has two materially different paths

**Standard Device Activity report:** Apple's report extension is sandboxed against network requests and moving sensitive content outside its address space. Rendering a report is not equivalent to exporting its underlying data to the Mac. Do not attempt to bypass that boundary. [A3]

**Newer official export:** Apple documents `FamilyActivityData` and `DeviceActivityData.activityData(filteredBy:using:)` starting in iOS/iPadOS 26.4. The latter explicitly supports exporting activity data for another app or platform. It requires the App and Website Usage entitlement and `approvedWithDataAccess` authorization. [A4, A5, A6]

Apple states that development/testing can occur in any region, but customer installations require both an EU-located device and an Apple Account with an EU country/region. Therefore:

- The reported phone OS is new enough for the API's documented availability, subject to actual SDK/device checks.
- Canada is not automatically a development-testing blocker.
- A successful development build in Canada would not establish availability for ordinary Canadian users.
- Sideloading is not, by itself, proof of entitlement or regional eligibility. Record the exact provisioning and installation mode.
- The main prototype must not depend on universal raw Screen Time export.

Apple's membership table lists **Family Controls (development)** under the paid Apple Developer Program, not the free Apple Developer column. It lists HealthKit in the free column. Verify the newer export entitlement's actual provisioning path separately; do not generalize one capability's eligibility to another. [A7, A8]

### 4.3 Interaction metadata is source-dependent

A native app can observe interactions inside its own interface; an unrelated iPhone collector does not automatically receive those scroll events, taps, or feed-item dwell times. Apple's sandbox boundary still applies. [A9]

Potential legitimate paths include the service's own account export/API, participant-shared content or annotations, and instrumentation of authorized Safari pages. Safari permissions do not grant access to native social apps. Do not equate a share, screenshot, or watch-history record with a complete interaction trace. [A10]

A browser extension is therefore optional, not a substitute for the owner's primarily native-app usage. Exact third-party scroll behavior remains an explicit coverage gap unless a source-specific route is demonstrated.

### 4.4 Health availability depends on its producers

The iPhone can supply steps and walking/running distance. Health can also receive records from compatible apps and devices. Heart-rate and sleep analyses must depend on actual available records and their sources, not merely on HealthKit being present. Do not assume the participant owns an Apple Watch. [A11]

### 4.5 Coverage matrix to complete with the probe

| Domain | Candidate path | What must be demonstrated |
|---|---|---|
| Place and movement | Core Location, Core Motion | Authorization, available history, locked/background behavior, sampling gaps, battery cost, export |
| Health/activity | HealthKit | Existing data producers, permitted types, units, overlap/deduplication, available records |
| Calendar/context | EventKit | Read access, time zones, recurrence, useful fields without unnecessary third-party details |
| App-resource/network metadata | App Privacy Report import | Actual export format on the device, seven-day windows, overlap handling, preserved aggregate semantics |
| App/website usage | Separate Family Controls / Device Activity spike | Membership, entitlement, region, provisioning mode, authorization, granularity, legitimate export |
| Content consumption | One export from a service actually used by the owner | Which fields really exist, timestamps, missingness, stable identifiers, current provider schema |
| Spending | Optional participant-provided transaction export | Availability and minimum needed fields; no assumption of a general iPhone transaction-history API |
| Detailed scrolling/dwell/taps | Source-specific export or explicitly instrumented surface | Whether obtainable at all; do not claim device-wide coverage |

The native-source rows retain the existing Sensor Probe intent; they are not new claims that those paths have passed device tests.

## 5. Delivery sequence and current status

### Step 1 — Align the documentation and establish the test baseline

Product-document alignment is complete. Mac version outputs and signing capability checks remain pending at the owner's request. Both the self-operated path and optional researcher sharing are documented. This step's native-build prerequisites are not complete.

**Exit:** the decision log and active guidance describe the same product; deployment prerequisites and unknown capabilities are visible. No framework or minimum OS is selected merely to fill an empty field.

### Step 2 — Run a collection feasibility lab

Preparation is specified in [the collection protocol](collection-probe.md). A documented subset of privacy-report semantics has synthetic test coverage; native-device and real-data tests have not been executed. Extend the existing **Sensor Probe** approach rather than beginning with the full dashboard:

- Test Location, Motion, HealthKit, and EventKit independently on the physical phone.
- Test App Privacy Report export/import and inspect one relevant account-export schema.
- Run the Screen Time investigation as a separately gated spike; record failures as useful results.
- Record source support, provisioning context, OS authorization where observable, record count, latest timestamp, units/granularity, foreground/background/locked behavior, export success, and limitations.
- Test pause/resume and revocation behavior; distinguish no data, unknown access, unsupported capability, and exposed denial states. In particular, absence of HealthKit records must not be labeled proof of read denial.
- Measure background reliability and battery impact against a comparable baseline before selecting a sampling strategy.

Use synthetic files for parser fixtures and repository examples. Before transferring real data, define protected local storage, export encryption/key handling, and deletion of the copies created by the test. Native source exports may be unencrypted: treat staging files as sensitive, not as ready-to-share Panoptes packages. Never put personal exports or secrets in Git or ask the participant to paste them into chat.

**Exit:** a reproducible capability report identifies useful, exportable sources and honest gaps. The next slice should use at least three useful categories across two domains, including a digital-behavior or app-metadata source. If coverage cannot support that, revisit the slice explicitly rather than quietly narrowing the product to a health dashboard.

### Step 3 — Build one small, local end-to-end explorer

After collection feasibility is established, implement the smallest useful path:

```text
Authorized phone records / participant-provided exports
    -> validated local import
    -> source-aware events and a small connected data model
    -> timeline, source coverage, and linked object/detail views
    -> evidence-backed analytical findings
```

Preserve raw/source representation where justified, stable source identifiers, schema/method versions, event time versus import time, time-zone context, source quality, missingness, and provenance. Keep aggregate records aggregate. A shared timeline means records can be compared; it does not assert causal links.

Use only the object and relationship types the selected data needs. A graph database, elaborate graph canvas, cloud service, and complete ontology editor are not prerequisites. Choose storage and UI frameworks after the probe establishes actual shapes, volumes, and query needs.

**Exit:** the owner can explore connected records from the selected sources and trace a derived result back to its inputs. Test repeated/overlapping imports, timestamps, source corrections, deletion of downstream derivatives, and isolation using two synthetic workspaces. No separate researcher is needed to operate the self-use path; researcher access remains separately authorized.

### Step 4 — Add one reproducible analytical investigation

Choose a question supported by the actual data rather than forcing the illustrative health, ad, or travel examples. Start with descriptive patterns and simple baselines; introduce classification, clustering, or other models where they answer a clear question.

The result must show its input window, source coverage, method/version, sample unit and sample size, uncertainty, supporting/contradicting evidence, and relevant alternative explanations. Sensor accuracy, model probability, statistical uncertainty, and participant agreement are separate concepts.

Separate exploratory findings from later validation. Repeated measurements are not automatically independent samples; avoid turning a large number of sensor records into a fictitiously large number of independent days. For broad association searches, address repeated testing and temporal dependence before making strong claims.

**Exit:** an analysis can be reproduced and inspected. A null finding or insufficient-evidence result is valid. A short collection trial establishes pipeline feasibility, not a guarantee of stable personal relationships or calibrated predictions. Future forecasting requires a predeclared score, a baseline, and a verifiable pre-outcome lock; a content hash alone does not prove when the prediction existed.

## 6. Cross-cutting acceptance criteria

- Clearly label observations, imports, interpretations, hypotheses, inferences, and predictions.
- Show collection scope, missing periods, freshness, and inaccessible categories prominently.
- Never label aggregate domain contacts as exact content consumption or inaccessible company profiles as observed facts.
- Every published finding retains source lineage, method/version, uncertainty, and a correction path.
- Correlations remain correlations; no clinical conclusions are implied by illustrative health examples.
- Test participant control: pause, select what to share, inspect, correct, export, and delete.
- Specify isolation, key management, derived-data invalidation, retention, and deletion limits before recruiting external participants. Revoking future access does not technically claw back an already decrypted copy.
- No external AI service receives personal data by default.
- No mandatory positive finding, Monday forecast, notification, or intervention is needed to prove the explorer's value.

## 7. Deliberately not selected in this plan

- Minimum iOS/macOS versions and exact build settings
- Paid developer membership or entitlement approvals
- Local database, graph technology, Python framework, or UI stack
- Export cryptography and key-exchange implementation
- A specific local or external LLM
- Universal background collection, device-wide scrolling capture, or all-platform visibility
- Continuous synchronization and automatic interventions
- A clinical/financial recommendation feature or guaranteed inference accuracy

These require concrete evidence and, where consequential, an explicit decision before implementation. Continue platform-independent collection-lab preparation now. Mac preflight still gates native scaffolding; it does not block documentation or synthetic test-case design. The complete Foundry-like interface comes after collection feasibility, not before it.

## References checked

Sources were checked on 2026-10-05. Apple developer pages that required JavaScript were read through their public DocC JSON representations. These are documentation checks only; recheck against the installed SDK and actual device.

- **A1:** Apple, [Inspecting app activity data](https://developer.apple.com/documentation/network/inspecting-app-activity-data). Share/export, NDJSON schema, seven-day window, resource-access records, and network aggregates.
- **A2:** Apple, [About App Privacy Report](https://support.apple.com/en-us/102188). User-facing feature and collection scope.
- **A3:** Apple, [DeviceActivityReport](https://developer.apple.com/documentation/deviceactivity/deviceactivityreport). Report-extension privacy sandbox.
- **A4:** Apple, [FamilyActivityData](https://developer.apple.com/documentation/familycontrols/familyactivitydata). Region, authorization, entitlement; iOS 26.4 availability confirmed in [DocC metadata](https://developer.apple.com/tutorials/data/documentation/familycontrols/familyactivitydata.json).
- **A5:** Apple, [activityData(filteredBy:using:)](https://developer.apple.com/documentation/deviceactivity/deviceactivitydata/activitydata%28filteredby%3Ausing%3A%29). Official export purpose and regional restrictions; iOS 26.4 availability confirmed in [DocC metadata](https://developer.apple.com/tutorials/data/documentation/deviceactivity/deviceactivitydata/activitydata%28filteredby%3Ausing%3A%29.json).
- **A6:** Apple, [Family Controls App and Website Usage entitlement](https://developer.apple.com/documentation/bundleresources/entitlements/com.apple.developer.family-controls.app-and-website-usage).
- **A7:** Apple, [Supported capabilities (iOS)](https://developer.apple.com/help/account/reference/supported-capabilities-ios/). Checked the HTML table's actual membership checkmarks, which were lost in the readable-text extraction.
- **A8:** Apple, [Configuring Family Controls](https://developer.apple.com/documentation/xcode/configuring-family-controls). Development and distribution provisioning requirements.
- **A9:** Apple, [Security of runtime process in iOS, iPadOS and visionOS](https://support.apple.com/en-gb/guide/security/sec15bfe098e/web). App sandbox and system-mediated access.
- **A10:** Apple, [Managing Safari web extension permissions](https://developer.apple.com/documentation/safariservices/managing-safari-web-extension-permissions). Site access and content-script permissions.
- **A11:** Apple, [Use the Health app on your iPhone or iPad](https://support.apple.com/en-us/104997). Phone activity measurements and compatible data producers.
- **P1:** Palantir, [Ontology overview](https://www.palantir.com/docs/foundry/ontology/overview/). General conceptual reference for connected objects, properties, links, and analytical interfaces; not an implementation or visual-design requirement.
