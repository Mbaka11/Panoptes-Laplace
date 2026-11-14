# ENV-01: first signed build run on the owner's iPhone

**Date:** 2026-11-13. **Scope:** the scaffold in [`ios/SensorProbe`](../../ios/SensorProbe/README.md) (D-044). It requests no permission and collects nothing, so this result says nothing about any data source.

| Item | Result |
|---|---|
| Mac | macOS 27.2 (26B123), MacBook Air M4, Xcode 27.2 (27B52), Swift 6.4.2, iOS SDK 27.2 |
| Phone | iPhone16,1 (iPhone 15 Pro), iOS 26.6.1 (23G83), wired USB, paired from the Mac, Developer Mode enabled by the owner |
| Signing mode | Xcode automatic signing, **free personal team** (Apple Development identity, team provisioning profile created by Xcode). No paid Developer Program membership. Not an App Store or TestFlight build. |
| Build | `xcodebuild … -sdk iphoneos -destination id=<device> -allowProvisioningUpdates build`: succeeded on the second attempt. The first attempt failed while the login keychain was awaiting the owner's approval for the new signing key. |
| Install | `xcrun devicectl device install app`: succeeded. |
| First launch | Refused until the owner trusted the developer profile on the phone (Settings → General → VPN & Device Management). After trust, `devicectl device process launch` succeeded. |
| What the owner observed on screen | TEST BUILD banner; model `iPhone16,1`; iOS `26.6.1`; version `0.0.1`; running on "device"; five sources, each "probe state: off, OS state: not requested"; **no permission dialog**. |
| Capabilities and entitlements | None declared. Verification of any capability (Location, Motion, Health, Calendar, Screen Time) is still open. |

## Limits

- Observations of the screen are the owner's report; no screenshot is stored.
- A free personal team signs with short validity and restricted capabilities. The re-signing interval and which capabilities it allows were **not** tested.
- The first-launch trust step is a manual owner action and cannot be skipped.
- This does not verify the Screen Time export (SCT-02), which has its own entitlement and region gate.

## Next

Add LOC-01 (Location) as the first module: verify the permission keys and authorization states against the installed SDK, show the pre-prompt text before any system dialog, and implement pause, resume and delete.
