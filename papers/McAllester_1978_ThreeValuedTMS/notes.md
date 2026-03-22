---
title: "A Three Valued Truth Maintenance System"
authors: "David A. McAllester"
year: 1978
venue: "MIT AI Lab Memo 473"
doi_url: "https://dspace.mit.edu/handle/1721.1/6296"
institution: "MIT Artificial Intelligence Laboratory"
---

# A Three Valued Truth Maintenance System

## One-Sentence Summary
Presents a TMS where each proposition has three truth states (true, false, unknown) with relations in disjunctive clause form, enabling symmetric deduction of both truth values and their negations from the same clause, and providing dependency-directed backtracking over default assumptions without the non-monotonic dependency structures of Doyle's TMS. *(p.1)*

## Problem Addressed
Prior truth maintenance systems (Stallman and Sussman 1976, Doyle 1978a) used only two truth states ("in" and "out"), requiring separate entities for a proposition and its negation, and used non-monotonic dependency structures to handle assumptions and backtracking. *(p.3-4)* McAllester's system eliminates these complexities by introducing an explicit "unknown" third truth state and representing all relations as disjunctive clauses, which treats an implication's antecedent negation as deducible in exactly the same way as its consequent. *(p.3-4)*

## Key Contributions
- Three-valued truth states (true, false, unknown) for each proposition node, eliminating the need for separate negation nodes *(p.4)*
- Representation of all logical relations as disjunctive clauses in conjunctive normal form (CNF) *(p.3, 5)*
- Symmetric deduction: the same clause used to deduce a consequent can also deduce the negation of antecedents leading to contradictions *(p.3)*
- Contradiction detection and clause generation: when contradictions arise, new clauses are formed that encode the deductive path, enabling future avoidance *(p.9-11)*
- Default values and dependency-directed backtracking: assumptions are tagged as defaults and removed when they lead to contradictions, with the backtracking algorithm selecting the assumption with minimum maximum distance from the contradiction *(p.12-14)*
- Clause validity mechanism: clauses can be effectively removed by adding a validity node, avoiding physical deletion *(p.13)*
- Hierarchies of assumptions: assumptions can depend on other assumptions, enabling structured belief organization *(p.13)*

## Methodology
The system is implemented in Lisp (MACLISP) as a set of procedures that manage a database of TMS nodes, truth values, terms (associations of nodes with values), and clauses (disjunctive constraints). *(p.5, 25-30)* The algorithm operates incrementally: when a truth value is added or removed, only the affected clauses are examined for possible new deductions. *(p.6)* Contradictions trigger clause generation and backtracking. *(p.9-12)*

## Key Data Structures

### Node Properties
| Name | Symbol | Units | Default | Range | Notes | Page |
|------|--------|-------|---------|-------|-------|------|
| TRUTH | - | - | UNKNOWN | {TRUE, FALSE, UNKNOWN} | Three-valued truth state | p.22 |
| SUPPORT | - | - | NIL | premise / clause / NIL | What justified the current truth value | p.22 |
| POS-CLAUSES | - | - | NIL | list | Clauses containing this node positively | p.22 |
| NEG-CLAUSES | - | - | NIL | list | Clauses containing the negation of this node | p.22 |
| MAKE-TRUE | - | - | NIL | function / NIL | Callback when node becomes true | p.22 |
| MAKE-FALSE | - | - | NIL | function / NIL | Callback when node becomes false | p.22 |
| MAKE-UNK | - | - | NIL | function / NIL | Callback when node becomes unknown | p.22 |
| DEFAULT | - | - | NIL | {TRUE, FALSE, NIL} | If set, the node has a default truth value | p.22 |
| ASSERTION | - | - | - | atom | External assertion the node represents | p.22 |
| EXPLANATION | - | - | - | atom | Reason for belief (premise, clause ref, DEFAULT) | p.22 |

### Truth Value Atoms (TRUE and FALSE)
| Name | Property | Value | Notes | Page |
|------|----------|-------|-------|------|
| TRUE | OPPOSITE | FALSE | Symmetric pairing | p.22-23 |
| TRUE | CLAUSES | POS-CLAUSES | Which clause list to use | p.23 |
| TRUE | OP-CLAUSES | NEG-CLAUSES | Opposite clause list | p.23 |
| TRUE | EFFECT | MAKE-TRUE | Callback to invoke | p.23 |
| FALSE | OPPOSITE | TRUE | Symmetric pairing | p.23 |
| FALSE | CLAUSES | NEG-CLAUSES | Which clause list to use | p.23 |
| FALSE | OP-CLAUSES | POS-CLAUSES | Opposite clause list | p.23 |
| FALSE | EFFECT | MAKE-FALSE | Callback to invoke | p.23 |

