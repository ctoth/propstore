---
title: "Propositional Defeasible Logic has Linear Complexity"
authors: "M.J. Maher"
year: 2001
venue: "Theory and Practice of Logic Programming"
pages: "691-711"
doi_url: "https://doi.org/10.1017/S1471068401001168"
---

# Propositional Defeasible Logic has Linear Complexity

## One-Sentence Summary

Maher proves that **inference in propositional defeasible logic (the full language with strict rules, defeasible rules, defeaters, and a programmable acyclic priority relation) can be performed in linear time in the size of the theory** — a striking contrast with most other propositional non-monotonic logics, which are intractable (co-NP-hard or Π₂ᵖ-hard).

## Problem Addressed

Most non-monotonic / nonmonotonic-reasoning languages have intractable propositional inference: sceptical default reasoning is Π₂ᵖ-hard, sceptical autoepistemic reasoning and propositional circumscription are similarly hard, and sceptical inference from logic programs under stable model or Clark completion semantics is co-NP-hard *(p.1)*. This blocks practical large-scale non-monotonic reasoning. Defeasible logic — a generalization of inheritance networks with exceptions, including a programmable priority relation, defeaters, and rules over arbitrary literals — is rich, but its complexity was not previously bounded tightly. Maher's earlier work showed full first-order defeasible logic is r.e. (ref [22]); this paper closes the propositional case at **linear time**.

## Key Contributions

- A **transition system** that progressively simplifies a defeasible theory while accumulating its consequences; preserves meaning; when no more transitions apply, all consequences have been accumulated *(p.2)*.
- A **linear-time algorithm** (in size of theory) to compute the set of all conclusions for a basic defeasible theory (no superiority, no defeaters), via careful data structures *(p.2)*.
- A **linear-time, linear-blowup reduction** from arbitrary defeasible theories (with superiority and defeaters and possibly classical-conflict rules) to basic defeasible logic, lifting the linear bound to the full language *(p.2)*.
- A formal proof system where the original four inference rules `+Δ, −Δ, +∂, −∂` are augmented with auxiliary tags `+σ, −σ` ("there is / is not a tentative reason for the literal") that reduce per-step work, providing the logical basis for the algorithm *(p.8)*.
- The algorithm is the basis of a real implementation of defeasible logic (ref [23]) *(p.2)*.

## Methodology

Defeasible logic is defined by a four-tag proof theory (`+Δ, −Δ, +∂, −∂`) over a defeasible theory `D = (F, R, >)` where `F` is a finite set of literal facts, `R` a finite set of rules of three kinds (strict `→`, defeasible `⇒`, defeaters `↝`), and `>` an acyclic superiority relation on `R`.

The complexity bound is established by:
1. Defining proof theory and a **simplified proof theory** for *basic defeasible logic* (a subset with no superiority, no defeaters) using new tags `+σ, −σ` *(p.8)*.
2. Defining a **transition system** over basic defeasible theories (extended with already-derived conclusions) that simplifies the theory in single-pass-friendly local steps; proving correctness (each transition preserves the conclusion set) and termination (transitions strictly reduce a well-founded measure).
3. Giving a concrete **algorithm** that performs the transitions in an order reachable by maintaining counters and worklists, achieving linear cost in `|D|`.
4. Defining **transformations** (from refs [3] and [1]) that map any defeasible theory to a basic theory, preserving conclusions, with linear time and linear size blowup.

## Defeasible Theory: Five Ingredients (Section 2.1, p.2)

A defeasible theory consists of five different kinds of knowledge:

- **Facts** — indisputable literal statements, e.g. `emu(tweety)` *(p.2)*.
- **Strict rules** `A(r) → C(r)` — classical rules: indisputable premises ⇒ indisputable conclusion. E.g. `emu(X) → bird(X)` *(p.2)*.
- **Defeasible rules** `A(r) ⇒ C(r)` — defeasible-by-contrary-evidence. E.g. `bird(X) ⇒ flies(X)` *(p.2)*.
- **Defeaters** `A(r) ↝ C(r)` — rules that **cannot** be used to draw conclusions; only used to defeat opposing defeasible rules. E.g. `heavy(X) ↝ ¬flies(X)` *(p.2)*.
- **Superiority relation** `>` on rules — programmable priorities; required to be **acyclic** (transitive closure is irreflexive); priorities are **local** — `>` only matters between rules with complementary heads (rules with non-conflicting heads can sit in `>` but it has no effect on proof theory) *(p.3)*.

Sets of rules with competing heads work as **teams** — a platypus example: `r₁: monotreme ⇒ mammal`, `r₂: hasFur ⇒ mammal`, `r₃: laysEggs ⇒ ¬mammal`, `r₄: hasBill ⇒ ¬mammal`, with `r₁ > r₃` and `r₂ > r₄`; no single rule beats all competitors but the team `{r₁,r₂}` jointly defeats `{r₃,r₄}` so defeasible logic concludes `mammal(platypus)` *(p.3)*.

### Differences from Default Logic (p.3)

- Default logic has no priority among rules and no defeaters.
- Default logic permits arbitrary logical expressions in facts/defaults; defeasible logic permits only literals in rules.
- Even restricted to Horn default theories `(W, D)` with `W` a literal conjunction and `D` Horn defaults (syntactically *weaker* than defeasible logic), sceptical inference is **co-NP-hard** (ref [9]) — yet defeasible logic is linear *(p.3)*.
- Application of rules differs: in default logic, the rules `:a/a` and `:¬a/¬a` are independent so either may apply; in defeasible logic the rules `{⇒a, ⇒¬a}` mutually defeat — neither applies (Nute, ref [28]) *(p.3)*.

## Formal Definitions (Section 2.2, p.4)

Restricted to propositional (rule schemas with finite Herbrand universe acceptable; instantiation is treated as fully grounded for this paper).

**Rule** `r: A(r) ↪ C(r)`:
- unique label `r`,
- antecedent (body) `A(r)` — a finite set of literals (omittable if empty),
- arrow `↪` — placeholder for `→` (strict), `⇒` (defeasible), `↝` (defeater),
- consequent (head) `C(r)` — a single literal *(p.4)*.

For a set `R` of rules, define:
- `R_s` — strict rules in `R`,
- `R_sd` — strict + defeasible rules in `R`,
- `R_d` — defeasible rules in `R`,
- `R_dd` — defeasible rules + defeaters in `R`,
- `R_dft` — defeaters in `R`,
- `R[q]` — rules in `R` with consequent `q` *(p.4)*.

**Complementary literal**: if `q = p` (positive literal) then `~q = ¬p`; if `q = ¬p`, then `~q = p`. Distinct from `−` (used for unprovability tag) *(p.4)*.

**Superiority relation**: `>` on `R`. `r₁ > r₂` ⇒ `r₁` superior to `r₂`, `r₂` inferior. Required acyclic *(p.4)*.

**Defeasible theory** `D = (F, R, >)` where `F` is a finite literal set (facts), `R` finite rule set, `>` an acyclic superiority relation on `R` *(p.4)*.

### Conclusions (four tags) (Section 2.3, p.5)

