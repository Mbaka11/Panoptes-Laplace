# Laplace inference engine

## Mission

Laplace converts a participant's ontology into testable knowledge. It discovers patterns, creates forecasts, explains evidence, proposes actions, and learns from outcomes.

It must not confuse an articulate explanation with a valid result.

## Inference pipeline

```text
Canonical events
    ↓
Feature construction
    ↓
Pattern and anomaly discovery
    ↓
Hypothesis generation
    ↓
Statistical/predictive validation
    ↓
Researcher review
    ↓
Participant-facing insight or forecast
    ↓
Feedback and observed outcome
    ↓
Inference update
```

## Analytical methods

The exact methods will be selected after inspecting real authorized data. Candidate families include:

### Place and routine discovery

- spatial clustering for repeated locations;
- route and mobility segmentation;
- day-of-week and time-window clustering;
- frequent sequence discovery; and
- transitions or Markov-style next-state baselines.

### Cross-domain associations

- personal baseline comparisons;
- rank and linear correlations where assumptions permit;
- lagged correlations;
- mutual information;
- stratified comparisons;
- anomaly and change-point detection; and
- correction for repeated hypothesis testing where relevant.

### Forecasting

- simple historical baselines first;
- day-of-week recurrence;
- probabilistic next-place or next-activity forecasts;
- time-window forecasts rather than false precision;
- confidence calibration; and
- comparisons against naive baselines.

### Clustering and categorization

- unsupervised grouping of places, days, activities, and behavior sequences;
- semantic labeling only after clusters exist;
- participant confirmation of generated categories; and
- preservation of model/version provenance.

## Language-model role

A local or external language model may later:

- categorize unstructured records;
- suggest hypotheses worth testing;
- label discovered clusters and routines;
- connect semantically related records;
- summarize evidence in understandable language; and
- propose participant experiments.

A language model must not be treated as the statistical authority. Its output begins as a hypothesis or narrative and remains linked to the exact prompt, provider/model, version, and input scope.

The choice between a local model and an external provider is deferred. The architecture should expose a provider-neutral interface.

## Inference lifecycle

Suggested statuses:

1. **Hypothesis** — proposed but untested.
2. **Candidate** — measurable support exists.
3. **Reviewed** — researcher inspected evidence and alternatives.
4. **Published** — participant can see and act on it.
5. **Confirmed** — repeated evidence or participant outcome strengthened it.
6. **Weakened** — later observations reduced confidence.
7. **Corrected** — participant supplied a better interpretation.
8. **Rejected** — unsupported, misleading, or not useful.
9. **Expired** — no longer current for the participant.

## Expected utility

The project uses a utility-first approach. A conceptual score is:

```text
expected utility =
    potential benefit
    × confidence
    × actionability
    − false-positive cost
    − privacy/security risk
```

The first implementation does not need to pretend these values are objectively precise. The purpose is to force explicit consideration of both benefit and cost before publishing a conclusion.

Broad and sensitive hypotheses may be researched with participant authorization. Higher-impact conclusions require stronger evidence, explicit uncertainty, and researcher review because false conclusions reduce utility.

## Correlation and causation

Observational personal data can reveal association and predictive value but usually cannot establish causation.

Participant-approved N-of-1 experiments can improve evidence:

1. Identify a repeatable association.
2. Define a measurable baseline.
3. Change one behavior where practical.
4. Observe a predetermined outcome window.
5. Repeat or alternate conditions.
6. Update confidence without overstating generality.

## Monday forecast benchmark

The first benchmark predicts a participant's Monday before it occurs.

Potential target events:

- departure time window;
- probable destination;
- arrival time window;
- mobility mode;
- recurring activity; and
- next-place sequence.

Evaluation requirements:

- lock or hash the prediction before Monday;
- retain predicted probabilities/time windows;
- define scoring before viewing actual outcomes;
- compare against simple baselines;
- score partial correctness consistently;
- expose misses, not only successful predictions; and
- distinguish calendar-derived knowledge from behavior-derived inference.

A future comparison can evaluate models based on:

- location only;
- location plus motion/activity;
- all authorized sources.

This reveals the marginal predictive value of each data category.

## Insight and notification contract

A participant-facing insight should contain:

1. **Observation:** what the system measured.
2. **Inference:** what pattern or conclusion is proposed.
3. **Evidence:** source records or an inspectable summary.
4. **Confidence:** probability, interval, or qualitative uncertainty with definition.
5. **Alternative explanations:** important competing interpretations.
6. **Privacy view:** what an outside observer could learn.
7. **Utility view:** why the participant may care.
8. **Action:** an optional participant-controlled next step.
9. **Feedback:** confirm, reject, correct, or mark not useful.

Notifications should be generated from reviewed insight objects, not directly from unvalidated model text.

## Research workbench capabilities

- Select time windows and source categories
- Visualize missingness and data quality
- Compare features with temporal lags
- Save versioned hypothesis definitions
- Run the same definition in isolated participant workspaces
- Inspect supporting and contradicting examples
- Review effect size and uncertainty
- Publish or reject candidate inferences
- Measure notification and experiment outcomes

## Open inference decisions

- Initial feature schema
- Spatial clustering method
- Monday forecast scoring function
- Minimum data volume for publication
- Confidence calibration approach
- Multiple-testing controls
- Definition language for reusable inferences
- Local versus external language model
- Local model hardware and latency targets
- How participant corrections retrain or override models
