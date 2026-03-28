# Phase 4+5+6 Report: Mutations through git, pks log, Repository integration

## Summary

All CLI mutation commands now write through git when `repo.git` is available. Non-git fallback preserved for all commands. Added `pks log` command and `Repository.ensure_git()` migration helper.

## Changes per file

### `propstore/cli/concept.py`
- **4a concept add:** Uses `git.next_concept_id()` for ID allocation when git active; `CounterLock` fallback preserved via try/finally. Commits concept YAML via `git.commit_files()` + `sync_worktree()`.
- **4b concept alias:** After updating aliases, commits via git if available.
- **4c concept rename:** Replaced `subprocess.run(["git", "rm/add"])` with `git.commit_batch(adds, deletes)` for atomic rename. Removed `import subprocess` (no longer needed).
- **4d concept deprecate:** Commits deprecation update via git.
- **4e concept link:** Commits relationship addition via git.
- **4f concept add-value:** Commits value addition via git.

### `propstore/cli/context.py`
- **4g context add:** Commits new context YAML via git.

### `propstore/cli/__init__.py`
- **4h promote:** After moving stance files, collects adds/deletes and commits via `git.commit_batch()`.
- **Phase 5 pks log:** New `log` command shows commit history (sha, time, message).

### `propstore/cli/worldline_cmds.py`
- **4i worldline create:** After `wl.to_file(path)`, reads bytes back and commits via git.

### `propstore/cli/init.py`
- **4j pks init:** After seeding forms, commits them via git. Removed `.counters/` from output display.

### `propstore/cli/repository.py`
- **Phase 6 Repository.init():** Now calls `KnowledgeRepo.init(root)` before creating subdirs (order matters — sync_worktree in init would remove empty dirs created before it).
- **Phase 6 ensure_git():** Collects existing YAML file bytes BEFORE calling `KnowledgeRepo.init()` (since init's sync_worktree would remove non-git files), then commits them.

### `propstore/cli/git_backend.py`
- **sync_worktree fix:** Removed empty directory cleanup from `sync_worktree()`. Empty dirs are harmless; removing them broke workflows that expect dirs to exist after `Repository.init()`.

### `propstore/cli/helpers.py`
- **No changes.** CounterLock and counter functions retained for non-git fallback path.

### `tests/test_git_backend.py`
- Added `Path` import.
- **7 new tests:**
  1. `test_concept_add_creates_commit` — CliRunner `pks concept add`, verify commit + file in git tree
  2. `test_concept_rename_atomic` — Rename produces one commit, old file gone, new present
  3. `test_promote_commits` — Promote stance files creates git commit
  4. `test_init_creates_git_repo` — `pks init` creates git-backed repo with commits
  5. `test_log_output` — `pks log` shows history entries
  6. `test_ensure_git_migrates` — Existing YAML files committed on migration
  7. `test_repo_no_git` — Plain dir has `git == None`

## Test results

- **test_git_backend.py:** 42 passed (35 existing + 7 new)
- **Full suite:** 1627 passed, 0 failed

## Commit

`f4d2f65` — feat: Phases 4-6 — mutations through git, pks log, Repository.ensure_git()
