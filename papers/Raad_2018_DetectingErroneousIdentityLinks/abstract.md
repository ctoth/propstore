# Abstract

## Original Text (Verbatim)

In the absence of a central naming authority on the Semantic Web, it is common for different datasets to refer to the same thing by different IRIs. Whenever multiple names are used to denote the same thing, owl:sameAs statements are needed in order to link the data and foster reuse. Studies that date back as far as 2009, have observed that the owl:sameAs property is sometimes used incorrectly. In this paper, we show how network metrics such as the community structure of the owl:sameAs graph can be used in order to detect such possibly erroneous statements. One benefit of the here presented approach is that it can be applied to the network of owl:sameAs links itself, and does not rely on any additional knowledge. In order to illustrate its ability to scale, the approach is evaluated on the largest collection of identity links to date, containing over 558M owl:sameAs links scraped from the LOD Cloud.

---

## Our Interpretation

The paper treats `owl:sameAs` quality as a graph-topology problem: suspicious links are weak or sparse bridges inside the identity-link graph. It is directly relevant to identity-claim evaluation because it supplies a scalable score that can be computed without descriptions, schemas, trusted-source metadata, or entity-resolution features.
