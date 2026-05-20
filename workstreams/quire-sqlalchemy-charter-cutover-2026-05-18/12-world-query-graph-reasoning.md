# Quire SQLAlchemy Charter Cutover: World Query, Graph, And Reasoning

Date: 2026-05-18

## Goal

Cut `WorldQuery`, graph construction, world reasoning, worldline
materialization, support-revision projection, and ASPIC bridge consumers from
raw SQLite/projection rows to typed model queries over Quire read-only
SQLAlchemy sessions.

End state:

- `WorldQuery` remains Propstore's semantic read facade and stops being a raw
  SQLite facade;
- `WorldQuery` requests a Quire derived-store read-only SQLAlchemy session from
  a Quire derived-store handle;
- family query APIs accept a session or typed repository/world context;
- graph construction consumes typed claim, concept, relation, stance,
  justification, micropublication, grounding, and context model objects;
- world reasoning consumes typed graph/value data;
- worldline materialization and argumentation consume typed world/session
  models;
- support-revision and ASPIC bridge code consume typed graph, stance, and
  justification models;
- app, CLI, and web surfaces keep their world-facing API shape.

## Prerequisites

Complete these cutover workstreams before this slice starts:

- Quire SQLAlchemy dependency and capability proof.
- Quire charter/schema IR.
- Quire SQLAlchemy table/mapping/session/catalog engine.
- Quire FTS and vector implementation.
- Propstore build orchestration cutover.
- Source and diagnostics cutover.
- Forms, concepts, and parameterizations cutover.
- Contexts and lifting cutover.
- Claims and active claims cutover.
- Relations, stances, and conflicts cutover.
- Justifications and micropublications cutover.
- Rules, grounding, calibration, and embeddings cutover.

Before implementation, verify the current repo state and prove the
prerequisite surface is already cut over:

```powershell
git status --short
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label world-prereq tests/test_world_query.py tests/test_worldline.py tests/test_graph_export.py tests/test_worldline_ic_merge_properties.py
rg -n -F -- "ProjectionTable(" propstore/families propstore/core propstore/world propstore/worldline tests
rg -n -F -- "ProjectionModel" propstore/families propstore/core propstore/world propstore/worldline tests
rg -n -F -- "sqlite3.Connection" propstore/world propstore/families propstore/core propstore/worldline tests
```

Implementation starts after the searches report only old
world/query/graph/reasoning paths named as deletion targets in this
workstream. Production hits outside those targets block implementation.

## Inventory Rows

| Inventory surface | Current owner | Final owner | Required action |
| --- | --- | --- | --- |
| `propstore/world/model.py` | Primary sidecar query facade over raw SQLite | Propstore `WorldQuery` over Quire read-only sessions | Replace raw connection/selectors with model/session queries |
| `propstore/world/queries.py` | World query helpers through projection rows | Typed world query helpers | Replace projection-model imports |
| `propstore/world/bound.py` and `propstore/world/overlay.py` | Bound/overlay worlds over projection rows | Bound/overlay worlds over typed model graph/store APIs | Replace row-model imports |
| `propstore/world/atms.py` | ATMS construction through projection rows | ATMS construction through typed graph/relation models | Replace row-model imports |
| `propstore/world/scm.py`, `propstore/world/intervention.py`, `propstore/world/resolution.py` | World reasoning consumers of row-derived graph/value data | World reasoning consumers of typed graph/value data | Replace row assumptions at world boundary |
| `propstore/core/graph_build.py` | Graph construction through projection models | Graph construction from typed model/session APIs | Replace row-model coercion with typed model reads |
| `propstore/core/analyzers.py` | Analyzer inputs through projection models | Analyzer inputs from typed graph/relation/claim models | Replace row coercion with typed model inputs |
| `propstore/graph_export.py` | Graph export from projection model rows | Graph export from typed world/session models | Replace projection-model imports |
| `propstore/structured_projection.py` | Analyzer projection back to assertions | Typed assertion projection owner | Replace row-derived data assumptions |
| `propstore/worldline/resolution.py` and `propstore/worldline/argumentation.py` | Worldline materialization/capture through row models | Worldline over typed world/session models | Replace projection imports and row coercion |
| `propstore/worldline/result_types.py` | Persisted result payload constructors named `from_mapping` | Explicit document/JSON payload constructors | Rename to boundary-specific constructors; keep typed result payload validation |
| `propstore/core/graph_types.py` | Graph provenance payload constructors named `from_mapping` | Explicit graph/provenance payload constructors | Rename to boundary-specific constructors; keep graph provenance validation |
| `propstore/world/queries.py` | `WorldBindActiveReport` active-object spelling | World binding report naming over activation state | Rename to `WorldBindActivationReport` |
| `propstore/support_revision/projection.py` and `propstore/support_revision/af_adapter.py` | Support-revision projection from row models | Support-revision over typed graph/relation models | Replace projection-model imports |
| `propstore/support_revision/state.py`, `history.py`, `snapshot_types.py`, and `explanation_types.py` | Support-revision persisted payload constructors named `from_mapping` | Explicit document/JSON payload constructors | Rename to boundary-specific constructors; keep typed revision payload validation |
| `propstore/aspic_bridge/extract.py` and `propstore/aspic_bridge/translate.py` | ASPIC bridge through stance projection model | ASPIC bridge over typed stance/justification models | Replace projection-model imports |

