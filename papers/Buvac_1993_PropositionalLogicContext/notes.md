---
title: "Propositional Logic of Context"
authors: "Saša Buvač, Ian A. Mason"
year: 1993
venue: "Proceedings of the Eleventh National Conference on Artificial Intelligence (AAAI-93), pp. 412-419"
doi_url: null
pages: "412-419"
note: "Read from the authors' PostScript (8 pages, no printed page numbers). Page citations use AAAI pagination: page-000 = p.412 ... page-007 = p.419. The mapping was checked against the AAAI CDN copy, whose pages 1 and 6 carry printed numbers 412 and 417 and match pages 1 and 6 of the author copy in layout."
---

# Propositional Logic of Context

## One-Sentence Summary
Defines the syntax, partial-truth-assignment semantics, and a sound and complete Hilbert-style proof system for a propositional logic with a context modality `ist(κ, φ)`, per-context vocabularies, and nested (non-flat) context sequences, plus correspondence results for consistency (D), flatness (Fl±), truth (Tr), and a meaninglessness-as-falsity variant (MF). *(p.412-418)*

## Problem Addressed
Contexts had been introduced informally (McCarthy 1987 Turing lecture; Guha 1991 thesis; Cyc microtheories; KIF context proposals), but "till now no formal logical explication of contexts has been given." The paper supplies a formal propositional logic with model theory and proof theory. *(p.412)*

## Key Contributions
- A propositional language extending classical PL with the modality `ist(κ, φ)` ("φ holds in context κ") and per-context vocabularies of meaningful atoms. *(p.412-413)*
- A semantics with three features: non-flatness (truth is relative to a *sequence* of contexts, i.e. from where a context is viewed), `ist` as **validity** over a set of truth assignments per context, and **partial** truth assignments (Bochvar three-valued logic) for meaningless atoms. *(p.413)*
- Hilbert system (PL, K, Δ+, Δ−, MP, CS) under a *definedness convention*; soundness and completeness theorems; completeness via a CNF lemma and a novel truth-lemma proof. *(p.414-416)*
- Correspondence results: (D) ↔ consistent models; (Fl+),(Fl−) ↔ flat models; (Tr) ↔ truth models; (MF) for a meaninglessness-as-falsity semantics close to Guha's. *(p.417-418)*

## Methodology
Standard modal-logic metatheory adapted to context sequences: define wffs, models as functions from context sequences to sets of partial truth assignments, satisfaction relative to a context sequence, a Hilbert proof system relative to a fixed vocabulary, and a canonical-model completeness proof (Lindenbaum + canonical model 𝔐₀ + truth lemma via CNF). *(p.413-416)*

## Notation *(p.412)*
- `X →_p Y`: set of partial functions from X to Y. `P(X)`: powerset of X.
- `X*`: finite sequences; `x̄ = [x₁,…,xₙ]` ranges over X*; `ε` is the empty sequence; `*` is append; no distinction between an element and the singleton sequence, so `x̄ * x₁` for `x̄ * [x₁]`.
- X* is treated as a tree growing downward: `x̄₁ < x̄₀ ≤ ε` iff x̄₁ properly extends x̄₀, i.e. `(∃ȳ ∈ X* − {ε})(x̄₁ = x̄₀ * ȳ)`.
- `Y ⊆ X*` is a **subtree rooted at ȳ** iff (1) `ȳ ∈ Y` and `(∀z̄ ∈ Y)(z̄ ≤ ȳ)`; (2) `(∀z̄ ∈ Y)(∀w̄ ∈ X*)(z̄ ≤ w̄ ≤ ȳ → w̄ ∈ Y)`.

## Syntax *(p.413)*
- 𝕂: countably infinite set of contexts; ℙ: countably infinite set of propositional atoms (distinct sets).
- Connectives: ¬, →, plus `ist`. ∧, ∨, ↔ are abbreviations. A *literal* is an atom or a negated atom. `±φ` stands for φ or ¬φ.

$$
\mathbb{W} = \mathbb{P} \cup (\neg\mathbb{W}) \cup (\mathbb{W} \to \mathbb{W}) \cup \mathrm{ist}(\mathbb{K}, \mathbb{W})
$$
*(p.413)*

Abbreviations, for κ̄ = [κ₁,…,κₙ]:

