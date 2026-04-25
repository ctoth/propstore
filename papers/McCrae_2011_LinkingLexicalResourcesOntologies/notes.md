---
title: "Linking Lexical Resources and Ontologies on the Semantic Web with Lemon"
authors: "John McCrae, Dennis Spohr, Philipp Cimiano"
year: 2011
venue: "ESWC 2011 (Extended Semantic Web Conference), LNCS 6643, pp. 245-259"
doi_url: "10.1007/978-3-642-21034-1_17"
pages: "245-259"
affiliation: "AG Semantic Computing, CITEC, University of Bielefeld"
publisher: "Springer-Verlag Berlin Heidelberg"
---

# Linking Lexical Resources and Ontologies on the Semantic Web with Lemon

## One-Sentence Summary

Introduces *lemon* (Lexicon Model for Ontologies), an RDF(S)-based lexicon model that links lexical resources to Semantic-Web ontologies via LexicalEntry / Form / LexicalSense / Reference, does not prescribe a fixed inventory of linguistic categories (delegating to external data-category registries such as ISOcat / GOLD / OLiA), and is demonstrated by converting WordNet to lemon, auto-generating a lemon-LexInfo lexicon for FOAF, and merging the two. *(p.245, p.250)*

## Problem Addressed

Current Semantic-Web label vocabularies (RDFS label, SKOS preferred/alternative/hidden) can only attach very limited linguistic information to ontologies, blocking effective NLP over ontological data. At the same time, rich lexical resources (Lefff, WordNet, LMF-based lexica) are trapped in "data silos" with no mechanism for relating lexica to ontologies. Prior lexicon-ontology models either fix a specific linguistic category inventory (GOLD, OLiA) or lack dereferenceable RDF URIs (LMF). Word-sense-based models in WordNet/LMF rely on the traditional discrete word-sense view which has been criticised as ontologically unsound (Gangemi et al.) and linguistically unsound (Kilgarriff). *(p.245-247)*

## Key Contributions

- **lemon core model** — RDF(S)-based class graph (Lexicon, LexicalEntry {Word, Phrase, Part}, Form, Representation, LexicalSense, Reference, Property, Frame/Argument, Component, Node) with explicit separation of lexical layer from ontology (semantics delegated to the ontology via `reference`). *(p.248-250)*
- **Open-category design** — lemon does not ship with a fixed linguistic category inventory; instead it supports reuse of any linguistic ontology such as GOLD, OLiA, or ISOcat data categories [[8], [5], [13]]. The concrete binding is done per lexicon. *(p.245-246, p.250)*
- **lemon-LexInfo extension** — concrete second-version LexInfo built on lemon that imports ISOcat morphosyntax as OWL classes/properties (complex data categories → RDF properties, simple data categories → OWL individuals), adds subclass/subproperty axioms, and gives OWL-style compositional definitions of subcategorization frames from COMLEX. Reduces COMLEX's 163 frames to 36 basic frames + 4 argument-control modifiers. *(p.251-252)*
- **Experiment 1: WordNet → lemon** — conversion methodology mapping WordNet synsets to lemon References, WordNet word-senses to lemon LexicalSenses (intersection of lexical/semantic usage), and switching part-of-speech from sense/synset level to word level via LexInfo/ISOcat morphosyntactic properties. Also manually recovered alternative forms that the Van Assem et al. RDF WordNet had dropped. *(p.253)*
- **Experiment 2: Auto-generate lemon-LexInfo lexicon for FOAF ontology** — uses the Monnet Lemon-Editor (label extraction from RDFS/SKOS/URI fragments; Lucene tokenizer; Stanford POS tagger; Stanford lemmatizer; Stanford Parser; rule-based subcategorization from phrase-structure patterns → OWL-typed frames). 113 Lexical Entries generated for 63 FOAF entities (12 classes + 51 properties), 81.5% overall accuracy. *(p.254-255)*
- **Experiment 3: Merge FOAF-generated lexicon with WordNet-lemon** — entry-level equality rule (same canonical written rep modulo capitalisation; equal POS if specified; no contradictory linguistic properties; non-canonical forms matchable without contradiction). 69% of FOAF entries map to WordNet entries; remaining 31% break into MWEs (22.1%), proper nouns (7.9%), other (0.9%). *(p.256-257)*
- **Multilingual modelling** — same ontology reference shared across entries in different languages (e.g., Dutch `:maag` and English `:stomach` both referencing `EHDAA_2993`), enabling translations without modifying the original lexicon or ontology. *(p.251)*
- **Framework for consistency checking** — because data categories are imported as OWL, linguistic conditions such as "every French noun is masculine and/or feminine" can be expressed and checked without an extra modelling language (contrast LMF). *(p.252)*

