# Backward Chaining Implementation Notes
## 2026-04-10

### GOAL
Implement `build_arguments_for()` in aspic.py — goal-directed backward chaining from a queried conclusion through rules to premises.

### OBSERVED SO FAR
- `aspic.py` is ~959 lines. Key types: `Literal`, `ContrarinessFn`, `Rule`, `PremiseArg`, `StrictArg`, `DefeasibleArg`, `KnowledgeBase`, `ArgumentationSystem`, `CSAF`.
- `build_arguments()` at line 527: forward/bottom-up, seeds from KB premises/axioms, iterates rules to fixpoint. Returns `frozenset[Argument]`.
- Acyclicity check at line 596-604: rule's consequent must not appear in any sub-argument's conclusions.
- `compute_attacks()` at line 620: works on any `frozenset[Argument]` — no coupling to how arguments were built.
- `compute_defeats()` at line 870: same — works on attacks frozenset.
- `ContrarinessFn` has `is_contradictory`, `is_contrary`, `is_conflicting` — but NO `contraries_of(literal)` method. Need to add a helper or iterate.
- Existing tests in `tests/test_aspic.py` use Hypothesis strategies for property testing.
- `conc()`, `prem()`, `sub()`, `all_concs()` are all `@functools.cache` decorated.

### PLAN
1. Add `_contraries_of()` helper to find all literals contrary/contradictory to a given literal
2. Implement `build_arguments_for()` with backward chaining + memoization
3. Write tests in `tests/test_backward_chaining.py`
4. Optionally add `query_claim` in aspic_bridge.py
5. Commit after each chunk

### DONE
- Implemented `_contraries_of()` helper in aspic.py
- Implemented `build_arguments_for()` in aspic.py (~170 lines) with backward chaining, memoization, cycle detection, depth limiting, attacker inclusion (2 passes for counter-attacks)
- Existing 68 tests still pass
- Wrote `tests/test_backward_chaining.py` with concrete tests + 3 Hypothesis property tests

### NEXT
- Run new tests, fix any failures
- Commit implementation + tests
- Optionally add query_claim in aspic_bridge.py
- Write report

### BLOCKERS
None — about to run new tests.
