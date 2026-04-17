---
title: "PROV-O: The PROV Ontology"
authors: "Timothy Lebo; Satya Sahoo; Deborah McGuinness; Khalid Belhajjame; James Cheney; David Corsar; Daniel Garijo; Stian Soiland-Reyes; Stephan Zednik; Jun Zhao (editors and contributors); Luc Moreau; Paolo Missier (PROV Working Group)"
year: 2013
venue: "W3C Recommendation"
doi_url: "https://www.w3.org/TR/prov-o/"
pages: 69
citation: "Lebo, Sahoo, McGuinness, et al. PROV-O: The PROV Ontology. W3C Recommendation 30 April 2013. http://www.w3.org/TR/2013/REC-prov-o-20130430/"
---

# PROV-O: The PROV Ontology

## One-Sentence Summary
PROV-O is the normative OWL2 encoding of the W3C PROV Data Model for provenance: it defines 30 classes, 50 object/datatype properties, and a *qualification pattern* that lets asserters elaborate any binary provenance relation with an intermediate influence class, all grouped into three incremental categories (Starting Point, Expanded, Qualified) and intentionally kept light (5 non-OWL-RL axioms) to maximise interoperability *(p.1-2)*.

## Problem Addressed
Interoperable interchange of provenance information across heterogeneous systems and domains on the Web requires (a) a shared vocabulary of the *things* whose provenance is recorded (entities, activities, agents), (b) a shared vocabulary for the *relations* among them, and (c) a mechanism to *qualify* those relations with extra context (time, location, role, plan) without forcing every asserter to pay that cost up front. PROV-O realises (a)–(c) as an OWL2 ontology mapped from the PROV Data Model (PROV-DM) *(p.2)*.

## Key Contributions
- Normative OWL2 Web Ontology Language encoding of the PROV Data Model *(p.2)*.
- Three-tier categorisation enabling *incremental* adoption: Starting Point → Expanded → Qualified Terms *(p.3)*.
- The **Qualification Pattern**: for every qualifiable binary relation `R(a,b)` there exists a qualifying property `qualifiedR` whose value is an instance of a qualified influence class whose `entity/activity/agent` property points back to the influencer, enabling attachment of arbitrary metadata (time, location, role, plan) to the influence *(p.9-12, Tables 2-3)*.
- Normative name-reservation for inverse properties (Appendix B, Table 5) even when PROV-O itself does not assert the inverses, avoiding interoperability fracture from parallel self-invented inverse vocabularies *(p.65-66)*.
- Lightweight profile: conforms to OWL 2 RL except for five explicit non-RL axioms (Table 5 / Appendix A) that use `owl:unionOf` for domains/ranges *(p.65)*.

## Study Design
*Non-empirical — specification document.*

## Methodology
PROV-O is derived by mapping every PROV-DM concept to an OWL2 construct — PROV-DM types become OWL classes, PROV-DM relations become OWL object properties, PROV-DM attributes become OWL datatype properties. The mapping discipline:
- Each ontology term cites its PROV-DM term in a "PROV-DM term" annotation *(p.14)*.
- Object properties are marked with an `op` superscript in the spec; datatype properties with `dp` *(p.14)*.
- `prov:qualifiedForm` / `prov:unqualifiedForm` annotation properties link qualified and unqualified forms of every qualifiable relation *(p.14)*.
- The ontology ships with a Turtle serialization at `http://www.w3.org/ns/prov-o#` *(p.1)* and a stable namespace IRI `http://www.w3.org/ns/prov#` *(p.3, Table 1)*.

## Three Categories (normative structure)

### 1. Starting Point Terms (p.4)
Minimal subset for basic provenance. Three classes, nine properties.

**Classes:** `prov:Entity`, `prov:Activity`, `prov:Agent`.

**Properties:** `prov:wasGeneratedBy`, `prov:wasDerivedFrom`, `prov:wasAttributedTo`, `prov:startedAtTime`, `prov:used`, `prov:wasInformedBy`, `prov:endedAtTime`, `prov:wasAssociatedWith`, `prov:actedOnBehalfOf`.

Diagrammatic shape convention: entities = yellow ovals, activities = blue rectangles, agents = orange pentagons, responsibility properties pink *(p.4, Fig 1)*.

### 2. Expanded Terms (p.6-9)
Builds on Starting Point with subclasses, additional subproperties, and temporal/location scaffolding. Six+ classes, ~16 properties.

**Classes:** `prov:Collection` (entity with members via `prov:hadMember`), `prov:EmptyCollection`, `prov:Bundle` (named set of provenance assertions — enables provenance-of-provenance), `prov:Person`, `prov:SoftwareAgent`, `prov:Organization`, `prov:Location`, `prov:Plan`.

