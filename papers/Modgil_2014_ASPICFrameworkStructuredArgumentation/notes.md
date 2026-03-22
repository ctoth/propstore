---
title: "The ASPIC+ framework for structured argumentation: a tutorial"
authors: "Sanjay Modgil, Henry Prakken"
year: 2014
venue: "Argument & Computation"
doi_url: "https://doi.org/10.1080/19462166.2013.869766"
pages: "31-62"
---

# The ASPIC+ framework for structured argumentation: a tutorial

## One-Sentence Summary

Provides a complete formal specification of the ASPIC+ framework for structured argumentation, which builds structured arguments from strict/defeasible inference rules and knowledge bases, defines attack/defeat relations, and generates Dung-style abstract argumentation frameworks -- serving as a reference for implementing rule-based argumentation systems.

## Problem Addressed

Abstract argumentation frameworks (Dung 1995) treat arguments as atomic, with no internal structure. Real argumentation requires structured arguments built from premises and inference rules, with different types of attack (undermining, rebutting, undercutting). ASPIC+ bridges this gap by providing a general framework that instantiates Dung's abstract approach with structured arguments while satisfying key rationality postulates.

## Key Contributions

- Complete formal definition of ASPIC+ with "ordinary" negation (simplified from the general version)
- Three types of attack: undermining (attack on premise), rebutting (attack on conclusion), undercutting (attack on defeasible inference step)
- Preference-based defeat: attacks succeed as defeats based on argument ordering
- Rationality postulates: conditions under which ASPIC+ satisfies sub-argument closure, closure under strict rules, direct and indirect consistency
- Tutorial on instantiation choices: how to choose strict rules, defeasible rules, axioms, and preferences
- Demonstration of modeling Walton-style argument schemes within ASPIC+
- Generalization to contrariness (Section 5) extending beyond classical negation

## Methodology

The paper defines the framework bottom-up:
1. Define an argumentation system AS = (L, R, n) with a logical language, rules, and naming function
2. Define a knowledge base K partitioned into necessary (Kn) and ordinary (Kp) premises
3. Define how arguments are recursively constructed from premises and rules
4. Define three attack relations and preference-based defeat
5. Generate a Dung-style abstract argumentation framework
6. Apply Dung semantics (grounded, preferred, stable) to determine justified arguments

## Key Definitions

### Definition 3.1: Argumentation System (simplified, with ordinary negation)

An argumentation system is a triple $AS = (\mathcal{L}, \mathcal{R}, n)$ where:

- $\mathcal{L}$ is a logical language closed under ordinary negation $\neg$ (where $\neg\neg\phi = \phi$)
- $\mathcal{R} = \mathcal{R}_s \cup \mathcal{R}_d$ is a set of strict ($\mathcal{R}_s$) and defeasible ($\mathcal{R}_d$) inference rules
- $n: \mathcal{R}_d \to \mathcal{L}$ is a naming function for defeasible rules

Strict rules have the form $\phi_1, \ldots, \phi_n \to \phi$. Defeasible rules have the form $\phi_1, \ldots, \phi_n \Rightarrow \phi$.

### Definition 3.3: Knowledge Base

A knowledge base in AS is $\mathcal{K} = (\mathcal{K}_n, \mathcal{K}_p)$ where:
- $\mathcal{K}_n$ = necessary premises (axioms): cannot be attacked
- $\mathcal{K}_p$ = ordinary premises: can be attacked

### Definition 3.5-3.6: Arguments

An argument A on the basis of a knowledge base K and argumentation system (L, R, n) is:

1. $\phi$ if $\phi \in \mathcal{K}$ with: $\text{Prem}(A) = \{\phi\}$, $\text{Conc}(A) = \phi$, $\text{Sub}(A) = \{\phi\}$, $\text{DefRules}(A) = \emptyset$, $\text{TopRule}(A) = \text{undefined}$
2. $A_1, \ldots, A_n \to/\Rightarrow \psi$ if there exists a strict/defeasible rule $\text{Conc}(A_1), \ldots, \text{Conc}(A_n) \to/\Rightarrow \psi$ in $\mathcal{R}$