## Study Design (empirical components)

- **Type:** Three engineering experiments over the published model.
- **Experiment 1 population:** WordNet (Fellbaum 1998) as imported from the Van Assem et al. RDF/OWL conversion [24]; reshaped into lemon with alternative forms manually reintroduced. No quantitative evaluation reported. *(p.253)*
- **Experiment 2 population:** FOAF 0.98 ontology; 63 entities (12 classes, 51 properties); generation produced 113 LexicalEntries. *(p.254-255)*
  - Tooling: Monnet Lemon-Editor at `http://monnetproject.deri.ie/Lemon-Editor`; Lucene tokenizer; Stanford Tagger [23]; Stanford Parser [15]; rule-based subcategorizer.
  - Primary endpoint: per-component precision and overall entry accuracy (Table 2). *(p.255)*
- **Experiment 3 population:** The two lexica from Experiments 1 and 2; per-entry equality check with the four rules above; report mapping rates to WordNet (Table 3). *(p.256-257)*

## Methodology

The paper is **model + RDF/OWL schema + three illustrative experiments**, not an empirical study in the statistical sense. The methodology consists of:

1. Survey prior art — SKOS, WordNet-in-RDF, GOLD, OLiA, LMF, ISOcat, LexInfo, and identify gaps (p.246-248).
2. Define the lemon class graph in RDF(S) with the elements enumerated below (p.248-250).
3. Extend it to lemon-LexInfo by importing ISOcat morphosyntax and compositionally defining COMLEX-style subcategorization frames in OWL (p.251-252).
4. Demonstrate three use-cases: legacy lexicon import (WordNet), ontology-driven lexicon generation (FOAF), and merging (FOAF ∪ WordNet) (p.253-257).

## Core Model (lemon core elements, p.248-250)

- **Lexicon** — resource; mono-lingual; has `language` (string tag) and optionally `topic`. *Example:* English names for diseases. *(p.248)*
- **LexicalEntry** — a single term; morphosyntactic information attaches here, so all forms of one entry share the same syntax. Variants (abbreviations, synonyms with same syntax) are separate entries connected via `lexicalVariant`. Subclasses: **Word**, **Phrase**, **Part** (of word). *Example:* "Cancer of the mouth" is one LexicalEntry; "Mouth cancer" is another, marked as a `lexicalVariant` of the first. *(p.249)*
- **Form** — inflectional variant of an entry. Distinguished subtypes via `canonicalForm` (lemma), `otherForm`, `abstractForm`. *Example:* LexicalEntry "bacterium" has forms "bacterium" (canonical) and "bacteria" (other). *(p.249)*
- **Representation** — each Form may have multiple representations: `writtenRep` (most important), phonetic, etc. *(p.249)*
- **LexicalSense** — correspondence between a LexicalEntry and an ontology entity (not the sense itself but the *link*). Explicitly **not assumed finite or disjoint**. May carry: `context`, `condition` (with subproperties `propertyDomain`, `propertyRange`), `definition`, `example`. May be labelled `preferred`, `alternative`, or `hidden` by analogy to SKOS. *Example:* "influenza" and "flu" both sense-link to `DOID_8469` in OBO; "influenza" marked as scientific context, "flu" as layman. *(p.249)*
- **Reference** — pointer from a LexicalSense (or entry) to an ontology entity. Semantics delegated entirely to the ontology. *(p.249)*
- **Property** — every lemon element can carry properties. Generic top-level `lexicalProperty`; concrete linguistic properties should be subproperties. *Example:* forms "bacterium"/"bacteria" have property `number` = `singular`/`plural`; entry carries `partOfSpeech` = `noun`. *(p.249)*
- **Frame / Argument** — subcategorization frames encode valency of verbs and other predicators. Each argument is a resource linked from the Frame (syntactic role) and from the LexicalSense (semantic role). *Example:* property `complicated_by` is a LexicalEntry with a frame for "Y complicates X" where X,Y are arguments. *(p.249)*
- **Component** — ordered RDF list decomposing a multi-word or compound LexicalEntry into components (which are themselves LexicalEntries). *Example:* German "hämorrhagisches Fieber" decomposes into "hämorrhagisch" + "Fieber"; "Ebolavirus" decomposes into "Ebola" + "Virus". *(p.250)*
- **Node / edge / leaf** — a LexicalEntry may carry a phrase-structure tree; internal nodes link to components via `edge` or `leaf` arcs. *Example:* parse of "African swine fever" = NP[JJ("african"), NP[NN("swine"), NP[NN("fever")]]] disambiguates it as "African" + "swine fever" rather than "African swine" + "fever". *(p.250)*
- **MorphPattern / MorphTransform / Prototype / generates / nextTransform / orStem** — morphology sub-model hanging off LexicalEntry via `pattern`; lets morphological rules be stated once and applied to derive Forms. *(p.248 Fig. 1)*

