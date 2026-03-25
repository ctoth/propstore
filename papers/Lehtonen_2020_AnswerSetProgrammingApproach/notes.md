---
title: "An Answer Set Programming Approach to Argumentative Reasoning in the ASPIC+ Framework"
authors: "Tuomo Lehtonen, Johannes P. Wallner, Matti Järvisalo"
year: 2020
venue: "KR 2020 - 17th International Conference on Principles of Knowledge Representation and Reasoning"
doi_url: "https://doi.org/10.24963/kr.2020/63"
---

# An Answer Set Programming Approach to Argumentative Reasoning in the ASPIC+ Framework

## One-Sentence Summary
Provides a direct ASP encoding for computing argumentation semantics in ASPIC+ (without preferences), bypassing the exponential blowup of translating to abstract AFs, with formal correctness proofs and empirical scalability results.

## Problem Addressed
Reasoning in ASPIC+ has lacked efficient practical implementations. The standard approach of translating ASPIC+ to abstract argumentation frameworks (AFs) and then using AF solvers is problematic because the translation can produce exponentially many arguments from a polynomially-sized ASPIC+ theory. Direct computational approaches were needed. *(p.1)*

## Key Contributions
- Introduces **argumentation theories (ATs)** as a restricted instantiation of ASPIC+ without preferences, contrariness only on ordinary premises, and all strict rules *(p.1-2)*
- Establishes a formal notion of **σ-assumptions** — pairs (P, D) of ordinary premises and defeasible rules — that correspond exactly to σ-extensions of the corresponding AF (Theorem 5) *(p.3-5)*
- Proves **complexity results**: credulous justification is NP-complete under admissible/complete/stable/preferred; skeptical justification is coNP-complete under stable, Π₂ᴾ-complete under preferred *(p.6)*
- Develops **direct ASP encodings** for reasoning about acceptance in ASPIC+ under conflict-free, admissible, complete, stable, and preferred semantics *(p.6-7)*
- Empirically demonstrates the ASP approach **scales to frameworks of significant size** (up to N=3000 atoms with 15 axioms) *(p.8)*

## Methodology
The paper works in three stages:
1. **Formal foundations**: Define argumentation theories (ATs), define σ-assumptions as pairs of defeasible elements, prove equivalence with AF extensions (Theorem 5)
2. **Complexity analysis**: Use the assumption-based reformulation to establish complexity bounds by working on polynomially-bounded structures
3. **ASP encoding**: Translate the assumption-based characterization directly into ASP rules, avoiding the exponential AF construction

## Key Definitions

### Argumentation Theory (AT)
An AT is a tuple T = (L, R, n, ‾, K) where: *(p.2)*
- L = set of atoms (language)
- R = Rₛ ∪ Rₐ (strict rules and defeasible rules)
- n: Rₐ → L maps each defeasible rule to its name
- ‾ : contrafunction mapping atoms to contrary sets
- K = Kₚ ∪ Kₐ (ordinary premises and axiom premises)

Restrictions vs full ASPIC+: *(p.2)*
- Contrariness only defined on ordinary premises (not axioms or rule names)
- All strict rules (no strict premises with contraries)
- No preferences

### Arguments in ATs
An argument A in AT T is defined recursively: *(p.2)*
1. A = p with p ∈ Kₚ ∪ Kₐ is an argument with Conc(A) = p
2. A = [A₁,...,Aₙ → c] if there is strict rule body(r) → head(r) with Conc(Aᵢ) matching body
3. A = [A₁,...,Aₙ ⇒ c] if there is defeasible rule body(r) ⇒ head(r) with Conc(Aᵢ) matching body

### Attacks
Three types of attack from argument A on argument B: *(p.2)*
1. **Undermining**: A undermines B if Conc(A) ∈ p̄ for some ordinary premise p in B
2. **Rebutting**: A rebuts B on B' ∈ Sub(B) if Conc(A) ∈ head(r) for the top defeasible rule r of B'
3. **Undercutting**: A undercuts B on B' ∈ Sub(B) if Conc(A) ∈ n(r) for the top defeasible rule r of B'

### σ-Assumptions (Core Innovation)
A pair (P, D) where P ⊆ Kₚ and D ⊆ Rₐ: *(p.3)*

