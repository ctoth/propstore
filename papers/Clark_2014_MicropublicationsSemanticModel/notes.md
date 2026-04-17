---
title: "Micropublications: a Semantic Model for Claims, Evidence, Arguments and Annotations in Biomedical Communications"
authors: "Tim Clark, Paolo N. Ciccarese, Carole A. Goble"
year: 2014
venue: "Journal of Biomedical Semantics"
doi_url: "https://doi.org/10.1186/2041-1480-5-28"
arxiv_id: "1305.3506v4"
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-04-03T07:59:20Z"
---
# Micropublications: a Semantic Model for Claims, Evidence, Arguments and Annotations in Biomedical Communications

## One-Sentence Summary
This paper presents a formal semantic model for representing scientific claims, their supporting evidence (data and methods), argumentation structure (support and challenge), attribution/provenance, and annotations in biomedical literature, grounded in argumentation theory and implemented as an OWL ontology with a web annotation tool (Domeo).

## Problem Addressed
Existing statement-based models for biomedical literature (SWAN, nanopublications, BEL) cannot (1) build transitive claim networks linking claims to underlying empirical evidence across publications, (2) model multipolar argumentation (support AND challenge), or (3) formally ground scientific discourse in argumentation theory. Citation distortions are rampant — Greenberg 2009 showed claims propagated without adequate evidence, and only 10-20% of cited papers are actually read by citing authors (Simkin & Roychowdhury). The paper provides a model that can trace claims back to their empirical basis and make the argumentation structure explicit. *(p.2-6)*

## Key Contributions
- A formal semantic model (Micropublications) for scientific claims, evidence, arguments, and annotations that is grounded in argumentation theory *(p.2-3)*
- A formal definition: MP = (A, mp, c, A_c, Phi, R) with explicit SupportGraph and ChallengeGraph DAGs *(p.19)*
- Nine detailed use cases demonstrating the model's applicability across the biomedical communications ecosystem *(p.5-8, Table 2 on p.6; detailed examples p.9-35)*
- Comparison with SWAN, nanopublications, and BEL showing the model's advantages in transitivity, multipolar argumentation, and evidence grounding *(p.4-5, 39-40)*
- An OWL ontology implementation using Open Annotation (OA) as the annotation framework *(p.34)*
- A prototype implementation in the Domeo web annotation toolkit *(p.38-39)*
- Analysis of citation distortion networks using the micropublication formalism *(p.36-37)*

## Nine Use Cases

*(p.5–8, Table 2 on p.6)*

| # | Use Case | Description | Page |
|---|----------|-------------|------|
| 1 | Building and Using Citable Claims | Constructing libraries of citable Claims with reference attribution | p.6, p.14 |
| 2 | Modeling Evidence Support for Claims | Enhancing citable Claims with supporting Data and reproducible Methods | p.6, p.15 |
| 3 | Producing Digital Abstracts | Computable digital abstracts based on citable Claims, Statements, Data, Methods | p.6, p.16 |
| 4 | Claim Network Analysis | Determining origin of, and evidence for, individual and contrasting claims | p.7, p.17 |
| 5 | Representing Common Meaning | Similarity groups with Holotype representatives for equivalent claims | p.8, p.19 |
| 6 | Claim Formalization | Translation of natural-language claims to formal vocabularies (BEL, ACE) | p.8, p.21 |
| 7 | Modeling Annotation and Discussion | Annotations, comments, discussion as micropublications | p.8, p.22 |
| 8 | Building Bipolar Claim-Evidence Networks | Support/attack relationships for alternative interpretations and hypotheses | p.8, p.23 |
| 9 | Contextualizing Micropublications | Annotation ontology (OAM) integration for document-level contextualization | p.8, p.25 |

Table 2 (p.6) maps these nine use cases to nine activities in the biomedical communications lifecycle (authoring, reviewing, editing/publishing, DB/KB curation, searching, reading, discussion, evaluation, experiment design).

## Complexity Spectrum

The model accommodates a spectrum of representational complexity: *(p.13–26)*

