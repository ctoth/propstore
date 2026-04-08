---
title: "Thematic Proto-Roles and Argument Selection"
authors: "David Dowty"
year: 1991
venue: "Language, Vol. 67, No. 3"
doi_url: "http://www.jstor.org/stable/415037"
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-04-03T08:15:30Z"
---
# Thematic Proto-Roles and Argument Selection

## One-Sentence Summary
Dowty proposes that thematic roles (Agent, Patient, etc.) are not discrete categories but cluster concepts (Proto-Agent and Proto-Patient) defined by lists of verbal entailments, and that argument selection (which NP becomes subject vs. object) is determined by counting which argument has more entailments of each proto-role type.

## Problem Addressed
The theoretical status of thematic roles in linguistics is deeply contested: there is no consensus on what roles exist, how many there are, how to identify them, or what formal type they have. Traditional discrete role inventories (Agent, Patient, Theme, Goal, Source, Experiencer, Instrument) fail because (1) role boundaries are unclear, (2) different researchers propose incompatible inventories, (3) generalizations stated in terms of roles are often misidentified as thematic when they are actually syntactic, semantic, or pragmatic, and (4) no principled criterion exists for identifying which linguistic evidence counts as evidence for a role type. *(p.547-551)*

## Key Contributions
- Proposes that thematic roles are **prototypes/cluster concepts** (like Rosch 1975 categories), not discrete categories *(p.571)*
- Reduces the entire role inventory to just **two proto-roles**: Proto-Agent (P-Agent) and Proto-Patient (P-Patient), each defined by a list of independent verbal entailments *(p.572)*
- Formulates the **Argument Selection Principle**: subject = argument with greatest number of P-Agent entailments; direct object = greatest number of P-Patient entailments *(p.576)*
- Introduces **Incremental Theme** as a new role category, based on telic predicates being homomorphisms from Theme argument structure to event structure *(p.567)*
- Eliminates **perspective-dependent roles** (Figure/Ground) from the thematic role inventory, reducing them to discourse structure *(p.562-564)*
- Explains the **unaccusative/unergative distinction** as a natural consequence of the Proto-Agent/Proto-Patient continuum *(p.605-612)*
- Provides a framework for **semantic bootstrapping** in language acquisition *(p.600-605)*

## Methodology
Model-theoretic semantics is the investigative tool. Thematic roles are defined as sets of lexical entailments (analytic implications from the meaning of the predicate alone) about NP referents in specific argument positions. The paper examines argument selection patterns across English verbs (with crosslinguistic data from ergative languages, Dutch, Italian, Lakhota, Choctaw, etc.) to motivate the proto-role hypothesis. Multiple verb classes are analyzed: symmetric predicates, psychological predicates, spray/load alternations, hit/break contrasts, and intransitives.

## Key Equations / Statistical Models

No formal equations per se, but key formal definitions:

**Definition: Thematic Role Type (as entailment set)**
A thematic role (type) is A SET OF ENTAILMENTS OF A GROUP OF PREDICATES WITH RESPECT TO ONE OF THE ARGUMENTS OF EACH. Thus a thematic role type is a kind of second-order property, a property of multiplace predicates indexed by their argument positions. *(p.552)*

**Definition: Lexical Entailment**
By ENTAILMENT, the standard logical sense: one formula entails another if in every possible situation (in every model) in which the first is true, the second is true also. LEXICAL ENTAILMENT: the implication follows from the meaning of the predicate in question alone. *(p.552)*

**Principle: Incremental Theme as Homomorphism**
THE MEANING OF A TELIC PREDICATE IS A HOMOMORPHISM FROM ITS (STRUCTURED) THEME ARGUMENT DENOTATIONS INTO A (STRUCTURED) DOMAIN OF EVENTS, modulo its other arguments. *(p.567)*
Where: If x is part of y (in the Theme domain), then the event of x is part of the event of y. The part-whole relation is preserved across the mapping.
*(p.567)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Proto-Agent entailment: Volition | (a) | — | — | present/absent | 572 | Volitional involvement in event or state |
| Proto-Agent entailment: Sentience | (b) | — | — | present/absent | 572 | Sentience and/or perception |
| Proto-Agent entailment: Causation | (c) | — | — | present/absent | 572 | Causing an event or change of state in another participant |
| Proto-Agent entailment: Movement | (d) | — | — | present/absent | 572 | Movement relative to position of another participant |
| Proto-Agent entailment: Independent existence | (e) | — | — | present/absent | 572 | Exists independently of the event named by the verb |
| Proto-Patient entailment: Change of state | (a) | — | — | present/absent | 572 | Undergoes change of state |
| Proto-Patient entailment: Incremental theme | (b) | — | — | present/absent | 572 | Incremental theme |
| Proto-Patient entailment: Causally affected | (c) | — | — | present/absent | 572 | Causally affected by another participant |
| Proto-Patient entailment: Stationary | (d) | — | — | present/absent | 572 | Stationary relative to movement of another participant |
| Proto-Patient entailment: Nonexistence | (e) | — | — | present/absent | 572 | Does not exist independently of the event, or not at all |

