# Qualia And Proto-Roles

WS-A Phase 3 adds the first executable layer above the lemon concept container.
The implementation follows the workstream's non-Davidsonian decision: there is
no `Event` type and no primitive event identity. Description-kinds are concepts;
particular descriptions are claims; coreference is represented by an argument
for merging descriptions at render time.

## Pustejovsky Qualia

`propstore.core.lemon.qualia` implements the four qualia roles from
Pustejovsky 1991:

- `formal`
- `constitutive`
- `telic`
- `agentive`

Each `QualiaReference` points at an `OntologyReference`, may carry a
`TypeConstraint`, and must carry `Provenance`. `coerce_via_qualia` returns an
explicit `CoercedReference` with a role path and composed provenance, so type
coercion is inspectable rather than an implicit rewrite. `purposive_chain`
recovers TELIC chains such as X affords Y and Y affords Z.

## Dowty Proto-Roles

`propstore.core.lemon.proto_roles` implements graded, provenance-bearing
entailments for proto-agent and proto-patient properties. Entailment values are
bounded to `[0, 1]`; missing provenance is a construction error. The
`predicted_subject_role` helper implements the first executable version of
Dowty's Argument Selection Principle: among named roles, the highest
proto-agent weight predicts subject position, while ties remain undecided.

## Description-Kinds

`propstore.core.lemon.description_kinds` defines participant slots, slot
bindings, description claims, Dung-backed coreference queries, and
account-sensitive causal connection assertions.

Description-kind slot bindings carry both a value and a value type. Validation
checks the value type against the slot's `OntologyReference` constraint.
Coreference is represented as merge hypotheses inside `CoreferenceQuery`, not
as a stored identity fact. The query exposes a `dung.ArgumentationFramework`;
cluster results are computed under a requested Dung semantics, so grounded
semantics can withhold a cluster while preferred/stable semantics surface rival
clusters without changing the stored merge hypotheses. Causal transitivity is
explicitly account-sensitive: the current implementation does not infer
transitivity for merely `stated` causal links and does not merge different
causal accounts.

## Worldline Review

`propstore/worldline/trace.py`, `revision_capture.py`, and
`argumentation.py` were reviewed for this slice. They currently capture
resolution steps, revision state, and argumentation state over existing active
claims. They are not changed in this slice because description-claims do not yet
have a persisted claim-document shape for worldline to consume. The intended
adoption point is the later Phase 3 claim/seed slice: once description-claims
are concrete claim records, worldline should treat them as an agent's
description trajectory rather than introducing a parallel event trajectory.

## Lexical Senses

`LexicalSense` now carries optional Phase 3 semantic structure:

- `qualia: QualiaStructure | None`
- `description_kind: DescriptionKind | None`
- `role_bundles: Mapping[str, ProtoRoleBundle] | None`

This keeps Phase 3 semantics at the sense level, where the workstream places
Pustejovsky qualia, description-kind structure, and Dowty role entailments.

## Tests

The first Phase 3 slice is guarded by
`tests/test_lemon_phase3_semantics.py`, including Hypothesis properties for
qualia coercion soundness, TELIC chain recovery, graded entailment bounds, and
Dowty-style argument selection.
