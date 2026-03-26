# Phase 2 Red: Conflicts-to-AF Integration Tests

Date: 2026-03-25

## GOAL
Write 5 failing tests for conflict-derived defeats in the AF.

## DONE
- Read prompt, scout report, source files
- Added `conflicts` table to `create_argumentation_schema` in conftest.py
- Added `conflicts()` method to `SQLiteArgumentationStore`
- Wrote 5 tests in `TestConflictDerivedDefeats` class

## OBSERVATIONS
- `ArgumentationFramework` has NO `supports` or `attack_relations` attributes
- Those live on `ClaimGraphRelations` (internal to `_collect_claim_graph_relations`)
- `build_argumentation_framework` returns only `ArgumentationFramework(arguments, defeats, attacks)`
- `build_praf` returns `ProbabilisticAF` which has the relation details

## FIX NEEDED
- `test_real_stance_takes_precedence_over_conflict`: remove `af.supports` assertion — just check defeats
- `test_conflict_synthetic_stances_have_vacuous_opinions`: use `build_praf` instead of `build_argumentation_framework` to access `attack_relations`, OR test via inspecting the PrAF

## CURRENT STATE
- 4 of 5 new tests fail (correct for red phase)
- 1 passes (PHI_NODE — no defeats expected, none generated)
- 2 tests fail for wrong reasons (AttributeError) — need fixing
- Pre-existing tests not yet verified (cancelled due to parallel error)

## NEXT
1. Fix the two tests with wrong failure modes
2. Verify all 4 should-fail tests fail with correct assertion errors
3. Verify pre-existing tests pass
4. Commit
5. Write report
