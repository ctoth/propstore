# propstore Consolidated Feature Inventory + Coverage Contract

Synthesis of 10 area inventory reports against the 527-entry master test list
(`_all_test_files.txt`) and the substrate spec (`decomposition/SPEC.md`). Reference
revision: propstore @ 20e55cca (worktree wt-2b240dcb).

**Tag legend.** PORT = behavioral (asserts an outcome/value/validation/render/solver
verdict/identity algorithm → rebuild against the test corpus). DROP = DTO/row/document
shape that vanishes under quire charters (SPEC §D). CONSUME = behavior owned by a
substrate package (import, delete local dup). Substrate codes match SPEC §A–F:
condition-ir, atms, causal-models, provenance-semiring, sympy-eval, calibration,
eq-equiv, ast-equiv, human-to-sympy, assignment-selection, doxa(opinion),
formal-argumentation, formal-belief-set, gunray, bridgman, cel-parser, quire,
named-uri.

Each capability is filed under its ONE owning rewrite slice. Where ≥2 area reports
exercised the same test, the non-owner is noted "(also exercised by X)". Conflicts the
reports disagreed on are flagged inline and collected in §F.

---

## Headline stats

| metric | value |
|---|---|
| Total capabilities inventoried (across 11 slices) | ~290 |
| PORT (behavioral) | ~225 |
| DROP (DTO-shape / charter-vanish) | ~65 |
| Master test files (`_all_test_files.txt`) | 527 |
| Claimed test files, deduped union (`_claimed_test_files.txt`) | 410 |
| ‑ of which present in master (527) | 375 |
| ‑ of which outside master (remediation/ tree + 2 stale) | 35 |
| UNCLAIMED master files (coverage gaps) | 152 (140 `test_*.py` + 12 infra/helper) |
| Multi-claimed master files (owner resolved below) | 75 |
| Capabilities flagged with NO dedicated gating test | 13 |

Per-slice capability counts: concept-core ~24 · claim ~28 · context-grounding-defeasibility
~18 · argumentation-bridge ~34 · world-atms-worldline ~40 · belief-revision ~40 ·
merge-conflict ~27 · source-proposals-provenance ~35 · storage-build-compile ~26 ·
render-cli-web ~22 · heuristic-embeddings ~14.

**Cross-report numeric note:** the master 527 list contains **no `remediation/` entries**
(only flat `test_T1_4`/`test_T1_7`). Every `tests/remediation/phase_*/test_T*.py` cited by
scouts is therefore a claim *outside* the master enumeration — real files, but the master
glob never recursed into `remediation/`. Treated as a distinct category in §D, not as
"unclaimed."

---

## A. Inventory by rewrite slice

### Slice: concept-core
OntoLex-Lemon concept model, forms, dimensions/units, qualia/proto-roles/description-kinds,
concept id minting, description generation, concept search/views/alignment.

| capability | user surface | gating tests | PORT/DROP | substrate |
|---|---|---|---|---|
| Lexical entry/form/sense model (entry≥1 sense; polysemy; homographs; reference-stable id; no dims on LexicalForm) | `propstore.core.lemon` API | test_lemon_concepts.py | PORT | quire, provenance |
| Pustejovsky qualia coercion (view satisfies target type; TELIC chain; provenance op) | `coerce_via_qualia`, `purposive_chain` | test_lemon_phase3_semantics.py | PORT | provenance-semiring |
| Dowty proto-roles (graded [0,1], provenance-bearing, argument selection, bounds enforced) | `ProtoRoleBundle`, `predicted_subject_role` | test_lemon_phase3_semantics.py | PORT | quire, provenance |
| Description-kinds (unique slots; slot-binding type validation; sense carries qualia+kind+roles) | `DescriptionKind`, `validate_slot_bindings` | test_lemon_phase3_semantics.py | PORT | quire, provenance |
| Description-claim coreference as Dung argument (policy-dependent clusters, not a fact) | `coreference_argument`, `coreference_query` | test_lemon_phase3_semantics.py | PORT | formal-argumentation (also exercised by merge-conflict M10) |
| Description-temporal Allen relations → TIMEPOINT/Z3 | `description_temporal_relation` | test_lemon_phase3_semantics.py | PORT | condition-ir |
| Account-sensitive causal transitivity | `causal_transitivity_allowed` | test_lemon_phase3_semantics.py | PORT | — |
| Lemon concept document boundary (rejects flat shape; qualia ref needs provenance; grade bounds; projects ConceptRecord) | `repo.families.concepts.coerce` | test_lemon_concept_documents.py | PORT (+2 roundtrip DROP) | quire (also exercised by merge-conflict) |
| LexicalForm/dimension module boundary (dim algebra only in propstore.dimensions) | architecture | test_lemon_form_dimension_boundary.py | PORT | import/AST assert |
| Concept type-satisfaction walks full is_a/kind_of chain | `passes._concept_satisfies_type` | remediation/phase_6_extend/test_T6_6_concept_type_transitive_closure.py | PORT | — |
| Concept semantic validation passes (logical_id/version/form/deprecated/relationship/parameterization/CEL/dimensional) | `run_concept_pipeline`, `pks validate` | (via quarantine gates) | PORT | bridgman, condition-ir, sympy |
| Build quarantines invalid form/concept/schema (not raises) | `pks build` | remediation/phase_2_gates/test_T2_2a, _2j, _2k, _2n | PORT | quire |
| Source-promote quarantines claim on ambiguous/unresolved concept | source promote | remediation/phase_2_gates/test_T2_2r, _2s | PORT | quire (cross: source) |
| Concept id minting (CAS counter on git ref, concurrent unique) | `next_concept_id_for_repo` | remediation/phase_7_race_atomicity/test_T7_4_concept_id_counter.py | PORT | quire git_store |
| Imported concept w/o status defaults to "proposed" | repository import | test_concept_import_status_proposed.py | PORT | quire |
| Form loading → FormDefinition (dimensions/dimensionless/kind/units/params) | `load_form` | test_form_dimensions.py | PORT | quire tree_path |
| Form document validation pipeline (dims conflict, key rule, non-int exponent, name match) | `run_form_pipeline` | test_form_dimensions.py | PORT | quire |
| Unit conversion (Pint+declared: multiplicative/affine/log, SI-prefix, clinical, unknown raises) | `dimensions.normalize_to_si/from_si` | test_form_utils.py [repoint off DEAD form_utils] | PORT | bridgman (pint) |
| Delta (relative) temperature units normalize without absolute offset | `dimensions` delta | test_temperature_delta_unit.py | PORT | pint |
| Form extra_units register into Pint + symbol table; reset | `register_form_units`, `clear_symbol_table` | test_form_units_pint_sync.py, test_form_dimensions.py | PORT | pint, resources |
| Form cache (clear/reload, path-cache by knowledge root, single owner) | `clear_form_cache` | test_form_utils.py, remediation/phase_6_extend/test_T6_8_form_cache_single_owner.py | PORT | — |
| dims_signature canonical Bridgman signature | `dimensions.dims_signature` | test_form_algebra.py | PORT | bridgman |
| Form algebra auto-derivation from parameterizations (dedup, powers, dim_verified flag, error propagation) | sidecar build / WorldQuery | test_form_algebra.py | PORT | bridgman, sympy, ast-equiv (cross: world) |
| Claim description generation (parameter/equation/observation/measurement/model/algorithm; CEL prose) | `generate_description` | test_description_generator.py | PORT | pure python |
| Concept search FTS (delegates to declaration owner; malformed → typed 400, never 500) | `pks concept search`, `/concepts.json` | test_concept_workflows.py, test_concept_fts_malformed_query.py | PORT | quire FTS5 |
| Concept embeddings (embed all/one, find-similar resolve id/default model) | `pks concept embed/similar` | test_concept_workflows.py | PORT | quire vec (also exercised by heuristic-embeddings) |
| Concept view report (form/status/value/provenance, visible vs blocked counts, errors) | `build_concept_view`, web | test_concept_views.py, test_render_policy_concept.py | PORT | world RenderPolicy (also exercised by render-cli-web) |
| Web concept routes (HTML/JSON parity, unknown→accessible error, policy/limit rejects) | `/concepts/...`, `/concepts.json` | test_web_concept_routes.py, test_web_concept_index_routes.py | PORT | fastapi (also exercised by render-cli-web) |
| Concept alignment (lemon-identity mutual attacks, no token-overlap inference, align/decide/promote) | `pks concept align/query/decide/promote` | test_concept_alignment_cli.py | PORT | formal-argumentation, quire (see merge-conflict R5) |
| Concept mutation CLI (add/alias/rename/deprecate/link/qualia/description-kind/proto-role/add-value; CEL-cascade rename) | `pks concept *` | **NO dedicated mutation test** (via alignment/workflows/validation) | PORT | quire — port-risk |
| Form CLI workflows (add/list/search/validate/remove) | `pks form *` | test_form_workflows.py, test_form_dimensions.py | PORT | quire |
| description_kinds layer must not import argumentation | architecture | remediation/phase_4_layers/test_T4_4_description_kinds_protocol.py | PORT | import assert |
| Concept/form sidecar projection rows | declaration projections | test_sidecar_concept_projection.py, test_sidecar_form_projection.py, test_sidecar_form_algebra_projection.py | DROP | quire projections |

### Slice: claim
Typed CEL frontend, ConditionIR + backends + ConditionSolver, equation/sympy comparison,
parameterization, value comparison, claim authoring/validate/quarantine. (condition-ir is
the dominant EXTRACT cluster; eq-equiv/human-to-sympy/value-comparison glue stays propstore.)

| capability | user surface | gating tests | PORT/DROP | substrate |
|---|---|---|---|---|
| CEL type-check (kind discipline, comparison mismatch, category set, ternary unify, in-list) | `pks claim validate` | test_cel_checker.py, test_cel_ternary_unification.py, test_cel_float_exponent.py, test_cel_string_escapes.py | PORT | condition-ir (cel-parser) |
| CEL→ConditionIR lowering + check (CheckedCondition + registry fingerprint + warnings) | `core.conditions` API | test_condition_ir.py, test_checked_condition_ir.py, test_condition_ir_semantic_metadata.py | PORT | condition-ir |
| ConditionIR node model + invariants (literal kind-guards, span, reference non-empty) | `core.conditions.ir` | test_condition_ir.py | PORT | condition-ir |
| ConditionIR JSON codec (versioned, unknown-version/node reject) | API | test_condition_ir_encoding.py | PORT | condition-ir |
| CheckedConditionSet build/normalize (dedupe, fingerprint agreement, roundtrip) | API | test_checked_condition_ir.py | PORT | condition-ir |
| Z3 satisfiability (`is_condition_satisfied`) | `pks claim compare` | test_condition_solver_parity.py, test_ztypes_category_prior.py | PORT | condition-ir/z3 |
| Z3 disjointness/equivalence/implication/partition | API; classifier; worldline | test_condition_solver_parity.py, test_atms_cel_semantic_equality.py | PORT | condition-ir/z3 (also exercised by world) |
| Z3 definedness/partiality projection (div-by-zero, AND/OR short-circuit, ternary unselected) | encoder API | test_z3_division_definedness.py | PORT | condition-ir/z3 |
| TIMEPOINT semantics (z3.Real, distinct kind, interval ordering constraints) | temporal Allen path | test_condition_solver_temporal_ordering.py, test_temporal_conditions.py | PORT | condition-ir/z3 |
| Category Z3 encoding (closed EnumSort vs open String; unknown closed rejected) | API | test_condition_solver_parity.py, test_condition_z3_backend.py | PORT | condition-ir/z3 |
| Honest-ignorance solver surface (Sat/Unsat/Unknown; Z3UnknownError; reason classify) | API | test_ztypes_solver_unknown.py, test_z3_translation_error_surfaced.py | PORT | condition-ir/z3 |
| Registry-fingerprint mismatch guard | API | test_condition_solver_parity.py, test_z3_registry_snapshot.py | PORT | condition-ir |
| Condition→Python AST eval backend | API | test_condition_python_backend.py | PORT | condition-ir |
| Condition→ESTree backend + JS-semantics eval | API | test_condition_estree_backend.py | PORT | condition-ir |
| Condition→SQL fragment backend | API; sidecar | test_condition_sql_backend.py | PORT | condition-ir |
| Runtime no-reparse (encoded_ir reused) | runtime | test_condition_runtime_no_reparse.py | PORT | condition-ir |
| Condition conflict classification → ConflictClass (CONFLICT/PHI_NODE/OVERLAP/UNKNOWN) | conflict detector | test_condition_classifier.py, test_ztypes_solver_unknown.py | PORT | condition-ir/z3 (cross: merge C6) |
| CEL ingest validation gate (reject structural/malformed CEL → CelIngestValidationError) | source commit, build | test_cel_validation.py, test_validate_claims.py, remediation/phase_3_ignorance/test_T3_5_activation_unknown_cel.py, phase_2_gates T2_2i/2o/2q | PORT | propstore over condition-ir |
| CEL registry projection (ConceptRecord→ConceptInfo; dup rejection; kind-from-form) | build path | test_z3_registry_snapshot.py, test_cel_types.py | PORT (+projection DROP) | propstore |
| CEL typed carriers (CelExpr/CelRegistryFingerprint NewTypes) | API | test_cel_types.py | PORT | condition-ir |
| Registry fingerprint determinism (sha256 over registry semantics) | API | test_z3_registry_snapshot.py | PORT | condition-ir |
| Standard synthetic CEL bindings (source/domain runtime env contract) | runtime | test_cel_validation.py | PORT | propstore |
| Equation parse (lark grammar, one `=`, whitelist, arity) | equation conflict | test_equation_comparison.py | PORT | eq-equiv (sympy/lark) |
| Equation structural signature (alpha-renamed) + render_equation | API | test_equation_comparison.py, test_equation_orientation.py | PORT | eq-equiv |
| Equation canonical equivalence (sympy residual, domain assumptions, UNKNOWN w/o assumptions) | conflict status | test_equation_comparison.py, test_equation_comparison_properties.py, test_equation_conflict_status.py, test_algorithm_sympy_tier_not_conflict.py | PORT | eq-equiv (cross: merge C3) |
| Equation concept-grouping signature (role-invariant) | grouping | test_equation_signature_role_invariance.py | PORT | eq-equiv (cross: merge) |
| Human-math → SymPy generation (identifier-vs-builtin, check_symbols, LHS not dropped) | claim validator, sidecar | test_sympy_generator.py, test_sympy_generator_no_lhs_drop.py | PORT | human-to-sympy CONSUME |
| Parameterization connected-component grouping (union-find over alias/inputs) | sidecar; worldline | test_parameterization_groups.py, test_sidecar_parameterization_group_projection.py, test_canonical_claim_groups_no_union_find.py | PORT | propstore (cross: merge) |
| Parameterization graph reachability (BFS, edge-map, exactness filter) | worldline; transitive conflicts | test_sidecar_parameterization_projection.py, test_parameter_conflict_* | PORT | propstore |
| Parameterization conflict (Z3 strictness, cross-class unknown, unit-aware, error preservation) | conflict detector | test_parameter_z3_strictness.py, test_parameter_conflict_unit_aware.py, test_parameter_conflict_error_preservation.py | PORT | propstore + condition-ir (cross: merge, concept) |
| Value/interval compatibility (point/range/tolerance, unit-aware SI normalization) | conflict detector | test_value_comparison_units.py | PORT | bridgman (cross: concept condition-glue) |
| Claim authoring/validation workflow (single/file/repo) | `pks claim validate/validate-file`, `pks validate` | test_validate_claims.py, test_claim_workflows.py, test_claim_compiler.py | PORT | propstore (cross: storage) |
| Claim compare (Z3 over two claim ids) | `pks claim compare` | test_condition_solver_parity.py | PORT | condition-ir/z3 |
| Claim immutability / promote / materialize provenance preserved | promote workflow | test_promote_claim_immutability.py, test_materialized_claim_provenance_preserved.py | PORT | quire + provenance (cross: source) |
| Claim quarantine pipeline (invalid claim LANDS as build_status='blocked' stub row in claim_core + a build_diagnostics row; render-policy filters — NEVER a build-time abort/drop) | ingest gates | phase_2_gates T2_2b/2g/2h, phase_7 test_T7_5f_sidecar_build_duplicate_claim.py | PORT (test asserts the blocked stub row EXISTS, positive) | propstore |
| Condition architecture boundary + docs-done | meta/test | test_condition_architecture_boundaries.py, test_condition_docs_done.py | PORT | condition-ir extraction gate |
| Claim document load/expand/accessors; schema/enums/type-contracts/views; id/version/dedupe/snapshot | claims.py API; document model | test_claim_roundtrip_fixtures.py, test_claim_and_stance_document_enums.py, test_claim_type_contracts.py, test_claim_views.py, test_claim_notes.py, test_codex2_claim_dedupe_diverges_on_version.py, test_snapshot_to_claim_ids.py, remediation/phase_5_bridge/test_T5_8_projection_typed_claim_identity.py | DROP | quire claim charter (also exercised by render, storage) |
| Claim display/search/list/neighborhood; render policy on direct claim | `pks claim show/list/...`, web | test_web_claim_routes.py, test_web_claim_index_routes.py, test_render_policy_direct_claim.py | PORT (render) | quire vec / render (owner render-cli-web; here for claim render-policy) |
| **NEW: Situated-assertion core model** (`core/assertions`: ConditionRef/ContextReference/AssertionCanonicalRecord/AssertionSourceRecord; UNCONDITIONAL_CONDITION_REF; canonical codec, refs, structural→situated conversion) — foundational identity carrier consumed by belief-revision/merge/base-rates | core.assertions API | test_situated_assertions.py, test_situated_assertion_codec.py, test_situated_assertion_refs.py, test_structural_assertion_conversion.py | PORT (content-identity) | quire hashing; provenance |
| **NEW: Algorithm-claim staging / free-variable locals + ast-equiv integration** | claim authoring; sidecar | test_algorithm_free_variable_locals.py, test_algorithm_stage_types.py, test_ws_o_ast_integration.py | PORT | ast-equiv CONSUME; human-to-sympy |

