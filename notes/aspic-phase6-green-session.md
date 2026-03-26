# ASPIC+ Phase 6 Green Session

Date: 2026-03-25

## GOAL
Implement `strict_closure()` in `propstore/aspic.py` and fix any bugs to make all 8 rationality postulate tests pass on 200 random well-formed theories.

## DONE
- Read prompt file: `prompts/aspic-phase6-green.md`
- Read paper notes: `papers/Modgil_2018_.../notes.md` - Theorems 12-15 (rationality postulates), Def 3 (strict closure), Def 12 (well-defined c-SAF), Def 14 (attack-based conflict-free)
- Read red report: `reports/aspic-phase6-red.md` - 8 postulate tests + 1 concrete test added, all fail with ImportError on `strict_closure`
- Read full `propstore/aspic.py` - has all dataclasses, build_arguments, compute_attacks, compute_defeats, CSAF dataclass. Missing: `strict_closure` function
- Read full `propstore/dung.py` - has ArgumentationFramework (with attacks field), conflict_free, complete_extensions, grounded_extension
- Read tests/test_aspic.py lines 1-1199 (need to read remaining: postulate tests and well_formed_csaf strategy)

## KEY OBSERVATIONS
1. `strict_closure` needs to be a fixpoint: iterate strict rules, if all antecedents in set, add consequent
2. CSAF dataclass already exists in aspic.py
3. The AF has both `attacks` and `defeats` fields - postulate 7 checks conflict_free against attacks
4. The well_formed_csaf strategy and 8 postulate tests are in the remaining part of test_aspic.py (after line 1199)
5. Tests expect `strict_closure` to be importable from `propstore.aspic`

## FILES
- `propstore/aspic.py` - main implementation file to edit
- `tests/test_aspic.py` - test file (DO NOT MODIFY)
- `propstore/dung.py` - Dung AF layer (reference)
- `reports/aspic-phase6-red.md` - red report (reference)

## PROGRESS
- strict_closure implemented and working (postulates 1, 2 pass)
- Postulate 3 (direct consistency) FAILS: counterexample has axiom p and defeasible rule p => ~p
- Root cause: `rebut_eligible` filter in `compute_attacks` prevents firm+strict args from rebutting defeasible args
- Modgil & Prakken 2018 Def 8b places NO constraint on the attacker — only the target must have defeasible top rule
- The `rebut_eligible` check and `_has_defeasible_conclusion` function are WRONG — must be removed
- First edit removed the function def + rebut_eligible set, but `a in rebut_eligible` still referenced on line 593
- Need to also remove the `if a in rebut_eligible:` guard and dedent the rebutting body

## ALL 8 POSTULATES PASS (200 examples each, 239s total)

### Bugs Found and Fixed

1. **rebut_eligible filter (WRONG):** `compute_attacks` had a `rebut_eligible` check that prevented
   firm+strict arguments from rebutting defeasible arguments. Modgil & Prakken 2018 Def 8b places
   NO constraint on the attacker — only the target sub-argument must have a defeasible top rule.
   Removed the `_has_defeasible_conclusion` function and `rebut_eligible` set entirely.

2. **_is_degenerate_rule over-filtering (WRONG):** I initially added a check rejecting rules where
   any antecedent is the contrary of the consequent (e.g., `~r, p -> ~p`). This prevented valid
   transpositions from being generated. Rule `(p, p) -> r` needs transposition `(~r, p) -> ~p`
   to create counter-arguments for consistency. Reverted to only checking contradictory antecedent
   pairs (both φ and ~φ in antecedents).

3. **Axiom consistency check (NEW):** Added post-fixpoint check in `transposition_closure`: for each
   literal φ in L, compute Cl_Rs({φ}) and verify ~φ is not in the closure. If any literal is
   axiom-inconsistent, the rule set is degenerate and we return empty frozenset(). This catches
   multi-step contradiction chains (e.g., `~p -> q, q -> p` makes Cl_Rs({~p}) = {~p, q, p}).

## CURRENT STATE
- All 8 postulate tests PASS
- Need to run full test suite to check for regressions
- Then commit and write report

## NEXT
1. Run full test suite: test_aspic.py + test_dung.py
2. Commit
3. Write report