$$
\mathrm{ist}(\bar\kappa, \phi) := \mathrm{ist}(\kappa_1, \mathrm{ist}(\kappa_2, \ldots, \mathrm{ist}(\kappa_n, \phi)))
$$

$$
\mathrm{ist}^{\pm}(\bar\kappa, \phi) := \pm\mathrm{ist}(\kappa_1, \pm\mathrm{ist}(\kappa_2, \cdots \pm \mathrm{ist}(\kappa_n, \phi)\cdots))
$$
In `ist±` the signs need not all have the same parity. *(p.413)*

- PROP: the set of wffs containing no `ist`.
- Instance: if ψ contains distinct atoms p₁…pₙ, ψ(φ₁,…,φₙ) is the result of simultaneously replacing each pᵢ by φᵢ. *(p.413)*

## Semantics *(p.413-414)*

Three features of the general system (fewest semantic restrictions; other systems obtained by restricting models and adding axioms):
1. **Non-flatness**: the nature of a context may itself be context dependent (e.g. car racing in the 1950s viewed from today vs. from the 1950s), so semantics is over *sequences* of contexts. Desirable e.g. when representing an agent's beliefs as sentences holding in a context. Flat systems are obtained by restricting models and enriching axioms. *(p.413)*
2. **ist as validity**: a context is modelled by a *set* of truth assignments (possible states of affairs); `ist(κ, ρ)` is true iff ρ is true in all truth assignments associated with κ. This follows Guha's proposal for Cyc. Treating `ist` as truth (one assignment per context) is a restriction plus extra axioms. *(p.413)*
3. **Partial assignments**: different contexts have different vocabularies; some propositions are meaningless in some contexts. *(p.413)*

**Definition (𝔐)** *(p.413)*:

$$
\mathfrak{M} \in \mathbb{K}^* \to_p \mathbf{P}(\mathbb{P} \to_p 2)
$$
with conditions:
1. `(∀κ̄)(∀ν₁, ν₂ ∈ 𝔐(κ̄))(Dom(ν₁) = Dom(ν₂))` — all assignments of one context sequence share a domain.
2. `Dom(𝔐)` is a subtree of 𝕂* rooted at some context sequence κ̄₀.

`κ̄^𝔐` denotes 𝔐(κ̄); it can be empty. 𝕄 is the collection of all models. *(p.413)*

Design choice: assuming a fixed outermost context would give Dom(𝔐) rooted at ε and simpler proofs, but the definition rests on the intuition that **there is no outermost context**. *(p.413)*

**Definition (Vocab of 𝔐)** *(p.413)*: Vocab relation `Vocab ⊆ 𝕂* × ℙ`.

$$
\mathit{Vocab}(\mathfrak{M}) := \{\langle\bar\kappa, \rho\rangle \mid \bar\kappa \in \mathrm{Dom}(\mathfrak{M}) \wedge \rho \in \mathrm{Dom}(\mathfrak{M}(\bar\kappa))\}
$$
𝔐 is **classical on vocabulary Vocab** iff `Vocab ⊆ Vocab(𝔐)`. *(p.413)*

**Definition (Vocab of φ in κ̄)** *(p.414)*: `Vocab : 𝕂* × 𝕎 → P(𝕂* × ℙ)`:
- `{⟨κ̄, φ⟩}` if φ ∈ ℙ
- `Vocab(κ̄, φ₀)` if φ = ¬φ₀
- `Vocab(κ̄ * κ, φ₀)` if φ = ist(κ, φ₀)
- `Vocab(κ̄, φ₀) ∪ Vocab(κ̄, φ₁)` if φ = φ₀ → φ₁

Extended to sets of formulas. This static vocabulary analysis is possible only in the propositional case, not in quantified versions. It differs from Guha's definedness, where `ist(κ, φ)` is false if φ is not in κ's vocabulary. *(p.414)*

**Satisfaction** uses Bochvar's three-valued logic (an implication is meaningless if antecedent or consequent is meaningless), chosen because meaningfulness is meant as *syntactic* meaningfulness, not semantic meaningfulness à la Kleene. *(p.414)*

