# Quire Dependency Review (2026-04-20)

Scope reviewed: `C:\Users\Q\code\quire\quire\` (sources), `C:\Users\Q\code\quire\tests\` (contract surface), `README.md`, `CLAUDE.md`, `AGENTS.md`.
Propstore consumer sweep: `C:\Users\Q\code\propstore\propstore\` (all `from quire` imports).

Status: checkpoint dump. Findings below are observations grounded in the source; severities are my call. Do not treat as a ship/no-ship verdict.

## API Contract Issues

### 1. `GitStore.raw_repo` exposes raw dulwich `BaseRepo`
`C:\Users\Q\code\quire\quire\git_store.py:111`
Summary: Public `raw_repo` property hands the dulwich `BaseRepo` back to callers. Tests (`test_git_store.py:367`, `test_git_store.py:398`) use it to poke the object store directly. This is a leaky abstraction that bypasses every safety invariant the rest of `GitStore` maintains (expected-head checks, add-path conflict detection, branch-meta bookkeeping).
Severity: medium.
Fix: rename to `_raw_repo` or restrict to a documented escape hatch with a warning; add explicit typed helpers for the operations tests actually need (e.g. `object_store_contains(sha)`). Propstore does NOT use `raw_repo` today, so tightening would not break the current consumer.

### 2. `quire.documents` subpackage is heavily exported but not re-exported from `quire/__init__.py`
`C:\Users\Q\code\quire\quire\__init__.py:19-39`
Summary: The `__all__` in `quire/__init__.py` lists high-level types but omits the entire `quire.documents` surface (`DocumentStruct`, `LoadedDocument`, `decode_document_bytes`, `convert_document_value`, `load_document_dir`, `encode_document`, `decode_yaml_mapping`, ...). Yet propstore imports from `quire.documents` in ~40 files. README example uses `from quire.artifacts import ArtifactFamily, FlatYamlPlacement` which is also not re-exported.
Severity: medium (contract surface is de-facto wider than declared; any `__init__.py` tightening would silently break propstore).
Fix: either promote `quire.documents` (and other frequently-imported modules) to the advertised public surface, or document explicitly that `quire.documents`, `quire.artifacts`, `quire.family_store`, `quire.tree_path`, `quire.git_store` submodule imports are part of the contract. Then add a contract test that imports every symbol propstore depends on.

### 3. `raw_repo` typing vs. `notes.py` typing of `repo: Any`
`C:\Users\Q\code\quire\quire\notes.py:34-78`
Summary: Free functions `write_git_note`, `read_git_note`, `remove_git_note` take `repo: Any`. Propstore passes a `dulwich.repo.BaseRepo`. The contract is implicit; a future refactor could change the internal assumption (dulwich `Notes` class) silently.
Severity: low.
Fix: narrow parameter type to `BaseRepo` (already the actual contract — dulwich `Notes(repo.object_store, repo.refs)` is invoked internally).

### 4. `revert_commit` ignores branch membership
`C:\Users\Q\code\quire\quire\git_store.py:383-449`
Summary: `revert_commit(commit_sha, branch=...)` computes an inverse commit against the branch tip, but does not verify that `commit_sha` is actually reachable from the branch. Reverting a commit that was never on `branch` will silently produce a fresh commit on that branch whose tree differs only in paths the unrelated commit happened to touch. Propstore does not currently call `revert_commit`, but it's exposed.
Severity: medium.
Fix: require `commit_sha` to be an ancestor of `current_head` (use `ancestor_distances(current_head).get(commit_sha)`); raise `ValueError` otherwise.

### 5. `ReadOnlyDocumentStoreBackend` Protocol does not include `iter_dir`
`C:\Users\Q\code\quire\quire\artifacts.py:196-212`
Summary: The read-only protocol has `exists`, `read_file`, `iter_dir_entries`, `branch_sha` — but neither `iter_dir` nor `flat_tree_entries`/`commit_flat_tree`/`store_blob`. Consumers that need merge semantics (propstore does) must type against concrete `GitStore`, which defeats the protocol abstraction. `DocumentStoreBackend` (family_store.py:27) adds only `commit_batch`. There is no documented protocol for "store that can do merge commits".
Severity: low (observation on architecture).
Fix: either extend the backend protocol family to include merge-capable operations, or document that propstore merge paths require `GitStore` concretely.

## Consumer Drift (propstore → quire)

No hard drift detected. All propstore imports resolve against current quire exports. Details:

- `propstore\storage\git_policy.py:7` — `GitStore`, `GitStorePolicy`: OK, stable.
- `propstore\storage\merge_commit.py` — uses `flat_tree_entries`, `store_blob`, `commit_flat_tree`. All present. Note: propstore omits `expected_head` on merge commit write (propstore bug, not quire — flagged separately).
- `propstore\storage\snapshot.py` — uses `branch_sha`, `create_branch`, `delete_branch`, `iter_branches`, `merge_base`, etc.: all present.
- `propstore\provenance\__init__.py:31` — imports `NotesRef, read_git_note, write_git_note` from `quire.notes`: OK.
- ~40 files importing from `quire.documents`: all symbols exist.
- `propstore\concept_ids.py:7` imports `RefName` — OK.
- `propstore\families\registry.py:9` imports many artifact placement types — OK, all present in `quire.artifacts`.

Fragility points (will break if quire changes reasonably):

1. **`quire.documents` as a public API** (see issue 2). If quire tightens its exports to match `__init__.py`, ~40 propstore files break.
2. **`ReadOnlyDocumentStoreBackend` / `DocumentStoreBackend` protocol boundary**: propstore uses `DocumentFamilyStore(backend=self.git)` (`propstore/repository.py:130`). `GitStore` is not declared as implementing either protocol via nominal typing; it's structural. If signatures drift (e.g. `iter_dir_entries` default commit type changes), this will break silently.
3. **`LoadedDocument`** is a plain dataclass (`quire/documents/loaded.py:13`). Propstore passes it to `ref_from_loaded` (`quire/artifacts.py:339` et al.) which uses `getattr(loaded, "source_path", ...)`, `getattr(loaded, "knowledge_root", ...)`. Duck-typed — brittle but not currently broken.
4. **`GitStore.sync_worktree`** called unconditionally on `init_git_store` (`propstore\storage\git_policy.py:49`). If quire ever changes `sync_worktree` to require a HEAD, startup will regress.

## Correctness / Git Semantics

### 1. No atomic compare-and-swap on ref updates
`C:\Users\Q\code\quire\quire\git_store.py:680-725` (and `commit_flat_tree` at 262-308)
Summary: `_commit` reads `tip_sha`, validates `expected_head` if provided, then builds the commit object and writes the ref via `_ref_set(refs, branch_ref, commit.id)`. The read-validate-write is NOT atomic. `dulwich.refs.RefsContainer.set_if_equals(...)` would provide CAS; it is not used. With a concurrent writer (even in-process with threads), the `expected_head` check is vacuous — another writer between line 680 and line 725 will be overwritten.
Severity: medium to high (depends on whether quire has concurrent-writer guarantees — README doesn't say). For propstore as a single-process CLI, the risk is low. For any daemon/service use, this is a real hole.
Fix: use `refs.set_if_equals(branch_ref, expected_tip_bytes, commit.id)`. If expected_tip is unknown (expected_head=None), either disallow or use `set_if_equals(ref, None, commit.id)` for "create only".

### 2. Two-parent merge-commit parent ordering reflects caller
`C:\Users\Q\code\quire\quire\git_store.py:262-308`
Summary: `commit_flat_tree` sets `commit.parents = [parent.encode() for parent in parents]`, preserving caller order. Git convention: first parent is "ours" (the branch being merged into). Propstore's `create_merge_commit` passes `parents=[left_sha, right_sha]` where `left_sha = branch_head(branch_a)`. If `target_branch == branch_b`, the first parent is NOT the target branch tip, which violates the usual convention. Quire itself is faithful to the caller — this is a propstore contract issue to document, but quire could help by offering a `merge_commit(target_branch, side_branch, ...)` helper that enforces convention.
Severity: low (quire is correct as a primitive; documentation gap).

### 3. `ancestor_distances` re-enqueues with stale relaxation
`C:\Users\Q\code\quire\quire\git_store.py:451-463`
Summary: BFS over unit-weight DAG. The `previous is None or next_distance < previous` condition causes redundant re-queueing when a node is reached via multiple parents. For unit-weight edges, the first pop is already optimal; re-enqueue is dead work but not incorrect.
Severity: low (performance).
Fix: simplify to "if parent_sha not in distances: distances[parent_sha] = current_distance + 1; queue.append(parent_sha)".

### 4. `merge_base` recomputes `ancestor_distances` per common ancestor
`C:\Users\Q\code\quire\quire\git_store.py:481-484`
Summary: For every common ancestor, an independent BFS is run to compute its ancestor set. Over N common ancestors with history of depth D, this is O(N·D). In practice common ancestors are few, but for pathological criss-cross histories this can blow up. Not a correctness issue.
Severity: low.
Fix: compute reverse-ancestor relationships in one pass, or topologically sort common ancestors.

### 5. `materialize_worktree` has no dirty-tree check
`C:\Users\Q\code\quire\quire\git_store.py:579-600`
Summary: Writes every blob from HEAD into the worktree with `abs_path.write_bytes(blob.data)`. No check for existing local edits; silently overwrites user changes. `sync_worktree` additionally removes untracked files (subject to `ignored_path_prefixes`/`ignored_path_suffixes`). Propstore calls `sync_worktree()` at `init_git_store`.
Severity: medium — propstore's init is the main caller, and init on an empty repo is safe. But any caller invoking `sync_worktree()` on a populated repo will lose local edits.
Fix: add a `force: bool = False` parameter; refuse silent overwrite when content differs.

### 6. `materialize_worktree` does not sanitize tree paths
`C:\Users\Q\code\quire\quire\git_store.py:590-595`
Summary: `abs_path = self._root / rel_path` uses `Path` join. `Path(".") / "../evil"` resolves to `"../evil"` relative, but `Path("/root") / "../evil"` ends up at `"/root/../evil"` which resolves outside `_root` when the OS follows it. Git blob paths come from `_collect_tree_paths` which decodes raw tree entry bytes — a malicious tree could contain `..`. For a self-authored store this is academic.
Severity: low (controllable corpus).
Fix: assert `abs_path.resolve().is_relative_to(self._root.resolve())` before `write_bytes`.

### 7. `commit_flat_tree` does not de-dup against existing tree
`C:\Users\Q\code\quire\quire\git_store.py:262-308`
Summary: `commit_flat_tree` builds a root tree from `entries` alone — it does NOT consult the current branch tip's tree. If the caller forgets to include a path, that path is effectively deleted in the new commit even if it's untouched. Combined with the missing `expected_head` in propstore's merge path (`propstore/storage/merge_commit.py:114`), any race could drop files silently. This is the documented primitive contract, but the naming "flat tree" is easy to misuse.
Severity: medium (contract-use hazard).
Fix: rename to `commit_exact_tree` or add a docstring hazard note; consider `commit_merge(target_branch, side_branch, entries_overlay)` that composes the two parent trees before applying an overlay.

### 8. Ref/notes ref write has no CAS either
`C:\Users\Q\code\quire\quire\git_store.py:509-521` (`write_ref`, `write_blob_ref`)
Summary: `write_ref` unconditionally sets the ref. No before-image check available. Concurrent writers clobber. Same CAS issue as #1 but even more silent because there is no `expected_head` parameter at all.
Severity: medium.
Fix: add optional `expected: str | None = <sentinel>` param that compiles to `set_if_equals`.

### 9. `current_branch_name` can silently return None on detached HEAD; writers fall back to `primary_branch`
`C:\Users\Q\code\quire\quire\git_store.py:148-152`, `661-667`
Summary: `_resolve_write_branch_name(branch=None)` → `current_branch_name()` → primary branch. If HEAD is detached (symref not set to `refs/heads/...`), writes silently land on `master`. AGENTS.md says "Branch-head mismatches must fail before writing a new commit" — detached-HEAD fallthrough is not a head-mismatch, but it IS a surprising routing.
Severity: low-medium.
Fix: raise `ValueError("cannot resolve write branch in detached HEAD")` when HEAD is a non-branch ref.

## Silent Failures

### 1. `_read_branch_meta` swallows decoding errors
`C:\Users\Q\code\quire\quire\git_store.py:730-750`
Summary: On any JSON decode error, Unicode error, or non-dict shape, returns `{}` silently. A corrupted branch-meta blob ends up reported as a branch with `parent_branch=""` and `created_at=0`. The surrounding consumer in `iter_branches` (line 363-377) normalizes missing fields to defaults too.
Severity: low (corruption shows as benign absence — but obscures the real problem).
Fix: log or raise on malformed payload; treat as a hard error for branches with quire-managed meta.

### 2. `materialize_worktree` silently no-ops on missing HEAD
`C:\Users\Q\code\quire\quire\git_store.py:582-585`
Summary: `try: head = self._repo.head() except KeyError: return`. A repo with no HEAD (fresh init before any commit) silently produces no worktree. Acceptable, but the caller has no way to distinguish "materialized zero files because repo is empty" from "skipped because there is no HEAD".
Severity: low.
Fix: return a bool or a count; distinguish empty-success from no-head-skip.

### 3. `_subtree` / `_walk_tree` silently return None on non-Tree entries
`C:\Users\Q\code\quire\quire\git_store.py:752-789`
Summary: Walking through a tree, if an intermediate path component is not a Tree, returns None. Callers (`iter_dir`, `iter_dir_entries`, `read_file`) then treat this as "not found". A git object of type `Commit` at an intermediate path (submodule / gitlink) produces the same outcome as "does not exist". For a non-submodule store this is fine.
Severity: low.
Fix: if quire means to reject submodules entirely, log/raise on gitlink encounters.

### 4. `_remove_extra_worktree_files` swallows OSError on rmdir
`C:\Users\Q\code\quire\quire\git_store.py:988-991`
Summary: Empty-directory prune catches `OSError` and continues. This is right for "directory is not actually empty" but hides permission errors and locked files on Windows. Propstore runs on Windows.
Severity: low.
Fix: catch only `OSError` with errno in {ENOTEMPTY, EEXIST, EPERM}, re-raise for other errnos.

### 5. `DocumentFamilyTransaction._check_preemptive_head` skips early check when branch is unset on first save
`C:\Users\Q\code\quire\quire\family_store.py:387-398`
Summary: If `expected_head` is set but `branch` is None at `__post_init__` (i.e. caller did not pass `branch=`), the pre-emptive check in `save()` runs BEFORE branch is inferred from the first prepared artifact (`save` → `_check_preemptive_head` runs with branch=None → returns early; then branch is set). The final commit still validates via `commit_batch(expected_head=...)`, so this is a missed-early-detection only, not a correctness bug.
Severity: low.
Fix: infer target branch once (from any ref the transaction has touched) or require explicit `branch=` when `expected_head` is set.

### 6. `DocumentFamilyStore.move` returns via `cast` after `with`-block exits
`C:\Users\Q\code\quire\quire\family_store.py:240-242`
Summary: `return cast(str, transaction.commit_sha)`. If `__exit__` did not commit (e.g. no adds/deletes because `save` failed silently somehow), `commit_sha` is None and `cast` lies to the type checker. Practically, `save` always adds an entry, so `__exit__` always commits — but the type safety is nominal.
Severity: low.
Fix: assert `commit_sha is not None` with a specific error before returning.

## Bugs

### 1. `GitStore.write_note` hardcodes `message=b"Write note"` and reuses policy author for both author and committer
`C:\Users\Q\code\quire\quire\git_store.py:532-542`
Summary: The method signature exposes none of author/committer/message. Propstore's `write_provenance_note` bypasses `GitStore.write_note` and calls the free function directly (`propstore/provenance/__init__.py:223`). So propstore already knows the member method is too rigid.
Severity: medium (API friction → consumer-written bypass).
Fix: accept `author`, `committer`, `message` kwargs on `GitStore.write_note` / `.delete_note`, defaulting to policy author.

### 2. `_apply_tree_changes` delete-vs-add asymmetry allows stray empty directories
`C:\Users\Q\code\quire\quire\git_store.py:853-870`
Summary: When a directory becomes empty after deletes, the code prunes it from the parent. But if an add creates a new empty directory (unreachable via normal APIs — adds always have a filename), the prune loop is not defensive. Current API cannot produce empty dirs, so this is latent.
Severity: low (not reachable via current API).

### 3. Branch-meta blob isn't written for `create_branch(source_commit=...)` when HEAD is detached
`C:\Users\Q\code\quire\quire\git_store.py:319-351`
Summary: `parent_branch` is set only if `source_commit is None AND current_branch_name() is not None`. When `source_commit` is provided, `parent_branch = ""` regardless of the actual ancestor. The `created_at` timestamp is still recorded. OK as designed, but `iter_branches` will report `parent_branch=""` for every branch created with explicit source_commit, which may surprise consumers.
Severity: low (UX / semantics).
Fix: if `source_commit` matches a known branch tip, record that branch name.

### 4. `exists()` decodes `obj.id` even when intermediate walk hit a non-Tree
`C:\Users\Q\code\quire\quire\git_store.py:163-182`
Summary: Inside the for-loop over path parts, when `obj` becomes a `Blob` mid-path, the next iteration checks `if not isinstance(obj, Tree): return None`. That works, but between the blob assignment and the None return, `obj = self._repo.get_object(sha)` runs without type narrowing. Type is typed `Blob | Tree | Commit` via `_repo.get_object` semantics but here uses `self._repo.get_object` which returns a dulwich base object (not `_repo_object`). Inconsistent with `_walk_tree` which DOES use `_repo_object`. Low risk but an inconsistency worth noting.
Severity: low.
Fix: route through `_repo_object` for consistency.

### 5. `VersionId._parse_calendar_version` runs on every `<` comparison
`C:\Users\Q\code\quire\quire\versions.py:27-30`
Summary: Each `__lt__` reparses both strings. In tight loops (sorting many `ContractEntry`s by version) this is wasted work, and any `VersionId` constructed from a non-calendar format (allowed when `allow_placeholder=True`) raises `ValueError` on comparison instead of returning NotImplemented.
Severity: low.
Fix: cache parsed date at construction when it succeeds; raise `TypeError` on comparison with a placeholder.

### 6. `ContractManifest.__post_init__` sorts but check uses `.count()` quadratically
`C:\Users\Q\code\quire\quire\contracts.py:97-100`
Summary: `duplicates = sorted({key for key in keys if keys.count(key) > 1})` is O(n²). For large manifests (hundreds of families), minor. Correctness fine.
Severity: trivial.
Fix: use `Counter`.

## Dead Code

### 1. `GitStore.log` 
`C:\Users\Q\code\quire\quire\git_store.py:560-577`
Summary: Returns `list[dict[str, object]]` with pre-formatted time string. Propstore wraps it unchanged via `RepositorySnapshot.log`. Returning a `list[dict]` of untyped data violates quire's own "Structural typing throughout" README promise. Not dead, but stale-shaped.
Severity: low.
Fix: return typed `list[CommitRecord]` dataclasses.

### 2. `GitStore.diff_commits` / `.show_commit` return untyped dicts
`C:\Users\Q\code\quire\quire\git_store.py:602-648`
Summary: Same as above — `dict[str, list[str]]` and `dict[str, object]`. Propstore exposes `snapshot.diff`/`snapshot.show_commit` with `-> dict` / `-> dict`. Unsafe contract.
Severity: low.
Fix: introduce `DiffSummary`, `CommitSummary` typed structs.

### 3. `FilesystemTreePath.from_filesystem_path` uses `relative_to(anchor)`
`C:\Users\Q\code\quire\quire\tree_path.py:95-99`
Summary: For a plain file path, `absolute.relative_to(Path(absolute.anchor))` is almost always the full path minus drive/root. Works, but the abstraction of "root" as drive-anchor is a strange choice — `cache_key` then resolves the root again. No real bug; just awkward.
Severity: trivial.

### 4. `TreePath.open` Protocol requires `TextIO | BinaryIO` return, concrete impls return `StringIO | BytesIO`
`C:\Users\Q\code\quire\quire\tree_path.py:26, 65-70`
Summary: `StringIO` is a `TextIO` and `BytesIO` is a `BinaryIO`, so type-wise fine. The Protocol only supports `r` and `rb` modes — `"rt"`, `"rU"` etc. raise. Users cannot write via TreePath. Documented non-goal.
Severity: none.

## Positive Observations

- **Refs are validated at construction.** `RefName` and `NotesRef` reject malformed refs with clear `ValueError`s. Tests cover invalid cases (`test_refs.py`).
- **Expected-head checks are wired end-to-end.** `commit_batch`, `commit_files`, `commit_deletes`, `commit_flat_tree`, `revert_commit` all accept `expected_head`; the `DocumentFamilyTransaction` also supports it and does a pre-emptive check before building the commit. AGENTS.md promises this; implementation keeps the promise (modulo the CAS atomicity gap noted above).
- **Branch metadata survives reopen** via `refs/quire/branch-meta/<name>` blobs — tested (`test_branch_metadata_survives_reopening_filesystem_repo`). Clean separation from refs/heads/.
- **No git shell-out.** Everything goes through dulwich; deterministic, testable, in-memory-friendly. `MemoryRepo` support enables propstore's test suite to run without touching disk.
- **Placement-policy abstraction is clean.** `ArtifactPlacementPolicy` protocol, five concrete placements (`FlatYamlPlacement`, `HashScatteredYamlPlacement`, `FixedFilePlacement`, `TemplateFilePlacement`, `SingletonFilePlacement`), each with `contract_body()` for versioning.
- **ContractManifest enforces the "bump or marker" discipline.** `check_contract_manifest` raises `ContractManifestError` on shape drift without a version bump and no compat marker. Tests confirm.
- **Iterator-first discipline is respected.** `iter_branches`, `iter_dir`, `iter_dir_entries`, `BoundFamily.iter`, etc. No list-returning point-operations snuck in.
- **`_apply_tree_changes` has a real path-conflict model.** It distinguishes file-vs-dir conflicts at commit time (`path conflict at ...`) rather than producing a mangled tree. Deep-tree property test (`test_deep_tree_paths_do_not_depend_on_python_recursion_limit`) demonstrates the iterative algorithm.
- **`test_git_properties.py` exists.** 1353 lines of Hypothesis stateful tests against the git substrate. Rare and good.

## Propstore → Quire call-site fragility summary

| Propstore file | Quire entry | Breakage-on-reasonable-change risk |
| --- | --- | --- |
| `propstore/storage/git_policy.py` | `GitStore.init/init_memory/open`, `GitStorePolicy` | Low — stable surface |
| `propstore/storage/merge_commit.py` | `flat_tree_entries`, `store_blob`, `commit_flat_tree` | Medium — no expected_head passed; quire's semantic primitives name could evolve |
| `propstore/storage/snapshot.py` | `branch_sha`, `create_branch`, `delete_branch`, `iter_branches`, `merge_base`, `primary_branch_name`, `current_branch_name`, `head_sha`, `read_file`, `iter_dir`, `iter_dir_entries`, `sync_worktree`, `log`, `show_commit`, `diff_commits` | Medium — broad surface; untyped `log`/`diff_commits`/`show_commit` returns are a future-shape liability |
| `propstore/provenance/__init__.py` | `NotesRef`, `read_git_note`, `write_git_note` (free functions) | Low — consumer uses free functions precisely because `GitStore.write_note` is too rigid (issue Bugs#1) |
| `propstore/repository.py` | `GitStore` cached property, `DocumentFamilyStore` constructor, `GitTreePath`, `FilesystemTreePath` | Low — stable |
| 40+ files across propstore | `quire.documents.*` | HIGH — `quire/__init__.py` does not advertise `quire.documents` as public (see API Contract #2). Any `__init__.py`-driven privatization would cascade. |

## Recommended near-term actions (for quire maintainers, not me to take)

1. Document `quire.documents`, `quire.artifacts`, `quire.family_store`, `quire.tree_path` as part of the public import surface OR re-export through `quire/__init__.py` consistently.
2. Use `dulwich` CAS (`set_if_equals`) in `_commit` and `commit_flat_tree`.
3. Extend `GitStore.write_note` signature with author/committer/message kwargs — eliminate the propstore bypass.
4. Add an `expected_head`-aware `merge_commit` helper that enforces first-parent = target branch tip and composes two parent trees (the propstore merge path today builds this ad hoc and without `expected_head`).
5. Type the `log`/`diff_commits`/`show_commit` returns.
6. Validate `revert_commit`'s `commit_sha` is ancestor of target branch tip.
