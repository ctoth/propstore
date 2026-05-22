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
