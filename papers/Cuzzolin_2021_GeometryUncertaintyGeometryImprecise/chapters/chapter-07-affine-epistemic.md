# Chunk #7 — Chapter 11 (Probability transforms: the affine family) + Chapter 12 (Probability transforms: the epistemic family)

**Book pages:** 431–516
**PDF idx:** 456–541 (assignment); actual content covered: PDF 447–532 (book p.431 = PDF 447, offset 16, not 25; PDF 533–541 are Chapter 13 opener which is owned by the next chunk reader)

## Sections covered

- 11 — Probability transforms: The affine family (book p.431 opener) *(p.431)*
- 11.1 Affine transforms in the binary case *(p.433)*
- 11.2 Geometry of the dual line *(p.435)*
  - 11.2.1 Orthogonality of the dual line *(p.436)*
  - 11.2.2 Intersection with the region of Bayesian normalised sum functions *(p.436)*
- 11.3 The intersection probability *(p.438)*
  - 11.3.1 Interpretations of the intersection probability *(p.439)*
  - 11.3.2 Intersection probability and affine combination *(p.444)*
  - 11.3.3 Intersection probability and convex closure *(p.447)*
- 11.4 Orthogonal projection *(p.447)*
  - 11.4.1 Orthogonality condition *(p.448)*
  - 11.4.2 Orthogonality flag *(p.449)*
  - 11.4.3 Two mass redistribution processes *(p.449)*
  - 11.4.4 Orthogonal projection and affine combination *(p.451)*
  - 11.4.5 Orthogonal projection and pignistic function *(p.452)*
- 11.5 The case of unnormalised belief functions *(p.453)*
- 11.6 Comparisons within the affine family *(p.455)*
- Appendix: Proofs (Theorems 39–52, Lemmas 9–11) *(pp.457–467)*
- 12 — Probability transforms: The epistemic family (book p.469 opener) *(p.469)*
- 12.1 Rationale for epistemic transforms *(p.471)*
  - 12.1.1 Semantics within the probability-bound interpretation *(p.472)*
  - 12.1.2 Semantics within Shafer's interpretation *(p.473)*
- 12.2 Dual properties of epistemic transforms *(p.474)*
  - 12.2.1 Relative plausibility, Dempster's rule and pseudo-belief functions *(p.475)*
  - 12.2.2 A (broken) symmetry *(p.475)*
  - 12.2.3 Dual properties of the relative belief operator *(p.476)*
  - 12.2.4 Representation theorem for relative beliefs *(p.479)*
  - 12.2.5 Two families of Bayesian approximations *(p.481)*
- 12.3 Plausibility transform and convex closure *(p.481)*
- 12.4 Generalisations of the relative belief transform *(p.482)*
  - 12.4.1 Zero mass assigned to singletons as a singular case *(p.482)*
  - 12.4.2 The family of relative mass probability transformations *(p.484)*
  - 12.4.3 Approximating the pignistic probability and relative plausibility *(p.485)*
- 12.5 Geometry in the space of pseudo-belief functions *(p.489)*
  - 12.5.1 Plausibility of singletons and relative plausibility *(p.489)*
  - 12.5.2 Belief of singletons and relative belief *(p.490)*
  - 12.5.3 A three-plane geometry *(p.491)*
  - 12.5.4 A geometry of three angles *(p.493)*
  - 12.5.5 Singular case *(p.496)*
- 12.6 Geometry in the probability simplex *(p.497)*
- 12.7 Equality conditions for both families of approximations *(p.504)*
  - 12.7.1 Equal plausibility distribution in the affine family *(p.504)*
  - 12.7.2 Equal plausibility distribution as a general condition *(p.505)*
- Appendix: Proofs (Theorems 53–67, Lemmas 12–13, Corollaries 13–14) *(pp.506–516)*

## Chapter overview

