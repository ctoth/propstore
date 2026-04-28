---
title: "On principle-based evaluation of extension-based argumentation semantics"
authors: "Pietro Baroni, Massimiliano Giacomin"
year: 2007
venue: "Artificial Intelligence, 171(10-15), 675-700"
doi_url: "https://doi.org/10.1016/j.artint.2007.04.004"
---

# On principle-based evaluation of extension-based argumentation semantics

## One-Sentence Summary

Provides a systematic framework of formal principles (criteria) for evaluating and comparing extension-based argumentation semantics, applied to grounded, complete, preferred, stable, ideal, semi-stable, CF2, prudent, and SCC-recursive semantics.

## Problem Addressed

The increasing variety of argumentation semantics proposed in Dung's framework makes it difficult to choose among them for a given application. No systematic, principle-based methodology existed for comparing and evaluating these semantics. Prior comparisons were ad hoc, example-based, or limited to specific pairs. *(p.1)*

## Key Contributions

- Introduces a set of formal evaluation criteria (principles) for argumentation semantics, organized into: language independence, basic properties, extension-based criteria, and skepticism-related criteria *(p.1)*
- Provides a systematic evaluation of 8 argumentation semantics against these criteria *(p.1)*
- Introduces the SCC-recursive schema as a general framework capturing several semantics *(p.11-12)*
- Defines the notions of skepticism relations between sets of extensions and skepticism adequacy *(p.7-9)*
- Introduces resolution adequacy as a criterion *(p.9-10)*
- Provides a comprehensive summary table (Table 1, Table 2) of which semantics satisfy which principles *(p.13-14)*

## Methodology

The paper proceeds in three phases:
1. Define a set of principles/criteria organized into categories (Sections 3-4)
2. Review argumentation semantics including grounded, complete, preferred, stable, ideal, semi-stable, CF2, and prudent (Section 5)
3. Systematically evaluate each semantics against each criterion (Section 6)

## Formal Framework

### Basic Definitions

**Definition 1.** An argumentation framework is a pair AF = <A, ->  where A is a set and -> is a subset of A x A (attack relation). *(p.2)*

**Definition 2.** Given AF = <A, ->  an argument a in A, a_par(a) = {b : (b,a) in ->} and a+_par(a) = {b : (b,a) in -> or (a,b) in ->}. If a_par(a) = empty, a is an initial argument. *(p.2)*

**Definition 3.** E is an extension of AF if E is a subset of A. *(p.2)*

**Definition 4.** The restriction of AF to S (subset of A) is AF|_S = <S, -> intersect (S x S)>. *(p.2)*

### Admissibility and Related Notions

- **Conflict-free:** no pair of arguments in S attack each other *(p.2)*
- **Acceptable (defended):** argument a is acceptable w.r.t. S if for every b attacking a, there exists c in S attacking b *(p.2)*
- **Admissible:** conflict-free and every element is acceptable w.r.t. S *(p.2)*
- **Characteristic function F_AF(S):** the set of arguments acceptable w.r.t. S *(p.10)*

## Key Principles/Criteria

### Language Independence (Section 3.1)

**Definition 8.** Two AFs AF1 = <A1, ->1> and AF2 = <A2, ->2> are isomorphic if and only if there is a bijection mapping m: A1 -> A2 such that (a,b) in ->1 iff (m(a),m(b)) in ->2. *(p.3)*

**Definition 9.** A semantics S satisfies the language independence principle if and only if V(AF1) = {v1,...,vn} iff V(AF2) = {m(v1),...,m(vn)} for isomorphic AF1, AF2 with isomorphism m. *(p.3)*

All semantics at the abstract level of Dung's framework satisfy this. *(p.3)*

### Conflict-Free Principle (CF)

A semantics satisfies CF if all its extensions are conflict-free sets. *(p.3)*

### Basic Admissibility Properties (Section 3.2)

