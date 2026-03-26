---
title: "A new approach for preference-based argumentation frameworks"
authors: "Leila Amgoud, Srdjan Vesic"
year: 2011
venue: "Annals of Mathematics and Artificial Intelligence"
doi_url: "https://doi.org/10.1007/s10472-011-9271-9"
---

# A new approach for preference-based argumentation frameworks

## One-Sentence Summary
Proposes handling preferences in argumentation at the semantics level (via dominance relations on the powerset of arguments) rather than at the attack level (removing critical attacks), proving that existing attack-removal approaches produce conflicting extensions under asymmetric attack and providing three new preference-aware generalizations of stable, preferred, and grounded semantics with full axiomatic characterization.

## Problem Addressed
Existing preference-based argumentation frameworks (PAFs) — notably Amgoud & Cayrol [6], Bench-Capon [17], and Simari & Loui [38] — handle preferences by identifying "critical attacks" (where a stronger argument is attacked by a weaker one) and removing them before computing extensions. This works correctly when the attack relation is symmetric, but when attacks are asymmetric, removing attacks can produce **conflicting extensions** — extensions that contain arguments that attack each other. This violates the fundamental requirement that extensions represent coherent positions. *(p.1-3)*

## Key Contributions
1. **Critique of attack-removal approach**: Formal demonstration that removing critical attacks from asymmetric attack relations produces conflicting extensions and violates rationality postulates *(p.6-8)*
2. **Preferences at semantics level**: Novel approach that applies preferences when comparing sets of arguments (via dominance relations on P(A)) rather than modifying the attack relation *(p.9)*
3. **Three new semantics**: Pref-stable, Pref-preferred, and Pref-grounded, each generalizing the corresponding Dung semantics with preferences *(p.11-15)*
4. **Axiomatic characterization**: Six postulates (P1-P6) that fully characterize pref-stable semantics, with proof that all pref-stable relations yield identical maximal elements *(p.15-17)*
5. **Attack inversion method**: Polynomial-time reduction from PAF pref-stable extension computation to standard Dung stable extension computation *(p.18)*
6. **Complexity preservation**: Pref-stable semantics has the same computational complexity as standard stable semantics *(p.19)*
7. **Preferred sub-theories correspondence**: Full bijection between pref-stable extensions and Brewka's preferred sub-theories for weighted knowledge bases *(p.20-22)*

## Methodology

### Formal Framework
A **Preference-based Argumentation Framework (PAF)** is a triple T = (A, R, ≥) where: *(p.4)*
- A is a set of arguments
- R ⊆ A × A is an attack relation
- ≥ ⊆ A × A is a (partial or total) preorder on arguments

### The Critical Example (Example 1)
*(p.6)*

$$
\mathcal{A} = \{a, b\}, \quad \mathcal{R} = \{(a, b)\}, \quad b > a
$$

Under the attack-removal approach: the attack (a,b) is "critical" because b > a, so it is removed. This leaves Def = ∅. Then {a,b} becomes a stable extension — but a attacks b under R, so this extension is **not conflict-free**. This is the fundamental flaw.

### The Dominance Relation Approach
Instead of modifying attacks, define a **dominance relation** ≽ on P(A) × P(A) (the powerset of arguments). A semantics is such a dominance relation satisfying certain postulates. Extensions are the **maximal elements** of ≽. *(p.9-10)*

## Key Equations

### Three Core Postulates

**Postulate P1 (Conflict-freeness)**:
$$
\frac{\mathcal{E} \in CF(\mathcal{T}) \quad \mathcal{E}' \notin CF(\mathcal{T})}{\mathcal{E} \succ \mathcal{E}'}
$$
Where: CF(T) is the set of conflict-free sets of T; ≻ is strict preference.
*(p.10)*

**Postulate P2 (Attack wins when not critical)**:
$$
\frac{a\mathcal{R}a' \quad \neg(a'\mathcal{R}a) \quad \neg(a' > a)}{\{a\} \succ \{a'\}}
$$
Where: aRa' means a attacks a'; a' > a means a' is strictly preferred to a.
*(p.10)*

