# 06 - Forms, Concepts, And Parameterizations Workstream

Date: 2026-05-18

## Goal

Cut forms, concepts, concept search, and parameterizations from the old
projection/read-model layer to Quire SQLAlchemy charters.

This workstream owns:

- forms closure before concept cutover;
- `propstore/form_utils.py` deletion after callers use the forms owner;
- form parsing and validation in `propstore/families/forms/stages.py`;
- the concept/form/parameterization slice;
- concept search over Quire/SQLAlchemy FTS;
- data parity for form, concept, alias, relationship, parameterization, FTS,
  and embedding-source results.

It does not own claims, relations, contexts, world-query conversion, concept
sidecar vector runtime migration, or generic Quire FTS/vector capability work.
Missing generic Quire FTS/vector capability blocks this workstream and returns
to Phases 1-4; it is not discovered or implemented here. Phase 11 owns
`propstore/families/concepts/sidecar_runtime.py`.

## Prerequisites

Complete the earlier cutover workstreams before starting implementation:

Required phase file prerequisites: `00-index.md`, `inventory-matrix.md`,
`helper-ledger.md`, `01-quire-capability-and-charter.md`,
`02-quire-sqlalchemy-engine.md`, `03-quire-fts-vector.md`,
`04-propstore-build-orchestration.md`, `05-source-and-diagnostics.md`.

1. Mechanical order check and current-state inventory confirmation.
2. Quire SQLAlchemy dependency and capability proof.
3. Quire charter/schema IR.
4. Quire SQLAlchemy table/mapping/session/catalog engine.
5. Quire FTS and vector implementation.
6. Propstore build orchestration cutover.
7. `05-source-and-diagnostics.md`.

No forms or concept production cutover starts until Quire can generate
charters, mappings, sessions, schema catalogs, JSON adapters, FTS declarations,
and vector hooks from the same schema IR used by the build orchestration.

Before implementation:

- reread `reports/code-inventory-2026-05-17.md`;
- reread `notes/architecture-wanted-outcome-2026-05-17.md`;
- confirm Propstore and Quire worktree states;
- confirm Propstore is pinned to a pushed Quire commit, never a local path;
- run or update the phase-order checker proving this workstream follows its
  prerequisites.

## Inventory Rows

| Inventory surface | Current owner | Final owner | Required action |
| --- | --- | --- | --- |
| `propstore/form_utils.py` | Duplicate form loading/parsing facade | `propstore/families/forms/stages.py` | Delete duplicate facade after callers use the family owner |
| `propstore/families/forms/stages.py` | Form semantic stage/loading owner | Form parsing/validation module plus form charter | Keep; expose form model data to Quire charter without duplicating parsing |
| `propstore/families/concepts/projection_model.py` | Concept row mapper | Concept charter plus Quire SQLAlchemy | Delete |
| `propstore/families/concepts/declaration.py` projection/query pieces | Concept sidecar compiler/query API | Concept semantics plus model queries | Delete generic projection/query plumbing |
| `propstore/parameterization_walk.py` | Parameterization traversal through row coercion | Parameterization traversal over typed models | Replace projection-model imports |
| `propstore/world/model.py` | Primary sidecar query facade over raw SQLite | Propstore `WorldQuery` over Quire read-only sessions | Replace concept/form selectors with model/session queries in this slice only |
| `propstore/world/queries.py` | World query helpers through projection rows | Typed world query helpers | Replace concept/form/parameterization projection-model imports in this slice only |

## Execution Rules

Execute deletion-first. Do not keep old and new form/concept production paths
in parallel.

Use this loop for each family slice:

1. Read the family inventory entry and current family files.
2. List every current production caller that imports or consumes projection
   rows, projection models, raw SQLite selectors, or generic helper layer.
3. Name the target charter/model classes in the phase notes or commit message.
4. Delete the old production projection/read-model surface first.
5. Run the smallest import/type/test command that exposes the next failures.
6. Fix only failures caused by the deletion in this workstream and the named
   caller list.
7. Replace raw SQLite access with Quire SQLAlchemy session/model access.
8. Replace loose dict/list/row payloads with typed model objects.
9. Delete field-specific coercers once generic charter conversion covers the
   field.
10. Run the family gates.
11. Run the old-path search gates.
12. Run the data-parity gate.
13. Commit only the current family slice when executing this workstream.
14. Reread this file before selecting the next slice.

