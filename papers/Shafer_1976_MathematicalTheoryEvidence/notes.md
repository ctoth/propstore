---
title: "A Mathematical Theory of Evidence"
authors: "Glenn Shafer"
year: 1976
venue: "Princeton University Press"
doi_url: "https://doi.org/10.2307/j.ctv10vm1qb"
publisher: "Princeton University Press"
note: "Only 32-page preview available (front matter + Ch.1 pp.3-16 of 297-page book). Full book covers 12 chapters."
---

# A Mathematical Theory of Evidence

## One-Sentence Summary
Foundational monograph establishing Dempster-Shafer theory: a calculus of belief functions that generalizes probability by replacing the additivity axiom with a weaker superadditivity condition, enabling representation of ignorance and combination of independent evidence via Dempster's rule.

## Problem Addressed
Classical probability theory (Bayesian approach) requires that degrees of belief be additive: Bel(A) + Bel(not-A) = 1. This forces one to assign precise probabilities even in the absence of evidence, making it impossible to distinguish "I believe A to degree 0.5" from "I have no information about A." Shafer develops a theory where partial ignorance can be explicitly represented. *(p.3-4)*

## Key Contributions
- **Belief functions** as a generalization of probability: Bel satisfies superadditivity (weaker than additivity), allowing Bel(A) + Bel(not-A) < 1 *(p.5)*
- **Dempster's rule of combination** (orthogonal sum) for pooling evidence from independent sources *(p.6)*
- **Simple support functions** as the atomic building blocks of evidence *(p.7)*
- **Separable support functions** as combinations of simple support functions *(p.7)*
- **Weight of evidence** as a logarithmic transform: w = -log(1-s) *(p.8)*
- **Weight-of-conflict conjecture** for decomposing general belief functions *(p.8)*
- **Quasi support functions** as limits of support functions *(p.8-9)*
- **Frames of discernment** as the finite sets over which belief is defined *(p.5)*
- Bayesian probability as a special (limiting) case of the theory *(p.4)*
- Clear distinction between **chance** (objective frequency) and **degree of belief** (epistemic state) *(p.9-16)*

## Methodology
The book develops belief function theory axiomatically. Starting from three axioms defining belief functions over finite frames of discernment, it builds up through simple support functions, Dempster's rule, weights of evidence, compatible frames, and general support functions. Each chapter has a mathematical appendix with formal proofs. *(p.10)*

## Key Equations

### Belief Function Axioms
A function Bel: 2^Theta -> [0,1] is a belief function if:

$$
\text{Bel}(\emptyset) = 0
$$

$$
\text{Bel}(\Theta) = 1
$$

$$
\text{Bel}(A_1 \cup \cdots \cup A_n) \geq \sum_i \text{Bel}(A_i) - \sum_{i<j} \text{Bel}(A_i \cap A_j) + \cdots + (-1)^{n+1} \text{Bel}(A_1 \cap \cdots \cap A_n)
$$

Where: Theta is the frame of discernment (finite set of possibilities), A_i are subsets of Theta, Bel(A) is the degree of belief that the truth lies in A.
*(p.5)*

### Simple Support Function
A belief function is a *simple support function* with focus A and degree s if:

$$
\text{Bel}(B) = \begin{cases} 0 & \text{if } B \not\supseteq A \\ s & \text{if } B \supseteq A, B \neq \Theta \\ 1 & \text{if } B = \Theta \end{cases}
$$

Where: A is a non-empty proper subset of Theta, 0 <= s <= 1.
*(p.7)*

### Weight of Evidence
For a simple support function with degree s:

$$
s = 1 - e^{-w}
$$

$$
w = -\log(1 - s)
$$

Where: w is the weight of evidence, s is the degree of support. As w -> infinity, s -> 1 (certainty).
*(p.8)*

### Chance Density (for comparison)

$$
\sum_{x \in \mathcal{X}} q(x) = 1
$$

Where: q(x) is the chance of outcome x, X is the finite set of possible outcomes.
*(p.10, eq 1.1)*

### Chance Function

$$
\text{Ch}(U) = \sum_{x \in U} q(x)
$$

Where: Ch is the chance function derived from chance density q, U is a subset of X.
*(p.11, eq 1.2)*

### Product Chance Density (independent trials)

$$
q^n(x_1, \ldots, x_n) = q(x_1) \cdots q(x_n)
$$

*(p.12)*

### Conditional Chance Density

