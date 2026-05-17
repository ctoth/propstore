# Family Declaration Cleanup Inventory - 2026-05-17

Status: current inventory for the next broader typed-metadata cleanup.

Parent workstreams:

- `workstreams/repo-wide-typed-metadata-cleanup-workstream-2026-05-14.md`
- `workstreams/generic-quire-projection-mapping-workstream-2026-05-16.md`
- `workstreams/quire-explicit-projection-boundaries-workstream-2026-05-16.md`
- `workstreams/source-generic-machinery-deletion-workstream-2026-05-17.md`

## Current Verified Shape

The source-specific cleanup is complete and should not be treated as the main
remaining surface. Current scanner output from:

```powershell
uv run scripts/typed_metadata_inventory.py --format markdown --limit 80
```

shows:

| Package | Lines | Projection Columns | Raw SQL Score | Codec Methods | Mapping Hints | Class Surfaces |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `families` | 16472 | 18 | 273 | 57 | 83 | 24 |
| `world` | 11186 | 0 | 4 | 2 | 26 | 52 |
| `app` | 10215 | 0 | 0 | 5 | 52 | 179 |
| `core` | 9109 | 0 | 0 | 45 | 26 | 7 |
| `source` | 3589 | 0 | 0 | 0 | 12 | 3 |

The next problem is family-owned derived-store declaration/query/mapping
boilerplate, not more source-local cleanup.

Old explicit-boundary surfaces are currently absent in the searched production
and test surfaces:

- `decode_columns`
- `CompositePath`
- `DerivedPath`
- `attribute_bucket`
- `decode_key`
- `ignored_columns`
- `claim_select_sql`
- `STANCE_SELECT_COLUMNS`
- `claim_stance_projection_row`

## Phase 0 Refresh - 2026-05-17

Command status:

- `git status --short --branch`: tracked files clean before Phase 0 edits;
  unrelated untracked diagnostics remain.
- `uv run scripts/typed_metadata_inventory.py --format markdown --limit 120`:
  completed.
- `uv run scripts/typed_metadata_inventory.py --format json --emit-row-mapping-metrics`:
  completed and emitted `child_row_assembly_loops`.
- `uv run scripts/typed_metadata_inventory.py --gates --ledger workstreams/typed-metadata-owner-ledger-2026-05-15.csv`:
  all gates passed; ledger had 1343 rows.
- `workstreams/phase-0-family-surface-baseline-2026-05-17.txt`: created
  from the exact Phase 0 `rg` command and committed in `cc63d2ab`.

Current scanner metrics:

| Package | Lines | Projection Columns | Raw SQL Score | Codec Methods | Mapping Hints | Class Surfaces |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `families` | 16727 | 18 | 273 | 51 | 82 | 24 |
| `world` | 11186 | 0 | 4 | 2 | 26 | 52 |
| `app` | 10221 | 0 | 0 | 5 | 52 | 179 |
| `core` | 9109 | 0 | 0 | 45 | 26 | 7 |
| `source` | 3598 | 0 | 0 | 0 | 12 | 3 |

User-provided current cloc context: 78 KLOC. The inventory scanner reports
95041 Propstore Python lines because it uses its own Python-file scan, not
the user's cloc command.

Row-mapping metrics relevant to this workstream:

- `child_row_assembly_loops`: 1, at
  `propstore/families/micropublications/declaration.py:242`.
- `attribute_bucket_classes`: 6:
  `ClaimRow`, `ConceptRow`, `ParameterizationRow`, `RelationshipRow`,
  `StanceRow`, `ConflictRow`.
- `cross_table_select_sql`: 5, all in claims/concepts declaration surfaces.
- `multi_source_merge_methods`: 7, including contexts, concepts,
  micropublications, relations, and claims.
- `nested_document_from_mapping_methods`: 2.
- `row_factory_targets`: 2, both in concepts.

Exact context old-path hit counts:

```text
rg -n --count-matches "FROM context\b|FROM context_assumption\b|FROM context_lifting_rule\b|FROM context_lifting_materialization\b" propstore tests
propstore\families\contexts\declaration.py:3
tests\test_contexts.py:3
tests\test_context_lifting_ws5.py:1
tests\remediation\phase_2_gates\test_T2_2l_compiler_context_validation_quarantine.py:1
tests\remediation\phase_2_gates\test_T2_2m_compiler_context_lifting_quarantine.py:2

rg -n --count-matches "CONTEXT_.*PROJECTION|ContextSidecarRows" propstore tests
propstore\derived_build_plan.py:2
propstore\families\projection_catalog.py:8
propstore\families\contexts\declaration.py:25
tests\test_context_lifting_ws5.py:2

rg -n --count-matches "ProjectionTable\(|ProjectionForeignKey\(|ProjectionIndex\(" propstore/families/contexts propstore/context_lifting.py propstore/compiler/context.py --glob "*.py"
propstore/families/contexts\declaration.py:14
```

Context deletion targets from those searches:

- `ContextSidecarRows`
- `CONTEXT_PROJECTION`
- `CONTEXT_ASSUMPTION_PROJECTION`
- `CONTEXT_LIFTING_RULE_PROJECTION`
- `CONTEXT_LIFTING_MATERIALIZATION_PROJECTION`
- raw SQL in `load_lifting_system`
- context projection catalog entries that only expose those concrete tables

Context behavior tests:

- `tests/test_contexts.py`
- `tests/test_context_workflows.py`
- `tests/test_context_lifting_ws5.py`
- `tests/test_context_lifting_phase4.py`
- `tests/test_sidecar_contexts.py`
- `tests/test_source_list_and_context.py`
- Phase 1 gate also includes `tests/test_build_sidecar.py` and
  `tests/test_world_query.py`.

Exact claim old-path hit counts:

```text
rg -n --count-matches "ClaimRow\b|ClaimConceptLinkRow\b|SourcePromotionClaimRow\b" propstore tests
propstore\app\concept_views.py:2
propstore\core\active_claims.py:7
propstore\core\embeddings.py:2
propstore\core\graph_build.py:5
propstore\families\claims\declaration.py:11
propstore\families\claims\projection_model.py:7
propstore\praf\engine.py:2
propstore\world\bridge.py:2
propstore\world\journal_replay.py:2
propstore\world\model.py:7
propstore\world\overlay.py:7
propstore\world\types.py:2
tests\fixtures\journal.py:8
tests\test_algorithm_stage_types.py:2
tests\test_claim_views.py:15
tests\test_concept_views.py:10
tests\test_neighborhoods.py:8

rg -n --count-matches "FROM claim_core\b|FROM claim_concept_link\b|FROM claim_numeric_payload\b|FROM claim_text_payload\b|FROM claim_algorithm_payload\b|FROM justification\b|FROM conflict_witness\b" propstore tests
propstore\families\claims\declaration.py:16
propstore\families\relations\declaration.py:3
tests\sqlite_argumentation_store.py:2
tests\test_build_sidecar.py:26
tests\test_cas_rejection_no_orphan_rows.py:1
tests\test_claim_notes.py:2
tests\test_cli.py:1
tests\test_cli_render_policy_flags.py:3
tests\test_codex2_claim_dedupe_diverges_on_version.py:2
tests\test_conftest_insert_claim_regression.py:1
tests\test_graph_build.py:4
tests\test_promote_atomicity.py:1
tests\test_source_promotion_alignment.py:2
tests\test_source_relations.py:1
tests\remediation\phase_2_gates\test_T2_2c_stance_source_quarantine.py:1
tests\remediation\phase_2_gates\test_T2_2d_stance_target_quarantine.py:1
tests\remediation\phase_2_gates\test_T2_2e_justification_conclusion_quarantine.py:1
tests\remediation\phase_2_gates\test_T2_2f_justification_premise_quarantine.py:1
tests\remediation\phase_2_gates\test_T2_2g_micropublication_claim_quarantine.py:1
tests\remediation\phase_2_gates\test_T2_2h_in_claim_stance_quarantine.py:1
tests\remediation\phase_2_gates\test_T2_2o_compiler_claim_schema_quarantine.py:1
tests\remediation\phase_2_gates\test_T2_2r_source_promote_ambiguous_concept_quarantine.py:1
tests\remediation\phase_2_gates\test_T2_2s_source_promote_unresolved_concept_quarantine.py:1
tests\remediation\phase_7_race_atomicity\test_T7_5d_promotion_blocked_id_collision.py:1
tests\remediation\phase_7_race_atomicity\test_T7_5e_promotion_blocked_fk_payload.py:1
tests\remediation\phase_7_race_atomicity\test_T7_5f_sidecar_build_duplicate_claim.py:4

rg -n --count-matches "CLAIM_.*PROJECTION|CONFLICT_WITNESS_PROJECTION|JUSTIFICATION_PROJECTION|CLAIM_FTS_PROJECTION|CLAIM_VEC_PROJECTION|CLAIM_EMBEDDING_STATUS_PROJECTION" propstore tests
propstore\derived_build.py:2
propstore\families\claims\declaration.py:32
propstore\families\embeddings\declaration.py:4
propstore\families\micropublications\declaration.py:3
propstore\families\projection_catalog.py:20
propstore\families\relations\declaration.py:2
tests\test_codex2_claim_dedupe_diverges_on_version.py:11
tests\remediation\phase_7_race_atomicity\test_T7_5f_sidecar_build_duplicate_claim.py:8

rg -n --count-matches "ProjectionTable\(|ProjectionForeignKey\(|ProjectionIndex\(|FtsProjection\(|rowid_vec_projection|embedding_status_projection" propstore/families/claims --glob "*.py"
propstore/families/claims\declaration.py:29

rg -n --count-matches "SourcePromotionClaimRow|ClaimsPass|ClaimReference\b|ClaimIdentity\b|claim_diagnostics|claim_check" propstore tests
propstore\compiler\workflows.py:5
propstore\core\graph_build.py:2
propstore\derived_build.py:12
propstore\derived_build_plan.py:2
propstore\families\claims\declaration.py:3
propstore\families\claims\references.py:4
propstore\importing\passes.py:2
propstore\importing\stages.py:2
tests\test_artifact_reference_resolver.py:6
```

Claim deletion targets from those searches:

- `ClaimRow`
- `ClaimConceptLinkRow`
- `SourcePromotionClaimRow`
- `CLAIM_CORE_PROJECTION`
- `CLAIM_CONCEPT_LINK_PROJECTION`
- `CLAIM_NUMERIC_PAYLOAD_PROJECTION`
- `CLAIM_TEXT_PAYLOAD_PROJECTION`
- `CLAIM_ALGORITHM_PAYLOAD_PROJECTION`
- `CONFLICT_WITNESS_PROJECTION`
- `JUSTIFICATION_PROJECTION`
- `CLAIM_FTS_PROJECTION`
- `CLAIM_EMBEDDING_STATUS_PROJECTION`
- `CLAIM_VEC_PROJECTION`
- raw SQL query helpers over claim, payload, justification, and conflict tables

Claim behavior tests:

- `tests/test_claim_roundtrip_fixtures.py`
- `tests/test_claim_views.py`
- `tests/test_claim_workflows.py`
- `tests/test_claim_type_contracts.py`
- `tests/test_source_claims.py`
- `tests/test_promote_claim_immutability.py`
- `tests/test_validate_claims.py`
- `tests/test_materialized_claim_provenance_preserved.py`
- Phase 2 gate also includes `tests/test_build_sidecar.py`,
  `tests/test_world_query.py`, and `tests/test_relate_opinions.py`.