Delete a helper when its body is a table-shaped `SELECT`, `COUNT`, `INSERT`,
`DELETE`, row attachment, row coercion, or projection-model wrapper with no
Propstore semantic policy. Keep and move semantic code when it owns concept-id
precedence, alias resolution, form/unit validation, authored-document identity,
or parameterization dimensional semantics. After moving kept semantics, delete
the original helper-shaped production path.

Explicitly disallowed replacement shapes:

- Do not replace a deleted declaration-level selector with a private
  `WorldQuery` method that has the same selector shape, such as
  `_concept_by_id`, `_concept_count`, `_concept_registry_rows`,
  `_build_concept_logical_id_index`, `_parameterizations_for_output_concept`,
  or equivalent names.
- Do not replace a deleted free function with a same-body class method,
  static method, app helper, owner helper, or differently named wrapper whose
  only job is a table-shaped `SELECT`, `COUNT`, row coercion, or generic
  projection of SQLAlchemy model rows.
- For one-off data access, put the Quire SQLAlchemy session query directly in
  the public owner-layer method that owns the behavior.
- If the behavior is reused because it is semantic policy, move only that
  policy to the named semantic owner module from this workstream; do not carry
  the old raw-selector body with it.
- Existing public owner methods such as `WorldQuery.get_concept`,
  `WorldQuery.resolve_concept`, `WorldQuery.resolve_alias`,
  `WorldQuery.all_concepts`, `WorldQuery.parameterizations_for`,
  `WorldQuery.group_members`, and `WorldQuery.stats` are the allowed surface;
  they must query typed SQLAlchemy models directly or call a true semantic
  owner, not a renamed selector helper.

## Slice Order

Execute in this order:

1. Forms closure.
2. `form_utils.py` caller migration and deletion.
3. Concept/form/parameterization model cutover.
4. Concept search cutover.
5. Data parity, search gates, and final completion gates.

## Forms Closure

Target model names:

- `Form`
- `FormAlgebra`

Keep:

- form semantic passes;
- dimensional validation;
- Bridgman/Sympy dimensional logic;
- form document authoring shape;
- `propstore/families/forms/stages.py` as the semantic stage/loading owner.

Delete:

- form projection table declarations embedded in concept declaration modules;
- raw form-row dictionaries;
- selectors that only wrap generic SQL selects;
- `propstore/form_utils.py` after callers use the forms family owner.

Named caller/update surfaces:

- `propstore/app/forms.py`;
- `propstore/form_utils.py`;
- `propstore/families/forms/stages.py`;
- `propstore/families/concepts/declaration.py`;
- `propstore/world/model.py`.

