---
title: "Global Sensitivity Analysis of Uncertain Parameters in Bayesian Networks"
authors: "Rafael Ballester-Ripoll, Manuele Leonelli"
year: 2024
venue: "Preprint submitted to Elsevier (arXiv:2406.05764)"
doi_url: "https://doi.org/10.48550/arXiv.2406.05764"
produced_by:
  agent: "Claude Opus 4.6 (1M context)"
  skill: "paper-reader"
  timestamp: "2026-03-28T22:45:27Z"
---
# Global Sensitivity Analysis of Uncertain Parameters in Bayesian Networks

## One-Sentence Summary
Proposes a global variance-based (Sobol) sensitivity analysis method for Bayesian networks that encodes parameter uncertainties as additional network dimensions and uses tensor train decomposition to keep computation tractable, revealing interaction effects that one-at-a-time (OAT) methods miss entirely.

## Problem Addressed
Traditional BN sensitivity analysis modifies CPT entries one-at-a-time (OAT), computing the gradient of an output probability w.r.t. each parameter independently. This fails to capture higher-order interaction effects between simultaneously uncertain parameters, leading to both false positives (parameters that appear important in OAT but are globally irrelevant) and false negatives (parameters whose importance only manifests through interactions). *(p.1-3)*

## Key Contributions
- A method for global variance-based sensitivity analysis of BN parameters using Sobol indices, replacing OAT sensitivity values *(p.1)*
- Encoding of parameter uncertainties as additional dimensions of the BN's tensor network representation *(p.14-15)*
- Use of tensor train (TT) decomposition to prevent exponential blow-up when adding uncertainty dimensions *(p.10-11, 15-16)*
- Proof that the augmented potential has TT rank at most sqrt(|Phi|) + P (Lemma 1) *(p.15)*
- Demonstration on 8 benchmark BNs that Sobol indices significantly differ from OAT sensitivity values (Spearman correlations of only 0.507 and 0.461) *(p.24-27)*

## Methodology
The method proceeds in four steps *(p.11-12)*:
1. Moralize the BN and convert to a tensor network (TN) representation
2. For each CPT with uncertain entries, encode each uncertainty as an additional parent (new dimension), adjusting other entries via proportional covariation
3. Compactly encode the augmented CPTs using TT decomposition to avoid exponential blow-up
4. Apply the method of Sobol via exact tensor contraction (variable elimination) to extract global sensitivity indices

## Key Equations / Statistical Models

### BN Factorization
$$
P(\mathbf{Y} = \mathbf{y}) = \prod_{i=1}^{p} P(Y_i = y_i | \mathbf{Y}_{\Pi_i} = \mathbf{y}_{\Pi_i})
$$
Where: $\mathbf{Y} = (Y_1, \ldots, Y_p)$ is the random vector, $\Pi_i$ denotes the parents of $Y_i$.
*(p.5)*

### Sensitivity Function
$$
f_O(\boldsymbol{\theta}) = P(Y_O = y_O)
$$
Where: $Y_O$ is the output variable of interest, $y_O$ is a chosen level, $\boldsymbol{\theta}$ is the vector of conditional probabilities. Under proportional covariation, $f$ is a ratio of two linear functions: $f(\theta_i) = \frac{c_0 + c_i \theta_i}{d_0 + d_i \theta_i}$.
*(p.6-7)*

### OAT Sensitivity Value
$$
|f'_O(\theta_i^0)|
$$
Where: $\theta_i^0$ is the original (baseline) value of parameter $\theta_i$. This is the gradient at the original value.
*(p.7)*

### Proportional Covariation
$$
\theta_j(\theta_i) = \frac{1 - \theta_i}{1 - \theta_i^0} \theta_j^0
$$
Where: $\theta_j$ is a co-varied parameter from the same conditional distribution as $\theta_i$. This preserves the sum-to-one constraint.
*(p.7)*