### Slice: context-grounding-defeasibility
First-class `ist(c,p)` contexts, authored lifting rules, CKR justifiable exceptions,
gunray Datalog grounding, predicate/rule artifacts.

| capability | user surface | gating tests | PORT/DROP | substrate |
|---|---|---|---|---|
| First-class ist(c,p) contexts; no ancestry visibility (effective_assumptions = own only) | `pks context add`, `LiftingSystem` | test_contexts.py, test_context_lifting_phase4.py, test_context_lifting_ws5.py | PORT | quire, cel-parser |
| Authored lifting decision LIFTED/BLOCKED/UNKNOWN (CEL rule-conditions gated through Z3) | `pks context lifting add/...`, `lift_decisions_*` | test_context_lifting_ws5.py, test_contexts.py | PORT | cel-parser+z3, provenance-semiring |
| Lifting exception local (blocks only matching rule/target/proposition; emits ExceptionDefeat) | same | test_context_lifting_ws5.py, test_lifting_blocked_in_provenance.py | PORT | provenance-semiring |
| CKR justifiable-exception applicability HOLDS/EXCEPTED/UNKNOWN (solver-unknown never positive) | `defeasibility.evaluate_contextual_claim` | test_defeasibility_satisfaction.py | PORT | cel-parser+z3, provenance-semiring |
| CKR exception defeats injected into CSAF Dung layer | `apply_exception_defeats_to_csaf` | test_defeasibility_aspic_integration.py | PORT | formal-argumentation (also exercised by argumentation-bridge) |
| Exception support algebra (live/nogood multiply, lift by rule support, quality compose) | `defeasibility.exception_*` | test_defeasibility_support_contract.py | PORT | provenance-semiring |
| Datalog grounding via gunray → four-valued (all 4 sections, deterministic, budget) | `pks grounding status/show/query` | test_grounding_grounder.py, test_grounder_budget_exceeded.py, test_defeasible_conformance_tranche.py | PORT | gunray (also exercised by concept-core glob false-match) |
| Fact extraction from concepts+claims via typed derived_from DSL (dedup, deterministic) | `grounding.facts.extract_facts` | test_grounding_facts.py | PORT | gunray, quire |
| Predicate registry (id→signature, dup reject, validate_atom arity/kind, parse_derived_from) | `PredicateRegistry` | test_predicate_registry.py | PORT | pure |
| Translator propstore→gunray DefeasibleTheory (rule-kind routing, strong-neg, superiority closure) | `translate_to_theory` | test_grounding_translator.py | PORT | gunray, formal-argumentation |
| Grounding inspection (classify surface, counts, atom query, argument projection, dialectical explain) | `pks grounding status/show/query/arguments/explain` | test_grounding_inspection.py, test_grounder_default_returns_arguments.py | PORT (reports DROP) | gunray (also exercised by argumentation-bridge) |
| Build runtime bundle from snapshot (rules-without-predicates fails loud; empty for rule-free) | `build_grounded_bundle` | test_grounding_loading.py | PORT | gunray, quire |
| Grounded-fact sidecar projection (4-section roundtrip, empty marker, PK set-semantics, no pickle) | sidecar build | test_grounded_bundle_round_trip.py | DROP (PORT 4-section invariant) | quire, gunray |
| Context sidecar projection + load_lifting_system rehydration | sidecar build | test_contexts.py, test_context_lifting_ws5.py | DROP | quire |
| Context semantic pipeline passes (normalize/identity/lifting-binding/graph; dup-id/missing diagnostics) | `run_context_pipeline` | test_contexts.py | PORT (scaffold DROP) | semantic_passes |
| Authored doc schemas (Context/LiftingRule/Structure; Rule/Predicate/Atom/Term/Superiority) — reject visibility-inheritance | YAML authoring | test_context_lifting_phase4.py, test_predicate_documents.py, test_rule_documents.py, test_contexts.py | DROP (PORT reject-visibility semantics) | quire documents |
| Authoring CRUD workflows (contexts/lifting/predicates/rules/superiority; dry-run, ref-block, CEL/source validation) | `pks context*`, rule/predicate authoring | test_context_workflows.py, test_predicate_workflows.py, test_rule_workflows.py, test_rule_artifact_workflows.py, test_rule_superiority_artifacts.py, test_predicate_authoring_properties.py, test_rule_authoring_properties.py | PORT (Click adapter DROP) | quire |
| ist-projection + lifting-decision architecture contracts (typed evidence carrier, not boolean) | architecture | architecture/test_ist_projection_contract.py, architecture/test_lifting_decision_contract.py | PORT | formal-argumentation |

### Slice: argumentation-bridge
Domain→formal-argumentation kernel bridges: claim_graph, aspic_bridge, praf,
source_trust_argumentation, preference, opinion(doxa) shim, calibration boundary,
structured_projection. **The real AF/PrAF assembly lives in `core/analyzers.py`** (not the
nominal `argumentation.py` marker) — the slice charter MUST include core/analyzers.

| capability | user surface | gating tests | PORT/DROP | substrate |
|---|---|---|---|---|
| Claim-graph → bipolar Dung AF (attacks+defeats over active claims) | `world extensions/resolve` backend=claim_graph; core/analyzers | test_argumentation_integration.py | PORT | formal-argumentation (dung) CONSUME; bridge PORT |
| **NEW: Core AF/PrAF assembly** (the real assembly in `core/analyzers.py`: `claim_graph.compute_claim_graph_justified_claims` + `praf.build_praf` + `argumentation.probabilistic.compute_probabilistic_acceptance` over one shared claim/stance/conflict input) | core/analyzers; `world resolve` | test_core_analyzers.py | PORT | formal-argumentation (dung+probabilistic) CONSUME; bridge PORT |
| **NEW: Justification synthesis from active graph** (`core/justifications.claim_justifications_from_active_graph` over StanceRow/ConflictRow) — previously only "(via test_argumentation_integration.py)", now dedicated | aspic_bridge harvest | test_core_justifications.py | PORT | propstore core.relation_types |
| Justified-claim extension (grounded/preferred/stable) | `world extensions --semantics` | test_argumentation_integration.py, test_worldline_argumentation_multi_extension.py | PORT | dung CONSUME (also exercised by world) |
| Cayrol support-derived defeats / bipolar closure (supports never defeats; phi inert) | core/analyzers + build_af | test_argumentation_integration.py | PORT | dung |
| Claims → ASPIC+ literals (contextual ist atoms) | `aspic_bridge.claims_to_literals` | test_aspic_bridge.py | PORT | argumentation.aspic |
| Justifications → strict/defeasible rules | `justifications_to_rules` | test_aspic_bridge.py | PORT | argumentation.aspic |
| Stances → contrariness fn (rebut/supersede/undermine/undercut) | `stances_to_contrariness` | test_aspic_bridge.py, test_ws_f_aspic_bridge.py | PORT | argumentation.aspic |
| Knowledge base build (Kn axioms/Kp premises) | `claims_to_kb` | test_aspic_bridge.py | PORT | argumentation.aspic |
| Preference config (elitist/democratic, premise+rule order, strict_partial_order_closure) | `build_preference_config`, preference | test_aspic_bridge.py, test_ws_f_aspic_bridge.py, architecture/test_argumentation_pin_preference_parity.py | PORT | argumentation.preference CONSUME; doxa |
| Full CSAF build (build_arguments/attacks/defeats + preference-sensitive directional filtering + induced Dung) | `build_bridge_csaf`, `compile_bridge_context` | test_argumentation_integration.py, test_ws_f_aspic_bridge.py, test_aspic_bridge_review_v2.py | PORT | argumentation.aspic CONSUME |
| Goal-directed ASPIC+ query (backward chaining one claim + attackers) | `query_claim` | test_ws_f_aspic_bridge.py | PORT | argumentation.aspic |
| Grounded gunray bundle → ASPIC+ rules (+origins/rule_order/facts→Kn; undercutter from defeaters) | `project_grounded_rules` | test_aspic_bridge_grounded.py, test_grounder_default_returns_arguments.py | PORT | argumentation.datalog_grounding, gunray |
| Context-lifting decisions → ASPIC+ ist bridge rules (BRIDGE=strict; only LIFTED projects) | `project_lifting_decisions` | test_ws_f_aspic_bridge.py, test_defeasibility_aspic_integration.py | PORT | argumentation.aspic (over context_lifting) |
| Structured projection (CSAF→StructuredProjection: strength, support quality, provenance frame, loss witness) | `build_aspic_projection`, `csaf_to_projection` | test_ws_f_aspic_bridge.py, test_structured_projection.py, test_structured_merge_projection.py, test_structured_merge_supports_preferred_stable.py, test_projection_boundary_ws6.py, architecture/test_backend_identity_contracts.py | PORT | argumentation.aspic (**mis-bucketed by storage report**; owner here) |
| Build PrAF from store (attacks/supports/direct defeats + P_A; uncalibrated omitted) | `praf.build_praf`; core/analyzers.build_praf_from_shared_input | test_praf.py, test_praf_integration.py, test_worldline_praf.py | PORT | argumentation.probabilistic (also exercised by merge, world) |
| Probabilistic acceptance compute (deterministic/exact/MC-CI/connected-component/tree-decomp DP) | `world extensions` backend=praf | test_praf.py, test_praf_paper_td_complete_routing.py | PORT | argumentation.probabilistic CONSUME |
| Opinion-derived edge/arg probabilities w/ honest NoCalibration | `p_arg_from_claim`, `p_relation_from_stance`, `p_defeat_from_stance` | test_praf.py, test_praf_uncalibrated_explicit.py, test_praf_raw_confidence_not_dogmatic.py | PORT | doxa CONSUME (also exercised by render, merge) |
| COH rationality enforcement (reconstruct opinions from clamped expectations; soft/hard divergence) | `praf.enforce_coh` | test_enforce_coh_convergence.py, test_enforce_coh_diverges_loudly.py | PORT | doxa (propstore provenance delta) |
| Defeat marginal summary → provenance-bearing ProbabilisticRelation (vacuous when uncalibrated) | `summarize_defeat_relations` | test_defeat_summary_opinion_honest.py, test_defeat_summary_opinion_no_fabrication.py | PORT | argumentation.probabilistic + provenance |
| PrAF immutability + argument-enumeration budget | `PropstorePrAF` frozen | test_praf_frozen_immutable.py, test_praf_argument_enumeration_budget.py | PORT | argumentation.probabilistic |
| Opinion type + validity discipline (b+d+u=1, mandatory base rate, vacuous/dogmatic, allow_dogmatic gate) | `opinion.Opinion` | test_opinion.py, test_opinion_allow_dogmatic_enforced.py, test_opinion_schema.py | PORT | doxa CONSUME (SPEC §B strongest, 13 importers) |
| **NEW: Base-rate resolution over situated-assertion identity** (`core.base_rates`: BaseRateResolver/BaseRateProfile → BaseRateResolved/BaseRateUnresolved; `construct_assertion_opinion`, AssertionOpinion) | core.base_rates | test_base_rate_resolution.py | PORT | doxa + provenance; SituatedAssertion identity |
| Binomial logic operators (negation/AND/OR) | `Opinion.__invert__/conjunction/disjunction` | test_opinion.py | PORT | doxa |
| Fusion + trust operators (consensus/WBF/CCF/fuse/discount) | `consensus/wbf/ccf/fuse/discount` | test_relate_wbf.py, test_relate_opinions.py, test_subjective_logic_operator_audit.py, test_subjective_logic_docs.py | PORT | doxa (also exercised by render relate) |
| Evidence↔opinion mapping (from_probability/from_evidence/BetaEvidence; W=2 prior) | `opinion.from_probability` | test_opinion.py, test_relate_opinions.py | PORT | doxa |
| SL operator coverage manifest / canonical-vector contract | API audit | test_subjective_logic_operator_audit.py | PORT (contract) | doxa boundary |
| Opinion ordering/equality/quantized hashing | `Opinion` rich comparison | test_opinion.py, test_relate_opinions.py | PORT | doxa |
| Claim metadata strength heuristic (3-dim Pareto + vacuous-opinion honesty) | `preference.metadata_strength_vector`, `claim_strength` | test_preference.py | PORT | doxa; propstore-proper heuristic |
| Source-trust calibration via argumentation (rule firings → Dung → grounded → SL opinion) | `calibrate_source_trust`; runs at promote | test_source_trust_argumentation.py, test_source_trust.py, test_trust_calibration_runs_at_promote.py, test_prior_base_rate_is_opinion.py | PORT | dung CONSUME; doxa (also exercised by source, render) |
| Source-trust rule loading from knowledge/rules YAML | `_load_rules_from_repo` | (via test_source_trust_argumentation.py) | PORT (IO) | yaml; quire |
| StanceType vocabulary + coercion | `stances.StanceType`, `coerce_stance_type` | test_claim_and_stance_document_enums.py | DROP (vocab) | quire charter enum (also exercised by claim) |
| Stance authoring workflow (relate heuristic → PROPOSAL files; commit/promote/idempotency) | `pks claim relate [--all]` | test_relate_async.py, test_relate_bulk.py, test_relate_dedup.py, test_relate_perspective_isolation.py, test_commit_stance_proposals_*, test_promote_stance_proposals_idempotency.py, test_plan_stance_proposal_promotion_typo_path.py | DROP (row/proposal) + PORT (heuristic) | quire; doxa (heuristic owner = render-cli-web H3) |
| Stance/justification harvest for AF (active graph → StanceRow; attack/support filter; justification synthesis) | `aspic_bridge.extract` | (via test_argumentation_integration.py) | PORT | propstore core.relation_types |
| Kernel-boundary contract (bridge imports kernel; kernel not propstore) | architecture | architecture/test_argumentation_boundary_contract.py, test_ws_f_aspic_bridge.py | PORT | import discipline |
| Kernel integration / track-E | test surface | test_argumentation_integration.py, test_argumentation_package_track_e.py | PORT (mixed) | formal-argumentation |

### Slice: world-atms-worldline
World query/render orchestration, bound world (Z3 activation), resolution strategies, ATMS
(EXTRACT), causal models (EXTRACT), worldline runner/capture, observatory, journal replay.

