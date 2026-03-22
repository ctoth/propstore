# Notes: Modgil 2018 Claims Extraction

## GOAL
Extract claims from Modgil & Prakken 2018 paper, register concepts, create claims.yaml.

## Observations
- concepts dir is empty — no concepts registered yet in the project
- claims.yaml exists but is empty (just source header, empty claims list)
- Format: see Dung_1995 and Modgil_2014 claims.yaml for reference
- `pks concept add` needs: --domain, --name, --definition, --form
- Forms available: structural, category, boolean, count, rate, score, ratio, etc.
- Most argumentation concepts will use form "structural" or "category"

## Concepts to Register
From the prompt: argumentation_framework, aspic_plus, structured_argumentation, defeasible_reasoning, strict_rules, defeasible_rules, attack_relation, defeat_relation, preference_ordering, conflict_free, rationality_postulates, preferred_subtheories, last_link_ordering, weakest_link_ordering, undercutting, rebutting, undermining

## Claims to Extract (from prompt)
1. Observation: rationality postulates hold under specific conditions
2. Observation: attack-based conflict-free more appropriate than defeat-based
3. Observation: ASPIC+ subsumes Brewka's preferred subtheories
4. Observation: ASPIC+ subsumes abstract logic approach
5. Observation: undercutting attacks always preference-independent
6. Model: argumentation system structure
7. Model: SAF/c-SAF construction
8. Model: three attack types and defeat conditions
9. Parameter: reasonable ordering conditions (Def 18)
10. Parameter: well-defined SAF conditions
11. Parameter: axiom of contraposition requirement

## DONE
- Registered 17 concepts (concept1-concept17): argumentation_framework, aspic_plus, structured_argumentation, defeasible_reasoning, strict_rules, defeasible_rules, attack_relation, defeat_relation, preference_ordering, conflict_free, rationality_postulates, preferred_subtheories, last_link_ordering, weakest_link_ordering, undercutting, rebutting, undermining
- All use domain "argumentation", form "structural" (category form requires form_parameters.values)

## DONE (continued)
- Wrote claims.yaml with 11 claims: 9 observations, 2 models
- Changed claim9/claim10 from type "parameter" to "observation" — parameter type requires numeric value/unit/concept fields, these are formal constraints not quantitative params
- Validation passes: `pks claim validate --dir papers/Modgil_2018_GeneralAccountArgumentationPreferences`
- Created scripts/validate_claims_only.py helper (not needed in the end, used CLI directly)
