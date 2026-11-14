# MOT-01: SDK verification and first Motion module

**Date:** 2026-11-13. **Scope:** the foreground Motion module in [`ios/SensorProbe`](../../ios/SensorProbe/README.md). **TEST BUILD, not cleared for real data** (gate R). This record covers SDK facts and the build; on-device behaviour is **not yet tested** (owner test below).

## Verified against the installed SDK (iPhoneOS 27.2, Xcode 27.2)

Headers under `…/iPhoneOS27.2.sdk/System/Library/Frameworks/CoreMotion.framework/Headers/`.

| Item | Result | Where |
|---|---|---|
| Activity availability | `CMMotionActivityManager.isActivityAvailable()` (class method) | `CMMotionActivityManager.h` |
| Activity authorization | `CMMotionActivityManager.authorizationStatus()` (class method, iOS 11+) | same |
| Pedometer availability | `CMPedometer.isStepCountingAvailable()`, `isDistanceAvailable()` (also floors, pace, cadence, events; floors/pace/cadence not used) | `CMPedometer.h` |
| Pedometer authorization | `CMPedometer.authorizationStatus()` (class method, iOS 11+). A separate status from the activity one is exposed; both are shown | `CMPedometer.h` |
| Status enum | `CMAuthorizationStatus`: `notDetermined`, `restricted`, `denied`, `authorized` (iOS 11+). `restricted` = system-wide restriction, `denied` = denied by the user | `CMAuthorization.h` |
| No request method | There is no `requestAuthorization`: the system dialog appears on the first Core Motion call (query or start). The pre-prompt therefore must come before the first call, and the probe re-reads the status by polling (up to 90 s) and on every foreground, because no delegate callback exists | headers (absence) |
| History query, activity | `queryActivityStartingFromDate:toDate:toQueue:withHandler:`; "The date range must be in the past. **Data is only available for the last seven days.**" The first returned activity may start before the requested start (it is the state at the start time) | `CMMotionActivityManager.h` |
| History query, pedometer | `queryPedometerDataFromDate:toDate:withHandler:`: "Data is available for up to 7 days", computed from a system-wide history collected in the background. `startDate`/`endDate` of the result are the **requested** window, so the returned window is not informative; the probe therefore queries one calendar day at a time and reports which days returned data | `CMPedometer.h` |
| Live updates | `startActivityUpdates(to:withHandler:)` (one handler at a time; first update is the current activity; "Updates are not delivered while the application is suspended"). `startUpdates(from:withHandler:)` for the pedometer delivers **cumulative** values since the start date | headers |
| Confidence | `CMMotionActivityConfidence`: `low` = 0, `medium`, `high` (ordinal, kept as ordinal) | `CMMotionActivity.h` |
| Activity flags | `unknown`, `stationary`, `walking`, `running`, `automotive`, `cycling` (iOS 8+). Flags are **not mutually exclusive** (for example stationary + automotive); all NO is possible. The probe stores the set as a label and uses `moving_unclassified` when none is set | `CMMotionActivity.h` |
| Errors | `CMError` codes include `CMErrorMotionActivityNotAvailable` (104), `...NotAuthorized` (105), `...NotEntitled` (106), `CMErrorNotAuthorized` (111). The probe records codes only and does **not** infer denial from them or from empty results | `CMError.h` |
| Swift 6 | Builds with `SWIFT_VERSION 6.0`, no concurrency warnings: `@MainActor @Observable` module, handler closures created in `nonisolated` factories and reduced to Sendable snapshots before hopping to the main actor. The Swift name of the pedometer stop is `stopUpdates()` | build log |
| Build | `** BUILD SUCCEEDED **` for the device; install and launch succeeded | 2026-11-13 |

## Unverified (header does not state it; the owner test or documentation must)

- **Purpose-string key.** `NSMotionUsageDescription` is the key I used (it is the key named in the project's own spec and, to my knowledge, Apple's documented one). It is **not present in any CoreMotion header** (grep over the SDK found nothing), so it is **not header-verified**. The owner test must confirm the system dialog shows the text; a missing/wrong key typically fails or crashes at first use.
- **Real history depth.** The headers say seven days. This is a documentation statement, not a measurement on this phone: the probe displays the oldest segment actually returned and the days with data; do not cite seven days as measured until the test.
- Dialog appearance and wording on iOS 26.6.1; whether denial yields `denied` for both activity and pedometer; whether the two statuses can ever differ.
- Whether the status is `notDetermined` until the first call on a fresh install, and how it behaves for "Ask next time"-like choices (not known to exist for Motion).
- Whether revocation while the app is suspended is seen on return (implemented: re-read on foreground).
- Whether a history query before authorization returns an error, an empty array, or blocks until the dialog is answered.
- Free personal team: no entitlement is declared; behaviour under that signing is untested for Motion.
- Battery cost of foreground live updates (BAT-01). Background delivery: **not built**.
- `CMErrorMotionActivityNotEntitled` conditions (cause unknown).

