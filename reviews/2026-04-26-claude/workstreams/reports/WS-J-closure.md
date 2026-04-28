# WS-J Closure Report

**Workstream**: WS-J - Worldline determinism, hashing, OverlayWorld rename
**Closing commit**: `9eefe5ce`
**Closed on**: 2026-04-28

## Findings Closed

- J-H1: transient subsystem exception reprs no longer enter worldline content hashes; capture failures use typed `WorldlineCaptureError` categories.
- J-H2: canonical hash surfaces no longer use `json.dumps(..., default=str)`; unknown non-JSON-native payloads fail loudly, and typed ATMS capture reports are normalized at the worldline result boundary.
- J-H3: multi-extension argumentation projections are captured with explicit extensions and inference mode instead of being dropped.
- J-H4: journal replay now re-dispatches typed operators and detects algorithmic divergence instead of checking only hash-chain integrity.
- J-H5: public revision operator callers must pass explicit enumeration budgets; unbounded hidden defaults are gone.
- J-H6: iterated revision recomputes entrenchment from the current revised base instead of stale ranking state.
- J-R1: `HypotheticalWorld` was deleted/renamed to `OverlayWorld`; no compatibility alias remains, and the docstring states overlay semantics rather than Pearl `do()` semantics.
- J-M1: worldline content hashes are widened to 32 hex chars.
- J-M2: epistemic snapshots detach through canonical mappings instead of shallow live-state references.
- J-M3: revision target shape is validated at parse time.
- J-M4: override claim filtering uses the shared `OVERRIDE_CLAIM_PREFIX` constant.
- J-M5: blocked lifting exceptions are surfaced as worldline dependency/provenance data.
- Adjacent snapshot finding: revision capture rejects live-state `to_dict` fallback snapshots.

## Tests Written First

- `tests/test_worldline_hash_repr_typed_failure.py` failed while canonical JSON accepted non-native objects through `default=str`; it now proves deterministic native encoding and typed failure on non-native values.
- `tests/test_worldline_hash_excludes_transient_errors.py` failed while equivalent failures with different reprs produced different hashes; it now proves failure category hashing.
- `tests/test_worldline_argumentation_multi_extension.py` failed while multi-extension claim-graph results produced no argumentation state.
- `tests/test_journal_entry_contract.py` and `tests/test_replay_determinism_actually_replays.py` failed while journals lacked typed replay inputs and replay did not dispatch operators.
- `tests/test_contract_enumeration_bound.py` failed while public revision calls could omit enumeration budgets.
- `tests/test_iterated_revision_recomputes_entrenchment.py` failed while iterated revision reused stale ranking state.
- `tests/test_overlay_world_renamed.py` failed while the production surface was still named `HypotheticalWorld`.
- `tests/test_worldline_hash_width.py`, `tests/test_epistemic_snapshot_detaches_state.py`, `tests/test_worldline_target_shape_validation.py`, `tests/test_worldline_override_prefix_constant.py`, `tests/test_lifting_blocked_in_provenance.py`, and `tests/test_worldline_revision_snapshot_boundary.py` failed on the medium findings.
- `tests/test_atms_engine.py::test_atms_worldline_future_capture_is_opt_in` exposed the final strict-encoding gap: typed ATMS future reports were still present in the materialized hash payload.
- `tests/test_workstream_j_done.py` is the closure sentinel tying the WS-J spec, index, gaps entry, and successor workstreams together.

## Verification

- `powershell -File scripts/run_logged_pytest.ps1 --label WS-J-future-capture-serialization tests/test_atms_engine.py::test_atms_worldline_future_capture_is_opt_in`
  - `logs/test-runs/WS-J-future-capture-serialization-20260428-091157.log`
- `uv run pyright propstore`
  - passed with 0 errors, 0 warnings.
- `uv run lint-imports`
  - passed: 432 files, 2932 dependencies, 4 contracts kept, 0 broken.
- `powershell -File scripts/run_logged_pytest.ps1 --label WS-J-targeted tests/test_worldline_argumentation_multi_extension.py tests/test_worldline_hash_repr_typed_failure.py tests/test_journal_entry_contract.py tests/test_replay_determinism_actually_replays.py tests/test_revision_operators.py tests/test_iterated_revision_recomputes_entrenchment.py tests/test_worldline_hash_width.py tests/test_worldline_revision_snapshot_boundary.py tests/test_worldline.py tests/test_worldline_properties.py tests/test_workstream_j_done.py tests/test_atms_engine.py::test_atms_worldline_future_capture_is_opt_in`
  - `logs/test-runs/WS-J-targeted-20260428-091438.log`
  - result: 94 passed.
- `powershell -File scripts/run_logged_pytest.ps1 --label WS-J-full`
  - `logs/test-runs/WS-J-full-20260428-091456.log`
  - result: 3189 passed.

An earlier aggregate command at `logs/test-runs/WS-J-20260428-091306.log` collected 0 tests because it named stale test paths; it is not counted as evidence.

## Property-Based Coverage

- Added canonical JSON native/non-native property coverage in `tests/test_worldline_hash_repr_typed_failure.py`.
- Existing worldline property gates in `tests/test_worldline_properties.py` were rerun in the WS-J targeted suite and full suite.
- Successor property work is explicit instead of hidden in WS-J:
  - WS-J3 owns Spohn kappa/firmness properties.
  - WS-J4 owns Bonanno merge-parent replay/merge properties.
  - WS-J5 owns context-lifting fixpoint closure properties.
  - WS-J6 owns cheap stale-fingerprint equivalence properties against full materialization.

## Files Changed

- `propstore/canonical_json.py`
- `propstore/worldline/*`
- `propstore/world/*`
- `propstore/support_revision/*`
- `propstore/core/activation.py`
- WS-J tests under `tests/`
- `docs/gaps.md`
- `reviews/2026-04-26-claude/workstreams/INDEX.md`
- `reviews/2026-04-26-claude/workstreams/WS-J-worldline-causal.md`
- `reviews/2026-04-26-claude/workstreams/WS-J3-spohn-kappa.md`
- `reviews/2026-04-26-claude/workstreams/WS-J4-bonanno-merge.md`
- `reviews/2026-04-26-claude/workstreams/WS-J5-lifting-closure.md`
- `reviews/2026-04-26-claude/workstreams/WS-J6-worldline-stale-fingerprint.md`

## Successors

- WS-J2: Pearl `do()` / Halpern HP-modified actual cause.
- WS-J3: Spohn OCF kappa revision state.
- WS-J4: Bonanno ternary belief merge.
- WS-J5: context lifting fixpoint closure.
- WS-J6: cheap worldline stale fingerprints.

WS-J itself is closed: all listed findings are either implemented and tested here or moved into named successor workstreams with explicit scope.
