# Abstract

## Original Text (Verbatim)

Support for ontology evolution becomes extremely important in distributed development and use of ontologies. Information about change can be represented in many different ways. We describe these different representations and propose a framework that integrates them. We show how different representations in the framework are related by describing some techniques and heuristics that supplement information in one representation with information from other representations. We present an ontology of change operations, which is the kernel of our framework.

---

## Our Interpretation

Klein and Noy frame ontology evolution as a problem of *integrating* three complementary representations of change rather than choosing one — a structural diff, a typed log of edits, and a conceptual narrative — and provide cross-derivation heuristics so missing information in one representation can be reconstructed from another. The kernel of the framework is an explicit *ontology of change operations* with a Basic / Complex stratification, where every basic operation targets exactly one ontology component (class, slot, facet, instance) and every modify operation is reversible by construction. The paper is directly relevant to propstore because its component-based, typed, role-bearing change-operation discipline is precisely what `ClaimConceptLinkDeclaration` aims to be in the lemon-shaped concept layer.
