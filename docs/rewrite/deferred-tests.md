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
- test_sidecar_relation_edge_projection.py -> SUPERSEDED in 9-3 (no concept-to-concept
  relation_edge family in the charter rewrite; relation edges derive from stances —
  the reference relation_edge projection VANISHES; see the Phase 9-3 section)
- test_sidecar_calibration_counts_projection.py -> 10 (families.calibration sidecar; calibration extract)
- test_opinion_schema.py -> 9/10 (opinion sidecar/schema projection)
- test_render_policy_opinions.py -> 10 (render policy)
- test_prior_base_rate_is_opinion.py -> 7 (base-rate resolution against a store)
- test_claim_and_stance_document_enums.py -> 9/10 (families.documents surface — 5b reconfirmed)

## Deferred during Phase 6c (merge math; commit→Phase 9)

merge math builds over plain claim inputs in 6c; the two-parent storage commit +
Repository/family-registry materialization need the Phase-9 Repository/snapshot
facade (quire GitStore has commit_flat_tree but no propstore Repository binds
git+families yet):
- test_repo_merge_object.py -> CLOSED in 9-2 (two-parent create_merge_commit +
  build_repository_merge_framework over Repository; charter-native translation —
  rivals materialized under distinct assertion ids, MergeManifest charter)
- test_merge_cli.py -> 10 (merge CLI over Repository; still deferred — CLI adapter)
- test_merge_symmetry_non_claim_files.py -> CLOSED in 9-2 (non-claim-file merge over
  git trees; NonClaimMergeConflict surfaced symmetrically over concept documents)

belief-set / worldline IC-merge (model-theoretic IC merge, layer 4 — distinct
from the merge-side IntegrityConstraint built in 6c):
- test_ic_postulate_coverage.py -> CLOSED in 9-2 (propstore.merge merge-framework
  IntegrityConstraint over a real Repository-backed merge — forbidden pruning,
  required-survival, violation; merge-side IC, NOT belief_set.ic_merge / support_revision)
- test_assignment_selection_merge.py -> 7 (world.assignment_selection_merge)
- test_worldline_ic_merge*.py -> 7b-4 (belief_set IC merge over a captured
  worldline epistemic state). test_revision_merge_uses_ic_merge.py PORTed in 7b-1.

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
- test_aspic_bridge_grounded.py -> 6 (non-empty grounding seam; gates the gaps.md:18 follow-up)
- test_justification_rule_kind_validated.py -> 8 (cli/source)

PORTed in Phase 7a-world-A (store->graph->AF assembly; now green, removed above):
- test_core_analyzers.py + test_argumentation_integration.py (store-based
  shared_analyzer_input_from_store / analyze_claim_graph / build_argumentation_framework /
  compute_claim_graph_justified_claims + conflict-stance synthesis) -> folded into
  tests/test_world_store_assembly.py over the in-memory compiled-graph feed
  (tests/world_store_feed.py); the reference SQLiteArgumentationStore/conftest dict
  store is replaced by the charter/compiled-graph WorldStore feed.
- test_praf_integration.py (build_praf deterministic/uncertain/no-stances +
  analyze_praf metadata + paper-td routing) -> tests/test_world_store_assembly.py.
  The reference resolve()/RenderPolicy/ValueResult slice stays deferred to
  7a-world-C (render policy + resolution).
- test_praf_uncalibrated_explicit.py -> tests/test_praf_uncalibrated_explicit.py.
- test_core_justifications.py -> tests/test_core_justifications.py (charter feed +
  build_compiled_world_graph + activate_compiled_world_graph + claim_justifications_from_active_graph).
- test_ws_f_aspic_bridge.py (analyzer slice: SharedAnalyzerInput.active_graph +
  analyze_praf paper-td + build_aspic_projection store path) -> covered by
  tests/test_world_store_assembly.py. The bridge-math slice already passes in
  tests/test_*_aspic*/structured_projection; the app/ContextReference slice stays
  for the app/lifting phase.
- test_praf_argument_enumeration_budget.py -> tests/test_praf_argument_enumeration_budget.py
  (skip stub; unskips when propstore consumes the gunray enumeration budget).

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
- test_concept_alignment_cli.py -> 10 (alignment CLI over a Repository; owner-layer
  align/decide/promote landed in 8-4, only the Click surface remains)
- test_source_promotion_alignment.py -> LANDED in 8-4 as
  tests/test_concept_alignment_promotion.py (align_sources/decide_alignment/
  promote_alignment over the Repository facade); the source-promote half of that
  reference file is covered by tests/test_source_promote_p83b.py, and its CLI
  assertions are Phase 10.
- test_source_relations.py -> 8 (already listed above; source-relation projection)

Phase 8-4 predicate proposals (landed) and their deferred edges:
- test_proposal_predicates_family.py -> LANDED-equivalent in
  tests/test_predicate_proposals.py (charter registration + address path +
  PredicateDeclaration arg-type/arity validation, over the rewrite charter rather
  than a families/documents/predicates DocumentStruct).
- test_promote_predicates_proposals.py -> owner-layer promote/plan/idempotency/
  conflict landed in tests/test_predicate_proposals.py, seeding via
  propose_predicates (the recorder). The LLM-seeded variant
  (propstore.heuristic.predicate_extraction._llm_call / propose_predicates_for_paper)
  and the app conflict layer (app.predicates.PredicateWorkflowError) stay deferred
  to the heuristic (Phase 6) and app/CLI (Phase 10) phases.
- test_propose_predicates_lifecycle.py -> 6 (LLM extraction heuristic + dry-run).
- test_promote_rules_proposals.py / test_proposal_rules_family.py /
  test_propose_rules_lifecycle.py -> 8-4 (rule proposals, sibling of predicates) or
  later; rule-proposal promotion not yet built.
- test_proposal_promotion.py / test_promote_stance_proposals_idempotency.py /
  test_plan_stance_proposal_promotion_typo_path.py -> owner-layer stance proposal
  record/plan/promote landed in tests/test_stance_proposals.py. The rewrite Stance
  charter diverges from the reference StanceDocument, so the stance proposal is its
  own charter and idempotency rides on the content-derived stance_id rather than a
  promoted_from_sha stamp. The reference's NLI/LLM commit_stance_proposals batch
  recorder and the CLI promote surface stay deferred to Phase 6 / Phase 10.
- test_cli_promote_rules_*.py / test_cli_propose_rules_*.py /
  test_concept_alignment_cli.py -> 10 (Click surface only).

## Phase 7a-world-B2 (BoundWorld + ATMS engine; commit f8ad6fe1 + follow-up)

B2 ported `world/bound.py` (BoundWorld) + `world/atms.py` (ATMSEngine) onto the
charters and the carved provenance-semiring label algebra. The reference ATMS
suite is row/dict-based and pulls in CLI / worldline / app-layer / sidecar paths;
the engine *behaviour* is re-covered charter-natively over the in-memory feed
`tests/atms_feed.py`.

PORTed in 7a-world-B2 (now green):
- tests/test_atms_engine.py — charter-native core: exact-support propagation
  (TRUE/IN/OUT + support quality), value-label attach, conflict→nogood pruning
  (NOGOOD_PRUNED), parameterization-derived support, derived-vs-derived
  contradiction → nogood, bounded future replay (could_become_in), stability,
  relevance, interventions + next-queryables, explain_node/explain_nogood/
  verify_labels, claims_in_environment, micropublication support, environment/
  context serialisation split, future-budget exhaustion, argumentation_state.
- tests/test_atms_derived_contradictions.py — charter port.
- tests/test_atms_cel_semantic_equality.py — charter port (CEL-equivalent
  antecedent matching).

PORTed in 7a-world-B2 COVERAGE follow-up (now green over `tests/atms_feed.py`):
- tests/test_atms_propagation_nogood_interleave.py — `_build` interleaves the
  nogood update before propagation observes final labels (source-level E.M3).
- tests/test_atms_consequent_field_discipline.py — one `consequent_id` field; the
  dead multi-consequent surface stays deleted (source-level E.M2).
- tests/test_atms_max_iterations_anytime.py — bounded build returns partial
  fixpoint state (`fixpoint_reached`/`iterations_run`/`warnings`), not an
  exception (E.M1).
- tests/test_atms_unbounded_stability_api.py — unbounded stability finds the
  flipping witness; `limit` is a required keyword; `BudgetExhausted(examined,
  total)` is loud + counted; AST gate on propstore call sites; monotone-budget
  property (E.H1a/b/c, Codex 2.9).
- tests/test_atms_was_pruned_by_nogood_cycle.py — a cycle whose external SCC
  support is a nogood is `NOGOOD_PRUNED`, not `MISSING_SUPPORT` (de Kleer p.146,
  E.H2).
- tests/test_provenance_atms_equivalence.py — rewrite-native: the propstore
  `core.labels` door IS the carved `provenance_semiring` algebra (no
  `label_to_polynomial`/`polynomial_to_label` mirror); `combine_labels` /
  `merge_labels` / `NogoodSet` pruning equal polynomial product / sum / `live`,
  and assumption-vs-context variable meaning survives projection.

