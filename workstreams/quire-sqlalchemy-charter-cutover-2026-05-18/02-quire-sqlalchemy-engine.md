# Quire SQLAlchemy Engine Workstream

Date: 2026-05-18

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