- **Minimal**: A single identified Statement with its Attribution (Figure 3) *(p.10)*
- **Simple**: Claim + Statement paraphrase + Reference attribution (Example 1, Figure 7) *(p.14–15)*
- **Evidence-backed**: Claim + Data + Methods + Attribution (Example 2, Figure 8) *(p.15–16)*
- **Digital abstract**: Full claim with all supporting Statements, Data, Methods, and backing References (Example 3, Figure 9) *(p.16–17)*
- **Cross-publication network**: Claims connected across multiple publications via claim lineages (Example 4, Figures 10-11) *(p.17–18)*
- **Similarity groups**: Equivalent claims from different publications normalized to a Holotype representative (Example 5, Figures 12-13) *(p.19–21)*
- **Formalized**: Claims translated to formal languages like BEL with provenance preserved (Example 6, Figures 14-15) *(p.21–22)*
- **Annotated**: Annotations modeled as micropublications referencing original claims (Example 7, Figure 16) *(p.22–23)*
- **Challenged**: Bipolar networks showing support and challenge relations between claims (Example 8, Figures 17-18) *(p.23–25)*
- **Contextualized**: Micropublications embedded as OAM annotations in full-text documents (Example 9, Figure 19) *(p.25–26)*

## Key Concepts

### Class Hierarchy (tree view)

*(p.10–11)* — the paper's full class taxonomy rendered as a tree:

1. **Entity** — things which may be real or imaginary
   - **Agent** — an Entity that makes, modifies, consumes, or uses an Artifact
     - **Person**
     - **Organization**
   - **Artifact** — an Entity produced, modified, consumed, or used by an Agent
     - **Representation** — an Artifact that *represents* something
       - **Sentence** — a well-formed series of symbols intended to convey meaning
         - **Statement** — a declarative/truth-bearing Sentence
           - **Claim** — the single principal Statement *arguedBy* a Micropublication
         - **Qualifier** — a Sentence which qualifies a Statement
           - **Reference** — a bibliographic qualifier
           - **SemanticQualifier** — a semantic tag
       - **Data** — empirical scientific evidence
       - **Method** — a reusable recipe (Procedure or Material)
       - **Attribution** — provenance information
       - **Micropublication** — a set of Representations with support/challenge relations
       - **ArticleText** — text from a publication
2. **Activity** — a process by which an Artifact is produced, modified, consumed, or used *(p.10)*

### Key Properties (extended)

*(p.11–12)*

| Property | Domain | Range | Description | Page |
|----------|--------|-------|-------------|------|
| argues | Micropublication | Claim | The Claim the MP argues for | p.11 |
| hasAttribution | Micropublication | Attribution | Attribution of the MP | p.11 |
| supports | Representation | Representation | Transitive support relation | p.11 |
| challenges | Representation | Representation | Inferred: *directlyChallenges* OR *indirectlyChallenges* via undercutting support | p.12 |
| directlyChallenges | Representation | Representation | Direct opposition | p.12 |
| indirectlyChallenges | Representation | Representation | Undercutting support for another | p.12 |
| qualifiedBy | Statement | Qualifier | Semantic or reference qualifier | p.11 |
| supportedByData | Statement | Data | Data supports statement | p.11 |
| supportedByMethod | Data | Method | Method supports data | p.11 |
| assertedBy | Representation | Micropublication | Originally instantiated by that MP | p.11 |
| quotedBy | Representation | Micropublication | Quoted after first being instantiated elsewhere | p.11 |
| elementOf | Representation | Micropublication | Membership in MP | p.11 |
| hasSupportGraphElement | Micropublication | Representation | Element of support graph | p.11 |
| hasChallengeGraphElement | Micropublication | Representation | Element of challenge graph | p.12 |
| attributionOfAgent | Attribution | Agent | Who made the attribution | p.11 |
| hasHolotype | Claim | Claim | Representative exemplar of a similarity group | p.19 |

### Claim Lineages

When support relations are resolved across micropublications (e.g., MP3 quotes C3 from Spilman, which is supported by S1 citing Harrison, whose Claim C1.1 is the actual backing), the resolved graphs C1.1 → S1 and C2.1 → S2 are called **Claim Lineages** — by analogy with biological lineages. *(p.17–18)*

