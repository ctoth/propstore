---
tags: [ontology-evolution, change-management, migration-framework, semantic-web]
---
Klein and Noy define a component-based framework for ontology evolution that integrates three complementary representations of change — a minimal structural transformation set, a typed log of change operations from an explicit change ontology, and a high-level conceptual description — together with heuristics that derive each representation from the others.
The change ontology partitions operations along Basic (atomic, single-component, complete) versus Complex (composed, semantically loaded, open-ended) axes, with every basic operation parametrized by exactly one component (class, slot, facet, instance) and every modify operation carrying both old and new values for reversibility.
For propstore this is the closest paper match for what `ClaimConceptLinkDeclaration` should be — typed, named, role-bearing operations on lemon-shaped concept components — and it ratifies the existing source-storage / proposal split as a basic-versus-complex layering.
