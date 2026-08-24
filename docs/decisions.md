# Decision log

This log records decisions made during initial product discovery. Dates reflect when the documentation baseline was created; the conversation established the decisions immediately beforehand.

## Accepted and provisional decisions

| ID | Status | Decision | Rationale and consequence |
|---|---|---|---|
| D-001 | Accepted | Combine historical data imports with ongoing authorized iPhone collection. | Historical data creates immediate value; live collection supports continued learning and prediction. |
| D-002 | Accepted | Build a privacy-revelation layer and a personal-utility layer. | Every useful conclusion should show both what the data reveals and how the participant can use it. |
| D-003 | Accepted | The system is an inference platform, not a literal full digital twin. | Focus remains on observable evidence, relationships, predictions, and actions rather than simulating an entire person. |
| D-004 | Accepted | First users are privacy-aware students, technical friends, and other personally recruited consenting adults. | These users are reachable and can tolerate sideloading and experimental workflows. |
| D-005 | Accepted | V1 does not require App Store distribution. | The application can be sideloaded for controlled testing; iOS permissions and sandboxing still apply. |
| D-006 | Accepted | Begin with a free Apple ID and upgrade only when a tested requirement justifies a paid developer membership. | Avoid premature cost while preserving a path to additional capabilities and easier distribution. |
| D-007 | Accepted | The researcher receives identifiable raw participant data under explicit authorization. | Researcher access is necessary to discover and validate new inferences. General installation consent is insufficient. |
| D-008 | Accepted | Use participant-controlled encrypted batch export in V1; add continuous synchronization later. | Enables rich analysis without immediately operating high-risk continuous surveillance infrastructure. |
| D-009 | Accepted | Run the researcher workbench locally on a Mac. | Local processing supports sensitive data, Python analytics, and possible local models without cloud infrastructure. |
| D-010 | Provisional | Use a native Swift/SwiftUI iPhone collector and a local Python-oriented Mac analysis layer. | Native iOS APIs are needed for collection; Python has the strongest exploratory ML/data ecosystem. Exact frameworks remain open. |
| D-011 | Accepted | Build an inference factory with a researcher workbench and participant experience. | Researchers discover and validate patterns; participants receive reviewed predictions, explanations, notifications, and experiments. |
| D-012 | Accepted | Use statistical/ML methods for evidence and language models for classification, hypothesis generation, and explanation. | Fluent model output is not proof of correlation or causation. |
| D-013 | Deferred | Choose between local open-weight language models and external AI providers later. | The inference architecture will be provider-neutral; privacy, quality, cost, and hardware evidence will guide the choice. |
| D-014 | Accepted | Make the combined narrative the hero demonstration. | V1 should reveal what the data knows, predict Monday, and discover one useful cross-domain pattern. |
| D-015 | Accepted | Model data as a temporal operational ontology rather than a simple dashboard. | Objects, relationships, provenance, predictions, actions, and outcomes create the desired Gotham-like depth. |
| D-016 | Accepted | Maintain multiple strictly isolated participant workspaces. | Inference code may be reused, but participant records and ontology relationships do not mix. |
| D-017 | Accepted | Follow a broad, utility-first inference philosophy for consenting participants. | Sensitive topics are not automatically excluded, but evidence, confidence, false-positive cost, review, and participant correction remain required. |
| D-018 | Accepted | Do not anonymize initial participant data. | The small controlled research workflow needs identifiable longitudinal records; isolation, encryption, access, and deletion remain required. |
| D-019 | Accepted | Use mythological/scientific branding with provocative surveillance messaging. | The product should invite curiosity while making its consent-based operation immediately clear. |
| D-020 | Provisional | Keep Panoptes and Laplace as the two leading names. | Panoptes can name the all-seeing platform; Laplace can name its predictive inference engine. Final naming requires collision research. |
| D-021 | Accepted | Keep the implementation open source. | Inspectability supports trust, recruiting value, extensibility, and technical review. A license remains open. |
| D-022 | Accepted | Avoid copying Palantir Gotham's proprietary visual identity. | The project adopts ontology and operational-action concepts while creating an original implementation and brand. |

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
