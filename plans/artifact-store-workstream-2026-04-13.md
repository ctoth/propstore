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
- Callers should not derive refs from repo paths or filenames for persisted artifacts.
- Callers should not call artifact codecs directly for dry-run or display output.
- Artifact moves and renames should be store-backed operations, not caller-built add/delete batches.
- No dual old/new persistence paths in steady state.
- No compatibility shims unless an external constraint explicitly requires one.

## Plan Correction

The first store cut landed a boundary that was still too low-level.

It proved that typed load/save/delete and family specs are useful, but it also
exposed the missing ownership:

- callers were still deriving refs from source paths
- callers were still rendering YAML for display
- caller code still had to think about path-level rename mechanics
- caller code was still converting loose payloads into typed artifact docs

That is not the target architecture.

The corrected target is:

- the store owns repo-artifact path, branch, and commit addressing
- the store owns artifact rendering for human display
- the store and transaction layers own artifact moves and renames
- family specs expose first-class helpers for locating refs from loaded domain objects
- CLI code orchestrates typed operations and validation only

Pause further family cutovers until that higher store boundary exists.

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
  - typed artifact resolution and rendering
  - typed artifact move/rename helpers

- `transaction.py`
  - atomic multi-artifact writes/deletes/moves

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


@dataclass(frozen=True)
class ArtifactHandle(Generic[TRef, TDoc]):
    family: ArtifactFamily[TRef, TDoc]
    ref: TRef
    resolved: ResolvedArtifact
    document: TDoc
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
    ref_from_path: Callable[[str], TRef] | None = None
    ref_from_loaded: Callable[[object], TRef] | None = None
    scan_type: type[msgspec.Struct] | None = None
