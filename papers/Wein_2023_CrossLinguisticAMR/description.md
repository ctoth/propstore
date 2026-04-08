---
tags: [semantic-representation, cross-lingual, amr, graph-comparison, evaluation-metrics]
---
This paper systematically assesses whether Abstract Meaning Representation (AMR), originally designed for English, faithfully captures meaning across languages, finding that source language significantly impacts AMR graph structure.
The authors develop a divergence annotation schema classifying cross-lingual AMR differences by type (focus, argument, non-core role) and cause (semantic, annotation, syntactic), and show that AMR-based Smatch metrics correlate more strongly with human similarity judgments than string-level metrics like BERTscore.
For propstore, the work demonstrates that structured semantic representations capture finer-grained meaning differences than surface text comparison, supporting the use of graph-based comparison for claim similarity and the preservation of representational divergences rather than collapsing them.
