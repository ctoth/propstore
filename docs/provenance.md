# Provenance

WS-A Phase 1 makes provenance a typed part of probability-bearing values.

## Paper Commitments

Buneman, Khanna, and Tan 2001 separates why-provenance from where-provenance. Propstore uses that split directly:

- `Provenance.witnesses` records why a value is present.
- `ProvenanceWitness.source_artifact_code` records where the witnessed source value came from.
- `compose_provenance(...)` unions witness chains when a value is derived by fusion or discounting.

Carroll, Bizer, Hayes, and Stickler 2005 treats named graphs as first-class carriers for provenance and trust. Propstore stores a provenance record as a deterministic JSON-LD named graph and attaches it to the git object being annotated with a git note on `refs/notes/provenance`.

## Status Values

Every probability-bearing document value that has crossed the Phase 1 boundary must carry one of:

- `measured`
- `calibrated`
- `stated`
- `defaulted`
- `vacuous`

`defaulted` is deliberately highest priority in composition. A fused value that used a defaulted input remains visibly default-tainted instead of being laundered into a measured or calibrated result.

## Storage

The logical carrier is a named graph. The physical carrier is git notes:

- Notes ref: `refs/notes/provenance`
- Serialization: deterministic JSON-LD encoded by `msgspec`
- Attachment point: the object SHA for the claim or value-bearing object being annotated

This keeps the annotated object's content hash stable. Updating provenance updates the notes ref, not the claim object.

## Document Boundary

`SourceTrustDocument` and `SourceTrustQualityDocument` require `status`. A source trust payload without status fails schema decoding.

`ResolutionDocument` no longer accepts independent `opinion_belief`, `opinion_disbelief`, `opinion_uncertainty`, and `opinion_base_rate` fields. It accepts one `opinion: OpinionDocument | None`, which makes invalid tuples such as `(0, 0, 0, 0.5)` unrepresentable at the authored-document boundary.

Sidecar storage may still project an `OpinionDocument` into normalized scalar columns as a storage detail. Authored YAML and classifier/proposal outputs use the single nested opinion shape.

## Tests

The Phase 1 foundation is guarded by:

- `tests/test_provenance_foundations.py`
- `tests/test_classify.py`
- `tests/test_relate_opinions.py`
- `tests/test_source_trust.py`
- `tests/test_build_sidecar.py`
- `tests/test_praf.py`

