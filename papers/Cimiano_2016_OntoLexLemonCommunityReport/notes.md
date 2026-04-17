---
title: "Lexicon Model for Ontologies: Community Report"
authors: "John P. McCrae, Julia Bosque-Gil, Jorge Gracia, Paul Buitelaar, Philipp Cimiano (editors: Cimiano, McCrae, Buitelaar)"
year: 2016
venue: "W3C Ontology-Lexica Community Group — Final Community Group Report"
doi_url: "https://www.w3.org/2016/05/ontolex/"
pages: 85
note: "Final Community Report, 10 May 2016. OntoLex-Lemon. No DOI; W3C Community Final Specification Agreement. Retrieved via headless Chrome print-to-pdf."
---

# Lexicon Model for Ontologies: Community Report

## One-Sentence Summary
OntoLex-Lemon is a W3C Community Group RDF/OWL vocabulary for attaching rich linguistic grounding (morphology, syntax, senses, concepts, translations, metadata) to ontologies, organized into five modules (ontolex, synsem, decomp, vartrans, lime) plus non-formal guidance sections on linguistic description and lexical nets. *(p.1-2)*

## Problem Addressed
OWL / RDF(S) only support a single `rdfs:label` per vocabulary element, which is insufficient for NLP applications: inflected forms, genders, multiple senses, usage notes, syntactic frames, morphological decomposition, cross-lingual equivalence, and full wordnet-style lexical resources cannot be captured. The model closes this gap by providing a linguistic-grounding vocabulary that follows the principle of *semantics by reference* (Buitelaar 2011 lemon): meaning of a lexical entry is expressed by pointing to an ontology entity. *(p.3)*

## Key Contributions
- Five-module architecture with explicit namespaces and an `all` import URL. *(p.2, p.4)*
- Core class hierarchy: `LexicalEntry` specialized into `Word`, `MultiwordExpression`, `Affix`; `Form` with `writtenRep`/`phoneticRep`; `LexicalSense` reifying the entry-ontology link; `LexicalConcept` as a SKOS-subclass reification of mental concepts evoked by entries; `ConceptSet`. *(p.5-6, p.17, p.20, p.23-24)*
- `synsem` module for syntactic frames, argument structure, ontology mapping, sub-mappings for complex predicates, and conditions (propertyDomain/propertyRange). *(p.25-38)*
- `decomp` module for subterm relations, components, phrase structure with OLiA tags. *(p.39-44)*
- `vartrans` module for lexico-semantic relations, translation (shared reference, sense-relation reification, translatableAs, TranslationSet). *(p.45-57)*
- `lime` module for metadata: Lexicon, LexicalizationSet, ConceptualizationSet, LexicalLinkset, partitions, statistics (references, lexicalizations, avgAmbiguity, avgSynonymy, percentage). *(p.58-72)*
- Four canonical publication scenarios and integration patterns with SKOS(-XL), LMF, and Open Annotation. *(p.72-73, p.82-85)*

## Study Design (empirical papers)
*Not applicable — normative specification, not empirical.*

## Methodology
Informal-formal mix. Each class/property box gives: URI, natural-language definition, Domain, Range, Characteristics (Functional / InverseFunctional / Symmetric), SubClassOf / SubPropertyOf, InverseOf, PropertyChain. Diagrams use UML-like boxes (classes) with property-labeled arrows; `X/Y` labels denote property/inverse pairs (e.g. `sense/isSenseOf`). All Turtle examples use the `iso639` language-tag convention and LexInfo for POS/grammatical features (not required, but illustrative). *(p.4-5)*

## Key Equations / Statistical Models

Average number of lexicalizations per ontology element:

$$
\text{avgNumOfLexicalizations} = \frac{|\text{LexicalizationSet}|}{|\text{Ontology}|}
$$

Where `|LexicalizationSet|` is the count of (entry, reference) pairs and `|Ontology|` is the element count (typically `void:entities`). *(p.65, Fig 6)*

Percentage of ontology entities lexicalized at least once:

$$
\text{percentage} = \frac{|\{o \in \text{Ontology} \;\mid\; \exists \ell : \text{LexicalEntry}. (o, \ell) \in \text{LexicalizationSet}\}|}{|\text{Ontology}|}
$$
*(p.66, Fig 7)*

Formal property schema for the three relations in lime (p.71-72):
- $R_{lex} \subseteq O \times L$ — lexicalizations (object, entry).
- $R_{con} \subseteq L \times C$ — conceptualizations (entry, concept).
- $R_{links} \subseteq O \times C$ — lexical links (object, concept).

For each $R_i \subseteq A \times B$ the spec defines:
- $\text{cardinality}(R_i) = |R_i|$
- $\text{count}(\pi_A(R_i)) = |\{a \in A \mid \exists b \in B . (a,b) \in R_i\}|$
- $\text{coverage}_A(R_i) = \text{count}(\pi_A(R_i)) / |A|$
- $\text{average}_A(R_i) = |R_i| / |A|$
*(p.71)*

LexInfo axiomatization of TransitiveFrame (p.77):

$$
\text{TransitiveFrame} \equiv \text{VerbFrame} \sqcap (=1\ \text{subject}) \sqcap (=1\ \text{directObject})
$$

Anonymous-class pattern for adjective membership (p.16-17):

$$
\text{female} : \exists\, \text{gender}.\{\text{Female}\}
$$

encoded as an `owl:Restriction` with `owl:onProperty dbo:gender; owl:hasValue dbr:Female`.

## Parameters

### Core module (ontolex) — Classes and typical cardinality

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| LexicalEntry | — | — | — | has ≥1 Form, ≤1 canonicalForm | 5-6 | SubClassOf semiotics:Expression |
| Word | — | — | — | single-token LexicalEntry | 6 | |
| MultiwordExpression | — | — | — | ≥2-word LexicalEntry | 6 | |
| Affix | — | — | — | prefix/suffix/infix/circumfix | 6 | |
| Form | — | — | — | writtenRep min 1 rdf:langString | 7 | |
| LexicalSense | — | — | — | reference exactly 1 rdfs:Resource; isSenseOf exactly 1 LexicalEntry | 17-18 | SubClassOf semiotics:Meaning |
| LexicalConcept | — | — | — | SubClassOf skos:Concept | 20 | |
| ConceptSet | — | — | — | SubClassOf skos:ConceptScheme, void:Dataset; EquivalentClass skos:inScheme min 1 LexicalConcept | 24 | |

### Core module — Properties

| Name | Symbol | Domain | Range | Characteristics | Page |
|------|--------|--------|-------|------|------|
| lexicalForm | — | LexicalEntry | Form | — | 7 |
| canonicalForm | — | LexicalEntry | Form | Functional; SubPropertyOf lexicalForm | 9 |
| otherForm | — | LexicalEntry | Form | SubPropertyOf lexicalForm | 12 |
| writtenRep | — | Form | rdf:langString | SubPropertyOf representation | 7 |
| phoneticRep | — | Form | rdf:langString | SubPropertyOf representation | 9 |
| representation | — | Form | rdf:langString | — | 9 |
| morphologicalPattern | — | LexicalEntry | — | — | 13 |
| denotes | — | LexicalEntry | rdfs:Resource | InverseOf isDenotedBy; SubPropertyOf semiotics:denotes; PropertyChain = sense ∘ reference | 13-14 |
| sense | — | LexicalEntry | LexicalSense | Inverse Functional; InverseOf isSenseOf | 19 |
| reference | — | LexicalSense or synsem:OntoMap | rdfs:Resource | Functional; InverseOf isReferenceOf | 19 |
| usage | — | LexicalSense | rdfs:Resource | — | 20 |
| evokes | — | LexicalEntry | LexicalConcept | InverseOf isEvokedBy; PropertyChain = sense ∘ isLexicalizedSenseOf | 21 |
| lexicalizedSense | — | LexicalConcept | LexicalSense | InverseOf isLexicalizedSenseOf | 22 |
| concept | — | owl:Thing | LexicalConcept | InverseOf isConceptOf | 23 |

