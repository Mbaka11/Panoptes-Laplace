# Panoptes

> **Working product name:** Panoptes
>
> **Working inference-engine name:** Laplace
>
> **Message:** See what sees you.

Panoptes Laplace is an open-source, consent-based personal intelligence research project. It connects authorized personal data into an explorable temporal ontology, revealing what those traces can say about a person's life. The ambition is a personal intelligence workbench—not an ad tracker, health-only dashboard, or mandatory prediction demo.

The project has two connected purposes:

1. **Privacy revelation:** show what a sufficiently capable observer can learn from personal data.
2. **Personal utility:** help the participant explore and understand connected evidence. Predictions, recommendations, and experiments are optional uses; understanding is itself valuable.

## Status

The project is in technical discovery. No native application has been implemented or validated on a device yet. A standalone [synthetic App Privacy Report inspector](spikes/app-privacy-report.md) is runnable locally; it is not a production importer or a real-data collection capability.

The next milestone is a [collection feasibility lab](docs/collection-probe.md), followed by a small local explorer that can:

- connect useful native signals and participant-provided imports;
- expose collection coverage, gaps, and source provenance;
- explore records by object, relationship, time, and source;
- run one reproducible analytical investigation, including an honest null result; and
- support participant corrections, export, and deletion.

The reported test setup is an iPhone 15 Pro on iOS 26.6.1 in Canada, with a Mac and Xcode available. Exact Mac versions are pending. Documentation and synthetic preparation can proceed on Windows; native scaffolding remains gated on the Mac preflight.

## Run the synthetic spike

Python 3.10+, standard library only, from the repository root:

```bash
python -m unittest discover -s tests -v
python -m spikes.app_privacy_report --demo
python -m spikes.app_privacy_report --demo --coverage
```

The demo only reads bundled fake records; it does not accept participant-file paths or access a device/network. The optional `--coverage` report adds record counts, source-line provenance, supported timestamp ranges, and explicit unknowns—not a claim of complete or verified device coverage. See [the test evidence](docs/results/app-privacy-report-synthetic.md) and [the Foundry/collection inspiration review](docs/inspirations-and-collection-patterns.md). Real-data protection and Mac build prerequisites remain open.

## Planned shape

```text
Authorized iPhone collection + participant-provided imports
        ↓ protected, participant-controlled batch transfer
Local Mac workbench — self-operated or authorized researcher
        ↓ source-aware ontology + Laplace analysis
Personal explorer — timelines, relationships, findings, evidence
        ↓ optional extension
Reviewed phone insights, forecasts, notifications, and experiments
```

The first version is sideloaded and local-first. Both self-operated and researcher-assisted use are central; sharing with a separate researcher is optional and specifically authorized. Begin with the owner's self-use, then fully informed adult participants after the controls are tested. It is not covert monitoring software.

## Documentation

- [Documentation index](docs/README.md)
- [Vision review and next steps](docs/review-and-next-steps.md)
- [Collection feasibility protocol](docs/collection-probe.md)
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
- Observable traces are not proof of what a company collected or concluded; inaccessible interaction data stays labeled as a coverage gap.

## License

A license has not yet been selected. This is tracked as an open decision.
