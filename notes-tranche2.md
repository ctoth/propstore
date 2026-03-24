# Tranche 2: Argumentation Correctness — Session Notes

## GOAL
Implement two semantic correctness fixes: (1) support-aware AF construction per Cayrol 2005, (2) attack-based conflict-free per Modgil & Prakken 2018 Def 14.

## BASELINE
- Branch: tranche2-argumentation-correctness
- 753 tests pass on clean master (1 deselected: test_missing_claims_key_errors)

## DONE
- Read all source files: argumentation.py, dung.py, dung_z3.py, preference.py
- Read paper notes: Cayrol 2005, Modgil & Prakken 2018
- Read failure notes from prior session
- Read existing tests: test_dung.py, test_argumentation_integration.py

## KEY OBSERVATIONS

### Current code (argumentation.py)
- `_NON_ATTACK_TYPES = {"supports", "explains", "none"}` — discarded at line 69
- `_ATTACK_TYPES = {"rebuts", "undercuts", "undermines", "supersedes"}`
- `_UNCONDITIONAL_TYPES = {"undercuts", "supersedes"}` — always defeat
- `_PREFERENCE_TYPES = {"rebuts", "undermines"}` — defeat iff not strictly weaker
- Returns `ArgumentationFramework(arguments, defeats)` — no attacks field

### Change 2: Attack-based CF (dung.py)
- `ArgumentationFramework` is frozen dataclass with `arguments` and `defeats`
- Need to add optional `attacks` field (default None for backward compat)
- `conflict_free(s, relation)` signature stays the same — callers choose what to pass
- `admissible()` needs optional `attacks` kwarg for CF check
- `complete_extensions()`, `stable_extensions()` need to pass attacks for CF
- `grounded_extension()` iterates characteristic_fn — doesn't call CF directly, no change needed
- `defends()`, `characteristic_fn()` stay on defeats — no change

### Change 1: Cayrol 2005 bipolar AF (argumentation.py)
- Supported defeat: A →sup B →def C ⟹ derived defeat (A, C). Chain: support path ending in defeat.
- Indirect defeat: A →def B →sup C ⟹ derived defeat (A, C). Chain: defeat then support path.
- Need transitive closure of support relation for chains of length > 2
- Implementation: collect supports, compute reachable-via-support, then combine with defeats

### dung_z3.py
- `_conflict_free_constraints()` uses `framework.defeats` — change to use attacks when available
- Defense constraints use defeats — no change

### Backward compatibility
- `ArgumentationFramework(arguments=X, defeats=Y)` still works (attacks defaults to None)
- When attacks is None, functions fall back to defeats for CF checks
- Existing test_dung.py property tests create AFs without attacks — will use defeats fallback
- Modgil 2018 Prop 16: under ASPIC+ assumptions, attack-based and defeat-based CF yield same extensions

### Existing test concerns
- test_argumentation_integration.py `test_excludes_supports`: checks (claim_a, claim_c) not in defeats where A supports C. After change: no derived defeat here because no one defeats claim_c. SAFE.
- test_argumentation_integration.py `test_grounded_is_conflict_free`: currently checks `conflict_free(ext, af.defeats)`. Should update to use `af.attacks` when available.
- test_dung.py property tests: AFs created without attacks field, will use defeats fallback. SAFE.

## COMMITS SO FAR
1. 84648aa — dung.py: attacks field, attack-based CF in admissible/complete/stable
2. 7dd134d — dung_z3.py: CF constraints use attacks when available
3. e3c7034 — argumentation.py: Cayrol derived defeats + attacks/defeats separation

## VERIFICATION
- 65 tests pass in test_dung.py + test_argumentation_integration.py + test_render_time_filtering.py
- All existing property tests pass (attacks defaults to None in pure Dung AFs, falls back to defeats)

## OBSERVATIONS
- Backward compat works: AF without attacks field uses defeats for CF (None default)
- Pre-existing pyright warnings in dung_z3.py (z3 type stubs) and argumentation.py (compute_consistent_beliefs LoadedClaimFile call) — not introduced by our changes
- `_SUPPORT_TYPES` now used in build_argumentation_framework for Cayrol support collection
- `_ATTACK_TYPES` flagged as unused by pyright — it's used conceptually but the check is `not in _NON_ATTACK_TYPES` and `in _UNCONDITIONAL_TYPES` / `in _PREFERENCE_TYPES`. Pre-existing.

## TEST FAILURE
test_complete_extensions_with_attacks fails:
- Setup: args={A,B}, defeats={}, attacks={(A,B)}
- Expected: {A} is a complete extension
- Actual: complete_extensions returns []

Analysis: complete_extensions requires S to be a fixed point of F AND admissible.
- F({A}) = {a | {A} defends a using defeats}. Since defeats is empty, no arg has attackers (in the defeat sense), so every arg is defended by any set. F({A}) = {A, B}.
- But F({A}) = {A, B} != {A}, so {A} is not a fixed point of F.
- F({A,B}) = {A, B}, so {A,B} is a fixed point. But {A,B} is not admissible (attack-based CF fails).
- F({}) = {A, B} (both unattacked in defeats). {} != {A,B}, not a fixed point.
- So no set is both a fixed point of F and attack-conflict-free. Result: []

This is actually correct behavior! When defeats is empty but attacks exist, the characteristic function says "everyone is defended" but attack-based CF rejects the full set. This is a genuine consequence of the split between attacks and defeats.

Fix: my test expectation was wrong. With no defeats, F always converges to all args. The only fixed point is {A,B}, which fails attack-CF. So complete_extensions=[] is correct. Need to fix the test.

Similarly for stable_extensions test — need to verify what the correct behavior is.

## NEXT
1. Fix test_complete_extensions_with_attacks expectation
2. Fix test_stable_extensions_with_attacks if needed
3. Re-run full suite
4. Write report
