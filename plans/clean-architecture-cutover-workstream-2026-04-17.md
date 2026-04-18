# Clean Architecture Cutover Workstream - 2026-04-17

## Objective

Cleanly converge the repository, storage, document schema, artifact persistence,
and compiled-world query surfaces before any typed GitStore extraction.

The goal is not to preserve the current shape. The goal is to delete old
surfaces, force one correct interface per ownership boundary, update every
caller, and let the tests expose hidden coupling.

## Non-Negotiable Cutover Rules

- Cut over first.
- Delete first.
- No wrappers.
- No aliases.
- No compatibility bridges.
- No fallback readers.
- No old/new dual paths.
- No bridge normalizers.
- No temporary adapter layer.
- No compatibility import re-exports.
- No "cleanup later" production path.

If a conversion cannot happen cleanly in a slice, stop immediately and report:

- the exact old surface that could not be removed
- the exact caller or invariant blocking removal
- the exact tests or type checks proving the block
- whether the slice was fully reverted or what kept reduction remains

Do not keep a partial old/new interface just to make tests pass.

## Current Shape Observed

This workstream is based on direct inspection of live code in `propstore/`.
It did not include a full test-suite read or a full-suite verification run.

Relevant current surfaces:

- `propstore.knowledge_path.KnowledgePath`
  - Read-only virtual tree over filesystem or git snapshot.
  - Implementations: `FilesystemKnowledgePath`, `GitKnowledgePath`.
  - Correct ownership: read-only semantic tree traversal.

- `propstore.loaded.LoadedDocument[T]`
  - Source metadata envelope for typed loaded documents.
  - Correct ownership: filename/source path/knowledge root/document carrier.

- `propstore.loaded.LoadedEntry`
  - Old dict-shaped compatibility envelope.
  - Target state: deleted.

- `propstore.artifacts.schema.DocumentStruct`
  - `msgspec.Struct` base for authored YAML document schemas.
  - Correct ownership: strict authored document schema boundary.

- `propstore.artifacts.documents.*`
  - Authored document schema structs.
  - Correct ownership: YAML document shape, not semantic runtime behavior.

- `propstore.repository.Repository`
  - Knowledge root/config/service access.
  - Correct ownership: locate/configure repo and expose tree/artifacts/snapshot.

- `propstore.storage.git_backend.GitStore`
  - Dulwich-backed git object store and refs/commits/worktree materialization.
  - Correct ownership: git mechanics and byte-level tree IO.

- `propstore.storage.snapshot.RepositorySnapshot`
  - History/read facade over git snapshots.
  - Correct ownership: snapshot reads/history operations.

- `propstore.artifacts.store.ArtifactStore`
  - Typed artifact persistence facade.
  - Problem: name collides with world/query protocol.

- `propstore.core.environment.ArtifactStore`
  - Compiled world/query protocol.
  - Problem: name collides with artifact persistence facade.

- `propstore.world.model.WorldModel`
  - Read-only reasoner over compiled sidecar SQLite.
  - Correct ownership: semantic query surface over compiled data.

- `_resources/schemas/*.schema.json`
  - Packaged JSON Schemas still coexist with `msgspec` document structs.
  - Claim validation still calls `jsonschema.validate`.

## Target Shape

The intended ownership chain is:

```text
Repository
  locates/configures the knowledge repo

GitStore
  owns git object storage, refs, commits, worktree materialization

KnowledgePath
  owns read-only tree traversal over filesystem/git snapshots

DocumentStruct/msgspec
  owns strict authored-document decoding and conversion

LoadedDocument[T]
  owns source metadata around typed loaded documents

ArtifactFamily + typed artifact persistence store
  owns typed refs, branch/path resolution, normalization, validation, writes

WorldModel / compiled world store protocol
  owns compiled sidecar query semantics

CLI
  owns command parsing and presentation only
```

## Global Execution Discipline

Work one slice at a time.

For each slice:

1. Define the target interface/name in its final form.
2. Delete or rename the old surface immediately.
3. Let type checks/tests/search expose every broken caller.
4. Update every caller to the target surface.
5. Run the slice gates.
6. Keep the reduction only if the gates pass.
7. If the gates fail and the fix is not obvious, inspect the failure directly.
8. If the slice cannot converge cleanly, revert that slice and report the block.

After any passing substantial targeted test run or full-suite run, reread this
plan and continue with the next incomplete slice.

Do not substitute passing tests for plan completion while old production paths
remain.

## Slice 1 - Rename Colliding Store Surfaces

### Problem

Two unrelated concepts are named `ArtifactStore`:

- `propstore.artifacts.store.ArtifactStore`
- `propstore.core.environment.ArtifactStore`

One is typed artifact persistence. The other is compiled semantic world query.
The shared name obscures ownership and would poison a later extraction.

### Target

Use distinct names with no compatibility aliases.

Recommended names:

- persistence: `ArtifactRepository`
- compiled query protocol: `WorldStore`

The exact names may change only if the replacement is clearer in code.

### Required Implementation Notes

- Cut over first: introduce the final names and remove the old names in the
  same edit before fixing callers.
- Rename classes, imports, annotations, tests, docs in production-facing code.
- Delete the old class names.
- Do not leave `ArtifactStore = ArtifactRepository`.
- Do not re-export old names from `__init__.py`.
- If public package exports currently expose the old name, update callers and
  tests to the new name.

### Gates

```powershell
rg -n -F "ArtifactStore" propstore tests
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label store-surface-rename tests
```

The `rg` gate may only return historical text in plans/reviews if the command is
broadened beyond `propstore tests`. Within `propstore tests`, the old name must
be gone.

## Slice 2 - Delete LoadedEntry

### Problem

`LoadedEntry` is an old dict-shaped compatibility envelope over
`LoadedDocument[dict[str, Any]]`.

It keeps `.data` alive and encourages loose payloads in semantic code.

### Target

Delete `LoadedEntry`.

Use one of:

- `LoadedDocument[TDocument]` for typed document loading
- a domain wrapper with explicit typed fields, such as `LoadedConcept`

### Required Implementation Notes

- Delete first: remove `LoadedEntry` before repairing import/call failures.
- Convert `context_types.py` and `core/concepts.py` call sites.
- Remove `.data` compatibility properties from production loaded domain objects
  unless they are replaced by explicit semantic methods.
- Tests should assert the target typed/document or record surface, not `.data`.
- Do not introduce a replacement `LoadedPayload`, `LoadedMapping`, or alias.

### Gates

```powershell
rg -n -F "LoadedEntry" propstore tests
rg -n "\.data" propstore tests
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label loaded-entry-removal tests
```

If `.data` remains, each remaining hit must be judged. Production compatibility
hits block the slice.

## Slice 3 - Centralize Typed YAML Loading

### Problem

`load_document` and `load_document_dir` provide the generic typed YAML loading
path, but some modules still duplicate directory traversal and decode logic.

Claims already mostly use the generic loader. Concepts still perform custom
file traversal before normalization.

### Target

All generic authored YAML file loading goes through:

- `decode_document_bytes`
- `decode_document_path`
- `load_document`
- `load_document_dir`

Domain loaders may transform typed loaded documents into semantic records, but
must not duplicate generic YAML scanning/decoding.

### Required Implementation Notes

- Cut over first: remove local duplicate traversal/decoding paths before
  repairing callers onto the generic typed loader.
- Refactor concept loading to:
  1. load `LoadedDocument[ConceptDocument]`
  2. normalize to `LoadedConcept`
- Keep `KnowledgePath` source metadata intact.
- Preserve deterministic ordering.
- Do not keep a concept-specific file traversal path if the generic loader can
  represent it.

### Gates

