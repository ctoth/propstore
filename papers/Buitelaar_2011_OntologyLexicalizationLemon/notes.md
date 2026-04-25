---
title: "Ontology Lexicalization: The lemon Perspective"
authors: "Paul Buitelaar, Philipp Cimiano, John McCrae, Elena Montiel-Posada, Thierry Declerck"
year: 2011
venue: "9th International Conference on Terminology and Artificial Intelligence (TIA 2011), Workshop Extended Abstracts"
produced_by:
  agent: "claude-opus-4-6[1m]"
  skill: "paper-reader"
  timestamp: "2026-04-03T08:05:28Z"
---
# Ontology Lexicalization: The lemon Perspective

## One-Sentence Summary
This paper presents the lemon (Lexicon Model for Ontologies) model for representing ontology lexicalizations as RDF, providing a modular core vocabulary for linking lexical entries to ontology entities with support for morphology, syntax-semantics mapping, and multilingual lexica.

## Problem Addressed
Ontologies (Guarino 1998) capture knowledge but fail to capture the structure and use of terms in expressing and referring to that knowledge in natural language. The structure and use of terms (terminology) is a concern as relevant as knowledge representation itself. Prior approaches to linking lexical knowledge and ontology knowledge lacked a shared, modular, language-independent model that could serve as an interchange format. *(p.1)*

## Key Contributions
- Introduces the lemon model: a concise, modular RDF model for ontology lexicalization *(p.2)*
- Defines a core model with supplementary modules for morphology, phrase structure, syntax-semantics mapping, and variation *(p.2-3)*
- Separates linguistic knowledge from ontological knowledge, maintaining ontology as the "semantic backbone" *(p.2)*
- Provides a language-independent representation so that lexicalizations can be multilingual by design *(p.1)*
- Demonstrates extraction of ontology lexicalizations from text via NLP and multilingual querying *(p.1)*

## Methodology
The authors motivate ontology lexicalization through use cases in ontology-based information extraction (mapping text to ontology facts) and terminology management (linking domain terms across languages via ontology anchors). They then derive requirements for a lexicon model and present the lemon core plus modular extensions. *(p.1-2)*

## Use Cases of Ontology Lexicalization

### 1. Knowledge Acquisition from Text
Using ontology lexicalizations from text to identify relevant text segments and align them with formally defined knowledge structures such as facts and actions. The focus is on ontology-based information extraction: extraction of facts from text relative to a given ontology. *(p.1)*

Example: The ontology defines concepts of relevance to tourism with ontology labels (terms) in Spanish. The Spanish terms (rendered by use of the `rdfs:label` property) link to "edificio historico" (historical building). Knowing this enables extraction of facts about historical buildings from text. *(p.1)*

### 2. Multilingual Knowledge Access
Ontology lexicalization can be extended to multiple languages, enabling applications such as multilingual ontology-based question answering. *(p.1)*

Key observation: the match between ontology label and text is straightforward only when the text and the ontology label match exactly. In practice, ambiguity is widespread in natural language: words have multiple meanings, and grammar can be ambiguous in structure and interpretation. Ontology labels alone provide little help here; however, a richer lexicon model with grammatical information resolves these ambiguities. *(p.1)*

### Distinction: Ontology Labels vs. Lexical Information
- Ontology labels (e.g., `rdfs:label`) identify entities but are not disambiguated *(p.1)*
- A lexicon entry is language-independent at its core: the relationship between label and ontology entity is language-independent; only surface forms are language-specific *(p.1)*
- SPARQL queries can be transformed into a language-independent representation and then matched *(p.1)*

## The lemon Core Model

### Requirements
The model must *(p.2)*:
1. **Represent linguistic information** relative to the semantics given by the ontology, thereby avoiding the representation of unnecessary lexical features that may lead to over-generation of term variants
2. **Allow strict separation** of "world knowledge" (describing domain objects referenced by ontology entities) from "word knowledge" (describing lexical objects)
3. **Enable easy update** of the model by providing a simple core model, supplemented with a set of modules that can be used, extended, or ignored per need

### Core Components *(p.2)*

| Component | Description | Role |
|-----------|-------------|------|
| **Ontology Entity** | URI of an ontology element to which a Lexical Sense points | Provides possible linguistic realizations for the Ontology Entity |
| **Lexical Entry** | Functional object that links a Lexical Form to an Ontology Entity | Produces a sense-disambiguated interpretation of the Lexical Entity |
| **Lexical Form** | Morphosyntactic representation of a Lexical Entry | Surface realization |
| **Lexical Sense** | Links Lexical Entry to Ontology Entity | Provides sense-disambiguated interpretation |

### Architecture Diagram (described)
The lemon core is described in the "lemon cook-book" (McCrae et al. 2010). It is organized around a core plus 6 supplementary modules. *(p.2)*

### lemon Modules *(p.2-3)*