## Key Equations / Formal Definitions

### OWL axiomatisation of linguistic categories (p.252)

$$
Noun \equiv \exists partOfSpeech.NounPOS
$$
Where: `partOfSpeech` is a property imported from ISOcat and typed as the general `lexicalProperty`; `NounPOS` is the range class whose individuals are the simple ISOcat values for the complex POS category. `Noun` is one of the specific LexicalEntry subclasses introduced beyond `Word`/`Phrase`/`Part`. *(p.252)*

### Compositional frame definitions (p.252)

$$
IntransitiveFrame \equiv (=1\,subject) \sqcap (=0\,directObject) \sqcap (=0\,indirectObject)
$$
Where: `subject`, `directObject`, `indirectObject` are OWL syntactic-role properties introduced as part of lemon-LexInfo; cardinality restrictions compose the Frame's definition. *(p.252)*

$$
PrepositionalObjectFrame \equiv \exists prepositionalObject
$$
*(p.252)*

$$
IntransitivePPFrame \equiv IntransitiveFrame \sqcap PrepositionalObjectFrame
$$
Where: a hierarchy of abstract frames (e.g., `PrepositionalObjectFrame`) is introduced so that concrete frames can be built by conjunction. This reduces COMLEX's 163 frames to 36 base frames + 4 argument-control modifiers, published at `http://www.lexinfo.net/basic-frames`. *(p.252)*

## Parameters

### Part-of-speech inventory sizes across formalisms (Table 1, p.247)

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| #POS values, WordNet 2.0 | — | count | 5 | — | 247 | baseline |
| #POS values, GOLD | — | count | 81 | — | 247 | linguistic ontology |
| #POS values, ISOcat | — | count | 115 | — | 247 | data-category registry |
| #POS values, OLiA | — | count | 174 | — | 247 | alignment of GOLD/ISOcat |
| #POS values, LexInfo 1.0 | — | count | 11 | — | 247 | LMF-derived |

### lemon-LexInfo frame compression (p.252)

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| COMLEX frames (before) | — | count | 163 | — | 252 | source vocabulary |
| Basic frames (after) | — | count | 36 | — | 252 | via OWL compositional defs |
| Argument-control modifiers | — | count | 4 | — | 252 | adds combinators |

### FOAF lexicon generation corpus (p.255)

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| FOAF entities input | — | count | 63 | — | 255 | FOAF 0.98 |
| FOAF classes | — | count | 12 | — | 255 | |
| FOAF properties | — | count | 51 | — | 255 | |
| LexicalEntries generated | — | count | 113 | — | 255 | extras for MWEs |

## Effect Sizes / Key Quantitative Results