$$
q_U(x) = \begin{cases} \frac{q(x)}{\text{Ch}(U)} & \text{if } x \in U \\ 0 & \text{if } x \notin U \end{cases}
$$

*(p.14)*

### Rule of Conditioning for Chances

$$
\text{Ch}(V|U) = \frac{\text{Ch}(U \cap V)}{\text{Ch}(U)}
$$

*(p.15)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Frame of discernment | Theta | - | - | finite set | 5 | Set of mutually exclusive possibilities |
| Belief function | Bel | - | - | [0,1] | 5 | Maps subsets of Theta to degrees of belief |
| Degree of support | s | - | - | [0,1] | 7 | Strength of a simple support function |
| Weight of evidence | w | - | - | [0, inf) | 8 | Logarithmic transform of s |
| Chance density | q | - | - | [0,1] | 10 | Additive probability on individual outcomes |
| Chance function | Ch | - | - | [0,1] | 11 | Additive probability on subsets |

## Implementation Details
- Belief functions operate over finite sets (frames of discernment) throughout the book *(p.10)*
- Simple support functions are the atomic units; they focus all evidence on a single subset A *(p.7)*
- Combining two simple support functions on the same focus A yields another simple support function on A *(p.7)*
- Combining simple support functions with different foci yields a separable support function (not simple) *(p.7)*
- Dempster's rule = orthogonal sum: computes combined belief from independent evidence sources *(p.6)*
- Bayesian belief functions are the special case where belief is additive (Chapter 2 discusses this) *(p.4)*

## Figures of Interest
- **Example 1.1 (p.5-6):** The Ming Vase — illustrating how degrees of belief s1 (genuine) and s2 (counterfeit) satisfy s1+s2 <= 1, unlike probabilities where they must sum to 1
- **Example 1.2 (p.10):** Dime-Store Dice — chance density for biased dice, illustrating the difference between chance and belief
- **Example 1.3 (p.13):** Compound experiment with two dice throws
- **Example 1.4 (p.15):** Inverse Sampling — conditioning with coin tosses

## Results Summary
This is a foundational theoretical work, not an empirical study. The key result is the mathematical framework itself: belief functions satisfying superadditivity can represent states of partial ignorance that additive probabilities cannot. Dempster's rule provides a principled method for combining independent evidence. *(p.3-8)*

## Limitations
- Theory limited to **finite** sets of possibilities throughout (Shafer acknowledges this explicitly) *(p.10)*
- Does not address the computational complexity of belief function operations
- The "weight-of-conflict conjecture" for decomposing general support functions is stated but not proven *(p.8)*
- Preview only covers Chapter 1; the remaining 11 chapters (Chapters 2-12, pp.35-286) are not available

