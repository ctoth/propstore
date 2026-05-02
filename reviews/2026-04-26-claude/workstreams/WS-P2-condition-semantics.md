# WS-P2: Condition Semantics Surface

**Status**: OPEN
**Depends on**: WS-P, WS-N2
**Blocks**: none
**Owner**: Codex implementation owner + human reviewer required

---

## Why this workstream exists

WS-P fixed specific CEL, Z3, unit, and equation bugs, but the condition
architecture still has two active representations and two active solver
surfaces:

- authored CEL strings and `CelExpr` still move through core runtime paths;
- `CheckedCelExpr` / `CheckedCelConditionSet` still carry parser ASTs;
- `CheckedCondition` / `CheckedConditionSet` and `ConditionIR` exist but are not
  the production condition carrier;
- `propstore.z3_conditions.Z3ConditionSolver` still parses CEL, type-checks,
  translates parser ASTs to Z3, owns solver result types, handles closed/open
  category semantics, injects temporal ordering constraints, and answers public
  semantic queries;
- `propstore.core.conditions.z3_backend` is an IR backend, but it does not yet
  preserve every semantic behavior in `propstore.z3_conditions`.

Externalizing the CEL parser makes the old shape more visible: CEL is a
frontend language, not the semantic condition representation. The target is one
checked semantic condition surface:

```text
authored CEL source
  -> core.conditions.cel_frontend
  -> CheckedConditionSet / ConditionIR
  -> core.conditions.solver.ConditionSolver
```

CEL parser ASTs must not leak past the frontend. Z3 must be a backend/query
implementation detail, not the public condition API.

This is a representation replacement. Per project rules, it must be types-first
and deletion-first: characterize current behavior, strengthen the target types,
delete the old production surface, update every caller, and do not add aliases,
fallback readers, compatibility shims, or dual old/new production paths.

## Review findings covered

| Finding | Current surface | Required closure |
|---|---|---|
| P2-1 mixed condition carriers | `propstore/cel_types.py`; `propstore/core/conditions/checked.py`; `propstore/compiler/ir.py` | `CheckedConditionSet` is the only checked condition carrier in compiler and runtime paths. |
| P2-2 public API named for backend | `propstore/z3_conditions.py`; imports of `Z3ConditionSolver` | Public query API is `propstore.core.conditions.solver.ConditionSolver`; Z3 is backend-only. |
| P2-3 frontend/parser leakage | `cel_parser` imports in `core/activation.py`, `defeasibility.py`, `world/atms.py`, tests outside frontend | Production `cel_parser` imports are confined to `core.conditions.cel_frontend` and CEL checker internals if not folded. |
| P2-4 IR semantic gap | `core/conditions/ir.py`; `core/conditions/z3_backend.py` | IR preserves TIMEPOINT, category extensibility, category value sets, strict literal kinds, and source spans. |
| P2-5 solver semantic parity gap | `z3_conditions.py` vs `core/conditions/z3_backend.py` | New solver preserves closed categories, open categories, division definedness, temporal ordering, timeouts, unknowns, fingerprint checks, and context isolation. |
| P2-6 runtime reparsing | `world/model.py`, `world/bound.py`, `core/activation.py`, `core/graph_build.py`, sidecar `conditions_cel` use | Core runtime paths consume checked condition carriers or encoded `ConditionIR`, not reparsed CEL strings. |
| P2-7 architecture docs drift | `docs/cel-typed-expressions.md`, `docs/conflict-detection.md`, `docs/data-model.md`, `docs/python-api.md`, `docs/argumentation-package-boundary.md` | Docs describe the new condition architecture, ownership boundaries, storage shape, and public API. |

## Target architecture

### Owned modules

- `propstore.core.conditions.registry`
  - Owns `ConceptInfo`, `KindType`, `ConditionRegistry` if introduced,
    `condition_registry_fingerprint`, `scope_condition_registry`,
    `with_synthetic_concepts`, `synthetic_category_concept`, and
    `with_standard_synthetic_bindings`.
  - Replaces registry ownership currently embedded in `propstore.cel_checker`.