| capability | user surface | gating tests | PORT/DROP | substrate |
|---|---|---|---|---|
| World query construction/load (from_path, auto-materialize, ctx mgr, historical) | `pks world status`; WorldQuery | test_world_query.py, test_world_model_branch_column_required.py | PORT | propstore |
| Unbound store reads (get/resolve concept/claim/alias, claims_for, conflicts, search) | `pks world query/explain` | test_world_query.py | PORT | propstore |
| FTS / similarity search (search, similar_claims/concepts) | `pks world query` | test_world_query.py | PORT | propstore + quire vec |
| Render-policy claim filtering (claims_with_policy, predicates, diagnostics) | `pks world query/status` flags | test_render_policy_filtering.py, test_render_time_filtering.py, test_render_policy_concept.py, test_render_policy_direct_claim.py, test_render_policy_neighborhood.py, test_render_policy_opinions.py | PORT | propstore (also exercised by render-cli-web — **owner render-cli-web R1-R7**; world owns the world-side predicate impl) |
| RenderPolicy DTO (flags→policy build) | CLI flags | test_render_contracts.py | DROP | propstore |
| Typed world query owner APIs (Status/Concept/Bind/Explain/Algorithms/Derive/Chain Report) | `pks world status/query/explain/algorithms/derive/chain` | test_world_query.py, test_world_layer_boundary.py | DROP wrappers (PORT underlying) | propstore |
| Bound world Z3 condition activation (bind/rebind/is_active/value_of/collect_known_values) | `pks world bind` | test_world_query.py, test_world_bound_conflicts_cache.py, test_world_model_resolve_cache.py | PORT | condition-ir (CEL/Z3) |
| Derived value parameterization eval (ActiveClaimResolver, algorithm equivalence) | `pks world derive` | test_worldline.py | PORT | ast-equiv + sympy-eval |
| Conflict recompute / determinacy | `pks world query` | test_world_bound_conflicts_cache.py, test_world_query.py | PORT | propstore |
| Resolution RECENCY / SAMPLE_SIZE / OVERRIDE | `pks world resolve --strategy` | **no standalone test** (via worldline/render-policy); override: test_worldline_override_prefix_constant.py | PORT | propstore — recency/sample_size port-risk |
| Resolution ARGUMENTATION (claim_graph/aspic/praf/atms backends) | `pks world resolve --strategy argumentation` | test_resolution_helpers.py, test_atms_engine.py, test_worldline_praf.py | PORT | formal-argumentation, atms |
| Resolution ASSIGNMENT_SELECTION_MERGE (problem build + integrity-constraint enrichment) | `pks world resolve --strategy assignment_selection_merge` | test_resolution_helpers.py | PORT | assignment-selection CONSUME |
| Assignment-selection solver (sigma/max/gmax, claim/assignment distance, mu constraints) | internal (via resolve) | test_assignment_selection_merge.py | PORT (operators CONSUME) | assignment-selection + condition-ir |
| IntegrityConstraint eval (RANGE/CATEGORY/CEL/CUSTOM) | internal | test_assignment_selection_merge.py, test_resolution_helpers.py | PORT | condition-ir (also merge M3) |
| Decision criterion / opinion tiebreak (apply_decision_criterion) | praf tiebreak | test_apply_decision_criterion_provenance.py (via worldline_praf/resolution_helpers) | PORT | doxa (**misplaced in world/types** — belongs at doxa boundary) |
| Backend/semantics validation (ReasoningBackend enum) | `pks world resolve` | test_resolution_helpers.py, test_atms_engine.py | PORT | propstore |
| Hypothetical / overlay diff (OverlayWorld, SyntheticClaim, grounded-ext diff) | `pks world hypothetical` | test_overlay_world_renamed.py, test_worldmodel_renamed.py, test_world_query.py | PORT | propstore + formal-argumentation |
| Chain query (transitive derivation) | `pks world chain` | test_worldline.py | PORT | propstore |
| Consistency check | `pks world check-consistency` | **NO dedicated test** (indirect) | PORT | propstore — port-risk |
| Sensitivity / fragility (worldline capture) | `pks world sensitivity/fragility` | test_worldline.py (gates in belief-revision slice) | PORT | sympy-eval (cross: belief) |
| Graph export | `pks world export-graph` | test_graph_export.py (owner render-cli-web G1/G2) | PORT | propstore |
| ATMS engine: labels/support | `pks world atms status` | test_atms_engine.py | PORT | atms + provenance-semiring |
| ATMS: nogoods / contradiction pruning / explain_nogood | `pks world atms why-out/verify` | test_atms_engine.py, test_atms_was_pruned_by_nogood_cycle.py, test_atms_propagation_nogood_interleave.py, test_atms_derived_contradictions.py | PORT | atms + provenance-semiring |
| ATMS: environments / essential support | `pks world atms context/status` | test_atms_engine.py, test_atms_environment_context_serialisation.py | PORT | atms |
| ATMS: context-labeled / micropublication nodes | `pks world atms context` | test_atms_engine.py, test_atms_categorical_provider_visibility.py | PORT | atms |
| ATMS: node status / support-quality honesty | `pks world atms status` | test_atms_engine.py | PORT | atms |
| ATMS: bounded future / replay / inquiry | `pks world atms futures/next-query` | test_atms_engine.py, test_atms_max_iterations_anytime.py | PORT | atms (anytime) |
| ATMS: stability | `pks world atms stability` | test_atms_engine.py, test_atms_unbounded_stability_api.py | PORT | atms |
| ATMS: relevance / interventions / next-query | `pks world atms relevance/interventions/next-query` | test_atms_engine.py | PORT | atms |
| ATMS: why-out / flip witnesses | `pks world atms why-out` | test_atms_engine.py | PORT | atms |
| ATMS: label verification | `pks world atms verify` | test_atms_engine.py | PORT | atms |
| ATMS: order-independence / cycle safety | internal | test_atms_engine.py | PORT | atms |
| ATMS: CEL semantic equality of providers | internal | test_atms_cel_semantic_equality.py, test_atms_categorical_provider_visibility.py, test_atms_consequent_field_discipline.py | PORT | atms + condition-ir (also exercised by claim) |
| ATMS: argumentation-state projection | worldline backend=atms | test_atms_engine.py | PORT | atms → worldline |
| ATMS CLI surface | `pks world atms ...` | test_atms_engine.py | DROP (CLI adapter) | propstore |
| Pearl intervention (do-surgery): InterventionWorld, scm.intervene, diff | WorldQuery.intervene | test_intervention_world_severs_edges.py, test_intervention_diff_walks_descendants.py, test_intervention_world_construction_requires_compiled_graph.py, test_intervention_world_public_surface.py | PORT | causal-models EXTRACT |
| Deterministic observation world | WorldQuery.observe | test_intervention_world_distinct_from_observation.py | PORT | causal-models |
| SCM core (StructuralCausalModel, from_compiled_graph, evaluate, descendants) | internal | (via intervention + actual_cause tests) | PORT | causal-models + sympy-eval |
| Halpern actual cause (modified-HP AC1/AC2/AC3, witness, minimality) | `world.actual_cause` | test_actual_cause_suzy_billy.py, test_actual_cause_forest_fire.py, test_actual_cause_voting.py, test_actual_cause_minimality.py, test_actual_cause_witness_budget.py | PORT | causal-models |
| Worldline definition/inputs/result DTOs (from_document/to_dict/roundtrip) | `pks worldline create/show/list` | test_worldline.py, test_worldline_target_shape_validation.py, test_worldline_result_boundaries.py | DROP | propstore (charter doc) |
| Worldline runner (run_worldline, target resolution, override precedence, determinism) | `pks worldline run` | test_worldline.py, test_worldline_properties.py | PORT | propstore |
| Worldline resolution targets (override/preresolved/claim/conflict/derived/chain resolvers) | internal | test_worldline.py | PORT | propstore |
| Worldline staleness (is_stale, content-hash freshness) | `pks worldline refresh` | test_worldline.py, test_worldline_hash_width.py | PORT | propstore |
| Worldline content hash (stability contract) | internal | test_worldline_hash_width.py, test_worldline_hash_excludes_transient_errors.py, test_worldline_hash_repr_typed_failure.py | PORT | quire canonical_json |
| Worldline argumentation capture (claim_graph/aspic/atms/praf, stance deps) | `pks worldline run` | test_worldline_argumentation_multi_extension.py, test_worldline_praf.py | PORT | formal-argumentation + atms (also argumentation-bridge) |
| Worldline revision capture (one-shot expand/contract/revise) | `pks worldline run`; `pks world revision *` | test_worldline_revision.py, test_worldline_revision_event_capture.py, test_worldline_revision_snapshot_boundary.py | PORT (roundtrip DROP) | formal-belief-set (also belief-revision) |
| Worldline iterated revision (Darwiche-Pearl) | `pks world revision iterated-revise` | test_worldline_revision.py, test_worldline_revision_properties.py | PORT | formal-belief-set |
| Worldline IC merge (merge-point refusal, requires explicit mu) | `pks world revision iterated-revise` | test_worldline_ic_merge.py, test_worldline_ic_merge_properties.py, test_worldline_ic_merge_realization.py, test_worldline_revision_merge_parent_evidence.py | PORT | formal-belief-set |
| Worldline error visibility (typed capture errors not swallowed) | `pks worldline run/show` | test_worldline_error_visibility.py | PORT | propstore |
| Worldline result-type DTOs | serialized artifact | test_worldline_result_boundaries.py, test_worldline_target_shape_validation.py | DROP | propstore |
| Worldline CLI (show/list/diff/create/run/refresh/delete/build-journal/at-step) | `pks worldline *` | test_worldline.py, test_world_query_at_journal_step.py, test_world_query_at_journal_step_method.py | DROP (CLI) | propstore |
| Journal replay / at-step (replay_at_step, at_journal_step, fixture commit, cache) | `pks worldline at-step/build-journal` | test_world_query_at_journal_step.py, test_world_query_at_journal_step_method.py | PORT | quire history |
| Observatory evaluation report (evaluate_scenarios, content-hash stability) | `pks observatory run` | test_observatory.py | PORT (roundtrip DROP) | quire canonical_json (also render-cli-web O1) |
| Lazy CLI registration (world/worldline/observatory/materialize) | root `pks` | test_observatory.py | PORT (contract) | propstore |
| World layer boundary (one-way dependency) | architecture | test_world_layer_boundary.py | PORT (guard) | discipline |

### Slice: belief-revision
support_revision adapters over formal-belief-set (AGM/iterated/IC/entrenchment), fragility
(PROPSTORE-PROPER), sensitivity (over sympy-eval), epistemic process/history/policy.

| capability | user surface | gating tests | PORT/DROP | substrate |
|---|---|---|---|---|
| AGM expand | `pks world revision expand`; decide_expand | test_revision_adapter_expand_contract_revise.py, test_revision_operators.py, test_revision_properties.py, test_revision_formal_decision_reports.py | PORT | belief-set |
| AGM contract (full-meet + support incision) | `pks world revision contract` | test_revision_adapter_expand_contract_revise.py, test_revision_operators.py | PORT | belief-set + propstore incision |
| AGM revise (Levi identity) | `pks world revision revise` | test_revision_operators.py, test_revision_properties.py | PORT | belief-set |
| Iterated revision (Darwiche-Pearl lexicographic/restrained) | `pks world revision iterated-revise` | test_revision_adapter_iterated.py, test_revision_iterated_examples.py, test_revision_iterated.py | PORT | belief-set |
| Gardenfors entrenchment (formal + support-reason overrides) | `pks world revision entrenchment` | test_revision_entrenchment.py, test_revision_formal_entrenchment_boundary.py, test_revision_phase1.py | PORT | belief-set + propstore override |
| Entrenchment recompute after iterate (no stale ranking) | iterated_revise | test_iterated_revision_recomputes_entrenchment.py, test_revision_iterated.py | PORT | belief-set |
| Model-theoretic IC merge (sigma/max/gmax over belief profile) | journal IC_MERGE; decide_ic_merge | test_revision_merge_uses_ic_merge.py, test_revision_argumentation_views.py | PORT | belief-set merge kernel |
| IC-merge-required signal at storage merge points | iterated_revise refusal | test_revision_iterated.py | PORT | propstore scope |
| Spohn distance-ranked default state (Hamming) + ranking provenance=defaulted | `_distance_ranked_state` | test_revision_policy_provenance.py | PORT | belief-set + propstore tag |
| Formal projection bundle (atoms→alphabet bijection) + alphabet budget | `project_formal_bundle` | test_revision_adapter_projection.py, test_revision_adapter_budget.py | PORT | belief-set + anytime |
| Belief-base projection from BoundWorld (exact-support only) | `revision_base`, project_belief_base | test_revision_projection.py, test_revision_state.py, test_revision_assertion_identity.py, test_revision_phase1.py | PORT | propstore (labels/SituatedAssertion) |
| Minimal support incision (hitting-set, entrenchment-weighted, ceiling) | `stabilize_belief_base` | test_revision_operators.py, test_revision_properties.py | PORT | propstore + anytime |
| Revision input normalization (atom/str/mapping → BeliefAtom) | `normalize_revision_input` | test_revision_operators.py, test_revision_properties.py | PORT | propstore |
| Revision explanation builder (accepted/rejected + ranking rationale) | `pks world revision explain` | test_revision_explain.py | PORT | propstore |
| Epistemic-state → argumentation-view projection | `af_adapter.project_epistemic_state_argumentation_view` | test_revision_af_adapter.py, test_revision_argumentation_views.py | PORT | propstore (claim_graph inputs) (also argumentation-bridge, render) |
| Journal replay / dispatch (replay 1 operator) | `dispatch`, TransitionJournal.replay | test_revision_event_contract.py, test_revision_policy_provenance.py | PORT | propstore + belief-set |
| make/advance epistemic state | `make/advance_epistemic_state` | test_revision_iterated.py | PORT | propstore |
| BoundWorld revision delegation (architecture boundary) | world/bound.py | test_revision_bound_world.py, test_revision_phase1.py | PORT | propstore |
| App typed split report | revision app contract | test_revision_app_contract.py | PORT | propstore (also render) |
| Revision CLI workflow + IC merge payload | `pks world revision *` | test_revision_cli.py, test_revision_phase1_cli.py | DROP (CLI) + PORT | propstore |
| Fragility ranking orchestrator (collect/score/rank/interactions, top_k) | `query_fragility` | test_fragility.py | PORT | propstore over ARG/PROV/ATMS |
| Ranking policies (heuristic_roi/family_local/pareto) | `_apply_ranking_policy` | test_fragility.py | PORT | propstore |
| Conflict fragility score (grounded-extension delta) | `score_conflict` | test_fragility.py | PORT | formal-argumentation |
| Combine-fragility policy (top2/mean/max/product) | `combine_fragility` | test_fragility.py | PORT | propstore |
| Weighted epistemic score (witness/future ratio, out-sign correction) | `weighted_epistemic_score` | test_fragility.py | PORT | propstore |
| Support-derivative fragility (why-provenance partial derivative) | `support_derivative_fragility` | test_fragility.py | PORT | provenance-semiring |
| ATMS assumption interventions (concept_stability witnesses) | `collect_assumption_interventions` | test_fragility.py | PORT | atms + provenance |
| Missing-measurement (discovery) interventions | `collect_missing_measurement_interventions` | test_fragility.py | PORT | propstore |
| Ground-fact/grounded-rule/bridge-undercut interventions (DeLP/ASPIC heuristics) | `collect_*_interventions` | test_fragility.py | PORT | formal-argumentation + gunray |
| Intervention interaction detection (synergistic/redundant/mixed/independent) | `detect_interactions` | test_fragility.py | PORT | atms |
| imps_rev (DFQuAD support-revision attack impact) | `imps_rev` | test_fragility.py | PORT | argumentation.dfquad + doxa |
| opinion_sensitivity (Jøsang WBF expectation perturbation) | `opinion_sensitivity` | **NO direct test** (via fusion) | PORT | doxa.wbf — port-risk |
| Intervention typed-target validation (kind/family/payload, cost_tier, bounds) | `fragility_types.*` | test_fragility.py | DROP (guards PORT) | propstore |
| Local OAT sensitivity (sympy partial derivative + elasticity, ranked) | `query_sensitivity` | test_sensitivity.py, test_sensitivity_global_method_or_honest_naming.py | PORT | sympy-eval |
| Global Sobol sensitivity (Saltelli, variance decomposition) | `analyze_global_sensitivity` | test_sensitivity_global_method_or_honest_naming.py | PORT | sympy-eval |
| Parameterization eval (bare/Eq-solve/self-ref, typed status) | `propagation.evaluate_parameterization` | test_propagation.py | PORT | sympy-eval EXTRACT |
| Fragility investigation plan (report→plan, stable id) | `plan_fragility_investigation` | test_epistemic_process_manager.py | PORT (+DTO DROP) | propstore + quire hashing |
| Process manager queue/complete/replay (job lifecycle) | `EpistemicProcessManager` | test_epistemic_process_manager.py | PORT | propstore + quire hashing |
| Epistemic snapshot/state-snapshot roundtrip + stable hash + detach | `history.EpistemicSnapshot` | test_epistemic_history.py, test_epistemic_snapshot_detaches_state.py, test_revision_event_contract.py | DROP | quire hashing |
| TransitionJournal entry typed replay contract + chain integrity | `history.TransitionJournalEntry` | test_journal_entry_contract.py, test_epistemic_history.py | DROP (chain-integrity PORT) | quire hashing + propstore |
| Semantic snapshot diff/apply (acceptance/warrant/ranking/provenance/dependency deltas) | `diff/apply_epistemic_diff` | test_epistemic_history.py | PORT | propstore |
| Revision event/episode/result typed records + roundtrip | state.py | test_revision_event_contract.py | DROP | quire hashing |
| Revision explanation records coercion/roundtrip | explanation_types.py | (via test_revision_explain.py) | DROP | propstore |
| PolicyProfile + sub-policies content identity | `policies.PolicyProfile` | test_policy_governance.py | DROP (fields→charter) | quire hashing |
| Policy → situated-assertion emission | `policy_assertions` | test_policy_governance.py | PORT | propstore (SituatedAssertion) |
| scope_policy decorator (degrade/require on partial RevisionScope) | `scope_policy.scope_policy` | **NO dedicated test** (indirect) | PORT | propstore — port-risk |
| belief_set import-edge discipline (only via revision adapters) | architecture | architecture/test_belief_set_boundary_contract.py, test_revision_entrenchment.py, test_revision_iterated.py, test_revision_af_adapter.py | PORT (re-target) | discipline |
| belief_set/ic_merge/af_revision doc-citation guards | doc guards | test_belief_set_docs.py | DROP (re-target) | n/a |
| Retired-revision-package guard | retirement guard | test_revision_retirement.py | DROP (obsolete) | n/a |

### Slice: merge-conflict
conflict_detector, merge orchestration (3-way + partial-AF), relations/sameas/alignment,
probabilistic relations.

