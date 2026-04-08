# Proposal: Claim Compiler Middle-End Extraction

**Date:** 2026-04-08
**Status:** Proposed
**Grounded in:** local codebase review of `propstore/validate_claims.py`, `propstore/sidecar/build.py`, `propstore/sidecar/claim_utils.py`, `propstore/sidecar/claims.py`, `propstore/world/model.py`, `propstore/world/bound.py`, `propstore/world/resolution.py`, `propstore/conflict_detector/*`, and `propstore/cli/compiler_cmds.py`

---

## Goal

Extract an explicit compiler middle-end for claims so that:

- authored YAML is normalized, bound, and type-checked once
- semantic information is preserved as typed IR instead of discarded as diagnostics
- sidecar lowering consumes semantic IR instead of re-resolving raw dicts
- `pks validate` and `pks build` share the same semantic pipeline
- runtime consumers continue to read the compiled sidecar and do not become validation-time dependencies

This is not a plan to make `validate_claims.py` larger.

This is a plan to split the current implicit pipeline into explicit phases.

---

## Current Shape

Today the pipeline is already compiler-shaped, but the boundaries are implicit and duplicated.

### Front-end work that already exists

- YAML parsing via `load_yaml_entries()` and `load_claim_files()`
- legacy identity normalization via `normalize_claim_file_payload()`
- schema validation in `validate_claims()`
- semantic checks in `validate_claims()`:
  - logical ID checks
  - claim artifact/version checks
  - CEL checks
  - unit compatibility checks
  - bridgman dimensional checks
  - sympy parse checks
  - algorithm AST parse and unbound-name checks
  - stance target existence checks

### Middle-end work that exists but is not explicit

- concept binding through `build_concept_registry*()` and `resolve_concept_reference()`
- claim binding through `collect_claim_reference_map()` and `resolve_claim_reference()`
- normalization to canonical authored forms before storage

### Back-end work that already exists

- storage lowering in `prepare_claim_insert_row()`
- SQL row emission in `insert_claim_row()` and `populate_claims()`
- sidecar orchestration in `build_sidecar()`
- runtime query/reasoning over sidecar in `WorldModel` and `BoundWorld`

### Primary architectural problems

1. Semantic analysis is computed and then thrown away.
2. Reference resolution and identity normalization are duplicated across validation and build.
3. Symbol-table construction is duplicated across validation, sidecar build, and runtime reconstruction.
4. Alias resolution does not preserve match provenance.
5. Some runtime code reconstructs source-shaped claims from compiled rows, which signals an unclear IR boundary.

---

## Non-Negotiable Constraints

These must remain true throughout the refactor.

### Validation constraints

- `pks validate` must run without building a sidecar.
- validation must operate over authored inputs, not compiled outputs
- diagnostics must remain available even if lowering is not run
- draft rejection and schema checks must remain front-end behavior

### Build constraints

- `pks build` must use the same semantic pipeline as `pks validate`
- lowering must not re-resolve already-resolved references
- sidecar schema and `WorldModel` behavior must remain stable until an explicit schema change is planned

### Runtime constraints

- `WorldModel` and `BoundWorld` continue to consume the sidecar, not authored YAML
- query-time registries may remain separate from authored-input compilation context
- no runtime dependency on validation-only code paths

### Identity constraints

- concept lookup namespace and claim lookup namespace must remain distinct
- match provenance must be preserved once IR exists
- authored-input symbol tables must not be built from sidecar state

---

## Target Architecture

The target pipeline is:

`LoadedEntry YAML -> normalized authored representation -> bound semantic IR -> lowered storage rows -> sidecar -> runtime models`

### Phase ownership

#### Front-end

Owns:

- YAML loading
- schema validation
- legacy payload normalization
- authored-input symbol-table construction

Does not own:

- SQL lowering
- SI normalization for storage
- runtime query concerns

#### Middle-end

Owns:

- concept reference binding
- claim reference binding
- typed semantic checks
- CEL validation
- unit and dimensional validation
- algorithm body binding checks
- structured semantic IR emission

Does not own:

- SQL row creation
- sidecar writes
- world/runtime resolution

#### Back-end

Owns:

- IR to row lowering
- SI normalization for numeric storage
- generated sympy persistence
- canonical AST persistence
- SQL emission
- sidecar indexing and derived tables

---

## New Core Types

