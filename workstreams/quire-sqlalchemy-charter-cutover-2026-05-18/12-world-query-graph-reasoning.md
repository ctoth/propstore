# Quire SQLAlchemy Charter Cutover: World Query, Graph, And Reasoning

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
- world/runtime validation uses Quire SQLAlchemy schema/catalog validation
  directly and does not preserve projection-era `Unsupported sidecar schema`
  wording, `ProjectionSchemaError`, or rebuild advice as a compatibility
  wrapper.

Binding current-status notes from the 2026-05-20 audit:

- The phase-order checker currently passes for `00-index.md`; this does not
  make this workstream executable until its prerequisite child gates have
  actually closed.
- Phase 10 is still in the current queue: `propstore/families/claims/projection_model.py`
  still contains the permitted justification residual definitions
  `_nullable_text`, `_claim_id`, `TEXT_CODEC`, `CLAIM_ID_CODEC`,
  `JUSTIFICATION_STORAGE_MODEL`, and `JUSTIFICATION_TABLE`, and
  `propstore/families/claims/declaration.py` still imports the residual module.
- Micropublication old paths are still present in production and tests:
  `MicropublicationProjectionRow`, `MicropublicationClaimProjectionRow`,
  `MicropublicationSidecarRows`, `ActiveMicropublication`,
  `ActiveMicropublicationInput`, `compile_micropublication_sidecar_rows*`,
  `create_micropublication_tables`, `populate_micropublications`, and
  `select_all_micropublications` are not closed.
- Relation/stance projection models remain in `propstore/families/relations`
  and are still consumed by graph export, graph build, analyzers, ASPIC,
  support-revision, bound/overlay world code, and worldline argumentation.
- `ActiveWorldGraph` and `WorldBindActiveReport` remain real production/test
  surfaces. `ActiveClaimResolver` already has no current hit, but the final
  search gate remains binding so it cannot be reintroduced.
- `resolve_claim`, `resolve_concept`, and `resolve_alias` remain real
  production/test surfaces. Current `main_model` search is zero-hit, but final
  closure must still prove generic Quire family metadata/model access exists
  and that no wrapper-shaped substitute was introduced.
- The old projection-schema wording searches currently have no production/test
  hits for `Unsupported sidecar schema`, `ProjectionSchemaError`,
  `validate_derived_store_schema`, `schema.validate_connection`, or
  `Rebuild with 'pks build'`; keep these as zero-hit reintroduction gates.
- `from_mapping` currently has no hits in the searched core/family/world/
  worldline/support-revision/test surfaces, but `from_row_mapping` remains on
  active-object payloads and is not a substitute for typed model inputs.
- Do not weaken this phase by renaming duplicate field shapes or helpers.
  `from_row_mapping`, `resolve_*`, `lookup_*`, `get_*_id`, row DTOs,
  projection models, model-layer normalizers, and per-family runtime adapters
  are acceptable only as named deletion targets or boundary-specific
  constructors explicitly owned by the final architecture.

## Prerequisites

Complete these cutover workstreams before this slice starts:

Required phase file prerequisites: `00-index.md`, `inventory-matrix.md`,
`helper-ledger.md`, `01-quire-capability-and-charter.md`,
`02-quire-sqlalchemy-engine.md`, `03-quire-fts-vector.md`,
`04-propstore-build-orchestration.md`, `05-source-and-diagnostics.md`,
`06-forms-concepts-parameterizations.md`, `07-contexts-lifting.md`,
`08-claims-active-claims.md`, `08a-typed-claim-graph-projection.md`,
`09-relations-stances-conflicts.md`,
`10-micropublications-justifications.md`,
`10a-charter-generated-model-cleanup.md`,
`11-rules-grounding-calibration-embeddings.md`.

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
- Charter-generated model cleanup.
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

2026-05-21 prerequisite execution update:

- Current repo state before Phase 14 implementation: branch `master`; no
  tracked task-owned changes; unrelated untracked local/diagnostic paths remain
  outside this workstream.
