# 13 - Final Deletion Gates

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

Close the Quire SQLAlchemy charter cutover after all family and world-query
child workstreams have moved their consumers to Quire SQLAlchemy sessions and
typed Propstore models.

This file owns final verification, old-path search gates, dependency-pin
closure, inventory closure, and completion criteria. It does not authorize a
production cutover before the prerequisite child gates pass.

Binding notes from the 2026-05-20 update:

- Final deletion must reject per-family identity lookup wrappers, convenience
  methods, and renamed helper-shaped APIs. The final state uses generic Quire
  family reference/FK lookup and generic Quire main-model access only.
- Family semantics may live on typed ORM/domain objects when the behavior is
  domain-specific. Generic identity, FK, table, session, vector, and
  main-model lookup mechanics belong in Quire.
- `rg` on 2026-05-20 found no `main_model` hits under `propstore` or `tests`,
  but `resolve_claim`, `resolve_concept`, and `resolve_alias` are still real
  production/test surfaces and must be covered by final old-path search gates.
- The final gate must distinguish semantic resolution behavior that remains on
  typed domain/world objects from old per-family lookup wrappers and call
  sites. Keeping a wrapper because it is convenient is not a valid closure.
- The 2026-05-20 audit confirmed `main_model` is still zero-hit, but
  `resolve_claim`, `resolve_concept`, and `resolve_alias` are live production
  and test queues. Final deletion must not replace them with differently named
  wrapper-shaped APIs; it must land generic Quire family reference/FK lookup
  and generic model access, then update every caller.
- The 2026-05-20 audit confirmed old schema-validation wording is currently
  zero-hit in production/tests. Keep every related search as a required
  zero-hit reintroduction gate.
- The current remaining queues include Phase 10 micropublication and
  justification residuals, relation/stance projection models, raw
  `sqlite3.Connection` family runtimes, `row_factory` setup, direct
  `connect_sqlite_store` usage, `ActiveWorldGraph`, `WorldBindActiveReport`,
  `ActiveClaim`/`ActiveMicropublication` active-object families, sidecar
  embedding/relation runtimes, and relation query-plan helpers.
- No duplicate field shape may survive as a row DTO, projection model, kwargs
  builder, cast family, model normalizer, `from_row_mapping` convenience path,
  or renamed helper. Boundary-specific constructors are allowed only at actual
  IO/document boundaries and must not carry DB row/projection coupling.

## Prerequisite Gate Dependencies

Check these before starting final deletion work:

| Dependency | Required evidence |
| --- | --- |
| `00-index.md` | Phase-order checker has passed for the split directory. |
| `inventory-matrix.md` | Every row has a delete, replace, move, or keep-as-semantic-owner closure entry. |
| `01-quire-capability-and-charter.md` | SQLAlchemy capability proof, charter/schema IR, Quire gates, and pushed Quire pin are complete. |
| `02-quire-sqlalchemy-engine.md` | SQLAlchemy table/mapping/session/catalog engine gates are complete. |
| `03-quire-fts-vector.md` | FTS/vector gates are complete and no Propstore workaround owns generic FTS/vector behavior. |
| `04-propstore-build-orchestration.md` | Build orchestration uses Quire writable sessions and charter catalogs. |
| `05-source-and-diagnostics.md` | Source and source-diagnostic old paths are deleted and parity passed. |
| `06-forms-concepts-parameterizations.md` | Form, concept, parameterization, and concept declaration/query old paths are deleted and parity passed; concept sidecar runtime evidence belongs to `11-rules-grounding-calibration-embeddings.md`. |
| `07-contexts-lifting.md` | Context/lifting projection paths are deleted and parity passed. |
| `08-claims-active-claims.md` | Claim projection/storage/active-claim row paths are deleted and parity passed. |
| `08a-typed-claim-graph-projection.md` | Typed claim-to-graph projection owner is complete and claim graph/source-assertion projection no longer uses duplicate row attributes. |
| `09-relations-stances-conflicts.md` | Relation, stance, and conflict row-model paths are deleted and parity passed. |
| `10-micropublications-justifications.md` | Micropub/justification projection paths are deleted and parity passed. |
| `10a-charter-generated-model-cleanup.md` | Every Propstore mapped sidecar model is a methods-only `FamilyModel` subclass and duplicated mapped field declarations, constructors, placeholder records, and mapping repair APIs are deleted. |
| `11-rules-grounding-calibration-embeddings.md` | Support-family projection/vector duplicates and claim/concept sidecar runtime old paths are deleted and parity passed. |
| `12-world-query-graph-reasoning.md` | `WorldQuery`, graph, worldline, support-revision, and ASPIC callers use typed session/model APIs. |
| `helper-ledger.md` | Every ledger row has a closure entry or is covered by the owning child workstream's closure report. |