### Asserts vs. Quotes

- A Representation **assertedBy** a Micropublication is originally instantiated by that MP *(p.11)*.
- A Representation **quotedBy** a Micropublication is referred to by that MP after first being instantiated elsewhere *(p.11)*.
- This distinction enables proper attribution tracking when claims are imported across publication boundaries, and prevents misattribution. *(p.11)*

### Ontological Status of Statements (Strawson)

The model deliberately avoids assigning explicit ontological status to Statements — whether true/false, real/imaginary. Following Strawson: "meaning" is expressed in the language of the statement, while "truth" is a property of its assertion in context. The model sidesteps the philosophical problem and represents both meaning and assertion separately. *(p.20)*

### "Current Best Explanation" Record

Scientific claims in the literature form an open, incrementally-constructed record which changes over time as claims are challenged and reassessed. The model treats the literature as a defeasible record rather than a fixed truth store. *(p.4, p.9)*

## Methodology
The paper is a model/ontology design paper, not an empirical study. The methodology consists of:
1. Analysis of existing statement-based models (SWAN, nanopublications, BEL) and identification of gaps *(p.4-5)*
2. Definition of use cases from the biomedical communications ecosystem *(p.9)*
3. Formal definition of the Micropublications model with abstract mathematical representation *(p.19)*
4. Worked examples from Alzheimer's Disease research (amyloid cascade hypothesis) *(p.8)*
5. OWL ontology construction using Open Annotation framework *(p.34)*
6. Prototype implementation in Domeo *(p.38)*

## Key Equations / Statistical Models

$$
MP_a = (A, mp, c, A_c, \Phi, R)
$$
Where:
- $A$ = an argument text, represented in a document
- $mp$ = a micropublication, or formalized argument structure, defined on $A$
- $c$ = a single Statement, being the principal Claim of $A$
- $A_c \in \Phi$ = the Attribution of the Claim $c$
- $\Phi$ = a finite, non-empty set of Representations which are elements of the Micropublication
- $R \subseteq \Phi \times \Phi$, $R$ being a summary set of supports and challenges relations, $r(\Phi_i, \Phi_j) | R$ is a strict partial order over $\Phi$ and its greatest element is $c$, the principal Claim of $A$
*(p.19)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Citing papers actually read | — | % | 10-20% | — | 6 | Simkin & Roychowdhury finding |
| Papers with cherry-picked data | — | % | — | — | 6 | Begley & Ellis 2012 |
| Retracted papers still cited positively | — | % | — | — | 6 | Neale et al. |
| Greenberg citation network size | — | publications | 8 | — | 37 | Supplemental data example |

## Methods & Implementation Details

### Model Architecture
- **Entities, Agents, Artifacts, Activities and Representations** are the top-level classes *(p.16)*
  - Entities: things which may be discussed (real or imaginary)
  - Agents: Entities that make, modify, comment, or use Artifacts
  - Artifacts: Entities produced, modified, consumed, or used by Agents
  - Activities: processes by which Artifacts are produced, modified, consumed, or used
  - Representations: Artifacts that represent something
- **Representation subtypes**: Sentence, Data, Method, Micropublication, Attribution, Artifact/Event *(p.16-17)*
- A **Sentence** is a well-formed series of symbols intended to convey meaning *(p.17)*
- A **Statement** is a truth-bearing Sentence *(p.17)*
- A **Claim** is the single principal Statement argued by a Micropublication *(p.17)*
- **Data** may be supported by Method; a description of how data was obtained *(p.17)*
- A **Method** is a reusable recipe (procedure or Material) *(p.15)*
- **Attribution** is attached to both the statement and the identification; may be as complex as an entire knowledge base *(p.13)*

