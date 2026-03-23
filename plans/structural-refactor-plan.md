# Structural Refactor Plan

Date: 2026-03-23
Status: In progress

## Goal

Address the structural issues called out for conflict detection, sidecar claim population, shared bound-world resolution helpers, and the CEL/Z3 condition stack. The work will be done incrementally under TDD, with public behavior preserved unless a failing test proves a bug.

## Constraints

- Do the minimum change needed per slice.
- Add or tighten executable tests before moving logic.
- Preserve current public entry points while internals are being extracted.
- Prove each slice with targeted `pytest` runs, then run a broader regression pass.
- Do not disturb unrelated untracked files in the worktree.

## Work Plan

### Slice 1: Characterization tests

Status: Complete

- Add tests that pin current conflict detector behavior by claim type and context path.
- Add tests that pin `_populate_claims()` behavior around derived fields and deferred stances.
- Add tests that pin shared `BoundWorld` / `HypotheticalWorld` resolution behavior.
- Add tests that expose redundant CEL parse/translate work and define the desired cache behavior.

Verification:

- `pytest tests/test_conflict_detector.py tests/test_build_sidecar.py tests/test_world_model.py tests/test_cel_checker.py tests/test_z3_conditions.py`

### Slice 2: Conflict detector package split

Status: Complete

- Convert `propstore/conflict_detector.py` into a package.
- Keep `detect_conflicts`, `detect_transitive_conflicts`, `ConflictClass`, `ConflictRecord`, and existing imports stable.
- Extract shared models/helpers and separate detector modules for:
  - parameters
  - measurements
  - equations
  - algorithms
  - orchestration

Verification:

- `pytest tests/test_conflict_detector.py tests/test_contexts.py tests/test_world_model.py tests/test_z3_conditions.py`

### Slice 3: CEL pipeline unification and caching

Status: Complete

- Make the CEL parser AST the single parse representation for the Z3 path.
- Add caches in `Z3ConditionSolver` for parsed expressions and translated normalized condition sets.
- Reuse compiled conditions across `are_disjoint`, `are_equivalent`, and equivalence partitioning.
- Route condition classification through the shared compiled path before fallback parsing.

Verification:

- `pytest tests/test_cel_checker.py tests/test_z3_conditions.py tests/test_conflict_detector.py tests/test_contexts.py`

### Slice 4: Sidecar claim population refactor

Status: Complete

- Split `_populate_claims()` into claim preparation and DB insertion responsibilities.
- Extract type-specific claim normalization.
- Extract derived-field generation for SymPy, canonical AST, summaries, and provenance/context handling.
- Preserve DB schema and inserted values.

Verification:

- `pytest tests/test_build_sidecar.py tests/test_claim_notes.py tests/test_graph_export.py tests/test_sensitivity.py`

### Slice 5: Shared world resolver refactor

Status: Complete

- Replace `_value_of_from_active` and `_derived_value_impl` free functions with a shared resolver abstraction or shared base-level methods.
- Use the same shared logic from both `BoundWorld` and `HypotheticalWorld`.
- Preserve value, conflict, and derived-value behavior.

Verification:

- `pytest tests/test_world_model.py tests/test_contexts.py`

### Slice 6: Full regression pass

Status: Complete

- Run the broader suite covering conflicts, sidecar building, world model behavior, contexts, CEL, and Z3 reasoning.
- Update this plan with final status and any residual risks if failures remain outside the touched scope.

Verification:

- `pytest tests/test_conflict_detector.py tests/test_build_sidecar.py tests/test_world_model.py tests/test_contexts.py tests/test_cel_checker.py tests/test_z3_conditions.py`

## Progress Log

- 2026-03-23: Plan created.
- 2026-03-23: Slice 1 started. Existing tests already cover most outward behavior for conflict detection, sidecar building, and bound/hypothetical worlds. Additional tests will focus on CEL/Z3 reuse and any narrow seams needed for safe extraction.
- 2026-03-23: Completed the conflict detector package split. `ConflictClass` / `ConflictRecord`, context helpers, collectors, and detector strategies now live in separate modules behind the same public entry point.
- 2026-03-23: Completed the CEL reuse slice. `Z3ConditionSolver` now caches parsed conditions and normalized condition sets, and `classify_conditions()` can reuse a supplied solver so `detect_conflicts()` shares one compiled Z3 path per run.
- 2026-03-23: Slice 4 started. `_populate_claims()` will be reduced to iteration and insertion by extracting claim preparation and deferred stance handling.
- 2026-03-23: Completed the sidecar claim-population refactor. `_populate_claims()` now delegates to helpers for valid-id collection, typed field extraction, equation/algorithm derived fields, and deferred stance extraction.
- 2026-03-23: Completed the shared world-resolver refactor. `BoundWorld` and `HypotheticalWorld` now use `world/value_resolver.py` instead of module-level helper functions.
- 2026-03-23: Slice 6 started. Running broader regression across detector, sidecar, world, context, CEL, and related integration suites.
- 2026-03-23: Full regression passed.
  `uv run pytest tests/test_conflict_detector.py tests/test_build_sidecar.py tests/test_world_model.py tests/test_contexts.py tests/test_cel_checker.py tests/test_z3_conditions.py tests/test_claim_notes.py tests/test_graph_export.py tests/test_sensitivity.py tests/test_property.py -q`
  Result: `401 passed` with existing parameterization-evaluation warnings.