**I-maximality (Definition 5):** A semantics S satisfies I-maximality if for any AF, no extension is a proper subset of another. *(p.4)*

**Reinstatement (Definition 12):** If a is acceptable w.r.t. extension E, then a must be in E. *(p.4)*

**Weak reinstatement (Definition 14):** If every argument attacking a is in turn attacked by some element of E and a does not conflict with E, then a should be in E. *(p.5)*

**CF-reinstatement (Definition 17):** Combines CF with reinstatement — if a is acceptable w.r.t. E and E union {a} is conflict-free, then a is in E. *(p.5)*

### Directionality (Section 3.3)

**Definition 13.** An argument a is strongly defended by S if S includes an initial argument, or for any attacker of a there exists b in S attacking it, and b is also strongly defended by S. *(p.5)*

**Strongly connected components (SCCs):** The directionality criterion requires that the extensions of unattacked portions of the AF are not affected by adding further arguments/attacks. *(p.5)*

**Definition 19.** A semantics satisfies the directionality criterion if for any AF and a set U that is unattacked (no attacks from outside U into U), the extensions restricted to U are exactly the extensions of AF|_U. *(p.5-6)*

### Skepticism Relations (Section 4.1-4.2)

**Definition 21.** Given two sets of extensions E1 and E2 of an AF, E1 <=_S^E E2 (E1 is more skeptical than E2 with respect to extensions) if for every e2 in E2 there exists e1 in E1 such that e1 is a subset of e2, and for every e1 in E1 there exists e2 in E2 such that e1 is a subset of e2. *(p.6)*

**Definition 22.** Weak skepticism: <=_W^E is similar but E2 may contain additional extensions unrelated to E1. *(p.7)*

Relations between skepticism: <=_S^E implies <=_W^E. These are preorders (reflexive, transitive). *(p.7)*

**Proposition 24.** The skepticism relations are reflexive and transitive (preorders), but not antisymmetric. *(p.7)*

### Skepticism Adequacy (Section 4.2)

**Definition 26.** A skepticism relation between AFs: given AF = <A, ->, considers all AF' obtained by partitioning attacks of AF into confirmed and unconfirmed, yielding sub-frameworks. *(p.8)*

The idea: a more skeptical semantics should correspond to a more undecided stance. If some attacks in AF are "unconfirmed," removing those attacks should not make the framework more skeptical.

**<=_S^E-skepticism adequacy (Definition 28):** For two AFs where AF' is obtained from AF by adding attacks, S satisfies this if the extensions of AF are always at least as skeptical as those of AF'. *(p.8-9)*

**<=_W^E-skepticism adequacy:** Weaker form using weak skepticism relation. *(p.8-9)*

### Resolution Adequacy (Section 4.4)

**Definition 30.** A resolution of AF is obtained by selecting, for each argument with multiple attackers, a subset of the attacks (resolving non-determinism). The set of all resolutions: RES(AF). *(p.9)*

**Resolution adequacy (Proposition 65):** For any AF, the "union resolution" UR(AF, PR) (taking the union of preferred extensions across all resolutions) should be skepticism-comparable to the preferred extensions of AF. *(p.20)*

Preferred and stable semantics satisfy resolution adequacy. Grounded, ideal, complete, semi-stable, CF2, and prudent do NOT. *(p.20-22)*

## SCC-Recursiveness (Section 5.2)

### Definition and Schema

**Definition 36.** Path-equivalence: nodes a and b are path-equivalent in AF = <A, -> if there is a directed path from a to b and from b to a. *(p.11)*

The equivalence classes under path-equivalence are the strongly connected components (SCCs) of AF. The set of SCCs is denoted SCCS_AF. *(p.11)*

**Definition 37.** Given AF = <A, -> and S a subset of A and an SCC S* in SCCS_AF:
- D_F(AF, S, S*): the defeated part — arguments in S* attacked by S from outside S*
- U_P(AF, S, S*): the provisionally undefeated part — arguments in S* not attacked by S from outside S* *(p.11)*

