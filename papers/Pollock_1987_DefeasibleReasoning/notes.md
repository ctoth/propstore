---
title: "Defeasible Reasoning"
authors: "John L. Pollock"
year: 1987
venue: "Cognitive Science"
doi_url: "https://doi.org/10.1207/s15516709cog1104_4"
pages: "481-518"
institution: "University of Arizona, Department of Philosophy"
---

# Defeasible Reasoning

## One-Sentence Summary
Develops a formal theory of defeasible (nonmonotonic) reasoning grounded in epistemology, distinguishing prima facie reasons from conclusive reasons, rebutting from undercutting defeaters, and implements these distinctions in a computer program called OSCAR that performs belief adoption, defeat, and reinstatement.

## Problem Addressed
Both epistemology and AI deal with nonmonotonic reasoning (where conclusions can be withdrawn given new information), but AI approaches are simplistic and overlook the fine structure of defeasible reasoning that epistemologists have identified. Conversely, epistemological theories are too abstract to implement. Pollock bridges this gap by constructing a theory precise enough to implement as a computer program, while being grounded in the philosophical analysis of reasons and defeaters.

## Key Contributions
- Distinguishes **prima facie reasons** (defeasible) from **conclusive reasons** (nondefeasible/deductive), and formalizes both as building blocks of arguments
- Distinguishes **rebutting defeaters** (reasons for denying the conclusion) from **undercutting defeaters** (reasons for denying the connection between reason and conclusion), arguing that undercutting defeat has been generally overlooked in AI
- Defines **warrant** as what an ideal reasoner would believe: a proposition is warranted iff supported by an ultimately undefeated argument
- Formalizes warrant via **levels of defeat and reinstatement**: level 0 arguments are all arguments; level n+1 arguments are level 0 arguments not defeated by any level n argument; ultimately undefeated arguments are those that are level n arguments for every n > m
- Introduces the **principle of collective defeat** (4.4): if a set of propositions is believed and each member has an equally good defeasible argument, but the conjunction of their premises defeats the original argument, then none of the propositions in the set is warranted on those defeasible arguments
- Identifies **self-defeating arguments** (4.5): arguments that support a defeater for one of their own defeasible steps, and argues these should be excluded from competition
- Extends the theory to **nonlinear (indirect) arguments** using conditionalization and weak conditionalization rules
- Proves **logical properties of warrant**: warranted propositions are deductively consistent (5.4), closed under deductive consequence (5.5), and satisfy a deduction theorem analogue (5.7)
- Generalizes collective defeat to **collective undercutting defeat** (5.8) and proves the **principle of joint defeat** (5.9, 5.10)
- Distinguishes warrant (ideal reasoner) from **justified belief** (real reasoner with finite memory), formulating rules for belief formation that appeal to local context rather than global argument structure
- Identifies three categories of belief-formation rules: **adoption rules**, **defeat rules**, and **reinstatement rules**
- Implements the theory in **OSCAR**, a computer program for defeasible reasoning, with concrete rules for adoption (ADOPT-ON, ADOPT-CON), retraction (UNDERCUT, REBUTa/b), collective defeat (NEG-COL-DEFa/b, POS-COL-DEFa/b), backtracking (BACKTRACK), reinstatement (U-REINSTATE, R-REINSTATE/U, R-REINSTATE/R), and hereditary retraction (H-RETRACT)
- Introduces key data structures: **onset** (believed on defeasible basis), **conset** (believed on conclusive basis), **beliefs** (all believed propositions), **adoptionset** (newly adopted), **retractionset** (newly retracted), **rebut** (pairs entering collective defeat)

## Methodology
The paper proceeds in three parts: Part I establishes the philosophical foundations (human rational architecture, types of reasons, kinds of defeaters, substantive examples from perception, memory, statistical syllogism, and induction). Part II constructs the formal theory of warrant for an ideal reasoner, addressing collective defeat, self-defeating arguments, indirect arguments, and logical properties. Part III moves from warrant to justified belief, constructing concrete rules for defeasible reasoning implementable in a computer program (OSCAR), and assessing its strengths and limitations.

## Key Equations

