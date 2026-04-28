---
title: "An Axiomatic Framework for Bayesian and Belief-function Propagation"
authors: "Prakash P. Shenoy, Glenn Shafer"
year: 1990
venue: "Conference on Uncertainty in Artificial Intelligence (UAI)"
doi_url: "https://doi.org/10.1007/978-3-540-44792-4_20"
produced_by:
  agent: "Claude Opus 4.6 (1M context)"
  skill: "paper-reader"
  timestamp: "2026-03-28T22:24:22Z"
---
# An Axiomatic Framework for Bayesian and Belief-function Propagation

## One-Sentence Summary
Establishes three axioms (commutativity/associativity of combination, commutativity/associativity of marginalization, and distributivity of marginalization over combination) for valuation-based systems that are necessary and sufficient for exact local computation of marginals via message-passing on hypertrees.

## Problem Addressed
Computing marginals of joint probability distributions or joint belief functions is computationally intractable for large numbers of variables when done globally. The paper provides a general axiomatic framework under which factorizations on hypertrees enable exact local computation — avoiding the need for global computation. *(p.1)*

## Key Contributions
- Defines an abstract framework of **valuations** with two primitive operators: **combination** and **marginalization** *(p.3)*
- States three axioms sufficient for local computation *(p.3)*
- Derives the possibility of local computation from these axioms via a **factorization** property *(p.3)*
- Describes a **propagation scheme** for computing marginals on hypertrees (Markov trees) using message passing *(p.4)*
- Shows probability propagation (via potentials) fits the framework *(p.5)*
- Shows belief-function propagation (via Dempster's rule of combination) fits the framework *(p.6-7)*

## Methodology
The paper defines an abstract algebraic framework called a **valuation-based system (VBS)**, then proves that three axioms on its operators guarantee exact local computation. It instantiates the framework for two concrete domains: probability distributions and belief functions (Dempster-Shafer theory). The propagation scheme is a message-passing algorithm on junction trees (Markov trees).

## Key Equations / Statistical Models

### Valuations and Operators

**Combination.** Given valuations G on variable set g and H on variable set h, their combination is a valuation on g ∪ h: *(p.3)*

$$
G \otimes H \quad \text{is a valuation on } g \cup h
$$

**Marginalization.** Given a valuation A on variable set a, the marginal of A for a subset t ⊆ a is: *(p.3)*

$$
A^{\downarrow t} \quad \text{is a valuation on } t
$$

Where: ↓t denotes marginalization to the variable set t.

### Three Axioms

**Axiom A1 (Identity):** Suppose G is a valuation on g. Then G↓g = G. *(p.3)*

**Axiom A1' (Consonance of marginalization):** Suppose G is a valuation on g and suppose s ⊆ g. Then G↓s = (G↓s)↓s. *(p.3)*
More generally: if t ⊆ s ⊆ g, then (G↓s)↓t = G↓t.

**Axiom A2 (Commutativity and associativity of combination):** Suppose G, H, K are valuations on g, h, k respectively. Then: *(p.3)*

$$
G \otimes H = H \otimes G \quad \text{and} \quad (G \otimes H) \otimes K = G \otimes (H \otimes K)
$$

**Axiom A3 (Distributivity of marginalization over combination):** Suppose G is a valuation on g and H is a valuation on h. Then: *(p.3)*

$$
(G \otimes H)^{\downarrow h} = G^{\downarrow(g \cap h)} \otimes H
$$

One implication of Axiom A3 is that when we have multiple combinations of valuations, we can re-order without using parentheses. E.g., (A₁ ⊗ (A₂ ⊗ (A₃ ⊗ ... ⊗ Aₙ))) can be written A₁ ⊗ A₂ ⊗ ... ⊗ Aₙ without indicating the order. *(p.3)*

### Factorization Proposition

**Proposition 3.1:** Suppose A is a valuation on Σ. Suppose A factorizes on a hypergraph S, i.e., A = ⊗{Aₛ | s ∈ S}, and suppose t is a twig in S with branch b. Let S' denote S \ {t} and let Σ' denote ∪S' = Σ \ (t \ b). Then the marginal of A to Σ' factorizes as: *(p.3)*

$$
A^{\downarrow \Sigma'} = \bigotimes\{A_s | s \in S' \setminus \{b\}\} \otimes (A_b \otimes A_t^{\downarrow b})
$$

Where: the marginal A↓Σ' can be computed locally — only Aₜ needs to be marginalized down to the twig-branch intersection b, then combined with Aᵦ. *(p.3-4)*

### Propagation Messages on Markov Trees

**Rule 1:** If μ ∈ Tₕ and M^{h→μ} is in working memory for all h in T_μ \ {t}, then compute M^{μ→t} as follows: *(p.4)*

$$
M^{\mu \to t} = (A_\mu \otimes (\bigotimes\{M^{h \to \mu} \mid h \in T_\mu \setminus \{t\}\}))^{\downarrow (\mu \cap t)}
$$

and place it in working memory.

**Rule 2:** If M^{h→μ} is in working memory for all h in T_μ \ {t}, then compute A_μ* as: *(p.4)*

$$
A_\mu^* = A_\mu \otimes (\bigotimes\{M^{h \to \mu} \mid h \in T_\mu\})
$$

and print the result.

Where: M^{μ→t} is the message from vertex μ to neighbor t; T_μ is the set of neighbors of μ; A_μ* is the marginal of the full joint onto μ. *(p.4)*

### Probability Propagation (Section 4)

**Potentials.** For variable set s with finite frame Ω_s (Cartesian product of individual variable frames), a potential on s is φ: Ω_s → [0,∞). The potential is a real-valued non-negative function. Potentials are unnormalized probability distributions. *(p.5)*

**Marginalization of potentials.** If g and h are sets of variables, h ⊆ g, and G is a potential on g, the marginal G↓h is defined by: *(p.5)*

$$
G^{\downarrow h}(x) = \sum_{y} G(x, y)
$$

Where: x is a configuration of h, y ranges over all configurations of g \ h, and G(x,y) denotes G evaluated at the joint configuration.

**Combination for potentials** is simply pointwise multiplication: *(p.5)*

$$
(G \otimes H)(x) = G(x^{\downarrow g}) \cdot H(x^{\downarrow h})
$$

Where: x is a configuration of g ∪ h, and x↓g, x↓h are its projections. *(p.5)*

The paper notes: all three axioms are satisfied, making local computation of marginal potentials possible. It is shown in Shenoy and Shafer [1988] that the marginalization and combination operations for potentials satisfy axioms A1-A3. *(p.5)*

### Belief-Function Propagation (Section 5)

**Random non-empty subsets.** Suppose Ω_X is the frame for a set of variables h. A random subset A of Ω_X is defined by giving a probability measure on the set of all subsets of Ω_X. *(p.6)*

$$
\text{Pr}(A = \emptyset) = 0
$$

The non-empty condition ensures vacuous belief functions are well-defined.

**Belief function.** A function Bel that assigns a degree of belief Bel(A) to every subset A of Ω_X is a belief function if and only if it exists a random non-empty subset A of Ω_X such that: *(p.6)*

$$
\text{Bel}(A) = \text{Pr}(A \subseteq A)
$$

for every subset A of Ω_X. Intuitively, the number Bel(A) is the degree to which a body gives evidence to support the proposition that the true value of variables h is in A. *(p.6)*

**Marginalization for belief functions.** If g and h are sets of variables, h ⊆ g, and G is a non-empty subset of Ω_g, then the marginal of G to h, denoted G↓h, is a subset of Ω_h given by: *(p.6)*

$$
G^{\downarrow h} = \{x^{\downarrow h} \mid x \in G\}
$$

This is the projection of the random set to a smaller frame. The marginal of Bel on Ω_g to Ω_h consists of the elements of Ω_h which can be obtained by marginalizing elements of A to Ω_{X(h)}. *(p.6)*

**Combination for belief functions — Dempster's rule.** For two random non-empty subsets A₁ on h₁ and A₂ on h₂ that are probabilistically independent: *(p.7)*

$$
\Pr(A_1 \cap A_2 = a) = \frac{\Pr(A_1^{\uparrow h_1 \cup h_2} \cap A_2^{\uparrow h_1 \cup h_2} = a)}{1 - \Pr(A_1^{\uparrow h_1 \cup h_2} \cap A_2^{\uparrow h_1 \cup h_2} = \emptyset)}
$$

for every non-empty subset a of Ω_{h₁∪h₂}, and Bel₁⊕Bel₂ (the combination of Bel₁ and Bel₂) is the belief function for A₁ corresponding to A₁ ∩ A₂. *(p.7)*

The bodies of evidence on which Bel₁ and Bel₂ are based are independent, then Bel₁⊕Bel₂ is supposed to represent the result of pooling these two bodies of evidence. *(p.7)*

It is shown in Shafer [1976] that Dempster's rule of combination is commutative and associative. In Shenoy and Shafer [1988], it is shown that the above definitions of marginalization and combination for belief functions satisfy axioms A1-A3. Thus all axioms are satisfied making local computation possible. *(p.7)*

**Vacuous extension.** Before combining belief functions on different frames, we need the concept of vacuous extension of subsets. For example, if A is a subset of Ω_{X,Y}, then the vacuous extension of A to Ω_{X,Y,Z} includes all elements of Ω_Z. *(p.6-7)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Variable set | Σ | — | — | finite | 3 | Set of all variables in the system |
| Frame | Ω_X | — | — | finite | 5 | Set of possible values of variable X |
| Valuation | V_g | — | — | — | 3 | Set of all valuations for variable set g |
| Potential | φ | — | ≥0 | [0,∞) | 5 | Real-valued non-negative function on Ω_s |

## Methods & Implementation Details
- The framework is abstract: it works for any system satisfying the three axioms, not just probability and belief functions *(p.1)*
- Hypertrees and hypergraphs are the structural backbone. A hypergraph is a collection of non-empty subsets (hyperedges) of a finite set of vertices *(p.2)*
- A **twig** in a hypergraph is a hyperedge t such that there exists another hyperedge b (called a **branch**) where all vertices shared between t and other hyperedges are contained in b: for every h ≠ t, t ∩ h ⊆ b *(p.2)*
- A **hypertree** is a hypergraph that can be reduced to the empty hypergraph by repeatedly deleting twigs *(p.2)*
- **Markov tree**: a tree where vertices are elements of a hypergraph, and every vertex of the hypergraph that is contained in two vertices of the tree is also contained in every vertex on the path between them *(p.2)*
- The propagation scheme starts with a Markov tree representation of the hypertree. Each vertex μ has an initial valuation A_μ. Messages flow inward first (Rule 1, computing messages for leaves first, working inward), then outward (Rule 2, computing marginals). *(p.4)*
- The propagation scheme resembles a forward-chaining production system: working memory + rules *(p.4)*
- Each processor sends messages to all neighbors; a processor sends to a neighbor only after receiving from all other neighbors *(p.4)*
- The term "Markov tree" is borrowed from probability theory, where it means a tree of variables in which separation implies probabilistic conditional independence *(p.2)*

## Figures of Interest
- No numbered figures in this paper.

## Results Summary
The three axioms (A1, A2, A3) are necessary and sufficient for local computation via message passing on hypertrees. Both probability propagation (using potentials with pointwise multiplication and summation) and belief-function propagation (using Dempster's rule of combination and set projection) satisfy all three axioms. The propagation scheme computes exact marginals for all vertices of the Markov tree simultaneously using only local operations. *(p.3-7)*

## Limitations
- The framework assumes finite variable frames (finite sets of possible values) *(p.5)*
- The paper does not address approximate computation for cases where exact computation is infeasible *(p.1)*
- The paper focuses on singly-connected (tree) structures; multiply-connected networks require transformation to hypertrees first *(p.2)*
- Dempster's rule requires probabilistic independence of bodies of evidence *(p.7)*

## Arguments Against Prior Work
- Prior treatments of local computation for probabilities (Lauritzen & Spiegelhalter 1988, Pearl 1986) were specific to probability; this paper provides a general framework covering both probability and belief functions *(p.1)*
- Many authors who described schemes for probability propagation on trees "have justified their schemes by emphasizing conditional probability" — the paper argues this emphasis is misplaced; what is essential is the factorization, not conditional probability per se *(p.5)*
- The paper argues its framework is more general than graph-theoretic treatments that require specific independence semantics *(p.1)*

## Design Rationale
- The abstract framework is chosen to unify probability and belief-function propagation under common axioms, rather than treating them as separate algorithmic traditions *(p.1)*
- Hypertrees rather than simple trees are used because they naturally represent factorizations where factors involve overlapping variable sets *(p.2)*
- The three axioms are chosen to be minimal: each is independently necessary for the factorization property that enables local computation *(p.3)*
- The Markov tree representation is preferred because it makes the message-passing algorithm natural and efficient *(p.4)*

## Testable Properties
- Combination must be commutative and associative (Axiom A2) *(p.3)*
- Marginalization must be consonant: (G↓s)↓t = G↓t for t ⊆ s ⊆ g (Axiom A1) *(p.3)*
- Distributivity: (G ⊗ H)↓h = G↓(g∩h) ⊗ H must hold (Axiom A3) *(p.3)*
- For potentials: marginalization is summation, combination is pointwise multiplication — these must satisfy A1-A3 *(p.5)*
- For belief functions: marginalization is set projection, combination is Dempster's rule — these must satisfy A1-A3 *(p.6-7)*
- The propagation scheme must compute exact marginals: A_μ* = (⊗{Aₛ | s ∈ S})↓μ for each vertex μ *(p.4)*
- Message passing terminates in 2|S|-2 steps for a Markov tree with |S| vertices *(p.4)*

## Relevance to Project
This paper is foundational for understanding valuation-based systems, which generalize both Bayesian networks and Dempster-Shafer belief function networks. The three axioms provide the theoretical justification for any local computation scheme on join trees / junction trees. For propstore:
- The combination operator maps to opinion fusion (Jøsang's consensus fusion is a special case)
- The marginalization operator maps to projection of beliefs onto subsets of variables
- The factorization/hypertree structure maps to the decomposition used in probabilistic argumentation (component decomposition in praf.py)
- The framework validates that Dempster-Shafer operations satisfy the requirements for local computation, which is relevant since propstore uses subjective logic (an extension of Dempster-Shafer theory)

## Open Questions
- [ ] Does Jøsang's subjective logic consensus fusion satisfy the three Shenoy-Shafer axioms? If so, local computation on hypertrees would apply to opinion fusion.
- [ ] How does this framework relate to the ATMS label propagation already implemented?
- [ ] Could the propagation scheme improve performance of the probabilistic argumentation framework (praf.py)?

## Collection Cross-References

### Already in Collection
- [[Shafer_1976_MathematicalTheoryEvidence]] — cited as the foundational text for Dempster-Shafer belief functions; Section 5 builds directly on Shafer's theory of evidence
- [[Denoeux_2018_Decision-MakingBeliefFunctionsReview]] — cites "Denoeux and Shenoy 2018" (axiomatic utility theory for DS theory); reviews decision criteria under the belief function framework that this paper's propagation scheme computes

### New Leads (Not Yet in Collection)
- Shafer & Shenoy (1988) — "Local computation in hypertrees" — companion technical report with full proofs for the axioms
- Lauritzen & Spiegelhalter (1988) — "Local computations with probabilities on graphical structures" — the probability-specific framework this paper generalizes
- Pearl (1986) — "Fusion, propagation and structuring in belief networks" — message passing for Bayesian networks
- Kong (1986) — "Multivariate belief functions and graphical models" — extends belief functions to graphical model settings

### Conceptual Links (not citation-based)
- [[Josang_2001_LogicUncertainProbabilities]] — **Strong.** Subjective logic's opinion algebra extends Dempster-Shafer theory. The question of whether Jøsang's consensus fusion satisfies the three Shenoy-Shafer axioms (A1-A3) determines whether local computation on hypertrees applies to opinion fusion networks.
- [[Falkenhainer_1987_BeliefMaintenanceSystem]] — **Moderate.** The BMS uses Dempster-Shafer intervals for belief propagation in a TMS-like network. Shenoy-Shafer axioms characterize when such propagation can be done locally on tree structures.
- [[Sensoy_2018_EvidentialDeepLearningQuantifyClassification]] — **Moderate.** Sensoy maps neural network evidence to Dirichlet/subjective logic opinions. The Shenoy-Shafer framework governs whether those opinions can be propagated efficiently through structured networks.
- [Belief Functions: The Disjunctive Rule of Combination and the Generalized Bayesian Theorem](../Smets_1993_BeliefFunctionsDisjunctiveRule/notes.md) — **Strong.** Same propagation goal, two operator algebras. Shenoy-Shafer axiomatize valuation-based propagation (combination + marginalization) on hypertrees with joint storage `2^{|X|*|Theta|}`; Smets 1993 presents an alternative directed-network propagation specifically for belief functions whose per-edge storage is `|Theta| * 2^|X|` — strictly less. The two operator algebras (valuation network vs conditional-belief edges + DRC/GBT) compute the same posteriors on directed BF graphs.

### Cited By (in Collection)
- [[Denoeux_2018_Decision-MakingBeliefFunctionsReview]] — references Denoeux & Shenoy 2018 work on axiomatic utility theory extending this framework to decision-making

## Related Work Worth Reading
- Shafer (1976) — A Mathematical Theory of Evidence (foundational for belief functions)
- Shenoy & Shafer (1988) — Local computation in hypertrees (the companion technical report with full proofs)
- Lauritzen & Spiegelhalter (1988) — Local computations with probabilities on graphical structures
- Pearl (1986, 1988) — Fusion, propagation and structuring in belief networks
- Kong (1986) — Multivariate belief functions and graphical models
- Dempster (1967) — Upper and lower probabilities induced by a multivalued mapping

---

**See also (conceptual link):** [The transferable belief model](../Smets_Kennes_1994_TransferableBeliefModel/notes.md) — Smets & Kennes' TBM defers axiomatic justification of Dempster's rule of *combination* to Shafer–Shenoy-style propagation frameworks (refs [14, 19, 20, 27, 40]). Shenoy's axioms apply directly to TBM's credal level once the combination operator is fixed.

---

**See also (conceptual link):** [Quantifying Beliefs by Belief Functions: An Axiomatic Justification](../Smets_1993_QuantifyingBeliefsBeliefFunctions/notes.md) - Smets axiomatizes the credibility function itself (point-valued belief). Shenoy axiomatizes the *propagation/combination operators* across Bayesian and belief-function settings. Complementary: Shenoy fixes the operator algebra, Smets fixes the underlying point-valued measure. Smets's identification of unnormalized Dempster's rule as the unique conditioning operator satisfying homomorphism + preservation lines up with Shenoy's combination-operator axioms when applied at the credal level.
