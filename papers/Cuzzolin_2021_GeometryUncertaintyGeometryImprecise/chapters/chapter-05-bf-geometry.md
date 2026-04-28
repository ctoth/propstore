# Chunk #5 — Chapter 7 (Geometry of Belief Functions) + Chapter 8 (Geometry of Dempster's Rule)

**Book pages:** 323–388 (with Chapter 9 opener at pp. 389–395 included as boundary)
**PDF idx:** 348–413

This is the geometric core of the monograph. Chapter 7 erects the simplicial belief space B and decomposes it as a recursive smooth fibre bundle. Chapter 8 then geometrises Dempster's orthogonal sum as an operator on points (and affine subspaces) of that simplex, culminating in a geometric construction algorithm.

## Sections covered

- Ch. 7 opener / outline (p. 323–326)
- 7.1 The space of belief functions (p. 326)
  - 7.1.1 The simplex of dominating probabilities (p. 326–327)
  - 7.1.2 Dominating probabilities and L1 norm (p. 328–329)
  - 7.1.3 Exploiting the Möbius inversion lemma (p. 329)
  - 7.1.4 Convexity of the belief space (p. 330)
- 7.2 Simplicial form of the belief space (p. 331–333)
  - 7.2.1 Faces of B as classes of belief functions (p. 334–335)
- 7.3 Differential geometry of belief functions (p. 335)
  - 7.3.1 The ternary case (p. 335–337)
  - 7.3.2 Definition of smooth fibre bundles (p. 338–339)
  - 7.3.3 Normalised sum functions (p. 339)
- 7.4 Recursive bundle structure (p. 339)
  - 7.4.1 Recursive bundle of S (p. 339–340)
  - 7.4.2 Recursive bundle of B (p. 340–341)
  - 7.4.3 Bases and fibres as simplices (p. 341–343)
- 7.5 Research questions (p. 344)
- Appendix: Proofs of Theorem 11, Lemma 4, Theorem 12 (p. 344–349)
- Ch. 8 opener / outline (p. 351–352)
- 8.1 Dempster combination of pseudo-belief functions (p. 352)
- 8.2 Dempster sum of affine combinations (p. 353–355)
- 8.3 Convex formulation of Dempster's rule (p. 356–357)
- 8.4 Commutativity (p. 357–359)
  - 8.4.1 Affine region of missing points (p. 358)
  - 8.4.2 Non-combinable points and missing points: a duality (p. 358–359)
  - 8.4.3 Unnormalised belief functions (p. 359–360)
- 8.5 Conditional subspaces (p. 360–363)
  - 8.5.1 Definition (p. 360–362)
  - 8.5.2 Unnormalised case (p. 362)
  - 8.5.3 Vertices of conditional subspaces (p. 363)
- 8.6 Constant-mass loci (p. 364)
  - 8.6.1 Geometry of Dempster's rule in B2 (p. 364–368)
  - 8.6.2 Affine form of constant-mass loci (p. 369–370)
  - 8.6.3 Action of Dempster's rule on constant-mass loci (p. 370–372)
- 8.7 Geometric orthogonal sum (p. 372)
  - 8.7.1 Foci of conditional subspaces (p. 372–375)
  - 8.7.2 Algorithm (p. 375–376)
- 8.8 Research questions (p. 376–378)
- Appendix: Proofs (Thm 13, Lem 6, Thm 16, Thm 18, Thm 20, Thm 21, Thm 23) (p. 378–388)

## Chapter overview

Chapter 7 is the "geometry comes online" chapter. Belief functions on a finite frame Θ of cardinality n are placed inside R^{2^|Θ|} as vectors of belief values; the **belief space** B is the locus of admissible such vectors. The chapter proves three increasingly strong structural results: (i) B is convex (Thm 8); (ii) B is the convex closure of the categorical belief functions Bel_A focused on each non-empty proper subset, hence B is a simplex of dimension N−2 = 2^n − 2 (Thm 9, Cor 3); and (iii) B inherits a recursive smooth fibre-bundle decomposition from the embedding R^{N−2} of normalised sum functions (Thm 11, Thm 12). The recursion has n−1 levels indexed by event size i = 1,…,n−1; at each level the base D_B^{(i)} is the set of "i-additive" discounted belief functions, while the fibre F_B^{(i)} captures the residual mass distributed over events of size i and Θ. The ternary case Θ_3 = {x,y,z} is worked in coordinates as the running scaffold. The chapter sets up everything subsequent geometric work depends on: simplicial coordinates = BPA values, vertices = categorical belief functions, the probability simplex P sits as one boundary face, etc.

Chapter 8 then geometrises Dempster's rule ⊕. The key trick is to **relax non-negativity**: the embedding space S = R^{N−2} of normalised sum functions admits a straightforward extension of Dempster's rule (Thm 13), allowing us to talk about ⊕ on whole affine subspaces rather than just inside the simplex B. This pays off in three cascading results: (1) ⊕ commutes with affine closures up to a lower-dimensional "missing-points" subspace M (Thm 16) — and on convex closures of belief functions ⊕ commutes outright with Cl (Cor 6); (2) the orthogonal sum admits a **convex decomposition** in terms of Bayes conditioning (Thm 15): Bel ⊕ Bel′ is a convex combination of the conditioned belief functions Bel ⊕ Bel_A as A ranges over the focal elements of Bel′; (3) for any belief function Bel, the **conditional subspace** ⟨Bel⟩ of all combinations of Bel with combinable BFs has a simplex-like structure, and the constant-mass loci H_A^k for the second operand all map under Bel ⊕ (·) to affine subspaces that share a common A-th **focus** F_A(Bel) (Thm 20–22). The chapter ends with **Algorithm 19**, which constructs Bel ⊕ Bel′ geometrically by intersecting affine subspaces parameterised by the foci.

These two chapters together are the foundational "geometric program" that Cuzzolin has been promising since the introduction. Everything later in the book — probability transforms, plausibility/commonality spaces (Ch. 9 begins on p. 389), consonant approximations, decision making — operates on the structures defined here.

## Definitions

### Definition 120 (Belief space) *(p.326)*

The belief space associated with Θ is the set B_Θ of vectors v ∈ R^{|2^Θ|} such that there exists a belief function Bel : 2^Θ → [0,1] whose belief values correspond to the components of v, for an appropriate ordering of the subsets of Θ. The vector of R^{|2^Θ|} corresponding to Bel is denoted **bel**.

### Categorical belief function Bel_A *(p.331, unnumbered defn.)*

The unique belief function with BPA m_{Bel_A}(A) = 1, m_{Bel_A}(B) = 0 for all B ≠ A. Its vector representation is denoted **bel**_A. Categorical belief functions are the vertices of B.

### Definition 121 (Smooth fibre bundle) *(p.338)*

A smooth fibre bundle ξ is a composed object {E, B, π, F, G, U} where:
1. E is an (s+r)-dimensional differentiable manifold (the **total space**).
2. B is an r-dimensional differentiable manifold (the **base space**).
3. F is an s-dimensional differentiable manifold (the **fibre**).
4. π : E → B is a smooth application of full rank r at each point of B (the **projection**).
5. G is the **structure group**.
6. The atlas U = {(U_α, φ_α)} defines a bundle structure: B admits a covering by open sets U_α such that E_α ≐ π^{−1}(U_α) is equipped with smooth direct-product coordinates φ_α : π^{−1}(U_α) → U_α × F, e ↦ (φ′_α(e), φ″_α(e)), satisfying (a) π ∘ φ_α^{−1}(x,f) = x, equivalently φ′_α(e) = π(e); (b) the fibre coordinate transforms under transition φ_β φ_α^{−1}(x,f) = (x, T^{αβ}(x)f) with T^{αβ} : U_{αβ} → G satisfying T^{αβ} = (T^{βα})^{−1} and T^{αβ} T^{βγ} T^{γα} = 1.

### Definition 122 (Conditional subspace) *(p.361)*