```

### Store

```python
class ArtifactStore:
    def __init__(self, repo: Repository) -> None: ...

    def resolve(
        self,
        family: ArtifactFamily[TRef, TDoc],
        ref: TRef,
        *,
        commit: str | None = None,
    ) -> ResolvedArtifact: ...

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

    def handle(
        self,
        family: ArtifactFamily[TRef, TDoc],
        ref: TRef,
        *,
        commit: str | None = None,
    ) -> ArtifactHandle[TRef, TDoc] | None: ...

    def require_handle(
        self,
        family: ArtifactFamily[TRef, TDoc],
        ref: TRef,
        *,
        commit: str | None = None,
    ) -> ArtifactHandle[TRef, TDoc]: ...

    def render(self, document: object) -> str: ...

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

    def move(
        self,
        family: ArtifactFamily[TRef, TDoc],
        old_ref: TRef,
        new_ref: TRef,
        doc: TDoc,
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
    def move(self, family: ArtifactFamily[TRef, TDoc], old_ref: TRef, new_ref: TRef, doc: TDoc) -> None: ...
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

## Corrected Workstream

Current kept state in git:

- source singleton artifact cutover
- `context` and `form` cutover
- worldline persistence cutover
- alignment and promotion artifact cutover
- typed claim reference resolution extraction

Those reductions stay kept unless the raised store boundary proves one of them
still leaks path/render mechanics upward enough to justify a focused repair.

### Phase 0: Freeze the corrected target

Add:

- [plans/artifact-store-workstream-2026-04-13.md](/C:/Users/Q/code/propstore/plans/artifact-store-workstream-2026-04-13.md)

Output:

- final API sketch
- family list
- grep-based completion criteria

### Phase 1: Raise the store boundary

Add:

- `ArtifactHandle`
- store-level render support
- store and transaction move support
- family-level ref derivation helpers where needed

Modify:

- [artifacts/store.py](/C:/Users/Q/code/propstore/propstore/artifacts/store.py)
- [artifacts/transaction.py](/C:/Users/Q/code/propstore/propstore/artifacts/transaction.py)
- [artifacts/families.py](/C:/Users/Q/code/propstore/propstore/artifacts/families.py)
- [artifacts/types.py](/C:/Users/Q/code/propstore/propstore/artifacts/types.py)
- [artifacts/codecs.py](/C:/Users/Q/code/propstore/propstore/artifacts/codecs.py)

Tests to add:

- store render tests
- store move/rename tests
- handle/ref-derivation tests

Completion criteria:

- callers no longer need codec imports for dry-run or display output
- callers no longer need to derive artifact refs from repo-relative paths
- callers can rename or move artifacts without building raw add/delete batches
- the boundary is high enough that the next family cutover removes helper code rather than relocating it

### Phase 2: Repair the in-flight concept cutover

Modify:

- [cli/concept.py](/C:/Users/Q/code/propstore/propstore/cli/concept.py)

Delete from callers:

- direct artifact rendering through codec helpers
- ref derivation from `source_path` or filenames where the family/store can own it
- path-level rename batching for concept artifact mutations

Tests to add/update:

- concept CLI mutation tests
- artifact move/render tests exercised through concept commands

Completion criteria:

- `cli/concept.py` does not import artifact codecs
- `cli/concept.py` does not convert repo-relative paths into concept refs
- `concept add`, `alias`, and `rename` use store and transaction APIs cleanly
- the unfinished partial concept slice is either completed cleanly or fully reverted

### Phase 3: Continue exact family cutovers

Proceed one target family at a time only after Phase 2 is cleanly kept.

Recommended order:

1. canonical concept / claims CLI mutations
2. repo import and merge materialization
3. any remaining output-only CLI YAML surfaces

Each slice must:

- use the corrected high store boundary
- delete the old production path in the same change
- stop widening if the boundary starts leaking path/render mechanics back upward

### Phase 4: Identity cutover

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

### Phase 5: Reference-resolution cutover

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

### Phase 6: Audit completed worldline cutover

Modify:

- [worldline/definition.py](/C:/Users/Q/code/propstore/propstore/worldline/definition.py)
- [cli/worldline_cmds.py](/C:/Users/Q/code/propstore/propstore/cli/worldline_cmds.py)

Tests to add/update:

- `tests/test_worldline_artifact_store.py`
- existing worldline tests

Completion criteria:

- worldline persistence remains store-backed
- worldline callers do not need codec imports or path-derived refs
- no worldline rename/display path leaks remain after the raised-boundary audit

### Phase 7: Audit completed alignment and promotion cutovers

Modify:

- [source/alignment.py](/C:/Users/Q/code/propstore/propstore/source/alignment.py)
- [source/promote.py](/C:/Users/Q/code/propstore/propstore/source/promote.py)
- [repo/merge_commit.py](/C:/Users/Q/code/propstore/propstore/repo/merge_commit.py) if artifact writes are still manual there

Completion criteria:

- alignment and promotion paths use family specs plus transactions
- multi-file promotion writes are atomic through `ArtifactTransaction`
- callers are not reconstructing refs or rendering YAML themselves

### Phase 8: Remaining CLI cleanup

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

### Phase 9: Optional runtime codec cleanup

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

## Baseline And Projection

Measured on 2026-04-13 after the first source-singleton cutover.

### Baseline counts

- production `yaml` importers in `propstore/`: `17`
- non-foundation git write callsites
  - `rg -n "commit_batch\\(|commit_files\\(" propstore | rg -v "propstore\\\\artifacts\\\\|propstore\\\\repo\\\\git_backend.py"`
  - current count: `19`
- decode callsites outside `document_schema.py` and `artifacts/codecs.py`:
  - current count: `18`
- ad hoc source/reference-map sites
  - `rg -n "local_to_artifact|logical_to_artifact|primary_logical_to_artifact" propstore | rg -v "propstore\\\\identity.py|propstore\\\\repo\\\\merge_classifier.py"`
  - current count: `47`

### End-state target for this workstream

This workstream should be able to reduce those surfaces to:

- production `yaml` importers: `5`
- non-foundation git write callsites: `1`
- decode callsites outside `document_schema.py` and `artifacts/codecs.py`: `12`
- ad hoc source/reference-map sites: `12`

### Why those targets are realistic

#### `yaml` importers: `17 -> 5`

The planned removals are:

- [cli/form.py](/C:/Users/Q/code/propstore/propstore/cli/form.py)
- [cli/context.py](/C:/Users/Q/code/propstore/propstore/cli/context.py)
- [cli/concept.py](/C:/Users/Q/code/propstore/propstore/cli/concept.py)
- [cli/worldline_cmds.py](/C:/Users/Q/code/propstore/propstore/cli/worldline_cmds.py)
- [cli/repository.py](/C:/Users/Q/code/propstore/propstore/cli/repository.py)
- [proposals.py](/C:/Users/Q/code/propstore/propstore/proposals.py)
- [repo/merge_commit.py](/C:/Users/Q/code/propstore/propstore/repo/merge_commit.py)
- [repo/repo_import.py](/C:/Users/Q/code/propstore/propstore/repo/repo_import.py)
- [source/promote.py](/C:/Users/Q/code/propstore/propstore/source/promote.py)
- [source/alignment.py](/C:/Users/Q/code/propstore/propstore/source/alignment.py)
- [worldline/definition.py](/C:/Users/Q/code/propstore/propstore/worldline/definition.py)
- [data_utils.py](/C:/Users/Q/code/propstore/propstore/data_utils.py)

The expected remaining `yaml` importers are output-oriented CLI surfaces:

- [cli/__init__.py](/C:/Users/Q/code/propstore/propstore/cli/__init__.py)
- [cli/compiler_cmds.py](/C:/Users/Q/code/propstore/propstore/cli/compiler_cmds.py)
- [cli/merge_cmds.py](/C:/Users/Q/code/propstore/propstore/cli/merge_cmds.py)
- [cli/repo_import_cmd.py](/C:/Users/Q/code/propstore/propstore/cli/repo_import_cmd.py)
- [cli/verify.py](/C:/Users/Q/code/propstore/propstore/cli/verify.py)

That is why the target is `5`, not `0`.

#### non-foundation git write callsites: `19 -> 1`

The current `19` remaining callsites outside `artifacts/` and `repo/git_backend.py`
are concentrated in:

- canonical artifact CLI mutations
- worldline persistence
- proposal persistence
- repo import / merge materialization
- source promotion and alignment
- one raw-byte helper in [source/common.py](/C:/Users/Q/code/propstore/propstore/source/common.py)

The target is to eliminate all of them except the raw-byte helper:

- keep: [source/common.py](/C:/Users/Q/code/propstore/propstore/source/common.py)
  - `commit_source_file(...)` for `notes.md` and `metadata.json`

If we later decide to add a raw-file family, this could become `0`, but the
honest target for the current workstream is `1`.

#### decode callsites outside the shared decode layer: `18 -> 12`

Not every decode site is artifact-store debt. Some are true external-ingress or
filesystem-ingress boundaries that should remain explicit.

The callsites likely removable in this workstream are:

- [source/common.py](/C:/Users/Q/code/propstore/propstore/source/common.py)
- [source/alignment.py](/C:/Users/Q/code/propstore/propstore/source/alignment.py)
- [worldline/definition.py](/C:/Users/Q/code/propstore/propstore/worldline/definition.py)
- [repo/git_backend.py](/C:/Users/Q/code/propstore/propstore/repo/git_backend.py)
- [cli/helpers.py](/C:/Users/Q/code/propstore/propstore/cli/helpers.py)
- one repo-import/path-specific scan path if absorbed into artifact indexes

The callsites expected to remain are true import or filesystem boundaries such
as:

- `source add-* --batch` file ingestion
- form loading
- sidecar/file-based analysis helpers
- artifact-code verification over arbitrary trees

That is why the realistic target is `12`, not `0`.

#### ad hoc source/reference-map sites: `47 -> 12`

The current `47` sites are mostly spread across:

- [source/claims.py](/C:/Users/Q/code/propstore/propstore/source/claims.py)
- [source/relations.py](/C:/Users/Q/code/propstore/propstore/source/relations.py)
- [source/finalize.py](/C:/Users/Q/code/propstore/propstore/source/finalize.py)
- [source/promote.py](/C:/Users/Q/code/propstore/propstore/source/promote.py)
- [repo/repo_import.py](/C:/Users/Q/code/propstore/propstore/repo/repo_import.py)

The target `12` assumes:

- one resolver module
- one index module
- small family-specific adapter seams

It does not assume those concepts disappear entirely. It assumes they stop being
copy-pasted across workflows.

### Expected net cleanup

If the workstream lands as designed, we should remove approximately:

- `12` production `yaml` importers
- `18` non-foundation git write callsites
- `6` repo-artifact decode callsites
- `35` ad hoc source/reference-map sites

That is the practical cleanup budget this design should cash out.

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
