---
title: "Causes and Explanations: A Structural-Model Approach. Part I: Causes"
authors: "Joseph Y. Halpern, Judea Pearl"
year: 2005
venue: "British Journal for the Philosophy of Science 56(4)"
doi_url: "https://doi.org/10.1093/bjps/axi147"
---

# Causes and Explanations: A Structural-Model Approach. Part I: Causes

## One-Sentence Summary

Provides a formal definition of actual causality using structural equation models (causal models) that handles preemption, overdetermination, and other classic problem cases via counterfactual reasoning with contingent interventions.

## Problem Addressed

Traditional counterfactual definitions of causality (Lewis, Hume) fail on cases of preemption, overdetermination, and late preemption. The "but-for" test (A caused B iff B would not have occurred but for A) breaks down when multiple sufficient causes exist. This paper provides a formal definition using structural equations that handles these cases correctly. *(p.0)*

## Key Contributions

- A formal definition of actual cause (Definition 3.1) using structural equation models with three conditions: AC1 (factual), AC2 (counterfactual with contingency), AC3 (minimality) *(p.2)*
- Demonstrates the definition handles classic problematic examples: forest fire with lightning/arson, voting scenarios, desert traveler, railroad switches, Billy/Suzy rock-throwing *(p.3-7)*
- Shows that the choice of causal model (what variables to include, what values they take) is crucial and can affect causal judgments *(p.7-8)*
- Introduces a ranking-based extension using "normality" to handle cases where structural contingencies should have varying plausibility *(p.8)*

## Methodology

Uses structural equation models (SEMs) as the formal framework. A causal model M = (S, F) where S = (U, V, R) is a signature with exogenous variables U, endogenous variables V, and ranges R, and F is a set of structural equations — one per endogenous variable — defining its value as a function of other variables. A causal setting pairs a model with a context (assignment to exogenous variables). Causality is then defined via interventions (setting variables to non-actual values) and checking whether the outcome changes. *(p.1-2)*

## Key Definitions

### Causal Model

A causal model M over signature S = (U, V, R) is a pair (S, F) where F = {F_X : X in V} and each F_X maps values of all other variables to R(X). *(p.1)*

### Causal Network

A causal network is a DAG with nodes for variables in U union V, with edges from parents of X to X for each structural equation F_X. Exogenous variables have no parents in the causal network. *(p.1)*

### Context

A context u-vector is an assignment of values to all exogenous variables U. Given context u, the structural equations determine a unique value for every endogenous variable. *(p.1-2)*

### Definition 3.1: Actual Cause *(p.2)*

X = x is an actual cause of phi in (M, u) if the following three conditions hold:

**AC1.** (M, u) |= (X = x) AND phi. (That is, both X = x and phi are true in the actual world.) *(p.2)*

**AC2.** There exists a partition (Z, W) of V with X in Z and some setting (x', w') of the variables in (X, W) such that:

(a) (M, u) |= (X = x' AND W = w') => NOT phi. In words, changing X to x' and W to w' changes phi from true to false. *(p.2)*