**SCC-recursive semantics** operate by:
1. Computing SCCs of the AF
2. For each SCC, restricting to the undefeated part given selections in "earlier" SCCs
3. Applying a base function to each restricted SCC
4. Combining results across SCCs *(p.11-12)*

**Definition 38.** A base function BF(AF, E) must satisfy: if AF has one SCC, then BF returns E; if E is empty, returns empty. *(p.12)*

**General SCC-recursive schema:** Given a base function, an argumentation semantics S is SCC-recursive if for any AF:
- If AF has one SCC, apply BF
- Otherwise, recursively process SCCs in topological order, propagating defeated/undefeated information *(p.12)*

**Lemma 40.** For any SCC-recursive semantics, every extension prescribed by CF2 semantics is a maximal conflict-free set of AF that satisfies the base function constraint. *(p.12)*

### Instantiations

Four SCC-recursive semantics are identified *(p.12)*:
- **CF2 semantics:** base function selects maximal conflict-free sets
- **Grounded:** base function is the grounded extension
- **Preferred:** base function selects preferred extensions
- **Stable:** base function selects stable extensions (but not truly SCC-recursive in full generality)

## Semantics Reviewed (Section 5)

### Traditional Semantics

**Stable (Definition 31):** E is a stable extension iff E is conflict-free and every argument not in E is attacked by E. Denoted ST. *(p.10)*

**Complete (Definition 33):** E is a complete extension iff E is admissible and contains every argument acceptable w.r.t. E. F_AF(E) = E. *(p.10)*

**Grounded (Definitions 34, 46-47):** The least fixed point of F_AF. Unique extension. Computed as the limit of F_AF^0 = empty, F_AF^(i+1) = F_AF(F_AF^i). Denoted GR or GPE. *(p.10, 13)*

**Preferred (Definition 35):** Maximal (w.r.t. set inclusion) admissible sets = maximal complete extensions. Denoted PR. *(p.10)*

### Newer Semantics

**Semi-stable (Definition 41):** A complete extension E such that E union E+ (the set of arguments attacked by E) is maximal. Denoted SST. *(p.12)*

**Ideal (Definition 42):** The maximal (w.r.t. set inclusion) admissible set contained in every preferred extension. Unique. Denoted ID. *(p.12)*

**CF2 (SCC-recursive, Definition 38 with maximal conflict-free base function):** Uses SCC-recursion with base function = maximal conflict-free subsets. *(p.11-12)*

**Prudent (Definition 43):** Accounts for indirect attacks. An argument a indirectly attacks b if there is an odd-length path from a to b in the defeat graph. A set S is without indirect conflicts if no member indirectly attacks another member. Prudent extensions: grounded prudent (GPrE), preferred prudent (PrPR), stable prudent (PrST). *(p.12-13)*

## Key Equations

$$
F_{AF}(S) = \{a \in \mathcal{A} : a \text{ is acceptable w.r.t. } S\}
$$
Where: F_AF is the characteristic function, S is a set of arguments, a is acceptable if all its attackers are counter-attacked by S.
*(p.10)*

$$
GE(AF) = \bigcap_{i=0}^{\infty} F_{AF}^i(\emptyset)
$$
Where: GE is the grounded extension, computed as the least fixed point of the characteristic function starting from the empty set.
*(p.10)*

$$
D_F(AF, S, S^*) = \{a \in S^* : \exists b \in S \setminus S^*, (b,a) \in \rightarrow\}
$$
Where: D_F is the set of arguments in SCC S* defeated by the selection S from outside S*.
*(p.11)*

