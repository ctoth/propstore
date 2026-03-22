---
title: "Micropublications: a Semantic Model for Claims, Evidence, Arguments and Annotations in Biomedical Communications"
authors: "Tim Clark, Paolo N Ciccarese, Carole A Goble"
year: 2014
venue: "Journal of Biomedical Semantics"
doi_url: "https://doi.org/10.1186/2041-1480-5-28"
---

# Micropublications: a Semantic Model for Claims, Evidence, Arguments and Annotations in Biomedical Communications

## One-Sentence Summary

Defines a layered semantic metadata model (micropublications) for representing scientific claims with their supporting evidence, arguments, attributions, and inter-claim relationships, formalized in OWL and designed to overlay existing publication infrastructure. *(p.1)*

## Problem Addressed

Scientific publications are documentary representations of defeasible arguments, but the linear document format (dating from 1665) cannot support machine-tractable verification of evidence, challenge/disagreement modeling, citation network analysis, or incremental annotation. *(p.1–2)* Statement-based models (nanopublications, SWAN, BEL) model only the statements themselves, with limited or no representation of the backing evidence, claim networks, or argumentation structure. *(p.2–3)* The micropublications model fills this gap by representing claims together with their complete evidentiary support graphs. *(p.1)*

## Key Contributions

- A semantic metadata model for scientific argument and evidence, grounded in Toulmin-Verheij defeasible argumentation theory *(p.5, p.9)*
- Nine use cases mapping the model to the lifecycle of biomedical communications (building citable claims, modeling evidence support, digital abstracts, claim network analysis, similarity groups, claim formalization, annotation/discussion, bipolar claim-evidence networks, contextualization via annotation ontologies) *(p.5–8)*
- A formal ontology (OWL 2) at http://purl.org/mp with class, predicate, and rule definitions *(p.9–12, p.30)*
- Design patterns for modeling claims at varying levels of complexity (minimal statement+attribution through full knowledge bases) *(p.13–26)*
- Integration with the Open Annotation Model (OAM) for contextualizing micropublications within full-text documents *(p.26)*
- Implementation in the Domeo web annotation toolkit *(p.28–29)*

## Methodology

The paper: *(p.5)*
1. Identifies nine use cases for micropublications by analyzing activities in the biomedical communications ecosystem lifecycle (authoring, reviewing, editing/publishing, DB/KB curation, searching, reading, discussion, evaluation, experiment design) *(p.5–7)*
2. Grounds the model in Toulmin's defeasible argumentation framework, extending it with both "support" and "challenge/rebuttal" relations, and with inter-argumentation relations *(p.5, p.9)*
3. Defines the model formally as a set of OWL classes and predicates *(p.9–12)*
4. Illustrates the model through a series of increasingly complex case studies drawn from Alzheimer Disease research (Spilman et al. 2010, Harrison et al. 2009, Hsia et al. 1999, Bryan et al. 2009) *(p.13–25)*
5. Shows how the model integrates with the W3C Open Annotation Model for document contextualization *(p.26)*

## Core Ontology Classes and Relations

### Class Hierarchy

*(p.10–11)*

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

2. **Activity** - a process by which an Artifact is produced, modified, consumed, or used *(p.10)*

### Key Properties

*(p.11–12)*

| Property | Domain | Range | Description | Page |
|----------|--------|-------|-------------|------|
| argues | Micropublication | Claim | The Claim the MP argues for | p.11 |
| hasAttribution | Micropublication | Attribution | Attribution of the MP | p.11 |
| supports | Representation | Representation | Transitive support relation | p.11 |
| challenges | Representation | Representation | Inferred when one Representation *directlyChallenges* another or *indirectlyChallenges* by undercutting support | p.12 |
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

### Mathematical Representation

*(p.12)*

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

*(p.12)*

### Complexity Spectrum

The model accommodates a spectrum of representations: *(p.13–26)*
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

Table 2 (p.6) maps these use cases to nine activities in the biomedical communications lifecycle.

## Key Concepts

### Claim Lineages
When support relations are resolved across micropublications (e.g., MP3 quotes C3 from Spilman, which is supported by S1 citing Harrison [109], whose Claim C1.1 is the actual backing), the graphs C1.1 -> S1 and C2.1 -> S2 are called **Claim Lineages**, by analogy with biological lineages. *(p.17–18)*

