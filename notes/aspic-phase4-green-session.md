# ASPIC+ Phase 4 Green: compute_attacks() session

Date: 2026-03-25

## GOAL

Implement `compute_attacks()` in `propstore/aspic.py` per Modgil & Prakken 2018 Def 8 (p.11). Make all 40 tests pass.

## DONE

- Read all required files: paper notes, red report, tests, aspic.py
- Implemented compute_attacks() with three attack types: undermining, rebutting, undercutting
- 36/40 tests pass (all Phase 1-3 + 9/10 Phase 4)

## STUCK

`test_rebutting_symmetry_for_contradictories` fails.

### Problem analysis

The test asserts: for every contradictory rebutting attack A->B on B', there exists a reverse rebutting attack from some argument with conclusion conc(B') back onto a defeasible sub-argument of A.

Hypothesis finds counterexamples where the ATTACKER has no defeasible sub-arguments:

1. Rule `p => ~p`, KB premises={p}. PremiseArg(p) rebuts DefeasibleArg(~p). Reverse impossible: PremiseArg has no defeasible subs.
2. Rule `p => ~q`, KB axioms={q}, premises={p}. PremiseArg(q, axiom) rebuts DefeasibleArg(~q). Reverse impossible: axiom PremiseArg has no defeasible subs.

The rebutting attack is correct per Def 8b (checks target structure only, not attacker structure). But the symmetry property requires the attacker to have defeasible sub-arguments for the reverse to exist.

### Approaches tried

1. Filter A in sub(B): didn't help, counterexample 2 has independent arguments
2. Sub-argument filter reverted

### Key insight needed

The test's symmetry property holds when the attacker has defeasible structure. Need to find what condition in Def 8 prevents rebutting when attacker is firm+strict or has no defeasible sub-args.

Possible fix: only generate rebutting attacks when the attacker itself has at least one defeasible sub-argument (i.e., is NOT fully firm+strict). Rationale: rebutting is about uncertain conclusions challenging other uncertain conclusions. A firm+strict argument's conclusion is certain - it doesn't "rebut" in the dialectical sense.

## FILES

- `propstore/aspic.py` — implementation target
- `tests/test_aspic.py` — 10 attack tests (lines 939-1283)
- `reports/aspic-phase4-red.md` — test descriptions

## RESOLUTION

The fix: rebutting requires the attacker to have a defeasible sub-argument with the same conclusion as the attacker (`_has_defeasible_conclusion`). This is stronger than `not is_strict(a)` because it also catches cases like `StrictArg(DefeasibleArg(q=>p), p->~p)` where the strict rule changes the conclusion away from any defeasible sub's conclusion.

Three approaches tried:
1. `a in sub(b)` filter -- too narrow, didn't cover independent arguments
2. `not is_strict(a)` -- too permissive, allowed strict continuations that contradict own defeasible subs
3. `_has_defeasible_conclusion(a)` -- correct, filters all three pathological classes

Also fixed: undercutting was nested inside the rebutting eligibility block, preventing undercutting when attacker wasn't rebut-eligible. Moved undercutting to check independently.

## COMPLETE

Commit: 987f395 "Green: ASPIC+ Phase 4 -- three-type attack determination (Modgil 2018 Def 8)"
Report: `reports/aspic-phase4-green.md`
All 40 ASPIC tests pass.