Given a belief function Bel ∈ B, the conditional subspace ⟨Bel⟩ is the set of all Dempster combinations of Bel with any other combinable belief function on the same frame:
$$\langle Bel \rangle \doteq \{ Bel \oplus Bel'\ :\ Bel' \in \mathcal{B}\ \text{s.t.}\ \exists\ Bel \oplus Bel' \}. \quad (8.13)$$
The **compatible subspace** C(Bel) ≐ {Bel′ : C_{Bel′} ⊂ C_{Bel}} is the collection of belief functions whose focal elements lie in the core of Bel; ⟨Bel⟩ = Bel ⊕ C(Bel).

### Definition 123 (A-th focus of a conditional subspace) *(p.372)*

The A-th focus of ⟨Bel⟩ for A ⊆ C_{Bel} is the linear variety
$$\mathcal{F}_A(Bel) \doteq \bigcap_{k\in[0,1]} v(Bel \oplus \mathcal{H}_A^k(Bel)),$$
i.e. the common intersection of the affine images of the constant-mass loci H_A^k(Bel) under Bel ⊕ (·) as k ranges over [0,1].

### Constant-mass loci *(p.369)*

$$H_A^k \doteq \{Bel : m(A) = k\},\ k \in [0,1],\quad \mathcal{H}_A^k \doteq \{\varsigma : m_\varsigma(A)=k\},\ k \in \mathbb{R},$$
for proper belief functions and normalised sum functions, respectively. Each constant-mass locus has dimension dim(B)−1; in B_2 it is a line. Restrictions H_A^k(Bel) ≐ H_A^k ∩ C(Bel) and similarly for H.

## Theorems, propositions, lemmas

### Lemma 2 *(p.326)*
If Bel = P : 2^Θ → [0,1] is Bayesian and B ⊆ Θ, then ∑_{A ⊆ B} P(A) = 2^{|B|−1} P(B). Proof: rewrites the sum as ∑_{θ∈B} k_θ P({θ}) with k_θ = 2^{|B|−1}.

### Corollary 1 (Limit simplex L) *(p.327)*
The set P of all Bayesian belief functions on Θ is a subset of the (|Θ|−1)-dimensional region
$$\mathcal{L} = \Big\{Bel : 2^\Theta \to [0,1] \in \mathcal{B}\ \text{s.t.}\ \sum_{A \subseteq \Theta} Bel(A) = 2^{|\Theta|-1}\Big\}\quad (7.1)$$
called the **limit simplex**.

### Theorem 6 (B dominated by L) *(p.327)*
For any frame Θ, ∑_{A ⊆ Θ} Bel(A) ≤ 2^{|Θ|−1}, with equality iff Bel is Bayesian. Proof: the sum equals ∑_i a_i m(A_i) with a_i = 2^{|Θ\A_i|}; the bound a_i ≤ 2^{|Θ|−1} is tight iff |A_i| = 1 for every focal element.

### Lemma 3 *(p.328)*
If Bel ≥ Bel′ (pointwise on 2^Θ), then C_{Bel} ⊆ C_{Bel′} (cores reverse-include).

### Theorem 7 (L1 distance to dominating Bayesian BF) *(p.328)*
For any Bel, the L1 distance ‖Bel − P‖_{L1} = ∑_{A ⊆ Θ} |Bel(A) − P(A)| equals the constant
$$f(Bel) \doteq 2^{|\Theta \setminus C_{Bel}|}\Big[ 2^{|C_{Bel}|-1} - 1 - \sum_{A \subsetneq C_{Bel}} Bel(A) \Big]\quad (7.3)$$
for every Bayesian P dominating Bel. Proof exploits Lemma 3 plus a counting argument: subsets containing A ⊆ C_{Bel} arbitrarily extended outside C_{Bel} contribute identically. Result: the distance does not depend on P, only on Bel.

### Möbius inversion lemma (recalled) *(p.329, eq. 7.4)*
$$m(A) = \sum_{B \subseteq A} (-1)^{|A \setminus B|} Bel(B)\quad (7.4)$$
Used to test admissibility: a vector v ∈ R^{|2^Θ|} corresponds to some Bel iff its Möbius transform m_v(A) = ∑_{B ⊆ A} (−1)^{|A\B|} v_B is a basic probability assignment (non-negative, summing to 1).

### Theorem 8 (Convexity) *(p.330)*
The belief space B is convex. Proof: positivity constraints have the form ∑_{A∈A} v_A ≥ ∑_{B∈B} v_B (eq. 7.7) for disjoint subset collections A, B; this form is preserved under convex combinations bel^α = (1−α)bel^0 + α bel^1.

### Theorem 9 (Convex decomposition of bel) *(p.331)*
Every vector representation **bel** of a belief function Bel ∈ B can be uniquely expressed as a convex combination of the categorical vectors **bel**_A:
$$\mathbf{bel} = \sum_{\emptyset \subsetneq A \subsetneq \Theta} m(A)\,\mathbf{bel}_A \quad (7.8)$$
with coefficients given by the BPA m of Bel. Proof: each component is bel(B) = ∑_{A⊆B, A≠∅} m(A) = ∑_A m(A) δ(B⊇A) = ∑_A m(A) [bel_A]_B.

### Theorem 10 (Faces of B as restricted-focal classes) *(p.331)*
The set of all belief functions with focal elements in a given collection X ⊂ 2^Θ is closed and convex in B:
$$\{\mathbf{bel} : \mathcal{E}_{Bel} \subset \mathcal{X}\} = Cl(\{\mathbf{bel}_A : A \in \mathcal{X}\}).$$
The convex closure of points v_1,…,v_k is Cl(v_1,…,v_k) ≐ {v ∈ R^m : v = ∑α_i v_i, ∑α_i = 1, α_i ≥ 0} (eq. 7.9).

### Corollary 2 / Corollary 3 (B is a simplex) *(p.332–333)*
B = Cl({**bel**_A : ∅ ⊊ A ⊆ Θ}) (eq. 7.10) and the vertices are affinely independent ⇒ **B is a simplex** of dimension N − 2 = 2^n − 2.

### Corollary 4 (Probability face) *(p.334)*
The Bayesian region of B is the (n−1)-dimensional face P = Cl(**bel**_x, x ∈ Θ).

### Theorem 11 (Recursive bundle of S) *(p.339–340)*
The space S = R^{N−2} of all sum functions ς on Θ has a recursive fibre-bundle structure: there exist smooth fibre bundles ξ_i = {F_S^{(i−1)}, D_S^{(i)}, F_S^{(i)}, π_i}, i = 1,…,n−1, with F_S^{(0)} = S = R^{N−2}, where the i-th total/base/fibre have dimensions ∑_{k=i}^{n−1} C(n,k), C(n,i), and ∑_{k=i+1}^{n−1} C(n,k) respectively. Each F_S^{(i−1)} is parameterised globally by ς^{i−1} = [ς^{i−1}(A), A ⊂ Θ, i ≤ |A| < n]′; smooth direct-product coordinates split into base φ′(ς^{i−1}) = {ς^{i−1}(A), |A|=i} and fibre φ″(ς^{i−1}) = {ς^{i−1}(A), i < |A| < n}; projection π_i[ς^{i−1}] = [ς^{i−1}(A), |A|=i]′ (eq. 7.19).

### Lemma 4 (Combinatorial bound) *(p.341)*
$$\sum_{|A|=i} Bel(A) \le 1 + \sum_{m=1}^{i-1} (-1)^{i-(m+1)} \binom{n-(m+1)}{i-m} \sum_{|B|=m} Bel(B),$$
with the upper bound reached iff ∑_{|A|=i} m(A) = 1 − ∑_{|A|<i} m(A).

### Theorem 12 (B inherits convex bundle decomposition) *(p.341)*
B ⊂ S inherits a "convex" bundle decomposition. Each i-th-level fibre is
$$\mathcal{F}_\mathcal{B}^{(i-1)}(\mathbf{d}^1,\dots,\mathbf{d}^{i-1}) = \{\mathbf{bel} \in \mathcal{B}\ |\ V_i \wedge \cdots \wedge V_{n-1}(\mathbf{d}^1,\dots,\mathbf{d}^{i-1})\}\quad (7.20)$$
with V_i (eq. 7.21) the system of constraints
$$V_i:\ \begin{cases} m(A) \ge 0 & \forall A : |A| = i,\\ \sum_{|A|=i} m(A) \le 1 - \sum_{|A|<i} m(A). \end{cases}$$
The i-th base is given by the system (eq. 7.22): m(A) = 0 for i < |A| < n; m(A) ≥ 0 for |A| = i; ∑_{|A|=i} m(A) ≤ 1 − ∑_{|A|<i} m(A). Proof in appendix uses induction levelwise and reduction of higher-size constraints by Lemma 4.

### Bases and fibres are simplices (7.4.3) — convex decomposition *(p.342–343)*
Convex expressions for the i-th level objects (eq. 7.24):
$$\begin{aligned}
\mathcal{F}_\mathcal{B}^{(i-1)} &= k\,\mathbf{bel}_0 + (1-k)\,Cl(\mathbf{bel}_A, |A| \ge i),\\
\mathcal{P}^{(i)} &= k\,\mathbf{bel}_0 + (1-k)\,Cl(\mathbf{bel}_A : |A|=i),\\
\mathcal{O}^{(i)} &= k\,\mathbf{bel}_0 + (1-k)\,\mathbf{bel}_\Theta,\\
\mathcal{D}_\mathcal{B}^{(i)} &= Cl(k\,\mathbf{bel}_0 + (1-k)\,\mathbf{bel}_A : |A| = i\ \text{or}\ A = \Theta) = Cl(\mathcal{O}^{(i)}, \mathcal{P}^{(i)}).
\end{aligned}$$
Where bel_0 absorbs the lower-size mass. P^(i) is the set of i-additive belief functions; O^(i) is the line of (1−ε)P + ε bel_Θ discounted versions; D_B^(i) is the i-th level base = collection of "discounted i-additive" BFs.

### Theorem 13 (Dempster of NSFs) *(p.352)*
The application of Dempster's rule (def. 2.6) to a pair of normalised sum functions ς_1, ς_2 : 2^Θ → R yields another normalised sum function denoted ς_1 ⊕ ς_2. Two NSFs are *not combinable* iff
$$\Delta(\varsigma_1, \varsigma_2) \doteq \sum_{A,B : A \cap B \ne \emptyset} m_{\varsigma_1}(A) m_{\varsigma_2}(B) = 0\quad (8.1)$$

### Lemma 5 (Combinability with affine combination) *(p.354)*
For NSFs {ς_1,…,ς_n} with affine combination ς = ∑α_iς_i, ∑α_i = 1: ς is combinable with ∑α_iς_i iff ∑_i α_i Δ_i ≠ 0, where Δ_i = ∑_{A∩B≠∅} m_ς(A) m_{ς_i}(B).

### Lemma 6 (Möbius transform of combined affine sum) *(p.354)*
$$m_{\varsigma \oplus \sum_i \alpha_i \varsigma_i}(C) = \sum_i \frac{\alpha_i N_i(C)}{\sum_j \alpha_j \Delta_j},\quad N_i(C) \doteq \sum_{B \cap A = C} m_{\varsigma_i}(B) m_\varsigma(A).$$

### Theorem 14 (Affine-preservation of ⊕ on NSFs) *(p.355)*
If ∑α_i = 1 and ∑α_iΔ_i ≠ 0 (so ς is combinable with ∑α_iς_i) and ς_i is combinable with ς for each i, then
$$\varsigma \oplus \sum_i \alpha_i \varsigma_i = \sum_i \beta_i (\varsigma \oplus \varsigma_i),\quad \beta_i = \frac{\alpha_i \Delta_i}{\sum_j \alpha_j \Delta_j}\quad (8.2)–(8.3)$$
i.e. the Dempster sum of an affine combination is itself an affine combination of partial sums, with re-normalised coefficients. When all NSFs are belief functions Δ_i ≥ 0, β_i ≥ 0, so convex combinations map to convex combinations.

### Lemma 7 (Combinability with convex combination of BFs) *(p.355)*
∃ Bel ⊕ ∑α_i Bel_i ⇔ ∃ i : ∃ Bel ⊕ Bel_i. Combinability with the convex combination is "or" combinability with at least one summand.

### Corollary 5 (Convex commutation when all combinable) *(p.356)*
If at least one Bel_j is combinable with Bel and α_i > 0 with ∑α_i = 1, then
$$Bel \oplus \sum_i \alpha_i Bel_i = \sum_i \beta_i\, Bel \oplus Bel_i,$$
β_i defined as in (8.3).

### Theorem 15 (Convex decomposition of ⊕ via Bayes conditioning) *(p.356)*
$$Bel \oplus Bel' = \sum_{A \in \mathcal{E}_{Bel'}} \frac{m'(A) Pl(A)}{\sum_B m'(B) Pl(B)}\, Bel \oplus Bel_A\quad (8.5)$$
Proof: write Bel′ = ∑_A m′(A) Bel_A via (7.8); apply Cor 5; the per-A normalisation factor Δ_A = 1 − Bel(A^c) = Pl(A). Since Bel ⊕ Bel_A is Bayes conditioning Bel|A, Theorem 15 says the orthogonal sum is a convex combination of Bayes conditionings of Bel weighted by m′(A)Pl(A).

