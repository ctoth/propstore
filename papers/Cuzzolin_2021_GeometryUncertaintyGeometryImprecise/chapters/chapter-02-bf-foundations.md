# Chunk #2 — Chapter 2 (Belief functions) + Chapter 3 (Understanding belief functions)

**Book pages:** 31-108
**PDF idx:** 56-133

## STATUS: All pages 056-128 read (book pp. 31-108). PDF 129-133 fall on Chapter 4 opener and end-of-chunk; chunk content fully captured.

## Sections covered

- 2.1 (tail) Dempster's original setting (murder trial example, multivalued mappings Γ1, Γ2) — book p.34
- 2.2 Belief functions as set functions (2.2.1 Basic definitions: BPA, focal element, core, BF, vacuous BF; Moebius inversion; 2.2.2 Plausibility, doubt, commonality; 2.2.3 Bayesian belief functions) — pp.34-37
- 2.3 Dempster's rule of combination (2.3.1 Definition / orthogonal sum, 2.3.2 Weight of conflict, 2.3.3 Conditioning belief functions) — pp.38-41
- 2.4 Simple and separable support functions (2.4.1 Heterogeneous and conflicting evidence, 2.4.2 Separable support functions, 2.4.3 Internal conflict, 2.4.4 Inverting Dempster's rule / canonical decomposition) — pp.41-45
- 2.5 Families of compatible frames of discernment (2.5.1 Refinings, 2.5.2 Families of frames, 2.5.3 Consistent and marginal BFs, 2.5.4 Independent frames, 2.5.5 Vacuous extension) — pp.45-50
- 2.6 Support functions (2.6.1 Families of compatible support functions in the evidential language, 2.6.2 Discerning the relevant interaction of bodies of evidence) — pp.51-53
- 2.7 Quasi-support functions (2.7.1 Limits of separable support functions, 2.7.2 Bayesian belief functions as quasi-support, 2.7.3 Bayes' theorem, 2.7.4 Incompatible priors) — pp.53-56
- 2.8 Consonant belief functions — pp.56-57
- 3 (opener) — p.59
- 3.1 Multiple semantics (3.1.1 Dempster's multivalued mappings; 3.1.2 BFs as generalised non-additive probabilities; 3.1.3 BFs as inner measures; 3.1.4 BFs as credal sets; 3.1.5 BFs as random sets; 3.1.6 Behavioural interpretations; 3.1.7 Common misconceptions) — pp.59-72
- 3.2 Genesis and debate (3.2.1 Early support, 3.2.2 Constructive probability and Shafer's canonical examples, 3.2.3 Bayesian vs belief reasoning, 3.2.4 Pearl's criticism, 3.2.5 Issues with multiple interpretations, 3.2.6 Rebuttals and justifications) — pp.73-79
- 3.3 Frameworks (3.3.1 Multivalued-mapping frameworks: hints, Kramosil, signed BFs, Hummel-Landy, context models, conditional/probabilistic multivalued mappings, non-monotonic compatibility, PMRVs; 3.3.2 Smets's TBM; 3.3.3 DSmT; 3.3.4 Gaussian (linear) BFs; 3.3.5 BFs on generalised domains: lattices, distributive lattices, Boolean algebras; 3.3.6 Qualitative models; 3.3.7 Intervals and sets of belief measures: IBSs, interval BPAs, generalised BPAs; 3.3.8 Other frameworks: Zadeh simple view, Lowrance-Strat, Improved evidence, Josang subjective evidential, Connectionist, Hybrid ATMS, Minimum commitment, Mass assignments, Exponential possibilities, Set-theoretic, Temporal, Conditioned DS / MDS, Self-conditional, Plausible reasoning) — pp.79-108

## Chapter overview

These two chapters constitute the formal heart of the book. Chapter 2 establishes Shafer's mathematical theory of evidence as a self-contained calculus: BPAs `m: 2^Θ → [0,1]`, belief / plausibility / commonality functions, Dempster's rule of combination ⊕, weight of conflict, conditioning, simple and separable support functions, the canonical decomposition (a Moebius-style inversion of ⊕ via weights `w(A)`), the algebra of refinings between compatible frames, support and quasi-support functions, and consonant BFs. The binary "Ming vase", ternary `{x,y,z}`, four-element `{θ1,…,θ4}` worked examples, and the alibi/murder-trial canonical examples are introduced; these recur throughout the rest of the book to anchor geometric intuition.

Chapter 3 then steps back from the Shafer-Dempster axioms and surveys (i) the multiple semantic readings of a belief function (multivalued maps, non-additive infinitely-monotone capacities, inner measures, credal sets, random sets, betting/B-consistency interpretations) and (ii) the long historical debate (early support, Pearl's criticism, Smets's, Dubois-Prade's and Shafer's replies, Halpern-Fagin's two-views thesis), and (iii) the manifold downstream frameworks built on or around BFs: Smets's TBM (credal/pignistic levels, BetP, unnormalised BFs, open-world assumption), Dezert-Smarandache theory with hyperpower sets, Dempster-Liu Gaussian (linear) BFs, lattice/Boolean-algebra extensions, qualitative DS, imprecise belief structures and generalised BPAs, and a long list of less prominent but historically interesting proposals (Lowrance-Grasper, Josang's beta-based subjective logic, ATMS hybrids, Mahler's MDS, plausible-reasoning pl-functions, etc.).

Chapter 2 sets up the formal objects on which the rest of the book's geometric programme operates; Chapter 3 establishes that those objects are theoretically contested and that the specific geometric/operational choices made later (mass-space coordinates, simplex of probabilities, consonant subspace, conditional cones) are choices among genuine alternatives, not bookkeeping.

## Definitions

### Definition 4 (Basic probability assignment, BPA) *(p.34)*
A BPA over an FoD Θ is a set function `m: 2^Θ → [0,1]` with `m(∅) = 0` and `Σ_{A⊆Θ} m(A) = 1`. `m(A)` is the basic probability number / mass; subsets with `m(A) > 0` are focal elements; the union of focal elements is the *core* `C_m`.

### Definition 5 (Belief function, BF) *(p.35)*
The belief function associated with BPA `m` is `Bel(A) = Σ_{B⊆A} m(B)`. Eq.(2.2).

### Definition 6 (Bayesian belief function) *(p.37)*
A BF satisfying additivity `Bel(A) + Bel(Ā) = 1` for all `A ⊆ Θ`.

### Definition 7 (Orthogonal sum / Dempster combination) *(p.38)*
`Bel1 ⊕ Bel2` is the unique BF whose focal elements are intersections of focal elements of `Bel1, Bel2`, with BPA Eq.(2.6). Combinable iff cores are not disjoint.

### Definition 8 (Weight of conflict) *(p.40)*
`K(Bel1,Bel2) = log[1/(1 - Σ_{B∩C=∅} m1(B)m2(C))]`. Eq.(2.7).

### Definition 9 (Simple support function) *(p.41)*
For focus `A` and degree `σ ∈ [0,1]`: `m(A) = σ`, `m(Θ) = 1-σ`, all else 0; equivalently Eq.(2.9).

### Definition 10 (Separable support function) *(p.43)*
A BF that is either simple or equal to the orthogonal sum `Bel = Bel1 ⊕ … ⊕ Beln` with each `Bel_i` simple, `n ≥ 1`.

### Definition 11 (Weight of internal conflict W) *(p.44)*
`W = 0` if `Bel` is simple; otherwise `W = inf K(Bel1,…,Beln)` over decompositions of `Bel` into simple SSFs. Equals `K` of the canonical decomposition.

### Definition 12 (Refining) *(p.45)*
A map `ρ: 2^Θ → 2^Ω` is a refining iff (1) `ρ({θ}) ≠ ∅ ∀θ`, (2) `ρ({θ}) ∩ ρ({θ'}) = ∅` for distinct singletons, (3) `∪_θ ρ({θ}) = Ω`. Then `ρ(A) = ∪_{θ∈A} ρ({θ})`.

### Definition 13 (Inner / outer reduction associated with refining ρ) *(p.46)*
Eq.(2.11) `ρ̄(B) = {θ ∈ Θ | ρ({θ}) ⊆ B}` (inner); Eq.(2.12) `ρ̃(B) = {θ ∈ Θ | ρ({θ}) ∩ B ≠ ∅}` (outer).

### Definition 14 (Family of compatible frames of discernment) *(p.47)*
Non-empty collection F of frames with refinings R closed under: composition, identity-of-coarsenings, identity-of-refinings, existence-of-coarsenings (any disjoint partition of Ω∈F induces a coarsening), existence-of-refinings (any θ∈Θ∈F can be split into n elements), existence of common refinements (every pair has one).

### Definition 15 (Consistent BFs on compatible frames) *(p.48)*
`Bel1, Bel2` on Θ1, Θ2 are consistent iff `Bel1(A1) = Bel2(A2)` whenever `A1 ⊂ Θ1`, `A2 ⊂ Θ2` and `ρ1(A1) = ρ2(A2)` in the minimal refinement `Θ1 ⊗ Θ2`.

### Definition 16 (Independent frames) *(p.49)*
Compatible frames Θ1,…,Θn with refinings ρi to their minimal refinement are independent iff `ρ1(A1) ∩ … ∩ ρn(An) ≠ ∅` for any non-empty `Ai ⊂ Θi`. Eq.(2.14).

### Definition 17 (Boolean algebra) *(p.49)*
Set U with `∩, ∪, ¬` satisfying standard properties.

### Definition 20 (Vacuous extension) *(p.50)*
A BF `Bel(A) = max_{B:ρ(B)⊆A} Bel(B)` extended from a coarser frame to a finer one — vacuous BF on Ω restricted to Θ stays vacuous.

### Definition 21 (Support function) *(p.51)*
A BF `Bel: 2^Θ → [0,1]` is a support function iff there exists a refinement Ω of Θ and a separable support function `Bel'` on Ω with `Bel = Bel'|2^Θ`.

### Definition 22 (Sharp impact / exhausting frame) *(p.52)*
Evidence E affects family F sharply iff some Ω ∈ F carries `s_E^Ω` for every Θ that is a refinement of Ω. Such Ω is said to *exhaust* the impact.

### Definition 23 (Discerning relevant interaction) *(p.53)*
Frame Ω in family F discerns the relevant interaction of evidence E1 and E2 iff `ρ̃(A∩B) = ρ̃(A) ∩ ρ̃(B)` for any focal element `A` of `s_{E1}^Θ` and focal element `B` of `s_{E2}^Θ`, where Θ is a refinement of Ω with outer reduction `ρ̃`.

### Definition 24 (Quasi-support function) *(p.53)*
A BF that is the limit on Θ of a sequence of separable support functions defined on a refinement Ω of Θ. Eq.(2.17) limit definition.

### Definition 25 (Relative plausibilities of singletons / contour function) *(p.54)*
`pl_s: Θ → [0,∞)` such that `pl_s(θ) = c · Pl_s({θ})` (constant c independent of θ). Eq.(2.18).

### Definition 26 (Consonant belief function) *(p.56)*
A BF whose focal elements `A1 ⊂ A2 ⊂ … ⊂ Am` are nested.

### Definition 27 (Belief function as superadditive set function) *(p.64)*
`Bel: 2^Θ → [0,1]` with `Bel(∅)=0`, `Bel(Θ)=1`, and the n-monotonicity / superadditivity inclusion-exclusion bound Eq.(3.6) `Bel(∪Ai) ≥ Σ Bel(Ai) − Σ Bel(Ai∩Aj) + … + (−1)^{n+1} Bel(A1∩…∩An)`. Equivalent to Definition 5 (Proposition 18); these are *infinitely monotone capacities*.

### Definition 28 (Inner probability) *(p.65)*
`P_*(A) = max{P(B) | B ⊆ A, B ∈ F}` for an extending P on σ-field F over X. Eq.(3.7).

### Definition 29 (Betting function R / B-consistency) *(p.70)*
`R: L → {0,1}` binary on gambles such that for each `X ∈ L` there is `α_X ∈ R` with `R(X+α)=0` for `α<α_X` and `R(X+α)=1` for `α ≥ α_X`. *(Also Definition 30 B-consistency, p.71)*.

### Definition 30 (B-consistency) *(p.71)*
Betting function R is B-consistent iff for all gambles X1..XN, Y1..YM with `Σ G_B(Xi) ≤ Σ G_B(Yj)` for every belief valuation B, also `Σ Buy_R(Xi) ≤ Σ Buy_R(Yj)`.

### Definition 31 (Signed measure) *(p.84)*
`μ: F → R* = (-∞,+∞) ∪ {-∞,+∞}` σ-additive with `μ(∅)=0`, taking at most one of `±∞`. Eq.(3.23).

### Definition 32 (Space of probabilistic opinions of experts) *(p.85)*
Triple `(N, K, ⊗)` where `N = {(E,μ,P) | μ measure on E, P = {p_ω}_{ω∈E}}` with constraint Eq.(3.24); ⊗ is the Bayesian-style binary combination Eq.(3.26).

### Definition 33 (Context conditioning of vague characteristics) *(p.87)*
For `γ1, γ2: C → 2^Θ`: `(γ1|γ2)(c) = γ1(c)` if `γ1(c) ⊆ γ2(c)`, else `∅`. Eq.(3.27).

### Definition 34 (Probabilistic multivalued mapping, PMM) *(p.87)*
`Γ*: Ω → 2^{2^Θ × [0,1]}` such that `Γ*(ω) = {(A_{i_1}, P(A_{i_1}|ω)), …, (A_{i_m}, P(A_{i_m}|ω))}` with disjoint nonempty `A_{i_j}` summing in conditional probability to 1.

### Definition 35 (Type I compatibility relation) *(p.88)*
Relation `C` on `Ω × Θ` with (i) `∀ω ∃θ: C(θ,ω)=1` and (ii) `∀θ ∃ω: C(θ,ω)=1`.

### Definition 36 (Type II compatibility relation) *(p.89)*
Relation `C` on `X × Θ` (with `X = 2^Ω \ {∅}`) such that for each `X ∈ X` there is some θ with `C(X,θ) = 1`.

### Definition 37 (Probabilistic multivalued random variable, PMRV) *(p.89)*
`μ: Ω × Θ → [0,1]` with `Σ_{θ∈Θ} μ(ω,θ) = 1` for all ω. Inverse Eq.(3.28); induced measure Eq.(3.29).

### Definition 38 (Hyperpower set D^Θ, DSmT) *(p.93)*
For frame `Θ = {θ1,…,θn}`: smallest set containing `∅, θ1, …, θn`, closed under both `∪` and `∩`. Cardinality follows the Dedekind numbers (1, 2, 5, 19, 167, 7580, …).

### Definition 39 (Generalised basic belief assignment, DSmT) *(p.94)*
`m: D^Θ → [0,1]` with `m(∅)=0` and `Σ_{A∈D^Θ} m(A) = 1`.

### Definition 40 (Lower / upper preference relations) *(p.98)*
Given preference `≻` on Ω and multivalued `Γ: Ω → 2^Θ`: `A ≻_* B ⇔ Γ_*(A) ≻ Γ_*(B)`, `A ≻^* B ⇔ Γ^*(A) ≻ Γ^*(B)`. Eq.(3.33).

### Definition 41 (Generalised BPA, Augustin) *(p.102)*
A non-empty closed subset `S ⊆ M(Ω, P(Ω))` of all classical BPAs.

### Definition 42 (pl-function, Guan-Bell plausible reasoning) *(p.108)*
`pl(θ|x): X → [0,1]` per `θ ∈ Θ` representing the extent to which we do not wish to rule out θ after observing `x ∈ X`.

## Theorems, propositions, lemmas

- **Proposition 1** *(p.37)* — `Bel` is Bayesian iff there is `p: Θ → [0,1]` with `Σ p(θ) = 1` and `Bel(A) = Σ_{θ∈A} p(θ)`.
- **Proposition 2** *(p.39)* — Three equivalent obstructions to combinability: `Bel1 ⊕ Bel2` does not exist iff their cores are disjoint iff `∃ A: Bel1(A) = Bel2(Ā) = 1`.
- **Proposition 3** *(p.40)* — Additivity of weights of conflict: `K(Bel1,…,Bel_{n+1}) = K(Bel1,…,Beln) + K(Bel1⊕…⊕Beln, Bel_{n+1})`.
- **Proposition 4** *(p.43)* — Canonical decomposition: every non-vacuous separable BF with core C admits a unique collection of non-vacuous SSFs `Bel1,…,Beln` with distinct cores `C_{Bel_i} ⊊ C`.
- **Proposition 5** *(p.43)* — Focal elements of a separable SSF closed under non-empty intersection.
- **Proposition 6** *(p.44)* — Every non-dogmatic BF admits a unique canonical decomposition `m = ⊕_{A⊊Θ} m_A^{w(A)}` with weights `w(A) = Π_{B⊇A} Q(B)^{(-1)^{|B|-|A|+1}}` (potentially negative — pseudo-belief functions).
- **Theorem 1** *(p.47)* — Existence of *minimal refinement* `Θ1 ⊗ … ⊗ Θn` for any compatible frames; uniqueness up to coarsening (Proposition 8, p.47).
- **Proposition 7** *(p.46)* — Refining ρ has unique inner reduction ρ̄ and outer reduction ρ̃, with `ρ̄(A) ⊆ ρ̄(B), ρ̃(A) ⊆ ρ̃(B)` for `A ⊆ B`. *(Reconstructed from text on p.46.)*
- **Proposition 9** *(p.51)* — `Bel` is a support function iff `m(C) > 0` (its core has positive mass).
- **Proposition 10** *(p.52)* — Sufficient condition `ρ̃(A∩B) = ρ̃(A) ∩ ρ̃(B)` (for focal elements A of s1, B of s2) implies `(s1⊕s2)|2^Ω = (s1|2^Ω) ⊕ (s2|2^Ω)` — relevant interaction discerned. Eq.(2.16).
- **Proposition 11** *(p.53)* — The class of BFs is closed under the limit operator (2.17).
- **Proposition 12** *(p.53)* — Every BF that is not a support function is a limit (in the (2.17) sense) of separable SSFs on some refinement Ω.
- **Proposition 13** *(p.54)* — If `Bel(A) > 0`, `Bel(Ā) > 0`, and `Bel(A) + Bel(Ā) = 1`, then Bel is quasi-support (in particular, Bayesian BFs are quasi-support unless concentrated on a single element).
- **Proposition 14 (Bayes' theorem in BF setting)** *(p.54)* — For Bayesian `Bel0` and support function `s`, with relative singleton-plausibilities `pl_s`, `Bel'({θ}) = K · Bel0({θ}) pl_s(θ)`, `K = (Σ Bel0({θ}) pl_s(θ))^{-1}`.
- **Proposition 15** *(p.55)* — Relative plausibilities multiply under combination: `pl_{s1⊕…⊕sn}(θ) ∝ Π pl_{si}(θ)`.
- **Proposition 16** *(p.56)* — Five equivalent characterisations of consonance: (1) nested focal elements; (2) `Bel(A∩B) = min(Bel(A), Bel(B))`; (3) `Pl(A∪B) = max(Pl(A), Pl(B))`; (4) `Pl(A) = max_{θ∈A} Pl({θ})`; (5) decomposition as `s1 ⊕ … ⊕ sn` with strictly nested foci.
- **Proposition 17** *(p.57)* — If `s1,…,sn` non-vacuous SSFs with foci C_i and `Bel = ⊕ s_i` is consonant with core C, then `C_i ∩ C` are nested.
- **Proposition 18** *(p.65)* — Definitions 27 (n-monotone superadditive capacity) and 5 (BPA-induced) are equivalent formulations of a BF.
- **Proposition 19** *(p.67)* — Closed convex sets of probabilities include Shafer's BFs as a special case (k-additive credal sets etc.; Miranda et al. result; 2-alternating capacity characterisation).
- **Proposition 20 (Kyburg)** *(p.68)* — Probability intervals from Dempster updating are included in (and may be strictly inside) those from Bayesian updating of the associated credal set.
- **Proposition 21** *(p.71)* — `Bel` is a BF iff there is a coherent (in Walley's sense) and B-consistent betting function R with `Bel(A) = Buy_R(1_A)`.
- **Proposition 22** *(p.71)* — A coherent betting function R is B-consistent iff there exists a BPA m with `Buy_R(X) = Σ m(A) min_{θ∈A} X(θ)`.
- **Theorem 2** *(p.84)* — Monotonicity of partial-compatibility-induced BFs: `Bel_{C̄1}(A) ≤ Bel_{C̄2}(A)`, `Pl_{C̄1}(A) ≤ Pl_{C̄2}(A)` whenever `Dom(C1) ⊂ Dom(C2)`.
- **Proposition 23 (Augustin, generalised belief accumulation)** *(p.103)* — `L(A) = min_{m∈S} Σ_{∅≠B⊆A} m(B)` is well defined and is a lower probability.

## Equations

$$
C_m = \bigcup_{A \subseteq \Theta : m(A) > 0} A
$$
**(Eq. 2.1, p.35)** Core of a BPA — union of focal elements.

$$
Bel(A) = \sum_{B \subseteq A} m(B)
$$
**(Eq. 2.2, p.35)** Belief of A is total mass of subsets contained in A.

$$
m(A) = \sum_{B \subseteq A} (-1)^{|A \setminus B|} Bel(B)
$$
**(Eq. 2.3, p.36)** Moebius inversion recovers BPA from BF.

$$
Pl(A) = 1 - Bel(\bar A) = \sum_{B \cap A \neq \emptyset} m(B)
$$
**(Eq. 2.4, p.36)** Plausibility / upper probability.

$$
Q(A) = \sum_{B \supseteq A} m(B)
$$
**(Eq. 2.5, p.36)** Commonality — mass that may "move freely" through A.

$$
m_{Bel_1 \oplus Bel_2}(A) = \frac{\sum_{B \cap C = A} m_1(B) m_2(C)}{1 - \sum_{B \cap C = \emptyset} m_1(B) m_2(C)}
$$
**(Eq. 2.6, p.38)** Dempster's rule of combination (orthogonal sum).

$$
\mathcal{K} = \log \frac{1}{1 - \sum_{B \cap C = \emptyset} m_1(B) m_2(C)}
$$
**(Eq. 2.7, p.40)** Weight of conflict (logarithm of normalising factor).

$$
Pl(A | B) = \frac{Pl(A \cap B)}{Pl(B)}
$$
**(Eq. 2.8, p.41)** Dempster's rule of conditioning, plausibility form. Equivalent BF form: `Bel(A|B) = (Bel(A∪B̄) - Bel(B̄)) / (1 - Bel(B̄))`.

$$
Bel(B) = \begin{cases} 0 & B \not\supset A \\ \sigma & B \supset A,\, B \neq \Theta \\ 1 & B = \Theta \end{cases}
$$
**(Eq. 2.9, p.41)** Simple support function focused on A with weight σ.

$$
m = \bigoplus_{A \subsetneq \Theta} m_A^{w(A)}
$$
**(Eq. 2.10, p.44)** Canonical decomposition into elementary simple BFs `m_A^w` where `m_A^w(A) = 1-w`, `m_A^w(Θ)=w`.

$$
\bar{\rho}(B) = \{ \theta \in \Theta : \rho(\{\theta\}) \subseteq B \}
$$
**(Eq. 2.11, p.46)** Inner reduction of a refining.

$$
\tilde{\rho}(B) = \{ \theta \in \Theta : \rho(\{\theta\}) \cap B \neq \emptyset \}
$$
**(Eq. 2.12, p.46)** Outer reduction.

$$
m_1(A) = \sum_{A = \bar{\rho}(B)} m_2(B)
$$
**(Eq. 2.13, p.49)** Mass relation between a BF and its restriction (marginal).

$$
\rho_1(A_1) \cap \cdots \cap \rho_n(A_n) \neq \emptyset
$$
**(Eq. 2.14, p.49)** Independence condition for compatible frames.

$$
\bar{\rho}(A \cap B) = \bar{\rho}(A) \cap \bar{\rho}(B)
$$
**(Eq. 2.16, p.52)** "Discerning the relevant interaction" condition (outer-reduction commutes with intersection on focal pairs).

$$
\lim_{i \to \infty} f_i(A) = f(A) \quad \forall A \subset \Theta
$$
**(Eq. 2.17, p.53)** Pointwise limit of set functions on a finite power set.

$$
pl_s(\theta) = c \cdot Pl_s(\{\theta\})
$$
**(Eq. 2.18, p.54)** Contour function — relative plausibility of singletons under a support function.

$$
Bel(A) = P(\{\omega | \Gamma(\omega) \subset A\})
$$
**(Eq. 3.1, p.62)** BF induced by a multivalued mapping Γ from a probability space (Ω,P).

$$
Pl(A) = P(\{\omega | \Gamma(\omega) \cap A \neq \emptyset\})
$$
**(Eq. 3.2, p.62)** Plausibility induced by Γ.

$$
\mathcal{C} = \{(\omega,\theta) | \theta \in \Gamma(\omega)\}
$$
**(Eq. 3.3, p.63)** Compatibility relation associated with Γ.

$$
\Gamma_1(\omega_1) \cap \Gamma_2(\omega_2) \neq \emptyset
$$
**(Eq. 3.4, p.64)** Non-conflict condition for combining two multivalued mappings.

$$
\Omega = \{(\omega_1,\omega_2) \in \Omega_1 \times \Omega_2 | \Gamma_1(\omega_1) \cap \Gamma_2(\omega_2) \neq \emptyset\},\quad P = P_1 \times P_2 |_\Omega,\quad \Gamma(\omega_1,\omega_2) = \Gamma_1(\omega_1) \cap \Gamma_2(\omega_2)
$$
**(Eq. 3.5, p.64)** Conditional product space construction underlying Dempster's rule.

$$
Bel(A_1 \cup \ldots \cup A_n) \geq \sum_i Bel(A_i) - \sum_{i<j} Bel(A_i \cap A_j) + \cdots + (-1)^{n+1} Bel(A_1 \cap \ldots \cap A_n)
$$
**(Eq. 3.6, p.65)** n-monotonicity (superadditivity) of a BF.

$$
P_*(A) = \max\{P(B) | B \subseteq A, B \in \mathcal{F}\}
$$
**(Eq. 3.7, p.65)** Inner probability.

$$
\mathcal{F} = \{\mathcal{C} \cap (E \times \Theta) | E \subset \Omega\}
$$
**(Eq. 3.8, p.65)** σ-field on the compatibility relation domain.

$$
Bel \leq Bel' \;\equiv\; Bel(A) \leq Bel'(A)\; \forall A \subset \Theta
$$
**(Eq. 3.9, p.66)** Weak inclusion order.

$$
\mathcal{P}[Bel] = \{P \in \mathcal{P} | P(A) \geq Bel(A)\,\forall A\}
$$
**(Eq. 3.10, p.66)** Credal set associated with BF — set of consistent / dominating probabilities.

$$
\underline{P}(A) = \inf_{P \in Cr} P(A),\quad \overline{P}(A) = \sup_{P \in Cr} P(A)
$$
**(Eq. 3.11, p.66)** Lower and upper probabilities of a credal set.

$$
P^\pi[Bel](\{x_{\pi(i)}\}) = \sum_{A \ni x_{\pi(i)},\, A \not\ni x_{\pi(j)}\, \forall j<i} m(A)
$$
**(Eq. 3.12, p.67)** Permutation-induced extremal probability of the BF credal set (k-additive characterisation, Miranda et al.).

$$
\underline{P}(A \cup B) = 0.75 < 0.9 = \underline{P}(A) + \underline{P}(B) - \underline{P}(A \cap B)
$$
**(Eq. 3.13, p.68)** Kyburg counterexample: lower envelope of Bernoulli-based credal set fails superadditivity → not a BF.

$$
Bel(A \cup B) \geq Bel(A) + Bel(B) - Bel(A \cap B)
$$
**(Eq. 3.14, p.68)** 2-monotonicity of BFs (contrast with 3.13).

$$
\Gamma_*(A) = \{\omega \in \Omega : \Gamma(\omega) \subseteq A,\, \Gamma(\omega) \neq \emptyset\}
$$
**(Eq. 3.15, p.69)** Lower inverse of Γ.

$$
\Gamma^*(A) = \{\omega \in \Omega : \Gamma(\omega) \cap A \neq \emptyset\}
$$
**(Eq. 3.16, p.69)** Upper inverse of Γ.

$$
\text{if } X = \omega,\text{ then } \theta \in \Gamma(\omega)
$$
**(Eq. 3.17, p.70)** Multivalued meaning condition for Ville-style irrelevance argument.

$$
\sum_{\lambda \in \Lambda} p_\omega(\lambda) = 1 \text{ or } p_\omega(\lambda) = 0 \forall\lambda
$$
**(Eq. 3.24, p.85)** Probabilistic-opinion constraint per expert.

$$
x_\omega(\lambda) = \begin{cases}1 & p_\omega(\lambda)>0 \\ 0 & p_\omega(\lambda)=0\end{cases}
$$
**(Eq. 3.25, p.85)** Boolean opinion (indicator) of expert ω.

$$
(\mathcal{E},\mu,P) = (\mathcal{E}_1,\mu_1,P_1) \otimes (\mathcal{E}_2,\mu_2,P_2)
$$
**(Eq. 3.26, p.85)** Combination of probabilistic-opinion spaces.

$$
(\gamma_1 | \gamma_2)(c) = \begin{cases}\gamma_1(c) & \gamma_1(c) \subseteq \gamma_2(c) \\ \emptyset & \text{otherwise}\end{cases}
$$
**(Eq. 3.27, p.87)** Context conditioning of vague characteristics.

$$
\mu^{-1}(\theta) = \{\omega \in \Omega | \mu(\omega,\theta) \neq 0\}
$$
**(Eq. 3.28, p.89)** Inverse of a PMRV (gives a multivalued map).

$$
P_\Theta(\theta) = \sum_{\omega \in \mu^{-1}(\theta)} P_\Omega(\omega) \mu(\omega,\theta)
$$
**(Eq. 3.29, p.89)** Probability on Θ induced by a PMRV.

$$
BetP(A) = \sum_{B \subseteq A} \frac{m(B)}{|B|}
$$
**(Eq. 3.30, p.90)** Pignistic transform — Smets's TBM probability used at decision time.

$$
b(A) = \sum_{\emptyset \subseteq B \subseteq A} m(B) = Bel(A) + m(\emptyset)
$$
**(Eq. 3.31, p.92)** Implicability function for unnormalised BFs (open-world TBM).

$$
M(X) = \begin{bmatrix} \mu \\ \Sigma \end{bmatrix}
$$
**(Eq. 3.32, p.96)** Linear-belief-function representation by mean μ and covariance Σ over hyperplane focal elements.

$$
A \succ_* B \Leftrightarrow \Gamma_*(A) \succ \Gamma_*(B),\quad A \succ^* B \Leftrightarrow \Gamma^*(A) \succ \Gamma^*(B)
$$
**(Eq. 3.33, p.99)** Lower / upper preference relations propagated through Γ.

$$
A \succ_{Bel} B \Leftrightarrow Bel(A) > Bel(B),\quad A \succ_{Pl} B \Leftrightarrow B^c \succ_{Bel} A^c
$$
**(Eq. 3.34, p.99)** Preferences induced by BFs / plausibilities. Wong et al. axiomatisation: asymmetry, negative transitivity, dominance, partial monotonicity, non-triviality.

$$
\mathbf{m}' = \{ m_1 \circledast m_2 | m_1 \in \mathbf{m}_1, m_2 \in \mathbf{m}_2 \}
$$
**(Eq. 3.35, p.101)** IBS combination as set of all pointwise combinations.

$$
m^-(A) = \min_{(m_1,m_2)} m_1 \circledast m_2(A),\quad m^+(A) = \max_{(m_1,m_2)} m_1 \circledast m_2(A)
$$
**(Eq. 3.36, p.101)** IBS combination via interval bounds.

$$
m_{1 \oplus 2}(A \cap B) \propto m_1(A) m_2(B) \alpha_\oplus(A,B),\quad \alpha_\oplus(A,B) = \frac{\rho(A \cap B)}{\rho(A)\rho(B)}
$$
**(Eq. 3.37, p.108)** Mahler MDS / agreement-function generalisation of Dempster's rule.

## Geometric structures

Chapter 2 mostly stays algebraic; geometry surfaces in passing references for chapters 7+. Key items the geometric programme will lean on:

- **Probability simplex** Δ_Θ — vertex `p({θ}) = 1` for each `θ ∈ Θ`. Dimension `|Θ|−1`. Drawn for ternary frames as a triangle (Fig.3.3, p.67; Fig.3.4, p.72; Fig.3.11, p.101). Bayesian BFs sit at this simplex.
- **Credal set `P[Bel]` of a BF** — *polytope inside* Δ_Θ whose face boundaries are parallel to level sets `P(A) = const` for events A. The boundaries that are *parallel* to such level sets distinguish "BF credal sets" from arbitrary credal sets (Fig.3.4(a) vs (b), p.72). Vertices given by Eq.(3.12), one per permutation π of singletons.
- **Belief space B_Θ** of all BFs on Θ — implicit; in the binary case `B_2` is a triangle in `R^2` with vertex coordinates `Bel_x = [0,0]'`, `Bel_y = [0,0]'`, and `Bel_Θ = [0,0]'` (Fig.3.11, p.101). The probability simplex `P_2` sits inside as the hypotenuse.
- **Imprecise belief structure m** as a *rectangular subset of mass space* — generated by interval bounds `[a_i, b_i]` on each focal element's mass (Fig.3.11, p.101).
- **Hyperpower set `D^Θ` (Dedekind lattice)** — DSmT space of all `∪/∩` combinations of frame elements; cardinalities `1, 2, 5, 19, 167, 7580…` (Dedekind numbers, OEIS A014466) — Fig.3.9, p.94.
- **Family of compatible frames** — algebraic/lattice structure on Boolean subalgebras of a common refinement (Fig.2.4, p.46; Fig.2.5, p.48 — number-system example).
- **Gaussian / linear belief function focal elements** — parallel hyperplanes in R^n, each carrying a Gaussian density; see Fig.3.10, p.96. Mean-covariance representation Eq.(3.32).
- **Consonant subspace** — BFs with nested foci `A1 ⊂ A2 ⊂ … ⊂ Am`. These will form the consonant subspace later in the book; characterised by max/min behaviour (Proposition 16) as in possibility theory.
- **TBM credal level / pignistic level** (Fig.3.8, p.91) — credal level holds BFs; pignistic transform `BetP` (Eq.3.30) maps to Δ for decisions.

## Algorithms

- **Dempster's combination algorithm (graphical, p.39, Fig.2.3):** treat unit square as total mass; horizontal strips of width `m1(B_i)` for focal elements of `Bel1`, vertical strips of width `m2(C_j)` for `Bel2`; intersection rectangle gets product mass committed to `B_i ∩ C_j`; sum rectangles assigned to the same subset; renormalise by `1 − Σ_{B∩C=∅} m1(B) m2(C)`.
- **Algorithm for combining n support functions with a Bayesian BF (p.55, Proposition 15 corollary):** compute `pl_i(θ) = c_i · Pl_{s_i}(θ)` for each support function; multiplicatively combine `pl(θ) = Π pl_i(θ)` to get singleton plausibilities; renormalise.
- **Iterative IBS combination (p.102):** quadratic programming defined by Eq.(3.36); algorithm in [445, §4.1.2] (Denoeux). Not detailed here.

## Parameters / quantities

| Name | Symbol | Domain | Page | Notes |
|------|--------|--------|------|-------|
| Frame of discernment | Θ | finite set, exhaustive answers | 34 | core ontological object |
| Power set | 2^Θ | events, Boolean σ-field | 35 | domain of m, Bel, Pl, Q |
| Mass / BPA | m(A) | [0,1] | 34 | Σ m(A) = 1, m(∅)=0 |
| Focal element | A | A ⊂ Θ, m(A)>0 | 34 | |
| Core | C_m | C_m ⊆ Θ | 35 | union of focal elements |
| Belief | Bel(A) | [0,1] | 35 | lower probability |
| Doubt | Dis(A) | [0,1] | 36 | =Bel(Ā) |
| Plausibility | Pl(A) | [0,1] | 36 | =1−Bel(Ā) |
| Commonality | Q(A) | [0,1] | 36 | mass moving freely through A |
| Simple-support weight | σ | [0,1] | 41 | strength of evidence for focus A |
| Weight of conflict | K | [0,∞] | 40 | log normaliser, additive across combinations |
| Weight of internal conflict | W | [0,∞] | 44 | infimum K over decompositions |
| Canonical weight | w(A) | [0,∞) (separable: [0,1]) | 44 | from commonality via inverse formula |
| Refining | ρ | 2^Θ → 2^Ω | 45 | partition map |
| Inner reduction | ρ̄ | 2^Ω → 2^Θ | 46 | dual; pulls Bel back |
| Outer reduction | ρ̃ | 2^Ω → 2^Θ | 46 | pulls Pl back |
| Minimal refinement | Θ1 ⊗ … ⊗ Θn | unique frame | 47 | smallest common refinement |
| Vacuous BF | Bel_v | m(Θ)=1 | 35 | absence of evidence |
| Bayesian BF | Bel_p | finite probability | 37 | Bel(A)+Bel(Ā)=1 |
| Contour function | pl_s(θ) | [0,∞) | 54 | relative singleton plausibility |
| Credal set | P[Bel] | polytope ⊂ Δ_Θ | 66 | Eq.(3.10) |
| Hyperpower set | D^Θ | Dedekind lattice | 93 | DSmT domain |
| Pignistic | BetP(A) | [0,1] probability | 90 | Eq.(3.30), TBM |
| Implicability | b(A) | [0,1] | 92 | open-world: Bel(A)+m(∅) |
| Beta-density params | α,β,r,s,a | reals | 105 | Josang subjective logic |

## Worked examples

**Example 1: Ming vase.** *(p.35)* Binary FoD `Θ = {θ1=genuine, θ2=fake}`. BPA assigns `m({θ1}), m({θ2}), m(Θ)`. Constraint `Bel({θ1})+Bel({θ2})+m(Θ) = 1`, with `m(Θ)` representing residual ignorance — *not* split equally as in Bayes. Sets up the geometric reading of `B_2` as a triangle with the diagonal `m(Θ) = 0` corresponding to Bayesian BFs.

**Example 2: ternary BF.** *(p.36)* `Θ = {x,y,z}`, `m({x}) = 1/3`, `m(Θ) = 2/3`. Computes `Bel({x,y}) = 1/3`, `Pl({x,y}) = 1`, `Q({x,y}) = 2/3`; demonstrates Bel ≤ Pl, commonality interpretation as freely moving mass.

**Example 3: Dempster combination on |Θ|=4.** *(pp.38-40)* `Θ = {θ1,…,θ4}`. `Bel1`: `m1({θ1})=0.7`, `m1({θ1,θ2})=0.3`. `Bel2`: `m2({θ2,θ3,θ4})=0.6`, `m2(Θ)=0.4`. Combined BPA after normalisation (conflict mass 0.42): `m({θ1})=0.7·0.4/0.58 = 0.48`, `m({θ2})=0.3·0.6/0.58 = 0.31`, `m({θ1,θ2})=0.3·0.4/0.58 = 0.21`. (Cuzzolin's stated denominator on p.40 is `1-0.42=0.58`, and the printed "0.42" denominator is a typo or printing artefact in the page — the values 0.48, 0.31, 0.21 sum to 1.00 only with denominator 0.58.) Illustrates the renormalisation step graphically (Fig.2.3 strips/rectangles).

**Example 4: alibi.** *(p.42)* `Θ = {G,I}`. Friend gives SSF on {I} with `m_I({I}) = 1/10`. Hard evidence: SSF on {G} with `m_G({G}) = 9/10`. Combined: `Bel({I}) = 1/91`, `Bel({G}) = 81/91` — mild erosion of strong evidence by weak counter-evidence; canonical heterogeneous-evidence example.

**Example 5: number systems.** *(p.47, Fig.2.5)* Real `r ∈ [0,1]` represented in binary, base-5, base-10. Each digit choice = a coarsening of [0,1]; minimal common refinement is two-digit base-10. Concretises Definition 14 (compatible frames) and Theorem 1.

**Example 6: Sirius's planets.** *(p.55-56)* Binary `Θ = {θ1=life, θ2=no life}`; ternary refinement `Ω = {ζ1=life, ζ2=planets without life, ζ3=no planets}`. Vacuous BF on Θ extends vacuously to Ω. Uniform Bayesian prior on Θ assigns 1/2,1/2; uniform on Ω assigns 1/3,1/3,1/3 → vacuous extension yields `p({ζ1})=1/3, p({ζ1,ζ2})=2/3` which contradicts the per-frame uniform on Ω. Demonstrates that *uniform priors do not survive frame refinement* — the canonical Bayesian-fragility critique.

**Example 7: Kyburg's credal-set-not-a-BF.** *(p.68)* Compound experiment: with probability p toss a fair coin twice; with probability 1−p draw biased coin from bag (40% two-headed, 60% two-tailed) and toss twice; p ∈ (0,1) unknown. Lower probability `P_(A∪B) = 0.75 < 0.9 = P_(A) + P_(B) − P_(A∩B)` violates BF 2-monotonicity Eq.(3.14). Hence belief functions are a *strict* subclass of credal sets.

**Murder trial / Dempster compatibility example** *(p.34, Fig.2.2)* — multivalued maps `Γ1: Ω1={Drunk, Not drunk} → Θ` and `Γ2: Ω2 = {Cleaned, Not cleaned} → Θ` (`Θ = {Peter, John, Mary}`) acting on independent evidence sources to produce a combined BF. Anchors the rest of Chapter 2's translation between Dempster's setting and Shafer's set-function setting.

## Figures of interest

- **Fig. 2.2 (p.34)** — Murder-trial multivalued mappings; two source spaces with probability mass mapped via Γ1, Γ2 to subsets of suspects.
- **Fig. 2.3 (p.39)** — Graphical Dempster combination for the four-element example: source masses as horizontal/vertical strips, intersections as rectangles labelled with Bel1⊕Bel2 focal elements `{θ1}, {θ2}, {θ1,θ2}`.
- **Fig. 2.4 (p.46)** — Refining ρ between FoDs Θ and Ω; visualises the partition image `ρ({θ}) ⊂ Ω`.
- **Fig. 2.5 (p.48)** — Number-system family of compatible frames: binary digits, base-5 digits, common refinement (base-10).
- **Fig. 2.6 (p.50)** — Independence of frames: pairwise non-empty intersections of refinings to common refinement.
- **Fig. 2.7 (p.56)** — Consonant BF: nested ellipses `A1 ⊂ A2 ⊂ A3 ⊂ Θ`.
- **Fig. 3.1 (p.59)** — Venn diagram positioning BFs among set functions, normalised mass functions, monotonic capacities, equally-monotone capacities. (Implicit chapter overview.)
- **Fig. 3.2 (p.63)** — Compatibility relation / multivalued mapping ω → Γ(ω); P on Ω induces Bel on Θ.
- **Fig. 3.3 (p.67)** — Probability simplex on `Θ = {x,y,z}`; Bel's credal set `P[Bel]` as a sub-polytope with face boundaries parallel to level sets `p(x)=const`, `p(y)=const`, `p(z)=const`.
- **Fig. 3.4 (p.72)** — Two ternary credal sets: (a) general credal-set polytope; (b) parameterised family `Fam` (Gaussian curve) — neither is a BF in general.
- **Fig. 3.5 (p.73)** — Second-order distributions (Dirichlet vs uniform on credal-set polytope) — BFs are *not* second-order distributions over Θ (sets of PDFs over the parameter space).
- **Fig. 3.6 (p.82)** — Functional model `x = f(θ,ω)` represented as a hint H_f.
- **Fig. 3.7 (p.87)** — Conditional / probabilistic multivalued mapping (Yen): each ω maps to a partition `{A_{i_j}}` of Θ with conditional probabilities.
- **Fig. 3.8 (p.91)** — Smets's TBM credal vs pignistic levels, with pignistic transform.
- **Fig. 3.9 (p.94)** — Hyperpower set D^Θ for `Θ = {θ1,θ2,θ3}` — 19 elements arranged as Dedekind lattice.
- **Fig. 3.10 (p.96)** — Gaussian/linear BF: parallel hyperplanes (focal elements) carrying a multivariate Gaussian density.
- **Fig. 3.11 (p.101)** — Imprecise belief structure m as a rectangular subset in the binary belief space `B_2`; `P_2` (probability simplex) is a side; `B_2` is the triangle.
- **Table 3.1 (p.100)** — Qualitative addition (left) and multiplication (right) operators on `{+, 0}`.

## Criticisms of prior work

- **Bayesian uniform priors are frame-dependent.** *(p.36, p.55-56, Example 6)* — the equal-mass-to-each-singleton convention gives incompatible priors under refinement; vacuous BF stays vacuous.
- **Belief functions are *not* arbitrary credal sets.** *(p.71-72, Example 7)* — Kyburg's compound coin yields a credal set whose lower envelope violates 2-monotonicity. A BF's credal-set boundaries must be parallel to level sets `P(A)=const`.
- **Belief functions are *not* parameterised families.** *(p.72, Fig.3.4(b))* — counter-example with Gaussian PDFs shows not every parameterised family corresponds to a BF.
- **Belief functions are *not* confidence intervals.** *(p.72)* — confidence intervals are a form of interval estimate (associated with a single scalar parameter), no probability attached; only in binary cases under specific hypotheses can a 1-1 correspondence be enforced.
- **Belief functions are *not* second-order distributions.** *(p.73)* — Bayesian inference yields probabilities over parameter space; BFs operate on the hypothesis space directly. Two distinct objects.
- **Pearl** *(p.76-77, [1399, 1406, 1408, 1407])* — three lines of attack: (i) BFs cannot represent if-then rules / conditional knowledge without counter-intuitive conclusions; (ii) updating violates "basic patterns of plausibility", undermining rationality; (iii) Dempster combination is opaque vs likelihood-based methods. Cuzzolin notes [1409] follow-up was largely shaky [1443].
- **Lindley [1174]** *(p.75)* — defends Bayes/de Finetti as the unique correct uncertainty calculus.
- **Wasserman [1916]** *(p.76)* — questions BF separation from frequentist probability, pointing to de Finetti exchangeability bridging subjective / frequentist.
- **Hummel-Landy [858] critique of Shafer's canonical examples** *(p.74-75)* — coded-message construction disregards the statistical foundation; "the connections between the logical structure of the example and the story of the uncertain codes is not at all clear" (Barnard); "calling into question the relevance of the canonical scales" (Fine).
- **Snow [1740]** *(p.90)* — Dutch-book argument against TBM.
- **Smets's TBM as response** *(p.78, [1683, 1686, 1693, 1703, 1713])* — axiomatic foundation severs BFs from probability; addresses Pearl by separating credal and pignistic levels.
- **Dubois-Prade [1399, 1408]** *(p.77)* — distinguish *updating* (Dempster's rule) from *focusing* (upper/lower conditional); argue focusing is the more natural reading of uncertain statements.

## Design rationale

- **Why m on subsets, not just on singletons** *(p.35, p.74)* — captures evidence that genuinely supports `{x,y}` without distinguishing x from y; Bayesian additivity forces a split that may not be present in the evidence.
- **Why Moebius inversion** *(p.36)* — gives 1-1 correspondence between BPA and BF, so either representation is sufficient and one can switch freely.
- **Why three set functions Bel/Pl/Q** *(p.36)* — encode the same information from three angles (lower, upper, "freely moving"); useful for different operations and equivalent characterisations (e.g. consonance via Pl-max / Bel-min, Proposition 16).
- **Why normalise Dempster combination** *(p.38-40)* — `Σ m1(B)m2(C)` over disjoint `B∩C=∅` represents joint conflict, must be discarded under closed-world independent-evidence assumption.
- **Open-world / unnormalised BFs (UBFs)** *(p.92-93)* — keeping `m(∅) > 0` in the TBM allows *frame-of-discernment incompleteness* to be represented; the implicability function `b(A) = Bel(A) + m(∅)` (3.31) is no longer a capacity but is an honest accounting.
- **Why simple/separable support functions matter** *(p.41-43)* — they form the building blocks: every body of evidence can be decomposed canonically; combination reduces to multiplication of weights `w_A`.
- **Why families of compatible frames** *(p.45-49)* — evidence may be expressed at different granularities; one needs an algebra that links them. Definition 14's six axioms ensure refinings compose, refine, coarsen, and admit common refinements; this is the formal scaffold for Shafer's "evidential language".
- **Why support and quasi-support distinction** *(p.51-55)* — separable SFs are the *finite-evidence* objects; quasi-support functions (limits) include Bayesian BFs as the *infinite-evidence* limiting case; this lets statistical inference live inside BF theory while still distinguishing actual finite evidence from "infinite chance".
- **Why consonant BFs** *(p.56-57)* — diametrically opposite class to quasi-support: focal elements all point "in the same direction"; correspond to possibility distributions (Pl is a possibility, Bel a necessity).
- **TBM credal vs pignistic separation** *(p.90-91)* — beliefs are maintained as BFs (credal level); decisions force conversion to a probability via BetP. Justifies entertaining beliefs without committing them to behaviour — addressed Wasserman's worry about the betting interpretation of belief.
- **DSmT rejecting excluded middle** *(p.93-95)* — for poorly defined hypotheses (sensor fusion), the frame elements may overlap; hyperpower set is the closure under both `∪` and `∩`. Cholvy [282] showed this is reformulable in standard DS theory; "interest of DSmT lies in compactness rather than expressive power".
- **Generalised BPAs (Augustin)** *(p.102-103)* — sets of BPAs subsume credal sets and IBSs; constructive approach to imprecise probability.
- **Lattice / Boolean-algebra extensions** *(p.97-98)* — accommodate frames with too many elements (e.g. partitions, preorders), non-classical logics, multi-agent coalitions; complexity argument for working on a lattice rather than `2^Θ`.
- **Why pseudo-belief functions** *(p.44, p.93)* — the canonical-decomposition weights `w(A)` may be > 1, generating negative masses; rather than disallow, treat as legitimate algebraic object that supports inversion of Dempster's rule. Crucial for the geometric programme later in the book.

## Open / research questions

The chapter is largely retrospective; explicit "open questions" are not foregrounded, but several gaps are signalled.

- *(p.51)* Zhang's [2108] weight-of-conflict conjecture — whether weight of evidence and weight of internal conflict extend canonically to *all* support functions; Cuzzolin notes Zhang showed extension is feasible *whether or not* the conjecture is true. The conjecture itself is left open.
- *(p.79)* Total belief problem — generalising the law of total probability to BFs, only formally stated by Hsia [846] but not constructively solved; deferred to Chapter 17.
- *(p.103)* Generalised BPA correspondence with credal sets is many-to-one — *which* set of BPAs is the canonical representation of a given credal set? Open.
- *(p.92)* `BetP` "is *not* the only probability mapping that commutes with convex combination" (Chapter 11) — alternative probability transforms remain to be classified.
- *(p.62, p.69)* Whether random-set theory should be the foundation, vs Smets's TBM, vs Dempster's lower/upper probabilities, vs inner measures, is left explicitly contested ("none of these models is the best, for each has its own domain of application", Smets [1683, 1696]).
- *(p.76)* Klopotek-Wierzcho [1006]'s claim that prior probabilistic interpretations of BFs [1086, 785, 582] failed → call for a fully compatible interpretation, with their three proposed models (marginally correct, qualitative, quantitative) as candidates.

## Notable references cited

- `[526]` Dempster — original combination rule (p.38).
- `[1583]` Shafer 1976 — foundational essay; cited as the canonical source for nearly every Chapter 2 result (pp.34-57 passim).
- `[1584]` Shafer 1976 (other) — rationale for evidential probability (p.74).
- `[66]` — BPA terminology (p.34).
- `[1081, 1079]` — basic probability number history (p.34).
- `[527, 442]` — Definition 4 cross-references (p.34).
- `[347]` — historical use of "lower probability" / "plausibility" (p.36).
- `[720, 1762]` — Moebius inversion and monotone-functions theory (p.36).
- `[1583], Theorem 2.1` — superadditivity of BFs (p.68 Eq.3.14).
- `[1064]` — Kramosil canonical-decomposition variant (p.45).
- `[1698]` — Smets's algebraic decomposition for non-dogmatic BFs (p.44).
- `[451]` — categorical BFs (p.44).
- `[369, 329, 351]` — algebra of compatible frames (p.47).
- `[1650]` — Boolean subalgebra / independence formalism (p.49).
- `[1015]` — support functions terminology (p.51).
- `[2108]` — Zhang on weight-of-conflict extension (p.51).
- `[1583]` Shafer — quasi-support construction (p.53).
- `[414, 1583, 1607, 1597]` — Dempster's and Shafer's foundational papers cited in Chapter 3.
- `[1086]` Kyburg — credal sets vs BFs, Proposition 20, Example 7 (pp.66-68).
- `[1141, 2094, 344, 48]` — credal-set terminology (p.66).
- `[1572]` — robust statistics framing of BFs (p.66).
- `[1879]` — permutation extremes (Eq.3.12) (p.67).
- `[1293]` — Miranda et al. characterisation of k-additive credal sets (p.67).
- `[717, 716, 1268]` — random-set theory introductions (p.68).
- `[950, 1268, 1304]` — Kendall, Matheron, Molchanov on stochastic geometry (p.69).
- `[1344]` Nguyen — random sets / lower-probability identification (p.69).
- `[826]` Hestir — random sets (p.69).
- `[1687]` — relations between TBM and random sets (p.69).
- `[403]` de Finetti — betting (p.70).
- `[916, 917, 918]` Josang — subjective evidential reasoning (p.105).
- `[1683, 1686, 1693, 1703, 1713, 1730, 1697, 1707, 1732]` Smets — TBM (pp.78-92).
- `[490, 491, 1665, 1155]` — DSmT papers (p.93).
- `[1189, 421, 1599, 1191, 1192, 1194, 1195]` — Gaussian / linear BFs (Liu, Dempster) (pp.95-97).
- `[721, 95]` Grabisch — BFs on lattices (p.97).
- `[2114, 2115]` Zhou — distributive lattices, NP-completeness of BF satisfiability (p.98).
- `[737, 756]` Guan-Bell, Guth — BFs on Boolean algebras (p.98).
- `[445, 446]` Denoeux — imprecise belief structures (p.101).
- `[68]` Augustin — generalised BPAs (p.102).
- `[1921, 1922]` Weichselberger — F-probability (p.103).
- `[2089]` Zadeh — "simple view" relational-database interpretation (p.103).
- `[668, 1218]` Lowrance-Strat / Garvey — Grasper II, dynamic compatibility relations (pp.104-105).
- `[372]` D'Ambrosio — ATMS / hybrid (p.106).
- `[846]` Hsia — minimum-commitment (p.106).
- `[81, 80]` Baldwin — mass assignments (p.106-107).
- `[1796]` Tanaka — exponential possibility distributions (p.107).
- `[1233]` Mahler — conditioned/modified DS (p.107).
- `[623]` Fixsen-Mahler — MDS / pignistic relation (p.108).
- `[305]` Cooke-Smets — self-conditional probabilities (p.108).
- `[739]` Guan-Bell — pl-functions, plausible reasoning (p.108).
- `[1399, 1406, 1407, 1408, 1409]` Pearl — Pearl-vs-belief debate (pp.76-77).
- `[1916]` Wasserman (p.76).
- `[1958, 1954]` Wong et al. — preference-based BFs (p.99).
- `[1956]` — interval structures (p.100).
- `[711]` Gordon-Shortliffe — early BF expert system (p.74).
- `[1773]` Strat-Lowrance — explanation generation (p.74).
- `[323]` Curley-Golden — legal-evidence experiment (p.74).
- `[1340]` Neapolitan — significance-testing analogy (p.79).

## Implementation notes for propstore

- **`propstore.world` (ATMS) and BPA layer.** Definition 4 (BPA), Definition 5 (Bel), Eq.(2.1)-(2.5) give the core data shape: a content-hashed BPA as a sparse map from focal-element-set to mass with `m(∅)=0` and `Σm = 1`. ATMS bundle nodes can carry both `m`, `Bel`, `Pl`, `Q` views; Moebius inversion (Eq.2.3) is the canonical pivot between BPA-storage and Bel-query views. Open-world `m(∅) > 0` (UBF, Eq.3.31) corresponds directly to Smets-style ATMS-with-failure mode where the empty environment carries non-zero mass.
- **`propstore.aspic_bridge`.** Simple support functions (Definition 9) and separable support functions (Definition 10) are the natural ASPIC+ ordinary-premise → defeasible-rule encodings: a single rule `→ A` with weight σ is an SSF on focus `A`. Multiplication-of-weights (p.45 / Proposition 15) is the analogue of independent-evidence combination on rule strengths. Canonical decomposition Eq.(2.10) gives an inverse: any defeasible-rule premise set can be canonically lifted into a unique multi-set of weighted simple SSFs.
- **`propstore.belief_set` (AGM/IC merge).** Definitions 12-16 (refinings, families, independence, common refinement) directly underwrite IC-merge over compatible signatures: when two belief sets are stated on different vocabularies, the minimal common refinement Θ1 ⊗ Θ2 (Theorem 1) is the canonical merge frame. Definition 16's independence condition is the analogue of "independent agents" in Konieczny-Pino-Pérez merging.
- **`propstore.defeasibility` / CKR contexts.** `ist(c, p)` corresponds tightly to context conditioning of vague characteristics (Definition 33, Eq.3.27): each context c maps to a `γ(c) ⊂ Θ` and conditioning of γ1 by γ2 keeps only contexts where γ1 is "covered" by γ2. This is the formal kernel of CKR's lifting rules.
- **`propstore.support_revision`.** The canonical decomposition (Proposition 6, Eq.2.10) is the support-incision adapter: given a current BPA, compute weights `w(A)`, identify which `m_A^{w(A)}` simple BFs to incise, recombine. Pseudo-belief functions (negative masses) are admissible scoped artefacts.
- **`propstore.world.assignment_selection_merge`.** Augustin's generalised BPA (Definition 41) and proposition 23 (`L(A) = min_{m∈S} Σ m(B)`) are the formal model: the ATMS sidecar holds a *set* of admissible BPAs (one per typed assignment) and the lower envelope L is the merge.
- **Dimensions / `propstore.dimensions`.** Gaussian / linear BFs (Eq.3.32, p.96) extend BFs to continuous parameter spaces through hyperplane focal elements with mean μ and covariance Σ — directly applicable to z3.Real-valued QUANTITY dimensions; provides the formal basis for "imprecise quantity" claims with both interval and Gaussian dependence.
- **CEL / TIMEPOINT condition reasoning.** Allen relations on description-claim intervals are isomorphic to BFs over a temporal frame `Θ_t = {before, after, during, …}`; the consonant case (Definition 26, Proposition 16) corresponds to nested temporal interval evidence and supports `Pl(A∪B) = max(Pl(A), Pl(B))` — exactly the temporal-precedence semantics needed.
- **Subjective-logic provenance.** Josang's framework (p.105) — beta-density `f(α,β)`, three-tuple `(b, d, u) = (r/(r+s+2), s/(r+s+2), 2/(r+s+2))` with base rate `a` — gives the calibrated-vs-vacuous discipline at the provenance layer: stated/calibrated BFs carry α,β,a explicitly, vacuous BFs collapse to `(0,0,1)`.
- **TBM credal/pignistic split** (Smets, p.90-91, Eq.3.30) is propstore's *render-time* policy: storage holds BPAs (credal level); render-policy may invoke `BetP` to flatten to a probability distribution for decision queries. The pignistic transform's caveats (p.92, Chapter 11 deferral) suggest pluggable transforms (BetP, plausibility transform, …) at render time, not a hard-coded canonical mapping.
- **Sets of BPAs / IBSs** (Denoeux, p.101, Eq.3.35-3.36; Augustin, p.102) ground propstore's non-commitment discipline: rather than collapse rival BPAs, store the closed set and resolve at render time via `m^-, m^+` envelopes.
- **Hyperpower set / DSmT** (Definition 38, p.93) — when concept boundaries are disputed (overlapping ontology references), the lattice closure under both `∪` and `∩` is the natural domain. Cholvy's reduction theorem (p.93) means we don't need a bespoke DSmT layer — a standard BF on a refinement suffices.
- **Lowrance-Grasper galleries / compatibility-relation regression** (p.105) — closely related to the geometric programme later in the book and to "families of compatible frames" as a graph-of-frames data structure; suggests a `propstore.frames` module representing the gallery / DAG of frames with refinings as edges.

## Quotes worth preserving

- "A new body of evidence is not constrained to be in the form of a single proposition `A` known with certainty, as happens in Bayesian reasoning. Yet, the incorporation of new certainties is permitted in the theory of evidence, as a special case." *(p.41)*
- "The vacuous belief function (our representation of ignorance) is left unchanged when moving from one hypothesis set to another, unlike what happens with Fisher's uninformative priors in Bayesian reasoning." *(p.51)*
- "Belief functions are not arbitrary credal sets… belief functions are a very special class of credal sets, those induced by a random set mapping." *(p.71)*
- "Most of the debate has taken place at the semantic level, for different interpretations imply the use of entirely different operators to construct a theory of reasoning with belief functions." *(p.60)*
- "Beliefs are necessary ingredients for our decisions, [but] that does not mean that beliefs cannot be entertained without being manifested in terms of actual behaviour." (Smets, paraphrased p.92)
- "The disagreement over the 'correct' meaning of belief functions boils down, fundamentally, to a lack of consensus on how to interpret probability, as belief functions are built on probability." (Shafer [1601], paraphrased p.79)
- "Consonant belief functions represent collections of pieces of evidence all pointing in the same direction." *(p.57)*
- "Belief functions and quasi-support functions can be considered as representing diametrically opposite subclasses of belief functions." *(p.57)*
- "[The interest of DSmT] lies in its compactness rather than its expressive power." *(p.93)*

## Done condition

All 78 page images in range 056-128 (book pp.31-108 with 109 falling on a chapter-4 transition page) read directly. Output file populated with: 19+ formal definitions (Defs 4-42 with gaps), 23 propositions/theorems including all of Propositions 1-23 plus Theorems 1, 2, the Bayes' theorem variant, and Proposition 18 (Definitions 5/27 equivalence), 35+ numbered equations covering Eqs (2.1)-(2.18) of Chapter 2 and (3.1)-(3.37) of Chapter 3, 7 worked examples (Ming vase, ternary BF, four-element Dempster combination, alibi, number systems, Sirius's planets, Kyburg's compound coin), 11 figures described, table 3.1 captured, and detailed criticism, design rationale, propstore-mapping sections.

Word count: see file. No pages failed. No further sub-agents spawned. Only the assigned output file modified.