Forms gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label forms-charter tests/test_form_algebra.py tests/test_required_schema_completeness.py tests/test_fixture_schema_parity.py
rg -n -F -- "FORM_PROJECTION" propstore tests
rg -n -F -- "FORM_ALGEBRA_PROJECTION" propstore tests
rg -n -F -- "ProjectionTable(" propstore/families/concepts propstore/families/forms tests
rg -n -F -- "propstore.form_utils" propstore tests
```

All searches are zero-hit gates outside notes, workstreams, docs, and reports.

## Concept, Form, And Parameterization Slice

The inventory identifies `propstore/families/concepts/declaration.py` and
`propstore/families/concepts/projection_model.py` as the main concept sidecar
boundary and duplicate row mapping layer.

Target model names:

- `Concept`
- `ConceptAlias`
- `ConceptRelationship`
- `Parameterization`
- `ParameterizationGroup`
- `FormAlgebra`

Deletion-first targets:

- `propstore/families/concepts/projection_model.py`;
- `ConceptRow`;
- `ParameterizationRow`;
- `CONCEPT_ROW_MODEL`;
- `PARAMETERIZATION_ROW_MODEL`;
- `CONCEPT_PROJECTION`;
- `CONCEPT_FTS_PROJECTION`;
- `PARAMETERIZATION_PROJECTION`;
- `ALIAS_PROJECTION`;
- `PARAMETERIZATION_GROUP_PROJECTION`;
- `RELATIONSHIP_PROJECTION`;
- concept projection codecs;
- concept search/select/count/id-resolution helpers whose only job is generic
  SQL selection;
- `_nullable_text`;
- concept id/status/exactness projection codecs;
- logical id JSON render-view helpers that generic schema conversion replaces.

Named caller/update surfaces:

- `propstore/app/concept_views.py`;
- `propstore/app/concepts/display.py`;
- `propstore/app/concepts/embedding.py`;
- `propstore/core/graph_build.py`;
- `propstore/fragility_contributors.py`;
- `propstore/graph_export.py`;
- `propstore/parameterization_walk.py`;
- `propstore/sensitivity.py`;
- `propstore/world/model.py`;
- `propstore/world/queries.py`;
- `propstore/world/bound.py`;
- `propstore/world/overlay.py`;
- `propstore/world/atms.py`;
- `propstore/worldline/resolution.py`.

Keep in exact target modules/functions:

- concept normalization in `propstore/families/concepts/stages.py`;
- concept identity in `propstore/families/identity/concepts.py`;
- concept semantic passes in `propstore/families/concepts/passes.py`;
- form parameter validation in `propstore/families/forms/stages.py`;
- relationship target validation in `propstore/families/concepts/stages.py`;
- parameterization dimensional checks in `propstore/families/concepts/stages.py`;
- CEL registry building from typed `Concept` objects in
  `propstore/compiler/context.py::build_authored_concept_registry`;
- concept handle/alias resolution policy in
  `propstore/families/concepts/declaration.py::resolve_concept_id`;
- concept logical-id precedence/index semantics in
  `propstore/families/identity/concepts.py`;
- concept symbol-candidate semantics in
  `propstore/families/concepts/stages.py::concept_symbol_candidates`.

Relationships:

- `Concept.aliases: list[ConceptAlias]`;
- `Concept.relationships: list[ConceptRelationship]`;
- `Concept.parameterizations_as_output: list[Parameterization]`;
- `Parameterization.inputs` as typed relationships or explicit link objects;
- `ParameterizationGroup.members` as typed concept membership.

FTS/search requirements:

- FTS schema is generated through Quire/SQLAlchemy extension declarations;
- app `search_concepts` keeps presentation/report ownership;
- concept family keeps only semantic search result mapping;
- raw FTS SQL is replaced by Quire/SQLAlchemy FTS query APIs;
- `CONCEPT_FTS_PROJECTION` is deleted; the concept charter declares FTS
  fields once and Quire generates the FTS storage/query surface;
- SQLite/FTS syntax classification moves to Quire FTS adapter;
- the concept owner maps Quire FTS syntax failures to
  `ConceptSearchQuerySyntaxError`.

Concept sidecar runtime ownership:

- Phase 11 owns `propstore/families/concepts/sidecar_runtime.py`,
  `find_similar_concept_rows`, and Quire vector/session runtime migration.
- This phase owns concept declaration/search/model semantics that Phase 11's
  runtime APIs consume.

## Helper Classification

File: `propstore/families/concepts/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `ConceptRelationshipProjectionRow` | delete | Replace with typed `ConceptRelationship`/relation model. |
| `ConceptSidecarRows` | delete | Replace with typed write plan/session adds. |
| `_concept_symbol_candidates` | move | Move symbol-candidate semantics to `propstore/families/concepts/stages.py::concept_symbol_candidates`; reuse that exact function from conflict detection and world value resolution. |
| `compile_concept_sidecar_rows` | replace | Replace with typed concept/form/alias/relationship/parameterization model construction. |
| `_compile_form_algebra_rows` | move | Move form algebra semantics to `propstore/families/forms/stages.py::compile_form_algebra`; delete row helper. |
| `ConceptRow` | delete | Replace with `Concept` model. |
| `ConceptEmbeddingSource` | replace | Replace with typed embedding source projection over `Concept` model. |
| `ParameterizationRow` | delete | Replace with `Parameterization` model. |
| `populate_concept_sidecar_rows` | delete | Replace with SQLAlchemy session add/flush through Quire build session. |
| `ConceptSearchQuerySyntaxError` | move | Move to concept search owner as the domain error raised by Quire/SQLAlchemy FTS query adapters. |
| `_is_concept_search_syntax_error` | move | Move SQLite/FTS syntax classification to Quire FTS adapter; concept search owner maps it to `ConceptSearchQuerySyntaxError`. |
| `fetch_concept_search_hits` | replace | Replace raw FTS SQL with Quire/SQLAlchemy FTS query API; keep presentation mapping in app layer. |
| `fetch_concept_search_hits_from_sidecar` | delete | Direct sidecar path opening is deleted; callers use Quire sessions. |
| `select_concept_by_id` | replace | Replace with SQLAlchemy session query. |
| `select_all_concepts` | replace | Replace with SQLAlchemy session query. |
| `select_concept_embedding_sources` | replace | Replace with typed embedding source query over `Concept` model. |
| `resolve_concept_embedding_entity` | move | Move concept-handle resolution policy to concept owner; implement through session query. |
| `select_aliases_by_concept_id` | replace | Replace with `Concept.aliases` relationship query. |
| `select_concept_registry_rows` | replace | Replace with typed registry projection from `Concept` models. |
| `build_concept_logical_id_index` | move | Move logical-id precedence/index semantics to concept owner; implement over typed models. |
| `resolve_concept_alias` | move | Move alias resolution policy to concept owner; implement over `Concept.aliases`. |
| `resolve_concept_id` | move | Move id/alias/logical/canonical precedence policy to concept owner; implement over typed models. |
| `select_concept_ids_for_group` | replace | Replace with `ParameterizationGroup.members` relationship. |
| `select_parameterizations_for_output_concept` | replace | Replace with `Concept.parameterizations_as_output` relationship. |
| `select_all_parameterizations` | replace | Replace with SQLAlchemy session query. |
| `select_parameterization_group_members` | replace | Replace with `ParameterizationGroup.members` relationship. |
| `select_all_form_rows` | replace | Replace with typed `Form` model query. |
| `select_form_algebra_rows_for_output` | replace | Replace with typed `FormAlgebra` model query. |
| `select_all_form_algebra_rows` | replace | Replace with typed `FormAlgebra` model query. |
| `search_concept_ids` | replace | Replace raw FTS SQL with Quire/SQLAlchemy FTS query API. |
| `count_concepts` | replace | Replace with SQLAlchemy count query through concept owner. |
| `resolve_sidecar_concept_id` | move | Move handle-resolution policy to concept owner; delete raw sidecar helper. |

