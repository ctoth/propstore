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
Introduces the first Truth Maintenance System (TMS), a problem-solver subsystem that records and maintains justifications for beliefs, enabling non-monotonic reasoning, dependency-directed backtracking, and automatic belief revision when assumptions change. *(p.231)*

## Problem Addressed
Reasoning programs need to make assumptions and subsequently revise their beliefs when discoveries contradict those assumptions. *(p.231)* The conventional monotonic view of reasoning (beliefs only grow, never shrink) fails to handle the frame problem, commonsense default reasoning, and the control problem of deciding what to do next. *(pp.232-233)* Doyle proposes that rational thought is the process of finding reasons for attitudes, and that by recording these reasons explicitly the system can perform principled non-monotonic belief revision. *(p.234)*

## Key Contributions
- Introduces the **Truth Maintenance System (TMS)** as a subsystem that records reasons for program beliefs and maintains the current belief set incrementally *(p.231)*
- Defines two justification types: **support-list (SL) justifications** `(SL <inlist> <outlist>)` for monotonic and non-monotonic deductions, and **conditional-proof (CP) justifications** `(CP <consequent> <inhypotheses> <outhypotheses>)` for hypothetical reasoning *(pp.239-240, 243)*
- Introduces the distinction between **in** (believed) and **out** (not believed) nodes, with the key insight that support-status is about valid reasons for belief, not about truth *(pp.234, 238)*
- Defines the concept of **well-founded supporting justification** as the non-circular argument used to determine belief status *(p.236)*
- Presents the **truth maintenance process** (7-step algorithm) for incrementally updating belief statuses when justifications are added *(pp.246-249)*
- Introduces **dependency-directed backtracking** (4-step procedure): trace maximal assumptions of a contradiction, create a nogood, select a culprit, and retract it *(pp.251-252)*
- Introduces **summarizing arguments** using CP-justifications to abstract away low-level details from explanations *(pp.253-256)*
- Proposes **dialectical argumentation** as a way to organize modular problem solvers *(pp.256-257)*
- Describes **models of others' beliefs** by mirroring justifications within the TMS *(pp.258-259)*
- Describes control structures embedded in assumption patterns: **default assumptions**, **sequences of alternatives**, and **equivalence class representatives** *(pp.261-265)*

## Methodology
The paper proceeds from a philosophical reframing of reasoning as finding reasons for attitudes (not discovering truth) *(pp.233-234)*, through the formal definition of the TMS data structures and algorithms *(pp.236-252)*, to several applications (summarizing arguments *(pp.253-256)*, dialectical argumentation *(pp.256-257)*, belief models *(pp.258-259)*, and control patterns *(pp.260-265)*).

## Key Equations

Nogood representation (from dependency-directed backtracking):

$$
\neg(\text{St}(A_1) \wedge \cdots \wedge \text{St}(A_n))
$$

Where St(A_i) is the statement of assumption node A_i. This is justified as a CP-justification to ensure the nogood remains believed regardless of which assumption is retracted.
*(p.251)*

Nogood justification form:

$$
(\text{CP } C \; S \; (\;))
$$

Where C is the contradiction node and S is the set of maximal assumptions.
*(p.251)*

Culprit retraction justification (selecting assumption A_i from set S = {A_1, ..., A_n} with denials D_1, ..., D_k):

$$
(\text{SL } (NG \; A_1 \cdots A_{i-1} \; A_{i+1} \cdots A_n)(D_1 \; D_{j-1} \; D_{j+1} \cdots D_k))
$$

*(p.251)*

Default assumption justification pattern (choosing A_i from alternatives S = {A_1, ..., A_n} using default-reason node G):

$$
(\text{SL } (G)(A_1 \cdots A_{i-1} \; A_{i+1} \cdots A_n))
$$

*(p.261)*

Sequence of alternatives justification pattern (ordered alternatives A_1, ..., A_n with ordering-reason node G):

$$
(\text{SL } (G \; \neg A_{i-1})(\neg A_i))
$$

*(p.263)*

Equivalence class representative selection (for node R_i as possible representative, with prior suggestions SR_1, ..., SR_{i-1}):

$$
SR_i: \; (\text{SL } (PR_i)(SR_1 \cdots SR_{i-1}))
$$
$$
R_i: \; (\text{CP } SR_i \; (\;)(SR_1 \cdots SR_{i-1}))
$$

*(p.264)*

## Parameters

This is a systems/algorithms paper with no empirical parameters. The key design parameters are:

| Name | Symbol | Units | Default | Range | Notes | Page |
|------|--------|-------|---------|-------|-------|------|
| Number of nodes | N | - | - | - | Total potential beliefs in the system | p.236 |
| Number of justifications per node | - | - | - | 1+ | Each node has a justification-set | p.238 |
| Number of assumptions per contradiction | - | - | - | 1+ | Maximal assumption set S for backtracking | p.251 |

## Implementation Details

### Data Structures
- **Node**: Has a statement St(N), a justification-set, a support-status (in/out/nil), a supporting-justification, and sets of supporting-nodes, antecedents, foundations, consequences, affected-consequences, believed-consequences, repercussions, believed-repercussions *(pp.241-242)*
- **Justification**: Either SL `(SL <inlist> <outlist>)` or CP `(CP <consequent> <inhypotheses> <outhypotheses>)` *(pp.239-240, 243)*
- **Supporting-justification**: The single selected well-founded justification for each *in* node *(p.241)*

### Three Fundamental TMS Actions
1. The TMS can create a new node, to which the problem solving program attaches a statement of belief *(p.236)*
2. It can add (or retract) a new justification for a node, representing an argument step *(p.236)*
3. The program can mark a node as a contradiction, representing inconsistency of beliefs entering its argument *(p.236)*

### Support-List (SL) Justification Validity
An SL-justification `(SL <inlist> <outlist>)` is **valid** if each node in its *inlist* is *in* and each node in its *outlist* is *out*. *(p.240)*

### SL-justification is **well-founded valid** if:
- Each node in the *inlist* is *in*
- No node of the *outlist* is *in*
*(p.247)*

### CP-justification Validity
A CP-justification `(CP C IH OH)` is valid if the consequent node is *in* whenever all *inhypotheses* are *in* and all *outhypotheses* are *out*. The TMS converts valid CP-justifications to equivalent SL-justifications via the Find Independent Support (FIS) procedure. *(pp.243-244)*

### Additional Justification Types (proposed but not implemented)
- **General-form (GF) justification**: merges SL and CP into one form: `(GF <inlist> <outlist> <consequent> <inhypotheses> <outhypotheses>)` *(p.244)*
- **Summarization (SUM) justification**: `(SUM <consequent> <inhypotheses> <outhypotheses>)`, abbreviates a GF that adds hypotheses back into the conditional-proof result *(p.244)*

### Truth Maintenance Process (7 Steps)
1. **Add justification**: Add to node's justification-set, update consequences. If node is already *in*, done. If *out*, check validity. *(p.246)*
2. **Update beliefs**: Check affected-consequences. If none, change to *in*, make supporting-nodes the sum of *inlist* and *outlist*, proceed to Step 3. *(pp.246-247)*
3. **Mark nodes**: Mark each node in L with support-status *nil*, proceed to Step 4. *(p.247)*
4. **Evaluate justifications**: For each node in L, try to find a valid well-founded SL-justification (chronological order, SL first then CP). If found, install as supporting-justification, mark *in*, recursively process *nil*-marked consequences. If only well-founded-invalid found, mark *out*. *(p.247)*
5. **Relax circularities**: For remaining *nil* nodes, attempt to find not-well-founded valid or invalid justifications. Assign support-statuses via constraint relaxation. Handle unsatisfiable circularities by detecting nodes that are their own ancestors in not-well-founded-valid justifications. *(pp.247-248)*
6. **Check CP-justifications and contradictions**: Derive new SL-justifications from valid CPs. Check for contradictions in newly-*in* nodes. If any found, restart from Step 1. *(p.249)*
7. **Signal changes**: Compare current support-status with initial, call user-supplied signal-recalling and signal-forgetting functions. *(p.249)*

### Dependency-Directed Backtracking (4 Steps)
1. **Find maximal assumptions**: Trace foundations of contradiction node C to find S = {A_1, ..., A_n}, the maximal assumptions underlying C. *(p.251)*
2. **Summarize the cause**: Create nogood node NG representing the inconsistency of S. Justify with `(CP C S ())`. *(p.251)*
3. **Select and reject a culprit**: Select some A_i from S. Let D_1, ..., D_k be the *out* nodes in A_i's supporting-justification outlist. Select D_j and justify it with `(SL (NG A_1...A_{i-1} A_{i+1}...A_n)(D_1...D_{j-1} D_{j+1}...D_k))`. *(p.251)*
4. **Repeat if necessary**: If contradiction C remains *in* after Step 3, repeat with new culprit (previous culprit A_i presumably no longer an assumption). If C becomes *out* and no assumptions remain in C's foundations, notify problem solver of unanalyzable contradiction. *(p.252)*