- `propstore.core.conditions.ir`
  - Owns the closed semantic condition ADT.
  - Must add `ConditionValueKind.TIMEPOINT`; do not collapse TIMEPOINT into
    ordinary numeric values.
  - Must carry category semantics needed by backends: open/closed flag and
    declared value set.
  - Must reject ill-typed literals at construction.

- `propstore.core.conditions.codec`
  - Owns the versioned JSON encoding and decoding for `ConditionIR`.
  - The encoding is the sidecar/graph storage shape for checked semantic
    conditions.
  - It must round-trip all IR node variants and fail hard on unknown encoding
    versions or unknown node/operator/kind tags.

- `propstore.core.conditions.checked`
  - Owns `CheckedCondition` and `CheckedConditionSet`.
  - This is the only checked condition carrier.
  - It stores source text for diagnostics and display, semantic IR for runtime,
    warnings, registry fingerprint, and the canonical encoded IR form needed by
    derived storage. It does not store CEL parser ASTs.

- `propstore.core.conditions.cel_frontend`
  - The only production frontend for authored CEL source.
  - Imports `cel_parser`.
  - Parses, type-checks, and lowers to `ConditionIR`.
  - Raises hard boundary failures for unsupported CEL constructs.

- `propstore.core.conditions.z3_backend`
  - Owns IR-to-Z3 projection only.
  - Preserves closed enum semantics, open string semantics, partial division
    definedness, boolean short-circuit definedness, ternary definedness, and
    TIMEPOINT interval constraints as backend semantics.

- `propstore.core.conditions.solver`
  - Owns `ConditionSolver`, `SolverSat`, `SolverUnsat`, `SolverUnknown`,
    `SolverUnknownReason`, `SolverResult`, `Z3TranslationError`,
    `Z3UnknownError`, and `solver_result_from_z3`.
  - Public query API:
    - `is_condition_satisfied_result`
    - `is_condition_satisfied`
    - `are_disjoint_result`
    - `are_disjoint`
    - `are_equivalent_result`
    - `are_equivalent`
    - `implies_result`
    - `implies`
    - `partition_equivalence_classes`
  - Accepts checked condition carriers, not raw CEL strings.

### Dependency direction

```text
families/*/passes
compiler/ir
sidecar build/read models
core/activation
context_lifting
defeasibility
conflict_detector
world
merge
    -> propstore.core.conditions
        -> cel_frontend -> cel_parser
        -> z3_backend -> z3
```

No production module outside `propstore.core.conditions.cel_frontend` should
parse CEL. No production module outside `propstore.core.conditions` should
import Z3 condition internals.

## Semantic pass placement

The semantic pass is condition checking and lowering:

```text
authored conditions: tuple[str, ...]
  -> CheckedConditionSet
```

This belongs in the family compiler pipelines for claims, concepts, and
contexts. It should reject unsupported CEL and registry mismatches before the
sidecar or runtime graph exists.

The solver is not a semantic pass. Disjointness, equivalence, implication, and
satisfaction are runtime queries over checked conditions and runtime bindings.
They belong to `core.conditions.solver`.

## First failing tests

Write these tests before production changes. They must fail against the current
target IR/solver path or demonstrate current architectural leakage. If a test
does not fail before the fix, stop and adjust the test or state that the premise
was wrong.

1. `tests/test_condition_solver_parity.py`
   - Builds checked conditions through `core.conditions.cel_frontend`.
   - Proves `ConditionSolver` preserves current `Z3ConditionSolver` behavior:
     numeric disjointness, open category equality, closed category enum
     rejection, `in` lists, boolean negation, equivalence, implication,
     timeout/unknown propagation, and registry fingerprint mismatch.

2. `tests/test_condition_ir_semantic_metadata.py`
   - `TIMEPOINT` lowers distinctly from numeric quantity.
   - Closed category references carry declared values and
     `category_extensible=False`.
   - Open category references carry `category_extensible=True`.
   - Numeric literals reject `bool` at `ConditionLiteral` construction time.
   - Bare string expressions fail unless they appear in supported comparison or
     membership positions.