**Properties:** `prov:alternateOf`, `prov:specializationOf`, `prov:generatedAtTime`, `prov:hadPrimarySource`, `prov:value`, `prov:wasQuotedFrom`, `prov:wasRevisionOf`, `prov:invalidatedAtTime`, `prov:wasInvalidatedBy`, `prov:hadMember`, `prov:wasStartedBy`, `prov:wasEndedBy`, `prov:invalidated`, `prov:influenced`, `prov:atLocation`, `prov:generated`.

Five sub-categories of expansion *(p.7)*:
1. Subclasses/subproperties/super-property of Starting Point (three Agent subclasses; three Entity subclasses; `prov:wasInfluencedBy` superproperty; `prov:wasQuotedFrom`/`prov:wasRevisionOf`/`prov:hadPrimarySource` as subproperties of `wasDerivedFrom`).
2. Abstraction levels among Entities (`prov:specializationOf`, `prov:alternateOf`).
3. Literal value and location of Entity/Activity/Agent/InstantaneousEvent (`prov:value`, `prov:atLocation`).
4. Entity lifetime beyond generation/usage (`prov:generatedAtTime`, `prov:invalidatedAtTime`, `prov:wasInvalidatedBy`, `prov:invalidated`, `prov:generated`).
5. Activity lifetime extensions (`prov:wasStartedBy`, `prov:wasEndedBy`).

### 3. Qualified Terms (p.9-13)
Applies the Qualification Pattern to 14 unqualified binary relations. Extensive class hierarchy rooted in `prov:Influence`.

**Qualified class hierarchy:**
```
prov:Influence
├── prov:EntityInfluence
│   ├── prov:Usage
│   ├── prov:Start
│   ├── prov:End
│   └── prov:Derivation
│       ├── prov:PrimarySource
│       ├── prov:Quotation
│       └── prov:Revision
├── prov:ActivityInfluence
│   ├── prov:Generation
│   ├── prov:Communication
│   └── prov:Invalidation
└── prov:AgentInfluence
    ├── prov:Attribution
    ├── prov:Association
    └── prov:Delegation
```
Also: `prov:Plan`, `prov:InstantaneousEvent`, `prov:Role` (structural aids rather than influence types) *(p.46, 54)*.

**Qualified/qualifying properties:** `prov:wasInfluencedBy`, `prov:qualifiedInfluence`, `prov:qualifiedGeneration`, `prov:qualifiedDerivation`, `prov:qualifiedPrimarySource`, `prov:qualifiedQuotation`, `prov:qualifiedRevision`, `prov:qualifiedInvalidation`, `prov:qualifiedStart`, `prov:qualifiedUsage`, `prov:qualifiedCommunication`, `prov:qualifiedAssociation`, `prov:qualifiedEnd`, `prov:qualifiedDelegation`, `prov:qualifiedAttribution`, `prov:influencer`, `prov:entity`, `prov:activity`, `prov:agent`, `prov:hadUsage`, `prov:hadGeneration`, `prov:hadPlan`, `prov:hadActivity`, `prov:atTime`, `prov:hadRole`.

## The Qualification Pattern (the load-bearing idea)

For every qualifiable unqualified influence relation `influenced_class ——unqualified_influence—→ influencing_class`, PROV-O provides:

1. A `qualification_property` from the influenced class to an instance of a `qualified_influence` class, which is a subclass of `prov:Influence`.
2. An `influencer_property` from the qualified-influence instance back to the original influencing resource.
3. Freedom to attach any additional RDF properties (e.g., `prov:atTime`, `prov:hadRole`, `prov:hadPlan`, `prov:atLocation`) to the qualified-influence instance.

### Table 2 (normative, p.10): Qualifying Starting-Point properties

| Influenced Class | Unqualified Influence | Influencing Class | Qualification Property | Qualified Influence | Influencer Property |
|---|---|---|---|---|---|
| prov:Entity | prov:wasGeneratedBy | prov:Activity | prov:qualifiedGeneration | prov:Generation | prov:activity |
| prov:Entity | prov:wasDerivedFrom | prov:Entity | prov:qualifiedDerivation | prov:Derivation | prov:entity |
| prov:Entity | prov:wasAttributedTo | prov:Agent | prov:qualifiedAttribution | prov:Attribution | prov:agent |
| prov:Activity | prov:used | prov:Entity | prov:qualifiedUsage | prov:Usage | prov:entity |
| prov:Activity | prov:wasInformedBy | prov:Activity | prov:qualifiedCommunication | prov:Communication | prov:activity |
| prov:Activity | prov:wasAssociatedWith | prov:Agent | prov:qualifiedAssociation | prov:Association | prov:agent |
| prov:Agent | prov:actedOnBehalfOf | prov:Agent | prov:qualifiedDelegation | prov:Delegation | prov:agent |

### Table 3 (normative, p.10-11): Qualifying Expanded properties

