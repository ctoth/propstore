# Quire Document Family Store Engine Workstream

Date: 2026-04-18

## Goal

Extract the smaller abstraction hiding under propstore's artifact repository:
quire should provide the generic typed document-family storage engine, while
propstore keeps semantic families, normalization, validation, branch policy,
materialization policy, and workflows.

This is not a wholesale transplant of propstore's artifact store. The target is
a reusable engine that can prepare, load, save, delete, move, list, and
transactionally commit typed document families through a git-like backend.

## Target Architecture

Quire owns:

- typed document codecs and defaults
- tree/path views over git objects
- refs, notes, and blob-backed ref payloads
- contract manifest/version checks
- artifact family declaration metadata
- a generic document-family store engine
- a generic document-family transaction engine

Propstore owns:

- family declarations for sources, claims, concepts, worldlines, and related
  semantic artifacts
- document schemas
- normalization and validation hooks
- branch naming and promotion policy
- CLI/workflow behavior
- explicit worktree materialization decisions

The intended boundary is:

```text
propstore semantic family callbacks
        |
        v
quire DocumentFamilyStore + DocumentFamilyTransaction
        |
        v
quire GitStore / git-like backend protocol
```

Quire must not import propstore.

## Phase 1: Define The Quire Store Boundary

Add a new quire module, `quire.family_store`.

Required quire concepts:

- `DocumentStoreBackend` protocol:
  - `read_file(path, commit=None) -> bytes`
  - `commit_batch(adds, deletes, message, branch=None) -> str`
  - `branch_sha(name) -> str | None`
- `DocumentFamilyStore[TOwner]`
  - owns an opaque `owner`
  - owns a backend
  - owns default codec functions
  - resolves families and refs
  - prepares documents through normalize/validate hooks
  - loads, saves, deletes, moves, lists, and requires documents
- `DocumentFamilyTransaction[TOwner]`
  - accumulates adds/deletes
  - enforces a single branch per transaction
  - commits through the backend

Tests first in quire:

- save/load typed msgspec document through an in-memory git store
- `prepare` runs normalize before validate before encode
- delete produces a commit deleting the resolved path
- transaction writes multiple files in one commit
- transaction rejects cross-branch writes
- move deletes the old path and writes the new path
- custom family codecs override default codecs
- unsupported `list`, `ref_from_path`, and `ref_from_loaded` fail clearly

## Phase 2: Move Generic Store Code Into Quire

Move the generic behavior currently embodied by
`propstore.artifacts.store.ArtifactRepository` into quire's
`DocumentFamilyStore`.

Move the generic behavior currently embodied by
`propstore.artifacts.transaction.ArtifactTransaction` into quire's
`DocumentFamilyTransaction`.

Also move the generic path helper:

- `normalized_path(path)`

Do not move propstore semantic hooks, family declarations, or workflows.

## Phase 3: Replace Propstore Artifact Store Surface Directly

Delete `propstore.artifacts.store.ArtifactRepository`.

`Repository.artifacts` should return quire's
`DocumentFamilyStore[Repository]` directly, constructed with propstore's
semantic owner, git backend, and document codec defaults.

Delete `propstore.artifacts.transaction` and update callers/tests to use
`quire.family_store.DocumentFamilyTransaction` directly where they need the
generic transaction type.

Delete `propstore.artifacts.types`; propstore semantic families should use
`quire.artifacts` types directly instead of re-exporting or subclassing them.

Propstore tests first:

- boundary test that there is no `ArtifactRepository`
- boundary test that there is no propstore transaction/type re-export shim
- transaction object is quire's `DocumentFamilyTransaction`
- existing artifact-store tests remain the behavioral contract

## Phase 4: Tighten Callback Typing

Improve the quire declaration model so owner/store typing is explicit without
requiring propstore imports.

Target callback shapes:

- resolve callback: `(owner, ref) -> ResolvedArtifact`
- normalize callback:
  `(ArtifactContext[TOwner, TRef], document, DocumentFamilyStore[TOwner]) -> document`
- validate callback:
  `(ArtifactContext[TOwner, TRef], document, DocumentFamilyStore[TOwner]) -> None`
- list callback: `(owner, branch, commit) -> list[ref]`

Propstore can keep a local type alias if needed to avoid repeated owner
specialization in every family declaration.

## Phase 5: Enrich Contract Metadata

Extend propstore's contract manifest body for artifact families so tests catch
semantic-family drift without version bumps.

Include stable callback identifiers for:

- `resolve_ref`
- `coerce_payload`
- `decode_bytes`
- `encode_document`
- `render_document`
- `document_payload`
- `normalize_for_write`
- `validate_for_write`
- `list_refs`
- `ref_from_path`
- `ref_from_loaded`
- `scan_type`

Keep the existing checked-in manifest comparison and baseline version-bump
enforcement. A family callback change with the same contract version must fail.

## Phase 6: Remove Propstore Duplication And Shim Surfaces

- delete generic transaction implementation from propstore
- delete generic store implementation from propstore
- delete old propstore generic type aliases and re-export surfaces
- leave only propstore policy wiring, semantic family declarations, and
  semantic callbacks
- do not move semantic hooks into quire

## Phase 7: Final Verification

Run:

- `C:\Users\Q\code\quire`: `uv run pytest tests`
- `C:\Users\Q\code\propstore`: targeted artifact/source tests
- `C:\Users\Q\code\propstore`: `uv run pyright propstore`
- `C:\Users\Q\code\propstore`: full logged suite

Push quire and pin propstore to the final quire commit.

## Stop Conditions

Stop and reassess if:

- quire needs to import propstore
- propstore semantic hooks need to move into quire for the abstraction to work
- the generic store starts mirroring propstore workflow concerns
- transaction behavior requires worktree materialization
- branch semantics cannot be expressed through a small backend/branch resolver
  protocol
