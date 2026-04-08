---
tags: [linked-data, identity, owl-sameas, knowledge-graphs, semantic-web]
---
Presents sameAs.cc, the largest dataset and web service collecting 558M owl:sameAs identity statements from the Linked Open Data Cloud, computing their equivalence closure into 49M non-singleton identity sets via union-find, and analyzing the resulting identity landscape including power-law set size distributions and namespace-level linking patterns.
The largest identity set (177,794 members) conflates Albert Einstein with countries and the empty string, demonstrating that transitive closure of identity assertions propagates errors without quality filtering.
Directly relevant to propstore's concept reconciliation and non-commitment discipline: identity closure should be computed at render time, not storage time, to avoid premature collapse of disagreement.