3. `tests/test_condition_ir_encoding.py`
   - Every `ConditionIR` node variant round-trips through the versioned JSON
     codec.
   - The encoded form preserves TIMEPOINT and category metadata.
   - Unknown encoding versions, node tags, operator tags, and value-kind tags
     fail hard.

4. `tests/test_condition_solver_temporal_ordering.py`
   - `valid_from > valid_until` is unsatisfiable when registry declares matching
     TIMEPOINT interval endpoints.
   - The ordering applies in satisfaction, disjointness, equivalence, and
     implication queries.

5. `tests/test_condition_architecture_boundaries.py`
   - No production import of `propstore.z3_conditions`.
   - No production import of `cel_parser` outside
     `propstore.core.conditions.cel_frontend` and tests dedicated to frontend
     behavior.
   - Until `cel_checker` is folded or deleted, `cel_checker` may import
     `cel_parser` only as an internal helper consumed by `cel_frontend`.
   - By Step 5, the only allowed production `cel_parser` importer is
     `propstore.core.conditions.cel_frontend`.
   - `CheckedCondition` does not store `ast`, `cel_ast`, `z3`, or backend helper
     names.

6. `tests/test_condition_runtime_no_reparse.py`
   - Activation, conflict classification, context lifting, world query, and
     assignment-selection merge receive checked condition carriers or encoded
     `ConditionIR`, not raw `CelExpr` reparsed in the runtime query path.

7. `tests/test_condition_docs_done.py`
   - Asserts the architecture docs name the final modules and do not document
     `propstore.z3_conditions` or `CheckedCelExpr` as production APIs.

## Production change sequence

Each step lands in its own commit. Before editing a step, run path-limited
`git status --short -- <owned paths>`. Commit only explicit paths owned by that
step.

### Step 1 - Registry ownership

Create `propstore/core/conditions/registry.py`.

Move from `propstore.cel_checker`:

- `KindType`
- `ConceptInfo`
- registry fingerprinting
- scoped registry helpers
- synthetic concept helpers
- standard synthetic binding augmentation

Update importers to the new module. `cel_checker` may import these types, but
does not own them.

Acceptance:

- `rg -F "from propstore.cel_checker import ConceptInfo" propstore`
  returns no production imports.
- `rg -F "from propstore.cel_checker import KindType" propstore`
  returns no production imports.
- `uv run pyright propstore` passes.

### Step 2 - Strengthen ConditionIR and checked carriers

Update `ConditionIR` and `CheckedCondition` before adding solver behavior:

- add `ConditionValueKind.TIMEPOINT`;
- add category metadata to references;
- validate literal kind/value pairs in constructors;
- preserve source spans;
- ensure `CheckedConditionSet` enforces one registry fingerprint.

Update `cel_frontend` to lower CEL into the stronger IR.

Create `propstore/core/conditions/codec.py` with a versioned JSON encoding for
`ConditionIR`. The codec is part of the type boundary, not a sidecar-specific
helper.

Acceptance:

- `powershell -File scripts/run_logged_pytest.ps1 -Label condition-ir tests/test_condition_ir.py tests/test_checked_condition_ir.py tests/test_condition_ir_semantic_metadata.py tests/test_condition_ir_encoding.py`
- `uv run pyright propstore`

### Step 3 - Implement the final solver surface

Create `propstore/core/conditions/solver.py` and complete
`propstore/core/conditions/z3_backend.py`.

The solver must preserve:

- per-solver Z3 context isolation;
- configured timeout;
- `SolverUnknown` propagation;
- `Z3UnknownError` for two-valued wrappers;
- registry fingerprint checks;
- closed category enum semantics;
- open category string semantics;
- category unknown-value hard failures for closed categories;
- TIMEPOINT interval ordering;
- division definedness under boolean and ternary structure;
- translation caching keyed by registry fingerprint and checked source;
- `partition_equivalence_classes`.

This is not a compatibility bridge. It is the target production API.

Acceptance:

- `powershell -File scripts/run_logged_pytest.ps1 -Label condition-solver tests/test_condition_solver_parity.py tests/test_condition_solver_temporal_ordering.py tests/test_z3_division_definedness.py tests/test_ztypes_solver_unknown.py`
- `uv run pyright propstore`

### Step 4 - Delete the old production solver surface