A *conclusion* is a tagged literal:
- `+Δq` — `q` is **definitely provable** in `D`.
- `−Δq` — proved that `q` is **not definitely provable** in `D`.
- `+∂q` — `q` is **defeasibly provable** in `D`.
- `−∂q` — proved that `q` is **not defeasibly provable** in `D` *(p.5)*.

`−` (failure / proven-not-provable) is distinct from `¬` (classical negation). `+Δq ⇒ +∂q` and `−∂q ⇒ −Δq` *(p.5)*.

### Inference Rules (Definition of Provability) (p.5–7)

A *derivation* in `D = (F, R, >)` is a finite sequence `P = (P(1), …, P(n))` of tagged literals built by the four inference rules below; `P(1..i)` denotes the prefix of length `i`.

**+Δ:** append `+Δq` if either `q ∈ F`, or `∃r ∈ R_s[q] ∀a ∈ A(r): +Δa ∈ P(1..i)` *(p.6)*.

**−Δ:** append `−Δq` if `q ∉ F` and `∀r ∈ R_s[q] ∃a ∈ A(r): −Δa ∈ P(1..i)`. Note: nonprovability does **not** involve loop detection — for `D = {p → p}`, `p` cannot be proved but defeasible logic also cannot derive `−Δp` *(p.6)*.

**+∂:** append `+∂q` if either `(1) +Δq ∈ P(1..i)`, or `(2) (2.1) ∃r ∈ R_sd[q] ∀a ∈ A(r): +∂a ∈ P(1..i)` and `(2.2) −Δ~q ∈ P(1..i)` and `(2.3) ∀s ∈ R[~q]` either `(2.3.1) ∃a ∈ A(s): −∂a ∈ P(1..i)` or `(2.3.2) ∃t ∈ R_sd[q] such that ∀a ∈ A(t): +∂a ∈ P(1..i) and t > s` *(p.6)*.

**−∂:** append `−∂q` if `(1) −Δq ∈ P(1..i)` and `(2) (2.1) ∀r ∈ R_sd[q] ∃a ∈ A(r): −∂a ∈ P(1..i)` or `(2.2) +Δ~q ∈ P(1..i)` or `(2.3) ∃s ∈ R[~q] such that (2.3.1) ∀a ∈ A(s): +∂a ∈ P(1..i) and (2.3.2) ∀t ∈ R_sd[q] either ∃a ∈ A(t): −∂a ∈ P(1..i) or t ≯ s` *(p.7)*.

`L is provable in D`, written `D ⊢ L`, iff there is a derivation in which `L` is a line *(p.7)*.

**Coherence**: defeasible logic is *coherent* — there is no `D` and literal `p` with `D ⊢ +∂p` and `D ⊢ −∂p`, or `D ⊢ +Δp` and `D ⊢ −Δp` (ref [6]). I.e. one cannot prove a literal both provable and unprovable *(p.7)*.

**Conclusion equivalence**: `D₁ ≡ D₂` iff `D₁ ⊢ L ⇔ D₂ ⊢ L` for every tagged literal `L` *(p.7)*.

### Strict Rules Used Two Ways (p.8)

When proving `+Δ`, strict rules act classically: bodies-proved-definitely ⇒ head-proved-definitely, regardless of opposing chains. When proving `+∂`, strict rules act exactly like defeasible rules: a strict rule's body proved defeasibly ⇒ the rule may fire, but it is **not automatically superior** to defeasible rules — it can still be defeated by an opposing not-weaker rule.

This paper assumes **duplicated strict rules**: every strict rule has a duplicate defeasible rule. Definite reasoning uses only strict rules; defeasible reasoning uses only defeasible rules. Conclusions are unchanged *(p.8)*.

### Basic Defeasible Logic + Auxiliary Tags σ (p.8)

**Basic defeasible logic** = the subset with no superiority statements and no defeaters. The proof theory simplifies (ref [1]). To simplify further, introduce two auxiliary tags `+σ, −σ` representing existence/non-existence of a tentative reason for the literal:

- **+σ:** append `+σq` if `∃r ∈ R_sd[q] ∀a ∈ A(r): +∂a ∈ P(1..i)` *(p.8)*.
- **−σ:** append `−σq` if `∀r ∈ R_sd[q] ∃a ∈ A(r): −∂a ∈ P(1..i)` *(p.8)*.

Tagged literals involving `σ, ∂, Δ` are called *extended conclusions*.

With the σ tags, the `+∂` and `−∂` rules collapse to:
- **+∂ (basic):** append `+∂q` if `+Δq ∈ P(1..i)` or `{+σq, −Δ~q, −σ~q} ⊆ P(1..i)` *(p.8)*.
- **−∂ (basic):** append `−∂q` if `−Δq ∈ P(1..i)` and `{−σq, +Δ~q, +σ~q} ∩ P(1..i) ≠ ∅` *(p.8)*.

This per-step simplification is the logical basis for the linear-time algorithm.

## §3 The Transition System (p.9–12)

The algorithm is defined on **states** `(D, C)` — a (current) defeasible theory `D` and a set of *extended conclusions* `C`. As the algorithm proceeds, `D` simplifies and conclusions accumulate in `C`. Positive-conclusion transitions are forward-chaining; negative conclusions arise dually *(p.9)*.

### Definition 1: Ten Transitions `(D_i, C_i) ⟹ (D_{i+1}, C_{i+1})` (p.9)

Conclusion-accumulating transitions (do not modify `D_i`):

1. `(D_i, C_i) ⟹ (D_i, C_i ∪ {+Δq, +∂q, +σq})` if there is a fact `q` in `D_i` or a strict rule in `D_i` with head `q` and empty body.
2. `(D_i, C_i) ⟹ (D_i, C_i ∪ {+σq})` if there is a defeasible rule in `D_i` with head `q` and empty body.
3. `(D_i, C_i) ⟹ (D_i, C_i ∪ {−Δq})` if there is no strict rule in `D_i` with head `q` and no fact `q` in `D_i`.
4. `(D_i, C_i) ⟹ (D_i, C_i ∪ {−σq})` if there is no rule in `D_i` with head `q`.
5. `(D_i, C_i) ⟹ (D_i, C_i ∪ {+∂q})` if `+Δq ∈ C_i` or `{−Δ~q, −σ~q, +σq} ⊆ C_i`.
6. `(D_i, C_i) ⟹ (D_i, C_i ∪ {−∂q})` if `−Δq ∈ C_i` and either `+Δ~q ∈ C_i` or `+σ~q ∈ C_i` or `−σq ∈ C_i`.

Theory-simplifying transitions (delete-and-shrink):

7. `(D_i, C_i) ⟹ ((D_i \ {r}) ∪ {r'}, C_i)` — strict rule `r` with body literal `q` becomes `r'` (with `q` deleted) when `+Δq ∈ C_i`.
8. `(D_i, C_i) ⟹ ((D_i \ {r}) ∪ {r'}, C_i)` — defeasible rule `r` with body literal `q` becomes `r'` (with `q` deleted) when `+∂q ∈ C_i`.
9. `(D_i, C_i) ⟹ ((D_i \ {r}), C_i)` — strict rule `r` with body literal `q` deleted when `−Δq ∈ C_i`.
10. `(D_i, C_i) ⟹ ((D_i \ {r}), C_i)` — defeasible rule `r` with body literal `q` deleted when `−∂q ∈ C_i`.