**Definition (⊨)** *(p.414)*: if `ν ∈ κ̄^𝔐` and `Vocab(κ̄, φ) ⊆ Vocab(𝔐)`, then
- `𝔐, ν ⊨_κ̄ ρ` iff ν(ρ) = 1, for ρ ∈ ℙ
- `𝔐, ν ⊨_κ̄ ¬φ` iff not `𝔐, ν ⊨_κ̄ φ`
- `𝔐, ν ⊨_κ̄ φ → ψ` iff `𝔐, ν ⊨_κ̄ φ` implies `𝔐, ν ⊨_κ̄ ψ`
- `𝔐, ν ⊨_κ̄ ist(κ₁, φ)` iff `∀ν₁ ∈ (κ̄*κ₁)^𝔐`, `𝔐, ν₁ ⊨_{κ̄*κ₁} φ`

κ̄ * κ₁ ∈ Dom(𝔐) holds because Dom(𝔐) is a rooted subtree and Vocab(κ̄, φ) ⊆ Vocab(𝔐). `𝔐 ⊨_κ̄ φ` iff `∀ν ∈ κ̄^𝔐, 𝔐, ν ⊨_κ̄ φ`. *(p.414)*

## Formal System *(p.414-415)*
Fix a vocabulary `Vocab ⊂ 𝕂* × ℙ`; provability `⊢^Vocab_κ̄`, written `⊢_κ̄ φ`.

**Definedness Convention**: whenever we write `⊢_κ̄ φ` we implicitly assume `Vocab(κ̄, φ) ⊆ Vocab`. The inference rules preserve the convention. *(p.414)*

**Table 1: Axioms and Inference Rules** *(p.415)*:
- (PL) `⊢_κ̄ φ` provided φ is an instance of a tautology.
- (K) `⊢_κ̄ ist(κ₁, φ → ψ) → ist(κ₁, φ) → ist(κ₁, ψ)`
- (Δ+) `⊢_κ̄ ist(κ₁, ist(κ₂, φ) ∨ ψ) → ist(κ₁, ist(κ₂, φ)) ∨ ist(κ₁, ψ)`
- (Δ−) `⊢_κ̄ ist(κ₁, ¬ist(κ₂, φ) ∨ ψ) → ist(κ₁, ¬ist(κ₂, φ)) ∨ ist(κ₁, ψ)`
- (MP) from `⊢_κ̄ φ` and `⊢_κ̄ φ → ψ` infer `⊢_κ̄ ψ`
- (CS) from `⊢_{κ̄*κ₁} φ` infer `⊢_κ̄ ist(κ₁, φ)` (context switching)

With one context, (CS) is necessitation and (K) is the standard K; ignoring Δ±, the system is the normal modal system (PL, MP, K, necessitation). Δ+ and Δ− accommodate the *validity* reading of `ist`; they are derivable in the system that treats `ist` as truth and disallows inconsistent contexts. *(p.414)*

**Provability** *(p.414)*: `⊢_κ̄ φ` iff it is an axiom instance or follows from provable formulas by rules; formally a sequence `[⊢_{κ̄₁} φ₁, …, ⊢_{κ̄ₙ} φₙ]` with κ̄ₙ = κ̄, φₙ = φ, each element an axiom or derived from earlier ones. From assumptions T in κ̄₀: `T ⊢_{κ̄₀} φ` iff there are φ₁…φₙ ∈ T with `⊢_{κ̄₀} (φ₁ ∧ … ∧ φₙ) → φ`. By the definedness convention, `T ⊢_{κ̄₀} φ` implies `Vocab(T) ⊆ Vocab`. *(p.414)*

**Consequences (derivable)** *(p.414)*:
- (C) `⊢_κ̄ ist(κ₁, φ) ∧ ist(κ₁, ψ) → ist(κ₁, φ ∧ ψ)`
- (Or) `⊢_κ̄ ist(κ₁, φ) ∨ ist(κ₁, ψ) → ist(κ₁, φ ∨ ψ)`
- (M) `⊢_κ̄ ist(κ₁, φ ∧ ψ) → ist(κ₁, φ) ∧ ist(κ₁, ψ)`
- (K*) `⊢_κ̄ ist(c̄, φ → ψ) → ist(c̄, φ) → ist(c̄, ψ)`
- (REP) from `⊢_κ̄ φ₁ ↔ φ′₁ … ⊢_κ̄ φₙ ↔ φ′ₙ` infer `⊢_κ̄ ψ(φ₁,…,φₙ) ↔ ψ(φ′₁,…,φ′ₙ)` provided ψ(p₁…pₙ) ∈ PROP.

