---
title: "Belief Revision and Truth Maintenance Systems: An Overview and a Proposal"
authors: "Stuart C. Shapiro"
year: 1998
venue: "CSE Technical Report 98-10, State University of New York at Buffalo"
doi_url: "https://cse.buffalo.edu/~shapiro/Papers/br-overview.pdf"
---

# Belief Revision and Truth Maintenance Systems: An Overview and a Proposal

## One-Sentence Summary
This paper provides a high-level comparative survey of truth maintenance systems (JTMSs, LTMSs, ATMSs) and AGM belief revision theory, identifying that the two traditions have developed in near-complete isolation, and proposes building a TMS implementation that satisfies AGM postulates. *(p.1)*

## Problem Addressed
The TMS literature (AI systems engineering) and the AGM belief revision literature (formal epistemology/logic) address the same fundamental problem --- maintaining consistency in a knowledge base when beliefs change --- yet almost no publication in either tradition cites any publication in the other. *(p.7)* The paper surveys both and proposes unifying them. *(p.1)*

## Key Contributions
- Defines a common framework: a Knowledge-Based System (KBS) consisting of a knowledge base (KB) of assertions, inference methods, and a belief revision subsystem (BRS/TMS) *(p.1)*
- Identifies three core BRS tasks: (1) find derivation support for an assertion, (2) find assertions derived from an assumption, (3) delete an assertion and all its dependents *(p.2--3)*
- Surveys four TMS architectures (JTMS, LTMS, ATMS, SNeBR) with how each handles the three BRS tasks *(p.3--6)*
- Surveys AGM belief revision (expansion, contraction, revision) and its two key constraints on culprit selection *(p.6--7)*
- Observes that the two traditions are nearly disjoint in citations *(p.7)*
- Proposes implementing a BRS on top of SNePS/SNeBR/SNePSwD that satisfies AGM constraints *(p.7--8)*

## Methodology
Comparative literature survey with a proposal for future experimental work. No formal proofs or experiments are presented; the contribution is taxonomic and architectural. *(p.1)*

## Key Equations

This paper contains no formal equations. The logical notation used is informal:

$$
\{A_1, \ldots, A_n\}\{B_1, \ldots, B_m\} \Rightarrow C
$$
Where: $A_i$ are conditions that must be in the KB, $B_j$ are conditions that must NOT be in the KB (non-monotonic), and $C$ is the conclusion. This is the general form of a non-monotonic rule. *(p.3)*

## Parameters

This is a survey/overview paper with no experimental parameters.

## Implementation Details

### KBS Architecture
A Knowledge-Based System consists of: *(p.1)*
- A **knowledge base (KB)** of assertions, which can be:
  - Ground atomic propositions ("facts") *(p.1--2)*
  - Closed non-atomic propositions with connectives/quantifiers ("rules") *(p.2)*
  - User-supplied assumptions/hypotheses *(p.2)*
  - Inferred/derived assertions *(p.2)*
