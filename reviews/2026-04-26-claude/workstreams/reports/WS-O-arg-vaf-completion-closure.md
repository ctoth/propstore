# WS-O-arg-vaf-completion closure

**Workstream**: WS-O-arg-vaf-completion
**Closed by propstore commit**: pending index/status closure
**Upstream argumentation commit**: `0d036dfef91e8c47ed47e5b030fe9d510bc53295`
**Propstore implementation evidence through**: `a9e6185dd787e589d127fa9ce1ae48851ee00e26`
**Date**: 2026-04-28

## Findings closed

- Bench-Capon 2003 Definition 6.3, p. 438: argument chains are represented as typed chains with same-value membership, in-chain attacker succession, and odd/even acceptance parity.
- Bench-Capon 2003 Definition 6.5, p. 439: lines of argument are represented as typed line objects over distinct-value chains with repeated-value termination.
- Bench-Capon 2003 Theorem 6.6, pp. 440-441: objective, subjective, and indefensible status classification is exposed through a named classifier that hard-fails outside the stated shape assumptions.
- Bench-Capon 2003 Corollary 6.7, pp. 440-441: two-value cycle preferred-extension behavior is exposed and checked against the existing preferred-extension engine.
- Bench-Capon 2003 pp. 444-447: factual arguments are modeled through an explicit `FACT_VALUE` helper and fact-first audience construction, with uncertainty checked by skeptical objectivity over preferred extensions.
- Propstore now observes the new surface only through the pushed `formal-argumentation` dependency pin and architecture sentinel tests.

## Tests written first

- Upstream `tests/test_vaf_completion.py` was written before implementation and initially failed at collection with `ModuleNotFoundError: No module named 'argumentation.vaf_completion'`.
- The first implementation run surfaced two incorrect test oracles. One over-constrained Definition 6.3 by treating external attackers as chain-local attackers; the paper restriction is on the chain relation. The other had a manual Corollary 6.7 expected extension that disagreed with both the existing preferred-extension engine and the generated property test. Both oracles were corrected before closure.
- Propstore architecture sentinel `tests/architecture/test_argumentation_pin_vaf_completion.py` proves one line-of-argument classification, one two-value cycle case, and one fact-uncertainty surface through the pinned dependency.
- The previous exact-SHA dependency test was removed. The retained dependency test checks the actual safety property: the dependency is a remote Git pin and not a local path.

## Property gates

- Upstream Hypothesis generated two-value cycles check Corollary 6.7 against ordinary audience-specific preferred extensions.
- Upstream Hypothesis generated fact-first audiences check that `FACT_VALUE` outranks ordinary values.
- The generated gates passed with `--hypothesis-show-statistics`: 32 passing two-value-cycle examples and 15 passing fact-first-audience examples.

## Verification

- Upstream focused gate: `cd ../argumentation && uv run pytest -vv tests/test_vaf_completion.py tests/test_workstream_o_arg_vaf_completion_done.py --hypothesis-show-statistics` -> `11 passed in 0.27s`.
- Upstream type gate: `cd ../argumentation && uv run pyright src/argumentation` -> `0 errors, 0 warnings`.
- Upstream full suite: `cd ../argumentation && uv run pytest -vv --timeout=180` -> `479 passed in 58.20s`.
- Propstore targeted sentinel: `powershell -File scripts/run_logged_pytest.ps1 -Label argumentation-vaf-completion-pin tests/architecture/test_argumentation_pin_vaf_completion.py` -> `4 passed in 2.42s`; log `logs\test-runs\argumentation-vaf-completion-pin-20260428-234000.log`.
- Propstore no-SHA pin gate: `powershell -File scripts/run_logged_pytest.ps1 -Label argumentation-vaf-completion-pin-nosha tests/architecture/test_argumentation_pin_gradual.py tests/architecture/test_argumentation_pin_vaf_completion.py` -> `7 passed in 3.27s`; log `logs\test-runs\argumentation-vaf-completion-pin-nosha-20260428-235000.log`.
- Propstore type gate: `uv run pyright propstore` -> `0 errors, 0 warnings`.
- Propstore full suite first surfaced the stale SHA-based test: `3217 passed, 1 failed in 444.49s`; log `logs\test-runs\argumentation-vaf-completion-full-20260428-234141.log`.
- Propstore full suite after removing SHA-based tests: `powershell -File scripts/run_logged_pytest.ps1 -Label argumentation-vaf-completion-full-nosha -n 0` -> `3217 passed in 459.70s`; log `logs\test-runs\argumentation-vaf-completion-full-nosha-20260428-235101.log`.

## Files changed

- Upstream argumentation:
  - `notes/bench-capon-2003-vaf-completion.md`
  - `src/argumentation/vaf_completion.py`
  - `src/argumentation/__init__.py`
  - `tests/test_vaf_completion.py`
  - `tests/test_workstream_o_arg_vaf_completion_done.py`
  - `docs/gaps.md`
- Propstore:
  - `pyproject.toml`
  - `uv.lock`
  - `tests/architecture/test_argumentation_pin_vaf_completion.py`
  - `tests/architecture/test_argumentation_pin_gradual.py`
  - `docs/gaps.md`
  - `reviews/2026-04-26-claude/cluster-P-argumentation-pkg.md`
  - `reviews/2026-04-26-claude/workstreams/reports/WS-O-arg-vaf-completion-closure.md`

## Remaining risks and successor work

- Dialogue protocol modeling from Bench-Capon and Dunne 2001 remains out of scope.
- General persuasion strategy synthesis remains out of scope.
- Oikarinen strong/local equivalence kernels remain a separate argumentation gap.
- I did not freshly reread Bench-Capon page images during the final closure slice after context compaction; this closure relies on the existing page-image-derived workstream and notes artifacts, plus tests that cite actual paper page numbers.
