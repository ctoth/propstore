# Abstract

## Original Text (Verbatim)

This document defines the SHACL Shapes Constraint Language, a language for validating RDF graphs against a set of conditions. These conditions are provided as shapes and other constructs expressed in the form of an RDF graph. RDF graphs that are used in this manner are called "shapes graphs" in SHACL and the RDF graphs that are validated against a shapes graph are called "data graphs". As SHACL shape graphs are used to validate that data graphs satisfy a set of conditions they can also be viewed as a description of the data graphs that do satisfy these conditions. Such descriptions may be used for a variety of purposes beside validation, including user interface building, code generation and data integration.

---

## Our Interpretation

Validation is an explicit operation over two authored artifacts, a shapes graph and a data graph, producing a typed validation report. This architecture is distinct from ontology entailment and cannot be supplied by local relation-property declarations with no persisted shapes or validator consumer.