### Similarity Groups and Holotypes
Groups of *similar* statements (equivalence classes defined by "sufficient" closeness in meaning) are represented with a representative exemplar called a **Holotype**. The *similog-holotype model* is empirically based, allowing normalization of diverse statements to a common natural language representation without dropping qualifiers or hedging. Translations to formal languages or other natural languages may also be considered similogs. *(p.19–20)*

### Asserts vs. Quotes
- A Representation **assertedBy** a Micropublication is originally instantiated by that MP *(p.11)*
- A Representation **quotedBy** a Micropublication is referred to by that MP after first being instantiated elsewhere *(p.11)*
- This distinction enables proper attribution tracking when claims are imported across publication boundaries *(p.11)*

### Challenge Relations
- *directlyChallenges*: explicit opposition to a claim *(p.12, p.23)*
- *indirectlyChallenges*: undercutting a support element of a claim *(p.12, p.23)*
- Both are modeled as elements of the MP's ChallengeGraph *(p.12)*
- Challenges can originate from within a publication (Case 1) or from outside (Case 2, by a third-party curator) *(p.23–25)*

### Ontological Status of Statements
The model deliberately avoids assigning explicit ontological status to Statements — whether they are true or false, real or imaginary. In Strawson's perspective, "meaning" is expressed in the language of the statement, while "truth" is a property of its assertion in context. The model sidesteps this philosophical problem. *(p.20)*

### The "current best explanation" Problem
Scientific claims in the literature form an open, incrementally-constructed record which changes over time as claims are challenged and reassessed. The model treats the literature as a defeasible record rather than a fixed truth store. *(p.4, p.9)*

## Arguments Against Prior Work

1. **Statement-based models lack argumentation structure.** SWAN (2008), nanopublications (2010), and BEL (2011) model only the statements themselves, with limited or no representation of backing evidence, claim networks, or argumentation structure. None support claim networks or direct empirical scientific evidence (Table 1). *(p.2-3)*
2. **Nanopublications are structurally flat.** Nanopublications formalize assertions as RDF triples with provenance but provide no mechanism for representing the support graph, challenge relations, or evidential backing chains that connect claims to empirical data. *(p.2-3)*
3. **The linear document format is inadequate for machine reasoning.** The journal article format, dating from 1665 (Philosophical Transactions of the Royal Society), cannot support machine-tractable verification of evidence, challenge/disagreement modeling, citation network analysis, or incremental annotation. *(p.1-2, p.5)*
4. **Citation-level analysis reveals unfounded authority.** Greenberg's 2009 study of 242 papers on beta-amyloid and inclusion body myositis demonstrated that citation bias, amplification, and invention create unfounded authority. Foundational publications expected to contain supporting data did not; Bhardwaj and Bhargava's article had no empirical support at all for its key claim, yet was cited as authoritative. Existing models cannot detect this because they operate at the paper level, not the claim level. *(p.4, p.27)*
5. **"Current best explanation" nature of science is not captured.** Statement-based models treat assertions as static, but scientific claims form an open, incrementally-constructed record that changes over time as claims are challenged and reassessed. The literature is a defeasible record, not a fixed truth store. *(p.4, p.9)*
6. **Cherry-picking data and method failures are unaddressed.** Even with micropublications, cherry picking data and failure to properly describe methods remain problems that the model itself cannot solve, though it makes them more visible by requiring explicit evidence chains. *(p.26-27)*

## Design Rationale