Delete `propstore/z3_conditions.py`.

Update every production caller to import from
`propstore.core.conditions.solver` and to pass checked conditions rather than
raw CEL where the caller is in a core semantic/runtime path.

Required caller sweep:

- `propstore/condition_classifier.py`
- `propstore/core/activation.py`
- `propstore/core/environment.py`
- `propstore/core/lemon/temporal.py`
- `propstore/context_lifting.py`
- `propstore/defeasibility.py`
- `propstore/conflict_detector/*`
- `propstore/conflict_detector/parameter_claims.py`
- `propstore/merge/merge_classifier.py`
- `propstore/world/assignment_selection_merge.py`
- `propstore/world/model.py`
- `propstore/world/types.py`
- tests that monkeypatch `propstore.z3_conditions`
- `tests/test_z3_conditions.py` is deleted; any unique behavior it covers is
  ported first into `tests/test_condition_solver_parity.py` or another
  `tests/test_condition_solver_*` file.

Acceptance:

- `rg -F "propstore.z3_conditions" propstore tests` returns no production
  references.
- `powershell -File scripts/run_logged_pytest.ps1 -Label condition-solver-cutover tests/test_condition_classifier.py tests/test_conflict_detector.py tests/test_context_lifting_ws5.py tests/test_defeasibility_satisfaction.py tests/test_assignment_selection_merge.py tests/test_temporal_conditions.py`
- `uv run pyright propstore`

### Step 5 - Replace checked CEL carriers in compiler/runtime

Delete `CheckedCelExpr` and `CheckedCelConditionSet` as production carriers.

Update:

- `propstore/core/conditions/cel_frontend.py`
  - rewrite the post-parse path so it produces `ConditionIR` directly and does
    not instantiate `CheckedCelExpr`;
- `propstore/compiler/ir.py`
- `propstore/families/claims/passes/__init__.py`
- `propstore/families/concepts/passes.py`
- `propstore/families/contexts/passes.py` if context assumptions/rules need a
  checked condition carrier
- sidecar build/read models
- graph build/runtime types
- `propstore/cel_types.py`
  - delete `CheckedCelExpr`, `CheckedCelConditionSet`,
    `ParsedCelExpr`, and checked-CEL normalization helpers;
- `propstore/cel_checker.py`
  - either fold the remaining type-checker into
    `propstore.core.conditions.cel_frontend` and delete the module, or reduce it
    to a private helper consumed only by `cel_frontend`. It must not be a second
    public CEL frontend and must not re-export checked carrier types.

Authored source strings may remain at IO/display boundaries. Core semantic
paths must use `CheckedConditionSet` or encoded `ConditionIR`.

Acceptance:

- `rg -F "CheckedCel" propstore tests` has no production references.
- `rg -F "from propstore.cel_checker" propstore` has no production
  references outside `propstore/core/conditions/cel_frontend.py` if
  `cel_checker.py` remains as an internal helper.
- `powershell -File scripts/run_logged_pytest.ps1 -Label checked-condition-cutover tests/test_validate_claims.py tests/test_cel_validation.py tests/test_condition_runtime_no_reparse.py`
- `uv run pyright propstore`

### Step 6 - Sidecar and graph storage shape

Replace runtime dependence on JSON CEL strings as the canonical condition
payload. The sidecar may retain authored source text for display and rebuild,
but runtime query rows/graph nodes must expose typed condition carriers or an
encoded `ConditionIR` payload.

The encoded payload is the versioned `ConditionIR` JSON form defined in
`propstore.core.conditions.codec`; do not invent a sidecar-local encoding.

Do not add fallback readers for old sidecars. A sidecar is derived state; if the
schema changes, rebuild it.

Acceptance:

- sidecar schema/version updated if storage columns change;
- world/query/activation paths do not parse CEL from `conditions_cel` during
  semantic evaluation;
- `powershell -File scripts/run_logged_pytest.ps1 -Label condition-sidecar tests/test_world_query.py tests/test_worldline.py tests/test_sidecar_contexts.py tests/test_condition_runtime_no_reparse.py`
- `uv run pyright propstore`

### Step 7 - Architecture documentation and docs gates