### Theorem 16 (Affine commutativity, with missing-points caveat) *(p.357)*
For ς combinable with ς_i for each i:
$$v(\varsigma \oplus v(\varsigma_1,\dots,\varsigma_n)) = v(\varsigma \oplus \varsigma_1, \dots, \varsigma \oplus \varsigma_n).$$
More precisely, the image affine space is
$$v(\varsigma \oplus \varsigma_1,\dots,\varsigma \oplus \varsigma_n) = \varsigma \oplus v(\varsigma_1,\dots,\varsigma_n) \cup \mathcal{M}(\varsigma,\varsigma_1,\dots,\varsigma_n),$$
where M is the "missing points" subspace
$$v\Big(\frac{\Delta_j}{\Delta_j-\Delta_n}\varsigma\oplus\varsigma_j - \frac{\Delta_n}{\Delta_j-\Delta_n}\varsigma\oplus\varsigma_i\,\Big|\,\forall j: \Delta_j \ne \Delta_n,\forall i:\Delta_i = \Delta_n\Big)\quad (8.8)$$

### Corollary 6 (Cl and ⊕ commute) *(p.358)*
If Bel is combinable with every Bel_i (i.e. Δ_i > 0 ∀i), then Cl and ⊕ commute:
$$Bel \oplus Cl(Bel_1,\dots,Bel_n) = Cl(Bel \oplus Bel_1,\dots,Bel \oplus Bel_n).$$

### Theorem 17 (Conditional subspace as image of compatible) *(p.362)*
$$\langle Bel \rangle = Bel \oplus C(Bel) = Cl\{Bel \oplus Bel_A,\ A \subseteq C_{Bel}\}.$$
Proof: any Bel′ ∈ B reduces to Bel″ with focal elements F_j = A_j ∩ C_{Bel} that is identically combined; then Cor 6 gives the convex closure form.

### Proposition 54 (Conjunctive analogue for UBFs) *(p.360)*
For unnormalised belief functions Bel̃ combined via the conjunctive operator ⊙ (Smets, eq. 4.25):
$$\tilde{Bel} \odot \sum_i \alpha_i\,\tilde{Bel}_i = \sum_i \alpha_i\,\tilde{Bel} \odot \tilde{Bel}_i$$
whenever ∑α_i = 1, α_i ≥ 0. UBFs are *always* combinable through ⊙, so the affine-preservation result holds without combinability caveats.

### Theorem 18 (Vertices of conditional subspaces) *(p.363)*
$$Bel = \sum_{B\subseteq C_{Bel}} \frac{m(B)}{Pl(B)}\,(Bel - Pl(B \setminus A) Bel)\quad (8.14)$$
(reformulation; the page-bottom theorem statement gives a closed form for vertices of ⟨Bel⟩ in terms of the projection of Bel onto a hyperplane indexed by E ⊆ C_{Bel}).
$$Bel = \sum_{E,F:E \cup F = C_{Bel}} (-1)^{|F|+1} \mathbf{v}_F^{[\dots]}\cdot Pl(E) \cdot Bel \oplus Bel_E,\quad (8.15)$$
with **v**_F^[N(F)] a vector of R^{|2^F|} N(F) coefficients summing to 1.

### Theorem 19 (Affine form of constant-mass loci) *(p.369)*
$$\mathcal{H}_A^k = v(k\,Bel_A + \gamma_B\,Bel_B : B \subseteq \Theta, B \ne A),\ k \in \mathbb{R},\quad (8.19)$$
$$H_A^k = Cl(k\,Bel_A + (1-k)Bel_B : B \subseteq \Theta, B \ne A),\ k \in [0,1].\quad (8.20)$$

