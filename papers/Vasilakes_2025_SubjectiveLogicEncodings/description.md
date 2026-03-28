---
tags: [subjective-logic, uncertainty, annotation-disagreement, dirichlet, evidential-deep-learning]
---
Proposes Subjective Logic Encodings (SLEs), a framework for encoding annotator labels as Dirichlet distributions via SL opinions with separate dimensions for annotator confidence, reliability, and inter-annotator disagreement.
SLEs use cumulative belief fusion and trust discounting to aggregate annotations into training targets, then train neural networks via KL divergence loss on the resulting Dirichlet distributions.
Directly relevant to propstore's SL opinion algebra, Sensoy 2018 evidential mapping, and multi-source evidence aggregation pipeline.