Definition of reason:

$$
\text{Being in states } M_1, \ldots, M_n \text{ is a reason for S to believe Q iff it is logically possible for S to be justified in believing Q on the basis of being in states } M_1, \ldots, M_n
$$

Definition (2.1): general notion of a reason.

Prima facie reason:

$$
\text{P is a prima facie reason for S to believe Q iff P is a reason for S to believe Q and there is an R such that R is logically consistent with P but (P \& R) is not a reason for S to believe Q}
$$

Definition (2.2): captures defeasibility.

Rebutting defeater:

$$
\text{R is a rebutting defeater for P as a prima facie reason for Q iff R is a defeater and R is a reason for believing } \neg Q
$$

Definition (2.4).

Undercutting defeater:

$$
\text{R is an undercutting defeater for P as a prima facie reason for S to believe Q iff R is a defeater and R is a reason for denying that P wouldn't be true unless Q were true}
$$

Definition (2.5). Symbolized as P->Q (a material-like conditional).

Defeat relation between argument lines:

$$
\langle \eta, j \rangle \text{ defeats } \langle \sigma, i \rangle \text{ iff } \langle \sigma, i \rangle \text{ is obtained by rule } \mathbf{R} \text{ using } \{P_1, \ldots, P_n\} \text{ as a prima facie reason for Q, and } \eta_j \text{ is either } \neg Q \text{ or } \neg[(P_1 \& \ldots \& P_n) \rightarrow Q]
$$

Definition (4.1) for linear arguments; generalized in (5.1) to include shared premise sets p(eta,j) = p(sigma,i).

Level n+1 argument:

$$
\sigma \text{ is a level } (n+1) \text{ argument iff } \sigma \text{ is a level 0 argument and there is no level } n \text{ argument } \eta \text{ such that for some } i \text{ and } j, \langle \eta, j \rangle \text{ defeats } \langle \sigma, i \rangle
$$

Definition (4.2).

Ultimately undefeated:

$$
\sigma \text{ is ultimately undefeated iff there is some } m \text{ such that } \sigma \text{ is a level } n \text{ argument for every } n > m
$$

Warrant:

$$
\text{P is warranted relative to an epistemic basis iff P is supported by some ultimately undefeated argument proceeding from that epistemic basis}
$$

Principle (4.3).

Self-defeating argument:

$$
\sigma \text{ is self-defeating iff } \sigma \text{ supports a defeater for one of its own defeasible steps, i.e., for some } i \text{ and } j, \langle \sigma, i \rangle \text{ defeats } \langle \sigma, j \rangle
$$

Definition (4.5).

Statistical syllogism:

$$
\text{If G is projectible with respect to F, } \text{prob}(Gx/Fx) \text{ is high, and } Fa, \text{ then this is a prima facie reason for } Ga
$$

Principle (3.10). Strength of the reason determined by how high the probability is.

Undercutting defeater for statistical syllogism:

$$
\text{If G is projectible with respect to } (F \& H), \text{ prob}(Gx/Fx \& Hx) < \text{prob}(Gx/Fx), \text{ and } Ha, \text{ then this is an undercutting defeater for (3.10)}
$$

Principle (3.11).

Logical properties of warrant (selected):

$$
\text{If } \Gamma \vdash P \text{ then } \Gamma \models_E P
$$

Principle (5.3): deductive consequences of warranted propositions are warranted.

$$
\text{If } \Gamma \text{ is deductively consistent, so is } \{P \mid \Gamma \models_E P\}
$$

Principle (5.4): the set of warranted propositions is deductively consistent.

$$
\text{If for every P in } \Gamma, A \models_E P, \text{ and } \Gamma \models_E Q, \text{ then } A \models_E Q
$$

Principle (5.6): warrant is closed under deductive consequence.

## Parameters

This paper is primarily a theoretical/philosophical work and does not contain quantitative parameters or measurements in the conventional sense. The framework is entirely qualitative.

## Implementation Details

### Data Structures
- **beliefs**: set of all believed propositions
- **onset**: set of pairs <P,X> where P is believed on basis of defeasible reason X
- **conset**: set of pairs <P,X> where P is believed on basis of conclusive reason X
- **adoptionset**: set of newly adopted beliefs (cleared each cycle)
- **retractionset**: set of newly retracted propositions
- **rebut**: set of pairs of argument endpoints entering collective rebutting defeat
- **adoptionflag**: 0/1 flag, set to 1 when any new adoption occurs
- **retractionflag**: 0/1 flag, set to 1 when any retraction occurs
- **reason schemas**: pairs <X,P> where X is a set of proposition-forms and P is a proposition-form
- **proposition-forms**: represented via whole_p and parts_p functions; assignments map variables to objects

### OSCAR Algorithm (Figure 7)
1. **Adopt input**: add new beliefs from external sources
2. **Loop 1 (Adoption module)**: repeatedly run ADOPT-ON, ADOPT-CON, NEG-COL-DEFa, NEG-COL-DEFb, POS-COL-DEF, and R-REINSTATE/U until adoptionflag = 0
3. **Run UNDERCUT and REBUT**: apply defeat rules, clear adoptionset, reset retractionflag
4. **Loop 2 (Retraction and reinstatement module)**: repeatedly run H-RETRACT, BACKTRACK, U-REINSTATE, and R-REINSTATE/R until retractionflag = 0
5. **Outer loop**: if adoptionflag = 1 or retractionset is nonempty, clear retractionset and return to Loop 1; otherwise stop

### Key Rules

**Adoption:**
- **ADOPT-ON**: For prima facie reason schema <X,q>, if you adopt X!s and don't believe ~(AX!s->q!s) and neither q!s nor ~q!s is rebutted, adopt q!s on X!s
- **ADOPT-CON**: For conclusive reason schema <X,q>, if you adopt X!s and neither q!s nor ~q!s is rebutted, adopt q!s con X!s

**Retraction by undercutting defeat:**
- **UNDERCUT**: If you adopt ~(AX!s->q!s) and believe q!s on X!s, delete <q!s,X!s> from onset, retract q!s if not believed on any other basis

**Retraction by rebutting defeat:**
- **REBUTa**: For prima facie reasons, if you believe ~q!s and adopt X!s (or it's newly adopted), find nearest defeasible ancestors of ~q!s, retract ~q!s and intermediate nondefeasible ancestors, add pairs to rebut
- **REBUTb**: Same for conclusive reasons

**Collective defeat enlargement:**
- **NEG-COL-DEFa/b**: When adopting X!s and ~q!s is rebutted, add relevant pairs to rebut for negatively-based collective defeat
- **POS-COL-DEFa/b**: When adopting X!s and q!s is rebutted, add relevant pairs for positively-based collective defeat

**Hereditary retraction:**
- **H-RETRACT**: If you believe q con X or q on X, but retract some member of X, then retract q and delete <q,X> from conset/onset

**Backtracking for conclusive reasons:**
- **BACKTRACK**: If you believe q con X but retract q, retract X

**Reinstatement:**
- **U-REINSTATE**: From undercutting defeat: if you retract ~(AX!s->q!s) and neither q!s nor ~q!s is rebutted, adopt every member of X!s
- **R-REINSTATE/U**: From rebutting defeat (during adoption): if you adopt ~(AX!s->q!s) and <q!s,X!s> is in rebut, delete from rebut and adopt every member of range of the sets
- **R-REINSTATE/R**: From rebutting defeat (during retraction): if you retract some member of X and {<q!s,X!s>} is in rebut, delete from rebut and adopt every member of range

## Figures of Interest
- **Fig 1 (page 492):** Three arguments alpha, beta, gamma showing defeat and reinstatement at different levels; gamma is ultimately undefeated
- **Fig 2 (page 494):** Lottery paradox: argument sigma supporting R extended by argument eta supporting ~R, illustrating self-defeating argument structure
- **Fig 3 (page 495):** Paradox of statistical induction with nested arguments showing how self-defeating arguments arise from statistical reasoning
- **Fig 4 (page 500):** Collective undercutting defeat example (Smith/Jones reliability)
- **Fig 5 (page 501):** Mixed rebutting/undercutting defeat reducing to collective rebutting defeat
- **Fig 6 (page 510):** Two linear argument chains leading to contradictory conclusions, entering collective rebutting defeat
- **Fig 7 (page 515):** OSCAR system architecture flowchart showing adoption module, retraction and reinstatement module, and outer control loop
- **Fig 8 (page 517):** Two long parallel argument chains requiring collective undercutting defeat detection, illustrating a case OSCAR cannot currently handle

## Results Summary
OSCAR correctly handles most cases of defeasible reasoning involving rebutting defeat, undercutting defeat, and reinstatement. It correctly resolves the lottery paradox (self-defeating arguments are excluded). However, it has known defects:
- Cannot handle conditional reasoning (no conditionalization rule implemented)
- Cannot detect collective undercutting defeat when it requires tracing back arbitrarily long chains (Figure 8)
- The self-defeating argument constraint is not implemented
- All reasons are treated as equally strong (no strength comparison)
- The system is interested in all possible conclusions, requiring careful choice of reason schemes to avoid combinatorial explosion

## Limitations
- Restricted to linear arguments (no conditionalization/indirect argument support)
- All reasons treated as equal strength (simplification 3)
- System interested in everything (may cause combinatorial explosion without interest constraints)
- Self-defeating argument check not implemented (requires expensive backtracking)
- Collective undercutting defeat not detectable without conditional reasoning
- No theory of projectibility available for constraining statistical syllogism
- The theory of warrant involves infinitely many levels of defeat/reinstatement; actual reasoners must approximate this

## Testable Properties
- Warranted propositions must be deductively consistent: if P and Q are both warranted from epistemic basis E, then P and Q must not be contradictory
- Warrant is closed under deductive consequence: if P1,...,Pn are all warranted and Q is a deductive consequence of P1,...,Pn, then Q must be warranted
- Self-defeating arguments must not contribute to warrant: if an argument's own conclusion defeats one of its own steps, the argument cannot be ultimately undefeated
- In the lottery paradox, no individual ticket-non-draw proposition should be warranted even though each has a high-probability prima facie reason
- Rebutting defeaters and undercutting defeaters must be handled differently: rebutting attacks the conclusion, undercutting attacks the reason-conclusion link
- Reinstatement must occur: if a defeater is itself defeated, the original conclusion should be restored
- Collective defeat must handle symmetrical cases: when two equally strong arguments lead to contradictory conclusions, neither should be warranted

## Relevance to Project
This paper provides the philosophical and formal foundations for defeasible reasoning that connects directly to the truth maintenance systems already in the propstore collection (Doyle 1979, de Kleer 1986). Pollock's distinction between rebutting and undercutting defeat, his formalization of warrant through levels of defeat and reinstatement, and his concrete implementation in OSCAR provide a complementary epistemological perspective to the more engineering-oriented TMS/ATMS approaches. The principle of collective defeat and the handling of self-defeating arguments are particularly relevant to the propstore's need to manage conflicting claims from different papers.

## Open Questions
- [ ] How does OSCAR's approach compare to ATMS environments for handling multiple competing hypotheses?
- [ ] Can the self-defeating argument constraint be efficiently implemented?
- [ ] How should collective undercutting defeat be detected without full conditional reasoning?
- [ ] What is the relationship between Pollock's warrant levels and de Kleer's assumption labels?
- [ ] How does the equal-strength simplification affect real-world claim adjudication?

## Related Work Worth Reading
- Pollock, J.L. (1986). *Contemporary theories of knowledge*. Totowa, NJ: Rowman and Allanheld. [Full account of the epistemological theory underlying this paper]
- Doyle, J. (1979). A truth maintenance system. *Artificial Intelligence, 12*, 231-272. [The TMS that OSCAR's approach contrasts with; already in collection]
- Reiter, R. (1980). A logic for default reasoning. *Artificial Intelligence, 13*, 81-132. [Default logic, the main AI alternative to Pollock's approach; already in collection]
- McCarthy, J. (1980). Circumscription -- a form of non-monotonic reasoning. *Artificial Intelligence, 13*, 27-39. [Another major AI nonmonotonic approach]
- Harman, G. (1986). *Change in view*. Cambridge, MA: MIT Press. [Philosophical account of belief revision that Pollock responds to]
- Pollock, J.L. (1983). Epistemology and probability. *Synthese, 55*, 231-252. [Foundation for statistical syllogism and projectibility]

## Collection Cross-References

### Already in Collection
- [[Doyle_1979_TruthMaintenanceSystem]] — cited as Doyle (1979); Pollock contrasts OSCAR's approach (storing only immediate bases, not all arguments) with Doyle's TMS (storing all arguments, creating memory burden).
- [[Reiter_1980_DefaultReasoning]] — cited as Reiter (1980); Pollock argues his epistemological approach provides richer structure than Reiter's default logic, particularly the rebutting/undercutting defeat distinction that default logic lacks.

### New Leads (Not Yet in Collection)
- Pollock, J.L. (1986) — "Contemporary theories of knowledge" — full epistemological theory underlying this paper
- Harman, G. (1986) — "Change in view" — competing philosophical account of belief revision
- McCarthy, J. (1980) — "Circumscription" — model-theoretic minimization approach to nonmonotonic reasoning

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- [[Dung_1995_AcceptabilityArguments]] — cited as [45]; Dung proves Pollock's indefeasible arguments correspond to the grounded extension of the corresponding argumentation framework (Theorem 47)

### Conceptual Links (not citation-based)
- [[Dung_1995_AcceptabilityArguments]] — **Strong.** Dung proves that Pollock's defeasible reasoning is a special case of abstract argumentation (Theorem 47). Pollock provides the epistemological content (prima facie reasons, rebutting/undercutting defeaters, warrant via defeat levels); Dung provides the abstract mathematical framework. OSCAR's adoption/retraction/reinstatement cycle is an operational procedure for computing something like the grounded extension.
- [[Reiter_1980_DefaultReasoning]] — **Strong.** Both provide formal frameworks for nonmonotonic reasoning. Reiter's defaults have prerequisite/justification/consequent; Pollock's reasons are prima facie or conclusive with rebutting or undercutting defeaters. Key difference: Pollock distinguishes rebutting defeat (attacking the conclusion) from undercutting defeat (attacking the reason-conclusion link), a distinction Reiter's defaults cannot express. Dung (1995) proves both are special cases of argumentation.
- [[deKleer_1986_AssumptionBasedTMS]] — **Moderate.** Both manage belief sets under contradictions: the ATMS tracks multiple consistent environments, while OSCAR manages a single evolving belief set with defeat and reinstatement. The ATMS's nogood management corresponds to Pollock's defeat detection, and ATMS context switching corresponds to Pollock's reinstatement.
- [[Clark_2014_Micropublications]] — **Moderate.** Clark's micropublication model is grounded in Toulmin-Verheij defeasible argumentation theory, which Pollock's work directly informs. Clark's support/challenge relations map to Pollock's prima facie reasons and defeaters. Clark's bipolar networks are practical instances of the kind of argumentation structure Pollock formalizes.
- [[Alchourron_1985_TheoryChange]] — **Moderate.** Pollock's warrant theory and AGM's belief revision both address rational belief management under contradictions, but from different traditions. Pollock's approach is constructive (build arguments, compute warrant via defeat levels); AGM's is axiomatic (specify postulates for rational contraction/revision). Both agree on minimal change and consistency preservation.
- [[Falkenhainer_1987_BeliefMaintenanceSystem]] — **Moderate.** Both address graded or defeasible support for beliefs. The BMS provides quantitative mechanisms (Dempster-Shafer intervals); Pollock provides qualitative ones (prima facie reasons with defeat levels). Pollock's undercutting defeaters are conceptually related to the BMS's evidence subtraction via inverted Dempster's rule.

---

**See also:** [[Prakken_2012_AppreciationJohnPollock'sWork]] - A 25-year retrospective survey by Prakken and Horty that contextualizes, extends, and critiques this 1987 paper's contributions, identifying limitations (unclear attack/defeat distinction, ad hoc argument strength) and connecting Pollock's ideas to modern structured argumentation (ASPIC+).
