---
title: "Semantical Considerations on Nonmonotonic Logic"
authors: "Robert C. Moore"
year: 1985
venue: "Artificial Intelligence 25 (1985) 75-94"
doi_url: "https://doi.org/10.1016/0004-3702(85)90042-6"
---

# Semantical Considerations on Nonmonotonic Logic

## One-Sentence Summary
Introduces autoepistemic logic as a formally grounded alternative to McDermott and Doyle's nonmonotonic logic, providing an intuitively based possible-worlds semantics that is both sound and complete, and explains why McDermott-Doyle systems exhibit pathological behavior.

## Problem Addressed
McDermott and Doyle's nonmonotonic logics [1,2] have peculiarities that suggest they fail to capture the intuitions behind nonmonotonic reasoning. Their first logic gives too weak a notion of consistency; their second attempt (S5-based) collapses to ordinary monotonic S5. Moore argues these problems arise from conflating two distinct forms of reasoning: default reasoning and autoepistemic reasoning. *(p.77)*

## Key Contributions
- Distinguishes **default reasoning** (drawing plausible inferences from incomplete information) from **autoepistemic reasoning** (reasoning about one's own beliefs), arguing these are fundamentally different forms of nonmonotonic reasoning *(p.77-78)*
- Introduces **autoepistemic logic** (AEL): a propositional logic augmented with a modal operator L meaning "is believed" *(p.80)*
- Provides a formal **possible-worlds semantics** for autoepistemic logic based on the notion of an ideally rational agent reflecting on their own beliefs *(p.80-81)*
- Defines **stable autoepistemic theories** via three closure conditions and proves soundness/completeness theorems connecting syntactic stability with semantic completeness *(p.83-84)*
- Shows that McDermott-Doyle nonmonotonic logic's peculiarities (including S5 collapse) are explained by the missing condition {LP | P in T} from their fixed-point definition *(p.86)*
- Proves that weak S5 axioms are redundant in autoepistemic logic (Theorem 4.1, Corollary 4.2) *(p.89)*

## Methodology
Moore defines autoepistemic logic by analogy with an ideally rational agent reasoning about their own beliefs. The key insight is that the modal operator L should be interpreted relative to the agent's complete belief set (making it indexical/context-sensitive), unlike standard modal logic where necessity has a fixed interpretation. *(p.79-80)*

The formal development proceeds in two stages:
1. Define propositional interpretation, autoepistemic interpretation, and autoepistemic model of a theory T *(p.80-81)*
2. Define soundness and completeness semantically, then characterize them syntactically via stability conditions *(p.81-84)*

## Key Definitions

### Autoepistemic Logic Language
Propositional logic augmented with modal operator L, where LP means "P is believed by the agent." Define M (consistency) as ~L~, i.e., "it is consistent to believe P." *(p.80)*

### Propositional Interpretation of Theory T
An assignment of truth-values to formulas of T consistent with usual propositional logic truth recursion, treating LP as propositional constants. *(p.80)*

### Autoepistemic Interpretation of Theory T
A propositional interpretation of T in which, for every formula P, LP is true iff P is in T. *(p.81)*

### Autoepistemic Model of Theory T
An autoepistemic interpretation of T in which all formulas of T are true. *(p.81)*

### Soundness
Theory T is **sound** with respect to premises A iff every autoepistemic interpretation of T in which all formulas of A are true is an autoepistemic model of T. *(p.81)*

### Semantic Completeness
Theory T is **semantically complete** iff T contains every formula that is true in every autoepistemic model of T. *(p.82)*

### Stable Autoepistemic Theory
A set of formulas T satisfying: *(p.83)*
1. If P_1,...,P_n in T and P_1,...,P_n |- Q, then Q in T (closure under tautological consequence)
2. If P in T, then LP in T (positive introspection)
3. If P not in T, then ~LP in T (negative introspection)

### Grounded Theory
T is **grounded** in premises A iff T is the set of tautological consequences of:

$$
A \cup \{LP \mid P \in T\} \cup \{\sim LP \mid P \notin T\}
$$
*(p.84)*

### Stable Expansion
The stable expansions of A are the autoepistemic theories that are both stable and grounded in A. *(p.84-85)*

## Key Equations

$$
T \text{ is stable iff } T = \text{taut. consequences of } A \cup \{LP \mid P \in T\} \cup \{\sim LP \mid P \notin T\}
$$
Where: T = autoepistemic theory, A = initial premises, L = belief operator
*(p.84)*

Fixed point of McDermott-Doyle (for comparison):

$$
T \text{ is a fixed point of } A \text{ just in case } T = \text{taut. consequences of } A \cup \{\sim LP \mid P \notin T\}
$$
Where: the crucial difference is the missing {LP | P in T} component
*(p.86)*

Weak S5 axiom schemata: *(p.89)*

$$
L(P \to Q) \to (LP \to LQ)
$$

$$
LP \to LLP
$$

$$
\sim LP \to L \sim LP
$$

## Parameters

This is a theoretical logic paper with no numerical parameters.

## Implementation Details

### Stable Expansion Computation
- A stable expansion of A is a fixed point: T must equal the tautological consequences of A augmented with {LP | P in T} and {~LP | P not in T} *(p.84)*
- There may be zero, one, or multiple stable expansions for a given set of premises *(p.85)*
- Example of multiple expansions: premises {~LP -> Q, ~LQ -> P} yield two stable expansions, one containing P but not Q, the other containing Q but not P *(p.85)*
- Example of no stable expansion: premises {~LP -> P} have no stable expansion because including P leaves it ungrounded and excluding P forces its inclusion *(p.85)*

### Relationship to McDermott-Doyle Fixed Points
- McDermott-Doyle's fixed point definition is equivalent to: T is the set of tautological consequences of A union {~LP | P not in T} *(p.86)*
- This OMITS {LP | P in T}, which means their agents are omniscient about what they don't believe but ignorant about what they do believe *(p.86)*
- This omission explains all the peculiarities of their logic *(p.86)*

### Modal Logic Comparisons
- McDermott's modal nonmonotonic logics (T, S4, S5) alter the fixed-point definition in two ways: (1) change "tautological consequences" to "modal consequences" using P|- LP as inference rule, and (2) restrict to theories including standard modal logic axioms *(p.87)*
- Adding P|- LP as inference rule means all modal fixed points of A are stable expansions of A, but not vice versa *(p.87)*
- In autoepistemic logic, if P can be in a stable expansion then {LP -> P} justifies it; in McDermott's logic, P must have a derivation not relying on LP *(p.87)*
- The S5 collapse: nonmonotonic S5 collapses to monotonic S5 because the S5 axiom schema ~LP -> L ~LP combined with LP -> P allows LP -> P to sanction any belief, making all formulas absent from fixed points absent from all fixed points, hence no nonmonotonic inferences survive *(p.88)*

## Figures of Interest
No figures in this paper.

## Results Summary
- **Theorem 3.1:** If T is a stable autoepistemic theory, then any autoepistemic interpretation of T that is a propositional model of the objective formulas of T is an autoepistemic model of T. *(p.83)*
- **Theorem 3.2:** If two stable autoepistemic theories contain the same objective formulas, then they contain exactly the same formulas. *(p.84)*
- **Theorem 3.3:** An autoepistemic theory T is semantically complete if and only if T is stable. *(p.84)*
- **Theorem 3.4:** An autoepistemic theory T is sound with respect to an initial set of premises A if and only if T is grounded in A. *(p.84)*
- **Theorem 4.1:** If P is true in every autoepistemic interpretation of T, then T is grounded in A union {P} if and only if T is grounded in A. *(p.89)*
- **Corollary 4.2:** If P is true in every autoepistemic interpretation of T, then T is a stable expansion of A union {P} if and only if T is a stable expansion of A. *(p.89)*

## Limitations
- Limited to propositional autoepistemic logic; quantification into the scope of L raises additional problems that are set aside *(p.80)*
- The paper models an ideally rational agent with unbounded resources — this is a competence model, not a performance model *(p.81)*
- Multiple stable expansions or no stable expansion can occur, and the paper does not resolve which expansion to prefer when there are multiple *(p.85)*
- Does not address combining autoepistemic reasoning with default reasoning (mentioned briefly in footnote 2) *(p.79)*

## Arguments Against Prior Work
- McDermott and Doyle's first nonmonotonic logic [1] gives too weak a notion of consistency: MP is not inconsistent with ~P, allowing a theory to simultaneously assert P is consistent and P is false *(p.77)*
- McDermott's nonmonotonic S5 [2] collapses to ordinary monotonic S5, losing all nonmonotonic character *(p.77)*
- The core problem: McDermott and Doyle confuse default reasoning with autoepistemic reasoning — their systems talk about default reasoning but actually model autoepistemic reasoning *(p.77-78)*
- McDermott-Doyle's nonmonotonic inference is not a form of valid inference but rather plausible/defeasible reasoning that lacks the guarantee of truth-preservation *(p.78)*
- The M operator in McDermott-Doyle should be read as "is consistent with the agent's beliefs" not "is consistent" in the bare logical sense — this reinterpretation reveals the autoepistemic character *(p.78)*
- The fixed-point definition of McDermott-Doyle is missing the positive introspection component {LP | P in T}, making agents omniscient about non-beliefs but ignorant about beliefs *(p.86)*

## Design Rationale
- L is taken as primitive ("is believed") rather than M ("is consistent") because the semantics is based on belief, not consistency *(p.80)*
- Stability conditions (1)-(3) are chosen to model an ideally rational agent: (1) = logical omniscience, (2) = positive introspection, (3) = negative introspection *(p.83)*
- Groundedness is required in addition to stability to ensure beliefs are justified by the premises, not self-supporting *(p.84)*
- The paper uses propositional logic (not first-order or modal) to avoid complications from quantifying into autoepistemic contexts *(p.80)*

## Testable Properties
- Any stable autoepistemic theory satisfies conditions (4) and (5): If LP in T then P in T; if ~LP in T then P not in T *(p.83)*
- Two stable theories with same objective formulas must be identical (Theorem 3.2) *(p.84)*
- Stability is equivalent to semantic completeness (Theorem 3.3) *(p.84)*
- Soundness w.r.t. premises A is equivalent to groundedness in A (Theorem 3.4) *(p.84)*
- Weak S5 axioms are tautologies of propositional logic when LP treated as atoms, so adding them as premises changes nothing (Corollary 4.2) *(p.89)*
- The intersection of all stable expansions equals the set of formulas in all fixed points for modal nonmonotonic logics (since every modal fixed point is a stable expansion) *(p.86-87)*

## Relevance to Project
This paper is foundational for understanding the epistemic dimension of argumentation. Autoepistemic logic provides the formal basis for reasoning about what an agent believes vs. what is merely consistent — directly relevant to propstore's ATMS-style assumption management where the system must track what is believed under which assumption sets without committing to a single expansion. The distinction between default reasoning and autoepistemic reasoning maps onto the distinction between defeasible inference (argumentation layer) and belief maintenance (ATMS layer). The multiple-stable-expansion phenomenon parallels Dung's multiple extensions.

## Open Questions
- [ ] How does autoepistemic logic relate to Dung's argumentation frameworks? (Both produce multiple "acceptable" belief sets)
- [ ] Can the groundedness requirement be used to define preference orderings over extensions?
- [ ] What is the relationship between Moore's stable expansions and ATMS contexts/environments?
- [ ] How does combining autoepistemic + default reasoning (mentioned in footnote 2) relate to ASPIC+ structured argumentation?

## Related Work Worth Reading
- McDermott, D. and Doyle, J., Non-monotonic logic I, Artificial Intelligence 13 (1,2) (1980) 41-72
- McDermott, D., Nonmonotonic logic II: Nonmonotonic modal theories, J. ACM 29 (1) (1982) 33-57
- Stalnaker, R., A note on non-monotonic modal logic, Department of Philosophy, Cornell University, unpublished manuscript
- Minsky, M., A framework for representing knowledge, MIT AI Lab, AIM-306, 1974