Chapters 11 and 12 jointly answer the question "given a belief function `Bel`, what is the *right* probability measure to use as its summary?" by classifying probability transforms into two structurally distinct families. Chapter 11 isolates the **affine family**, characterised by commutation with affine combinations of belief functions (Smets's *linearity* axiom): its members are the **pignistic function `BetP[Bel]`**, the **intersection probability `p[Bel]`** introduced here as the unique Bayesian belief function obtained by intersecting the dual line `a(Bel,Pl)` with the affine hull `P'` of Bayesian NSFs, and the **orthogonal projection `π[Bel]`** of `Bel` onto the probability simplex `P`. Chapter 12 isolates the **epistemic family**, characterised by commutation with Dempster's rule of combination (in some form): its members are the **relative plausibility `Pl̃`** and **relative belief `B̃el` of singletons**. Cuzzolin's central thesis is that these two families are *not* substitutes; they are two answers to two different questions ("preserve linear convex structure" vs. "preserve evidence combination"), and the choice of transform is therefore a structured design decision, not a free parameter.

The chapter pair is pedagogically organised around three layers: (1) the **binary case** (`Θ = {x,y}`), where in `R²` all transforms collapse to one point — the centre of `P[Bel]` — but the *geometry* (dual line, orthogonality, segment of consistent probabilities) is fully exposed; (2) the **general finite case**, where the dual line `a(Bel,Pl)` remains orthogonal to `P` (Theorem 39) but generally fails to intersect `P` itself, intersecting only the larger affine hull `P'` of Bayesian NSFs in the point `ς[Bel]` whose Bayesian belief is `p[Bel]`; (3) **equality conditions** (Section 12.7), where the conditions under which all transforms collapse to a single probability are derived in terms of equal plausibility distribution `Pl(x;k) = const` over focal-element sizes.

The argument has three theoretical pivots. First, a *duality table* (Section 12.2.5) showing that swapping `Bel ↔ Pl` and `P̃l ↔ B̃el` exchanges the affine and epistemic perspectives — the relative belief of singletons is itself the relative plausibility of singletons of the associated plausibility function `Pl`, viewed as a pseudo-belief function. Second, a *broken symmetry*: the relative belief `B̃el` does not exist whenever `Σ_x m(x) = 0`, while `P̃l` always exists, motivating the *relative mass transformations* `m̃_s` of level `s` (Definition 127) as a generalisation. Third, the **three-plane / three-angle geometry** in `B`: `Pl̃` and `B̃el` are determined by three planes through the duals (`Pl̄, P̂l, P̃l̄, B̄el, B̂el, B̃el`) and three angles `φ₁,φ₂,φ₃[Bel]` whose vanishing characterise the orthogonality, the alignment with `Pl_Θ = 1`, and the coincidence of `B̃el = P̃l`, respectively.

The chapter pair sets up the comparison-and-evaluation framework that Chapters 13–15 (consonant approximation, geometric conditioning, decision making) will exploit; in particular the orthogonality flag `O[Bel]`, the relative-mass family, and the geometric reduction of the epistemic family to a planar object are reused. Cuzzolin frames this as a research-programme statement: "the choice of probability transform is a structured design space" (paraphrased), and provides exhaustive sufficient conditions under which the design space collapses.

## Definitions

### Probability transform `PT` *(p.431)*
A mapping `PT : B → P, Bel ∈ B ↦ PT[Bel] ∈ P`, such that an appropriate distance/similarity measure `d` from `Bel` is minimised: `PT[Bel] = arg min_{P∈P} d(Bel, P)` *(Eq. 11.1)*.

### Affine space `a(v₁, …, v_k)` *(p.435, footnote)*
The affine subspace of `R^m` generated by points `v₁, …, v_k`: `a(v₁,…,v_k) = {v ∈ R^m : v = α₁v₁ + ⋯ + α_k v_k, Σ α_i = 1}`.

### Region of Bayesian NSFs `P'` *(p.435)*
`P' = {ς ∈ R² : m_ς(x) + m_ς(y) = 1} = a(P)`, the affine hull of the Bayesian simplex `P` in the binary case; in general `P' = {ς = Σ_{A⊂Θ} m_ς(A) Bel_A ∈ R^{N−2} : Σ_{|A|=1} m_ς(A) = 1, Σ_{|A|>1} m_ς(A) = 0}` *(Eq. 11.8)*.

### Bayesian NSF `ς[Bel]` *(p.437, Eq. 11.7)*
`ς[Bel] ≐ Bel + β[Bel](Pl − Bel) = a(Bel,Pl) ∩ P'`, the unique intersection of the dual line `a(Bel,Pl)` with the affine hull of Bayesian NSFs. Mass: `m_{ς[Bel]}(x) = m(x) + β[Bel] Σ_{A⊋x} m(A)` *(Eq. 11.9)*.

### Coordinate `β[Bel]` of `ς[Bel]` on the dual line *(p.437, Eq. 11.10)*
`β[Bel] = (1 − Σ_{x∈Θ} m(x)) / Σ_{x∈Θ} (Pl(x) − m(x)) = (Σ_{|B|>1} m(B)) / (Σ_{|B|>1} m(B)|B|)`.

### Intersection probability `p[Bel]` *(p.438, Eq. 11.12)*
The Bayesian belief function `p[Bel] ≐ Σ_{x∈Θ} m_{ς[Bel]}(x) Bel_x`, with mass `m_{p[Bel]}(x) = m_{ς[Bel]}(x)` on singletons and zero elsewhere. Equivalent forms (Eq. 11.14, p.439): `p[Bel](x) = m(x) + (1 − k_{Bel}) R[Bel](x) = m(x) + β[Bel](Pl(x) − m(x))`.

### Non-Bayesianity contribution `R[Bel](x)` (also called *probability flag* / relative uncertainty in the probabilities of singletons) *(p.440, p.494)*
`R[Bel](x) = Σ_{A⊋x} m(A) / Σ_{|A|>1} m(A)|A| = (Pl(x) − m(x)) / (k_{Pl} − k_{Bel})`. It indicates how much the uncertainty `Pl(x) − m(x)` in the probability value of `x` "weighs" in the total uncertainty.

### Total mass and total plausibility of singletons *(throughout)*
`k_{Bel} ≐ Σ_{x∈Θ} m(x)`; `k_{Pl} ≐ Σ_{x∈Θ} Pl(x) = Σ_{A⊆Θ} m(A)|A|`.

### Pignistic function `BetP[Bel]` *(p.435, Eq. 11.2)*
`BetP[Bel] = Σ_{x∈Θ} Bel_x Σ_{A⊃x} m(A)/|A|` (Smets). In the binary frame: `BetP[Bel] = Bel_x(m(x) + m(Θ)/2) + Bel_y(m(y) + m(Θ)/2)`.

### Auxiliary mass form `β'[Bel_A]` *(p.441)*
`β'[Bel_A] = (Σ_{|B|>1} m(B)) / (Σ_{|B|>1} m(B)|B|) = 1/|A|` for the pignistic function (constant in `A`).

### Auxiliary `T[Bel₁, Bel₂]` *(p.444, Eq. 11.20)*
`T[Bel₁, Bel₂](x) ≐ D̂₁ p[Bel₂, Bel₁] + D̂₂ p[Bel₁, Bel₂]` with `D̂_i ≐ D_i/(D₁ + D₂)` and `p[Bel_i, Bel_j](x) ≐ m_i(x) + β[Bel_j](Pl_i(x) − m_i(x))` *(Eq. 11.21)*.

### Orthogonality flag `O[Bel]` *(p.449, Eq. 11.28)*
`O[Bel](x) = Ō[Bel](x)/k_O[Bel] = (Σ_{A∋x} m(A) 2^{1−|A|}) / (Σ_{A⊂Θ} m(A)|A| 2^{1−|A|}) = (Σ_{A∋x} m(A)/2^{|A|}) / (Σ_{A⊂Θ} m(A)|A|/2^{|A|})`. The Bayesian belief function `O[Bel]` measures the non-orthogonality of `Bel` with respect to `P`. Theorem 47: `π[Bel] = P̄(1 − k_O[Bel]) + k_O[Bel] · O[Bel]`.

### Mass redistributions `Bel_∥` and `Bel_{2∥}` *(p.449)*
- `Bel_∥ ≐ (1/k_∥) Σ_{A⊂Θ} (m(A)/|A|) Bel_A` — redistributes mass of each focal element equally among its singletons (yields `BetP[Bel]` as relative plausibility of singletons).
- `Bel_{2∥} ≐ (1/k_{2∥}) Σ_{A⊂Θ} (m(A)/2^{|A|}) Bel_A` — redistributes mass equally among all subsets `B ⊆ A` (yields the orthogonality flag `O[Bel]` as relative plausibility of singletons).

### Unnormalised belief function (UBF) framework *(p.453)*
UBFs are belief functions admitting `m(∅) ≠ 0`. Coordinates use `N = 2^{|Θ|}` basis vectors `{Bel_A ∈ R^N, ∅ ⊆ A ⊆ Θ}` including `Bel_∅ ≐ [1, 0, …, 0]'`. Implicability `b(A) = Σ_{∅⊆B⊆A} m(B) = Bel(A) + m(∅)` *(Eq. 11.32)*.

### Relative plausibility of singletons `P̃l` *(Section 4.7.2 recall)*
`P̃l(x) = Pl(x)/k_{Pl}`.

### Relative belief of singletons `B̃el` *(Section 4.7.2 recall, p.476 Eq. 12.6 generalised)*
`B̃el[Pl](x) ≐ m(x) / Σ_{y∈Θ} m(y) = m(x)/k_{Bel}`, defined when `k_{Bel} ≠ 0`. The dual relative-belief operator extends to plausibility functions/NSFs: `B̃el : PL → P, Pl ↦ B̃el[Pl]`.

### Limit of belief function `Bel^∞` *(p.475, Eq. 12.4)*
`Bel^∞ ≐ lim_{n→∞} Bel^n ≐ lim_{n→∞} Bel ⊕ ⋯ ⊕ Bel (n times)` (Dempster orthogonal sum of `Bel` with itself).

### Plausibility of singletons `P̄l` (pseudo-belief function) *(p.489)*
`P̄l : 2^Θ → [0,1]` with Möbius inverse `m̄_{P̄l}(x) = Pl(x) ∀x ∈ Θ`, `m̄_{P̄l}(Θ) = 1 − k_{Pl}`, `m̄_{P̄l}(A) = 0 ∀A : |A| ≠ 1, n`. Vector form: `P̄l = Σ_{x∈Θ} Pl(x) Bel_x + (1 − k_{Pl}) Bel_Θ = Σ_{x∈Θ} Pl(x) Bel_x` (since `Bel_Θ = 0`) *(Eq. 12.15)*.

### Belief of singletons `B̄el` (pseudo-belief function) *(p.490)*
`B̄el : 2^Θ → [0,1]` with mass `m̄_{B̄el}(x) = m(x)`, `m̄_{B̄el}(Θ) = 1 − k_{Bel}`, `m̄_{B̄el}(A) = 0 ∀A : |A| ≠ 1, n`. Vector form: `B̄el = Σ_{x∈Θ} m(x) Bel_x` *(Eq. 12.17)*.

### Duals `B̂el` and `P̂l` in the plausibility space *(p.491, Eq. 12.19)*
`B̂el = Σ_{x∈Θ} m(x) Pl_x + (1 − k_{Bel}) Pl_Θ = B̄el + (1 − k_{Bel}) Pl_Θ`,
`P̂l = Σ_{x∈Θ} Pl(x) Pl_x + (1 − k_{Pl}) Pl_Θ = P̄l + (1 − k_{Pl}) Pl_Θ`.

### Three angles `φ₁, φ₂, φ₃[Bel]` *(p.493, Eq. 12.23)*
`φ₁[Bel] = ∠(P̃l p[Bel] P̄l)` — angle at `p[Bel]` between segments to `P̃l` and `P̄l`.
`φ₂[Bel] = ∠(B̄el p[Bel] P̂l)` — angle at `p[Bel]` between `B̄el` and `P̂l` (top of three-plane diagram).
`φ₃[Bel] = ∠(B̃el B̄el_Θ P̃l)` — angle at `B̄el_Θ` between `B̃el` and `P̃l`.

### Relative uncertainty `R[Bel]` (probability function) *(p.494, Eq. 12.25)*
`R[Bel] ≐ Σ_{x∈Θ} (Pl(x) − m(x))/(k_{Pl} − k_{Bel}) Bel_x = (P̄l − B̄el)/(k_{Pl} − k_{Bel})`. The relative uncertainty in the probability values of the singletons.

### Relative mass transformation of level `s` (Definition 127) *(p.485)*
Given `Bel : 2^Θ → [0,1]` with BPA `m`, the relative mass transformation of level `s`, denoted `m̃_s`, is the unique transform mapping `Bel` to the probability `P(x) = (Σ_{A⊇{x}:|A|=s} m(A)) / (s · Σ_{A⊆Θ:|A|=s} m(A)) = Pl(x;s)/(s k^s)` *(Eq. 12.11)*. Equivalently, `Bel ↦ m̃_s` retains the size-`s` focal elements only and computes either their relative plausibility or pignistic transform (which yields the same result).

### Extended relative belief operator `B̃el^{ext}` *(p.486, Eq. 12.14)*
`B̃el^{ext}(x) ≐ (Σ_{A⊇{x}: |A|=min} m(A)) / (|A|_{min} · Σ_{A⊆Θ:|A|=min} m(A))`, where `min` is the smallest cardinality with non-zero mass. Reduces to standard `B̃el` whenever `Σ_x m(x) ≠ 0`.

### Lower chain measure (Definition 128, p.526; cited because it appears at chapter boundary)
A monotone set function `ν : S → [0,1]` is a *lower chain measure* if there exists a chain `C ⊂ S` containing `∅` and `Θ` such that `ν = (ν|_C)_* |_S`, i.e., `ν` is the inner extension of its restriction to the chain.

## Theorems, propositions, lemmas

### Lemma 9 *(p.436)*
`[Bel_y − Bel_x](A^c) = −[Bel_y − Bel_x](A)` for all `A ⊆ Θ`. Proof uses the case analysis of `Bel_B(A) = 1 ⟺ A ⊇ B`.

### Theorem 39 (Dual line orthogonal to P) *(p.436)*
`a(Bel − Pl) ⊥ a(P)`. The line connecting `Pl` and `Bel` is orthogonal to the affine space generated by the probability simplex. Proof in appendix uses Lemma 9 and the antisymmetry of the basis vectors `Bel_y − Bel_x`.

### Theorem 40 (coordinates of `ς[Bel]`) *(p.437, Eq. 11.9)*
The coordinates of `ς[Bel]` in the categorical reference frame `{Bel_x : x ∈ Θ}` are expressible in BPA: `m_{ς[Bel]}(x) = m(x) + β[Bel] Σ_{A⊋x} m(A)`, with `β[Bel]` from Eq. 11.10.

### Theorem 41 (when `ς[Bel]` is a Bayesian belief function) *(p.438)*
The Bayesian NSF `ς[Bel]` is a probability measure (`ς[Bel] ∈ P`) iff `Bel` is **2-additive** (`m(A) = 0 ∀ |A| > 2`). In that case, `Pl` is the reflection of `Bel` through `P`, and `ς[Bel] = (Bel + Pl)/2` is the *mean probability function*.

### Theorem 42 (Intersection probability vs pignistic) *(p.442)*
The intersection probability and pignistic function coincide for `Bel` whenever the focal elements of `Bel` have size 1 or `k` only (i.e. all non-singleton focal elements have a single common cardinality `k`). In particular this is true when `Bel` is 2-additive.

### Theorem 43 (Intersection probability under affine combination) *(p.444, Eq. 11.19)*
For `α₁, α₂ ∈ [0,1]`, `α₂ = 1 − α₁`:
`p[α₁ Bel₁ + α₂ Bel₂] = α̂₁D₁(α₁ p[Bel₁] + α₂ T[Bel₁,Bel₂]) + α̂₂D₂(α₁ T[Bel₁,Bel₂] + α₂ p[Bel₂])`,
with `α̂_iD_i = α_iD_i/(α₁D₁ + α₂D₂)`. Proof develops `β[α₁Bel₁+α₂Bel₂]` as a convex combination of `β[Bel_i]` with weights proportional to `α_iD_i`.

### Theorem 44 (Commutativity with convex closure) *(p.447)*
The intersection probability `p[·]` and convex closure `Cl(·)` commute iff `T[Bel₁,Bel₂] = D̂₁ p[Bel₂] + D̂₂ p[Bel₁]`, equivalently `β[Bel₁] = β[Bel₂]` *or* `R[Bel₁] = R[Bel₂]`. Geometrically: only when the two lines `l₁, l₂` are parallel to `a(p[Bel₁], p[Bel₂])`.

### Theorem 45 (Sufficient condition via cardinality ratios) *(p.447, Eq. 11.23)*
If `σ_l^l/σ_1^m = σ_2^l/σ_2^m ∀l, m ≥ 2` such that `σ_1^m, σ_2^m ≠ 0`, where `σ_k = Σ_{|B|=k} m(B)`, then `p[·]` and convex combination commute.

### Theorem 46 (Orthogonal projection in BPA) *(p.448)*
`π[Bel](x)` admits two equivalent forms:
- `π[Bel](x) = Σ_{A∋x} m(A) 2^{1−|A|} + Σ_{A⊂Θ} m(A)((1 − |A|2^{1−|A|})/n)` *(Eq. 11.26)*.
- `π[Bel](x) = Σ_{A∋x} m(A)((1 + |A^c|2^{1−|A|})/n) + Σ_{A∌x} m(A)((1 − |A|2^{1−|A|})/n)` *(Eq. 11.27)*.
The latter shows `π[Bel]` is non-negative (hence a probability), since `1 + |A^c| 2^{1−|A|} ≥ 0` and `1 − |A| 2^{1−|A|} ≥ 0`.

### Theorem 47 (Decomposition via orthogonality flag) *(p.449)*
`π[Bel] = P̄(1 − k_O[Bel]) + k_O[Bel] · O[Bel]`, where `P̄ = [1/n,…,1/n]'` is the uniform probability and `O[Bel]` is the orthogonality flag. Hence `π[Bel] ∈ Cl(P̄, O[Bel])` and `π[Bel] = P̄` iff `Bel ⊥ a(P)`.

### Theorem 48 (Orthogonality flag = relative plausibility of singletons of `Bel_{2∥}`) *(p.449)*
`O[Bel]` is the relative plausibility of singletons of `Bel_{2∥}`; `BetP[Bel]` is the relative plausibility of singletons of `Bel_∥`.

### Theorem 49 (`π` commutes with affine combination) *(p.451)*
If `α₁ + α₂ = 1`: `π[α₁ Bel₁ + α₂ Bel₂] = α₁ π[Bel₁] + α₂ π[Bel₂]`.

### Lemma 11 (orthogonal projection of categorical BF) *(p.451)*
`π[Bel_A] = (1 − |A| 2^{1−|A|}) P̄ + |A| 2^{1−|A|} P̄_A`, with `P̄_A = (1/|A|) Σ_{x∈A} Bel_x`.

### Theorem 50 (`π[Bel]` as convex combination of `P̄_A`s) *(p.452, Eq. 11.29)*
`π[Bel] = P̄(1 − Σ_{A≠Θ} α_A) + Σ_{A≠Θ} α_A P̄_A`, with `α_A ≐ m(A)|A| 2^{1−|A|}`.

### Proposition 57 (Intersection probability domain) *(p.455)*
The intersection probability `p[Bel]` is well defined for *classical* (normalised) belief functions only.

### Proposition 58 (Dual line for UBFs) *(p.455)*
The dual line `a(Bel,Pl)` is orthogonal to `P` for each unnormalised belief function `Bel`, although `ς[Bel] = a(Bel,Pl) ∩ P'` exists iff `Bel` is classical (`m(∅) = 0`) or (trivially) `Bel ∈ P`.

### Proposition 59 (`p[Bel] = π[Bel]` if 2-additive) *(p.455)*
Sufficient condition: `Bel` 2-additive ⟹ `p[Bel] = π[Bel]`.

### Proposition 60 (`p[Bel] = BetP[Bel]` if 1-and-`k`-only support) *(p.456)*
If `∃ k ∈ [2, …, n]` such that `σ^i = 0 for all i ≠ k`, then `p[Bel] = BetP[Bel]`.

### Theorem 51 (`BetP[Bel] = p[Bel]` when masses are equal-per-size) *(p.456, Eq. 11.34)*
If `m(A) = const ∀ A : |A| = k`, for all `k = 2, …, n`, then `BetP[Bel] = p[Bel]`.

### Theorem 52 (Same condition gives `π[Bel] = p[Bel]`) *(p.456)*
The condition `m(A) = const ∀A : |A| = k`, `∀k = 2, …, n`, is also sufficient for `π[Bel] = p[Bel]`.

### Proposition 61 (Maxima of `‖p − BetP‖_p`) *(p.456)*
For `Bel` on a ternary frame, `‖p[Bel] − BetP[Bel]‖_p` has three maxima with BPAs:
`m₁ = [0, 0, 0, 3 − √6, 0, 0, √6 − 2]'`,
`m₂ = [0, 0, 0, 0, 3 − √6, 0, √6 − 2]'`,
`m₃ = [0, 0, 0, 0, 0, 3 − √6, √6 − 2]'`,
regardless of `p ∈ {1, 2, ∞}`.

### Proposition 62 (Cobb–Shenoy properties of `P̃l`) *(p.475)*
1. `Bel = Bel₁ ⊕ ⋯ ⊕ Bel_m ⟹ P̃l = P̃l₁ ⊕ ⋯ ⊕ P̃l_m`.
2. If `m ⊕ m = m`, then `P̃l` is idempotent w.r.t. Bayes' rule.
3. If `∃x ∈ Θ : Pl(x) > Pl(y) ∀y ≠ x`, then `P̃l^∞(x) = 1`, `P̃l^∞(y) = 0 ∀y ≠ x`.
4. If `∃A ⊆ Θ, |A| = k`, with `Pl(x) = Pl(y) ∀x,y ∈ A` and `Pl(x) > Pl(z) ∀x ∈ A, z ∈ A^c`, then `P̃l^∞(x) = P̃l^∞(y) = 1/k ∀x,y ∈ A`, `P̃l^∞(z) = 0 ∀z ∈ A^c`.

### Proposition 63 (Voorbraak representation theorem) *(p.475)*
`Bel ⊕ P = P̃l ⊕ P, ∀P ∈ P`. The relative plausibility of singletons is a "perfect representative" of `Bel` in `P` under Dempster's rule.

### Theorem 53 (Relative belief inconsistency) *(p.473)*
The relative belief of singletons of a belief function `Bel` is not always consistent with `Bel` (i.e. may fall outside `P[Bel]`).

### Theorem 54 (Relative plausibility inconsistency) *(p.473)*
The relative plausibility of singletons of `Bel` is not always consistent with `Bel`.

### Theorem 55 (Cross-symmetry between `B̃el` and `P̃l`) *(p.476)*
For any `Bel, Pl : 2^Θ → [0,1]`, `B̃el[Bel] = P̃l[Pl]`. The relative belief transform of `Bel` coincides with the (extended) plausibility transform of the associated `Pl` viewed as a pseudo-belief function.

### Theorem 56 (Relative belief commutes with Dempster of `Pl`s) *(p.477)*
`B̃el[Pl₁ ⊕ Pl₂] = B̃el[Pl₁] ⊕ B̃el[Pl₂]`. Critically, this commutation is for combinations of *plausibility* functions, not belief functions.

### Corollary 11 (`B̃el` idempotence dual) *(p.477)*
If `Pl ⊕ Pl = Pl`, then `B̃el[Pl] ⊕ B̃el[Pl] = B̃el[Pl]`.

### Theorem 57 (`B̃el` limit of dominant belief) *(p.477)*
If `∃x ∈ Θ : Bel(x) > Bel(y) ∀y ≠ x`, then `B̃el[Pl^∞](x) = 1`, `B̃el[Pl^∞](y) = 0 ∀y ≠ x`.

### Corollary 12 *(p.477)*
If `∃A ⊆ Θ, |A|=k` such that `Bel(x) = Bel(y) ∀x,y∈A`, `Bel(x) > Bel(z) ∀x ∈A, z ∈ A^c`, then `B̃el[Pl^∞](x) = B̃el[Pl^∞](y) = 1/k ∀x,y∈A`, `B̃el[Pl^∞](z) = 0 ∀z ∈ A^c`.

### Proposition 64 (Pseudo-belief closure under Dempster) *(p.476)*
Dempster's rule applied to a pair of pseudo-belief functions (NSFs) yields a pseudo-belief function.

### Proposition 65 (Dempster sum and affine combination) *(p.479, Eq. 12.10)*
`Bel ⊕ Σ_i α_i Bel_i = Σ_i γ_i (Bel ⊕ Bel_i)`, where `γ_i = α_i k(Bel, Bel_i) / Σ_j α_j k(Bel, Bel_j)`.

### Theorem 58 (Dual representation theorem) *(p.480)*
`B̃el ⊕ P = Pl ⊕ P, ∀ Bayesian P ∈ P`. The relative belief of singletons "perfectly represents" the *plausibility function* `Pl` (not `Bel`) when combined with any probability through extended Dempster's rule.

### Lemma 12 (`P̃l` and affine combination) *(p.482)*
For all `α ∈ R`: `P̃l[α Bel₁ + (1−α) Bel₂] = β₁ P̃l[Bel₁] + β₂ P̃l[Bel₂]`, where `β₁ = α k_{Pl₁}/(α k_{Pl₁} + (1−α) k_{Pl₂})`, `β₂ = (1−α) k_{Pl₂}/(α k_{Pl₁} + (1−α) k_{Pl₂})`.

### Theorem 59 (Plausibility transform commutes with convex closure) *(p.482)*
`P̃l[Cl(Bel₁, …, Bel_k)] = Cl(P̃l[Bel₁], …, P̃l[Bel_k])`.

### Theorem 60 (`P̃l` as line intersection in `B`) *(p.490)*
`P̃l` is the intersection of the line joining the vacuous belief function `Bel_Θ` with the plausibility of singletons `P̄l`, with the probability simplex: `P̃l = Cl(P̄l, Bel_Θ) ∩ P`.

### Theorem 61 (Three-plane / convex-line equation) *(p.491, Eq. 12.20)*
The line passing through the duals (Eq. 12.19) of the plausibility of singletons (12.15) and the belief of singletons (12.17) crosses `p[Bel]`, and `β[Bel](P̂l − B̂el) + B̂el = p[Bel] = β[Bel](P̄l − B̄el) + B̄el`.

### Theorem 62 (Orthogonality of `a(B̄el, P̄l)`) *(p.494)*
The line `a(B̄el, P̄l)` is orthogonal to the vector space generated by `P` (so `φ₁[Bel] = π/2`) iff `Σ_{A⊋{x}} m(A) = Pl(x) − m(x) = const ∀ x ∈ Θ`.

### Corollary 13 *(p.494)*
The line `a(B̄el, P̄l)` is orthogonal to `P` iff the relative uncertainty in the probabilities of singletons is the uniform probability: `R[Bel](x) = 1/|Θ| ∀ x ∈ Θ`.

### Theorem 63 (Angle `φ₂` formula) *(p.495, Eq. 12.26)*
With `1 = Pl_Θ = [1, …, 1]'`: `cos(π − φ₂[Bel]) = 1 − ⟨1, R[Bel]⟩ / ‖R[Bel]‖² · (something)` (full form `cos(π − φ₂) = (‖R[Bel]‖² − ⟨1, R[Bel]⟩) / (‖R[Bel]‖ √(‖R[Bel]‖² + ⟨1,1⟩ − 2⟨R[Bel], 1⟩))`). Encodes the relative-uncertainty dependence.

### Theorem 64 (`φ₂[Bel] ≠ 0` for non-trivial frames) *(p.495)*
`φ₂[Bel] ≠ 0` and the lines `a(B̄el, P̄l)`, `a(B̂el, P̂l)` never coincide for any `Bel ∈ B` whenever `|Θ| > 2`. Conversely, `φ₂[Bel] = 0 ∀Bel ∈ B` whenever `|Θ| ≤ 2`.

### Theorem 65 (Singular case: `R[Bel] = P̃l = p[Bel]`) *(p.497)*
If `Bel` does not admit a relative belief of singletons (`k_{Bel} = 0`), then its relative plausibility of singletons and intersection probability coincide, and the relative uncertainty equals both: `R[Bel] = P̃l = p[Bel]`.

### Lemma 13 (`π − BetP` decomposition) *(p.504, Eq. 12.31)*
`π[Bel](x) − BetP[Bel](x) = Σ_{A⊆Θ} m(A)((1−|A|2^{1−|A|})/n) − Σ_{A⊇{x}} m(A)((1−|A|2^{1−|A|})/|A|)`.

### Theorem 66 (Equality `π = BetP`) *(p.504, Eq. 12.32)*
`π[Bel] = BetP[Bel]` iff `Σ_{A⊇{x}} m(A)(1 − |A|2^{1−|A|})|A^c|/|A| = Σ_{A∌x} m(A)(1 − |A|2^{1−|A|}) ∀ x ∈ Θ`.

### Corollary 14 (Sufficient conditions for `BetP = π`) *(p.505)*
Each is sufficient:
1. `m(A) = 0 ∀ A ⊆ Θ : |A| ≠ 1, 2, n`.
2. Mass equally distributed within each size class for `k = 3, …, n−1`: `m(A) = (Σ_{|B|=k} m(B)) / C(n,k) ∀A : |A|=k`.
3. `Pl(x; k) = const = Pl(·; k) ∀ x, k = 3, …, n − 1`.

### Corollary 15 *(p.505)*
`BetP[Bel] = π[Bel]` for `|Θ| ≤ 3`.

### Corollary 16 *(p.505)*
If `Pl(x;k) = const` for all `x ∈ Θ` and all `k = 2, …, n−1`, then `a(B̄el, P̄l) ⊥ P`, and `R[Bel] = P̄`.

### Theorem 67 (Universal collapse) *(p.506, Eq. 12.35)*
If `Pl(x; k) = const = Pl(·; k)` for all `k = 1, …, n − 1`, then `Bel ⊥ P` and all probability transformations coincide: `P̃l = R[Bel] = π[Bel] = BetP[Bel] = P̄`.

## Equations

(Selected equations — every numbered equation in the chapter pair appears below; the ones above are referenced by their book numbering.)

$$
\mathcal{PT}[Bel] = \arg\min_{P\in\mathcal{P}} d(Bel, P)
$$
**(Eq. 11.1, p.431)** Generic distance-minimisation framing of probability transforms. `d` is any dissimilarity; output is the closest probability to `Bel`.

$$
BetP[Bel] = \sum_{x\in\Theta} Bel_x \sum_{A\supset x} \frac{m(A)}{|A|}
$$
**(Eq. 11.2, p.435)** Pignistic function. `m(A)` is the BPA, `|A|` the cardinality of the focal element.

$$
Bel_B(A) = \begin{cases} 1 & A \supseteq B \\ 0 & \text{otherwise} \end{cases}
$$
**(Eq. 11.3, p.436)** Categorical belief function focused on `B`.

$$
[Bel_y - Bel_x](A) = \begin{cases} 1 & A \supset \{y\}, A \not\supset \{x\} \\ 0 & A \supset \{x\},\{y\} \text{ or } A \not\supset \{x\},\{y\} \\ -1 & A \not\supset \{y\}, A \supset \{x\} \end{cases}
$$
**(Eq. 11.4, p.436)**

$$
Bel(x) + \alpha[Pl(x) - Bel(x)] = Bel(x) + \alpha[1 - Bel(\{x\}^c) - Bel(x)]
$$
**(Eq. 11.5, p.437)**

$$
\alpha = \frac{1 - \sum_{x\in\Theta} Bel(x)}{\sum_{x\in\Theta}[1 - Bel(\{x\}^c) - Bel(x)]} \doteq \beta[Bel]
$$
**(Eq. 11.6, p.437)** Line coordinate of `ς[Bel]` on `a(Bel, Pl)`.

$$
\varsigma[Bel] \doteq Bel + \beta[Bel](Pl - Bel) = a(Bel, Pl) \cap \mathcal{P}'
$$
**(Eq. 11.7, p.437)** Bayesian NSF associated with `Bel`.

$$
\mathcal{P}' = \left\{\varsigma = \sum_{A\subset\Theta} m_\varsigma(A) Bel_A \in \mathbb{R}^{N-2} : \sum_{|A|=1} m_\varsigma(A) = 1, \sum_{|A|>1} m_\varsigma(A) = 0\right\}
$$
**(Eq. 11.8, p.437)** Affine hull of Bayesian NSFs.

$$
m_{\varsigma[Bel]}(x) = m(x) + \beta[Bel] \sum_{A\supsetneq x} m(A)
$$
**(Eq. 11.9, p.437)** BPA of `ς[Bel]`.

$$
\beta[Bel] = \frac{1 - \sum_{x\in\Theta} m(x)}{\sum_{x\in\Theta}(Pl(x) - m(x))} = \frac{\sum_{|B|>1} m(B)}{\sum_{|B|>1} m(B)|B|}
$$
**(Eq. 11.10, p.437)**

$$
m_{\varsigma[Bel]}(x) = Bel(x) \frac{\sum_{|B|=1} m(B)}{\sum_{|B|=1} m_B(B)|B|} + [Pl - Bel](x) \frac{\sum_{|B|>1} m(B)}{\sum_{|B|>1} m(B)|B|}
$$
**(Eq. 11.11, p.438)** Symmetric form.

$$
p[Bel] \doteq \sum_{x\in\Theta} m_{\varsigma[Bel]}(x) Bel_x
$$
**(Eq. 11.12, p.438)** Intersection probability.

$$
k_{Bel} = \sum_{x\in\Theta} m(x), \quad k_{Pl} = \sum_{x\in\Theta} Pl(x) = \sum_{A\subseteq\Theta} m(A)|A|
$$
**(Eq. 11.13, p.439)**

$$
p[Bel](x) = m(x) + (1 - k_{Bel}) R[Bel](x)
$$
**(Eq. 11.14, p.439)** Distribution form: original mass plus a share of non-Bayesianity.

$$
p[Bel] = k_{Bel} \tilde{Bel} + (1 - k_{Bel}) R[Bel]
$$
**(Eq. 11.15, p.440)** Convex combination of relative belief of singletons and probability flag.

$$
\tilde{Pl} = \left(\frac{k_{Bel}}{k_{Pl}}\right) \tilde{Bel} + \left(1 - \frac{k_{Bel}}{k_{Pl}}\right) R[Bel]
$$
**(Eq. 11.16, p.440)** Decomposition of relative plausibility along `Cl(R[Bel], B̃el)`.

$$
p[Bel](x) = m(x) + \beta[Bel](Pl(x) - m(x))
$$
**(Eq. 11.17, p.441)** Re-expression as fraction of non-Bayesian contribution.

$$
m(x) = 0.1, m(y) = 0, m(z) = 0.2, m(\{x,y\}) = 0.3, m(\{x,z\}) = 0.1, m(\{y,z\}) = 0, m(\Theta) = 0.3
$$
**(Eq. 11.18, p.442)** Worked-example BPA.

$$
p[\alpha_1 Bel_1 + \alpha_2 Bel_2] = \widehat{\alpha_1 D_1}(\alpha_1 p[Bel_1] + \alpha_2 T[Bel_1, Bel_2]) + \widehat{\alpha_2 D_2}(\alpha_1 T[Bel_1, Bel_2] + \alpha_2 p[Bel_2])
$$
**(Eq. 11.19, p.444)** Affine-combination law for `p[·]`.

$$
T[Bel_1, Bel_2](x) \doteq \hat{D}_1 p[Bel_2, Bel_1] + \hat{D}_2 p[Bel_1, Bel_2]
$$
**(Eq. 11.20, p.444)** Auxiliary probability `T`.

$$
p[Bel_2, Bel_1](x) \doteq m_2(x) + \beta[Bel_1](Pl_2(x) - m_2(x))
$$
**(Eq. 11.21, p.444)** Cross-`β` intersection probability.

$$
\beta[Bel] = \frac{\sigma^2 + \cdots + \sigma^n}{2\sigma^2 + \cdots + n\sigma^n}, \quad \sigma^k \doteq \sum_{|B|=k} m(B)
$$
**(Eq. 11.22, p.447)** Decomposition of `β[Bel]` by focal-element size.

$$
\frac{\sigma_1^l}{\sigma_1^m} = \frac{\sigma_2^l}{\sigma_2^m} \quad \forall l, m \geq 2 \text{ s.t. } \sigma_1^m, \sigma_2^m \neq 0
$$
**(Eq. 11.23, p.447)** Sufficient ratio condition for `p[·]`-convex commute.

$$
v(\mathcal{P})^\perp = \left\{\mathbf{v} \mid \sum_{A\ni y, A\not\ni x} v_A = \sum_{A\ni x, A\not\ni y} v_A \,\forall y \neq x, x, y \in \Theta\right\}
$$
**(Eq. 11.24, p.448)** Orthogonal complement of `a(P)` in vector form.

$$
\sum_{B\ni y, B\not\ni x} m(B) 2^{1-|B|} = \sum_{B\ni x, B\not\ni y} m(B) 2^{1-|B|} \quad \forall y \neq x, x, y \in \Theta
$$
**(Eq. 11.25, p.448)** Belief-function orthogonality condition (`Bel ⊥ a(P)`).

$$
\pi[Bel](x) = \sum_{A\ni x} m(A) 2^{1-|A|} + \sum_{A\subset\Theta} m(A)\frac{1 - |A|2^{1-|A|}}{n}
$$
**(Eq. 11.26, p.448)** Orthogonal projection (form 1).

$$
\pi[Bel](x) = \sum_{A\ni x} m(A)\frac{1 + |A^c|2^{1-|A|}}{n} + \sum_{A\not\ni x} m(A)\frac{1 - |A|2^{1-|A|}}{n}
$$
**(Eq. 11.27, p.448)** Orthogonal projection (form 2 — manifestly non-negative).

$$
O[Bel](x) = \frac{\bar{O}[Bel](x)}{k_O[Bel]} = \frac{\sum_{A\ni x} m(A) 2^{1-|A|}}{\sum_{A\subset\Theta} m(A)|A|2^{1-|A|}} = \frac{\sum_{A\ni x} m(A)/2^{|A|}}{\sum_{A\subset\Theta} m(A)|A|/2^{|A|}}
$$
**(Eq. 11.28, p.449)** Orthogonality flag.

$$
\pi[Bel] = \overline{\mathcal{P}}\left(1 - \sum_{A\neq\Theta} \alpha_A\right) + \sum_{A\neq\Theta} \alpha_A \overline{\mathcal{P}}_A, \quad \alpha_A \doteq m(A)|A| 2^{1-|A|}
$$
**(Eq. 11.29, p.452)** `π[Bel]` as convex combination of category-A barycentres.

$$
\pi[Bel] = \sum_{A\subset\Theta} m(A) BetP[Bel_A], \quad \pi[Bel] = \sum_{A\not\equiv\Theta} \alpha_A BetP[Bel_A] + (1 - \sum_{A\neq\Theta} \alpha_A) BetP[Bel_\Theta]
$$
**(Eq. 11.30, p.452)** `π` as convex combination of pignistic functions of categorical belief functions, with size-1, size-2 weights.

$$
m(x) = 1/3, m(\{x,z\}) = 1/3, m(\Theta_3) = 1/3
$$
**(Eq. 11.31, p.453)** Ternary worked example.

$$
b(A) = \sum_{\emptyset \subseteq B \subseteq A} m(B) = Bel(A) + m(\emptyset)
$$
**(Eq. 11.32, p.454)** Implicability function for UBFs.

$$
\beta[Bel] = \frac{\sigma^2 + \cdots + \sigma^n}{2\sigma^2 + \cdots + n\sigma^n}
$$
**(Eq. 11.33, p.456)** Same as Eq. 11.22, restated for comparisons.

$$
m(A) = \text{const} \quad \forall A : |A| = k, \forall k = 2, \ldots, n
$$
**(Eq. 11.34, p.456)** Sufficient condition for `BetP[Bel] = p[Bel]` and `π[Bel] = p[Bel]`.

$$
[Pl - Bel](A^c) = [Pl - Bel](A)
$$
**(Eq. 11.35, p.457)** Antisymmetry of `Pl − Bel`.

$$
\mu(A) \sum_{|B|>1} m(B) + m(A) \sum_{|B|>1} m(B)(|B|-1) = 0 \quad \forall A : |A|>1
$$
**(Eq. 11.36, p.458)** Condition reduced via Möbius.

$$
[m(A) + \mu(A)] M_1[Bel] + m(A) M_2[Bel] = 0 \quad \forall A : |A|>1
$$
**(Eq. 11.37, p.458)** With `M_1[Bel] ≐ Σ_{|B|>1} m(B)`, `M_2[Bel] ≐ Σ_{|B|>2} m(B)(|B|-2)`.

$$
\beta[Bel] = \frac{M_1[Bel]}{M_2[Bel] + 2 M_1[Bel]}
$$
**(Eq. 11.38, p.459)**

$$
m_{\alpha_1 Bel_1 + \alpha_2 Bel_2}(x) + \beta[\alpha_1 Bel_1 + \alpha_2 Bel_2] \sum_{A \supsetneq \{x\}} m_{\alpha_1 Bel_1 + \alpha_2 Bel_2}(A)
$$
**(Eq. 11.39, p.459)** Expansion used in proof of Theorem 43.

(Equations 11.40, 11.41, 11.42, 11.43, 11.44, 11.45 are intermediate algebraic steps in proofs of Theorems 43, 44, 46, 47, 51, 52 — present on pp.460–467 — and are too long to reproduce verbatim but are captured implicitly by the theorem statements above.)

---

$$
\sum_{x\in\Theta} m(x) \neq 0
$$
**(Eq. 12.1, p.470)** Existence condition for `B̃el[Bel]`.

$$
m(x_1) = 0.01, m(\{x_2, \ldots, x_n\}) = 0.99
$$
**(Eq. 12.2, p.473)** Counterexample BPA showing `B̃el` inconsistency.

$$
\tilde{Bel}(x_1) = 1, \tilde{Bel}(x_i) = 0 \quad \forall i = 2, \ldots, n
$$
**(Eq. 12.3, p.473)** Resulting `B̃el` — clearly not consistent with any sensible probability bound on `Bel` from Eq. 12.2.

$$
Bel^\infty \doteq \lim_{n\to\infty} Bel^n \doteq \lim_{n\to\infty} Bel \oplus \cdots \oplus Bel
$$
**(Eq. 12.4, p.475)**

$$
\sum_{A\supseteq\{x\}} \mu(A) = m(x)
$$
**(Eq. 12.5, p.475)** Möbius identity used to show the cross-symmetry.

$$
\tilde{Bel}[Pl](x) \doteq \frac{m(x)}{\sum_{y\in\Theta} m(y)} \quad \forall x \in \Theta
$$
**(Eq. 12.6, p.476)** Dual form of relative belief operator.

$$
\tilde{Bel}[(Pl)^n] = (\tilde{Bel}[Pl])^n
$$
**(Eq. 12.7, p.477)**

$$
m(\{x,y\}) = 0.4, m(\{y,z\}) = 0.4, m(w) = 0.2
$$
**(Eq. 12.8, p.477)** Worked example BPA.

$$
\mu(x)=0.4, \mu(y)=0.8, \mu(z)=0.4, \mu(w)=0.2, \mu(\{x,y\})=-0.4, \mu(\{y,z\})=-0.4
$$
**(Eq. 12.9, p.477)** Möbius (BPlA).

$$
Bel \oplus \sum_i \alpha_i Bel_i = \sum_i \gamma_i (Bel \oplus Bel_i), \quad \gamma_i = \frac{\alpha_i k(Bel, Bel_i)}{\sum_j \alpha_j k(Bel, Bel_j)}
$$
**(Eq. 12.10, p.480)**

$$
P(x) = \frac{\sum_{A\supseteq\{x\}: |A|=s} m(A)}{\sum_{y\in\Theta} \sum_{A\supseteq\{y\}: |A|=s} m(A)} = \frac{\sum_{A\supseteq\{x\}: |A|=s} m(A)}{s \sum_{A\subseteq\Theta: |A|=s} m(A)}
$$
**(Eq. 12.11, p.485)** Relative mass transformation of level `s`.

$$
\tilde{Pl}(x) = \sum_s \alpha_s \tilde{m}_s(x), \quad \alpha_s = \frac{s k^s}{\sum_r r k^r} \propto s k^s
$$
**(Eq. 12.12, p.486)** Convex decomposition of `P̃l` into relative mass probabilities.

$$
BetP[Bel](x) = \sum_s \beta_s \tilde{m}_s(x), \quad \beta_s = k^s
$$
**(Eq. 12.13, p.486)**

$$
\tilde{Bel}^{ext}(x) \doteq \frac{\sum_{A\supseteq\{x\}: |A|=\min} m(A)}{|A|_{\min} \cdot \sum_{A\subseteq\Theta: |A|=\min} m(A)}
$$
**(Eq. 12.14, p.486)** Natural extension of relative belief.

$$
\overline{Pl} = \sum_{x\in\Theta} Pl(x) Bel_x + (1 - k_{Pl}) Bel_\Theta = \sum_{x\in\Theta} Pl(x) Bel_x
$$
**(Eq. 12.15, p.490)** Plausibility of singletons in `B`.

$$
p[Bel] = (1 - \beta[Bel]) \sum_{x\in\Theta} m(x) Bel_x + \beta[Bel] \sum_{x\in\Theta} Pl(x) Bel_x
$$
**(Eq. 12.16, p.490)** Convex form of `p[Bel]`.

$$
\overline{Bel} = \sum_{x\in\Theta} m(x) Bel_x + (1 - k_{Bel}) Bel_\Theta = \sum_{x\in\Theta} m(x) Bel_x
$$
**(Eq. 12.17, p.491)** Belief of singletons in `B`.

$$
p[Bel] = (1 - \beta[Bel]) \overline{Bel} + \beta[Bel] \overline{Pl}
$$
**(Eq. 12.18, p.491)** Crucial: `p[Bel]` is a convex combination of belief and plausibility of singletons.

$$
\widehat{Bel} = \overline{Bel} + (1 - k_{Bel}) Pl_\Theta, \quad \widehat{Pl} = \overline{Pl} + (1 - k_{Pl}) Pl_\Theta
$$
**(Eq. 12.19, p.491)** Duals in the plausibility frame.

$$
\beta[Bel](\widehat{Pl} - \widehat{Bel}) + \widehat{Bel} = p[Bel] = \beta[Bel](\overline{Pl} - \overline{Bel}) + \overline{Bel}
$$
**(Eq. 12.20, p.491)** `p[Bel]` lies on both lines `a(B̄el, P̄l)` and `a(B̂el, P̂l)`.

$$
\widetilde{Pl} - Bel_\Theta = \frac{\overline{Pl} - Bel_\Theta}{k_{Pl}}
$$
**(Eq. 12.21, p.493)**

$$
\widetilde{Pl} - Pl_\Theta = \frac{\widehat{Pl} - Pl_\Theta}{k_{Pl}}
$$
**(Eq. 12.22, p.493)**

$$
\phi_1[Bel] = \widehat{\widetilde{Pl}\,p[Bel]\,\overline{Pl}}, \quad \phi_2[Bel] = \widehat{\overline{Bel}\,p[Bel]\,\widehat{Pl}}, \quad \phi_3[Bel] = \widehat{\widetilde{Bel}\,Bel_\Theta\,\widetilde{Pl}}
$$
**(Eq. 12.23, p.493)** Three angles describing the geometry.

$$
\exists y \neq x \in \Theta \text{ s.t. } \langle \overline{Pl} - \overline{Bel}, Bel_y - Bel_x \rangle \neq 0
$$
**(Eq. 12.24, p.494)** Non-orthogonality condition.

$$
R[Bel] \doteq \sum_{x\in\Theta} \frac{Pl(x) - m(x)}{k_{Pl} - k_{Bel}} Bel_x = \frac{\overline{Pl} - \overline{Bel}}{k_{Pl} - k_{Bel}}
$$
**(Eq. 12.25, p.494)** Probability function of relative uncertainty.

$$
\cos(\pi - \phi_2[Bel]) = 1 - \frac{\langle 1, R[Bel]\rangle}{\|R[Bel]\|^2}
$$
**(Eq. 12.26, p.495)**

$$
R[Bel](x) = \frac{Pl(x) - m(x)}{k_{Pl} - k_{Bel}} = \frac{1}{k_{Pl} - k_{Bel}}\left(\frac{k_{Pl}}{k_{Bel}} m(x) - m(x)\right) = \frac{m(x)}{k_{Bel}}
$$
**(Eq. 12.27, p.496)** Under singular condition `kPl = kBel`-style relations: `R = B̃el`.

$$
R[Bel] = \widetilde{Bel} + \frac{k_{Pl}}{k_{Pl} - k_{Bel}}(\widetilde{Pl} - \widetilde{Bel})
$$
**(Eq. 12.28, p.498)** Collinearity of `B̃el, R[Bel], P̃l`.

$$
\{Bel : m(x) = 0.5, m(y) = 0.1, m(z) = 0, \sum_{|A|>1} m(A) = 0.4\}
$$
**(Eq. 12.29, p.500)** Set of belief functions sharing fixed singleton mass profile.

$$
Cl(p_1', p_2', p_3') = Cl([2/5, 2/5, 1/5]', [2/5, 1/5, 2/5]', [1/5, 2/5, 2/5]')
$$
**(Eq. 12.30, p.502)** Triangle of pignistic transforms in ternary frame for `m(Θ) = 1/2`.

(Eq. 12.31 = Eq. 12.45 are decomposition formulas for `π − BetP`, see Lemma 13 / Theorem 66 above.)

$$
\sum_{A\supseteq\{x\}} m(A)\left(1 - |A|2^{1-|A|}\right)\frac{|A^c|}{|A|} = \sum_{A\not\supseteq\{x\}} m(A)\left(1 - |A|2^{1-|A|}\right)
$$
**(Eq. 12.32, p.504)** Theorem 66 form.

$$
Pl(x; k) = \text{const} = Pl(\cdot; k)
$$
**(Eq. 12.33, p.505)** Equal-plausibility-distribution condition.

$$
\sum_{A\supsetneq\{x\}} m(A) = \sum_{k=2}^n \sum_{|A|=k, A\supset\{x\}} m(A) = m(\Theta) + \sum_{k=2}^{n-1} Pl(\cdot; k)
$$
**(Eq. 12.34, p.505)**

$$
\widetilde{Pl} = R[Bel] = \pi[Bel] = BetP[Bel] = \overline{\mathcal{P}}
$$
**(Eq. 12.35, p.506)** Universal collapse.

(Equations 12.36–12.46 are intermediate proof steps on pp.508–515.)

## Geometric structures

- **The dual line `a(Bel, Pl)`** — the affine line through the belief function and its associated plausibility, lying in the (`N − 2`)-dimensional Euclidean space (where `N = 2^n`). Always orthogonal to `a(P)` (Theorem 39). Generally fails to intersect `P` itself but intersects the larger affine hull `P'` of Bayesian NSFs in a single point `ς[Bel]`. *(p.435–438)*

- **Region `P'` of Bayesian NSFs** — line in `R²` for the binary case; affine hyperplane of dimension `n − 1` in general; its location is "across" `P` from the belief space.

- **Probabilistic simplex `P` and its hull `a(P)`** — the natural ambient for any probability transform.

- **Set `P[Bel]` of consistent probabilities** — `{P ∈ P : P(A) ≥ Bel(A) ∀A ⊂ Θ}`, the credal set; in the binary case it is a segment whose centre of mass is `BetP[Bel]`. *(p.435)*

- **Segment `Cl(R[Bel], B̃el)`** — segment in `B` containing both `p[Bel]` (with coordinate `k_{Bel}`) and `P̃l` (with coordinate `k_{Bel}/k_{Pl}`). Provides the geometric link between intersection probability and relative plausibility/belief.

- **Bayesian-NSF point `ς[Bel]`** — single intersection point of `a(Bel, Pl)` with `P'`; coordinates given by Eq. 11.9. Lives in `P'` but not in `P` unless `Bel` is 2-additive (Theorem 41).

- **Orthogonality flag `O[Bel]`** — Bayesian belief function on `Θ` measuring the non-orthogonality of `Bel` w.r.t. `P`. Lies in `Cl(P̄, π[Bel])` segment; coincides with `P̄` iff `Bel ⊥ a(P)`.

- **Polytope `Cl(P̄_A, A ⊆ Θ)` in `B`** — `π[Bel]` lies in this polytope as a convex combination with weights `α_A = m(A)|A| 2^{1−|A|}`.

- **Three-plane geometry of the epistemic family** *(p.491–493, Fig. 12.5)*:
  1. Plane `a(B̄el, p[Bel], B̂el) = a(P̄l, p[Bel], P̂l)` — top plane through duals of belief/plausibility of singletons.
  2. Plane `a(Bel_Θ, P̃l, Pl_Θ)` — plane containing relative plausibility.
  3. Plane `a(Bel_Θ, B̃el, Pl_Θ)` — plane containing relative belief.

- **Three angles `φ₁, φ₂, φ₃`** — independent geometric invariants of `Bel` characterising orthogonality/equality patterns; each has a distinct interpretation in degrees of belief.

- **`P̄l` (plausibility of singletons)** — pseudo-belief function at the boundary; on the line `a(Bel_Θ, P̄l)`, `P̃l` is the unique intersection with `P` (Theorem 60).

- **`B̄el` (belief of singletons)** — pseudo-belief function whose mass on `Θ` is `1 − k_{Bel}`; vector form: `B̄el = Σ m(x) Bel_x`.

- **Singular geometry** *(p.496, Fig. 12.7)* — when `k_{Bel} = 0`, the three planes collapse to a single planar configuration; `B̄el = Bel_Θ`, `B̂el = Pl_Θ`, and `p[Bel] = P̃l = R[Bel]`.

- **Probability simplex picture for ternary frames** *(p.499, Fig. 12.8; p.503, Fig. 12.9)* — relative plausibility `P̃l_i`, intersection probability `p[Bel_i]`, relative uncertainty `R[Bel_i]` and pignistic `BetP[Bel_i]` form correlated families; for fixed singleton-mass profile they live in dotted/dashed/solid triangles.

## Algorithms

The chapters do not present numbered algorithmic pseudocode but the following constructive procedures are explicit:

1. **Compute `p[Bel]`** *(p.438)*:
   - Compute `k_{Bel} = Σ_{x∈Θ} m(x)`.
   - Compute `β[Bel]` via Eq. 11.10.
   - For each `x`, set `m_{p[Bel]}(x) = m(x) + β[Bel] Σ_{A⊋x} m(A)`.

2. **Compute `π[Bel]`** *(p.448)* via Eq. 11.27 directly, OR via Theorem 47 by computing `O[Bel]` (Eq. 11.28), `k_O[Bel] = Σ_{A⊂Θ} m(A)|A| 2^{1−|A|}`, and convex-combining with `P̄`.

3. **Compute `O[Bel]` (orthogonality flag)** *(p.450)* via the redistribution `Bel_{2∥}`: for each focal element `A` with mass `m(A)`, redistribute as `m'(B) = m(A)/2^{|A|}` for each `B ⊆ A`; sum over `A`'s contributions to each singleton, divide by total singleton mass.

4. **Compute `BetP[Bel]`** *(p.435)*: standard Smets formula `BetP[Bel](x) = Σ_{A⊃x} m(A)/|A|`.

5. **Compute `P̃l`** *(p.490)*: `P̃l(x) = Pl(x)/k_{Pl}` with `k_{Pl} = Σ_x Pl(x)`.

6. **Compute `B̃el`** *(p.476)*: if `k_{Bel} ≠ 0`: `B̃el(x) = m(x)/k_{Bel}`. Else use `B̃el^{ext}` (Eq. 12.14) with smallest non-zero focal-element size.

7. **Relative mass `m̃_s` of level `s`** *(p.485)*: filter `Bel` to focal elements of size exactly `s`, then apply Eq. 12.11.

## Parameters / quantities

| Name | Symbol | Domain/Units | Default | Range | Page | Notes |
|------|--------|--------------|---------|-------|------|-------|
| Total mass of singletons | `k_{Bel}` | `[0, 1]` | — | `0 ≤ k ≤ 1` | 439 | `Σ m(x)`. Equals 0 in singular case |
| Total plausibility of singletons | `k_{Pl}` | `≥ 1` | — | `1 ≤ k_{Pl} ≤ n` | 439 | `Σ_x Pl(x)`; ≥ 1 always |
| Line coordinate of `ς[Bel]` | `β[Bel]` | `[0, 1]` | — | `0 ≤ β ≤ 1` | 437 | Eq. 11.10 |
| Non-Bayesianity contribution | `R[Bel](x)` | `[0, 1]` | — | probability | 440, 494 | "Probability flag" Eq. 11.14, also called "relative uncertainty" |
| Orthogonality flag | `O[Bel]` | probability | — | `O[Bel] ∈ P` | 449 | Eq. 11.28 |
| Orthogonality factor | `k_O[Bel]` | `[0, 1]` | — | `0 ≤ k_O ≤ 1` | 449 | Normalisation; `k_O[Bel] = 0 ⟺ Bel ⊥ P` ⟹ `π = P̄` |
| Mass-of-size-`k` totals | `σ^k`, `k^s` | `[0, 1]` | — | sum of `m` over size-`k` events | 447, 485 | `σ^k ≐ Σ_{|B|=k} m(B)` |
| Relative-mass coefficients | `α_s, β_s` | `[0, 1]` | — | `α_s = sk^s/Σ rk^r`, `β_s = k^s` | 486 | Convex weights for `P̃l` and `BetP` |
| Three angles | `φ₁, φ₂, φ₃` | radians | — | `[0, π]` | 493 | Geometric invariants |
| Mass of empty set | `m(∅)` | `[0, 1]` | 0 | UBF allows `> 0` | 453 | Indicator of internal conflict |
| Cardinality | `n = |Θ|` | `Z⁺` | — | `n ≥ 2` | throughout | Frame size |
| Power-set size | `N = 2^n` | `Z⁺` | — | — | 453 | Coordinate-vector dimension |

## Worked examples

### Example 28: intersection probability — ternary frame *(p.442)*
Frame `Θ = {x, y, z}`, BPA `m(x)=0.1, m(y)=0, m(z)=0.2, m({x,y})=0.3, m({x,z})=0.1, m({y,z})=0, m(Θ)=0.3`. Computed values:
- `μ` (BPlA via Eq. 9.1): `μ(x)=0.8, μ(y)=0.6, μ(z)=0.6, μ({x,y})=−0.6, μ({x,z})=−0.4, μ({y,z})=−0.3, μ(Θ)=0.3`.
- `k_{Bel} = 0.3`, so `β[Bel] = 0.7 / 1.7 ≈ 0.412`.
- `m_{ς[Bel]}(x) = 0.388`, `m_{ς[Bel]}(y) = 0.247`, `m_{ς[Bel]}(z) = 0.365` (with negative non-singleton components verifying that `ς[Bel]` is a NSF, not BF — sums: `−0.071 − 0.106 − 0.123 + 0.3 = 0`).
- `Pl(x) − m(x) = 0.7, Pl(y) − m(y) = 0.6, Pl(z) − m(z) = 0.4`. Therefore `R(x) = 0.7/1.7, R(y) = 0.6/1.7, R(z) = 0.4/1.7`.
- `p[Bel](x) = 0.1 + 0.7 · 0.7/1.7 ≈ 0.388`, `p[Bel](y) ≈ 0.247`, `p[Bel](z) ≈ 0.365`. **`p[Bel]` matches `ς[Bel]` restricted to singletons.**

**Takeaway:** Two equivalent interpretations of `p[Bel]`. (1) Each non-singleton mass `1 − k_{Bel} = 0.7` is split among singletons proportionally to `R(x)`. (2) Each `Pl(x) − m(x)` is split among singletons with the constant share `β[Bel]`.

### Example 29: orthogonality flag and orthogonal projection *(p.450)*
Same BPA. Computing the redistribution `m'(B) = m(A)/2^{|A|}` for all `B ⊆ A`: `m^U(x) = 0.1875, m^U(y) = 0.1125, m^U(z) = 0.1625`. Sum = 0.4625, so `k_O[Bel] = 0.4625`. After normalisation: `O[Bel] = [0.405, 0.243, 0.351]'`. Then `π[Bel] = P̄(1 − 0.4625) + 0.4625 · O[Bel] = [0.366, 0.291, 0.342]'`.

**Takeaway:** The orthogonal projection differs from `p[Bel] = [0.388, 0.247, 0.365]'`, reflecting the distinct redistribution principles (split among subsets vs. split proportional to non-Bayesianity).

### Example 30: unnormalised case — binary *(p.454)*
Coordinates use 4 dimensions: `Bel_∅ = [1,0,0,0]'`, `Bel_x = [0,1,0,1]'`, `Bel_y = [0,0,1,1]'`, `Bel_Θ = [0,0,0,1]'` and `Pl_∅ = [0,0,0,0]'`, etc. Noting `Bel(Θ) = 1 − m(∅) = Pl(Θ)`. Belief and plausibility spaces are *not* in the section `{v_Θ = 1}`, so `a(Bel, Pl)` no longer guaranteed to intersect `P'`. The line `a(Bel_∅, Pl_∅)` reduces to the origin.

### Example 31: ternary frame collapse *(p.456)*
For `|Θ| = 3`, `π[Bel] = BetP[Bel]` (universal in the ternary case). Hence checking `p[Bel] = π[Bel]` reduces to checking `p[Bel] = BetP[Bel]`. Maxima of `‖p − BetP‖_p` from Proposition 61 are the three "permutation extremes" with `m({x,y}) = 3 − √6 ≈ 0.55, m(Θ) = √6 − 2 ≈ 0.45`, etc.

### Example 32: lack of consistency *(p.473)*
`m(x_1) = 0.01`, `m({x_2, …, x_n}) = 0.99`. Real-world reading: poor person `x_1` has a small amount of money; potential heirs `x_2, …, x_n` are all candidates to inherit a fortune. Consistent probabilities include "0.99 to a single heir". But `B̃el(x_1) = 1`, `B̃el(x_i) = 0`. **Demonstrates `B̃el` discards essential evidence about heirs.**

### Example 33: numerical example for `B̃el ⊕` and `Pl ⊕` *(p.477)*
Frame `Θ = {x, y, z, w}`, BPA `m({x,y}) = 0.4, m({y,z}) = 0.4, m(w) = 0.2`. Computed `μ` (Eq. 12.9). Verifies Theorem 56: applying Dempster to `Pl ⊕ Pl` and computing `B̃el[Pl²]` produces `[0, 0, 0, 1]'`, equal to `B̃el ⊕ B̃el = [0, 0, 0, 1]'` (since `m(w) = 0.2` is the only singleton with mass). The example also computes `μ²`, `μ³` series and shows `Pl^∞ → P_w = 1`, `B̃el[Pl^∞] → 1` on `w`, confirming Theorem 57. **Important:** commutation is for plausibility-function combinations; for belief-function combinations the property fails (`Bel ⊕ Bel ≠ B̃el ⊕ B̃el`).

### Example 34: example continued — failure of `Bel ⊕ Bel` analogue *(p.480)*
Same example. `Bel² = Bel ⊕ Bel` has `m²({x,y}) = 0.16/0.68 = 0.235`, `m²({y,z}) = 0.235`, `m²(w) = 0.058`, `m²(y) = 0.47`. Hence `B̃el ⊕ B̃el (BPA on m²) = [0, 0.47/0.528, 0, 0.058/0.528]' ≠ [0,0,0,1]'`. Because `[Pl₁ ⊕ Pl₂] ≠ Pl_{Bel₁ ⊕ Bel₂}` in general.

### Example 35: scenario 1 (high-mass `Θ`, small mass on size-2 elements) *(p.487)*
`m({x,y}) = m({y,z}) = ε`, `m(Θ) = 1 − 2ε ≫ ε`. C1 (highest-coefficient class) selects `n = |Θ|` ⟹ uniform probability `p(w) = 1/n`. C2 (smallest non-zero focal-element size) selects size-2 elements. C2 produces a profile near `BetP, P̃l` which discriminates between `x, y, z, w`; C1 discards all evidence.

### Example 36: scenario 2 (highly conflicting size-2 evidence) *(p.488)*
`A, B` only, `|A| > |B|` and `m(A) ≫ m(B)`. C1 picks the larger `A` ⟹ uniform on `A`. C2 picks the smaller `B` ⟹ uniform on `B`. C1 favours support; C2 favours precision. Conclusion: C2 (`B̃el^{ext}`) is preferred when conflicting evidence makes larger focal elements "less reliable".

### Example 37: binary vs ternary frame *(p.495)*
Binary: `Pl(x) − m(x) = m(Θ) = Pl(y) − m(y)`, so `R[Bel] = (1/2)Bel_x + (1/2)Bel_y = P̄`. Hence `φ₂[Bel] = 0` for all binary `Bel`. Ternary: Even `Bel_Θ` does not satisfy condition 2: `R[Bel_Θ] = P̄`, but `⟨R[Bel_Θ], R[Bel_Θ]⟩ = 1/3 ≠ 1/2 ⟨1, R⟩ = 3/2`, so the angle is non-zero. **Demonstrates the geometric collapse is binary-specific.**

### Example 38: geometry in the three-element frame *(p.498)*
`Bel_1: m(x)=0.5, m(y)=0.1, m({x,y})=0.3, m({y,z})=0.1`. Pl-uncertainty widths: `Pl₁(x)−m(x) = 0.3, Pl₁(y)−m(y) = 0.4, Pl₁(z)−m(z) = 0.1`. `R[Bel₁](x) = 3/8, R[Bel₁](y) = 1/2, R[Bel₁](z) = 1/8`. Distance from uniform `P̄`: 0.073. `k_{Bel₁} = 0.6, k_{Pl₁} = 1.4, β[Bel₁] = 0.5`. `p[Bel₁] = [0.65, 0.3, 0.05]'`. Plotted as a "square" on the dotted-triangle edge in Fig. 12.8.

The example continues with `Bel_2: m(x)=0.5, m(y)=0.1, m({x,y})=0.4` (mass concentrated on a single non-singleton). Higher relative uncertainty in `R[Bel₂]`. And `Bel_3: m(x)=0.5, m(y)=0.1, m({x,y})=0.2, m({y,z})=0.2`. **Takeaway:** All three `Bel_i` share the same `B̃el = [5/6, 1/6, 0]'`, and `R[Bel_i]`, `P̃l_i`, `p[Bel_i]` lie on collinear chains through `B̃el` per Eq. 12.18 and Eq. 12.28.

### Example 39: singular case in three-element frame *(p.501)*
`m(x) = m(y) = m(z) = 0`. Then `P̃l(x) = (1 − m({y,z}))/(2 + m(Θ))`, etc. As `m(Θ)` varies from 0 to 1, the locus `Cl(p₁', p₂', p₃')` (Eq. 12.30) sweeps from a triangle to the uniform point. For `m(Θ) = 1/2`, the locus is `Cl([2/5, 2/5, 1/5]', [2/5, 1/5, 2/5]', [1/5, 2/5, 2/5]')`. **Confirms Theorem 65** (`R[Bel] = P̃l = p[Bel]` in the singular case).

## Figures of interest

- **Fig. 11.1 (p.434)** — In the binary frame, `Bel` and `Pl` lie symmetrically across the segment `P` of probabilities. The dual line is shown perpendicular to `P`. The pignistic, orthogonal projection, and intersection probability all coincide with the centre of `P[Bel]`.
- **Fig. 11.2 (p.439)** — Probability simplex `P` with `p[Bel]`, `R[Bel]`, `B̃el`, `P̃l` plotted; `P[Bel]` (consistent probabilities) and `P'` (Bayesian NSFs) shown.
- **Fig. 11.3 (p.441)** — Triangle showing the location of `p[Bel]` between `R[Bel]` and `B̃el`, with `P̃l` closer to `R[Bel]`.
- **Fig. 11.4 (p.443)** — Visualises Example 28: subsets of `Θ` with non-zero BPA (left), with non-zero BPlA where dashed ellipses indicate negative mass (middle); `p[Bel]`-mass (right).
- **Fig. 11.5 (p.445)** — Geometric construction of `p[α₁ Bel₁ + α₂ Bel₂]` as a point in `Cl(T[Bel₁,Bel₂], p[Bel₁], p[Bel₂])`.
- **Fig. 11.6 (p.446)** — Location of `T[Bel₁, Bel₂]` in `B₂` via the trigonometric construction `Cl(Bel₁, Pl₂) ∩ P = Cl(Bel₂, Pl₁) ∩ P`.
- **Fig. 11.7 (p.450)** — Two redistribution processes: top, pignistic distributes mass `m(A)` among elements of `A`; bottom, orthogonal projection (via flag) distributes `m(A)` among all subsets `B ⊆ A`.
- **Fig. 11.8 (p.452)** — `π[Bel]` and `BetP[Bel]` in the simplex of barycentres `P̄_A`. Both are convex combinations; `π` weights size-1 vertices by `|A|2^{1-|A|}` (less than the pignistic weight `1` for `|A|>2`).
- **Fig. 11.9 (p.454)** — Ternary case showing `π[Bel] = BetP[Bel]` for ternary frames (Example 31).
- **Fig. 12.1 (p.478)** — Intersection table of focal elements in `BPlA ⊕ BPlA` for Example 33.
- **Fig. 12.2 (p.483)** — (Left) `B̃el` location in the binary case; (right) ternary singular region as a triangle delimited by dashed lines.
- **Fig. 12.3 (p.488)** — Scenario 1 belief function (left); pignistic + relative plausibility profile (right).
- **Fig. 12.4 (p.488)** — Scenario 2 with `m(A), m(B)`, `|A| > |B|`, `m(A) ≫ m(B)`.
- **Fig. 12.5 (p.492)** — Three planes and three angles describing geometry of `P̃l` and `B̃el` in `B`. The figure shows `P̄l, P̂l, B̄el, B̂el, P̃l, B̃el, p[Bel]` with the three angles `φ_1, φ_2, φ_3`.
- **Fig. 12.6 (p.496)** — In the binary frame, `R[Bel] = P̄ = (1/2)Pl_Θ` for all `Bel`, so the angle `φ₂[Bel] = 0`.
- **Fig. 12.7 (p.497)** — Singular-case planar geometry when `k_{Bel} = 0`. `B̄el = Bel_Θ`, `B̂el = Pl_Θ`, `p[Bel] = P̃l = R[Bel]` collapse.
- **Fig. 12.8 (p.499)** — Probability simplex location of the epistemic family for the three example BFs (`Bel₁, Bel₂, Bel₃`) of Example 38, showing dashed/dotted/solid triangles.
- **Fig. 12.9 (p.503)** — Singular ternary case: locations of `p[Bel]`, `P̃l`, `BetP[Bel]`, and the triangle defined by `(12.30)` for `m(Θ) = 1/2`.

## Criticisms of prior work

- **Probability-bound interpretation** *(p.473, Section 12.1.1)*: Cuzzolin proves that both `P̃l` and `B̃el` are not consistent with `Bel` in the probability-bound interpretation (Theorems 53, 54), because they come from "jointly assuming a number of incompatible redistribution processes" — i.e. each singleton uses a different mass-reassignment strategy. The pignistic transform alone is consistent (it uses the principle of insufficient reason: equal split among elements of each focal set).

- **Smets's claim that pignistic is unique under linearity** *(p.481)*: "Incidentally, there seems to be a flaw in Smets's argument that the pignistic transform is uniquely determined as the probability transformation which commutes with affine combination". Cuzzolin counters that the orthogonal projection `π[Bel]` *also* commutes with affine combination (Theorem 49) — so linearity does not uniquely determine `BetP`. Hence Smets's later utility-theoretic justification [1717] is needed.

- **Dempster's "floating probability mass"** *(p.471)*: critique of the casual probability-bound interpretation supposedly endorsed by Dempster but later disavowed by Shafer [1583, 1607] and ultimately by Dempster [426] himself.

- **Voorbraak's representation theorem extension** *(p.475–476)*: the symmetry between `P̃l` and `B̃el` is "broken" because `B̃el` does not exist when `Σ m(x) = 0`. Cuzzolin frames this as a limitation of Voorbraak [1859] not addressed in the original.

- **Cobb–Shenoy result reformulation** *(p.475 footnote 74)*: "The original statements in [293] have been reformulated according to the notation used in this book."

- **Plausibility transform NOT unique under Dempster commutation** *(p.481)*: Cuzzolin shows in Section 12.4.2 that the relative plausibility transform "is not unique as a probability transformation which commutes with `⊕`", because the relative belief operator `B̃el` *also* commutes with Dempster (Theorem 56), albeit applied to different objects.

- **Plausibility-bound mismatch under Dempster aggregation** *(p.473)*: Shafer's argument (cited via [1583, 1607, 2089]) that consistent probabilities for individual `Bel`s do not behave coherently under Dempster aggregation, supporting the *non*-probability-bound (epistemic) interpretation.

- **Negative-mass component of `ς[Bel]`** *(p.443, Example 28)*: Although `ς[Bel]` lives on the dual line and is a Bayesian NSF, the resulting BPA assigns negative mass to non-singletons (`m_{ς[Bel]}({x,y}) = −0.071`, etc.). This is the formal expression of why `ς[Bel]` is not generally a belief function — Theorem 41 makes this exact.

## Design rationale

- **Why the affine family** *(p.432)*: "transforms which commute (at least under certain conditions) with affine combination". Affine combination corresponds to Smets's *linearity* property. Two new transforms (intersection probability, orthogonal projection) join the pignistic function in this group from "purely geometric considerations" — not requiring an upper-lower probability semantics.

- **Why probability-bound semantics is rejected as a *requirement*** *(p.432)*: "this does not require probability transforms to adhere to the much-debated upper–lower probability semantics. Some important transforms of this kind are not compatible with such semantics."

- **Why the orthogonality flag `O[Bel]` is named that way** *(p.449)*: "The Bayesian belief function `O[Bel]` then deserves the name of orthogonality flag" because `π[Bel] = P̄` iff `Bel ⊥ a(P)`, and `O[Bel]` measures the deviation from this orthogonality.

- **Why two redistribution processes (pignistic vs. flag)** *(p.450)*: pignistic redistributes mass to *singletons* of each focal element; the orthogonality flag redistributes to *all subsets* including the empty set. The latter produces an unnormalised belief function `Bel^U`, whose relative belief of singletons is `O[Bel]`.

- **Why work with pseudo-belief functions** *(p.479, p.481)*: Voorbraak/Cobb-Shenoy results "are not valid for all pseudo-belief functions but only for proper BFs"; nonetheless, embedding the analysis in pseudo-belief space unifies the relative plausibility and relative belief operators via Theorem 55 (cross-symmetry) and reveals the duality table.

- **Why the relative mass family** *(p.484)*: the relative belief is "merely one representative of an entire family". When `B̃el` does not exist (singular case `k_{Bel} = 0`), the relative mass family `m̃_s` (Definition 127) provides a low-cost proxy that can approximate `P̃l` or `BetP` using only `C(n,s)` focal elements.

- **Why C2 is preferred over C1** *(p.489, "A critical look")*: in the presence of conflicting evidence, "it is not irrational [...] to judge larger-size focal elements 'less reliable' (as carriers of greater ignorance) than more focused focal elements". This is a pragmatic decision-theoretic argument for the relative belief operator and its natural extension `B̃el^{ext}` (Eq. 12.14).

- **Why the equality conditions matter** *(p.504, Section 12.7)*: the entire "rich tapestry" of probability transforms collapses to a single distribution under the equal-plausibility-distribution condition `Pl(x; k) = const` (Theorem 67). When the design space collapses, the choice becomes irrelevant. This is the formal justification for using *any* transform when the BF is highly symmetric.

- **Why the chapter ordering** *(p.469)*: Chapter 11 (affine) before Chapter 12 (epistemic) reflects the *historical* ordering (affine constructions go back to Smets's pignistic) and the *structural* ordering (affine geometry is simpler, sets up the dual concepts needed for epistemic analysis).

## Open / research questions

- *(p.487, 489)* "What about the 'extended' operator `B̃el^{ext}`?" — relative-mass proxy criteria C1 vs C2, and which is optimal in conflicting-evidence regimes, is left as open in the sense of "two opposite scenarios" with no general answer.

- *(p.506, after Theorem 67)* "Less binding conditions [for universal collapse] may be harder to formulate — we plan on studying them in the near future." Cuzzolin explicitly defers a complete characterisation of equality conditions to future work.

- *(p.467 / Section 11.6)* Beyond the sufficient conditions of Theorems 51, 52, the *necessary* conditions for `BetP[Bel] = p[Bel]` and `π[Bel] = p[Bel]` are not characterised in general (only the binary case is settled). Implicit research question.

- *(p.489)* "we will get some insight into this in Section 12.6, at least in the case study of a frame of size 3" — full characterisation of the geometry in `P` for general `n` is left implicit.

- *(p.486, "C1 vs C2")* Whether the optimal C1 approximation `ŝ[BetP] = arg max_s k^s` and `ŝ[P̃l] = arg max_s sk^s` can differ — and how to reconcile their decision-making interpretations — is an open question.

## Notable references cited

- `[245]` Chateauneuf — affine geometry / probability-bound interpretation, dual lines, also outer-consonant ideas *(p.434, 437)*.
- `[291]` Cobb & Shenoy — plausibility transform commutes with Dempster's rule, motivation for the epistemic family *(p.471, 474)*.
- `[293]` Cobb & Shenoy — original notation later reformulated *(footnote 74, p.475)*.
- `[295]` Cobb & Shenoy — proof that `P̃l` commutes with `⊕` *(p.475)*.
- `[327]` Cuzzolin — "Most of the material of this chapter was originally published in" *(p.433)*; also cited for the orthogonal-sum extension to NSFs *(p.476)*.
- `[333]` Cuzzolin — preliminary results on equality conditions and `π = BetP` for ternary frames *(p.455, 456, 502, 504)*.
- `[345]` Cuzzolin — geometry of outer consonant approximations *(p.517, chapter 13 opener cited)*.
- `[347]` Cuzzolin — Theorem 25 (Möbius identity used in cross-symmetry) *(p.475)*.
- `[358]` Cuzzolin & Frezza — relative plausibility/belief paper, cited for non-Bayesianity reflection through `P` *(p.438, 469)*.
- `[382]` Dubois & Prade — distance functions for probability transforms *(p.431, 490 footnote 76)*.
- `[425, 426]` Dempster — original "floating probability mass" claim, later disavowal *(p.471)*.
- `[531]` Dubois et al. — consonant approximation references *(p.484, 518)*.
- `[758]` Ha & Haddawy — affine operator for sets of probabilities; "affine trees" *(p.432)*.
- `[757]` Ha & Haddawy — convex-closure operator on probability intervals (`pcc`-tree) *(p.432)*.
- `[1096]` Keynes — principle of insufficient reason *(p.472)*.
- `[1583, 1607]` Shafer — disavowal of probability-bound interpretation *(p.471, 473)*.
- `[1685]` Smets — open-world / unnormalised BF semantics *(p.450, 453)*.
- `[1717]` Smets — utility-theoretic justification of pignistic transform; rebuttal of insufficient-reason critique *(p.435, 481, 472 footnote 73)*.
- `[1722]` Smets — internal-conflict reading of `m(∅)` *(p.453)*.
- `[1730]` Smets — linearity axiom of TBM *(p.435, 481)*.
- `[1859]` Voorbraak — relative plausibility representation theorem *(p.435, 472, 475)*.
- `[2089]` Shafer — disagreement with renormalisation *(p.474)*.
- `[195]` (chain measure paper) — invoked for Definition 128 *(p.526, chapter 13 boundary)*.

## Implementation notes for propstore

This pair of chapters provides the formal infrastructure for several propstore subsystems:

- **`propstore.aspic_bridge` / Bayesian summarisation of belief sets**: When ASPIC+ extensions need a single probability for ranking arguments, the choice between `BetP[Bel]`, `p[Bel]`, `π[Bel]`, `P̃l`, `B̃el` is a render-time policy decision — exactly the kind of "non-commitment in storage" the project mandates. Each transform should be implemented as a pure function on a `BeliefFunction` value with provenance type `defaulted` (per the global design principle): the user picks the policy, the system does *not* default to one.

- **`propstore.world` (ATMS) — environments labelled by belief functions**: The intersection probability `p[Bel]` is the natural Bayesian summary of an ATMS environment when the focal sets correspond to assumption sets. The orthogonality flag `O[Bel]` provides a "distance from non-informativeness" metric useful for environment ranking.

- **`propstore.belief_set.ic_merge` — model-theoretic IC merge**: Theorem 49 (`π` commutes with affine combination) and Lemma 12 (`P̃l` does *not* commute with affine combination but with weighted convex combinations) directly inform whether a merge operator should be applied at the belief-function level (use `π` or `BetP`) or at the probability level (use `P̃l` then merge). Cuzzolin's duality table (Section 12.2.5) is a literal classification of merge-discipline options.

- **`propstore.heuristic_analysis` (proposal artifacts)**: Each candidate BF-to-P transform is a typed proposal; the `affine` vs `epistemic` family classification is a meaningful tag. Storing both `p[Bel]` and `P̃l` as alternative summaries with separate provenance lets render queries select per-policy.

- **Honest ignorance** (project design principle): Theorem 65 (singular case) is precisely the "honest ignorance" pattern — when `k_{Bel} = 0`, the relative belief does not exist, and pretending it does (e.g. by uniform default) would be fabrication. The codebase should expose `B̃el = None` (or equivalent) and require explicit fallback policy.

- **`propstore.dimensions` / structured equality conditions**: Corollary 14 and Theorem 67 give compositional sufficient conditions ("equal mass within each cardinality") that can be tested at storage-time as a metadata check on a BF. If the condition holds, a single canonical probability summary is justified; otherwise the system holds all rival summaries.

- **Render policy library**: Implement `RenderPolicy` constants `RenderPolicy.PIGNISTIC`, `RenderPolicy.INTERSECTION_PROB`, `RenderPolicy.ORTHOGONAL_PROJ`, `RenderPolicy.RELATIVE_PLAUSIBILITY`, `RenderPolicy.RELATIVE_BELIEF`, `RenderPolicy.RELATIVE_MASS_S=k`. Make explicit the design rationale for each in module docstrings, citing Cuzzolin Chapter 11/12.

- **Test surface (Hypothesis property tests)**: Generate random `Bel` over small frames; assert (a) `BetP[Bel] = p[Bel] = π[Bel]` for `|Θ| ≤ 3` (Corollary 15), (b) `BetP[Bel] = p[Bel]` whenever focal elements have only sizes 1 and `k` (Theorem 42), (c) the universal collapse Eq. 12.35 under `Pl(x;k) = const`. Property tests over geometric invariants (`φ₁=π/2 ⟺ Eq. 12.32`, etc.) provide strong correctness checks.

- **Worldline / temporal**: Theorems 43 and 49 specify how `p[·]` and `π[·]` transform under affine combinations of belief functions over time. When merging beliefs from temporally-ordered evidence sources, these laws give the closed-form update.

## Quotes worth preserving

- "The line connecting `Pl` and `Bel` is orthogonal to the affine space generated by the probabilistic simplex." — Theorem 39, p.436. *(Sets the geometric foundation of the chapter.)*

- "Inherently epistemic notions such as 'consistency' and 'linearity' (one of the rationality principles behind the pignistic transform) seem to be related to geometric properties such as orthogonality. It is natural to wonder whether this is true in general, or is just an artefact of the binary frame." — p.435. *(The chapter's animating question.)*

- "We add a further element to this ongoing debate by proving that the plausibility transform, although it does not obviously commute with affine combination, does commute with the convex closure of belief functions in the belief space `B`." — p.481, Theorem 59. *(Bridging the affine/epistemic divide via convex closure.)*

- "It is not irrational, in the case of conflicting evidence, to judge larger-size focal elements 'less reliable' (as carriers of greater ignorance) than more focused focal elements." — p.489. *(Design rationale for C2 / `B̃el`.)*

- "The relative belief and plausibility of singletons are linked by a form of duality, as `B̃el` can be interpreted as the relative plausibility of singletons of the plausibility function `Pl` associated with `Bel`." — p.474. *(Theorem 55 in plain English.)*

- "These results lead to a classification of all probability transformations into two families, related to the Dempster sum and affine combination, respectively." — p.481. *(The chapter pair's central thesis.)*

- "If `Pl(x;k) = const = Pl(·;k)` for all `k = 1, …, n − 1`, then `Bel` is orthogonal to `P`, and `P̃l = R[Bel] = π[Bel] = BetP[Bel] = P̄`." — Theorem 67, p.506. *(The universal collapse, the strongest equality result of the chapter.)*

- "Less binding conditions may be harder to formulate — we plan on studying them in the near future." — p.506. *(Explicit deferral of further work, an honest acknowledgement of the open frontier.)*
