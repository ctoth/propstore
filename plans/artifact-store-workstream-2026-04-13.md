# Artifact Store Workstream

Date: 2026-04-13

## Goal

Replace the current repo-artifact persistence story:

- ad hoc `yaml.safe_dump(...)`
- ad hoc `decode_document_path(...)` / `decode_document_bytes(...)`
- ad hoc `repo.git.commit_batch(...)`
- per-module branch/path resolution
- per-module identity normalization
- per-module local/logical reference rewriting

with one typed artifact layer that owns:

1. typed git-backed YAML persistence
2. typed artifact addressing
3. atomic multi-artifact commits
4. family-specific normalization and validation hooks
5. family-specific identity policy
6. cross-artifact reference resolution

This is not a helper extraction. It is a hard cut to a new boundary.

## Cutover Strategy

Use a build-then-delete slice strategy:

1. build the minimal infra needed for one artifact family
2. switch that family to the new path immediately
3. delete the old production path for that family in the same slice
4. keep tests green
5. move to the next family

Do not:

- build the full abstraction stack first and migrate later
- preserve old and new persistence paths in parallel for convenience
- let “adapter” code become a semi-permanent bridge

The correct pattern is:

- infra first
- immediate family cutover
- immediate deletion

That is the only way to keep the cutover simple.

## Architectural Claim

The hidden abstraction in this repo is not “an ORM”.

It is:

- a typed artifact store over git-backed YAML
- plus identity policy
- plus reference resolution

Those three seams are currently smeared across:

- [source/common.py](/C:/Users/Q/code/propstore/propstore/source/common.py)
- [source/concepts.py](/C:/Users/Q/code/propstore/propstore/source/concepts.py)
- [source/claims.py](/C:/Users/Q/code/propstore/propstore/source/claims.py)
- [source/relations.py](/C:/Users/Q/code/propstore/propstore/source/relations.py)
- [source/finalize.py](/C:/Users/Q/code/propstore/propstore/source/finalize.py)
- [source/promote.py](/C:/Users/Q/code/propstore/propstore/source/promote.py)
- [source/alignment.py](/C:/Users/Q/code/propstore/propstore/source/alignment.py)
- [repo/repo_import.py](/C:/Users/Q/code/propstore/propstore/repo/repo_import.py)
- [cli/worldline_cmds.py](/C:/Users/Q/code/propstore/propstore/cli/worldline_cmds.py)
- [cli/concept.py](/C:/Users/Q/code/propstore/propstore/cli/concept.py)

The workstream only succeeds if those old paths are deleted rather than wrapped.

## Technology Choice

Lean into:

- `msgspec` for typed document models and strict conversion
- small dataclasses for refs and specs
- explicit functions and policies instead of framework-heavy inheritance

Do not introduce:

- SQLAlchemy
- SQLModel
- an ORM-backed domain layer
- Pydantic as a second primary model system

If extra library support is needed later for generic dataclass structuring, the
only plausible addition is `cattrs`, and only after the artifact-store cut
proves a real need.

## Design Principles

- The store owns persistence mechanics, not domain semantics.
- Family specs own path resolution and write hooks.
- Identity policies own `logical_ids`, `artifact_id`, and `version_id`.
- Reference resolution owns local/logical/canonical lookup.
- Callers should ask for typed artifacts, not manipulate git/YAML directly.
- No dual old/new persistence paths in steady state.
- No compatibility shims unless an external constraint explicitly requires one.

## Module Layout

Add a new package:

- [artifacts/](/C:/Users/Q/code/propstore/propstore/artifacts/)
  - `__init__.py`
  - `codecs.py`
  - `refs.py`
  - `types.py`
  - `families.py`
  - `store.py`
  - `transaction.py`
  - `identity.py`
  - `indexes.py`
  - `resolution.py`

Recommended responsibilities:

- `codecs.py`
  - the only production module importing `yaml`
  - encode/decode typed artifact documents
  - preserve strict source-labelled errors

- `refs.py`
  - artifact reference types

- `types.py`
  - `ResolvedArtifact`
  - `ArtifactContext`
  - small shared generics and protocols

- `families.py`
  - `ArtifactFamily`
  - concrete family declarations

- `store.py`
  - `ArtifactStore`

- `transaction.py`
  - atomic multi-artifact writes/deletes

- `identity.py`
  - `ClaimIdentityPolicy`
  - `ConceptIdentityPolicy`

- `indexes.py`
  - branch/commit scan and lookup indexes