With functions:
- $\text{Prem}(A)$: all premises (leaves of argument tree)
- $\text{Conc}(A) = \psi$: the conclusion
- $\text{Sub}(A) = \text{Sub}(A_1) \cup \ldots \cup \text{Sub}(A_n) \cup \{A\}$: all sub-arguments
- $\text{DefRules}(A)$: all defeasible rules used
- $\text{TopRule}(A)$: the last rule applied

### Definition 3.8: Argument Properties

- **strict**: $\text{DefRules}(A) = \emptyset$ (uses only strict rules)
- **defeasible**: $\text{DefRules}(A) \neq \emptyset$
- **firm**: $\text{Prem}(A) \subseteq \mathcal{K}_n$ (all premises are necessary)
- **plausible**: $\text{Prem}(A) \cap \mathcal{K}_p \neq \emptyset$

Notation: $S \vdash \varphi$ if there exists a strict argument for $\varphi$ from premises in S; $S \mid\sim \varphi$ if there exists a defeasible argument.

### Definition 3.10: Attack (three types)

A attacks B iff A **undermines**, **rebuts**, or **undercuts** B:

1. **Undermining**: A undermines B (on $B'$) if $\text{Conc}(A) = \neg\phi$ for some $B' \in \text{Sub}(B)$ where $B' = \phi$ and $\phi \in \mathcal{K}_p$ (attack on an ordinary premise)
2. **Rebutting**: A rebuts B (on $B'$) if $\text{Conc}(A) = \neg\phi$ for some $B' \in \text{Sub}(B)$ where $B'$ has a defeasible top rule and $\text{Conc}(B') = \phi$ (attack on a defeasibly-derived conclusion)
3. **Undercutting**: A undercuts B (on $B'$) if $\text{Conc}(A) = \neg n(r)$ for some $B' \in \text{Sub}(B)$ where $B'$ has defeasible top rule $r$ (attack on the applicability of a defeasible rule)

### Definition 3.12: Defeat (preference-based)

A **successfully rebuts** B if A rebuts B on B' and $B' \not\prec A$ (B' is not strictly preferred to A).
A **successfully undermines** B if A undermines B on B' and $B' \not\prec A$.
A **defeats** B if A successfully rebuts, successfully undermines, or undercuts B.

Key insight: Undercutting attacks always succeed as defeats regardless of preferences.

### Definition 3.14: Structured Argumentation Framework

Given AT = (AS, K), a structured argumentation framework (SAF) is $(A, C, \preceq)$ where:
- $A$ = the set of all finite arguments constructable from K in AS
- $C$ = the defeat relation on A
- $\preceq$ = an ordering on A

### Definition 3.16: Corresponding Dung Framework

The corresponding abstract argumentation framework AF is $(A, \text{Def})$ where Def is the defeat relation derived from attacks and preferences.

## Argument Orderings

### Definition 3.19: Orderings on Sets (Elitist and Democratic)

Given a preorder $\leq'$ on elements:
- **Elitist**: $\Gamma \leq_E \Gamma'$ iff for every $\gamma \in \Gamma$ there exists $\gamma' \in \Gamma'$ such that $\gamma \leq' \gamma'$
- **Democratic**: $\Gamma \leq_D \Gamma'$ iff for every $\gamma \in \Gamma$ that is not in $\Gamma'$, there exists $\gamma' \in \Gamma'$ not in $\Gamma$ such that $\gamma \leq' \gamma'$

### Definition 3.21: Last Link Principle

A $\preceq$ B iff $\text{LastDefRules}(A) \leq \text{LastDefRules}(B)$ or $\text{LastDefRules}(A) \leq \text{LastDefRules}(B)$ and $\text{Prem}(A) \leq \text{Prem}(B)$

### Definition 3.23: Weakest Link Principle

A $\preceq$ B iff $\text{DefRules}(A) \leq \text{DefRules}(B)$ and $\text{Prem}(A) \leq \text{Prem}(B)$

Last-link compares only the last defeasible rules applied; weakest-link compares all defeasible rules and all ordinary premises.

## Rationality Postulates (Section 4.2)

For ASPIC+ to satisfy rationality postulates, the following conditions suffice:

1. **Sub-argument Closure**: Every argument's sub-arguments are also in the set
2. **Closure under Strict Rules**: If S can derive $\varphi$ via strict rules from conclusions of arguments in S, then $\varphi$ is a conclusion of some argument in S
3. **Direct Consistency**: The conclusions of any extension are consistent
4. **Indirect Consistency**: The closure of any extension's conclusions under strict rules is consistent

**Sufficient conditions** (Theorem, referenced from Modgil & Prakken 2013):
- The argumentation system is closed under transposition (Def 4.3)
- Axioms ($\mathcal{K}_n$) are consistent
- Preferences are "reasonable" (a well-behaved ordering)

### Definition 4.3: Closed Under Transposition

An argumentation theory AT is closed under transposition iff for every strict rule $\phi_1, \ldots, \phi_n \to \phi$ in $\mathcal{R}_s$, all transpositions $\phi_1, \ldots, \phi_{i-1}, \neg\phi, \phi_{i+1}, \ldots, \phi_n \to \neg\phi_i$ are also in $\mathcal{R}_s$.

## Section 4.3: Argument Schemes

ASPIC+ can model Walton-style argument schemes by:
1. Representing schemes as defeasible inference rules
2. Representing critical questions as potential undercutters or rebutters
3. Different types of critical questions map to different attack types

Example: Position-to-know scheme formalized with predicates like $\text{inPositionToKnow}(s, p)$, $\text{asserts}(s, p)$.

## Section 4.4: Representing facts

Two choices for representing undercutting in ASPIC+:
- **Explicit**: use the naming function $n$ to create undercutters $\neg n(d)$ for specific defeasible rules
- **Implicit**: represent undercutting via ordinary negation and additional defeasible rules

## Section 4.5: Illustrating uses of ASPIC+ with and without defeasible rules

Two approaches to classical logic integration:
1. **With defeasible rules**: Classical logic provides strict rules; domain knowledge provides defeasible rules
2. **Without defeasible rules**: All formulas are ordinary premises; all rules are strict; conflict resolution is purely through premise preferences. This corresponds to Brewka's (1989) Preferred Subtheories.

Example: Tweety/penguin problem modeled both ways.

## Section 5: Generalizing the Framework

The general ASPIC+ framework replaces ordinary negation with a **contrariness function**:

### Definition 5.1: Contrariness Function

A function from $\mathcal{L}$ to $2^{\mathcal{L}}$ such that:
- $\phi$ is a **contrary** of $\psi$ if $\phi \in \bar{\psi}$ but $\psi \notin \bar{\phi}$ (asymmetric)
- $\phi$ is a **contradictory** of $\psi$ if $\phi \in \bar{\psi}$ and $\psi \in \bar{\phi}$ (symmetric)

This generalizes beyond classical negation to allow asymmetric conflict relations.

With contrariness:
- Undermining and rebutting use contrariness instead of negation
- If $\text{Conc}(A) \in \overline{\phi}$ for a premise or conclusion $\phi$, then A attacks on that point
- One can model assumption-based argumentation (ABA) within generalized ASPIC+

### Definition 5.2: Successful Attack with Contrariness

Same structure as Definition 3.12 but:
- A successfully rebuts B on B' if $\text{Conc}(A) \in \overline{\text{Conc}(B')}$ and either $\text{Conc}(A)$ is a **contrary** of $\text{Conc}(B')$, or $B' \not\prec A$
- Contrary-based attacks always succeed (like undercutting); contradictory-based attacks are preference-dependent

## Section 6: Relationship to Other Approaches

- **Dung's framework**: ASPIC+ generates Dung-style AFs; any ASPIC+ SAF has a corresponding AF
- **ABA (Assumption-Based Argumentation)**: Can be modeled in generalized ASPIC+ using contrariness
- **Besnard and Hunter's classical-logic approach**: Uses only strict rules with deductive logic; undercutting is absent
- **Carneades**: Similar structured approach but with different proof standards; doesn't use Dung semantics
- **Pollock**: Pioneered defeasible reasoning with argument graphs; ASPIC+ makes Pollock's approach more general

## Implementation Details

### Data Structures Needed

1. **Logical Language L**: Set of well-formed formulas closed under negation (or contrariness)
2. **Rule Store**: Partitioned into strict rules (Rs) and defeasible rules (Rd)
3. **Knowledge Base K**: Partitioned into necessary premises (Kn) and ordinary premises (Kp)
4. **Naming Function n**: Maps defeasible rules to formulas in L
5. **Argument Tree**: Recursive structure with Prem, Conc, Sub, DefRules, TopRule functions
6. **Ordering**: Binary relation on arguments (last-link or weakest-link)
7. **Attack/Defeat Relations**: Computed from argument structure and ordering

### Argument Construction Algorithm

1. Start with premises from K as atomic arguments
2. For each applicable rule (strict or defeasible) whose antecedents match conclusions of existing arguments, construct a new argument
3. Repeat until no new arguments can be constructed
4. Result: set A of all finite arguments

### Attack Computation

For each pair of arguments (A, B):
1. Check if A undermines any sub-argument of B (conclusion of A negates an ordinary premise of B)
2. Check if A rebuts any sub-argument of B (conclusion of A negates a defeasibly-derived conclusion of B)
3. Check if A undercuts any sub-argument of B (conclusion of A negates the name of a defeasible rule in B)

### Defeat Computation

For each attack from A on B:
1. If undercutting: always a defeat
2. If rebutting on B': defeat iff B' is not strictly preferred to A
3. If undermining on B': defeat iff B' is not strictly preferred to A

## Figures of Interest

- **Fig 1 (page 8):** Argument tree structure showing premises at bottom, conclusion at top, with rule applications
- **Fig 2 (page 10):** Complete argument/attack diagram for running example showing arguments A1-A5, B1-B3, C1-C3, D3-D4 with attack arrows

## Results Summary

ASPIC+ satisfies all four rationality postulates (sub-argument closure, strict closure, direct consistency, indirect consistency) when:
- The argumentation system is well-defined (finite language, rules properly formed)
- Strict rules closed under transposition
- Axioms (Kn) are consistent
- The preference ordering is reasonable

## Limitations

- Framework is abstract -- does not specify which logic L to use, which rules to include, or which ordering to apply
- Generating all arguments is computationally expensive (potentially infinite set)
- The paper does not address computational complexity
- Preference orderings must be externally specified
- The simplified version with ordinary negation doesn't handle all cases (generalization to contrariness needed for some applications)

## Testable Properties

- An argument with only strict rules and necessary premises cannot be attacked
- Undercutting attacks always succeed as defeats regardless of preferences
- If the ordering is empty (no preferences), all attacks succeed as defeats
- Sub-argument closure: every sub-argument of a justified argument is also justified
- Strict closure: conclusions derivable by strict rules from justified conclusions are justified
- Direct consistency: the set of conclusions of any complete extension is consistent (under sufficient conditions)
- Indirect consistency: the closure under strict rules of any complete extension's conclusions is consistent (under sufficient conditions)
- A firm and strict argument has no attackers
- Transposition closure: if $\phi_1, \phi_2 \to \phi_3$ then $\neg\phi_3, \phi_2 \to \neg\phi_1$ and $\phi_1, \neg\phi_3 \to \neg\phi_2$

## Relevance to Project

ASPIC+ provides the formal foundation for structured argumentation that propstore could use to:
1. Model claims as premises in a knowledge base
2. Model relationships between claims as inference rules (strict or defeasible)
3. Formally define how claims conflict (attack relations)
4. Use preference orderings to resolve conflicts
5. Apply Dung semantics to determine which claims are justified

The framework's separation of strict/defeasible rules and necessary/ordinary premises maps naturally onto different levels of confidence in claims. The contrariness function (Section 5) could model asymmetric conflict relations between claims.

## Open Questions

- [ ] How to efficiently enumerate arguments in practice (the set can be infinite)
- [ ] Which preference ordering (last-link vs weakest-link) is most appropriate for claim conflict resolution
- [ ] How to map propstore's existing claim structures to ASPIC+ knowledge bases
- [ ] Whether the contrariness function adds value beyond ordinary negation for this project's use cases

## Related Work Worth Reading

- Dung, P.M. (1995). On the acceptability of arguments and its fundamental role in nonmonotonic reasoning, logic programming, and n-person games. Artificial Intelligence, 77, 321-357. [Foundational abstract argumentation]
- Modgil, S. & Prakken, H. (2013). A general account of argumentation with preferences. Artificial Intelligence, 195, 361-397. [Full version with proofs and general contrariness]
- Prakken, H. (2010). An abstract framework for argumentation with structured arguments. Argument and Computation, 1(2), 93-124. [Earlier version of ASPIC+]
- Walton, D. (2006). Fundamentals of critical argumentation. Cambridge University Press. [Source for argument schemes]
- Toni, F. (2014). A tutorial on assumption-based argumentation. Argument & Computation, 5(1), 89-117. [ABA approach, closely related]
- Caminada, M. & Amgoud, L. (2007). On the evaluation of argumentation formalisms. Artificial Intelligence, 171(5-6), 286-310. [Rationality postulates]

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — The foundational abstract argumentation framework that ASPIC+ builds upon. ASPIC+ generates Dung-style AFs and applies Dung's semantics (grounded, preferred, stable extensions) to determine justified arguments.
- [[Pollock_1987_DefeasibleReasoning]] — Cited as a pioneer of defeasible reasoning with argument graphs. ASPIC+ generalizes Pollock's approach by adding explicit preference-based defeat and a framework-level separation of strict/defeasible rules. Pollock's rebutting/undercutting defeater distinction is formalized as the three attack types in ASPIC+.
- [[Reiter_1980_DefaultReasoning]] — Default logic is discussed as a related nonmonotonic formalism. ASPIC+ can model default reasoning by treating default rules as defeasible inference rules.

### New Leads (Not Yet in Collection)
- Modgil, S. & Prakken, H. (2013) — "A general account of argumentation with preferences" — Full technical version of ASPIC+ with complete proofs and general contrariness function
- Caminada, M. & Amgoud, L. (2007) — "On the evaluation of argumentation formalisms" — Defines the rationality postulates that ASPIC+ is designed to satisfy
- Toni, F. (2014) — "A tutorial on assumption-based argumentation" — Companion tutorial on ABA, closely related framework
- Walton, D. (2006) — "Fundamentals of critical argumentation" — Source for argument schemes modeled in ASPIC+
- Prakken, H. (2010) — "An abstract framework for argumentation with structured arguments" — Earlier version of ASPIC+

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)
- [[Clark_2014_Micropublications]] — **Strong.** Clark's micropublication model uses Toulmin-Verheij defeasible argumentation with explicit support/challenge relations between claims. ASPIC+ provides the formal framework for computing which claims are justified when challenges (attacks) exist. Clark's claim-evidence networks could be formalized as ASPIC+ knowledge bases with claims as premises and evidence relationships as inference rules.
- [[deKleer_1986_AssumptionBasedTMS]] — **Moderate.** ATMS environments (consistent assumption sets) correspond structurally to conflict-free sets in Dung's framework, which ASPIC+ generates. Both systems address the problem of maintaining consistency under contradictory information, but from different traditions (AI engineering vs argumentation theory).
- [[Dixon_1993_ATMSandAGM]] — **Moderate.** Dixon bridges ATMS and AGM belief revision; ASPIC+ bridges structured and abstract argumentation. Both are bridging papers connecting different formalisms for managing beliefs under contradiction.
- [[Shapiro_1998_BeliefRevisionTMS]] — **Moderate.** Shapiro surveys TMS architectures as belief revision mechanisms; ASPIC+ provides an argumentation-theoretic alternative for the same consistency maintenance problem, with explicit preference-based conflict resolution.
- [[Walton_2015_ClassificationSystemArgumentationSchemes]] — **Strong.** Walton & Macagno's hierarchical taxonomy of argumentation schemes classifies the argument types that ASPIC+ can instantiate as defeasible inference rules. Each scheme's premise-conclusion structure maps to a defeasible rule, and each scheme's critical questions map to ASPIC+'s three attack types. The classification answers "what kinds of arguments exist" while ASPIC+ answers "how to formally construct and evaluate them."
