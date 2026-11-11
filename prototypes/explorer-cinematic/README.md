# Cinematic explorer prototype (D-039)

A standalone page that tests a "living corpus" look on the synthetic persona (Subject EX-01, fictional Port Meridian). Every value is invented. It is not a production UI, and no framework has been chosen.

## Run

From the repository root (D-042):

```bash
python -m explorer.server
# open http://127.0.0.1:8765/
```

The server builds and validates the workspaces from the spikes and serves them at `/api/workspaces/{key}`, with daily metric series at `/api/workspaces/{key}/metrics`; see [the server README](../../explorer/README.md). The workspace selector is filled from `/api/workspaces` (persona, fixtures and the six 56-day profiles). A plain static server still works from `prototypes/`:

```bash
python -m http.server 8765 --bind 127.0.0.1
# open http://127.0.0.1:8765/explorer-cinematic/
```

Without the API, the selector offers only the persona and the fixture export, read from `data/`. There is then no `/metrics` series: Shifts lists its findings only, Train is unavailable, and Fan works only on the persona's finding-0002. Three.js r128 loads from cdnjs. Without it, only the Corpus and Control lenses are missing. The observation window is read from `meta.window`, so the 28-day persona and the 56-day profiles both work.

## Lenses

| Key | Lens | What it shows |
|---|---|---|
| 1 | Corpus | Each record is one bright core with decorative dust around it. Five forms: anatomy, sphere (time-ordered), strata (evidence ladder), chrono (source lanes with declared missing periods) and map (fictional plane plus an unlocated ring). Records ignite in time order during playback. |
| 2 | Shifts | Small multiples of the daily metrics. Dots are known days, hatched columns are unknown days (never zero), amber and cyan lines are the level before and after the change day of the shift Finding, a dashed line marks the change day, and each panel carries effect ratio and q-value with "descriptive change; cause not identified". Metrics with no shift are dimmed (toggle to hide). The header shows metrics scanned and alpha. Click a panel for the Finding, its alternatives and uncertainty. Without `/metrics`, only the shift findings are listed. |
| 3 | Mirror | "What an observer could infer": one card per `observer_inference` Finding with segment label, could-infer statement, a Sensitive badge (distinct card, visible only in the participant's own workspace), required sources with their real-world status, who could see them, typical uses, the findings it rests on (clickable) and alternative explanations. Below: optional suggestions and "Not enough data" findings. Empty state: "Nothing an observer could infer at the declared evidence level". |
| 4 | Fan | One lagged association, recomputed: 1,500 seeded bootstrap trend lines against a permutation null, a ρ histogram and a percentile interval. A selector lists every `lagged_association` Finding (and the persona's finding-0002), using the `/metrics` series at the Finding's lag. Correlation, not causation. |
| 5 | Train | Prediction, optional (D-025): "Will tonight be a late night?" (late-night minutes above the person's own training median), from the previous day's late-night minutes, sleep, steps, screen minutes and a weekend flag. First 70% of days train, last 30% test, scored against a majority-class and a persistence baseline. Unavailable, with the reason, when those metrics are unknown (persona, fixtures, sparse). Edge thickness is weight, pulse speed is gradient. |
| 6 | Clusters | Live k-means over the days using daily measures, never the weekday. Hour rings per day, silhouette for k = 2-5, and a 60-resample bootstrap stability before a candidate name appears. |
| 7 | Loom | Provenance threads for each finding: source, import batch, observation, normalized event, finding, correction. Skipped levels are dashed and marked "not linked". Hypotheses that rest on other findings thread through them; findings with no chain say what is missing. |
| 8 | Control | A simulated participant control room on the 3D corpus. Pause a source, preview a deletion cascade along provenance, then watch it go dark. Includes an export manifest with a SHA-256 of the remaining records. Nothing real is changed. |

Other controls:
- **Tour:** an automatic cinematic walkthrough of every lens with captions. Any click or key stops it.
- **Density:** a dust slider in Corpus, which defaults to 60% on narrow screens.
- **Workspace selector:** lists the workspaces from `/api/workspaces` (label and workspace id), with a static fallback to the persona and `data/fixtures-workspace.json` (D-040). Lenses whose data is missing say so instead of showing anything. The choice is kept in session storage.

## Known limits

- Train uses a short synthetic window with a date split. Habits can shift between train and test days, and one test day moves accuracy by several points. It checks the pipeline and says nothing about predictability.
- Fan recomputes Spearman on raw daily values. The engine removes weekday effects first, so its rho differs slightly.
- The Fan's percentile bootstrap and the record's Fisher-z interval differ. Neither corrects for autocorrelation.
- Checked in desktop Chrome, and at 400 px width inside an iframe. Not checked on a real phone or with a screen reader.
- `prefers-reduced-motion` skips the intro, the auto-rotation and the pulses, and jumps to the end state.