| Influenced Class | Unqualified Influence | Influencing Class | Qualification Property | Qualified Influence | Influencer Property |
|---|---|---|---|---|---|
| prov:Entity or prov:Activity or prov:Agent | prov:wasInfluencedBy | prov:Entity or prov:Activity or prov:Agent | prov:qualifiedInfluence | prov:Influence | prov:influencer |
| prov:Entity | prov:hadPrimarySource | prov:Entity | prov:qualifiedPrimarySource | prov:PrimarySource | prov:entity |
| prov:Entity | prov:wasQuotedFrom | prov:Entity | prov:qualifiedQuotation | prov:Quotation | prov:entity |
| prov:Entity | prov:wasRevisionOf | prov:Entity | prov:qualifiedRevision | prov:Revision | prov:entity |
| prov:Entity | prov:wasInvalidatedBy | prov:Activity | prov:qualifiedInvalidation | prov:Invalidation | prov:activity |
| prov:Activity | prov:wasStartedBy | prov:Entity | prov:qualifiedStart | prov:Start | prov:entity |
| prov:Activity | prov:wasEndedBy | prov:Entity | prov:qualifiedEnd | prov:End | prov:entity |

**Equivalence rule** *(p.11)*: "Consuming applications SHOULD recognize both qualified and unqualified forms, and treat the qualified form as implying the unqualified form." The unqualified form is preferred when no extra attributes are needed; including both simultaneously facilitates PROV-O consumption.

## Key Class Reference (Section 4, Cross-Reference)

Every class/property is documented in Section 4 with a uniform template: IRI, textual definition, at least one Turtle example, "described with properties" (outgoing), "in range of" (incoming), "has super-properties" / "has subclasses" / "is subclass of", "can be qualified with" (unqualified side) or "qualifies" (qualified side), and a `PROV-DM term` back-reference *(p.14-65)*.

### Starting Point (Section 4.1)

| Class | IRI | Def | Sub/Super | Page |
|---|---|---|---|---|
| prov:Entity | `http://www.w3.org/ns/prov#Entity` | Physical, digital, conceptual, or other thing with some fixed aspects; may be real or imaginary | Subclasses: prov:Collection, prov:Plan, prov:Bundle | p.14-15 |
| prov:Activity | `http://www.w3.org/ns/prov#Activity` | Something that occurs over a period of time and acts upon or with entities; may include consuming, processing, transforming, modifying, relocating, using, or generating entities | — | p.15 |
| prov:Agent | `http://www.w3.org/ns/prov#Agent` | Something that bears some form of responsibility for an activity taking place, for the existence of an entity, or for another agent's activity | Subclasses: prov:Organization, prov:Person, prov:SoftwareAgent | p.15-16 |

### Expanded classes (Section 4.2)

| Class | Def | Super | Page |
|---|---|---|---|
| prov:Collection | Entity that provides a structure (set, list, etc.) to constituent entities | prov:Entity | p.21 |
| prov:EmptyCollection | Empty collection | prov:Collection | — |
| prov:Bundle | Named set of provenance descriptions which may itself have provenance | prov:Entity | p.6 |
| prov:Person | — | prov:Agent | — |
| prov:SoftwareAgent | — | prov:Agent | — |
| prov:Organization | — | prov:Agent | — |
| prov:Location | Identifiable geographic place (but place within objects, etc. is also allowed); domain prop for `prov:atLocation` | — | p.7 |
| prov:Plan | Entity representing a set of actions or steps intended by agents to achieve some goal | prov:Entity | p.61 |

### Qualified classes (Section 4.3)