## Methods & Implementation Details

- **Argument Selection Principle (31):** In predicates with grammatical subject and object, the argument for which the predicate entails the greatest number of Proto-Agent properties will be lexicalized as the subject; the argument having the greatest number of Proto-Patient entailments will be lexicalized as the direct object. *(p.576)*

- **Corollary 1 (32):** If two arguments of a relation have (approximately) equal numbers of entailed Proto-Agent and Proto-Patient properties, then either or both may be lexicalized as the subject (and similarly for objects). *(p.576)*

- **Corollary 2 (33):** With a three-place predicate, the nonsubject argument having the greater number of entailed Proto-Patient properties will be lexicalized as the direct object and the nonsubject argument having fewer entailed Proto-Patient properties will be lexicalized as an oblique or prepositional object (and if two nonsubject arguments have approximately equal numbers of P-Patient properties, either or both may be lexicalized as direct object). *(p.576)*

- **Nondiscreteness (34):** Proto-roles obviously do not classify arguments exhaustively (some arguments have neither role) or uniquely (some arguments may share the same role) or discretely (some arguments could qualify partially but equally for both proto-roles). *(p.576)*

- **Role Hierarchy derived from proto-roles (36):** Agent > {Instrument, Experiencer} > Patient > {Source, Goal} (usually). This hierarchy falls out of counting P-Agent vs P-Patient entailments without being stipulated. *(p.578)*

- **Unaccusative/unergative classification via Table 1 (p.607):** Cross-classification by agentivity (yes/no) and telicity (atelic/telic) yields four cells: Cell 1 (agentive, atelic) = definitely unergative; Cell 2 (agentive, telic) = ?; Cell 3 (non-agentive, atelic) = ?; Cell 4 (non-agentive, telic) = definitely unaccusative. *(p.607)*

- **Incremental Theme identification:** A direct object NP is an Incremental Theme if the parts of the NP referent correspond to parts of the event, such that the event is 'complete' only if all parts of the NP referent are affected/effected. Diagnosed by perfective aspect: "Mary completely loaded the truck with hay" — *completely* targets the direct object NP. *(p.567-568, 589-590)*

## Figures of Interest
- **Fig. 1 (p.603):** Croft's (1986b) causal chain diagram showing cause→SUBJECT→*means/*manner/*instrument→OBJECT→result, with inverse and straight syncretisms. Roles to the left of the vertical line have Proto-Agent entailments; roles to the right have Proto-Patient entailments.
- **Table 1 (p.607):** Cross-classification of intransitive verbs by agentivity (agentive/non-agentive) and telicity (atelic/telic), yielding four cells mapping to unergative vs. unaccusative.

## Results Summary

The proto-role hypothesis successfully accounts for:
1. **Standard argument selection** in transitive verbs — subject has more P-Agent entailments, object has more P-Patient entailments *(p.577)*
2. **Role hierarchies** — the familiar Agent > Instrument/Experiencer > Patient > Source/Goal ranking falls out from entailment counting without stipulation *(p.578)*
3. **Argument selection indeterminacy** — buy/sell, like/please doublets arise when both arguments have equal proto-role entailment counts (Corollary 1) *(p.579)*
4. **Psychological predicates** — Experiencer-subject vs. Stimulus-subject verbs explained by which argument has the inchoative (change-of-state) P-Patient entailment *(p.579-580, 586-587)*
5. **Spray/load alternations** — the Incremental Theme (a P-Patient entailment) always ends up as direct object in both argument configurations *(p.587-593)*
6. **Hit vs. break contrast** — break entails change of state in one argument only (fixed to direct object, no alternation); hit has no P-entailment difference (free alternation) *(p.594-595)*
7. **Ergative languages** — same proto-roles with REVERSED alignment: high P-Patient → absolutive (syntactic pivot), high P-Agent → ergative *(p.582)*
8. **Unaccusative/unergative distinction** — corresponds to the P-Agent vs. P-Patient continuum among intransitive verb subjects *(p.605-607)*

