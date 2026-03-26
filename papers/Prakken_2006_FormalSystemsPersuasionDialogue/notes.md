---
title: "Formal systems for persuasion dialogue"
authors: "Henry Prakken"
year: 2006
venue: "The Knowledge Engineering Review"
doi_url: "https://doi.org/10.1017/S0269888906000865"
pages: "163-188"
---

# Formal systems for persuasion dialogue

## One-Sentence Summary
Provides a formal specification framework for the main design elements of persuasion dialogue systems (topic language, speech acts, protocol rules, commitment stores, argument structures, turntaking, termination, outcome) and uses it to critically review and compare the major formal dialogue systems in computational argumentation. *(p.1)*

## Problem Addressed
There was no unified framework for comparing the growing number of formal persuasion dialogue systems in computational argumentation. Each system made different design choices about speech acts, commitment rules, turntaking, and termination, but these choices were not systematically compared. *(p.1-2)*

## Key Contributions
- A formal specification of dialogue systems identifying the core elements: communication language $L_c$, topic language $L_t$, a protocol $P$, commitment stores $C_s$, rules for argument structure, turntaking, and termination *(p.4)*
- A taxonomy of speech acts for persuasion: claim, why, since, concede, retract, question *(p.6-7)*
- Distinction between peer persuasion (both sides proponent/opponent simultaneously) and conflict resolution (different initial commitments) *(p.5)*
- Classification of commitment rules into four categories: assertion/acceptance attitudes (cautious vs. bold), dialectical obligations, burden of proof handling *(p.10)*
- Critical comparative review of nine specific dialogue systems: Mackenzie (1979), Walton & Krabbe (1995), PPD0 (Prakken 2001), Lodder (1999), TDG (Bench-Capon 1998), Dunne's Lodder, Parsons et al. (2003), Prakken (2005), and argument games *(p.12-24)*
- Identification of key design tensions: unique-reply vs. multiple-reply protocols, strict vs. liberal turntaking, immediate vs. postponed replies *(p.8-9)*

## Methodology
The paper takes a game-theoretic view on dialogue systems. It proposes a formal specification template for dialogue systems and then applies this template to review existing systems. The review is organized around the specification elements, allowing systematic comparison of design choices across systems. *(p.2)*

## Key Definitions and Formal Elements

### Dialogue System Specification *(p.4)*
A dialogue system $D$ consists of:
- A topic language $L_t$: a logical language closed under classical negation and a connective formation
- A communication language $L_c$: speech acts built from $L_t$
- A set of participants, and a set $\mathbf{R}$ of roles
- Dialogue $d$: a sequence of moves from $L_c$
- Commitment store $C_s(d, p)$: the set of formulas participant $p$ is committed to after dialogue $d$
- Context $K \subseteq L_t$: background knowledge that is presupposed and not retractable
- A topic $t \in L_t$: the proposition under dispute
- Effect rules $E$ for $L_c$: specifying effects of speech acts on commitments

### Commitment Store Updates *(p.4)*
Changes in commitments are completely determined by the last move in a dialogue and the commitments just before making that move:

$$
U = H \times L_c \to \text{(new commitments)}
$$

Where $H$ is the set of all finite dialogue sequences. *(p.4)*

### Protocol Definition *(p.4-5)*
A protocol $P$ for $L_c$ specifies the legal moves at each stage of a dialogue. Formally, $A$, the protocol on $L_c$, is a function of $V$ that denotes the context plus a nonempty subset $D$ of $M^{1+n}$:

$$
P: Post(L_c) \cup D \to Post(L_c)
$$

The elements of $D$ are called the *legal finite dialogues*. The elements of $P(d)$ are called the moves allowed after $d$. *(p.4-5)*

### Persuasion Types *(p.5)*
Two types distinguished by Walton & Krabbe (1995):
1. **Persuasion dialogues**: goal is to resolve a conflict of opinion; participants try to persuade each other
2. **Conflict resolution**: participants have a positive point of view ($p$) and a doubtful attitude toward $\neg p$

The paper uses a formal framework where:
- $prop(t)$: the set of participants with a positive point of view toward topic $t$
- $opp(t)$: the set with a doubtful point of view
- For any $t$, the sets $prop(t)$ and $opp(t)$ are disjoint but do not necessarily jointly exhaust all participants *(p.5)*