Known Quire capability blockers before deletion can proceed:

- Contexts: Quire has projection declarations and projection mapping, but this
  inventory has not yet verified a Quire query API that replaces
  `load_lifting_system` without a Propstore-local query wrapper. Phase 1 must
  verify that API or add a `BLOCKED:` entry to the workstream before deleting
  context query helpers.
- Claims: Quire-backed generated decoders and child-row declaration/query
  paths must be verified against a non-claim family in the same claim slice.
  If that non-claim consumer cannot be named before implementation, Phase 2
  must add a `BLOCKED:` entry rather than create a claim-only abstraction.

## Cleanup Target

For each family, one semantic declaration must own:

- projection table/column/FK/index identity;
- row encode/decode shape;
- typed query/read-model rows;
- FTS source plans;
- vector/status source plans;
- family reference boundaries;
- source-local versus canonical visibility;
- diagnostics/quarantine facts if that family owns them.

Quire owns the generic execution of those declarations. Propstore owns semantic
meaning. Propstore must not keep hand-written table/query/mapping boilerplate
once the declaration can express it.

## Family Inventory

| Family | Current files | Remaining custom surfaces | Why it matters | First old-path searches |
| --- | --- | --- | --- | --- |
| contexts and lifting | `propstore/families/contexts/declaration.py`, `propstore/context_lifting.py`, `propstore/compiler/context.py`, world query context reconstruction | `CONTEXT_*_PROJECTION`, `ContextSidecarRows`, raw `SELECT` over context tables, lifting materialization validation | Context references are shared by claims, micropublications, relations, diagnostics, and lifting. Cleaning this establishes the reference/cardinality pattern. | `FROM context`, `FROM context_assumption`, `FROM context_lifting_rule`, `FROM context_lifting_materialization`, `CONTEXT_.*PROJECTION` |
| claims | `propstore/families/claims/declaration.py`, `propstore/families/claims/projection_model.py`, `propstore/families/claims/storage.py`, `propstore/families/claims/stages.py` | `ClaimRow`, `ClaimConceptLinkRow`, `SourcePromotionClaimRow`, `CLAIM_*_PROJECTION`, `CONFLICT_WITNESS_PROJECTION`, `JUSTIFICATION_PROJECTION`, claim FTS/vector/status declarations, raw `SELECT`/`JOIN` over claim tables, promotion blocked row compilation | Claims are large but not special. They must be included as a full family vertical, not deferred indefinitely. The claim split into core/link/numeric/text/algorithm/justification/conflict/FTS/vector is load-bearing until proven otherwise. | `ClaimRow`, `ClaimConceptLinkRow`, `SourcePromotionClaimRow`, `FROM claim_core`, `FROM claim_concept_link`, `FROM claim_text_payload`, `CLAIM_.*PROJECTION`, `claim_fts`, `claim_vec` |
| concepts/forms/parameterization | `propstore/families/concepts/declaration.py`, `propstore/families/concepts/projection_model.py`, concept app/query callers | `ConceptRow`, `ParameterizationRow`, `ConceptRelationshipProjectionRow`, `CONCEPT_PROJECTION`, `FORM_PROJECTION`, `FORM_ALGEBRA_PROJECTION`, alias/parameterization/group declarations, concept FTS/vector/status declarations, many concept SQL queries | This is the densest query family after claims. It owns search, forms, aliases, and concept relationship surfaces. | `ConceptRow`, `ParameterizationRow`, `FROM concept`, `FROM alias`, `FROM parameterization`, `CONCEPT_.*PROJECTION`, `concept_fts`, `concept_vec` |
| relations and opinions | `propstore/families/relations/declaration.py`, `propstore/families/relations/projection_model.py`, `propstore/relation_analysis.py`, `propstore/world/queries.py`, graph/ASPIC readers | `RelationshipRow`, `StanceRow`, `ConflictRow`, relation-edge query APIs, conflict witness query APIs, opinion fields | Relation edge is the polymorphic physical table and is the main proof that claims are not privileged. Opinion metadata must be typed, not hidden in loose row surfaces. | `RelationshipRow`, `StanceRow`, `ConflictRow`, `FROM relation_edge`, `FROM conflict_witness`, `RELATION_EDGE_TABLE`, `opinion_` |
| sources | `propstore/families/sources/declaration.py`, source app/status/promote readers | `SOURCE_PROJECTION`, `SourceProjectionRow`, source query helpers, source trust projection fields | Canonical sources and source-local documents must stay separated. Source cleanup removed generic source machinery, but family source projection remains a family vertical. | `SOURCE_PROJECTION`, `SourceProjectionRow`, `FROM source`, `source_quality`, `source_prior_base_rate` |
| diagnostics and quarantine | `propstore/families/diagnostics/declaration.py`, authoring lints, source status, compiler diagnostics | `BUILD_DIAGNOSTICS_PROJECTION`, `SourceStatusDiagnosticRow`, `QuarantinableWriter`, raw diagnostics select/delete helpers | Diagnostics are cross-family but should still be a typed diagnostic declaration, not a custom SQL island. | `BUILD_DIAGNOSTICS_PROJECTION`, `FROM build_diagnostics`, `SourceStatusDiagnosticRow`, `QuarantinableWriter` |
| micropublications | `propstore/families/micropublications/declaration.py`, micropublication documents, world query readers | `MICROPUBLICATION_PROJECTION`, `MICROPUBLICATION_CLAIM_PROJECTION`, `MicropublicationProjectionRow`, `MicropublicationClaimProjectionRow`, raw select with nested claim aggregation | Micropublications tie contexts and claims together and exercise many-to-many child rows. | `MICROPUBLICATION_.*PROJECTION`, `FROM micropublication`, `FROM micropublication_claim`, `MicropublicationProjectionRow` |
| grounded rules | `propstore/families/rules/declaration.py`, grounding build/inspection/query paths | `GROUNDED_FACT_PROJECTION`, `GROUNDED_FACT_EMPTY_PREDICATE_PROJECTION`, `GROUNDED_BUNDLE_INPUT_PROJECTION`, three projection row classes, raw select reconstruction | Grounding persists enough input to rehydrate grounded bundles; it needs typed projection rows, not table-specific helpers. | `GROUNDED_.*PROJECTION`, `FROM grounded_fact`, `FROM grounded_bundle_input`, `GroundedFactProjectionRow` |
| calibration | `propstore/families/calibration/declaration.py`, trust calibration readers | `CALIBRATION_COUNTS_PROJECTION`, `CalibrationCountsProjectionRow`, raw select helper | Smallest vertical; useful as a low-risk proof for declaration compression after harder shared patterns are known. | `CALIBRATION_COUNTS_PROJECTION`, `FROM calibration_counts`, `CalibrationCountsProjectionRow` |
| embeddings/vector | `propstore/families/embeddings/declaration.py`, claim/concept declarations, heuristic/app embedding callers | embedding model/status projections, dynamic vec table declarations, snapshot/restore plumbing | Vector storage is generic machinery plus semantic text identity. Quire owns vector mechanics; families own text/source meaning. | `embedding_status`, `concept_embedding_status`, `claim_vec`, `concept_vec`, `rowid_vec_projection`, `embedding_status_projection` |