1. **Grounded in Toulmin-Verheij defeasible argumentation theory.** The model adopts Toulmin's classical argumentation structure (claim, data, warrant, backing, qualifier, rebuttal) as formalized by Verheij, extending it with both "support" and "challenge/rebuttal" relations and with inter-argumentation relations. This provides a principled theoretical foundation rather than an ad hoc data model. *(p.5, p.9)*
2. **Spectrum of representational complexity.** The model deliberately accommodates a range from minimal (a single Statement with Attribution) to maximal (full cross-publication claim-evidence networks with challenge/support relations). No scenario requires deploying all concepts. This addresses the adoption barrier: users can start simple and add complexity as needed. *(p.10, p.13-26, p.29)*
3. **Backward compatibility with statement-based formalisms.** The model is designed so that nanopublications, BEL statements, and SWAN annotations can all be represented as micropublications. This ensures existing investments in these formalisms are not lost. *(p.3, p.30)*
4. **Deliberate avoidance of ontological status.** The model does not assign explicit truth values to Statements, following Strawson's distinction between "meaning" (expressed in language) and "truth" (a property of assertion in context). This sidesteps intractable philosophical debates about the ontological status of scientific claims. *(p.20)*
5. **Holotype normalization without loss of nuance.** Similarity groups use a representative exemplar (Holotype) to normalize diverse formulations of equivalent claims, but the original formulations (similogs) are preserved with their qualifiers and hedging intact. This allows normalization without the information loss that formal-language translation typically causes. *(p.19-20)*
6. **Integration with W3C Open Annotation Model.** By designing micropublications to be compatible with OAM, the model ensures that micropublications can be contextualized within full-text documents via standard Web annotation infrastructure, enabling overlay on existing publications without requiring publisher cooperation. *(p.25-26)*
7. **Mathematical formalization constrains the model.** The formal definition MP_a = (A_mpa, c, A_c, Phi, R) with R+ as a strict partial order over the support graph ensures structural invariants: exactly one principal Claim, acyclic support, and well-defined challenge relations. This makes the model amenable to computational verification. *(p.12)*
8. **Asserts vs. quotes distinction for attribution tracking.** The model distinguishes between a Representation originally instantiated by a Micropublication (assertedBy) and one referred to after first being instantiated elsewhere (quotedBy). This enables proper attribution tracking when claims cross publication boundaries and prevents misattribution. *(p.11)*

## Comparison with Statement-Based Models (Table 1, p.3)

| Feature | SWAN | Nanopublications | BEL |
|---------|------|------------------|-----|
| First specification | 2008 | 2010 | 2011 |
| Statements in | Natural language | Formal language | Formal language |
| Statement provenance | SWAN-PAV ontology | SWAN-PAV ontology | SWAN-PAV ontology |
| Backing references from literature | Yes | Yes | Yes |
| Support claim networks | No | No | No |
| Direct empirical scientific evidence | No | No | No |

Micropublications go beyond all three by supporting claim networks, direct empirical evidence, similarity groups, and challenge/disagreement modeling. *(p.3)*

## Figures of Interest

- **Fig 1 (p.4):** Nanopublication representation of statements and evidence (NP -> Assertion -> Support -> Provenance)
- **Fig 2 (p.7):** Activity lifecycle of biomedical communications, mapping 9 use cases to 9 activities in a cycle
- **Fig 3 (p.10):** Minimal form of a micropublication (Statement + Attribution)
- **Fig 4 (p.11):** Simplified model showing Claim supported by Statement, Data, Method, with References and Attribution
- **Fig 5 (p.12):** Full class diagram showing all major classes and relationships in the model
- **Fig 6 (p.13):** Concrete example - representation of Spilman et al. claim about rapamycin/mTOR
- **Fig 7 (p.15):** Example 1 - Citable claim with semantic qualifiers
- **Fig 8 (p.16):** Example 2 - Scientific evidence (Data + Methods) supporting a claim
- **Fig 9 (p.17):** Example 3 - Full digital abstract micropublication
- **Fig 10 (p.18):** Example 4 - Transition from document-level to claim-level backing references
- **Fig 11 (p.18):** Example 4 - Connected support relations across three publications (claim network)
- **Fig 12 (p.20):** Example 5 - Similarity Group with Holotype claim
- **Fig 13 (p.21):** Example 5 - Homology group as a micropublication
- **Fig 14 (p.22):** Example 6 - BEL representation at document level
- **Fig 15 (p.22):** Example 6 - BEL representation with claim-level resolution
- **Fig 16 (p.23):** Example 7 - Annotation using micropublication relations
- **Fig 17 (p.25):** Example 8 - Challenge relation (Claim C11 challenges Statement S3)
- **Fig 18 (p.25):** Example 8 - Annotation of inconsistency between two publications as independent MP
- **Fig 19 (p.26):** Example 9 - Contextualizing a claim within full-text using Open Annotation
- **Fig 20 (p.27):** Citation distortion - claim network from Greenberg 2009 showing unfounded authority
- **Fig 21 (p.29):** Domeo version 2 software implementation for creating micropublications

## Implementation Details

### Domeo Web Annotation Toolkit
*(p.28–29)*
- Open source, licensed under Apache 2.0 *(p.29)*
- Plug-in based architecture with browser-based interface *(p.28)*
- Knowledgebase, parsers, web services, proxy server *(p.28)*
- Supports profile-based selection of user interfaces *(p.28)*
- Peer-to-peer knowledge base communication *(p.28)*
- Private, group-specific, or public annotations *(p.28)*
- Version 1: SWAN ontology annotations *(p.28)*
- Version 2: Micropublications-based annotation functionality *(p.28–29)*
- Active use in Neuroscience Information Framework, drug-hunting teams, pharmaceutical companies *(p.29)*

