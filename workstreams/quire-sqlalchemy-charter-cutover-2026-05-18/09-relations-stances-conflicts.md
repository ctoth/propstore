# 09 - Relations, Stances, And Conflicts Workstream

Date: 2026-05-18

## Goal

Cut relations, stances, and conflicts from the old projection/read-model layer
to typed Propstore domain models backed by Quire SQLAlchemy charters.

Final state:

- `Stance` is the mapped stance model used for sidecar reads and writes.
- `ConceptRelation` is the mapped concept-relation model used for authored and
  derived relation edges.
- `ConflictWitness` is the mapped conflict witness model used for conflict
  detector output and world/reasoning inputs.
- Relation-edge polymorphism is expressed through SQLAlchemy mapping, not a
  second projection vocabulary.
- Graph edge classification remains Propstore semantic behavior over typed
  relation objects.
- Stance reference validation, broken-reference quarantine diagnostics, and
  conflict detector output semantics remain in Propstore relation owners.
- `propstore/families/relations/projection_model.py` is deleted.
- `propstore/families/relations/declaration.py` no longer owns generic
  projection, table creation, row carrier, select/count, or query-plan
  plumbing.

## Prerequisites

Complete the earlier cutover workstreams before starting implementation:

Required phase file prerequisites: `00-index.md`, `inventory-matrix.md`,
`helper-ledger.md`, `01-quire-capability-and-charter.md`,
`02-quire-sqlalchemy-engine.md`, `03-quire-fts-vector.md`,
`04-propstore-build-orchestration.md`, `05-source-and-diagnostics.md`,
`06-forms-concepts-parameterizations.md`, `07-contexts-lifting.md`,
`08-claims-active-claims.md`.

1. Mechanical order check and current-state inventory confirmation.
2. Quire SQLAlchemy dependency and capability proof.
3. Quire charter/schema IR.
4. Quire SQLAlchemy table/mapping/session/catalog engine.
5. Quire FTS and vector implementation.
6. Propstore build orchestration cutover.
7. `05-source-and-diagnostics.md`.
8. `06-forms-concepts-parameterizations.md`.
9. `07-contexts-lifting.md`.
10. `08-claims-active-claims.md`.

Before implementation:

- reread `00-index.md`;
- reread `inventory-matrix.md`;
- reread this file;
- reread the relations phase in
  `workstreams/quire-sqlalchemy-charter-cutover-workstream-2026-05-18.md`;
- confirm Propstore and Quire worktree states;
- confirm Propstore is pinned to a pushed Quire commit, never a local path;
- run or update the phase-order checker proving this workstream follows its
  prerequisites.

This workstream is blocked until the prerequisite workstreams have delivered
Quire-generated charters, mappings, sessions, relationships, JSON adapters,
catalog metadata, and build orchestration over writable sessions.

## Inventory Rows

| Inventory surface | Current owner | Final owner | Required action |
| --- | --- | --- | --- |
| `propstore/relation_analysis.py` | Stance summary through projection model rows | Stance summary from typed relation models | Replace projection-model imports |
| `propstore/families/relations/projection_model.py` | Relation/stance/conflict row mapper | Typed relation/stance/conflict models | Delete |
| `propstore/families/relations/declaration.py` projection/query pieces | Relation sidecar compiler/query API | Relation semantics plus model queries | Delete generic projection/query plumbing |

The broader world, graph, support-revision, ASPIC, and worldline conversion
rows remain owned by the later WorldQuery/graph/reasoning workstream. This
slice updates those callers only when deletion of the relation projection
surface exposes a direct import/type failure in the current family cutover.

## Target Models

Declare these Propstore domain models through the Quire charter system:

- `Stance`
- `ConceptRelation`
- `ConflictWitness`

Model requirements:

- `relation_edge` is mapped explicitly with SQLAlchemy polymorphic mapping;
- stance source, target, kind, polarity, and resolution fields are typed model
  fields or typed value objects;
- condition-difference serialization uses the relation/stance model JSON
  adapter;
- conflicts reference typed claim, concept, and stance identities through Quire
  reference/FK APIs;
- generic null, enum, id, JSON, table, and query-plan conversion belongs to
  Quire, not relation family helpers.

## Deletion Targets

Delete these old production surfaces first, then use import/type/test failures
as the work queue:

- `propstore/families/relations/projection_model.py`;
- `RelationshipRow`;
- `StanceRow`;
- `ConflictRow`;
- relation projection codecs;
- `RELATION_EDGE_TABLE`;
- `CLAIM_STANCE_STORAGE_MODEL`;
- `CONCEPT_RELATIONSHIP_STORAGE_MODEL`;
- `RELATIONSHIP_ROW_MODEL`;
- `STANCE_ROW_MODEL`;
- `CONFLICT_ROW_MODEL`;
- discriminator/query-plan objects that duplicate SQLAlchemy polymorphism or
  relationship filtering;
- raw stance/conflict/relationship row dictionaries;
- manual relation select/count helpers whose only job is generic SQL selection;
- generic projection/query plumbing in
  `propstore/families/relations/declaration.py`.

