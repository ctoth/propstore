# Phase 1: Batch Equivalence Classes - Session Notes

## GOAL
Implement `partition_equivalence_classes` on `Z3ConditionSolver`, wire into conflict_detector, TDD.

## Current State
- Step 1 DONE: 7 tests written in `TestBatchEquivalenceClasses`, all fail with AttributeError (expected - TDD red)
- Step 2 NEXT: Implement `partition_equivalence_classes` in `propstore/z3_conditions.py`

## Key Observations
- `Z3ConditionSolver` lives at `propstore/z3_conditions.py` (286 lines)
- Already has `are_equivalent()` and `are_disjoint()` methods
- `conflict_detector.py` does O(n^2) pairwise in `detect_conflicts()` at lines 186-213 (parameter claims)
- The pairwise loop calls `_classify_conditions()` from `condition_classifier.py`
- `_classify_conditions` calls `_try_z3_classify` which creates a fresh `Z3ConditionSolver` per call
- Step 3 (wiring) needs to be careful: the optimization is about grouping by equivalence class within a concept group, NOT changing the output format

## Files Modified
- `tests/test_z3_conditions.py` - added TestBatchEquivalenceClasses (7 tests)

## Architecture for Step 3
- `detect_conflicts` groups parameter claims by concept (line 182)
- For each concept with 2+ claims, it does pairwise comparison (lines 186-213)
- The pairwise loop: check value compat first, then classify conditions
- Optimization: partition condition sets into equiv classes, then within-class = CONFLICT, between-class = check disjointness once per class pair
- BUT: value compatibility check happens per pair and can short-circuit. Need to keep that.
- The wiring is in conflict_detector.py, not condition_classifier.py

## DONE
- All 5 steps complete
- Commit: 43a396c on master
- Report written to reports/phase1-batch-equivalence-report.md
- 700/701 tests pass (1 pre-existing failure unrelated to changes)
- Note: committed to master (that's where the working tree was, despite gitStatus saying aspic-argumentation)