Files: `propstore/families/concepts/projection_model.py` and concept-side
projection helpers.

| Helper family | Classification | Required final owner/action |
| --- | --- | --- |
| nullable scalar codecs such as `_nullable_text`, `_nullable_int`, `_nullable_float`, `_optional_float`, `_optional_int` | delete | Quire charter conversion owns generic scalar/null handling. |
| id coercion codecs such as `_concept_id` | delete | SQLAlchemy mapped model fields use typed id constructors at model/document boundaries. |
| enum value codecs such as `_concept_status_value` and `_exactness_value` | delete | Enum storage adapters are generic Quire SQLAlchemy adapters. |
| JSON/render helpers such as `_logical_ids_payload`, `_logical_ids_from_value`, `_logical_ids_to_columns`, and `_logical_ids_from_columns` | replace | Replace with typed value objects and Quire JSON adapter; semantic payload rendering moves to document/view boundaries. |

## Data-Parity Gate

```powershell
uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --before reports/sqlalchemy-charter-parity/forms-concepts-parameterizations/before.sqlite --build-after sqlalchemy-charter --after reports/sqlalchemy-charter-parity/forms-concepts-parameterizations/after.sqlite --owner forms-concepts-parameterizations --workstream workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/06-forms-concepts-parameterizations.md --out reports/sqlalchemy-charter-parity/forms-concepts-parameterizations.json
```

Compare the captured projection baseline against the charter-generated sidecar
for each slice in this workstream.

Compare:

- form and form-algebra table names, primary keys, row counts, and key sets;
- concept, alias, relationship, parameterization, and parameterization-group
  table names, primary keys, row counts, and key sets;
- form owner query outputs for typed `Form` listing,
  `FormAlgebra` lookup by output form, and typed `FormAlgebra` listing
  over the fixtures exercised by `tests/test_sidecar_form_projection.py` and
  `tests/test_sidecar_form_algebra_projection.py`;
- concept owner query outputs for `Concept` lookup by id,
  full concept listing, `Concept.aliases`, typed concept registry projection,
  `build_concept_logical_id_index`, `resolve_concept_alias`, and
  `resolve_concept_id` over the fixtures
  exercised by `tests/test_sidecar_concept_projection.py`,
  `tests/test_sidecar_alias_projection.py`, and `tests/test_concept_views.py`;
- parameterization traversal results;
- concept FTS hit sets;
- concept embedding source rows and entity resolution results;
- exact column and table names.