### Speech Act Taxonomy *(p.6-7)*
Core locutions for persuasion dialogue:
- **claim** $\varphi$: assert/statement. Speaker asserts $\varphi$ is the case
- **why** $\varphi$: challenge/dispute. Speaker challenges that $\varphi$ is the case
- **concede** $\varphi$: accept/grant. Speaker admits $\varphi$ is the case
- **retract** $\varphi$: withdraw. Speaker declares belief is not committed (may not be disbelief)
- **since** $S$: argument. Speaker provides reasons why $\varphi$ is the case (where $S$ is a set of propositions)
- **question** $\varphi$: ask another participant's opinion on $\varphi$

### Commitment Rules Classification *(p.10-11)*

**1. Assertion and acceptance attitudes:**
- Cautious: speaker only claims what they can currently support with argument
- Bold: speaker claims freely, must defend when challenged
- Thoughtful: agent cautious regarding assertions but cannot be forced to concede on insufficient basis
- Skeptical: like thoughtful but requires stronger proof

The Toulmin-Liverpool approach combines assertion and acceptance attitudes:
- *cautious agent*: accepts $\varphi$ if it can construct an acceptable argument for $\varphi$
- *credulous agent*: does so only if it has no counter-argument stronger than its argument
- *thoughtful agent*: can do so only if it has no counter-argument that is at least as strong *(p.11)*

**2. Dialectical obligations:**
- Force speaker to support claims when challenged or retract *(p.8)*

**3. Burden of proof handling:**
- Rules for when challenges must be answered vs. can be deflected *(p.10)*

**4. Dark-side commitments:**
In some systems (Walton & Krabbe), participants must also maintain and defend assertions; assertions and premises of arguments are placed in the assertion store while conceded propositions go in the concession store. Dark-side commitments are hidden or veiled commitments. *(p.14)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Communication language | $L_c$ | - | - | - | p.4 | Speech acts built from topic language |
| Topic language | $L_t$ | - | - | - | p.4 | Logical language with negation |
| Commitment store | $C_s$ | - | - | - | p.4 | Set of formulas per participant |
| Context/background knowledge | $K$ | - | - | - | p.4 | Non-retractable shared knowledge |
| Topic | $t$ | - | - | - | p.4 | Proposition under dispute |
| Dialogue | $d$ | - | - | - | p.4 | Sequence of moves |
| Protocol | $P$ | - | - | - | p.4 | Function from dialogue states to legal moves |

## Implementation Details

### Protocol Design Choices *(p.8-9)*
- **Unique-reply vs. multiple-reply**: whether at most one reply to a move is allowed throughout a dialogue *(p.9)*
- **Immediate vs. postponed replies**: whether participants must respond immediately or can delay *(p.6, 18)*
- **Liberal vs. strict turntaking**: whether participants alternate strictly or have more flexibility *(p.15)*