| Class | IRI | Def | is subclass of | qualifies | Page |
|---|---|---|---|---|---|
| prov:Influence | `…#Influence` | Capacity of an entity, activity, or agent to have an effect on the character, development, or behavior of another | — | prov:wasInfluencedBy | — |
| prov:EntityInfluence | `…#EntityInfluence` | Entity-as-influencer | prov:Influence | — | — |
| prov:ActivityInfluence | `…#ActivityInfluence` | Activity-as-influencer | prov:Influence | — | — |
| prov:AgentInfluence | `…#AgentInfluence` | Agent-as-influencer | prov:Influence | — | — |
| prov:Usage | `…#Usage` | Beginning of utilizing an entity by an activity | prov:EntityInfluence, prov:InstantaneousEvent | prov:used | — |
| prov:Generation | `…#Generation` | Completion of production of a new entity by an activity | prov:ActivityInfluence, prov:InstantaneousEvent | prov:wasGeneratedBy | p.41 |
| prov:Derivation | `…#Derivation` | Transformation of an entity into another | prov:EntityInfluence | prov:wasDerivedFrom | — |
| prov:Attribution | `…#Attribution` | Ascribing of an entity to an agent | prov:AgentInfluence | prov:wasAttributedTo | — |
| prov:Association | `…#Association` | Assignment of responsibility to an agent for an activity | prov:AgentInfluence | prov:wasAssociatedWith | p.55 |
| prov:Communication | `…#Communication` | Exchange of an entity by two activities | prov:ActivityInfluence | prov:wasInformedBy | p.41 |
| prov:Delegation | `…#Delegation` | Assignment of authority/responsibility to an agent | prov:AgentInfluence | prov:actedOnBehalfOf | p.45-46 |
| prov:Start | `…#Start` | Beginning of an activity triggered by an entity | prov:EntityInfluence, prov:InstantaneousEvent | prov:wasStartedBy | p.36 |
| prov:End | `…#End` | Ending of an activity triggered by an entity | prov:EntityInfluence, prov:InstantaneousEvent | prov:wasEndedBy | p.36 |
| prov:Invalidation | `…#Invalidation` | Start of destruction, cessation, or expiry of an entity | prov:ActivityInfluence, prov:InstantaneousEvent | prov:wasInvalidatedBy | — |
| prov:PrimarySource | `…#PrimarySource` | Particular case of derivation from a primary source | prov:Derivation | prov:hadPrimarySource | — |
| prov:Quotation | `…#Quotation` | Repeat (of some or all of) an entity | prov:Derivation | prov:wasQuotedFrom | p.51 |
| prov:Revision | `…#Revision` | Derivation where resulting entity is a revised version of the original | prov:Derivation | prov:wasRevisionOf | — |
| prov:InstantaneousEvent | `…#InstantaneousEvent` | Events that mark a change in the world; atomic and instantaneous | — | — | p.46 |
| prov:Role | `…#Role` | Function of an entity or agent with respect to an activity, in the context of a usage/generation/invalidation/association/start/end | — | — | p.46-47, 62 |
| prov:Plan | `…#Plan` | Entity representing steps intended to achieve a goal | prov:Entity | — | p.61 |

## Key Property Reference (selected)

### Starting Point properties

| prov: URI | Domain | Range | Superproperty | Can be qualified with | PROV-DM term | Page |
|---|---|---|---|---|---|---|
| prov:wasGeneratedBy | prov:Entity | prov:Activity | prov:wasInfluencedBy | prov:Generation, prov:qualifiedGeneration | Generation | p.16 |
| prov:wasDerivedFrom | prov:Entity | prov:Entity | prov:wasInfluencedBy | prov:Derivation, prov:qualifiedDerivation | Derivation | p.16 |
| prov:wasAttributedTo | prov:Entity | prov:Agent | prov:wasInfluencedBy | prov:Attribution, prov:qualifiedAttribution | Attribution | — |
| prov:used | prov:Activity | prov:Entity | prov:wasInfluencedBy | prov:Usage, prov:qualifiedUsage | Usage | — |
| prov:wasInformedBy | prov:Activity | prov:Activity | prov:wasInfluencedBy | prov:Communication, prov:qualifiedCommunication | Communication | — |
| prov:wasAssociatedWith | prov:Activity | prov:Agent | prov:wasInfluencedBy | prov:Association, prov:qualifiedAssociation | Association | — |
| prov:actedOnBehalfOf | prov:Agent | prov:Agent | prov:wasInfluencedBy | prov:Delegation, prov:qualifiedDelegation | Delegation | p.20 |
| prov:startedAtTime | prov:Activity | xsd:dateTime | — | — | Start (time) | — |
| prov:endedAtTime | prov:Activity | xsd:dateTime | — | — | End (time) | — |

### Key expanded properties

| prov: URI | Domain | Range | Notes | Page |
|---|---|---|---|---|
| prov:wasInfluencedBy | union(Entity, Activity, Agent) | union(Entity, Activity, Agent) | Top-level super of all influence; can be qualified with prov:Influence / prov:qualifiedInfluence | p.65 (non-OWL-RL) |
| prov:wasStartedBy | prov:Activity | prov:Entity | Superproperty: prov:wasInfluencedBy | — |
| prov:wasEndedBy | prov:Activity | prov:Entity | Superproperty: prov:wasInfluencedBy | p.31 |
| prov:invalidated | prov:Activity | prov:Entity | Inverse of prov:wasInvalidatedBy | p.31 |
| prov:wasInvalidatedBy | prov:Entity | prov:Activity | Destruction start | p.31 |
| prov:generatedAtTime | prov:Entity | xsd:dateTime | Time entity completed creation | p.25 |
| prov:invalidatedAtTime | prov:Entity | xsd:dateTime | Time of invalidation | — |
| prov:hadPrimarySource | prov:Entity | prov:Entity | Subproperty: wasDerivedFrom | p.25-26 |
| prov:wasQuotedFrom | prov:Entity | prov:Entity | Subproperty: wasDerivedFrom | — |
| prov:wasRevisionOf | prov:Entity | prov:Entity | Subproperty: wasDerivedFrom | — |
| prov:value | prov:Entity | rdfs:Literal (datatype) | Direct value of entity | — |
| prov:atLocation | union(Activity, Entity, Agent, InstantaneousEvent) | prov:Location | Non-OWL-RL (union domain) | p.65 |
| prov:alternateOf | prov:Entity | prov:Entity | Different aspects of same thing | — |
| prov:specializationOf | prov:Entity | prov:Entity | More specific aspects of same thing | — |
| prov:hadMember | prov:Collection | prov:Entity | Collection membership | — |

