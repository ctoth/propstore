# Helper-Shaped Debt Inventory - 2026-05-21

Input scan:

```powershell
rg -n -- "\b(def|class)\s+\w*(helper|adapter|shim|coerce|normalize|from_row|from_mapping|resolve_\w+_id|to_\w+_id)\w*\b|\b\w*(Helper|Adapter|Shim|Row|Record|DTO)\b" propstore
```

Classification values: `delete`, `io-boundary`, `presentation`,
`semantic-owner`, `quire-needed`.

## SQLAlchemy Gate Audit Backfill

Recorded 2026-05-21 from the wave gate audits under
`workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/gate-audits/`.

The earlier classification below is superseded where this section names a
stricter action. A surface is not complete merely because the old projection
symbol gate is zero-hit. Direct string table/model lookup, duplicate payload
constructors, and broad compatibility/classification hits remain work until
they are deleted or moved to the exact owner boundary named here.

| Surface | Classification | Required final state |
| --- | --- | --- |
| `propstore/families/world_charters.py:_MODELS`, `_CLAIM_MODEL_TABLES`, `world_model`, `world_record`, `_claim_models` | `delete` | No Propstore-owned table/model registry and no claim-special model routing. Callers use Quire family/charter metadata and session APIs for main model lookup and table access. |
| Direct `derived.schema.table("claim_core")`, `derived.schema.table("build_diagnostics")`, `derived.schema.model("build_diagnostics")`, and `schema.model("claim_core")` hits | `delete` | Source status, diagnostics, claims, embeddings, and world callers use generic family metadata/session APIs rather than string table/model lookup. |
| Direct `schema.model("alias")` and `schema.model("concept")` hits | `delete` | Concept and alias lookup use generic Quire family-reference/model metadata APIs. Do not replace with concept-specific resolver wrappers. |
| Direct `schema.model("context")`, `schema.model("context_assumption")`, `schema.model("context_lifting_rule")`, and `schema.model("context_lifting_materialization")` hits | `delete` | Context/lifting callers use generic Quire family metadata/session APIs. Do not keep context-specific table/model selectors. |
| `propstore/core/justifications.py:CanonicalJustification` and `CanonicalJustification(` production/test construction hits | `delete` | Delete the duplicate canonical justification payload class/constructor path. Keep justification model behavior in the justification family owner and active-graph projection in the world/argumentation owner. |
| `propstore/core/assertions/conversion.py:_from_payload`, `propstore/families/claims/stages.py:_from_payload`, and `propstore/world/bound.py:_from_payload` | `delete` unless promoted to a named IO boundary in the owning module | Active runtime/family/core surfaces must not carry broad `_from_payload` constructors. If a payload decoder is real IO, rename/place it as an explicit owner-boundary parser and make malformed shapes hard-fail. |
| `quire/charters.py:**values` | `quire-needed` | Quire charter construction must not use a broad kwargs sink that duplicates field shape. Replace with typed charter construction or prove this is not a field-shape/compatibility sink in Quire, then record the proof. |
| `legacy`, `backward compat`, `backwards compat`, `compat shim`, `fallback`, and broad `coerce_*` hits | `delete` or exact owner-boundary classification required per hit | Each production hit must be classified as real IO boundary, semantic lowering, or illegal compatibility. Illegal compat/fallback/coercer paths are deleted; no generic allowance remains. |
| `tests/test_world_query.py:claim["..."]` hits | `delete` | World-query tests use typed claim/domain objects or typed fixtures, not dict-shaped claim access. |
| `propstore/app/repository_overview.py:count_claims(` | `presentation` pending owner check | This is not the deleted claim-family SQLite helper, but the app helper must remain presentation-only and must not open or preserve old storage/query mechanics. |

## Delete

| Surface | Classification | Required final state |
| --- | --- | --- |
| `propstore/world/overlay.py:_ParameterizationCatalogAdapter` and its call at `_compiled_graph_for_bound` | `delete` | `build_compiled_world_graph` accepts stores with `parameterizations_for` by deriving the catalog from `all_concepts`; the adapter class is gone. |
| `propstore/core/justifications.py:_normalize_attrs` | `delete` | `CanonicalJustification` accepts typed attribute tuples internally; dictionary decoding happens only in `from_dict`. |
| `propstore/conflict_detector/models.py:coerce_conflict_class` | `delete` | Conflict producers and ATMS nogood provenance carry `ConflictClass` directly; no generic conflict-class coercer remains. |
| `propstore/support_revision/state.py:coerce_assumption_ref` | `delete` | `AssumptionAtom` requires an `AssumptionRef`; `normalize_revision_input` owns mapping-to-domain parsing. |

## IO Boundary