### Sobol Variance Component (First-Order Index)
$$
S_i := \frac{\text{Var}_i\left[\text{E}_{\setminus i}[f]\right]}{\text{Var}[f]}
$$
Where: $\text{E}_{\setminus i}$ is the expectation w.r.t. all parameters except $\theta_i$, $\text{Var}_i$ is the variance w.r.t. $\theta_i$. Quantifies how much the average model output changes as $\theta_i$ is varied.
*(p.10, Eq. 1)*

### Sobol Total Index
$$
S_i^T := \frac{\text{E}_{\setminus i}\left[\text{Var}_i[f]\right]}{\text{Var}[f]}
$$
Where: roles of expectation and variance are swapped vs. $S_i$. Captures additive effects plus all interaction terms. $S_i \leq S_i^T$ always; equality iff $\theta_i$ separable from $f$.
*(p.10)*

### Tensor Train Decomposition
$$
\mathcal{T}(i_1, \ldots, i_N) \approx G_1(i_1) \cdots G_N(i_N)
$$
Where: $G_1(i_1)$ is a row vector, $G_2(i_2), \ldots, G_{N-1}(i_{N-1})$ are matrices, $G_N(i_N)$ is a column vector. The dimensions $r_1, \ldots, r_{N-1}$ are called bond dimensions or TT ranks.
*(p.11, Eq. 2)*

### Extended TT with Learned Matrices
$$
\mathcal{T}(i_1, \ldots, i_N) \approx (G_1 \times_2 \mathbf{U}_1)(i_1) \cdots (G_N \times_2 \mathbf{U}_N)(i_N)
$$
Where: $\times_2$ is the tensor-times-matrix product along the second mode, $\mathbf{U}_k$ are learned matrices providing compression for continuous variables.
*(p.11, Eq. 4)*

### Augmented Potential
$$
\Phi'(\mathbf{X} = \mathbf{x}, Y = k, \mathbf{Y}_\Pi = \mathbf{y}_\Pi) := \begin{cases} \frac{1 - x_p}{1 - \Phi(y_p, \mathbf{y}_\Pi)} \Phi(k, \mathbf{y}_\Pi) & \text{if } \mathbf{y}_\Pi = \mathbf{y}_p^{\text{U}} \text{ for some } p \in \{1,\ldots,P\} \\ \Phi(k, \mathbf{y}_\Pi) & \text{otherwise} \end{cases}
$$
Where: $x_p \in [0,1]$ are the new uncertainty dimensions, $P$ is the number of uncertain entries, $\mathbf{y}_p^{\text{U}}$ are the parent indices of the uncertain entries.
*(p.15)*

### Decomposition of Augmented Potential (Eq. 5)
$$
\mathcal{T}_p(\mathbf{x}, y, \mathbf{y}_\Pi) := \begin{cases} \frac{1 - x_p}{1 - \Phi(y_p, \mathbf{y}_\Pi)} \Phi(k, \mathbf{y}_\Pi) - \Phi(k, \mathbf{y}_\Pi) & \text{if } \mathbf{y}_\Pi = \mathbf{y}_p^{\text{U}} \\ 0 & \text{otherwise} \end{cases}
$$
Where: $\Phi' := \Phi + \mathcal{T}_1 + \ldots + \mathcal{T}_P$. Each $\mathcal{T}_p$ has TT rank 1.
*(p.16, Eq. 5)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Uncertainty variance | $\sigma^2$ | - | 0.02 | - | 21 | Fixed variance for Beta distributions of uncertain params |
| Beta distribution alpha | $\alpha$ | - | - | - | 21 | $\alpha = \theta_i^0 \lambda$ |
| Beta distribution beta | $\beta$ | - | - | - | 21 | $\beta = (1-\theta_i^0)\lambda$ |
| Lambda | $\lambda$ | - | - | - | 21 | $\lambda := \frac{\theta_i^0 - \sigma^2 - (\theta_i^0)^2}{\sigma^2}$ |
| Discretization bins | $I$ | - | - | - | 16 | Number of bins for each $x_p$ in [0,1] |
| Bond dimension / TT rank | $r$ | - | - | - | 11 | Controls approximation quality; can be increased to reduce error $\epsilon$ |
| Compression error | $\epsilon$ | - | - | - | 11 | Error from TT approximation; zero when tensor is exactly low-rank |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| OAT vs Variance component correlation | Spearman | 0.507 | - | - | COVID-MEASURES, target P(COUNTRYFIN=Agree) | 24 |
| OAT vs Total index correlation | Spearman | 0.461 | - | - | COVID-MEASURES, target P(COUNTRYFIN=Agree) | 24 |
| Max interaction term | $S^T - S$ | 0.15 | - | - | Across benchmark networks (hepar2) | 27 |
| Max OAT-Sobol discrepancy | $\|S^T - f'\|$ | 0.45 | - | - | Across benchmark networks (hepar2) | 27-28 |
| 31st parameter OAT sensitivity | $\|f'_O(\theta_{31})\|$ | 0.168 | - | - | COVID-MEASURES, 2nd highest OAT | 24 |
| 31st parameter Sobol indices | $S, S^T$ | ~$10^{-4}$ | - | - | COVID-MEASURES, insignificant globally | 24 |
| Top parameter OAT sensitivity | $\|f'_O(\theta_1)\|$ | 0.207 | - | - | COVID-MEASURES | 24 |
| Top parameter Sobol total index | $S_1^T$ | ~0.6 | - | - | COVID-MEASURES, 3x larger than OAT | 24-25 |
| Augmented TN size (COVID-MEASURES) | N. params | 12,783 | - | - | After encoding 55 uncertainties (vs millions without TT) | 23 |

