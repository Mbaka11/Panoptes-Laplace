# Trust and data governance

## Purpose

Panoptes intentionally handles highly sensitive, identifiable personal data. Trust controls are part of the product's utility: participants cannot benefit from a system they cannot understand or control, and compromised or misused data creates substantial negative utility.

This document records the V1 trust model. It is not a substitute for legal review if the project expands beyond a small private research prototype.

## Roles

### Participant

A consenting adult who owns the source device and is the subject of a workspace.

The participant can:

- choose each source category and inspect collection status/gaps;
- pause collection and initiate an export;
- operate their own local workspace without a separate researcher;
- choose whether to share and understand exactly what a researcher will receive;
- correct or reject interpretations without treating agreement as statistical proof;
- revoke future sharing/access; and
- delete controlled copies and request deletion of researcher copies.

### Self-operator

The participant acting as the analyst of their own workspace. They can explore evidence and provisional hypotheses without granting anyone else access. Self-use does not remove the need for protected storage, provenance, uncertainty, or deletion controls.

### Researcher

A separately authorized operator who receives selected identifiable data, explores relationships, develops analyses, reviews evidence, and shares findings for an agreed purpose.

Both modes are central (D-024), but researcher access is optional and must be described directly. Installing the application or using the self-operated workbench is not consent to disclose data to a researcher. Appropriate review remains necessary for consequential claims; ordinary self-exploration does not require a separate reviewer.

## V1 data posture

- Raw data is identifiable; anonymization is not required for the initial experiments.
- Phone-collected data remains on the participant's iPhone until a participant-initiated export; imported account files have their own source/staging lifecycle.
- The participant can select a date range and data categories for export.
- Data is transferred to a local Mac workbench operated by the participant or, if separately authorized, a researcher.
- Native export files may be unencrypted. Before real transfer, define protected staging, encrypted packaging/transport, key handling, retention, and deletion of temporary copies; the existence of a share button does not establish those controls.
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

### Accepted for V1: self-operated local analysis

The participant initiates protected transfer to their own local workbench. No researcher grant is required for their own data. Permissions, source scope, storage protection, and copy/deletion records remain explicit.

### Accepted for V1: optional controlled batch sharing

The participant selects and initiates an encrypted export to an authorized researcher. Research access begins when the package is transferred and is bounded by its contents and agreed purpose. Restricting future access cannot technically claw back a copy already decrypted by a recipient; communicate that limit and track deletion requests and confirmation.

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

Strict isolation is required, but its logical checks, cryptographic separation, at-rest protection, and key management have not been designed or tested. Do not claim that a workspace identifier alone establishes a security boundary. Use synthetic multi-workspace tests and resolve the protection design before external-participant work.

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
- human review appropriate to the consequence and operating mode;
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
- Optional predictions are verifiably locked before the outcome period and scored prospectively; a content hash alone proves neither creation time nor a pre-outcome commitment.
- Corrections do not silently rewrite historical model output.
- Operator review/publication and participant feedback are auditable events, with the reviewer role visible.
- Missing data is not interpreted as proof that an event did not occur.
- Source-provided aggregates remain aggregates; overlapping exports do not become duplicate activity.
- Resource access or a domain connection is not proof of transmitted content, a company's internal profile, or a causal explanation.
- A null or inconclusive analysis is valid; a positive result is not required for publication as an honestly labeled finding.

## Deletion

V1 must define and test deletion for:

- data still on the participant's device;
- generated export packages;
- imported raw records on the Mac;
- normalized events and ontology objects;
- model features and caches;
- predictions and published insight packages; and
- backups, if backups are later introduced.

Deletion semantics and verification require a concrete technical design before the first external participant study. Define which dependent features/findings are removed or invalidated when a source record is deleted; do not retain sensitive raw values in correction logs or reports while claiming deletion. Record unverified copies and any retention exceptions explicitly rather than promising universal erasure.

## Open-source implications

Open source improves inspection and trust but does not guarantee safe deployments. The repository should:

- document intended consent-based use;
- avoid stealth or evasion features;
- include a security policy before accepting external reports;
- exclude participant data and realistic identifiable fixtures;
- use synthetic demonstration datasets; and
- never commit exports, API keys, signing credentials, or model-provider secrets.

## External AI decision

The choice between a local model and an external provider is intentionally deferred and provider-neutral.

Before raw or derived participant information reaches an external provider, the project must decide:

- exactly what is transmitted;
- provider retention and training policies;
- geographic processing and storage;
- deletion guarantees;
- participant authorization language;
- logging and secret management; and
- whether local feature extraction can reduce disclosure.
