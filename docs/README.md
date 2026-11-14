# Panoptes documentation

This directory records product direction, decision history, and technical discovery.

Start with the product vision and [decision log](decisions.md). The [vision review and next steps](review-and-next-steps.md) records the clarification, dated capability references, and implementation sequence. Product changes are reconciled in D-023 through D-027; collection criteria remain provisional, and no device results have been established. Use the [collection feasibility protocol](collection-probe.md) for the next milestone.

## Working vocabulary

- **Panoptes:** provisional name for the complete personal intelligence platform.
- **Laplace:** provisional name for the prediction and inference engine.
- **Participant:** a consenting adult whose data is collected and analyzed; may operate their own workspace.
- **Self-operator:** the participant using the local workbench without sharing with a separate researcher.
- **Researcher:** a separately authorized operator who explores selected participant data for an agreed purpose.
- **Inference:** an evidence-backed conclusion derived from one or more observations.
- **Intervention:** a participant-approved action intended to test or use an inference.

## Documents

| Document | Purpose |
|---|---|
| [Vision review and next steps](review-and-next-steps.md) | Clarified intent, reconciliation status, test environment, and sourced iPhone constraints |
| [Collection feasibility protocol](collection-probe.md) | Native/import test cases, gates, and provisional exit criteria |
| [Transfer package design options](transfer-package-design.md) | Provisional encrypted batch-export options, threat model, and synthetic test plan |
| [Sensor Probe specification](sensor-probe-spec.md) | Provisional native probe contract: modules, participant text, authorization states, acceptance checklist |
| [Participant texts (French, provisional)](participant-text-fr.md) | Draft intro, per-source consent cards, deletion/withdrawal, researcher mode, permission strings (FR/EN); needs legal review (D-041) |
| [Explorer export spike](../spikes/explorer-export.md) | Maps parser-spike results to the explorer data contract, with a validator; fixture-derived dataset for the UI (D-040) |
| [Owner manual procedures](owner-manual-procedures.md) | Phone inventory, APR-01/ACC-01 export steps, and BAT-01 protocol the owner can run without a Mac |
| [Investigation catalogue](investigation-catalogue.md) | Provisional candidate investigations, sample units, null criteria, and first pilot picks |
| [Explorer UI concept](explorer-ui-concept.md) | Provisional ops-room interface concept, lenses, screens, and prototype plan |
| [Cinematic explorer prototype](../prototypes/explorer-cinematic/README.md) | Particle-corpus, bootstrap-fan, live-training, and provenance-loom lenses on synthetic data (D-039) |
| [Sensor Probe scaffold](../ios/SensorProbe/README.md) | Minimal SwiftUI app (ENV-01 only; requests nothing), XcodeGen project, build and signing steps (D-044) |
| [Local explorer server](../explorer/README.md) | Read-only loopback server that builds, validates and serves the synthetic workspaces to the explorer (D-042) |
| [Insight lenses](insight-lenses.md) | Shifts, observer Mirror and Context findings, contract 0.2 additions, six synthetic profiles, guardrails (D-043) |
| [Collection results template](templates/collection-probe-result.md) | Unfilled template for recording actual evidence; not a successful test report |
| [Synthetic privacy-report spike](../spikes/app-privacy-report.md) | Runnable local inspector, opt-in source-coverage report, limits, and test commands |
| [Synthetic inspection results](results/app-privacy-report-synthetic.md) | Actual synthetic test evidence, not device validation |
| [Inspirations and collection patterns](inspirations-and-collection-patterns.md) | Cited Foundry, analytics, and spyware lessons mapped to authorized alternatives |
| [Product vision](product-vision.md) | Problem, thesis, users, principles, and desired experience |
| [V1 and first experiment](mvp.md) | Initial scope, pilot workflow, acceptance criteria, and deferred work |
| [System architecture](architecture.md) | Conceptual components, data flow, platform feasibility, and trust boundaries |
| [Personal ontology](ontology.md) | Proposed object, relationship, event, evidence, and action model |
| [Laplace inference engine](inference-engine.md) | Discovery, validation, prediction, explanation, and intervention lifecycle |
| [Trust and data governance](trust-and-data-governance.md) | Consent, identifiable data, isolation, access, deletion, and research integrity |
| [Branding](branding.md) | Panoptes/Laplace naming direction and provocative messaging strategy |
| [Decision log](decisions.md) | Accepted, provisional, and deferred decisions |

## Status language

- **Accepted:** explicitly selected during product discovery.
- **Provisional:** current working direction that may change after a technical spike.
- **Deferred:** intentionally not decided until evidence is available.
- **Open:** requires a future decision.
- **Proposed:** a recommendation under review, not yet an accepted implementation decision.
- **Superseded:** a historical decision retained with a link to its replacement.

## Documentation principles

1. Separate long-term vision from V1 commitments.
2. Record why a decision was made, not only what was selected.
3. Mark technical uncertainty rather than presenting assumptions as facts.
4. Preserve provenance for product requirements just as the product preserves provenance for data.
5. Update the decision log whenever a material product, architecture, or trust decision changes.
