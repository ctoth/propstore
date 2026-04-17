# Citations

## Reference List

The W3C Community Report uses inline hyperlinks rather than a numbered bibliography. The following are the external resources, vocabularies, standards, and prior works explicitly referenced (or linked via `<a href>`) in the normative text, gathered here in citation-like form.

### Prior lexicon / semantic models

- **Buitelaar, P., Cimiano, P., McCrae, J., et al. (2011). Ontology Lexicalization: The lemon Perspective.** The seed paper for this spec; cited by the Overview as the origin of the *semantics by reference* principle. URL: the "lemon" label throughout the document refers to this.
- **Lexical Markup Framework (LMF), ISO-24613:2008.** Referenced in sections 2.1 (Purpose of the model), 2.2 (implicit), and 10.2 (explicit comparison).
- **LexInfo ontology, v2.0.** `http://www.lexinfo.net/ontology/2.0/lexinfo` — used throughout examples to supply grammatical categories.
- **LIR model** — linguistic information repository, cited in 2.1.
- **LMM — Linguistic Meta Model** — cited in 2.1.
- **semiotics.owl** ontology design pattern — `http://www.ontologydesignpatterns.org/cp/owl/semiotics.owl#` — provides `semiotics:Expression`, `semiotics:Meaning`, `semiotics:denotes` that lemon SubClassOfs / SubPropertyOfs.
- **Senso Comune core model** — cited in 2.1.

### W3C / external standards used

- **RDF 1.1 specification** — `https://www.w3.org/TR/rdf11-concepts/`.
- **OWL 2** — `http://www.w3.org/2002/07/owl#`.
- **RDF Schema** — `http://www.w3.org/2000/01/rdf-schema#`.
- **XML Schema Datatypes** — `http://www.w3.org/2001/XMLSchema#`.
- **SKOS** — `http://www.w3.org/2004/02/skos/core#` — used as superclass for LexicalConcept and for alignment in Section 10.1.
- **SKOS-XL** — `http://www.w3.org/2008/05/skos-xl` — contrast model rejected as a lexicalization target.
- **Dublin Core Terms (dct / dc)** — `http://purl.org/dc/terms/`.
- **DCMI Types** — `http://purl.org/dc/dcmitype/` — used by Open Annotation example.
- **PROV Ontology** — `http://www.w3.org/ns/prov#` — used for translation confidence and dataset provenance.
- **VoID — Vocabulary of Interlinked Datasets** — `http://rdfs.org/ns/void#` — supplies `void:Dataset`, `void:Linkset`, `void:entities`, `void:vocabulary`.
- **VOAF — Vocabulary of a Friend** — `http://purl.org/vocommons/voaf#` — `voaf:Vocabulary`, `voaf:classNumber`, `voaf:propertyNumber`.
- **DCAT** — `http://www.w3.org/ns/dcat#` — referenced as a complementary metadata profile.
- **Open Annotation (oa)** — `http://www.w3.org/ns/oa#` — Section 10.3.
- **BCP 47 language tags**, **ISO 639-1/2/3**, **ISO 3166-1** — Section 2.3.
- **DBpedia ontology** — `http://dbpedia.org/ontology/` and resource — many examples.

### Linguistic category systems / data category registries

- **ISOcat** data category registry — `http://www.isocat.org/` (example uses `http://www.isocat.org/datcat/DC-1345`, `DC-396`, `DC-1333`).
- **CLARIN concept registry** — referenced alongside ISOcat.
- **OLiA — Ontologies of Linguistic Annotation** — `http://purl.org/olia/olia.owl` — used for Penn TreeBank tags in decomp examples.
- **GOLD — General Ontology for Linguistic Description** — referenced in Section 2.1.
- **Penn TreeBank tagset** — referenced in Section 5.3.
- **LIAM** — morphological-pattern vocabulary cited as a possible implementation of `morphologicalPattern`.

### Lexical resources and annotation

- **Princeton WordNet 3.0** — `http://wordnet-rdf.princeton.edu/ontology/`; the canonical example.
- **Global WordNet Association schema** — `http://globalwordnet.github.io/schemas/wn#` — wn: prefix extension to OntoLex-Lemon used in Section 9.
- **CILI — Collaborative Interlingual Index** — `http://globalwordnet.github.io/schemas/` — used in Swedish/English farfar example.
- **NIF — NLP Interchange Format** — cited as an alternative for text annotation.
- **Earmark — Extremely Annotational RDF Markup** — cited as an alternative.

### Translation and language identification

- **Library of Congress Vocabulary** — `http://id.loc.gov/vocabulary/iso639-1/*`, `iso639-2/*`.
- **Lexvo.org** — `http://www.lexvo.org/id/iso639-3/*`.
- **purl.org/net/translation-categories** — vartrans:category vocabulary.

### Contributors (Acknowledgements, p.85)

- Guadalupe Aguado-de-Cea (Universidad Politécnica de Madrid, Spain)
- Manuel Fiorelli (Università degli Studi di Roma Tor Vergata, Italy)
- Francesca Frontini (ILC «A. Zampolli», Italian National Research Council)
- Aldo Gangemi (LIPN, Université Paris 13, France)
- Jorge Gracia (Universidad Politécnica de Madrid, Spain)
- Thierry Declerck (DFKI, Germany)
- Anas Fahad Khan (ILC «A. Zampolli», Italy)
- Elena Montiel Ponsoda (Universidad Politécnica de Madrid, Spain)
- Armando Stellato (Università degli Studi di Roma Tor Vergata, Italy)

### Editors (p.1)

- Philipp Cimiano (Cognitive Interaction Technology Excellence Center, Bielefeld University)
- John P. McCrae (Insight Centre for Data Analytics, National University of Ireland, Galway)
- Paul Buitelaar (Insight Centre for Data Analytics, National University of Ireland, Galway)

---

## Key Citations for Follow-up

1. **Buitelaar 2011 "Ontology Lexicalization: The lemon Perspective"** — already in the propstore collection as `Buitelaar_2011_OntologyLexicalizationLemon/`. This is the seed paper the 2016 report updates. Read first to understand *semantics by reference* and the original design choices.
2. **LexInfo 2.0 ontology** — concrete vocabulary for POS, gender, number, syntactic frames used throughout examples. Without it the Turtle examples are unparseable. Likely needed as a dependency for any propstore implementation of OntoLex.
3. **Global WordNet Association `wn:` schema** (`http://globalwordnet.github.io/schemas/wn#`) — recommended extension for lexical nets with ILI alignment; demonstrates the ontolex:LexicalConcept integration pattern.
4. **LMF (ISO-24613:2008)** — Section 10.2 enumerates four concrete differences between lemon and LMF that clarify the design space for propstore's own lexical layer.
5. **PROV-O** — `http://www.w3.org/ns/prov#` — the `qualifiedGeneration` pattern used for translation confidence is directly transferable to propstore claim provenance (e.g. vacuous-opinion annotations, algorithm-vs-human extraction).