### Per-component precision of lemon-LexInfo generation on FOAF (Table 2, p.255)

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Tokenizer errors | count + precision | 1 err / 112 correct → 99.1% | — | — | FOAF labels | 255 |
| POS Tagger errors | count + precision | 8 / 105 → 92.9% | — | — | FOAF labels | 255 |
| Parser errors | count + precision | 12 / 101 → 89.4% | — | — | FOAF labels | 255 |
| Subcategorizer errors | count + precision | 6 / 57 → 92.1% | — | — | FOAF labels, raw parses | 255 |
| Subcategorizer (parses corrected) | count + precision | 2 / 61 → 96.8% | — | — | FOAF labels, gold parses | 255 |
| Overall entry accuracy | precision | 81.5% | — | — | 21 errors / 103 entries judged end-to-end | 255 |

Note: the accuracy denominator quoted in prose (103) differs from the 113 generated entries because some entries were not judged at all levels; Tokenizer column totals 113. *(p.255)*

### FOAF ↔ WordNet mapping (Table 3, p.256)

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Mapped to WordNet | count, % | 78 (69.0%) | — | — | 113 FOAF entries | 256 |
| Not mapped (multiple word expression) | count, % | 25 (22.1%) | — | — | | 256 |
| Not mapped (proper noun) | count, % | 9 (7.9%) | — | — | | 256 |
| Not mapped (other; "weblog" neologism) | count, % | 1 (0.9%) | — | — | | 256 |

## Rules / Algorithms

### Subcategorization rule schema for Lemon-Editor (p.254)

A subcategorization rule consists of four parts:
1. A **phrase-structure pattern** matching the label of the LexicalEntry, e.g., `FRAG (VP, PP)` = fragment made of verb phrase + prepositional phrase, as in "located in".
2. A set of **classes** the ontology entity must be an instance of via RDF `type` (typically basic OWL types such as `ObjectProperty`).
3. The **class of the generated frame** (selected from the lemon-LexInfo frame hierarchy).
4. The **definition of the arguments** of the frame, with syntactic + semantic roles.

### Entry-equality rule for experiment 3 (p.256)

Two entries e1, e2 are considered equal iff:
1. Canonical form has the same `writtenRep` or differs only in capitalisation of the initial letter.
2. Part-of-speech tag is equal, **if specified** in both (partial match allowed if one omits POS).
3. There is no linguistic property on which e1 and e2 carry different values (one-sided missing values do not break equality).
4. Non-canonical forms can be paired such that each pair has the same `writtenRep` and no contradictory property values. (Needed because the same surface form may fill different grammatical slots; e.g., "made" is both preterite and past participle of "make".)

### WordNet → lemon conversion (p.253)

1. Map WordNet synsets to lemon `reference` targets (synsets + inter-synset links act as a quasi-ontology).
2. Map WordNet word-senses to lemon `LexicalSense` (= intersection between lexical usage of the entry and semantic usage of the ontology entity).
3. Map WordNet words to lemon `LexicalEntry` one-to-one (definitions corresponded well).
4. Manually recover alternative forms (the Van Assem RDF/OWL WordNet [24] dropped them).
5. Move part-of-speech from sense/synset level (WordNet convention) to entry level (lemon convention) via LexInfo/ISOcat morphosyntactic properties.

### Turtle example: multilingual reuse of one ontology entity (p.251)

```
@prefix lemon: <http://www.monnet-project.eu/lemon#> .
@prefix isocat: <http://www.isocat.org/datcat/> .

:maag
    lemon:canonicalForm [ lemon:writtenRep "maag"@nl ;
        isocat:DC-1298 isocat:DC-1387 ] ;      # number=singular
    lemon:otherForm    [ lemon:writtenRep "magen"@nl ;
        isocat:DC-1298 isocat:DC-1354 ] ;      # number=plural
    isocat:DC-1345 isocat:DC-1333 ;             # partOfSpeech=noun
    isocat:DC-1297 isocat:DC-1880 ;             # gender=feminine
    lemon:sense [
        lemon:reference <http://purl.org/obo/owl/EHDAA#EHDAA_2993> ] .

isocat:DC-1298 rdfs:subPropertyOf lemon:property .
isocat:DC-1345 rdfs:subPropertyOf lemon:property .
isocat:DC-1297 rdfs:subPropertyOf lemon:property .
```