## Phase 15: Delete Quire Projection Modules

Repository: `C:\Users\Q\code\quire`.

### Deletion Checklist

- [x] Confirm all Propstore and Quire consumers have moved away from Quire
  projection primitives.
- [x] Delete `quire/projection_mapping.py`.
- [x] Delete `quire/projections.py`.
- [x] Delete public exports for projection classes from `quire/__init__.py`.
- [x] Delete tests that only test deleted projection primitives.
- [x] Confirm replacement coverage exists for charter IR, SQLAlchemy mapping,
  schema catalog, FTS/vector extension, and derived-store sessions.

### Phase 15 Execution Record

Recorded 2026-05-21.

- Quire commit: `f43dd1be83fd0c0b52a06104c79d1550bdf5f3a6` (`Delete projection primitives`).
- Deleted in Quire: `quire/projection_mapping.py`, `quire/projections.py`, and
  `tests/test_projection_mapping.py`.
- Updated in Quire: `quire/__init__.py`,
  `quire/derived_runtime.py`, `quire/sqlite_vec_store.py`, and
  `tests/test_derived_store.py`.
- Propstore import checks for `from quire.projections`,
  `from quire.projection_mapping`, `quire.projections`, and
  `quire.projection_mapping` were zero-hit in `propstore` and `tests`.
- Quire old-path searches listed below were zero-hit in `quire` and `tests`.
- Quire replacement coverage: `uv run pyright` passed with 0 errors;
  `uv run pytest -vv tests/test_derived_store.py` passed with 12 tests; full
  `uv run pytest -vv` passed with 327 tests.

### Quire Search Gates

Run from `C:\Users\Q\code\quire`:

```powershell
rg -n -F -- "ProjectionTable" quire tests
rg -n -F -- "ProjectionSchema" quire tests
rg -n -F -- "ProjectionIndex" quire tests
rg -n -F -- "ProjectionColumn" quire tests
rg -n -F -- "ProjectionSelectedColumn" quire tests
rg -n -F -- "ProjectionModel" quire tests
rg -n -F -- "ProjectionCodec" quire tests
rg -n -F -- "ScalarPath" quire tests
rg -n -F -- "ReferencePath" quire tests
rg -n -F -- "FtsProjection" quire tests
rg -n -F -- "VecProjection" quire tests
```

Gate: zero production hits. Documentation hits are limited to notes,
workstreams, docs, and reports.

## Phase 16: Delete Propstore Projection And Helper Leftovers

Repository: `C:\Users\Q\code\propstore`.

### Deletion Checklist

- [x] Verify `propstore/families/claims/projection_model.py` is absent after
  Phase 10 deletes the justification residual.
- [x] Delete `propstore/families/concepts/projection_model.py`.
- [x] Delete `propstore/families/relations/projection_model.py`.
- [x] Delete `propstore/families/projection_catalog.py`.
- [x] Delete embedded projection declarations in family declaration modules.
- [x] Delete row classes that duplicate domain models.
- [x] Delete manual select/count/insert/decode/attached-row helpers that are
  generic DB plumbing.
- [x] Delete manual field coercers now owned by the charter engine.
- [x] Confirm remaining IO boundary constructors use names such as
  `from_yaml_payload`, `from_json_payload`, or `from_row_mapping`.
- [x] Confirm `from_mapping` is absent from core, families, world, worldline,
  support-revision, and tests.
- [x] Confirm no PascalCase `Active*` production type remains. Activation
  state names use `Activation`, `Activated`, or domain-specific report names.

### Helper Deletion Predicate

- [x] Delete helpers whose body is table-shaped `SELECT`, `COUNT`, `INSERT`,
  `DELETE`, row attachment, row coercion, or projection-model wrapping with no
  Propstore semantic policy.
