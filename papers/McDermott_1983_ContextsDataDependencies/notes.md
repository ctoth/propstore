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
AI programming languages like Conniver and QA4 had "contexts" (data pools) for maintaining multiple hypothetical database views, while newer "data dependency" systems (Doyle's TMS, de Kleer's assumptions) tracked reasons for beliefs. *(p.237)* These were treated as separate mechanisms with different tradeoffs: contexts offered fast switching but coarse-grained control, while dependencies offered fine-grained reason tracking but expensive status recomputation. *(p.237)* McDermott shows how to combine both into a single framework that preserves the advantages of each. *(p.237)*

## Key Contributions
- Defines **data pools** as pairs (b, S) where b is a bead (natural number) and S is a set of natural numbers, with operations for copying, pushing down, adding, and erasing assertions *(p.237)*
- Shows that data pools can be viewed as a special case of data dependencies by treating beads as premisses and labels as justifications *(p.240)*
- Introduces **in-justifiers** and **out-justifiers** as the two components of a justification tuple (in-justifiers, out-justifiers, justificand), replacing Doyle's support-list justifications *(p.239)*
- Defines **consistent** and **well-founded** status assignments for dependency networks in terms of Boolean label expressions rather than IN/OUT truth values *(p.241)*
- Presents a **Boolean substitution algorithm** for finding consistent, well-founded labelings by solving simultaneous Boolean equations *(p.241-242)*
- Proves the algorithm always halts and produces a well-founded labeling *(p.242)*
- Introduces the concept of **odd loops** (loops with an odd number of negative links) as the constraint that must be forbidden in dependency networks *(p.242)*
- Describes **blocking beads** and **latent assertions** as mechanisms for efficient deductive chaining across data pools *(p.243)*
- Introduces **signal functions** for communication between the knowledge-representation (KR) level and the data-dependency (DD) level *(p.240)*
- Reports performance benchmarks: approximately 0.3 ms per node for adding a justification, about 3 CONSes per node for the label computation *(p.244)*

## Methodology
The paper proceeds in four parts: (I) explains data pools and data dependencies separately, showing how each works and its tradeoffs *(pp.237-240)*; (II) shows how to combine them by treating labels as Boolean expressions over beads rather than simple IN/OUT values *(pp.240-242)*; (III) describes the actual implementation as a Boolean equation solver with forward chaining and back-substitution *(pp.243-244)*; (IV) discusses applications to temporal reasoning and chronset management *(pp.245-246)*. *(p.237)*

## Key Equations

The fundamental labeling equation for a node A with two beads b1, b2 in a simple network (Fig. 7):

$$
A = b1 \lor \sim B
$$

$$
B = b2 \lor \sim A
$$

Where A, B are assertions; b1, b2 are beads; the tilde (~) denotes negation; disjunction comes from multiple justifications. *(p.241)*

Substituting A from (1) into (2):

$$
B = b2 \lor \sim(b1 \lor \sim B) = b2 \lor (\sim b1 \land B)
$$

This has solution B = b2, giving A = b1 V ~b2 (the labeling in Fig. 7). *(p.242)*

General form for monotonic substitution: if A = f(A), then f can be put into disjunctive normal form:

$$
A = C_1 \lor C_2 \lor \cdots \lor C_n \lor D_1 \lor \cdots \lor D_m
$$

Where A occurs in D_i but not in C_i. By factoring out A's:

$$
A = C \lor (A \land D)
$$

This always has the solution A = C (the ouTest possible solution). *(p.242)*

Label equation for a network fragment (Fig. 9):

$$
A = b2 \lor (\sim b2 \land B)
$$

Which simplifies to:

$$
A = b2 \lor B
$$

*(p.241)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Nodes in benchmark | n | - | 200 | - | p.244 | Benchmark test network size |
| Time per justification add | - | ms | 0.3 | - | p.244 | Per node, on DEC 2060, ILISP |
| CONSes per node | - | - | 3 | - | p.244 | Average for label computation |
| Total CONSes | - | - | 606 | - | p.244 | Total for 200-node benchmark |
| CONSes reclaimed | - | - | 39 | - | p.244 | Reclaimed by garbage collection |
| CONSes per CONS (garbage) | - | - | 0.1 | ms | p.244 | ms per garbage collection per CONS |
| Supported nodes per justification | - | - | 99 | - | p.244 | Each node supports the next in chain |
| Total time for benchmark | - | ms | 65 | - | p.244 | Adding justification to node 0 |

