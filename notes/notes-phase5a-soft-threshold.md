# Phase 5A: Soft Threshold Migration — Session Notes

## GOAL
Replace hard confidence_threshold gate in argumentation.py and structured_argument.py with soft epsilon prune (vacuous opinion u > 0.99). HARD DELETE confidence_threshold from everywhere.

## DONE (reading phase)
- Read all 8 required files from prompt
- Read Li 2012 notes (PrAF: each argument has existence probability, threshold gates destroy information)
- Read Hunter & Thimm 2017 notes (epistemic approach: AF topology determines constraints, not arbitrary threshold)
- Read Fang 2025 notes (LLM-ASPIC+: contradictions resolved by AF, not pre-filtered)
- Read argumentation.py (threshold gate at lines 131-133, stance_summary at 205+, compute_claim_graph_justified_claims at 175+)
- Read structured_argument.py (parallel threshold gate at lines 147-148 in _build_projected_framework)
- Read opinion.py (Opinion dataclass, vacuous = (0,0,1,a), u=1.0)
- Read impact analysis (Change 5 section: all callers listed)
- Read world/types.py (RenderPolicy.confidence_threshold at line 193)
- Read test_render_time_filtering.py (full file — 153 lines, 3 test classes)
- Read test_argumentation_integration.py lines 140-180 (test_confidence_threshold at line 156)

## FILES TO MODIFY

### Core changes:
1. `propstore/argumentation.py` — Remove confidence_threshold param from build_argumentation_framework (line 106), compute_claim_graph_justified_claims (line 181), stance_summary (line 208). Replace gate at 131-133 with vacuous opinion check. Update stance_summary reporting.
2. `propstore/structured_argument.py` — Remove confidence_threshold from build_structured_projection (line 60), _build_projected_framework (line 134). Replace gate at 147-148.
3. `propstore/world/types.py` — DELETE confidence_threshold from RenderPolicy (line 193)

### Callers to update (from impact analysis):
4. `propstore/world/resolution.py` — Lines 252-253 extract confidence_threshold from policy
5. `propstore/worldline_runner.py` — Lines 75, 193, 223
6. `propstore/cli/compiler_cmds.py` — Lines 1254-1255, 1310-1311 (CLI options)
7. `propstore/worldline.py` — WorldlinePolicy.confidence_threshold (line 68)

### Tests to rewrite:
8. `tests/test_render_time_filtering.py` — Complete rewrite for new semantics
9. `tests/test_argumentation_integration.py` — test_confidence_threshold at line 156

### Tests that may reference confidence_threshold:
10. `tests/test_render_contracts.py` — line 21
11. `tests/test_world_model.py` — lines 1080, 1089

## PLAN
1. Read remaining caller files (resolution.py, worldline_runner.py, compiler_cmds.py, worldline.py)
2. Read test files that reference confidence_threshold
3. Write tests FIRST (TDD)
4. Implement changes
5. Run full test suite
6. Commit + report

## OBSERVATIONS FROM READING
- conftest.py schema already has opinion_belief, opinion_disbelief, opinion_uncertainty, opinion_base_rate columns
- WorldlinePolicy has from_dict/to_dict that serialize confidence_threshold
- resolution.py has confidence_threshold in: resolve() (line 220), _resolve_claim_graph_argumentation (line 86), _resolve_structured_argumentation (line 133)
- compiler_cmds.py has --confidence-threshold CLI option in world_resolve (line 1254) and world_extensions (line 1317)
- worldline_runner.py references definition.policy.confidence_threshold at lines 75, 196, 226
- test_render_contracts.py line 21 asserts policy.confidence_threshold == 0.5
- test_world_model.py lines 1080,1089 construct RenderPolicy with confidence_threshold

## COMPLETE LIST OF confidence_threshold REFERENCES TO DELETE
Source files:
1. propstore/argumentation.py: lines 106, 133, 181, 191, 208, 232, 244
2. propstore/structured_argument.py: lines 60, 103, 134, 148
3. propstore/world/types.py: line 193
4. propstore/world/resolution.py: lines 86, 104, 133, 158, 220, 252-253, 266-267, 314, 324
5. propstore/worldline.py: lines 68, 98, 120-121
6. propstore/worldline_runner.py: lines 75, 196, 226
7. propstore/cli/compiler_cmds.py: lines 1254-1255, 1265, 1287, 1317-1318, 1323, 1368, 1373, 1395, 1407, 1411, 1415

Test files:
8. tests/test_render_time_filtering.py: complete rewrite
9. tests/test_argumentation_integration.py: line 156-162
10. tests/test_render_contracts.py: line 21
11. tests/test_world_model.py: lines 1080, 1089

## PROGRESS
- Tests written in test_render_time_filtering.py (12 tests, 10 fail as expected — TDD red)
- argumentation.py: DONE (removed confidence_threshold from 3 functions, replaced gate with vacuous prune, updated stance_summary)
- structured_argument.py: IN PROGRESS (removed from build_structured_projection and _build_projected_framework signatures, need to replace gate at line 148)

## COMPLETED EDITS
- argumentation.py: DONE (3 functions updated, gate replaced, stance_summary rewritten)
- structured_argument.py: DONE (3 locations updated)
- world/types.py: DONE (field deleted from RenderPolicy)
- world/resolution.py: DONE (removed from resolve, _resolve_claim_graph, _resolve_structured)
- worldline.py: IN PROGRESS (field deleted, still need from_dict and to_dict)

## REMAINING EDITS
- test_argumentation_integration.py: fix property test test_no_supports_in_defeats (conf>=0.5 check needs removal)
- Then run full test suite

## COMMITTED
- Commit hash: 1d2896d
- 1159 tests pass (>= 1155 required)
- All 12 source/test files staged and committed
- No pre-commit hooks configured (ruff/pre-commit not installed)

## REMAINING
- Write report to reports/phase5a-soft-threshold-report.md
