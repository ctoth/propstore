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
Presents a TMS where each proposition has three truth states (true, false, unknown) with relations in disjunctive clause form, enabling symmetric deduction of both truth values and their negations from the same clause, and providing dependency-directed backtracking over default assumptions without the non-monotonic dependency structures of Doyle's TMS.

## Problem Addressed
Prior truth maintenance systems (Stallman and Sussman 1976, Doyle 1978a) used only two truth states ("in" and "out"), requiring separate entities for a proposition and its negation, and used non-monotonic dependency structures to handle assumptions and backtracking. McAllester's system eliminates these complexities by introducing an explicit "unknown" third truth state and representing all relations as disjunctive clauses, which treats an implication's antecedent negation as deducible in exactly the same way as its consequent.

## Key Contributions
- Three-valued truth states (true, false, unknown) for each proposition node, eliminating the need for separate negation nodes
- Representation of all logical relations as disjunctive clauses in conjunctive normal form (CNF)
- Symmetric deduction: the same clause used to deduce a consequent can also deduce the negation of antecedents leading to contradictions
- Contradiction detection and clause generation: when contradictions arise, new clauses are formed that encode the deductive path, enabling future avoidance
- Default values and dependency-directed backtracking: assumptions are tagged as defaults and removed when they lead to contradictions, with the backtracking algorithm selecting the assumption with minimum maximum distance from the contradiction
- Clause validity mechanism: clauses can be effectively removed by adding a validity node, avoiding physical deletion
- Hierarchies of assumptions: assumptions can depend on other assumptions, enabling structured belief organization

## Methodology
The system is implemented in Lisp (MACLISP) as a set of procedures that manage a database of TMS nodes, truth values, terms (associations of nodes with values), and clauses (disjunctive constraints). The algorithm operates incrementally: when a truth value is added or removed, only the affected clauses are examined for possible new deductions. Contradictions trigger clause generation and backtracking.

## Key Data Structures

### Node Properties
| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|
| TRUTH | - | - | UNKNOWN | {TRUE, FALSE, UNKNOWN} | Three-valued truth state |
| SUPPORT | - | - | NIL | premise / clause / NIL | What justified the current truth value |
| POS-CLAUSES | - | - | NIL | list | Clauses containing this node positively |
| NEG-CLAUSES | - | - | NIL | list | Clauses containing the negation of this node |
| MAKE-TRUE | - | - | NIL | function / NIL | Callback when node becomes true |
| MAKE-FALSE | - | - | NIL | function / NIL | Callback when node becomes false |
| MAKE-UNK | - | - | NIL | function / NIL | Callback when node becomes unknown |
| DEFAULT | - | - | NIL | {TRUE, FALSE, NIL} | If set, the node has a default truth value |
| ASSERTION | - | - | - | atom | External assertion the node represents |
| EXPLANATION | - | - | - | atom | Reason for belief (premise, clause ref, DEFAULT) |

### Clause Properties
| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|
| CLAUSE-LIST | - | - | - | list of dotted pairs | (node . truth-value) pairs that make up the clause |
| PSAT | - | - | - | integer | Count of nodes that could potentially satisfy the clause |
| CLAUSE-NODE | - | - | - | node | A validity node; clause is active only when this node is TRUE |

### Global Variables
| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|
| CONTRA-LIST | - | - | NIL | list | All clauses that are contradictions (PSAT = 0) |
| CONTRA-CLAUSE | - | - | NIL | clause | Used during contradiction resolution |
| CONTRA-SOURCE | - | - | NIL | clause | The contradiction that triggered new clause construction |
| REMOVED-LIST | - | - | NIL | list | Tracks nodes whose truth values were removed during REMOVE-TRUTH |
| ASSUM-LIST | - | - | NIL | alist | Assumptions underlying a contradiction, with distances |

## Implementation Details

### Core API (Appendix I)
1. `(TMS-INIT)` -- Initialize TMS data structures
2. `(MAKE-DEPENDENCY-NODE assertion when-true when-false when-unknown)` -- Create a new TMS node with optional callbacks
3. `(SET-TRUTH node value reason)` -- Add a truth value; value must be TRUE or FALSE; reason is either PREMISE, DEFAULT, or a clause reference
4. `(ADD-CLAUSE clause-list reason)` -- Add a disjunctive clause; clause-list is a list of (node . truth-value) dotted pairs
5. `(REMOVE-TRUTH node)` -- Remove truth value, cascading to all critically dependent values
6. `(WHY object)` -- Explain justification for a node or clause; returns support chain
7. `(BACKTRACK)` -- Resolve contradictions by removing default assumptions

