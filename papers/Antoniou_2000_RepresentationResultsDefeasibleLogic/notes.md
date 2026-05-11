---
title: "Representation Results for Defeasible Logic"
authors: "G. Antoniou, D. Billington, G. Governatori, M. J. Maher"
year: 2001
venue: "ACM Transactions on Computational Logic 2(2):255-287"
doi_url: "https://doi.org/10.1145/371316.371517"
arxiv_id: "cs.LO/0003082"
pages: "1-23"
note: "Reading in progress; checkpoint after pages 0-9. Page numbers below refer to PDF page numbers in this preprint (arXiv:cs/0003082v1, 30 Mar 2000), which are 1-indexed in the printed text. Final paper appears as ACM TOCL 2001."
---

# Representation Results for Defeasible Logic

## One-Sentence Summary
Establishes representation theorems for Antoniou-Billington-Governatori-Maher Defeasible Logic — every defeasible theory is conclusion-equivalent to a normal-form theory with no facts, no defeaters, and an empty superiority relation — and gives modular/incremental transformations realizing the normal form, plus a simplified proof theory.

## Problem Addressed
Defeasible Logic (DL) has five primitives — facts, strict rules, defeasible rules, defeaters, superiority — and four proof tags +Δ, -Δ, +∂, -∂. This is operationally rich but theoretically heavy. The paper asks: which features are *expressively necessary*, and can the rest be *eliminated by transformation* while preserving the 4-tuple of conclusions? Answer: facts, defeaters, and the superiority relation are all eliminable; the simplified residual is essentially "strict + defeasible rules with implicit team comparison."

## Key Contributions
- Proof-theoretic analysis: classifies each literal p into one of 6 outcomes A-F based on the four sets +Δ, -Δ, +∂, -∂; only 6 of 16 set-membership combinations are realizable, and the joint outcome for (p, ¬p) admits 21 of 36 possible pairings (with 5 pair classes only realizable via cyclic > relations) *(p.7-9)*.
- Theorem 2 (acyclic representation): every acyclic defeasible theory D is conclusion-equivalent to a theory D' with **no superiority relation and no defeaters** *(p.10)*.
- Theorem 2 (cyclic representation): every cyclic theory is conclusion-equivalent to a defeater-free theory whose only cycles are length-2 between rules for a literal and its complement *(p.10)*.
- Two structural properties of transformations: **modularity** (apply per-rule without notifying the rest) and **incrementality** (cost of recomputing after a small theory edit is proportional to the edit) *(p.2)*.
- For each transformation, proves whether it satisfies modularity / incrementality, and shows non-existence of any modular / incremental transformation when the headline transformation does not satisfy that property.
- Construction: explicit transformations that (i) eliminate facts, (ii) separate strict from defeasible reasoning ("normal form"), (iii) eliminate defeaters, (iv) reduce superiority to empty, all without theory-wide evaluation.
- Simplified proof theory once the normal form is reached.
- Implementation foothold: these transformations underpin the **Delores** consequence-computing system, while **Deimos** is a query system for raw DL with 100,000s of rules *(p.1)*.

## Literature Lineage
Defeasible Logic family begins with Nute (refs 15, 16). Recent variants in the same "logic programming without negation as failure" family: Courteous logic programs (ref 10), LPwNF (ref 9). DL is shown to be the most sceptically expressive of these (ref 5). Application domains cited: regulations and business rules (refs 11, 3), contracts (ref 18), information integration (ref 4). The team-of-rules metaphor is borrowed from Courteous LP (ref 10). Billington (ref 6) earlier proved consistency of the defeasible part of an acyclic theory.

## Methodology
Pure proof-theoretic analysis on propositional Defeasible Logic with finite ground rule schemas. Uses derivation sequences over four tagged-literal proof rules (+Δ, -Δ, +∂, -∂) of section 2.3. Defines conclusion-equivalence ≡ as identity of the 4-tuple (+Δ, -Δ, +∂, -∂). Works modulo language extension: writes ≡_Σ when equivalence is required only over a sublanguage Σ. Transformations are constructed and proven correct by case analysis over the proof rules.

## Notation and Primitives
- **Language Σ**: finite set of propositional atoms and rule labels.
- **Literal**: atom or its classical negation. ~q is the complementary literal of q.
- **Rule** r: A(r) ↪ C(r), with antecedent A(r) finite set of literals, consequent C(r) a literal, label r unique.
  - Strict: → ; defeasible: ⇒ ; defeater: ⤳.