$$
\text{att}(P, D) = \{x \in K_p \cup R_d \mid \exists c \in \bar{x}, c \in Th_T(P, D)\}
$$

Where ThT(P, D) = set of all atoms derivable from premises P using rules in D plus all strict rules. *(p.3)*

- **Conflict-free**: (P, D) does not attack any x ∈ P ∪ D
- **Admissible**: conflict-free and defends all its elements
- **Complete**: admissible and includes everything it defends (except non-applicable rules)
- **Stable**: conflict-free and attacks or contains every ordinary premise, and attacks/contains/renders-non-applicable every defeasible rule
- **Preferred**: ⊑-maximal admissible (where ⊑ is subset ordering on both P and D components)

### Theorem 5 (Main Correspondence)
For AT T, σ ∈ {adm, com, prf, stb}, and AF F corresponding to T: *(p.5)*
- If (P, D) is a σ-assumption in T, then E = {A | A based on (P, D)} is a σ-extension of F
- If E is a σ-extension of F, then (Premₐ(E), DefRules(E)) is a σ-assumption of T

This means reasoning can be done entirely on (P, D) pairs without constructing arguments.

## Key Equations

$$
Th_T(P, D) = \{c \in L \mid c \text{ derivable from } P \cup K_a \text{ using rules in } D \cup R_s\}
$$
Where: P = ordinary premises, D = defeasible rules, Kₐ = axiom premises, Rₛ = strict rules
*(p.3)*

$$
\text{att}(P, D) = \{x \in K_p \cup R_d \mid \exists c \in \bar{x}, c \in Th_T(P, D)\}
$$
Where: Kₚ = ordinary premises, Rₐ = defeasible rules, x̄ = contraries of x
*(p.3)*

$$
\text{def}(P, D) = (K_p \setminus \text{att}(P, D), \{r \in R_d \setminus \text{att}(P, D) \mid r \text{ applicable by } (P', D')\})
$$
Where: (P', D') = (Kₚ \ att(P,D), Rₐ \ att(P,D))
*(p.3)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of atoms | N | - | - | 5-3000 | 8 | Benchmark parameter |
| Number of axioms | \|Kₐ\| | - | 15 | - | 8 | Fixed in experiments |
| Defeasible rules ratio | - | % | 0.75, 0.19, 0.15, 0.1 | - | 8 | Fraction of atoms as defeasible rules |
| Ordinary premises ratio | - | % | 0.25 | - | 8 | Fraction of atoms as ordinary premises |
| Body size | - | rules | - | 1-15 | 8 | Random, chosen from [1, 15] |

## Implementation Details

### ASP Encoding Structure (Listings 1-4)
The ASP encoding uses several modules: *(p.7)*

**Listing 1: Module Γ_guess** — guesses a subset of defeasible elements:
- `{sel(X) : ordinary(X)}` — select ordinary premises
- `{sel(X) : defeasible(X)}` — select defeasible rules
*(p.7)*

**Listing 2: Module Δ_der** — computes derivations from selected elements:
- `deriv(X) :- sel(X), ordinary(X)` — selected premises are derived
- `deriv(X) :- axiom(X)` — axioms always derived
- `deriv(head(R)) :- defeasible(R), sel(R), deriv(body elements)` — apply defeasible rules
- `deriv(head(R)) :- strict(R), deriv(body elements)` — apply strict rules
*(p.7)*

**Listing 3: Module Δ_adm** — enforces admissibility:
- Computes attacks: `defeated_by(underlying(X)) :- supported_by_undefeated(X), ...`
- Ensures conflict-free: `:- sel(X), defeated_by(sel(X))`
- Ensures defense: `:- sel(X), defeated_by(X), not defeated_by(underlying(X))`
*(p.7)*

**Listing 4: Module Δ_sem(σ)** — encodes specific semantics: *(p.7)*
- **Complete**: adds `sel(X) :- ordinary(X), not defeated_by(X)` and similar for defeasible rules (forces inclusion of defended elements)
- **Stable**: adds `:- ordinary(X), not sel(X), not defeated_by(X)` (every unselected premise must be attacked) and similar constraints
- **Preferred**: uses saturation technique with `block_cand` atoms and `not not` patterns

### Encoding for Preferred Semantics
Uses the **saturation-based approach**: *(p.7)*
- Guess a candidate assumption, verify admissibility
- Then check there is no strictly larger admissible assumption (coNP check)
- Encoding uses `block_cand` constraints and saturation (standard ASP technique for Π₂ᴾ problems)

