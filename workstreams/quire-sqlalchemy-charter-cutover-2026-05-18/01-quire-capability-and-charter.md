# Quire SQLAlchemy Capability And Charter Workstream

Date: 2026-05-18

## Goal

Prove SQLAlchemy can support the Quire-owned charter/schema architecture, then
introduce the Quire generic charter and schema IR that later engine work
consumes.

The end state for this workstream is:

- Quire has SQLAlchemy declared as a normal published dependency.
- Quire has proof tests for imperative mapping, reserved field names,
  relationships, association objects, enum storage, generic JSON value object
  storage, and read-only derived-store sessions.
- Quire has a generic charter/schema IR that composes with existing Quire
  artifact-family, document-store, placement, and reference/FK APIs.
- Propstore is pinned to a pushed Quire commit before Propstore consumes the
  new Quire APIs.

## Repository

- Quire implementation repository: `C:\Users\Q\code\quire`
- Propstore dependency-pin repository: `C:\Users\Q\code\propstore`

## Sources To Read First

- `C:\Users\Q\code\propstore\workstreams\quire-sqlalchemy-charter-cutover-workstream-2026-05-18.md`
- `C:\Users\Q\code\propstore\notes\architecture-wanted-outcome-2026-05-17.md`
- `C:\Users\Q\code\propstore\reports\code-inventory-2026-05-17.md`
- Quire source around `families.py`, `family_store.py`, `artifacts.py`,
  `references.py`, `derived_store.py`, `derived_runtime.py`,
  `projections.py`, and `projection_mapping.py`
- SQLAlchemy 2.1 documentation for dataclass mapping, imperative mapping,
  relationship mapping, and the association object pattern

## Prerequisites

Required phase file prerequisites: `00-index.md`, `inventory-matrix.md`,
`helper-ledger.md`.

- Confirm the Quire and Propstore worktree states before editing.
- Confirm `reports/code-inventory-2026-05-17.md` is still present and is the
  controlling inventory.
- Confirm `notes/architecture-wanted-outcome-2026-05-17.md` still assigns the
  generic charter/schema/SQLAlchemy derived-store machinery to Quire.
- Inspect the parsed Propstore `pyproject.toml` dependency and
  `[tool.uv.sources]` entries before editing dependency metadata.
- A local path, workspace, or file URL dependency on Quire is a hard blocker
  until Quire has been pushed and Propstore is pinned to a pushed branch commit
  or immutable pushed commit SHA.

Required starting searches in Propstore:

```powershell
rg -n -F -- "quire" pyproject.toml uv.lock
rg -n -F -- "[tool.uv.sources]" pyproject.toml
rg -n -F -- "path =" pyproject.toml
rg -n -F -- "workspace = true" pyproject.toml
rg -n -F -- "quire @ file" pyproject.toml uv.lock
rg -n -F -- "quire @ .." pyproject.toml uv.lock
rg -n -F -- "quire @ C:" pyproject.toml uv.lock
```

## Owned Files

Quire:

- `pyproject.toml`
- `uv.lock`
- `quire/charters.py`
- `quire/schema_ir.py`
- `quire/sql_types.py`
- `quire/schema_catalog.py`
- focused Quire tests for SQLAlchemy capability and charter/schema IR behavior

`quire/sqlalchemy_schema.py` and `quire/sqlalchemy_store.py` are created and
owned by `02-quire-sqlalchemy-engine.md`; this workstream defines the charter
IR those implementation files consume.

Propstore:

- `pyproject.toml`
- `uv.lock`

Do not edit Propstore production code in this workstream.

## SQLAlchemy Capability Decision

Do not assume SQLAlchemy can do the required work. Prove it first in Quire.

The expected architecture is:

- SQLAlchemy imperative mappings use `registry.map_imperatively`.
- Quire generates SQLAlchemy `Table` objects from schema IR and maps
  already-defined Python classes to those tables.
