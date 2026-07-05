# scout-field-ownership-violations progress

## State at checkpoint 2

- HEAD: e13e302d195ddf38bbde5c965744e992ae57166b
- Tree state: only untracked files; no modified tracked files; no conflict with parallel scout
- Parallel scout `reports/scout-failing-tests-triage.md` STILL DOES NOT EXIST — section 5 will say "PARALLEL SCOUT NOT YET LANDED"

## Reads completed (all required)
- prompt file (71 lines)
- 00-index.md (72 lines)
- phase 01..12 all read
- six breakdown reports all read:
  - quire-prereqs-report.md (207L)
  - family-docs-registry-report.md (216L)
  - source-lifecycle-report.md (148L)
  - root-semantic-surfaces-report.md (128L)
  - worldline-resolution-report.md (133L)
  - old-workstream-reconciliation-report.md (~206L)
- CLAUDE.md (from system reminder context — full content available)

## Verified violations with current file:line evidence (collected so far)

### V001-class: deleted-file fallout (Phase 01)
- `world_charters` imports in:
  - propstore/app/concepts/display.py:30
  - propstore/compiler/workflows.py:88
  - propstore/source/status.py:18
  - propstore/families/claims/sidecar_runtime.py:11
  - propstore/families/contexts/declaration.py:188
  - propstore/world/model.py:53
  - propstore/families/concepts/sidecar_runtime.py:9
  - propstore/families/embeddings/declaration.py:39
- `claim_metadata_value` imports in: propstore/preference.py:11, propstore/praf/engine.py:22, propstore/world/resolution.py:23 (with usages at preference.py:79-85, praf/engine.py:202-277, world/resolution.py:593-597)

### V002-class: direct string table/model lookup (Phase 03)
- `derived.schema.table("claim_core")`: propstore/source/status.py:56, propstore/families/claims/declaration.py:770
- `derived.schema.table("build_diagnostics")`: propstore/families/diagnostics/declaration.py:187,202,226
- `derived.schema.model("build_diagnostics")`: propstore/families/diagnostics/declaration.py:188,203
- `schema.model("claim_core")`: propstore/families/claims/sidecar_runtime.py:78,116; propstore/families/embeddings/declaration.py:108,291; propstore/world/model.py:289,313,334,411,455,629,847
- `schema.model("concept")`: propstore/app/concepts/display.py:51; propstore/families/embeddings/declaration.py:134,340; propstore/world/model.py:237,261,553,697,846
- `schema.model("alias")`: propstore/families/embeddings/declaration.py:135
- `schema.model("context"/_assumption/_lifting_rule)`: propstore/families/contexts/declaration.py:191-193

### V003-class: handwritten family document files (Phase 04)
- propstore/families/{claims,concepts,contexts,forms,sameas}/documents.py (5)
- propstore/families/documents/{source_alignment,merge,justifications,stances,predicates,rules,micropubs,sources,worldlines}.py (9)

### V004-class: registry-owned field/reference facts (Phase 05)
- propstore/families/registry.py:339 CLAIM_FOREIGN_KEYS; :399 CONCEPT_FOREIGN_KEYS; :444 STANCE_FOREIGN_KEYS; :472 JUSTIFICATION_FOREIGN_KEYS; :493 MICROPUBLICATION_FOREIGN_KEYS; :512 CLAIM_REFERENCE_KEYS; :518 CONCEPT_REFERENCE_KEYS
- propstore/families/batch_specs.py:14-48 six DocumentBatchSpec
- propstore/families/registry.py:606-783 decode/render/payload helpers
- propstore/contracts.py:19 DOCUMENT_SCHEMA_CONTRACT_VERSION_OVERRIDES; :129 iter_document_schema_types; :20 worldline class path keyed override

### V005-class: source-local helpers (Phase 06)
- propstore/source/claim_concepts.py:18 ClaimConceptSource union (the forbidden Document|Doc|Mapping)
- propstore/source/claim_concepts.py:36 rewrite_claim_concept_refs; :155 _claim_payload; :161 _place_source_local_concept

### V006-class: proposal root workflows (Phase 07)
- propstore/proposals.py:58 StanceProposalPromotionPlan
- propstore/proposals_rules.py:32 RuleProposalPromotionPlan
- propstore/proposals_predicates.py:40 PredicateProposalPromotionPlan

### V007-class: artifact/graph hardcoded (Phase 08)
- propstore/artifact_codes.py exists 253L with concrete doc imports
- propstore/artifact_verification.py exists 280L; verify_claim_tree manual walk
- propstore/graph_export.py:23 _claim_concept_id; :37 _display_claim_id_from_store; :151 build_knowledge_graph; :239 json.loads(row.concept_ids)

### V008-class: worldline (Phase 09)
- propstore/worldline/resolution.py 653L (huge)
- propstore/worldline/resolution.py:63 def _claim_value; :281 _resolve_claim_target; :528 _resolve_claim_input
- duplicate _claim_value also at world/resolution.py:134, world/value_resolver.py:66, world/assignment_selection_policy.py:37 (FOUR copies)
- propstore/families/documents/worldlines.py 164L hand-authored
- propstore/families/registry.py:64,971 imports/registers WorldlineDefinitionDocument
- propstore/contracts.py:20 class-path version override
- propstore/_resources/contract_manifests/semantic-contracts.yaml:577,2686,3969 references handwritten worldline doc path

### V009-class: context-lifting root module (Phase 10)
- propstore/context_lifting.py 497L; imported from 24+ callers across aspic_bridge, conflict_detector, core, families/contexts, app/contexts, cli/context, world/*, worldline/*
- CanonicalJustification constructors: propstore/aspic_bridge/extract.py:67,80,91; propstore/core/justifications.py:40,116,131
- _claim_algorithm_variable_from_payload: propstore/families/claims/stages.py:57,114

### V010-class: concept_ids + compat (Phase 11)
- propstore/concept_ids.py 191L root module; consumed by propstore/app/concepts/mutation.py:29,954,981

## Outstanding before writing report
- Still need to check: CLI-owns-domain violations (Phase boundaries with cli/* importing workflow semantics)
- Need to quickly enumerate which phase file quotes which IDs for the phase-mapping table — already mapped above per-section.

## Blocker
None. Proceeding to write final report. The breakdown reports are at `reports/charter-cutover-breakdown/` (top-level), not `workstreams/.../reports/` — already located.
