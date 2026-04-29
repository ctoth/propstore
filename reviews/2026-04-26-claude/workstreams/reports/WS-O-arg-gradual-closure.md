# WS-O-arg-gradual Closure Report

Closed in propstore commit `fcbc77b1` after pinning `formal-argumentation` to pushed upstream commit `dbb036b9968b370856c22cb2ebf6157a72587956`.

## Upstream argumentation

- `0757b83` added the Rago 2016 DF-QuAD graph kernel; `f6de501` added continuous Potyka integration; `227cfa6` deleted the old probabilistic DF-QuAD production surface; `97c8bd8` routed probabilistic DF-QuAD through the graph kernel.
- `609cd1e` added Matt-Toni game strength; `3721f3a` added Gabbay equational semantics; `cee83ac` added Baroni principle predicates; `c8bc3e0` added hard tau validation.
- `3afedda`, `f91df1b`, `64f8b64`, `9a7168c`, and `dbb036b` added and fixed the missing named property/relation gates for DF-QuAD, Matt-Toni, Potyka, and Gabbay.
- Focused upstream gate: `31 passed in 1.09s` for the WS-O gradual test set, including `test_workstream_o_arg_gradual_done.py`.
- Type gate: `uv run pyright src` passed with 0 errors.
- Push: upstream `main` was pushed through `dbb036b9968b370856c22cb2ebf6157a72587956`.

The full upstream test suite was not completed in this execution. An earlier full run hit an existing ASPIC Hypothesis memory blowup around the rationality-postulate tests, with process memory near 96 GB. The focused WS-O gradual gate passed after the final property gates were added.

## Propstore

- Final dependency commits: `865f4d05` updated `pyproject.toml`, `a93bb208` updated `uv.lock`, and `fcbc77b1` updated the pin sentinel to `dbb036b9968b370856c22cb2ebf6157a72587956`.
- Propstore migration commits include `72ffb345`, `2dfd95f1`, and `bd90b9e5` for DF-QuAD graph API consumers, plus `0cdbeb66` and `166c6f46` for boundary documentation.
- Targeted gate: `powershell -File scripts/run_logged_pytest.ps1 -Label arg-gradual-property-pin tests/architecture/test_argumentation_pin_gradual.py tests/test_fragility.py tests/test_dfquad.py` passed with `83 passed in 5.48s`; log `logs/test-runs/arg-gradual-property-pin-20260428-214828.log`.
- Package type gate: `uv run pyright propstore` passed with 0 errors.
- Architecture gate: `uv run lint-imports` passed with 4 contracts kept and 0 broken.
- Full final gate: `powershell -File scripts/run_logged_pytest.ps1 -Label arg-gradual-property-full-final-n0 -n 0` passed with `3214 passed in 555.88s`; log `logs/test-runs/arg-gradual-property-full-final-n0-20260428-214915.log`.

The first propstore full run timed out in `tests/test_aspic_bridge.py::TestBridgeRationalityPostulates::test_sub_argument_closure`. The isolated test then passed, and subsequent full reruns passed.

## Paper Contract

- Rago 2016 DF-QuAD, pp. 65-66: support and attack sequences use noisy-or aggregation, `1 - product(1 - v_i)`. Combined influence is support aggregate minus attack aggregate. Final aggregation is `b + c(1-b)` for positive `c` and `b + cb` for negative `c`, so equal support and attack leaves base score `b` unchanged.
- Rago/Cyras/Toni 2016 bipolar DF-QuAD, p. 35: a neutral BAF base is `0.5`; with support product `Sprod = product(1 - s_i)` and attack product `Aprod = product(1 - a_j)`, neutral target strength is `0.5 + 0.5 * (Aprod - Sprod)`.
- `argumentation.dfquad` implements supports as `source_strength * support_weight`, bounded to `[0, 1]`; attacks use attacker strength. Missing QuAD tau is a hard `ValueError` at the probabilistic boundary.

Page citations are actual paper page numbers, not page-image artifact indices.

## Issues Surfaced

- The first closure audit found four missing exact upstream gate files named in the workstream: `test_dfquad_baroni_2019_principles.py`, `test_matt_toni_baroni_2019_compliance.py`, `test_potyka_convergence_on_stiff_graphs.py`, and `test_gabbay_equational_relation_to_dung.py`. They were added and pushed before the final propstore pin.
- The upstream full suite remains unproven because of the existing ASPIC Hypothesis memory blowup. This workstream closes on the focused upstream gradual gate plus full propstore verification.
- No `propstore/grounding/...` Opinion-producing gradual-strength consumers exist in the current code; the WS-O kernel provenance requirement is therefore inapplicable on the propstore side for this workstream.
