# Investigation catalogue

## Status and purpose

**Status:** PROVISIONAL planning catalogue. Nothing here has been run on real data, and no source below is yet verified on the physical phone. Thresholds are starting heuristics to be revised after the collection feasibility lab ([collection-probe.md](collection-probe.md)) reports actual coverage; they are not statistical guarantees.

This catalogue supports Step 4 of [review-and-next-steps.md](review-and-next-steps.md#step-4--add-one-reproducible-analytical-investigation) and the V1 acceptance target in [mvp.md](mvp.md): choose a question the actual data supports, run it reproducibly, and report evidence and uncertainty. A null or insufficient-evidence result is a valid completed investigation (D-025). It does not select a schema, framework, or statistical library, and it does not reopen any accepted decision.

Governing rules (D-012, D-017, D-023 to D-025, [inference-engine.md](inference-engine.md)):

- Statistical and ML methods establish evidence. A language model may phrase a hypothesis, label a cluster, or summarize a result; its prose is never evidence and its prompt/model/version/input scope is recorded.
- Associations are associations. No causal, clinical, financial, or legal conclusion is drawn from any investigation here.
- Only the participant's own records are analysed. People who appear incidentally (calendar attendees, contacts, co-located people, content creators) are not inferred about.
- Forecasts are optional later benchmarks with a baseline, predeclared scoring, and a verifiable pre-outcome lock (a bare hash does not prove time).
- Coverage gaps are not behavior. Missing data is `unknown`, not zero or "stationary" or "inactive".

## Conventions used in every entry

**Observation versus sample unit.** Sensor and event records are observations, not independent samples. Every investigation names a sample unit (usually a person-day, a visit, a trip, or a week) and reports its count `n`. Thousands of location fixes in 20 days remain at most about 20 person-days. Within-unit records are collapsed to a unit-level feature before inference.

**Method ladder.** Each investigation proceeds in order and may stop early:

1. Coverage and quality description (what exists, what is missing).
2. Descriptive summary (counts, distributions, timelines).
3. Simple baseline (e.g. day-of-week mean, "same as last week", shuffled labels).
4. Optional model (clustering, classification, change-point detection) only if the question requires it and the previous rung is insufficient.

**Uncertainty display.** Prefer intervals over p-values: bootstrap by whole days (or blocked bootstrap) rather than by record; show the raw per-unit values beside any summary; show sample size and exclusions; show a permutation or shuffled-day reference where a comparison is made. Keep four things separate and labeled: sensor accuracy, statistical uncertainty, model probability, and participant confirmation.

**Privacy-revelation angle.** Each entry has a short paragraph "Observer with only this source" describing what such an observer could plausibly infer, at what stated confidence, and how far this is from the claim that any real company did so. The paragraph never asserts what an actual company's model contains (see [product-vision.md](product-vision.md)). It is the privacy view of the insight contract, not a finding about a vendor.

**Participant role.** Every output is inspectable; the participant may confirm, reject, or correct a label (e.g. "this cluster is not my workplace"). Correction is recorded as a new version, not an overwrite.

**Minimum coverage notation.** "Days" means calendar days with usable data for the stated sources, not days since collection started. "Completeness" is a fraction of the expected observation windows that are present, measured against the source's own coverage report where available.

## Index

| ID | Title | Sources | First-pilot candidate |
|---|---|---|---|
| INV-01 | Where do I spend time? | Location | Yes |
| INV-02 | How regular are my days? | Location | No |
| INV-03 | Do motion and location agree? | Location + Motion | No |
| INV-04 | Is trip timing consistent? | Location + Motion | No |
| INV-05 | Steps by day type | Health steps + Calendar | Fallback |
| INV-06 | Steps and where I was | Health steps + Location | No |
| INV-07 | Which apps touch which resources? | App Privacy Report | Yes |
| INV-08 | Which domains recur across apps? | App Privacy Report | Yes (with INV-07) |
| INV-09 | How stable are seven-day reports? | App Privacy Report | No |
| INV-10 | Resource access and place | APR + Location | No |
| INV-11 | When am I active in a service? | Account export + time | Yes |
| INV-12 | Has the mix of content changed? | Account export + time | No |
| INV-13 | Calendar load and digital activity | Calendar + Account export | No |
| INV-14 | One shared timeline, one week | Cross-domain (any 3) | No (demonstration) |
| INV-15 | Broad association scan | Cross-domain | No (exploratory only) |
| INV-16 | Optional forecast benchmark | Location (+ Motion, Calendar) | No (later) |

An additional note applies to a "source-comparison" view: INV-14 and INV-16 both compare the marginal information each source adds.

---

## Group A: Location only

### INV-01 Where do I spend time?

- **Question.** Which places do I repeatedly visit, how long do I stay, and which hours and weekdays do those visits occupy?
- **Sources and minimum coverage.** Core Location. At least 14 days with usable data and at least about 60% of waking hours covered on most of those days. Below that, report coverage only; do not claim a place list.
- **Sample unit.** A visit (a stay at one place with start and end) is the unit for dwell statistics; a person-day is the unit for any day-level claim. Raw fixes are never the unit. Collapse fixes into stays first (dwell threshold and radius are parameters recorded with the run).
- **Method ladder.** (1) Coverage map by hour and day. (2) Stay-point extraction and a visit table. (3) Baseline: place identified by a naive "most common night location" rule, compared with density-based clustering of stays. (4) Optional: spatial clustering (e.g. density-based), with a stability check across parameter values and across halves of the period.
- **Outputs and uncertainty.** Place list with visit counts, median dwell, and an interval over visits by day-bootstrap; a stability score (do the same places appear under reasonable parameter changes and in each half-period?); a map-free table is acceptable. Cluster boundaries are shown as uncertain, not exact.
- **Supporting evidence.** Repeated visits across several distinct days; stable clusters across parameter sweeps. **Contradicting evidence.** Clusters that vanish with small parameter changes; a place defined by one day; visits concentrated in coverage-heavy periods only.
- **Alternative explanations and confounders.** GPS drift indoors creating phantom stays; sparse background sampling merging distinct places; different sampling policy at different times (charging, low power); the phone left at home while the person is elsewhere.
- **Null / insufficient result.** "Coverage was too sparse or irregular to separate places; no place list is offered" or "no place exceeded the visit threshold across at least three days." Both are valid.
- **Observer with only this source.** An observer with location history could plausibly infer a likely home area (night-time dwell), a likely repeated daytime location, and routine hours. These are candidate inferences with stated confidence; the semantic label ("home", "work") is a hypothesis the participant confirms or rejects. This does not show that any specific company computed them.
- **How it could mislead.** Labeling clusters with confident names (an LLM may suggest a label, which is a hypothesis only); equating dwell with activity; mistaking missing data for time away; reporting precise addresses that the sensor accuracy does not support.

### INV-02 How regular are my days?

- **Question.** Do weekdays and weekends differ in when I leave and return, and how variable is it?
- **Sources and minimum coverage.** Core Location. At least 3 weeks with at least 8 usable weekdays and 4 usable weekend days; day-completeness above a stated threshold (for example, a first-and-last departure that can be seen).
- **Sample unit.** Person-day, with day type (weekday/weekend/holiday as marked by the participant). `n` is the number of usable days per type.
- **Method ladder.** (1) Daily timeline of "away/at-anchor" derived from INV-01. (2) Per-day first departure, last return, and away duration; distribution by day type. (3) Baseline: "every day is the same as the pooled mean"; compare with the day-type mean using a leave-one-day-out error. (4) Optional: clustering of day profiles (hourly away indicator), reporting whether clusters differ from random assignment.
- **Outputs and uncertainty.** Distributions with medians and day-bootstrap intervals; a table of each day's value; effect size for weekday versus weekend with an interval; explicit `n` per group.
- **Supporting / contradicting.** Consistent departure windows with narrow spread support regularity; many days with no clear departure, or large unexplained spread, contradict it. Show the outlier days rather than trimming them silently.
- **Alternatives and confounders.** Holidays, illness, travel, and schedule changes; the participant's own calendar; a changed collection setting midway through the period; days where the phone stayed home.
- **Null / insufficient.** "The weekday/weekend difference interval includes zero" or "fewer than the minimum usable days in one group."
- **Observer with only this source.** Could infer a rough daily rhythm and when the person is typically away. It does not tell what they did, and routine is not intent.
- **How it could mislead.** Equating regularity with predictability; selecting a flattering window; ignoring autocorrelation across adjacent days; forgetting that a few weeks is not a stable personal norm.

---

## Group B: Location plus Motion

### INV-03 Do motion and location agree?

- **Question.** When location indicates travel, does the motion/activity source indicate walking, driving, or stationary, and how often do they disagree?
- **Sources and minimum coverage.** Core Location and Core Motion activity records for the same windows. At least 10 days and at least 20 distinct movement segments with both sources present. The motion source's actual history depth and sampling are probe outputs; if motion history is absent, this investigation is not run.
- **Sample unit.** A movement segment (a continuous stretch between two stays), not a fix and not a motion record. Motion records overlapping a segment are summarised per segment (share of time per activity label, with the source's confidence class retained).
- **Method ladder.** (1) Overlap and missingness between the two sources. (2) Confusion-style cross-tabulation of location-derived speed bands against motion labels, per segment. (3) Baseline: speed-threshold rule alone. (4) Optional: a simple classifier only if the rule baseline is clearly insufficient and enough labeled segments exist; otherwise stop.
- **Outputs and uncertainty.** Agreement rate with interval (bootstrap by segment), a table of disagreeing segments, and the motion source's own confidence categories shown separately from the statistical interval.
- **Supporting / contradicting.** Agreement across varied segment types supports consistency; disagreement concentrated in particular conditions (phone in a bag, slow traffic) is itself a finding about sensor reliability, not about behavior.
- **Alternatives and confounders.** The motion label is a model output with its own errors; phone placement; different timestamps and sampling between sources; interval versus point semantics (preserve them, do not align by rounding).
- **Null / insufficient.** "Too few segments with both sources to estimate agreement" or "no usable motion history."
- **Observer with only this source (both).** Could infer travel mode patterns (walks versus vehicle trips). This is a sensor-reliability study first; mode claims are uncertain.
- **How it could mislead.** Treating a model-derived activity label as ground truth; averaging over unlike segments; counting each motion record as an independent agreement test.

### INV-04 Is trip timing consistent?

- **Question.** For a recurring trip (between two INV-01 places), how consistent are departure time, duration, and mode?
- **Sources and minimum coverage.** Location, Motion optional for mode. At least 8 trips of the same origin-destination pair over at least 3 weeks.
- **Sample unit.** A trip; `n` is the number of trips for the pair. Trips on the same day are not independent of each other and are flagged.
- **Method ladder.** (1) List trips and durations. (2) Distribution by weekday and time window. (3) Baseline: "median of earlier trips" as a predictor of the next trip's duration; compare mean absolute error to a seasonal baseline. (4) Optional: nothing more complex than a day-of-week effect unless data clearly warrants it.
- **Outputs and uncertainty.** Duration distribution with interval; predicted-versus-actual only in a retrospective, clearly labeled exploratory form. This is not a forecast benchmark (see INV-16).
- **Supporting / contradicting.** Narrow, stable durations support consistency; large day-to-day spread, or a visible change after a particular date (change-point), qualifies it.
- **Alternatives and confounders.** Traffic, weather, schedule, partial trips split by sampling gaps, trips merged by a short stop.
- **Null / insufficient.** "Fewer than the minimum number of comparable trips" or "variation too large to distinguish a pattern."
- **Observer with only this source.** Could infer recurring commuting times and the route's origin and destination types. Specific purposes remain hypotheses.
- **How it could mislead.** Trip segmentation errors dominating the result; overinterpreting a small number of trips; ignoring that trips are clustered in weeks.

---

## Group C: Health steps plus Calendar (and Location)

### INV-05 Steps by day type

- **Question.** Does my step count differ between days that have different kinds of calendar entries (for example no entries, a few, many; or entries marked by the participant as "away")?
- **Sources and minimum coverage.** HealthKit steps (phone-produced), EventKit. At least 21 days with step data from a single stated producer, and calendar data in the same window. Planned events are scheduled context only (SYN-08); they are not evidence the activity happened.
- **Sample unit.** Person-day. Hourly step intervals are aggregated to a day total after de-duplicating overlapping producers (do not sum overlapping sources). Interval and aggregate records stay distinct from individual events.
- **Method ladder.** (1) Step coverage and producer inventory; empty days are `unknown`, not zero. (2) Distribution of daily steps by calendar-defined day type, pre-registered categories only. (3) Baseline: day-of-week mean. A calendar effect must beat the day-of-week baseline to be worth reporting. (4) Optional: none; a regression with one or two terms at most.
- **Outputs and uncertainty.** Difference with interval (bootstrap by day, or a blocked bootstrap by week), both day-of-week-adjusted and unadjusted views, raw dots for all days. State `n` per group.
- **Supporting / contradicting.** A consistent direction after adjusting for day of week supports an association; a difference that disappears after adjustment, or reverses across weeks, contradicts it.
- **Alternatives and confounders.** Weekday/weekend, weather, phone not carried (steps undercounted), wear time unknown, a one-off event, changes in producer or settings, calendar entries that did not happen.
- **Null / insufficient.** "Group sizes are too small or the interval includes zero after day-of-week adjustment."
- **Observer with only this source (Health plus Calendar).** Could infer busy and quiet days and activity level by day type. Statements about health or fitness are not made; step counts are not a clinical measure.
- **How it could mislead.** Reading a step change as a health claim; double counting across producers; treating calendar load as behavior; testing many day-type definitions until one looks significant.

### INV-06 Steps and where I was

- **Question.** On days I spent time at a given place (from INV-01) or away for a long period, were my steps different?
- **Sources and minimum coverage.** HealthKit steps and Location. At least 21 days with both, and at least 5 days in each compared place category.
- **Sample unit.** Person-day with a place-based day label derived from INV-01, which inherits its uncertainty. Labels are recorded with their derivation version.
- **Method ladder.** As INV-05, with the place-derived day type in place of the calendar type; compare against the day-of-week baseline.
- **Outputs and uncertainty.** As INV-05, plus the propagated uncertainty of the place label (sensitivity analysis excluding low-confidence days).
- **Supporting / contradicting.** As INV-05; agreement between this and INV-05 on shared days is a consistency check, not independent confirmation, because the same step data is reused.
- **Alternatives and confounders.** Same as INV-05, plus circularity: place assignment and steps can both depend on the phone being carried.
- **Null / insufficient.** As INV-05.
- **Observer with only this source pair.** Could link activity level to places. Sensitive places (for example medical) can be inferred only as hypotheses; this investigation does not infer or report health conditions or reasons for visits.
- **How it could mislead.** Circular definitions, especially if the phone's carrying behavior drives both measures.

---

## Group D: App Privacy Report alone

The report is a participant-initiated export. The documented window is seven days after recording is enabled, and a rolling export overlaps with prior exports ([review-and-next-steps.md §4.1](review-and-next-steps.md#41-a-useful-omitted-source-app-privacy-report)). Overlaps are never summed (SYN-03). Browser private-browsing network activity is not recorded, so absence is not proof of no activity. These are metadata, not content.

### INV-07 Which apps touch which resources?

- **Question.** Which apps accessed which sensitive resources (location, camera, microphone, and so on), how often, in what time windows, and for how long where intervals are matched?
- **Sources and minimum coverage.** A real exported App Privacy Report with a documented window. At least one full seven-day window; ideally 3 to 4 non-overlapping windows collected weekly over the 2 to 4 week pilot. Enabled-since date is recorded; nothing is assumed before it.
- **Sample unit.** An access interval (matched begin/end) is the unit for durations; unmatched endpoints remain incomplete and carry no invented duration. Counts are per app-resource-day. The overall unit for day-level claims is an app-resource-day.
- **Method ladder.** (1) Window and validation coverage (malformed lines, unknown record types, unmatched endpoints). (2) Per-app, per-resource tables and a time-of-day profile. (3) Baseline: the same counts under a naive "uniform over the window" assumption, to show whether any concentration is notable. (4) Optional: none needed.
- **Outputs and uncertainty.** Tables with counts and interval durations, unmatched endpoints flagged, and window coverage. Uncertainty is mainly about completeness, shown as coverage, not as a confidence interval.
- **Supporting / contradicting.** Repeated access at consistent times supports a regular pattern; accesses at times the participant did not use the app (or after recording started) are a flagged anomaly for the participant to review, not an assertion of misconduct.
- **Alternatives and confounders.** Background refresh, system services, widgets, notification handling, features triggered by the participant's own settings, short window.
- **Null / insufficient.** "The window is too short or the report is incomplete for a pattern claim" or "no access records of the chosen resource in the window."
- **Observer with only this source.** Could learn which apps the person has installed and used, which resources those apps touch, and the daily rhythm of use. It does not tell what data was transmitted or how it was used.
- **How it could mislead.** Equating access with data exfiltration; summing overlapping exports; reading unmatched endpoints as long durations; naming an app as intrusive from access counts alone.

### INV-08 Which domains recur across apps?

- **Question.** Which network domains are contacted by several of my apps, and how concentrated is contact in a few domains?
- **Sources and minimum coverage.** App Privacy Report network records, at least one seven-day window, ideally 3 to 4 weekly windows. Domain records are aggregates with hit counts and first/most-recent timestamps.
- **Sample unit.** An app-domain pair per window. Hit counts are aggregate, not events; no page views or request times are synthesised.
- **Method ladder.** (1) Coverage and validation. (2) Domains-per-app and apps-per-domain tables; concentration measure (for example share of hits to the top domains). (3) Baseline: compare with a random reassignment of domains to apps preserving per-app totals, to see whether apparent overlap exceeds chance structure. (4) Optional: an external, versioned domain-category list as a labeling aid; categories are labels by a third party and are not verified facts about purpose.
- **Outputs and uncertainty.** Tables, a concentration summary with window-level bootstrap if enough windows exist, and a clear separate field for "category label source and version."
- **Supporting / contradicting.** The same domain reached by several apps supports a shared-infrastructure observation; domains that appear once in a single window may be noise, and absence is not evidence of non-contact.
- **Alternatives and confounders.** CDNs and cloud providers are shared by unrelated apps; one domain can serve many purposes; category lists are incomplete; rolling-window overlap.
- **Null / insufficient.** "No domain recurs across at least two apps beyond what the reassignment baseline produces."
- **Observer with only this source.** Could infer which services the person likely uses and how heavy usage is. It could not infer content, and a shared domain is not shared ownership or data-sharing between companies.
- **How it could mislead.** Reading "same domain" as "same company" or "data was shared"; reading hit counts as activity volume; summing overlapping windows; trusting a category label as a fact.

### INV-09 How stable are seven-day reports?

- **Question.** Between consecutive rolling exports, which records overlap, which differ, and what does a decrease in a total mean?
- **Sources and minimum coverage.** At least 3 exports from the same device, ideally collected on a regular schedule, with known generation times.
- **Sample unit.** A snapshot (one export); comparisons are between snapshot pairs.
- **Method ladder.** (1) Reconciliation view per D-034: per-snapshot totals with provenance, latest observed total, decreases flagged as possible window rollover. (2) Descriptive comparison of overlapping windows. (3) No model.
- **Outputs and uncertainty.** A reconciliation table; explicit "cannot determine" where semantics are unknown. No sums, no deltas, no invented events.
- **Supporting / contradicting.** Consistent overlap behavior supports the assumed window semantics; unexplained decreases contradict a simple additive reading.
- **Alternatives and confounders.** Recording toggled off and on, device restart, OS updates, retention rules the source does not document.
- **Null / insufficient.** "Window semantics could not be established from the exports available."
- **Observer with only this source.** Not a privacy-revelation question; this is a data-quality investigation that determines whether INV-07, INV-08, and INV-10 can be trusted.
- **How it could mislead.** Over-interpreting a total drop as behavior change when it may be rollover.

---

## Group E: App Privacy Report plus Location

### INV-10 Resource access and place

- **Question.** Do resource accesses (especially location) cluster at particular places or movement periods, and do domain-contact first/last timestamps align with my time at particular places?
- **Sources and minimum coverage.** App Privacy Report (at least two windows) and Location in the same period, with at least 10 days of overlapping usable data. Domain records are aggregate: only their first and most-recent timestamps place them in time, so they can be tested only for consistency with a place, never assigned to a place event.
- **Sample unit.** An access interval joined to the participant's location state at that time (at place, moving, unknown). Unknown location state is retained as a category, not dropped silently. For aggregates, the unit is the app-domain-window.
- **Method ladder.** (1) Join coverage (how many accesses have a known location state). (2) Cross-tabulation of access counts by place state, with the base rate of time spent in each state as the reference. (3) Baseline: expected accesses proportional to time in each state. (4) No model.
- **Outputs and uncertainty.** Observed/expected ratios with day-bootstrap intervals; the join-coverage rate prominently; list of accesses with unknown location state.
- **Supporting / contradicting.** A ratio above one for a state across several days and apps supports clustering; a ratio near one, or one driven by a single app-day, does not.
- **Alternatives and confounders.** The participant is simply at that place more; timestamp offsets between sources and time zones; apps accessing location because the participant opened them.
- **Null / insufficient.** "Join coverage too low" or "observed/expected ratios are consistent with time-share."
- **Observer with only these sources.** Could connect which apps use location and at which kinds of places or movement. It would not show where data went or what was inferred from it.
- **How it could mislead.** Treating co-occurrence as app behavior; time-zone misalignment; presenting an aggregate domain contact as if it were a located event.

---

## Group F: Account export plus time

An account export's value depends on which fields exist (ACC-01). Consumption, interaction, duration, and timestamp fields are checked individually before an investigation is chosen. Dwell time and scroll depth are never inferred from gaps between unrelated records (D-030). Exports are overlapping snapshots; repeated imports are deduplicated and are not double-counted.

### INV-11 When am I active in a service?

- **Question.** At what hours and weekdays does the service record my activity (searches, views, interactions), and has that rhythm changed over the months in the export?
- **Sources and minimum coverage.** One participant-owned account export with timestamps. Historical depth is an advantage: at least 8 weeks if the export provides it. Fields that exist are listed in the coverage audit first. If only a few weeks are present, the investigation reduces to description.
- **Sample unit.** A day (activity count per day) for temporal claims and a day-by-hour cell for rhythm profiles. Individual records are never treated as independent samples; counts are per day.
- **Method ladder.** (1) Field and gap audit (ACC-01). (2) Hour-of-day by weekday heat table and weekly series. (3) Baseline: weekly mean and a day-of-week profile; a change is reported only if it exceeds the variation seen in the baseline. (4) Optional: simple change-point detection with a stated sensitivity analysis.
- **Outputs and uncertainty.** Profiles with bootstrap intervals by week; a change-point, if any, shown with its candidate range (not one exact date) and the alternative of no change.
- **Supporting / contradicting.** A repeated daily profile across many weeks supports a rhythm; a shift coinciding with an export-format change or a coverage gap is flagged, not reported as behavior.
- **Alternatives and confounders.** Logging policy changes at the service, deleted history, time-zone shifts, account-sharing, travel, devices not logged in, activity outside the service.
- **Null / insufficient.** "The export covers too short a period or lacks timestamps for the activity type."
- **Observer with only this source.** The service operator, or anyone with such an export, could infer sleep-wake rhythm, work hours, and routine changes at a stated confidence. That is a statement about what a holder of the export could infer; it is not a claim that any provider did.
- **How it could mislead.** Equating records with usage time; reading activity as presence (the record is the service's log, not the person's whole day); reading a gap as inactivity.

### INV-12 Has the mix of content changed?

- **Question.** Has the composition of what I searched or viewed in the service changed across months, according to the service's own fields?
- **Sources and minimum coverage.** An account export with viewed or searched content text or categories and timestamps; at least 8 weeks. If only titles exist, categories require an explicit labeling step.
- **Sample unit.** A week (category shares per week). Records within a week are not independent. A category must have at least a stated number of weekly records for its share to be reported.
- **Method ladder.** (1) Coverage audit. (2) Descriptive category shares by week using the service's own categories if present. (3) Baseline: shuffled-week reference, to show how much week-to-week change arises by chance. (4) Optional: topic clustering of titles. A language model may propose cluster labels as a hypothesis; the labels are recorded with prompt/model/version/input scope, are shown as suggestions for participant correction, and are not evidence. No external service receives data by default.
- **Outputs and uncertainty.** Weekly share series with bootstrap or Dirichlet-style intervals, the shuffled reference band, and the participant-confirmed label status per category.
- **Supporting / contradicting.** A sustained shift beyond the shuffled band supports a change; a shift limited to one week, or tied to a single event, does not.
- **Alternatives and confounders.** Recommendation algorithms shape what is viewed (the content is partly the service's choice, not purely the person's interest); sampling by the export; shared accounts; mislabelled clusters.
- **Null / insufficient.** "Changes are within the shuffled reference band" or "too few records per week."
- **Observer with only this source.** A holder could infer topics of interest and changes in them. Topic inference of a sensitive nature is not drawn automatically; the participant chooses which topics are explored (D-017). No claims about beliefs, health, or intent.
- **How it could mislead.** Treating viewed content as chosen interest; trusting LLM labels; reporting a topic inference about a third party in the content.

---

## Group G: Cross-domain

### INV-13 Calendar load and digital activity

- **Question.** On days with more scheduled calendar time, is the account-export activity (INV-11) lower, higher, or shifted in time?
- **Sources and minimum coverage.** EventKit and one account export, overlapping for at least 28 days. Planned events are scheduled context only; the participant may mark entries as "did not happen".
- **Sample unit.** Person-day. Calendar load is a pre-declared daily feature (scheduled hours). Adjacent days are serially dependent; analysis uses a blocked bootstrap and reports the autocorrelation.
- **Method ladder.** (1) Coverage of both sources. (2) Scatter with raw days and rank correlation. (3) Baseline: day-of-week-adjusted comparison, plus a lag-0 versus lag-1 (previous-day) view declared before looking. (4) No model.
- **Outputs and uncertainty.** Effect with a blocked-bootstrap interval, the shuffled-day (or circular shift) reference, and `n` days. Only the pre-declared lags are tested.
- **Supporting / contradicting.** Same direction in both halves of the period, after adjusting for day-of-week, supports an association; a sign flip between halves contradicts it.
- **Alternatives and confounders.** Weekends, holidays, calendar entries that were cancelled, and the participant's changing habits in the period. Attendee identities are excluded from the analysis; nobody else is inferred about.
- **Null / insufficient.** "The interval includes zero after adjustment" or "fewer than 28 usable overlapping days."
- **Observer with only these sources.** A holder could infer a person's busy periods and how they spend free time online. It does not reveal what the meetings were.
- **How it could mislead.** Interpreting an association as "meetings reduce my activity"; ignoring day-of-week; using many lags and reporting the best one.

### INV-14 One shared timeline, one week

- **Question.** For a single chosen week, what does the combined record of the available sources (location stays, steps, calendar entries, app access intervals, account activity) show, and where do the sources agree, disagree, or have gaps?
- **Sources and minimum coverage.** Any three categories from at least two domains (the V1 target), one week of overlapping data.
- **Sample unit.** Not an inferential sample. This is a descriptive case study of one week; it makes no population or stability claim and states `n = 1 week`.
- **Method ladder.** Only rungs 1 and 2: coverage, then a connected timeline with provenance, source granularity, and per-source gaps. No model. A narrative summary may be drafted by a language model only as a labeled explanation of the displayed records, with the source records linked.
- **Outputs and uncertainty.** An annotated timeline; each statement linked to its source records; disagreements listed (for example, calendar says meeting, location says elsewhere). A correction path for the participant.
- **Supporting / contradicting.** Records that independently point to the same episode (a visit, a meeting, an app session) are consistent; conflicts are shown, not resolved silently.
- **Alternatives and confounders.** Clock and time-zone differences between sources; interval versus point records aligned by eye.
- **Null / insufficient.** "The week has too few overlapping sources to show a connected episode."
- **Observer with only these sources.** Illustrates the value of combining sources: how much more a combined observer could say than one with a single source. This is a demonstration of coverage, not a quantitative inference.
- **How it could mislead.** A smooth story hides gaps; the fluent narrative may be mistaken for evidence; one week is one week.

### INV-15 Broad association scan (exploratory only)

- **Question.** Among all pre-defined daily features from all available sources, which pairs show a notable association, as a source of hypotheses to test later?
- **Sources and minimum coverage.** At least three sources, 28 or more usable days, and a feature list fixed in advance. If fewer than about 28 usable days exist, do not run; the pair count would exceed what the data can support.
- **Sample unit.** Person-day. The effective number of independent days is smaller than the day count because of serial dependence; report an estimate of effective sample size.
- **Method ladder.** (1) Declare the full feature list and lags before looking, and log every pair tested. (2) Rank correlations or mutual information for each pair, with day-of-week removed. (3) Baseline: the same scan on circularly shifted or block-permuted series to estimate how many "associations" arise by chance. (4) Control for multiple comparisons (false discovery rate or similar) across all tested pairs and lags. Only pairs that survive and agree in both halves of the period are listed as candidates.
- **Outputs and uncertainty.** The total number of tests, the count that would be expected by chance (from the shifted baseline), a ranked candidate list marked "hypothesis, not finding," and effect sizes with intervals. The status is always exploratory; a candidate needs a new period of data to be validated.
- **Supporting / contradicting.** A candidate that persists in a held-out later period supports it; one that appears only in the discovery period contradicts it.
- **Alternatives and confounders.** Shared day-of-week and seasonal structure, a single outlier day, shared missingness, and features that are algebraically related (calendar load and away-time).
- **Null / insufficient.** "No pair exceeds the chance level after correction" is the expected and acceptable result for a short pilot.
- **Observer with only these sources.** Shows how many weak, spurious links a large dataset generates, which is itself a privacy-and-inference lesson about unreliable profiling.
- **How it could mislead.** Reporting the top-ranked pair without the number of tests; ignoring temporal dependence; presenting a hypothesis as a finding; a language model writing a plausible story for a chance association.

### INV-16 Optional forecast benchmark (later)

- **Question.** Can a model predict a defined, near-term event (for example the next day's first-departure window, or whether a given place is visited) better than simple baselines, and how much does each additional source add?
- **Sources and minimum coverage.** Location alone, then Location plus Motion, then all authorized sources. Requires weeks of history beyond the pilot; defer until INV-01, INV-02, and INV-04 are stable. This is an optional follow-on (D-025), not part of the first explorer.
- **Sample unit.** A prediction-day (or prediction-event). Predictions on consecutive days are dependent and the evaluation is rolling and forward-only.
- **Method ladder.** (1) Baselines first: same-weekday last value, historical mode, calendar-derived knowledge kept separate from behavior-derived inference. (2) Candidate models only if they beat baselines in a forward-only backtest. (3) Prospective test: predictions with probabilities or time windows are committed before the outcome by a verifiable pre-outcome lock (not a bare hash), with the scoring rule fixed in advance.
- **Outputs and uncertainty.** Scored predictions including misses, calibration against the stated probabilities, and the marginal improvement of each source with intervals over the prospective period.
- **Supporting / contradicting.** Beating the baseline prospectively over enough events supports predictive value; matching the baseline means the extra source adds nothing measurable.
- **Alternatives and confounders.** Routine alone explains the prediction; leakage from future data; a schedule change; the baseline's strength.
- **Null / insufficient.** "No improvement over the baseline" is a useful result about marginal information.
- **Observer with only this source.** Measures what location alone could predict of a person's next day, versus a richer source set, as a privacy quantity.
- **How it could mislead.** Backtesting with leaked data; choosing the metric after seeing the outcome; reporting only correct predictions; reading predictive accuracy as causation.

---

## Recommended first investigations for a 2 to 4 week self-collection pilot

The pilot validates the pipeline and coverage (D-025); it cannot establish stable personal relationships. The following selection is conditional on the lab's actual coverage and should be revised if a source is unavailable.

1. **INV-01 Where do I spend time? (Location only).** A descriptive question needing no cross-source assumption. Two to four weeks gives enough distinct days for repeated-visit structure and a split-half stability check, and the output feeds the place objects of the explorer. It tests the location pipeline, gaps, and battery behavior (BAT-01) together.
2. **INV-07 with INV-08 (App Privacy Report inventory).** This supplies the digital-behavior or app-metadata source required by the V1 target (three categories across two domains). The seven-day window means a 2 to 4 week pilot can capture several non-overlapping windows, which directly exercises overlap handling (SYN-03, D-034). The analysis is descriptive and does not depend on weak statistical assumptions. The conclusions remain limited to metadata, not content.
3. **INV-11 When am I active in a service? (Account export plus time).** An export can supply historical depth that the pilot cannot collect live, so the question can be answered with more weeks of data than the pilot itself produces. It depends on ACC-01 showing timestamped fields; if the export lacks them, replace with INV-05 (Health steps plus Calendar), which is the fallback if Location is sparse.

Why these three: they are descriptive, low in multiple-comparison burden, and each stands on one source so a failure in another source does not block them. Together they cover mobility, app metadata, and a service account across two domains, and they can be placed on the shared timeline of INV-14 as a first connected demonstration. Their data volumes (visits, app-resource-days, active days) are measured in tens, not thousands, and the entries state this.

Deferred for the pilot: INV-15 (too few days for a scan after correction), INV-16 (needs history and a lock procedure), INV-03/INV-04 (depend on Motion history that is not yet established), INV-12 and INV-13 (need longer histories or an overlapping period of at least 28 days).

## Common failure modes to check before publishing any result

- The sample unit and `n` are stated and the observations were collapsed to it.
- Coverage and missingness are shown beside the result; missing is not zero.
- The method ladder was followed in order and the baseline was reported.
- Exploratory and confirmatory results are separated; a discovery period is not reused for validation.
- Every comparison tested is counted, including those not reported.
- The privacy-revelation paragraph is not worded as a claim about a company.
- No clinical, financial, or legal conclusion; no inference about a nonparticipant.
- Any language model contribution is labeled, versioned, and treated as a hypothesis or phrasing only.
- The participant can inspect, correct, export, and delete the result and its inputs.

## Open items

- Real coverage will replace the heuristic thresholds above.
- The exact set of pre-declared features, the dwell and radius parameters, and the choice of bootstrap or permutation method are undecided and belong to a later technical decision.
- Minimum data volume for publication and the multiple-testing approach remain open items in [inference-engine.md](inference-engine.md#open-inference-decisions).
- Any investigation touching Screen Time data is excluded until SCT-01/SCT-02 produce a legitimate, exportable source.
