---
title: "Properties of Sensitivity Analysis of Bayesian Belief Networks"
authors: "Veerle M.H. Coupé, Linda C. van der Gaag"
year: 2002
venue: "Annals of Mathematics and Artificial Intelligence"
doi_url: "https://doi.org/10.1023/A:1016398407857"
pages: "323-356"
produced_by:
  agent: "Claude Opus 4.6 (1M context)"
  skill: "paper-reader"
  timestamp: "2026-03-28T22:09:44Z"
---
# Properties of Sensitivity Analysis of Bayesian Belief Networks

## One-Sentence Summary

This paper proves that a Bayesian belief network's posterior probability of interest is a linear fractional function (quotient of two linear functions) of any single conditional probability parameter, enabling efficient one-way sensitivity analysis by reducing network evaluations from full sweeps to as few as three.

## Problem Addressed

Sensitivity analysis of BNs investigates the effects of inaccuracies in the conditional probability tables on the network's output. Full sensitivity analysis — varying every CPT entry and recomputing the posterior — is computationally prohibitive for large networks. The paper addresses two subproblems: (1) identifying which conditional probabilities are *uninfluential* (can be excluded from analysis), and (2) characterizing the *functional form* of how the remaining influential probabilities affect the output. *(p.1-2)*

## Key Contributions

1. **Sensitivity set definition and partition:** Formal definition of the sensitivity set Sen(V_r, O) — the set of nodes whose conditional probabilities can affect the probability of interest — and a three-way partition of non-sensitivity-set nodes into Insen_1, Insen_2, Insen_3. *(p.5-8)*
2. **Algebraic independence theorem (Proposition 3.11):** The probability of interest is algebraically independent of the conditional probabilities of any node NOT in the sensitivity set. These uninformative CPTs can be excluded from analysis entirely. *(p.13)*
3. **Linear fractional function theorem (Proposition 4.1):** The probability of interest relates to any single conditional probability x in the sensitivity set as Pr(v_r | o) = (ax + b)/(cx + d), where a, b, c, d are constants determined by the remaining network parameters. *(p.14)*
4. **Linear function special case (Propositions 4.3, 4.5):** When the sensitivity set node V_s has no observed descendants (sigma*(V_s) ∩ O = emptyset), the function reduces to a simple linear function Pr(v_r | o) = ax + b. This also holds when observations are empty (O = emptyset). *(p.16-18)*
5. **Computational reduction:** The constants a, b, c, d can be determined from as few as 2-3 network evaluations (2 for linear case, 3 for fractional case), rather than a full sweep over all parameter values. *(p.18-19)*

## Methodology

The paper uses algebraic manipulation of the joint probability distribution expressed as products of conditional probabilities in a Bayesian belief network. The proofs exploit the factorization property of BNs (each joint configuration is a product of local CPTs), the d-separation criterion for conditional independence, and the concept of an auxiliary digraph G* that extends the network's digraph with an auxiliary predecessor X for each ancestral node of the node of interest. The auxiliary digraph is used to define the sensitivity set via d-separation. *(p.2-8)*

## Key Equations / Statistical Models

### Bayesian belief network joint distribution

$$
\Pr(\mathbf{V}) = \prod_{V_i \in V(G)} p(V_i \mid \pi_G(V_i))
$$

Where: V(G) is the set of all nodes in the digraph G, pi_G(V_i) is the set of parents of V_i in G, and p(V_i | pi_G(V_i)) is the conditional probability of V_i given its parents.
*(p.3)*

### Probability of interest (posterior)

$$
\Pr(v_r \mid o) = \frac{\Pr(v_r \wedge o)}{\Pr(o)}
$$

Where: v_r is a specific value of the node of interest V_r, and o is the set of observed values for observed nodes O.
*(p.9)*

### Main result: Linear fractional function (Proposition 4.1)

$$
\Pr(v_r \mid o) = \frac{ax + b}{cx + d}
$$

Where: x = p(v_s | pi) is any single conditional probability for a node V_s in Sen(V_r, O); a, b, c, d are constants that depend on v_r, o, and all other conditional probabilities in the network but NOT on x.
*(p.14)*

### Numerator decomposition

$$
\Pr(v_r \wedge o) = ax + b
$$

Where:

