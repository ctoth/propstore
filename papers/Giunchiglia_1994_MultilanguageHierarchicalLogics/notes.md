---
title: "Multilanguage hierarchical logics, or: how we can do without modal logics"
authors: "Fausto Giunchiglia, Luciano Serafini"
year: 1994
venue: "Artificial Intelligence"
doi_url: "https://doi.org/10.1016/0004-3702(94)90037-X"
pages: "29-70"
affiliations: "Mechanized Reasoning Group, IRST, Trento, Italy; DIST, University of Genoa, Italy"
note: "Received June 1991; Revised November 1992. Preliminary version: Canadian Society for Computational Studies of Intelligence, Vancouver, BC, 1992."
---

# Multilanguage hierarchical logics, or: how we can do without modal logics

## One-Sentence Summary
Introduces MultiLanguage (ML) systems — formal systems with a hierarchy of distinct first-order languages linked by bridge rules of reflection up/down — and proves that several common modal logics (K, T, S4, S5) embed into corresponding ML systems, while the ML systems carry additional intuitively-justified properties (locality, non-global inconsistency, distinct languages per view) that modal logics cannot express because they collapse all "worlds" into a single language. *(p.29-30)*

## Problem Addressed
Modal logics use a single language with a modal operator to talk about provability, belief, or other propositional attitudes. Collapsing all reasoning into one language loses the distinction between provability and belief [ref 30 Konolige], prevents formalizing distinct views with distinct languages, and forces global propagation of inconsistency. The paper asks: can we *add structure to the logic* (hierarchies of languages with bridge rules) instead of *extending the language* (modal operators), and thereby obtain systems that match implementation practice (GETFOL, OYSTER/CLAM, ViewGen) and intuitions about contextual reasoning? *(p.30-32)*

