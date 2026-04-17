---
title: "Microtheories"
authors: "Robert C. Kallem, Jennifer Sullivan"
year: 2006
venue: "PAKM 2006 (Practical Aspects of Knowledge Management), Vienna, Austria"
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-04-03T08:10:08Z"
---
# Microtheories

## One-Sentence Summary
Describes the microtheory system in CYC for partitioning a knowledge base into named contexts that scope assertion visibility, enabling representation of contradictory viewpoints, multiple source readings, temporal progression, and unshared assumptions without forcing global consistency.

## Problem Addressed
In large knowledge bases that combine facts from many sources, contradictions inevitably arise — different sources assert conflicting facts. The problem is how to represent and reason with contradictory knowledge without the system becoming inconsistent (anything follows from a contradiction in classical logic). CYC's microtheory system provides named contexts that partition assertions so contradictions are isolated and reasoning remains locally consistent. *(p.0)*

## Key Contributions
- Argues that contexts/microtheories are highly relevant to textual analysis in the Humanities *(p.0)*
- Describes practical considerations for using microtheories in CYC *(p.0)*
- Identifies five key use cases for microtheories: managing multiple points of view, multiple readings, temporal progression, unshared assumptions, and interfacing with external models *(p.1-4)*
- Provides detailed worked example using the Christmas narratives in Matthew and Luke to demonstrate microtheory-based contradiction management *(p.5-9)*
- Discusses microtheory hierarchy shape (tree vs. diamond/lattice) and its implications *(p.3-4)*
- Introduces temporal qualification within microtheories using Time Dimensions and Time Parameters *(p.8-9)*

## Methodology
Conceptual/architectural paper demonstrating CYC's microtheory system through explanation of design principles and a detailed worked example. No formal experiments or quantitative evaluation — the contribution is the knowledge engineering methodology itself.

## Key Concepts

### What is a Microtheory
A microtheory (Mt) in CYC is a named context that scopes which assertions are visible during inference. Every fact and rule in CYC is asserted within a specific microtheory. The `ist` (is true in) operator from McCarthy's work is fundamental: `(ist Mt P)` means proposition P is true in context Mt. *(p.0)*

Microtheories are organized in a subsumption lattice. A microtheory inherits all assertions from its parent (more general) microtheories. More specific microtheories can override or contradict inherited assertions. *(p.3)*

### Logical Foundation
Logical inference can conclude arbitrary facts from a knowledge base that contains both P and ¬P. While a well-designed expert system might handle this via the "one case" where multiple points of view exist, independently constructed systems cannot. This is the so-called Consistency of AI problem, ascribed to John McCarthy (McCarthy 1987). CYC's microtheory approach provides a systematic solution. *(p.0)*

### Key Properties of Microtheories
- Each microtheory has both P and ¬P available, though not at the same moment during reasoning *(p.0)*
- Each context has to be locally consistent *(p.0)*
- Contexts allow logical control: having both P and ¬P available while never using them simultaneously *(p.0)*
- Microtheories are "reified" — that is, first-class objects in CycL — enabling reasoning about contexts themselves *(p.4)*
- CYC's language contains several functions that allow constructive specification of regions of context space, by forming the union of microtheories *(p.4)*

### Five Use Cases

#### 1. Managing Multiple Points of View *(p.1)*
The classical situation: source documents express multiple and conflicting versions of events. Example: conflicting descriptions from the Norse Edda regarding the death of Sigurd.

Three separate microtheories represent three versions:
- *Fragment of Sigurd*
- *Short Lay of Sigurd*
- *Ballad of Brynhild*

Any ontological representation that models the contents of these lays has to come to terms with the fact that Sigurd cannot be in three places at once. By mapping these to three separate microtheories, all representations can co-exist. Some microtheories are like having several acknowledged sub-realities available at once. *(p.1)*

#### 2. Managing Multiple Readings *(p.1)*
Divergent points of view need not be as striking as offering alternative narratives for the same event. Often they are minor differences in documentary evidence. Humanists-specific microtheories can provide the level of support a text-critical apparatus can provide in a critical edition. *(p.1)*