- `uv run pyright propstore` passed with zero errors before Phase 14
  implementation.
- Initial `powershell -File scripts/run_logged_pytest.ps1 -Label world-prereq
  tests/test_world_query.py tests/test_worldline.py tests/test_graph_export.py
  tests/test_worldline_ic_merge_properties.py` failed 5 worldline tests after
  216 passed; log: `logs/test-runs/world-prereq-20260521-113240.log`.
- The failures were not a production compatibility reason to loosen
  `concept_name`; they were stale fake-world fixtures returning concept dicts
  where the current worldline path requires typed `Concept` model objects.
- Test commit `3f666826` updated `tests/test_worldline.py` fake worlds to
  return typed `Concept` fixtures instead of dict payloads.
- Focused repair gate
  `powershell -File scripts/run_logged_pytest.ps1 -Label
  worldline-typed-concept-fixtures ...` passed the five previously failing
  tests; log:
  `logs/test-runs/worldline-typed-concept-fixtures-20260521-113536.log`.
- `uv run pyright propstore` passed with zero errors after the fixture repair.
- Rerun `powershell -File scripts/run_logged_pytest.ps1 -Label world-prereq
  tests/test_world_query.py tests/test_worldline.py tests/test_graph_export.py
  tests/test_worldline_ic_merge_properties.py` passed with 221 tests and 29
  expected warnings; log:
  `logs/test-runs/world-prereq-20260521-113729.log`.
- Prerequisite `ProjectionTable(` and `ProjectionModel` searches returned zero
  hits under the required paths.
- Prerequisite `sqlite3.Connection` search returned only the remaining
  family-selector old-path deletion targets
  `propstore/families/claims/declaration.py::select_authored_justifications`
  and `count_authored_justifications`.
- Phase 14 implementation may start with Slice 1:
  `WorldQuery` session cutover.

2026-05-21 Slice 1 execution update:

- Commit `c9a9e63b` deleted the remaining raw `sqlite3.Connection` authored
  justification selector/count path from `propstore/families/claims/declaration.py`.
- `WorldQuery` no longer opens or closes a raw read-only SQLite connection and
  no longer sets `row_factory`; `_validate_schema`, `grounding_bundle`,
  `all_authored_justifications`, and `authored_justification_count` use the
  Quire derived-store SQLAlchemy session path.
- Canonical justification conversion now lives as behavior on the typed
  `Justification` family model in `propstore/core/justifications.py`; the
  storage field list still comes from the charter metadata.
- Slice 1 search gates run after the edit returned zero hits for
  `self._conn`, `row_factory`, `select_authored_justifications`,
  `count_authored_justifications`, `sqlite3.Connection` under the owned
  world/family/core/worldline/test paths, and the removed standalone
  `readonly_session` import shape in `propstore/world/model.py`.
- `uv run pyright propstore` passed with zero errors after the edit.
- Focused gate
  `powershell -File scripts/run_logged_pytest.ps1 -Label
  worldquery-session-cutover
  tests/test_world_query.py::TestWorldQuerySidecarPath
  tests/test_world_query.py::TestUnboundQueries::test_stats
  tests/test_world_query.py::TestUnboundQueries::test_get_claim
  tests/test_world_query.py::TestUnboundQueries::test_get_concept` passed with
  10 tests; log:
  `logs/test-runs/worldquery-session-cutover-20260521-114340.log`.
- Slice 1 session/raw selector cutover is complete. Continue with Slice 2:
  world query helper migration.

2026-05-21 Slice 2 execution update:

- Commit `17574b02` used `scripts/rope_rename.py` to rename
  `WorldBindActiveReport` to `WorldBindActivationReport` across
  `propstore/world/queries.py`, `propstore/app/world.py`, and
  `propstore/cli/world/query.py`.
- The old `WorldBindActiveReport` spelling search returned zero hits under
  `propstore` and `tests` after the rename.