Note: only (Or), not its converse, holds in the general (validity) system; the converse holds only with (D)+(Tr) (see Truth). *(p.414, p.418)*

**Definition (CNF)** *(p.414)*: φ is in CNF iff `E₁ ∧ … ∧ E_k`, each `Eᵢ = αᵢ₁ ∨ … ∨ αᵢᵣᵢ`, each α a literal or `ist±(c̄, β)` with β a disjunction of literals. i and k can be 1.

**Lemma (CNF)** *(p.414)*: for any φ and κ̄ there is φ* in CNF with `⊢_κ̄ φ ↔ φ*`. (Δ± are what allow pushing disjunctions out of `ist`.)

## Soundness and Completeness *(p.415-416)*

**Theorem (soundness)** *(p.415)*: If `⊢_κ̄ φ` then for all models 𝔐 classical on Vocab, `𝔐 ⊨_κ̄ φ`. If `T ⊢_κ̄ φ`, then for all models 𝔐 classical on Vocab, if `𝔐 ⊨_κ̄ ψ` for all ψ ∈ T then `𝔐 ⊨_κ̄ φ`.

**Definition (satisfiability)**: T is satisfiable in κ̄ with Vocab iff some 𝔐 classical on Vocab has `𝔐 ⊨_κ̄ φ` for all φ ∈ T. *(p.415)*

**Definition (consistency)**: φ (with Vocab(κ̄, φ) ⊆ Vocab) is consistent in κ̄ with Vocab iff not `⊢_κ̄ ¬φ`. Finite T consistent iff ⋀T consistent; infinite T consistent iff every finite subset is. Maximally consistent: consistent and for all φ ∉ T with Vocab(κ̄, φ) ⊆ Vocab, T ∪ {φ} inconsistent. *(p.415)*

**Lemma (Lindenbaum)**: consistent T extends to a maximally consistent T₀ in κ̄ with Vocab. *(p.415)*

**Theorem (completeness)** *(p.415)*: T is consistent in κ̄₀ with Vocab iff T is satisfiable in κ̄₀ with Vocab.

**Proof construction** *(p.415)*: extend T to maximally consistent T₀. For each `κ̄ = κ̄₀ * c̄ ∈ 𝕂*`:

$$
T_{\bar\kappa+} := \{\phi \mid T_0 \vdash_{\bar\kappa_0} \mathrm{ist}(\bar c, \phi), \phi \in \mathrm{PROP}\}
$$

**Lemma (T_κ̄+)**: closed under logical consequence: for φ with Vocab(κ̄, φ) ⊆ Vocab, if φ tautologically follows from T_κ̄+ then φ ∈ T_κ̄+. T_κ̄+ need not be maximally consistent or even consistent. *(p.415)*

Canonical model 𝔐₀:

$$
\mathrm{Dom}(\mathfrak{M}_0) := \{\bar\kappa \mid \bar\kappa \le \bar\kappa_0, \exists \bar\kappa' \in \mathrm{Dom}(\mathsf{Vocab}), \bar\kappa' \le \bar\kappa\}
$$

$$
\mathfrak{M}_0(\bar\kappa) := \{\nu \mid \mathrm{Dom}(\nu) = \mathsf{Vocab}(\bar\kappa), \forall\phi \in T_{\bar\kappa+}, \bar\nu(\phi) = 1\}
$$
ν̄ is the unique homomorphic extension of ν over the connectives. Condition 1 holds (shared domain); condition 2 holds (subtree rooted at κ̄₀). If T_κ̄+ is empty (Vocab(κ̄) = ∅), 𝔐₀(κ̄) is the singleton containing the *empty truth assignment*. Completeness reduces to the truth lemma, whose proof via CNF is the paper's novel element. *(p.415)*

**Lemma (truth)** *(p.415)*: for φ with Vocab(κ̄₀, φ) ⊆ Vocab, `φ ∈ T₀ iff 𝔐₀ ⊨_{κ̄₀} φ`. Hence φ ∈ T gives 𝔐₀ ⊨_{κ̄₀} φ. □

**Lemma (𝔐₀)** *(p.416)*: for φ ∈ PROP with Vocab(κ̄₀ * c̄, φ) ⊆ Vocab: `T₀ ⊢_{κ̄₀} ist(c̄, φ)` iff for all ν ∈ 𝔐₀(κ̄₀ * c̄), ν(φ) = 1. Frequent instance: `T₀ ⊢_{κ̄₀} ist(c̄, φ ∧ ¬φ)` iff `𝔐₀(κ̄₀ * c̄) = ∅`.