Example: Goethe — in describing his family's new house in Frankfurt — literary scholars disagree on whether the "many" reading or "funny" reading is correct. This requires four microtheories: one for Goethe's prints, one for Beutler, one for Beutler (who presumably does not agree with other corrections), and one for the Hamburg edition. *(p.1-2)*

#### 3. Managing Temporal Progression *(p.2)*
Microtheories can model temporal progression of a researcher's changing thinking/indexes. The microtheories that model different publications of a researcher can be indexed by the year of the Gregorian calendar in which they were published. *(p.2)*

Temporal progression is also relevant to appropriately model the propositional attitudes of the entities described as the sources change over time. Example: how Grimm's brothers became wary of Simrock in the ways in which Grimm exacts vengeance on her own family — the temporal index is no longer congruent with the source's temporal index. *(p.2)*

The notion of "story true" in such a source-dependent construct and temporal information is often very sparse, making it difficult to give general suggestions on how to best model this context-internal time. *(p.2)*

#### 4. Managing Unshared Assumptions *(p.2-3)*
Microtheories can be used to segregate assumptions of the sources that the reconstructing researcher cannot share. Example: the ordered ruling by nature that Grimm and Adi's feminist motives (Helga studies when Helen's wrongfully accuses Gudrun of infidelity — *Third Lay of Guthrún*). To the original audience of the lays, it was clear that the person with Truth on their side would not be hurt by a simple forward physical event (in this case, hot water), while the person with Truth against her could not but sustain injuries. *(p.2-3)*

While such an understanding is an important part of the ontological model of the lore of the source, it is not convenient to have that knowledge present and "active" — so to speak — at all times during the reconstruction process. By delegating such "mentalities," extensions of everyday physics to a separate microtheory, the exception can be treated as an exception and quarantined until needed. *(p.3)*

#### 5. Dealing Correctly with RefIds and other Models *(p.3)*
Microtheories contain statements about how the world is (or was), not just simple claims. The main issue is that within a microtheory, all the standard rules of first- and higher-order logical inference hold. But statements of belief, desire, interpretation, etc. are modal and not subject to the standard rules of first- and higher-order logical inference. So in order to perform standard inference within the reconstructed mental models of sources and colleagues, a microtheory representation of their arguments and beliefs has to be available. *(p.3)*

At the same time, a model representation is needed, because their beliefs, wishes and desires are modal. *(p.3)*

### Practical Considerations *(p.3-4)*

#### Designing Microtheory Hierarchies *(p.3)*
Microtheories are organized in subsumption lattices, with more specific microtheories collecting facts from more general ones. Inheritance works like whole-sale inclusion: every fact or rule present in the more general microtheory is available in the more specific client microtheories.

**Key design principle:** Microtheories should only contain as much information as absolutely necessary. Facts that one or more microtheories might want to share are best factored out into their own microtheory. Example: if three lays of Sigurd did not know about the character of Guthorm, it might be best to keep the information about Guthorm in a separate microtheory to be included only in those lays that have the character. *(p.3)*

#### The Shape of Microtheory Hierarchies *(p.3-4)*
While microtheory hierarchies are typically tree-like in shape, there is no aprion reason they need to form a tree. However, cases such as diamond-shaped directed acyclic graphs or even a loop-base semantics that are often unintentional, so it is worth considering the implications:

- **Diamond-shaped:** A diamond-shaped directed acyclic microtheory hierarchy means that the terminal (often so-called "collector") microtheory holds the union of all beliefs. In the case of disagreement over Sigurd's place of death, this would be a meaningless operation, for that microtheory would be self-inconsistent and therefore could infer arbitrary facts. *(p.3-4)*
- **Graph loop:** A microtheory graph loop has the semantics of an equivalence class: the set of microtheories involved in the loop form one large microtheory, again containing the union of all the beliefs. *(p.4)*
- **"Collector" microtheories:** These are most useful when there are several points of view to be modeled, and none of the points of view agree about most but not all of the facts. *(p.4)*

