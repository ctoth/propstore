---
title: "A Truth Maintenance System"
authors: "Jon Doyle"
year: 1979
venue: "Artificial Intelligence"
doi_url: "https://doi.org/10.1016/0004-3702(79)90008-0"
pages: "231-272"
institution: "Massachusetts Institute of Technology, Artificial Intelligence Laboratory"
---

# A Truth Maintenance System

## One-Sentence Summary
Introduces the first Truth Maintenance System (TMS), a problem-solver subsystem that records and maintains justifications for beliefs, enabling non-monotonic reasoning, dependency-directed backtracking, and automatic belief revision when assumptions change.

## Problem Addressed
Reasoning programs need to make assumptions and subsequently revise their beliefs when discoveries contradict those assumptions. The conventional monotonic view of reasoning (beliefs only grow, never shrink) fails to handle the frame problem, commonsense default reasoning, and the control problem of deciding what to do next. Doyle proposes that rational thought is the process of finding reasons for attitudes, and that by recording these reasons explicitly the system can perform principled non-monotonic belief revision.

## Key Contributions
- Introduces the **Truth Maintenance System (TMS)** as a subsystem that records reasons for program beliefs and maintains the current belief set incrementally
- Defines two justification types: **support-list (SL) justifications** `(SL <inlist> <outlist>)` for monotonic and non-monotonic deductions, and **conditional-proof (CP) justifications** `(CP <consequent> <inhypotheses> <outhypotheses>)` for hypothetical reasoning
- Introduces the distinction between **in** (believed) and **out** (not believed) nodes, with the key insight that support-status is about valid reasons for belief, not about truth
- Defines the concept of **well-founded supporting justification** as the non-circular argument used to determine belief status
- Presents the **truth maintenance process** (7-step algorithm) for incrementally updating belief statuses when justifications are added
- Introduces **dependency-directed backtracking** (4-step procedure): trace maximal assumptions of a contradiction, create a nogood, select a culprit, and retract it
- Introduces **summarizing arguments** using CP-justifications to abstract away low-level details from explanations
- Proposes **dialectical argumentation** as a way to organize modular problem solvers
- Describes **models of others' beliefs** by mirroring justifications within the TMS
- Describes control structures embedded in assumption patterns: **default assumptions**, **sequences of alternatives**, and **equivalence class representatives**

## Methodology
The paper proceeds from a philosophical reframing of reasoning as finding reasons for attitudes (not discovering truth), through the formal definition of the TMS data structures and algorithms, to several applications (summarizing arguments, dialectical argumentation, belief models, and control patterns).

## Key Equations

Nogood representation (from dependency-directed backtracking):

$$
\neg(\text{St}(A_1) \wedge \cdots \wedge \text{St}(A_n))
$$

Where St(A_i) is the statement of assumption node A_i. This is justified as a CP-justification to ensure the nogood remains believed regardless of which assumption is retracted.

Nogood justification form:

$$
(\text{CP } C \; S \; (\;))
$$

Where C is the contradiction node and S is the set of maximal assumptions.

Culprit retraction justification (selecting assumption A_i from set S = {A_1, ..., A_n} with denials D_1, ..., D_k):

$$
(\text{SL } (NG \; A_1 \cdots A_{i-1} \; A_{i+1} \cdots A_n)(D_1 \; D_{j-1} \; D_{j+1} \cdots D_k))
$$

Default assumption justification pattern (choosing A_i from alternatives S = {A_1, ..., A_n} using default-reason node G):

$$
(\text{SL } (G)(A_1 \cdots A_{i-1} \; A_{i+1} \cdots A_n))
$$

Sequence of alternatives justification pattern (ordered alternatives A_1, ..., A_n with ordering-reason node G):

$$
(\text{SL } (G \; \neg A_{i-1})(\neg A_i))
$$

Equivalence class representative selection (for node R_i as possible representative, with prior suggestions SR_1, ..., SR_{i-1}):

$$
SR_i: \; (\text{SL } (PR_i)(SR_1 \cdots SR_{i-1}))
$$
$$
R_i: \; (\text{CP } SR_i \; (\;)(SR_1 \cdots SR_{i-1}))
$$

## Parameters

This is a systems/algorithms paper with no empirical parameters. The key design parameters are:

| Name | Symbol | Units | Default | Range | Notes |
|------|--------|-------|---------|-------|-------|
| Number of nodes | N | - | - | - | Total potential beliefs in the system |
| Number of justifications per node | - | - | - | 1+ | Each node has a justification-set |
| Number of assumptions per contradiction | - | - | - | 1+ | Maximal assumption set S for backtracking |

## Implementation Details

### Data Structures
- **Node**: Has a statement St(N), a justification-set, a support-status (in/out/nil), a supporting-justification, and sets of supporting-nodes, antecedents, foundations, consequences, affected-consequences, believed-consequences, repercussions, believed-repercussions
- **Justification**: Either SL `(SL <inlist> <outlist>)` or CP `(CP <consequent> <inhypotheses> <outhypotheses>)`
- **Supporting-justification**: The single selected well-founded justification for each *in* node

