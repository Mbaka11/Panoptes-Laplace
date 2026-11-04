# Inspirations and consent-compatible collection patterns

## Scope

Research checked on 2026-10-05 at the owner's request: learn from Palantir Foundry and documented tracker/spyware capabilities, then identify legitimate ways to serve the same personal-understanding goal. This is a capability/design comparison, not a malware implementation guide or a claim that participant consent removes operating-system restrictions.

No spyware, exploit, third-party tracker SDK, screen recorder, VPN, or background agent was installed or added. The only implemented spike is the [synthetic App Privacy Report inspector](../spikes/app-privacy-report.md).

**Main finding:** distinguish the question we want to answer from the access mechanism that made someone else's system possible. Some observable outcomes can be reproduced through an authorized source; others remain unavailable. Broader malware access is not an ordinary app capability with a consent checkbox added.

## 1. Foundry: borrow the structure of investigation

Foundry is useful as more than a visual-dashboard reference. Its documented tools combine objects and relationships with exploration, analysis, and provenance. These references are vendor descriptions of capabilities, not independent evidence of analytical accuracy. [F1-F3]

| Foundry concept | Documented behavior | Panoptes adaptation to consider |
|---|---|---|
| Object Explorer | Search/filter objects, inspect an Object View, compare sets, save explorations | Search personal observations and derived objects; filter a time window; inspect one source, activity, or place with its evidence |
| Quiver | Analyze object/time-series data, traverse links, parameterize views, inspect analysis dependencies | Save an investigation with its input selection, method/version, derived series, comparison, and limitations |
| Data Lineage | Show dataset dependencies, freshness, schemas, and generating code | Follow a finding back through features and transformations to the original export/record; show missing sources and stale inputs |
| Operational writeback | Quiver can write analytical decisions through ontology actions | Record participant corrections as versioned interpretations, not silent edits to original observations |

The most useful first interface is not necessarily a huge graph. A source/coverage panel, shared timeline, linked object details, and an evidence drawer can express these concepts. This is design inspiration, not a selected UI framework or permission to reproduce Palantir's proprietary visual identity.

Suggested investigation example, not an observed finding:

> Select a period, compare mobility/activity with available digital-life metadata, inspect a candidate pattern, and follow every contributing field back to its source and transformation.

Keep a distinction between a person's real-world relationship graph and the analysis dependency graph. Neither implies causal links merely because two records share a time window.

## 2. Why trackers and spyware can obtain data

The sources below describe different systems and different access conditions. Their capabilities are not interchangeable and historical findings do not prove access on the owner's current iPhone.

| Reference | Where its access comes from | Transferable lesson | Consent-compatible Panoptes path and limit |
|---|---|---|---|
| PostHog session replay / privacy controls [C1] | Instrumentation embedded in the app or website being observed | Events need source context; mask sensitive values at collection and make recording controllable | Instrument a participant-authorized surface we actually control, or an authorized browser page. Installing an SDK in Panoptes would not expose another native app's feed or taps. No SDK is selected here. |
| ActivityWatch [C2, C3] | Source-specific watchers on supported desktop/browser environments | Small source adapters, local storage, and a visible distinction between data sources | Use modular authorized collectors/importers. Desktop active-window/URL capabilities are not proof of equivalent global access on iOS. We are borrowing concepts, not installing its watchers. |
| SpyFone, as described in FTC allegations [M1] | Hidden monitoring; Android protection bypass and rooting for some capabilities | Rich central aggregation creates both misuse and breach risk; nominal access must not replace device-owner control | Collect only selected categories through legitimate OS APIs or owner-provided exports, with visible status, bounded sharing, and tested deletion. Do not reproduce stealth, root dependence, or credential collection. |
| Pegasus, as described in Citizen Lab's historical analysis [M2] | Exploitation of the endpoint and penetration of device security, followed by broad data access | A compromised endpoint can expose information far beyond what an ordinary sandboxed app sees | Use per-source APIs/exports or participant-selected material. Messages, credentials, and arbitrary other-app files do not become available to a normal collector by requesting general consent. No exploit path is pursued. |

The Citizen Lab report cited here concerns 2016-2018 observations. It is evidence of that investigated spyware model, not a current exploit assessment or a complete catalogue of every Pegasus version. The FTC source describes allegations and an enforcement action, not an API specification.

Three important distinctions:

1. **Own-app instrumentation:** an app can observe its own displayed interface and interaction events. That is why an app operator may know scroll positions or content impressions that an unrelated collector cannot see.
2. **Authorized system/account access:** permissions, managed entitlements, and participant exports expose specified categories and granularity. They do not establish unrestricted device access. [A1]
3. **Compromised endpoint:** an attacker may defeat boundaries that this project must retain. Consent is necessary for Panoptes, but it neither creates those privileges nor makes reproducing the compromise part of this project.

Visible content is also not proof of attention, reading, or intent. Even when a legitimate source supplies a scroll or view event, the interpretation remains separate from the observation.

## 3. Candidate collection paths, not new commitments

### A. Native APIs and participant-owned exports — retain as the baseline

Location, Motion, HealthKit, EventKit, App Privacy Report, and relevant account exports remain the collection lab's baseline. App Privacy Report supplies access/domain metadata, not decrypted traffic or viewed-content histories. Screen Time must retain its entitlement, authorization, and development/customer regional distinctions. [A2; existing review]

The inspector now tests how to preserve the privacy-report subset's meaning. It does not establish that the owner's device currently exports the same structure.

### B. Explicitly instrumented surfaces — useful but incomplete

A purpose-built participant-operated reader or permissioned Safari page could produce richer interaction metadata. The engineering lesson from analytics SDKs is to record a small, explainable event vocabulary and exclude secrets/third-party content at the source. [C1]