## Methods & Implementation Details
- BN moralization: remove arrow directions, marry parents, creating MRF with clique potentials *(p.12-13)*
- MRF-to-TN duality: MRF nodes become TN edges, MRF cliques become TN nodes (tensors = potentials) *(p.12-13)*
- Uncertain parameter selection heuristic: (1) select target $P(Y_O = y_O)$, (2) compute all OAT sensitivity values, (3) for each CPT select rows with non-zero sensitivity, (4) mark parameter with highest sensitivity per row, (5) assign Beta distribution with mean $\theta_i^0$ and variance $\sigma^2 = 0.02$ *(p.19-21)*
- Constraint: cannot have multiple uncertain entries for the same parent configuration (sum-to-1 constraint introduces correlation, Sobol method requires independence) *(p.29)*
- For binary variables this is not a problem since $P(\text{yes}) = 1 - P(\text{no})$ *(p.29)*
- Software: cotengra library (Gray and Kourtis, 2021) for TN contraction with AUTO-HQ heuristic for elimination ordering; quimb (Gray, 2018) for tensor manipulation; PyTorch and YODO for sensitivity values *(p.21)*
- Variable elimination (= tensor contraction) used for exact inference; finding optimal elimination order is NP-hard *(p.21)*

## Figures of Interest
- **Fig 1 (p.5-6):** Simple 3-node BN (Y1, Y2, Y3) with CPTs showing the running example
- **Fig 2 (p.7):** One-way sensitivity functions showing limited individual effect of parameters
- **Fig 3 (p.8-9):** Two-way sensitivity surface showing strong interaction effect between P(Y1=yes) and P(Y2=yes)
- **Fig 4 (p.13-14):** ASIA network as BN, MRF, and tensor network (dual graph)
- **Fig 5 (p.17-18):** Encoding four uncertainties into a 3D CPT via TT decomposition, showing tensor network diagrams
- **Fig 6 (p.19-20):** ASIA network after encoding 10 uncertainties (left) and squared network for Sobol computation (right)
- **Fig 7 (p.22):** COVID-MEASURES BN structure (15 nodes, 34 edges, 588 parameters)
- **Fig 8 (p.23):** TN for COVID-MEASURES after encoding 55 uncertain parameters (Kamada-Kawai layout)
- **Fig 9 (p.24-25):** Log-scale comparison of sensitivity value, variance component, and total index for top 40 parameters — shows dramatic ranking differences
- **Fig 10 (p.26-27):** P(INFO=Radio) target showing OAT spike for parameter that Sobol reveals as irrelevant

