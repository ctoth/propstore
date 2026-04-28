# Chunk #6 — Chapter 9 (Three equivalent models) + Chapter 10 (The geometry of possibility)

**Book pages:** 389–430 (Chapter 9: 389–407; Chapter 10: 409–428; the assigned PDF range 414–455 extends past Chapter 10 into the start of Part III / Chapter 11, so this surrogate covers Chapters 9 and 10 only — the Chapter 11 opener at PDF p.447 / book p.431 falls into the next chunk.)
**PDF idx:** 414–455 (effective content 407–445; PDF idx = book_page + 18 in this region, not +25 as the front-matter convention says)

## Sections covered

- 9 Three equivalent models *(book p.389)*
  - 9.1 Basic plausibility assignment *(p.390)*
    - 9.1.1 Relation between basic probability and plausibility assignments *(p.391)*
  - 9.2 Basic commonality assignment *(p.392)*
    - 9.2.1 Properties of basic commonality assignments *(p.393)*
  - 9.3 The geometry of plausibility functions *(p.393)*
    - 9.3.1 Plausibility assignment and simplicial coordinates *(p.394)*
    - 9.3.2 Plausibility space *(p.395)*
  - 9.4 The geometry of commonality functions *(p.396)*
  - 9.5 Equivalence and congruence *(p.399)*
    - 9.5.1 Congruence of belief and plausibility spaces *(p.399)*
    - 9.5.2 Congruence of plausibility and commonality spaces *(p.400)*
  - 9.6 Pointwise rigid transformation *(p.402)*
    - 9.6.1 Belief and plausibility spaces *(p.402)*
    - 9.6.2 Commonality and plausibility spaces *(p.403)*
  - Appendix: Proofs *(p.405)*
- 10 The geometry of possibility *(p.409)*
  - 10.1 Consonant belief functions as necessity measures *(p.409)*
  - 10.2 The consonant subspace *(p.411)*
    - 10.2.1 Chains of subsets as consonant belief functions *(p.412)*
    - 10.2.2 The consonant subspace as a simplicial complex *(p.414)*
  - 10.3 Properties of the consonant subspace *(p.416)*
    - 10.3.1 Congruence of the convex components of CO *(p.416)*
    - 10.3.2 Decomposition of maximal simplices into right triangles *(p.418)*
  - 10.4 Consistent belief functions *(p.418)*
    - 10.4.1 Consistent knowledge bases in classical logic *(p.419)*
    - 10.4.2 Belief functions as uncertain knowledge bases *(p.419)*
    - 10.4.3 Consistency in belief logic *(p.420)*
  - 10.5 The geometry of consistent belief functions *(p.422)*
    - 10.5.1 The region of consistent belief functions *(p.422)*
    - 10.5.2 The consistent complex *(p.423)*
    - 10.5.3 Natural consistent components *(p.424)*
  - 10.6 Research questions *(p.426)*
  - Appendix: Proofs *(p.427)*

## Chapter overview

Chapter 9 establishes that belief, plausibility (`Pl`), and commonality (`Q`) functions are three equivalent representations of the same underlying body of evidence. Cuzzolin defines two new combinatorial objects — the **basic plausibility assignment** (BPlA, denoted `μ`) and the **basic commonality assignment** (`q`) — as the Möbius inverses of `Pl` and `Q` respectively. Each is a "sum function" on the powerset `2^Θ`, but with crucial differences: BPlAs satisfy normalisation but not non-negativity (unlike `m`); basic commonality assignments are unnormalised. The chapter then carries the simplicial geometry of belief space (Chapter 7) over to plausibility space `PL` and commonality space `Q`, showing each is a simplex whose vertices correspond to categorical belief functions, and whose simplicial coordinates are the corresponding Möbius inverse. Finally it proves the three simplices `B`, `PL`, `Q` are *congruent* (Theorems 28–29, Corollaries 8–10) and that the equivalence between `Bel`, `Pl`, `Q` is geometrically a **pointwise rigid transformation**: a composition of two reflections (Theorem 30 + the analogous map for commonality, Section 9.6).

