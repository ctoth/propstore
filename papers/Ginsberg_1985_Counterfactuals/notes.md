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

Provides a formal framework for reasoning about counterfactual conditionals ("if p, then q") using three-valued truth functions with closure operations over a logical language, connecting the philosophical "possible worlds" interpretation to concrete AI implementation via context-dependent sublanguage selection. *(p.80)*

## Problem Addressed

Counterfactual reasoning ("If the electricity hadn't failed, dinner would have been ready on time") is pervasive in commonsense reasoning, planning, goal regression, automated diagnosis, and design analysis, yet lacks a formal computational treatment that is both faithful to the philosophical literature (Lewis, Stalnaker) and practical for AI systems. *(p.80)* The core difficulty is formalizing what "similarity" between possible worlds means and making the context-dependent nature of counterfactuals explicit. *(p.81)*

## Key Contributions

- Formal description of counterfactuals using three-valued logic (true/false/unknown) and truth function closure, reducing the "possible worlds" interpretation to operations on truth functions over a logical language *(p.80, p.82)*
- Clear distinction between context-dependent and context-independent features of counterfactual reasoning, encoded via the choice of sublanguage *(p.81)*
- Proof that the construction is formally identical to Lewis's possible world interpretation of counterfactuals (Theorem 4) *(p.84)*
- Demonstration that counterfactual reasoning subsumes the minimal fault assumption used in automated diagnosis *(p.85-86)*
- Application to automated diagnosis of a full adder circuit, showing how counterfactual analysis can identify faulty components *(p.85-86)*

## Methodology

### Three-Valued Truth Functions

The paper works in a three-valued logic with truth values $T = \{t, f, u\}$ where $t$ = true, $f$ = false, $u$ = unknown. A truth function is a mapping: *(p.82)*

$$
\phi : L \to T
$$

Where: $L$ is the set of sentences in the language, $T = \{t, f, u\}$ is the set of truth values (true, false, unknown).
*(p.82)*

A truth function $\psi$ is an **extension** of $\phi$ (written $\phi \leq \psi$) if for all $p \in L$, $\phi(p) = \psi(p)$ or $\phi(p) = u$. Informally, $\phi(p) = u$ if we are uncertain as to the truth or falsity of $p$. *(p.82)*

A **simple extension** changes only a single proposition from $u$ to $t$ or $f$: $\psi$ is a simple extension of $\phi$ if $\phi \leq \psi$ and $\phi(p) \neq \psi(p)$ for only a single $p \in L$. *(p.82)*

A **complete extension** assigns only $t$ or $f$ (no $u$ values). An **interpretation** is a complete truth function: $\phi(p) \neq u$ for all $p \in L$. *(p.82)*

### Consistency

A truth function is **consistent** iff it has a consistent complete extension. *(p.82)* In the predicate calculus, truth values of compound sentences are defined recursively from components; the truth value of a compound sentence is defined assuming its components have truth values — if either component has value $u$, the value of the compound is $u$ unless the compound's value is forced regardless. *(p.82)*

The truth values of these compounds are $t$ or $f$ (as opposed to $u$). The consistent assignment of the truth values in all of the sentences in $L$ constitutes an interpretation. *(p.82)*

A truth function $\phi$ is **consistent** if $\phi \leq \psi$ for some interpretation $\psi$. If $\phi(p) \neq u$ for all $p \in L$, then $\phi$ is an interpretation; we call it a **complete extension** of the truth function $\phi_0$ if $\phi_0 \leq \phi$. *(p.82)*

### Closure

**For a consistent truth function $\phi$, the closure of $\phi$ will be the maximally extended truth function $\psi$ such that every consistent complete extension of $\phi$ is an extension of $\psi$.** The closure is denoted $\text{cl}(\phi)$. If $\phi = \text{cl}(\phi)$, $\phi$ is called **closed**. *(p.82)*

**Lemma 1.** No extension of an inconsistent truth function is consistent. *(p.82)*

**Lemma 2.** $\text{cl}(\phi) \leq \phi$. (The closure is always less than or equal to the original truth function.) *(p.82)*

