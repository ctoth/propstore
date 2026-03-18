---
title: "Problem Solving with the ATMS"
authors: "Johan de Kleer"
year: 1986
venue: "Artificial Intelligence"
doi_url: "https://doi.org/10.1016/0004-3702(86)90082-2"
---

# Problem Solving with the ATMS

## One-Sentence Summary
Presents a complete control regime and constraint language for building problem solvers on top of the Assumption-based Truth Maintenance System (ATMS), including consumer architecture, scheduling, dependency-directed backtracking, and comparison with Doyle's TMS, McAllester's RUP, McDermott's system, and MBR.

## Problem Addressed
The ATMS provides soundness, completeness, and consistency guarantees for default reasoning, but these can be inadvertently lost if the problem solver does not interface correctly. This paper addresses how to build problem solvers that preserve those guarantees through a disciplined control regime.

## Key Contributions
- Defines a **consumer architecture** for encoding problem-solving steps as modular units (consumers) attached to ATMS nodes
- Introduces **class consumers**, **conjunctive class consumers**, and **constraint consumers** for efficient rule encoding
- Presents scheduling strategies: simplest-label-first, before/after consumer ordering, dependency-directed backtracking via control disjunctions
- Defines a **simple constraint language** (PLUS, TIMES, AND, OR, ONEOF, etc.) built entirely on ATMS primitives
- Provides detailed comparison with Doyle's TMS, McAllester's RUP, McDermott's system, Martins' MBR, and Williams' ART

## Methodology
The paper builds a layered architecture:
1. **ATMS base**: nodes with labels (sets of environments), justifications, nogoods
2. **Consumer layer**: rules that fire when antecedent nodes have nonempty labels; consumers run once per node, producing new justifications
3. **Control layer**: scheduling (simplest environments first), dependency-directed backtracking (control disjunctions), delayed justifications, kernel environments
4. **Constraint language**: translates arithmetic/logical constraints into sets of consumers and justifications

## Key Equations

Justification form:

$$
\alpha_1, \alpha_2, \ldots \Rightarrow \beta
$$

Where $\alpha_i$ are problem-solver data, assumptions, or falsity $\perp$. Interpreted as material implication:

$$
\alpha_1 \wedge \alpha_2 \wedge \cdots \rightarrow \beta
$$

Node representation:

$$
\langle \text{datum}, \text{label}, \text{justifications} \rangle
$$

Environment lattice: for $n$ assumptions, $2^n$ environments, at most $2^n$ contexts.

Label for $x = 1$:

$$
\langle x = 1, \{\{A, C\}, \{D, E\}\}, \{\ldots\} \rangle
$$

Constraint consumer inverse:

$$
x_i = R_i^{-1}(x_1, \ldots, x_{i-1}, x_{i+1}, \ldots)
$$

PLUS constraint inverse:

$$
v_i = -\sum_{j \neq i} v_j
$$

TIMES constraint inverse (when $v \neq 0$):

$$
v_i = \frac{\prod_{j \neq i} v_j}{v}
$$

Parity encoding with delayed justifications:

$$
p_{i-1} = 0, b_i = 1 \implies p_i = 1
$$

$$
p_{i-1} = 1, b_i = 0 \implies p_i = 1
$$

$$
p_{i-1} = 0, b_i = 0 \implies p_i = 0
$$

$$
p_{i-1} = 1, b_i = 1 \implies p_i = 0
$$

## Parameters

| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|
| Number of assumptions | $n$ | - | - | 1-$\infty$ | Determines environment lattice size $2^n$ |
| Number of environments per label | - | - | - | 1-$2^n$ | Label is set of greatest lower bounds |
| Consumer execution count | - | - | 1 | 1 | Consumers execute exactly once per node |

## Implementation Details

### Data Structures
- **Node**: (datum, label, justifications) triple
- **Environment lattice**: $2^n$ vertices for $n$ assumptions; nogoods are crossed-out vertices
- **Consumer queue**: nodes with pending consumers and nonempty labels; no separate agenda needed
- **Control disjunctions**: `control{C1, C2, ...}` — scheduler maintains current environment satisfying all control disjunctions

