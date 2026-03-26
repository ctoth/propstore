# Review Fix Cleanup Session

## GOAL
Fix 2 remaining analyst findings: bare except in parameters.py:213, type:ignore in validate_claims.py

## DONE
- Baseline: 841 passed
- Read parameters.py: bare `except Exception` at line 213 in `_detect_cross_class_parameter_conflicts`, catches errors from `z3_solver.are_disjoint()`
- Read validate_claims.py: `type: ignore[union-attr]` at lines 607-608, `build_concept_registry` takes `repo: object`
- Read existing test pattern at line 994: `test_z3_partition_unexpected_error_propagates` — patches `partition_equivalence_classes`

## FILES
- `propstore/conflict_detector/parameters.py` — Fix 1: line 213 bare except
- `propstore/validate_claims.py` — Fix 2: lines 607-608 type:ignore
- `tests/test_conflict_detector.py` — New test for are_disjoint RuntimeError propagation

## NEXT
1. Write RED test for are_disjoint RuntimeError propagation
2. Run test (expect FAIL)
3. Fix the except clause
4. Run test (expect PASS)
5. Fix validate_claims.py type annotations
6. Full test suite
7. Commit
