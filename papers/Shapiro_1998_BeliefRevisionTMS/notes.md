---
title: "Belief Revision and Truth Maintenance Systems: An Overview and a Proposal"
authors: "Stuart C. Shapiro"
year: 1998
venue: "CSE Technical Report 98-10, State University of New York at Buffalo"
doi_url: "https://cse.buffalo.edu/~shapiro/Papers/br-overview.pdf"
---

# Belief Revision and Truth Maintenance Systems: An Overview and a Proposal

## One-Sentence Summary
This paper provides a high-level comparative survey of truth maintenance systems (JTMSs, LTMSs, ATMSs) and AGM belief revision theory, identifying that the two traditions have developed in near-complete isolation, and proposes building a TMS implementation that satisfies AGM postulates.

## Problem Addressed
The TMS literature (AI systems engineering) and the AGM belief revision literature (formal epistemology/logic) address the same fundamental problem --- maintaining consistency in a knowledge base when beliefs change --- yet almost no publication in either tradition cites any publication in the other. The paper surveys both and proposes unifying them.

## Key Contributions
- Defines a common framework: a Knowledge-Based System (KBS) consisting of a knowledge base (KB) of assertions, inference methods, and a belief revision subsystem (BRS/TMS)
- Identifies three core BRS tasks: (1) find derivation support for an assertion, (2) find assertions derived from an assumption, (3) delete an assertion and all its dependents
- Surveys four TMS architectures (JTMS, LTMS, ATMS, SNeBR) with how each handles the three BRS tasks
- Surveys AGM belief revision (expansion, contraction, revision) and its two key constraints on culprit selection
- Observes that the two traditions are nearly disjoint in citations
- Proposes implementing a BRS on top of SNePS/SNeBR/SNePSwD that satisfies AGM constraints

## Methodology
Comparative literature survey with a proposal for future experimental work. No formal proofs or experiments are presented; the contribution is taxonomic and architectural.

## Key Equations

This paper contains no formal equations. The logical notation used is informal:

$$
\{A_1, \ldots, A_n\}\{B_1, \ldots, B_m\} \Rightarrow C
$$
Where: $A_i$ are conditions that must be in the KB, $B_j$ are conditions that must NOT be in the KB (non-monotonic), and $C$ is the conclusion. This is the general form of a non-monotonic rule.

## Parameters

This is a survey/overview paper with no experimental parameters.

## Implementation Details

### KBS Architecture
A Knowledge-Based System consists of:
- A **knowledge base (KB)** of assertions, which can be:
  - Ground atomic propositions ("facts")
  - Closed non-atomic propositions with connectives/quantifiers ("rules")
  - User-supplied assumptions/hypotheses
  - Inferred/derived assertions