### Find Independent Support (FIS) Procedure (6 Steps)
Computes SL-justifications equivalent to valid CP-justifications by finding nodes in the foundations of the consequent that are not hypotheses or their repercussions: *(pp.249-250)*
1. Mark hypotheses and subordinate nodes *(p.250)*
2. Mark the foundations *(p.250)*
3. Unmark the foundations *(p.250)*
4. Remark the hypotheses *(p.250)*
5. Collect the net support (IS and OS sets) *(p.250)*
6. Clean up and return `(SL IS OS)` *(p.250)*

### Three Types of Circularity
1. **Consistent circularities**: Nodes which are *out* consistently with their justifications (e.g., equivalent or conditionally-equivalent beliefs that mutually constrain) *(p.245)*
2. **Choice circularities**: At least one node must be *in* (e.g., `F: TO-BE (SL()(G))` and `G: NOT-TO-BE (SL()(F))`) *(p.245)*
3. **Unsatisfiable circularities**: No consistent assignment exists (e.g., `F: ... (SL()(F))` -- F must be *in* iff F is *out*) *(p.245)*

### Summarizing Arguments
Long or detailed arguments are made intelligible by structuring them into separated levels of detail using CP-justifications to subtract low-level nodes from explanations. *(pp.253-254)* The technique uses structured descriptions (description-items with roles) where internal and external role-item nodes are separated so the TMS can summarize via SUM-justifications that replace internal computation dependencies with the single description node. *(pp.254-256)*

### Dialectical Argumentation
Organizes problem solving as modular argumentation in three steps: *(p.256)*
1. **Make an argument**: Put forward argument A for a conclusion based on shared premises
2. **Reply to challenges**: When challenged by argument B, either make a new argument for A's conclusion, or make an argument for a challenged premise/step of A
3. **Repeat**: Continue replying to challenges or making new arguments

Implementation in TMS: argument steps are represented as justifications, beliefs as assumptions. Challenges create new nodes representing the challenge, justified with `(SL () (neg-J))` where J is the challenged justification. The belief system becomes additive -- arguments accumulate monotonically while the current set of beliefs changes non-monotonically. *(pp.256-257)*

### Models of Others' Beliefs
For each node N in another agent U's belief system, create nodes UB[N] and neg-UB[N], representing that U believes/does not believe in N. Mirror U's justifications by creating corresponding justifications in our TMS using UB[N] nodes. *(pp.258-259)* This technique embodies the modal logic axiom: Bel(p => q) => (Bel(p) => Bel(q)). *(p.258)* Can be nested for embedded belief spaces (beliefs about beliefs about beliefs). *(p.259)*

### Control Patterns

#### Default Assumptions
To pick a default from alternatives S = {A_1, ..., A_n}, use default-reason node G and justify each A_i with `(SL (G)(A_1...A_{i-1} A_{i+1}...A_n))`. If no additional information, exactly one alternative will be *in*. *(p.261)* For extensible defaults where alternatives are discovered piecemeal, use negation nodes: justify A_i with `(SL (G)(neg-A_i))` and justify each neg-A_j with `(SL (A_j)())`. New alternatives can be added at any time. *(p.262)*

#### Sequences of Alternatives
Linearly ordered alternatives add heuristic ordering: justify each A_i with `(SL (G neg-A_{i-1})(neg-A_i))`. A_1 is selected initially; as it is rejected, alternatives are tried in order. *(p.263)* For linearly ordered alternatives with reconsideration support, use three auxiliary nodes per alternative: PA_i (possible alternative), NSA_i (not selected alternative), ROA_i (ruled-out alternative). *(pp.263-264)*

#### Equivalence Class Representatives
For selecting a representative from coincident values, use CP-justifications to hide the selection from the backtracker: SR_i: `(SL (PR_i)(SR_1...SR_{i-1}))` and R_i: `(CP SR_i ()(SR_1...SR_{i-1}))`. *(p.264)* The CP-justification for R_i makes the reason for believing R_i be the reason for suggesting and selecting it, minus the default assumption for selecting it, thus making the choice invisible to backtracking. *(p.265)*

## Figures of Interest
- **Fig 1 (p.242):** Dependency graph for Table 1's six-node system. Arrows represent justifications, uncrossed arrows are *inlist* references, crossed line of J2 represents an *outlist* reference. Support relationships point upwards.
- **Table 1 (p.241):** A sample system of six nodes and seven justifications showing node-justification structure
- **Table 2 (p.241):** All dependency relationships (support-status, supporting-justification, supporting-nodes, antecedents, foundations, ancestors, consequences, affected/believed-consequences, repercussions, believed-repercussions) for the Table 1 system

