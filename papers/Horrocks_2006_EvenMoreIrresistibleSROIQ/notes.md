---
title: "The Even More Irresistible SROIQ"
authors: "Ian Horrocks, Oliver Kutz, and Ulrike Sattler"
year: 2006
venue: "KR 2006"
pages: "452-457"
produced_by:
  skill: "paper-reader"
  timestamp: "2026-08-08"
---
# The Even More Irresistible SROIQ

## One-Sentence Summary

SROIQ makes relation properties meaningful as ontology-wide role axioms with model-theoretic semantics and a decidable reasoning procedure, not as free-standing declarations over an in-memory edge set.

## Relation Semantics

- SROIQ extends OWL-DL's underlying logic with disjoint, reflexive, irreflexive, and asymmetric roles, inverse roles, complex role inclusions, a universal role, self restrictions, and negative role assertions. (pp. 452-453)
- A knowledge base separates a role hierarchy and role assertions from concept and individual axioms, but all contribute to one interpretation. Relation properties therefore affect satisfiability, subsumption, and inferred role membership globally. (pp. 453-454)
- Complex role inclusions describe propagation across role chains. Transitivity and symmetry can be represented through role inclusions, while other characteristics require explicit role assertions or concept constructions. (pp. 452-454)
- A model interprets each role as a binary relation on a domain. Symmetry, asymmetry, reflexivity, irreflexivity, disjointness, inverse relationships, and chain inclusions constrain that interpretation. (pp. 453-454)

## Decidability and Ownership

- Expressiveness is constrained by regular role hierarchies and simple-role conditions. These restrictions are global properties of the ontology, not checks local to one assertion. (pp. 454-455)
- Cyclic dependencies among complex role inclusions can make reasoning undecidable. A production admission path must therefore validate the authored axiom system before accepting it. (pp. 454-455)
- The tableau procedure is proved sound, complete, and terminating for satisfiability and subsumption with respect to ABoxes, RBoxes, and TBoxes. Merely computing a local transitive or symmetric closure is not an implementation of the described capability. (pp. 455-457)

## Propstore Decision Relevance

- `RoleDefinition`, `RoleSignature`, and the relation-property assertion classes are not a latent SROIQ subsystem. They have no persisted RBox or ontology owner, no admission rule for regularity/simple roles, and no production reasoner.
- `RelationConceptRef`, `RoleBinding`, and `RoleBindingSet` remain useful typed values for identifying relation concepts and binding participants. Their continued use does not justify retaining unconsumed schema declarations.
- A future relation-entailment feature should begin with a generic authored ontology/axiom owner, a typed admission report, and an explicit reasoning/query consumer. It must not be recreated inside the first concrete relation family.
- The present test-only kernel should therefore be deleted rather than wired into unrelated argumentation, query, or storage paths.

## Limitations

- The paper gives classical monotonic model-theoretic semantics. It does not define defeasible relation assertions or ASPIC preference/defeat behavior. (pp. 453-457)
- It establishes a decidable logic and tableau algorithm, not a Propstore persistence schema or authoring workflow. (pp. 454-457)

## Collection Cross-References

### Already in Collection

- [OWL 2 Web Ontology Language Direct Semantics](../Motik_2012_OWL2DirectSemantics/notes.md) - standardizes the compatible model theory and inference problems.
- [Shapes Constraint Language (SHACL)](../Knublauch_2017_ShapesConstraintLanguageSHACL/notes.md) - supplies a separate validation architecture that must not be conflated with entailment.

### New Leads (Not Yet in Collection)

- Horrocks and Sattler (2004) - establishes decidability for SHIQ with complex role inclusions.
- Baader et al. (2007) - broader description-logic theory and implementation reference.

### Supersedes or Recontextualizes

- (none)

### Cited By (in Collection)

- [OWL 2 Web Ontology Language Direct Semantics](../Motik_2012_OWL2DirectSemantics/notes.md) - adopts SROIQ-compatible direct semantics.

### Conceptual Links (not citation-based)

- Propstore's argumentation papers define defeasible support and defeat, a different semantic owner from classical ontology entailment.