#### Reasoning with Microtheories *(p.4)*
CYC supports a special logical operator called `ist`, best understood as "in true (in a region of context space)", which takes as its arguments a region of context space and a conjunction of sentences. During logical inference, each `ist` inference is handled independently of the others, thereby preserving the specific point of view. This effectively compartmentalizes the reasoning steps, so that each inference can encounter in a consistent view of the knowledge base. Humanities researchers perform such inferences all the time, e.g. "Compare and contrast the descriptions of the death of Sigurd in the Short Lay of Sigurd with the descriptions in the *Chaos of Gudrun's Wars*." *(p.4-5)*

#### Reasoning Into Microtheories *(p.5)*
One question the authors address is how to leverage the contradictory knowledge that has been carefully segregated into separate microtheories. While it is already built into the argumentation engine of CYC's reasoning tool, there remain several questions about preserving the power of logical inference. CYC provides for a specific way in which the contradictory knowledge can be carefully exploited in inference. *(p.5)*

**Key capability:** It is not possible to block individual facts from being inherited if a microtheory is declared to be a specialization of another. This has the somewhat counter-intuitive consequence that if a microtheory wants to inherit only part of another microtheory's contents, the more general microtheory has to be re-factored into the interesting part and the remainder. *(p.5, footnotes 10-11)*

This capability follows from the property of *contextual omniscience* of the theory of contexts, which means that all microtheories can interpret into all the other microtheories (cf. Ihroni 1995 and Ihroni et al. 1998). *(p.5, footnote 10)*

## Detailed Example: Christmas Narratives *(p.5-9)*

### Setup *(p.5-6)*
The worked example analyzes the Christmas stories in the Gospels of Matthew and Luke, demonstrating how microtheory setup works in practice.

Microtheory structure:
```cycl
In Mt: GospelOfMatthewContext(mt).
f: (isa(Mt) Author(St) Matthew-BookOfBible)
f: (isa JesusOfNazareth Messiah).

In Mt: GospelOfMatthewMt.
f: (isa JesusOfNazareth Messiah).

In Mt: GospelOfLukeContext(mt).  
f: (isa(Mt) Author(St) Luke-BookOfBible)
f: (isa JesusOfNazareth Messiah).
```
*(p.5-6)*

### The Prophetic Precondition *(p.6)*
From the Old Testament, Matthew and Luke both know the Messiah has to be born in Bethlehem. The prophetic passage regarding location is from Micah 5:2, and regarding virgin birth from Isaiah 7:14.

The critical aspects that the two gospels amalgamate from these two prophetic passages are represented in a `MessianicPropheciesMt` microtheory:
```cycl
In Mt: MessianicPropheciesMt.
f: (implies
      (and
        (isa ?SON MalePerson)
        (isa ?VIRGIN Virgin)
        (isa ?B-DAY BirthingEvent)
        (birthChild ?B-DAY ?SON)
        (birthParent ?B-DAY ?VIRGIN)
        (locationOf ?B-DAY Bethlehem))
      (isa ?SON Messiah)).
```
*(p.6)*

### The Historical Precondition *(p.6)*
A `FertileCrescentNamingConventionMt` encodes the naming convention that famous people from the Fertile Crescent are typically known by their first name + "of" + their childhood town:
```cycl
In Mt: FertileCrescentNamingConventionMt.
f: (implies
      (and
        (isa ?PERSON FamousPerson)
        (isa ?EVENT Childhood)
        (animateActedOn ?EVENT ?PERSON)
        (locationOf ?EVENT ?TOWN)
        (firstName ?PERSON ?NAME))
      (ist EnglishLexiconMt
        (commonNickName ?PERSON
          (WordConcatenationFn ?NAME Of-TheWord ?TOWN)))).
```
This means the narrative of Jesus's childhood has to end in the village of Nazareth in Galilee. *(p.6)*

### The Differences in the Christmas Narratives *(p.6-8)*
The two narratives cannot co-exist in the same context of reasoning without inducing contradictions.

**Announcement of the birth:** Three differences considered:
1. Who is the recipient of the announcement?
2. Does the announcement precede the beginning of the pregnancy?
3. Where and when does the announcement occur?

