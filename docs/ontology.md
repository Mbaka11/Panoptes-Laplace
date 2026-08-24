# Personal ontology

## Purpose

The ontology turns fragmented records into a queryable model of a participant's life. It must support observations, relationships, inferred knowledge, predictions, actions, and outcomes without confusing one category for another.

This is a conceptual model, not a final database schema.

## Design principles

### Temporal by default

Objects and links may change. The model records when something happened, when the system learned it, and when an inference was valid.

### Provenance by default

Every derived property and relationship can be traced to source records and the method that produced it.

### Observation is not inference

A GPS coordinate is an observation. “Home” is an inference. “The participant will leave home at 08:20 Monday” is a prediction. They must have different types and lifecycles.

### Confidence and correction

Derived knowledge carries confidence and can be confirmed, rejected, or corrected by the participant.

### Actionable objects

Predictions and patterns should connect to notifications, experiments, decisions, and measured outcomes rather than ending as visualizations.

### Participant isolation

Every object belongs to exactly one participant workspace in V1. No relationship may cross participant boundaries.

## Core object types

### Identity and access

- **Participant** — owner and subject of one workspace
- **Device** — authorized source device
- **DataSource** — API, export, file, or manual input
- **ConsentGrant** — authorization scope, purpose, duration, and researcher access
- **ResearcherAccess** — authorized researcher and access period

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
    "confidence": 0.95,
    "accuracy_meters": 18.0
  },
  "integrity": {
    "payload_hash": "..."
  }
}
```

The final implementation may use a different serialization, but the concepts above should remain.

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
    ↓ researcher review
Published insight
    ↓ participant feedback / observed outcome
Confirmed, weakened, corrected, or rejected inference
```

## Example: screen usage and sleep

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

## Gotham-inspired operational behavior

The ontology is not only navigated; it supports actions:

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
