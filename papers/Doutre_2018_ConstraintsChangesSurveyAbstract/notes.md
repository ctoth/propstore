---
title: "Constraints and changes: A survey of abstract argumentation dynamics"
authors: "Sylvie Doutre, Jean-Guy Mailly"
year: 2018
venue: "Argument & Computation"
doi_url: "https://doi.org/10.3233/AAC-180425"
---

# Constraints and changes: A survey of abstract argumentation dynamics

## One-Sentence Summary
Provides a comprehensive typology and survey of approaches for dynamically enforcing constraints on argumentation systems, classifying them by the type of constraint (structural, semantic, acceptability), the type of change (structural, semantic), and quality criteria (minimality, postulates). *(p.1)*

## Problem Addressed
When an argumentation framework evolves (new arguments appear, agents want certain arguments accepted, semantics need to change), how should the system be modified to enforce the new constraint while maintaining quality? The paper surveys and unifies disparate approaches to this dynamic enforcement problem. *(p.1-2)*

## Key Contributions
- A unified three-component model of argumentation systems: (1) argumentation framework, (2) evaluation semantics, (3) evaluation result *(p.2)*
- A typology of constraints that can be imposed: structural, semantic, and acceptability constraints *(p.13-16)*
- A typology of changes that can be applied: structural changes (add/remove arguments/attacks) and semantic changes *(p.7-12)*
- Quality criteria for enforcement operations: structural minimality, semantic minimality, acceptability minimality, and postulate-based criteria *(p.17-18)*
- Summary tables (Tables 3-7) mapping all existing approaches against this typology *(p.20-22)*
- Identification of underexplored areas: semantic change quality, combination of constraints, dynamics in ranking-based and structured frameworks *(p.20-21)*

## Methodology
The paper builds a typology along three dimensions — constraint type, change type, quality measure — and classifies existing approaches from the literature into this grid. It covers elementary changes, extension enforcement, belief update/revision, acceptability constraints, semantic constraints, and combinations thereof.

## Key Definitions and Formalisms

### Argumentation System (three components) *(p.2)*
An argumentation system consists of:
1. An **argumentation framework** $F = (A, R)$ — a set of arguments $A$ and attack relation $R$
2. An **evaluation semantics** $\sigma$ — a formal method to evaluate arguments
3. An **argument evaluation** $\sigma(F)$ — the result computed from (1) and (2)

### Extension-based Semantics *(p.4)*

**Definition 2.** Let $F = (A, R)$ be an argumentation framework. A set of arguments $S \subseteq A$ is:
- *conflict-free* if $\forall a, b \in S$, $(a, b) \notin R$
- *admissible* if $S$ is conflict-free and $\forall a \in S$, $S$ defends $a$ against each attacker
- a *complete extension* if $S$ is admissible and contains each argument that it defends
- a *preferred extension* if $S$ is maximal (with respect to $\subseteq$) admissible set
- a *stable extension* if $S$ is conflict-free and attacks each argument in $A \setminus S$
- the *grounded extension* if $S$ is the minimal (with respect to $\subseteq$) complete extension *(p.4)*

### Credulous and Skeptical Acceptance *(p.4)*
- $\text{cred}_\sigma(F) = \bigcup_{E \in \sigma(F)} E$ — credulously accepted arguments
- $\text{skep}_\sigma(F) = \bigcap_{E \in \sigma(F)} E$ — skeptically accepted arguments *(p.4)*

### Labelling-based Semantics *(p.4-5)*

**Definition 3.** A labelling on $F$ is a mapping from $A$ to $\{in, out, und\}$. A labelling is admissible if:
- if $a$ is labelled *in* then all its attackers are labelled *out*
- if $a$ is labelled *out* then at least one of its attackers is labelled *in* *(p.4-5)*

**Definition 4.** Given extension-based semantics $\sigma$, and $E$ an extension of $F$, the labelling:
- $a \mapsto in$ if $a \in E$
- $a \mapsto out$ if $\exists b \in S$ such that $(b, a) \in R$
- $a \mapsto undec$ otherwise
is a $\sigma$-labelling. *(p.5)*

### Ranking-based Semantics *(p.5-6)*

**Definition 5.** A gradual acceptability semantics associates to an AF $F = (A, R)$ a function $\text{Deg}: A \to [0, 1]$. A ranking-based acceptability semantics associates to $F$ a preorder on $A$ (a reflexive and transitive binary relation). *(p.6)*

The **categoriser function** $\text{Cat}(a)$ is defined:
$$
\text{Cat}(a) = \begin{cases} 1 & \text{if } \text{Att}(a) = \emptyset \\ \frac{1}{1 + \sum_{b \in \text{Att}(a)} \text{Cat}(b)} & \text{otherwise} \end{cases}
$$
Where $\text{Att}(a)$ is the set of attackers of $a$. This always yields a unique result. When the graph is a tree, this produces a ranking. *(p.6)*

