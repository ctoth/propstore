---
tags: [bayesian-networks, sensitivity-analysis, tensor-decomposition, uncertainty-quantification]
---
Proposes global variance-based sensitivity analysis for Bayesian network parameters using Sobol indices, replacing traditional one-at-a-time (OAT) methods that miss parameter interactions. The method encodes uncertainties as additional tensor network dimensions with low-rank tensor train decomposition, enabling exact Sobol index computation via tensor contraction; experiments on 8 benchmark BNs show OAT sensitivity values have Spearman correlations below 0.51 with the global indices. Tangentially relevant to propstore's probabilistic argumentation layer, where global SA could identify which argument/defeat probabilities actually drive extension outcomes.