### Support-List (SL) Justification Validity
An SL-justification `(SL <inlist> <outlist>)` is **valid** if each node in its *inlist* is *in* and each node in its *outlist* is *out*.

### SL-justification is **well-founded valid** if:
- Each node in the *inlist* is *in*
- No node of the *outlist* is *in*

### CP-justification Validity
A CP-justification `(CP C IH OH)` is valid if the consequent node is *in* whenever all *inhypotheses* are *in* and all *outhypotheses* are *out*. The TMS converts valid CP-justifications to equivalent SL-justifications via the Find Independent Support (FIS) procedure.

### Truth Maintenance Process (7 Steps)
1. **Add justification**: Add to node's justification-set, update consequences. If node is already *in*, done. If *out*, check validity.
2. **Update beliefs**: Check affected-consequences. If none, change to *in*, make supporting-nodes the sum of *inlist* and *outlist*, proceed to Step 3.
3. **Mark nodes**: Mark each node in L with support-status *nil*, proceed to Step 4.
4. **Evaluate justifications**: For each node in L, try to find a valid well-founded SL-justification (chronological order, SL first then CP). If found, install as supporting-justification, mark *in*, recursively process *nil*-marked consequences. If only well-founded-invalid found, mark *out*.
5. **Relax circularities**: For remaining *nil* nodes, attempt to find not-well-founded valid or invalid justifications. Assign support-statuses via constraint relaxation. Handle unsatisfiable circularities by detecting nodes that are their own ancestors in not-well-founded-valid justifications.
6. **Check CP-justifications and contradictions**: Derive new SL-justifications from valid CPs. Check for contradictions in newly-*in* nodes. If any found, restart from Step 1.
7. **Signal changes**: Compare current support-status with initial, call user-supplied signal-recalling and signal-forgetting functions.

### Dependency-Directed Backtracking (4 Steps)
1. **Find maximal assumptions**: Trace foundations of contradiction node C to find S = {A_1, ..., A_n}, the maximal assumptions underlying C.
2. **Summarize the cause**: Create nogood node NG representing the inconsistency of S. Justify with `(CP C S ())`.
3. **Select and reject a culprit**: Select some A_i from S. Let D_1, ..., D_k be the *out* nodes in A_i's supporting-justification outlist. Select D_j and justify it with `(SL (NG A_1...A_{i-1} A_{i+1}...A_n)(D_1...D_{j-1} D_{j+1}...D_k))`.
4. **Repeat if necessary**: If contradiction C remains *in* after Step 3, repeat with new culprit (previous culprit A_i presumably no longer an assumption). If C becomes *out* and no assumptions remain in C's foundations, notify problem solver of unanalyzable contradiction.

### Find Independent Support (FIS) Procedure (6 Steps)
Computes SL-justifications equivalent to valid CP-justifications by finding nodes in the foundations of the consequent that are not hypotheses or their repercussions:
1. Mark hypotheses and subordinate nodes
2. Mark the foundations
3. Unmark the foundations
4. Remark the hypotheses
5. Collect the net support (IS and OS sets)
6. Clean up and return `(SL IS OS)`

### Three Types of Circularity
1. **Consistent circularities**: Nodes which are *out* consistently with their justifications (e.g., equivalent or conditionally-equivalent beliefs that mutually constrain)
2. **Choice circularities**: At least one node must be *in* (e.g., `F: TO-BE (SL()(G))` and `G: NOT-TO-BE (SL()(F))`)
3. **Unsatisfiable circularities**: No consistent assignment exists (e.g., `F: ... (SL()(F))` -- F must be *in* iff F is *out*)

## Figures of Interest
- **Fig 1 (page 242/p12):** Dependency graph for Table 1's six-node system. Arrows represent justifications, uncrossed arrows are *inlist* references, crossed line of J2 represents an *outlist* reference. Support relationships point upwards.
- **Table 1 (page 241/p11):** A sample system of six nodes and seven justifications showing node-justification structure
- **Table 2 (page 241/p11):** All dependency relationships (support-status, supporting-justification, supporting-nodes, antecedents, foundations, ancestors, consequences, affected/believed-consequences, repercussions, believed-repercussions) for the Table 1 system

## Results Summary
The TMS was first implemented in September 1976 as an extension of Stallman and Sussman's fact garbage collector. It was subsequently used in circuit analysis, synthesis programs, blocks-world problem solvers, symbolic algebra, electronic circuit analysis, natural explanation systems, and program understanding systems. The implementation trades off CP-justification complexity for the FIS procedure's overhead, and does not handle unsatisfiable circularities (removed for efficiency). Incrementality issues remain: the TMS normally examines only repercussions of changed nodes but circularities can force examination of nodes not in the repercussion set.

## Limitations
- **Blind culprit selection**: The backtracker picks the culprit and denial randomly from the alternatives, relying on blind search; inadequate for all but the simplest problems
- **No unsatisfiable circularity handling**: Removed from implementation for efficiency; a robust version would reinstate this check
- **Incrementality problems**: Circularities can force examining nodes outside the normal repercussion set; some circumstances force the TMS to examine large numbers of nodes
- **No grading of beliefs**: The TMS makes binary in/out decisions; no notion of belief strength, credibility, or confidence
- **Circular arguments possible in transient states**: During truth maintenance, nodes may temporarily hold beliefs on circular grounds; the well-founded support mechanism addresses this but the relaxation step (Step 5) may produce non-unique assignments
- **CP-justification overhead**: The FIS procedure and constant checking of CP-justifications for validity makes the implementation considerably more complex than a pure SL system would be