Then `:stomach` with `writtenRep "stomach"@en` references the same EHDAA_2993 entity. Publishing a translated lexicon requires no change to the source lexicon or source ontology. *(p.251)*

### Turtle example: WordNet synset in lemon (p.253)

```
lwn:marmoset-noun-entry rdf:type lemon:LexicalEntry ;
    lexinfo:partOfSpeech lexinfo:noun ;
    lemon:sense lwn:sense-marmoset-noun-1 ;
    lemon:canonicalForm lwn:word-marmoset-canonicalForm .

lwn:sense-marmoset-noun-1 lemon:reference wn20:synset-marmoset-noun-1 .

lwn:word-marmoset-canonicalForm lemon:writtenRep "Marmoset"@en .
```
`lwn` is the lemon-WordNet namespace, `wn20` is the original WordNet-RDF mapping. *(p.253)*

## Figures of Interest

- **Fig. 1 (p.248):** UML-style class diagram of lemon core. Central `LexicalEntry*` (subclasses: Word, Phrase, Part) with `entry` link from Lexicon, `form` to LexicalForm (with `canonicalForm`, `otherForm`, `abstractForm`), `sense` to LexicalSense (linking to Ontology via `reference`/`isReferenceOf`), `decomposition` into Component list, `phraseRoot` into Node tree (edge/leaf arcs), `synBehavior` into Frame (with `synArg` → Argument and `marker`, with `semArg`/`subjOfProp`/`objOfProp`/`isA`/`extrinsicArg` linking to LexicalSense). `MorphPattern` + `MorphTransform` + `Prototype` sub-graph attached via `pattern` and `transform`/`nextTransform`/`generates`/`orStem` drives morphology. `LexicalCategory` and `lexicalProperty` hang on the right. Annotations: LexicalEntry has three subclasses (Word, Phrase, Part); definition/example are represented as nodes-with-value; `condition` subproperties are `propertyDomain`/`propertyRange`.
- **Parse tree on p.250:** NP[JJ("african"), NP[NN("swine"), NP[NN("fever")]]] — disambiguating "African swine fever".

## Results Summary

- The lemon RDF(S) model captures WordNet's core structure cleanly; authors believe lemon can act as a vendor-neutral interchange format for merging lexica without loss. *(p.253, p.257)*
- Auto-generating a lexicon from just an ontology's labels is feasible at 81.5% overall entry accuracy for FOAF; most errors come from the parser's bias toward full-sentence parses on fragmentary labels. *(p.255)*
- ~69% of auto-generated FOAF entries can be replaced by pre-existing WordNet entries via simple equality matching, confirming a large reusability gain from sharing entries. *(p.256-257)*
- The remaining 31% are dominated by MWEs (22.1%) and proper nouns (7.9%) that WordNet under-covers — motivating collaborative expansion via linked data. *(p.257)*

## Methods & Implementation Details

- Toolchain for Experiment 2: Lucene tokenizer, Stanford Tagger [23], Stanford lemmatizer, Stanford Parser [15], rule-based subcategorizer. *(p.254)*
- Monnet Lemon-Editor UI at `http://monnetproject.deri.ie/Lemon-Editor`; auto-generates most lexicon fields for a given ontology. *(p.254)*
- Publicly available resources: lemon namespace `http://www.monnet-project.eu/lemon#`; full technical report `http://www.lexinfo.net/lemon-cookbook.pdf`; lemon↔LMF converter `http://www.lexinfo.net/lemon2lmf`; lemon-LexInfo LMF source `http://www.lexinfo.net/lmf`; basic frames list `http://www.lexinfo.net/basic-frames`. *(p.250, p.252)*
- ISOcat integration: DCIF files for the morphosyntax section converted to RDF; complex data categories → RDF properties, simple data categories → OWL individuals; each property declared `subPropertyOf` the appropriate lemon property (mostly `lexicalProperty`, but `register` mapped to a sense-level `context`). *(p.252)*
- ISO data categories referenced by numeric URIs (e.g., `DC-1298` = number, `DC-1345` = partOfSpeech); lexicon authors must declare `isocat:DC-XXXX rdfs:subPropertyOf lemon:property` for properties they use. *(p.251)*

