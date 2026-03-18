---
title: "Counterfactuals"
authors: "Matthew L. Ginsberg"
year: 1985
venue: "Proceedings of the Ninth International Joint Conference on Artificial Intelligence (IJCAI-85)"
doi_url: "https://www.ijcai.org/Proceedings/85-1/Papers/015.pdf"
pages: "80-86"
affiliation: "Logic Group, Knowledge Systems Laboratory, Stanford University"
---

# Counterfactuals

## One-Sentence Summary

Provides a formal framework for reasoning about counterfactual conditionals ("if p, then q") using three-valued truth functions with closure operations over a logical language, connecting the philosophical "possible worlds" interpretation to concrete AI implementation via context-dependent sublanguage selection.

## Problem Addressed

Counterfactual reasoning ("If the electricity hadn't failed, dinner would have been ready on time") is pervasive in commonsense reasoning, planning, goal regression, automated diagnosis, and design analysis, yet lacks a formal computational treatment that is both faithful to the philosophical literature (Lewis, Stalnaker) and practical for AI systems. The core difficulty is formalizing what "similarity" between possible worlds means and making the context-dependent nature of counterfactuals explicit.

## Key Contributions

- Formal description of counterfactuals using three-valued logic (true/false/unknown) and truth function closure, reducing the "possible worlds" interpretation to operations on truth functions over a logical language
- Clear distinction between context-dependent and context-independent features of counterfactual reasoning, encoded via the choice of sublanguage
- Proof that the construction is formally identical to Lewis's possible world interpretation of counterfactuals (Theorem 4)
- Demonstration that counterfactual reasoning subsumes the minimal fault assumption used in automated diagnosis
- Application to automated diagnosis of a full adder circuit, showing how counterfactual analysis can identify faulty components

## Methodology

### Three-Valued Truth Functions

The paper works in a three-valued logic with truth values $T = \{t, f, u\}$ where $t$ = true, $f$ = false, $u$ = unknown. A truth function is a mapping:

$$
\phi : L \to T
$$

Where $L$ is the set of sentences in the language.

A truth function $\psi$ is an **extension** of $\phi$ (written $\phi \leq \psi$) if for all $p \in L$, $\phi(p) = \psi(p)$ or $\phi(p) = u$. A **simple extension** changes only a single proposition from $u$ to $t$ or $f$.

A **complete extension** assigns only $t$ or $f$ (no $u$ values). An **interpretation** is a truth function $\phi$ such that $\phi(p) \neq u$ for all $p \in L$.

### Consistency

A truth function is **consistent** iff it has a consistent complete extension. In the predicate calculus, truth values of compound sentences are defined recursively from components; consistency requires component truth values to be $t$ or $/$ (not both leading to contradiction).

### Closure

**For a consistent truth function $\phi$, the closure of $\phi$ will be the maximally extended truth function $\psi$ such that every consistent complete extension of $\phi$ is an extension of $\psi$.** The closure is denoted $\text{cl}(\phi)$. If $\phi = \text{cl}(\phi)$, $\phi$ is called **closed**. This corresponds precisely to logical closure.

**Lemma 1.** No extension of an inconsistent truth function is consistent.

**Lemma 2.** $\text{cl}(\phi) \leq \phi$.

**Lemma 3.** A consistent truth function $\phi$ is reduced if and only if it is closed.

A truth function $\phi$ is **reduced** if all of its simple extensions are consistent. Equivalently, a truth function is reduced iff replacing any $\phi(p) = u$ with $t$ (or $f$) yields a consistent truth function.

### Counterfactual Construction

Given a closed truth function $\phi$ defined on $L - \{/\}$ (the language minus some proposition), and a counterfactual premise $p$:

1. Define a new truth function $\phi|_p$ corresponding to $\phi$ **with the truth value at $p$ replaced by $t$**
2. Define $\phi|_p(q) = \text{cl}(\theta)(q)$ where $\theta$ is the truth function obtained by this replacement
3. The counterfactual "$p > q$" holds iff $\phi|_p(q) = t$