- [x] Preserve semantic behavior that owns concept-id precedence, alias
  resolution, source-local lowering, quarantine/blocked policy, form/unit
  validation, visibility/render policy, context/lifting semantics,
  argumentation semantics, revision semantics, or authored-document identity.
- [x] After semantic behavior is moved to its owner, delete the original
  helper-shaped production path.

### Phase 16 Execution Record

Recorded 2026-05-21.

- Commit `a53b7457` (`Delete optional coercer helpers`) deleted the remaining
  `_optional_string`, `_optional_int`, `_optional_float`,
  `_optional_float_input`, `_optional_numeric`, and `_claim_optional_float`
  search-gate hits in `propstore` and `tests`.
- The kept parsing logic is located at actual payload/YAML boundaries:
  `from_json_payload` constructors, merge-claim provenance extraction, and the
  defeasible conformance YAML test loader. No replacement helper family was
  added.
- The same commit made relation model comparison behavior-only and based on
  public mapped attributes, and made relation attribute extraction tolerant of
  absent optional charter fields without adding fields outside the charter.
- Verification: `uv run pyright propstore` passed with 0 errors; logged pytest
  `phase16-coercer-20260521-131326.log` passed with 20 tests.
- Final Phase 16 projection/model/helper/coercer/schema-validation/active-object
  search gates were zero-hit in `propstore` and `tests`, except the broad
  classification searches below.
- Narrow forbidden lookup-wrapper searches were zero-hit:
  `def resolve_claim`, `def resolve_concept`, `def resolve_alias`,
  `.resolve_claim(`, `.resolve_concept(`, `.resolve_alias(`,
  `resolve_claim_id`, `resolve_concept_id`, and `resolve_concept_alias`.
- Remaining broad `resolve_claim` hits are semantic world/worldline resolution
  behavior: target/input value resolution and claim-graph argumentation
  adjudication. They are not family identity lookup wrappers.
- Remaining broad `resolve_concept` hits are description rendering behavior:
  concept-id-to-display-name formatting inside `description_generator.py`.
  They are not generic family reference lookup wrappers.
- `resolve_alias` and `main_model` are zero-hit.

### Propstore Search Gates

Run from `C:\Users\Q\code\propstore`:

```powershell
rg -n -F -- "ProjectionTable" propstore tests
rg -n -F -- "ProjectionSchema" propstore tests
rg -n -F -- "ProjectionIndex" propstore tests
rg -n -F -- "ProjectionColumn" propstore tests
rg -n -F -- "ProjectionSelectedColumn" propstore tests
rg -n -F -- "ProjectionModel" propstore tests
rg -n -F -- "ProjectionCodec" propstore tests
rg -n -F -- "ProjectionRow" propstore tests
rg -n -F -- "ScalarPath" propstore tests
rg -n -F -- "ReferencePath" propstore tests
rg -n -F -- "FtsProjection" propstore tests
rg -n -F -- "VecProjection" propstore tests
rg -n -F -- "CLAIM_ROW_MODEL" propstore tests
rg -n -F -- "CONCEPT_ROW_MODEL" propstore tests
rg -n -F -- "STANCE_ROW_MODEL" propstore tests
rg -n -F -- "RELATIONSHIP_ROW_MODEL" propstore tests
rg -n -F -- "SOURCE_PROJECTION" propstore tests
rg -n -F -- "CONCEPT_FTS_PROJECTION" propstore tests
rg -n -F -- "CONCEPT_VEC_PROJECTION" propstore tests
rg -n -F -- "CONTEXT_SCHEMA" propstore tests
rg -n -F -- "PROPSTORE_WORLD_PROJECTION_SCHEMA" propstore tests
rg -n -F -- "TEXT_CODEC" propstore/families/contexts tests
rg -n -F -- "PARAMETERS_CODEC" propstore/families/contexts tests
rg -n -F -- "CONDITIONS_CODEC" propstore/families/contexts tests
rg -n -F -- "PROVENANCE_CODEC" propstore/families/contexts tests
rg -n -F -- "AUTOINCREMENT_CODEC" propstore/families/contexts tests
rg -n -F -- "_optional_float_input" propstore tests
rg -n -F -- "_optional_string" propstore tests
rg -n -F -- "_optional_int" propstore tests
rg -n -F -- "_claim_optional_float" propstore tests
rg -n -F -- "_nullable_text" propstore tests
rg -n -F -- "_nullable_int" propstore tests
rg -n -F -- "_nullable_float" propstore tests
rg -n -F -- "_optional_numeric" propstore tests
rg -n -F -- "_optional_float" propstore tests
rg -n -F -- "_parse_string_tuple" propstore tests
rg -n -F -- "coerce_active_micropublication" propstore tests
rg -n -F -- "propstore.core.active_claims" propstore tests
rg -n -- "class Active[A-Z]|\\bActive[A-Z][A-Za-z0-9_]*\\b" propstore tests
rg -n -F -- "ActiveClaim" propstore tests
rg -n -F -- "ActiveClaimInput" propstore tests
rg -n -F -- "ActiveMicropublicationInput" propstore tests
rg -n -F -- "ActiveClaimVariable" propstore tests
rg -n -F -- "ActiveClaimResolver" propstore tests
rg -n -F -- "ActiveWorldGraph" propstore tests
rg -n -F -- "WorldBindActiveReport" propstore tests
rg -n -F -- "ActiveClaim(" propstore tests
rg -n -F -- "ActiveMicropublication" propstore tests
rg -n -F -- "ClaimSidecarRows" propstore tests
rg -n -F -- "RawIdQuarantineSidecarRows" propstore tests
rg -n -F -- "PromotionBlockedSidecarRows" propstore tests
rg -n -F -- "SidecarClaimRelationStore" propstore tests
rg -n -F -- "find_similar_claim_rows" propstore tests
rg -n -F -- "find_similar_concept_rows" propstore tests
rg -n -F -- "from_mapping" propstore/core propstore/families propstore/world propstore/worldline propstore/support_revision tests
rg -n -F -- "Unsupported sidecar schema" propstore tests
rg -n -F -- "ProjectionSchemaError" propstore tests
rg -n -F -- "validate_derived_store_schema" propstore tests
rg -n -F -- "schema.validate_connection" propstore tests
rg -n -F -- "Rebuild with 'pks build'" propstore tests
rg -n -F -- "resolve_claim" propstore tests
rg -n -F -- "resolve_concept" propstore tests
rg -n -F -- "resolve_alias" propstore tests
rg -n -F -- "main_model" propstore tests
```

Gate: zero production hits for deleted projection, schema-validation, row,
coercer, and helper paths. Documentation hits are limited to notes,
workstreams, docs, and reports.

For `resolve_claim`, `resolve_concept`, `resolve_alias`, and `main_model`,
classify every hit. Per-family identity lookup wrappers, convenience methods,
and call sites that bypass generic Quire family reference/FK lookup or generic
main-model access must be zero-hit. Typed domain/world semantic resolution may
remain only when it is not a generic lookup wrapper under another name.

Current discovered Propstore queues from the 2026-05-20 audit, all still
subject to the zero-hit gates above:

- Phase 10 residual: `propstore/families/claims/projection_model.py` still
  contains `JUSTIFICATION_STORAGE_MODEL` and `JUSTIFICATION_TABLE`; the only
  current importer is `propstore/families/claims/declaration.py`.
- Micropublication queue: `propstore/families/micropublications/declaration.py`
  still defines projection rows, sidecar rows, projection models, row
  compilers, table creation, population, and selection helpers; production
  callers remain in `propstore/derived_build_plan.py`, `propstore/world/atms.py`,
  `propstore/world/model.py`, and `propstore/world/overlay.py`.
- Relation/stance queue: `propstore/families/relations/projection_model.py`
  still defines `RELATIONSHIP_ROW_MODEL`, `STANCE_ROW_MODEL`, and query-plan
  helpers; current consumers include `propstore/core/graph_build.py`,
  `propstore/core/analyzers.py`, `propstore/graph_export.py`,
  `propstore/aspic_bridge`, `propstore/support_revision`,
  `propstore/world/bound.py`, `propstore/world/overlay.py`, and
  `propstore/worldline/argumentation.py`.
- Raw runtime queue: `sqlite3.Connection`, `row_factory`, and
  `connect_sqlite_store` remain in family/world/runtime paths, especially
  claims/concepts sidecar runtime, embeddings, grounding/rules, relations,
  micropublications, and `propstore/world/model.py`.
