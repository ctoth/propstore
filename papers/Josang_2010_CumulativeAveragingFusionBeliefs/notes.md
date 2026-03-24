---
title: "Multiplication of Multinomial Subjective Opinions"
authors: "Audun Josang, Stephen O'Hara"
year: 2010
venue: "13th International Conference on Information Processing and Management of Uncertainty (IPMU2010), Dortmund, July 2010"
note: "WARNING — Directory name says CumulativeAveragingFusionBeliefs but this PDF is actually the Multiplication paper. The cumulative/averaging fusion paper is a different Josang 2010 publication."
---

# Multiplication of Multinomial Subjective Opinions

## One-Sentence Summary
Defines how to compute the multiplicative product of two multinomial subjective opinions on different frames, producing a joint opinion on the Cartesian product frame — with two methods for reassigning belief mass from overlapping subsets to singletons.

## Problem Addressed
The multiplicative product of two multinomial opinions produces belief mass terms on overlapping subsets of the Cartesian product frame, which violates the multinomial opinion requirement that belief mass only reside on singletons and the whole frame. A method is needed to reassign this excess belief mass consistently. *(p.1)*

## Key Contributions
- Formal definition of multinomial subjective opinions (belief vector, uncertainty mass, base rate vector) *(p.3-4)*
- Cartesian product construction for combining opinions on independent frames *(p.6)*
- Two methods for determining uncertainty mass in the product opinion: "Assumed Belief Mass" and "Assumed Uncertainty" *(p.7-8)*
- Demonstration that the product operator is commutative and associative *(p.8)*
- Worked example with genetic engineering egg classification *(p.8-9)*

## Methodology
Given two multinomial opinions on frames X and Y, compute the raw Dempster-Shafer multiplicative product on the Cartesian product frame X x Y. The raw product generates four groups of belief mass terms: singletons, rows, columns, and the whole frame. The row/column terms are "overlapping subsets" that must be redistributed. Two methods are proposed for this redistribution. *(p.6-7)*

## Key Equations

### Definition 1: Belief Mass Vector
$$
\vec{b}(\emptyset) = 0 \quad \text{and} \quad \sum_{x \in X} \vec{b}(x) \leq 1
$$
Where: $\vec{b}$ is the belief mass vector, a function from singletons of frame $X$ to $[0,1]^k$. $\vec{b}(x_i)$ is the amount of positive belief that $x_i$ is true.
*(p.3)*

### Definition 2: Uncertainty Mass
$$
u + \sum_{x \in X} \vec{b}(x) = 1
$$
Where: $u \in [0,1]$ is the uncertainty mass representing uncommitted belief.
*(p.3)*

### Definition 3: Base Rate Vector
$$
\vec{a}(\emptyset) = 0 \quad \text{and} \quad \sum_{x \in X} \vec{a}(x) = 1
$$
Where: $\vec{a}$ is the base rate vector from singletons of $X$ to $[0,1]^k$, representing non-informative a priori probability.
*(p.3)*

### Definition 4: Subjective Opinion (Multinomial)
A multinomial opinion over frame $X = \{x_i | i = 1, \ldots k\}$ is the composite function $\omega_X = (\vec{b}, u, \vec{a})$ where $\vec{b}$ is the belief vector, $u$ is the uncertainty mass, and $\vec{a}$ is the base rate vector. *(p.4)*

The frame has $k$ singletons, the belief vector has $k$ parameters, plus 1 uncertainty parameter, for a total of $3k - 1$ degrees of freedom (since base rate sums to 1). A multinomial opinion over a frame of cardinality $k$ will only have $2k - 1$ degrees of freedom. *(p.4)*

### Definition 5: Probability Expectation Vector
$$
\mathbf{E}_X(x_i) = \vec{b}(x_i) + \vec{a}(x_i) u
$$
Where: $\mathbf{E}_X$ maps from singletons of $X$ to $[0,1]^k$.
*(p.4)*

Satisfies additivity:
$$
\mathbf{E}_X(\emptyset) = 0 \quad \text{and} \quad \sum_{x \in X} \mathbf{E}_X(x_i) = 1
$$
*(p.4)*

### Raw Product Terms (4 groups)

**Group 1 — Singleton belief masses on $X \times Y$:**
$$
b^{\text{I}}_{X \times Y}(x_i, y_j) = b_X(x_i) b_Y(y_j)
$$
*(p.6)*

**Group 2 — Row belief masses (overlapping subsets):**
$$
b^{\text{Rows}}_{X \times Y} = (u_X b_Y(y_1), \quad u_X b_Y(y_2), \quad \ldots \quad u_X b_Y(y_l))
$$
*(p.6)*

