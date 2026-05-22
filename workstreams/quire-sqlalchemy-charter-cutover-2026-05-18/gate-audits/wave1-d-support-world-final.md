# Wave 1-D Support, World, And Final Gate Audit

Date: 2026-05-21

## Files Audited

- `workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/11-rules-grounding-calibration-embeddings.md`
- `workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/12-world-query-graph-reasoning.md`
- `workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/13-final-deletion-gates.md`

## Scope

- Did not use `git log`.
- Did not run `pyright`.
- Did not run `pytest`.
- Ran only read-only `rg` searches from `C:\Users\Q\code\propstore` or `C:\Users\Q\code\quire` as required by each gate path.

## Result

Pass, with classified non-zero inspection hits.

- Phase 11 support-family old-path gates: pass. All required absence/deletion searches were zero-hit.
- Phase 12 world/query/graph gates: pass. All required absence/deletion searches were zero-hit.
- Phase 13 Quire projection gates: pass. All required absence/deletion searches were zero-hit from `C:\Users\Q\code\quire`.
- Phase 13 Propstore projection/helper/active-object gates: pass. All required absence/deletion searches were zero-hit.
- Phase 13 dependency local-path gates: pass. Local path, file URL, and workspace searches were zero-hit.
- Classification gates: pass. `resolve_claim` and `resolve_concept` hits are semantic resolution/rendering behavior, not per-family identity lookup wrappers. `resolve_alias` and `main_model` were zero-hit.

## Non-Zero Classified Hits

These were not deletion-gate failures.

- `rg -n -F -- "[tool.uv.sources]" pyproject.toml`
  - `pyproject.toml:81:[tool.uv.sources]`
  - Expected meaning: inspect the dependency source section. This is not an absence gate; the local-path dependency gates around it were zero-hit.
- `rg -n -F -- "quire.projection_mapping" propstore tests scripts`
  - `scripts\typed_metadata_inventory.py:642:                if module == "quire.projection_mapping" or module.startswith("quire.projection_mapping."):`
  - Expected meaning: historical inventory classification logic. The final file explicitly allows this retained inventory string.
- `rg -n -F -- "resolve_claim" propstore tests`
  - `propstore\worldline\resolution.py:173:        _resolve_claim_target,`
  - `propstore\worldline\resolution.py:221:            _resolve_claim_input,`
  - `propstore\worldline\resolution.py:282:def _resolve_claim_target(`
  - `propstore\worldline\resolution.py:529:def _resolve_claim_input(`
  - `propstore\world\resolution.py:187:def _resolve_claim_graph_argumentation(`
  - `propstore\world\resolution.py:712:            winner_id, reason = _resolve_claim_graph_argumentation(`
  - `tests\test_resolution_helpers.py:19:    _resolve_claim_graph_argumentation,`
  - `tests\test_resolution_helpers.py:231:    winner, reason = _resolve_claim_graph_argumentation(`
  - `tests\test_resolution_helpers.py:256:    winner, reason = _resolve_claim_graph_argumentation(`
  - Classification: semantic world/worldline target, input, and argumentation resolution behavior. No per-family identity lookup wrapper hit found.
- `rg -n -F -- "resolve_concept" propstore tests`
  - `propstore\description_generator.py:55:def _resolve_concept_name(`
  - `propstore\description_generator.py:82:    name = _resolve_concept_name(claim.output_concept, concept_registry)`
  - `propstore\description_generator.py:124:    target_name = _resolve_concept_name(claim.target_concept, concept_registry)`
  - Classification: description-rendering concept-id-to-display-name behavior. No generic family reference lookup wrapper hit found.

## Failing Hits

None.

## Ambiguous Or Uninterpretable Gates

None.

## Commands Run

### From `C:\Users\Q\code\propstore`

