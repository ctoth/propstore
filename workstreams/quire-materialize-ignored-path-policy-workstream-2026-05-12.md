# Quire Materialize and Ignored Path Policy Workstream

## Goal

Move generic worktree materialization and ignored-runtime-path mechanics into
`../quire`, then delete Propstore's storage wrapper boilerplate.

The target architecture is:

- Quire owns conflict-aware materialization of a commit or branch into a
  worktree, generic ignored-path predicates, and generic tree file walking.
- Propstore owns the ignored-path policy values, semantic clean roots,
  repository bootstrap/config/discovery, and user-facing materialize reports.
- `propstore/storage/snapshot.py` and `propstore/storage/git_policy.py` shrink
  sharply or disappear where they only forward to Quire.

This is deletion-first in Propstore. Once Quire exposes the generic operations,
delete the duplicate Propstore implementation before repairing callers.

This is a two-repository workstream. Quire changes land first. Propstore must
never pin Quire to a local path; pin only to a pushed tag or immutable pushed
commit SHA.

## Non-Goals

Do not move these into Quire:

- Propstore's ignored path values: `sidecar/`, SQLite suffixes, `.hash`, or
  `.provenance`
- `semantic_init_roots()` or semantic clean-root policy
- `Repository.find`, `Repository.init`, bootstrap manifest rules, or
  `propstore.yaml`
- sidecar rebuild policy
- CLI rendering of materialize reports

Do not keep Propstore pass-through methods around as aliases. If callers can use
`repo.git` or Quire directly, update them and delete the pass-through.

## Dependency Order

The phases below are topologically ordered.

1. Quire materialization tests
2. Quire generic materialize/file-walk implementation
3. Propstore dependency pin
4. Propstore git-policy wrapper deletion
5. Propstore snapshot pass-through deletion
6. Propstore semantic clean adapter
7. Final gates

## Phase 1: Quire Materialization Tests

Repository: `../quire`

Write failing tests for generic materialization behavior.

Required cases:

- materialize a commit into a filesystem worktree
- skip identical existing files
- refuse to overwrite local edits unless `force=True`
- report written paths
- support a generic ignored-path predicate during clean
- delete stale materialized files when `clean=True`
- skip ignored stale files during clean
- avoid deleting `.git`
- preserve empty/nonexistent branch failure semantics

Target tests:

- `../quire/tests/test_git_store.py`
- `../quire/tests/test_git_properties.py` if property coverage fits

Required gate:

- `uv run pytest tests/test_git_store.py tests/test_git_properties.py`

## Phase 2: Quire Generic Materialize/File-Walk Implementation

Repository: `../quire`

Add generic APIs.

Candidate API:

```python
report = git.materialize(
    commit=sha,
    root=path,
    clean_roots=("books", "notes"),
    ignored_path=lambda relpath: relpath.startswith("cache/"),
    force=False,
)

files = tuple(git.iter_tree_files(commit=sha, roots=("books", "notes")))
```

Required behavior:

- no Propstore vocabulary
- generic report type with written/deleted/skipped/conflict fields
- conflict errors name exact relative paths
- ignored path handling is function- or policy-driven
- tree walking is lazy where possible
- materialization does not require a Propstore repository object

Required gates:

- `uv run pytest tests/test_git_store.py tests/test_git_properties.py`
- `uv run pytest`

## Phase 3: Propstore Dependency Pin

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

## Phase 4: Propstore Git-Policy Wrapper Deletion

Repository: `propstore`

Delete first from `propstore/storage/git_policy.py`:

- `init_git_store`
- `init_memory_git_store`
- `open_git_store`
- `is_git_repo`
- `_is_ignored_runtime_path` if Quire now accepts the policy object or a generic
  predicate directly

Then repair callers to use `GitStore` classmethods with the Propstore policy
constant.

Target shape:

- Propstore keeps a `PROPSTORE_GIT_POLICY` value
- calls use `GitStore.open(root, policy=PROPSTORE_GIT_POLICY)` and similar
- `propstore/storage/__init__.py` either exports only policy values or is
  deleted if no production caller needs it

Search gates:

- `rg -F "init_git_store" propstore tests` returns no refs unless the symbol is
  deleted from production and only mentioned by a deletion gate
- `rg -F "open_git_store" propstore tests` returns no refs unless the symbol is
  deleted from production and only mentioned by a deletion gate
- `rg -F "is_git_repo" propstore tests` returns no Propstore wrapper refs

Required gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label git-policy-delete tests/test_init.py tests/test_git_backend.py tests/test_import_repo.py`
- `uv run pyright propstore`

## Phase 5: Propstore Snapshot Pass-Through Deletion

Repository: `propstore`

Delete pass-through methods from `RepositorySnapshot` before caller repair.

Deletion candidates:

- `primary_branch_name`
- `current_branch_name`
- `head_sha`
- `branch_head`
- `ensure_branch`
- `delete_branch`
- `iter_branches` if Quire exposes equivalent typed branch records
- `read_bytes`
- `read_text`
- `iter_dir`
- `iter_dir_entries`
- `files`
- `sync_worktree`
- `log`
- `show_commit`
- `diff`
- `merge_base`

Repair callers to use `repo.git` or Quire's generic API directly when no
Propstore policy is added.

Keep only methods that add Propstore-owned policy:

- semantic clean roots
- branch taxonomy if it remains Propstore-specific
- repository object convenience where it meaningfully reduces application code

Search gates:

- `rg -F "repo.snapshot." propstore tests` is reviewed and every remaining call
  adds Propstore policy rather than forwarding to Quire
- `rg -F "def branch_head" propstore/storage/snapshot.py` returns no refs if it
  is only a pass-through

Required gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label snapshot-pass-through-delete tests/test_git_backend.py tests/test_import_repo.py tests/test_repo_branch.py tests/test_repo_merge_object.py`
- `uv run pyright propstore`

## Phase 6: Propstore Semantic Clean Adapter

Repository: `propstore`

Delete the old local `materialize` implementation before adding the adapter to
Quire's generic materialize API.

Target shape:

- Propstore passes `semantic_init_roots()` as clean roots
- Propstore passes the Propstore ignored-path predicate or policy
- Quire performs conflict detection, writes, deletes, and report construction
- Propstore maps the Quire report into any user-facing app/CLI result if needed

Search gates:

- `rg -F "_clean_materialized_semantic_files" propstore tests` returns no refs
- `rg -F "MaterializeConflictError" propstore tests` returns no local duplicate
  unless it is a presentation alias over Quire's typed error
- `rg -F "MaterializeReport" propstore/storage` shows no duplicate generic
  report type

Required gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label materialize-adapter tests/test_worldline.py tests/test_import_repo.py tests/test_git_backend.py`
- `uv run pyright propstore`

## Phase 7: Final Gates

Repository: both

Final Quire gates:

- `uv run pytest`

Final Propstore gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label materialize-policy-full tests/test_init.py tests/test_git_backend.py tests/test_import_repo.py tests/test_repo_branch.py tests/test_repository_artifact_boundary_gates.py`
- `uv run pyright propstore`

Completion evidence:

- generic materialization behavior is implemented once in Quire
- Propstore stores policy values but not generic materialization mechanics
- `propstore/storage/snapshot.py` is materially smaller or deleted
- `propstore/storage/git_policy.py` no longer wraps one-line Quire constructors
- no local Quire dependency pin is committed
