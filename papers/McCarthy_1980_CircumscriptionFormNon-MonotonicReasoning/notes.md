---
title: "Circumscription — A Form of Non-Monotonic Reasoning"
authors: "John McCarthy"
year: 1980
venue: "Artificial Intelligence"
doi_url: "https://doi.org/10.1016/0004-3702(80)90011-9"
pages: "27-39"
---

# Circumscription — A Form of Non-Monotonic Reasoning

## One-Sentence Summary
Introduces circumscription as a formalized rule of conjecture (not inference) for first-order logic that allows jumping to the conclusion that the entities satisfying a predicate are only those that can be shown to satisfy it from the known facts.

## Problem Addressed
The "qualification problem": representing general common sense knowledge in first-order logic requires an impractical number of qualifications on every statement. For example, stating that a boat can cross a river requires enumerating every possible preventing condition. Classical (monotonic) logic cannot support the kind of default reasoning humans use, where we assume that the only relevant entities or conditions are those we know about. *(p.27-28)*

## Key Contributions
- Formalizes circumscription as a sentence schema that can augment first-order theories to achieve non-monotonic reasoning without modifying the underlying logic *(p.27)*
- Distinguishes **predicate circumscription** (minimizing the extension of a predicate) from **domain circumscription** (minimizing the domain of discourse) *(p.28)*
- Provides a model-theoretic characterization via **minimal entailment** — truth in all minimal models with respect to a predicate *(p.35)*
- Proves that circumscriptive inference is sound with respect to minimal entailment (Theorem, p.35; Corollary: if A |-_P q then A |=_P q)
- Demonstrates application to the frame problem in blocks world via circumscription of a "prevents" predicate *(p.36-37)*
- Shows circumscription subsumes the axiom schema of mathematical induction as a special case *(p.34)*

## Methodology
Circumscription is formulated as a sentence schema added to a first-order theory A. Given a predicate P being circumscribed, the schema asserts: (1) the axioms A hold under a substituted predicate Phi, and (2) if Phi is a subset of P, then P is a subset of Phi — i.e., P is the minimal predicate satisfying A. This is non-monotonic because adding new axioms to A can enlarge P's required extension, invalidating previous circumscriptive conclusions. *(p.28-32)*

## Key Equations

### Predicate Circumscription Schema (Definition)

$$
A(\Phi) \land \forall \bar{x}.(\Phi(\bar{x}) \supset P(\bar{x})) \supset \forall \bar{x}.(P(\bar{x}) \supset \Phi(\bar{x}))
$$
Where: A is the axiom set, P is the predicate being circumscribed, Phi is an arbitrary predicate parameter (can be any predicate expression including lambda-expressions), x-bar is the tuple of variables.
*(p.32, eq. 1)*

This asserts: the only tuples satisfying P are those that must satisfy any predicate Phi that satisfies A and is contained in P.

### Joint Circumscription of Two Predicates

$$
A(\Phi, \Psi) \land \forall \bar{x}.(\Phi(\bar{x}) \supset P(\bar{x})) \land \forall \bar{y}.(\Psi(\bar{y}) \supset Q(\bar{y})) \supset \forall \bar{x}.(P(\bar{x}) \supset \Phi(\bar{x})) \land \forall \bar{y}.(Q(\bar{y}) \supset \Psi(\bar{y}))
$$
Where: P and Q are jointly circumscribed predicates, Phi and Psi are their respective predicate parameters.
*(p.32, eq. 2)*

### Domain Circumscription

$$
Axiom(\Phi) \land A^{\Phi} \supset \forall x. \Phi(x)
$$
Where: A^Phi is the relativization of A with respect to Phi (replacing each universal quantifier forall x in A by forall x.(Phi(x) => ...) and each existential quantifier exists x by exists x.(Phi(x) /\ ...)); Axiom(Phi) is the conjunction of Phi(a) for each constant a and forall x.(Phi(x) => Phi(f(x))) for each function symbol f.
*(p.34, eq. 20)*

### Natural Number Induction as Special Case

Given `isnatnum 0 /\ forall x.(isnatnum x => isnatnum succ x)` (eq. 14), circumscribing isnatnum with substitution Phi(x) = Psi(x) /\ isnatnum x yields:

$$
\Psi(0) \land \forall x.(\Psi(x) \supset \Psi(succ\ x)) \supset \forall x.(isnatnum\ x \supset \Psi(x))
$$
Which is precisely the axiom schema of mathematical induction.
*(p.34, eq. 16)*

### Frame Problem — Prevents Predicate

$$
\forall x\ y\ s.(\forall z.\ \neg prevents(z, move(x, y), s) \supset on(x, y, result(move(x, y), s)))
$$
Where: prevents(z, move(x,y), s) captures conditions z that prevent the action move(x,y) in situation s; circumscribing prevents allows concluding that actions succeed when no known preventers exist.
*(p.36, eq. 22)*