### Key qualified properties

| prov: URI | Domain | Range | Inverse | Notes | Page |
|---|---|---|---|---|---|
| prov:qualifiedInfluence | Entity∪Activity∪Agent | prov:Influence | — | Generic qualification | — |
| prov:qualifiedGeneration | prov:Entity | prov:Generation | — | Qualifies wasGeneratedBy | — |
| prov:qualifiedDerivation | prov:Entity | prov:Derivation | — | Qualifies wasDerivedFrom | — |
| prov:qualifiedAttribution | prov:Entity | prov:Attribution | — | Qualifies wasAttributedTo | — |
| prov:qualifiedUsage | prov:Activity | prov:Usage | — | Qualifies used | — |
| prov:qualifiedCommunication | prov:Activity | prov:Communication | — | Qualifies wasInformedBy | — |
| prov:qualifiedAssociation | prov:Activity | prov:Association | — | Qualifies wasAssociatedWith | — |
| prov:qualifiedDelegation | prov:Agent | prov:Delegation | — | Qualifies actedOnBehalfOf | — |
| prov:qualifiedStart | prov:Activity | prov:Start | — | Qualifies wasStartedBy | — |
| prov:qualifiedEnd | prov:Activity | prov:End | — | Qualifies wasEndedBy | p.56 |
| prov:qualifiedInvalidation | prov:Entity | prov:Invalidation | — | Qualifies wasInvalidatedBy | — |
| prov:qualifiedPrimarySource | prov:Entity | prov:PrimarySource | — | Qualifies hadPrimarySource | — |
| prov:qualifiedQuotation | prov:Entity | prov:Quotation | — | Qualifies wasQuotedFrom | p.51 |
| prov:qualifiedRevision | prov:Entity | prov:Revision | — | Qualifies wasRevisionOf | — |
| prov:influencer | prov:Influence | union(Entity, Activity, Agent) | — | Generic "points back to influencer" | — |
| prov:entity | prov:EntityInfluence | prov:Entity | — | Cites Entity influencer | — |
| prov:activity | prov:ActivityInfluence | prov:Activity | — | Cites Activity influencer | — |
| prov:agent | prov:AgentInfluence | prov:Agent | — | Cites Agent influencer | — |
| prov:hadRole | prov:Association∪prov:InstantaneousEvent | prov:Role | Non-OWL-RL (union domain) | p.62, p.65 |
| prov:hadPlan | prov:Association | prov:Plan | Optional plan on Association | p.61 |
| prov:hadUsage | prov:Derivation | prov:Usage | Optional Usage in a Derivation | p.59 |
| prov:hadGeneration | prov:Derivation | prov:Generation | Optional Generation in a Derivation | p.59 |
| prov:hadActivity | union(Delegation, Derivation, Start, End) | prov:Activity | Non-OWL-RL (union domain) | p.65 |
| prov:atTime | prov:InstantaneousEvent | xsd:dateTime | Time for Start/End/Usage/Generation/Invalidation | — |

## Appendix A — PROV-O OWL Profile (non-normative, p.65)

PROV-O conforms to the **OWL 2 RL profile** except for **five axioms** that use non-superclass (`owl:unionOf`) expressions where OWL 2 RL requires a named superclass. Introducing named "placeholder" union classes was rejected as confusing and bloat-inducing.

### Table 5 — The five non-OWL-RL axioms

| Property | Axiom | Expression |
|---|---|---|
| prov:atLocation | rdfs:domain | `owl:unionOf (prov:Activity prov:Agent prov:Entity prov:InstantaneousEvent)` |
| prov:wasInfluencedBy | rdfs:domain | `owl:unionOf (prov:Activity prov:Agent prov:Entity)` |
| prov:wasInfluencedBy | rdfs:range | `owl:unionOf (prov:Activity prov:Agent prov:Entity)` |
| prov:hadActivity | rdfs:domain | `owl:unionOf (prov:Delegation prov:Derivation prov:Start prov:End)` |
| prov:hadRole | rdfs:domain | `owl:unionOf (prov:Association prov:InstantaneousEvent)` |

### Table 6 — OWL 2 RL-safe fallbacks

For OWL 2 RL environments that ignore union domains, PROV-O provides alternate intersecting domains/ranges *(p.65)*:

| Property | Direction | Domain/Range (RL-safe) |
|---|---|---|
| prov:atLocation | rdfs:domain | (implied owl:Thing) |
| prov:wasInfluencedBy | rdfs:domain / rdfs:range | (implied owl:Thing) |
| prov:hadActivity | rdfs:domain | prov:Influence |
| prov:hadRole | rdfs:domain | prov:Influence |

