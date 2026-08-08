---
title: "OWL 2 Web Ontology Language Direct Semantics (Second Edition)"
authors: "Boris Motik, Peter F. Patel-Schneider, and Bernardo Cuenca Grau"
year: 2012
venue: "W3C Recommendation"
pages: "1-15"
produced_by:
  skill: "paper-reader"
  timestamp: "2026-08-08"
---
# OWL 2 Web Ontology Language Direct Semantics

## One-Sentence Summary

OWL 2 interprets object-property characteristics as ontology axioms over binary relations and defines named reasoning operations over the ontology's axiom closure.

## Typed Ontology Vocabulary

- The vocabulary separates classes, object properties, data properties, individuals, datatypes, literals, and facets. Object-property expressions are named properties or inverses. (pp. 4-6)
- An interpretation maps each object property to a binary relation over the object domain. Class and individual meanings share that interpretation, so property axioms cannot be evaluated as an isolated fixture. (pp. 5-7)
- An ontology includes an axiom closure accounting for imports. The ontology is satisfied only when every axiom in that closure is satisfied. (pp. 3-4, 12)

## Object-Property Axioms

- The direct semantics covers subproperty and property-chain axioms, equivalent and disjoint properties, inverse properties, domains, ranges, functionality, inverse functionality, reflexivity, irreflexivity, symmetry, asymmetry, and transitivity. Each constrains the interpreted binary relation. (pp. 8-10)
- Restrictions involving cardinality and self expressions require simple object properties. This is a global structural condition on the ontology and is not represented by a local property flag. (pp. 7, 14)
- Assertions about individuals are distinct from property-schema axioms: positive and negative object-property assertions state whether a pair belongs to an interpreted relation. (pp. 11-12)

## Explicit Consumers

- The specification defines ontology consistency, entailment, equivalence, equisatisfiability, class satisfiability, subsumption, instance checking, and Boolean conjunctive query answering. (pp. 12-14)
- These operations make the semantic purpose explicit. A production feature must name which operation it offers and provide the ontology to which that operation applies. (pp. 12-14)
- Query answering is defined using entailment of assertion sets; it is not a synonym for graph traversal or local closure. (pp. 13-14)

## Propstore Decision Relevance

- The deleted candidates in #212 do not have an ontology document, import/axiom closure, structural admission checks, or a reasoner-backed production operation. Wiring them into an arbitrary caller would invent semantics rather than integrate existing work.
- A future classical relation subsystem should own typed, persisted property axioms and expose typed consistency, entailment, or query requests and reports. It is a generic ontology capability, not a relation-family convenience.
- OWL entailment is separate from SHACL validation and from defeasible ASPIC assertions. Propstore should keep those semantic roles distinct instead of using one relation-property set for all three.
- Deleting the current test-only kernel is therefore the architecture-preserving decision.

## Limitations

- Direct Semantics assumes OWL 2's classical, monotonic model theory. It does not define validation against closed-world application requirements. (pp. 3-14)
- It does not define defeasible priority, attack, or defeat. Those remain argumentation-layer concerns. (pp. 12-14)

## Collection Cross-References

### Already in Collection

- [The Even More Irresistible SROIQ](../Horrocks_2006_EvenMoreIrresistibleSROIQ/notes.md) - provides the description-logic basis and decidability constraints.
- [Shapes Constraint Language (SHACL)](../Knublauch_2017_ShapesConstraintLanguageSHACL/notes.md) - defines graph validation as a separate operation with different artifacts and reports.

### New Leads (Not Yet in Collection)

- Motik, Patel-Schneider, and Parsia (2012) - OWL 2 structural specification and functional-style syntax, needed when designing a persisted authoring representation.
- Baader et al. (2007) - description-logic handbook covering theory and implementations.

### Supersedes or Recontextualizes

- [The Even More Irresistible SROIQ](../Horrocks_2006_EvenMoreIrresistibleSROIQ/notes.md) - standardizes a compatible Web ontology semantics and explicit inference vocabulary.

### Cited By (in Collection)

- (none found)

### Conceptual Links (not citation-based)

- Propstore's typed request/report pattern is a suitable shape for future consistency, entailment, and query consumers, but no such owner exists today.