### Theorem 20 (Existence of focal-points subspace F′_A) *(p.373)*
For all A ⊆ C_{Bel}, the family {v(Bel ⊕ H_A^k(Bel)) : 0 ≤ k < 1} has a non-empty common intersection F′_A(Bel) ⊃ v(ς_B | B ⊆ C_{Bel}, B ≠ A), where the **focal point** is
$$\varsigma_B = \frac{1}{1 - Pl(B)} Bel + \frac{Pl(B)}{Pl(B) - 1} Bel \oplus Bel_B.\quad (8.24)$$

### Theorem 21 (Two-line determination of focus) *(p.373)*
$$v(Bel \oplus \mathcal{H}_A^0(Bel)) \cap v(Bel \oplus \mathcal{H}_A^1(Bel)) = v(\varsigma_B | B \subseteq C_{Bel}, B \ne A).$$
Hence the A-th focus equals this two-line intersection.

### Corollary 7 (Focus of ⟨Bel⟩) *(p.374)*
$$\mathcal{F}_A(Bel) = v(\varsigma_B | B \subseteq C_{Bel}, B \ne A).\quad (8.25)$$
Focal points are not admissible BFs (Bel coefficient ≥ 0, Bel⊕Bel_B coefficient ≤ 0); intuitively ς_B = lim_{k→+∞} Bel ⊕ (1−k) Bel_B.

### Theorem 22 (Foci coincide with missing points) *(p.374)*
F_A(Bel) coincides with the missing-point subspace of v(Bel ⊕ H_A^k(Bel)) for each k ∈ [0,1]. Proof: missing points are limits γ_B → ∞ of Bel ⊕ [k Bel_A + γ_B Bel_B], which equal ς_B.

### Theorem 23 (Two-affine-spaces identity for orthogonal sum) *(p.375)*
$$v(Bel \oplus \mathcal{H}_A^k(Bel)) = v(\mathcal{F}_A(Bel),\ Bel \oplus k\,Bel_A).$$
Each constant-mass image affine space is generated by the focus plus the single point Bel ⊕ k Bel_A.

### Proposition 55 (Canonical decomposition in B_2) *(p.376)*
For any **bel** ∈ B_2, there exist two uniquely determined simple support functions co_x ∈ CO_x and co_y ∈ CO_y such that bel = co_x ⊕ co_y, with the geometric definitions
$$\mathbf{co}_x = \overline{\mathbf{bel}_y \mathbf{bel}} \cap \mathcal{CO}_x,\quad \mathbf{co}_y = \overline{\mathbf{bel}_x \mathbf{bel}} \cap \mathcal{CO}_y,\quad (8.26)$$
where bel_x bel̄ is the line through bel_x and bel.

## Equations (numbered as in book)

$$\mathcal{P}[Bel] = \sum_{i=1}^k m(A_i) \operatorname{conv}(A_i)\quad (\text{p.329, unnumbered})$$
The set of probability distributions consistent with Bel (Ha et al. [758]) — sum of probability simplices conv(A_i) of focal elements weighted by their masses.

$$Bel \ge Bel' \Leftrightarrow Bel(A) \ge Bel'(A)\ \forall A\quad (7.2)$$
Pointwise dominance order on belief functions.

$$f(Bel) = 2^{|\Theta \setminus C_{Bel}|}\Big[2^{|C_{Bel}|-1} - 1 - \sum_{A \subsetneq C_{Bel}} Bel(A)\Big]\quad (7.3)$$
Closed form for ‖Bel − P‖_{L1} valid for any Bayesian P dominating Bel.

$$m(A) = \sum_{B \subseteq A} (-1)^{|A \setminus B|} Bel(B)\quad (7.4)$$
Möbius inversion lemma.

$$v_A - \dots + (-1)^{|A\setminus B|}\sum_{|B|=k} v_B + \dots + (-1)^{|A|-1}\sum_{\theta \in \Theta} v_{\{\theta\}} \ge 0\ \forall A \subseteq \Theta\quad (7.5)$$
Positivity (admissibility) constraints in terms of vector components, equivalent to BPA non-negativity m_v(A) ≥ 0.

Ternary positivity constraints with shorthand x = v_{{θ_1}}, y = v_{{θ_2}}, z = v_{{θ_3}}, u = v_{{θ_1,θ_2}}, v = v_{{θ_1,θ_3}}, w = v_{{θ_2,θ_3}}:
$$\mathcal{B}: \begin{cases} x,y,z \ge 0,\\ u \ge x+y,\quad v \ge x+z,\quad w \ge y+z,\\ 1 - (u+v+w) + (x+y+z) \ge 0. \end{cases}\quad (7.6)$$

$$\sum_{A \in \mathcal{A}} v_A \ge \sum_{B \in \mathcal{B}} v_B\quad (7.7)$$
Generic form of the positivity constraint shaping B (A, B disjoint subset families).

$$\mathbf{bel} = \sum_{\emptyset \subsetneq A \subsetneq \Theta} m(A)\, \mathbf{bel}_A\quad (7.8)$$
Simplicial coordinates: BPA values are barycentric coordinates of bel in the simplex B with vertices at categorical bels.

$$Cl(\mathbf{v}_1,\dots,\mathbf{v}_k) = \{ \mathbf{v} : \mathbf{v} = \sum \alpha_i \mathbf{v}_i,\ \sum \alpha_i = 1,\ \alpha_i \ge 0\}\quad (7.9)$$
Convex closure operator.

$$\mathcal{B} = Cl(\mathbf{bel}_A, \emptyset \subsetneq A \subseteq \Theta)\quad (7.10)$$
Belief space as convex hull of categorical BFs.

$$\mathbf{bel} = [Bel(x) = m(x), Bel(y) = m(y)]' \in \mathbb{R}^2\quad (7.11)$$
Binary-frame coordinates (since N = 4, N−2 = 2).

$$\mathcal{D} \doteq \{\mathbf{bel} \in \mathcal{B}_3 : \pi[\mathbf{bel}] = \mathbf{d}\},\quad \mathbf{d} = [m(x), m(y), m(z)]'\quad (7.12)/(7.13)$$
Ternary base D parameterised by singleton masses.

$$\mathcal{F}(\mathbf{d}) = \{\mathbf{bel} \in \mathcal{B}_3 : Bel(\{x\})=m(x), \dots, Bel(\{x,y\}) \ge m(x)+m(y), \dots\}\quad (7.14)$$
Ternary fibre over base point d.

$$\mathcal{D} \doteq \{\mathbf{bel} \in \mathcal{B} : m(A) = 0,\ \forall A : 1 < |A| < n\}\quad (7.15)$$
Generalised first-level base: BFs with no mass on intermediate-cardinality events.

$$\phi_\alpha : \pi^{-1}(U_\alpha) \to U_\alpha \times F\quad (7.16)$$
Fibre-bundle local trivialisation chart.

$$\pi \circ \phi_\alpha^{-1}(x,f) = x \quad (7.17)$$
Projection–chart compatibility.

$$T^{\alpha\beta} = (T^{\beta\alpha})^{-1},\quad T^{\alpha\beta} T^{\beta\gamma} T^{\gamma\alpha} = 1\quad (7.18)$$
Cocycle conditions for transition functions.

$$\pi_i[\varsigma^{i-1}] = [\varsigma^{i-1}(A), |A| = i]'\quad (7.19)$$
Recursive bundle projection at level i.

$$\mathcal{F}_\mathcal{B}^{(i-1)}(\mathbf{d}^1,\dots,\mathbf{d}^{i-1}) = \{\mathbf{bel} \in \mathcal{B}\,|\,V_i \wedge \dots \wedge V_{n-1}\}\quad (7.20)$$

$$V_i: \begin{cases}m(A) \ge 0 & \forall A : |A|=i,\\ \sum_{|A|=i}m(A) \le 1 - \sum_{|A|<i} m(A)\end{cases}\quad (7.21)$$

$$\mathcal{D}_\mathcal{B}^{(i)}: m(A) = 0\ \forall i<|A|<n;\ m(A) \ge 0\ \forall|A|=i;\ \sum_{|A|=i}m(A) \le 1 - \sum_{|A|<i}m(A)\quad (7.22)$$

$$\pi[\varsigma](A) = [\varsigma(A), |A|=1]'\quad (7.25)$$
Sum-function projection onto base D_S.