1. **Lexical Entry module**: morphosyntactic representation of one or more Lexical Forms *(p.2)*

2. **Lexical Entry: morphosyntactic variation**: the representation of a Lexical Entry as the set of data categories such as `EuroWordNet` category set; specific data categories can be used in particular instances of the lemon model *(p.2)*

3. **Morphology module**: concerned with the analysis or representation of inflected and agglutinative morphology. Allows specification of regular inflections by use of Perl-like regular expressions *(p.2)*

4. **Phrase structure module**: concerned with the modeling of lexical entries that are syntactically complex, such as phrases and clauses, to enable representation of the syntactic structure of such lexical entries *(p.3)*

5. **Syntax and mapping module**: concerned with a description of a lexical entity's subcategorization frames with syntactic arguments and semantic predicates (operators with subjectposition on the ontology side and the mapping between them) *(p.3)*

6. **Variation module**: concerned with a description of the relationship between elements of a lemon lexicon; sense relations (e.g., translations) require a semantic context; lexical variations (e.g., plural) require a morphosyntactic context; form variations (e.g., homographs) include all other variations *(p.3)*

## Key Properties of lemon

- **Ontology as "hub"**: In lemon, ontology is used as the "semantic layer" and the lexicon adds linguistic knowledge on top *(p.2)*
- **RDF native**: Designed as an RDF vocabulary, making it interoperable with Semantic Web standards *(p.2)*
- **Modular**: Core is minimal; modules are opt-in *(p.2)*
- **Language-independent core**: The relationship between a lexical entry and an ontology entity is language-independent; multilingual support is achieved by having separate lexical entries per language all pointing to the same ontology entities *(p.1)*
- **Separation of concerns**: "world knowledge" (domain/ontology) vs. "word knowledge" (linguistic/lexical) are kept strictly separate *(p.2)*

## lemon in Action: Examples

### Spanish Historical Buildings
The ontology defines `edificio historico` (historical building). A text segment specifies a set of facts concerning a historical building (University building at Elia Rogers), its architect, and building period (1863-1882). The lemon lexicalization enables extraction of these facts. *(p.1)*

### SPARQL-based Multilingual QA
Questions in different languages (e.g., "Who painted the Mona Lisa?" in German, Spanish) can be transformed into language-independent SPARQL queries using lemon lexicalizations. The queries are structurally identical regardless of source language. *(p.1)*

Example queries shown *(p.1)*:
- `"Wer malte die Mona Lisa?"` (German)
- `"Quien pinto la Mona Lisa?"` (Spanish)

Both resolve to the same SPARQL query pattern:
```
PREFIX rdf: <...> SELECT ?x ...
SELECT ?x WHERE { ?x rdf:type ... }
```

### Multilingual Labels
Dutch: "malen" (German: "pinta" / Spanish: "paint") all refer to the same ontology property. *(p.2)*

## Figures of Interest
- **Fig (p.2):** lemon core model diagram showing Ontology Entity, Lexical Entry, Lexical Form, Lexical Sense and their relationships (described textually, not a numbered figure)

## Results Summary
The paper presents lemon as a model that fulfills the requirements for an ontology lexicalization model: it separates linguistic from ontological knowledge, provides a modular architecture, and has been developed based on use cases in knowledge acquisition from text and multilingual knowledge access. The model is already in use in several projects including the Semantic Web conference context and the CTTCE excellence initiative. *(p.3)*

## Limitations
- This is a 4-page workshop extended abstract, not a full paper with evaluation *(throughout)*
- No formal evaluation or comparison with alternative models is presented *(throughout)*
- The paper focuses on motivation and architecture rather than implementation details or performance metrics *(throughout)*
- Does not address scalability or computational complexity of using lemon lexicalizations in practice *(throughout)*

## Arguments Against Prior Work
- Ontology labels (`rdfs:label`) are insufficient for NLP tasks because they lack disambiguation and grammatical information *(p.1)*
- Prior ontology labeling approaches (e.g., SKOS) provide little help with ambiguity in text *(p.1)*
- Knowledge representation approaches (like SKOS) that ignore terminology create barriers to practical use in NLP pipelines *(p.1)*

## Design Rationale
- **Ontology as hub rather than lexicon as hub**: The ontology is the authoritative semantic layer; the lexicon enriches it with linguistic knowledge rather than replacing or duplicating semantic information *(p.2)*
- **Modularity over monolithic design**: Core is kept minimal so that users need not adopt the full model; they can opt in to specific modules *(p.2)*
- **Language-independence at the structural level**: Lexical entries are language-specific but their relationship to ontology entities is language-independent, enabling true multilingual support *(p.1)*
- **RDF as representation**: Ensures interoperability with existing Semantic Web infrastructure *(p.2)*

