---
title: "Computational Properties of Argument Systems Satisfying Graph-theoretic Constraints"
authors: "Paul E. Dunne, Michael Wooldridge"
year: 2009
venue: "Artificial Intelligence, 2009 (Tech Report, Dept of Comp. Sci., Univ. of Liverpool, August 2006)"
doi_url: "https://doi.org/10.1007/978-0-387-98197-0_5"
---

# Computational Properties of Argument Systems Satisfying Graph-theoretic Constraints

## One-Sentence Summary

Provides a comprehensive complexity map of standard decision problems (credulous acceptance, sceptical acceptance, existence of preferred/stable extensions, coherence) across structural restrictions on argument systems (k-partite, bounded degree, planar, bounded treewidth, value-based), establishing exact complexity classes and identifying tractable fragments.

## Problem Addressed

Many natural decision problems in abstract argumentation (credulous/sceptical acceptance under preferred, stable, grounded semantics) are computationally intractable in general -- NP-complete, coNP-complete, or Pi_2^p-complete. The paper investigates which graph-theoretic restrictions on the attack structure yield tractable classes, and which restrictions preserve the hardness. *(p.1)*

## Key Contributions

- Complete complexity classification (Table 1) for 7 decision problems (CA, CA^S, PREF-EXT, STAB-EXT, SA, SA^S, COHERENT) in the general case *(p.5)*
- Complexity classification (Table 2) for k-partite argument systems: bipartite systems are polynomial for CA and SA; 3-partite systems remain NP/coNP/Pi_2^p-complete *(p.8)*
- Proof that bounded degree systems with (p,q)-bounded degree for any fixed p,q do NOT lead to improved complexity -- the class Delta^(2,2) is polynomially CA-universal and SA-universal *(p.12-14)*
- Proof that planar argument systems remain NP-complete for CA and coNP-complete for SA *(p.16-21)*
- Linear-time decidability for all standard problems on systems with bounded treewidth, via MSOL definability (Theorem 17) *(p.22-27)*
- Extension to value-based argumentation frameworks (VAFs): SBA is NP-complete and OBA is coNP-complete even when the graph structure is a tree *(p.28-32)*
- Two open conjectures on fixed-parameter tractability of VAFs *(p.37-38)*

## Methodology

The paper uses reduction-based complexity analysis throughout. Key techniques:

1. **Reduction gadgets**: Two canonical argument systems H_Phi and G_Phi constructed from CNF/QSAT formulae, used as building blocks for all hardness proofs *(p.5-7)*
2. **Simulation**: The concept of one class of argument systems "polynomially simulating" another (Definition 9), enabling universality results *(p.13)*
3. **Graph-theoretic transformations**: Systematic replacement of high-degree nodes, crossing elimination for planarity, tree decomposition width bounding *(p.14-18)*
4. **MSOL definability**: Encoding decision problems as monadic second-order logic sentences, then applying Courcelle's theorem for linear-time decidability on bounded treewidth *(p.23-27)*

## Key Definitions

### Argument System (Definition 1)
An argument system is a pair H = (X, A) where X is a finite set of arguments and A subset X x X is the attack relationship. *(p.4)*

### Standard Decision Problems (Table 1)

| Problem | Instance | Question |
|---------|----------|----------|
| CA | H(X,A), x in X | Is x credulously accepted? |
| CA^S | H(X,A), x in X | Is x in any stable extension? |
| PREF-EXT | H(X,A) | Does H have a non-empty preferred extension? |
| STAB-EXT | H(X,A) | Does H have any stable extension? |
| SA | H(X,A), x in X | Is x sceptically accepted? |
| SA^S | H(X,A), x in X | Is x in every stable extension? |
| COHERENT | H(X,A) | Is the system H coherent? |

*(p.5)*

### Semantics Definitions
- **Conflict-free**: S subset X is conflict-free if no argument in S is attacked by any other argument in S *(p.4)*
- **Admissible**: S is admissible if S is conflict-free and every S in S is acceptable w.r.t. S (i.e., every attacker of s has an attacker in S) *(p.4)*
- **Preferred extension**: A maximal (w.r.t. set inclusion) admissible set *(p.4)*
- **Stable extension**: S is conflict-free and every y not in S is attacked by S *(p.4)*
- **Coherent**: Every preferred extension is also a stable extension *(p.4)*
- **Credulously accepted**: x is in some preferred extension *(p.4)*
- **Sceptically accepted**: x is in every preferred extension *(p.4)*

