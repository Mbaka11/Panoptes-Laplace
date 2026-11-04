# V1 and first experiment

## Objective

V1 should prove that heterogeneous personal data can become an explorable, evidence-backed ontology and support a reproducible analytical investigation. Understanding is itself valuable. A positive association, profile, Monday forecast, notification, or intervention is not required.

This is a research prototype, not a general consumer release. The scope follows D-023 through D-027 in [the decision log](decisions.md). Numerical source-coverage targets below remain provisional until the collection lab establishes feasibility.

## Operating modes

- **Self-operated:** the participant collects/imports their own data and operates the local workbench. No separate researcher is required.
- **Researcher-assisted:** the participant explicitly selects and shares an encrypted package with an authorized researcher, who uses an isolated workspace for the agreed purpose.

Both modes are central. Begin with the owner's self-use and test isolation with synthetic workspaces before recruiting external participants. Findings do not become more certain simply because either operator reviewed them.

## V1 components

### Native iPhone collector

Planned responsibilities:

- explain and request permissions independently;
- collect supported location, motion, activity, available Health records, and calendar signals;
- investigate Screen Time through a separate capability spike, without assuming raw export;
- preserve event times, source granularity, provenance, and collection gaps;
- display collection status and provide pause/delete controls;
- store records with an explicitly tested protection policy; and
- create a participant-initiated encrypted export.

Returning reviewed insight packages to the phone remains a possible follow-on, not a prerequisite for the first local explorer.

### Local Mac workbench

Planned responsibilities:

- create isolated participant workspaces for either operating mode;
- validate imports and preserve original source meaning alongside normalized data;
- expose source coverage, freshness, and missingness;
- explore a small connected ontology by timeline, object, relationship, and source;
- run a reproducible investigation with supporting and contradicting evidence;
- capture participant interpretations/corrections without rewriting historical findings; and
- export and delete records and dependent results.

Native Swift/SwiftUI collection and Python-oriented local analysis remain the working direction. Exact frameworks, storage, UI packaging, and minimum OS versions have not been selected. A graph database or full graph canvas is not necessary to prove connected exploration.

### Import system

Test App Privacy Report and one participant-owned account export relevant to actual usage. Google remains an initial candidate, not a guarantee that historical location or detailed consumption records will be present. Select the first service-specific importer only after inspecting its available schema and coverage.

Keep connectors modular. Participant annotations, shared content, or screenshots may fill specific gaps, but must retain their manual/partial status rather than masquerading as complete telemetry.

## Candidate source set

The aim is breadth sufficient for connected personal understanding, not complete device visibility.

| Source | Initial purpose | Current status |
|---|---|---|
| Core Location | Places, movement, repeated visits | Native device test pending |
| Core Motion | Available movement/activity context and history | Native device test pending |
| HealthKit | Steps/activity and other records actually supplied by authorized apps/devices | Native device test pending; no Watch assumed |
| EventKit | Calendar/reminder context | Native device test pending; minimize third-party fields |
| App Privacy Report | Resource-access and contacted-domain metadata | Documented user export; local import/device validation pending |
| Relevant account export | Historical activity or consumption context where available | Provider/schema selection pending |
| Screen Time report view | On-device usage presentation | Separate membership/entitlement/authorization test; not a raw export path |
| Newer Screen Time export API | Legitimate activity-data export where eligible | Separate test; development and customer regional eligibility differ |
| Participant input | Explicitly labeled context or correction | Optional supplement, not automatic observation |

A future spending connector may use participant-provided transaction exports. Additional sources such as photos, browsing, music, and purchases remain a roadmap rather than commitments to a full connector suite. Exact scrolling, taps, and feed dwell times in unrelated native apps are not established capabilities.

