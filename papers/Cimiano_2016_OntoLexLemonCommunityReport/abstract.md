# Abstract

## Original Text (Verbatim)

This document describes the lexicon model for ontologies (*lemon*) as a main outcome of the work of the Ontology Lexicon (Ontolex) community group.

Ontologies are an important component of the Semantic Web but current ontology languages such as OWL and RDF(S) lack support for enriching ontologies with linguistic information, in particular with information concerning how ontology entities, i.e. properties, classes, individuals, etc. can be realized in natural language. The model described in this document aims to close this gap by providing a vocabulary that allows ontologies to be enriched with information about how the vocabulary elements described in them are realized linguistically, in particular in natural languages.

OWL and RDF(S) rely on the RDFS lable property to capture the relation between a vocabulary element and its (preferred) lexicalization in a given language. This lexicalization provides a lexical anchor that makes the class, property, individual etc. understandable to a human user. The use of a simple label for linguistic grounding as available in OWL and RDF(S) is far from being able to capture the necessary linguistic and lexical information that Natural Language Processing (NLP) applications working with a particular ontology need.

The aim of *lemon* is to provide rich linguistic grounding for ontologies. Rich linguistic grounding includes the representation of morphological and syntactic properties of lexical entries as well as the syntax-semantics interface, i.e. the meaning of these lexical entries with respect to an ontology or vocabulary.

---

## Our Interpretation

OntoLex-Lemon is the canonical W3C community report specifying how to ground an ontology in natural language: every lexical entry is connected to an ontology entity via a reified sense, and forms, concepts, and translations are represented as first-class RDF resources. It exists because `rdfs:label` is far too weak for any real NLP or lexicographic workflow — inflection, ambiguity, syntactic frames, and cross-lingual equivalence all need explicit vocabulary. For propstore this document is the implementation target: it fixes the IRIs, class axioms, and property characteristics that the concept registry and `form_utils.py` rewrite must conform to if they are to interoperate with any OntoLex-compliant lexical resource (BabelNet, WordNet-RDF, TermeNet, etc.).
