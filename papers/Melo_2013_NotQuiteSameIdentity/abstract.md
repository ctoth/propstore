# Abstract

## Original Text (Verbatim)

Linked Data is based on the idea that information from different sources can flexibly be connected to enable novel applications that individual datasets do not support on their own. This hinges upon the existence of links between datasets that would otherwise be isolated. The most notable form, sameAs links, are intended to express that two identifiers are equivalent in all respects. Unfortunately, many existing ones do not reflect such genuine identity. This study provides a novel method to analyse this phenomenon, based on a thorough theoretical analysis, as well as a novel graph-based method to resolve such issues to some extent. Our experiments on a representative Web-scale set of sameAs links from the Web of Data show that our method can identify and remove hundreds of thousands of constraint violations.

---

## Our Interpretation

The paper addresses the widespread misuse of owl:sameAs in Linked Data, where links intended to assert strict identity are instead used for approximate similarity or relatedness. De Melo formalizes the detection and repair of these erroneous identity links as a minimum multicut problem, proves it NP-hard, and provides polynomial-time approximation algorithms that scale to millions of URIs. This is relevant to any system managing concept identity across multiple sources, particularly for detecting when merges violate uniqueness constraints.