## Deletion Targets

Delete these old production surfaces first, then use import/type/test failures
as the work queue:

- direct `sqlite3.Connection` runtime assumptions in `WorldQuery`;
- `row_factory` setup in world and family runtime paths;
- direct `connect_sqlite_store` usage in world/query/graph/reasoning paths;
- family selectors that accept raw connections where a session/model query is
  the real abstraction;
- graph construction coercion through projection row models;
- world, bound, overlay, and ATMS imports of projection row/model classes;
- `_claim_rows` in `propstore/world/model.py`;
- `ActiveClaimInput` and `ActiveMicropublicationInput` protocol surfaces in
  world/environment/overlay/ATMS APIs;
- `ActiveClaimResolver` in `propstore/world/value_resolver.py`;
- `ActiveWorldGraph` spelling in public world/graph APIs;
- `WorldBindActiveReport` spelling in world query report APIs;
- raw SQL snippets that duplicate SQLAlchemy query construction;
- `ProjectionRow` usage in world, family, graph, and worldline runtime paths;
- generic `from_mapping` persisted-result constructors in
  `propstore/worldline/result_types.py`;
- generic `ProvenanceRecord.from_mapping` and graph provenance payload
  constructors in `propstore/core/graph_types.py`;
- generic support-revision `from_mapping` constructors and helper functions
  in `state.py`, `history.py`, `snapshot_types.py`, and `explanation_types.py`;
- support-revision row projection paths;
- ASPIC bridge imports of stance projection models.

## Caller And Update Surfaces

Update every caller that imports or consumes raw sidecar connections,
projection rows, projection models, row factories, or raw SQL query helpers:

- `propstore/world/model.py`;
- `propstore/world/queries.py`;
- `propstore/world/bound.py`;
- `propstore/world/overlay.py`;
- `propstore/world/atms.py`;
- `propstore/world/scm.py`;
- `propstore/world/intervention.py`;
- `propstore/world/resolution.py`;
- `propstore/core/graph_build.py`;
- `propstore/core/analyzers.py`;
- `propstore/graph_export.py`;
- `propstore/structured_projection.py`;
- `propstore/worldline/resolution.py`;
- `propstore/worldline/argumentation.py`;
- `propstore/worldline/result_types.py`;
- `propstore/support_revision/projection.py`;
- `propstore/support_revision/af_adapter.py`;
- `propstore/support_revision/dispatch.py`;
- `propstore/aspic_bridge/extract.py`;
- `propstore/aspic_bridge/translate.py`.

Required caller final state:

- `WorldQuery` owns semantic read facade behavior and receives typed sessions
  from Quire derived-store handles;
- `world/queries.py` contains typed query helpers and no projection-model
  imports;
- bound and overlay worlds read typed graph/store objects;
- ATMS construction uses typed graph/relation models;
- SCM, intervention, and resolution code consume typed graph/value data;
- graph build and analyzers consume typed domain models rather than row
  dictionaries or projection rows;
- graph export reads typed world/session results;
- worldline resolution and argumentation consume typed world/session models;
- persisted result payload constructors use boundary-specific names such as
  `from_json_payload`, `from_document_payload`, or `from_row_mapping`;
- graph provenance payload constructors use boundary-specific names and do not
  expose generic `from_mapping`;
- world bind report names describe activation state without introducing a
  second `Active*` object family;
- support-revision consumes typed graph/relation models;
- support-revision persisted payload constructors use boundary-specific names
  such as `from_json_payload` or `from_document_payload`;
