# Panoptes project context

## Start here

Read these before making material product or architecture changes:

1. `docs/README.md`
2. `docs/product-vision.md`
3. `docs/decisions.md`
4. `docs/review-and-next-steps.md`
5. The topic-specific document relevant to the task; collection work starts with `docs/collection-probe.md`

Treat `docs/decisions.md` as the decision record. Do not silently reverse an accepted decision; document the replacement and why it changed.

## Product in one paragraph

Panoptes Laplace is an open-source, consent-based personal intelligence research project. It combines historical exports with authorized iPhone data in an explorable temporal ontology, revealing what those traces can say about a person's life. Think personal Foundry-like workbench: connected evidence and open-ended understanding, not a compulsory profile, ad-analysis, health, or prediction demo. Understanding is itself useful; forecasts, notifications, and experiments are optional extensions. Panoptes is the working platform name; Laplace is the working inference-engine name.

## Accepted direction

- Serve both privacy revelation and personal understanding; not every finding needs an action.
- Support self-operated and explicitly authorized researcher-assisted use. A separate researcher is not required for self-use.
- Build a dashboard backed by connected objects, relationships, time, provenance, and evidence—not isolated charts. Predictions, actions, and outcomes remain supported concepts, not mandatory first-build features.
- Retain the native Swift/SwiftUI iPhone collector and local Mac workbench direction; Python and exact frameworks remain provisional.
- Keep identifiable participant workspaces strictly isolated.
- Use participant-controlled encrypted batch exports in V1; continuous synchronization comes later.
- Let statistical/ML methods establish evidence. LLMs may classify, suggest hypotheses, and explain, but model prose is not proof.
- Keep local versus external LLM selection deferred and provider-neutral.
- Sideload for early testing; App Store deployment is not required.
- Begin with a free Apple development account and pay only when a tested capability requires it.
- Keep Panoptes/Laplace as working names. Logo work is deferred.

## Immediate next milestone: Collection feasibility lab

Follow `docs/collection-probe.md`. Do not start with the full ontology UI or ML engine. First prove useful collection coverage, extending the Sensor Probe with digital-life imports:

1. Core Location, including background behavior and battery impact
2. Core Motion and available historical activity
3. HealthKit activity and any sleep/heart-rate records actually available from authorized producers
4. EventKit calendar/reminders
5. App Privacy Report export/import and one relevant participant-owned account export
6. Screen Time through Family Controls/Device Activity, as a separately gated spike

For every capability, record support, provisioning, authorization where observable, record count, latest timestamp, granularity, missingness, and export success. Do not infer HealthKit read denial from empty results. Keep interval and aggregate records distinct from individual events. Before real-data transfer, establish protected storage, encrypted transfer, key handling, and deletion of test copies; synthetic parser work can precede those choices.

The provisional explorer target is three useful categories across at least two domains, including digital-behavior or app-metadata data. This is not a reason to fabricate access to native-app scrolling, viewed content, or company profiles. Explicitly revise the slice if coverage falls short.

Before scaffolding against a deployment target, collect on the Mac:

```bash
sw_vers
xcodebuild -version
```

The owner reports an iPhone 15 Pro on iOS 26.6.1 in Canada and a Mac with Xcode. Exact Mac outputs are pending; the owner explicitly authorized continuing platform-independent work while deferring them. Do not select a deployment target or scaffold a native project until that preflight is available. Windows can support documentation and synthetic preparation, not an Xcode validation claim.

Apple's newer activity-data export documents regional distinctions between development testing and customer use. A development success in Canada would not prove customer eligibility. Verify membership and entitlements separately; do not buy membership or promise universal Screen Time export. See the dated reference checks in `docs/review-and-next-steps.md`.

## Current executable preparation

The isolated Python 3.10+ standard-library spike in `spikes/app_privacy_report.py` has synthetic tests. Run from the repository root:

```bash
python -m unittest discover -s tests -v
python -m spikes.app_privacy_report --demo
python -m spikes.app_privacy_report --demo --coverage
```

The CLI only reads bundled fake fixtures. Its opt-in coverage report includes source timestamps and line provenance while leaving device support, export success, full collection windows, and missing periods unverified/unknown; neither output is an anonymization guarantee. It does not implement native collection, production import, encrypted transfer, persistence, or workspace isolation. Read `spikes/app-privacy-report.md` and `docs/results/app-privacy-report-synthetic.md` before extending it. Do not turn its provisional record structures into a production schema without a separate decision.

The inspiration research in `docs/inspirations-and-collection-patterns.md` does not authorize implementing exploits, stealth, credential capture, screen recording, or network interception. Optional capture approaches require a separate scoped decision and the existing trust gates.

## V1 first demonstration

Start with the owner's self-operated workspace, then extend to authorized researchers and other consenting adults after controls are tested:

1. Establish actual source coverage, quality, and protected transfer.
2. Connect available historical imports and live observations.
3. Explore a small ontology by time, object, relationship, and source.
4. Run one reproducible investigation with evidence and uncertainty.
5. Let the participant inspect, correct, export, and delete data and derived findings.
6. Test isolation with separate synthetic workspaces before external-participant work.

A positive association, profile, Monday forecast, notification, or intervention is not compulsory (D-023 through D-025). A short collection trial validates the pipeline, not statistical significance. Forecasts, if later selected, require baseline scoring and a verifiable pre-outcome lock, not a bare hash treated as proof of time.

## Non-negotiable engineering boundaries

- No hidden collection, permission bypassing, sandbox escape, credential capture, global keylogging, or analysis of nonparticipants.
- Sideloading does not remove iOS permission or sandbox restrictions.
- Preserve the distinction between observation, normalized event, hypothesis, inference, and prediction.
- Every published inference must preserve source provenance, method/version, evidence, confidence, and participant correction.
- Frame observational correlations as correlations, not causation.
- Keep raw participant exports, generated datasets, signing credentials, API keys, and provider secrets out of Git.
- Use synthetic fixtures and demonstration data in the repository.
- Participants must be able to understand collection, pause it, initiate sharing, correct conclusions, and delete data.

## Working style

- Prefer small feasibility spikes before committing to frameworks or schemas.
- Keep V1 separate from the long-term vision.
- Mark uncertainty explicitly in documentation.
- Update affected docs and `docs/decisions.md` after material decisions.
- Do not copy Palantir Foundry/Gotham's proprietary visual identity; borrow only general ontology-centered analytical and operational concepts.
- Run available builds, tests, and validation before committing. If the current machine cannot run an Apple build, state that clearly and leave exact Mac verification commands.
