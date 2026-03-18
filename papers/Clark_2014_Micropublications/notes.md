---
title: "Micropublications: a Semantic Model for Claims, Evidence, Arguments and Annotations in Biomedical Communications"
authors: "Tim Clark, Paolo N Ciccarese, Carole A Goble"
year: 2014
venue: "Journal of Biomedical Semantics"
doi_url: "https://doi.org/10.1186/2041-1480-5-28"
---

# Micropublications: a Semantic Model for Claims, Evidence, Arguments and Annotations in Biomedical Communications

## One-Sentence Summary

Defines a layered semantic metadata model (micropublications) for representing scientific claims with their supporting evidence, arguments, attributions, and inter-claim relationships, formalized in OWL and designed to overlay existing publication infrastructure.

## Problem Addressed

Scientific publications are documentary representations of defeasible arguments, but the linear document format (dating from 1665) cannot support machine-tractable verification of evidence, challenge/disagreement modeling, citation network analysis, or incremental annotation. Statement-based models (nanopublications, SWAN, BEL) model only the statements themselves, with limited or no representation of the backing evidence, claim networks, or argumentation structure. The micropublications model fills this gap by representing claims together with their complete evidentiary support graphs.

## Key Contributions

- A semantic metadata model for scientific argument and evidence, grounded in Toulmin-Verheij defeasible argumentation theory
- Nine use cases mapping the model to the lifecycle of biomedical communications (building citable claims, modeling evidence support, digital abstracts, claim network analysis, similarity groups, claim formalization, annotation/discussion, bipolar claim-evidence networks, contextualization via annotation ontologies)
- A formal ontology (OWL 2) at http://purl.org/mp with class, predicate, and rule definitions
- Design patterns for modeling claims at varying levels of complexity (minimal statement+attribution through full knowledge bases)
- Integration with the Open Annotation Model (OAM) for contextualizing micropublications within full-text documents
- Implementation in the Domeo web annotation toolkit

## Methodology

The paper:
1. Identifies nine use cases for micropublications by analyzing activities in the biomedical communications ecosystem lifecycle (authoring, reviewing, editing/publishing, DB/KB curation, searching, reading, discussion, evaluation, experiment design)
2. Grounds the model in Toulmin's defeasible argumentation framework, extending it with both "support" and "challenge/rebuttal" relations, and with inter-argumentation relations
3. Defines the model formally as a set of OWL classes and predicates
4. Illustrates the model through a series of increasingly complex case studies drawn from Alzheimer Disease research (Spilman et al. 2010, Harrison et al. 2009, Hsia et al. 1999, Bryan et al. 2009)
5. Shows how the model integrates with the W3C Open Annotation Model for document contextualization

## Core Ontology Classes and Relations

### Class Hierarchy

1. **Entity** - things which may be real or imaginary
   - **Agent** - an Entity that makes, modifies, consumes, or uses an Artifact
     - **Person**
     - **Organization**
   - **Artifact** - an Entity produced, modified, consumed, or used by an Agent
     - **Representation** - an Artifact that *represents* something
       - **Sentence** - a well-formed series of symbols intended to convey meaning
         - **Statement** - a declarative Sentence
           - **Claim** - the single principal Statement *arguedBy* a Micropublication
         - **Qualifier** - a Sentence which qualifies a Statement
           - **Reference** - a bibliographic qualifier
           - **SemanticQualifier** - a semantic tag
       - **Data** - empirical scientific evidence
       - **Method** - a reusable recipe (Procedure or Material)
       - **Attribution** - provenance information
       - **Micropublication** - a set of Representations with support/challenge relations
       - **ArticleText** - text from a publication

2. **Activity** - a process by which an Artifact is produced, modified, consumed, or used

### Key Properties

| Property | Domain | Range | Description |
|----------|--------|-------|-------------|
| argues | Micropublication | Claim | The Claim the MP argues for |
| hasAttribution | Micropublication | Attribution | Attribution of the MP |
| supports | Representation | Representation | Transitive support relation |
| challenges | Representation | Representation | Inferred when one Representation *directlyChallenges* another or *indirectlyChallenges* by undercutting support |
| directlyChallenges | Representation | Representation | Direct opposition |
| indirectlyChallenges | Representation | Representation | Undercutting support for another |
| qualifiedBy | Statement | Qualifier | Semantic or reference qualifier |
| supportedByData | Statement | Data | Data supports statement |
| supportedByMethod | Data | Method | Method supports data |
| assertedBy | Representation | Micropublication | Originally instantiated by that MP |
| quotedBy | Representation | Micropublication | Quoted after first being instantiated elsewhere |
| elementOf | Representation | Micropublication | Membership in MP |
| hasSupportGraphElement | Micropublication | Representation | Element of support graph |
| hasChallengeGraphElement | Micropublication | Representation | Element of challenge graph |
| attributionOfAgent | Attribution | Agent | Who made the attribution |
| hasHolotype | Claim | Claim | Representative exemplar of a similarity group |