### Consistency Conditions *(p.6)*
Three conditions for commitment stores at start of dialogue:
- If $s \in prop(t)$ then $T \notin C_s(d,B)$ — proponents don't start committed to the topic
- In persuasion, at most one side in a dialogue grows (opponents don't gain commitments from proponents) *(p.6)*
- If $s \in opp(t)$ then $t \notin C_s(d)$ — opponents don't start committed to topic *(p.6)*

### Paul and Olga Running Example *(p.3, 7-9)*
The paper uses a car safety dialogue throughout:
- Paul claims a car is safe (has airbag)
- Olga challenges and provides counterarguments (newspaper says "explode", high max speed)
- Demonstrates claim, why, since, concede, retract speech acts
- Shows how reply structure forms a tree (Figure 1, p.9)
- Demonstrates unique-reply vs. multiple-reply protocols

### Protocol Rules for Running Example *(p.7)*
Commitment rules for the Paul and Olga example:
- If $m(s) = \text{claim}(p)$ then $C_s(d, m) = C_s(d) \cup \{p\}$
- If $m(s) = \text{why}(p)$ then $C_s(d, m) = C_s(d)$
- If $m(s) = \text{concede}(p)$ then $C_s(d, m) = C_s(d) \cup \{p\}$
- If $m(s) = \text{retract}(p)$ then $C_s(d, m) = C_s(d) \setminus \{p, \neg p\}$
- If $m(s) = \varphi \text{ since } S$ then $C_s(d, m) = C_s(d) \cup S \cup \{\varphi\}$

### Mackenzie (1979) System *(p.13-14)*
- Based on Hamblin's formal dialectics
- Uses propositional logic with no explicit reply structure
- Has commitment store with both "assertion" and "concession" operations
- Commitments are used to manage coherence of participants' dialogues
- Not complete — participants cannot always build adequate arguments *(p.13)*
- Protocol is unique-response but simulates multiple-reply *(p.13)*

### Walton & Krabbe (1995) PPD System *(p.14-15)*
- Two dialogue protocols: PPD for "permissive" and RPD for "rigorous" persuasion dialogues
- PPD is like other systems but has dark-side commitments
- Every participant has their own possible inconsistent belief base
- Participants assumed to adopt assertion and acceptance attitudes
- Communication language consists of claims, challenges, concessions, retractions
- No explicit reply structure; no defined turntaking *(p.14)*
- Table 2: Example PPD dialogue (p.15) with moves, actions, and commitment stores
- System allows indirect challenges but is not fully deterministic *(p.14)*

### PPD0 — Prakken's Earlier Framework *(p.15-16)*
- Argument-based with explicit reply structure
- Formal legal argumentation background
- Uses Toulmin-Liverpool approach to assertion/acceptance attitudes
- Allows postponed replies through flexible turntaking *(p.16)*

### Lodder's DiaLaw (1999) *(p.23)*
- Final development of research of Hage et al. (1994)
- Supplemented by applications to legal disputes
- Developed for handling legal reasoning
- Uses connection to underlying legal logic
- Has two participants: proponent and opponent
- Context has no background knowledge — the logic is used for managing justification structure
- Dialogues have fixed structure with claim, challenge, withdrawal operations *(p.23)*

### Parsons et al. (2003) Toulmin-Liverpool Framework *(p.16-18)*
- Series of papers from Toulouse and Liverpool
- Spells dialogue systems for various types: persuasion, negotiation, information-seeking, inquiry
- Two-party dialogues
- Participants appear to have a proponent and opponent role, can switch
- Communication language: claims, challenges, concessions, questions
- Uses explicit reply structure but has no explicit turntaking — structured internally
- Example protocol (Table 3, p.17): $B_1$ claims $p$, $B_2$ concede $p$; then specific reply structure
- Has formal termination condition tied to logical dialogue lengths *(p.17)*

### Prakken (2005) Framework *(p.19-20)*
- Framework for specifying two-party persuasion dialogues as argument games
- Instantiated with many underlying argument protocols
- Participants have proponent and opponent roles, their roles are irrelevant to protocol
- Allows framework for abstract argumentation
- Has context/no context modes
- Explicitly reply structure based, each reply is an attack
- Moves are unique-reply, where each move targets exactly one prior move
- Table 3 shows an example $L_c$ (p.19)
- Dialogue state is a move tree: open nodes (not yet replied to), closed (replied to), used (their assertions are conceded), and dead (challenged and not defended) *(p.19)*
- Termination: game terminates when no more open moves remain *(p.19)*
- Key innovation: allows a series of fallbacks; freedom to move backward in the reply tree *(p.19-20)*

### TDG — The Dialectical Game (Bench-Capon 1998) *(p.21-22)*
- Precursor to persuasion dialogue games
- Uses FIPA-like speech acts in an adapted version of Drobnikovsky's (1995) dialogue framework
- Has explicit reply structure but also tables of attacks and surrenders (Table 4, p.22)
- Supports claim, why, concede, and since acts with additional data/fact distinction
- A claim can be attacked with a rebuttal which itself is a claim
- Claims and concessions can concern both individual propositions and sets of propositions *(p.22)*

### Argument Games *(p.23-24)*
- A special case of dialogue system: two-party game with proponent and opponent
- Used as proof theory for argumentation logics
- Systems by Loui (1998), Jakobovits & Vermeir (1999), Jakobovits (2000), and Prakken (2001b) studied argument games in formal settings
- Key observation: when a game proof is "grounded" (i.e., the theory from which arguments are constructed is not given in advance), the properties of the game can change *(p.23)*

## Figures of Interest
- **Fig 1 (p.9):** Reply structure of the example dialogue — tree structure showing branching replies to Paul's initial claim, illustrating multiple-reply protocol
- **Fig 2 (p.21):** The example dialogue in Prakken's framework — move tree with open/closed/dead annotations
- **Table 1 (p.9):** Locutions and typical replies — maps speech acts to their allowed responses
- **Table 2 (p.15):** An example PPD dialogue — full trace with actions and commitment stores
- **Table 3 (p.17):** Parsons et al. protocol — example rules for two-party dialogue
- **Table 4 (p.22):** Attacks and surrenders in TDG — mapping of acts to responses

## Results Summary
The paper does not present experimental results but rather a comparative analysis. Key findings:
- No single system addresses all design elements comprehensively *(p.24)*
- Most systems focus on commitment rules and protocol but neglect turntaking and termination *(p.24)*
- The Toulmin-Liverpool approach and Prakken's own framework are closest to complete specifications *(p.16-20)*
- Formal properties like soundness and completeness of dialogue outcomes remain understudied *(p.12)*

## Limitations
- The review focuses primarily on two-party persuasion dialogues; multi-party extensions are noted as open *(p.24)*
- Dialogue with uncooperative participants is not well addressed *(p.20)*
- No system achieves a complete formal treatment of all identified design elements *(p.24)*
- The paper acknowledges that the dialogue framework is still in early stages and much work remains to integrate persuasion systems with cognitive and pragmatic aspects *(p.24)*

## Arguments Against Prior Work
- Mackenzie's system lacks explicit reply structure and is not complete — participants cannot always build adequate arguments *(p.13)*
- Walton & Krabbe's PPD has no explicit turntaking rules and dark-side commitments introduce complexity without clear formal benefit *(p.14-15)*
- Many systems fail to distinguish between peer persuasion and conflict resolution *(p.5)*
- Most existing systems lack formal termination conditions or sound outcome rules *(p.12)*
- Systems that use propositional logic only (Mackenzie) cannot handle structured argumentation with defeasible reasoning *(p.11)*

## Design Rationale
- Game-theoretic view chosen because it provides clear formal specifications with verifiable properties *(p.2)*
- Commitment stores preferred over belief bases because they are publicly observable *(p.4)*
- Multiple-reply protocols preferred because they allow more natural dialogue structure *(p.9)*
- Separation of topic language from communication language enables different instantiations with different logics *(p.4)*
- Explicit protocol rules preferred over informal descriptions for verifiability *(p.4)*

## Testable Properties
- A protocol is *context-independent* if the set of legal moves and the outcome is always independent of the context $K$ *(p.5)*
- A protocol $P$ is *fully deterministic* if $P$ always returns a singleton (exactly one legal move) *(p.5)*
- A protocol is *unique-reply* if at most one reply to a move is allowed throughout a dialogue *(p.9)*
- A dialogue system is for *pure persuasion* iff for any terminated dialogue it holds that either $s \in prop(t)$ and $t \in C_s(d)$ for all $s' \in opp(t)$: $t \notin opp(t)$, or $s \in opp(t)$ and $t \notin C_s(d)$ for all $s' \in prop(t)$: $t \notin prop(t)$ *(p.8)*
- Dialogue termination: a terminated dialogue's outcome is fully determined by the participants' final commitments *(p.5)*

## Relevance to Project
Highly relevant to propstore's argumentation and render layers. The paper provides the formal vocabulary and design space for any system that must manage competing claims through structured dialogue. Key connections:
1. The commitment store model maps directly to propstore's stance tracking — commitments are public, observable, and retractable
2. The speech act taxonomy (claim, challenge, concede, retract) provides formal grounding for the agent workflow layer's operations
3. The distinction between peer persuasion and conflict resolution informs how the render layer should handle competing claims from different sources
4. The protocol framework provides design constraints for any automated argumentation system built on top of propstore

## Open Questions
- [ ] How to extend the two-party framework to multi-party persuasion with more than two participants?
- [ ] What formal termination conditions ensure sound outcomes in practice?
- [ ] How to handle uncooperative participants who violate protocol rules?
- [ ] Can the framework be extended to model mixed dialogue types (persuasion + information-seeking)?
- [ ] How do assertion/acceptance attitudes interact with probabilistic or graded argumentation?

## Related Work Worth Reading
- Walton, D. & Krabbe, E. (1995). *Commitment in Dialogue*. SUNY Press. — Foundational work on dialogue types and commitment
- Parsons, S., Wooldridge, M., & Amgoud, L. (2003). "On the outcomes of formal inter-agent dialogues" — Toulouse-Liverpool framework for multiple dialogue types
- Prakken, H. (2005). "Coherence and flexibility in dialogue games for argumentation" — The author's own extended framework reviewed in Section 8.4
- Bench-Capon, T. (1998). "Specification and implementation of Toulmin dialogue game" — TDG system
- Jakobovits, H. & Vermeir, D. (1999). "Obsolete but well-known: dialectical argumentation" — Argument games approach
- Amgoud, L., Cayrol, C., & Lagasquie-Schiex, M.-C. (2000). "On the acceptability of arguments in preference-based argumentation" — Preference-based extensions relevant to commitment attitudes
- Vreeswijk, G. (1997). "Abstract argumentation systems" — Formal framework for argument games

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — cited as foundational abstract argumentation framework; all dialogue systems reviewed are built on or relate to Dung's AF semantics *(p.1, 11)*
- [[Pollock_1987_DefeasibleReasoning]] — cited for rebutting vs. undercutting defeat distinction used in argumentation-based commitment rules *(p.10)*
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] — Cayrol's bipolar argumentation relates to the support/attack distinction in dialogue moves; not directly cited but Amgoud & Cayrol (2002) is cited for reasoning models *(p.10)*

