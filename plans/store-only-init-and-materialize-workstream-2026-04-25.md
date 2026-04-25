# Store-Only Init And Materialize Workstream

Date: 2026-04-25
Status: Draft

## Purpose

Make `pks init` initialize the authoritative propstore git store without
materializing semantic YAML files into `knowledge/` by default.

The new split is:

- `pks init` creates the store, commits bootstrap and seed artifacts, and records
  repository identity.
- `pks materialize` explicitly projects a committed store snapshot to loose files
  for human inspection, external editors, or export/debug workflows.
- Ordinary semantic commands read and write the store directly.

The work is not to add another path helper family. The work is to delete the
idea that repository-native semantic state is discovered from, proven by, or
mutated through directories on disk.

## Current Understanding

Observed current behavior:

- `pks` dispatches to `propstore.cli:cli`.
- The root CLI special-cases `init` so repository lookup is skipped before a
  repository exists.
- `pks init [DIRECTORY]` defaults to `knowledge/`.
- `propstore.app.project_init.initialize_project()` treats an existing
  `concepts/` directory as "already initialized".
- `Repository.init()` calls `init_git_store(root)`, then creates semantic
  directories and `sidecar/`.
- `init_git_store()` calls `GitStore.init(...)` and immediately
  `sync_worktree()`.
- `initialize_project()` commits packaged forms and concepts, then calls
  `repo.snapshot.sync_worktree()`.

Live verification before this plan:

- `uv run pks init` in a temp directory created `knowledge/.git`,
  `.gitignore`, semantic directories, runtime directories, and materialized seed
  YAML.
- Git history contained at least:
  - `Initialize knowledge repository`
  - `Seed default forms and concepts`

Already-good direction in current code:

- `Repository.tree()` returns a `GitTreePath` for git-backed repositories.
- Build/validate paths already have tests asserting uncommitted worktree edits
  do not affect git-backed semantic reads.
- `repo.families.*` already loads/saves typed artifacts through the git backend.
- Concept ID allocation already uses `refs/propstore/indexes/concept-id-counter`
  for git-backed repositories; the old `.counters` directory is no longer the
  production counter authority.

Main contradiction:

- The store is supposed to be authoritative, but init/discovery/tests still use
  filesystem shape as repository state.

## Target Architecture

`knowledge/` is a propstore repository container.

The authoritative semantic state is the git object/ref graph. The loose
filesystem tree is an optional projection.

Target command semantics:

- `pks init [DIRECTORY]`
  - creates a store-only propstore repository
  - writes bootstrap identity and seed artifacts to git
  - does not write `concepts/*.yaml`, `forms/*.yaml`, `claims/`, `contexts/`,
    `stances/`, `worldlines/`, `predicates/`, or `rules/` as loose files
  - does not create empty semantic directories as proof of initialization
  - may create only store/runtime control directories that are not semantic
    artifact surfaces

- `pks materialize [DIRECTORY]`
  - projects the selected commit or branch to loose files
  - defaults to current branch HEAD
  - has explicit overwrite/clean behavior
  - preserves ignored runtime outputs such as sidecar SQLite files
  - is the only ordinary command whose purpose is to write semantic YAML files
    into the worktree

- `pks build`, `pks validate`, `pks log`, `pks show`, `pks diff`,
  `pks checkout`, `pks concept`, `pks form`, `pks context`, `pks predicate`,
  `pks rule`, `pks source`, `pks proposal`, `pks worldline`, and repository
  import read/write committed semantic artifacts directly.

Storage layout target:

- The store must not be a normal non-bare git worktree with tracked files
  missing from disk. That state is corrupt-by-default: native git status sees
  mass deletions and a native git commit can destroy the seed tree.
- The target is a real bare/internal git store for store-only repositories. The
  implementation may use `knowledge/.git` as an internal bare store or a
  Quire-owned store directory, but it must not expose an index/worktree pair
  that claims unmaterialized semantic blobs are deleted.
- If Quire/Dulwich currently requires a non-bare worktree for `GitStore.init`,
  change Quire's interface instead of compensating in propstore.
- Native git worktree commands are not the source-of-truth interface for a
  store-only propstore repository. Propstore commands read the object store.
- `pks materialize` writes a projection of committed objects to loose files; it
  must not become a second authoritative store.
- `sync_worktree()` is not an ordinary semantic operation. It is replaced or
  narrowed to explicit materialization/export behavior.

