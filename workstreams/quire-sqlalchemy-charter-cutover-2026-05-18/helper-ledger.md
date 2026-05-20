# Helper Classification Ledger

Date: 2026-05-18

This ledger is executable inventory for helper deletion and semantic-owner
movement during the Quire SQLAlchemy charter cutover.

## Action Vocabulary

- `delete`: remove the helper because Quire charter/SQLAlchemy machinery owns
  the behavior.
- `replace`: remove the helper after callers use SQLAlchemy relationships,
  session queries, model construction, or typed owner APIs.
- `move`: preserve the semantic behavior in the named owner, then delete the
  old helper-shaped path.
- `keep-boundary`: keep the behavior as explicit document/result IO or payload
  conversion with a boundary-specific name.

## Global Deletion Predicate

- Delete a helper when its body is table-shaped `SELECT`, `COUNT`, `INSERT`,
  `DELETE`, row attachment, row coercion, or projection-model wrapping with no
  Propstore semantic policy.
- Move semantic behavior that owns concept-id precedence, alias resolution,
  source-local lowering, quarantine/blocked policy, form/unit validation,
  visibility/render policy, context/lifting semantics, argumentation
  semantics, revision semantics, or authored-document identity.
- After moving kept semantics, delete the original helper-shaped production
  path.

## Closure Checklist

- [ ] Every helper row below has a closure entry in the owning child workstream
  report or commit message.
- [ ] Every `delete` row is absent from production code by its search gate.
- [ ] Every `replace` row has typed model/session/owner API callers.
- [ ] Every `move` row has the named semantic owner and no old helper-shaped
  production path.
- [ ] Every `keep-boundary` row has no DB row/projection coupling.

## Source Helpers

File: `propstore/families/sources/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `SourceProjectionRow` | delete | Replace with `Source` model. |
| `_opinion_json` | delete | Generic typed JSON storage belongs to Quire JSON adapter. |
| `compile_source_sidecar_rows` | replace | Replace with `Source` model construction. |
| `populate_sources` | delete | Replace with SQLAlchemy session add/flush. |

File: `propstore/core/claim_values.py`.

| Helper/surface | Classification | Required final owner/action |
| --- | --- | --- |
| `_opinion_from_mapping` | replace | Replace with boundary-specific source/trust payload conversion or direct typed construction. |
| `SourceOrigin.from_mapping` | replace | Rename to boundary-specific source payload constructor or construct directly from typed source values. |
| `SourceTrust.from_mapping` | replace | Rename to boundary-specific source payload constructor or construct directly from typed source values. |
| `ClaimSource.from_mapping` | replace | Rename to boundary-specific source payload constructor or construct directly from typed source values. |

## Diagnostics Helpers

File: `propstore/families/diagnostics/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `QuarantineDiagnostic` | keep-boundary | Keep as semantic diagnostic input value object with no row coupling. |
| `Written` | replace | Replace with typed write/quarantine report not tied to projection insertion. |
| `Quarantined` | replace | Replace with typed write/quarantine report not tied to projection insertion. |
| `SourceStatusDiagnosticRow` | replace | Replace with typed source-status diagnostic view over `BuildDiagnostic`. |
| `QuarantinableWriter` | replace | Replace raw insert writer with diagnostic service using SQLAlchemy session. |
| `record_build_exception` | replace | Replace raw insert with diagnostic service/session add. |
| `record_embedding_restore_diagnostic` | replace | Replace raw insert with diagnostic service/session add. |
| `record_pass_diagnostics` | move | Keep diagnostic mapping semantics; write through diagnostic service/session. |
| `record_authoring_diagnostics` | move | Keep authoring diagnostic semantics; write through diagnostic service/session. |
| `record_quarantine_diagnostics` | move | Keep quarantine diagnostic semantics; write through diagnostic service/session. |
| `compile_promotion_blocked_diagnostic_rows` | replace | Replace projection rows with `BuildDiagnostic` model construction. |
| `has_build_diagnostics_table` | delete | Schema presence validation belongs to Quire catalog validation. |
| `select_build_diagnostics` | replace | Replace with SQLAlchemy query over `BuildDiagnostic`. |
| `select_source_status_diagnostic_rows` | replace | Replace with typed source-status diagnostic query. |
| `delete_promotion_blocked_diagnostics` | replace | Replace with SQLAlchemy delete/query scoped to `BuildDiagnostic`. |

