# Quire SQLAlchemy Engine Workstream

Date: 2026-05-18

## Refactor Zen

This workstream succeeds only if the refactor removes duplicate structure and
makes the project smaller, clearer, and more beautiful. Field and schema shape
is written once in Quire charters or in the exact Propstore semantic owner; do
not restate it in helper families, casts, kwargs builders, row DTOs, projection
models, or model-layer normalizers. After an IO boundary has parsed input, the
type system carries meaning: no generic coercion, loose mapping repair, shim,
adapter, alias, compatibility bridge, or old/new dual path is allowed. Delete
the old production surface first; compiler, type, test, and search failures are
the work queue. If a bridge feels necessary, stop and move parsing/validation
to the owning boundary or add the missing Quire generic capability.

## Goal

Build the generic Quire SQLAlchemy engine over the Quire charter/schema IR.

The end state for this workstream is:

- Quire generates SQLAlchemy metadata, tables, mappings, relationships,
  association objects, type adapters, constraints, and indexes from charters.
- Quire writes and validates schema catalog tables and schema hashes.
- Quire derived-store handles open read-only SQLAlchemy sessions and writable
  build sessions.
- Propstore obtains sessions from Quire derived-store handles and does not
  create SQLAlchemy sessions directly or receive raw `sqlite3.Connection`
  objects for charter-backed access.

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
- SQLAlchemy 2.1 documentation for imperative mapping, relationship mapping,
  JSON type decorators, session lifecycle, and the association object pattern

## Prerequisites

- `00-index.md`, `inventory-matrix.md`, and `helper-ledger.md` are complete.
- `01-quire-capability-and-charter.md` is complete.
- Quire SQLAlchemy dependency is declared from a published package source.
- Quire capability proof tests pass for imperative mapping, `metadata` field
  mapping, enum storage, generic JSON value objects, relationships,
  association objects, derived-store read-only sessions, and non-frozen mapped
  entities.
- Quire has `charters.py`, `schema_ir.py`, `sql_types.py`, and
  `schema_catalog.py` with a stable schema catalog payload and hash.
- Propstore is pinned to a pushed Quire branch commit or immutable pushed
  commit SHA before Propstore consumes engine APIs.
- Inspect the parsed Propstore `pyproject.toml` dependency and
  `[tool.uv.sources]` entries before editing dependency metadata.
- A local path, workspace, or file URL dependency on Quire is a hard blocker.

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

- `quire/sqlalchemy_schema.py`
- `quire/sqlalchemy_store.py`
- `quire/schema_catalog.py`
- `quire/sql_types.py`
- `quire/derived_store.py`
- `quire/derived_runtime.py`
- focused Quire tests for generated DDL, generated mappings, sessions, schema
  catalog validation, schema hash behavior, and relationship loading

Propstore:

- `pyproject.toml`
- `uv.lock`

Do not edit Propstore production code in this workstream.

## SQLAlchemy-Native Mapping Decision

The engine uses SQLAlchemy primitives directly:

- generated SQLAlchemy `MetaData`;
- generated SQLAlchemy `Table` objects;
- imperative mappings through `registry.map_imperatively`;
- primary keys as SQLAlchemy `Column(..., primary_key=True)`;
- FKs derived from Quire reference specs into SQLAlchemy `ForeignKey`;
- one Quire SQLAlchemy JSON type decorator for JSON value objects;
- generic enum storage adapters;
- SQLAlchemy `relationship` for relationships and association objects;
- SQLAlchemy indexes and uniqueness constraints;
- charter field metadata and SQLAlchemy `Column.info` for search, vector, and
  semantic metadata consumed by later workstreams.

Do not make callers type SQL column names, SQL types, JSON suffixes, or
per-field codecs when the Python type, Quire reference spec, and SQLAlchemy
mapping metadata determine them. Do not introduce a parallel `PrimaryKey[T]`,
`ForeignKey[T]`, `Json[T]`, `Relation[T]`, or similar marker type family.

## Existing Quire Integration

The engine composes with existing Quire APIs:

- `quire.families.ArtifactFamily` remains the document family identity and
  placement/FK owner.
- `quire.family_store.DocumentFamilyStore` remains the document IO owner.
- `quire.artifacts` remains the placement/addressing owner.
- `quire.references.ForeignKeySpec` remains the source of cross-family
  reference semantics.