- A set of **inference methods** (sound with respect to the logic's semantics)
- A **belief revision system (BRS)** / truth maintenance system (TMS)

### Three Core BRS Tasks
1. **Find derivation support**: Given an assertion, find the assertions used to derive it
2. **Find derived assertions**: Given an assumption, find all assertions derived from it
3. **Delete and cascade**: Delete an assertion and all assertions derived from it from the KB

### JTMS (Justification-based TMS, Doyle 1979)
- Uses propositional logic only, atomic propositions and negations ("literals")
- Dependency graph with two vertex types: **nodes** (literals) and **justifications**
- Arcs go from nodes to justifications and from justifications to nodes
- Nodes labeled "in" or "out" (in KB or not)
- Assumptions: nodes with no arcs coming into their justifications
- **Task 1** (find support): Follow arcs backward from assertion to justifications to their input nodes, recursively to assumptions
- **Task 2** (find derived): Follow arcs forward from assumption to justifications it points to, to nodes those justify, recursively
- **Task 3** (delete + cascade): If assumption, set label to "out" and propagate forward, changing dependent nodes to "out" unless they have an alternative justification or are already "out". If not an assumption, find its supporting assumptions (task 1), choose a culprit, delete it (task 3, first clause), repeat until the target assertion's label is "out"
- **Non-monotonic extension**: "inverter" arcs from justifications to literals that must be "out" for the justification to hold. Rule $\{D\}\{E\} \Rightarrow F$: normal arc from $D$, inverter arc from $E$ to the justification producing $F$
- **Limitation**: Following chains of justifications can be inefficient and may contain cycles

### LTMS (Logic-based TMS, McAllester 1978)
- Adds the rule in clause form to the justification, eliminating arc directedness
- Example: $A \wedge B \Rightarrow C$ gets justification containing clause $\{\neg A, \neg B, C\}$
- Label of any literal can depend on labels of the others in the clause
- Three labels: "true", "false", "unknown"
- Generally based on propositional logic

### ATMS (Assumption-based TMS, de Kleer 1986)
- Each inferred assertion is associated directly with the **sets of assumptions** it depends on (no intermediate assertion records)
- **Task 1** (find support): Every assertion points directly to its assumption sets; no intermediate chain traversal needed
- **Task 2** (find derived): Assumptions point directly to assertions derived from them
- **Task 3** (delete + cascade): Current KB is determined by a "current context" (a set of assumptions). To delete an assumption, remove it from the current context. Derived assertions with no remaining assumption set as a subset of the current context are no longer in the KB. To delete a derived assertion, remove at least one assumption from each of its assumption sets from the current context
- Like JTMSs, ATMSs are a service separate from the reasoner

### SNeBR (SNePS Belief Revision, Martins and Shapiro 1988)
- Unites the ATMS with the reasoner: calculates assumptions of each inferred assertion directly from the inference rule used
- For most common cases: assumptions of inferred assertion = parent(s) of the inference (and-elimination) or union of parents' assumptions (modus ponens)
- Uses **relevance logic** (Anderson and Belnap 1975): paraconsistent, a contradiction does not imply everything
- SNePSwD (Cravo and Martins 1993): extends SNeBR with non-monotonic logic using classical (rather than relevance) logic

### AGM Belief Revision (Alchourron, Gardenfors, Makinson 1985)
- Three operations: **expansion** (add assertion), **contraction** (remove assertion), **revision** (add assertion inconsistent with KB, then restore consistency)
- Revision = contraction followed by expansion
- Two key constraints:
  1. **Minimality of information loss**: The amount of information lost in a belief change should be kept minimal
  2. **Entrenchment-based priority**: Some beliefs are more important/entrenched; retract the least important ones first
- AGM tradition assumes a logically closed, potentially infinite set of assertions
- AGM tradition does not concern itself with implementation; TMS tradition does
- The two traditions are almost completely disjoint in their citations

### Implementing AGM Constraints in TMSs (Section 9)
- **Constraint (i)** (minimality): Choose the culprit whose removal causes the fewest other assertions to be removed. Author knows of no implemented TMS that does this.
- **Constraint (ii)** (entrenchment): Rank assertions by "importance" or "entrenchment" and choose the culprit whose removal causes the least important assertions to be removed. SNePSwD (Cravo and Martins 1993) allows partial importance ordering; user can categorize assertions and use category ordering during belief revision.

### Proposed Future Work
- Assess which existing BRSs satisfy AGM constraints
- Build an experimental BRS on SNePS 2.4 with SNeBR as built-in BRS
- Use ideas from SNePSwD (non-monotonic rules, partial importance ordering)
- Investigate category-based importance ordering from Ehrlich (1995, 1997)
- Apply to data fusion for enhanced situation assessment

## Figures of Interest
This paper contains no figures.

## Results Summary
No experimental results. The contribution is a comparative taxonomy of TMS architectures and AGM theory, plus identification of the gap between the two traditions.

## Limitations
- Very high-level overview; does not go into algorithmic details of any TMS
- Does not present any formal comparison or proof relating TMS properties to AGM postulates
- The proposed future work (building AGM-compliant TMS) was not yet implemented at time of writing
- Author acknowledges not knowing whether the category-based importance ordering from Ehrlich's earlier version of SNePSwD is present in the current version

## Testable Properties
- A JTMS with inverter arcs for non-monotonic rules must propagate label changes in both directions ("in" to "out" AND "out" to "in")
- In an ATMS, deleting a derived assertion requires removing at least one assumption from each of its assumption sets from the current context
- AGM constraint (i): the culprit whose removal minimizes total number of removed assertions should be chosen
- AGM constraint (ii): among possible culprits, the one causing removal of the least entrenched assertions should be chosen
- SNeBR calculates assumption sets per inference rule: for and-elimination, assumptions equal the parent's; for modus ponens, assumptions are the union of parents'

## Relevance to Project
This paper is directly relevant to the propstore's architecture. It provides a clear taxonomy of TMS types and their tradeoffs, identifies the BRS tasks any belief revision system must perform, and bridges the gap between the TMS implementation tradition (already covered by Doyle 1979, McAllester 1978, de Kleer 1986 in this collection) and the AGM formal theory. The AGM constraints on culprit selection (minimality and entrenchment) are directly applicable to how the propstore should handle contradictory claims.

## Open Questions
- [ ] Has the proposed AGM-compliant BRS on SNePS been implemented since 1998?
- [ ] How does the entrenchment-based culprit selection interact with the propstore's existing stance/claim architecture?
- [ ] Can the category-based importance ordering from Ehrlich (1997) be adapted for claim types in the propstore?

## Related Work Worth Reading
- Martins, J.P. and Shapiro, S.C. (1988). A model for belief revision. *Artificial Intelligence*, 35:25-79. [The SNeBR model in detail]
- Cravo, M.R. and Martins, J.P. (1993). SNePSwD: a newcomer to the SNePS family. *JETAI*, 5(2&3):135-148. [Non-monotonic extension with importance ordering]
- Gardenfors, P. and Rott, H. (1995). Belief revision. In *Handbook of Logic in AI and Logic Programming*, vol 4, pp 35-132. [The only cross-tradition citation noted by Shapiro]
- Friedman, N. and Halpern, J.Y. (1996). Belief revision: A critique. In *KR '96*, pp 421-431. [Notes that both AGM postulates and TMS were motivated by chronological backtracking]

## Collection Cross-References

### Already in Collection
- [[Doyle_1979_TruthMaintenanceSystem]] — cited as Doyle (1979); surveyed as the foundational JTMS architecture with dependency graph and IN/OUT labeling.
- [[McAllester_1978_ThreeValuedTMS]] — cited as McAllester (1978); surveyed as the LTMS architecture adding clause-based three-valued labeling.
- [[deKleer_1986_AssumptionBasedTMS]] — cited as de Kleer (1986); surveyed as the ATMS architecture tracking minimal assumption sets per derived assertion.
- [[Martins_1988_BeliefRevision]] — cited as Martins and Shapiro (1988); surveyed as the SNeBR architecture that unites ATMS-style assumption tracking with the reasoner, computing assumption sets per inference rule.
- [[Alchourron_1985_TheoryChange]] — cited as Alchourron, Gardenfors, and Makinson (1985); surveyed as the foundational AGM belief revision paper defining expansion, contraction, and revision postulates.

### New Leads (Not Yet in Collection)
- Cravo, M.R. and Martins, J.P. (1993) — "SNePSwD" — extends SNeBR with non-monotonic rules and partial importance ordering; directly implements AGM entrenchment constraint
- Gardenfors, P. and Rott, H. (1995) — "Belief revision" in Handbook — the only cross-tradition citation Shapiro identifies

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)
- [[Dixon_1993_ATMSandAGM]] — **Strong.** Both papers bridge TMS and AGM traditions. Dixon provides a formal proof of ATMS-AGM equivalence via entrenchment encoding; Shapiro provides a taxonomic survey and proposes building AGM-compliant SNeBR. Complementary contributions: Dixon solves the theoretical bridge, Shapiro identifies the implementation path.
- [[Martins_1983_MultipleBeliefSpaces]] — **Moderate.** The 1983 MBR conference paper introduces the context/belief-space mechanism that Shapiro surveys as part of the SNeBR lineage.
- [[Dung_1995_AcceptabilityArguments]] — **Moderate.** Dung's argumentation frameworks provide an alternative abstract framework for the same belief maintenance problem Shapiro surveys. Both address which beliefs to accept under conflict, but from different traditions (TMS/AGM vs. argumentation).
- [[Reiter_1980_DefaultReasoning]] — **Moderate.** Shapiro's non-monotonic rule format (conditions that must be IN, conditions that must be OUT) directly echoes Reiter's default rules (prerequisite, justification, consequent). Default logic provides the formal underpinning for the non-monotonic TMS extensions Shapiro surveys.
- [[Pollock_1987_DefeasibleReasoning]] — **Moderate.** Pollock's epistemological approach to belief revision (warrant via defeat levels) provides a philosophical complement to the engineering-oriented TMS architectures Shapiro surveys. Both aim for principled culprit selection during contradiction resolution.
