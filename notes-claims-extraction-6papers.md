# Claims Extraction Session - 6 Papers (2026-03-22)

## GOAL
Extract claims from 6 papers with full concept registration and validation.

## Papers
1. Clark_2014_Micropublications
2. Groth_2010_AnatomyNanopublication
3. Greenberg_2009_CitationDistortions
4. Mayer_2020_Transformer-BasedArgumentMiningHealthcare
5. Ginsberg_1985_Counterfactuals
6. Falkenhainer_1987_BeliefMaintenanceSystem

## System Understanding
- `pks concept add --name X --domain D --form structural --definition "..."` creates concept YAML
- `pks claim validate-file <path>` validates against schema + concept registry
- Concepts referenced by ID (concept1) or canonical_name in claims
- Claims need: id, type, provenance (paper + page), type-specific fields
- observation: statement, concepts list
- measurement: target_concept, measure, value, unit
- equation: expression, sympy, variables
- No existing concepts directory (empty). All concepts must be registered fresh.

## Concepts Registered So Far
- concept197: micropublication
- concept216: scientific_claim
- concept220: support_relation
- concept223: challenge_relation
- concept226: scientific_evidence
- concept227: attribution
- concept228: similarity_group
- concept229: holotype
- concept230: claim_lineage
- concept231: nanopublication
- concept233: defeasible_argumentation
- concept236: claim_network
- concept240: citation_distortion
- concept244: open_annotation_model

## Additional Concepts Registered
- concept295: rdf_named_graph
- concept298: s_evidence
- concept301: concept_identifier
- concept303: statement_provenance
- concept327: citation_bias
- concept328: citation_amplification
- concept329: citation_invention
- concept330: citation_transmutation
- concept331: network_authority
- concept332: information_cascade

## More Concepts Registered
- concept345: argument_component
- concept346: argument_relation
- concept347: transformer_language_model
- concept348: sequence_labeling
- Pre-existing: argument_mining, attack_relation, argumentation_framework, etc.

## More Concepts Registered (Ginsberg/Falkenhainer)
- concept358: counterfactual_reasoning
- concept361: three_valued_truth_function
- concept364: truth_function_closure
- concept365: possible_worlds_semantics
- concept366: automated_diagnosis
- concept368: belief_maintenance_system
- concept369: dempster_shafer_theory
- concept370: belief_propagation
- concept371: support_link
- concept372: frame_of_discernment

## Progress - ALL COMPLETE
- [x] Paper 1: Clark_2014 - 15 claims, VALIDATED clean
- [x] Paper 2: Groth_2010 - 12 claims, VALIDATED clean
- [x] Paper 3: Greenberg_2009 - 17 claims (incl 8 measurements), VALIDATED clean
- [x] Paper 4: Mayer_2020 - 14 claims (incl 5 measurements), VALIDATED clean
- [x] Paper 5: Ginsberg_1985 - 12 claims, VALIDATED clean
- [x] Paper 6: Falkenhainer_1987 - 13 claims, VALIDATED clean

Total: 83 claims across 6 papers, all validated with 0 errors and 0 warnings.
Total new concepts registered: ~30 across all papers.
