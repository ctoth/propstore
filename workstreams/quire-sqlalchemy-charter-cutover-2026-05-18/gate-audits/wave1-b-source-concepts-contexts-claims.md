# Wave 1B Gate Audit: Source, Concepts, Contexts, Claims

Date: 2026-05-21

## Scope

Files audited:

- `05-source-and-diagnostics.md`
- `06-forms-concepts-parameterizations.md`
- `07-contexts-lifting.md`
- `08-claims-active-claims.md`

Commands were run from `C:\Users\Q\code\propstore`. No extracted gate used
`quire/tests`, so no command was run from `C:\Users\Q\code\quire`.

Not run by request: `git log`, `pyright`, `pytest`.

Interpretation rule used here:

- Old-path/deletion searches are pass only when zero-hit, except where the
  workstream text names an allowed nonzero owner residual.
- Correction/follow-up searches written as zero-hit gates fail on any
  production or test hit.
- A nonzero search that the file explicitly describes as an expected residual
  is reported as open/ambiguous rather than a deletion-gate failure.

## 05 Source And Diagnostics

Pass: the required source/diagnostics deletion gates returned zero hits:

```powershell
rg -n -F -- "SourceProjectionRow" propstore tests
rg -n -F -- "SOURCE_PROJECTION" propstore tests
rg -n -F -- "quality_json" propstore tests
rg -n -F -- "derived_from_json" propstore tests
rg -n -F -- "_opinion_from_mapping" propstore/core/claim_values.py tests
rg -n -F -- "from_mapping" propstore/core/claim_values.py tests
rg -n -F -- "SourceStatusDiagnosticRow" propstore tests
rg -n -F -- "QuarantinableWriter" propstore tests
rg -n -F -- "compile_promotion_blocked_diagnostic_rows" propstore tests
rg -n -F -- "has_build_diagnostics_table" propstore tests
rg -n -F -- "select_source_status_diagnostic_rows" propstore tests
rg -n -F -- "BUILD_DIAGNOSTICS_PROJECTION" propstore/families/diagnostics tests
rg -n -F -- "ProjectionTable(" propstore/families/sources propstore/families/diagnostics tests
rg -n -F -- "BUILD_DIAGNOSTICS_PROJECTION" propstore tests
rg -n -F -- "def resolve_claim" propstore tests
```

Fail/open correction hits:

```text
rg -n -F -- 'derived.schema.table("claim_core")' propstore tests
propstore\source\status.py:56

rg -n -F -- 'derived.schema.table("build_diagnostics")' propstore tests
propstore\families\diagnostics\declaration.py:96
propstore\families\diagnostics\declaration.py:111
propstore\families\diagnostics\declaration.py:135

rg -n -F -- 'derived.schema.model("build_diagnostics")' propstore tests
propstore\families\diagnostics\declaration.py:97
propstore\families\diagnostics\declaration.py:112

rg -n -F -- 'schema.model("claim_core")' propstore tests
propstore\families\claims\sidecar_runtime.py:78
propstore\families\claims\sidecar_runtime.py:116
propstore\families\embeddings\declaration.py:95
propstore\families\embeddings\declaration.py:278
propstore\world\model.py:287
propstore\world\model.py:311
propstore\world\model.py:332
propstore\world\model.py:409
propstore\world\model.py:453
propstore\world\model.py:628
propstore\world\model.py:841
```

Expected meaning: the original source/diagnostic projection deletion gates
pass, but the generic family-metadata correction remains open.

## 06 Forms, Concepts, Parameterizations

Pass: the required forms/concepts projection/read-model deletion gates returned
zero hits:

```powershell
rg -n -F -- "FORM_PROJECTION" propstore tests
rg -n -F -- "FORM_ALGEBRA_PROJECTION" propstore tests
rg -n -F -- "ProjectionTable(" propstore/families/concepts propstore/families/forms tests
rg -n -F -- "propstore.form_utils" propstore tests
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
rg -n -F -- "def resolve_alias" propstore tests
rg -n -F -- "resolve_concept_id" propstore tests
rg -n -F -- "resolve_sidecar_concept_id" propstore tests
rg -n -F -- "_get_concept_logical_id_index" propstore tests
rg -n -F -- 'table == "concept"' propstore tests
rg -n -F -- "WorldQuery(derived_store=derived_store).resolve_concept" propstore tests
rg -n -F -- "world.resolve_concept(" propstore tests
rg -n -F -- 'getattr(world, "resolve_concept"' propstore tests
rg -n -F -- "def resolve_concept" propstore tests
```

Failing correction hits:

```text
rg -n -F -- 'schema.model("alias")' propstore tests
propstore\families\embeddings\declaration.py:122
tests\test_sidecar_alias_projection.py:40

rg -n -F -- 'schema.model("concept")' propstore/world propstore/app tests
propstore/app\concepts\display.py:51
propstore/world\model.py:235
propstore/world\model.py:259
propstore/world\model.py:552
propstore/world\model.py:696
propstore/world\model.py:840
tests\test_concept_workflows.py:39
tests\test_sidecar_concept_projection.py:55

rg -n -F -- 'schema.model("concept")' propstore tests
propstore\app\concepts\display.py:51
propstore\families\embeddings\declaration.py:121
propstore\families\embeddings\declaration.py:327
propstore\world\model.py:235
propstore\world\model.py:259
propstore\world\model.py:552
propstore\world\model.py:696
propstore\world\model.py:840
tests\test_concept_workflows.py:39
tests\test_sidecar_concept_projection.py:55
```

Expected meaning: the original forms/concepts projection deletion gates pass,
but direct concept/alias model lookup still violates the family-reference
correction gates.

## 07 Contexts And Lifting

Pass: prerequisite and required context projection/read-model deletion gates
returned zero hits:

```powershell
rg -n -F -- "ProjectionTable" propstore/families/contexts propstore/derived_build.py propstore/derived_build_plan.py tests
rg -n -F -- "ProjectionModel" propstore/families/contexts tests
rg -n -F -- "sqlite3.Connection" propstore/families/contexts propstore/context_lifting.py propstore/app/contexts.py tests
rg -n -F -- "CONTEXT_TABLE" propstore tests
rg -n -F -- "CONTEXT_ASSUMPTION_TABLE" propstore tests
rg -n -F -- "CONTEXT_LIFTING_RULE_TABLE" propstore tests
rg -n -F -- "CONTEXT_LIFTING_MATERIALIZATION_TABLE" propstore tests
rg -n -F -- "CONTEXT_SCHEMA" propstore tests
rg -n -F -- "CONTEXT_MODEL" propstore tests
rg -n -F -- "CONTEXT_ASSUMPTION_MODEL" propstore tests
rg -n -F -- "CONTEXT_LIFTING_RULE_MODEL" propstore tests
rg -n -F -- "CONTEXT_LIFTING_MATERIALIZATION_MODEL" propstore tests
rg -n -F -- "CONTEXT_TABLES" propstore tests
rg -n -F -- "ProjectionModel(" propstore/families/contexts tests
rg -n -F -- "create_context_tables" propstore tests
rg -n -F -- "populate_contexts" propstore tests
rg -n -F -- "compile_context_sidecar_rows" propstore tests
rg -n -F -- "compile_context_lifting_materialization_rows" propstore tests
rg -n -F -- "_nullable_text" propstore/families/contexts tests
rg -n -F -- "_json_or_none" propstore/families/contexts tests
rg -n -F -- "_json_mapping" propstore/families/contexts tests
rg -n -F -- "_json_string_tuple" propstore/families/contexts tests
rg -n -F -- "TEXT_CODEC" propstore/families/contexts tests
rg -n -F -- "PARAMETERS_CODEC" propstore/families/contexts tests
rg -n -F -- "CONDITIONS_CODEC" propstore/families/contexts tests
rg -n -F -- "PROVENANCE_CODEC" propstore/families/contexts tests
rg -n -F -- "AUTOINCREMENT_CODEC" propstore/families/contexts tests
rg -n -F -- "resolve_concept(" propstore/context_lifting.py propstore/families/contexts propstore/aspic_bridge propstore/worldline tests
rg -n -F -- "resolve_claim(" propstore/context_lifting.py propstore/families/contexts propstore/aspic_bridge propstore/worldline tests
rg -n -F -- "def resolve_context" propstore tests
rg -n -F -- "def resolve_lifting" propstore tests
```

