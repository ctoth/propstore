# Quire Typed Git Document Store Workstream - 2026-04-18

## Objective

Extract the generic typed git document-store substrate from propstore into
`quire`, then make propstore's semantic schema more declarative, versioned, and
registry-driven on top of that substrate.

This is one workstream with two ownership tracks:

1. `quire`: a standalone typed git document store.
2. `propstore`: declarative semantic families, versioned hooks, sidecar
   materializers, and domain policy.

The goal is not to preserve current module locations. The goal is to cut to the
target architecture directly: change interfaces, update every caller, and delete
the old production paths in each slice.

This plan is based on direct inspection of the current repo and an older
proposal at
`C:\Users\Q\code\working\propstore\plans\typed-documentstore-and-semantic-families-proposal-2026-04-17.md`.
Tests were not run while drafting this workstream.

## Non-Negotiable Rules

- `quire` must import no `propstore` modules.
- `quire` owns git objects, refs, notes, commits, snapshots, document codecs,
  artifact families, transactions, manifests, versions, and scan-aware APIs.
- `quire` must not know claims, concepts, source promotion, sidecars,
  argumentation, artifact codes, or propstore identity formats.
- Normal reads and writes must use the git object store, not the worktree.
- Worktree materialization is explicit export/debug behavior only.
- Generated, cached, or expensive outputs stored in git must carry versioned
  manifests.
- Versions are mandatory. Unversioned families, hooks, materializers, generated
  refs, generated notes, or build outputs are invalid.
- Point operations must not hide whole-repo scans.
- No compatibility shims, aliases, fallback readers, or old/new production
  paths unless the user explicitly requires support for old external data.

## Current Relevant Surfaces

Generic candidate surfaces:

- `propstore/storage/git_backend.py`
- `propstore/storage/branch.py`
- `propstore/storage/snapshot.py`
- `propstore/knowledge_path.py`
- `propstore/loaded.py`
- `propstore/artifacts/schema.py`
- `propstore/artifacts/codecs.py`
- `propstore/artifacts/types.py`
- `propstore/artifacts/store.py`
- `propstore/artifacts/transaction.py`

Propstore-specific surfaces that must not move as generic package code:

- `propstore/repository.py`
- `propstore/artifacts/documents/*`
- `propstore/artifacts/families.py`
- `propstore/artifacts/identity.py`
- `propstore/artifacts/codes.py`
- `propstore/artifacts/indexes.py`
- `propstore/artifacts/resolution.py` where claim-specific
- `propstore/concept_ids.py`
- `propstore/storage/repository_import.py`
- `propstore/storage/merge_commit.py` as a workflow
- `propstore/storage/merge_framework.py`
- `propstore/storage/paf_merge.py`
- `propstore/storage/paf_queries.py`
- `propstore/merge/*`
- `propstore/sidecar/*`
- `propstore/world/*`
- `propstore/source/*`
- `propstore/provenance/*` semantics

Known current leaks to address:

- `GitStore` hardcodes propstore author and ignore policy.
- `GitStore.init()` materializes `.gitignore` through `sync_worktree()`.
- `sync_worktree()` is called in ordinary semantic flows.
- provenance notes use Dulwich directly instead of a generic note API.
- generic codecs special-case propstore `ConceptDocument`.
- artifact store/family types depend on concrete `propstore.repository.Repository`.
- write operations flatten whole trees.
- concept ID allocation scans concept files.

## Target Architecture

```text
quire
  git object/ref/note store
  typed tree snapshots
  strict msgspec document boundary
  typed artifact families and transactions
  generated-output refs/notes and manifests
  version and storage-format contracts
  scan-aware point vs scan APIs

propstore
  Repository implements quire repository protocol
  semantic family registry
  family specs for claim/concept/source/etc.
  versioned semantic hooks and materializers
  provenance named graph schemas over quire notes
  sidecar compiler and world model
```

`quire` is the first implementation milestone after cleanup. Propstore's
declarative semantic schema is part of the same workstream, but it is
propstore-owned and follows the substrate extraction.

## Quire Package Scope

`quire` should provide:

- `GitStore`
- `GitStorePolicy`
- typed object IDs and commit IDs
- validated ref names
- branch helpers over `refs/heads/*`
- arbitrary refs under `refs/*`
- git notes over arbitrary `refs/notes/*`
- read-only tree path abstraction
- snapshot/history/diff/show APIs
- explicit materialize/export API
- `DocumentStruct`, strict `msgspec` YAML/JSON decode/convert helpers
- loaded document envelopes
- generic document codecs
- `ArtifactFamily`, `ResolvedArtifact`, `ArtifactContext`,
  `ArtifactRepository`, and `ArtifactTransaction`
- generated ref/note manifests
- storage format version APIs
- scan-aware API naming and tests

`quire` must not provide:

- propstore document schemas
- propstore family declarations
- sidecar schema or build logic
- provenance named graph semantics
- source promotion
- argumentation or semantic merge logic
- claim/concept identity normalization

## Propstore Semantic Scope

Propstore should provide:

- `SemanticFamilyRegistry`
- `FamilySpec`, `StageSpec`, `SurfaceSpec`, and `ConversionEdge`
- concrete family specs for source, claim, concept, stance, justification,
  context, form, worldline, provenance, merge, and future families
- typed hooks for semantic conversions
- typed materializers for sidecar rows
- family-specific ref types and path templates
- versioned provenance schemas over quire git notes
- policy for expensive outputs stored as refs, notes, sidecar rows, or caches

Start semantic declarations as typed Python objects. Do not start with YAML or
LinkML generation. Add schema-authored declarations later only after the Python
shape is stable.

## Versioning Contract

Versions are first-class and mandatory.

`quire` owns:

- package version
- storage format version
- ref/note layout version
- transaction manifest schema version
- generated artifact manifest schema version
- codec/document-boundary version where needed

Propstore owns:

- package version
- semantic registry version
- family spec versions
- document schema versions
- conversion hook versions
- sidecar materializer versions
- sidecar schema version
- generated output producer versions

Unversioned semantic declarations must be unrepresentable. Required shapes:

```python
@dataclass(frozen=True)
class VersionId:
    value: str

@dataclass(frozen=True)
class VersionedHook(Generic[TCallable]):
    name: str
    version: VersionId
    fn: TCallable

@dataclass(frozen=True)
class FamilySpec(Generic[TRef]):
    key: str
    version: VersionId
    stages: Mapping[RepresentationStage, StageSpec]
    edges: tuple[ConversionEdge, ...]
```

Raw callables are not legal conversion hooks. Generated refs and notes must be
written through APIs that require a manifest.

Every generated-output manifest records at minimum:

- `quire` package version
- `quire` storage format version
- propstore package version, if propstore generated it
- propstore semantic registry version, if semantic-family driven
- family spec versions involved
- hook and materializer versions involved
- sidecar schema version, if relevant
- source commit or annotated object
- output ref or notes ref

Stale or missing manifests make a generated output unusable. Rebuild instead of
guessing.

## Contract Manifest Enforcement

The failure mode to design against is every component carrying `0.1`, `1.0`,
or another unchanged token forever. The enforcement should stay small:
contracts are versioned, declarations are rendered into a checked-in manifest,
and tests fail when a contract changes without an explicit compatibility
decision.

Use two identities:

- package version: distribution metadata
- contract version: compatibility surface for persisted readers, writers,
  refs, notes, schemas, family specs, hooks, materializers, sidecar
  projections, and generated-output producers

The contract manifest is generated from declarations and checked into the
repository. It records enough stable structure to make behavior-affecting
changes visible in review: names, contract versions, document fields, family
surfaces, hook registrations, materializer registrations, ref layouts, notes
layouts, sidecar schemas, and generated-output producer declarations.

Rules:

- A contract version is mandatory for every persisted or generated ABI:
  storage format, ref layout, notes layout, document schema, family spec,
  conversion hook, materializer, sidecar schema, generated ref producer, and
  generated note producer.
- Contract versions are human decisions. They are not auto-bumped.
- CI regenerates the contract manifest and compares it to the checked-in
  manifest.
- If a contract body changes and its contract version changes, the manifest
  diff is accepted.
- If a contract body changes and its contract version does not change, the
  declaration must explicitly record compatibility with the previous contract.
- If a contract body changes with neither a version bump nor an explicit
  compatibility marker, tests fail.
- Generated outputs do not trust version strings alone. They record source
  commit, input object IDs where available, producer name, producer contract
  version, producer package version, and output ref or notes ref.
- Optional content digests may be added only where git object IDs are not
  enough. Do not build a general self-hashing framework.