### Full ASP Program Construction
For semantics σ, the program is: *(p.7)*
- Conflict-free: Γ_guess ∪ Δ_der ∪ conflict-free constraints
- Admissible: Γ_guess ∪ Δ_der ∪ Δ_adm
- Complete: Γ_guess ∪ Δ_der ∪ Δ_adm ∪ Δ_sem(com)
- Stable: Γ_guess ∪ Δ_der ∪ Δ_adm ∪ Δ_sem(stb)
- Preferred: Γ_guess ∪ Δ_der ∪ Δ_adm ∪ Δ_sem(prf)

### Theorem 3 (Correctness)
For each σ ∈ {cf, adm, com, stb, prf}, an answer set of the encoding corresponds to a σ-assumption, and vice versa. *(p.7)*

## Figures of Interest
- **Fig 1 (p.2):** Example AT and corresponding AF — shows how an AT with atoms {a, b, c, d, e}, rules r1-r3, and premises maps to an abstract AF with 7 arguments
- **Table 1 (p.8):** Instances and mean runtimes with 15 axioms — shows scalability across N=5 to N=3000
- **Fig 2 (p.8):** Impact of number of axioms on mean runtimes — shows runtime growth with increasing axiom count

## Results Summary
- Benchmarks generated with N atoms (5 to 3000), 25 frameworks per N, 4 semantics per framework *(p.8)*
- Used Clingo 4.5.0 as ASP solver on Intel Xeon E5-2680 v4 *(p.8)*
- Timeout: 300s per instance *(p.8)*
- With N=3000 and 15 axioms: approach solves majority of instances for all semantics and reasoning modes *(p.8)*
- Credulous reasoning faster than skeptical under preferred semantics *(p.8)*
- Small numbers of axioms (5) drops timeout rate; larger numbers (19+) increase difficulty *(p.8)*
- Runtime scales well: at N=500, mean runtimes under 1 second for most configurations *(p.8)*

## Limitations
- Restricted to ASPIC+ **without preferences** — the full ASPIC+ with last-link or weakest-link orderings is not covered *(p.1, p.8)*
- Only **contrariness on ordinary premises** — no contrariness on axioms or rule names *(p.2)*
- Only **strict rules** in the strict part — no defeasible strict rules *(p.2)*
- Benchmarks are randomly generated, not from real-world applications *(p.8)*
- Does not handle **incomplete information** (stability/relevance problems) — addressed in their later 2023 paper *(p.1)*

## Arguments Against Prior Work
- The standard approach of translating ASPIC+ to AFs and then using AF solvers suffers from **exponential blowup** — ATs can yield exponentially many arguments *(p.1, p.6)*
- Prior ASPIC+ implementations like TOAST (Snaith and Reed 2012) are **online tools, not scalable solvers** *(p.1)*
- Approaches based on deductive argumentation (DeLPG, DASP) use **different formalisms** that don't capture ASPIC+ directly *(p.1)*
- The authors' own prior work on ABA (Lehtonen, Wallner, Järvisalo 2019) handles assumption-based argumentation but **not ASPIC+ specifically** *(p.1)*

## Design Rationale
- **Why assumptions instead of arguments?** Arguments can be exponentially many; assumption pairs (P, D) are polynomially bounded by the input AT *(p.3, p.6)*
- **Why ASP?** The complexity of credulous reasoning (NP-complete for most semantics) matches the complexity of answer set existence, making ASP a natural fit *(p.6)*
- **Why saturation for preferred?** Preferred semantics requires a Π₂ᴾ check (⊑-maximality of admissible sets), which the saturation technique in ASP handles declaratively *(p.7)*
- **Why no preferences?** Handling preferences (last-link, weakest-link) significantly changes the complexity landscape — addressed in their later 2024 paper *(p.8)*