### k-partite (Definition 5)
An argument system H(X, A) is k-partite if there is a partition of X into k sets (X_1, ..., X_k) such that for all (y, z) in A, y in X_i implies z not in X_i. *(p.8)*

### Bounded Degree (Definition 10)
An argument system H(X, A) has (p, q)-bounded degree if for all x in X: |{y in X : (y,x) in A}| <= p and |{y in X : (x,y) in A}| <= q. Notation: Delta^(p,q). *(p.13)*

### Treewidth (Definition 15)
A tree decomposition (T, S) of a directed graph H(X,A) is a tree T = (r_1, ..., r_t) with family of sets S = {S_1, ..., S_t}, S_i subset X, satisfying:
- a. For all (y, z) in A, there is at least one S_i containing both y and z
- b. For each x in X, the subtree of T induced by {r_i : x in S_i} is connected (i.e., a subtree)
The width = max|S_i| - 1. The treewidth tw(H) = minimum width over all tree decompositions. *(p.23)*

### Value-based Argumentation Framework (Definition 21)
A VAF is a triple (H(X, A, V, eta)) where H(X, A) is an argument system, V = {v_1, ..., v_r} a set of values, and eta: X -> V maps each argument to a value. An audience R is a binary relation on V (irreflexive, transitive, asymmetric -- a strict partial order). Attack succeeds only when the attacker's value is not less preferred than the attacked argument's value under R. *(p.28)*

## Key Equations

### H_Phi Construction (from CNF formula)
Given a CNF formula Phi(Z_n) = conjunction of C_j, each C_j a disjunction of literals from {z_1, ..., z_n, not z_1, ..., not z_n}:

$$
\mathcal{X} = \{\Phi, C_1, \ldots, C_m\} \cup \{z_i, \neg z_i : 1 \leq i \leq n\}
$$

$$
\mathcal{A} = \{\langle C_j, \Phi \rangle : 1 \leq j \leq m\} \cup \{\langle z_i, \neg z_i \rangle, \langle \neg z_i, z_i \rangle : 1 \leq i \leq n\} \cup \{\langle z_i, C_j \rangle : z_i \text{ occurs in } C_j\} \cup \{\langle \neg z_i, C_j \rangle : \neg z_i \text{ occurs in } C_j\}
$$

*(p.6)*

### G_Phi Construction (from QSAT formula)
Extends H_Phi with additional variables y_i, blocker arguments b_1, b_2, b_3, and additional attacks:

$$
\mathcal{W} = \{\Phi, C_1, \ldots, C_m\} \cup \{y_i, \neg y_i, z_i, \neg z_i : 1 \leq i \leq n\} \cup \{b_1, b_2, b_3\}
$$

$$
\mathcal{B} = \{\langle C_j, \Phi \rangle : 1 \leq j \leq m\} \cup \{\langle y_i, \neg y_i \rangle, \langle \neg y_i, y_i \rangle, \langle z_i, \neg z_i \rangle, \langle \neg z_i, z_i \rangle : 1 \leq i \leq n\} \cup \{\langle y_i, C_j \rangle, \langle \neg y_i, C_j \rangle, \langle z_i, C_j \rangle, \langle \neg z_i, C_j \rangle \text{ as appropriate}\} \cup \{\langle \Phi, b_1 \rangle, \langle \Phi, b_3 \rangle, \langle b_1, b_2 \rangle, \langle b_2, b_3 \rangle, \langle b_3, b_1 \rangle\} \cup \{\langle b_1, z_i \rangle, \langle b_1, \neg z_i \rangle : 1 \leq i \leq n\}
$$

*(p.7)*

### MSOL Encoding of PREF-EXT
$$
\exists U \subseteq \mathcal{X} \; (U \neq \emptyset) \wedge ADM(\mathcal{X}, \mathcal{A}, U)
$$

where ADM(X, A, U) is:
$$
\forall x \in \mathcal{X} \; \forall y \in \mathcal{X} \; \langle x, y \rangle \in \mathcal{A} \rightarrow (\neg(x \in U) \vee \neg(y \in U)) \wedge (y \in U \rightarrow (\exists z (z \in U) \wedge \langle z, x \rangle \in \mathcal{A}))
$$

*(p.25)*

