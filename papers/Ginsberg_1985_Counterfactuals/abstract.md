# Abstract

## Original Text (Verbatim)

Counterfactuals are a form of commonsense non-monotonic inference that has been of long-term interest to philosophers. In this paper, we begin by describing some of the impact counterfactuals can be exported to have in artificial intelligence, and by reviewing briefly some of the philosophical conclusions which have been drawn about them. Philosophers have noted that the content of any particular counterfactual is in part context-dependent; we present a formal description of counterfactuals that is formally identical to the "possible worlds" interpretation due to David Lewis and which allows us to encode this context-dependent information clearly in the choice of a sublanguage of the logical language in which we are working. Finally, we examine the application of our ideas in the domain of automated diagnosis of hardware faults.

---

## Our Interpretation

Ginsberg addresses the problem of formalizing counterfactual reasoning -- statements about what would be true if something false were true -- for use in AI systems. The key finding is that by using three-valued truth functions (true/false/unknown) with closure operations and encoding context dependence through sublanguage selection, counterfactuals can be formalized in a way provably equivalent to Lewis's philosophical possible worlds semantics while remaining implementable. This is relevant to the propstore because it provides the theoretical bridge between assumption-based truth maintenance (ATMS-style reasoning about what holds under different assumption sets) and counterfactual/hypothetical reasoning needed for diagnosis and planning.