## Decisions made in this step (proposed)

- Three capabilities kept distinct in code and screens: activity history (intervals), live activity (intervals, start only; end = next start), pedometer (aggregates over a window; history = one window per calendar day, live = cumulative per run).
- Live collection is foreground only (stopped explicitly on leaving the active state, so the gap is the probe's own). No background mode, no entitlement; only the motion purpose string.
- Resume starts from now. The participant is asked separately whether to import the paused interval (default **no**); a yes queries activity and pedometer for that interval, clipped to the documented window, with `acquisition = backfill_after_pause`. Control events `backfill_chosen_yes/no`.
- A separate participant-initiated "import history" action, behind its own pre-prompt (the query itself raises the OS dialog), leaves the probe state unchanged (`off` stays `off`); records are labelled `history_import`.
- Duplicates (same start and label) are dropped and counted, so repeated imports or overlap with live data do not inflate counts; acquisition of the first copy is kept.
- Revocation observed => `blocked_by_os`; restored authorization => `paused`, never a silent restart (as D-045). A scope change is logged, not treated as revocation.
- Storage: memory only; no file, database, export or network. Control events carry state labels, counts and error codes only. The UI shows counts, windows, confidence distribution and missingness, no timeline.

## Owner test script (français)

1. Ouvrez Sensor Probe (bannière « VERSION D'ESSAI »). Touchez **Motion**. Notez : sonde `off`, système (activité / podomètre) probablement `not_determined`, et la ligne « Disponibilité ».
2. Touchez **Activer le mouvement (en direct)…**. L'explication apparaît **avant** toute fenêtre iOS. Essayez **Pas maintenant** : aucune fenêtre iOS, la sonde reste `off`.
3. Rouvrez l'explication, **Continuer vers la demande du système**. Fenêtre iOS « Mouvements et forme » : autorisez. Notez le texte affiché et les choix offerts.
4. Notez : sonde `on`, système `authorized` (activité et podomètre), « Collecte en direct : oui ».
5. Marchez environ 3 minutes, application ouverte et écran allumé, puis restez immobile 1 minute. Notez : nombre de segments en direct, confiance faible/moyenne/haute, pas cumulés en direct, séances.
6. **Pause**, marchez 1 minute (application ouverte), attendez, puis **Reprendre…** : choisissez d'abord la première option (sans importer, par défaut). Vérifiez que le compteur « rattrapage » reste 0. Refaites une pause de ~1 minute avec marche, puis **Reprendre** avec l'option d'import : notez les segments et fenêtres « rattrapage ».
7. Touchez **Importer l'historique conservé par iOS…** (lisez l'explication) et continuez. Notez, dans « Importations d'historique » : fenêtre demandée, **premier segment renvoyé** (c'est la profondeur réelle), nombre de segments, fenêtres de podomètre renvoyées et jours avec pas, codes d'erreur.
8. Réglages iOS > Confidentialité et sécurité > **Mouvements et forme** > Sensor Probe : désactivez. Revenez : attendu, système `denied`, sonde `blocked_by_os`, `revocation_observed` au journal. Notez si l'historique déjà en mémoire est resté. Réactivez : sonde `paused`, il faut reprendre vous-même.
9. Fermez de force, rouvrez : les enregistrements sont perdus (mémoire seulement), la sonde repart à `off`.
10. Importez l'historique de nouveau, puis **Supprimer les enregistrements…** : lisez la confirmation (elle rappelle que l'historique iOS n'est pas supprimé), confirmez : tout revient à 0, le journal garde `deleted_all`.

**À me rapporter** (comptes et fenêtres seulement, pas d'horodatages précis de votre vie) : choix et texte de la fenêtre iOS ; états système après chaque étape ; **profondeur réelle de l'historique** (nombre de jours renvoyés, pas l'heure exacte) ; nombres de segments par acquisition ; répartition de confiance ; codes d'erreur ; les valeurs affichées ont-elles correspondu à ce que vous avez fait ; tout texte confus ; batterie approximative.

## Owner run 1 (2026-11-13, partial, owner's report)

| Item | Observed |
|---|---|
| Authorization | Activity authorized, pedometer authorized, activity available. |
| Activity segments | About 8,394 in total: about 59 live and about 8,338 from the history import. The live count rose while the app was open. Confidence low, medium and high all present (distribution not reported). |
| Pedometer | History import returned 8 daily windows (consistent with today plus seven days; exact depth to confirm), about 5,000 steps reported after import. Live pedometer windows: 0 so far; 2 live sessions. |
| Backfill after pause | Counter at 0. Expected: it only fills after Pause, then "Reprendre et aussi importer la période en pause". Not yet exercised. |
| Not yet tested | Pause/resume with and without import, revocation in Settings, force-quit, delete, the oldest returned date, battery. |
