# Quire Head-Bound Transactions Workstream

## Goal

Move generic optimistic branch-head transaction mechanics from Propstore into
`../quire`, then delete Propstore's local transaction wrapper code.

The target architecture is:

- Quire owns head capture, expected-head validation, stale-head typed errors,
  family transaction binding, and post-commit callback hooks.
- Propstore owns when a command needs a head-bound transaction, sidecar write
  semantics, and Propstore-specific error presentation.
- `propstore/repository.py` shrinks to a thin repository locator/config object
  plus a one-line adapter, or no adapter if callers can use Quire directly.

This is deletion-first in Propstore. Once the Quire transaction exists, delete
Propstore's `HeadBoundTransaction` implementation before repairing callers.

This is a two-repository workstream. Quire changes land first. Propstore must
never pin Quire to a local path; pin only to a pushed tag or immutable pushed
commit SHA.

## Non-Goals

Do not move these into Quire:

- Propstore repository discovery
- `propstore.yaml` parsing
- `refs/propstore/bootstrap` format checks
- sidecar path choices or sidecar data writes
- CLI error rendering
- source promotion/finalize semantics

Do not leave a Propstore wrapper class that duplicates Quire behavior under a
new name. If an adapter remains, it should only supply Propstore-owned policy or
be deleted.

## Workstream Order

The phases below are topologically ordered.

1. Quire head-bound transaction tests
2. Quire generic transaction implementation
3. Propstore dependency pin
4. Propstore transaction deletion and caller repair
5. Propstore sidecar hook adaptation
6. Final gates

## Phase 1 - Quire Head-Bound Transaction Tests

Repository: `../quire`

Write failing tests for generic head-bound transactions.

Required cases:

- transaction captures the current branch head on enter
- `commit_batch` passes the captured head as `expected_head`
- stale branch head raises Quire's typed head-mismatch error
- `families_transact` uses the same captured head
- a transaction with no commit does not run post-commit hooks
- post-commit hooks run only after a successful commit
- exception paths clear pending post-commit hooks
- nested family transactions cannot write a second branch accidentally

Target tests:

- `../quire/tests/test_git_store.py`
- `../quire/tests/test_family_store.py`
- `../quire/tests/test_families.py`

Required gate:

- `uv run pytest tests/test_git_store.py tests/test_family_store.py tests/test_families.py`

## Phase 2 - Quire Generic Transaction Implementation

Repository: `../quire`

Add a generic transaction primitive near `GitStore` / `DocumentFamilyStore`.

Candidate API:

```python
with store.head_bound_transaction("master") as txn:
    with txn.families_transact(families, message="update") as family_txn:
        family_txn.books.save(BookRef("a"), doc)
    txn.after_commit(lambda commit_sha: ...)
```

Acceptable alternative:

- `HeadBoundTransaction` in `quire.family_store`
- `GitStore.head_bound_transaction(...)` with optional family registry binding

Requirements:

- typed stale-head errors preserve branch, expected head, and actual head
- no string parsing of error messages
- expected-head check occurs before writing a new commit
- post-commit hooks receive the commit SHA or can close over it explicitly
- no Propstore terms such as `sidecar`, `knowledge`, `source`, or `pks`
- existing `BoundFamilyTransaction` FK validation still runs

Required gates:

- `uv run pytest tests/test_git_store.py tests/test_family_store.py tests/test_families.py`
- `uv run pytest`

## Phase 3 - Propstore Dependency Pin

Repository: `propstore`

Only start after Quire changes are pushed to a shared remote.

Before editing dependency metadata:

- verify the Quire reference is a pushed tag or immutable pushed commit SHA
- reject local paths, editable paths, local git paths, Windows drive paths, WSL
  paths, and `file://` URLs

Update:

- `pyproject.toml`
- `uv.lock`

Required gate:

- `uv run pyright propstore`

## Phase 4 - Propstore Transaction Deletion and Caller Repair

Repository: `propstore`

Delete first:

- `propstore/repository.py::HeadBoundTransaction`
- `propstore/repository.py::StaleHeadError` if callers can use Quire's typed
  error directly
- `Repository.head_bound_transaction` if it becomes a one-line alias with no
  Propstore policy

Then repair callers with Quire's transaction primitive.

Known callers:

- `propstore/importing/repository_import.py`
- `propstore/storage/snapshot.py`
- `propstore/source/promote.py`
- proposal promotion flows that use branch-head CAS
- tests under `tests/test_branch_head_cas_matrix.py`
- tests under `tests/test_repository_concurrency_boundary.py`

Rules:

- do not wrap Quire errors just to preserve old Propstore exception names
- if CLI needs a presentation-specific message, map Quire's typed error at the
  CLI boundary
- if an adapter remains on `Repository`, it must add Propstore policy and be
  smaller than the deleted implementation

Search gates:

- `rg -F "class HeadBoundTransaction" propstore tests` returns no refs
- `rg -F "StaleHeadError" propstore tests` returns no production refs unless it
  is a presentation-only alias with no state parsing
- `rg -F "head_bound_transaction" propstore tests` shows only direct use of the
  Quire primitive or a justified Propstore policy adapter

Required gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label head-bound-transactions tests/test_branch_head_cas_matrix.py tests/test_repository_concurrency_boundary.py tests/test_cas_no_silent_retry.py tests/test_cas_rejection_no_orphan_rows.py`
- `uv run pyright propstore`

## Phase 5 - Propstore Sidecar Hook Adaptation

Repository: `propstore`

Delete local sidecar deferral machinery from the old transaction class before
adding replacement usage.

Target shape:

- commands register sidecar writes through Quire's generic post-commit hook
  surface
- sidecar write functions stay in Propstore owner layers
- hooks run only after successful Git commit
- failed CAS or failed family validation does not write sidecar artifacts

Known areas:

- sidecar update paths in source promotion/finalize
- concept/claim embedding write deferrals if they rely on commit success
- tests that simulate stale heads with sidecar updates

Search gates:

- `rg -F "_sidecar_writes" propstore tests` returns no refs
- `rg -F "sidecar_write" propstore tests` returns no refs unless it is the new
  Quire hook call with Propstore-owned callback content

Required gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label head-bound-sidecar tests/test_cas_rejection_no_orphan_rows.py tests/test_source_promotion_alignment.py tests/test_repository_concurrency_boundary.py`
- `uv run pyright propstore`

## Phase 6 - Final Gates

Repository: both

Final Quire gates:

- `uv run pytest`

Final Propstore gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label head-bound-full tests/test_branch_head_cas_matrix.py tests/test_repository_concurrency_boundary.py tests/test_cas_no_silent_retry.py tests/test_cas_rejection_no_orphan_rows.py tests/test_artifact_store.py`
- `uv run pyright propstore`

Completion evidence:

- Propstore no longer owns generic branch-head transaction state
- Propstore no longer parses stale-head messages
- sidecar writes are deferred through a generic Quire post-commit hook
- `propstore/repository.py` is smaller, with no duplicate transaction class
- no local Quire dependency pin is committed