- Imperative mapping avoids Declarative class-body reserved-name collisions,
  including a Python field named `metadata` mapped to a SQL column named
  `metadata`.
- SQLAlchemy relationships own one-to-many and many-to-one links.
- SQLAlchemy association objects own join rows with payload columns, including
  `ClaimConceptLink`.
- SQLAlchemy dataclass integration does not support frozen/slots mapped
  entities. Mapped domain objects must be instrumentable. Nested value objects
  stay frozen only when they are explicit non-mapped value objects.
- SQLAlchemy attrs support is imperative-only and is not the foundation for
  this architecture.

If any proof requires handwritten row dictionaries or field-specific coercer
functions, the proof failed. Fix the Quire engine or the SQLAlchemy extension
before touching Propstore production paths.

## Phase 1: Quire SQLAlchemy Capability Proof

Repository: `C:\Users\Q\code\quire`

Add SQLAlchemy as a Quire dependency. Use a normal published dependency in
`pyproject.toml`; do not use a local path.

Create proof tests in Quire before implementation. The tests must prove:

- a plain/dataclass domain class with a Python field named `metadata` maps to a
  SQL column named `metadata`;
- SQLAlchemy `Table` objects are generated from a small schema IR instead of
  writing Declarative class-body mappings by hand;
- mapping is imperative through `registry.map_imperatively`;
- enum fields persist and load without field-specific coercer functions;
- nested JSON value objects persist and load through one generic JSON type
  adapter;
- one-to-many and many-to-one relationships work;
- an association object with payload columns works;
- a read-only SQLAlchemy session opens from a derived-store handle;
- mapped entities are not frozen/slots while nested value objects may be frozen
  when not mapped.

Required proof models:

- `Source` with `metadata`
- `Claim`
- `Concept`
- `ClaimConceptLink` with `role`, `ordinal`, `binding_name`
- `SourceTrust` as a nested JSON value object

Required Quire gates:

```powershell
uv run pyright
uv run pytest -vv
```

After this phase passes, push the Quire branch and pin Propstore to the pushed
Quire commit before editing Propstore. Refresh that pushed pin after every
later Quire phase that changes APIs consumed by Propstore. Never pin Propstore
to a local Quire checkout.

### Phase 1 Execution Record

Recorded 2026-05-20.

- Quire dependency commit: `20d848f Add SQLAlchemy dependency`; `pyproject.toml` declares `sqlalchemy>=2.0` and `uv.lock` resolves `sqlalchemy==2.0.49` from PyPI.
- Quire proof-test commits: `50de55a Add SQLAlchemy capability proof tests`, `b7504a2 Fix proof integer SQL type mapping`, and `2741419 Keep relationship proof assertions bound`.
- Targeted proof gate: `uv run pytest -vv tests/test_sqlalchemy_capability.py` passed with 3 tests.
- Proof coverage: generated SQLAlchemy Core tables from a small IR, imperative `registry.map_imperatively`, `Source.metadata` mapped to SQL column `metadata`, generic enum adapter, generic JSON value-object adapter for frozen `SourceTrust`, one-to-many and many-to-one relationships, `ClaimConceptLink` association object payload fields, and a read-only SQLAlchemy `Session` over a Quire `DerivedStoreHandle` path.

Phase 1 targeted proof is complete. Full Quire gates still run at the workstream completion gate after Phase 2 IR lands.

## Phase 2: Quire Charter/Schema IR

Repository: `C:\Users\Q\code\quire`

Introduce the generic schema declaration layer.

Target files:

- `quire/charters.py`
- `quire/schema_ir.py`
- `quire/sql_types.py`
- `quire/schema_catalog.py`

The charter API must let a consumer define one family/object declaration with:

- Python model class;
- existing Quire `ArtifactFamily` identity;
- document codec/renderer hooks;
- lifecycle/state metadata;
- field definitions and Python types;
- primary keys;
- nullable/non-null fields;
- foreign keys;
- association objects;
- JSON value object fields;
- enum fields;
- generated/default fields;
- indexes and unique constraints;
- search fields;
- vector fields;
- source-local-only fields;
- canonical-only fields;
- semantic metadata supplied by the consumer.

The charter API composes with existing Quire APIs:

- `quire.families.ArtifactFamily` remains the document family identity and
  placement/FK owner;
- `quire.family_store.DocumentFamilyStore` remains the document IO owner;
- `quire.artifacts` remains the placement/addressing owner;
- `quire.references.ForeignKeySpec` remains the source of cross-family
  reference semantics;
- charters add derived-store model/schema/query metadata for those existing
  families and do not create a second registry.

Use SQLAlchemy-native mapping primitives for relational roles:

- primary keys are derived into SQLAlchemy `Column(..., primary_key=True)`;
- FKs are derived from Quire reference specs into SQLAlchemy `ForeignKey`;
- JSON value objects use one Quire SQLAlchemy JSON type decorator;
- relationships and association objects use SQLAlchemy `relationship`;
- search/vector/index metadata is carried through charter field metadata and
  SQLAlchemy `Column.info`.

Do not make callers type SQL column names, SQL types, JSON suffixes, or
per-field codecs when the Python type, Quire reference spec, and SQLAlchemy
mapping metadata determine them. Do not introduce a parallel `PrimaryKey[T]`,
`ForeignKey[T]`, `Json[T]`, `Relation[T]`, or similar marker type family.

The IR must be serializable into a stable schema catalog payload and hash.
That hash participates in derived-store cache identity.

### Phase 2 Execution Record

Recorded 2026-05-20.

- Quire charter/schema IR commits: `af545e0 Add charter schema IR tests`, `87b3a6d Add schema IR objects`, `eaede7e Add Python type SQL mapping`, `9d2bf7a Add schema catalog hashing`, `ada528b Add schema relationship IR`, and `30e23ca Add family charter declarations`.
- Quire type-fix commits needed for the full Phase 2 gate: `34f622d Type-narrow enum SQL mapping`, `57d17f9 Type-tighten charter IR tests`, `c1724c6 Type-tighten SQLAlchemy proof tests`, `d21b879 Type benchmark repo access`, `de7ff76 Type vec identity test double`, `fc38400 Type custom document codec test`, `a8e1e2f Type family tests`, `b805dd8 Type family store tests`, `781d8b2 Accept homogeneous path mappings`, `081d079 Keep GitStore backend protocol compatible`, `e66d6a0 Type document codec constructors`, `485887e Type family store codec constructor`, `76f39c5 Type projection mapping schema material tests`, and `c3e53c5 Type reference key extractors`.
- Charter API coverage: Python model class, existing `ArtifactFamily`, optional `DocumentFamilyStore` binding, lifecycle/state metadata, typed fields, primary keys, nullable fields, `ForeignKeySpec`-derived FKs, association-object and relationship metadata, JSON value-object fields, enum fields, generated/default fields, indexes, search/vector metadata, source-local/canonical scopes, and consumer semantic metadata.
- Existing Quire ownership preserved: `ArtifactFamily` remains family identity, document stores remain document IO, placement/addressing remains in `quire.artifacts`, and cross-family references remain through `ForeignKeySpec`.
- Schema catalog: `SchemaCatalog.from_objects(...)` serializes a stable payload and `canonical_json_sha256` hash.
- Quire type gate: `uv run pyright` passed with 0 errors, 0 warnings, 0 informations.
- Quire test gate: `uv run pytest -vv` passed with 355 tests in 304.38s.

Old-path inventory outputs copied from the Phase 2 completion searches:

```text
rg -n -F -- "ProjectionTable" quire tests
tests\test_derived_store.py:38:    ProjectionTable,
tests\test_derived_store.py:389:    pages = ProjectionTable(
tests\test_derived_store.py:432:    table = ProjectionTable(
tests\test_derived_store.py:456:        ProjectionTable(
tests\test_derived_store.py:469:        ProjectionTable(
tests\test_derived_store.py:477:    pages = ProjectionTable(
tests\test_derived_store.py:510:    pages = ProjectionTable(
tests\test_derived_store.py:543:    first = ProjectionTable(
tests\test_derived_store.py:547:    second = ProjectionTable(
tests\test_derived_store.py:561:        pages = ProjectionTable(
tests\test_derived_store.py:575:        notes = ProjectionTable(
tests\test_derived_store.py:629:    pages = ProjectionTable(
tests\test_derived_store.py:675:        pages = ProjectionTable(
tests\test_derived_store.py:710:        pages = ProjectionTable(
tests\test_derived_store.py:734:        ProjectionTable(
tests\test_derived_store.py:750:        pages = ProjectionTable(
tests\test_projection_mapping.py:28:from quire.projections import ProjectionColumn, ProjectionField, ProjectionIndex, ProjectionRow, ProjectionTable, json_decoder, json_encoder
tests\test_projection_mapping.py:430:    core = ProjectionTable(
tests\test_projection_mapping.py:437:    source = ProjectionTable(
tests\test_projection_mapping.py:474:    edge = ProjectionTable(
quire\derived_runtime.py:12:    ProjectionTable,
quire\derived_runtime.py:30:DERIVED_STORE_META_PROJECTION = ProjectionTable(
quire\projections.py:294:class ProjectionTable:
quire\projections.py:734:SemanticProjection: TypeAlias = ProjectionTable | FtsProjection | VecProjection
quire\projections.py:763:            if isinstance(projection, (ProjectionTable, FtsProjection, VecProjection)):
quire\projections.py:797:            if not isinstance(projection, (ProjectionTable, FtsProjection, VecProjection)):
quire\projections.py:838:    if isinstance(projection, ProjectionTable):
quire\projections.py:850:    if isinstance(projection, ProjectionTable):
quire\projection_mapping.py:16:    ProjectionTable,
quire\projection_mapping.py:346:    def child_table(self, parent_table: str) -> ProjectionTable:
quire\projection_mapping.py:350:        return ProjectionTable(
quire\projection_mapping.py:445:    table: ProjectionTable
quire\projection_mapping.py:500:    base_table: ProjectionTable
quire\projection_mapping.py:729:    def projection_tables(self) -> tuple[ProjectionTable, ...]:
quire\projection_mapping.py:756:            ProjectionTable(
quire\__init__.py:78:    ProjectionTable,
quire\__init__.py:232:    "ProjectionTable",
quire\sqlite_vec_store.py:7:from quire.projections import ProjectionColumn, ProjectionIndex, ProjectionTable, VecProjection, quote_identifier
quire\sqlite_vec_store.py:46:    status_projection: ProjectionTable
quire\sqlite_vec_store.py:74:EMBEDDING_MODEL_PROJECTION = ProjectionTable(
quire\sqlite_vec_store.py:94:) -> ProjectionTable:
quire\sqlite_vec_store.py:95:    return ProjectionTable(

rg -n -F -- "ProjectionModel" quire tests
tests\test_projection_mapping.py:21:    ProjectionModel,
tests\test_projection_mapping.py:122:    model = ProjectionModel(
tests\test_projection_mapping.py:136:    model = ProjectionModel(
tests\test_projection_mapping.py:153:    model = ProjectionModel(
tests\test_projection_mapping.py:166:    model = ProjectionModel(
tests\test_projection_mapping.py:180:    model = ProjectionModel(
tests\test_projection_mapping.py:218:    model = ProjectionModel(
tests\test_projection_mapping.py:308:    model = ProjectionModel(
tests\test_projection_mapping.py:329:    model = ProjectionModel(
tests\test_projection_mapping.py:372:    model = ProjectionModel(
tests\test_projection_mapping.py:384:    model = ProjectionModel(
tests\test_projection_mapping.py:411:    model = ProjectionModel(
tests\test_projection_mapping.py:520:    model = ProjectionModel(
tests\test_projection_mapping.py:545:    model = ProjectionModel(
tests\test_projection_mapping.py:560:    first = ProjectionModel(
tests\test_projection_mapping.py:566:    second = ProjectionModel(
tests\test_projection_mapping.py:577:    first = ProjectionModel(
tests\test_projection_mapping.py:583:    second = ProjectionModel(
tests\test_projection_mapping.py:594:    flat = ProjectionModel(
tests\test_projection_mapping.py:600:    reference = ProjectionModel(
tests\test_projection_mapping.py:612:    model = ProjectionModel(
tests\test_projection_mapping.py:642:    model = ProjectionModel(
tests\test_projection_mapping.py:687:    model = ProjectionModel(
tests\test_projection_mapping.py:750:    model = ProjectionModel(
tests\test_projection_mapping.py:781:def _parent_model() -> ProjectionModel:
tests\test_projection_mapping.py:782:    return ProjectionModel(
quire\projection_mapping.py:553:class ProjectionModel(Generic[ResultT]):
quire\__init__.py:107:    ProjectionModel,
quire\__init__.py:225:    "ProjectionModel",

rg -n -F -- "ProjectionCodec" quire tests
tests\test_projection_mapping.py:15:    ProjectionCodec,
tests\test_projection_mapping.py:641:    real_codec = ProjectionCodec("real", "REAL")
tests\test_projection_mapping.py:686:    id_codec = ProjectionCodec("auto_id", "INTEGER PRIMARY KEY AUTOINCREMENT")
quire\projection_mapping.py:28:class ProjectionCodec:
quire\projection_mapping.py:48:SCALAR_CODEC = ProjectionCodec()
quire\projection_mapping.py:49:JSON_CODEC = ProjectionCodec("json", "TEXT", json_encoder, json_decoder)
quire\projection_mapping.py:111:    codec: ProjectionCodec = SCALAR_CODEC
quire\projection_mapping.py:163:    codec: ProjectionCodec = JSON_CODEC
quire\projection_mapping.py:212:    codec: ProjectionCodec = SCALAR_CODEC
quire\__init__.py:101:    ProjectionCodec,
quire\__init__.py:214:    "ProjectionCodec",

rg -n -F -- "ScalarPath" quire tests
tests\test_projection_mapping.py:26:    ScalarPath,
tests\test_projection_mapping.py:126:        fields=(ScalarPath(("id",), "id"), ScalarPath(("title",), "title"),),
tests\test_projection_mapping.py:141:            ScalarPath(("id",), "id"),
tests\test_projection_mapping.py:142:            ScalarPath(("source", "origin", "type"), "source_origin_type"),
tests\test_projection_mapping.py:157:        fields=(ScalarPath(("id",), "id"), EnumPath(("status",), "status", enum=Status),),
tests\test_projection_mapping.py:170:        fields=(ScalarPath(("id",), "id"), JsonPath(("payload",), "payload_json"),),
tests\test_projection_mapping.py:184:        fields=(ScalarPath(("id",), "id"), ScalarPath(("note",), "note"),),
tests\test_projection_mapping.py:223:            ScalarPath(("id",), "id"),
tests\test_projection_mapping.py:230:                fields=(ScalarPath(("concept_id",), "concept_id"), ScalarPath(("role",), "role")),
tests\test_projection_mapping.py:313:            ScalarPath(("id",), "id"),
tests\test_projection_mapping.py:334:            ScalarPath(("id",), "id"),
tests\test_projection_mapping.py:376:        fields=(ScalarPath(("id",), "id"),),
tests\test_projection_mapping.py:389:            ScalarPath(("id",), "id"),
tests\test_projection_mapping.py:392:                fields=(ScalarPath(("confidence",), "confidence"),),
tests\test_projection_mapping.py:416:            ScalarPath(("id",), "id"),
tests\test_projection_mapping.py:525:            ScalarPath(("id",), "id"),
tests\test_projection_mapping.py:526:            ScalarPath(("title",), "title"),
tests\test_projection_mapping.py:549:        fields=(ScalarPath(("id",), "id"), ScalarPath(("title",), "title"),),
tests\test_projection_mapping.py:564:        fields=(ScalarPath(("id",), "id"),),
tests\test_projection_mapping.py:570:        fields=(ScalarPath(("identifier",), "id"),),
tests\test_projection_mapping.py:581:        fields=(ScalarPath(("id",), "id"), ScalarPath(("title",), "title"),),
tests\test_projection_mapping.py:587:        fields=(ScalarPath(("title",), "title"), ScalarPath(("id",), "id"),),
tests\test_projection_mapping.py:598:        fields=(ScalarPath(("id",), "id"),),
tests\test_projection_mapping.py:604:        fields=(ScalarPath(("id",), "id"), ReferencePath(("context_id",), "context_id", family="context")),
tests\test_projection_mapping.py:617:            ScalarPath(("source_id",), "source_id"),
tests\test_projection_mapping.py:618:            ScalarPath(("target_id",), "target_id"),
tests\test_projection_mapping.py:620:            ScalarPath(("note",), "note"),
tests\test_projection_mapping.py:647:            ScalarPath(
tests\test_projection_mapping.py:653:            ScalarPath(("target_id",), "target_id", nullable=False),
tests\test_projection_mapping.py:654:            ScalarPath(("relation_type",), "relation_type", nullable=False),
tests\test_projection_mapping.py:655:            ScalarPath(
tests\test_projection_mapping.py:692:            ScalarPath(("id",), "id", codec=id_codec, insertable=False),
tests\test_projection_mapping.py:693:            ScalarPath(("title",), "title"),
tests\test_projection_mapping.py:755:            ScalarPath(("id",), "id"),
tests\test_projection_mapping.py:787:            ScalarPath(("id",), "id"),
tests\test_projection_mapping.py:795:                fields=(ScalarPath(("concept_id",), "concept_id"), ScalarPath(("role",), "role")),
quire\projection_mapping.py:108:class ScalarPath:
quire\projection_mapping.py:162:class JsonPath(ScalarPath):
quire\projection_mapping.py:167:class EnumPath(ScalarPath):
quire\projection_mapping.py:194:class ReferencePath(ScalarPath):
quire\projection_mapping.py:249:ProjectionPath = ScalarPath | JsonPath | EnumPath | ReferencePath | ProjectionBinding
quire\projection_mapping.py:753:            if isinstance(field, ScalarPath) and field.indexed
quire\projection_mapping.py:833:        elif isinstance(field, ScalarPath | ProjectionBinding) and field.path == path:
quire\__init__.py:112:    ScalarPath,
quire\__init__.py:245:    "ScalarPath",

rg -n -F -- "ReferencePath" quire tests
tests\test_projection_mapping.py:25:    ReferencePath,
tests\test_projection_mapping.py:314:            ReferencePath(("context_id",), "context_id", family="context"),
tests\test_projection_mapping.py:604:        fields=(ScalarPath(("id",), "id"), ReferencePath(("context_id",), "context_id", family="context")),
quire\projection_mapping.py:194:class ReferencePath(ScalarPath):
quire\projection_mapping.py:249:ProjectionPath = ScalarPath | JsonPath | EnumPath | ReferencePath | ProjectionBinding
quire\projection_mapping.py:748:            if isinstance(field, ReferencePath)
quire\__init__.py:111:    ReferencePath,
quire\__init__.py:234:    "ReferencePath",
```