- Active-object queue: `ActiveWorldGraph`, `WorldBindActiveReport`,
  `ActiveClaim`, `ActiveClaimInput`, `ActiveMicropublication`, and
  `ActiveMicropublicationInput` remain in production/test surfaces.
- Sidecar helper queue: `SidecarClaimRelationStore`,
  `find_similar_claim_rows`, and `find_similar_concept_rows` remain and must
  be replaced with generic Quire vector/session APIs plus typed Propstore
  owner reports.
- Current zero-hit queues that must stay zero-hit: `ActiveClaimResolver`,
  `main_model`, `Unsupported sidecar schema`, `ProjectionSchemaError`,
  `validate_derived_store_schema`, `schema.validate_connection`,
  `Rebuild with 'pks build'`, and generic `from_mapping` in the searched
  core/family/world/worldline/support-revision/test surfaces.

## Phase 17: Full Gates And Dependency Pin

### Quire Full Gates

Run from `C:\Users\Q\code\quire`:

```powershell
uv run pyright
uv run pytest -vv
```

### Propstore Full Gates

Run from `C:\Users\Q\code\propstore`:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label sqlalchemy-charter-full
```

### Dependency Pin Checklist

- [x] Push Quire first.
- [x] Pin Propstore to the pushed Quire commit or tag.
- [x] Update `uv.lock`.
- [x] Inspect parsed `pyproject.toml` dependencies and `[tool.uv.sources]`.
- [x] Confirm no Quire dependency entry resolves only from the local
  filesystem.

### Dependency Search Gates

Run from `C:\Users\Q\code\propstore`:

```powershell
rg -n -F -- "quire @ file" pyproject.toml uv.lock
rg -n -F -- "quire @ .." pyproject.toml uv.lock
rg -n -F -- "quire @ C:" pyproject.toml uv.lock
rg -n -F -- "[tool.uv.sources]" pyproject.toml
rg -n -F -- "path =" pyproject.toml
rg -n -F -- "workspace = true" pyproject.toml
```

Gate: no local path, workspace, or file URL Quire dependency.

### 2026-05-21 Phase 17 Evidence

- Quire projection deletion and public charter/schema exports are complete and
  pushed through `ac05ff5e66d8a744ec0be9406f8912c81dfaa6bd`; Propstore
  dependency files are pinned to that pushed commit in
  `7664c87c Pin Quire public charter API`.
- Propstore focused typed-family regression slice is committed as
  `8a187282 Carry typed fixtures through claim metadata`.
- Propstore focused ASPIC/IST typed-fixture cleanup is committed as
  `f26d402e Use typed ASPIC fixture inputs`.
- Propstore remediation bridge typed-fixture cleanup is committed as
  `1a2a2c6b Use typed remediation bridge fixtures`.
- Propstore preference typed-claim cleanup is committed as
  `eea33f7b Use typed preference claim fixtures`.
- Propstore revision assertion cleanup is committed as
  `565a8653 Include claim content in revision assertions`.
- Propstore context/worldline typed fixture cleanup is committed as
  `d22a0066 Use typed context worldline fixtures`.
- Propstore web/concept charter fixture cleanup is committed as
  `7c5b3b4f Align web concept fixtures with charters`.
- Propstore CEL checker concept-id fixture cleanup is committed as
  `0ae57cc9 Use concept id field in CEL fixture`.
- Propstore resolution-helper typed concept fixture cleanup is committed as
  `642b85e7 Use typed resolution concept fixtures`.
- Propstore review-regression typed fixture cleanup is committed as
  `656147a7 Use typed review regression fixtures`.
- Propstore PrAF store typed fixture cleanup is committed as
  `9de025ec Use typed PrAF store fixture`.
- Propstore web revision base JSON serialization cleanup is committed as
  `086ac24a Serialize revision base through owner payload`.
- Propstore algorithm canonical AST projection cleanup is committed as
  `12c9436f Populate algorithm canonical AST`.
- Propstore SI numeric normalization cleanup is committed as
  `520eae85 Normalize claim numeric SI values`.
- Propstore worldline dependency identity cleanup is committed as
  `ceb995ac Use canonical worldline dependency ids`.
- Passing focused gates:
  - `uv run pyright propstore`
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-regression-clusters-7 ...`
    passed 53 tests across value resolver, PrAF, ATMS, and WS-F ASPIC.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-quire-public-api tests/test_quire_boundary.py::test_propstore_quire_imports_are_public`
    passed 1 test.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-aspic-ist-typed-fixtures tests/architecture/test_backend_identity_contracts.py tests/architecture/test_ist_projection_contract.py tests/test_literal_keys.py tests/test_defeasibility_aspic_integration.py tests/test_aspic_bridge_review_v2.py`
    passed 30 tests.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-remediation-bridge-typed-2 tests/remediation/phase_4_layers/test_T4_8_exception_defeats_post_preference.py tests/remediation/phase_5_bridge/test_T5_11_exception_sibling_survival.py tests/remediation/phase_5_bridge/test_T5_1_undermines_preference_sensitive.py tests/remediation/phase_5_bridge/test_T5_6_bridge_edge_domain_invariant.py tests/remediation/phase_5_bridge/test_T5_7_justification_unknown_premise.py tests/remediation/phase_5_bridge/test_T5_8_projection_typed_claim_identity.py tests/remediation/phase_5_bridge/test_T5_9_projection_premise_dependency_split.py`
    passed 7 tests.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-preference-typed-claims tests/test_preference.py tests/remediation/phase_3_ignorance/test_T3_3_preference_missing_metadata_vacuous.py`
    passed 13 tests.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-revision-typed-claims-2 tests/test_revision_assertion_identity.py tests/test_revision_projection.py tests/test_revision_state.py`
    passed 7 tests.
  - `uv run pyright propstore` passed with 0 errors after the revision
    assertion identity production change.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-context-worldline-typed tests/test_context_lifting_ws5.py::test_bound_world_projection_honors_local_lifting_exception tests/test_contexts.py::TestBoundWorldContextLifting tests/test_contexts.py::TestWorldQueryContextLifting::test_world_query_bind_loads_lifting_rules_from_sidecar tests/test_worldline_praf.py tests/test_lifting_blocked_in_provenance.py::test_ws_j_worldline_dependencies_include_blocked_lifting_exception`
    passed 7 tests.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-web-demo-source-charter-3 tests/test_web_demo_fixture.py::test_web_demo_fixture_exercises_first_surface_states tests/test_concept_views.py`
    passed 6 tests.
  - `uv run pyright propstore` passed with 0 errors after the concept-view
    production change.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-cel-concept-id tests/test_cel_checker.py::TestBuildCelRegistry::test_store_projection_rejects_missing_kind`
    passed 1 test.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-resolution-typed-concepts tests/test_resolution_helpers.py`
    passed 5 tests.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-review-regression-typed-2 tests/test_review_regressions.py`
    passed 6 tests.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-praf-store-typed tests/test_praf.py::test_build_praf_from_store`
    passed 1 test.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-web-revision-json tests/test_web_revision_readonly.py::test_web_revision_base_route_is_read_only_app_backed`
    passed 1 test.
  - `uv run pyright propstore` passed with 0 errors after the web revision
    owner-payload production change.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-algorithm-canonical-ast-2 tests/test_build_sidecar.py::TestAlgorithmClaim tests/test_build_sidecar.py::TestAlgorithmBindings::test_algorithm_canonical_ast_includes_bindings`
    passed 4 tests.
  - `uv run pyright propstore` passed with 0 errors after the algorithm AST
    production change.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-si-normalized-values tests/test_build_sidecar.py::TestClaimValueSI tests/test_cli.py::TestClaimShow::test_owner_build_claim_view_reports_si_value tests/test_cli.py::TestClaimShow::test_claim_show_displays_si_values tests/test_cli.py::TestClaimShow::test_claim_show_json_uses_report_shape`
    passed 7 tests.
  - `uv run pyright propstore` passed with 0 errors after the SI normalization
    production change.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-worldline-dependency-ids-2 tests/test_worldline_properties.py::TestSoundness::test_force_dependency_on_g_earth_is_necessary tests/test_worldline_properties.py::TestCompleteness::test_changing_g_earth_changes_force tests/test_worldline_properties.py::TestBindingIsolation::test_binding_isolation`
    passed 3 tests.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-si-normalized-values-2 tests/test_build_sidecar.py::TestClaimValueSI tests/test_cli.py::TestClaimShow::test_owner_build_claim_view_reports_si_value tests/test_cli.py::TestClaimShow::test_claim_show_displays_si_values tests/test_cli.py::TestClaimShow::test_claim_show_json_uses_report_shape`
    passed 7 tests after the no-canonical-unit correction.
  - `uv run pyright propstore` passed with 0 errors after the canonical
    dependency id and no-canonical-unit correction.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-bound-conflicts-boundary tests/test_world_bound_conflicts_cache.py`
    passed 5 tests after moving catalog-only concept resolution behind the
    catalog-store boundary and converting the non-catalog conflict fixture to
    typed `Claim`/`ConflictWitness` objects.
  - `uv run pyright propstore` passed with 0 errors after the conflict query
    boundary repair.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-form-utils-deleted-2 tests/test_lemon_form_dimension_boundary.py`
    passed 5 tests after keeping `propstore/form_utils.py` deleted and removing
    the direct dimension API import from `propstore.families.forms.stages`.
  - `uv run pyright propstore` passed with 0 errors after the forms-stage
    dimension API import cleanup.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-source-blocked-rows-2 tests/remediation/phase_2_gates/test_T2_2r_source_promote_ambiguous_concept_quarantine.py tests/remediation/phase_2_gates/test_T2_2s_source_promote_unresolved_concept_quarantine.py tests/test_source_promotion_alignment.py::test_promote_source_branch_materializes_blocked_rows_from_source_state tests/test_promote_atomicity.py::test_promote_returns_in_memory_blocked_diagnostics_after_committed_mirror tests/test_cli_source_status.py::test_source_status_report_lists_blocked_promotion_rows tests/test_cli_source_status.py::test_source_status_lists_blocked_promotion_rows tests/remediation/phase_7_race_atomicity/test_T7_5b_promotion_diagnostic_scope.py tests/remediation/phase_7_race_atomicity/test_T7_5d_promotion_blocked_id_collision.py tests/remediation/phase_7_race_atomicity/test_T7_5e_promotion_blocked_fk_payload.py`
    passed 9 tests after `PromotionBlockedClaimFact` carried the real
    `ClaimType`, `compile_promotion_blocked_models` emitted blocked `Claim`
    models, and the flush path preserved existing non-blocked canonical claim
    rows.
  - `uv run pyright propstore` passed with 0 errors after the source promotion
    blocked-row projection repair.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-claim-source-relationship tests/test_world_query.py::TestUnboundQueries::test_get_claim_joins_source_by_source_slug`
    passed 1 test after the claim charter declared the source relationship and
    `WorldQuery.get_claim` eager-loaded it through the Quire SQLAlchemy model.
  - `uv run pyright propstore` passed with 0 errors after the claim-source
    relationship repair.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label phase17-algorithm-stage-charter-2 tests/test_algorithm_stage_types.py`
    passed 3 tests after `claim_algorithm_payload.algorithm_stage` kept `str`
    storage and carried `propstore.core.algorithm_stage.AlgorithmStage` through
    charter field metadata.
  - `uv run pyright propstore` passed with 0 errors after the algorithm-stage
    charter metadata repair.
- Full Propstore gate:
  - `powershell -File scripts/run_logged_pytest.ps1 -Label sqlalchemy-charter-full-2`
    failed: 125 failed, 3474 passed, 4 skipped.
  - Log: `logs/test-runs/sqlalchemy-charter-full-2-20260521-135558.log`.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label sqlalchemy-charter-full-3`
    failed: 58 failed, 3541 passed, 4 skipped.
  - Log: `logs/test-runs/sqlalchemy-charter-full-3-20260521-143149.log`.
  - `powershell -File scripts/run_logged_pytest.ps1 -Label sqlalchemy-charter-full-4`
    failed: 35 failed, 3564 passed, 4 skipped.
  - Log: `logs/test-runs/sqlalchemy-charter-full-4-20260521-145951.log`.
  - Remaining failure clusters from full-4:
    - Conflict query boundary: non-catalog stores must not require catalog
      concept lookup before the cheap active-claim/conflict pass-through path.
    - Source promotion blocked-row projection: blocked source-local claims are
      still omitted from `claim_core` promotion-status rows.
    - Source/source-slug and source status display paths still read fields no
      longer present on the current source charter shape.
    - Typed fixture drift remains in ATMS, PrAF, semantic repair, fragility,
      sensitivity, micropublication, and preference import tests; fix fixtures
      to build charter/domain objects, not production dict fallbacks.
    - Argumentation/vacuous stance behavior must reject vacuous attackers at
      the typed relation boundary, not via compatibility wrappers.
    - Demo and worldline tests still assert source-local handles where current
      runtime surfaces expose canonical claim ids.
    - Sidecar cache-key schema fields and contract manifest snapshots must be
      regenerated/versioned through the intended contract workflow after
      production semantics settle.
    - Deleted `propstore/form_utils.py` test assumes the old file exists; keep
      the production deletion and update the gate to assert absence.

