---
title: "What does a conditional knowledge base entail?"
authors: "Daniel Lehmann, Menachem Magidor"
year: 1989
venue: "Artificial Intelligence"
doi_url: "https://doi.org/10.1016/0004-3702(92)90041-U"
pages: "212-222 (journal); arXiv version 58pp"
affiliations: "Hebrew University, Jerusalem (Lehmann: CS; Magidor: Math)"
note: "arXiv preprint cs/0202022 v1, 18 Feb 2002, of the 1989/1992 AI Journal article"
produced_by:
  agent: "claude-opus-4-7"
  skill: "paper-reader"
  status: "stated"
  timestamp: "2026-04-28T07:47:45Z"
---
# What does a conditional knowledge base entail?

## One-Sentence Summary
Defines *rational closure* of a conditional knowledge base K — the unique ≺-minimal rational consequence relation extending K — as a tractable, well-behaved answer to "what does K entail?" in nonmonotonic propositional reasoning, with representation theorems linking System P + Rational Monotonicity to ranked preferential models, Adams probabilistic semantics, and non-standard probability semantics. *(p.1, p.26, p.27)*

## Problem Addressed
Given a propositional conditional knowledge base K (set of pairs α |~ β, "from α typically conclude β"), determine which conditional assertions are entailed by K under nonmonotonic reasoning. The minimal preferential closure K^p of Kraus-Lehmann-Magidor 1990 (System P) under-generates: it is not in general *rational* and fails Rational Monotonicity. The maximal extension is trivial. The paper supplies a principled middle: rational closure K̄. *(p.1-3, p.18, p.27)*

## Key Contributions
- Identifies *Rational Monotonicity* (eq.12, p.17) as the missing rationality principle and defines *rational consequence relations* = preferential + RM. *(p.18)*
- Representation theorem (Theorem 5, p.21): rational consequence relations ↔ *ranked* preferential models (modular strict partial orders). *(p.19-21)*
- Theorem 6 (p.23): the intersection of all rational extensions of K equals K^p — so the simple "intersect all rationals" definition collapses, motivating choice-based rational closure.
- Defines a strict partial order ≺ on rational consequence relations via attack/defense semantics (Definition 20, p.29). *(p.29-31)*
- **Definition 21 (p.31):** rational closure K̄ = the unique ≺-minimal rational extension of K (when one exists).
- **Theorem 7 (p.34):** for *admissible* K (Definition 11, p.12), K̄ exists and equals the set of α|~β with rank(α) < rank(α∧¬β) (or α has rank but α∧¬β does not), or α has no rank.
- Polynomial-time-relative-to-SAT algorithm for rational closure (Section 5.8, p.38), reducing exceptional checks to propositional entailment via material counterparts (Lemma 33, Cor 6).
- Cumulativity / reciprocity / loop properties for the rational-closure operator (Lemmas 28–30, Cors 4–5, p.33-34).
- Equivalence: ranked entailment = preferential entailment K^p (Theorem 6, p.23) — a negative result motivating the chosen-extension approach.
- Adams probabilistic entailment recovered: Lemmas 19–22 (pp.24-25); rational relations exactly correspond to non-standard probabilistic models (Appendix B, Theorems 10, 11, p.53-58).
- Demonstrates rational closure on Nixon Diamond and Penguin Triangle examples and identifies the *inheritance failure* (rational closure does not inherit generic properties to exceptional subclasses; Swedes-blond example, p.41).
- Strengthens conjectured answer: **Thesis 2 (p.41)** — any reasonable answer is a rational *superset* of K̄.

## Methodology
Pure logic: propositional language L over a set of variables; conditional assertions α |~ β as syntactic pairs; consequence relations as binary relations on L. Two semantic frameworks: (a) preferential and ranked structures with a strict (modular) partial order on states each labeled by a world, smoothness condition; (b) non-standard probability spaces over R*. Proof-theoretic side: System P (Rules 1-6 = LLE, RW, Reflexivity, And, Or, CM) plus Rational Monotonicity; soundness/completeness via Henkin-style construction over equivalence classes by exceptionality.

## Key Equations / Statistical Models / Inference Rules

### System P inference rules (Definition 1, p.5)

$$\frac{\models \alpha \leftrightarrow \beta,\ \alpha\,|\!\sim\,\gamma}{\beta\,|\!\sim\,\gamma} \quad \text{(LLE, eq.1)}$$ *(p.5)*

$$\frac{\models \alpha \to \beta,\ \gamma\,|\!\sim\,\alpha}{\gamma\,|\!\sim\,\beta} \quad \text{(RW, eq.2)}$$ *(p.5)*

$$\alpha\,|\!\sim\,\alpha \quad \text{(Reflexivity, eq.3)}$$ *(p.5)*