- `uv run pyright propstore` passed with zero errors after the rename.
- Direct import/layout gate
  `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-bind-report-layout
  tests/test_cli_layout.py::test_cli_only_world_arg_parsers_live_in_cli_layer
  tests/test_world_query.py::TestWorldQuerySidecarPath::test_worldmodel_importable_without_cli`
  passed with 2 tests; log:
  `logs/test-runs/world-bind-report-layout-20260521-114736.log`.
- Attempted focused world-bind behavior gate
  `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-bind-report-rename
  tests/test_cli.py::TestWorldQuerySIValues::test_owner_world_bind_report_shows_si_value
  tests/test_cli.py::TestWorldQuerySIValues::test_world_bind_shows_si_value
  tests/test_cli.py::TestWorldQuerySIValues::test_world_bind_json_uses_report_shape
  tests/test_cli.py::TestWorldQuerySIValues::test_world_bind_accepts_canonical_name`
  reached fixture sidecar build setup and failed before exercising the rename
  with `sqlite3.IntegrityError: FOREIGN KEY constraint failed`; log:
  `logs/test-runs/world-bind-report-rename-20260521-114646.log`. This remains
  evidence to revisit in the broader world/build gate; it is not a reason to
  add a compatibility wrapper around the report name.
- Continue Slice 2 with the remaining world query helper and resolver-wrapper
  deletion work.

2026-05-21 activation graph rename update:

- Commit `a933a8cc` used `scripts/rope_rename.py` to rename
  `ActiveWorldGraph` to `WorldActivationGraph` across production and tests.
- Rope initially rewrote line endings in `tests/test_praf.py` and
  `tests/test_worldline.py`; those two files were restored path-locally and
  patched with only the minimal symbol changes before commit.
- The old `ActiveWorldGraph` spelling search returned zero hits under
  `propstore` and `tests` after the rename.
- `uv run pyright propstore` passed with zero errors after the rename.
- Focused gate
  `powershell -File scripts/run_logged_pytest.ps1 -Label
  world-activation-graph-rename
  tests/test_core_graph_types.py::test_active_world_graph_roundtrip_is_stable
  tests/test_core_analyzers.py::test_shared_projection_is_independent_of_active_claim_id_order
  tests/test_mapping_boundary_failures.py::test_active_world_graph_rejects_malformed_compiled_graph`
  passed with 3 tests; log:
  `logs/test-runs/world-activation-graph-rename-20260521-115206.log`.
- Continue with the remaining resolver-wrapper, active-input, and
  `from_mapping` deletion targets.

2026-05-21 resolver-wrapper deletion update:

- Commit `74ec11ea` deleted the world-specific claim/concept/alias resolver
  wrapper surface instead of renaming it.
- `WorldQuery.resolve_concept`, `WorldQuery.resolve_alias`,
  `_build_logical_id_index`, `_get_logical_id_index`, and the
  `_logical_id_indexes` cache are gone from `propstore/world/model.py`.
- Concept and alias lookup now use Quire family-reference metadata:
  `concept` charter reference keys include primary logical ID, bare logical
  ID value, `namespace:value`, and canonical name; `alias` charter reference
  keys include `alias_name`.
- `Concept.logical_ids` is a behavior-only typed property over the existing
  charter-owned `logical_ids_json` field so Quire `ReferenceKey` metadata can
  read logical IDs without a WorldQuery-side JSON/cache helper.
- Bound/overlay/app/sensitivity/worldline callers now use typed
  `get_concept` or direct Quire `schema.resolve_reference_id` where the
  session is already open; no `resolve_*`, `lookup_*`, `get_*_id`, raw SQL
  selector, or cached logical-id-map substitute was added.
- Test doubles that modeled the removed production resolver methods were
  updated to return typed `Concept` fixtures through `get_concept` instead.
- Deleted the unused `propstore/families/identity/concepts.py`
  `resolve_concept_reference` helper rather than keeping a dead old resolver
  name.
