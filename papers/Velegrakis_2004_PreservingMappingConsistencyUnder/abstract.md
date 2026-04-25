# Abstract

## Original Text (Verbatim)

In dynamic environments like the Web, data sources may change not only their data but also their schemas, their semantics, and their query capabilities. When a mapping is left inconsistent by a schema change, it has to be detected and updated. We present a novel framework and a tool (ToMAS) for automatically adapting (rewriting) mappings as schemas evolve. Our approach considers not only local changes to a schema but also changes that may affect and transform many components of a schema. Our algorithm detects mappings affected by structural or constraint changes and generates all the rewritings that are consistent with the semantics of the changed schemas. Our approach explicitly models mapping choices made by a user and maintains these choices, whenever possible, as the schemas and mappings evolve. When there is more than one candidate rewriting, the algorithm may rank them based on how close they are to the semantics of the existing mappings.

---

## Our Interpretation

The paper formalizes when a mapping (a typed nested-relational query bridging a source schema to a target schema) becomes inconsistent under a schema edit and gives an incremental rewriting algorithm decomposed over a small operator set (rename, copy, move, create, delete element; add/remove constraint). Consistency reduces to membership in the set of maximal logical associations of the post-change schemas, computed via a chase over key and foreign-key constraints. Critically for propstore, the algorithm preserves user-chosen mappings and ranks alternative rewritings by similarity to the prior batch — exactly the cross-projection consistency discipline a concept-model migration in propstore needs.
