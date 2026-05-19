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
  may remain frozen when they are not mapped entities.
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