## Verified Family File Inventory

Read-only file listing on 2026-05-17 showed the family surface is broader than
the declaration modules. These files are in scope for deletion-first cleanup
when their family or cross-family owner is active:

| Owner | Files |
| --- | --- |
| claims | `propstore/families/claims/declaration.py`, `propstore/families/claims/documents.py`, `propstore/families/claims/projection_model.py`, `propstore/families/claims/references.py`, `propstore/families/claims/sidecar_runtime.py`, `propstore/families/claims/stages.py`, `propstore/families/claims/storage.py`, `propstore/families/claims/passes/checks.py`, `propstore/families/claims/passes/diagnostics.py` |
| contexts | `propstore/families/contexts/declaration.py`, `propstore/families/contexts/documents.py`, `propstore/families/contexts/passes.py`, `propstore/families/contexts/stages.py`, `propstore/context_lifting.py`, `propstore/compiler/context.py` |
| concepts | `propstore/families/concepts/declaration.py`, `propstore/families/concepts/documents.py`, `propstore/families/concepts/passes.py`, `propstore/families/concepts/projection_model.py`, `propstore/families/concepts/sidecar_runtime.py`, `propstore/families/concepts/stages.py` |
| forms | `propstore/families/forms/documents.py`, `propstore/families/forms/passes.py`, `propstore/families/forms/stages.py` |
| relations | `propstore/families/relations/declaration.py`, `propstore/families/relations/projection_model.py`, `propstore/relation_analysis.py` |
| rules | `propstore/families/rules/declaration.py`, `propstore/families/documents/rules.py`, `propstore/families/documents/predicates.py` |
| sources | `propstore/families/sources/declaration.py`, `propstore/families/documents/sources.py`, `propstore/families/documents/source_alignment.py` |
| diagnostics | `propstore/families/diagnostics/declaration.py`, `propstore/families/diagnostics/authoring_lints.py` |
| micropublications | `propstore/families/micropublications/declaration.py`, `propstore/families/documents/micropubs.py` |
| calibration | `propstore/families/calibration/declaration.py` |
| embeddings | `propstore/families/embeddings/declaration.py` |
| same-as | `propstore/families/sameas/documents.py` |
| identity | `propstore/families/identity/claims.py`, `propstore/families/identity/concepts.py`, `propstore/families/identity/justifications.py`, `propstore/families/identity/logical_ids.py`, `propstore/families/identity/micropubs.py`, `propstore/families/identity/stances.py` |
| family registry | `propstore/families/registry.py`, `propstore/families/projection_catalog.py`, `propstore/families/addresses.py` |
| shared documents | `propstore/families/documents/justifications.py`, `propstore/families/documents/merge.py`, `propstore/families/documents/stances.py`, `propstore/families/documents/worldlines.py` |