**Group 3 — Column belief masses (overlapping subsets):**
$$
b^{\text{Columns}}_{X \times Y} = (b_X(x_1) u_Y, \quad b_X(x_2) u_Y, \quad \ldots \quad b_X(x_k) u_Y)
$$
*(p.6)*

**Group 4 — Frame uncertainty:**
$$
u^{\text{Frame}}_{X \times Y} = u_X u_Y
$$
*(p.6)*

### Method 1: Assumed Belief Mass
The simplest method: assign the belief mass terms from Eqs.(10) and (11) to singletons. Only the uncertainty mass from Eq.(12) (i.e., $u_X u_Y$) is considered as uncertainty in the product opinion:
$$
u_{X \times Y} = u_X u_Y
$$
*(p.7)*

Problem: this approach produces less uncertainty than intuition would dictate. *(p.7)*

### Method 2: Assumed Uncertainty (Recommended)
Treats row masses (Eq.10) and column masses (Eq.11) as potential uncertainty mass, combined with the frame uncertainty from Eq.(12) to produce an **intermediate uncertainty mass**:
$$
u^*_{X \times Y} = u_X u_Y + u_X \sum_{j} b_Y(y_j) + u_Y \sum_{i} b_X(x_i)
$$
Which simplifies to:
$$
u^*_{X \times Y} = u_X + u_Y - u_X u_Y
$$
*(p.7)*

The probability expectation values:
$$
\mathbf{E}(x_i, y_j) = \mathbf{E}_X(x_i) \mathbf{E}_Y(y_j)
$$
*(p.7)*

The product expectation should also satisfy:
$$
\mathbf{E}(x_i, y_j) = b_{X \times Y}(x_i, y_j) + a_{X \times Y}(x_i, y_j) u_{X \times Y}
$$
*(p.7)*

To find the correct uncertainty mass, for each state $(x_i, y_j) \in X \times Y$, find the smallest uncertainty mass satisfying both constraints:
$$
\frac{b_{X \times Y}(x_i, y_j)}{b^*_{X \times Y}(x_i, y_j)} = \frac{\mathbf{E}_{X \times Y}(x_i, y_j)}{a_{X \times Y}(x_i, y_j)}
$$
*(p.7)*

Uncertainty mass:
$$
u_{X \times Y}(x_i, y_j) = \frac{u^*_{X \times Y} \mathbf{E}(x_i, y_j)}{a_{X \times Y}(x_i, y_j)}
$$
*(p.8)*

Product uncertainty is the smallest of these per-state values:
$$
u_{X \times Y} = \min_{(x_i, y_j) \in X \times Y} u_{X \times Y}(x_i, y_j)
$$
*(p.8)*

### Belief mass computation
$$
b_{X \times Y}(x_i, y_j) = \mathbf{E}(x_i, y_j) - a_{X \times Y}(x_i, y_j) u_{X \times Y}
$$
*(p.8)*

### Additivity verification
$$
u_{X \times Y} + \sum_{(x_i, y_j) \in X \times Y} b_{X \times Y}(x_i, y_j) = 1
$$
*(p.8)*

The product operator is **commutative** and **associative**. *(p.8)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Belief mass (singleton) | $\vec{b}(x_i)$ | - | - | [0,1] | 3 | Positive belief in state $x_i$ |
| Uncertainty mass | $u$ | - | - | [0,1] | 3 | Uncommitted belief; $u + \sum b(x_i) = 1$ |
| Base rate | $\vec{a}(x_i)$ | - | $1/k$ | [0,1] | 3 | A priori probability; $\sum a(x_i) = 1$ |
| Frame cardinality | $k$ | - | - | $\geq 2$ | 4 | Number of singletons in frame |
| Degrees of freedom | $2k-1$ | - | - | $\geq 3$ | 4 | For multinomial opinion on cardinality-$k$ frame |

## Implementation Details
- A multinomial opinion is the triple $\omega_X = (\vec{b}, u, \vec{a})$ where $\vec{b}$ is a $k$-vector, $u$ is a scalar, and $\vec{a}$ is a $k$-vector summing to 1. *(p.4)*
- The constraint $u + \sum b(x_i) = 1$ must always hold. *(p.3)*
- Base rate vector defaults to uniform $a(x_i) = 1/k$ for a frame of cardinality $k$, but arbitrary base rates are allowed as long as they sum to 1. *(p.4)*
- Two different observers can assign different base rates to the same frame. *(p.4-5)*
- Opinions can be derived from Beta/Dirichlet distributions if base rates can be assumed. Specifically, subjective logic is equivalent to the Beta/Dirichlet framework. *(p.10)*
- The "Assumed Uncertainty" method (Method 2) is recommended because it preserves more uncertainty and is therefore safer. *(p.9)*
- Row and column terms from the raw product must be redistributed — this is the core implementation challenge. *(p.7)*
- The product frame base rate: $a_{X \times Y}(x_i, y_j) = a_X(x_i) \cdot a_Y(y_j)$ (implied by independence). *(p.7)*

