# ASPIC+ Phase 5 Red: Defeat and Preference Ordering Properties

Date: 2026-03-25

## GOAL
Write Hypothesis property tests for defeat determination with last-link/weakest-link preference orderings per Modgil & Prakken 2018 Defs 9, 19-21. Tests must FAIL with ImportError for `compute_defeats`.

## DONE
- Read prompt: `prompts/aspic-phase5-red.md`
- Read all required papers: Modgil 2018 notes (Defs 9, 19-21), Prakken 2010 notes (Defs 6.12-6.17)
- Read `propstore/aspic.py` — has Literal, Rule, Argument types, build_arguments, compute_attacks, property functions (conc, prem, sub, top_rule, def_rules, last_def_rules, prem_p, is_firm, is_strict)
- Read all of `tests/test_aspic.py` (1283 lines, 40 tests across 4 phases)
- Read `reports/aspic-phase4-green.md`
- Added `PreferenceConfig` dataclass to `propstore/aspic.py` (after KnowledgeBase)

## FILES
- `propstore/aspic.py` — modified: added PreferenceConfig dataclass
- `tests/test_aspic.py` — TO DO: add preference_config strategy, TestDefeatProperties (7 tests), TestDefeatConcrete (2 tests)
- `reports/aspic-phase5-red.md` — TO DO: write report

## KEY OBSERVATIONS
- Existing strategies: logical_language(), strict_rules(), defeasible_rules(), knowledge_base()
- Existing test classes: TestLanguageProperties, TestLanguageConcrete, TestRuleProperties, TestTranspositionClosure, TestRuleConcrete, TestArgumentConstructionProperties, TestArgumentConstructionConcrete, TestAttackProperties, TestAttackConcrete
- Import line at top already imports: build_arguments, compute_attacks, conc, prem, sub, top_rule, def_rules, last_def_rules, prem_p, is_firm, is_strict
- Need to add: compute_defeats, PreferenceConfig to imports
- preference_config strategy needs: partial order generation (irreflexive + transitive), comparison mode, link mode

## NEXT
1. Write preference_config strategy and 9 test methods in test_aspic.py
2. Verify tests fail with ImportError
3. git add + commit
4. Write report