$$
U_P(AF, S, S^*) = S^* \setminus D_F(AF, S, S^*)
$$
Where: U_P is the provisionally undefeated part of SCC S* given selection S.
*(p.11)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Argumentation framework | AF = <A, -> | - | - | - | 2 | Directed graph |
| Attack relation | -> | - | - | subset of A x A | 2 | Binary |
| Characteristic function | F_AF | - | - | - | 10 | Maps sets to sets |
| Grounded extension | GE/GPE | - | - | unique | 10 | Least fixed point of F_AF |
| SCC base function | BF | - | - | - | 12 | Varies per semantics |

## Figures of Interest

- **Fig 1 (p.10):** A three-node cycle — demonstrates stable extension non-existence
- **Fig 2 (p.15):** AF example showing admissibility and reinstatement distinctions
- **Fig 3 (p.15):** Direct and indirect attacks illustration for prudent semantics
- **Fig 4 (p.17):** Stable semantics does not satisfy directionality
- **Fig 5 (p.19):** Several semantics are not skepticism adequate (counterexamples)
- **Fig 6 (p.20):** Stable prudent semantics is not skepticism adequate
- **Fig 7 (p.20):** Grounded prudent semantics is not skepticism adequate
- **Fig 8 (p.20):** Complete prudent semantics is not skepticism adequate
- **Fig 9 (p.21):** Semi-stable semantics is not <=_W^E resolution adequate
- **Fig 10 (p.22):** Several semantics are not resolution adequate
- **Fig 11 (p.22):** CF2 semantics is not resolution adequate
- **Fig 12 (p.23):** Preferred prudent and complete prudent are not resolution adequate

## Results Summary — Evaluation Tables

### Table 1: Satisfaction of adequacy criteria (p.13)

| Semantics | CF | I-max | Reinst | Weak Reinst | CF-Reinst | Admiss | Dir | SST |
|-----------|-----|-------|--------|-------------|-----------|--------|-----|-----|
| Grounded (GR) | Yes | Yes | Yes | Yes | Yes | Yes | Yes | - |
| Complete (CO) | Yes | No | Yes | Yes | Yes | Yes | Yes | - |
| Preferred (PR) | Yes | Yes | Yes | Yes | Yes | Yes | Yes | - |
| Stable (ST) | Yes | Yes | Yes | Yes | Yes | Yes | No | - |
| Semi-stable (SST) | Yes | Yes | Yes | Yes | Yes | Yes | Yes | - |
| Ideal (ID) | Yes | Yes | Yes | Yes | Yes | Yes | Yes | - |
| CF2 | Yes | Yes | No | No | Yes | No | Yes | - |
| Prudent (Pr) | Yes | Yes | Yes | Yes | Yes | Yes | No | - |

*(p.13)*

### Table 2: Skepticism adequacy (p.14)

| Semantics | <=_S^E skept. adeq. | <=_W^E skept. adeq. | <=_S^E resol. adeq. | <=_W^E resol. adeq. |
|-----------|---------------------|---------------------|---------------------|---------------------|
| Preferred | Yes | Yes | Yes | Yes |
| Stable | Yes | Yes | Yes | Yes |
| Grounded | No | No | No | No |
| Complete | No | No | No | No |
| Semi-stable | Yes | Yes | No | No |
| Ideal | Yes | Yes | No | No |
| CF2 | Yes | Yes | No | No |
| Prudent (various) | No | No | No | No |

*(p.14)*

Key findings from the evaluation:
- Preferred and stable are the only semantics satisfying ALL criteria including resolution adequacy *(p.23)*
- CF2 fails reinstatement and admissibility but satisfies directionality and skepticism adequacy *(p.13-14)*
- Stable fails directionality (because stable extensions may not exist for all AFs) *(p.17)*
- Grounded and complete fail skepticism adequacy *(p.14)*
- Ideal and semi-stable satisfy skepticism adequacy but not resolution adequacy *(p.14)*

## Limitations

- The framework only considers extension-based semantics, not labelling-based approaches *(p.1, 23)*
- Only considers Dung's abstract AFs — does not address structured argumentation *(p.23)*
- Resolution adequacy results depend on the specific form of skepticism relation used *(p.20-22)*
- The criteria are necessary conditions, not sufficient — satisfying all criteria does not uniquely determine a "best" semantics *(p.23)*
- Authors acknowledge that labelling-based formalisms deserve their own principle-based treatment *(p.23)*