### MSOL Encoding of STAB-EXT
$$
\exists U \subseteq \mathcal{X} \; ADM(\mathcal{X}, \mathcal{A}, U) \wedge \forall x \in \mathcal{X} \; \neg(x \in U) \rightarrow (\exists z \in U \; \langle z, x \rangle \in \mathcal{A})
$$

*(p.25)*

### MSOL Encoding of COHERENT
$$
\forall U \subseteq \mathcal{X} \; PREF(\mathcal{X}, \mathcal{A}, U) \rightarrow STABLE(\mathcal{X}, \mathcal{A}, U)
$$

*(p.25)*

### Treewidth Bound for H_Phi
$$
tw(\mathcal{H}_\Phi) \leq tw(H^{prm}) \leq (D(H) + 1)(tw(H) + 1) - 1
$$

where D(H) is the maximum degree of the primal graph and H^prm is the primal graph. *(p.27)*

### VAF Attack Parameter
$$
\sigma(\langle \mathcal{H}(\mathcal{X}, \mathcal{A}), \mathcal{V}, \eta \rangle) = |\{\langle x, y \rangle \in \mathcal{A} : \eta(x) = \eta(y)\}|
$$

Counts attacks between arguments sharing the same value. *(p.38)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of arguments | \|X\| | - | - | finite | 4 | Core parameter |
| Number of attacks | \|A\| | - | - | subset X x X | 4 | |
| Partition count (k-partite) | k | - | - | k >= 2 | 8 | k=2 is bipartite |
| In-degree bound | p | - | - | p >= 0 | 13 | Bounded degree |
| Out-degree bound | q | - | - | q >= 0 | 13 | Bounded degree |
| Treewidth | tw(H) | - | - | >= 1 | 23 | Width of tree decomposition |
| Number of values (VAF) | \|V\| | - | - | >= 1 | 28 | Value-based frameworks |
| Same-value attack count | sigma | - | - | 0 to \|A\| | 38 | VAF parameter |

## Implementation Details

### Algorithm 1: Credulous Acceptance in Bipartite Systems *(p.10)*
**Input**: Bipartite argument system B(Y, Z, A) and argument x in Y or Z
**Output**: Whether x is credulously accepted

1. Set S = {x}
2. Repeat:
   - A_S = Y_S union {y in Y : exists z in Z, (y,z) in A and (z,y) in A_S} and similarly for Z
   - A_S = A_S union {y : y not in S and (y,z) not in A for all z in S or y has defender in S}
3. Until S stabilizes
4. Return whether S is admissible

This runs in polynomial time -- at most |Y| iterations of the main loop, each taking only polynomial many steps. *(p.10)*

### Algorithm 2: Ordering of Arguments in X_e *(p.19)*
**Input**: Set X_e of crossing-point arguments
**Output**: Labeling lambda: X_e -> {0, 1, ..., r}

1. lambda(x) := 0 for all x in X_e
2. T := X_e; k := 1
3. While k <= r do:
   - If exists x in T attacked by two literals: lambda(x) := k; T := T \ {x}
   - Else if exists x in T attacked by a literal and x' in X_e \ T: lambda(x) := k; T := T \ {x}
   - Else: Choose any x in T with both attackers in X_e \ T; lambda(x) := k; T := T \ {x}
4. k := k + 1
5. End while

Used in the planar graph reduction to order crossing-point arguments for the crossover gadget construction. *(p.19)*

## Figures of Interest

- **Fig 1 (p.6):** The argument system H_Phi for a 4-variable 3-clause CNF formula -- canonical reduction gadget
- **Fig 2 (p.7):** The argument system G_Phi -- extended gadget for Pi_2^p-completeness proofs
- **Fig 3 (p.14):** Argument x attacked by k >= 3 arguments -- starting point for degree reduction
- **Fig 4 (p.14):** Reducing k attacks to k-1 attacks -- the core transformation for bounded degree universality
- **Fig 5 (p.16):** Planar drawing of K_4 (complete graph on 4 vertices)
- **Fig 6 (p.17):** H_Phi after crossings replaced by new arguments z_i
- **Fig 7 (p.18):** Crossing edges in H_Phi and their replacement -- key planar construction
- **Fig 8 (p.19):** Planar crossover gadget -- the diamond-shaped structure preserving credulous acceptance
- **Fig 9 (p.31):** T_Phi for a VAF instance -- tree-structured value-based framework
- **Fig 10 (p.38):** Local modification of G_Phi for 3-partite construction
- **Fig 11 (p.39):** Reducing occurrences of a value in T_Phi -- for binary tree restriction
- **Fig 12 (p.40):** Reducing clause sub-trees to binary trees in T_Phi^(3)

