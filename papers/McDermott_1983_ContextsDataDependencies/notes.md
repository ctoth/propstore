---
title: "Contexts and Data Dependencies: A Synthesis"
authors: "Drew McDermott"
year: 1983
venue: "IEEE Transactions on Pattern Analysis and Machine Intelligence"
doi_url: "https://doi.org/10.1109/TPAMI.1983.4767388"
pages: "237-246"
institution: "Department of Computer Science, Yale University"
---

# Contexts and Data Dependencies: A Synthesis

## One-Sentence Summary
Unifies two AI data-organization mechanisms -- data pools (contexts) and data dependencies -- by showing that data pools can be implemented as a special case of dependency networks, and presents an efficient Boolean-equation-based algorithm for computing consistent, well-founded status assignments in the combined system.

## Problem Addressed
AI programming languages like Conniver and QA4 had "contexts" (data pools) for maintaining multiple hypothetical database views, while newer "data dependency" systems (Doyle's TMS, de Kleer's assumptions) tracked reasons for beliefs. These were treated as separate mechanisms with different tradeoffs: contexts offered fast switching but coarse-grained control, while dependencies offered fine-grained reason tracking but expensive status recomputation. McDermott shows how to combine both into a single framework that preserves the advantages of each.

## Key Contributions
- Defines **data pools** as pairs (b, S) where b is a bead (natural number) and S is a set of natural numbers, with operations for copying, pushing down, adding, and erasing assertions
- Shows that data pools can be viewed as a special case of data dependencies by treating beads as premisses and labels as justifications
- Introduces **in-justifiers** and **out-justifiers** as the two components of a justification tuple (in-justifiers, out-justifiers, justificand), replacing Doyle's support-list justifications
- Defines **consistent** and **well-founded** status assignments for dependency networks in terms of Boolean label expressions rather than IN/OUT truth values
- Presents a **Boolean substitution algorithm** for finding consistent, well-founded labelings by solving simultaneous Boolean equations
- Proves the algorithm always halts and produces a well-founded labeling
- Introduces the concept of **odd loops** (loops with an odd number of negative links) as the constraint that must be forbidden in dependency networks
- Describes **blocking beads** and **latent assertions** as mechanisms for efficient deductive chaining across data pools
- Introduces **signal functions** for communication between the knowledge-representation (KR) level and the data-dependency (DD) level
- Reports performance benchmarks: approximately 0.3 ms per node for adding a justification, about 3 CONSes per node for the label computation

## Methodology
The paper proceeds in four parts: (I) explains data pools and data dependencies separately, showing how each works and its tradeoffs; (II) shows how to combine them by treating labels as Boolean expressions over beads rather than simple IN/OUT values; (III) describes the actual implementation as a Boolean equation solver with forward chaining and back-substitution; (IV) discusses applications to temporal reasoning and chronset management.

## Key Equations

The fundamental labeling equation for a node A with two beads b1, b2 in a simple network (Fig. 7):

$$
A = b1 \lor \sim B
$$

$$
B = b2 \lor \sim A
$$

Where A, B are assertions; b1, b2 are beads; the tilde (~) denotes negation; disjunction comes from multiple justifications.

Substituting A from (1) into (2):

$$
B = b2 \lor \sim(b1 \lor \sim B) = b2 \lor (\sim b1 \land B)
$$

This has solution B = b2, giving A = b1 V ~b2 (the labeling in Fig. 7).

General form for monotonic substitution: if A = f(A), then f can be put into disjunctive normal form:

$$
A = C_1 \lor C_2 \lor \cdots \lor C_n \lor D_1 \lor \cdots \lor D_m
$$

Where A occurs in D_i but not in C_i. By factoring out A's:

$$
A = C \lor (A \land D)
$$

This always has the solution A = C (the ouTest possible solution).

Label equation for a network fragment (Fig. 9):

$$
A = b2 \lor (\sim b2 \land B)
$$

Which simplifies to:

$$
A = b2 \lor B
$$

## Parameters

| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|
| Nodes in benchmark | n | - | 200 | - | Benchmark test network size |
| Time per justification add | - | ms | 0.3 | - | Per node, on DEC 2060, ILISP |
| CONSes per node | - | - | 3 | - | Average for label computation |
| CONSes per CONS (garbage) | - | - | 0.1 | - | ms per garbage collection per CONS |
| Supported nodes per justification | - | - | 99 | - | Each node supports the next in chain |

## Implementation Details

### Data Structures
- **Bead**: a natural number serving as a unique identifier; bead 0 is used for values that are always IN
- **Data pool**: a pair (b, S) where b is the characteristic bead and S is a set of natural numbers
- **Assertion**: an identifiable datum with a label (Boolean expression over beads) and a set of justifications
- **Justification**: a tuple (in-justifiers, out-justifiers, justificand) where in-justifiers and out-justifiers are sets of nodes
- **Label**: a Boolean combination of beads, stored in disjunctive normal form as disjunctions of conjunctions of possibly-negated beads
- **Gated list**: a list of heuristics gated by assertion labels; elements become actionable when their label becomes constant OUT