Deferred (reference test files whose remaining surface is not B2's):
- test_atms_engine.py CLI / `app.world_atms` / worldline paths -> 10 (CLI/web) /
  7b (worldline).
- test_atms_categorical_provider_visibility.py -> ported as a SKIP
  (`tests/test_atms_categorical_provider_visibility.py`,
  `@pytest.mark.skip`). The engine behaviour (a categorical parameterization
  input surfaced as a visible OUT `ATMSDerivedNode` with
  `PARAMETERIZATION_INPUT_TYPE_INCOMPATIBLE`) is implemented, but it needs a
  categorical *claim value* the float-only `Claim.value` charter cannot hold.
  Tracked in docs/gaps.md (HIGH, categorical-provider entry); unskip after the
  Claim charter carries categorical/boolean values.
- test_micropub_identity_consumes_wscm.py -> 8 (source/document subsystem). This
  is a *document-identity* test (trusty `ni:///sha-256` URIs over
  `propstore.families.documents.micropubs.MicropublicationDocument` +
  `propstore.families.identity.micropubs` + `propstore.provenance.trusty`), none
  of which exist yet — it is not an ATMS-engine test. The engine's
  micropublication *support* node behaviour is already covered by
  `tests/test_atms_engine.py::test_micropublication_node_supported_when_claims_and_context_supported`.
  Port when the Phase-8 source/document/trusty-identity infra lands.
- test_world_bound_conflicts_cache.py -> 9 (its fixtures import the repo-backed
  `tests.test_world_query` `world` fixture; the in-memory cases use row-dict
  stores rather than charters). The cache itself (`conflict_inputs_for_store`
  built once per BoundWorld) is implemented and exercised by the conflict path.
- BoundWorld revision surface (expand/contract/revise/iterated/epistemic) -> 7b
  (support_revision); the seam is marked in `world/bound.py`.

## Phase 7a-world-C3 (WorldQuery glue + OverlayWorld + consistency; this commit)

C3 built the render-time query glue (`world/model.py` — bind / active_graph /
compiled_graph / intervene / observe / chain_query as free functions over the
`WorldStore` protocol), `world/overlay.py` (charter-native OverlayWorld +
`_GraphOverlayStore`), `world/consistency.py`, and the `world/__init__` render
re-export surface. The reference `WorldQuery` tests are sqlite/sidecar-backed; the
glue *behaviour* is re-covered charter-natively over `tests/atms_feed.py`.

PORTed in 7a-world-C3 (now green):
- tests/test_world_model_glue.py — bind / active_graph / compiled_graph /
  chain_query (derive / unresolved-conflict / strategy-resolve) / intervene /
  observe over the in-memory feed (translates the reference
  test_world_query.py bind/chain/intervene/observe/active_graph/compiled_graph
  cases off the repo fixture).
- tests/test_overlay_world.py — add / replace / remove / diff / parameterization
  preservation / recompute_conflicts (translates the reference overlay cases).
- tests/test_world_consistency.py — direct-conflict report + JSON-ready view.
- tests/test_chain_query_enum_discipline.py — AST: chain_query compares
  ValueStatus by identity (copied; works over `world/model.py`).
- tests/test_overlay_world_renamed.py — AST: no `HypotheticalWorld` surface +
  `propstore.OverlayWorld` export + disclaimer docstring (copied).

Deferred (reference surface not built in C3):
- test_world_query.py sidecar-build / historical / embedding / similar /
  build-diagnostics / form-algebra / grounding / schema-validation cases -> 9
  (concrete repo-backed `WorldQuery` reader: `__init__`/`from_path`/`select_*`/
  sqlite-vec/`materialize_world_sidecar`). The Phase-9 reader satisfies the
  `WorldStore` protocol and reuses the `world/model.py` glue.
- test_world_model_resolve_cache.py, test_world_model_branch_column_required.py
  -> 9 (sqlite reader caching / branch column).
- test_world_query_at_journal_step.py, test_world_query_at_journal_step_method.py
  -> 8 (`at_journal_step` / `bind_for_view` / `_BoundView` / `ClaimView` —
  support_revision journal/worldline bridge).

## Deferred during Phase 7a-worldline

7a-worldline built the worldline materialization core (definition / runner /
resolution / argumentation / hashing / result_types / revision_types data
shapes) + observatory over the in-memory `WorldlineStore` feed. Revision/
sensitivity *capture* and the concrete repo-backed store land later:

Closed in 7b-4 (see "## Phase 7b-4" below):
- test_worldline_hash_repr_typed_failure.py, test_capture_journal.py (in-memory
  capture cases; document/CLI cases stay deferred),
  test_worldline_error_visibility.py::test_sensitivity_failure_produces_error_indicator,
  test_worldline_revision.py, test_worldline_revision_event_capture.py,
  test_worldline_revision_properties.py,
  test_worldline_revision_snapshot_boundary.py, test_worldline_ic_merge.py,
  test_worldline_ic_merge_properties.py, test_worldline_ic_merge_realization.py.

Closed in 9-2 (now that the two-parent merge DAG exists):
- test_worldline_revision_merge_parent_evidence.py -> CLOSED in 9-2
  (`create_merge_commit` produces the real two-parent merge DAG;
  `project_belief_base` threads `commit_parent_shas` into
  `RevisionScope.merge_parent_commits`).

Deferred to Phase 9 (need a concrete repo-backed WorldStore beyond the
in-memory feed; the reference fakes are pre-charter dict-shaped):
- test_worldline.py -> 9 (Repository / GitStore / CLI / family_helpers /
  conftest fixtures).
- test_worldline_properties.py -> 9 (family_helpers.materialized_world_store_path).
- test_worldline_praf.py -> 9 (full store->AF PRAF path over a charter-shaped
  store feed; reference FakeWorld returns pre-charter dict claims/stances).

Observatory CLI/doc cases (test_observatory.py
test_observatory_cli_adapter_builds_typed_app_request /
test_root_cli_registers_observatory_lazily /
test_epistemic_os_documentation_maps_artifact_to_journal) -> CLI/docs phase; the
owner-layer report-builder cases are ported and green.

## Phase 7b-1 (support_revision core)

7b-1 built the `support_revision/` support-incision package (L0-L7 + explain):
explanation_types, scope_policy, state, belief_set_adapter (the sole belief_set
contact point), input_normalization, entrenchment, realization, snapshot_types,
history, iterated, dispatch, explain. belief_set is consumed directly (now
py.typed) with no propstore mirror; support_revision.BeliefBase stays distinct
from belief_set.BeliefBase.

PORTed in 7b-1 (now green), translated to the structural situated-assertion
helper (`tests/support_revision/revision_assertion_helpers.make_assertion_atom`
builds a `SituatedAssertion` via `core.assertions`, not `projection`):
- test_revision_operators.py, test_revision_iterated.py,
  test_revision_adapter_budget.py, test_revision_adapter_expand_contract_revise.py,
  test_revision_adapter_iterated.py, test_revision_iterated_examples.py,
  test_revision_properties.py, test_revision_entrenchment.py,
  test_revision_formal_entrenchment_boundary.py, test_revision_explain.py,
  test_revision_event_contract.py, test_revision_formal_decision_reports.py,
  test_iterated_revision_recomputes_entrenchment.py,
  test_revision_merge_uses_ic_merge.py, test_revision_policy_provenance.py
  (the last inlines `TransitionJournalEntry.from_states` rather than the
  charter-heavy `tests.fixtures.journal` fixture).

Deferred past 7b-1:
- test_revision_retirement.py -> 7b-4 (reads
  `propstore/worldline/revision_capture.py`, which lands in 7b-4).

## Phase 7b-2 (projection + af_adapter + workflows + BoundWorld re-attach)

7b-2 built `support_revision/{projection,af_adapter,workflows}` and re-attached the
BoundWorld revision surface (revision_base / revision_entrenchment / expand /
contract / revise / revision_explain / epistemic_state / revision_state_snapshot /
iterated_revise + the two free helpers). `projection.py` retypes the situated-
assertion build over the slim charter `ActiveClaim` (value/claim_type ride in
`attributes`; conditions are not on the thin claim view, so the projected
assertion is unconditional — the condition's belief effect is already in the
support sets / essential support). `af_adapter.py` retypes the read-only overlay
over the charter `Claim`/`Stance`/`ConflictRecord` and `core.environment` store
protocols (no `*Row`/`*RowInput`). belief_set stays confined to
`belief_set_adapter.py`.

PORTed in 7b-2 (now green), `_RevisionStore`/`_make_bound` replaced by the
charter-native `tests.atms_feed.build_bound` / `ClaimSpec`:
- test_revision_projection.py, test_revision_state.py,
  test_revision_assertion_identity.py (the two 7b-1-deferred rows above),
  test_revision_bound_world.py (carries `_operator_bound`/`_atom_id_for_claim` +
  the entrenchment-override case from the reference test_revision_phase1.py),
  test_revision_adapter_projection.py, test_revision_argumentation_views.py.
- test_revision_af_adapter.py: the structured-projection (`build_aspic_projection`
  over the revision overlay + support metadata) case and the import-discipline AST
  case are ported. The `build_argumentation_framework`-over-the-overlay case
  (`test_project_epistemic_state_builds_claim_graph_inputs_over_accepted_claims`)
  is NOT ported: it asserts the overlay store returns a synthetic accepted claim
  (`claim_synthetic`) with `.value == 9.0`, which the slim charter `ActiveClaim`
  cannot carry (the value lives in the situated assertion, not the claim) — it
  needs a charter-Claim synthesis from the accepted assertion. Deferred until the
  revision overlay can materialize charter claims for synthetic atoms.

Deferred past 7b-2 (CLI/web phase):
- test_revision_cli.py, test_revision_phase1_cli.py, test_revision_app_contract.py,
  test_web_revision_readonly.py -> CLI/web phase (Click/app surface over the
  workflows owner layer).

## Phase 7b-3 (fragility / sensitivity intervention-ranking)

PORTed in 7b-3 (now green), `tests/test_fragility.py` (26 passed / 3 skipped):
- TestInterventionModel, TestUtilityScores, TestATMSInterventions,
  TestMissingMeasurementInterventions, TestConflictInterventions,
  TestInteractions, TestRankFragility — all ported. Retyped over the rewrite
  surface: the semiring value objects import from `provenance_semiring` (not the
  reference `propstore.provenance`, which keeps only the lemon
  `Provenance`/`ProvenanceStatus`); `ProvenanceNogood` is the two-argument
  `(variables, witness)` form; parameterization mocks return
  `core.graph_types.ParameterizationEdge` (the charter type `all_parameterizations`
  yields) instead of the reference row dicts; the world mocks use the public
  `store` / `active_graph` properties (`FragilityWorld` exposes those, not a
  private `_store`); the conflict AF reader is
  `core.analyzers.shared_analyzer_input_from_graph`.
- `imps_rev` retyped to take `propstore.opinion_provenance.OpinionWithProvenance`
  (the canonical provenance-paired opinion; `doxa.Opinion` is provenance-free).
  `test_imps_rev_uses_supplied_opinions_without_fabricating_certainty` is ported
  with `OpinionWithProvenance` inputs and the dfquad monkeypatch retargeted to
  `argumentation.gradual.dfquad.dfquad_strengths`. `opinion_sensitivity` is
  re-exported from `doxa` (doxa lifted it from propstore), not re-implemented.

DROPPED in 7b-3:
- `test_imps_rev_rejects_unprovenanced_opinions` — its premise (passing a
  provenance-free `Opinion`) is now enforced by the `OpinionWithProvenance`
  parameter type rather than a runtime "provenance-bearing" check, so the runtime
  rejection path no longer exists.

SKIPPED in 7b-3 (deferred — see `docs/gaps.md` MED grounding/bridge entry):
- TestGroundFactInterventions, TestGroundedRuleInterventions,
  TestBridgeUndercutInterventions — the grounding/bridge families need the
  rule-authoring document surface `propstore.families.documents.rules` to author a
  non-empty grounded bundle, plus the gunray complement encoder
  `propstore.grounding.gunray_complement.GUNRAY_COMPLEMENT_ENCODER` /
  `aspic_bridge.grounding._decode_grounded_predicate`; none are present in the
  rewrite substrate. The collectors are implemented and importable (no-complement
  decode), but cannot be driven end-to-end until that surface lands.

The fragility-driven worldline sensitivity-capture case
(`test_worldline_error_visibility.py::test_sensitivity_failure_produces_error_indicator`)
and `epistemic_process` cases remain owed to Phase 7b-4.

## Phase 7b-4 (worldline revision tail + epistemic_process)

7b-4 built `propstore/worldline/revision_capture.py`
(`capture_revision_state` / `capture_journal` over the re-attached BoundWorld
revision surface), re-wired `worldline/runner.py` (both seams:
`_capture_sensitivity` -> `propstore.sensitivity.analyze_sensitivity`, and
`definition.revision` -> `capture_revision_state`; the content hash now lowers the
render policy through `policies.policy_profile_from_render_policy`), added the
`event: RevisionEvent | None` field to `worldline/revision_types.WorldlineRevisionState`,
and built `propstore/epistemic_process.py` (JobKind / InvestigationPlan /
InterventionPlan / plan_fragility_investigation / ProcessJob / QueuedProcessJob /
ProcessCompletionRecord / ProcessReplayReport / EpistemicProcessManager).
`plan_fragility_investigation` takes a `core.environment.WorldStore` (the rewrite
has no `WorldQuery` type). belief_set stays confined to `belief_set_adapter.py`.

PORTed in 7b-4 (now green):
- test_worldline_revision.py, test_worldline_revision_event_capture.py,
  test_worldline_revision_properties.py,
  test_worldline_revision_snapshot_boundary.py, test_worldline_ic_merge.py,
  test_worldline_ic_merge_properties.py, test_worldline_ic_merge_realization.py,
  test_worldline_hash_repr_typed_failure.py, test_epistemic_process_manager.py,
  test_epistemic_history.py, test_epistemic_snapshot_detaches_state.py,
  test_revision_retirement.py (paths trimmed to surfaces that exist in the
  rewrite — `cli/compiler_cmds.py` is not present yet),
  test_worldline_error_visibility.py::test_sensitivity_failure_produces_error_indicator
  (skip removed). `tests/fixtures/journal.py` was ported, translated off the
  deleted `ClaimRow`/`ActiveClaim.from_claim_row` onto `coerce_active_claim`;
  the Mara-Jade / SyntheticBeliefSpace `bind_for_view` fixtures (Phase-8
  `at_journal_step` only) were not carried over.

PORTed partially (in-memory capture only) in 7b-4:
- test_capture_journal.py — the `capture_journal` determinism / replay-vs-direct-
  dispatch / revise-revise-contract / expand-operator cases are ported and green.
  The document-codec roundtrip cases (need
  `families.documents.worldlines.WorldlineDefinitionDocument` +
  `WorldlineDefinition.journal` / `to_document`), the
  `worldline_build_journal` / `worldline_at_step` CLI cases (need
  `propstore.cli.worldline.journal` + `propstore.app.worldlines`), and the
  `at_journal_step` case (Phase 8) are NOT ported — those surfaces are not in the
  rewrite yet.

Closed in 9-2:
- test_worldline_revision_merge_parent_evidence.py -> CLOSED in 9-2 (real git merge
  DAG via `create_merge_commit`; `RevisionScope.merge_parent_commits` populated).

## Phase 8-0 — Repository facade + charter-derived family registry

Landed (rewrite): the charter-derived `PROPSTORE_FAMILY_REGISTRY` + foreign-key
graph (quire `registry_from_charters`; FK specs live only on charter fields), the
`Repository` facade (`git` / `require_git` / `families` / `snapshot` /
`derived_stores` / `config` / `uri_authority` / `tree` / `mutation_guard` /
`find` / `init` / `is_propstore_repo`), `storage/` package (git policy +
`RepositorySnapshot` + the concept sidecar builder), `canonical_namespaces`, and
the `micropublication` + `justification` family charters. The PLAN.md §12.6
charter→FK spike is proven on both hardest families: lemon (`concept` →
`form`) and `micropublication` (→ `context`, `claim`). Tests written:
`test_semantic_family_registry`, `test_repository`, `test_canonical_namespaces`,
`test_git_policy`, plus quire `test_registry_from_charters`.

Deferred to later slices (charters/logic land WITH their owning slice):
- The source-branch family charters (`source_documents`, `source_concepts`,
  `source_claims`, `source_micropubs`, `source_justifications`, `source_stances`,
  `source_notes`, `source_metadata`, `source_finalize_reports`) and the canonical
  `source` family, plus the proposal families (`proposal_stances`,
  `proposal_predicates`, `proposal_rules`, `concept_alignments`) and
  `merge_manifests` → authored alongside the **8-2 / 8-3 / Phase-9** logic that
  uses them (e.g. the ~40-field source-claim document is source-authoring shape).
- `artifact_codes` (`stamp_source_artifact_codes`, `claim_artifact_code`, …) →
  **8-3**: it depends on the claim/concept identity canonicalizers
  (`canonicalize_claim_for_version`, `derive_*_artifact_id`,
  `compute_*_version_id`) which do not exist in the rewrite yet (the rewrite uses
  the `identity_field` value directly as the store key). Those identity
  canonicalizers are **8-1 / 8-3** work.
- The transactional multi-family write path is available now as quire
  `GitStore.head_bound_transaction(branch).families_transact(repo.families,
  message=...)` → `txn.<family>.save(ref, doc)` → `txn.commit_sha`; source
  finalize/promote (8-3) consume it directly (no propstore wrapper needed).

## Phase 8-1 — provenance named-graph carrier + identity + PROV-O

Landed (rewrite): `propstore/provenance.py` became the `propstore/provenance/`
package. The one canonical `Provenance` struct gained `graph_name` +
`derived_from`; `compose_provenance` is now variadic with status-max fusion
(`_STATUS_RANK` keeps the weakest honest status visible after fusion) and causal
operation-order preservation. New carrier: `encode_named_graph` /
`decode_named_graph` (deterministic JSON-LD `NamedGraph`, Carroll 2005) +
`write_provenance_note` / `read_provenance_note` over quire
`refs/notes/provenance` (provenance is a git note keyed by object sha — never in
the claim/artifact blob). New submodules `provenance/records.py` (the six typed
records + `ExternalStatementAttitude`, the single `ProjectionFrameProvenanceRecord`
spelling — the duplicate msgspec one was deleted), `provenance/prov_o.py` (PROV-O
JSON-LD export), `provenance/trusty.py` (ni-URI re-export). `propstore/uri.py`
gained the RFC 6920 ni-URI byte primitives (`compute_ni_uri` / `verify_ni_uri` /
`ni_uri_for_bytes` / `ni_uri_for_file`) + `source_tag_uri` / `claim_tag_uri`.
Tests ported (now green): `test_compose_provenance_causal_order` (the PLAN-level
7a-causal deferral — closed), `test_provenance` (stamp), `test_provenance_records`,
`test_prov_o_export`, `test_trusty_uri_verification`, `test_uri`,
`test_uri_authority_validation`, and `test_named_graph` (the named-graph carrier
subset of the reference `test_provenance_foundations`).

Deferred:
- The opinion-fusion + family-document cases of the reference
  `test_provenance_foundations` (`propstore.opinion`,
  `propstore.families.claims.documents`, `propstore.families.documents.sources`)
  → their owning **opinion / families-document** slices; the provenance carrier
  cases are ported in `test_named_graph`.
- The claim/concept **identity canonicalizers** (`canonicalize_claim_for_version`,
  `compute_claim_version_id`, `derive_claim_artifact_id`,
  `derive_concept_artifact_id`, `compute_concept_version_id`) and
  `artifact_codes.py` → **8-3**. The reference implementations operate on the
  pre-charter dict payload shape and need the source-claim document shape +
  promote-time immutable-rebuild semantics (`families/claims/documents`,
  `families/documents/sources`, `families/identity/*`) that are 8-2/8-3
  source-authoring surfaces — not the pure identity layer 8-1 owns. The genuinely
  pure identity primitives (ni-URI byte carrier + trusty) landed here.

## Phase 8-2 — source-branch authoring (commits 8-2a / 8-2b)

Landed the source-branch authoring subsystem over the 8-0 Repository facade:
`families/sources.py` (the five source family charters — `SourceDocument`,
`SourceConceptsDocument`, `SourceClaimsDocument` with the ~40-field
`SourceClaimDocument`, `SourceStancesDocument`, `SourceJustificationsDocument` —
plus their nested structs, the `SOURCE_BRANCH` placement and `SourceRef`),
`families/identity/{logical_ids,claims}.py` (the CLAIM-side identity primitives
pulled forward to their canonical home: `derive_claim_artifact_id`,
`compute_claim_version_id`, `canonicalize_claim_for_version`,
`normalize_logical_value`), and `source/{common,concepts,claims,relations,
reference_indexes,claim_concepts,stages}.py`. Reference lowering (source-local
handle → canonical claim id) goes through quire's `FamilyReferenceIndex`, not
string munging; the reserved-namespace guard and the CEL (condition_ir) +
value-bound (form registry) guards run at the authoring edge.

Tests ported (now green) in `tests/test_source_authoring_p82.py` (owner-API over
`Repository.init`, translated from the CLI-driven reference suites
`test_source_propose` / `test_source_claims` / `test_source_relations` /
`test_source_cannot_mint_canonical_ids` / `test_source_claim_concept_rewrite` /
`test_local_handle_collision_blocks_commit`): init + manifest, concept proposal +
form validation + master linking, claim identity stamping, reserved-namespace
guard, unknown-concept guard, value-bound guard, stance/justification reference
lowering + validation, `resolve_source_or_primary_claim_id`, local-handle
collision (AmbiguousReferenceError), and `rewrite_claim_concept_refs`.

Deferred:
- `SourcePromotionPlan` (source/stages.py) and the import/promote claim
  normalizers (`normalize_imported_claim_artifact` /
  `normalize_promoted_source_claim_artifact`, formerly in claim_concepts.py) →
  **8-3 / 8-5**: they build the *canonical* `ClaimDocument`/`ConceptDocument`
  charters that do not exist yet. The pure source-local concept rewrite
  (`rewrite_claim_concept_refs`) landed here.
- The opinion-typed source fields (`SourceTrustDocument.prior_base_rate`,
  `ResolutionDocument.opinion`) → **8-3**: `doxa.Opinion` is the only Opinion and
  is not a msgspec struct, so these are added with promote-time trust calibration
  rather than mirrored into a second Opinion spelling. Source authoring only sets
  `trust.status = DEFAULTED`.
- `source/finalize.py`, `source/promote.py`, `source/registry.py`,
  `source/status.py`, `source/passes.py`, and the `source_micropubs` /
  `source_finalize_reports` families → **8-3 / 8-5** (finalize / promote /
  micropublications / import). The CLI-status reference tests
  (`test_cli_source_status`, `test_source_list_and_context`) need those surfaces.
- The CEL/value-bound negative cases that require the full Phase-9 compilation
  context (`build_compilation_context_from_repo`) — the 8-2 guards reimplement the
  concept-kind registry directly from the repo's concept + form families, which
  covers the authoring-edge cases; the compiler-backed paths remain Phase 9.

## Phase 8-3a (finalize + micropublication compose + artifact codes)

8-3a built `propstore/artifact_codes.py` (`stamp_source_artifact_codes` and the
source/justification/stance/claim content-code helpers), the `source_micropubs`
+ `source_finalize_reports` family charters (`SourceMicropublicationsDocument`,
`SourceFinalizeReportDocument`, plus the `SourceMicropublicationDocument` bundle
struct — FK-free on the source branch, reusing the canonical
`MicropublicationEvidence`), `families/identity/micropubs.py` (the `ni:` trusty
URI + content-version identity over a micropub bundle), and `source/finalize.py`
(`finalize_source_branch`: micropub-coverage + reference-integrity preconditions,
artifact-code stamping, Clark micropublication composition, and the
`SourceFinalizeReportDocument`, all written atomically via
`git.head_bound_transaction(branch).families_transact`).

Tests ported (now green) in `tests/test_source_finalize_p83a.py` (owner-API over
`Repository.init`, translated from the CLI-/`*Document`-driven reference suites
`test_finalize_micropub_required`, `test_micropub_identity_trusty_uri`,
`test_micropub_identity_not_logical_handle`, `test_micropub_trusty_verification`,
`test_artifact_identity_policy`): finalize blocks an uncontexted claim and writes
no micropub file; ready finalize stamps codes + composes bundles with `ni:`
identity; empty-claim finalize is ready/empty; calibration fallback without
derived priors; reference-integrity blocks (dangling justification premise,
unresolved stance target); micropub trusty-URI determinism + claim-order
insensitivity + byte-exact `verify_ni_uri`; artifact-code determinism,
content-sensitivity, recursive-field exclusion, and relation-code folding.

Deferred:
- `test_micropubs.py` -> **9** (render/app surface: `propstore.app.micropubs`
  `find/list/inspect_micropub_lift` + the `micropub list/show/lift` CLI).
- `test_micropub_identity_dedupe_shape.py`,
  `test_micropublications_phase4.py`,
  `test_micropub_identity_consumes_wscm.py` -> **CLOSED 9-5** (sidecar
  projection). In the rewrite the per-family `populate_micropublications` /
  `MicropublicationProjectionRow` mass VANISHES into the generic charter
  projection; the WS-CM payload-identity dedupe folds into
  `propstore.derived_build._project_documents` (first-writer-wins on the charter
  identity field — a micropub's `artifact_id` is the `ni:` content URI). Covered
  by `tests/test_micropub_sidecar_dedupe.py`
  (`test_identical_payload_micropubs_dedupe_to_one_row`, driven end-to-end through
  `build_repository`). The trusty-URI + `verify_ni_uri` content-id consumption
  that `test_micropub_identity_consumes_wscm` asserted is already covered by the
  8-3a `tests/test_source_finalize_p83a.py` micropub identity cases. The
  `test_micropublications_phase4` CLI/source-promote/ATMS-node parts remain
  Phase-10 (render/app + `pks` adapters); the empty-bundle validation is the
  charter's required-`claims` field.
- The `merge/finalize` per-source report *path* and the CLI-driven
  `source finalize` invocation -> **9** (CLI adapter); 8-3a writes the report to
  the fixed-file `finalize-report.yaml` placement on the source branch and is
  driven through the owner function.
- `parameterization_group_merges` on the finalize report is left empty in 8-3a;
  `preview_source_parameterization_group_merges` (`source/registry.py`) lands in
  **8-3b** with promote.

## Phase 8-3b — source-branch promote + trust calibration (DONE)

8-3b built `source/promote.py` (`promote_source_branch`: load finalize report →
resolve source concepts to canonical FKs → immutable canonical-claim rebuild →
per-item quarantine of unpromotable claims → atomic `master` commit via
`git.head_bound_transaction(primary).families_transact` over the
claim/concept/justification/stance/micropublication families → promotion
provenance git note → promote-time trust calibration stamp; plus
`resolve_source_concept_promotions`, `compute_blocked_claim_artifact_ids`,
`PromotionResult`, `sync_source_branch`, `load_finalize_report`), the immutable
claim rebuild (`source/claim_concepts.build_promoted_claim`), the concept /
justification / stance identity derivers (`families/identity/{concepts,
justifications,stances}.py`), `SourcePromotionPlan` (`source/stages.py`),
`source/registry.py` (`load_primary_branch_concepts`,
`primary_branch_concept_id_by_name`, `primary_branch_concept_match`),
`source/status.py` (families-only `inspect_source_status`), the
`SourceTrustPriorDocument` / `SourceTrustDocument.prior_base_rate` charter field,
and the repository-bound `source_trust_argumentation.calibrate_source_trust`
wiring over the pure `project_source_trust` projection.

The two load-bearing non-commitment invariants are enforced and tested in
`tests/test_source_promote_p83b.py`:
- **quarantine, never drop** — a claim that cannot promote cleanly (unresolved
  concept mapping, unresolved context, dangling justification reference) stays on
  the source branch (present), is surfaced in `PromotionResult.blocked_claims` /
  `blocked_diagnostics`, and never reaches `master`; promotion only aborts when
  *every* claim is blocked.
- **calibration stamps, never gates** — a low-trust (or vacuous/defaulted) source
  still promotes its claims, carrying its honest calibrated prior-trust
  provenance stamped onto the source manifest; calibration never rejects a claim.

Tests ported (now green): `test_promote_atomicity`,
`test_promote_claim_immutability`, `test_promote_writes_provenance_note`,
`test_source_promote_dangling_refs` (→ quarantine), `test_source_trust` /
`test_trust_calibration_runs_at_promote`, `test_no_derive_source_document_trust`
(→ defaulted-leaves-no-prior), plus the two written store-write-boundary
invariant tests above.

Deferred:
- `compile_*_promotion_blocked_projection_rows` / `PromotionBlockedProjectionRows`
  (the sidecar quarantine *mirror* rows over `quire.projections.ProjectionRow` +
  `CLAIM_CORE_PROJECTION` / `BUILD_DIAGNOSTICS_PROJECTION`) -> **9**. The
  quarantine invariant itself is met without them: blocked claims stay on the
  source branch and are surfaced in `PromotionResult`; the derived-store mirror is
  a Phase-9 projection of that same state. `test_sidecar_source_projection`,
  `test_cli_source_status` (the derived-store reader) -> **9**.
- `_validate_promoted_claims_before_commit`'s full CEL/`run_claim_pipeline`
  re-validation (`propstore.compiler` + `families.claims.passes`) -> **9**;
  the registry's commit-time foreign-key validation already enforces canonical
  reference integrity for the promoted slice.
- Canonical artifact-code stamping (`stamp_canonical_artifact_codes`): the flat
  rewrite charters carry no `artifact_code` field, so only the source-side codes
  (8-3a) exist; nothing to port.
- A canonical *source* record family: the rewrite does not model one (the flat
  `Claim` charter carries no source pointer), so promotion writes no master-side
  source artifact; the reference `CanonicalSourceRef`/sources-family write is
  dropped.
- `source/registry.py` parameterization-group merge preview
  (`projected_source_concepts`, `parameterization_group_merge_preview`,
  `preview_source_parameterization_group_merges`, `test_param_group_merge_preview`)
  -> later: it projects concept parameterization relationships that the flat
  rewrite `Concept` charter does not yet model (the rewrite exposes
  `build_parameterization_groups(edges)`, a different shape than the reference's
  `build_groups(concept_payloads)`).
- `source/passes.py` (the semantic-import normalization pipeline) -> **8-5**
  (import); promote does not depend on it.

## Phase 8-5 — import contract + repository import + source/passes.py (DONE)

8-5 builds the import subsystem on the rewrite's charter identity model and the
8-2 source-authoring path: `importing/machinery.py` (the per-row authored-import
assertion compiler), `importing/contract.py` (the typed `ImportManifest` + honest
provenance validation), `importing/repository_import.py` (`import_manifest`), and
`source/passes.py` (the normalization pipeline: type coercion, dedup-to-handle,
identity assignment, reference lowering). An imported row lands on a source
branch as a defeasible claim carrying `stated`/`defaulted` provenance (never
`measured`/`calibrated`), then follows the ordinary finalize → promote lifecycle.

Tests ported (now green): `test_import_machinery` (the per-row contract; pure,
ported verbatim). Tests written (rewrite-native, over `Repository.init`):
`test_import_contract` (provenance honesty + row validation), `test_source_passes`
(coercion / dedup / identity / stance-handle lowering), `test_import_defeasible`
(the discipline proof: measured rejected; stated/defaulted stamped on source trust
+ git provenance note; rows on the source branch, master canonical families empty;
no privileged identity).

Deferred:
- `test_import_repo.py`, `test_repository_import_provenance_attached.py`,
  `test_concept_import_status_proposed.py` (the reference *committed-snapshot
  repo-to-repo* import: `plan_repository_import` / `commit_repository_import`) ->
  **CLOSED in Phase 9-4** (rebuilt rewrite-native, see the Phase 9-4 section). The
  reference cases assumed the 0.2.0 `*Document` identity model (`logical_ids` /
  `version_id` / `.to_payload()` + `make_claim_identity` conftest helpers); the
  rewrite's thin charters key by `concept_id` / `claim_id` alone, so the behavior
  was ported over `Repository.init` source repos in `test_repository_import.py`.
- `import-repository` CLI (`test_import_repo_cli_*`) -> **10** (CLI/presentation).
- `EquivalenceWitnessStore` composition is the non-commitment equivalence surface
  (`test_import_machinery` covers it); any sidecar projection of witnesses -> **9**.

## Phase 8-6 — verify_claim_tree (canonical claim-tree integrity; DONE)

8-6 closes the PLAN §8 mandate "WRITE test for verify_claim_tree if still
unwired". `propstore/verify.py` adds `verify_claim_tree(repo, *, commit=None)` —
the read-only, post-hoc counterpart of the commit-time foreign-key gate
(`quire.families._validate_registry_post_state`). Where that gate *raises* on the
first dangling reference at write time, verify walks the same charter-derived
foreign-key graph (`semantic_foreign_keys()` + `repo.families.by_name(...)
.reference_index()` + quire `validate_foreign_key`) over an arbitrary committed
repository state and returns a typed `ClaimTreeIntegrityReport`
(`resolved` / `dangling` / `quarantined` / `malformed_identity`) — it surfaces
problems, it never drops or collapses anything (non-commitment). A `BLOCKED`
(quarantined) record's unresolved references are reported under `quarantined`,
not counted as a hard failure: quarantine is a valid present-but-filtered state.

Test written (rewrite-native, over `Repository.init`):
`test_verify_claim_tree.py` — clean tree verifies OK; an authored dangling
reference is reported (and the broken row remains present); a quarantined/blocked
row with the same unresolved reference is reported as quarantined and keeps the
tree `ok`; authored vs quarantined references bucket separately; verify is
read-only (master head unchanged). The reference `verify_claim_tree`
(`artifact_verification.py`) is 0.2.0-shaped (`dict[str, Any]`, artifact-code
recomputation, `.to_payload()`, `*Document`, `WorldQuery`); it was rebuilt over
charters rather than ported, per the WRITE mandate.

Deferred:
- `test_verify_cli.py` (the `pks verify tree` CLI surface, recursive artifact-code
  recomputation, origin ni-URI match, and ATMS-label serialization) -> **10**
  (CLI/presentation) and **9** (the artifact-code + WorldQuery recompute path).
  The 8-6 charter-derived FK-integrity audit is the owner-layer entry point those
  presentation surfaces will call.

## Phase 9-0-rest-A — compiler workflows + per-family semantic passes (DONE)

9-0-rest-A builds the AUTHORED -> CHECKED compiler half on top of the 9-0
semantic-pass framework + the Z1 charter-derived schema: the per-family flat-tree
passes/stages (`families/{forms,concepts,claims,contexts}_passes.py`), the CEL
registry + validation (`cel_registry.py`, `cel_validation.py`), the compilation
context (`compiler/context.py`), and the two terminal workflows
(`compiler/workflows.py`). `validate_repository` and `build_repository` run ONE
pass framework + ONE check set and differ only in terminal sink (PLAN.md §12.6).

Flat-tree stage design (DESIGNED, not copied from the reference dir-families):
`LoadedForm` / `LoadedConcept` / `LoadedContext` / `LoadedLiftingRule` /
`LoadedClaim` wrap the one charter directly (the charter is the document — no
`*Record` / `*Row` / `ClaimFileEntry` / `to_payload` mass); `*CheckedRegistry`
(`FormCheckedRegistry`, `ConceptCheckedRegistry`, `ContextCheckedGraph`) and
`ClaimCheckedBundle` (in `compiler/ir.py`) are the per-family checked outputs.

Z1 abort-vs-quarantine split (honored + tested in `test_compiler_workflows.py`):
form/concept/context validation failures and a structural concept in a CEL
expression ABORT (both workflows, `CompilerWorkflowError`); a semantically
invalid *claim* (contract failure, CEL type error, dangling context) is
QUARANTINED as a blocked `CheckedClaim` and the build proceeds. The narrow
structural-CEL pre-pass (`structural_concepts_in_expression`) aborts only on a
`KindType.STRUCTURAL` concept, so ordinary claim CEL errors still quarantine.

Tests written (rewrite-native over `Repository.init` + authored charters):
`test_cel_validation.py`, `test_cel_registry.py`, `test_compilation_context.py`
(PLAN WRITE mandate), `test_family_passes.py`, `test_compiler_workflows.py`.
These translate the reference `test_validate_claims` / `test_cel_checker` /
`test_claim_compiler` / `test_condition_architecture_boundaries` (compiler
boundary) over the flat tree; the reference files are `*Document`/`*Row`-shaped
and were rebuilt, not ported.

Deferred (the build_repository terminal sink + readers are not in this tree yet):
- `test_build_sidecar.py` (+`TestRebuildSkipping`),
  `test_T1_7_build_repository_propagates_sidecar_errors.py`,
  `test_codex5_sidecar_cache_derived_invalidation.py`, `test_sidecar_contexts.py`,
  `test_sidecar_alias_projection.py`, `test_sidecar_grounded_facts.py` -> **9-0-rest-B**
  (the `derived_build` materialize path: `materialize_world_sidecar` /
  `_build_sidecar_file` / `derived_build_plan`). `build_repository` leaves the
  materialize step a clearly-marked seam and honestly reports `sidecar_missing`;
  it never fabricates a sidecar.
- `test_world_query.py`, `test_worldline*.py`, the conflict/phi summary half of
  the build report -> **9-1** (`WorldQuery` reader). `build_repository` reports
  empty `conflicts` / `phi_groups` until the reader exists.
- `test_generated_schema_freshness.py` / `test_fixture_schema_parity.py` /
  `test_required_schema_completeness.py` -> **9-0-rest-B** (assert the
  charter-derived `derived_schema.build_world_sidecar_schema` shape once the
  materialize path consumes it).
- Authoring lints / `strict_authoring` enforcement + `families/diagnostics`
  projection -> **9-0-rest-B** (`build_repository` accepts `strict_authoring` as a
  documented seam; no lint source exists yet so there is nothing to upgrade).
- All `pks build` / `pks validate` Click surfaces -> **Phase 10** (CLI/presentation).


## Phase 9-1 — concrete repo-backed WorldQuery reader (DONE)

9-1 built `world/model.py::WorldQuery(WorldStore)` (the concrete reader over the
materialized content-addressed world sidecar) + `world/queries.py` (the `select_*`
SQL reads + query-error types). The reader opens the sidecar through quire's
charter-derived SQLAlchemy schema (`readonly_session` over
`derived_schema.build_world_sidecar_schema`) and rebuilds the ONE canonical
charter / value type per row via the charter's own msgspec field set — no `*Row`
second spelling. It satisfies the 28-method `WorldStore` protocol (declared as a
subclass so pyright verifies it) and DELEGATES the render-time glue (`bind` /
`active_graph` / `compiled_graph` / `intervene` / `observe` / `chain_query`) to the
C3 free functions in `world/model.py` (bound as private aliases, passing `self`),
re-using the glue unchanged. `from_path` / `historical_query` (rebuild a temp
sidecar at a commit) / `close` / context-manager / `_validate_schema` (catalog
hash + sidecar version, both with a rebuild hint).

Non-commitment / honesty: storage methods return every row regardless of
lifecycle status; `claims_with_policy` / `build_diagnostics` are the render-time
views that hide draft/blocked/quarantine rows unless opted in; a missing sidecar
raises `FileNotFoundError("run pks build")` rather than collapsing to empty;
`similar_claims`/`similar_concepts` return honest-empty (embeddings deferred to
Phase 10 — no sqlite-vec index in this slice). Parameterization edges are derived
at read time from `EQUATION` claims rather than a duplicated projection.

Closed (rewrite-native over `Repository.init` → author → `materialize_world_sidecar`
→ `WorldQuery`):
- `test_world_query.py` (42 cases): the §7a-world-C3 sidecar-build / historical /
  build-diagnostics / schema-validation / parameterization / micropublication /
  render-policy cases. Embedding/similar cases assert the honest-empty contract
  (Phase 10).
- `test_worldline_world_query.py`: the §7a-worldline rows that needed "a concrete
  repo-backed store beyond the in-memory feed" — `test_worldline` /
  `test_worldline_properties` / `test_worldline_praf` (run_worldline + build_praf
  over a real `WorldQuery`), and the §7a-world-B2 `test_world_bound_conflicts_cache`
  row (BoundWorld conflict resolution over the repo-backed reader). The reference
  `FakeWorld` of pre-charter dicts is replaced by the charter-backed reader.

Fixed latent bug surfaced by the concrete reader: `worldline/resolution.py` read
`ActiveClaim.value` (the reference's claim shape); the rewrite's slim `ActiveClaim`
carries the value in `attributes`, so it now reads `attribute_value("value")`.

Superseded (NOT ported — they pin reference reader internals that vanished in the
charter rewrite):
- `test_world_model_resolve_cache.py` — the reference cached a per-instance
  logical-id index over the sidecar; the charter reader resolves by id / canonical
  name directly in SQL (`resolve_concept_id` / `resolve_claim_id`), so there is no
  logical-id cache to pin.
- `test_world_model_branch_column_required.py` — the reference sidecar carried a
  per-row `branch` column; the charter-derived world schema is the single master
  projection (source/proposal branches are not part of it — their sidecar mirror is
  9-3), so there is no branch column.

Still deferred:
- `test_world_query_at_journal_step.py` / `test_world_query_at_journal_step_method.py`
  -> **8** (the `at_journal_step` / `bind_for_view` / `_BoundView` / `ClaimView`
  support_revision journal/worldline bridge is not on the rewrite reader; it is a
  support_revision surface, not a sidecar read).
- Embedding similarity (`similar_*` sqlite-vec backing), `pks build` / `pks
  validate` / `pks log` Click surfaces, and the worldline CLI/document cases ->
  **10** (CLI / embeddings).


## Phase 9-0-rest-B — derived_build materialize + diagnostics + grounded facts (DONE)

9-0-rest-B fills the `build_repository` materialize seam left by 9-0-rest-A. The
build now writes the content-addressed world sidecar and summarises the conflict /
phi compute from the build plan; it is still ONE pass framework (PLAN.md §12.6) —
build only adds the materialize sink downstream of the shared `_compile_repository`.

New surfaces:
- `derived_build.py` — `world_sidecar_hash_inputs` / `world_sidecar_hash` (cache key:
  source revision, sorted source-branch tips, semantic-pass versions, family contract
  versions, `PROPSTORE_SIDECAR_CACHE_BUST`, a digest over the **charter-derived**
  schema [`schema.catalog_hash`, replacing the deleted `schema/generated` dir], and
  dependency pins for argumentation/ast-equiv/bridgman/gunray/quire), and
  `materialize_world_sidecar` / `_build_sidecar_file`. quire OWNS rebuild-on-change
  (`materialize_with_report` returns `built=False` on a cache hit); propstore only
  supplies the hash + builder.
- `derived_build_plan.py` — `RepositoryCheckedBundle` (assembled from the shared
  compile output), `SidecarBuildPlan`, `compile_sidecar_build_plan` (conflict rows +
  the `BuildDiagnostic` rows; quarantine-then-insert for dangling stance / justification
  / micropublication refs).
- `families/diagnostics.py` (`BuildDiagnostic` charter), `families/conflicts.py`
  (`ConflictProjection` charter) — derived-only projection families (no `semantic`
  tag, FK-free, like `LiftingMaterialization`); added to `_CHARTER_MODELS` + the
  `PropstoreFamily` enum. `build_diagnostics.py` — authoring lints + diagnostic lowering.
- Grounded facts: `derived_build` adapts the repo to a `GroundingRepo` and writes the
  raw `grounded_fact` table via the existing `grounding.sidecar`; the rule-authoring
  surface (`families.rules`) exists, so the non-empty grounded path works.

The projection MASS vanished: every authored family is projected directly from its
charter (`session.add_family(name, {charter fields})`) under advisory foreign keys
(`enforce_foreign_keys=False`) — no per-family `compile_*_sidecar_rows` / `ProjectionRow`.

Closed (rewrite-native tests over `Repository.init` + authored charters):
- `test_build_sidecar.py` (+`TestRebuildSkipping`) / `test_codex5_sidecar_cache...` ->
  `test_derived_build.py` (first-build/rebuild-skip, force, source-change invalidation,
  `PROPSTORE_SIDECAR_CACHE_BUST`, charter-family projection).
- `test_sidecar_grounded_facts.py` (build wiring) -> `test_world_sidecar_grounded.py`.
- `test_required_schema_completeness.py` (charter-derived schema shape) -> asserted via
  `test_derived_build.py` + the existing `test_sidecar_quarantine_z1.py`.
- Authoring lints / `strict_authoring` -> `test_build_diagnostics.py`.
- `test_compiler_workflows.py::test_build_materializes_sidecar` (the former
  `test_build_reports_sidecar_missing_honestly`, now that the seam is filled).
- **Z1 §12.1 standing gate** (`T2_2b/2g/2h`, `test_T7_5f_sidecar_build_duplicate_claim`
  analog) -> `test_sidecar_build_z1.py`: a build over a blocked claim or a dangling
  stance / justification / micropublication reference PROCEEDS, projects the offending
  rows, and records a blocking `build_diagnostic` for each.

Still deferred:
- `test_world_query.py`, `test_worldline*.py`, `test_sidecar_alias_projection.py`, and
  the sidecar-read stats (similar / historical) in the build report -> **9-1**
  (`WorldQuery` reader). The conflict / phi summary in the build report is taken from
  the plan, not the reader.
- `lifting_materialization` rows in the *world* sidecar -> **9-1** (the standalone
  `ContextRepository.build_sidecar` path + `test_sidecar_contexts.py` already cover the
  projection; the world-sidecar lifting materialization needs the reader-side lift
  policy). The lifting system already feeds cross-context conflict detection here.
- All `pks build` / `pks validate` Click surfaces -> **Phase 10**.

## Phase 9-3 — blocked-claim sidecar mirror + source-status reader + verify recompute (DONE)

9-3 closes the §A4 source-status derived-store reader + blocked-claim sidecar
mirror, the §A8 artifact-code recompute (with its backward-layer-dep resolved),
and the 8-3b deferred full CEL re-validation in promote.

New surfaces:
- `source/promote.py` — `PromotionBlockedProjectionRows` +
  `compile_source_promotion_blocked_projection_rows` /
  `compile_all_source_promotion_blocked_projection_rows`: each source branch's
  per-item block reasons (the same quarantine `promote_source_branch` applies) are
  lowered to `promotion_blocked` `BuildDiagnostic` rows (`source_ref=
  "<source-branch>:<artifact-id>"`, `claim_id`, structured `reason_kind` in
  `detail_json`). The world `claim` charter is the master projection only (no
  per-row `branch` column — see the 9-1 `test_world_model_branch_column_required`
  supersession), so the branch-scoped blocked state rides on diagnostic rows.
- `derived_build._build_sidecar_file` — mirrors every source branch's blocked
  state into the sidecar `build_diagnostic` table (present, filtered at render via
  `policy.show_quarantined` — never dropped, Z1).
- `source/status.py` — `read_sidecar_source_status(handle, name)` surfaces one
  source branch's blocked claims from the sidecar through the source subsystem's
  own sqlite read (it does NOT import the world layer).
- `source/promote.py` — `_validate_promoted_claims` runs the full claim
  CEL/contract/context pipeline (`run_claim_pipeline`) over the about-to-promote
  immutable claim rebuilds; a semantically invalid promoted claim is QUARANTINED
  (added to the blocked set, `reason_kind="claim_validation"`), not aborted (Z1).
- `verify.py` — `verify_source_artifact_codes` recomputes each source artifact's
  content code (reusing `stamp_source_artifact_codes`) and verifies the origin
  ni-URI; world-free.
- `world/model.py` — `serialize_claim_atms_label` is the world-layer half of the
  verify surface (the bound belief space + ATMS label).

**A8 backward-layer-dep RESOLUTION (option b).** The reference
`artifact_verification.py` imported `world.WorldQuery` + `core.labels` (storage
reaching UP — forbidden). The pure artifact-code recompute + origin ni-URI needs
only claim/source content + `artifact_codes` + `uri`, so it stays in the
storage-layer `verify.py` with NO `from propstore.world` import (asserted by
`test_verify_recompute_p93::test_verify_module_has_no_world_import`). The
ATMS-label walk, which genuinely needs the bound world, lives in the world layer
(`serialize_claim_atms_label`). The CLI/audit surface (Phase 10) composes the two.

Tests written (rewrite-native over `Repository.init` -> author -> finalize ->
build/promote): `test_sidecar_source_status_p93.py` (mirror present + reader
surfaces blocked + honest-empty), `test_verify_recompute_p93.py` (recompute
ok/tamper-mismatch, origin match, world-layer ATMS label, the A8 no-upward-import
gate, promote-time CEL quarantine).

Closed: §A4 (`test_sidecar_source_projection` / `test_cli_source_status` reader
half), §A8 (verify recompute + ATMS-label parts of `test_verify_cli`), the 8-3b
`_validate_promoted_claims_before_commit` row.

Superseded / not ported:
- `test_sidecar_relation_edge_projection.py` (5a -> 9): the charter rewrite stores
  no concept-to-concept `relation_edge` family (`WorldQuery.all_relationships` is
  honest-empty; relation edges derive from stances), so the reference relation_edge
  projection VANISHES like the other reference `*_PROJECTION` mass.

Still deferred:
- `test_cli_source_status` / `pks verify tree` Click surfaces -> **Phase 10**
  (CLI/presentation; the owner readers `read_sidecar_source_status` /
  `verify_source_artifact_codes` / `serialize_claim_atms_label` are the entries
  those adapters will call).
- `test_sidecar_calibration_counts_projection.py` / `test_opinion_schema.py`
  (calibration extract + opinion render projection) -> **Phase 10**.

## Phase 9-4 — repo-to-repo committed-snapshot import + history owner cores (DONE)

9-4 closes §A5 (the committed-snapshot repo-to-repo import deferred at 8-5) and
the §B6 history owner cores. Both are owner-layer surfaces; the Click adapters are
Phase 10.

**Committed-snapshot import** (`importing/repository_import.py`
`plan_repository_import` / `commit_repository_import`, normalization in
`importing/snapshot_passes.py`, `families/registry.semantic_import_roots`): reads
another propstore repository's *committed* canonical semantic tree (HEAD, never
the worktree) restricted to `semantic_import_roots()`, runs it through the generic
`semantic_passes` runner, and lands the result on an `import/<name>` branch as
defeasible claims. Normalization reconciles identity into the importing repository
(concepts dedup by canonical name; claims re-keyed into the repository namespace),
rewrites cross-family references (concept refs on claims via the reconciled map;
stance source/target via quire's `FamilyReferenceIndex` — not string munging), and
passes every other semantic family through verbatim. Identity is content-derived
and provenance-free, so a repeated import of the same commit yields an identical
tree (convergence), and the plan's `deletes` prune import-branch paths the latest
snapshot dropped. A `stated` import provenance note (`operations =
("repository-import",)`, `derived_from = (source_commit,)`) is attached to the
commit — honest provenance that never enters identity and never launders the
import into measured/calibrated; no source row is privileged. The import branch
then follows the normal finalize/promote lifecycle.

**History owner cores** (`propstore/history/reports.py`): `build_log_report` /
`build_diff_report` / `build_commit_show_report` / `checkout_commit` /
`classify_log_operation` over quire git log/diff/show and the build pipeline's
rebuild-from-commit (`materialize_world_sidecar(commit=...)`). Typed reports only
(`LogReport` / `LogRecord` / `MergeLogSummary` / `FileChangeReport` /
`CommitShowReport` / `CheckoutReport`) and typed errors (`BranchNotFoundError` /
`CommitNotFoundError` / `CommitHasNoConceptsError`); no Click, stdout, or
`sys.exit`. A merge commit's log record carries a `MergeLogSummary` loaded from the
merge manifest authored at that commit, preserving the surviving rival argument
counts without collapsing them.

Tests written (rewrite-native, over `Repository.init`, authoring canonical charter
docs via the families API): `test_repository_import.py` (git-backed guard,
committed-head snapshot, default `import/<name>` branch, semantic-tree-only,
concept-ref + stance-ref rewrite, target-master without worktree materialization,
deletes/convergence, `stated` provenance note, importing-surface exports) and
`test_history_reports.py` (diff/show/log + operation classification, show-files
change sets, merge-summary enrichment, checkout rebuild, missing-commit errors).

Closed: §A5 (committed-snapshot import), the §B6 history owner cores.

Still deferred:
- `import-repository` CLI (`test_import_repo_cli_*`) -> **Phase 10**
  (CLI/presentation; composes `plan_repository_import` / `commit_repository_import`).
- `pks log` / `pks diff` / `pks show` / `pks checkout` Click surfaces -> **Phase 10**
  (compose the `propstore.history` owner cores).

## Phase 9-5 — contract manifest + micropub projection + discipline gates (DONE) — PHASE 9 COMPLETE

9-5 closes §A6 (the micropub sidecar projection contract) and the §B4 contract
manifest, and wires the standing discipline gates. It is the final Phase-9 slice.

**Contract manifest / drift** (`propstore/contracts.py`,
`propstore/_resources/contract_manifests/semantic-contracts.yaml`):
`build_propstore_contract_manifest()` assembles the manifest from quire's
`ContractManifest` / `ContractEntry` / `VersionId`. Per the charter-derivation
thesis (PLAN.md §12.6) the hand-authored `document_schema` / `artifact_family` /
`foreign_key` bodies DROP — they fold into the registry's charter-derived
`family-registry` / `family` entries (the FK graph and identity field live inside
each `family` body). What this module composes by hand is the part the charter
does not own: the per-type `claim_type_contract` entries and the `semantic_pass` /
`semantic_stage` pipeline entries (derived from the registered passes, so a stage
cannot drift from a pass). The committed manifest is the drift baseline:
`tests/test_contract_manifest.py` asserts the checked-in YAML equals the derived
one and runs quire's `check_contract_manifest` against `HEAD` (a body change
without a version bump fails). Reference `test_contract_manifest.py` /
`test_doc_drift_clean.py` are retargeted to the charter shape.

**Micropublication WS-CM dedupe** — see the §A6 / Phase-8-3a closure above:
folded into `derived_build._project_documents` first-writer-wins dedupe; covered
by `tests/test_micropub_sidecar_dedupe.py`.

**Standing discipline gates**:
- Import-linter layer contract (`.importlinter`, run by
  `tests/architecture/test_import_boundaries.py`): a one-way layer stack
  (`cli > world > aspic_bridge:praf > heuristic > source > storage`) plus a
  substrate-boundary `forbidden` contract (storage/core never import
  world/aspic_bridge/praf/cli). Both KEPT. The one pre-existing
  `core.analyzers -> praf` entanglement is grandfathered via `ignore_imports` and
  recorded in `docs/gaps.md` (the gate still catches any new substrate→upward
  import). The stale committed config (which referenced the not-yet-built
  `argumentation`/`web`/`app` layers) was replaced with the realised stack.
- Z1 quarantine-not-reject standing gates already landed in 9-0 and stay green:
  `tests/test_sidecar_quarantine_z1.py` (schema advisory FK) and
  `tests/test_sidecar_build_z1.py` (build-level: a blocked claim or dangling
  stance/justification/micropub reference quarantines, the build proceeds).

Closed: §A6 (micropub projection contract + the contract manifest), the standing
import-linter + Z1 discipline gates. **This completes Phase 9.**

Still deferred (Phase 10, presentation only):
- `test_micropubs.py` render/app surface (`find/list/inspect_micropub_lift`) and
  the `micropub list/show/lift` CLI.
- The `test_micropublications_phase4.py` CLI source-promote / ATMS-node cases
  (owner cores exist; only the `pks` adapters remain).
- `pks contract-manifest` Click surface (composes `build_propstore_contract_manifest`).

## Phase 10-0 (render view-builders — the owner-layer view tier)

10-0 built the `propstore.app` owner-layer render view tier (CLAUDE.md layer 5):
typed view-builders that take an already-open `WorldQuery` + a `RenderPolicy` and
return JSON-ready report objects, which the `pks` CLI (10-1) and the web routes
(10-2) consume. No Click, no FastAPI — the single flag→policy construction path is
`propstore.app.rendering.build_render_policy`; owner modules accept the
`RenderPolicy`, never reconstruct it from flags.

Landed surfaces + their tests (rewrite-native, over `Repository.init` → author
charters → `WorldQuery`):
- `app/rendering.py` — `AppRenderPolicyRequest` / `build_render_policy` /
  `summarize_render_policy` / `RenderPolicyValidationError`
  (`tests/test_app_rendering.py`).
- `app/view_state.py` — the view tier's single `ViewState` vocabulary with a
  distinct `UNKNOWN` (PLAN.md §12.4) and the honest-ignorance routing
  (`lifting_view_state` / `applicability_view_state` / `solver_view_state`):
  context-lifting `LIFTED`, defeasible `EXCEPTED`, and a `condition_ir` solver
  `UNKNOWN` all route to `ViewState.UNKNOWN`, which is provably `≠ BLOCKED`
  (policy-hidden) and `≠ MISSING` (no data) — `tests/test_view_state_unknown.py`.
- `app/claim_views.py` + `app/claims.py` — `build_claim_view` per-field state
  machine + NL sentences, and the claim list/search summary rows
  (`tests/test_claim_views.py`).
- `app/concept_views.py` + `app/concepts/` — `build_concept_view` state machine,
  concept list/search reports, `ConceptSearchSyntaxError`
  (`tests/test_concept_views.py`).
- `app/neighborhoods.py` — `build_semantic_neighborhood` (focus_kind=claim only;
  other focuses raise `SemanticNeighborhoodUnsupportedFocusError`)
  (`tests/test_neighborhoods.py`).
- `app/repository_overview.py` — KB-stats / reasoning-inventory report over
  `WorldQuery.stats()` (`tests/test_app_repository_overview.py`).
- `description_generator.py` — `generate_description(claim, concept_registry)`
  retyped onto the charter `Claim` (`tests/test_description_generator.py`).
- Render-time non-commitment + JSON contracts: `tests/test_render_time_filtering.py`
  (present-but-hidden rows filtered at render, never dropped) and
  `tests/test_render_contracts.py` (every report is JSON-ready via `JsonReportMixin`).

Charter-honesty consequences (the charter is thinner than the reference `*Row`):
the claim charter is provenance-free, so the provenance field/section renders
`MISSING` (provenance rides the git-notes sidecar, not the claim row); the
charter has no SI projection, so no `value_si`/`canonical_unit` is fabricated; and
the charter FK forbids dangling concept references, so `build_claim_view`'s
concept-`UNKNOWN` branch is defensive (guards historical/cross-snapshot reads) and
the §12.4 `unknown` contract is proven through the routing functions.

Still deferred past 10-0 (need later 10-x slices, NOT closed here):
- `test_render_policy_opinions.py` / `test_opinion_schema.py` — opinion render
  projection over stance/opinion rows (needs the opinion render surface).
- `test_claim_and_stance_document_enums.py` — families.documents render enum surface.
- `test_world_query.py` embedding-similarity cases (still honest-empty until the
  10-3 sqlite-vec index).
- The CLI render-flag adapter (`test_cli_render_policy_flags`) → 10-1; all
  `test_web_*` route tests → 10-2 (both consume these 10-0 builders).

## Phase 10-0b — owner-layer reasoning-report tier (CLOSED)

The OWNER report functions the CLI/web adapt — genuinely missing from the rewrite
(the reference `world/queries.py` reasoning tier and `app/{project_init,forms,
claims,materialize}` over stale `*Row`/`*Document` projections) — built here as
owner-layer (no Click/FastAPI), retyped over the charter, with new charter-shaped
tests (the reference tests were `*Row`-shaped, so behaviour was ported not files):

- World reasoning tier `world/reasoning_reports.py` (alongside, not clobbering,
  the 9-1 `select_*` readers in `world/queries.py`): `get_world_status`,
  `query_world_concept`, `query_bound_world`, `explain_world_claim`,
  `list_world_algorithms`, `derive_world_value`, `resolve_world_value`,
  `query_world_chain`, `diff_hypothetical_world` + their `World*Request`/
  `World*Report` types (`tests/test_world_reasoning_reports.py`). Closes the
  owner half of the reference `test_world_query` O2/O3 resolve/derive/extensions/
  explain cases.
- `sensitivity.query_sensitivity` + `SensitivityRequest`/`SensitivityReport`
  (`tests/test_sensitivity_query.py`) — over the existing finite-difference
  `analyze_sensitivity` (human-to-sympy, no raw SymPy).
- `app/project_init.initialize_project` (`tests/test_app_project_init.py`) —
  seeds forms + base concepts mapped from the historical resource shape.
- `app/forms.show_form` (`tests/test_app_forms.py`).
- `app/claims.compare_algorithm_claims` + `ClaimCompareRequest`/
  `ClaimComparisonError` (`tests/test_app_claims_compare.py`).
- `app/aliases.export_concept_aliases` (`tests/test_app_aliases.py`) and
  `app/materialize.materialize_repository` (`tests/test_app_materialize.py`).

Charter-honesty consequences: `Stance` has no strength/note (uses `confidence`);
`Claim` has no `algorithm_stage`/`value_si` (omitted, never fabricated); `Concept`
has no top-level aliases (export reads lemon `other_forms`) and no `is_a` field
(seed `is_a` links not stored); `WorldQuery` has no form-algebra projection
(`show_form` omits decomposition/use views until it lands).

Remaining reference cases deferred past 10-0b (NOT closed here):
- The CLI adapter cases of these surfaces (`pks world …`, `pks init`, `pks form
  show`, `pks claim compare`, `pks export-aliases`, `pks materialize`) → 10-1.
- The web routes over the same builders → 10-2.
- `world export-graph` / graph_export + embedding-backed `similar_*` → 10-3.

Value-layer note (pre-existing, not an owner-tier issue): `collect_known_values`
reads the first claim of a determined concept, so an equation claim (value `None`)
sorting before a parameter claim by id can make `derived_value` underspecified —
visible only when authoring equation + parameter claims whose ids sort that way.

## Phase 10-1 (the `pks` CLI adapter tree)

10-1 built the lazy CLI families as thin Click adapters over the 0-9 + 10-0/10-0b
owner layer. CLAUDE.md "CLI adapter discipline" holds throughout: families parse
flags into typed requests, call owner functions, render typed results, and map
typed failures to exit codes; no owner semantics live in `cli/`. The two class-B
discipline gates are green (`tests/test_app_layer_no_cli_payloads.py`,
`tests/test_no_cli_flags_in_owner_errors.py`).

CLOSED here (the A1 CLI rows): the Click surfaces of
- core-read: `pks init` / `build` / `validate` / `log` / `diff` / `show` /
  `checkout` / `merge inspect` / `merge commit` / `verify tree` / `materialize` /
  `contract-manifest` / `export-aliases` (`tests/test_init_cli.py`,
  `test_log_cli.py`, `test_merge_cli.py`, `test_verify_cli.py`,
  `test_materialize_cli.py`, `test_contract_manifest_cli.py`). Adds the owner
  facade `app/merge.commit_merge` (reads the merge tree into a typed report).
- world: `pks world status/query/bind/explain/algorithms/derive/resolve/chain/
  hypothetical/sensitivity/check-consistency/fragility` + `world revision …` and
  the synthetic root `status` (`tests/test_cli_world.py`). Closes the CLI half of
  `test_revision_cli` / `test_revision_phase1_cli` / `test_cli_render_policy_flags`
  (render-policy flags exercised through the world family's lifecycle options).
- authoring read-views: `pks claim show/list/search/neighborhood/compare`,
  `concept list/search/show` + `concept align/decide/promote`, `form show`,
  `context list/show` (`tests/test_cli_claim.py`, `test_cli_concept_display.py`,
  `test_concept_alignment_cli.py`, `test_cli_form.py`, `test_cli_context.py`).
- source: `pks source init/finalize/promote/status/sync/write-*/add-*/propose-*`
  (`tests/test_cli_source_p101.py`); closes `test_source_cli` / `test_cli_source_status`.
- advanced: `pks import-repository`, `grounding status/show/query/arguments`,
  `observatory run`, `predicate list/show/declare/promote`, `rule list/show`,
  `proposal promote` + `proposal predicates promote`, `micropub list/show`
  (`tests/test_cli_phase10_advanced.py`, `test_cli_phase10_1.py`). Extracted a
  public `grounding.loading.load_grounding_repo` so the grounding adapter stays
  thin (`derived_build` delegates to it — single canonical spelling).

NOT closed in 10-1 (owner/phase prerequisites):
- `pks worldline …` (show/list/diff/create/run/refresh/delete/build-journal/
  at-step) and `test_capture_journal.py` CLI cases → the `propstore.app.worldlines`
  owner + repo-backed worldline definition/result persistence do not exist (a
  Phase-9/app-layer prerequisite, already deferred above as `test_worldline.py`
  → 9). The registry keeps a lazy `worldline` entry; it errors only if invoked.
- `pks proposal propose-rules` / `promote-rules` and `test_cli_propose_rules_*` /
  `test_cli_promote_rules_*` / `test_promote_rules_proposals` → need
  `heuristic.rule_extraction` + a rule-proposals family (Phase 10-4).
- `pks micropub lift` and the `test_micropubs` lift cases → need a Phase-10
  `inspect_micropub_lift` owner facade (not built).
- `pks web` → 10-2. `world export-graph` + embedding-backed `claim/concept
  embed/similar` and `claim relate` → 10-3/10-4.
- `grounding explain`, `world atms …`, `world extensions`, `claim validate/
  conflicts`, `concept categories`, direct `concept`/`context`/`form`/`predicate`/
  `rule` mutation → no owner report-builder/mutation owner in the rewrite (the
  conflict surface is already `pks world check-consistency`; mutation flows
  through the `source` subsystem). Skipped, not reimplemented in the CLI.
