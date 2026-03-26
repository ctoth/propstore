---
title: "On Computing Explanations in Argumentation"
authors: "Xiuyi Fan, Francesca Toni"
year: 2015
venue: "Proceedings of the Twenty-Ninth AAAI Conference on Artificial Intelligence"
doi_url: "https://doi.org/10.1609/aaai.v29i1.9420"
---

# On Computing Explanations in Argumentation

## One-Sentence Summary
Introduces "related admissibility," a new argumentation semantics designed specifically for computing explanations of why arguments are acceptable, applicable to both Abstract Argumentation (AA) and Assumption-based Argumentation (ABA), with a correct computational counterpart via dispute forests.

## Problem Addressed
Existing argumentation semantics (grounded, preferred, stable, complete) identify *which* arguments are acceptable but do not provide concrete justifications for *why* they are acceptable. The paper addresses the gap between acceptability computation and explanation generation. *(p.1)*

## Key Contributions
- A new argumentation semantics called **related admissibility** for both AA and ABA *(p.1)*
- Identification of different types of explanations (Minimal, Compact, Maximal Explanations, and MuEs) defined in terms of the new semantics *(p.3)*
- A correct computational counterpart using **dispute forests** *(p.3-4)*
- Proof that dispute trees/forests can be used to compute related admissible assumptions *(p.4)*
- Extension to ABA with concrete examples including a decision-making scenario *(p.4-5)*

## Methodology

### Abstract Argumentation (AA) Setting
Given a standard AA framework (Args, Attacks), the paper defines "related admissibility" to filter out irrelevant arguments from explanations. The key insight: standard admissible sets can contain arguments that play no role in defending the argument being explained. *(p.1-2)*

### Assumption-based Argumentation (ABA) Setting
An ABA framework is a tuple (L, R, A, C) where L is a language, R is a set of rules, A is a set of assumptions, and C is a contrariness mapping. Arguments are deductions from assumptions using rules. *(p.2)*

### Dispute Trees and Forests
The computational mechanism uses dispute trees (from Dung, Kowalski, and Toni 2006/2009) extended to dispute forests. A dispute forest for a set S of arguments consists of dispute trees for each argument in S. *(p.3-4)*

## Key Definitions

### Definition 1: Explanations in AA *(p.2)*
Given an AA framework (Args, Attacks) and argument A in Args:
- X attacks A if X attacks some member of A (set-level attack)
- A is **related admissible** if:
  1. A is admissible (conflict-free + defends all its members)
  2. For every argument B in A, either B = the target argument, or B defends some member of A against an attacker

### Definition 3: Types of Explanations in AA *(p.3)*
Given AA framework and argument A with related admissible set S:
- **Minimal Explanation (MiE):** S is a smallest related admissible set containing A
- **Compact Explanation (CoE):** S is smaller than the set of all admissible arguments for A
- **Maximal Explanation (MaE):** S is the largest related admissible set for A
- **MuE (a.k.a. "Mull Explanation"):** S contains all related admissible arguments

Invariants: MiEs and CoEs are subsets of MaE; MaE is unique. *(p.3)*

### Definition 7: Related Admissibility in AA (formal) *(p.2)*
Given an AA framework (Args, Attacks), a set S of arguments is related admissible for A in Args iff:
1. A is in S
2. S is admissible
3. For every B in S with B != A, B defends some element of S

### Definition 10: Related Admissibility in ABA *(p.5)*
Given an ABA framework (L, R, A, C):
- A set of assumptions Delta is **related admissible** w.r.t. a set of sentences sigma iff:
  1. Delta is admissible
  2. There exists a topic sentence t of S (i.e., t is the claim of some argument supported by a subset of Delta)
  3. For every argument of Delta not supporting t, it defends some argument of S

### Definition 14: Admissible Dispute Forest in ABA *(p.4)*
Given an ABA framework (L, R, A, C) and a sentence x in L, the dispute forest for x is (T/T) where T is an admissible dispute tree for x.

