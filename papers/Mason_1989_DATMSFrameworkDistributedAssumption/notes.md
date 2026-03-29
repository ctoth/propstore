---
title: "DATMS: A Framework for Distributed Assumption Based Reasoning"
authors: "Cindy L. Mason, Rowland R. Johnson"
year: 1989
venue: "Distributed Artificial Intelligence, Volume II (Gasser & Huhns, eds.), Morgan Kaufmann"
doi_url: "https://doi.org/10.1016/B978-1-55860-092-8.50017-4"
pages: "293-317"
affiliation: "University of California, Lawrence Livermore National Laboratory"
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-03-29T04:19:25Z"
---
# DATMS: A Framework for Distributed Assumption Based Reasoning

## One-Sentence Summary
DATMS extends de Kleer's ATMS to a multi-agent setting where each agent maintains its own local ATMS and shares results/nogoods via message passing, deliberately allowing agents to hold inconsistent views across the network while maintaining local consistency.

## Problem Addressed
Single-agent ATMS (de Kleer 1986) maintains multiple contexts for one problem solver. When multiple agents each use assumption-based reasoning and share results, two new problems arise: (1) the number of contexts can explode because each communicated fact may introduce new assumption sets, and (2) there is no mechanism for distributed belief revision that preserves each agent's autonomy. The Smith & Davis (1981) result-sharing model assumes mutual credibility and can lead to "wrong consensus" when faulty information propagates through agents that revise beliefs based on external confirmations/denials. *(p.293-298)*

## Key Contributions
- A distributed ATMS architecture (DATMS) where each agent has its own ATMS, facts database, assumptions database, inference rules, communication rules, and TMS rules *(p.302-303)*
- A "liberal belief revision policy" that explicitly rejects requiring global consistency: agents maintain their own assumption-based perspectives, the union of two agents' extensions may be inconsistent, analogous to a "hung jury" model *(p.298-299)*
- A globally unique fact identification scheme: Fact-ID = <identifier:agent> that enables building assumption sets and justifications from mixtures of internal and external facts *(p.301, 303-304)*
- Four fact creation operators (GIVEN, ASSUMED, ASSERTED, COMMUNICATED) that define how assumption sets propagate through inference *(p.305)*
- CONTRADICT predicate in TMS rules with communication policy argument controlling how nogoods propagate across the agent network *(p.307-308)*
- Two message types (TMS messages carrying nogoods, RESULT messages carrying facts with assumption sets) with configurable communication policies *(p.312)*
- FOBJECT declarations that let agents selectively accept/reject classes of external facts *(p.311)*

## Methodology
The paper presents a formal framework for distributed assumption-based reasoning, extending de Kleer's ATMS to multiple agents. The approach modifies Smith and Davis's result-sharing model so that agents do not automatically revise beliefs based on external results. Instead, agents integrate external facts into their own ATMS with the external fact's assumptions tracked as communicated assumption sets. Contradictions are detected locally and propagated via configurable policies.

Implementation is in C and Common LISP on Sun workstations using MATE (Multi-Agent Test Environment). Testing domains include the "animal identification" domain and seismic interpretation for the Nevada Test Site Deployable Seismic Verification System testbed. *(p.294, 313-314)*

## Key Equations / Statistical Models

$$
a_1 \wedge a_2 \wedge \cdots \wedge a_n \rightarrow c
$$
Where: $a_1, \ldots, a_n$ are antecedent facts and $c$ is the consequent fact. The dependency record for $c$ comes from the data dependency records of the antecedents. Communicated antecedents have no local dependency records. *(p.301)*

$$
a_1 \wedge a_2 \wedge \ldots \wedge a_n \rightarrow c_1 \ldots c_m
$$
General rule form. Each consequent $c_i$ can be created by one of four actions producing different assumption set values $A(c_i)$. *(p.305)*

**Fact creation operators and their assumption set semantics:**

$$
\text{GIVEN}(c): A(c) = c
$$
$c$ is a premise, inferred with no antecedents, holds universally in local environments. *(p.305)*

