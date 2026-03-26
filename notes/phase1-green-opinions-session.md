# Phase 1 Green: Wire Real Opinions Into Pipeline

Date: 2026-03-25

## GOAL
Make the 5 failing tests pass by wiring CorpusCalibrator and calibration_counts into the opinion pipeline.

## DONE
- Read all referenced files: prompt, scout report, red report, Josang 2001 notes
- Read source files: relate.py, calibrate.py, opinion.py, build_sidecar.py
- Read test files: test_relate_opinions.py, test_calibrate.py

## 5 FAILING TESTS
1. `test_corpus_calibrator_reduces_uncertainty` - TypeError: _classify_stance_async() got unexpected kwarg 'reference_distances'
2. `test_no_reference_distances_stays_vacuous` - Same TypeError
3. `test_corpus_and_categorical_fused_via_consensus` - Same TypeError + 'calibration_counts'
4. `test_categorical_to_opinion_with_loaded_counts` - ImportError: cannot import 'load_calibration_counts'
5. `test_load_calibration_counts_empty_table` - Same ImportError

## CHANGES NEEDED
1. **relate.py**: Add `reference_distances` and `calibration_counts` params to `_classify_stance_async`. After categorical_to_opinion call, create CorpusCalibrator opinion and fuse via consensus_pair. Guard for dogmatic opinions. Pass calibration_counts to categorical_to_opinion.
2. **calibrate.py**: Add `load_calibration_counts(conn)` function.
3. **build_sidecar.py**: Add `calibration_counts` table to `_create_claim_tables()`.

## NEXT
- Implement changes in order: calibrate.py, build_sidecar.py, relate.py
- Run all tests
- Commit
