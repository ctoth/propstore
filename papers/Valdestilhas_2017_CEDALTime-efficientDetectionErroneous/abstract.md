# Abstract

## Original Text (Verbatim)

More than 500 million facts on the Linked Data Web are statements across knowledge bases. These links are of crucial importance for the Linked Data Web as they make a large number of tasks possible, including cross-ontology, question answering and federated queries. However, a large number of these links are erroneous and can thus lead to these applications producing absurd results. We present a time-efficient and complete approach for the detection of erroneous links for properties that are transitive. To this end, we make use of the semantics of URIs on the Data Web and combine it with an efficient graph partitioning algorithm. We then apply our algorithm to the LinkLion repository and show that we can analyze 19,200,114 links in 4.6 minutes. Our results show that at least 13% of the owl:sameAs links we considered are erroneous. In addition, our analysis of the provenance of links allows discovering agents and knowledge bases that commonly display poor linking. Our algorithm can be easily executed in a parallel and on a GPU. We show that these implementations are up to two orders of magnitude faster than classical reasoners and a non-parallel implementation.

---

## Our Interpretation

The paper treats erroneous `owl:sameAs` links as a scalable graph consistency problem: if transitive identity puts distinct same-dataset URIs in one connected component, the identity path or source data is suspect. Its main value is that it detects those candidates through union-find partitioning and provenance-preserving output rather than full closure materialization or automatic repair.
