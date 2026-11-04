# Decision log

This log preserves the initial discovery decisions and subsequent changes. Superseded entries retain their original decision and rationale; the linked replacement records the new direction and its basis.

## Accepted and provisional decisions

| ID | Status | Decision | Rationale and consequence |
|---|---|---|---|
| D-001 | Accepted | Combine historical data imports with ongoing authorized iPhone collection. | Historical data creates immediate value; live collection supports continued learning and prediction. |
| D-002 | Superseded by [D-023](#review-2026-10-05) | Build a privacy-revelation layer and a personal-utility layer. | Every useful conclusion should show both what the data reveals and how the participant can use it. |
| D-003 | Accepted | The system is an inference platform, not a literal full digital twin. | Focus remains on observable evidence, relationships, predictions, and actions rather than simulating an entire person. |
| D-004 | Accepted | First users are privacy-aware students, technical friends, and other personally recruited consenting adults. | These users are reachable and can tolerate sideloading and experimental workflows. |
| D-005 | Accepted | V1 does not require App Store distribution. | The application can be sideloaded for controlled testing; iOS permissions and sandboxing still apply. |
| D-006 | Accepted | Begin with a free Apple ID and upgrade only when a tested requirement justifies a paid developer membership. | Avoid premature cost while preserving a path to additional capabilities and easier distribution. |
| D-007 | Superseded by [D-024](#review-2026-10-05) | The researcher receives identifiable raw participant data under explicit authorization. | Researcher access is necessary to discover and validate new inferences. General installation consent is insufficient. |
| D-008 | Accepted | Use participant-controlled encrypted batch export in V1; add continuous synchronization later. | Enables rich analysis without immediately operating high-risk continuous surveillance infrastructure. |
| D-009 | Superseded by [D-024](#review-2026-10-05) | Run the researcher workbench locally on a Mac. | Local processing supports sensitive data, Python analytics, and possible local models without cloud infrastructure. |
| D-010 | Provisional | Use a native Swift/SwiftUI iPhone collector and a local Python-oriented Mac analysis layer. | Native iOS APIs are needed for collection; Python has the strongest exploratory ML/data ecosystem. Exact frameworks remain open. |
| D-011 | Superseded by [D-024](#review-2026-10-05) | Build an inference factory with a researcher workbench and participant experience. | Researchers discover and validate patterns; participants receive reviewed predictions, explanations, notifications, and experiments. |
| D-012 | Accepted | Use statistical/ML methods for evidence and language models for classification, hypothesis generation, and explanation. | Fluent model output is not proof of correlation or causation. |
| D-013 | Deferred | Choose between local open-weight language models and external AI providers later. | The inference architecture will be provider-neutral; privacy, quality, cost, and hardware evidence will guide the choice. |
| D-014 | Superseded by [D-025](#review-2026-10-05) | Make the combined narrative the hero demonstration. | V1 should reveal what the data knows, predict Monday, and discover one useful cross-domain pattern. |
| D-015 | Accepted | Model data as a temporal operational ontology rather than a simple dashboard. | Objects, relationships, provenance, predictions, actions, and outcomes create the desired Gotham-like depth. |
| D-016 | Accepted | Maintain multiple strictly isolated participant workspaces. | Inference code may be reused, but participant records and ontology relationships do not mix. |
| D-017 | Accepted | Follow a broad, utility-first inference philosophy for consenting participants. | Sensitive topics are not automatically excluded, but evidence, confidence, false-positive cost, review, and participant correction remain required. |
| D-018 | Accepted | Do not anonymize initial participant data. | The small controlled research workflow needs identifiable longitudinal records; isolation, encryption, access, and deletion remain required. |
| D-019 | Accepted | Use mythological/scientific branding with provocative surveillance messaging. | The product should invite curiosity while making its consent-based operation immediately clear. |
| D-020 | Provisional | Keep Panoptes and Laplace as the two leading names. | Panoptes can name the all-seeing platform; Laplace can name its predictive inference engine. Final naming requires collision research. |
| D-021 | Accepted | Keep the implementation open source. | Inspectability supports trust, recruiting value, extensibility, and technical review. A license remains open. |
| D-022 | Accepted | Avoid copying Palantir Gotham's proprietary visual identity. | The project adopts ontology and operational-action concepts while creating an original implementation and brand. |

## Review 2026-10-05

**Basis:** the owner clarified that the core is a personal Foundry-like explorer: connect authorized personal data, expose what it can reveal, and support open-ended understanding. Self-operated and researcher-assisted use are equally central. The owner then authorized continuing with available information while deferring the Mac version commands. See [the review and reference checks](review-and-next-steps.md).

| ID | Status | Decision | Rationale and consequence |
|---|---|---|---|
| D-023 | Accepted | Make connected personal exploration and understanding the core value; retain privacy revelation and personal utility without requiring an action for every insight. | Replaces D-002's action-centered interpretation. Profiles, ads/offers, forecasts, recommendations, and experiments are possible applications, not the product definition. Show what available traces could reveal without claiming access to a company's internal model or assuming every observer sees all sources. |
| D-024 | Accepted | Support both self-operated and explicitly authorized researcher-assisted analysis in a local Mac workbench. | Replaces D-007, D-009, and D-011. The participant may operate their own workspace without sharing with a separate researcher. Researcher access to identifiable raw data still requires specific authorization; installation is not sharing consent. The local Mac direction, workspace isolation, batch transfer, and provisional Swift/Python choices are retained. |
| D-025 | Accepted | Define the first demonstration as connected personal exploration plus a reproducible analytical investigation; permit null or insufficient-evidence results. | Replaces D-014. A profile, positive association, Monday forecast, notification, or intervention is not compulsory. Forecasts remain optional benchmarks requiring prospective evaluation. A short collection pilot proves pipeline feasibility, not stable statistical findings. |
| D-026 | Provisional | Expand the Sensor Probe into a collection feasibility lab covering native signals, App Privacy Report import, one relevant account export, and a separately gated Screen Time spike. | Native sensors alone do not establish coverage of digital life. Start with a target of three useful categories across two domains, including digital-behavior or app-metadata data; revise explicitly if unsupported. Capability, authorization, records, granularity, and exportability must be tested separately. See [the probe protocol](collection-probe.md). |
| D-027 | Accepted | Continue platform-independent documentation and synthetic preparation now; leave deployment targets and native scaffolding gated on Mac preflight. | The owner will provide `sw_vers` and `xcodebuild -version` later. Reported phone: iPhone 15 Pro, iOS 26.6.1, located in Canada; Mac with Xcode available. These are reported configuration facts, not successful build or entitlement tests. |

Apple's documented membership and regional restrictions are recorded as evidence in the review, not as successful device tests. D-006 still governs any paid membership decision; none has been purchased or selected. Cryptographic isolation, export encryption, and their verification remain unimplemented design work, not guarantees established by this documentation update.

## Synthetic spike and inspiration research 2026-10-05

**Basis:** the owner authorized continuing the synthetic import spike and studying Foundry and existing malware/trackers for consent-compatible lessons. This does not change the existing prohibitions on hidden collection, credential capture, exploits, or permission bypasses. Research candidates are not approved collectors.

| ID | Status | Decision | Rationale and consequence |
|---|---|---|---|
| D-028 | Provisional | Use an isolated Python 3.10+ standard-library App Privacy Report inspector for synthetic feasibility tests only. | The [spike](../spikes/app-privacy-report.md) preserves source bytes, line provenance, interval ambiguity, and separate network aggregates without choosing production storage or an ontology schema. Its CLI reads only bundled fixtures. Synthetic tests do not establish real export compatibility, secure transfer, persistent idempotency, or participant isolation. Foundry/spyware inspiration is documented in [a separate capability review](inspirations-and-collection-patterns.md), not used to expand runtime collection permissions. |

**Implementation follow-up, 2026-10-05:** continued under D-028 with an opt-in synthetic coverage report, source-line/original-input provenance, direct byte comparison for duplicate artifacts, and UTC-boundary validation. The default reduced summary remains available; the detailed report intentionally includes timestamps and is not a de-identification guarantee. See the updated [run record](results/app-privacy-report-synthetic.md). This does not select a production report/event schema, add a collector, or relax the Mac and real-data gates; no existing decision is superseded.

## Deferred decisions

- Final product and engine names
- Open-source license
- Minimum iOS/macOS versions
- Paid Apple Developer membership
- Exact Screen Time capability and entitlement path
- iPhone local database and encryption scheme
- Export-package format and key exchange
- Mac UI/backend/database frameworks
- Graph database versus relational/event-backed ontology
- Local versus external language model
- Continuous synchronization architecture
- Cross-participant aggregate research
- Additional data-source priority after V1

## Decision-change process

When changing a material decision:

1. Add a new decision entry rather than silently rewriting history.
2. Mark the superseded decision and link the replacement.
3. Record the evidence or constraint that caused the change.
4. Update affected architecture, MVP, trust, and ontology documents.