## Limitations
- The lists of Proto-Agent and Proto-Patient entailments (27, 28) are acknowledged as not necessarily exhaustive; they could be better partitioned. *(p.572)*
- Movement's role in argument selection is ambiguous — it may be irrelevant for object selection entirely, or it may need to be weighted differently. *(p.574, 596)*
- The paper does not fully resolve whether entailments should be WEIGHTED (some counting more than others for argument selection) rather than simply counted. *(p.597)*
- The unaccusative/ergative discussion is preliminary; the paper cannot fully resolve whether syntactic or semantic unaccusativity is at issue in each language. *(p.608-610)*
- Perspective-dependent roles (Figure/Ground) are argued to be discourse-structural, but the argument is acknowledged as requiring further work. *(p.564)*
- Non-standard lexicalizations (receive, undergo, suffer, inherit) violate the selection principle but are a very small class. *(p.581)*

## Arguments Against Prior Work
- **Against discrete role inventories (Fillmore, Gruber, Jackendoff):** No one has ever proposed a complete list of roles; there is fundamental disagreement even on familiar roles like Agent and Theme; role boundaries are unclear and assignment is often arbitrary or theory-dependent. *(p.548-549)*
- **Against the theta-criterion / argument-indexing view (Chomsky 1981):** Demands each argument get exactly one role from a discrete set — but there is massive empirical evidence that roles are not discrete and boundaries are unclear. *(p.549)*
- **Against Jackendoff's conceptual-structure roles:** While compatible with the present proposal, Jackendoff's roles violate the theta-criterion: some verbs assign the same role to two arguments, some assign no role to some arguments. *(p.550)*
- **Against role hierarchy approaches (Nishigauchi 1984, Belletti & Rizzi 1986):** These require a small set of distinguishable role types that effectively index all arguments — the proto-role hypothesis shows this set may not exist. *(p.550)*
- **Against Tenny (1987, 1988) on Incremental Theme:** Tenny claims aspectual delimitedness is associated exclusively with direct objects and not with thematic roles — but transitive motion verbs like enter, cross have Incremental Theme subjects. *(p.570-571)*

## Design Rationale
- **Why only two proto-roles?** When nondiscreteness of roles is recognized, only an opposition between two clusters is needed. Traditional hierarchies and all standard role types fall out from the two proto-role entailment lists. *(p.571-572)*
- **Why entailments rather than decomposition?** The entailment-based definition avoids the question of whether meanings decompose into primitives like CAUSE, GO, STAY. It is compatible with both decompositional and non-decompositional approaches. *(p.553, 598-599)*
- **Why focus on argument selection?** It provides the clearest domain where thematic roles have demonstrable grammatical consequences, avoiding the methodological trap of using any syntactic or lexical pattern as evidence for a role. *(p.561-562)*
- **Why eliminate perspective-dependent roles?** Figure/Ground distinctions are discourse-structural (which NP is more connected to prior discourse), not event-structural. By Ockham's Razor, they should not be in the thematic role inventory. *(p.563-564)*

## Testable Properties
- For any two-place predicate, the argument with more P-Agent entailments should be the subject, and the argument with more P-Patient entailments should be the direct object. *(p.576)*
- Verbs where both arguments have equal P-Agent and P-Patient counts should permit alternate lexicalizations (doublets like buy/sell, like/please). *(p.576)*
- In spray/load alternations, the Incremental Theme should always be the direct object in both syntactic configurations. *(p.588)*
- In ergative languages, the same proto-role entailments should predict argument selection with REVERSED polarity (P-Patient → absolutive). *(p.582)*
- Unaccusative intransitive predicates should tend to have P-Patient entailments for their subject; unergative predicates should tend to have P-Agent entailments. *(p.607)*
- Non-agentive telic intransitives should be definitively unaccusative; agentive atelic intransitives should be definitively unergative. *(p.607)*
- Change-of-state entailment in the direct object should always entail that it is the direct object rather than a prepositional object (break class behavior). *(p.594)*
- Proto-role entailments should serve as semantic defaults in child language acquisition — children should initially assume full proto-role complements. *(p.604-605)*

## Relevance to Project
**Rating: High** — The proto-role framework — semantic categories as graded cluster concepts defined by independent entailment properties rather than discrete labels — IS propstore's non-commitment discipline applied to lexical semantics. This paper belongs to the concept-layer cluster alongside Fillmore, Pustejovsky, Baker, Buitelaar, Clark, McCarthy, and Kallem.

Dowty's central move — replacing a contested inventory of discrete thematic roles with two gradient prototypes defined by independently testable entailment properties (p.571-572) — is the exact structural pattern propstore's concept registry must follow. Concepts that resist neat categorization are not edge cases to be forced into bins; they are the normal case, and the system must represent gradient membership honestly.