$$
\text{ASSUMED}(c): A(c) = \bigcup_{j=1}^{n} A(a_j) + c
$$
$c$ is a reasoned assumption dependent on itself as well as antecedent assumptions. *(p.305)*

$$
\text{ASSERTED}(c): A(c) = \bigcup_{j=1}^{n} A(a_j)
$$
$c$ is a data item dependent solely on the assumption sets of antecedent facts. *(p.305)*

$$
\text{COMMUNICATED}(c): A(c) = \hat{A}(\hat{c})
$$
$c$ is a data item depending on the communicated assumption set for the external data item $\hat{c}$. *(p.305)*

**CONTRADICT action:**

$$
a_1 \wedge a_2 \wedge \ldots \wedge a_n \rightarrow \text{CONTRADICT}(a_j \ldots a_k)
$$
When this fires, the assumption set $\bigcup_{i=j}^{k} A(a_i)$ and any superset are marked INCONSISTENT and cached in the NOGOOD database. *(p.307)*

**Assumption set consistency propagation:** If $A \subset B$ and $A$ is INCONSISTENT, then $B$ must also be INCONSISTENT. *(p.304-305)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Assumption set | A(f) | set | - | power set of known facts | p.304 | Subset of known facts; labeled CONSISTENT or INCONSISTENT |
| Fact-ID | <id:agent> | identifier | - | - | p.303-304 | Globally unique across agent network |

## Methods & Implementation Details
- **TMS Node structure:** < Fact-ID, Justification, Assumption-Set-ID > where Justification is the inference history and Assumption-Set-ID is an index into the assumptions database *(p.303)*
- **Facts Database:** stores < fact, database-ID, status > where status is Believed or Disbelieved *(p.306)*
- **Assumptions Database:** stores < index, assumption-set, status > where status is Consistent or Inconsistent *(p.304, 306)*
- **NOGOODS Database:** caches all inconsistent assumption sets for fast lookup *(p.308)*
- **Communicated facts** have justification "EXTERNAL" since antecedents reside in the external agent *(p.304)*
- **TMS rules** have the form: (TMSRULE NAME PATTERN (CONTRADICT <Comm-Policy | Agent-List> Fact-List)) *(p.307)*
- **Communication rules** have the form: (COMMRULE NAME PATTERN (SEND <Comm-Policy | Agent-List> Fact-List)) *(p.310)*
- **FOBJECT declaration** specifies which types of external facts an agent will accept and store locally *(p.311)*
- **Message format:** < Msg-Type, To, From, NOGOODS-or-FACTS > where Msg-Type is TMS or RESULT *(p.312)*
- **Inference engine cycle (7 steps):** *(p.312-313)*
  1. Check current beliefs against all rules, decide which inference rule to fire
  2. Execute inference rule, record justification and new TMS node
  3. Execute all instantiated truth maintenance rules
  4. If inconsistency detected, record new NOGOODS, propagate effects, communicate TMS messages per policy
  5. Execute all instantiated communication rules, accept incoming messages
  6. Using TMS messages received, update NOGOODS database
  7. Using RESULT messages received, update working memory and assumptions database

## Figures of Interest
- **Fig 13.1 (p.297):** Conceptual separation of problem solver and truth maintenance system
- **Fig 13.2 (p.297):** Result-sharing model of cooperation — agents E1-E4 exchanging results R
- **Fig 13.3 (p.303):** Architecture of assumption based reasoning agent: inference rules, comm rules, facts DB on left; TMS rules, assumptions DB on right; control in center; message passing below
- **Fig 13.4 (p.308):** CONTRADICT function flow — TMS rules trigger CONTRADICT which updates NOGOOD in assumptions DB and optionally sends TMS messages via comm software
- **Fig 13.5 (p.310):** Communication rules trigger SEND which transmits via comm software using comm policy
- **Fig 13.6 (p.312):** DATMS message format: Msg Type, To, From, NOGOODS or FACTS
- **Fig 13.7 (p.313):** Agent Opus communicating with agents W, Y, Z, U — pi symbols for TMS messages, lambda for result messages
- **Fig 13.8 (p.314):** MATE test program architecture — User controls MATE which manages multiple ABR (assumption based reasoner) processes
- **Fig 13.9 (p.314):** MATE architecture detail — Agent with inference engine, TMS rules, communication rules, application-specific support, and C-based network interface connecting to communication server

