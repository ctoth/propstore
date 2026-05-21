# 09 - Relations, Stances, And Conflicts Workstream

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

Binding notes from the 2026-05-20 update:

- Do not replace relation row lookup helpers with per-family identity lookup
  wrappers, convenience methods, or renamed helper-shaped APIs.
- Do not add standalone Propstore relation model classes and call that the
  cutover. `Stance`, `ConceptRelation`, and `ConflictWitness` are only valid
  final-state models when they are registered through the existing Propstore
  world family charter infrastructure in
  `propstore/families/world_charters.py`, backed by Quire catalog metadata and
  SQLAlchemy mappings. Plain classes in
  `propstore/families/relations/declaration.py` that are not chartered family
  models are just another duplicate model layer and are forbidden.
- Relation, stance, and conflict references must use generic Quire family
  reference/FK lookup and generic Quire main-model access. If a needed lookup
  capability is missing, add it in Quire; do not add a Propstore relation-only
  workaround.
- Family semantics may live on typed ORM/domain objects when the behavior is
  relation-specific, including stance visibility policy, conflict witness
  meaning, and graph edge classification. Generic identity, FK, table,
  session, and main-model lookup mechanics do not belong in this family.
- The current Phase 10 claim work has already deleted the production
  `ActiveClaim` import path and `CLAIM_ROW_MODEL` production callers. This
  phase must consume typed `Claim` fields and relationships already provided
  by Phase 10; it must not recreate `ActiveClaim`, claim row models, claim id
  aliases, claim lookup wrappers, row payload adapters, or graph-attribute
  stand-ins to make relation callers compile.
- No subsection of this phase is complete while any relation projection model,
  row carrier, storage-model constant, raw selector, or `sqlite3.Connection`
  relation query path remains in production. A passing type check before the
  old-path searches are zero-hit is only an intermediate repair signal.
- Downstream `coerce` calls are not a valid repair for deleted relation row
  models. Once IO has parsed an artifact or Quire has loaded a sidecar row, the
  caller must already hold typed `Stance`, `ConceptRelation`, and
  `ConflictWitness` instances. Remaining `STANCE_ROW_MODEL.coerce`,
  `CONFLICT_ROW_MODEL.coerce`, relation-row `.coerce`, or replacement
  "normalize/coerce" helpers in support-revision/world/runtime callers must be
  deleted by fixing the owning query/session boundary or typed construction
  site, not by adding a new coercion layer.
- Deleting `_optional_numeric` or row helpers must not be repaired by writing
  repeated field-name validation blocks, repeated constructor kwargs, or local
  type-narrowing code for `embedding_distance`, `confidence`, opinion fields,
  or any other relation field. Field shape is carried by typed documents,
  typed models, and Quire charter field metadata. If a field's type is unclear,
  fix the typed boundary or charter metadata; do not restate the field list in
  relation owner code.

Current old-surface findings from `rg` on 2026-05-20:

- The old relation projection surface is still present in production:
  `propstore/families/relations/projection_model.py` defines
  `RELATION_EDGE_TABLE`, `RELATIONSHIP_ROW_MODEL`, `STANCE_ROW_MODEL`,
  `CLAIM_STANCE_STORAGE_MODEL`, `CONCEPT_RELATIONSHIP_STORAGE_MODEL`, and
  `CONFLICT_ROW_MODEL`.
- `propstore/families/relations/declaration.py` still defines
  `RelationshipRow`, `StanceRow`, `ConflictRow`, `_optional_numeric`,
  `compile_authored_stance_sidecar_rows*`, `select_stances_between`,
  `select_conflicts`, `select_all_relationships`,
  `select_all_claim_stances`, `select_claim_stances_with_policy`,
  `select_explanation_stances`, and `count_conflicts`.
- Production callers still import or coerce relation rows/projection models in
  `propstore/aspic_bridge/extract.py`,
  `propstore/aspic_bridge/translate.py`, `propstore/core/analyzers.py`,
  `propstore/core/graph_build.py`, `propstore/graph_export.py`,
  `propstore/relation_analysis.py`,
  `propstore/support_revision/af_adapter.py`, `propstore/world/atms.py`,
  `propstore/world/bound.py`, `propstore/world/model.py`,
  `propstore/world/overlay.py`, and
  `propstore/worldline/argumentation.py`.
