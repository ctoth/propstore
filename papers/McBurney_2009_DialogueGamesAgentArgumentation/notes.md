---
title: "Dialogue Games for Agent Argumentation"
authors: "Peter McBurney, Simon Parsons"
year: 2009
venue: "Argumentation in Artificial Intelligence (Rahwan & Simari, eds.), Springer"
doi_url: "https://doi.org/10.1007/978-0-387-98197-0_13"
---

# Dialogue Games for Agent Argumentation

## One-Sentence Summary
Provides a comprehensive framework for formal dialogue game protocols between autonomous agents, structured by syntax (locutions, commitment rules), semantics (denotational and operational), and pragmatics (strategic considerations), with application to argumentation-based multi-agent interaction.

## Problem Addressed
Agent communication languages like KQML and FIPA ACL provide too many choices of utterance at each turn, leading to state-space explosion. Dialogue games provide a structured alternative that balances flexibility of expression with tractable interaction. *(p.261)*

## Key Contributions
- Generic framework for specifying dialogue game protocols with components: commencement rules, locutions, combination rules, commitment rules, and termination rules *(p.266)*
- Analysis of dialogue games from three linguistic perspectives: syntax, semantics, and pragmatics *(p.263)*
- Survey of existing agent dialogue game protocols categorized by Walton & Krabbe's dialogue typology *(p.264)*
- Discussion of formal semantics for agent dialogues using denotational and operational approaches *(p.270-274)*
- Protocol design criteria and assessment methodology *(p.275-278)*

## Methodology
The chapter structures agent dialogue games according to the standard linguistic division between syntax (surface form of utterances), semantics (truth/falsity of utterances), and pragmatics (meaning beyond truth conditions). It presents a generic framework for dialogue game specification, discusses semantic approaches, gives an illustrative example, and considers protocol design and assessment.

## Key Concepts

### Walton & Krabbe Dialogue Typology *(p.263-264)*
Six primary dialogue types based on initial information state and dialogue goals:
- **Information-Seeking**: one participant seeks an answer another is believed to know
- **Inquiry**: all participants collaborate to find an unknown answer
- **Persuasion**: one participant seeks to persuade another to accept a proposition
- **Negotiation**: participants bargain over division of a scarce resource
- **Deliberation**: participants collaborate to decide on a course of action
- **Eristic**: participants quarrel verbally to vent grievances

Key observations:
- Only participants (not dialogues) have goals; participants may have hidden goals *(p.264)*
- Most actual dialogues involve mixtures of types *(p.264)*
- Walton & Krabbe do not claim their typology is comprehensive *(p.264)*

### Dialogue Game Protocol Components *(p.266)*
A dialogue game specification comprises:
1. **Commencement Rules**: conditions under which the dialogue begins
2. **Locutions**: permitted utterances (assert, question, challenge, justify, propose, retract, etc.)
3. **Rules for Combination of Locutions**: which locutions are permitted/obligatory in which dialogical contexts
4. **Commitment Rules**: how each locution affects participants' commitment stores
5. **Termination Rules**: conditions under which the dialogue ends

### Commitment Stores *(p.265-266)*
Following Hamblin [41], speakers in dialogue incur commitments: asserting a statement commits the speaker to justifying it if challenged. Commitment stores are public records of each participant's commitments, distinct from their private beliefs. A key design choice is whether stores are:
- Monotonic (commitments only accumulate) vs non-monotonic (retraction allowed)
- Publicly visible to all vs privately maintained

### Agent Dialogue Frameworks *(p.264)*
Three frameworks for combining dialogue types:
1. Prakken's framework for persuasion dialogues supporting embedded sub-dialogues *(p.264)*
2. McBurney & Parsons' Agent Dialogue Frameworks based on PDL, supporting iterated, sequential, parallel and embedded dialogues *(p.264)*
3. Miller & McBurney's RASA frameworks for any types of agent interaction protocols *(p.264)*