### Consumer Types
1. **Basic consumer** $F$: attached to single node, runs once per node when label becomes nonempty
2. **Conjunctive consumer**: attached to list of nodes, runs when conjunction of antecedent labels yields consistent environment; invoked on cross-product of antecedent-class node sets (tuple-based)
3. **Class consumer**: attached to a class (generalized variable), runs once per node-class instance
4. **Constraint consumer**: triggers constraint $R(x_1, x_2, \ldots)$ when all but one antecedent hold; suppresses spurious retriggering
5. **Conditional constraint consumer**: like constraint consumer but conditional on a node being in a particular operating region
6. **Implication consumer** (exclusive/inclusive): encodes $a \rightarrow b \oplus c$ using `choose{B', C'}` disjunction; builds environment consumers that delay until efficient

### Scheduling Algorithm
1. Pick node with smallest environment (fewest assumptions) from consumer queue
2. Execute consumer, discard it
3. Repeat until no pending consumers with nonempty labels
- Before/after ordering: "before" consumers (cheap checks like contradiction detection) run first; "after" consumers (expensive computation) run last

### Constraint Language Primitives
- `EQ(l, v1, v2)`: $v_1 = v_2$ iff $l = \text{TRUE}$
- `NOT(l1, l2)`: $l_1 = \text{TRUE}$ iff $l_2 = \text{FALSE}$ and vice versa
- `MINUS(v1, v2)`: $v_1 = -v_2$
- `PLUS(v1, v2, ...)`: $\sum v_i = 0$
- `TIMES(v, v1, v2, ...)`: $v = \prod v_i$
- `DIVIDE(v, v1, v2)`: if $v_2 \neq 0$ then $v_1 = v \times v_2$
- `AND(l, l1, l2, ...)`: $l = \text{TRUE}$ iff all $l_i = \text{TRUE}$
- `OR(l, l1, l2, ...)`: $l = \text{TRUE}$ iff at least one $l_i = \text{TRUE}$
- `ONEOF(l, l1, l2, ...)`: $l = \text{TRUE}$ iff exactly one $l_i = \text{TRUE}$
- `ELEMENT(l, v, v1, v2, ...)`: equivalent to ONEOF + EQ combinations

### Key Design Decisions
- Consumers run exactly once, then are discarded (like compilation)
- Consumer may not have internal state or make control decisions
- All inferences recorded as ATMS justifications
- ATMS is neutral to search order (depth-first, breadth-first, or mixed)
- Control exercised only *before* running a consumer; once run, justifications are permanent

## Figures of Interest
- **Fig 1 (page 3/199):** Environment lattice for 5 assumptions {A,B,C,D,E} — shows all $2^5 = 32$ environments with nogoods crossed out and maximal consistent vertices boxed

## Results Summary
- The consumer architecture provides a clean separation between problem-solving logic and ATMS maintenance
- Scheduling by simplest-label-first finds solutions with near-minimum effort
- Dependency-directed backtracking via control disjunctions achieves at least the efficiency of chronological backtracking
- For problems with many solutions where all are needed: ATMS has inherent advantage (avoids all dependency-directed backtracking and context switching)
- For problems with one solution: advantage depends on whether dependency-directed backtracking cost exceeds ATMS overhead
- For problems with many solutions but few needed: requires careful use of control disjunctions to avoid exponential label growth

## Limitations
- ATMS is slower than conventional TMS for problems needing only one solution (due to database access overhead)
- Label sizes can grow exponentially ($2^{i+2} + 2^i$ environments for $i$-bit parity problem without control)
- No built-in support for time/action modeling (ATMS is purely inferential)
- Weak notion of control compared to Doyle's TMS data pool mechanism
- ONEOF implementation is quite complex
- Symbolic algebra for infinite-valued variables not fully addressed (only covers finite domains cleanly)

## Testable Properties
- Environment lattice has exactly $2^n$ vertices for $n$ assumptions
- A datum's label must be a subset of any of its environments
- If a context is inconsistent (nogood), no datum should be derivable in that context alone
- Consumers execute exactly once per node — rerunning produces no new justifications
- Constraint consumer $R_i^{-1}$ must satisfy: if $R(x_1, \ldots, x_n)$ holds and all $x_j$ ($j \neq i$) are known, then $x_i = R_i^{-1}(x_1, \ldots, x_{i-1}, x_{i+1}, \ldots, x_n)$
- Control disjunctions partition the search space: the next consistent current environment found is guaranteed consistent with all control disjunctions
- Parity problem with control: first solution found after creating $4i$ environments (linear), vs $2^{i+2} + 2^i$ without control (exponential)
- Adding arbitrary antecedents to a justification forces the ATMS to consider more contexts than intended (over-general labels if too few; inconsistent results if wrong antecedents)

