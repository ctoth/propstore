# Family Protocol Cutover Workstream Index

Date: 2026-05-24

## Refactor Zen

One field, schema, relationship, lifecycle state, artifact participation rule,
storage fact, document shape, and reference fact lives in one place: the family
charter and its field metadata. Propstore owns semantic behavior on family
models and family/domain owners. Quire owns generated document structs/codecs,
generated mapped models, generic family lookup, generic relationship traversal,
generic lifecycle execution, and generic local-id reservation.

Deletion is the first operation for every replaced surface. Do not restore a
deleted module under a new name. Do not add aliases, shims, adapters, fallback
readers, compatibility bridges, broad coercers, kwargs builders, duplicate DTOs,
or per-family wrappers around generic family infrastructure.

## Forked Scout Inputs

This split was produced from explicitly forked worker reports written under
`reports/charter-cutover-breakdown/`:

- `quire-prereqs-report.md`
- `family-docs-registry-report.md`
- `source-lifecycle-report.md`
- `root-semantic-surfaces-report.md`
- `worldline-resolution-report.md`
- `old-workstream-reconciliation-report.md`

## Phase Order

Execute in this exact order:

| Phase | Child workstream file | Gate to proceed |
| --- | --- | --- |
| 1. Deleted-file fallout repair | `01-deleted-file-fallout-repair.md` | Deleted modules stay deleted; import fallout is routed to charter/registry and typed model owners; narrow pyright gate passes. |
| 2. Quire generated family protocols | `02-quire-generated-family-protocols.md` | Quire generated documents, lifecycle, graph/artifact, local-id, and FTS/vector proof gates pass and are pushed. |
| 3. Generic family lookup cleanup | `03-generic-family-lookup-cleanup.md` | Direct string table/model lookup gates are zero production hits or replaced by owner APIs backed by generic family metadata. |
| 4. Family document deletion | `04-family-document-deletion.md` | Handwritten family document classes are deleted family by family; generated document API gates pass. |
| 5. Registry, contracts, and batches | `05-registry-contracts-batch-specs.md` | Registry is composition only; contracts enumerate generated charter documents; batch specs are charter metadata. |
| 6. Source lifecycle state machines | `06-source-lifecycle-state-machines.md` | Source-local helper files stop owning document shape, payload rewriting, reference normalization, and branch workflow semantics. |
| 7. Proposal lifecycle state machines | `07-proposal-lifecycle-state-machines.md` | Stance/rule/predicate proposal root workflows are deleted and replaced by generic lifecycle transitions. |
| 8. Artifact, graph, verification, export | `08-artifact-graph-verification-export.md` | Artifact codes, verification traversal, and graph discovery are metadata-driven; rendering surfaces remain only as presentation. |
| 9. Worldline resolution protocol | `09-worldline-resolution-protocol.md` | Worldline target/input/trace projection uses typed world/family protocols; handwritten worldline documents are gone. |
| 10. Context lifting and justification views | `10-context-lifting-justification-views.md` | Context lifting semantics live under context owner; duplicate `CanonicalJustification` schema/construction path is deleted. |
| 11. Concept local IDs, compatibility, fixtures | `11-concept-local-id-compatibility-fixtures.md` | Concept numeric reservation is concept-family identity over Quire reservation; compat/coerce/fallback and dict fixture gates are resolved. |
| 12. Final gates | `12-final-gates.md` | Search, pyright, logged pytest, parity, dependency, and manifest gates pass. |

## First Repair Answer

The deleted files are repaired by moving their real contents to owners, not by
writing the files back.

- `propstore/families/world_charters.py`: split charter definitions into the
  owning family charter modules, compose the whole derived-store schema through
  the registry/charter owner, and expose only generic registry-level schema
  access. Do not recreate a world-charters module.
- `propstore/families/claims/metadata.py`: replace string-key metadata lookup
  with typed `Claim`/claim-family/world-analysis behavior. Do not recreate a
  claim metadata helper.

## Completion Criteria

- Every child phase has run its search/type/test gates.
- Every old production surface named in these files is deleted or moved to the
  exact owner named here.
- Every child phase records kept behavior and final owner in its execution
  record before moving on.
- Parent workstream order still passes.
- This nested workstream order passes.
