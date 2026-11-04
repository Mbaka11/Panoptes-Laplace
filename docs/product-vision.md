# Product vision

## One-sentence thesis

Panoptes Laplace connects personal data that a participant explicitly authorizes and the platform can legitimately access into an explorable intelligence system, revealing what those traces can say about their life.

## Problem

Large technology platforms derive valuable behavioral knowledge from fragmented personal data. Individuals often know that collection occurs but cannot inspect what their own traces make inferable, understand the relationships, or test the resulting claims for themselves.

Panoptes does not promise access to a company's actual internal model. It reveals what the available data supports, which sources enable a conclusion, and what remains unknown. The full personal dataset is not automatically visible to every outside observer.

Existing personal dashboards usually present isolated metrics. A sleep chart, screen-time total, location history, and calendar remain separate. The more interesting knowledge exists in the relationships between them:

- Did unusual evening device usage precede interrupted sleep?
- Which activities, places, consumption patterns, or spending categories change together?
- How identifiable are home, work, and recurring destinations from location alone?
- Which behavior changed before a participant's baseline shifted?
- How accurately can past observations predict the next day?

## Product promise

Panoptes is a personal Foundry-like workbench: a dashboard backed by connected objects, relationships, time, and evidence. It supports open-ended exploration rather than only answering a predetermined prediction or advertising question.

### What the data reveals

Show what an outside observer could infer, including the evidence, source, confidence, and uncertainty behind the conclusion.

### How the participant can understand it

Explore a timeline, follow relationships, compare periods, inspect source records, and test an explanation. Understanding is itself a valid outcome. Validated knowledge may later support a forecast, notification, or participant-controlled experiment, but none is required for every insight.

Illustrative question, not an established finding:

> How do my activity, sleep, available heart-rate measurements, and food spending vary together?

The system should show the data, gaps, method, and uncertainty. It may find an association, contradict the proposed explanation, or report insufficient evidence. It must not assume causation or a clinical interpretation.

## Intended first users

Begin with the owner's self-operated workspace. The first external participants remain privacy-aware students, technical friends, and other personally recruited consenting adults who:

- are curious about what their data reveals;
- understand that this is an experimental prototype;
- knowingly authorize collection and, separately if chosen, researcher access;
- tolerate sideloading, data exports, and incomplete software; and
- participate as co-designers rather than passive tracking targets.

Both self-operated and researcher-assisted use are central. A participant can operate the local workbench without a separate researcher; sharing identifiable data is an optional, explicitly authorized mode. External-participant work follows testing of the trust controls. The small cohort does not require App Store distribution.

## Product pillars

### 1. Broad authorized observation

The long-term system supports many data sources rather than optimizing a single isolated metric. “All available data” means all data the participant explicitly authorizes and the platform can technically and legitimately access. It does not mean bypassing iOS permissions or obtaining nonparticipant data.

### 2. Dashboard backed by an ontology

Raw records become typed objects, events, relationships, and evidence. The dashboard must answer “what happened?”, “how is it connected?”, and “what can the evidence support?” Predictions and actions are supported extensions. Connected meaning matters more than a particular database or a visually elaborate graph.

### 3. Evidence before narrative

Statistics and ML establish measurable patterns. A language model may classify, suggest hypotheses, and explain results, but it is not itself proof that a correlation exists.

### 4. Utility-first inference

The project does not exclude an inference merely because the subject is uncomfortable or sensitive. It evaluates the benefit of understanding or an optional action, evidence strength, false-positive cost, and privacy/security risk. Actionability is relevant when proposing an action, not a prerequisite for useful exploration. Consequential conclusions require stronger evidence and appropriate review.

### 5. Participant agency

Participants can understand collection, correct conclusions, control researcher access, pause collection, export data, and delete it.

### 6. Learning from evidence and correction

New observations and participant corrections strengthen, weaken, or reject interpretations. Confirming a label is not the same as establishing a statistical relationship. Optional interventions add measured outcomes; an action is not required to complete every insight.

## Desired experience

The first demonstration should tell one coherent story:

1. Establish what the participant's iPhone and available exports can actually supply.
2. Connect authorized historical records and live observations across useful domains.
3. Explore the resulting temporal ontology through timelines and linked detail views.
4. Inspect coverage, missingness, data freshness, and source provenance.
5. Investigate a question with reproducible analysis and explicit uncertainty.
6. Correct an interpretation and see its downstream effects.
7. Inspect, export, and delete the workspace.

Profiles, ad/offer investigations, forecasts, notifications, and experiments are possible later demonstrations. A positive association is not guaranteed. Detailed scrolling and native-app consumption traces must remain labeled as inaccessible unless a source-specific path is demonstrated.

## Long-term possibility space

- Continuous encrypted synchronization
- Richer participant-facing ontology exploration beyond the first local explorer
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
- a visual clone of Palantir Foundry or Gotham.

The project takes inspiration from ontology-centered operational systems: objects, relationships, provenance, decisions, actions, and feedback. It will develop its own implementation and visual identity.

## Measures of success

V1 should measure more than whether the software runs:

- **Coverage:** authorized sources successfully normalized into the ontology.
- **Provenance:** conclusions trace back to original records.
- **Exploration:** participant can connect records across domains and inspect why an interpretation exists.
- **Inference quality:** reproducibility, effect size where applicable, uncertainty, stability, and false-positive control; honest null results count.
- **Usefulness:** participant understanding and ability to question or correct the evidence, whether or not an action follows.
- **Forecast quality, when forecasting is selected:** prospectively locked predictions compared against actual events and simple baselines.
- **Correctability:** participant corrections alter the graph and future output.
- **Trust:** participant can inspect collection and successfully pause, export, and delete it.