**Postulate P3 (Preferences privileged in critical attacks)**:
$$
\frac{a\mathcal{R}a' \quad a' > a}{\{a'\} \succ \{a\}}
$$
*(p.10)*

### Pref-stable Semantics (Definition 11)

$$
\mathcal{E} \succeq_s \mathcal{E}' \text{ iff } \begin{cases} \mathcal{E} \in CF(\mathcal{T}) \text{ and } \mathcal{E}' \notin CF(\mathcal{T}), \text{ or} \\ \mathcal{E}, \mathcal{E}' \in CF(\mathcal{T}) \text{ and } \forall a' \in \mathcal{E}' \setminus \mathcal{E}, \exists a \in \mathcal{E} \setminus \mathcal{E}' \text{ s.t. } (a\mathcal{R}a' \wedge \neg(a' > a)) \text{ or } (a > a') \end{cases}
$$
*(p.12)*

### Pref-preferred Semantics (Definition 12)

$$
\mathcal{E} \succeq_p \mathcal{E}' \text{ iff } \begin{cases} \mathcal{E} \in CF(\mathcal{T}) \text{ and } \mathcal{E}' \notin CF(\mathcal{T}), \text{ or} \\ \mathcal{E}, \mathcal{E}' \in CF(\mathcal{T}) \text{ and conditions on defense hold} \end{cases}
$$
Where: for all a ∈ E, for all a' ∈ E', if (a'Ra and not(a > a')) or (aRa' and a' > a), then ∃b ∈ E such that (bRa' and not(a' > b)) or (a'Rb and b > a').
*(p.13)*

### Pref-grounded Semantics (Definition 13-14)

**Strong defense** (Definition 13): E strongly defends argument a from attacks, where for each attacker of a, either the attack is "won" by a (via preferences) or there is a defender in E. *(p.14)*

**Pref-grounded semantics**: The paper defines a dominance relation `≽_g` over subsets: `E ≽_g E'` iff `E` is conflict-free while `E'` is not, or every argument in `E` is strongly defended against attacks coming from `E'`. Extensions are the maximal elements of this relation. *(p.14)*

**Implementation caution**: The paper page does not directly define pref-grounded as a simple unary characteristic-function least fixpoint. Any implementation that replaces the relation on subsets with a post-hoc pruning of a defeat-only fixpoint is making an extra move that needs its own justification. *(p.14-15)*

### Additional Characterization Postulates (Section 6.1)

**Postulate P4 (Incomparability blocks preference)**:
$$
\frac{(\exists a' \in \mathcal{E}')(\forall a \in \mathcal{E}) \neg(a\mathcal{R}a' \wedge \neg(a' > a)) \wedge \neg(a > a')}{\neg(\mathcal{E} \succeq \mathcal{E}')}
$$
Where: E, E' ∈ CF(T) and E ∩ E' = ∅.
*(p.15)*