| Surface | Classification | Owner |
| --- | --- | --- |
| `propstore/app/rules.py:_coerce_term` | `io-boundary` | App request parsing for rule proposal terms. |
| `propstore/heuristic/rule_extraction.py:_coerce_term` | `io-boundary` | Heuristic extraction parser for rule terms. |
| `propstore/app/worldlines.py:_coerce_json_value`, `_coerce_json_object` | `io-boundary` | App JSON request parsing. |
| `propstore/cli/helpers.py:_coerce_cli_scalar` | `io-boundary` | CLI scalar parsing. |
| `propstore/cli/worldline/materialize.py:_coerce_override_values` | `io-boundary` | CLI override parsing. |
| `propstore/cli/world/analysis.py:_coerce_hypothetical_value` | `io-boundary` | CLI hypothetical value parsing. |
| `propstore/source/common.py:normalize_source_slug` | `io-boundary` | Source-name filesystem slug parsing. |
| `propstore/source/claims.py:normalize_source_claims_payload` | `io-boundary` | Source branch claim document parsing. |
| `propstore/source/concepts.py:normalize_source_concepts_document` | `io-boundary` | Source branch concept document parsing. |
| `propstore/source/relations.py:normalize_source_justifications_payload`, `normalize_source_stances_payload` | `io-boundary` | Source branch relation document parsing. |
| `propstore/source/claim_concepts.py:normalize_imported_claim_artifact`, `normalize_promoted_source_claim_artifact` | `io-boundary` | Source-local claim artifact parsing and promotion input shaping. |
| `propstore/importing/passes.py:_normalize_concept_payload`, `_normalize_concept_batch`, `_normalize_claim_batch`, `_normalize_stance_batch`, `_normalize_passthrough_batch`, `_normalize_semantic_import_writes` | `io-boundary` | Import bundle parsing before semantic writes. |
| `propstore/families/contexts/stages.py:parse_context_record`, `parse_context_record_document` | `io-boundary` | Context charter document decoding. |
| `propstore/families/concepts/stages.py:normalize_concept_payload`, `normalize_concept_document_for_write`, `parse_concept_record`, `parse_concept_record_document`, `normalize_loaded_concepts` | `io-boundary` | Concept charter document decoding and write encoding. |
| `propstore/families/concepts/passes.py:normalize_concept_record` | `io-boundary` | Concept import pass document decoding. |
| `propstore/families/identity/concepts.py:normalize_canonical_concept_payload`, `_normalize_numeric_range` | `io-boundary` | Canonical concept identity document parsing. |
| `propstore/families/identity/claims.py:normalize_claim_file_payload`, `normalize_canonical_claim_payload`, `_normalize_claim_file_entry`, `_normalize_claim_logical_ids`, `_normalize_existing_logical_ids` | `io-boundary` | Canonical claim identity document parsing. |
| `propstore/families/identity/logical_ids.py:normalize_identity_namespace`, `normalize_logical_value` | `io-boundary` | Logical-id text token parsing. |
| `propstore/merge/structured_merge.py:_normalize_for_signature`, `_stance_row_from_mapping` | `io-boundary` | Structured merge input parsing and signature construction. |
| `propstore/probabilistic_relations.py:provenance_from_row`, `relation_from_row` | `io-boundary` | SQLite row decoding. |
| `propstore/support_revision/input_normalization.py:normalize_revision_input` | `io-boundary` | Support-revision request parsing. |
| `propstore/support_revision/explanation_types.py:coerce_revision_atom_detail`, `coerce_entrenchment_reason`, `_coerce_override_priority` | `io-boundary` | Explanation payload decoding. |
| `propstore/worldline/result_types.py:coerce_worldline_capture_error`, `_coerce_variable_refs`, `coerce_worldline_target_value`, `coerce_worldline_step` | `io-boundary` | Worldline journal/result payload decoding. |

## Presentation

| Surface | Classification | Owner |
| --- | --- | --- |
| `propstore/app/neighborhoods.py:SemanticNeighborhoodRow` and all `SemanticNeighborhoodRow` hits | `presentation` | App neighborhood report table. |
| `propstore/app/repository_overview.py:InventoryRow` and all `InventoryRow` hits | `presentation` | App repository overview table. |
| `propstore/app/repository_history.py:LogRecord` and all `LogRecord` hits | `presentation` | App history report. |
| `propstore/source/status.py:SourceStatusRow` and all `SourceStatusRow` hits | `presentation` | Source status report. |
| `propstore/web/html.py:LinkRow` and all `LinkRow` hits | `presentation` | HTML rendering table row. |

## Semantic Owner

