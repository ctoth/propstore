# Abstract

## Original Text (Verbatim)

Traditionally, the sensitivity analysis of a Bayesian network studies the impact of individually modifying the entries of its conditional probability tables in a one-at-a-time (OAT) fashion. However, this approach fails to give a comprehensive account of each inputs' relevance, since simultaneous perturbations in two or more parameters often entail higher-order effects that cannot be captured by an OAT analysis. We propose to conduct global variance-based sensitivity analysis instead, whereby n parameters are viewed as uncertain at once and their importance is assessed jointly. Our method works by encoding the uncertainties as n additional variables of the network. To prevent the curse of dimensionality while adding these dimensions, we use low-rank tensor decomposition to break down the new potentials into smaller factors. Last, we apply the method of Sobol to the resulting network to obtain n global sensitivity indices. Using a benchmark array of both expert-elicited and learned Bayesian networks, we demonstrate that the Sobol indices can significantly differ from the OAT indices, thus revealing the true influence of uncertain parameters and their interactions.

---

## Our Interpretation

This paper addresses the limitation of one-at-a-time sensitivity analysis in Bayesian networks by proposing global Sobol indices that capture parameter interactions. The key technical contribution is encoding parameter uncertainties as additional tensor network dimensions with bounded TT rank, enabling exact computation via tensor contraction. The results demonstrate that OAT methods can dramatically misidentify which parameters actually matter (Spearman correlation < 0.51 with Sobol indices), suggesting that any system relying on BN parameter sensitivity should consider global methods instead.