## Figures of Interest
- **Fig 1 (p.5):** Opinion tetrahedron — visualizes a trinomial opinion (3-state frame) as a point inside a tetrahedron. Vertical elevation = uncertainty mass, barycentric coordinates on base plane = belief masses, projection onto base via director line = probability expectation point. Only works for $k \leq 3$.
- **Fig 2 (p.9):** Multiplication of opinions on orthogonal aspects of GE eggs — Sensor A observes gender, Sensor B observes mutation, multiplication produces joint opinion.

## Results Summary
Worked example: GE eggs with Gender frame $X = \{M, F\}$ and Mutation frame $Y = \{S, T\}$. *(p.8-9)*
- Method 1 (Assumed Belief Mass): $u_{X \times Y} = 0.02$, much less uncertainty preserved *(p.9)*
- Method 2 (Assumed Uncertainty): $u_{X \times Y} = 0.09$, preserves more uncertainty *(p.9)*
- Significant difference between methods; Method 2 is recommended. *(p.9)*

## Limitations
- Visualization only works for trinomial opinions ($k = 3$) via tetrahedron; higher cardinality opinions cannot be visualized traditionally. *(p.5-6)*
- This paper covers only multiplication (combining opinions on DIFFERENT frames). Fusion (combining opinions on the SAME frame from different sources) is covered in other papers. *(p.10)*
- The paper does not discuss computational complexity for large frames. *(observed)*

## Arguments Against Prior Work
- Standard Dempster-Shafer multiplication produces belief mass on overlapping subsets, which violates the multinomial opinion constraint. This paper provides the fix. *(p.1)*
- The "Assumed Belief Mass" method (Method 1) is criticized for producing too little uncertainty — it is overconfident. *(p.7)*

## Design Rationale
- Multinomial opinions restrict belief mass to singletons and the whole frame (unlike general belief functions which allow any subset). This restriction enables the opinion representation as a simple triple $(\vec{b}, u, \vec{a})$ rather than requiring $2^k$ mass values. *(p.1-2)*
- The "Assumed Uncertainty" method is preferred because it preserves more uncertainty, following the principle that less information should produce more uncertainty. *(p.9)*
- The product operator is designed to be commutative and associative, enabling chaining. *(p.8)*

## Testable Properties
- $u + \sum_{x \in X} b(x) = 1$ for any valid multinomial opinion *(p.3)*
- $\sum_{x \in X} a(x) = 1$ for base rate vector *(p.3)*
- $\mathbf{E}(x_i) = b(x_i) + a(x_i) u$ and $\sum \mathbf{E}(x_i) = 1$ *(p.4)*
- Product expectation: $\mathbf{E}(x_i, y_j) = \mathbf{E}_X(x_i) \cdot \mathbf{E}_Y(y_j)$ *(p.7)*
- Product additivity: $u_{X \times Y} + \sum b_{X \times Y}(x_i, y_j) = 1$ *(p.8)*
- Method 2 uncertainty: $u_{X \times Y} \geq u_X u_Y$ (always preserves at least as much uncertainty as Method 1) *(p.7-9)*
- Commutativity: $\omega_X \cdot \omega_Y = \omega_Y \cdot \omega_X$ *(p.8)*
- Associativity: $(\omega_X \cdot \omega_Y) \cdot \omega_Z = \omega_X \cdot (\omega_Y \cdot \omega_Z)$ *(p.8)*
- Worked example verification: Gender opinion $\omega_X^A = (0.8, 0, 0.1)$, Mutation opinion $\omega_Y^B = (0.7, 0.1, 0.1)$ yield Method 2 product $u = 0.09$ *(p.8-9)*

## Relevance to Project
This paper defines multinomial subjective opinions — the extension from binary (2-state) to K-state opinions. For propstore's 7-stance classification system, this provides the formal representation: each stance assessment is a multinomial opinion over 7 outcomes. However, this specific paper covers opinion **multiplication** (combining opinions on different/orthogonal frames), NOT fusion (combining opinions on the same frame from different sources). For fusion operators (cumulative and averaging), a different Josang paper is needed.

