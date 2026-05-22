# Runtime Condition Scope Activation Workstream - 2026-05-22

## Purpose

Fix the full-suite ATMS/revision failures exposed by deleting the activation
fallback reparse path.

The failure is desirable evidence: persisted checked condition artifacts now
enforce their registry fingerprint. The remaining bug is that activation still
turns runtime environment/queryable CEL into fake checked condition sets under
a runtime-expanded registry, then compares them to persisted `conditions_ir`
checked under the store registry.

## Governing Principles

- Persisted authored conditions keep strict registry fingerprints.
- Runtime environment/queryable assumptions are runtime constraints, not
  persisted checked artifacts.
- Activation does not reparse persisted claim condition sources.
- Activation does not create replacement solvers, wrapper solvers, fallback
  branches, compatibility paths, adapters, aliases, or dual old/new paths.
- Runtime condition typing lives in the condition owner layer, not in ATMS,
  CLI, tests, or per-caller field lists.
- The type system and CEL AST carry runtime assumption shape. Do not hardcode
  per-field or per-model condition names.
- Delete the wrong production surface first, then use type/test/search failures
  as the work queue.

## Exact Final State

- `propstore/core/activation.py` never calls `ConditionSolver(...)`.
- `propstore/core/activation.py` never imports or calls
  `with_standard_synthetic_bindings`.
- `propstore/core/activation.py` never wraps runtime binding/queryable CEL in
  `checked_condition_set(...)`.
- `_solver_with_environment_bindings` is deleted.
- Persisted checked-condition mismatch still raises
  `Z3TranslationError("Checked condition was validated against a different condition registry")`.
- Runtime environment/queryable assumptions are lowered as non-persisted
  runtime `ConditionIR` and projected into the existing solver context.
- Unknown runtime assumption symbols are typed from the runtime CEL expression
  and environment bindings through one condition-owner API.
- Runtime symbols already present in the canonical/store registry use the
  canonical/store semantics.
- Runtime symbols absent from the canonical/store registry are local to the
  runtime assumption scope and never become persisted registry entries.
- Docs contain no live reference to deleted production path
  `propstore/core/analyzers.py`.
- The targeted failing tests, package pyright gate, and full logged pytest suite
  pass.

## Owner Boundaries

- `propstore.core.conditions.cel_frontend` owns CEL parsing, type checking, and
  lowering source CEL into `ConditionIR`.
- `propstore.core.conditions.solver.ConditionSolver` owns Z3 projection and
  semantic comparison of persisted checked conditions against runtime IR
  constraints.
- `propstore.core.activation` owns collection of environment binding/effective
  assumption CEL from `Environment` and calls the condition-owner API.
- `propstore.world.atms` owns ATMS replay/future enumeration only. It does not
  lower CEL, expand registries, bypass fingerprints, or reinterpret condition
  source strings.
- `propstore.cli` remains a presentation adapter and receives no condition
  semantics.
- Tests express the contract; they do not own runtime condition conversion
  helpers.

## Forbidden Surfaces

- `_solver_with_environment_bindings`
- `ConditionSolver(` inside `propstore/core/activation.py`
- `with_standard_synthetic_bindings` inside `propstore/core/activation.py`
- `checked_condition_set(` inside `propstore/core/activation.py`
- `check_condition_ir(` inside `propstore/core/activation.py`
- `claim_conditions.sources` in activation or ATMS runtime paths
- `except Z3TranslationError` fallback branches in activation
- condition fingerprint superset acceptance
- compatibility language or behavior for old condition shapes
- wrapper/adaptor methods around the new condition-owner API
- per-field condition-name lists outside CEL parsing/lowering
- stale live docs pointing at `propstore/core/analyzers.py`

## Deletion Targets

1. Delete `_solver_with_environment_bindings` from
   `propstore/core/activation.py`.
2. Delete the `ConceptInfo`, `KindType`, and `with_standard_synthetic_bindings`
   imports from `propstore/core/activation.py`.
3. Delete activation's runtime `checked_condition_set(check_condition_ir(...))`
   construction.
4. Delete stale live documentation references to
   `propstore/core/analyzers.py`.

## Target Condition API

Add one generic condition-owner surface:

- A CEL frontend/runtime-scope function lowers runtime CEL sources to
  `ConditionIR` without creating `CheckedCondition` or
  `CheckedConditionSet`.
- The function receives:
  - base canonical/store registry from `ConditionSolver.registry`;
  - runtime environment bindings from `Environment.bindings`;
  - runtime CEL sources from `_binding_conditions(environment)`.
- The function uses canonical/store semantics for names present in the base
  registry.
- The function types runtime-only names from the CEL AST and runtime binding
  values:
  - numeric literal/binding means quantity;
  - boolean literal/binding means boolean;
  - string literal/binding means extensible category;
  - unknown or ambiguous runtime-only references raise a hard `ValueError`.
- The function returns runtime `ConditionIR` values only. It does not return a
  registry fingerprint and does not mutate the persisted registry.

Add one generic solver surface:

- `ConditionSolver` compares persisted checked conditions against runtime
  `ConditionIR` constraints in the solver's existing Z3 context.
- The persisted side still passes the existing fingerprint check.
- The runtime side has no persisted fingerprint and is projected directly from
  `ConditionIR`.
- Existing checked-vs-checked APIs keep their current strict behavior.

## Ordered Execution

### Phase 1 - Delete Activation Registry Expansion

1. Read:
   - `propstore/core/activation.py`
   - `propstore/core/conditions/cel_frontend.py`
   - `propstore/core/conditions/solver.py`
   - `propstore/core/conditions/checked.py`
   - `propstore/core/conditions/ir.py`
   - `propstore/core/conditions/z3_backend.py`
