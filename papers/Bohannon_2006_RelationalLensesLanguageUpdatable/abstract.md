# Abstract

## Original Text (Verbatim)

We propose a novel approach to the classical view update problem. The view update problem arises from the fact that modifications to a database view may not correspond uniquely to modifications on the underlying database; we need a means of determining an "update policy" that guides how view updates are reflected in the database. Our approach is to define a bi-directional query language, in which every expression can be read both (from left to right) as a view definition and (from right to left) as an update policy. We treat in detail the case of relational lenses, a basic combinator language for transforming relations together with their integrity constraints (functional dependencies). The relational lenses include selection, projection, and join. We show that the resulting lenses obey the laws of bi-directional programming and we define a static type system enforcing those laws.

---

## Our Interpretation

The paper recasts the view-update problem as a language-design problem: rather than asking which arbitrary view-updates can be back-propagated, the authors define a small combinator language (σ, π, ⋈ as relational lenses) where every expression is simultaneously a view definition and an update policy, statically typed by a functional-dependency set in tree form. Well-typedness guarantees the bidirectional lens laws GetPut and PutGet, giving a formal round-trip / information-preservation account. For propstore, this is the foundational specification of when a migration between two storage representations is allowed to collapse structure without losing information.