Current full-gate repair queue, deletion-first:

- Replace remaining dict-shaped context/worldline test fixtures with typed
  `Claim`, `Stance`, `CanonicalJustification`, and typed compiled-graph
  fixtures. Do not add dict fallback acceptance to production ASPIC, revision,
  worldline, or context-lifting APIs. Direct ASPIC/IST callers and remediation
  bridge callers from the 2026-05-21 focused slices are converted and passing.
- Continue repairing any remaining source/web fixture drift by using current
  charter fields; do not add old source columns such as `origin_type` back as
  compatibility columns. The first web demo fixture now writes the current
  source charter shape.
- Continue repairing canonical typed-model construction in tests that set
  read-only semantic properties; use charter fields and family semantic
  properties directly. The concept view fixture now uses `Concept.id` instead
  of `Concept.concept_id`.
- Rerun the full Propstore gate and repair any remaining failures
  deletion-first.
- Contract manifest failures are not deferrable; after charter-field changes,
  update the manifest/version evidence through the intended contract workflow,
  not by weakening the manifest test.

## Completion Checklist

The cutover is complete only when every item is checked:

- [ ] Quire has a SQLAlchemy-backed charter/schema engine.
- [ ] Quire derived-store handles open read-only SQLAlchemy sessions.
- [ ] Quire schema catalogs describe the derived store from the same charters
  that generated the mappings.