$$
a = \sum_{\{V_1,...,V_n\} \setminus (\{V_r,V_s\} \cup \pi_G(V_s) \cup O)} \left( \prod_{\substack{i=1,...,n \\ i \neq s}} p(V_i \mid \pi_G(V_i)) \right) \bigg|_{\substack{V_r=v_r, O=o \\ V_s=v_s, \pi_G(V_s)=\pi}} - \sum_{\{V_1,...,V_n\} \setminus (\{V_r,V_s\} \cup \pi_G(V_s) \cup O)} \left( \prod_{\substack{i=1,...,n \\ i \neq s}} p(V_i \mid \pi_G(V_i)) \right) \bigg|_{\substack{V_r=v_r, O=o \\ V_s=\neg v_s, \pi_G(V_s)=\pi}}
$$

$$
b = \sum_{\{V_1,...,V_n\} \setminus (\{V_r,V_s\} \cup \pi_G(V_s) \cup O)} \left( \prod_{\substack{i=1,...,n \\ i \neq s}} p(V_i \mid \pi_G(V_i)) \right) \bigg|_{\substack{V_r=v_r, O=o \\ V_s=\neg v_s, \pi_G(V_s)=\pi}} + \sum_{\substack{\{V_1,...,V_n\} \setminus O, \\ \pi_G(V_s) \neq \pi}} \left( \prod_{i=1,...,n} p(V_i \mid \pi_G(V_i)) \right) \bigg|_{\substack{V_r=v_r \\ O=o}}
$$

*(p.29-30)*

### Denominator decomposition

$$
\Pr(o) = cx + d
$$

With c, d defined analogously to a, b but without the constraint V_r = v_r.
*(p.30-31)*

### Linear special case (Proposition 4.3)

When sigma*(V_s) ∩ O = emptyset (no observed descendants of V_s):

$$
\Pr(v_r \mid o) = ax + b
$$

Where: a and b are constants dependent on v_s and pi.
*(p.16)*

### No-observations case (Corollary 4.5)

When O = emptyset (prior probability, no observations):

$$
\Pr(v_r) = ax + b
$$

for every conditional probability x = p(v_s | pi) of V_s, where a and b are constants.
*(p.18)*

### Constants from network evaluations (Corollary 4.6)

