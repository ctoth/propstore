# ASPIC completeness fixed-point execution log

## Package publication

- Gated package branch tip:
  `eb816eed559888563e44ba14c1aeed02e6182e76`.
- Published `origin/main` merge commit:
  `978b10edb8eaf106f64cd760cfeedce1c3cbb237`.
- Both commits have tree hash
  `f23ce11bee5f4a2fa08b0818c92c2ffcbd4ccbfb`.
- Post-amend package gates on the gated tree: 3165 tests passed, 4 skipped,
  1 xfailed; package Pyright, Ruff check, and Ruff format check passed.

## Propstore iteration 1 - typed query and analyzer propagation

Slice read:
- `propstore/aspic_bridge/query.py`
- `propstore/core/results.py`
- `propstore/core/analyzers.py`
- `tests/test_aspic_bridge.py`
- `tests/test_core_analyzers_phase6.py`
- `tests/test_core_semantic_kernel.py`

Surfaces:
- `query_claim()` treating `build_arguments_for()` as a bare argument set
  - Disposition: rewrite the caller to the typed owner interface.
  - Classification: valid capability with wrong representation.
  - Owner after cleanup: package `ArgumentBuildResult`.
  - Action: expose the direct construction result on `ClaimQueryResult` and use
    only its `.arguments` field for argument expansion.
- Analyzer metadata key `package_status`
  - Disposition: move the capability to the typed result owner and delete the
    metadata path in the same slice.
  - Classification: valid capability in the wrong representation.
  - Owner after cleanup: `AnalyzerResult.aspic_query_status` typed with package
    `ASPICQueryStatus`.
- Formal-argumentation dependency at the pre-B2 experiment commit
  - Disposition: repin to the published package owner revision before caller
    edits.
  - Owner after cleanup: `pyproject.toml` and generated `uv.lock` at
    `978b10edb8eaf106f64cd760cfeedce1c3cbb237`.

Gate results:
- `uv lock` resolved formal-argumentation exactly to published merge commit
  `978b10edb8eaf106f64cd760cfeedce1c3cbb237` in both lockfile entries.
- Final logged focused pytest: 38 passed in 6.06 seconds; log
  `logs/test-runs/pytest-20260722-171109.log`.
- `uv run pyright propstore`: zero errors, warnings, or informations.
- `uv run lint-imports`: 384 files and 2643 dependencies analyzed; all three
  contracts kept.
- Focused Ruff check passed and all six focused files passed Ruff format check.
- Propstore B2 searches report zero hits for the removed metadata key, the old
  bounded-query default, and any shared ASPIC adapter surface.

Commit:
- This iteration is committed as `feat(aspic): propagate computation status`.

Next slice:
- Normalize production worldline ASPIC result shapes and make materialization
  fail closed on typed capture failure.
