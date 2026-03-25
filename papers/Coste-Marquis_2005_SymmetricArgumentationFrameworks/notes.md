---
title: "Symmetric Argumentation Frameworks"
authors: "Sylvie Coste-Marquis, Caroline Devred, Pierre Marquis"
year: 2005
venue: "ECSQARU 2005, LNCS 3571"
doi_url: "https://doi.org/10.1007/11518655_28"
---

# Symmetric Argumentation Frameworks

## One-Sentence Summary
Characterizes the family of Dung argumentation frameworks with symmetric (and irreflexive, nonempty) attack relations, proving that all standard semantics collapse to at most two distinct forms of acceptability and that the generalized acceptability problems remain tractable only for grounded/naive semantics.

## Problem Addressed
Dung's theory of argumentation is general-purpose but says nothing about what happens when the attack relation has structural properties. Symmetric frameworks (mutual attacks only) arise naturally when arguments are built from a knowledge base containing contradictions. The paper asks: what simplifications to the semantics and what complexity gains (or losses) follow from restricting to symmetric attacks? *(p.1)*

## Key Contributions
- Shows that no symmetric argumentation framework is well-founded (Proposition 3) *(p.6)*
- Proves every symmetric AF is both coherent and relatively grounded (Propositions 5, 9) *(p.5, p.7)*
- Demonstrates that preferred extensions = stable extensions = naive extensions in symmetric AFs, and complete extensions = grounded plus preferred (Proposition 4, Proposition 5) *(p.6)*
- Establishes that there are at most two distinct forms of acceptability for symmetric AFs: skeptical (= grounded) and credulous w.r.t. preferred/stable/naive (all coincide) *(p.8)*
- Provides complete complexity map for set-of-arguments acceptability problems under all standard semantics for symmetric AFs (Propositions 10, 11, 12) *(p.8-10)*
- Shows that the grounded extension of a symmetric AF is exactly the set of unattacked arguments, computable in linear time (Proposition 7) *(p.7)*
- Proves every argument belongs to at least one preferred (= stable = naive) extension (Proposition 6) *(p.6)*

## Methodology
The paper works entirely within Dung's abstract argumentation framework, restricting to the subfamily where the attack relation R is symmetric and irreflexive. It applies graph-theoretic reasoning (symmetric digraphs correspond to undirected graphs; conflict-free sets are independent sets; naive extensions are maximal independent sets; stable extensions are maximal independent sets that dominate). Proofs are largely combinatorial, using the characteristic function and fixed-point theory. *(p.2-10)*

## Key Equations

### Characteristic Function
$$
\mathcal{F}_{AF}(S) = \{a \mid a \text{ is acceptable w.r.t. } S\}
$$
Where: $AF = \langle A, R \rangle$ is a finite argumentation framework, $S \subseteq A$, and $a$ is acceptable w.r.t. $S$ iff for every $b \in A$ s.t. $(b, a) \in R$, there exists $c \in S$ s.t. $(c, b) \in R$. *(p.4)*

### Grounded Extension (Symmetric Case)
$$
E_G = \{a \in A \mid \nexists b \in A, (b, a) \in R\}
$$
Where: In a symmetric AF, the grounded extension is exactly the set of arguments that are not attacked by any argument. *(p.7)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Arguments | A | - | - | finite set | p.2 | Set of arguments in the framework |
| Attack relation | R | - | - | binary on A | p.2 | Must be symmetric and irreflexive for this paper |

## Implementation Details
- A symmetric AF is a finite digraph where R is symmetric and irreflexive *(p.6)*
- Graph-theoretically, symmetric AFs correspond to undirected graphs (edges = mutual attacks) *(p.6)*
- Conflict-free sets = independent sets in the corresponding undirected graph *(p.3)*
- Naive extensions = maximal independent sets *(p.3)*
- Stable extensions = maximal independent sets that dominate all other vertices *(p.6)*
- In symmetric AFs, every preferred extension is also a naive extension (Proposition 5) *(p.6)*
- The grounded extension consists of exactly the unattacked arguments, computable in O(|AF|) *(p.7)*
- Every argument a belongs to every preferred extension iff a is not attacked (Proposition 8) *(p.7)*
- An argument not in the grounded extension still belongs to at least one preferred extension (Proposition 6) *(p.6)*
- For set-of-arguments acceptability: checking whether S is in every/some preferred extension is coNP-complete/NP-complete (Proposition 11) *(p.9)*
- Reductions come from the fact that preferred = stable = naive in symmetric AFs, and checking independent set membership/existence in graphs *(p.9)*

