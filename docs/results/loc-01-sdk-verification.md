# LOC-01: SDK verification and first Location module

**Date:** 2026-11-13. **Scope:** the foreground, when-in-use-only Location module in [`ios/SensorProbe`](../../ios/SensorProbe/README.md). **TEST BUILD, not cleared for real data** (gate R). This record covers SDK facts and the build; the on-device behaviour is **not yet tested** (owner test below).

## Verified against the installed SDK (iPhoneOS 27.2, Xcode 27.2)

Headers under `…/iPhoneOS27.2.sdk/System/Library/Frameworks/CoreLocation.framework/Headers/` (and `_LocationEssentials.framework/Headers/CLLocationEssentials.h` for `CLLocation`, because `CLLocation.h` is now a one-line import).

| Item | Result | Where |
|---|---|---|
| When-in-use purpose key | `NSLocationWhenInUseUsageDescription`; `requestWhenInUseAuthorization` does nothing if it is missing | `CLLocationManager.h` (doc of `requestWhenInUseAuthorization`) |
| Always purpose key | `NSLocationAlwaysAndWhenInUseUsageDescription`, required together with the when-in-use key. **Not declared** (not needed for this step) | `CLLocationManager.h` (doc of `requestAlwaysAuthorization`) |
| Authorization enum | `CLAuthorizationStatus`: `notDetermined`, `restricted`, `denied`, `authorizedAlways`, `authorizedWhenInUse` (+ deprecated `authorized`). `denied` also covers "location services disabled in Settings", so the probe cannot tell these apart from this value | `CLLocationManager.h` |
| Reading it | instance property `authorizationStatus` (iOS 14+); class method is deprecated | `CLLocationManager.h` |
| Accuracy scope | `accuracyAuthorization`: `fullAccuracy` / `reducedAccuracy` (iOS 14+) | `CLLocationManager.h` |
| Change callback | `locationManagerDidChangeAuthorization(_:)` (iOS 14+), fired for status and accuracy changes | `CLLocationManagerDelegate.h` |
| Background | `allowsBackgroundLocationUpdates` requires `UIBackgroundModes` to include `location`; not set, not declared | `CLLocationManager.h` |
| Newer APIs | `CLLocationUpdate.liveUpdates` family (`CLLocationUpdater.h`, iOS 17+; `CLUpdate` flags such as `authorizationDenied`, `stationary`, `insufficientlyInUse` iOS 18+) and `CLServiceSession` (iOS 18+) exist. **Not used here**: the delegate API is enough and simpler to state; evaluating them is a BAT-01 question | `CLLocationUpdater.h`, `CLServiceSession.h` |
| Per-sample fields | `timestamp`, `horizontalAccuracy`, `speed`/`course` (negative = invalid), `speedAccuracy`, `courseAccuracy`, `sourceInformation.isSimulatedBySoftware` / `isProducedByAccessory` (iOS 15+) | `CLLocationEssentials.h` |
| Swift 6 | Builds with `SWIFT_VERSION 6.0` and no concurrency warnings: `@MainActor @Observable` class, delegate callbacks `nonisolated` extracting Sendable values before hopping to the main actor | build log |
| Build | `** BUILD SUCCEEDED **` for the device; install and launch succeeded (`Launched application with dev.panoptes.sensorprobe bundle identifier.`) | 2026-11-13 |

## Still unverified (need the phone or documentation)

- The exact on-device prompt appearance and button wording on iOS 26.6.1 (the "Allow Once" / "Allow While Using" choices and the precise-location toggle are system UI, not read from headers).
- That the status moves to `.denied` (not another value) when the participant picks "Don't Allow", and what "Allow Once" reports after the app is closed. Observed value is recorded by the probe; the owner confirms.
- That revocation in Settings while the app is suspended is detected on return to foreground (implemented: re-read on every active scene phase, plus the delegate callback).
- Whether `locationManagerDidChangeAuthorization` fires while the app is open and Settings changes arrive (not possible while foreground except via Control Center toggles).
- Behaviour with free-personal-team signing (no entitlement is needed for when-in-use).
- Real sample rate, accuracy distribution and battery cost (BAT-01).
- Behaviour of `sourceInformation` flags on a real device (stored as nullable).
- Background and always modes: **not built**, not verified.