- ASPIC bridge consumes typed stance and justification models.

## Semantic Boundaries

Preserve these Propstore-owned behaviors:

- world-facing APIs;
- `WorldQuery` cache ownership;
- condition solver caches;
- lifting caches;
- historical query behavior;
- render policy semantics;
- app facade behavior;
- graph edge classification;
- ATMS construction semantics;
- SCM and intervention semantics;
- world resolution semantics;
- worldline materialization and argumentation semantics;
- support-revision semantics;
- ASPIC extraction and translation semantics.

Raw SQLite connection management, row factory setup, SQL query construction,
projection row conversion, and generic persisted-payload mapping names move to
Quire session/query machinery or disappear.

## Slice Order

Execute in this order:

1. `WorldQuery` session cutover.
2. World query helper migration.
3. Bound, overlay, and ATMS typed-model migration.
4. Graph build, analyzer, structured projection, and graph export migration.
5. SCM, intervention, and world resolution migration.
6. Worldline resolution, argumentation, and result payload constructor cutover.
7. Support-revision and ASPIC bridge migration.
8. Data parity, behavior parity, search gates, and completion gates.

## Execution Loop

1. Read the inventory rows in this file and the current world/query/graph files.
2. List all current production callers from the caller/update surface above.
3. Name the target session/query model classes and typed graph/value inputs in
   the implementation notes or commit message.
4. Delete the old raw connection, projection-row, and row-coercion surfaces
   first.
5. Run the smallest import/type/test command that exposes the next failures.
6. Fix only failures caused by this slice's deletion and named caller list.
7. Replace raw SQLite access with Quire SQLAlchemy session/model access.
8. Replace loose dict/list/row payloads with typed world, graph, relation,
   claim, stance, justification, grounding, context, and micropublication model
   objects.
9. Rename `ActiveWorldGraph` to `WorldActivationGraph`; it remains a semantic
   activation result because it carries environment plus active/inactive claim
   id sets, but it stops using the misleading active-object-family spelling.
10. Rename `ActiveClaimResolver` to `ClaimValueResolver` and make it consume
   typed `Claim` query results.
11. Rename `WorldBindActiveReport` to `WorldBindActivationReport`.
12. Use Rope for the project-wide Python renames above before hand-fixing
   dynamic references, tests, docs, and string mentions exposed by the named
   `rg` gates.
13. Delete `ActiveClaimInput` and `ActiveMicropublicationInput` from world,
   environment, overlay, ATMS, ASPIC, support-revision, and value-resolution
   APIs.
14. Replace generic persisted-result, graph-provenance, and support-revision
    `from_mapping` constructors with boundary-specific constructors.
15. Run the world/query/graph/reasoning gates.
16. Run the old-path search gates.
17. Run the data-parity and behavior-parity gates.

Implementation starts only after session, relationship, query, catalog, FTS,
vector, JSON, and association-object capabilities are complete in their owning
Quire or family workstreams.

## Data-Parity And Metric Gates

```powershell
uv run scripts/compare_sqlalchemy_charter_parity.py --before <old-sidecar.sqlite> --after <new-sidecar.sqlite> --owner world-query-graph-reasoning --out reports/sqlalchemy-charter-parity/world-query-graph-reasoning.json
uv run scripts/compare_sqlalchemy_charter_parity.py --before <old-sidecar.sqlite> --after <new-sidecar.sqlite> --owner world-query-graph-reasoning --out reports/sqlalchemy-charter-parity/world-query-graph-reasoning-behavior.json --require-behavior world-query --require-behavior graph-build --require-behavior atms --require-behavior scm-intervention-resolution --require-behavior worldline --require-behavior support-revision --require-behavior aspic
```

Build the sidecar from the same repository snapshot before and after this
slice and compare:

- `WorldQuery` method outputs for `get_claim`, `resolve_claim`,
  `claims_for`, `claims_related_to_concept`, `claims_with_policy`,
  `claims_by_ids`, `get_concept`, `resolve_concept`, `all_concepts`,
  `all_parameterizations`, `all_relationships`, `all_claim_stances`,
  `stances_between`, `conflicts`, `all_authored_justifications`,
  `justifications_for_claim_scope`, `claim_stances_with_policy`,
  `all_micropublications`, `search`, `similar_claims`, `similar_concepts`,
  `forms_by_dimensions`, `form_algebra_for`, `form_algebra_using`, `stats`,
  `authored_justification_count`, `parameterizations_for`, `group_members`,
  `explain`, `bind`, `intervene`, `observe`, and `chain_query` over the
  fixtures exercised by `tests/test_world_query.py`,
  `tests/test_world_query_at_journal_step.py`, and `tests/test_worldline.py`;