### Support and Challenge Relations
- **supports** property is transitive between Representations *(p.17)*
- **challenges** property is induced when a Representation either directly challenges another, or by undermining (deleting) a Representation which supports it *(p.17)*
- The **SupportGraph** consists of Representations related to the Claim by the supports property, and which are *closest* to that Micropublication *(p.17)*
- The **ChallengeGraph** works similarly with hasChallengeGraphElement *(p.17)*
- Both are structured as directed acyclic graphs (DAGs) *(p.17)*
- A Micropublication is a set of Representations, having supports and/or challenge relations to one another and potentially to those which are not closest to either Micropublication *(p.17)*

### Semantic Qualifiers
- Statements may be variously qualified: some SemanticQualifiers include **References** and **Semantics(Qualifier/tags)** *(p.17)*
- A **Qualifier** is a Sentence which may modify a Statement *(p.17)*

### Formal Argument Structure (Toulmin-Verheij mapping)
- **Claim** = the principal Statement = Toulmin's "claim" *(p.14-15)*
- **Warrant** = the paraphrase that supports belief = Toulmin's "warrant" *(p.14)*
- **Backing** = the citation/reference that validates the warrant = Toulmin's "backing" *(p.14-15)*
- Warrant and Backing are *relative terms* — to construct a network, we need to have backing in the form of a single statement from another work *(p.15)*
- The SupportGraph is the set of relations: supports(A_c, C3, C1), supports(D1.3, C3), supports(M1, D1), supports(M2, D1) *(p.20)*

### Similarity Groups and Holotypes
- A **Similarity Group** is a set of Statements with similar or identical meaning *(p.27)*
- A **Holotype** is the representative of the group, selected as a matter of convenience and exemplification — to stand for the common meaning of the Statements in the group *(p.27)*
- Concept borrowed from biological taxonomy; implemented as RAFT system (preferred exemplar) *(p.27)*
- Holotypes are *not* universals or Platonic forms — they are selected exemplars *(p.27)*
- The group-of-similogs / holotype approach is empirical, based on the notion that scientific communication is fundamentally a social activity *(p.27)*

### BEL Formalization
- Claims can be translated into Biological Expression Language (BEL) format *(p.28)*
- BEL statement = triple in relational database: statement text + reference to source document *(p.29)*
- Example: `{"w(CHEBI:9168) = kin(p(HGNC:FRAP1))"`, "PMID: 12069768"} *(p.29)*
- BEL statements can be modeled as Micropublications with document-level or claim-level support *(p.29-30)*

### OWL Ontology Implementation
- Uses Open Annotation (OA) ontology, orthogonal to the domain ontology and model ontology *(p.34)*
- Previously used Annotation Ontology (AO) [56, 57]; transitioned to OA richer model *(p.34)*
- "Stand-off annotation" = annotation is stored separately and references the document via a special set of mechanisms *(p.35)*
- AO and OA both allow free text, social tagging, or semantic tagging of Web documents using stand-off annotation *(p.35)*
- Selectors specify prefix, target, postfix, and range; image selector for figures *(p.35)*
- OA annotations can be exported in RDF and retrieved independently *(p.35)*

### Domeo Implementation
- Domeo: web-document annotation toolkit [17, 55, 58], version 2 release *(p.35)*
- Open source, licensed under Apache 2.0 *(p.35)*
- Alpha UI plugin for creating micropublications *(p.38)*
- MongoDB backend for storage *(p.38)*
- Can serialize and store in MongoDB or other database; can deploy for alpha testing *(p.38)*

### Nanopublication Recruitment
- A nanopublication assertion can be "recruited" as an mp:Claim and encapsulated within a Micropublication *(p.36)*
- Figure 20 shows how a nanopublication's assertion becomes a Claim with provenance preserved *(p.36)*