(b) (M, u) |= (X = x AND W = w' AND Z = z) => phi for all subsets Z' of Z and z values consistent with setting X = x. In words, setting W to w' should have no effect on phi as long as X is kept at its current value x. *(p.2)*

**AC3.** X is minimal; no proper subset of X satisfies AC1 and AC2. *(p.2)*

### Key Elements of AC2

- The partition (Z, W) separates endogenous variables into Z (variables allowed to vary freely under their equations) and W (variables frozen at potentially non-actual values w')
- AC2(a) is the counterfactual test: there must exist some intervention that changes the outcome
- AC2(b) is the stability condition: freezing W at w' while keeping X at actual value x must preserve phi, ensuring W's non-actual values don't independently affect the outcome
- The "contingency" W = w' can be thought of as setting up circumstances under which the but-for test works *(p.2-3)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Exogenous variables | U | - | - | context-dependent | 1 | External factors not modeled |
| Endogenous variables | V | - | - | model-dependent | 1 | Variables with structural equations |
| Range function | R | - | - | finite sets | 1 | Possible values for each variable |
| Structural equations | F | - | - | deterministic functions | 1 | One per endogenous variable |
| Context | u | - | - | assignment to U | 1 | Determines actual world |

## Implementation Details

- A causal model is recursive (acyclic) if the causal network is a DAG. All examples in this paper use recursive models. *(p.1)*
- Given a context u, computing the actual values of all endogenous variables requires forward propagation through the DAG. *(p.1)*
- Interventions are modeled by replacing structural equations: to set X = x', replace F_X with the constant function x'. *(p.1-2)*
- AC2 requires searching over partitions (Z, W) of V \ X and over possible values (x', w'). This is computationally expensive in general. *(p.2)*
- The beam criterion (for specific causal structures) only depends on relationship between a variable and its parents in the causal diagram — a tractable special case. *(p.3)*

## Figures of Interest

- **Fig 1 (p.4):** Causal network for forest fire with two scenarios (disjunctive vs conjunctive). Shows how the same events lead to different causal judgments based on model structure.
- **Fig 2 (p.5):** Rock-throwing scenario (Billy and Suzy). Classic late preemption example.
- **Fig 3 (p.6):** Billy's medical condition model — demonstrates how adding variables changes causal verdicts.
- **Fig 4 (p.6):** Extended version of AC2(b) example showing the need for the stability condition.
- **Fig 5 (p.7):** The switch/railroad example — illustrates sensitivity to model granularity.
- **Fig 6 (p.8):** Extended model showing how ranking/normality can resolve structural contingency issues.

## Results Summary

The definition handles the following classic cases correctly:

1. **Forest fire (disjunctive):** Both lightning and arson are causes of the fire (overdetermination handled by freezing one while testing the other). *(p.3-4)*
2. **Forest fire (conjunctive):** Both matches are required — straightforward but-for causation. *(p.4)*
3. **Voting scenarios:** In 11-0 vote, each voter is a cause; definition correctly identifies this via AC2 contingencies. *(p.4)*
4. **Billy and Suzy (late preemption):** Suzy's throw is the cause (her rock hits first); Billy's is not, because his rock hitting (BH=1) only happens when Suzy's rock doesn't hit (SH=0), and this contingency doesn't satisfy AC2(b). *(p.5)*
5. **Desert traveler:** Correctly identifies the poisoner as the cause of death, not the person who poked a hole in the canteen (since the traveler would have died anyway from the poison). *(p.4)*
6. **Railroad switch:** Causality depends on granularity of the model — whether intermediate track segments are modeled. *(p.7)*
7. **Larry the Loanshark (bogus prevention):** Correctly handles cases where an apparent preventer's action doesn't qualify as a cause. *(p.7-8)*

## Limitations

- The definition is sensitive to the choice of causal model — which variables are included, how they're structured, what their ranges are. The authors acknowledge this is both a feature and a limitation. *(p.7-8)*
- No general theory for how to make modeling choices (which variables to include, what ranges to use). The authors state "we do not have a general theory" for making appropriate choices. *(p.8)*
- Computational complexity of checking AC2 is high in general (exponential in number of variables due to partition search). *(p.2)*
- Only handles deterministic structural equations in this formulation. Probabilistic causation requires extension. *(p.1)*
- The ranking/normality extension is presented as preliminary — "a slight modification" — and not fully developed. *(p.8)*

## Arguments Against Prior Work

- Lewis's counterfactual definition fails on overdetermination: if two assassins both fire and both bullets are sufficient, neither is a but-for cause, yet intuitively both are causes. *(p.0)*
- The "fragility" strategy (making events more fine-grained to restore counterfactual dependence) is criticized as ad hoc. *(p.0)*
- Simple regularity theories and NESS-test approaches don't handle late preemption correctly. *(p.0)*
- Previous structural equation approaches (by the same authors, Halpern & Pearl 2001) had problems pointed out by Hopkins and Pearl [2003] — the updated definition fixes these. *(p.0)*

## Design Rationale

- Structural equations are chosen over possible-worlds semantics because they make interventions explicit and compositional. *(p.1)*
- The partition (Z, W) in AC2 allows "freezing" some variables at non-actual values to create contingencies under which the but-for test works — this is what handles preemption. *(p.2-3)*
- AC2(b) (the stability condition) prevents spurious causes by requiring that the frozen variables don't independently flip the outcome. *(p.2)*
- AC3 (minimality) prevents conjunctive inflation — without it, any superset of a cause would also count as a cause. *(p.2)*
- Recursive (acyclic) models are used because they guarantee unique solutions; non-recursive models would require additional machinery. *(p.1)*

## Testable Properties

- If X = x is an actual cause of phi, then X = x and phi must both be true in the actual world (AC1). *(p.2)*
- Every actual cause must have a counterfactual witness: some intervention that changes the outcome (AC2a). *(p.2)*
- Actual causes are minimal: no proper subset of the cause variables satisfies the definition (AC3). *(p.2)*
- In a model with two independent sufficient causes (overdetermination), each is individually an actual cause. *(p.3-4)*
- In late preemption (A's effect arrives before B's would have), A is a cause and B is not. *(p.5)*
- Adding variables to a model can change causal verdicts — causality is model-relative. *(p.6-7)*
- The beam criterion (a simplification) is equivalent to the full definition when the causal structure has no "structural contingencies" — i.e., when the relationship between a variable and the outcome depends only on its parents in the DAG. *(p.3)*

## Relevance to Project

This paper is foundational for any system that needs to reason about actual causation in structured domains. For propstore:

1. **Argumentation layer:** The structural equation framework provides a rigorous way to model causal arguments. When claims conflict about what caused what, Definition 3.1 provides formal criteria for adjudication.
2. **Explanation layer:** The companion paper (Part II) builds explanations on top of this causation definition — relevant for rendering explanations of why certain claims are accepted/defeated.
3. **Non-commitment discipline:** The paper's emphasis on model-relativity (same events, different causal models, different verdicts) aligns perfectly with propstore's principle of holding multiple rival normalizations without forcing one to be canonical.
4. **Structural equations as claims:** Each structural equation F_X can be viewed as a claim about causal mechanism — these can be stored, contested, and argued about within the propstore framework.

## Open Questions

- [ ] How does computational complexity of AC2 checking scale for realistic models? (Eiter & Lukasiewicz 2002 address tractable cases)
- [ ] How does the 2015 Halpern modification (arxiv 1505.00162) change the definition and its properties? [Addressed by Halpern_2015_ModificationHalpern-PearlDefinitionCausality - it restricts AC2 witnesses so non-causal variables may be held only at their actual values, removes the separate sufficiency clause, and lowers the general decision problem to D_1^P-complete.]
- [ ] Can the ranking/normality extension be formalized as argumentation preferences?
- [ ] How does this relate to ASPIC+ preference orderings in the argumentation layer?

## Collection Cross-References

### Already in Collection
- (none — no papers in the collection directly cite this paper or are cited by it)

### New Leads (Not Yet in Collection)
- Pearl (2000) — "Causality: Models, Reasoning, and Inference" — comprehensive textbook treatment of structural causal models
- Eiter & Lukasiewicz (2002) — tractable cases for HP causality checking

### Now in Collection (previously listed as leads)
- [A Modification of the Halpern-Pearl Definition of Causality](../Halpern_2015_ModificationHalpern-PearlDefinitionCausality/notes.md) - modifies the HP AC2 witness discipline by allowing non-causal variables in the contingency only at their actual values; this directly answers the open question about how the 2015 version changes the definition and complexity.

### Supersedes or Recontextualizes
- (none in collection)

### Cited By (in Collection)
- [A Modification of the Halpern-Pearl Definition of Causality](../Halpern_2015_ModificationHalpern-PearlDefinitionCausality/notes.md) - cites the 2005 HP definition as the updated baseline it simplifies and strengthens.

### Conceptual Links (not citation-based)
- [[Ginsberg_1985_Counterfactuals]] — **Strong.** Ginsberg formalizes counterfactual reasoning via three-valued truth functions and closure operations, proving equivalence with Lewis's possible-worlds semantics (Theorem 4). Halpern-Pearl use counterfactuals as the core mechanism for causality but operationalize them via structural equations and interventions rather than possible worlds. Both papers share the fundamental insight that counterfactual evaluation requires determining what to hold fixed and what to vary — Ginsberg via sublanguage selection, HP via the (Z, W) partition in AC2.
- [[deKleer_1984_QualitativePhysicsConfluences]] — **Moderate.** De Kleer's "mythical causality" provides causal explanations of device behavior using information-passing between components in a partial temporal ordering, while HP causality defines actual causation via structural equations and interventions. Both address the question of "what caused what" in a formal system, but at different levels: de Kleer's causality is about explanation generation in qualitative physics, while HP's is about the metaphysics of actual causation. The structural equation framework could potentially formalize de Kleer's component models.

## Related Work Worth Reading

- Halpern [2015] "A Modification of the Halpern-Pearl Definition of Causality" — updated definition addressing remaining problems -> NOW IN COLLECTION: [A Modification of the Halpern-Pearl Definition of Causality](../Halpern_2015_ModificationHalpern-PearlDefinitionCausality/notes.md)
- Halpern & Pearl [2001/2005] Part II: Explanations — companion paper on causal explanation
- Pearl [2000] "Causality: Models, Reasoning, and Inference" — comprehensive textbook treatment
- Eiter & Lukasiewicz [2002] — tractable cases for HP causality
- Chockler & Halpern — degree of responsibility and blame extensions
- Hopkins & Pearl [2003] — problems with original 2001 definition that motivated this update
