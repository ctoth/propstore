# Family Declaration Cleanup Workstream - 2026-05-17

Status: executable for Phase 0 and Phase 1; Phase 2 claims inventory is required
before any post-context family implementation. This workstream is the active
control surface after `workstreams/family-declaration-cleanup-inventory-2026-05-17.md`.

Inventory:

- `workstreams/family-declaration-cleanup-inventory-2026-05-17.md`

Parent workstreams:

- `workstreams/repo-wide-typed-metadata-cleanup-workstream-2026-05-14.md`
- `workstreams/generic-quire-projection-mapping-workstream-2026-05-16.md`
- `workstreams/quire-explicit-projection-boundaries-workstream-2026-05-16.md`

Completed dependency:

- `workstreams/source-generic-machinery-deletion-workstream-2026-05-17.md`

## Goal

Delete family-specific derived-store declaration, row-mapping, query, FTS, and
vector boilerplate by moving each family to one typed semantic declaration
surface backed by Quire projection/query mechanics.

This is not a source cleanup and not a claim-only cleanup. Claims are a required
family vertical and must not be skipped, avoided, or treated as privileged.

## Target State

For every durable family surface:

- one family-owned semantic declaration names the fields, references,
  visibility, FTS/vector meaning, and query/read-model shape;
- Quire owns generic DDL, FKs, indexes, schema hash material, row encoding,
  row decoding, FTS/vector mechanics, and query-plan execution through
  `quire.projections` and `quire.projection_mapping` unless a Phase 0/Phase N
  blocker names a missing Quire owner and exact API shape;
- family declaration modules contain semantic declarations and semantic
  extraction logic, not hand-written table/query boilerplate;
- app/world/source/heuristic/CLI layers use typed owner APIs and do not know
  physical table names.

## Non-Negotiables

- Deletion-first: delete the old production surface for the active family slice
  before introducing a replacement spelling.
- No compatibility paths, aliases, fallback readers, or old/new bridges.
- No Propstore-local generic ORM/mapper DSL parallel to Quire.
- No claim-special API. Every abstraction used for claims must be usable by at
  least one non-claim family.
- Do not collapse authored artifact shape, source-local shape, projection row
  shape, runtime domain shape, and app/report shape into one object.
- Do not merge load-bearing physical tables without a separate proof.
- Reread this workstream and the inventory before every implementation edit.
- Before starting a family implementation slice, append that family's populated
  "Required Per-Family Inventory" section to the inventory and commit it.
- After every implementation commit and every passing substantial targeted test
  run, reread this workstream and identify the next unchecked item.
- Run scanner diffs for every family slice and keep only slices that reduce the
  targeted handwritten surface.

## Current Evidence

Read-only checks on 2026-05-17 showed the old explicit-boundary blocker names
are already absent:

```powershell
rg -n -F "decode_columns" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
rg -n -F "CompositePath" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
rg -n -F "DerivedPath" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
rg -n -F "attribute_bucket" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
rg -n -F "decode_key" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
rg -n -F "ignored_columns" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
rg -n -F "claim_select_sql" propstore tests
rg -n "RELATION_EDGE_PROJECTION|STANCE_SELECT_COLUMNS|claim_stance_projection_row" propstore tests
```

Current scanner output shows the remaining center of gravity:

- `propstore/families`: raw SQL score `273`, projection columns `18`,
  class surfaces `24`;
- `propstore/source`: raw SQL score `0`;
- app/source/heuristic red SQL is no longer the main blocker.

## Phase 0: Baseline And Family Gate Refresh

Status: executable.

Run:

```powershell
git status --short --branch
uv run scripts/typed_metadata_inventory.py --format markdown --limit 120
uv run scripts/typed_metadata_inventory.py --format json --emit-row-mapping-metrics
uv run scripts/typed_metadata_inventory.py --gates --ledger workstreams/typed-metadata-owner-ledger-2026-05-15.csv
rg -n "class .*Row|ProjectionTable\(|ProjectionForeignKey\(|ProjectionIndex\(|FtsProjection\(|rowid_vec_projection|embedding_status_projection|SELECT |FROM |JOIN |\.execute\(" propstore/families --glob "*.py" > workstreams/phase-0-family-surface-baseline-2026-05-17.txt
```

