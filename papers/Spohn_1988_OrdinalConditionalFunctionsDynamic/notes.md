---
title: "Ordinal Conditional Functions: A Dynamic Theory of Epistemic States"
authors: "Wolfgang Spohn"
year: 1988
venue: "Causation in Decision, Belief Change, and Statistics II (eds. Harper & Skyrms), Springer"
doi_url: "https://doi.org/10.1007/978-94-009-2865-7_6"
pages: "105-134"
produced_by:
  agent: "Claude Opus 4.6 (1M context)"
  skill: "paper-reader"
  timestamp: "2026-03-29T04:15:52Z"
---
# Ordinal Conditional Functions: A Dynamic Theory of Epistemic States

## One-Sentence Summary
Introduces ordinal conditional functions (OCFs/kappa-functions) as a qualitative, ordinal-valued representation of epistemic states that supports reversible conditionalization and generalized belief change, providing the concrete epistemic state representation that makes iterated revision well-defined.

## Problem Addressed
Deterministic epistemology (belief sets) and probabilistic epistemology are treated as separate; there is no adequate formal framework for the dynamics of belief that is qualitative yet supports reversible, iterated epistemic change. Simple conditional functions (SCFs) are not closed under conditionalization, losing information about deleted empty terms and making epistemic changes irreversible. *(p.105-107)*

## Key Contributions
- Defines **ordinal conditional functions (OCFs)** as a qualitative epistemic state representation mapping propositions to ordinals, with κ(W)=0 and κ(∅)=Ω *(p.115)*
- Shows OCFs generalize both SCFs and well-ordered partitions (WOPs) while being closed under conditionalization *(p.115-117)*
- Defines **A_n-conditionalization** as the general epistemic change operation with firmness parameter n, supporting reversible belief revision *(p.117)*
- Proves commutativity of conditionalization (Theorem 3) and generalized conditionalization (Theorems 4-5) *(p.118-119)*
- Establishes independence concepts for OCFs (probabilistic, conditional) with full parallel to probability theory *(p.120-125)*
- Demonstrates OCFs are the qualitative counterpart of probability measures via connection to Popper measures *(p.125-127)*
- Relates OCFs to Shackle's functions of potential surprise (FPSs) *(p.129-130)*

## Methodology
Axiomatic/constructive approach: defines SCFs first, identifies their deficiency (not closed under conditionalization), then constructs OCFs as the closure. Proves representation theorems, conditionalization theorems, and independence properties. Establishes connections to probability theory via Popper measures.

## Key Equations / Statistical Models

### Simple Conditional Function (SCF)

$$
\kappa: \mathcal{P}(W) \setminus \{\emptyset\} \to \mathbb{N}_0
$$

Where: κ is a function from non-empty subsets of W to natural numbers (including 0), such that:
(a) κ(A ∩ B) ≥ 0, and κ is deductively closed
(b) if κ(A) ∩ B ≠ ∅, then κ(A ∩ B) = κ(A) ∩ B
The key property: κ(A) = 0 for at least one non-empty A ⊆ W.
*(p.108)*

### A-Conditionalization of SCF

$$
\kappa_A(B) = \kappa(A \cap B) - \kappa(A)
$$

Where: κ_A is the new epistemic state after learning A, B is any proposition. This shifts disbelief grades relative to A. *(p.109)*

### Ordinal Conditional Function (OCF) - Definition 4

$$
\kappa: \mathcal{A} \to \mathcal{O} \cup \{\Omega\}
$$

Where: A is a non-empty set of subsets of W closed under complementation and arbitrary intersection, O is an ordinal class, Ω is a distinguished "impossible" element, and κ satisfies:
1. κ(∅) = Ω (contradiction gets maximum disbelief)
2. κ(W) = 0 (tautology gets zero disbelief)
3. For any A ∈ A(∅): κ(A) = min{κ(w) | w ∈ A} (minimum over constituent worlds)
*(p.115)*

### A-part of κ - Definition 5

$$
\kappa(\cdot | A)^* = \kappa(\cdot) - \kappa(A)
$$

Where: the A-part of κ is the restriction of κ to A with κ(A) shifted to 0, defined on all B for which A ∩ B ∈ A. Formally: κ(B|A) = κ(A∩B) - κ(A) for all B with A ∩ B ≠ ∅ and A ∩ B ∈ A.
*(p.117)*

### A_n-Conditionalization of OCF - Definition 6

$$
\kappa_{A,n}(w) = \begin{cases} \kappa(w) - \min(\kappa(A), n) & \text{if } w \in A \\ \kappa(w) - \min(\kappa(\bar{A}), n) & \text{if } w \in \bar{A} \end{cases}
$$

