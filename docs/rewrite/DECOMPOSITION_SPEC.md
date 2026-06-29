# propstore decomposition spec (from 10-scout survey of reference 20e55cca)

Goal: propstore = thin semantic-composition layer over substrate packages. This maps every
module cluster to: CONSUME (import a package), EXTRACT (new package), PROPSTORE-proper,
VANISH (DTO/wiring that disappears under quire charters), or DEAD.

## A. ALREADY CONSUMED — pinned in the reference pyproject (verify still wired post-rewrite)
quire, formal-argumentation, formal-belief-set, bridgman, cel-parser, ast-equiv, gunray.
(gunray = Defeasible Datalog evaluator — the grounding substrate; NOT clingo.)

## B. CONSUME — package exists, NOT yet wired; delete the local duplicate
- doxa  <- opinion.py (768L Jøsang fork, 13 importers). Delta = provenance carriers (doxa Non-Goal).
  STRONGEST finding — flagged by 4 scouts. Fix: thin propstore opinion shim adding provenance, OR push
  a provenance variant upstream to doxa. NOT a coercer mesh — one boundary type.
- assignment-selection <- world/assignment_selection_merge.py (parallel reimpl). Keep a thin propstore
  CEL/Z3 IntegrityConstraint + anytime-ceiling adapter; consume the sigma/max/gmax operators.
- eq-equiv <- equation_parser.py + equation_comparison.py (stale dups; pkg unpinned). Keep ConflictClaim
  adapter (compare_equation_claims / equation_signature).
- human-to-sympy <- sympy_generator.py.