Failing correction hits:

```text
rg -n -F -- 'schema.model("context")' propstore/families/contexts propstore/context_lifting.py propstore/aspic_bridge propstore/worldline tests
propstore/families/contexts\declaration.py:191
tests\test_contexts.py:371

rg -n -F -- 'schema.model("context_assumption")' propstore/families/contexts propstore/context_lifting.py propstore/aspic_bridge propstore/worldline tests
propstore/families/contexts\declaration.py:192
tests\test_contexts.py:372

rg -n -F -- 'schema.model("context_lifting_rule")' propstore/families/contexts propstore/context_lifting.py propstore/aspic_bridge propstore/worldline tests
propstore/families/contexts\declaration.py:193
tests\test_contexts.py:373

rg -n -F -- 'schema.model("context_lifting_materialization")' propstore/families/contexts propstore/context_lifting.py propstore/aspic_bridge propstore/worldline tests
tests\test_context_lifting_ws5.py:263
tests\test_sidecar_contexts.py:121
```

Expected meaning: the original context/lifting projection deletion gates pass,
but direct context-family model lookup remains open.

## 08 Claims And Active Claims

Pass: these required old-path gates returned zero hits:

```powershell
rg -n -F -- "ProjectionTable" propstore/families/claims propstore/derived_build.py propstore/derived_build_plan.py tests
rg -n -F -- "ProjectionModel" propstore/families/claims tests
rg -n -F -- "CLAIM_CORE_STORAGE_MODEL" propstore tests
rg -n -F -- "CLAIM_CONCEPT_LINK_STORAGE_MODEL" propstore tests
rg -n -F -- "CLAIM_NUMERIC_PAYLOAD_STORAGE_MODEL" propstore tests
rg -n -F -- "CLAIM_TEXT_PAYLOAD_STORAGE_MODEL" propstore tests
rg -n -F -- "CLAIM_ALGORITHM_PAYLOAD_STORAGE_MODEL" propstore tests
rg -n -F -- "CLAIM_ROW_MODEL" propstore tests
rg -n -F -- "CLAIM_ROW_QUERY_PLAN" propstore tests
rg -n -F -- "CLAIM_FTS_PROJECTION" propstore tests
rg -n -F -- "CLAIM_EMBEDDING_STATUS_PROJECTION" propstore tests
rg -n -F -- "CLAIM_EMBEDDING_JOIN_SOURCE" propstore tests
rg -n -F -- "CLAIM_EMBEDDING_JOIN_COLUMNS" propstore tests
rg -n -F -- "CLAIM_VEC_PROJECTION" propstore tests
rg -n -F -- "CLAIM_CORE_TABLE" propstore tests
rg -n -F -- "CLAIM_CONCEPT_LINK_TABLE" propstore tests
rg -n -F -- "CLAIM_NUMERIC_PAYLOAD_TABLE" propstore tests
rg -n -F -- "CLAIM_TEXT_PAYLOAD_TABLE" propstore tests
rg -n -F -- "CLAIM_ALGORITHM_PAYLOAD_TABLE" propstore tests
rg -n -F -- "CLAIM_STORAGE_TABLES" propstore tests
rg -n -F -- "compile_claim_sidecar_rows" propstore tests
rg -n -F -- "populate_claims" propstore tests
rg -n -F -- "ProjectionRow" propstore/families/claims
rg -n -F -- "BUILD_DIAGNOSTICS_PROJECTION" propstore/families/claims tests
rg -n -F -- "ClaimSidecarRows" propstore tests
rg -n -F -- "RawIdQuarantineSidecarRows" propstore tests
rg -n -F -- "PromotionBlockedSidecarRows" propstore tests
rg -n -F -- "_optional_float_input" propstore tests
rg -n -F -- "_optional_string" propstore tests
rg -n -F -- "_optional_int" propstore tests
rg -n -F -- "TypedClaimFields" propstore tests
rg -n -F -- "prepare_claim_insert_row" propstore tests
rg -n -F -- "prepare_claim_concept_link_rows" propstore tests
rg -n -F -- "_iter_claim_concept_link_values" propstore tests
rg -n -F -- "_claim_concept_link_values_for_declaration" propstore tests
rg -n -F -- "canonicalize_claim_for_storage" propstore tests
rg -n -F -- "extract_numeric_claim_fields" propstore tests
rg -n -F -- "extract_typed_claim_fields" propstore tests
rg -n -F -- "resolve_equation_sympy" propstore tests
rg -n -F -- "resolve_algorithm_storage" propstore tests
rg -n -F -- "extract_deferred_stance_rows_with_diagnostics" propstore tests
rg -n -F -- "propstore.core.active_claims" propstore tests
rg -n -F -- "ActiveClaimInput" propstore tests
rg -n -F -- "ActiveClaimVariable" propstore tests
rg -n -F -- "ActiveClaim.from_claim" propstore tests
rg -n -F -- "ActiveClaim.from_mapping" propstore tests
rg -n -F -- "ActiveClaim(" propstore tests
rg -n -F -- "coerce_active_claim" propstore tests
rg -n -F -- "coerce_active_claims" propstore tests
rg -n -F -- "_coerce_claim_concept_link" propstore tests
rg -n -F -- "_require_claim_concept_link_role" propstore tests
rg -n -F -- 'metadata={"coerce"' propstore/families/claims propstore/core tests
rg -n -F -- '"coerce":' propstore/families/claims propstore/core tests
rg -n -F -- "_coerce_claim_model_value" propstore tests
rg -n -F -- "claim_model_from_payload" propstore tests
rg -n -F -- "compile_raw_id_quarantine_sidecar_rows" propstore tests
rg -n -F -- "compile_promotion_blocked_sidecar_rows" propstore tests
rg -n -F -- "populate_promotion_blocked_claims" propstore tests
rg -n -F -- "ActiveClaim" propstore tests
rg -n -F -- "is_claim_node_active" propstore/core/activation.py propstore tests
rg -n -F -- "claim.claim_id" propstore/world/queries.py
rg -n -F -- "def resolve_claim" propstore tests
rg -n -F -- ".resolve_claim(" propstore tests
rg -n -F -- "resolve_claim_id" propstore tests
rg -n -F -- "_claim_from_test_fixture" propstore tests
rg -n -F -- "propstore.families.claims.storage" propstore tests
rg -n -F -- "normalize_conditions_differ" propstore tests
rg -n -F -- "stance_rows" propstore/families/claims/declaration.py
rg -n -F -- "populate_stances" propstore tests
rg -n -F -- "compile_conflict_sidecar_rows" propstore tests
rg -n -F -- "populate_conflicts" propstore tests
rg -n -F -- "attribute_value(\"source_assertion_ids\")" propstore tests
rg -n -F -- "attributes={\"source_assertion_ids\"" propstore tests
rg -n -F -- "_coerce_source_assertion_ids" propstore tests
rg -n -F -- "has_claim_core_table" propstore tests
rg -n -F -- "delete_claim_core_row" propstore tests
rg -n -F -- "select_source_promotion_claim_rows" propstore tests
rg -n -F -- "select_claim_text" propstore tests
rg -n -F -- "select_claim_texts" propstore tests
rg -n -F -- "select_all_claim_ids" propstore tests
rg -n -F -- "_Phase6HypotheticalStore" propstore tests
rg -n -F -- ".claim_id" tests/test_world_query.py
rg -n -F -- "confidence=1.0" tests/test_world_query.py
```