| Surface | Classification | Owner |
| --- | --- | --- |
| `propstore/dimensions.py:normalize_to_si` | `semantic-owner` | Dimension arithmetic. |
| `propstore/epistemic_process.py:ProcessCompletionRecord` and all `ProcessCompletionRecord` hits | `semantic-owner` | Epistemic process state. |
| `propstore/conflict_detector/models.py:ConflictRecord` and all `ConflictRecord` hits | `semantic-owner` | Conflict detector domain result. |
| `propstore/conflict_detector/parameterization_conflicts.py:_normalize_claim_value` | `semantic-owner` | Parameterization conflict comparison. |
| `propstore/grounding/predicates.py:_normalize_argument_type` | `semantic-owner` | Predicate declaration semantics. |
| `propstore/aspic_bridge/lifting_projection.py:LiftingProjectionRecord` and all `LiftingProjectionRecord` hits | `semantic-owner` | ASPIC lifting projection result. |
| `propstore/core/assertions/codec.py:AssertionCanonicalRecord` and all `AssertionCanonicalRecord` hits | `semantic-owner` | Assertion canonical codec. |
| `propstore/core/assertions/conversion.py:AssertionSourceRecord` and all `AssertionSourceRecord` hits | `semantic-owner` | Assertion source codec. |
| `propstore/core/base_rates.py:BaseRateAssertionRecord` | `semantic-owner` | Base-rate assertion model. |
| `propstore/core/results.py:_normalize_strings`, `_normalize_metadata` | `semantic-owner` | Result value canonicalization. |
| `propstore/core/analyzers.py:_normalize_query_claim_ids`, `_claim_node_from_row`, `_relation_edge_from_row`, `_conflict_witness_from_row` | `semantic-owner` | Graph analyzer projection from family model rows. |
| `propstore/core/graph_types.py:_normalize_pairs`, `ProvenanceRecord` and all `ProvenanceRecord` hits | `semantic-owner` | Graph provenance and attribute ordering. |
| `propstore/core/graph_build.py:_display_claim_id_from_row` | `semantic-owner` | Compiled graph claim display identity selection. |
| `propstore/core/labels.py:normalize_environments`, `JustificationRecord` | `semantic-owner` | Label and justification semantics. |
| `propstore/core/conditions/checked.py:_normalize_checked_conditions` | `semantic-owner` | Checked condition canonical form. |
| `propstore/families/claims/references.py:ClaimReferenceRecord`, `claim_reference_keys`, `claim_references_from_claims`, `build_claim_reference_index`, `resolve_first_claim_reference_id` and all `ClaimReferenceRecord` hits | `semantic-owner` | Claim family reference indexing. |
| `propstore/families/claims/stages.py:RawIdQuarantineRecord` and all `RawIdQuarantineRecord` hits | `semantic-owner` | Claim family quarantine diagnostics. |
| `propstore/families/concepts/stages.py:ConceptRecord`, its symbol-listing helper, `primary_logical_id`, `format_loaded_concept_logical_ids`, and all `ConceptRecord` hits | `semantic-owner` | Concept family staged model. |
| `propstore/families/contexts/stages.py:ContextRecord` and all `ContextRecord` hits | `semantic-owner` | Context family staged model. |
| `propstore/observatory.py:SemanticTraceRecord` and all `SemanticTraceRecord` hits | `semantic-owner` | Observatory trace state. |
| `propstore/parameterization_groups.py:_unwrap_concept`, its concept-key collection helper, `_concept_artifact_id`, `_parameterization_inputs` | `semantic-owner` | Parameterization grouping over concept domain objects. |
| `propstore/provenance/records.py:*ProvenanceRecord` and all provenance record hits | `semantic-owner` | Provenance domain model. |
| `propstore/provenance/projections.py:normalize_why_supports` | `semantic-owner` | Provenance projection canonical form. |
| `propstore/provenance/prov_o.py:*_nodes` functions over provenance records | `semantic-owner` | PROV-O projection. |
| `propstore/structured_projection.py:ProjectionFrameProvenanceRecord` hits | `semantic-owner` | Structured projection provenance. |
| `propstore/world/assignment_selection_policy.py:_normalized_form_parameters` | `semantic-owner` | Assignment selection policy. |
| `propstore/world/atms.py:_normalize_value`, `_coerce_queryables`, `_coerce_concept_target_status`, `_coerce_environment_key` | `semantic-owner` | ATMS engine internal canonical values. |
| `propstore/world/bound.py:_normalize_claim_id_set`, `_normalize_override_values`, `_normalize_revision_targets` | `semantic-owner` | Bound-world query/revision semantics. |
| `propstore/world/resolution.py:_coerce_resolution_claim` | `semantic-owner` | Resolution over claim domain values. |
| `propstore/world/value_resolver.py:_coerce_override_value`, `_normalize_value` | `semantic-owner` | Value resolver numeric/string semantics. |
| `propstore/world/types.py:coerce_value_status`, `normalize_queryable_cel`, `coerce_queryable_assumptions`, `_normalize_merge_operator_value` | `semantic-owner` | World type canonicalization. |
| `propstore/worldline/revision_capture.py:_normalize_query_atom` | `semantic-owner` | Worldline revision atom capture. |
| `propstore/core/*_types.py` enum coercers not listed in `Delete` | `semantic-owner` | Enum owner modules currently define the boundary value semantics. |
| `propstore/policies.py:_normalize_merge_operator_value` | `semantic-owner` | Merge policy semantics. |
| `propstore/uri.py:normalize_uri_token` | `semantic-owner` | URI token canonicalization. |
| `propstore/value_comparison.py:_normalize_interval` | `semantic-owner` | Value comparison interval semantics. |

## Quire Needed

No current production hit requires a missing Quire capability.