**Lemma 3.** A consistent truth function $\phi$ is reduced if and only if it is closed. *(p.82)*

A truth function $\phi$ is **reduced** if all of its simple extensions are consistent. Equivalently, a truth function is reduced iff replacing any $\phi(p) = u$ with $t$ (or $f$) yields a consistent truth function. *(p.82)*

**Proof sketch for Lemma 3**: For any $p \in L$, if $\phi(p) \neq u$ and $\phi$ is consistent, then $\phi(p) = \text{cl}(\phi_0)(p)$ where $\phi_0$ has $\phi_0(p) = u$. Specifically $\phi$ is consistent and therefore has a consistent complete extension which will be the maximally extended truth function $\psi$ with every consistent complete extension agreeing on $p$. The closure of $\phi$ will be reduced iff $\phi(p)$, the closure of $\phi_0$, at $p$ equals $t$ or $f$. *(p.82-83)*

### Counterfactual Construction

The paper introduces the terminology in the test section allowing the definitions of truth functions, extensions, consistency, and closure to correspond to familiar logical notions — words like "consistent" correspond to consistent interpretations, and "closure" to logical closure. *(p.82)*

Given a closed truth function $\phi$ and a counterfactual premise $p$: *(p.83)*

1. Define a new truth function $\phi|_p$ corresponding to $\phi$ **with the truth value at $p$ replaced by $t$** *(p.83)*
2. Define $\phi|_p(q) = \text{cl}(\theta)(q)$ where $\theta$ is the truth function obtained by this replacement *(p.83)*
3. The counterfactual "$p > q$" holds iff $\phi|_p(q) = t$ *(p.83)*

The key insight: simply changing $\phi(p)$ to $t$ may produce an **inconsistent** truth function. *(p.83)* The procedure therefore:
- If $\phi$ is closed and has been in context and the counterfactual premise $p$ is such that $\phi(p) = f$, then setting $\phi(p) = t$ may well produce an inconsistent truth function *(p.83)*
- Since logically the resulting $\phi'|_p$ must be consistent (since $\phi$ is the truth function of the **actual** world and we want a consistent counterfactual world), the procedure resolves this by: *(p.83)*

The construction: *(p.83-84)*
- Start with the result of replacing $\phi(p)$ with $t$; if it is necessarily consistent, $\phi'$ is reduced and $\phi'(q) = \phi_p(q)$ trivially *(p.84)*
- Take the truth function consisting of the values of all the propositions which are **not directly compatible** with $\phi$ (i.e. not $\phi(p)$ replaced by $t$); call this $\phi_p$ *(p.84)*
- The closure of $\phi_p$ with $\phi(p) = t$ is $\text{cl}(\phi_p)$, the counterfactual truth function *(p.84)*

Having constructed similar worlds where $p$ might hold, it is straightforward to investigate the consequences of $p$ in each — a proposition $q$ is a counterfactual consequence of $p$ iff $\phi_p(q) = t$ for all of the possible counterfactual worlds. *(p.84)*

### Similarity and Context Dependence

There are two sources of similarity between possible worlds: *(p.81)*

1. **Number of propositions** whose truth values change (fewer changes = more similar) *(p.81)*
2. **Relative importance** of propositions -- syntactic in nature; if a truth value changes unnecessarily, the world incorporating the change is "more distant" *(p.81)*

The context dependence is encoded by choosing a **sublanguage** $V \subset L$. *(p.81, p.83)* Given $V$ and a closed truth function $\phi$ on $L - V$:
- Define $\psi'$ on $V$ to be consistent iff the truth function agreeing with $\phi$ outside $V$ and with $\psi'$ on $V$ is consistent *(p.84)*
- The **counterfactual worlds** are those where $\phi(p) = t$ and the values outside $V$ are fixed by $\phi$ *(p.84)*

**An alternative** would be to assume that the worlds where we abandon our assumptions are just as similar to ours as those in which we abandon nothing. Lewis might well make this choice; in Ginsberg's formalism, defining $\phi|_p$ so that for $s \notin V$ it takes the value independent of the choice of $\phi'$, and is otherwise equivalent. *(p.84)*