**Critical for propstore:**
- The multinomial opinion representation $(\vec{b}, u, \vec{a})$ is exactly what's needed for K-ary stance classification
- The probability expectation formula $\mathbf{E}(x_i) = b(x_i) + a(x_i) u$ gives the "projected probability" for rendering
- The base rate vector allows different priors per observer — important for multi-source stance assessment
- Multiplication may be useful for combining orthogonal stance dimensions

**What this paper does NOT provide:**
- Cumulative fusion (combining same-frame opinions, evidence accumulation)
- Averaging fusion (combining same-frame opinions, opinion pooling)
- The Dirichlet distribution mapping for K-ary case (mentioned briefly on p.10 but not developed)

## Open Questions
- [ ] Locate the actual "Cumulative and Averaging Fusion of Beliefs" paper — it may be a different Josang 2010 publication
- [ ] The Dirichlet connection: this paper mentions it (p.10) but the details are in Josang's other work (ref [1], [2])
- [ ] How does the base rate vector interact with propstore's prior stance distributions?
- [ ] For 7-stance classification, the product frame would be very large ($7^n$ for $n$ orthogonal dimensions) — is this practical?

## Related Work Worth Reading
- [1] A. Josang, "A Logic for Uncertain Probabilities," International Journal of Uncertainty, Fuzziness and Knowledge-Based Systems, 9(3):279-311, June 2001. — Original binary opinion framework
- [2] A. Josang, "Conditional Reasoning with Subjective Logic," Journal of Multiple-Valued Logic and Soft Computing, 2008. — Conditional operations
- [3] A. Josang and D. McAnally, "Multiplication and Comultiplication of Beliefs," International Journal of Approximate Reasoning, 38(1):19-51, 2004. — Earlier multiplication work
- [4] A. Josang, S. O'Hara, and K. O'Grady, "Base Rates for Belief Functions," Proceedings of the Workshop on the Theory of Belief Functions/WBF 2010, Brest, April 2010. — Base rate theory
- [5] G. Shafer, "A Mathematical Theory of Evidence," Princeton University Press, 1976. — Foundation
- [6] M. Smithson, "Ignorance and Uncertainty: Emerging Paradigms," Springer, 1984.

## Collection Cross-References

### Already in Collection
- [[Josang_2001_LogicUncertainProbabilities]] — cited as ref [1], the foundational binary opinion paper. This 2010 paper extends the binary opinion $(b, d, u, a)$ to multinomial $(\vec{b}, u, \vec{a})$ with $k$ singletons. The 2001 paper provides the Beta distribution mapping; this paper mentions but does not develop the Dirichlet generalization.

### New Leads (Not Yet in Collection)
- Josang (2008) — "Conditional Reasoning with Subjective Logic" — conditional operations on opinions, needed for dependent reasoning chains
- Josang & McAnally (2004) — "Multiplication and Comultiplication of Beliefs" — earlier multiplication work for general (non-multinomial) beliefs
- Josang, O'Hara & O'Grady (2010) — "Base Rates for Belief Functions" — base rate theory directly relevant to prior stance distributions

### Supersedes or Recontextualizes
- Extends [[Josang_2001_LogicUncertainProbabilities]] from binary to multinomial opinions. The 2001 paper's binary opinion $(b, d, u, a)$ is the $k=2$ special case of the multinomial $(\vec{b}, u, \vec{a})$.

### Cited By (in Collection)
- (none found — this paper is not directly cited by other collection papers, though Sensoy 2018 and Denoeux 2018 cite the broader Josang subjective logic framework)

### Conceptual Links (not citation-based)
**Subjective logic and uncertainty quantification:**
- [[Sensoy_2018_EvidentialDeepLearningQuantifyClassification]] — **Strong.** Sensoy's EDL maps neural network evidence to Dirichlet distributions, which are the statistical counterpart of this paper's multinomial opinions. The $\alpha_k = e_k + 1$ mapping in Sensoy corresponds to the belief-to-Dirichlet bridge mentioned on p.10 of this paper. For propstore, EDL could produce the evidence that parameterizes multinomial opinions for stance classification.
- [[Denoeux_2018_Decision-MakingBeliefFunctionsReview]] — **Moderate.** Denoeux reviews decision criteria under Dempster-Shafer belief functions. The multinomial opinions defined here are a restricted subclass of belief functions (mass only on singletons and frame). Denoeux's pignistic transformation and E-admissibility criteria apply at render time to the probability expectation values computed from multinomial opinions.

**Argumentation and evidence combination:**
- [[Falkenhainer_1987_BeliefMaintenanceSystem]] — **Moderate.** The BMS propagates Dempster-Shafer belief masses through dependency networks. This paper's multinomial opinions are a constrained form of DS masses; the BMS's propagation mechanisms could be adapted for multinomial opinion networks.