```powershell
rg -n -F -- "ProjectionTable(" propstore/families/rules propstore/families/calibration propstore/families/embeddings tests
rg -n -F -- "VecProjection" propstore/families/embeddings tests
rg -n -F -- "sqlite3.Connection" propstore/families/rules propstore/families/calibration propstore/families/embeddings propstore/grounding tests
rg -n -F -- "GROUNDED_FACT_PROJECTION" propstore tests
rg -n -F -- "GROUNDED_FACT_EMPTY_PREDICATE_PROJECTION" propstore tests
rg -n -F -- "GROUNDED_BUNDLE_INPUT_PROJECTION" propstore tests
rg -n -F -- "CALIBRATION_COUNTS_PROJECTION" propstore tests
rg -n -F -- "EMBEDDING_MODEL_PROJECTION" propstore tests
rg -n -F -- "CLAIM_EMBEDDING_STATUS_PROJECTION" propstore tests
rg -n -F -- "CONCEPT_EMBEDDING_STATUS_PROJECTION" propstore tests
rg -n -F -- "CONCEPT_VEC_PROJECTION" propstore tests
rg -n -F -- "GroundedFactProjectionRow" propstore tests
rg -n -F -- "GroundedFactEmptyPredicateProjectionRow" propstore tests
rg -n -F -- "GroundedBundleInputProjectionRow" propstore tests
rg -n -F -- "CalibrationCountsProjectionRow" propstore tests
rg -n -F -- "create_grounded_fact_table" propstore tests
rg -n -F -- "populate_grounded_facts" propstore tests
rg -n -F -- "_persist_bundle_inputs" propstore tests
rg -n -F -- "_read_bundle_inputs" propstore tests
rg -n -F -- "read_grounded_facts" propstore tests
rg -n -F -- "read_grounded_bundle" propstore tests
rg -n -F -- "load_calibration_counts" propstore tests
rg -n -F -- "ensure_embedding_tables" propstore tests
rg -n -F -- "SidecarEmbeddingRegistry" propstore tests
rg -n -F -- "_SidecarEntityEmbeddingStore" propstore tests
rg -n -F -- "SidecarClaimEmbeddingStore" propstore tests
rg -n -F -- "SidecarConceptEmbeddingStore" propstore tests
rg -n -F -- "SidecarEmbeddingSnapshotStore" propstore tests
rg -n -F -- "SidecarClaimRelationStore" propstore tests
rg -n -F -- "find_similar_claim_rows" propstore tests
rg -n -F -- "find_similar_concept_rows" propstore tests
rg -n -F -- "from_mapping" propstore/core/store_results.py tests
rg -n -F -- "connect_sqlite_store" propstore/families/claims/sidecar_runtime.py propstore/families/concepts/sidecar_runtime.py tests
rg -n -F -- "connect_sqlite_store_readonly" propstore/families/claims/sidecar_runtime.py propstore/families/concepts/sidecar_runtime.py tests
rg -n -F -- "sqlite3.Connection" propstore/families/claims/sidecar_runtime.py propstore/families/concepts/sidecar_runtime.py tests
rg -n -F -- "row_factory" propstore/families/claims/sidecar_runtime.py propstore/families/concepts/sidecar_runtime.py tests
rg -n -F -- "ProjectionTable(" propstore/families propstore/core propstore/world propstore/worldline tests
rg -n -F -- "ProjectionModel" propstore/families propstore/core propstore/world propstore/worldline tests
rg -n -F -- "sqlite3.Connection" propstore/world propstore/families propstore/core propstore/worldline tests
rg -n -F -- "sqlite3.Connection" propstore/world propstore/families tests
rg -n -F -- "row_factory" propstore/world propstore/families tests
rg -n -F -- "connect_sqlite_store" propstore/world propstore/families tests
rg -n -F -- "ProjectionRow" propstore/world propstore/families tests
rg -n -F -- "ProjectionModel" propstore/world propstore/core propstore/graph_export.py propstore/worldline propstore/support_revision propstore/aspic_bridge tests
rg -n -F -- "from_mapping" propstore/core propstore/families propstore/world propstore/worldline propstore/support_revision tests
rg -n -F -- "from_row_mapping" propstore/core propstore/families propstore/world propstore/worldline propstore/support_revision tests
rg -n -F -- "_claim_rows" propstore/world tests
rg -n -F -- "._conn" propstore tests/test_graph_export.py
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
rg -n -F -- "ProjectionTable" propstore tests
rg -n -F -- "ProjectionSchema" propstore tests
rg -n -F -- "ProjectionIndex" propstore tests
rg -n -F -- "ProjectionColumn" propstore tests
rg -n -F -- "ProjectionSelectedColumn" propstore tests
rg -n -F -- "ProjectionCodec" propstore tests
rg -n -F -- "ScalarPath" propstore tests
rg -n -F -- "ReferencePath" propstore tests
rg -n -F -- "FtsProjection" propstore tests
rg -n -F -- "CLAIM_ROW_MODEL" propstore tests
rg -n -F -- "CONCEPT_ROW_MODEL" propstore tests
rg -n -F -- "STANCE_ROW_MODEL" propstore tests
rg -n -F -- "RELATIONSHIP_ROW_MODEL" propstore tests
rg -n -F -- "SOURCE_PROJECTION" propstore tests
rg -n -F -- "CONCEPT_FTS_PROJECTION" propstore tests
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
rg -n -F -- "ActiveClaimVariable" propstore tests
rg -n -F -- "ActiveClaim(" propstore tests
rg -n -F -- "ActiveMicropublication" propstore tests
rg -n -F -- "ClaimSidecarRows" propstore tests
rg -n -F -- "RawIdQuarantineSidecarRows" propstore tests
rg -n -F -- "PromotionBlockedSidecarRows" propstore tests
rg -n -F -- "resolve_claim" propstore tests
rg -n -F -- "resolve_concept" propstore tests
rg -n -F -- "resolve_alias" propstore tests
rg -n -F -- "main_model" propstore tests
rg -n -F -- "quire @ file" pyproject.toml uv.lock
rg -n -F -- "quire @ .." pyproject.toml uv.lock
rg -n -F -- "quire @ C:" pyproject.toml uv.lock
rg -n -F -- "[tool.uv.sources]" pyproject.toml
rg -n -F -- "path =" pyproject.toml
rg -n -F -- "workspace = true" pyproject.toml
rg -n -F -- "file://" pyproject.toml uv.lock
rg -n -F -- "C:\\Users\\Q\\code\\quire" pyproject.toml uv.lock
rg -n -F -- "from quire.projections" propstore tests
rg -n -F -- "from quire.projection_mapping" propstore tests
rg -n -F -- "quire.projections" propstore tests scripts
rg -n -F -- "quire.projection_mapping" propstore tests scripts
rg -n -F -- "load_vec_extension" propstore tests
rg -n -F -- "_require_sqlite_vec" propstore tests
rg -n -F -- "CLAIM_VEC_PROJECTION" propstore tests
rg -n -F -- "CLAIM_EMBEDDING_JOIN_COLUMNS" propstore tests
rg -n -F -- "CLAIM_EMBEDDING_JOIN_SOURCE" propstore tests
rg -n -F -- "select_claim_embedding_rows" propstore tests
```

### From `C:\Users\Q\code\quire`

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
