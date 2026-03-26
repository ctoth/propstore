# Phase 2c Notes: Extract condition_classifier.py

## GOAL
Extract condition classification logic from conflict_detector.py into condition_classifier.py

## What to move (lines in conflict_detector.py)
- Lines 95-104: 3 regex constants (_NUMERIC_CONDITION_RE, _STRING_CONDITION_RE, _BOOLEAN_CONDITION_RE)
- Lines 107-127: 3 dataclasses (_NumericConstraint, _DiscreteConstraint, _ConditionSummary)
- Lines 136-200: _try_z3_classify, _classify_conditions (entry point -> make public)
- Lines 275-460: _parse_condition_atom, _summarize_conditions, _numeric_constraints_disjoint, _numeric_value_excluded, _max_lower_bound, _min_upper_bound, _discrete_constraints_disjoint, _conditions_disjoint

## Imports needed in new module
- re, dataclasses (dataclass, field)
- ConflictClass from conflict_detector (or shared types)
- ConceptInfo from propstore.cel_checker

## What stays in conflict_detector.py
- ConflictClass enum (lines 32-38)
- ConflictRecord dataclass (lines 41-51)
- _classify_pair_context (lines 57-82)
- Value comparison imports (lines 87-94)
- _collect_* functions (lines 206+)
- detect_conflicts and _detect_param_conflicts

## Test file changes
- tests/test_z3_conditions.py imports _classify_conditions from conflict_detector -> change to classify_conditions from condition_classifier

## STATUS: Starting implementation
