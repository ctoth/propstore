# Epistemic Operating System

The public surface exposes epistemic behavior as typed requests and typed reports.
CLI commands parse files and flags, call the application layer, and render results;
the owner layer holds the semantic model.

## Trace Contract

Every observatory scenario preserves this audit chain:

```text
source artifact -> assertion -> projection -> state -> journal
```

The chain is represented by `SemanticTraceRecord` and exported with a stable
content hash. A report can therefore be compared across policy choices,
operator families, replay runs, and known falsification fixtures without
depending on file order or command-line rendering.

## Micropublication Alignment

Clark's Micropublication model treats a citable claim as a structured object
with attribution, support graphs, challenge graphs, data, methods, references,
and links across publications. Propstore maps that shape into explicit
assertions, projections, and journaled state transitions instead of flattening
claim support into prose.

The same model informs Observatory fixtures: a falsification scenario should
identify the source artifact that introduced the assertion, the projection that
interpreted it, the state hash produced by replay, and the journal entry that
records the transition. Citation-distortion examples become testable scenarios
only when they can be represented with that provenance.

## Observatory

The Observatory compares deterministic semantic behavior. It accepts typed
`EvaluationScenario` values and returns an `ObservatoryReport` containing:

- per-scenario replay hashes and falsification identifiers;
- per-operator summaries;
- trace records tying each result back to source artifacts and journal entries;
- stable export/import hashes for regression fixtures.

The Python API can call the app-layer request directly. The CLI is a
presentation adapter that reads fixture JSON and renders the same typed report.
