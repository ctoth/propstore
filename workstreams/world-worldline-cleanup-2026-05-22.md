# World/Worldline Cleanup Refactor Fixed-Point Log - 2026-05-22

Target architecture:
- `propstore.world` and `propstore.worldline` runtime APIs receive typed domain
  values after the IO/app boundary.
- CLI/app request boundaries parse strings into typed enums before calling
  runtime owners.
- Package and runtime modules do not preserve old paths through coercers,
  normalizers, compatibility branches, fallback readers, broad re-exports, or
  duplicated field knowledge.

Forbidden surfaces:
- `coerce_*` helpers that accept `object` or raw strings past the boundary.
- `normalize_*` helpers that carry old spellings or aliases through runtime.
- fallback/legacy compatibility paths not required by an external data target.
- loose `dict`/payload constructors past exact IO/document boundaries.
- broad package initializer imports used by production internals instead of
  concrete owner modules.

Search gates:
- `rg -n -F -- "coerce_value_status" propstore tests`
- `rg -n -F -- "normalize_reasoning_backend" propstore tests`
- `rg -n -F -- "normalize_argumentation_semantics" propstore tests`
- `rg -n -F -- "fallback" propstore/world propstore/worldline`
- `rg -n -F -- "legacy" propstore/world propstore/worldline`
- `rg -n -F -- "from_payload" propstore/world propstore/worldline`

Runtime gates:
- `powershell -File scripts/run_logged_pytest.ps1 -Label world-value-status-cleanup ...`
- `uv run pyright propstore`

## Iteration 1 - `propstore/world/types.py::coerce_value_status`

Slice read:
- `propstore/world/types.py`
- `propstore/world/atms.py`
- `propstore/app/world_atms.py`
- current `coerce_value_status` callers from literal search.

Surfaces:
- `coerce_value_status`
  - Disposition: delete.
  - Owner after cleanup: `ValueStatus` enum at runtime; app/CLI boundaries call
    `ValueStatus(raw_string)` when parsing user input.
  - Action: remove the runtime coercer, require `ValueStatus` in world result
    dataclasses, and update runtime/app callers.
  - Evidence: current helper accepts `object`, stringifies it, and lets raw
    status strings cross runtime object construction.

Gate results:
- Pass: `rg -n -F -- "coerce_value_status" propstore tests` returned zero
  hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-value-status-cleanup tests/test_worldline.py tests/test_labelled_core.py
  tests/test_worldline_praf.py tests/test_praf_integration.py
  tests/test_resolution_helpers.py tests/test_worldline_result_boundaries.py`
  returned `105 passed`.
- Log: `logs/test-runs/world-value-status-cleanup-20260522-020128.log`.

Commit:
- `6bfd7eb8 Delete value status coercer`

Next slice:
- Continue world/worldline fixed-point search after this gate.

## Iteration 4 - `propstore/worldline/result_types.py::_coerce_variable_refs`

Slice read:
- `propstore/worldline/result_types.py`
- current `_coerce_variable_refs` callers from literal search.

Surfaces:
- `_coerce_variable_refs`
  - Disposition: delete.
  - Owner after cleanup: `WorldlineTargetValue.from_json_payload`, the exact IO
    boundary that owns parsing serialized variable references.
  - Action: inline the variable-reference payload parser into
    `WorldlineTargetValue.from_json_payload`; keep hard failures for wrong
    variable shapes.
  - Evidence: there is one caller, and a private coercer helper creates a
    reusable-looking surface for a single field parser.

Gate results:
- Pass: `rg -n -F -- "_coerce_variable_refs" propstore tests` returned
  zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  worldline-variable-ref-cleanup tests/test_worldline_result_boundaries.py
  tests/test_worldline.py::TestWorldlineDefinition::test_worldline_result_from_yaml`
  returned `7 passed`.
- Log: `logs/test-runs/worldline-variable-ref-cleanup-20260522-021151.log`.

Commit:
- Pending.

Next slice:
- Continue world/worldline fixed-point search after this gate.

## Iteration 3 - `WorldlineResult` value/step coercers

Slice read:
- `propstore/worldline/result_types.py`
- `propstore/worldline/definition.py`
- current `WorldlineResult(` construction sites from literal search.

Surfaces:
- `coerce_worldline_target_value`
- `coerce_worldline_step`
  - Disposition: delete.
  - Owner after cleanup: `WorldlineResult.from_document` and
    `WorldlineResult.from_dict` parse serialized mappings; direct
    `WorldlineResult` construction receives typed `WorldlineTargetValue` and
    `WorldlineStep` objects.
  - Action: remove the coercers and make runtime construction reject mapping
    values/steps.
  - Evidence: `WorldlineResult.__post_init__` currently accepts mapping payloads
    and converts them, duplicating the existing explicit IO constructors.

Gate results:
- Pass: `rg -n -F -- "coerce_worldline_target_value" propstore tests`
  returned zero hits.
- Pass: `rg -n -F -- "coerce_worldline_step" propstore tests` returned
  zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  worldline-result-coercer-cleanup tests/test_worldline.py
  tests/test_worldline_result_boundaries.py tests/test_capture_journal.py
  tests/test_worldline_revision.py` returned `75 passed`.
- Log: `logs/test-runs/worldline-result-coercer-cleanup-20260522-020908.log`.

Commit:
- `8b786db4 Delete worldline result coercers`

Next slice:
- Continue world/worldline fixed-point search after this gate.

## Iteration 2 - `propstore/worldline/result_types.py::coerce_worldline_capture_error`

Slice read:
- `propstore/worldline/result_types.py`
- `propstore/worldline/revision_types.py`
- current `coerce_worldline_capture_error` callers from literal search.

Surfaces:
- `coerce_worldline_capture_error`
  - Disposition: delete.
  - Owner after cleanup: `WorldlineCaptureError` enum in runtime objects;
    `from_json_payload` methods parse serialized strings at the worldline IO
    boundary.
  - Action: remove the coercer, require typed enum values in dataclass
    construction, and parse raw payload strings only inside JSON payload
    readers.
  - Evidence: the helper accepts strings through runtime `__post_init__`
    paths, preserving a coercion surface beyond the IO boundary.

Gate results:
- Pass: `rg -n -F -- "coerce_worldline_capture_error" propstore tests`
  returned zero hits.
- Pass: `uv run pyright propstore` returned `0 errors, 0 warnings`.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label
  worldline-capture-error-cleanup tests/test_worldline_error_visibility.py
  tests/test_worldline_hash_excludes_transient_errors.py
  tests/test_worldline_revision.py tests/test_worldline_revision_event_capture.py
  tests/test_worldline_result_boundaries.py tests/test_capture_journal.py`
  returned `27 passed`.
- Log: `logs/test-runs/worldline-capture-error-cleanup-20260522-020548.log`.

Commit:
- `777ea1c6 Delete worldline capture error coercer`

Next slice:
- Continue world/worldline fixed-point search after this gate.
