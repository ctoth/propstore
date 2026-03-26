# Abstract

## Original Text (Paraphrased)

The paper studies approximate reasoning for structured argumentation, specifically ASPIC+, by sampling only a subset of all constructible arguments instead of building the full argument graph. It introduces two approaches: one that samples arguments independently and one that samples arguments relative to a query by following attacker links. Experiments on random, data-mined, and MaxSAT-derived benchmarks show large runtime reductions with only small losses in accuracy.

## Our Interpretation

The key contribution is not a new semantics, but a practical construction shortcut: approximate the argument graph first, then reason over the sampled subgraph. The dependent sampler is especially interesting because it preserves query relevance by expanding along attacker paths, making it a better fit for systems that need explainable but scalable reasoning.

