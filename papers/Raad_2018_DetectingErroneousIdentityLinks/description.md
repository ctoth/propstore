---
tags: [linked-data, identity, owl-sameas, semantic-web, network-metrics]
---
Defines a topology-only method for detecting erroneous `owl:sameAs` identity links by compacting reciprocal assertions, partitioning equality sets, applying Louvain community detection, and ranking each link by an error-degree score. Evaluates the method on over 558M LOD Cloud identity links, showing that low scores validate many true links while near-1 scores in large equality sets expose many related or unrelated terms miscast as identical. Directly relevant to propstore's identity and concept reconciliation work because it provides a scalable graph-derived quality signal for equivalence claims without prematurely collapsing all identity assertions.
