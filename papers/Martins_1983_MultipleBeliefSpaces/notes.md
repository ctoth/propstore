---
title: "Reasoning in Multiple Belief Spaces"
authors: "Joao P. Martins, Stuart C. Shapiro"
year: 1983
venue: "IJCAI-83"
doi_url: "https://www.ijcai.org/Proceedings/83-1/Papers/088.pdf"
---

# Reasoning in Multiple Belief Spaces

## One-Sentence Summary
Describes MBR (Multiple Belief Reasoner), a reasoning system built on the SWM logic and SNePS network that allows multiple agents' possibly contradictory and hypothetical beliefs to coexist in a single knowledge base, with mechanisms for detecting contradictions within and across belief spaces and recovering from them.

## Problem Addressed
Previous approaches to contradiction detection and recording (e.g., Doyle's TMS, McAllester's three-valued TMS, McDermott's contexts) did not handle multiple agents with different, possibly conflicting beliefs represented simultaneously in the same knowledge base. MBR addresses how to: (1) represent beliefs from multiple agents and hypothetical sources in a shared network, (2) partition the knowledge base into per-agent "belief spaces" via contexts, (3) detect contradictions within a single agent's belief space, and (4) recover from those contradictions by identifying and removing culprit hypotheses.

## Key Contributions
- Introduces **contexts** as sets of hypotheses that define a **Belief Space (BS)** — the set of all propositions derivable from those hypotheses
- Defines the **Current Belief Space (CBS)** as the BS defined by the **Current Context (CO)** — the set of all hypotheses currently believed
- Introduces **supported wffs** of the form `F!:t,a,p` where F is a wff, t is an origin tag, a is the origin set, and p is the restriction set
- Defines **origin tag (OT)** values: `hyp` (hypothesis), `der` (normally derived wff), `ext` (extended origin set — not discussed in this paper)
- Defines the **origin set (OS)** as the set of hypotheses actually used to derive a proposition
- Defines the **restriction set (RS)** as a set of sets of hypotheses, each of which when combined with the hypotheses in the OS forms an inconsistent set
- Introduces two SWM inference rules for contradiction handling: **negation introduction (~I)** and **updating of restriction sets (URS)**
- Shows that contradictions are detected by following only two types of arcs — no need to explicitly mark propositions as believed/disbelieved, no need to worry about circular proofs, no separate NOGOOD list needed
- Demonstrates that BS definition via contexts provides power-set-many belief spaces from a single knowledge base

## Methodology
1. **SWM Logic**: The underlying formal logic for MBR, loosely based on relevance logic [1] and [7]. Distinguished by: recording dependencies of wffs (not irrelevancies), allowing irrelevancies to be introduced, and providing mechanisms for dealing with contradictions.
2. **SNePS Network Representation**: Propositions are represented as network nodes linked by arcs; hypotheses are stored with their origin sets and restriction sets.
3. **Belief Space Mechanism**: A context (set of hypotheses) defines a BS. Retrieval operations only return propositions within the CBS, ignoring propositions outside it.
4. **Contradiction Handling**: Two rules (~I and URS) detect and record contradictions by updating restriction sets. When contradiction is found, culprit hypothesis(es) are identified and disbelieved (dropped from the context).

## Key Equations

Rule of negation introduction (~I):

$$
\text{From } A\!:\!t,a,p \text{ and } \neg A\!:\!\xi,\beta,\theta \text{, derive } A\&\neg A\!:\!\text{can be deduced}
$$

This means: from the hypotheses in $a \cup \beta$, a contradiction can be derived. The negation of the conjunction of any number of hypotheses in $a \cup \beta$ under an OS containing the remaining hypotheses can be derived.

Rule of URS (updating of restriction sets):

$$
\text{From } A\!:\!t,a,p \text{ and } \neg A\!:\!\xi,\beta,\theta \text{, we must update the RS of every hypothesis in } t \cup \xi \text{ and of all the wffs derived from them.}
$$

The effect of URS updating is to record the existence of the inconsistent set $a \cup \beta$.

## Parameters

This paper is primarily architectural/logical. No numerical parameters, constants, or thresholds are defined.

## Implementation Details

### Platform
- Implemented in **Franz Lisp** on a **VAX-11/750**
- Uses the **SNePS semantic network processing system** [6]
- The example presented was obtained from an actual MBR run with minor output formatting changes

### Data Structures
- **Supported wff**: `F!:t,a,p` — a 4-tuple of (formula, origin-tag, origin-set, restriction-set)
- **Origin tag (OT)**: `hyp` for hypotheses, `der` for derived wffs
- **Origin set (OS)**: set of hypotheses used in derivation; once derived, a proposition's OT and OS remain constant
- **Restriction set (RS)**: set of sets of hypotheses; RS changes as new contradictions are discovered. Each element of RS represents a set of hypotheses that, when combined with those in the OS, yield inconsistency

### Context and Belief Space
- A **context** = a set of hypotheses
- **Belief Space (BS)** = all propositions in the context plus all propositions derivable from them in SWM
- **Current Context (CO)** = the set of hypotheses currently believed by the user
- **Current Belief Space (CBS)** = the BS defined by CO
- Retrieval operations only return propositions within CBS, ignoring all others
- Contexts delimit smaller knowledge bases (Belief Spaces) within the larger knowledge base

### Contradiction Detection and Recovery
1. If only one of the contradictory wffs belongs to the CBS: the contradiction is recorded via URS application, but nothing else happens. The effect is recording that some set of hypotheses containing the CC is now Known to be inconsistent.
2. If both contradictory wffs belong to the CBS: the rule of URS is applied AND the rule of ~I is also applied. New wffs are added to the knowledge base, and the CC is revised.

### Key Properties
- No need to explicitly mark propositions as believed or disbelieved
- No need to worry about circular proofs
- No need to keep a separate data structure to record previous contradictions (e.g., Doyle's NOGOOD list)
- Contradiction detection uses only two types of arcs
- RSs waive the need for a separate contradiction data structure — all contradiction information is distributed across the RS of each hypothesis

## Figures of Interest
- **Fig 1 (page 3):** Hypotheses in the knowledge base for the meeting scheduling example — shows hyp1 through hyp7 with their supported wff representations
- **Fig 2 (page 3):** Wffs derived from "Stu-schedule" context — shows wff1 through wff4 with their origin sets and restriction sets
- **Fig 3 (page 3):** Wffs derived from "Tony-schedule" context — shows wff5 and wff6
- **Fig 4 (page 3):** Knowledge base after URS rule application — shows updated wff1 through wff6 with modified restriction sets recording the inconsistency
- **Fig 5 (page 4):** Wffs derived within the CC (combined context of Stu-schedule and Tony-schedule) — shows wff1' and wff2' after context combination

## Results Summary
MBR successfully handles the meeting scheduling example with two users (Stu and Tony) whose schedules contain contradictions. The system:
1. Detects that merging Stu and Tony's belief spaces creates an inconsistency (both need the same time slot)
2. Records the inconsistency through URS updates to restriction sets
3. Identifies the culprit hypothesis (hyp1) through the RS and ~I rule
4. Drops the culprit from the context, restoring consistency

## Limitations
- Extended origin sets (T=ext) are not discussed in this paper
- The paper describes only a "small feature" of MBR — the contradiction detection and recording mechanism
- The example is a simplified meeting scheduling scenario; scalability to large multi-agent systems is not evaluated
- No formal complexity analysis is provided
- The selection of which hypothesis to drop when resolving a contradiction is not deeply explored

## Testable Properties
- A context defines a unique Belief Space: two different contexts may yield different BSs from the same knowledge base
- Once a proposition is derived, its OT and OS remain constant (only RS changes)
- If a contradiction is found between two wffs, one or both belonging to the CBS, the RS of every hypothesis in their combined OS is updated
- If both contradictory wffs are in the CBS, the ~I rule fires in addition to URS, causing CC revision
- Retrieval within a CBS returns only propositions whose OS is a subset of the current context
- The RS records inconsistency information without requiring a separate NOGOOD data structure

## Relevance to Project
This paper is a direct precursor to de Kleer's ATMS work (1986) already in the collection. MBR's approach to multiple belief spaces, contexts, and contradiction handling via origin sets and restriction sets represents an alternative architecture for the same core problems the ATMS solves: maintaining multiple hypothetical worlds simultaneously and detecting/recording inconsistencies. The context/belief-space mechanism provides a different perspective on how to partition assumptions and manage per-agent reasoning, which is relevant to the propstore's assumption-tracking and multi-perspective belief management.

## Open Questions
- [ ] How does MBR's performance compare with de Kleer's ATMS on the same problem instances?
- [ ] What is the relationship between MBR's restriction sets and the ATMS's nogood environments?
- [ ] How does the choice of culprit hypothesis during contradiction recovery affect soundness?
- [ ] Does the SWM logic's treatment of relevance (vs. classical logic) create meaningful differences in derivable conclusions?

## Related Work Worth Reading
- [1] Anderson A. and Belnap N., "Entailment: The Logic of Relevance and Necessity", Princeton University Press, 1975 — The relevance logic foundation for SWM
- [2] Doyle J., "A Truth Maintenance System", Artificial Intelligence 12:3, 1979 — The original TMS that MBR improves upon (already in collection)
- [3] Martins J., "Reasoning in Multiple Belief Spaces", Ph.D. Dissertation, SUNY at Buffalo, May 1983 — Full dissertation with complete details
- [5] McDermott D., "Contexts and Data Dependencies", Department of Computer Science, Yale University, 1982 — Alternative approach to contextual reasoning
- [6] Shapiro S., "The SNePS semantic network processing system", in Associative Networks, N.v.Findler (ed.), Academic Press, 1979 — The underlying network system