Ambiguous literal prerequisite command:

```text
rg -n -F -- "sqlite3.Connection" propstore/families/claims propstore/core/active_claims.py tests
rg: propstore/core/active_claims.py: The system cannot find the file specified. (os error 2)
```

Expected meaning: `propstore/core/active_claims.py` appears deleted, which is
consistent with the active-claim deletion target, but the literal `rg` command
did not complete cleanly because the named path is absent.

Failing or nonzero claim gates:

```text
rg -n -F -- "SimpleNamespace" propstore/families/claims propstore/core tests
tests\test_artifact_boundary_failures.py:1
tests\test_artifact_boundary_failures.py:20
tests\architecture\test_argumentation_pin_iccma_adapter.py:3
tests\architecture\test_argumentation_pin_iccma_adapter.py:46
tests\test_artifact_store.py:4
tests\test_artifact_store.py:203
tests\test_artifact_store.py:204
tests\remediation\phase_2_gates\test_T2_3c_embedding_restore_diagnostics.py:4
tests\remediation\phase_2_gates\test_T2_3c_embedding_restore_diagnostics.py:42
tests\test_cli.py:12
tests\test_cli.py:214
tests\test_cli.py:219
tests\test_cli.py:1668
tests\test_cli.py:1672
tests\test_cli.py:1681
tests\test_cli.py:1687
tests\test_cli.py:1695
tests\test_cli.py:1703
tests\test_cli.py:1709
tests\test_cli.py:1772
tests\test_cli.py:1805
tests\test_cli.py:1806
tests\test_cli.py:1807
tests\test_cli.py:2322
tests\test_conflict_detector.py:13
tests\test_conflict_detector.py:901
tests\test_grounder_budget_exceeded.py:3
tests\test_grounder_budget_exceeded.py:18
tests\test_grounder_default_returns_arguments.py:3
tests\test_grounder_default_returns_arguments.py:17
tests\test_grounder_default_returns_arguments.py:18
tests\test_proposal_promotion.py:4
tests\test_proposal_promotion.py:196
tests\test_repository_artifact_boundary_gates.py:158
tests\test_repository_artifact_boundary_gates.py:178
tests\test_resolution_helpers.py:4
tests\test_resolution_helpers.py:268
tests\test_resolution_helpers.py:300
tests\test_resolution_helpers.py:353
tests\test_resolution_helpers.py:400
tests\test_worldline.py:14
tests\test_worldline.py:1761
tests\test_worldline_revision_merge_parent_evidence.py:3
tests\test_worldline_revision_merge_parent_evidence.py:11
tests\test_worldline_revision_merge_parent_evidence.py:12
tests\test_ws_f_aspic_bridge.py:8
tests\test_ws_f_aspic_bridge.py:544
tests\test_ws_f_aspic_bridge.py:546

rg -n -F -- "count_claims(" propstore tests
propstore\app\repository_overview.py:150

rg -n -F -- 'claim["' tests/test_world_query.py
tests/test_world_query.py:134
tests/test_world_query.py:137
tests/test_world_query.py:140
tests/test_world_query.py:143
tests/test_world_query.py:171
```

Expected meaning:

- `SimpleNamespace` is too broad to interpret as claim-owned only because all
  current hits are under `tests`, many unrelated to claims. If the gate is
  literal zero-hit, it fails.
- `count_claims(` has the same non-claim app helper residual described in the
  workstream note; it is not the deleted claim-family SQLite helper.
- `claim["` in `tests/test_world_query.py` was described as a zero-hit
  cleanup search in the Phase 6 overlay typed-store cleanup note; it currently
  fails.

Could not interpret as a pass/fail gate:

```text
rg -n -F -- "CONFLICT_WITNESS_TABLE" propstore/families/claims/declaration.py propstore/families/relations/declaration.py
```

This returned zero hits. The workstream note expected relation-owner hits, so
zero hits means there is no claim-family residual but the exact expected
current meaning is stale or superseded.

Extra check run but not used as a gate result:

```text
rg -n -F -- "confidence" propstore/families/claims propstore/core tests/test_world_query.py tests/test_render_time_filtering.py
```

This was a broad sanity check for a prose concern, not a literal gate. It
returned hits in claim documents/graph code, tests, and core analyzer code, so
it needs a narrower owner-specific gate before it can be judged.