The compatibility marker is review surface, not a loophole hidden in test code.
It should name the component, old contract version, new declaration identity as
represented in the manifest, and the reason the old contract remains valid.

This gives lazy agents one hard local failure: a changed declaration with an
unchanged contract version does not pass unless the change is deliberately
classified as compatible.

### Contract Manifest Shape

The manifest should be plain, deterministic, and generated from typed
declarations. Start with JSON or YAML; do not introduce a new schema language
for this first slice.

Proposed propstore path:

```text
propstore/contracts/semantic-contracts.yaml
```

Proposed `quire` path:

```text
quire/contracts/quire-contracts.yaml
```

Minimum manifest shape:

```yaml
format_version: 1
package:
  name: propstore
  version: 0.0.0
registry:
  name: semantic-family-registry
  contract_version: 2026.04.18
contracts:
  - kind: document_schema
    name: concept-document
    contract_version: 2026.04.18
    body:
      fields:
        - name: id
          type: ConceptId
          required: true
  - kind: family_spec
    name: concept
    contract_version: 2026.04.18
    body:
      stages:
        - source_document
        - canonical_document
        - sidecar_rows
      surfaces:
        - kind: git_document
          ref_scope: source
          path_template: concepts.yaml
      hooks:
        - concept-normalize
  - kind: conversion_hook
    name: concept-normalize
    contract_version: 2026.04.18
    body:
      input: source_concept_document
      output: canonical_concept_document
compatible_changes:
  - contract: concept-normalize
    contract_version: 2026.04.18
    reason: "Validation tightened for previously invalid input only."
```

The `body` is not a full copy of all implementation code. It is the stable
contract surface needed to catch compatibility-relevant drift. For hook and
materializer code, the body records typed inputs, typed outputs, registered
side effects, generated surfaces, and declared dependencies. It does not try to
hash arbitrary source code.

Required tooling:

- generate: render current declarations into the manifest format
- check: regenerate and fail if the checked-in manifest differs
- explain: print the changed contracts and whether each one bumped version,
  kept version with compatibility marker, or failed

The check command is the enforcement point used by local tests and CI.

## Refs, Notes, And Long-Running Outputs

Long-running or expensive outputs should usually not be materialized into the
worktree. They should be stored as git objects reachable from refs, notes, or
sidecar rows depending on semantics.

Candidate output classes:

- sidecar build manifests
- sidecar build input manifests
- embedding snapshots
- source finalize reports
- provenance named graphs
- merge analysis and partial framework outputs
- validation/build diagnostics
- artifact-code verification results
- semantic family registry manifests
- hook/materializer version manifests

Choice rules:

- Use a git note when metadata annotates an existing object without changing the
  object's identity.
- Use a namespaced ref when the output is a generated object or snapshot with
  its own lifecycle.
- Use a branch artifact when the output is authored or reviewable source state.
- Use sidecar rows when the output is query ABI for runtime reasoning.
- Use ephemeral cache only when the output is cheap to recompute or has no
  semantic/provenance value.

Propstore provenance named graphs should move from direct Dulwich notes usage to
a generic `quire` notes API. Propstore still owns the JSON-LD schema and
meaning of `refs/notes/provenance`.

## Scan Discipline

APIs must distinguish point operations from scans.

Point operations:

- load one family/ref
- save one family/ref
- read one path
- write one generated ref
- read one note
- write one note

Point operations must not scan unrelated directories or flatten the whole repo.

Scan operations:

- list family refs
- validate all
- build sidecar
- import repository
- diff commits
- export/materialize worktree
- whole-root history reports

Scan operations must be explicit in API name or documentation. Tests should use
instrumented readers or operation counters where practical, not timing-only
assertions.

Known point-operation risks:

- `GitStore._commit()` flattens the current tree.
- `diff_commits()` flattens both trees, acceptable only for diff.
- `sync_worktree()` scans git tree and worktree, acceptable only for export.
- `RepositorySnapshot.files()` recursively scans roots, acceptable only for
  explicit snapshot scans.
- `next_concept_id()` scans concepts and should become counter/ref/index policy.

## Implementation Phases

### Phase 0: Inventory And Classification

Produce four checked-in inventories under `plans/` or `reports/`:

- materialized/generated outputs and whether each should be ref, note, branch
  artifact, sidecar row, or ephemeral cache
- `sync_worktree()` callsites classified as remove, keep export-only, or test
  fixture only