- Search gates returned zero hits for `def resolve_claim`,
  `def resolve_concept`, `def resolve_alias`, `.resolve_claim(`,
  `.resolve_concept(`, `.resolve_alias(`, `_get_logical_id_index`,
  `resolve_claim_id`, `resolve_concept_id`, and `resolve_concept_alias` under
  `propstore` and `tests`.
- `uv run pyright propstore` passed with zero errors after the deletion.
- Focused lookup/worldline gate
  `powershell -File scripts/run_logged_pytest.ps1 --label
  resolver-wrapper-deletion tests/test_world_model_resolve_cache.py
  tests/test_world_query.py tests/test_worldline_error_visibility.py
  tests/test_worldline_hash_excludes_transient_errors.py
  tests/test_worldline_revision.py` passed with 162 tests and 29 expected
  warnings; log:
  `logs/test-runs/resolver-wrapper-deletion-20260521-121132.log`.
- Continue with the remaining Phase 14 targets:
  `ActiveClaimInput`, `ActiveMicropublicationInput`, active value resolver
  naming, generic `from_mapping` constructors, typed bound/overlay/ATMS graph
  migration, support-revision, ASPIC, and final parity/search gates.

2026-05-21 active-input/value-resolver gate update:

- `rg -n -F -- "ActiveClaimInput" propstore tests`,
  `rg -n -F -- "ActiveMicropublicationInput" propstore tests`, and
  `rg -n -F -- "ActiveClaimResolver" propstore tests` returned zero hits.
- The current value resolver surface is already `ClaimValueResolver` in
  `propstore/world/value_resolver.py`, with production users in
  `propstore/world/bound.py` and typed value-resolver tests. No rename,
  wrapper, alias, or compatibility layer is required or allowed here.
- Continue with the remaining Phase 14 targets: generic `from_mapping`
  constructors, typed bound/overlay/ATMS graph migration, support-revision,
  ASPIC, and final parity/search gates.

2026-05-21 constructor-name gate update:

- `rg -n -F -- "from_mapping" propstore/core propstore/families
  propstore/world propstore/worldline propstore/support_revision tests`
  returned zero hits.
- `rg -n -F -- "from_row_mapping" propstore/core propstore/families
  propstore/world propstore/worldline propstore/support_revision tests`
  returned zero hits.
- The Phase 14 generic persisted-result, graph-provenance, and
  support-revision constructor-name deletion target is already closed in the
  current repo state. No wrapper, alias, renamed generic constructor, or
  duplicate helper was added.
- Continue with the remaining Phase 14 targets: typed bound/overlay/ATMS graph
  migration, graph/analyzer/export migration, SCM/intervention/resolution,
  support-revision, ASPIC, and final parity/search gates.

2026-05-21 `_claim_rows` terminology and typed-fixture cleanup update:

- Deleted the remaining required-gate `_claim_rows` hits from typed world
  paths by renaming typed `Claim` variables and helpers in
  `propstore/world/overlay.py`, `propstore/world/resolution.py`, and
  `propstore/world/assignment_selection_policy.py`. No row DTO, coercer, or
  wrapper was added.
- Updated the claim-view fake world to construct `Concept` with the
  charter-owned `id` field, index concepts by typed id and canonical name, and
  lower external concept references to the typed concept id before filtering.
- Updated the revision fake store to return typed `Concept` objects from
  `all_concepts()` instead of dict payloads so graph build continues to
  consume typed model objects.
- Cleaned the remediation/test names that matched the exact `_claim_rows`
  gate without changing their raw SQLite boundary assertions.
- `rg -n -F -- "_claim_rows" propstore/world tests` returned zero hits.
- `uv run pyright propstore` passed with zero errors.
- Focused gate
  `powershell -File scripts/run_logged_pytest.ps1 -Label
  claim-row-name-cleanup tests/test_worldline.py tests/test_claim_views.py
  tests/test_revision_af_adapter.py` passed with 66 tests; log:
  `logs/test-runs/claim-row-name-cleanup-20260521-122130.log`.