## Results Summary
The TMS was first implemented in September 1976 as an extension of Stallman and Sussman's fact garbage collector. *(p.265)* It was subsequently used in circuit analysis, synthesis programs, blocks-world problem solvers, symbolic algebra, electronic circuit analysis, natural explanation systems, and program-understanding systems. *(pp.265-266)* The implementation trades off CP-justification complexity for the FIS procedure's overhead, and does not handle unsatisfiable circularities (removed for efficiency). *(pp.245-246, 266)* Incrementality issues remain: the TMS normally examines only repercussions of changed nodes but circularities can force examination of nodes not in the repercussion set. *(pp.266-267)*

Doyle notes that "Belief Revision System" might be a more accurate label than "Truth Maintenance System," and suggests distinguishing binary judgemental assertions (opinions) from graded underlying feelings (beliefs), following Dennett. *(p.268)*

The paper is based on a thesis submitted May 12, 1977; Sections 6 and 7 contain material not in that thesis. *(p.269)*

## Limitations
- **Blind culprit selection**: The backtracker picks the culprit and denial randomly from the alternatives, relying on blind search; inadequate for all but the simplest problems *(p.252)*
- **No unsatisfiable circularity handling**: Removed from implementation for efficiency; a robust version would reinstate this check *(p.245)*
- **Incrementality problems**: Circularities can force examining nodes outside the normal repercussion set; some circumstances force the TMS to examine large numbers of nodes *(pp.266-267)*
- **No grading of beliefs**: The TMS makes binary in/out decisions; no notion of belief strength, credibility, or confidence *(p.268)*
- **Circular arguments possible in transient states**: During truth maintenance, nodes may temporarily hold beliefs on circular grounds; the well-founded support mechanism addresses this but the relaxation step (Step 5) may produce non-unique assignments *(pp.245, 248)*
- **CP-justification overhead**: The FIS procedure and constant checking of CP-justifications for validity makes the implementation considerably more complex than a pure SL system would be *(p.266)*
- **Overhead of recording justifications**: Recording justifications for every program belief may seem excessive; summarization and disciplined retention of essential records can mitigate this *(p.269)*
- **Four-element belief set needed**: The in/out distinction is not the same as true/false; each statement and its negation need separate nodes, leading to a four-element belief state (true, false, unknown, contradictory) *(pp.238-239)*

## Testable Properties
- A node is *in* if and only if at least one justification in its justification-set is well-founded valid *(p.238)*
- A node is *out* if and only if no justification in its justification-set is well-founded valid *(p.238)*
- An SL-justification `(SL I O)` is valid iff every node in I is *in* and every node in O is *out* *(p.240)*
- A well-founded supporting-justification for an *in* node must be non-circular: the node must not appear in its own foundations via the supporting-justification chain *(pp.244-245)*
- After truth maintenance completes, no *in* node has only circular supporting justifications *(p.245)*
- The supporting-nodes of a node are exactly the union of the *inlist* and *outlist* of its supporting-justification *(p.241)*
- The antecedents of an *in* node are its supporting-nodes; the foundations are the transitive closure of antecedents *(p.242)*
- Dependency-directed backtracking must retract at least one assumption from the maximal assumption set of the contradiction *(p.251)*
- After culprit retraction, the nogood node remains *in* (justified by CP-justification independent of assumptions) *(p.251)*
- Default assumptions: given alternatives {A_1, ..., A_n}, exactly one should be *in* at any time (unless external mechanism constructs a new default when all are ruled out) *(pp.261-262)*

## Relevance to Project
This is the foundational paper for the entire truth maintenance / belief revision line of work that the propstore's world model is built on. It introduces the core concepts (justifications, support-status, dependency-directed backtracking, assumptions, nogoods) that de Kleer's ATMS later refines and improves. Understanding the original TMS design is essential for understanding the ATMS's design decisions and what problems it was solving. The control patterns (defaults, sequences, equivalence classes) described here are directly relevant to how the propstore manages competing claims and alternative hypotheses.

## Open Questions
- [ ] How does the relaxation step (Step 5) perform in practice? Is the non-determinism in circularity resolution a practical problem? *(p.248)*
- [ ] What is the computational complexity of the FIS procedure in the worst case? *(pp.249-250)*
- [ ] The paper mentions the AMORD explicit control of reasoning system [11] -- how does this relate to the propstore's control architecture? *(p.260)*
- [ ] Doyle suggests "Belief Revision System" as a better name and distinguishes opinions (binary judgements) from beliefs (graded feelings) following Dennett [13] -- does this distinction matter for the propstore? *(p.268)*