## Arguments Against Prior Work
- Rejects the Bayesian requirement that degrees of belief must be additive probabilities *(p.4-5)*
- Argues that the "rule of additivity" (Ch(A union B) = Ch(A) + Ch(B) for disjoint A,B) is appropriate for chances but NOT for degrees of belief *(p.11)*
- Criticizes the identification of "chance" with "degree of belief" that pervades both popular and scholarly thought *(p.9)*
- Notes that Bayesian theorists have historically tied the idea of partial belief to Bayesian theory, making it seem inseparable; Shafer's theory frees partial belief from this constraint *(p.4)*
- Argues that conditioning (Bayes' rule) figures most prominently in the theory of partial belief, not in the theory of chance per se *(p.15-16)*

## Design Rationale
- Superadditivity chosen over additivity to allow Bel(A) + Bel(not-A) < 1, representing genuine ignorance *(p.5-6)*
- Combination (Dempster's rule) chosen over conditioning as the fundamental operation, because combination pools independent evidence while conditioning updates within a single evidence framework *(p.3)*
- Simple support functions chosen as building blocks because they correspond to a single body of evidence pointing to a specific subset *(p.7)*
- Weight of evidence uses logarithmic transform so that combining two pieces of evidence on the same focus corresponds to adding their weights *(p.8)*

## Testable Properties
- For any belief function: Bel(A) + Bel(complement of A) <= 1 *(p.5-6)*
- A simple support function with degree s on focus A satisfies: Bel(B) = 0 for all B not containing A *(p.7)*
- Weight of evidence is non-negative and additive under combination of evidence on the same focus *(p.8)*
- The three axioms (Bel(empty)=0, Bel(Theta)=1, superadditivity) are strictly weaker than the axioms for probability *(p.5)*
- Bayesian belief functions (where additivity holds with equality) form a proper subset of all belief functions *(p.4)*

## Relevance to Project
This is the foundational text for Dempster-Shafer theory, which is directly relevant to propstore's uncertainty representation layer. The belief function framework provides a principled way to represent and combine uncertain evidence without forcing premature commitment to precise probabilities — aligning with propstore's core design principle of non-commitment. Key concepts for propstore:
- Belief functions for representing uncertain claim support
- Dempster's rule for combining evidence from multiple sources
- Weight of evidence as a quantitative measure
- Weight of conflict for detecting disagreement between evidence sources
- The distinction between "chance" and "degree of belief" maps to propstore's distinction between computed scores and epistemic states

## Open Questions
- [ ] How does Dempster's rule handle conflicting evidence? (Covered in Ch.3 section 4 "Weight of Conflict" and Ch.5 section 4 "Weight of Internal Conflict" — not in preview)
- [ ] What are the computational properties of belief functions on large frames? (Not addressed in preview)
- [ ] How do "compatible frames of discernment" (Ch.6) relate to propstore's concept hierarchies?
- [ ] What is the exact relationship between support functions and ATMS assumption sets?
- [ ] Need full book to extract the formal definition of Dempster's rule, plausibility functions, and the mass function (basic probability assignment)

## Related Work Worth Reading
- Dempster, A.P. (1967-1968) — Original work on upper and lower probabilities that Shafer extends
- Choquet, G. — Theory of capacities (mathematical foundation for belief functions)
- Iverson et al. (1971) in Psychometrika — Dime-store dice analysis referenced in Example 1.2

## Book Structure (from Table of Contents)
1. Introduction (pp.3-34)
2. Degrees of Belief (pp.35-56) — Subsets as propositions, belief functions, commonality numbers
3. Dempster's Rule of Combination (pp.57-73) — The core combination operation
4. Simple and Separable Support Functions (pp.74-87) — Building blocks of evidence
5. The Weights of Evidence (pp.88-113) — Logarithmic measure, internal conflict
6. Compatible Frames of Discernment (pp.114-140) — Refinement, coarsening, consistent belief
7. Support Functions (pp.141-171) — General class of belief functions obtainable from evidence
8. The Discernment of Evidence (pp.172-195) — Interaction of evidence, weight-of-conflict conjecture
9. Quasi Support Functions (pp.196-218) — Limits of support functions, Bayes' theorem
10. Consonance (pp.219-236) — Nested focal elements, possibility theory connection
11. Statistical Evidence (pp.237-273) — Application to statistical inference
12. The Dual Nature of Probable Reasoning (pp.274-286) — Role of assumptions, epistemic probability

---

**See also:** [The transferable belief model](../Smets_Kennes_1994_TransferableBeliefModel/notes.md) — Smets & Kennes' 1994 reinterpretation of DS theory: removes the underlying probability requirement, splits credal/pignistic levels, and gives the axiomatic uniqueness theorem for the pignistic transformation.

**See also:** [Subjective Logic: A Formalism for Reasoning Under Uncertainty](../Josang_2016_SubjectiveLogic/notes.md) — Jøsang 2016 cites this book as reference [90] and reinterprets Dempster's rule as belief constraint fusion (BCF), arguing it is appropriate for preference combination but not for cumulative evidence combination. Subjective logic adds a base-rate distribution that DST lacks, and bijects to Beta/Dirichlet PDFs (DST↔SL mapping in book Eq. 5.1: `m(x) = b_X(x), m(X) = u_X`).

---

**See also (citation):** [Quantifying Beliefs by Belief Functions: An Axiomatic Justification](../Smets_1993_QuantifyingBeliefsBeliefFunctions/notes.md) - Smets cites Shafer (1976) as the source of belief functions and provides an axiomatic justification: from axioms A1, R1, R2, M1, M2, M3, and a closure axiom, the credibility function on a finite Boolean algebra must be a Shafer belief function. The 1993 paper closes the gap between Shafer's mathematical theory and the *agent-relative* credal interpretation used in TBM.

**See also (recontextualization):** [The Nature of the Unnormalized Beliefs Encountered in the Transferable Belief Model](../Smets_1992_NatureUnnormalizedBeliefsEncountered/notes.md) - Smets 1992 explicitly rejects the normalization step (`m(A) := m(A)/(1-K)`) that Shafer 1976 imposes, arguing it discards conflict information and is incompatible with refinement of the frame. Smets reinterprets m(empty) > 0 as either inter-source conflict or open-world residual mass, rather than as something to be eliminated.