$$\frac{\alpha\,|\!\sim\,\beta,\ \alpha\,|\!\sim\,\gamma}{\alpha\,|\!\sim\,\beta\wedge\gamma} \quad \text{(And, eq.4)}$$ *(p.5)*

$$\frac{\alpha\,|\!\sim\,\gamma,\ \beta\,|\!\sim\,\gamma}{\alpha\vee\beta\,|\!\sim\,\gamma} \quad \text{(Or, eq.5)}$$ *(p.5)*

$$\frac{\alpha\,|\!\sim\,\beta,\ \alpha\,|\!\sim\,\gamma}{\alpha\wedge\beta\,|\!\sim\,\gamma} \quad \text{(Cautious Monotonicity, eq.6)}$$ *(p.5)*

### Derived (preferential) rules

$$\frac{\alpha\wedge\beta\,|\!\sim\,\gamma}{\alpha\,|\!\sim\,\beta\to\gamma} \quad \text{(S, eq.7)}$$ *(p.6)*

$$\frac{\alpha\wedge\beta\,|\!\sim\,\gamma,\ \alpha\,|\!\sim\,\beta}{\alpha\,|\!\sim\,\gamma} \quad \text{(Cut Gentzen-form, eq.8)}$$ *(p.6)*

The unrestricted Cut form (eq.9) is rejected because it implies Monotonicity. *(p.6)*

### Rationality rules

$$\frac{\alpha\wedge\gamma\,|\!\not\sim\,\beta,\ \alpha\wedge\neg\gamma\,|\!\not\sim\,\beta}{\alpha\,|\!\not\sim\,\beta} \quad \text{(Negation Rationality, eq.10)}$$ *(p.16)*

$$\frac{\alpha\,|\!\not\sim\,\gamma,\ \beta\,|\!\not\sim\,\gamma}{\alpha\vee\beta\,|\!\not\sim\,\gamma} \quad \text{(Disjunctive Rationality, eq.11)}$$ *(p.16)*

$$\frac{\alpha\wedge\beta\,|\!\not\sim\,\gamma,\ \alpha\,|\!\not\sim\,\neg\beta}{\alpha\,|\!\not\sim\,\gamma} \quad \text{(Rational Monotonicity, eq.12)}$$ *(p.17)*

Implications: Monotonicity ⇒ DisjRat ⇒ NegRat (Lemma 10, p.16). Rational ⇒ DisjRat (Lemma 12, p.18). DisjRat ⇏ Rational (Lemma 13 Makinson, p.18). NegRat ⇏ DisjRat (Lemma 11, p.16-17).

### Derived ranked rules (Lemma 16, p.20)

$$\frac{\alpha\,|\!\sim\,\textbf{false}}{\alpha\wedge\beta\,|\!\sim\,\textbf{false}} \quad \text{(eq.14)}$$ *(p.20)*

$$\frac{\alpha\vee\beta\,|\!\sim\,\neg\beta}{\alpha\,|\!\sim\,\neg\beta} \quad \text{(eq.15)}$$ *(p.20)*

$$\frac{\alpha\vee\beta\vee\gamma\,|\!\sim\,\neg\alpha\wedge\neg\beta}{\beta\vee\gamma\,|\!\sim\,\neg\beta} \quad \text{(eq.16)}$$ *(p.20)*

$$\frac{\alpha\vee\beta\,|\!\sim\,\neg\alpha}{\alpha\vee\beta\vee\gamma\,|\!\sim\,\neg\alpha} \quad \text{(eq.17)}$$ *(p.20)*

$$\frac{\alpha\vee\gamma\,|\!\sim\,\neg\alpha,\ \beta\vee\gamma\,|\!\not\sim\,\neg\beta}{\alpha\vee\beta\,|\!\sim\,\neg\alpha} \quad \text{(eq.18, Lemma 17, p.21)}$$

### Adams' probabilistic semantics (Definition 17, p.24)

K probabilistically entails A iff for every ε>0 there exists δ>0 such that for every probability assignment p proper for K and A, p(B) ≥ 1−δ for all B in K implies p(A) ≥ 1−ε. The conditional probability p(A) = p(α|~β) := p(β|α). *(p.24)*

### Non-standard probability semantics (Appendix B)

$$Pr(B \mid A) = \frac{Pr(A \cap B)}{Pr(A)} \quad \text{(R*-conditional probability)}$$ *(p.52)*

$$Pr^*(A,f)(B) = \frac{\sum^*_{x \in B} f(x)}{\sum^*_{x \in A} f(x)} \quad \text{(hyperfinite probability space, Definition 32)}$$ *(p.52)*

Validity in M: M ⊨ α |~ β iff Pr(α) = 0 or 1 − Pr(β | α) is infinitesimal, equivalently Pr(α) = 0 or Pr(¬β | α) is infinitesimal (Definition 33, p.53).

### Probabilistic measure on a finite ranked model (proof of Lemma 22, p.25)

