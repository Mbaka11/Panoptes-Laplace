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