$$\Delta(\varsigma_1,\varsigma_2) \doteq \sum_{A \cap B \ne \emptyset} m_{\varsigma_1}(A) m_{\varsigma_2}(B) = 0\quad (8.1)$$
Combinability test for NSFs.

$$\varsigma \oplus \sum_i \alpha_i \varsigma_i = \sum_i \beta_i (\varsigma \oplus \varsigma_i)\quad (8.2),\quad \beta_i = \frac{\alpha_i \Delta_i}{\sum_j \alpha_j \Delta_j}\quad (8.3)$$

$$Bel \oplus Bel' = \sum_{A \in \mathcal{E}_{Bel'}} \frac{m'(A) Pl(A)}{\sum_B m'(B) Pl(B)} Bel \oplus Bel_A\quad (8.5)$$

$$\alpha_i = \frac{\beta_i}{\Delta_i} \cdot \frac{1}{\sum_j \beta_j/\Delta_j}\quad (8.9)$$
Inverse map from image-space affine coordinates β_i to source-space α_i.

$$\sum_i \frac{\beta_i}{\Delta_i} = 0\quad (8.10)$$
Locus of "missing points" (no preimage).

$$\sum_i \alpha_i \Delta_i = 0\quad (8.11)$$
Locus of "non-combinable points" in source affine space.

$$m_{\tilde{Bel} \odot \sum_i \alpha_i \tilde{Bel}_i}(C) = \sum_i \alpha_i m_{\tilde{Bel} \odot \tilde{Bel}_i}(C)\quad (8.12)$$
Affine preservation under conjunctive (unnormalised) combination.

