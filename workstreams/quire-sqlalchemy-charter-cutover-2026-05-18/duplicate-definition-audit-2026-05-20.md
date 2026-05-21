# Duplicate Definition Audit

Date: 2026-05-20

## Verdict

No. The cutover output does not yet define every field/state shape exactly
once in a charter or exact semantic owner.

This audit exists because Phase 10 briefly added an uncommitted
`ClaimCompiledPayload` plus `*_from_payload` helper draft. That draft repeated
the old row-builder pattern under a new name. It was reverted before this
audit was written, but it exposed a broader execution problem: prior committed
slices also left or introduced loose model constructors, mapping repair paths,
and duplicate field/state lists.

## Scope Audited

Propstore committed workstream range:

```powershell
git log --oneline --reverse be748ae0^..HEAD
git diff --name-only be748ae0^..HEAD -- *.py pyproject.toml uv.lock workstreams/quire-sqlalchemy-charter-cutover-2026-05-18
```

Quire committed SQLAlchemy/charter range:

```powershell
git log --oneline --max-count=80
git diff --name-only 20d848f^..HEAD -- quire tests pyproject.toml uv.lock
```

Pattern searches run in Propstore:

```powershell
rg -n -F -- 'metadata={"coerce"' propstore tests
rg -n -F -- '"coerce":' propstore tests
rg -n -F -- "CompiledPayload" propstore tests
rg -n -F -- "_from_payload" propstore/families propstore/core propstore/world propstore/worldline tests
rg -n -F -- "**values" propstore/families propstore/core propstore/world propstore/worldline tests
rg -n -F -- "from_row_mapping" propstore tests
rg -n -F -- "ConceptInput" propstore tests
rg -n -F -- "ParameterizationInput" propstore tests
```

Pattern searches run in Quire:

```powershell
rg -n -F -- "CompiledPayload" quire tests
rg -n -F -- "from_payload" quire tests
rg -n -F -- 'metadata={"coerce"' quire tests
rg -n -F -- '"coerce":' quire tests
rg -n -F -- "**values" quire tests
```

## Confirmed Violations Introduced Or Left By This Execution

### Current Reverted Draft: `ClaimCompiledPayload`

Status: reverted before writing this file; not committed.

Problem: the draft added a scalar-field DTO and private payload factories in
`propstore/families/claims/stages.py` and
`propstore/families/claims/declaration.py`.

Why it is forbidden: it duplicated claim core/payload field shape outside the
charter and outside the actual semantic owner. It was exactly the
`claim_model_from_payload`-style replacement layer the Phase 10 workstream
forbids.

Required rule before resuming Phase 10: no `*CompiledPayload`, no
`*_from_payload` factory, no scalar-field DTO, and no model-layer payload
repair may be added to replace `prepare_claim_insert_row`.

### Phase 6 Concept Slice: Mapping Repair Reintroduced As Typed Model APIs

Commits: `5151fafe`, `af025aa4`.

Files and evidence:

- `propstore/families/concepts/declaration.py:269`:
  `Concept.from_row_mapping`.
- `propstore/families/concepts/declaration.py:297`:
  `Concept.coerce`.
- `propstore/families/concepts/declaration.py:421`:
  `Parameterization.from_row_mapping`.
- `propstore/families/concepts/declaration.py:437`:
  `Parameterization.coerce`.
- `propstore/families/concepts/declaration.py:462`:
  `ParameterizationInput = Parameterization | Mapping[str, Any]`.
- `propstore/families/concepts/declaration.py:465`:
  `ConceptInput = Concept | Mapping[str, Any]`.

Problem: these are compatibility/mapping repair paths. They keep a dict input
surface alive after the model/charter cutover and duplicate field lists in
`known` sets and `to_row_mapping` dictionaries.

Required cleanup: delete `ConceptInput`, `ParameterizationInput`,
`from_row_mapping`, `coerce`, and `to_row_mapping` from this production path;
update callers to receive typed `Concept` and `Parameterization` objects or
move true IO parsing to the owner boundary.

### Phase 6 Forms Slice: Loose Model Constructors

Commit: `f6e6b54e`.

Files and evidence:

- `propstore/families/forms/stages.py:53`: `Form.__init__(**values)`.
- `propstore/families/forms/stages.py:59`: `FormAlgebra.__init__(**values)`.

Problem: these are not precise model definitions. They allow any caller to
attach arbitrary fields and make the charter less than the single executable
shape for the model.

Required cleanup: replace loose `**values` model constructors with exact
typed construction or let Quire instantiate mapped objects from the charter
without a Propstore-level arbitrary field sink.

### Phase 7 Context Slice: Constructor Field Lists Duplicate Charter Fields

Commit: `cd011c7e`.

Files and evidence:

- `propstore/families/contexts/declaration.py:30`: `Context`.
- `propstore/families/contexts/declaration.py:46`: `ContextAssumption`.
- `propstore/families/contexts/declaration.py:53`: `ContextLiftingRule`.
- `propstore/families/contexts/declaration.py:71`:
  `ContextLiftingMaterialization`.
- `propstore/families/contexts/declaration.py:101`: `ContextWriteModels`.

Problem: the model constructor signatures and the world charters both enumerate
the storage fields. `ContextWriteModels` is a batch carrier, but the model
classes themselves still require a second field list outside the charter.

Required cleanup: make the context charter/model boundary single-source. The
field list must not live once in constructor signatures and again in charters.

### Phase 5 Source Slice: Loose Model Constructor

Commit: `cf305578`.

Files and evidence:

- `propstore/families/sources/declaration.py:43`: `Source.__init__(**values)`.

Problem: `Source` is a mapped domain model but accepts arbitrary fields rather
than a precise charter-derived shape. The source charter is the intended single
field declaration; `**values` is a loose model-layer sink.

Required cleanup: remove arbitrary `**values` construction for mapped source
objects.

### Phase 10 Claim Model Slice: Claim/Payload Classes Duplicate Charter Shape

Commits: `80921a98`, `63109c0a`, `2ad2cabb`.

Files and evidence:

- `propstore/families/claims/declaration.py:80`: `Claim`.
- `propstore/families/claims/declaration.py:101`: `Claim.__init__(**values)`.
- `propstore/families/claims/declaration.py:134`: `ClaimNumericPayload`.
- `propstore/families/claims/declaration.py:147`:
  `ClaimNumericPayload.__init__(**values)`.
- `propstore/families/claims/declaration.py:152`: `ClaimTextPayload`.
- `propstore/families/claims/declaration.py:168`:
  `ClaimTextPayload.__init__(**values)`.
- `propstore/families/claims/declaration.py:173`: `ClaimAlgorithmPayload`.
- `propstore/families/claims/declaration.py:180`:
  `ClaimAlgorithmPayload.__init__(**values)`.

Problem: claim fields are listed in the model annotations, listed again in
`world_charters.py`, and then accepted through broad kwargs constructors. This
does not satisfy the single-definition requirement.

Required cleanup: remove broad kwargs construction and do not add a replacement
DTO. The next claim slice must either make Quire instantiate the mapped model
from the charter shape or use exact typed owner objects without duplicating
charter field lists.

### Phase 10 Claim Variable Move: Coercion Metadata Was Introduced Then Fixed

Commits: `75ae67a8`, fixed by `472b2a60`.

Problem: `ClaimAlgorithmVariable` briefly gained `coerce` metadata and broad
value repair in the model layer.

Current status: fixed. Searches for `metadata={"coerce"` and `"coerce":`
across `propstore tests` returned no hits.

Required rule: the fix is kept, and this pattern must become a mechanical
zero-hit gate before further model moves.

### Build Plan: Family Batch Functions Duplicate Table Routing

Commits: `75963c64`, later family cutover commits.

Files and evidence:

- `propstore/derived_build_plan.py:75`: `WorldWriteBatch`.
- `propstore/derived_build_plan.py:191`: `_batch`.
- `propstore/derived_build_plan.py:195`: `_context_batches`.
- `propstore/derived_build_plan.py:207`: `_concept_batches`.
- `propstore/derived_build_plan.py:220`: `_claim_batches`.

Problem: `WorldWriteBatch` is not itself a scalar-field DTO, but the
`_*_batches` functions restate family table names and state routing outside
the charter/catalog. This is a transitional duplicate routing layer.

Required cleanup: replace per-family batch routing with Quire catalog/session
mechanics once the current family cutover reaches that gate.

### World/Family Lookup Wrappers: Per-Family Reference Resolution

Status: newly identified during Phase 10 review.

Files and evidence:

- `propstore/world/model.py`: `WorldQuery.resolve_claim`,
  `WorldQuery.resolve_concept`, and `WorldQuery.resolve_alias`.
- `propstore/world/overlay.py`: overlay `resolve_claim`,
  `resolve_concept`, and `resolve_alias` passthrough wrappers.
- `propstore/core/environment.py`: `WorldStore` protocol requires
  claim/concept/alias-specific resolver methods.
- `propstore/world/bound.py`: `_store.resolve_claim`,
  `_store.resolve_concept`, `_resolve_claim_lookup_id`, and
  `hasattr(..., "resolve_claim")` branches.
- `propstore/families/claims/declaration.py`: `resolve_claim_id` and
  `resolve_claim_embedding_entity`.
- `propstore/families/concepts/sidecar_runtime.py`: constructs
  `WorldQuery(...).resolve_concept(...)`.

Problem: these are not family semantics. They are generic family-reference
lookup encoded as claim/concept-specific methods and helpers. Keeping them as
thin wrappers over a future generic lookup would preserve the same duplicate
surface under a different implementation.