### Algorithm: Adding Truth Values (SET-TRUTH)
1. Verify node is currently UNKNOWN (error otherwise)
2. Set node's TRUTH property to the value, record SUPPORT
3. For each clause containing the term that just became FALSE, decrement PSAT
4. For each clause where PSAT reaches 1 and there exists one UNKNOWN node, deduce that node's value (the only way to satisfy the clause)
5. If PSAT reaches 0 for any clause, a contradiction has been found; add to CONTRA-LIST
6. If the node has an EFFECT callback, apply it
7. Recursively check for further one-step deductions via DEDUCE-CHECK

### Algorithm: Removing Truth Values (REMOVE-TRUTH)
1. Set node to UNKNOWN, clear SUPPORT
2. For each clause containing the term that was FALSE, increment PSAT (it can now potentially satisfy the clause again)
3. Remove truth values of nodes that critically depended on this one (those whose SUPPORT clause used this value)
4. After all removals, for nodes on the REMOVED-LIST that now have default values but no other truth value, re-check if the default can be re-asserted
5. After removal cascade, check for new deductions from clauses containing the newly-UNKNOWN terms

### Algorithm: Contradiction Handling
1. A contradiction occurs when a clause has PSAT = 0 (all terms are false)
2. When a truth value is added that causes a contradiction in clause C1, trace back through the deduction chain
3. The term F1 that became true when the contradiction was caused, and F2 the opposite value that was deducible from C1, together with F1's supporting clause, yield a new clause: the resolvent
4. The new clause is added, potentially enabling deduction of the negation of whatever caused the contradiction
5. If the new clause itself becomes a contradiction (all its terms are false), the process repeats recursively

### Algorithm: Backtracking (BACKTRACK)
1. If CONTRA-LIST is empty, return T (no contradictions)
2. For each contradiction, call WHY to find the assumptions (nodes with DEFAULT support) that the contradiction depends on
3. Collect assumptions with their maximum distance from the contradiction (number of clauses in the support chain)
4. Select the assumption with the minimum maximum distance
5. Call REMOVE-TRUTH on that assumption
6. The contradicting clause can now be used to deduce the negation of the default value
7. Repeat until no contradictions remain or no assumptions are left

### Key Design Decisions
- **One-step clause deductions only**: to avoid NP-complete satisfiability checking, only deductions from a single clause (when PSAT = 1) are performed. Multi-clause resolution is not attempted.
- **Clause representation eliminates antecedent/consequent distinction**: P1 ^ P2 ^ P3 -> Q is stored as (-P1 v -P2 v -P3 v Q), making negation deduction natural.
- **DeMorgan transformation for mutual exclusion**: -(P1 ^ P2 ^ ... ^ Pn) becomes (-P1 v -P2 v ... v -Pn), which is a single clause.
- **Support tracing is well-founded**: supports are always premises or clauses, never circular.
- **Clause validity nodes**: rather than physically deleting clauses, a validity node is added; setting it false effectively removes the clause.

## Figures of Interest
- **Fig 1 (page 11):** Example of clause formation from a contradiction. Shows how addition of -A causes C3 to become a contradiction, leading to the new clause (B ^ D ^ F) -> A.
- **Fig 2 (page 11):** General case of clause formation from contradiction. Shows the resolution process when adding -F2 causes C1 to become a contradiction, producing a new clause from the resolvent of C1 and the supporting clauses.

## Results Summary
The system is demonstrated to handle:
- Incremental truth maintenance with three-valued logic
- Automatic contradiction detection and resolution
- Dependency-directed backtracking that avoids chronological backtracking
- Default reasoning with assumption hierarchies
- The system was used in electronic circuit analysis applications (Stallman and Sussman 1976)

