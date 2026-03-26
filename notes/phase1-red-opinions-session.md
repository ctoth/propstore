# Phase 1 Red: Failing Tests for Real Opinions

Date: 2026-03-25

## GOAL
Write 7 failing tests per prompts/phase1-red-opinions.md, commit, report.

## Required reading: DONE
- reports/phase1-scout-opinions.md — read
- Josang 2001 notes — read (consensus Thm 7, vacuous p.8, evidence Def 12)
- Guo 2017 notes — read (raw outputs not calibrated)
- Sensoy 2018 notes — read (evidence-to-opinion mapping)
- propstore/relate.py — read (line 196: categorical_to_opinion without calibration_counts)
- propstore/calibrate.py — read (CorpusCalibrator, categorical_to_opinion)
- propstore/opinion.py — read (consensus_pair at line 172)
- tests/test_relate_opinions.py — read (12 existing test classes)
- tests/test_calibrate.py — read (existing patterns, hypothesis tests)
- tests/test_opinion.py — read (valid_opinions strategy exists at line 362)
- tests/conftest.py — read (create_argumentation_schema)

## Key observations
1. _classify_stance_async has NO reference_distances param — tests 1-3 will fail with TypeError or vacuous opinions
2. No load_calibration_counts function exists — tests 4-5 will fail on import
3. consensus_pair already tested in test_opinion.py with hypothesis — test 6 can go there
4. CorpusCalibrator b+d+u=1 already tested in test_calibrate.py — test 7 can use different approach
5. valid_opinions strategy already exists in test_opinion.py (line 362)

## Plan
- Tests 1-3: Add to test_relate_opinions.py
- Tests 4-5: Add to test_calibrate.py
- Test 6: Add to test_opinion.py (consensus reduces uncertainty, hypothesis)
- Test 7: Add to test_calibrate.py (corpus opinion b+d+u=1, hypothesis)

## DONE
- All reading complete
- 7 tests written across 3 files
- Tests 1-3 (test_relate_opinions.py): FAIL as expected (TypeError: reference_distances not accepted)
- Tests 4-5 (test_calibrate.py): FAIL as expected (ImportError: load_calibration_counts doesn't exist)
- Test 6 (test_opinion.py): PASSES — guard test, consensus_pair already reduces uncertainty
- Test 7 (test_calibrate.py): PASSES — guard test, b+d+u=1 already holds
- 89 pre-existing tests PASS (unchanged)
- Committed: c047d58 "Red: failing tests for real opinions pipeline (Phase 1)"

## NEXT
- Write report to reports/phase1-red-opinions.md