### `CompilationContext`

Introduce a single immutable authored-input compilation context.

Recommended shape:

```python
@dataclass(frozen=True)
class CompilationContext:
    form_registry: dict[str, FormDefinition]
    context_ids: frozenset[str]
    concept_records: dict[str, ConceptRecord]
    concept_lookup: ConceptLookupIndex
    claim_lookup: ClaimLookupIndex
    cel_registry: dict[str, ConceptInfo]
```

This replaces duplicated registry construction in:

- `validate_claims.build_concept_registry_from_paths()`
- inline concept registry construction in `sidecar/build.py`
- ad hoc claim reference map creation in `claim_utils.py`

### `ResolvedReference`

Every bound reference in semantic IR should preserve how it resolved.

Recommended shape:

```python
@dataclass(frozen=True)
class ResolvedReference:
    raw_text: str
    resolved_id: str | None
    target_kind: Literal["concept", "claim"]
    matched_by: str | None
    matched_text: str | None
    ambiguous_candidates: tuple[str, ...] = ()
```

### Semantic IR

Recommended initial IR:

- `SemanticClaimFile`
- `SemanticClaim`
- `SemanticStance`
- `SemanticVariable`
- `SemanticDiagnostic`

The first version should stay close to current claim schema fields to minimize migration risk.

---

## Execution Plan

## Phase 0: Lock Current Behavior

Goal:

Add characterization tests before changing architecture.

Deliverables:

- fixtures covering representative claim types
- tests for current validation diagnostics
- tests for sidecar rows emitted from fixed fixtures
- tests for concept and claim reference resolution behavior

Acceptance:

- current `validate` and `build` behavior is captured in tests

Suggested test surfaces:

- `tests/test_validate_claims_*.py`
- `tests/test_sidecar_build_*.py`
- `tests/test_claim_reference_resolution_*.py`

## Phase 1: Introduce `CompilationContext`

Goal:

Unify authored-input symbol tables without changing public behavior.

Tasks:

- add `propstore/compiler/context.py`
- move concept/form/CEL/context registry construction there
- move claim lookup map construction there
- keep claim and concept lookup indices separate
- make the context immutable

Refactor targets:

- `propstore/validate_claims.py`
- `propstore/sidecar/build.py`
- `propstore/sidecar/claim_utils.py`
- possibly small shared helpers extracted from `sidecar/concept_utils.py`

Acceptance:

- `validate_claims()` and `build_sidecar()` can both consume the same context
- no semantic behavior change
- duplicate concept registry construction in `build.py` is removed

## Phase 2: Extract Pure Semantic Passes

Goal:

Break `validate_claims()` into explicit reusable passes.

Tasks:

- extract authored-claim normalization pass
- extract identity validation pass
- extract concept-binding pass
- extract claim-binding pass for stances
- extract CEL checking pass
- extract unit and dimension pass
- extract algorithm AST checking pass

Implementation rule:

- each pass returns structured outputs plus diagnostics
- no pass writes SQL or mutates global registries

Acceptance:

- `validate_claims()` becomes orchestration over pass functions
- all existing diagnostics still appear

## Phase 3: Introduce Semantic IR

Goal:

Preserve semantic results instead of discarding them.

Tasks:

- define IR dataclasses in `propstore/compiler/ir.py`
- emit semantic claims from the pass pipeline
- attach resolved-reference provenance
- attach typed/checked fields to semantic claims
- attach per-claim/per-file diagnostics

Design rule:

- keep IR close to authored claim shapes first
- do not over-normalize the first version

Acceptance:

- the pipeline can produce semantic IR plus diagnostics for all existing claim types
- `validate_claims()` can ignore lowering and still report full diagnostics

## Phase 4: Make `validate_claims()` a Thin Wrapper

Goal:

Keep the CLI surface stable while moving semantics underneath it.

Tasks:

- keep `validate_claims(claim_files, ...) -> ValidationResult`
- implement it by running the compiler front-end and middle-end
- convert semantic diagnostics to the existing `ValidationResult`

Acceptance:

- CLI output remains compatible
- no sidecar build is required for validation

## Phase 5: Refactor Sidecar Lowering To Consume IR

Goal:

Remove duplicate binding/resolution from build-time lowering.

Tasks:

- update `prepare_claim_insert_row()` to accept semantic claims
- stop calling `canonicalize_claim_for_storage()` on raw dicts
- lower already-resolved concept IDs and claim IDs directly
- keep SI normalization, generated sympy, and canonical AST in lowering

Important boundary:

- semantic passes decide what a reference means
- lowering decides how to persist it

Acceptance:

- sidecar row contents are unchanged for existing fixtures
- duplicate concept and claim re-resolution code is removed

## Phase 6: Clean Up Duplicated Resolution Helpers

Goal:

Delete superseded ad hoc binding paths.

Candidates:

- duplicated concept registry logic
- duplicated claim lookup map logic
- fallback re-resolution paths in sidecar lowering

Acceptance:

- one authored-input resolution path remains
- one runtime sidecar-resolution path remains

## Phase 7: Optional Follow-On Migrations

These are explicitly out of the critical path for middle-end extraction.

Possible later work:

- migrate conflict detection to consume semantic IR rather than raw `LoadedEntry`
- reduce runtime source-shape reconstruction in `BoundWorld`
- introduce a compiled semantic graph IR above SQL rows if needed

Do not mix these into Phases 1 through 5.

---

## File Plan

### New files

- `propstore/compiler/__init__.py`
- `propstore/compiler/context.py`
- `propstore/compiler/ir.py`
- `propstore/compiler/passes.py`
- `propstore/compiler/diagnostics.py`

### Existing files likely to change

- `propstore/validate_claims.py`
- `propstore/sidecar/build.py`
- `propstore/sidecar/claim_utils.py`
- `propstore/sidecar/claims.py`
- `propstore/sidecar/concept_utils.py`
- `propstore/cli/compiler_cmds.py`

### Existing files intentionally not in first-wave scope

- `propstore/world/model.py`
- `propstore/world/bound.py`
- `propstore/world/resolution.py`
- `propstore/conflict_detector/*`

These should only receive compatibility adjustments if required.

---

## Testing Plan

Every phase should end with kept test coverage before moving on.

### Required test categories

- legacy authored claim normalization
- logical ID uniqueness and version ID behavior
- concept binding by artifact ID, canonical name, logical ID, and alias
- claim binding by artifact ID, logical ID, and local handle
- stance target resolution across files
- CEL diagnostics
- unit compatibility diagnostics
- dimensional diagnostics for equations
- algorithm AST parse and unbound-name diagnostics
- sidecar row equivalence before and after lowering refactor

### Command rule

Run pytest as:

```bash
uv run pytest -vv
```

and tee full output to timestamped logs under `logs/test-runs/`.

---

## Risks

### Risk 1: Context becomes a mutable grab-bag

Mitigation:

- make `CompilationContext` immutable
- treat pass outputs as new values, not in-place mutations

### Risk 2: Validation starts depending on build-time lowering

Mitigation:

- keep validation stopping at semantic IR
- keep lowering and SQL emission downstream only

### Risk 3: Claim and concept namespaces get collapsed

Mitigation:

- separate `concept_lookup` and `claim_lookup`
- separate concept and claim resolution APIs

### Risk 4: Refactor widens scope into runtime redesign

Mitigation:

- hold `WorldModel`, `BoundWorld`, and conflict detector constant until semantic IR is stable

### Risk 5: Provenance of alias resolution is lost again

Mitigation:

- require `ResolvedReference` in semantic IR
- do not store only final IDs when the pass had to choose among lookup surfaces

---

## Recommended Execution Order

This plan should be executed one target surface at a time.

Recommended first slices:

1. Add characterization tests.
2. Add immutable `CompilationContext` and route `validate` and `build` through it.
3. Extract concept and claim binding passes.
4. Add `ResolvedReference` and semantic claim IR.
5. Move sidecar lowering to semantic IR.
6. Delete duplicated authored-input resolution code.

If two consecutive slices on the same target do not yield a kept simplification, stop and reassess rather than widening scope.

---

## Definition Of Done

This proposal is complete when:

- `validate_claims()` is a thin wrapper over reusable semantic passes
- authored-input symbol-table construction exists in one place
- semantic IR exists and carries resolution provenance
- sidecar lowering consumes semantic IR instead of raw dicts
- duplicate authored-input re-resolution paths are removed
- `pks validate`, `pks build`, and current sidecar/runtime behavior remain intact

At that point, claim validation will no longer merely look like a compiler front-end.

It will be one.
