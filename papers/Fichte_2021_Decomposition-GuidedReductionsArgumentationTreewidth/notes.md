---
title: "Decomposition-Guided Reductions for Argumentation and Treewidth"
authors: "Johannes Fichte, Markus Hecher, Yasir Mahmood, Arne Meier"
year: 2021
venue: "IJCAI 2021"
doi_url: "https://doi.org/10.24963/ijcai.2021/259"
pages: "1880-1886"
---

# Decomposition-Guided Reductions for Argumentation and Treewidth

## One-Sentence Summary
This paper introduces decomposition-guided (DG) reductions that compile abstract and logic-based argumentation problems into SAT or 2-QBF while linearly preserving treewidth, and proves these reductions are essentially optimal under ETH.

## Problem Addressed
SAT-based argumentation solvers can exploit low treewidth for fast solving, but it was unknown whether reductions from argumentation to SAT/QBF could preserve treewidth linearly. Naive reductions create dense parts in the primal graph, blowing up treewidth. For logic-based argumentation, even bounded treewidth results were missing entirely. *(p.1)*

## Key Contributions
- Introduction of decomposition-guided (DG) reductions: a new type of reduction guided by tree decompositions that compiles argumentation problems into SAT or 2-QBF with linear treewidth overhead *(p.1)*
- DG reductions for abstract argumentation covering the full set of standard semantics: stable, admissible, complete, preferred, semi-stable, stage *(p.1)*
- Confirmation that these reductions cannot be significantly improved under ETH *(p.1)*
- New upper bounds for logic-based argumentation (ARG, ARG-Check, ARG-Rel) using DG reductions *(p.1)*
- New lower bounds for logic-based argumentation by reducing from 2-QBF (ARG, ARG-Rel) or SAT (ARG-Check) *(p.1)*

## Methodology
The paper defines DG reductions as functions that take both an instance I of a problem P and a tree decomposition T = (T, chi) of the primal graph G_I, returning a qBf phi in time tower(l, o(width(T))) * poly(|var(phi)|). The key constraint is that the reduction must yield a TD T' = (T, chi') of G_phi, ensuring the resulting formula's treewidth is bounded by O(max_t |f(t, chi(t), chi'(children(t)))|). *(p.3)*

The reductions are constructed node-by-node along the tree decomposition, using auxiliary variables to split formulas that would otherwise create dense primal graphs. *(p.3-4)*

## Key Equations

### Extension Variables
$$
E := \{e_a \mid a \in A\}
$$
Where: $e_a$ indicates whether argument $a$ is in the extension.
*(p.3)*

### Conflict-Freeness Formula
$$
\text{conf}_R(E) := \bigwedge_{(a,b) \in R} (\neg e_a \vee \neg e_b)
$$
Where: ensures no two attacking arguments are both in the extension.
*(p.3)*

### In-Or-Attacked Formula (naive, breaks treewidth)
$$
\text{inOrX}_R(E) := \bigwedge_{a \in A} \left( \bigvee_{(b,a) \in R} e_b \vee e_a \right)
$$
Where: every argument is either in the extension or attacked by the extension.
*(p.3)*