### Clause Properties
| Name | Symbol | Units | Default | Range | Notes | Page |
|------|--------|-------|---------|-------|-------|------|
| CLAUSE-LIST | - | - | - | list of dotted pairs | (node . truth-value) pairs that make up the clause | p.23 |
| PSAT | - | - | - | integer | Count of nodes that could potentially satisfy the clause | p.23 |
| CLAUSE-NODE | - | - | - | node | A validity node; clause is active only when this node is TRUE | p.13, 23 |

### Global Variables
| Name | Symbol | Units | Default | Range | Notes | Page |
|------|--------|-------|---------|-------|-------|------|
| CONTRA-LIST | - | - | NIL | list | All clauses that are contradictions (PSAT = 0) | p.21, 23 |
| CONTRA-CLAUSE | - | - | NIL | clause | Used during contradiction resolution to construct new clauses | p.23 |
| CONTRA-SOURCE | - | - | NIL | clause | The contradiction that initialized new clause construction | p.23 |
| REMOVED-LIST | - | - | NIL | list | Tracks nodes whose truth values were removed during REMOVE-TRUTH | p.23 |
| ASSUM-LIST | - | - | NIL | alist | Assumptions underlying a contradiction, with maximum distances | p.24 |

## Implementation Details

### Core API (Appendix I)
1. `(TMS-INIT)` -- Initialize TMS data structures *(p.19)*
2. `(MAKE-DEPENDENCY-NODE assertion when-true when-false when-unknown)` -- Create a new TMS node with optional callbacks; returns an atom with ASSERTION property set; node is initially UNKNOWN *(p.19)*
3. `(SET-TRUTH node value reason)` -- Add a truth value; value must be TRUE or FALSE; reason is either PREMISE, DEFAULT, or a clause reference; errors if node is not UNKNOWN *(p.19)*
4. `(ADD-CLAUSE clause-list reason)` -- Add a disjunctive clause; clause-list is a list of (node . truth-value) dotted pairs; creates a clause node representing the clause's validity; if reason is DEFAULT the clause node gets a default true value *(p.20)*
5. `(REMOVE-TRUTH node)` -- Remove truth value, cascading to all critically dependent values; at the end, nodes with default values that were removed are re-checked for default re-assertion *(p.21)*
6. `(WHY object)` -- Explain justification for a node or clause; for nodes returns PREMISE or list of supporting nodes; for clauses returns the clause node then the nodes contained in the clause; clause nodes can be identified by ASSERTION property being CLAUSE *(p.21)*
7. `(BACKTRACK)` -- Resolve contradictions by removing default assumptions; uses FIND-ASSUM to trace WHY chains and find assumptions with maximum distances *(p.21)*

### Algorithm: Adding Truth Values (SET-TRUTH)
1. Verify node is currently UNKNOWN (error otherwise) *(p.6)*
2. Set node's TRUTH property to the value, record SUPPORT *(p.6)*
3. For each clause containing the term that just became FALSE, decrement PSAT *(p.6)*
4. For each clause where PSAT reaches 1 and there exists one UNKNOWN node, deduce that node's value (the only way to satisfy the clause) *(p.6)*
5. If PSAT reaches 0 for any clause, a contradiction has been found; add to CONTRA-LIST *(p.6)*
6. If the node has an EFFECT callback, apply it *(p.6)*
7. Recursively check for further one-step deductions via DEDUCE-CHECK *(p.6)*

### Algorithm: Removing Truth Values (REMOVE-TRUTH)
1. Set node to UNKNOWN, clear SUPPORT *(p.7, 9)*
2. For each clause containing the term that was FALSE, increment PSAT (it can now potentially satisfy the clause again) *(p.9)*
3. Remove truth values of nodes that critically depended on this one (those whose SUPPORT clause used this value) *(p.7-8)*
4. After all removals, for nodes on the REMOVED-LIST that now have default values but no other truth value, re-check if the default can be re-asserted *(p.7, 21)*
5. After removal cascade, check for new deductions from clauses containing the newly-UNKNOWN terms *(p.8-9)*