For state weights w_n (probability mass at rank n), the construction sets w_{n+1}/w_n = ε. As ε→0, conditional probabilities approach 1 for satisfied assertions and stay bounded away from 1 otherwise. *(p.25)*

### Equation 21 (RM proof in non-standard models, p.54)

$$Pr(\neg\gamma \mid \alpha\wedge\beta) = Pr(\neg\gamma \mid \alpha) \times \frac{1}{Pr(\beta \mid \alpha)} \quad \text{when } Pr(\alpha\wedge\beta) > 0$$ *(p.54)*

### Eq 22 (overspill construction, p.56)

$$\frac{\sum_{m<k, r(m) > x} f(m)}{\sum_{m<k, r(m) = x} f(m)} \le \sum_{i=1}^{\infty}\epsilon^i = \frac{\epsilon}{1-\epsilon} \quad \text{(rank-ratio bound for B_n triples)}$$ *(p.56)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Probabilistic entailment lower bound on K | 1−δ | — | — | (0,1) | 24 | Def 17: any ε>0 ↦ some δ>0 |
| Probabilistic entailment lower bound on A | 1−ε | — | — | (0,1) | 24 | Def 17 target |
| Adams properness threshold | p(α) | — | >0 | (0,1] | 24 | Def 15 |
| State-rank weight ratio (finite ranked model probability) | w_{n+1}/w_n | — | ε | (0,1) | 25 | Lemma 22 construction |
| Algorithm exceptional-loop iterations | — | iterations | — | ≤ n | 38-39 | n=|K| |
| Algorithm propositional entailment checks total | — | calls | — | O(n²) | 39 | Section 5.8 |
| Preferential entailment complexity | — | class | co-NP | — | 13, 39 | Theorem 4, Section 2.7 |
| Preferential entailment Horn complexity | — | class | P | — | 15, 39 | Dix's reduction |
| Rank ordinal | τ | ordinal | — | 0..ω+ | 11-12 | Definition 10 |
| Per-formula relative weight ε^{i+1} threshold | — | — | 1/2^{i+1} | (0,1) | 55-56 | App B completeness |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | Population/Context | Page |
|---------|---------|-------|--------------------|------|
| Computing α∈K^p complexity | class | co-NP-complete | finite K, propositional | 13, 15 |
| Horn case complexity | class | polynomial | Horn K, Horn A | 15, 39 |
| Rational closure decision (general) | class | NP via SAT calls (≤O(n²)) | finite admissible K | 39 |
| Rational closure decision (Horn) | class | polynomial | Horn finite K | 39 |
| Adams probabilistic entailment failure on infinite K | counterexample | exists | non-finite | 26 |

## Methods & Implementation Details

- **Preferential model** ⟨S, l, ≺⟩: states S, world labeling l: S→U, strict partial order ≺, smoothness for every formula α (Definition 4, p.7).
- **Ranked model** = preferential model whose strict partial order is *modular*; Lemma 14 (p.19) gives four equivalent characterizations including ranking function r:V→Ω with s≺t iff r(s)<r(t).
- **Rank construction (Definition 10, p.11):** C_0=K; C_{τ+1}=E(C_τ) (exceptional sub-base); limit ordinals: intersection. rank(α) = least τ with α not exceptional for C_τ; "no rank" if exceptional for all C_τ.
- **Exceptionality test (Cor 6, p.38):** α exceptional for K iff K̃ ⊨ ¬α, where K̃ is the *material counterpart* (replace α|~β with α→β, Definition 23 p.38). Reduces to propositional entailment.
- **Rational-closure decision algorithm** (Section 5.8, p.38):
  1. C := K
  2. While α exceptional for C and E(C) ≠ C: C := E(C)
  3. Answer "yes" iff α ∧ ¬β is exceptional for C.
- **Reduction K^p ↔ K̄ (J. Dix, p.39):** α |~ β ∈ K^p iff α |~ false ∈ rational-closure of K ∪ {α|~¬β}. Allows reusing rational-closure algorithm to decide preferential entailment.
- **Witness algorithm for non-entailment (Definition 12, p.14):** sequences (I_k, f_k), I ⊆ {1..N}, f_k worlds; conditions (1)-(6); short witnesses, polynomial in |K|+|A|.
- **Material counterpart Lemma 33 (p.38):** K̃ ⊨ α iff K preferentially entails true|~α — propositional decision suffices.
- **Loop / Reciprocity / Cumulativity (Lemma 28, Cors 4–5, p.33):** if K_{i+1} ⊆ K̄_i for all i (mod n), all closures K̄_i agree; in particular K ⊆ X ⊆ K̄ ⇒ X̄ = K̄.
- **Henkin-style ranked model construction (Appendix A, pp.46-48):**
  - Definition 24 (p.46) normal world for α: m |= α and m |= β whenever α|~β.
  - R-relation αRβ iff α∨β |~/ ¬α (Definition 25, p.46): "α not more exceptional than β".
  - Equivalence classes ᾱ under ~ (αRβ and βRα). < strict total order on E.
  - Ranked model V = pairs ⟨m, α⟩ with m normal world for α; ⟨m,α⟩ ≺ ⟨n,β⟩ iff ᾱ < β̄.
  - Lemmas 38–42 (pp.46-48) verify smoothness and that the model defines exactly |~.