$$\langle Bel \rangle \doteq \{Bel \oplus Bel'\ :\ Bel' \in \mathcal{B}\ \text{s.t.}\ \exists Bel \oplus Bel'\}\quad (8.13)$$

$$Bel = \frac{1}{P(B)} \sum_{E \subseteq C_{Bel}} \mathbf{v}_E^{[\dots]}[Pl(E) - Pl(E \setminus B)]\quad (8.14)$$
Vertex computation step.

$$Bel = \sum_{E,F:E\cup F = C_{Bel}} (-1)^{|F|+1} \mathbf{v}_F^{[N(F)]} m_E^{[\dots]}\quad (8.15)$$
Vertex form of conditional subspace.

Binary closed form (B_2):
$$m_{Bel \oplus Bel'}(x) = 1 - \frac{(1-m(x))(1-k)}{1 - m(x) l - m(y) k},\quad m_{Bel \oplus Bel'}(y) = 1 - \frac{(1-m(y))(1-l)}{1 - m(x) l - m(y) k}\quad (8.16)$$

$$F_x(Bel) = \Big(1, -\frac{m(\Theta_2)}{m(x)}\Big),\quad F_y(Bel) = \Big(-\frac{m(\Theta)}{m(y)}, 1\Big)\quad (8.17)$$
The two foci of ⟨Bel⟩ in B_2 (when m(Θ_2) ≠ 0) — points outside the belief space.

$$F_{A_B^k}(Bel) = \Big(\frac{1-m(y)}{m(x)-m(y)k}, \frac{1-m(x)}{m(y)-m(x)l}\Big)\quad (8.18)$$
General-A focus formula in B_2.

$$\mathcal{H}_A^k = v(k Bel_A + \gamma_B Bel_B : B \ne A)\quad (8.19),\quad H_A^k = Cl(k Bel_A + (1-k) Bel_B : B \ne A)\quad (8.20)$$

$$Bel \oplus [k Bel_A + (1-k) Bel_B] = \frac{k Pl(A)}{\Delta_B^k} Bel \oplus Bel_A + \frac{(1-k)Pl(B)}{\Delta_B^k} Bel \oplus Bel_B = Bel \oplus [k Bel_{A \cap C_{Bel}} + (1-k) Bel_{B \cap C_{Bel}}]\quad (8.22)$$

$$v(Bel \oplus \mathcal{H}_A^k(Bel)) = v(Bel \oplus [k Bel_A + (1-k)Bel_B] : B \subseteq C_{Bel}, B \ne A) = v(Bel \oplus H_A^k(Bel))\quad (8.23)$$

$$\varsigma_B = \frac{1}{1-Pl(B)} Bel + \frac{Pl(B)}{Pl(B)-1} Bel \oplus Bel_B\quad (8.24)$$
Focal-point coordinates.

$$\mathbf{co}_x = \overline{\mathbf{bel}_y \mathbf{bel}} \cap \mathcal{CO}_x,\quad \mathbf{co}_y = \overline{\mathbf{bel}_x \mathbf{bel}} \cap \mathcal{CO}_y\quad (8.26)$$
Geometric canonical decomposition in B_2.

(Eqs. 8.27–8.36 are appendix-proof bookkeeping for Theorems 16, 18, 20, 21, 23.)

## Geometric structures

### Belief space B *(p.326–333)*
- **Ambient space**: R^{|2^Θ|} = R^{2^n}, with components indexed by subsets of Θ.
- **Reduced ambient**: R^{N−2} = R^{2^n−2} after dropping bel(∅) = 0 and bel(Θ) = 1 (recoverable from normalisation).
- **Defining constraints**: positivity ∑_{A∈A} v_A ≥ ∑_{B∈B} v_B for disjoint A, B; equivalently m_v(A) ≥ 0 for all A.
- **Convex hull form**: B = Cl({bel_A : ∅ ⊊ A ⊆ Θ}).
- **Vertices**: 2^n − 1 categorical belief functions Bel_A; affinely independent.
- **Dimension**: N − 2 = 2^n − 2 (one less than vertex count = standard simplex relation).
- **Coordinates**: BPA values m(A) = barycentric coordinates (eq. 7.8).

### Probability simplex P *(p.334)*
- (n−1)-dimensional face of B.
- Vertices: {bel_x : x ∈ Θ} (n singleton-categorical BFs).
- P = Cl(bel_x, x ∈ Θ).
- Strict subset of the limit simplex L = {Bel : ∑_A Bel(A) = 2^{n−1}}.

### Limit simplex L *(p.327)*
- (n−1)-dim region of R^{2^n}.
- Defining constraint ∑_A Bel(A) = 2^{|Θ|−1}.
- Bounds B from above; coincides with B only on the Bayesian face P.
- Equal to the locus of *normalised set functions* with ∑_x m_ς(x) = 1.

### Simple support segments S *(p.334–335)*
- One-dimensional face S = ∪_{A ⊂ Θ} Cl(bel_Θ, bel_A).
- Each segment Cl(bel_Θ, bel_A) is the locus of simple support BFs focused on A, parameterised by α ∈ [0,1]: bel = α bel_A + (1−α) bel_Θ ↔ m(A) = α, m(Θ) = 1−α.

### Recursive bundle ξ_i = (F_S^{(i−1)}, D_S^{(i)}, F_S^{(i)}, π_i) *(p.339–340)*
| Object | Dimension | Coordinates | Meaning |
|---|---|---|---|
| Total F_S^{(i−1)} | ∑_{k=i}^{n−1} C(n,k) | ς^{i−1}(A), i ≤ |A| < n | NSFs constrained by lower-level decisions |
| Base D_S^{(i)} | C(n,i) | ς^{i−1}(A), |A| = i | Mass distribution over size-i events |
| Fibre F_S^{(i)} | ∑_{k=i+1}^{n−1} C(n,k) | ς^{i−1}(A), i < |A| < n | Residual mass over higher-cardinality events |

The chain terminates at i = n−1 with dim F_S^{(n)} = 0.

### Belief-space recursive structure *(p.341–343)*
B inherits a "convex bundle" decomposition; bases and fibres are simplices:
- i-th level base D_B^{(i)}: collection of "discounted i-additive belief functions" — BFs whose mass lies entirely on size-i events plus Θ. Convex closure of (i-additive Bayesian on level i) and (the line of vacuous-discounted ones).
- Section P^{(i)}: i-additive BFs (no mass on Θ). P^{(1)} = P, the Bayesian face.
- Section O^{(i)}: discounted vacuous BFs (1−ε)P + ε bel_Θ.

### Belief space B_2 (binary frame Θ_2 = {x,y}) *(p.333)*
- Triangle in R^2 with vertices bel_Θ = [0,0]′, bel_x = [1,0]′, bel_y = [0,1]′.
- Coordinates: bel = [Bel(x) = m(x), Bel(y) = m(y)]′.
- P_2 = segment between bel_x and bel_y.
- Constraint: m(x) ≥ 0, m(y) ≥ 0, m(x) + m(y) ≤ 1.

### Belief space B_3 (ternary frame Θ_3 = {x,y,z}) *(p.335–337)*
- 6-dimensional region in R^6 with bel = [Bel(x), Bel(y), Bel(z), Bel({x,y}), Bel({x,z}), Bel({y,z})]′.
- Base D = 3-simplex Cl(bel_x, bel_y, bel_z, bel_Θ), coordinates d = [m(x), m(y), m(z)]′.
- Fibre F(d) = 3-simplex parameterised by [m({x,y}), m({x,z}), m({y,z})]′ with constraints m({x,y}) ≥ 0, m({x,z}) ≥ 0, m({y,z}) ≥ 0, total mass ≤ 1 − m(x) − m(y) − m(z).
- Both base and fibre are 3-dim simplices, total = 6-dim consistent with N − 2 = 8 − 2 = 6.

### Conditional subspace ⟨Bel⟩ *(p.361)*
- Image of the compatible subspace C(Bel) = {Bel′ : C_{Bel′} ⊂ C_{Bel}} under Bel ⊕ (·).
- = Cl({Bel ⊕ Bel_A, A ⊆ C_{Bel}}) (Theorem 17).
- Has Bel itself among its vertices (Bel ⊕ Bel_{C_{Bel}} = Bel).
- In B_2: triangle with vertices Bel, Bel_x, Bel_y when Bel is fully combinable with both.

### Constant-mass loci H_A^k, H_A^k *(p.369)*
- H_A^k = locus of BFs with m(A) = k, k ∈ [0,1]. Dimension dim(B) − 1 = N − 3.
- H_A^k = locus of NSFs with m_ς(A) = k, k ∈ R. Affine subspace.
- In B_2: each H_A^k is a line.

### Foci F_A(Bel) *(p.372)*
- A-th focus is the linear variety ∩_{k ∈ [0,1]} v(Bel ⊕ H_A^k(Bel)).
- Coincides with v(ς_B | B ⊆ C_{Bel}, B ≠ A) (Cor 7).
- Dimension |C_{Bel}| − 2 (generated by 2^{|C_{Bel}|} − 2 affinely related focal points).
- Focal points ς_B are limits Bel ⊕ (1−k)Bel_B as k → ∞ — outside B.
- Coincide with the missing-point subspace of v(Bel ⊕ H_A^k(Bel)) (Theorem 22).

### Affine missing-points subspace M *(p.357–358, eq. 8.8)*
- The subset of the image affine space v(Bel ⊕ ς_1, …, Bel ⊕ ς_n) without a preimage in v(ς_1,…,ς_n).
- Dimension n − 2 in the generic case.
- Defined by ∑_i β_i / Δ_i = 0 with normalisation ∑β_i = 1.

### Non-combinable points subspace *(p.358, eq. 8.11)*
- Subset of source v(ς_1,…,ς_n) on which Δ = ∑α_iΔ_i = 0, i.e. the affine combination ∑α_iς_i is not combinable with ς.
- Defined by ∑α_iΔ_i = 0 with ∑α_i = 1.

## Algorithms

### Algorithm 18 — Geometric Dempster combination in B_2 *(p.367)*
**Procedure** GEOORTHOSUM2D(Bel, Bel′)
1. Compute the foci F_x(Bel) and F_y(Bel) of ⟨Bel⟩ via (8.18).
2. Project Bel′ onto P (the probabilistic face) along the lifting directions, obtaining P_x′ and P_y′.
3. Combine Bel ⊕ P_x′ and Bel ⊕ P_y′ to land back on the probabilistic face.
4. Draw lines F_x(Bel) P_x′ ⊕ Bel and F_y(Bel) P_y′ ⊕ Bel; their intersection is the desired Bel ⊕ Bel′.

Note: Algorithm 18 fails when m(Θ_2) = 0 (Bel = P is Bayesian) — in that case the lines coincide with v(P), so intersection is non-unique.

### Algorithm 19 — Dempster's rule: geometric construction *(p.376)*
**Procedure** GEODEMPSTER(Bel, Bel′)
1. **Compute the foci** {F_A(Bel), A ⊆ C_{Bel}} of the subspace ⟨Bel⟩ conditioned by Bel — by computing the focal points (8.24).
2. **Detect** an additional point Bel ⊕ m″(A) Bel_A for each A ⊆ C_{Bel}, identifying the subspace v(Bel ⊕ H_A^{m″(A)}(Bel)) = v(Bel ⊕ [m″(A) Bel_A + (1 − m″(A)) Bel_B] : B ⊂ C_{Bel}, B ≠ A) — where m″ is the BPA of the projection Bel″ of Bel′ onto C(Bel).
3. **Intersect** all these subspaces to obtain Bel ⊕ Bel′ = Bel ⊕ Bel″.
4. End procedure.

Complexity / efficiency note: focal points ς_B need to be computed only once per Bel (they depend solely on Pl(B), B ⊆ C_{Bel}); each focus is a particular selection of 2^{|C_{Bel}|} − 3 focal points out of 2^{|C_{Bel}|} − 2. Each ς_B is just **Bayes conditioning** Bel|B = Bel ⊕ Bel_B — cheaper than full Dempster combination.

## Parameters / quantities

| Name | Symbol | Domain | Range | Page | Notes |
|------|--------|--------|-------|------|-------|
| Frame cardinality | n = |Θ| | ℕ | n ≥ 2 | 326 | Parameterises 2^n |
| Power-set cardinality | N = 2^|Θ| | ℕ | 2^n | 326 | Ambient dimension before reduction |
| Belief-space dimension | dim(B) | ℕ | N − 2 = 2^n − 2 | 332 | Standard simplex |
| Number of categorical BFs (vertices) | – | ℕ | 2^n − 1 | 331 | All non-empty subsets |
| Probability simplex dimension | dim(P) | ℕ | n − 1 | 334 | Bayesian face |
| BPA value | m(A) | [0,1] | sums to 1 | 329 | Simplicial coordinate |
| Belief value | Bel(A) | [0,1] | – | 326 | Vector component |
| Plausibility | Pl(A) | [0,1] | 1 − Bel(A^c) | 357 | Used in Δ_A normalisation |
| Combinability factor | Δ(ς_1,ς_2) | ℝ | ≠ 0 required | 352 | Eq. 8.1 |
| Per-summand normaliser | Δ_i | ℝ | ≠ 0 for combinability | 354 | Used in β_i |
| Constant-mass parameter | k | [0,1] for BFs / ℝ for NSFs | – | 369 | Defines H_A^k, H_A^k |
| Focal point | ς_B | R^{N−2} | outside B | 373 | Eq. 8.24 |
| Discount level | i | {1,…,n−1} | – | 339 | Recursive bundle level |

## Worked examples

### Example 17: Ternary frame *(p.329)*
Setup: Θ = {θ_1, θ_2, θ_3}; introduce x = v_{{θ_1}}, y = v_{{θ_2}}, z = v_{{θ_3}}, u = v_{{θ_1,θ_2}}, v = v_{{θ_1,θ_3}}, w = v_{{θ_2,θ_3}}; v_Θ recovered by normalisation. 
The positivity constraints (7.5) become the system (7.6) above. B is the 6-dim region of R^6 cut out by these inequalities. Vertices of B: bel_∅ (origin), bel_x = e_1, bel_y = e_2, bel_z = e_3, bel_{x,y} = e_1+e_2+e_4 (etc.), bel_Θ = sum of all basis vectors (and equivalent normalised forms). All vertices are categorical BFs.

Takeaway: in low dimension the simplex can be visualised; the constraints u ≥ x+y, v ≥ x+z, w ≥ y+z are the "monotonicity-of-belief" axioms of Shafer.

### Example 18: Simplicial structure on a binary frame *(p.333)*
Setup: Θ_2 = {x, y}. Each Bel uniquely determined by [Bel(x), Bel(y)] = [m(x), m(y)]. Triangle in R^2:
- Vertex bel_Θ = [0,0]′ — vacuous (m(Θ)=1).
- Vertex bel_x = [1,0]′ — categorical Bayesian on {x}.
- Vertex bel_y = [0,1]′ — categorical Bayesian on {y}.
- P_2 = segment between bel_x and bel_y (Bayesian BFs satisfy m(x)+m(y)=1).
- L_1 distance to dominating Bayesian = 1 − m(x) − m(y) = m(Θ_2), constant.
- The limit simplex condition becomes ς(x) + ς(y) = 1, but for proper BFs we have m(x) + m(y) ≤ 1, so P_2 is a strict subset of the limit simplex line.

### Ternary fibre-bundle case study (Section 7.3.1) *(p.335–337)*
Setup: Θ_3 = {x,y,z}, n = 3, N = 8, N − 2 = 6. Project bel ↦ d = [m(x), m(y), m(z)]′; D = 3-simplex Cl(bel_x, bel_y, bel_z, bel_Θ) = the discounted Bayesian face. Fibre F(d) = 3-simplex of admissible {m({x,y}), m({x,z}), m({y,z})} given d, vertices when one of the three is maximal subject to total ≤ 1 − Σm(singletons). Result: B_3 is locally R^3 × Δ^3, globally a 6-simplex.

The takeaway proven by induction: a recursive decomposition into bases-of-i-additive BFs and fibres-of-residual-mass at each cardinality level i = 1,…,n−1, all of which are simplices.

### Example 19: Zero normalisation factor *(p.353)*
Setup: NSFs ς_1 with focal elements A_1, A_2, A_3 with masses m_{ς_1}(A_1) = −1, m_{ς_1}(A_2) = m_{ς_1}(A_3) = 1; ς_2 has single focal element A_2 ⊊ A_1 with mass 1, and A_2 ∩ A_3 = ∅.
Combination: A_1 ∩ B = A_2 (with sign +1) and A_2 ∩ B = A_2 (with sign +1), giving Δ = 1·(−1) + 1·1 = 0.
Conclusion: pseudo-NSFs can have zero combinability denominator even when focal-element intersections are non-empty. This is the failure mode (8.1) is testing for.

### Geometry of Dempster's rule in B_2 (toy problem 8.6.1) *(p.364–368)*
Setup: Θ_2 = {x,y}, Bel = [m_b(x), m_b(y)]′, Bel′ = [k, l]′ with k = m′(x), l = m′(y).
Closed form (8.16): m_{Bel⊕Bel′}(x) = 1 − (1−m(x))(1−k)/(1 − m(x)l − m(y)k), similarly for y.
Foci (when m(Θ_2) ≠ 0): F_x(Bel) = (1, −m(Θ)/m(x)) — a point outside B_2 below the bel_x corner; F_y(Bel) = (−m(Θ)/m(y), 1) — a point outside B_2 above the bel_y corner. These foci are the "missing points" in the affine images of the constant-mass loci k = const and l = const.
Geometric construction:
1. Line l_x = Bel ⊕ {Bel″ : m″(x) = k} passes through F_x(Bel) and the point P_x = l_x ∩ P (where P is the Bayesian segment).
2. Line l_y = similar through F_y(Bel) and P_y.
3. Bel ⊕ Bel′ = l_x ∩ l_y.

Degenerate case m(Θ_2) = 0 (Bel = P is Bayesian): the foci go to infinity / coincide with vertices. F_x = Bel_x. Algorithm 18 breaks because the lines collapse onto v(P).

## Figures of interest

- **Fig. 7.1 (p.332)**: Belief space concept — small triangle (Bel_Θ, Bel_A, Bel_B) showing **bel** as convex combination of vertices, with m(A) and m(B) as barycentric coordinates and the Bayesian sub-face P highlighted.
- **Fig. 7.2 (p.333)**: Belief space B_2 for binary frame — right triangle in R^2 with vertices bel_Θ=[0,0]′, bel_x=[1,0]′, bel_y=[0,1]′, hypotenuse = P_2 (Bayesian BFs).
- **Fig. 7.3 (p.337)**: Bundle structure of B_3 — left panel shows base D (3-simplex with vertices bel_x, bel_y, bel_z, bel_Θ); right panel shows fibre F(d) (3-simplex parameterised by m({x,y}), m({x,z}), m({y,z})) over a base point d.
- **Fig. 8.1 (p.353)**: Two non-combinable NSFs whose focal elements have non-empty pairwise intersection (illustrating Example 19's "zero normalisation").
- **Fig. 8.2 (p.359)**: Duality between non-combinable points and missing points — non-combinable points satisfy ∑α_iΔ_i = 0 in source space, missing points satisfy ∑β_i/Δ_i = 0 in image space; the map ⊕ is generically a bijection between source minus non-combinables and image minus missings.
- **Fig. 8.3 (p.361)**: Conditional and compatible subspaces in B_2 — ⟨Bel⟩ shown as the upper triangle (Bel, Bel_x, Bel_y) and C(Bel) = B_2 itself.
- **Fig. 8.5 (p.365)**: x-focus F_x(Bel) of ⟨Bel⟩ in B_2 with m(Θ_2) ≠ 0 — F_x(Bel) lies outside B_2 at coordinates (1, −m(Θ)/m(x)); each constant-mass line k = const through Bel ⊕ (·) passes through F_x(Bel) but missing it as a "missing point".
- **Fig. 8.6 (p.367)**: Graphical construction of Dempster's orthogonal sum in B_2 — illustrates Algorithm 18 with the two foci, the points P_x', P_y' on the Bayesian segment, and the intersection Bel ⊕ Bel′.
- **Fig. 8.7 (p.368)**: Degenerate case m(Θ_2) = 0 — when Bel = P, the focus F_x = bel_x and the construction collapses; for k = 1 the locus reduces to a single point regardless of l.
- **Fig. 8.8 (p.377)**: Geometric canonical decomposition of bel ∈ B_2 — bel = co_x ⊕ co_y where co_x and co_y are the unique simple support functions defined as line intersections (8.26).

## Criticisms of prior work

- **Walley's coherent-lower-prob approach** *(p.330)*: Walley proved coherent lower probabilities are closed under convex combination, hence convex combinations of belief functions are still coherent. Theorem 8 is **stronger**: it shows convex combinations of BFs remain *completely* monotone (i.e., still belief functions, not merely coherent lower probabilities). [1874] cited.
- **Smets's [1698] and Kramosil's [1064] solutions to canonical decomposition** *(p.377)*: Cuzzolin's geometric construction (Section 8.8 / Proposition 55) is presented as an *alternative* to the existing Smets and Kramosil solutions for the canonical decomposition problem, opening a path to a geometric solution of canonical decomposition for arbitrary frames. The advantage claimed: the geometric language requires only the convex closure and orthogonal sum operators.

## Design rationale

- **Use mass instead of belief as simplicial coordinates** *(p.331, eq. 7.8)*: BPA values m(A) are the natural barycentric coordinates of B because they are non-negative and sum to 1 — exactly the simplex structure. Belief values are convolutions and don't decompose conveniently. *Implication*: when storing BFs computationally, prefer the BPA representation.
- **Embed B in S = R^{N−2} via NSF extension** *(p.339, 352)*: Working only inside B is too restrictive because Dempster combinations of affine combinations naturally produce points outside B (negative-mass NSFs). Extending Dempster's rule to NSFs (Theorem 13) is what allows affine subspaces — and hence the geometric algorithm in Section 8.7 — to make sense.
- **Drop v(∅) and v(Θ) from coordinates** *(p.330, 339)*: The vacuous v_∅ = 0 is fixed; v_Θ = 1 is recoverable by normalisation. Storing N − 2 components instead of 2^n eliminates redundancy and aligns the dimension with the simplex identity.
- **Use foci instead of full constant-mass-loci images** *(p.376)*: Algorithm 19 detects ⟨Bel⟩ via 2^{|C_{Bel}|} − 3 focal points per focus (computed once per Bel, just by Bayes conditioning) instead of recomputing intersections of high-dimensional affine spaces. Foci are characteristic of Bel and shared across all combinations.
- **Algorithm 18 fails when m(Θ_2) = 0** *(p.368)*: explicit acknowledgement; the "construction" requires the vacuous mass to be non-zero so the foci are finite and distinct. Cuzzolin presents this not as a flaw but as a structural feature — Bayesian BFs degenerate to a lower-dimensional case.

## Open / research questions

### Chapter 7 (Section 7.5)

- **Question 1** *(p.344)*: "First of all, is it possible to extend the results of Chapter 7 to the case of infinite sample spaces?" Cuzzolin notes that random closed intervals, MV algebras, and random sets are the most promising continuous formulations; in the Borel interval case a BF is in 1–1 correspondence with an integrable function from a triangle onto [0,1]. Functional analysis required.
- **Question 2** *(p.344)*: "How can we extend the geometric language to other classes of uncertainty measures?" Candidates: monotone capacities, probability intervals / 2-monotone capacities, gambles / lower previsions. Geometric representations of previsions likely resemble both MV algebras and BFs on fuzzy sets. Chapter 17 outlines the geometry of 2-monotone capacities.

### Chapter 8 (Section 8.8)

- **Question 3** *(p.376)*: "Can the Dempster inversion problem, or 'canonical decomposition' (see Chapter 2, Proposition 4), be solved by geometric means?" Proposition 55 (geometric canonical decomposition in B_2 via line intersections) and the conjectured generalisation co_{x/y} = Cl(bel, bel_{x/y}) ∩ Cl(bel_Θ, bel_{x/y}) suggest yes. Alternative to Smets [1698] and Kramosil [1064].
- **Question 4** *(p.378)*: "What is the geometric behaviour of the other major combination rules?" Conjunctive and disjunctive (Smets), bold and cautious (Denoeux). A geometric description would characterise belief-function 'tubes' in B. Section 17 of the book addresses the conjunctive rule and Yager's rule.
- **Question 5** *(p.378)*: "Does our geometric construction of Dempster's rule apply, with suitable amendments, to the case of unnormalised belief functions contemplated under the open-world assumption?" Preliminary analysis in Chapter 17, Section 17.2.1.
- **Question 6** *(p.378)*: "How does the geometric treatment of rules of combination, including Dempster's rule, extend to belief measures on infinite domains?"

## Notable references cited

- `[357]` Ha et al. — analytical form of P[Bel] (consistent probabilities) studied further *(p.329)*
- `[1583]` Shafer 1976 — original axioms of belief functions *(p.329)*
- `[1874]` Walley — coherent lower previsions, closed under convex combination *(p.330)*
- `[551]` Husemoller / fibre-bundle reference — definition of smooth fibre bundle *(p.337–338)*
- `[327]` Cuzzolin's earlier paper — material of Chapter 8 first published *(p.352)*
- `[1677]` Smets — transferable belief model, conjunctive combination *(p.360)*
- `[326]` Cuzzolin earlier — antipodal face concept *(p.372)*
- `[364]` Cuzzolin — binary canonical decomposition source *(p.376)*
- `[1698]` Smets — canonical decomposition algorithm for BFs *(p.377)*
- `[1064]` Kramosil — alternative canonical decomposition *(p.377)*
- `[715]` Combinatorial identity reference (Volume 3, Eq. 1.9) *(p.347)*
- `[1086]` Definition of "consistent" probability with Bel *(p.328)*
- `[1296]` i-additive belief functions *(p.343)*
- `[758]` Ha et al. — proof of P[Bel] sum-of-simplices form *(p.328)*

## Implementation notes for propstore

- **`propstore.dimensions` / `propstore.belief_set`**: the N − 2 = 2^n − 2 simplex dimension count is load-bearing for any belief-set storage. If propstore wants to store BFs as points in B, the natural representation is the BPA vector (the simplicial coordinates of eq. 7.8). Existing storage already keeps focal-element + mass pairs; this aligns with simplicial coordinates.
- **`propstore.world` / ATMS environments labeled with focal elements**: the categorical BFs Bel_A correspond to "all mass on environment A" — these are the *vertex labels* of the belief simplex. ATMS environments could be tagged with their associated bel_A coordinate when materialising belief functions for inspection.
- **`propstore.belief_set.ic_merge` / Dempster combination**: Theorem 15's convex decomposition Bel ⊕ Bel′ = ∑ μ(A) Bel ⊕ Bel_A reduces a full Dempster combination to a convex combination of *Bayes conditionings*. This matters because Bayes conditioning Bel|A is a O(|2^Θ|) operation whereas naive Dempster is O(|2^Θ|^2). Useful for any fast-path implementation of ⊕ in propstore.
- **`propstore.belief_set.ic_merge` (cont.)**: Algorithm 19 gives a *geometric* construction with even better cache properties — the foci ς_B are computed once per Bel and reused. Could underwrite an "incremental Dempster" path when one operand is reused (e.g., a fixed model belief combined with many evidence updates).
- **Provenance discipline**: Cuzzolin's "missing-points" duality (Section 8.4.2) is meaningful for propstore's non-commitment principle. The image of an affine combination under Bel ⊕ (·) generically has dimension *strictly less than* the source minus the missing-point subspace M. Combining beliefs may *lose* representational expressiveness; a faithful storage layer should not collapse the source affine combination just because one image happens to be combinable. Storage must hold all operands, render must compute ⊕.
- **`propstore.support_revision`**: the recursive bundle (Theorems 11–12) gives a layered view of belief: level 1 = singleton mass, level 2 = pair mass, …, level n−1 = mass on size-(n−1) sets. This is a natural axis for *partial* support revision: revise mass-on-singletons leaving higher-cardinality mass intact, or vice versa. Each level admits its own simplex coordinate chart.
- **`propstore.defeasibility`**: conditional subspaces ⟨Bel⟩ characterise the "possible futures" of Bel under any combinable update (p.351). For CKR-style defeasible reasoning, ⟨Bel⟩ is the set of belief states reachable from Bel by any non-conflicting evidence — useful as the *envelope* over which exception injection can range without forcing Bel → ⊥.
- **No fabricated confidence**: focal points ς_B (eq. 8.24) sit *outside* the belief space. Any propstore module that computes them as intermediates must not present them as belief functions; they are tools for affine intersection, not admissible states.

## Quotes worth preserving

- "B is then a simplex." *(Corollary 3, p.333)* — the headline result of Chapter 7.
- "It is well known that Dempster sums involving categorical belief functions, Bel ⊕ Bel_A, can be thought of as applications of (a generalised) Bayes' rule to the original belief function Bel, when conditioning with respect to an event A: Bel ⊕ Bel_A ≐ Bel|A." *(p.357)* — the bridge between Dempster combination and Bayes conditioning.
- "Strikingly, for any subset A, the resulting affine spaces *have a common intersection for all k ∈ [0,1]*, which is therefore characteristic of Bel. We call this the A-th *focus* of the conditional subspace." *(p.364)* — discovery of foci as belief-function invariants.
- "Bases and fibres are simply geometric counterparts of the mass assignment mechanism." *(p.340)* — the unifying intuition behind the bundle construction.
- "All the points of this section are sum functions satisfying the normalisation axiom ∑_A m_ς(A) = 1, or *normalised sum functions* (NSFs). NSFs are the natural extensions of belief functions in our geometric framework." *(p.339)*

---

## Boundary content (Chapter 9 opener, pp. 389–395)

PDF range nominally extends to 413 ⇒ briefly: Chapter 9 ("Three equivalent models") begins p.389 and shows belief, plausibility (Pl(A) = 1 − Bel(A^c) = ∑_{B∩A≠∅} m(B)) and commonality (Q(A) = ∑_{B⊇A} m(B)) functions are all sum functions on 2^Θ with their own simplicial geometry. **Definitions** (basic plausibility μ, basic commonality q): μ(A) = (−1)^{|A|+1} ∑_{C⊇A} m(C) for A ≠ ∅ (eq. 9.3); q(B) = (−1)^|B| (1 − Pl(B)) = (−1)^|B| Bel(B^c) (eq. 9.7). **Theorem 24** (Bel BPA → BPlA via μ(A) = (−1)^{|A|+1} ∑_{C⊇A} m(C)). **Theorem 25** (∑_{A⊇{x}} μ(A) = m(x)). **Theorem 26**: the plausibility space PL is the simplex Cl(Pl_A, ∅ ⊊ A ⊆ Θ) with vertices Pl_A = − ∑_{∅⊊B⊆A} (−1)^|B| Bel_B (eq. 9.11). **Theorem 27**: vertex Pl_A is the plausibility vector of categorical Bel_A. The full Chapter 9 development belongs to Chunk #6.
