---
title: "Computer supported argumentation and collaborative decision making: the HERMES system"
authors:
  - Nikos Karacapilidis
  - Dimitris Papadias
year: 2001
venue: "Information Systems 26 (2001) 259-277"
doi_url: "https://doi.org/10.1016/S0306-4379(01)00020-5"
---

# Notes: Computer Supported Argumentation and Collaborative Decision Making — The HERMES System

## One-Sentence Summary

HERMES is a web-based collaborative decision support system that integrates argumentation with multi-criteria decision making through a formal Discussion Forum model featuring weighted positions, preferences, constraints, and an automated scoring/activation mechanism for reasoning about alternatives. *(p.1)*

## Problem Addressed

Collaborative decision support systems (CDSSs) need to help groups reach consensus, but existing approaches either focus on informal argumentation structures (like IBIS) without quantitative reasoning, or on formal decision theory without capturing the argumentative discourse. *(p.1-2)* There is a gap between argumentative deliberation and multi-criteria preference aggregation. *(p.2-3)*

## Key Contributions

1. **Hybrid argumentation + MCDM framework**: Combines argumentation discourse elements (issues, alternatives, positions, constraints) with multi-criteria weighting and scoring mechanisms. *(p.3-4)*
2. **Discussion Forum data model**: A structured graph where issues contain alternatives, which are supported/attacked by positions, which are related via preferences and constraints. *(p.3-4)*
3. **Activation labels and scoring**: Each argumentation element gets an activation label (active, inactive, pending) computed from the weights and scores of its supporters/attackers. *(p.6-7)*
4. **Consistency checking via constraints**: Detects inconsistent constraints between positions and resolves them through a weighting mechanism. *(p.7-9)*
5. **Web-based implementation**: Fully implemented in Java and runs on the Web with database backend (Oracle). *(p.1, p.9)*

## Methodology

The system builds on an extension of IBIS (Issue-Based Information Systems) with formal decision-making constructs. The Discussion Forum is a directed graph where: *(p.3-4)*

- **Issues** are the top-level decision problems
- **Alternatives** are possible solutions to issues
- **Positions** argue for or against alternatives (with weights)
- **Constraints** express preference relations between positions (e.g., "position-6 is more important than position-7")
- The graph is stored in a relational database (Oracle) *(p.4)*

Reasoning is performed through an **activation/scoring mechanism** that propagates weights and determines which alternatives are best supported. *(p.6-7)*

## Key Equations

### Score of a position *(p.9)*

$$\text{score}(p) = \text{max\_weight} \times \text{max\_scAgainst}(p) + \text{max\_weight} \times X - \text{weightAgainst}(p) \times X - \text{weight}(p) \times \text{max\_scAgainst}(p)$$

Where:
- `max_weight` = maximum possible weight value
- `max_scAgainst(p)` = max score among positions attacking p
- `X` = `max(scAgainst)` — the maximum score among counter-arguments
- Simplified: `score(p) = max_weight * max_scAgainst + max_weight * max_scAgainst - weightAgainst * max_scAgainst - weight(p) * max_scAgainst` *(p.9)*

### Activation conditions *(p.6-7)*

- **Active**: position has score > 0 and at least one active position in favor, or no counter-arguments exist
- **Inactive**: score = 0 or all supporting positions inactive
- **Pending**: intermediate state during recomputation

### Constraint resolution *(p.8)*

When constraint-56 says "position-6 is more important than position-7" and constraint-12 says the reverse, inconsistency is detected through a polynomial (O(k^3)) path consistency algorithm. *(p.8)*

## Parameters

| Parameter | Description | Source |
|-----------|-------------|--------|
| Weight | User-assigned importance of a position (numeric) | *(p.5-6)* |
| Score | Computed from weights of supporting/attacking positions | *(p.6-7, 9)* |
| Activation label | {active, inactive, pending} — computed status | *(p.6-7)* |
| Preference relation | "X is more important than Y" between positions | *(p.5-6)* |
| Constraint | Ordered relation between positions on same issue | *(p.5-6)* |
| BRD (Beyond reasonable doubt) | Proof standard requiring active position in favor, none against | *(p.7)* |
| Scintilla of evidence | Proof standard requiring at least one active position in favor | *(p.7)* |
| Preponderance of evidence | Proof standard comparing aggregate support vs opposition | *(p.7)* |