### synsem module

| Name | Domain | Range | Characteristics | Page |
|------|--------|-------|------|------|
| SyntacticFrame | — | — | — | 25 |
| SyntacticArgument | — | — | marker, optional | 25 |
| OntoMap | — | — | — | 28 |
| synBehavior | ontolex:LexicalEntry | SyntacticFrame | InverseFunctional | 26 |
| synArg | SyntacticFrame | SyntacticArgument | — | 27 |
| ontoMapping | OntoMap | LexicalSense | Functional, InverseFunctional | 28 |
| ontoCorrespondence | OntoMap or LexicalSense | SyntacticArgument | — | 28 |
| isA | — | — | SubPropertyOf ontoCorrespondence (unary pred arg) | 29 |
| subjOfProp | — | — | SubPropertyOf ontoCorrespondence (1st arg of binary) | 29 |
| objOfProp | — | — | SubPropertyOf ontoCorrespondence (2nd arg of binary) | 29 |
| marker | SyntacticArgument | rdfs:Resource | — | 31 |
| submap | OntoMap | OntoMap | — | 33 |
| optional | SyntacticArgument | xsd:boolean | — | 34 |
| condition | LexicalSense | rdfs:Resource | SubPropertyOf usage | 37 |
| propertyDomain | LexicalSense | rdfs:Resource | — | 38 |
| propertyRange | LexicalSense | rdfs:Resource | — | 38 |

### decomp module

| Name | Domain | Range | Notes | Page |
|------|--------|-------|------|------|
| subterm | LexicalEntry | LexicalEntry | compound part | 39 |
| Component | — | — | class for ordered/tagged component | 40 |
| constituent | LexicalEntry or Component | Component | — | 41 |
| correspondsTo | Component | LexicalEntry or SyntacticArgument | — | 41 |

Ordering of components uses `rdf:_1`, `rdf:_2`, ... *(p.42)*. Penn-TreeBank tags via `olia:hasTag penn:NP|JJ|NN|VP|S|V` *(p.43-44)*.

### vartrans module

| Name | Domain | Range | Notes | Page |
|------|--------|-------|------|------|
| LexicoSemanticRelation | — | — | `relates exactly 2` of LexicalEntry/LexicalSense/LexicalConcept | 47 |
| relates | LexicoSemanticRelation | Entry∪Sense∪Concept | — | 47 |
| source | — | — | SubPropertyOf relates | 47 |
| target | — | — | SubPropertyOf relates | 47 |
| lexicalRel | LexicalEntry | LexicalEntry | — | 46 |
| senseRel | LexicalSense | LexicalSense | — | 46 |
| conceptRel | LexicalConcept | LexicalConcept | — | 51 |
| category | LexicoSemanticRelation | — | Functional | 48 |
| LexicalRelation | — | — | `relates exactly 2 ontolex:LexicalEntry` | 48 |
| SenseRelation | — | — | `relates exactly 2 ontolex:LexicalSense` | 49 |
| TerminologicalRelation | — | — | SubClassOf SenseRelation (diatopic/diaphasic/diachronic/diastratic/dimensional) | 50 |
| ConceptualRelation | — | — | `relates exactly 2 ontolex:LexicalConcept` | 52 |
| Translation | — | — | SubClassOf SenseRelation | 53 |
| translation | LexicalSense | LexicalSense | SubPropertyOf senseRel | 54 |
| translatableAs | LexicalEntry | LexicalEntry | Symmetric; SubPropertyOf `isSenseOf ∘ translation ∘ sense` | 55 |
| TranslationSet | — | — | set of Translations | 56 |
| trans | TranslationSet | Translation | — | 57 |

Translation category uses `<http://purl.org/net/translation-categories>`. *(p.54)*

### lime module