This would observe that surface, not replicate Instagram, TikTok, or every native app. Requiring the participant to change how they consume content also changes the behavior being measured. Evaluate that trade-off before selecting such a feature.

### C. Participant-selected screen material — investigate only as a separate option

A deliberately shared screenshot or short, user-started screen-capture session may expose some visible context that an account export omits. Apple's ReplayKit documentation describes user-facing recording/broadcast facilities, and its system broadcast picker lets the user choose a provider. These are visible capture paths, not silent collection. ReplayKit also documents content limitations. [A3, A4]

This is **not implemented or approved as the next collector**. Before any trial, decide:

- the narrow purpose, session duration, visible start/stop controls, and storage/retention;
- how the participant selects/reviews material and excludes messages, credentials, other people's information, and unrelated screens;
- what happens when content is unavailable, protected, or redaction/OCR fails;
- whether raw frames are needed at all, and how derived text is corrected and deleted;
- how to distinguish a visible item from verified viewing, attention, tapping, or scroll position.

A screen recording is not a reliable global touch-event feed. Do not promise complete capture, automatic perfect redaction, passive all-day recording, or clinical/behavioral conclusions from OCR alone. The documentation reviewed includes a ReplayKit picker deprecation at iOS 27.0; check the actual SDK and reported 26.6.1 device rather than assuming a newer replacement API is available there. [A4]

### D. Network observation — not a universal content sensor

Start with participant-exported domain metadata. A VPN or packet tunnel is not a generic way to see screen content, touch interactions, or decrypt other applications' protected traffic. Apple documents specific supported and unsupported uses for packet tunnel providers; do not design the collector around unsupported interception patterns. [A5]

A network-extension experiment would need a separate capability, purpose, security, and deployment review. This work does not install a VPN, interception certificate, proxy, or monitoring profile. Packet metadata is not equivalent to a platform's internal behavioral model.

### E. Account history and explicit contextual input — broaden understanding

Participant-authorized histories and transaction exports can provide context the phone cannot expose centrally. Preserve export scope and source semantics. A manual note is a participant statement, not automatically an observed fact. Prefer one actual useful service export over a promise of universal integrations.

## 4. Recommended product implications

These are recommendations to evaluate after the probe, not silently adopted architecture decisions:

- Use a **coverage map**: direct observation, provider export, manual input, derived interpretation, and unavailable information.
- Make **lineage and freshness** visible before elaborate dashboard decoration.
- Keep **source adapters small**, with source-specific quality and granularity rules.
- Save **investigations** as explicit input selections and reproducible transformations; preserve null and contradictory results.
- Reproduce useful **outcomes through legitimate access paths**, not the spyware mechanisms that defeated the device's protections.
- Keep optional screen capture and network extensions outside the current milestone until their value, access limits, and privacy trade-offs justify a separate decision.

For the current iPhone-first project, the next practical evidence is still actual export/source coverage. Studying malware does not remove that dependency or justify advertising device-wide scrolling access.

## References

Checked 2026-10-05. Historical malware sources are labeled as such; no binaries or exploit code were acquired or executed.

- **F1:** Palantir, [Object Explorer overview](https://www.palantir.com/docs/foundry/object-explorer/overview/).
- **F2:** Palantir, [Quiver overview](https://www.palantir.com/docs/foundry/quiver/overview/).
- **F3:** Palantir, [Data Lineage overview](https://www.palantir.com/docs/foundry/data-lineage/overview/).
- **C1:** PostHog, [Privacy controls](https://posthog.com/docs/session-replay/privacy.md). Source-side masking and recording scope; commercial SDK reference, not an adopted dependency.
- **C2:** ActivityWatch, [Watchers](https://docs.activitywatch.net/en/latest/watchers.html). Desktop/browser source distinctions.
- **C3:** ActivityWatch, [Privacy policy](https://docs.activitywatch.net/en/latest/privacy.html). Local activity-data handling and the separate release-check caveat.
- **M1:** FTC, [SpyFone enforcement announcement](https://www.ftc.gov/news-events/news/press-releases/2021/09/ftc-bans-spyfone-ceo-surveillance-business-orders-company-delete-all-secretly-stolen-data), September 2021. Historical allegations concerning covert access, rooting for some functions, and inadequate data protection.
- **M2:** Citizen Lab, [HIDE AND SEEK](https://citizenlab.ca/research/hide-and-seek-tracking-nso-groups-pegasus-spyware-to-operations-in-45-countries/), September 2018. Historical investigation of spyware operators and endpoint-compromise capabilities.
- **A1:** Apple, [Runtime process security](https://support.apple.com/en-gb/guide/security/sec15bfe098e/web); also see [the existing dated collection review](review-and-next-steps.md#4-reference-checked-collection-boundaries).
- **A2:** Apple, [Inspecting app activity data](https://developer.apple.com/documentation/network/inspecting-app-activity-data).
- **A3:** Apple, [ReplayKit](https://developer.apple.com/documentation/replaykit). Public [DocC representation](https://developer.apple.com/tutorials/data/documentation/replaykit.json) used to read the JavaScript-rendered documentation.
- **A4:** Apple, [RPSystemBroadcastPickerView](https://developer.apple.com/documentation/replaykit/rpsystembroadcastpickerview). User-facing picker and version metadata checked through [DocC](https://developer.apple.com/tutorials/data/documentation/replaykit/rpsystembroadcastpickerview.json).
- **A5:** Apple, [TN3120: Expected use cases for Network Extension packet tunnel providers](https://developer.apple.com/documentation/technotes/tn3120-expected-use-cases-for-network-extension-packet-tunnel-providers).