We write `(D_i, C_i) ⟹⁄` (no further nontrivial transition applies). `D` *derives* `C` if `(D, ∅) ⟹ ⋯ ⟹ (D', C') ⟹⁄` and `C` is the subset of `C'` involving only the four standard tags `+Δ, −Δ, +∂, −∂` *(p.9)*.

The system **ignores defeaters and superiority** — it is therefore *incorrect* for full defeasible logic and *incomplete* in general for basic defeasible logic. Counterexample: rules `a → b` and `⇒ a` cannot derive `+σb` via these transitions. **But under the assumption of duplicated strict rules, the transition system is sound and complete** *(p.10)*.

### Theorem 1 (Soundness) (p.10)

Let `D` be a basic defeasible theory with duplicated strict rules. If `(D, ∅) ⟹ ⋯ ⟹ (D', C') ⟹⁄` and `c ∈ C'`, then `D ⊢ c`.

Proof by induction on `i`, showing for each transition: (a) if `c ∈ C_{i+1}\C_i` then `D_i ⊢ c`; (b) `D_i ≡ D_{i+1}` (conclusion-equivalent). The first six transitions instantiate the inference rules. The last four (rule-modifying) preserve provability bidirectionally — proofs in `D_i` translate to proofs in `D_{i+1}` and vice versa, leveraging `D_i ⊢ +Δq` (transition 7), `D_i ⊢ +∂q` (8), `D_i ⊢ −Δq` (9), or `D_i ⊢ −∂q` (10) plus coherence to avoid circularity *(p.10–11)*.

**Corollary 1**: under the same hypotheses, `D ≡ D'`.

### Theorem 2 (Completeness) (p.11–12)

Let `D` be a basic defeasible theory with duplicated strict rules. If `(D, ∅) ⟹ ⋯ ⟹ (D', C') ⟹⁄` and `D' ⊢ c`, then `c ∈ C'`. Proved by minimal-counterexample on proof length: if some derivable `c` is missing from `C'`, examining the tag of `c` and the absence of further-applicable transitions yields a contradiction in every case.

### Theorem 3 (Combined Soundness+Completeness) (p.12)

Let `D` be a basic defeasible theory with duplicated strict rules. If `D` derives `C`, then for every conclusion `c`, `D ⊢ c` iff `c ∈ C`.

## §4 The Linear Algorithm (p.12, continuing)

Two parts:
1. A **series of transformations** producing an equivalent basic defeasible theory with duplicated strict rules — this is the work of section 4.1, building on transformations from ref [1].
2. **Application of transitions** in a computationally efficient order with the right data structures — section 4.2.

### §4.1 Transformations (p.12–14)

Three transformations (from ref [1]) convert any defeasible theory to an equivalent basic defeasible theory:
1. Place the defeasible theory in normal form.
2. Eliminate defeaters.
3. Reduce the superiority relation to the empty relation (`elim_sup`).

The composite is called *Basic*.

**Definition 2 — `elim_sup` (p.13)**: Let `D` be a regular defeasible theory with rules `R`, language `Σ`. Then

```
elim_sup(R) = R_s
            ∪ { ¬inf⁺(r₁) ⇒ inf⁺(r₂),
                ¬inf⁻(r₁) ⇒ inf⁻(r₂)        | r₁ > r₂ }
            ∪ { A(r) ⇒ ¬inf⁺(r),
                ¬inf⁺(r) ⇒ p,
                A(r) ⇒ ¬inf⁻(r),
                ¬inf⁻(r) ⇒ p                | r ∈ R_d[p] }
            ∪ { A(r) ⇒ ¬inf⁻(r),
                ¬inf⁻(r) ↝ p                | r ∈ R_dft[p] }
```

For each rule `r`, `inf⁺(r)` and `inf⁻(r)` are *new* atoms not in `Σ`; all such new atoms are distinct *(p.13)*.

Intuition: `inf⁺(r)` and `inf⁻(r)` mean `r` is *inferior* to a rule in `R_sd` (resp. `R`) that has a defeasibly provable body. If `D ⊢ +σ inf⁺(r)`, then `D ⊬ +∂ ¬inf⁺(r)`; even when `A(r)` is proved defeasibly, the consequent `p` of `r` cannot be established defeasibly via `r` because the link is broken *(p.13)*.

**Defeater elimination** is similar in flavor: introduce `p⁺, p⁻` for each proposition `p`, replace each rule with up to three rules, encoding "p (resp. ¬p) is not defeated by a defeater" as a link that a defeater can break with a defeasible rule. (See ref [1] for full definition.) These transformations are *profligate* but are one-pass each, so the resulting theory is at most a constant factor larger *(p.13)*.

**Theorem 4 (ref [1])**: Let `D` be a defeasible theory with language `Σ`, `D' = Basic(D)`. Then `D'` is a basic defeasible theory and for all conclusions `c` in `Σ`: `D ⊢ c` iff `D' ⊢ c`. Furthermore `D'` can be constructed in time linear in `|D|` and `|D'|` is linear in `|D|` *(p.13)*.

**Definition 3 — `DupStrict` (p.14)**: For `D = (F, R, >)`, let `DupStrict(D) = (F, R', >)` where `R' = R ∪ {(r: B ⇒ q) | (r: B → q) ∈ R_s}`. Adds a defeasible duplicate of every strict rule.

**Proposition 1 (p.14)**: For any defeasible theory `D` and conclusion `c`, `D ⊢ c` iff `DupStrict(D) ⊢ c`. Proof sketch: definite provability uses only strict rules + facts (unchanged); defeasible inference rules don't distinguish strict vs defeasible at the rule-application level, and don't care about rule multiplicity.

### §4.2 The Algorithm (p.14–17)

**Pseudocode (Figure 1, p.15)**:

```
D' = (F', R', ∅) = Basic(D)
R = DupStrict(R')
initialize S
K = ∅

while (S ≠ ∅) {
  choose s ∈ S and delete s from S
  add s to K
  case s of
    +Δp:
      delete all occurrences of p in all rule bodies
      whenever a body of a strict rule with head h becomes empty:
        add +Δh to S
        record +Δh, +∂h, +σh
        CheckInference(+Δh, S)
      whenever a body of a defeasible rule with head h becomes empty:
        record +σh
        CheckInference(+σh, S)
    −Δp:
      delete all strict rules where p occurs in the body
      whenever there are no more strict rules for a literal h, and there is no fact h:
        add −Δh to S
        record −Δh
        CheckInference(−Δh, S)
    +∂p:
      delete all occurrences of p in defeasible rule bodies
      whenever a body with head h becomes empty:
        record +σh
        CheckInference(+σh, S)
    −∂p:
      delete all defeasible rules where p occurs in the body
      whenever there are no more defeasible rules for a literal h:
        record −σh
        CheckInference(−σh, S)
}
```

`p` ranges over literals; `s` over conclusions. `K` accumulates conclusions that have been *proved and used*; `S` holds *proven but unused* conclusions. `CheckInference(s, S)` adds `+∂p` or `−∂p` (when justified) to `S`. E.g. `CheckInference(+σp, S)` checks whether `−Δ~p` and `−σ~p` have been established so `+∂p` can be inferred (and added); and if `−Δ~p` has been established, adds `−∂~p` to `S`. Similarly `CheckInference(−Δp, S)` checks `+σ~p` and `−σp` so `+∂~p` might be inferred, and checks `−σp, +Δ~p, +σ~p` for `−∂p` *(p.15)*. Coherence (ref [6]) ensures defeasible logic never infers both `+∂p` and `−∂p`, so the algorithm need not track both *(p.15, footnote 3)*.