Initial filesystem target:

- After `pks init`, no loose semantic directory or semantic YAML file exists.
- `.gitignore` is tooling/projection policy, not semantic content. If the final
  store layout has no native worktree, `.gitignore` may be produced by
  `pks materialize` rather than init.
- `sidecar/` is derived runtime output and may be created lazily by `pks build`;
  init does not need it as a proof of structure.

Repository identity target:

- Repository initialization is recognized by git-native state, not by
  `concepts/`.
- Add an explicit bootstrap marker, manifest, or ref owned by propstore.
- The marker must be committed or ref-backed in the store and include enough
  version information to identify the repository format.
- A stray `concepts/` directory is not an initialized repository.
- A `.git` directory without propstore bootstrap state is not a propstore
  repository.

Path surface target:

- Semantic family placement remains in the family registry.
- Callers ask `repo.families` / `repo.snapshot` / `repo.tree()` for semantic
  data.
- `Repository.concepts_dir`, `claims_dir`, `forms_dir`, `contexts_dir`,
  `stances_dir`, `worldlines_dir`, `counters_dir`, and similar semantic
  directory properties are deleted as production APIs.
- `sidecar_path` may remain because sidecar SQLite is derived runtime output,
  not semantic source truth.
- `config_path` needs an explicit decision: either make repo config a committed
  typed artifact or move it to a local runtime config surface. It must not stay
  an implicit semantic filesystem read.

## Non-Goals

- Do not preserve old and new init/materialization paths in parallel.
- Do not add compatibility shims such as `semantic_root_path_or_materialized`.
- Do not replace `concepts_dir` with renamed helpers like
  `concepts_root_path`, `concepts_location`, or `family_root`.
- Do not make `pks build` or `pks validate` materialize as a side effect.
- Do not treat local YAML edits as semantic mutations unless they enter through
  an explicit import/materialize/sync command that commits them.
- Do not use tests passing while ordinary semantic workflows still call
  `sync_worktree()` as evidence of completion.
- Do not delete `FilesystemKnowledgePath` or arbitrary external file/directory
  IO in this workstream. Plain paper/source authoring trees are external input
  surfaces; repository-native semantic storage is the git store.

## Workstream

### Phase 0: Baseline And Failing Contract Tests

Goal: lock the intended contract before deleting surfaces.

Add failing tests that assert:

- `pks init` creates a propstore store but does not create semantic loose files.
- `initialize_project()` seeds packaged forms/concepts into git only.
- `Repository.find()` recognizes a store-only propstore repo.
- `Repository.find()` rejects:
  - a plain directory containing `concepts/`
  - a plain `.git` repo without propstore bootstrap identity
- a repo with bootstrap identity but missing seed artifacts fails with an
  explicit corrupt/missing-seed diagnostic rather than looking uninitialized
- `pks validate` succeeds immediately after store-only `pks init`.
- `pks build` succeeds immediately after store-only `pks init` and writes only
  derived sidecar output.
- store-only init does not produce a native git state where seeded semantic
  artifacts appear deleted
- `pks materialize` creates the expected loose semantic files.
- Re-running `pks materialize --clean` removes stale materialized semantic files
  while preserving ignored runtime outputs.