## Concept And Form Helpers

File: `propstore/families/concepts/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `ConceptRelationshipProjectionRow` | delete | Replace with typed `ConceptRelationship` or relation model. |
| `ConceptSidecarRows` | delete | Replace with typed write plan/session adds. |
| `_concept_symbol_candidates` | move | Move symbol selection semantics to concept/form-algebra owner. |
| `compile_concept_sidecar_rows` | replace | Replace with typed concept/form/alias/relationship/parameterization model construction. |
| `_compile_form_algebra_rows` | move | Move form algebra semantics to form/concept semantic owner. |
| `ConceptRow` | delete | Replace with `Concept` model. |
| `ConceptEmbeddingSource` | replace | Replace with typed embedding source projection over `Concept` model. |
| `ParameterizationRow` | delete | Replace with `Parameterization` model. |
| `populate_concept_sidecar_rows` | delete | Replace with SQLAlchemy session add/flush through Quire build session. |
| `ConceptSearchQuerySyntaxError` | move | Move to concept search owner as the domain error raised by Quire/SQLAlchemy FTS query adapters. |
| `_is_concept_search_syntax_error` | move | Move SQLite/FTS syntax classification to Quire FTS adapter; concept search owner maps it to `ConceptSearchQuerySyntaxError`. |
| `fetch_concept_search_hits` | replace | Replace raw FTS SQL with Quire/SQLAlchemy FTS query API. |
| `fetch_concept_search_hits_from_sidecar` | delete | Direct sidecar path opening is deleted; callers use Quire sessions. |
| `select_concept_by_id` | replace | Replace with SQLAlchemy session query. |
| `select_all_concepts` | replace | Replace with SQLAlchemy session query. |
| `select_concept_embedding_sources` | replace | Replace with typed embedding source query over `Concept` model. |
| `resolve_concept_embedding_entity` | move | Move concept-handle resolution policy to concept owner. |
| `select_aliases_by_concept_id` | replace | Replace with `Concept.aliases` relationship query. |
| `select_concept_registry_rows` | replace | Replace with typed registry projection from `Concept` models. |
| `build_concept_logical_id_index` | move | Move logical-id precedence/index semantics to concept owner. |
| `resolve_concept_alias` | move | Move alias resolution policy to concept owner. |
| `resolve_concept_id` | move | Move id/alias/logical/canonical precedence policy to concept owner. |
| `select_concept_ids_for_group` | replace | Replace with `ParameterizationGroup.members` relationship. |
| `select_parameterizations_for_output_concept` | replace | Replace with `Concept.parameterizations_as_output` relationship. |
| `select_all_parameterizations` | replace | Replace with SQLAlchemy session query. |
| `select_parameterization_group_members` | replace | Replace with `ParameterizationGroup.members` relationship. |
| `select_all_form_rows` | replace | Replace with typed `Form` model query. |
| `select_form_algebra_rows_for_output` | replace | Replace with typed `FormAlgebra` model query. |
| `select_all_form_algebra_rows` | replace | Replace with typed `FormAlgebra` model query. |
| `search_concept_ids` | replace | Replace raw FTS SQL with Quire/SQLAlchemy FTS query API. |
| `count_concepts` | replace | Replace with SQLAlchemy count query through concept owner. |
| `resolve_sidecar_concept_id` | move | Move handle-resolution policy to concept owner. |

## Context Helpers

File: `propstore/families/contexts/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `_nullable_text` | delete | Generic nullable text conversion belongs to Quire charter conversion. |
| `_json_or_none` | delete | Generic JSON conversion belongs to Quire JSON adapter. |
| `_json_mapping` | delete | Generic JSON conversion belongs to Quire JSON adapter. |
| `_json_string_tuple` | delete | Generic JSON conversion belongs to Quire JSON adapter. |
| `TEXT_CODEC` | delete | Generic text conversion belongs to Quire charter conversion. |
| `PARAMETERS_CODEC` | delete | Generic JSON conversion belongs to Quire JSON adapter. |
| `CONDITIONS_CODEC` | delete | Generic JSON conversion belongs to Quire JSON adapter. |
| `PROVENANCE_CODEC` | delete | Generic JSON conversion belongs to Quire JSON adapter. |
| `AUTOINCREMENT_CODEC` | delete | Generic integer/autoincrement conversion belongs to Quire charter conversion. |
| `CONTEXT_SCHEMA` | delete | Quire charter/schema catalog replaces the local projection schema bundle. |
| `create_context_tables` | delete | Quire charter creates tables. |
| `populate_contexts` | delete | Replace with SQLAlchemy session add/flush. |
| `filter_invalid_context_lifting_rows` | move | Move invalid lifting-rule filtering semantics to context/lifting semantic owner. |
| `compile_context_sidecar_rows` | replace | Replace with typed `Context`, `ContextAssumption`, and `ContextLiftingRule` model construction. |
| `compile_context_lifting_materialization_rows` | replace | Replace with typed `ContextLiftingMaterialization` model construction. |
| `load_lifting_system` | move | Keep lifting-system assembly as context owner API; implement over typed model queries. |
| `_projection_row` | delete | Projection row wrapper is deleted. |
| `_lifting_materialization_row` | delete | Projection row wrapper is deleted. |