- SQLAlchemy FKs are derived from the same Quire reference specs.
- Derived-store lifecycle remains in Quire `derived_store.py`.
- Runtime validation policy remains in Quire `derived_runtime.py`, with
  projection-schema validation replaced by SQLAlchemy catalog validation.

Do not create a parallel family registry, document IO layer, placement layer,
or reference/FK system.

## Phase 3: Quire SQLAlchemy Engine

Repository: `C:\Users\Q\code\quire`

Build the generic SQLAlchemy engine over the charter IR:

- generate SQLAlchemy `MetaData`;
- generate `Table` objects;
- map Python classes imperatively;
- generate relationships;
- generate association object mappings;
- generate generic JSON type decorators;
- generate enum storage adapters;
- generate indexes and uniqueness constraints;
- generate FKs from family references;
- create all tables in a derived SQLite store;
- write schema catalog tables;
- validate opened stores against schema catalog and schema hash;
- expose `DerivedStoreHandle.readonly_session()` and writable build-session
  APIs;
- expose a typed `DerivedSession`/query context API.

Quire owns session lifecycle. Propstore requests sessions from Quire
derived-store handles. Propstore does not create SQLAlchemy sessions directly
and does not receive raw `sqlite3.Connection` objects.

Required proof models carried forward from the capability workstream:

- `Source` with `metadata`
- `Claim`
- `Concept`
- `ClaimConceptLink` with `role`, `ordinal`, `binding_name`
- `SourceTrust` as a nested JSON value object

Required Quire tests:

- generated DDL has expected tables, columns, FKs, and indexes;
- generated mappings can insert, query, update, and delete in a temporary
  SQLite DB;
- read-only sessions reject writes;
- writable build sessions create and populate generated tables;
- schema catalog round-trips and detects missing tables and columns;
- schema hash changes when charter shape changes;
- relationship lazy/selectin loading works for source, claim, concept, and
  claim-concept-link proof models;