| Name | Domain | Range | Notes | Page |
|------|--------|-------|------|------|
| Lexicon | — | — | SubClassOf: entry min 1 LexicalEntry, language exactly 1 rdfs:Literal, void:Dataset | 59 |
| LexicalizationSet | — | — | SubClassOf: void:Dataset; lexiconDataset max 1 Lexicon; referenceDataset exactly 1 void:Dataset; partition only LexicalizationSet; lexicalizationModel exactly 1 | 62 |
| LexicalLinkset | — | — | SubClassOf: void:Linkset; conceptualDataset exactly 1 ConceptSet; referenceDataset exactly 1 void:Dataset; partition only LexicalLinkset | 68 |
| ConceptualizationSet | — | — | SubClassOf: void:Dataset; lexiconDataset exactly 1 Lexicon; conceptualDataset exactly 1 ontolex:ConceptSet | 70 |
| entry | Lexicon | LexicalEntry | — | 60 |
| language | Lexicon / LexicalEntry / ConceptSet / LexicalizationSet | xsd:language | — | 60 |
| linguisticCatalog | Lexicon | — | SubPropertyOf voaf:Vocabulary | 61 |
| referenceDataset | LexicalizationSet or LexicalLinkset | void:Dataset | — | 62 |
| lexiconDataset | LexicalizationSet or ConceptualizationSet | Lexicon | — | 62-63 |
| lexicalizationModel | LexicalizationSet | rdfs:Resource | SubPropertyOf void:vocabulary | 63 |
| references | LexicalizationSet or LexicalLinkset | xsd:integer | — | 63 |
| lexicalEntries | Lexicon / LexicalizationSet / ConceptualizationSet | xsd:integer | — | 60 |
| lexicalizations | LexicalizationSet | xsd:integer | — | 65 |
| avgNumOfLexicalizations | LexicalizationSet | xsd:decimal | — | 65 |
| percentage | LexicalizationSet or LexicalLinkset | xsd:decimal | — | 66 |
| partition | LexicalizationSet or LexicalLinkset | LexicalizationSet or LexicalLinkset | SubPropertyOf void:subset | 67 |
| resourceType | LexicalizationSet or LexicalLinkset | rdfs:Class | Functional | 67 |
| conceptualDataset | LexicalLinkset or ConceptualizationSet | ontolex:ConceptSet | — | 68 |
| concepts | ConceptSet / LexicalLinkset / ConceptualizationSet | xsd:integer | — | 69 |
| links | LexicalLinkset | xsd:integer | — | 69 |
| avgNumOfLinks | LexicalLinkset | xsd:decimal | — | 69 |
| conceptualizations | ConceptualizationSet | xsd:integer | — | 70 |
| avgAmbiguity | ConceptualizationSet | xsd:decimal | — | 70 |
| avgSynonymy | ConceptualizationSet | xsd:decimal | — | 70 |

### Namespace URIs

| Module | Namespace | Prefix |
|---|---|---|
| Core | `http://www.w3.org/ns/lemon/ontolex#` | ontolex |
| Syntax & semantics | `http://www.w3.org/ns/lemon/synsem#` | synsem |
| Decomposition | `http://www.w3.org/ns/lemon/decomp#` | decomp |
| Variation & translation | `http://www.w3.org/ns/lemon/vartrans#` | vartrans |
| Linguistic metadata | `http://www.w3.org/ns/lemon/lime#` | lime |
| All-in-one | `http://www.w3.org/ns/lemon/all` | (import) |

## Effect Sizes / Key Quantitative Results
*Not applicable — normative specification. The only quantitative content is the WordNet 3.0 metadata example (p.71): 155287 lexicalEntries, 117659 concepts, 206941 conceptualizations, avgAmbiguity=1.33, avgSynonymy=1.76.*

## Methods & Implementation Details