### Refinement and Abstraction *(p.7)*

**Definition 6.** Let $F = (A, R)$ and $F' = (A', R')$ be two argumentation frameworks:
- $F'$ is an *argument refinement* from $F$ iff $A \subseteq A'$ and $\forall a, a' \in A$, $(a,a') \in R'$ only if $(a,a') \in R$
- $F'$ is an *attack refinement* from $F$ iff $A = A'$ and $R \subseteq R'$
- $F'$ is an *argument-attack refinement* from $F$ iff $A \subseteq A'$ and $R \subseteq R'$
- Similarly for abstraction (reverse direction) *(p.7)*

### Change Operations *(p.7-8)*

**Definition 7.** The following change operations are defined:
- **Addition of an attack** $(a_1, a_2)$: $F \oplus (a_1, a_2)$ where $a_1, a_2 \in A$
- **Deletion of an attack**: $F \ominus (a_1, a_2)$
- **Addition of an argument** $a$ with attacks: $F \oplus (\{a\}, R_a^+, R_a^-)$
  - $R_a^+$: new attacks from $a$; $R_a^-$: new attacks to $a$
- **Removal of an argument** $a$: $F \ominus a$ — removes $a$ and all attacks involving $a$ *(p.8)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Arguments | A | - | - | finite set | p.3 | Nodes of the AF graph |
| Attack relation | R | - | - | $R \subseteq A \times A$ | p.3 | Directed edges |
| Semantics | $\sigma$ | - | - | {grounded, preferred, stable, complete} | p.4 | Extension-based family |
| Extension | E | - | - | $E \subseteq A$ | p.4 | Conflict-free admissible set |
| Acceptability degree | Deg | - | - | [0, 1] | p.6 | For gradual semantics |
| Categoriser value | Cat(a) | - | 1 (no attackers) | [0, 1] | p.6 | Besnard and Hunter ranking |

## Implementation Details

