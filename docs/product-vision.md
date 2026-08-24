# Product vision

## One-sentence thesis

Panoptes collects as much personal data as a participant explicitly authorizes and the platform can legitimately access, organizes it into a temporal ontology, reveals what can be inferred, and gives that intelligence back as explainable predictions and actions.

## Problem

Large technology platforms derive valuable behavioral knowledge from fragmented personal data. Individuals often know that collection occurs but cannot see the resulting model, inspect its evidence, test its accuracy, or use the same intelligence for themselves.

Existing personal dashboards usually present isolated metrics. A sleep chart, screen-time total, location history, and calendar remain separate. The more interesting knowledge exists in the relationships between them:

- Did unusual evening device usage precede interrupted sleep?
- Which sequences define a person's Monday routine?
- How identifiable are home, work, and recurring destinations from location alone?
- Which behavior changed before a participant's baseline shifted?
- How accurately can past observations predict the next day?

## Product promise

Panoptes provides two connected views of every meaningful conclusion.

### What the data reveals

Show what an outside observer could infer, including the evidence, source, confidence, and uncertainty behind the conclusion.

### How the participant can use it

Turn validated knowledge into a forecast, notification, experiment, or other participant-controlled action.

Example:

> Your sleep contained more interruptions than your 14-day baseline. Evenings with more than three hours of screen use were associated with 21% more interruptions. This does not establish causation. Would you like to test a lower-screen evening?

## Intended first users

The first participants are privacy-aware students, technical friends, and other people personally known to the researcher who:

- are curious about what their data reveals;
- understand that this is an experimental prototype;
- knowingly authorize collection and researcher access;
- tolerate sideloading, data exports, and incomplete software; and
- participate as co-designers rather than passive tracking targets.

The first cohort is small and does not require App Store distribution.

## Product pillars

### 1. Broad authorized observation

The long-term system supports many data sources rather than optimizing a single isolated metric. “All available data” means all data the participant explicitly authorizes and the platform can technically and legitimately access. It does not mean bypassing iOS permissions or obtaining nonparticipant data.

### 2. Ontology rather than dashboard

Raw records become typed objects, events, relationships, evidence, predictions, and actions. The product must answer not only “what happened?” but also “how is it connected, what can be inferred, and what can be done?”

### 3. Evidence before narrative

Statistics and ML establish measurable patterns. A language model may classify, suggest hypotheses, and explain results, but it is not itself proof that a correlation exists.

### 4. Utility-first inference

The project does not exclude an inference merely because the subject is uncomfortable or sensitive. It evaluates expected benefit, confidence, actionability, false-positive cost, and privacy/security risk. Consequential conclusions require stronger evidence and review.

### 5. Participant agency

Participants can understand collection, correct conclusions, control researcher access, pause collection, export data, and delete it.

### 6. Closed-loop learning

A useful inference creates an action whose outcome can be measured. Participant feedback and observed results strengthen, weaken, or reject the inference.

## Desired experience

The complete demonstration should tell one coherent story:

1. Import historical data held by technology platforms.
2. Collect authorized live signals from an iPhone.
3. Build a temporal personal ontology.
4. Present a dossier describing what the data reveals.
5. Produce and timestamp a Monday forecast.
6. Discover a cross-domain behavioral pattern.
7. deliver an evidence-backed notification.
8. Compare predictions and interventions with actual outcomes.

## Long-term possibility space

- Continuous encrypted synchronization
- Participant-facing ontology exploration
- More platform and account connectors
- Personalized experiments and intervention tracking
- Local or external language-model adapters
- Reusable inference definitions tested across isolated participant workspaces
- On-device inference for immediate notifications
- Privacy exposure reports showing which source enables each conclusion
- Portable participant-owned personal data models

## Non-goals

Panoptes is not intended to be:

- covert monitoring or stalkerware;
- a method for bypassing operating-system permissions;
- a credential, message, or keystroke collector;
- an analysis system for people who did not participate;
- a generic health dashboard;
- a language-model wrapper that presents generated claims as evidence;
- a clinical diagnostic system; or
- a visual clone of Palantir Gotham.

The project takes inspiration from ontology-centered operational systems: objects, relationships, provenance, decisions, actions, and feedback. It will develop its own implementation and visual identity.

## Measures of success

V1 should measure more than whether the software runs:

- **Coverage:** authorized sources successfully normalized into the ontology.
- **Provenance:** conclusions trace back to original records.
- **Forecast quality:** predicted events compared with timestamped actual events.
- **Inference quality:** effect size, confidence, stability, and false-positive rate.
- **Usefulness:** participant rating and whether an insight prompted a useful action.
- **Correctability:** participant corrections alter the graph and future output.
- **Trust:** participant can inspect collection and successfully pause, export, and delete it.
