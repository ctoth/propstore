# Chunk #8 — Chapters 13 (Consonant approximation) and 14 (Consistent approximation)

**Book pages:** 517-594
**PDF idx:** 530-625

## Sections covered

- Ch 12 tail (proof of Theorem 67) *(p.515-516, PDF 530-531)*
- Ch 13 chapter opener and prior literature *(p.517-518)*
- Ch 13 The geometric approach to approximation *(p.518)*
- Ch 13 Chapter content + Summary of main results *(p.519-520)*
- Ch 13 Table 13.1 properties + chapter outline *(p.521)*
- Section 13.1 Geometry of outer consonant approximations in the consonant simplex *(p.521)*
  - 13.1.1 Geometry in the binary case *(p.522)*
  - 13.1.2 Convexity (Theorem 68) *(p.523)*
  - 13.1.3 Weak inclusion and mass reassignment (Lemma 14) *(p.524)*
  - 13.1.4 The polytopes of outer approximations (Theorem 69) *(p.524-525)*
  - 13.1.5 Maximal outer approximations (Theorem 70, Corollary 17) *(p.525)*
  - 13.1.6 Maximal outer approximations as lower chain measures (Definition 128, Theorem 71, Example 40) *(p.526-528)*
- Section 13.2 Geometric consonant approximation *(p.528-534)*
  - 13.2.1 Mass space representation *(p.529-530)*
  - 13.2.2 Approximation in the consonant complex (Definition 129) *(p.531-532)*
  - 13.2.3 Möbius inversion and norm preservation *(p.533-534)*
- Section 13.3 Consonant approximation in the mass space *(p.534-549)*
  - 13.3.1 Lp Minkowski results — Theorems 72, 73, 74 *(p.535-537)*
  - 13.3.2 Semantics of partial consonant approximations *(p.537-540)*
  - 13.3.3 Computability and admissibility of global solutions (Theorem 75) *(p.540-)*
  - 13.3.4 Relation to other approximations *(p.tbc)*
- Section 13.4 Consonant approximation in the belief space *(p.tbc)*
- Section 13.5 Belief-versus-mass-space approximations *(p.tbc)*
- Chapter 14 Consistent approximation *(p.581-594)*

## Chapter overview

Chapters 13 and 14 form the operational pair on geometric *approximation*. Chapter 13 takes a target belief function `Bel` and asks for the closest consonant belief function under L1 / L2 / L∞ norms, in the mass-space `M` and the belief-space `B` representations. Chapter 14 asks the same question for the larger class of *consistent* belief functions — those whose focal-element family has non-empty intersection.

The first half of Chapter 13 (Section 13.1) is geometric. The set `O^C[Bel]` of *outer* consonant approximations of `Bel` confined to the simplicial component `CO^C` of the consonant complex (one component per maximal chain `C = {B_1 ⊂ ... ⊂ B_n = Θ}`) is a convex polytope. Its vertices are indexed by *assignment functions* `B : 2^Θ → C` with `B(A) ⊇ A`. The Dubois–Prade contour-based vertex `Co^ρ` (associated to the singleton-permutation `ρ` that generates the chain `C_ρ`) is the *maximal* vertex with respect to weak inclusion. Section 13.1.6 reframes this maximal vertex as the *chain measure* of `Bel` on the chain `C` — `Bel_C(A) = max_{B ∈ C, B ⊆ A} Bel(B)` — which is a necessity measure on a finite frame.

The second half (Sections 13.2–13.5) is analytic. For each maximal chain there is a *partial* L1/L2/L∞ approximation problem, and a *global* problem selecting the best chain. Closed-form expressions are given for both representations:

- **L1, M:** unique partial solution per (N–2)-dim section (mass redistribution to a single chain element); a simplex of partial solutions in the full (N–1)-dim mass space, vertices reassigning all out-of-chain mass to one chain element. Globally selects chains that maximise total in-chain mass.
- **L2, M:** unique; equals the *barycentre* of the L1 simplex (equal redistribution of out-of-chain mass over chain elements). Globally selects chains minimising the sum of squared out-of-chain masses.
- **L∞, M:** simplex (or single point); admissibility may fail if some chain element has less mass than the maximum out-of-chain mass; barycentre coincides with L2; global optimum picks chains minimising max out-of-chain mass.
- **L1 / L2 / L∞ in B:** different formulas — L1 yields a polytope, L2 a point, L∞ a polytope; admissibility depends on the *contour* (plausibility-of-singletons) function. The L∞ B-space optimum picks chains maximising `Pl(A_1)`.

The chapter culminates in Table 13.1 (a one-page comparison) and in Section 13.5's qualitative comparison of mass-, belief-, and pignistic-based families of consonant approximations. Chapter 14 then runs the same program for the consistent class and compares belief-space vs mass-space results.

For propstore the operational deliverables are: (i) closed-form formulas for the closest consonant / consistent approximation of any stored belief function under each `Lp` norm; (ii) the *semantics* attached to each (mass-redistribution story for L1, equal-share story for L2, max-mass-outside story for L∞); (iii) admissibility checks (when the closed-form solution might assign negative mass and must be reported as improper or repaired); (iv) the choice of *which space* to project in (mass vs belief, complete vs reduced).

## Definitions

### Definition 128 (Lower chain measure) *(p.526)*

A monotone set function `ν : S → [0,1]` is called a *lower chain measure* if there exists a chain `C ⊂ S` (with `∅, Θ ∈ C`) such that `ν = (ν|_C)_*|_S`, i.e. `ν` is the inner extension of its own restriction to the chain. (`(μ)_*(A) = sup_{B ∈ S, B ⊂ A} μ(B)` is the inner extension; outer extension dual.)

### Definition 129 (Geometric consonant approximation) *(p.531)*

Given a belief function `Bel`, the consonant approximation of `Bel` induced by a distance function `d` in `M` (resp. `B`) is the belief function(s) `Co_{M/B,d}[m/Bel]` minimising the distance `d(m, CO_M)` (resp. `d(Bel, CO_B)`) between `m` (resp. `Bel`) and the consonant simplicial complex in `M` (resp. `B`):

$$
Co_{M,d}[m] = \arg\min_{m_{Co} \in CO_M} d(m, m_{Co}) \;\Big/\; Co_{B,d}[Bel] = \arg\min_{Co \in CO_B} d(Bel, Co)
$$
**(Eq. 13.12, p.531)**

### Definition (Outer consonant approximation, recalled from Ch 4) *(p.517-520)*

For a maximal chain `{A_1 ⊂ ... ⊂ A_n = Θ}` of focal elements,

$$
m'(A_i) = Bel(A_i) - Bel(A_{i-1})
$$
**(Eq. 13.1, p.518)** with `A_0 = ∅`.

### Definition 131 (Maximal outer consonant approximation Co^ρ) *(p.520, recalled)*

For permutation `ρ` of `Θ = {x_1, ..., x_n}` generating chain `C_ρ = {S_1^ρ, ..., S_n^ρ}` with `S_i^ρ = {x_{ρ(1)}, ..., x_{ρ(i)}}`, `Co^ρ` reassigns each focal element `A`'s mass to the smallest chain element `S_i^ρ ⊇ A`.

### Assignment function B *(p.524-525, Eq. 13.5)*

Map `B : 2^Θ → C, A ↦ B(A) ⊇ A`. Vertex consonant BF has BPA `m^B[Bel](B_i) = Σ_{A : B(A)=B_i} m(A)` (Eq. 13.4). For ternary frame there are `∏_{k=1}^{3} k^{2^{3-k}} = 1^4 · 2^2 · 3^1 = 12` such functions.

### Mass space (full and reduced) *(p.529, Eq. 13.10–13.11)*

$$
\mathbf{m} = \sum_{\emptyset \subsetneq A \subseteq \Theta} m(A) \mathbf{m}_A \in \mathbb{R}^{N-1} \quad\text{(full)}
$$
$$
\mathbf{m} = \sum_{\emptyset \subsetneq A \subseteq \Theta, A \neq \bar A} m(A) \mathbf{m}_A \quad\text{((N–2)-dim reduced)}
$$
**(Eqs. 13.10, 13.11, p.529)** where `m_A` is the categorical-BF mass vector for `A`, `N = 2^|Θ|`, and `Ā` is the focal element neglected by reduction.

## Theorems, propositions, lemmas

### Theorem 67 (Equality conditions both families — proof tail, Ch 12 boundary) *(p.515-516)*

Captured for boundary completeness only.

### Theorem 68 (Convexity of `O^C[Bel]`) *(p.523)*

For each maximal chain `C` of `2^Θ`, the set of outer consonant approximations of `Bel` belonging to component `CO^C` is **convex**. Proof: convex (not affine) combinations of weakly-included consonant BFs on the same chain remain weakly included and consonant on that chain.

### Lemma 14 (Mass-reassignment characterisation of weak inclusion) *(p.524)*

`Co` weakly included in `Bel` iff there exist coefficients `α_A^B ∈ [0,1]` with `Σ_{A ⊇ B} α_A^B = 1 ∀B` and `m_{Co}(A) = Σ_{B ⊆ A} α_A^B m(B)`.

### Theorem 69 (Polytope structure of `O^C[Bel]`) *(p.525)*

`O^C[Bel] = Cl(Co^B[Bel], ∀B)` — the convex closure of consonant BFs (Eq. 13.4) indexed by all admissible assignment functions (Eq. 13.5). The points (Eq. 13.4) are not always proper vertices.

### Theorem 70 (Co^ρ is a vertex) *(p.525)*

The outer consonant approximation Co^ρ generated by a permutation ρ of singletons is a vertex of `O^{C_ρ}[Bel]`.

### Corollary 17 (Co^ρ is the maximal-weak-inclusion vertex) *(p.525)*