## Limitations

- Generated lexica cover only lexical entries and canonical/alternative forms; they do not disambiguate to specific senses when linking to WordNet (e.g., "ID" could be "identification" or "Idaho"; the merge maps the word, not the sense). *(p.256)*
- Parser bias toward full sentences is the dominant error source in Experiment 2 (12 errors / 101 correct = 89.4%). Discarding sentence parses did not help because the next-best parse was typically the same verb-phrase parse. *(p.255)*
- FOAF labels are overwhelmingly noun phrases, which means the subcategorizer's grammar of frames is barely stressed; authors acknowledge need for evaluation on an ontology with more complex labels and predicates of arity > 2 (e.g., donative verbs). *(p.255)*
- WordNet is under-populated for MWEs and proper nouns (jointly ~30% of FOAF entries); addressing this requires collaborative resource expansion, not lemon itself. *(p.257)*
- No formal evaluation of the WordNet→lemon conversion in Experiment 1 — only qualitative claim of "relatively close". *(p.253)*
- Authors state lemon is **not technically an instantiation of LMF** — there are modelling differences due to RDF and optimizations; only "many aspects" correspond directly. *(p.250)*

## Arguments Against Prior Work

- **SKOS** — sufficient for simple label attachment but cannot represent morphology, phrase structure, or subcategorization information needed by modern lexica (e.g., Lefff). *(p.246)*
- **RDF-ified / "ontologized" WordNet** — limited by the amount of data in WordNet and by WordNet's own format; WordNet's conceptual model is "unsound from an ontological perspective" (citing Gangemi et al. [11]). *(p.247)*
- **GOLD, OLiA** — provide inventories of linguistic categories but do not provide a methodology for representing morphosyntactic information per se. *(p.246)*
- **LMF** — rich but has no mechanism for relating lexica to ontologies, and relies on traditional word-sense model criticized by Kilgarriff [14]. *(p.247)*
- **LexInfo (v1)** — good separation of linguistic layer vs semantic-syntactic correspondence, but based on a non-canonical form of LMF without dereferenceable URIs. Authors republished LMF themselves and replaced LMF's 3 generic relations `isAssociated`, `isPartOf`, `isAdorned` with specific ones like `hasWordForm`. *(p.247)*
- **Van Assem WordNet-RDF [24]** — loses information about alternative forms; authors manually recovered these. *(p.253)*
- **Existing lexica in general** — confined to "data silos" by format/distribution; a specific disadvantage when creating lexica for specific domains (e.g., SNOMED) that must reuse general-domain terms. *(p.245)*

## Design Rationale

- **RDF(S)-based** — chosen so lexica can be published as linked data and combined with existing ontological data. Enables cheap reuse of external linguistic ontologies without a separate modelling language. *(p.246, p.252)*
- **Openness w.r.t. linguistic categories** — deliberate non-commitment: the paper explicitly chooses not to prescribe an inventory, because different applications prefer different inventories and disagreements exist even on fundamentals like part-of-speech (see Table 1 and the GOLD vs others example on p.247). Data categories are externalised to ISOcat-style registries. *(p.246, p.248)*
- **Separate lexical layer from semantic layer** — inherited from LexInfo via LMF tradition; ensures that the lexical half can evolve independently and that the same LexicalEntry can reference multiple ontologies. *(p.247)*
- **Senses are not finite/disjoint** — explicit rejection of the classical WordNet-style enumerated-discrete-senses assumption, aligning with Kilgarriff's "I Don't Believe in Word Senses" critique [14]. Senses are treated as context-conditioned correspondences, with optional `preferred`/`alternative`/`hidden` labelling borrowed from SKOS. *(p.249)*
- **Entry-level subclasses Word / Phrase / Part** — replaces the LexInfo/LMF entry hierarchy with a minimal one; specific classes like Verb, NounPhrase are defined **axiomatically** via existential restrictions on ISOcat properties rather than hard-wired. *(p.252)*
- **Compositional OWL frames** — using OWL for subcategorization frames collapses COMLEX from 163 frames to 36 + 4 modifiers, gives consistency-checking for free, and avoids inventing a new modelling language. *(p.252)*
- **Replacement of LMF's 3 generic properties with specific ones like `hasWordForm`** — because generic property names interact badly with RDF inference and linked-data URIs. *(p.247)*
- **Alternative-form recovery in WordNet conversion** — information loss in the chosen source [24] was judged critical enough to manually repair. *(p.253)*

