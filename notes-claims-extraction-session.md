# Claims Extraction Session - 2026-03-21

## Agent 3 - AGM/TMS Batch

### Goal
Extract claims from 5 papers with full concept registration.

### Papers
1. Alchourron_1985_TheoryChange - DONE (claims.yaml written, 20 claims)
2. Dixon_1993_ATMSandAGM - DONE (claims.yaml written, 15 claims)
3. Martins_1983_MultipleBeliefSpaces - DONE (claims.yaml written, 14 claims)
4. Martins_1988_BeliefRevision - DONE (claims.yaml written, 17 claims)
5. McDermott_1983_ContextsDataDependencies - DONE (claims.yaml written, 16 claims)

### ALL 5 PAPERS COMPLETE. Total: 82 claims, 36 concepts registered.

### Concepts registered by this agent (36 total)
Paper 1 (Alchourron): belief_set, contraction, revision, expansion, agm_postulates, remainder_set,
  selection_function, partial_meet_contraction, levi_identity, harper_identity,
  representation_theorem, maxichoice_contraction, full_meet_contraction, deductive_closure, recovery_postulate
Paper 2 (Dixon): atms, epistemic_entrenchment, environment, justification, label,
  essential_support, foundational_belief, context_switching
Paper 3 (Martins 1983): belief_space, context, origin_set, restriction_set, supported_wff,
  negation_introduction, restriction_set_update
Paper 4 (Martins 1988): swm_logic, snebr, combinability
Paper 5 (McDermott): data_pool, data_dependency, boolean_label, well_founded_labeling, odd_loop

---

## Agent 4 - Dung/Pollock/Cayrol/Modgil Batch

### Goal
Extract claims from 5 papers: Dung 1995, Pollock 1987, Cayrol 2005, Modgil 2014, Modgil 2018.

### Concepts registered
- argumentation_framework (concept24), conflict_free_set (concept28), admissible_set (concept29)
- preferred_extension (concept31), stable_extension (concept32), grounded_extension (concept33)
- complete_extension (concept34), characteristic_function (concept35), acceptability (concept36)
- attack_relation (concept37), coherent_framework (concept38), well_founded_framework (concept39)
- finitary_framework (concept41), meta_interpreter (concept43)
- prima_facie_reason (concept62), conclusive_reason (concept63), rebutting_defeater (concept64)
- undercutting_defeater (concept65), warrant (concept66), defeat_level (concept67)
- self_defeating_argument (concept69), collective_defeat (concept71), reinstatement (concept74)

### Additional concepts registered (Cayrol)
- bipolar_argumentation_framework (concept101), supported_defeat (concept104)
- indirect_defeat (concept107), safe_set (concept114), d_admissible (concept116)
- s_admissible (concept118), c_admissible (concept124)

### Additional concepts registered (Modgil 2014)
- undermining_attack (concept138), rebutting_attack (concept140), undercutting_attack (concept141)
- strict_rule (concept143), defeasible_rule (concept144), preference_ordering (concept145)
- rationality_postulate (concept146), contrariness_function (concept148), transposition_closure (concept149)

### Additional concepts registered (Modgil 2018)
- attack_based_conflict_free (concept157), reasonable_ordering (concept158), preferred_subtheory (concept160)

### Status - ALL DONE
- [x] Dung 1995 - claims.yaml written (21 claims)
- [x] Pollock 1987 - claims.yaml written (11 claims)
- [x] Cayrol 2005 - claims.yaml written (15 claims)
- [x] Modgil 2014 - claims.yaml written (13 claims)
- [x] Modgil 2018 - claims.yaml written (15 claims)

### Total: 75 claims, ~36 new concepts registered

---

## Agent 1 - Scientific Communication / Mixed Batch

### Goal
Extract claims from 6 papers with full concept registration.

### Papers
1. Clark_2014_Micropublications - DONE (9 claims, 9 concepts)
2. Groth_2010_AnatomyNanopublication - DONE (7 claims, 3 concepts)
3. Greenberg_2009_CitationDistortions - DONE (13 claims, 6 concepts)
4. Mayer_2020_Transformer-BasedArgumentMiningHealthcare - DONE (12 claims, 5 concepts)
5. Ginsberg_1985_Counterfactuals - DONE (10 claims, 5 concepts)
6. Falkenhainer_1987_BeliefMaintenanceSystem - DONE (13 claims, 5 concepts)

### ALL 6 PAPERS COMPLETE. Total: 64 claims, 33 concepts registered.

### Concepts registered by this agent
- Clark: micropublication, scientific_claim, support_relation, challenge_relation, claim_lineage, similarity_group, holotype, attribution, support_graph
- Groth: nanopublication, named_graph, s_evidence
- Greenberg: citation_distortion, citation_bias, citation_amplification, citation_invention, claim_specific_citation_network, citation_transmutation
- Mayer: argument_mining, argument_component_detection, argument_relation_prediction, bio_sequence_labeling, multichoice_architecture
- Ginsberg: counterfactual_conditional, three_valued_truth_function, truth_function_closure, sublanguage_selection, possible_worlds_semantics
- Falkenhainer: belief_maintenance_system, dempster_shafer_interval, belief_propagation, support_link, frame_of_discernment

---

## Previous Agent Notes (kept for reference)

### Agent 2 Progress (Odekerken batch)

#### Paper 1: Odekerken_2023 - DONE
- Registered: aspic_plus, grounded_semantics, justification_status, incomplete_information, stability, relevance, queryable, answer_set_programming, knowledge_base
- claims.yaml written: 12 claims (4 justification statuses, stability coNP-complete, relevance Sigma2P-complete, ASP algorithms, etc.)

#### Paper 2: Prakken_2012 - DONE
- Registered: defeasible_reasoning, inference_graph, defeat_status, argumentation_scheme, argument_strength
- claims.yaml written: 10 claims (rebutting/undercutting defeat, inference graphs, partial defeat status, argumentation schemes, etc.)

#### Paper 3: Reiter_1980 - DONE
- Registered: default_rule, default_theory, default_extension, normal_default
- claims.yaml written: 15 claims (default rule form, extensions as fixed points, normal defaults existence, orthogonality, semi-monotonicity, non-semi-decidability, belief revision criteria)

#### Paper 4: Shapiro_1998 - DONE
- Registered: belief_revision_system
- claims.yaml written: 11 claims (KBS architecture, 3 BRS tasks, JTMS/ATMS/SNeBR comparison, AGM isolation, culprit selection constraints)

#### Paper 5: Walton_2015 - DONE
- Registered: critical_question, practical_reasoning, abductive_reasoning
- claims.yaml written: 12 claims (scheme taxonomy, source-dependent/independent, critical questions, practical reasoning, ASPIC+ mapping)