Where: n is the firmness parameter (how firmly A is accepted), A is the learned proposition, Ā is its complement. The parameter n controls the strength of belief change: larger n means firmer acceptance of A. κ_{A,0} is the trivial (no change) case. *(p.117)*

### Commutativity of Conditionalization - Theorem 3

$$
(\kappa_{A,\alpha})_{B,\beta} = (\kappa_{B,\beta})_{A,\alpha} = \kappa'
$$

Where: α, β are ordinals with α + β ≠ 0, and κ' satisfies:
κ'(A ∩ B) = κ(A ∩ B), κ'(Ā ∩ B) = κ(Ā ∩ B) + α, κ'(A ∩ B̄) = κ(A ∩ B̄) + β, κ'(Ā ∩ B̄) = κ(Ā ∩ B̄) + α + β (all shifted by -min over W). This proves that the order of conditionalization does not matter. *(p.118-119)*

### Generalized Conditionalization - Theorem 4

For κ an A-OCF, A, B ∈ A(∅, W) such that κ(A ∩ B) = κ(Ā ∩ B) = 0, and α, β two commuting ordinals:

$$
\kappa_{A,\alpha}(C) = b_n + d_n
$$

Where the sequences b_n, d_n are defined inductively. *(p.118)*

### λ-Conditionalization - Definition 7 and Theorem 5

$$
\kappa_\lambda(w) = \begin{cases} l & \text{if } w \in A_l \\ \kappa(w) & \text{for } w \in \bar{A} \end{cases}
$$

Where: B is a complete subfield of A, λ is an A-OCF, and for all atoms B_i of B and all w ∈ B_i: κ_λ(w) = κ(w) + λ(w|B_i). The measurable coarsening (κ_λ)_B = κ_B. *(p.119)*

### Independence - Definition 8

$$
\kappa(A \cap C) = \kappa(A) + \kappa(C) \quad \forall \text{ atoms } C \text{ of } B
$$

Where: A is independent of B with respect to κ iff for all atoms C of B: κ(B ∩ C) = κ(B) for all B ∈ B and all atoms C of B and κ(A ∩ C) = κ(A) + κ(C). Equivalently (Theorem 8): (a) κ is independent of B, (b) for each B-OCF κ and C ∈ κ'(∅): κ(C|B) = κ(C), (c) κ(B ∩ C) = κ(B) + κ(C) holds. *(p.120-121)*

### Conditional Independence - Definition 10

$$
\kappa(A \cap C | D) = \kappa(A | D) + \kappa(C | D) \quad \forall \text{ atoms } C, D
$$

Where: A is conditionally independent of B given D iff for all atoms C of B and D_j of D: κ(A ∩ C | D_j) = κ(A | D_j) + κ(C | D_j). *(p.123)*

### FPS-OCF Correspondence

Shackle's functions of potential surprise (FPSs) satisfy *(p.129)*:
1. y(∅) = 1
2. y(A) = 0 or y(Ā) = 0 or both
3. y(A ∪ B) = min{y(A), y(B)}

These are identical with OCF Theorem 2 conditions (a) and (c). FPSs are displaced by (1)-(4) and are purely ordinal concepts. FPSs as displayed by (1)-(4) are purely ordinal. *(p.129-130)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Disbelief grade | κ(A) | ordinal | 0 for W | 0 to Ω | 115 | 0 = maximally plausible, higher = more disbelieved |
| Firmness parameter | n | ordinal | — | ≥ 0 | 117 | Controls strength of belief change in A_n-conditionalization |
| Maximum disbelief | Ω | ordinal | ∞ | — | 115 | κ(∅) = Ω always; represents impossibility |

## Methods & Implementation Details
- W is a non-empty set of possible worlds (or sample space in probabilistic terms). A proposition is a subset of W. *(p.108)*
- An SCF κ assigns natural number disbelief grades to propositions; κ(A) = 0 means A is among the most plausible propositions. *(p.108)*
- The net content of an epistemic state at time t is the set of propositions believed true: {A | A ⊆ W, κ(A̅) > 0}. *(p.108-109)*
- SCFs are equivalent to well-ordered partitions (WOPs): the sequence ⟨E_0, E_1, ...⟩ where E_n = {w | κ(w) = n}. Theorem 1 proves bijection. *(p.110-111)*
- OCFs extend to ordinal-valued (not just natural number) disbelief grades, allowing transfinite levels. *(p.115)*
- A_n-conditionalization preserves the A-part and the Ā-part of κ while shifting their relative positions — it changes only the relative disbelief between A-worlds and Ā-worlds by the firmness parameter n. *(p.117)*
- Conditionalization is commutative (Theorem 3): learning A then B gives the same result as learning B then A, provided the firmness parameters are the same. *(p.118)*
- Generalized conditionalization (Theorem 5) handles learning a complete partition (not just a single proposition). *(p.119)*
- Independence (Definition 8) directly parallels probabilistic independence but uses additive κ-values instead of multiplicative probabilities. *(p.120)*
- Conditional independence (Definition 10) also parallels the probabilistic version. *(p.123)*