### New Leads (Not Yet in Collection)
- Walton & Krabbe (1995) "Commitment in Dialogue" — foundational classification of dialogue types and commitment stores; directly defines the PPD system reviewed in Section 8.2 *(p.5, 14)*
- Parsons, Wooldridge & Amgoud (2003) "Properties of formal inter-agent dialogues" — Toulouse-Liverpool framework with formal properties for multi-type dialogues *(p.16-17)*
- Gordon (1994) "The Pleadings Game" — early formal dialogue system from legal AI with Gripe-based procedure *(p.21)*
- Mackenzie (1979) "Question begging in non-cumulative systems" — foundational dialogue logic system *(p.13)*
- Lodder (1999) "DiaLaw" — dialogue system for legal justification *(p.23)*
- Bench-Capon (1998) "Specification and implementation of Toulmin dialogue game" — TDG system *(p.21-22)*

### Supersedes or Recontextualizes
- (none — this is a review/survey paper that frames existing work rather than superseding it)

### Cited By (in Collection)
- [[Prakken_2012_AppreciationJohnPollock'sWork]] — cites this paper in its reference list as Prakken (2006); both are by the same author and share the argumentation dialogue framework perspective

### Conceptual Links (not citation-based)
**Argumentation foundations:**
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — ASPIC+ provides the structured argumentation framework that could instantiate the topic language and argument structure components of dialogue systems specified here; the speech act "since S" directly maps to presenting an ASPIC+ argument
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — the preference orderings in ASPIC+ connect to the commitment rule classification (cautious/bold/thoughtful/skeptical assertion attitudes) and to how argument strength determines dialectical obligations
- [[Clark_2014_Micropublications]] — Clark's claim/challenge/support structure for scientific discourse maps directly to the speech act taxonomy (claim/why/since/concede/retract); micropublications are essentially frozen persuasion dialogues

**Belief revision connections:**
- [[Dixon_1993_ATMSandAGM]] — commitment store operations (add on claim, remove on retract) parallel AGM expansion and contraction; Dixon's proof that ATMS context switching simulates AGM provides a formal bridge between dialogue commitment dynamics and belief revision
- [[deKleer_1986_AssumptionBasedTMS]] — the ATMS's multiple simultaneous contexts map to the multiple commitment stores maintained across dialogue participants; the non-commitment discipline aligns with maintaining all participant viewpoints without forcing resolution