Chapter 10 specialises the theory to **consonant belief functions** — those whose focal elements form a chain under inclusion. These are the belief-function counterparts of necessity measures (Pos's dual), and studying their geometry *is* studying the geometry of possibility theory on a finite frame. Cuzzolin shows the **consonant subspace** `CO` is the union of `n!` maximal simplices (one per maximal chain of subsets of `Θ`), each of dimension `n-1`, forming a **simplicial complex** in the sense of Definition 125. He then proves all maximal simplices are congruent (Theorem 33), and that two-dimensional faces of any maximal component are *right triangles* (Theorem 34). The second half introduces **consistent belief functions** as the BF-theoretic counterpart of consistent classical knowledge bases — BFs whose focal elements have non-empty intersection (Theorems 35–36). Their region `CS` also forms a simplicial complex `CS` (Theorem 37) of `n` maximal simplices each of dimension `2^{n-1}-1`, all congruent (Theorem 38). Equation (10.11) decomposes any `Bel` into `n` consistent components weighted by the pignistic transformation `BetP[Bel]`, foreshadowing Chapters 13–14 (consonant and consistent approximations).

Together these two chapters constitute the geometric "trinity" payload of Part II: every uncertainty measure of interest in DS theory is a point in some Cartesian-space simplex with explicit simplicial coordinates and a known rigid-transformation relationship to its peers.

## Definitions

### Definition 124 (Possibility measure) *(p.411)*

A possibility measure on a domain `Θ` is a function `Pos : 2^Θ → [0,1]` such that `Pos(∅)=0`, `Pos(Θ)=1` and
$$
Pos\left(\bigcup_i A_i\right) = \sup_i Pos(A_i)
$$
for any family `{A_i | A_i ∈ 2^Θ, i ∈ I}` with `I` an arbitrary index set. Each `Pos` is uniquely characterised by a *membership function* `π : Θ → [0,1]`, `π(x) ≐ Pos({x})`, via `Pos(A) = sup_{x∈A} π(x)`. The plausibility function `Pl` of a `Bel` is a possibility measure iff `Bel` is consonant, with the contour function `pl` playing the role of `π`: `π = pl`.

### Definition 125 (Simplicial complex) *(p.414)*

A simplicial complex is a collection `Σ` of simplices of arbitrary dimensions possessing the following properties:
1. If a simplex belongs to `Σ`, then all its faces of any dimension belong to `Σ`.
2. The intersection of any two simplices in the complex is a face of both.

### Definition 126 (Consistent belief function) *(p.421)*

A belief function `Bel` on `Θ` is termed **consistent** if there exists no proposition `B ⊂ Θ` such that both `B` and its negation `B^c` are implied by `Bel`. Different implication relations (10.3)/(10.4)/(10.5) produce different "consistent" classes; the chapter eventually settles on (10.5): `Bel ⊢ B ⇔ Bel(B) ≠ 0`.

### Implicit / running definitions used throughout the chunk

- **Basic plausibility assignment (BPlA)** `μ : 2^Θ → ℝ`: the Möbius inverse of `Pl`, defined via (9.1) `μ(A) ≐ Σ_{B⊆A} (-1)^{|A\B|} Pl(B)`; equivalent explicit form (9.3): `μ(A) = (-1)^{|A|+1} Σ_{C⊇A} m(C)` for `A≠∅`, `μ(∅)=0` *(p.390–391)*.
- **Basic commonality assignment** `q : 2^Θ → ℝ`: the Möbius inverse of `Q`, defined via (9.6) `q(B) = Σ_{∅⊆A⊆B} (-1)^{|B\A|} Q(A)`; equivalent explicit form (9.7): `q(B) = (-1)^{|B|}(1 - Pl(B)) = (-1)^{|B|} Bel(B^c)` *(p.392–393)*.
- **Plausibility space** `PL`: region of `ℝ^{N-2}` of admissible plausibility vectors *(p.395)*.
- **Commonality space** `Q ⊂ ℝ^N`: vector representation of commonality functions on `2^Θ` (here `N = 2^{|Θ|}`, full power set including `∅` and `Θ`) *(p.396)*.
- **Conjunctive core** `C^∩ ≐ ⋂_{m(A)≠0} A` (10.6) *(p.421)*; **disjunctive core** `C^∪ = ⋃_{m(A)≠0} A` (the traditional "core") *(p.421)*.
- **Internal conflict** `c(Bel) ≐ Σ_{A,B⊆Θ : A∩B=∅} m(A) m(B)` (10.8) *(p.422)*.
- **Consonant** `Bel`: focal elements are nested *(p.409)*.
- **Maximal chain** `C = {A_1 ⊂ ⋯ ⊂ A_n=Θ}` of subsets of `Θ`; vectors `{Bel_{A_i}, A_i ∈ C}` are affinely independent *(p.412)*.

## Theorems, propositions, lemmas, corollaries

### Theorem 24 *(p.390–391; proof p.405)*

Given a belief function `Bel` with bpa `m`, the corresponding basic plausibility assignment is
$$
\mu(A) = \begin{cases}(-1)^{|A|+1} \sum_{C\supseteq A} m(C) & A \neq \emptyset \\ 0 & A=\emptyset\end{cases}
$$
**(Eq. 9.3)** Proof: substitute `Pl(B)=1-Bel(B^c)` into (9.1), use Newton's binomial. Like BPAs, BPlAs are normalised (`Σ_{A⊆Θ} μ(A)=1`), but unlike `m`, `μ` is not guaranteed non-negative.

### Theorem 25 *(p.392)*

For any singleton `{x}`: `Σ_{A⊇{x}} μ(A) = m(x)` (Eq. 9.5). The basic plausibility values of all events containing `x` sum to its bpa. Proof uses Newton's binomial.

### Theorem 26 (Plausibility space is a simplex) *(p.395; proof p.407)*

`PL = Cl(Pl_A, ∅⊊A⊆Θ)` whose vertices in the categorical-belief reference frame are
$$
Pl_A = -\sum_{\emptyset \subsetneq B \subseteq A} (-1)^{|B|} Bel_B
$$
**(Eq. 9.11)**. Note `Pl_x = -(-1)^{|x|} Bel_x = Bel_x` for `x∈Θ` (singletons), so `B ∩ PL ⊃ P` (the probability simplex sits in the intersection of belief and plausibility space).

### Theorem 27 *(p.395; proof p.407)*

The vertex `Pl_A` of `PL` is the plausibility vector associated with the categorical belief function `Bel_A`: `Pl_A = Pl_{Bel_A}`.

### Theorem 28 (Congruence of 1-faces of B and PL) *(p.399)*

The one-dimensional faces `Cl(Bel_A, Bel_B)` and `Cl(Pl_A, Pl_B)` are congruent:
$$
\|Pl_B - Pl_A\|_p = \|Bel_A - Bel_B\|_p
$$
for the classical p-norm `‖v‖_p = (Σ|v_i|^p)^{1/p}`, all `p∈{1,2,...,+∞}`. Proof: `Pl_A(C)=1-Bel_A(C^c)` ⇒ `Bel_A(C^c) - Bel_B(C^c) = Pl_B(C) - Pl_A(C)`, then sum over `C`.

### Corollary 8 *(p.399)*

`B` and `PL` are congruent; `B^U` and `PL^U` are congruent (unnormalised case).

### Theorem 29 (Congruence of 1-faces of Q and PL) *(p.401)*

`‖Q_B - Q_A‖_p = ‖Pl_{B^c} - Pl_{A^c}‖_p`. Proof: `Q_A = Bel_∅ - Pl_{A^c}` (cf. (9.14)), so `Q_A - Q_B = Pl_{B^c} - Pl_{A^c}`. The map `Q_A ↦ Pl_{A^c}` (Eq. 9.15) sends 1-faces of `Q^U` to congruent 1-faces of `PL^U`.

### Corollary 9, 10 *(p.401)*

`Q^U` and `PL^U` are congruent; `Q^U` and `B^U` are congruent.

### Theorem 30 (Pointwise rigid transformation `B → PL`) *(p.402)*

The plausibility vector `Pl` associated with a belief function `Bel` is the reflection in `ℝ^{N-2}` through the segment `Cl(Bel_Θ, Pl_Θ) = Cl(0,1)` of the "complement" belief function `Bel^c`, where `Bel^c(A) ≐ Bel(A^c)`. In compact form: `Pl = 1 - Bel^c` (normalised) or `Pl = Pl_∅ + Bel_∅ - Bel^c` (unnormalised; `Pl` is the reflection of `Bel^c` through `Cl(Bel_∅, Pl_∅) = Cl(0,1)`).

The full rigid transformation is the composition of two reflections: (i) swap of axes `v_A ↔ v_{A^c}` induced by set complement (sending `Bel ↦ Bel^c`); (ii) reflection through the centre of `Cl(0,1)`. Analogously for `PL → Q`: `τ_{PL^U Q^U}: Pl ↦ Pl^{m^c}` (mass-complement) ↦ `Q` *(p.404)*.

### Proposition 56 *(p.410)*

Suppose `Bel_1, ..., Bel_n` are non-vacuous simple support functions with foci `C_1,...,C_n` and `Bel = Bel_1 ⊕ ⋯ ⊕ Bel_n` is consonant. If `C` denotes the core of `Bel`, then `C_i ∩ C` are nested.

### Theorem 32 (Consonant subspace is a simplicial complex) *(p.415)*

`CO ⊆ B` is a simplicial complex (Definition 125) embedded in the belief space. Property 1 holds because chains map to subchains; property 2 (intersections of two simplices are faces of both) follows because `Bel_A` are linearly independent and `a(Bel_A, A∈L_1) ∩ a(Bel_A, A∈L_2) ≠ ∅` iff `L_1 ∩ L_2 ≠ ∅`, with the intersection being `Cl(Bel_{C_j}, j=1,...,k)` for `{C_j} = A∩B`.

### Theorem 33 (All maximal simplices of CO are congruent) *(p.417)*

Proof by 1–1 correspondence between vertices of any two maximal simplices using cardinality matching: `|A_i|=|B_i|`, `|A_j|=|B_j|`, with `‖Bel_{A_i} - Bel_{A_j}‖_2 = √(|A_j \ A_i|) = ‖Bel_{B_i} - Bel_{B_j}‖_2`.

### Theorem 34 (Right-angle property in CO) *(p.418)*

If `A_i ⊋ A_j ⊋ A_k` then the angle `Bel_{A_i} \widehat{Bel_{A_j}} Bel_{A_k} = π/2`. Proof: `‖Bel_{A_j} - Bel_{A_i}‖` is supported on `{B : B⊇A_j, B⊉A_i}`, `‖Bel_{A_k} - Bel_{A_j}‖` on `{B : B⊇A_k, B⊉A_j}`, and these sets are disjoint (since `B⊇A_j ⇒ B⊇A_k` is automatic but `B⊉A_j` and `B⊇A_j` partition), giving zero inner product. Consequence: every 2-face of every maximal `CO` component is a right triangle; every 3-face (tetrahedron) has right-triangle 2-faces, and so on (Fig. 10.4).

### Theorem 35 (Consistency criterion under (10.5)) *(p.421)*

A belief function is consistent under `Bel ⊢ B ⇔ Bel(B) ≠ 0` iff its conjunctive core is non-empty:
$$
C^\cap = \bigcap_{A : m(A) \neq 0} A \neq \emptyset
$$
**(Eq. 10.7)**. Forward: if `B`, `B^c` both implied (have non-zero `Bel`), then `⋂{A:Bel(A)≠0}` is contained in `B ∩ B^c = ∅`, contradicting `C^∩ ≠ ∅`. Backward: if `C^∩ = ∅`, take `B` to be any focal element; then `B^c` contains another focal (else `C^∩` non-empty), giving `Bel(B^c) ≠ 0`, and `Bel(B) ≥ m(B) ≠ 0`. Under (10.4) the condition `C^∩ ≠ ∅` is *not* sufficient — must additionally have `|C^∩| = 1`.

### Theorem 36 (Consistency ↔ zero internal conflict) *(p.422)*

`Bel : 2^Θ → [0,1]` is consistent iff `c(Bel) = Σ_{A,B:A∩B=∅} m(A)m(B) = 0` (Eq. 10.8). Direct corollary of Theorem 35.

### Theorem 37 (`CS` is a simplicial complex) *(p.423; proof p.427)*

The region of consistent BFs `CS = ⋃_{x∈Θ} Cl(Bel_A, A∋x)` (Eq. 10.9) is a simplicial complex in `B`. Proof uses Definition 125: faces of any "principal-filter simplex" are simplices of consistent BFs (cores remain non-empty because they contain `x`); intersections of principal-filter simplices are themselves principal filters for the union of cores, hence faces of both.

### Theorem 38 (All maximal simplices of `CS` are congruent) *(p.424; proof p.428–429)*

Proof constructs a vertex map (10.13)–(10.14) `A=B∪{x} ↦ A'=B'∪{y}`, with `B' = B` if `B⊆{x,y}^c` and `B' = C∪{x}` if `B = C∪{y}` (and symmetric). Case analysis (4 cases) shows `‖Bel_{A'_2} - Bel_{A'_1}‖ = ‖Bel_{A_2} - Bel_{A_1}‖`, then Euclid's congruence theorem.

## Equations

$$
Pl(A) = 1 - Bel(A^c) = \sum_{B\cap A \neq \emptyset} m(B)
$$
**(p.389, ch.9 opener)** Plausibility as a sum function over events meeting `A`.

$$
Q(A) = \sum_{B \supseteq A} m(B)
$$
**(p.389, ch.9 opener)** Commonality as upward-cumulative mass.

$$
\mu(A) \doteq \sum_{B\subseteq A} (-1)^{|A\setminus B|} Pl(B)
$$
**(Eq. 9.1, p.390)** Möbius inverse defining the basic plausibility assignment `μ`.

$$
Pl(A) = \sum_{B\subseteq A} \mu(B)
$$
**(Eq. 9.2, p.390)** `Pl` recovered as a (signed) sum function over its BPlA.

$$
\mu(A) = \begin{cases}(-1)^{|A|+1} \sum_{C\supseteq A} m(C) & A\neq\emptyset \\ 0 & A=\emptyset\end{cases}
$$
**(Eq. 9.3, p.391)** Closed form of BPlA in terms of bpa `m`.

$$
\sum_{k=0}^{n} \binom{n}{k} p^k q^{n-k} = (p+q)^n
$$
**(Eq. 9.4, p.391)** Newton's binomial theorem (used throughout proofs).

$$
\sum_{A \supseteq \{x\}} \mu(A) = m(x)
$$
**(Eq. 9.5, p.392)** Singleton-summation identity (Theorem 25).

$$
q(B) = \sum_{\emptyset \subseteq A \subseteq B} (-1)^{|B\setminus A|} Q(A)
$$
**(Eq. 9.6, p.392)** Möbius inverse defining basic commonality assignment `q`.

$$
q(B) = (-1)^{|B|}(1 - Pl(B)) = (-1)^{|B|} Bel(B^c)
$$
**(Eq. 9.7, p.393)** Closed form of `q` (note `q(∅)=Bel(Θ)=1`).

$$
Bel = \sum_{\emptyset \subsetneq A \subseteq \Theta} Bel(A) v_A, \qquad Pl = \sum_{\emptyset \subsetneq A \subseteq \Theta} Pl(A) v_A
$$
**(Eq. 9.8, p.394)** Vector representations in the standard reference frame `{v_A}`.

$$
v_A = \sum_{B \supseteq A} (-1)^{|B\setminus A|} Bel_B
$$
**(Eq. 9.9, p.394; Lemma 8)** Coordinate change between standard and categorical reference frames.

$$
Pl = \sum_{\emptyset \subsetneq A \subsetneq \Theta} \mu(A) Bel_A
$$
**(Eq. 9.10, p.394)** `Pl`'s simplicial coordinates in the categorical frame are exactly the BPlA.

$$
Pl_A = -\sum_{\emptyset \subsetneq B \subseteq A} (-1)^{|B|} Bel_B
$$
**(Eq. 9.11, p.395)** Vertex of plausibility space.

$$
Q_A \doteq \sum_{\emptyset \subseteq B \subseteq A^c} (-1)^{|B|} Bel_B
$$
**(Eq. 9.12, p.397)** Vertex of commonality space.

$$
Q_A = \sum_{\emptyset \subseteq B \subseteq A^c} (-1)^{|B|} Bel_B = -Pl_{A^c} + Bel_\emptyset
$$
**(Eq. 9.14, p.401)** Relation linking commonality vertices to plausibility vertices on complementary subsets.

$$
Q_A \mapsto Pl_{A^c}
$$
**(Eq. 9.15, p.401)** Vertex map between `PL^U` and `Q^U`.

$$
Pl = 1 - Bel^c, \qquad Pl = Pl_\emptyset + Bel_\emptyset - Bel^c
$$
**(p.402, Theorem 30)** Normalised / unnormalised pointwise rigid map.

$$
Pl = \sum_{\emptyset \subsetneq C \subseteq \Theta} m(C) Pl_C
$$
**(Eq. 9.18, p.407)** `Pl` as a convex combination of plausibility-space vertices weighted by `m`.

$$
Pos\left(\bigcup_i A_i\right) = \sup_i Pos(A_i)
$$
**(p.411)** Possibility-measure axiom.

$$
\mathcal{CO} = \bigcup_{C=\{A_1\subset\cdots\subset A_n\}} Cl(Bel_{A_1},\ldots,Bel_{A_n})
$$
**(Eq. 10.1, p.413)** Consonant subspace as union of `n!` maximal simplices indexed by maximal chains of `2^Θ`.

$$
\prod_{k=1}^{n} \binom{k}{1} = n!
$$
**(p.413)** Counting maximal chains in `(2^Θ, ⊆)`.

$$
Bel \vdash B \Leftrightarrow Bel(B) = 1
$$
**(Eq. 10.3, p.420)** Strong implication relation (`B` implied iff every focal `⊆ B`).

$$
Bel \vdash B \Leftrightarrow Pl(B) = 1
$$
**(Eq. 10.4, p.420)** Dual implication: `B` implied iff `Pl(B)=1`.

$$
Bel \vdash B \Leftrightarrow Bel(B) \neq 0
$$
**(Eq. 10.5, p.420)** Weak implication: `B` implied iff there is positive support for it.

$$
\mathcal{C}^\cap \doteq \bigcap_{m(A)\neq 0} A
$$
**(Eq. 10.6, p.421)** Conjunctive core (intersection of focals).

$$
\mathcal{C}^\cap = \bigcap_{A:m(A)\neq 0} A \neq \emptyset
$$
**(Eq. 10.7, p.421)** Consistency criterion under (10.5) — Theorem 35.

$$
c(Bel) \doteq \sum_{A,B \subseteq \Theta : A \cap B = \emptyset} m(A) m(B)
$$
**(Eq. 10.8, p.422)** Internal conflict.

$$
\mathcal{CS} = \bigcup_{x\in\Theta} Cl(Bel_A, A \ni x)
$$
**(Eq. 10.9, p.423)** Region of consistent belief functions: union of `n` "principal-filter" simplices.

$$
Cl(Bel_A : A\ni x) = Cl(Bel_x, Bel_{\{x,y\}}, Bel_{\{x,z\}}, Bel_\Theta) \quad \text{(ternary)}
$$
**(Eq. 10.10 fragments, p.423)** The 3 maximal simplices of `CS` for `Θ={x,y,z}`, each of dimension `2^{n-1}-1=3`.

$$
Bel = \sum_{x\in\Theta} BetP[Bel](x) \cdot Bel^x, \qquad Bel^x \doteq \frac{1}{BetP[Bel](x)} \sum_{A\ni x} \frac{m(A)}{|A|} Bel_A
$$
**(Eq. 10.11, p.424)** Decomposition of any `Bel` into `n` consistent components weighted by the pignistic probability `BetP[Bel](x) = Σ_{A∋x} m(A)/|A|`. Each `Bel^x` is consistent with conjunctive core `{x}` and lives in the maximal simplex `CS^{A∋x}`.

$$
\{A\subseteq\Theta : A\ni x\} = \{A\subseteq\Theta : A = B\cup\{x\}, B\subseteq\{x\}^c\}
$$
**(Eq. 10.12, p.427)** Reformulation of principal-filter event collections.

## Geometric structures

- **Plausibility space** `PL ⊂ ℝ^{N-2}` (normalised) or `PL^U ⊂ ℝ^N` (unnormalised). Simplex with `N-2` (resp. `N`) vertices `{Pl_A : ∅⊊A⊆Θ}` (resp. `∅⊆A⊆Θ`). Vertex `Pl_A = -Σ_{∅⊊B⊆A}(-1)^{|B|} Bel_B`. Each `Pl_A = Pl_{Bel_A}` (Theorem 27). Simplicial coordinates of any `Pl ∈ PL` are the BPlA `μ(A)` (Eq. 9.10) — equivalently `Pl = Σ_C m(C) Pl_C` (Eq. 9.18). For singletons `x∈Θ`: `Pl_x = Bel_x`, so `B ∩ PL ⊃ P` (probability simplex sits in the intersection).

- **Commonality space** `Q ⊂ ℝ^N` (always extended frame; `Q(∅)=1` always, so `Q^U` is natural). Simplex with vertices `Q_A = Σ_{∅⊆B⊆A^c}(-1)^{|B|} Bel_B`. In the binary frame: `Q_∅ = [1,0,0,0]'`, `Q_x = [1,1,0,0]'`, `Q_y = [1,0,1,0]'`, `Q_Θ = [1,1,1,1]'` (Example 22, p.398). Each vertex `Q_A` equals the commonality vector of the categorical BF `Bel_A`.

- **Belief space** `B^U` (unnormalised): simplex `Cl(Bel_A, ∅⊆A⊆Θ)` in `ℝ^N` with `N=2^{|Θ|}` vertices. Adds `Bel_∅ = [1,0,...,0]'`. In binary: `Bel_∅=[1,1,1,1]'`, `Bel_x=[0,1,0,1]'`, `Bel_y=[0,0,1,1]'`, `Bel_Θ=[0,0,0,1]'` (Eq. 9.13).

- **Congruence**: `B^U ≅ PL^U ≅ Q^U` (Corollaries 8–10). In normalised case, `B ≅ PL` but `PL_2` is *not* congruent to `Q_2` in normalised form (the latter is equilateral with side `√2` while `PL_2` has two unit sides) — congruence requires the unnormalised setting.

- **Pointwise rigid transformation** `τ_{B^U PL^U} : B^U → PL^U`: composition of two reflections — (i) coordinate swap `v_A ↔ v_{A^c}` (i.e. `Bel ↦ Bel^c`), (ii) reflection through the segment `Cl(0,1) = Cl(Bel_Θ, Pl_Θ)` (or `Cl(Bel_∅, Pl_∅)` in unnormalised case). Analogously `τ_{PL^U Q^U}: Pl ↦ Pl^{m^c} ↦ Q`. In binary case: just a reflection through the Bayesian segment `P_2 = Cl(Bel_x, Bel_y)`. Each pair `(Bel, Pl)` lies on a line `a(Bel, Pl)` orthogonal to `P_2`, in symmetric positions on its two sides (Fig. 9.1).

- **Consonant subspace** `CO ⊆ B`: union of `n!` maximal simplices `Cl(Bel_{A_1},...,Bel_{A_n})`, one per maximal chain `A_1 ⊂ ⋯ ⊂ A_n=Θ`. Each maximal simplex has dimension `n-1`. Each categorical `Bel_A` with `|A|=k` belongs to `(n-k)!k!` maximal simplices. Each `Bel_x` (for `|x|=1`) belongs to `(n-1)!` components. `CO` is connected (every pair of components shares `Bel_Θ`). `CO` is part of the boundary `∂B` of the belief space. In the ternary case (Fig. 10.2): `B_3` is six-dimensional with two-dimensional probabilistic face `P_3 = Cl(Bel_x, Bel_y, Bel_z)`; `CO_3` is the union of `3!=6` triangles each of dimension 2, every vertex of `P_3` shared by `(n-1)!=2!=2` of them.

- **Right-triangle decomposition (Theorem 34)**: every triangle `Cl(Bel_{A_i}, Bel_{A_j}, Bel_{A_k})` with `A_i ⊋ A_j ⊋ A_k` is a right triangle with the right angle at `Bel_{A_j}` (the *middle* set in the chain). Hence every 2-face of every maximal `CO`-component is a right triangle, every 3-face (tetrahedron) has right-triangle 2-faces, and so on (Fig. 10.4).

- **Consistent complex** `CS = ⋃_{x∈Θ} Cl(Bel_A : A ∋ x)`. `n=|Θ|` maximal simplices ("principal filters" associated with singletons `{x}`). Each maximal simplex `CS^{A∋x}` has `2^{n-1}` vertices and dimension `2^{n-1}-1 = dim B / 2`. `CS` is connected (every pair of components shares `Bel_Θ`). Each maximal simplex of `CS` is congruent (Theorem 38). In ternary case: `CS_3` has 3 maximal simplices (dim 3), `CS^{A∋x}=Cl(Bel_x, Bel_{xy}, Bel_{xz}, Bel_Θ)`, etc. (Eq. 10.10).

- **Pignistic decomposition simplex** `P^{Bel} ≐ Cl(Bel^x, x∈Θ) ⊂ CS`: each `Bel` lives in this `n-1`-dimensional simplex with simplicial coordinates `BetP[Bel](x)` (Fig. 10.5). Both `Bel` and `BetP[Bel]` have the same pignistic values, so `P^{Bel}` is a bridge between belief-, probability-, and possibility-related decompositions.

## Algorithms / decompositions

The chapter does not give procedural algorithms but provides constructive schemes:

- **Computing BPlA from bpa** (Theorem 24, Eq. 9.3): for each `A≠∅`, set `μ(A) = (-1)^{|A|+1} Σ_{C⊇A} m(C)`. `μ(∅) = 0`.
- **Computing basic commonality from `Bel`** (Eq. 9.7): `q(B) = (-1)^{|B|} Bel(B^c)`.
- **Plausibility-space vertex computation** (Eq. 9.11): `Pl_A = -Σ_{∅⊊B⊆A}(-1)^{|B|} Bel_B`.
- **Pignistic decomposition** (Eq. 10.11) — natural decomposition of `Bel` into consistent components, foreshadowing Chapter 14's consistent approximation algorithm; minimisation `BetP[b] = arg min_{P∈P} d(P,Bel)` for any distance `d` whose convex coordinates of `Bel` in `P^{Bel}` coincide with pignistic values *(p.426)*.

## Parameters / quantities

| Name | Symbol | Domain/Units | Default | Range | Page | Notes |
|------|--------|--------------|---------|-------|------|-------|
| Frame cardinality | `n = |Θ|` | ℕ | — | finite | 389 | Powerset has `N=2^n` elements |
| Reference-frame dimension | `N` | ℕ | `2^n` | — | 393 | Includes `∅` and `Θ` for unnormalised |
| BPlA | `μ(A)` | ℝ | — | unbounded sign | 391 | Möbius inverse of `Pl`; `Σ_A μ(A)=1`, can be `<0` |
| Basic commonality | `q(B)` | ℝ | — | unbounded sign | 393 | `q(∅)=1`; `Σ_B q(B) = m(Θ)`, **not** normalised to 1 |
| `p`-norm | `‖·‖_p` | ℝ_{≥0} | — | `p∈{1,2,...,∞}` | 399 | Used for congruence theorems |
| Internal conflict | `c(Bel)` | [0,1] | 0 | `c=0` ⇔ consistent | 422 | Pairwise mass on disjoint focals |
| Consonant maximal-simplex count | — | ℕ | `n!` | — | 413 | Number of maximal chains |
| Consonant simplex dimension | `dim Cl(Bel_{A_1},...,Bel_{A_n})` | ℕ | `n-1` | — | 413 | All maximal components |
| Consistent maximal-simplex count | — | ℕ | `n` | — | 423 | One per singleton `x∈Θ` |
| Consistent maximal-simplex vertices | — | ℕ | `2^{n-1}` | — | 423 | `dim = 2^{n-1}-1` |
| Pignistic prob | `BetP[Bel](x)` | [0,1] | — | `Σ_x BetP=1` | 424 | `Σ_{A∋x} m(A)/|A|` |

## Worked examples

### Example 20: basic plausibility assignment (binary) *(p.391)*

`Θ_2 = {x,y}`, `m(x)=1/3`, `m(Θ)=2/3`. Computing via (9.1):
`μ(x) = (-1)^{|x|+1}(m(x)+m(Θ)) = +1`. `μ(y) = (-1)^{|y|+1} m(Θ) = +2/3`. `μ(Θ) = (-1)^{|Θ|+1} m(Θ) = -2/3 < 0`. Sum = `1+2/3-2/3 = 1` ✓ normalised, but `μ(Θ)<0` confirming non-negativity fails.

### Example 21: belief and plausibility spaces in the binary case *(p.395)*

`Bel = [m(x), m(y)]'`, `Pl = [1-m(y), 1-m(x)]'`. `B_2 = Cl(Bel_∅=[0,0]', Bel_x=[1,0]', Bel_y=[0,1]')`, `PL_2 = Cl(Pl_Θ=[1,1]', Pl_x=[1,0]', Pl_y=[0,1]')`. Both are triangles, congruent via reflection through the Bayesian segment `P_2 = Cl(Bel_x, Bel_y)` (Fig. 9.1). Each `(Bel, Pl)` pair lies on a line orthogonal to `P_2` at symmetric positions.

### Example 22: commonality space in the binary case *(p.396)*

`Q_2 ⊂ ℝ^4` with `N=4` coordinates `[Q(∅), Q(x), Q(y), Q(Θ)]'`. `Q(∅)=1`, `Q(x)=Pl(x)`, `Q(y)=Pl(y)`, `Q(Θ)=m(Θ)`. Vertices: `Q_∅=[1,0,0,0]'`, `Q_x=[1,1,0,0]'`, `Q_y=[1,0,1,0]'`, `Q_Θ=[1,1,1,1]'`. Drawn (neglecting constant `Q(∅)`) as a 3D simplex (Fig. 9.2).

### Example 23: congruence in the binary case (unnormalised) *(p.400)*

For `n=2`, all of `B^U_2`, `PL^U_2`, `Q^U_2` are 3D simplices with 4 vertices in `ℝ^4`. Explicit listing (Eq. 9.13). Equality of `‖Bel_A - Bel_B‖_2` and `‖Pl_A - Pl_B‖_2` for matching pairs verifies congruence.

### Example 24: congruence of commonality and plausibility spaces *(p.401)*

In the *normalised* binary case, `PL_2` and `Q_2` are *not* congruent (`Q_2` is equilateral with `√2` sides, `PL_2` has two unit sides). In the *unnormalised* case, with vertex pairings `Q_Θ-Q_∅ = [0,1,1,1]' = Pl_Θ-Pl_∅`, etc. (Eq. 9.16), congruence holds.

### Example 25: ternary case (p.413)

`Θ={x,y,z}`. `Bel ∈ ℝ^6`. Six maximal chains listed. Six maximal convex components of `CO_3`, each of dimension 2 (a triangle), every singleton vertex shared by 2 of them.

### Example 26: congruence in the ternary case *(p.416–417)*

For `CO^{x,{x,y},Θ} = Cl(Bel_x, Bel_{xy}, Bel_Θ)`: side lengths `√3`, `1`, `√2`. Same triple of side lengths recurs for `CO^{x,{x,z},Θ}`, `CO^{y,{x,y},Θ}`, `CO^{z,{x,z},Θ}` — confirming pairwise congruence by Euclid's theorem.

### Example 27: consistent BFs in the binary frame *(p.422)*

`CS_2 = CS^{x,Θ} ∪ CS^{y,Θ} = Cl(Bel_Θ, Bel_x) ∪ Cl(Bel_Θ, Bel_y)`. *Coincides* with `CO_2` in the binary case — meaning every consistent BF on `Θ_2` is also consonant. They diverge for `n≥3`.

## Figures of interest

- **Fig. 9.1 (p.396):** Binary belief and plausibility spaces `B_2, PL_2` as congruent triangles in `ℝ^2`, symmetric across the Bayesian segment `P_2 = Cl(Bel_x, Bel_y)`. Each `(Bel, Pl)` pair lies on a line orthogonal to `P_2`. Visualises Theorem 28 + 30.
- **Fig. 9.2 (p.398):** Commonality space `Q_2` (neglecting constant `Q(∅)=1` axis), shown as a 3D simplex in `ℝ^3`.
- **Fig. 9.3 (p.403):** Pointwise rigid map `Bel ↦ Pl` instantiated in the binary case for normalised BFs (referenced in proof of Theorem 30).
- **Fig. 10.1 (p.412):** Binary consonant subspace `CO_2 = CS_2 = Cl(Bel_Θ, Bel_x) ∪ Cl(Bel_Θ, Bel_y)` shown as two segments inside the triangle `B_2`, with the probabilistic segment `P_2 = Cl(Bel_x, Bel_y)` as the third side.
- **Fig. 10.2 (p.414):** Ternary consonant complex `CO_3` — six triangular components inside the six-dimensional simplex `B_3`. Visualises both connectedness and right-angle structure.
- **Fig. 10.3 (p.415):** Pair of triangles in `ℝ^2` illustrating Definition 125 condition 2 — only the right-hand pair (intersecting in a face — a vertex) is a valid simplicial complex.
- **Fig. 10.4 (p.419):** Tetrahedron `Cl(Bel_{A_i}, Bel_{A_j}, Bel_{A_k}, Bel_{A_l})` for chain `A_i ⊊ A_j ⊊ A_k ⊊ A_l`, with all faces drawn as right triangles (Theorem 34 visualisation).
- **Fig. 10.5 (p.425):** Pictorial representation of `BetP[Bel]` and the role of consistent components — the simplex `P^{Bel} = Cl(Bel^x, x∈Θ)` sits inside the consistent complex `CS`, with `Bel` and `BetP[Bel]` being two distinct points sharing the same pignistic coordinates.

## Criticisms of prior work

- **Implicit critique of additive probability**: by exhibiting BPlA (`μ`) which is normalised but can be negative, Cuzzolin emphasises that "sum function on a power set" is a more general structural primitive than non-negative probability mass *(p.391)*.
- **(10.4) implicit critique**: Cuzzolin notes that under the dual implication `Bel ⊢ B ⇔ Pl(B)=1`, the *only* non-consistent BF is `Bel_∅` (the unnormalised vacuous one), which trivialises the notion. Hence (10.4) is rejected as too weak; (10.5) is preferred *(p.421)*.
- **Possibility theory as a *special case* of belief theory**: Cuzzolin frames possibility (`Pos = Pl` for consonant `Bel`) and necessity (`Nec = Bel` for consonant `Bel`) as *special* cases inside the broader DS landscape, not as an alternative or competitor framework — implicit critique of treating them as foundationally distinct *(p.409)*.

## Design rationale

- **Why introduce BPlA and basic commonality assignment at all?** They are useful for the probability transformation problem (Chapter 4 / Section 4.7.2; cited refs [1218, 1675, 1859, 1810, 100, 291, 333]) and for the canonical decomposition of support functions ([1698, 1052]). Two alternative combinatorial views complement the bpa-centric one *(p.389)*.
- **Why work in `ℝ^{N-2}` for `B` and `PL` but `ℝ^N` for `Q`?** Because `Bel(∅)=0` and `Bel(Θ)=1` are constants for normalised BFs (so 2 dimensions are redundant), but `Q(∅)=1` is constant *while* `Q(Θ)=m(Θ)` varies — only one constant axis to drop, and Cuzzolin chooses to keep both for symmetry, hence `Q ⊂ ℝ^N`. Section 9.4 explicitly walks through this *(p.396)*.
- **Why the "extended" reference frame `{v_A : ∅⊆A⊆Θ}` for unnormalised BFs?** Because in TBM, `m(∅)≠0` is meaningful, and `Bel_∅ = [1,0,...,0]' ≠ 0` must be a proper vertex of the simplex. Used throughout Section 9.3 *(p.394)*.
- **Why decompose via the pignistic transform (10.11)?** Because pignistic values `BetP[Bel](x)` are exactly the convex coordinates of `Bel` inside `P^{Bel} = Cl(Bel^x, x∈Θ) ⊂ CS`, providing a *natural*, *connected*, basis-aligned decomposition into consistent components — and serves as a launchpad for Chapter 14's consistent approximation problem *(p.424–425)*.
- **Why care about consistent BFs at all?** Because a non-consistent BF can imply both `B` and `B^c`, the BF analogue of an inconsistent classical KB. Working only with consistent BFs (analogous to maximal consistent subsets in non-classical logic — Paris [1389], Rescher–Manor) avoids this — *Internal conflict zero ⇔ consistent* (Theorem 36) gives a clean combinatorial criterion *(p.418–422)*.

## Open / research questions

Verbatim from Section 10.6 *(p.426)*:

- **Question 7.** "Can we extend the notion of a belief space to belief functions defined on fuzzy subsets of a frame of discernment?" *(p.426)* (Connects to MV algebras, coherent lower previsions on gambles.)
- **Question 8.** "The notion of consistency is central in imprecise probability (see Section 6.1): how does the concept of consistency for belief functions relate to the former?" *(p.426)*
- **Question 9.** "If consistency is desirable, for the reasons explained in Section 10.4, should we seek a combination rule able to preserve the consistency of a belief structure?" *(p.426)*

Closing remark: "The justification of consistent belief functions in terms of knowledge bases requires additional work, in the light of the extensive efforts conducted in the area of logic interpretation of the theory of evidence" *(p.426)*.

## Notable references cited

- `[347]` — basic plausibility/commonality combinatorial formulation *(p.389)*
- `[334], [333], [327]` — Cuzzolin's prior work on geometric belief-function theory *(p.389, 393)*
- `[1583]` — Shafer-style equivalence list of consonant BFs (5 conditions, p.409)
- `[531]` — Zadeh, on possibility measures *(p.409)*
- `[533, 930, 546, 91]` — consonant BFs as counterparts of necessity measures *(p.409)*
- `[551]` — simplicial complex definition *(p.414, 423)*
- `[1389]` — Paris, on inconsistent classical KBs and degree-of-belief approach *(p.419)*
- `[1267]` — propositional logic interpretation *(p.420)*
- `[1526], [767]` — generalising knowledge bases via belief on sets of interpretations *(p.420)*
- `[1944], [1730]` — pignistic transformation, Smets *(p.410, 424)*
- `[1196, 860, 1209]` — recent novel analyses of belief logic *(p.419)*
- `[2009, 1670, 1460]` — conflict and combinability in evidence theory *(p.419)*
- `[1440, 97]` — non-classical semantics for inconsistency-tolerant inference *(p.419)*
- `[328, 360, 345]` — original Cuzzolin papers re-elaborated in this chapter *(p.410)*
- `[1218, 1675, 1859, 1810, 100, 291, 333]` — probability transformation problem *(p.389)*
- `[1698, 1052]` — canonical decomposition of support functions *(p.389)*

## Implementation notes for propstore

This pair of chapters bears directly on several layers:

- **`propstore.world` (ATMS) and probabilistic argumentation**: BPlA, basic commonality, and pignistic transforms are the natural *coordinates* in which to express ATMS-derived bundles when their supports are Möbius-inverse-coupled. `Bel`, `Pl`, and `Q` should be treated as three faces of a single internal representation (a mass vector), with the rigid transformation (Theorem 30, Section 9.6) implemented as a closed-form map `Pl = 1 - Bel^c` and dual `Q_A = (-1)^{|A|} Bel(A^c)` — never as independent fits. Important guard: the basic commonality assignment `q` is *not* normalised; any code that consumes `q` must not assume `Σ q = 1`.
- **`propstore.belief_set` (AGM, Darwiche–Pearl)**: consistent belief functions (Theorem 35–36, Definition 126) are the BF-theoretic analogue of consistent classical KBs. The internal-conflict scalar `c(Bel) = Σ m(A)m(B), A∩B=∅` (Eq. 10.8) is a candidate "conflict" sensor for revision/contraction triggers — when `c(Bel) > 0`, the belief set is internally inconsistent and AGM-style contraction is required before further conditioning. The pignistic decomposition `Bel = Σ_x BetP[Bel](x) Bel^x` (Eq. 10.11) gives a principled "natural projection" of an inconsistent corpus onto the closest consistent components — directly relevant to IC merge / belief-set repair.
- **`propstore.defeasibility` (CKR-style exceptions)**: consistent-BF logic (Theorem 35) maps cleanly to "this proposition has support and its negation does not," which is the core CKR justification check. Using `Bel(B) ≠ 0 ⇒ Bel ⊢ B` as the implication relation (Eq. 10.5) gives a defeasible-logic-compatible reading.
- **`propstore.aspic_bridge`**: the consonant subspace's right-triangle decomposition (Theorem 34) is structurally analogous to chained ASPIC+ argument trees where each defeasible step extends a strictly-included support set — `A_i ⊋ A_j ⊋ A_k`. A consonant approximation could implement "principled simplification" of an argument graph by projecting onto the closest consonant component.
- **`propstore.storage` and provenance**: vacuous opinions, calibration, and the `vacuous` provenance tag map onto unnormalised BFs (`Bel_∅` plays the role of the vacuous opinion) — Cuzzolin's unnormalised setting (`B^U`, `PL^U`, `Q^U`) is the right home for these. A provenance-aware Bel should support both normalised and unnormalised storage.
- **Render layer / consonant approximation (Chapter 13–14 forward reference)**: Chapter 10's geometric structure of `CO` and `CS` is the input to the consonant- and consistent-approximation render policies. Concretely, given a stored `Bel`, the render layer can compute:
  - The closest consonant `Bel'` (some maximal `CO^C` simplex projection).
  - The pignistic decomposition `{Bel^x : x∈Θ}` as the natural consistent-component spread (Eq. 10.11).
  - The internal-conflict scalar `c(Bel)` as a "consistency health" signal exposed to the user.
- **`propstore.dimensions` / kind types**: nothing direct — Chapter 9–10 are abstract simplicial geometry, no QUANTITY/TIMEPOINT semantics involved.

## Quotes worth preserving

- "Possibility measures are, just like probability measures, a special case of belief functions when defined on a finite frame of discernment." *(p.409)*
- "Studying the geometry of consonant belief functions amounts therefore to studying the geometry of possibility." *(p.411)*
- "Belief, plausibility and commonality functions form simplices which can be moved onto each other by means of a rigid transformation, as a reflection of the equivalence of the associated models." *(p.402)*
- "A belief function can therefore be seen in this context as a generalisation of a knowledge base, i.e., a set of propositions together with their non-zero belief values." *(p.420)*
- "If `A_i ⊋ A_j ⊋ A_k`, then `Bel_{A_i} \widehat{Bel_{A_j}} Bel_{A_k} = π/2`." *(Theorem 34, p.418)* — every triangle in a consonant chain is a right triangle.
- "A belief function `Bel : 2^Θ → [0,1]` is consistent if and only if its internal conflict is zero." *(Theorem 36, p.422)*
- "Each pair of belief/plausibility functions `(Bel,Pl)` determines a line `a(Bel,Pl)` which is orthogonal to `P`, on which they lie in symmetric positions on the two sides of the Bayesian segment." *(p.396)*

---

**Coverage note:** Pages 446 (book p.430, Part III opener) and 447–455 (book p.431+, beginning of Chapter 11 "Probability transforms: The affine family") fall outside the Chapter 9–10 scope of this chunk and are owned by the next chunk reader. They were inspected to confirm chapter boundaries but not extracted here.