### DG Reduction for Stable Extensions (Formula 1)
$$
d^t_a \leftrightarrow \bigvee_{t' \in \text{children}(t), a \in \chi(t')} d^{t'}_a \vee \bigvee_{(b,a) \in R_t} e_b
$$
Where: $d^t_a$ are defeated variables indicating whether $a$ is attacked by some argument $b \in \chi(t)$; guides defeated-argument information along the TD.
*(p.4)*

### Stable Extension Completion (Formula 3)
$$
e_a \vee d^{\text{last}(a)}_a \quad \text{for every } a \in A
$$
Where: ensures every argument is either in the extension or defeated.
*(p.4)*

### Defense Formula (naive, breaks treewidth)
$$
\text{def}_R(E) := \bigwedge_{(b,a) \in R} \left( \bigvee_{(c,b) \in R} e_c \vee \neg e_a \right)
$$
Where: ensures attackers of the extension are counter-attacked (defended).
*(p.4)*

### Admissible Extension - No-Attacking Variables (Formula 4)
$$
\neg n_a \vee \neg e_b \quad \text{for every } (a,b) \in R
$$
Where: $n_a$ indicates argument $a$ never attacks an argument in the extension.
*(p.4)*

### Admissible Extension Completion (Formula 5)
$$
e_a \vee n_a \vee d^{\text{last}(a)}_a \quad \text{for every } a \in A
$$
Where: generalizes Formula 3 - every argument is in the extension, never-attacking, or defeated.
*(p.4)*

### Bijective Preservation for Counting (Formulas 6-7)
$$
\neg n_a \vee \neg e_a \quad \text{for every } a \in A
$$
$$
\neg n_a \vee \neg d^{\text{last}(a)}_a \quad \text{for every } a \in A
$$
Where: ensures bijective correspondence between AF extensions and SAT solutions for counting problems.
*(p.4)*

### Preferred Extension Inequality (Formulas 8-11)
$$
e_a \wedge \neg \tilde{e}_a \quad \text{for every } a \in A
$$
$$
\neg(q_a \leftrightarrow \tilde{e}_a \wedge \neg e_a) \quad \text{for every } a \in A
$$
$$
\neg\left(q^t \leftrightarrow \bigvee_{t' \in \text{children}(t)} q^{t'} \vee \bigvee_{a \in \chi(t)} q_a\right) \quad \text{for every } t \text{ of } T
$$
$$
\neg q^{\text{root}(T)}
$$
Where: $\tilde{E}$ is a fresh copy of extension variables; $q_a$ tracks inequality between $E$ and $\tilde{E}$; $q^t$ guides inequality along the TD. These formulas ensure no proper superset of $E$ is also admissible (maximality check).
*(p.4-5)*

### Logic-Based ARG Reduction
$$
\text{cons}_\Delta(E, M) := \bigwedge_{C_i \in \Delta} (\neg e_i \vee C_i)
$$
$$
\text{ent}_{\Delta,\alpha}(E, \tilde{N}) := \bigvee_{C_i \in \Delta} (e_i \wedge \neg \tilde{C}_i) \vee \tilde{\alpha}
$$
Where: $e_i$ indicates whether clause $C_i$ is in the support; $\text{cons}$ ensures consistency of selected support; $\text{ent}$ ensures entailment of the claim.
*(p.5)*

### Tower Function
$$
\text{tower}(i, p) = \begin{cases} p & \text{if } i = 0 \\ \text{tower}(i-1, 2^p) & \text{if } i > 0 \end{cases}
$$
Where: used to express runtime bounds parameterized by treewidth and quantifier rank.
*(p.2)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Treewidth | k = tw(G_F) | - | - | >= 0 | p.2 | Width of tree decomposition minus 1 |
| Number of arguments | n = \|A\| | - | - | >= 1 | p.6 | For abstract argumentation |
| Number of variables | n = \|var(Delta) union var(alpha)\| | - | - | >= 1 | p.6 | For logic-based argumentation |
| Quantifier rank | l | - | - | >= 1 | p.2 | Number of quantifier alternations in QBF |
| Bag size multiplier (stable) | - | - | 5 | - | p.4 | |chi'(t)| <= 5 * |chi(t)| for stable reduction |

## Implementation Details
- DG reductions are constructed node-by-node along a tree decomposition *(p.3)*
- For each node t of T, the constructed bag chi'(t) depends on the original bag chi(t) and the constructed bags of child nodes *(p.3)*
- Tree decompositions are assumed to have |children(t)| <= 2 for every node, obtainable from any TD in linear time *(p.2)*
- For fixed width w >= 1, computing a TD of width w is feasible in linear time *(p.2)*
- Defeated variables D := {d^t_a | a in A, t in T} track which arguments are attacked, propagated along TD *(p.4)*
- No-attacking variables N := {n_a | a in A} track arguments that never attack any extension member *(p.4)*
- Inequality variables Q := {q^t, q_a | t of T, a in A} track differences between E and E-tilde for preferred/semi-stable *(p.4)*
- ARG-Check reduction produces n+2 independent qBfs that can be solved independently *(p.6)*
- ARG-Check formulas can be merged into 2 qBfs *(p.6)*

## Figures of Interest
- **Fig 1 (p.3):** Illustration of a DG reduction R from problem P to QBF, showing how the original TD T = (T, chi) maps to T' = (T, chi') where each new bag is constructed by function f depending on the original bag and children's constructed bags.

## Results Summary

### Treewidth Awareness (Table 1, p.6)
All DG reductions achieve O(k) treewidth overhead:
- Abstract argumentation (all semantics): O(k) *(p.6)*
- Logic-based argumentation (ARG, ARG-Rel, ARG-Check): O(k) *(p.6)*

