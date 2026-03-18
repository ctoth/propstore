---
title: "A Logic for Default Reasoning"
authors: "Raymond Reiter"
year: 1980
venue: "Artificial Intelligence"
doi_url: "https://doi.org/10.1016/0004-3702(80)90014-4"
---

# A Logic for Default Reasoning

## One-Sentence Summary
Provides the foundational formal logic for default reasoning --- defining default rules, default theories, extensions, and normal defaults --- with a complete proof theory for normal default theories based on top-down linear resolution, plus criteria for when belief revision is needed upon new observations.

## Problem Addressed
Standard first-order logic is monotonic: adding new information never invalidates previous conclusions. But in AI, reasoning frequently requires defaults --- assumptions made "in the absence of information to the contrary" --- which must be retractable when contradicting evidence emerges. No prior work had provided a satisfactory formal logic for this kind of reasoning within a purely first-order framework.

## Key Contributions
- Formal definition of **default rules** with prerequisite, justification, and consequent
- Definition of **default theories** as pairs (D, W) of defaults and first-order axioms
- Definition of **extensions** as fixed points of the operator Gamma, characterizing acceptable belief sets induced by defaults
- Identification of the important subclass of **normal defaults** (where justification equals consequent) and proof that every closed normal default theory has an extension
- A complete **proof theory** for closed normal default theories using top-down linear resolution with indexed clauses
- Proof that the **extension membership problem** for closed normal default theories is not semi-decidable (Theorem 4.9)
- Formal criteria for **belief revision** --- when derived beliefs can safely persist despite new information
- Generalization from closed to **open (arbitrary) default theories** via Skolemization

## Methodology
The paper works entirely within first-order logic, extending it with meta-rules called defaults. The approach:
1. Define a fixed-point operator Gamma on sets of closed wffs, whose fixed points are the extensions
2. Prove basic properties (minimality, consistency, semi-monotonicity) for closed theories
3. Specialize to normal defaults where stronger results hold (existence of extensions, orthogonality, unique extension under consistency)
4. Develop a proof theory based on default proofs (sequences of default sets) and show completeness for normal defaults
5. Interface the proof theory with a resolution theorem prover via indexed clauses
6. Address belief revision by showing when derived beliefs safely persist under new observations or new defaults
7. Generalize all results to open defaults via Skolemization

## Key Equations

### Default Rule Form

$$
\frac{\alpha(\mathbf{x}) : M\beta_1(\mathbf{x}), \ldots, M\beta_m(\mathbf{x})}{w(\mathbf{x})}
$$

Where: $\alpha(\mathbf{x})$ is the prerequisite (a wff), $\beta_1, \ldots, \beta_m$ are the justifications (wffs prefixed with the modal operator M meaning "it is consistent to assume"), and $w(\mathbf{x})$ is the consequent.

### Normal Default Form

$$
\frac{\alpha(\mathbf{x}) : Mw(\mathbf{x})}{w(\mathbf{x})}
$$

Where: the single justification equals the consequent. Read: "If alpha holds and it is consistent to assume w, then conclude w."

### Extension Operator (Definition 1)

For a closed default theory $\Delta = (D, W)$ where every default has closed wffs, for any set of closed wffs $S \subseteq L$, define $\Gamma(S)$ as the smallest set satisfying:

- D1. $W \subseteq \Gamma(S)$
- D2. $\text{Th}_L(\Gamma(S)) = \Gamma(S)$
- D3. If $(\alpha : M\beta_1, \ldots, M\beta_m / w) \in D$ and $\alpha \in \Gamma(S)$ and $\neg\beta_1, \ldots, \neg\beta_m \notin S$, then $w \in \Gamma(S)$.

A set of closed wffs $E$ is an **extension** for $\Delta$ iff $\Gamma(E) = E$ (i.e., $E$ is a fixed point).

### Iterative Characterization of Extensions (Theorem 2.1)

$$
E_0 = W
$$

$$
E_{i+1} = \text{Th}_L(E_i) \cup \left\{ w \;\middle|\; \frac{\alpha : M\beta_1, \ldots, M\beta_m}{w} \in D,\; \alpha \in E_i,\; \neg\beta_1, \ldots, \neg\beta_m \notin E \right\}
$$

Then $E$ is an extension for $\Delta$ iff $E = \bigcup_{i=0}^{\infty} E_i$.

### Generating Defaults

$$
\text{GD}(E, \Delta) = \left\{ \frac{\alpha : M\beta_1, \ldots, M\beta_m}{w} \in D \;\middle|\; \alpha \in E \text{ and } \neg\beta_1, \ldots, \neg\beta_m \notin E \right\}
$$

### Extension Content (Theorem 2.5)

$$
E = \text{Th}_L(W \cup \text{CONSEQUENTS}(\text{GD}(E, \Delta)))
$$

### Non-Monotonic Translation (Equation 2.2)

