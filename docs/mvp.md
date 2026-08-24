# V1 and first experiment

## Objective

V1 must prove that heterogeneous personal data can be transformed into an evidence-backed ontology that produces a memorable prediction and at least one useful cross-domain insight.

The first version is a research prototype, not a general consumer release.

## V1 components

### Native iPhone collector

Planned responsibilities:

- request and explain each permission independently;
- collect supported location, motion, activity, sleep, and calendar signals;
- investigate permitted Screen Time collection;
- preserve source and observation timestamps;
- display collection status;
- store records locally with platform data protection;
- let the participant pause and delete collection;
- create a participant-initiated encrypted export; and
- import validated insight packages for local presentation and notifications.

### Local Mac research workbench

Planned responsibilities:

- create isolated participant workspaces;
- validate and import encrypted packages;
- retain the original record alongside normalized data;
- explore raw records through timelines, maps, tables, and graphs;
- construct and inspect the ontology;
- cluster places, activities, and repeated sequences;
- define, execute, and evaluate inference rules;
- timestamp predictions before the predicted period;
- compare predictions against actual outcomes; and
- export approved insights to the participant.

The working implementation direction is a local Python analysis layer with a local browser or desktop interface. Exact frameworks are not yet selected.

### Historical import system

The first importer targets Google-provided account or device exports where relevant data is available. Import availability and schema stability require a technical spike.

The importer architecture should be modular so that future connectors can support additional account exports without changing the canonical event model.

## Initial source set

The source set is chosen to support the hero demonstration rather than to represent the complete vision.

| Source | V1 intent | Status |
|---|---|---|
| Core Location | Visits, routes, recurring places, mobility routines | Planned |
| Core Motion | Walking, driving, stationary periods, activity context | Planned |
| HealthKit | Authorized sleep and activity signals | Planned |
| EventKit | Authorized calendar events and routines | Planned |
| Screen Time APIs | Device/application usage where Apple permits it | Technical spike required |
| Screen Time import fallback | Participant-provided report or screenshot if API access is insufficient | Provisional |
| Google export | Historical activity/location data where available | Technical spike required |

Photos, contacts, browsing, purchases, music, and additional platforms belong to the connector roadmap, not the first build.

## Hero demonstration

V1 uses a combined narrative with three outcomes.

### 1. What does the data know?

Generate an inferred participant profile with evidence and confidence. Initial examples may include recurring places, routine windows, mobility modes, and repeated sequences.

### 2. Predict my Monday

Create a forecast before the target Monday. A prediction may include probable departure, arrival, destination, activity, and transition windows.

The forecast must be timestamped and immutable or content-hashed before Monday so that evaluation cannot benefit from hindsight.

### 3. Discover something useful

Find at least one cross-domain pattern, such as evening device activity versus sleep quality, then create an evidence-backed notification or participant-approved experiment.

## First pilot protocol

1. Recruit one fully informed adult participant.
2. Review collection categories and researcher access.
3. Install the sideloaded iPhone collector.
4. Import available historical information.
5. Collect approximately 14 days of live data; extend if the routine is too sparse.
6. Transfer an encrypted, participant-initiated export to the research Mac.
7. Build and review the participant ontology.
8. Generate and lock the Monday forecast.
9. Return an insight package to the participant.
10. Collect Monday's actual observations.
11. Score forecast accuracy and inference usefulness.
12. Let the participant inspect, correct, export, or delete their workspace.
13. Repeat with additional participants after addressing failures.

## V1 acceptance criteria

The first successful prototype should demonstrate all of the following:

- One physical iPhone collects at least three supported native data categories.
- One historical export is imported, if an available participant export supports the use case.
- Records normalize into a source-aware canonical event model.
- One participant ontology can be explored by object, relationship, time, and source.
- Every published inference links to supporting evidence.
- One Monday forecast is locked before the predicted period and evaluated afterward.
- One cross-domain association is measured rather than merely narrated.
- One approved insight reaches the participant as a local report or notification.
- Participant feedback can confirm, reject, or correct the conclusion.
- The participant can pause collection and delete their data.
- A second participant workspace can be created without mixing records.

## Suggested delivery phases

### Phase 0: feasibility spikes

- Verify free Apple provisioning on the test device.
- Test background location behavior and battery cost.
- Test HealthKit, Core Motion, and EventKit authorization/data availability.
- Determine what Screen Time data can be legitimately obtained in this build and entitlement context.
- Inspect an actual participant-authorized Google export.
- Select the encrypted transfer format.

### Phase 1: trustworthy collection

Build source adapters, the canonical event envelope, local storage, collection status, pause/delete controls, and export.

### Phase 2: ontology workbench

Build isolated participant imports, provenance, temporal exploration, typed objects and links, and corrections.

### Phase 3: Laplace inference loop

Implement routine clustering, baseline statistics, Monday forecasting, cross-domain analysis, evidence packaging, and prediction evaluation.

### Phase 4: participant action loop

Return insights to the iPhone, schedule local notifications, capture participant feedback, and measure outcomes.

### Phase 5: repeatability

Run the same pipeline with additional participants and document where inference definitions generalize or fail.

## Deferred from V1

- App Store deployment
- Paid Apple Developer membership unless a tested capability requires it
- Continuous synchronization
- Cloud researcher dashboard
- Cross-participant social relationships
- Cross-participant aggregate modeling
- Final local versus external LLM decision
- Clinical or diagnostic claims
- Automatic interventions beyond participant-approved notifications
- Complete coverage of every available personal data source