- linear scans classified as point-operation blocker, explicit scan API, test
  fixture, or acceptable low-level primitive
- tests classified as quire unit/property, propstore integration, propstore
  semantic, obsolete, or rewrite

Gates:

```powershell
rg -n -F "sync_worktree" propstore tests docs plans
rg -n "for .* in .*iterdir|rglob\\(|glob\\(|_flatten_tree|files\\(" propstore tests
rg -n -F "dulwich.notes" propstore tests
```

### Phase 1: Storage Namespace Cleanup

Move semantic merge/import/PAF code out of storage ownership.

Targets:

- `propstore/storage/repository_import.py` -> propstore import workflow module
- `propstore/storage/merge_commit.py` -> propstore merge workflow module, after
  extracting any generic N-parent commit primitive
- `propstore/storage/merge_framework.py` -> semantic/world merge namespace
- `propstore/storage/paf_merge.py` -> semantic/world merge namespace
- `propstore/storage/paf_queries.py` -> semantic/world merge namespace

Acceptance:

- `propstore.storage` contains only generic storage or thin imports from
  `quire` after extraction.
- no production storage module imports Dung, PAF, claim, concept, stance,
  sidecar, source, world, or propstore artifact document schemas.

Gates:

```powershell
rg -n "propstore\\.storage\\.(merge|paf|repository_import)" propstore tests
rg -n "from propstore\\.(dung|claims|sidecar|world|source|artifacts\\.documents)" propstore/storage
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label storage-namespace-cleanup tests/test_repo_branch.py tests/test_merge_classifier.py tests/test_repo_merge_object.py tests/test_structured_merge_projection.py tests/test_import_repo.py
```

### Phase 2: Object-Store-Only Contract

Remove ordinary worktree materialization from semantic write paths. Keep
materialization only as explicit export/checkout/debug behavior.

Acceptance:

- artifact save/load/transaction paths do not call `sync_worktree()`
- source, concept, form, context, worldline, promote, and import workflows do
  not materialize unless command semantics explicitly say export/sync
- init commits seed objects without relying on materialized worktree files
- tests assert ordinary workflows leave worktree materialization unused

Gates:

```powershell
rg -n -F "sync_worktree" propstore
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label object-store-only tests/test_git_backend.py tests/test_knowledge_path.py tests/test_source_cli.py tests/test_contexts.py tests/test_form_workflows.py tests/test_project_init.py
```

Remaining `sync_worktree` production hits must be export/materialization only.

### Phase 3: Generic Refs And Notes API

Add generic ref and notes primitives before extraction.

Required concepts:

- validated `RefName`
- `BranchName` and branch helpers
- `NotesRef`
- typed object IDs
- `read_ref`, `write_ref`, `delete_ref`, `compare_and_swap_ref` where possible
- `write_note`, `read_note`, `delete_note`
- note APIs over arbitrary notes refs
- generic N-parent commit primitive

Acceptance:

- propstore provenance writes notes through the generic API
- annotated object identity is unchanged by note writes
- note updates move only the notes ref
- tests cover arbitrary refs and notes refs

Gates:

```powershell
rg -n -F "dulwich.notes" propstore tests
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label refs-notes tests/test_repo_branch.py tests/test_provenance_foundations.py tests/test_provenance.py
```

### Phase 4: Mandatory Version And Manifest Infrastructure

Introduce mandatory versions before generated refs/notes proliferate.

Acceptance:

- `VersionId` or equivalent exists
- `ContractManifest` or equivalent exists
- manifest generator and check command exist
- generated-output writes require manifests
- family specs, hooks, materializers, and generated outputs cannot be
  registered/written unversioned
- every generated-output manifest records source commit, input object IDs where
  available, producer name, producer contract version, producer package
  version, and output ref or notes ref
- a checked-in contract manifest is generated and tested
- changed contract bodies with unchanged contract versions require explicit
  compatibility markers in the declaration or manifest
- manifest check reports changed contracts as bumped, compatible, or failed
- registry construction fails on missing versions
- stale generated outputs are ignored or rebuilt
- placeholder contract versions are rejected after the first contract-manifest
  baseline

Gates:

```powershell
rg -n "FamilySpec\\(|VersionedHook\\(|Materializer\\(" propstore tests
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label mandatory-versioning tests/test_document_schema.py tests/test_artifact_store.py tests/test_contract_manifest.py tests/test_provenance_foundations.py
```