Matthew: `GospelAccordingToMatthewMt` — angel Gabriel tells Joseph *(p.7)*
Luke: `GospelAccordingToLukeMt` — angel tells Mary *(p.7)*

**Pregnancy relationship:** Luke asserts `MiracleOfPregnancyOfMaryWithJesus` as a specific physiological event *(p.7)*

**Residency:** Both gospels assert different residency locations:
- Luke: Mary and Joseph reside in Nazareth, Galilee *(p.7)*  
- Matthew: Mary and Joseph reside in Bethlehem, Judea (initially) *(p.8)*

**Birth location:**
- Matthew: Birth occurs at `HouseOfJosephInBethlehem` (a House) *(p.8)*
- Luke: Birth occurs at `StableWhereJesusWasBorn` (a Stable, adjacent to a hotel building) *(p.8)*

### Temporal Qualification Problem *(p.8-9)*
The paper identifies a subtle representation issue: the temporal extent of microtheory contexts can be larger than appropriate for the facts stated. Individual events are fine, but residency statements about Mary and Joseph are problematic:

```cycl
In Mt: GospelOfMatthewMt. ;; WRONG WRONG WRONG WRONG
f: (residesInRegion Mary-MotherOfJesus BethlehemJudea).
f: (residesInRegion Joseph-FatherOfJesus BethlehemJudea).
```

This is false because they also reside in Egypt for a couple of years and then move to Nazareth. The solution uses **Time Dimensions** and **Time Parameters**:

```cycl
In Mt: GospelOfMatthewMt.
Time Dimension: (TimeIntervalInclusiveFn
  (YearBCE-JulianFn 7) (YearBCE-JulianFn 3)).
Time Parameter: Time-Point.
f: (residesInRegion JesusOfNazareth BethlehemJudea).
```
*(p.8-9)*

Temporal qualification is not restricted to absolute dates. The temporal constraints can also be pushed into the temporal dimension of the content specification, allowing modeling the constraints in terms of event time as long as the events themselves are temporally related to each other in terms of their sequence. *(p.9)*

```cycl
In Mt: GospelOfMatthewMt.
Constant: HolyFamilyLivingInEgypt.
startActionOfEnd: HolidOTThemaSalah.
endActionBefore: HolyFamilyInNazareth.
f: (residesIn ...)

In Mt: AbsenceOfResearchHolyFamilyInNazarethEgypt.
Time Dimensions: (TemporalExtentInfo ...)
Time Parameter: Time-Point.
f: (residesInRegion JesusOfNazareth Egypt).
```
*(p.9)*

## Figures of Interest
- No numbered figures in this paper; the content is primarily CycL code examples and prose.

## Results Summary
The paper demonstrates that CYC's microtheory system effectively handles contradictory knowledge from multiple sources by partitioning assertions into named, hierarchically organized contexts. The Christmas narrative example shows this working in practice with real contradictions between Matthew and Luke's gospels, including managing birth announcements, locations, residency, and temporal scoping of facts. *(p.0-9)*

## Limitations
- The paper acknowledges that much work remains in implementing microtheories — only some of the additional dimensions of context space have been identified, mainly time *(p.5)*
- It is not possible to block individual inherited facts from a parent microtheory — the entire parent must be refactored to exclude unwanted facts *(p.5)*
- Temporal qualification is "often inappropriate" for many events described; the temporal constraints at issue are not restricted to absolute dates, and only rough estimates are available *(p.9)*
- The contextual omniscience property means all microtheories can interpret into all others, which has counter-intuitive consequences *(p.5)*

## Arguments Against Prior Work
- McCarthy's original `ist` operator (McCarthy 1987, 1993) and Guha's formalization (Guha 1991) laid the groundwork, but CYC's practical implementation goes beyond the theoretical proposals by handling real-world knowledge engineering challenges *(p.0)*
- The paper implicitly argues that simple consistency enforcement (the "Consistency of AI" problem) is the wrong approach — instead, contradictions should be managed through contextual partitioning *(p.0)*
- Prior implementations of contexts in Doug Lenat's CYC Project, where contexts were called "micro-eras" (Guha, in formalizing common-sense), did not achieve global consistency *(p.0)*

