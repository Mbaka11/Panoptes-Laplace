# Synthetic profiles (contract 0.2, PROVISIONAL)

## Status

`spikes/profiles.py` deterministically generates six fictitious 8-week profiles under `persona-contract-0.2-provisional` (work package 1 of `docs/insight-lenses.md`). Synthetic only: a fictional city, `com.example.*` bundle ids, `*.example` hosts, pseudonymous contacts. It is a demonstration contract, not a production schema, and synthetic availability of a source is not a capability claim.

Window: 56 days from Monday 2026-01-05, fixed `Etc/GMT+5`. Each profile uses its own seeded RNG streams; output is byte-identical across runs (about 0.5 to 0.9 MB each).

## Run

```bash
python3 -m spikes.profiles --summary     # per-profile type counts and sizes
python3 -m unittest tests.test_profiles -v
```

API: `PROFILES`, `build(key) -> {meta, records}`, `scenario_truth(key)` (hidden planted truth for tests and scoring only; never in the document), `dumps(doc)`.

## Profiles

| Key | Workspace | Sources present | Planted story (truth lives in `scenario_truth`) |
|---|---|---|---|
| `steady` | ws-prof-steady | all | none (null control) |
| `doomscroll` | ws-prof-doomscroll | all | changes on several metrics at one day, plus a one-day lag |
| `social_drop` | ws-prof-social | all | one pseudonymous contact stops; evenings at home rise |
| `search_drift` | ws-prof-search | all | share of sensitive-topic searches rises |
| `commuter` | ws-prof-commuter | all plus Transactions | three office days, parking spend, rain context |
| `sparse` | ws-prof-sparse | no Screen Time source, no sleep records | many location-off days, missing steps |

## Invariants (tested)

- `explorer_export.validate_contract(build(k)) == []`; unique workspace ids; two builds are equal.
- Unknown is never 0: missing steps are `"unknown"` with `steps_status`; sparse has no `SleepInterval`, HealthKit sleep read status `unknown`, and no Screen Time source or records (absent, not zeros).
- `MessagingDaily` carries only `contact-A` style refs and counts; no names or content.
- `ScreenTimeDaily` has `summable: false`.
- No planted-scenario keys or words appear in `meta` or `records`.

## Not claimed

- No finding, correction, or inference records: the insight engine adds those.
- No `LocationSample`, `ResourceAccess`, or `NetworkAggregate` records.
- Noise levels are chosen for plausibility, not calibrated to any population; topic labels are a toy lexicon.
- Sleep, Screen Time, messaging, and transaction sources are unproven or gated on real devices (see each Source `availability`).
- Nothing here is evidence about real people or companies.