Phase 0 gate:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label store-only-init-contract tests/test_init.py tests/test_project_init.py tests/test_knowledge_path.py
```

Expected status at first: fails for the new contract tests.

### Phase 1: Add Git-Native Bootstrap Identity

Goal: stop using directories as proof of initialization.

Delete first:

- the `semantic_root_path(CONCEPTS, root).is_dir()` initialized check in
  `initialize_project()`
- the `concepts/`-based repository recognition path in `Repository.find()`
- tests that assert init is complete because semantic directories exist

Implement:

- a propstore bootstrap manifest/ref in the git store
- `Repository.is_propstore_repo(root)` or equivalent owner-layer predicate
  backed by that manifest/ref
- `Repository.find()` based on store presence plus bootstrap identity
- an idempotent `initialize_project()` that reads bootstrap state

The bootstrap marker should include at least:

- repository format version
- propstore family registry contract version
- seed bundle version or seed commit identity
- primary branch name

Gate:

```powershell
rg -n -F "Already initialized" propstore tests
rg -n -F "semantic_root_path(PropstoreFamily.CONCEPTS.value" propstore
powershell -File scripts/run_logged_pytest.ps1 -Label bootstrap-identity tests/test_init.py tests/test_project_init.py tests/test_git_backend.py::test_repository_find_rejects_non_git_knowledge_dir
```

Completion for this phase:

- no production initialized/repository-found path depends on `concepts/`
- stray semantic directories do not make a repo valid

### Phase 2: Make GitStore Support A Real Store-Only Layout

Goal: stop forcing a checked-out worktree during store creation without creating
the unsafe "normal non-bare git repo with missing checkout files" state.

Delete first:

- `init_git_store()` calling `store.sync_worktree()`
- `GitStore.init()` behavior that assumes init must produce a materialized
  worktree
- tests whose contract is "init materializes `.gitignore`"

Implement the target Quire/propstore store interface directly:

- a real bare/internal store creation API
- repository detection for that store layout
- open/read/write/ref/history support for that store layout
- no on-disk index that can report committed seed files as deleted
- explicit materialization/export API separate from store mutation
- clear handling for `.gitignore`:
  - either it is materialized only by `pks materialize`
  - or it is a tooling file outside the semantic seed tree

Forbidden implementation:

- `Repo.init(root)` followed by skipping checkout/index refresh while HEAD
  contains seed forms/concepts. That produces a dangerous native-git state and
  is not a valid store-only implementation.

Gate:

```powershell
rg -n -F "sync_worktree()" propstore\storage propstore\app\project_init.py propstore\repository.py
powershell -File scripts/run_logged_pytest.ps1 -Label gitstore-store-only tests/test_quire_consumer_contracts.py tests/test_knowledge_path.py tests/test_git_backend.py
```

State gates:

```powershell
$tmp = Join-Path $env:TEMP ("pks-store-layout-" + [guid]::NewGuid().ToString("N"))
uv run pks init $tmp
git -C $tmp status --porcelain
```

Expected:

- either native `git status` is explicitly unsupported for the store-only
  layout, or it reports no tracked semantic deletions
- it must never report seed forms/concepts as deleted

Completion for this phase:

- store-only init produces committed seed objects
- no semantic YAML is written as a side effect of store creation
- the store is not left in an index/worktree-deleted state

### Phase 3: Add `pks materialize`

Goal: make projection explicit.

Add a new root CLI command:

```text
pks materialize [DIRECTORY] [--commit SHA | --branch NAME] [--clean] [--force]
```

Command semantics:

- default target is the current repository root
- default source is current branch HEAD
- writes committed semantic artifacts and bootstrap-visible tracked files to the
  loose filesystem tree
- creates parent directories as needed
- refuses to overwrite local untracked edits unless `--force` is passed
- with `--clean`, removes stale materialized semantic files no longer present in
  the selected snapshot
- preserves ignored runtime outputs, including sidecar SQLite files, WAL files,
  hash/provenance files, and explicitly ignored runtime paths

Owner-layer API:

- add materialization to `repo.snapshot`, not to CLI logic
- CLI constructs a typed request and renders a typed report
- report includes source commit, written paths, deleted stale paths, skipped
  ignored paths, and whether force/clean was used

Gate:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label pks-materialize tests/test_init.py tests/test_repo_snapshot.py tests/test_quire_consumer_contracts.py
```

Manual CLI smoke gate:

```powershell
$tmp = Join-Path $env:TEMP ("pks-materialize-" + [guid]::NewGuid().ToString("N"))
uv run pks init $tmp
Test-Path (Join-Path $tmp "concepts")
uv run pks -C $tmp materialize
Test-Path (Join-Path $tmp "concepts\measurement.yaml")
```

Expected:

- first `Test-Path` is `False`
- second `Test-Path` is `True`

### Phase 4: Delete Ordinary Semantic `sync_worktree()` Calls

Goal: ordinary semantic writes commit to the store and stop refreshing loose
files.

Delete production `repo.snapshot.sync_worktree()` calls from:

- `propstore.app.project_init`
- `propstore.app.concepts.mutation`
- `propstore.app.forms`
- `propstore.app.contexts`
- `propstore.predicate_workflows`
- `propstore.rule_workflows`
- `propstore.app.worldlines`
- `propstore.proposals`
- repository import default sync
- source promotion/alignment paths unless the command is explicitly a sync/export
  command

Keep materialization only in:

- `pks materialize`
- source sync/export commands whose command semantics explicitly write external
  files
- demo materialization helpers
- low-level snapshot/materialization implementation