- **R_s, R_sd, R_d, R_dft**: strict rules / strict+defeasible / defeasible / defeaters subsets of R.
- **R[q]**: rules in R with consequent q.
- **Superiority** > on R; r1 > r2 means r1 overrules r2. Acyclic = transitive closure irreflexive. **Local**: > only relevant on rules with complementary heads.
- **Defeasible theory** D = (F, R, >). Well-formed iff > acyclic AND > only defined on complementary-head rule pairs. Cyclic iff > is cyclic. Triple (∅, R, ∅) abbreviated as just R.

## Proof Theory (verbatim, from Section 2.3, p.4-5)

A *conclusion* is a tagged literal in {+Δq, -Δq, +∂q, -∂q}.

**+Δ**: If P(i+1) = +Δq then either q ∈ F or ∃r ∈ R_s[q] ∀a ∈ A(r): +Δa ∈ P(1..i)

**-Δ**: If P(i+1) = -Δq then q ∉ F and ∀r ∈ R_s[q] ∃a ∈ A(r): -Δa ∈ P(1..i)

**+∂**: If P(i+1) = +∂q then either
  (1) +Δq ∈ P(1..i), or
  (2) (2.1) ∃r ∈ R_sd[q] ∀a ∈ A(r): +∂a ∈ P(1..i) and
       (2.2) -Δ~q ∈ P(1..i) and
       (2.3) ∀s ∈ R[~q] either
            (2.3.1) ∃a ∈ A(s): -∂a ∈ P(1..i), or
            (2.3.2) ∃t ∈ R_sd[q] such that ∀a ∈ A(t): +∂a ∈ P(1..i) and t > s.

**-∂**: If P(i+1) = -∂q then
  (1) -Δq ∈ P(1..i) and
  (2) (2.1) ∀r ∈ R_sd[q] ∃a ∈ A(r): -∂a ∈ P(1..i), or
       (2.2) +Δ~q ∈ P(1..i), or
       (2.3) ∃s ∈ R[~q] such that ∀a ∈ A(s): +∂a ∈ P(1..i) and ∀t ∈ R_sd[q] either
                ∃a ∈ A(t): -∂a ∈ P(1..i) or t ≯ s.

Loop semantics: -Δ has no loop detection — for D = {p → p} we have ⊬ +Δp but also ⊬ -Δp.

Sceptical-applicability invariant: once -∂a is established at some prefix it stays established; defeasible logic does not change applicability mid-proof (p.6-7).

## The Six Per-Literal Outcomes (Section 3, p.7)

Define +Δ, -Δ, +∂, -∂ as the four sets of literals provable with each tag. Containments and disjointness:

$$
+\Delta \subseteq +\partial \qquad +\Delta \cap -\Delta = \emptyset
$$

$$
-\partial \subseteq -\Delta \qquad +\partial \cap -\partial = \emptyset
$$

$$
+\Delta \cap -\partial = \emptyset
$$

These collapse the 2^4 = 16 abstract memberships into exactly 6 per-literal outcomes A-F:

| Outcome | Memberships | Sample theory |
|---------|-------------|---------------|
| A | ⊬ -Δp and ⊬ +∂p | p → p |
| B | ⊢ +∂p, ⊬ +Δp, ⊬ -Δp | ⇒ p; p → p |
| C | ⊢ +Δp (and ⊢ +∂p) | → p |
| D | ⊢ +∂p and ⊢ -Δp | ⇒ p |
| E | ⊢ -Δp, ⊬ +∂p, ⊬ -∂p | p ⇒ p |
| F | ⊢ -∂p (and ⊢ -Δp) | ∅ (empty theory) |

Venn structure (Figure 1, p.8): left ellipse +∂ contains B,C,D; inner ellipse +Δ is C; right ellipse -Δ contains D,E,F; inner ellipse -∂ is F.

## Joint Outcomes for (p, ¬p) (p.8-9)

Per-pair outcome admits 36 candidates; Proposition 1 prunes to 21 admissible joint outcomes (16 in acyclic theories). Proposition 1:
1. If ⊬ -Δ¬p and ⊬ +Δp then ⊬ +∂p.
2. If ⊢ +Δ¬p and ⊢ -Δp then ⊢ -∂p.
3. If ⊢ +∂¬p and ⊢ -Δp and ⊬ -∂p, then D is cyclic.

Properties 1, 2, 3 yield the impossibility-table on p.9 (Poss / NP(1) / NP(2) / NP(3)). NP(3) entries are realizable only via cyclic >. The five cyclic-only joint outcomes are DD, BE, DE and reverses.

Sample cyclic theories (p.9-10):
- DD: r1: ⇒ p, r2: ⇒ ¬p, r1 > r2, r2 > r1.
- BE: r1: p ⇒ p, r2: ⇒ ¬p, r3: ¬p → ¬p, r1 > r2, r2 > r1.
- DE: r1: p ⇒ p, r2: ⇒ ¬p, r1 > r2, r2 > r1.