- [ ] Quire charters compose with existing `ArtifactFamily`, document-store,
  placement, and reference/FK APIs.
- [ ] Quire projection modules and projection public exports are deleted.
- [ ] Propstore supplies domain charters for every sidecar family.
- [ ] `propstore/derived_build.py` and `propstore/derived_build_plan.py` use
  Quire writable sessions and charter catalogs.
- [ ] Propstore no longer imports Quire projection primitives.
- [ ] Propstore has no family `projection_model.py` files.
- [ ] Propstore has no duplicate `*Row` model layer for domain objects.
- [ ] `claim.concept_links` is the primary relationship.
- [ ] `ClaimConceptLink` owns role, ordinal, and binding metadata.
- [ ] Micropublication claim links, aliases, parameterizations, context
  lifting records, stances, and conflicts are typed models or association
  objects.
- [ ] Source-local and canonical states are explicit charter/lifecycle states.
- [ ] Manual helper/coercer families listed in the search gates are deleted.
- [ ] Remaining IO boundary constructors use boundary-specific names and do
  not use the generic `from_mapping` name.
- [ ] No PascalCase `Active*` production/report/model type remains.
- [ ] `WorldQuery` uses Quire sessions and typed model queries.
- [ ] `WorldQuery` has no projection-schema validation wrapper and does not
  rewrite Quire schema/catalog validation failures into old sidecar-schema
  messages.
- [ ] Every row in `inventory-matrix.md` has a final delete, move, replace, or
  keep-as-semantic-owner outcome in a commit message or final closure report.
- [ ] Every family cutover has a passing data-parity gate for row counts, key
  sets, the exact owner-layer query/API results named in the child workstream,
  and every FTS, vector, and diagnostic comparison explicitly listed in the
  child workstream.
- [ ] App/CLI/web surfaces call owner-layer APIs.
- [ ] Quire and Propstore full gates pass.
- [ ] Propstore is pinned to a pushed Quire commit or tag, never a local
  checkout.