Each deletion slice must update tests from "file exists on disk" to "artifact is
committed and loadable through `repo.families` or `repo.snapshot`".

Gate:

```powershell
rg -n -F "sync_worktree" propstore
powershell -File scripts/run_logged_pytest.ps1 -Label no-ordinary-sync tests/test_concept_workflows.py tests/test_form_workflows.py tests/test_context_workflows.py tests/test_predicate_workflows.py tests/test_rule_workflows.py tests/test_source_cli.py tests/test_import_repo.py
```

Allowed final `rg` hits:

- materialization implementation
- `pks materialize` CLI owner-layer call
- explicit source sync/export
- demo materialization helper
- tests for materialization behavior

### Phase 5: Delete Semantic Directory Properties

Goal: remove the public APIs that make loose semantic directories look
authoritative.

Delete production properties:

- `Repository.concepts_dir`
- `Repository.claims_dir`
- `Repository.forms_dir`
- `Repository.contexts_dir`
- `Repository.stances_dir`
- `Repository.justifications_dir`
- `Repository.sources_dir` if it refers to canonical/source semantic storage
  rather than an external workspace
- `Repository.worldlines_dir`
- `Repository.counters_dir`

Keep or re-home:

- `Repository.sidecar_path` and `sidecar_dir` as derived runtime output
- repository root itself
- explicit external user-provided paths
- package resource paths

Fix callers by using:

- `repo.families.<family>.address(ref).require_path()` for display paths
- `repo.families.<family>.load/require/iter/save/delete` for artifacts
- `repo.tree()` or `repo.snapshot.files()` for committed snapshot traversal
- typed owner-layer reports that carry semantic addresses, not filesystem paths,
  unless the command truly writes external files

Gate:

```powershell
rg -n "repo\\.(concepts_dir|claims_dir|forms_dir|contexts_dir|stances_dir|justifications_dir|sources_dir|worldlines_dir|counters_dir)" propstore
rg -n "def (concepts_dir|claims_dir|forms_dir|contexts_dir|stances_dir|justifications_dir|sources_dir|worldlines_dir|counters_dir)" propstore\repository.py
powershell -File scripts/run_logged_pytest.ps1 -Label delete-semantic-dir-properties tests/test_semantic_family_registry.py tests/test_artifact_store.py tests/test_artifact_reference_resolver.py tests/test_repository_history_reports.py
```

Completion for this phase:

- placement declarations are the production source of semantic paths
- repository semantic APIs no longer expose materialized directories

### Phase 6: Resolve Repository Config

Goal: remove the last implicit source-truth filesystem read.

Current issue:

- `Repository.config` reads `propstore.yaml` directly from disk through
  `config_path`.

Choose one target and implement it directly:

- committed typed repository config artifact in the store
- or local runtime config under non-semantic propstore control state

Default target for this project should be committed typed config unless there is
a real reason `uri_authority` must be machine-local.

Gate:

```powershell
rg -n -F "config_path" propstore tests
rg -n -F "propstore.yaml" propstore tests
powershell -File scripts/run_logged_pytest.ps1 -Label repository-config tests/test_uri.py tests/test_source_cli.py
```

Completion for this phase:

- no production semantic setting is read from an uncommitted loose file

### Phase 7: Rewrite Init, Materialize, And Git Backend Docs

Goal: make docs match the new contract.

Update:

- `docs/cli-reference.md`
- `docs/git-backend.md`
- relevant README/CLAUDE technical convention language if it still says
  `knowledge/` means materialized directories
- tests that encode doc examples

Required doc claims:

- `pks init` creates a store-only repository
- `pks materialize` projects a committed snapshot to loose files
- loose semantic files are not source truth
- local edits are not semantic input until explicitly imported/committed
- sidecar remains derived runtime output

Gate:

```powershell
rg -n -F "Creates the standard directory structure" docs README.md CLAUDE.md propstore tests
rg -n -F "working tree is a materialized view" docs README.md CLAUDE.md
powershell -File scripts/run_logged_pytest.ps1 -Label init-materialize-docs tests/test_cli_layout.py tests/test_init.py tests/test_quire_consumer_contracts.py
```

### Phase 8: Final Verification

Run package type check:

```powershell
uv run pyright propstore
```