## Figures of Interest
- **Fig 1 (p.10):** Activity lifecycle of biomedical communications linked to use cases — inputs, activities, outputs
- **Fig 3 (p.15):** Minimal form of a Micropublication: Claim + SupportGraph + Attribution
- **Fig 4 (p.16):** Full Micropublication with Statement, References, Scientific Evidence, Method, and reusable Method
- **Fig 5 (p.18):** Major classes and relationships in the model — Claim is main Statement argued by Micropublication
- **Fig 6 (p.19):** Formal representation of statements and evidence with SupportGraph, author attribution, and PubMed URIs
- **Fig 7 (p.20):** Example 1 in Toulmin-Verheij terminology — Warrant, Backing, Claim
- **Fig 8 (p.22):** Scientific Evidence = Data (composite image) + Methods (M1, M2) supporting Claim C3
- **Fig 9 (p.24):** Full micropublication for principal claim of Bhatt et al. 2010 with backing references
- **Fig 10 (p.25):** Transition from document-level backing references to claim-level backing
- **Fig 11 (p.25):** Connected support relations across three publications forming a Claim network
- **Fig 12 (p.28):** Similarity Group with representative (Holotype) Claims — Holotype is one of three additional publications outside the Claim Lineage
- **Fig 13 (p.29):** Similarity group as micropublication with user-defined holotype
- **Fig 14 (p.30):** BEL representation of a Claim with document-level support resolved from PubMed ID
- **Fig 15 (p.30):** BEL representation with support resolved to Claim level — S4 is the specific Claim translated into BEL
- **Fig 16 (p.31):** Annotation using Micropublication relations — C18 as Claim by annotator, supported by Statement C1
- **Fig 17 (p.33):** Claim C11 challenges Statement S3 across micropublications — FDAPP mice confounding
- **Fig 18 (p.34):** Annotation of inconsistency between MP3/S3 and MP11/C11 — challenge relationships
- **Fig 19 (p.35):** Contextualizing a Claim within a full-text document using Open Annotation ontology
- **Fig 20 (p.36):** Nanopublication assertion recruited as mp:Claim within a Micropublication
- **Fig 21 (p.37):** Claim network from Greenberg 2009 — citation distortion with 8 publications, showing unsupported claims
- **Fig 22 (p.39):** Creating a micropublication in Domeo version 2 alpha UI plugin

## Results Summary
The Micropublications model provides a comprehensive semantic framework for representing:
1. Scientific claims with explicit support graphs (data + methods) *(p.14-17)*
2. Challenge/disagreement relations enabling multipolar argumentation *(p.31-34)*
3. Cross-publication claim networks with transitive support relations *(p.25-26)*
4. Citation distortion detection by tracing claims to their empirical basis *(p.36-37)*
5. Annotation of existing publications with formal argumentation structure *(p.30-31)*
6. Similarity groups for vocabulary normalization across claims *(p.27)*
7. Formalization in BEL for computational biology applications *(p.28-30)*

The model was implemented as an OWL ontology using Open Annotation and prototyped in the Domeo web annotation toolkit. *(p.34-39)*

## Limitations
- The model does not address automated extraction — it requires manual annotation or tool-assisted markup *(p.38)*
- Scalability of manual annotation is acknowledged as a barrier; the authors suggest integration with bibliography management tools *(p.38)*
- The Domeo implementation was alpha-stage at time of publication *(p.38)*
- The model does not formally verify argumentation properties (e.g., no extension computation) — it provides the representational framework only *(p.40)*
- SWAN comparison reveals: SWAN does not model multipolar argumentation; Micropublications do, but lack SWAN's formal claim-level statement similarity mechanisms *(p.40)*
- The paper acknowledges that purely statement-based models are too unstructured to deal with scientific controversy and evidentiary requirements *(p.40)*
- Widespread adoption depends on useful software environments that don't exist yet in the form of scholarly tooling *(p.41)*

## Arguments Against Prior Work
- **Nanopublications** model only the informal statement; lack attribution for supporting statements, backing references, or any notion of challenge *(p.4-5)*
- **SWAN** models a principal statement with supporting statements and claims from same publication only; cannot transitively link to underlying evidence across publications *(p.4-5)*
- **BEL** provides backing from literature but associates one or more PubMed identifiers with every statement — no structured evidence or methods, and at the original point of extraction the actual Backing could have been cited directly *(p.12, 28)*
- None of the three prior models provide a means to transitively close claim linkages to underlying empirical evidence — because they don't represent it *(p.4)*
- None of the three prior models provide a means to build claim networks of arbitrary depth *(p.4)*
- Table 1 comparison (p.5): SWAN and nanopublications lack support claim networks, direct empirical evidence, and scientific evidence modeling capabilities that Micropublications provide
- Greenberg's work on citation distortions *(p.6, 36-37)* demonstrates that the biomedical literature contains claims propagated without evidence basis — a problem the Micropublications model is designed to address
- Statement-based models are criticized for being too unstructured to deal with scientific controversy and evidentiary requirements *(p.40)*