- `propstore/families/concepts/declaration.py` and
  `propstore/families/claims/declaration.py` still write relation projection
  rows through relation table/model constants, so this phase must coordinate
  those direct old-path call sites while preserving the owning phase
  boundaries.

Current audit update on 2026-05-20:

- Status: not started. This phase remains a future workstream and is blocked
  until the current Phase 10 claim queue is clean.
- Current Phase 10 queue from `uv run pyright propstore`: 25 package errors
  remain. The relation-owned dependency is
  `propstore/families/relations/declaration.py` importing deleted
  `CLAIM_CORE_TABLE` in `select_claim_stances_with_policy`; that must be
  repaired by deleting the raw claim-table query path and moving to typed
  `Claim`/`Stance` model queries, not by restoring `CLAIM_CORE_TABLE`.
- Current old-path searches: production `propstore.core.active_claims` and
  production `CLAIM_ROW_MODEL` hits are gone, but tests still reference those
  deleted Phase 10 surfaces. This phase must not depend on those test fixtures
  as compatibility evidence.
- Relation old paths remain current: `RELATION_EDGE_TABLE` still has
  production hits in claim, concept, and relation family declarations;
  `STANCE_ROW_MODEL` still has production hits in ASPIC, analyzer, graph,
  export, relation-analysis, support-revision, world, and worldline callers.
  These hits are the deletion work queue for this phase.
- Known dependency from completed Phase 10 work: relation callers that formerly
  accepted active-claim rows must now read claim identity, type, context,
  conditions, concept links, payloads, and source assertions from typed
  `Claim` objects and relationships. Do not reintroduce row-shaped claim
  fields such as `claim_id`, `claim_type`, `statement`, or `artifact_id`.
- Phase 10 handoff update: commit `017f694a` deleted
  `propstore/families/claims/storage.py` and moved embedded claim-stance
  validation/opinion extraction into this relation owner as
  `compile_claim_embedded_stance_rows_with_diagnostics`. This is a handoff,
  not a final relation implementation: the function still returns row tuples
  consumed by `StanceRow`/`RELATION_EDGE_TABLE`, so Phase 11 must delete that
  row-output path along with `compile_authored_stance_sidecar_rows*`,
  `StanceRow`, `CLAIM_STANCE_STORAGE_MODEL`, and the rest of the relation
  projection vocabulary. Do not copy that function into another helper,
  wrapper, or compatibility layer; replace it with typed `Stance` model
  construction and Quire session writes.

## Prerequisites

Complete the earlier cutover workstreams before starting implementation:

Required phase file prerequisites: `00-index.md`, `inventory-matrix.md`,
`helper-ledger.md`, `01-quire-capability-and-charter.md`,
`02-quire-sqlalchemy-engine.md`, `03-quire-fts-vector.md`,
`04-propstore-build-orchestration.md`, `05-source-and-diagnostics.md`,
`06-forms-concepts-parameterizations.md`, `07-contexts-lifting.md`,
`08-claims-active-claims.md`, `08a-typed-claim-graph-projection.md`.

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
11. `08a-typed-claim-graph-projection.md`.

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

- the model classes may live in the relation semantic owner, but the mapping
  source of truth is the existing Propstore world charter in
  `propstore/families/world_charters.py`;
- `relation_edge` is mapped explicitly with SQLAlchemy polymorphic mapping;
- `Stance` and `ConceptRelation` are declared on the `relation_edge` charter
  through Quire `CharterPolymorphicModel` metadata; do not create a parallel
  relation registry, local mapper, row DTO, or unchartered model layer;
