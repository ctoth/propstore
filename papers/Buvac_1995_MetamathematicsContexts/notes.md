---
title: "Metamathematics of Contexts"
authors: "Saša Buvač, Vanja Buvač, Ian A. Mason"
year: 1995
venue: "Fundamenta Informaticae 23(2/3/4):263-301"
doi_url: "https://doi.org/10.3233/FI-1995-232345"
pages: "263-301"
note: "Read from the authors' accepted manuscript (PostScript from www-formal.stanford.edu/buvac/, 39 pages; footer: 'To appear in Fundamenta Informaticae, 23(3), 1995 ... Latexed on November 7, 1994'). The manuscript has no printed page numbers. Page citations are manuscript pages: ms p.N = page-image index N-1. They are not journal page numbers; the journal article spans 263-301 (39 pages), but the mapping ms p.N -> journal p.(262+N) is not verified."
---

# Metamathematics of Contexts

## One-Sentence Summary
Journal treatment of the propositional logic of context: syntax, partial-assignment semantics over context sequences, a Hilbert system (PL, K, Δ, MP, CS) with soundness and completeness, correspondence results for consistency (D), truth (Tr), flatness (4⁻¹, 5⁻¹) and meaninglessness-as-falsity (MF), a finite-model-property decidability proof, and a translation-based comparison to multi-modal Kripke semantics. *(ms p.1-36)*

## Problem Addressed
No formal logical explication of contexts existed despite their use in Cyc, KIF, and computational linguistics; the paper gives one and establishes its metatheory. *(ms p.1-2)*

## Key Contributions
- Sound and complete Hilbert system with a single (Δ) axiom; (ND) and (Δ−) shown equivalent to it. *(ms p.8-17)*
- Correspondence theory for consistent, truth, and flat contexts and for Guha-style meaningless-as-false semantics. *(ms p.18-23)*
- Decidability via finite model property. *(ms p.24-26)*
- Representation theorems relating context models and Kripke models (C₁ = Δ-models). *(ms p.26-34)*

## Section structure *(ms p.2)*
§1 introduction and notation; §2 syntax, semantics, proof theory of the general system, soundness and completeness; §3 correspondence results; §4 completeness of the propositional fragment of Guha's logic of context; §5 decidability; §6 comparison to Kripke semantics; §7 related work; §8 conclusions. Most results of §2-§4 first announced in [5] (Buvač & Mason 1993, AAAI-93); §5 first announced in [6]; most of §6 first announced in [4].

## Motivation *(ms p.2-3)*
- Problem of generality in AI: systems never permanently stuck with their concepts because they can transcend their context; "lifting axioms" restate facts from a narrow context in a broader one with qualifications. *(ms p.2)*
- Example 1 (McCarthy [18]): `on(x,y,s)` in a situation-calculus context; `above` defined in a general common-sense context; lift the definition of `above` into the situation-calculus context. Needs full quantificational logic. *(ms p.3)*
- Example 2: Stanford KB contains "kids drive BMW's", Berkeley KB contains its negation; a logic of context lets a reasoner use seemingly inconsistent KBs without deriving a contradiction. *(ms p.3)*

## Notation *(ms p.3)*
Same as Buvač & Mason 1993: `X →_p Y` partial functions; `P(X)` powerset; `X*` finite sequences, `ε` empty, `*` append, element = singleton; tree order `x̄₁ < x̄₀ ≤ ε` iff `(∃ȳ ∈ X* − {ε})(x̄₁ = x̄₀ * ȳ)`; subtree rooted at ȳ: (1) `ȳ ∈ Y ∧ (∀z̄ ∈ Y)(z̄ ≤ ȳ)`, (2) `(∀z̄ ∈ Y)(∀w̄ ∈ X*)(z̄ ≤ w̄ ≤ ȳ → w̄ ∈ Y)`.

## 2.1 Syntax *(ms p.4)*

$$
\mathbb{W} = \mathbb{P} \cup (\neg\mathbb{W}) \cup (\mathbb{W} \to \mathbb{W}) \cup \mathrm{ist}(\mathbb{K}, \mathbb{W})
$$
𝕂 contexts, ℙ atoms, both countably infinite and distinct. *(ms p.4)*

Abbreviations (new vs 1993: the empty-sequence case):

$$
\mathrm{ist}(\epsilon, \phi) := \phi
$$

$$
\mathrm{ist}(\bar\kappa, \phi) := \mathrm{ist}(\kappa_1, \mathrm{ist}(\kappa_2, \ldots, \mathrm{ist}(\kappa_n, \phi)))
$$

$$
\mathrm{ist}^{\pm}(\bar\kappa, \phi) := \pm\mathrm{ist}(\kappa_1, \pm\mathrm{ist}(\kappa_2, \cdots \pm\mathrm{ist}(\kappa_n, \phi)\cdots))
$$
Signs in ist± need not share parity. PROP = ist-free wffs. Instances ψ(φ₁,…,φₙ) by simultaneous substitution. *(ms p.4)*

**Design rationale (modal operator vs reified predicate)** *(ms p.4)*: chosen a modal logic rather than reifying sentences and treating ist as a predicate because (1) it gives a more natural semantics, and (2) the language cannot express self-referential statements, avoiding paradoxes. Self-reference matters for theories of truth but not for describing states of affairs in contexts. The reifying approach is Attardi & Simi [1] (§7).

## 2.2 Semantics *(ms p.4-6)*
Naïve model: a context = set of truth assignments (possible states of affairs); ist interpreted as validity (true in all assignments), matching Guha's proposal for Cyc; ist-as-truth (single assignment) is a restriction plus axioms. Refined in two stages *(ms p.4-5)*:
1. Non-flatness: sets of assignments attach to context *sequences* (1950s car racing example; agent beliefs). Flat systems by restriction (§3.2).
2. Partial assignments because vocabularies differ.

**Definition (𝔐)** *(ms p.5)*:

$$
\mathfrak{M} \in (\mathbb{K}^* \to_p \mathbf{P}(\mathbb{P} \to_p 2))
$$
conditions: (1) `(∀κ̄)(∀ν₁, ν₂ ∈ 𝔐(κ̄))(Dom(ν₁) = Dom(ν₂))`; (2) `Dom(𝔐)` is a subtree of 𝕂* rooted at some κ̄₀. `κ̄^𝔐 = 𝔐(κ̄)`, may be empty; `Dom(𝔐(κ̄))` names the shared domain; 𝕄 is the class of models.

**Condition 1 is not a real restriction** *(ms p.5-6)*: from any 𝔐 build 𝔐′ by restricting each assignment to the atoms all assignments of that context share:

