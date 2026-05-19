# Quire SQLAlchemy Charter Cutover: Contexts And Lifting

Date: 2026-05-18

## Goal

Replace the context/lifting projection and raw-row query surface with Quire
SQLAlchemy charter models while preserving Propstore's context semantics and
lifting behavior.

End state:

- Quire owns generic SQLAlchemy table creation, mapping, sessions, JSON/null
  conversion, catalog metadata, and FK mechanics.
- Propstore owns authored context documents, context semantic passes, lifting
  rule binding, lifting graph validation, and `LiftingSystem` domain behavior.
- Context and lifting persistence uses typed model objects, not projection
  rows, raw SQLite selectors, or helper-built dictionaries.
- `propstore/families/contexts/declaration.py` no longer owns generic
  projection/query plumbing.

## Prerequisites

Complete these cutover workstreams before this slice starts:

- Quire SQLAlchemy dependency and capability proof.
- Quire charter/schema IR.
- Quire SQLAlchemy table/mapping/session/catalog engine.
- Quire FTS and vector implementation.
- Propstore build orchestration cutover.
- Source vertical slice.
- Forms and sources cleanup closure.
- Concept/form/parameterization slice.

Before implementation, verify the current repo state and prove the prerequisite
surface is already cut over:

```powershell
git status --short
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label context-prereq tests/test_world_query.py tests/test_required_schema_completeness.py tests/test_fixture_schema_parity.py
rg -n -F -- "ProjectionTable" propstore/families/contexts propstore/derived_build.py propstore/derived_build_plan.py tests
rg -n -F -- "ProjectionModel" propstore/families/contexts tests
rg -n -F -- "sqlite3.Connection" propstore/families/contexts propstore/context_lifting.py propstore/app/contexts.py tests
```

This slice is blocked until the first two searches have zero production hits
outside notes, workstreams, docs, and reports, except hits in the context files
named as deletion targets below.

## Target Models

Declare these Propstore domain models through the Quire charter system:

- `Context`
- `ContextAssumption`
- `ContextLiftingRule`
- `ContextLiftingMaterialization`

Context authored document identity, authored fields, and semantic validation
remain Propstore-owned. Quire persists and queries the typed model fields
declared by the context charter.

## Deletion Targets

Delete these old production surfaces first, then use import/type/test failures
as the work queue:

- context `ProjectionModel` declarations;
- context `ProjectionTable` declarations;
- `CONTEXT_TABLE`;
- `CONTEXT_ASSUMPTION_TABLE`;
- `CONTEXT_LIFTING_RULE_TABLE`;
- `CONTEXT_LIFTING_MATERIALIZATION_TABLE`;
- context table creation helpers;
- context row dictionaries;
- selectors/loaders that merely reconstruct lifting systems from raw rows;
- generic projection/query plumbing in
  `propstore/families/contexts/declaration.py`.

The inventory row for this slice is:

| Inventory surface | Current owner | Final owner | Required action |
| --- | --- | --- | --- |
| `propstore/families/contexts/declaration.py` projection pieces | Context/lifting projection/query API | Context charter plus lifting semantics | Delete generic projection/query plumbing |

## Helper Classification

