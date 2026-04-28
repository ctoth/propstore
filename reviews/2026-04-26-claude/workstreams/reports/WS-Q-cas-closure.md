# WS-Q-cas closure report

Workstream id: WS-Q-cas
Closing implementation commit: `645df92f`

## Findings closed

- D-23 branch-head discipline: `Repository.head_bound_transaction(...)` captures the branch head once, exposes `expected_head`, maps quire head-mismatch failures to typed `StaleHeadError`, and buffers sidecar writes until kernel CAS success.
- D-23 finalize/promote/import/materialize races: source finalize, source promote, repository import, and materialize now use the captured head instead of relying on an internal re-read at commit time.
- D-23 no silent retry: stale-head rejection propagates for every scoped mutation path.
- D-23 no orphan sidecar state: queued sidecar writes are discarded on stale-head rejection; promotion-blocked mirror rows are staged off to the side and published only after the primary-branch CAS succeeds, so failed CAS attempts do not leak blocked rows or diagnostics.
- D-23 regression gate: scoped WS-Q mutation paths are AST-guarded against direct family/git commit calls.

## Tests written first

- `tests/test_head_bound_transaction_primitive.py` failed first with `ImportError` because `StaleHeadError` and `Repository.head_bound_transaction` did not exist. It now passes.
- `tests/test_branch_head_cas_matrix.py` failed first for finalize, promote, repository_import, and materialize because none raised `StaleHeadError` under a simulated stale expected head. It now passes for all four paths.
- `tests/test_workstream_q_cas_done.py` failed first because this WS file, `INDEX.md`, and `docs/gaps.md` still showed WS-Q-cas open. It now passes after closure tracking was updated.
- `tests/test_cas_rejection_no_orphan_rows.py`, `tests/test_cas_no_silent_retry.py`, `tests/test_branch_head_cas_properties.py`, and `tests/test_no_unbounded_quire_commit.py` were added as hardening gates after the path migrations were in place.
- The first full-suite run exposed one missed atomicity interaction: promotion-blocked rows were being buffered until after the git CAS, but existing rollback semantics also require a sidecar write failure to prevent the primary branch from advancing. Commit `645df92f` fixes this by preparing blocked rows in a temporary sidecar, then publishing them only after the primary-branch CAS succeeds.

## Logged test commands