## Implementation Details

### Data Structures
- **Bead**: a natural number serving as a unique identifier; bead 0 is used for values that are always IN *(p.237)*
- **Data pool**: a pair (b, S) where b is the characteristic bead and S is a set of natural numbers *(p.237)*
- **Assertion**: an identifiable datum with a label (Boolean expression over beads) and a set of justifications *(p.237)*
- **Justification**: a tuple (in-justifiers, out-justifiers, justificand) where in-justifiers and out-justifiers are sets of nodes *(p.239)*
- **Label**: a Boolean combination of beads, stored in disjunctive normal form as disjunctions of conjunctions of possibly-negated beads *(p.238)*
- **Gated list**: a list of heuristics gated by assertion labels; elements become actionable when their label becomes constant OUT *(p.245)*

### Algorithm: Boolean Substitution for Label Assignment
1. Sweep forward from any added or deleted justification *(p.243)*
2. Set labels of possibly-affected assertions to *UNKNOWN *(p.243)*
3. Sweep forward again, assigning labels *(p.243)*
4. If an assertion's label depends on another assertion whose label is not yet known, assign a provisional label containing the unknown assertion *(p.243)*
5. When a self-referential label A = f(A) is encountered, compute the new label as f(OUT) since f is monotonic *(p.242)*
6. Every time a label is assigned, substitute it into the labels of all assertions that depend on it *(p.241)*
7. Use back-substitution when arriving at a self-referential label *(p.242)*

### Key Properties of the Algorithm
- The algorithm always halts because every substitution eliminates one variable *(p.242)*
- The result is always a consistent, well-founded labeling *(p.242)*
- Worst-case complexity: n^2 substitutions (when every assertion is directly connected to every other) *(p.242)*
- Typical case: much better, since assertions usually have only one or two associated beads *(p.242)*
- Odd loops are forbidden; even loops always have consistent labelings *(p.242)*
- A loop is defined as a sequence of justifications (J_0, J_1, ..., J_{n-1}) such that the justificand of each J_i appears as a justifier of J_{i+1(mod n)} *(p.242)*
- A loop is *odd* if it contains an odd number of negative links (out-justifier appearances) *(p.242)*

