# WS-O-ast closure

Closing propstore commit: `294bb726`
Pushed ast-equiv commit: `b7423889daef74154193317099ae9992ecbcd958`

## Findings closed

- C-1: identity elimination is type-narrowed so non-numeric `x + 0` does not collapse to `x`.
- C-2: repeated multiplication to power is gated to pure operands/calls and does not reduce side-effecting call counts.
- C-3: while-to-for normalization refuses unsafe loops with break/continue, body reassignments, bound reassignments, or non-int initializers.
- X-1 / RD-4: `compare()` catches only tier refusal exceptions, records `tier_failures`, and lets internal errors propagate.
- D-14 / X-2 / X-3: the bytecode tier, bytecode helper, and bytecode public API are deleted.
- S-1 / S-2 / S-3 / RD-1: the SymPy bridge handles two-arg `math.log`, `log2`, `FloorDiv`, `Mod`, and real/finite symbols with positive-domain assertions.
- X-4: README and enum tier names agree on `{NONE, CANONICAL, SYMPY, PARTIAL_EVAL}`.
- X-6 / flipped-pairs: adversarial negative corpus and property tests cover canonicalization idempotence, equivalence transitivity, and false-positive risks.
- RD-3: `canonical_dump` is a SymPy-version-independent `SEMANTIC_EQUIVALENCE_VERSION:sha256` key derived from normalized AST structure only.
- RD-2: `extract_names` is deleted; `extract_all_names` and `extract_free_variables` replace it.
- PV-1 / PV-2: propstore no longer catches `AstToSympyError` outside `compare()`, and `RecursionError` handling is consistent across propstore callers.

## Tests written first

- ast-equiv red gates covered typed identity elimination, repeated-call count, unsafe loop normalization, narrow error propagation, log/floordiv/mod bridge behavior, real-domain assumptions, tier naming, property tests, cache-key independence/invalidation, bytecode deletion, adversarial negatives, and name-extraction split.
- propstore red gates covered value-resolver dead-except deletion, canonical-dump golden stability, `extract_free_variables` migration, and the workstream sentinel.
- Propstore targeted integration initially failed an old conflict-detector expectation because SymPy-tier equivalence now suppresses conflicts correctly.
- Propstore full-suite verification then exposed two stale expectations: undeclared algorithm parameter warnings and sidecar `canonical_ast` contents. Both were fixed and rerun before closure.

## Verification

- `cd ../ast-equiv && uv run pytest` -> `220 passed`.
- `cd ../ast-equiv && uv run pyright` -> `0 errors, 0 warnings, 0 informations`.
- `cd ../ast-equiv && uv run pytest tests/test_corpus.py` -> included in the full and targeted upstream runs; corpus remained green.
- `uv run pyright propstore` -> `0 errors, 0 warnings, 0 informations`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label WS-O-ast-targeted tests/test_ws_o_ast_integration.py tests/test_workstream_o_ast_done.py tests/test_conflict_detector.py tests/test_value_resolver_failure_reasons.py` -> `67 passed`; log `logs/test-runs/WS-O-ast-targeted-20260430-171639.log`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label WS-O-ast-failure-fixes tests/test_validate_claims.py::TestValidateAlgorithm::test_algorithm_unbound_name_warns tests/test_build_sidecar.py::TestAlgorithmBindings::test_algorithm_canonical_ast_includes_bindings tests/test_ws_o_ast_integration.py` -> `6 passed`; log `logs/test-runs/WS-O-ast-failure-fixes-20260430-172140.log`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label WS-O-ast-final-full` -> `3505 passed, 2 skipped`; log `logs/test-runs/WS-O-ast-final-full-20260430-172231.log`.

## Property gates

- Added upstream Hypothesis gates for canonicalization idempotence and compare transitivity over controlled generated programs.
- Added upstream cache-key properties for SymPy-version perturbation and deliberate semantic-version invalidation.
- Added upstream and propstore mechanical gates for deleted bytecode surfaces, deleted `extract_names`, README tier alignment, and public pin shape.

## Files changed

ast-equiv:
- `ast_equiv/canonicalizer.py`
- `ast_equiv/comparison.py`
- `ast_equiv/sympy_bridge.py`
- `ast_equiv/__init__.py`
- `README.md`
- `pyproject.toml`
- `uv.lock`
- new and updated tests under `tests/`

Propstore:
- `pyproject.toml`
- `uv.lock`
- `propstore/families/claims/passes/checks.py`
- `propstore/world/value_resolver.py`
- `propstore/app/claims.py`
- `propstore/conflict_detector/algorithms.py`
- `tests/__resources__/ws_o_ast_canonical_dump_golden.json`
- `tests/test_ws_o_ast_integration.py`
- `tests/test_workstream_o_ast_done.py`
- `tests/test_conflict_detector.py`
- `tests/test_build_sidecar.py`
- `docs/gaps.md`
- `reviews/2026-04-26-claude/workstreams/WS-O-ast-ast-equiv.md`
- `reviews/2026-04-26-claude/workstreams/INDEX.md`

## Remaining risks / successor work

- WS-P remains the consumer workstream for CEL, unit, and equation semantics. WS-O-ast only provides the corrected equivalence and cache-key substrate.
- `canonical_dump` now intentionally invalidates previous SymPy-srepr-derived cache keys. There is no compatibility fallback; consumers regenerate.