## Arguments Against Prior Work

- Ad hoc, example-based comparisons of semantics are inadequate for systematic evaluation *(p.1)*
- Prior work on "reinstatement" criteria (e.g., CF semantics [2,6]) has been confused with different meanings; the paper distinguishes reinstatement from CF-reinstatement and weak reinstatement *(p.4-5)*
- Stable semantics suffers from the fundamental problem of non-existence of extensions for some AFs (e.g., odd-length cycles) *(p.10)*
- CF2's lack of reinstatement and admissibility is a significant limitation, though it handles odd cycles well *(p.13)*
- Prudent semantics fails directionality because it considers indirect attacks that cross SCC boundaries *(p.13)*

## Design Rationale

- Extension-based (set-of-sets) formalism chosen over labelling because most semantics in the literature use it *(p.2)*
- Principles organized from basic (conflict-free, language independence) to advanced (skepticism adequacy, resolution adequacy) to allow incremental comparison *(p.3)*
- SCC-recursion introduced as a unifying schema because it captures the locality intuition: what happens in one part of the AF should not depend on distant, unconnected parts *(p.11)*
- Directionality formalized via unattacked sets rather than SCCs directly, to be more general *(p.5)*
- Skepticism defined as a relation between extension sets (not just intersection of extensions) to capture both credulous and skeptical aspects *(p.6-7)*

## Testable Properties

- For any AF, grounded semantics produces exactly one extension that is a subset of every preferred extension *(p.10)*
- Stable extensions are a subset of preferred extensions (every stable extension is preferred) *(p.10)*
- For any AF with no odd cycles, stable extensions exist *(p.10)*
- CF2 produces at least one extension for every AF *(p.12)*
- The ideal extension is unique and is a subset of every preferred extension *(p.12)*
- Semi-stable extensions always exist (unlike stable) *(p.12)*
- For any SCC-recursive semantics, the directionality criterion is satisfied *(p.17)*
- Preferred semantics satisfies <=_S^E-skepticism adequacy *(p.14)*
- Grounded semantics does NOT satisfy <=_W^E-skepticism adequacy *(p.14)*
- Complete semantics does NOT satisfy I-maximality *(p.13)*
- For any AF, UR(AF, PR) <=_S^E E_PR(AF) — union resolution is more skeptical than preferred *(p.20)*

## Relevance to Project

This paper is foundational for propstore's argumentation layer. It provides the formal criteria by which to evaluate whether the chosen semantics (grounded, preferred, stable, etc.) are appropriate for a given render policy. The skepticism adequacy and resolution adequacy results directly inform which semantics to use when the goal is conservative (skeptical) vs. liberal (credulous) rendering. The SCC-recursive schema is relevant to the ATMS-like decomposition approach in propstore, where SCCs correspond to clusters of mutually-dependent claims.

## Open Questions

- [ ] How do these principles extend to weighted/probabilistic argumentation frameworks?
- [ ] Can the resolution adequacy criterion be adapted for the ATMS context-switching model?
- [ ] What is the relationship between SCC-recursiveness and the ATMS label propagation?
- [ ] How does the principle-based evaluation change when preferences (ASPIC+) are added?

## Related Work Worth Reading