## Appendix B — Names of inverse properties (normative, p.66-67)

PROV-O deliberately asserts only **two inverses** (`prov:generated` is inverse of `prov:wasGeneratedBy`; `prov:invalidated` is inverse of `prov:wasInvalidatedBy`). All other inverses are intentionally not asserted — asserting both directions multiplies the query surface that non-reasoning consumers must handle.

However, the *names* of inverse properties are **reserved** in the PROV namespace so that asserters who want to model in the opposite direction use the canonical inverse name instead of inventing their own (`my:hadDerivation`, `your:ledTo`, etc.).

### Table 5 (normative, p.66): Reserved inverse names

| Domain | PROV-O Property | Recommended inverse name | Range |
|---|---|---|---|
| prov:Agent | prov:actedOnBehalfOf | prov:hadDelegate | prov:Agent |
| prov:ActivityInfluence | prov:activity | prov:activityOfInfluence | prov:Activity |
| prov:AgentInfluence | prov:agent | prov:agentOfInfluence | prov:Agent |
| prov:Entity | prov:alternateOf | prov:alternateOf | prov:Entity |
| union | prov:atLocation | prov:locationOf | prov:Location |
| prov:EntityInfluence | prov:entity | prov:entityOfInfluence | prov:Entity |
| prov:Activity | prov:generated | prov:wasGeneratedBy | prov:Entity |
| union | prov:hadActivity | prov:wasActivityOfInfluence | prov:Activity |
| prov:Derivation | prov:hadGeneration | prov:generatedAsDerivation | prov:Generation |
| prov:Collection | prov:hadMember | prov:wasMemberOf | prov:Entity |
| prov:Association | prov:hadPlan | prov:wasPlanOf | prov:Plan |
| prov:Entity | prov:hadPrimarySource | prov:wasPrimarySourceOf | prov:Entity |
| union | prov:hadRole | prov:wasRoleIn | prov:Role |
| … | *(table continues; see paper)* | | |

(Full row listing continues on pp.66-67 for every qualification property, every starting-point property, etc. The discipline: "if you want the inverse, use the reserved name.")

## Figures of Interest
- **Fig 1 (p.4):** Starting Point classes and properties as a directed graph — Entity (yellow oval), Activity (blue rectangle), Agent (orange pentagon) + `wasDerivedFrom`, `used`, `wasGeneratedBy`, `wasInformedBy`, `wasAssociatedWith`, `wasAttributedTo`, `actedOnBehalfOf`, `startedAtTime`/`endedAtTime`.
- **Fig 2 (p.6):** Worked Example 1 — Derek's crime-chart provenance rendered as a PROV-O graph.
- **Fig 3 (p.6):** Expanded terms superimposed on Starting-Point diagram.
- **Fig 4 (p.12):** Ten subfigures (a-j) illustrating the Qualification Pattern for Usage, Generation, Invalidation, Communication, Start, End, Derivation, Attribution, Association, Delegation. PrimarySource/Quotation/Revision follow the same pattern as Derivation and are omitted as special cases.

## Examples / Running Scenario
The spec uses a **crime-chart publishing** scenario throughout *(pp.4-13)*:
- Agent `:derek` (Person, acting on behalf of `:national_newspaper_inc`).
- `:aggregationActivity` uses `:crimeData` (attributed to `:government`) and `:nationalRegionsList` (attributed to `:civil_action_group`), generates `:aggregatedByRegions`.
- `:illustrationActivity` uses `:aggregatedByRegions`, generates `:bar_chart`; is informed by `:aggregationActivity`.
- Later: `:postEditor` (SoftwareAgent) publishes two versions `:post9821v1` (invalidated, with typo "currius") and `:post9821v2` (revision fixing typo; alternateOf+specializationOf permalink `:more-crime-happens-in-cities`). All provenance wrapped in a `prov:Bundle`.
- Monica produces `:post9822` (alternate for a different audience). John writes `:post19201` quoting `:quote_from_derek` and `:quote_from_monica`. John's post gets invalidated by `:hard_disk_failure`.
This scenario exercises every class and property family at least once.

