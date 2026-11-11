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
| 4 | Loom | Provenance threads for each finding: source → import batch → observation → normalized event → finding → participant correction. Skipped levels are dashed and marked "not linked". The hypothesis finding ends in "needs evidence". |

## Known limits

- The synthetic month is very regular, so the trained model scores almost perfectly. That checks the pipeline. It says nothing about predictability.
- The Fan's percentile bootstrap and the record's Fisher-z interval differ. Neither corrects for autocorrelation.
- Checked in desktop Chrome only. Phone layout (panel toggles) and screen-reader use are not verified.
- `prefers-reduced-motion` skips the intro, the auto-rotation and the pulses, and jumps to the end state.
