# Abstract

## Original Text (Verbatim)

We describe an extension of the description logic underlying OWL-DL, SHOIN, with a number of expressive means that we believe will make it more useful in practice. Roughly speaking, we extend SHOIN with all expressive means that were suggested to us by ontology developers as useful additions to OWL-DL, and which, additionally, do not affect its decidability and practicability. We consider complex role inclusion axioms of the form R o S subsumed by R or S o R subsumed by R to express propagation of one property along another one, which have proven useful in medical terminologies. Furthermore, we extend SHOIN with reflexive, antisymmetric, and irreflexive roles, disjoint roles, a universal role, and constructs exists R.Self, allowing, for instance, the definition of concepts such as a "narcist". Finally, we consider negated role assertions in Aboxes and qualified number restrictions. The resulting logic is called SROIQ. We present a rather elegant tableau-based reasoning algorithm: it combines the use of automata to keep track of universal value restrictions with the techniques developed for SHOIQ. The logic SROIQ has been adopted as the logical basis for the next iteration of OWL, OWL 1.1.

---

## Our Interpretation

Relation characteristics such as transitivity, symmetry, disjointness, reflexivity, and inverse relationships are ontology axioms interpreted together with role, concept, and individual assertions. They are not isolated flags whose meaning can be supplied by local set utilities. Their usefulness depends on an authored ontology representation and a sound, complete reasoning procedure subject to global decidability restrictions.
