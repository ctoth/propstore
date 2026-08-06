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

## Propstore iteration 2 - production worldline consumption

Surfaces:
- `_capture_aspic()` discarding non-grounded successful result shapes
  - Disposition: rewrite the caller to consume both existing owner result
    shapes directly.
  - Classification: valid capability with a wrong caller disposition.
  - Action: normalize grounded, multiple-extension, and zero-extension results,
    map every extension to claim ids, and populate the existing typed worldline
    fields.
- Argumentation capture failure without its selected backend
  - Disposition: populate the already-owned backend field alongside the
    existing typed status/error evidence.
  - Classification: valid capability with incomplete typed evidence.
- Grounding-only materialization failure check
  - Disposition: replace the incomplete consumer with a fail-closed condition
    over the existing status/error fields.
  - Classification: valid failure marker with an incomplete consumer.
- Resolution semantics exception
  - Disposition: keep the existing propagating production path and add only the
    missing regression.
  - Classification: already-owned capability that uses its true owner directly.

Gate results:
- Final logged focused pytest: 55 passed in 8.32 seconds; log
  `logs/test-runs/pytest-20260722-171802.log`.
- `uv run pyright propstore`: zero errors, warnings, or informations after the
  zero-extension claim set was explicitly typed as `frozenset[ClaimId]`.
- `uv run lint-imports`: 384 files and 2643 dependencies analyzed; all three
  contracts kept.
- Package-wide Ruff check passed and all 640 files passed Ruff format check.
- Every B2 package and Propstore search gate returned zero hits.

Commit:
- This iteration is committed as
  `fix(worldline): refuse incomplete argumentation results`.

Next slice:
- Run the combined B2 final gate, repeat all static gates, then run the full
  logged Propstore suite and close the fixed-point record on the final commit.

## Final fixed point

- Combined B2 logged gate: 93 passed in 9.88 seconds; log
  `logs/test-runs/pytest-20260722-172029.log`.
- Final `uv run pyright propstore`: zero errors, warnings, or informations.
- Final `uv run lint-imports`: 384 files and 2643 dependencies analyzed; all
  three contracts kept.
- Final package-wide Ruff check passed and all 640 files passed Ruff format
  check.
- Full logged Propstore suite: 1830 passed and 1 skipped in 87.87 seconds; log
  `logs/test-runs/pytest-20260722-172134.log`.
- The formal-argumentation package remains published at merge commit
  `978b10edb8eaf106f64cd760cfeedce1c3cbb237`, and Propstore's dependency and
  lockfile remain pinned to that exact revision.
- Every B2 execution item and final gate is complete; the active plan's B2
  checklist is closed.

## Issue 10 follow-up - remove the false PrAF dependency edge

Target architecture:
- Structured grounding completeness remains owned by the Gunray/ASPIC build,
  resolution, worldline, and fragility paths.
- PrAF analysis remains an abstract claim/stance graph computation over
  `SharedAnalyzerInput`; generic enumeration routing belongs to the
  `argumentation` package.

Forbidden surface:
- An unconditional placeholder test that makes PrAF analysis appear to depend
  on `GroundedRulesBundle`, `GroundingStatus`, or Propstore-owned argument
  enumeration limits.

Slice read:
- `tests/test_praf_argument_enumeration_budget.py`
- `tests/test_app_worldlines.py`
- `tests/test_fragility.py`
- `propstore/core/analyzers.py`
- `propstore/worldline/argumentation.py`

Surfaces:
- The skipped PrAF enumeration-budget test
  - Classification: dead/test/scaffold surface plus a wrong caller assumption.
  - Disposition: delete the caller path.
  - Owner after cleanup: no Propstore owner; generic PrAF computation routing
    remains dependency-owned.
  - Evidence: the test contained only an unconditional skip and an
    `AssertionError`; the real structured-grounding failure contract is already
    exercised through the ASPIC app-worldline and fragility paths.

Search gates:
- No `test_praf_argument_enumeration_budget.py` file remains.
- No PrAF production path consumes `GroundedRulesBundle`, `GroundingStatus`,
  or `max_arguments`.

Runtime gates:
- Logged focused app-worldline and fragility regressions.
- `uv run pyright propstore`.
- Package Ruff check and format check.
- Full logged test suite.

Gate results:
- Red acceptance gate: one unconditional skip in
  `logs/test-runs/issue-10-red-20260805-225912.log`.
- Focused owner-path regressions: 2 passed in 9.99 seconds in
  `logs/test-runs/issue-10-green-focused-20260805-230053.log`.
- PrAF owner search: zero hits for `GroundedRulesBundle`, `GroundingStatus`,
  and `max_arguments`.
- `uv run pyright propstore`: zero errors, warnings, or informations.
- `uv run ruff check .`: all checks passed.
- `uv run ruff format --check .`: all 639 files already formatted.
- `uv run lint-imports`: all three contracts kept.
- Full logged suite: 1817 passed and 3 skips in 60.26 seconds
  in `logs/test-runs/issue-10-full-20260805-230141.log`.

Commit:
- Planned as `test: remove false PrAF grounding placeholder`.

Next slice:
- None; issue 10 reaches fixed point when the search and runtime gates pass.