- `resolution.py`
  - `ReferenceResolver`

## First-Cut API

### Core refs

Use small explicit ref types, not stringly-typed tuples:

```python
@dataclass(frozen=True)
class SourceRef:
    name: str


@dataclass(frozen=True)
class SourceArtifactRef:
    source: SourceRef
    artifact_name: str


@dataclass(frozen=True)
class WorldlineRef:
    name: str


@dataclass(frozen=True)
class AlignmentRef:
    cluster_id: str


@dataclass(frozen=True)
class CanonicalConceptRef:
    handle: str
```

### Shared types

```python
TRef = TypeVar("TRef")
TDoc = TypeVar("TDoc")


@dataclass(frozen=True)
class ResolvedArtifact:
    branch: str
    relpath: str
    commit: str | None = None


@dataclass(frozen=True)
class ArtifactContext(Generic[TRef]):
    repo: Repository
    ref: TRef
    branch: str
    relpath: str
```

### Family declaration

```python
@dataclass(frozen=True)
class ArtifactFamily(Generic[TRef, TDoc]):
    name: str
    doc_type: type[TDoc]
    resolve_ref: Callable[[Repository, TRef], ResolvedArtifact]
    normalize_for_write: Callable[[ArtifactContext[TRef], TDoc, "ArtifactStore"], TDoc] | None = None
    validate_for_write: Callable[[ArtifactContext[TRef], TDoc, "ArtifactStore"], None] | None = None
    scan_type: type[msgspec.Struct] | None = None
```

### Store

```python
class ArtifactStore:
    def __init__(self, repo: Repository) -> None: ...

    def load(
        self,
        family: ArtifactFamily[TRef, TDoc],
        ref: TRef,
        *,
        commit: str | None = None,
    ) -> TDoc | None: ...

    def require(
        self,
        family: ArtifactFamily[TRef, TDoc],
        ref: TRef,
        *,
        commit: str | None = None,
    ) -> TDoc: ...

    def save(
        self,
        family: ArtifactFamily[TRef, TDoc],
        ref: TRef,
        doc: TDoc,
        *,
        message: str,
        branch: str | None = None,
    ) -> str: ...

    def delete(
        self,
        family: ArtifactFamily[TRef, object],
        ref: TRef,
        *,
        message: str,
        branch: str | None = None,
    ) -> str: ...

    def list(
        self,
        family: ArtifactFamily[TRef, TDoc],
        *,
        branch: str | None = None,
        commit: str | None = None,
    ) -> list[TRef]: ...

    def transact(
        self,
        *,
        message: str,
        branch: str | None = None,
    ) -> "ArtifactTransaction": ...
```

### Transaction

```python
class ArtifactTransaction:
    def save(self, family: ArtifactFamily[TRef, TDoc], ref: TRef, doc: TDoc) -> None: ...
    def delete(self, family: ArtifactFamily[TRef, object], ref: TRef) -> None: ...
    def commit(self) -> str: ...
```

### Identity and resolution

```python
@dataclass(frozen=True)
class ClaimIdentity:
    logical_ids: tuple[ClaimLogicalIdDocument, ...]
    artifact_id: str
    version_id: str
    source_local_id: str | None


class ClaimIdentityPolicy:
    def normalize(self, claim: SourceClaimDocument, *, source_uri: str, source_namespace: str) -> SourceClaimDocument: ...


class ConceptIdentityPolicy:
    def normalize_canonical(self, payload: Mapping[str, Any], *, local_seed: str, primary_namespace: str) -> ConceptDocument: ...


class ReferenceResolver:
    def resolve_source_claim(self, source: SourceRef, ref: str) -> str: ...
    def resolve_primary_claim_logical_id(self, logical_id: str) -> str | None: ...
    def resolve_claim_any(self, source: SourceRef, ref: str) -> str: ...
```

## Initial Artifact Families

Phase 1 families:

- source singleton docs
  - `source.yaml`
  - `concepts.yaml`
  - `claims.yaml`
  - `justifications.yaml`
  - `stances.yaml`
  - `merge/finalize/{slug}.yaml`

Phase 2 families:

- worldlines
  - `worldlines/{name}.yaml`

Phase 3 families:

- alignment artifacts
  - `proposal/concepts:merge/concepts/{slug}.yaml`

Phase 4 families:

- canonical concepts
  - `concepts/{handle}.yaml`
- canonical claims
  - `claims/{handle}.yaml` or claim file family as appropriate