The key insight: simply changing $\phi(p)$ to $t$ may produce an **inconsistent** truth function. The procedure therefore:
- Starts with $\phi$ and replaces $\phi(p)$ with $u$ (not $t$)
- Takes the closure $\phi'$ of this modified function
- Then constructs an intermediate truth function $\phi''$ where $\phi''(p) = t$ and for all other propositions, $\phi''(p) = u$ initially
- Finds minimal elements $\phi''$ in the partial order of reduced truth functions that are extensions of $\phi'$ with $\phi(p) = t$

### Similarity and Context Dependence

There are two sources of similarity between possible worlds:

1. **Number of propositions** whose truth values change (fewer changes = more similar)
2. **Relative importance** of propositions -- syntactic in nature; if a truth value changes unnecessarily, the world incorporating the change is "more distant"

The context dependence is encoded by choosing a **sublanguage** $V \subset L$. Given $V$ and a closed truth function $\phi$ on $L - V$:
- Define $\psi'$ on $V$ to be consistent iff the truth function agreeing with $\phi$ outside $V$ and with $\psi'$ on $V$ is consistent
- The **counterfactual worlds** are those where $\phi(p) = t$ and the values outside $V$ are fixed by $\phi$

**Theorem 4.** With the above definition, the construction is formally identical to Lewis's possible world interpretation of counterfactuals.

### Connection to Automated Diagnosis

The counterfactual framework subsumes the minimal fault assumption: device assumptions (that components are functioning correctly) can be recast as counterfactual assumptions. When observations contradict design predictions, counterfactual reasoning identifies which component assumptions must be abandoned.

## Key Equations

$$
\phi : L \to T
$$
Where: $L$ is the language (set of sentences), $T = \{t, f, u\}$ is the set of truth values (true, false, unknown).

$$
\phi \leq \psi \iff \forall p \in L,\ \phi(p) = \psi(p) \text{ or } \phi(p) = u
$$
Extension ordering on truth functions.

$$
\text{cl}(\phi) \leq \phi
$$
Closure is always less than or equal to the original truth function (Lemma 2).

$$
\psi'(p) = \begin{cases} \psi(p), & \text{for } p \in L' \\ \phi(p), & \text{for } p \notin L' \end{cases}
$$
Construction for restricting truth function changes to sublanguage $L'$.

$$
\phi|_p(q) \doteq \text{cl}(\theta)(q)
$$
The counterfactual evaluation: the truth value of $q$ given counterfactual premise $p$.

## Parameters

This is a theoretical/formal paper with no numerical parameters.

## Implementation Details

### Data Structures
- **Truth function**: A mapping from propositions to $\{t, f, u\}$, implementable as a dictionary/hash map
- **Language $L$**: The set of well-formed sentences; in practice, a finite set of atomic propositions plus compound sentences
- **Sublanguage $V$**: A subset of $L$ encoding context-dependent information; determines which propositions may change under counterfactual reasoning

### Core Algorithm: Counterfactual Evaluation

Given truth function $\phi$, premise $p$, and query $q$:

1. Set $\phi(p) \leftarrow u$ (make premise unknown)
2. Compute closure $\phi' = \text{cl}(\phi)$ (propagate logical consequences)
3. Set $\phi'(p) \leftarrow t$ (assert premise true)
4. Compute closure $\phi'' = \text{cl}(\phi')$ (propagate consequences of counterfactual premise)
5. Return $\phi''(q)$ as the counterfactual truth value

### Application to Diagnosis (Section 6)

The paper demonstrates the framework on a **full adder** circuit with:
- Three inputs (X, Y, Z)
- Two outputs: S (sum) and C (carry)
- Components: two XOR gates (X1, X2), two AND gates (A1, A2), one OR gate (O1)

**Structural description** in prefix predicate calculus (17 axioms SD1-SD17):
- SD1: (XORG X1)
- SD2: (XORG X2)
- SD3: (ANDG A1)
- SD4: (ANDG A2)
- SD5: (ORG O1)
- SD6-SD17: Connection axioms specifying wiring between gates

**Observed behavior** (fault indicators):
- AC1: (VAL (IN 1 F1) ON)
- AC2: (VAL (IN 2 F1) OFF)
- AC3: (VAL (IN 3 F1) OFF)
- OB1: (VAL (OUT 1 F1) OFF)
- OB2: (VAL (OUT 2 F1) OFF)

**Diagnosis using predicate calculus**: Device assumptions SD1-SD5 are made independent of the counterfactual assumptions SD6-SD17 and AC1-AC3 (which are taken as inviolable). Analysis yields:

$$
\text{(OR (NOT (XORG X1)) (NOT (XORG X2)))}
$$

Conclusion: one of the exclusive-or gates must be faulty.

**Diagnosis using counterfactuals**: Taking device assumptions as counterfactual assumptions:

$$
\text{OB1} \wedge \text{OB2} \to \text{(AND (ANDG A1) (ANDG A2) (ORG O1))}
$$

The remaining components (A1, A2, O1) are not contributing to the fault; their continued performance is *counterfactually* implied by the observed behavior.

### Edge Cases
- If changing $\phi(p)$ to $t$ produces no inconsistency, the counterfactual is trivially evaluated by closure
- If the sublanguage $V$ is empty, no propositions can change and the counterfactual may be vacuously true or undefined
- Multiple minimal $\phi''$ may exist (the paper notes this ambiguity in choosing between them remains an open problem)

## Figures of Interest

- **Fig 1 (page 5):** Full adder circuit diagram showing three inputs (X, Y, Z), two XOR gates (X1, X2), two AND gates (A1, A2), one OR gate (O1), and two outputs (S = sum, C = carry)

## Results Summary

- The three-valued truth function framework with closure operations successfully formalizes counterfactual reasoning
- The construction is provably equivalent to Lewis's possible worlds semantics (Theorem 4)
- The approach cleanly separates context-dependent from context-independent aspects of counterfactual reasoning via sublanguage selection
- Applied to automated diagnosis, the framework naturally encodes the single fault assumption and produces correct diagnostic conclusions for a full adder circuit
- Counterfactual analysis can handle cases where the single fault assumption is violated by generating new diagnoses involving minimal sets of faulty components

## Limitations

- The choice of sublanguage $V$ (which encodes context) has no formal method for selection -- it must be chosen on a case-by-case basis
- The paper acknowledges ambiguity when multiple minimal truth functions $\phi''$ exist and provides no method for choosing between them
- The approach requires generating device assumptions to replace the structural description, which may be difficult if these assumptions are invalid
- The connection between counterfactual reasoning and causality is noted as "very loose" and not formalized
- Only demonstrated on a simple circuit (full adder); scalability to larger systems not addressed

## Testable Properties

- **Closure idempotency**: For any consistent truth function $\phi$, $\text{cl}(\text{cl}(\phi)) = \text{cl}(\phi)$
- **Extension ordering**: If $\phi \leq \psi$ then $\text{cl}(\phi) \leq \text{cl}(\psi)$
- **Consistency preservation**: If $\phi$ is consistent, then $\text{cl}(\phi)$ is consistent
- **Contraposition failure**: Given counterfactual $p > q$, it does NOT follow that $\neg q > \neg p$ (contraposition is not valid for counterfactuals)
- **Transitivity failure**: From $p > q$ and $q > r$, it does NOT follow that $p > r$ (counterfactuals are not transitive)
- **Non-monotonicity**: From $p > r$, it does NOT follow that $p \wedge q > r$ (strengthening the antecedent is invalid)
- **Reduced iff closed**: A consistent truth function is reduced if and only if it is closed (Lemma 3)

## Relevance to Project

This paper provides the theoretical foundation for counterfactual reasoning within the propstore's belief revision and truth maintenance architecture. The three-valued truth function framework with closure operations maps directly onto ATMS-style environment management: assumptions correspond to propositions that may be set to $u$ (unknown/retracted), and counterfactual evaluation corresponds to exploring alternative assumption sets. The sublanguage mechanism for encoding context dependence could inform how the propstore selects which assumptions are revisable vs. fixed when performing hypothetical reasoning. The diagnosis application demonstrates how counterfactual reasoning integrates with the kind of assumption-based problem solving already represented in the collection (de Kleer 1986).

## Open Questions

- [ ] How does the sublanguage selection mechanism map to ATMS context/environment selection?
- [ ] Can the closure operation be implemented incrementally (as the ATMS does for label maintenance)?
- [ ] How does performance scale with the size of the language $L$?
- [ ] What is the relationship between Ginsberg's counterfactual framework and de Kleer's ATMS nogood management?
- [ ] The paper mentions Ginsberg (1984) technical report as a more complete treatment -- is that worth retrieving?

## Related Work Worth Reading

- Lewis, D., *Counterfactuals*, Harvard University Press, Cambridge (1973) -- the philosophical foundation
- Stalnaker, I., "A theory of conditionals", in *Studies in Logical Theory* (1968) -- alternative possible worlds semantics
- Genescreth, M.R., "The use of design descriptions in automated diagnosis", *Artificial Intelligence* 24 (1984), 411-436 -- the diagnosis framework applied in Section 6
- Glymour, C. and Thomason, R.H., "Default reasoning and the logic of theory perturbation", *Non-monotonic Reasoning Workshop* (1984) -- non-monotonic inference connection
- Adams, E., "The logic of conditionals", *Inquiry* 8 (1965), 166-197 -- early formal treatment of conditionals

## Collection Cross-References

### Already in Collection
- (none directly cited)

### New Leads (Not Yet in Collection)
- Lewis, D. (1973) — "Counterfactuals" — the foundational philosophical work on possible worlds semantics that Ginsberg proves equivalent to his construction
- Genescreth, M.R. (1984) — "The use of design descriptions in automated diagnosis" — the diagnosis framework applied in Section 6

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)
- [[deKleer_1986_AssumptionBasedTMS]] — **Strong.** Ginsberg's counterfactual framework maps directly onto ATMS assumption management. Setting a proposition to "unknown" and recomputing closure corresponds to retracting an ATMS assumption and observing which derived beliefs change. The sublanguage mechanism for encoding context dependence parallels the ATMS's distinction between assumptions (revisable) and justifications (fixed). Ginsberg's diagnosis application (identifying faulty components by counterfactual analysis) is exactly the kind of problem the ATMS was designed to support.
- [[deKleer_1984_QualitativePhysicsConfluences]] — **Moderate.** Ginsberg's diagnosis application on a full adder circuit uses the same assumption-based reasoning pattern as de Kleer's qualitative physics: component assumptions that may be individually false, with the goal of identifying the minimal set of faulty assumptions. Different domains (digital circuits vs. physical devices) but same reasoning pattern.
- [[Reiter_1980_DefaultReasoning]] — **Moderate.** Both address reasoning under assumptions that may need revision. Reiter's defaults are assumptions held absent contrary information; Ginsberg's counterfactuals explore consequences of changing assumptions. Glymour and Thomason (1984, cited by Ginsberg) explicitly connect default reasoning to theory perturbation.
- [[McAllester_1978_ThreeValuedTMS]] — **Moderate.** Both use three-valued logic (true/false/unknown). McAllester uses it for truth maintenance with clause-based dependency tracking; Ginsberg uses it for counterfactual evaluation with closure operations. Ginsberg's closure operation over three-valued truth functions is conceptually related to McAllester's label computation.
- [[McDermott_1983_ContextsDataDependencies]] — **Moderate.** McDermott's data pool switching enables hypothetical reasoning by maintaining multiple contexts; Ginsberg formalizes the semantics of the kind of hypothetical ("what if?") reasoning that data pool switching supports.