- **Non-standard probabilistic completeness (App B.4, pp.54-58):**
  - Theorem 11 (p.54): for countable L and any rational P, there is a non-standard *neat* R*-probabilistic model M with K(M) = K = P.
  - B_n triples (k, ε, f) with five conditions (p.56) approximate the desired infinitesimal probability assignment; intersection by Robinson Overspill.
  - Per-formula r = 1/2^{i+1} guards relative weight; Σ 1/2^{i+1} = 1.

## Figures of Interest
- No formal numbered figures.
- Examples 1, 2, 3 (pp.31, 39, 40): integer-indexed knowledge base (no rational closure), Nixon diamond, Penguin triangle — these function as the paper's concrete illustrations.

## Results Summary

- System P (preferential consequence) has Theorem 1 representation by preferential models; preferential entailment K^p is co-NP-complete and equals proof-system P closure (Theorem 2).
- *Rational* relations = preferential + RM (Definition 13, p.18); Theorem 5 (p.21) gives bijection with ranked models. Logically finite L → finite ranked model.
- Theorem 6 (p.23): ranked entailment ≡ preferential entailment, so intersection-of-rationals trivializes to K^p — must use a different selection principle.
- Definitions 18-19 (p.28) introduce *supported* and *perfect* rational extensions; Lemma 23 shows perfect rational extensions don't always exist.
- ≺ on rational extensions (Definition 20, p.29) is a strict partial order; rational closure K̄ is the ≺-least element when it exists. Defined for arbitrary K but only guaranteed for *admissible* K (every no-rank formula inconsistent for K).
- For admissible K (in particular finite K, Lemma 7 p.13), K̄ exists and admits both an algorithmic characterization (Theorem 7, p.34) and a rank-based characterization. Rank construction terminates and is invariant under K↔K^p (Lemma 6).
- Computing rational closure: O(n²) propositional-entailment calls; co-NP overall, polynomial for Horn (Section 5.8, p.39).
- Inherits generic properties to *normal* subclasses but not exceptional ones (rational closure is not "deep" inheritance) — known limitation, leads to Thesis 2 (p.41) advocating for rational supersets of K̄.
- Probabilistic semantics (Adams + non-standard) coincide with rational consequence in the appropriate setting; Theorem 11 (p.54) is the completeness result.