## Results Summary

### General Complexity (Table 1, p.5)

| Problem | Complexity |
|---------|-----------|
| CA | NP-complete |
| PREF-EXT | NP-complete |
| STAB-EXT | NP-complete (trivially, since a = d) |
| SA | coNP-complete |
| SA^S | coNP-complete |
| COHERENT | Pi_2^p-complete |

*(p.4-5)*

### k-partite Systems (Table 2, p.8)

| Problem | k=2 | k=3 |
|---------|-----|-----|
| CA | Polynomial-time | NP-complete |
| CA with bipartite 1-1 | NP-complete | - |
| SA | Polynomial-time | Pi_2^p-complete |
| SA with bipartite 1-1 | Polynomial-time | - |
| COHERENT(2) | Trivial | - |
| COHERENT(3) | Pi_2^p-complete | - |

*(p.8)*

### Bounded Degree
- Delta^(2,2) is polynomially CA-universal and SA-universal (Theorem 11) *(p.14)*
- This means restricting to bounded degree does NOT reduce complexity *(p.12)*

### Planar Systems
- CA restricted to planar graphs is NP-complete (Theorem 12) *(p.17)*
- PREF-EXT restricted to planar 3-partite systems is NP-complete (Corollary 4) *(p.22)*
- SA, COHERENT for planar systems: Theorem 14 gives SA^P is NP-complete, COHERENT^P is Pi_2^p-complete *(p.22)*

### Bounded Treewidth (the tractable case!)
- **Theorem 17**: For constant k, given H(X,A) in W^(k) (treewidth <= k) together with a width-k tree decomposition, PREF-EXT, STAB-EXT, COHERENT, and "at least one sceptically accepted argument" are all decidable in LINEAR TIME *(p.24)*
- This is via Courcelle's theorem: any property definable in MSOL is linear-time decidable on graphs of bounded treewidth *(p.23-24)*
- The fixed-parameter tractability result: CA_k(H, S) can be computed in O(f(g(n)) * n) time where g(n) is a constant independent of H and n is the size of H *(p.26)*

### Value-based Frameworks
- SBA^(T) (subjective acceptance on trees) is NP-complete (Theorem 23) *(p.29)*
- OBA^(T) (objective acceptance on trees) is coNP-complete (Corollary 7) *(p.32)*
- SBA^(T,V,S,B) is NP-complete even if instances are binary trees (Theorem 25) *(p.37)*

## Limitations

- Bounded treewidth tractability depends on having the tree decomposition in hand; computing optimal treewidth is itself NP-hard in general, though FPT algorithms exist *(p.24)*
- The MSOL approach, while giving linear-time theoretical results, involves constants that "increase rapidly with the treewidth bound" -- the hidden constant in Courcelle's theorem is non-elementary *(p.34)*
- The relationship between treewidth of the primal graph and the argument system's own treewidth involves multiplicative factors: tw(H_Phi) <= (D(H)+1)(tw(H)+1) - 1 *(p.27)*
- For value-based frameworks, restricting to trees does NOT yield tractability (unlike standard argumentation) *(p.29)*
- The paper does not address semi-stable or ideal semantics *(p.1)*
- Open: whether efficient algorithms exist in practice for bounded-treewidth systems despite the non-elementary constant *(p.34-35)*

## Arguments Against Prior Work

- Prior complexity results by Dimopoulos and Torres [18] and Dunne and Bench-Capon [24] established completeness results but did not systematically investigate graph-theoretic restrictions *(p.2)*
- The general intractability results "should not be overstated" -- they motivate the search for tractable subclasses rather than abandonment of the framework *(p.2)*
- Dunne [20] identified directed acyclic graphs as a tractable class, but "recent work of Coste-Marquis et al. [14] has shown that symmetric argument systems -- those in which x attacks y if and only if y attacks x -- also form a tractable class" *(p.2)*
- The bounded degree restriction is shown to be insufficient despite intuitions that limiting connectivity might help: "restricting to bounded degree does not lead to improved algorithmic methods" *(p.12)*

## Design Rationale