### Phase 5: Scan-Aware API Cleanup

Separate point APIs from scan APIs and fix the worst hidden scans.

Acceptance:

- point `load(family, ref)` reads one resolved path
- point `save(family, ref)` does not flatten the whole tree if the git backend
  supports path-local tree updates
- concept ID allocation no longer scans concept documents in ordinary concept
  creation
- explicit scan APIs are named and documented as scans
- instrumentation tests cover at least artifact point load and point save

Gates:

```powershell
rg -n "next_concept_id|_flatten_tree|RepositorySnapshot\\.files|load_document_dir" propstore tests
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label scan-discipline tests/test_git_properties.py tests/test_artifact_store.py tests/test_concept_workflows.py
```

### Phase 6: Extract Quire

Move the generic substrate into `C:\Users\Q\code\quire` or the agreed package
location.

Minimum package modules:

```text
quire/
  __init__.py
  versions.py
  git_store.py
  refs.py
  notes.py
  branch.py
  tree_path.py
  snapshot.py
  contracts.py
  manifests.py
  documents/
    __init__.py
    schema.py
    codecs.py
    loaded.py
  artifacts/
    __init__.py
    family.py
    store.py
    transaction.py
```

Propstore imports `quire` as an external dependency or workspace package.
Delete old propstore production implementations for moved code in the same
slice.

Acceptance:

- `quire` imports no `propstore`
- `quire` package metadata declares dependencies directly
- generic tests live in `quire`
- propstore uses `quire` public APIs only
- no compatibility re-export modules preserve old production paths unless the
  user explicitly asks for external compatibility

Gates:

```powershell
rg -n -F "propstore" C:\Users\Q\code\quire\quire
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label quire-extraction tests/test_repository_artifact_boundary_gates.py tests/test_git_backend.py tests/test_git_properties.py tests/test_knowledge_path.py tests/test_artifact_store.py tests/test_document_schema.py
```

Run `quire`'s own test suite from the `quire` repo with `uv run pytest`.

### Phase 7: Propstore Semantic Family Registry

Introduce a propstore-owned semantic registry over `quire`.

Required types:

- `RepresentationStage`
- `SurfaceKind`
- `FamilySpec`
- `StageSpec`
- `SurfaceSpec`
- `GitDocumentSurface`
- `GitTextSurface`
- `GitJsonSurface`
- `GitNoteSurface`
- `GeneratedRefSurface`
- `SqliteSurface`
- `VectorSurface`
- `ConversionEdge`
- `SemanticFamilyRegistry`

Required stages:

- source document
- source-local document
- canonical document
- identity payload
- domain object
- sidecar row(s)
- embedding entity
- argumentation projection
- provenance note
- generated diagnostic/ref output

Acceptance:

- every current artifact family has a corresponding semantic family or an
  explicit reason it is not semantic
- every family has a version
- every stored git surface has a branch/ref scope and path template
- every git note surface has a notes ref and document type
- every conversion edge names a versioned hook
- every sidecar surface names a versioned materializer
- semantic registry can render a deterministic contract manifest

Gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label semantic-family-registry tests/test_artifact_store.py tests/test_document_schema.py tests/test_contract_manifest.py tests/test_repository_artifact_boundary_gates.py
```

### Phase 8: Convert Simple Families To Specs

Start with low-semantic families:

- source notes
- source metadata
- context
- form
- worldline
- merge manifest

Acceptance:

- these families are declared as `FamilySpec`
- `ArtifactFamily` values are generated from specs or built mechanically from
  specs
- hand-written declarations for converted families are deleted
- tests cover source notes as text, metadata as JSON, and worldline as typed
  document

Gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label simple-family-specs tests/test_artifact_store.py tests/test_source_cli.py tests/test_contexts.py tests/test_form_workflows.py tests/test_worldline.py
```

### Phase 9: Convert Concept Family

Declare concept stages and versioned hooks:

- source concept document
- canonical concept document
- identity payload
- `ConceptRecord`
- sidecar rows
- embedding entity
- provenance note where applicable

Acceptance:

- concept document loading uses spec-backed families
- concept normalization remains typed propstore hook code
- concept sidecar population is registry-driven
- concept embedding projection is declared as a conversion edge
- concept ID allocation uses non-scan policy

Gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label concept-family-spec tests/test_concept_workflows.py tests/test_lemon_concept_documents.py tests/test_build_sidecar.py tests/test_graph_export.py tests/test_world_model.py
```

### Phase 10: Convert Claim And Relation Families

Declare claim, stance, justification, micropublication, and source relation
stages and hooks.

Acceptance:

- claim document loading uses spec-backed families
- claim identity normalization is a versioned hook
- claim compilation is a versioned materializer
- stance and justification projections are versioned
- claim embedding projection is a conversion edge
- raw source-local IDs remain explicit diagnostics/quarantine semantics

Gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label claim-family-spec tests/test_claim_compiler.py tests/test_validate_claims.py tests/test_source_claims.py tests/test_source_relations.py tests/test_claim_notes.py tests/test_build_sidecar.py tests/test_world_model.py tests/test_verify_cli.py
```

### Phase 11: Registry-Driven Sidecar And Generated Outputs

Refactor sidecar build and generated outputs to use family specs and manifests.

Acceptance:

- sidecar build records `quire`, propstore, registry, family, hook,
  materializer, and sidecar schema versions
- build input hashing is based on registered git surfaces plus schema/compiler
  versions
- generated diagnostics or expensive outputs use refs/notes with manifests
- raw `notes.md` remains source-branch text and is not compiled into reasoning
  rows

Gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label registry-sidecar tests/test_build_sidecar.py tests/test_claim_notes.py tests/test_graph_export.py tests/test_embed_operational_error.py tests/test_world_model.py tests/test_source_cli.py
```

### Phase 12: Final Boundary And Full Suite Gates

Final acceptance:

- no generic implementation remains duplicated in propstore
- no ordinary semantic workflow materializes the worktree
- `quire` has no propstore imports
- all generated outputs are version-manifested
- all semantic families, hooks, and materializers are versioned
- storage point operations do not hide whole-repo scans
- propstore semantic schema is inspectable through the registry

Final gates:

```powershell
rg -n -F "propstore" C:\Users\Q\code\quire\quire
rg -n -F "sync_worktree" propstore
rg -n "propstore\\.storage\\.(merge|paf|repository_import)" propstore tests
rg -n -F "dulwich.notes" propstore tests
rg -n "FamilySpec\\(" propstore
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label quire-semantic-family-cutover tests
```

## Test Ownership

Move or recreate in `quire`:

- generic git backend lifecycle/read/write/list/delete/batch/history tests
- branch ref and merge-base tests without propstore branch kind policy
- property tests for git store and tree path behavior
- tree path parity tests
- strict document schema loader tests
- generic artifact repository tests using toy families
- refs and notes tests
- generated manifest/version tests
- scan-discipline instrumentation tests

Keep in propstore:

- CLI tests
- repository discovery/init policy tests
- source branch/source promotion tests
- claim/concept/form/context/worldline workflow tests
- sidecar build and world model tests
- semantic merge/argumentation tests
- provenance named graph semantic tests
- family registry and semantic hook tests

Add propstore boundary tests:

- every semantic family has a version
- every conversion hook has a version
- every materializer has a version
- every generated ref/note write requires a manifest
- no row type is used as an authored document schema
- no authored document type is used as a sidecar row
- no canonical git surface accepts source-local-only fields except as hard
  validation failure
- no world/core semantic module imports low-level storage internals

## Stop Conditions

Stop and report instead of adding compatibility glue if:

- a slice cannot delete the old production path cleanly
- a public external API requires the old import path
- a generated output cannot be versioned because its producer is unclear
- a point operation cannot avoid a whole-repo scan without a real storage design
  change
- a worktree materialization call is required for semantics rather than export
- a family cannot be declared without hiding untyped semantic behavior
- two consecutive slices against the same target produce no kept reduction

The report must identify:

- the exact unfinished phase item
- the exact old surface still present
- the exact caller or invariant blocking removal
- the tests or searches used
- whether the slice was fully reverted or what kept reduction remains

## Completion Definition

This workstream is complete only when:

- `quire` is the sole owner of generic typed git document-store mechanics
- propstore imports `quire` through public APIs
- propstore semantic families are declarative and versioned
- generated refs/notes carry mandatory manifests
- ordinary semantic operations do not materialize the worktree
- scan-heavy operations are explicit
- full propstore tests pass through the logged pytest wrapper
- `quire` tests pass in the `quire` repo
