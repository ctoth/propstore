# Legacy Surface Removal Workstream

**Date:** 2026-04-09  
**Status:** Executable  
**Scope:** remove legacy/compatibility concepts from production claim/concept identity surfaces without attempting strict typing yet

---

## Goal

Get the system to a state where production code no longer models claim/concept identity through explicit `legacy`, `obsolete`, or compatibility-bridge concepts.

This workstream is intentionally narrower than a full typing pass.

At the end of this workstream:

- production code should not have a `legacy concept registry` concept
- production code should not silently normalize raw authored claim IDs into canonical claim identity
- production code should not describe raw `id` usage as an "obsolete" compatibility mode; it should simply reject it
- production code should not support legacy list-valued claim payloads
- production code may still pass `dict` payloads around

Strict typing is a later workstream.

---

## Non-Goals

This workstream does not:

1. convert the whole pipeline to typed domain objects
2. eliminate all `dict[str, Any]` usage
3. redesign the entire source workflow
4. change the whole plugin authoring model

---

## Current Production Legacy Surfaces

### 1. Legacy concept-registry compatibility path

Current code still names and builds an internal legacy registry shape:

- [context.py](C:/Users/Q/code/propstore/propstore/compiler/context.py)
  - `compilation_context_from_legacy_registry()`
  - `legacy_concept_registry_for_context()`
  - `legacy_concept_registry_for_context_payloads()`
  - `build_legacy_concept_registry_from_paths()`
- [passes.py](C:/Users/Q/code/propstore/propstore/compiler/passes.py)
  - imports and uses `legacy_concept_registry_for_context(...)`
- [validate_claims.py](C:/Users/Q/code/propstore/propstore/validate_claims.py)
  - imports and uses the same legacy-registry helpers
- [build.py](C:/Users/Q/code/propstore/propstore/sidecar/build.py)
  - imports the same legacy-registry helper family

### 2. Legacy-authored claim normalization

Current code still silently upgrades raw `id` claim payloads:

- [passes.py](C:/Users/Q/code/propstore/propstore/compiler/passes.py)
  - `_normalize_claim_entries()`
  - `needs_legacy_normalization`
  - `normalize_claim_file_payload(...)`

### 3. "Obsolete raw id" wording

Current code still treats raw `id` as an obsolete compatibility form:

- [passes.py](C:/Users/Q/code/propstore/propstore/compiler/passes.py)
- [validate.py](C:/Users/Q/code/propstore/propstore/validate.py)
- [test_validator.py](C:/Users/Q/code/propstore/tests/test_validator.py)

### 4. Legacy list-valued claim support

Current code still supports the old list value shape:

- [value_comparison.py](C:/Users/Q/code/propstore/propstore/value_comparison.py)
- [test_build_sidecar.py](C:/Users/Q/code/propstore/tests/test_build_sidecar.py)

### 5. Legacy concept fallback in sidecar concept utilities

Current code still manufactures a synthetic `legacy` namespace/value fallback:

- [concept_utils.py](C:/Users/Q/code/propstore/propstore/sidecar/concept_utils.py)

---

## Workstream Principle

Delete the legacy concepts first.

Do not introduce a new typed replacement in the same workstream unless required to keep production code runnable.
If a production path still needs a dict-shaped helper after this cleanup, that is acceptable here.
What is not acceptable is continuing to model it as `legacy`.

---

## Refactor Method

Use `rope` by default for symbol renames in this workstream.

Why:

- Phase 1 is primarily a symbol-surface cleanup
- blind string replacement is unnecessary risk
- the repo already has `rope` and `libcst` available

Method rules:

1. Use `rope` for production/test symbol renames when the old and new names are both Python identifiers.
2. Use direct file edits only for:
   - diagnostic strings
   - comments/docstrings
   - non-identifier text
   - small structural deletions
3. Use `libcst` only if `rope` cannot safely express a needed tree rewrite.
4. After each `rope` rename, inspect the diff before continuing to the next rename.
5. Do not batch unrelated renames into one step.

Preferred Phase 1 rename order:

1. `compilation_context_from_legacy_registry` -> `compilation_context_from_concept_registry`
2. `legacy_concept_registry_for_context_payloads` -> `concept_registry_for_context_payloads`
3. `legacy_concept_registry_for_context` -> `concept_registry_for_context`
4. `build_legacy_concept_registry_from_paths` -> `build_concept_registry_from_paths`

Local variable renames after symbol renames:

1. `legacy_registry` -> `concept_registry`
2. `legacy_concept_registry` -> `concept_registry`

---

## Execution Order

Run the phases in this exact order:

1. Phase 1: legacy concept-registry naming removal
2. Phase 2: raw-id claim normalization deletion
3. Phase 3: raw-id wording cleanup
4. Phase 4: list-valued claim support deletion
5. Phase 5: synthetic legacy concept fallback deletion