- **RDF 1.1 compliance required**, language tags follow BCP47; ISO 639-1/2/3 for language codes, ISO 3166-1 for country codes. *(p.4)*
- **Turtle is the canonical serialization for examples.** Prefixes used throughout: `rdf`, `owl`, `xsd`, `skos`, `dbr`, `dbo`, `void`, `lexinfo`, `semiotics`, `oils`, `dct`, `provo`. *(p.3-4)*
- **Anonymous class pattern (adjectives):** use `owl:Restriction` inlined in `ontolex:reference` for entries that denote a class not explicitly in the ontology. *(p.16-17)*
- **Abbreviation modelling:** `lexinfo:abbreviationFor` + separate `LexicalEntry` (e.g. NASA ↔ National Aeronautics and Space Administration). *(p.11)*
- **Bank example (p.15-16):** shows how etymologicalRoot, gender, partOfSpeech, number distinguish `bank1_en`, `bank2_en`, `bank3_en`, `bank1_de`, `bank2_de` as distinct LexicalEntry instances.
- **Complex predicate composition (launch):** `synsem:submap` binds each sub-predicate's subj/obj to a shared `SyntacticArgument`. *(p.32-33)*
- **Diathesis alternation** (gave X Y vs. gave Y to X): two synBehavior links pointing at two distinct SyntacticFrames with three submaps. *(p.35)*
- **Phrase structure tree:** `decomp:Component` nodes annotated with `olia:hasTag penn:S|NP|VP|NN|V|JJ`; ordered via `rdf:_1`, `rdf:_2`. *(p.43-44)*
- **Lexical net → OntoLex mapping:** synset → LexicalConcept; word → LexicalEntry; sense → LexicalSense; lemma → canonical Form. *(p.79)*
- **Global WordNet Association extension** at `http://globalwordnet.github.io/schemas/wn#`; worked example with English and Swedish farfar uses `wn:partOfSpeech`, `wn:ili`, `wn:definition`, `wn:iliDefinition`, `wn:sense`, `wn:example`. *(p.80-82)*
- **SKOS-XL pitfall:** reified labels would make forms/entries inferred to be `skosxl:Label`, contradicting the "linguistic object, not label" philosophy. OntoLex avoids this. *(p.84)*
- **LMF relationship:** lemon imports many LMF classes but (a) grounds meaning by OWL reference, (b) provides a compact syntax-semantics interface, (c) relies on external category systems, (d) has no intentional morphology module. *(p.84)*
- **Open Annotation:** not a goal of lemon; annotations of text use OA's `oa:hasBody` / `oa:hasTarget` with the OntoLex entity as body. *(p.84-85)*
- **Four publication scenarios:** (1) Independent resources with a third-party lexicalization set, (2) Linking to 3rd party lexicon, (3) Linking to 3rd party ontology, (4) Integrated single dataset. *(p.72-73)*
- **Morphosyntactic properties enumerated** via LexInfo: Animacy, Aspect, Case, Cliticness, Definiteness, Degree, Finiteness, Gender, Modification Type, Mood, Negative, Number, Part of Speech, Person, Tense, Voice. *(p.74-75)*
- **Entry-level vs. form-level properties** discipline: e.g. gender is entry-level for nouns but form-level for adjectives (Italian `famoso` ↔ famosa/famose/famosi, each with its own gender/number). *(p.75-76)*
- **Syntactic argument types** (LexInfo): Subject, Object (direct/indirect/prepositional/genitive), Adjunct (prepositional/possessive/comparative/superlative), Copulative, Clausal (declarative/gerundive/infinitive/etc.), Attributive. *(p.77)*
- **PROV integration** for translation confidence: `lexinfo:translationConfidence` qualified by `prov:qualifiedGeneration [ prov:activity ... ]` (humanTranslationActivity vs. executionOfMyAlgorithm). *(p.78-79)*

