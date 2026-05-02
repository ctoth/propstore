---
tags: [linked-data, identity, owl-sameas, graph-algorithms, data-quality]
---
Presents CEDAL, a union-find graph-partitioning algorithm for detecting erroneous transitive RDF identity links by finding clusters with distinct resources from the same dataset. Shows the method processes 19.2M LinkLion owl:sameAs links in 4.6 minutes, finds at least 13% erroneous links, and preserves path/provenance evidence rather than automatically deleting links. Relevant to propstore because it gives a scalable, provenance-preserving check for when identity closure would wrongly collapse source-local resources.