Required cleanup: Quire must expose generic family main-model access and
reference lookup from charter/catalog metadata. Delete `resolve_claim`,
`resolve_concept`, `resolve_alias`, `resolve_claim_id`,
`resolve_concept_id`, `resolve_concept_alias`, and equivalent per-family
wrappers/call sites. Callers that need identity resolution must use the
generic family-reference API directly. Typed ORM/domain model methods may
remain only for family-local semantics over already-loaded typed fields and
relationships.

## Quire Audit Result

The Quire SQLAlchemy/charter commits are not where this specific Propstore
mistake was introduced.

Findings:

- `CompiledPayload` search: no hits.
- `metadata={"coerce"` and `"coerce":` searches: no hits.
- `from_payload` hits are in `quire/contracts.py`, which was not part of the
  SQLAlchemy/charter diff range audited here.
- `**values` hits are in old projection row builders in `quire/projections.py`,
  not in the new SQLAlchemy charter engine files audited here.

Quire still has old projection machinery by design until the final deletion
phase, but the duplicate DTO/factory mistake under review is in the Propstore
family cutover work, not in the new Quire charter engine commits.

## 2026-05-21 Quire Model Capability Update

Quire now has the concrete pattern required to delete Propstore hand-authored
mapped storage classes:

- Quire commit `f69c2f018c25c6aaca277af35976fd419ded39fe` is pushed.
- Propstore pins that pushed commit in `pyproject.toml` and `uv.lock`.
- Quire exposes `FamilyModel` for methods-only mapped classes.
- Quire proof test
  `tests/test_sqlalchemy_engine.py::test_family_model_subclass_uses_charter_fields_and_keeps_behavior`
  proves a `FamilyModel` subclass can define methods only while
  `FamilyCharter.fields` supplies storage shape and SQLAlchemy/Quire
  construction supplies mapped attributes, including construction before the
  SQLAlchemy schema is built.
- `uv run pyright` passed in Quire after that proof.

Required Propstore consequence: every mapped sidecar model class becomes a
methods-only `FamilyModel` subclass. Storage field annotations, constructor
field lists, broad `__init__(**values)` constructors, placeholder `*Record`
classes, and mapping repair APIs are old paths and must be deleted.

## Mechanical Gates Required Before Resuming Implementation

Before Phase 10 execution resumes, add or run a guard that fails on these
patterns in production code touched by the active phase:

```powershell
rg -n -F -- "CompiledPayload" propstore tests
rg -n -F -- "claim_model_from_payload" propstore tests
rg -n -F -- "_from_payload" propstore/families/claims propstore/core tests
rg -n -F -- 'metadata={"coerce"' propstore tests
rg -n -F -- '"coerce":' propstore tests
rg -n -F -- "from_row_mapping" propstore/families/claims propstore/families/concepts propstore/core propstore/world tests
rg -n -F -- "**values" propstore/families/claims propstore/families/concepts propstore/families/forms propstore/families/sources propstore/families/contexts propstore/families/world_charters.py
rg -n -- "Input\\s*=.*Mapping" propstore/families propstore/core propstore/world tests
rg -n -F -- "def resolve_claim" propstore tests
rg -n -F -- "def resolve_concept" propstore tests
rg -n -F -- "def resolve_alias" propstore tests
rg -n -F -- ".resolve_claim(" propstore tests
rg -n -F -- ".resolve_concept(" propstore tests
rg -n -F -- ".resolve_alias(" propstore tests
rg -n -F -- "resolve_claim_id" propstore tests
rg -n -F -- "resolve_concept_id" propstore tests
rg -n -F -- "resolve_concept_alias" propstore tests
```

The exact allowed set must be zero for active cutover production code unless
the active workstream explicitly marks a true IO boundary and names the owner.

## Cleanup Order

1. Keep the reverted `ClaimCompiledPayload` draft out of the tree.
2. Update the active workstream to make this audit binding before the next code
   slice.
3. Delete Phase 10 claim broad kwargs/payload replacement paths before adding
   any new claim construction code.
4. Clean Phase 6 concept mapping repair (`ConceptInput`,
   `ParameterizationInput`, `from_row_mapping`, `coerce`, `to_row_mapping`).
5. Add or use Quire generic family main-model/reference lookup, then delete
   per-family lookup wrappers and call sites instead of rebuilding them as
   thin convenience methods.
6. Execute `10a-charter-generated-model-cleanup.md`: convert every mapped
   sidecar model to a methods-only `FamilyModel` subclass and delete storage
   field annotations, constructor field lists, broad `__init__(**values)`
   constructors, placeholder `*Record` classes, and mapping repair APIs.
7. Replace per-family build-plan table routing with Quire catalog/session
   routing when the current family gates reach that owner boundary.

No future code slice should be considered executable if it adds a new DTO,
payload factory, mapping repair path, broad kwargs constructor, hand-authored
mapped storage field, placeholder record class, or table-routing helper as a
replacement for a deleted projection surface.