### Mathematical Representation

Let *a* denote the text of an argument (e.g., sections of a scientific article). Let MP_a denote its formalization as a Micropublication.

$$
MP\_a = (A\_mpa, c, A\_c, \Phi, R)
$$

Where:
- *a* := an argument text, represented in a document
- *MP_a* := a micropublication, or formalized argument structure, defined on *a*
- *A_mpa* := the Attribution of this formalization of *a* as a micropublication
- *c* is an element of *Phi*: a single Statement, being the principal Claim of *a*
- *A_c* := the Attribution of the Claim *c*
- *Phi* is a finite non-empty set of Representations which are elements of the Micropublication
- R is a subset of Phi x Phi: where R is a nonempty disjoint union of supports (R+) and challenges (R-) relations, r(phi_i, phi_j); Phi+ is a subset of Phi is the nonempty set of all phi_i covered by R+; R+ is a strict partial order over Phi+, whose greatest element is c, the principal Claim of the argument in a

### Complexity Spectrum

The model accommodates a spectrum of representations:
- **Minimal**: A single identified Statement with its Attribution (Figure 3)
- **Simple**: Claim + Statement paraphrase + Reference attribution (Example 1, Figure 7)
- **Evidence-backed**: Claim + Data + Methods + Attribution (Example 2, Figure 8)
- **Digital abstract**: Full claim with all supporting Statements, Data, Methods, and backing References (Example 3, Figure 9)
- **Cross-publication network**: Claims connected across multiple publications via claim lineages (Example 4, Figures 10-11)
- **Similarity groups**: Equivalent claims from different publications normalized to a Holotype representative (Example 5, Figures 12-13)
- **Formalized**: Claims translated to formal languages like BEL with provenance preserved (Example 6, Figures 14-15)
- **Annotated**: Annotations modeled as micropublications referencing original claims (Example 7, Figure 16)
- **Challenged**: Bipolar networks showing support and challenge relations between claims (Example 8, Figures 17-18)
- **Contextualized**: Micropublications embedded as OAM annotations in full-text documents (Example 9, Figure 19)

## Nine Use Cases

| # | Use Case | Description |
|---|----------|-------------|
| 1 | Building and Using Citable Claims | Constructing libraries of citable Claims with reference attribution |
| 2 | Modeling Evidence Support for Claims | Enhancing citable Claims with supporting Data and reproducible Methods |
| 3 | Producing Digital Abstracts | Computable digital abstracts based on citable Claims, Statements, Data, Methods |
| 4 | Claim Network Analysis | Determining origin of, and evidence for, individual and contrasting claims |
| 5 | Representing Common Meaning | Similarity groups with Holotype representatives for equivalent claims |
| 6 | Claim Formalization | Translation of natural-language claims to formal vocabularies (BEL, ACE) |
| 7 | Modeling Annotation and Discussion | Annotations, comments, discussion as micropublications |
| 8 | Building Bipolar Claim-Evidence Networks | Support/attack relationships for alternative interpretations and hypotheses |
| 9 | Contextualizing Micropublications | Annotation ontology (OAM) integration for document-level contextualization |

Table 2 (page 6) maps these use cases to nine activities in the biomedical communications lifecycle.

## Key Concepts

### Claim Lineages
When support relations are resolved across micropublications (e.g., MP3 quotes C3 from Spilman, which is supported by S1 citing Harrison [109], whose Claim C1.1 is the actual backing), the graphs C1.1 -> S1 and C2.1 -> S2 are called **Claim Lineages**, by analogy with biological lineages.

### Similarity Groups and Holotypes
Groups of *similar* statements (equivalence classes defined by "sufficient" closeness in meaning) are represented with a representative exemplar called a **Holotype**. The *similog-holotype model* is empirically based, allowing normalization of diverse statements to a common natural language representation without dropping qualifiers or hedging. Translations to formal languages or other natural languages may also be considered similogs.

