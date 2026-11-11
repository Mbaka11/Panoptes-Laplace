# Insight engine (spike, PROVISIONAL, synthetic only)

**Status:** work package 2 of [docs/insight-lenses.md](../docs/insight-lenses.md) (D-043). `spikes/insights.py` reads a `persona-contract-0.2-provisional` workspace document and returns new Finding records plus `SUPPORTED_BY` links. Standard library only, Python 3.10+, deterministic for a given `seed`. It is a demonstration engine, not a production analyzer or schema.

## Run

```bash
python -m spikes.insights --demo            # built-in synthetic document; prints findings, writes nothing
python -m unittest tests.test_insights -v
```

API: `daily_metrics(doc)`, `analyze(doc, *, alpha=0.05, seed=0, permutations=999)` (new records only, input untouched), `enrich(doc, ...)` (a new document; sets `meta.type_counts` and `meta.insights = {engine, version, alpha, metrics_scanned, day_types: {features, silhouette_by_k, k, unclassified_days}}`; re-running replaces earlier insight output).

## Daily metrics

Per local calendar day (date taken from the record's own timestamp string): steps, screen minutes, short-video minutes (`app_category` in `short_video`), late-night minutes, pickups, notifications, sleep onset (minutes after 18:00, assigned to the wake day), sleep duration, messages per contact, distinct places, minutes away from home, office visit, searches per sensitive category, sensitive-search share, precipitation. An absent source or unmeasured day is `"unknown"`, never 0. Overlapping Screen Time reports for the same `(day, app_id)` replace each other rather than adding. Each metric-day remembers its feeding record ids, used as evidence.

Assumption (ambiguity in the spec): for exports that list every event (messaging, searches) a day with no record is 0 while the source is present, unless its `Source.missing_periods` covers the whole day. Screen Time, Health, and sleep days without a record are unknown.

## Methods and limits

| Kind | Method | Limits |
|---|---|---|
| `shift` | Weekday medians removed, then scan every change day with at least 10 known days per side; statistic is the difference of medians (means for zero-inflated metrics, over 25% zeros). P comes from 999 seeded shuffles repeating the whole scan; Benjamini-Hochberg across scanned metrics; reported only if q <= alpha. The reported change day is the best of the near-maximal splits by within-segment deviation. Effect is reported as after/before ratio and difference with unit. | Shuffling ignores autocorrelation, so p is optimistic. Small n. BH controls false discoveries only across the scanned metrics. A metric needs at least 20 known days and 60% coverage, else an `insufficient` finding. |
| `lagged_association` | Spearman rho (weekday effects removed) for a predeclared pair list at lag 0 or 1, permutation p, BH across testable pairs. | Same autocorrelation caveat. Pairs with fewer than 20 day pairs are skipped. `precip_mm -> office_visit` uses only usual office weekdays. Association, never effect. |
| `routine` | Office visits on weekdays with at least 75% regularity (at least 4 measured such days); recurring transactions per `merchant_category` on weekdays with at least 75% recurrence. | Descriptive over a short window. |
| `day_type`, `day_type_trend`, `day_types_none` | See "Day types" below. | See "Day types" below. |
| `observer_inference` | Rule table below, over the findings above. | Hypothesis only; inherits every upstream limit. |
| `suggestion` | Only the rainy usual-office-weekday association (negative rho). | Optional note, not advice. |
| `insufficient` | Missing sleep, Screen Time, Health, Visit, or messaging source; or a metric with too few measured days. | States what is unknown. |

## Mirror rules

| Rule | Requires | Source types | Sensitive |
|---|---|---|---|
| `sleep_deprivation_low_activity` | sleep duration down or onset later, and steps down | SleepInterval, DailyHealthAggregate | yes |
| `heavy_short_video_use` | short-video shift up, or recent median >= 90 min | ScreenTimeDaily | no |
| `possible_relationship_change` | shift down in messages with a contact (per contact; about the participant's pattern only) | MessagingDaily | yes |
| `sensitive_topic_interest` | shift up in searches on a sensitive topic or in the sensitive-search share (topic-interest wording) | AccountActivity | yes |
| `state_timing` | a `day_type_trend` that became more frequent, whose type portrait has late-night use up (or later sleep onset) and steps down (or shorter sleep) | ScreenTimeDaily, DailyHealthAggregate | yes |
| `commuter_paid_parking` | office-weekday routine and a recurring `*park*` spend routine | Visit, Transaction | yes (finances) |

Each carries `segment_label`, `sources_required` (source ids actually present), `holders` ("could see" wording), `typical_uses`, `sensitive`, `rests_on` (finding ids), and `alternatives`. A rule does not fire if a required source type is absent.

## Guardrails (enforced in code, checked in tests)

Statements say "could infer" for Mirror findings; no "diagnos", "depress", "disorder", "causes", "because of"; topic labels containing such stems are replaced by "a sensitive topic"; `causal_claim` is always false; supporting evidence is limited to observation or normalized-event records (Place and other inference records are never cited; hypotheses cite through `rests_on` only); contact references appear as given and only in the participant's own pattern; null or mostly-unknown data yields no shift; sensitive findings are flagged. `check_guardrails` raises on a violation.

## What it does not claim

No causation, no diagnosis, no statement that any company holds a source or drew a conclusion, no statistical significance for real data, and no feasibility of the underlying real-world sources (see the status column in the lens spec). Permutation p-values are optimistic under autocorrelation. Prediction is not implemented (D-025).

## Validator notes

`explorer_export.validate_contract` resolves only `*_id` strings and the lists `evidence_ids` and `supporting_evidence_ids`; `rests_on`, `context_ids`, and `contradicting_evidence_ids` are not checked for resolution. Any `app_id` or `place_id` on input records must resolve to an `App` or `Place`/unknown record.

## Day types (version 0.2)

Question answered: which kinds of days does this person have, relative to their own usual weekday, and is one kind becoming more frequent? Output is a measured portrait, never a psychological label.

1. **Features:** screen, short-video and late-night minutes, pickups, notifications, sleep onset and duration, steps, minutes away, distinct places, total messages (sum over contacts). A feature needs at least 60% known days. Each has its weekday medians removed (`_deseasonalize`), then is scaled by median and 1.4826 x MAD; when MAD is 0 the mean absolute deviation about the median is used, and a feature that is still constant is dropped. z-scores are clipped to +/-5. Fewer than 3 features, or fewer than 20 classified days, gives an `insufficient` finding.
2. **Unclassified days:** a day whose known features are below 70% of the eligible set is not clustered and not imputed (listed in `meta.insights.day_types.unclassified_days`).
3. **Clustering:** k-means for k = 2..5 with a partial distance (mean squared difference over features known in both vectors), k-means++ seeding, 10 seeded restarts, best inertia. k with the best mean silhouette wins (ties favour smaller k); a clustering with a cluster under 4 days is not eligible. A best silhouette under 0.25 gives a `day_types_none` finding, a valid null.
4. **Stability:** 60 bootstrap resamples (3 restarts each); each type's mean best-match Jaccard (its days in the resample versus the closest bootstrap cluster). Stable is >= 0.6; unstable types are still reported, flagged, and never trended.
5. **Portrait:** features ranked by absolute median z of the member days (|z| >= 0.5); up to 6 are stored, the statement quotes the first 4, in original units against `usual` (overall median of the raw feature, "the person's usual level" and not the weekday-adjusted one). Keys `T1..Tk` are ordered by size (descending), then first day.
6. **Trend:** the 0/1 membership of classified days is scanned with the shift method (mean center, min 10 days per side, 999 permutations), BH across the stable types tested. For k = 2 the two types are complements, so only the one that became more frequent is tested. `day_type_trend` rests on its `day_type` finding.

Limits: k-means favours compact, similar-spread groups and always returns k clusters, so the silhouette gate and bootstrap carry the weight; partial distance makes days with different known features only loosely comparable; consecutive days are autocorrelated, so both the bootstrap stability and the trend p-value are optimistic; with 56 days a 3-4 day cluster is fragile; the types are fitted on the same days that the trend scan then tests (circular for a change that defines the clusters), so a trend is a description of when the fitted types occurred, not independent evidence; weekday removal assumes a stable weekly rhythm; a feature that changes level at a step splits the person into "before" and "after" types by construction, which is the point here but is not evidence about causes.
