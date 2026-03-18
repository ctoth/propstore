---
title: "An Assumption-based TMS"
authors: "Johan de Kleer"
year: 1986
venue: "Artificial Intelligence"
doi_url: "https://doi.org/10.1016/0004-3702(86)90080-9"
---

# An Assumption-based TMS

## One-Sentence Summary
Defines the Assumption-based Truth Maintenance System (ATMS), a new TMS architecture that labels every datum with the sets of assumptions under which it holds, enabling simultaneous exploration of multiple problem-solving contexts without backtracking or retraction.

## Problem Addressed
Conventional justification-based TMSs (Doyle's TMS) maintain a single consistent database state, requiring expensive context switching, suffering from overzealous contradiction avoidance, experiencing the unouting problem, and being unable to compare multiple solutions simultaneously. These limitations make them poorly suited for tasks like differential diagnosis, qualitative reasoning, and constraint satisfaction where multiple hypothetical worlds must coexist.

## Key Contributions
- Introduces the **ATMS** as a fundamentally new kind of TMS that manipulates **assumption sets** rather than justifications alone
- Defines the core data structures: **nodes**, **assumptions**, **justifications**, **environments**, **labels**, **nogoods**, and **contexts**
- Establishes four key label properties: **consistency**, **soundness**, **completeness**, and **minimality**
- Shows how the ATMS eliminates context switching, backtracking, retraction, and the unouting problem
- Introduces **classes** as a mechanism for grouping nodes and encoding constraint-language variables
- Provides detailed **implementation guidance** using bit-vectors for environments, hash tables for subset tests, and three-cache optimization for environment unions
- Presents a complete comparison showing how the ATMS overcomes all seven limitations of conventional TMSs

## Methodology
The paper proceeds through:
1. **Motivation via search analysis** (Section 2): Shows four defects of chronological backtracking (futile backtracking, rediscovering contradictions, rediscovering inferences, incorrect ordering) and how dependency-directed backtracking partially addresses them
2. **Limitations of conventional TMSs** (Section 3): Catalogs seven specific problems (single-state, overzealous contradiction avoidance, switching states, dominance of justifications, cumbersome machinery, unouting, circular support)
3. **ATMS definition** (Section 4): Formal definitions of all data structures and algorithms
4. **Limitations removed** (Section 5): Shows how the ATMS resolves each limitation
5. **Implementation** (Section 6): Practical data structure and algorithm choices
6. **Summary** (Section 7): Four key ATMS properties

## Key Equations

Justification form (propositional Horn clause):

$$
x_1, x_2, \ldots \Rightarrow n
$$

Material implication interpretation:

$$
x_1 \wedge x_2 \wedge \cdots \rightarrow n
$$

Derivability condition (node n holds in environment E given justifications J):

$$
E, J \vdash n
$$

Inconsistency condition:

$$
E, J \vdash \perp
$$

Label soundness (for every environment E in n's label):

$$
J \vdash E \rightarrow n
$$

Label completeness (every consistent E for which J entails E->n is a superset of some label environment E'):

$$
E' \subseteq E
$$

Label update algorithm (complete label for consequent node n given justification k with antecedent labels j_ik):

$$
\bigcup_k \left\{ x \mid x = \bigcup_i x_i \text{ where } x_i \in j_{ik} \right\}
$$

In propositional form, a complete label is computed by converting the conjunction of disjunctions:

$$
\bigvee_k \bigwedge_i j_{ik}
$$

into disjunctive normal form, then removing inconsistent and subsumed environments.

## Parameters

| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|
| Number of assumptions | n | - | - | 1-1000+ | Practical ATMS handles n=1000 (2^1000 space) |
| Garbage collection threshold | - | % | 30 | - | ~30% of assumptions can typically be garbage collected |
| Nogood cache size threshold | - | assumptions | 3 | - | Nogoods of length 3+ cached per assumption |

## Implementation Details

### Core Data Structures

**ATMS Node** has five slots:
1. **Datum**: Problem solver's representation of the fact
2. **Label**: Set of environments (computed by ATMS, never modified by problem solver)
3. **Justifications**: List of derivations of the datum
4. **Consequents**: List of justifications where node is antecedent
5. **Contradictory**: Single bit indicating whether datum is contradictory

**Environment** has three additional slots beyond basic:
1. **Assumptions**: Set of assumptions defining it
2. **Nodes**: Set of nodes whose label mentions it
3. **Contradictory**: Single bit for inconsistency

**Justification** has three slots:
1. **Informant**: Problem-solver-supplied description of inference
2. **Consequent**: The node justified
3. **Antecedents**: List of nodes the inference depends on

### Four Node Types
1. **Premises**: Justification with no antecedents; label = {empty environment}; hold universally
2. **Assumptions**: Label contains singleton environment mentioning itself; notation: gamma_x for assumption associated with datum x
3. **Assumed nodes**: Neither premise nor assumption; justified under an assumption
4. **Derived nodes**: All other nodes; derived from justifications

### Bit-Vector Representation
- Each assumption assigned a unique bit position
- Environment = bit-vector of assumptions
- Union of environments = bitwise OR
- Subset test = (set1 AND NOT set2) == 0
- Hash table keyed by bit-vectors for O(1) environment lookup
- Nogood test via hash table of nogood bit-vectors

### Three-Cache Optimization for Environment Unions
When adding a single assumption to an environment:
1. **First cache**: Set of minimal nogoods of size >= 3 containing this assumption
2. **Second cache**: Bit-vector of assumptions inconsistent with this environment
3. **Third cache**: Each added assumption paired with resulting consistent environment
These three caches combined with the hash table make assumption addition very fast.

### Label Update Algorithm
1. For each new justification, compute cross-product of antecedent labels (union of one environment from each antecedent)
2. Remove inconsistent environments (check against nogood database)
3. Remove subsumed environments (any environment that is a superset of another in the label)
4. If new label differs from old, propagate to all consequent nodes
5. If node is gamma_perp, add new environments to nogood database and remove from all labels

### Retraction of Justifications
- Direct retraction is inefficient (isomorphic to LISP garbage collection)
- Preferred approach: conjoin extra "defeasability" assumption with justification
- To retract: contradict the conjoined assumption
- This avoids recursive label invalidation

### Assumption Garbage Collection
- An assumption can be garbage collected if all consequent nodes are true (hold universally) or false (contradictory)
- Or if the singleton environment containing the assumption is contradictory
- Typically ~30% of assumptions qualify
- Must integrate into justifications before collecting; problem solver must signal when collectible

## Figures of Interest
- **Fig 1 (page 15/141):** Reasoning system architecture — Problem Solver sends justifications to TMS, TMS returns beliefs
- **Fig 2 (page 23/149):** Environment lattice for assumptions {A, B, C, D, E} — shows how environments form a lattice with subset relationships, circled nodes = contexts of a particular datum, crossed-out nodes = nogoods and their supersets

## Results Summary
The ATMS:
- Handles n=1000 assumptions (2^1000 potential contexts) efficiently because only minimal environments are stored in labels
- Efficiency is proportional to number of environments actually considered, not total space size
- Most environments are inconsistent in practice, so label sizes remain manageable
- Three primitive operations: create node, create assumption, add justification
- Order-independent: results insensitive to order of assumption/justification introduction

## Limitations
- The ATMS is oriented toward finding ALL solutions; extra cost is incurred to find fewer solutions (opposite of conventional TMS tradeoff)
- Worst-case exponential in number of assumptions (2^n environments)
- Pathological cases exist where every possible environment is a minimal nogood or minimal label environment for some node
- Direct justification retraction is expensive; the defeasability-assumption workaround adds complexity
- Node-class framework, while convenient, is not logically necessary

## Testable Properties
- Label consistency: No environment in any node's label should be a superset of any nogood
- Label soundness: Every environment in a node's label must entail the node given the justifications
- Label completeness: Every consistent environment from which the node is derivable must be a superset of some label environment
- Label minimality: No environment in a label is a superset of another environment in the same label
- Nogoods are closed under subset: if {A,B} is nogood, {A,B,C} need not be stored (it's implied)
- Order independence: The same set of assumptions and justifications must produce the same labels regardless of introduction order
- Node categories partition: Every node is in exactly one of {true, in, out, false} sets; these are non-overlapping
- Bit-vector subset: For environments E1, E2 represented as bit-vectors, E1 subset of E2 iff (E1 AND NOT E2) == 0
- Assumption garbage: An assumption is collectible iff its singleton environment is nogood OR all its consequent nodes are true or false

## Relevance to Project
This is the foundational paper for the ATMS, which is the core inference substrate for the propstore's assumption-tracking, environment management, and hypothetical reasoning. Every concept introduced here (environments, labels, nogoods, contexts, label properties) is directly used in the propstore world model. The companion paper [8] (already in collection as deKleer_1986_ProblemSolvingATMS) builds the problem-solving architecture on top of this foundation.

## Open Questions
- [ ] How does the ATMS interact with probabilistic or graded assumptions (not addressed in this paper)?
- [ ] What are practical limits on number of assumptions before bit-vector operations become impractical?
- [ ] How does the three-cache optimization perform with very dense nogood sets?

## Collection Cross-References

### Already in Collection
- [[deKleer_1986_ProblemSolvingATMS]] — companion paper in same journal issue; builds the problem-solving architecture (consumers, scheduling, constraint language, control disjunctions) on top of the ATMS substrate defined here

### New Leads (Not Yet in Collection)
- Doyle (1979) — "A truth maintenance system" — the original justification-based TMS that the ATMS replaces
- de Kleer (1986) — "Extending the ATMS" — extends the basic ATMS with default reasoning, disjunction axioms, propositional expressions
- Reiter (1980) — "A logic for default reasoning" — formal framework for the kind of nonmonotonic reasoning the ATMS supports
- Stallman and Sussman (1977) — "Forward reasoning and dependency-directed backtracking" — early dependency tracking that the ATMS builds upon

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- [[deKleer_1986_ProblemSolvingATMS]] — references this as [8] throughout for ATMS definitions, label properties, and the problem-solver-TMS protocol

### Conceptual Links (not citation-based)
- [[deKleer_1986_ProblemSolvingATMS]] — direct companion; this paper defines the ATMS substrate, that paper defines the problem-solving architecture that runs on top of it

## Related Work Worth Reading
- Doyle [12]: Original justification-based TMS (the system the ATMS improves upon)
- de Kleer [7]: Extending the ATMS with propositional expressions (disjunction axioms)
- de Kleer [8]: Problem solving with the ATMS (companion paper, already in collection)
- Martins [13]: Reasoning in multiple belief spaces (related multi-context approach)
- Williams [22]: ART advanced reasoning tool (alternative architecture compared in paper)
- Stallman and Sussman [20]: Forward reasoning and dependency-directed backtracking (early dependency tracking)
- Reiter [18]: Default logic (formal framework for the kind of reasoning the ATMS supports)