**Proof of truth lemma** *(p.416)*: prove (TL): ψ in CNF implies (ψ ∈ T₀ iff 𝔐₀ ⊨_{κ̄₀} ψ). The general case follows via the CNF lemma, maximal consistency of T₀ and soundness. Induction on ψ: atoms from the definition of 𝔐₀(κ̄₀); ∨ via maximal consistency (χ∨μ ∈ T₀ iff χ ∈ T₀ or μ ∈ T₀); ∧, ¬ similar; sub-formulas of CNF formulas are CNF. Interesting case ψ = `ist±(c̄, χ)` with χ a disjunction of literals, c̄ = κ₁ * … * κₙ. Two cases, depending on whether any T_{(κ̄₀*c̄′)+} with c̄ ≤ c̄′ is inconsistent. They are all consistent iff

$$
(D_{\bar c})\quad \mathrm{ist}(\bar c, \neg\phi) \to \neg\mathrm{ist}(\bar c, \phi)
$$
is in T₀ for any wff φ satisfying definedness; equivalently `¬ist(c̄, φ ∧ ¬φ) ∈ T₀`. *(p.416)*

**Lemma (D_c̄)** *(p.416)*: let c̄ = κ₁ * … * κₙ. If `D_{(κ₁*…*κₙ₋₁)} ∈ T₀` then `ist±(c̄, φ) ∈ T₀ iff ±ist(c̄, φ) ∈ T₀`, the sign on the right positive iff there is an even number of negations in the ist± on the left.

- Case `D_{(κ₁*…*κₙ₋₁)} ∈ T₀`: via the D_c̄ lemma, the 𝔐₀ lemma and the definition of satisfaction, `𝔐₀ ⊨_{κ̄₀} ist(c̄, χ) iff 𝔐₀ ⊨_{κ̄₀} ist±(c̄, χ)`; only the positive case is given. *(p.416)*
- Case `D_{(κ₁*…*κₙ₋₁)} ∉ T₀`: let j be the index of the first inconsistent context (`D_{(κ₁*…*κⱼ)} ∉ T₀`, `D_{(κ₁*…*κⱼ₋₁)} ∈ T₀`). Then `¬ist(κ₁*…*κⱼ, φ∧¬φ) ∉ T₀`; by maximal consistency, (K*), (MP), `ist(κ₁*…*κⱼ, φ∧¬φ) ∈ T₀ iff ist(κ₁*…*κⱼ, ψ) ∈ T₀`; so T_{(κ̄₀*κ₁*…*κⱼ)+} is inconsistent, 𝔐₀(κ̄₀*κ₁*…*κⱼ) = ∅, and the result follows similarly. *(p.416)*
- The ist step needs no inductive hypothesis; it uses only the special form of χ guaranteed by CNF. □ *(p.416)*

## Correspondence Results *(p.417-418)*
Same syntax and semantics; definedness convention still holds; only the model class and axioms change.

### Consistency *(p.417)*
Class ℭonsistent: 𝔐 ∈ ℭonsistent iff for any κ̄ ∈ Dom(𝔐), 𝔐(κ̄) ≠ ∅.
- (D) `⊢_κ̄ ist(κ, ¬φ) → ¬ist(κ, φ)` — sound for ℭonsistent; commonly used in modal logic; sound and complete for serial Kripke frames. Equivalent to `⊢_κ̄ ¬ist(κ, φ ∧ ¬φ)` (the page image prints `⊢_κ̄ ist(κ, φ ∧ ¬φ)` without the negation; that reading contradicts the stated equivalence with (D), so the negation appears to be missing in print).
- **Theorem (completeness)**: general system + (D) is complete w.r.t. ℭonsistent.