- enum and JSON adapters are generic and do not require field-specific coercer
  functions.

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
rg -n -F -- "FtsProjection" quire tests
rg -n -F -- "VecProjection" quire tests
```

Before the later Quire projection-module deletion phase, the search output is
an inventory of remaining old paths, not a passing zero-hit gate. Copy the
output into the phase report. No Propstore cutover may import those old paths.
The later deletion workstream turns these searches into zero-hit gates.

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

- Quire has generated SQLAlchemy tables from charter IR.
- Quire has imperative mappings over existing Python model classes.
- Quire has generated relationships and association object mappings.
- Quire has generic enum conversion and JSON value object conversion.
- Quire has generated FKs from existing family reference specs.
- Quire has schema catalog, hash, and version validation.
- Quire derived-store handles expose read-only runtime sessions.
- Quire exposes writable build-session APIs.
- Quire session lifecycle is owned by Quire derived-store handles.
- Quire type and test gates pass.
- Propstore is pinned to a pushed Quire commit, never a local checkout.

## Phase 3 Execution Record

Recorded 2026-05-20.

Quire commits:

- `b74a015 Add SQLAlchemy engine tests`
- `3b3564c Add SQLAlchemy schema generation`
- `58033ff Add SQLAlchemy store sessions`
- `886bb95 Expose SQLAlchemy sessions on derived handles`
- `1609088 Allow repeated SQLAlchemy schema builds`
- `d969a4e Assert generated foreign key columns`
- `7637b8a Corrupt schema store through session SQL`

Implemented Quire surfaces:

- `quire/sqlalchemy_schema.py` generates SQLAlchemy `MetaData`, `Table` objects, columns, FKs, indexes, generic enum and JSON value-object adapters, imperative mappings, relationships, and association-object mappings from the charter/schema IR.
- `quire/sqlalchemy_store.py` creates SQLite stores, writes the schema catalog table and schema hash, validates opened stores against generated table/column shape and schema hash, and exposes read-only and writable SQLAlchemy session contexts through Quire-owned lifecycle functions.
- `DerivedStoreHandle.readonly_session()` and `DerivedStoreHandle.writable_session()` delegate session opening to Quire SQLAlchemy store APIs.
- `tests/test_sqlalchemy_engine.py` carries the required proof models: `Source` with `metadata`, `Claim`, `Concept`, `ClaimConceptLink` with `role`, `ordinal`, and `binding_name`, plus nested JSON `SourceTrust`.

Focused gate:

```powershell
uv run pytest -vv tests/test_sqlalchemy_engine.py
```

Result: `3 passed in 0.63s`.

Quire completion gates:

```powershell
uv run pyright
```

Result: `0 errors, 0 warnings, 0 informations`.

```powershell
uv run pytest -vv
```

Result: `358 passed in 278.41s (0:04:38)`.

Old-path inventory searches for the later Quire projection-module deletion phase:

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
tests\test_projection_mapping.py:28:from quire.projections import ProjectionColumn, ProjectionField, ProjectionIndex, ProjectionRow, ProjectionTable, json_decoder, json_encoder
tests\test_projection_mapping.py:430:    core = ProjectionTable(
tests\test_projection_mapping.py:437:    source = ProjectionTable(
tests\test_projection_mapping.py:474:    edge = ProjectionTable(
quire\sqlite_vec_store.py:7:from quire.projections import ProjectionColumn, ProjectionIndex, ProjectionTable, VecProjection, quote_identifier
quire\sqlite_vec_store.py:46:    status_projection: ProjectionTable
quire\sqlite_vec_store.py:74:EMBEDDING_MODEL_PROJECTION = ProjectionTable(
quire\sqlite_vec_store.py:94:) -> ProjectionTable:
quire\sqlite_vec_store.py:95:    return ProjectionTable(
quire\__init__.py:78:    ProjectionTable,
quire\__init__.py:232:    "ProjectionTable",

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

rg -n -F -- "FtsProjection" quire tests
tests\test_derived_store.py:32:    FtsProjection,
tests\test_derived_store.py:482:    search = FtsProjection(
tests\test_derived_store.py:518:    search = FtsProjection(
tests\test_derived_store.py:759:        page_search = FtsProjection(
tests\test_derived_store.py:798:        page_search = FtsProjection(
quire\projections.py:476:class FtsProjection:
quire\projections.py:734:SemanticProjection: TypeAlias = ProjectionTable | FtsProjection | VecProjection
quire\projections.py:763:            if isinstance(projection, (ProjectionTable, FtsProjection, VecProjection)):
quire\projections.py:797:            if not isinstance(projection, (ProjectionTable, FtsProjection, VecProjection)):
quire\projections.py:862:    elif isinstance(projection, FtsProjection):
quire\__init__.py:62:    FtsProjection,
quire\__init__.py:192:    "FtsProjection",

rg -n -F -- "VecProjection" quire tests
tests\test_derived_store.py:40:    VecProjection,
tests\test_derived_store.py:488:    vectors = VecProjection(
tests\test_derived_store.py:524:    vectors = VecProjection(
tests\test_derived_store.py:831:        vectors = VecProjection(
quire\projections.py:606:class VecProjection:
quire\projections.py:734:SemanticProjection: TypeAlias = ProjectionTable | FtsProjection | VecProjection
quire\projections.py:763:            if isinstance(projection, (ProjectionTable, FtsProjection, VecProjection)):
quire\projections.py:797:            if not isinstance(projection, (ProjectionTable, FtsProjection, VecProjection)):
quire\sqlite_vec_store.py:7:from quire.projections import ProjectionColumn, ProjectionIndex, ProjectionTable, VecProjection, quote_identifier
quire\sqlite_vec_store.py:48:    vector_projection: VecProjection
quire\sqlite_vec_store.py:109:def rowid_vec_projection(table: str) -> VecProjection:
quire\sqlite_vec_store.py:110:    return VecProjection(
quire\__init__.py:82:    VecProjection,
quire\__init__.py:260:    "VecProjection",
```

Quire push:

- Current Quire branch: `master`.
- Pushed commit: `7637b8a33fa3d8d76ea2f996a8d1bdce5f0ada7f`.
- Push output: `c3e53c5..7637b8a  master -> master`.

Propstore pin and dependency gates:

- `pyproject.toml` and `uv.lock` pin Quire to pushed Git commit `7637b8a33fa3d8d76ea2f996a8d1bdce5f0ada7f`.
- `uv run pyright propstore` passed with `0 errors, 0 warnings, 0 informations`; the command built Quire from `git+https://github.com/ctoth/quire@7637b8a33fa3d8d76ea2f996a8d1bdce5f0ada7f`.
- `rg -n -F -- "quire @ file" pyproject.toml uv.lock`: no hits.
- `rg -n -F -- "quire @ .." pyproject.toml uv.lock`: no hits.
- `rg -n -F -- "quire @ C:" pyproject.toml uv.lock`: no hits.
- `rg -n -F -- "[tool.uv.sources]" pyproject.toml`: `80:[tool.uv.sources]`.
- `rg -n -F -- "path =" pyproject.toml`: no hits.
- `rg -n -F -- "workspace = true" pyproject.toml`: no hits.
- `uv lock --check` resolved 159 packages.
- `uv tree --package quire` resolves `quire v0.2.0` with `sqlalchemy v2.0.49`.
- SHA search confirms the pushed Quire commit in `pyproject.toml` and `uv.lock`.

