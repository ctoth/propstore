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
- test_ic_postulate_coverage.py -> 8/9 (propstore.merge merge-framework over a
  git-backed knowledge store + tests.git_store_helpers / tests.ws_l_merge_helpers;
  this is the merge-side IntegrityConstraint, not support_revision)
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
- test_concept_alignment_cli.py -> 8 (alignment CLI over a Repository)
- test_source_promotion_alignment.py -> 8 (align_sources/decide/promote_alignment)
- test_source_relations.py -> 8 (already listed above; source-relation projection)

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

Still deferred past 7b-4 (need a concrete repo-backed git scope):
- test_worldline_revision_merge_parent_evidence.py -> 8/9 (needs
  `propstore.repository.Repository` + a real git merge DAG to populate
  `RevisionScope.merge_parent_commits`; the in-memory feed degrades scope to
  `None`/`()`).

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

Still deferred past 7b-4:
- test_worldline_revision_merge_parent_evidence.py -> 8/9 (real git merge DAG via
  `propstore.repository.Repository`).

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
