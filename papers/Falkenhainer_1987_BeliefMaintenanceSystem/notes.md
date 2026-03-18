---
title: "Towards a General-Purpose Belief Maintenance System"
authors: "Brian Falkenhainer"
year: 1987
venue: "AAAI-87 (Second Conference on Uncertainty in Artificial Intelligence)"
doi_url: "https://arxiv.org/abs/1304.3084"
---

# Towards a General-Purpose Belief Maintenance System

## One-Sentence Summary
Presents a Belief Maintenance System (BMS) that extends justification-based Truth Maintenance Systems to manage probabilistic beliefs using Dempster-Shafer theory, replacing binary true/false states with continuous belief intervals while preserving TMS-like dependency-driven propagation.

## Problem Addressed
Traditional Truth Maintenance Systems operate with true/false/unknown states, but many real-world AI problems require reasoning under uncertainty with partial, graded beliefs. Non-monotonic TMS (Doyle, 1979) attempts reasoning when not all facts are known, but fails to account for degrees of belief or combine evidence from multiple uncertain sources. Previous probabilistic reasoning systems (Pearl, 1983; Buchanan et al, 1984) used static networks that cannot be dynamically modified, or simple forward chaining without complete reason-maintenance facilities. The BMS bridges this gap.

## Key Contributions
- Defines a **Belief Maintenance System** (BMS) that manages a current set of beliefs in the same way a TMS manages true/false propositions
- Beliefs are represented as Dempster-Shafer intervals [s(A), p(A)] rather than binary truth values
- Automatically propagates belief changes through a dependency network when antecedent beliefs change
- Reduces to a standard TMS when all beliefs are absolute (0 or 1)
- Introduces **support links** with two types: **hard links** and **invertible links**, governing how belief changes propagate
- Implements belief-threshold-based query semantics (true?, false?, unknown?, etc.)
- Supports **frames of discernment** for user-defined possibility spaces
- Includes a **rule engine** with three rule types: `:INTERN`, `BELIEF+`, `BELIEF-`
- Demonstrates **rule-based probabilistic pattern matching** consistent with Gentner's Structure-Mapping Theory of analogy

## Methodology
The paper builds the BMS as a monotonic extension of Doyle's justification-based TMS (1979). The core design has three parts: (1) the knowledge base network structure, (2) the user hooks to the control structure, and (3) the belief formalism. A simple parser translates user assertions (e.g. `implies`, `and`, `a`, `b`, `c`) into control primitives, enabling the basic design to be semi-independent of the specific belief system used.

## Key Equations

### Dempster's Rule (Combining Beliefs)
For combining two basic probability functions m_1 and m_2 over the same frame of discernment:

$$
m = m_1 \oplus m_2
$$

Where m is the orthogonal sum of the two sources.

### Simplified Dempster's Rule (Two-Valued Case)
In the deductive reasoning case where the frame of discernment contains only {A, not-A}, the basic probability function has three values: m(A), m(not-A), and m(Theta). The simplified combination formula (Prade, 1983; Ginsberg, 1984):

$$
(a \; b) \oplus (c \; d) = \left(1 - \frac{\bar{a}\bar{c}}{1 - (ad + bc)}, \quad 1 - \frac{\bar{b}\bar{d}}{1 - (ad + bc)}\right)
$$

Where a-bar means (1 - a). This allows formulating an inverse function for subtracting evidence (Ginsberg, 1984):

$$
(a \; b) - (c \; d) = \left(\frac{\bar{c}(a\bar{d} - \bar{b}\bar{c})}{\bar{c}d - b\bar{c}\bar{c} - \bar{a}\bar{d}\bar{d}}, \quad \frac{\bar{d}(b\bar{c} - \bar{a}\bar{d})}{\bar{c}d - b\bar{c}\bar{c} - \bar{a}\bar{d}\bar{d}}\right)
$$

### Belief Representation
A node's belief is represented as the Shafer interval:

$$
[s(A), p(A)]
$$

Where:
- s(A) = current amount of support for A (belief function value)
- p(A) = plausibility of A
- p(A) = 1 - s(not-A)