Then update the inventory with:

- current family metrics;
- exact old-path search results for contexts and claims;
- exact targeted tests for contexts and claims;
- any Quire capability that is missing before deletion can proceed.

Gate:

- no tracked dirty files before implementation;
- inventory contains populated `Contexts Required Inventory` and
  `Claims Required Inventory` sections with runnable `rg` lines and enumerated
  test paths;
- `workstreams/phase-0-family-surface-baseline-2026-05-17.txt` exists and
  contains the initial family-surface scan;
- `scripts/typed_metadata_inventory.py` emits every metric referenced by this
  workstream, including `child_row_assembly_loops`;
- any blocker is explicit and tied to a missing owner/capability.

## Phase 1: Contexts And Lifting Vertical

Status: next implementation phase after Phase 0 refresh.

Owned files:

- `propstore/families/contexts/declaration.py`
- `propstore/families/contexts/documents.py`
- `propstore/families/contexts/passes.py`
- `propstore/families/contexts/stages.py`
- `propstore/context_lifting.py`
- `propstore/compiler/context.py`
- context/lifting tests directly affected by deleted APIs
- generated/declaration-owner files if Quire-backed output already exists

Delete first:

- context projection row/bundle surfaces whose only job is table shape;
- hand-written query helpers over context tables once their typed query owner is
  in place;
- duplicated FK/index declarations that the declaration/query model can derive.

Old-path searches:

```powershell
rg -n "FROM context\b|FROM context_assumption\b|FROM context_lifting_rule\b|FROM context_lifting_materialization\b" propstore tests
rg -n "CONTEXT_.*PROJECTION|ContextSidecarRows" propstore tests
rg -n "ProjectionTable\(|ProjectionForeignKey\(|ProjectionIndex\(" propstore/families/contexts --glob "*.py"
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label family-contexts tests/test_contexts.py tests/test_context_lifting_ws5.py tests/test_build_sidecar.py tests/test_world_query.py
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric projection_table_column_count --metric row_factory_targets --metric row_class_from_mapping_loc --metric row_class_to_dict_loc
```

Required result:

- context/lifting behavior is unchanged;
- context-derived boilerplate decreases;
- context references remain Quire family references/FKs;
- no local context mapper/query wrapper is introduced.

## Phase 2: Claims Vertical, Mandatory Inventory And Slices

Status: mandatory before moving to relations or concepts.

Claims must not be skipped. This phase opens immediately after Phase 1 passes.
It may be split into sub-slices, but the claims vertical remains active until
each sub-slice is complete or explicitly blocked in this file with evidence.

Owned files:

- `propstore/families/claims/declaration.py`
- `propstore/families/claims/documents.py`
- `propstore/families/claims/projection_model.py`
- `propstore/families/claims/references.py`
- `propstore/families/claims/sidecar_runtime.py`
- `propstore/families/claims/storage.py`
- `propstore/families/claims/stages.py`
- `propstore/families/claims/passes/checks.py`
- `propstore/families/claims/passes/diagnostics.py`
- `propstore/families/identity/claims.py`
- tests directly affected by deleted claim APIs

Pre-implementation inventory:

```powershell
rg -n "ClaimRow\b|ClaimConceptLinkRow\b|SourcePromotionClaimRow\b" propstore tests
rg -n "FROM claim_core\b|FROM claim_concept_link\b|FROM claim_numeric_payload\b|FROM claim_text_payload\b|FROM claim_algorithm_payload\b|FROM justification\b|FROM conflict_witness\b" propstore tests
rg -n "CLAIM_.*PROJECTION|CONFLICT_WITNESS_PROJECTION|JUSTIFICATION_PROJECTION|CLAIM_FTS_PROJECTION|CLAIM_VEC_PROJECTION|CLAIM_EMBEDDING_STATUS_PROJECTION" propstore tests
rg -n "ProjectionTable\(|ProjectionForeignKey\(|ProjectionIndex\(|FtsProjection\(|rowid_vec_projection|embedding_status_projection" propstore/families/claims --glob "*.py"
rg -n "SourcePromotionClaimRow|ClaimsPass|ClaimReference\b|ClaimIdentity\b|claim_diagnostics|claim_check" propstore tests
```

