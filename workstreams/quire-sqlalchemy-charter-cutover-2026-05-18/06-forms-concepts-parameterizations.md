# 06 - Forms, Concepts, And Parameterizations Workstream

Date: 2026-05-18

## Goal

Cut forms, concepts, concept search, concept sidecar runtime, and
parameterizations from the old projection/read-model layer to Quire
SQLAlchemy charters.

This workstream owns:

- forms closure before concept cutover;
- `propstore/form_utils.py` deletion after callers use the forms owner;
- `propstore/families/forms/stages.py` as the form semantic owner;
- the concept/form/parameterization slice;
- concept search over Quire/SQLAlchemy FTS;
- data parity for form, concept, alias, relationship, parameterization, FTS,
  embedding-source, and concept runtime query results.

It does not own claims, relations, contexts, world-query conversion, concept
sidecar vector runtime migration, or generic Quire FTS/vector capability work
except where a gate exposes a missing prerequisite. Phase 11 owns
`propstore/families/concepts/sidecar_runtime.py`.

## Prerequisites

Complete the earlier cutover workstreams before starting implementation:

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
| `propstore/families/forms/stages.py` | Form semantic stage/loading owner | Form semantic owner plus form charter | Keep; expose form model data to Quire charter without duplicating parsing |
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

## Slice Order

Execute in this order:

1. Forms closure.
2. `form_utils.py` caller migration and deletion.
3. Concept/form/parameterization model cutover.
4. Concept search cutover.
5. Concept sidecar runtime cutover.
6. Data parity, search gates, and final completion gates.

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

Keep as semantic owner code:

- concept normalization and identity in `stages.py`;
- concept semantic passes;
- form parameter validation;
- relationship target validation;
- parameterization dimensional checks;
- CEL registry building from typed `Concept` objects;
- concept handle/alias resolution policy;
- concept logical-id precedence/index semantics;
- concept symbol-candidate semantics in the concept/form-algebra owner.

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
| `_concept_symbol_candidates` | move | Move symbol-candidate semantics to concept/form-algebra owner; reuse the same owner from conflict detection and world value resolution. |
| `compile_concept_sidecar_rows` | replace | Replace with typed concept/form/alias/relationship/parameterization model construction. |
| `_compile_form_algebra_rows` | move | Move form algebra semantics to form/concept semantic owner; delete row helper. |
| `ConceptRow` | delete | Replace with `Concept` model. |
| `ConceptEmbeddingSource` | replace | Replace with typed embedding source projection over `Concept` model. |
| `ParameterizationRow` | delete | Replace with `Parameterization` model. |
| `populate_concept_sidecar_rows` | delete | Replace with SQLAlchemy session add/flush through Quire build session. |
| `ConceptSearchQuerySyntaxError` | move | Move to concept search owner as the domain error raised by Quire/SQLAlchemy FTS query adapters. |
| `_is_concept_search_syntax_error` | move | Move SQLite/FTS syntax classification to Quire FTS adapter; concept search owner maps it to `ConceptSearchQuerySyntaxError`. |
| `fetch_concept_search_hits` | replace | Replace raw FTS SQL with Quire/SQLAlchemy FTS query API; keep presentation mapping in app layer. |
| `fetch_concept_search_hits_from_sidecar` | delete | Direct sidecar path opening is deleted; callers use Quire sessions. |
| `find_similar_concept_rows` | delete | Replace row-shaped vector helper with concept owner API over Quire vector/session APIs. |
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
uv run scripts/compare_sqlalchemy_charter_parity.py --before <old-sidecar.sqlite> --after <new-sidecar.sqlite> --owner forms-concepts-parameterizations --out reports/sqlalchemy-charter-parity/forms-concepts-parameterizations.json
```

Build the sidecar from the same repository snapshot before and after each
slice in this workstream.

Compare:

- form and form-algebra table names, primary keys, row counts, and key sets;
- concept, alias, relationship, parameterization, and parameterization-group
  table names, primary keys, row counts, and key sets;
- form owner query outputs for `select_all_form_rows`,
  `select_form_algebra_rows_for_output`, and `select_all_form_algebra_rows`
  over the fixtures exercised by `tests/test_sidecar_form_projection.py` and
  `tests/test_sidecar_form_algebra_projection.py`;
- concept owner query outputs for `select_concept_by_id`,
  `select_all_concepts`, `select_aliases_by_concept_id`,
  `select_concept_registry_rows`, `build_concept_logical_id_index`,
  `resolve_concept_alias`, and `resolve_concept_id` over the fixtures
  exercised by `tests/test_sidecar_concept_projection.py`,
  `tests/test_sidecar_alias_projection.py`, and `tests/test_concept_views.py`;
- parameterization traversal results;
- concept FTS hit sets;
- concept embedding source rows and entity resolution results;
- accepted column/table renames, explicitly listed in the commit message.

Fail the phase when a row, key, FTS hit, embedding-source row, vector entity,
or semantic query result disappears. The only accepted disappearance is a
table, helper, or column already named as a deletion target in this file.

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
rg -n -F -- "find_similar_concept_rows" propstore tests
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
- `propstore/families/forms/stages.py` remains the form semantic owner;
- `propstore/form_utils.py` is deleted and its callers use the forms owner;
- `Concept`, `ConceptAlias`, `ConceptRelationship`, `Parameterization`,
  `ParameterizationGroup`, and `FormAlgebra` reads/writes are mapped through
  Quire SQLAlchemy charters;
- concept build writes use Quire writable sessions and typed write plans;
- concept search uses Quire/SQLAlchemy FTS APIs;
- concept sidecar runtime uses Quire session/vector APIs;
- concept handle, alias, logical-id, form validation, and parameterization
  semantics are preserved in owner modules;
- all deletion targets in this file are gone from production code;
- forms and concept/parameterization data parity passes;
- required pyright, pytest, and search gates pass.
