# Trust and data governance

## Purpose

Panoptes intentionally handles highly sensitive, identifiable personal data. Trust controls are part of the product's utility: participants cannot benefit from a system they cannot understand or control, and compromised or misused data creates substantial negative utility.

This document records the V1 trust model. It is not a substitute for legal review if the project expands beyond a small private research prototype.

## Roles

### Participant

A consenting adult who owns the source device and is the subject of a workspace.

The participant can:

- choose each source category;
- inspect collection status;
- pause collection;
- initiate an export;
- understand what the researcher will receive;
- correct or reject conclusions;
- revoke future access; and
- request deletion of device and researcher copies.

### Researcher

The explicitly authorized operator who receives identifiable raw data, explores correlations, creates inference definitions, reviews evidence, and publishes participant insights.

Researcher access must be described directly. Installing the application is not by itself consent for unrestricted researcher access.

## V1 data posture

- Raw data is identifiable; anonymization is not required for the initial experiments.
- Data remains on the participant's iPhone until a participant-initiated export.
- The participant can select a date range and data categories for export.
- Exported data is transferred to a local Mac research workbench.
- Participant workspaces remain isolated.
- No continuous synchronization or cloud participant database exists in V1.
- No external AI provider receives data until a separate decision and authorization process exists.

## Consent model

Consent should be specific enough to answer:

- What data categories are collected?
- Is collection foreground, background, or imported?
- What date range is involved?
- What can the researcher inspect?
- For what experiment or purpose?
- How long will each copy be retained?
- How can collection and access be stopped?
- How is deletion requested and confirmed?
- Will any external processor receive data?

OS permission prompts are necessary but not sufficient. Panoptes should explain the product-level purpose before triggering an iOS permission dialog.

## Access modes

### Accepted for V1: controlled batch sharing

The participant initiates an encrypted export. Research access begins when the package is transferred and is bounded by the package contents and agreed purpose.

### Deferred: continuous trusted sharing

A future version may synchronize authorized categories continuously. It will require authentication, encryption, revocation, access logs, device management, and incident-response design before implementation.

## Workspace isolation

The Mac workbench may contain multiple identifiable participants, but:

- each workspace has a unique identifier;
- records are never merged by default;
- ontology edges cannot cross workspace boundaries;
- exports and insight packages identify exactly one workspace;
- shared inference definitions contain code/configuration, not participant records; and
- cross-participant analysis is deferred.

Cryptographic separation is desirable and remains a technical design decision.

## Third-party information

Calendar events, contacts, photos, communications, and location traces may reveal information about people who did not participate.

V1 should avoid collecting or exporting third-party content unless it is essential to an explicitly approved experiment. Connectors should support minimization, such as excluding attendee details, message contents, faces, or contact fields that are not about the participant.

The system does not construct dossiers about nonparticipants.

## Broad inference scope

Panoptes follows a utility-first research direction and does not automatically exclude a hypothesis because its subject is sensitive. Broad scope does not turn hypotheses into facts.

Requirements for consequential inferences include:

- clear evidence lineage;
- confidence and uncertainty;
- alternative explanations;
- false-positive cost;
- researcher review;
- participant visibility and correction; and
- no automatic consequential action.

The prototype is not a clinical diagnostic tool. Health-related observations must be framed as personal associations or measurements unless supported by an appropriate validated method and future review.

## Technical boundaries

The project will not implement:

- hidden installation or collection;
- iOS permission bypassing;
- sandbox escape or persistence evasion;
- credential or global keystroke capture;
- covert microphone or camera activation;
- arbitrary access to other applications' private data;
- tracking of a person who did not participate; or
- deceptive collection status.

These boundaries preserve the project's declared consent-based purpose and distinguish provocative branding from actual malware behavior.

## Integrity and provenance

- Original records are retained or referenced separately from normalized events.
- Derived assertions identify their method and evidence.
- Predictions are timestamped and locked before evaluation.
- Corrections do not silently rewrite historical model output.
- Researcher publication and participant feedback are auditable events.
- Missing data is not interpreted as proof that an event did not occur.

## Deletion

V1 must define and test deletion for:

- data still on the participant's device;
- generated export packages;
- imported raw records on the Mac;
- normalized events and ontology objects;
- model features and caches;
- predictions and published insight packages; and
- backups, if backups are later introduced.

Deletion semantics and verification require a concrete technical design before the first external participant study.

## Open-source implications

Open source improves inspection and trust but does not guarantee safe deployments. The repository should:

- document intended consent-based use;
- avoid stealth or evasion features;
- include a security policy before accepting external reports;
- exclude participant data and realistic identifiable fixtures;
- use synthetic demonstration datasets; and
- never commit exports, API keys, signing credentials, or model-provider secrets.

## External AI decision

The use of a local Chinese or other open-weight model versus an external commercial provider is intentionally deferred.

Before raw or derived participant information reaches an external provider, the project must decide:

- exactly what is transmitted;
- provider retention and training policies;
- geographic processing and storage;
- deletion guarantees;
- participant authorization language;
- logging and secret management; and
- whether local feature extraction can reduce disclosure.
