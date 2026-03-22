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

Provides a complete formal specification of the ASPIC+ framework for structured argumentation, which builds structured arguments from strict/defeasible inference rules and knowledge bases, defines attack/defeat relations, and generates Dung-style abstract argumentation frameworks -- serving as a reference for implementing rule-based argumentation systems. *(p.31)*

## Problem Addressed

Abstract argumentation frameworks (Dung 1995) treat arguments as atomic, with no internal structure. Real argumentation requires structured arguments built from premises and inference rules, with different types of attack (undermining, rebutting, undercutting). ASPIC+ bridges this gap by providing a general framework that instantiates Dung's abstract approach with structured arguments while satisfying key rationality postulates. *(p.31-32)*

The framework is based on two key ideas: (1) conflicts between arguments are often resolved with explicit preferences, and (2) some premises only create a presumption in favour of their conclusion -- accordingly the framework distinguishes strict from defeasible rules, and necessary from ordinary premises. *(p.31)*

## Key Contributions

- Complete formal definition of ASPIC+ with "ordinary" negation (simplified from the general version) *(p.31-32)*
- Three types of attack: undermining (attack on premise), rebutting (attack on conclusion), undercutting (attack on defeasible inference step) *(p.33, p.38)*
- Preference-based defeat: attacks succeed as defeats based on argument ordering *(p.39-40)*
- Rationality postulates: conditions under which ASPIC+ satisfies sub-argument closure, closure under strict rules, direct and indirect consistency *(p.49-50)*
- Tutorial on instantiation choices: how to choose strict rules, defeasible rules, axioms, and preferences *(p.45-48)*
- Demonstration of modeling Walton-style argument schemes within ASPIC+ *(p.50-52)*
- Generalization to contrariness (Section 5) extending beyond classical negation *(p.57-58)*

## Methodology

The paper defines the framework bottom-up: *(p.32)*
1. Define an argumentation system AS = (L, R, n) with a logical language, rules, and naming function *(p.35)*
2. Define a knowledge base K partitioned into necessary (Kn) and ordinary (Kp) premises *(p.35)*
3. Define how arguments are recursively constructed from premises and rules *(p.36-37)*
4. Define three attack relations and preference-based defeat *(p.38-40)*
5. Generate a Dung-style abstract argumentation framework *(p.40-41)*
6. Apply Dung semantics (grounded, preferred, stable) to determine justified arguments *(p.41)*

## Key Definitions

### Definition 3.1: Argumentation System (simplified, with ordinary negation)

An argumentation system is a triple $AS = (\mathcal{L}, \mathcal{R}, n)$ where: *(p.35)*

- $\mathcal{L}$ is a logical language closed under ordinary negation $\neg$ (where $\neg\neg\phi = \phi$)
- $\mathcal{R} = \mathcal{R}_s \cup \mathcal{R}_d$ is a set of strict ($\mathcal{R}_s$) and defeasible ($\mathcal{R}_d$) inference rules
- $n: \mathcal{R}_d \to \mathcal{L}$ is a naming function for defeasible rules

Strict rules have the form $\phi_1, \ldots, \phi_n \to \phi$. Defeasible rules have the form $\phi_1, \ldots, \phi_n \Rightarrow \phi$. *(p.35)*

### Definition 3.3: Knowledge Base

A knowledge base in AS is $\mathcal{K} = (\mathcal{K}_n, \mathcal{K}_p)$ where: *(p.35)*
- $\mathcal{K}_n$ = necessary premises (axioms): cannot be attacked
- $\mathcal{K}_p$ = ordinary premises: can be attacked

### Definition 3.4: Closure

The closure $\text{Cl}_{\mathcal{R}_s}(S)$ of a set $S$ under strict rules $\mathcal{R}_s$ is the smallest set containing $S$ and the conclusions of all strict rules whose antecedents are in the set. *(p.36)*

### Definition 3.5: Argumentation Theory

An argumentation theory is a pair $AT = (AS, \mathcal{K})$ where $AS$ is an argumentation system and $\mathcal{K}$ is a knowledge base in $AS$. *(p.36)*

### Definition 3.6: Arguments

An argument A on the basis of a knowledge base K and argumentation system (L, R, n) is: *(p.36)*

1. $\phi$ if $\phi \in \mathcal{K}$ with: $\text{Prem}(A) = \{\phi\}$, $\text{Conc}(A) = \phi$, $\text{Sub}(A) = \{\phi\}$, $\text{DefRules}(A) = \emptyset$, $\text{TopRule}(A) = \text{undefined}$
2. $A_1, \ldots, A_n \to/\Rightarrow \psi$ if there exists a strict/defeasible rule $\text{Conc}(A_1), \ldots, \text{Conc}(A_n) \to/\Rightarrow \psi$ in $\mathcal{R}$