## Implementation Notes / Design Details
- **Namespace**: `http://www.w3.org/ns/prov#` (prefix `prov:`) *(p.3, Table 1)*.
- **OWL encoding download**: the spec links to the actual OWL file ("OWL encoding of the PROV Ontology is available here") *(p.1)*.
- **Compliance scope**: Sections 1.1, 1.2, 3, 4, and Appendix B are normative. Tables inside normative sections are normative. All figures and diagrams are informative. All examples are informative *(p.2)*.
- **RFC 2119** terminology: MUST, SHOULD, MAY interpreted per RFC 2119 *(p.3)*.
- **Interoperability rule for qualified forms**: implementers MAY emit either form; consumers SHOULD accept both. Qualified form IMPLIES unqualified form. Emitting both simultaneously is encouraged when qualified attributes are present *(p.11)*.
- **Bundle semantics**: A `prov:Bundle` is "an abstract set of RDF triples, and adding or removing a triple creates a new distinct Bundle of PROV-O assertions" *(p.6)*. PROV-O does not itself provide a way to name a Bundle in RDF — examples use TriG *(p.14)*.
- **Examples use Turtle** throughout the cross-reference section *(p.14)*.
- **Instance of an Agent** is always inferable from `foaf:Person`, `foaf:Organization`, or `prov:SoftwareAgent` — examples routinely show `a foaf:Person, prov:Agent` *(p.4-5)*.

## Results Summary (what's shipped)
- **80 indexed terms** in the Term Index (Section 4.4, Table 4; pp.63-64): 30 classes, 50 properties counted by my tally (see Term Index listing).
- **5 non-OWL-RL axioms** (Table 5, Appendix A, p.65).
- **2 asserted OWL inverses** (`prov:generated` ↔ `prov:wasGeneratedBy`; `prov:invalidated` ↔ `prov:wasInvalidatedBy`) and a full **reservation table** for the rest (Appendix B, Table 5, pp.66-67).
- Three normative tables of qualification structure (Tables 2, 3) plus one cross-reference term index (Table 4).
- A complete worked example scenario elaborated across Section 3 (Examples 1-11).

## Limitations / Intentional Omissions
- PROV-O is "intentionally minimal and lightweight" — specifically, it does **not** define inverses for most properties to avoid doubling the reasoning/query surface *(p.66)*.
- Does **not** specify how to encode Bundles in RDF (suggests TriG) *(p.6, p.14)*.
- `prov:Location` instances are "outside the scope of PROV-O; reuse of other existing vocabulary is encouraged" *(p.7)*.
- `prov:Plan` and `prov:Role` content "left to be extended by applications" *(p.11, p.62)*.
- Some property domains/ranges use OWL union expressions that fall outside OWL 2 RL, preventing full RL reasoning on those axioms *(p.65)*.
- PROV-O does not provide the subclass of Bundle that names a set of PROV-O assertions — "more appropriate to do so using other recommendations" *(p.6)*.

## Arguments Against Prior / Alternative Approaches
- **Against defining all inverses**: modelers "may choose from two logically equivalent properties", forcing downstream consumers to handle both cases (OWL reasoner, extra code, or bigger queries). PROV-O therefore defines only two inverses *(p.66)*.
- **Against leaving inverse names unreserved**: without reservation, "modelers are free to create their own properties", leading to a fracture like `my:hadDerivation` vs `your:ledTo` vs `their:derivedTo`, all logically equivalent but interoperability-hostile. Hence the normative reservation table *(p.66)*.
- **Against fully OWL 2 RL conformance**: named-class placeholders for union domains were rejected as bloating the ontology and confusing users; five explicit non-RL axioms were accepted instead *(p.65)*.
- **Against forcing qualified form**: the qualified form is "more verbose"; "the unqualified form should be favored in cases where additional properties are not provided" *(p.11)*.

## Design Rationale
- **Three-tier grouping (Starting / Expanded / Qualified)**: supports *incremental adoption* — "PROV-O users may only need to use parts of the entire ontology, depending on their needs and according to how much detail they want to include" *(p.3)*.
- **Qualification pattern (intermediate class)**: keeps the base graph simple for consumers while allowing asserters to attach arbitrary RDF attributes without extending the binary-relation schema *(p.9)*.
- **PROV-DM back-references**: every class/property has a `PROV-DM term` pointer for auditability *(p.14)*.
- **Turtle-serialised examples**: conventional linked-data presentation; examples are informative but follow the ontology strictly.
- **Namespace stability**: `http://www.w3.org/ns/prov#` is the single namespace for all PROV documents (PROV-DM, PROV-O, PROV-N share it) *(p.3)*.

## Testable Properties
- Every instance of `prov:Generation` has exactly one `prov:activity` filler pointing to the generating activity *(p.41, Table 2)*.
- For any RDF triple `?e prov:wasGeneratedBy ?a`, adding `?e prov:qualifiedGeneration ?g ; ?g a prov:Generation ; ?g prov:activity ?a` MUST be valid (qualified form implies unqualified) *(p.11)*.
- `prov:Entity`, `prov:Activity`, and `prov:Agent` are NOT asserted disjoint — an Entity can simultaneously be an Agent in some contexts (e.g., `prov:Plan` is a subclass of `prov:Entity`, and `prov:SoftwareAgent` is a subclass of `prov:Agent`; nothing prevents a single resource from being both in principle) *(p.14-15 inferred)*.
- `prov:InstantaneousEvent` has four subclasses: `prov:Generation`, `prov:Start`, `prov:Invalidation`, `prov:End`, `prov:Usage` — all influence classes that are naturally instantaneous events *(p.46)*.
- Inverse-name reservation (Appendix B): if an asserter wants the inverse of `prov:wasDerivedFrom`, it MUST be named `prov:hadDerivation` in the PROV namespace — not an application-specific name *(p.66)*.
- Domain union of `prov:atLocation` is the 4-way union `{Activity, Agent, Entity, InstantaneousEvent}` *(p.65)*.
- Exactly **5** axioms violate OWL 2 RL (Table 5, p.65).