Phase 2 Quire gates are complete. Propstore dependency pin update is blocked by the required Quire push.

Push blocker recorded 2026-05-20:

- Current Quire branch: `master`.
- Required operation: push Quire changes before pinning Propstore to a Quire commit.
- Blocking state: `master` is ahead of `origin/master` by 29 commits, and five commits in `origin/master..HEAD` predate this workstream execution: `440c0f5 Add Hypothesis property tests for iter_* laziness contract`, `6955e68 Dedup _source_label helper between documents/schema and documents/batch`, `b3c0ffd Rewrite test_transaction_head_check_is_named_as_advisory as behavior test`, `61b145e Use hypothesis.assume in test_family_reference_index_rejects_generated_duplicate_aliases`, and `b35f9fc Add VersionId NotImplemented contract tests`.
- I did not create those five commits in this execution, and pushing `master` would publish them along with the SQLAlchemy charter commits. Shared worktree etiquette blocks that push without explicit user direction for the preexisting ahead commits.
- Because the Quire push is blocked, Propstore dependency pinning and the Propstore Phase 2 gates have not run.

Push blocker resolved 2026-05-20:

- User explicitly authorized pushing the Quire ahead commits.
- Quire push: `git push origin master` succeeded, updating `origin/master` from `1343248` to `c3e53c5`.
- Pushed Quire commit pinned by Propstore: `c3e53c5c2be0492cc953d44dfa36d03765a447f4`.
- Propstore pin commit: `0e666050 Pin Propstore to pushed Quire charter commit`; `pyproject.toml` and `uv.lock` both resolve Quire from `https://github.com/ctoth/quire` at `c3e53c5c2be0492cc953d44dfa36d03765a447f4`, never from a local checkout.
- Propstore type gate: `uv run pyright propstore` passed with 0 errors, 0 warnings, 0 informations.
- Dependency string gates: `quire @ file`, `quire @ ..`, `quire @ C:`, `path =`, and `workspace = true` returned no hits; `[tool.uv.sources]` is present.
- Parsed dependency verification: `uv lock --check` resolved 159 packages; `uv tree --package quire` resolved Quire `v0.2.0` with `sqlalchemy v2.0.49` from the pushed Git package.