## Figures of Interest
- **Fig 1 (p.3):** Digraph for running example AF with 5 arguments {a,b,c,d,e} and symmetric attack relation. Shows mutual attacks between b-c, b-d, c-d, c-e, plus a attacks nothing.

## Results Summary
The paper's main structural results: *(p.6-10)*
1. Symmetric AFs are never well-founded but always coherent and relatively grounded
2. The hierarchy of Dung semantics collapses: preferred = stable = naive (as extensions)
3. Complete extensions are exactly: the grounded extension plus all preferred extensions
4. The grounded extension = unattacked arguments (linear time)
5. For single-argument acceptability, skeptical acceptance is trivial (just check if unattacked) and credulous acceptance is trivial (every argument is credulously accepted)
6. For set-of-arguments acceptability, the complexity picture matches independent set problems on graphs: coNP-complete for skeptical/preferred, NP-complete for credulous/preferred, P for grounded/naive

## Limitations
- Restricted to finite AFs only *(p.2)*
- The symmetry + irreflexivity requirement is quite strong; many real argumentation scenarios involve asymmetric attacks *(p.1)*
- The paper acknowledges that skeptical acceptability under the grounded extension is "rather poor" for symmetric AFs since it only accepts unattacked arguments *(p.8)*
- Does not address weighted or probabilistic extensions *(p.10)*
- Connection to structured argumentation (ASPIC+, logic-based AF construction) only briefly mentioned *(p.1)*

## Arguments Against Prior Work
- Prior complexity results (Dimopoulos et al., Dunne & Bench-Capon) focused on single-argument acceptability; the paper argues this trivializes for symmetric AFs and one must consider set-of-arguments problems to get meaningful complexity distinctions *(p.8)*
- The Elvang-Goransson et al. approach to logic-based argumentation forces symmetric attacks, but the authors note this is not the only way symmetric AFs arise *(p.1)*

## Design Rationale
- Symmetric AFs are studied because they naturally arise in logic-based argumentation when the rebuttal relation is used (if argument A rebuts argument B, then B rebuts A) *(p.1)*
- The symmetry requirement is not "an assumption about the nature of an argument" but arises from the structure of contradiction in the underlying logic *(p.1)*
- Set-of-arguments acceptability is studied instead of single-argument because single-argument problems trivialize under symmetry *(p.8)*

## Testable Properties
- For any symmetric AF: the set of preferred extensions equals the set of stable extensions equals the set of naive extensions *(p.6)*
- For any symmetric AF: the grounded extension = {a in A | no b attacks a} *(p.7)*
- For any symmetric AF: every argument belongs to at least one preferred extension *(p.6)*
- For any symmetric AF: the framework is coherent (every preferred extension is stable) *(p.5)*
- For any symmetric AF: the framework is relatively grounded (grounded = intersection of preferred) *(p.5, p.7)*
- No symmetric AF is well-founded *(p.6)*
- For any symmetric AF: an argument a is in every preferred extension iff a is unattacked *(p.7)*
- ACCEPTABILITY_{forall,N} is in P for symmetric AFs *(p.8)*
- ACCEPTABILITY_{forall,P} is coNP-complete for symmetric AFs *(p.9)*
- ACCEPTABILITY_{exists,P} is NP-complete for symmetric AFs *(p.9)*

## Relevance to Project
Directly relevant to propstore's argumentation layer. When claims from different sources contradict each other symmetrically (each rebuts the other), the attack graph is symmetric. This paper shows that in such cases: (1) the preferred/stable/naive semantics all coincide, simplifying implementation; (2) the grounded extension is trivially the unattacked claims; (3) meaningful conflict resolution requires considering sets of arguments, not individual ones. This informs how propstore should handle symmetric contradiction patterns -- the grounded semantics is too conservative (only accepts uncontested claims), while preferred semantics requires solving an NP-complete problem but gives every argument a chance at acceptance.