```powershell
rg -n "suffix == \"\\.yaml\"|suffix != \"\\.yaml\"|iterdir\\(" propstore
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label typed-loader-convergence tests
```

The search gate is diagnostic, not automatically zero. Each remaining YAML
traversal must be either:

- a non-document traversal with a stated reason
- an artifact-family listing concern
- deleted in this slice

## Slice 4 - Make DocumentStruct/msgspec the Authored Schema Boundary

### Problem

The repo has a strong `DocumentStruct` boundary, but loose dict/Mapping payloads
still appear in semantic paths.

### Target

Authored YAML ingress decodes into `DocumentStruct` models or explicitly partial
scanner structs.

Allowed partial scanner example:

- `ConceptIdScanDocument`, because it intentionally allows unknown fields for
  cheap ID scanning.

### Required Implementation Notes

- Cut over first: delete duplicate loose authored-document ingress before
  replacing callers with typed document decoding/conversion.
- Do not turn runtime semantic records into `msgspec.Struct` just because
  `msgspec` exists.
- Keep document schema and semantic domain objects separate when they encode
  different concepts.
- Convert decoded YAML/JSON/SQLite rows immediately at IO boundaries.
- Core semantic paths should not pass loose dicts as domain objects.

### Gates

```powershell
rg -n "dict\\[str, Any\\]|Mapping\\[str, Any\\]" propstore/core propstore/compiler propstore/world
rg -n "^import msgspec$|^from msgspec import" propstore
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label document-struct-boundary tests
```

The `dict`/`Mapping` search is diagnostic. Remaining hits must be classified as
IO boundary, payload rendering, SQLite row conversion, or removed.

`msgspec` imports should remain only in schema/document/boundary modules.

## Slice 5 - Remove JSON Schema Duplication

### Problem

Packaged JSON Schemas coexist with `msgspec` document structs.

Known live path:

- claim validation loads `claim.schema.json`
- compiler passes call `jsonschema.validate`

This creates duplicate authored-shape authority.

### Target

`DocumentStruct/msgspec` owns authored structure.

Semantic validation that is not expressible as document shape lives in typed
Python validators.

Delete JSON Schema files and code if they do not serve an external contract.

### Required Implementation Notes

- Delete first: remove the duplicate JSON Schema validation path before moving
  any truly semantic checks into typed Python validators.
- Start with claims.
- For each JSON Schema rule:
  - if it is authored shape, rely on `ClaimsFileDocument`
  - if it is semantic, move it to typed validation
  - if it is externally required, stop and report the exact external constraint
- Then handle form/concept schema resources.
- Do not keep JSON Schema as a second validation path for convenience.

### Gates

```powershell
rg -n -F "jsonschema" propstore tests
rg -n -F "schemas/" propstore tests
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label jsonschema-removal tests
```

Any remaining JSON Schema usage must be justified by an explicit external
contract. If there is no such contract, it blocks completion.

## Slice 6 - Clarify Repository, Snapshot, Storage, and KnowledgePath

### Problem

Some semantic code still depends on concrete repository directories or raw
filesystem operations where a `KnowledgePath` or artifact family should own the
surface.

### Target

- `Repository` locates/configures and exposes services.
- `KnowledgePath` is read-only semantic tree traversal.
- `GitStore` owns git mechanics and bytes.
- `RepositorySnapshot` owns history/snapshot reads.
- Artifact writes go through artifact families and transactions.

### Required Implementation Notes

- Cut over first: remove direct semantic dependence on concrete repository
  directory properties before repairing callers onto `KnowledgePath` or artifact
  families.
- Replace direct semantic reads from `repo.concepts_dir`, `repo.claims_dir`,
  `repo.forms_dir`, etc. with `repo.tree() / "concepts"` where appropriate.
- Keep direct filesystem path use only for repository initialization, sidecar
  SQLite file location, worktree materialization, and explicit filesystem glue.
- Do not add write methods to `KnowledgePath`.
- Do not write semantic artifacts with raw `Path.write_*` when an artifact
  family exists.