### NOT Operator
Because Dempster-Shafer theory expresses belief as a single probability interval, NOT is simply:

$$
(\text{not } A)_{[s, p]} = A_{[1-p, 1-s]}
$$

### AND Operator (Garvey et al, 1981)
For conjuncts A, B, C:

$$
(A \& B \& C)_{[\max(s_A + s_B + s_C - 2, 0), \min(s_A, s_B, s_C)]}
$$

The -2 term represents (1 - cardinality(conjuncts)).

### OR Operator
The belief in OR is the maximum of the individual beliefs (Garvey et al, 1981):

$$
(A \vee B)_{[\max(s_A, s_B), \max(0, p_A + p_B - 1)]}
$$

### IMPLIES Operator
Following Ginsberg (1984) and Dubois & Prade (1985), for A implies B, if full belief in A implies B_{0,b} then a half belief in A should imply B_{0,4}:

$$
(A \rightarrow B)_{[s, p]} = \frac{A_{[s_A, p_A]}}{B_{[s_B, p_B]}}
$$

This adheres to the principle that full belief in A implying B implies B with the same strength proportionally.

## Parameters

| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|
| Propagation-delta threshold | - | - | 10^-3 | >0 | Below this threshold, belief changes are not propagated further (terminates early) |
| Belief-threshold (true?) | - | - | - | [0, 1] | belief+(node) > threshold for a node to be considered true |
| Belief-threshold (false?) | - | - | - | [0, 1] | belief-(node) > threshold for a node to be considered false |

### Query Semantics

| Query | Definition |
|-------|-----------|
| true? | belief+(node) > *belief-threshold* |
| false? | belief-(node) > *belief-threshold* |
| unknown? | belief+(node) < *belief-threshold* AND belief-(node) < *belief-threshold* |
| absolutely-true? | belief+(node) = 1.0 |
| absolutely-false? | belief-(node) = 1.0 |
| absolutely-unknown? | belief+(node) = 0.0 AND belief-(node) = 0.0 |
| support-for | belief+(node) |
| support-against | belief-(node) |
| possible-true | 1 - belief-(node) |
| possible-false | 1 - belief+(node) |
| belief-uncertainty | 1 - belief-(node) - belief+(node) |

## Implementation Details

### Three-Part Architecture
1. **Knowledge base** — network of nodes with support links and belief intervals
2. **Control structure** — hooks for user to interact, assertion parsing
3. **Belief formalism** — Dempster-Shafer interval arithmetic

