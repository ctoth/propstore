# Phase 1 GREEN Report: propstore/repo/ Package

## Commits

- `5a1ab43` — Phase 1 GREEN: propstore/repo/ package with multi-branch git primitives
- `baf8048` — Fix Dulwich DiskRefsContainer has no .get() — add _ref_get helper

## Test Results

### 1. `tests/test_repo_branch.py` — 15/15 passed
All 15 new branch tests pass: branch CRUD, commit isolation, linear history, parallel divergence, merge base (simple, no-divergence, deep, same-branch), backward compat, canonical import path.

### 2. `tests/test_git_backend.py` — 47/47 passed
All existing git backend tests pass with the new import path.

### 3. `tests/test_git_properties.py` — 11/11 passed
All Hypothesis property tests pass.

### 4. Full suite — 1733 passed, 2 failed (pre-existing)
The 2 failures are both in `test_relate_opinions.py` — a pre-existing sidecar column issue (`target_justification_id`), unrelated to this change. `test_aspic.py` excluded due to pre-existing hash recursion timeout.

## Files Created

- `propstore/repo/__init__.py` — re-exports KnowledgeRepo
- `propstore/repo/git_backend.py` — KnowledgeRepo moved from cli/, with:
  - `_commit()` parameterized by `branch: str = "master"`
  - `commit_files/commit_deletes/commit_batch` accept `branch` kwarg
  - `log()` accepts `branch` kwarg, walks from branch tip, includes `parents` in output
  - `branch_sha()` method added
  - `_ref_get()` helper for Dulwich refs (no `.get()` on DiskRefsContainer)
- `propstore/repo/branch.py` — BranchInfo dataclass, create_branch, delete_branch, list_branches, branch_head, merge_base (BFS ancestor walk)

## Files Modified

- `propstore/cli/git_backend.py` — emptied (moved to propstore/repo/)
- `propstore/cli/repository.py` — 3 import sites updated to `propstore.repo`
- `propstore/tree_reader.py` — TYPE_CHECKING import updated to `propstore.repo.git_backend`
- `tests/test_git_backend.py` — import updated to `propstore.repo`
- `tests/test_git_properties.py` — import updated to `propstore.repo`
- `tests/test_repo_branch.py` — `test_old_import_path_works` updated to test canonical path (no shim per coordinator)

## Deviations from Plan

1. **No backward-compatibility shim**: Coordinator directed updating all callers directly instead of creating a shim at `propstore/cli/git_backend.py`. Updated all 6 import sites in 4 files. The `test_old_import_path_works` test was changed to verify the new canonical import path instead.

2. **`_ref_get` helper**: Dulwich's `DiskRefsContainer` lacks a `.get()` method. Added `_ref_get(refs, ref_name)` that wraps `try/except KeyError` — used in both `git_backend.py` and `branch.py`.