| capability | user surface | gating tests | PORT/DROP | substrate |
|---|---|---|---|---|
| C1 Parameter-claim value conflict (pairwise + Z3 partition + cross-class disjointness) | `detect_conflicts()` | test_conflict_detector.py, test_param_conflicts.py, test_parameter_z3_strictness.py, test_parameter_conflict_error_preservation.py | PORT | condition-ir; value-comparison |
| C2 Measurement-claim conflict (interval/value compat + population PHI_NODE) | `detect_conflicts()` | test_conflict_detector.py | PORT | value-comparison |
| C3 Equation-claim conflict (orientation-invariant) | `detect_conflicts()` | test_equation_conflict_status.py, test_equation_signature_role_invariance.py | PORT | eq-equiv CONSUME (also claim) |
| C4 Algorithm-claim conflict (AST compare + tier/similarity) | `detect_conflicts()` | test_algorithm_sympy_tier_not_conflict.py | PORT | ast-equiv CONSUME (also claim) |
| C5 Parameterization-derived conflict (single-hop + transitive fixpoint; unit normalization) | `detect_conflicts()`, `detect_transitive_conflicts()` | test_param_conflicts.py, test_parameter_conflict_unit_aware.py | PORT | sympy-eval; param-groups/walk; dimensions |
| C6 Condition→conflict-class classification (+context-lifted CONTEXT_PHI_NODE) | internal to detectors | test_conflict_detector.py, test_classify_pair_no_concept_fallthrough.py | PORT | condition-ir; condition_classifier; context_lifting |
| C7 Lifted-claim expansion (lifting rules, derivation dedupe, decision cache, synthetic collision guard) | `detect_conflicts(lifting_system=)` | test_conflict_orchestrator_isolation.py | PORT | context_lifting; condition-ir |
| C8 ConflictClaim/Record/Class models + from/to_payload + with_source_condition | detector I/O DTO | test_conflict_detector.py, test_comparison_source_no_synthetic_paper.py | DROP (with_source_condition semantics PORT) | quire charter |
| C9 Conflict-claim collection/grouping by concept/measure/signature | internal | test_conflict_detector.py | PORT (grouping) / DROP (coercion) | eq-equiv |
| M1 Repository merge framework (3-way diff, canonical groups no union-find, per-rival args, partial-AF) | `inspect_merge` → `pks merge inspect` | test_repo_merge_object.py, test_canonical_claim_groups_no_union_find.py, test_merge_regime_split_preserved.py, test_merge_corroboration_preserved.py | PORT | argumentation.partial_af CONSUME; conflict_detector |
| M2 Merge pair classification (_DiffKind over detect_conflicts + condition-set equality) | internal to M1 | test_merge_classifier.py, test_comparison_source_no_synthetic_paper.py | PORT | conflict_detector |
| M3 IntegrityConstraint (required/forbidden artifact-id, accepts/assert_satisfied) | param of build_merge_framework | **NO dedicated test** (via M1) | PORT (thin) | assignment-selection CONSUME — port-risk |
| M4 Two-parent merge commit (non-claim union, rival materialization, manifest, CAS) | `commit_merge` → `pks merge commit` | test_merge_classifier.py, test_merge_symmetry_non_claim_files.py, test_repo_merge_object.py, remediation/phase_1_crits/test_T1_1_merge_preserves_rivals.py, remediation/phase_7_race_atomicity/test_T7_2_merge_commit_expected_head.py | PORT | quire (CAS); families coerce |
| M5 Branch structured summary + structured merge candidates (sum/max/leximax over partial AFs) | library/world | test_structured_merge_projection.py, test_structured_merge_supports_preferred_stable.py | PORT | argumentation.partial_af CONSUME; aspic_bridge; structured_projection (also storage report) |
| M6 Merge framework report (skeptical/credulous, completion count, attack/ignorance surface) | payload of inspect/commit | test_merge_report.py, test_merge_witness_basis.py, test_merge_assertion_id_includes_provenance.py | PORT (thin) | argumentation.partial_af CONSUME |
| M7 MergeClaim typed surface (assertion-id from SituatedAssertion, provenance, semantic key) | DTO of M1/M4/M5 | test_merge_assertion_id_includes_provenance.py, test_materialized_claim_provenance_preserved.py | DROP (assertion-id logic PORT) | quire charter; SituatedAssertion (also claim, storage) |
| M8 MergeArgument/Framework/BranchSummary/Evidence records | DTO | (via M1/M5) | DROP | quire charter; argumentation |
| M9 ProvenanceWitness source basis | embedded carrier | test_merge_witness_basis.py | DROP (thin keep) | provenance-carrier |
| M10 Description-kind coreference merge (Dung clusters grounded/preferred/stable) | library/world | test_lemon_phase3_semantics.py, test_lemon_concept_documents.py | PORT | argumentation.dung — **belongs to concept-core lemon; merge/ re-export DROP** |
| R1 Stance summary over WorldStore (counts, vacuous tally, mean uncertainty) | render explanation | test_relation_analysis.py | PORT (thin) | WorldStore; relation_types; doxa |
| R2 Relation/stance/conflict row models + projection tables/query-plans | sidecar SQL | test_sidecar_relation_edge_projection.py, test_relation_concept_identity.py, test_schema_versioning_conflict.py, test_world_bound_conflicts_cache.py | DROP/VANISH | quire projections; doxa (opinion columns) |
| R3 Authored-stance sidecar compile w/ source/target quarantine diagnostics | build/compile | remediation/phase_2_gates/test_T2_2c_stance_source_quarantine.py, test_T2_2d_stance_target_quarantine.py, test_T2_2h_in_claim_stance_quarantine.py | PORT (row emission VANISHES) | quire references; diagnostics |
| R4 SameAs assertion document (graded identity vocab) | sameas family | test_sameas_family_schema.py | DROP | quire charter |
| R5 Concept alignment (classify_relation lemon-identity → attack/non-attack; partial-AF; align/decide/promote) — lives in `source/alignment.py` | `pks` source/concept alignment | test_alignment_default_classification.py, remediation/phase_6_extend/test_T6_1_alignment_ignorance_relation.py, test_source_promotion_alignment.py | PORT | argumentation.partial_af CONSUME; doxa; core/lemon (also source, render) |
| R6 Probabilistic relation records (opinion-bearing edges, RelationProvenance) | consumed by PrAF/claim_graph | test_praf_integration.py, test_praf_uncalibrated_explicit.py, test_argumentation_package_track_e.py, test_ws_f_aspic_bridge.py | PORT (thin DTO) | argumentation praf CONSUME; doxa |
| Layer boundary: storage does not import merge | architecture | remediation/phase_4_layers/test_T4_2_storage_does_not_import_merge.py | PORT | discipline |