- Red primitive: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-Q-cas-primitive-red tests/test_head_bound_transaction_primitive.py`; log `logs/test-runs/WS-Q-cas-primitive-red-20260428-014414.log`.
- Primitive green: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-Q-cas-primitive-green tests/test_head_bound_transaction_primitive.py`; log `logs/test-runs/WS-Q-cas-primitive-green-20260428-014506.log`.
- Matrix red: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-Q-cas-matrix-red tests/test_branch_head_cas_matrix.py`; log `logs/test-runs/WS-Q-cas-matrix-red-20260428-014638.log`.
- Path slices: finalize `logs/test-runs/WS-Q-cas-finalize-20260428-014839.log`; promote `logs/test-runs/WS-Q-cas-promote-20260428-014921.log`; repository import `logs/test-runs/WS-Q-cas-repository-import-20260428-014950.log`; materialize `logs/test-runs/WS-Q-cas-materialize-20260428-015036.log`.
- Matrix green: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-Q-cas-matrix-green tests/test_branch_head_cas_matrix.py`; log `logs/test-runs/WS-Q-cas-matrix-green-20260428-015054.log`.
- No orphan rows: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-Q-cas-no-orphans tests/test_cas_rejection_no_orphan_rows.py`; log `logs/test-runs/WS-Q-cas-no-orphans-20260428-015155.log`.
- No retry: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-Q-cas-no-retry tests/test_cas_no_silent_retry.py`; log `logs/test-runs/WS-Q-cas-no-retry-20260428-015242.log`.
- Property gates: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-Q-cas-properties tests/test_branch_head_cas_properties.py`; log `logs/test-runs/WS-Q-cas-properties-20260428-015356.log`.
- AST gate: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-Q-cas-ast-gate tests/test_no_unbounded_quire_commit.py`; log `logs/test-runs/WS-Q-cas-ast-gate-20260428-015448.log`.
- Targeted WS-Q bundle: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-Q-cas-targeted tests/test_head_bound_transaction_primitive.py tests/test_branch_head_cas_matrix.py tests/test_cas_rejection_no_orphan_rows.py tests/test_cas_no_silent_retry.py tests/test_branch_head_cas_properties.py tests/test_no_unbounded_quire_commit.py`; log `logs/test-runs/WS-Q-cas-targeted-20260428-015505.log`.
- Closure sentinel red: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-Q-cas-sentinel-red tests/test_workstream_q_cas_done.py`; log `logs/test-runs/WS-Q-cas-sentinel-red-20260428-015709.log`.
- Closure sentinel green: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-Q-cas-sentinel-green tests/test_workstream_q_cas_done.py`; log `logs/test-runs/WS-Q-cas-sentinel-green-20260428-015920.log`.
- Closure sentinel final after evidence update: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-Q-cas-sentinel-final tests/test_workstream_q_cas_done.py`; log `logs/test-runs/WS-Q-cas-sentinel-final-20260428-020756.log`.
- First full suite: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-Q-cas-full`; log `logs/test-runs/WS-Q-cas-full-20260428-020014.log`; failed only `tests/test_source_promotion_alignment.py::test_promote_source_branch_does_not_advance_master_when_sidecar_write_fails`, which commit `645df92f` fixed.
- Focused promotion atomicity rerun after `645df92f`: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-Q-cas-promote-atomicity tests/test_source_promotion_alignment.py::test_promote_source_branch_does_not_advance_master_when_sidecar_write_fails tests/test_cas_rejection_no_orphan_rows.py tests/test_branch_head_cas_matrix.py::test_concurrent_writer_loses_cleanly[promote]`; log `logs/test-runs/WS-Q-cas-promote-atomicity-20260428-020306.log`.
- Final acceptance bundle: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-Q-cas-acceptance-final tests/test_head_bound_transaction_primitive.py tests/test_branch_head_cas_matrix.py tests/test_cas_rejection_no_orphan_rows.py tests/test_cas_no_silent_retry.py tests/test_branch_head_cas_properties.py tests/test_no_unbounded_quire_commit.py tests/test_workstream_q_cas_done.py tests/test_source_promotion_alignment.py::test_promote_source_branch_does_not_advance_master_when_sidecar_write_fails`; log `logs/test-runs/WS-Q-cas-acceptance-final-20260428-020347.log`.
- Final full suite: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-Q-cas-full-final`; log `logs/test-runs/WS-Q-cas-full-final-20260428-020409.log`; result `3048 passed`.
- `uv run pyright propstore`: passed with 0 errors after `645df92f`.
- `uv run lint-imports`: passed with 4 contracts kept after `645df92f`.

## Property-based tests

- Added `tests/test_branch_head_cas_properties.py` for the WS-Q property matrix:
  generated stale expected heads fail before mutation; generated concurrent operations have one winning order and one typed stale-head loser.

## Files changed

- `propstore/repository.py`
- `propstore/source/finalize.py`
- `propstore/source/promote.py`
- `propstore/storage/repository_import.py`
- `propstore/storage/snapshot.py`
- `tests/test_head_bound_transaction_primitive.py`
- `tests/test_branch_head_cas_matrix.py`
- `tests/test_cas_rejection_no_orphan_rows.py`
- `tests/test_cas_no_silent_retry.py`
- `tests/test_branch_head_cas_properties.py`
- `tests/test_no_unbounded_quire_commit.py`
- `tests/test_workstream_q_cas_done.py`
- `docs/gaps.md`
- `reviews/2026-04-26-claude/workstreams/WS-Q-cas-branch-head-discipline.md`
- `reviews/2026-04-26-claude/workstreams/INDEX.md`
- `reviews/2026-04-26-claude/workstreams/reports/WS-Q-cas-closure.md`

## Remaining risks / successor workstreams

- Quire still exposes stale-head rejection as a generic head-mismatch `ValueError`; WS-Q-cas maps it at the propstore boundary. A future quire release can export a typed stale-head exception, but this WS did not modify quire.
- The AST gate is scoped to the mutation paths named in WS-Q-cas. Broader repository mutation surfaces remain owned by their respective workstreams.
- WS-C and WS-E can now consume `head_bound_transaction`; they are still open.