Fail the phase when a row, key, FTS hit, embedding-source row, vector entity,
or semantic query result disappears. The only accepted disappearance is a
table, helper, or column already named as a deletion target in this file.

Accepted parity difference allowlist:

- deleted form, form-algebra, concept, alias, relationship, parameterization,
  parameterization-group, FTS, vector, row, codec, table-helper, and raw
  selector surfaces named in this file's deletion targets;
- no column rename, table rename, row disappearance, key disappearance,
  FTS-result disappearance, embedding-source disappearance, vector-entity
  disappearance, or semantic-query disappearance is allowed.

## Required Gates

Run the forms gates before the concept slice:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label forms-charter tests/test_form_algebra.py tests/test_required_schema_completeness.py tests/test_fixture_schema_parity.py
rg -n -F -- "FORM_PROJECTION" propstore tests
rg -n -F -- "FORM_ALGEBRA_PROJECTION" propstore tests
rg -n -F -- "ProjectionTable(" propstore/families/concepts propstore/families/forms tests
rg -n -F -- "propstore.form_utils" propstore tests
```

Run the concept gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label concept-charter tests/test_required_schema_completeness.py tests/test_fixture_schema_parity.py tests/test_render_time_filtering.py
```

Run concept old-path searches:

```powershell
rg -n -F -- "propstore.families.concepts.projection_model" propstore tests
rg -n -F -- "ConceptRow" propstore tests
rg -n -F -- "ParameterizationRow" propstore tests
rg -n -F -- "CONCEPT_ROW_MODEL" propstore tests
rg -n -F -- "PARAMETERIZATION_ROW_MODEL" propstore tests
rg -n -F -- "CONCEPT_PROJECTION" propstore tests
rg -n -F -- "CONCEPT_FTS_PROJECTION" propstore tests
rg -n -F -- "PARAMETERIZATION_PROJECTION" propstore tests
rg -n -F -- "ALIAS_PROJECTION" propstore tests
rg -n -F -- "PARAMETERIZATION_GROUP_PROJECTION" propstore tests
rg -n -F -- "RELATIONSHIP_PROJECTION" propstore tests
rg -n -F -- "_nullable_text" propstore/families/concepts tests
rg -n -F -- "fetch_concept_search_hits_from_sidecar" propstore tests
rg -n -F -- "select_concept_by_id" propstore tests
rg -n -F -- "select_all_concepts" propstore tests
rg -n -F -- "select_concept_embedding_sources" propstore tests
rg -n -F -- "select_parameterizations_for_output_concept" propstore tests
rg -n -F -- "select_parameterization_group_members" propstore tests
rg -n -F -- "select_all_form_rows" propstore tests
rg -n -F -- "select_all_form_algebra_rows" propstore tests
```

All searches are zero-hit gates outside notes, workstreams, docs, and reports.

## Completion Gate

This workstream is complete only when:

- `Form` and `FormAlgebra` are mapped through Quire SQLAlchemy charters;
- form parsing and validation remains in `propstore/families/forms/stages.py`;
- `propstore/form_utils.py` is deleted and its callers use the forms owner;
- `Concept`, `ConceptAlias`, `ConceptRelationship`, `Parameterization`,
  `ParameterizationGroup`, and `FormAlgebra` reads/writes are mapped through
  Quire SQLAlchemy charters;
- concept build writes use Quire writable sessions and typed write plans;
- concept search uses Quire/SQLAlchemy FTS APIs;
- concept sidecar runtime ownership is handed to Phase 11 and is not a
  completion criterion for this phase;
- concept handle, alias, logical-id, form validation, and parameterization
  semantics are preserved in owner modules;
- all deletion targets in this file are gone from production code;
- forms and concept/parameterization data parity passes;
- required pyright, pytest, and search gates pass.

## Phase 7-8 Execution Record

Recorded 2026-05-20.

Prerequisites:

- Reread `reports/code-inventory-2026-05-17.md`; it remains the controlling
  inventory for the forms/concepts/parameterizations slice.
- Reread `notes/architecture-wanted-outcome-2026-05-17.md`; it says Quire
  owns the generic charter/schema engine, SQLAlchemy mapping/session
  machinery, schema catalog, FTS/vector hooks, and query/index mechanics,
  while Propstore owns form/concept/parameterization semantics.
- Propstore current branch: `master`; tracked task-owned files clean before
  Phase 7-8 edits; unrelated untracked files present.