A default $\alpha(\mathbf{x}) : M\beta_1(\mathbf{x}), \ldots, M\beta_m(\mathbf{x}) / w(\mathbf{x})$ maps to the modalized formula:

$$
(\mathbf{x}).\alpha(\mathbf{x}) \wedge M\beta_1(\mathbf{x}) \wedge \cdots \wedge M\beta_m(\mathbf{x}) \supset w(\mathbf{x})
$$

### Default Proof (Definition 3)

For a closed normal default theory $\Delta = (D, W)$, a finite sequence $D_0, \ldots, D_k$ of finite subsets of $D$ is a **default proof of $\beta$** with respect to $\Delta$ iff:

- P1. $W \cup \text{CONSEQUENTS}(D_0) \vdash \beta$
- P2. For $1 \leq i \leq k$: $W \cup \text{CONSEQUENTS}(D_i) \vdash \text{PREREQUISITES}(D_{i-1})$
- P3. $D_k = \emptyset$
- P4. $W \cup \bigcup_{i=0}^{k} \text{CONSEQUENTS}(D_i)$ is satisfiable

### Consistency Condition for Belief Revision (Theorem 6.1)

Let $\Delta_0 = (D, W)$ be a closed normal default theory. If $\beta_i$ has been derived with default proof $P_{\beta_i}$ with respect to $\Delta_i$ where $\Delta_{i+1} = (D, W \cup \{\beta_0, \ldots, \beta_i\})$, then for any $n \geq 0$, if:

$$
W \cup \bigcup_{i=0}^{n} \text{CONSEQUENTS}(\text{DS}(P_{\beta_i})) \text{ is consistent}
$$

then $\Delta_0$ has an extension $E_0$ such that $\{\beta_0, \ldots, \beta_n\} \subseteq E_0$.

## Parameters

This is a formal logic paper; no empirical parameters in the usual sense.

| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|
| Number of justifications in a default | m | - | - | 1 to infinity | Normal defaults have m=1 with justification = consequent |

## Implementation Details

### Data Structures
- **Default rule**: triple of (prerequisite wff, list of justification wffs, consequent wff)
- **Default theory**: pair (D, W) where D is a set of defaults and W is a set of first-order wffs
- **Extension**: a deductively closed set of wffs --- computed as a fixed point
- **Indexed clause**: pair (C, D) where C is a clause and D is a set of defaults that contributed to deriving C
- **Default proof**: sequence of finite sets of defaults $D_0, \ldots, D_k$ satisfying P1-P4

### Initialization
1. Start with axiom set W
2. Define default set D
3. Compute extensions via the iterative characterization (Theorem 2.1)

### Top-Down Default Proof Procedure (Definition 4, Section 5)
1. Given goal wff $\beta$, begin with a linear resolution proof of $\beta$ from CLAUSES($\Delta$)
2. Determine $D_0$ from the defaults used in the proof
3. For each subsequent level, determine $D_i$ by proving PREREQUISITES($D_{i-1}$) using linear resolution
4. Terminate when $D_k = \emptyset$
5. Check satisfiability: $W \cup \bigcup_{i=0}^{k} \text{CONSEQUENTS}(D_i)$ must be satisfiable

### Edge Cases
- A default theory may have **no extensions** (Example 2.6: $D = \{:MA / \neg A\}$, $W = \emptyset$)
- A default theory may have **multiple extensions** (Example 2.1: different defaults yield conflicting conclusions)
- An **inconsistent extension** arises iff W itself is inconsistent (Corollary 2.2-2.3)
- Extension membership is **not semi-decidable** for closed normal default theories (Theorem 4.9)

### Skolemization for Open Defaults (Section 7.1)
To handle open (non-closed) defaults:
1. Replace each wff $w(\mathbf{x})$ of $W$ by its Skolemized form
2. Replace each default's consequent by its Skolemized form (top half unchanged)
3. Define individuals of the theory as elements of $F \cup \Sigma$ (function letters and Skolem functions)
4. Define CLOSED-DEFAULTS($\Delta$) as all ground instances over $H(F \cup \Sigma)$
5. Extensions for the open theory $\Delta$ are extensions of the closed theory CLOSED($\Delta$) = (CLOSED-DEFAULTS($\Delta$), $W$)

### Belief Revision Protocol (Section 6)
When derived beliefs may conflict with new observations:
1. Attempt to rederive a minimal subset of derived beliefs B such that the resulting set of default proofs satisfies the consistency property
2. Failing that, reject some minimal subset of B
3. This is the role of Doyle's Truth Maintenance System (1978)