## Limitations
- The paper does not address the scalability problem of assumption set explosion in detail — it acknowledges the number of contexts can be "dangerously high" but relies on contradiction knowledge to prune, without formal complexity analysis *(p.300)*
- No formal proof of correctness properties (soundness, completeness) for the distributed protocol *(throughout)*
- Trust model is simplistic: agents are assumed benevolent but possibly compromised; no formal trust calculus *(p.302)*
- The framework does not address the problem of detecting purely external inconsistencies (those involving only externally deduced facts) — an agent may lack the knowledge to detect these *(p.301)*
- Communication strategies are domain-dependent (no general-purpose communication policy provided) *(p.315)*
- Implementation was early-stage at time of writing, testing in limited domains *(p.313-314)*
- No mechanism for determining when/how an agent should retract a communicated fact if the originating agent later discovers it was wrong *(implicit)*

## Arguments Against Prior Work
- Smith and Davis (1981) result-sharing model presumes mutual credibility and trust, which can lead to wrong consensus: agents revise beliefs based on external confirmations without self-supporting evidence *(p.298)*
- Single-context TMSs (Doyle 1979) are insufficient for multiagent reasoning because they cannot represent multiple possibly inconsistent sets of facts simultaneously *(p.294)*
- Forcing global consistency across agents is both impractical and undesirable — it's theoretically impossible to ensure consistency when agents can't derive all logically possible conclusions (Konolige 1986), and the credibility problem has no satisfactory domain-independent solution *(p.299)*
- Previous distributed AI approaches don't address culpability — the ability to trace results back to the originating agent *(p.300-301)*

## Design Rationale
- **Liberal belief revision over forced consensus:** Each agent reasons with its own extensions (consistent assumption sets). The union of two agents' extensions may be inconsistent. This is by design: it preserves each agent's autonomy and prevents contamination from faulty external data *(p.298-299)*
- **Fact-ID = <identifier:agent> rather than location-transparent IDs:** Explicitly ties each datum to its originating agent. This enables culpability tracking, building mixed justifications from internal and external facts, and explanation facilities across the network *(p.303-304)*
- **CONTRADICT with communication policy argument:** Rather than using domain-independent belief revision (as in Doyle 1979 or de Kleer 1986), the CONTRADICT predicate is domain-configurable. The rule writer specifies which agents to inform and what facts constitute the inconsistency. This gives the application designer control over contradiction propagation *(p.307-308)*
- **FOBJECT declarations for selective fact acceptance:** Agents only store externally communicated facts of declared types. This limits context explosion by filtering irrelevant incoming facts *(p.311)*
- **Incremental consistency checking per inference cycle** rather than complete consistency checks: checking all assumptions before use is impractical in an asynchronous multiagent environment *(p.302)*

## Testable Properties
- If assumption set A is INCONSISTENT and A is a subset of B, then B must also be INCONSISTENT *(p.304-305)*
- Communicated facts have justification "EXTERNAL" and their assumption sets reference the originating agent's identifiers *(p.304)*
- The CONTRADICT action marks the union of specified antecedent assumption sets as INCONSISTENT and caches it in the NOGOODS database *(p.307)*
- A received NOGOOD is treated as locally derived: any assumption set containing it is also marked INCONSISTENT *(p.308)*
- Facts whose assumption sets are INCONSISTENT have status Disbelieved in the facts database *(p.309)*
- GIVEN facts have assumption sets containing only themselves (no antecedent dependencies) *(p.305)*
- ASSUMED facts include themselves in their assumption set (self-dependent) *(p.305)*
- ASSERTED facts do NOT include themselves in their assumption set (purely derivative) *(p.305)*
- COMMUNICATED facts inherit the external item's communicated assumption set *(p.305)*

