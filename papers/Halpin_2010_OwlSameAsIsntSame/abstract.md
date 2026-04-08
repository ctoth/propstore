# Abstract

## Original Text (Verbatim)

In Linked Data, the use of owl:sameAs is ubiquitous in interlinking data-sets. There is however, ongoing discussion about its use, and potential misuse, particularly with regards to interactions with inference. In fact, owl:sameAs can be viewed as encoding only one point on a scale of similarity, one that is often too strong for many of its current uses. We describe how referentially opaque contexts that do not allow inference exist, and then outline some varieties of referentially-opaque alternatives to owl:sameAs. Finally, we report on an empirical experiment over randomly selected owl:sameAs statements from the Web of data. This theoretical apparatus and experiment shed light upon how owl:sameAs is being used (and misused) on the Web of data.

---

## Our Interpretation

The paper addresses the fundamental problem that owl:sameAs, the standard identity link in Linked Data, commits to full Leibnizian substitutivity but is routinely used for weaker relationships like similarity or topical relatedness. The authors propose a graded Similarity Ontology with eight properties of varying logical strength and validate the problem empirically, finding that roughly half of owl:sameAs statements in the wild are not true identity. This is directly relevant to any system that must represent identity claims without prematurely collapsing disagreements.
