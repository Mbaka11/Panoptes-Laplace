# Laplace inference engine

## Mission

Laplace turns a participant's connected data into inspectable analytical findings: descriptions, patterns, comparisons, and testable hypotheses. Forecasts and proposed actions are optional extensions. Understanding, contradictory evidence, and insufficient-data findings are valid outputs.

It must not confuse an articulate explanation with a valid result. Both self-operators and authorized researchers use the analysis capabilities within their access scopes.

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
Evidence review appropriate to consequence and operator role
    ↓
Inspectable finding, including null or inconclusive results
    ↓
Corrections, later observations, or optional action outcomes
    ↓
Inference update
```

Exploratory output may be inspected before validation if its status and limitations are explicit. Not every observation needs to advance through the entire pipeline or become a published inference.

## Data sufficiency and evaluation

- State the question, observation unit, input window, source coverage, and exclusions.
- Preserve interval/aggregate semantics and handle overlapping exports before constructing features.
- Distinguish sensor accuracy, model probability, statistical uncertainty, and participant confirmation. Do not substitute one for another.
- Account for missingness, temporal dependence, and repeated hypothesis testing. Thousands of sensor records are not thousands of independent days.
- Separate exploratory discovery from subsequent validation; do not select only flattering windows or successful findings.
- Compare predictive methods with simple baselines and define evaluation before observing the outcome.
- A short collection trial tests reliability and coverage. The duration needed for a defensible finding depends on the question and data, not a fixed 14-day promise.

## Analytical methods

The exact methods will be selected after inspecting real authorized data. Begin with descriptive exploration and simple baselines; classification or clustering is useful when it answers a defined question, not because every finding must use ML. Candidate families include:

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
3. **Reviewed** — the recorded operator/reviewer inspected evidence and alternatives with review appropriate to the claim's consequence.
4. **Published** — participant can inspect the finding; an action is optional.
5. **Confirmed** — later evidence strengthened it under stated criteria, not merely because someone agreed with its wording.
6. **Weakened** — later observations reduced confidence.
7. **Corrected** — participant supplied a better interpretation.
8. **Rejected** — unsupported, misleading, or not useful.
9. **Expired** — no longer current for the participant.

## Expected utility

The project uses a utility-first approach in which understanding is itself a benefit (D-023). Review the value of the explanation or optional action alongside evidence strength, false-positive cost, and privacy/security risk.

Do not multiply every finding's value by actionability: that would discard useful understanding simply because no intervention follows. These considerations are qualitative review criteria, not a calibrated numerical score.

Broad and sensitive hypotheses may be investigated with participant authorization. Higher-impact conclusions require stronger evidence, explicit uncertainty, and appropriate human review. Self-exploration is not an exemption from those requirements.

## Correlation and causation

Observational personal data can reveal association and predictive value but usually cannot establish causation.

Participant-approved N-of-1 experiments can improve evidence:

1. Identify a repeatable association.
2. Define a measurable baseline.
3. Change one behavior where practical.
4. Observe a predetermined outcome window.
5. Repeat or alternate conditions.
6. Update confidence without overstating generality.

## Optional Monday forecast benchmark

A later benchmark may predict a participant's Monday before it occurs. This remains an example, not the first explorer's success criterion (D-025).

Potential target events:

- departure time window;
- probable destination;
- arrival time window;
- mobility mode;
- recurring activity; and
- next-place sequence.

Evaluation requirements:

- retain a verifiable pre-outcome commitment to the prediction; a content hash alone does not prove when it existed;
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
6. **Privacy view:** what an observer with the specified source access could learn, not an unsupported claim about a company's actual internal model.
7. **Utility view:** what the participant can understand, with an action only if useful.
8. **Action:** an optional participant-controlled next step.
9. **Feedback:** confirm, reject, correct, or mark not useful.

For descriptive or inconclusive findings, state that status rather than forcing an inference into every report. Notifications are optional and should be generated from reviewed insight objects, not directly from unvalidated model text.

## Operator workbench capabilities

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
- Scoring and commitment method for any later forecast benchmark
- Minimum data volume for publication
- Confidence calibration approach
- Multiple-testing controls
- Definition language for reusable inferences
- Local versus external language model
- Local model hardware and latency targets
- How participant corrections retrain or override models