## Testable Properties
- For any AT T and σ ∈ {adm, com, prf, stb}: σ-assumptions biject with σ-extensions of the corresponding AF (Theorem 5) *(p.5)*
- Every stable assumption is admissible (Proposition 3) *(p.5)*
- Credulous justification under adm = credulous justification under com = credulous justification under prf (Proposition 6) *(p.6)*
- The number of σ-assumptions is at most 2^|Kₚ| × 2^|Rₐ| (polynomial bound on search space) *(p.6)*
- Each answer set of the ASP encoding Π(T, σ) corresponds to exactly one σ-assumption (Theorem 3) *(p.7)*
- If (P, D) is conflict-free and not stable, then either ∃p ∈ Kₚ not in P and not attacked by (P,D), or ∃r ∈ Rₐ not in D, not attacked, and applicable *(p.3)*

## Relevance to Project
This paper is directly relevant to propstore's argumentation layer (Layer 4). It provides:
1. A practical computational approach for ASPIC+ that avoids the exponential AF construction — important for scaling propstore's argumentation
2. The σ-assumption reformulation could simplify propstore's implementation: instead of enumerating all arguments, work with (premise, rule) pairs
3. The ASP encodings (Listings 1-4) are directly implementable and could serve as the computational backend for ASPIC+ reasoning in propstore
4. The complexity results confirm that credulous reasoning is NP-complete (feasible with SAT/ASP) while skeptical preferred reasoning is Π₂ᴾ-complete (harder, needs iterative approach)

## Open Questions
- [ ] How do preferences (last-link, weakest-link) change the encodings? (Addressed in Lehtonen et al. 2022, 2024)
- [ ] How does incomplete information interact with assumptions? (Addressed in Odekerken et al. 2023)
- [ ] Can the ASP encoding be extended to handle bipolar argumentation (support + attack)?
- [ ] What is the practical performance comparison with translating to AFs and using state-of-art AF solvers?

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — cited as foundational; AF semantics (admissible, preferred, stable, complete) are the target that Theorem 5 connects σ-assumptions to
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — cited as "Modgil & Prakken 2013"; defines the full ASPIC+ framework with preferences that this paper restricts to the preference-free case
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — the tutorial introduction to ASPIC+ that presents the framework this paper implements computationally
- [[Odekerken_2023_ArgumentationReasoningASPICIncompleteInformation]] — co-authored by Lehtonen and Wallner; extends this paper's ASP encodings with incomplete-information reasoning (stability and relevance)

### New Leads (Not Yet in Collection)
- Lehtonen, Wallner, Järvisalo 2019 — ASP for assumption-based argumentation (ABA), predecessor to this work
- Lehtonen, Wallner, Järvisalo 2022 — Extends to weakest-link preferences in ASPIC+
- Lehtonen, Odekerken, Wallner, Järvisalo 2024 — Full preferences with last-link principle
- Snaith and Reed 2012 — TOAST: online ASPIC+ implementation (comparison point)
- Brewka, Delgrande, Romero, Schaub 2015 — asprin: customizing answer set preferences (different approach to preference handling in ASP)

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- [[Odekerken_2023_ArgumentationReasoningASPICIncompleteInformation]] — cited as ref 15; this paper's ASP encodings are the base that Odekerken et al. extend with incomplete-information reasoning

### Conceptual Links (not citation-based)
- [[Brewka_1989_PreferredSubtheoriesExtendedLogical]] — **Moderate.** Brewka's preferred subtheories provide the semantic target for ASPIC+ with classical logic instantiation (Modgil & Prakken 2018 Theorem 31). Lehtonen's ASP encodings handle the preference-free case; extending them to handle preferences would need to account for the preferred subtheory correspondence.
- [[Amgoud_2011_NewApproachPreference-basedArgumentation]] — **Moderate.** Amgoud & Vesic propose preference handling at the semantics level rather than attack-removal; Lehtonen's restriction to preference-free ASPIC+ sidesteps this debate entirely, but any extension to preferences must engage with it.

## Related Work Worth Reading
- Lehtonen, Wallner, Järvisalo 2019 — ASP for assumption-based argumentation (ABA), predecessor to this work
- Lehtonen, Wallner, Järvisalo 2022 — Extends to weakest-link preferences in ASPIC+
- Lehtonen, Odekerken, Wallner, Järvisalo 2024 — Full preferences with last-link principle
- Odekerken, Lehtonen, Borg, Wallner, Järvisalo 2023 — Incomplete information in ASPIC+
- Modgil and Prakken 2018 — The ASPIC+ framework definition (Handbook of Formal Argumentation ch.6)
- Snaith and Reed 2012 — TOAST: online ASPIC+ implementation (comparison point)