## Limitations
- Only one-step clause deductions are performed (no multi-clause resolution), which may miss some valid inferences
- Contradiction resolution via new clause generation can sometimes "pulse" -- repeatedly adding and retracting the same value before stabilizing, though the author states this would require a complex structure and at most one or two pulses
- No conditional proof mechanism is implemented (unlike Doyle's TMS which uses conditional proofs for condensed explanations)
- The backtracking heuristic (minimum maximum distance) is simple and may not always choose the optimal assumption to retract
- The paper acknowledges that because no specific set of assumptions is chosen to blame for a contradiction, new assumptions leading to old contradictions can be proven false but the number of such extra contradictions is small compared to dependency-directed backtracking savings

## Testable Properties
- A node's TRUTH value is always one of {TRUE, FALSE, UNKNOWN}
- A node can never transition directly from TRUE to FALSE or vice versa; it must pass through UNKNOWN
- When a clause has PSAT = 0, it must appear on CONTRA-LIST
- When a clause has PSAT = 1 and the remaining unknown node exists, a deduction must occur
- SUPPORT for a truth value is always well-founded (traceable to premises without cycles)
- Removing a truth value must also remove all truth values that critically depend on it
- After BACKTRACK completes, either CONTRA-LIST is empty or no default assumptions remain
- Adding a clause with PSAT = 0 immediately triggers contradiction handling
- The clause (node . value) representation satisfies: if all terms are false except one unknown, that unknown term's value is deducible

## Relevance to Project
This paper is the "RUP" (Reason, Unknown, Premiss) system referenced in de Kleer's 1986 ATMS papers. It represents an intermediate step between Doyle's original TMS (1979) and de Kleer's ATMS (1986). Key concepts that carry forward to the ATMS include: clause-based representation of justifications, support tracing for explanations, and contradiction-driven constraint propagation. The three-valued approach is simpler than Doyle's two-valued system with separate negation nodes, though de Kleer's ATMS takes a fundamentally different approach by tracking assumption sets (environments) rather than maintaining a single consistent state.

## Open Questions
- [ ] How does the "pulsing" behavior during contradiction resolution compare to the ATMS's label update mechanism?
- [ ] Could the clause-generation mechanism from contradictions be adapted for the propstore's constraint system?
- [ ] What is the empirical computational cost of the one-step-only restriction vs. full resolution?

## Related Work Worth Reading
- McAllester, D. (1980) "An Outlook on Truth Maintenance" -- MIT AI Memo 551, the more mature follow-up
- Stallman and Sussman (1976) "Forward Reasoning and Dependency Directed Backtracking in a System for Computer Aided Circuit Analysis" -- the ARS system this TMS was designed to support
- de Kleer, Doyle, Steele, and Sussman (1977) "Explicit Control of Reasoning" -- the AMORD system

## Collection Cross-References

### Already in Collection
- [[Doyle_1979_TruthMaintenanceSystem]] -- cited as [Doyle 1978a]; the primary comparison point. McAllester's system is designed as a simpler alternative to Doyle's TMS, using three-valued logic and clauses instead of two-valued logic with SL/CP justifications and non-monotonic dependencies.
- [[deKleer_1986_ProblemSolvingATMS]] -- cites this paper as the "RUP" system; compares ATMS consumer architecture against McAllester's clause-based approach. The ATMS supersedes this TMS by tracking multiple assumption sets simultaneously.
- [[deKleer_1986_AssumptionBasedTMS]] -- cites this paper [14] as part of the TMS lineage; the ATMS addresses limitations of both Doyle's and McAllester's approaches by maintaining all consistent contexts simultaneously.

### New Leads (Not Yet in Collection)
- Stallman and Sussman (1976) -- "Forward Reasoning and Dependency Directed Backtracking" -- the ARS system; primary application domain for this TMS
- de Kleer, Doyle, Steele, and Sussman (1977) -- "Explicit Control of Reasoning" -- AMORD system

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- [[Doyle_1979_TruthMaintenanceSystem]] -- cites McAllester [30] as an alternative TMS design with cleaner organization
- [[deKleer_1986_ProblemSolvingATMS]] -- cites this as [14], the RUP system, in comparison of TMS architectures
- [[deKleer_1986_AssumptionBasedTMS]] -- cites this as [14] in the lineage of truth maintenance systems

### Conceptual Links (not citation-based)
- [[Doyle_1979_TruthMaintenanceSystem]] -- Strong: both papers solve the same core problem (maintaining consistent beliefs under contradiction) with fundamentally different architectures. Doyle uses two-valued SL/CP justifications with non-monotonic dependencies; McAllester uses three-valued clausal representation. McAllester's clause-based contradiction resolution (generating new clauses from contradictions) is a precursor to the ATMS's nogood management. Key difference: McAllester eliminates non-monotonic dependencies but loses conditional proofs.
- [[deKleer_1986_AssumptionBasedTMS]] -- Strong: the ATMS can be seen as the natural evolution of McAllester's ideas. McAllester's clause representation and symmetric deduction anticipate the ATMS's justification-based label propagation. The ATMS's key innovation (maintaining all consistent environments simultaneously rather than a single state) directly addresses the limitation that McAllester's system still maintains only one consistent state at a time.
- [[deKleer_1986_ProblemSolvingATMS]] -- Strong: this paper's default backtracking algorithm (selecting assumptions by distance from contradiction) is the precursor to the ATMS's dependency-directed backtracking via nogoods and control disjunctions. The ATMS problem-solving paper explicitly compares against McAllester's RUP system.