## Relevance to Project
Directly relevant to propstore's ATMS implementation when considering branch assumptions. The paper confirms the key concern: in a multi-agent (or multi-branch) ATMS, the number of contexts can be "dangerously high" because each external fact (branch assumption) may introduce new assumption sets. The DATMS approach of using contradiction knowledge (nogoods) to prune and limit the space is the same approach propstore uses. Key design lessons:

1. **Liberal non-commitment is the right philosophy** — the paper explicitly argues against forcing consistency across agents/branches, matching propstore's core design principle
2. **Context explosion is real but manageable** — contradiction knowledge is the primary defense, confirming propstore should invest in efficient nogood management
3. **Fact provenance (Fact-ID = <id:agent>) is essential** — every datum must track its originating source for culpability/explanation, matching propstore's provenance requirements
4. **Selective fact acceptance (FOBJECT) limits explosion** — agents can choose which types of external facts to internalize, suggesting propstore could limit which branch assumptions propagate

## Open Questions
- [ ] How does DATMS compare to later distributed TMS work (e.g., Huhns & Bridgeland 1991)?
- [ ] Does the framework handle cycles in inter-agent communication (agent A sends to B, B sends back to A)?
- [ ] What is the actual worst-case complexity of the assumption set space with N agents and K assumptions per agent?
- [ ] Can the FOBJECT filtering mechanism be adapted for propstore's branch assumption filtering?

## Related Work Worth Reading
- Provan 1987, "Efficiency Analysis of Multiple-Context TMSs in Scene Representation" — directly relevant to context explosion performance *(p.315)*
- Konolige 1986, "A Deductive Model of Belief" — formal treatment of belief in multiagent setting *(p.299)*
- Mason 1988, "A Seismic Event Analyzer for Nuclear Test Ban Treaty Verification" — the application domain *(p.294)*
- Stallman and Sussman 1971, "Forward Reasoning and Dependency-Directed Backtracking" — foundational ATMS concepts *(p.302)*

## New Leads
- Provan 1987 "Efficiency Analysis of Multiple-Context TMSs in Scene Representation"
- Mason 1988 "A Seismic Event Analyzer for Nuclear Test Ban Treaty Verification"

## Collection Cross-References

### Already in Collection
- [[deKleer_1986_AssumptionBasedTMS]] — the foundational ATMS paper that DATMS directly extends to the multi-agent setting
- [[deKleer_1986_ProblemSolvingATMS]] — companion paper on problem solving with ATMS, relevant architecture
- [[Doyle_1979_TruthMaintenanceSystem]] — single-context TMS that DATMS argues is insufficient for multi-agent reasoning
- [[Reiter_1980_DefaultReasoning]] — default logic formalization cited for the philosophical basis of assumption-based reasoning
- [[McCarthy_1980_CircumscriptionFormNon-MonotonicReasoning]] — circumscription as alternative nonmonotonic approach

### New Leads (Not Yet in Collection)
- Provan 1987 — "Efficiency Analysis of Multiple-Context TMSs in Scene Representation" — directly addresses TMS performance with multiple contexts, the core scalability question
- Konolige 1986 — "A Deductive Model of Belief" — formal model of belief in multiagent systems, key for understanding why global consistency is theoretically impossible
- Smith and Davis 1981 — "Frameworks for Cooperation in Distributed Problem Solving" — the result-sharing paradigm that DATMS modifies

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)
- [[Dixon_1993_ATMSandAGM]] — Dixon bridges ATMS context switching with AGM belief revision operations; Mason's DATMS extends the same ATMS to multi-agent settings, providing a complementary distributed dimension. Dixon's entrenchment-from-justification-structure idea could apply to DATMS's cross-agent justifications.
- [[deKleer_1984_QualitativePhysicsConfluences]] — the qualitative physics domain that originally motivated ATMS development; DATMS extends the same ATMS to distributed sensor interpretation, a different application of the same multiple-interpretation philosophy
- [[Forbus_1993_BuildingProblemSolvers]] — comprehensive treatment of building systems with ATMS including nogood management and context switching; DATMS adds the distributed agent layer on top of these same mechanisms