**Algorithm correctness (p.16)**: Execution corresponds to a restricted form of the transition system. `S ∪ K` plus recorded extended conclusions corresponds to `C_i`. Deletions correspond to transitions 7–10; `add` statements to transitions 1 and 3; `record` statements to transitions 1–4 (these also reflected in `S` initialization); `CheckInference` embodies transitions 5–6. The first `+Δ` case requires that all transitions 7 and 8 involving `p` occur as a block, uninterrupted; the only other transitions allowed in the block are 1 and 2 (when `p` is the last remaining literal in a rule) and 5 and 6 (when recorded info about `p` triggers them). The algorithm restricts ordering only — every original transition remains achievable — so soundness/completeness lift directly.

### §4.2 Data Structure (Figure 2, p.16)

The data structure (illustrated for `r₁: b,c,d ⇒ a; r₂: ¬b,d,¬e ⇒ a; r₃: d,¬e ⇒ ¬a`) supports:

- **Rule body** as a doubly-linked list (horizontal arrows in Fig. 2).
- For each literal `p`: a doubly-linked list of *occurrences* of `p` in bodies of strict rules and another for defeasible rules (diagonal arrows).
- For each literal `p`: doubly-linked lists of strict rules with head `p` and defeasible rules with head `p` (dashed arrows).
- Each literal occurrence has a back-link to the rule record.
- Each literal `p` holds the recorded extended-conclusion flags about `p` and a link to the record for `~p`.

**Cost properties**:
- Deletion of a literal/rule is `O(1)` per literal deleted.
- Detect in `O(1)` whether a deleted literal was the *only* literal in that body.
- Detect in `O(1)` whether a deleted rule with head `h` was the *only* strict (resp. defeasible) rule for `h`.
- Each literal occurrence is deleted at most once; each rule deleted at most once.
- `CheckInference` runs in `O(1)` (≤3 checks).

**Theorem 5 (Main Result) (p.17)**: The consequences of a defeasible theory `D` can be computed in `O(N)` time, where `N` is the number of symbols in `D`.

The main loop is `O(N)` where `N = |literal occurrences in D'|`; `S`-initialization is proportional to `|propositions in D'|`; `S` operates as queue/stack with `O(1)` push/pop. Initial transformations producing `D'` are linear (Theorem 4). Total: linear in `|D|` *(p.17)*.

**Comparison with Dowling–Gallier (refs [11], [12])** *(p.17)*: The algorithm restricted to positive definite conclusions is similar to the bottom-up linear algorithm for Horn-clause SAT. Difference: Dowling–Gallier keeps a *count* of body atoms; this algorithm *tracks the body itself*. Higher memory, but allows reconstructing the *residue* — the simplified rules that remain after computation — which is useful for understanding theory behaviour and for some applications of defeasible logic.

## §5 Discussion (p.17–18)

Features of defeasible logic that contribute to its linear complexity:

1. **Form of failure**: `−Δ` and `−∂` proof conditions correspond to Kunen's semantics for logic programs with negation-as-failure (ref [22]); does not include looping failures; propositional Kunen has linear complexity *(p.17)*.
2. **Static and local nature of conflict**: when deriving `+∂q` or `−∂q`, only rules for `q` and `~q` matter — `~q` is the unique conflictant literal. Set of conflicting rules is unchanging and immediately readable. Logics with no a priori bound on conflicting literals/rules (e.g. plausible logic, ref [8]) are expected to be more complex *(p.17)*.
3. **Linear-cost elimination of superiority relation**: based on a simple syntactic transformation (ref [1]); similar transformation has been proposed for higher-complexity logics (ref [19]). Success here partly attributable to static superiority and static/local conflict — neither changes during evaluation *(p.17–18)*.

**Non-factor — team defeat** *(p.18)*: Conceptually team defeat (two competing rule sets) might cause combinatorial blow-up, but reformulating it as competing *literals* shows there's a fixed amount of relevant information; each rule contributes individually.

**Expected extensions** *(p.18)*: Variants in ref [2] and variants where strict rules dominate defeasible rules (ref [28]) should also be linear-complexity. **Well-founded defeasible logic** (ref [22]) is expected to be **quadratic** since it employs well-founded semantics (ref [32]) which has quadratic complexity.

## §6 Conclusion (p.18)

The algorithm has been implemented as the system **Delores** (ref [24]), with preliminary experimental evaluation (ref [23]); executes simple but large theories of basic defeasible logic very quickly; linear complexity is supported empirically. The transformations to convert arbitrary theories into basic form impose a *large constant factor* on initialization cost — attributed to multiplication of rules and propositions during the transformations — and may be improvable by integrating transformations more tightly and/or abandoning the design goal of incrementality (ref [1]). Work proceeding on improvements and on application to reasoning about regulations (ref [4]).

## Key Equations / Statistical Models

This is a complexity / proof-theory paper; key quantitative claims are size and time bounds.

$$
T_{\mathrm{algorithm}}(D) \in O(|D|)
$$
Where: `|D|` is the number of symbols in `D` (literals, rule occurrences, etc.). Linear-time computation of the full conclusion set of an arbitrary propositional defeasible theory `D` *(p.17, Theorem 5)*.

$$
|\mathit{Basic}(D)| \in O(|D|)
$$
Where: `Basic(D)` is the basic-defeasible-logic theory produced by Antoniou–Billington–Maher transformations applied to `D`. Linear blowup *(p.13, Theorem 4)*.

$$
T_{\mathrm{Basic}}(D) \in O(|D|)
$$
Where: time to construct `Basic(D)` *(p.13, Theorem 4)*.

`elim_sup(R)` adds:
- 2 new propositions (`inf⁺(r), inf⁻(r)`) per rule `r ∈ R`;
- 2 new rules per superiority statement `r₁ > r₂` *(p.13)*;
- up to 4 rules replacing each original rule *(p.12)*.

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Theory size (literal occurrences) | N | symbols | — | — | 17 | Linear-bound parameter; total work is `O(N)` |
| Conclusion forms | — | tags | 4 | {+Δ, −Δ, +∂, −∂} | 5 | Standard tags |
| Auxiliary tags (basic logic) | — | tags | 2 | {+σ, −σ} | 8 | Reduce per-step work |
| Rule kinds | — | — | 3 | {strict →, defeasible ⇒, defeater ↝} | 4 | |
| `elim_sup` new atoms per rule | — | atoms | 2 | inf⁺(r), inf⁻(r) | 13 | |
| `elim_sup` new rules per superiority statement | — | rules | 2 | — | 13 | |
| `elim_sup` rules replacing each original rule | — | rules | up to 4 | — | 12 | |
| `CheckInference` checks per call | — | checks | ≤3 | — | 17 | Constant time |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | Population/Context | Page |
|---------|---------|-------|--------------------|------|
| Inference complexity, propositional defeasible logic | time complexity | `O(N)` | basic + full defeasible logic via `Basic` | 17 |
| Theory size after `Basic` transformation | size | linear in `|D|` | arbitrary defeasible theory | 13 |
| `Basic(D)` construction time | time | linear in `|D|` | arbitrary defeasible theory | 13 |
| Inference complexity, sceptical default logic | time complexity | Π₂ᵖ-hard | comparison | 1 |
| Inference, autoepistemic / circumscription | time complexity | Π₂ᵖ-hard / co-NP-hard | comparison | 1 |
| Inference, Horn default theories `(W,D)` | time complexity | co-NP-hard | comparison (ref [9]) | 3 |
| Expected complexity, well-founded defeasible logic | time complexity | `O(N²)` (predicted) | not proved here, refs [22], [32] | 18 |