## Key Theorems

### Theorem 1 *(p.3)*
Given an AA framework (Args, Attacks) and an argument A, if F is an admissible dispute tree for A, then the set of proponent nodes in F (denoted P(F)) is a related admissible set for A.

### Theorem 3 *(p.3)*
Dispute trees can be used to compute related admissible assumptions. Given an admissible dispute tree T, the selected set of T is related admissible.

### Theorem 5 *(p.4)*
Given an AA framework (Args, Attacks) and a sentence x in L, if T is an admissible dispute tree for x, then {a|p} subset of P is a related admissible set. The converse also holds: every related admissible set can be obtained from an admissible dispute forest.

### Proposition 1 *(p.2)*
Given an AA framework (Args, Attacks), and a related admissible set S for A, for all S' subset of S with A in S', S' is a related admissible set iff S' is admissible.

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Argument set | Args | - | - | - | 1 | Set of all arguments in the framework |
| Attack relation | Attacks | - | - | - | 1 | Binary relation over Args |
| Language | L | - | - | - | 2 | Set of sentences in ABA |
| Rules | R | - | - | - | 2 | Inference rules in ABA |
| Assumptions | A | - | - | - | 2 | Distinguished subset of L |
| Contrariness | C | - | - | - | 2 | Mapping from assumptions to their contraries |

## Implementation Details
- Dispute trees are concrete data structures: trees where nodes alternate between proponent (P) and opponent (O) *(p.3)*
- A proponent node is labeled with an argument; an opponent node is labeled with an attacking argument *(p.3)*
- For ABA: dispute trees have nodes labeled with sets of assumptions and sentences, with proponent/opponent alternation *(p.4)*
- Computation proceeds by building dispute forests — collections of dispute trees for each argument that needs explanation *(p.4)*
- The selected set from a dispute forest gives the related admissible set *(p.4)*
- For finding MiE: find the smallest admissible dispute forest *(p.3)*
- For finding MaE: find the largest admissible dispute forest *(p.3)*
- In ABA, related admissibility works with assumptions rather than arguments directly *(p.5)*

## Figures of Interest
- **Fig 1 (p.3):** Dispute trees for A in Example 1 (use Example 1): shows four dispute trees T1-T4 for argument A, each with different proponent/opponent structure. The trees demonstrate how different dispute trees yield different related admissible sets.

## Results Summary
- Related admissibility is strictly more restrictive than standard admissibility — it excludes "freeloading" arguments that don't contribute to defense *(p.2)*
- Every related admissible set is admissible, but not vice versa *(p.2)*
- MaE is unique for a given argument *(p.3)*
- Dispute forests provide a sound and complete computational mechanism *(p.4)*
- The approach extends naturally from AA to ABA *(p.4-5)*
- In ABA, the approach handles decision-making scenarios where explanations for choices are needed *(p.4-5)*

## Limitations
- The paper acknowledges it focuses on generating explanations, not on evaluating their quality or user comprehension *(p.5)*
- The approach works only for admissibility-based semantics, not for preferred or stable extensions directly *(p.2)*
- Complexity analysis is not provided *(p.1-6)*
- The paper does not address how to present explanations to end users *(p.5-6)*

## Arguments Against Prior Work
- Standard admissibility semantics allows "freeloading" arguments that don't contribute to defense but are included in admissible sets — these make explanations bloated and confusing *(p.1-2)*
- Existing semantics (grounded, preferred, stable, complete) identify acceptable arguments but never explain *why* they are acceptable *(p.1)*
- Garcia and Sarmiento (2013) study dialectical explanation for argument-based reasoning in knowledge-based systems, but their work uses "explanations" to refer to sets of trees rather than defining explanation as a semantic property *(p.5-6)*
- Schulz and Toni (2013) use ABA to explain why a literal is or is not contained in an answer set, but do not formalize explanation as a semantics *(p.6)*