## Testable Properties

- A lemon lexicon is monolingual: each `Lexicon` instance carries exactly one `language` tag, so all of its entries are in that language. *(p.248)*
- All forms of one `LexicalEntry` must share the same syntax; variants with different syntax are modelled as separate entries connected by `lexicalVariant`. *(p.249)*
- `LexicalSense` is a relation object, not a type object — it is the intersection of a `LexicalEntry` and an ontology entity, not a node of the ontology. *(p.249)*
- `lemon:sense` objects are not assumed to be finite or disjoint per entry. *(p.249)*
- Part-of-speech is attached at the `LexicalEntry` level, **not** at the `LexicalSense` level (contra WordNet). *(p.253)*
- Any ISOcat property used in a lexicon must declare `rdfs:subPropertyOf lemon:property` (or a more specific subproperty of it), so all linguistic properties can be enumerated uniformly. *(p.251)*
- With the lemon-LexInfo axiomatisation, any entry classified as `Noun` must satisfy `∃partOfSpeech.NounPOS`; this enables OWL consistency checks. *(p.252)*
- Compositional frame constraints such as `IntransitiveFrame ≡ (=1 subject) ⊓ (=0 directObject) ⊓ (=0 indirectObject)` are OWL-checkable. *(p.252)*
- Two lemon entries merge iff: same canonical `writtenRep` (modulo initial-capital), equal POS if specified, no contradictory linguistic properties, and non-canonical forms can be paired without contradiction. *(p.256)*
- `lemon:reference` carries the ontology semantics; two lexical entries in different languages that point at the same URI denote the same ontological entity. *(p.251)*
- Multi-word expressions decompose via an **ordered** RDF list of `Component`, each a lexical entry. Order is significant. *(p.250)*

## Relevance to Project

**High, anchor-level.** This paper is the canonical lemon specification. propstore's concept layer formally links linguistic expressions to ontological entities via lemon (per project CLAUDE.md: "The concept registry formally links linguistic expressions to ontological entities (lemon model)"). The following aspects of lemon map directly onto propstore's concept/semantic layer:

- `LexicalEntry` ↔ propstore's lexical surface representation; `Form` / `Representation` ↔ multi-form/phonetic alternatives per entry.
- `LexicalSense` (not-finite, not-disjoint) ↔ propstore's non-commitment principle — the system should not collapse sense disagreement at storage time.
- `Reference` ↔ propstore's concept-registry mapping of a form to an ontological concept; concepts stay distinct from the lexical items that name them.
- `Frame`/`Argument` ↔ Fillmorean frame semantics that the concept layer is grounded in (per project CLAUDE.md).
- `Component` decomposition ↔ Pustejovsky-style structured internal composition for multi-word/compound concepts.
- OWL-composed frames and cardinality-constrained definitions ↔ propstore's CEL + Z3 typing of forms.
- `preferred`/`alternative`/`hidden` sense labelling ↔ rendering-policy choices (render layer in propstore architecture).
- External data-category registries (ISOcat) ↔ the "don't prescribe a fixed inventory" stance — compatible with propstore's non-commitment design principle.
- Multilingual reuse via shared `reference` ↔ one concept, many surface forms across languages; concept ≠ label.

This 2011 paper is theoretically grounded; the Cimiano 2016 OntoLex community report supersedes it for current RDF production URIs but is an engineering consolidation, not a theoretical exposition. Buitelaar 2011 (4pp workshop) is a much shorter sketch.

## Differentiation from Already-Collected Papers