## Claim Helpers

File: `propstore/families/claims/storage.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `TypedClaimFields` | replace | Replace with `ClaimNumericPayload`, `ClaimTextPayload`, and `ClaimAlgorithmPayload`; delete the storage DTO. |
| `_optional_string` | delete | Generic nullable string conversion belongs to Quire charter conversion. |
| `_optional_float_input` | delete | Generic nullable numeric conversion belongs to Quire charter conversion. |
| `_optional_int` | delete | Generic nullable integer conversion belongs to Quire charter conversion. |
| `claim_version_id` | delete | Claim version identity comes from claim identity/domain model. |
| `_iter_claim_concept_link_values` | replace | Construct `ClaimConceptLink` association objects from claim contracts. |
| `_claim_concept_link_values_for_declaration` | replace | Construct `ClaimConceptLink` association objects from claim contracts. |
| `normalize_conditions_differ` | delete | Condition-difference serialization belongs to the relation/stance model JSON adapter. |
| `coerce_stance_resolution` | move | Move stance resolution validation to relation/stance semantic owner. |
| `resolution_opinion_columns` | move | Move opinion extraction to a typed stance-resolution value object. |
| `canonicalize_claim_for_storage` | move | Split raw-id/logical/artifact identity into claim identity/source promotion owners; split concept-reference lowering into claim semantic normalization. |
| `extract_numeric_claim_fields` | replace | Replace with typed claim payload construction from claim contracts. |
| `extract_typed_claim_fields` | replace | Replace with typed claim payload construction from claim contracts. |
| `resolve_equation_sympy` | move | Move equation Sympy generation to claim semantic compilation. |
| `resolve_algorithm_storage` | move | Move algorithm body/canonical AST/stage handling to claim semantic compilation. |
| `extract_deferred_stance_rows_with_diagnostics` | move | Move embedded-stance validation/quarantine semantics to relation/stance owner; replace tuple rows with `Stance` models. |
| `prepare_claim_insert_row` | delete | Replace with `Claim` model construction and SQLAlchemy session add. |
| `prepare_claim_concept_link_rows` | delete | Replace with `ClaimConceptLink` association objects and SQLAlchemy relationship persistence. |

File: `propstore/families/claims/stages.py`.

| Helper/surface | Classification | Required final owner/action |
| --- | --- | --- |
| `ClaimCheckedBundle` | keep-boundary | Keep as the checked semantic compiler-stage bundle; remove projection-row and sidecar-row coupling from its reachable fields. |
| `ClaimSidecarRows` | delete | Replace with typed write plans and SQLAlchemy session adds. |
| `RawIdQuarantineSidecarRows` | delete | Replace with typed quarantine claim/diagnostic models written through claim and diagnostic owners. |
| `PromotionBlockedSidecarRows` | delete | Replace with typed promotion-blocked claim/diagnostic models written through claim and diagnostic owners. |

File: `propstore/core/active_claims.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `ActiveClaimVariable` | move | Rename/move to `ClaimAlgorithmVariable` in the claim algorithm payload owner; delete the `Active*` spelling. |
| `_parse_conditions` | delete | Replaced by typed checked-condition fields on `Claim`. |
| `_parse_variables` | move | Move to algorithm payload document/model boundary. |
| `_parse_checked_conditions` | delete | Quire JSON adapter plus claim model owns checked-condition loading. |
| `_require_claim_concept_link_role` | delete | SQLAlchemy `ClaimConceptLink.role` uses typed enum validation. |
| `_coerce_claim_concept_link` | delete | `ClaimConceptLink` is the object. |
| `ActiveClaim` | delete | Replace with typed `Claim` plus activation query results; delete the parallel active claim object family. |
| `ActiveClaimInput` | delete | Runtime receives typed `Claim`; dict/mapping input unions are deleted. |
| `ActiveClaim.from_claim` | delete | Projection/dict coercion constructor is deleted. |
| `ActiveClaim.from_mapping` | delete | Projection-row construction path is deleted. |
| `ActiveClaim.to_dict` | replace | Replace with explicit view/document payload rendering that does not import `CLAIM_ROW_MODEL`. |
| `ActiveClaim.to_source_claim_payload` | move | Move conflict-detector payload rendering to a conflict-detector input adapter. |
| `coerce_active_claim` | delete | Runtime receives typed `Claim`; mapping coercion is deleted. |
| `coerce_active_claims` | delete | Runtime receives typed `Claim`; mapping coercion is deleted. |