Phase 3 is complete. Phase 4 may start.

### Generic Family Metadata Correction Audit

Recorded 2026-05-20.

Binding note: Quire's SQLAlchemy engine/session layer owns generic access to a
family's main mapped model and reference/FK metadata. Propstore must not reach
around Quire with claim-specific or concept-specific model lookups, lookup
wrappers, model maps, aliases, or per-family reference helpers.

Completed-record audit:

- Phase 3 mapped `Claim`, `Concept`, and `ClaimConceptLink` as proof models and
  exposed read-only and writable sessions through `DerivedStoreHandle`. The
  record does not preserve a Propstore claim/concept lookup wrapper.
- The completed gate requires a typed `DerivedSession`/query context API, but
  does not explicitly require that API to resolve a family main model and
  reference/FK metadata generically from Quire family metadata.

Follow-up gate for the next Quire-owned engine slice: `DerivedSession` or its
owner-layer query context must expose a generic family metadata lookup that
returns the mapped main model and reference/FK metadata for any registered
charter family. Proof coverage must query the claim and concept proof families
through that same generic path.

Generic family metadata correction implemented 2026-05-20:

- Quire commit `2917fd0` added `identity_field` and `reference_keys` to
  charter-derived `SchemaObject` records, propagated those facts from
  `FamilyCharter`, and added generic `SqlAlchemySchema.identity_field`,
  `reference_index_from_records`, `resolve_reference_id`, and
  `require_reference_id` APIs.
- Quire proof gates passed: `uv run pyright` returned 0 errors, and
  `uv run pytest tests/test_sqlalchemy_engine.py
  tests/test_charters_schema_ir.py` passed with 14 tests.
- Quire push completed: `bc71de8..2917fd0 master -> master`.
- Propstore commit `c2c55bed` pins Quire to pushed SHA
  `2917fd08bd03cb2d317f4dceb5221b1e6b88a6e6`; local dependency searches for
  `quire @ file`, `quire @ ..`, `quire @ C:`, `path =`, and
  `workspace = true` returned no hits.

### Post-Completion Engine Audit

Recorded 2026-05-20.

Current repository audit:

- Current Propstore dependency state pins Quire to pushed commit
  `2917fd08bd03cb2d317f4dceb5221b1e6b88a6e6`. This supersedes the earlier
  Phase 3 pin to `7637b8a33fa3d8d76ea2f996a8d1bdce5f0ada7f` and includes all
  completed engine follow-up capability repairs listed here.
- Quire commit `8a84f20` repaired a missing engine capability by adding
  charter-driven SQLAlchemy model construction and family write routing on
  `SqlAlchemySchema` and `DerivedSession`. Propstore commit `8b1daac7` pinned
  that pushed Quire commit before later claim cutover work consumed it.
- Quire commit `bc71de8` repaired a missing relationship capability by adding
  `order_by` to `CharterRelationship`/`SchemaRelationship` and passing it to
  SQLAlchemy `relationship()` generically. Propstore commit `baf75265` pinned
  that pushed Quire commit before ordered claim source-assertion relationships
  consumed it.
- Quire commit `2917fd0` is the current audited pin and includes the generic
  family reference lookup record above. The current audit found no newer Quire
  engine commit after `2917fd0` that is missing from this file.

Remaining fix audit:

- The completed Phase 3 record was incomplete until the construction,
  relationship-ordering, and generic family metadata repairs above were added.
  Those repairs are now recorded as owned engine follow-up fixes.
- No compatibility shim, duplicate model map, claim/concept lookup wrapper,
  fallback reader, row DTO, kwargs builder, or parallel old/new construction
  path is allowed as a replacement for these Quire generic capabilities. If a
  later Propstore family cutover needs another model construction or metadata
  fact, the fix belongs in Quire's generic engine/session API first.