- A set of **inference methods** (sound with respect to the logic's semantics) *(p.1)*
- A **belief revision system (BRS)** / truth maintenance system (TMS) *(p.2)*

### Reasons for Needing Belief Revision
KBSs may need belief revision because: *(p.2)*
- Assertions are entered by/from multiple sources that may contradict one another *(p.2)*
- New assertions may contradict old ones because the world has changed *(p.2)*
- Old assertions might be retracted because the world changed or the source no longer wants them in the KB *(p.2)*

### BRS Responsibilities
A BRS is a subsystem of a KBS intended to solve: *(p.2)*
- Notice when the KBS contains a contradiction *(p.2)*
- Identify the assertions used to derive the contradiction ("possible culprits") *(p.2)*
- Choose one as the culprit *(p.2)*
- Delete the culprit from the KB *(p.2)*
- Delete all assertions derived from the deleted culprit *(p.2)*
- Prevent the reintroduction of deleted contradictions *(p.2)*

### Three Core BRS Tasks
1. **Find derivation support**: Given an assertion, find the assertions used to derive it *(p.2)*
2. **Find derived assertions**: Given an assumption, find all assertions derived from it *(p.2)*
3. **Delete and cascade**: Delete an assertion and all assertions derived from it from the KB *(p.3)*

### Dependency-Directed Backtracking (Section 2)
- The first idea leading to TMSs was dependency-directed backtracking *(p.3)*
- In chronological backtracking, assertions $A_1, \ldots, A_n$ are asserted in order; when $A_{n+1}$ yields a contradiction, $A_n$ would be retracted and $A_{n-1}$ re-added, etc. --- very inefficient *(p.3)*
- More efficient to point the contradiction directly to the assertions it depends on, so the right ones can be retracted immediately *(p.3)*
- This idea was called "dependency-directed backtracking" (Stallman and Sussman, 1977) *(p.3)*

### JTMS (Justification-based TMS, Doyle 1979)
- Uses propositional logic only, atomic propositions and negations ("literals") *(p.3)*
- Dependency graph with two vertex types: **nodes** (literals) and **justifications** *(p.3)*
- Arcs go from nodes to justifications and from justifications to nodes *(p.3)*
- Nodes labeled "in" or "out" (in KB or not) *(p.3)*
- Assumptions: nodes with no arcs coming into their justifications *(p.3)*
- **Task 1** (find support): Follow arcs backward from assertion to justifications to their input nodes, recursively to assumptions *(p.4)*
- **Task 2** (find derived): Follow arcs forward from assumption to justifications it points to, to nodes those justify, recursively *(p.4)*
- **Task 3** (delete + cascade): If assumption, set label to "out" and propagate forward, changing dependent nodes to "out" unless they have an alternative justification or are already "out". If not an assumption, find its supporting assumptions (task 1), choose a culprit, delete it (task 3, first clause), repeat until the target assertion's label is "out" *(p.4)*
- **Non-monotonic extension**: "inverter" arcs from justifications to literals that must be "out" for the justification to hold. Rule $\{D\}\{E\} \Rightarrow F$: normal arc from $D$, inverter arc from $E$ to the justification producing $F$ *(p.4)*
- A non-monotonic JTMS works like a monotonic JTMS for tasks 1-3, but for task 3 it needs to handle the more general problem of changing a label either from "in" to "out" or from "out" to "in", and propagating the change *(p.4)*
- An assertion may be derived from the KB by changing the label of one of its assumptions from "out" to "in" *(p.4)*
- **Limitation**: Following chains of justifications can be inefficient and may contain cycles *(p.4--5)*

### LTMS (Logic-based TMS, McAllester 1978)
- Adds the rule in clause form to the justification, eliminating arc directedness *(p.5)*
- Example: $A \wedge B \Rightarrow C$ gets justification containing clause $\{\neg A, \neg B, C\}$ *(p.5)*
- Label of any literal can depend on labels of the others in the clause *(p.5)*
- Three labels: "true", "false", "unknown" *(p.5)*
- Generally based on propositional logic *(p.5)*

### TMSs as Services (Section 5)
- JTMSs are generally implemented as service systems separate from the reasoning systems *(p.5)*
- Each time the reasoning system produces a new assertion, it sends the new assertion and its justifications to the JTMS, which records it *(p.5)*
- In such a JTMS, there is no logical principle connecting an assertion to its justifications *(p.5)*
- LTMSs associate the reasoner more closely with the TMS by using the logic of the justification clauses for revision *(p.5)*

### ATMS (Assumption-based TMS, de Kleer 1986)
- Each inferred assertion is associated directly with the **sets of assumptions** it depends on (no intermediate assertion records) *(p.5)*
- If a contradiction occurs, the assumptions associated with the contradiction form the set of possible culprits *(p.5)*
- That set of assumptions may be recorded as being contradictory, and any operation that might form a superset of that set may be blocked *(p.5)*
- **Task 1** (find support): Every assertion points directly to its assumption sets; no intermediate chain traversal needed *(p.5)*
- **Task 2** (find derived): Assumptions point directly to assertions derived from them *(p.5)*
- **Task 3** (delete + cascade): Current KB is determined by a "current context" (a set of assumptions). To delete an assumption, remove it from the current context. Derived assertions with no remaining assumption set as a subset of the current context are no longer in the KB. To delete a derived assertion, remove at least one assumption from each of its assumption sets from the current context *(p.6)*
- Like JTMSs, ATMSs are a service separate from the reasoner *(p.6)*

### SNeBR (SNePS Belief Revision, Martins and Shapiro 1988)
- Unites the ATMS with the reasoner: calculates assumptions of each inferred assertion directly from the inference rule used *(p.6)*
- For most common cases: assumptions of inferred assertion = parent(s) of the inference (and-elimination) or union of parents' assumptions (modus ponens) *(p.6)*
- Uses **relevance logic** (Anderson and Belnap 1975): paraconsistent, a contradiction does not imply everything *(p.6)*
- SNePS handles paraconsistent logic using a variant of relevance logic *(p.6)*
- SNePSwD (Cravo and Martins 1993): extends SNeBR with non-monotonic logic using classical (rather than relevance) logic, but uses classical non-monotonic logic *(p.6)*

### Choosing the Culprit (Section 7)
- JTMSs, LTMSs, and ATMSs are all capable of finding the possible culprits (the set of assumptions underlying the contradiction) *(p.6)*
- How to choose the culprit to blame from the set of possible culprits is much less clear *(p.6)*
- SNeBR (Martins and Shapiro, 1988) presents all the possible culprits to the user for him or her to choose *(p.6)*

### AGM Belief Revision (Alchourron, Gardenfors, Makinson 1985)
- A "theory change" tradition, takes as its starting point the postulates for belief revision (Alchourron et al., 1985), though with roots at least as far back as Gardenfors (1978) *(p.6)*
- Three operations: **expansion** (add assertion), **contraction** (remove assertion), **revision** (add assertion inconsistent with KB, then restore consistency) *(p.6--7)*
- Revision = contraction followed by expansion *(p.7)*
- Revision can be accomplished by a step of contraction followed by a step of reorganization *(p.7)*
- Two key constraints:
  1. **Minimality of information loss** (constraint i): The amount of information lost in a belief change should be kept minimal *(p.7)*
  2. **Entrenchment-based priority** (constraint ii): Some beliefs are more important/entrenched; retract the least important ones first *(p.7)*
- AGM tradition assumes a logically closed, potentially infinite set of assertions *(p.7)*
- AGM tradition is a "very high level way" that assumes a KB that "is logically closed, a potentially infinite set of assertions" --- not concerned with implementation *(p.7)*
- AGM tradition does not concern itself with implementation; TMS tradition does *(p.7)*
- The two traditions are almost completely disjoint in their citations *(p.7)*
- Almost no publication in one tradition cites any publication in the other tradition *(p.7)*
- Most stunning is the fact that these two traditions seem to ignore each other *(p.7)*
- The only notable exception: Gardenfors and Rott (1995) *(p.7)*
- An interesting example: Friedman and Halpern (1996) note that both AGM postulates and TMS were motivated by chronological backtracking --- but do not refer to any publication in the TMS tradition *(p.7)*

### Implementing AGM Constraints in TMSs (Section 9)
- **Constraint (i)** (minimality): Choose the culprit whose removal causes the fewest other assertions to be removed. Author knows of no implemented TMS that does this. *(p.7)*
- **Constraint (ii)** (entrenchment): Rank assertions by "importance" or "entrenchment" and choose the culprit whose removal causes the least important assertions to be removed. *(p.7)*
- SNePSwD (Cravo and Martins, 1993) allows the user to specify an explicit ordering among specific assertions, and allows the user to sort assertions into categories with an importance ordering among the categories, and then uses this ordering used in belief revision *(p.7--8)*
- The author does not know whether the category-based explicit ordering feature in the earlier version of SNePSwD was in the current version at time of writing, or was added by Ehrlich to SNePSwD *(p.8)*

### Proposed Future Work (Section 10)
- Propose to continue investigating belief revision and truth maintenance systems, especially for the domain of data fusion systems for enhanced situation assessment *(p.7--8)*
- Assess which existing BRSs satisfy AGM constraints *(p.8)*
- Build an experimental BRS on SNePS 2.4 with SNeBR as built-in BRS *(p.8)*
- Build on a knowledge representation and reasoning system with SNePS (Shapiro and SNePS Implementation Group, 1998), using SNeBR (Martins and Shapiro, 1988) as its BRS *(p.8)*
- Use ideas from SNePSwD (non-monotonic rules, partial importance ordering) *(p.8)*
- Investigate category-based importance ordering from Ehrlich (1995, 1997) *(p.8)*
- Apply to data fusion for enhanced situation assessment *(p.8)*

## Figures of Interest
This paper contains no figures.

## Results Summary
No experimental results. The contribution is a comparative taxonomy of TMS architectures and AGM theory, plus identification of the gap between the two traditions. *(p.1)*

## Arguments Against Prior Work

### Against JTMSs *(p.4--5)*
- Following chains of justifications to find support can be inefficient, and those chains might contain cycles *(p.4--5)*
- In a JTMS implemented as a service system, there is no logical principle connecting an assertion to its justifications --- any assertion can be sent with any justification, so the JTMS has no way to verify correctness *(p.5)*
- The problems with JTMSs (inefficient chain-following, possible cycles) were among the motivations for ATMSs *(p.5)*

### Against LTMSs *(p.5)*
- LTMSs are generally based on propositional logic only, limiting their expressiveness *(p.5)*
- While LTMSs eliminate arc directedness by adding the rule in clause form, they still share the fundamental chain-following limitations of JTMSs for finding support *(p.5)*

### Against ATMSs *(p.5--6)*
- ATMSs are implemented as service systems separate from the reasoner, so there is no record of intermediate assertions --- every assertion points directly to assumption sets but the derivation chain is lost *(p.5--6)*
- Like JTMSs, ATMSs as service systems have no logical principle connecting assertions to their assumption sets *(p.5--6)*

### Against Chronological Backtracking *(p.3)*
- In chronological backtracking, if assertions $A_1, \ldots, A_n$ are asserted in order and $A_{n+1}$ yields a contradiction, the system backtracks to $A_n$, then $A_{n-1}$, etc. --- this is very inefficient because the actual culprit may be far back in the ordering *(p.3)*
- Dependency-directed backtracking was invented specifically to address this inefficiency by pointing the contradiction directly to the assertions it actually depends on *(p.3)*

### Against the Two-Tradition Divide *(p.7)*
- The TMS tradition and the AGM belief revision tradition address the same fundamental problem but have developed in near-complete isolation, with almost no publication in either tradition citing any publication in the other *(p.7)*
- This is "most stunning" because both traditions were motivated by the same problem: chronological backtracking. Friedman and Halpern (1996) explicitly note that both AGM postulates and TMS were motivated by chronological backtracking, yet their paper does not refer to any publication in the TMS tradition *(p.7)*
- The AGM tradition assumes a logically closed, potentially infinite set of assertions and is "not concerned with implementation" --- a very high-level view that ignores practical engineering concerns *(p.7)*
- The TMS tradition is concerned with implementation but ignores the formal constraints on culprit selection that AGM provides *(p.7)*

### Against Existing Culprit Selection *(p.6--7)*
- JTMSs, LTMSs, and ATMSs can all identify the set of possible culprits, but how to choose the actual culprit from that set is "much less clear" *(p.6)*
- SNeBR's approach of presenting all possible culprits to the user to choose is a practical solution but does not automate the selection *(p.6)*
- The author knows of no implemented TMS that satisfies AGM constraint (i) (minimality of information loss) *(p.7)*

## Design Rationale

### Why unify TMS and AGM *(p.7--8)*
The two traditions address the same fundamental problem --- maintaining consistency when beliefs change --- but from opposite ends. The TMS tradition provides efficient implementation mechanisms (dependency graphs, assumption sets, label propagation) but lacks principled criteria for culprit selection. The AGM tradition provides formal constraints on what constitutes rational belief revision (minimality, entrenchment) but ignores implementation. A unified approach would provide both principled culprit selection and efficient implementation. *(p.7--8)*

### Why SNeBR as the starting point *(p.6, 8)*
SNeBR (Martins and Shapiro 1988) is unique among TMS architectures in uniting the ATMS with the reasoner: it calculates assumption sets directly from the inference rule used, rather than accepting arbitrary justifications from a separate reasoning system. This tighter coupling means the assumption-set computation is logically grounded rather than arbitrary. SNeBR also uses relevance logic, making it paraconsistent --- a contradiction does not imply everything. *(p.6)*

### Why category-based importance ordering *(p.7--8)*
AGM constraint (ii) requires ranking beliefs by "entrenchment" and choosing the least entrenched culprit. SNePSwD (Cravo and Martins 1993) implements this by allowing users to sort assertions into categories with importance orderings. Ehrlich (1995, 1997) extends this with vocabulary expansion and explicit ordering among specific assertions. Category-based ordering provides a practical mechanism for implementing the abstract AGM entrenchment requirement. *(p.7--8)*

### Why three BRS tasks as the comparison framework *(p.2--3)*
The three tasks --- (1) find derivation support, (2) find derived assertions, (3) delete and cascade --- are common to all BRS/TMS architectures and provide a uniform basis for comparison. Each TMS type (JTMS, LTMS, ATMS, SNeBR) can be evaluated by how efficiently and correctly it handles each task. *(p.2--3)*

## Limitations
- Very high-level overview; does not go into algorithmic details of any TMS *(p.1)*
- Does not present any formal comparison or proof relating TMS properties to AGM postulates *(p.7)*
- The proposed future work (building AGM-compliant TMS) was not yet implemented at time of writing *(p.8)*
- Author acknowledges not knowing whether the category-based importance ordering from Ehrlich's earlier version of SNePSwD is present in the current version *(p.8)*

## Testable Properties
- A JTMS with inverter arcs for non-monotonic rules must propagate label changes in both directions ("in" to "out" AND "out" to "in") *(p.4)*
- In an ATMS, deleting a derived assertion requires removing at least one assumption from each of its assumption sets from the current context *(p.6)*
- AGM constraint (i): the culprit whose removal minimizes total number of removed assertions should be chosen *(p.7)*
- AGM constraint (ii): among possible culprits, the one causing removal of the least entrenched assertions should be chosen *(p.7)*
- SNeBR calculates assumption sets per inference rule: for and-elimination, assumptions equal the parent's; for modus ponens, assumptions are the union of parents' *(p.6)*
- In a JTMS, there is no logical principle connecting an assertion to its justifications --- any assertion can be sent to the JTMS with any justification *(p.5)*
- ATMS records contradictory assumption sets and blocks any operation that might form a superset of a contradictory set *(p.5)*

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
- [[Doyle_1979_TruthMaintenanceSystem]] — cited as Doyle (1979); surveyed as the foundational JTMS architecture with dependency graph and IN/OUT labeling. *(p.3--4)*
- [[McAllester_1978_ThreeValuedTMS]] — cited as McAllester (1978); surveyed as the LTMS architecture adding clause-based three-valued labeling. *(p.5)*
- [[deKleer_1986_AssumptionBasedTMS]] — cited as de Kleer (1986); surveyed as the ATMS architecture tracking minimal assumption sets per derived assertion. *(p.5--6)*
- [[Martins_1988_BeliefRevision]] — cited as Martins and Shapiro (1988); surveyed as the SNeBR architecture that unites ATMS-style assumption tracking with the reasoner, computing assumption sets per inference rule. *(p.6)*
- [[Alchourron_1985_TheoryChange]] — cited as Alchourron, Gardenfors, and Makinson (1985); surveyed as the foundational AGM belief revision paper defining expansion, contraction, and revision postulates. *(p.6--7)*

### New Leads (Not Yet in Collection)
- Cravo, M.R. and Martins, J.P. (1993) — "SNePSwD" — extends SNeBR with non-monotonic rules and partial importance ordering; directly implements AGM entrenchment constraint *(p.6, 7--8)*
- Gardenfors, P. and Rott, H. (1995) — "Belief revision" in Handbook — the only cross-tradition citation Shapiro identifies *(p.7)*
- Stallman, R. and Sussman, G.J. (1977) — "Forward reasoning and dependency-directed backtracking" — origin of dependency-directed backtracking idea *(p.3)*
- Ehrlich, K. (1995, 1997) — vocabulary expansion and category-based importance ordering for SNePSwD *(p.8)*

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