## Results Summary
The method reveals that OAT sensitivity analysis systematically misidentifies parameter importance in BNs. Key findings *(p.24-28)*:
- Parameters ranked highly by OAT can have near-zero Sobol indices (e.g., 31st parameter has OAT value 0.168 but Sobol indices ~$10^{-4}$)
- Conversely, top Sobol parameters can have total indices 3x their OAT sensitivity value
- Sobol indices drop much faster than sensitivity values across parameter rankings, suggesting OAT overestimates the importance of most BN entries
- Interaction terms ($S^T - S$) can reach ~0.15, meaning substantial parameter influence comes through joint effects
- The gap $|S^T - f'|$ can reach ~0.45, showing dramatic disagreement between local and global measures
- Method scales to networks with 70 nodes and thousands of parameters, running in seconds
- TT decomposition keeps the augmented network tractable (e.g., 12,783 parameters instead of millions for 55 uncertainties)

## Limitations
- Cannot model uncertainties for multiple child state probabilities given the same parent configuration, because the sum-to-1 constraint introduces correlations between CPT entries, and the Sobol method requires independent parameters *(p.29)*
- For binary variables this is not a problem since $P(\text{yes}) = 1 - P(\text{no})$ *(p.29)*
- Restricted to exact tensor contraction, sufficient for networks up to 50-100 nodes after augmentation *(p.29)*
- Uncertain parameter selection is heuristic-based (could alternatively be expert-elicited) *(p.21)*
- Discretization of continuous uncertainty variables into $I$ bins introduces approximation *(p.16)*

## Arguments Against Prior Work
- OAT sensitivity analysis provides only a partial and sometimes wrong picture of parameter influence, since it cannot capture interaction effects between parameters *(p.7-9)*
- Multi-way sensitivity analyses have been studied but are challenging: sensitivity functions cannot be visualized in high dimensions, number of parameter groups grows exponentially, and associated measures are hard to interpret *(p.9)*
- Li and Mahadevan (2017) and Zio et al. (2022) implemented Monte Carlo-based global sensitivity for BNs, but their approach requires very large MC simulations, making it infeasible for moderate-size networks, and the implementation is not freely available *(p.3)*
- Ballester-Ripoll and Leonelli (2022a) developed exact methods but lacked the tensor network encoding for handling many uncertainties simultaneously *(p.3-4)*

## Design Rationale
- Chose Sobol indices over other global SA measures because they are the most widely used framework and have clear interpretation (variance decomposition) *(p.9-10)*
- Used proportional covariation as the covariation scheme because it is the gold standard with strong theoretical properties (Laskey, 1995; Chan and Darwiche, 2005) *(p.7)*
- Represented BNs as tensor networks (via MRF duality) to leverage TT decomposition and tensor contraction libraries *(p.12-13)*
- Used exact tensor contraction rather than Monte Carlo sampling to make Sobol estimation exact (no sampling noise) *(p.18)*
- TT format chosen because the augmented potential can be proven to have bounded TT rank (Lemma 1: at most $\sqrt{|\Phi|} + P$) *(p.15)*

## Testable Properties
- $S_i \leq S_i^T$ always (total index includes interaction terms) *(p.10)*
- $S_i = S_i^T$ iff $f(\boldsymbol{\theta}) = g(\theta_i) + h(\boldsymbol{\theta}_{\setminus i})$, i.e., parameter separable from $f$ in additive fashion *(p.10)*
- TT rank of augmented potential $\Phi'$ is at most $\sqrt{|\Phi|} + P$ where $|\Phi|$ is the number of elements and $P$ is the number of uncertainties *(p.15)*
- Each perturbation tensor $\mathcal{T}_p$ has TT rank exactly 1 *(p.16)*
- The augmented potential $\Phi'$ preserves the sum-to-1 property of the original CPT for all values of $x_p \in [0,1]$ *(p.16)*
- OAT sensitivity values have Spearman correlation < 0.51 with Sobol variance components on the COVID-MEASURES BN *(p.24)*