- Quire current branch: `master`; tracked files clean; unrelated untracked
  notes/reports/prompts/reviews paths present.
- Order checker passed:
  `uv run scripts/check_workstream_order.py workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/00-index.md`
  returned `workstream order ok`.
- Quire pin: `pyproject.toml` and `uv.lock` resolve `quire` from pushed commit
  `65df665b85053c1741dcd22d3a12deb15f35a4be`.
- Local dependency-pin searches for `path =`, `workspace = true`,
  `quire @ file`, `quire @ ..`, and `quire @ C:` returned no hits.

Forms closure:

- Current old-path inventory before forms edits found `FORM_PROJECTION` and
  `FORM_ALGEBRA_PROJECTION` only in `propstore/families/concepts/declaration.py`
  and form projection tests, and found `propstore.form_utils` imports in
  production/test callers.
- Added typed `Form` and `FormAlgebra` model construction to
  `propstore/families/forms/stages.py` and kept form parsing, cache, unit,
  dimension, and form-algebra semantic logic in the forms owner.
- Moved concept symbol-candidate semantics to
  `propstore/families/concepts/stages.py::concept_symbol_candidates` for the
  form-algebra compiler.
- Deleted `FORM_PROJECTION`, `FORM_ALGEBRA_PROJECTION`, form projection row
  construction, and form raw selector helpers from
  `propstore/families/concepts/declaration.py`.
- Updated `propstore/families/world_charters.py` so the `form` and
  `form_algebra` charters map the forms-owner `Form` and `FormAlgebra`
  classes.
- Updated `WorldQuery` form methods to read typed form and form-algebra models
  through Quire SQLAlchemy read-only sessions.
- Migrated production and test imports from `propstore.form_utils` to
  `propstore.families.forms.stages`, then deleted `propstore/form_utils.py`.
- Focused forms pyright passed:
  `uv run pyright propstore/families/forms/stages.py propstore/families/concepts/stages.py propstore/families/concepts/declaration.py propstore/families/world_charters.py propstore/world/model.py propstore/app/forms.py`
  returned 0 errors.
- Focused forms closure pytest passed:
  `powershell -File scripts/run_logged_pytest.ps1 -Label forms-closure-focused tests/test_form_utils.py tests/test_sidecar_form_projection.py tests/test_sidecar_form_algebra_projection.py tests/test_form_algebra.py`
  returned `66 passed`; log:
  `logs/test-runs/forms-closure-focused-20260520-123400.log`.
- Form-specific old-path searches for `FORM_PROJECTION`,
  `FORM_ALGEBRA_PROJECTION`, and `propstore.form_utils` returned zero hits.
- The broad forms gate search `ProjectionTable(` under
  `propstore/families/concepts` still finds concept, alias, relationship, and
  parameterization projection tables. Those are the next slice's named
  deletion targets in this same workstream.

Concept/form/parameterization model cutover correction:

- During the initial concept model cutover, the attempted top-level helpers
  `coerce_concept`, `concept_to_mapping`, `coerce_parameterization`, and
  `parameterization_to_mapping` were identified as duplicate projection-model
  wrapper helpers, not the target architecture.
- The required correction is deletion-first: remove those attempted helpers,
  delete `CONCEPT_ROW_MODEL` and `PARAMETERIZATION_ROW_MODEL`, and update
  callers to consume typed `Concept` and `Parameterization` models directly.
- Remaining IO-boundary conversion must live on the boundary-specific model
  constructors/methods such as `Concept.from_row_mapping`,
  `Concept.to_row_mapping`, `Parameterization.from_row_mapping`, and
  `Parameterization.to_row_mapping` only where a row-mapping boundary still
  exists during the slice.
- Internal concept, world, traversal, registry, and view code must not use
  top-level per-model wrapper helpers as a replacement for the deleted
  projection model layer.

Concept projection-model deletion and wrapper cleanup:

- Removed the attempted top-level concept/parameterization wrapper helpers
  from `propstore/families/concepts/declaration.py`.
- Deleted `propstore/families/concepts/projection_model.py`.
- Updated concept and parameterization callers to use `Concept.coerce`,
  `Concept.to_row_mapping`, `Parameterization.coerce`, and
  `Parameterization.to_row_mapping` directly instead of
  `CONCEPT_ROW_MODEL`, `PARAMETERIZATION_ROW_MODEL`, or replacement wrapper
  helpers.
