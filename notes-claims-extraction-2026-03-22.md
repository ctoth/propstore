# Claims Extraction Session 2026-03-22

## GOAL
Extract claims from 5 papers with full concept registration and validation.

## Papers
1. Alchourron_1985_TheoryChange - notes.md read, rich AGM postulates content
2. Dixon_1993_ATMSandAGM - notes.md read, ATMS-AGM equivalence
3. Martins_1983_MultipleBeliefSpaces - notes.md read, MBR contexts
4. Martins_1988_BeliefRevision - notes.md read, SWM logic + SNeBR
5. McDermott_1983_ContextsDataDependencies - notes.md read, data pools + dependencies

## State
- No existing concept files in knowledge/concepts/
- No existing claims files found (all empty or missing)
- Forms available: structural (main one for argumentation domain concepts)
- Schema read: observation needs statement + concepts, equation needs expression + sympy + variables
- CLI: `pks concept add --domain --name --definition --form`
- CLI: `pks claim validate-file <path>`

## Concepts needed (across all 5 papers)
Core AGM/belief revision: theory, belief_set, contraction, revision, expansion, remainder_set, selection_function, partial_meet_contraction, agm_postulates, epistemic_entrenchment, levi_identity, harper_identity, recovery_postulate, deductive_closure

TMS/ATMS: truth_maintenance_system, assumption_based_tms, justification, environment, label, nogood, assumption, foundational_belief

MBR/SWM: belief_space, context, current_context, origin_set, restriction_set, origin_tag, supported_wff, swm_logic, snebr, contradiction_detection, culprit_selection, belief_revision

McDermott: data_pool, data_dependency, bead, boolean_label, odd_loop, well_founded_labeling, blocking_bead, latent_assertion, signal_function

## Concepts registered so far
- theory (concept173)
- belief_set (concept174)
- contraction (concept175)
- revision (concept177)
- expansion (concept179)

Counter jumps (173->174->175->177->179) suggest other concepts already exist in the range.

## Session 2 - Argumentation Papers

### Papers (this session)
1. papers/Dung_1995_AcceptabilityArguments/ - IN PROGRESS
2. papers/Pollock_1987_DefeasibleReasoning/
3. papers/Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation/
4. papers/Modgil_2014_ASPICFrameworkStructuredArgumentation/
5. papers/Modgil_2018_GeneralAccountArgumentationPreferences/

### New concepts registered (argumentation domain, structural form):
- argumentation_framework, attack_relation, conflict_free_set, acceptability
- admissible_set, preferred_extension, stable_extension, grounded_extension
- complete_extension, characteristic_function, well_founded_framework
- finitary_framework, coherent_framework, controversial_argument
- nonmonotonic_reasoning, default_logic, logic_programming, meta_interpreter
- credulous_reasoning, skeptical_reasoning

### Observations from validator:
- Claims need: id (claim1, claim2...), type, provenance (paper + page required), statement, concepts
- Validator checks concepts exist in registry by canonical_name
- Old format used descriptive IDs and `reference` field; new format needs `provenance` with `paper` and `page`

### Dung 1995 notes.md: Read in full (484 lines)
- Rich paper: definitions, theorems, design rationale, arguments against prior work
- All theoretical - only observation claims, no parameter/measurement/equation
- Page numbers well-documented throughout notes

## Session 3 - Belief Revision Papers (this session)

### Additional concepts registered (via scripts/register_concepts.py)
- assumption_based_tms, environment, label, foundational_belief
- belief_space, context, current_context, origin_set, restriction_set
- origin_tag, supported_wff, swm_logic, snebr, culprit_selection
- data_pool, data_dependency, bead, boolean_label, odd_loop
- well_founded_labeling, blocking_bead, latent_assertion, signal_function
- maxichoice_contraction, full_meet_contraction, transitively_relational

### Claims extraction COMPLETE - all 5 validated clean
1. Alchourron_1985_TheoryChange - 18 claims
2. Dixon_1993_ATMSandAGM - 15 claims
3. Martins_1983_MultipleBeliefSpaces - 14 claims
4. Martins_1988_BeliefRevision - 18 claims
5. McDermott_1983_ContextsDataDependencies - 16 claims
Total: 81 claims across 5 papers, 0 errors, 0 warnings

## Session 4 - Argumentation Papers Extraction (current)

### Progress
1. Dung_1995_AcceptabilityArguments - DONE, 30 claims, validated clean
2. Pollock_1987_DefeasibleReasoning - DONE, 20 claims, validated clean
3. Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation - DONE, 16 claims, validated clean
4. Modgil_2014_ASPICFrameworkStructuredArgumentation - DONE, 16 claims, validated clean
5. Modgil_2018_GeneralAccountArgumentationPreferences - IN PROGRESS (reading notes.md)

### New concepts registered this session
Dung 1995: argumentation_framework, attack_relation, conflict_free_set, acceptability,
  admissible_set, preferred_extension, stable_extension, grounded_extension,
  complete_extension, characteristic_function, well_founded_framework,
  finitary_framework, coherent_framework, controversial_argument,
  nonmonotonic_reasoning, default_logic, logic_programming, meta_interpreter,
  credulous_reasoning, skeptical_reasoning

Pollock 1987: prima_facie_reason, conclusive_reason, rebutting_defeater,
  undercutting_defeater, warrant, defeat_level, collective_defeat,
  reinstatement, justified_belief, foundational_state
  (self_defeating_argument already existed)

Cayrol 2005: bipolar_argumentation_framework, supported_defeat, indirect_defeat,
  safe_set, d_admissible, s_admissible, c_admissible
  (support_relation already existed)

Modgil 2014: argumentation_system, strict_rule, defeasible_rule,
  undercutting_attack, preference_ordering, structured_argument,
  rationality_postulate, transposition_closure, argument_scheme, rebutting_attack
  (undermining_attack already existed)

Modgil 2018: attack_based_conflict_free, contrariness_function, reasonable_ordering

### Claims extraction COMPLETE - all 5 validated clean
1. Dung_1995_AcceptabilityArguments - 30 claims
2. Pollock_1987_DefeasibleReasoning - 20 claims
3. Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation - 16 claims
4. Modgil_2014_ASPICFrameworkStructuredArgumentation - 16 claims
5. Modgil_2018_GeneralAccountArgumentationPreferences - 18 claims
Total: 100 claims across 5 papers, 0 errors, 0 warnings
