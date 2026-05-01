# WS-P Closure Report

Workstream: WS-P — CEL / units / equations

Closing implementation commit: `99f2a666`

## Findings Closed

- T2.4 / Codex #30 / G-H1: CEL ternary typing now requires a boolean condition and unified branch types.
- T2.12 / Codex #29 / G-H4: Z3 division partiality is represented by typed definedness projections, including OR and ternary short-circuit behavior.
- T2.13 / G-M5 / G-M6: CEL float exponent literals and standard escapes are accepted according to the local CEL spec.
- Codex #28: parameter conflict detection threads form metadata so unit-compatible values normalize before comparison.
- Codex #31 / G-M8: equation comparison and equation signatures are orientation/role invariant.
- Codex #32: SymPy generation separates RHS generation from full-equation generation; the old LHS-dropping API was deleted.
- Codex #33 / D-14: algorithm conflict suppression accepts proof tiers `CANONICAL`, `SYMPY`, and `PARTIAL_EVAL`; `Tier.BYTECODE` references are gone.
- Codex #34: algorithm validation uses scoped free-variable extraction instead of all-name extraction.
- G-H2 / G-M4: temperature delta units and form-declared units are represented in schemas/resources and registered into Pint.
- G-H3 / Codex 1.11: domain-aware symbolic equation equivalence returns `EQUIVALENT` only under explicit assumptions and `UNKNOWN` otherwise.
- G-M1 / G-M2: CEL type errors no longer get masked by absorbing `UNKNOWN` and unary operator result coercion.
- G-M3: Z3 solver registries are defensively snapshotted.

## Tests Written First

- `tests/test_cel_ternary_unification.py` failed because the condition type was not checked and false-branch type was discarded.
- `tests/test_z3_division_definedness.py` failed because division guards were globally conjoined rather than carried through CEL definedness semantics.
- `tests/test_parameter_conflict_unit_aware.py` failed because the conflict detector never passed forms into value comparison.
- `tests/test_equation_orientation.py` and `tests/test_equation_signature_role_invariance.py` failed because equation identity was sign- and role-sensitive.
- `tests/test_log_product_under_positive_reals.py`, `tests/test_exp_sum_under_reals.py`, and `tests/test_sqrt_square_under_nonnegative_reals.py` failed because comparison had no explicit domain-assumption channel or honest `UNKNOWN`.
- `tests/test_sympy_generator_no_lhs_drop.py` failed because equation input was silently truncated to the RHS.
- `tests/test_algorithm_sympy_tier_not_conflict.py` and `tests/test_algorithm_free_variable_locals.py` failed because ast-equiv proof tiers and free-variable APIs were misused.
- `tests/test_temperature_delta_unit.py`, `tests/test_cel_float_exponent.py`, and `tests/test_cel_string_escapes.py` failed on missing delta-unit and CEL grammar support.
- `tests/test_workstream_p_done.py` remained a red sentinel until the WS-P gates were satisfied.

## Verification

- `powershell -File scripts/run_logged_pytest.ps1 -Label WS-P ...` passed: `61 passed`, log `logs/test-runs/WS-P-20260430-180542.log`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label WS-P-focused ...` passed: `174 passed`, log `logs/test-runs/WS-P-focused-20260430-180610.log`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label WS-P-z3-old-guard-tests tests/test_z3_conditions.py::TestZ3GuardStateLeak tests/test_z3_division_definedness.py` passed: `8 passed`, log `logs/test-runs/WS-P-z3-old-guard-tests-20260430-181735.log`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label WS-P-contract-manifest tests/test_contract_manifest.py` passed: `8 passed`, log `logs/test-runs/WS-P-contract-manifest-20260430-181946.log`.
- `uv run pyright propstore` passed with 0 errors.
- `uv run lint-imports` passed.
- `git grep "Tier\.BYTECODE" -- propstore tests` returned zero hits.
- `git grep "FreshConst" -- propstore` returned zero hits.
- Full suite passed: `3547 passed, 2 skipped`, log `logs/test-runs/WS-P-full-final-20260430-182050.log`.

## Property-Based Gates

- CEL string escapes now include a Hypothesis round-trip/property gate.
- Z3 division definedness includes generated OR and ternary short-circuit properties.
- Algorithm tier conflict suppression includes a generated proof-tier property.
- Existing WS-P-adjacent equation, form, and conflict-detector property suites remained green in the focused and full runs.

## Files Changed

- CEL and condition typing: `propstore/cel_checker.py`, `propstore/cel_types.py`, `propstore/z3_conditions.py`, `propstore/core/conditions/z3_backend.py`.
- Units/forms: `propstore/dimensions.py`, `propstore/unit_dimensions.py`, `propstore/families/forms/*`, `propstore/_resources/forms/temperature.yaml`, form schemas and generated schema resources.
- Conflicts/equations: `propstore/value_comparison.py`, `propstore/conflict_detector/*`, `propstore/equation_comparison.py`, `propstore/sympy_generator.py`.
- Algorithm validation: `propstore/families/claims/passes/checks.py`, ast-equiv tier/free-variable call sites.
- Contracts and closure metadata: `propstore/contracts.py`, `propstore/contract_manifests/semantic-contracts.yaml`, `docs/gaps.md`, this workstream file, and `reviews/2026-04-26-claude/workstreams/INDEX.md`.

## Remaining Risks

- No WS-P finding is deferred.
- Paper notes for several cited papers remain absent, but that is tracked as a paper-faithful workflow issue outside WS-P; the implemented CEL escape and conditional behavior was checked against the local CEL spec at `~/src/cel-spec`.
