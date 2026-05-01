# WS-J2 Closure Report

Workstream: WS-J2 - InterventionWorld (Pearl do, Halpern HP-modified)

Closing implementation commit: `e4207ff5` (`WS-J2 flip completion sentinel`)

## Findings Closed

- J2-F1: `InterventionWorld` now performs Pearl-style intervention by replacing the intervened equation with a constant equation and severing the intervened node from its former parents.
- J2-F2: Intervened concepts now evaluate from the constant post-do equation rather than competing with preserved parent parameterizations.
- J2-F3: Intervention diffs now include downstream descendants affected by post-surgery SCM evaluation.
- J2-F4: `actual_cause` now evaluates Halpern 2015 modified-HP AC1, AC2, and AC3 with explicit witnesses.
- J2-F5: A separate `InterventionWorld` public surface exists, distinct from `OverlayWorld`.
- J2-F6: `observe()` is a deterministic-only not-intervention operator with disjoint provenance and fail-closed inconsistency handling; full Bayesian observation is deferred to WS-J7.

## Tests Written First

- `tests/test_intervention_world_severs_edges.py`: failed initially because no `InterventionWorld`/SCM do-surgery surface existed.
- `tests/test_intervention_world_distinct_from_observation.py`: failed initially because there was no distinct deterministic observation operator.
- `tests/test_actual_cause_suzy_billy.py`: failed initially because no actual-cause API existed; now pins Halpern 2015 Suzy/Billy.
- `tests/test_actual_cause_forest_fire.py`: failed initially because no actual-cause API existed; now pins Halpern 2015 disjunctive forest-fire behavior.
- `tests/test_actual_cause_voting.py`: failed initially because no actual-cause API existed; now pins Halpern 2015 voting behavior.
- `tests/test_intervention_diff_walks_descendants.py`: failed initially because overlay diffs did not walk downstream SCM descendants.
- `tests/test_actual_cause_minimality.py`: failed initially because AC3 minimality was absent.
- `tests/test_actual_cause_witness_budget.py`: failed initially because there was no witness budget or `EnumerationExceeded` signal.
- `tests/test_intervention_world_construction_requires_compiled_graph.py`: failed initially because intervention construction had no structured missing-SCM failure.
- `tests/test_intervention_world_public_surface.py`: failed initially because the public exports and query methods did not exist.
- `tests/test_workstream_j2_done.py`: failed/xfail sentinel flipped only after the workstream gates were implemented.

## Logged Gates

- `uv run pyright propstore` passed with 0 errors.
- `uv run lint-imports` passed with the six-layer architecture contract intact.
- `uv run python reviews/2026-04-26-claude/workstreams/check_index_order.py` passed with 41 rows checked.
- `powershell -File scripts/run_logged_pytest.ps1 -Label WS-J2 tests/test_intervention_world_severs_edges.py tests/test_intervention_world_distinct_from_observation.py tests/test_actual_cause_suzy_billy.py tests/test_actual_cause_forest_fire.py tests/test_actual_cause_voting.py tests/test_intervention_diff_walks_descendants.py tests/test_actual_cause_minimality.py tests/test_actual_cause_witness_budget.py tests/test_intervention_world_construction_requires_compiled_graph.py tests/test_intervention_world_public_surface.py tests/test_workstream_j2_done.py` passed: 16 passed. Log: `logs/test-runs/WS-J2-20260430-193708.log`.
- First full-suite run `powershell -File scripts/run_logged_pytest.ps1 -Label WS-J2-full` exposed an xdist race in source-scan tests against transient `_ws_n2_violation_*.py` files. Log: `logs/test-runs/WS-J2-full-20260430-194003.log`.
- Race-focused rerun `powershell -File scripts/run_logged_pytest.ps1 -Label WS-J2-flake-fix tests/test_ws_f_aspic_bridge.py::test_query_no_private_argumentation_imports tests/test_canonical_json_single_source.py::test_propstore_defines_no_local_canonical_json_helpers tests/test_import_linter_negative.py::test_import_linter_rejects_every_lower_to_higher_layer_import` passed: 3 passed. Log: `logs/test-runs/WS-J2-flake-fix-20260430-194409.log`.
- Final full suite `powershell -File scripts/run_logged_pytest.ps1 -Label WS-J2-full-final` passed: 3563 passed, 2 skipped. Log: `logs/test-runs/WS-J2-full-final-20260430-194443.log`.

## Property-Based Gates

- Added `tests/test_actual_cause_witness_budget.py` as a Hypothesis-backed budget invariant: witness search either returns a verdict or raises `EnumerationExceeded`; it must not silently return "not a cause" because enumeration stopped.
- The remaining broader property families are explicitly successor work: probabilistic counterfactual/observation properties in WS-J7, continuous-domain intervention properties in WS-J9, actual-cause staleness properties in WS-J10, and optimized AC2 search equivalence properties in WS-J11.

## Files Changed

- `propstore/world/scm.py`
- `propstore/world/intervention.py`
- `propstore/world/actual_cause.py`
- `propstore/world/model.py`
- `propstore/world/__init__.py`
- `propstore/__init__.py`
- `docs/worldlines.md`
- `docs/gaps.md`
- `tests/intervention_world_helpers.py`
- `tests/test_intervention_world_severs_edges.py`
- `tests/test_intervention_world_distinct_from_observation.py`
- `tests/test_actual_cause_suzy_billy.py`
- `tests/test_actual_cause_forest_fire.py`
- `tests/test_actual_cause_voting.py`
- `tests/test_intervention_diff_walks_descendants.py`
- `tests/test_actual_cause_minimality.py`
- `tests/test_actual_cause_witness_budget.py`
- `tests/test_intervention_world_construction_requires_compiled_graph.py`
- `tests/test_intervention_world_public_surface.py`
- `tests/test_workstream_j2_done.py`
- `tests/test_ws_f_aspic_bridge.py`
- `tests/test_canonical_json_single_source.py`
- `reviews/2026-04-26-claude/workstreams/WS-J7-probabilistic-counterfactuals.md`
- `reviews/2026-04-26-claude/workstreams/WS-J8-responsibility-blame.md`
- `reviews/2026-04-26-claude/workstreams/WS-J9-continuous-interventions.md`
- `reviews/2026-04-26-claude/workstreams/WS-J10-actual-cause-stale-fingerprint.md`
- `reviews/2026-04-26-claude/workstreams/WS-J11-actual-cause-search-optimization.md`
- `reviews/2026-04-26-claude/workstreams/INDEX.md`

## Remaining Risks And Successors

- WS-J7 owns full probabilistic counterfactuals and Bayesian observation; WS-J2 intentionally implements only deterministic consistency observation.
- WS-J8 owns responsibility and blame on top of actual cause.
- WS-J9 owns non-finite and continuous intervention domains.
- WS-J10 owns materialized actual-cause staleness fingerprints.
- WS-J11 owns search optimization for AC2 enumeration.
- The final suite issue encountered during closure was an xdist race in two source-scan tests, fixed by commits `6fe1b209` and `2a47b192`.