Identity, shared document, registry, projection-catalog, address, forms, and
same-as surfaces are not optional leftovers. They are either their own vertical
or an explicitly named dependency of the active family slice.

## Cross-Family Repeated Surfaces

These are not separate verticals. They are repeated patterns that each family
vertical must reduce when it touches the owner:

- row dataclasses whose main job is projection storage shape;
- raw `conn.execute(...)` with table-name SQL in family declarations;
- hand-authored `ProjectionTable`, `ProjectionForeignKey`, and
  `ProjectionIndex` lists not generated from the family projection model;
- FTS `source_query` SQL strings not declared through a Quire FTS source plan;
- vector/status declaration calls not sourced from one family semantic
  embedding declaration;
- sidecar row bundle classes that only package projection rows;
- typed app/world request/report rows that merely restate family fields.

## Required Per-Family Inventory Before Edits

For each family vertical, append a short section to this inventory before
editing production code:

- exact old-path search commands;
- exact files owned by the slice;
- row classes to delete;
- projection constants to delete or move under generated/declaration ownership;
- raw SQL query helpers to delete or replace with generated typed query APIs;
- FTS/vector declarations involved;
- tests that prove behavior;
- scanner metrics expected to decrease;
- any load-bearing table split that is deliberately retained.

### Contexts Required Inventory

Owned files:

- `propstore/families/contexts/declaration.py`
- `propstore/families/contexts/documents.py`
- `propstore/families/contexts/passes.py`
- `propstore/families/contexts/stages.py`
- `propstore/context_lifting.py`
- `propstore/compiler/context.py`