File: `propstore/families/contexts/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `_nullable_text` | delete | Generic nullable text conversion belongs to Quire charter conversion. |
| `_json_or_none` | delete | Generic JSON conversion belongs to Quire JSON adapter. |
| `_json_mapping` | delete | Generic JSON conversion belongs to Quire JSON adapter. |
| `_json_string_tuple` | delete | Generic JSON conversion belongs to Quire JSON adapter. |
| `create_context_tables` | delete | Quire charter creates tables. |
| `populate_contexts` | delete | Replace with SQLAlchemy session add/flush. |
| `filter_invalid_context_lifting_rows` | move | Move invalid lifting-rule filtering semantics to context/lifting semantic owner. |
| `compile_context_sidecar_rows` | replace | Replace with typed `Context`, `ContextAssumption`, and `ContextLiftingRule` model construction. |
| `compile_context_lifting_materialization_rows` | replace | Replace with typed `ContextLiftingMaterialization` model construction. |
| `load_lifting_system` | move | Keep lifting-system assembly as context owner API; implement over typed model queries. |
| `_projection_row` | delete | Projection row wrapper is deleted. |
| `_lifting_materialization_row` | delete | Projection row wrapper is deleted. |

Generic SQL/helper deletion predicate for this slice:

- delete helpers whose body is table-shaped `SELECT`, `COUNT`, `INSERT`,
  `DELETE`, row attachment, row coercion, or projection-model wrapping with no
  Propstore semantic policy;
- keep and move semantic code that owns context/lifting semantics,
  lifting-rule validation, authored-document identity, or graph validation;
- after moving kept semantics, delete the original helper-shaped production
  path.

## Caller And Update Surfaces

Update every caller that imports or consumes context projection rows, raw
SQLite selectors, or helper-built row dictionaries:

- `propstore/app/contexts.py`;
- `propstore/context_lifting.py`;
- `propstore/world/model.py`;
- `propstore/worldline/runner.py`;
- `propstore/worldline/argumentation.py`;
- `propstore/aspic_bridge/lifting_projection.py`.

Required caller final state:

- app code calls context owner APIs and does not import context projection
  constants or raw selectors;
- `propstore/context_lifting.py` assembles `LiftingSystem` from typed
  `Context`, `ContextAssumption`, `ContextLiftingRule`, and
  `ContextLiftingMaterialization` model queries;
- world and worldline code use typed context/lifting owner APIs or Quire
  sessions, not raw sidecar connections;
- ASPIC lifting projection code consumes typed lifting models or owner-layer
  reports, not raw context rows.

## Semantic Moves

Preserve these behaviors as Propstore semantic owner code:

- context authored document schema;
- context semantic passes;
- lifting rule binding;
- lifting graph validation;
- invalid lifting-rule filtering semantics;
- `LiftingSystem` domain behavior.

Move those semantics into context/lifting owner modules before deleting the
helper-shaped paths that currently host them. Generic null/JSON/table/query
behavior moves to Quire charter/session/catalog machinery.

## Execution Loop

1. Read the current context inventory entry and context family files.
2. List all current production callers from the caller/update surface above.
3. Name the target models in the implementation notes or commit message.
4. Delete the old context projection/read-model surface first.
5. Run the smallest import/type/test command that exposes the next failures.
6. Fix only failures caused by this slice's deletion and named caller list.
7. Replace raw SQLite access with Quire SQLAlchemy session/model access.
8. Replace loose dict/list/row payloads with typed context/lifting model
   objects.
9. Delete field-specific JSON/null coercers once generic charter conversion
   covers the field.
10. Run the family gates.
11. Run the old-path search gates.
12. Run the data-parity gate.

No Propstore workaround is allowed for a missing Quire generic feature. A
missing SQLAlchemy charter, JSON, relationship, catalog, or session capability
returns the work to the Quire owner workstream.

## Data Parity Gate

Build the sidecar from the same repository snapshot before and after this
slice and compare:

- row counts for context, context assumption, lifting rule, and lifting
  materialization tables;
- primary-key/key-set coverage for every context/lifting table this slice
  owns;
- representative context owner API results;
- representative `LiftingSystem` assembly results;
- world/worldline context query results that depend on lifting rules;
- build diagnostics associated with invalid context/lifting rows.

The phase fails when a row, key, diagnostic, semantic query result, or lifting
materialization disappears. The only accepted disappearances are the table
constants, projection rows, and helper paths named as deletion targets in this
file. Accepted column/table renames must be listed in the implementation
closure report or commit message.

## Required Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label context-charter tests/test_world_query.py tests/test_required_schema_completeness.py tests/test_fixture_schema_parity.py
rg -n -F -- "CONTEXT_TABLE" propstore tests
rg -n -F -- "CONTEXT_ASSUMPTION_TABLE" propstore tests
rg -n -F -- "CONTEXT_LIFTING_RULE_TABLE" propstore tests
rg -n -F -- "CONTEXT_LIFTING_MATERIALIZATION_TABLE" propstore tests
rg -n -F -- "ProjectionModel(" propstore/families/contexts tests
rg -n -F -- "create_context_tables" propstore tests
rg -n -F -- "populate_contexts" propstore tests
rg -n -F -- "compile_context_sidecar_rows" propstore tests
rg -n -F -- "compile_context_lifting_materialization_rows" propstore tests
rg -n -F -- "_nullable_text" propstore/families/contexts tests
rg -n -F -- "_json_or_none" propstore/families/contexts tests
rg -n -F -- "_json_mapping" propstore/families/contexts tests
rg -n -F -- "_json_string_tuple" propstore/families/contexts tests
```

All searches are zero-hit gates outside notes, workstreams, docs, and reports.

## Completion Criteria

This slice is complete only when:

- the context/lifting charter declares the target models listed above;
- context/lifting tables are generated by Quire charter/catalog machinery;
- context/lifting population writes typed model objects through a Quire
  SQLAlchemy session;
- `load_lifting_system` or its replacement owner API reads typed model objects;
- invalid lifting-rule filtering semantics are preserved in context/lifting
  owner code;
- every named caller/update surface no longer imports context projection rows,
  table constants, raw SQLite selectors, or row dictionaries;
- the data parity gate passes;
- all required tests pass through the logged pytest wrapper;
- all old-path search gates above are zero-hit outside notes, workstreams,
  docs, and reports.
