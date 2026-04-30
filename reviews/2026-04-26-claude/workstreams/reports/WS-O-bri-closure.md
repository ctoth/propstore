# WS-O-bri closure

Closing propstore commit: `69241ae1`
Pushed Bridgman commit: `d0f20b5db359e4c95ff0ab08f494f2e09718063c`

## Findings closed

- HIGH-1: `verify_equation` is deleted from Bridgman and absent from exports/imports/call sites.
- HIGH-2 / Missing-1 / LOW-4: `verify_expr` handles transcendental dimensionless-argument checks, unsupported SymPy nodes, and nested `Eq` via `DimensionalError`, not swallowed `TypeError`.
- HIGH-3: `pow_dims` rejects non-`int` and bool exponents.
- MED-1: theta-glyph source scan is direct `pathlib`, not `git grep`.
- MED-2 / LOW-3: Bridgman README and CHANGELOG document all live APIs, exact exponent rules, and the v0.2.0 deletion boundary.
- MED-3: propstore concept checks no longer mark a failed symbolic warning as definitive verification.
- MED-4: propstore claim checks record Bridgman `DimensionalError` as an error diagnostic.
- Missing-3 / Missing-5: propstore delegates dimension signatures and theta canonicalization to Bridgman.
- Dead-import: propstore no longer imports `dims_of_expr` from Bridgman.

## Tests written first

- Bridgman red gates: `test_pow_dims_integer_guard.py`, `test_transcendentals.py`, `test_theta_glyph_source_scan.py`, `test_dimensions_canonical_signature.py`, `test_canonicalize_theta.py`, `test_verify_equation_deleted.py`, and `test_workstream_o_bri_done.py`.
- Propstore red gates: `tests/test_bridgman_signal_propagation.py` and `tests/test_bridgman_pin_post_deletion.py`.
- Initial propstore red run: `logs/test-runs/WS-O-bri-propstore-red-20260430-160128.log` failed with 4 failures: old Bridgman pin, swallowed claim/concept dimensional errors, and surviving `dims_of_expr` import.
- Added upstream property gates in `bridgman/tests/test_dimension_properties.py`; first generated run found and corrected an over-broad duplicate-key order-insensitivity property.

## Verification

- `cd ../bridgman && uv run pytest` -> `82 passed`.
- `cd ../bridgman && uv run pyright` -> `0 errors, 0 warnings, 0 informations`.
- `cd ../bridgman && uv run pytest tests/test_verify_equation_deleted.py -q` -> `3 passed`.
- `uv run pyright propstore` -> `0 errors, 0 warnings, 0 informations`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label WS-O-bri-post-property-pin tests/test_bridgman_signal_propagation.py tests/test_bridgman_pin_post_deletion.py` -> `5 passed`; log `logs/test-runs/WS-O-bri-post-property-pin-20260430-161545.log`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label WS-O-bri-final-full` -> `3500 passed, 2 skipped`; log `logs/test-runs/WS-O-bri-final-full-20260430-161616.log`.

## Property gates

- Implemented upstream generated tests for multiplication/division/power algebra laws.
- Implemented generated canonical signature order-stability and round-trip tests.
- Implemented generated transcendental accept/reject tests for dimensionless vs dimensioned arguments.
- `verify_equation` absence is covered by deterministic import/export/AST scans because generated import names do not strengthen deletion evidence.

## Files changed

Bridgman:
- `src/bridgman/dimensions.py`
- `src/bridgman/symbolic.py`
- `src/bridgman/__init__.py`
- `README.md`
- `CHANGELOG.md`
- `pyproject.toml`
- `uv.lock`
- new and updated tests under `tests/`

Propstore:
- `pyproject.toml`
- `uv.lock`
- `propstore/families/claims/passes/checks.py`
- `propstore/families/concepts/passes.py`
- `propstore/dimensions.py`
- `propstore/unit_dimensions.py`
- `tests/test_bridgman_signal_propagation.py`
- `tests/test_bridgman_pin_post_deletion.py`
- `tests/test_form_algebra.py`
- `docs/gaps.md`
- `reviews/2026-04-26-claude/workstreams/WS-O-bri-bridgman.md`
- `reviews/2026-04-26-claude/workstreams/INDEX.md`

## Remaining risks / successor work

- `propstore/families/concepts/passes.py` still has the brute-force `mul`/`div` fallback by design; WS-O-bri explicitly leaves its deletion to WS-D or a later owner-layer simplification.
- `propstore/unit_dimensions.py::resolve_unit_dimensions` remains in propstore by scope decision; WS-O-bri only moved canonicalization/signature ownership to Bridgman.
- LOW-2 about duplicate `DimensionalError` classes when SymPy is absent remains cosmetic and deferred by the workstream spec.
