---
title: "Rational Closure for Defeasible Description Logics"
authors: "Giovanni Casini, Umberto Straccia"
year: 2010
venue: "JELIA 2010 (12th European Conference on Logics in Artificial Intelligence), LNAI 6341, Springer-Verlag Berlin Heidelberg"
pages: "77-90"
doi_url: "https://doi.org/10.1007/978-3-642-15675-5_9"
affiliations:
  - "Scuola Normale Superiore, Pisa, Italy"
  - "Istituto di Scienza e Tecnologie dell'Informazione (ISTI - CNR), Pisa, Italy"
produced_by:
  agent: "claude-opus-4-7[1m]"
  skill: "paper-reader"
  status: "stated"
  timestamp: "2026-04-28T07:49:07Z"
---
# Rational Closure for Defeasible Description Logics

## One-Sentence Summary
Casini & Straccia give a default-assumption (Poole/Freund) reformulation of Lehmann–Magidor rational closure that needs only classical entailment checks, then port the construction into the description logic ALC to support a defeasible subsumption operator C |~ D, with the propositional case shown coNP-complete and the ALC case EXPTIME-complete.

## Problem Addressed
DLs (ALC etc.) are monotonic. Substantial prior work integrates non-monotonic reasoning into DLs (refs [1,4,5,7,8,9,10,11,12,13,14,15,17,18,21,22,23,24,25,27,31,32,34,35,36]) but, per the authors, none specifically model *rational closure* — the well-behaved Lehmann–Magidor rational consequence relation [28] — for DLs *(p.77)*. Lehmann–Magidor's original construction uses preferential-closure tests (computing P(B)); the authors want a construction that uses only classical entailment ⊨, so it can be directly implemented on top of a standard DL reasoner *(p.77)*.

## Key Contributions
- (i) A reformulation of propositional rational closure as a six-step transformation K = ⟨T,B⟩ ⤳ ⟨∅,B′⟩ ⤳ ⟨T̃,B̃⟩ ⤳ ⟨T̃,Δ̃⟩ that yields a default-assumption KB whose default-assumption consequence relation coincides with the rational closure R(B′) of Lehmann–Magidor [28]; built on Freund's representation result [19] *(p.77, p.81)*.
- (ii) A transposition of this construction to ALC: a concept-level defeasible operator C |~ D whose consequence relation is shown to be a rational consequence relation, and a corresponding ABox-level relation ⊩_s parameterised by a linear order s on individuals *(p.77, p.84, p.87)*.
- (iii) Complexity results: deciding propositional defeasible consequence under rational closure is coNP-complete (Corollary 1, p.81); deciding C |~ D in ALC is EXPTIME-complete (Corollary 2, p.85); deciding K ⊩_s a:C in ALC with unfoldable TBox is PSPACE-complete (Proposition 7, p.88).
- (iv) Demonstrates closure inherits the underlying DL's complexity (so polynomial for EL, citing [2]) *(p.85)*.

## Study Design (empirical papers)
*(Not applicable — this is a theoretical / KR paper.)*

## Methodology
- Build on Freund [19], who shows a default-assumption (Poole-style [33]) construction reproduces the Lehmann–Magidor rational closure for propositional logic. The authors take Freund's machinery and combine it with material from Bochman [6] (clash, Corollary 7.5.2, Definition 7.5.2, Lemma 7.5.5) to fold a non-empty background theory T into the construction *(p.80)*.
- Map a conditional KB ⟨T,B⟩ to a default-assumption KB ⟨T̃,Δ̃⟩ via an exceptionality ranking computed using only ⊨ over the materialisations of sequents *(p.80)*.
- For the DL case, replace propositions by ALC concepts, sequents C|~D by GCI-shaped tests ⊤ ⊑ C → D / ⊤ ⊑ ¬C, and reuse the construction line-for-line *(p.83–84)*.
- Handle individuals (ABox) under an *unfoldable* TBox restriction by completing A and applying defaults to individuals in a fixed linear order *(p.86)*.

## Key Equations / Statistical Models

### Default-assumption consequence (propositional)