Specific preventers enumerated:
- NONBLOCK: not being a block prevents move *(p.36, eq. 23)*
- COVERED: not being clear prevents move *(p.36, eq. 24)*
- tooheavy: weight prevents move *(p.36, eq. 25)*

Circumscribing the prevents predicate yields eq. 26:

$$
\forall z.(prevents(z, move(A, C), s0) \supset \Phi(z))
$$

asserting the only things that can prevent the move are the enumerated phenomena. *(p.36)*

## Parameters

This is a foundational theoretical paper — no numerical parameters, thresholds, or empirical values.

## Implementation Details
- Circumscription is a **sentence schema**, not a rule of inference — it produces new sentences to be added to the theory *(p.32)*
- The relation A |-_P q denotes circumscriptive inference: q can be deduced from A by circumscribing P *(p.32)*
- Circumscription is **non-monotonic**: A |-_P q does NOT imply A' |-_P q for A' a superset of A *(p.29)*
- Lambda-expressions are allowed as predicate substitutions in the schema *(p.32)*
- Joint circumscription (eq. 2) allows simultaneous minimization of multiple predicates *(p.32)*
- Domain circumscription reduces to predicate circumscription by introducing a new predicate "all" and relativizing *(p.35, eq. 21)*
- The results of circumscription depend on the choice of predicates used to axiomatize the domain — different representations yield different circumscriptive conclusions *(p.38)*

## Figures of Interest
No figures in this paper.

## Results Summary
- Circumscription applied to blocks world (isblock predicate) correctly concludes that only the named objects are blocks *(p.32-33, Examples 1-2)*
- Circumscribing a disjunction shows non-monotonicity: from "isblock A or isblock B," circumscription concludes either A is the only block or B is the only block, but not both *(p.33, eq. 13)*
- Circumscription of isnatnum yields the induction schema, showing it subsumes standard mathematical induction *(p.34)*
- Application to the frame problem: circumscribing "prevents" allows a heuristic program to conjecture that an action will succeed when no known preventers exist *(p.36-37)* *(p.38)*