## Methods & Implementation Details

- The proof-theory `+Δ, −Δ, +∂, −∂` is replaced with `+Δ, −Δ, +σ, −σ, +∂, −∂` for *basic* defeasible logic to localise per-step work *(p.8)*.
- Strict rules duplicated as defeasible rules (`DupStrict`) so that defeasible inference uses only defeasible rules, simplifying algorithm cases without changing conclusions *(p.14)*.
- `Basic(D)`: normal form → eliminate defeaters → `elim_sup` (eliminate superiority); each pass linear *(p.12–13)*.
- Algorithm uses worklist `S` (queue/stack — supports add, choose+delete, test-empty in `O(1)`), proven-and-used set `K`, current theory `D'` *(p.14–15)*.
- Rule body = doubly-linked list. Per literal `p`: doubly-linked list of body occurrences (split by strict/defeasible) and doubly-linked list of head occurrences. Each occurrence back-links to its rule record. Each literal's record holds extended-conclusion flags and link to `~p` *(p.16)*.
- Edge case: when a defeasible rule's body becomes empty due to `+Δ`, also record `+σh`; when no remaining strict (resp. defeasible) rules for a literal, record `−Δh` (resp. `−σh`) *(Figure 1, p.15)*.
- Coherence used to avoid tracking both `+∂p` and `−∂p` for the same literal *(p.15, fn 3)*.

## Figures of Interest

- **Fig 1 (p.15):** Inference algorithm for defeasible logic — pseudocode; main while-loop with `+Δ, −Δ, +∂, −∂` cases.
- **Fig 2 (p.16):** Data structure for rules — example with three rules; doubly-linked horizontal lists for rule bodies, dashed lists for rules-by-head, diagonal lists for occurrences per literal.

## Results Summary

**Theorem 5**: The consequences of a propositional defeasible theory `D` are computable in `O(N)` time, where `N` = number of symbols in `D`. Holds for **full** defeasible logic with strict rules, defeasible rules, defeaters, and an acyclic superiority relation, by composing the linear-blowup linear-time `Basic` transformations with the linear basic-DL algorithm *(p.17)*. Empirically supported by the Delores implementation (ref [24]) *(p.18)*.

## Limitations

- The transformations to `Basic(D)` impose a **large constant factor** on initialization cost — multiplication of rules and propositions makes the constant practically painful even though asymptotically linear *(p.18)*.
- The proof of correctness for the linear algorithm uses the duplicated-strict-rules assumption; this duplication is "not strictly necessary" but is used for proof simplicity rather than performance optimality *(p.13, fn 2)*.
- The transition system is **incomplete in general** for basic defeasible logic when rules don't have duplicated strict-as-defeasible duplicates — counter-example `a → b, ⇒ a` cannot derive `+σb` without the duplication assumption *(p.10)*.
- Algorithm covers propositional case only; full first-order DL is r.e. (ref [22]) *(p.1)*.
- Variants like plausible logic (ref [8]) where conflicts are not statically/locally bounded are expected to be more complex *(p.17)*.

## Arguments Against Prior Work

- Sceptical default reasoning (Reiter [29]) is `Π₂ᵖ`-hard; sceptical autoepistemic and circumscription are similarly hard; sceptical inference under stable-model or Clark-completion semantics is co-NP-hard (refs [13], [9]). These languages are very expressive but have not produced practical NMR applications *(p.1)*.
- Default logic lacks priorities and defeaters; rule application semantics differs in a key way (Nute [28]): `:a/a, :¬a/¬a` allow either to fire but `{⇒a, ⇒¬a}` interfere — the latter behavior is needed to model team defeat and exception-handling *(p.3)*.
- Even Horn default theories `(W, D)` (syntactically weaker than DL) have co-NP-hard sceptical inference (ref [9]) — DL is *richer* yet linear *(p.3)*.

## Design Rationale

- **Strict rules duplicated as defeasible rules**: makes definite reasoning isolated to strict rules and defeasible reasoning use only defeasible rules; conclusions unchanged but algorithm cleaner. The duplication is for proof/implementation simplicity, not strictly necessary *(p.8, p.13 fn 2)*.
- **Auxiliary tags `+σ, −σ`**: per-step work in deriving `+∂, −∂` can be reduced if "tentative reason exists / does not exist for `q`" is materialised explicitly. This is the logical basis for the linear-time bound *(p.8)*.
- **Tracking rule bodies vs counts**: Dowling–Gallier (refs [11–12]) keeps a body-atom count for Horn satisfiability; this algorithm tracks the body itself. Higher memory but produces a *residue* (simplified remaining rules) usable for theory introspection and applications *(p.17)*.
- **Superiority eliminated by syntactic transformation `elim_sup`**: works because superiority is *static* — does not change during evaluation. Same kind of transformation has been tried for higher-complexity logics (ref [19]) but only succeeds linearly here because of the static/local conflict structure *(p.18)*.
- **Reformulating team defeat as competing literals**: prevents combinatorial blow-up that would arise from naive "two teams" framing *(p.18)*.

## Testable Properties

- Coherence: for every defeasible theory `D` and literal `p`, not both `D ⊢ +∂p` and `D ⊢ −∂p`; not both `D ⊢ +Δp` and `D ⊢ −Δp` *(p.7)*.
- Implication: `D ⊢ +Δq ⇒ D ⊢ +∂q`; `D ⊢ −∂q ⇒ D ⊢ −Δq` *(p.5)*.
- Conclusion equivalence: `D ≡ DupStrict(D)` *(p.14)*.
- Conclusion equivalence: `D ≡ Basic(D)` for conclusions in `Σ` (the original language) *(p.13)*.
- Linearity: total time on `|D|` literal occurrences is `O(|D|)` *(p.17)*.
- Acyclicity of `>`: required by definition of defeasible theory *(p.4)*.
- Locality of `>`: `r > r'` only matters when `head(r), head(r')` are complementary *(p.3)*.
- Loop sensitivity: for `D = {p → p}`, neither `+Δp` nor `−Δp` is derivable — failure-to-prove does **not** include loop detection; `−Δp` is only inferred from absence of strict rules with head `p`, which loops fail to satisfy *(p.6)*.
- Restricted transition system soundness: if `(D, ∅) ⟹⋯⟹ (D', C') ⟹⁄` and `c ∈ C'`, then `D ⊢ c` (Theorem 1, only under duplicated-strict-rules assumption) *(p.10)*.
- Restricted transition system completeness: under the same hypotheses, `D' ⊢ c ⇒ c ∈ C'` (Theorem 2) *(p.11)*.

