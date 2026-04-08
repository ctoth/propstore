# Abstract

## Original Text (Verbatim)

In a decentralized knowledge representation system such as the Web of Data, it is common and indeed allowed for different knowledge graphs to provide multiple names used to denote the same thing, i.e., owl:sameAs statements are used to indicate equivalence between entity representations. The declarative nature of such identity statements can have wide-ranging effects in a global knowledge space like the Web of Data. Web surveys provide an extensive overview of the sameAs problem in the Web of Data, addressing identity link creation, the quality of identity in the Web of Data, detection of erroneous identity links, identity repair approaches, and alternative identity relations. An open discussion highlights the main weaknesses offered by solutions in the literature, and draws open challenges to be faced in the future.

---

## Our Interpretation

The paper addresses the fundamental problem of identity management in decentralized knowledge graphs: when multiple URIs refer to the same entity, the owl:sameAs predicate's formal semantics (full substitutability, transitivity) cause cascading errors because publishers use it loosely for contextual similarity. The survey catalogs five dimensions of the problem — creation, quality, detection, repair, and alternatives — finding that most existing approaches lack comprehensive evaluation. This is directly relevant to propstore's concept merging: identity should be a contextual, policy-driven decision at render time rather than a collapsed assertion in storage.