## Testable Properties
- A lemon lexicalization must separate "world knowledge" from "word knowledge" — no lexical entry should contain domain facts, and no ontology entity should contain linguistic structure *(p.2)*
- Multilingual queries over the same ontology using different lemon lexicons must produce identical SPARQL query structures *(p.1)*
- The core model alone (without modules) must be sufficient to link a lexical entry to an ontology entity with at least one form and one sense *(p.2)*
- Morphological variations expressible via Perl-like regular expressions must be generable from the morphology module *(p.2)*

## Relevance to Project
**Rating: High** — This paper provides the missing formalism underneath propstore's concept registry and vocabulary reconciliation layer.

Propstore's concept registry (`knowledge/concepts/*.yaml`) links canonical concept names to formal definitions, domains, and forms. The vocabulary reconciliation workflow resolves variant surface terms to canonical concepts. Lemon's architecture is exactly this pattern, formalized: Lexical Entries (surface terms from claims) link via Lexical Senses to Ontology Entities (registered concepts), with Lexical Forms capturing morphological/syntactic variants. The strict separation of "word knowledge" from "world knowledge" (p.2) is propstore's own separation between claims (linguistic/propositional content) and concepts (formal semantic entities in the registry).

Specific points of contact:
1. **Concept registration as ontology lexicalization**: When propstore registers a concept with a `canonical_name` and `definition`, it is creating the ontology entity side. When claims reference that concept via varying surface terms, those are lexical entries. Lemon formalizes this relationship with Lexical Sense as the disambiguating link — something propstore currently handles ad hoc in vocabulary reconciliation.
2. **Multilingual/variant term resolution**: Lemon's language-independent core (the concept-to-sense link is language-independent; only forms are language-specific) provides a principled model for how propstore should handle terminology variants that all refer to the same concept.
3. **Modular enrichment**: Lemon's opt-in modules (morphology, phrase structure, syntax-semantics mapping) provide a template for how propstore could enrich its concept registry with structured linguistic metadata without bloating the core.
4. **Form-concept linking**: The lemon model's separation of syntactic form from semantic reference parallels propstore's `form` field on concepts (`structural`, `scalar`, etc.) — different ways of measuring or describing the same underlying entity.

## Open Questions
- [ ] How does lemon compare to more recent ontology lexicalization standards (e.g., OntoLex-lemon W3C community group)?
- [ ] Could lemon-style lexicalizations improve propstore's concept registration and vocabulary reconciliation?
- [ ] What is the relationship between lemon senses and propstore stances?

## Collection Cross-References

### Already in Collection
- (none found)

### New Leads (Not Yet in Collection)
- Guarino (1998) — "Formal Ontology in Information Systems" — foundational ontology theory, defines formal ontology framework
- McCrae, Spohr, Cimiano (2011) — "Linking Lexical Resources and Ontologies on the Semantic Web with Lemon" — full conference paper for lemon model
- McCrae et al. (forthcoming) — "Interchanging lexical resources on the Semantic Web" — comprehensive lemon interchange treatment

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)
- [[Fillmore_1982_FrameSemantics]] — Lemon's Ontology Entity corresponds to a Fillmorean frame; lemon formalizes the link between linguistic surface forms and the frame-structured concepts they reference
- [[Baker_1998_BerkeleyFrameNet]] — FrameNet's Lexical Units (word senses tied to frames) are the empirical counterpart to lemon's Lexical Entries tied to Ontology Entities
- [[Clark_2014_Micropublications]] — Clark's Similarity Groups / Holotypes address the same vocabulary normalization problem that lemon's sense-disambiguated lexicalization solves structurally
- [A Component-Based Framework For Ontology Evolution](../Klein_2003_ComponentBasedFrameworkOntologyEvolution/notes.md) — Klein and Noy define a typed change-operation framework parametrized over Frames-style ontology components (class / slot / facet / instance). For propstore the lemon decomposition (OntologyReference / LexicalEntry / LexicalForm / LexicalSense) is the propstore-era equivalent of those components; a Klein/Noy-style change ontology *for propstore* would be parametrized over lemon components rather than Frames components. Lemon supplies the substrate, Klein/Noy supplies the migration discipline.

## Related Work Worth Reading
- Guarino N. (1998) — Formal Ontology in Information Systems (foundational ontology reference)
- Buitelaar P. (2010) — Ontology-based Semantic Lexicon: Mapping between Terms and Object Descriptions (extends this work)
- McCrae J., Spohr D., Cimiano P. (2011) — Linking Lexical Resources and Ontologies on the Semantic Web with Lemon (full conference paper)
- McCrae J. et al. (forthcoming at time of publication) — Interchanging lexical resources on the Semantic Web (Language Resources and Evaluation)
- Reymonet A., Thomas J., Aussenac-Gilles N. (2007) — Modelling ontological and terminological resources in OWL-DL
- Saiz O., D. Teresas Langergen (2010) — "The Onto/WordNet project: extension and automation of concept-based relations in WordNet" (GSMAKE Symposium)