### Slice: source-proposals-provenance
source/* lifecycle, importing/*, proposals + promotion, provenance carrier (named-graph on
git notes) + trusty/ni-uri, identity, micropublications, artifact codes/verification.

| capability | user surface | gating tests | PORT/DROP | substrate |
|---|---|---|---|---|
| Source branch init (mint source tag-uri, seed SourceDocument DEFAULTED trust + ni-uri ref) | `pks source init` | test_source_cli.py, test_source_promotion_alignment.py | PORT | quire git_store; uri |
| Source-local concept authoring/proposal | `pks source add-concepts/propose-concept` | test_source_propose.py | PORT | families, identity |
| Source-local claim authoring + validation (concept-ref/CEL/value-bounds) | `pks source add-claim/propose-claim` | test_source_claims.py, test_source_propose.py | PORT | cel-parser/z3; families (also claim) |
| Source-local justification/stance authoring | `pks source add-justification/add-stance` | test_source_relations.py | PORT | families |
| Reserved-namespace guard (source cannot mint canonical ids) | source writers | test_source_cannot_mint_canonical_ids.py | PORT | identity/logical_ids |
| Reference lowering (source-local handle → canonical FK; strip source-local fields) | claim_concepts/reference_indexes | test_source_claim_concept_rewrite.py, test_source_promote_properties.py | PORT | quire references; identity (also claim, concept) |
| Finalize (micropub-coverage gate, ref-integrity, artifact-code stamp, micropub compose, report) | `pks source finalize` | test_finalize_micropub_required.py, test_source_promotion_alignment.py | PORT | artifact_codes; families; identity/micropubs |
| Promotion (per-item blocking filter, concept resolution, immutable rebuild, atomic master commit, provenance note, promote-time trust calib) | `pks source promote` | test_promote_atomicity.py, test_promote_claim_immutability.py, test_promote_writes_provenance_note.py, test_source_promote_dangling_refs.py, test_source_promote_properties.py, test_source_promotion_alignment.py | PORT | quire head_bound_transaction; provenance; doxa |
| Blocked-claim projection rows (sidecar mirror of quarantined) | compile blocked projection | test_source_promotion_alignment.py, test_promote_atomicity.py | PORT | families/diagnostics |
| Source sync (export source-branch tree to papers) | `pks source sync` | test_source_promotion_alignment.py | PORT | quire iter_tree_files |
| Source status report (sidecar claim_core + diagnostics correlation) | `pks source status` | test_source_cli.py, test_source_list_and_context.py, test_cli_source_status.py | PORT+DTO | derived_store; families |
| Vocabulary reconciliation/alignment (lemon identity → Dung PAF → skeptical/credulous; decide/promote) | `align_sources` | test_source_promotion_alignment.py | PORT (bridge) | formal-argumentation; core/lemon; doxa (= merge R5) |
| Source registry / primary-branch concept match + paramgroup-merge preview | registry.py | test_source_promotion_alignment.py | PORT | families/concepts; param-groups |
| Stance proposal promotion (heuristic → canonical) | `pks proposal promote` | test_proposal_promotion.py, test_promote_stance_proposals_idempotency.py | PORT | quire family transaction (also argumentation) |
| Predicate proposal declare + promote | `pks proposal predicates declare/promote` | test_promote_predicates_proposals.py, test_proposal_predicates_family.py | PORT | families/rules+predicates |
| Rule proposal propose + promote (review-mode plan print) | `pks proposal propose-rules/promote-rules` | test_promote_rules_proposals.py, test_proposal_rules_family.py | PORT | families/rules (also render H6) |
| Shared planned-canonical-artifact transaction helper | `commit_planned_canonical_artifacts` | test_proposal_promotion.py | PORT | quire transaction |
| Proposal path discipline (no placeholder owner) | proposal path helpers | test_proposal_paths_no_placeholder_owner.py | PORT | quire references |
| Provenance named-graph carrier (typed Provenance/Witness, deterministic JSON-LD, status-rank composition, git-note read/write) | API; stamp-provenance | test_provenance_foundations.py | PORT | quire.notes; msgspec; doxa (fusion) |
| produced_by stamping (md/yaml frontmatter, idempotent) | `pks source stamp-provenance` | test_provenance.py | PORT | regex/YAML |
| Provenance semiring math (polynomial/homomorphism/derivative/nogoods/support/variables) | provenance/* | test_provenance_polynomial_properties.py, test_provenance_derivative_properties.py, test_provenance_nogoods_properties.py, test_provenance_atms_equivalence.py | CONSUME | provenance-semiring EXTRACT |
| why-provenance / projections (boolean_presence/derivation_count/tropical_cost/WhySupport) | provenance/projections.py | test_provenance_projection_properties.py, test_provenance_atms_equivalence.py | CONSUME+adapter | provenance-semiring + propstore id-binding |
| Typed provenance records (SourceVersion/License/ImportRun/ProjectionFrame/External*) — URI/hash invariants | provenance/records.py | test_provenance_records.py | PORT (invariants) / DROP (payload) | provenance-semiring |
| PROV-O JSON-LD export | provenance/prov_o.py | test_prov_o_export.py | PORT | pure dict projection |
| ni-URI byte primitive + verify (RFC6920 sha-256; sha1 rejected) + tag-uri minting + authority | uri.py, trusty.py, uri_authority.py | test_trusty_uri_verification.py, test_uri.py, test_uri_authority_validation.py | PORT | named-uri (EXTRACT weak or fold into quire) (also storage) |
| Micropublication content identity (canonical payload excludes id fields; ni-uri artifact_id; sha256 version_id) | families/identity/micropubs.py | test_micropub_identity_trusty_uri.py, test_micropub_trusty_verification.py, test_micropub_identity_consumes_wscm.py, test_micropub_identity_not_logical_handle.py | PORT | uri; quire hashing |
| Micropublication bundle compose (Clark: claims+evidence+assumptions+stance+provenance+source) | finalize._compose_source_micropubs | test_micropubs.py, test_micropublications_phase4.py, test_finalize_micropub_required.py | PORT (document DROP) | families/documents/micropubs |
| Micropublication sidecar projection + claim-FK + quarantine-on-dangling + first-writer dedupe | families/micropublications/declaration.py | test_micropubs.py, test_micropublications_phase4.py | PORT | quire projections |
| Micropub inspect/lift (render lifting decisions for target context) | `pks micropub list/show/lift` | test_micropubs.py | PORT | context_lifting/defeasibility |
| Cross-entity content identity (claim/concept/justification/stance artifact-id + version-id) | families/identity/* | (via test_source_*, test_import_repo, test_micropub_identity_not_logical_handle) | PORT | quire hashing/references |
| Artifact-code witness chain (Buneman where-pointer) | artifact_codes.py | test_source_promotion_alignment.py | PORT | quire hashing (also storage) |
| Claim-tree verification (recursive code check + origin ni-uri match + ATMS label serialize) | `pks verify tree` | **NO dedicated test** (also `test_verify_cli.py` is UNCLAIMED) | PORT | artifact_codes; uri; world/ATMS — port-risk |
| Typed import contract compiler (authored surface → SituatedAssertion + provenance; lens laws; equivalence-witness no identity collapse) | importing/machinery.py | test_import_machinery.py | PORT (payload DROP) | provenance/records; core/assertions |
| Committed-snapshot repository import (plan/commit, convergent, semantic-tree scope, ref rewrite, deletes, provenance note) | `pks import-repository` | test_import_repo.py | PORT | quire FamilyRegistry+transaction |
| Semantic-import normalization pipeline (concept/claim/stance batch normalizers, ref map, ambiguity warnings) | source/passes.py | test_import_repo.py | PORT | semantic_passes; identity |
| Source/import/machinery payload + Source*Document schemas | families/documents/* | (covered by source/import tests) | DROP | quire charters |

### Slice: storage-build-compile
Repository facade (thin), build/validate orchestration, sidecar cache-key + rebuild,
semantic-pass framework, contract manifest/drift, family registry (mostly vanishes),
snapshot/materialize, history, architecture import-linter rules.

| capability | user surface | gating tests | PORT/DROP | substrate |
|---|---|---|---|---|
| Repo init / store-only bootstrap (seed forms/concepts, no loose materialization) | `pks init` | test_init.py, test_semantic_family_registry.py | PORT | quire GitStore/Policy |
| Repo discovery / find walk-up + is_propstore_repo | Repository.find | **NO dedicated test** (indirect) | PORT | quire GitStore — port-risk |
| Repository facade (root/git/tree/families/snapshot/config accessors) | Repository | test_repository_artifact_boundary_gates.py | PORT (thin, mostly VANISHES) | quire stores |
| Git policy (author, master, gitignore prefixes/suffixes) | storage/git_policy.py | (via init/materialize + boundary gates) | PORT (config) | quire GitStorePolicy |
| Repository config doc (propstore.yaml → uri_authority) | Repository.config | test_uri.py, test_uri_authority_validation.py | PORT (parse) / DROP (doc) | quire DocumentStruct |
| Build pipeline orchestration (validate concepts→forms→claims→contexts, AUTHORED→CHECKED, CEL pre-pass, lints, sidecar, conflict/phi summary) | `pks build` | test_build_sidecar.py | PORT | quire derived_store; argumentation; world |
| Validate-only workflow (schema + AUTHORED pipelines, CEL invariant, no sidecar write) | `pks validate` | test_validate_claims.py | PORT | CEL+Z3; quire (also claim) |
| CEL structural-invariant pre-pass (reject structural concept in claim/context conditions) | compiler/workflows | test_validate_claims.py | PORT | cel_validation, cel_registry |
| Compilation context construction (CEL registry, concept registry, claim index) | compiler/context.py | **NO isolated test** (transitive) | PORT | cel_registry; forms; concepts — port-risk |
| Sidecar rebuild-on-source-change (content-hash: rev+tips+schema+pass+contract+pins+digest+env) | derived_build.world_sidecar_hash | test_build_sidecar.py (TestRebuildSkipping) | PORT | quire derived_store_content_hash |
| Sidecar file writer (create_all schema, populate all families, FTS, build-exception capture) | derived_build._build_sidecar_file | test_build_sidecar.py | PORT (rows DROP) | quire sqlite store |
| Sidecar build PLAN compilation (CheckedBundle → per-family rows + diagnostics) | derived_build_plan.compile_sidecar_build_plan | (via test_build_sidecar.py) | PORT (row DTOs DROP) | quire ProjectionRow |
| Semantic-pass framework (AUTHORED→NORMALIZED→BOUND→CHECKED runner; stage contracts; lazy registry; PassDiagnostic/Result; per-pass version) | API (semantic_passes/*) | **NO dedicated test** (via validate/build) | PORT (no quire analog) | pure — port-risk |
| Semantic-pass versioning feeds cache key | derived_build._semantic_pass_versions | (via TestRebuildSkipping) | PORT | — |
| Contract manifest emission (documents+registry+families+FKs+claim-type+stage+pass) | `pks contract-manifest` | test_contract_manifest.py | PORT (pass/stage/identity) / DROP (doc/family/FK bodies) | quire ContractManifest |
| Contract drift detection / version-bump gate | test/CI | test_contract_manifest.py | PORT | quire VersionId |
| Family registry + FK graph (28 families; placement/identity policies; reference keys; FK specs) | families/registry.py | test_semantic_family_registry.py | DROP bulk wiring / PORT (FK semantics, identity policy) | quire FamilyRegistry |
| Family registry helper queries (semantic/import families, roots, FKs, address_path) | families/registry.py | test_semantic_family_registry.py | DROP wiring / PORT discovery | quire families |
| Artifact identity policies (claim/concept artifact_id+version_id+canonical/normalize) | families/registry.py → families/identity | test_artifact_identity_policy.py, test_repository_artifact_boundary_gates.py | PORT (algorithm) | quire FamilyIdentityPolicy |
| Projection catalog (33 tables, schema v6) | families/projection_catalog.py | test_sidecar_projection_contract.py, test_projection_boundary_ws6.py, test_sidecar_sqlite_runtime_contract.py, test_sidecar_projection_fts_contract.py, test_sidecar_projection_vec_contract.py | DROP/VANISH | quire ProjectionSchema |
| Build-diagnostics projection + quarantine writer (try_write/quarantine; build-not-render discipline) | families/diagnostics/declaration.py | (via test_build_sidecar.py) | PORT (discipline) / DROP (table) | quire ProjectionTable |
| Authoring lints (Unknown_ slug, missing description/strength, undercut target, placeholder page; --strict-authoring) | families/diagnostics/authoring_lints.py | test_build_sidecar.py | PORT | none |
| Semantic artifact-code hashing (canonical-JSON sha256; claim binds source+justification+stance codes) | artifact_codes.py | test_validate_claims.py, test_repository_artifact_boundary_gates.py | PORT (algorithm) | quire canonical_json_sha256 (also source) |
| Artifact-code verification + claim-tree walk (ATMS label serialize, ni-URI origin verify) | `pks verify` → artifact_verification.py | **NO dedicated test** | PORT | world WorldQuery; core.labels; uri — port-risk |
| ni-URI / tag-URI / tagging-authority (RFC 6920/4151) | uri.py, uri_authority.py | test_uri.py, test_uri_authority_validation.py | PORT | pure (named-uri EXTRACT candidate) (= source) |
| Repository snapshot (branch taxonomy paper/source/agent/hypothesis/workspace) | storage/snapshot.py | test_repository_artifact_boundary_gates.py | PORT | quire GitStore |
| Materialize (project snapshot→loose files, clean stale, conflict detect, head-bound txn) | `pks materialize` | test_init.py | PORT | quire GitStore.materialize |
| History log/diff/show/checkout (+sidecar rebuild from historical commit) | `pks log/diff/show/checkout` | test_repository_history_reports.py | PORT | quire git log; derived_build |
| Architecture import-linter / boundary rules (storage facade, no cli→production, shallow owners, forbidden symbols) | CI/test | architecture/test_repository_artifact_boundary_gates.py, test_import_boundaries.py, test_import_linter_negative.py, test_forbidden_symbols.py, test_semantic_family_registry.py | PORT (all) | import-linter (test_import_boundaries also claimed by source) |

### Slice: render-cli-web
Presentation: render policy, claim/concept/neighborhood views, repository overview, web
routes + accessibility, CLI shell, graph export, observatory/world-render surfaces.

| capability | user surface | gating tests | PORT/DROP | substrate |
|---|---|---|---|---|
| R1 Render policy construction + normalize (backend/strategy/semantics/decision/pessimism/praf/include-drafts/blocked/show-quarantined) | every view; CLI flags; web params | test_app_rendering.py, test_cli_render_policy_flags.py, test_render_policy_filtering.py, test_render_policy_opinions.py | PORT (RenderPolicyValidationError) | world.RenderPolicy (also world slice) |
| R2 Claim view per-field STATE machine (known/unknown/vacuous/underspecified/blocked/missing/not_applicable) + NL sentences | `pks claim show`; web | test_claim_views.py, test_render_policy_direct_claim.py, test_render_contracts.py, test_web_claim_routes.py | PORT | propstore (also claim) |
| R3 Claim list/search summary rows (value/condition/concept display; status; query match) | `pks claim list/search`; web | test_claim_views.py, test_web_claim_index_routes.py, test_render_policy_filtering.py | PORT | propstore |
| R4 Concept view STATE machine | `pks concept show`; web | test_concept_views.py, test_render_policy_concept.py, test_web_concept_routes.py | PORT | propstore (also concept-core) |
| R5 Concept list/search reports (domain/status filter; ConceptSearchSyntaxError) | `pks concept list/search/categories`; web | test_concept_views.py, test_web_concept_index_routes.py | PORT | propstore |
| R6 Repository overview report (KB stats / reasoning inventory) | `pks status`; web `/` | test_app_repository_overview.py, test_web_index_route.py | PORT | propstore |
| R7 Semantic neighborhood report (focus claim; supporters/attackers; states; NL sentences). **Only focus_kind=claim implemented**; others raise Unsupported | `pks claim neighborhood`; web | test_neighborhoods.py, test_render_policy_neighborhood.py, test_web_neighborhood_routes.py | PORT | propstore |
| R8 JSON report serialization (json_ready; JsonReportMixin.to_json) | every web .json; CLI --json | (via web .json route tests), test_render_contracts.py | DROP wiring (PORT to_json content) | json_types VANISHES |
| W1 Web route registry + content negotiation (HTML/JSON, error→title/status 400/404/409, limit 1..500) | FastAPI routes; `pks web` | test_web_skeleton.py, test_web_request_float_boundary.py, test_web_revision_readonly.py, test_cli_web.py | PORT | propstore |
| W2 Web read-only revision endpoint (/world/revision/base.json) | web | test_web_revision_readonly.py | PORT | propstore over belief-set |
| W3 `pks web` serve (--host/--port/--insecure/--open; refuses public bind without --insecure) | CLI | test_cli_web.py, test_pks_web_insecure_flag.py | PORT | propstore |
| W4 Web accessibility (HTML pages, AT facts) | web HTML | test_web_accessibility.py, test_web_demo_fixture.py | PORT | propstore html |
| C1 pks root lazy CLI group (quickstart vs advanced, status→world status, forms→form alias, -C, --traceback, expected-error rendering) | CLI root | test_cli.py, test_cli_layout.py, test_cli_error_rendering.py | PORT | propstore |
| C2 CLI→owner discipline (no CLI flag shapes in owner errors; app emits no CLI payloads) | arch gate | test_app_layer_no_cli_payloads.py, test_no_cli_flags_in_owner_errors.py, test_cli_compiler_rendering.py | PORT | propstore |
| G1 Knowledge graph export (nodes concept/claim, conflicted=red; edges colored; group/binding scoping) | `pks world export-graph` | test_graph_export.py, test_graph_build.py, test_core_graph_types.py | PORT | propstore over world store |
| G2 Graph DOT render (graphviz) + JSON dict render | `pks world export-graph --format dot/json` | test_graph_export.py | PORT | propstore |
| O1 Observatory fixtures run | `pks observatory run` | test_observatory.py | PORT | propstore (owner world; also here) |
| O2 World resolution/derive/extensions/explain/algorithms render surfaces | `pks world resolve/derive/...` | test_world_query.py, test_apply_decision_criterion_provenance.py, test_render_time_filtering.py, test_praf_uncalibrated_explicit.py | PORT | propstore bridges + render (owner world) |
| O3 Worldline materialized query artifacts (render surface) | `pks worldline *` | test_world_query_at_journal_step.py, test_world_query_at_journal_step_method.py, test_revision_app_contract.py, test_revision_argumentation_views.py | PORT | propstore (owner world/belief) |
| Misc CLI (source status render, review-no-commit) | `pks source status` | test_cli_source_status.py, test_cli_review_no_commit.py | PORT | propstore |

### Slice: heuristic-embeddings
Heuristic analysis layer (proposals only): embeddings/similarity, LLM stance classify,
relate orchestration, calibration (metrics EXTRACT; corpus/categorical PROPSTORE),
source-trust heuristic, predicate/rule extraction.

| capability | user surface | gating tests | PORT/DROP | substrate |
|---|---|---|---|---|
| E1 Embedding generation via litellm (batch, content-hash skip, float32 blob, dimension capture, progress) | `pks claim/concept embed` | test_embed_operational_error.py, remediation/phase_2_gates/test_T2_3c_embedding_restore_diagnostics.py, test_no_embedding_key_collision.py | PORT | adapter over quire vec |
| E2 Embedding TEXT representation (claim: summary>statement>...; concept: canonical+aliases+definition) | drives E1/E3 | test_no_embedding_key_collision.py | PORT | propstore core/embeddings |
| E3 Similarity search top-k (distance-ranked, self-excluded) | `pks claim/concept similar` | test_relate_*.py, test_embed_operational_error.py | PORT | adapter over quire vec |
| E4 Multi-model AGREE / DISAGREE (intersection / symmetric-diff) | `pks claim/concept similar --agree/--disagree` | **NO dedicated test** (via relate/embed) | PORT | adapter over quire vec — port-risk |
| H1 LLM stance classification (directional forward+reverse independent, prompt, enrichment gating, JSON parse+shape) | `pks claim relate` | test_classify.py, test_classify_forward_reverse_independent.py, test_classify_no_silent_fallback.py, test_classify_pair_no_concept_fallthrough.py, remediation/phase_3_ignorance/test_T3_1a/1b/1c | PORT | propstore (proposals only) |
| H2 Honest-ignorance discipline (classifier failure/missing-confidence/strength/base-rate → ABSTAIN + vacuous Opinion + provenance op) | same as H1 | test_classify_no_silent_fallback.py, remediation T3_1a/1b/1c, remediation/phase_3_ignorance/test_T3_1d_malformed_json_no_reverse_stance.py | PORT | doxa + provenance |
| H3 Relate orchestration (dedup pairs, shared-concept, relate_claim/relate_all async, perspective isolation) | `pks claim relate` (bulk) | test_relate_async.py, test_relate_bulk.py, test_relate_dedup.py, test_relate_opinions.py, test_relate_perspective_isolation.py, test_relate_wbf.py | PORT | propstore (also argumentation-bridge stance authoring) |
| H4 Source-trust heuristic consensus (derive_source_trust(prior, chain_opinion)) | workflow | test_source_trust.py, test_source_trust_argumentation.py, remediation/phase_3_ignorance/test_T3_4_source_trust_heuristic_consensus.py | PORT | doxa (also argumentation-bridge calibration, source) |
| H5 Predicate extraction proposals (LLM → PredicateDeclaration proposal) | `pks proposal predicates declare/promote` | **NO dedicated test** (rule sibling only) | PORT | propstore (proposals) — port-risk |
| H6 Rule extraction proposals (LLM → DeLP rules, predicate-registry gating, rejections, dry-run, selective promote) | `pks proposal propose-rules/promote-rules` | test_cli_propose_rules_dry_run.py, test_cli_propose_rules_help.py, test_cli_propose_rules_with_mocked_llm.py, test_cli_promote_rules_selective.py, test_cli_promote_rules_unknown_id.py | PORT | propstore (proposals) (also source) |
| K1 Calibration METRICS (TemperatureScaler golden-section NLL, ECE Guo2017, Brier, log_loss) | library; runs at promote | test_calibrate.py, test_calibrate_brier_and_log_loss.py, test_trust_calibration_runs_at_promote.py | PORT | calibration EXTRACT (also argumentation-bridge) |
| K2 CorpusCalibrator (percentile/CDF, effective-sample-size, to_opinion via from_probability; CALIBRATED provenance) | classify enrichment; promote | remediation/phase_3_ignorance/test_T3_2_corpus_calibrator_provenance.py, test_calibrate.py | PORT | over doxa + provenance |
| K3 categorical_to_opinion (strong/moderate/weak/none → Opinion or BaseRateUnresolved; CategoryPrior; counts) | classify strength path | test_calibrate.py, test_classify.py, test_sidecar_calibration_counts_projection.py | PORT | doxa + provenance |
| K4 calibration_counts sidecar projection ((pass,cat)→(correct,total)) | build/promote | test_sidecar_calibration_counts_projection.py, test_trust_calibration_runs_at_promote.py | PORT | quire sidecar |
| Heuristic package layout | architecture | test_heuristic_package_layout.py | PORT | discipline |

---

## B. CLI command tree (`pks`)

Root group `pks` (`propstore/cli/__init__.py`, `_LazyCLIGroup`, lazy `_COMMANDS` registry).
Global options: `-C/--directory`, `--traceback` (env `PKS_TRACEBACK=1`). Quickstart-visible
set = `_QUICKSTART_COMMANDS`; rest under `pks advanced`. Synthetic: `pks status` → `world
status`; alias `forms` → `form`. Shared render-policy flags
(`claim_render_policy_options`): `--include-drafts`, `--include-blocked`, `--show-quarantined`.

```
pks
├── init                       (cli/init.py)
├── build                      (cli/compiler_cmds.py)
├── validate                   (cli/compiler_cmds.py)
├── export-aliases             (cli/compiler_cmds.py)
├── status  [-> world status]  (cli/world/query.py)
├── log / diff / show / checkout   (cli/history_cmds.py)
├── merge
│   ├── inspect
│   └── commit
├── verify
│   └── tree
├── web                        (--host --port --insecure --open)
├── contract-manifest          (cli/contracts.py)
├── import-repository          (cli/repository_import_cmd.py)
├── materialize                (cli/materialize.py)
├── observatory
│   └── run
│
├── claim                      (group)
│   ├── show / list / search / neighborhood
│   ├── compare
│   ├── embed / similar [--agree --disagree --top-k --model]
│   ├── relate
│   └── validate / validate-file / conflicts
│
├── concept                    (group)
│   ├── align / query / decide / promote
│   ├── search / list / categories / show
│   ├── embed / similar [--agree --disagree]
│   └── add / alias / rename / deprecate / link / qualia-add /
│       description-kind / proto-role / add-value
│
├── context                    (group)
│   ├── add / list / show / remove / search
│   └── lifting
│       └── list / show / add / update / remove
│
├── form  [alias: forms]
│   └── list / search / show / add / remove / validate
│
├── grounding
│   └── status / show / query / arguments / explain
│
├── micropub
│   └── list / show / lift
│
├── predicate
│   └── list / show / add / remove
│
├── proposal
│   ├── promote
│   ├── propose-rules / promote-rules
│   └── predicates
│       └── declare / promote
│
├── rule
│   ├── list / show / add / remove
│   └── superiority
│       └── add / list / remove
│
├── source
│   ├── init / finalize / promote / status / list / sync / stamp-provenance   (lifecycle.py)
│   ├── write-notes / write-metadata          (authoring.py)
│   ├── add-concepts / add-claim / add-justification / add-stance  (batch.py)
│   └── propose-concept / propose-claim / propose-justification / propose-stance  (proposal.py)
│
├── world                      (group)
│   ├── status / query / bind / explain / algorithms   (query.py)
│   ├── derive / resolve / extensions                  (reasoning.py)
│   ├── hypothetical / chain / export-graph / sensitivity / fragility / check-consistency  (analysis.py)
│   ├── atms
│   │   └── status / context / verify / futures / why-out / stability / relevance / interventions / next-query
│   └── revision
│       └── base / entrenchment / expand / contract / revise / explain / iterated-state / iterated-revise
│
└── worldline                  (group)
    ├── show / list / diff      (display.py)
    ├── build-journal / at-step (journal.py)
    ├── create / run / refresh  (materialize.py)
    └── delete                  (mutation.py)
```

Note: `adjudicate` agent workflow named in the original task is **CONFIRMED ABSENT** — no
command/module/test/markdown in the reference (argumentation-stances-flags.md).

---

## C. Coverage

- **Total test files (master `_all_test_files.txt`):** 527
- **Claimed (deduped union, `_claimed_test_files.txt`):** 410
  - present in master: **375**
  - outside master (remediation/ tree + 2 stale names): **35** (see §D)
- **UNCLAIMED master files (no area claimed):** **152** = 140 `test_*.py` + 12 infra/helper

### UNCLAIMED `test_*.py` — coverage gaps to assign (140), grouped by inferred owning slice

**argumentation-bridge (21):** test_af_revision_no_stable_distinct_from_empty_stable.py,
test_af_revision_postulates.py, test_base_rate_resolution.py, test_consensus_clamp_consistency.py,
**test_core_analyzers.py** (the real AF/PrAF assembly — high priority), test_dfquad.py,
test_dfquad_attack_support_per_paper_contract.py, test_exp_sum_under_reals.py,
test_from_probability_n_one_round_trip.py, test_ic_postulate_coverage.py,
test_log_product_under_positive_reals.py, test_p_heavy.py, test_p_mara_gate.py,
test_pignistic_vs_smets_kennes_1994.py, test_pls_property.py,
test_sqrt_square_under_nonnegative_reals.py, test_toy_dp.py, test_treedecomp.py,
test_treedecomp_differential.py, test_wbf_vs_van_der_heijden_2018_def_4.py, test_why_support_subsumes.py

**argumentation kernel-pins (architecture, 19):** all 17 architecture/test_argumentation_pin_*.py
(aba_adf, asp_literal_validity, caf, dung_extensions, dynamic, enforcement, epistemic, gradual,
iccma_adapter, ideal_admissibility, partial_skeptical, rule_collision, setaf, state_lazy,
vaf_completion, vaf_ranking, z_continuous) + architecture/test_import_linter_negative.py +
architecture/test_no_local_agm_logic.py. (These verify the CONSUMED formal-argumentation kernel
surface stays wired; argumentation-stances flagged them as "kernel-pin / CONSUME" but did not list
them in its CLAIMED set.)

**storage-build-compile (38):** test_T1_4_materialize_atomicity.py, test_T1_7_build_repository_propagates_sidecar_errors.py,
test_authoring_roundtrip_contract.py, test_branch_head_cas_matrix.py, test_branch_head_cas_properties.py,
test_canonical_json_single_source.py, test_cas_no_silent_retry.py, test_cas_rejection_no_orphan_rows.py,
test_codex5_sidecar_cache_derived_invalidation.py, test_doc_drift_clean.py, test_document_schema.py,
test_fixture_schema_parity.py, test_generated_schema_freshness.py, test_git_backend.py,
test_head_bound_transaction_primitive.py, test_knowledge_path.py, test_layered_contract_covers_six_readme_layers.py,
test_literal_keys.py, test_mapping_boundary_failures.py, test_no_old_data_shims.py,
test_no_process_streams_in_owners.py, test_no_typed_dicts.py, test_no_unbounded_quire_commit.py,
test_project_init.py, test_property_marker_discipline.py, test_quire_boundary.py, test_quire_consumer_contracts.py,
test_repo_branch.py, test_repo_snapshot.py, test_required_schema_completeness.py, test_review_regressions.py,
test_sidecar_alias_projection.py, test_sidecar_contexts.py, test_sidecar_grounded_facts.py,
test_sidecar_source_projection.py, test_transaction_commit_sha_lifetime.py, test_validator.py,
test_workstream_q_cas_done.py

**cross-cutting workstream-gate (19):** test_workstream_{a,agm,b,c,cm,d,e,f,g,h,i,j2,j,k,l,m,n1,n2,p}_done.py
(per-workstream "done" acceptance gates spanning multiple slices; assign per the workstream's domain)

**context-grounding-defeasibility (10):** test_core_justifications.py, test_gunray_boundary_ws6.py,
test_gunray_integration.py, test_justification_rule_kind_validated.py, test_propose_predicates_lifecycle.py,
test_propose_rules_lifecycle.py, test_propstore_rule_kind_widened.py, test_workstream_o_ast_done.py,
test_ws7_grounding_completion.py, test_ws_o_ast_integration.py

**source-proposals-provenance (8):** test_compose_provenance_causal_order.py,
test_extraction_provenance_aware_timestamps.py, test_local_handle_collision_blocks_commit.py,
test_no_derive_source_document_trust.py, test_no_privileged_namespace.py, test_no_truncated_identity.py,
test_polynomial_provenance_preserved_through_combine.py, **test_verify_cli.py** (the verify_claim_tree gate)

**world-atms-worldline (8):** test_capture_journal.py, test_chain_query_enum_discipline.py,
test_labelled_core.py, test_labels_properties.py (core/labels.py = atms substrate),
test_replay_determinism_actually_replays.py, test_value_resolver_consensus_with_abstention.py,
test_value_resolver_failure_reasons.py, test_value_status_surface.py (value_resolver — world flagged thin coverage)

**claim (6):** test_algorithm_free_variable_locals.py, test_algorithm_stage_types.py,
test_situated_assertion_codec.py, test_situated_assertion_refs.py, test_situated_assertions.py,
test_structural_assertion_conversion.py

**concept-core (4):** test_alias_collision_rejected.py, test_bridgman_pi_signal_propagation.py,
test_bridgman_pin_post_deletion.py, test_bridgman_signal_propagation.py

**render-cli-web (3):** test_log_cli.py, test_property.py, test_reasoning_demo_cli.py

**belief-revision (2):** test_scope_policy.py (the scope_policy decorator gate),
test_support_realization_postulates.py

**UNTRIAGED (2):** test_dedup_pairs_preserves_mirror.py (likely heuristic-embeddings relate),
test_verdict_renamed.py (likely a rename/contract guard — drop candidate)

### UNCLAIMED infra/helper (12 — not gating tests, expected unclaimed)
__init__.py, architecture/__init__.py, atms_helpers.py, builders.py, conftest.py,
family_helpers.py, fixtures/__init__.py, fixtures/journal.py, git_store_helpers.py,
intervention_world_helpers.py, sidecar_schema_helpers.py, support_revision/__init__.py.
(Plus claimed-but-helper files already in the union: sqlite_argumentation_store.py,
web_demo_fixture.py, ws_k2_cli_helpers.py, ws_l_merge_helpers.py,
support_revision/formal_realization_helpers.py, support_revision/revision_assertion_helpers.py.)

### Multi-claimed master files (75) — resolved owners

Format: file :: claiming areas → **OWNER** (rationale).

- test_render_policy_concept.py :: concept-core, render-cli-web, world → **render-cli-web** (concept/world also-exercise)
- test_render_policy_direct_claim.py :: claim, render, world → **render-cli-web**
- test_render_policy_filtering.py / _neighborhood / _opinions / test_render_time_filtering.py / test_render_contracts.py :: render+world(+others) → **render-cli-web**
- test_world_query.py / test_world_query_at_journal_step.py / _method.py :: render, world → **world-atms-worldline**
- test_observatory.py :: render, world → **world-atms-worldline**
- test_claim_views.py :: claim, render → **render-cli-web**
- test_web_claim_routes.py / _index_routes.py :: claim, render → **render-cli-web**
- test_web_concept_routes.py / _index_routes.py :: concept-core, render → **render-cli-web**
- test_concept_views.py :: concept-core, render → **render-cli-web** (state machine is render; concept-core owns the model)
- test_calibrate.py / test_calibrate_brier_and_log_loss.py / test_sidecar_calibration_counts_projection.py :: argumentation, render → **heuristic-embeddings** (K1/K3/K4)
- test_trust_calibration_runs_at_promote.py :: argumentation, render → **heuristic-embeddings** (also source promote)
- test_source_trust.py / test_source_trust_argumentation.py :: argumentation, render, source → **argumentation-bridge** (calibrate-source-trust = AF→opinion; source owns the promote write)
- test_relate_async/_bulk/_dedup/_opinions/_perspective_isolation/_wbf.py :: argumentation, render → **heuristic-embeddings** (relate orchestration H3; argumentation owns stance-proposal authoring)
- test_promote_stance_proposals_idempotency.py :: argumentation, source → **source-proposals-provenance**
- test_claim_and_stance_document_enums.py :: argumentation, claim → **claim** (stance vocab DROP)
- test_defeasibility_aspic_integration.py :: argumentation, context → **context-grounding-defeasibility** (CKR owns; injects at aspic boundary)
- test_grounder_default_returns_arguments.py :: argumentation, context → **context-grounding-defeasibility**
- test_defeasible_conformance_tranche.py :: concept-core(false-match "conformance"), context → **context-grounding-defeasibility**
- test_atms_cel_semantic_equality.py :: claim, world → **world-atms-worldline**
- test_algorithm_sympy_tier_not_conflict.py / test_equation_conflict_status.py / test_equation_signature_role_invariance.py / test_parameter_conflict_error_preservation.py / test_parameter_z3_strictness.py :: claim, merge → **merge-conflict** (conflict detection; claim owns the comparator primitive)
- test_parameter_conflict_unit_aware.py :: claim, concept-core, merge → **merge-conflict**
- test_canonical_claim_groups_no_union_find.py :: claim, merge → **merge-conflict**
- test_value_comparison_units.py :: claim, concept-core → **claim** (value_comparison glue; concept-core also-exercises units)
- test_merge_symmetry_non_claim_files.py :: claim(name-only), merge → **merge-conflict**
- test_lemon_phase3_semantics.py / test_lemon_concept_documents.py :: concept-core, merge → **concept-core** (M10 coreference belongs to lemon)
- test_relation_concept_identity.py :: concept-core, merge → **merge-conflict** (relations R2)
- test_classify_pair_no_concept_fallthrough.py :: concept-core, merge, render → **heuristic-embeddings** (classify H1; merge classify_pair also)
- test_merge_classifier.py :: merge, render → **merge-conflict**
- test_alignment_default_classification.py :: merge, render → **merge-conflict** (R5; lives in source/)
- test_argumentation_package_track_e.py :: argumentation, merge → **argumentation-bridge** (kernel pin)
- test_praf_integration.py :: argumentation, merge → **argumentation-bridge**
- test_praf_uncalibrated_explicit.py :: argumentation, merge, render → **argumentation-bridge**
- test_ws_f_aspic_bridge.py :: argumentation, merge → **argumentation-bridge**
- test_worldline_argumentation_multi_extension.py / test_worldline_praf.py :: argumentation, world → **world-atms-worldline**
- test_revision_argumentation_views.py :: argumentation, belief, render → **belief-revision**
- test_revision_app_contract.py :: belief, render → **belief-revision**
- test_revision_formal_decision_reports.py / test_revision_formal_entrenchment_boundary.py :: belief, concept-core(false "form" match) → **belief-revision**
- test_world_bound_conflicts_cache.py :: merge, world → **world-atms-worldline**
- test_structured_merge_projection.py / test_structured_merge_supports_preferred_stable.py :: merge, storage → **merge-conflict** (uses structured_projection from argumentation-bridge)
- test_materialized_claim_provenance_preserved.py :: claim, merge, storage → **source-proposals-provenance** (promote provenance invariant)
- test_promote_claim_immutability.py :: claim, source → **source-proposals-provenance**
- test_snapshot_to_claim_ids.py :: claim, storage → **storage-build-compile**
- test_validate_claims.py :: claim, storage → **storage-build-compile** (validate workflow; claim owns CEL primitives)
- test_source_claim_concept_rewrite.py :: claim, concept-core, source → **source-proposals-provenance**
- test_source_claims.py :: claim, source → **source-proposals-provenance**
- test_source_promotion_alignment.py / test_source_relations.py :: merge, source → **source-proposals-provenance**
- test_web_concept_index_routes.py (dup with above) → **render-cli-web**
- architecture/test_import_boundaries.py / architecture/test_import_linter_negative.py :: source, storage → **storage-build-compile**
- support_revision/formal_realization_helpers.py :: belief, concept-core(false match) → **belief-revision** (helper)
- test_T2_2h_in_claim_stance_quarantine.py :: claim, merge → **merge-conflict** (stance quarantine R3)

---

## D. Capabilities with NO dedicated gating test (port-risk — write tests during rewrite)

1. **Concept mutation CLI** (`pks concept add/alias/rename/deprecate/link/qualia-add/description-kind/proto-role/add-value`; CEL-cascade rename) — concept-core. Exercised only via alignment/workflows/validation.
2. **verify_claim_tree** / `pks verify tree` + ni-URI origin matching — source-proposals-provenance & storage. (`test_verify_cli.py` exists but is UNCLAIMED — wire it.)
3. **Semantic-pass framework** runner/registry (AUTHORED→CHECKED) — storage-build-compile. No `test_semantic_pass*`.
4. **CompilationContext construction** (compiler/context.py) — storage-build-compile. Transitive only.
5. **Repo discovery / find walk-up** (`Repository.find`, `is_propstore_repo`) — storage-build-compile.
6. **recency / sample_size resolution** strategies — world-atms-worldline. Only via worldline/render-policy.
7. **world check-consistency** (`world/consistency.py`) — world-atms-worldline.
8. **value_resolver derive math** (`ActiveClaimResolver`, algorithm-equivalence) — world. (`test_value_resolver_*` exist but UNCLAIMED — wire them.)
9. **E4 AGREE/DISAGREE** multi-model embedding set logic — heuristic-embeddings.
10. **H5 predicate extraction** proposals (`propose_predicates_for_paper`) — heuristic-embeddings.
11. **M3 IntegrityConstraint** (merge_classifier) — merge-conflict. Only via build_merge_framework.
12. **opinion_sensitivity** (fragility_scoring) — belief-revision. Only via WBF fusion.
13. **scope_policy decorator** — belief-revision. (`test_scope_policy.py` exists but UNCLAIMED — wire it.)

---

## E. Substrate decisions (reconciled across all reports + SPEC)

**CONSUME (package exists; delete local dup):**
- doxa ← opinion.py (768L, 13 importers) — STRONGEST finding, flagged by 4 scouts; delta is provenance carriers → thin propstore opinion shim. (argumentation, belief, merge, render all agree.)
- assignment-selection ← world/assignment_selection_merge.py — keep thin CEL/Z3 IntegrityConstraint + anytime adapter; consume sigma/max/gmax. (world + merge M3.)
- eq-equiv ← equation_parser.py + equation_comparison.py — keep ConflictClaim adapter. (claim + merge C3.)
- human-to-sympy ← sympy_generator.py. (claim.)
- (already pinned per SPEC §A) quire, formal-argumentation, formal-belief-set, bridgman, cel-parser, ast-equiv, gunray.

**EXTRACT (new substrate package):**
- condition-ir [CLEAN, HIGH] = core/conditions/* + cel_types.py (CEL ConditionIR + Z3/SQL/python/estree backends + ConditionSolver). Only seam: ir.py's ConceptId → str brand. (claim slice.)
- provenance-semiring [~470L] = provenance/{polynomial,homomorphism,derivative,nogoods,support,projections,variables}(+records,prov_o optional). Unlocks atms labels. (source slice.)
- atms [HIGH] = world/atms.py (2944L) + core/labels.py (394L), generalized over a label semiring. (world slice.)
- causal-models [MEDIUM ~644L] = world/{scm,intervention,actual_cause}. (world slice.)
- calibration [CLEAN] = pure-metrics half of heuristic/calibrate.py (TemperatureScaler/ECE/Brier/log_loss). CorpusCalibrator + categorical_to_opinion STAY propstore. (heuristic slice — extract boundary runs through the module.)
- sympy-eval [CLEAN ~177L] = propagation.py. (belief slice / consumed by world+merge.)
- (weak/optional) named-uri = uri.py + uri_authority.py (RFC6920/4151) — EXTRACT or fold into quire identity. unit-convert (dimensions Pint layer) — or keep in propstore over bridgman. (source/storage + concept.)

**VANISH (under quire charters; not ported, not consumed):**
- families/documents/* (~1366L DocumentStruct + to_payload)
- families/projection_catalog.py + bulk of families/registry.py (per-family ArtifactFamily/placement/FK/ref wiring)
- most of contracts.py emission (doc/family/FK bodies)
- json_types.py, families/addresses.py
- the distributed symptom mass: ~347 coerce_*, ~283 to_payload, ~1216 Document refs.

**DEAD (delete):**
- form_utils.py (dup of families/forms/stages — but 2 BEH tests import from it; repoint imports on rewrite).
- empty/pycache-only dirs: families/predicates, families/stances, families/merge, families/source_alignment, families/meta.
- world/__pycache__ orphans: assignment_selection_policy, conflict_projection, graph_projection, journal_projection.
- merge/description_kinds.py (thin re-export of core/lemon/description_kinds.py — delete, M10 moves with lemon).
- Stale pyc with no source: test_opinion_adapter.py, test_realization.py (confirmed nonexistent).

---

## F. Cross-report conflicts / discrepancies flagged

1. **Master list excludes remediation/.** `_all_test_files.txt` (527) has zero `remediation/` entries, but reports cite ~33 real `tests/remediation/phase_*/test_T*.py` files (listed in `_claimed_test_files.txt` with their `remediation/...` prefix). These are claims against files outside the master enumeration — the master glob never recursed into `remediation/`. The 152 "unclaimed" count is therefore strictly within the 527; the remediation tree is uncounted by both. Recommend re-globbing to include `remediation/` before treating coverage as complete.
2. **structured_projection.py owner.** storage-compiler-build report inventoried it; argumentation-stances and merge both treat it as an argumentation BRIDGE (SPEC §E). → owner **argumentation-bridge** (storage report itself flags the mis-bucket).
3. **decision-criterion / apply_decision_criterion** lives in `world/types.py` but is opinion math SPEC routes to doxa CONSUME — world report flags it as misplaced. → port to the doxa boundary, not world DTOs.
4. **core/analyzers.py is the real AF/PrAF assembly**, outside the nominal `argumentation-stances` module set (`argumentation.py` is a 2-line marker). The argumentation-bridge slice charter MUST include core/analyzers.py; its test (`test_core_analyzers.py`) is UNCLAIMED — high-priority gap.
5. **M10 description-kind coreference** appears in both concept-core (test_lemon_phase3) and merge (`merge/description_kinds.py`). The merge module is a re-export; behavior owns to concept-core lemon. → owner **concept-core**, delete merge re-export.
6. **opinion / calibration / source-trust** are split across argumentation, render, source, belief. Resolved: opinion algebra → argumentation-bridge (over doxa); calibration metrics → heuristic-embeddings (EXTRACT calibration); source-trust calibration (AF→opinion) → argumentation-bridge; source-trust heuristic consensus + promote write → source/heuristic. Reports agree on the doxa boundary; they differ only on which slice "owns" the test file (resolved in §C).
7. **Glob false-positives (zero real files):** `test_source_alignment*`, `test_probabilistic*`, `test_disjoint*` (merge report); `test_realization*` (belief report). The behaviors exist under differently-named files; do not assume these names in CI selection.
8. **propagation.py substrate tag.** belief report lists it in-area but tags it EXTRACT sympy-eval (SPEC §C) — it gates the extracted package, not propstore-proper. No conflict, just dual-home noting.
9. **provenance records.py / projections.py dual-home.** SPEC §C puts them inside provenance-semiring EXTRACT; source report argues the AssumptionId/ContextId id-binding makes the adapter propstore-flavored. Decision deferred: generalize the id-binding to a str brand and push into the semiring pkg, or keep a thin propstore adapter.

---

## Coverage closure

Every one of the **196** files in `_unclaimed.txt` is classified below (A–F), plus
**16 phantoms** (full `remediation/phase_*/…` paths that path-normalize to an already-claimed
bare name — ALREADY COVERED, not re-assigned). Combined with the 387 directly-claimed master
files, all **583** files in `_ref.txt` are accounted: ledger in `_coverage_final.txt`
(0 UNCLASSIFIED). Classification source of truth: `_unclaimed_classified.tsv`.

**Headline counts (of the 196 unclaimed):**

| class | meaning | count |
|---|---|---|
| A | maps to a capability (49 existing + **6 NEW**) | **55** |
| B | discipline-gate (architecture/import-linter/no-* invariant) | 19 |
| C | consume-pin (pins a CONSUMED/EXTRACT substrate's behavior) | 43 |
| D | remediation-crit (hardening: security/atomicity/quarantine/race/anytime) | 40 |
| E | workstream-meta (`*_done` completion markers) | 21 |
| F | drop (DTO-shape / `*_renamed` / obsolete) | 2 |
| (phantom) | already covered under bare name | 16 |
| **total** | | **196** |

**NEW capabilities added to slice tables (6 A-NEW files → 4 capability rows):**
- **argumentation-bridge :: Core AF/PrAF assembly** — `core/analyzers.py` is the *real* Dung-AF +
  PrAF assembly (`argumentation.py` is a 2-line marker). Gated by `test_core_analyzers.py`. This is
  the high-priority gap from §F.4; the slice charter MUST include `core/analyzers.py`.
- **argumentation-bridge :: Justification synthesis from active graph** — `core/justifications.py`,
  gated by `test_core_justifications.py` (was only "(via test_argumentation_integration.py)").
- **argumentation-bridge :: Base-rate resolution over situated-assertion identity** —
  `core.base_rates` (BaseRateResolver/Profile), gated by `test_base_rate_resolution.py`.
- **claim :: Situated-assertion core model** — `core/assertions` (codec/refs/structural conversion),
  gated by `test_situated_assertions.py` + `_codec` + `_refs` + `test_structural_assertion_conversion.py`.
  (Also added a claim row for algorithm-claim staging + ast-equiv integration.)

**Port-risks from §D now CLOSED (dedicated test found while triaging):**
- #2 verify_claim_tree → `test_verify_cli.py` (A, source-proposals-provenance).
- #8 value_resolver derive math → `test_value_resolver_consensus_with_abstention.py`,
  `test_value_resolver_failure_reasons.py` (A, world).
- #11 M3 IntegrityConstraint → `test_ic_postulate_coverage.py` (A, merge-conflict). **Note: the
  team-lead heuristic routed `test_ic_postulate_*`→belief-set, but this file imports
  `merge.merge_classifier.IntegrityConstraint`/`build_merge_framework`, NOT belief_set ic_merge —
  it is merge M3, not an IC-merge postulate test.**
- #13 scope_policy decorator → `test_scope_policy.py` (A, belief-revision).
- part of #1 concept mutation CLI → `test_alias_collision_rejected.py` (A, concept-core).

### Discipline gates (B) — port as architecture gates, not features (19)
2 already under `architecture/` (`test_import_linter_negative.py`, `test_no_local_agm_logic.py`) +
17 flat: the `test_no_*` family (`no_old_data_shims`, `no_typed_dicts`, `no_privileged_namespace`,
`no_truncated_identity`, `no_process_streams_in_owners`, `no_derive_source_document_trust`,
`no_unbounded_quire_commit`), the AST-invariant gates (`canonical_json_single_source`,
`chain_query_enum_discipline`, `transaction_commit_sha_lifetime`, `property_marker_discipline`,
`quire_boundary`, `gunray_boundary_ws6`), the drift/freshness/parity gates (`doc_drift_clean`,
`generated_schema_freshness`, `fixture_schema_parity`), and `layered_contract_covers_six_readme_layers`.

### Consume-pins (C) — move to the substrate package's own suite OR keep as propstore integration pins (43)
- **formal-argumentation** (kernel): 17 `architecture/test_argumentation_pin_*` + `test_dfquad*` (2) +
  `test_treedecomp*`/`test_toy_dp` (3) → move to argumentation suite.
- **formal-belief-set**: `test_af_revision_postulates.py`, `test_af_revision_no_stable_distinct_from_empty_stable.py`.
- **doxa**: `test_consensus_clamp_consistency.py`, `test_wbf_vs_van_der_heijden_2018_def_4.py`.
- **eq-equiv**: `test_exp_sum_under_reals.py`, `test_log_product_under_positive_reals.py`,
  `test_sqrt_square_under_nonnegative_reals.py` (equation canonical-equivalence under sympy domain assumptions).
- **provenance-semiring**: `test_polynomial_provenance_preserved_through_combine.py`, `test_why_support_subsumes.py`.
- **atms** (EXTRACT): `test_labels_properties.py`, `test_labelled_core.py` (core/labels kernel; latter may stay a propstore integration pin).
- **quire**: `test_git_backend.py`, `test_branch_head_cas_matrix.py`, `test_branch_head_cas_properties.py`,
  `test_head_bound_transaction_primitive.py`, `test_knowledge_path.py`, `test_document_schema.py`, `test_quire_consumer_contracts.py`.
- **bridgman**: `test_bridgman_pi_signal_propagation.py`, `test_bridgman_pin_post_deletion.py`, `test_bridgman_signal_propagation.py`.

### Workstream-meta (E, 21) — KEEP/DROP recommendation (FLAG for human)
**Recommend DROP (20):** all `test_workstream_{a,agm,b,c,cm,d,e,f,g,h,i,j,j2,k,l,m,n1,n2,p,q_cas}_done.py`
— pure completion markers: either `assert True` (e.g. `_a_`) or read a finished review `.md` and
assert sentinel strings exist (`_agm_`, `_q_cas_`). They gate a workstream's *closure*, not a live
feature invariant. **Recommend KEEP/FOLD (1):** `test_workstream_o_ast_done.py` asserts a *live*
invariant (`{t.name for t in ast_equiv.comparison.Tier} == {...}`) — fold it into the **ast-equiv
consume-pin** rather than dropping. Nothing deleted; human decides.

### Files I was genuinely unsure of after inspection
- `test_value_status_surface.py` (classed A/world) — a one-assert guard that `ValueStatus` has no
  `UNDERDETERMINED` member; thin enough to be F, but it pins a deliberate value-resolution design
  invariant, so kept A.
- `test_authoring_roundtrip_contract.py` (A/storage) — "roundtrip" usually signals DROP, but it
  drives the **CLI** author→reload path and asserts content fidelity, so PORT/behavioral.
- `test_mapping_boundary_failures.py` (F) — tests coercion failures of snapshot/explanation DTOs
  that VANISH under quire charters; could be A/belief-revision if the boundary-validation is kept.
- `test_from_probability_n_one_round_trip.py` (A/argumentation-bridge) — team-lead heuristic said
  doxa, but it imports `propstore.praf.p_relation_from_stance`; it is the PrAF-bridge honesty path
  (doxa-adjacent), not a pure doxa operator pin.
- `test_pignistic_vs_smets_kennes_1994.py` (A/world) — pins `world.types.apply_decision_criterion`
  naming; §F.3 flags that function as misplaced (belongs at the doxa boundary), so this may re-home.

### Full ledger of all 196

| file | class | slice/capability or note |
|---|---|---|
| `architecture/test_argumentation_pin_aba_adf.py` | C | formal-argumentation kernel pin (ABA/ADF) -> move to argumentation suite |
| `architecture/test_argumentation_pin_asp_literal_validity.py` | C | formal-argumentation kernel pin (ASP literal validity) |
| `architecture/test_argumentation_pin_caf.py` | C | formal-argumentation kernel pin (CAF) |
| `architecture/test_argumentation_pin_dung_extensions.py` | C | formal-argumentation kernel pin (Dung extensions) |
| `architecture/test_argumentation_pin_dynamic.py` | C | formal-argumentation kernel pin (dynamic AF) |
| `architecture/test_argumentation_pin_enforcement.py` | C | formal-argumentation kernel pin (enforcement) |
| `architecture/test_argumentation_pin_epistemic.py` | C | formal-argumentation kernel pin (epistemic) |
| `architecture/test_argumentation_pin_gradual.py` | C | formal-argumentation kernel pin (gradual) |
| `architecture/test_argumentation_pin_iccma_adapter.py` | C | formal-argumentation kernel pin (ICCMA adapter) |
| `architecture/test_argumentation_pin_ideal_admissibility.py` | C | formal-argumentation kernel pin (ideal admissibility) |
| `architecture/test_argumentation_pin_partial_skeptical.py` | C | formal-argumentation kernel pin (partial skeptical) |
| `architecture/test_argumentation_pin_rule_collision.py` | C | formal-argumentation kernel pin (rule collision) |
| `architecture/test_argumentation_pin_setaf.py` | C | formal-argumentation kernel pin (SETAF) |
| `architecture/test_argumentation_pin_state_lazy.py` | C | formal-argumentation kernel pin (state lazy) |
| `architecture/test_argumentation_pin_vaf_completion.py` | C | formal-argumentation kernel pin (VAF completion) |
| `architecture/test_argumentation_pin_vaf_ranking.py` | C | formal-argumentation kernel pin (VAF ranking) |
| `architecture/test_argumentation_pin_z_continuous.py` | C | formal-argumentation kernel pin (continuous) |
| `architecture/test_import_linter_negative.py` | B | import-linter negative discipline gate |
| `architecture/test_no_local_agm_logic.py` | B | no-local-AGM invariant (belief-set consumed not reimplemented) |
| `remediation/phase_1_crits/test_T1_1_merge_preserves_rivals.py` | PHANTOM | already claimed as bare test_T1_1_merge_preserves_rivals.py (merge-conflict M4) |
| `remediation/phase_1_crits/test_T1_2_sidecar_survives_exception.py` | D | guards: sidecar atomicity (storage Sidecar writer survives exception) |
| `remediation/phase_1_crits/test_T1_5_zip_slip.py` | D | guards: import security (zip-slip path traversal) |
| `remediation/phase_2_gates/test_T2_1_quarantine_writer.py` | D | guards: build-diagnostics quarantine writer (storage) |
| `remediation/phase_2_gates/test_T2_2b_claim_pipeline_quarantine.py` | PHANTOM | already claimed bare (claim quarantine pipeline) |
| `remediation/phase_2_gates/test_T2_2c_stance_source_quarantine.py` | PHANTOM | already claimed bare (merge R3 stance quarantine) |
| `remediation/phase_2_gates/test_T2_2d_stance_target_quarantine.py` | PHANTOM | already claimed bare (merge R3 stance quarantine) |
| `remediation/phase_2_gates/test_T2_2e_justification_conclusion_quarantine.py` | D | guards: justification conclusion quarantine (claim/source) |
| `remediation/phase_2_gates/test_T2_2f_justification_premise_quarantine.py` | D | guards: justification premise quarantine (claim/source) |
| `remediation/phase_2_gates/test_T2_2g_micropublication_claim_quarantine.py` | PHANTOM | already claimed bare (micropub claim quarantine) |
| `remediation/phase_2_gates/test_T2_2h_in_claim_stance_quarantine.py` | PHANTOM | already claimed bare (merge R3 in-claim stance quarantine) |
| `remediation/phase_2_gates/test_T2_2i_compiler_claim_validation_quarantine.py` | PHANTOM | already claimed bare (claim CEL ingest quarantine) |
| `remediation/phase_2_gates/test_T2_2l_compiler_context_validation_quarantine.py` | D | guards: context validation quarantine (context-grounding) |
| `remediation/phase_2_gates/test_T2_2m_compiler_context_lifting_quarantine.py` | D | guards: context-lifting quarantine (context-grounding) |
| `remediation/phase_2_gates/test_T2_2o_compiler_claim_schema_quarantine.py` | PHANTOM | already claimed bare (claim schema quarantine) |
| `remediation/phase_2_gates/test_T2_2p_compiler_claim_pipeline_output_quarantine.py` | PHANTOM | already claimed bare (claim pipeline output quarantine) |
| `remediation/phase_2_gates/test_T2_2q_compiler_claim_pipeline_schema_exception_quarantine.py` | PHANTOM | already claimed bare (claim pipeline schema-exception quarantine) |
| `remediation/phase_2_gates/test_T2_3a_sidecar_schema_version_content_hash.py` | D | guards: sidecar schema-version content-hash (storage cache key) |
| `remediation/phase_2_gates/test_T2_3b_atomic_sidecar_write.py` | D | guards: atomic sidecar write (storage atomicity) |
| `remediation/phase_3_ignorance/test_T3_10_stamp_file_requires_status.py` | D | guards: provenance stamp requires status (source) |
| `remediation/phase_3_ignorance/test_T3_11_dogmatic_opinion_audit.py` | D | guards: dogmatic-opinion audit (doxa honesty) |
| `remediation/phase_3_ignorance/test_T3_3_preference_missing_metadata_vacuous.py` | D | guards: preference missing-metadata -> vacuous (argumentation-bridge) |
| `remediation/phase_3_ignorance/test_T3_5_activation_unknown_cel.py` | PHANTOM | already claimed bare (claim CEL activation unknown) |
| `remediation/phase_3_ignorance/test_T3_7_praf_defeat_summary_provenance.py` | D | guards: PrAF defeat-summary provenance (argumentation-bridge) |
| `remediation/phase_3_ignorance/test_T3_8_aspic_grounded_argument_strength.py` | D | guards: ASPIC+ grounded argument strength (argumentation-bridge) |
| `remediation/phase_3_ignorance/test_T3_9_fragility_coefficient_provenance.py` | D | guards: fragility coefficient provenance (belief-revision) |
| `remediation/phase_4_layers/test_T4_1_importlinter_layers.py` | D | guards: import-linter layer contract (architecture) |
| `remediation/phase_4_layers/test_T4_2_storage_does_not_import_merge.py` | PHANTOM | already claimed bare (storage !-> merge layer guard) |
| `remediation/phase_4_layers/test_T4_5_support_revision_exports.py` | D | guards: support_revision export surface (belief-revision) |
| `remediation/phase_4_layers/test_T4_7_praf_enforce_coh_attacks.py` | D | guards: PrAF enforce_coh attacks (argumentation-bridge) |
| `remediation/phase_4_layers/test_T4_8_exception_defeats_post_preference.py` | D | guards: exception defeats post-preference (context-grounding) |
| `remediation/phase_5_bridge/test_T5_10_exception_pattern_authoring_unbound.py` | D | guards: exception-pattern authoring unbound (context-grounding) |
| `remediation/phase_5_bridge/test_T5_11_exception_sibling_survival.py` | D | guards: exception sibling survival (context-grounding) |
| `remediation/phase_5_bridge/test_T5_1_undermines_preference_sensitive.py` | D | guards: undermine preference-sensitivity (argumentation-bridge) |
| `remediation/phase_5_bridge/test_T5_3_preference_order_cycles.py` | D | guards: preference-order cycles (argumentation-bridge) |
| `remediation/phase_5_bridge/test_T5_4_query_goal_contraries.py` | D | guards: goal-query contraries (argumentation-bridge) |
| `remediation/phase_5_bridge/test_T5_5_bridge_stance_no_silent_rewrite.py` | D | guards: bridge stance no-silent-rewrite (argumentation-bridge) |
| `remediation/phase_5_bridge/test_T5_6_bridge_edge_domain_invariant.py` | D | guards: bridge edge domain invariant (argumentation-bridge) |
| `remediation/phase_5_bridge/test_T5_7_justification_unknown_premise.py` | D | guards: justification unknown-premise (argumentation-bridge) |
| `remediation/phase_5_bridge/test_T5_8_projection_typed_claim_identity.py` | PHANTOM | already claimed bare (projection typed claim identity) |
| `remediation/phase_5_bridge/test_T5_9_projection_premise_dependency_split.py` | D | guards: projection premise dependency split (argumentation-bridge) |
| `remediation/phase_6_extend/test_T6_1_alignment_ignorance_relation.py` | PHANTOM | already claimed bare (R5 alignment ignorance relation) |
| `remediation/phase_6_extend/test_T6_7_predicate_atom_type_validation.py` | D | guards: predicate atom type validation (context-grounding) |
| `remediation/phase_7_race_atomicity/test_T7_2_merge_commit_expected_head.py` | PHANTOM | already claimed bare (merge commit expected-head CAS) |
| `remediation/phase_7_race_atomicity/test_T7_5a_sqlite_wal_busy_timeout.py` | D | guards: sqlite WAL busy-timeout race (storage) |
| `remediation/phase_7_race_atomicity/test_T7_5b_promotion_diagnostic_scope.py` | D | guards: promotion diagnostic scope (source) |
| `remediation/phase_7_race_atomicity/test_T7_5c_source_status_like_escape.py` | D | guards: source-status LIKE escape (source/sidecar SQL) |
| `remediation/phase_7_race_atomicity/test_T7_5d_promotion_blocked_id_collision.py` | D | guards: promotion blocked id-collision (source) |
| `remediation/phase_7_race_atomicity/test_T7_5e_promotion_blocked_fk_payload.py` | D | guards: promotion blocked FK payload (source) |
| `remediation/phase_7_race_atomicity/test_T7_5f_sidecar_build_duplicate_claim.py` | PHANTOM | already claimed bare (sidecar build duplicate claim) |
| `remediation/phase_7_race_atomicity/test_T7_5g_sidecar_build_duplicate_micropublication.py` | D | guards: sidecar build duplicate micropublication (source/storage) |
| `remediation/phase_7_race_atomicity/test_T7_6_full_race_suite.py` | D | guards: full race suite aggregate (storage atomicity) |
| `remediation/phase_8_dos_anytime/test_T8_1_assignment_candidates_ceiling.py` | D | guards: assignment-candidates anytime ceiling (world assignment-selection) |
| `remediation/phase_8_dos_anytime/test_T8_1_choose_incision_set_ceiling.py` | D | guards: incision-set anytime ceiling (belief-revision) |
| `remediation/phase_8_dos_anytime/test_T8_1_future_queryable_sets_ceiling.py` | D | guards: future-queryable-sets ceiling (world ATMS anytime) |
| `remediation/phase_8_dos_anytime/test_T8_4_atms_build_termination_guard.py` | D | guards: ATMS build termination guard (world ATMS anytime) |
| `test_T1_4_materialize_atomicity.py` | A | storage-build-compile :: Materialize (atomicity invariant) |
| `test_T1_7_build_repository_propagates_sidecar_errors.py` | A | storage-build-compile :: Build pipeline (sidecar error propagation) |
| `test_af_revision_no_stable_distinct_from_empty_stable.py` | C | formal-belief-set (AF revision: no-stable distinct from empty-stable) |
| `test_af_revision_postulates.py` | C | formal-belief-set (AF revision postulates) |
| `test_algorithm_free_variable_locals.py` | A | claim :: algorithm-claim free-variable locals (human-to-sympy/ast) |
| `test_algorithm_stage_types.py` | A | claim :: algorithm-claim stage types |
| `test_alias_collision_rejected.py` | A | concept-core :: Concept mutation CLI (alias collision rejected) - closes part of port-risk #1 |
| `test_authoring_roundtrip_contract.py` | A | storage-build-compile :: authoring roundtrip contract (CLI author->reload fidelity) |
| `test_base_rate_resolution.py` | A-NEW | argumentation-bridge :: NEW Base-rate resolution over situated-assertion identity (BaseRateResolver/Profile) |
| `test_branch_head_cas_matrix.py` | C | quire (branch-head CAS matrix) |
| `test_branch_head_cas_properties.py` | C | quire (branch-head CAS properties) |
| `test_bridgman_pi_signal_propagation.py` | C | bridgman (pi-group signal propagation) |
| `test_bridgman_pin_post_deletion.py` | C | bridgman (pin survives post-deletion) |
| `test_bridgman_signal_propagation.py` | C | bridgman (signal propagation) |
| `test_canonical_json_single_source.py` | B | discipline-gate: canonical_json single source (AST) |
| `test_capture_journal.py` | A | world-atms-worldline :: Worldline journal capture (TransitionJournal/EpistemicState) |
| `test_cas_no_silent_retry.py` | A | storage-build-compile :: CAS / head-bound txn (no silent retry) |
| `test_cas_rejection_no_orphan_rows.py` | A | storage-build-compile :: CAS rejection leaves no orphan sidecar rows (atomicity) |
| `test_chain_query_enum_discipline.py` | B | discipline-gate: chain_query ValueStatus-by-identity (AST) |
| `test_codex5_sidecar_cache_derived_invalidation.py` | A | storage-build-compile :: Sidecar rebuild-on-source-change (derived invalidation) |
| `test_compose_provenance_causal_order.py` | A | source-proposals-provenance :: Provenance carrier (compose preserves causal order) |
| `test_consensus_clamp_consistency.py` | C | doxa (consensus operator clamp consistency) |
| `test_core_analyzers.py` | A-NEW | argumentation-bridge :: NEW Core AF/PrAF assembly (claim_graph + praf.build_praf + probabilistic acceptance over shared input) |
| `test_core_justifications.py` | A | argumentation-bridge :: Justification synthesis from active graph (core/justifications) - was (via test_argumentation_integration), now dedicated |
| `test_dedup_pairs_preserves_mirror.py` | A | heuristic-embeddings :: H3 relate dedup (preserves mirror pair) |
| `test_dfquad.py` | C | formal-argumentation (DFQuAD) |
| `test_dfquad_attack_support_per_paper_contract.py` | C | formal-argumentation (DFQuAD attack/support per-paper contract) |
| `test_doc_drift_clean.py` | B | discipline-gate: doc drift clean |
| `test_document_schema.py` | C | quire (DocumentStruct/DocumentSchemaError load/decode) |
| `test_exp_sum_under_reals.py` | C | eq-equiv (equation canonical-equivalence under Real domain) |
| `test_extraction_provenance_aware_timestamps.py` | A | source-proposals-provenance :: extraction provenance-aware timestamps |
| `test_fixture_schema_parity.py` | B | discipline-gate: test-fixture schema parity with derived store |
| `test_from_probability_n_one_round_trip.py` | A | argumentation-bridge :: PrAF opinion-derived edges honest NoCalibration (n=1 no fabricated evidence) [doxa-adjacent] |
| `test_generated_schema_freshness.py` | B | discipline-gate: generated schema resources committed and fresh |
| `test_git_backend.py` | C | quire (Dulwich GitStore + KnowledgePath) |
| `test_gunray_boundary_ws6.py` | B | discipline-gate: gunray consumption boundary (AST) [tag gunray] |
| `test_gunray_integration.py` | A | context-grounding-defeasibility :: gunray pipeline end-to-end (concepts->grounder->ASPIC+->query_claim) |
| `test_head_bound_transaction_primitive.py` | C | quire (head-bound transaction / HeadMismatchError primitive) |
| `test_ic_postulate_coverage.py` | A | merge-conflict :: M3 IntegrityConstraint (build_merge_framework) - closes port-risk #11 [TASK HEURISTIC SAID belief-set; CORRECTED: imports merge.merge_classifier] |
| `test_justification_rule_kind_validated.py` | A | context-grounding-defeasibility :: justification rule-kind validation (CLI) |
| `test_knowledge_path.py` | C | quire (FilesystemTreePath/GitTreePath knowledge-path) |
| `test_labelled_core.py` | C | atms substrate (core/labels + world/labelled core; integration w/ BoundWorld) - may stay propstore integration pin |
| `test_labels_properties.py` | C | atms substrate (de Kleer 1986 label kernel property tests: minimality/combine/merge/nogood) |
| `test_layered_contract_covers_six_readme_layers.py` | B | discipline-gate: import-linter layered contract covers 6 README layers |
| `test_literal_keys.py` | A | argumentation-bridge :: Claims -> ASPIC+ literals (ClaimLiteralKey/IstLiteralKey/GroundLiteralKey) |
| `test_local_handle_collision_blocks_commit.py` | A | source-proposals-provenance :: reference lowering (local-handle collision blocks commit) |
| `test_log_cli.py` | A | render-cli-web :: History log CLI surface |
| `test_log_product_under_positive_reals.py` | C | eq-equiv (equation canonical-equivalence under Positive domain) |
| `test_mapping_boundary_failures.py` | F | DROP: DTO coercion boundary failures (snapshot/explanation types vanish under quire charters) |
| `test_no_derive_source_document_trust.py` | B | discipline-gate: no source-document-trust derivation fn (AST) |
| `test_no_old_data_shims.py` | B | discipline-gate: no old-data shims |
| `test_no_privileged_namespace.py` | B | discipline-gate: no privileged namespace (NamespaceAmbiguity invariant) |
| `test_no_process_streams_in_owners.py` | B | discipline-gate: no process streams in owner layers (AST) |
| `test_no_truncated_identity.py` | B | discipline-gate: no truncated identity hashes (AST) |
| `test_no_typed_dicts.py` | B | discipline-gate: no TypedDicts (AST) |
| `test_no_unbounded_quire_commit.py` | B | discipline-gate: no unbounded quire commit (AST scan finalize/promote) |
| `test_p_heavy.py` | A | belief-revision :: at_journal_step heavy variant (P-HEAVY 1/2/3, scope) |
| `test_p_mara_gate.py` | A | belief-revision :: at_journal_step minimal-vs-heavy gate (P-MARA) |
| `test_pignistic_vs_smets_kennes_1994.py` | A | world-atms-worldline :: Decision criterion / opinion tiebreak (apply_decision_criterion naming) [doxa-adjacent] |
| `test_pls_property.py` | A | belief-revision :: Semantic snapshot diff/apply frame property (Bonanno 2010 PLS: apply(diff)=identity) |
| `test_polynomial_provenance_preserved_through_combine.py` | C | provenance-semiring (polynomial provenance preserved through combine) |
| `test_project_init.py` | A | storage-build-compile :: Repo/project init (initialize_project seeds packaged artifacts) |
| `test_property.py` | A | claim :: CEL tokenizer + numeric interval comparison property tests (T4) |
| `test_property_marker_discipline.py` | B | discipline-gate: @pytest.mark.property usage discipline (AST) |
| `test_propose_predicates_lifecycle.py` | A | source-proposals-provenance :: Predicate proposal declare+promote lifecycle |
| `test_propose_rules_lifecycle.py` | A | source-proposals-provenance :: Rule proposal propose+promote lifecycle |
| `test_propstore_rule_kind_widened.py` | A | context-grounding-defeasibility :: DeLP rule-kind schema closure (proper/blocking defeater; default vs strong neg, Garcia&Simari) |
| `test_quire_boundary.py` | B | discipline-gate: quire import boundary (AST) |
| `test_quire_consumer_contracts.py` | C | quire (propstore consumer contracts over generic GitStore) |
| `test_reasoning_demo_cli.py` | A | render-cli-web :: reasoning demo CLI (materialize_reasoning_demo) |
| `test_replay_determinism_actually_replays.py` | A | belief-revision :: Journal replay re-executes recorded operators (determinism) |
| `test_repo_branch.py` | A | storage-build-compile :: multi-branch git primitives (branch CRUD, commit isolation, merge-base) |
| `test_repo_snapshot.py` | A | storage-build-compile :: Repository snapshot (branch taxonomy) |
| `test_required_schema_completeness.py` | A | storage-build-compile :: sidecar projection schema completeness (columns WorldQuery requires) |
| `test_review_regressions.py` | A | argumentation-bridge :: PrAF/Dung review regression suite (build_praf over ProbabilisticAF) |
| `test_scope_policy.py` | A | belief-revision :: scope_policy decorator (degrade/require/noop) - closes port-risk #13 |
| `test_sidecar_alias_projection.py` | A | storage-build-compile :: sidecar alias projection (DROP-tagged row) |
| `test_sidecar_contexts.py` | A | context-grounding-defeasibility :: Context sidecar projection + load_lifting_system rehydration |
| `test_sidecar_grounded_facts.py` | A | context-grounding-defeasibility :: Grounded-fact sidecar projection (4-section roundtrip) |
| `test_sidecar_source_projection.py` | A | source-proposals-provenance :: source/blocked-claim projection rows |
| `test_situated_assertion_codec.py` | A-NEW | claim :: NEW Situated-assertion canonical codec (core/assertions; content-identity PORT) |
| `test_situated_assertion_refs.py` | A-NEW | claim :: NEW Situated-assertion refs (ConditionRef/ContextReference, core/assertions) |
| `test_situated_assertions.py` | A-NEW | claim :: NEW Situated-assertion model (core/assertions) |
| `test_sqrt_square_under_nonnegative_reals.py` | C | eq-equiv (equation canonical-equivalence under NonNegative domain) |
| `test_structural_assertion_conversion.py` | A-NEW | claim :: NEW Structural->situated assertion conversion (core/assertions) |
| `test_support_realization_postulates.py` | A | belief-revision :: Minimal support incision / realization postulates |
| `test_toy_dp.py` | C | formal-argumentation (probabilistic I/O/U labelling DP, Popescu&Wallner 2024) |
| `test_transaction_commit_sha_lifetime.py` | B | discipline-gate: scoped-mutation commit-sha lifetime (AST scan finalize/promote) |
| `test_treedecomp.py` | C | formal-argumentation (tree-decomposition exact DP for PrAF, Popescu&Wallner 2024) |
| `test_treedecomp_differential.py` | C | formal-argumentation (tree-decomp differential vs brute force) |
| `test_validator.py` | A | concept-core :: Concept file validator (artifact_id uniqueness, deprecation chains, relationship targets) |
| `test_value_resolver_consensus_with_abstention.py` | A | world-atms-worldline :: value_resolver derive (ActiveClaimResolver consensus w/ abstention) - closes port-risk #8 |
| `test_value_resolver_failure_reasons.py` | A | world-atms-worldline :: value_resolver typed failure reasons (ALGORITHM_UNPARSEABLE) - closes port-risk #8 |
| `test_value_status_surface.py` | A | world-atms-worldline :: ValueStatus surface invariant (no UNDERDETERMINED member) [thin; F-adjacent] |
| `test_verdict_renamed.py` | F | DROP: *_renamed contract guard (grounder/bundle verdict rename, AST/path) |
| `test_verify_cli.py` | A | source-proposals-provenance :: verify CLI / claim-tree verification - closes port-risk #2 |
| `test_wbf_vs_van_der_heijden_2018_def_4.py` | C | doxa (WBF operator regression vs van der Heijden 2018 Def 4 / Table I) |
| `test_why_support_subsumes.py` | C | provenance-semiring (WhySupport subsumption / normalize_why_supports) |
| `test_workstream_a_done.py` | E | workstream-meta: assert True -> DROP |
| `test_workstream_agm_done.py` | E | workstream-meta: reads review .md sentinels -> DROP |
| `test_workstream_b_done.py` | E | workstream-meta -> DROP |
| `test_workstream_c_done.py` | E | workstream-meta -> DROP |
| `test_workstream_cm_done.py` | E | workstream-meta -> DROP |
| `test_workstream_d_done.py` | E | workstream-meta -> DROP |
| `test_workstream_e_done.py` | E | workstream-meta -> DROP |
| `test_workstream_f_done.py` | E | workstream-meta -> DROP |
| `test_workstream_g_done.py` | E | workstream-meta -> DROP |
| `test_workstream_h_done.py` | E | workstream-meta -> DROP |
| `test_workstream_i_done.py` | E | workstream-meta -> DROP |
| `test_workstream_j2_done.py` | E | workstream-meta -> DROP |
| `test_workstream_j_done.py` | E | workstream-meta -> DROP |
| `test_workstream_k_done.py` | E | workstream-meta -> DROP |
| `test_workstream_l_done.py` | E | workstream-meta -> DROP |
| `test_workstream_m_done.py` | E | workstream-meta -> DROP |
| `test_workstream_n1_done.py` | E | workstream-meta -> DROP |
| `test_workstream_n2_done.py` | E | workstream-meta -> DROP |
| `test_workstream_o_ast_done.py` | E | workstream-meta BUT asserts live ast_equiv.Tier enum invariant -> KEEP/fold into ast-equiv pin (FLAG human) |
| `test_workstream_p_done.py` | E | workstream-meta -> DROP |
| `test_workstream_q_cas_done.py` | E | workstream-meta: reads review .md -> DROP |
| `test_ws7_grounding_completion.py` | A | context-grounding-defeasibility :: WS7 grounding-completion contract (live, not a done-marker) |
| `test_ws_o_ast_integration.py` | A | claim :: ast-equiv algorithm AST integration (ast_equiv.canonical_dump) [ast-equiv substrate] |
