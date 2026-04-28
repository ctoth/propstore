# WS-O-arg Closure Report

**Workstream**: WS-O-arg - argumentation package HIGH bugs (kernel)
**Closing propstore commit**: `a2f41029`
**Upstream argumentation commit**: `f8ebd8575681f150e658c733cf0b25a265966503`
**Closed on**: 2026-04-28

## Findings Closed

- Bug 1 / T2.10: `ideal_extension` no longer has a union fallback; impossible multiple maxima now fail loudly. Added named ideal admissibility, defense-not-downward-closed, and mutual-defense regressions.
- Bug 2 / T2.11: ASPIC encoding emits ASP-valid literal ids and exposes `literal_by_id`.
- Bug 3: duplicate defeasible rule names are rejected at encode time.
- Bug 4: AF revision classification now uses extension content, not only family cardinality.
- Bug 5: `ExtensionRevisionState` accepts lazy rank callables and does not enumerate the full powerset at construction.
- Bug 6: `preference.strictly_weaker(non-empty, empty)` now matches the ASPIC set-lifting boundary.
- Bug 7: partial-AF acceptance separates `necessary_skeptical` and `possible_skeptical`, and rejects bare `skeptical` as ambiguous.
- Bug 8: Monte Carlo confidence accepts continuous confidence values via inverse-normal CDF.
- Propstore pin now points to the pushed remote `argumentation` commit `f8ebd8575681f150e658c733cf0b25a265966503`, not a local repository.

## Tests Written First

- Bug 1's "must fail today" premise was stale in the current upstream repo: the existing implementation already enumerated admissible subsets of the preferred-extension intersection, and `tests/test_dung.py::test_ideal_is_maximal_admissible_subset_of_every_preferred` already passed. No fake red test was written for that stale premise; the implementation was hardened by deleting the union fallback.
- Bugs 2 and 3: red tests in `argumentation/tests/test_aspic_encodings.py` failed on invalid ASP constants and missing duplicate-name rejection; fixed by `60e9f30`.
- Bugs 4 and 5: red tests in `argumentation/tests/test_af_revision.py` failed on decisive/expansive classification and eager lazy-ranking calls; fixed by `ac5ec44`.
- Bugs 6, 7, and 8: red tests in `argumentation/tests/test_preference.py`, `tests/test_semantics.py`, and `tests/test_probabilistic.py` failed on the empty-set preference boundary, ambiguous partial skeptical mode, and non-lookup confidence; fixed by `5a48004`.
- Upstream global sentinel `argumentation/tests/test_workstream_o_arg_done.py` is green at `f55aeac` and included in the pushed commit.
- Propstore architecture sentinels under `tests/architecture/test_argumentation_pin_*.py` and `test_workstream_o_arg_pin_done.py` are green at `a2f41029`.

## Verification

- `cd C:\Users\Q\code\argumentation && uv run pyright src/argumentation` -> 0 errors.
- `cd C:\Users\Q\code\argumentation && uv run pytest tests/ -q` -> `395 passed in 30.61s`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label ws-o-arg-architecture ...` -> `9 passed in 5.89s`; log `logs/test-runs/ws-o-arg-architecture-20260428-120132.log`.
- `uv run pyright propstore` -> 0 errors.
- `powershell -File scripts/run_logged_pytest.ps1 -Label ws-o-arg-full` -> `3198 passed in 87.83s`; log `logs/test-runs/ws-o-arg-full-20260428-120310.log`.

## Property-Based Gates

- Upstream: existing Hypothesis ideal-extension maximality property remains green; new named regressions cover mutual defense and defense non-downward-closure.
- Upstream: AF revision property suite remains green with lazy rank callables.
- Propstore: full suite includes the existing Hypothesis-heavy world, ATMS, form, import, and treedecomp gates against the new dependency pin.

## Files Changed

- Upstream `argumentation`: `src/argumentation/dung.py`, `aspic_encoding.py`, `af_revision.py`, `preference.py`, `semantics.py`, `probabilistic.py`; tests and `docs/gaps.md`.
- Propstore: `pyproject.toml`, `uv.lock`, nine architecture sentinel files under `tests/architecture/`, this workstream status, index row, gap entry, and this closure report.

## Remaining Risks / Successors

- `argumentation.af_revision._classify_extension_change` is still not surfaced through a public classifier API; the Propstore sentinel reaches it directly because the current upstream package exposes no public equivalent.
- WS-O-arg deliberately does not implement ABA, ADF, VAF/ranking, Dung-extension coverage, or gradual-semantics coverage. Those remain in successor workstreams `WS-O-arg-aba-adf`, `WS-O-arg-dung-extensions`, `WS-O-arg-vaf-ranking`, and `WS-O-arg-gradual`.