For the linear case, two network evaluations suffice to determine a and b. For the fractional case, three evaluations at distinct x values (e.g., x = 0, x = 0.5, x = 1) yield three equations in three unknowns (a'/c', a, b' where a' = a/c', b' = b/c'):

$$
\Pr(v_r \mid o) = \frac{a'x + b'}{x + e}
$$

solved by three linear equations.
*(p.18-19)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Conditional probability under study | x | - | - | [0,1] | p.14 | x = p(v_s \| pi) for node V_s in sensitivity set |
| Numerator linear coefficient | a | - | - | - | p.14 | Depends on all other CPTs, not on x |
| Numerator constant | b | - | - | - | p.14 | Depends on all other CPTs, not on x |
| Denominator linear coefficient | c | - | - | - | p.14 | Depends on all other CPTs, not on x |
| Denominator constant | d | - | - | - | p.14 | Depends on all other CPTs, not on x |

## Methods & Implementation Details

- **Sensitivity set computation (Definition 3.1):** For a BN with node of interest V_r and observed nodes O, construct auxiliary digraph G* by adding an auxiliary predecessor X_i to every node V_i in the set of ancestors of V_r (and V_r itself). Sen(V_r, O) is the set of all nodes V_i such that X_i is NOT d-separated from V_r given O in G*. *(p.5)*
- **Three-way partition of insensitive nodes:** *(p.7-8)*
  - Insen_1(V_r, O): nodes V_i where V_i is d-separated from V_r given O in the original graph (not just G*). Their CPTs don't influence Pr(v_r | o).
  - Insen_2(V_r, O): non-ancestor nodes of V_r that have observed descendants. They can influence Pr(o) but their influence cancels in the ratio Pr(v_r ∧ o)/Pr(o).
  - Insen_3(V_r, O): ancestor nodes of V_r whose auxiliary predecessors are d-separated from V_r by O in G*. These are ancestors whose variation is "screened off" by observations.
- **ALARM network running example:** The 37-node ALARM network (Beinlich et al. 1989) is used throughout to illustrate concepts. For node LV failure with observations {LV failure, History}, the sensitivity set has only 17 of 37 nodes' CPTs, reduced further to 10 nodes for specific observation sets. *(p.6-7)*
- **Computing constants a, b, c, d:** Rather than deriving constants algebraically from the full network structure, they can be computed by evaluating the network at 2 or 3 specific values of x: *(p.18-19)*
  - Linear case: evaluate at x=0 and x=1 to get b and a+b, yielding a and b directly.
  - Fractional case: evaluate at x=0, x=0.5, x=1 to get three equations in three unknowns; solve the linear system.
- **Sensitivity value:** The derivative of the sensitivity function at the current assessment gives the sensitivity value — how much the probability of interest changes per unit change in x. For the linear case, this is simply a (constant). For the fractional case, the derivative of (ax+b)/(cx+d) is (ad-bc)/(cx+d)^2, which varies with x. *(p.16, 19)*
- **Proof technique for Proposition 4.1:** The proof uses a sensitivity ordering (a topological ordering of G compatible with the sensitivity set partition) and exploits the fact that the joint probability factorizes into a product of CPTs. The conditional probability x appears in exactly one factor, so the numerator Pr(v_r ∧ o) splits into terms that are linear in x and terms that are independent of x, yielding Pr(v_r ∧ o) = ax + b. Similarly for the denominator. *(p.24-31)*

## Figures of Interest

- **Fig 1 (p.4):** The ALARM network digraph — 37 nodes with observable nodes indicated by double circles and node of interest LV failure by a shaded node.
- **Fig 2 (p.9):** Example belief network illustrating the sets Insen_1 (LV failure, {PCWP}).
- **Fig 3 (p.11):** Example belief network illustrating the set Insen_2 (LV failure, {CO, Blood press}).
- **Fig 4 (p.13):** Example belief network illustrating the set Insen_3 (LV failure, {History}).
- **Fig 5 (p.15):** Example belief network with observed node PAP and node of interest Shunt — used for the linear fractional example.
- **Fig 6 (p.16):** Plot of Pr(normal Shunt | high PAP) vs p(high PAP | no pulm emb), showing the characteristic curve of a linear fractional function with high sensitivity near x=0.05.

## Results Summary

The paper establishes that sensitivity analysis of any BN output with respect to any single CPT parameter follows a linear fractional (or linear) functional form. This has three practical consequences: (1) many CPT entries can be excluded from analysis entirely (those outside the sensitivity set), (2) the functional relationship for included parameters is fully determined by 2-3 network evaluations rather than a full sweep, and (3) the sensitivity function is monotonic (either always increasing or always decreasing), so extremal sensitivity values occur at the boundary of the parameter range. For the ALARM network example, this reduces the computational burden from evaluating all 37 nodes' CPTs to evaluating only 17 (or fewer depending on observations). *(p.16-22)*

## Limitations

- The paper focuses exclusively on **one-way sensitivity analysis** — varying a single conditional probability at a time. Higher-order sensitivity analysis (varying two or more parameters simultaneously) yields more complex functional forms that are harder to interpret. The authors note this as future work. *(p.21-22)*
- The complement constraint p(not-v_s | pi) = 1 - p(v_s | pi) is implicitly maintained. The analysis does not address what happens when multiple CPT entries for the same node are varied independently (which would violate the probability axioms). *(p.14)*
- The sensitivity set is defined for a single node of interest and a fixed observation set. Different queries require recomputing the sensitivity set. *(p.5)*
- The paper assumes exact inference; numerical precision issues in actual BN inference engines are not addressed. *(p.21)*

## Arguments Against Prior Work

- **Laskey [12]:** Laskey's method for sensitivity analysis suggests varying every single conditional probability, which is computationally infeasible for large networks. The authors' sensitivity set concept excludes uninformative probabilities a priori. However, Laskey did observe that some conditional probabilities have no effect, though she used a different (less formal) criterion. *(p.19-20)*
- **Castillo et al. [2]:** Castillo's symbolic propagation approach derives algebraic expressions for sensitivity but handles symbolic expressions that become unwieldy for large networks. The authors' approach requires only numerical evaluations. *(p.20)*
- **Kjærulff and van der Gaag [4, 19]:** Their own prior work on sensitivity analysis used auxiliary networks and did not establish the functional form analytically. This paper provides the theoretical foundation for why those methods work. *(p.1, 19-20)*

## Design Rationale

- **Auxiliary digraph G* for sensitivity set computation:** The auxiliary digraph extends the original BN digraph by adding a "virtual parent" X_i to each ancestor of the node of interest. This allows d-separation queries in G* to determine which CPTs can influence the output, without requiring actual inference. The alternative of computing sensitivity by full evaluation would be O(n * |values|) evaluations. *(p.5)*
- **Focus on one-way analysis:** The authors deliberately restrict to one-way analysis because the resulting functional form (linear fractional) is simple enough to be practically useful — you can determine the full sensitivity curve from 2-3 evaluations. Multi-way analysis does not have this property. *(p.21)*
- **Sensitivity ordering:** The proofs use a carefully constructed topological ordering that places sensitivity-set nodes first and insensitive nodes last, enabling clean separation of x-dependent and x-independent terms in the joint probability factorization. *(p.24)*

## Testable Properties

- **Linear fractional form:** For any BN, any node of interest V_r, any observation set O, and any single CPT parameter x = p(v_s | pi) where V_s in Sen(V_r, O): Pr(v_r | o) = (ax+b)/(cx+d) for constants a,b,c,d independent of x. *(p.14)*
- **Linear special case:** When sigma*(V_s) ∩ O = emptyset: the function reduces to Pr(v_r | o) = ax + b (c = 0, d = constant). *(p.16)*
- **Three-point determination:** For the fractional case, exactly three evaluations at distinct x values suffice to determine the full sensitivity function. *(p.18-19)*
- **Two-point determination:** For the linear case, exactly two evaluations at distinct x values suffice. *(p.18)*
- **Monotonicity:** The sensitivity function (ax+b)/(cx+d) is monotonic on [0,1] (no local extrema). *(p.16)*
- **Sensitivity set exclusion:** Varying any CPT parameter for a node NOT in Sen(V_r, O) does not change Pr(v_r | o). *(p.13)*

## Relevance to Project

This paper is relevant to propstore's probabilistic argumentation layer. When BN-style probabilistic reasoning is used to compute argument strengths or claim probabilities, sensitivity analysis tells you which input parameters actually matter. The linear fractional function result means that parameter sensitivity can be cheaply computed — useful for understanding which evidence or which CPT assessments most affect the outcome of probabilistic argumentation. This connects to:

- **Hunter & Thimm 2017 probabilistic argumentation:** Understanding how argument acceptance probabilities respond to parameter changes.
- **Subjective Logic (Josang 2001):** The uncertainty parameter u in opinions could be analyzed for sensitivity — how much does changing u affect the fused result?
- **Calibration (Guo et al. 2017):** Sensitivity analysis could quantify how calibration errors propagate through the argumentation network.

## Open Questions

- [ ] Can the linear fractional result be extended to multi-way sensitivity (varying k parameters simultaneously)? The authors mention this produces quotients of multilinear functions.
- [ ] How does the sensitivity set relate to d-separation in probabilistic argumentation frameworks (PrAFs)?
- [ ] Can the 3-evaluation trick be applied to ASPIC+ argument strength computation?

## Related Work Worth Reading

- **Castillo et al. 1997** [2] — Sensitivity analysis in discrete Bayesian networks using symbolic propagation
- **Laskey 1995** [12] — Sensitivity analysis for probability assessments in Bayesian networks (IEEE Trans SMC)
- **Chan & Darwiche 2005** — Sensitivity analysis in Bayesian networks → NOW IN COLLECTION: [[Chan_2005_DistanceMeasureBoundingProbabilistic]]
- **van der Gaag & Renooij 2001** [19] — Analysing sensitivity data (UAI 2001)
- **Jensen 2001** [11] — Bayesian Networks and Decision Graphs (textbook)

## Collection Cross-References

### Already in Collection
- [[Chan_2005_DistanceMeasureBoundingProbabilistic]] — Chan & Darwiche cite Coupe et al. 2000 (a related technical report by the same group). Chan & Darwiche's distance-based approach to bounding belief change complements this paper's functional characterization of sensitivity.

### New Leads (Not Yet in Collection)
- Castillo, Gutierrez & Hadi (1997) — "Sensitivity analysis in discrete Bayesian networks" — alternative symbolic approach to the same problem
- Laskey (1995) — "Sensitivity analysis for probability assessments in Bayesian networks" — earlier work this paper builds on and critiques
- van der Gaag & Renooij (2001) — "Analysing sensitivity data" — follow-up by same group on interpreting sensitivity results

### Conceptual Links (not citation-based)
- [[Hunter_2021_ProbabilisticArgumentationSurvey]] — Hunter's probabilistic argumentation survey covers acceptance probabilities over probabilistic AFs; the linear fractional result from this paper could characterize how argument acceptance responds to parameter perturbation in BN-encoded argumentation
- [[Popescu_2024_ProbabilisticArgumentationConstellation]] — Popescu's tree-decomposition approach to PrAF computation involves repeated marginalizations over probabilistic parameters; the sensitivity set concept could identify which argument/defeat probabilities actually affect a given query
- [[Josang_2001_LogicUncertainProbabilities]] — SL opinion fusion involves combining belief/disbelief/uncertainty parameters; the linear fractional sensitivity result may apply to understanding how individual opinion parameters affect fused outcomes