## C. EXTRACT — new substrate packages (not yet extracted)
- condition-ir  [CLEAN, HIGH] = core/conditions/* + cel_types.py. Typed CEL ConditionIR + Z3/SQL/python/
  estree backends + ConditionSolver. Deps: cel-parser + z3. Only seam: ir.py imports core.id_types.ConceptId
  -> generalize to a str brand.
- provenance-semiring  [CLEAN, ~470L] = provenance/{polynomial,homomorphism,derivative,nogoods,support,
  projections,variables}(+records,prov_o optional). Green semiring / why-provenance math. Near-zero blast.
  UNLOCKS atms (its labels carry these polynomials).
- atms  [HIGH value/effort] = world/atms.py (2944L) + core/labels.py (394L). De Kleer label/env/nogood +
  bounded future/replay/inquiry. Kernel is semiring-fused -> generalize over a label semiring (provenance
  polynomial = one instantiation, from provenance-semiring). Node adapters stay PROPSTORE.
- causal-models  [MEDIUM, ~644L] = world/{scm,intervention,actual_cause}. Pearl do() + Halpern 2015 actual
  cause. Make generic over a variable->equation map; propstore adapts CompiledWorldGraph in.
- calibration  [CLEAN] = pure-metrics half of heuristic/calibrate.py (TemperatureScaler, ECE, Brier,
  log_loss; Guo 2017). Split from the CorpusCalibrator/categorical_to_opinion half (stays PROPSTORE; or doxa sibling).
- sympy-eval  [CLEAN, ~177L] = propagation.py. Typed sympy expression eval, zero propstore imports.
- (weak/optional) unit-convert (dimensions.py Pint layer; or keep in propstore over bridgman);
  named-uri (uri.py+uri_authority.py RFC6920 ni:/RFC4151 tag:; or fold into quire identity).

## D. VANISHES under quire charter classes — NOT ported, NOT consumed; ceases to exist
- families/documents/* (~1366L DocumentStruct + to_payload boilerplate)
- families/projection_catalog.py; bulk of families/registry.py (placement/FK/ref-type/per-family
  ArtifactFamily/projection wiring)
- most of contracts.py emission (doc/family/FK contract bodies — charter contracts replace)
- json_types.py, families/addresses.py
- the distributed symptom mass: ~347 coerce_*, ~283 to_payload, ~1216 Document refs (one charter per entity)

## E. PROPSTORE-PROPER — the actual semantic OS (what's left after A-D)
- Concept/semantic core: core/lemon/* (OntoLex-Lemon: entry/form/sense, qualia, proto-roles, description-kinds,
  Allen temporal, Dung coreference), families/concepts, families/forms.
- Condition/conflict glue (over condition-ir): cel_registry, cel_validation, condition_classifier,
  parameterization_groups/walk, value_comparison.
- Claims/contexts/stances authoring: families/claims, families/contexts, claims.py, stances.py,
  context_lifting.py (McCarthy/Guha ist), defeasibility.py (CKR exceptions), families/rules,
  families/documents schemas for rules/predicates/stances (the SCHEMA decl, as charters), grounding/* (gunray bridges).
- Argumentation BRIDGES (domain -> formal-argumentation kernel): aspic_bridge, praf, claim_graph,
  source_trust_argumentation, preference.py, structured_projection.py.
- World render + worldline orchestration: world/{model,bound,overlay,resolution,queries,consistency,types,
  journal_replay,bridge}, value_resolver (consumes ast-equiv), worldline/*, observatory.
- Belief adapter: support_revision/* (over belief-set), fragility*, sensitivity (over sympy-eval),
  epistemic_process, policies.
- Merge/conflict orchestration: merge/*, conflict_detector/*, probabilistic_relations, relation_analysis,
  families/relations, families/sameas.
- Source/import/proposals/provenance-carrier: source/*, importing/*, proposals*, proposal_promotion,
  provenance/__init__ (named-graph carrier on quire.notes) + trusty, families/sources,
  families/micropublications, families/identity, artifact_codes, artifact_verification.
- Build/compile orchestration: repository (thin), derived_build*, compiler/*, semantic_passes/* (AUTHORED->
  CHECKED; no quire analog), CompilationContext, storage/snapshot (branch taxonomy), families/diagnostics, resources.
- Presentation: app/*, cli/*, web/*, reporting, graph_export, core/embeddings, heuristic/{embed,classify,
  relate,predicate_extraction,rule_extraction,rule_corpus,source_trust,embedding_identity},
  families/embeddings (adapter over quire vec), families/calibration.

## F. DEAD — delete
form_utils.py (dup of families/forms/stages); empty/pycache-only dirs: families/predicates,
families/stances, families/merge, families/source_alignment, families/meta; world/__pycache__ orphans
(assignment_selection_policy/conflict_projection/graph_projection/journal_projection).

## G. Issues to track (not blocking)
- belief-set Hansson base/anytime contraction surface paid-for but UNUSED (propstore rolls its own incision).
- CLAUDE.md doc drift: AF revision lives in argumentation.af_revision (not belief_set); af_adapter.py misnamed.
- latent bug grounder.py:342-351 (_inspection_rule_instances double-count).
- minor dups: _CONTEXT JSON-LD (provenance/__init__ vs prov_o), _URI_PREFIXES (records vs importing/machinery).

## HEADLINE
Substrate is ~done: 7 packages already consumed, 4 more are delete-and-consume, 6 fresh extracts (2 clean +
2 medium + atms big). ~70% of storage/infra + the coerce/payload symptom mass VANISHES under charters.
PROPSTORE-PROPER = the OntoLex-Lemon concept model + claim/context/stance authoring + non-commitment render
policy + the kernel BRIDGES + build/compile orchestration. That irreducible core is the real "semantic OS";
everything else is import, vanish, or delete.

## SEQUENCING IMPLICATION
1. Wire the already-extracted CONSUMEs + delete dups (doxa, eq-equiv, human-to-sympy, assignment-selection).
2. Extract the clean substrates (sympy-eval, calibration, provenance-semiring, condition-ir).
3. Extract atms (over provenance-semiring) + causal-models.
4. Author canonical charters per entity (claims/concepts/contexts/...) on quire; DTO layer vanishes.
5. Rebuild propstore-proper (bridges + render + orchestration) against the behavioral test corpus.
Discipline throughout: one-direction lowering at each package boundary; if an adapter needs a second coercer,
the boundary is wrong — move it, don't add the coercer.