- **Why k-partite?** Bipartite systems capture a natural "two-sided" debate structure and yield polynomial algorithms; the jump to 3-partite restores full hardness, precisely delineating the boundary *(p.8-9)*
- **Why treewidth?** Tree-like structure is the canonical parameterization for tractability in graph problems; the MSOL approach provides a unified framework rather than ad-hoc algorithms *(p.22-23)*
- **Why value-based extensions?** VAFs (Bench-Capon [7]) add preference orderings via audience-relative defeat, representing a natural extension; the paper shows that graph-theoretic restrictions alone cannot tame VAF complexity because the combinatorics of value orderings (audiences) dominate *(p.28-29)*
- **Simulation as a tool**: The polynomial simulation concept (Definition 9) lets them prove universality results -- showing that a restricted class can encode any general system -- rather than constructing individual reductions for each problem *(p.13)*

## Testable Properties

- In bipartite argument systems, credulous and sceptical acceptance are polynomial-time decidable *(p.5, 9)*
- Every argument system H is coherent iff H has no odd-length simple directed cycles (Fact 2d) *(p.5)*
- If H(X,A) is a tree, then H is coherent (Coste-Marquis et al. [14]) *(p.5)*
- If H(X,A) contains no odd-length simple directed cycles, then H is coherent *(p.5)*
- If H(X,A) is coherent then SA(H, x) can be decided in co-NP (rather than Pi_2^p) *(p.5)*
- For bipartite systems: every system has at least one preferred extension; if bipartite and a tree, it has a unique preferred extension computable in linear time *(p.5)*
- The class Delta^(2,2) (in-degree <= 2, out-degree <= 2) is polynomially universal for both CA and SA *(p.14)*
- For bounded treewidth k: all of CA, SA, PREF-EXT, STAB-EXT, COHERENT are decidable in O(f(k) * n) time *(p.24)*
- In VAFs: SBA on trees is NP-complete, so tree structure alone is insufficient for tractability *(p.29)*
- Conjecture 1: SBA^(V,S,S) (fixed values, fixed occurrences per value) is polynomial-time decidable *(p.37)*
- Conjecture 2: SBA is fixed-parameter tractable w.r.t. the parameter sigma (same-value attack count) *(p.38)*

## Relevance to Project

This paper provides the computational complexity landscape that governs what the propstore argumentation layer can efficiently compute. Key implications:

1. **Extension computation feasibility**: The grounded extension is always polynomial, but preferred/stable extension computation is NP-hard in general. Systems with bounded treewidth offer a tractable pathway.
2. **Tree decomposition as optimization target**: The treewidth results (Theorem 17) directly connect to the project's `praf_treedecomp.py` module -- if argument graphs have bounded treewidth, all standard semantics become linear-time.
3. **Bipartite structure as design target**: If argument systems can be structured as bipartite (e.g., pro/con partitions), credulous and sceptical acceptance become polynomial.
4. **Value-based hardness warning**: Even tree-structured VAFs are NP-hard, meaning preference-based argumentation requires careful algorithmic design regardless of graph structure.

## Open Questions

- [ ] What is the practical treewidth of argument graphs arising from propstore's claim extraction pipeline?
- [ ] Can the bipartite polynomial algorithm (Algorithm 1) be applied to pro/con structured debates?
- [ ] Is the non-elementary constant in Courcelle's theorem a practical barrier for the treewidth bounds encountered in real argumentation?
- [ ] Can the VAF hardness results be circumvented by fixing the number of values (Conjecture 1)?
- [ ] What is the relationship between tw(H) and the number of arguments for typical propstore workloads?

## Related Work Worth Reading

- Dimopoulos and Torres [18] -- original NP-completeness of CA via 3-SAT reduction
- Dunne and Bench-Capon [24] -- Pi_2^p-completeness of SA, complexity in value-based frameworks
- Courcelle [15,16] -- MSOL definability and linear-time decidability on bounded treewidth graphs (foundational theorem)
- Bodlaender [13] -- FPT algorithm for computing treewidth
- Gottlob et al. [29] -- fixed-parameter tractability of CNF-SAT via treewidth
- Bench-Capon [7] -- value-based argumentation frameworks (VAFs)
- Coste-Marquis et al. [14] -- symmetric argumentation frameworks and tractable classes
- Dvořák and Woltran (cited in context of semi-stable semantics, not in this paper but relevant follow-up)
