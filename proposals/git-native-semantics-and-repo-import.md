# Proposal: Git-Native Semantics And Repo Import

**Date:** 2026-03-30
**Status:** Draft
**Depends on:** `proposals/epistemic-operating-system-roadmap.md`, `proposals/multi-source-structured-merge.md`

---

## Problem

propstore already claims that the git object store is the source of truth and the working tree is only a materialized view:

- `propstore/repo/git_backend.py`
- `docs/git-backend.md`

But current live read semantics are still mixed:

- `Repository.tree(commit=None)` returns `FilesystemKnowledgePath` in `propstore/cli/repository.py`
- historical or explicit commit reads use `GitKnowledgePath`

This creates an architectural contradiction:

1. merge, revision, worldlines, and other durable epistemic objects want commit-scoped semantics
2. ordinary current-state reads can still depend on uncommitted local disk state
3. repo-to-repo ingestion becomes ambiguous because “what is the source state?” can mean either `HEAD` or the working tree

The design goal of this proposal is to remove that ambiguity.

---

## Design Rule

**For git-backed repositories, propstore semantics should be defined by git state, not by ambient working-tree state.**

More precisely:

1. the authoritative current state is `HEAD` of the selected branch
2. the working tree exists for human editing and inspection
3. semantic commands should not silently read uncommitted files
4. if the user wants a proposed/imported/draft state to matter semantically, that state should become a tracked commit or branch artifact first

This does **not** require abolishing the working tree physically.

It requires making the working tree semantically irrelevant by default.

---

## Current Inconsistency

The repo already has strong git-native pieces:

- `KnowledgeRepo.read_file()` and `KnowledgeRepo.list_dir()` read from the object store in `propstore/repo/git_backend.py`
- `GitKnowledgePath` exists for commit-scoped reads in `propstore/knowledge_path.py`
- merge reads explicit branch snapshots from git in `propstore/repo/merge_classifier.py`
- merge commits are emitted as formal storage objects in `propstore/repo/merge_commit.py`
- worldline/revision work is already oriented around durable replay objects rather than local disk accidents

But the default repository view still weakens that story:

- `Repository.tree(commit=None)` uses `FilesystemKnowledgePath` in `propstore/cli/repository.py`
- `ensure_git()` imports existing YAML from disk into git in `propstore/cli/repository.py`
- `import-papers` is still directory-oriented in `propstore/cli/compiler_cmds.py`

So the repo is already philosophically git-native, but not yet operationally git-native.

---

## Recommendation

Adopt this rule:

**If `Repository.git` exists, default semantic reads should resolve through git-backed `HEAD`, not the filesystem.**

Implications:

- merge/revision/worldline semantics stay coherent
- import can target a branch or commit cleanly
- uncommitted edits stop affecting reasoning silently
- proposal-like states must be materialized as commits or branches before they participate in reasoning

This is the stronger and cleaner direction than inventing more “working-tree semantic surfaces.”

---

## Repo Import Command

The immediate ergonomic feature that follows from this model is:

### `pks import-repo SOURCE_REPO`

Run from the destination repo, or via `-C DEST_REPO`.

Example:

```bash
uv run pks -C repo-a import-repo ../repo-b
```

Behavior:

1. inspect the source repo at committed `HEAD` by default
2. create or update an import branch in the destination repo, for example `import/repo-b`
3. import the source knowledge tree as repo-relative files on that branch
4. commit the import atomically
5. print a structured result including:
   - `source_repo`
   - `source_commit`
   - `target_branch`
   - `commit_sha`
   - touched paths

Then the normal flow becomes:

```bash
uv run pks -C repo-a import-repo ../repo-b
uv run pks -C repo-a merge inspect master import/repo-b
uv run pks -C repo-a merge commit master import/repo-b --target-branch master
```

---

## Why `import-repo` Before `merge-repo`

`merge-repo` is useful, but it should be a wrapper over a lower-level primitive.

Recommended layering:

1. `import-repo`
   - explicit
   - branch-producing
   - audit-friendly

2. `merge-repo`
   - convenience wrapper
   - calls `import-repo`
   - then `merge inspect`
   - optionally `merge commit`

This keeps the formal merge boundary honest.

---

## Source Capture Semantics

### Default mode

Default import should use the source repo’s committed `HEAD`.

Preferred implementation substrate:

- `git archive` when available
- or direct object-store/tree reads if we want to stay fully inside the repo abstraction

Why:

- no `.git/` leakage
- clean committed snapshot
- deterministic
- easy to report and replay

### Non-default working-tree mode

This should **not** be the default.

If ever added, it should require an explicit flag such as:

- `--working-tree`

That mode would mean:

- include uncommitted tracked/untracked files from the source filesystem
- produce an import commit from that local snapshot
- mark the result clearly as a working-tree-derived import

This is optional and should be deferred unless real user demand justifies the extra complexity.

---

## Read And Write Semantics

### Read side

The import planner should validate against commit-scoped repository state, not the ambient filesystem.

That means:

- concepts/forms/contexts should be resolved from the destination branch tip or an explicit read commit
- use `repo.tree(commit=...)` / `KnowledgeRepo.tree(...)`
- do not validate against local uncommitted files by default

### Write side

Do not invent a writable `KnowledgePath`.

Instead:

1. build a `dict[repo_relative_path, bytes]`
2. commit once via `KnowledgeRepo.commit_files(..., branch=target_branch)`
3. optionally materialize the result to disk according to sync policy

This keeps mutation explicit and atomic.

---

## Worktree Sync Policy

This is the main operational question.

Recommended policy:

- if `target_branch == master`, sync the worktree automatically
- otherwise do not sync by default

Optional flag:

- `--sync-worktree auto|never|always`

Default:

- `auto`

This avoids surprising users by overwriting the visible checkout when importing onto a non-checked-out branch, while still keeping the common path ergonomic.

---

## Proposed API Surface

### Planning

```python
plan_repo_import(
    destination_repo: Repository,
    source_repo_path: Path,
    *,
    target_branch: str | None = None,
    include_working_tree: bool = False,
) -> RepoImportPlan
```

`RepoImportPlan` should contain:

- `source_repo`
- `source_commit`
- `target_branch`
- `repo_name`
- `writes: dict[str, bytes]`
- `touched_paths`
- `sync_worktree_default`
- warnings

### Commit

```python
commit_repo_import(
    repo: Repository,
    plan: RepoImportPlan,
    *,
    message: str | None = None,
    sync_worktree: str = "auto",
) -> RepoImportResult
```

`RepoImportResult` should contain:

- `surface: repo_import_commit`
- `source_repo`
- `source_commit`
- `target_branch`
- `commit_sha`
- `touched_paths`
- `worktree_synced`

### CLI

```bash
uv run pks import-repo SOURCE_REPO
uv run pks import-repo SOURCE_REPO --target-branch import/foo
uv run pks import-repo SOURCE_REPO --dry-run
uv run pks import-repo SOURCE_REPO --message "Import foo snapshot"
```

Optional later wrapper:

```bash
uv run pks merge-repo SOURCE_REPO --inspect
uv run pks merge-repo SOURCE_REPO --commit --target-branch master
```

---

## Migration Direction

This command should not be implemented as a one-off hack.

It should sit inside a broader cleanup:

### Phase A

- spec and implement `import-repo`
- make it commit-oriented from day one

### Phase B

- audit semantic commands that currently use `FilesystemKnowledgePath`
- move git-backed repos toward `HEAD`-based semantic reads by default

### Phase C

- make working-tree-sensitive behavior explicit rather than ambient

This proposal is about Phase A and the design rule that justifies Phase B/C.

---

## Relation To Remaining Merge Work

This is **not** the next unchecked item in the active merge checklist.

The remaining merge work is still:

- reconcile `6.2` control docs with landed tests
- finish `6.3` structured-summary contract tightening
- do `6.5` policy-readiness scoping

So the recommended sequencing is:

1. finish Phase 6.5 planning/control work first
2. hand this import spec to another worker as a separate implementation track
3. do not pretend `import-repo` completes merge phase 6

That keeps the control surface honest.

---

## Sharp Objections

1. the repo is not yet fully write-native, only partially read-native
2. changing default semantic reads away from the filesystem is a bigger migration than just adding one CLI command
3. users may expect imported files to appear immediately in the visible tree even when the import target is a non-checked-out branch
4. `git archive` is good for committed snapshots, but not for uncommitted source edits

These objections are real, but they argue for a careful staged migration, not against the design rule itself.

---

## Bottom Line

The right principle is:

**For git-backed propstore repos, semantics should follow tracked git state by default.**

And the right first ergonomic feature under that principle is:

**`pks import-repo SOURCE_REPO`**

implemented as a branch-producing, commit-producing import command, not as a filesystem copy trick.