## Figures of Interest
- **Fig. 1 (page 106/p26):** Structure of a linear resolution proof --- a chain of resolvents $R_0, R_1, \ldots, R_n$ with side clauses $C_0, C_1, \ldots, C_{n-1}$
- **Fig. 2 (page 109/p29):** Example top-down default proofs for Example 5.2, showing how indexed clauses track default usage
- **Fig. 3 (page 110/p30):** Top-down default proofs for Example 5.3, including a blocked proof attempt
- **Fig. 4 (page 118/p38):** Linear resolution proof structure with pairs $(R_i, D'_i)$ and $(C_i, D_i)$, generalized for open defaults
- **Fig. 5 (page 120/p40):** Example top-down default proofs with indexed clauses for Example 5.2 under the modified definition
- **Fig. 6 (page 123/p43):** Admissible proof sequences for Example 7.2, showing Skolemized defaults
- **Fig. 7 (page 125/p45):** Counter-example (Example 7.3) showing why admissible proof sequences need to be restricted to top-down default proofs

## Results Summary
- Every closed normal default theory has at least one extension (Theorem 3.1)
- Extensions of normal default theories are minimal (Theorem 2.4) and orthogonal: distinct extensions of a normal default theory union to an inconsistent set (Theorem 3.3)
- A consistent closed normal default theory with $W \cup \text{CONSEQUENTS}(D)$ consistent has a unique extension (Corollary 3.4)
- Semi-monotonicity: adding normal defaults to a normal default theory can never reduce the number of extensions (Theorem 3.2, 3.5)
- The proof theory for closed normal defaults is complete (Theorem 4.8): $\beta \in E$ iff $\beta$ has a default proof w.r.t. $\Delta$
- Top-down default proofs are complete for closed normal defaults (Theorem 5.1)
- Extension membership is not semi-decidable (Theorem 4.9)
- Belief revision criteria: derived beliefs safely persist if the union of their default supports remains consistent (Theorems 6.1-6.3)
- All results on normal defaults generalize to open normal defaults via Skolemization (Section 7)
- Completeness of top-down default proofs generalizes to open normal defaults (Theorem 7.3)

## Limitations
- The proof theory is only complete for **normal** default theories; general (non-normal) default theories do not admit a local proof procedure
- General default theories may have **no extensions** and are inherently non-local in their proof requirements
- Extension membership is **not semi-decidable** even for normal defaults, meaning any computational treatment must be heuristic
- The satisfiability test in condition P4 of default proofs is itself undecidable in general
- The belief revision problem (when consistency fails) is left largely unaddressed --- the paper identifies the problem but does not solve it
- No model theory is provided for default logic (identified as future work in Section 8)
- No treatment of priorities among conflicting defaults beyond a brief discussion

## Testable Properties
- For any closed normal default theory $(D, W)$ with consistent $W$: at least one extension exists
- If $E$ and $F$ are distinct extensions of a closed normal default theory: $E \cup F$ is inconsistent
- If $W \cup \text{CONSEQUENTS}(D)$ is consistent for a closed normal default theory: there is a unique extension
- Adding normal defaults to a closed normal default theory never reduces the number of extensions
- For a consistent closed normal default theory: $\beta \in E$ for some extension $E$ iff there exists a default proof of $\beta$
- An extension $E$ satisfies $E = \text{Th}_L(W \cup \text{CONSEQUENTS}(\text{GD}(E, \Delta)))$
- The extension membership problem is not semi-decidable (no algorithm can enumerate all beliefs of an arbitrary extension)

## Relevance to Project
This paper is the foundational reference for default reasoning in the propstore's truth maintenance and assumption-tracking architecture. Default logic provides the formal substrate for:
- Representing assumptions that hold "by default" and can be retracted when contradicting evidence arrives
- Defining extensions as coherent sets of beliefs under defaults, directly analogous to ATMS environments
- The proof theory mechanism for determining whether a belief is supported by defaults, which maps to the propstore's claim provenance tracking
- Belief revision criteria that determine when previously derived beliefs must be revisited upon new observations, which is the core problem for maintaining a consistent world model

## Open Questions
- [ ] Relationship between extensions and model theory (model-theoretic characterization of extensions)
- [ ] Relationship between default logic and McCarthy's circumscription
- [ ] Efficient heuristics for the satisfiability test in default proofs
- [ ] Techniques for choosing between competing extensions
- [ ] How to handle priorities among defaults
- [ ] Decidable subclasses beyond the sentential and monadic cases

## Related Work Worth Reading
- McDermott, D. and Doyle, J., "Non-monotonic Logic I" (1978) --- modal logic approach to non-monotonic reasoning, closely related but more general/less tractable
- Doyle, J., "Truth Maintenance Systems for Problem Solving" (1978) --- heuristic implementation of belief revision, already in the collection
- McCarthy, J., "Epistemological problems of Artificial Intelligence" (1977) --- circumscription as an alternative formalization
- Sandewall, E., "An approach to the frame problem" (1972) --- frame default as a default schema
- Clark, K., "Negation as failure" (1978) --- relationship between negation in PROLOG and closed world defaults