### Extension Enforcement *(p.9-10)*
- **Goal:** Given AF $F$ and desired extension $E$, modify $F$ minimally so $E \in \sigma(F')$ *(p.9)*
- **Baumann [12]:** Enforcement by adding a single new argument that attacks all arguments not in $E$ and is attacked by all arguments in $E$. This is a "strong enforcement" — always works for stable and preferred semantics *(p.9)*
- **Coste-Marquis et al. [31]:** Argument-fixed enforcement — only add/remove attacks, not arguments. More constrained but preserves argument set *(p.10)*
- **Wallner et al. [66]:** Complexity results — enforcement is in general NP-complete or harder *(p.10)*

### Minimal Change Principle *(p.17-18)*
- **Structural minimality:** Minimize changes to the argument graph (add/remove fewest arguments/attacks) *(p.17)*
- **Semantic minimality:** Minimize changes to extensions — the distance between old and new extension sets *(p.18)*
- **Acceptability minimality:** Minimize changes to the acceptability status of individual arguments *(p.18)*
- Multiple distance measures possible: symmetric difference, Hamming-like distances between extensions *(p.18)*

### Belief Revision Approaches *(p.11-12)*
- **Booth et al. [24]:** Map AF to propositional formula, use AGM-style revision. Acceptability constraint as propositional formula, revise the formula encoding the AF *(p.12)*
- **Coste-Marquis et al. [33,34]:** Use Dalal-style distance minimization to find closest AF satisfying new constraint *(p.12)*
- **Diller et al. [37]:** Define families of revision operators parameterized by distance measures between AFs *(p.12)*
- **Linsbichler, Woltran [56]:** Revision of extension-based semantics, focus on syntax-independence *(p.12)*
- **Baumann, Brewka [15]:** Expand AF with new arguments from belief base; defined as extended approach *(p.12)*

### Acceptability Constraints *(p.14-15)*
- Constraint that specific arguments must be accepted/rejected *(p.14)*
- Can be enforced by structural change or semantic change *(p.14)*
- For labelling-based semantics: constraint is a partial labelling that must be satisfied *(p.14-15)*
- **Doutre et al. [39,40]:** Enforce structural + acceptability constraints jointly; use integrity constraints *(p.15)*

### Semantic Constraints *(p.15-16)*
- Agent may want a different semantics to be applied *(p.15)*
- **Baumann and Brewka [14]:** Expand AF with new arguments/attacks to make desired extensions emerge under given semantics *(p.16)*
- **Doutre and Mailly [41]:** Enforce acceptability constraint by changing semantics rather than structure — when no structural change can achieve the goal, switch to a semantics where it's already satisfied *(p.16)*

### Control Argumentation Frameworks *(p.10)*
- **Dimopoulos, Mailly, Moraitis [38]:** CAFs handle uncertainty — some arguments/attacks are "uncertain" and may or may not exist. The agent can "control" certain arguments. Goal: ensure desired set is accepted regardless of uncertain elements *(p.10)*
- QBF encoding for reasoning with CAFs *(p.10)*

## Figures of Interest
- **Fig 1 (p.2):** Argumentation System — three components (AF, semantics, evaluation) with arrows
- **Fig 2 (p.4):** Example AF with 6 arguments showing attack relations
- **Fig 3 (p.6):** Example AF with gradual acceptability values on arguments
- **Fig 4 (p.7):** Ranking of arguments derived from categoriser function
- **Fig 5 (p.9):** Strong enforcement of an extension — adding new argument
- **Fig 6 (p.9):** Argument-fixed enforcement of an extension
- **Fig 7 (p.10):** Enforcement of extension with semantic change

## Results Summary
The survey identifies that most existing work focuses on structural constraints with structural changes, while semantic constraints and semantic changes are underexplored. Tables 3-7 provide a comprehensive mapping of 20+ approaches across the typology. The paper reveals that quality criteria (especially semantic minimality and postulate-based criteria) are rarely studied for enforcement operations. *(p.20-21)*

## Limitations
- Paper covers only abstract (Dung-style) argumentation — not structured frameworks like ASPIC+ *(p.21)*
- Ranking-based semantics dynamics are almost entirely unexplored at time of writing *(p.21)*
- Combination of constraints (structural + semantic + acceptability together) is underexplored *(p.17)*
- Computational complexity of many enforcement operations not fully characterized *(p.10)*

## Arguments Against Prior Work
- Classical enforcement operators (Baumann, Coste-Marquis) do not handle semantic change — they only modify structure *(p.10)*
- Approaches that do not consider semantics changes are incomplete since semantic change may be the only way to enforce some constraints *(p.15-16)*
- Pure belief revision approaches may not capture argumentation-specific properties since they work at propositional level *(p.12)*
- Most enforcement work ignores quality criteria beyond structural minimality *(p.17)*

## Design Rationale
- The three-component model (AF, semantics, evaluation) was chosen because constraints can target any component and changes can affect any component *(p.2)*
- Distinguishing structural from semantic changes is essential because they have different computational properties and different quality criteria apply *(p.7, 17)*
- The typology approach was chosen over a chronological survey to reveal gaps and connections between approaches *(p.1)*

## Testable Properties
- Adding a single argument that attacks all non-extension arguments and is attacked by all extension arguments enforces the extension under stable semantics *(p.9)*
- Refinement preserves: if $E$ is conflict-free in $F$ and $F'$ is an argument refinement of $F$, then $E$ is conflict-free in $F'$ *(p.7)*
- Extension enforcement under stable semantics is possible for any non-empty desired extension by structural change *(p.9)*
- Structural minimality and semantic minimality can conflict — minimal structural change may cause maximal semantic change *(p.18)*
- For the categoriser function, if all attackers are removed, Cat(a) = 1 (maximum acceptability) *(p.6)*

## Relevance to Project
This paper is directly relevant to propstore's argumentation layer. The typology of constraints and changes provides a framework for understanding how propstore should handle:
1. **Extension enforcement** — when render policy demands certain arguments be accepted
2. **Structural vs semantic change** — propstore can modify the AF structure or switch semantics at render time
3. **Quality criteria** — minimality principles guide how propstore should choose among possible modifications
4. **Non-commitment** — the paper's framework supports maintaining multiple possible enforcement strategies, consistent with propstore's lazy-until-render principle
5. **Control AFs** — the CAF concept maps to propstore's handling of incomplete/uncertain argumentation

## Open Questions
- [ ] How do enforcement operators compose when multiple constraints must be enforced simultaneously?
- [ ] Can the quality criteria (structural/semantic/acceptability minimality) be computed efficiently for propstore's AF sizes?
- [ ] How does the enforcement framework interact with ASPIC+ structured argumentation?
- [ ] Which distance measures between extensions are most appropriate for propstore's use case?

## Related Work Worth Reading
- Baumann 2012 [12] — extension enforcement via single-argument addition, foundational enforcement result
- Coste-Marquis et al. 2014 [33,34] — belief revision for AFs using Dalal distance, connects AGM to AFs
- Wallner et al. 2017 [66] — complexity results for enforcement, important for understanding computational limits
- Diller et al. 2018 [37] — families of revision operators, parameterized framework
- Dimopoulos, Mailly, Moraitis 2018 [38] — Control Argumentation Frameworks, handles uncertainty
- Booth et al. 2013 [24] — propositional encoding of AF belief revision
- Cayrol and Lagasquie-Schiex (multiple) — elementary changes and their effects on extensions

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — the foundational paper defining AFs, semantics, and extensions that this survey builds upon; all constraint/change operations operate over Dung's framework
- [[Caminada_2006_IssueReinstatementArgumentation]] — labelling-based semantics (in/out/undec) used as an alternative to extension-based representation throughout the survey
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] — elementary changes in bipolar AFs; Cayrol and Lagasquie-Schiex are the primary authors on structural dynamics
- [[Cayrol_2014_ChangeAbstractArgumentationFrameworks]] — directly surveys Cayrol et al.'s work on adding/removing arguments and attacks (Def 7 change operations)
- [[Baroni_2005_SCC-recursivenessGeneralSchemaArgumentation]] — SCC decomposition used in analyzing how local changes propagate through AF structure
- [[Baroni_2007_Principle-basedEvaluationExtension-basedArgumentation]] — principle-based evaluation of semantics; the survey's quality criteria (Section 5) complement Baroni's axiomatic approach
- [[Bonzon_2016_ComparativeStudyRanking-basedSemantics]] — ranking-based semantics; the survey identifies dynamics for ranking-based semantics as an open area
- [[Hunter_2017_ProbabilisticReasoningAbstractArgumentation]] — probabilistic argumentation; the survey does not cover probabilistic dynamics, a potential extension
- [[Amgoud_2008_BipolarityArgumentationFrameworks]] — bipolar frameworks; Doutre & Mailly note that dynamics in bipolar settings need further study
- [[Odekerken_2023_ArgumentationReasoningASPICIncompleteInformation]] — incomplete information in ASPIC+; closely related to the survey's discussion of enforcement under uncertainty
- [[Verheij_2002_ExistenceMultiplicityExtensionsDialectical]] — extension existence/multiplicity; relevant to understanding when enforcement is possible
- [[Coste-Marquis_2007_MergingDung'sArgumentationSystems]] — distance-based merging of Dung AFs using PAFs; this survey covers the merging approach as part of its broader dynamics typology

### New Leads (Not Yet in Collection)
- Baumann 2012 — "What does it take to enforce an argument?" — foundational enforcement result
- Coste-Marquis, Konieczny, Mailly, Marquis 2015 — "Extension enforcement in abstract argumentation as an optimization problem" — computational enforcement framework
- Wallner, Niskanen, Jarvisalo 2017 — "Complexity results and algorithms for extension enforcement" — complexity characterization
- Diller, Haret, Linsbichler, Ruemmele, Woltran 2018 — "An extension-based approach to belief revision in abstract argumentation" — revision operators
- Dimopoulos, Mailly, Moraitis 2018 — "Control Argumentation Frameworks" — enforcement under uncertainty via QBF

### Supersedes or Recontextualizes
- [[Cayrol_2014_ChangeAbstractArgumentationFrameworks]] — this survey subsumes and extends the Cayrol 2014 work on change operations, placing it in a broader typology alongside enforcement and revision approaches

### Now in Collection (previously listed as leads)
- [[Baumann_2010_ExpandingArgumentationFrameworksEnforcing]] — Defines normal/strong/weak expansion types and conservative/liberal enforcement. Proves any conflict-free set can be enforced by adding a single argument (Theorem 4). Establishes monotonicity of extension counts and justification states for weak expansions under directional semantics. The foundational paper for the enforcement operations surveyed in Section 3.

### Cited By (in Collection)
- (none found — this is a 2018 survey, and the collection does not yet contain papers that cite it)

### Conceptual Links (not citation-based)
- [[Odekerken_2023_ArgumentationReasoningASPICIncompleteInformation]] — Odekerken's stability and relevance concepts directly address a gap identified in this survey: how to reason about enforcement when the AF is incomplete. Odekerken provides the formal tools (stability, relevance) for deciding whether enforcement is robust to future information, while Doutre & Mailly provide the enforcement operations themselves.
- [[Bonzon_2016_ComparativeStudyRanking-basedSemantics]] — Doutre & Mailly explicitly identify dynamics in ranking-based semantics as an unexplored area (Section 6); Bonzon's axiomatic comparison of ranking semantics provides the formal properties that any future ranking-dynamics framework would need to preserve.
- [[Hunter_2017_ProbabilisticReasoningAbstractArgumentation]] — Hunter's epistemic probability approach and Doutre & Mailly's enforcement typology are complementary: enforcement under probabilistic uncertainty (enforcing expected acceptability rather than categorical membership) is an open problem connecting both papers.