### Algorithm: Contradiction Handling
1. A contradiction occurs when a clause has PSAT = 0 (all terms are false) *(p.9)*
2. Contradictions can only arise from the addition of truth values, not from clause addition alone (since in a quiescent state all possible one-step deductions have been made) *(p.9-10)*
3. When a truth value is added that causes a contradiction in clause C1, the term F1 that became true and F2 (the opposite value deducible from C1) together with F1's supporting clause yield a new clause: the resolvent *(p.10)*
4. The new clause is formed by the MERGE function: combining the terms of the contradicting clause and the supporting clause, excluding the two resolved terms *(p.10-11)*
5. The new clause is added, potentially enabling deduction of the negation of whatever caused the contradiction *(p.10-12)*
6. If the new clause itself becomes a contradiction (all its terms are false), the process repeats recursively *(p.10-11)*

### Algorithm: Backtracking (BACKTRACK)
1. If CONTRA-LIST is empty, return T (no contradictions) *(p.12)*
2. For each contradiction, call WHY to find the assumptions (nodes with DEFAULT support) that the contradiction depends on *(p.12)*
3. Collect assumptions with their maximum distance from the contradiction (number of clauses in the support chain) *(p.13-14)*
4. Select the assumption with the minimum maximum distance *(p.13-14)*
5. Call REMOVE-TRUTH on that assumption *(p.12)*
6. The contradicting clause can now be used to deduce the negation of the default value *(p.12)*
7. Repeat until no contradictions remain or no assumptions are left *(p.12-13)*

### Key Design Decisions
- **One-step clause deductions only**: to avoid NP-complete satisfiability checking, only deductions from a single clause (when PSAT = 1) are performed. Multi-clause resolution is not attempted. *(p.7)*
- **Clause representation eliminates antecedent/consequent distinction**: P1 ^ P2 ^ P3 -> Q is stored as (-P1 v -P2 v -P3 v Q), making negation deduction natural. *(p.3, 5)*
- **DeMorgan transformation for mutual exclusion**: -(P1 ^ P2 ^ ... ^ Pn) becomes (-P1 v -P2 v ... v -Pn), which is a single clause. *(p.4)*
- **Support tracing is well-founded**: supports are always premises or clauses, never circular. Since support is assigned when a truth value is added, and truth values can only be added to UNKNOWN nodes, the support chain cannot loop. *(p.7-8)*
- **Clause validity nodes**: rather than physically deleting clauses, a validity node is added; setting it false effectively removes the clause. This also serves as a provenance device for tracking clause origins. *(p.13)*
- **Assumption hierarchies via clause validity**: the dog/mammal example shows how clause (A1 -> A2) with a default clause node allows A2 to be assumed only if A1 is believed, and both can be retracted during backtracking. *(p.13)*
- **Minimum maximum distance heuristic for backtracking**: choosing the closest assumption to the contradiction ensures that implied assumptions (further away in the support chain) are retracted before the assumptions they depend on. *(p.13-14)*

### Additional Implementation Details from Appendix III
- **CLAUSE-RESOLUTION**: when a contradiction is detected during SET-TRUTH (CONTRA-SOURCE is non-nil), the system calls ADD-2 with reason CLAUSE-RESOLUTION to generate a new clause by merging the contradicting clause with the clause that supported the added truth value *(p.28)*
- **SET-2**: the internal version of SET-TRUTH that handles both premise-based and clause-based truth value addition, and drives the recursive deduction and contradiction detection *(p.28)*
- **SATISFY**: a utility function that sets all nodes without truth values to their default values using SET-TRUTH with DEFAULT reason *(p.30)*
- **NODE-DEDUCE-CHECK**: after REMOVE-TRUTH, checks both POS-CLAUSES and NEG-CLAUSES of the removed node for possible new deductions *(p.29)*
- **CONSEQ** (in REMOVE-TRUTH code): finds a node in the clause that satisfies the clause (has the required truth value), used to identify candidates for removal *(p.29)*

## Figures of Interest
- **Fig 1 (p.11):** Example of clause formation from a contradiction. Shows how addition of -A causes C3 to become a contradiction, leading to the new clause (B ^ D ^ F) -> A. The diagram shows three clauses: (-A ^ B) -> C, (C ^ D) -> E, and (-A ^ F) -> -E, with the contradiction yielding the resolvent.
- **Fig 2 (p.11):** General case of clause formation resulting from a contradiction. Shows the abstract case where the addition of -F2 causes C1 to become a contradiction, producing a new clause from the resolvent of C1 and the supporting clauses. Uses notation F_i^{C_j} to denote the terms of each clause.