## Limitations
- Rational closure does *not* support inheritance of generic properties to exceptional subclasses ("short Swedes blond?" example, p.41). *(p.41)*
- Knowledge bases without rational closure exist (Example 1 pn|~p_{n+2}, pn|~¬p_{n-2}, p.31; Lemma 27 proof p.32).
- Ranked-entailment definition (intersect all ranked extensions) collapses to K^p — so it does *not* by itself give a stronger answer (Theorem 6, p.23). *(p.22-23)*
- Rational closure of perfect-extension form does not always exist (Lemma 23, p.28).
- Approach is propositional only; first-order extension flagged as nontrivial (Section 6, p.42, references [20] for first steps).
- Non-standard probabilistic completeness (Theorem 11) requires *countable* L; an explicit counterexample exists in the uncountable case (p.49). *(p.49)*
- Probabilistic consistency lacks compactness on infinite K (Adams' result, p.26). *(p.26)*

## Arguments Against Prior Work
- Against systems (circumscription [22], modal nonmonotonic logics [23, 24], default logic [29], negation as failure [5]): "not clear that any one of them really captures the whole generality of nonmonotonic reasoning" (p.2). They lack a uniform logical analysis.
- Against intersection-of-all-extensions definitions of entailment for ranked models: collapses to K^p (Theorem 6, p.23). *(p.22-23)*
- Against preferential entailment K^p as final answer: typically not rational; e.g. K = {p|~q} fails to derive p∧r|~q (Section 3.5, p.18-19), an "annoying instance" of RM failure.
- Against Delgrande's logic N (Section 3.7, p.21-22): N lacks Cautious Monotonicity, lacks finite model property; its models do not satisfy smoothness; its entailment notion differs.
- Against unrestricted Cut (eq.9, p.6): implies Monotonicity, so it is rejected; only the Gentzen-restricted form (eq.8) is preserved.
- Against pure Bayesian/probabilistic-only approach (school represented in [3, 2], p.48-49): impractical bookkeeping of conditional probabilities; choice of ε≠0 yields ill-behaved consequence relation; ε=0 collapses to monotonic material implication. Proposes infinitesimal-ε non-standard semantics as resolution.
- Against perfect rational extensions (Definition 19, p.28): Lemma 23 (p.28) shows a finite K with no perfect rational extension exists. So Definition 21 chooses ≺-least extension, not necessarily perfect.

## Design Rationale
- Treat conditional assertions as syntactic primitives, separate from worlds; preferential models give truth values to assertions, not to propositional formulas. (p.2)
- Hard constraints α encoded *softly* as ¬α |~ false rather than restricting U; preserves the rational-closure construction's freedom to add α∧γ |~ β-style new conditionals. (p.6)
- Reject unrestricted Cut to avoid implying monotonicity. (p.6)
- Smoothness condition keeps every α̂ guaranteeing minimal elements without forcing well-foundedness — essential for the representation theorem to hold for arbitrary preferential relations (Lemma 1 shows some have no well-founded model). (p.7)
- Modularity (rather than well-foundedness) is the right structural condition on ranked models; yields the four equivalent characterizations of Lemma 14. (p.19)
- Why Rational Monotonicity: an agent should not retract previously defeasible conclusions on learning a fact whose negation was not previously derivable (p.17). Compared to CV thesis of conditional logic.
- Choose ≺-least rational extension (Definition 21, p.31) rather than intersection (collapses) or supported/perfect (may not exist).
- Reduce rank computation to propositional entailment via material counterparts (Lemma 33, Cor 6) so the algorithm uses standard SAT machinery. (p.38)
- Non-standard probability framework (Appendix B): infinitesimal ε resolves the ε=0 vs ε>0 dilemma in standard probability. *(p.49)*
- Defer to Thesis 2 (p.41): K̄ is a *lower bound* on reasonable answers, leaving room for stronger inheritance-respecting systems.

## Testable Properties
- The rules of System P (1-6, p.5) hold in any preferential consequence relation. *(p.5)*
- Rational consequence relations satisfy Rational Monotonicity, Disjunctive Rationality, Negation Rationality, and all System-P rules. *(p.18)*
- A consequence relation is rational iff it is defined by some ranked preferential model (Theorem 5, p.21).
- For admissible K, K̄ exists and α|~β ∈ K̄ iff rank(α) < rank(α∧¬β), or α has rank but α∧¬β does not, or α has no rank (Theorem 7, p.34).
- α exceptional for K iff K̃ ⊨ ¬α (Cor 6, p.38).
- α|~β preferentially entailed by K iff α|~false preferentially entailed by K∪{α|~¬β} (Cor 3, p.11).
- Rank assignments are invariant under K↔K^p (Lemma 6, p.12).
- Loop property: K_{i+1} ⊆ K̄_i (mod n) for all i ⇒ all K̄_i equal (Lemma 28, p.33).
- Cumulativity: K ⊆ X ⊆ K̄ ⇒ X̄ = K̄ (Cor 5, p.33).
- Reciprocity: X ⊆ Ȳ and Y ⊆ X̄ ⇒ X̄ = Ȳ (Cor 4, p.33).
- K^p ⇒ K-probabilistically-entails (Lemma 20, p.24); for finite probabilistically-consistent K, K-prob-entails ⇒ K^p (Lemma 22, p.25).
- For countable L and rational P, ∃ R*-neat probabilistic model M with K(M) = P (Theorem 11, p.54).
- Penguin triangle: K = {penguin|~bird, penguin|~¬fly, bird|~fly} ⇒ rational closure includes bird∧penguin|~¬fly (preemption), penguin∧black|~¬fly, bird∧green|~fly; excludes bird∧¬fly|~penguin, penguin|~fly. *(p.40)*
- Nixon diamond: K = {republican|~¬pacifist, quaker|~pacifist} ⇒ rational closure excludes both republican∧quaker|~pacifist and republican∧quaker|~¬pacifist; includes worker∧republican|~¬pacifist (irrelevance), pacifist|~¬republican (contraposition), republican|~¬quaker, quaker|~¬republican. *(p.39-40)*

## Relevance to Project

Lehmann-Magidor 1989 is foundational for propstore's argumentation/reasoning layer:

- **System P + RM correspond directly to the inference-rule machinery in `propstore.aspic_bridge` and `aspic.py`.** The defeasible rule machinery and exceptional-formula construction here is the textbook reference for ASPIC+ defeasible inference under preferential ordering.
- **Rank construction (Definition 10, p.11)** maps to propstore's stance/exceptionality bookkeeping: every claim's exceptional rank is computable from the knowledge base and provides an ordinal default-priority that interfaces with rule priorities.
- **Rational closure algorithm (Section 5.8, p.38)** suggests an in-storage materialization strategy: per-claim rank precomputed at build time as a sidecar, then rational-closure membership decided by propositional-entailment checks via material counterparts.
- **Modular/ranked semantics (Theorem 5, p.21)** matches propstore's render-time policy layer — `RenderPolicy` corresponds to a particular ranked extension; multiple render policies = multiple consistent ranked models over the same source corpus.
- **Theorem 6 (p.23)** is a cautionary tale for naive intersection: if propstore's argumentation layer takes "intersect all rational extensions of K", it collapses to K^p. We need a chosen-extension policy (analogous to K̄) at render time, not at storage time, to preserve non-commitment in storage.
- **Thesis 2 (p.41):** any reasonable answer is a *rational superset* of K̄ — strongly aligns with the propstore design principle that "rational closure is a lower bound; multiple render policies may extend it" — supports the system's commitment to lazy / multi-policy rendering.
- **Inheritance failure (Swedes-blond, p.41)** is exactly the kind of situation where propstore's defeasibility / context layer (`propstore.defeasibility`, contextual `ist(c, p)` lifting) needs to interject CKR-style exceptions over rational closure.
- **Adams + non-standard probability (Section 4.3, Appendix B)** validates probabilistic-style claim valuations alongside symbolic ones — supports propstore's commitment to subjective-logic / probabilistic argumentation backends as alternative semantics for the same syntactic claim base.
- **Admissibility (Definition 11, p.12)** is a useful precondition concept for source-bootstrap: when adding new conditional assertions, ensure admissibility so the per-source ranking is well-defined.

## Open Questions
- [ ] Concrete: how to lift propositional rational closure to first-order? (paper defers to [20])
- [ ] What is a propstore-suitable algorithm for inheritance of generic properties to exceptional subclasses (a Thesis-2 superset of K̄)? Pearl's System Z [27], Lehmann's Lexicographic Closure (later work, not in this paper) are natural candidates.
- [ ] Does the rank construction interact stably with multi-source merge (assignment-selection merge / IC merge)? Each source has its own E(C) sequence — how do we reconcile per-source ranks?
- [ ] How does CKR contextual-exception injection interact with rank-based exceptionality? Are CKR exceptions themselves rank-1 assertions in the merged base?
- [ ] In propstore, should rank metadata be a build-time sidecar (rebuild on source change) or a lazy on-demand calculation in the render layer? Lemma 6 (rank invariance under K↔K^p) suggests build-time is safe.
- [ ] Probabilistic backend: Adams' construction (Section 4.3) gives standard probability semantics; the non-standard appendix gives R*-semantics for arbitrary rational. Does subjective-logic encoding sit closer to Adams' standard or to App B's non-standard?

## Related Work Worth Reading
- [17] Kraus, Lehmann, Magidor 1990 — *Nonmonotonic reasoning, preferential models and cumulative logics* — System P origin and primary background. **Already in collection.**
- [27] Pearl 1990 — *System Z* — Pearl's tractable rational-closure variant, in same TARK proceedings.
- [11] Freund, Lehmann, Morris (1991) — *Rationality, transitivity and contraposition* — follow-up rationality results.
- [10] Freund 1991 — *A semantic characterization of disjunctive relations*.
- [21] Makinson 1988 — *General theory of cumulative inference* — cumulative-logic background.
- [1] Adams 1975 — *The Logic of Conditionals* — probabilistic reference for Section 4.3.
- [7], [8] Delgrande (1987, 1988) — first-order conditional / default reasoning system N, compared in Section 3.7.
- [22] McCarthy 1980 — *Circumscription*.
- [29] Reiter 1980 — *A logic for default reasoning*.
- [33] Shoham 1987 — preferential semantics origin.
- [32] Satoh 1989 — alternative probabilistic interpretation of rational relations.
- [20] Lehmann & Magidor 1990 — *Preferential logics: predicate calculus case* — first-order extension.
- [18] Lehmann 1989 — *What does a conditional knowledge base entail?* (KR'89 conference version).
- [19] Lehmann, Magidor 1988 — *Rational logics and their models: a study in cumulative logic* (Tech Report).
- [31] Robinson — *Non-standard Analysis* — for App B.
- [16] Keisler — *Foundations of Infinitesimal Calculus* — alternative non-standard analysis reference.

## Collection Cross-References

### Already in Collection
- [Nonmonotonic Reasoning, Preferential Models and Cumulative Logics](../Kraus_1990_NonmonotonicReasoningPreferentialModels/notes.md) — direct prequel by the same authors plus Kraus; defines System P, preferential models, cumulative logic. This paper assumes its results and extends with Rational Monotonicity, ranked models, and rational closure.
- [Circumscription — A Form of Non-Monotonic Reasoning](../McCarthy_1980_CircumscriptionFormNon-MonotonicReasoning/notes.md) — cited (ref [22]) as a prior nonmonotonic system; criticised in Section 3.2 for not always satisfying Negation Rationality.
- [Semantical Considerations on Nonmonotonic Logic](../Moore_1985_SemanticalConsiderationsNonmonotonicLogic/notes.md) — cited (ref [24]) as one of the modal nonmonotonic logics this paper aims to subsume.
- [A Logic for Default Reasoning](../Reiter_1980_DefaultReasoning/notes.md) — cited (ref [29]) as default logic; contrasted in Section 5.9 (p.42) for requiring expert handcrafting of default precedence.
- [Counterfactuals](../Ginsberg_1985_Counterfactuals/notes.md) — cited (ref [12], 1986 in the paper but Ginsberg 1985 in the collection — same paper). Used for the modular-lattice connection on rational relations and CV-thesis discussion.

### New Leads (Not Yet in Collection)
- Pearl (1990) — "System Z: a natural ordering of defaults with tractable applications to nonmonotonic reasoning" — cited as [27]; alternative tractable rational-closure-style construction in the same TARK proceedings as Lehmann-Magidor's predicate-calculus paper.
- Adams (1975) — "The Logic of Conditionals" — cited as [1]; primary probabilistic-conditional reference used as Section 4.3 alternative semantics.
- Lehmann & Magidor (1990) — "Preferential logics: the predicate calculus case" — cited as [20]; first-order extension flagged as essential follow-up in conclusion.
- Freund, Lehmann, Morris (1991) — "Rationality, transitivity and contraposition" — cited as [11]; refines rationality landscape.
- Freund (1991) — "A semantic characterization of disjunctive relations" — cited as [10]; provides DisjRat semantic characterization.
- Makinson (1988) — "General theory of cumulative inference" — cited as [21]; cumulative logic background.
- Delgrande (1987, 1988) — cited as [7], [8]; contrasted in Section 3.7 for first-order conditional / default reasoning system N.
- Stalnaker & Thomason (1970) — cited as [34]; Henkin-style completeness in conditional logics.
- Satoh (1989) — cited as [32]; alternative one-parameter probabilistic representation of rational relations.
- Robinson (1966) "Non-standard Analysis" — cited as [31]; foundational reference for Appendix B.
- Keisler (1976) "Foundations of Infinitesimal Calculus" — cited as [16]; alternative non-standard analysis reference.
- Cutland (1983) "Non-standard measure theory" — cited as [6]; non-standard probability background.

### Supersedes or Recontextualizes
- This paper is the journal-published full version of Lehmann (1989) KR-89 conference paper [18] and supersedes Lehmann-Magidor TR 88-16 [19]. Neither earlier preprint is in the collection.
- Provides the *follow-up* representation theorem deferred in Kraus-Lehmann-Magidor 1990 (KLM): KLM defers Rational Monotonicity and ranked-model representation to this paper.

### Cited By (in Collection)
- [Nonmonotonic Reasoning, Preferential Models and Cumulative Logics](../Kraus_1990_NonmonotonicReasoningPreferentialModels/notes.md) — references this paper as the forthcoming follow-up that handles Rational Monotonicity, ranked models, and rational closure (the gap KLM leave open, e.g. inferring p∧r|~q from K = {p|~q}).
- [Deciding Consistency of Databases Containing Defeasible and Strict Information](../Goldszmidt_1992_DefeasibleStrictConsistency/notes.md) — uses Lehmann-Magidor's System Z / rational-closure equivalence as its semantic anchor; p-entailment shown equivalent to ranked-model entailment defined here.
- [Algorithmic Definitions for KLM-style Defeasible Disjunctive Datalog](../Morris_2020_DefeasibleDisjunctiveDatalog/notes.md) — extends the propositional rational-closure machinery defined here into Disjunctive Datalog; explicitly adopts "LM-rationality" (this paper's standard) as the benchmark for its three closure variants.
- [Rational Closure for Defeasible Description Logics](../Casini_2010_RationalClosure/notes.md) — direct extension to DLs: reformulates this paper's rational closure as a default-assumption (Poole-style) construction usable on a standard DL reasoner; complexity results inherit from this paper's coNP-completeness for propositional rational closure.

### Conceptual Links (not citation-based)

**Rational closure and its descendants:**
- [Rational Closure for Defeasible Description Logics](../Casini_2010_RationalClosure/notes.md) — **Strong.** Reformulates this paper's construction as default-assumption for DLs; preserves complexity. Already a direct cite, but the ALC transposition is conceptually the key descendant.
- [Algorithmic Definitions for KLM-style Defeasible Disjunctive Datalog](../Morris_2020_DefeasibleDisjunctiveDatalog/notes.md) — **Strong.** Extends to Disjunctive Datalog with Lexicographic and Relevant Closure variants addressing the inheritance failure flagged in Section 5.9 (Swedes-blond example) of this paper.
- [Defeasible Reasoning via Datalog](../Maher_2021_DefeasibleReasoningDatalog/notes.md) — **Moderate.** Datalog-based defeasible reasoning; alternative compilation strategy that does not use ranked models but addresses similar tractability concerns.

**Defeasible reasoning and rule-based argumentation:**
- [On the links between argumentation-based reasoning and nonmonotonic reasoning](../Li_2016_LinksBetweenArgumentation-basedReasoningNonmonotonicReasoning/notes.md) — **Strong.** Direct application of System P + RM rationality postulates as the benchmark for ASPIC+'s consequence relations.
- [The ASPIC+ framework for structured argumentation: a tutorial](../Modgil_2014_ASPICFrameworkStructuredArgumentation/notes.md) — **Strong.** ASPIC+ defeasible-rule semantics consume the System P + RM rationality framework defined here; rational consequence is the inference target structured argumentation aims to satisfy.
- [Complexity Results and Algorithms for Preferential Argumentative Reasoning in ASPIC+](../Lehtonen_2024_PreferentialASPIC/notes.md) — **Moderate.** Complexity analysis of preferential reasoning in ASPIC+; the underlying preferential semantics traces back to this paper's foundations.
- [A Mathematical Treatment of Defeasible Reasoning and its Implementation](../Simari_1992_MathematicalTreatmentDefeasibleReasoning/notes.md) — **Moderate.** Argument-structure approach to defeasible reasoning, contemporaneous and complementary to Lehmann-Magidor's consequence-relation approach.
- [Defeasible Logic Programming: An Argumentative Approach](../Garcia_2004_DefeasibleLogicProgramming/notes.md) — **Moderate.** Argument-based defeasible reasoning; rational closure is the consequence-relation analogue.
- [Defeasible Reasoning](../Pollock_1987_DefeasibleReasoning/notes.md) — **Moderate.** Independent epistemological framework for defeasible reasoning; same problem from a different (argument-based, philosophical) angle.

**Probabilistic and rank-based connections:**
- [Ordinal Conditional Functions: A Dynamic Theory of Epistemic States](../Spohn_1988_OrdinalConditionalFunctionsDynamic/notes.md) — **Strong.** Spohn's OCFs assign ordinals to formulas; the rank construction in Definition 10 (Section 2.6) is structurally an OCF computed from K. Different motivation (epistemic state dynamics vs nonmonotonic entailment) but isomorphic rank machinery.
- [Deciding Consistency of Databases Containing Defeasible and Strict Information](../Goldszmidt_1992_DefeasibleStrictConsistency/notes.md) — **Strong.** Goldszmidt-Pearl's p-entailment equivalence to System Z is the bridge between Adams' probabilistic semantics (Section 4.3 here) and the ranked-model representation (Theorem 5).

**Context and exception handling:**
- [Enhancing Context Knowledge Repositories with Justifiable Exceptions](../Bozzato_2018_ContextKnowledgeJustifiableExceptions/notes.md) — **Strong.** Addresses the inheritance-to-exceptional-subclass failure (Section 5.9, Swedes-blond example) via CKR-style contextual exceptions — exactly the propstore mechanism for going beyond rational closure toward Thesis 2.
- [A Datalog Translation for Reasoning on DL-Lite_R with Defeasibility](../Bozzato_2020_DatalogDefeasibleDLLite/notes.md) — **Moderate.** Datalog encoding of defeasibility consistent with KLM/rational-closure tradition.
- [DR-Prolog: A System for Defeasible Reasoning with Rules and Ontologies on the Semantic Web](../Antoniou_2007_DefeasibleReasoningSemanticWeb/notes.md) — **Moderate.** Practical defeasible-reasoning system; rational closure is one of the consequence relations such systems aim to compute.

**Belief revision:**
- [On the Logic of Theory Change: Partial Meet Contraction and Revision Functions](../Alchourron_1985_TheoryChange/notes.md) — **Moderate.** AGM postulates govern belief change; rational closure can be viewed as a specific belief-extension operator on conditional bases. Both frameworks rely on entrenchment-like ranking.
- [Knowledge in Flux: Modeling the Dynamics of Epistemic States](../Gärdenfors_1988_RevisionsKnowledgeSystemsEpistemic/notes.md) — **Moderate.** Epistemic-entrenchment ranking of formulas connects directly to this paper's rank construction; both define an ordering by exceptional-ness/entrenchment.
- [Admissible and Restrained Revision](../Booth_2006_AdmissibleRestrainedRevision/notes.md) — **Moderate.** Revision operators with admissibility constraints; conceptually close to admissible knowledge bases (Definition 11).
- [Preferred Subtheories — An Extended Logical Framework for Default Reasoning](../Brewka_1989_PreferredSubtheoriesExtendedLogical/notes.md) — **Moderate.** Independent 1989 default-reasoning framework based on prioritized maximal-consistent subtheories; tackles the same multiple-default-precedence problem rational closure resolves through ranks.