## Relevance to Project

**propstore commits to defeasible logic as the substrate** for its argumentation/reasoning layer (ASPIC+, Dung AFs, ATMS, IC merge are *over* DL-style defeasible reasoning). Maher 2001 supplies:

1. **The complexity bound `O(N)`** that the propstore stack inherits when DL is used as the substrate. Any implementation strategy that preserves the structure of Maher's algorithm preserves linearity. Concretely: the `pks` query path's worst-case bound is governed by Theorem 5 here *(p.17)*.
2. **A reusable proof technique** — auxiliary tags + transition system + linear-blowup transformations — that propstore can apply to its own bounds for related reasoning surfaces (e.g. `propstore.defeasibility`'s CKR-style justifiable-exceptions injection at the ASPIC+ boundary, where the contextual-applicability decision is itself a DL-style derivation).
3. **A canonical pseudocode** (Figure 1) and **canonical data structures** (Figure 2) which propstore's DL evaluator should mirror to inherit the linearity argument. Departures from this layout require a new complexity proof.
4. **A coherence guarantee** (no `+∂p` and `−∂p` together) propstore can rely on at the AF-construction layer — the DL substrate will not present contradictory grounded conclusions for the AF builder to puzzle over.
5. **A negative-conclusion semantics** (`−` is *proven-not-provable*, distinct from classical `¬`) which maps naturally onto propstore's distinction between absence-of-evidence and rebuttal — and onto the source-branch's policy of holding rival normalizations rather than collapsing to truth.
6. **An empirical implementation reference**: Delores (ref [24], [23]) — concrete artefact for benchmarking propstore's DL evaluator.
7. **A predicted quadratic bound for well-founded defeasible logic** (p.18) — relevant if propstore later adopts WFS-based DL for richer failure handling.

The complexity bound applies to **basic** DL extended with the `Basic` transformation; propstore's existing `propstore.defeasibility` and `propstore.aspic_bridge` should be examined for whether they preserve or break the static/local conflict structure that makes linearity possible (ref [Maher §5, p.17–18]).

## Open Questions

- [ ] How tightly can the `Basic` transformation's constant factor be reduced if propstore relaxes incrementality? (Conclusion §6.)
- [ ] Does propstore's CKR-style `propstore.defeasibility` exception-injection at the ASPIC+ boundary preserve static/local conflict, hence linearity?
- [ ] Does propstore's IC-merge layer (`propstore.belief_set.ic_merge`) compose with the linear DL substrate without reintroducing intractability? Maher does not address merging.
- [ ] What is the actual constant factor measured in Delores for representative theories? Useful as a reality check for propstore's DL evaluator.
- [ ] Is there a closed-form bound for the number of `+σ, −σ` introductions per literal in worst case? Theorem 5 implies at most one each per literal, but worth confirming when propstore tracks provenance for these auxiliary conclusions.

## Notable References Cited (with citation keys, Maher's numbering)

- [1] Antoniou, Billington, Governatori, Maher. *Representation Results for Defeasible Logic*. ACM TOCL 2(3):255–287, 2001 — the source of the `Basic` transformations relied on for Theorem 4.
- [2] Antoniou, Billington, Governatori, Maher. *A Flexible Framework for Defeasible Logics*. AAAI-00, 405–410.
- [3] Antoniou, Billington, Maher. *Normal forms for defeasible logic*. JICSLP 1998.
- [5] Antoniou, Maher, Billington. *Defeasible Logic versus Logic Programming without Negation as Failure*. JLP 41(1):45–57, 2000 — already in propstore's collection (Antoniou_2000).
- [6] Billington. *Defeasible Logic is Stable*. JLC 3:370–400, 1993 — coherence result.
- [9] Cadoli, Schaerf. *A Survey of Complexity Results for Nonmonotonic Logics*. JLP 17(2,3,4):127–160, 1993.
- [11] Dowling, Gallier. *Linear-Time Algorithms for Testing Satisfiability of Propositional Horn Formulae*. JLP 1(3):267–284, 1984 — comparison anchor.
- [12] Gallo, Urbani. *Algorithms for Testing the Satisfiability of Propositional Formulae*. JLP 7(1):45–61, 1989.
- [22] Maher. *Denotational Semantics for Defeasible Logic*. CL 2000, LNAI 1861, 209–222 — first-order DL r.e. and well-founded DL.
- [23] Maher, Rock, Antoniou, Billington, Miller. *Efficient Defeasible Reasoning Systems*. ICTAI 2000, 384–392 — implementation evaluation.
- [24] Miller. *DELORES User's Manual*. 2000 — concrete implementation.
- [28] Nute. *Defeasible Logic*. Handbook of Logic in AI and LP Vol 3, OUP 1994 — definitional ancestor of DL.
- [29] Reiter. *A logic for default reasoning*. AI 13:81–132, 1980.
- [32] Van Gelder, Ross, Schlipf. *The Well-Founded Semantics for General Logic Programs*. JACM 38(3):620–650, 1991.

## Implementation Notes for propstore

- Mirror Figure 1's worklist + case-split structure inside any propstore DL evaluator. Departure invalidates the linearity argument.
- Mirror Figure 2's bidirectional indexes: literal→rules-with-this-literal-in-body (split strict/defeasible), literal→rules-with-this-literal-as-head (split strict/defeasible), occurrence→rule, literal→`~literal`. Each index lookup must be `O(1)`.
- Use coherence (Theorem in ref [6]) to reject DL evaluator results that produce both `+∂p` and `−∂p` — that's a bug, not a "rival stance".
- Track `+σ, −σ` even when only `+∂, −∂` are user-visible — they are needed for the `CheckInference` constant-time check.
- Reify the `Basic` transformation as a separately-tested, separately-bounded unit. Its constant factor is the dominant practical cost (per Conclusion §6).
- `−` (failure-to-prove) is **not** classical `¬`. The negation-handling code path must distinguish them — same point as Maher's "Notice the distinction between `−` and `¬`" *(p.5)*.
- Treat `>` as static: any propstore feature that would make the priority relation evaluation-time-dependent will break the `elim_sup` argument and forfeit linearity.

## Quotes Worth Preserving (verbatim)

- "Notice the distinction between `−`, which is used only to express unprovability, and `¬`, which expresses classical negation." *(p.5)*
- "this property says that we cannot establish that a literal is simultaneously provable and unprovable." (coherence) *(p.7–8)*

## Sections covered (full paper, pages 1–20)

- §1 Introduction (p.1–2)
- §2 Defeasible Logic (p.2–8): §2.1 informal, §2.2 formal definition, §2.3 proof theory
- §3 The Transition System (p.9–12): Definition 1, Theorems 1–3
- §4 The Linear Algorithm (p.12–17): §4.1 Transformations (Definitions 2–3, Theorem 4, Proposition 1), §4.2 The Algorithm (Figure 1, Figure 2, Theorem 5)
- §5 Discussion (p.17–18)
- §6 Conclusion (p.18)
- Acknowledgements (p.18)
- References (p.19–20)

## Notes-status checkpoint

Full paper extracted (20pp). Notes complete.

## Collection Cross-References

### Already in Collection

- [Representation Results for Defeasible Logic](../Antoniou_2000_RepresentationResultsDefeasibleLogic/notes.md) — Maher's ref [1]; supplies the `Basic` transformations (`normal`, `elim_dft`, `elim_sup`) Theorem 4 of this paper relies on for linear-blowup reduction to basic defeasible logic. Same author group (Antoniou, Billington, Governatori, Maher); the *representation* counterpart to this paper's *complexity* result.
- [Defeasible logic versus Logic Programming without Negation as Failure](../Antoniou_2000_DefeasibleLogicVersusLogic/notes.md) — Maher's ref [5]; sister paper showing DL strictly subsumes Horn-LP-without-NAF and embeds courteous logic programs. Same group; provides the proof-tag system whose complexity is bounded here.
- [A Logic for Default Reasoning](../Reiter_1980_DefaultReasoning/notes.md) — Maher's ref [29]; the canonical default logic Maher contrasts with throughout (sceptical default reasoning is `Π₂ᵖ`-hard, p.1; default rules `:a/a` and `:¬a/¬a` interact differently from `{⇒a, ⇒¬a}`, p.3).

### New Leads (Not Yet in Collection)

- **Antoniou, Billington, Maher (1998) — "Normal forms for defeasible logic," JICSLP 1998 [Maher ref 3].** The *normal form* transformation that is the first stage of `Basic`; precursor to ref [1].
- **Antoniou, Billington, Governatori, Maher (2000) — "A Flexible Framework for Defeasible Logics," AAAI-00 [Maher ref 2].** Variants of DL Maher predicts also have linear complexity (p.18); useful baseline for propstore's choice of DL flavour.
- **Antoniou, Billington, Maher (1999) — "On the analysis of regulations using defeasible rules," HICSS-32 [Maher ref 4].** Proposed application domain for Delores; test case for whether propstore's regulation-style claims fit DL.
- **Billington (1993) — "Defeasible Logic is Stable," J. Logic Comput. 3:370-400 [Maher ref 6].** Coherence proof — propstore relies on this when asserting the DL substrate cannot produce both `+∂p` and `−∂p`. Load-bearing.
- **Billington, de Coster, Nute (1990) — "A modular translation from defeasible nets to defeasible logic," JETAI 2:151-177 [Maher ref 7].** DL as generalisation of inheritance networks with exceptions.
- **Billington, Rock (2001) — "Propositional Plausible Logic: Introduction and Implementation," Studia Logica 67(2):243-269 [Maher ref 8].** Plausible logic — Maher's example of a logic where the static/local-conflict structure breaks, hence higher complexity expected (p.17).
- **Cadoli, Schaerf (1993) — "A Survey of Complexity Results for Nonmonotonic Logics," JLP 17(2,3,4):127-160 [Maher ref 9].** The complexity-landscape anchor for the NMR comparison; even Horn default theories are co-NP-hard.
- **Dimopoulos, Kakas (1995) — "Logic Programming without Negation as Failure," ISLP 1995 [Maher ref 10].** Relevant for the LPwNF-to-DL translation question (companion to ref [5]).
- **Dowling, Gallier (1984) — "Linear-Time Algorithms for Testing the Satisfiability of Propositional Horn Formulae," JLP 1(3):267-284 [Maher ref 11].** The methodological ancestor of Maher's algorithm — Dowling–Gallier counts body atoms; Maher tracks the body itself.
- **Gallo, Urbani (1989) — "Algorithms for Testing the Satisfiability of Propositional Formulae," JLP 7(1):45-61 [Maher ref 12].** Companion algorithmic work on Horn-clause SAT.
- **Gottlob (1992) — "Complexity results for nonmonotonic logics," JLC 2:397-425 [Maher ref 13].** The other anchor for the NMR-is-hard contrast.
- **Governatori, Maher (2000) — "An Argumentation-Theoretic Characterization of Defeasible Logic," ECAI 2000:469-474 [Maher ref 14].** Argumentation-theoretic semantics for DL — relevant to propstore's `propstore.aspic_bridge` translation surface.
- **Grosof (1997) — "Prioritized Conflict Handling for Logic Programs," ILPS 1997 [Maher ref 15].** Courteous logic programs — embedded in DL by Antoniou_2000 Theorem 5.1.
- **Horty (1994) — "Some Direct Theories of Nonmonotonic Inheritance," Handbook of Logic in AI Vol 3 [Maher ref 17].** Directly sceptical inheritance — DL generalises this.
- **Horty, Thomason, Touretzky (1987) — "A skeptical theory of inheritance in nonmonotonic semantic networks," AAAI-87:358-363 [Maher ref 18].** The classic ambiguity-blocking inheritance discussion.
- **Kowalski, Toni (1996) — "Abstract Argumentation," AI & Law 4:275-296 [Maher ref 19].** Abstract argumentation — Maher cites for the higher-complexity logic that has been "transformed" similarly without yielding linearity.
- **Maher (2000) — "A Denotational Semantics for Defeasible Logic," CL 2000, LNAI 1861:209-222 [Maher ref 20].** Maher's own denotational semantics for DL.
- **Maher, Antoniou, Billington (1998) — "A Study of Provability in Defeasible Logic," AJCAI 1998, LNAI 1502:215-226 [Maher ref 21].** Companion deeper analysis of DL provability.
- **Maher, Governatori (1999) — "A Semantic Decomposition of Defeasible Logics," AAAI-99:299-305 [Maher ref 22].** First-order DL is r.e.; well-founded DL framing — relevant if propstore later adopts WFS-style DL.
- **Maher, Rock, Antoniou, Billington, Miller (2000) — "Efficient Defeasible Reasoning Systems," ICTAI 2000:384-392 [Maher ref 23].** Implementation evaluation of Delores — empirical reality check for any propstore DL evaluator.
- **Miller (2000) — "DELORES User's Manual" [Maher ref 24].** The Delores implementation of Maher's algorithm — concrete reference artefact for propstore's DL evaluator.
- **Morgenstern (1998) — "Inheritance Comes of Age: Applying Nonmonotonic Techniques to Problems in Industry," AI 103:1-34 [Maher ref 25].** Industrial NMR survey — useful framing for propstore's case for adopting DL.
- **Niemelä (1999) — "Logic Programs with Stable Model Semantics as a Constraint Programming Paradigm," AMAI 25(3-4):241-273 [Maher ref 26].** ASP framing — propstore's expressiveness comparison reference.
- **Nute (1987) — "Defeasible Reasoning," HICSS 1987:470-477 [Maher ref 27].** Origin of Nute-style DL.
- **Nute (1994) — "Defeasible Logic," Handbook of Logic in AI Vol 3, OUP 1994:353-395 [Maher ref 28].** The handbook chapter; primary semantic ancestor of Maher's DL.
- **Stein (1992) — "Resolving Ambiguity in Nonmonotonic Inheritance Hierarchies," AI 55:259-310 [Maher ref 30].** Polynomial-time algorithms for inheritance with exceptions — Maher's predecessor for tractable NMR.
- **Stillman (1992) — "The Complexity of Propositional Default Logics," AAAI-92:794-799 [Maher ref 31].** Default-logic complexity anchor.
- **Van Gelder, Ross, Schlipf (1991) — "The Well-Founded Semantics for General Logic Programs," JACM 38(3):620-650 [Maher ref 32].** WFS — Maher predicts well-founded DL is `O(N²)` because WFS is quadratic.

### Cited By (in Collection)

- [A Defeasible Logic-based Framework for Contextualizing Deployed Applications](../Al-Anbaki_2019_DefeasibleLogicContextualizingApplications/notes.md) — cites this as ref [15]; complexity bound the Al-Anbaki `L = ⟨G, β, D, λ⟩` framework inherits when grounded in propositional DL.
- [Revision of Defeasible Logic Preferences](../Governatori_2012_RevisionDefeasibleLogicPreferences/notes.md) — cites this as ref [18]; load-bearing for Governatori et al.'s NP-completeness proof — the linear-time DL extension oracle the reduction invokes.
- [Defeasible Contextual Reasoning with Arguments in Ambient Intelligence](../Bikakis_2010_DefeasibleContextualReasoningArguments/notes.md) — appears in citations.md (citation list yet to be cross-checked for in-text use); Bikakis & Antoniou cite both Antoniou_2000_RepresentationResults and Maher 2001 in the same DL-foundations cluster.

### Supersedes or Recontextualizes

- (none) — Maher 2001 is the canonical complexity result for propositional DL; nothing in the collection is superseded by it.

### Conceptual Links (not citation-based)

**Algorithmic / complexity for argumentation reasoning (propstore complexity ceiling):**
- [Complexity of Abstract Argumentation](../Dunne_2009_ComplexityAbstractArgumentation/notes.md) — Strong. Dunne surveys complexity for abstract argumentation (mostly hard). Maher's paper is the linear lower bound for the rule-based substrate — together they bracket what propstore can hope for at each layer.
- [Methods for Solving Reasoning Problems in Abstract Argumentation](../Charwat_2015_MethodsSolvingReasoningProblems/notes.md) — Strong. Survey of solver techniques for AF problems — Maher's Dowling-Gallier-style worklist algorithm is the analogue at the DL substrate; informs implementation strategies for propstore's argumentation layer.
- [Polynomial-Time Algorithms for Computing Subjective Logic Operators](../Potyka_2019_PolynomialTimeEpistemicProbabilistic/notes.md) — Moderate. Potyka establishes polynomial-time bounds for probabilistic argumentation; Maher does so for crisp defeasible logic. Both contribute to a tractability story for the propstore argumentation/reasoning layer.
- [Fixed-Parameter Tractable Algorithms for Abstract Argumentation](../Dvorak_2012_FixedParameterTractableAlgorithmsAbstractArgumentation/notes.md) — Moderate. FPT for AFs. Maher's `O(N)` for DL is unconditional, but the parameterised view applies when propstore encodes DL theories into AFs.
- [Decomposition-Guided Reductions for Argumentation Treewidth](../Fichte_2021_Decomposition-GuidedReductionsArgumentationTreewidth/notes.md) — Moderate. Treewidth-based reductions for AF problems; structurally similar bookkeeping discipline to Maher's bidirectional-link rule data structures.

**Defeasible-logic substrate (direct upstream / parallel):**
- [Algorithmic Definitions for KLM-style Defeasible Disjunctive Datalog](../Morris_2020_DefeasibleDisjunctiveDatalog/notes.md) — Strong. Morris et al. give algorithmic definitions for KLM-style defeasible Datalog — the *Datalog* analogue of what Maher does for DL. Both are candidate substrates for `propstore.defeasibility`; Maher's bound is tighter, Morris's expressiveness is broader.
- [Defeasible Strict Consistency](../Goldszmidt_1992_DefeasibleStrictConsistency/notes.md) — Moderate. Goldszmidt's strict-vs-defeasible consistency results are the foundational hygiene that any partition `R = R_s ∪ R_d ∪ R_f` (which Maher's algorithm consumes directly) inherits.
- [What does a conditional knowledge base entail?](../Lehmann_1989_DoesConditionalKnowledgeBase/notes.md) — Moderate. Lehmann's rational-closure framework is a sibling tractable NMR formalism; both provide non-monotonic reasoning that escapes the `Π₂ᵖ` / co-NP cliff Maher contrasts with.
- [Nonmonotonic Reasoning, Preferential Models and Cumulative Logics](../Kraus_1990_NonmonotonicReasoningPreferentialModels/notes.md) — Moderate. KLM preferential models are the semantic/abstract counterpart to DL; Maher's complexity result sits at the algorithmic side of the same NMR cluster.