## Relation Helpers

File: `propstore/families/relations/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `RelationshipRow` | delete | Replace with typed `ConceptRelation` model. |
| `StanceRow` | delete | Replace with typed `Stance` model. |
| `ConflictRow` | delete | Replace with typed `ConflictWitness` model. |
| `_optional_numeric` | delete | Generic nullable numeric conversion belongs to Quire charter conversion. |
| `compile_authored_stance_sidecar_rows` | replace | Replace with `Stance` model construction. |
| `compile_authored_stance_sidecar_rows_with_diagnostics` | move | Move stance reference validation/quarantine diagnostics to relation semantic owner. |
| `select_stances_between` | replace | Replace with SQLAlchemy relationship/session query. |
| `select_conflicts` | replace | Replace with SQLAlchemy session query over `ConflictWitness`. |
| `select_all_relationships` | replace | Replace with SQLAlchemy session query over `ConceptRelation`. |
| `select_all_claim_stances` | replace | Replace with SQLAlchemy session query over `Stance`. |
| `select_claim_stances_with_policy` | move | Move visibility/render policy semantics to relation/world owner. |
| `select_explanation_stances` | move | Move explanation traversal semantics to relation/world owner. |
| `count_conflicts` | replace | Replace with SQLAlchemy count query over `ConflictWitness`. |

## Micropublication Helpers

Files: `propstore/core/micropublications.py` and
`propstore/families/micropublications/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `_parse_string_tuple` | delete | Generic row string parsing is deleted. |
| `ActiveMicropublication` | delete | Replace with typed `Micropublication` plus `MicropublicationClaimLink`; active is a query state, not a second object family. |
| `ActiveMicropublicationInput` | delete | Runtime receives typed `Micropublication`; dict/mapping input unions are deleted. |
| `ActiveMicropublication.from_mapping` | delete | Projection-row construction path is deleted. |
| `coerce_active_micropublication` | delete | Runtime receives typed `Micropublication`; mapping coercion is deleted. |
| `MicropublicationProjectionRow` | delete | Replace with `Micropublication` model. |
| `MicropublicationClaimProjectionRow` | delete | Replace with `MicropublicationClaimLink` association object. |
| `MicropublicationSidecarRows` | delete | Replace with typed write plan/session adds. |
| `compile_micropublication_sidecar_rows` | replace | Replace with typed `Micropublication`/link model construction. |
| `compile_micropublication_sidecar_rows_with_diagnostics` | move | Keep missing-claim quarantine semantics in micropublication owner. |
| `create_micropublication_tables` | delete | Quire charter creates tables. |
| `populate_micropublications` | delete | Replace with SQLAlchemy session add/flush. |
| `select_all_micropublications` | replace | Replace with SQLAlchemy session query. |

## World And Activation Helpers