2. Delete `_solver_with_environment_bindings`.
3. Delete activation imports made unnecessary by that deletion.
4. Delete runtime `checked_condition_set(check_condition_ir(...))`
   construction from activation.
5. Leave activation temporarily failing while the owner APIs are added.

### Phase 2 - Add Runtime CEL Lowering In The Condition Owner

1. Add runtime CEL lowering in `propstore/core/conditions/cel_frontend.py`.
2. Runtime lowering returns `ConditionIR`, never `CheckedCondition`.
3. Runtime-only symbol typing is derived from parsed CEL and environment
   bindings, never from hardcoded field names.
4. Runtime lowering hard-fails ambiguous runtime-only symbols.
5. Add focused tests in condition tests for:
   - persisted `x == 1` checked under registry `x`;
   - runtime `y == 2` lowered without a persisted fingerprint;
   - runtime symbol `x` using canonical/store semantics;
   - ambiguous runtime-only symbol hard failure;
   - existing checked-condition fingerprint mismatch still failing.

### Phase 3 - Add Solver Runtime-IR Comparison

1. Add one `ConditionSolver` API for checked conditions versus runtime
   `ConditionIR` constraints.
2. Reuse existing Z3 projection machinery.
3. Keep `_require_matching_fingerprint` unchanged for persisted checked
   conditions.
4. Add tests proving:
   - checked-vs-checked mismatch still raises;
   - checked-vs-runtime-IR does not require a runtime fingerprint;
   - runtime-IR constraints can be disjoint or overlapping with persisted
     checked conditions.

### Phase 4 - Wire Activation To The Owner API

1. `is_claim_active()` collects `_binding_conditions(environment)`.
2. Activation calls the condition-owner runtime lowering function with
   `solver.registry`, `environment.bindings`, and the binding/effective
   assumption CEL.
3. Activation calls the new solver checked-vs-runtime-IR API.
4. Activation catches only `ValueError` for unknown CEL concept reporting
   through `UnknownConceptInCEL`.
5. Activation does not catch `Z3TranslationError`.

### Phase 5 - Fix Live Doc Drift

1. Update `docs/argumentation-package-boundary.md`.
2. Update other live docs that mention `propstore/core/analyzers.py` and are
   covered by `tests/test_doc_drift_clean.py`.
3. Do not edit historical workstreams or historical inventories for this doc
   drift gate.

### Phase 6 - Gates

Run these exact gates:

```powershell
rg -n -F -- "_solver_with_environment_bindings" propstore tests
rg -n -F -- "ConditionSolver(" propstore/core/activation.py
rg -n -F -- "with_standard_synthetic_bindings" propstore/core/activation.py
rg -n -F -- "checked_condition_set(" propstore/core/activation.py
rg -n -F -- "check_condition_ir(" propstore/core/activation.py
rg -n -F -- "claim_conditions.sources" propstore/core/activation.py propstore/world
rg -n -F -- "except Z3TranslationError" propstore/core/activation.py
rg -n -F -- "propstore/core/analyzers.py" docs
powershell -File scripts/run_logged_pytest.ps1 tests/test_condition_solver_parity.py tests/test_atms_unbounded_stability_api.py tests/test_atms_engine.py tests/test_revision_projection.py tests/test_doc_drift_clean.py
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1
```

## Completion Criteria

- Every deletion target is gone.
- Every forbidden production search gate is zero-hit.
- Persisted checked-condition mismatch remains a hard solver error.
- Runtime assumptions no longer create checked condition sets.
- Targeted logged pytest passes.
- `uv run pyright propstore` passes.
- Full logged pytest passes.
- Workstream log records the final commit and gate log paths.

## Execution Log

Record each implementation commit here before moving to the next phase.

- `e8cbca57 Add runtime condition scope workstream`
  - Created this executable workstream.
- `3767a5a8 Fix runtime condition activation scope`
  - Phase 1: deleted `_solver_with_environment_bindings`, activation-side
    runtime registry expansion imports, and runtime
    `checked_condition_set(check_condition_ir(...))` construction.
  - Phase 2: added condition-owner runtime CEL lowering to non-persisted
    `ConditionIR`; runtime-only symbol typing comes from CEL AST context and
    environment bindings, with ambiguous symbols hard-failing.
  - Phase 3: added solver comparison of persisted checked conditions against
    runtime `ConditionIR` while preserving strict checked-condition fingerprint
    validation.
  - Phase 4: wired activation through the condition-owner runtime lowering API
    and solver runtime-IR comparison API.
  - Phase 5: updated live docs covered by the doc drift gate.
- `3bba92d7 Update runtime activation remediation contract`
  - Updated the stale remediation test to match the workstream contract:
    inferable runtime-only CEL identifiers are local runtime constraints rather
    than persisted registry errors.

Final gates:

- Forbidden-surface searches: zero matches for all Phase 6 `rg -n -F` gates.
- Targeted logged pytest:
  `powershell -File scripts/run_logged_pytest.ps1 tests/test_condition_solver_parity.py tests/test_atms_unbounded_stability_api.py tests/test_atms_engine.py tests/test_revision_projection.py tests/test_doc_drift_clean.py`
  - `58 passed`
  - `LOG_PATH=logs\test-runs\pytest-20260522-001910.log`
- Package Pyright:
  `uv run pyright propstore`
  - `0 errors, 0 warnings, 0 informations`
- Full logged pytest:
  `powershell -File scripts/run_logged_pytest.ps1`
  - `3518 passed, 4 skipped, 30 warnings`
  - `LOG_PATH=logs\test-runs\pytest-20260522-001254.log`
