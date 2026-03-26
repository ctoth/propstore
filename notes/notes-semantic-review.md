# Semantic Foundations Review Notes

## GOAL
Adversarial review of all files in the semantic-foundations-impl branch for bugs, regressions, semantic mismatches with the plan, missing tests, and compatibility risks.

## ALL FILES NOW READ (second pass complete 2026-03-23)
- propstore/build_sidecar.py ✓ (full)
- propstore/conflict_detector.py ✓ (full)
- propstore/graph_export.py ✓ (full)
- propstore/relate.py ✓ (full)
- propstore/validate_claims.py ✓ (full)
- propstore/world/bound.py ✓ (full)
- propstore/world/model.py ✓ (full)
- propstore/world/types.py ✓ (full)
- propstore/z3_conditions.py ✓ (full)
- tests/test_build_sidecar.py ✓ (1-598)
- tests/test_conflict_detector.py ✓ (full)
- tests/test_contexts.py ✓ (1-597, full)
- tests/test_graph_export.py ✓ (full)
- tests/test_sensitivity.py ✓ (full)
- tests/test_validate_claims.py ✓ (1-598)
- tests/test_world_model.py ✓ (1-599)
- plans/semantic-contract.md ✓ (full)
- plans/semantic-foundations-and-atms-plan.md ✓ (full)

## STILL TO READ
- ../research-papers-plugin/.../generate_claims.py
- ../research-papers-plugin/.../test_generate_claims.py
- propstore/stances.py (new file, untracked)

## CRITICAL FINDINGS

### C1. build_sidecar.py:777-779 — canonical_ast always gets empty bindings for list-of-dicts variables
Confirmed. The validated schema shape is list-of-dicts. `isinstance(variables, dict)` is False, so `bindings = {}`. canonical_dump gets empty bindings. This means sidecar canonical_ast is weaker than conflict_detector's AST comparison.

### C2. bound.py:92-96 — _derived_value_impl `any(not ...)` should be `all(not ...)`
If ANY parameterization is condition-incompatible, returns "no_relationship" instead of "underspecified", even when other parameterizations failed for other reasons (e.g., missing inputs). Triggers when concept has multiple parameterizations with different condition scopes.

### C3. No cross-repo integration test for draft stage rejection (plan R4)
validate_claims.py:137-142 rejects stage=="draft". generate_claims.py emits stage: "draft". No test feeds one into the other.

### C4. No test for build-time vs render-time conflict agreement on CONTEXT_PHI_NODE
The plan requires: "build-time and render-time conflict paths agree on unrelated-context handling." No such test exists. The _recomputed_conflicts path in bound.py uses _claim_row_to_source_claim which could differ from build-time source claims.

## IMPORTANT FINDINGS

### I1. model.py:191-202 — pragma_table_info checked on every claims_for() call (perf)
Not cached. Every concept query hits SQLite pragma to check if target_concept column exists.

### I2. validate_claims.py:233-234 — mechanism/comparison/limitation validated as observations
Undocumented in the semantic contract. These types exist in the system but the contract only discusses observation, parameter, measurement, equation, algorithm, model.

### I3. Fixture duplication across 3 test files
test_graph_export.py, test_sensitivity.py, test_world_model.py have near-identical fixtures. Maintenance risk.

### I4. test_validate_claims.py — draft stage rejection untested
Code exists (validate_claims.py:137-142) but TestDraftArtifactBoundary at line 572 confirms it IS now tested. Retracted — this IS tested.

### I5. relate.py — no test that argumentation layer ignores "none" stances
Semantic contract says "none" stances must be ignored by attack/support/defeat computation. No test proves this.

### I6. _collect_algorithm_claims legacy fallback (conflict_detector.py:162-173)
Dead code path for claims without `claim["concept"]` that falls back to first variable concept. Well-formed claims always have `concept`. Not a bug but a dead code smell.

## PLAN PROOF OBLIGATION COVERAGE

| Obligation | Status |
|-----------|--------|
| WorldModel.bind(env+context) matches manual BoundWorld | PARTIAL — test_contexts.py:276 tests via BoundWorld, not WorldModel.bind |
| Build/render conflict agreement on contexts | MISSING |
| Invalid stance targets rejected | PRESENT (validate_claims + build_sidecar) |
| Measurements in runtime query surface | PRESENT (test_world_model.py:455) |
| Algorithm attribution follows output concept | PRESENT (test_conflict_detector.py:691) |
| Context/form/stance changes force rebuild | PRESENT (test_build_sidecar.py:410-468) |
| Draft rejection | PRESENT (test_validate_claims.py:572) |
| Plugin/compiler round-trip | MISSING |

## NEXT
- Read stances.py, generate_claims.py, test_generate_claims.py
- Finalize review report
