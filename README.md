# Panoptes

> **Working product name:** Panoptes
>
> **Working inference-engine name:** Laplace
>
> **Message:** See what sees you.

Panoptes is an open-source, consent-based personal intelligence research project. It collects personal data that a participant explicitly authorizes, organizes it into a temporal ontology, reveals what can be inferred from it, and turns validated conclusions into useful predictions, notifications, and personal experiments.

The project has two connected purposes:

1. **Privacy revelation:** show what a sufficiently capable observer can learn from personal data.
2. **Personal utility:** give that intelligence back to the participant in an understandable and actionable form.

## Status

The project is in its product-definition and technical-discovery phase. No production application exists yet.

The first planned experiment combines historical imports and live iPhone collection to:

- construct a participant's personal ontology;
- reveal an evidence-backed inferred profile;
- produce a timestamped prediction of their Monday;
- discover at least one cross-domain behavioral pattern; and
- return a useful notification whose outcome can be measured.

## Planned shape

```text
Native iPhone collector
        ↓ encrypted participant-controlled export
Local Mac research workbench
        ↓ ontology + Laplace inference engine
Participant insight package
        ↓
iPhone explanation, notification, and feedback
```

The first version is sideloaded, local-first, and designed for a small group of fully informed adult participants personally recruited by the researcher. It is not covert monitoring software.

## Documentation

- [Documentation index](docs/README.md)
- [Product vision](docs/product-vision.md)
- [V1 and first experiment](docs/mvp.md)
- [System architecture](docs/architecture.md)
- [Personal ontology](docs/ontology.md)
- [Laplace inference engine](docs/inference-engine.md)
- [Trust and data governance](docs/trust-and-data-governance.md)
- [Branding](docs/branding.md)
- [Decision log](docs/decisions.md)

## Current boundaries

- Collection requires informed, explicit participant authorization.
- Raw identifiable data may be used in the initial research prototype.
- Participant datasets remain isolated from one another.
- Batch export to a local Mac comes before continuous synchronization.
- Statistical and ML methods establish evidence; language models may help classify, hypothesize, and explain.
- The choice between local and external language models is deferred.
- iOS permissions and sandbox restrictions are respected even when the application is sideloaded.

## License

A license has not yet been selected. This is tracked as an open decision.
