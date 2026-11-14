# Sensor Probe (native iPhone collector), scaffold stage

**Status: PROVISIONAL (D-044).** A minimal SwiftUI app that implements only the environment report (ENV-01) of [the specification](../../docs/sensor-probe-spec.md). It requests no permission, declares no capability or entitlement, and collects nothing. Every source is shown as `off` with the OS state "not requested". It is a *TEST BUILD, not cleared for real data* (real-data gate, D-031, D-032, D-040).

Verified 2026-11-13 on macOS 27.2, Xcode 27.2, iOS SDK 27.2: it compiles, signs with a free personal team, installs and runs on the owner's iPhone 15 Pro (iOS 26.6.1). See [the ENV-01 record](../../docs/results/env-01-device-run.md).

## Generate and build

`project.yml` is the source of truth (XcodeGen 2.46.0); the `.xcodeproj` is generated and git-ignored.

```bash
cd ios/SensorProbe
xcodegen generate
xcodebuild -project SensorProbe.xcodeproj -scheme SensorProbe -sdk iphoneos \
  -destination 'generic/platform=iOS' CODE_SIGNING_ALLOWED=NO build
```

## Signing on a new machine (manual, owner only)

1. Xcode → Settings → Accounts: sign in with the Apple Account. This is the owner's credential; do not paste it anywhere else.
2. Open `SensorProbe.xcodeproj`, select the SensorProbe target → Signing & Capabilities, choose the personal team.
3. Copy `Config/Local.xcconfig.example` to `Config/Local.xcconfig` (git-ignored) and set a bundle identifier unique to the team and your team id. They survive `xcodegen generate`. Keep the team id and any provisioning material out of Git.
4. Choose the connected iPhone as the run destination and run. On first launch the phone may ask to trust the developer profile under Settings → General → VPN & Device Management.

A free personal team signs with a short validity and cannot use every capability. Record the actual signing mode in ENV-01 rather than calling it "sideloaded".

## Next modules

Each module (Location, Motion, Health, Calendar, then Screen Time as a separate gate) is added by its own change: purpose strings and capabilities verified against the installed SDK, the pre-prompt text from [the French participant texts](../../docs/participant-text-fr.md), the pause/resume/delete controls, and a test record.
