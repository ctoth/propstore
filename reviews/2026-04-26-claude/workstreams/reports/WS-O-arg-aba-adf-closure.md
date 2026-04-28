# WS-O-arg-aba-adf Closure Report

**Workstream**: WS-O-arg-aba-adf - flat ABA / ABA+ and ADF kernels  
**Closing propstore commit**: `58bbae38`  
**Upstream argumentation commit**: `9887559a75c595bfcb0042adcafbf8ddedcb6ac6`  
**Closed on**: 2026-04-28

## Findings Closed

- P-A.1: ADF coverage now exists upstream with typed acceptance-condition ASTs, JSON/ICCMA formula I/O, three-valued operator semantics, Brewka 2013 reduct-based stable semantics, structural link classification, and Dung bridge coverage.
- P-A.2: flat ABA coverage now exists upstream with assumptions, contraries, derivability, attack/defence, classical extensions, flat ABA+ preference-aware attack, ICCMA I/O, and argument-level Dung bridge coverage for joint-support attacks.
- P-A.3: the foundational paper track is represented by executable tests for Bondarenko 1997, Toni 2014, Čyras 2016, Brewka 2010, Brewka 2013, and Polberg-facing ADF behavior.
- P-A.4: the open question about where ABA/ADF belongs is resolved by landing the kernels in `argumentation` and pinning Propstore to the pushed upstream commit.

## Tests Written First

- Upstream red ADF tests covered the acceptance-condition AST, Brewka 2010/2013 operator examples, Dung bridge, ICCMA ADF I/O, and the workstream sentinel before the first ADF implementation.
- Upstream red ABA tests covered Bondarenko/Toni/Čyras examples, flatness rejection, ABA+ attack reversal, ABA I/O, and Dung correspondence before the first ABA implementation.
- During closure review, two additional red tests were added because the first implementation was too weak:
  - `tests/test_adf_brewka_2013_operator.py::test_stable_models_use_brewka_2013_reduct_not_just_two_valued_models` failed while `stable_models()` was only `model_models()`.
  - `tests/test_aba_dung_correspondence.py::test_flat_aba_to_dung_preserves_joint_support_attacks` failed while `aba_to_dung()` represented only singleton assumption attacks.
- Propstore red behavior sentinel `tests/architecture/test_argumentation_pin_aba_adf.py` failed against the old pin, then passed after the pin advanced to `9887559a75c595bfcb0042adcafbf8ddedcb6ac6`.

## Verification

- `cd C:\Users\Q\code\argumentation && uv run pytest tests/test_adf_acceptance_condition_ast.py tests/test_adf_brewka_2010_examples.py tests/test_adf_brewka_2013_operator.py tests/test_adf_dung_bridge.py tests/test_adf_iccma_io.py tests/test_aba_bondarenko_examples.py tests/test_aba_toni_2014_tutorial.py tests/test_aba_plus_cyras_2016.py tests/test_aba_dung_correspondence.py tests/test_aba_iccma_io.py tests/test_workstream_o_arg_aba_adf_done.py -q` -> `26 passed in 0.51s`.
- `cd C:\Users\Q\code\argumentation && uv run pyright src/argumentation` -> 0 errors.
- `cd C:\Users\Q\code\argumentation && uv run pytest tests/ -q` -> `421 passed in 38.45s`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label ws-o-arg-aba-adf-behavior-red tests/architecture/test_argumentation_pin_aba_adf.py` -> expected red against old pin; log `logs/test-runs/ws-o-arg-aba-adf-behavior-red-20260428-133607.log`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label ws-o-arg-aba-adf-behavior-green tests/architecture/test_argumentation_pin_aba_adf.py` -> `3 passed in 5.19s`; log `logs/test-runs/ws-o-arg-aba-adf-behavior-green-20260428-133756.log`.
- `uv run pyright propstore` -> 0 errors.
- `powershell -File scripts/run_logged_pytest.ps1 -Label ws-o-arg-aba-adf-full-final -n 0` -> `3200 passed in 578.67s`; log `logs/test-runs/ws-o-arg-aba-adf-full-final-20260428-133824.log`.

## Property-Based Gates

- Upstream retained and expanded the generated flat-ABA/Dung correspondence coverage with a regression for collective support attacks.
- Upstream ADF tests cover generated acceptance-condition serialization/evaluation consistency and the reduct-based stable-model counterexample.
- Propstore full suite includes the existing Hypothesis-heavy world, import, ATMS, form, revision, and toy-DP gates against the new dependency pin.

## Files Changed

- Upstream `argumentation`: `src/argumentation/adf.py`, `src/argumentation/aba.py`, ADF/ABA tests, package docs, version/lock metadata, and upstream gap/sentinel docs.
- Propstore: `pyproject.toml`, `uv.lock`, `tests/architecture/test_argumentation_pin_aba_adf.py`, `docs/gaps.md`, `reviews/2026-04-26-claude/workstreams/WS-O-arg-aba-adf.md`, `reviews/2026-04-26-claude/workstreams/INDEX.md`, `reviews/2026-04-26-claude/cluster-P-argumentation-pkg.md`, and this report.

## Remaining Risks / Successors

- Non-flat ABA remains out of scope and is intentionally rejected with `NotFlatABAError`; it needs a separate workstream.
- ADF/ABA solver-protocol wrappers, SAT/ASP encoders, dispute derivations, and dialogue games remain successor work, not hidden partial paths in this WS.
- The first two Propstore xdist full-suite attempts lost worker processes near 99% on different tests. The crashed tests passed in isolation, and the final full-suite evidence uses `-n 0` through the required logged wrapper to remove that infrastructure failure mode.
- Čyras 2016 paper artifacts now include page images and implementation-focused notes. Its `citations.md` does not transcribe the full bibliography; that is paper-collection polish, not a remaining ABA/ADF kernel blocker.