Phase 1-2 is complete. Phase 3 may start.

## Completion Gates

Run from `C:\Users\Q\code\quire`:

```powershell
uv run pyright
uv run pytest -vv
rg -n -F -- "ProjectionTable" quire tests
rg -n -F -- "ProjectionModel" quire tests
rg -n -F -- "ProjectionCodec" quire tests
rg -n -F -- "ScalarPath" quire tests
rg -n -F -- "ReferencePath" quire tests
```

The old-path searches are inventory gates for this workstream. They must be
copied into the workstream report. Production code introduced by this
workstream must not import or depend on those old projection primitives.

Run from `C:\Users\Q\code\propstore` after the Quire branch is pushed and the
Propstore dependency pin is updated:

```powershell
uv run pyright propstore
rg -n -F -- "quire @ file" pyproject.toml uv.lock
rg -n -F -- "quire @ .." pyproject.toml uv.lock
rg -n -F -- "quire @ C:" pyproject.toml uv.lock
rg -n -F -- "[tool.uv.sources]" pyproject.toml
rg -n -F -- "path =" pyproject.toml
rg -n -F -- "workspace = true" pyproject.toml
```

The dependency gate must inspect parsed `pyproject.toml` source tables. A
Quire dependency entry that resolves only from the local filesystem fails the
gate even when string searches miss it.

This workstream is complete only when:

- SQLAlchemy is declared from a published package source in Quire.
- The required proof tests demonstrate the exact SQLAlchemy behavior needed by
  the architecture.
- Quire has the generic charter/schema IR.
- Quire charters compose with existing `ArtifactFamily`,
  `DocumentFamilyStore`, `artifacts`, and `ForeignKeySpec` APIs.
- The schema IR serializes into a stable catalog payload and hash.
- Quire type and test gates pass.
- Propstore is pinned to a pushed Quire commit, never a local checkout.