## Semantics *(p.270-274)*

### Three Semantic Approaches
1. **Axiomatic semantics**: relates protocol states via logical axioms (mentalist/BDI approach per Cohen & Levesque, Singh) *(p.270)*
2. **Denotational semantics**: maps dialogues to mathematical objects (sets, categories); McBurney & Parsons [69] map dialogues to topological spaces *(p.271)*
3. **Operational semantics**: defines meaning via state transitions; uses labeled transition systems, Linda-based or process algebra approaches *(p.272)*

### Denotational Approach Details
- Dialogues mapped to topological spaces via Tarski's correspondence between modal logic S4 and topological spaces *(p.271)*
- Open sets correspond to propositions knowable by participants; closed sets to propositions assertable
- Provides abstract mathematical characterization independent of specific protocol syntax *(p.271)*

### Operational Approach Details
- Doutre, McBurney & Wooldridge [22,23] use law-governed Linda tuple-spaces to define operational semantics *(p.272)*
- Miller & McBurney [73] use CSP process algebra for specification and verification *(p.273)*

## Protocol Design and Assessment *(p.275-278)*

### Desiderata for Agent Argumentation Protocols
McBurney, Parsons & Wooldridge [74] proposed criteria including:
- **Stated purpose**: protocol should have a clear objective
- **Diversity of individual purposes**: allowing participants different goals
- **Inclusiveness**: all relevant parties should be able to participate
- **Transparency**: rules should be clear to all participants
- **Fairness**: no participant should be systematically disadvantaged
- **Accountability**: participants should be held to their commitments
- **System-level properties**: termination, completeness, soundness

### Strategic Considerations (Pragmatics) *(p.274-275)*
- Participants may have hidden agendas — Dunne [25,26] studies prevarication and suspicion of hidden agenda
- Optimal utterance selection — Dunne & McBurney [28] study efficiency of moves
- Belief revision after dialogue — Parsons & Sklar [77] study how agents update beliefs post-dialogue

## Illustrative Example *(p.274)*
The chapter presents an example dialogue from McBurney, Hitchcock & Parsons [64] showing an eightfold deliberation dialogue with locutions for proposing, questioning, justifying, and deciding courses of action.

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of dialogue types (Walton & Krabbe) | - | count | 6 | - | 263 | Information-seeking, Inquiry, Persuasion, Negotiation, Deliberation, Eristic |
| Chapter pages | - | pages | 20 | 261-280 | - | Book chapter length |

## Implementation Details
- Commitment stores must be maintained per-participant and updated according to locution-specific rules *(p.265-266)*
- Dialogue combination requires mechanisms for embedding, sequencing, and parallel composition *(p.264)*
- Semantics can be verified using process algebra (CSP) tools for protocol checking *(p.273)*
- Linda tuple-space model provides executable operational semantics *(p.272)*

## Limitations
- The chapter is primarily a survey/framework paper, not presenting new formal results *(throughout)*
- The Walton & Krabbe typology is acknowledged as non-comprehensive *(p.264)*
- Denotational semantics remains quite abstract; practical implementation guidance is limited *(p.271)*
- Strategic analysis (pragmatics) of dialogue games is identified as an open research area *(p.274)*

## Arguments Against Prior Work
- KQML and FIPA ACL are criticized for causing state-space explosion due to too many utterance choices at each turn *(p.261)*
- Mentalist (BDI) semantics for agent communications are criticized as unverifiable since mental states are private *(p.270)*
- Previous dialogue game work in philosophy (Hamblin, Lorenzen) is noted as insufficient for multi-agent systems which need richer locution sets *(p.262)*

## Design Rationale
- Dialogue games chosen over unconstrained ACLs because they provide tractable interaction while maintaining expressiveness *(p.261)*
- Syntax/semantics/pragmatics structure chosen because dialogue protocol design mirrors natural language design challenges *(p.263)*
- Commitment-based semantics preferred over mentalist semantics because commitments are publicly observable and verifiable *(p.265)*
- Topological denotational semantics chosen to abstract away from specific protocol syntax *(p.271)*