Files: `propstore/core/graph_types.py`, `propstore/world/model.py`,
`propstore/world/value_resolver.py`, `propstore/world/atms.py`,
`propstore/world/overlay.py`, and `propstore/core/environment.py`.

| Helper/surface | Classification | Required final owner/action |
| --- | --- | --- |
| `_claim_rows` | delete | Replace raw `select_claim_rows` wrapper with typed Quire session/model query. |
| `ActiveClaimInput` protocol usage | delete | World/environment APIs receive typed `Claim` objects, not dict/mapping unions. |
| `ActiveMicropublicationInput` protocol usage | delete | World/environment APIs receive typed `Micropublication` objects, not dict/mapping unions. |
| `ActiveClaimResolver` | replace | Rename to `ClaimValueResolver` and make it consume typed `Claim` query results. |
| `ActiveWorldGraph` | replace | Rename to `WorldActivationGraph`; keep activation graph semantics, delete misleading active-object-family spelling. |
| `WorldBindActiveReport` | replace | Rename to `WorldBindActivationReport` or another non-`Active*` activation-state report name. |
| `ProvenanceRecord.from_mapping` | replace | Rename to a boundary-specific graph/provenance payload constructor. |

File: `propstore/worldline/result_types.py`.

| Helper/surface | Classification | Required final owner/action |
| --- | --- | --- |
| worldline result `from_mapping` constructors | replace | Rename persisted-result constructors to boundary-specific document/JSON payload constructors. |

Files: `propstore/support_revision/state.py`,
`propstore/support_revision/history.py`,
`propstore/support_revision/snapshot_types.py`, and
`propstore/support_revision/explanation_types.py`.

| Helper/surface | Classification | Required final owner/action |
| --- | --- | --- |
| support-revision `from_mapping` constructors and helper functions | replace | Rename persisted revision payload constructors to boundary-specific document/JSON payload constructors. |

## Grounding And Rule Helpers

File: `propstore/families/rules/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `GroundedFactProjectionRow` | delete | Replace with `GroundedFact` model. |
| `GroundedFactEmptyPredicateProjectionRow` | delete | Replace with typed `GroundedEmptyPredicate` model. |
| `GroundedBundleInputProjectionRow` | delete | Replace with `GroundedBundleInput` model. |
| `create_grounded_fact_table` | delete | Quire charter creates tables. |
| `populate_grounded_facts` | replace | Replace with model construction/session writes while preserving four-valued bundle semantics. |
| `_persist_bundle_inputs` | replace | Replace raw row persistence with `GroundedBundleInput` model writes. |
| `_read_bundle_inputs` | replace | Replace raw row reads with `GroundedBundleInput` model queries. |
| `_encode_bundle_input`, `_decode_bundle_input`, `_bundle_input_payload`, `_is_json_value` | keep-boundary | Keep only inside grounding payload serialization. |
| `_encode_gunray_atom`, `_decode_gunray_atom`, `_encode_gunray_rule`, `_decode_gunray_rule` | keep-boundary | Keep as Gunray payload serialization boundary. |
| `_rule_key` | keep-boundary | Keep as deterministic grounding ordering helper. |
| `read_grounded_facts` | replace | Replace raw SQL read with typed model query and bundle assembly. |
| `read_grounded_bundle` | replace | Replace raw SQL read with typed model query and bundle assembly. |
| `build_runtime_grounded_bundle` | keep-boundary | Keep semantic bundle assembly API; internally use typed model queries. |
| `_read_source_rules`, `_read_source_superiority`, `_read_source_facts` | replace | Replace raw row reads with `GroundedBundleInput` query plus payload decoder. |

## Embedding Helpers

File: `propstore/families/embeddings/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `_require_sqlite_vec` | move | Move extension loading policy to Quire vector backend. |
| `load_vec_extension` | move | Move extension loading policy to Quire vector backend. |
| `EmbeddingSnapshot` | keep-boundary | Keep as Propstore embedding snapshot value object. |
| `EmbeddingSnapshotReport` | keep-boundary | Keep as Propstore embedding snapshot report value object. |
| `ensure_embedding_tables` | delete | Quire vector/charter machinery creates tables. |
| `SidecarEmbeddingRegistry` | replace | Replace with Quire vector registry/session API. |
| `_SidecarEntityEmbeddingStore` | replace | Replace with Quire vector entity store over SQLAlchemy session. |
| `SidecarClaimEmbeddingStore` | replace | Replace with claim-specific adapter over Quire vector entity store. |
| `SidecarConceptEmbeddingStore` | replace | Replace with concept-specific adapter over Quire vector entity store. |
| `SidecarEmbeddingSnapshotStore` | replace | Replace with Quire vector snapshot store plus Propstore snapshot report mapping. |
| `get_registered_models` | replace | Replace with Quire vector registry query. |
| `embed_claims`, `embed_concepts` | replace | Keep workflow API; route through Quire vector/session APIs. |
| `find_similar`, `find_similar_concepts` | replace | Replace raw vector SQL with Quire vector query API. |
| `find_similar_agree`, `find_similar_disagree` | replace | Replace raw vector SQL with Quire vector query API. |
| `find_similar_concepts_agree`, `find_similar_concepts_disagree` | replace | Replace raw vector SQL with Quire vector query API. |
| `extract_embeddings`, `extract_embedding_snapshot_from_store` | replace | Replace raw snapshot extraction/opening with Quire vector snapshot API. |
| `restore_embeddings`, `restore_embedding_snapshot` | replace | Replace raw restore/opening with Quire vector snapshot API. |

