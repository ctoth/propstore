# Codex Cut 11 Claim Views Fold Report

Workflow used: `workstreams/family-protocol-cutover-2026-05-24/prompts/codex-cut11-claim-views-fold.md`.

## Outcome

Halted under hard-stop H-B: `propstore/app/claim_views.py::_claim_value` does not match `propstore.world.value_resolver.ClaimValueResolver.claim_value`'s signature or behavior.

No production code was edited.

## Evidence

- `propstore/app/claim_views.py::_claim_value` accepts `(claim, concept: ClaimViewConcept)` and returns `ClaimViewValue`.
- Its return value includes app presentation state and fields: `state`, `value`, `unit`, `value_si`, `canonical_unit`, and `sentence`.
- It distinguishes missing values from values that are not applicable for `mechanism`, `limitation`, `comparison`, `algorithm`, and `equation` claim types.
- It uses the focus concept form as the `canonical_unit` in the returned app view.
- `ClaimValueResolver.claim_value` accepts only `(claim: Claim)` and returns `float | str | None`.
- `ClaimValueResolver.claim_value` only normalizes the numeric payload scalar: bool is rejected, int/float becomes float, str is passed through, and absent/unsupported values return `None`.

Replacing the two app callers with `ClaimValueResolver.claim_value` would not preserve the `ClaimViewValue` contract consumed by `ClaimViewReport` and `_claim_value_display`.

## Gates

- `git rev-parse --short HEAD`
  - `a3f21d54`
- `rg -n -C 8 -F "def _claim_value" propstore/app/claim_views.py`
  - found the local helper at `propstore/app/claim_views.py:267`
- `rg -n -C 8 -F "claim_value" propstore/world/value_resolver.py propstore/app/claim_views.py`
  - confirmed app call sites at `propstore/app/claim_views.py:196` and `propstore/app/claim_views.py:433`
  - confirmed resolver API at `propstore/world/value_resolver.py:144`

Not run after H-B halt:

- `uv run lint-imports`
- `uv run pyright propstore`
- `rg -n -F -- "def _claim_value" propstore tests`
- `powershell -File scripts/run_logged_pytest.ps1 tests/`