## Testable Properties
- A node is *in* if and only if at least one justification in its justification-set is well-founded valid
- A node is *out* if and only if no justification in its justification-set is well-founded valid
- An SL-justification `(SL I O)` is valid iff every node in I is *in* and every node in O is *out*
- A well-founded supporting-justification for an *in* node must be non-circular: the node must not appear in its own foundations via the supporting-justification chain
- After truth maintenance completes, no *in* node has only circular supporting justifications
- The supporting-nodes of a node are exactly the union of the *inlist* and *outlist* of its supporting-justification
- The antecedents of an *in* node are its supporting-nodes; the foundations are the transitive closure of antecedents
- Dependency-directed backtracking must retract at least one assumption from the maximal assumption set of the contradiction
- After culprit retraction, the nogood node remains *in* (justified by CP-justification independent of assumptions)
- Default assumptions: given alternatives {A_1, ..., A_n}, exactly one should be *in* at any time (unless external mechanism constructs a new default when all are ruled out)

## Relevance to Project
This is the foundational paper for the entire truth maintenance / belief revision line of work that the propstore's world model is built on. It introduces the core concepts (justifications, support-status, dependency-directed backtracking, assumptions, nogoods) that de Kleer's ATMS later refines and improves. Understanding the original TMS design is essential for understanding the ATMS's design decisions and what problems it was solving. The control patterns (defaults, sequences, equivalence classes) described here are directly relevant to how the propstore manages competing claims and alternative hypotheses.

## Open Questions
- [ ] How does the relaxation step (Step 5) perform in practice? Is the non-determinism in circularity resolution a practical problem?
- [ ] What is the computational complexity of the FIS procedure in the worst case?
- [ ] The paper mentions the AMORD explicit control of reasoning system [11] -- how does this relate to the propstore's control architecture?

## Related Work Worth Reading
- Stallman and Sussman [53] (1977) -- Forward reasoning and dependency-directed backtracking in circuit analysis; the direct predecessor to the TMS
- McDermott and Doyle [35] (1978) -- Non-monotonic logic I; formalizes the logic underlying TMS-style reasoning
- McAllester [30,31] (1978,1980) -- Three-valued TMS and alternative implementation with cleaner organization
- de Kleer [9,10] (1976,1979) -- Fault localization and circuit recognition using dependency tracking; the application that motivated much of the TMS work

## Collection Cross-References

### Already in Collection
- [[deKleer_1986_AssumptionBasedTMS]] — cited as improving upon and replacing this TMS; the ATMS was designed to overcome seven specific limitations of Doyle's justification-based TMS (single-state, overzealous contradiction avoidance, context switching, justification dominance, cumbersome machinery, unouting, circular support)
- [[deKleer_1986_ProblemSolvingATMS]] — references this paper for comparison of control approaches; notes that Doyle's TMS data pool mechanism provides a stronger notion of control than the ATMS consumer architecture

### New Leads (Not Yet in Collection)
- Stallman and Sussman (1977) — "Forward reasoning and dependency-directed backtracking" — direct predecessor to the TMS
- McDermott and Doyle (1978) — "Non-monotonic logic I" — formalizes the logic underlying TMS reasoning

### Now in Collection (previously listed as leads)
- [[McAllester_1978_ThreeValuedTMS]] — Three-valued TMS using disjunctive clause representation with true/false/unknown states. Designed as a simpler alternative to Doyle's TMS: eliminates non-monotonic dependency structures and separate negation nodes. Does not implement conditional proofs but achieves similar non-monotonic power through clause-based contradiction resolution and default backtracking.

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- [[deKleer_1986_AssumptionBasedTMS]] — cites this as [12], the original justification-based TMS that the ATMS replaces; catalogs seven limitations of this system that motivate the ATMS design
- [[deKleer_1986_ProblemSolvingATMS]] — cites this for comparison of TMS architectures; compares control mechanisms, data pool vs. consumer architecture

### Conceptual Links (not citation-based)
- [[deKleer_1986_AssumptionBasedTMS]] — Strong: this paper defines the single-context justification-based TMS; that paper defines the multi-context assumption-based TMS that replaces it. Same core problem (belief revision under contradictions) with fundamentally different architecture (retraction-based vs. label-based). Key concepts from this paper (justifications, nogoods, dependency-directed backtracking) are preserved but reconceptualized in the ATMS.
- [[deKleer_1986_ProblemSolvingATMS]] — Strong: this paper's control patterns (default assumptions, sequences of alternatives, equivalence classes) are the precursors to the ATMS problem-solving paper's consumer architecture and control disjunctions. The ATMS paper's constraint language (PLUS, TIMES, AND, OR, ONEOF) provides a more structured version of the ad-hoc control patterns described here.