## Figures of Interest
- **Fig 1 (p.5) Lemon_OntoLex_Core.png:** The core class diagram. Concept Set ↔ Lexical Concept ↔ Lexical Sense ↔ Ontology Entity ↔ Lexical Entry ↔ Form ↔ Word/MultiwordExpression/Affix, with all property labels and inverses.
- **Fig 2 (p.25) Lemon_Syntax_and_Semantics.png:** SyntacticFrame/SyntacticArgument/LexicalSense/OntoMap with synBehavior, synArg, ontoMapping, ontoCorrespondence (subjOfProp/objOfProp/isA), submap.
- **Fig 3 (p.39) Lemon_Decomposition.png:** LexicalEntry — subterm (reflexive); Component with constituent (reflexive) and correspondsTo to Argument/Frame.
- **Fig 4 (p.45) Lemon_Variation_and_Translation.png:** LexicoSemanticRelation with category; LexicalRelation/SenseRelation; Translation subclass; TranslationSet with trans; TerminologicalRelation; conceptRel for LexicalConcept.
- **Fig 5 (p.58) Lemon_Lime_Metadata.png:** void:Dataset subclasses for LexicalLinkset, ConceptSet, ConceptualizationSet, Lexicon, LexicalizationSet with all metadata properties.
- **Fig 6 (p.65):** avgNumOfLexicalizations formula image.
- **Fig 7 (p.66):** percentage formula image.

## Results Summary
Not an empirical paper. The artifact is a W3C Community Final Specification: the URIs, Turtle namespace declarations, class axioms, and property characteristics listed above are the result. The document is the authoritative implementation target. *(p.1)*

## Limitations
The authors explicitly enumerate non-goals and gaps *(p.4, p.84)*:
- **Does not replace SKOS** — informal taxonomies/thesauri/classification schemes stay in SKOS. *(p.4)*
- **Is not a vocabulary for annotating texts** — that is Open Annotation / NIF / Earmark. *(p.4, p.84)*
- **Is not a formal model of semantics** — it is a model of lexicography; semantics of denoted predicates is outside scope. *(p.4)*
- **Does not define linguistic categories** — relies on LexInfo, ISOcat, CLARIN, OLiA, GOLD. *(p.4)*
- **Is not generic for any linguistic data** — not for corpora, typological data, word lists. *(p.4)*
- **No intentional morphology module** (unlike LMF). Inflection patterns must be captured via external vocabularies such as LIAM; lemon only references them via `morphologicalPattern`. *(p.13, p.84)*
- **No global constraint language on the lexicon itself** (use raw OWL axioms). *(p.84)*
- **Usage conditions are not formally specified** — how to constrain sense usage is left to users; lemon only provides the `usage` hook with `rdf:value` strings. *(p.20)*

## Arguments Against Prior Work
- **rdfs:label is insufficient:** cannot express inflected forms, genders, multiple senses, usage notes, or full wordnet-style lexical resources. *(p.3)*
- **LMF (ISO-24613:2008):** XML-only; does not address syntax-semantics interface between lexica and ontologies; has syntactic overhead; no OWL-based semantics-by-reference. lemon imports LMF classes but reorganizes around the ontology interface. *(p.84)*
- **SKOS-XL reified labels:** would force forms/entries to be inferred as `skosxl:Label`, contradicting the community's stance that forms are linguistic objects, not labels. lemon therefore rejects SKOS-XL as the lexicalization mechanism. *(p.84)*
- **Earlier lemon (Buitelaar 2011):** implicit; the whole document updates and extends Buitelaar's original lemon (semantics-by-reference retained; modular decomposition added; vartrans and lime added; synsem simplified; translation and conditions formalized). *(p.3, p.4)*