## Design Rationale
- **Why argumentation theory?** The model is explicitly grounded in argumentation theory (Toulmin, Verheij) because scientific discourse is inherently argumentative — claims must be supported by evidence and can be challenged *(p.7, 14)*
- **Why transitive support?** Document-level citations are inadequate; tracing claims to empirical evidence requires transitive linking through intermediate claims *(p.25-26)*
- **Why holotypes instead of universals?** Scientific meaning is socially constructed and context-dependent; selecting representative exemplars is more practical than defining abstract universals *(p.27)*
- **Why Open Annotation?** OA provides stand-off annotation that is orthogonal to both the domain ontology and the model ontology, enabling annotation of any web document without modifying it *(p.34)*
- **Why separate SupportGraph and ChallengeGraph?** Scientific discourse involves both supporting and undermining relations; collapsing these loses critical information about the nature of the relationship *(p.17)*
- **Why not extend SWAN?** SWAN lacks multipolar argumentation, is not grounded in argumentation theory, and cannot represent challenge relations as first-class constructs *(p.39-40)*

## Testable Properties
- The supports relation is transitive: if A supports B and B supports C, then there is a support path from A to C *(p.17)*
- The SupportGraph and ChallengeGraph are DAGs (directed acyclic graphs) — no cycles allowed *(p.17)*
- R is a strict partial order over Phi with the Claim c as its greatest element *(p.19)*
- Every element of the Micropublication (every Phi_i) must have Attribution (A_c in Phi) *(p.17)*
- A Micropublication's minimal form requires exactly: one Claim, one SupportGraph, and one Attribution *(p.15)*
- Similarity Groups must have exactly one Holotype *(p.27)*
- A Claim must be a Statement (truth-bearing Sentence), not merely a Sentence *(p.17)*
- Challenge relationships require that the challenging statement be part of a different Micropublication (external criticism) or an annotation micropublication *(p.31-33)*

## Relevance to Project
**Rating: High** — This paper is directly relevant to multiple propstore layers, including both the argumentation layer and the concept/vocabulary layer.

1. **Claim representation**: The Micropublications model provides a formal framework for claims with provenance, evidence, and argumentation structure — closely aligned with propstore's claim storage layer
2. **Support/Challenge as bipolar argumentation**: The SupportGraph/ChallengeGraph structure maps directly to Cayrol 2005 bipolar argumentation (already implemented in propstore)
3. **Similarity Groups / Holotypes for vocabulary reconciliation**: The concept of grouping equivalent claims under a canonical representative (Holotype, p.27) is directly the problem propstore's vocabulary reconciliation solves. The Holotype is not a Platonic universal but a selected exemplar — this matches propstore's `canonical_name` in the concept registry, which is a chosen representative, not a definition. The Similarity Group mechanism provides a formal model for how propstore should group variant surface expressions of the same concept.
4. **Non-commitment discipline**: The model preserves multiple viewpoints without forcing resolution, aligning with propstore's core design principle. Similarity Groups explicitly preserve all variants while designating one as representative — never collapsing to a single form.
5. **Transitive evidence chains**: The model's transitive support linking maps to propstore's ASPIC+ argument construction with recursive premise chains
6. **Attribution/Provenance**: Every element carries provenance, matching propstore's provenance requirements
7. **Claim-level vs document-level resolution**: The paper's progression from document-level backing to claim-level backing (Figs 10-11, p.24-25) models a problem propstore faces: whether provenance attaches to an entire source or to specific claims within it