**Postulate P5 (Winning condition)**:
$$
\frac{(\forall a' \in \mathcal{E}')(\exists a \in \mathcal{E}) \text{ s.t. } (a\mathcal{R}a' \wedge \neg(a' > a)) \text{ or } (a'\mathcal{R}a \wedge a > a')}{\mathcal{E} \succeq \mathcal{E}'}
$$
Where: E, E' ∈ CF(T) and E ∩ E' = ∅.
*(p.16)*

**Postulate P6 (Distinct elements determine preference)**:
$$
\frac{\mathcal{E} \succ \mathcal{E}'}{\mathcal{E} \setminus \mathcal{E}' \succeq \mathcal{E}' \setminus \mathcal{E}} \quad \text{and} \quad \frac{\mathcal{E} \setminus \mathcal{E}' \succ \mathcal{E}' \setminus \mathcal{E}}{\mathcal{E} \succeq \mathcal{E}'}
$$
Where: E, E' ∈ CF(T).
*(p.16)*

### Direct Characterization of Pref-stable Extensions (Theorem 10)

$$
\mathcal{E} \in \succeq_{max} \text{ iff } \mathcal{E} \in CF(\mathcal{T}) \text{ and } \forall a' \in \mathcal{A} \setminus \mathcal{E}, \exists a \in \mathcal{E} \text{ s.t. } (a\mathcal{R}a' \wedge \neg(a' > a)) \text{ or } (a'\mathcal{R}a \wedge a > a')
$$
*(p.18)*

### Attack Inversion Method (Theorem 11)

$$
\mathcal{R}' = \{(a,b) \mid (a,b) \in \mathcal{R} \wedge \neg(b > a)\} \cup \{(b,a) \mid (a,b) \in \mathcal{R} \wedge b > a\}
$$
Then: ≽_max = Ext_s(A, R') (stable extensions of the inverted framework).
*(p.18)*

### Preferred Sub-theory (Definition 18)
Let Σ be stratified into Σ_1 ∪ ... ∪ Σ_n. A preferred sub-theory is:
$$
\mathcal{S} = S_1 \cup \ldots \cup S_n \text{ s.t. } \forall k \in [1,n], S_1 \cup \ldots \cup S_k \text{ is a maximal consistent subbase of } \Sigma_1 \cup \ldots \cup \Sigma_k
$$
*(p.20)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Argument set | A | - | - | finite | 4 | Set of abstract arguments |
| Attack relation | R | - | - | R ⊆ A×A | 4 | May be symmetric or asymmetric |
| Preference preorder | ≥ | - | - | partial or total | 4 | Over individual arguments |
| Dominance relation | ≽ | - | - | ≽ ⊆ P(A)×P(A) | 9 | Over sets of arguments |
| Maximal elements | ≽_max | - | - | ⊆ P(A) | 9 | The extensions |

## Implementation Details

### Attack Inversion Algorithm (Theorem 11)
Given PAF T = (A, R, ≥): *(p.18)*
1. For each (a,b) ∈ R:
   - If not(b > a): keep (a,b) in R'
   - If b > a: add (b,a) to R' instead
2. Compute stable extensions of (A, R')
3. These are exactly the pref-stable extensions of T

This is a **polynomial-time reduction** — the PAF adds no complexity over standard AF computation.

### Pref-grounded Extension Computation (Definition 14)
*(p.14)*
1. Start with E_0 = ∅
2. At each step, E_{i+1} = F(E_i) where F adds arguments strongly defended by E_i
3. Continue until fixpoint: E* = F(E*)
4. E* is the unique pref-grounded extension

### Key Data Structures
- PAF triple: (A, R, ≥) *(p.4)*
- Dominance relation: binary relation on P(A) *(p.9)*
- Conflict-free sets: CF(T) = {E ⊆ A | ∄a,b ∈ E s.t. aRb} *(p.4)*
- Critical attack: (a,b) ∈ R where b > a *(p.5)*

## Figures of Interest
- **Fig 1 (p.22):** Preferred sub-theories of Σ mapped to Pref-stable extensions of (Arg(Σ), R_as, ≥_WLP) — shows the bijective correspondence
- **Fig 2 (p.30):** Counterexample proving no transitive relation can generalize stable semantics and satisfy P1 and P5 — framework with arguments x, y, z, a where transitivity forces {x} to be maximal but it's not a stable extension

## Results Summary

### Generalization Theorems
- Theorem 2: ≽_s generalizes stable semantics *(p.12)*
- Theorem 3: ≽_p generalizes preferred semantics *(p.13)*
- Theorem 5: ≽_g generalizes grounded semantics *(p.15)*

### Relationships Between Semantics
- Every pref-stable extension is pref-preferred (Theorem 4) *(p.13)*
- Pref-grounded ⊆ intersection of all pref-preferred (Theorem 6) *(p.15)*

### Uniqueness Results
- All pref-stable relations yield the same maximal elements (Theorem 7) *(p.16)*
- Pref-grounded extension is unique (Property 5) *(p.14)*

### Complexity (Theorem 12) *(p.19)*
- Verification: P (polynomial)
- Existence: NP-complete
- Credulous acceptance: NP-complete
- Skeptical acceptance: coNP-complete

### Non-transitivity
- ≽_s is NOT transitive (Example 4, p.12)
- ≽_p is NOT transitive (p.13)
- Property 9: NO transitive relation can generalize stable semantics and satisfy P1 + P5 *(p.17)*

## Limitations
- The dominance relation approach operates on P(A), which is exponential in |A| — though Theorem 11's attack inversion provides a polynomial reduction for pref-stable *(p.18)*
- Non-transitivity of the dominance relations means standard ordering techniques don't apply *(p.12, 17)*
- Only pref-stable semantics gets full axiomatic characterization; pref-preferred and pref-grounded are less thoroughly characterized *(p.15)*
- The approach assumes a fixed preference ordering over arguments; it does not address how preferences themselves should be derived *(p.4)*
- The paper focuses on abstract argumentation; extension to structured argumentation (like ASPIC+) is not addressed — this is exactly the gap that Modgil & Prakken 2018 addresses *(p.23-24)*

## Arguments Against Prior Work
- **Amgoud & Cayrol [6] approach**: Removing critical attacks produces conflicting extensions when attack is asymmetric (Example 1, p.6). Also violates rationality postulates of [24] *(p.6)*
- **Bench-Capon [17] approach**: Same problem — only correct when attack relation is symmetric *(p.3, 22)*
- **Simari & Loui [38] approach**: Same class of problem *(p.3)*
- **General critique of attack-removal**: Removing an attack loses information about the conflict between two arguments. When a stronger argument's attack is removed, the conflict disappears entirely — but the conflict still exists, the preference just determines who wins it *(p.8)*
- **Modgil [38] approach**: Also removes attacks, suffers from same fundamental problem *(p.5)*
- **Value-based AF [17]**: The framework in [17] is a particular case of the one in [6], which in turn suffers from the critical attack problem when attacks are asymmetric *(p.5)*

## Design Rationale
- **Why powerset-level dominance?** Because comparing individual arguments doesn't capture the collective strength of sets of arguments. A set may be preferred even if no single argument in it dominates the corresponding argument in the rival set. *(p.9)*
- **Why keep all attacks?** Removing attacks loses information. The conflict between a and b exists regardless of who is preferred. Preferences should determine the *winner* of a conflict, not whether the conflict exists. *(p.8)*
- **Why non-transitive relations?** Transitivity is incompatible with generalizing stable semantics (Property 9, p.17). The attack relation itself is not transitive, so expecting transitivity from a relation that encodes attack dynamics is unreasonable. *(p.17)*
- **Why six postulates for pref-stable?** P1 ensures conflict-freeness. P2-P3 handle attack vs preference priority. P4 prevents unjustified preferences. P5 encodes the "winning" condition. P6 ensures common elements don't affect comparison. Together they uniquely determine the pref-stable extensions (Theorem 7). *(p.15-17)*

## Testable Properties
- P1: Every pref-stable extension must be conflict-free w.r.t. R *(p.10)*
- P2: If a attacks a' and a' doesn't attack a and a' is not preferred to a, then {a} ≻ {a'} *(p.10)*
- P3: If a attacks a' and a' > a, then {a'} ≻ {a} *(p.10)*
- Theorem 2: When no critical attacks exist, pref-stable extensions = stable extensions *(p.12)*
- Theorem 4: Every pref-stable extension is a pref-preferred extension *(p.13)*
- Theorem 7: All pref-stable relations yield the same set of extensions *(p.16)*
- Theorem 10: Direct characterization — E is pref-stable iff CF and every external argument is "defeated" *(p.18)*
- Theorem 11: Pref-stable extensions = stable extensions of attack-inverted framework *(p.18)*
- Theorem 12: Complexity classes match standard stable semantics *(p.19)*
- Property 9: No transitive relation generalizes stable semantics with P1+P5 *(p.17)*

## Relevance to Project
This paper is directly relevant to propstore's argumentation layer. The key insight — that preferences should be applied at the semantics level rather than by modifying attacks — has implications for how propstore's render layer should handle preference orderings over competing claims. The attack inversion method (Theorem 11) provides a practical implementation path: transform the preference-augmented framework into a standard Dung AF and use existing extension computation. This paper is the primary critique that Modgil & Prakken 2018 rebuts in Section 6.2, making it essential context for understanding ASPIC+'s design choices around preference handling.

## Open Questions
- [ ] How does Modgil & Prakken 2018 respond to the conflict-freeness critique in their Section 6.2?
- [ ] Can the attack inversion method be composed with ATMS assumption labeling?
- [ ] How does the dominance relation approach interact with bipolar argumentation (Cayrol 2005)?
- [ ] Is the non-transitivity of ≽_s a problem in practice for propstore's rendering?

## Related Work Worth Reading
- [6] Amgoud and Cayrol 2002 — "A reasoning model based on the production of acceptable arguments" — the original PAF that this paper critiques
- [17] Bench-Capon 2003 — "Persuasion in practical argument using value-based argumentation frameworks" — value-based AF also critiqued
- [21] Brewka 1989 — "Preferred subtheories: An extended logical framework for default reasoning" — the preferred sub-theories that correspond to pref-stable extensions
- [24] Caminada and Amgoud 2007 — "On the evaluation of argumentation formalisms" — rationality postulates that attack-removal violates
- [29] Dung 1995 — "On the acceptability of arguments" — the foundational AF framework being extended
- [38] Modgil 2009 — "Reasoning about preferences in argumentation frameworks" — another attack-removal approach critiqued
- [39] Modgil and Prakken 2011 — "Revisiting preferences and argumentation" — IJCAI response
- [43] Prakken 2011 — "An abstract framework for argumentation with structured arguments" — ASPIC+ framework