## Design Rationale
- **Microtheory partitioning over global consistency:** The fundamental choice is to allow contradictions to exist across microtheories while maintaining local consistency within each one, rather than attempting to force global consistency *(p.0)*
- **Subsumption lattice over flat contexts:** Organizing microtheories hierarchically enables inheritance and factoring of shared knowledge, reducing redundancy *(p.3)*
- **Tree shape preferred over diamond/loop:** Diamond shapes lead to collector microtheories containing the union of all beliefs (self-inconsistent if beliefs contradict); loops create equivalence classes that merge contexts unintentionally *(p.3-4)*
- **Minimal content principle:** Each microtheory should contain only what is absolutely necessary; shared facts should be factored into their own microtheory *(p.3)*
- **Temporal qualification via Time Dimensions:** Rather than encoding time in the assertions themselves, CYC uses Time Dimension and Time Parameter metadata on the microtheory to scope when assertions hold *(p.8-9)*

## Testable Properties
- A microtheory must be internally consistent — no P and ¬P within the same microtheory *(p.0)*
- Facts in a parent microtheory are visible in all child microtheories (subsumption inheritance) *(p.3)*
- Diamond-shaped microtheory hierarchies produce collector microtheories containing the union of all beliefs *(p.3-4)*
- Loop structures in microtheory graphs create equivalence classes (all microtheories in the loop behave as one) *(p.4)*
- The `ist` operator compartmentalizes inference — each `ist` inference is handled independently *(p.4)*
- Contradictory facts in sibling microtheories do not produce inconsistency at the parent level *(p.0, p.5-9)*
- Temporal qualification restricts fact visibility to time intervals without modifying the fact itself *(p.8-9)*

## Relevance to Project
This paper is directly relevant to propstore's core design principle of non-commitment discipline. CYC's microtheory system is essentially a production implementation of contextual partitioning for contradictory knowledge — exactly what propstore does with its branch isolation, ATMS assumption sets, and render-time filtering. Key parallels:

1. **Microtheories ↔ ATMS assumption sets / branches:** Both partition assertions into named contexts that can hold contradictory facts without forcing resolution.
2. **Microtheory inheritance ↔ branch subsumption:** Parent-child relationships in both systems propagate facts downward.
3. **`ist` operator ↔ render policy filtering:** Both defer contradiction resolution to query/render time rather than storage time.
4. **Temporal qualification ↔ context conditions:** Both systems allow scoping when assertions hold without modifying the assertions themselves.
5. **Collector microtheories ↔ IC merge:** The problem of merging contradictory contexts maps to propstore's IC merge operators.

The paper's warning about diamond-shaped hierarchies creating inconsistent collectors is directly relevant to propstore's merge classification and IC merge design.

