# Fix 3A: Z3 Division-by-Zero — Session Notes

**GOAL:** TDD fix for Z3 division-by-zero unsoundness in condition solver.

## DONE
- RED: Wrote `test_division_by_zero_unsoundness` — confirmed failure (Z3 returns `sat` for `F0/Ps > 3` with `Ps = 0`)
- GREEN: Added `_current_guards` list to collect `right != 0` during division translation, conjuncted into final expression in `_condition_to_z3`
- VERIFY: 984 pass, 6 pre-existing failures (none in z3_conditions tests)
- COMMIT: Changes landed in `2f48db1`
- REPORT: Written to `reports/fix-3a-z3-divzero-report.md`

## FILES
- `propstore/z3_conditions.py` — division guard implementation
- `tests/test_z3_conditions.py` — regression test

## Pre-existing failures (not ours)
- `test_bipolar_argumentation.py::TestAttackBasedConflictFree::test_grounded_extension_respects_attacks`
- `test_conflict_detector.py::TestTransitiveContextSemantics::test_transitive_conflicts_in_unrelated_contexts_exit_as_context_phi_node`
- `test_contexts.py` (3 failures related to context phi node classification)
- `test_dung.py::TestGroundedConcrete::test_grounded_extension_conflict_free_wrt_attacks`