- `ConflictWitness` is the model registered for the `conflict_witness` charter,
  not a separate wrapper around `ConflictWitnessRecord`;
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
uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --before reports/sqlalchemy-charter-parity/relations-stances-conflicts/before.sqlite --build-after sqlalchemy-charter --after reports/sqlalchemy-charter-parity/relations-stances-conflicts/after.sqlite --owner relations-stances-conflicts --workstream workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/09-relations-stances-conflicts.md --out reports/sqlalchemy-charter-parity/relations-stances-conflicts.json
```

Compare the captured projection baseline against the charter-generated sidecar
for this slice and compare:

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

## Phase 11 Execution Record

Recorded 2026-05-20.

- Generated relation identity metadata: commit `6581f945` marked the
  chartered `relation_edge.id` and `conflict_witness.id` fields as generated
  integer primary keys in `propstore/families/world_charters.py`. This keeps
  autoincrement identity in field metadata and SQLAlchemy instead of adding
  row-id constructors or restoring projection-row behavior. `uv run pyright
  propstore` passed with 0 errors, and focused logged pytest `powershell -File
  scripts/run_logged_pytest.ps1 -Label generated-relation-id
  tests/test_world_query.py::TestWorldQueryConstruction::test_construct_from_repo
  tests/test_world_query.py::TestAlgorithmWorldQuery::test_algorithm_value_of_single`
  passed with 2 tests and log
  `logs\test-runs\generated-relation-id-20260520-203640.log`.
- Deletion-first projection model removal: commit `2abd51c7` deleted
  `propstore/families/relations/projection_model.py` outright. The immediate
  `uv run pyright propstore` fallout was 15 errors, all caused by deleted
  projection-model imports or symbols in
  `propstore/aspic_bridge/extract.py`,
  `propstore/aspic_bridge/translate.py`,
  `propstore/core/analyzers.py`,
  `propstore/core/graph_build.py`,
  `propstore/families/concepts/declaration.py`,
  `propstore/families/relations/declaration.py`,
  `propstore/graph_export.py`, `propstore/relation_analysis.py`,
  `propstore/support_revision/af_adapter.py`, `propstore/world/atms.py`,
  `propstore/world/bound.py`, `propstore/world/overlay.py`, and
  `propstore/worldline/argumentation.py`. The repair queue is to replace those
  callers with typed `Stance`, `ConceptRelation`/`ConceptRelationship`, and
  `ConflictWitness`/`ConflictWitnessRecord` model access through Quire
  sessions and relation owners, not to restore a projection-model module,
  constants, row DTOs, coercers, or compatibility aliases.
- Required Quire capability repair: current Quire charter mapping has no
  charter-declared SQLAlchemy polymorphic model support. Phase 11 cannot
  truthfully map `Stance` and `ConceptRelation` through `relation_edge`
  polymorphism until Quire owns that generic capability. The next execution
  slice returns to Quire to add charter/schema/SQLAlchemy polymorphic mapping,
  then Propstore is pinned to the pushed Quire commit before relation callers
  are repaired.
- Quire capability repair completed: Quire commit
  `a506af4984f4a83d5e6d4752344a4bd59309492f` adds
  `CharterPolymorphicModel`, carries polymorphic declarations through schema
  IR/catalog hashing, maps single-table subclasses with SQLAlchemy
  `map_imperatively`, and proves querying the base relation table returns
  typed subclass instances. The commit was pushed to
  `github.com:ctoth/quire.git` on `master`. Quire gates passed:
  `uv run pyright` with 0 errors and `uv run pytest -vv` with 368 passed.
  Propstore `pyproject.toml` and `uv.lock` are pinned to that pushed Git SHA,
  not a local path.
- Propstore implementation correction: relation model cleanup must use that
  Quire polymorphic family infrastructure directly. The next Propstore slice
  must first update `propstore/families/world_charters.py` so the existing
  `relation_edge` charter maps the base relation edge plus `Stance` and
  `ConceptRelation` subclasses, and so the `conflict_witness` charter maps the
  final `ConflictWitness` model. Adding model-looking classes in the relation
  declaration file without charter registration is explicitly not a valid
  Phase 11 repair.
- Chartered relation model slice: `propstore/families/relations/declaration.py`
  now defines the relation semantic models `RelationEdge`, `Stance`,
  `ConceptRelation`, and `ConflictWitness`; `propstore/families/world_charters.py`
  registers `RelationEdge` as the `relation_edge` family model and maps
  `Stance`/`ConceptRelation` through Quire `CharterPolymorphicModel` on
  `source_kind`; `ConflictWitness` is registered directly for the
  `conflict_witness` family. The concept compiler now emits typed
  `ConceptRelation` objects for derived relation edges instead of relation
  projection rows. Targeted pyright for the three edited family files passed
  with 0 errors. Remaining work: remove the raw selector helpers still present
  in the relation owner, update named callers importing the deleted projection
  model, run package pyright, then continue through the old-path and parity
  gates.
- First caller fallout repair: commit `c567f152` updated ASPIC bridge callers
  and core store/analyzer protocols to use typed `Stance`, `ConceptRelation`,
  and `ConflictWitness` models directly instead of deleted
  `StanceRowInput`/`ConflictRowInput`/`RelationshipRowInput` types or
  relation projection-model coercers. Targeted pyright for
  `propstore/aspic_bridge/{extract,translate,build,query}.py`,
  `propstore/core/environment.py`, and `propstore/core/analyzers.py` passed
  with 0 errors. Remaining caller queue still includes graph/export,
  relation-analysis, support-revision, world, and worldline imports plus the
  raw selector helpers in the relation owner.
- Second caller fallout repair: commit `25d48c0a` updated
  `propstore/core/graph_build.py`, `propstore/graph_export.py`,
  `propstore/relation_analysis.py`, `propstore/merge/structured_merge.py`,
  and `propstore/worldline/argumentation.py` to consume typed relation models
  directly and remove deleted relation projection-model serialization/coercion
  calls. Targeted pyright for those five files passed with 0 errors.
  Remaining pyright/import queue is now concentrated in support-revision and
  world runtime callers, plus the relation-owner raw selector helpers and
  final old-path search gates.
- Coercion correction: the next support-revision/world runtime slice must
  delete the remaining `STANCE_ROW_MODEL.coerce` and `CONFLICT_ROW_MODEL.coerce`
  fallout by making the runtime APIs return typed relation models directly.
  Adding new `coerce`, `normalize`, row-dict, adapter, alias, or compatibility
  helpers is explicitly out of bounds for this phase.
- World/support runtime coercion deletion: commit `3b98068f` updated
  support-revision and world runtime callers so stance/conflict APIs carry
  typed `Stance`, `ConceptRelation`, and `ConflictWitness` objects directly.
  `WorldQuery` relation, stance, conflict, policy, stats, and explanation
  reads now use Quire SQLAlchemy session/model queries instead of relation
  selector helpers or projection-model coercion. `BoundWorld`,
  `OverlayWorld`, `ATMSEngine`, journal replay, and `ClaimView` now consume
  typed relation models without `STANCE_ROW_MODEL.coerce` or
  `CONFLICT_ROW_MODEL.coerce`. Targeted pyright for the edited runtime files
  passed with 0 errors. Next required gate is package pyright, followed by
  old-path searches and deletion of remaining raw selector helpers in the
  relation owner.
- Conflict warning-class typing repair: commit `4bc77c36` tightened
  `ConflictWitness` construction so stored warning/conflict classes are string
  model fields, detector output lowers enum values at the construction
  boundary, graph conflicts pass their existing typed string kind directly,
  and consistency reporting reads the typed field without `.value` or a
  coercion repair. Targeted pyright for
  `propstore/families/relations/declaration.py`, `propstore/world/bound.py`,
  `propstore/world/atms.py`, and `propstore/world/consistency.py` passed with
  0 errors. Next required gate remains package pyright, followed by old-path
  searches and deletion of remaining raw selector helpers in the relation
  owner.
- Package pyright gate after typed runtime repairs: `uv run pyright propstore`
  passed with 0 errors after commits `3b98068f` and `4bc77c36`. This is not
  phase completion because the required old-path searches and parity gate have
  not passed; the next execution queue is the Phase 11 search gates, starting
  with remaining relation owner helper/select/count surfaces.
- Old-path search gate status after package pyright: production hits remain
  for relation owner helper names in
  `propstore/families/relations/declaration.py` and build-plan imports/calls
  in `propstore/derived_build_plan.py`. Required deletions are
  `_optional_numeric`, `compile_authored_stance_sidecar_rows*`,
  `compile_claim_embedded_stance_sidecar_rows_with_diagnostics`,
  `select_stances_between`, `select_conflicts`, `select_all_relationships`,
  `select_all_claim_stances`, `select_explanation_stances`, and
  `count_conflicts`. Test hits remain for deleted row/projection vocabulary in
  `tests/test_world_query.py`, `tests/test_relate_opinions.py`,
  `tests/test_neighborhoods.py`, `tests/test_p_heavy.py`,
  `tests/test_relation_analysis.py`, and semantic-core/support-revision test
  doubles. The next production slice deletes/renames the relation owner
  helper names and updates `derived_build_plan.py`; tests are then repaired to
  use typed `Stance`, `ConceptRelation`, and `ConflictWitness` models directly.
- Repeated field-name repair rejection: the attempted local repair after
  deleting `_optional_numeric` repeated relation field names and constructor
  shape for resolution numeric fields. That edit was discarded before commit.
  The next production attempt must delete the old helper names while preserving
  field shape through the typed document/model boundary or Quire field
  metadata, not by recreating a field list in validation or kwargs assembly.
- Relation owner production helper deletion: commit `23d8ef2d` removed the
  production `_optional_numeric`, raw SQLite selector/count helpers,
  row-mapping constructors, and sidecar-row compiler names from
  `propstore/families/relations/declaration.py`. The embedded claim stance IR
  now carries typed claim `StanceDocument` objects instead of `dict` payloads,
  and `derived_build_plan.py` calls typed model compilers. Targeted pyright for
  `propstore/compiler/ir.py`,
  `propstore/families/claims/passes/__init__.py`,
  `propstore/families/relations/declaration.py`, and
  `propstore/derived_build_plan.py` passed with 0 errors. Search confirms the
  production old helper names are gone; `tests/test_relate_opinions.py` still
  references `compile_authored_stance_sidecar_rows` and is the next old-path
  test repair queue.
- Relation opinion test repair: commit `d28fee41` updated
  `tests/test_relate_opinions.py` to assert authored stance opinion fields at
  the typed `Stance` model boundary through
  `compile_authored_stance_models_with_diagnostics`, deleting the raw in-memory
  SQLite `claim_core`/`relation_edge` setup, `RELATION_EDGE_TABLE` import, and
  `populate_stances` use from that test file. The same commit removed the
  import-time cycle where `QuarantineDiagnostic` pulled in
  `world_charters.BuildDiagnostic` before relation models finished loading.
  Targeted pyright for
  `propstore/families/diagnostics/declaration.py` and
  `propstore/families/relations/declaration.py` passed with 0 errors. Focused
  logged pytest `powershell -File scripts/run_logged_pytest.ps1 -Label
  relate-opinions tests/test_relate_opinions.py` passed with 21 tests and log
  `logs\test-runs\relate-opinions-20260520-232747.log`. The next old-path
  queue is the remaining Phase 11 search hits outside
  `tests/test_relate_opinions.py`.
- Relation row test-surface deletion: commit `5610336e` removed the remaining
  test imports and uses of deleted relation projection vocabulary:
  `StanceRow`, `ConflictRow`, `StanceRowInput`, `ConflictRowInput`,
  `STANCE_ROW_MODEL`, `CONFLICT_ROW_MODEL`, `RELATION_EDGE_TABLE`, and
  `propstore.families.relations.projection_model`. Test stores now return
  typed `Stance` and `ConflictWitness` objects, and the touched runtime test
  fixtures use typed `Claim` objects instead of passing claim dictionaries
  into typed BoundWorld, ASPIC, graph, and worldline APIs. Package pyright
  `uv run pyright propstore` passed with 0 errors. Focused logged pytest
  `powershell -File scripts/run_logged_pytest.ps1 -Label
  relation-row-test-repair ...` passed with 246 tests and log
  `logs\test-runs\relation-row-test-repair-20260520-234025.log`. The full
  Phase 11 old-path search set for relation projection imports, row classes,
  storage-model constants, row-model constants, `_optional_numeric`,
  authored stance sidecar-row compiler names, raw selector helpers, and
  `count_conflicts` is now zero-hit in `propstore` and `tests`.
- Required gate fallout: `uv run pyright propstore` passed with 0 errors, but
  the required logged pytest gate `powershell -File
  scripts/run_logged_pytest.ps1 -Label relations-charter
  tests/test_graph_export.py tests/test_world_query.py tests/test_worldline.py`
  failed with 10 failures and 11 errors in
  `logs\test-runs\relations-charter-20260520-234452.log`. The gate exposed two
  typed-boundary issues: worldline fake stores still returned claim
  dictionaries where the typed runtime now requires `Claim` objects, and
  claim-artifact fixtures authored claims with `source_slug='test'` without
  authoring the matching canonical `source` artifact required by the
  SQLAlchemy FK. Commit `8d8a4c78` fixed the generic test fixture authoring
  boundary in `tests/family_helpers.py` so `claim_artifact_commit_payloads`
  writes the corresponding source artifact payload once. Remaining queue:
  repair `tests/test_worldline.py` fake stores to return typed `Claim` objects,
  rerun the required logged pytest gate, then continue to parity.
- Worldline typed-claim fixture repair: commit `52d5a2ff` updated
  `tests/test_worldline.py` fake world and bound-world fixtures so
  `ValueResult.claims`, `active_claims`, `claims_by_ids`, and `get_claim`
  return typed `Claim` objects built at the test boundary. This deletes the
  remaining worldline fake claim dictionaries exposed by the required gate
  without adding a production coercion, compatibility adapter, or dict repair
  path. The next required action is to rerun the `relations-charter` logged
  pytest gate.
- Remaining worldline typed-fixture repair: commit `0676d254` updated the
  remaining graph-projection, recency-liveness, and argumentation-liveness
  worldline test doubles so they return typed `Claim` and `Stance` objects
  instead of dictionaries. Dependency expectations now use the typed logical
  IDs produced by the claim model boundary. The required gate still exposed
  two production worldline issues to repair next: `WorldlineTargetValue`
  materialization drops typed algorithm claim payload fields, and chain target
  resolution still assumes non-derived results expose a direct `.value` field
  instead of reading typed `ValueResult` claims.
- Worldline typed payload repair: commit `20fb24c4` updated
  `propstore/worldline/resolution.py` so `WorldlineTargetValue`
  materialization reads statement, expression, name, algorithm body,
  canonical AST, and variables from typed `Claim` payload relationships, and
  chain target resolution reads typed `ValueResult` claims instead of
  assuming a row-like `.value` field. Targeted pyright
  `uv run pyright propstore/worldline/resolution.py` passed with 0 errors.
  The next required actions are package pyright and the `relations-charter`
  logged pytest gate.
- Required package and logged pytest gates passed after the worldline repair:
  `uv run pyright propstore` passed with 0 errors, and `powershell -File
  scripts/run_logged_pytest.ps1 -Label relations-charter
  tests/test_graph_export.py tests/test_world_query.py tests/test_worldline.py`
  passed with 211 tests and 29 warnings in
  `logs\test-runs\relations-charter-20260520-235932.log`. The next required
  Phase 11 queue is to rerun the old-path search gates and then the
  relations data-parity gate.
- Required old-path searches passed after the gate repair: all Phase 11
  `rg -n -F` searches for the deleted relation projection import path, row
  classes, storage-model constants, row-model constants, `_optional_numeric`,
  authored stance sidecar-row compiler names, raw selector helper names, and
  `count_conflicts` returned zero matches in the required `propstore` and
  `tests` scopes. The next required Phase 11 gate is the relations
  data-parity command.
- Relations data-parity gate passed: `uv run
  scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --before
  reports/sqlalchemy-charter-parity/relations-stances-conflicts/before.sqlite
  --build-after sqlalchemy-charter --after
  reports/sqlalchemy-charter-parity/relations-stances-conflicts/after.sqlite
  --owner relations-stances-conflicts --workstream
  workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/09-relations-stances-conflicts.md
  --out reports/sqlalchemy-charter-parity/relations-stances-conflicts.json`
  exited 0. The report has no failures; row counts, key sets, diagnostics,
  FTS, vector checks, and table schema checks all report `pass`. Phase 11 is
  complete.