Run focused store-only gates:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label store-only-init-final tests/test_init.py tests/test_project_init.py tests/test_git_backend.py tests/test_knowledge_path.py tests/test_quire_consumer_contracts.py tests/test_repo_snapshot.py
powershell -File scripts/run_logged_pytest.ps1 -Label store-only-workflows tests/test_concept_workflows.py tests/test_form_workflows.py tests/test_context_workflows.py tests/test_predicate_workflows.py tests/test_rule_workflows.py tests/test_source_cli.py tests/test_import_repo.py tests/test_build_sidecar.py
```

Run state-observation gates, implemented as tests rather than only shell
searches:

- after `pks init`, recursively snapshot the repository container excluding the
  store control directory; assert no semantic directories or seed YAML exist
- after representative semantic mutations, assert that same filesystem snapshot
  is unchanged until `pks materialize`
- after `pks init`, native git status must either be explicitly unsupported for
  the chosen store layout or report no tracked semantic deletions
- after `pks init` plus an empty native git commit if native git worktree mode is
  supported, seed forms/concepts must still be present in the propstore store
- after `pks init && pks build && pks materialize --clean`, sidecar SQLite/WAL,
  hash, and provenance outputs are preserved and not touched by clean
- AST-based tests assert app/workflow modules do not call any materialization
  function by renamed alias

Run full suite:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label store-only-init-full tests
```

Live CLI proof:

```powershell
$tmp = Join-Path $env:TEMP ("pks-store-only-final-" + [guid]::NewGuid().ToString("N"))
uv run pks init $tmp
uv run pks -C $tmp validate
uv run pks -C $tmp build
uv run pks -C $tmp materialize --clean
uv run pks -C $tmp validate
```

Expected:

- init writes no loose semantic tree before `pks materialize`
- validate/build work before materialization
- materialization writes seed forms/concepts
- validate still reads committed store state after materialization

## Definition Of Done

This workstream is complete only when all of the following are true:

- `pks init` does not materialize semantic YAML files or empty semantic
  directories by default.
- `pks init` seeds forms/concepts into the authoritative git store.
- the store-only layout is not a normal non-bare worktree with missing tracked
  files; native git cannot see the seed tree as a mass deletion.
- repository discovery and initialized-state checks are based on propstore
  git-native bootstrap identity, not `concepts/` or any semantic directory.
- `pks materialize` exists and is the explicit command for writing committed
  semantic artifacts to loose files.
- ordinary semantic workflows do not call `sync_worktree()` or any renamed
  equivalent.
- production code has no `Repository.*_dir` semantic directory properties.
- sidecar/runtime output paths remain explicit derived-output paths and are not
  confused with semantic source paths.
- repository config is either a committed typed artifact or explicitly local
  runtime config; it is not an uncommitted semantic filesystem read.
- tests prove uncommitted materialized edits do not affect `pks validate`,
  `pks build`, or semantic query behavior.
- tests prove `pks materialize` preserves ignored runtime outputs while cleaning
  stale materialized semantic files when requested.
- `uv run pyright propstore` passes.
- logged focused gates and the logged full suite pass.

## Completion Search Gates

These searches should be clean or contain only explicitly allowed hits:

```powershell
rg -n -F "semantic_root_path(PropstoreFamily.CONCEPTS.value" propstore
rg -n "repo\\.(concepts_dir|claims_dir|forms_dir|contexts_dir|stances_dir|justifications_dir|sources_dir|worldlines_dir|counters_dir)" propstore
rg -n "def (concepts_dir|claims_dir|forms_dir|contexts_dir|stances_dir|justifications_dir|sources_dir|worldlines_dir|counters_dir)" propstore\repository.py
rg -n -F "sync_worktree" propstore
rg -n -F ".counters" propstore
rg -n -F "config_path" propstore
```

Allowed remaining hits:

- materialization implementation and tests
- explicit source sync/export implementation
- demo materialization helper
- sidecar/runtime output paths
- package resource paths
- external file validation options

## Risks

- Quire may currently assume a non-bare worktree. If so, fix Quire rather than
  preserving propstore materialization as a workaround.
- Many tests assert loose files because older behavior made the checkout visible
  immediately. These tests should be rewritten to assert committed artifacts
  unless the test is specifically about `pks materialize`.
- Human-editable YAML workflows become explicit. That is intentional: editing
  loose files is not a semantic mutation until an import/commit workflow accepts
  them.
- Git CLI ergonomics may change for store-only repositories. The propstore CLI
  should be the supported interface for store-only repositories; `pks
  materialize` provides the inspection/export surface.
