# Abstract

## Original Text (Verbatim)

The owl:sameAs predicate is an essential ingredient of the Semantic Web architecture. It allows parties to independently mint identifiers, while at the same time ensuring that these parties are able to understand each other's data. An online resource that collects all owl:sameAs statements in the Linked Open Data Cloud has therefore considerable potential value, both as a reference for the same entity as well as analytical value (it reveals important aspects of the connectivity of the LOD Cloud).

This paper presents sameAs.cc: the largest dataset of identity statements has been gathered from the LOD Cloud to date. We describe our approach for crawling, indexing, and calculating the equivalence closure over this dataset. The dataset is published online, as well as a web service that can be queried by both humans and machines.

---

## Our Interpretation

The paper addresses the lack of a comprehensive, centralized owl:sameAs identity service for the entire Linked Open Data Cloud. By collecting 558M explicit identity statements and computing their transitive closure (yielding 49M non-singleton identity sets), the authors reveal both the connectivity structure of the LOD Cloud and the data quality problems inherent in unchecked identity propagation. For propstore, this demonstrates why concept identity closure must be deferred to render time rather than baked into storage.