## Open Questions
- [ ] How does CYC handle the case where a user explicitly wants to merge contradictory microtheories? (The paper identifies the problem but doesn't detail the merge semantics)
- [ ] What is the formal relationship between CYC's microtheory subsumption and ATMS label propagation?
- [ ] Could the temporal qualification mechanism (Time Dimensions/Parameters) inform propstore's context condition system?

## Collection Cross-References

### Already in Collection
- [[McCarthy_1980_CircumscriptionFormNon-MonotonicReasoning]] — McCarthy is cited as the originator of the "Consistency of AI" problem and the `ist` operator for contexts; the 1980 circumscription paper is a different work but same author's non-monotonic reasoning program
- [[deKleer_1986_AssumptionBasedTMS]] — CYC microtheories and ATMS assumption sets solve the same fundamental problem (holding contradictory beliefs without forcing resolution); microtheory = named context with assertion scoping, ATMS environment = assumption set labeling each datum
- [[deKleer_1986_ProblemSolvingATMS]] — practical problem-solving with ATMS directly parallels practical reasoning with microtheories
- [[Dixon_1993_ATMSandAGM]] — Dixon bridges ATMS and AGM belief revision; microtheory merging (collector microtheories) maps to AGM contraction/revision operations on context unions
- [[Mason_1989_DATMSFrameworkDistributedAssumption]] — DATMS distributes assumption-based reasoning across agents; microtheories distribute assertion scoping across named contexts — same partitioning principle, different mechanism

### New Leads (Not Yet in Collection)
- Guha, R.V. (1991). "Contexts: A Formalization and Some Applications." PhD Thesis, Stanford — formal theory of contexts underlying CYC's microtheory system. Directory exists at papers/Guha_1991_ContextsFormalizationApplications/ but notes.md not yet written.
- Buvac, S. et al. (1995). "Metamathematics of Contexts" — formal properties of context systems including contextual omniscience
- Ramachandran, D. et al. (2005). "First-ordered Data-Type Expressions and Efficiency in a Common Sense Knowledge Base" — CYC efficiency

### Now in Collection (previously listed as leads)
- [[McCarthy_1993_FormalizingContext]] — Formalizes contexts as first-class logical objects via ist(c, p), defines lifting rules for cross-context reasoning, nonmonotonic inheritance via abnormality predicates, and transcendence for expanding limited axiomatizations. This is the formal foundation that Kallem's Cyc microtheories directly implement — the ist operator used throughout Kallem's paper originates here.

### Supersedes or Recontextualizes
- (none — this paper applies existing context theory to Humanities use cases rather than superseding prior formalization work)

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)

**Context partitioning and non-commitment:**
- [[deKleer_1986_AssumptionBasedTMS]] — **Strong.** Microtheories and ATMS environments are dual mechanisms for the same goal: holding contradictory information without forcing commitment. Microtheories use named contexts with subsumption inheritance; ATMS uses assumption labels with environment intersection. Both defer resolution to query time. The "collector microtheory" problem (diamond-shaped hierarchies producing inconsistent unions) is exactly the ATMS environment-merging problem.
- [[Dixon_1993_ATMSandAGM]] — **Strong.** Dixon shows ATMS context switching implements AGM operations. Microtheory inheritance (child sees all parent assertions) maps to ATMS label propagation. The inability to block individual inherited facts (Kallem p.5) is the microtheory analog of ATMS's completeness requirement.
- [[Mason_1989_DATMSFrameworkDistributedAssumption]] — **Moderate.** DATMS partitions belief spaces across agents using ATMS assumptions. Microtheories partition assertion visibility across named contexts. Both solve distributed non-commitment, but DATMS adds inter-agent communication protocols that microtheories lack.

**Belief revision and merging:**
- [[Alchourron_1985_TheoryChange]] — **Moderate.** AGM postulates define correctness for belief revision operations. Microtheory merging (collector microtheories) implicitly performs belief union, which AGM governs. The paper's warning about diamond shapes creating inconsistency is essentially the AGM observation that unconstrained expansion can break consistency.

**Predication-level eventualities:**
- [Ontological Promiscuity](../Hobbs_1985_OntologicalPromiscuity/notes.md) — **Strong.** Hobbs reifies the *condition* of a single predication via `p'(e, x₁,…,xₙ)`, where microtheories reify the *stable context* in which many predications hold. The two grains are complementary — a microtheory is a bag of Hobbs-style atomic predications sharing contextual assumptions. Propstore's claim layer needs both: Hobbs-shape per-claim eventualities carried inside Kallem-shape microtheory contexts.

## Related Work Worth Reading
- McCarthy, J. (1987, 1993). "Generality in Artificial Intelligence" — original `ist` operator and context formalization → NOW IN COLLECTION: [[McCarthy_1993_FormalizingContext]]
- Guha, R.V. (1991). "Contexts: A Formalization and Some Applications." PhD Thesis, Stanford — formal theory of contexts underlying CYC
- Buvac, S. (1993). "Resolving lexical ambiguity using a formal theory of context" — context-based disambiguation
- Ramachandran, D., Regan, K., Goolsbey, K. (2005). "First-ordered Data-Type Expressions and Efficiency in a Common Sense Knowledge Base" — CYC efficiency improvements
- Guha, R.V., Lenat, D.B. (1994). "Enabling agents to work together" — CYC agent collaboration via contexts
