# Personal ontology

## Purpose

The ontology turns fragmented records into a queryable model of a participant's life. It must support observations, relationships, inferred knowledge, predictions, actions, and outcomes without confusing one category for another.

This is a conceptual model, not a final database schema or a requirement to implement every listed type. The first slice needs only enough structure for connected personal exploration and evidence inspection. Both self-operated and authorized researcher-assisted workspaces use the model.

## Design principles

### Temporal by default

Objects and links may change. The model records when something happened, when the system learned it, and when an inference was valid.

### Provenance by default

Every derived property and relationship can be traced to source records and the method that produced it.

### Observation is not inference

A GPS coordinate is an observation. “Home” is an inference. “The participant will leave home at 08:20 Monday” is a prediction. They must have different types and lifecycles.

### Confidence and correction

Derived knowledge carries explicitly defined uncertainty and can be confirmed, rejected, or corrected by the participant. Sensor accuracy, model probability, statistical uncertainty, and participant agreement are distinct; a corrected label is not proof of a causal explanation.

### Preserve source granularity

Point observations, time intervals, and windowed aggregates are different. App Privacy Report domain-contact totals must retain their window and provenance; they are not exact browsing events or proof of content consumption. Repeated overlapping imports must not multiply the underlying activity.

### Understanding before optional actions

Connected exploration and an evidence-backed explanation are valid endpoints. Predictions and patterns may also connect to notifications, experiments, decisions, and outcomes; an action is not required for each insight.

### Participant isolation

Every object belongs to exactly one participant workspace in V1. No relationship may cross participant boundaries.

## Core object types

### Identity and access

- **Participant** — owner and subject of one workspace; may also be its operator
- **Device** — authorized source device
- **DataSource** — API, export, file, or manual input
- **ConsentGrant** — authorization scope, purpose, duration, and any optional researcher sharing
- **ResearcherAccess** — separately authorized researcher and access period; not required for self-use

### Place and movement

- **CoordinateObservation**
- **Place**
- **Visit**
- **Route**
- **MobilitySegment**
- **RecurringJourney**

### Time and activity

- **ActivitySession**
- **DeviceUsageSession**
- **SleepSession**
- **WorkoutSession**
- **CalendarEvent**
- **Routine**
- **DayProfile**

### Knowledge and evidence

- **Observation**
- **EvidenceSet**
- **Feature**
- **BehaviorPattern**
- **Hypothesis**
- **Inference**
- **Prediction**
- **ParticipantCorrection**

### Operations

- **Insight**
- **Notification**
- **Intervention**
- **PersonalExperiment**
- **Outcome**
- **Feedback**

## Example relationship types

```text
Participant        OWNS                 Device
Device             RECORDED             Observation
Observation        CAME_FROM            DataSource
Observation        OCCURRED_AT          Place
Participant        VISITED              Place
Visit              PART_OF              Routine
MobilitySegment    CONNECTS             Place -> Place
DeviceUsageSession PRECEDED             SleepSession
BehaviorPattern    SUPPORTED_BY          EvidenceSet
EvidenceSet        CONTAINS              Observation
Inference          DERIVED_FROM          BehaviorPattern
Prediction         PREDICTS              FutureActivity
Insight            EXPLAINS              Inference
Notification       COMMUNICATES          Insight
Intervention       TESTS                 Inference
Outcome            RESULTED_FROM         Intervention
Feedback           CONFIRMS_OR_REJECTS   Insight
ConsentGrant       AUTHORIZES            DataSource
```

Links can themselves carry time ranges, confidence, provenance, and correction history.

## Canonical event envelope

A normalized event could follow this conceptual shape:

```json
{
  "event_id": "evt_...",
  "workspace_id": "participant_...",
  "event_type": "mobility.location_observed",
  "observed_at": "2026-01-01T08:21:00Z",
  "observed_until": null,
  "ingested_at": "2026-01-01T08:21:04Z",
  "source": {
    "source_type": "ios.core_location",
    "device_id": "device_...",
    "source_record_id": "..."
  },
  "consent_grant_id": "consent_...",
  "payload": {},
  "quality": {
    "accuracy_meters": 18.0
  },
  "integrity": {
    "payload_hash": "..."
  }
}
```

The final implementation may use a different serialization, but the concepts above should remain. The example is synthetic and describes one point observation, not a universal schema. Sensor accuracy must not be converted into an unexplained probability. Importers will also need interval/aggregate semantics, time-zone context, schema versions, and missingness appropriate to their source; those field designs remain open.

## Inference object

An inference should capture at least:

- statement or machine-readable conclusion;
- participant workspace;
- input time window;
- method and method version;
- evidence references;
- measured effect or forecast;
- confidence and uncertainty;
- alternative explanations;
- expected-utility assessment;
- review status;
- participant confirmation/correction;
- creation, publication, and expiration times; and
- downstream insights or interventions.

## Fact lifecycle

```text
Raw observation
    ↓ normalization
Canonical event
    ↓ object/link resolution
Ontology assertion
    ↓ analysis
Hypothesis
    ↓ statistical or predictive validation
Candidate inference
    ↓ review appropriate to consequence and operator role
Published insight
    ↓ participant feedback / observed outcome
Confirmed, weakened, corrected, or rejected inference
```

An exploratory view may stop at observations or hypotheses. Unsupported and inconclusive investigations need not become candidate inferences. Corrections preserve history and invalidate or recompute dependent interpretations as appropriate; deleting source data must also account for sensitive derivatives.

## Illustrative extension: screen usage and sleep

The following numbers are synthetic, not measured project results. This example assumes both sources are legitimately available; it is not a promise that a 21-day window validates the relationship or that Screen Time export works on every device. The experiment is optional.

```text
DeviceUsageSession(evening, 3h42m)
    PRECEDED
SleepSession(6h18m, elevated interruptions)

BehaviorPattern
    statement: evenings above 3h screen usage are associated with more interruptions
    input window: previous 21 days
    effect: +21% interruptions relative to personal baseline
    confidence: provisional
    supported by: EvidenceSet(...)

Insight
    privacy view: combined device and sleep data exposes a recurring behavioral association
    utility view: test a lower-screen evening

PersonalExperiment
    intervention: reduce evening screen use
    outcome: compare sleep against baseline
```

## Exploration and optional operational behavior

Following the general ontology-centered ideas of systems such as Foundry, the first explorer lets the participant navigate time, objects, links, coverage, and evidence. Further workflows can support actions:

- correct a place classification;
- confirm or reject a routine;
- approve a notification;
- lock a prediction;
- start or stop an experiment;
- revoke a source permission;
- delete a source/date range;
- compare predicted and actual events; and
- inspect the complete evidence chain.

The visual implementation must be original and should not reproduce Palantir's proprietary interface.

## Open ontology questions

- Graph database versus relational/event representation
- Identity resolution strategy
- Bitemporal history requirements
- Inference-definition representation
- Property-level provenance model
- Sensitive-property labels and review workflow
- Schema and connector versioning
- Participant correction semantics
- Ontology migration strategy
