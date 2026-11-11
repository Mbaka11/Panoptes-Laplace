# Insight engine on six synthetic profiles (run record)

**Date:** 2026-11-11. **Scope:** `spikes.insights` 0.1 against the hidden scenario truth of `spikes.profiles` (contract 0.2, D-043). Synthetic only. These numbers describe how the engine behaves on data built to contain known effects. They say nothing about real people, real sources, or real effect sizes.

Environment: macOS 27.2, Python 3.14.7. Command: `python3 -m unittest tests.test_insight_profiles -v`, plus a five-seed scoring run (permutation seeds 0 to 4, 999 permutations, α = 0.05, Benjamini-Hochberg across about 16 scanned metrics).

## Shift detection versus planted truth (five permutation seeds)

| Profile | Planted change | Detected | Change-day error | Unplanted shifts |
|---|---|---|---|---|
| steady (null control) | none | not applicable | not applicable | 0 of 5 runs |
| doomscroll | 7 metrics at day 28 | 7 of 7 in 5 of 5 runs | 0 to 2 days | 0 |
| social_drop | contact-A messages at day 31 | 5 of 5 | 0 days | 1 of 5 runs (`sleep_onset`, q ≈ 0.04; means before and after are equal) |
| social_drop | minutes away from home, −7% at day 31 | 0 of 5 | not applicable | (same as above) |
| search_drift | sensitive search share, 10% to 40% from day 24 | 1 of 5 | 6 days | 0 |
| commuter | none (routine and rain context only) | not applicable | not applicable | 0 |
| sparse | none | not applicable | not applicable | 0 |

## Other findings

- **doomscroll:** lagged associations late-night minutes → next-day steps (ρ ≈ −0.80, the planted lag), late-night → same-day sleep duration, sleep → next-day steps, and screen → same-day steps. Mirror: "possible sleep deprivation and declining activity" (sensitive) and "heavy short-video use".
- **social_drop:** Mirror hypothesis about the participant's own messaging pattern with contact-A. It is flagged sensitive and lists alternatives (travel, another channel, a changed phone, a busy period). Nothing is said about the contact.
- **commuter:** rain → fewer office visits on usual office weekdays (ρ ≈ −0.74). Routines: office Tue/Wed/Thu, parking on those days, food on Fridays, groceries on Sundays. Mirror: commuter with paid parking. One optional suggestion, labelled "Context only".
- **sparse:** `insufficient` findings for sleep (no producer) and screen time (no source). No values were invented.

## Interpretation and limits

- The engine finds strong, abrupt, multi-metric changes reliably and places them within two days.
- **Detection boundary.** A sensitive-search share change of 10% to 40%, on about four searches a day over eight weeks, sits at the boundary once 16 metrics are corrected together. Whether it is reported depends on the permutation seed. A real person's search history would usually carry more searches a day. We did not raise the synthetic volume to make the test pass, and the test asserts direction only.
- **Small changes are not detected.** A −7% change in time away from home is not detected. That is expected at this sample size.
- **False positives.** Benjamini-Hochberg controls the false-discovery *rate*, not the chance of any false positive. One unplanted shift appeared in 1 of 30 profile-runs. Autocorrelation is ignored, so p-values are optimistic. Findings are labelled exploratory.
- **Built-in effects.** The planted effects are generator choices, so a successful detection checks the pipeline. It does not discover anything.

## Day types (engine 0.2, 2026-11-11)

Command: `enrich(profile)` for each profile, permutation seeds 0 to 4, defaults (999 permutations, 60 bootstrap resamples). Whole `enrich` per profile: 0.07 to 0.45 s. Same caveats: planted effects are generator choices, so this checks the pipeline.

| Profile | Features | k (silhouette) | Types (days, stability) | Trends | `state_timing` |
|---|---|---|---|---|---|
| steady | 11 | none (best 0.18 to 0.21, below 0.25) | none | none | no |
| doomscroll | 11 | 3 (0.27 to 0.28), all seeds | T1 28 d, J 0.84 to 0.90: late-night use 56 vs usual 9 min, short-video 68 vs 40, steps 4218 vs 6487, sleep 391 vs 436 min. T2 21 d, J 0.76 to 0.80: sleep 463 vs 436 min, earlier sleep onset, steps 7912 vs 6487. T3 7 d, J 0.56 to 0.62 (stable in 2 of 5 seeds): at home, minutes away 0 vs 490, 1 place, 31 messages vs 25 | T1 more frequent from day 28 (29 in 1 seed), 0% to 100%; T2 less frequent from day 26 | yes, all seeds |
| social_drop | 11 | none (0.17 to 0.18) | none | none | no |
| search_drift | 11 | none (0.12 to 0.15) | none | none | no |
| commuter | 11 | none (0.20 to 0.23) | none | none | no |
| sparse | 4 (steps, minutes away, places, messages; no sleep or screen) | 2 (0.49) | T1 30 d, J 0.93: no feature departs clearly. T2 6 d, J 0.73 to 0.84: minutes away 43 vs 488 (days at home) | none (k = 2 tests one type; membership is steady) | no |

Observations and limits:

- The planted multi-metric change appears as one late-night, low-activity type whose share goes from 0% to 100% at day 28 (a step in the generator), plus a complementary earlier-and-longer-sleep type becoming rarer. That is two views of one change, and they are not independent findings.
- The silhouette threshold held on all five null or near-null profiles, but steady and commuter come within 0.02 to 0.05 of it. With 11 features and 56 days, noise silhouettes of about 0.2 occur; 0.25 is a heuristic, not a calibrated test.
- sparse yields a home-days type that is real in the generated data (location off on many days), found from only four features. It shows the engine does not invent sleep or screen features: none are listed in `meta.insights.day_types.features`.
- T3 in doomscroll sits near the stability threshold (J 0.56 to 0.62) and flips between stable and unstable across seeds; it is a small cluster of 7 days.
- Unit tests on small documents: a planted two-state document gives a stable type and a trend within 5 days of the change; across 12 pure-noise seeds the total number of trends is at most 1 (observed 0).