## Key Contributions
- Defines ML systems generally and the subclass $\mathcal{MR}$ whose members are hierarchical metalogics connected only by reflection-up/reflection-down bridge rules. *(p.32-36)*
- Introduces MK (ascending chain, for provability/metatheory) and MBK (descending chain, for belief/propositional attitudes), both $\mathcal{MR}$ systems equivalent to modal K via a syntactic mapping. *(p.37, 42-43)*
- Proves the main equivalence: `A+ ⊢K` iff `∃i. ⟨A,i⟩ ⊢MK` (Theorem 5.1) and similarly for MBK (Cor C.1). *(p.55, 66)*
- Proves **localization of inconsistency**: in MK, `Γ ⊢MK ⟨⊥,i⟩` only propagates *down* to theories with index ≤ i, not up (Theorem 5.3). Inconsistency cannot be added finitely without leaving some theory consistent (Theorem 5.4, Cor 5.5). These properties fail in modal K. *(p.55-57)*
- Proves the "assumption-as-axiom" theorem: any ML system MS based on MK is equivalent to MK augmented with "lifted" axioms of the form `⟨Th^{i0-j}("B"), i0⟩` (Theorem 6.2). *(p.58)*
- Extends equivalence to T, S4, S5, both axiom-style (MT/MS4/MS5) and bridge-rule-style (MT'/MS4'/MS5') formulations, and proves their equivalence (Theorems 6.4 and 6.6). *(p.59-61)*
- Observes that localization of consistency (Theorem 5.4, Cor 5.5) does *not* generalize to MT/MS4/MS5 because the T axiom (or bridge rule) propagates inconsistency upward. *(p.62)*

## Study Design
*Not applicable — purely theoretical paper (proof-theoretic definitions, theorems with proof sketches).*

## Methodology
- Natural deduction in Prawitz [37] style, extended with language-indexed formulas `⟨A, i⟩` read "A is an Li-wff". *(p.32-33)*
- Two kinds of inference rules: *i-rules* (premises and conclusion share language index i) and *bridge rules* (premises/conclusions span different indices). i-rules reason within a theory; bridge rules export results between theories. *(p.33)*
- Deductions graphically represented as labeled boxes: box `i` encloses an i-only subdeduction; stacked boxes connected by bridge rules. *(p.35)*
- Syntactic mapping `(·)*` from modal wffs to Li-wffs: propositional constants unchanged, distributes over connectives, `(□A)* = Th("A*")`. Inverse `(·)+`. `depth(A)` = nesting of □/Th. *(p.47)*
- Equivalence proofs via two operators transforming deductions: `(·)^{*,i}` maps K-deduction into MK-deduction at level i (Lemma 4.1); `(·)^{+,i}` maps MK-deduction into K-deduction with n boxes for level-n wffs (Lemma 4.3). *(p.49, 53-54)*
- Sublevel (weak subformula) property of MK (Theorem A.1): any `Γ ⊢MK ⟨A,i⟩` has a deduction with all occurrences at index ≤ max-index of Γ ∪ {⟨A,i⟩}. Proved via an operator `(·)^{(-1)}` that flattens overflowing formulas. *(p.55, 63-64)*

## Key Equations / Statistical Models

Inference rules without discharging assumptions:
$$
\frac{\langle A_1, i_1\rangle \;\ldots\; \langle A_n, i_n\rangle}{\langle A, i\rangle}\,\iota
$$
Where: labeled formulas have `⟨Ak, ik⟩` meaning `Ak` is an `L_{ik}`-wff. *(p.33, eq 1)*

Inference rules discharging assumptions `[⟨Bk, jk⟩]`:
$$
\frac{\langle A_1, i_1\rangle \;\ldots\; \langle A_n, i_n\rangle \quad \frac{[\langle B_1, j_1\rangle]}{\langle A_{n+1}, i_{n+1}\rangle} \;\ldots\; \frac{[\langle B_m, j_m\rangle]}{\langle A_{n+m}, i_{n+m}\rangle}}{\langle A, i\rangle}\,\delta
$$
Where: rule `δ` discharges `⟨B1, j1⟩, …, ⟨Bm, jm⟩`. *(p.33, eq 2)*

Reflection up and reflection down bridge rules (for MR-class, unary predicate `•`):
$$
\frac{\langle A, O\rangle}{\langle \bullet(\text{``}A\text{''}), M\rangle}\,\mathcal{R}_{up.} \qquad \frac{\langle \bullet(\text{``}A\text{''}), M\rangle}{\langle A, O\rangle}\,\mathcal{R}_{dn.}
$$
Where: `O` is object-theory index, `M` is metatheory index, `•` is a unary predicate (e.g. `Th` for provability, `Bl` for belief). *(p.36, eq 4)*

MR-system theoremhood correspondence (object/meta link):
$$
\vdash_{MR} \langle A, O\rangle \iff \vdash_{MR} \langle \bullet(\text{``}A\text{''}), M\rangle
$$
*(p.36, eq 5)*

MR-system closure under implication in metatheory:
$$
\vdash_{MR} \langle \bullet(\text{``}A \supset B\text{''}) \supset (\bullet(\text{``}A\text{''}) \supset \bullet(\text{``}B\text{''})), M\rangle
$$
*(p.36, eq 6)*

MK's indexed R_up and R_dn (with R_up restriction: undischarged-assumption index strictly > i):
$$
\frac{\langle A, i\rangle}{\langle Th(\text{``}A\text{''}), i+1\rangle}\,\mathcal{R}_{up.i} \qquad \frac{\langle Th(\text{``}A\text{''}), i+1\rangle}{\langle A, i\rangle}\,\mathcal{R}_{dn.i}
$$
*(p.38)*

MBK's R_up / R_dn (with R_up restriction: undischarged-assumption index ≤ i — *opposite direction to MK*):
$$
\frac{\langle A, i+1\rangle}{\langle Bl(\text{``}A\text{''}), i\rangle}\,\mathcal{R}_{up.i} \qquad \frac{\langle Bl(\text{``}A\text{''}), i\rangle}{\langle A, i+1\rangle}\,\mathcal{R}_{dn.i}
$$
*(p.43)*

Modal-to-first-order mapping `(·)*`:
$$
(A)^* = A \text{ if } A \text{ is a propositional constant};\quad (\cdot)^* \text{ distributes over connectives};\quad (\Box A)^* = Th(\text{``}A^*\text{''})
$$
*(p.47)*

Iterated Th predicate:
$$
Th^n(\text{``}A\text{''}) = \begin{cases} A, & n = 0 \\ Th(\text{``}Th^{n-1}(\text{``}A\text{''})\text{''}), & \text{otherwise} \end{cases}
$$
*(p.47)*

Derived MK rules from K rules (eqs 7-13, p.48) — schematic at level `i+n` mirroring modal K's `□^n`-prefixed rules:
$$
\frac{\langle Th^n(\text{``}A\text{''}), i+n\rangle}{\langle A, i\rangle}\,\mathcal{R}_{dn.i}^{n}
$$
*(p.48, eq 7)* (plus analogous ∧E^n, ∧I^n, ⊃E^n, ⊃I^n, ⊥^n — eqs 8-13)

Operator `(·)^{*,i}` (base case for wff translation):
$$
(A)^{\langle *, i\rangle} = \langle A^*, i\rangle
$$
*(p.49)*

Operator `(·)^{+,i}` (inverse base case, defined only for `i ≥ j`):
$$
(\langle A, j\rangle)^{\langle +, i\rangle} = \Box^{i-j} A^+
$$
*(p.51)*

Characteristic axioms for modal extensions:
$$
T_{i+1} = \langle Th(\text{``}A\text{''}) \supset A, i+1\rangle
$$
$$
S4_{i+2} = \langle Th(\text{``}A\text{''}) \supset Th(\text{``}Th(\text{``}A\text{''})\text{''}), i+2\rangle
$$
$$
S5_{i+2} = \langle \neg Th(\text{``}A\text{''}) \supset Th(\text{``}\neg Th(\text{``}A\text{''})\text{''}), i+2\rangle
$$
*(p.59, Def 6.3)*

Alternative bridge-rule formulation for extensions (Def 6.5):
$$
\frac{\langle A, i\rangle}{\langle A, i+1\rangle}\,\mathcal{T}_i \qquad \frac{\langle Th(\text{``}A\text{''}), i+1\rangle}{\langle Th(\text{``}A\text{''}), i\rangle}\,\mathcal{S}4_i \qquad \frac{\langle \neg Th(\text{``}A\text{''}), i+1\rangle}{\langle \neg Th(\text{``}A\text{''}), i\rangle}\,\mathcal{S}5_i
$$
*(p.60)*

MBK versions of characteristic axioms (Def C.8):
$$
T_i = \langle Bl(\text{``}A\text{''}) \supset A, i\rangle
$$
$$
S4_i = \langle Bl(\text{``}A\text{''}) \supset Bl(\text{``}Bl(\text{``}A\text{''})\text{''}), i\rangle
$$
$$
S5_i = \langle \neg Bl(\text{``}A\text{''}) \supset Bl(\text{``}\neg Bl(\text{``}A\text{''})\text{''}), i\rangle
$$
*(p.66)*

Operator `(·)^{(-1)}` on wffs (Appendix A):
$$
p^{(-1)} = p \text{ (propositional constant)};\quad \text{distributes over connectives};\quad Th(\text{``}A\text{''})^{(-1)} = A
$$
*(p.64)*

Operator `(·)^{(MBK, i)}` (Appendix B) — maps MK deduction to MBK deduction by substituting `Bl` for `Th` and reversing indices: each occurrence `⟨A, i⟩` becomes `⟨A[Th/Bl], i0 − i⟩` where `i0` is greatest index in the deduction. *(p.65)*

## Parameters

Not a parameterized system in the empirical/algorithmic sense. The "parameters" are structural choices when instantiating an ML system:

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Language index set | I | — | ω (naturals) | any set | p.32 | For MK, MBK, MT/S4/S5: I = ω |
| Family of languages | {Li}i∈I | — | — | — | p.32 | MK: Li has names for Li-1; MBK: all Li = L(Bl) |
| Family of axiom sets | {Ωi}i∈I | — | ∅ for all i | — | p.37, p.43 | MK/MBK: all Ωi = ∅; modal extensions: axiom schemas per level |
| Reflection-up restriction (MK) | — | — | strictly > i | — | p.38 | Index of every undischarged assumption must be strictly > i |
| Reflection-up restriction (MBK) | — | — | ≤ i | — | p.43 | Opposite direction: assumptions have lower-or-equal index |
| Characteristic axiom schema | T / S4 / S5 | — | none (= MK/MBK) | T / S4 / S5 | p.59, p.66 | Parameterizes the specific modal system |
| Depth of modal wff | depth(A) | — | — | ℕ | p.47 | Greatest nesting of □ / Th; determines minimum index i where A* is Li-wff |

## Effect Sizes / Key Quantitative Results

*Not applicable — theoretical paper. Main quantitative "result" is the bijective-mapping preservation of derivability between K and MK (Theorem 5.1).*

## Rules / Algorithms / Theorems

**Definition 2.1 (ML system) — p.32.** Triple `MS = ⟨{Li}i∈I, {Ωi}i∈I, Δ⟩`. Family of languages, family of axiom sets per language, one set of deductive rules Δ.

**Definition 3.1 (MK) — p.37-38.** Propositional language L, Li inductively built (i..v) including `Th("A") is L_{i+1}-wff if A is Li-wff`. Ωi = ∅. Δ contains per-level classical ND rules (∧I, ∧E, ∨I, ∨E, ⊃I, ⊃E, ⊥) plus R_up.i / R_dn.i. Restrictions: R_up.i requires all undischarged assumption indices strictly > i; ⊥i requires A not of form B⊃⊥.

**Proposition 3.2 — p.38.** MK proves the K-axiom analog and K's theorems: `⟨Th("A⊃B")⊃(Th("A")⊃Th("B")), i+1⟩`, `⟨Th("⊥")⊃Th("A"), i+1⟩`, `⟨¬Th("⊥")⊃(Th("A")⊃¬Th("¬A")), i+1⟩`.

**Definition 3.3 (MBK) — p.43.** Languages all equal to `L(Bl)` (closed under `Bl("A")` at same level). Same rule set as MK with `Bl` in place of `Th` and with the R_up restriction reversed.

**Proposition 3.4 — p.44.** MBK analogs of the three K-like theorems hold at each level i.

**Lemma 4.1 — p.49-50.** If Π is a K-deduction of A from A0,…,Am, ∃ i0 such that ∀ i ≥ i0, `Π^{*,i}` is an MK-deduction of ⟨A*, i⟩ from ⟨A0*, i⟩,…,⟨Am*, i⟩.

**Lemma 4.2 — p.51.** If `Γ ⊢MK ⟨A,i⟩`, there exists a deduction Π of ⟨A,i⟩ from Γ in which every occurrence above a ⊃Ii or ⊥i has index ≤ i. (Reduction steps 14, 15.)

**Lemma 4.3 — p.53.** If `⟨A1,i1⟩,…,⟨An,in⟩ ⊢MK ⟨A,i⟩` with i0 = maximum index in the MK-deduction Π, then `Π^{+,i0}` is a K-deduction of `□^{i0-i} A+` from `□^{i0-i1} A1+, …, □^{i0-in} An+`.

**Theorem 5.1 (Main equivalence K ↔ MK) — p.55.** `A1+,…,An+ ⊢K A+` iff `∃i. ⟨A1,i⟩,…,⟨An,i⟩ ⊢MK ⟨A,i⟩`.

**Corollary 5.2 (Consistency of MK) — p.55.** For every `i ∈ ω`, `⟨⊥, i⟩` is not a theorem of MK.

**Theorem 5.3 (Downward inconsistency propagation) — p.55.** If `Γ ⊢MK ⟨⊥, i⟩`, then `Γ ⊢MK ⟨⊥, j⟩` for any `j ≤ i`. The *converse fails* — inconsistency does not propagate upward. **Local inconsistency does not imply global inconsistency.** *(p.56)*

**Theorem 5.4 — p.56.** For every finite set Γ, there exists a wff `⟨A,i⟩` such that `Γ ⊬MK ⟨A,i⟩`. (Finite assumption set cannot render MK globally inconsistent.)

**Corollary 5.5 — p.56.** `⟨⊥, i⟩ ⊬MK ⟨⊥, i+1⟩`. Even adding `⟨⊥, i⟩` as an axiom leaves theory i+1 consistent.

**Theorem 5.6 (Simulation / "metatheory simulates object theory") — p.57.** `⟨A1,i⟩,…,⟨An,i⟩ ⊢MK ⟨A,i⟩` iff `⟨Th("A1"), i+1⟩,…,⟨Th("An"), i+1⟩ ⊢MK ⟨Th("A"), i+1⟩`.

**Definition 6.1 (based-on) — p.58.** MS' based on MS iff same languages, same Δ, and `Ωi ⊆ Ω'i` for all i. Elements of `Ω'i \ Ωi` are characteristic axioms.

**Theorem 6.2 (assumptions-as-lifted-axioms) — p.58.** If `Γ ⊢MS ⟨A,i⟩` with MS based on MK, characteristic axioms Ω used in the proof Π, and i0 = greatest index in Π, then `Γ, Ω' ⊢MK ⟨A,i⟩` where Ω' is the minimal set such that for each `⟨B,j⟩ ∈ Ω`, `⟨Th^{i0-j}("B"), i0⟩ ∈ Ω'`.

**Definition 6.3 — p.59.** T_{i+1}, S4_{i+2}, S5_{i+2} characteristic axioms (see equations above).

**Theorem 6.4 (K↔MT, S4↔MS4, S5↔MS5 equivalence) — p.59-60.** `⊢X A+` iff `∃i. ⊢MX ⟨A,i⟩` where X ∈ {T, S4, S5}.

**Definition 6.5 — p.60.** Alternative bridge-rule formulation `T_i, S4_i, S5_i` (see equations).

**Theorem 6.6 — p.60.** `Γ ⊢MX ⟨A,i⟩` iff `Γ ⊢MX' ⟨A,i⟩`.

**Corollary 6.7 — p.62.** `⟨⊥,i⟩` is not a theorem of any of MT, MS4, MS5, MT', MS4', MS5'. Local-inconsistency results do NOT generalize — these systems propagate ⊥ upward.

**Theorem A.1 (Sublevel / weak subformula property) — p.64.** If `Γ ⊢MK ⟨A,i⟩`, there exists a deduction of `⟨A,i⟩` from Γ with no overflowing formulas (formulas at index > max-index of Γ ∪ {⟨A,i⟩}).

**Corollary A.2 — p.64.** If `⊢MK ⟨A,i⟩`, there exists a proof with all wffs at index ≤ i.

**Theorem B.1 (MK ↔ MBK deduction translation) — p.65.** If Π is MK-deduction of `⟨A,i⟩` from Γ with i0 = greatest index in Π, then `Π^{(MBK, i0)}` is MBK-deduction of `⟨A[Th/Bl], i0 − i⟩` from Γ'.

**Corollaries B.2, B.3 — p.65.** `⊢MK ⟨A,i⟩` iff `∃j. ⊢MBK ⟨A[Th/Bl], j⟩`; equivalently iff `⊢MBK ⟨A[Th/Bl], 0⟩`.

**Corollary C.1 (MBK version of Theorem 5.1) — p.66.** `A1+,…,An+ ⊢K A+` iff `∃i. ⟨A1,i⟩,…,⟨An,i⟩ ⊢MBK ⟨A,i⟩`. By sublevel, can take i=0 (agent's top theory).

**Corollaries C.3, C.4, C.5, C.6, C.7 — p.66.** MBK versions of 5.2, 5.3 (*indexes flipped*: `j ≥ i`), 5.5, 5.6, 6.2. **Theorem 5.4 analog fails** for MBK: MBK has a top theory (0), so assuming ⊥ at the top makes everything inconsistent.

## Figures of Interest
- **Fig 1 (p.34):** The ML system ML3 — three nodes (0, 1, 2) with bridge rules B1 (from 1 to 0) and B2 (from 2 to 0). Example of a fan-in three-agent system where Mr.0 trusts Mr.1 and Mr.2.
- **Fig 2 (p.36):** The family $\mathcal{MR}$ — two nodes O (below) and M (above), with R_up pointing up and R_dn pointing down, exchanging `•("A")` (in M) and `A` (in O).
- **Fig 3 (p.38):** MK as an infinitely ascending chain of theories 0, 1, 2, …; reflection rules labeled `R_up.i` / `R_dn.i` between adjacent levels.
- **Fig 4 (p.44):** MBK as an infinitely descending chain with top theory 0 and levels 1, 2, …, all having same expressive power (each allows nested `Bl`).
- **Fig 5 (p.46):** Multi-agent MBK — top theory ε branches to n agent theories (labeled by agent index), each branching again into n theories for each level-of-nesting, growing as a tree in both depth and breadth.

## Results Summary
- Every modal K, T, S4, S5 theorem corresponds to an ML-system theorem at some level i, and vice versa (Theorems 5.1, 6.4).
- MK has the sublevel property (weak subformula, Theorem A.1), giving a Prawitz-style consistency argument (Cor 5.2).
- MK has localization of inconsistency: local ⊥ doesn't propagate upward (Theorem 5.3 + fact that converse fails); no finite Γ makes all of MK inconsistent (Theorem 5.4, Cor 5.5). Modal K has none of these.
- MBK is equivalent to K under the same syntactic map but is essentially different in structure (descending vs ascending; same-expressive-power languages vs different-expressive-power languages). MBK has a top theory and therefore *loses* Theorem 5.4, but retains Cor 5.5 equivalent.
- Modal systems T, S4, S5 are obtained by adding either axioms (MT/MS4/MS5) or bridge rules (MT'/MS4'/MS5') to MK, and the two formulations prove the same theorems (Theorem 6.6).
- Localization of consistency does NOT generalize to MT-family systems (Cor 6.7 applies only to consistency-at-each-level, not to localization).

## Methods & Implementation Details
- Languages indexed by natural numbers (ω). Indices are *metanotation*, not part of the language — they track locality of reasoning. *(p.33)*
- Contrast with Labeled Deductive Systems (Gabbay [10]): LDS has labels as part of the formula and allows label-conditions in rules; ML labels carry only locality info and rules apply only to formulas. *(p.33)*
- Deductions graphically rendered as nested/stacked boxes labeled with theory indices; bridge rules connect boxes. *(p.35)*
- GETFOL system [12] implements arbitrary ML systems with arbitrary bridge rules — total reimplementation of FOL [23, 45, 44]. Results of this paper show mechanized multicontextual reasoning in GETFOL is consistent and as expressive as modal logic. *(p.31)*
- OYSTER/CLAM [28, 42] — theorem prover with declarative metalevel in distinct language from object. *(p.31)*
- ViewGen [47, 49] — distinct signatures per belief set. *(p.31)*
- Modal K axiomatized natural-deduction style per Bull & Segerberg [2], extended with `□^n`-prefixed rule schemas. *(p.47-48)*
- Proof strategy for main equivalence: build operators `(·)^{*,i}` (K → MK) and `(·)^{+,i}` (MK → K), prove structural induction lemmas (4.1, 4.3), invoke sublevel property for ⇐ direction of Theorem 5.1.

## Limitations
- Proofs are "only hinted" in the paper; full technical proofs in Tech Report [15] (Hierarchical meta-logics: some proof theoretic results, Trento 1993). *(p.32)*
- MK is propositional; metatheoretic theorem proving is typically first-order. First-order extensions require adding metalevel axioms for syntax and extended languages. *(p.41)*
- Authors explicitly do not consider applications where metatheoretic reasoning is studied *per se* (induction, reflection axioms, admissibility proofs); these need stronger metatheory than MK allows. *(p.40, footnote 2)*
- Extension to modal systems beyond T/S4/S5 is nontrivial: Theorem 6.4's (⇐) direction exploits `⊢X □A ⇒ ⊢X A` (the T axiom's effect); modal systems without this property need separate treatment. *(p.62)*
- Semantics not given in the paper — "out of the goal of this paper"; see [17] for MK semantics (intuition: theories are partial descriptions of the *unique* world, not possible-worlds Kripke structures). *(p.47)*
- MBK has a top theory, so the localization-of-inconsistency property (Theorem 5.4) fails for MBK — an inconsistent believer at level 0 makes all levels inconsistent. *(p.57)*
- Localization of consistency does not generalize to MT/MS4/MS5 families. *(p.62)*

## Arguments Against Prior Work
- **Modal logics (general):** collapse multiple views into a single language, losing distinction between provability and belief (Konolige [30] modeled belief as provability — the authors argue this is a symptom of the single-language limitation). *(p.46)*
- **Tarski [39]:** hierarchical metatheories but metatheories not formalized and no bridge rules — prevents proof-theoretic study of multi-theory interaction. *(p.41)*
- **First-order treatments of modality (Thomason [41], Montague [35], Des Rivieres & Levesque [5]):** face paradoxes; paper cites these as motivation but argues its results are "very different" from [5]. *(p.30)*
- **Perlis [36]:** argued against multiple hierarchical theories on quantification grounds. Authors defend: in the propositional case Perlis's objection doesn't apply; even in first-order, one need not quantify over theories unless that is the desired reasoning. *(p.45)*
- **Labeled Deductive Systems (Gabbay [10]):** superficially similar (labeled formulas) but different in intent — LDS labels track derivation metadata (step count, possible world); ML indices track locality of reasoning. LDS rules take metalevel premises (label conditions); ML rules only formulas. *(p.33)*
- **Provability logics (Boolos [1], Smorynski [38]):** different in goal; some similarity would arise if ML systems were applied to PA, PRA-style theories. *(p.42)*

## Design Rationale
- **Multiple languages over single-language + operator:** provides flexibility to have distinct signatures per view, matches practice (ViewGen, OYSTER/CLAM), allows deductions spanning different languages (assumptions and conclusions in distinct languages). *(p.31-32, p.45)*
- **Indices as metanotation, not part of language:** preserves locality as a proof-theoretic property; keeps the language clean and the rules applicable only to formulas. *(p.33)*
- **Bridge rules (reflection up/down):** weakest conditions guaranteeing the object/meta relation between two theories. *(p.36, eq 5-6)*
- **Same inference rules at every level:** ensures any theory i is complete for classical propositional logic (proves all tautologies) and permits uniform shifting of deductions through layers. *(p.38, p.50)*
- **R_up restriction differs between MK and MBK:** MK requires undischarged-assumption indices strictly > i (prevents importing local-theory assumptions into metatheory); MBK requires ≤ i (different locality intuition: the agent's beliefs are at the bottom, views expand above). *(p.38 vs p.43)*
- **MK vs MBK: ascending vs descending chain:** motivated by intuitions. Metatheory for provability is "above and more powerful" (ascending). Belief structure is "the agent is above, his views of himself are below" (descending, same expressive power because arbitrary nesting must be possible). *(p.45-46)*
- **Axiom formulation vs bridge-rule formulation (Def 6.3 vs 6.5):** two equivalent ways to obtain MT/MS4/MS5. Bridge-rule version is "more elegant" and suggests research direction: "many reasoning phenomena can be modeled simply by controlling the propagation of consequences among theories." *(p.61-62)*

## Testable Properties
- `⊢K A+` iff `∃i. ⊢MK ⟨A, i⟩`. *(p.55, Theorem 5.1)*
- For every `i ∈ ω`, `⟨⊥, i⟩` is not provable in MK. *(p.55, Cor 5.2)*
- If `Γ ⊢MK ⟨⊥, i⟩` then `Γ ⊢MK ⟨⊥, j⟩` for every `j ≤ i`. *(p.55, Theorem 5.3)*
- `⟨⊥, i⟩ ⊬MK ⟨⊥, i+1⟩`. *(p.56, Cor 5.5)*
- For any finite Γ, ∃ ⟨A,i⟩ such that `Γ ⊬MK ⟨A,i⟩`. *(p.56, Theorem 5.4)*
- `⟨A1,i⟩,…,⟨An,i⟩ ⊢MK ⟨A,i⟩` iff `⟨Th("A1"),i+1⟩,…,⟨Th("An"),i+1⟩ ⊢MK ⟨Th("A"),i+1⟩`. *(p.57, Theorem 5.6)*
- `⊢X A+` iff `∃i. ⊢MX ⟨A,i⟩` for X ∈ {T, S4, S5}. *(p.59-60, Theorem 6.4)*
- `Γ ⊢MX ⟨A,i⟩` iff `Γ ⊢MX' ⟨A,i⟩`. *(p.60, Theorem 6.6)*
- `⟨⊥,i⟩` not provable in MT/MS4/MS5/MT'/MS4'/MS5'. *(p.62, Cor 6.7)*
- Sublevel property: every `Γ ⊢MK ⟨A,i⟩` has a deduction with max index ≤ max(indices in Γ ∪ {⟨A,i⟩}). *(p.64, Theorem A.1)*
- `⊢MK ⟨A,i⟩` iff `⊢MBK ⟨A[Th/Bl], 0⟩`. *(p.65, Cor B.3)*

## Relevance to Project

**Directly central** to propstore's context/semantic layer. The paper provides the computational companion to McCarthy's `ist(c, p)` by formalizing:

1. **Contexts as theories with distinct languages:** propstore's `contexts/` can be viewed as MK-style theories, each with its own form/concept vocabulary. A claim `⟨A, c⟩` in propstore corresponds naturally to a labeled formula `⟨A, c⟩` in an ML system. *(p.32-33)*
2. **Bridge rules as context morphisms:** reflection up/down (p.36, eq 4) is exactly the primitive the project needs for "this claim holds in context c1 iff its named form holds in the view c2 about c1". Claims can be exported/imported across contexts via named bridge rules rather than merging into a single global theory.
3. **Non-commitment at the semantic core (from project CLAUDE.md):** Theorem 5.3 and Theorem 5.4 are the formal foundation of the project's "don't collapse disagreement in storage" principle. *Local inconsistency does not imply global inconsistency* — propstore can hold multiple rival normalizations and competing stances in separate contexts without losing the ability to reason globally. This is exactly the Giunchiglia-Serafini property MK has but modal K doesn't. *(p.55-56)*
4. **Two dual topologies (MK ascending vs MBK descending):** suggests propstore might need *both* topologies depending on use case: one for "theories with increasingly rich metalanguage about a source" (MK) and one for "agents sitting above their own views" (MBK). The same syntactic machinery supports both. *(p.45-46)*
5. **Assumptions-behave-as-axioms (Theorem 6.2):** formal grounding for "working in branch ≡ working with additional axioms" in propstore's branch-isolated storage. When the branch merges back, the added context-axioms need explicit lifting to the merged context. *(p.58)*
6. **Syntactic equivalence suffices for mechanized reasoning:** paper argues that for building mechanized reasoners, syntactic equivalence is all one needs (p.46). Matches propstore's implementation-oriented design.
7. **Explicit rejection of possible-worlds semantics:** "a theory is a partial description of the *unique* world" (p.47) — aligns with propstore's treatment of contexts as *qualifications* on propositions about one world, not as distinct Kripke worlds.

**Practical implications for propstore code:**
- Consider adding a `BridgeRule` primitive (reflection up/down between contexts) alongside existing context relations.
- Locality of inconsistency should be a **testable invariant** on propstore's claim graph: adding an inconsistent claim in context `c` must not be provable from contexts `c'` that don't reach `c`.
- When the argumentation layer builds ASPIC+ arguments, the MK bridge-rule formulation maps onto the assumption-labeled derivations — worth investigating whether `aspic_bridge.py` could reuse the MK index semantics.

## Open Questions
- [ ] How do MK's indices interact with propstore's `ContextWorld` merge semantics (IC merge operators)? Is there a natural mapping from MK-index shifts to IC-merge levels?
- [ ] Can we get "semantic" (model-theoretic) accounts of propstore contexts by adapting [17] (Giunchiglia-Serafini-Simpson local models semantics) rather than possible-worlds?
- [ ] Does propstore's branch / merge machinery give us Theorem 6.2 (assumptions-as-lifted-axioms) for free, or does it need explicit index lifting?
- [ ] For propstore's belief-of-belief structure (multi-agent propositional attitudes), does MBK's tree topology (Fig 5, p.46) provide the right data structure?
- [ ] Are propstore's normalization/reconciliation operations locality-preserving? Does a heuristic proposal at context c affect provability at contexts `c' ≥ c`?

## Related Work Worth Reading
- **[17] Giunchiglia, Serafini, Simpson — Hierarchical meta-logics: intuitions, proof theory and semantics** (1992). Detailed MK semantics. Cited as the followup with the model-theoretic story. **Already in our collection as Giunchiglia_1992_HierarchicalMeta-logics — see `papers/Giunchiglia_1992_HierarchicalMeta-logics/`.** Critical for the semantics side.
- **[15] Giunchiglia, Serafini — Hierarchical meta-logics: some proof theoretic results** (Trento Tech. Report 1993). Full proofs of this paper's theorems + stronger subformula property.
- **[11] Giunchiglia — Multilanguage systems** (AAAI Spring Symp. 1990). Original ML systems paper.
- **[13] Giunchiglia — Contextual reasoning** (1993). The contextual reasoning angle — close cousin.
- **[18] Giunchiglia, Smaill — Reflection in constructive and non-constructive automated reasoning** (1989). Reflection-up/down origin.
- **[33] McCarthy — Notes on formalizing context** (IJCAI-93). Philosophical `ist(c, p)` this paper operationalizes.
- **[14] Giunchiglia, Serafini — Multilanguage first order theories of propositional attitudes** (1991). First-order MBK.
- **[16] Giunchiglia, Serafini, E. Giunchiglia, Frixione — Non-omniscient belief as context-based reasoning** (IJCAI-93). MBK applied to non-omniscient belief.
- **[46] Weyhrauch — FOL with metatheory** (1982). Foundational ancestor of the implementation motivation.
- **[37] Prawitz — Natural Deduction** (1965). Proof-theoretic toolkit used throughout.

## Full Reference List

*Transcribed from pp.67-70. See `citations.md` for the formatted list and key-citations notes.*