### OWL Vocabulary
*(p.9, p.30)*
- Available at http://purl.org/mp *(p.30)*
- W3C Web Ontology Language (OWL 2) *(p.9)*
- RDF examples provided in Additional file 1 *(p.30)*
- Class, Predicate, and DL-safe Rule definitions in Additional file 2 *(p.30)*
- Comparison to SWAN model in Additional file 3 *(p.30)*

### Integration with Open Annotation Model (OAM)
*(p.25–26)*
- W3C Open Annotation Community Group standard *(p.26)*
- Annotation created on HTML targets exported as RDF *(p.26)*
- Referenced independently by PDF viewer (Utopia) *(p.26)*
- Contextualization via oa:Annotation, oa:hasBody, oa:hasTarget, oa:SpecificResource, oa:hasSelector *(p.26)*

## Discussion: Citation Distortions
*(p.27)*
The paper discusses Greenberg's 2009 study showing how citation bias, amplification, and invention create unfounded authority in biomedical literature. A claim network of 242 papers on beta-amyloid and inclusion body myositis (IBM) revealed that foundational publications which would be expected to contain supporting data did not; Bhardwaj and Bhargava's article had no empirical support at all for Claim C15, yet was cited as authoritative. The micropublication model addresses this by requiring that the ultimate evidence supporting a claim — the *support for belief* — be made explicit, in addition to any empirical supporting statement. *(p.27)*

## Results Summary

The micropublications model successfully represents scientific arguments at varying levels of complexity, from simple attributed statements to complex cross-publication claim-evidence networks with challenge/support relations. *(p.13–26)* Nine use cases demonstrate applicability across the entire biomedical communications lifecycle. *(p.5–8)* The model is backward-compatible with statement-based formalisms (nanopublications, BEL) while providing richer argumentation structure. *(p.3, p.30)* Implementation in Domeo version 2 demonstrates practical feasibility. *(p.28–29)*

## Limitations

- The model is complex; full deployment of all concepts is not required for any particular scenario but may be overwhelming *(p.29)*
- Adoption depends on creation of useful software tools *(p.29)*
- Similarity/holotype determination is subjective ("sufficient" closeness is application-dependent) *(p.20)*
- The model does not assign explicit ontological status to Statements (avoids the philosophical problem but leaves it unresolved) *(p.20)*
- Citation-level claim resolution requires significant human effort (reading cited works, identifying backing claims) *(p.27)*
- Reagent-level citation tracking requires publisher/author action beyond the model itself *(p.27)*
- The model does not itself solve the problem of verifying whether cited evidence actually exists or is fabricated *(p.27)*
- Cherry picking data and failure to properly describe methods remain unaddressed *(p.26)*

## Testable Properties

- A Micropublication must have exactly one Claim (the principal Statement) *(p.9, p.12)*
- A Micropublication must have exactly one Attribution (hasAttribution) *(p.11–12)*
- The supports relation must form a DAG (directed acyclic graph) rooted at the Claim *(p.12)*
- Every element of a SupportGraph must be an elementOf the Micropublication *(p.11)*
- The challenges relation is inferred: directlyChallenges OR indirectlyChallenges (which undercuts a support element) *(p.12)*
- A Representation can only be assertedBy one Micropublication (original instantiation) *(p.11)*
- A Representation may be quotedBy multiple Micropublications *(p.11)*
- Similarity groups form equivalence classes; each group has exactly one Holotype *(p.19–20)*
- The minimal valid Micropublication consists of: Claim + Attribution *(p.10)*
- R+ (support relations) must be a strict partial order over the support graph elements *(p.12)*

## Relevance to Project

This paper is directly foundational for the propstore's claim representation architecture. The micropublications model provides the theoretical framework for:
1. **Claim structure**: The Claim/Statement/Data/Method hierarchy maps directly to the propstore's claim types (parameter, equation, observation, model, measurement) *(p.10–11)*
2. **Provenance tracking**: The Attribution and Reference model informs provenance.paper, provenance.page, provenance.quote_fragment *(p.11)*
3. **Cross-paper relationships**: The supports/challenges relations and claim lineages map to the propstore's stances (supported_by, contradicted_by, superseded_by, mechanism_for) *(p.12, p.17–18)*
4. **Similarity groups and holotypes**: The similog-holotype model provides theoretical grounding for the propstore's concept of reconciling equivalent claims across papers *(p.19–20)*
5. **Evidence grounding**: The requirement that claims be backed by empirical evidence (Data + Methods), not just statements, aligns with the propstore's emphasis on grounding claims in verifiable data *(p.15–16)*