With functions: *(p.36-37)*
- $\text{Prem}(A)$: all premises (leaves of argument tree)
- $\text{Conc}(A) = \psi$: the conclusion
- $\text{Sub}(A) = \text{Sub}(A_1) \cup \ldots \cup \text{Sub}(A_n) \cup \{A\}$: all sub-arguments
- $\text{DefRules}(A)$: all defeasible rules used
- $\text{TopRule}(A)$: the last rule applied

### Definition 3.8: Argument Properties

*(p.37)*

- **strict**: $\text{DefRules}(A) = \emptyset$ (uses only strict rules)
- **defeasible**: $\text{DefRules}(A) \neq \emptyset$
- **firm**: $\text{Prem}(A) \subseteq \mathcal{K}_n$ (all premises are necessary)
- **plausible**: $\text{Prem}(A) \cap \mathcal{K}_p \neq \emptyset$

Notation: $S \vdash \varphi$ if there exists a strict argument for $\varphi$ from premises in S; $S \mid\sim \varphi$ if there exists a defeasible argument. *(p.37)*

### Definition 3.10: Attack (three types)

A attacks B iff A **undermines**, **rebuts**, or **undercuts** B: *(p.38)*

1. **Undermining**: A undermines B (on $B'$) if $\text{Conc}(A) = \neg\phi$ for some $B' \in \text{Sub}(B)$ where $B' = \phi$ and $\phi \in \mathcal{K}_p$ (attack on an ordinary premise) *(p.38)*
2. **Rebutting**: A rebuts B (on $B'$) if $\text{Conc}(A) = \neg\phi$ for some $B' \in \text{Sub}(B)$ where $B'$ has a defeasible top rule and $\text{Conc}(B') = \phi$ (attack on a defeasibly-derived conclusion) *(p.38)*
3. **Undercutting**: A undercuts B (on $B'$) if $\text{Conc}(A) = \neg n(r)$ for some $B' \in \text{Sub}(B)$ where $B'$ has defeasible top rule $r$ (attack on the applicability of a defeasible rule) *(p.38)*

Note: an argument can only be attacked on sub-arguments that are ordinary premises or that have a defeasible top rule. A firm and strict argument has no attackers. *(p.38)*

### Definition 3.12: Defeat (preference-based)

*(p.40)*

A **successfully rebuts** B if A rebuts B on B' and $B' \not\prec A$ (B' is not strictly preferred to A).
A **successfully undermines** B if A undermines B on B' and $B' \not\prec A$.
A **defeats** B if A successfully rebuts, successfully undermines, or undercuts B.

Key insight: Undercutting attacks always succeed as defeats regardless of preferences. *(p.39-40)*

### Definition 3.14: Structured Argumentation Framework

Given AT = (AS, K), a structured argumentation framework (SAF) is $(A, C, \preceq)$ where: *(p.40)*
- $A$ = the set of all finite arguments constructable from K in AS
- $C$ = the defeat relation on A
- $\preceq$ = an ordering on A

### Definition 3.16: Corresponding Dung Framework

The corresponding abstract argumentation framework AF is $(A, \text{Def})$ where Def is the defeat relation derived from attacks and preferences. *(p.41)*

### Definition 3.15: Justified Arguments

A wff $\varphi \in \mathcal{L}$ is **sceptically justified** if $\varphi$ is the conclusion of a sceptically justified argument, and **credulously justified** if $\varphi$ is not sceptically justified and is the conclusion of a credulously justified argument. *(p.41)*

## Argument Orderings

### Definition 3.19: Orderings on Sets (Elitist and Democratic)

Given a preorder $\leq'$ on elements: *(p.42)*
- **Elitist**: $\Gamma \leq_E \Gamma'$ iff for every $\gamma \in \Gamma$ there exists $\gamma' \in \Gamma'$ such that $\gamma \leq' \gamma'$
- **Democratic**: $\Gamma \leq_D \Gamma'$ iff for every $\gamma \in \Gamma$ that is not in $\Gamma'$, there exists $\gamma' \in \Gamma'$ not in $\Gamma$ such that $\gamma \leq' \gamma'$

### Definition 3.21: Last Link Principle

A $\preceq$ B iff $\text{LastDefRules}(A) \leq \text{LastDefRules}(B)$ or $\text{LastDefRules}(A) \leq \text{LastDefRules}(B)$ and $\text{Prem}(A) \leq \text{Prem}(B)$ *(p.43)*

### Definition 3.23: Weakest Link Principle

A $\preceq$ B iff $\text{DefRules}(A) \leq \text{DefRules}(B)$ and $\text{Prem}(A) \leq \text{Prem}(B)$ *(p.43)*

Last-link compares only the last defeasible rules applied; weakest-link compares all defeasible rules and all ordinary premises. *(p.43-44)*

### Last-Link vs Weakest-Link Comparison

Which ordering is better is context-dependent. Last-link gives the better outcome when the conflict is between the two final rules about whether someone may be denied access to the library, since a preference between those rules is sufficient to resolve the conflict. Weakest-link ordering is more appropriate when an example can be given of exactly the same form but with the legal rules replaced by empirical generalizations. *(p.44)*

It has been argued that for reasoning with legal rules and other normative rules, the last-link ordering is appropriate, while for epistemic reasoning the weakest-link ordering seems to favour. *(p.44)*

## Section 4: Ways to Use the Framework

### 4.1: Choosing strict rules, axioms and defeasible rules

When designing your ASPIC+ system, you can specify domain-specific strict inference rules, as illustrated by the following example based on Example 4 of Caminada & Amgoud (2007) in which the strict inference rules capture definitional knowledge. *(p.45)*

**Example 4.1** (Domain-specific strict inference rules): $\mathcal{R}_s = \{s_1, s_2\}$ and $\mathcal{K}_n = \{s_1, s_2\}$ where strict rules capture that Married implies not Bachelor, and vice versa (via transposition). The argumentation theory is closed under transposition, so that strict rules cannot generate inconsistencies. *(p.45)*

### Definition 4.3: Closed Under Transposition

An argumentation theory AT is closed under transposition iff for every strict rule $\phi_1, \ldots, \phi_n \to \phi$ in $\mathcal{R}_s$, all transpositions $\phi_1, \ldots, \phi_{i-1}, \neg\phi, \phi_{i+1}, \ldots, \phi_n \to \neg\phi_i$ are also in $\mathcal{R}_s$. *(p.46)*

In general it is a good idea to ensure that your theory is closed under transposition. If a strict rule is performing inference that is deductive, then it is a perfect inference (a strict rule $\phi_1, ..., \phi_n \to \psi$ guarantees the truth of $\psi$, so rather than have $\phi_1$ and $\psi$ and deny $\phi_2$, we should have $\neg\phi_2$). *(p.46)*

### 4.2: Strict inference rules and axioms based on deductive logic

Two approaches to incorporating classical logic: *(p.46-47)*

1. **Simple way**: Take $\mathcal{R}_s = \emptyset$ and only $\mathcal{K}_n$ and $\mathcal{K}_p$ with materialized implications. Not standard but works for simple cases. *(p.46)*
2. **Sophisticated way**: Build a classical logic-based argumentation system. Given a propositional language L, for every tautology $\phi_1 \land ... \land \phi_n \to \psi$, include a strict rule. This ensures closure under strict rules satisfies closure under the consequence relation. *(p.46)*

A simple way is to use a standard propositional (or first-order) language, and if you have a classical logic with inference rules, define: $3 \to \phi \in \mathcal{R}_s$ if and only if $3 \vdash \phi$. *(p.46)*

### 4.2 continued: Satisfaction of Rationality Postulates

**Theorem** (referenced from Modgil & Prakken 2013): ASPIC+ satisfies all four rationality postulates under sufficient conditions. *(p.49)*

Required conditions: *(p.49-50)*
- The argumentation system is closed under transposition (Def 4.3)
- Axioms ($\mathcal{K}_n$) are consistent
- Preferences are "reasonable" (a well-behaved ordering)
- For complete extensions: sub-argument closure and closure under strict rules hold automatically *(p.49)*
- Direct consistency and indirect consistency require closure under transposition and consistent axioms *(p.49)*

**Example 4.4**: Shows that if an argumentation theory is NOT closed under transposition, consistency can fail. If we adopt last-link ordering and some rule is not transposed, then an argument may not have appropriate counter-arguments. *(p.49-50)*

**Example 4.5**: As described in Example 3.7, but shows that with proper transposition closure, the framework behaves correctly and consistency is maintained. *(p.50)*

### Section 4.3: Argument Schemes

ASPIC+ can model Walton-style argument schemes by: *(p.50-51)*
1. Representing schemes as defeasible inference rules *(p.50)*
2. Representing critical questions as potential undercutters or rebutters *(p.51)*
3. Different types of critical questions map to different attack types *(p.51)*

John Pollock's work first used defeasible rules as principles of cognition in argumentation. His formalized defeasible rules do not have meta-variables ranging over classes of situations. *(p.50)*

In ASPIC+, the principles of perception and memory can be written as follows: *(p.50)*
- $d_1(x, p)$: if x perceives p, then p
- $d_2(x, p)$: if x remembers p, then p

These are schemes for argument: ground instances obtained by substituting specific perceiving agents and specific perceived states of affairs. *(p.50)*

**Position-to-know scheme**: Formalized with predicates like $\text{inPositionToKnow}(s, p)$, $\text{asserts}(s, p)$. *(p.51)*

Three types of critical questions for schemes: *(p.51)*
1. Questions that challenge assumptions (presumptions) = can generate undermining attacks
2. Questions that challenge conclusion = can generate rebutting attacks
3. Questions about exceptions = can generate undercutting attacks

**Example (position-to-know)**: Detailed formalization showing witness testimony about John being in Holland Park, with the position-to-know scheme, memory scheme, and critical questions modeled as undercutters and rebutters. Knowledge base includes facts about witnesses, perceptions, assertions. Arguments constructed include the main testimony chain and counterarguments. *(p.51-53)*

### Section 4.4: Instantiation with Schemes and Toulmin

Connections to Toulmin model noted: data = premises, warrant = defeasible rule, backing = support for the rule, rebuttal = attacking argument. *(p.53)*

The paper notes that counterarguments based on critical questions of argument schemes may themselves employ argument schemes, and these themselves may be questioned, yielding a rich dialectical structure. *(p.53)*

### Section 4.5: Illustrating uses of ASPIC+ with and without defeasible rules

Two approaches to classical logic integration: *(p.54-56)*
1. **With defeasible rules**: Classical logic provides strict rules; domain knowledge provides defeasible rules *(p.54)*
2. **Without defeasible rules**: All formulas are ordinary premises; all rules are strict; conflict resolution is purely through premise preferences. This corresponds to Brewka's (1989) Preferred Subtheories. *(p.55-56)*

**Tweety example modeled both ways**: *(p.54-55)*
- With defeasible rules: "birds fly" as defeasible rule $d_1$: $\text{bird}(x) \Rightarrow \text{flies}(x)$; "penguins don't fly" as $d_2$: $\text{penguin}(x) \Rightarrow \neg\text{flies}(x)$; with $d_1 < d_2$ (penguin rule preferred). *(p.54-55)*
- Without defeasible rules: All premises in $\mathcal{K}_p$, all rules strict, conflict resolved by $\text{penguin} \to \neg\text{flies}$ being preferred over $\text{bird} \to \text{flies}$. The difference: in this approach, argument construction becomes simpler since only strict rules and ordinary premises are involved, but only undermining attacks are possible. *(p.55-56)*

Key observation: without defeasible rules, the set of constructable arguments can be very big since ALL defeasible-rule-based arguments need to be computed; with defeasible rules and the choice way, this difference is smaller. *(p.56)*

### Section 4.6: Representing facts

Two choices for whether to include defeasible rules in a logic or only strict rules. *(p.56)*

### Section 4.7: Summary

ASPIC+ allows you to make any choice of axioms, strict and defeasible rules you like. You can choose domain-specific strict and/or defeasible inference rules, and you can choose logical strict and/or defeasible inference rules, for any deductive and/or nonmonotonic logic. *(p.57)*

## Section 5: Generalizing the Framework

The general ASPIC+ framework replaces ordinary negation with a **contrariness function**: *(p.57)*

### Definition 5.1: Contrariness Function

A function from $\mathcal{L}$ to $2^{\mathcal{L}}$ such that: *(p.57)*
- every $\phi \in \mathcal{L}$ has at least one element in $\bar{\phi}$ or is contrary/contradictory of some element
- $\phi$ is a **contrary** of $\psi$ if $\phi \in \bar{\psi}$ but $\psi \notin \bar{\phi}$ (asymmetric)
- $\phi$ is a **contradictory** of $\psi$ if $\phi \in \bar{\psi}$ and $\psi \in \bar{\phi}$ (symmetric)

This generalizes beyond classical negation to allow asymmetric conflict relations. *(p.57)*

With contrariness: *(p.57-58)*
- Undermining and rebutting use contrariness instead of negation
- If $\text{Conc}(A) \in \overline{\phi}$ for a premise or conclusion $\phi$, then A attacks on that point
- One can model assumption-based argumentation (ABA) within generalized ASPIC+ *(p.58)*

### Definition 5.2: Successful Attack with Contrariness

Same structure as Definition 3.12 but: *(p.58)*
- A successfully rebuts B on B' if $\text{Conc}(A) \in \overline{\text{Conc}(B')}$ and either $\text{Conc}(A)$ is a **contrary** of $\text{Conc}(B')$, or $B' \not\prec A$
- Contrary-based attacks always succeed (like undercutting); contradictory-based attacks are preference-dependent

The extension for ABA: ABA can be reconstructed as a special case of ASPIC+, since ABA uses assumptions as premises and contrariness to model conflict. This reconstruction is formally shown in Prakken (2010), in which assumption premises were distinguished from ordinary premises, and used strict rules. *(p.58)*

### Rationality postulates with contrariness

Following from the discussion in Section 4.2, the paper shows (from Modgil & Prakken 2013) that with the additional notion of contrariness, satisfaction of the four rationality postulates not only requires that the argument theory satisfy axiom consistency, and transposition and contraposition, but also that it is well-formed in the sense that whenever $\phi$ is a contrary of $\psi$ then $\phi$ is not an axiom/premise or the consequent of a strict rule. *(p.58)*

## Section 6: Relationship to Other Approaches

*(p.59-60)*

- **Dung's framework**: ASPIC+ generates Dung-style AFs; any ASPIC+ SAF has a corresponding AF *(p.59)*
- **ABA (Assumption-Based Argumentation)**: Can be modeled in generalized ASPIC+ using contrariness. Both Dung (with his original acceptance semantics) and Bondarenko et al. (1997) pioneered abstract argumentation. *(p.59)*
- **Besnard and Hunter's classical-logic approach**: Uses only strict rules with deductive logic; no undercutting. They distinguish between "deductible" and "defeasible" argumentation but in a different way from ASPIC+. *(p.59-60)*
- **Carneades**: Similar structured approach but with different proof standards; doesn't use Dung semantics *(p.60)*
- **Pollock**: Pioneered defeasible reasoning with argument graphs; ASPIC+ makes Pollock's approach more general *(p.59)*
- **Vreeswijk (1997)**: Also presented abstract argumentation-theoretic approach, very similar to Pollock's. Uses only defeasible inference rules, no underminers and no preferences. *(p.59)*
- **Toni and Besnard and Hunter**: Two reasoning approaches discussed in the paper that are complementary to ASPIC+. *(p.59-60)*

### Implementations

Two implementations available: *(p.60)*
- **TOAST** (http://toast.arg-tech.org) by Snaith and Reed: web-based tool for generating ASPIC+ argumentation frameworks
- **Vreeswijk's EFP**: another implementation

Other works using ASPIC+: *(p.60)*
- Wu (2012) studied well-founded semantics
- Caminada, Carnoix & Dunne (2012) and van Gijzel & Prakken (2012) have reconstructed Tarksi-style logics in ASPIC+
- Snaith & Reed (2012) used ASPIC+ to give logical account of the Argument Interchange Format (AIF)
- Modgil (2009) showed ASPIC+ can be applied to legal reasoning
- Prakken (2012) used it for evidential reasoning and risk assessment

## Figures of Interest

- **Fig 1 (p.37):** Argument tree structure showing premises at bottom, conclusion at top, with rule applications. Shows argument A3 with premises p (necessary, boxed with superscript n) and p (ordinary, boxed with superscript p), strict rule s1 applied to reach conclusion r. Superscripts indicate premise type; dotted lines indicate defeasible inferences; dashed boxes indicate underminable premises and rebuttable conclusions. *(p.37)*
- **Fig 2 (p.39):** Complete argument/attack diagram for running example showing arguments A1-A3, B1-B3, C1-C3, D3-D4 with attack arrows. Shows all three types of attack in a single diagram. *(p.39)*

## Running Example (Example 3.7)

*(p.37)*

Argumentation system with $\mathcal{L}$ consisting of $p, q, r, s, t, u, v, w, x, d_1, d_2, d_3, d_4, d_5, d_6$ and their negations, with $\mathcal{R}_s = \{s_1, s_2\}$ and $\mathcal{R}_d = \{d_1, d_2, d_3, d_4, d_5, d_6\}$, where:

| Rule | Definition |
|------|-----------|
| $d_1$ | $p \Rightarrow q$ |
| $d_2$ | $s \Rightarrow t$ |
| $d_3$ | $t \Rightarrow \neg d_1$ |
| $d_4$ | $u \Rightarrow v$ |
| $d_5$ | $v, x \Rightarrow \neg t$ |
| $d_6$ | $s \Rightarrow \neg p$ |
| $s_1$ | $p, q \to r$ |
| $s_2$ | $v \to \neg s$ |

Knowledge base: $\mathcal{K}_n = \{p\}$ and $\mathcal{K}_p = \{s, u, x\}$. *(p.37)*

Arguments constructed: *(p.38-39)*
- $A_1$: p (necessary premise)
- $A_2$: $A_1 \Rightarrow q$ (using $d_1$)
- $A_3$: $A_1, A_2 \to r$ (using $s_1$)
- $B_1$: s (ordinary premise)
- $B_2$: $B_1 \Rightarrow t$ (using $d_2$)
- $B_3$: $B_1, B_2 \Rightarrow \neg d_1$ (using $d_3$)
- $C_1$: u (ordinary premise)
- $C_2$: $C_1 \Rightarrow v$ (using $d_4$)
- $C_3$: $C_2, C_1 \to \neg s$ (using $s_2$) -- Note: underminable since attacks ordinary premise s
- $D_3$: x (ordinary premise)
- $D_4$: $C_2, D_3 \to \neg t$ (using $d_5$)

Attacks in the example: *(p.38-39)*
- $B_3$ undercuts $A_2$ and $A_3$ (on $A_2$) since $\text{Conc}(B_3) = \neg d_1$
- $C_3$ undermines $B_1$, $B_2$, $B_3$ (on $B_1$) since $\text{Conc}(C_3) = \neg s$ and $s \in \mathcal{K}_p$
- $D_4$ rebuts $B_2$ and $B_3$ (on $B_2$) since $\text{Conc}(D_4) = \neg t = \neg\text{Conc}(B_2)$

## Rationality Postulates (Section 4.2)

For ASPIC+ to satisfy rationality postulates, the following conditions suffice: *(p.49)*

1. **Sub-argument Closure**: Every argument's sub-arguments are also in the set *(p.49)*
2. **Closure under Strict Rules**: If S can derive $\varphi$ via strict rules from conclusions of arguments in S, then $\varphi$ is a conclusion of some argument in S *(p.49)*
3. **Direct Consistency**: The conclusions of any extension are consistent *(p.49)*
4. **Indirect Consistency**: The closure of any extension's conclusions under strict rules is consistent *(p.49)*

**Sufficient conditions** (Theorem, referenced from Modgil & Prakken 2013): *(p.49-50)*
- The argumentation system is closed under transposition (Def 4.3)
- Axioms ($\mathcal{K}_n$) are consistent
- Preferences are "reasonable" (a well-behaved ordering)

Sub-argument closure and closure under strict rules are automatically satisfied for all complete extensions of any AF that corresponds to an ASPIC+ argumentation theory. *(p.49)*

## Implementation Details

### Data Structures Needed

1. **Logical Language L**: Set of well-formed formulas closed under negation (or contrariness) *(p.35)*
2. **Rule Store**: Partitioned into strict rules (Rs) and defeasible rules (Rd) *(p.35)*
3. **Knowledge Base K**: Partitioned into necessary premises (Kn) and ordinary premises (Kp) *(p.35)*
4. **Naming Function n**: Maps defeasible rules to formulas in L *(p.35)*
5. **Argument Tree**: Recursive structure with Prem, Conc, Sub, DefRules, TopRule functions *(p.36-37)*
6. **Ordering**: Binary relation on arguments (last-link or weakest-link) *(p.42-43)*
7. **Attack/Defeat Relations**: Computed from argument structure and ordering *(p.38-40)*

### Argument Construction Algorithm

*(p.36)*

1. Start with premises from K as atomic arguments
2. For each applicable rule (strict or defeasible) whose antecedents match conclusions of existing arguments, construct a new argument
3. Repeat until no new arguments can be constructed
4. Result: set A of all finite arguments

Note: ASPIC+ arguments are assumed to be finite (Def 3.1), and the set of well-formed formulas under application of strict inference rules is assumed to be finite for any finite set of premises (Note 2, p.61). *(p.36, p.61)*

### Attack Computation

For each pair of arguments (A, B): *(p.38)*
1. Check if A undermines any sub-argument of B (conclusion of A negates an ordinary premise of B)
2. Check if A rebuts any sub-argument of B (conclusion of A negates a defeasibly-derived conclusion of B)
3. Check if A undercuts any sub-argument of B (conclusion of A negates the name of a defeasible rule in B)

### Defeat Computation

For each attack from A on B: *(p.40)*
1. If undercutting: always a defeat
2. If rebutting on B': defeat iff B' is not strictly preferred to A
3. If undermining on B': defeat iff B' is not strictly preferred to A

## Results Summary

ASPIC+ satisfies all four rationality postulates (sub-argument closure, strict closure, direct consistency, indirect consistency) when: *(p.49-50)*
- The argumentation system is well-defined (finite language, rules properly formed)
- Strict rules closed under transposition
- Axioms (Kn) are consistent
- The preference ordering is reasonable

## Limitations

- Framework is abstract -- does not specify which logic L to use, which rules to include, or which ordering to apply *(p.57)*
- Generating all arguments is computationally expensive (potentially infinite set) *(p.61, Note 2)*
- The paper does not address computational complexity *(p.31-62, not discussed)*
- Preference orderings must be externally specified *(p.39)*
- The simplified version with ordinary negation doesn't handle all cases (generalization to contrariness needed for some applications) *(p.57)*

## Testable Properties

- An argument with only strict rules and necessary premises cannot be attacked *(p.38)*
- Undercutting attacks always succeed as defeats regardless of preferences *(p.39-40)*
- If the ordering is empty (no preferences), all attacks succeed as defeats *(p.40)*
- Sub-argument closure: every sub-argument of a justified argument is also justified *(p.49)*
- Strict closure: conclusions derivable by strict rules from justified conclusions are justified *(p.49)*
- Direct consistency: the set of conclusions of any complete extension is consistent (under sufficient conditions) *(p.49)*
- Indirect consistency: the closure under strict rules of any complete extension's conclusions is consistent (under sufficient conditions) *(p.49)*
- A firm and strict argument has no attackers *(p.38)*
- Transposition closure: if $\phi_1, \phi_2 \to \phi_3$ then $\neg\phi_3, \phi_2 \to \neg\phi_1$ and $\phi_1, \neg\phi_3 \to \neg\phi_2$ *(p.46)*
- In the generalized framework with contrariness: contrary-based attacks always succeed as defeats (like undercutting), while contradictory-based attacks are preference-dependent *(p.58)*

## Relevance to Project

ASPIC+ provides the formal foundation for structured argumentation that propstore could use to: *(p.31-32)*
1. Model claims as premises in a knowledge base
2. Model relationships between claims as inference rules (strict or defeasible)
3. Formally define how claims conflict (attack relations)
4. Use preference orderings to resolve conflicts
5. Apply Dung semantics to determine which claims are justified

The framework's separation of strict/defeasible rules and necessary/ordinary premises maps naturally onto different levels of confidence in claims. The contrariness function (Section 5) could model asymmetric conflict relations between claims. *(p.57-58)*

## Open Questions

- [ ] How to efficiently enumerate arguments in practice (the set can be infinite) *(p.61, Note 2)*
- [ ] Which preference ordering (last-link vs weakest-link) is most appropriate for claim conflict resolution *(p.44)*
- [ ] How to map propstore's existing claim structures to ASPIC+ knowledge bases
- [ ] Whether the contrariness function adds value beyond ordinary negation for this project's use cases *(p.57-58)*

## Related Work Worth Reading

- Dung, P.M. (1995). On the acceptability of arguments and its fundamental role in nonmonotonic reasoning, logic programming, and n-person games. Artificial Intelligence, 77, 321-357. [Foundational abstract argumentation] *(cited throughout)*
- Modgil, S. & Prakken, H. (2013). A general account of argumentation with preferences. Artificial Intelligence, 195, 361-397. [Full version with proofs and general contrariness] *(cited p.31, p.40, p.49)*
- Prakken, H. (2010). An abstract framework for argumentation with structured arguments. Argument and Computation, 1(2), 93-124. [Earlier version of ASPIC+] *(cited p.59)*
- Walton, D. (2006). Fundamentals of critical argumentation. Cambridge University Press. [Source for argument schemes] *(cited p.51)*
- Toni, F. (2014). A tutorial on assumption-based argumentation. Argument & Computation, 5(1), 89-117. [ABA approach, closely related] *(cited p.59)*
- Caminada, M. & Amgoud, L. (2007). On the evaluation of argumentation formalisms. Artificial Intelligence, 171(5-6), 286-310. [Rationality postulates] *(cited p.45, p.49)*

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — The foundational abstract argumentation framework that ASPIC+ builds upon. ASPIC+ generates Dung-style AFs and applies Dung's semantics (grounded, preferred, stable extensions) to determine justified arguments. *(p.34, p.41)*
- [[Pollock_1987_DefeasibleReasoning]] — Cited as a pioneer of defeasible reasoning with argument graphs. ASPIC+ generalizes Pollock's approach by adding explicit preference-based defeat and a framework-level separation of strict/defeasible rules. Pollock's rebutting/undercutting defeater distinction is formalized as the three attack types in ASPIC+. *(p.50, p.59)*
- [[Reiter_1980_DefaultReasoning]] — Default logic is discussed as a related nonmonotonic formalism. ASPIC+ can model default reasoning by treating default rules as defeasible inference rules. *(p.59)*
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — cited as "Modgil & Prakken (2013)"; the full technical version of ASPIC+ with complete proofs, general contrariness function, revised attack-based conflict-free definition, and broader instantiation results including classical logic and Brewka's preferred subtheories. This tutorial is the accessible introduction; the 2018 paper is the definitive reference. *(p.31, p.40, p.49)*

### New Leads (Not Yet in Collection)
- Caminada, M. & Amgoud, L. (2007) — "On the evaluation of argumentation formalisms" — Defines the rationality postulates that ASPIC+ is designed to satisfy *(cited p.45, p.49)*
- Toni, F. (2014) — "A tutorial on assumption-based argumentation" — Companion tutorial on ABA, closely related framework *(cited p.59)*
- Walton, D. (2006) — "Fundamentals of critical argumentation" — Source for argument schemes modeled in ASPIC+ *(cited p.51)*
- Wu (2012) — Studied well-founded semantics for ASPIC+ *(cited p.60)*
- Snaith & Reed (2012) — TOAST implementation and AIF logical account *(cited p.60)*
- Brewka, G. (1989) — "Preferred Subtheories: An Extended Logical Framework for Default Reasoning" — The approach without defeasible rules corresponds to Brewka's Preferred Subtheories *(cited p.55)*

### Now in Collection (previously listed as leads)
- [[Prakken_2010_AbstractFrameworkArgumentationStructured]] — The original ASPIC framework paper (precursor to ASPIC+). Defines arguments as inference trees from strict/defeasible rules, three attack types (undermining, rebutting, undercutting), and proves rationality postulates (closure, consistency) for well-formed theories closed under contraposition/transposition. Also proves ABA is a special case. This 2014 tutorial extends and simplifies the 2010 framework.

### Supersedes or Recontextualizes
- (none — but see [[Modgil_2018_GeneralAccountArgumentationPreferences]] which supersedes this tutorial with the full technical treatment)

### Cited By (in Collection)
- [[Walton_2015_ClassificationSystemArgumentationSchemes]] — cites ASPIC+ as the formal mechanism for instantiating argumentation schemes
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] — conceptual link; both enrich Dung's framework in complementary directions
- [[Mayer_2020_Transformer-BasedArgumentMiningHealthcare]] — conceptual link; extracted argument components map to ASPIC+ elements
- [[Prakken_2012_AppreciationJohnPollock'sWork]] — positions ASPIC+ as the modern integration of Pollock's ideas
- [[Odekerken_2023_ArgumentationReasoningASPICIncompleteInformation]] — cited as ref 21; extends the ASPIC+ framework defined in this tutorial to handle incomplete information, adding stability and relevance decision problems for justification statuses under grounded semantics

### Conceptual Links (not citation-based)
- [[Clark_2014_Micropublications]] — **Strong.** Clark's micropublication model uses Toulmin-Verheij defeasible argumentation with explicit support/challenge relations between claims. ASPIC+ provides the formal framework for computing which claims are justified when challenges (attacks) exist. Clark's claim-evidence networks could be formalized as ASPIC+ knowledge bases with claims as premises and evidence relationships as inference rules.
- [[deKleer_1986_AssumptionBasedTMS]] — **Moderate.** ATMS environments (consistent assumption sets) correspond structurally to conflict-free sets in Dung's framework, which ASPIC+ generates. Both systems address the problem of maintaining consistency under contradictory information, but from different traditions (AI engineering vs argumentation theory).
- [[Dixon_1993_ATMSandAGM]] — **Moderate.** Dixon bridges ATMS and AGM belief revision; ASPIC+ bridges structured and abstract argumentation. Both are bridging papers connecting different formalisms for managing beliefs under contradiction.
- [[Shapiro_1998_BeliefRevisionTMS]] — **Moderate.** Shapiro surveys TMS architectures as belief revision mechanisms; ASPIC+ provides an argumentation-theoretic alternative for the same consistency maintenance problem, with explicit preference-based conflict resolution.
- [[Walton_2015_ClassificationSystemArgumentationSchemes]] — **Strong.** Walton & Macagno's hierarchical taxonomy of argumentation schemes classifies the argument types that ASPIC+ can instantiate as defeasible inference rules. Each scheme's premise-conclusion structure maps to a defeasible rule, and each scheme's critical questions map to ASPIC+'s three attack types. The classification answers "what kinds of arguments exist" while ASPIC+ answers "how to formally construct and evaluate them."