$$
\mathrm{Dom}(\mathfrak{M}'(\bar\kappa)) := \bigcap_{\nu \in \mathfrak{M}(\bar\kappa)} \mathrm{Dom}(\nu)
$$

$$
\mathfrak{M}'(\bar\kappa) := \{\nu' \mid (\exists \nu \in \mathfrak{M}(\bar\kappa))(\nu' \sqsubseteq \nu) \wedge \mathrm{Dom}(\nu') = \mathrm{Dom}(\mathfrak{M}'(\bar\kappa))\}
$$
𝔐 and 𝔐′ satisfy the same formulas. *(ms p.5-6)*

**No outermost context** *(ms p.6)*: a fixed outermost context (Dom rooted at ε) would simplify notation and proofs, but the definition rests on the intuition that there is no outermost context, so automated reasoners can always transcend their current context.

### 2.2.1 Vocabularies *(ms p.6)*
`Vocab ⊆ 𝕂* × ℙ`; the vocabulary of κ̄ is `{ρ | ⟨κ̄, ρ⟩ ∈ Vocab}`.

$$
\mathit{Vocab}(\mathfrak{M}) := \{\langle\bar\kappa, \rho\rangle \mid \bar\kappa \in \mathrm{Dom}(\mathfrak{M}) \wedge \rho \in \mathrm{Dom}(\mathfrak{M}(\bar\kappa))\}
$$
𝔐 classical on Vocab iff `Vocab ⊆ Vocab(𝔐)`.

Vocab of φ in κ̄ (`𝕂* × 𝕎 → P(𝕂* × ℙ)`): `{⟨κ̄, φ⟩}` for φ ∈ ℙ; `Vocab(κ̄, φ₀)` for ¬φ₀; `Vocab(κ̄ * κ, φ₀)` for ist(κ, φ₀); `Vocab(κ̄, φ₀) ∪ Vocab(κ̄, φ₁)` for φ₀ → φ₁. For sets:

$$
\mathrm{Vocab}(\bar\kappa, T) = \bigcup_{\phi \in T} \mathrm{Vocab}(\bar\kappa, \phi)
$$
Static analysis only possible propositionally; differs from Guha's definedness (Guha: ist(κ, φ) false if φ not in κ's vocabulary). *(ms p.6)*

### 2.2.2 Satisfaction *(ms p.7)*
Bochvar three-valued logic (implication meaningless if either side meaningless); chosen because meaningfulness is syntactic, not Kleene-style semantic.

If `ν ∈ κ̄^𝔐` and `Vocab(κ̄, χ) ⊆ Vocab(𝔐)`:
- `𝔐, ν ⊨_κ̄ ρ` iff ν(ρ) = 1
- `𝔐, ν ⊨_κ̄ ¬φ` iff not `𝔐, ν ⊨_κ̄ φ`
- `𝔐, ν ⊨_κ̄ φ → ψ` iff `𝔐, ν ⊨_κ̄ φ` implies `𝔐, ν ⊨_κ̄ ψ`
- `𝔐, ν ⊨_κ̄ ist(κ₁, φ)` iff `∀ν₁ ∈ (κ̄ * κ₁)^𝔐, 𝔐, ν₁ ⊨_{κ̄*κ₁} φ`

**If the preconditions fail, neither `𝔐, ν ⊨_κ̄ χ` nor `𝔐, ν ⊨_κ̄ ¬χ`** (explicit in this version). In particular if κ̄ > κ̄₀ (above the root), not `𝔐, ν ⊨_κ̄ χ`. `𝔐 ⊨_κ̄ χ` iff `Vocab(κ̄, χ) ⊆ Vocab(𝔐)` and `∀ν ∈ κ̄^𝔐, 𝔐, ν ⊨_κ̄ χ`; `⊨_κ̄ χ` iff for all 𝔐 classical on Vocab, `𝔐 ⊨_κ̄ χ`. *(ms p.7)*

## 2.3 Formal System *(ms p.7-8)*
Fixed `Vocab ⊂ 𝕂* × ℙ`; `⊢_κ̄ φ`. **Definedness Convention**: writing `⊢_κ̄ φ` implicitly assumes `Vocab(κ̄, φ) ⊆ Vocab`; rules preserve it. *(ms p.7)*

**Table 1 (ms p.8) — differs from the 1993 version:**
- (PL) `⊢_κ̄ φ` provided φ is an instance of a tautology
- (K) `⊢_κ̄ ist(κ₁, φ → ψ) → ist(κ₁, φ) → ist(κ₁, ψ)`
- (Δ) `⊢_κ̄ ist(κ₁, ist(κ₂, φ) ∨ ψ) → ist(κ₁, ist(κ₂, φ)) ∨ ist(κ₁, ψ)` — the single Δ axiom (1993's Δ+)
- (MP) from `⊢_κ̄ φ`, `⊢_κ̄ φ → ψ` infer `⊢_κ̄ ψ`
- (CS) from `⊢_{κ̄*κ₁} φ` infer `⊢_κ̄ ist(κ₁, φ)` **provided κ̄ ≤ κ̄₀** (new proviso)

With one context, (CS) = necessitation, (K) = K; ignoring (Δ), the system is the normal modal system. (Δ) accommodates the validity reading; derivable in the ist-as-truth system with no inconsistent contexts (§3.3); ramifications in §6, §7. *(ms p.7)*

### 2.3.1 Provability *(ms p.8)*
As in 1993: proof sequences `[⊢_{κ̄₁} φ₁, …, ⊢_{κ̄ₙ} φₙ]`; `T ⊢_{κ̄₀} φ` iff `⊢_{κ̄₀} (φ₁ ∧ … ∧ φₙ) → φ` for some φᵢ ∈ T; then `Vocab(T) ⊆ Vocab`.

## 2.4 Consequences *(ms p.8-10)*
- (C) `ist(κ₁, φ) ∧ ist(κ₁, ψ) → ist(κ₁, φ ∧ ψ)`
- (Or) `ist(κ₁, φ) ∨ ist(κ₁, ψ) → ist(κ₁, φ ∨ ψ)`
- (M) `ist(κ₁, φ ∧ ψ) → ist(κ₁, φ) ∧ ist(κ₁, ψ)` (converse of C; from K, PL, MP)
- (ND) `¬ist(κ₁, ist(κ₂, φ)) → ist(κ₁, ¬ist(κ₂, φ))`
- (Δ−) `ist(κ₁, ¬ist(κ₂, φ) ∨ ψ) → ist(κ₁, ¬ist(κ₂, φ)) ∨ ist(κ₁, ψ)`
- (CSE) from `⊢_{κ̄*κ₁} φ ↔ ψ` infer `⊢_κ̄ ist(κ₁, φ) ↔ ist(κ₁, ψ)` (analogue of modal RE, as CS is of RN)
- (REP) from `⊢_κ̄ φᵢ ↔ φ′ᵢ` infer `⊢_κ̄ ψ(φ₁…φₙ) ↔ ψ(φ′₁…φ′ₙ)`, ψ(p₁…pₙ) ∈ PROP, pᵢ new distinct atoms.
Proofs of C, Or, REP as in normal modal logic [7]. *(ms p.8)*

**(ND) and (Δ−) are each equivalent to (Δ)** in this system *(ms p.8-10)*:
- (ND) from (Δ): PL gives `⊢_{κ̄*κ₁} ist(κ₂, φ) ∨ ¬ist(κ₂, φ)`; CS gives `⊢_κ̄ ist(κ₁, ist(κ₂, φ) ∨ ¬ist(κ₂, φ))`; (Δ)+MP give `ist(κ₁, ist(κ₂, φ)) ∨ ist(κ₁, ¬ist(κ₂, φ))`, i.e. (ND). *(ms p.9)*
- (Δ) from (ND): PL tautology `(ist(κ₁, ¬ist(κ₂, φ)) → ist(κ₁, ψ)) → (¬ist(κ₁, ist(κ₂, φ)) → ist(κ₁, ψ))` plus K-instance `ist(κ₁, ¬ist(κ₂, φ) → ψ) → (ist(κ₁, ¬ist(κ₂, φ)) → ist(κ₁, ψ))`, PL, MP give `ist(κ₁, ¬ist(κ₂, φ) → ψ) → (¬ist(κ₁, ist(κ₂, φ)) → ist(κ₁, ψ))`, which is (Δ). *(ms p.9)*
- (ND) from (Δ−) identical with Δ− in place of Δ; (Δ−) from (ND) symmetric, using the ND instance `¬ist(κ₁, ¬ist(κ₂, φ)) → ist(κ₁, ist(κ₂, φ))`. *(ms p.9-10)*
- (CSE) proof: CS on φ → ψ then K; both directions. *(ms p.10)*

**Generalized to context sequences** *(ms p.10-11)*:
- (K*) `⊢_κ̄ ist(c̄, φ → ψ) → ist(c̄, φ) → ist(c̄, ψ)`
- (Δ*) `⊢_κ̄ ist(c̄, ist(κ₁, φ) ∨ ψ) → ist(c̄, ist(κ₁, φ)) ∨ ist(c̄, ψ)`
- (Δ*−) `⊢_κ̄ ist(c̄, ¬ist(κ₁, φ) ∨ ψ) → ist(c̄, ¬ist(κ₁, φ)) ∨ ist(c̄, ψ)`
- (CS*) from `⊢_{κ̄*c̄} φ` infer `⊢_κ̄ ist(c̄, φ)`
Proofs by induction on |c̄| (base K / Δ; step CS then K, transitivity, MP); CS* by applying CS once per context. *(ms p.10-11)*

### 2.4.1 CNF *(ms p.11-12)*
**Definition (CNF)**: `E₁ ∧ … ∧ E_l`, `Eᵢ = αᵢ₁ ∨ … ∨ αᵢᵣᵢ`, each α a literal or `ist±(c̄, β)` with β a disjunction of literals; rᵢ, l may be 1. *(ms p.11)*

**Lemma (CNF)**: for φ, κ̄ with Vocab(κ̄, φ) ⊆ Vocab, there is φ* in CNF with `⊢_κ̄ φ ↔ φ*`. *(ms p.11)*

**Proof** *(ms p.11-12)*: induction on n = max ist nesting. n = 0: φ ↔ φ* tautology, same vocabulary, so an axiom. Step, case φ = ist(κ, ψ) with ψ = ψ* in CNF:

$$
\psi^* = \bigwedge_i \bigvee_j \alpha_{ij}
$$
αᵢⱼ literal, ist(c̄, β) or ¬ist(c̄, β). By (M), `ist(κ, ⋀ᵢ ⋁ⱼ αᵢⱼ)` ≡ `⋀ᵢ ist(κ, ⋁ⱼ αᵢⱼ)`; reorder to `⋀ᵢ ist(κ, ist±(c̄ᵢ₁, βᵢ₁) ∨ … ∨ ist±(c̄ᵢₗ, βᵢₗ) ∨ βᵢₗ₊₁)`. If l = 0 it is CNF; if l ≥ 1, (Δ), (Δ−), (Or) propagate ist through the disjunction to `⋀ᵢ ist±(κ * c̄ᵢ₁, βᵢ₁) ∨ … ∨ ist±(κ * c̄ᵢₗ, βᵢₗ) ∨ ist(κ, βᵢₗ₊₁)`. General case: φ = μ(θ₁…θₙ), θᵢ = ist±(c̄ᵢ, χᵢ), μ ∈ PROP; by the above and (REP), replace θᵢ by CNF θ*ᵢ; rewrite as χ(ξ₁…ξₘ), ξᵢ = ist±(c̄ᵢ, πᵢ); take PL CNF χ* of χ; then χ*(ξ₁…ξₘ) is φ*. □ *(ms p.12)*

## 2.5 Soundness *(ms p.12-13)*
**Theorem**: if `⊢_κ̄ φ` then `𝔐 ⊨_κ̄ φ` for every 𝔐 classical on Vocab; if `T ⊢_κ̄ φ` and 𝔐 classical on Vocab satisfies all of T in κ̄, then `𝔐 ⊨_κ̄ φ`. *(ms p.12)*
Proof cases: PROP (classical on φ gives classical connectives); K (unfold ist satisfaction); Δ (ν₁ does not occur in the inner disjunct, so the universal distributes: `∀ν₁ ((∀ν₂ ∈ (κ̄*κ₁*κ₂)^𝔐 …) or 𝔐,ν₁ ⊨ ψ)` gives `(∀ν₂ …) or (∀ν₁ … ψ)`); MP (classical in a fixed context); CS (definition of ist satisfaction). *(ms p.12-13)*

## 2.6 Completeness *(ms p.13-17)*
Satisfiability, consistency, maximal consistency as in 1993. *(ms p.13)*

**Lemma (Lindenbaum)** with proof *(ms p.14)*: enumerate φᵢ with Vocab(κ̄, φᵢ) ⊆ Vocab; T₁ := T; Tᵢ₊₁ := Tᵢ ∪ {φᵢ} or Tᵢ ∪ {¬φᵢ}, whichever is consistent (one must be, else Tᵢ ∪ {φᵢ ∨ ¬φᵢ} inconsistent, so Tᵢ inconsistent); ⋃Tᵢ is maximally consistent.

**Theorem (completeness)** *(ms p.14)*: if T is consistent in κ̄₀ with Vocab then T is satisfiable in κ̄₀ with Vocab. (Stated one-directionally here; the 1993 version stated "iff".) Single formula contrapositive: `𝔐₀ ⊨_{κ̄₀} ¬φ` implies `⊢_κ̄ ¬φ`. *(ms p.15)*

Canonical construction (same as 1993) *(ms p.14)*:

$$
T_{\bar\kappa+} := \{\phi \mid T_0 \vdash_{\bar\kappa_0} \mathrm{ist}(\bar c, \phi), \phi \in \mathrm{PROP}\}, \quad \bar\kappa = \bar\kappa_0 * \bar c
$$

$$
\mathrm{Dom}(\mathfrak{M}_0) := \{\bar\kappa \mid \bar\kappa \le \bar\kappa_0, \exists \bar\kappa' \in \mathrm{Dom}(\mathsf{Vocab}), \bar\kappa' \le \bar\kappa\}
$$

$$
\mathfrak{M}_0(\bar\kappa) := \{\nu \mid \mathrm{Dom}(\nu) = \mathsf{Vocab}(\bar\kappa), \forall\phi \in T_{\bar\kappa+}, \bar\nu(\phi) = 1\}
$$
Lemma (T_κ̄+): closed under tautological consequence; T_κ̄+ may be inconsistent. Empty vocabulary gives the singleton {empty assignment}. Lemma (truth): `φ ∈ T₀ iff 𝔐₀ ⊨_{κ̄₀} φ`. *(ms p.14)*

### 2.6.1 Proof of the Truth Lemma *(ms p.15-17)*
- Lemma (𝔐₀): for φ ∈ PROP with Vocab(κ̄₀ * c̄, φ) ⊆ Vocab: `T₀ ⊢_{κ̄₀} ist(c̄, φ)` iff ∀ν ∈ 𝔐₀(κ̄₀ * c̄), ν(φ) = 1. Instance: `T₀ ⊢ ist(c̄, φ ∧ ¬φ)` iff 𝔐₀(κ̄₀ * c̄) = ∅. *(ms p.15)*
- (TL) `(∀ψ ∈ 𝕎)` ψ in CNF implies (ψ ∈ T₀ iff 𝔐₀ ⊨_{κ̄₀} ψ); full lemma via CNF lemma, maximal consistency, soundness. Induction: atoms, ∨, ∧, ¬ routine; ist case ψ = ist±(c̄, χ), χ a disjunction of literals, c̄ = κ₁ * … * κₙ. *(ms p.15)*
- `(D_c̄) ist(c̄, ¬φ) → ¬ist(c̄, φ)`; all T_{(κ̄₀*c̄′)+} (c̄ ≤ c̄′) consistent iff D_c̄ ∈ T₀ for all defined φ; proof as for (D) w.r.t. consistent models in §3.3 [sic; consistency is §3.1 in this manuscript]. Equivalent to `¬ist(c̄, φ ∧ ¬φ) ∈ T₀`. *(ms p.15-16)*
- Lemma (D_c̄): if D_{(κ₁*…*κₙ₋₁)} ∈ T₀ then `ist±(c̄, φ) ∈ T₀ iff ±ist(c̄, φ) ∈ T₀`, sign positive iff even number of negations. *(ms p.16)*
- Case D ∈ T₀: positive case via 𝔐₀ lemma and satisfaction; negative case `¬ist(c̄, χ) ∈ T₀ iff 𝔐₀ ⊨ ¬ist(c̄, χ)` reduces to the positive case by maximal consistency, satisfaction and definedness. *(ms p.16)*
- Case D ∉ T₀: j = index of first inconsistent context; `ist(κ₁*…*κⱼ, φ∧¬φ) ∈ T₀`; by K*, MP, `ist(κ₁*…*κⱼ, ψ) ∈ T₀` for all defined ψ; T_{(κ̄₀*κ₁*…*κⱼ)+} inconsistent, 𝔐₀(κ̄₀*κ₁*…*κⱼ) = ∅, so `ist(κ₁*…*κⱼ, φ) ∈ T₀ iff 𝔐₀ ⊨ ist(κ₁*…*κⱼ, φ)`. With D_{(κ₁*…*κⱼ₋₁)} ∈ T₀ and the D_c̄ lemma: `ist±(c̄, χ) ∈ T₀ iff ±ist(κ₁*…*κⱼ, ±ist±(κⱼ₊₁*…*κₙ, χ)) ∈ T₀`; positive case via the property of κ₁*…*κⱼ and the 𝔐₀ lemma; negative case analogous. No inductive hypothesis needed in the ist step. □ *(ms p.16-17)*

### 2.6.2 Minor lemmas *(ms p.17-18)*
- D_c̄ lemma proof: write ist±(c̄, φ) as `ist(c̄₁, ¬ist(c̄₂, ¬ist(c̄₃, ⋯ ¬ist(c̄ⱼ, φ)⋯)))` with c̄ = c̄₁ * … * c̄ⱼ; using D_{c̄₁} ∈ T₀, K*, MP, "bubble" negations out: if ist±(c̄, φ) ∈ T₀ then ist(c̄₁*…*c̄ⱼ, φ) ∈ T₀ if j even, ¬ist(c̄₁*…*c̄ⱼ, φ) ∈ T₀ if j odd. Other direction from (ND). *(ms p.17-18)*
- T_κ̄+ lemma proof: compactness gives φ₀…φₙ ∈ T_κ̄+ implying φ; closed under conjunction by (C); ψ = ⋀φᵢ with ist(c̄, ψ) ∈ T₀; ψ → φ tautology and defined so an axiom in κ̄; CS* gives ⊢_{κ̄₀} ist(c̄, ψ → φ); with K, ist(c̄, φ) ∈ T₀. *(ms p.18)*
- 𝔐₀ lemma proof: ⇒ trivial by construction; ⇐ if not T₀ ⊢ ist(c̄, φ) then ¬ist(c̄, φ) ∈ T₀, so T_κ̄+ ∪ {¬φ} consistent, so some ν ∈ 𝔐₀(κ̄) has ν(φ) = 0. *(ms p.18)*

## 3 Correspondence Results (begins ms p.18)
Same syntax/semantics, definedness convention holds; model class and axioms change.

Section order in this manuscript: §3.1 Consistency, §3.2 Truth, §3.3 Flatness. (Internal cross-references on ms p.5 "flat … cf. §3.2" and ms p.15 "(D) … given in §3.3" do not match this order.)

### 3.1 Consistency *(ms p.18-19)*
𝔐 ∈ ℭonsistent iff for any κ̄ ∈ Dom(𝔐) with **κ̄ < κ̄₀**, 𝔐(κ̄) ≠ ∅ (κ̄₀ = root of Dom(𝔐)). The restriction κ̄ < κ̄₀ is needed because the language cannot express facts about the consistency of the root context κ̄₀. *(ms p.18-19)*
- (D) `⊢_κ̄ ist(κ, ¬φ) → ¬ist(κ, φ)` for any κ̄ ∈ Dom(𝔐), under definedness; sound for ℭonsistent; sound and complete for serial Kripke frames. Equivalent to `⊢_κ̄ ¬ist(κ, φ ∧ ¬φ)` (printed with the ¬ here; the AAAI-93 version printed it without). *(ms p.19)*
- **Theorem (completeness)**: general system + (D) complete w.r.t. ℭonsistent. Proof: show 𝔐₀ ∈ ℭonsistent. If 𝔐₀(κ̄ * κ) = ∅ then `𝔐₀ ⊨_{κ̄*κ} φ ∧ ¬φ` for any defined φ (one always exists, by the definition of Dom(𝔐₀)); by CS `𝔐₀ ⊨_κ̄ ist(κ, φ ∧ ¬φ)`; by (M) `ist(κ, φ) ∧ ist(κ, ¬φ)`, contradicting (D). □ *(ms p.19)*

### 3.2 Truth *(ms p.19-20)*
ist as truth ("is true"; McCarthy [18]); one assignment per context.
- 𝔐 ∈ 𝔗ruth iff for any κ̄ ∈ Dom(𝔐) with κ̄ < κ̄₀, |𝔐(κ̄)| ≤ 1. *(ms p.19)*
- (Tr) `⊢_κ̄ ist(κ, φ) ∨ ist(κ, ¬φ)`, κ̄ ∈ Dom(𝔐), under definedness; converse of (D). A weak form of truth, (ND), is equivalent to (Δ). *(ms p.19)*
- **Theorem (completeness)**: general system + (Tr) complete w.r.t. 𝔗ruth. Proof: if 𝔐₀(κ̄) has ν₁ ≠ ν₂, some atom ρ has ν₁(ρ) ≠ ν₂(ρ), so `𝔐₀ ⊨_{κ̄₀} ¬ist(κ, ρ) ∧ ¬ist(κ, ¬ρ)`, contradicting soundness of (Tr). □ *(ms p.20)*
- In a system with (D) and (Tr), (Δ) is derivable; stronger: `⊢_κ̄ ist(κ, φ ∨ ψ) ↔ (ist(κ, φ) ∨ ist(κ, ψ))`. *(ms p.20)*

### 3.3 Flatness *(ms p.20-22)*
Motivation: independent databases (Northwest airlines flight 921 seen from any travel agent's context). *(ms p.20)*
- 𝔐 ∈ 𝔉lat iff Dom(𝔐) = 𝕂* and for any κ̄₁, κ̄₂, κ: 𝔐(κ̄₁ * κ) = 𝔐(κ̄₂ * κ); viewed as `𝔐 ∈ 𝕂 ∪ {ε} ↦ P(ℙ →_p 2)` with the shared-domain side condition `(∀κ̄ ∈ 𝕂 ∪ {ε})(∀ν₁, ν₂ ∈ 𝔐(κ̄))(Dom(ν₁) = Dom(ν₂))`. *(ms p.20)*
- Flatness axioms (renamed from the 1993 Fl+, Fl−; Fl+ there was a biconditional, here only the left-to-right direction is the axiom):
  - (4⁻¹) `⊢_κ̄ ist(κ₂, ist(κ₁, φ)) → ist(κ₁, φ)`
  - (5⁻¹) `⊢_κ̄ ist(κ₂, ¬ist(κ₁, φ)) → ¬ist(κ₁, φ)`
  sound for 𝔉lat provided the vocabulary satisfies `Vocab(κ̄₁ * κ) = Vocab(κ̄₂ * κ)`. *(ms p.21)*
- Converse (4) corresponds to S4 axiom (when κ₁ = κ₂); converse (5) to S5. The text says "both the schema (4) and the schema (5) are theorems in our system", and the derivations given use (4⁻¹)/(5⁻¹): *(ms p.21)*
  - (5): from `ist(κ, φ) ∨ ¬ist(κ, φ)` get `ist(κ₁, ist(κ, φ)) ∨ ist(κ₁, ¬ist(κ, φ))` by CS, Δ, MP; then by (4⁻¹), REP, MP: `¬ist(κ, φ) → ist(κ₁, ¬ist(κ, φ))`.
  - (4): same disjunction; with (5⁻¹) instance `ist(κ₁, ¬ist(κ, φ)) → ¬ist(κ, φ)` and PL: `ist(κ₁, ist(κ, φ)) ∨ ¬ist(κ, φ)`.
- (D) derivable from (4⁻¹) and (5⁻¹): from tautology `¬(¬ist(κ, φ) ∧ ist(κ, φ))`, via (4⁻¹), (5⁻¹), (4), (5), REP get `¬(ist(κ₁, ¬ist(κ, φ)) ∧ ist(κ₁, ist(κ, φ)))`; by C, REP `¬ist(κ₁, ¬ist(κ, φ) ∧ ist(κ, φ))`; with `(¬ist(κ₁, ¬ist(κ, φ) ∧ ist(κ, φ))) → (¬ist(κ₁, ¬ψ ∧ ψ))` (provable given vocabulary conditions) get `¬ist(κ₁, ¬ψ ∧ ψ)`, i.e. (D). Semantically every flat model is consistent. Also (4⁻¹) is derivable from (5) and (D); (5⁻¹) from (4) and (D). *(ms p.21-22)*
- **Theorem (completeness)**: general system + (4⁻¹), (5⁻¹) complete w.r.t. 𝔉lat. Proof: if 𝔐₀(κ̄₀ * κ) ≠ 𝔐₀(κ̄₀ * κ₁ * κ), some φ with `𝔐₀ ⊨_{κ̄₀} ¬ist(κ, φ)` and `𝔐₀ ⊨_{κ̄₀*κ₁} ist(κ, φ)` (or the converse); the latter is `𝔐₀ ⊨_{κ̄₀} ist(κ₁, ist(κ, φ))`, by soundness of (4⁻¹) gives `ist(κ, φ)`, contradiction; other disjunct via (5⁻¹). □ *(ms p.22)*

## 4 Meaninglessness as Falsity *(ms p.23)*
Models the semantics described but not investigated in Guha [12]: if φ is not in κ's vocabulary, ist(κ, φ) is false, not meaningless.
- New Vocab clause: `Vocab(κ̄, φ) = ∅ if φ is ist(κ, φ₀)`.
- New satisfaction clause: `𝔐, ν ⊨_κ̄ ist(κ₁, φ)` iff `Vocab(φ, κ̄*κ₁) ⊆ Vocab(𝔐)` and `(∀ν₁ ∈ (κ̄*κ₁)^𝔐) 𝔐, ν₁ ⊨_{κ̄*κ₁} φ`.
- Proof system: general system + (MF) `⊢_κ̄ ¬ist(κ₁, φ)` if `Vocab(κ̄ * κ₁, φ) ⊄ Vocab`.
- Observations (new vs 1993): the definedness convention is much more liberal, so (PL) admits many more instances; it holds vacuously for (Δ), (Δ−) and (modulo its side condition) (MF); in (CS) it holds vacuously for the conclusion but not the hypothesis. Some schemas are no longer derivable in full generality, e.g. (Or) only as `⊢_κ̄ ist(κ₁, φ) ∨ ist(κ₁, ψ) → ist(κ₁, φ ∨ ψ)` if `Vocab(κ̄ * κ₁, φ ∨ ψ) ⊆ Vocab`; the side condition legitimizes the needed PL instances and CS applications. Completeness proof structurally similar to §2; new points only from the liberal Vocab. *(ms p.23)*

## 5 Decidability *(ms p.24-26)*
Via the finite model property: any satisfiable formula is satisfiable in a model with finitely many finite truth assignments. *(ms p.24)*

**Definition (restriction of 𝔐(κ̄))** *(ms p.24)*: the restriction of ν w.r.t. Vocab(κ̄₀, φ) agrees with ν on atoms in the scope of κ̄ and is false elsewhere:

$$
\nu_{\mathrm{Vocab}(\bar\kappa_0,\phi),\bar\kappa}(p) = \begin{cases} \nu(p) & \langle\bar\kappa, p\rangle \in \mathrm{Vocab}(\bar\kappa_0, \phi) \\ 0 & \langle\bar\kappa, p\rangle \notin \mathrm{Vocab}(\bar\kappa_0, \phi) \end{cases}
$$

$$
V_{\mathrm{Vocab}(\bar\kappa_0,\phi)} = \{\nu_{\mathrm{Vocab}(\bar\kappa_0,\phi),\bar\kappa} \mid \nu \in V\}
$$

**Definition (restriction of 𝔐)** *(ms p.24)*: maps each context sequence appearing in φ to its restricted assignment set:

$$
\mathfrak{M}_{\mathrm{Vocab}(\bar\kappa_0,\phi)} : S \to \{\mathfrak{M}(\bar\kappa)_{\mathrm{Vocab}(\bar\kappa_0,\phi)} \mid \bar\kappa \in \mathrm{Dom}(\mathrm{Vocab}(\bar\kappa_0,\phi))\}
$$

$$
S = \{\bar\kappa_1 \mid \bar\kappa_1 \le \bar\kappa_0 \wedge \exists \bar\kappa_2 \in \mathrm{Dom}(\mathrm{Vocab}(\bar\kappa_0,\phi)), \bar\kappa_2 \le \bar\kappa_1\}
$$
i.e. `κ̄ ↦ 𝔐(κ̄)_{Vocab(κ̄₀,φ)}`.

**Theorem (finite model property)** *(ms p.24)*: `𝔐 ⊨_{κ̄₀} φ iff 𝔐_{Vocab(κ̄₀,φ)} ⊨_{κ̄₀} φ`. Only (⇒) is needed for decidability. Proof of a stronger claim by induction on structure: if Vocab(κ̄, α) ⊆ Vocab(κ̄₀, φ) then (𝔐 ⊨_κ̄ α iff 𝔐_{Vocab(κ̄₀,φ)} ⊨_κ̄ α). Cases atomic, negation, implication (as negation), ist — each uses that the restricted model's vocabulary contains all atoms/contexts relevant to φ (hence α) and `Vocab(𝔐_{Vocab(κ̄₀,φ)}) ⊆ Vocab(𝔐)`, so satisfaction preconditions hold in both directions. □ *(ms p.24-26)*

**Corollary (decidability)** *(ms p.26)*: effective procedure for validity in a context. φ valid in κ̄₀ iff ¬φ not satisfiable in κ̄₀. Generate all models of form 𝔐_{Vocab(κ̄₀,¬φ)}: finitely many, each with finitely many assignments over finitely many atoms (Vocab is recursive). If none satisfies ¬φ then by the FMP no model does, so φ is valid. □

## 6 Comparison to Kripke Semantics *(ms p.26-35)*
Disregarding partiality, most context models match a class of Kripke models; the match has leeway depending on definitions. *(ms p.26)*

- **Non-partial model**: `𝔐 ∈ (𝕂* → P(ℙ → 2))`; side conditions unnecessary; `𝔐, ν ⊨_κ̄ ¬φ iff not 𝔐, ν ⊨_κ̄ φ`. "Context logic" in §6 = §2 general system restricted to non-partial models, model theory only. *(ms p.26-27)*
- Modal language with □₁, □₂, … one per context of 𝕂 = {κ_β}_{β<α}; bijective translation φ ↦ φ^□ replacing ist(κ_β, ψ) by □_β(ψ^□). Kripke model ⟨𝕊, w₀, π, R_β⟩_{β<α} (worlds, actual world, assignment map, binary relations, α ≤ ω); □_β φ true at w iff φ true at all w′ with w R_β w′. *(ms p.27)*
- **Definition (association relation)** A from 𝔐 to 𝔐^□ *(ms p.27)*:
  1. `A ⊆ 𝕂* × (ℙ → 2) × 𝕊`
  2. `(∀κ̄)(∀ν ∈ 𝔐(κ̄))(∃w) A(κ̄, ν, w)`
  3. `A(κ̄, ν, w)` implies `(∀w′)(∃β)(w R_β w′ implies (∃κ′)(∃ν′) A(κ̄ * κ′, ν′, w′))`
  4. `A(κ̄, ν, w)` implies `π(w) = ν`
  5. `A(ε, π(w₀), w₀)`
  The same assignment in different context sequences may produce different worlds. *(ms p.27-28)*
- **Definition (elementary equivalence)**: 𝔐 ≡ 𝔐^□ w.r.t. A iff `A(κ̄, ν, w)` implies (`𝔐, ν ⊨_κ̄ φ iff 𝔐^□, w ⊨ φ^□`) for all κ̄, ν ∈ 𝔐(κ̄), w, φ. *(ms p.28)*
- **Properties of relations** *(ms p.28)*:
  - Φ₁(Rᵢ, Rⱼ): `∀w₁w₂w′₂w₃ ((w₁Rᵢw₂ & w₂Rⱼw₃ & w₁Rᵢw′₂) ⇒ w′₂Rⱼw₃)` — corresponds to (Δ) in standard correspondence theory
  - Φ₂(R): `∀w ∃w′ wRw′` (seriality)
  - Φ₃(R): `∀w₁w₂w′₂ (w₁Rw₂ & w₁Rw′₂ ⇒ w₂ = w′₂)` (functionality)
  - Φ₄(Rᵢ, Rⱼ): `Φ₂(Rᵢ) & Φ₂(Rⱼ) & ∀w₁w₂w′₂ (w₁Rᵢw₂ ⇒ (w₂Rⱼw′₂ ⇔ w₁Rⱼw′₂))`
  C₁…C₄ = classes of Kripke models whose relations (or pairs) satisfy Φ₁…Φ₄.
- **Definition (𝔄ctual)**: 𝔐 ∈ 𝔄ctual iff |𝔐(ε)| = 1 (the actual state of affairs). *(ms p.28)*

### 6.1 Theorem (representation1) *(ms p.28-30)*
For every 𝔐 ∈ 𝔄ctual there exist 𝔐^□ and A with 𝔐 ≡ 𝔐^□ w.r.t. A. Construction (four stages): `𝕊 := {⟨κ̄, ν⟩ | κ̄ ∈ 𝕂*, ν ∈ 𝔐(κ̄)}`; `A := {⟨κ̄, ν, ⟨κ̄, ν⟩⟩}`; π(⟨κ̄, ν⟩) = ν; `w Rᵢ w′ iff ∃κ̄ν ν′ (w = ⟨κ̄, ν⟩ and w′ = ⟨κ̄ * κᵢ, ν′⟩)`; actual world ⟨ε, ν⟩ (unique since 𝔐 ∈ 𝔄ctual); 𝔐^□ := ⟨𝕊, w₀, π, R_β⟩_{β<|𝕂|}. Properties: the ε-world has no Rᵢ-predecessors; if 𝔐(κ̄ * κᵢ) = ∅, worlds of κ̄ have no Rᵢ-successors. Elementary equivalence by induction (atomic, negation, implication, ist both directions). *(ms p.28-30)*

### 6.2 Theorem (representation2) *(ms p.30-32)*
Representable Kripke models = C₁ (the models satisfying Δ). For every 𝔐^□ ∈ C₁ there is 𝔐 with 𝔐 ≡ 𝔐^□ w.r.t. A. Construction: 𝕂 := {R_β}_{β<α}; `A(ε, π(w₀), w₀)`; `A(κ̄ * Rᵢ, π(w), w) iff ∃w′ ∈ 𝕊 A(κ̄, π(w′), w′) and w′ Rᵢ w` (context sequences = paths from w₀; example path [w₂, R₈, R₅, R₁, R₄]); `𝔐(κ̄) = {π(w) | A(κ̄, π(w), w)}`. *(ms p.30-31)*
- **Lemma (association)**: `∀w∀w′ (A(κ̄, π(w), w) and A(κ̄ * Rᵢ, π(w′), w′)) implies w Rᵢ w′` — all worlds of κ̄ are Rᵢ-related to all worlds of κ̄ * Rᵢ; follows from the construction of A and Φ₁. Proof by induction on |κ̄| (base: only w₀ associated with ε; step uses Φ₁). *(ms p.31-32)*
- ist case of equivalence in both directions uses the association lemma. *(ms p.31-32)*

### 6.3 Discussion *(ms p.33)*
Results depend on the definitions of Kripke model and elementary equivalence. If the actual world is excluded from Kripke models, representation1 generalizes to all context models; representation2 would then need multiple subtrees in one context model (e.g. connect subtrees to ε with empty vocabulary). Stronger results with A matching every world would again need vocabularies or multiple rooted subtrees. Purpose: the general flavor of relative expressiveness and a comparison methodology.

### 6.4 Proposition (correspondences) *(ms p.33-34)*
If 𝔐 ≡ 𝔐^□ w.r.t. A: (1) 𝔐^□ ∈ C₂ ⇒ 𝔐 ∈ ℭonsistent; (2) 𝔐^□ ∈ C₃ ⇒ 𝔐 ∈ 𝔗ruth; (3) 𝔐^□ ∈ C₄ ⇒ 𝔐 ∈ 𝔉lat.
- Proof (1): if 𝔐 ∉ ℭonsistent, pick the highest κ̄ * κᵢ with 𝔐(κ̄ * κᵢ) = ∅; then not `𝔐, ν ⊨_κ̄ ¬ist(κᵢ, ⊥)`, so not `𝔐^□, w ⊨ ¬□ᵢ⊥`, so 𝔐^□ ∉ C₂. □ *(ms p.33)*
- (2) uses `not 𝔐^□, w ⊨ □ᵢφ ∨ ¬□ᵢφ` [as printed] ⇒ not in C₃; (3) uses `not 𝔐^□, w ⊨ (□ᵢ□ⱼφ → □ⱼφ) ∧ (□ᵢ¬□ⱼφ → ¬□ⱼφ)`, corresponding to (4⁻¹), (5⁻¹); since (4⁻¹)+(5⁻¹) is equivalent to (4)+(5)+(D) (§3.3), and those correspondences are known, they characterize C₄. *(ms p.34)*

## 7 Related Work *(ms p.34-36)*
- McCarthy [16, 18]: contexts as formal objects, ist(κ, φ), transcending limited axiomatizations. *(ms p.34)*
- Three ways contexts differ: vocabularies; same vocabulary different states of affairs; (first order) same vocabulary treated differently (arities). First two studied in [3]; Lifschitz [15] the third; Shoham [19] the second (every proposition meaningful in every context; κ₁ •⊃ κ₂ "as general as"; contexts identified with propositions current-context-is(κ); ist(κ, p) as current-context-is(κ) → p with intuitionistic/relevance implication; 14 benchmark sentences). *(ms p.34-35)*
- Guha: examples of context use, motivated by and implemented in Cyc micro-theories. *(ms p.35)*
- Giunchiglia [10] (after Weyhrauch [20]) multilanguage systems: different vocabularies allowed but no ist modality; bridge rules infer formulas in one context from facts in another; proof-theoretic, semantics never made precise, "procedural flavor"; "significantly weaker" than the systems above. *(ms p.35)*
- Attardi & Simi [1] viewpoints: syntactic modality (names of sentences, ist as a predicate) allows self-reference and paradoxes; much of their work avoids paradoxes by weakening the CS-analogue, so ist(κ₁, p) in κ̄ need not give p in κ̄ * κ₁; viewpoints are sets of sentence names (assumptions), not primitive objects, with axioms like `ist(κ, p) → (κ → p)` (similar to Shoham); all viewpoints share one language (no partiality). *(ms p.35)*

### 7.1 Comparison to Logic of Belief *(ms p.35-36)*
ist(κ, φ) can read as "agent κ knows/believes φ" [14], but ist captures what is actually true/valid in a context, not believed. Shown by (Δ), which (ignoring vocabulary) is `ist(κ₁, ist(κ₂, φ)) ∨ ist(κ₁, ¬ist(κ₂, φ))`: a context is committed on what is valid in another context. Not true of belief (no agent is committed on others' beliefs). Justification via contexts as knowledge bases: κ₁ "can see into" κ₂ and decide validity of any φ there. Kripke semantics for belief would not reify contexts as first-class objects (needed in the predicate case to relate contexts, define operations, and lift sentences). Vocabulary is not commonly addressed in belief logics. *(ms p.35-36)*

## 8 Conclusions and Future Work *(ms p.36)*
Extend to full quantificational logic (relations between contexts, operations, lifting rules); with context variables the vocabulary of a sentence may depend on variable bindings, so first examine propositional systems with dynamic meaningfulness. Non-Hilbert systems, notably natural deduction (entering a context = making an assumption; exiting = discharging), in line with McCarthy.

## Parameters
None; purely formal paper (no numeric parameters or measurements).

## Figures of Interest
- **Table 1 (ms p.8):** axioms PL, K, Δ and rules MP, CS (with proviso κ̄ ≤ κ̄₀).

## Results Summary
- General system (PL, K, Δ, MP, CS) sound and complete for models classical on Vocab. *(ms p.12-17)*
- (ND) and (Δ−) each equivalent to (Δ); generalized K*, Δ*, Δ*−, CS* over context sequences; CNF lemma. *(ms p.8-12)*
- (D) ↔ consistent models; (Tr) ↔ truth models; (4⁻¹)+(5⁻¹) ↔ flat models; (MF) for meaninglessness-as-falsity. *(ms p.18-23)*
- Finite model property and decidability of validity. *(ms p.24-26)*
- Every actual context model has an elementarily equivalent Kripke model; every C₁ (Δ-satisfying) Kripke model has an elementarily equivalent context model; C₂/C₃/C₄ map to consistent/truth/flat. *(ms p.28-34)*

## Changes relative to Buvač & Mason 1993 (AAAI-93) observed in the page images
- `ist(ε, φ) := φ` abbreviation added. *(ms p.4)*
- Explicit justification for a modal operator over a reified ist predicate (no self-reference/paradox). *(ms p.4)*
- Proof that the shared-domain condition 1 is not a real restriction (𝔐′ construction). *(ms p.5-6)*
- Explicit "neither 𝔐,ν ⊨ χ nor 𝔐,ν ⊨ ¬χ" when preconditions fail. *(ms p.7)*
- One axiom (Δ) instead of Δ+ and Δ−; Δ− and (ND) derived and shown equivalent; new derived rule (CSE). *(ms p.8-10)*
- (CS) carries proviso κ̄ ≤ κ̄₀. *(ms p.8)*
- Consistent and truth model conditions restricted to κ̄ < κ̄₀. *(ms p.18-19)*
- Flatness axioms (4⁻¹), (5⁻¹) replace (Fl+) biconditional and (Fl−). *(ms p.21)*
- New sections: decidability (§5) and Kripke comparison (§6); Giunchiglia and Attardi & Simi in related work. *(ms p.24-35)*

## Limitations
- Propositional only; static vocabulary analysis does not extend to quantified versions. *(ms p.6)*
- Context variables may prevent defining a sentence's vocabulary statically. *(ms p.36)*
- MF completeness only sketched. *(ms p.23)*
- Kripke representation results depend on chosen definitions; not a precise match. *(ms p.26, p.33)*
- Consistency of the root context κ̄₀ is not expressible in the language. *(ms p.19)*

## Arguments Against Prior Work
- No prior formal logical explication of contexts. *(ms p.2)*
- Attardi & Simi: reified ist permits self-reference/paradoxes, forces weakening CS; viewpoints are not primitive; no partiality. *(ms p.4, p.35)*
- Giunchiglia: no ist modality, only bridge rules; semantics not made precise. *(ms p.35)*
- Shoham: every proposition meaningful in every context. *(ms p.34-35)*
- Belief logics: lack vocabularies/partiality; Kripke relations do not reify contexts; (Δ) fails for belief. *(ms p.35-36)*
- Guha's definedness (out-of-vocabulary ist is false) differs; modelled separately as MF. *(ms p.6, p.23)*

## Design Rationale
- Modal operator rather than predicate: natural semantics, no self-reference. *(ms p.4)*
- Context sequences for non-flatness/perspective. *(ms p.5)*
- No outermost context, so reasoners can always transcend their current context. *(ms p.6)*
- Bochvar (syntactic meaningfulness) not Kleene. *(ms p.7)*
- Validity reading of ist (Guha/Cyc); truth reading by restriction. *(ms p.4)*
- (Δ) encodes that a context is committed on what is valid in another (contexts as knowledge bases). *(ms p.36)*

## Testable Properties
- (ND) ⊣⊢ (Δ) ⊣⊢ (Δ−) in the general system. *(ms p.8-10)*
- (M) is the converse of (C) and derivable from K, PL, MP. *(ms p.8)*
- Every formula has a provably equivalent CNF. *(ms p.11-12)*
- `T₀ ⊢ ist(c̄, φ ∧ ¬φ)` iff `𝔐₀(κ̄₀ * c̄) = ∅`. *(ms p.15)*
- (4⁻¹) + (5⁻¹) ⊢ (D); (5) + (D) ⊢ (4⁻¹); (4) + (D) ⊢ (5⁻¹). *(ms p.21-22)*
- (D) + (Tr) ⊢ `ist(κ, φ ∨ ψ) ↔ ist(κ, φ) ∨ ist(κ, ψ)`. *(ms p.20)*
- Under MF, (Or) holds only when `Vocab(κ̄ * κ₁, φ ∨ ψ) ⊆ Vocab`. *(ms p.23)*
- Validity of a formula in a context is decidable by enumerating finitely many restricted models. *(ms p.26)*
- Kripke models representable by context models are exactly those in C₁ (Φ₁ ↔ Δ). *(ms p.30)*

## Relevance to Project
The journal version of the propositional ist logic that propstore's `ist(c, p)` contexts rest on, with three additions that matter here: decidability via a finite model property over the formula's own vocabulary (so context reasoning over finite claim sets can be decided by bounded model enumeration); an explicit semantics in which an out-of-vocabulary formula is neither satisfied nor refuted (non-commitment rather than forced falsity), with Guha's meaningless-as-false reading kept as a separate, explicitly chosen variant (MF); and the (Δ) axiom's reading that one context is committed on what is valid in another, which distinguishes ist from belief and bears on how lifting between contexts should behave. The no-outermost-context design and the "seemingly inconsistent KBs without contradiction" example match the storage discipline of holding rival claims in separate contexts.

## Open Questions
- [ ] Quantificational extension with lifting rules and dynamic meaningfulness. *(ms p.36)*
- [ ] Natural deduction for contexts. *(ms p.36)*
- [ ] The text says (4) and (5) are theorems "in our system", but the derivations use (4⁻¹)/(5⁻¹); it is not explicit whether they hold in the general system. *(ms p.21)*
- [ ] Whether the journal typeset version differs from this manuscript (not checked; journal copy not retrieved).

## Related Work Worth Reading
- [5] Buvač & Mason 1993, Propositional Logic of Context (in collection: Buvac_1993_PropositionalLogicContext).
- [6] V. Buvač 1994, Decidability of contextual reasoning (AAAI-94).
- [4] Buvač, Buvač & Mason 1994, The semantics of propositional contexts (ISMIS).
- [12] Guha 1991 thesis (in collection: Guha_1991_ContextsFormalization).
- [18] McCarthy 1993, Notes on formalizing context.
- [10] Giunchiglia & Serafini 1991, multilanguage systems.
- [1] Attardi & Simi 1993, A formalization of viewpoints.
- [7] Chellas 1980, Modal Logic.

## Collection Cross-References

### Already in Collection
- [Propositional Logic of Context](../Buvac_1993_PropositionalLogicContext/notes.md) - ref [5], the AAAI-93 conference version this paper extends
- [Contexts: A Formalization and Some Applications](../Guha_1991_ContextsFormalization/notes.md) - ref [12], source of the validity reading of `ist` and of the meaningless-as-false (MF) semantics
- [Notes on Formalizing Context](../McCarthy_1993_FormalizingContext/notes.md) - ref [18], `ist` and lifting

### New Leads (Not Yet in Collection)
- V. Buvač (1994) - "Decidability of contextual reasoning" - original decidability result
- Buvač, Buvač and Mason (1994) - "The semantics of propositional contexts" - ISMIS semantics paper
- Giunchiglia and Serafini (1991) - "Multilanguage first order theories of propositional attitudes" - multilanguage systems with bridge rules, the main rival formalism
- Attardi and Simi (1993) - "A formalization of viewpoints"
- Shoham (1991) - "Varieties of context"
- Halpern and Moses (1992) - "A guide to completeness and complexity for modal logics of knowledge and belief"
- de Kleer (1986) - "An assumption-based truth maintenance system" (no `deKleer_1986_AssumptionBasedTMS` directory exists, although other notes link to that name)
- Weyhrauch (1980) - "Prolegomena to a Theory of Mechanized Formal Reasoning"
- Chellas (1980) - "Modal Logic, an Introduction"

### Supersedes or Recontextualizes
- Extends [Propositional Logic of Context](../Buvac_1993_PropositionalLogicContext/notes.md): single (Δ) axiom with (Δ−) and (ND) shown equivalent, a more liberal definedness convention, a proviso on (CS), decidability via the finite model property, and representation theorems relating context models and Kripke models.

### Cited By (in Collection)
- [Formalizing Context (Expanded Notes)](../McCarthy_1997_FormalizingContextExpanded/notes.md) - ref [12], cited for the propositional-context to multi-modal reduction
- [Microtheories](../Kallem_2006_Microtheories/notes.md) - lists this for formal properties of context systems (its "contextual omniscience" gloss is not supported by these notes; see the correction in Kallem's notes)
- [Local Models Semantics, or Contextual Reasoning = Locality + Compatibility](../Ghidini_2001_LocalModelsSemanticsContextual/notes.md) - ref [7]

### Conceptual Links (not citation-based)
- [Local Models Semantics, or Contextual Reasoning = Locality + Compatibility](../Ghidini_2001_LocalModelsSemanticsContextual/notes.md) - Moderate. Both give a semantics for contexts with local vocabularies; Ghidini and Giunchiglia's multi-language, bridge-rule tradition (Giunchiglia and Serafini, cited here as the main rival) versus this paper's single modal language and Kripke-model representation.