## Related Work Worth Reading
- Stallman and Sussman [53] (1977) -- Forward reasoning and dependency-directed backtracking in circuit analysis; the direct predecessor to the TMS *(p.265)*
- McDermott and Doyle [35] (1978) -- Non-monotonic logic I; formalizes the logic underlying TMS-style reasoning *(p.268)*
- McAllester [30,31] (1978,1980) -- Three-valued TMS and alternative implementation with cleaner organization *(p.266)*
- de Kleer [9,10] (1976,1979) -- Fault localization and circuit recognition using dependency tracking; the application that motivated much of the TMS work *(pp.265-266)*
- Colby [6] (1973) -- Simulations of belief systems with reasons for beliefs and measures of credibility and emotional importance; the exception to most work being restricted to backtracking algorithms *(p.267)*
- Rescher [44] (1964) -- Hypothetical Reasoning, builds on Goodman's counterfactual conditionals framework *(p.268)*
- Quine and Ullian [43] (1978) -- The Web of Belief, surveys evaluative criteria for judging belief revisions *(p.268)*

## Collection Cross-References

### Already in Collection
- [[deKleer_1986_AssumptionBasedTMS]] -- cited as improving upon and replacing this TMS; the ATMS was designed to overcome seven specific limitations of Doyle's justification-based TMS (single-state, overzealous contradiction avoidance, context switching, justification dominance, cumbersome machinery, unouting, circular support)
- [[deKleer_1986_ProblemSolvingATMS]] -- references this paper for comparison of control approaches; notes that Doyle's TMS data pool mechanism provides a stronger notion of control than the ATMS consumer architecture

### New Leads (Not Yet in Collection)
- Stallman and Sussman (1977) -- "Forward reasoning and dependency-directed backtracking" -- direct predecessor to the TMS
- McDermott and Doyle (1978) -- "Non-monotonic logic I" -- formalizes the logic underlying TMS reasoning

### Now in Collection (previously listed as leads)
- [[McAllester_1978_ThreeValuedTMS]] -- Three-valued TMS using disjunctive clause representation with true/false/unknown states. Designed as a simpler alternative to Doyle's TMS: eliminates non-monotonic dependency structures and separate negation nodes. Does not implement conditional proofs but achieves similar non-monotonic power through clause-based contradiction resolution and default backtracking.

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- [[deKleer_1986_AssumptionBasedTMS]] -- cites this as [12], the original justification-based TMS that the ATMS replaces; catalogs seven limitations of this system that motivate the ATMS design
- [[deKleer_1986_ProblemSolvingATMS]] -- cites this for comparison of TMS architectures; compares control mechanisms, data pool vs. consumer architecture
- [[Martins_1983_MultipleBeliefSpaces]] -- cites this as [2]; MBR improves upon Doyle's TMS with restriction sets replacing the NOGOOD list
- [[Martins_1988_BeliefRevision]] -- cites this as [12]; MBR/SWM designed to improve upon Doyle's justification-based approach by computing dependencies automatically
- [[Falkenhainer_1987_BeliefMaintenanceSystem]] -- cites this as the foundational TMS that the BMS directly generalizes to continuous-valued beliefs
- [[McDermott_1983_ContextsDataDependencies]] -- cites this as [5]; McDermott directly extends and synthesizes Doyle's data dependencies with data pools
- [[Reiter_1980_DefaultReasoning]] -- cites Doyle (1978) as the heuristic implementation mechanism for belief revision under default reasoning
- [[Pollock_1987_DefeasibleReasoning]] -- cites this as Doyle (1979); contrasts OSCAR's approach (storing only immediate bases) with Doyle's TMS (storing all arguments)
- [[Shapiro_1998_BeliefRevisionTMS]] -- surveys this as the foundational JTMS architecture

### Conceptual Links (not citation-based)
- [[deKleer_1986_AssumptionBasedTMS]] -- Strong: this paper defines the single-context justification-based TMS; that paper defines the multi-context assumption-based TMS that replaces it. Same core problem (belief revision under contradictions) with fundamentally different architecture (retraction-based vs. label-based). Key concepts from this paper (justifications, nogoods, dependency-directed backtracking) are preserved but reconceptualized in the ATMS.
- [[deKleer_1986_ProblemSolvingATMS]] -- Strong: this paper's control patterns (default assumptions, sequences of alternatives, equivalence classes) are the precursors to the ATMS problem-solving paper's consumer architecture and control disjunctions. The ATMS paper's constraint language (PLUS, TIMES, AND, OR, ONEOF) provides a more structured version of the ad-hoc control patterns described here.
