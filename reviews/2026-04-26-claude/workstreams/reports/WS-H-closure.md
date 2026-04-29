# WS-H closure: Probabilistic argumentation correctness

Workstream: WS-H
Closed: 2026-04-29
Closing implementation commit: `dd69f2bd`

## Findings closed

- Codex #14: `praf-paper-td-complete` now routes to paper-TD complete extension-probability mode instead of ordinary argument acceptance.
- Codex #15: uncalibrated PrAF arguments are retained in the kernel topology with vacuous opinions and explicit omission diagnostics; target omissions are surfaced by world resolution rather than silently producing a winner.
- Codex #16 / Cluster F #4: raw stance confidence no longer fabricates dogmatic or one-sample evidence; missing evidence count returns `NoCalibration`.
- Cluster F #3 / #14: scalar defeat marginals no longer claim calibrated subjective-logic evidence.
- Cluster F #12: COH enforcement has typed convergence state and rejects dogmatic input without a magic pseudo-count.
- Cluster F #15: `PropstorePrAF` omission maps are immutable mapping proxies.
- Cluster F #16: local sensitivity reports `method="local_oat"` and a global variance-decomposition API exists.
- Cluster F #25: Brier score and log-loss are exposed as calibration metrics.
- Codex #17 and D-18 consumer gates: propstore-side test scaffolds exist and remain explicitly skipped where the WS-H spec requires successor/upstream gating.

## Red tests

- `tests/test_praf_paper_td_complete_routing.py`: failed because resolver requested argument acceptance instead of extension probability.
- `tests/test_praf_uncalibrated_explicit.py`: failed because uncalibrated arguments were deleted from the PrAF topology.
- `tests/test_praf_raw_confidence_not_dogmatic.py`: failed because `confidence=1.0` became dogmatic evidence and raw confidence without evidence count was promoted.
- `tests/test_defeat_summary_opinion_honest.py`: failed because scalar defeat summaries claimed calibrated provenance.
- `tests/test_enforce_coh_convergence.py`: failed because convergence was not observable and dogmatic inputs had a hidden pseudo-count.
- `tests/test_sensitivity_global_method_or_honest_naming.py`: failed because sensitivity did not name local OAT and had no global method.
- `tests/test_calibrate_brier_and_log_loss.py`: failed because Brier/log-loss were absent.
- `tests/test_praf_frozen_immutable.py`: failed because omission maps were mutable.
- `tests/test_praf_argument_enumeration_budget.py`: added as a correctly skipped WS-O-gun/WS-M successor gate.
- `tests/test_workstream_h_done.py`: added as the WS-H sentinel.

## Verification

- `powershell -File scripts/run_logged_pytest.ps1 -Label WS-H-red-fixed ...` -> 11 failed, 3 passed, 1 skipped; log `logs/test-runs/WS-H-red-fixed-20260429-143439.log`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label WS-H-praf-green ...` -> 9 passed, 1 skipped; log `logs/test-runs/WS-H-praf-green-20260429-143725.log`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label WS-H-calibration-metrics tests/test_calibrate_brier_and_log_loss.py` -> 3 passed; log `logs/test-runs/WS-H-calibration-metrics-20260429-143836.log`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label WS-H-sensitivity tests/test_sensitivity_global_method_or_honest_naming.py tests/test_sensitivity.py` -> 9 passed; log `logs/test-runs/WS-H-sensitivity-20260429-143942.log`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label WS-H tests/test_praf_paper_td_complete_routing.py tests/test_praf_uncalibrated_explicit.py tests/test_praf_raw_confidence_not_dogmatic.py tests/test_defeat_summary_opinion_honest.py tests/test_enforce_coh_convergence.py tests/test_sensitivity_global_method_or_honest_naming.py tests/test_calibrate_brier_and_log_loss.py tests/test_praf_frozen_immutable.py tests/test_praf_argument_enumeration_budget.py tests/test_workstream_h_done.py` -> 14 passed, 1 skipped; log `logs/test-runs/WS-H-20260429-145057.log`.
- `uv run pyright propstore` -> 0 errors.
- `uv run lint-imports` -> 4 contracts kept, 0 broken.
- `powershell -File scripts/run_logged_pytest.ps1 -Label WS-H-full` -> 3358 passed, 2 skipped; log `logs/test-runs/WS-H-full-20260429-145111.log`.

## Property-based tests

- Added Hypothesis coverage for scalar defeat-summary opinions over probabilities in `[0, 1]`.
- Added/generated property-style coverage around PrAF topology preservation and omission-map immutability.
- The argument-enumeration budget property remains skipped by design until WS-O-gun plus WS-M expose the budget-exhaustion surface to this consumer path.

## Files changed

- `propstore/praf/engine.py`
- `propstore/praf/__init__.py`
- `propstore/core/analyzers.py`
- `propstore/world/resolution.py`
- `propstore/calibrate.py`
- `propstore/sensitivity.py`
- `docs/gaps.md`
- `tests/test_praf_paper_td_complete_routing.py`
- `tests/test_praf_uncalibrated_explicit.py`
- `tests/test_praf_raw_confidence_not_dogmatic.py`
- `tests/test_defeat_summary_opinion_honest.py`
- `tests/test_enforce_coh_convergence.py`
- `tests/test_sensitivity_global_method_or_honest_naming.py`
- `tests/test_calibrate_brier_and_log_loss.py`
- `tests/test_praf_frozen_immutable.py`
- `tests/test_praf_argument_enumeration_budget.py`
- `tests/test_workstream_h_done.py`
- `tests/test_from_probability_n_one_round_trip.py`
- `tests/test_praf.py`
- `tests/test_review_regressions.py`
- `tests/test_world_model.py`

## Remaining risks / successors

- `tests/test_praf_argument_enumeration_budget.py` is intentionally skipped until WS-M flips the propstore consumer to request argument-set return against the WS-O-gun `EnumerationExceeded` surface.
- `tests/test_dfquad_attack_support_per_paper_contract.py` remains an upstream-contract scaffold; WS-O-arg-gradual has closed, but the propstore consumer assertion remains a successor flip outside WS-H's close criteria.
