# CEL Registry Hardening Workstream

Date: 2026-04-14
Status: active
Refines: `plans/cel-subsystem-unification-plan-2026-04-08.md` phase `U1`

## Goal

Finish the registry cleanup as an architectural boundary change, not just a
line-count reduction.

Target outcome:

1. `propstore.cel_checker` stops knowing about concept payload shapes.
2. Registry projection happens at the boundary that owns the source data.
3. Invalid or ambiguous registry input fails hard instead of being silently
   skipped.
4. Canonical authored concepts and world/sidecar concepts use explicit,
   separate projection paths.
5. Synthetic CEL binding definitions live with the runtime/environment
   contract, not inside the checker.

This workstream is registry-only. It does not include the typed-AST refactor,
span-carrying diagnostics, or parse/type error unification except where a
small change is required to keep the registry boundary coherent.

## Why This Slice Exists

The recent CEL cleanup reduced the builder surface to one public
`build_cel_registry(...)` function, but the current state is still too weak:

- `cel_checker` still parses concept payload structure
- `cel_checker` still accepts mapping-shaped input instead of typed domain
  objects
- malformed entries are silently dropped
- duplicate canonical names still resolve by overwrite
- `STANDARD_SYNTHETIC_BINDING_NAMES` still defines part of the runtime schema
  from inside the checker

That is thinner than before, but it is not yet a principled boundary.

## End State

The intended end state is:

- `propstore.cel_checker` accepts a ready registry of `ConceptInfo` and
  performs checking only
- canonical concept projection is defined over `ConceptRecord`
- world/store projection is defined over typed world/store rows, not generic
  mappings
- conflict detection and compiler code normalize before projection instead of
  asking CEL to normalize for them
- duplicate canonical names and invalid projection input fail immediately

Forbidden end state:

- `cel_checker` still contains payload parsing helpers
- registry builders still accept a grab bag of payload/container shapes
- malformed concept inputs are silently ignored
- synthetic binding names remain hardcoded in the checker

## Architectural Rules

1. No compatibility shims in production.
   Do not preserve both mapping-based and typed registry projection surfaces.

2. Keep source boundaries separate.
   Canonical concept projection and world/store projection are different
   boundaries and may live in different modules.

3. `cel_checker` is not a normalization layer.
   It should not decode JSON, infer kinds from mixed payload shapes, or invent
   missing IDs.

4. Fail hard on bad registry state.
   Duplicate canonical names, missing IDs, missing kinds, or other projection
   violations are boundary errors.

5. Synthetic bindings belong to the environment contract.
   The checker can consume them, but it does not define them.

## Current State

Already completed:

- the old CEL registry builder fan-out was collapsed into one public builder
- the concept-vs-concept mismatch bug was fixed
- arithmetic/ordering kind checks were collapsed into one table-driven helper
- the current CEL slice is on `master`

Remaining registry debt:

- `build_cel_registry(...)` still takes `Iterable[Mapping[str, Any]]`
- `_mapping_form_parameters`, `_kind_type_from_record`, and payload scanning
  still live in `propstore/cel_checker.py`
- `propstore/world/model.py` projects sidecar rows through the checker’s
  mapping-based builder
- `propstore/conflict_detector/orchestrator.py` still has a local payload
  normalization bridge
- `STANDARD_SYNTHETIC_BINDING_NAMES` is still defined in `cel_checker`

## Proposed Module Ownership

### Checker

`propstore/cel_checker.py`

Owns:

- `ConceptInfo`
- `KindType`
- `CelError`
- parser/tokenizer/AST/type-checking
- registry scoping and synthetic-registry augmentation helpers if they operate
  purely on `ConceptInfo`

Does not own:

- projection from canonical concepts
- projection from sidecar/world rows
- environment schema constants

### Canonical Projection

Likely module:

- `propstore/core/concepts.py`
  or
- `propstore/cel_registry.py`

Owns:

- `ConceptRecord -> ConceptInfo`
- `Iterable[ConceptRecord] -> dict[str, ConceptInfo]`

### World Projection

Likely module:

- `propstore/world/model.py`
- `propstore/core/row_types.py`
- or a small dedicated world-side helper module

Owns:

- `ConceptRow` or typed world/store concept row -> `ConceptInfo`
- world-side registry construction for active reasoning and IC-merge inputs

### Environment Contract

Likely module:

- `propstore/core/labels.py`
- `propstore/world/types.py`
- or a new focused module such as `propstore/cel_bindings.py`

Owns:

- standard synthetic binding names
- any binding metadata beyond bare names

## Execution Sequence

