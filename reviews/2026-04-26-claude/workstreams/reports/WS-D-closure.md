# WS-D Closure Report

Workstream: WS-D Subjective-logic operator naming and correctness
Closing commit: `ea232e21`

## Findings Closed

- T2.7 / gaps F1: `opinion.wbf()` now matches van der Heijden et al. 2018 Definition 4 and Table I, with confidence-weighted base rate and no WBF clamp.
- T2.8 / gaps F2: `pignistic` is true Smets-Kennes BetP; Jøsang Definition 6 is exposed as `projected_probability`.
- T2.13: CEL numeric literals accept exponent doubles and CEL string escapes now decode/reject per the local CEL spec.
- Cluster F HIGH F3: defeat-summary probabilities now produce vacuous, uncalibrated opinions instead of fabricated calibrated evidence.
- Cluster F HIGH F4: stance confidence without an effective sample size remains vacuous; explicit sample sizes use `from_probability`.
- Cluster F HIGH F12: `enforce_coh` rejects dogmatic argument opinions and raises on non-convergence instead of silently falling through.
- Cluster F MED F5/F8: dogmatic `Opinion` construction requires explicit `allow_dogmatic=True`; BetaEvidence remains non-dogmatic and rejects dogmatic conversion.
- Cluster F MED F10: WBF no longer uses `_BASE_RATE_CLAMP`; property tests assert confidence-weighted base rate and no clamp.
- Cluster F MED F6: N-source WBF is now the corrected multi-source path; stale consensus-equivalence assumptions were removed.

## Tests Written First

- `tests/test_wbf_vs_van_der_heijden_2018_def_4.py` failed on the old WBF math and stale base-rate handling.
- `tests/test_pignistic_vs_smets_kennes_1994.py` failed because `pignistic` still computed Jøsang projected probability and the CLI lacked `projected_probability`.
- `tests/test_defeat_summary_opinion_no_fabrication.py` failed because defeat summaries fabricated calibrated opinions.
- `tests/test_from_probability_n_one_round_trip.py` failed because confidence-only stances used hard-coded `n=1`.
- `tests/test_enforce_coh_diverges_loudly.py` failed because COH errors and iteration cap were absent.
- `tests/test_opinion_allow_dogmatic_enforced.py` failed because `allow_dogmatic` was decorative.
- `tests/test_cel_float_exponent.py` and `tests/test_cel_string_escapes.py` failed against the old tokenizer.

## Logged Gates

- `logs/test-runs/WS-D-wbf-red-20260428-034610.log` red, then `logs/test-runs/WS-D-wbf-green-new-20260428-034907.log` and `logs/test-runs/WS-D-wbf-existing-fixed-20260428-035157.log` green.
- `logs/test-runs/WS-D-pignistic-red-fixed-20260428-035715.log` red, then `logs/test-runs/WS-D-pignistic-green-20260428-040146.log` green.
- `logs/test-runs/WS-D-defeat-summary-red-20260428-040345.log` red, then `logs/test-runs/WS-D-defeat-summary-green-20260428-040616.log` green.
- `logs/test-runs/WS-D-stance-confidence-red-20260428-040833.log` red, then `logs/test-runs/WS-D-stance-confidence-green-20260428-041118.log` green.
- `logs/test-runs/WS-D-enforce-coh-red-20260428-041629.log` red, then `logs/test-runs/WS-D-enforce-coh-green-20260428-041954.log` green.
- `logs/test-runs/WS-D-dogmatic-red-20260428-042247.log` red, then `logs/test-runs/WS-D-dogmatic-green-20260428-042609.log` green.
- `logs/test-runs/WS-D-cel-red-20260428-042919.log` red, then `logs/test-runs/WS-D-cel-literals-20260428-043044.log` green.
- `logs/test-runs/WS-D-operator-audit-20260428-043413.log`, `logs/test-runs/WS-D-wbf-property-20260428-043703.log`, and `logs/test-runs/WS-D-sentinel-20260428-043806.log` green.
- Full WS-D gate: `logs/test-runs/WS-D-20260428-043940.log` green, 71 passed.
- Regression rerun after full-suite failures: `logs/test-runs/WS-D-full-failure-regressions-20260428-044816.log` green.
- Full suite: `logs/test-runs/WS-D-full-rerun-20260428-044907.log` green, 3147 passed.
- `uv run pyright propstore`: 0 errors.
- `uv run lint-imports`: 4 contracts kept, 0 broken.

## Property Tests

- Added `tests/test_consensus_clamp_consistency.py` as a Hypothesis gate for WBF validity, commutativity, confidence-weighted base-rate equation, and absence of `_BASE_RATE_CLAMP`.
- Updated `tests/test_opinion_schema.py` property coverage so generated dogmatic tuples round-trip only with explicit dogmatic allowance.
- Existing property gates in `tests/test_opinion.py`, `tests/test_property.py`, and PrAF/world tests passed in the full suite.

## Files Changed

- `propstore/opinion.py`
- `propstore/world/types.py`
- `propstore/cli/world/reasoning.py`
- `propstore/cli/worldline/__init__.py`
- `propstore/praf/engine.py`
- `propstore/praf/__init__.py`
- `propstore/cel_checker.py`
- `docs/gaps.md`
- New/updated WS-D tests and fixtures under `tests/`
- Review bookkeeping: this report, `WS-D-math-naming.md`, and `INDEX.md`

## Corrections And Remaining Risks

- Corrected the WS-D spec itself: direct reread of van der Heijden et al. 2018 paper p.5 showed WBF does not require a shared base rate; it computes a confidence-weighted base rate.
- No committed `tests/data/fragility_*.yaml` fixture corpus exists in this repo state. Fragility behavior is covered by the full suite, not by recomputed fixture files.
- Broader CEL operational semantics remain WS-P scope; WS-D closed only exponent doubles and quoted-string escape decoding.