**Theorem 4.** With the above definition, the construction is formally identical to Lewis's possible world interpretation of counterfactuals. The construction is formally identical to Lewis's possible world construction if we restrict our attention to a countably infinite language. *(p.84)*

*Proof (Theorem 4)*: With the above definition, the construction is formally identical to Lewis's "possible world construction" (Lewis's spheres semantics). Lewis requires a total preorder on possible worlds centered on the actual world; Ginsberg shows this is induced by the truth function extension ordering restricted to sublanguage $V$. *(p.84)*

### Properties of Counterfactuals

The paper discusses several properties of counterfactual reasoning: *(p.81)*

- **Contraposition fails**: The power didn't fail → dinner was on time, but it does NOT follow from the electricity failing that dinner would have been late (other causes possible, such as laziness on the part of the cook). *(p.81)*
- **Transitivity fails**: Counterfactuals are not necessarily transitive. From $p > q$ and $q > r$, we cannot necessarily conclude $p > r$. Example: "If J. Edgar Hoover had been born a Russian, he would have been a Communist" and "If he had been a Communist, he would have been a traitor" — but NOT "If he had been born a Russian, he would have been a traitor." *(p.81)*
- **Strengthening the antecedent fails (non-monotonicity)**: From $p > r$, it does NOT follow that $p \wedge q > r$. It is possible to have $p \wedge q > r$ and $p \wedge q > \neg r$. Example: "The two sides would have fought on, had there been no ceasefire" but "had there been no ceasefire and had a nuclear weapon been used, [there would not have been a fight]." *(p.81)*

### Connection to Automated Diagnosis

The counterfactual framework subsumes the minimal fault assumption: device assumptions (that components are functioning correctly) can be recast as counterfactual assumptions. When observations contradict design predictions, counterfactual reasoning identifies which component assumptions must be abandoned. *(p.85-86)*

**Key insight for diagnosis**: The paper distinguishes between two approaches *(p.85)*:
1. **Predicate calculus approach**: Device assumptions SD1-SD5 are treated as axioms that can be denied, and the structural description SD6-SD17 and observations AC1-AC3 are taken as inviolable. Analysis yields which device assumptions must be false. *(p.85-86)*
2. **Counterfactual approach**: Device assumptions are replaced by device axioms that can be used counterfactually. This allows the system to deduce not only which components might be faulty but also which components are definitely *not* faulty (their correct behavior is counterfactually implied by observations). *(p.85-86)*

## Key Equations

$$
\phi : L \to T
$$
Where: $L$ is the language (set of sentences), $T = \{t, f, u\}$ is the set of truth values (true, false, unknown).
*(p.82)*

$$
\phi \leq \psi \iff \forall p \in L,\ \phi(p) = \psi(p) \text{ or } \phi(p) = u
$$
Extension ordering on truth functions.
*(p.82)*

$$
\text{cl}(\phi) \leq \phi
$$
Closure is always less than or equal to the original truth function (Lemma 2).
*(p.82)*

$$
\psi'(p) = \begin{cases} \psi(p), & \text{for } p \in L' \\ \phi(p), & \text{for } p \notin L' \end{cases}
$$
Construction for restricting truth function changes to sublanguage $L'$.
*(p.84)*

$$
\phi|_p(q) \doteq \text{cl}(\theta)(q)
$$
The counterfactual evaluation: the truth value of $q$ given counterfactual premise $p$.
*(p.83)*

## Parameters

This is a theoretical/formal paper with no numerical parameters.

## Implementation Details

### Data Structures
- **Truth function**: A mapping from propositions to $\{t, f, u\}$, implementable as a dictionary/hash map *(p.82)*
- **Language $L$**: The set of well-formed sentences; in practice, a finite set of atomic propositions plus compound sentences *(p.82)*
- **Sublanguage $V$**: A subset of $L$ encoding context-dependent information; determines which propositions may change under counterfactual reasoning *(p.81, p.83-84)*

### Core Algorithm: Counterfactual Evaluation

Given truth function $\phi$, premise $p$, and query $q$: *(p.83-84)*

