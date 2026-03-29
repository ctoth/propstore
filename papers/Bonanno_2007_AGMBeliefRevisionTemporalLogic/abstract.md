# Abstract

## Original Text (Verbatim)

Since belief revision deals with the interaction of belief and information over time, branching-time temporal logic seems a natural setting for a theory of belief change. We propose two extensions of a modal logic that, besides the next-time temporal operator, contains a belief operator and an information operator. The first logic is shown to provide an axiomatic characterization of the first six postulates of the AGM theory of belief revision, while the second, stronger, logic provides an axiomatic characterization of the full set of AGM postulates.

---

## Our Interpretation

The paper bridges the gap between static belief logic (modal/Kripke) and dynamic belief change (AGM theory) by embedding both in a single branching-time temporal logic. The key result is that AGM revision postulates are exactly captured by frame conditions on temporal belief revision structures, with the Qualitative Bayes Rule as the semantic core. This is directly relevant to propstore's question of whether AGM revision can be mapped onto git's commit DAG: the answer is no without modification, because the framework requires Backward Uniqueness (linear backward history), which merge commits violate.