## Open Questions
- [ ] How does this interact with ASPIC+ preference orderings that might break symmetry?
- [ ] Does the equivalence preferred=stable=naive hold when symmetric AFs are extended with support (bipolar)?
- [ ] What happens to these results under incomplete information (Odekerken 2022)?

## Related Work Worth Reading
- Elvang-Goransson et al. [11, 12]: Logic-based argumentation that naturally produces symmetric attacks
- Baroni & Giacomin [20, 21, 22]: Extending abstract argumentation systems theory, odd-length cycles, recursive approach -- relevant to understanding when symmetry interacts with cycles
- Cayrol et al. [23]: Minimal defence refinement of preferred semantics
- Dunne & Bench-Capon [26]: Coherence in finite argument systems -- provides the complexity baselines this paper extends
- Dimopoulos et al. [19]: Computational complexity of assumption-based argumentation for default reasoning

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — the foundational paper defining AFs, extensions, and all semantics that this paper restricts to symmetric attacks
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] — same year, same venue tradition; extends Dung AFs with support relation (bipolar), while this paper restricts to symmetric attacks. Complementary structural investigations.
- [[Simari_1992_MathematicalTreatmentDefeasibleReasoning]] — cited as [8] for defeasible reasoning foundations
- [[Pollock_1987_DefeasibleReasoning]] — cited as [7] for defeasible reasoning theory
- [[Baroni_2005_SCC-recursivenessGeneralSchemaArgumentation]] — Baroni & Giacomin's recursive approach cited as [22]; their SCC decomposition handles odd-length cycles while this paper shows even-length cycles (from symmetric mutual attacks) have cleaner semantics
- [[Baroni_2007_Principle-basedEvaluationExtension-basedArgumentation]] — evaluates argumentation principles including coherence and relative groundedness, which this paper proves hold universally for symmetric AFs
- [[Amgoud_2011_NewApproachPreference-basedArgumentation]] — Amgoud & Cayrol cited as [13, 15, 16] for preference-based argumentation

### New Leads (Not Yet in Collection)
- Dunne & Bench-Capon (2002) — "Coherence in finite argument system" — Artificial Intelligence 141:187-203 — provides complexity baselines for general AFs that this paper specializes to symmetric
- Dimopoulos, Nebel & Toni (2002) — "On the computational complexity of assumption-based argumentation" — AI 141:57-78 — single-argument complexity results extended here to set-of-arguments
- Elvang-Goransson, Fox & Krause (1993) — "Dialectic reasoning with inconsistent information" — motivation for symmetric AFs from logic-based argumentation
- Bondarenko, Dung, Kowalski & Toni (1997) — "An abstract argumentation-theoretic approach to default reasoning" — AI 93:63-101 — foundational structured argumentation

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- (none found — collection papers referencing "Coste-Marquis 2005" cite the companion "Prudent semantics" paper, not this one)

### Conceptual Links (not citation-based)
- [[Dung_1995_AcceptabilityArguments]] — Dung defines coherence (preferred=stable) and relative groundedness (grounded = intersection of preferred) as properties some AFs have; this paper proves all symmetric AFs have both properties universally, strengthening Dung's Theorem 33 (limited controversial => coherent) since symmetric AFs are a different structural class
- [[Baroni_2005_SCC-recursivenessGeneralSchemaArgumentation]] — Baroni's SCC-recursive approach and CF2 semantics handle problematic cases (odd-length cycles) where standard semantics fail; symmetric AFs create only even-length cycles (every mutual attack is a 2-cycle), explaining why standard semantics behave well here — the pathologies CF2 was designed to fix cannot arise in symmetric frameworks
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] — Cayrol's bipolar AFs add support alongside attack; an open question is whether adding support to a symmetric AF preserves the collapse of preferred/stable/naive, since supported defeats could introduce asymmetry
- [[Caminada_2006_IssueReinstatementArgumentation]] — Caminada's labelling approach (in/out/undec) applied to symmetric AFs would yield: every argument is either IN (unattacked, in grounded) or in an even cycle where it alternates between preferred extensions — semi-stable semantics would coincide with preferred since preferred=stable here
