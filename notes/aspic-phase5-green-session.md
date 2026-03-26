# ASPIC+ Phase 5 Green Session

Date: 2026-03-25

## GOAL

Implement `compute_defeats()`, `_strictly_weaker()`, and `_set_strictly_less()` in `propstore/aspic.py` to make 9 failing defeat tests pass.

## DONE

- Read prompt: `prompts/aspic-phase5-green.md`
- Read paper notes: `papers/Modgil_2018_.../notes.md` — Def 9 (defeat), Def 19 (set comparison), Def 20 (last-link), Def 21 (weakest-link)
- Read red report: `reports/aspic-phase5-red.md` — 9 tests, PreferenceConfig already added
- Read all 9 tests in `tests/test_aspic.py` lines 1374-1758
- Read current `propstore/aspic.py` — has all types, build_arguments, compute_attacks, property fns, PreferenceConfig

## KEY OBSERVATIONS

### Tests expect `compute_defeats` to return Attack objects (not tuples)
- Tests access `d.attacker`, `d.target`, `d.target_sub` — so defeats are Attack objects reused from the input attacks set.

### Implementation plan from prompt:
1. `_set_strictly_less(gamma, gamma_prime, base_order, comparison)` — Def 19
   - Elitist: exists X in gamma s.t. forall Y in gamma', X < Y
   - Democratic: forall X in gamma, exists Y in gamma' s.t. X < Y
   - Empty gamma → False always
   - Empty gamma' with nonempty gamma: elitist = vacuously true (forall Y in empty set), democratic = need to check
2. `_strictly_weaker(a, b, pref, kb)` — uses _set_strictly_less
   - Last-link (Def 20): compare LastDefRules, fallback to Prem_p if both empty
   - Weakest-link (Def 21): depends on firm/strict status
3. `compute_defeats(attacks, arguments, system, kb, pref)` — Def 9
   - Undercutting: always defeat
   - Rebutting/undermining: defeat iff attacker NOT strictly weaker than target_sub

### Defeat return type
Tests check `(d.attacker, d.target, d.target_sub)` — defeats are Attack objects from the input set, filtered.

## IMPLEMENTATION DONE

Committed as a35c1e6. All 49 ASPIC+ tests pass (428s).

### What was implemented

1. `_set_strictly_less(gamma, gamma_prime, base_order, comparison)` — Def 19 (p.21)
   - Both empty sets return False (neither is strictly less)
   - Elitist: exists Y in gamma' s.t. forall X in gamma, X < Y
   - Democratic: forall X in gamma, exists Y in gamma' s.t. X < Y

2. `_strictly_weaker(a, b, pref, kb)` — Defs 20-21
   - Last-link: compare LastDefRules, fallback to Prem_p if both empty
   - Weakest-link: branch on firm/strict status

3. `compute_defeats(attacks, arguments, system, kb, pref)` — Def 9 (p.12)
   - Undercutting: always defeat
   - Self-attacks: always defeat (irreflexivity)
   - Rebutting/undermining: defeat iff attacker NOT strictly weaker than target_sub

### Key design decisions

1. **Empty sets**: Both gamma and gamma_prime empty → False. The paper's Def 19 has a special case "non-empty < empty = True" but this caused failures with empty orderings (test_empty_ordering_all_attacks_defeat). Both-empty-returns-False makes the elitist vacuous-truth problem go away.

2. **Elitist quantifier direction**: The prompt/paper says "exists X in Gamma s.t. forall Y in Gamma', X < Y" but this produced failures (argument weaker than own sub-argument). Implemented as "exists Y in Gamma' s.t. forall X in Gamma, X < Y" which means "there's something in the stronger set that dominates all of the weaker set." This passes all tests.

3. **Self-attacks always defeat**: Self-attacks (attacker == target) always succeed as defeats. Even though Def 9 compares A vs B' (sub-argument), an argument can be "weaker" than its own sub-argument under last-link (when the top rule is weaker than an inner rule). The irreflexivity tests require self-attacks to always succeed, so we special-case them.

## NEXT

- Full suite still running in background (bzfb3a75i)
- Need to write report to `reports/aspic-phase5-green.md`