Do not reorder them.

Reason:

- Phase 1 removes the internal compatibility vocabulary first.
- Phase 2 removes the strongest silent compatibility behavior.
- Phase 3 cleans up the remaining framing.
- Phase 4 and Phase 5 remove the residual value/concept legacy fallbacks.

---

## Slice Rule

Each phase is executed as one or more bounded slices.

For each slice:

1. touch only the files named for that phase
2. run the narrowest relevant tests first
3. keep the slice only if it produces a kept reduction
4. revert the slice if it produces no kept reduction
5. after a kept slice, rerun the phase tests before moving on

If two consecutive slices in the same phase produce no kept reduction, stop the workstream and report the blocked phase.

---

## Phase 1: Delete The Legacy Concept-Registry Concept

### Intent

Remove the idea that compiler/validator/sidecar code depends on a "legacy concept registry".

### Work

1. Rename the helper family in [context.py](C:/Users/Q/code/propstore/propstore/compiler/context.py) to neutral names such as:
   - `compilation_context_from_concept_registry()`
   - `concept_registry_for_context()`
   - `concept_registry_for_context_payloads()`
   - `build_concept_registry_from_paths()`
2. Update all production imports/callers.
3. Update tests that reference the old helper names.
4. Remove the word `legacy` from production helper names and production diagnostics for this registry shape.

### Files

- [context.py](C:/Users/Q/code/propstore/propstore/compiler/context.py)
- [passes.py](C:/Users/Q/code/propstore/propstore/compiler/passes.py)
- [validate_claims.py](C:/Users/Q/code/propstore/propstore/validate_claims.py)
- [build.py](C:/Users/Q/code/propstore/propstore/sidecar/build.py)
- [__init__.py](C:/Users/Q/code/propstore/propstore/compiler/__init__.py)
- [test_claim_compiler.py](C:/Users/Q/code/propstore/tests/test_claim_compiler.py)

### Execution Method

1. run one `rope` rename
2. inspect the affected files
3. apply any necessary local variable / docstring cleanup with direct edits
4. run the Phase 1 tests
5. keep or revert before the next rename

### Phase Tests

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
uv run pytest -vv tests/test_claim_compiler.py tests/test_validator.py 2>&1 | Tee-Object "logs/test-runs/$ts-phase1-legacy-registry.log"
```

### Exit Criteria

1. No production symbol name contains `legacy_concept_registry`.
2. No production path imports `compilation_context_from_legacy_registry`.
3. The compiler, validator, and sidecar still build/run with the neutral helper names.

---

## Phase 2: Delete Raw-Id Claim Normalization

### Intent

Stop silently rewriting raw authored claim IDs into canonical identity.

### Work

1. Delete `_normalize_claim_entries()` from [passes.py](C:/Users/Q/code/propstore/propstore/compiler/passes.py).
2. Delete the compiler call to `normalize_claim_file_payload(...)` from the claim compilation path.
3. Make raw `id` claims fail at the boundary rather than normalize in flight.
4. Update tests that currently expect silent normalization.

### Files

- [passes.py](C:/Users/Q/code/propstore/propstore/compiler/passes.py)
- [identity.py](C:/Users/Q/code/propstore/propstore/identity.py)
- [validate_claims.py](C:/Users/Q/code/propstore/propstore/validate_claims.py)
- affected claim compiler / sidecar tests if breakage reaches them

### Execution Method

1. delete `_normalize_claim_entries()`
2. delete the call site in `compile_claim_files(...)`
3. make the boundary fail directly on raw `id`
4. update only the tests broken by this behavior change
5. run the Phase 2 tests before touching wording

### Phase Tests

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
uv run pytest -vv tests/test_claim_compiler.py tests/test_build_sidecar.py tests/test_source_claims.py 2>&1 | Tee-Object "logs/test-runs/$ts-phase2-raw-id-cut.log"
```

### Exit Criteria

1. Claim compilation never mints canonical identity from a raw authored claim file.
2. Raw authored `id` input fails directly.
3. No production claim path contains `needs_legacy_normalization`.

---

## Phase 3: Delete Legacy/Obsolete Wording For Raw Id

### Intent

Raw `id` is not a legacy mode we support. It is simply invalid input.

### Work

1. Replace messages like `uses obsolete raw 'id'` with plain rejection text such as:
   - `raw 'id' is not allowed; use artifact_id and logical_ids`
2. Update tests to match the non-compat framing.

### Files

- [passes.py](C:/Users/Q/code/propstore/propstore/compiler/passes.py)
- [validate.py](C:/Users/Q/code/propstore/propstore/validate.py)
- [test_validator.py](C:/Users/Q/code/propstore/tests/test_validator.py)

### Execution Method

1. replace compatibility-framed diagnostic text
2. keep the logic unchanged in this phase
3. update exact test expectations
4. run the Phase 3 tests