## Relevance to Project
This paper is foundational for the propstore project's world model and assumption-based reasoning. The ATMS architecture directly maps to: environments as assumption sets, labels as minimal environments supporting a datum, nogoods as contradictory assumption sets, and consumers as forward-chaining rules. The constraint language (Section 5.3) provides a template for implementing numeric and logical constraints over ATMS-tracked variables. The control regime (Section 4) is directly applicable to the hypothetical world exploration in propstore.

## Open Questions
- [ ] How does the consumer architecture scale to very large numbers of assumptions (hundreds/thousands)?
- [ ] Can the constraint language be extended to support continuous/real-valued domains without symbolic algebra?
- [ ] What is the practical overhead of the ATMS label-update algorithm compared to incremental constraint propagation?
- [ ] How to model temporal actions within the purely inferential ATMS framework (Section 7.3)?

## Related Work Worth Reading
- de Kleer, J., "An assumption-based TMS", Artificial Intelligence 28 (1986) 127-162 [companion paper, defines the ATMS itself]
- de Kleer, J., "Extending the ATMS", Artificial Intelligence 28 (1986) 163-196 [extends ATMS with defaults, disjunctions, nonmonotonic justifications]
- Doyle, J., "A truth maintenance system", Artificial Intelligence 12 (1979) 231-272 [original TMS]
- McAllester, D., "A three-valued truth maintenance system" (1978) and "An outlook on truth maintenance" (1980) [RUP system]
- McDermott, D., "Contexts and data dependencies: a synthesis", IEEE Trans. PAMI 5(3) (1983) 237-246
- Martins, J.P. and Shapiro, S.C., "Reasoning in multiple belief spaces" (1983) [MBR]
- Williams, C., "ART the advanced reasoning tool" (1984) [proprietary]
- de Kleer, J. and Brown, J.S., "A qualitative physics based on confluences", Artificial Intelligence 24 (1984) 7-83
- Reiter, R., "A logic for default reasoning", Artificial Intelligence 13 (1980) 81-132
- Ginsberg, M.L., "Counterfactuals", Proc. IJCAI (1985) 107-110

## Collection Cross-References

### Already in Collection
- [[deKleer_1986_AssumptionBasedTMS]] — the foundational companion paper defining the ATMS itself (environments, labels, nogoods, contexts, label properties); this problem-solving paper builds the control regime and constraint language on top of that substrate

### Now in Collection (previously listed as leads)
- [[Doyle_1979_TruthMaintenanceSystem]] — The original justification-based TMS. Introduces SL/CP justifications, truth maintenance process, dependency-directed backtracking, and control patterns (defaults, sequences, equivalence classes) that this paper's consumer architecture and constraint language supersede. This paper compares the ATMS consumer approach favorably against Doyle's data pool mechanism for control.
- [[Reiter_1980_DefaultReasoning]] — Referenced as Reiter (1980); provides the formal framework for default reasoning that the ATMS supports computationally. Reiter's extensions (fixed-point belief sets under defaults) correspond to ATMS environments.

### New Leads (Not Yet in Collection)
- de Kleer (1986) — "Extending the ATMS" — extends the basic ATMS with default reasoning, disjunction axioms, nonmonotonic justifications

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- [[Dixon_1993_ATMSandAGM]] — the ATMS functional specification from this and the companion paper is what Dixon proves equivalent to AGM operations

### Conceptual Links (not citation-based)
- [[deKleer_1986_AssumptionBasedTMS]] — direct companion; this paper defines the problem-solving architecture, that paper defines the ATMS substrate it runs on
- [[deKleer_1984_QualitativePhysicsConfluences]] — **Strong.** The constraint language (PLUS, TIMES, AND, OR, ONEOF) directly generalizes the qualitative constraint satisfaction demonstrated in the qualitative physics paper. The consumer architecture mirrors ENVISION's component models.
