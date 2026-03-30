# Knowledge Path Abstraction Plan

Date: 2026-03-29

## Decision

Use a single read-only virtual path abstraction for semantic knowledge-tree reads.

Do not keep the current split between:

- raw filesystem `Path` inputs
- `TreeReader`
- `LoadedEntry.filepath: Path | None`

Do not subclass `pathlib.Path`.

Do not standardize on `Repository.collection(name) -> Path | None` as the long-term model.

The right end state is:

- real `Path` for mutable worktree operations
- a read-only `KnowledgePath` for semantic tree reads from either the filesystem or git history

## Why The Current Design Is Still Wrong

The repo currently has three competing read-side models:

1. path-based loaders
2. reader-based loaders
3. loaded entries with optional concrete file paths

That leak shows up directly in code:

- `load_concepts(concept_dir: Path | None, *, reader: TreeReader | None)`
- `load_claim_files(claims_dir: Path | None, *, reader: TreeReader | None)`
- `load_contexts(contexts_dir: Path | None, *, reader: TreeReader | None)`
- `LoadedEntry.filepath: Path | None`

Those signatures admit that the abstraction is incomplete. If a loaded semantic file may or may not have a real filesystem path, then `Path` is not the correct read-side type.

The newest cleanup commit helps only cosmetically:

- `e722ef42c1d5c62ff7d010cce00ffe36027d380a`
- `refactor(repo): add Repository.collection() for optional-path access`

That change removes repeated call-site clutter, but it does not solve the design problem:

- `collection(name)` is stringly typed
- it still returns `Path | None`
- it is still filesystem-only
- callers still combine it with `reader.exists(...)`

So the read model is still split.

## Best Abstraction

### 1. Introduce `KnowledgePath`

Add a read-only virtual path abstraction for the semantic tree.

It should be:

- path-like
- rooted at the knowledge tree
- backed either by the live worktree or a git tree snapshot
- stable under typed use

This should be a small custom protocol or concrete class family modeled after `importlib.resources.abc.Traversable`, not a `Path` subclass.

Reason:

- `Traversable` is already the right conceptual model: traversable, readable, not necessarily a real filesystem path
- but the repo wants a slightly more pathlib-like surface than raw `Traversable`
- subclassing `Path` is the wrong fight and creates fake filesystem expectations

### 2. Required Surface

The read-side abstraction should support only what semantic readers need:

- `name`
- `stem`
- `suffix`
- `parent`
- `joinpath(...)`
- `/`
- `iterdir()`
- `exists()`
- `is_dir()`
- `is_file()`
- `read_bytes()`
- `read_text(encoding="utf-8")`
- `open("r" | "rb")`
- `as_posix()`

Optional but useful:

- `relative_to(...)`
- `with_suffix(...)`

This is intentionally read-only. No `write_text`, `mkdir`, `unlink`, or mutation methods.

### 3. Two Backends

Implement:

- `FilesystemKnowledgePath`
- `GitKnowledgePath`

Both represent paths inside the knowledge tree.

Examples:

- `repo.tree() / "claims" / "paper.yaml"`
- `repo.tree(commit=sha) / "concepts" / "foo.yaml"`

### 4. Repository API

Add:

- `Repository.tree(commit: str | None = None) -> KnowledgePath`

This becomes the canonical read entrypoint for semantic data.

Keep current concrete `Path` properties for mutable operations:

- `repo.concepts_dir`
- `repo.claims_dir`
- `repo.forms_dir`
- `repo.sidecar_path`
- `repo.worldlines_dir`

Those are still right for CLI commands that edit files, create directories, or write outputs.

## Loader End State

Loaders should stop accepting dual path-or-reader signatures.

Current:

- `load_concepts(concept_dir, reader=...)`
- `load_claim_files(claims_dir, reader=...)`
- `load_contexts(contexts_dir, reader=...)`

End state:

- `load_concepts(concepts_root: KnowledgePath)`
- `load_claim_files(claims_root: KnowledgePath)`
- `load_contexts(contexts_root: KnowledgePath)`

For convenience, callers should pass subtree roots:

- `load_concepts(repo.tree() / "concepts")`
- `load_claim_files(repo.tree(commit=sha) / "claims")`

## Loaded Entry End State

Replace:

- `LoadedEntry.filepath: Path | None`

with:

- `LoadedEntry.source_path: KnowledgePath`

That removes the current `None` leak and makes loaded artifacts uniformly locatable whether they came from disk or git history.

If some call site truly needs a concrete filesystem path, that need should be explicit and localized. It should not infect the whole read model.

## Relationship To `TreeReader`

`TreeReader` is not the right final abstraction.

Why:

- it is less expressive than a path-like object
- it forces callers into string subdir APIs like `list_yaml("claims")`
- it separates traversal from identity
- it created the current split with path-based code instead of replacing it

The migration should delete `TreeReader` after the new path abstraction lands.

## Relationship To `Repository.collection()`

`Repository.collection(name) -> Path | None` is a local cleanup, not the target architecture.

It is acceptable as a temporary call-site simplifier.

It should not be the final public read model because:

- `name` is a free string
- absence is represented as `None`
- git snapshots cannot use it
- it perpetuates filesystem-only thinking on the read side

## What This Fixes

This abstraction directly addresses the first failure cluster:

- path-vs-reader mismatches in sidecar and loaders
- `Path | None` leakage in loaded semantic artifacts
- dual-signature loader complexity

This should eliminate the design class behind failures like the direct sidecar helper mismatch that currently distinguishes `Path` callers from `TreeReader` callers.

## What This Does Not Fix

This does not, by itself, fix the other current failure clusters.

Those are separate architectural problems:

### 1. Parameterization contract split

`parameterizations_for(concept_id)` is not the same contract as a canonical parameterization catalog row.

That needs:

- a separate lookup-row type
- a separate catalog-row type

### 2. `HypotheticalWorld` capability mismatch

Some semantic stores can answer semantic queries without supporting full compiled-graph inventory.

That needs:

- a cleaner semantic-runtime protocol
- a separate graph-compilation capability boundary

### 3. Private helper boundary regressions

Helpers like the algorithm equivalence checker should normalize their inputs or expose honest helper contracts instead of silently narrowing accepted shapes.

That needs:

- helper redesign
- not path abstraction work

## Migration Order

### Phase 1: Introduce the new read abstraction

Add:

- `propstore/knowledge_path.py`

Define:

- `KnowledgePath`
- `FilesystemKnowledgePath`
- `GitKnowledgePath`

Also add:

- `Repository.tree(commit: str | None = None) -> KnowledgePath`

### Phase 2: Move loaders to subtree roots

Refactor:

- `validate.py`
- `validate_claims.py`
- `validate_contexts.py`

So they accept subtree `KnowledgePath` roots directly.

Keep thin compatibility wrappers only briefly if needed for migration.

### Phase 3: Replace `LoadedEntry.filepath`

Update:

- `loaded.py`
- loader call sites
- validation paths
- repo merge paths

to carry `source_path: KnowledgePath`.

### Phase 4: Refactor sidecar and merge readers

Refactor:

- `build_sidecar.py`
- `repo/merge_classifier.py`
- `repo/structured_merge.py`

to consume `KnowledgePath` trees rather than `TreeReader`.

### Phase 5: Delete `TreeReader`

Once all read-only semantic consumers are on `KnowledgePath`, remove:

- `TreeReader`
- `FilesystemReader`
- `GitTreeReader`

or reduce them to internal implementation details behind `KnowledgePath`.

## Non-Goals

- Do not fake a fully writable virtual filesystem.
- Do not subclass `pathlib.Path`.
- Do not keep both `TreeReader` and `KnowledgePath` permanently.
- Do not use this work to paper over unrelated row-contract or runtime-capability bugs.

## Recommendation Summary

The correct abstraction is:

- a single read-only virtual knowledge-tree path
- with filesystem and git implementations
- used uniformly by loaders, validators, sidecar build, and git-history readers

That is the right long-term replacement for the current mixture of raw `Path`, `TreeReader`, and `Path | None`.