## Open Questions

- [ ] How does the propstore's claim schema map specifically to the micropublication ontology classes?
- [ ] Could the propstore adopt the asserts/quotes distinction for tracking claim provenance across papers?
- [ ] Is the holotype/similog model useful for the propstore's claim reconciliation workflow?
- [ ] How should the challenge/support distinction map to the propstore's stance types?

## Related Work Worth Reading

- Toulmin S: The Uses of Argument (1958/2003) - foundational argumentation model *(cited p.5, p.9)*
- Groth P, Gibson A, Velterop J: The anatomy of a nanopublication (2010) - statement-based model comparison → NOW IN COLLECTION: [[Groth_2010_AnatomyNanopublication]] *(cited p.2–3)*
- Greenberg SA: How citation distortions create unfounded authority (2009) - motivation for claim networks → NOW IN COLLECTION: [[Greenberg_2009_CitationDistortions]] *(cited p.4, p.27)*
- Verheij B: Artificial argument assistants (2003/2005) - bipolar argumentation frameworks *(cited p.9)*
- Carroll JJ et al: Named graphs, provenance and trust (2005) - RDF named graph foundations *(cited p.2)*
- Ciccarese P et al: The SWAN biomedical discourse ontology (2008) - predecessor model *(cited p.2)*

## Collection Cross-References

### Already in Collection
- (none directly cited)

### Now in Collection (previously listed as leads)
- [[Groth_2010_AnatomyNanopublication]] — Defines nanopublication model (concept→triple→statement→annotation→nanopublication) with RDF Named Graph serialization. Structurally analogous to the micropublication model but focused on Semantic Web interoperability rather than argumentation structure. Clark's model adds supports/challenges argumentation; Groth provides concrete RDF serialization.
- [[Greenberg_2009_CitationDistortions]] — Empirically demonstrates how citation bias, amplification, and invention create unfounded authority in a claim-specific citation network (242 papers on β-amyloid/IBM). Provides the motivating case study for why claim-level tracking (micropublications) is needed: paper-level citation fails to distinguish data-supported from citation-amplified claims.

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)
- [[Groth_2010_AnatomyNanopublication]] — **Strong.** Both define atomic scientific assertion models with layered provenance. Complementary formalizations: Clark adds argumentation structure, Groth adds Semantic Web serialization.
- [[Greenberg_2009_CitationDistortions]] — **Strong.** Greenberg's citation distortion taxonomy (bias, amplification, invention) is the empirical motivation for Clark's micropublication model. Clark's supports/challenges stances directly address Greenberg's citation bias problem by making claim-level evidence explicit.
- [[Dung_1995_AcceptabilityArguments]] — **Strong.** Clark's micropublication model is grounded in Toulmin-Verheij defeasible argumentation theory with explicit support and challenge relations. Dung's abstract argumentation frameworks provide the formal semantics for these challenge/attack relations. Clark's bipolar claim-evidence networks (Use Case 8) are instances of argumentation frameworks where claims form arguments and challenge relations form attacks. Dung's multiple semantics (preferred, stable, grounded) offer formal strategies for resolving the competing claims Clark models.
- [[Pollock_1987_DefeasibleReasoning]] — **Moderate.** Clark grounds the micropublication model in Toulmin-Verheij defeasible argumentation theory. Pollock provides the formal epistemological theory of defeasible reasoning (prima facie reasons, rebutting/undercutting defeaters) that underpins the kind of argumentation Clark models. Clark's directlyChallenges maps to rebutting defeat; Clark's indirectlyChallenges (undercutting support) maps to undercutting defeat.
- [[Mayer_2020_Transformer-BasedArgumentMiningHealthcare]] — **Strong.** Clark's micropublications model defines the semantic representation for claims, evidence, and their support/challenge relations; Mayer provides a computational pipeline for automatically extracting these structures from biomedical text (RCT abstracts). Clark's model could serve as the target ontology for structuring the output of Mayer's mining pipeline, with Mayer's evidence/claim component types mapping to Clark's Data/Claim types and the support/attack relations mapping to Clark's supports/challenges stances.