## Design Rationale
- **Semantics by reference (p.3):** meaning of a LexicalEntry is pointed to (via `denotes`/`sense → reference`) rather than defined internally. This keeps the lexicon agnostic to the ontology's logical framework (OWL, RDF(S), or any KR that has a "predicate-like" interpretation).
- **Reify LexicalSense (p.17-18):** to attach per-context conditions, subject/domain, dating, register — information that would otherwise conflate with ontology semantics.
- **Separate LexicalConcept (p.20-21):** to support onomasiological lexicons (wordnets) and SKOS-style conceptual backbones; preserves a mental/linguistic abstraction distinct from ontology entities. `evokes` vs. `denotes` is the key contrast: `die → evokes :Dying` (mental concept) vs. `die → denotes dbo:deathDate` (ontology predicate).
- **Modular decomposition (p.2):** apps that only need the core `ontolex` pay no cost for synsem/decomp/vartrans/lime; minimum choice is OntoLex alone.
- **External category systems (p.4):** deliberately excluded because existing efforts (ISOcat, CLARIN, OLiA, GOLD, LexInfo) already cover morphosyntactic categories. Avoids duplication and theoretical commitment.
- **Submap for complex predicates (p.32-33):** rather than extend ontology signature with n-ary predicates, lemon decomposes a complex sense into a set of binary submappings that jointly cover the arguments. This keeps the target ontology OWL-compatible.
- **Anonymous restriction pattern for adjectives (p.16-17):** avoids ontology pollution with `:Female` classes when `∃gender.{Female}` suffices.
- **Ordered components via rdf:_N (p.42):** standard RDF Seq mechanism reused rather than introducing a new ordering vocabulary.
- **Translation at three levels (p.52):** (1) ontological equivalence = shared reference; (2) sense-level `translation` or reified `Translation`; (3) entry-level `translatableAs` for under-specified cases. Each maps to a different epistemic commitment.

## Testable Properties
- Every `LexicalEntry` has at least one `Form` and at most one `canonicalForm`. *(p.6)*
- `canonicalForm` is Functional. *(p.9)*
- `sense` is Inverse Functional; `reference` is Functional — so a LexicalSense has a unique Entry and unique ontology reference. *(p.19)*
- `ontoMapping` is both Functional and Inverse Functional — LexicalSense and OntoMap are in exact 1:1 correspondence when both present; the spec recommends reusing the same URI. *(p.28)*
- `synBehavior` is Inverse Functional. *(p.26)*
- `denotes` ≡ `sense ∘ reference` (Property Chain). *(p.14)*
- `evokes` ≡ `sense ∘ isLexicalizedSenseOf`. *(p.21)*
- `translatableAs` is Symmetric and ≡ `isSenseOf ∘ translation ∘ sense`. *(p.55)*
- `LexicoSemanticRelation` `relates exactly 2` of LexicalEntry/LexicalSense/LexicalConcept. *(p.47)*
- `LexicalRelation` subclass constrains range to exactly 2 `ontolex:LexicalEntry`. *(p.48)*
- `SenseRelation` subclass constrains range to exactly 2 `ontolex:LexicalSense`. *(p.49)*
- `ConceptualRelation` subclass constrains range to exactly 2 `ontolex:LexicalConcept`. *(p.52)*
- `Lexicon` requires at least 1 entry and exactly 1 language literal. *(p.59)*
- `LexicalizationSet` requires exactly 1 `referenceDataset`, at most 1 `lexiconDataset`, exactly 1 `lexicalizationModel`; partition is only over LexicalizationSet. *(p.62)*
- `LexicalLinkset` requires exactly 1 `conceptualDataset` of type ConceptSet and exactly 1 `referenceDataset`. *(p.68)*
- `ConceptualizationSet` requires exactly 1 `lexiconDataset` Lexicon and exactly 1 `conceptualDataset` ontolex:ConceptSet. *(p.70)*
- Language tags on forms must be consistent with the language of the containing Lexicon. *(p.60)*
- avgNumOfLexicalizations, percentage, and coverage ratios defined as specific quotients (testable by counting). *(p.65-66, p.71-72)*
- TransitiveFrame axiom: exactly 1 subject and exactly 1 directObject. *(p.77)*

## Relevance to Project

**Direct target for propstore's concept registry / form_utils.py rewrite.** The project's CLAUDE.md explicitly cites "ontology lexicalization (lemon/Buitelaar 2011)" as a foundation. This 2016 community report is the *implementation-level* specification — it's what actual RDF tooling produces and consumes. Concrete alignments:

- **propstore Form (dimensional) vs. ontolex:Form (grammatical):** naming collision. propstore's Form is dimensional structure (CEL-typed parameters). OntoLex Form is a grammatical realization of a lexical entry with writtenRep/phoneticRep. If we adopt ontolex IRIs, we should rename one side or prefix namespaces. Worth surfacing to Q.
- **LexicalSense + synsem:condition is the McCarthy-style context hook:** sense carries `usage`/`condition` modulating when the entry denotes the reference. Maps cleanly to propstore's "contexts are first-class logical objects qualifying when propositions hold".
- **LexicalConcept vs. propstore concept:** propstore treats concepts as frame elements (Fillmore 1982) with Pustejovsky qualia structure. OntoLex LexicalConcept is explicitly *mental* (a skos:Concept) distinct from ontology referent — matches propstore's two-tier "concept registry that links linguistic expressions to ontological entities".
- **vartrans:TerminologicalRelation with diatopic/diaphasic/diachronic/diastratic/dimensional categories:** non-trivial input to cross-paper reconciliation in `reconcile-vocabulary`. When two papers use different lemmas for the same concept, the category label tells us *why* they differ (register vs. region vs. time vs. style) — this is evidence the argumentation layer can weigh.
- **LexicalizationSet metadata (coverage, avgAmbiguity, avgSynonymy):** gives propstore measurable quantities about its own knowledge base — how well the concept registry covers the papers' claims.
- **Semantics-by-reference principle:** aligns with propstore's architecture that source-of-truth storage is immutable and references (not copies) are the norm.
- **The four publication scenarios map to how propstore exposes knowledge:** propstore is closest to scenario 4 (integrated) but the spec's independent-resource model is the cleaner one for multi-contributor settings. Worth considering.

## Open Questions
- [ ] Should propstore's `form_utils.py` adopt the ontolex namespace directly, or mint its own and `owl:equivalentClass` map? The naming collision (propstore Form = dimensional, ontolex Form = grammatical) is unresolved.
- [ ] `LexicalSense` with `condition` is at `LexicalSense` granularity, not claim granularity. If propstore claims carry conditions, do conditions attach to (claim, sense) pairs or to senses?
- [ ] `evokes` is a property chain through `sense ∘ isLexicalizedSenseOf` — does propstore's argumentation layer need to reason over the chained form or just the direct arc?
- [ ] How does the `submap` mechanism compose with propstore's multi-context claim encoding? Complex predicate decomposition seems structurally related to propstore's conditional claim operators.
- [ ] SKOS-XL rejection: propstore should document why it does not use SKOS-XL reified labels, since ontolex makes this an explicit design commitment.

## Related Work Worth Reading
- **Buitelaar 2011 — Ontology Lexicalization: The lemon Perspective** (already in collection as `Buitelaar_2011_OntologyLexicalizationLemon`). This is the seed paper; 2016 report is the community-ratified evolution.
- **LexInfo 2.0** — `http://www.lexinfo.net/ontology/2.0/lexinfo` — the concrete linguistic-categories vocabulary used throughout the examples.
- **LIAM** — morphological pattern vocabulary, for the `morphologicalPattern` property whose implementation is deliberately not specified by OntoLex.
- **LMF (ISO-24613:2008)** — the XML lexicon framework lemon critiques and draws from. Worth reading for the "what intentional morphology costs" design trade-off.
- **SKOS / SKOS-XL** — relationship to taxonomies; the rejected-reified-label argument.
- **OLiA** — Ontologies of Linguistic Annotation; used for Penn TreeBank tagging in decomp examples.
- **VOID, VOAF, DCAT, PROV** — used by lime for dataset metadata and translation provenance. PROV's qualifiedGeneration pattern is particularly useful for propstore claim provenance.
- **Open Annotation** — complements OntoLex for text annotation.
- **GlobalWordnet `wn:` extension** at `http://globalwordnet.github.io/schemas/wn#` — recommended extension for wordnet-style lexical nets with ILI alignment.