- **vs Buitelaar 2011 (4pp workshop short paper, already in corpus):** The Buitelaar short paper is a brief positioning note. This McCrae 2011 ESWC full paper (15pp) is the actual canonical lemon specification: it (i) defines every core class and property of the model with examples; (ii) gives the Fig.1 UML class diagram; (iii) introduces lemon-LexInfo with ISOcat import and compositional OWL frames; (iv) provides three worked experiments (WordNet conversion, FOAF generation, merge). The Buitelaar paper does none of this at comparable detail.
- **vs Cimiano 2016 OntoLex community report (already in corpus):** The 2016 community report is the W3C-style consolidation that renames the vocabulary (e.g., `ontolex:` namespace), stabilises property names, integrates community feedback from 2011-2016, and is the production citation for tools today. This 2011 paper is the theoretically grounded original — it is where the *design rationale* for the core classes (open category inventory, non-finite senses, OWL-composed frames, LMF property renaming) is argued. For propstore's theoretical grounding layer, the 2011 paper is canonical; for propstore's serialisation-layer decisions (URIs, property names), the 2016 report is authoritative. They complement rather than supersede each other in theoretical terms.

## Open Questions

- [ ] How does lemon's `condition` on `LexicalSense` (with subproperties `propertyDomain`, `propertyRange`) relate to propstore's first-class `Condition` object on stances?
- [ ] Are the ISO data-category URIs (e.g., `isocat:DC-1298`) still dereferenceable in 2026, or have they migrated to successor registries? Affects whether lemon's literal URIs can be quoted directly in propstore knowledge/.
- [ ] Does propstore intend to import the lemon-LexInfo OWL frame compositions verbatim, or re-derive frames from Fillmore's FrameNet?
- [ ] Is the "LexicalEntry subclasses = Word, Phrase, Part" granularity sufficient, or does propstore need the LexInfo-extended axiomatic subclasses (Verb, NounPhrase, etc.) at the form-typing layer?

## Related Work Worth Reading (from the paper's references)

- [6] Cimiano, Buitelaar, McCrae, Sintek — **LexInfo: A Declarative Model for the Lexicon-Ontology Interface** (Web Semantics 9(1), 2011). Direct predecessor; the "v1" that this paper extends into lemon-LexInfo.
- [10] Francopoulo et al. — **LMF (Lexical Markup Framework)** (LREC 2006). Parent standard; lemon is positioned against it.
- [14] Kilgarriff — **I Don't Believe in Word Senses** (Computers and the Humanities 31(2), 1997). Grounds the non-finite/non-disjoint sense decision.
- [11] Gangemi, Guarino, Masolo, Oltramari — **Sweetening WordNet with DOLCE** (AI Magazine 24(3), 2003). Cited for the "WordNet's conceptual model is unsound from an ontological perspective" critique.
- [13] Kemps-Snijders, Windhouwer, Wittenburg, Wright — **ISOcat: Corralling data categories in the wild** (LREC 2008). The data-category registry that lemon-LexInfo imports from.
- [5] Chiarcos — **Grounding an Ontology of Linguistic Annotations in the Data Category Registry** (LREC 2010). OLiA paper.
- [8] Farrar, Langendoen — **Markup and the GOLD Ontology** (2003).
- [24] Van Assem, Gangemi, Schreiber — **Conversion of WordNet to a standard RDF/OWL representation** (LREC 2006). The RDF WordNet lemon converts from.
- [4] Buitelaar — **Ontology-based Semantic Lexicons: Mapping between Terms and Object Descriptions** (Ontology and the Lexicon, 2010) — already in propstore corpus as the 4pp Buitelaar 2011 relative.
- [16] Korhonen, Krymolowski, Briscoe — **A large subcategorization lexicon for NLP** (LREC 2006). COMLEX; source of the 163 frames.

## Collection Cross-References

### Conceptual Links (not citation-based)
- [A Component-Based Framework For Ontology Evolution](../Klein_2003_ComponentBasedFrameworkOntologyEvolution/notes.md) — Klein and Noy define a typed change-operation framework parametrized over Frames-style ontology components (class / slot / facet / instance) and argue that change information itself should be first-class structured data with the same substrate as the ontologies it describes. lemon supplies the propstore-era component decomposition (OntologyReference / LexicalEntry / LexicalForm / LexicalSense) that a Klein/Noy-style change ontology would target — `ClaimConceptLinkDeclaration` in propstore is exactly such a typed component-targeted change operation, but parametrized over lemon components rather than Frames components.