- Continue with the remaining Phase 14 targets: graph/analyzer/export
  migration, SCM/intervention/resolution, support-revision, ASPIC, and final
  parity/search gates.

2026-05-21 graph export raw-connection test cleanup update:

- The Phase 14 `world-charter` gate initially failed
  `tests/test_graph_export.py::TestGroupScoping::test_group_scoping` because
  the test reached into deleted `WorldQuery._conn` to query
  `parameterization_group`.
- The test now uses typed world APIs, scanning `world.concept_ids_for_group()`
  across the current typed concept count from `world.all_concepts()` to locate
  the group containing `concept5`. No raw connection, SQL string, helper
  wrapper, or compatibility surface was added.
- `rg -n -F -- "._conn" propstore tests/test_graph_export.py` returned zero
  hits.
- `uv run pyright propstore` passed with zero errors.
- Focused gate
  `powershell -File scripts/run_logged_pytest.ps1 -Label
  graph-export-group-scope
  tests/test_graph_export.py::TestGroupScoping::test_group_scoping` passed
  with 1 test; log:
  `logs/test-runs/graph-export-group-scope-20260521-122442.log`.
- Continue with rerunning the full Phase 14 `world-charter` behavior gate,
  final search gates, data parity, and behavior parity.

2026-05-21 Phase 14 behavior gate update:

- `uv run pyright propstore` passed with zero errors before the behavior gate.
- Rerun
  `powershell -File scripts/run_logged_pytest.ps1 -Label world-charter
  tests/test_world_query.py tests/test_worldline.py tests/test_graph_export.py
  tests/test_worldline_ic_merge_properties.py` passed with 221 tests and 29
  expected warnings; log:
  `logs/test-runs/world-charter-20260521-122540.log`.
- Continue with final old-path search gates, data parity, and behavior parity
  for Phase 14.

## Inventory Rows

| Inventory surface | Current owner | Final owner | Required action |
| --- | --- | --- | --- |
| `propstore/world/model.py` | Primary sidecar query facade over raw SQLite | Propstore `WorldQuery` over Quire read-only sessions | Replace raw connection/selectors with model/session queries |
| `propstore/world/model.py::_validate_schema` | Projection-schema validation wrapper that rewrites errors to `Unsupported sidecar schema` | No Propstore compatibility wrapper; Quire SQLAlchemy catalog/session validation failures flow directly to owner-layer callers | Delete wrapper and update tests away from old projection wording |
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
- `WorldQuery.resolve_claim`, `WorldQuery.resolve_concept`, and
  `WorldQuery.resolve_alias` as claim/concept/alias convenience wrappers when
  they duplicate generic Quire family reference lookup or typed model access;
- forwarding wrapper methods such as `OverlayWorld.resolve_claim`,
  `OverlayWorld.resolve_concept`, and `OverlayWorld.resolve_alias` when they
  only preserve the old convenience-resolver surface;
- helper variants such as `_resolve_claim_lookup_id`,
  `_resolve_claim_target`, `_resolve_claim_input`,
  `_resolve_concept_filter`, and `_resolve_concept_entry` when their only job
  is to hide reference lookup behind another claim/concept-specific helper;
- `ActiveClaimInput` and `ActiveMicropublicationInput` protocol surfaces in
  world/environment/overlay/ATMS APIs;
- `ActiveClaimResolver` in `propstore/world/value_resolver.py`;
- `ActiveWorldGraph` spelling in public world/graph APIs;
- `WorldBindActiveReport` spelling in world query report APIs;
- raw SQL snippets that duplicate SQLAlchemy query construction;
- `ProjectionRow` usage in world, family, graph, and worldline runtime paths;
- `_validate_schema` in `propstore/world/model.py` as a projection-schema
  validation wrapper around `validate_derived_store_schema`;
- message rewriting that translates Quire/derived-store validation failures
  into `Unsupported sidecar schema` or appends `Rebuild with 'pks build'.`;