Update architecture and user-facing docs in the same workstream:

- `docs/cel-typed-expressions.md`
  - Replace `CheckedCelExpr` / parser AST language with
    `CheckedCondition` / `ConditionIR`.
  - State that CEL is an authoring frontend only.

- `docs/conflict-detection.md`
  - Replace `Z3ConditionSolver` / `z3_conditions.py` references with
    `ConditionSolver` and `core.conditions` modules.
  - Explain that conflict detection consumes checked semantic conditions.

- `docs/data-model.md`
  - Document authored source vs checked semantic condition representation.
  - Clarify sidecar rebuild expectations if condition IR storage changes.

- `docs/python-api.md`
  - Replace public API type references and examples.

- `docs/argumentation-package-boundary.md`
  - Keep CEL/condition reasoning owned by propstore, but name the new
    `core.conditions` owner surface.

- Any README or architecture-layer doc that names `propstore.z3_conditions`.

Acceptance:

- `rg -F "z3_conditions" docs README.md reviews/2026-04-26-claude/workstreams/WS-P2-condition-semantics.md`
  only finds historical/current-workstream references, not final API docs.
- `rg -F "CheckedCelExpr" docs README.md` returns no final API references.
- `powershell -File scripts/run_logged_pytest.ps1 -Label condition-docs tests/test_condition_docs_done.py`

### Step 8 - Final architecture gates

Add or update architecture tests to make the new boundary enforceable:

- `propstore.core.conditions.ir` imports no frontend or backend modules.
- `propstore.core.conditions.checked` imports no frontend or backend modules.
- `propstore.core.conditions.cel_frontend` may import `cel_parser`.
- `propstore.core.conditions.z3_backend` may import `z3` but not `cel_parser`.
- no production module imports deleted solver surfaces.

Coordinate this with the closed WS-N2 architecture contract. If the package
layer contract needs to know about a new `core.conditions` owner surface, amend
the root `.importlinter` contract in this step and rerun the WS-N2
negative-injection architecture gate instead of adding only local spot checks.

Acceptance:

- `powershell -File scripts/run_logged_pytest.ps1 -Label condition-architecture tests/architecture tests/test_condition_architecture_boundaries.py`
- `uv run pyright propstore`

### Step 9 - Full verification and closure report

Run:

- `powershell -File scripts/run_logged_pytest.ps1 -Label WS-P2-full tests`
- `uv run pyright propstore`

Write:

- `reviews/2026-04-26-claude/workstreams/reports/WS-P2-closure.md`

Then update `reviews/2026-04-26-claude/workstreams/INDEX.md` from `OPEN` to
`CLOSED <sha>` with the closure report path.

## Done means done

This workstream is complete only when all of the following are true:

- `propstore/z3_conditions.py` is deleted.
- No production code imports `propstore.z3_conditions`.
- `CheckedCelExpr` and `CheckedCelConditionSet` are not production carriers.
- `propstore/cel_checker.py` is deleted or reduced to a re-export-free private
  helper consumed only by `propstore.core.conditions.cel_frontend`; no other
  production module imports it.
- CEL parser ASTs do not cross the CEL frontend boundary.
- Core semantic/runtime paths consume `CheckedConditionSet` or encoded
  `ConditionIR`, not reparsed raw CEL strings.
- `ConditionSolver` preserves every pinned behavior from the old solver.
- Architecture tests enforce the new module boundary.
- Architecture docs and user-facing docs describe the new surface.
- Full logged test suite and `uv run pyright propstore` pass.
- Closure report exists and names all tests/logs/files.

## Notes and risks

- The IR must be strengthened before solver cutover. A naive cutover to the
  current `core.conditions.z3_backend` would lose closed-category semantics,
  TIMEPOINT ordering, context isolation, unknown propagation, and fingerprint
  checks.
- Sidecar data is derived. This workstream may change sidecar schema without
  fallback readers, but must fail clearly and require rebuild.
- Unsupported CEL constructs should fail at the authoring/compile boundary,
  not at solver time.
- Do not add `Z3ConditionSolver = ConditionSolver`, import aliases, fallback
  readers, or old/new adapter functions.