### Subsumption Optimization
- Bead B1 subsumes B2 if B1 never occurs in a pool without B2 (because B1 was created by pushing from B2's pool) *(p.241)*
- When B1 subsumes B2, the label B1 V B2 simplifies to B2 *(p.241)*
- Boolean expression E1 *subsumes* E2 if for every valuation, either E1 is OUT in that valuation, or E2 is IN *(p.241)*
- This helps alleviate the exponential explosion when assertions have multiple proofs *(p.242)*

### Deductive Chaining
- Forward chaining: when A -> B are both asserted simultaneously, only some implications need marking *(p.243)*
- **Blocking beads**: attached to latent assertions, checked every time a bead enters or leaves a data pool *(p.243)*
- If a blocking bead's transition causes a latent assertion to become present, it is indexed and chained *(p.243)*
- Latent assertions are assertions whose labels evaluate to OUT in the current data pool; they are stored but not indexed *(p.243)*
- When a bead changes state, blocking beads check whether previously latent assertions should become active *(p.243)*

### Signal Functions
- Communication mechanism between the knowledge-representation (KR) level and the data-dependency (DD) level *(p.240)*
- The DD system signals the KR system when an assertion's status changes (IN to OUT or vice versa) *(p.240)*
- The KR system can respond by adding or removing justifications *(p.240)*
- This allows the two levels to interact without the DD system needing to understand the semantics of the KR system *(p.240)*

### Comparison with Doyle's TMS
- In Doyle's original algorithm, status assignments were never explicitly computed; they were determined directly from the justification set and recomputed every time the pool was switched *(p.241)*
- McDermott's version summarizes all status computations at once via Boolean labels *(p.241)*
- Doyle's algorithm handles well-founded support via a tree structure; McDermott's uses Boolean expressions over premisses and OUT assertions *(p.244)*
- McDermott argues the Boolean substitution approach is more efficient for the common case because an assertion's label tells its status in all data pools simultaneously *(p.241)*

## Figures of Interest
- **Fig. 1 (p.238):** Tree of data pools showing hierarchical pool structure with beads and assertions
- **Fig. 2 (p.239):** A simple data dependency with (ATTACK OPP K) -> (GOOD-MOVE (CASTLE K)) -> (NOT (ATTACK OPP K))
- **Fig. 3 (p.239):** A non-monotonic data dependency
- **Fig. 4 (p.240):** Data pool label as justification -- shows how bead membership is equivalent to a justification
- **Fig. 5 (p.240):** Data dependency simulation of a data pool
- **Fig. 6 (p.240):** Deductive chaining example across data pools
- **Fig. 7 (p.241):** A labeled dependency network combining beads and justifications
- **Fig. 8 (p.241):** Circular network example
- **Fig. 9 (p.241):** Network fragment used to derive label equations
- **Fig. 10 (p.242):** Odd loops -- shows why loops with odd numbers of negative links are problematic
- **Fig. 11 (p.242):** Large labels -- exponential growth example with 4 beads (a1-a4) supporting A and 4 beads (b1-b4) supporting B, producing labels with many disjuncts
- **Fig. 12 (p.243):** A worked example showing forward sweep and back-substitution

## Results Summary
- Implementation in ILISP on DEC 2060 achieves ~0.3 ms per node for adding a justification with 200-node networks *(p.244)*
- About 3 CONSes per node average for label computation (606 CONSes total, 39 reclaimed) *(p.244)*
- Garbage collection adds about 0.1 ms per CONS *(p.244)*
- Total time for the 200-node benchmark: approximately 65 ms *(p.244)*
- The algorithm handles both data pool switching and dependency maintenance in a unified framework *(p.241)*
- Applied to two domains: a rule-based AI language ("DUCK") and a temporal reasoning system with chronsets *(p.245)*

## Applications

### DUCK Language
- A rule-based AI programming language that uses data pools and dependencies *(p.245)*
- Rules are represented as latent assertions with blocking beads *(p.245)*
- Forward chaining deduction is integrated with the dependency system *(p.245)*

### Chronsets (Temporal Reasoning)
- A mechanism for managing multiple sets of a database chunked into temporal intervals *(p.245)*
- Each chronset represents a different temporal perspective *(p.245)*
- Data pools provide the mechanism for switching between temporal viewpoints *(p.245)*
- Gated lists are used to track which heuristics become applicable when temporal assertions change status *(p.245)*

## Arguments Against Prior Work

### Against Conniver/QA4 Data Pools *(p.237)*
- Data pools (contexts) offer only coarse-grained control: switching between pools is fast, but they provide no way to track *why* something is believed or to do fine-grained dependency management *(p.237)*
- Contexts had been neglected partly because they were supplemented by data dependencies, but neither alone provides adequate functionality *(p.237)*

### Against Doyle's TMS *(p.237, 239, 241, 244)*
- In Doyle's original algorithm, status assignments were never explicitly computed; they were determined directly from the justification set and had to be recomputed every time the pool was switched — the Boolean label approach summarizes all status computations simultaneously *(p.241)*
- Doyle's well-founded support tree structure is not necessary; the same information is captured in Boolean expressions over premisses and OUT assertions *(p.244)*
- Doyle's system does not provide a mechanism for efficiently managing multiple hypothetical database views (data pools); it focuses on single-context dependency tracking *(p.237)*

### Against Simple Forward Chaining *(p.243)*
- In a system with no data dependencies, forward chaining works trivially (if A and A->B are asserted, B is asserted). But in a data-pool system, dependencies create problems: an assertion can be indexed and still be OUT, and the generalized data-dependency system makes this more delicate since one can be removed from asserting an assertion by assigning it an IN or OUT status *(p.243)*
- The solution of waiting until at least one data pool indexes an assertion before doing further chaining is insufficient because assertions need blocking beads to track which pools they should become active in *(p.243)*

### Against Separate Treatment of Contexts and Dependencies *(p.237, 240)*
- The AI community had treated contexts and data dependencies as separate mechanisms with different tradeoffs, but McDermott shows they are actually the same mechanism: a bead in a data pool is equivalent to a premiss justification, and pool membership is equivalent to a dependency label *(p.240)*

## Design Rationale

### Why Boolean labels over beads *(p.241)*
Labels are Boolean combinations of beads (premisses) rather than simple IN/OUT truth values. This allows a single label to simultaneously encode an assertion's status in all possible data pools. The label tells you the assertion's status in any pool without recomputation. *(p.241)*

### Why disjunctive normal form *(p.238, 242)*
Labels are stored in disjunctive normal form (disjunctions of conjunctions of possibly-negated beads). This representation directly corresponds to the multiple justifications an assertion may have — each justification contributes one disjunct. The format also enables efficient subsumption checking. *(p.238)*

### Why forbid odd loops *(p.242)*
An odd loop (a cycle of justifications with an odd number of negative links) means an assertion's being OUT is sufficient reason for it to be IN, which is self-contradictory. Since finding a consistent labeling for networks with odd loops is NP-complete, the practical solution is to forbid them entirely. Even loops always have consistent labelings. *(p.242)*

### Why the outest (most OUT) solution *(p.242)*
When a self-referential equation A = f(A) has multiple solutions, the algorithm picks A = f(OUT) — the "outest" possible solution. This is the well-founded choice: an assertion should not be believed unless there is positive reason for it. The outest solution ensures no assertion is IN without grounded support. *(p.242)*

### Why signal functions between KR and DD levels *(p.240)*
The dependency system needs to communicate status changes to the knowledge-representation level without understanding KR semantics. Signal functions provide this decoupled interface: the DD system signals when an assertion changes status, and the KR system can respond by adding or removing justifications. This separation of concerns allows the same dependency machinery to serve different KR systems. *(p.240)*

### Why blocking beads and latent assertions *(p.243)*
Forward chaining across data pools creates a problem: assertions may need to be indexed in some pools but not others. Blocking beads are attached to "latent" (not-yet-indexed) assertions and checked every time a bead enters or leaves a data pool. When a blocking bead's transition causes a latent assertion to become present, it is indexed and forward chaining proceeds. This avoids the cost of eagerly computing all possible chains across all pools. *(p.243)*

### Why subsumption optimization *(p.241--242)*
When bead B1 is created by pushing from B2's pool, B1 subsumes B2 (B1 never occurs without B2). This means the label B1 V B2 simplifies to B2, helping prevent the exponential label growth that McAllester warned about (personal communication). In practice, most assertions are associated with only one or two beads, so the simplification keeps labels manageable. *(p.241--242)*

## Limitations
- Odd loops must be forbidden; if they exist, no consistent labeling is possible *(p.242)*
- Worst-case label size can grow exponentially (Fig. 11), though this is rare in practice *(p.242)*
- Assertions in multiple data pools create "cross-pool" dependency tracking challenges *(p.243)*
- The paper does not compute well-founded support in the sense of Doyle's original algorithm; labels can be justified ultimately in terms of premisses and OUT assertions, but the tree structure is not explicitly maintained *(p.244)*
- Chronset/temporal reasoning application is sketched but not fully worked out; details deferred to a later paper *(p.245)*
- McAllester has pointed out (personal communication) that in some circumstances the labels on assertions can grow exponentially with the depth of their well-founded support *(p.242)*

## Testable Properties
- Odd loops in a dependency network must prevent the algorithm from finding a consistent labeling *(p.242)*
- A = f(A) where f is monotonically increasing always has solution A = f(OUT) *(p.242)*
- Bead subsumption: if B1 is created by pushing from B2's pool, then B1 V B2 should simplify to B2 *(p.241)*
- Adding a justification to node 0 bringing 0-99 IN and sending 100-199 OUT should complete in ~65 ms on comparable hardware *(p.244)*
- The Boolean substitution algorithm should produce the same labelings as Doyle's TMS for networks without data pools *(p.244)*
- For a circular network (Fig. 8) with b1 and b2 both IN, A and B cannot both be OUT; the interesting case is when b1 and b2 are both OUT, selecting A to be IN and B OUT (or vice versa) *(p.241)*
- In the network of Fig. 9, A = b2 V (~b2 ^ B) simplifies to A = b2 V B *(p.241)*

## Relevance to Project
This paper is foundational for understanding how the propstore's data dependency and belief revision mechanisms should work. It provides the key insight that multiple "contexts" (data pools) and reason-tracking (dependencies) are the same mechanism, and gives an efficient algorithm for maintaining consistent labelings. The algorithm described here is a direct predecessor of de Kleer's ATMS and is relevant to the project's handling of multiple competing claim sets and belief revision across papers.

## Open Questions
- [ ] How does the chronset application relate to modern temporal reasoning systems?
- [ ] What is the exact relationship between McDermott's "labels" and de Kleer's "environments" in the ATMS?
- [ ] How does the subsumption optimization scale with many overlapping data pools?
- [ ] Can the blocking bead / latent assertion mechanism be applied to lazy evaluation of cross-paper claim dependencies?

## Related Work Worth Reading
- Doyle [5]: "A Truth Maintenance System" -- the original TMS that McDermott extends *(p.237)*
- de Kleer et al. [4]: "Explicit control of reasoning" -- early dependency-directed backtracking work *(p.237)*
- Charniak, Riesbeck, and McDermott [2]: "Artificial Intelligence Programming" -- textbook with data dependency implementation *(p.237)*
- McAllester [11]: "An outlook on truth maintenance" -- related approach to the same problems *(p.242)*
- Stallman and Sussman [19]: First to point out correspondence between beads/premisses and data pool labels *(p.240)*

## Collection Cross-References

### Already in Collection
- [[Doyle_1979_TruthMaintenanceSystem]] — cited as [5]; McDermott directly extends and synthesizes Doyle's data dependency framework with data pools (contexts).
- [[McAllester_1978_ThreeValuedTMS]] — cited as [11]; McAllester pointed out that labels can grow exponentially with depth of well-founded support, which McDermott's Boolean substitution algorithm addresses.

### New Leads (Not Yet in Collection)
- Stallman and Sussman (1977) — "Forward reasoning and dependency-directed backtracking" — first to identify correspondence between data pool beads and dependency premisses
- de Kleer, Doyle, Steele, and Sussman (1977) — "Explicit control of reasoning" — early dependency-directed backtracking

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- [[Martins_1983_MultipleBeliefSpaces]] — cited as [5]; referenced as an alternative approach to contextual reasoning
- [[Martins_1988_BeliefRevision]] — cited as [34]; McDermott's synthesis is referenced as an alternative multi-context approach

### Conceptual Links (not citation-based)
- [[deKleer_1986_AssumptionBasedTMS]] — **Strong.** McDermott's unified framework of data pools and dependencies is a direct precursor to the ATMS. McDermott's Boolean labels over beads anticipate the ATMS's labels as sets of environments. McDermott's beads correspond to ATMS assumptions, and his label computation algorithm is a precursor to ATMS label propagation. The ATMS generalizes McDermott's approach by maintaining all consistent environments simultaneously with formal minimality guarantees.
- [[Martins_1983_MultipleBeliefSpaces]] — **Moderate.** Both papers address multi-context reasoning: McDermott via data pools with Boolean labels, Martins via contexts (hypothesis sets) with restriction sets. Different mechanisms for the same problem of maintaining multiple hypothetical views of a knowledge base.
- [[Ginsberg_1985_Counterfactuals]] — **Moderate.** McDermott's data pools enable hypothetical reasoning by switching between contexts; Ginsberg formalizes counterfactual reasoning (what would be true if an assumption changed). McDermott provides the operational mechanism; Ginsberg provides the formal semantics for the kind of hypothetical reasoning data pools support.