- graph node and edge counts plus edge key sets;
- graph edge classification results;
- analyzer inputs and outputs;
- graph export output keys and edge sets;
- bound and overlay world query results;
- ATMS nodes, justifications, conflicts, and labels;
- SCM, intervention, and resolution outputs;
- render policy results;
- historical query behavior;
- worldline resolution and argumentation materialization outputs;
- persisted worldline result payload round trips;
- support-revision argument framework outputs;
- ASPIC extraction and translation outputs.

The phase fails when a row, key, semantic query result, graph edge, ATMS label,
reasoning result, render policy result, worldline materialization, support
revision result, or ASPIC output disappears. The only accepted disappearances
are the raw connection paths, projection imports, row-coercion helpers, raw SQL
snippets, and constructor names listed as deletion targets in this file.
Accepted output-shape renames must be listed in the implementation closure
report or commit message.

## Required Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label world-charter tests/test_world_query.py tests/test_worldline.py tests/test_graph_export.py tests/test_worldline_ic_merge_properties.py
rg -n -F -- "sqlite3.Connection" propstore/world propstore/families tests
rg -n -F -- "row_factory" propstore/world propstore/families tests
rg -n -F -- "connect_sqlite_store" propstore/world propstore/families tests
rg -n -F -- "ProjectionRow" propstore/world propstore/families tests
rg -n -F -- "ProjectionModel" propstore/world propstore/core propstore/graph_export.py propstore/worldline propstore/support_revision propstore/aspic_bridge tests
rg -n -F -- "from_mapping" propstore/core propstore/families propstore/world propstore/worldline propstore/support_revision tests
rg -n -F -- "_claim_rows" propstore/world tests
rg -n -F -- "ActiveClaimInput" propstore tests
rg -n -F -- "ActiveMicropublicationInput" propstore tests
rg -n -F -- "ActiveClaimResolver" propstore tests
rg -n -F -- "ActiveWorldGraph" propstore tests
rg -n -F -- "WorldBindActiveReport" propstore tests
rg -n -F -- "claim_row_query_plan" propstore/world propstore/core propstore/graph_export.py propstore/worldline propstore/support_revision tests
rg -n -F -- "claim_stance_policy_query_plan" propstore/world propstore/core propstore/graph_export.py propstore/worldline propstore/support_revision tests
```

All searches are zero-hit gates outside notes, workstreams, docs, and reports.

## Completion Criteria

This slice is complete only when:

- `WorldQuery` obtains read-only SQLAlchemy sessions from Quire derived-store
  handles;
- world query helpers use typed session/model queries;
- family query APIs consumed by world code accept sessions or typed
  repository/world contexts;
- bound and overlay worlds consume typed graph/store APIs;
- ATMS construction consumes typed graph/relation models;
- SCM, intervention, and resolution consumers use typed graph/value data;
- graph construction and analyzers consume typed model objects;
- `WorldActivationGraph` is the activation result type; `ActiveWorldGraph`
  is absent from production code and tests;
- `ClaimValueResolver` consumes typed `Claim` query results; `ActiveClaimResolver`
  is absent from production code and tests;
- `WorldBindActivationReport` is the world binding report type;
  `WorldBindActiveReport` is absent from production code and tests;
- world/environment/overlay/ATMS protocols do not accept `ActiveClaimInput`,
  `ActiveMicropublicationInput`, dict rows, or mapping coercion inputs;
- graph export uses typed world/session results;
- worldline resolution and argumentation consume typed world/session models;
- persisted result payload constructors use boundary-specific constructor
  names and no generic `from_mapping` path remains in the owned surface;
- support-revision uses typed graph/relation models;
- support-revision state, history, snapshot, and explanation payload
  constructors use boundary-specific names and no generic `from_mapping` path
  remains in `propstore/support_revision`;
- ASPIC bridge code uses typed stance and justification models;
- every named caller/update surface no longer imports raw sidecar connection
  helpers, projection rows, projection models, row factories, or row
  dictionaries;
- the data-parity and behavior-parity gates pass;
- all required tests pass through the logged pytest wrapper;
- all old-path search gates above are zero-hit outside notes, workstreams,
  docs, and reports.