See [the dated Apple reference checks](review-and-next-steps.md#4-reference-checked-collection-boundaries) and [the collection protocol](collection-probe.md). The reported test phone is in Canada; an EU-only customer API must not become an assumed Canadian customer capability.

## First demonstration

### 1. What data do I actually have?

Show collected/imported categories, time ranges, freshness, missing periods, granularity, and unavailable sources. Separate direct observations, source-provided aggregates, manual entries, and model interpretations.

### 2. How is it connected?

Explore records from different domains on a shared timeline and through meaningful objects and links. Every derived relationship must expose its basis. Temporal proximity alone is not a causal link.

### 3. What does an investigation support?

Choose a question supported by the available sources, state the method and assumptions, and present the result with evidence and uncertainty. A supported association, contradictory evidence, no measured association, and insufficient data are all legitimate outcomes.

## First pilot protocol

1. Review the owner's authorized categories and intended self-operated workflow.
2. Complete the Mac preflight and establish tested protection, encrypted transfer, and deletion procedures before persisting or transferring sensitive test samples.
3. Build and install the minimal probe only after the device/toolchain compatibility checks.
4. Run the collection feasibility lab, including available historical/context imports, and record failures as well as successes.
5. Select the verified source paths and implement the bounded collector/importer slice and self-operated workspace before beginning the pilot collection.
6. Collect enough data to evaluate reliability and coverage; determine the analytical observation period from the selected question, not a promise that 14 days proves a relationship.
7. Transfer selected records to the local Mac and explore the connected data.
8. Run one reproducible investigation and distinguish exploration from later validation.
9. Let the participant inspect, correct, export, and delete data and dependent findings.
10. Verify isolation with a second synthetic workspace, then consider a separately authorized researcher-assisted pilot after trust controls pass.

## Provisional V1 acceptance targets

- The physical phone and imports provide at least three useful categories across two domains, including a digital-behavior or app-metadata source. They need not all be native sensor categories.
- Records preserve source meaning, event/import time, units, granularity, and provenance.
- The owner can explore one connected workspace by object, relationship, time, and source.
- Coverage gaps are visible; lack of access is not misrepresented as lack of activity.
- One analytical investigation is reproducible, with its observation unit, uncertainty, and limitations stated. It need not find a positive relationship.
- Published findings link to their inputs and method/version; exploratory output stays visibly provisional.
- Participant feedback can correct interpretation without silently changing the original evidence.
- Pause, controlled export, and deletion work for the copies and derivatives in scope.
- Repeated and overlapping imports do not invent duplicate activity.
- A second synthetic workspace remains isolated.

If the source target cannot be met, revise the slice explicitly using probe evidence. Do not quietly substitute a health-only dashboard or fabricated digital behavior to satisfy a numerical target.

## Delivery phases

### Phase 0: collection feasibility lab

Follow [the test protocol](collection-probe.md). Separate platform-independent preparation, native-device tests, and real-data handling prerequisites. Mac version collection may happen later; deployment-target selection and Xcode scaffolding may not precede it.

### Phase 1: trustworthy collection and import

Implement verified source paths, a minimal source-aware representation, protection/transfer, status, and pause/delete controls. Choose the concrete formats and key handling through explicit technical decisions before handling real transfers.

### Phase 2: connected local explorer

Build isolated imports, provenance, temporal exploration, the necessary objects/links, and correction/deletion behavior. Prioritize traceable relationships over an elaborate visual graph.

### Phase 3: analytical investigation

Implement descriptive analysis and simple baselines first. Add classification, clustering, association analysis, or other methods only when justified by the question and data. Return inspectable results, including negative or inconclusive ones.

### Optional follow-ons

Profiles, a prospectively scored Monday forecast, phone insight packages, notifications, or N-of-1 experiments can demonstrate further uses. Each receives its own evidence and evaluation requirements; none defines the first explorer's success.

## Deferred from V1's first slice

- App Store deployment and continuous synchronization
- Paid membership unless a capability justifies a separately authorized purchase
- Cloud workbench and cross-participant modeling or relationships
- Final local versus external LLM selection
- Clinical or diagnostic claims
- Automatic consequential interventions
- Complete coverage of every personal source or native-app interaction
- A full ontology editor and every conceptual object/view
