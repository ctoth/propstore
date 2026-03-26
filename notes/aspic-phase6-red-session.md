# ASPIC+ Phase 6 Red: Rationality Postulates

Date: 2026-03-25

## GOAL
Write 8 rationality postulate property tests + well_formed_csaf() composite strategy + CSAF dataclass + regression test. All must FAIL (red phase).

## DONE (reading)
- Read prompt: `prompts/aspic-phase6-red.md`
- Read Modgil 2018 notes: Thms 12-15, Def 12, Def 14, Def 18
- Read Prakken 2010 notes (first 50 lines — enough for Thm 6.10 context)
- Read `propstore/aspic.py` fully: has Literal, Rule, ContrarinessFn, Argument types, build_arguments, compute_attacks, compute_defeats, transposition_closure, property functions (conc, prem, sub, top_rule, def_rules, last_def_rules, prem_p, is_firm, is_strict). NO CSAF dataclass. NO strict_closure.
- Read `propstore/dung.py` fully: has ArgumentationFramework, conflict_free, complete_extensions, preferred_extensions, stable_extensions, grounded_extension
- Read `tests/test_dung.py` fully: has argumentation_frameworks() strategy, af_with_attacks_superset() strategy, property tests with 200 examples
- Read `reports/hypothesis-aspic-feasibility.md` fully: strategy architecture, pseudocode for well_formed_csaf()
- Read `tests/test_aspic.py` first 100 lines: has logical_language() strategy, imports from aspic

## OBSERVATIONS
1. `propstore/aspic.py` already has: Literal, Rule, ContrarinessFn, PremiseArg, StrictArg, DefeasibleArg, Attack, KnowledgeBase, PreferenceConfig, ArgumentationSystem, build_arguments, compute_attacks, compute_defeats, transposition_closure
2. Missing from aspic.py: CSAF dataclass, strict_closure function
3. `propstore/dung.py` has conflict_free (takes frozenset[str] and relation)
4. Existing strategies in test_aspic.py: logical_language() at minimum. Need to read rest.
5. Tests should fail with ImportError for strict_closure and/or CSAF

## DONE (reading complete)
- Read full test_aspic.py (1757 lines, 49 existing tests across 8 classes)
- Existing strategies: logical_language(), strict_rules(), defeasible_rules(), knowledge_base(), preference_config()
- Helper functions: _transitive_closure_pairs(), _has_cycle()
- File ends at line 1757 with TestDefeatConcrete

## IN PROGRESS
- Added TYPE_CHECKING import for ArgumentationFramework to aspic.py
- Need to: add CSAF dataclass to end of aspic.py, write well_formed_csaf() + 9 tests at end of test_aspic.py
- Prompt says defeats in CSAF is frozenset[tuple[Argument, Argument]] but compute_defeats returns frozenset[Attack]
  - Strategy must extract (attacker, target) pairs from Attack objects for the defeat tuples
  - The AF.defeats needs string ID pairs, derived from CSAF.defeats via arg_to_id mapping

## COMPLETED
- Added CSAF dataclass to aspic.py (with TYPE_CHECKING import for ArgumentationFramework)
- Added well_formed_csaf() composite strategy to test_aspic.py
- Added 8 rationality postulate property tests (TestRationalityPostulates)
- Added 1 regression test (TestRationalityPostulatesConcrete::test_married_bachelor_consistency)
- Verified tests FAIL with ImportError for strict_closure
- Verified test_dung.py still passes (45 passed, no regression)
- Committed: 45b06a6
- Wrote report: reports/aspic-phase6-red.md

## BLOCKER FOR GREEN
- `strict_closure()` must be implemented in `propstore/aspic.py`
- Once implemented, all tests should become runnable (may still fail if implementation is wrong)