- Updated the affected production/test caller set:
  `propstore/app/world_reasoning.py`, `propstore/core/graph_build.py`,
  `propstore/fragility_contributors.py`, `propstore/graph_export.py`,
  `propstore/parameterization_walk.py`, `propstore/sensitivity.py`,
  `propstore/world/assignment_selection_policy.py`, `propstore/world/atms.py`,
  `propstore/world/bound.py`, `propstore/world/consistency.py`,
  `propstore/world/model.py`, `propstore/world/overlay.py`,
  `propstore/world/queries.py`, `propstore/worldline/resolution.py`, and
  `tests/test_world_query.py`.
- Old-path searches for `propstore.families.concepts.projection_model`,
  `ConceptRow`, `ParameterizationRow`, `CONCEPT_ROW_MODEL`, and
  `PARAMETERIZATION_ROW_MODEL` returned zero hits in `propstore` and `tests`.
- Focused pyright passed:
  `uv run pyright propstore/families/concepts/declaration.py propstore/core/graph_build.py propstore/world/assignment_selection_policy.py propstore/world/bound.py propstore/world/model.py propstore/world/consistency.py propstore/fragility_contributors.py propstore/parameterization_walk.py propstore/graph_export.py propstore/sensitivity.py propstore/worldline/resolution.py propstore/world/atms.py propstore/world/overlay.py propstore/world/queries.py propstore/app/world_reasoning.py`
  returned 0 errors.
- Package pyright passed:
  `uv run pyright propstore` returned 0 errors.
- Focused logged pytest passed:
  `powershell -File scripts/run_logged_pytest.ps1 -Label concept-model-helper-cleanup tests/test_world_query.py tests/test_cel_checker.py tests/test_concept_views.py tests/test_neighborhoods.py`
  returned `224 passed, 29 warnings`; log:
  `logs/test-runs/concept-model-helper-cleanup-20260520-124711.log`.

Concept typed write-model cutover:

- Replaced `ConceptSidecarRows` with `ConceptWriteModels`.
- Added typed SQLAlchemy-mapped write models `ConceptAlias`,
  `ConceptRelationship`, and `ParameterizationGroup`, and mapped
  `concept`, `alias`, `relationship`, `parameterization`, and
  `parameterization_group` charters to the concept-owner model classes.
- Updated `compile_concept_sidecar_rows` to emit typed models for concept,
  alias, relationship, parameterization, and parameterization-group writes.
- Deleted the old concept-family `ProjectionTable` declarations:
  `CONCEPT_PROJECTION`, `ALIAS_PROJECTION`, `RELATIONSHIP_PROJECTION`,
  `PARAMETERIZATION_PROJECTION`, and `PARAMETERIZATION_GROUP_PROJECTION`.
- Deleted `CONCEPT_FTS_PROJECTION`; the FTS declaration now lives only in the
  Quire SQLAlchemy charter in `propstore/families/world_charters.py`.
- Deleted `populate_concept_sidecar_rows`; concept writes now flow through the
  existing Quire SQLAlchemy write batches in `derived_build_plan.py` and
  `derived_build.py`.
- Replaced projection-table tests with SQLAlchemy model round-trip tests for
  concept, alias, parameterization, parameterization-group, relation-edge,
  form, and form-algebra write models.
- Old-path searches for `ConceptSidecarRows`,
  `populate_concept_sidecar_rows`, `CONCEPT_PROJECTION`, `ALIAS_PROJECTION`,
  `RELATIONSHIP_PROJECTION`, `PARAMETERIZATION_PROJECTION`,
  `PARAMETERIZATION_GROUP_PROJECTION`, `CONCEPT_FTS_PROJECTION`, and
  `ProjectionTable(` under `propstore/families/concepts` plus the updated
  sidecar tests returned zero hits.
- Package pyright passed:
  `uv run pyright propstore` returned 0 errors.
- Focused logged pytest passed:
  `powershell -File scripts/run_logged_pytest.ps1 -Label concept-write-models tests/test_sidecar_concept_projection.py tests/test_sidecar_alias_projection.py tests/test_sidecar_parameterization_projection.py tests/test_sidecar_parameterization_group_projection.py tests/test_sidecar_relation_edge_projection.py tests/test_sidecar_form_projection.py tests/test_sidecar_form_algebra_projection.py`
  returned `7 passed`; log:
  `logs/test-runs/concept-write-models-20260520-125547.log`.

