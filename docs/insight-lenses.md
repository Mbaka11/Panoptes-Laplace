# Insight lenses: shifts, observer mirror, and context (provisional)

**Status: PROVISIONAL (D-043). Synthetic only.** This document specifies the next explorer work after the owner's review on 2026-11-11. It extends the demonstration contract `persona-contract-0.1-provisional` to `persona-contract-0.2-provisional`. It is not a production schema, and it does not relax the collection-feasibility, Mac, or real-data gates.

## Why

The owner asked what the Train lens ("is the subject at work this hour?") reveals about a life. Not much. The project's purpose is to show **what an outside observer could infer from a person's traces**, and to let the person see those patterns first (D-023, `product-vision.md`, `inference-engine.md` §6 "Privacy view"). The explorer had no lens for that.

Three insight families replace the work-hour question as the core story:

| Family | Question | Example |
|---|---|---|
| **Shifts** | When did a habit change, by how much, and how sure are we? | From week 5, short-video screen time rose 2.4×, late-night phone use started, sleep onset moved 70 min later, steps fell 30%. |
| **Mirror** | What could someone holding these sources conclude, and who holds them? | "Possible sleep deprivation and declining activity." Sources: Screen Time plus Health. Typical ad use: delivery or fast-food promotions, sleep aids. Holders: the device vendor (on-device), the app vendor (its own usage only). |
| **Context** | Which patterns repeat together, and what context sits around them? | Late-night use is followed by fewer steps the next day (lagged association, permutation p, n days). On rainy office days the subject stays home more often. Optional suggestion, clearly labelled. |

Prediction stays optional (D-025). When shown, it should answer a life-relevant question, such as "is tonight likely to be a late night?", against a stated baseline. The work-hour question goes.

## Guardrails (binding for this work)

- **Could, not did.** A Mirror finding says what an observer *could* infer from named sources. It never claims a company did infer it, holds every source, or acted on it.
- **Correlation stays correlation.** Shift and Context findings are descriptive or associational. Every hypothesis lists alternative explanations.
- **Sensitive categories.** Health and mental-health topics, relationships, sexuality, religion, politics, finances. Findings touching them carry `sensitive: true`, use topic-interest wording ("searches increasingly about anxiety"), never a diagnosis or a label of the person, and are shown only inside the participant's own workspace.
- **Nonparticipants.** Messaging data appears only as daily counts per pseudonymous contact (`contact-A`), sent and received, from the participant's own export. No names, handles, content, or attributes of the other person, and no inference about them. "Possible relationship change" is a hypothesis about the participant's own pattern, with alternatives (travel, a new channel, a changed phone).
- **Unknown is not zero.** A profile without a sleep producer or a Screen Time source yields `insufficient` findings, not low values.
- **Multiple testing.** Shift scanning reports how many metrics were scanned and controls the false-discovery rate with Benjamini-Hochberg. A profile with no planted change must produce no shift finding at the declared level (checked across all seeds in tests).
- **Suggestions** are optional, marked `finding_kind: "suggestion"`, `evidence_class: "hypothesis"`, and cite the findings they rest on. No clinical, financial, or legal advice.
- **Source realism.** Each new record type carries the real-world path it would come from and that path's status (see the table below). Several are gated or unproven. Synthetic availability is not a capability claim.

## Contract 0.2 additions

All records keep the 0.1 envelope: `id`, `type`, `workspace_id`, `source_id`, `evidence_class`, `granularity`, `timezone`, `import_batch_id`, `event_time` or `event_start`/`event_end`, and `provenance`. Unknown values use the string `"unknown"` with a sibling `*_status`.

| Type | Class | Granularity | Fields | Real-world path (status) |
|---|---|---|---|---|
| `SleepInterval` | observation | interval | `sleep_source` (`watch`, `phone_schedule`, `unknown`), `stage` (`asleep`, `in_bed`) | HealthKit sleep analysis from an authorized producer. Unproven: needs a producer (HLT-01). |
| `ScreenTimeDaily` | observation | aggregate | `app_id`, `app_category`, `minutes`, `pickups`, `late_night_minutes` (00:00 to 05:00 local), `summable: false` across overlapping reports | Family Controls / DeviceActivity export. Gated: entitlement, iOS 26.4+, region (A4 to A6). |
| `NotificationDaily` | observation | aggregate | `app_id`, `count` | Screen Time report. Gated, as above. |
| `MessagingDaily` | observation | aggregate | `app_id`, `contact_ref` (`contact-A`…), `sent`, `received` | Participant's own account export (for example a social app data download). Unproven: ACC-01. |
| `AccountActivity` (extended) | observation | point | adds `topic` and `topic_method` (`keyword_lexicon_v0`), and `sensitive_category` (or `none`) on searches | Account export. Topic is a derived label: `topic_method` records how. |
| `Transaction` | observation | point | `merchant_category`, `amount`, `currency`, `place_id` or `unknown` | Optional participant-provided transaction export. No general iPhone API. |
| `WeatherDaily` | observation | aggregate | `precip_mm`, `temp_c_max`, `condition` | Public weather for the fictional city. A real lookup would reveal a coarse location to the weather provider. |