### Flatness *(p.417)*
Motivation: independent databases — booked on flight 921 in the Northwest airlines database context holds regardless of which travel agent's context it is viewed from.
- 𝔐 ∈ 𝔉lat iff Dom(𝔐) = 𝕂* and for any κ̄₁, κ̄₂, κ: `𝔐(κ̄₁ * κ) = 𝔐(κ̄₂ * κ)`.
- Equivalently 𝔐 ∈ 𝕂 ∪ {ε} ↦ P(ℙ →_p 2), with side condition `(∀κ̄ ∈ 𝕂∪{ε})(∀ν₁, ν₂ ∈ 𝔐(κ̄))(Dom(ν₁) = Dom(ν₂))`.
- (Fl+) `⊢_κ̄ ist(κ₂, ist(κ₁, φ)) ↔ ist(κ₁, φ)`
- (Fl−) `⊢_κ̄ ist(κ₂, ¬ist(κ₁, φ)) → ¬ist(κ₁, φ)`
- Sound for 𝔉lat provided the vocabulary satisfies the flatness condition `Vocab(κ̄₁ * κ) = Vocab(κ̄₂ * κ)`.
- Backward direction of (Fl+) corresponds to S4 (when κ₁ = κ₂); converse of (Fl−) corresponds to S5; the converse of (Fl−) is a theorem of the system.
- In every system with (Fl+) and (Fl−), (D) is derivable: every flat model is consistent. If a context were inconsistent, in it all other contexts would be inconsistent, and by flatness all other contexts would really be inconsistent.
- **Theorem (completeness)**: general system + (Fl+), (Fl−) is complete w.r.t. 𝔉lat.

### Truth *(p.417-418)*
`ist` = "is true", McCarthy's original suggestion (McCarthy 1993): one truth assignment per context.
- 𝔐 ∈ 𝔗ruth iff for any κ̄ ∈ Dom(𝔐), |𝔐(κ̄)| ≤ 1.
- (Tr) `⊢_κ̄ ist(κ, φ) ∨ ist(κ, ¬φ)`; (Tr) is the converse of (D).
- **Theorem (completeness)**: general system + (Tr) is complete w.r.t. 𝔗ruth.
- Δ+ and Δ− are derivable in a system with (D) and (Tr); stronger: `⊢_κ̄ ist(κ, φ ∨ ψ) ↔ (ist(κ, φ) ∨ ist(κ, ψ))`. *(p.418)*

### Meaninglessness as Falsity *(p.418)*
Models the semantics described but not investigated in Guha 1991: if φ is not in the vocabulary of κ, `ist(κ, φ)` is false rather than meaningless.
- New Vocab clause: `Vocab(κ̄, φ) = ∅ if φ is ist(κ, φ₀)` — `ist(κ, φ)` is always in the vocabulary of any context.
- New satisfaction clause: `𝔐, ν ⊨_κ̄ ist(κ₁, φ)` iff `Vocab(φ, κ̄ * κ₁) ⊆ Vocab(𝔐)` and for all `ν₁ ∈ (κ̄ * κ₁)^𝔐`, `𝔐, ν₁ ⊨_{κ̄*κ₁} φ`.
- Other clauses unchanged, with Vocab referring to the new definition; definedness convention maintained.
- New axiom (MF) `⊢_κ̄ ¬ist(κ₁, φ)` if `Vocab(κ̄ * κ₁, φ) ⊄ Vocab`.
- Completeness proof structurally similar; new points arise only from the liberal definition of Vocab.

## Parameters
None. The paper is purely formal; there are no numeric parameters, thresholds, or measured quantities.

## Figures of Interest
- **Table 1 (p.415):** the complete axiom and rule set (PL, K, Δ+, Δ−, MP, CS).

## Results Summary
- General system (PL, K, Δ+, Δ−, MP, CS) is sound and complete for models classical on a fixed vocabulary. *(p.415)*
- + (D) complete for consistent models; + (Fl+),(Fl−) complete for flat models (with the flat vocabulary condition); + (Tr) complete for truth models. *(p.417)*
- (MF) system for meaninglessness-as-falsity; completeness stated as structurally similar, proof not given. *(p.418)*

## Limitations
- Propositional only; static vocabulary analysis does not carry over to quantified versions. *(p.414)*
- In the presence of context variables the vocabulary of a sentence may not be definable without knowing what the variable is bound to. *(p.419)*
- Completeness proofs for D/Flat/Truth/MF extensions are stated, not given in this paper. *(p.417-418)*
- Only a Hilbert system; no natural deduction, no decision procedure (future work). *(p.419)*
- No lifting rules or relations between contexts: those need the quantificational system. *(p.419)*