Remaining concept read/session/search cutover queue:

- Completed `WorldQuery` concept and parameterization read cutover to Quire
  SQLAlchemy read-only sessions over typed `Concept`, `ConceptAlias`,
  `Parameterization`, and `ParameterizationGroup` models directly inside the
  owner methods that own the reads.
- Deleted declaration-owned raw selector helpers whose `WorldQuery` callers
  now use typed model queries directly:
  `select_concept_by_id`, `select_all_concepts`,
  `select_concept_registry_rows`, `build_concept_logical_id_index`,
  `resolve_concept_alias`, `resolve_concept_id`,
  `select_concept_ids_for_group`,
  `select_parameterizations_for_output_concept`,
  `select_all_parameterizations`, `select_parameterization_group_members`,
  `search_concept_ids`, and `count_concepts`.
- Did not replace those selectors with private `WorldQuery` selector methods.
  Searches for `_concept_by_id`, `_concept_registry_rows`, and
  `to_concept_id(hit.entity_id)` returned zero hits in `propstore` and
  `tests`; `_concept_count` has no production helper hit.
- Corrected the FTS identity smell in `WorldQuery.search`: FTS entity ids are
  used only as lookup keys to fetch typed `Concept` models, and the returned
  `ConceptSearchHit` uses `Concept.concept_id` instead of manually converting
  `hit.entity_id`.
- Focused pyright passed:
  `uv run pyright propstore/world/model.py propstore/families/concepts/declaration.py propstore/core/graph_build.py`
  returned 0 errors.
- Focused logged pytest passed:
  `powershell -File scripts/run_logged_pytest.ps1 -Label concept-worldquery-sessions tests/test_world_query.py tests/test_cel_checker.py tests/test_concept_views.py tests/test_neighborhoods.py`
  returned `224 passed, 29 warnings`; log:
  `logs/test-runs/concept-worldquery-sessions-20260520-131346.log`.
- Added generic Quire FTS syntax classification in pushed Quire commit
  `52312677995eb27f7c72dffb265f8efabacd17bf` and pinned Propstore to that
  pushed commit in `pyproject.toml` and `uv.lock`.
- Replaced app concept search with Quire `search_fts_index` through the
  materialized `DerivedStoreHandle` read-only session. App search now fetches
  typed `Concept` models and maps presentation results from those typed
  objects; it no longer calls a sidecar-opening concept declaration helper or
  maps raw result dictionaries.
- Deleted `fetch_concept_search_hits`, `fetch_concept_search_hits_from_sidecar`,
  and the SQLite-specific `_is_concept_search_syntax_error` helper from
  `propstore/families/concepts/declaration.py`.
- Replaced declaration-level concept embedding source selection with typed
  `Concept` and `ConceptAlias` SQLAlchemy model queries in the embedding
  owner. `SidecarConceptEmbeddingStore` now receives the `DerivedStoreHandle`
  and uses read-only sessions for concept source text and concept entity
  resolution.
- Replaced concept sidecar-runtime concept-handle resolution with
  `WorldQuery.resolve_concept`, then deleted the unused raw
  `resolve_sidecar_concept_id` helper.
- Deleted `select_aliases_by_concept_id`,
  `select_concept_embedding_sources`, and
  `resolve_concept_embedding_entity`; searches for those names, for
  `fetch_concept_search_hits`, and for `resolve_sidecar_concept_id` returned
  zero hits in `propstore` and `tests`.
- Focused pyright passed:
  `uv run pyright propstore/app/concepts/display.py propstore/app/concepts/embedding.py propstore/families/concepts/declaration.py propstore/families/concepts/sidecar_runtime.py propstore/families/embeddings/declaration.py propstore/world/model.py tests/test_concept_workflows.py`
  returned 0 errors.
- Focused logged pytest passed:
  `powershell -File scripts/run_logged_pytest.ps1 -Label concept-search-embedding-cleanup tests/test_concept_workflows.py tests/test_world_query.py tests/test_concept_views.py tests/test_neighborhoods.py`
  returned `162 passed, 29 warnings`; log:
  `logs/test-runs/concept-search-embedding-cleanup-20260520-134919.log`.
- Phase 11 still owns `propstore/families/concepts/sidecar_runtime.py`,
  `find_similar_concept_rows`, and the vector runtime, but this workstream
  still owns deletion or relocation of declaration-level concept embedding
  source selectors named in the helper table.
