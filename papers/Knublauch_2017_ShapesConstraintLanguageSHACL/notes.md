---
title: "Shapes Constraint Language (SHACL)"
authors: "Holger Knublauch and Dimitris Kontokostas"
year: 2017
venue: "W3C Recommendation"
pages: "1-76"
produced_by:
  skill: "paper-reader"
  timestamp: "2026-08-08"
---
# Shapes Constraint Language (SHACL)

## One-Sentence Summary

SHACL validates an authored data graph against a separate authored shapes graph and returns structured conformance results, keeping validation distinct from ontology entailment and query derivation.

## Validation Architecture

- SHACL defines validation completely in terms of a shapes graph, a data graph, a processor, focus-node selection, and a validation report. Shapes are RDF nodes, not transient method calls. (pp. 1-9)
- Node shapes and property shapes target nodes explicitly. Property shapes own well-formed property paths, including inverse, sequence, alternative, zero-or-more, one-or-more, and zero-or-one paths. (pp. 7-13)
- The validation process does not modify the shapes or data graphs and is expected to be idempotent. Ill-formed shapes cause failure rather than an inferred fallback meaning. (pp. 13-16)
- Recursive shape semantics are deliberately left undefined. A production owner must make unsupported or ambiguous structures explicit rather than silently interpreting them. (pp. 13-14)

## Typed Results and Constraints

- A validation report states `sh:conforms` and contains validation results. Results identify the focus node, result path, value, source shape, source constraint component, severity, messages, and optional details. (pp. 15-18)
- Core constraints cover value type, cardinality, value ranges, string characteristics, property-pair comparisons, logical composition, nested shapes, qualified counts, closed shapes, required values, and membership. (pp. 19-51)
- Property-pair constraints such as equality and disjointness compare values found along authored paths. They validate observed graph shape; they do not infer symmetric or transitive relation closure. (pp. 36-39)
- Closed shapes make a deliberately closed-world validation choice by reporting properties not enumerated by the shape. This differs from OWL's open-world model theory. (pp. 49-50)

## Extension and Query Boundaries

- SHACL-SPARQL expresses custom constraints as persisted SELECT or ASK queries with specified pre-bound variables and result mappings. It is still a validation mechanism with a report contract. (pp. 52-61)
- Custom constraint components have authored parameter declarations, validators, well-formedness rules, and explicit node-shape/property-shape applicability. Reusable behavior is owned by the component, not copied into its first caller. (pp. 56-60)
- SPARQL execution is restricted for safe pre-binding, and processors must fail on prohibited query forms. This reinforces the need for an admission boundary. (pp. 60-61)
- SHACL may request an entailment regime, but entailment is an input preparation choice, not supplied by SHACL Core itself. The data graph must contain the relevant ontology axioms or inferred triples for targeting and validation. (pp. 8-10)

## Propstore Decision Relevance

- `RelationPropertyKind`, `RelationPropertyAssertion`, and `RelationPropertySet` do not constitute a SHACL-style validation subsystem. There is no persisted shapes owner, target-selection representation, validation request, processor, or typed report.
- Turning those classes into admission checks inside a concrete relation caller would embed a generic validation mechanism in the wrong owner and still omit authored schema persistence and reporting.
- A future relation-validation feature should start with generic persisted schema/shapes artifacts, typed validation requests and reports, well-formedness checks, and an explicit production admission or audit consumer.
- Classical entailment remains ontology/reasoner-owned; defeasible relation assertions remain argumentation-owned; query derivation remains query/reasoning-owned. The current test kernel should not collapse those roles.
- #212 should delete the unconsumed kernel and retain only the live typed relation concept and binding values.

## Limitations

- SHACL validates RDF graphs. Propstore would need a deliberate mapping from its semantic artifacts to a graph or an equivalent native shapes representation. (pp. 1-13)
- SHACL Core does not define classical ontology entailment, and SHACL-SPARQL inherits SPARQL security considerations. (pp. 8-10, 52-61, 75)

## Collection Cross-References

### Already in Collection

- [OWL 2 Web Ontology Language Direct Semantics](../Motik_2012_OWL2DirectSemantics/notes.md) - distinguishes model-theoretic entailment from validation.
- [The Even More Irresistible SROIQ](../Horrocks_2006_EvenMoreIrresistibleSROIQ/notes.md) - supplies the relation-axiom semantics and reasoning constraints SHACL does not replace.

### New Leads (Not Yet in Collection)

- Steyskal and Coyle (2016) - SHACL use cases and requirements, useful before designing a native validation owner.
- Harris and Seaborne (2013) - SPARQL 1.1 query semantics and security surface underlying SHACL-SPARQL.

### Supersedes or Recontextualizes

- (none)

### Cited By (in Collection)

- (none found)

### Conceptual Links (not citation-based)

- Propstore's typed admission/report APIs are architecturally compatible with SHACL's separation of authored constraints, immutable inputs, processor, and report.