The maximal outer consonant approximation with chain `C` of `Bel` is the vertex Co^ρ of `O^{C_ρ}[Bel]` whose ρ generates `C = C_ρ`. Argument: by Lemma 14 every outer consonant Co with chain `C` redistributes each focal `A`'s mass to chain supersets `B_i ⊇ A`. Co^ρ assigns it all to the smallest such; any other Co is weakly included in Co^ρ.

### Theorem 71 (Chain measure = maximal outer approximation) *(p.526)*

Define the chain measure of `Bel` on chain `C` by

$$
Bel_C(A) = \max_{B \in C, B \subseteq A} Bel(B)
$$
**(Eq. 13.7, p.526)**. Then `Bel_C` coincides with the vertex `Co^ρ` (Eq. 4.69) of `O^{C_ρ}[Bel]` whose permutation ρ generates `C = C_ρ`. *I.e. the chain measure built from `Bel` on `C` is the maximal outer consonant approximation on that chain.*

### Theorem 72 (L1 partial consonant approximation in the complete mass space `M`) *(p.535)*

Given `Bel : 2^Θ → [0,1]` with BPA `m`, the partial L1 consonant approximations of `Bel` with chain `C` in `M` are the consonant BFs `Co` with chain `C` such that `m_{Co}(A) ≥ m(A) ∀A ∈ C`. They form the simplex

$$
CO^C_{M,L_1}[m] = Cl\!\left(m^{\bar A}_{L_1}[m], \bar A \in C\right)
$$
**(Eq. 13.19, p.535)** with vertex BPAs

$$
m^{\bar A}_{L_1}[m](A) = \begin{cases} m(A) + \sum_{B \notin C} m(B) & A = \bar A \\ m(A) & A \in C, A \neq \bar A \end{cases}
$$
**(Eq. 13.20, p.535)** and barycentre

$$
Co^C_{M,L_1}[m](A) = m(A) + \frac{1}{n} \sum_{B \notin C} m(B) \quad \forall A \in C.
$$
**(Eq. 13.21, p.535)** Global L1 approximations are the union of those simplices over the chains maximising total in-chain mass `Σ_{A ∈ C} m(A)`. The partial L1 in the (N–2)-section `M \ Ā` with `Ā ∈ C` is *unique* with BPA (13.20).

### Theorem 73 (L2 partial consonant approximation in `M`) *(p.536)*

The partial L2 consonant approximation of `Bel` with chain `C` in `M` has mass assignment (13.21):

$$
Co^C_{M,L_2}[m] = Co^C_{M,L_1}[m]
$$
i.e. equals the barycentre of the L1 simplex. Global L2 approximations are the union of partial solutions over chains in `argmin_C Σ_{B ∉ C} (m(B))^2`. In the (N–2)-section: `Co^{C}_{M\Ā,L_2}[m] = Co^{C}_{M\Ā,L_1}[m]`. L1 and L2 *globals* generally fall on different simplicial components.

### Theorem 74 (L∞ partial consonant approximation in `M`) *(p.536)*

The partial L∞ consonant approximations of `Bel` with chain `C` in `M` form the simplex

$$
CO^C_{M,L_\infty}[m] = Cl\!\left(m^{\bar A}_{L_\infty}[m], \bar A \in C\right)
$$
**(Eq. 13.22, p.536)** with vertex BPAs

$$
m^{\bar A}_{L_\infty}[m](A) = \begin{cases}
m(A) + \max_{B \notin C} m(B), & A \in C, A \neq \bar A \\
m(\bar A) + \max_{B \notin C} m(B) + \big(\sum_{B \notin C} m(B) - n\,\max_{B \notin C} m(B)\big), & A = \bar A
\end{cases}
$$
**(Eq. 13.23, p.536)** whenever the BF being approximated satisfies

$$
\max_{B \notin C} m(B) \ge \frac{1}{n}\sum_{B \notin C} m(B)
$$
**(Eq. 13.24, p.537).** When (13.24) is violated the partial L∞ reduces to the L2 / barycentre `Co^C_{M,L_1}[m]`.

When (13.24) holds, global L∞ approximations associate with chains in `argmin_C max_{B ∉ C} m(B)` (Eq. 13.25). Otherwise globals correspond to chains in `argmin_C Σ_{B ∉ C} m(B)`. In the (N–2)-section excluding `Ā`, the partial L∞ approximations form the set `CO^C_{M\Ā,L_∞}[m]` with BPA satisfying

$$
m(A) - \max_{B \notin C} m(B) \le m_{Co}(A) \le m(A) + \max_{B \notin C} m(B), \quad \forall A \in C, A \neq \bar A
$$
**(Eq. 13.26, p.537).** Its barycentre `Co^C_{M\Ā,L_∞}[m] = Co^C_{M\Ā,L_2}[m] = m^{\bar A}_{L_1}[m]` — equal to the L1 vertex.

### Theorem 75 (Full mass space vs (N–2)-section L∞) *(p.540)*

Partial L∞ consonant approximations in the complete mass space `CO^C_{M,L_∞}[m]` are not necessarily partial L∞ approximations in the (N–2)-section `CO^C_{M\Ā,L_∞}[m]`. However, for all `Ā ∈ C` the two sets share the vertex (13.23). For `|Θ| = 3` the full-mass-space L∞ partial set is a *subset* of the (N–2)-section partial set for any choice of `Ā ∈ C`.

## Equations (running list)

- 13.1 (p.518): `m'(A_i) = Bel(A_i) − Bel(A_{i-1})`
- 13.2–13.3 (p.524): mass reassignment via `α_A^B`
- 13.4 (p.525): `m^B[Bel](B_i) = Σ_{B(A)=B_i} m(A)`
- 13.5 (p.525): assignment function `B : 2^Θ → C`
- 13.6 (p.526): inner extension `μ_*(A) = sup_{B ∈ S, B ⊂ A} μ(B)`
- 13.7 (p.526): chain measure `Bel_C(A) = max_{B ∈ C, B ⊆ A} Bel(B)`
- 13.8 (p.527): list of 12 ternary assignment-function vertex BPAs
- 13.9 (p.527): example BPA `m(x)=0.3, m(y)=0.5, m({x,y})=0.1, m(Θ)=0.1`
- 13.10–13.11 (p.529): mass-space embeddings (full and reduced)
- 13.12 (p.531): `Co_{M/B,d}[m/Bel]` definition
- 13.13 (p.531): Lp norms in `M` over `∅ ⊊ B ⊆ Θ`
- 13.14 (p.532): Lp norms in `B`
- 13.15 (p.533): partial-solution definitions `Co^C_{B,L_p}` and `Co^C_{M,L_p}`
- 13.16 (p.534): difference vector in full `M`
- 13.17 (p.534): difference vector in `M \ Ā` when `Ā ∈ C`
- 13.18 (p.534): difference vector in `M \ Ā` when `Ā ∉ C`
- 13.19 (p.535): L1 simplex `CO^C_{M,L_1}[m]`
- 13.20 (p.535): vertex BPA of L1 simplex
- 13.21 (p.535): L1 barycentre / equal-share BPA
- 13.22 (p.536): L∞ simplex `CO^C_{M,L_∞}[m]`
- 13.23 (p.536): L∞ vertex BPA
- 13.24 (p.537): admissibility condition `max_{B ∉ C} m(B) ≥ (1/n) Σ_{B ∉ C} m(B)`
- 13.25 (p.537): global L∞ chains `argmin_C max_{B ∉ C} m(B)`
- 13.26 (p.537): L∞ partial set in (N–2)-section
- 13.27 (p.537): summary of partial Lp approximations in full `M`
- 13.28 (p.538): summary of partial Lp approximations in (N–2)-section `M \ Ā`

## Geometric structures

- **Consonant complex `CO`** — union of simplicial components `CO^C`, one per maximal chain `C`. Each `CO^C = Cl(Bel_{A_1}, ..., Bel_{A_n})` in `B`, or `Cl(m_{A_1}, ..., m_{A_n})` in `M`.
- **Outer-approx polytope `O^C[Bel]`** — convex polytope inside `CO^C`; vertices indexed by assignment functions; maximal-(weak-inclusion) vertex is `Co^ρ`.
- **L1 partial simplex `CO^C_{M,L_1}[m]`** — simplex with vertices that reassign all out-of-chain mass to one chain element each; barycentre = L2 partial solution.
- **L∞ partial simplex `CO^C_{M,L_∞}[m]`** — simplex; admissible only when (13.24) holds; barycentre = L2.
- **Mass space `M`** — `R^{N-1}` (full) or `R^{N-2}` (reduced after omitting `Ā`).
- **Belief space `B`** — `R^{N-2}` after omitting `Bel(∅)` and `Bel(Θ)`.

## Worked examples

### Example 40 (Outer approximations on a ternary frame) *(p.526-528)*

Frame `Θ = {x,y,z}`; chain `C = {{x}, {x,y}, {x,y,z}}`. By Theorem 69 there are `1·4·1 = 12` assignment functions for this chain (counted as `∏_{k=1}^3 k^{2^{3-k}}`). The 12 candidate vertex BPAs are listed (Eq. 13.8). For example BPA `m(x)=0.3, m(y)=0.5, m({x,y})=0.1, m(Θ)=0.1` (Eq. 13.9), Fig. 13.3 shows polytope `O^C[Bel]` plotted on component `CO^C = Cl(Bel_x, Bel_{x,y}, Bel_Θ)`. Not all 12 candidates are proper vertices; the singleton-permutation vertex Co^B_1 is the maximal outer approximation (green square). Fig. 13.4 shows the partial-order graph of the 12 candidates by weak inclusion.

### Example 41 (Mass space in the binary case) *(p.530)*