### Algorithm: Boolean Substitution for Label Assignment
1. Sweep forward from any added or deleted justification
2. Set labels of possibly-affected assertions to *UNKNOWN
3. Sweep forward again, assigning labels
4. If an assertion's label depends on another assertion whose label is not yet known, assign a provisional label containing the unknown assertion
5. When a self-referential label A = f(A) is encountered, compute the new label as f(OUT) since f is monotonic
6. Every time a label is assigned, substitute it into the labels of all assertions that depend on it
7. Use back-substitution when arriving at a self-referential label

### Key Properties of the Algorithm
- The algorithm always halts because every substitution eliminates one variable
- The result is always a consistent, well-founded labeling
- Worst-case complexity: n^2 substitutions (when every assertion is directly connected to every other)
- Typical case: much better, since assertions usually have only one or two associated beads
- Odd loops are forbidden; even loops always have consistent labelings

### Subsumption Optimization
- Bead B1 subsumes B2 if B1 never occurs in a pool without B2 (because B1 was created by pushing from B2's pool)
- When B1 subsumes B2, the label B1 V B2 simplifies to B2
- This helps alleviate the exponential explosion when assertions have multiple proofs

### Deductive Chaining
- Forward chaining: when A -> B are both asserted simultaneously, only some implications need marking
- **Blocking beads**: attached to latent assertions, checked every time a bead enters or leaves a data pool
- If a blocking bead's transition causes a latent assertion to become present, it is indexed and chained

## Figures of Interest
- **Fig. 1 (page 238):** Tree of data pools showing hierarchical pool structure with beads and assertions
- **Fig. 2 (page 239):** A simple data dependency with (ATTACK OPP K) -> (GOOD-MOVE (CASTLE K)) -> (NOT (ATTACK OPP K))
- **Fig. 3 (page 239):** A non-monotonic data dependency
- **Fig. 4 (page 240):** Data pool label as justification -- shows how bead membership is equivalent to a justification
- **Fig. 5 (page 240):** Data dependency simulation of a data pool
- **Fig. 7 (page 241):** A labeled dependency network combining beads and justifications
- **Fig. 8 (page 241):** Circular network example
- **Fig. 9 (page 241):** Network fragment used to derive label equations
- **Fig. 10 (page 242):** Odd loops -- shows why loops with odd numbers of negative links are problematic
- **Fig. 11 (page 242):** Large labels -- exponential growth example
- **Fig. 12 (page 243):** A worked example showing forward sweep and back-substitution

## Results Summary
- Implementation in ILISP on DEC 2060 achieves ~0.3 ms per node for adding a justification with 200-node networks
- About 3 CONSes per node average for label computation (6 CONS cells total, 39 reclaimed)
- Garbage collection adds about 0.1 ms per CONS
- The algorithm handles both data pool switching and dependency maintenance in a unified framework
- Applied to two domains: a rule-based AI language ("DUCK") and a temporal reasoning system with chronsets

## Limitations
- Odd loops must be forbidden; if they exist, no consistent labeling is possible
- Worst-case label size can grow exponentially (Fig. 11), though this is rare in practice
- Assertions in multiple data pools create "cross-pool" dependency tracking challenges
- The paper does not compute well-founded support in the sense of Doyle's original algorithm; labels can be justified ultimately in terms of premisses and OUT assertions, but the tree structure is not explicitly maintained
- Chronset/temporal reasoning application is sketched but not fully worked out; details deferred to a later paper

## Testable Properties
- Odd loops in a dependency network must prevent the algorithm from finding a consistent labeling
- A = f(A) where f is monotonically increasing always has solution A = f(OUT)
- Bead subsumption: if B1 is created by pushing from B2's pool, then B1 V B2 should simplify to B2
- Adding a justification to node 0 bringing 0-99 IN and sending 100-199 OUT should complete in ~65 ms on comparable hardware
- The Boolean substitution algorithm should produce the same labelings as Doyle's TMS for networks without data pools

## Relevance to Project
This paper is foundational for understanding how the propstore's data dependency and belief revision mechanisms should work. It provides the key insight that multiple "contexts" (data pools) and reason-tracking (dependencies) are the same mechanism, and gives an efficient algorithm for maintaining consistent labelings. The algorithm described here is a direct predecessor of de Kleer's ATMS and is relevant to the project's handling of multiple competing claim sets and belief revision across papers.

## Open Questions
- [ ] How does the chronset application relate to modern temporal reasoning systems?
- [ ] What is the exact relationship between McDermott's "labels" and de Kleer's "environments" in the ATMS?
- [ ] How does the subsumption optimization scale with many overlapping data pools?
- [ ] Can the blocking bead / latent assertion mechanism be applied to lazy evaluation of cross-paper claim dependencies?

## Related Work Worth Reading
- Doyle [5]: "A Truth Maintenance System" -- the original TMS that McDermott extends
- de Kleer et al. [4]: "Explicit control of reasoning" -- early dependency-directed backtracking work
- Charniak, Riesbeck, and McDermott [2]: "Artificial Intelligence Programming" -- textbook with data dependency implementation
- McAllester [11]: "An outlook on truth maintenance" -- related approach to the same problems
- Stallman and Sussman [19]: First to point out correspondence between beads/premisses and data pool labels