### Phase R0: Freeze The Registry Contract In Tests

Commit message:

- `test(cel): freeze registry boundary and duplicate handling`

Work:

- add RED tests that canonical projection requires typed canonical concepts
- add RED tests that duplicate canonical names are rejected
- add RED tests that missing canonical name, artifact ID, or kind fail hard
- add RED tests that synthetic binding names come from the environment contract,
  not `cel_checker`

Target suites:

- `tests/test_cel_checker.py`
- `tests/test_world_model.py`
- `tests/test_conflict_detector.py`
- add focused projection tests if needed

Stop condition:

- the intended failure semantics are encoded before implementation proceeds

### Phase R1: Remove Projection Logic From `cel_checker`

Commit message:

- `refactor(cel): delete payload-based registry projection from checker`

Work:

- remove payload parsing helpers from `propstore/cel_checker.py`
- remove mapping-based `build_cel_registry(...)` from the checker
- keep checker-facing surfaces only:
  - `ConceptInfo`
  - checking functions
  - registry transforms over `ConceptInfo`

Acceptance:

- `cel_checker.py` does not inspect `form`, `form_parameters`, `artifact_id`,
  `id`, or `kind_type`
- `cel_checker.py` no longer imports `json`

### Phase R2: Add Typed Canonical Projection

Commit message:

- `refactor(cel): project canonical concepts from ConceptRecord`

Work:

- add one canonical projection API over `ConceptRecord`
- make compilation context and concept validation use that projection directly
- delete any mapping-based canonical concept adapters created only for CEL

Likely target API:

- `concept_info_from_concept_record(record: ConceptRecord) -> ConceptInfo`
- `build_canonical_cel_registry(records: Iterable[ConceptRecord]) -> dict[str, ConceptInfo]`

Files:

- `propstore/core/concepts.py`
- `propstore/compiler/context.py`
- `propstore/validate_concepts.py`

Acceptance:

- canonical concept paths no longer convert `ConceptRecord` to payload mappings
  just to reach CEL

### Phase R3: Add Typed World/Store Projection

Commit message:

- `refactor(world): project cel registry from typed concept rows`

Work:

- define one world/store projection path from typed concept rows
- update `world/model.py` and `world/resolution.py` to use it
- keep sidecar rows distinct from canonical concept records

Important:

- do not route sidecar rows through canonical concept parsing just to satisfy
  CEL
- do not reintroduce a generic mapping-based builder as a shortcut

Acceptance:

- world/store paths use typed row projection, not generic dict projection

### Phase R4: Hard-Fail Registry Invariants

Commit message:

- `refactor(cel): reject invalid and duplicate registry entries`

Work:

- make duplicate canonical names a hard failure
- make missing ID/name/kind a hard failure at the projection boundary
- update tests and any callers that currently depend on silent skipping

Decision:

- canonical name uniqueness is required for CEL registry construction
- the workstream does not permit last-write-wins behavior

Acceptance:

- there is no silent drop behavior in production registry construction

### Phase R5: Move Synthetic Binding Contract Out Of The Checker

Commit message:

- `refactor(cel): move synthetic binding contract out of checker`

Work:

- move `STANDARD_SYNTHETIC_BINDING_NAMES` to a contract-owning module
- update `with_standard_synthetic_bindings(...)` to consume that contract
- document what each binding means and who owns it

Acceptance:

- `cel_checker.py` does not define the standard synthetic binding schema

## Test Discipline

Use the project wrapper, not bare pytest:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label cel-registry tests/test_cel_checker.py tests/test_conflict_detector.py tests/test_world_model.py tests/test_resolution_helpers.py tests/test_validator.py
```

Expand targeted coverage as phases land:

- `tests/test_contexts.py`
- `tests/test_ic_merge.py`
- `tests/test_z3_conditions.py`

Full-suite closeout:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label cel-registry-full
```

## Suggested First Execution Slice

The first execution slice should be:

1. add RED tests for duplicate canonical names and hard-failure projection
2. delete mapping-based projection from `cel_checker`
3. add `ConceptRecord -> ConceptInfo` projection in the canonical concept layer
4. update compiler context and concept validation

Reason:

- this finishes the canonical boundary first
- it removes the largest remaining architectural lie in the checker
- it avoids mixing canonical and world/store concerns in the same slice

## Explicitly Deferred

Not part of this workstream unless explicitly pulled in later:

- typed AST
- two-pass CEL checking
- span/position-rich diagnostics
- parse error protocol redesign
- Z3 runtime unification beyond the registry boundary

Those are valid follow-on slices, but they are not required to finish the
registry hardening boundary.