## Testable Properties
- A well-formed dialogue game protocol must have defined commencement, locution, combination, commitment, and termination rules *(p.266)*
- Commitment stores must be consistent with the locution rules (each locution must have defined commitment effects) *(p.266)*
- Protocol termination must be decidable given the termination rules *(p.266)*
- Agent dialogue frameworks must support at least iterated and sequential composition of sub-dialogues *(p.264)*

## Relevance to Project
This paper provides the theoretical foundation for structured multi-agent argumentation dialogues. For propstore, it grounds:
- How agents could engage in structured argumentation over claims (persuasion dialogues)
- How multiple resolution strategies could be modeled as different dialogue types
- The commitment store concept maps directly to propstore's provenance-tracked stance system
- Protocol design criteria (fairness, transparency, accountability) align with propstore's non-commitment discipline

## Open Questions
- [ ] How do dialogue game protocols interact with Dung AF-based argumentation? (The paper treats them separately)
- [ ] Can the denotational semantics (topological spaces) be connected to propstore's render-time resolution?
- [ ] How would protocol design criteria apply to automated (non-human) argumentation in propstore?

## Related Work Worth Reading
- Walton & Krabbe 1995 — Commitment in Dialogue: foundational typology of dialogue types
- Prakken 2006 — Formal systems for persuasion dialogue: comprehensive review -> NOW IN COLLECTION: [[Prakken_2006_FormalSystemsPersuasionDialogue]]
- McBurney & Parsons 2002 — Games that agents play: the formal PDL-based framework
- Hamblin 1970 — Fallacies: origin of commitment stores concept
- Amgoud, Maudet & Parsons 2000 — Modelling dialogues using argumentation

## Collection Cross-References

### Already in Collection
- [[Prakken_2006_FormalSystemsPersuasionDialogue]] — cited [80] as comprehensive review of formal persuasion dialogue systems
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] — Cayrol, Doutre & Mengin [13] cited for decision problems in preferred semantics
- [[Caminada_2006_IssueReinstatementArgumentation]] — not directly cited but Caminada's labelling semantics are relevant to dialogue outcomes
- [[Dung_1995_AcceptabilityArguments]] — foundational AF framework underlying the argumentation that dialogue games operate over

### New Leads (Not Yet in Collection)
- Walton & Krabbe (1995) — "Commitment in Dialogue" — foundational dialogue typology used throughout
- Hamblin (1970) — "Fallacies" — origin of commitment stores concept
- McBurney & Parsons (2002) — "Games that agents play" — formal PDL-based agent dialogue framework

### Cited By (in Collection)
- [[Prakken_2006_FormalSystemsPersuasionDialogue]] — cites McBurney & Parsons for dialogue game protocols
- [[Gabbay_2012_EquationalApproachArgumentationNetworks]] — cites McBurney & Parsons
- [[Amgoud_2008_BipolarityArgumentationFrameworks]] — cites McBurney & Parsons
- [[Caminada_2007_EvaluationArgumentationFormalisms]] — cites McBurney & Parsons
- [[Prakken_2010_AbstractFrameworkArgumentationStructured]] — cites McBurney & Parsons

### Conceptual Links (not citation-based)
- [[Prakken_2006_FormalSystemsPersuasionDialogue]] — Strong: directly overlapping topic. Prakken reviews persuasion dialogue systems in detail; McBurney & Parsons provide the broader framework covering all dialogue types and protocol design criteria
- [[Dung_1995_AcceptabilityArguments]] — Moderate: dialogue games operate over argumentation frameworks but at a different abstraction level; Dung AFs determine argument acceptability while dialogue games govern the process by which arguments are exchanged
- [[Čyras_2021_ArgumentativeXAISurvey]] — Moderate: dialogical explanations surveyed by Cyras are a direct application of the dialogue game framework described here