## Figures of Interest
- No figures in this paper — it is entirely formal/algebraic.

## Results Summary
- OCFs solve the closure problem of SCFs: the class of all OCFs is closed under A_n-conditionalization, unlike SCFs which lose empty terms and become irreversible. *(p.115-117)*
- OCFs support reversible epistemic change: if you conditionalize by A with firmness n, you can recover the original state. *(p.117)*
- Commutativity means the order of evidence acquisition doesn't matter (for the same firmness levels). *(p.118)*
- Independence and conditional independence for OCFs have the same structural properties as for probability measures. *(p.120-125)*
- OCFs are the qualitative counterpart of probability measures: there exists a homomorphism from nonstandard probability measures to OCFs. *(p.125-127)*
- OCFs subsume Shackle's functions of potential surprise as a special case. *(p.129-130)*

## Limitations
- The paper works only at the "surface level" of first-order epistemic states — it explicitly defers higher-order epistemic states (beliefs about beliefs). *(p.109)*
- The paper does not provide a language for conditional sentences — it mentions this as an important open direction (related ideas in Section 8 point 2). *(p.128)*
- OCFs use ordinals rather than real-valued measures, making them qualitative — this is both a feature (simpler) and limitation (no ratio-scale comparisons). *(p.130)*
- The paper acknowledges that the connection between OCFs and Gardenfors (1984) belief revision framework provides only a "restricted solution" since Gardenfors' approach does not track enough structure. *(p.129)*

## Arguments Against Prior Work
- **Against SCFs (his own earlier formalism):** SCFs are not closed under conditionalization because empty terms get deleted, making epistemic changes irreversible. The central problem of Section 3. *(p.112-114)*
- **Against Gardenfors (1984) belief sets:** Belief sets with selection functions provide only a restricted solution to the dynamics problem because they don't track the fine-grained ordinal structure needed for iterated revision. *(p.129)*
- **Against purely probabilistic approaches:** Probabilities conditioned on propositions with probability 0 are undefined in standard probability theory; OCFs handle this naturally since κ(A) = 0 just means "most plausible," not "certain." *(p.125)*

## Design Rationale
- **Why ordinals over naturals:** Natural numbers suffice for finitely many worlds but ordinals are needed for the general case; the move to ordinals also gives closure under conditionalization. *(p.115, 130)*
- **Why the firmness parameter n:** Without n, conditionalization would always set κ(A) to exactly 0 (full acceptance). The parameter n allows graded acceptance — you can learn A with varying degrees of confidence. *(p.117)*
- **Why A_n-conditionalization preserves both parts:** By shifting only the relative positions of the A-part and Ā-part (not restructuring within them), the operation preserves all relative disbelief orderings within each part, ensuring reversibility. *(p.117)*
- **Why not just use probabilities:** OCFs provide a qualitative analogue that avoids the problem of conditioning on probability-zero events, while preserving the structural properties (independence, conditional independence) that make probability theory useful. *(p.125-127)*

## Testable Properties
- κ(∅) = Ω for any OCF *(p.115)*
- κ(W) = 0 for any OCF *(p.115)*
- κ(A) = min{κ(w) | w ∈ A} for any proposition A *(p.115)*
- A_n-conditionalization with n=0 is the identity: κ_{A,0} = κ *(p.117)*
- Commutativity: (κ_{A,α})_{B,β} = (κ_{B,β})_{A,α} *(p.118)*
- After A_n-conditionalization: κ_{A,n}(A) = 0 when n ≥ κ(A) (A becomes believed) *(p.117)*
- Independence is symmetric: A independent of B iff B independent of A (Theorem 8) *(p.121)*
- If A independent of B and B independent of C given A, then A independent of B ∩ C (Theorem 11) *(p.123)*
- κ(A ∩ B) = κ(A) + κ(B) when A and B are independent *(p.120)*
- OCFs subsume WOPs: each WOP corresponds to exactly one OCF and vice versa (Theorem 1 generalized) *(p.115)*