Old-path searches:

```powershell
rg -n "FROM context\b|FROM context_assumption\b|FROM context_lifting_rule\b|FROM context_lifting_materialization\b" propstore tests
rg -n "CONTEXT_.*PROJECTION|ContextSidecarRows" propstore tests
rg -n "ProjectionTable\(|ProjectionForeignKey\(|ProjectionIndex\(" propstore/families/contexts propstore/context_lifting.py propstore/compiler/context.py --glob "*.py"
rg -n "ContextDocument|ContextStage|ContextPass|context_lifting" propstore/families/contexts propstore/context_lifting.py propstore/compiler/context.py tests
```

Rows/projection constants/query helpers to delete or replace must be listed
from those searches before any context implementation edit. Context table split
and context-lifting materialization are assumed load-bearing until the slice
proves otherwise.

Behavior tests verified present by file-name search:

- `tests/test_contexts.py`
- `tests/test_context_workflows.py`
- `tests/test_context_lifting_ws5.py`
- `tests/test_context_lifting_phase4.py`
- `tests/test_sidecar_contexts.py`
- `tests/test_source_list_and_context.py`

### Claims Required Inventory

Owned files:

- `propstore/families/claims/declaration.py`
- `propstore/families/claims/documents.py`
- `propstore/families/claims/projection_model.py`
- `propstore/families/claims/references.py`
- `propstore/families/claims/sidecar_runtime.py`
- `propstore/families/claims/stages.py`
- `propstore/families/claims/storage.py`
- `propstore/families/claims/passes/checks.py`
- `propstore/families/claims/passes/diagnostics.py`
- `propstore/families/identity/claims.py`

Old-path searches:

```powershell
rg -n "ClaimRow\b|ClaimConceptLinkRow\b|SourcePromotionClaimRow\b" propstore tests
rg -n "FROM claim_core\b|FROM claim_concept_link\b|FROM claim_numeric_payload\b|FROM claim_text_payload\b|FROM claim_algorithm_payload\b|FROM justification\b|FROM conflict_witness\b" propstore tests
rg -n "CLAIM_.*PROJECTION|CONFLICT_WITNESS_PROJECTION|JUSTIFICATION_PROJECTION|CLAIM_FTS_PROJECTION|CLAIM_VEC_PROJECTION|CLAIM_EMBEDDING_STATUS_PROJECTION" propstore tests
rg -n "ProjectionTable\(|ProjectionForeignKey\(|ProjectionIndex\(|FtsProjection\(|rowid_vec_projection|embedding_status_projection" propstore/families/claims --glob "*.py"
rg -n "SourcePromotionClaimRow|ClaimsPass|ClaimReference\b|ClaimIdentity\b|claim_diagnostics|claim_check" propstore tests
```

Rows/projection constants/query helpers to delete or replace must be listed
from those searches before any claim implementation edit. Claims are not
special, but the current claim physical split is assumed load-bearing until
separately proven unnecessary.

Behavior tests verified present by file-name search:

- `tests/test_claim_roundtrip_fixtures.py`
- `tests/test_claim_views.py`
- `tests/test_claim_workflows.py`
- `tests/test_claim_type_contracts.py`
- `tests/test_source_claims.py`
- `tests/test_promote_claim_immutability.py`
- `tests/test_validate_claims.py`
- `tests/test_materialized_claim_provenance_preserved.py`

## Initial Execution Order

The workstream must include claims. The order is:

1. contexts and lifting;
2. claims, first inventory then split into sub-slices if needed;
3. relations and opinions;
4. concepts and parameterization;
5. forms;
6. identity and shared document surfaces that block completed family deletion;
7. diagnostics/quarantine;
8. micropublications;
9. grounded rules;
10. sources;
11. family registry/projection catalog/address surfaces;
12. calibration;
13. embeddings/vector.

Claims are second so they are neither privileged as the only architecture driver
nor avoided because they are large.