## Arguments Against Prior Work
- No prior formal logical explication of contexts (McCarthy, Guha, KIF proposals were informal). *(p.412)*
- Guha's definedness treats `ist(κ, φ)` as false when φ is outside κ's vocabulary; the paper's main system instead treats it as meaningless, and captures Guha's reading separately as the MF variant. *(p.414, p.418)*
- Lifschitz 1986 concentrates on contexts treating the same vocabulary differently (arities); Shoham 1991 assumes every proposition meaningful in every context and defines `ist(κ, p)` as `current-context(κ) → p` under intuitionistic/relevance implication, with a generality relation κ₁ •⊃ κ₂ and 14 benchmark sentences. *(p.418)*
- Logics of knowledge and belief (Halpern & Moses 1992) do not handle variable vocabularies and partiality, and use possible-world relations; the authors want contexts reified as first-class objects in the semantics rather than modelling truth in a context by a relation between worlds. *(p.418-419)*

## Design Rationale
- Context **sequences**, not single contexts: what holds in a context depends on the path by which it is reached / perspective. *(p.413)*
- **No outermost context**: Dom(𝔐) rooted at some κ̄₀, not ε, despite simpler proofs with a fixed outermost context. *(p.413)*
- **Validity** reading of `ist` (set of assignments per context), following Guha/Cyc; truth reading recoverable by restriction + (Tr). *(p.413)*
- **Bochvar** (not Kleene) three-valued logic because meaningfulness is syntactic. *(p.414)*
- Δ+, Δ− added to K to accommodate validity semantics; they enable the CNF lemma. *(p.414)*
- Three ways contexts can differ: vocabulary; same vocabulary but different states of affairs; (first order) same vocabulary treated differently (arities). *(p.418)*

## Testable Properties
- With one context and ignoring Δ±, the system is the normal modal system K. *(p.414)*
- `⊢_κ̄ ist(κ₁, φ) ∨ ist(κ₁, ψ) → ist(κ₁, φ ∨ ψ)` holds in general; the converse holds when (D) and (Tr) are present. *(p.414, p.418)*
- Every formula is provably equivalent to a CNF formula whose ist-literals are `ist±(c̄, β)` with β a disjunction of literals. *(p.414)*
- If `T ⊢_{κ̄₀} φ` then `Vocab(T) ⊆ Vocab`. *(p.414)*
- A context sequence with empty vocabulary has exactly one (empty) truth assignment in the canonical model. *(p.415)*
- `T₀ ⊢ ist(c̄, φ ∧ ¬φ)` iff `𝔐₀(κ̄₀ * c̄) = ∅`. *(p.416)*
- (Fl+) + (Fl−) ⊢ (D). *(p.417)*
- (D) + (Tr) ⊢ Δ+, Δ−, and `ist(κ, φ ∨ ψ) ↔ ist(κ, φ) ∨ ist(κ, ψ)`. *(p.418)*
- Under MF, `¬ist(κ₁, φ)` is provable whenever `Vocab(κ̄ * κ₁, φ) ⊄ Vocab`. *(p.418)*