### Asserts vs. Quotes
- A Representation **assertedBy** a Micropublication is originally instantiated by that MP
- A Representation **quotedBy** a Micropublication is referred to by that MP after first being instantiated elsewhere
- This distinction enables proper attribution tracking when claims are imported across publication boundaries

### Challenge Relations
- *directlyChallenges*: explicit opposition to a claim
- *indirectlyChallenges*: undercutting a support element of a claim
- Both are modeled as elements of the MP's ChallengeGraph
- Challenges can originate from within a publication (Case 1) or from outside (Case 2, by a third-party curator)

## Comparison with Statement-Based Models (Table 1, page 3)

| Feature | SWAN | Nanopublications | BEL |
|---------|------|------------------|-----|
| First specification | 2008 | 2010 | 2011 |
| Statements in | Natural language | Formal language | Formal language |
| Statement provenance | SWAN-PAV ontology | SWAN-PAV ontology | SWAN-PAV ontology |
| Backing references from literature | Yes | Yes | Yes |
| Support claim networks | No | No | No |
| Direct empirical scientific evidence | No | No | No |

Micropublications go beyond all three by supporting claim networks, direct empirical evidence, similarity groups, and challenge/disagreement modeling.

## Figures of Interest

- **Fig 1 (page 4):** Nanopublication representation of statements and evidence (NP -> Assertion -> Support -> Provenance)
- **Fig 2 (page 7):** Activity lifecycle of biomedical communications, mapping 9 use cases to 9 activities in a cycle
- **Fig 3 (page 10):** Minimal form of a micropublication (Statement + Attribution)
- **Fig 4 (page 11):** Simplified model showing Claim supported by Statement, Data, Method, with References and Attribution
- **Fig 5 (page 12):** Full class diagram showing all major classes and relationships in the model
- **Fig 6 (page 13):** Concrete example - representation of Spilman et al. claim about rapamycin/mTOR
- **Fig 7 (page 15):** Example 1 - Citable claim with semantic qualifiers
- **Fig 8 (page 16):** Example 2 - Scientific evidence (Data + Methods) supporting a claim
- **Fig 9 (page 17):** Example 3 - Full digital abstract micropublication
- **Fig 10 (page 18):** Example 4 - Transition from document-level to claim-level backing references
- **Fig 11 (page 18):** Example 4 - Connected support relations across three publications (claim network)
- **Fig 12 (page 20):** Example 5 - Similarity Group with Holotype claim
- **Fig 13 (page 21):** Example 5 - Homology group as a micropublication
- **Fig 14 (page 22):** Example 6 - BEL representation at document level
- **Fig 15 (page 22):** Example 6 - BEL representation with claim-level resolution
- **Fig 16 (page 23):** Example 7 - Annotation using micropublication relations
- **Fig 17 (page 24):** Example 8 - Challenge relation (Claim C11 challenges Statement S3)
- **Fig 18 (page 25):** Example 8 - Annotation of inconsistency between two publications as independent MP
- **Fig 19 (page 26):** Example 9 - Contextualizing a claim within full-text using Open Annotation
- **Fig 20 (page 27):** Citation distortion - claim network from Greenberg 2009 showing unfounded authority
- **Fig 21 (page 29):** Domeo version 2 software implementation for creating micropublications

## Implementation Details

### Domeo Web Annotation Toolkit
- Open source, licensed under Apache 2.0
- Plug-in based architecture with browser-based interface
- Knowledgebase, parsers, web services, proxy server
- Supports profile-based selection of user interfaces
- Peer-to-peer knowledge base communication
- Private, group-specific, or public annotations
- Version 1: SWAN ontology annotations
- Version 2: Micropublications-based annotation functionality
- Active use in Neuroscience Information Framework, drug-hunting teams, pharmaceutical companies

### OWL Vocabulary
- Available at http://purl.org/mp
- W3C Web Ontology Language (OWL 2)
- RDF examples provided in Additional file 1
- Class, Predicate, and DL-safe Rule definitions in Additional file 2
- Comparison to SWAN model in Additional file 3

### Integration with Open Annotation Model (OAM)
- W3C Open Annotation Community Group standard
- Annotation created on HTML targets exported as RDF
- Referenced independently by PDF viewer (Utopia)
- Contextualization via oa:Annotation, oa:hasBody, oa:hasTarget, oa:SpecificResource, oa:hasSelector

