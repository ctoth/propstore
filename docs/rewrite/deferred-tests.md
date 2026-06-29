# Cross-phase deferred PORT tests

Tests whose behavioral contract is owned by a slice, but whose *infrastructure*
(WorldStore, source Documents, sidecar projection schemas, praf engine, render
policy) lands in a later phase. These are NOT dropped — they must be PORTed when
their owning phase is built. The Phase-9/10 completion gate is not satisfied
until every row here is green.

Recording convention: `reference test -> owning phase (infra it needs)`.

## Deferred during Phase 5a (commit 1bc1ace3)

5a built the value/honesty layer self-contained over quire; these need substrate
that 5a deliberately did not stub (stubbing phantom infra would violate
build-fresh + no-Document-mirror):

- test_relate_opinions.py -> 6/10 (classify/proposals/sidecar/core.relations — 5b reconfirmed)
- test_relation_concept_identity.py -> 6/10 (relation+concept alignment graph — 5b reconfirmed)
- test_source_relations.py -> 8 (source subsystem)
- test_trust_calibration_runs_at_promote.py -> 8 (source promote lifecycle)
- test_sidecar_relation_edge_projection.py -> 9 (projection_catalog relation_edge schema)
- test_sidecar_calibration_counts_projection.py -> 9/10 (families.calibration sidecar; calibration extract)
- test_opinion_schema.py -> 9/10 (opinion sidecar/schema projection)
- test_render_policy_opinions.py -> 10 (render policy)
- test_prior_base_rate_is_opinion.py -> 7 (base-rate resolution against a store)
- test_claim_and_stance_document_enums.py -> 9/10 (families.documents surface — 5b reconfirmed)

## Deferred during Phase 6c (merge math; commit→Phase 9)

merge math builds over plain claim inputs in 6c; the two-parent storage commit +
Repository/family-registry materialization need the Phase-9 Repository/snapshot
facade (quire GitStore has commit_flat_tree but no propstore Repository binds
git+families yet):
- test_repo_merge_object.py -> 9 (two-parent merge_commit + Repository)
- test_merge_cli.py -> 9/10 (merge CLI over Repository)
- test_merge_symmetry_non_claim_files.py -> 9 (non-claim-file merge over git trees)

belief-set / worldline IC-merge (model-theoretic IC merge, layer 4 — distinct
from the merge-side IntegrityConstraint built in 6c):
- test_ic_postulate_coverage.py -> 7 (belief_set.ic_merge)
- test_assignment_selection_merge.py -> 7 (world.assignment_selection_merge)
- test_revision_merge_uses_ic_merge.py / test_worldline_ic_merge*.py -> 7

## Deferred during Phase 5b (commits 8e9a10a8, bbe56d71)

5b built the ASPIC+ kernel bridge + PrAF value layer + source-trust + CKR
(empty-bundle). It deferred the store→AF *assembly* (core/analyzers, claim_graph,
praf.build_praf, aspic_bridge/projection) because the reference builds those over
`propstore.conflict_detector` (Phase 6) + `propstore.world.types` /
active-claim-graph (Phase 7) — building them now needs phantom WorldStore/
conflict_detector or a parallel mirror. They land WITH Phase 6/7.

Moved deliverables (PLAN updated): core/analyzers.py (Dung-AF + PrAF assembly over
the active claim graph), claim_graph.py, praf.build_praf, aspic_bridge/projection.py
(csaf_to_projection -> StructuredProjection), and the gunray-inspection -> ASPIC+
GroundedDatalogTheory seam for NON-empty bundles (currently NotImplementedError +
HIGH gap docs/gaps.md:18).

Tests deferred to their owning phase:
- test_core_analyzers.py -> 6/7 (analyzers/SharedAnalyzerInput + conflict synthesis)
- test_praf_integration.py -> 6/7 (analyzers/build_praf)
- test_praf_uncalibrated_explicit.py -> 6/7 (analyzers/build_praf)
- test_argumentation_integration.py -> 6/7 (SQLiteArgumentationStore/conflict_detector)
- test_core_justifications.py -> 6/7 (active claim graph)
- test_ws_f_aspic_bridge.py (lifting/projection/Label subset) -> 6/7 (StructuredProjection/Label)
- test_aspic_bridge_grounded.py -> 6 (non-empty grounding seam; gates the gaps.md:18 follow-up)
- test_justification_rule_kind_validated.py -> 8 (cli/source)
- test_praf_argument_enumeration_budget.py -> 7 (gunray budget; was a skipped stub in the reference too)

## Phase 6d (concept alignment + sameas + relation-concept identity)

6d built the alignment MATH over plain inputs (proposal-only, never source
mutation): `source/alignment.py` (classify_relation by lemon identity,
build_alignment_artifact over a PartialArgumentationFramework, repo-free
load/save), the `families/alignment.py` ConceptAlignmentArtifact charter, the
`families/sameas.py` SameAs charter, and the `core/relations.py`
relation-concept-identity kernel.

PORTed in 6d (now green, removed from the deferred set above):
- test_relation_concept_identity.py -> tests/test_relation_concept_identity.py
  (was deferred to 6/10 at line 18; the kernel landed in 6d).
- test_alignment_default_classification.py -> folded into
  tests/test_alignment_classification.py (classify_relation + artifact + codec).
- test_sameas_family_schema.py -> rewritten to charter shape as
  tests/test_sameas_charter.py (no PROPSTORE_FAMILY_REGISTRY / DocumentStruct /
  to_payload in the rewrite; the family name + columns fall out of the charter).

Superseded (NOT ported): test_relation_analysis.py — the reference's store-based
`stance_summary(store, active_ids) -> dict` is replaced by
`families.relations.stance_summary(Iterable[Stance]) -> StanceSummary`, already
covered by tests/test_relations_charter.py
(test_stance_summary_counts_attacks_without_pruning).

Deferred to Phase 8 (source subsystem: Repository / source branches / CLI):
- test_concept_alignment_cli.py -> 8 (alignment CLI over a Repository)
- test_source_promotion_alignment.py -> 8 (align_sources/decide/promote_alignment)
- test_source_relations.py -> 8 (already listed above; source-relation projection)