1. Set $\phi(p) \leftarrow u$ (make premise unknown) *(p.83)*
2. Compute closure $\phi' = \text{cl}(\phi)$ (propagate logical consequences) *(p.83)*
3. Set $\phi'(p) \leftarrow t$ (assert premise true) *(p.83)*
4. Compute closure $\phi'' = \text{cl}(\phi')$ (propagate consequences of counterfactual premise) *(p.84)*
5. Return $\phi''(q)$ as the counterfactual truth value *(p.84)*

### Application to Diagnosis (Section 6)

The paper demonstrates the framework on a **full adder** circuit with: *(p.85)*
- Three inputs (X, Y, Z) *(p.85)*
- Two outputs: S (sum) and C (carry) *(p.85)*
- Components: two XOR gates (X1, X2), two AND gates (A1, A2), one OR gate (O1) *(p.85)*

**Structural description** in prefix predicate calculus (17 axioms SD1-SD17): *(p.84-85)*
- SD1: (XORG X1) *(p.84)*
- SD2: (XORG X2) *(p.84)*
- SD3: (ANDG A1) *(p.84)*
- SD4: (ANDG A2) *(p.84)*
- SD5: (ORG O1) *(p.84)*
- SD6-SD17: Connection axioms specifying wiring between gates *(p.84-85)*

**Observed behavior** (fault indicators): *(p.85)*
- AC1: (VAL (IN 1 F1) ON) *(p.85)*
- AC2: (VAL (IN 2 F1) OFF) *(p.85)*
- AC3: (VAL (IN 3 F1) OFF) *(p.85)*
- OB1: (VAL (OUT 1 F1) OFF) *(p.85)*
- OB2: (VAL (OUT 2 F1) OFF) *(p.85)*

**Diagnosis using predicate calculus**: Device assumptions SD1-SD5 are made independent of the counterfactual assumptions SD6-SD17 and AC1-AC3 (which are taken as inviolable). Analysis yields: *(p.85-86)*

$$
\text{(OR (NOT (XORG X1)) (NOT (XORG X2)))}
$$

Conclusion: one of the exclusive-or gates must be faulty. *(p.86)*

**Diagnosis using counterfactuals**: Taking device assumptions as counterfactual assumptions: *(p.86)*

$$
\text{OB1} \wedge \text{OB2} \to \text{(AND (ANDG A1) (ANDG A2) (ORG O1))}
$$

The remaining components (A1, A2, O1) are not contributing to the fault; their continued performance is *counterfactually* implied by the observed behavior. *(p.86)*

**Device assumptions replacement**: The paper replaces the structural description axioms SD1-SD5 with device axioms such as: *(p.85)*
- IF (XORG X) AND (VAL (IN 1 X) V1) AND (VAL (IN 2 X) V2) THEN (VAL (OUT 1 X) (XOR V1 V2))
- Similar axioms for ANDG and ORG *(p.85)*

These new axioms are consistent with the observed behavior of the adder, and lead to the conclusion that: *(p.85)*

$$
\text{(ON INT (XORG X1) (NOT (XORG X2)))}
$$
*(p.85)*

and: *(p.86)*

$$
\text{AND (AND A1) (AND2 A2) (ORG O1)}
$$

i.e., eliminate all but the first from the counterfactual results by restricting the five component descriptions SD1-SD5 to the restricted language $V$. *(p.86)*

### Edge Cases
- If changing $\phi(p)$ to $t$ produces no inconsistency, the counterfactual is trivially evaluated by closure *(p.84)*
- If the sublanguage $V$ is empty, no propositions can change and the counterfactual may be vacuously true or undefined *(p.84)*
- Multiple minimal $\phi''$ may exist (the paper notes this ambiguity in choosing between them remains an open problem) *(p.84)*
- It is possible, however, for a counterfactual analysis to suggest a violation of the single fault assumption when one is adequate; if the observed behavior can be explained either by the failure of a single component or by the simultaneous failure of a pair of different components, both will be proposed *(p.86)*

## Figures of Interest

- **Fig 1 (p.85):** Full adder circuit diagram showing three inputs (X, Y, Z), two XOR gates (X1, X2), two AND gates (A1, A2), one OR gate (O1), and two outputs (S = sum, C = carry)

## Results Summary

- The three-valued truth function framework with closure operations successfully formalizes counterfactual reasoning *(p.82-84)*
- The construction is provably equivalent to Lewis's possible worlds semantics (Theorem 4) *(p.84)*
- The approach cleanly separates context-dependent from context-independent aspects of counterfactual reasoning via sublanguage selection *(p.81, p.83-84)*
- Applied to automated diagnosis, the framework naturally encodes the single fault assumption and produces correct diagnostic conclusions for a full adder circuit *(p.85-86)*
- Counterfactual analysis can handle cases where the single fault assumption is violated by generating new diagnoses involving minimal sets of faulty components *(p.86)*

## Arguments Against Prior Work

### Against Lewis's Possible Worlds Semantics *(p.81)*
- From an AI perspective, the difficulty with Lewis's possible world semantics is that his notion of "similarity" is too vaguely defined to be computationally useful *(p.81)*
- Lewis's approach treats counterfactuals as statements about the "most similar" possible world where the antecedent is true, but what "similar" means is left to intuition rather than formalized *(p.81)*
- The paper provides a formal construction (Theorem 4) that is provably equivalent to Lewis's semantics but makes the similarity relation computationally tractable via truth function extension ordering *(p.84)*

### Against Pure Predicate Calculus Diagnosis *(p.85--86)*
- The standard predicate calculus approach to diagnosis can identify which components might be faulty (by finding which device assumptions must be denied), but it cannot establish which components are definitely *not* faulty *(p.85--86)*
- Counterfactual reasoning goes further: it can conclude that the continued correct performance of non-faulty components is counterfactually implied by the observations, providing positive evidence of correct functioning rather than mere absence of fault indicators *(p.86)*

### Against Unstructured Counterfactual Reasoning *(p.81)*
- Previous approaches to counterfactual reasoning failed to make the context-dependent nature of counterfactuals explicit *(p.81)*
- The paper argues that counterfactual evaluation requires separating context-dependent features (what may change) from context-independent ones (what is held fixed), and encoding this via sublanguage selection rather than leaving it implicit *(p.81, 83--84)*

### Against Classical Logic for Counterfactuals *(p.81)*
- Counterfactuals violate three properties that hold for classical material conditionals: contraposition fails, transitivity fails, and strengthening the antecedent fails (non-monotonicity) *(p.81)*
- The power failure example: "if the electricity hadn't failed, dinner would have been on time" does NOT license "if dinner wasn't on time, the electricity failed" (contraposition fails because other causes are possible, such as laziness on the part of the cook) *(p.81)*
- The Hoover example: "if Hoover had been born Russian, he'd have been a Communist" and "if he'd been a Communist, he'd have been a traitor" does NOT license "if he'd been born Russian, he'd have been a traitor" (transitivity fails) *(p.81)*
- Any adequate formal treatment must therefore use a non-classical logic that permits these failures *(p.81)*

## Design Rationale

### Why three-valued logic *(p.82)*
Two-valued logic (true/false) cannot represent uncertainty about propositions. By adding the truth value $u$ (unknown), the framework can represent partial knowledge: propositions whose truth value is genuinely unknown in the current state of knowledge. This is essential for counterfactual reasoning, where changing one proposition's truth value may leave others indeterminate. *(p.82)*

### Why closure as the core operation *(p.82)*
The closure of a truth function is the maximally extended consistent truth function — it assigns truth values to everything that can be determined from what is already known. This provides a unique, well-defined result for counterfactual evaluation: start with a partial truth function (after setting the counterfactual premise), compute its closure, and read off the consequences. The closure is always well-defined for consistent truth functions (Lemma 2). *(p.82)*

### Why sublanguage selection for context *(p.81, 83--84)*
Context dependence in counterfactual reasoning is encoded by choosing a sublanguage $V \subset L$. Propositions in $V$ are those whose truth values may change under counterfactual evaluation; propositions outside $V$ are held fixed. This makes the context-dependent/context-independent distinction explicit and formal, rather than relying on vague intuitions about "similarity." Different choices of $V$ correspond to different counterfactual evaluations of the same premise. *(p.81, 83--84)*

### Why prove equivalence to Lewis (Theorem 4) *(p.84)*
The equivalence to Lewis's possible worlds semantics establishes that the three-valued truth function framework is not a simplification or approximation but captures the full formal power of the philosophical theory. This licenses using the framework as a faithful computational implementation of counterfactual reasoning. *(p.84)*

### Why apply to automated diagnosis *(p.84--86)*
Diagnosis is a natural application domain because it inherently involves counterfactual reasoning: "if this component were functioning correctly, what would the output be?" The full adder example demonstrates that the framework subsumes the minimal fault assumption used in Genesereth's (1984) diagnosis methodology, while also providing stronger conclusions (exonerating non-faulty components). *(p.84--86)*

## Limitations

- The choice of sublanguage $V$ (which encodes context) has no formal method for selection -- it must be chosen on a case-by-case basis *(p.81)*
- The paper acknowledges ambiguity when multiple minimal truth functions $\phi''$ exist and provides no method for choosing between them *(p.84)*
- The approach requires generating device assumptions to replace the structural description, which may be difficult if these assumptions are invalid *(p.85)*
- The connection between counterfactual reasoning and causality is noted as "very loose" and not formalized *(p.80)*
- Only demonstrated on a simple circuit (full adder); scalability to larger systems not addressed *(p.85-86)*
- From an AI perspective, the difficulty with the possible worlds semantics is that Lewis's notion of "similarity" is too vaguely defined; the paper's approach addresses this but doesn't fully resolve it *(p.81)*

## Testable Properties

- **Closure idempotency**: For any consistent truth function $\phi$, $\text{cl}(\text{cl}(\phi)) = \text{cl}(\phi)$ *(p.82)*
- **Extension ordering**: If $\phi \leq \psi$ then $\text{cl}(\phi) \leq \text{cl}(\psi)$ *(p.82)*
- **Consistency preservation**: If $\phi$ is consistent, then $\text{cl}(\phi)$ is consistent *(p.82)*
- **Contraposition failure**: Given counterfactual $p > q$, it does NOT follow that $\neg q > \neg p$ (contraposition is not valid for counterfactuals) *(p.81)*
- **Transitivity failure**: From $p > q$ and $q > r$, it does NOT follow that $p > r$ (counterfactuals are not transitive) *(p.81)*
- **Non-monotonicity**: From $p > r$, it does NOT follow that $p \wedge q > r$ (strengthening the antecedent is invalid) *(p.81)*
- **Reduced iff closed**: A consistent truth function is reduced if and only if it is closed (Lemma 3) *(p.82)*
- **Lemma 1**: No extension of an inconsistent truth function is consistent *(p.82)*
- **Lemma 2**: Closure is always an extension: $\text{cl}(\phi) \leq \phi$ *(p.82)*

## Missed Findings (Added on Re-read)

### Counterfactual Implication Provides a Useful Constraint Beyond Classical Deduction
The paper argues that counterfactual implication (the $>$ connective) provides AI systems with information unavailable from classical deduction alone. Given a power failure example: "If there hadn't been a power failure after a MTrCH run, we want to know why the machine was undone. The answer 'there was a power failure' is inadequate, but 'the operator didn't switch over to battery' or 'the operations group would have been notified' — this is a useful constraint." *(p.81)*

### Ginsberg 1984 Technical Report
The paper cites Ginsberg (1984) as containing a more complete description of counterfactuals than can be included in the conference paper, including formal proofs. *(p.80)*

### Connection to Goal Regression
Counterfactuals will necessarily play a part in natural language understanding. The extent to which they capture our commonsense reasoning is a matter for future investigation. *(p.80)*

### Relationship to Quantified Counterfactuals
The paper notes that in more distant worlds (such as those where the ceasefire example applies), we need to consider not just propositional counterfactuals but also quantified ones — this is flagged as an area needing further work. *(p.81)*

### Framework Section Structure
Section 3 (Framework) explicitly defines the formal apparatus: a countably infinite language $L$, a set of propositions, truth functions as mappings $\phi: L \to \{t, f, u\}$. The paper notes the framework is most difficult to understand in any formal sense since it will be used in the next section in a fundamentally dependent upon context fashion. *(p.82)*

### Gensereth's Diagnosis Framework
The diagnosis application directly builds on Gensereth's (1984) proposal that it is possible for machines to be used in automated diagnosis, provided that the machines are given both a design for the device in question and the ability to manipulate the device by varying inputs and observing the results directly. *(p.84-85)*

## Relevance to Project

This paper provides the theoretical foundation for counterfactual reasoning within the propstore's belief revision and truth maintenance architecture. The three-valued truth function framework with closure operations maps directly onto ATMS-style environment management: assumptions correspond to propositions that may be set to $u$ (unknown/retracted), and counterfactual evaluation corresponds to exploring alternative assumption sets. *(p.82-84)* The sublanguage mechanism for encoding context dependence could inform how the propstore selects which assumptions are revisable vs. fixed when performing hypothetical reasoning. *(p.81, p.83-84)* The diagnosis application demonstrates how counterfactual reasoning integrates with the kind of assumption-based problem solving already represented in the collection (de Kleer 1986). *(p.85-86)*

## Open Questions

- [ ] How does the sublanguage selection mechanism map to ATMS context/environment selection? *(p.81, p.83-84)*
- [ ] Can the closure operation be implemented incrementally (as the ATMS does for label maintenance)? *(p.82)*
- [ ] How does performance scale with the size of the language $L$? *(p.82)*
- [ ] What is the relationship between Ginsberg's counterfactual framework and de Kleer's ATMS nogood management? *(p.82-84)*
- [ ] The paper mentions Ginsberg (1984) technical report as a more complete treatment -- is that worth retrieving? *(p.80)*

## Related Work Worth Reading

- Lewis, D., *Counterfactuals*, Harvard University Press, Cambridge (1973) -- the philosophical foundation *(cited p.80, p.81, p.84, p.86)*
- Stalnaker, I., "A theory of conditionals", in *Studies in Logical Theory* (1968) -- alternative possible worlds semantics *(cited p.86)*
- Genescreth, M.R., "The use of design descriptions in automated diagnosis", *Artificial Intelligence* 24 (1984), 411-436 -- the diagnosis framework applied in Section 6 *(cited p.84-85, p.86)*
- Glymour, C. and Thomason, R.H., "Default reasoning and the logic of theory perturbation", *Non-monotonic Reasoning Workshop* (1984) -- non-monotonic inference connection *(cited p.81, p.86)*
- Adams, E., "The logic of conditionals", *Inquiry* 8 (1965), 166-197 -- early formal treatment of conditionals *(cited p.86)*
- Ginsberg, M.L., "Counterfactuals", Stanford Logic Group Tech Report, 1984 -- the more complete treatment *(cited p.80, p.86)*
- Enderton, H.B., *A Mathematical Introduction to Logic*, Academic Press, 1972 -- formal logic foundations *(cited p.86)*
- Shoenfield, J., *Mathematical Logic*, Addison-Wesley, 1967 -- mathematical logic reference *(cited p.86)*

## Collection Cross-References

### Already in Collection
- (none directly cited)

### New Leads (Not Yet in Collection)
- Lewis, D. (1973) — "Counterfactuals" — the foundational philosophical work on possible worlds semantics that Ginsberg proves equivalent to his construction *(cited p.80, p.81, p.84, p.86)*
- Genescreth, M.R. (1984) — "The use of design descriptions in automated diagnosis" — the diagnosis framework applied in Section 6 *(cited p.84-85, p.86)*

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
- [[Halpern_2005_CausesExplanationsStructuralModel]] — **Strong.** Halpern-Pearl operationalize counterfactual reasoning for actual causation via structural equations and interventions rather than possible worlds. Both papers share the fundamental insight that counterfactual evaluation requires determining what to hold fixed and what to vary — Ginsberg via sublanguage selection, HP via the (Z, W) partition in AC2. Ginsberg's equivalence with Lewis (Theorem 4) connects to HP's critique of Lewis's counterfactual account of causation.