## Results Summary

The micropublications model successfully represents scientific arguments at varying levels of complexity, from simple attributed statements to complex cross-publication claim-evidence networks with challenge/support relations. Nine use cases demonstrate applicability across the entire biomedical communications lifecycle. The model is backward-compatible with statement-based formalisms (nanopublications, BEL) while providing richer argumentation structure. Implementation in Domeo version 2 demonstrates practical feasibility.

## Limitations

- The model is complex; full deployment of all concepts is not required for any particular scenario but may be overwhelming
- Adoption depends on creation of useful software tools
- Similarity/holotype determination is subjective ("sufficient" closeness is application-dependent)
- The model does not assign explicit ontological status to Statements (avoids the philosophical problem but leaves it unresolved)
- Citation-level claim resolution requires significant human effort (reading cited works, identifying backing claims)
- Reagent-level citation tracking requires publisher/author action beyond the model itself
- The model does not itself solve the problem of verifying whether cited evidence actually exists or is fabricated

## Testable Properties

- A Micropublication must have exactly one Claim (the principal Statement)
- A Micropublication must have exactly one Attribution (hasAttribution)
- The supports relation must form a DAG (directed acyclic graph) rooted at the Claim
- Every element of a SupportGraph must be an elementOf the Micropublication
- The challenges relation is inferred: directlyChallenges OR indirectlyChallenges (which undercuts a support element)
- A Representation can only be assertedBy one Micropublication (original instantiation)
- A Representation may be quotedBy multiple Micropublications
- Similarity groups form equivalence classes; each group has exactly one Holotype
- The minimal valid Micropublication consists of: Claim + Attribution
- R+ (support relations) must be a strict partial order over the support graph elements

## Relevance to Project

This paper is directly foundational for the propstore's claim representation architecture. The micropublications model provides the theoretical framework for:
1. **Claim structure**: The Claim/Statement/Data/Method hierarchy maps directly to the propstore's claim types (parameter, equation, observation, model, measurement)
2. **Provenance tracking**: The Attribution and Reference model informs provenance.paper, provenance.page, provenance.quote_fragment
3. **Cross-paper relationships**: The supports/challenges relations and claim lineages map to the propstore's stances (supported_by, contradicted_by, superseded_by, mechanism_for)
4. **Similarity groups and holotypes**: The similog-holotype model provides theoretical grounding for the propstore's concept of reconciling equivalent claims across papers
5. **Evidence grounding**: The requirement that claims be backed by empirical evidence (Data + Methods), not just statements, aligns with the propstore's emphasis on grounding claims in verifiable data

## Open Questions

- [ ] How does the propstore's claim schema map specifically to the micropublication ontology classes?
- [ ] Could the propstore adopt the asserts/quotes distinction for tracking claim provenance across papers?
- [ ] Is the holotype/similog model useful for the propstore's claim reconciliation workflow?
- [ ] How should the challenge/support distinction map to the propstore's stance types?

## Related Work Worth Reading

- Toulmin S: The Uses of Argument (1958/2003) - foundational argumentation model
- Groth P, Gibson A, Velterop J: The anatomy of a nanopublication (2010) - statement-based model comparison → NOW IN COLLECTION: [[Groth_2010_AnatomyNanopublication]]
- Greenberg SA: How citation distortions create unfounded authority (2009) - motivation for claim networks
- Verheij B: Artificial argument assistants (2003/2005) - bipolar argumentation frameworks
- Carroll JJ et al: Named graphs, provenance and trust (2005) - RDF named graph foundations
- Ciccarese P et al: The SWAN biomedical discourse ontology (2008) - predecessor model

## Collection Cross-References

### Now in Collection (previously listed as leads)
- [[Groth_2010_AnatomyNanopublication]] — Defines nanopublication model (concept→triple→statement→annotation→nanopublication) with RDF Named Graph serialization. Structurally analogous to the micropublication model but focused on Semantic Web interoperability rather than argumentation structure. Clark's model adds supports/challenges argumentation; Groth provides concrete RDF serialization.

### Conceptual Links (not citation-based)
- [[Groth_2010_AnatomyNanopublication]] — **Strong.** Both define atomic scientific assertion models with layered provenance. Complementary formalizations: Clark adds argumentation structure, Groth adds Semantic Web serialization.
