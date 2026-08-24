# Panoptes project context

## Start here

Read these before making material product or architecture changes:

1. `docs/README.md`
2. `docs/product-vision.md`
3. `docs/decisions.md`
4. The topic-specific document relevant to the task

Treat `docs/decisions.md` as the decision record. Do not silently reverse an accepted decision; document the replacement and why it changed.

## Product in one paragraph

Panoptes is an open-source, consent-based personal intelligence research project. It combines historical account exports with ongoing authorized iPhone data, organizes observations into a temporal operational ontology, reveals what the data can infer about a participant, and returns useful predictions, notifications, and personal experiments. Panoptes is the provisional platform name; Laplace is the provisional inference-engine name.

## Accepted direction

- Serve both privacy revelation and personal utility.
- Build an ontology with objects, relationships, time, provenance, evidence, predictions, actions, and outcomes—not a simple dashboard.
- Use a native Swift/SwiftUI iPhone collector and a local Mac research workbench; Python is the provisional analysis direction.
- Keep identifiable participant workspaces strictly isolated.
- Use participant-controlled encrypted batch exports in V1; continuous synchronization comes later.
- Let statistical/ML methods establish evidence. LLMs may classify, suggest hypotheses, and explain, but model prose is not proof.
- Keep local versus external LLM selection deferred and provider-neutral.
- Sideload for early testing; App Store deployment is not required.
- Begin with a free Apple development account and pay only when a tested capability requires it.
- Keep Panoptes/Laplace as working names. Logo work is deferred.

## Immediate next milestone: Sensor Probe

Do not start with the full ontology UI or ML engine. First prove what the target iPhone can collect.

Build a minimal native iOS Sensor Probe that tests:

1. Core Location, including background behavior and battery impact
2. Core Motion and historical activity
3. HealthKit sleep/activity
4. EventKit calendar/reminders
5. Screen Time through Family Controls/Device Activity, as a separate feasibility spike

For every capability, report support, authorization state, record count, latest timestamp, and export success. Normalize samples into a minimal source-aware JSON event format and export through a participant-initiated share flow.

Before scaffolding against a deployment target, collect on the Mac:

```bash
sw_vers
xcodebuild -version
```

Also record the physical iPhone model and iOS version. The previous Pi session ran on Windows and could not compile or validate Xcode projects.

## V1 hero experiment

With a fully informed adult participant:

1. Import available historical data.
2. Collect roughly 14 days of authorized live data.
3. Build an evidence-backed personal ontology.
4. Reveal what the data appears to know.
5. Lock and timestamp a Monday forecast before Monday.
6. Discover at least one measured cross-domain association.
7. Send a reviewed notification or proposed experiment.
8. Compare predictions and outcomes with reality.

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
- Do not copy Palantir Gotham's proprietary visual identity; borrow only general ontology-centered operational concepts.
- Run available builds, tests, and validation before committing. If the current machine cannot run an Apple build, state that clearly and leave exact Mac verification commands.