### Runtime Upper Bounds (Table 1, p.6)
- cstab, cadm, ccomp, cpref: 2^{O(k)} * poly(n) *(p.6)*
- spref / #cpref: 2^{2^{O(k)}} * poly(n) *(p.6)*
- csemiSt, cstage: 2^{2^{O(k)}} * poly(n) *(p.6)*
- #cstab, #cadm, #ccomp: 2^{O(k)} * poly(n) *(p.6)*
- #csemiSt, #cstage: 2^{2^{O(k)}} * poly(n) *(p.6)*
- ARG, ARG-Rel: 2^{2^{O(k)}} * poly(n) *(p.6)*
- ARG-Check: 2^{O(k)} * poly(n) *(p.6)*

### Runtime Lower Bounds under ETH (Table 1, p.6)
- cstab, cadm, ccomp, cpref: 2^{o(k)} * poly(n) *(p.6)*
- spref: 2^{2^{o(k)}} * poly(n) / open *(p.6)*
- csemiSt, cstage: 2^{2^{o(k)}} * poly(n) *(p.6)*
- ARG, ARG-Rel: 2^{2^{o(k)}} * poly(n) *(p.6)*
- ARG-Check: 2^{o(k)} * poly(n) *(p.6)*

### Key Specific Results
- Theorem 5 (TW-Awareness for stable): tw(G_matrix(psi)) in O(k), with |chi'(t)| <= 5*|chi(t)| *(p.4)*
- Theorem 6 (TW-LB for stable): Under ETH, no reduction from cstab to SAT can achieve tw in o(tw(G_F)) *(p.4)*
- Theorem 11 (Runtime UB for ARG): ARG solvable in time tower(2, O(k)) * poly(n) *(p.5)*
- Theorem 12 (Runtime LB for ARG): Under ETH, ARG cannot be solved in time tower(2, o(tw(G_I))) * poly(n) *(p.5)*

## Limitations
- The lower bound for spref is marked as "open" - it is not known whether the double-exponential runtime is necessary *(p.6)*
- The work is theoretical; practical implementation is left as future work *(p.6)*
- Results assume the ETH; without ETH the lower bounds do not hold *(p.4-6)*
- Only considers standard Dung semantics; extensions to other frameworks not addressed *(p.1)*

## Arguments Against Prior Work
- Naive reductions from argumentation to SAT (e.g., inOrX_R(E) for stable semantics) cause dense parts in the primal graph, destroying the treewidth structure *(p.3-4)*
- Previous work on treewidth for abstract argumentation covered only admissible and preferred semantics [Lampis et al., 2018]; this paper provides a systematic approach for the full set of standard semantics *(p.2)*
- For logic-based argumentation, even bounded treewidth results were entirely missing before this work *(p.1)*

## Design Rationale
- DG reductions are guided by tree decompositions to avoid creating dense connections in the primal graph *(p.3)*
- Auxiliary "defeated" variables propagate attack information along the TD instead of creating direct connections between distant arguments *(p.4)*
- The reduction is designed node-by-node so that each new bag chi'(t) only depends on the original bag and children, ensuring the result is still a valid TD *(p.3)*
- For preferred/semi-stable, inequality variables are propagated along the TD rather than compared globally, preserving treewidth *(p.4-5)*
- ARG-Check is reduced to multiple independent qBfs (rather than one 2-QBF) because it is DP-complete, and each sub-question (consistency, entailment, minimality) can be handled separately *(p.6)*

## Testable Properties
- For any AF F with TD of width k, the DG reduction for stable extensions produces a formula with treewidth O(k) *(p.4)*
- Specifically, |chi'(t)| <= 5 * |chi(t)| for the stable extension reduction *(p.4)*
- The DG reductions are correct: #cS on F coincides with the corresponding QBF problem on the reduced formula, for all semantics S *(p.5)*
- Under ETH, no reduction from cstab to SAT can produce a formula with treewidth in o(tw(G_F)) and be computed in time 2^{o(tw(G_F))} * poly(|A|) *(p.4)*
- ARG-Rel is as hard as ARG: an instance (Delta, alpha) of ARG has a support iff (Delta union {psi}, alpha, psi) of ARG-Rel has one *(p.6)*