Specific points of contact:
1. **Gradient concept membership as default**: The proto-role framework demonstrates that semantic categories are prototype-structured (Rosch 1975), not classical sets. Propstore's concept registry should expect gradient membership — a concept may partially satisfy multiple category definitions without fully belonging to any. The `definition` field in `knowledge/concepts/*.yaml` should accommodate entailment-list definitions, not just necessary-and-sufficient conditions.
2. **Argument Selection Principle = operationalized gradient classification**: Dowty's counting of entailment properties to determine subject/object selection (p.576) is an existence proof that gradient categories can drive concrete decisions without first collapsing to discrete labels. This directly informs how propstore's render layer should handle concept classification — count evidence for competing categorizations at render time, never hardcode a winner at storage time.
3. **Non-discreteness as a feature, not a bug**: Definition (34) (p.576) explicitly states that proto-roles do not classify exhaustively, uniquely, or discretely. This is propstore's non-commitment discipline stated as a linguistic principle: the system must hold partial, overlapping, and indeterminate classifications without forcing resolution.
4. **Corollary 1 = rival normalizations**: When two arguments have equal entailment counts, either can be lexicalized as subject (p.576), producing doublets like buy/sell and like/please. This is the lexical-semantic analog of propstore holding multiple rival normalizations for the same underlying phenomenon.
5. **Vocabulary reconciliation via entailment structure**: The paper shows that the traditional role hierarchy (Agent > Instrument > Patient > Goal) falls out from entailment counting without stipulation (p.578). This provides a model for how propstore's vocabulary reconciliation should work — derive relationships between competing concept labels from their entailment profiles rather than imposing a taxonomy top-down.
6. **Incremental Theme as structured homomorphism**: The formal definition of Incremental Theme as a homomorphism from structured argument denotations into event structure (p.567) provides a model for how propstore's form dimensions can capture structured relationships between concept components, not just flat feature lists.

## Open Questions
- [ ] Should proto-role entailments be weighted (some counting more than others)?
- [ ] Is movement truly irrelevant to object selection?
- [ ] How exactly do proto-roles interact with ergative split-S systems?
- [ ] Can the entailment lists be refined or extended?
- [ ] Do proto-role categories correspond to cognitive/neurological categories?

## Collection Cross-References

### Already in Collection
- [[Fillmore_1982_FrameSemantics]] — Fillmore is extensively cited throughout as the originator of Case Grammar (1966, 1968) and its later revisions (1977). Dowty's proto-role framework is partly a response to the problems Fillmore identified with discrete case/role inventories.

### Cited By (in Collection)
- [[Pustejovsky_1991_GenerativeLexicon]] — Cites Dowty 1985 critically regarding multiple lexical entries for control/raising verbs
- [[Wein_2023_CrossLinguisticAMR]] — Notes that AMR's numbered argument roles (arg0, arg1) are grounded in thematic proto-role theory; shows these role assignments diverge cross-linguistically

### New Leads (Not Yet in Collection)
- Krifka, Manfred (1987, 1989) — Nominal reference and temporal constitution; provides the formal semantics of Incremental Theme via event homomorphisms
- Tenny, Carol L. (1987, 1988) — Grammaticalizing aspect and affectedness; competing account of aspectual delimitedness
- Foley, William A. and Robert D. Van Valin (1984) — Functional syntax and universal grammar; Actor/Undergoer macroroles are the closest competing framework
- Croft, William (1986b) — Categories and relations in syntax; causal chain analysis with typological case syncretism data across 40 languages

### Conceptual Links (not citation-based)
- [[Pustejovsky_1991_GenerativeLexicon]] — Both papers address the compositionality of verb meaning and argument structure; Pustejovsky's qualia structure and event coercion mechanisms complement Dowty's entailment-based role theory by providing a generative account of how argument configurations arise
- [[Fillmore_1982_FrameSemantics]] — Fillmore's frame semantics evolved partly in response to the same problems with discrete role inventories that Dowty addresses; the two approaches converge on the insight that roles are not atomic primitives but emerge from richer semantic structures

## Related Work Worth Reading
- Krifka, Manfred. 1987/1989. Nominal reference, temporal constitution, and quantification in event semantics (formal treatment of Incremental Theme)
- Tenny, Carol L. 1987/1988. Grammaticalizing aspect and affectedness (aspectual delimitedness)
- Foley, William A. and Robert D. Van Valin. 1984. Functional syntax and universal grammar (Actor/Undergoer macroroles)
- Rozwadowska, Bozena. 1988. Thematic restrictions on derived nominals (semantic features approach)
- Croft, William. 1986b. Categories and relations in syntax: The clause-level organization of information (causal chains and case syncretisms)
- Clark, Eve V. and Kathie L. Carpenter. 1989. The notion of source in language acquisition (emergent categories in acquisition)