## Relevance to propstore
propstore's architecture treats **provenance as first-class metadata on every claim, stance, extraction, concept merge proposal, and render policy selection** (cf. CLAUDE.md: "Every probability that enters the argumentation layer must carry provenance: either empirical evidence counts, a calibrated model output, or an explicit vacuous marker"). PROV-O gives the normative vocabulary:
- **Entity** ↔ propstore's Claim, Concept, Form, Context (every persisted artifact).
- **Activity** ↔ extraction run, reconciliation run, merge operation, render invocation.
- **Agent** ↔ the LLM, the human user, the heuristic pipeline (prov:SoftwareAgent vs prov:Person).
- **wasDerivedFrom** ↔ source-of-truth lineage between source branch, proposal branch, merged artifact.
- **Bundle** ↔ propstore "source branch" (a named set of provenance assertions that itself has provenance — matches Git's commit-as-provenance model closely).
- **Qualification Pattern** ↔ the architecture's need to attach time, confidence, calibration-model identity, and reasoning role to every provenance-bearing edge.
- **Appendix B inverse reservation** ↔ propstore's cross-reference vocabulary discipline (avoid fracture of inverse naming across subsystems).
- **Five-axiom OWL-RL non-conformance trade-off** ↔ an explicit precedent for preferring modeling clarity over strict profile conformance when the alternative (placeholder named classes) hurts usability.

This paper is **P1 (provenance foundations)** in the semantic-substrate plan: the normative anchor for propstore's provenance type redesign.

## Open Questions
- [ ] How do propstore's `Context` (McCarthy `ist(c,p)`) objects map to PROV-O's `prov:Bundle`? Bundles name-scope a set of assertions but do not themselves qualify truth conditions — propstore's Context does. Hybrid term needed.
- [ ] Does propstore want to reserve its own `pks:` inverse-name convention following Appendix B's discipline, or reuse `prov:` reserved names where applicable?
- [ ] Which calibration / subjective-logic uncertainty attributes attach to a `prov:qualifiedInfluence` instance in propstore's render-layer model — do they go on the qualified-influence instance (Influence class) or on the influenced Entity (claim)?
- [ ] Should propstore treat LLM extractions as `prov:SoftwareAgent` activities, or would introducing a `pks:ModelAgent` subclass (following the PROV-O extension pattern) be warranted?

## Related Work Worth Reading (key cited)
- **PROV-DM** (Moreau & Missier, eds., 2013) — the PROV Data Model that PROV-O encodes. Required companion read.
- **PROV-CONSTRAINTS** (Cheney, Missier, Moreau, 2013) — inference/validity rules over PROV. Governs which PROV-O graphs are well-formed.
- **PROV-N** (Moreau, Missier, 2013) — human-consumption provenance notation; alternative syntax for the same model.
- **PROV-PRIMER** (Gil, Miles, 2013) — introductory companion; contains the crime-chart scenario used throughout PROV-O.
- **PROV-OVERVIEW** (Groth, Moreau, 2013) — document map; ought to be read first.
- **PROV-AQ** (Klyne, Groth, 2013) — access and query over PROV provenance.
- **PROV-SEM** (Cheney, 2013) — first-order-logic declarative semantics; bridges PROV-DM to formal reasoning.
- **PROV-LINKS** (Moreau, Lebo, 2013) — linking bundles across sources.
- **OWL2-PRIMER** / **OWL2-OVERVIEW** — OWL 2 spec baseline for understanding PROV-O's profile choices.
- **LD-Patterns-QR** (Dodds, Davis) — the "Qualified Relation" LD pattern that PROV-O's qualification pattern instantiates.
- **RFC 2119** — MUST/SHOULD/MAY compliance language.

## Provenance of These Notes
- Paper retrieved via headless Chrome print-to-pdf from https://www.w3.org/TR/prov-o/ on 2026-04-16.
- Notes produced by reading all 69 page PNGs (chunked reads at section boundaries plus dense reading of introductory and normative-table pages). Full coverage of Sections 1-3, Tables 2-6, Appendices A and B; sampled coverage of the repetitive Section 4 cross-reference (structure captured exhaustively, per-entry examples sampled).
- Canary-pilot notes; intended as a dense surrogate for downstream extract-claims / register-concepts workflows.