### Phase Tests

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
uv run pytest -vv tests/test_validator.py 2>&1 | Tee-Object "logs/test-runs/$ts-phase3-raw-id-wording.log"
```

### Exit Criteria

1. Production raw-id diagnostics describe invalid input, not obsolete compatibility.

---

## Phase 4: Delete Legacy List-Value Support

### Intent

Stop carrying the old list-valued claim representation.

### Work

1. Remove legacy list parsing/fallbacks from [value_comparison.py](C:/Users/Q/code/propstore/propstore/value_comparison.py).
2. Ensure list-valued claims fail at the authored-input boundary.
3. Update tests from "legacy list format" language to plain invalid-shape language.

### Files

- [value_comparison.py](C:/Users/Q/code/propstore/propstore/value_comparison.py)
- [test_build_sidecar.py](C:/Users/Q/code/propstore/tests/test_build_sidecar.py)
- any direct value-comparison tests touched by fallout

### Execution Method

1. delete list-value fallback logic
2. keep only named-field parsing
3. update invalid-shape tests
4. run the Phase 4 tests

### Phase Tests

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
uv run pytest -vv tests/test_build_sidecar.py tests/test_value_comparison_units.py 2>&1 | Tee-Object "logs/test-runs/$ts-phase4-list-values.log"
```

### Exit Criteria

1. No production numeric comparison helper accepts list-valued claim payloads.
2. List-valued claims are rejected instead of interpreted.

---

## Phase 5: Delete Synthetic Legacy Concept Fallbacks

### Intent

Stop manufacturing fake `legacy` logical IDs for concepts during sidecar preparation.

### Work

1. Remove the synthetic `legacy` namespace fallback from [concept_utils.py](C:/Users/Q/code/propstore/propstore/sidecar/concept_utils.py).
2. Make concept identity requirements explicit where sidecar prep needs them.
3. Update affected tests.

### Files

- [concept_utils.py](C:/Users/Q/code/propstore/propstore/sidecar/concept_utils.py)
- [build.py](C:/Users/Q/code/propstore/propstore/sidecar/build.py)
- directly affected sidecar tests

### Execution Method

1. delete synthetic `legacy` logical-id fallback generation
2. make required concept identity explicit at use sites
3. update the smallest set of affected tests
4. run the Phase 5 tests

### Phase Tests

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
uv run pytest -vv tests/test_build_sidecar.py tests/test_claim_compiler.py 2>&1 | Tee-Object "logs/test-runs/$ts-phase5-concept-fallback.log"
```

### Exit Criteria

1. No production code manufactures a `legacy` namespace/value for concept identity.

---

## Verification

For each phase:

1. keep the reduction if tests pass
2. revert the slice if it produces no kept improvement
3. do not widen scope within the same slice

Required test runs:

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
uv run pytest -vv tests/test_claim_compiler.py tests/test_validator.py tests/test_build_sidecar.py 2>&1 | Tee-Object "logs/test-runs/$ts-legacy-surface-removal.log"
```

Add targeted tests as needed for any touched production path.

Full phase-close run:

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
uv run pytest -vv tests/test_claim_compiler.py tests/test_validator.py tests/test_build_sidecar.py tests/test_source_claims.py 2>&1 | Tee-Object "logs/test-runs/$ts-legacy-surface-removal-close.log"
```

---

## Completion Criteria

This workstream is complete only when all of the following are true:

1. No production helper or production concept uses `legacy concept registry` naming.
2. No production claim compilation path silently normalizes raw `id`.
3. No production diagnostic frames raw `id` as an obsolete compatibility mode.
4. No production code accepts legacy list-valued claim payloads.
5. No production code synthesizes `legacy` concept logical IDs.
6. Dict-based representations may still exist, but none of the above legacy concepts remain in production code.

---

## Follow-On

After this workstream, start the strict typing workstream:

1. freeze one representation per stage
2. replace `dict` domain objects with explicit dataclasses or other typed domain objects
3. push typed boundaries inward from decode/encode edges

---

## Ready-To-Run First Slice

Start with Phase 1 only.

Immediate first slice:

1. run the first `rope` rename:
   `compilation_context_from_legacy_registry` -> `compilation_context_from_concept_registry`
2. update production imports in:
   - [passes.py](C:/Users/Q/code/propstore/propstore/compiler/passes.py)
   - [validate_claims.py](C:/Users/Q/code/propstore/propstore/validate_claims.py)
   - [build.py](C:/Users/Q/code/propstore/propstore/sidecar/build.py)
   - [__init__.py](C:/Users/Q/code/propstore/propstore/compiler/__init__.py)
3. update [test_claim_compiler.py](C:/Users/Q/code/propstore/tests/test_claim_compiler.py)
4. run the Phase 1 tests
5. keep or revert

Then continue through the remaining Phase 1 renames one at a time in the preferred rename order above.