`DailyHealthAggregate`, `Visit`, `Trip`, `ActivityInterval`, `CalendarEvent`, `App`, `Domain`, `ResourceAccess`, `NetworkAggregate`, `Place`, and `Source` keep their 0.1 meaning.

### New Finding kinds

Existing Finding fields stay (`statement`, `input_window`, `method`, `method_version`, `statistic`, `supporting_evidence_ids`, `contradicting_evidence_ids`, `uncertainty`, `confidence`, `status`, `causal_claim: false`, `participant_correction`, `participant_review_status`). Added kinds:

| `finding_kind` | Class | Extra fields |
|---|---|---|
| `shift` | inference | `metric`, `change_day`, `baseline` {window, median, mad, n}, `after` {window, median, n}, `effect` (ratio or difference, with unit), `p_value`, `q_value` (BH), `metrics_scanned` |
| `lagged_association` | inference | `x_metric`, `y_metric`, `lag_days`, `rho`, `n`, `permutation_p`, `alternatives` [] |
| `routine` | inference | `pattern` (for example weekday × hour visit regularity), `support` (share of eligible days) |
| `observer_inference` | hypothesis | `segment_label`, `sources_required` [source ids], `holders` [{`holder`, `sees`}], `typical_uses` [], `sensitive`, `rests_on` [finding ids], `alternatives` [] |
| `suggestion` | hypothesis | `rests_on` [finding ids], `context_ids` [], `text` |
| `insufficient` | inference | `wanted` (what analysis), `missing` (which source or metric), `reason` |

Daily metrics fed to the analyzers (computed, never stored as raw observations): steps, total screen minutes, short-video minutes, late-night minutes, pickups, notifications, sleep onset (minutes after 18:00), sleep duration, messages with each contact, distinct places visited, minutes away from home, office visits, searches per sensitive category.

## Synthetic profiles

Eight weeks (56 days) each, seeded and deterministic, fictional city and identifiers, `meta.synthetic: true`. Each profile has a hidden **scenario truth** (planted change days, planted lags), exported by a separate function for tests only. It never appears in the workspace document.

| Key | Workspace | Story | What detectors should find |
|---|---|---|---|
| `steady` | ws-prof-steady | Regular office worker, no planted change | No shift (null control). Routine findings only. |
| `doomscroll` | ws-prof-doomscroll | From day 28: short-video time ×2.5, late-night use, later and shorter sleep, steps −30% | Shifts on those metrics near day 28. Lag: late-night minutes → next-day steps. Mirror: sleep deprivation and low activity. |
| `social_drop` | ws-prof-social | Daily messages with `contact-A` stop at day 31; evenings at home rise | Shift on contact-A messages. Hypothesis: possible relationship change, with alternatives. |
| `search_drift` | ws-prof-search | Searches drift toward sleep and anxiety topics after day 24; content otherwise similar | Shift in sensitive-topic share. Sensitive Mirror finding worded as topic interest. |
| `commuter` | ws-prof-commuter | Office Tue/Wed/Thu, paid parking each office day, stays home on most rainy office days | Routine (office days). Lag/context: rain → stays home. Mirror: commuter, parking spend. Optional suggestion. |
| `sparse` | ws-prof-sparse | Location off on many days, no sleep producer, no Screen Time source | `insufficient` findings, not zeros. No fabricated shift. |

## Work packages

1. **Profiles generator** (`spikes/profiles.py`): build the six profiles under contract 0.2, together with `scenario_truth(key)`.
2. **Insight engine** (`spikes/insights.py`): compute daily metrics, then shifts with BH correction, lagged associations with permutation tests, routines, Mirror rules, suggestions, and `insufficient` findings. Append Finding and Link records to a workspace document. Everything uses the standard library and is deterministic.
3. **Integration**: the server registers each profile as generator plus engine, and the validator accepts 0.2. Tests score the engine against scenario truth on every profile, including false positives on `steady`.
4. **UI**: replace the Train question with a life-relevant one. Add a Shifts lens (timeline of metric baselines and change points) and a Mirror lens (what could be inferred, from which sources, held by whom). Add a profile selector fed by `/api/workspaces`.
