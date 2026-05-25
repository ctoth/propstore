# Codex Cut 10 Slice D Fold Report

Workflow used: `workstreams/family-protocol-cutover-2026-05-24/prompts/codex-cut10-slice-d-fold.md`.

## Outcome

- Folded the final duplicate `_claim_value` from `propstore/world/assignment_selection_policy.py` into `ClaimValueResolver.claim_value`.
- Deleted the local `_claim_value` helper. No shim, alias, wrapper, or fallback path was kept.
- `ClaimValueResolver` is now the single owner for the checked `def _claim_value` surface.

## Semantics Check

- The deleted helper matched `ClaimValueResolver.claim_value`:
  - signature accepted `Claim`
  - returned `float | str | None`
  - ignored `bool`
  - converted `int | float` values to `float`
  - passed through `str`
  - returned `None` for absent or unsupported payload values
- Hard-stop H-A did not apply.

## Changes

- Added `ClaimValueResolver` import in `propstore/world/assignment_selection_policy.py`.
- Replaced all three local `_claim_value` call sites with `ClaimValueResolver.claim_value`.
- Removed `def _claim_value` from `assignment_selection_policy.py`.

## Gates

- `uv run pyright propstore/world/assignment_selection_policy.py propstore/world/value_resolver.py`
  - `0 errors, 0 warnings, 0 informations`
- `uv run pyright propstore`
  - `0 errors, 0 warnings, 0 informations`
- `uv run lint-imports`
  - `Contracts: 1 kept, 0 broken.`
- `rg -n -F -- "def _claim_value" propstore/world propstore/worldline tests`
  - zero hits
- `powershell -File scripts/run_logged_pytest.ps1 tests/`
  - `3527 passed, 4 skipped, 30 warnings in 313.66s`
  - Log: `logs\test-runs\pytest-20260525-041631.log`