Files: `propstore/families/claims/sidecar_runtime.py`,
`propstore/families/concepts/sidecar_runtime.py`, and
`propstore/core/store_results.py`.

| Helper/surface | Classification | Required final owner/action |
| --- | --- | --- |
| `SidecarClaimRelationStore` | delete | Replace raw sidecar relation/vector access with claim owner APIs over Quire sessions/vector APIs. |
| `find_similar_claim_rows` | delete | Replace row-shaped claim similarity API with typed claim similarity query over Quire vector/session APIs. |
| `find_similar_concept_rows` | delete | Replace row-shaped concept similarity API with typed concept similarity query over Quire vector/session APIs. |
| `ConceptSearchHit.from_mapping` | replace | Rename to boundary-specific payload constructor or construct directly from typed query results. |
| `ClaimSimilarityHit.from_mapping` | replace | Rename to boundary-specific payload constructor or construct directly from typed query results. |
| `ConceptSimilarityHit.from_mapping` | replace | Rename to boundary-specific payload constructor or construct directly from typed query results. |

## Calibration Helpers

File: `propstore/families/calibration/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `CalibrationCountsProjectionRow` | delete | Replace with `CalibrationCount` model. |
| `load_calibration_counts` | replace | Replace raw SQL/table-missing behavior with typed optional query over `CalibrationCount`. |

## Projection Model Helper Families

Files: `propstore/families/claims/projection_model.py`,
`propstore/families/concepts/projection_model.py`, and
`propstore/families/relations/projection_model.py`.

| Helper family | Classification | Required final owner/action |
| --- | --- | --- |
| nullable scalar codecs such as `_nullable_text`, `_nullable_int`, `_nullable_float`, `_optional_float`, `_optional_int` | delete | Quire charter conversion owns generic scalar/null handling. |
| id coercion codecs such as `_claim_id`, `_concept_id`, `_context_id`, `_justification_id` | delete | SQLAlchemy mapped model fields use typed id constructors at model/document boundaries. |
| enum value codecs such as `_role_value`, `_claim_type_value`, `_algorithm_stage_value`, `_concept_status_value`, `_exactness_value`, `_stance_type_value`, `_conflict_class_value` | delete | Enum storage adapters are generic Quire SQLAlchemy adapters. |
| JSON/render helpers such as `_logical_ids_payload`, `_logical_ids_from_value`, `_logical_ids_to_columns`, `_logical_ids_from_columns`, `_provenance_to_columns`, `_provenance_from_columns`, `_source_to_columns`, `_source_from_columns`, `_normalize_conditions_differ` | replace | Replace with typed value objects and Quire JSON adapter; semantic payload rendering moves to document/view boundaries. |
| query-plan builders such as `claim_row_query_plan`, `_edge_column`, `claim_stance_policy_query_plan` | delete | SQLAlchemy relationships/session query construction replaces projection query-plan helpers. |