`Θ_2 = {x,y}`; `m = [m(x), m(y)] ∈ R^2`; `m(Θ) = 1 - m(x) - m(y)`. Mass space `M_2` coincides with belief space `B_2`. `M_2 = B_2` is a triangle with vertices `Bel_Θ = m_Θ = [0,0]'`, `Bel_x = m_x = [1,0]'`, `Bel_y = m_y = [0,1]'`. Consonant BFs live on `CO^{x,Θ} ∪ CO^{y,Θ}`. Fig. 13.5 shows the unique L1=L2 consonant approximation (purple circle) and the segment of L∞ consonant approximations on `CO^{x,Θ}`.

### Example 42 (mass-space L∞ comparison full vs (N–2)-section) *(referred p.540)*

For `|Θ|=3`, the full-mass-space L∞ partial set is a subset of the (N–2)-section partial set; the inclusion is strict because (13.24) becomes `max ≥ Σ` which is impossible.

### Binary L2-distance illustration *(p.533)*

For `Bel = Bel_y` and consonant segment `Cl(Bel_x, Bel_Θ)`: in `B`, `||Bel_y - Bel_Θ||_{L_2} = 1 < ||Bel_y - Bel_x||_{L_2} = √2`, so `Bel_Θ` is closer to `Bel_y`. In `M` (R^3), `||m_y - m_Θ||_{L_2} = √2`, while `||m_y - (m_x+m_Θ)/2||_{L_2} = √3/2 < √2`. The L2 partial consonant approximation differs across spaces (`Bel_Θ` in B; `(m_x+m_Θ)/2` in M). Same effect for L1 and L∞.

## Figures of interest

- **Fig. 13.1 (p.523):** geometry of outer consonant approximations in `B_2` (binary belief space). Solid lines bound `O[Bel]`; segments `O^{x,Θ}[Bel], O^{y,Θ}[Bel]` are the components.
- **Fig. 13.2 (p.524):** convex combinations of two weakly-included BFs stay weakly included; affine combinations (dashed) can leave the region.
- **Fig. 13.3 (p.527):** ternary polytope `O^C[Bel]` for `C={{x},{x,y},Θ}` with example BPA (13.9); 12 candidate magenta squares; minimal/maximal weak-inclusion vertices Co^B_12 and Co^B_1.
- **Fig. 13.4 (p.529):** Hasse-style partial order over the 12 candidate consonant BFs (13.8) by weak inclusion.
- **Fig. 13.5 (p.530):** binary mass space `M_2 = B_2` triangle with consonant segments `CO^{x,Θ}, CO^{y,Θ}`, and the unique L1=L2 vs L∞ consonant approximations on `CO^{x,Θ}`.
- **Fig. 13.6 (p.532):** schematic of partial vs global Lp consonant approximations across simplicial components.
- **Fig. 13.7 (p.539):** diamond-shape graphic comparing partial Lp approximations in full mass space vs (N–2)-section. L1, L2 in section barycentres track L∞ vertices; L∞ section relations remain to be characterised.

## Algorithms / computational procedure

The chapter does not present numbered pseudocode but the implicit algorithm for the L_p partial consonant approximation in the mass space is:

1. **Input:** belief function `Bel` with BPA `m` on `2^Θ`; desired maximal chain `C = {B_1 ⊂ ... ⊂ B_n = Θ}`; norm choice `p ∈ {1, 2, ∞}`.
2. **Compute out-of-chain total** `S = Σ_{B ∉ C} m(B)` and (for L∞) `M = max_{B ∉ C} m(B)`.
3. **L1 case:** vertices `m^{Ā}_{L_1}` for each `Ā ∈ C` (Eq. 13.20). Barycentre = L2 (Eq. 13.21).
4. **L2 case:** `m_{Co}(A) = m(A) + S/n` for `A ∈ C` (Eq. 13.21).
5. **L∞ case:** if `M ≥ S/n`, vertices given by Eq. 13.23; else solution = L2 barycentre.
6. **Global step:** repeat over all chains and select the chain minimising the global criterion: `argmin_C Σ_{B ∉ C} m(B)` for L1; `argmin_C Σ_{B ∉ C} (m(B))^2` for L2; `argmin_C max_{B ∉ C} m(B)` for L∞ (Eqs at p.540).
7. **Admissibility:** L1 always admissible; L2 always admissible; L∞ admissible iff `min_{A ∈ C} m(A) ≥ max_{B ∉ C} m(B)` (else partial-set may include negative-mass points and require pruning).

## Parameters / quantities

| Name | Symbol | Domain | Page | Notes |
|------|--------|--------|------|-------|
| Frame size | n = \|Θ\| | int ≥ 1 | p.518 | binary, ternary worked |
| Power-set size | N = 2^n | int | p.518 | mass space dim N–1 (full) or N–2 (reduced) |
| Maximal chain | C = {B_1 ⊂ ... ⊂ B_n = Θ} | length-n chain | p.518 | one per permutation of singletons |
| Singleton-permutation | ρ | S_n | p.520 | n! such, generates Co^ρ |
| Chain-element count | n | int | p.535 | denominator in L2/L∞ barycentre |
| Out-of-chain mass | S = Σ_{B ∉ C} m(B) | [0,1] | p.535 | drives partial solutions |
| Max out-of-chain mass | M = max_{B ∉ C} m(B) | [0,1] | p.536 | drives L∞ admissibility (13.24) |
| Neglected component | Ā ∈ C | element of C | p.534 | for (N–2)-section reduction |

## Section 13.3.3 / 13.3.4 admissibility and other approximations

### Admissibility of partial / global solutions in M *(p.541)*

- L1, L2 partial solutions: always admissible in both representations.
- L∞ in full mass space: even global solutions need not have all admissible vertices (13.23). The condition `Σ_{B ∉ C} m(B) − n · max_{B ∉ C} m(B) ≤ 0` (which holds by (13.24)) makes `m^{Ā}_{L_∞}[m](Ā)` potentially negative.
- L∞ in `M\Ā` (Eq. 13.26): the partial set is entirely admissible iff

$$
\min_{A \in C, A \neq \bar A} m(A) \ge \max_{B \notin C} m(B)
$$
**(Eq. 13.29, p.541).** Counter-example: a `Bel` with no cardinality-1 focal elements but several cardinality-2 ones — minimising `max_{B ∉ C} m(B)` does not imply (13.29).

### Computational complexity *(p.541)*

- L1, L2 globals: search over chains maximising in-chain (or squared) mass — must inspect all `n!` chains.
- L∞ globals: `O(2^n)` instead of `O(n!)` because a single pass over focal elements identifies max-mass focal elements; chains avoiding them are optimal. Trade-off: L∞ globals are spread over many simplicial components and thus less informative.

### Definition 130 (Isopignistic consonant approximation) *(p.541)*

`Co_{iso}[Bel]` is the unique consonant BF with `BetP[Co_{iso}[Bel]] = BetP[Bel]`. Its contour is

$$
pl_{Co_{iso}[Bel]}(x) = \sum_{x' \in \Theta} \min\{BetP[Bel](x), BetP[Bel](x')\}
$$
**(Eq. 13.30, p.541).** Mass values:

$$
m_{Co}(A_i) = \begin{cases} pl(x_i) - pl(x_{i+1}) & i = 1,...,n-1 \\ pl(x_n) & i = n \end{cases}
$$
**(Eq. 13.31, p.542)** with singletons sorted by plausibility. The mass is given by `m_{Co_{iso}}(A_i) = i·(BetP(x_i) − BetP(x_{i+1}))` for `i = 1..n-1`, `n·BetP(x_n)` for `i=n` (Eq. 13.32). Complexity: `O(n log n)` for sorting plus `O(n · 2^n)` for `BetP`.

### Definition 131 (Contour-based consonant approximation Co_con) *(p.542)*

For chain `C = {A_1 ⊂ ... ⊂ A_n}`,

$$
m_{Co_{con}[Bel]}(A_i) = \begin{cases} 1 - pl(x_2) & i = 1 \\ pl(x_i) - pl(x_{i+1}) & i = 2,...,n-1 \\ pl(x_n) & i = n \end{cases}
$$
**(Eq. 13.33, p.542).** Uses the contour function as a possibility distribution after replacing the maximal-element plausibility with 1. Sorting cost `O(n log n)`; `pl(x)` cost `O(n · 2^n)`.

### Theorem 76 (Outer / L1 intersection) *(p.543)*

The set `CO^C_{M,L_1}[m]` of partial L1 consonant approximations and the set `O^C[Bel]` of partial outer consonant approximations with the same chain have **non-empty intersection**, containing at least the convex closure of the candidate vertices of `O^C[Bel]` whose assignment functions `B(A_i) = A_i ∀i = 1,...,n`.

In particular `Co^C_{max}[Bel]` (Eq. 4.69) and the trivial-redistribution-to-Θ vertex

$$
Co^C_{M\setminus\Theta, L_{1/2}}[m] : m_{Co}(A) = m(A) \;(A \in C, A \neq \Theta), \quad m_{Co}(\Theta) = m(\Theta) + \sum_{B \notin C} m(B)
$$
**(Eq. 13.34, p.543)** belong to both partial outer and L1, M consonant approximations.

### Theorem 77 (No L∞ analogue) *(p.543)*

The intersection `O^C[Bel] ∩ CO^C_{M,L_∞}[Bel]` may be **empty**. In particular `Co^C_{max}[Bel]` is not necessarily an L∞, M approximation of Bel.

### Example 42 — ternary mass-space approximations *(p.543-544, Fig 13.8)*

