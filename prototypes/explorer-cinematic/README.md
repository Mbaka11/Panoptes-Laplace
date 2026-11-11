# Cinematic explorer prototype (D-039)

A standalone page that tests a "living corpus" look on the synthetic persona (Subject EX-01, fictional Port Meridian). Every value is invented. It is not a production UI, and no framework has been chosen.

## Run

From `prototypes/`:

```bash
python -m http.server 8765 --bind 127.0.0.1
# open http://127.0.0.1:8765/explorer-cinematic/
```

The page reads `data/persona.json` and falls back to `../explorer-concept/data/persona.json`, so the dataset is not duplicated. Three.js r128 loads from cdnjs. Without it, only the Corpus lens is missing.

## Lenses

| Key | Lens | What it shows |
|---|---|---|
| 1 | Corpus | Each record is one bright core with decorative dust around it. Five forms: anatomy (source lobes, import stem, findings core), sphere (time-ordered), strata (evidence ladder), chrono (source lanes with declared missing periods) and map (fictional plane plus an unlocated ring). During playback, records ignite in time order and links grow when both ends exist. |
| 2 | Fan | finding-0002, recomputed: 1,500 seeded bootstrap trend lines against a permutation null, plus a ρ histogram and a percentile interval. The verdict is computed, not hard-coded. |
| 3 | Train | Logistic regression or a small MLP trained live to answer "at the work place this hour?" from time, calendar, motion and phone metadata. Edge thickness is the weight, pulse speed is the gradient, and every weight is traced over epochs. Uses a date split (D00–D20 train, D21–D27 test) against an hour × weekday baseline. Hours with unknown location are excluded, never labelled. |
| 4 | Clusters | Live k-means over the 28 days, using twelve daily measures and never the weekday. Each day carries a 24-hour ring coloured by place. The silhouette score is shown for k = 2–5, and a 60-resample bootstrap measures each group's stability before a candidate name appears. On EX-01 it separates Saturdays, Sundays and weekdays without being given the weekday. |
| 5 | Loom | Provenance threads for each finding: source → import batch → observation → normalized event → finding → participant correction. Skipped levels are dashed and marked "not linked". The hypothesis finding ends in "needs evidence". |

| 6 | Control | A simulated participant control room on the 3D corpus. Pause a source from the cursor, preview a deletion cascade that follows provenance (source → records and batches → findings → corrections and hypotheses), then watch it go dark. Includes an export manifest with a SHA-256 of the remaining records. Nothing real is changed. |

Other controls:
- **Tour:** an automatic cinematic walkthrough of every lens with captions. Any click or key stops it.
- **Density:** a dust slider in Corpus, which defaults to 60% on narrow screens.
- **Workspace selector:** switches between the EX-01 persona and `data/fixtures-workspace.json`. That file is produced by `python -m spikes.explorer_export --fixtures` from the parser spikes (D-040). Lenses whose required record types are missing say so instead of showing anything. The choice is kept in session storage.

## Known limits

- The synthetic month is very regular, so the trained model scores almost perfectly. That checks the pipeline. It says nothing about predictability.
- The Fan's percentile bootstrap and the record's Fisher-z interval differ. Neither corrects for autocorrelation.
- Checked in desktop Chrome, and at 400 px width inside an iframe. Not checked on a real phone or with a screen reader.
- `prefers-reduced-motion` skips the intro, the auto-rotation and the pulses, and jumps to the end state.
