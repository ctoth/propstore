# WS-P2 Closure Report

Workstream: WS-P2 - Condition semantics surface

Closing code commit: `dbc1e3c4`

Closure date: 2026-05-02

## Findings Closed

- P2-1 mixed condition carriers: compiler and runtime paths now use `CheckedConditionSet` / `ConditionIR` rather than checked CEL carriers.
- P2-2 public API named for backend: `propstore/z3_conditions.py` is deleted; public semantic queries use `propstore.core.conditions.solver.ConditionSolver`.
- P2-3 frontend/parser leakage: production CEL parser imports are confined to the condition frontend boundary.
- P2-4 IR semantic gap: `ConditionIR` carries TIMEPOINT/category metadata, validates literal kinds, and round-trips through the versioned codec.
- P2-5 solver semantic parity gap: `ConditionSolver` preserves the pinned Z3 semantics, unknown handling, fingerprint checks, temporal ordering, category behavior, and context isolation.
- P2-6 runtime reparsing: runtime paths consume checked carriers or encoded condition IR from sidecar/graph storage instead of reparsing CEL as the semantic payload.
- P2-7 architecture docs drift: condition architecture docs now name `core.conditions` as the owner surface and describe CEL as an authoring frontend.

## Tests Written First

The workstream introduced the first-failing gates named in `WS-P2-condition-semantics.md` before the corresponding production cutovers. They were designed to fail against the old surface because:

- `tests/test_condition_solver_parity.py` and `tests/test_condition_solver_temporal_ordering.py` required the new solver to preserve old solver behavior without importing `propstore.z3_conditions`.
- `tests/test_condition_ir_semantic_metadata.py` and `tests/test_condition_ir_encoding.py` required TIMEPOINT/category metadata and hard-failing versioned condition encoding before the old loose IR could satisfy it.
- `tests/test_condition_architecture_boundaries.py` and `tests/test_condition_runtime_no_reparse.py` required deletion-first boundary convergence: no production old solver import, no parser leakage, and no runtime CEL reparsing path.
- `tests/test_condition_docs_done.py` required the docs to stop presenting `propstore.z3_conditions` or `CheckedCelExpr` as production APIs.

I verified the final passing gates in this session. I do not have a single preserved pre-fix failure log for every first-failing test in this report.

## Verification Logs

- Step 6 sidecar targeted: `logs/test-runs/condition-sidecar-targeted-20260502-123626.log` - 11 passed.
- Step 6 sidecar gate: `logs/test-runs/condition-sidecar-20260502-123706.log` - 205 passed.
- Step 7 docs gate: `logs/test-runs/condition-docs-20260502-124220.log` - 2 passed.
- Step 8 architecture gate: `logs/test-runs/condition-architecture-20260502-125432.log` - 97 passed.
- Fixture repair slice: `logs/test-runs/condition-fixture-slice-20260502-131418.log` - 89 passed.
- ATMS equivalence regression: `logs/test-runs/WS-P2-atms-equivalence-20260502-133148.log` - 1 passed.
- Failure-slice rerun: `logs/test-runs/WS-P2-failure-slice-20260502-133206.log` - 154 passed.
- Merge translation/regime guard: `logs/test-runs/WS-P2-merge-translation-20260502-133804.log` - 2 passed.
- Superseded full-suite failure: `logs/test-runs/WS-P2-full-20260502-133355.log` - 1 failed before `242bcc68`.
- Superseded full-suite pass before final Pyright typing repair: `logs/test-runs/WS-P2-full-20260502-133830.log` - 3425 passed, 2 skipped.
- Final current-code full suite: `logs/test-runs/WS-P2-full-20260502-134333.log` - 3425 passed, 2 skipped.
- Final Pyright: `uv run pyright propstore` - 0 errors, 0 warnings, 0 informations.

## Property Gates

Property-style and architecture gates were added or extended in the condition workstream rather than moved to a successor. Notable gates include condition solver parity/temporal behavior, condition IR codec round-trip and hard-failure behavior, runtime no-reparse scans, docs scans, and import-boundary scans.

No WS-P2 property gate is deferred.

## Files Changed

Principal production surfaces changed:

- `propstore/core/conditions/registry.py`
- `propstore/core/conditions/ir.py`
- `propstore/core/conditions/codec.py`
- `propstore/core/conditions/checked.py`
- `propstore/core/conditions/cel_frontend.py`
- `propstore/core/conditions/solver.py`
- `propstore/core/conditions/z3_backend.py`
- `propstore/core/conditions/__init__.py`
- `propstore/z3_conditions.py` deleted
- `propstore/cel_checker.py`
- `propstore/cel_types.py`
- `propstore/compiler/ir.py`
- `propstore/families/claims/passes/__init__.py`
- `propstore/families/concepts/passes.py`
- `propstore/condition_classifier.py`
- `propstore/context_lifting.py`
- `propstore/defeasibility.py`
- `propstore/conflict_detector/*`
- `propstore/core/activation.py`
- `propstore/core/environment.py`
- `propstore/core/graph_build.py`
- `propstore/core/graph_types.py`
- `propstore/core/row_types.py`
- `propstore/merge/merge_classifier.py`
- `propstore/sidecar/*`
- `propstore/world/assignment_selection_merge.py`
- `propstore/world/atms.py`
- `propstore/world/bound.py`
- `propstore/world/model.py`
- `propstore/world/types.py`

Principal docs and architecture surfaces changed:

- `.importlinter`
- `README.md`
- `docs/argumentation-package-boundary.md`
- `docs/cel-typed-expressions.md`
- `docs/conflict-detection.md`
- `docs/data-model.md`
- `docs/python-api.md`

Principal tests changed or added:

- `tests/test_condition_solver_parity.py`
- `tests/test_condition_ir_semantic_metadata.py`
- `tests/test_condition_ir_encoding.py`
- `tests/test_condition_solver_temporal_ordering.py`
- `tests/test_condition_architecture_boundaries.py`
- `tests/test_condition_runtime_no_reparse.py`
- `tests/test_condition_docs_done.py`
- `tests/test_condition_classifier.py`
- `tests/test_conflict_detector.py`
- `tests/test_context_lifting_ws5.py`
- `tests/test_defeasibility_satisfaction.py`
- `tests/test_assignment_selection_merge.py`
- `tests/test_temporal_conditions.py`
- `tests/test_world_query.py`
- `tests/test_sidecar_contexts.py`
- `tests/test_graph_build.py`
- `tests/test_atms_engine.py`
- `tests/atms_helpers.py`
- fixture and regression tests named in the verification logs above.

## Done Checks

- `propstore/z3_conditions.py` is deleted.
- `rg -F "propstore.z3_conditions" propstore tests docs README.md` finds only tests that enforce absence.
- `rg -F "CheckedCel" propstore tests docs README.md` finds only the docs sentinel test.
- Final full logged suite passed.
- Final `uv run pyright propstore` passed.

## Remaining Risks

No WS-P2 work is deferred. Existing unrelated dirty tracked files and untracked artifacts were present in the worktree and were not part of this closure.