## Decisions made in this step (proposed, see the report)

- Delegate-based `CLLocationManager` standard updates; `desiredAccuracy = nearest ten meters`, no distance filter, at most one stored sample per 5 s. These are predeclared and shown on screen (spec 4.1: recorded, not hidden).
- When-in-use only. The spec makes "always" a **separate optional step** after results from the lower level (spec 4.1), so it is not requested and `UIBackgroundModes` is not declared.
- Collection is foreground only: updates are stopped explicitly when the app leaves the active state, so the gap is the probe's own, visible, and counted as a gap (never as stillness).
- Resume starts from now. Location has no OS-held history, so there is no backfill question.
- Revocation observed => `blocked_by_os` with a `revocation_observed` control event (time observed, not time revoked). If authorization returns in Settings while blocked, the probe goes to `paused` and waits for a deliberate resume (it never restarts silently).
- A scope change (for example full to reduced accuracy) is logged as `authorization_change_observed`, not as revocation.
- The purpose string is the French draft from `participant-text-fr.md`, but its last sentence was changed from "jusqu'à ce que vous les exportiez" to a statement that matches this build (in memory, no export), per the spec rule that purpose strings must not promise more than the probe does.
- Storage: **memory only**; lost on exit. No file, database, export, network or logging of coordinates. Control events never contain values. The UI shows counts, first/latest timestamps and gaps, not a map or coordinates.

## Owner test script (français)

1. Ouvrez Sensor Probe. Bannière « VERSION D'ESSAI » visible. Touchez **Location**. Notez : état de la sonde `off`, état du système `not_determined`.
2. Touchez **Activer la localisation…**. L'écran d'explication s'affiche **avant** toute fenêtre iOS. Essayez d'abord **Pas maintenant** : aucune fenêtre iOS ne doit apparaître, la sonde reste `off`.
3. Rouvrez l'explication, touchez **Continuer vers la demande du système**. Fenêtre iOS : choisissez **Autoriser lorsque l'app est active** (ou, pour un second passage, autre choix ; notez lequel).
4. Notez : sonde `on`, système `authorized (when in use)` + précision `full`/`reduced`, « Collecte en cours : oui ». Les compteurs montent.
5. Marchez environ 5 minutes en gardant l'application ouverte et l'écran allumé (pas en conduisant). Notez : nombre de relevés, premier/dernier, trous.
6. Touchez **Pause**. Le nombre ne doit plus monter. Attendez 30 s. Touchez **Reprendre** : la collecte repart de maintenant.
7. Mettez l'application en arrière-plan 1 minute (écran verrouillé), revenez : notez les trous et le journal (aucun relevé hors premier plan attendu).
8. Réglages iOS > Confidentialité et sécurité > Service de localisation > Sensor Probe : choisissez **Jamais**. Revenez dans l'application : attendu, système `denied`, sonde `blocked_by_os`, événement `revocation_observed` au journal. Remettez ensuite « Lorsque l'app est active » et vérifiez : sonde `paused`, il faut reprendre vous-même.
9. Fermez de force l'application, rouvrez : les relevés sont perdus (mémoire seulement) ; l'état de la sonde repart à `off`.
10. Retournez à l'étape 4 brièvement, puis **Supprimer les relevés…** : lisez la confirmation, confirmez ; le nombre revient à 0 et le journal garde `deleted_all`.

**À me rapporter** (sans coordonnées, sans capture de position) : la fenêtre iOS (choix offerts), l'état système après chaque étape, le nombre de relevés après 5 min, le plus long trou, si les valeurs ont correspondu à ce qui est affiché, tout texte jugé confus, et la batterie (pourcentage début/fin approximatif).