## Results Summary
The system is demonstrated to handle:
- Incremental truth maintenance with three-valued logic *(p.3, 5-6)*
- Automatic contradiction detection and resolution *(p.9-12)*
- Dependency-directed backtracking that avoids chronological backtracking *(p.3, 12-14)*
- Default reasoning with assumption hierarchies *(p.12-13)*
- The system was designed for use in electronic circuit analysis applications (Stallman and Sussman 1976) *(p.3)*

## Limitations
- Only one-step clause deductions are performed (no multi-clause resolution), which may miss some valid inferences *(p.7)*
- Contradiction resolution via new clause generation can sometimes "pulse" -- repeatedly adding and retracting the same value before stabilizing, though the author states this would require a quite complex structure and at most one or two pulses *(p.12)*
- No conditional proof mechanism is implemented (unlike Doyle's TMS which uses conditional proofs for condensed explanations); McAllester explicitly states he had no application to justify implementing it *(p.16-17)*
- The backtracking heuristic (minimum maximum distance) is simple and may not always choose the optimal assumption to retract *(p.13-14)*
- Because no specific set of assumptions is chosen to blame for a contradiction, new assumptions leading to old contradictions can be proven false, but the number of such extra contradictions is small compared to dependency-directed backtracking savings *(p.16)*

## Comparison with Other Work

### vs. Stallman and Sussman ARS (1976)
- ARS has two truth states ("believed" and "unknown"), needs separate mechanism (NOGOOD assertions) to prevent contradictory assumption sets from being re-believed *(p.15)*
- McAllester's three-valued system handles this naturally through clause-based contradiction resolution *(p.15-16)*

### vs. Doyle's TMS (1978a)
- Doyle's TMS has two truth states ("in" and "out"), requires two TMS nodes per assertion (one for the assertion, one for its negation) *(p.15)*
- Doyle uses non-monotonic dependency structure: truth of a node can depend on another node being unknown (i.e., "out") *(p.16)*
- Doyle's contradiction handling requires separate contradiction nodes with justifications implying mutual exclusion for each pair of nodes *(p.15)*
- Doyle implements conditional proof (CP): a mechanism where C -> (A^B -> D) can be condensed, useful for explanation but computationally expensive to verify *(p.15-16)*
- McAllester's system achieves similar non-monotonic power through defaults and clause-based contradiction resolution without non-monotonic dependencies *(p.16)*
- McAllester's contradiction is simply a clause that cannot be satisfied (PSAT=0), which directly allows deduction of opposite truth values; this is "the tremendous conceptual and programming simplicity advantage of this system" *(p.16)*

## Testable Properties
- A node's TRUTH value is always one of {TRUE, FALSE, UNKNOWN} *(p.5, 22)*
- A node can never transition directly from TRUE to FALSE or vice versa; it must pass through UNKNOWN *(p.5, 19)*
- When a clause has PSAT = 0, it must appear on CONTRA-LIST *(p.9, 21)*
- When a clause has PSAT = 1 and the remaining unknown node exists, a deduction must occur *(p.6)*
- SUPPORT for a truth value is always well-founded (traceable to premises without cycles) *(p.7-8)*
- Removing a truth value must also remove all truth values that critically depend on it *(p.7-8)*
- After BACKTRACK completes, either CONTRA-LIST is empty or no default assumptions remain *(p.12-13)*
- Adding a clause with PSAT = 0 immediately triggers contradiction handling *(p.27)*
- The clause (node . value) representation satisfies: if all terms are false except one unknown, that unknown term's value is deducible *(p.6)*
- Truth values deduced from clauses can only be removed by removing the premises or clauses from which they were deduced, not directly by the TMS user *(p.21)*
- A clause node is always given a true truth value with PREMISE support upon creation; its ASSERTION property is CLAUSE *(p.20, 27)*

## Relevance to Project
This paper is the "RUP" (Reason, Unknown, Premiss) system referenced in de Kleer's 1986 ATMS papers. It represents an intermediate step between Doyle's original TMS (1979) and de Kleer's ATMS (1986). Key concepts that carry forward to the ATMS include: clause-based representation of justifications, support tracing for explanations, and contradiction-driven constraint propagation. The three-valued approach is simpler than Doyle's two-valued system with separate negation nodes, though de Kleer's ATMS takes a fundamentally different approach by tracking assumption sets (environments) rather than maintaining a single consistent state.

## Open Questions
- [ ] How does the "pulsing" behavior during contradiction resolution compare to the ATMS's label update mechanism?
- [ ] Could the clause-generation mechanism from contradictions be adapted for the propstore's constraint system?
- [ ] What is the empirical computational cost of the one-step-only restriction vs. full resolution?

## Related Work Worth Reading
- McAllester, D. (1980) "An Outlook on Truth Maintenance" -- MIT AI Memo 551, the more mature follow-up
- Stallman and Sussman (1976) "Forward Reasoning and Dependency Directed Backtracking in a System for Computer Aided Circuit Analysis" -- the ARS system this TMS was designed to support *(p.18)*
- de Kleer, Doyle, Steele, and Sussman (1977) "Explicit Control of Reasoning" -- the AMORD system *(p.18)*
- Doyle (1978a) "Truth Maintenance Systems for Problem Solving" -- MIT AI Lab TR-419 *(p.18)*
- Doyle (1978b) "A Glimpse of Truth Maintenance" -- MIT AI Memo 461 *(p.18)*
- McDermott (1976) "Flexibility and Efficiency in a Computer System for Designing Circuits" -- MIT AI Lab TR-402 *(p.18)*
- Sussman (1977) "Slices: At the Boundary Between Analysis and Synthesis" -- MIT AI Lab Memo 433 *(p.18)*

## Collection Cross-References

### Already in Collection
- [[Doyle_1979_TruthMaintenanceSystem]] -- cited as [Doyle 1978a]; the primary comparison point. McAllester's system is designed as a simpler alternative to Doyle's TMS, using three-valued logic and clauses instead of two-valued logic with SL/CP justifications and non-monotonic dependencies. *(p.15-17)*
- [[deKleer_1986_ProblemSolvingATMS]] -- cites this paper as the "RUP" system; compares ATMS consumer architecture against McAllester's clause-based approach. The ATMS supersedes this TMS by tracking multiple assumption sets simultaneously.
- [[deKleer_1986_AssumptionBasedTMS]] -- cites this paper [14] as part of the TMS lineage; the ATMS addresses limitations of both Doyle's and McAllester's approaches by maintaining all consistent contexts simultaneously.

### New Leads (Not Yet in Collection)
- Stallman and Sussman (1976) -- "Forward Reasoning and Dependency Directed Backtracking" -- the ARS system; primary application domain for this TMS *(p.18)*
- de Kleer, Doyle, Steele, and Sussman (1977) -- "Explicit Control of Reasoning" -- AMORD system *(p.18)*

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- [[Doyle_1979_TruthMaintenanceSystem]] -- cites McAllester [30] as an alternative TMS design with cleaner organization
- [[deKleer_1986_ProblemSolvingATMS]] -- cites this as [14], the RUP system, in comparison of TMS architectures
- [[deKleer_1986_AssumptionBasedTMS]] -- cites this as [14] in the lineage of truth maintenance systems
- [[Martins_1983_MultipleBeliefSpaces]] -- cites as [4]; referenced as a prior approach to contradiction handling
- [[Martins_1988_BeliefRevision]] -- cites as [31]; part of the TMS lineage that MBR/SWM improves upon
- [[Falkenhainer_1987_BeliefMaintenanceSystem]] -- cites McAllester 1980 (Reasoning Utility Package); BMS rule engine builds on McAllester's pattern-matching
- [[McDermott_1983_ContextsDataDependencies]] -- cites as [11]; McAllester pointed out that labels can grow exponentially
- [[Shapiro_1998_BeliefRevisionTMS]] -- surveys this as the LTMS architecture with three-valued clause-based labeling

### Conceptual Links (not citation-based)
- [[Doyle_1979_TruthMaintenanceSystem]] -- Strong: both papers solve the same core problem (maintaining consistent beliefs under contradiction) with fundamentally different architectures. Doyle uses two-valued SL/CP justifications with non-monotonic dependencies; McAllester uses three-valued clausal representation. McAllester's clause-based contradiction resolution (generating new clauses from contradictions) is a precursor to the ATMS's nogood management. Key difference: McAllester eliminates non-monotonic dependencies but loses conditional proofs.
- [[deKleer_1986_AssumptionBasedTMS]] -- Strong: the ATMS can be seen as the natural evolution of McAllester's ideas. McAllester's clause representation and symmetric deduction anticipate the ATMS's justification-based label propagation. The ATMS's key innovation (maintaining all consistent environments simultaneously rather than a single state) directly addresses the limitation that McAllester's system still maintains only one consistent state at a time.
- [[deKleer_1986_ProblemSolvingATMS]] -- Strong: this paper's default backtracking algorithm (selecting assumptions by distance from contradiction) is the precursor to the ATMS's dependency-directed backtracking via nogoods and control disjunctions. The ATMS problem-solving paper explicitly compares against McAllester's RUP system.