### Support Link Types
1. **Hard support links** — provide an absolute statement of consequent's belief. AND nodes get their value from the conjunctive formula. The value of the consequent node equals the link's support.
2. **Invertible support links** — act as the only source of evidence for their consequent. Old support must be subtracted (using inverted Dempster's rule) before new value is added. Used for implication and user-support links.

### Belief Propagation (Section 2.4)
- When a node's belief is modified, effects propagate throughout the system via outgoing links
- For hard links: new support = recalculated from all antecedents
- For invertible links: old support subtracted, new support added using Dempster's rule
- **Propagation-delta threshold** (default 10^-3): if the change to a node's positive and negative beliefs are both less than this threshold, propagation stops at that node (Ginsberg, 1985a)

### Circular Support Handling (Section 2.4.1)
Current implementation: no circular support structures allowed; system signals error if one is discovered. Three identified problems:
1. **Interpretation of circular evidence** — When A is partially believed and E's status is unknown, which node's support does D provide to B? Circular evidence amplifies belief along the loop.
2. **Possible cures** — (a) D could be disallowed from supporting B (undefined under normal probability theory); (b) chain can be stopped by not allowing support to reach a supporter (introduces new problem: what about independent support for D?); (c) force system to only propagate supports for D that are independent of B (requires sophisticated control structure)
3. **Retraction/modification of support** — Modifying support links in circular structures requires retracting old support from A, propagating through B, then through the entire cycle, leading to quadratic propagation cost

### Non-Monotonic Reasoning Support
The BMS handles non-monotonic reasoning more elegantly than a two or three valued logic system (Ginsberg, 1984, 1985b). For the classic "birds fly" problem:
- `(bird ?x) -> (fly ?x)_{[0.90, 0.95]}` states 90-95% of birds fly
- `(ostrich ?x) -> (fly ?x)_{[0, 1)}` overrides without needing special control structure changes

### Rule Engine (Section 2.6)
Rules are pattern-directed, in the form: `(rule (nested-triggers) body)`

Three rule trigger types:
- **`:INTERN`** — fires each time a new fact matching the pattern is added to the knowledge base
- **`BELIEF+`** — fires each time the support in favor of a matching pattern first exceeds a specified value (e.g., 0.8)
- **`BELIEF-`** — fires when the support against a matching pattern exceeds a specified value

### Rule-Based Probabilistic Pattern Matching (Section 3.1)
The BMS implements a rule-based, probabilistic pattern matching algorithm consistent with Gentner's Structure-Mapping Theory of analogy (Gentner, 1983; Falkenhainer, Forbus, & Gentner, 1986):
1. Assert a **match hypothesis** for each potential predicate or object pairing between source (a) and target (b) with belief of zero
2. All predicates with the same name pair up; all functional predicates pair up if their parent predicates pair up
3. Run **match hypothesis evidence rules** to calculate the likelihood of each match hypothesis
4. Form **global matches** — consistent sets of matches where no item is paired with more than one other item
5. Select the "best" global match using a frame of discernment over the set of global matches, with support based on syntactic aspects (overall size, "match quality")

Example match hypothesis evidence rule:
```
(assert same-functor)
(rule ((:intern (MH ?i1 ?i2)
        test (and (fact? ?i1) (fact? ?i2)
                  (equal-functors? ?i1 ?i2))))
  (assert (implies same-functor (MH ?i1 ?i2)
           (0.5  0.0))))
```
States: "If two items are facts and their functors are the same, then supply 0.5 evidence in favor of the match hypothesis."

## Figures of Interest
- **Fig 1 (page 72):** Sample BMS network showing nodes A through E with belief intervals. A=(0.5, 0.0), B=(0.7, 0.0), A&B=(0.2, 0.0), C=(0.15, 0.24) with D=(0.4, 0.0) and connections showing hard and invertible support links with belief intervals at each node.
- **Fig 2 (page 73):** Circular support structure — nodes A, B, C, D, E in a cycle demonstrating the problematic case where evidence can be amplified by flowing around the loop.
- **Fig 3 (page 75):** BMS state after running match hypothesis evidence rules. Table showing 10 match hypotheses with their evidence values ranging from 0.632 to 0.932.

## Results Summary
The paper demonstrates the BMS through two examples:
1. **Standard deductive logic** — the BMS performs normal TMS operations (assert, retract, contradict) when beliefs are absolute
2. **Analogical pattern matching** — the BMS successfully identifies structural correspondences between two domains (beaker/coffee vs ice-cube/heat-bar) using probabilistic match hypotheses, with evidence values ranging from 0.632 to 0.932 for different match hypotheses

## Limitations
- **Circular support structures** are not handled — the system simply signals an error when one is discovered
- Explicit **transitivity relations** cause problems — asserting A->C based on A->B and B->C increases C's belief even though it's making explicit information that already existed
- The system does not provide operations for generating explicit transitivity relations, which would cause new problems for belief-based reasoning systems
- The design is **independent of belief formalism** but the specific Dempster-Shafer implementation has known issues with certain edge cases
- Non-monotonic inferences in the presence of circular support should not be interpreted as contradictions, adding complexity

## Testable Properties
- When all beliefs are absolute (0 or 1), the BMS must reduce to standard TMS behavior (true/false/unknown)
- Combining two independent belief sources via Dempster's rule must be commutative: (a b) + (c d) = (c d) + (a b)
- Belief propagation must terminate when both positive and negative belief changes are below the propagation-delta threshold (default 10^-3)
- For any node: belief-uncertainty = 1 - belief+(node) - belief-(node) >= 0
- The NOT operator must be self-inverse: NOT(NOT(A)) = A (i.e., inverting the interval twice returns the original)
- AND of conjuncts must never exceed the minimum individual support: s(A & B) <= min(s(A), s(B))
- Subtracting evidence and then re-adding it must return to the original belief (invertibility of Dempster's rule for invertible links)
- The BMS must signal an error when circular support structures are detected

## Relevance to Project
This paper presents a foundational approach to maintaining a network of beliefs with continuous confidence values and automatic propagation — directly relevant to any propositional store that needs to track belief strengths, evidence combination, and dependency-driven updates across a knowledge base. The BMS design pattern of support links (hard vs invertible) and Dempster-Shafer belief intervals provides a concrete architecture for managing uncertain propositions.

## Open Questions
- [ ] How should circular support structures be handled in practice? The paper identifies the problem but offers no solution.
- [ ] What is the computational complexity of belief propagation in large networks? The paper does not analyze this.
- [ ] How does the BMS interact with more modern belief update frameworks (e.g., Bayesian networks)?
- [ ] The pattern matching application uses Gentner's SMT — how does the probabilistic version compare to the deterministic SME implementation (Falkenhainer et al, 1986)?

## Related Work Worth Reading
- Doyle, J., "A Truth Maintenance System," *Artificial Intelligence* 12, 1979. (Foundation TMS that the BMS extends)
- Shafer, G., *A Mathematical Theory of Evidence*, Princeton, 1976. (Dempster-Shafer theory basis)
- Ginsberg, M.L., "Non-Monotonic Reasoning Using Dempster's Rule," *Proceedings AAAI*, August, 1984. (Direct predecessor for the belief formalism)
- Ginsberg, M.L., "Implementing Probabilistic Reasoning," *Workshop on Uncertainty and Probability in Artificial Intelligence*, August, 1985a. (Propagation-delta threshold, combination formula details)
- Falkenhainer, B., Forbus, K., Gentner, D., "The Structure-Mapping Engine," *Proceedings AAAI*, August, 1986. (The pattern matching algorithm the BMS implements)
- McAllester, D.A., "Reasoning Utility Package User's Manual," MIT AI Memo 667, April, 1980. (Rule engine foundation)

## Collection Cross-References

### Already in Collection
- [[Doyle_1979_TruthMaintenanceSystem]] — cited as the foundational justification-based TMS that the BMS directly generalizes from binary to continuous-valued beliefs.
- [[McAllester_1978_ThreeValuedTMS]] — cited via McAllester 1980 (Reasoning Utility Package); the BMS rule engine builds on McAllester's pattern-matching architecture.

### New Leads (Not Yet in Collection)
- Shafer, G. (1976) — "A Mathematical Theory of Evidence" — the Dempster-Shafer theory foundation for the BMS's belief intervals
- Ginsberg, M.L. (1984) — "Non-Monotonic Reasoning Using Dempster's Rule" — provides the simplified Dempster's rule formulas used in the BMS

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- [[Shapiro_1998_BeliefRevisionTMS]] — surveys the BMS implicitly as part of the TMS tradition; the BMS is a variant of the JTMS architecture extended with continuous beliefs

### Conceptual Links (not citation-based)
- [[Ginsberg_1985_Counterfactuals]] — **Moderate.** Both Falkenhainer and Ginsberg draw on three-valued or continuous-valued approaches to extend binary TMS reasoning. The BMS uses Dempster-Shafer intervals [s,p] while Ginsberg uses {t,f,u} truth values with closure operations. Both address the same limitation of binary TMS systems: inability to represent partial/uncertain belief.
- [[deKleer_1986_AssumptionBasedTMS]] — **Strong.** Both systems extend Doyle's TMS in different dimensions: the ATMS extends to multiple simultaneous contexts (environments), while the BMS extends to continuous-valued beliefs within a single context. The BMS's hard and invertible support links are analogous to ATMS justifications, and both propagate changes through dependency networks. Complementary extensions that could theoretically be combined.
- [[Pollock_1987_DefeasibleReasoning]] — **Moderate.** Both address graded or defeasible support for beliefs. The BMS provides a quantitative mechanism (Dempster-Shafer intervals) while Pollock provides a qualitative one (prima facie reasons with defeat levels). Pollock's undercutting defeaters are conceptually related to the BMS's evidence subtraction via inverted Dempster's rule.