$$
\Gamma \,|\!\!\sim_{\langle \mathcal{T},\Delta\rangle}\, D \iff (\mathcal{T}\cup\Gamma\cup\Delta')\models D \text{ for every } (\mathcal{T}\cup\Gamma)\text{-maxiconsistent } \Delta'\subseteq\Delta.
$$

Where: Δ′ is *Φ-maxiconsistent* in Δ iff (i) Δ′ ⊆ Δ, (ii) Δ′ ⊭ ¬(⋀ Φ), and (iii) no Δ′ ⊊ Δ″ ⊆ Δ also satisfies (ii). *(p.79)*

### Exceptionality ranking r (propositional)

$$
r(C\,|\!\!\sim D) = \begin{cases} i & \text{if } C\,|\!\!\sim D \in \mathcal{E}_i \text{ and } C\,|\!\!\sim D\notin \mathcal{E}_{i+1}\\ \infty & \text{if } C\,|\!\!\sim D \in \mathcal{E}_i \text{ for every } i\end{cases}
$$

Where: E_0 = B′; E_{i+1} = E(E_i) = {C|~D ∈ E_i | C is exceptional for E_i}; C is exceptional for D iff Γ_D ⊨ ¬C (Lehmann–Magidor [28], Cor. 5.22) *(p.80)*.

### Default-assumption set Δ̃ (propositional, Eq. 1)

$$
\delta_i = \bigwedge \{ C\to D \mid C\,|\!\!\sim D \in \widetilde{\mathcal{B}} \text{ and } r(C\,|\!\!\sim D)\ge i\}
$$

Where: B̃ = {C|~D ∈ B′ | r(C|~D) < ∞}; n is the highest finite rank-value in B̃; the produced sequence is linearly ordered by ⊨, i.e. δ_i ⊨ δ_{i+1} for 0 ≤ i < n *(p.81)*.

### KB transformation chain (Eq. 2, propositional)

$$
\mathcal{K} = \langle \mathcal{T},\mathcal{B}\rangle \rightsquigarrow \langle \emptyset,\mathcal{B}'\rangle \rightsquigarrow \langle \widetilde{\mathcal{T}},\widetilde{\mathcal{B}}\rangle \rightsquigarrow \langle \widetilde{\mathcal{T}},\widetilde{\Delta}\rangle
$$

Where: B′ = B ∪ {¬C |~ ⊥ | C ∈ T}; T̃ = {¬C | C|~D ∈ B′ and r(C|~D) = ∞}; B̃ = {C|~D ∈ B′ | r(C|~D) < ∞} *(p.80, p.81)*.

### Proposition 1 (equivalence with Lehmann–Magidor rational closure)

$$
\Gamma\,|\!\!\sim_{\langle \widetilde{\mathcal{T}},\widetilde{\Delta}\rangle}\, D \iff \Gamma\,|\!\!\sim D \in \mathbb{R}(\mathcal{B}')
$$

Where: R is the Lehmann–Magidor rational closure operation [28] *(p.81)*.

### Proposition 2 (linear-search decision procedure, propositional)

$$
\Gamma\,|\!\!\sim_{\langle \widetilde{\mathcal{T}},\widetilde{\Delta}\rangle}\, D \iff \widetilde{\mathcal{T}}\cup\Gamma\cup\{\delta_i\}\models D
$$

Where: δ_i is the first (Γ ∪ T̃)-consistent formula of the sequence ⟨δ_0, ..., δ_n⟩, i.e. the smallest i with T̃ ∪ Γ ⊭ ¬δ_i *(p.81)*. Footnote 4 makes the consistency condition explicit.

### DL default-assumption consequence (Section 3)

$$
\Gamma\,|\!\!\sim_{\langle \mathcal{T},\Delta\rangle}\, E \iff \models (\mathfrak{T}\cup\Gamma\cup\Delta') \sqsubseteq E \text{ for every } (\mathfrak{T}\cup\Gamma)\text{-maxiconsistent } \Delta'\subseteq\Delta.
$$

Where: T = {⊤ ⊑ C_1, ..., ⊤ ⊑ C_m}, 𝔗 = {C_1, ..., C_m} (the concept side of T), Γ a finite set of concepts, Δ a set of default concepts *(p.84)*.

### Proposition 3 (DL linear-search decision procedure)

$$
\Gamma\,|\!\!\sim_{\langle \widetilde{\mathcal{T}},\widetilde{\Delta}\rangle}\, D \iff \models \bigsqcap\Gamma \sqcap \bigsqcap \mathfrak{T} \sqcap \delta_i \sqsubseteq D
$$

Where: δ_i is the first (Γ ∪ 𝔗)-consistent formula of ⟨δ_0, ..., δ_n⟩, i.e. ⊭ ⋀𝔗 ⊓ ⋀Γ ⊑ ¬δ_i *(p.84, footnote 5)*.

### DL default-assumption set δ_i

$$
\delta_i = \bigsqcap\{C \to D \mid C\,|\!\!\sim D \in \widetilde{\mathcal{B}} \text{ and } r(C\,|\!\!\sim D)\ge i\}
$$

Where: C → D abbreviates ¬C ⊔ D in ALC *(p.83)*.

### Default-assumption extension on individuals

K̃ = ⟨A_Δ⟩ is a default-assumption extension of K = ⟨A, Δ⟩ iff:
- K̃ is classically consistent and A ⊆ A_Δ.
- For any a ∈ O_A, a:C ∈ A_Δ \ A iff C = δ_i for some i and for every δ_h with h < i, A_Δ ∪ {a:δ_h} ⊨ ⊥.
- There is no K′ ⊋ K̃ satisfying the above. *(p.86)*

## Parameters

### Construction parameters (single defeasible KB)

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Background theory (certain knowledge) | T | set of formulae / GCIs | — | — | 78, 83 | After transformation becomes T̃ |
| Conditional / defeasible base | B | set of sequents C\|~D | — | — | 78, 83 | After transformation becomes B̃ |
| ABox (DL only) | A | set of assertions a:C, (a,b):R | — | — | 83 | Used in individual-level closure |
| Default-assumption set | Δ | set of formulae / concepts | — | — | 78, 83 | Linearly ordered by ⊨ |
| Number of rank classes | n | — | — | finite | 81, 84 | Highest finite rank value in B̃ |
| Rank of a sequent | r(C\|~D) | — | — | {0,1,...,n} ∪ {∞} | 80 | ∞ ↔ part of background theory T̃ |
| Sequence of default formulae | ⟨δ_0,...,δ_n⟩ | — | — | — | 81, 83 | δ_i = ⋀{C→D : r(C\|~D) ≥ i}, with δ_0 ⊨ δ_1 ⊨ ... ⊨ δ_n |
| Linear order on individuals | s | tuple of O_A | — | any total order | 87 | Determines unique extension; priority of *attention*, not typicality |

### Penguin example (Example 3, p.82)

| Name | Symbol | Page | Value |
|------|--------|------|-------|
| Materialisations | Γ_B' | 82 | {P ∧ ¬B → ⊥, P → ¬F, B → F} |
| Antecedents | A_B' | 82 | {P ∧ ¬B, P, B} |
| E_0 | — | 82 | {P∧¬B \|~ ⊥, P\|~¬F, B\|~F} |
| E_1 | — | 82 | {P∧¬B \|~ ⊥, P\|~¬F} |
| E_2 | — | 82 | {P∧¬B \|~ ⊥} |
| E_3 | — | 82 | {P∧¬B \|~ ⊥} (fixed point) |
| r(B\|~F) | — | 82 | 0 |
| r(P\|~¬F) | — | 82 | 1 |
| r(P∧¬B \|~ ⊥) | — | 82 | ∞ |
| Background T̃ | — | 82 | {¬(P ∧ ¬B)} |
| δ_0 | — | 82 | (B → F) ∧ (P → ¬F) |
| δ_1 | — | 82 | P → ¬F |

### Bird/Penguin/Insect/Fish DL example (Example 5, p.85)

| Quantity | Page | Value |
|----------|------|-------|
| r(B\|~F) | 85 | 0 |
| r(B\|~∀Prey.I) | 85 | 0 |
| r(P\|~¬F) | 85 | 1 |
| r(P\|~∀Prey.Fi) | 85 | 1 |
| r(P ⊓ ¬B \|~ ⊥) | 85 | ∞ |
| r(I ⊓ Fi \|~ ⊥) | 85 | ∞ |
| Background T̃ | 85 | {⊤ ⊑ ¬(P∧¬B), ⊤ ⊑ ¬(I⊓Fi)} |
| δ_0 | 85 | (B→F) ⊓ (B→∀Prey.I) ⊓ (P→¬F) ⊓ (P→∀Prey.Fi) |
| δ_1 | 85 | (P→¬F) ⊓ (P→∀Prey.Fi) |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Decision complexity, propositional defeasible consequence under rational closure | complexity class | coNP-complete | — | — | classical propositional logic | 81 |
| Number of classical entailment tests for one query | count | O(\|K\|) | — | — | propositional | 81 |
| Decision complexity, C \|~ D in ALC | complexity class | EXPTIME-complete | — | — | ALC, concept-level | 85 |
| Decision complexity, C \|~ D in EL | complexity class | polynomial | — | — | EL [2] | 85 |
| Decision complexity, K ⊩_s a:C in ALC | complexity class | PSPACE-complete | — | — | ALC + unfoldable TBox + ABox | 88 |

## Methods & Implementation Details

### Six-step propositional construction *(p.80–81)*
- **Step 1.** Translate T into B′ = B ∪ {¬C |~ ⊥ | C ∈ T}; treat the agent as ⟨∅, B′⟩. Justification: "C is valid" is equivalent to "¬C is an absurdity (¬C |~ ⊥)" (Bochman [6], Section 6.5).
- **Step 2.** Materialise: Γ_B′ = {C → D | C|~D ∈ B′}; antecedents A_B′ = {C | C|~D ∈ B′}.
- **Step 3.** Exceptionality ranking.
  - **3.1.** C is exceptional for set of sequents D iff Γ_D ⊨ ¬C (this is the only place ⊨ is used). Equivalently, Lehmann–Magidor's ⊤|~¬C ∈ P(D) reduces to Γ_D ⊨ ¬C ([28], Corollary 5.22).
  - **3.2.** E(A_D) = {C ∈ A_D | Γ_D ⊨ ¬C}; E(D) = {C|~D ∈ D | C ∈ E(A_D)}; obviously E(D) ⊆ D.
  - **3.3.** Iterate E_0 = B′, E_{i+1} = E(E_i). Since B′ is finite, terminates with E_n = ∅ or fixed point.
  - **3.4.** Define rank r as in the equation above.
- **Step 4.**
  - **4.1.** B′ is inconsistent iff ⊤|~⊥ ∈ P(B′); checkable via Γ_B′ ⊨ ⊥.
  - **4.2.** T̃ = {¬C | C|~D ∈ B′ and r(C|~D) = ∞}. By footnote 3, this corresponds to *clash* in Bochman [6] (definition p.175, Cor. 7.5.2, Def. 7.5.2, Lemma 7.5.5): the ∞-rank sequents form the greatest clash of B.
  - **4.3.** B̃ = {C|~D ∈ B′ | r(C|~D) < ∞}; B̃ ⊆ B.
- **Step 5.** Construct Δ̃ = {δ_0, ..., δ_n} via Eq. (1). Result: linearly ordered by ⊨ — δ_i ⊨ δ_{i+1}.
- **Step 6.** Associate ⟨T̃, Δ̃⟩.

### One-shot decision recipe (after construction) *(p.81)*
1. Apply transformations once; obtain ⟨T̃, Δ̃⟩.
2. Given premise set Γ and target D, find δ_i = first (Γ ∪ T̃)-consistent formula of ⟨δ_0,...,δ_n⟩ (i.e. T̃ ∪ Γ ⊭ ¬δ_i).
3. Return whether T̃ ∪ Γ ∪ {δ_i} ⊨ D.

The construction step needs at most O(|K|) classical entailment tests *(p.81)*.

### DL construction (concept level) *(p.83–84)*
- **Step 1.** B′ = B ∪ {C ⊓ ¬D |~ ⊥ | C ⊑ D ∈ T}.
- **Step 2.** Γ_B′ = {⊤ ⊑ C → D | C |~ D ∈ B′}; A_B′ = antecedents.
- **Step 3.** Replace "Γ_D ⊨ ¬C" with "Γ_D ⊨ ⊤ ⊑ ¬C" in Steps 3.1–3.4; otherwise identical to propositional.
- **Step 4.** T̃ = {⊤ ⊑ ¬C | r = ∞}; B̃ = {C|~D ∈ B′ | r < ∞}.
- **Step 5.** Δ̃ defined by δ_i = ⊓{C → D | C|~D ∈ B̃ and r(C|~D) ≥ i}.
- Closure validates K: if C ⊑ E ∈ T then C ⊓ ¬E |~ ⊥; if C |~ E ∈ B then C |~ E *(p.84)*.

### Individual-level closure (ABox / unfoldable TBox) *(p.86–87)*
Preconditions:
- ⟨A, T⟩ is consistent: ⟨A, T⟩ ⊭ a:⊥ for any a.
- T is *unfoldable*: (i) axioms are A ⊑ C or A = C with A a concept name; (ii) at most one axiom per concept-name LHS; (iii) acyclic (footnote 7: "depends on" is the transitive closure of "directly depends on", where A directly depends on B if there is an axiom with A on LHS and B on RHS).
- Unfoldable T can be eliminated by: replacing A ⊑ C ∈ T with A = C ⊓ A′ for fresh A′; recursively unfolding concept names; dropping T.
- A in NNF (footnote 8: ¬∀R.C ≡ ∃R.¬C).
- A closed under completion rules: (i) a:C⊓D → a:C, a:D; (ii) a:∃R.C → introduce b with (a,b):R, b:C; (iii) a:∀R.C and (a,b):R → b:C.

Linear-order procedure (p.87):
1. Fix linear order s = ⟨a_1, ..., a_m⟩ of O_A.
2. For each a_j in order, find the first default δ_i s.t. A ∪ {a_j:δ_i} is consistent.
3. Add a_j:δ_i to A; continue.

K ⊩_s a:C iff K̃ ⊨ a:C, where K̃ is the default-assumption extension generated from order s.

Strict defeasible consequence: K ⊩ a:C iff K ⊩_s a:C for every linear order s. May not be rational, except in the unique-extension case where it is *(p.88)*.

### Why multiple extensions appear *(p.85–86)*
Roles transmit information between individuals. Example 6: K = ⟨{(a,b):R}, ∅, {A ⊓ ∀R.¬A}⟩ has two extensions depending on whether default is applied to a or b first; without role-connections each individual would be local and the extension would be unique.

### Edge cases
- Empty B → trivial; B̃ = ∅; δ-sequence empty.
- Inconsistent B′ (Step 4.1) detected via Γ_B′ ⊨ ⊥; in propositional inconsistency derives ⊤|~⊥ and via RW+CM any other sequent.
- δ_n is the conjunction of *all* finite-rank materialisations; δ_0 ⊨ δ_1 ⊨ ... ⊨ δ_n.

### Rational consequence axioms (rules satisfied) *(p.78, p.84)*
- (REF) C |~ C
- (LLE) (C |~ F, ⊨ C ↔ D) / (D |~ F)
- (RW) (C |~ D, D ⊨ F) / (C |~ F)
- (CT) (C |~ D, C ∧ D |~ F) / (C |~ F)
- (CM) (C |~ D, C |~ F) / (C ∧ D |~ F)
- (OR) (C |~ F, D |~ F) / (C ∨ D |~ F)
- (RM) (C |~ F, C |̸~ ¬D) / (C ∧ D |~ F) — Rational Monotony
- DL versions REF_DL ... RM_DL replace ∧ by ⊓, ∨ by ⊔, parameterised by ⟨A, Δ⟩ *(p.87)*.

## Figures of Interest
*(No figures; the paper contains inference-rule diagrams on p.78 (REF, CT, CM, LLE, RW, OR, RM) and p.84 (DL-typed versions), and a rule diagram for the individual-level relation ⊩_s on p.87 (REF_DL, LLE_DL, RW_DL, CT_DL, CM_DL, OR_DL, RM_DL).)*

## Results Summary
- The default-assumption pair ⟨T̃, Δ̃⟩ characterises rational closure exactly (Proposition 1, p.81); this is "an analogous of Freund's [19], Theorem 24" extended with a non-empty background theory using machinery from Bochman [6] *(p.80)*.
- Because the default formulae are linearly ordered by classical implication, *exactly one* (Γ ∪ T̃)-maxiconsistent subset of Δ̃ exists for any Γ — represented by some δ_i, with all δ_j for j ≥ i implied (Proposition 2, p.81).
- For ALC, the same construction produces a rational consequence relation validating K (Proposition 4, p.84).
- Individual-level relation ⊩_s satisfies REF_DL through RM_DL (Proposition 6, p.87); it is determined by linear orders, every default-assumption extension corresponds to some linear order, and vice versa (Proposition 5, p.87).
- Non-monotonic reasoning here adds *no* asymptotic complexity over the underlying entailment problem.

## Limitations
- The TBox needs to be *unfoldable* for the individual-level (ABox) procedure (definition on p.86); arbitrary GCIs are not directly handled at the individual level *(p.86)*.
- ABox-level multiple extensions must be resolved by an externally chosen linear order s; "strict" defeasible consequence (intersection over all orders) may fail to be rational in general *(p.88)*.
- The order s denotes a *priority on the individuals on which to focus the attention*, not a typicality ordering — explicitly contrasted with [11, 23] where the order indicates one individual is more typical than another *(p.88)*.
- Authors only conjecture (do not prove) a representation result connecting their default-assumption consequence with semantical models having a modular (reflexive, transitive, complete) typicality relation defined over individuals *(p.88)*.
- Method has been transposed to ALC; extension to more expressive DLs is left as future work *(p.88)*.

## Arguments Against Prior Work
- "[T]o the best of our knowledge, none of [the prior NM-DL extensions] address specifically the issue to model rational closure in DLs" — applies to refs [1,4,5,7,8,9,10,11,12,13,14,15,17,18,21,22,23,24,25,27,31,32,34,35,36] *(p.77)*.
- About [11, 23] (Britz, Heidema, Meyer; Giordano et al. typicality): "both model rational consequence relations, while we refer to a rational consequence relation that is recognised as particularly well-behaved, that is, rational closure" *(p.77)*.
- Lehmann–Magidor's [28] original characterisation of rational closure relies on preferential closure tests (P(B)), which is "generally considered too weak to be satisfactory" as a stopping point and requires more than classical entailment; the authors argue that their reduction to ⊨-only is more amenable to direct DL implementation *(p.79)*.
- About [11, 23] again, in conclusions: their orders denote "an individual is more typical than another", which is a *different* semantic commitment from this paper's "priority on attention" interpretation of the linear order s *(p.88)*.

## Design Rationale
- *Why default-assumption rather than direct rational closure?* So that the construction can be implemented over a black-box ⊨ oracle: classical DL reasoners can be reused *(p.79)*.
- *Why fold T into B′ as ¬C |~ ⊥ (resp. C ⊓ ¬D |~ ⊥)?* This unifies certain knowledge with conditional knowledge in a single ranking step; absurdity of negation captures validity (Bochman, Sec. 6.5) *(p.80)*.
- *Why infinite rank as the boundary?* Sequents with r = ∞ are exactly those that survive every exceptionality round — they are part of the *clash* of B (Bochman, Lemma 7.5.5, footnote 3 p.80) and so represent the genuinely strict residue. Authors verify T ⊆ T̃ *(p.80)*.
- *Why δ_i = ⋀{C → D : r(C|~D) ≥ i}?* This guarantees δ_i ⊨ δ_{i+1} (linear ordering of defaults), which in turn forces the (Γ ∪ T̃)-maxiconsistent subset of Δ̃ to be unique — replacing maxiconsistent-set quantification with single-formula search *(p.81)*.
- *Why the unfoldable-TBox restriction at individual level?* Because in unfoldable TBoxes one can substitute concept-name definitions into A and Δ and then drop T entirely, simplifying default application to individuals *(p.86)*.
- *Why "priority of attention" rather than "typicality" for s?* The authors keep typicality at the *concept* level (rational closure) and only let individuals receive the strongest default consistent at their turn — the order is an *implementation* choice for picking among extensions, not a semantic claim about which individual is more typical *(p.88)*.

## Testable Properties
- For propositional: ⟨T̃, Δ̃⟩ |~ Γ ⇒ D iff Γ |~ D ∈ R(B′) (Lehmann–Magidor rational closure) — Proposition 1 *(p.81)*.
- δ_0 ⊨ δ_1 ⊨ ... ⊨ δ_n always holds for the produced sequence *(p.81)*.
- After construction, deciding Γ |~ D is one classical entailment test against T̃ ∪ Γ ∪ {δ_i} where δ_i is found by a linear scan over n+1 consistency tests — Proposition 2 *(p.81)*.
- Construction stage uses O(|K|) classical entailment tests; whole procedure adds no asymptotic complexity *(p.81)*.
- Rational closure under this construction is coNP-complete in propositional logic and EXPTIME-complete in ALC; tracks the underlying entailment cost *(p.81, p.85)*.
- |~_⟨T̃,Δ̃⟩ on ALC concepts validates K = ⟨T,B⟩: every C ⊑ D ∈ T gives C ⊓ ¬D |~ ⊥, and every C |~ D ∈ B is preserved (Proposition 4) *(p.84)*.
- ⊩_s on ALC ABox satisfies all of REF_DL, LLE_DL, RW_DL, CT_DL, CM_DL, OR_DL, RM_DL (Proposition 6) *(p.87)*.
- Every default-assumption extension corresponds to some linear order on O_A, and every linear order yields one extension (Proposition 5) *(p.87)*.
- "Strict" defeasible consequence ⊩ over all orders may fail RM in general; in the unique-extension case it satisfies REF_DL–RM_DL *(p.88)*.
- Inconsistency check via Γ_B′ ⊨ ⊥ is correct: ⊤|~⊥ ∈ P(B′) iff Γ_B′ ⊨ ⊥ *(p.80)*.

## Relevance to Project
This paper is a primary citation for **rational closure** in propstore's argumentation/defeasibility layer. Concretely:
- The Casini–Straccia construction is the canonical implementation recipe for an *order-of-typicality* over defaults, which connects directly to (a) the ASPIC+ rule-priority bridge (`propstore.aspic_bridge`), (b) the CKR-style justifiable-exception module (`propstore.defeasibility`) that decides `ist(c, p)` applicability, and (c) any future rational-closure render policy in the render layer. The construction's "no extra entailment cost" property aligns with propstore's "lazy until rendering" principle: the ⟨T̃, Δ̃⟩ presentation is computed once and queried with single ⊨ tests, so it sits naturally on top of an immutable claim store without forcing build-time gates.
- The defeasible operator C |~ D is a clean target for the lemon-shaped concept layer's "typically" semantics: a paper-derived defeasible inclusion can be stamped as a CONTEXT_PHI_NODE bridge that, at render time, becomes a Dung defeat at the ASPIC+ boundary if exception conditions fire.
- Complexity inheritance (coNP for propositional, EXPTIME for ALC, polynomial for EL) is a useful boundary fact when picking which DL fragment underlies the propstore concept-typing layer.
- The unfoldable-TBox restriction is a *gap* signal: propstore's concept layer permits arbitrary GCIs, so the ABox-level procedure here only ports as-is to the unfoldable subset of the concept layer — a constraint to flag in `docs/gaps.md` if/when this construction is implemented.

## Open Questions
- [ ] How does the linear-order `s` on individuals interact with propstore's per-claim provenance? Is the "priority of attention" choice a property of the render policy, of the source branch, or of the agent posing the query?
- [ ] Can we lift the unfoldable-TBox restriction by combining this construction with circumscription-style techniques ([8, 9, 25])?
- [ ] Authors' conjectured representation result connecting modular typicality models with default-assumption consequence — is there a published proof attempt? (See [29], [30] follow-ups by Makinson.)
- [ ] How does this construction compose with belief revision (AGM) over Δ̃? Re-running construction after each revision vs. incremental updates is unaddressed.
- [ ] In the multi-extension case (with roles), the "strict" intersection ⊩ may fail RM. What rendering policy is appropriate when we want a single deterministic answer?

## Related Work Worth Reading
- [28] Lehmann, D. & Magidor, M. — "What does a conditional knowledge base entail?" Artif. Intell. 55(1), 1–60 (1992). The original rational closure paper; this paper recovers its construction via Freund.
- [19] Freund, M. — "Preferential reasoning in the perspective of Poole default logic." Artif. Intell. 98(1-2), 209–235 (1998). The default-assumption representation result this paper builds on (Theorem 24).
- [6] Bochman, A. — "A logical theory of nonmonotonic inference and belief change." Springer (2001). Source of the *clash* machinery (Cor. 7.5.2, Def. 7.5.2, Lemma 7.5.5) used to justify Step 4.2.
- [33] Poole, D. — "A logical framework for default reasoning." Artif. Intell. 36(1), 27–47 (1988). The default-assumption framework.
- [26] Kraus, S., Lehmann, D., Magidor, M. — "Nonmonotonic reasoning, preferential models and cumulative logics." Artif. Intell. 44(1-2), 167–207 (1990). KLM properties (REF–OR without RM).
- [30] Makinson, D. — "Bridges from Classical to Nonmonotonic Logic." (2005). Background reference for default-assumption approach.
- [11, 23] Britz, Heidema, Meyer / Giordano et al. — closest related DL work on rational consequence relations, contrasted in this paper.
- [16] Donini, F.M., Massacci, F. — "Exptime tableaux for ALC." (Source of the EXPTIME-complete bound used in Corollary 2.)
- [2] Baader, Brandt, Lutz — "Pushing the EL envelope." (Source of polynomial-time entailment claim for EL.)

## Collection Cross-References

### Already in Collection
- [What does a conditional knowledge base entail?](../Lehmann_1989_DoesConditionalKnowledgeBase/notes.md) — cited as [28]; the Lehmann–Magidor original rational-closure paper that this paper reformulates as a default-assumption construction and ports to ALC.
- [Nonmonotonic Reasoning, Preferential Models and Cumulative Logics](../Kraus_1990_NonmonotonicReasoningPreferentialModels/notes.md) — cited as [26]; KLM properties REF–OR (without RM) used as the rationality benchmark.

### New Leads (Not Yet in Collection)
- Freund (1998) "Preferential reasoning in the perspective of Poole default logic" — cited as [19]; Theorem 24 is the default-assumption representation this paper builds on.
- Bochman (2001) "A logical theory of nonmonotonic inference and belief change" — cited as [6]; clash machinery used in Step 4.2.
- Poole (1988) "A logical framework for default reasoning" — cited as [33]; the default-assumption framework.
- Makinson (2005) "Bridges from Classical to Nonmonotonic Logic" — cited as [30]; default-assumption background.
- Britz, Heidema, Meyer / Giordano et al. — cited as [11], [23]; closest prior DL rational-consequence work.

### Cited By (in Collection)
- [Enhancing Context Knowledge Repositories with Justifiable Exceptions](../Bozzato_2018_ContextKnowledgeJustifiableExceptions/notes.md) — cites this paper twice (as [46] and [55]) in its survey of rational-closure-based defeasible DLs, contrasted against the CKR clashing-assumption semantics.
- [A Datalog Translation for Reasoning on DL-Lite_R with Defeasibility](../Bozzato_2020_DatalogDefeasibleDLLite/notes.md) — cites this as [14]; argues that rational closure does not directly provide a materialization-based reasoning procedure, motivating the justifiable-exception alternative.

### Conceptual Links (not citation-based)
**Defeasible DLs / alternative semantics:**
- [What does a conditional knowledge base entail?](../Lehmann_1989_DoesConditionalKnowledgeBase/notes.md) — **Strong.** This paper is a direct algorithmic descendant: replaces Lehmann–Magidor's preferential-closure tests with classical entailment tests and ports the construction to ALC.
- [Algorithmic Definitions for KLM-style Defeasible Disjunctive Datalog](../Morris_2020_DefeasibleDisjunctiveDatalog/notes.md) — **Strong.** Both papers extend propositional rational closure to richer logics (ALC vs Disjunctive Datalog) while preserving LM-rationality. Complementary algorithmic strategies for the same theoretical target.
- [Enhancing Context Knowledge Repositories with Justifiable Exceptions](../Bozzato_2018_ContextKnowledgeJustifiableExceptions/notes.md) — **Strong.** CKR's "justifiable exception" semantics is a direct semantic alternative to this paper's rational closure for defeasible DL inclusions. Both target the same problem (T-axioms that should fail on exceptional individuals); rational closure does it via concept-level exceptionality ranking, CKR via ABox-level clashing-assumption tests under multiple contexts. Directly relevant to propstore.defeasibility.
- [A Datalog Translation for Reasoning on DL-Lite_R with Defeasibility](../Bozzato_2020_DatalogDefeasibleDLLite/notes.md) — **Strong.** Single-context DL-Lite simplification of CKR; explicitly contrasts itself against this paper's rational closure on the materialization-procedure axis.

**Foundations / argumentation bridges:**
- [The ASPIC+ framework for structured argumentation: a tutorial](../Modgil_2014_ASPICFrameworkStructuredArgumentation/notes.md) — **Moderate.** ASPIC+ is propstore's argumentation surface; the priority-on-defaults that Casini–Straccia derive (the order δ_0 ⊨ δ_1 ⊨ ... ⊨ δ_n) is a candidate principled input to the ASPIC+ rule-priority order for defeasible DL knowledge.
- [On the links between argumentation-based reasoning and nonmonotonic reasoning](../Li_2016_LinksBetweenArgumentation-basedReasoningNonmonotonicReasoning/notes.md) — **Strong.** Li 2016 analyses ASPIC+ through the same KLM/Lehmann–Magidor axioms (REF, LLE, RW, CT, CM, OR, RM) Casini–Straccia validate at the DL level. Direct bridge for verifying whether an ASPIC+-typed rational closure preserves the rationality postulates.
- [An abstract, argumentation-theoretic approach to default reasoning](../Bondarenko_1997_AbstractArgumentation-TheoreticApproachDefault/notes.md) — **Moderate.** ABA reframes default reasoning as argumentation; Casini–Straccia's default-assumption set Δ̃ plays a role analogous to ABA's assumptions.
- [A Logic for Default Reasoning](../Reiter_1980_DefaultReasoning/notes.md) — **Moderate.** Reiter defaults are the alternative formalism Casini–Straccia explicitly *don't* use; they choose Poole/default-assumption to align with Freund's representation result.

**Ranking-based / probabilistic-flavoured semantics:**
- [Defeasible Strict Consistency](../Goldszmidt_1992_DefeasibleStrictConsistency/notes.md) — **Strong.** Goldszmidt & Pearl's ε-semantics / System Z gives a probabilistic justification for the same exceptionality ranking Casini–Straccia compute symbolically. Different formalisms converging on the same ranking.
- [Ordinal Conditional Functions: A Dynamic Theory of Epistemic States](../Spohn_1988_OrdinalConditionalFunctionsDynamic/notes.md) — **Moderate.** Spohn's OCFs are the abstract structure underlying both System Z and Casini–Straccia's r(C\|~D); the rank function is essentially a finitary OCF over sequents.

**Belief revision:**
- [Theory Change](../Alchourron_1985_TheoryChange/notes.md) — **Moderate.** AGM postulates capture the dual side of rational closure's "what is presumed when nothing forbids it." The transformation chain ⟨T,B⟩ ⤳ ⟨T̃, Δ̃⟩ is a belief-state reorganisation but is not connected to AGM dynamics in this paper — open question for propstore.belief_set.