## Theorem 2 (p.10)
- **Acyclic case:** every acyclic defeasible theory D is conclusion-equivalent to a theory D' that contains no use of the superiority relation and no defeaters.
- **Cyclic case:** every cyclic D is conclusion-equivalent to a D' with no defeaters, whose cycles (if any) have length 2 and involve exactly the two rules for some literal and its complement.

Acyclicity is justified ex post: cyclic > buys at most 5 extra joint-outcome pairings (DD, BE, DE and reverses), all of which the authors describe as "of no practical usefulness" (p.10).

## Modularity and Incrementality (p.10–onward)

A *transformation* T : D ↦ T(D) is a mapping between defeasible theories.
- **Modularity:** T is modular iff T can be applied per-unit-of-information (per rule / per fact) without notifying or recomputing the rest. Equivalently: T(D ∪ X) = T(D) ∪ T(X) up to a fixed harmless prelude.
- **Incrementality:** the cost of obtaining T(D ∪ {edit}) given T(D) is proportional to the size of the edit, not |D|.

Both properties are required for an implementation that supports interactive theory editing without re-evaluating the whole knowledge base.

For each transformation in §5 the paper:
1. Exhibits the transformation.
2. Proves correctness (D ≡_Σ T(D)).
3. Proves modularity / incrementality where they hold.
4. When (3) fails, proves *no* correct transformation can satisfy the property — a non-existence result.

## Modularity / Incrementality / Correctness — Formal Defs (Section 4, p.10-11)

- **Correctness:** T is correct iff for every defeasible theory D, D ≡_Σ T(D), where Σ is the language of D *(p.11)*.
- **Incrementality:** T is incremental iff for all D1, D2: T(D1 ∪ D2) ≡_Σ T(D1) ∪ T(D2), where Σ = language(D1) ∪ language(D2) *(p.11)*.
- **Modularity:** T is modular iff for all D1, D2: D1 ∪ D2 ≡_Σ T(D1) ∪ D2, with Σ as above *(p.11)*.

**Proposition 4 (p.11):** Modular ⇒ correct AND incremental. Inverse fails (Proposition 8 below provides a witness).

## Section 5.1 — Normalization (eliminate facts, separate strict/defeasible)

**Definition 5 (p.12) — Normalized theory.** D = (F, R, >) is normalized iff:
  (a) every literal is defined either solely by strict rules, or by exactly one strict rule plus other non-strict rules;
  (b) no strict rule participates in >;
  (c) F = ∅.

**Definition 6 (p.12) — Transformation `normal`.** Let `'` map propositions → fresh propositions and rule names → fresh rule names (extended pointwise to literals/conjunctions). Then `normal(D) = (∅, R', >)` where:

$$
R' = R_d \cup R_{dft} \cup \{\to f' \mid f \in F\} \cup \{r' : A' \to C' \mid r : A \to C \in R_s\} \cup \{r : A \Rightarrow C \mid r : A \to C \in R_s\} \cup \{p' \to p \mid (A \to p) \in R \text{ or } p \in F\}
$$

Each fresh rule (from F or of form p' → p) gets a distinct fresh name. Strict rules become defeasible in their original-name copy, while a primed-language strict-only twin (r') preserves definite reasoning. > is unchanged but no longer touches any strict rule.

**Theorem 7 (p.13) — `normal` is correct.** Proof by induction on length of derivation, splitting on tag (+Δ, -Δ, +∂, -∂); both directions D ⊢ q ⇔ normal(D) ⊢ q for q in the original language Σ.

**Proposition 8 (p.14) — `normal` is incremental but not modular.**
- Incremental because normal(D1) ∪ normal(D2) = normal(D1 ∪ D2).
- Not modular: D1 = {a → b}, D2 = {→ a}. Then D1 ∪ D2 ⊢ +Δb but normal(D1) ∪ D2 ⊢ -Δb (the primed `a'` rule is missing).

This witnesses that the inverse of Proposition 4 fails.

## Section 5.2 — Eliminating the Superiority Relation (`elim_sup`)

**Idea (p.14):** introduce per-rule fresh atoms inf+(r), inf−(r). Intuitively ¬inf+(r) means "r is not inferior to any applicable strict/defeasible rule"; ¬inf−(r) means "r is not inferior to any applicable rule (including defeaters)". Use defeasible rules over these fresh atoms to *simulate* superiority by attacking inferences.

**Definition 9 (p.14).** For normal D = (∅, R, >):