## Relevance to Project
propstore implements first-class `ist(c, p)` contexts with explicit claim context references and lifting rules (CLAUDE.md). This paper is the formal propositional base for that: it fixes what `ist` means (validity over a set of partial assignments), why vocabularies are per-context and partial (a proposition can be meaningless rather than false in a context), why nesting/perspective matters (context sequences, non-flatness), and which axioms correspond to which assumptions (D: no inconsistent contexts; Fl±: flatness; Tr: ist-as-truth; MF: Guha's meaningless-as-false). For the non-commitment discipline: the general system lets an inconsistent context exist (𝔐(κ̄) = ∅) without forcing global inconsistency; adding (D) rules that out. The choice between meaningless and false for out-of-vocabulary claims (main system vs. MF) maps onto how a render policy treats a claim whose concepts are not in a context's vocabulary.

## Open Questions
- [ ] Quantificational extension, lifting rules, relations between contexts (addressed later in Buvač 1996 "Quantificational Logic of Context"). *(p.419)*
- [ ] Natural-deduction system where entering/exiting a context = making/discharging an assumption. *(p.419)*
- [ ] Decision procedure in the style of Mints 1992 (addressed in the journal version, Buvač, Buvač & Mason 1995). *(p.419)*
- [ ] Possible typo in the (D) equivalence on p.417 (missing ¬).

## Related Work Worth Reading
- Guha 1991, *Contexts: A Formalization and Some Applications* (already in collection as Guha_1991_ContextsFormalization).
- McCarthy 1993, "Notes on formalizing context" (IJCAI-93).
- McCarthy 1987, "Generality in artificial intelligence."
- Shoham 1991, "Varieties of context."
- Halpern & Moses 1992, "A guide to completeness and complexity for modal logics of knowledge and belief."
- Bochvar 1972 (three-valued logic); de Kleer 1986 (ATMS contexts).
- Buvač, Buvač & Mason 1995, "Metamathematics of Contexts" (journal version, adds decidability).

## Collection Cross-References

### Already in Collection
- [Contexts: A Formalization and Some Applications](../Guha_1991_ContextsFormalization/notes.md) - the thesis whose validity reading of `ist` and treatment of meaningless sentences this paper formalizes; the (MF) meaninglessness-as-falsity variant is presented as close to Guha's semantics *(p.412, p.418)*
- [Notes on Formalizing Context](../McCarthy_1993_FormalizingContext/notes.md) - the original `ist` proposal (McCarthy 1993, IJCAI-93, cited as "to appear") that this paper gives a propositional logic for *(p.412)*

### New Leads (Not Yet in Collection)
- Shoham (1991) - "Varieties of context" - rival approach in which every proposition is meaningful in every context
- Halpern and Moses (1992) - "A guide to completeness and complexity for modal logics of knowledge and belief" - the modal logics this system relates to
- de Kleer (1986) - "An assumption-based truth maintenance system" - ATMS contexts (no `deKleer_1986_AssumptionBasedTMS` directory exists in the collection, although other notes link to that name)
- McCarthy (1987) - "Generality in artificial intelligence" - the Turing lecture introducing contexts
- Bochvar (1972) - "Two papers on partial predicate calculus" - the three-valued logic behind the partial truth assignments
- Mints (1992) - "Lewis' systems and system T" - the style of decision procedure proposed as future work
- Genesereth and Fikes (1992) - KIF 3.0 reference manual - KIF context proposals

### Supersedes or Recontextualizes
- (none)
- **See also:** [Metamathematics of Contexts](../Buvac_1995_MetamathematicsContexts/notes.md) - the journal version extends and partly supersedes this paper: reworked axioms and definedness convention, decidability, and Kripke-model representation theorems

### Cited By (in Collection)
- [Metamathematics of Contexts](../Buvac_1995_MetamathematicsContexts/notes.md) - the journal version (ref [5]); its Hilbert system uses a single (Δ) axiom (this paper's Δ+), with (Δ−) shown equivalent, and adds decidability and Kripke-model representation results
- [Notes on Formalizing Context](../McCarthy_1993_FormalizingContext/notes.md) - cites this as the formal propositional logic of context
- [A Defeasible Logic-based Framework for Contextualizing Deployed Applications](../Al-Anbaki_2019_DefeasibleLogicContextualizingApplications/notes.md) - ref [20], companion to McCarthy for the propositional layer of `ist`
- [Defeasible Contextual Reasoning with Arguments in Ambient Intelligence](../Bikakis_2010_DefeasibleContextualReasoningArguments/notes.md) - ref [10], companion to McCarthy's `ist` formalisation

### Conceptual Links (not citation-based)
- [Formalizing Context (Expanded Notes)](../McCarthy_1997_FormalizingContextExpanded/notes.md) - Strong. McCarthy and Buvač's expanded notes are the axiomatic, first-order `ist(c, p)` account with lifting axioms, co-authored by this paper's first author; they report (via Buvač, Buvač and Mason 1995) that propositional context logic reduces to multi-modal logic and (via Buvač 1996) that the reduction fails for the quantified case, which is the extension this paper leaves open.
- [Local Models Semantics, or Contextual Reasoning = Locality + Compatibility](../Ghidini_2001_LocalModelsSemanticsContextual/notes.md) - Moderate. Ghidini and Giunchiglia give a rival semantics for contexts with multiple local languages and Tarskian local models related by compatibility; this paper instead keeps one modal language with `ist` and per-context partial vocabularies. Both make vocabulary local to a context.
- [Microtheories](../Kallem_2006_Microtheories/notes.md) - Moderate. Cyc microtheories are the engineering form of the contexts this paper formalizes, with inheritance between microtheories where this paper has nested context sequences.