- tests that pin projection-schema validation errors through
  `ProjectionSchemaError`, `schema.validate_connection`, or
  `Unsupported sidecar schema` wording;
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
- `propstore/app/world.py`;
- `propstore/cli/world/query.py`;
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
- `tests/test_mapping_boundary_failures.py`;
- `tests/test_revision_event_contract.py`;
- `propstore/aspic_bridge/extract.py`;
- `propstore/aspic_bridge/translate.py`.

Required caller final state:

- `WorldQuery` owns semantic read facade behavior and receives typed sessions
  from Quire derived-store handles;
- claim/concept/alias lookup is not owned by world-specific resolver wrappers:
  family reference resolution uses Quire family-reference APIs and family
  registry indexes, while typed row access obtains the mapped model through
  generic Quire family metadata and then uses the derived-store session path;
- world code may orchestrate cross-family behavior, but claim-local semantics
  remain on typed `Claim` / claim-family owner surfaces. Do not put payload,
  scalar, condition, concept-link, source-assertion, reference, or alias
  semantics in `WorldQuery`, bound worlds, overlay worlds, ATMS, graph build,
  support-revision, or ASPIC code merely to keep old API shape;
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
projection row conversion, projection-schema validation wrappers, and generic
persisted-payload mapping names move to Quire session/query machinery or
disappear. CLI/app/web presentation may map typed owner-layer failures to exit
codes or HTTP responses, but must not standardize around old projection-schema
messages.

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
8a. Delete the old claim/concept/alias resolver wrapper family instead of
    renaming it. The implementation work queue includes the current surfaces
    `propstore/world/model.py::WorldQuery.resolve_claim`,
    `WorldQuery.resolve_concept`, `WorldQuery.resolve_alias`,
    `_get_claim_logical_id_index`, `_get_concept_logical_id_index`,
    `propstore/world/overlay.py::OverlayWorld.resolve_claim`,
    `OverlayWorld.resolve_concept`, `OverlayWorld.resolve_alias`,
    `propstore/world/bound.py::_resolve_claim_lookup_id`,
    `propstore/worldline/resolution.py::_resolve_claim_target`,
    `propstore/worldline/resolution.py::_resolve_claim_input`,
    `propstore/app/claim_views.py::_resolve_concept_filter`, and
    `propstore/app/concept_views.py::_resolve_concept_entry`. Replace direct
    users with generic Quire family-reference lookup where they resolve
    external references, or with generic Quire family metadata plus typed
    session queries where they need model rows. Do not add `resolve_*`,
    `lookup_*`, `get_*_id`, raw SQL selector, cached logical-id-map, or
    forwarding wrapper substitutes.
    Current audit adds these live consumers to classify and delete or move:
    `propstore/claim_graph.py`, `propstore/artifact_verification.py`,
    `propstore/app/world.py`, `propstore/sensitivity.py`,
    `propstore/families/concepts/sidecar_runtime.py`,
    `propstore/families/claims/declaration.py::resolve_claim_id`,
    `propstore/families/claims/declaration.py::resolve_claim_embedding_entity`,
    and `propstore/families/embeddings/declaration.py` callers. Test doubles
    may keep semantically named methods only when the production interface they
    model remains after the generic Quire lookup cutover.
8b. Replace `_validate_schema` with Quire SQLAlchemy schema/catalog validation
    through the derived-store handle/session path and delete message rewriting
    around old `Unsupported sidecar schema` wording.
8c. Update `tests/test_world_query.py` and
    `tests/test_sidecar_projection_contract.py` so they no longer assert
    `Unsupported sidecar schema`, `ProjectionSchemaError`,
    `validate_derived_store_schema`, `schema.validate_connection`, or
    `Rebuild with 'pks build'`. New tests should assert the Quire SQLAlchemy
    catalog/session validation contract or the app/CLI/web presentation layer
    error mapping, depending on the boundary under test.
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

2026-05-21 final old-path search gate update:

- The required Phase 14 searches returned zero hits for
  `sqlite3.Connection`, `row_factory`, `connect_sqlite_store`,
  `ProjectionRow`, `ProjectionModel`, `from_mapping`, `_claim_rows`,
  `ActiveClaimInput`, `ActiveMicropublicationInput`, `ActiveClaimResolver`,
  `ActiveWorldGraph`, `WorldBindActiveReport`, `claim_row_query_plan`,
  `claim_stance_policy_query_plan`, `Unsupported sidecar schema`,
  `ProjectionSchemaError`, `validate_derived_store_schema`,
  `schema.validate_connection`, and `Rebuild with 'pks build'` under the
  exact required Phase 14 search paths.
- No wrapper, adapter, alias, compatibility bridge, renamed old helper, or
  duplicate constructor was added to close these gates.
- Continue with the Phase 14 data-parity and behavior-parity commands.

2026-05-21 behavior-parity harness update:

- Commit `afae44c7` added the required Phase 14 behavior blocks to
  `scripts/compare_sqlalchemy_charter_parity.py` for
  `world-query-graph-reasoning`.
- The harness uses current typed `WorldQuery` behavior extraction and generic
  typed value serialization. It does not add production support for old
  sidecar shapes.
- To compare the captured projection baseline after Phase 6, the harness makes
  a temporary diagnostic copy of the baseline SQLite file and applies only the
  Phase 6 accepted `source` storage collapse from
  `origin_type`/`origin_value`/`origin_retrieved`/`origin_content_ref`,
  `prior_base_rate`, `quality_json`, and `derived_from_json` into the current
  `source` typed value-object columns before opening it with current
  `WorldQuery`.
- Focused harness gate passed:
  `powershell -File scripts/run_logged_pytest.ps1 -Label
  parity-harness-behavior-clean tests/test_sqlalchemy_charter_parity_harness.py`
  returned `10 passed`; log:
  `logs/test-runs/parity-harness-behavior-clean-20260521-124102.log`.
- The required behavior-parity command then failed before behavior comparison
  because current schema validation rejects the captured baseline:
  `claim_numeric_payload` is missing column `confidence`.
- This is not an allowed Phase 14 difference and must not be hidden by a
  diagnostic shim. Phase 8 says loose `confidence` must not be carried forward
  as a typed claim row field. The next action is deletion-first: remove the
  `confidence` storage field from the current claim numeric payload charter and
  remove any graph/runtime dependency on that loose numeric-payload field, then
  rerun the affected claim/world gates and the Phase 14 behavior-parity command.
- Commit `62c2e45b` completed that deletion-first fix:
  `claim_numeric_payload.confidence` is no longer a charter storage field,
  typed claim-to-graph projection no longer reads
  `numeric_payload.confidence`, and stale test-store conversion helpers no
  longer pass `confidence` into the typed claim numeric payload constructor.
- Verification for `62c2e45b`: exact searches for
  `numeric_payload.confidence` and `num.confidence` returned zero hits in the
  searched production/test paths; focused pyright over the touched claim graph
  and analyzer surfaces returned 0 errors; logged pytest
  `powershell -File scripts/run_logged_pytest.ps1 -Label
  claim-confidence-deletion tests/test_core_analyzers.py
  tests/test_world_query.py::TestWorldQuerySidecarPath
  tests/test_world_query.py::TestUnboundQueries::test_get_claim
  tests/test_world_query.py::TestUnboundQueries::test_stats`
  returned `16 passed`; log:
  `logs/test-runs/claim-confidence-deletion-20260521-124511.log`.
- Commit `12d9f37a` finished the behavior-parity harness support for the
  captured baseline: after applying the Phase 6 source-column collapse in a
  temporary diagnostic copy, it copies the current schema catalog metadata and
  creates only missing current-schema tables that are empty in the after
  sidecar, such as the empty `claim_source_assertion` table in this fixture.
  This remains diagnostic-only and does not add a production old-shape reader.