## Relevance to Project
This is the foundational paper for ordinal epistemic state representation in propstore. OCFs provide:
1. **The concrete epistemic state for iterated revision** — Darwiche & Pearl 1997 references OCFs as the epistemic state that makes their postulates C1-C4 satisfiable. Without OCFs, we have no formal representation of "how much" a proposition is believed/disbelieved.
2. **The distance metric for belief merging** — OCF values provide the ordinal distances needed for merging operations (Konieczny & Pino Perez style).
3. **A qualitative counterpart to subjective logic opinions** — OCF disbelief grades can be mapped to/from opinion uncertainty, providing a bridge between the argumentation layer and the belief revision layer.
4. **Reversible belief change** — A_n-conditionalization with explicit firmness parameters means the system can track how firmly each piece of evidence was incorporated and potentially retract it.
5. **Independence structure** — OCF independence parallels probabilistic independence, enabling the ATMS assumption-based reasoning to interface cleanly with belief revision.

## Open Questions
- [ ] How exactly do OCF κ-values map to Josang opinion components (b, d, u)?
- [ ] Can the firmness parameter n be derived from source reliability or argument strength?
- [ ] How does A_n-conditionalization interact with ASPIC+ preference orderings?
- [ ] What is the computational complexity of maintaining OCFs over a large proposition space?
- [ ] How to handle the transfinite ordinal case in practice — are natural numbers sufficient for our use cases?

## Related Work Worth Reading
- Gardenfors (1984) "Epistemic importance and minimal changes of belief" — the belief set approach OCFs improve upon
- Harper (1976) "Rational belief change, Popper functions and counterfactuals" — connection to Popper measures
- Shackle (1969) *Decision, Order, and Time in Human Affairs* — functions of potential surprise that OCFs subsume
- Lewis (1973) *Counterfactuals* — similarity spheres that OCFs can model
- Darwiche & Pearl (1997) — postulates C1-C4 for iterated revision that OCFs satisfy -> NOW IN COLLECTION: [[Darwiche_1997_LogicIteratedBeliefRevision]]
- Spohn (1988) "Stochastic independence, causal independence, and shieldability" — companion paper on independence

## Collection Cross-References

### Already in Collection
- [[Darwiche_1997_LogicIteratedBeliefRevision]] — builds bullet operator directly on OCFs; C1-C4 postulates regulate iterated revision using Spohn's (mu,m)-conditionalization
- [[Alchourron_1985_TheoryChange]] — AGM postulates that OCFs satisfy; Spohn's framework extends AGM by providing the epistemic state structure needed for iterated revision
- [[Booth_2006_AdmissibleRestrainedRevision]] — classifies revision operators (natural, lexicographic, restrained) that operate on OCF-based epistemic states

### New Leads (Not Yet in Collection)
- Gardenfors (1984) "Epistemic importance and minimal changes of belief" — the belief set approach OCFs improve upon; cited extensively
- Harper (1976) "Rational belief change, Popper functions and counterfactuals" — connection between Popper measures and OCFs
- Shackle (1969) *Decision, Order, and Time in Human Affairs* — functions of potential surprise that OCFs subsume
- Jeffrey (1965) *The Logic of Decision* — probability kinematics that generalized conditionalization parallels

### Supersedes or Recontextualizes
- [[Alchourron_1985_TheoryChange]] — OCFs provide the epistemic state structure that AGM belief sets lack; AGM operates on belief sets (sets of sentences) while OCFs track ordinal disbelief grades over worlds, enabling iterated revision

### Cited By (in Collection)
- [[Darwiche_1997_LogicIteratedBeliefRevision]] — uses OCFs as the mathematical foundation for the bullet operator and (mu,m)-conditionalization
- [[Booth_2006_AdmissibleRestrainedRevision]] — cites OCFs as the epistemic state representation underlying all ranking-based revision operators
- [[Halpern_2005_CausesExplanationsStructuralModel]] — cites in bibliography for epistemic state foundations

### Conceptual Links (not citation-based)
- [[Dixon_1993_ATMSandAGM]] — **Strong.** Dixon proves ATMS context switching = AGM operations. OCFs provide the richer epistemic state that AGM alone cannot capture, suggesting ATMS labels could encode OCF disbelief grades to enable iterated revision beyond what Dixon's AGM bridge provides.
- [[Konieczny_2002_MergingInformationUnderConstraints]] — **Strong.** Konieczny's IC merging framework uses distance-based pre-orders on interpretations; OCF values provide a natural distance metric for these pre-orders, potentially grounding the abstract distance functions in Spohn's ordinal disbelief grades.
- [[Bonanno_2010_BeliefChangeBranchingTime]] — **Moderate.** Bonanno's branching-time belief revision extends iterated revision to temporal structures; OCFs provide the epistemic state representation that branching-time functions B(h,K,phi) operate on.