$$
elim\_sup(D) = (\emptyset, R', \emptyset)
$$

where R' = R_s ∪ {¬inf+(r1) ⇒ inf+(r2), ¬inf−(r1) ⇒ inf−(r2) | r1 > r2} ∪ {A(r) ⇒ ¬inf+(r), ¬inf+(r) ⇒ p, A(r) ⇒ ¬inf−(r), ¬inf−(r) ⇒ p | r ∈ R_d[p]} ∪ {A(r) ⇒ ¬inf−(r), ¬inf−(r) ⤳ p | r ∈ R_dft[p]}.

The two predicates (inf+ vs inf−) are split because defeaters cannot serve as positive support — they only attack — so the third "phase" of a defeasible proof needs a stronger non-inferiority witness.

The transformation is contrasted with Brewka-style priority elimination in credulous abstract argumentation (ref 12) — that approach does not handle defeaters correctly. An earlier author variant (ref 2) worked for a DL flavour where defeaters could counterattack.

**Example 3 (p.15) — Genetically altered penguin.** Demonstrates `elim_sup` in action on the well-known example with rules r1: → gap, r2: gap → p, r3: p → b, r4: b ⇒ f, r5: p ⇒ ¬f, r6: gap ⤳ f, r5 > r4, r6 > r5.

### `elim_sup` properties (p.15-21)

**Distinctness condition (p.16):** D1 = (F1, R1, >1) and D2 = (F2, R2, >2) are *distinct* iff for i = 1, 2: if (r, r') ∈ >_i then neither r nor r' is in R_{3-i}. (Theory cross-superiority cannot reach into the partner theory's rule set.)

**Theorem 10 (p.16) — `elim_sup` is modular** for distinct well-formed normalized theories. Proof by induction on derivation length, splitting on cases r ∈ R1 vs r ∈ R2, walking back through the >-chain by acyclicity, repeatedly applying clause (2.3.2) of +∂. Modularity ⇒ incremental.

**Corollary 11 (p.21):** `elim_sup` is correct on well-formed normalized theories.

**Theorem 12 (p.21) — Negative result for cyclic theories.** No correct, incremental T can satisfy T(D) = (F', R', ∅) on cyclic D in general. Witness: D1 = (∅, r1: ⇒ p, r1 > r2), D2 = (∅, r2: ⇒ ¬p, r2 > r1). D = D1 ∪ D2 cyclic with both +∂p and +∂¬p; T(D1) ∪ T(D2) is acyclic so by consistency cannot have both, contradiction. Hence no modular such T either (by Prop 4).

**Theorem 13 (p.21) — Negative result for non-distinct theories.** Even acyclic D admits no *modular* sup-eliminator in general. Witness: D = {r1: ⇒ p, r2: ⇒ ¬p, r1 > r2}, partition into D1 = rules and D2 = {r1 > r2}. Modularity would require D ≡_Σ D1 ∪ T(D2); but D ⊢ +∂p while D1 ∪ T(D2) ⊢ -∂p (no superiority).

So acyclicity AND distinctness are *both* required for any modular sup-eliminator.

## Section 5.3 — Eliminating Defeaters (`elim_dft`)

**Definition 14 (p.22).** For each atom p ∈ Σ introduce fresh atoms p+ (proof carrier) and p− (attack carrier). Define elim_dft(D) = (F, R', >'):

For each rule r in R, elim_dft(r) splits by rule kind and head polarity:
- r ∈ R_s[p]: {r+: A(r) → p+, r−: A(r) → ¬p−, r: p+ → p}
- r ∈ R_s[¬p]: {r−: A(r) → p−, r+: A(r) → ¬p+, r: p− → ¬p}
- r ∈ R_d[p]: {r+: A(r) ⇒ p+, r−: A(r) ⇒ ¬p−, r: p+ ⇒ p}
- r ∈ R_d[¬p]: {r−: A(r) ⇒ p−, r+: A(r) ⇒ ¬p+, r: p− ⇒ ¬p}
- r ∈ R_dft[p]: {r: A(r) ⇒ ¬p−}  (defeater becomes only an attacker on p−)
- r ∈ R_dft[¬p]: {r: A(r) ⇒ ¬p+}  (defeater becomes only an attacker on p+)

Superiority lifted: r' >' s' iff ∃r,s ∈ R such that r' ∈ elim_dft(r), s' ∈ elim_dft(s), r > s, and r', s' have conflicting heads.

Intuition: p+ behaves like p; p− behaves like ¬p. A defeater A(r) ⤳ p only attacks ¬p, never supports p. Its translation A(r) ⇒ ¬p− carries that semantics. Defeasible rules become twofold (support + attack on the dual).

**Example 4 (p.22):** Re-applies elim_dft to the genetically altered penguin theory.

**Theorem 15 (p.23-26) — `elim_dft` is correct.** Proof by induction on proof length, split into ±Δ and ±∂ cases. Uses an Auxiliary Lemma (p.24) establishing four bidirectional translations between provability of ±∂p in D and provability of ±∂p+ in elim_dft(D), and likewise between ±∂¬p and ±∂p−.

**Proposition 16 (p.26) — `elim_dft` is incremental but not modular.** Witness for non-modularity: D1 = {⤳ p}, D2 = {⇒ ¬p}. D1 ∪ D2 ⊢ -∂¬p (the defeater attacks the rule); but elim_dft(D1) = {⇒ ¬p−}, so elim_dft(D1) ∪ D2 ⊢ +∂¬p — a different conclusion in the language Σ = {p}.

**Theorem 17 (p.26-27) — Negative result: no modular defeater eliminator.** Even taking R as an already-normalized, sup-eliminated theory (∅, R, ∅), there is *no* modular T that produces a defeater-free equivalent. Auxiliary Lemma proof goes by contradiction over three witness theories R = ∅, R = {⇒ p}, R = {⇒ ¬p}: any candidate R' that simulates {⤳ p} must simultaneously support certain conclusions in each of the three contexts, and Billington's stability result (ref [6]: it is impossible to derive both +∂p and -∂p) forces a contradiction.

## Section 5.4 — A Minimal Set of Ingredients (p.27-28)

**Theorem 18 (p.27-28).** For every well-formed defeasible theory D = (F, R, >) over Σ, an effective procedure constructs a normalized D' = (∅, R', ∅) with R'_dft = ∅ and identical conclusions on Σ. The procedure is the composition: 1. `normal`, 2. `elim_dft`, 3. `elim_sup`.

**Proposition 19 (p.28) — No correct strict-rule eliminator.** Witness: R = {→ p}. R ⊢ +Δp; any T(R) without strict rules cannot prove +Δ.

**Proposition 20 (p.28) — No correct defeasible-rule eliminator.** Witness: R = {⇒ p}. R ⊢ +∂p but ⊬ +Δp. Any T(R) using only strict rules either proves both or neither.

So strict rules and defeasible rules are *the* irreducible kernel of DL — facts, defeaters, and superiority are inessential.

### Simplified Proof Theory (p.28)

After all three transformations, F = ∅, R_dft = ∅, > = ∅. The +∂ and -∂ inference conditions collapse into a much simpler form (no superiority comparison, no defeater check):

**+∂ (simplified):** P(i+1) = +∂q iff either (1) +Δq ∈ P(1..i), or
(2) (2.1) ∃r ∈ R[q] ∀a ∈ A(r): +∂a ∈ P(1..i) and
       (2.2) -Δ~q ∈ P(1..i) and
       (2.3) ∀s ∈ R[~q] ∃a ∈ A(s): -∂a ∈ P(1..i).

**-∂ (simplified):** P(i+1) = -∂q iff (1) -Δq ∈ P(1..i) and
(2) (2.1) ∀r ∈ R[q] ∃a ∈ A(r): -∂a ∈ P(1..i) or
       (2.2) +Δ~q ∈ P(1..i) or
       (2.3) ∃s ∈ R[~q] ∀a ∈ A(s): +∂a ∈ P(1..i).

Compare to the original (p.4-5) with its nested superiority test t > s in (2.3.2) and its split between R_sd and R_dft. Here the "every attack must be counterattacked by a strictly stronger rule" clause becomes simply "every attack must be discarded" — because superiority is empty and defeaters are gone.

### Implementation footprint (p.29 Conclusion)
- Linear-time consequence computation on the normal form (Maher, Rock, Antoniou, Billington, Miller — ref [13], the **Delores** system).
- Transformations cause only *linear* size blow-up: factor 3 for normalization, factor 4 for superiority elimination, factor 3 for defeater elimination (on top of one another, multiplicatively bounded but linear in input).
- Implementation discipline therefore: input theory → normal → elim_dft → elim_sup → linear-time evaluator.

## Theorems / Propositions / Lemmas — Master Index

| # | Statement | Page |
|---|-----------|------|
| Prop 1 | Three structural impossibility laws on (p, ¬p) joint outcomes | 8 |
| Theorem 2 | Acyclic D ≡ defeater-free, sup-free D'; cyclic D ≡ defeater-free D' with only length-2 cycles | 10 |
| Prop 3 | Acyclic D + ⊢ +∂p + ⊢ +∂¬p ⇒ ⊢ +Δp and ⊢ +Δ¬p | 10 |
| Prop 4 | Modular ⇒ correct + incremental | 11 |
| Def 5 | Normalized theory: per-literal mostly-strict-or-mostly-defeasible, no strict in >, F = ∅ | 12 |
| Def 6 | `normal` transformation construction | 12 |
| Theorem 7 | `normal` is correct | 13 |
| Prop 8 | `normal` is incremental but not modular | 14 |
| Def 9 | `elim_sup` transformation with inf+/inf− atoms | 14 |
| Theorem 10 | `elim_sup` is modular for distinct well-formed normalized theories | 16 |
| Cor 11 | `elim_sup` is correct on well-formed normalized theories | 21 |
| Theorem 12 | No correct + incremental sup-eliminator for cyclic theories | 21 |
| Theorem 13 | No modular sup-eliminator for non-distinct theory pairs | 21 |
| Def 14 | `elim_dft` transformation with p+/p− atoms | 22 |
| Theorem 15 | `elim_dft` is correct | 23 |
| Prop 16 | `elim_dft` is incremental but not modular | 26 |
| Theorem 17 | No modular defeater-eliminator (even on already-normalized + sup-eliminated theories) | 26 |
| Theorem 18 | Composition `normal` ∘ `elim_dft` ∘ `elim_sup` produces normalized defeater-free sup-free equivalent | 27 |
| Prop 19 | No correct strict-rule eliminator | 28 |
| Prop 20 | No correct defeasible-rule eliminator | 28 |

## Testable Properties (for propstore implementation)

- **TP1:** For acyclic D, `normal(elim_dft(elim_sup(D)))` (after wrapping into a normalized form) computes the same set of {+Δ, -Δ, +∂, -∂}-tagged literals on Σ as D *(p.27)*.
- **TP2:** All three transformations are size-linear in input theory: blow-up factors 3, 4, 3 *(p.29)*.
- **TP3:** Inversion of Proposition 4 fails: there exist correct + incremental transformations that are not modular (witness: `normal`, `elim_dft`) *(p.14, 26)*.
- **TP4:** No defeater-eliminating transformation can be modular *(p.26)*.
- **TP5:** No sup-eliminating transformation is correct + incremental on cyclic theories in general *(p.21)*.
- **TP6:** Strict rules and defeasible rules are mutually irreducible — neither can be eliminated by any correct transformation *(p.28)*.
- **TP7:** Per-literal outcome ∈ {A, B, C, D, E, F}; per-pair (p, ¬p) outcome admits exactly 21 cyclic-theory cases or 16 acyclic cases *(p.7-9)*.
- **TP8:** For acyclic D, the defeasible part is consistent: not both ⊢ +∂p and ⊢ +∂¬p unless both ⊢ +Δp and ⊢ +Δ¬p (Billington stability via Prop 3) *(p.10)*.

## Limitations
- The transformations are correctness-preserving but not in general modular without strong side conditions (acyclicity + distinctness for elim_sup).
- The cyclic case is mostly avoided. Cyclic theories can produce 5 extra joint outcomes (DD, BE, DE and reverses) but the authors classify these as having no practical use, so the work treats acyclic theories as the regime of interest.
- The transformations introduce many fresh propositions/labels (linear blow-up). Performance gain comes from the simplified evaluator on the normal form, not from saving memory.
- Sceptical-only: the paper analyzes sceptical (single-extension-style) DL semantics. Credulous variants are out of scope.

## Design Rationale
- **Sceptical, not credulous.** "Strict rules can also be used to show defeasible provability" because the calculus needs strict knowledge to discharge defeasible attackers.
- **Local priorities.** > is meaningful only on rules with complementary heads. Other > pairs are tolerated but inert. This is what makes superiority eliminable by per-rule local rewrites.
- **Defeaters cannot support.** This is preserved through `elim_dft`: A(r) ⤳ p translates to A(r) ⇒ ¬p− (attack only), never to A(r) ⇒ p+ (support).
- **Two indices inf+ vs inf−.** Defeater asymmetry forces splitting non-inferiority into "not inferior to a strict/defeasible rule" (positive support phase) vs "not inferior to any rule including defeaters" (counterattack phase).
- **Loop-free, no fixpoint.** The proof theory uses a purely definitional sequence-based derivation (no Kripke-Kleene fixpoint, no well-founded semantics). Trade-off: ⊢ -Δp may fail on D = {p → p}.
- **Consistency by acyclicity.** Acyclic D ⇒ defeasible part consistent. The five DL-only cyclic joint outcomes are ruled out as "of no practical usefulness."

## Notable References Cited (page citations refer to the references list, p.29-30)

| Ref | Authors / Title / Venue |
|-----|-------------------------|
| [1] | G. Antoniou. *Nonmonotonic Reasoning*. MIT Press 1997. |
| [2] | Antoniou, Billington, Maher. Normal Forms for Defeasible Logic. JICSLP 1998, MIT Press, 160-174. |
| [3] | Antoniou, Billington, Maher. On the analysis of regulations using defeasible rules. HICSS 1999. |
| [4] | Antoniou, Maruyama, Masuoka, Kitajima. Issues in Intelligent Information Integration. IASTED 1999. |
| [5] | Antoniou, Maher, Billington. Defeasible Logic versus Logic Programming without Negation as Failure. JLP 41(1), 2000, 45-57. — **the sister paper Antoniou_2000_DefeasibleLogicVersusLogic** |
| [6] | D. Billington. Defeasible Logic is Stable. JLC 3, 1993, 370-400. |
| [7] | E.F. Codd. Further Normalization of the Data Base Relational Model. 1972. |
| [8] | Covington, Nute, Vellino. Prolog Programming in Depth. Prentice Hall 1997. |
| [9] | Dimopoulos, Kakas. Logic Programming without Negation as Failure. ISLP 1995, MIT Press, 369-384. |
| [10] | B.N. Grosof. Prioritized Conflict Handling for Logic Programs. ILPS 1997, 197-211. |
| [11] | Grosof, Labrou, Chan. A Declarative Approach to Business Rules in Contracts: Courteous Logic Programs in XML. EC-99, ACM 1999. |
| [12] | Kowalski, Toni. Abstract Argumentation. AI & Law 4(3-4), Kluwer 1996. |
| [13] | Maher, Rock, Antoniou, Billington, Miller. Efficient defeasible reasoning systems. CL 2000. — **the Delores implementation paper** |
| [14] | Marek, Truszczynski. Nonmonotonic Reasoning. Springer 1993. |
| [15] | D. Nute. Defeasible Reasoning. HICSS 1987, 470-477. |
| [16] | D. Nute. Defeasible Logic. In Handbook of Logic in AI and LP Vol. 3, OUP 1994, 353-395. |
| [17] | Pettorossi, Proietti. Transformation of Logic Programs. JLP 19/20, 1994, 261-320. |
| [18] | Reeves, Grosof, Wellman, Chan. Towards a Declarative Language for Negotiating Executable Contracts. AIEC-99, AAAI/MIT 1999. |
| [19] | J.A. Robinson. A machine oriented logic based on the resolution principle. JACM 12(1), 1965, 23-41. |
| [20] | A. Rock. Deimos: Query Answering Defeasible Logic System. http://www.cit.gu.edu.au/~arock/defeasible/Defeasible.cgi |

Acknowledgments note: this paper extends earlier work at AI'98 (11th Australian Joint Conference on Artificial Intelligence) and JICSLP'98. Funded by ARC Large Grant A49803544.

## Open Questions
- [ ] Does the simplified proof theory of §5.4 admit a fixpoint / well-founded semantics characterization that would handle loops (e.g., D = {p → p})?
- [ ] Are the 5 cyclic-only joint outcomes (DD, BE, DE and reverses) really useless? They might map onto "paradoxical disagreement" cases that propstore's IC merge layer might want to represent.
- [ ] Can the linear-time Delores algorithm be adapted to compute *only the queried literal* with sub-linear cost (i.e., goal-directed query mode like Deimos)?

## Collection Cross-References

### Already in Collection (cited by this paper)

- [Defeasible logic versus Logic Programming without Negation as Failure](../Antoniou_2000_DefeasibleLogicVersusLogic/notes.md) — cited as ref [5]; the sister paper by the same author group, published the same year. The 2000 JLP paper compares DL against LPwNF expressively (`±Δ / ±∂` proof tags); this 2001 ACM TOCL paper uses the same proof system and proves *representation-theoretic* results about which DL features are eliminable. Together they form the canonical formal foundation that propstore's `propstore.defeasibility` module inherits: 2000 establishes "what tags exist and how they fire," 2001 establishes "which primitives are essential and which are syntactic sugar."

### Cited By (in Collection)

- [A Defeasible Logic-based Framework for Contextualizing Deployed Applications](../Al-Anbaki_2019_DefeasibleLogicContextualizingApplications/notes.md) — cites this paper as ref [13] for "representation-theoretic grounding for the proof system." Al-Anbaki et al.'s `L = ⟨G, β, D, λ⟩` framework reuses exactly the DL primitives this paper proves are inessential vs essential — so any propstore engine that wants to normalize Al-Anbaki-style theories before reasoning has formal license here.
- [Revision of Defeasible Logic Preferences](../Governatori_2012_RevisionDefeasibleLogicPreferences/notes.md) — cites this paper as ref [12] for "equivalence-preserving normalisations used in footnote 2." Governatori et al. extend DL with eight new auxiliary proof tags ($\pm\Sigma, \pm\sigma, \pm\omega, \pm\varphi$) for revising the superiority relation — and the eliminability of `>` proven in the present paper is what makes their revision question well-posed (revising `>` is non-trivial only because `>` is not freely eliminable in the modular sense; this paper's Theorem 13 supplies the precise non-existence statement).

### Conceptual Links (not citation-based)

- [Defeasible logic versus Logic Programming without Negation as Failure](../Antoniou_2000_DefeasibleLogicVersusLogic/notes.md) — Strong (also cited; doubled here for the conceptual link). The two papers are complementary halves of the same formal program: 2000 places DL in the LPwNF landscape and proves DL ⊋ sceptical LPwNF via the team-of-rules mechanism; 2001 takes the same calculus and proves which of its primitives carry expressive weight. Anyone implementing DL needs both.
- [Revision of Defeasible Logic Preferences](../Governatori_2012_RevisionDefeasibleLogicPreferences/notes.md) — Strong. The negative results in §5.2 (Theorems 12, 13: no modular sup-eliminator exists in general) are *exactly* the obstruction Governatori 2012 routes around by introducing dedicated revision tags rather than trying to compile away `>`. Reading them in sequence: Antoniou 2001 says "you cannot factor `>` out modularly," Governatori 2012 says "fine, then let's reason about how to *revise* `>` in place."
- [A Defeasible Logic-based Framework for Contextualizing Deployed Applications](../Al-Anbaki_2019_DefeasibleLogicContextualizingApplications/notes.md) — Strong. Al-Anbaki et al.'s per-authority `D^A`, `D^B` partition with global priority `λ` is structurally a multi-context DL theory; this paper's normalization theorems apply per-authority before the global priority is consulted, providing a clean reasoning pipeline.

## Workflow Checkpoint (paper-process, 2026-05-07)

**State of the world:**
- All 30 page images read (page-000 through page-029).
- All paper artifacts written: notes.md (this file, exhaustive across all sections, all theorems / propositions / transformations / negative results indexed), abstract.md, description.md, citations.md, metadata.json (fetcher-generated, captures DOI 10.1145/371316.371517 + arxiv cs/0003082).
- papers/index.md updated with the new entry inserted alphabetically right after the existing `Antoniou_2000_DefeasibleLogicVersusLogic` entry.
- Reconcile work in progress on Al-Anbaki_2019 (the citing paper):
  - Inline "Related Work Worth Reading" entry annotated with `→ NOW IN COLLECTION:` link.
  - "New Leads" entry struck through and rewritten with substantive synopsis pointing to this paper's notes.
  - Unprocessed-leads count updated from 9 to 8 in the post-parallel-swarm checkpoint.
- Identified additional reverse cited-by edge: Governatori_2012_RevisionDefeasibleLogicPreferences cites this paper as ref [12] (already noted in Governatori_2012/notes.md line 443 and citations.md line 16) — needs forward annotation to be added in the new paper's Cited-By section.

**Done as of this checkpoint:**
- `Already in Collection`, `Cited By (in Collection)`, `Conceptual Links` sections added to this paper's notes.
- Governatori_2012/notes.md ref [12] mention upgraded to bidirectional → NOW IN COLLECTION cross-link with substantive synopsis.
- Al-Anbaki_2019/notes.md inline "Related Work Worth Reading" annotated; "New Leads" entry struck through with substantive synopsis; unprocessed-leads count corrected from 9 → 8.
- Antoniou_2000_DefeasibleLogicVersusLogic/notes.md updated with a `Sister Paper` section pointing to this paper (same authors, same year, same DL calculus, complementary halves of the canonical formal program).

**Blocker:** none. Reconcile complete. All bidirectional cross-references in place between the new paper and its three collection partners (Antoniou_2000, Governatori_2012, Al-Anbaki_2019).

## Relevance to propstore
Foundational: propstore's defeasibility layer (`propstore.defeasibility`) and ASPIC+ bridge sit on top of exactly this DL machinery. The four-tag proof theory (+Δ, -Δ, +∂, -∂) is the calculus that justifiable-exceptions-style CKR layering uses. Theorem 2 says we can implement a normalized engine — strict + defeasible rules only, no defeaters, empty superiority — without losing expressive power for acyclic theories, which is the regime propstore commits to (acyclic priority + complementary-head locality already in scope).