Frame `Θ = {x,y,z}`, chain `C = {{x} ⊂ {x,y} ⊂ Θ}`, BPA `m(x)=0.2, m(y)=0.3, m({x,z})=0.5` (Eq. 13.35). Six candidate outer-approximation vertices listed (Eq. 13.36). L1 partial set is the magenta triangle; L2/M is the light-blue square (= barycentre of L1); L∞ is the blue triangle. Outer approximation polytope shown in dashed yellow; isopignistic in orange diamond. For this BPA, isopignistic `m_{iso} = [0.15, 0.1, 0.75]'` is admissible; contour-based `m_{con} = [0.7, -0.2, 0.5]'` is *not* admissible (negative middle mass). Pignistic values `BetP[Bel] = (0.45, 0.3, 0.25)` for `(x,y,z)`. The isopignistic chain happens to coincide with `{{x},{x,y},Θ}`. The contour-based approximation is not admissible because the singletons have a different plausibility ordering. The chapter notes that the isopignistic approximation is also an outer approximation in this example (but not in general).

## Section 13.4 Consonant approximation in the belief space

### Lemma 15 (Difference vector in B) *(p.545)*

Given `Bel` and consonant `Co` with chain `C = {A_1 ⊂ ... ⊂ A_n}`, the difference between corresponding belief-space vectors is

$$
Bel - Co = \sum_{A \not\supseteq A_1} Bel(A)\mathbf{x}_A + \sum_{i=1}^{n-1} \sum_{A \supseteq A_i, A \not\supseteq A_{i+1}} \mathbf{x}_A \left[\gamma(A_i) + Bel(A) - \sum_{j=1}^{i} m(A_j)\right]
$$
**(Eq. 13.37, p.545)** where `γ(A) = Σ_{B ⊆ A, B ∈ C} (m(B) − m_{Co}(B))` and `{x_A}` is the orthonormal reference frame in `B`.

### Theorem 78 (L1 partial consonant approximations in B) *(p.546)*

The partial L1 consonant approximations form the convex closure

