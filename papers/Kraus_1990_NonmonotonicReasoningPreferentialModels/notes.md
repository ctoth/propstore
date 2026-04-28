---
title: "Nonmonotonic Reasoning, Preferential Models and Cumulative Logics"
authors: "Sarit Kraus, Daniel Lehmann, Menachem Magidor"
year: 1990
venue: "Artificial Intelligence (journal)"
doi_url: "https://doi.org/10.1016/0004-3702(90)90101-5"
pages: "44 (arXiv re-host cs/0202021v1)"
produced_by:
  agent: "claude-opus-4-7[1m]"
  skill: "paper-reader"
  status: "stated"
  timestamp: "2026-04-28T07:22:11Z"
---
# Nonmonotonic Reasoning, Preferential Models and Cumulative Logics

## One-Sentence Summary
KLM map nonmonotonic reasoning by characterizing five families of nonmonotonic consequence relations (C, CL, P, CM, M) via Gentzen-style inference rules and proving representation theorems linking each system to a corresponding family of preferential/cumulative models.

## Problem Addressed
Prior nonmonotonic systems (negation as failure, circumscription, default logic, autoepistemic logic, Shoham's preferential models) were defined ad hoc and described only negatively (by lacking monotonicity). KLM provide a positive, axiomatic taxonomy via *consequence relations* on conditional assertions α |~ β ("if α, normally β"), and bridge proof theory with semantics through representation theorems. *(p.1-3)*

## Key Contributions
- Five logical systems characterized by Gentzen-style rules: **C** (cumulative), **CL** (cumulative with Loop, also called **CT** in conclusion p.40), **P** (preferential — central system), **CM** (cumulative monotonic), **M** (monotonic / classical). *(p.5, 39-40)*
- Five corresponding model families with **representation theorems** (soundness + completeness). *(Theorems 1-6, p.20, 24, 31, 36, 38)*
- Original rule **Loop** (Eq. 14) and original rule **Or** (Eq. 16) for system P; rule **Cautious Monotonicity** rehabilitated and given semantics. *(p.22, 25, 12)*
- Demonstration that circumscription, default logic, autoepistemic logic each fail at conditional reasoning; explicit comparison of A: γ∧α |~ β vs B: γ |~ ¬α∨β. *(p.8-10)*
- Three "rationality" rules (Negation Rationality, Disjunctive Rationality, **Rational Monotonicity**) deliberately *not* in P — their representation result is deferred to a follow-up paper (Lehmann-Magidor 1992). *(p.32-33)*
- Concrete handling of **Nixon diamond** and **penguin triangle** without "multiple extension problem". *(p.33-34)*
- Theorem 4: P and CL coincide on Horn knowledge bases. *(p.35)*

## Study Design (empirical papers)
*Not applicable — pure theory paper (axiomatic systems + representation theorems).*

## Methodology
- Treat α |~ β ("conditional assertion") as a meta-language binary relation between formulas of a propositional language L over a universe U of possible worlds. *(p.6-7)*
- Knowledge base K = a set of conditional assertions; inference = deducing new conditional assertions from K within a logical system. *(p.7-8)*
- For each axiomatic system, construct a model family and prove (i) soundness — every model defines a relation in the system, and (ii) completeness/representation — every relation in the system is defined by some model.
- Construction trick for representation: given a relation |~, define states as pairs ⟨m, α⟩ where m is a *normal world* for α (Def 10, p.18: m normal for α iff m satisfies every β with α|~β). The labeling and preference relation are derived from |~ itself.
- Compactness assumed on the underlying logic (Sec 2.1, p.6). All proofs use only finite premises.

## Key Equations / Statistical Models

### Inference rules of system C (cumulative)

$$
\alpha \mathrel{|\!\sim} \alpha \quad\text{(Reflexivity)}
$$
*(p.11)*

$$
\frac{\models \alpha \leftrightarrow \beta \quad\quad \alpha \mathrel{|\!\sim} \gamma}{\beta \mathrel{|\!\sim} \gamma} \quad\text{(Left Logical Equivalence)}
$$
*(p.11)*

$$
\frac{\models \alpha \to \beta \quad\quad \gamma \mathrel{|\!\sim} \alpha}{\gamma \mathrel{|\!\sim} \beta} \quad\text{(Right Weakening)}
$$
*(p.11)*

$$
\frac{\alpha \wedge \beta \mathrel{|\!\sim} \gamma \quad\quad \alpha \mathrel{|\!\sim} \beta}{\alpha \mathrel{|\!\sim} \gamma} \quad\text{(Cut)}
$$
*(p.11)*

$$
\frac{\alpha \mathrel{|\!\sim} \beta \quad\quad \alpha \mathrel{|\!\sim} \gamma}{\alpha \wedge \beta \mathrel{|\!\sim} \gamma} \quad\text{(Cautious Monotonicity)}
$$
*(p.12)*

### Derived rules of C

$$
\frac{\alpha \mathrel{|\!\sim} \beta \quad\quad \alpha \mathrel{|\!\sim} \gamma}{\alpha \mathrel{|\!\sim} \beta \wedge \gamma} \quad\text{(And)}
$$
*(p.13)*

$$
\frac{\alpha \mathrel{|\!\sim} \beta \to \gamma \quad\quad \alpha \mathrel{|\!\sim} \beta}{\alpha \mathrel{|\!\sim} \gamma} \quad\text{(MPC)}
$$
*(p.13)*

$$
\frac{\alpha \mathrel{|\!\sim} \beta \quad\quad \beta \mathrel{|\!\sim} \alpha \quad\quad \alpha \mathrel{|\!\sim} \gamma}{\beta \mathrel{|\!\sim} \gamma} \quad\text{(Equivalence)}
$$
*(p.13)*

### Rules NOT derivable in C (Section 3.3, p.14)

$$
\frac{\models \alpha \to \beta \quad\quad \beta \mathrel{|\!\sim} \gamma}{\alpha \mathrel{|\!\sim} \gamma} \quad\text{(Monotonicity / Left Strengthening)}
$$

$$
\frac{\alpha \mathrel{|\!\sim} \beta \to \gamma}{\alpha \wedge \beta \mathrel{|\!\sim} \gamma} \quad\text{(EHD — easy half deduction)}
$$

$$
\frac{\alpha \mathrel{|\!\sim} \beta \quad\quad \beta \mathrel{|\!\sim} \gamma}{\alpha \mathrel{|\!\sim} \gamma} \quad\text{(Transitivity)}
$$

$$
\frac{\alpha \mathrel{|\!\sim} \beta}{\neg\beta \mathrel{|\!\sim} \neg\alpha} \quad\text{(Contraposition)}
$$
*(p.14)* — Lemma 3: Monotonicity ≡ EHD ≡ Transitivity in the presence of C.

### Loop rule (system CL = CT)

$$
\frac{\alpha_0 \mathrel{|\!\sim} \alpha_1 \quad \alpha_1 \mathrel{|\!\sim} \alpha_2 \quad \cdots \quad \alpha_{k-1} \mathrel{|\!\sim} \alpha_k \quad \alpha_k \mathrel{|\!\sim} \alpha_0}{\alpha_0 \mathrel{|\!\sim} \alpha_k} \quad\text{(Loop)}
$$
*(p.22, Eq. 14)*

### Or rule and S rule (system P)

$$
\frac{\alpha \mathrel{|\!\sim} \gamma \quad\quad \beta \mathrel{|\!\sim} \gamma}{\alpha \vee \beta \mathrel{|\!\sim} \gamma} \quad\text{(Or)}
$$
*(p.25, Eq. 16)*

$$
\frac{\alpha \wedge \beta \mathrel{|\!\sim} \gamma}{\alpha \mathrel{|\!\sim} \beta \to \gamma} \quad\text{(S — derived in P from Or, RW, LLE)}
$$
*(p.25, Eq. 17)*

$$
\frac{\alpha \wedge \neg\beta \mathrel{|\!\sim} \gamma \quad\quad \alpha \wedge \beta \mathrel{|\!\sim} \gamma}{\alpha \mathrel{|\!\sim} \gamma} \quad\text{(D — proof by cases, equivalent to Or in P)}
$$
*(p.26, Eq. 18; Lemma 21 p.26)*

### Rationality rules — NOT in P

$$
\frac{\alpha \wedge \gamma \not\mathrel{|\!\sim} \beta \quad\quad \alpha \wedge \neg\gamma \not\mathrel{|\!\sim} \beta}{\alpha \not\mathrel{|\!\sim} \beta} \quad\text{(Negation Rationality)}
$$
*(p.32, Eq. 23)*

$$
\frac{\alpha \not\mathrel{|\!\sim} \gamma \quad\quad \beta \not\mathrel{|\!\sim} \gamma}{\alpha \vee \beta \not\mathrel{|\!\sim} \gamma} \quad\text{(Disjunctive Rationality)}
$$
*(p.32, Eq. 24)*

$$
\frac{\alpha \wedge \beta \not\mathrel{|\!\sim} \gamma \quad\quad \alpha \not\mathrel{|\!\sim} \neg\beta}{\alpha \not\mathrel{|\!\sim} \gamma} \quad\text{(Rational Monotonicity)}
$$
*(p.32, Eq. 25)*

Strict implications: Rational Monotonicity ⇒ Disjunctive Rationality ⇒ Negation Rationality (Makinson). All implied by Monotonicity. Form is *novel*: deduce *absence* of an assertion from absence of others. *(p.32-33)*

### Smoothness condition

A set P ⊆ U is **smooth** with respect to ≺ iff ∀t∈P, either ∃s minimal in P with s ≺ t, OR t itself is minimal in P. *(Def 4, p.16)*

A triple ⟨S, l, ≺⟩ satisfies the **smoothness condition** iff ∀α ∈ L the set α̂ = {s ∈ S : s ⊨ α} is smooth. *(Def 7, p.17)*

Smoothness is essential for Cautious Monotonicity to hold; it is the analog of Stalnaker/Lewis "limit assumption" (and "well-foundedness" in [8, 26], a misnomer — true well-foundedness is stronger). *(p.17)*

### Satisfaction in models

For cumulative models (multi-world labels): s ⊨ α iff ∀m ∈ l(s), m ⊨ α. α̂ = {s ∈ S : s ⊨ α}. *(Def 6, p.17)*
For preferential models (single-world labels): s ⊨ α iff l(s) ⊨ α. *(p.27)*

### Consequence relation defined by a model

$$
\alpha \mathrel{|\!\sim_W} \beta \;\;\text{iff}\;\; \forall s \in S: s \text{ minimal in } \widehat{\alpha} \implies s \models \beta
$$
*(Def 8, p.17)*

## Parameters

The "parameters" of this paper are the system axioms and the model-class structural restrictions. There are no numeric parameters.

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of inference rule schemas in C | — | — | 5 | — | 10-12 | Reflexivity, LLE, RW, Cut, CM |
| Additional rule for CL (= CT) | Loop | — | 1 | — | 22 | (14) |
| Additional rule for P | Or | — | 1 | — | 25 | (16); CL ⊊ P |
| Additional rule for CM | Monotonicity | — | 1 | — | 36 | (10); subsumes LLE and CM-rule |
| Additional rule for M | Contraposition | — | 1 | — | 37 | (13); Or becomes derived (Lemma 34) |
| Number of representation theorems | — | — | 5+1 | — | 20,24,31,36,38 | Thm 1, 2, 3, 5, 6 (Thm 4 is Horn equivalence) |
| Smoothness condition required for | Cautious Monotonicity | — | — | — | 17 | Without smoothness, CM may fail |
| Equivalence in P axiomatization | — | — | — | — | 26 | {Reflexivity, LLE, RW, And, Or, CM} also axiomatize P (Lemma 20) |

## Effect Sizes / Key Quantitative Results

Not applicable — theoretical paper. Key qualitative inclusion lattice:

| Relation | Containment | Source |
|----------|-------------|--------|
| C ⊆ CL | strict | p.21-22 (Loop fails in some cumulative models — Lemma 15) |
| CL ⊆ P | strict (over rich language) | p.24 (Or independent of Loop) |
| P ⊆ M | strict | p.32-33 (P fails Negation Rationality, hence Monotonicity) |
| CM ⊆ M | strict | p.36-37 (CM ⊊ M because Contraposition not derivable) |
| CM and P incomparable | both directions strict | p.36 (preferential models violating Monotonicity; simple cumulative models violating Or) |
| CL ⊆ CM | strict (CM = C + Monotonicity ⇒ Transitivity ⇒ Loop) | p.36 |
| **CL ≡ P on Horn assertions** | equivalence | Theorem 4, p.35 |

## Methods & Implementation Details

### Family hierarchy of models *(p.39-40 summary)*
1. **Cumulative model** ⟨S, l, ≺⟩: l: S → 2^U \\ {∅}, smoothness condition (Def 5, p.16). Defines C.
2. **Cumulative ordered model**: ≺ is strict partial order (Def 13, p.21). Defines CL = CT.
3. **Preferential model**: l: S → U single world, ≺ strict partial order, smoothness (Def 16, p.27). Defines P.
4. **Simple cumulative model**: ≺ = ∅ (Def 20, p.36). Defines CM.
5. **Simple preferential model**: ≺ = ∅ in preferential model (Def 22, p.38). Defines M; equivalent to V ⊆ U with implicit "everything in V matters equally."

### Algorithm: build a strong cumulative model from a relation in C *(Sec 3.5, p.18-20)*
Inputs: a consequence relation |~ satisfying the rules of C.
Output: cumulative model W = ⟨S, l, ≺⟩ such that |~_W = |~.
1. Define ∼ on L: α ∼ β iff α |~ β and β |~ α (Def 11, p.19; Lemma 9: equivalence relation).
2. Let S = L/∼ be equivalence classes ᾱ.
3. Define l(ᾱ) = {m ∈ U : m is normal world for α} (Def 10, p.18). Independent of representative.
4. Define ᾱ ≺ β̄ iff ᾱ ≤ β̄ and ᾱ ≠ β̄, where ᾱ ≤ β̄ iff ∃α' ∈ ᾱ such that β |~ α' (Def 12, p.19).
5. Verify: ᾱ is a minimum of α̂ (Lemma 11, p.19); thus ≺ is asymmetric and α̂ has a minimum, hence W is a *strong* cumulative model.
6. Lemma 12 (p.20): α |~ β iff α |~_W β.

### Algorithm: build a cumulative ordered model from a relation in CL *(Sec 4.3, p.22-24)*
1. Build the cumulative model W as above from |~.
2. Take ≺⁺ = transitive closure of W's ≺.
3. Lemma 16 (p.23): under Loop, ≺⁺ is irreflexive ⇒ strict partial order.
4. Lemma 17 (p.24): V = ⟨S, l, ≺⁺⟩ is a strong cumulative ordered model and α̂ minimal state still ᾱ.
5. Lemma 18: α |~ β iff α |~_V β. ⇒ Theorem 2.

### Algorithm: build a preferential model from a relation in P *(Sec 5.3, p.28-31)*
1. Define ≤ on L by α ≤ β iff α∨β |~ α (Def 17, p.29; Lemma 25: reflexive + transitive).
2. Build W = ⟨S, l, ≺⟩ where:
   - S = {⟨m, α⟩ : m is a normal world for α}
   - l(⟨m, α⟩) = m  (single world!)
   - ⟨m, α⟩ ≺ ⟨n, β⟩ iff α ≤ β AND m ⊭ β
3. Lemma 28 (p.30): ≺ is strict partial order. Lemma 30: smoothness holds.
4. Lemma 29 (p.30): ⟨m, β⟩ minimal in α̂ iff m ⊨ α and β ≤ α.
5. Lemmas 31, 32: |~ = |~_W. ⇒ Theorem 3.

### Algorithm: build a simple cumulative model for CM *(Sec 6.3, p.36-37)*
W = ⟨A, l, ∅⟩ where A = {α ∈ L : α |⊬ false} and l(α) = {m : m normal for α}. Empty ≺. (≺ = ∅ ⇒ Monotonicity satisfied.) ⇒ Theorem 5.

### Algorithm: build a simple preferential model for M *(Sec 7.3, p.38)*
V = {m ∈ U : ∀α,β ∈ L, α |~ β ⇒ m ⊨ α → β}. l = identity. ≺ = ∅. ⇒ Theorem 6.

### Pragmatic three-tier knowledge architecture *(Sec 2.2, p.7-8)*
1. **Universe of reference U** — hard constraints, e.g. "penguins are birds". Stable.
2. **K** — set of conditional assertions, soft constraints, e.g. "birds normally fly".
3. **Specific situation formula** — e.g. "Tweety is a bird".

A formula α of type 1 may be re-expressed as the conditional ¬α |~ false. *(p.8)*

### Inference patterns rejected as broken in prior systems *(Sec 2.3, p.8-10)*
- **Circumscription**: cannot distinguish A: α∧¬abnormal → β from B: ¬abnormal → (α → β) without ad hoc abnormality priorities.
- **Autoepistemic logic**: with M for "consistent", B becomes strictly stronger than A — wrong direction.
- **Default logic**: normal default (α, β; β) and (true, α→β; α→β) collapse on situations where α is concluded true; α |~ false has no useful default-logic translation.

### Lemma 1 (intuition for Cut + CM)
Cut + CM ≡ "if α |~ β then plausible consequences of α and α∧β coincide." *(p.13)*

### Important lemma chain establishing Theorem 3 for P
- Lemma 23 (p.28): For preferential models, α ∨ β̂ = α̂ ∪ β̂ (does NOT hold for cumulative — see Lemma 6 for the cumulative analog α ∧ β̂ = α̂ ∩ β̂).
- Lemma 24 (Soundness): preferential models satisfy P. *Or* alone needs proof; it follows because a state minimal in α∨β̂ = α̂ ∪ β̂ is minimal in whichever of α̂ or β̂ contains it.
- Lemma 26-27 (p.29): normality of worlds is preserved up the ≤-chain.
- Lemma 28 (p.30): the constructed ≺ is strict partial order (proved via Lemma 25 on transitivity of ≤).
- Lemmas 29-30: minimal characterization + smoothness.
- Lemmas 31-32: |~ ↔ |~_W.

### Examples worked out *(Sec 5.5, p.33-34)*
**Nixon diamond.** K = {t |~ p, t |~ s, p |~ e, s |~ ¬e} (teen-ager, poor, student, employed). Neither t |~ e nor t |~ ¬e is preferentially entailed by K (no contradiction inferred). However true |~ ¬t and true |~ ¬(p ∧ s) ARE entailed. Multiple-extension problem dissolved.

**Penguin triangle.** K = {p |~ b (penguins are birds), p |~ ¬f (penguins don't fly), b |~ f (birds fly)}. Then K preferentially entails: p ∧ b |~ ¬f, f |~ ¬p, b |~ ¬p, b ∨ p |~ f, b ∨ p |~ ¬p. *Specificity wins:* preferential reasoning correctly pre-empts the less specific default.

What K does NOT preferentially entail: a |~ e (where a is unmentioned). *(p.34)* For that you need rational closure / ranked models — see [20] (Lehmann 1989, "What does a conditional knowledge base entail?").

## Figures of Interest
No figures in the body. Inclusion lattice over five systems implicitly described in §8 conclusion *(p.39-40)*. The implied lattice:

```
              M (classical)
             /      \
           CM        P
            \      /
             CL = CT (cumulative ordered)
              |
              C (cumulative)
```

## Results Summary
- 5 representation theorems link 5 axiomatic systems to 5 model families. *(Theorems 1-3, 5, 6.)*
- Compactness corollaries (3 and 5): K entails an assertion iff a finite subset of K does. *(p.21, 39)*
- Theorem 4 (p.35): Horn-restricted P collapses to CL, so for Horn assertions cumulative ordered models are sufficient.
- Loop is novel and naturally captures transitivity of preferences without invoking propositional connectives. *(p.22)*
- Or rule supplies disjunctive case analysis natively. *(p.25)*
- Preferential reasoning over Nixon diamond / penguin triangle works WITHOUT multiple extensions. *(p.33-34)*

## Limitations
- Paper *does not* propose a specific nonmonotonic reasoning system; only the framework. Steps toward such a system live in [19, 20, 22] = Lehmann 1988, Lehmann 1989, Lehmann-Magidor TR 1988. *(p.4, 40)*
- All consequence relations are *flat* (no nested conditionals); language is propositional. Predicate-calculus extension and complexity results deferred to companion paper. *(p.1, 40)*
- Rational Monotonicity (p.32) is desirable but not in P; no inference procedure satisfying it is constructed here. The full representation theorem for ranked models is deferred to a separate paper (Lehmann-Magidor 1992 "What does a conditional knowledge base entail?"). *(p.33, 40)*
- Quantification of conditional assertions like bird(x) |~ fly(x) is unsolved — the second and third authors have an unpublished solution. *(p.40)*
- Smoothness condition is non-trivial to check on cumulative models where ≺ is not a partial order. *(p.17)*
- Compactness assumption needed only when treating consequence relations defined as the set of assertions entailed by infinite sets of premises (footnote, p.6).

## Arguments Against Prior Work
- **Circumscription** (McCarthy [29]) — A and B (single vs scoped abnormality) are logically equivalent without ad hoc priorities. *(p.8)* Also fails Negation Rationality on the special/beautiful example. *(p.32)*
- **Autoepistemic logic** (Moore [31]) — translation makes B strictly stronger than A, opposite to natural reading. *(p.9)*
- **Default logic** (Reiter [35]) — normal default and "true →" default collapse undesirably; α |~ false has no useful translation. *(p.9-10)* Default logic does not satisfy Cautious Monotonicity (Makinson [28]). *(p.12)*
- **Shoham [38]'s preferential models** — required S ⊆ U and l = identity and ≺ a well-order; either restriction breaks the representation theorem. *(p.28)*
- **Probabilistic semantics** (Adams [2]) interpretation as p(β|α) > q for q < 1 *invalidates Cut and CM*. *(p.12)* The preferential models presented here are strictly stronger than Adams' probabilistic semantics. *(abstract, p.5)*
- **Ginsberg [14]'s counterfactual translation** is built around the conditional-logic semantics, which differs from KLM's "α is good enough reason for β"; explains disagreement on Rational Monotonicity. *(p.5)*
- **Shoham**'s "well-foundedness" terminology (also [8, 26]) is incorrect mathematical usage; the right notion is what KLM call **smoothness**. *(p.17)*

## Design Rationale
- **Why conditional assertions α |~ β as a binary meta-relation, not a unary modal "if α normally β"?** Unary translations N(α → β) or α → Nβ are insufficiently expressive. *(p.7)*
- **Why labels in 2^U for cumulative models, single worlds for preferential?** Multi-world labels give a degree of freedom needed for the cumulative representation theorem (the same world set may appear at multiple states); Shoham's account is missing this freedom. *(p.16)*
- **Why is ≺ NOT required to be a partial order in cumulative models?** Because the construction in §3.5 builds a model where ≺ is not transitive in general; requiring transitivity would prevent representation of all C-relations. Requiring asymmetry alone preserves the theorem. *(p.16, 21)*
- **Why Cautious Monotonicity instead of full Monotonicity?** Full Monotonicity collapses to classical reasoning (Lemma 3 + Lemma 4: Monotonicity + LLE + RW = Transitivity = EHD). CM lets us add hypotheses we already plausibly accept without invalidating prior conclusions, but disallows arbitrary strengthening. *(p.12)*
- **Why is Cut accepted but probabilistic Cut rejected?** Cut says "a plausible conclusion is as secure as the assumptions it is based on." Probabilistic readings break this. *(p.12)*
- **Why systems strictly weaker than monotonic logic (CM)?** They show that one can have *some* monotonicity rules (Monotonicity itself) without the full force of Or; useful for reasoning patterns where preference is empty. *(p.36)*
- **Why M includes Contraposition rather than Monotonicity directly?** Lemma 34: Or becomes derivable from Contraposition + And. Lemma 35: M ≡ {Reflexivity, RW, Monotonicity, And, Or}. Choice is presentational. *(p.37-38)*
- **Why explicit "ist(c, p)" not present:** This 1990 paper does not add explicit per-context qualification — that's added later by McCarthy/Buvač. KLM treat U as a single fixed universe. *(p.6)*

## Testable Properties
- **(Inclusion lattice)** C ⊊ CL ⊊ {CM, P} ⊊ M; CM and P incomparable. *(p.39-40)*
- **(Soundness/completeness, Theorem 1)** A consequence relation satisfies {Reflexivity, LLE, RW, Cut, CM} iff it equals |~_W for some cumulative model W. *(p.20)*
- **(Soundness/completeness, Theorem 2)** Loop-cumulative iff defined by some cumulative ordered model. *(p.24)*
- **(Soundness/completeness, Theorem 3)** Preferential iff defined by some preferential model. *(p.31)*
- **(Soundness/completeness, Theorem 5)** Cumulative monotonic iff defined by some simple cumulative model (≺ = ∅). *(p.36)*
- **(Soundness/completeness, Theorem 6)** Monotonic iff defined by some simple preferential model (subset of U). *(p.38)*
- **(Lemma 23)** In a preferential model, α ∨ β̂ = α̂ ∪ β̂. (Does NOT hold in cumulative; cumulative has α ∧ β̂ = α̂ ∩ β̂ — Lemma 6.) *(p.28, 18)*
- **(Lemma 1)** Cut + CM iff α|~β implies "plausible consequences of α and α∧β coincide". *(p.13)*
- **(Loop derived from Or in P)** Loop is a derived rule of P. *(p.25)*
- **(Lemma 20)** {Reflexivity, LLE, RW, And, Or, CM} axiomatizes P. *(p.26)*
- **(Theorem 4 / Horn equivalence)** For Horn knowledge bases and Horn queries, P-derivability ≡ CL-derivability. *(p.35)*
- **(Smoothness ⇒ CM)** Without smoothness, Cautious Monotonicity fails in the model. *(p.17-18)*
- **(Negation Rationality fails for circumscription)** A circumscriptive reasoner over `special/beautiful` predicates violates Negation Rationality. *(p.32)*
- **(Compactness, Corollaries 3 and 5)** K entails α |~ β iff a finite subset of K does. *(p.21, 39)*

## Relevance to Project

**Highly relevant.** The propstore argumentation/reasoning layer is grounded in Dung AFs and ASPIC+, but the *consequence relation* level — what defeasible inference is licensed in the absence of attack — is exactly what KLM characterize. Specific touch-points:

1. **Defeasibility primitives** — `propstore.defeasibility` claims to host CKR-style justifiable exceptions; KLM's |~ is the canonical defeasible-conditional algebra. The five systems give a formal yardstick for which inference rules `defeasibility` may use without committing to monotonicity.
2. **Stance algebra and `propstore.belief_set` AGM revision** — Gardenfors entrenchment relates closely to KLM's ≤-relation (α ≤ β iff α∨β |~ α, "α not less ordinary than β"). Our entrenchment ordering should at least satisfy P; whether to insist on Rational Monotonicity is a render-policy choice.
3. **ATMS environments and `propstore.world.assignment_selection_merge`** — KLM's notion of "minimal states satisfying α" corresponds to ATMS environments minimal under inclusion in the consistent extension of K ∪ {α}. Lemma 23 (preferential) vs Lemma 6 (cumulative) tells us when distributing α∨β across environments is sound.
4. **Render-time non-commitment** — KLM systems give five mutually distinct closure operators over a knowledge base K. The render layer can expose these as policy options ("close under C", "close under P") instead of hard-coding one.
5. **Honest ignorance** — when the paper says "K does NOT entail t|~e in the Nixon diamond," that's exactly the system *not* fabricating a probability when it has no evidence. KLM's preferential semantics is the formal grounding for the project's "vacuous opinion" principle.
6. **Horn equivalence (Theorem 4)** — for Horn knowledge bases, the simpler CL is sufficient. Useful when sidecar materializes Horn-shaped fragments (e.g. type assertions).
7. **Loop rule** — directly applicable to detection of cycles in stance graphs / ranked-model inputs; gives a proof-theoretic discipline rather than a graph-theoretic one.

## Open Questions
- [ ] Does propstore's existing belief_set entrenchment satisfy at least P? (Verification task.)
- [ ] Where does ASPIC+ argument-level defeat sit relative to KLM Or vs Loop? (Translation task.)
- [ ] Should the render layer expose system selection (C, CL, P, CM, M) as a `RenderPolicy` flag?
- [ ] Is rational closure (deferred to Lehmann 1989 [20] / Lehmann-Magidor 1992) needed for the propstore use case, or is preferential entailment enough?
- [ ] Does propstore's notion of context (`ist(c, p)`) commute with KLM's universe restriction U_Γ (p.7)?
- [ ] How does smoothness interact with infinite stance corpora? (Compactness corollary may help.)

## Collection Cross-References

### Already in Collection
- [Counterfactuals](../Ginsberg_1985_Counterfactuals/notes.md) — KLM ref [14]; Ginsberg's counterfactual translation built around conditional-logic semantics; KLM disagree on Rational Monotonicity for this reason. *(p.5)*
- [Circumscription, a form of non-monotonic reasoning](../McCarthy_1980_CircumscriptionFormNon-MonotonicReasoning/notes.md) — KLM ref [29]; KLM critique circumscription's inability to distinguish A=γ∧α|~β from B=γ|~¬α∨β without ad hoc abnormality priorities, and show circumscription violates Negation Rationality. *(p.8, 32)*
- [A Logic for Default Reasoning](../Reiter_1980_DefaultReasoning/notes.md) — KLM ref [35]; default logic does not satisfy Cautious Monotonicity; default translations of α|~β and α|~¬α∨β collapse undesirably. *(p.9-10, 12)*
- [Semantical Considerations on Nonmonotonic Logic](../Moore_1985_SemanticalConsiderationsNonmonotonicLogic/notes.md) — autoepistemic-logic family; KLM show autoepistemic translation makes B strictly stronger than A, opposite of natural reading. *(p.9, related to Moore's [31])*

### New Leads (Not Yet in Collection)
- **Adams (1975)** — *The Logic of Conditionals*, D. Reidel. Probabilistic semantics for indicative conditionals; system P strictly extends it. Foundational for understanding why probabilistic readings invalidate Cut and CM (KLM p.12).
- **Makinson (1988)** — "General theory of cumulative inference," NMR-88 (LNAI 346). Independent and parallel infinitistic version of cumulative reasoning. Coined "cumulative."
- **Pearl-Geffner (1988)** — "Probabilistic semantics for default reasoning," UCLA TR. Built on Adams + system P.
- **Shoham (1988)** — *Reasoning about Change*, MIT Press. Original (flawed) preferential-model semantics; KLM fix the smoothness/labeling issue.
- **Burgess (1981)** — "Quick completeness proofs for some logics of conditionals," NDJFL 22:76-84. P is the flat fragment of Burgess' system S.
- **Veltman (1986)** — *Logics for Conditionals*, PhD Amsterdam. Closest semantic analog to KLM's preferential models.
- **Gabbay (1985)** — "Theoretical foundations for non-monotonic reasoning in expert systems." Origin of Reflexivity/Cut/CM as the rock bottom; KLM's system C closely matches.
- **Touretzky (1986)** — *The Mathematics of Inheritance Systems*. Inheritance-network reasoning, related to penguin triangle.

### Now in Collection (previously listed as leads)
- [What does a conditional knowledge base entail?](../Lehmann_1989_DoesConditionalKnowledgeBase/notes.md) — the deferred follow-up: introduces Rational Monotonicity, ranked models (Theorem 5), rational closure, and shows ranked entailment ≡ preferential entailment (Theorem 6). Provides the representation theorem KLM defer to "a separate paper" on p.33. Also subsumes the earlier KR-89 conference and TR-88-16 versions noted as leads.

### Supersedes or Recontextualizes
- (Foundational paper — not superseded, but extended by Lehmann 1989 and Lehmann-Magidor 1992 for Rational Monotonicity / ranked models.)

### Conceptual Links (not citation-based)
- [Algorithmic Definitions for KLM-style Defeasible Disjunctive Datalog](../Morris_2020_DefeasibleDisjunctiveDatalog/notes.md) — **Strong.** Morris proves Rational and Lexicographic Closure satisfy all KLM properties (Ref, LLE, And, Or, RW, CM, RM) over Disjunctive Datalog; KLM 1990 defines those properties. Direct algorithmic implementation of the KLM rationality program over a logic-programming target language.
- [Links Between Argumentation-based Reasoning and Nonmonotonic Reasoning](../Li_2016_LinksBetweenArgumentation-basedReasoningNonmonotonicReasoning/notes.md) — **Strong.** Li classifies which KLM-style axioms (Ref, LLE, RW, Cut, CM, M, T, CP) hold for ASPIC+'s `|~a` (argument constructibility) and `|~j` (justified conclusions) consequence relations. Direct application of KLM's framework to ASPIC+; answers project Open Question "where does ASPIC+ defeat sit relative to KLM Or vs Loop?"
- [Defeasible Strict Consistency](../Goldszmidt_1992_DefeasibleStrictConsistency/notes.md) — **Strong.** Goldszmidt & Pearl's p-entailment is shown equivalent to System Z (Lehmann-Magidor 1992 ranked-model semantics), the very system KLM defer to a sequel. Probabilistic ε-semantics that grounds the preferential closure operator.
- [Rational Closure](../Casini_2010_RationalClosure/notes.md) — **Strong.** Casini's rational closure is the canonical algorithmic instantiation of the Rational Monotonicity-satisfying entailment KLM 1990 acknowledge as desirable but defer (p.32-33). Direct sequel-of-sequel.
- [Theory Change](../Alchourron_1985_TheoryChange/notes.md) — **Strong.** AGM postulates K1-K8 share structural DNA with KLM's |~ algebra: epistemic entrenchment is closely related to KLM's α≤β iff α∨β|~α. Both formalize "what should be retained when adding new info." Provides the belief-revision side that KLM's consequence-relation side complements.
- [Iterated Belief Revision](../Darwiche_1997_LogicIteratedBeliefRevision/notes.md) — **Moderate.** Darwiche-Pearl postulates C1-C4 govern how epistemic states evolve; KLM's |~ describes the static defeasible-conditional layer that those revisions act over.
- [Preferred Subtheories](../Brewka_1989_PreferredSubtheoriesExtendedLogical/notes.md) — **Moderate.** Brewka's priority-based maximal consistent subsets and KLM's preferential reasoning are alternative formal accounts of "what to conclude in face of conflicting defaults"; KLM is model-theoretic, Brewka is preference-syntactic.
- [Defeasible Reasoning](../Pollock_1987_DefeasibleReasoning/notes.md) — **Moderate.** Pollock's rebutting/undercutting defeat distinction and KLM's |~ algebra are alternative formalisms for defeasible inference; Pollock is argument-graph centric, KLM is consequence-relation centric.
- [Mathematical Treatment of Defeasible Reasoning](../Simari_1992_MathematicalTreatmentDefeasibleReasoning/notes.md) — **Moderate.** Simari-Loui formalize argument structure and specificity; KLM 1990 formalize the conditional algebra over which such arguments range. The penguin-triangle specificity intuition is captured semantically by KLM's preferential model and operationally by Simari-Loui defeat.
- [Defeasible Logic Programming](../Garcia_2004_DefeasibleLogicProgramming/notes.md) — **Moderate.** DeLP's strict/defeasible rule split is a programmable instantiation of KLM's hard-constraint U vs soft-constraint K distinction (KLM Sec 2.2 p.7-8).
- [Ordinal Conditional Functions](../Spohn_1988_OrdinalConditionalFunctionsDynamic/notes.md) — **Moderate.** OCFs (κ-functions) are the formal counterpart of ranked models that Lehmann-Magidor 1992 use to characterize Rational Monotonicity; KLM defer that result.
- [Context Knowledge with Justifiable Exceptions](../Bozzato_2018_ContextKnowledgeJustifiableExceptions/notes.md) — **Moderate.** Bozzato et al.'s CKR justifiable exceptions are a context-aware operationalization of the KLM idea that defeasible inference licenses can be over-ridden by more specific information; CKR adds explicit per-context qualification (`ist(c, p)`) that KLM 1990 does not have.
- [An Abstract Argumentation-theoretic Approach to Default Reasoning](../Bondarenko_1997_AbstractArgumentation-TheoreticApproachDefault/notes.md) — **Moderate.** Bondarenko-Dung-Kowalski-Toni unify default logics through abstract argumentation; KLM 1990 unifies them through abstract consequence relations. Different abstraction layers, complementary projects.
- [Defeasible Reasoning on the Semantic Web](../Antoniou_2007_DefeasibleReasoningSemanticWeb/notes.md) — **Moderate.** Defeasible logic for the Semantic Web; the rationality postulate framework KLM defines is the yardstick by which any such defeasible logic is evaluated.

### Cited By (in Collection)
- [Algorithmic Definitions for KLM-style Defeasible Disjunctive Datalog](../Morris_2020_DefeasibleDisjunctiveDatalog/notes.md) — cites this as the "foundational KLM properties paper" defining Ref, LLE, And, Or, RW, CM, RM that Morris proves Rational and Lexicographic Closure satisfy over Disjunctive Datalog.
- [Links Between Argumentation-based Reasoning and Nonmonotonic Reasoning](../Li_2016_LinksBetweenArgumentation-basedReasoningNonmonotonicReasoning/notes.md) — cites this for the foundational axiom system used to evaluate ASPIC+'s consequence relations.
- [What does a conditional knowledge base entail?](../Lehmann_1989_DoesConditionalKnowledgeBase/notes.md) — cites this paper as ref [17]; the direct sequel that takes KLM's preferential framework and adds Rational Monotonicity / ranked models / rational closure to close the inference gap KLM flag.

## Related Work Worth Reading
- Adams [2] — *The Logic of Conditionals*, D. Reidel, 1975. Probabilistic semantics for indicative conditionals; preferential (system P) is the strengthening of Adams' system. Already in collection? Should be.
- Lehmann [20] — "What does a conditional knowledge base entail?" *KR-89*. Solves the "a not in K, want a∧p|~e" gap (Sec 5.5). The follow-up that introduces rational closure / ranked models.
- Lehmann-Magidor 1992 — "What does a conditional knowledge base entail?" (full paper) — representation theorem for Rational Monotonicity. Mentioned as "in a separate paper" (p.33).
- Makinson [28] — "General theory of cumulative inference," *NMR-88*. Independent infinitistic version of cumulative reasoning; coined the term *cumulative*.
- Shoham [38, 39] — *Reasoning about Change* (MIT 1988) + *Logics in CS* (1987). Original preferential semantics; representation theorem incorrect as stated (KLM fix).
- Pearl-Geffner [34] — *Probabilistic semantics for a subset of default reasoning*, UCLA TR. Built on Adams + system P.
- Burgess [4] — *Quick completeness proofs for some logics of conditionals*, NDJFL 1981. P is the flat fragment of Burgess' system S.
- Veltman [47] — *Logics for Conditionals*, PhD 1986. Closest semantic analog to KLM's preferential.
- Gabbay [10] — original Reflexivity/Cut/CM proposal; system C closely matches.
- Reiter [36] — *Nonmonotonic Reasoning*, ARCS 1987. Survey reference for the field at the time.
