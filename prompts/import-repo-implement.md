Implement `pks import-repo` for propstore.

Do not restate the task. Work directly in the repo. Use TDD. Commit only your work files as you go. Reread the active plan after every passing targeted run.

Context:

- The design is specified in [proposals/git-native-semantics-and-repo-import.md](/C:/Users/Q/code/propstore/proposals/git-native-semantics-and-repo-import.md).
- The key architectural rule is: for git-backed repositories, propstore semantics should follow tracked git state by default, not ambient working-tree state.
- This command is adjacent to merge work, not a substitute for finishing merge Phase 6.
- Do not broaden into `merge-repo`.

Required outcome:

Add a new CLI command:

```bash
uv run pks -C DEST_REPO import-repo SOURCE_REPO
```

The command should:

1. inspect the source repo at committed `HEAD` by default
2. create or update an import branch in the destination repo, defaulting to `import/<repo-name>`
3. import the source knowledge tree into the destination repo on that branch
4. commit the import atomically
5. print structured YAML with:
   - `surface: repo_import_commit`
   - `source_repo`
   - `source_commit`
   - `target_branch`
   - `commit_sha`
   - `touched_paths`
   - `worktree_synced`

Scope for this slice:

- implement only committed-snapshot import
- no `--working-tree` mode
- no `merge-repo` wrapper
- no global migration of all semantic reads yet

Preferred implementation shape:

1. pure planning function
2. commit function
3. thin CLI wrapper

Recommended APIs:

```python
plan_repo_import(
    destination_repo: Repository,
    source_repo_path: Path,
    *,
    target_branch: str | None = None,
) -> RepoImportPlan

commit_repo_import(
    repo: Repository,
    plan: RepoImportPlan,
    *,
    message: str | None = None,
    sync_worktree: str = "auto",
) -> RepoImportResult
```

Recommended files:

- new module under `propstore/repo/` for repo import logic
- `propstore/cli/__init__.py` or whichever CLI module is the right home for a top-level command
- `propstore/cli/repository.py` only if needed for destination/source repo handling
- `docs/cli-reference.md`
- maybe `README.md` if the new surface is prominent enough

Likely tests:

- `tests/test_import_repo.py`
- maybe one CLI-focused file if you want to separate unit/API and CLI surface

Behavioral requirements:

1. Source capture must come from committed git state, not raw filesystem copy.
2. Destination writes must go through git commit machinery, not ad hoc file writes.
3. Default target branch should be derived from the source repo name, e.g. `import/repo-b`.
4. Sync policy:
   - if target branch is `master`, auto-sync the worktree
   - otherwise default to no sync
5. The command must not mutate destination `master` unless explicitly targeted.
6. The result must be structured YAML, not a bare SHA.

Source tree scope:

- Start with the propstore-managed semantic tree only.
- Be conservative and explicit.
- At minimum include the canonical knowledge directories the repo already treats as meaningful:
  - `claims/`
  - `concepts/`
  - `contexts/`
  - `forms/`
  - `stances/`
  - `worldlines/`
- Exclude:
  - `.git/`
  - `sidecar/`
  - generated SQLite/state artifacts
  - other obvious non-semantic junk

Implementation guidance:

- The repo already says the git object store is the single source of truth in `propstore/repo/git_backend.py`.
- The repo already has git-backed read APIs and branch commit APIs.
- Do not invent a writable `KnowledgePath`.
- Build a `dict[path, bytes]` and commit it atomically.
- If you need a source snapshot, prefer existing repo/object-store reads first. `git archive` is acceptable if that genuinely simplifies the implementation and keeps the snapshot committed-only.

TDD order:

1. RED tests for planning:
   - source repo must be git-backed
   - source `HEAD` snapshot is used
   - default branch naming
   - touched paths exclude `sidecar/` and `.git/`
2. GREEN minimal planning code
3. RED tests for commit behavior:
   - import commit lands on target branch
   - `master` unchanged unless targeted
   - structured result shape
   - sync behavior for `master` vs non-`master`
4. GREEN minimal commit code
5. RED tests for CLI
6. GREEN CLI wiring
7. docs update

Test discipline:

- Run tests as `uv run pytest -vv`
- Tee full output to timestamped logs under `logs/test-runs/`
- After each passing targeted run, reread:
  - [proposals/git-native-semantics-and-repo-import.md](/C:/Users/Q/code/propstore/proposals/git-native-semantics-and-repo-import.md)
  - [plans/multi-source-structured-merge-checklist.md](/C:/Users/Q/code/propstore/plans/multi-source-structured-merge-checklist.md)

Do not:

- do `merge-repo`
- change all semantic read defaults repo-wide
- widen into policy work
- silently import uncommitted source working-tree files

When done, report:

1. commits created
2. files changed
3. tests run with log paths
4. any deliberate defers or sharp edges
