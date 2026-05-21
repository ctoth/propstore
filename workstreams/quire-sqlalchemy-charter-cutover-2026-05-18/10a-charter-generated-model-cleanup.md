# 10a - Charter-Generated Model Cleanup

Date: 2026-05-21

## Refactor Zen

Storage/model field shape is declared exactly once in Quire charter metadata.
Propstore mapped model classes are methods-only subclasses of Quire
`FamilyModel`: they may define semantic properties or methods, but they must
not declare storage fields, constructor field lists, row DTOs, broad
`__init__` sinks, compatibility constructors, or placeholder record fields.
If a method needs a mapped value, it reads the already-loaded mapped attribute;
it does not create a second field schema.

## Goal

Delete the duplicate mapped-model field layer introduced or left by prior
cutover phases.

Final state:

- Quire commit `f69c2f018c25c6aaca277af35976fd419ded39fe` is pinned in
  Propstore and provides `FamilyModel` plus a proof test that charter fields,
  generic construction, and methods-only subclass behavior compose.
- Every Propstore sidecar mapped model subclasses `FamilyModel`.
- Propstore sidecar mapped model classes contain no storage field annotations,
  no constructor field lists, no `__init__(**values)` sinks, no `from_row_mapping`,
  no `coerce`, no `Input = Model | Mapping[...]`, and no `to_row_mapping`.
- Quire `FamilyCharter.fields` remains the only storage field list.
- Semantic behavior stays in Propstore as methods/properties or owner-layer
  functions when it interprets already-loaded typed fields and relationships.

## Prerequisites

Required phase file prerequisites: `00-index.md`, `inventory-matrix.md`,
`helper-ledger.md`, `01-quire-capability-and-charter.md`,
`02-quire-sqlalchemy-engine.md`, `03-quire-fts-vector.md`,
`04-propstore-build-orchestration.md`, `05-source-and-diagnostics.md`,
`06-forms-concepts-parameterizations.md`, `07-contexts-lifting.md`,
`08-claims-active-claims.md`, `08a-typed-claim-graph-projection.md`,
`09-relations-stances-conflicts.md`, `10-micropublications-justifications.md`.

Before implementation:

- confirm Propstore pins Quire to pushed commit
  `f69c2f018c25c6aaca277af35976fd419ded39fe`;
- confirm Quire proof gates passed:
  `uv run pyright` and
  `uv run pytest -vv tests/test_sqlalchemy_engine.py::test_family_model_subclass_uses_charter_fields_and_keeps_behavior`;
- rerun the workstream order checker.

## Deletion Targets

Delete or rewrite these production surfaces so only methods remain on mapped
classes:

- `propstore/families/sources/declaration.py`: `Source.__init__(**values)`.
- `propstore/families/forms/stages.py`: `Form.__init__(**values)` and
  `FormAlgebra.__init__(**values)`.
- `propstore/families/concepts/declaration.py`: field annotations,
  `from_row_mapping`, `coerce`, `to_row_mapping`, `ConceptInput`, and
  `ParameterizationInput` on `Concept`, `ConceptAlias`, `ConceptRelationship`,
  `Parameterization`, and `ParameterizationGroup`.
- `propstore/families/contexts/declaration.py`: constructor field lists on
  `Context`, `ContextAssumption`, `ContextLiftingRule`,
  `ContextLiftingMaterialization`, and any write model that only carries typed
  model batches.
- `propstore/families/claims/declaration.py`: storage field annotations and
  broad constructors on `Claim`, `ClaimConceptLink`, `ClaimNumericPayload`,
  `ClaimTextPayload`, `ClaimAlgorithmPayload`, and `ClaimSourceAssertion`.
- `propstore/families/relations/declaration.py`: storage field annotations and
  constructors on `RelationEdge`, `Stance`, `ConceptRelation`, and
  `ConflictWitness`.
- `propstore/families/micropublications/declaration.py`: storage field
  annotations and constructors on `Micropublication` and
  `MicropublicationClaimLink`; keep only semantic methods if any.
- `propstore/core/justifications.py`: storage field annotations and
  constructor field list on `Justification`; delete duplicated
  `CanonicalJustification` schema/conversion role in Phase 12.
- `propstore/families/world_charters.py`: `WorldModel`, placeholder
  `*Record` classes, and any local broad-constructor record family.

## Required Pattern

For every mapped sidecar model:

```python
from quire.charters import FamilyModel


class Claim(FamilyModel):
    def semantic_method(self) -> str:
        return cast(str, getattr(self, "id"))
```

Rules:

- no storage field annotations in the class body;
- no `__init__` in the class unless it is pure semantic behavior and does not
  accept storage fields;
- no dataclass/attrs/msgspec model for mapped storage shape;
- no compatibility constructor;
- no field-name list outside the charter;
- model construction goes through `SqlAlchemySchema.construct`,
  `DerivedSession.add_family`, or direct SQLAlchemy mapped construction after
  the schema is built.

## Execution Loop

1. Update this workstream and `00-index.md` first.
2. Convert one owner file at a time to methods-only `FamilyModel` subclasses.
3. After each owner file, run `uv run pyright propstore`.
4. Fix only failures caused by removing field declarations/constructors.
5. Commit each owner file slice before moving to the next owner file.
6. Run the required search gates.
7. Run the targeted logged tests from the owning child phase.
8. Reread `00-index.md` and this file after each passing substantial gate.

## Required Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label charter-generated-model-cleanup tests/test_world_query.py tests/test_graph_export.py
rg -n -F -- "__init__(self, **values" propstore/families propstore/core propstore/world tests
rg -n -F -- "from_row_mapping" propstore/families propstore/core propstore/world tests
rg -n -F -- ".coerce(" propstore/families propstore/core propstore/world tests
rg -n -F -- "Input = " propstore/families propstore/core propstore/world tests
rg -n -F -- "to_row_mapping" propstore/families propstore/core propstore/world tests
rg -n -F -- "class WorldModel" propstore tests
rg -n -- "class .*Record\\(" propstore/families/world_charters.py propstore tests
```

The gates are zero-hit gates outside notes, workstreams, docs, and reports
unless a hit is a non-mapped authored document boundary explicitly named in
that owner workstream.

## Execution Log

- 2026-05-21 Quire `FamilyModel` support was pushed at
  `f69c2f018c25c6aaca277af35976fd419ded39fe`, Propstore was pinned to that
  pushed commit, and `uv run scripts/check_workstream_order.py
  workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/00-index.md` passed.
- Source slice complete: `Source` now subclasses `FamilyModel` and no longer
  defines a Propstore `__init__(**values)` constructor. `uv run pyright
  propstore` passed after the slice.

## Completion Criteria

This cleanup is complete only when:

- every mapped sidecar model subclasses `FamilyModel`;
- every mapped sidecar model class body is methods-only;
- Quire charters are the only storage field declarations;
- all deletion-target searches are clean;
- `uv run pyright propstore` passes;
- the targeted logged tests pass;
- `00-index.md`, `duplicate-definition-audit-2026-05-20.md`, and the relevant
  child workstreams record that hand-authored mapped storage classes are not
  allowed.
