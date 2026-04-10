# Implementation Report: Goal-Directed Backward Chaining (R2)

## Summary

Implemented `build_arguments_for()` in `propstore/aspic.py` and `query_claim()` in `propstore/aspic_bridge.py`, adding goal-directed backward chaining to propstore's ASPIC+ argumentation engine. The implementation constructs only arguments relevant to a queried conclusion, rather than exhaustively enumerating all possible arguments.

## Commits

- `48d186a` — Core implementation: `build_arguments_for()` and `_contraries_of()` in aspic.py, plus 20 tests in test_backward_chaining.py
- `fa2b1db` — Integration: `query_claim()` and `ClaimQueryResult` in aspic_bridge.py

## What Was Implemented

### `_contraries_of(literal, contrariness, language)` (aspic.py)

Helper that finds all literals in L that conflict with a given literal (both contradictories and contraries). Iterates the language since `ContrarinessFn` stores pairs rather than indexing by target.

### `build_arguments_for(system, kb, goal, *, include_attackers=True, max_depth=10)` (aspic.py)

Goal-directed argument construction via backward chaining:

1. **Base case**: If goal is in `kb.axioms` or `kb.premises`, create `PremiseArg`
2. **Recursive case**: Find rules whose consequent matches goal, recursively build arguments for each antecedent, combine via Cartesian product into `StrictArg`/`DefeasibleArg`
3. **Attacker discovery** (when `include_attackers=True`): Two passes to find arguments for contraries of all conclusions in the goal's argument tree, plus counter-arguments against those attackers
4. **Cycle prevention**: Both call-stack tracking (`in_progress` set) and the same acyclicity check as `build_arguments()` (consequent must not appear in sub-argument conclusions)
5. **Depth limiting**: `max_depth` parameter prevents infinite chains
6. **Memoization**: Results cached per literal to avoid redundant computation
7. **c-consistency**: Same `is_c_consistent()` check as forward construction

The function reuses existing types (`PremiseArg`, `StrictArg`, `DefeasibleArg`) and is fully compatible with `compute_attacks()` and `compute_defeats()`.

### `ClaimQueryResult` and `query_claim()` (aspic_bridge.py)

Integration wrapper that:
1. Runs the same T1-T5 translation pipeline as `build_bridge_csaf()`
2. Replaces `build_arguments()` with `build_arguments_for()` for the queried claim
3. Runs `compute_attacks()` / `compute_defeats()` on the focused subset
4. Returns `ClaimQueryResult` with arguments partitioned into for/against, plus attacks and defeat pairs

### Tests (test_backward_chaining.py)

20 tests total:

- **`TestContrariesOf`** (2): Contradictory pairs, asymmetric contraries
- **`TestBasicBackwardChaining`** (6): Premise-only, axiom-only, strict rule, defeasible rule, rule chain, unreachable goal
- **`TestAttackerInclusion`** (3): Contrary included, excluded when disabled, rule-based attacker
- **`TestDepthLimiting`** (2): Deep chain truncation, cyclic rule termination
- **`TestCorrectnessProperty`** (4): Simple system, multi-path, attackers subset, attacks work on result
- **Hypothesis property tests** (3):
  - `test_backward_subset_of_forward`: `build_arguments_for(goal) <= build_arguments()` for random systems
  - `test_backward_with_attackers_subset_of_forward`: Same with `include_attackers=True`
  - `test_backward_finds_all_goal_conclusions`: Every exhaustive argument concluding goal appears in backward result (completeness)

All 20 tests pass. All 142 existing ASPIC/bridge tests pass with no regressions.

## Design Decisions

1. **Additive, not modifying**: `build_arguments()` is untouched. `build_arguments_for()` is a new function alongside it.
2. **Two-pass attacker discovery**: First pass finds attackers of goal arguments. Second pass finds counter-attackers (for reinstatement). This covers the common case without full transitive closure.
3. **Memoization per literal**: The `memo` dict caches backward results within a single call, avoiding exponential blowup on diamond-shaped rule graphs.
4. **Cycle detection via `in_progress` set**: Complements the acyclicity check — prevents infinite recursion even when rules form cycles that the acyclicity check alone wouldn't catch during construction.

## Files Modified

- `/propstore/aspic.py` — Added `_contraries_of()` (~20 lines) and `build_arguments_for()` (~170 lines)
- `/propstore/aspic_bridge.py` — Added `dataclass` import, `Argument` and `build_arguments_for` imports, `ClaimQueryResult` dataclass, `query_claim()` function (~100 lines)
- `/tests/test_backward_chaining.py` — New file, 20 tests (~370 lines)

## Test Results

```
tests/test_backward_chaining.py: 20 passed in 1.19s
tests/test_aspic.py: 68 passed
tests/test_aspic_bridge.py: 54 passed
Total: 142 passed, 0 failed
```