Required sub-slices:

1. Delete claim projection row classes and replace them with Quire-backed
   generated decoders.
2. Delete claim concept-link child-row assembly and replace it with the same
   child-row declaration/query path used by another family.
3. Delete claim-only payload-table mapping helpers for numeric, text, and
   algorithm payloads after the generic declaration can express them.
4. Delete claim-only justification and conflict witness projection helpers.
5. Delete `SourcePromotionClaimRow` or move the semantics to a generic
   family-promotion declaration used by a non-claim family in the same slice.
6. Delete claim-local FTS SQL source plan in favor of the Quire FTS source plan.
7. Delete claim-local embedding status/vector helper declarations in favor of
   the family semantic embedding declaration.
8. Delete hand-written claim `SELECT`/`JOIN` helpers after typed query APIs
   replace each caller.

Gate per sub-slice:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label family-claims tests/test_claim_roundtrip_fixtures.py tests/test_claim_views.py tests/test_build_sidecar.py tests/test_world_query.py tests/test_source_claims.py tests/test_relate_opinions.py
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric row_class_from_mapping_loc --metric row_class_to_dict_loc --metric child_row_assembly_loops --metric projection_table_column_count --metric raw_sql_score
```

Each new declaration/query API introduced for a claim sub-slice must be
consumed by at least one non-claim family in the same commit or the slice does
not land. The commit message must name the non-claim caller and the `rg` command
used to verify it. If no non-claim caller can exist yet, append a `BLOCKED:`
entry to this file naming the missing Quire owner module, the missing API
signature, and the file/line of the read-only verification before stopping.

Required result:

- claims remain semantically unchanged;
- no claim-only Quire API is added;
- claim table split is preserved unless separately proven unnecessary;
- handwritten claim mapping/query/projection boilerplate decreases after each
  kept sub-slice;
- claims are not deferred behind later families.

## Phase 3: Relations And Opinions Vertical

Status: blocked until Phase 2 is complete or explicitly blocked.

Inventory refresh:

- append and commit `Relations And Opinions Required Inventory` to the
  inventory before implementation edits.

Old-path searches:

```powershell
rg -n "RelationshipRow\b|StanceRow\b|ConflictRow\b" propstore tests
rg -n "FROM relation_edge\b|FROM conflict_witness\b" propstore tests
rg -n "opinion_belief|opinion_disbelief|opinion_uncertainty|opinion_base_rate|resolution_method|resolution_model|embedding_distance" propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label family-relations tests/test_sidecar_relation_edge_projection.py tests/test_relate_opinions.py tests/test_graph_build.py tests/test_world_query.py tests/test_praf.py
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric row_class_from_mapping_loc --metric row_class_to_dict_loc --metric raw_sql_score
```

## Phase 4: Concepts And Parameterization Vertical

Status: blocked until Phase 3.

Inventory refresh:

- append and commit `Concepts Required Inventory` to the inventory before
  implementation edits.

Old-path searches:

```powershell
rg -n "ConceptRow\b|ParameterizationRow\b|ConceptRelationshipProjectionRow\b" propstore tests
rg -n "FROM concept\b|FROM alias\b|FROM parameterization\b|FROM parameterization_group\b|FROM form\b|FROM form_algebra\b|FROM concept_fts\b" propstore tests
rg -n "CONCEPT_.*PROJECTION|FORM_PROJECTION|FORM_ALGEBRA_PROJECTION|ALIAS_PROJECTION|PARAMETERIZATION_.*PROJECTION|CONCEPT_FTS_PROJECTION|CONCEPT_VEC_PROJECTION|CONCEPT_EMBEDDING_STATUS_PROJECTION" propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label family-concepts tests/test_sidecar_concept_projection.py tests/test_concept_views.py tests/test_build_sidecar.py tests/test_graph_build.py tests/test_world_query.py
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric projection_table_column_count --metric raw_sql_score --metric attributes_bucket_classes
```

## Phase 5: Forms Vertical

Status: blocked until Phase 4.

Inventory refresh:

- append and commit `Forms Required Inventory` to the inventory before
  implementation edits.

Old-path searches:

```powershell
rg -n "FormDocument|FormStage|FormPass|FORM_PROJECTION|FORM_ALGEBRA_PROJECTION" propstore/families/forms propstore/families/concepts tests
rg -n "FROM form\b|FROM form_algebra\b" propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label family-forms tests/test_form_algebra.py tests/test_build_sidecar.py tests/test_world_query.py
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric projection_table_column_count --metric raw_sql_score
```

## Phase 6: Identity And Shared Document Surfaces

Status: blocked until Phase 5.

Inventory refresh:

- append and commit `Identity And Shared Documents Required Inventory` to the
  inventory before implementation edits.

Old-path searches:

```powershell
rg -n "ClaimIdentity|ConceptIdentity|LogicalId\b|MicropublicationIdentity|StanceIdentity|JustificationIdentity" propstore/families/identity propstore tests
rg -n "from_mapping|to_dict|dict\\[|Dict\\[" propstore/families/documents propstore/families/identity --glob "*.py"
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label family-identity-documents tests/test_claim_type_contracts.py tests/test_claim_and_stance_document_enums.py tests/test_micropublications_phase4.py tests/test_build_sidecar.py
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric nested_document_from_mapping_methods --metric row_class_from_mapping_loc --metric row_class_to_dict_loc
```

## Phase 7: Diagnostics And Quarantine Vertical

Status: blocked until Phase 6.

Inventory refresh:

- append and commit `Diagnostics Required Inventory` to the inventory before
  implementation edits.

Old-path searches:

```powershell
rg -n "BUILD_DIAGNOSTICS_PROJECTION|SourceStatusDiagnosticRow|QuarantinableWriter" propstore tests
rg -n "FROM build_diagnostics\b|DELETE FROM build_diagnostics\b" propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label family-diagnostics tests/test_build_sidecar.py tests/test_cli_source_status.py tests/test_render_policy_filtering.py tests/remediation/phase_2_gates
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric projection_table_column_count --metric raw_sql_score
```

## Phase 8: Micropublications Vertical

Status: blocked until Phase 7.

Inventory refresh:

- append and commit `Micropublications Required Inventory` to the inventory
  before implementation edits.

Old-path searches:

```powershell
rg -n "MICROPUBLICATION_.*PROJECTION|MicropublicationProjectionRow|MicropublicationClaimProjectionRow" propstore tests
rg -n "FROM micropublication\b|FROM micropublication_claim\b" propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label family-micropublications tests/test_build_sidecar.py tests/test_micropublications_phase4.py tests/test_micropub_identity_dedupe_shape.py tests/test_world_query.py
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric projection_table_column_count --metric raw_sql_score
```

## Phase 9: Grounded Rules Vertical

Status: blocked until Phase 8.

Inventory refresh:

- append and commit `Grounded Rules Required Inventory` to the inventory before
  implementation edits.

Old-path searches:

```powershell
rg -n "GROUNDED_.*PROJECTION|GroundedFactProjectionRow|GroundedBundleInputProjectionRow" propstore tests
rg -n "FROM grounded_fact\b|FROM grounded_fact_empty_predicate\b|FROM grounded_bundle_input\b" propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label family-grounded-rules tests/test_sidecar_grounded_facts.py tests/test_argumentation_integration.py tests/test_build_sidecar.py
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric projection_table_column_count --metric raw_sql_score
```

## Phase 10: Sources Vertical

Status: blocked until Phase 9.

Inventory refresh:

- append and commit `Sources Required Inventory` to the inventory before
  implementation edits.

Old-path searches:

```powershell
rg -n "SOURCE_PROJECTION|SourceProjectionRow|FROM source\b" propstore tests
rg -n "source_prior_base_rate|source_quality_json|source_quality_opinion|source_derived_from_json" propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label family-sources tests/test_build_sidecar.py tests/test_source_cli.py tests/test_source_trust.py tests/test_world_query.py
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric projection_table_column_count --metric raw_sql_score
```

## Phase 11: Family Registry, Projection Catalog, And Addresses

Status: blocked until Phase 10.

Inventory refresh:

- append and commit `Family Registry Required Inventory` to the inventory before
  implementation edits.

Old-path searches:

```powershell
rg -n "PropstoreFamily|PROPSTORE_FAMILY_REGISTRY|projection_catalog|PlacementContract|family.*root|init_directory|import_order" propstore/families/registry.py propstore/families/projection_catalog.py propstore/families/addresses.py propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label family-registry tests/test_init.py tests/test_build_sidecar.py tests/test_import_repo.py
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric quire_projection_mapping_imports --metric projection_table_column_count
```

## Phase 12: Calibration Vertical

Status: blocked until Phase 11.

Inventory refresh:

- append and commit `Calibration Required Inventory` to the inventory before
  implementation edits.

Old-path searches:

```powershell
rg -n "CALIBRATION_COUNTS_PROJECTION|CalibrationCountsProjectionRow|FROM calibration_counts\b" propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label family-calibration tests/test_calibrate.py tests/test_source_trust.py tests/test_build_sidecar.py
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric projection_table_column_count --metric raw_sql_score
```

## Phase 13: Embeddings And Vector Vertical

Status: blocked until Phase 12. Claim and concept embedding-status/vector
declarations are owned by Phase 2 and Phase 4. This phase owns
`propstore/families/embeddings/declaration.py` and generic Quire vector or
embedding plumbing only.

Inventory refresh:

- append and commit `Embeddings Required Inventory` to the inventory before
  implementation edits.

Old-path searches:

```powershell
rg -n "embedding_status|concept_embedding_status|claim_vec|concept_vec|rowid_vec_projection|embedding_status_projection|VecProjection|sqlite_vec" propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label family-embeddings tests/test_embed_operational_error.py tests/test_build_sidecar.py tests/test_claim_views.py tests/test_concept_views.py
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric projection_table_column_count --metric raw_sql_score
```

## Phase 14: World/App Consequence Sweep

Status: blocked until Phase 13.

Delete only consequence code that became dead because family typed APIs own it.

Searches:

```powershell
rg -n "materialize_world_sidecar|DerivedStoreHandle|validate_derived_store_schema|SELECT |FROM |JOIN |\.execute\(" propstore/app propstore/world propstore/heuristic propstore/source propstore/merge --glob "*.py"
```

Required result:

- app/world/source/heuristic/merge layers contain no table-shape knowledge;
- remaining uses are typed derived-store handles or domain reasoning only.

## Phase 15: Final Gates

Status: blocked until Phase 14.

Run:

```powershell
uv run scripts/typed_metadata_inventory.py --format markdown --limit 120
uv run scripts/typed_metadata_inventory.py --format json --emit-row-mapping-metrics
uv run scripts/typed_metadata_inventory.py --gates --ledger workstreams/typed-metadata-owner-ledger-2026-05-15.csv
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label family-declaration-cleanup-targeted tests/test_build_sidecar.py tests/test_world_query.py tests/test_claim_roundtrip_fixtures.py tests/test_relate_opinions.py tests/test_source_cli.py tests/test_contexts.py tests/test_sidecar_grounded_facts.py
powershell -File scripts/run_logged_pytest.ps1 -Label family-declaration-cleanup-full
```

Completion requires:

- claims included and completed, or a `BLOCKED:` entry in this file naming the
  missing Quire owner module, the missing API signature, and the file/line of
  read-only verification;
- family raw SQL score materially reduced from the Phase 0 refreshed baseline;
- no custom table/query/mapping surface remains outside the declaration/query
  owner for completed families;
- old production paths do not coexist with new generated/declaration paths;
- no claim-only abstraction was introduced.