## Helper Classification

File: `propstore/families/relations/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `RelationshipRow` | delete | Replace with typed `ConceptRelation` model. |
| `StanceRow` | delete | Replace with typed `Stance` model. |
| `ConflictRow` | delete | Replace with typed `ConflictWitness` model. |
| `_optional_numeric` | delete | Generic nullable numeric conversion belongs to Quire charter conversion. |
| `compile_authored_stance_sidecar_rows` | replace | Replace with `Stance` model construction. |
| `compile_authored_stance_sidecar_rows_with_diagnostics` | move | Move stance reference validation/quarantine diagnostics to `propstore/families/relations/declaration.py::compile_authored_stance_models_with_diagnostics`; delete row output. |
| `select_stances_between` | replace | Replace with SQLAlchemy relationship/session query. |
| `select_conflicts` | replace | Replace with SQLAlchemy session query over `ConflictWitness`. |
| `select_all_relationships` | replace | Replace with SQLAlchemy session query over `ConceptRelation`. |
| `select_all_claim_stances` | replace | Replace with SQLAlchemy session query over `Stance`. |
| `select_claim_stances_with_policy` | move | Move visibility/render policy semantics to `propstore/world/model.py::WorldQuery.claim_stances_with_policy`; implement through typed `Stance` relationship predicates. |
| `select_explanation_stances` | move | Move explanation traversal semantics to `propstore/world/model.py::WorldQuery.explain`; implement over typed `Stance` relationships. |
| `count_conflicts` | replace | Replace with SQLAlchemy count query over `ConflictWitness`. |

Generic SQL/helper deletion predicate for this slice:

- delete helpers whose body is table-shaped `SELECT`, `COUNT`, `INSERT`, row
  attachment, row coercion, projection-model wrapping, or query-plan assembly
  with no Propstore semantic policy;
- keep and move semantic code that owns authored stance document schema,
  stance target/reference validation, quarantine diagnostics, conflict detector
  output semantics, graph edge classification, visibility/render policy, or
  explanation traversal semantics;
- after moving kept semantics, delete the original helper-shaped production
  path.

## Caller And Update Surfaces

Update every caller that imports or consumes relation projection rows, stance
storage models, conflict rows, raw SQLite selectors, or helper-built row
dictionaries:

- `propstore/relation_analysis.py`;
- `propstore/aspic_bridge/extract.py`;
- `propstore/aspic_bridge/translate.py`;
- `propstore/core/analyzers.py`;
- `propstore/core/graph_build.py`;
- `propstore/graph_export.py`;
- `propstore/support_revision/af_adapter.py`;
- `propstore/support_revision/projection.py`;
- `propstore/world/atms.py`;
- `propstore/world/bound.py`;
- `propstore/world/overlay.py`;
- `propstore/worldline/argumentation.py`.

Required caller final state:

- `propstore/relation_analysis.py` queries typed `Stance` models or relation
  owner APIs, not stance projection rows;
- graph/analyzer/export code consumes typed `Stance`, `ConceptRelation`, and
  `ConflictWitness` data exposed by the relation owner;
- ASPIC and support-revision code use typed stance/relation owner APIs for the
  relation fields this slice deletes from projection models;
- world and worldline callers no longer import
  `propstore.families.relations.projection_model`, relation row classes, or
  relation storage model constants.

The later WorldQuery/graph/reasoning workstream still owns the full conversion
of raw sidecar world access to Quire read-only sessions.

## Semantic Moves

Preserve these behaviors in the named Propstore modules:

- authored stance document schema;
- stance target/reference validation;
- quarantine diagnostics for broken claim references;
- condition-difference serialization;
- stance-resolution validation and opinion extraction moved from claim storage
  helpers;
- conflict detector output semantics;
- graph edge classification;
- visibility/render policy semantics;
- explanation traversal semantics.

Target owners:

- `propstore/families/relations/declaration.py::compile_authored_stance_models_with_diagnostics`
  receives authored stance validation, stance reference validation, and
  quarantine diagnostics;
- `propstore/families/relations/declaration.py::coerce_stance_resolution_payload`
  and `StanceResolutionOpinion.from_payload` receive stance-resolution
  validation, opinion extraction, and condition-difference serialization;
- `propstore/families/relations/declaration.py::compile_conflict_witness_models`
  receives conflict detector output materialization and typed
  `ConflictWitness` query APIs;
- `propstore/core/graph_build.py` receives graph edge classification over
  typed mapped relation objects;
- `propstore/world/model.py::WorldQuery.claim_stances_with_policy` receives
  visibility/render policy predicates;
- `propstore/world/model.py::WorldQuery.explain` receives explanation
  traversal over typed `Stance` relationships.

Generic null, enum, id, JSON, table, query-plan, select/count, insert-row, and
row-carrier behavior moves to Quire charter/session/catalog machinery or is
deleted.

## Execution Loop

1. Read the relations inventory entries and current relation family files.
2. List all current production callers from the caller/update surface above.
3. Name `Stance`, `ConceptRelation`, `ConflictWitness`, and the SQLAlchemy
   polymorphic `relation_edge` decision in the implementation notes or commit
   message.
4. Delete the old relation projection/read-model surface first.
5. Run the smallest import/type/test command that exposes the next failures.
6. Fix only failures caused by this slice's deletion and named caller list.
7. Replace raw SQLite access with Quire SQLAlchemy session/model access.
8. Replace loose dict/list/row payloads with typed relation, stance, and
   conflict model objects.
9. Delete field-specific optional, enum, id, JSON, query-plan, and row coercers
   once generic charter conversion covers the field.
10. Run the family gates.
11. Run the old-path search gates.
12. Run the data-parity gate.

No Propstore workaround is allowed for a missing Quire generic feature. A
missing SQLAlchemy charter, polymorphic mapping, JSON, enum, relationship,
catalog, reference/FK, or session capability returns the work to the Quire
owner workstream.

## Data-Parity Gate

```powershell
uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --build-before projection --before reports/sqlalchemy-charter-parity/relations-stances-conflicts/before.sqlite --build-after sqlalchemy-charter --after reports/sqlalchemy-charter-parity/relations-stances-conflicts/after.sqlite --owner relations-stances-conflicts --workstream workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/09-relations-stances-conflicts.md --out reports/sqlalchemy-charter-parity/relations-stances-conflicts.json
```

Build the sidecar from the same repository snapshot before and after this
slice and compare:

- row counts for stance, concept relation, and conflict witness tables;
- primary-key/key-set coverage for every relation table this slice owns;
- stance lookup results by source claim, target claim, target concept, kind,
  polarity, and visibility/render policy predicate;
- conflict witness query results and `count_conflicts` replacement results;
- relationship query results for concept relation edges;
- graph edge classification results;
- relation analysis stance summaries;
- ASPIC stance extraction and translation inputs for relation-owned fields;
- support-revision relation projection inputs for relation-owned fields;
- world/worldline relation query results that depend on stance and conflict
  data;
- build diagnostics associated with broken stance references.

The phase fails when a row, key, diagnostic, semantic query result, graph edge,
stance summary, conflict result, ASPIC input, support-revision input, or
worldline relation result disappears.

Accepted parity difference allowlist:

- deleted projection model file, storage model constants, row classes,
  query-plan helpers, and generic helper paths named in this file's deletion
  targets;
- no column rename, table rename, row disappearance, key disappearance,
  diagnostic disappearance, semantic-query disappearance, graph-edge
  disappearance, stance-summary disappearance, conflict-result disappearance,
  ASPIC-input disappearance, support-revision-input disappearance, or
  worldline-relation-result disappearance is allowed.

## Required Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label relations-charter tests/test_graph_export.py tests/test_world_query.py tests/test_worldline.py
rg -n -F -- "propstore.families.relations.projection_model" propstore tests
rg -n -F -- "RelationshipRow" propstore tests
rg -n -F -- "StanceRow" propstore tests
rg -n -F -- "ConflictRow" propstore tests
rg -n -F -- "RELATION_EDGE_TABLE" propstore tests
rg -n -F -- "CLAIM_STANCE_STORAGE_MODEL" propstore tests
rg -n -F -- "CONCEPT_RELATIONSHIP_STORAGE_MODEL" propstore tests
rg -n -F -- "RELATIONSHIP_ROW_MODEL" propstore tests
rg -n -F -- "STANCE_ROW_MODEL" propstore tests
rg -n -F -- "CONFLICT_ROW_MODEL" propstore tests
rg -n -F -- "_optional_numeric" propstore/families/relations tests
rg -n -F -- "compile_authored_stance_sidecar_rows" propstore tests
rg -n -F -- "compile_authored_stance_sidecar_rows_with_diagnostics" propstore tests
rg -n -F -- "select_stances_between" propstore tests
rg -n -F -- "select_conflicts" propstore tests
rg -n -F -- "select_all_relationships" propstore tests
rg -n -F -- "select_all_claim_stances" propstore tests
rg -n -F -- "select_claim_stances_with_policy" propstore tests
rg -n -F -- "select_explanation_stances" propstore tests
rg -n -F -- "count_conflicts" propstore tests
```

All searches are zero-hit gates outside notes, workstreams, docs, and reports.

## Completion Criteria

This slice is complete only when:

- the relation charter declares `Stance`, `ConceptRelation`, and
  `ConflictWitness`;
- relation-edge polymorphism is implemented through SQLAlchemy mapping;
- relation population writes typed model objects through a Quire SQLAlchemy
  session;
- stance, concept relation, and conflict witness queries use typed
  model/session APIs;
- authored stance validation, broken-reference quarantine diagnostics,
  conflict detector output semantics, graph edge classification,
  visibility/render policy, and explanation traversal have final Propstore
  owners;
- every named caller/update surface no longer imports relation projection
  rows, storage models, row classes, raw SQLite selectors, or row dictionaries;
- the data parity gate passes;
- all required tests pass through the logged pytest wrapper;
- all old-path search gates above are zero-hit outside notes, workstreams,
  docs, and reports.