## Design Rationale
- Related admissibility is chosen over simply filtering admissible sets because it defines explanation as a *semantic* concept, not a post-processing step *(p.2)*
- Dispute forests (rather than single dispute trees) are used because a single tree may not capture all arguments needed for a complete explanation *(p.3-4)*
- The approach builds on existing dispute tree infrastructure from Dung/Kowalski/Toni, extending rather than replacing it *(p.3)*
- Both AA and ABA are supported because ABA provides structured argumentation needed for real applications while AA provides the theoretical foundation *(p.1)*

## Testable Properties
- Every related admissible set must be admissible (conflict-free + self-defending) *(p.2)*
- In a related admissible set S for argument A, every member B != A must defend some member of S against attack *(p.2)*
- MaE for a given argument is unique *(p.3)*
- Every MiE is a subset of MaE *(p.3)*
- Every CoE is a subset of MaE *(p.3)*
- The proponent nodes of an admissible dispute tree form a related admissible set *(p.3)*
- For any admissible set S, S is related admissible iff for every B in S with B != A, B defends some element of S *(p.2)*

## Relevance to Project
Directly relevant to propstore's argumentation layer. Related admissibility provides a principled way to generate explanations for why certain arguments (claims) are accepted in the AF. This connects to the render layer's need to explain resolution outcomes to users. The dispute forest computation can be implemented alongside existing Dung AF extension computation.

## Open Questions
- [ ] How does related admissibility interact with preferred/stable extensions?
- [ ] What is the computational complexity of finding MiE vs MaE?
- [ ] How to present dispute-forest-based explanations in propstore's CLI?
- [ ] Does the approach extend to bipolar argumentation frameworks (Cayrol 2005)?
- [ ] How does this relate to Odekerken's stability/relevance work for incomplete frameworks?

## Related Work Worth Reading
- Dung, Kowalski, and Toni 2006/2009 — Dispute trees for admissibility in ABA (foundational for the dispute forest mechanism)
- Garcia and Sarmiento 2013 — Dialectical explanation for argument-based reasoning
- Schulz and Toni 2013 — Using ABA to explain answer set membership
- Dong, Toni, and Mancarella 2010 — Three principles for designing argumentation systems (simplicity, transparency, arguments)
- Baroni and Giacomin 2007 — Semantics evaluation criteria (referenced for comparison)
- Zhong, Fan, Toni, and Luo 2014 — Explaining Bayesian networks via argumentation (CEUR)
- Modgil and Caminada 2009 — Proof procedures and algorithms for abstract argumentation
- Craven, Toni, and Williams 2013 — Graph-based dispute detection in assumption-based argumentation

## Collection Cross-References

### Papers in collection cited by this paper
- [[Baroni_2007_Principle-basedEvaluationExtension-basedArgumentation]] — Baroni & Giacomin 2007, semantics evaluation criteria
- [[Bondarenko_1997_AbstractArgumentation-TheoreticApproachDefault]] — Bondarenko et al 1997, abstract argumentation-theoretic approach to default reasoning
- [[Dung_1995_AcceptabilityArguments]] — Dung 1995, foundational AF semantics
- [[Pollock_1987_DefeasibleReasoning]] — Pollock 1987, defeasible reasoning
- [[Prakken_2010_AbstractFrameworkArgumentationStructured]] — Prakken 2010, abstract framework for structured argumentation
- [[Toni_2014_TutorialAssumption-basedArgumentation]] — Toni 2014, ABA tutorial

### Papers in collection that cite this paper
- [[Čyras_2021_ArgumentativeXAISurvey]] — cites Fan and Toni 2015b as central to extension-based explanations (Section 4); defines explanations as related admissible extensions

### New leads from citations
- Garcia, Chesnevar, Rotstein, Simari 2013 — dialectical explanation for argument-based reasoning in knowledge-based systems
- Schulz & Toni 2013 — ABA-based answer set justification
- Dong, Toni, Mancarella 2010 — three principles for designing argumentation systems
