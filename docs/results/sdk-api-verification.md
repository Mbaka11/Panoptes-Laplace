# SDK declaration check (Xcode 27.2, iOS SDK 27.2)

**Date:** 2026-11-11. **Scope:** whether names used in the Sensor Probe specification exist in the installed SDK headers, Swift interfaces and Xcode build specifications. **This is a declaration check only.** It does not show that any API works on the device, that an entitlement can be provisioned, or that a participant will see a given prompt. No device was connected.

Environment: macOS 27.2, Xcode 27.2 (27B52), Swift 6.4.2, `iPhoneOS27.2.sdk`.

## Results

| Claim in the spec | Finding in the SDK |
|---|---|
| EventKit read access uses `requestFullAccessToEvents` / `requestFullAccessToReminders` | Declared, `ios(17.0)`. `requestAccessToEntityType:` is deprecated since 17.0. |
| Info.plist keys `NSCalendarsFullAccessUsageDescription`, `NSRemindersFullAccessUsageDescription` (older: `NSCalendarsUsageDescription`, `NSRemindersUsageDescription`) | All four are listed in Xcode's build specification (`CoreBuildSystem.xcspec`), as is `NSCalendarsWriteOnlyAccessUsageDescription`. |
| `NSMotionUsageDescription`, `NSLocationWhenInUseUsageDescription`, `NSLocationAlwaysAndWhenInUseUsageDescription`, `NSHealthShareUsageDescription`, `NSHealthUpdateUsageDescription` | All listed in the build specification. |
| Core Motion activity: `isActivityAvailable`, `authorizationStatus`, `queryActivityStarting…` | Declared in `CMMotionActivityManager.h`. `CMPedometer.isStepCountingAvailable` also declared. |
| Core Location: `allowsBackgroundLocationUpdates`, `showsBackgroundLocationIndicator`, `accuracyAuthorization` | Declared (`ios(9.0)`, `ios(11.0)`, `ios(14.0)`). |
| HealthKit read authorization is not exposed (`unknown_not_exposed`) | `authorizationStatusForType:` and `getRequestStatusForAuthorizationToShareTypes:…` are declared; the header only describes sharing status. Whether read denial is observable is a runtime question and stays `unknown_not_exposed` as specified. |
| `DeviceActivityData.activityData(filteredBy:using:)` and `FamilyActivityData` need iOS 26.4 | Both `@available(iOS 26.4, *)`, unavailable on macOS, tvOS, visionOS, watchOS. `approvedWithDataAccess` is declared in FamilyControls. Matches reference checks A4 to A6. |

## Not established here

- Whether the free development account can provision Family Controls or the App and Website Usage entitlement.
- Whether `NSHealthUpdateUsageDescription` is required for a read-only build (spec: record as a finding).
- Whether the Screen Time export works at all in Canada (A5: development testing only).
- Whether a deployment target below the SDK version (iOS 26.6.1 on the phone) builds and installs. Needs the device.
- Any runtime behavior: authorization prompts, background delivery, record counts, battery.