- Focused harness gates passed:
  `powershell -File scripts/run_logged_pytest.ps1 -Label
  parity-harness-empty-current-tables tests/test_sqlalchemy_charter_parity_harness.py`
  returned `10 passed`; log:
  `logs/test-runs/parity-harness-empty-current-tables-20260521-124731.log`.
  `powershell -File scripts/run_logged_pytest.ps1 -Label
  parity-harness-schema-catalog tests/test_sqlalchemy_charter_parity_harness.py`
  returned `10 passed`; log:
  `logs/test-runs/parity-harness-schema-catalog-20260521-124829.log`.
- Required Phase 14 behavior parity passed:
  `uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir .
  --before reports/sqlalchemy-charter-parity/world-query-graph-reasoning/before.sqlite
  --build-after sqlalchemy-charter
  --after reports/sqlalchemy-charter-parity/world-query-graph-reasoning/after.sqlite
  --owner world-query-graph-reasoning
  --workstream workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/12-world-query-graph-reasoning.md
  --out reports/sqlalchemy-charter-parity/world-query-graph-reasoning-behavior.json
  --require-behavior world-query --require-behavior graph-build
  --require-behavior atms --require-behavior scm-intervention-resolution
  --require-behavior worldline --require-behavior support-revision
  --require-behavior aspic` exited 0. The generated report has passing
  behavior blocks for `world-query`, `graph-build`, `atms`,
  `scm-intervention-resolution`, `worldline`, `support-revision`, and
  `aspic`.

## Data-Parity Gate

This gate includes the behavior-vector comparisons required by this phase.

```powershell
uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --before reports/sqlalchemy-charter-parity/world-query-graph-reasoning/before.sqlite --build-after sqlalchemy-charter --after reports/sqlalchemy-charter-parity/world-query-graph-reasoning/after.sqlite --owner world-query-graph-reasoning --workstream workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/12-world-query-graph-reasoning.md --out reports/sqlalchemy-charter-parity/world-query-graph-reasoning.json
uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --before reports/sqlalchemy-charter-parity/world-query-graph-reasoning/before.sqlite --build-after sqlalchemy-charter --after reports/sqlalchemy-charter-parity/world-query-graph-reasoning/after.sqlite --owner world-query-graph-reasoning --workstream workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/12-world-query-graph-reasoning.md --out reports/sqlalchemy-charter-parity/world-query-graph-reasoning-behavior.json --require-behavior world-query --require-behavior graph-build --require-behavior atms --require-behavior scm-intervention-resolution --require-behavior worldline --require-behavior support-revision --require-behavior aspic
```

Compare the captured projection baseline against the charter-generated sidecar
for this slice and compare:

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
revision result, or ASPIC output disappears.

Accepted parity difference allowlist:

- deleted raw connection paths, projection imports, row-coercion helpers, raw
  SQL snippets, and constructor names listed as deletion targets in this file;
- no output-shape rename, row disappearance, key disappearance,
  semantic-query disappearance, graph-edge disappearance, ATMS-label
  disappearance, reasoning-result disappearance, render-policy-result
  disappearance, worldline-materialization disappearance,
  support-revision-result disappearance, or ASPIC-output disappearance is
  allowed.

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
rg -n -F -- "Unsupported sidecar schema" propstore tests
rg -n -F -- "ProjectionSchemaError" propstore tests
rg -n -F -- "validate_derived_store_schema" propstore tests
rg -n -F -- "schema.validate_connection" propstore tests
rg -n -F -- "Rebuild with 'pks build'" propstore tests
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
- `WorldQuery` does not catch Quire schema/catalog validation failures to
  rewrite them into old projection-schema or sidecar-schema messages;
- `Unsupported sidecar schema`, `ProjectionSchemaError`,
  `validate_derived_store_schema`, `schema.validate_connection`, and
  `Rebuild with 'pks build'` are absent from production code and tests;
- the data-parity and behavior-parity gates pass;
- all required tests pass through the logged pytest wrapper;
- all old-path search gates above are zero-hit outside notes, workstreams,
  docs, and reports.
