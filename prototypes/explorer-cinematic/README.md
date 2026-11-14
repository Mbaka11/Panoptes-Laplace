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
| 1 | Corpus | Each record is one bright core with decorative dust around it. Five forms: anatomy, sphere (time-ordered), strata (evidence ladder), chrono (source lanes with declared missing periods) and map (fictional plane plus an unlocated ring). Records ignite in time order during playback. Reviewed on the eight workspaces: lanes and strata depth scale with the number of sources (up to 11); a finding's evidence links (up to ~400) are drawn faint until the finding or one of its records is selected (Finding links: Focus or All); labels are placed by priority and skipped when they would overlap; legend counts per class or source and flags sources with declared gaps; visits fan out around their place in the map (layout, not geography); sources without a fixed colour get a stable derived one; records in a sensitive category show their text, topic and category as withheld; the inspector caps long id lists and groups links by type, and findings offer Trace in Loom. |
| 2 | Shifts | Small multiples of the daily metrics. Dots are known days, hatched columns are unknown days (never zero), amber and cyan lines are the level before and after the change day of the shift Finding, a dashed line marks the change day, and each panel carries effect ratio and q-value with "descriptive change; cause not identified". Metrics with no shift are dimmed (toggle to hide). The header shows metrics scanned and alpha. Click a panel for the Finding, its alternatives and uncertainty. Without `/metrics`, only the shift findings are listed. |
| 3 | Mirror | "What an observer could infer": one card per `observer_inference` Finding with segment label, could-infer statement, a Sensitive badge (distinct card, visible only in the participant's own workspace), required sources with their real-world status, who could see them, typical uses, the findings it rests on (clickable) and alternative explanations. Below: optional suggestions and "Not enough data" findings. Empty state: "Nothing an observer could infer at the declared evidence level". |
| 4 | Fan | One lagged association, recomputed: 1,500 seeded bootstrap trend lines against a permutation null, a ρ histogram and a percentile interval. A selector lists every `lagged_association` Finding (and the persona's finding-0002), using the `/metrics` series at the Finding's lag. Correlation, not causation. |
| 5 | Train | Prediction, optional (D-025): "Will tonight be a late night?" (late-night minutes above the person's own training median), from the previous day's late-night minutes, sleep, steps, screen minutes and a weekend flag. First 70% of days train, last 30% test, scored against a majority-class and a persistence baseline. Unavailable, with the reason, when those metrics are unknown (persona, fixtures, sparse). Edge thickness is weight, pulse speed is gradient. |
| 6 | Day types | Engine results (engine 0.2 `day_type`, `day_type_trend`, `day_types_none` Findings), not browser clustering. Each day is a point pulled toward its type with the 24-hour place ring; unclassified days stay apart ("unclassified (not enough measured features)") and are never assigned. A calendar strip colours every day by type (unclassified hatched) with a marker at each trend's change day. Portrait cards show size, share, stability (Jaccard) and measures in original units against the usual level ("late night minutes 56 vs usual 9 min/day"), strictly descriptive; unstable types are muted. Trend callouts note that p-values are optimistic and that complementary trends are one change. A silhouette-by-k chart marks the 0.25 threshold. `day_types_none` shows an honest null with the calendar; `insufficient` (day_types) shows an unavailable message. A type links to the Mirror cards that rest on it. With no day-type findings (persona, fixtures) the lens falls back to the old live k-means, relabelled "Raw grouping (legacy)", which mostly rediscovers the weekly rhythm. |
| 7 | Loom | Provenance audit for one finding. Columns run source → import batch → observations (and normalized events) → computed daily metric → inference → derived inference → hypothesis → participant review. Threads are bundled per record type and batch (width = record count), and findings that rest on other findings are followed to any depth. The panel lists checks re-run in the browser from the published records and series, never trusting the engine's numbers: evidence ids resolve, provenance and batch digests are present, declared `sources_required` match the sources actually reached, shift medians, lagged Spearman ρ (weekday-adjusted) and day-type shares are re-computed, gated or unproven real-world sources and declared missing periods are flagged, no causal claim, review status. Every step opens with sample records and their provenance line; a metric step shows its daily series with unknown days marked. "Trace in Loom" in the Shifts, Mirror and Day types inspectors opens a finding here. Narrow screens stack the columns vertically. |
| 8 | Control | A simulated participant control room on the 3D corpus (nothing real is paused, deleted or stored). Per-source cards show state, live/total records, declared gaps (unknown, not zero; undeclared gaps shown as unknown, not none) and real-world status (gated, partly unproven). Pause and "delete records from cursor on" act from the time-rail cursor. The deletion preview cascades along provenance, including hypotheses and day-type trends that only `rests_on` a removed finding, lists findings with evidence lost (a of N, review status, Trace in Loom link) and warns when the participant's own corrections would go with them. The workbench's findings source is shown separately as derived, with no Pause. The export manifest has a SHA-256, counts per type and source, declared gaps, finding review states, an option to leave out sensitive records, and how many kept findings cite left-out records. Out-of-reach copies are stated. |

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


Note (Day types lens): the tab was renamed from Clusters; key 6 and its position are unchanged. See `docs/insight-lenses.md` (Day types) for the engine method.