$$
Cl\!\left([Bel^1, Bel^2 - Bel^1, ..., Bel^i - Bel^{i-1}, ..., 1 - Bel^{n-1}]', \; Bel^i \in \{\gamma^i_{int1}, \gamma^i_{int2}\} \forall i = 1,...,n-1\right)
$$
**(Eq. 13.38, p.546)** where `γ^i_{int1}, γ^i_{int2}` are the innermost (median) elements of the *list of belief values*

$$
\mathcal{L}_i = \{Bel(A), A \supseteq A_i, A \not\supseteq A_{i+1}\}
$$
**(Eq. 13.39, p.546).** In particular `Bel^{n-1} = γ^{n-1}_{int1} = γ^{n-1}_{int2} = Bel(A_{n-1})`. Barycentre BPA of partial L1 set:

$$
m_{Co^C_{B,L_1}[Bel]} = \left[\frac{γ^1_{int1}+γ^1_{int2}}{2}, \frac{γ^2_{int1}+γ^2_{int2}}{2} - \frac{γ^1_{int1}+γ^1_{int2}}{2}, ..., 1 - Bel(A_{n-1})\right]'
$$
**(Eq. 13.40, p.546).**

### Theorem 79 (Global L1 in B) *(p.546)*

Global L1 consonant approximations in `B` live in the union of partial approximations associated with maximal chains maximising `Σ_i Σ_{Bel(A) ∈ L_i, Bel(A) ≤ γ_{int1}} Bel(A)` (Eq. 13.41).

### Theorem 80 (Partial L2 in B) *(p.547)*

Unique. Mass assignment

$$
m_{Co^C_{B,L_2}[Bel]}(A_i) = ave(\mathcal{L}_i) - ave(\mathcal{L}_{i-1}) \quad \forall i = 1,...,n
$$
**(Eq. 13.44, p.547)** with `L_0 := {0}` and

$$
ave(\mathcal{L}_i) = \frac{1}{2^{|A^c_{i+1}|}} \sum_{A \supseteq A_i, A \not\supseteq A_{i+1}} Bel(A)
$$
**(Eq. 13.45, p.547).** Footnote: global L2 in `B` is computationally involved and left for future work.

### Theorem 81 (Partial L∞ in B is a polytope with `2^{n-1}` vertices) *(p.547-548)*

The partial L∞ consonant approximations in B with chain `C` have mass vectors in the convex closure (Eq. 13.46) of `2^{n-1}` vertices

$$
Bel^i \in \left\{\frac{Bel(A_i) + Bel(\{x_{i+1}\}^c)}{2} \pm Bel(A^c_1)\right\}.
$$
The barycentre `Co^C_{B,L_∞}[Bel]` has BPA

$$
m_{Co^C_{B,L_∞}[Bel]}(A_i) = \begin{cases}
\frac{Bel(A_1) + Bel(\{x_2\}^c)}{2} & i = 1 \\
\frac{Bel(A_i) - Bel(A_{i-1})}{2} + \frac{Pl(\{x_i\}) - Pl(\{x_{i+1}\})}{2} & i = 2,...,n-1 \\
1 - Bel(A_{n-1}) & i = n
\end{cases}
$$
**(Eq. 13.47, p.548).** The size of the partial polytope (13.46) is a function of `Pl({x_1}) = 1 − Bel(A^c_1)` only — it shrinks to a point when the innermost focal element `A_1 = {x_1}` has plausibility 1 (i.e., `Bel` is consistent and `A_1` is in its core). **Identity** `m_{Co} = (m_{Co_max} + m_{Co_con})/2`: the L∞ barycentre is the average of the maximal outer and contour-based approximations.

### Theorem 82 (Global L∞ in B) *(p.548)*

Global L∞ consonant approximations in `B` are the union of partial approximations with chains whose smallest focal element is the maximum-plausibility singleton:

$$
CO_{B,L_\infty}[Bel] = \bigcup_{C : A_1 = \{\arg\max_{x \in \Theta} Pl(\{x\})\}} CO^C_{B,L_\infty}[Bel]
$$
**(p.548).** Argument: the L∞ partial distance equals `Bel(A^c_1) = 1 - Pl(A_1)` (Eq. 13.73 in proof of Th 81), so we minimise `1 - Pl(A_1)`, i.e. maximise `Pl(A_1)`.

### Section 13.4.4 Approximations as generalised maximal outer *(p.549-550)*

All five approximations (`Co_max`, `Co_con`, L1, L2, L∞) can be written as differences of representative values from the chain-induced lists:

$$
\begin{aligned}
m_{Co^C_{max}[Bel]}(A_i) &= \min(\mathcal{L}_i) - \min(\mathcal{L}_{i-1}) \\
m_{Co^C_{con}[Bel]}(A_i) &= \max(\mathcal{L}_i) - \max(\mathcal{L}_{i-1}) \\
m_{Co^C_{B,L_1}[Bel]}(A_i) &= \frac{int_1(\mathcal{L}_i) + int_2(\mathcal{L}_i)}{2} - \frac{int_1(\mathcal{L}_{i-1}) + int_2(\mathcal{L}_{i-1})}{2} \\
m_{Co^C_{B,L_2}[Bel]}(A_i) &= ave(\mathcal{L}_i) - ave(\mathcal{L}_{i-1}) \\
m_{Co^C_{B,L_\infty}[Bel]}(A_i) &= \frac{\max(\mathcal{L}_i)+\min(\mathcal{L}_i)}{2} - \frac{\max(\mathcal{L}_{i-1})+\min(\mathcal{L}_{i-1})}{2}
\end{aligned}
$$
**(Eq. 13.48, p.549).** Each L1 vertex picks one innermost element per list; each L∞ vertex picks one outermost (max or min) per list. Maximal outer = min, contour-based = max; L2 = average; L1 = average of innermost pair; L∞ = average of outermost pair.

#### Interpretation

If `2^Θ` were totally ordered, each `L_i` would have a single element and all five Lp approximations would collapse to `Co_max`. The variety arises from `2^Θ`'s partial order. The list `L_i` has `2^{n-(i+1)}` elements (with `|L_0| = 1`).

#### Relations

- Barycentre of L∞ = average of `Co_max` and `Co_con`.
- For `i ≥ n-2` or `i = 0` (i.e., `|L_i| ≤ 2`): `ave(L_i) = (max+min)/2 = (int1+int2)/2`. Hence the last two components of L1 barycentre, L2, L∞ barycentre coincide.
- For `|Θ| ≤ 3`: `Co^C_{B,L_1} = Co^C_{B,L_2} = Co^C_{B,L_∞}` exactly.
- The last component of all approximations is identical: `m(A_n) = 1 - Bel(A_{n-1})`.

#### Admissibility

All Lp B-space approximations are differences of vectors of positive values. They are admissible iff the underlying list-statistic vector is monotonic over the chain. Sufficient conditions can be derived from `L_i` structure. For `Co^C_{max}` and `Co^C_{con}`, since `min(L_{i-1}) = Bel(A_{i-1}) ≤ Bel(A_i) = min(L_i)` (and similarly for max), they are **always** admissible.

For `Co_con` (contour-based), since `max(L_i) = Bel(A_i + A^c_{i+1}) = Bel(\{x_{i+1}\}^c) = 1 - Pl(x_{i+1})`, admissibility reduces to `Pl(x_i) \ge Pl(x_{i+1})`, i.e. the chain is generated by singletons sorted by plausibility *(p.551)*. The L∞ barycentre BPA

$$
m_{Co^C_{B,L_\infty}[Bel]}(A_i) = \frac{\min(\mathcal{L}_i) - \min(\mathcal{L}_{i-1})}{2} + \frac{\min(\mathcal{L}_i) - \min(\mathcal{L}_{i-1})}{2}
$$

is admissible on the same plausibility-sorted chain(s) *(p.551)*.

### Example 43 (Ternary, belief-space approximations) *(p.551-553, Fig. 13.9)*

Same ternary setting as Example 42. Lists for chain `C = {{x} ⊂ {x,y} ⊂ Θ}`:

- `L_1 = {Bel(x), Bel({x,z})}`,
- `L_2 = {Bel({x,y})}`.

So `min(L_1)=int_1(L_1)=Bel(x)`, `max(L_1)=int_2(L_1)=Bel({x,z})`, `ave(L_1)=(Bel(x)+Bel({x,z}))/2`. `L_2` is a singleton: `min=int_1=int_2=max=ave=Bel({x,y})`.

**L1 partial set in B (Eq. 13.49, p.552)** is a *segment* with two vertex BPAs

$$
[Bel(x), Bel(\{x,y\}) - Bel(x), 1 - Bel(\{x,y\})]', \quad
[Bel(\{x,z\}), Bel(\{x,y\}) - Bel(\{x,z\}), 1 - Bel(\{x,y\})]'
$$

which **coincide with `Co_max` and `Co_con` respectively**. Set "is not entirely admissible, not even in the special ternary case" — counter-example to admissibility hopes.

**L2 partial in B (Eq. 13.50, p.552)** is unique and equals the L∞ barycentre:

$$
m_{Co_{B,L_2}[Bel]} = m_{Co_{B,L_\infty}[Bel]} = \left[\tfrac{Bel(x)+Bel(\{x,z\})}{2}, \; Bel(\{x,y\}) - \tfrac{Bel(x)+Bel(\{x,z\})}{2}, \; 1 - Bel(\{x,y\})\right]'
$$

(coincidence of L2 and L∞ barycentres holds in the ternary case, *not* in general).

**L∞ partial set** has 4 vertices in B (listed on p.553), which are not all admissible (light-blue quadrangle in Fig. 13.9).

## Section 13.5 — Belief versus mass space approximations *(p.553-556)*

### Six summary observations *(p.553-554)*

1. `L_p` consonant approximations in `M` are mass-redistribution processes: out-of-chain mass is reassigned to chain elements.
2. Their relationships with classical outer approximations and with pignistic-based approximations are weak.
3. The different `L_p` approximations in `M` are characterised by natural geometric relations.
4. Consonant approximation in `B` is inherently linked to the *list-of-belief-values* `L_i` of focal elements "intermediate" between consecutive chain elements.
5. The contour-based approximation, together with the `L_p` approximations in `B`, can be seen as distinct generalisations of the maximal outer approximation, induced by the partial-order nature of `2^Θ`.
6. In `M`, the L1 and L2 partial approximations are always admissible; some others (notably L∞) are not. In `B`, all partial approximations are differences of shifted copies of the same positive vector but admissibility is not guaranteed for arbitrary chains.

Table 13.1 summarises behaviour by *multiplicity* (point/simplex/polytope), *admissibility* (always/ may fail), and *global* solution (which chains are selected).

### Section 13.5.1 Links between approximations in M and B *(p.554-555)*

Approximations in `M` and `B` do not coincide: Möbius inversion preserves neither `L_p` norms nor the ordering induced by them (counter-examples in Section 13.2.3).

**Three conjectures** suggested by the ternary example (Fig. 13.9) — *all three are false in general*:

1. The L2 partial in B is one of the L1 partial in M.
2. The L2 partial in B is one of the L∞ partial in M, possibly on the boundary of (13.22).
3. The L1 partial in B is an element of (13.22).

The counter-example uses

$$
m^C_{B,L_2}[Bel](A_i) = ave(\mathcal{L}_i) - ave(\mathcal{L}_{i-1}) = \sum_{B \ni x_i, B \not\ni x_{i+1}} \frac{m(B)}{2^{|B \cap A^c_{i+1}|}} - \sum_{B \ni x_{i+1}, B \not\ni x_i} \frac{m(B)}{2^{|B \cap A^c_i|}}
$$
**(Eq. 13.51, p.554).**

For conjecture 1, `m^C_{B,L_2}[Bel](A_i) - m(A_i)` is not guaranteed positive (Theorem 72 needs ≥ 0 for L1 in M).

For conjecture 2, the L∞ M partial set has the constraints

$$
\begin{cases}
m_{Co}(A) - m(A) \le \max_{B \notin C} m(B) & A \in C, A \neq \bar A, \\
\sum_{A \in C, A \neq \bar A} (m_{Co}(A) - m(A)) \ge \sum_{B \notin C} m(B) - \max_{B \notin C} m(B).
\end{cases}
$$
**(Eq. 13.52, p.555).** A `Bel` for which `m(B) = 0` for `B ∋ x_{i+1}, B \not\ni x_i` produces an L2-B value violating this — counter-example.

For conjecture 3, every L1-B vertex has `m_Co(A_1) ∈ {Bel(A_1 ∪ C) : C ⊆ A^c_2}`. If the argmax-mass focal is one of these subsets `B ⊆ A_1 ∪ C` with `C ⊆ A^c_2`, `B ≠ A_1`, the first constraint of (13.52) fails for `A = A_1`. Hence empty intersection.

**Conclusion:** "not only are approximations in `M` and `B` distinct, owing to the properties of Möbius inversion, but they are also not related in any apparent way."

### Section 13.5.2 Three families of consonant approximations *(p.555-556)*

- **Mass-space family** (`L_p`-in-`M`): different mass-redistribution processes, all built on reassigning out-of-chain mass to chain elements.
- **Belief-space family** (`Co_max`, `Co_con`, `L_p`-in-`B`): all are *generalised maximal outer approximations* in the sense of Eq. 13.48, picking different statistics (min / max / mid-pair / mean / outermost-pair) over the lists `L_i`.
- **Isopignistic family** (`Co_iso`): TBM-derived, "completely unrelated to approximations in either the mass or the belief space".

These three families "have fundamentally different rationales: which approach to be used will therefore vary according to the framework chosen, and the problem at hand."

---

# Chapter 14 — Consistent approximation

**Book pages:** 575-592.

## Chapter overview *(p.575-577)*

Belief functions can encode mutually conflicting evidence (fusion of inconsistent expert opinions, corrupted measurements). Acting on inconsistent BFs may mislead, motivating a *consistent* approximation: project `Bel` to the region `CS` of consistent belief functions. Consistent BFs are characterised by non-empty intersection of focal elements, equivalently `max_{x ∈ Θ} pl(x) = 1`, equivalently a *principal ultrafilter* core `{A ⊇ {x}}` for some `x`. Consistent BFs are the natural counterpart to consistent knowledge bases in classical logic; consistent transformations parallel the role of paraconsistent reasoning in inconsistent KBs.

The consistent transformation problem is

$$
Cs[Bel] = \arg\min_{Cs \in \mathcal{CS}} dist(Bel, Cs)
$$
**(Eq. 14.1, p.575).**

The chapter solves it for `L_1, L_2, L_∞` Minkowski distances in both the mass space `M` and the belief space `B`. The `L_∞` norm is naturally tied to consistency because `CS = {Bel : max_x pl(x) = 1}` and `Pos(A) = max_{x ∈ A} Pos(x)`.

The consistent simplicial complex decomposes by element of the frame:

$$
\mathcal{CS}_\mathcal{B} = \bigcup_{x \in \Theta} \mathcal{CS}_\mathcal{B}^{\{A \ni x\}} = \bigcup_{x \in \Theta} Cl(Bel_A, A \ni x), \quad
\mathcal{CS}_\mathcal{M} = \bigcup_{x \in \Theta} Cl(m_A, A \ni x).
$$

Each maximal simplex `CS^{A∋x}` is the convex closure of categorical BFs whose conjunctive core contains `x`.

The `L_p` partial consistent transformations focused on `x` are

$$
Cs^x_{L_p}[Bel] = \arg\min_{Cs \in \mathcal{CS}_\mathcal{B}^{\{A \ni x\}}} \|Bel - Cs\|_{L_p}, \quad
Cs^x_{L_p}[m] = \arg\min_{m_{Cs} \in \mathcal{CS}_\mathcal{M}^{\{A \ni x\}}} \|m - m_{Cs}\|_{L_p}.
$$
**(Eq. 14.2, p.577).**

Global approximations are partial approximations at minimum distance from `Bel`.

## Section 14.1 The Minkowski consistent approximation problem *(p.577)*

Recalls (14.1) and (14.2). Notes that "as in the consonant case (see Section 13.2.2)" the problem decomposes into one partial problem per maximal simplex, then a global selection step.

## Section 14.2 Consistent approximation in the mass space *(p.578-580)*

### Difference vector and norms *(p.578)*

Using the notation `m_{Cs} = Σ_{B ⊇ {x}, B ≠ Θ} m_{Cs}(B) m_B`, `m = Σ_{B ⊊ Θ} m(B) m_B` (in `R^{N-2}`, i.e., `m(Θ)` not included by normalisation), the difference vector is

$$
m - m_{Cs} = \sum_{B \supseteq \{x\}, B \neq \Theta} \big(m(B) - m_{Cs}(B)\big) m_B + \sum_{B \not\supseteq \{x\}} m(B) m_B
$$
**(Eq. 14.3, p.578)** with norms

$$
\begin{aligned}
\|m - m_{Cs}\|^M_{L_1} &= \sum_{B \supseteq \{x\}, B \neq \Theta} |m(B) - m_{Cs}(B)| + \sum_{B \not\supseteq \{x\}} |m(B)|, \\
\|m - m_{Cs}\|^M_{L_2} &= \sqrt{\sum_{B \supseteq \{x\}, B \neq \Theta} |m(B) - m_{Cs}(B)|^2 + \sum_{B \not\supseteq \{x\}} |m(B)|^2}, \\
\|m - m_{Cs}\|^M_{L_\infty} &= \max\!\Big\{\max_{B \supseteq \{x\}, B \neq \Theta} |m(B) - m_{Cs}(B)|,\; \max_{B \not\supseteq \{x\}} |m(B)|\Big\}.
\end{aligned}
$$
**(Eq. 14.4, p.578).**

### 14.2.1 L1 approximation — Theorem 83 *(p.578-579)*

Introduce `β(B) := m(B) - m_Cs(B)`. Then

$$
\|m - m_{Cs}\|^M_{L_1} = \sum_{B \supseteq \{x\}, B \neq \Theta} |β(B)| + \sum_{B \not\supseteq \{x\}} |m(B)|
$$
**(Eq. 14.5, p.578)** which is minimised by `β(B) = 0` for all `B ⊇ {x}, B ≠ Θ`.

#### Theorem 83 (Unique partial L1 in M) *(p.578)*

Given `Bel : 2^Θ → [0,1]` and `x ∈ Θ`, the unique L1 consistent approximation `Cs^x_{L_1, M}[m]` in `M` with conjunctive core containing `x` has BPA

$$
m_{Cs^x_{L_1, M}[m]}(B) = \begin{cases}
m(B) & \forall B \supseteq \{x\}, B \neq \Theta, \\
m(\Theta) + Bel(\{x\}^c) & B = \Theta.
\end{cases}
$$
**(Eq. 14.6, p.578).** *All mass of subsets not in the principal ultrafilter `{B ⊇ {x}}` is reassigned to `Θ`.*

#### Global L1 in M *(p.579)*

Partial focused on `x` has L1 distance `Bel({x}^c) = Σ_{B \not\supseteq \{x\}} m(B)` from `m`. Global approximation is the union of partials associated with maximum-plausibility singletons:

$$
\hat{x} = \arg\min_x Bel(\{x\}^c) = \arg\max_x Pl(x).
$$

### 14.2.2 L∞ approximation — Theorem 84 *(p.579)*

Norm

$$
\|m - m_{Cs}\|^M_{L_\infty} = \max\!\Big\{\max_{B \supseteq \{x\}, B \neq \Theta} |β(B)|, \; \max_{B \not\supseteq \{x\}} m(B)\Big\}
$$

is minimised when `|β(B)| ≤ max_{B \not\supseteq \{x\}} m(B)`.

#### Theorem 84 (Partial L∞ in M, polytope) *(p.579)*

Given `Bel` and `x ∈ Θ`, the L∞ consistent approximations in `M` with core `∋ x` are those whose mass values on subsets `B ⊋ {x}, B ≠ Θ` differ from the original by at most the maximum mass of subsets not in the ultrafilter:

$$
m(B) - \max_{C \not\supseteq \{x\}} m(C) \le m_{Cs^x_{L_\infty, M}[m]}(B) \le m(B) + \max_{C \not\supseteq \{x\}} m(C), \quad \forall B \supseteq \{x\}, B \neq \Theta.
$$
**(Eq. 14.7, p.579).** Set may include pseudo-belief functions (negative mass) — admissibility is not guaranteed.

#### Global L∞ in M *(p.579)*

$$
\hat{x} = \arg\min_x \max_{B \not\supseteq \{x\}} m(B).
$$

The barycentre of the L∞ rectangle (14.7) coincides with the L1 partial (14.6) — equal redistribution to `Θ` is "the centre" of the polytope.

### 14.2.3 L2 approximation — Theorem 85 *(p.580-581)*

Orthogonality of `m - m_Cs` to the subspace `CS^{A∋x}` whose generators are `m_B - m_x` for `B ⊋ {x}`:

$$
\langle m - m_{Cs}, m_B - m_x \rangle = 0
$$

reduces (in the `R^{N-2}` representation) to

$$
\langle m - m_{Cs}, m_B - m_x \rangle = \begin{cases}
β(B) - β(\{x\}) = 0 & \forall B \supsetneq \{x\}, B \neq \Theta, \\
-β(x) = 0 & B = \Theta.
\end{cases}
$$
**(Eq. 14.8, p.580).**

In the `R^{N-1}` representation `m = Σ_{∅ ⊊ B ⊆ Θ} m(B) m_B` (Eq. 14.9, p.580), the orthogonality condition reads

$$
\langle m - m_{Cs}, m_B - m_x \rangle = β(B) - β(\{x\}) = 0 \quad \forall B \supsetneq \{x\}.
$$
**(Eq. 14.10, p.580).**

#### Theorem 85 (Unique partial L2 in M) *(p.580)*

In `R^{N-2}`, the partial L2 consistent approximation with core ∋ `x` *coincides with the partial L1*: `Cs^x_{L_2, M}[m] = Cs^x_{L_1, M}[m]`.

In `R^{N-1}`, the partial L2 has a different solution: redistribute equally to all `2^{|Θ|-1}` elements of the ultrafilter:

$$
m_{Cs^x_{L_2, M}[m]}(B) = m(B) + \frac{Bel(\{x\}^c)}{2^{|\Theta|-1}}, \quad \forall B \supseteq \{x\}.
$$
**(Eq. 14.11, p.580).**

#### Global L2 in M *(p.581)*

$$
\hat{x} = \arg\min_x \sum_{B \not\supseteq \{x\}} (m(B))^2.
$$

In `R^{N-2}` representation L1 and L2 partials coincide but globals can fall on different consistent components.

## Section 14.3 Consistent approximation in the belief space *(p.581-586)*

### 14.3.1 L1/L2 approximations *(p.581-583)*

Notation: `Cs = Σ_{B ⊇ {x}} m_Cs(B) Bel_B`, `Bel = Σ_{B ⊊ Θ} m(B) Bel_B`.

**L2 case.** Orthogonality of `Bel - Cs` to the generators `Bel_B - Bel_Θ = Bel_B` for `{x} ⊆ B ⊊ Θ`:

$$
\langle Bel - Cs, Bel_B \rangle = 0 \;\;\Leftrightarrow\;\; \sum_{A \supseteq \{x\}} β(A)\langle Bel_A, Bel_B \rangle + \sum_{A \not\supseteq \{x\}} m(A)\langle Bel_A, Bel_B \rangle = 0.
$$
**(Eq. 14.12, p.581).**

**L1 case.**

$$
\sum_{B \subseteq A, B \supseteq \{x\}} β(B) + \sum_{B \subseteq A, B \not\supseteq \{x\}} m(B) = 0 \quad \forall A : \{x\} \subseteq A \subsetneq \Theta.
$$
**(Eq. 14.13, p.582).**

#### Example 44: ternary linear systems coincide *(p.582)*

For `Θ = {x, y, z}` the L1 system is

$$
\begin{cases}
3β(x) + β(\{x,y\}) + β(\{x,z\}) + m(y) + m(z) = 0, \\
β(x) + β(\{x,y\}) + m(y) = 0, \\
β(x) + β(\{x,z\}) + m(z) = 0,
\end{cases}
$$

and the L2 system can be recovered from the L1 system by the row transformation `e_1 \to e_1 - e_2 - e_3` (Eq. 14.14, p.582). Same solution.

#### Lemma 16 *(p.582)*

$$
\sum_{B \supseteq A} \langle Bel_B, Bel_C \rangle (-1)^{|B \setminus A|} = \begin{cases} 1 & C \subseteq A, \\ 0 & \text{otherwise}. \end{cases}
$$

#### Corollary 18 (L2 system reduces to L1 system) *(p.582)*

The linear system (14.12) reduces to (14.13) via

$$
row_A \mapsto \sum_{B \supseteq A} row_B (-1)^{|B \setminus A|}.
$$
**(Eq. 14.15, p.582).**

#### Theorem 86 (Solution of the linear system) *(p.583)*

The unique solution of (14.13) is

$$
β(A) = -m(A \setminus \{x\}) \quad \forall A : \{x\} \subseteq A \subsetneq \Theta.
$$

#### Corollary 19 (L1 = L2 partial in B = "focused consistent transformation") *(p.583)*

For all `x ∈ Θ` and all `A ⊇ {x}, A ⊆ Θ`,

$$
m_{Cs^x_{L_1}[Bel]}(A) = m_{Cs^x_{L_2}[Bel]}(A) = m(A) + m(A \setminus \{x\}).
$$

Interpretation: each event `B ⊇ {x}` receives the original mass plus the mass of `B \ {x}`. There are exactly two events whose mapping `B ↦ B ∪ {x}` lands on `A`: `A` itself and `A \ {x}`. So the partial L1/L2 in B is the *focused consistent transformation* — every focal element `A` of `Bel` is replaced by `A ∪ {x}` and the masses are summed.

#### Example 45 (focused consistent transformation, Fig. 14.1) *(p.583-584)*

`Θ = {x, y, z, w}`. BF with focal elements `{y}, {y, z}, {x, z, w}`:

- `{y} ↦ {x} ∪ {y} = {x, y}`,
- `{y, z} ↦ {x} ∪ {y, z} = {x, y, z}`,
- `{x, z, w} ↦ {x} ∪ {x, z, w} = {x, z, w}` (fixed point — already contains `x`).

The masses transfer unchanged.

#### Theorem 87 (Global L1 in B) *(p.584)*

Global L1 consistent approximation:

$$
\hat{x} = \arg\min_{x \in \Theta} \sum_{A \subseteq \{x\}^c} Bel(A).
$$
**(Eq. 14.16, p.584).** In binary `Θ = {x,y}`, simplifies to `argmax_x pl(x)`. **In general it does not coincide with `argmax_x pl(x)`** — counter-example shown.

#### Theorem 88 (Global L2 in B) *(p.585)*

$$
Cs_{L_2}[Bel] = Cs^{\hat x}_{L_2}[Bel], \quad \hat{x} = \arg\min_{x \in \Theta} \sum_{A \subseteq \{x\}^c} (Bel(A))^2.
$$

In binary, equals `argmax_x pl(x)`. In general, *not* on the maximum-plausibility component.

### 14.3.2 L∞ consistent approximation in B — Theorem 89 *(p.585-586)*

For each component `CS^{A∋x}` the partial L∞ approximations form a polytope whose centre of mass is the partial L1/L2 approximation.

#### Theorem 89 (Partial L∞ in B is a rectangle) *(p.585)*

The partial L∞ consistent approximation with core ∋ `x` is determined by the system

$$
-Bel(\{x\}^c) - \sum_{B \subseteq A, B \not\supseteq \{x\}} m(B) \le γ(A) \le Bel(\{x\}^c) - \sum_{B \subseteq A, B \not\supseteq \{x\}} m(B),
$$
**(Eq. 14.17, p.585)** where

$$
γ(A) := \sum_{B \subseteq A, B \supseteq \{x\}} β(B) = \sum_{B \subseteq A, B \supseteq \{x\}} (m(B) - m_{Cs}(B)).
$$
**(Eq. 14.18, p.585).** This is a high-dimensional 'rectangle' in the space of variables `{γ(A)}`.

#### Corollary 20 (Barycentre = L1/L2) *(p.586)*

The partial L1/L2 consistent approximation on any component `CS^{A∋x}_B` equals the geometric **barycentre** of the L∞ partial approximations on the same component.

#### Corollary 21 (Global L∞ in B) *(p.586)*

The global L∞ consistent approximations in `B` are the union of partial L∞ approximations on the components associated with the maximum-plausibility element(s):

$$
CS_{L_\infty, B}[m] = \bigcup_{x = \arg\max pl(x)} CS^x_{L_\infty, B}[m].
$$

Argument: distance equals `Bel({x}^c)`, minimised over `x = argmax pl(x)`.

## Section 14.4 Approximations in belief vs mass space *(p.586-588)*

### Mass-space summary

- Partial L1 focused on `x`: reassign all `Bel({x}^c)` to `Θ` (Eq. 14.6).
- Global L1: conjunctive cores containing the maximum-plausibility element(s).
- L∞: polytope of partial approximations, barycentre = L1 partial.
- Global L∞: components focused on `x` minimising `max_{B \not\supseteq \{x\}} m(B)`.
- L2 partial in `R^{N-2}`: coincides with L1.
- L2 partial in `R^{N-1}`: redistributes `Bel({x}^c)` *equally* over all `2^{|Θ|-1}` ultrafilter elements (Eq. 14.11).
- Global L2: harder to interpret epistemically.
- Set of partial L∞ solutions is a polytope on each component, whose centre of mass is the L1/L2 partial.
- Global L∞: components associated with maximum-plausibility element(s); when unique, the centre of mass is the **consistent transformation focused on the max-plausibility singleton** — coinciding with possibility-theoretic constructions ([533]).

### Belief-space summary

- Partial L1 = partial L2 on each component (unique). Both equal the **focused consistent transformation** ([533, 91]):

$$
m_{Cs^x_{L_1}[Bel]}(A) = m_{Cs^x_{L_2}[Bel]}(A) = m(A) + m(A \setminus \{x\}).
$$

- Global L1: `x̂ = argmin_x Σ_{A ⊆ \{x\}^c} Bel(A)`.
- Global L2: `x̂ = argmin_x Σ_{A ⊆ \{x\}^c} (Bel(A))^2`. Neither has a "simple epistemic interpretation" — neither is `argmax pl(x)` in general.
- L∞ partial: polytope, barycentre = L1/L2.
- Global L∞: union over `x = argmax pl(x)` of partial polytopes; centre of mass when unique = focused consistent transformation on max-pl singleton.

### Master comparison

Both `M`- and `B`-space approximations reassign the total *out-of-ultrafilter* mass `Bel({x}^c)`, but **how** they redistribute it differs:

- **Mass space:** equal-basis (L2 in `R^{N-1}`) or all-to-`Θ` (L1, L2 in `R^{N-2}`). Mass space approximations *do not distinguish focal elements by their set-theoretic relationships with subsets `B \not\ni x`*.
- **Belief space:** uses the *focused consistent transformation* principle — each focal `A` is mapped to `A ∪ {x}` and masses summed. Set-theoretic structure is preserved.

### Example 46 (Ternary, full visual comparison, Fig. 14.2) *(p.587-588)*

Frame `Θ = {x,y,z}`. BPA (Eq. 14.19, p.587):

$$
m(x)=0.2, \; m(y)=0.1, \; m(z)=0, \; m(\{x,y\})=0.4, \; m(\{x,z\})=0, \; m(\{y,z\})=0.3.
$$

Wanting the consistent approximation focused on `x`, the simplex `CS^{A∋x} = Cl(m_x, m_{\{x,y\}}, m_{\{x,z\}}, m_Θ)` is a tetrahedron (blue). Then in the figure:

- **Mass-space partial L∞** = a *purple cube* (rectangle in 3D), partly outside the admissible tetrahedron.
- **Mass-space partial L1** = a single *purple square*, the barycentre of the cube; falls inside the tetrahedron and equals the partial L2 in `R^{N-2}`.
- **Mass-space partial L2 in `R^{N-1}`** = a *green square*, distinct from the purple square but inside both the cube and the tetrahedron. Splits `Bel({x}^c)` equally over the four ultrafilter elements.
- **Belief-space partial L1/L2** = the *focused consistent transformation* (analytical via Cor 19).
- **Belief-space partial L∞** = a polytope with barycentre at the L1/L2 point.

Strong interpretation case for the L1 partial in `M`: "all the mass outside the filter is reassigned to `Θ`, increasing the overall uncertainty of the belief state." Strong interpretation case for L2 partial in `R^{N-1}`: "splits the mass not in the filter focused on `x` equally among all the subsets in the filter."

## Equations (Chapter 14 list)

- 14.1 (p.575): `Cs[Bel] = argmin_{Cs ∈ CS} dist(Bel, Cs)`
- 14.2 (p.577): partial Lp problem in B and M
- 14.3 (p.578): difference vector `m - m_Cs` in `R^{N-2}`
- 14.4 (p.578): explicit L1/L2/L∞ M-space norms
- 14.5 (p.578): L1 norm via `β(B) := m(B) - m_Cs(B)`
- 14.6 (p.578): L1 partial in M, redistribution to Θ
- 14.7 (p.579): L∞ partial-in-M rectangle
- 14.8 (p.580): orthogonality in `R^{N-2}` for L2-in-M
- 14.9 (p.580): mass embedding in `R^{N-1}`
- 14.10 (p.580): orthogonality in `R^{N-1}`
- 14.11 (p.580): L2 partial in `R^{N-1}`, equal-share
- 14.12 (p.581): orthogonality in B for L2
- 14.13 (p.582): L1 linear system in B
- 14.14 (p.582): ternary L1 vs L2 systems
- 14.15 (p.582): row transformation reducing L2 → L1 system
- 14.16 (p.584): global L1 in B
- 14.17 (p.585): L∞ rectangle in B
- 14.18 (p.585): definition of `γ(A)`
- 14.19 (p.587): example 46 BPA
- 14.20 (p.589): Lemma 16 expansion in proofs

## Geometric structures (Chapter 14)

- **Consistent simplicial complex `CS_B = ∪_{x ∈ Θ} Cl(Bel_A, A ∋ x)`** — one maximal simplex per element of the frame; vertices are categorical BFs whose core contains `x`.
- **`CS_M = ∪_{x ∈ Θ} Cl(m_A, A ∋ x)`** — same in mass space.
- **L∞ partial-in-M rectangle (14.7)** — N-1 hyperrectangle of width `2 max_{B ∌ x} m(B)`; barycentre = L1 partial.
- **L∞ partial-in-B rectangle (14.17)** — N-2 hyperrectangle in the `γ(A)` variables; barycentre = L1/L2 partial.
- **Focused consistent transformation `Cs^x[Bel]`** — point in `B`, BPA `m_Cs(A) = m(A) + m(A \ {x})`. Equivalent to mapping every focal `A` to `A ∪ {x}` and summing masses.

## Algorithms (Chapter 14)

The chapter does not give numbered pseudocode but the constructive procedures are:

### Partial Lp consistent approximation in M, focused on x

1. **Input:** `m`, focus `x`, norm `p ∈ {1, 2, ∞}`.
2. **Compute** `Bel({x}^c) = Σ_{B ∌ x} m(B)`.
3. **L1 (Theorem 83):** `m_Cs(B) = m(B)` for all `B ⊇ {x}, B ≠ Θ`; `m_Cs(Θ) = m(Θ) + Bel({x}^c)`.
4. **L∞ (Theorem 84):** any `m_Cs` with `|m_Cs(B) - m(B)| ≤ max_{B ∌ x} m(B)` for `B ⊇ {x}, B ≠ Θ`. Barycentre = L1.
5. **L2 in `R^{N-2}`:** equals L1.
6. **L2 in `R^{N-1}` (Eq. 14.11):** `m_Cs(B) = m(B) + Bel({x}^c) / 2^{|Θ|-1}` for `B ⊇ {x}`.
7. **Admissibility:** L1 always; L2 always (both representations); L∞ may include negative-mass points.

### Partial Lp consistent approximation in B, focused on x

1. **Input:** `Bel`, focus `x`, norm `p ∈ {1, 2, ∞}`.
2. **L1 = L2 (Corollary 19):** `m_Cs(A) = m(A) + m(A \ {x})` for `A ⊇ {x}`.
3. **L∞ (Theorem 89):** rectangle (14.17) in `γ(A)` space; barycentre = L1/L2.
4. **Admissibility:** L1/L2 always; L∞ may produce pseudo-BFs.

### Global selection

| Problem | Global criterion |
|---------|------------------|
| L1 in M | `x̂ = argmax_x Pl(x) = argmin_x Bel({x}^c)` |
| L2 in M, `R^{N-1}` | `x̂ = argmin_x Σ_{B ∌ x} (m(B))^2` |
| L∞ in M | `x̂ = argmin_x max_{B ∌ x} m(B)` |
| L1 in B | `x̂ = argmin_x Σ_{A ⊆ {x}^c} Bel(A)` |
| L2 in B | `x̂ = argmin_x Σ_{A ⊆ {x}^c} (Bel(A))^2` |
| L∞ in B | `x̂ = argmax_x pl(x)` |

## Worked examples (Chapter 14)

### Example 44 (ternary linear systems coincide) *(p.582)*

For `Θ = {x,y,z}`, the L1 system and L2 system for partial consistent approximation in B yield identical solutions. The L2 system can be obtained from the L1 system by replacing `e_1 ↦ e_1 - e_2 - e_3`. This is generalised to arbitrary frames by Lemma 16 + Corollary 18.

### Example 45 (focused consistent transformation, Fig. 14.1) *(p.583-584)*

`Θ = {x, y, z, w}`; original BPA on `{y}, {y,z}, {x,z,w}`. After focusing on `x`, focal elements become `{x,y}, {x,y,z}, {x,z,w}` with the same masses. Visualised as a directed mapping where pre-images and images share colour codes.

### Example 46 (ternary, comparison of all approximations, Fig. 14.2) *(p.587-588)*

See Section 14.4 above. Demonstrates all five constructions on a single ternary BPA.

## Figures of interest (Chapter 14)

- **Fig. 14.1 (p.584):** Belief function on `{x, y, z, w}` (left) and its `L_1/L_2` consistent approximation in `B` with core `{x}` (right). Colour-coded focal elements before and after mapping.
- **Fig. 14.2 (p.588):** Comparison of `L_p` consistent approximations on `Θ = {x, y, z}` in `M` and `B`. Tetrahedron of admissible consistent BFs (blue), L∞-M cube (purple), L1/L2-M point (purple square = barycentre of cube), L2-M `R^{N-1}` point (green square — equal redistribution), corresponding `B`-space approximations also visible.

## Implementation notes for propstore

This chunk delivers two operational primitives the render layer needs:

### Consonant approximation

For any stored belief function `Bel` with BPA `m`, the renderer can compute the closest consonant approximation under any of `L_1, L_2, L_∞` in `M` or `B`:

- **`closest_consonant_M_L1(m, chain)`** — Eq. 13.20 (vertices) / 13.21 (barycentre). Always admissible. Global step = pick chain maximising `Σ_{A ∈ C} m(A)`.
- **`closest_consonant_M_L2(m, chain)`** — Eq. 13.21 directly. Always admissible. Global step = `argmin_C Σ_{B ∉ C} m(B)^2`.
- **`closest_consonant_M_Linf(m, chain)`** — Eq. 13.23 if `max_{B ∉ C} m(B) ≥ S/n` else falls back to L2 barycentre. *Admissibility check required* (Eq. 13.29). Global step = `argmin_C max_{B ∉ C} m(B)`, complexity `O(2^n)` versus `O(n!)`.
- **`closest_consonant_B_L1(Bel, chain)`** — list-based, vertices of polytope (13.38) by selecting innermost elements of `L_i`.
- **`closest_consonant_B_L2(Bel, chain)`** — Eq. 13.44 (unique).
- **`closest_consonant_B_Linf(Bel, chain)`** — `2^{n-1}`-vertex polytope (13.46); barycentre is `(Co_max + Co_con) / 2`.

The chapter explicitly notes (Section 13.5.2) that **mass-space approximations**, **belief-space approximations**, and **isopignistic approximation** form three families with fundamentally different rationales — render policy must choose explicitly which family is desired, not silently compute one.

### Consistent approximation

For any stored belief function `Bel`, the renderer can compute the closest consistent approximation under any norm in `M` or `B`:

- **`closest_consistent_M_L1(m, x)`** — Eq. 14.6: `m_Cs(B) = m(B)` for `B ⊇ {x}, B ≠ Θ`; `m_Cs(Θ) = m(Θ) + Bel({x}^c)`.
- **`closest_consistent_M_Linf(m, x)`** — rectangle (14.7); admissibility may fail.
- **`closest_consistent_M_L2_N1(m, x)`** — Eq. 14.11: equal redistribution of `Bel({x}^c)` to all `2^{|Θ|-1}` ultrafilter elements.
- **`closest_consistent_B(Bel, x)`** — focused consistent transformation Cor 19: `m_Cs(A) = m(A) + m(A \ {x})` for `A ⊇ {x}`. **One unique answer for L1, L2 in B.** This is the cleanest formula in the chapter and the canonical "focused" transformation.

### Global selection / focus point `x̂`

Different norms select different `x̂` (table above). For propstore:

- L1 in M and L∞ in B both select `argmax_x pl(x)` — the *most plausible singleton*.
- L1/L2 in B select `argmin_x Σ_{A ⊆ {x}^c} Bel(A)` (or its squared version), which **is not generally `argmax_x pl(x)`**. Render policy must store this distinction.
- The renderer should be able to expose the consistent transformation focused on a *user-chosen* `x` (e.g., a specific singleton claim under analysis), not only the global optimum.

### Provenance implications

A consonant or consistent approximation is a *derived* artifact, not a source belief function. When the render layer materialises it, the resulting object should carry provenance (`derived`, `source: <Bel-id>`, `method: closest-consonant-M-L1-chain-C`, `not-admissible: bool`). The chapter's repeated admissibility caveats (L∞ M, L∞ B, ternary B-space L1) mean propstore must mark some approximations as *pseudo*-belief-functions when negative mass is produced, never silently clip.

### Belief-vs-mass-space rendering choice

Section 13.5.2 and Section 14.4 jointly establish that:

- Mass-space approximations are mass-redistribution stories.
- Belief-space approximations are generalised maximal-outer / focused-consistent stories that preserve set-theoretic relations among focal elements.

These are different *epistemic operations*. Render policy should expose the choice and document the chosen family in produced reports.

### Operational reuse

Theorem 71 (chain measure = maximal outer approximation) gives a clean way to compute `Co^ρ` directly from `Bel` without enumerating assignment functions: `Bel_C(A) = max_{B ∈ C, B ⊆ A} Bel(B)`. This is `O(n · 2^n)` instead of `O(n^{2^n})`.

The L∞-M global complexity gain (`O(2^n)` vs `O(n!)`) noted in Section 13.3.3 is operationally important for moderate-`n` frames where chain enumeration becomes infeasible.

## Notable references cited *(this chunk)*

- `[1389]` — logic with inconsistent knowledge bases. Cited as motivation for the consistent transformation problem *(p.575)*.
- `[416]` Dempster's rule of combination — does not preserve consistency *(p.575)*.
- `[1689]` — disjunctive combination — does not preserve consistency *(p.575)*.
- `[382, 333]` — probability transforms (Chapters 11–12) *(p.575)*.
- `[533]` — Dubois-Prade possibilistic transformation; consistent transformation focused on `x` is the same construction *(p.575, p.586, p.587)*.
- `[91]` — earlier work on classical inner approximations of consistent BFs *(p.576, p.587)*.
- `[551, 338]` — earlier geometric work on consistent simplicial complex *(p.576)*.
- `[356]` — Cuzzolin's earlier paper computing some conditional belief functions via minimisation (cited at the very start of Chapter 15, p.595).
- `[1086, 245, 584, 640, 691, 439, 2080, 873, 1800]` — proposals for conditional belief functions in different mathematical setups (forward reference at p.595, into chunk 9).
- `[165, 391, 1229, 1128]` — geometric formulations of conditioning (forward reference at p.595).

## Open / research questions *(this chunk)*

- "Global L2 in B" — Theorem 80 footnote (p.547): "computationally involved and left for future work."
- The relationship between "L2/L∞ barycentre in B" and "L1 partial in M" is conjectured (Section 13.5.1) and shown to fail in general — but tightening this characterisation is open.
- Theorem 87 (Global L1 in B) explicitly notes that `argmin_x Σ_{A ⊆ \{x\}^c} Bel(A) ≠ argmax_x pl(x)` in general — the epistemic interpretation of the L1-B global focus is not yet clean.
- Theorem 88 (Global L2 in B) similarly lacks a "simple epistemic interpretation" *(p.586)*.

## Quotes worth preserving

- "Approximations in `M` and `B` do not coincide. This is a direct consequence of the fact that Möbius inversion does not preserve either `L_p` norms or the ordering induced by them." *(p.554)*
- "The isopignistic, mass space and belief space consonant approximations form three distinct families of approximations, with fundamentally different rationales: which approach to be used will therefore vary according to the framework chosen, and the problem at hand." *(p.556)*
- "Consistent belief functions are characterised by null internal conflict. It may therefore be desirable to transform a generic belief function to a consistent one prior to making a decision or choosing a course of action." *(p.575)*
- "There are just two such events: `A` itself, and `A \ {x}`." *(p.583)* — the two-event interpretation of the focused consistent transformation.
- "[Mass space approximations] do not distinguish focal elements by virtue of their set-theoretic relationships with subsets `B ⊉ x` outside the filter. In contrast, approximations in the belief space do so according to the focused consistent transformation principle." *(p.587)*

## Criticisms of prior work

- Dempster sum and disjunctive combination "do not preserve consistency" (p.575) — motivates the need for an explicit consistent transformation.
- Pignistic-based approximations of consonants are *unrelated* to mass-space and belief-space families (Section 13.5.2, p.555-556).
- The contour-based approximation `Co_con` is admissible only when the chain is generated by *plausibility-sorted* singletons (p.551), not generally.

## Design rationale captured

- *Why two spaces?* Möbius inversion fails to preserve both `L_p` norms and the order they induce, so M-approximations and B-approximations are inequivalent. Both must be available to the render layer (Section 13.5.1, p.554).
- *Why four families of consonant approximations (mass-space, belief-space, isopignistic, contour-based)?* Each captures a different rationale: mass redistribution, generalised maximal outer, pignistic equivalence, contour-as-possibility. There is no single "correct" approximation (Section 13.5.2, p.555-556).
- *Why focus on `x`?* The consistent simplicial complex `CS` decomposes into one maximal simplex per element of `Θ`. Each partial problem has a closed-form solution; only the global optimum involves cross-component selection (Section 14.1, p.577).

