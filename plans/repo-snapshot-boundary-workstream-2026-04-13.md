# Repo Snapshot Boundary Workstream

Date: 2026-04-13

## Goal

Finish the next architectural cut after artifact-boundary convergence.

The target is:

- `repo.artifacts` owns typed persisted artifacts
- `repo.snapshot` owns branch/head/tree/worktree/history mechanics
- workflow code does not touch `repo.git` directly

This is not a request to make `ArtifactStore` into a generic git wrapper.
The point is to keep the artifact boundary narrow and add a sibling boundary
for repository mechanics.

## Target Shape

Use three concrete surfaces:

1. `repo.artifacts`
   Owns:
   - artifact refs
   - artifact families
   - typed codecs
   - load/save/delete/list/move/render
   - typed transactions
   - artifact indexes/resolvers
   - artifact verification

2. `repo.snapshot`
   Owns:
   - branch existence/head lookup
   - branch create/delete/list
   - snapshot tree enumeration
   - snapshot file reads for non-artifact surfaces
   - worktree sync/materialization
   - log/diff/show/history
   - merge-base and other history/topology queries

3. Workflow / CLI / repo operations
   Own:
   - orchestration
   - domain semantics
   - user interaction
   - sidecar build logic

   They should call either `repo.artifacts` or `repo.snapshot`, but not
   `repo.git`.

## What Should Not Happen

- Do not widen `ArtifactStore` until it effectively means "the repository".
- Do not keep the name `ArtifactStore` while stuffing general git mechanics
  into it.
- Do not let workflows call both `repo.artifacts` and raw `repo.git`.
- Do not add compatibility shims; move callers and delete the old path.

## Proposed Boundary

Create a snapshot boundary object exposed from `Repository`, likely:

- `repo.snapshot`

That object should be the only workflow-facing route for repo mechanics.

Example responsibilities:

- `repo.snapshot.branch_head(name)`
- `repo.snapshot.ensure_branch(name, source_commit=None)`
- `repo.snapshot.primary_branch_name()`
- `repo.snapshot.current_branch_name()`
- `repo.snapshot.read_text(path, commit=...)`
- `repo.snapshot.read_bytes(path, commit=...)`
- `repo.snapshot.list_dir(path="", commit=...)`
- `repo.snapshot.export_tree(commit=..., destination=...)`
- `repo.snapshot.sync_worktree()`
- `repo.snapshot.log(branch=..., max_count=...)`
- `repo.snapshot.show_commit(sha)`
- `repo.snapshot.diff(commit1=..., commit2=...)`
- `repo.snapshot.tree(commit=...)`
- `repo.snapshot.merge_base(branch_a, branch_b)`

These names are illustrative; the important point is the split, not the exact
method names.

## Current Direct-Access Surface

The main remaining workflow-level repo access today is in:

- `propstore/source/common.py`
- `propstore/source/alignment.py`
- `propstore/source/promote.py`
- `propstore/source/registry.py`
- `propstore/repo/repo_import.py`
- `propstore/repo/merge_classifier.py`
- `propstore/repo/merge_commit.py`
- `propstore/repo/structured_merge.py`
- `propstore/cli/__init__.py`
- `propstore/cli/claim.py`
- `propstore/cli/compiler_cmds.py`
- `propstore/cli/context.py`
- `propstore/cli/concept.py`
- `propstore/cli/form.py`
- `propstore/cli/init.py`
- `propstore/cli/merge_cmds.py`
- `propstore/cli/repo_import_cmd.py`
- `propstore/cli/worldline_cmds.py`

Not all of these should be artifact-store clients. Some are legitimately
repo-facing, but they still should not touch `repo.git`.

## Slice Mapping

### Slice 1: Introduce `repo.snapshot`

Add the new boundary object and hang it off `Repository`.

Start by wrapping existing git operations without changing behavior:

- branch head / branch existence
- primary/current branch access
- tree access
- raw file reads
- directory listing
- worktree sync
- log/diff/show

This slice is only valid if at least one real caller is cut over immediately.

### Slice 2: Move Source Workflow Repo Mechanics

Targets:

- `source/common.py`
- `source/alignment.py`
- `source/promote.py`
- `source/registry.py`

Expected cleanup:

- no `repo.git` in source workflows
- source branch creation/head checks through `repo.snapshot`
- source sync/export through `repo.snapshot`
- branch scanning in promotion through `repo.snapshot`

### Slice 3: Move Repo Import Snapshot Mechanics

Targets:

- `repo/repo_import.py`

Expected cleanup:

- committed snapshot enumeration through `repo.snapshot`
- branch-head existence checks through `repo.snapshot`
- no direct `branch_head(...)` / `repo.git.head_sha()` calls in import workflow

### Slice 4: Move Repo-Facing CLI Commands

Targets:

- `cli/__init__.py` log/diff/show/checkout/promote
- `cli/merge_cmds.py`
- any remaining CLI command that directly reaches for `repo.git`

Expected cleanup:

- repo-facing commands still operate on history/worktree, but through
  `repo.snapshot`
- no CLI module directly touching `repo.git`

### Slice 5: Move Merge/Topology Mechanics

Targets:

- `repo/merge_classifier.py`
- `repo/merge_commit.py`
- `repo/structured_merge.py`

Expected cleanup:

- merge and topology code uses the snapshot boundary instead of a raw
  `KnowledgeRepo`
- branch-head/merge-base/tree access go through one repo-mechanics surface

This may suggest a small nested surface under snapshot, but the public repo
boundary should still stay coherent.

### Slice 6: Final Verification

Criteria:

- `rg -n -F "repo.git" propstore`
  - results should be limited to:
    - `propstore/artifacts/*`
    - `propstore/repo/git_backend.py`
    - `propstore/cli/repository.py`
    - the new snapshot boundary implementation

- `rg -n -F "branch_head(" propstore`
  - workflow hits should be gone

- `rg -n -F "read_file(" propstore`
  - workflow hits should be gone except true boundary internals

- broad targeted suite passes after the final cut

## Design Rules

- `repo.snapshot` may be a facade over existing `KnowledgeRepo` methods first.
- That facade should become the only workflow-facing repo-mechanics surface.
- `KnowledgeRepo` remains the low-level implementation detail.
- `ArtifactStore` stays typed-artifact-specific.

## Success Bar

The workstream is done only when the answer to "how do workflows touch repo
state?" is:

- typed persisted things: `repo.artifacts`
- repo mechanics: `repo.snapshot`

If the answer is still "well, some of them still use `repo.git` directly",
the workstream is not done.