## Limitations
- Circumscription is not a logic — it is a rule of conjecture, and its conclusions can be wrong and must sometimes be retracted *(p.37)*
- Default case reasoning via circumscription is less general than full default reasoning — e.g., concluding "block x is not on block y" unless stated requires separate default statements for each individual block *(p.37)*
- The choice of predicates to circumscribe is domain-dependent and affects the results — there is no automatic way to determine which predicates to minimize *(p.38)*
- The paper does not develop a complete proof theory or decision procedure for circumscriptive reasoning *(p.35)*
- Irrelevant facts do no harm (they appear on the left side of implications and don't affect provability), but domain-dependent heuristics are needed to decide when to circumscribe and when to retract *(p.38)* *(p.38)*

## Arguments Against Prior Work
- Against probability-based approaches to the qualification problem: probabilities cannot handle the issue because we mentally exclude extraneous possibilities (bridges, sea monsters) before even considering their probability; the non-bridge, non-sea-monster interpretation is formed before probabilities enter *(p.31)*
- Against modifying the logic itself (modal logic approaches): better to use sentence schemata in first-order logic because modifying the logic introduces many temptations and difficulties in maintaining compatibility *(p.37, remark 1)*
- Against Hewitt's PLANNER approach [5]: while PLANNER uses schemata for similar purposes, the ideas are of a different kind from circumscription *(p.29)*

## Design Rationale
- Circumscription is formulated as a schema rather than a new logic to avoid the complications of creating and maintaining a separate non-monotonic logic *(p.37)*
- Predicate circumscription is preferred over domain circumscription because domain circumscription can be reduced to predicate circumscription, and predicate circumscription is more general *(p.34-35)*
- The schema uses second-order quantification (over predicate parameters Phi) but remains expressible as a first-order schema by allowing any predicate expression as substitution *(p.32)*
- The "prevents" predicate approach to the frame problem is preferred over axioms stating what doesn't change, because circumscription naturally handles the open-world aspect *(p.36-37)*

## Testable Properties
- Circumscribing isblock in "isblock A /\ isblock B /\ isblock C" must yield "forall x.(isblock x => x=A \/ x=B \/ x=C)" *(p.32-33)*
- Circumscribing a disjunction "isblock A \/ isblock B" must yield "forall x.(isblock x => x=A) \/ forall x.(isblock x => x=B)" — i.e., either A or B is the only block, but the result is a disjunction *(p.33)*
- Adding isblock D to a theory where circumscription concluded only A, B, C are blocks must invalidate that conclusion (non-monotonicity) *(p.29)*
- Circumscribing isnatnum with axioms "isnatnum 0 /\ forall x.(isnatnum x => isnatnum succ x)" must yield the induction schema *(p.34)*
- Soundness: if A |-_P q then A |=_P q (circumscriptive inference is sound w.r.t. minimal entailment) *(p.35)*

## Relevance to Project
McCarthy 1980 is the foundational paper for circumscription, one of the three major non-monotonic reasoning formalisms (alongside Reiter's default logic and McDermott-Doyle's non-monotonic logic). For propstore's argumentation layer:
- The qualification problem is directly analogous to the challenge of representing defeasible claims — claims hold "unless something prevents them"
- Circumscription's non-monotonicity maps to how adding new evidence can retract previously supported conclusions in argumentation
- The "prevents" predicate pattern is relevant to modeling undercutting defeat in ASPIC+
- The minimal model semantics connects to skeptical reasoning in argumentation (grounded extension = conclusions true in all minimal models)
- The distinction between rule of conjecture vs. rule of inference aligns with propstore's principle of non-commitment — circumscriptive conclusions are proposals, not source-of-truth mutations

## Open Questions
- [ ] How does circumscription relate to Reiter's default logic (ref [11], same journal issue)?
- [ ] Can the "prevents" predicate pattern be used to model undercutting defeaters in ASPIC+?
- [ ] What is the computational complexity of checking circumscriptive entailment?
- [ ] How does prioritized circumscription (later work by McCarthy 1986) handle preference orderings?

## Related Work Worth Reading
- Reiter 1980 "A logic for default reasoning" (ref [11], same journal issue — the companion NMR formalism) -> NOW IN COLLECTION: [[Reiter_1980_DefaultReasoning]]
- Davis 1980 "Notes on the mathematics of non-monotonic reasoning" (ref [3], same journal issue — formal analysis)
- McCarthy 1977 "Epistemological problems of artificial intelligence" (ref [8] — earlier formulation of the qualification problem)
- McCarthy 1979 "First order theories of individual concepts and propositions" (ref [10] — related logical foundations)

## Collection Cross-References

### Already in Collection
- [[Reiter_1980_DefaultReasoning]] — cited as ref [11]; published in the same special issue of Artificial Intelligence. Reiter's default logic is the companion NMR formalism to circumscription. Reiter notes the relationship is unresolved: for the closed-world case minimal models coincide with extension-induced models, but the general case is open.

### New Leads (Not Yet in Collection)
- Davis, M. (1980) — "Notes on the mathematics of non-monotonic reasoning" — formal mathematical foundations, same journal issue
- McDermott, D. and Doyle, J. (1980) — "Non-monotonic Logic I" — the modal logic approach to NMR, also same issue

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- [[Reiter_1980_DefaultReasoning]] — Reiter discusses circumscription as an alternative formalization, notes potential deep relationship with default logic (Section 8)
- [[Pollock_1987_DefeasibleReasoning]] — Pollock cites McCarthy 1980 as a model-theoretic minimization approach, contrasting it with his epistemological analysis of reasons; argues his approach provides richer structure (rebutting vs. undercutting defeat distinction)

### Conceptual Links (not citation-based)
- [[Reiter_1980_DefaultReasoning]] — **Strong.** Both are foundational NMR formalisms published in the same 1980 special issue. Circumscription minimizes predicate extensions via sentence schemata; default logic provides default rules with prerequisite/justification/consequent structure. Dung (1995) later proved both are special cases of abstract argumentation. The two approaches represent the syntactic (schema) vs. proof-theoretic (default rule) divide in NMR.
- [[Pollock_1987_DefeasibleReasoning]] — **Strong.** Pollock's defeasible reasoning provides the epistemological counterpart to McCarthy's logical formalism. McCarthy's "prevents" predicate captures what Pollock formalizes as undercutting defeat — conditions that block the connection between premises and conclusion rather than denying the conclusion itself. Pollock explicitly critiques the NMR tradition (McCarthy, Reiter) for overlooking undercutting defeat.
- [[Moore_1985_SemanticalConsiderationsNonmonotonicLogic]] — **Moderate.** Moore's autoepistemic logic provides model-theoretic semantics for non-monotonic reasoning, directly relevant to circumscription's minimal model semantics. Both papers address why classical monotonic entailment is inadequate for common-sense reasoning.
- [[Brewka_1989_PreferredSubtheoriesExtendedLogical]] — **Moderate.** Brewka cites McCarthy's 1984 follow-up on circumscription. Brewka's preferred subtheories address the same problem of reasoning with incomplete/inconsistent knowledge that motivates circumscription, but via prioritized subsets of beliefs rather than predicate minimization.
- [[Dung_1995_AcceptabilityArguments]] — **Strong.** Dung proves that both Reiter's default logic (Theorem 43) and Pollock's defeasible reasoning (Theorem 47) are special cases of abstract argumentation. Since circumscription's relationship to default logic is established, Dung's framework provides argumentation-theoretic semantics for circumscriptive reasoning.
