# Abstract

## Original Text (Verbatim)

It is generally recognized that the possibility of detecting contradictions and identifying their sources is an important feature of an intelligent system. Systems that are able to detect contradictions, identify their causes, or readjust their knowledge bases to remove the contradiction, called Belief Revision Systems, Truth Maintenance Systems, or Reason Maintenance Systems, have been studied by several researchers in Artificial Intelligence (AI).

In this paper, we present a logic suitable for supporting belief revision systems, discuss the properties that a belief revision system based on this logic will exhibit, and present a particular implementation of our model of a belief revision system.

The system we present differs from most of the systems developed so far in three respects: First, it is based on a logic that was developed to support belief revision systems. Second, it uses the rules of inference of the logic to automatically compute the dependencies among propositions rather than having to force the user to do this, as in many existing systems. Third, it was the first belief revision system whose implementation relies on the manipulation of sets of assumptions, not justifications.

---

## Our Interpretation

The paper addresses the problem of building belief revision systems that can automatically track propositional dependencies and detect contradictions without requiring the user to manually specify dependency information. Its key contribution is the SWM relevance logic and its associated MBR (Multiple Belief Reasoner) abstraction, which together provide a formal framework where the inference rules themselves compute origin sets (which hypotheses support a conclusion) and restriction sets (which hypothesis combinations are known to be inconsistent). This is directly relevant to the propstore project as it provides the theoretical foundation for assumption-based reasoning with automatic dependency tracking and contradiction-driven belief revision.