## Exact Workstream

### Phase 0: Freeze the target

Add:

- [plans/artifact-store-workstream-2026-04-13.md](/C:/Users/Q/code/propstore/plans/artifact-store-workstream-2026-04-13.md)

No production changes yet.

Output:

- final API sketch
- family list
- grep-based completion criteria

### Phase 1: Foundation

Add:

- `propstore/artifacts/__init__.py`
- `propstore/artifacts/codecs.py`
- `propstore/artifacts/refs.py`
- `propstore/artifacts/types.py`
- `propstore/artifacts/families.py`
- `propstore/artifacts/store.py`
- `propstore/artifacts/transaction.py`

Modify:

- [document_schema.py](/C:/Users/Q/code/propstore/propstore/document_schema.py)
  - keep strict decode boundary
  - reuse from artifact codecs rather than duplicating error logic

Tests to add:

- `tests/test_artifact_store_roundtrip.py`
- `tests/test_artifact_store_transactions.py`

Completion criteria:

- store can load/save/delete a synthetic typed artifact family
- transaction can atomically write multiple paths
- no production caller is migrated yet
- the foundation stays minimal until the first real family cutover

### Phase 2: Source singleton artifact migration

Add:

- concrete source families in `propstore/artifacts/families.py`

Modify:

- [source/common.py](/C:/Users/Q/code/propstore/propstore/source/common.py)
- [source/concepts.py](/C:/Users/Q/code/propstore/propstore/source/concepts.py)
- [source/claims.py](/C:/Users/Q/code/propstore/propstore/source/claims.py)
- [source/relations.py](/C:/Users/Q/code/propstore/propstore/source/relations.py)
- [source/finalize.py](/C:/Users/Q/code/propstore/propstore/source/finalize.py)

Delete from callers:

- direct `yaml.safe_dump(...).encode("utf-8")`
- direct `repo.git.commit_batch(...)` for these families
- bespoke `load_source_*_document(...)` helpers as the primary path

Tests to add/update:

- `tests/test_source_artifact_store.py`
- existing source CLI tests to assert behavior is unchanged

Completion criteria:

- all source singleton YAML writes go through `ArtifactStore`
- source modules no longer import `yaml`
- old source persistence paths for migrated families are deleted in the same slice

### Phase 3: Identity cutover

Add:

- `propstore/artifacts/identity.py`

Modify:

- [source/claims.py](/C:/Users/Q/code/propstore/propstore/source/claims.py)
- [source/promote.py](/C:/Users/Q/code/propstore/propstore/source/promote.py)
- [repo/repo_import.py](/C:/Users/Q/code/propstore/propstore/repo/repo_import.py)
- [cli/concept.py](/C:/Users/Q/code/propstore/propstore/cli/concept.py)
- [core/concepts.py](/C:/Users/Q/code/propstore/propstore/core/concepts.py)
- possibly [source/alignment.py](/C:/Users/Q/code/propstore/propstore/source/alignment.py)

Delete from callers:

- direct concept/claim `artifact_id` assembly
- direct concept/claim `version_id` assembly
- direct `logical_ids` construction outside policy layer

Tests to add:

- `tests/test_artifact_identity_policy.py`

Completion criteria:

- all concept/claim identity generation is policy-owned
- repeated normalization is stable
- caller-local identity assembly is deleted as each policy-backed path lands

### Phase 4: Reference-resolution cutover

Add:

- `propstore/artifacts/indexes.py`
- `propstore/artifacts/resolution.py`

Modify:

- [source/relations.py](/C:/Users/Q/code/propstore/propstore/source/relations.py)
- [source/promote.py](/C:/Users/Q/code/propstore/propstore/source/promote.py)
- [source/finalize.py](/C:/Users/Q/code/propstore/propstore/source/finalize.py)
- [repo/repo_import.py](/C:/Users/Q/code/propstore/propstore/repo/repo_import.py)

Delete from callers:

- ad hoc `local_to_artifact`
- ad hoc `logical_to_artifact`
- ad hoc primary-branch lookup maps

Tests to add:

- `tests/test_artifact_reference_resolver.py`

Completion criteria:

- one resolver layer owns source-local and logical-id resolution
- ambiguity hard-fails with explicit errors
- old per-module resolution maps are deleted rather than left behind as fallback

### Phase 5: Worldline migration

Add:

- `WorldlineRef` family support

Modify:

- [worldline/definition.py](/C:/Users/Q/code/propstore/propstore/worldline/definition.py)
- [cli/worldline_cmds.py](/C:/Users/Q/code/propstore/propstore/cli/worldline_cmds.py)

Delete from callers:

- handwritten worldline YAML save/load path

Tests to add/update:

- `tests/test_worldline_artifact_store.py`
- existing worldline tests

Completion criteria:

- worldline persistence is store-backed
- CLI worldline commands no longer import `yaml`
- old worldline YAML persistence code is deleted in the same cutover

### Phase 6: Alignment and promotion artifact migration

Modify:

- [source/alignment.py](/C:/Users/Q/code/propstore/propstore/source/alignment.py)
- [source/promote.py](/C:/Users/Q/code/propstore/propstore/source/promote.py)
- [repo/merge_commit.py](/C:/Users/Q/code/propstore/propstore/repo/merge_commit.py) if artifact writes are still manual there

Completion criteria:

- alignment and promotion paths use family specs plus transactions
- multi-file promotion writes are atomic through `ArtifactTransaction`

### Phase 7: CLI cleanup

Modify:

- [cli/__init__.py](/C:/Users/Q/code/propstore/propstore/cli/__init__.py)
- [cli/repo_import_cmd.py](/C:/Users/Q/code/propstore/propstore/cli/repo_import_cmd.py)
- [cli/merge_cmds.py](/C:/Users/Q/code/propstore/propstore/cli/merge_cmds.py)
- [cli/context.py](/C:/Users/Q/code/propstore/propstore/cli/context.py)
- [cli/form.py](/C:/Users/Q/code/propstore/propstore/cli/form.py)
- [cli/concept.py](/C:/Users/Q/code/propstore/propstore/cli/concept.py)

Goal:

- CLI code should orchestrate store/policy/resolver calls
- not manipulate repo/YAML directly

### Phase 8: Optional runtime codec cleanup

Only do this if the prior phases expose a clear remaining win.

Targets:

- [worldline/definition.py](/C:/Users/Q/code/propstore/propstore/worldline/definition.py)
- [worldline/result_types.py](/C:/Users/Q/code/propstore/propstore/worldline/result_types.py)
- [revision/snapshot_types.py](/C:/Users/Q/code/propstore/propstore/revision/snapshot_types.py)
- [core/row_types.py](/C:/Users/Q/code/propstore/propstore/core/row_types.py)

This is explicitly secondary. Do not widen scope before the persistence cutover
is complete.

## Completion Criteria

Hard criteria:

- only `propstore/artifacts/codecs.py` imports `yaml` in production code
- only the artifact store/transaction layer performs repo artifact writes
- only the artifact store/codecs layer directly decodes repo artifact YAML
- no production caller outside identity policy computes concept/claim identity fields
- no production caller outside resolver builds ad hoc local/logical lookup maps
- source and worldline persistence paths are store-backed
- old per-module persistence code is deleted rather than wrapped

Suggested grep checks:

- `rg -l "^import yaml$|^from yaml import" propstore`
- `rg -n "commit_batch\\(|commit_files\\(" propstore`
- `rg -n "decode_document_path\\(|decode_document_bytes\\(" propstore`
- `rg -n "derive_.*artifact_id|compute_.*version_id|logical_ids" propstore`
- `rg -n "local_to_artifact|logical_to_artifact" propstore`

The output counts should shrink toward:

- one production `yaml` importer
- store-owned artifact writes only
- resolver-owned reference-map logic only

## Test Matrix

Shared suites:

- `tests/test_artifact_store_roundtrip.py`
- `tests/test_artifact_store_transactions.py`
- `tests/test_artifact_identity_policy.py`
- `tests/test_artifact_reference_resolver.py`
- `tests/test_artifact_family_specs.py`

Behavior suites to keep green:

- source CLI tests
- worldline tests
- promotion/finalize tests
- repo import tests

Per project rule:

- run `uv run pytest -vv`
- tee full output to timestamped logs under `logs/test-runs/`

## Primary Failure Modes

- building a generic store that still leaves normalization in callers
- building family specs that still require raw git/YAML in callers
- preserving old and new persistence paths in parallel
- widening into runtime codec cleanup before the artifact boundary is finished

## The Bar For Success

The workstream is successful only if:

- callers stop thinking in terms of branch/path/YAML/git
- callers think in terms of typed artifact refs and typed documents
- identity and reference rules live in one place each
- the diff shows deletion pressure, not abstraction accumulation
- each migrated family ends with a single production path