## Implementation Details

- **Language**: Java *(p.1)*
- **Platform**: Web-based, runs in browser *(p.1, p.4)*
- **Database**: Oracle relational database for storing Discussion Forum graph *(p.4)*
- **Architecture**: Client-server with Java applet front-end *(p.4-5)*
- **Agent layer**: Agents set user actions and are connected to functionalities (open issue, insert alternative, add position, insert constraint) *(p.9-10)*
- **Two agent categories**: agree/act and traverse/context *(p.9-10)*
- **View menu**: Provides access to the entire graph structure with selective visibility *(p.4)*
- **Discourse elements stored**: Issues, alternatives, positions (for/against), preferences, constraints *(p.4-5)*

## Figures of Interest

- **Fig. 1** *(p.5)*: Screenshot of the HERMES Discussion Forum interface showing tree structure of issues/alternatives/positions with color-coded icons for different element types
- **Fig. 2** *(p.6)*: Software architecture diagram (not fully visible but referenced)
- **Fig. 3** *(p.8)*: Detecting inconsistent constraints — shows the constraint graph with conflicting preference orderings
- **Fig. 4** *(p.9)*: The weighting mechanism — shows the argumentation graph with computed scores

## Results Summary

The paper presents a system description rather than experimental results. The key demonstration is a medical decision-making scenario (pituitary tumor treatment) where: *(p.4-5)*

- Multiple doctors (Dr. Brown, Dr. Clark) propose alternatives ("Pharmacological treatment", "Surgical operation")
- Positions for/against are entered with weights
- Constraints express inter-position preferences
- The system automatically computes which alternatives are best supported
- Inconsistent constraints are detected and flagged *(p.7-8)*

## Limitations

1. **No formal semantics grounding**: Unlike Dung-style frameworks, the system does not compute extensions or provide formal guarantee of rationality postulates. *(throughout)*
2. **Weight-based aggregation**: The scoring mechanism is essentially a weighted sum, which may not capture complex defeat relationships. *(p.6-7, 9)*
3. **No defeat distinction**: Does not distinguish rebutting vs undercutting defeat (cf. Pollock 1987). *(throughout)*
4. **Constraint language limited**: Preferences are simple orderings between positions, not general logical constraints. *(p.5-6)*
5. **No belief revision**: When new information arrives, the system recomputes scores but does not formally track belief revision operations. *(p.3)*
6. **Centralized database**: Oracle backend is a single point of failure and doesn't support distributed argumentation. *(p.4)*

## Arguments Against Prior Work

- **Against pure IBIS**: IBIS and its derivatives (gIBIS, QuestMap) lack formal reasoning mechanisms — they capture discourse structure but cannot compute which position is best supported. *(p.2)*
- **Against pure decision theory**: Tools like Decision Theory or MCDM alone don't capture the deliberative process — they operate on pre-structured preference data. *(p.2)*
- **Against Toulmin-only approaches**: Toulmin's argument schema is too informal for computational support. *(p.2)*
- **Against ZENO**: While ZENO uses a rich graphical language, its "category of systems provides a cognitive argumentation environment" but lacks quantitative decision support. *(p.2-3)*
- **Against SIBYL**: SIBYL is not generic enough to address non-trivial decision making. *(p.3)*

## Design Rationale

The key design choice is **merging argumentation discourse with multi-criteria decision analysis**. Rather than treating them as separate phases, HERMES interleaves them: positions in the argumentation graph carry weights, and the scoring mechanism provides quantitative guidance while preserving the argumentative structure. *(p.3-4)*

The **proof standards** (scintilla of evidence, preponderance of evidence, beyond reasonable doubt, dialectical validity) are adopted from Farley and Freeman's work and provide different aggregation policies over the same underlying discourse. *(p.7)* This is an early form of what propstore calls "render policies."

## Testable Properties

1. The scoring mechanism should be monotonic: adding a supporting position should never decrease an alternative's aggregate score.
2. Constraint consistency checking should be sound: flagged inconsistencies should always be real cycles in the preference ordering.
3. The activation label computation should terminate (no infinite oscillation between active/inactive).
4. The proof standards should form a strict ordering: scintilla < preponderance < BRD < dialectical validity.

## Relevance to Project

**Medium-high relevance.** Several concepts map directly to propstore:

1. **Proof standards as render policies**: HERMES' four proof standards (scintilla, preponderance, BRD, dialectical validity) are exactly the kind of resolution strategies propstore supports at the render layer. *(p.7)*
2. **Non-commitment in storage**: HERMES stores all positions and constraints without resolving them until rendering — similar to propstore's design principle. *(p.3-4)*
3. **Weighted argumentation**: The scoring mechanism is a simple version of what could be done with Z3-based optimization in propstore. *(p.9)*
4. **Constraint consistency**: The constraint checking algorithm detects preference cycles, which relates to propstore's conflict detection. *(p.7-8)*
5. **Multi-agent discourse**: The agent architecture (agree/act vs traverse/context) could inform propstore's agent workflow layer design. *(p.9-10)*

**Gaps relative to propstore**: No formal AF semantics (no Dung extensions), no ATMS-style assumption labeling, no belief revision formalism. The quantitative scoring is ad hoc rather than grounded in argumentation semantics.

## Open Questions

1. How does the scoring mechanism relate to gradual/ranking-based argumentation semantics (e.g., categorizer semantics)?
2. Could the constraint consistency checking be formalized as a Dung AF where constraints attack each other?
3. What is the relationship between HERMES' proof standards and Prakken & Sartor's burden of proof formalization?

## New Leads

- **Farley and Freeman** — proof standards in computational argumentation (referenced for the four proof standards) *(p.7)*
- **Gordon and Karacapilidis [14]** — earlier foundational work on the HERMES model *(p.3)*
- **Loui [22]** — requirements on argumentation that are "not generic enough to address non-trivial decision making" — worth checking what requirements were stated *(p.3)*
- **ZENO system (Gordon 1994)** — rich graphical argumentation language, predecessor approach *(p.2)*
- **Constraint-based preference aggregation** — the polynomial consistency checking algorithm referenced from [40] *(p.8)*

## Collection Cross-References

### Already in Collection
- [[Walton_2015_ClassificationSystemArgumentationSchemes]] — related via Walton 1996 citation; Walton's argumentation schemes could formalize the types of positions and constraints used in HERMES.

### New Leads (Not Yet in Collection)
- **Farley and Freeman (1995)** — "Burden of proof in legal argumentation" — source of the four proof standards used in HERMES
- **Gordon and Karacapilidis (1997)** — "The Zeno argumentation framework" — foundational predecessor to HERMES
- **Simari and Loui (1992)** — "A mathematical treatment of defeasible reasoning" — formal treatment that could bridge HERMES' informal scoring and Dung-style semantics
- **Kunz and Rittel (1970)** — "Issues as elements of information systems" — the original IBIS paper

### Cited By (in Collection)
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] — lists Karacapilidis & Papadias (2001) as Related Work Worth Reading and as a New Lead, citing it for practical support relations in argumentation.
- [[Amgoud_2008_BipolarityArgumentationFrameworks]] — cites as [KP02]; referenced as an example of bipolarity in decision-making argumentation.

### Conceptual Links (not citation-based)
- [[Dung_1995_AcceptabilityArguments]] — **Strong.** HERMES provides a practical system for argumentation-based decision making but lacks formal AF semantics. Dung's framework provides the formal grounding that HERMES' ad hoc scoring mechanism approximates.
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — **Moderate.** ASPIC+ provides structured argumentation with formal semantics; HERMES provides a practical collaborative interface. The gap between HERMES' weighted scoring and ASPIC+'s formal defeat semantics is a design tension relevant to propstore's render layer.
- [[Amgoud_2008_BipolarityArgumentationFrameworks]] — **Moderate.** Both address bipolar argumentation (positions for/against). Amgoud formalizes this as BAFs; HERMES implements it as a weighted scoring system. Amgoud's gradual valuation functions could replace HERMES' ad hoc scoring.
- [[Stab_2016_ParsingArgumentationStructuresPersuasive]] — **Moderate.** Both deal with structured argumentation discourse. Stab extracts argumentation structures from text; HERMES provides a collaborative interface for constructing them. The extracted structures could populate a HERMES-like discussion forum.
- [[Mayer_2020_Transformer-BasedArgumentMiningHealthcare]] — **Moderate.** Mayer's pipeline extracts claims and support/attack relations from medical text; HERMES' medical decision-making scenario (pituitary tumor) demonstrates the target use case for such extracted structures.
