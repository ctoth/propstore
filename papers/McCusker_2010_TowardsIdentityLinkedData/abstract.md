# Abstract

## Original Text (Verbatim)

Many Linked Data applications have come to rely on owl:sameAs for linking datasets. However, the current semantics for owl:sameAs assert that identity entails isomorphism, or that if a=b, then all statements of a and b are shared by both. This becomes problematic when dealing with provenance, context, and imperfect representations, all of which are endemic issues in Linked Data. Merging provenance can be problematic or even catastrophic in biomedical applications that demand access to provenance information. We use examples in biospecimen management, experimental metadata representations, and personal identity in Friend-of-a-Friend (FOAF) to demonstrate some of the problems that can arise with the use of owl:sameAs. We also show that the existence of an isomorphic owl:sameAs can be inconsistent with current expectations in a number of our use cases. We present a solution that allows the extraction of isomorphic statements without requiring their direct assertion. We also introduce a set of identity properties that can be extended for domain-specific purposes while maintaining clarity of definition within each property.

---

## Our Interpretation

The paper argues that Linked Data needs identity relations weaker and more specific than owl:sameAs, because full substitutability can merge provenance, context, and representation-specific assertions that users need to keep distinct. Its Identity Ontology gives a compact design space for identity-like links and lets systems recover isomorphic behavior only when a domain-specific identity property warrants it.