**ASPIC+ / structured argumentation translation surface:**
- [The ASPIC+ framework for structured argumentation: a tutorial](../Modgil_2014_ASPICFrameworkStructuredArgumentation/notes.md) — Strong. ASPIC+ has the same strict + defeasible + priority structure Maher reasons about. propstore's `propstore.aspic_bridge` translates between DL-style claims and ASPIC+ types — the linearity argument here is a precondition for propstore's claim that the bridge is computationally well-founded.
- [LLM-ASPIC+: A Neuro-Symbolic Framework for Defeasible Reasoning](../Fang_2025_LLM-ASPICNeuro-SymbolicFrameworkDefeasible/notes.md) — Moderate. LLM-extracted defeasible rules are a candidate input to a Maher-style evaluator at scale; the linearity bound becomes the throughput justification for the symbolic side of the LLM-symbolic pipeline.

**Forward-chaining / TMS / data-dependency:**
- [Building Problem Solvers](../Forbus_1993_BuildingProblemSolvers/notes.md) — Moderate. ATMS / data-dependency machinery; Maher's transition system is structurally analogous (forward-chaining accumulation + body-link bookkeeping).
- [Truth Maintenance System](../Doyle_1979_TruthMaintenanceSystem/notes.md) — Moderate. Doyle's TMS is the ancestor of body-link tracking; Maher's Figure 2 data structure is the DL specialisation.
- [Linear-Time Resolution Theorem Proving](../Bachmair_2001_ResolutionTheoremProving/notes.md) — Moderate. Resolution-style reasoning at the strict-rule layer; Maher's `+Δ` derivation for definite consequences is essentially unit resolution.

## Reconciliation provenance

Reconciled: 2026-05-07. Forward links established to 3 already-collected papers (Antoniou_2000_RepresentationResultsDefeasibleLogic, Antoniou_2000_DefeasibleLogicVersusLogic, Reiter_1980_DefaultReasoning). Reverse links established from 2 collection papers (Al-Anbaki_2019, Governatori_2012) — both updated with bidirectional cross-references and inline `→ NOW IN COLLECTION` annotations on their Related Work entries. Bikakis_2010 has citation-list mention only; treated as a Cited By candidate pending in-text confirmation. 27 new leads recorded from Maher's reference list. 13 conceptual links surfaced (5 Strong, 8 Moderate). No supersession. No tensions.

### Checkpoint state (post-reconcile)

- Notes complete (full 20-page extraction).
- description.md, abstract.md, citations.md, metadata.json all present.
- Backward annotation in Al-Anbaki_2019: lead moved to "Now in Collection", inline annotation added at line 370 of Al-Anbaki notes, leads-remaining count updated from 8 to 7.
- Backward annotation in Governatori_2012: inline annotation added at line 441, "Already in Collection" subsection extended with Maher 2001 entry.
- Pending: papers/index.md update.
- Blocker: none.