## Relevance to Project
This paper is tangentially relevant to propstore. It addresses sensitivity analysis of Bayesian networks, which is a different domain from the argumentation frameworks (Dung, ASPIC+, bipolar AFs) that form propstore's core. However, there are two potential connection points:
1. **Parameter uncertainty in probabilistic argumentation:** propstore's PrAF (probabilistic argumentation framework) layer uses probabilities on arguments and defeats. If those probabilities come from BN-learned or expert-elicited sources, global SA could identify which probabilities actually matter for extension outcomes, rather than assuming all are equally important.
2. **Tensor decomposition for inference:** The TN/TT approach to exact inference on augmented networks could be relevant if propstore ever needs to scale probabilistic argumentation to larger networks, since variable elimination in BNs is equivalent to tensor contraction.

## Open Questions
- [ ] How does the discretization bin count $I$ affect accuracy of Sobol indices?
- [ ] Could approximate tensor contraction (SVD rank truncation) extend the method to larger networks (>100 nodes)?
- [ ] Could higher-order Sobol indices, closed/upper indices, or Shapley values provide more actionable decomposition?
- [ ] Is there a way to handle correlated uncertainties (multiple entries per parent config)?

## Related Work Worth Reading
- Ballester-Ripoll, R., Leonelli, M., 2022a. Computing Sobol indices in probabilistic graphical models. Reliability Engineering & System Safety 225, 108573. — The foundational algorithm for Sobol index computation in TNs used by this paper.
- Saltelli, A. et al., 2019. Why so many published sensitivity analyses are false. Environmental Modelling & Software 114, 29-39. — Systematic critique of OAT sensitivity analysis practices.
- Sobol, I.M., 1990. Sensitivity estimates for nonlinear mathematical models. Mathematical Models 2, 112-118. — Original Sobol indices paper.
- Oseledets, I.V., 2011. Tensor-train decomposition. SIAM Journal on Scientific Computing 33, 2295-2317. — Foundation for the TT format used throughout.
- Gray, J., Chan, G.K.L., 2024. Hyperoptimized approximate contraction of tensor networks with arbitrary geometry. Physical Reviews X 14, 011009. — Approximate contraction for scaling to larger networks.

## Collection Cross-References

### Already in Collection
- [[Coupé_2002_PropertiesSensitivityAnalysisBayesian]] — cited as Coupe et al. (2000, 2002) for foundational properties of sensitivity analysis in BNs; this paper's OAT sensitivity function $f(\theta_i)$ is the ratio-of-linear-functions form that Coupe et al. proved

### New Leads (Not Yet in Collection)
- Ballester-Ripoll & Leonelli (2022a) — "Computing Sobol indices in probabilistic graphical models" — foundational algorithm for exact Sobol index computation in tensor networks
- Saltelli et al. (2019) — "Why so many published sensitivity analyses are false" — systematic critique of OAT sensitivity analysis practices
- Oseledets (2011) — "Tensor-train decomposition" — mathematical foundation for the TT format
- Sobol (1990) — "Sensitivity estimates for nonlinear mathematical models" — original Sobol indices paper

### Conceptual Links (not citation-based)
- [[Hunter_2021_ProbabilisticArgumentationSurvey]] — both deal with uncertainty in probabilistic graphical structures; Ballester-Ripoll's global SA could identify which argument/defeat probabilities in a PrAF actually drive extension outcomes, complementing Hunter's constellation approach
- [[Popescu_2024_ProbabilisticArgumentationConstellation]] — both use exact inference over combinatorial structures (tensor contraction vs tree-decomposition DP); the TT decomposition approach to avoiding exponential blow-up parallels Popescu's use of treewidth-bounded DP for PrAF computation
- [[Li_2011_ProbabilisticArgumentationFrameworks]] — Li's PrAF assigns independent probabilities to arguments/defeats analogous to Ballester-Ripoll's independent Beta-distributed parameter uncertainties; global SA could identify which PrAF probabilities actually matter for acceptance probability