## Open Questions
- [ ] How does the Micropublications model handle conflicting evidence weights? (No quantitative mechanism provided)
- [ ] Can the Holotype/Similarity Group concept be formalized as an equivalence class with a canonical representative in propstore's concept registry?
- [ ] How would the SupportGraph/ChallengeGraph DAG constraint interact with ASPIC+ recursive argument construction?
- [ ] The model lacks quantitative uncertainty — how to bridge to Subjective Logic opinions?

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — cited as [47] for foundational abstract argumentation framework; the micropublications model claims grounding in argumentation theory
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] — cited as [49] for bipolar abstract argumentation systems; the SupportGraph/ChallengeGraph structure directly maps to Cayrol's support+defeat framework
- [[Caminada_2006_IssueReinstatementArgumentation]] — cited as [63] for semi-stable semantics; referenced in context of argumentation-based evaluation
- [[Groth_2010_AnatomyNanopublication]] — cited as [24] as the competing nanopublication model that Micropublications extends beyond

### New Leads (Not Yet in Collection)
- Verheij (2005/2009) — "Evaluating Arguments Based on Toulmin's Scheme" and "The Toulmin Argument Model in Artificial Intelligence" — the Toulmin-Verheij theoretical foundation for the micropublication argument structure
- Greenberg (2009) — "How citation distortions create unfounded authority" — motivating problem for claim network tracing
- Ciccarese et al. (2012/2013) — Open Annotation ontology papers — the annotation framework underlying implementation
- de Waard (2009) — "The HypER Approach for Representing Scientific Knowledge Claims" — alternative hypothesis/evidence representation

### Cited By (in Collection)
- [[Wilkinson_2016_FAIRGuidingPrinciplesScientific]] — cites Clark 2014 in context of machine-readable scientific outputs
- [[Groth_2010_AnatomyNanopublication]] — the nanopublication model that Micropublications compares against and extends

### Conceptual Links (not citation-based)
- [[Kuhn_2014_TrustyURIs]] — trusty URIs provide the immutable content-addressed identifier layer that micropublications need for reliable cross-publication linking
- [[Kuhn_2015_DigitalArtifactsVerifiable]] — verifiable digital artifacts address the provenance and attribution requirements central to the micropublications model
- [[Juty_2020_UniquePersistentResolvableIdentifiers]] — persistent identifiers for scientific objects directly serve the micropublication attribution and reference resolution needs
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — ASPIC+ provides the formal structured argumentation framework that could formalize the micropublication SupportGraph/ChallengeGraph as proper arguments with preference orderings
- [[Pollock_1987_DefeasibleReasoning]] — Pollock's rebutting vs undercutting defeat maps to the micropublication distinction between challenge (rebutting a claim) and undermining (attacking supporting evidence)
- [Ontological Promiscuity](../Hobbs_1985_OntologicalPromiscuity/notes.md) — **Strong.** Hobbs's separation of `Exist(e)` from `p'(e, x₁,…,xₙ)` is the logical-form analog of Clark's separation of a claim's propositional content from its evidence and attribution. Both refuse to collapse reference onto commitment. The micropublication "claim present without asserted truth" shape is exactly what Hobbs's reified-condition + optional-existence apparatus licenses at the formula level. Propstore's non-commitment principle has both a logical-form precursor (Hobbs) and a scientific-discourse precursor (Clark).

## Related Work Worth Reading
- **Clark et al. 2011 [9]**: SWAN model predecessor — for understanding what Micropublications extends
- **Groth et al. 2010 [21]**: Nanopublications — the competing model
- **Greenberg 2009 [3]**: Citation distortion analysis — the motivating problem for claim networks
- **Verheij 2003 [64]**: The Toulmin Argument Model in Artificial Intelligence — theoretical foundation
- **Ciccarese et al. 2012 [71]**: Open Annotation — the annotation framework used
- **Carroll et al. 2005 [85]**: Named Graphs, Provenance and Trust — provenance framework
- **Mons et al. 2011 [87]**: FAIR data principles predecessor — related data management context
- **Rahwan & Simari 2009 [67]**: Argumentation in Artificial Intelligence — comprehensive reference
- **Caminada 2006 [63]**: Argumentation-based semantics — related to the argumentation grounding