### Gates

```powershell
rg -n "repo\\.(claims_dir|concepts_dir|forms_dir|contexts_dir|stances_dir|justifications_dir|sources_dir|worldlines_dir)" propstore
rg -n "write_text\\(|write_bytes\\(|unlink\\(|mkdir\\(" propstore
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label repository-storage-boundary tests
```

The filesystem-operation search is diagnostic. Each remaining production write
must be classified as repository setup, sidecar/runtime artifact, git worktree
materialization, or removed.

## Slice 7 - Normalize ArtifactFamily Ownership

### Problem

Artifact families are intended to own typed refs, branch/path resolution,
document type, encode/decode, listing, and write normalization. Some callers
still reconstruct paths or payloads manually.

### Target

For every family-backed artifact:

- refs come from the family/store
- relpaths come from the family resolver
- document coercion goes through the artifact persistence store
- writes go through the artifact persistence store or transaction

### Required Implementation Notes

- Cut over first: delete caller-local artifact path/ref reconstruction before
  repairing those callers onto artifact families.
- Do not manually write `claims/foo.yaml`, `concepts/foo.yaml`, etc. where a
  family exists.
- Do not duplicate `ref_from_path` logic in callers.
- Keep family-specific normalization on the family.
- If a family is missing for a production artifact, add the real family and
  update all callers. Do not add a caller-local adapter.

### Gates

```powershell
rg -n "claims/.*\\.yaml|concepts/.*\\.yaml|forms/.*\\.yaml|contexts/.*\\.yaml|stances/.*\\.yaml|worldlines/.*\\.yaml" propstore
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label artifact-family-boundary tests
```

The path search is diagnostic. Remaining literal artifact paths must be
family definitions, tests intentionally constructing fixture files, or removed.

## Slice 8 - Prepare Storage for Typed GitStore Extraction

### Problem

`GitStore` currently contains at least one propstore semantic concern:
concept ID scanning via `ConceptIdScanDocument`.

A reusable typed GitStore extraction should not know about propstore document
schemas or semantic IDs.

### Target

`propstore.storage` should depend only on storage-level concepts.

Propstore-specific scans and semantic allocation policies should move to an
owner above storage, likely repository/artifact/domain service code.

### Required Implementation Notes

- Cut over first: remove semantic imports/methods from storage before repairing
  callers through the new owner.
- Remove imports from `propstore.storage` to artifact document schemas, core,
  compiler, world, or semantic validators.
- Move concept ID allocation policy out of `GitStore`.
- Keep generic git tree traversal and commit operations in `GitStore`.
- Do not introduce a storage callback wrapper to preserve the old method.
  Change the interface and update every caller.

### Gates

```powershell
rg -n "propstore\\.artifacts\\.documents|propstore\\.core|propstore\\.compiler|propstore\\.world" propstore/storage
rg -n -F "next_concept_id" propstore tests
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label storage-extraction-readiness tests
```

Completion requires no semantic document imports from storage.

## Final Completion Gates

Run these after all slices pass their targeted gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label clean-architecture-cutover tests
rg -n -F "LoadedEntry" propstore tests
rg -n -F "ArtifactStore" propstore tests
rg -n -F "jsonschema" propstore tests
rg -n "^import msgspec$|^from msgspec import" propstore
rg -n "propstore\\.artifacts\\.documents|propstore\\.core|propstore\\.compiler|propstore\\.world" propstore/storage
```

Final state is not complete if any old production path still coexists with the
new path.

## Stop Conditions

Stop and report instead of inventing compatibility when:

- a public API outside this repo requires the old name or shape
- a test encodes a real semantic invariant that conflicts with the target shape
- a conversion requires changing authored data semantics, not just code shape
- a storage extraction concern requires a new domain service design
- two consecutive implementation slices against the same target produce no kept
  reduction

The report must say plainly what was read, what was verified, and what remains
unverified.
