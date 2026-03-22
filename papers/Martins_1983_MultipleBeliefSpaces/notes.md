---
title: "Reasoning in Multiple Belief Spaces"
authors: "Joao P. Martins, Stuart C. Shapiro"
year: 1983
venue: "IJCAI-83"
doi_url: "https://www.ijcai.org/Proceedings/83-1/Papers/088.pdf"
---

# Reasoning in Multiple Belief Spaces

## One-Sentence Summary
Describes MBR (Multiple Belief Reasoner), a reasoning system built on the SWM logic and SNePS network that allows multiple agents' possibly contradictory and hypothetical beliefs to coexist in a single knowledge base, with mechanisms for detecting contradictions within and across belief spaces and recovering from them. *(p.370)*

## Problem Addressed
Previous approaches to contradiction detection and recording (e.g., Doyle's TMS, McAllester's three-valued TMS, McDermott's contexts) did not handle multiple agents with different, possibly conflicting beliefs represented simultaneously in the same knowledge base. *(p.370)* MBR addresses how to: (1) represent beliefs from multiple agents and hypothetical sources in a shared network, (2) partition the knowledge base into per-agent "belief spaces" via contexts, (3) detect contradictions within a single agent's belief space, and (4) recover from those contradictions by identifying and removing culprit hypotheses. *(p.370-371)*

## Key Contributions
- Introduces **contexts** as sets of hypotheses that define a **Belief Space (BS)** -- the set of all propositions derivable from those hypotheses *(p.371)*
- Defines the **Current Belief Space (CBS)** as the BS defined by the **Current Context (CO)** -- the set of all hypotheses currently believed *(p.371)*
- Introduces **supported wffs** of the form `F!:t,a,p` where F is a wff, t is an origin tag, a is the origin set, and p is the restriction set *(p.370)*
- Defines **origin tag (OT)** values: `hyp` (hypothesis), `der` (normally derived wff), `ext` (extended origin set -- not discussed in this paper) *(p.370)*
- Defines the **origin set (OS)** as the set of hypotheses actually used to derive a proposition *(p.370)*
- Defines the **restriction set (RS)** as a set of sets of hypotheses, each of which when combined with the hypotheses in the OS forms an inconsistent set *(p.370)*
- Introduces two SWM inference rules for contradiction handling: **negation introduction (~I)** and **updating of restriction sets (URS)** *(p.371)*
- Shows that contradictions are detected by following only two types of arcs -- no need to explicitly mark propositions as believed/disbelieved, no need to worry about circular proofs, no separate NOGOOD list needed *(p.373)*
- Demonstrates that BS definition via contexts provides power-set-many belief spaces from a single knowledge base *(p.371)*

## Methodology
1. **SWM Logic**: The underlying formal logic for MBR, loosely based on relevance logic [1] and [7]. Distinguished by: recording dependencies of wffs (not irrelevancies), allowing irrelevancies to be introduced, and providing mechanisms for dealing with contradictions. *(p.370)*
2. **SNePS Network Representation**: Propositions are represented as network nodes linked by arcs; hypotheses are stored with their origin sets and restriction sets. *(p.370)*
3. **Belief Space Mechanism**: A context (set of hypotheses) defines a BS. Retrieval operations only return propositions within the CBS, ignoring propositions outside it. *(p.371)*
4. **Contradiction Handling**: Two rules (~I and URS) detect and record contradictions by updating restriction sets. When contradiction is found, culprit hypothesis(es) are identified and disbelieved (dropped from the context). *(p.371)*

## Key Equations

Rule of negation introduction (~I):

$$
\text{From } A\!:\!t,a,p \text{ and } \neg A\!:\!\xi,\beta,\theta \text{, derive } A\&\neg A\!:\!\text{can be deduced}
$$

This means: from the hypotheses in $a \cup \beta$, a contradiction can be derived. The negation of the conjunction of any number of hypotheses in $a \cup \beta$ under an OS containing the remaining hypotheses can be derived. *(p.371)*

Rule of URS (updating of restriction sets):

$$
\text{From } A\!:\!t,a,p \text{ and } \neg A\!:\!\xi,\beta,\theta \text{, we must update the RS of every hypothesis in } a \cup \beta \text{ and of all the wffs derived from them.}
$$

The effect of URS updating is to record the existence of the inconsistent set $a \cup \beta$. *(p.371)*

## Parameters

This paper is primarily architectural/logical. No numerical parameters, constants, or thresholds are defined. *(p.370-373)*

## Implementation Details

### Platform
- Implemented in **Franz Lisp** on a **VAX-11/750** *(p.373)*
- Uses the **SNePS semantic network processing system** [6] *(p.370, p.373)*
- The example presented was obtained from an actual MBR run with minor output formatting changes *(p.372)*

### Data Structures
- **Supported wff**: `F!:t,a,p` -- a 4-tuple of (formula, origin-tag, origin-set, restriction-set) *(p.370)*
- **Origin tag (OT)**: `hyp` for hypotheses, `der` for derived wffs *(p.370)*
- **Origin set (OS)**: set of hypotheses used in derivation; once derived, a proposition's OT and OS remain constant *(p.370)*
- **Restriction set (RS)**: set of sets of hypotheses; RS changes as new contradictions are discovered. Each element of RS represents a set of hypotheses that, when combined with those in the OS, yield inconsistency *(p.370)*
- **Hypotheses**: propositions which the user explicitly wanted the system to believe; they have OT=hyp and their OS is the singleton set containing themselves *(p.370)*

### Context and Belief Space
- A **context** = a set of hypotheses *(p.371)*
- **Belief Space (BS)** = all propositions in the context plus all propositions derivable from them in SWM *(p.371)*
- **Current Context (CO)** = the set of hypotheses currently believed by the user *(p.371)*
- **Current Belief Space (CBS)** = the BS defined by CO *(p.371)*
- Retrieval operations only return propositions within CBS, ignoring all others *(p.371)*
- Contexts delimit smaller knowledge bases (Belief Spaces) within the larger knowledge base *(p.371)*
- At any point, the set of all hypotheses in the system constitutes a **total context** defining the **total belief space (Total BS)** *(p.371)*

### Contradiction Detection and Recovery
1. If only one of the contradictory wffs belongs to the CBS: the contradiction is recorded via URS application, but nothing else happens. The effect is recording that some set of hypotheses containing the CC is now known to be inconsistent. *(p.371)*
2. If both contradictory wffs belong to the CBS: the rule of URS is applied AND the rule of ~I is also applied. New wffs are added to the knowledge base, and the CC is revised. *(p.371)*
3. MBR relies on only the two rules ~I and URS; there is no explicit contradiction detection mechanism -- the contradiction is a consequence of the two rules' application. *(p.371)*
4. When CBS revision occurs, the system must select which hypothesis to drop -- it either selects automatically or asks the user for a culprit choice. *(p.371)*

### Key Properties
- No need to explicitly mark propositions as believed or disbelieved *(p.373)*
- No need to worry about circular proofs *(p.373)*
- No need to keep a separate data structure to record previous contradictions (e.g., Doyle's NOGOOD list) -- the RS of each hypothesis distributes this information *(p.373)*
- Contradiction detection uses only two types of arcs *(p.373)*
- RSs waive the need for a separate contradiction data structure -- all contradiction information is distributed across the RS of each hypothesis *(p.373)*
- In MBR, propositions are represented in the SNePS network; the OS and RS are associated with nodes, not with arcs *(p.373)*
- The number of sets that has to be checked for inconsistency at any given time is bounded by the number of elements in the restriction set of the derived proposition *(p.373)*

## Figures of Interest
- **Fig 1 (p.372):** Hypotheses in the knowledge base for the meeting scheduling example -- shows hyp1 through hyp7 with their supported wff representations (e.g., `hyp1!:hyp,{hyp1},{}` meaning "Stu has free the morning")
- **Fig 2 (p.372):** Wffs derived from "Stu-schedule" context -- shows wff1 through wff4 with their origin sets and restriction sets (e.g., `wff1!:der,{hyp1,hyp2,hyp3},{}` meaning "the best time for the meeting is in the afternoon")
- **Fig 3 (p.372):** Wffs derived from "Tony-schedule" context -- shows wff5 and wff6 with their derivation from {hyp4,hyp5,hyp6,hyp7}
- **Fig 4 (p.372):** Knowledge base after URS rule application -- shows updated wff1 through wff6 with modified restriction sets recording the inconsistency between the two schedules
- **Fig 5 (p.373):** Wffs derived within the CC (combined context of Stu-schedule and Tony-schedule) -- shows wff1' and wff2' after context combination, with updated restriction sets reflecting that {hyp1,hyp2,hyp3,hyp4,hyp5,hyp6,hyp7} is inconsistent

## Results Summary
MBR successfully handles the meeting scheduling example with two users (Stu and Tony) whose schedules contain contradictions. The system: *(p.372-373)*
1. Detects that merging Stu and Tony's belief spaces creates an inconsistency (both need the same time slot) *(p.372)*
2. Records the inconsistency through URS updates to restriction sets *(p.372)*
3. Identifies the culprit hypothesis (hyp1) through the RS and ~I rule *(p.373)*
4. Drops the culprit from the context, restoring consistency *(p.373)*

## Annotated Example Detail
- The example involves scheduling a faculty meeting. Stu wants to attend, entering 7 hypotheses about his and Tony's schedule. *(p.372)*
- "Stu-schedule" context = {hyp1, hyp2, hyp3}; "Tony-schedule" context = {hyp4, hyp5, hyp6, hyp7} *(p.372)*
- Stu's reasoning derives wff1 ("best time is afternoon") from {hyp1, hyp2, hyp3} *(p.372)*
- Tony's reasoning derives wff5 ("best time is afternoon") and wff6 ("reports too long, meeting will go on all afternoon") *(p.372)*
- When contexts are combined, MBR detects wff2 ("Stu can attend the meeting in the afternoon") contradicts wff6 implications *(p.372-373)*
- Someone new wants to schedule, and when all 7 hypotheses form the CC, the system detects the contradiction and must revise *(p.373)*

## Limitations
- Extended origin sets (T=ext) are not discussed in this paper *(p.370)*
- The paper describes only a "small feature" of MBR -- the contradiction detection and recording mechanism *(p.370)*
- The example is a simplified meeting scheduling scenario; scalability to large multi-agent systems is not evaluated *(p.372-373)*
- No formal complexity analysis is provided *(p.370-373)*
- The selection of which hypothesis to drop when resolving a contradiction is not deeply explored *(p.371)*

## Distinguishing Characteristics of MBR
- Based on a logic designed for belief representation (SWM), not classical logic *(p.373)*
- By defining a context and a CBS, a single knowledge base can be used for any number of reasoners -- the same network supports 2^n belief spaces from n hypotheses *(p.373)*
- When contradiction is detected, the culprit propositions are identified through their restriction sets -- removal is done just by dropping them from the context, not by deleting nodes *(p.373)*

## Testable Properties
- A context defines a unique Belief Space: two different contexts may yield different BSs from the same knowledge base *(p.371)*
- Once a proposition is derived, its OT and OS remain constant (only RS changes) *(p.370)*
- If a contradiction is found between two wffs, one or both belonging to the CBS, the RS of every hypothesis in their combined OS is updated *(p.371)*
- If both contradictory wffs are in the CBS, the ~I rule fires in addition to URS, causing CC revision *(p.371)*
- Retrieval within a CBS returns only propositions whose OS is a subset of the current context *(p.371)*
- The RS records inconsistency information without requiring a separate NOGOOD data structure *(p.373)*
- The number of inconsistency checks is bounded by the cardinality of the RS of the derived proposition *(p.373)*

## Relevance to Project
This paper is a direct precursor to de Kleer's ATMS work (1986) already in the collection. MBR's approach to multiple belief spaces, contexts, and contradiction handling via origin sets and restriction sets represents an alternative architecture for the same core problems the ATMS solves: maintaining multiple hypothetical worlds simultaneously and detecting/recording inconsistencies. The context/belief-space mechanism provides a different perspective on how to partition assumptions and manage per-agent reasoning, which is relevant to the propstore's assumption-tracking and multi-perspective belief management.

## Open Questions
- [ ] How does MBR's performance compare with de Kleer's ATMS on the same problem instances?
- [ ] What is the relationship between MBR's restriction sets and the ATMS's nogood environments?
- [ ] How does the choice of culprit hypothesis during contradiction recovery affect soundness?
- [ ] Does the SWM logic's treatment of relevance (vs. classical logic) create meaningful differences in derivable conclusions?

## Related Work Worth Reading
- [1] Anderson A. and Belnap N., "Entailment: The Logic of Relevance and Necessity", Princeton University Press, 1975 -- The relevance logic foundation for SWM *(p.370)*
- [2] Doyle J., "A Truth Maintenance System", Artificial Intelligence 12:3, 1979 -- The original TMS that MBR improves upon (already in collection) *(p.370)*
- [3] Martins J., "Reasoning in Multiple Belief Spaces", Ph.D. Dissertation, SUNY at Buffalo, May 1983 -- Full dissertation with complete details *(p.373)*
- [4] McAllester D., "An Outlook on Truth Maintenance", MIT AI Lab, 1980 -- Three-valued TMS approach *(p.373)*
- [5] McDermott D., "Contexts and Data Dependencies", Department of Computer Science, Yale University, 1982 -- Alternative approach to contextual reasoning *(p.373)*
- [6] Shapiro S., "The SNePS semantic network processing system", in Associative Networks, N.v.Findler (ed.), Academic Press, 1979 -- The underlying network system *(p.373)*
- [7] Shapiro S. and Wand M., "The Relevance of Relevance", Computer Science Department, Indiana University, 1976 -- Theoretical basis for SWM's relevance constraints *(p.373)*

## Collection Cross-References

### Already in Collection
- [[Doyle_1979_TruthMaintenanceSystem]] -- cited as [2]; the original TMS that MBR improves upon. MBR's restriction sets replace Doyle's NOGOOD list, and MBR's context/belief-space mechanism replaces Doyle's single-state architecture.
- [[McAllester_1978_ThreeValuedTMS]] -- cited as [4]; referenced as a prior approach to contradiction handling that MBR extends with multi-agent belief spaces.
- [[McDermott_1983_ContextsDataDependencies]] -- cited as [5]; presents an alternative approach to contextual reasoning via data pools and data dependencies that MBR's context/belief-space mechanism can be compared against.

### New Leads (Not Yet in Collection)
- Anderson A. and Belnap N. (1975) -- "Entailment: The Logic of Relevance and Necessity" -- the relevance logic foundation for SWM
- Shapiro S. and Wand M. (1976) -- "The Relevance of Relevance" -- theoretical basis for SWM's relevance constraints

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- [[Martins_1988_BeliefRevision]] -- cites this as [28]; this is the conference paper version of the full model presented in the 1988 journal paper
- [[deKleer_1986_AssumptionBasedTMS]] -- cites Martins [13] as a related multi-context approach
- [[Shapiro_1998_BeliefRevisionTMS]] -- surveys MBR/SNeBR as one of four TMS architectures, describing its context/belief-space mechanism

### Conceptual Links (not citation-based)
- [[deKleer_1986_AssumptionBasedTMS]] -- **Strong.** Both systems maintain multiple hypothetical contexts simultaneously. MBR uses contexts (sets of hypotheses) to define belief spaces with restriction sets recording inconsistencies; the ATMS uses environments with labels and nogoods. MBR's restriction sets are functionally analogous to the ATMS's nogoods, and MBR's contexts map to ATMS environments. Key difference: MBR operates within a relevance logic (SWM) while the ATMS is logic-independent.
- [[Martins_1988_BeliefRevision]] -- **Strong.** The 1988 paper is the full journal-length presentation of the MBR model introduced in this 1983 conference paper, adding formal proofs, the ext origin tag, nonstandard connectives, and the SNeBR implementation.
- [[Dixon_1993_ATMSandAGM]] -- **Moderate.** Dixon bridges ATMS and AGM belief revision; MBR's interactive culprit selection during contradiction recovery is an informal precursor to the entrenchment-based culprit selection that Dixon formalizes.
