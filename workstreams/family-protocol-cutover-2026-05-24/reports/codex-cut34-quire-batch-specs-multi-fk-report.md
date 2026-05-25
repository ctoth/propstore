# Codex Cut 34 Report: Quire batch specs and multi-FK

## Workflow used

Executed `workstreams/family-protocol-cutover-2026-05-24/prompts/codex-cut34-quire-batch-specs-multi-fk.md`.

## Result

- Quire commit pushed: `e6eaed44aa5fac3abcf2a3a728d3aacab12b74cf` (`Add charter batch specs and multi foreign keys`).
- Propstore Quire pin updated from `5852fc653202c247072d4b52edcd2d78a14115a1` to `e6eaed44aa5fac3abcf2a3a728d3aacab12b74cf`.
- `DocumentBatchSpec` is re-exported from `quire`.
- `FamilyCharter.batch_specs` projects to `SchemaObject.batch_specs`.
- `CharterField.foreign_keys` projects to `SchemaField.foreign_keys`.
- Singular `CharterField.foreign_key` remains supported; setting both singular and plural now raises `ValueError`.

## Verification

- Quire targeted pre-implementation test run failed as expected because `DocumentBatchSpec` was not exported yet:
  `uv run pytest tests/test_charter_multi_fk_and_batch.py`
- Quire targeted post-implementation test run passed:
  `uv run pytest tests/test_charter_multi_fk_and_batch.py` -> `3 passed`
- Quire full suite passed:
  `uv run pytest` -> `350 passed`
- Quire typing passed:
  `uv run pyright quire` -> `0 errors`
- Propstore sync resolved the pushed Quire SHA:
  `uv sync`
- Propstore full suite passed the H-B gate:
  `powershell -File scripts/run_logged_pytest.ps1` -> `3526 passed, 4 skipped, 30 warnings`
  log: `logs\test-runs\pytest-20260525-154352.log`
- Propstore typing passed:
  `uv run pyright propstore` -> `0 errors`

## Hard-stop status

- H-A: Did not trigger; SchemaIR accepted and projected the new tuple fields.
- H-B: Did not trigger; Propstore test result was exactly `3526 passed, 4 skipped`.
- H-C: Did not trigger; Quire push succeeded.