## Relevance to Project
This paper provides the theoretical foundations for understanding the computational complexity of argumentation problems when parameterized by treewidth. It directly connects abstract argumentation (Dung's framework) to SAT solving via structure-preserving reductions. The DG reduction framework shows how argumentation problems can be compiled into SAT/QBF while preserving the structural properties that make solving efficient. This is relevant to understanding which argumentation instances are tractable and why SAT-based argumentation solvers work well in practice.

## Open Questions
- [ ] Can the lower bound for spref be closed (currently marked "open" in Table 1)?
- [ ] What is the practical performance of DG reductions in actual solver implementations?
- [ ] Can strong ETH improve the bounds further?
- [ ] Do other graph parameters (besides treewidth) admit similar DG reduction frameworks? [Addressed by Mahmood_2025_Structure-AwareEncodingsArgumentationProperties — yes, clique-width admits DDG reductions with O(k) preservation for all standard semantics]
- [ ] Can the bijective solution preservation be exploited for enumeration complexity?

## Related Work Worth Reading
- [Lampis et al., 2018] - QBF reductions for admissible/preferred with treewidth (predecessor work)
- [Fichte et al., 2019] - Dynamic programming algorithms and lower bounds for various semantics
- [Hecher, 2020] - Treewidth-aware reductions for answer-set programming (inspired DG reductions)
- [Dvorak et al., 2012] - Fixed-parameter tractable algorithms for abstract argumentation -> NOW IN COLLECTION: [[Dvorak_2012_FixedParameterTractableAlgorithmsAbstractArgumentation]]
- [Creignou et al., 2014] - Complexity classifications for logic-based argumentation
- [Besnard and Hunter, 2008] - Elements of Argumentation (logic-based framework)
- [Dung, 1995] - On the acceptability of arguments (foundational abstract argumentation) -> NOW IN COLLECTION: [[Dung_1995_AcceptabilityArguments]]

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — cited as foundational framework; all DG reductions in this paper target Dung's standard semantics (stable, admissible, complete, preferred, semi-stable, stage)
- [[Dvorak_2012_FixedParameterTractableAlgorithmsAbstractArgumentation]] — cited as [Dvorak et al., 2012]; predecessor work on fixed-parameter tractable algorithms for abstract argumentation using treewidth

### New Leads (Not Yet in Collection)
- Lampis, Mengel, Mitsou (2018) — "QBF as an alternative to Courcelle's theorem" (SAT'18) — predecessor providing QBF reductions for admissible/preferred with treewidth preservation
- Fichte, Hecher, Meier (2019) — "Counting complexity for reasoning in abstract argumentation" (AAAI'19) — predecessor establishing dynamic programming algorithms and lower bounds
- Hecher (2020) — "Treewidth-aware reductions of normal ASP to SAT" (KR'20) — inspired the DG reduction concept
- Besnard, Hunter (2008) — "Elements of Argumentation" — defines the logic-based argumentation framework studied in Section 4
- Creignou, Egly, Schmidt (2014) — "Complexity classifications for logic-based argumentation" — baseline complexity results for ARG, ARG-Check, ARG-Rel

### Cited By (in Collection)
- [[Mahmood_2025_Structure-AwareEncodingsArgumentationProperties]] — cites this as [24], direct predecessor; extends DG reductions from treewidth to clique-width, generalizing from tree decompositions to k-expressions

### Conceptual Links (not citation-based)
- **Structural complexity for argumentation:**
  - [[Mahmood_2025_Structure-AwareEncodingsArgumentationProperties]] — **Strong.** Direct successor by same research group. Where this paper shows O(k) treewidth preservation with DG reductions, Mahmood 2025 achieves O(k) clique-width preservation with DDG reductions. The clique-width approach handles dense graphs where treewidth is large. Same semantics covered, same ETH lower bound methodology, same solution-bijection property for counting.
  - [[Dvorak_2012_FixedParameterTractableAlgorithmsAbstractArgumentation]] — **Strong.** Predecessor establishing fixed-parameter tractability for abstract argumentation via treewidth. This paper's DG reductions provide an alternative approach (compilation to SAT/QBF) vs Dvorak's direct dynamic programming algorithms.
- **Argumentation semantics computation:**
  - [[Dung_1995_AcceptabilityArguments]] — **Strong.** This paper provides the complexity-theoretic analysis of computing Dung's semantics when parameterized by treewidth. The stable/admissible/preferred/complete semantics defined by Dung are exactly what the DG reductions target.
  - [[Odekerken_2023_ArgumentationReasoningASPICIncompleteInformation]] — **Moderate.** Odekerken uses ASP for computing argumentation semantics. This paper's SAT/QBF reductions offer an alternative computational backend, and the treewidth analysis could inform when ASP vs SAT approaches are preferable.