- Baroni, Giacomin, Guida (2005) — SCC-recursiveness: a general scheme for argumentation semantics [4] *(p.25)*
- Caminada (2006) — Semi-stable semantics [7] *(p.25)*
- Dung (1995) — On the acceptability of arguments [10] — the foundational paper *(p.25)*
- Jakobovits, Vermeir (1999) — Robust semantics for argumentation frameworks [13] *(p.25)*
- Modgil, Caminada (2009) — Proof procedures and labelling algorithms *(mentioned p.23)*
- Baroni, Giacomin (2003) — Solving semantic problems with odd-length cycles [3] *(p.25)*

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — cited as [10]; the foundational AF paper defining grounded/preferred/stable/complete semantics that this paper systematically evaluates against formal principles
- [[Baroni_2005_SCC-recursivenessGeneralSchemaArgumentation]] — cited as [4/19]; the workshop version of the SCC-recursive schema that this paper extends with the full principle-based evaluation framework. This paper IS the full journal version of that work.
- [[Pollock_1987_DefeasibleReasoning]] — cited as [17]; Pollock's defeasible reasoning with rebutting/undercutting defeat relates to the reinstatement principles evaluated here
- [[Caminada_2006_IssueReinstatementArgumentation]] — cited as [7/9]; introduces semi-stable semantics and the labelling-based reinstatement analysis that this paper evaluates under the principle-based framework

### New Leads (Not Yet in Collection)
- Jakobovits, Vermeir (1999) — "Robust semantics for argumentation frameworks" — relevant for alternative semantics handling problematic cycles
- Coste-Marquis, Devred, Marquis (2005) — "Prudent semantics for argumentation frameworks" — relevant as cautionary example of how indirect defeats change formal properties
- Dung, Mancarella, Toni (2007) — "Computing ideal sceptical argumentation" — defines ideal semantics, relevant to conservative rendering modes

### Supersedes or Recontextualizes
- [[Baroni_2005_SCC-recursivenessGeneralSchemaArgumentation]] — this is the full journal version (AIJ 2007) of the NMR 2004 workshop paper, with complete proofs, the full principle-based evaluation framework, and comprehensive comparison across 8 semantics

### Cited By (in Collection)
- [[Baroni_2005_SCC-recursivenessGeneralSchemaArgumentation]] — lists this paper as a New Lead (the full journal version)
- [[Prakken_2012_AppreciationJohnPollock'sWork]] — references Baroni and Giacomin (2007/2009) in discussion of odd-cycle handling and Pollock's late revision of his semantics *(p.10)*

### Conceptual Links (not citation-based)
**Semantics evaluation and comparison:**
- [[Verheij_2002_ExistenceMultiplicityExtensionsDialectical]] — **Strong.** Both papers analyze fundamental properties of argumentation extensions. Verheij characterizes when extensions exist and why multiple extensions arise; Baroni provides formal criteria (I-maximality, reinstatement, directionality, skepticism adequacy) for evaluating semantics that produce those extensions. Complementary analytical frameworks.
- [[Caminada_2007_EvaluationArgumentationFormalisms]] — **Strong.** Both papers evaluate argumentation formalisms against formal criteria. Caminada's labelling-based approach provides an alternative perspective to Baroni's extension-based evaluation; together they cover both sides of the extension/labelling duality.

**Extending Dung's framework:**
- [[Amgoud_2008_BipolarityArgumentationFrameworks]] — **Moderate.** Baroni evaluates semantics for standard AFs; Amgoud extends AFs with support relations. Whether Baroni's principles (especially directionality and SCC-recursiveness) generalize to bipolar frameworks is an open question.
- [Developing the Abstract Dialectical Framework](../Polberg_2017_DevelopingAbstractDialecticalFramework/notes.md) — **Strong.** Polberg's §3.6 evaluates 16 EAFC semantics against 24 Caminada-style postulates — a direct application of the principle-based methodology Baroni & Giacomin establish here, scaled up to the EAFC setting. Polberg also generalizes Baroni's analysis to a much wider semantics catalogue: ADF semantics across the full xy-classification (cc/aa/ac/ca₁/ca₂ × adm/com/prf/gr/stb/naive/sst/stg/two- and three-valued labellings) and the EAFC Eq family. The principles Baroni identifies (I-maximality, reinstatement, directionality, skepticism adequacy) carry over and are checked across the larger semantics surface.
