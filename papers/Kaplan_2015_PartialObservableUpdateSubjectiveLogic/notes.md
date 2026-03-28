---
title: "Partial observable update for subjective logic and its application for trust estimation"
authors: "L. Kaplan, M. Sensoy, S. Chakraborty, G. de Mel"
year: 2015
venue: "Information Fusion 26:66-83"
doi_url: "https://doi.org/10.1016/j.inffus.2015.01.005"
---

# Partial Observable Update for Subjective Logic and Its Application for Trust Estimation

## One-Sentence Summary
Extends Subjective Logic to incorporate belief updates from partially observable evidence via likelihood functions, deriving a Dirichlet moment-matching algorithm that generalizes SL's fully-visible evidence updates and applies it to trust estimation. *(p.66)*

## Problem Addressed
Standard SL (Josang 2001) assumes each observation directly reveals which of the K mutually exclusive attribute states occurred — equivalent to rolling a die and seeing the result. In practice, the true state is often hidden and only a noisy measurement is available (e.g., sensor readings, classifier outputs, reported opinions). The paper addresses how to update SL opinions when evidence is only statistically related to the hidden state through a likelihood function. *(pp.66-67)*

The prior conference version (Kaplan et al. 2012) contained an error: the Dirichlet strength was forced to increase monotonically, preventing parameters from decreasing and causing uncertainty to shrink too fast. This paper corrects that error. *(p.73)*

## Key Contributions
- Formal extension of SL to partial observations via likelihood vectors $l_k^{(t)} = f(x | z = k)$ *(p.71, Eq. 21)*
- Algorithm 1: Partial Observable Update — computes updated opinion from prior opinion and T partial observations using method of moments to fit a Dirichlet approximation *(p.72, Algorithm 1)*
- Three computation methods for the moment integrals (calcint): *(pp.72-73)*
  - Attribute-based recursion: $O(K^{T+1})$ *(Algorithm 2)*
  - Observation-based recursion: $O(K^2 T!)$ *(Algorithm 3)*
  - Grid-based numerical integration: $O(TK^2 D^K)$ *(Eq. 31)*
- Sequential update (T=1 at a time) as practical approximation with negligible performance loss *(pp.73-74, Eqs. 32-33)*
- Five formal properties of the partial observable update *(pp.71-72, 74-75)*
- Trust estimation application using likelihood ratios derived from comparing reported vs. observed opinions *(pp.76-78)*
- Correction of the monotonic update error from Kaplan et al. 2012 *(p.73)*

## Methodology

### Partial Observable Update Derivation

Starting from a prior Dirichlet $f_b(\mathbf{p} | \boldsymbol{\alpha})$ with parameters related to SL opinion via: *(p.70, Eq. 10)*
$$\alpha_k = \frac{W b_k}{u} + W a_k$$

where $W$ is the non-informative prior weight, $b_k$ is belief, $u$ is uncertainty, $a_k$ is base rate.

Given T partial observations with likelihood vectors $\mathbf{l}^{(1)}, \ldots, \mathbf{l}^{(T)}$, the posterior is: *(p.71, Eq. 26)*
$$f(\mathbf{p} | \boldsymbol{\alpha}, X_T) \propto \prod_{t=1}^{T} \left( \sum_{k=1}^{K} l_k^{(t)} p_k \right) f_b(\mathbf{p} | \boldsymbol{\alpha})$$

This posterior is NOT a Dirichlet in general — it is a weighted mixture of Dirichlets. The method of moments is used to fit a single Dirichlet by matching marginal means and second moments. *(pp.71-72)*

The updated Dirichlet strength $S^+$ is computed by least-squares fit of second moments: *(p.72, Eq. 29)*
$$S^+ = \frac{\sum_{k=1}^{K} (m_k - v_k) m_k (1 - m_k)}{\sum_{k=1}^{K} (v_k - m_k^2) m_k (1 - m_k)}$$

### Naive Update (What NOT to Do)

A naive approach treats the likelihood as a fractional observation, incrementing $\alpha_k$ by $l_k / \sum_i l_i$. This is WRONG — it ignores the nonlinear interaction between the likelihood and the prior, producing biased estimates. The naive update always decreases uncertainty, even when the observation is completely vacuous ($l_k$ all equal). *(pp.71-72)*

### Sequential vs. Batch Update

For T=1 (sequential), the moments simplify to closed-form expressions (Eqs. 32-33). Simulations show sequential updating achieves nearly identical performance to batch updating with dramatically lower computational cost. *(pp.73-74)*

## Key Properties

### Property 1: Dirichlet Expected Product
For a Dirichlet with parameters $\boldsymbol{\alpha}$ and strength $S$: *(p.70)*
$$E_{\boldsymbol{\alpha}}[p_j \cdot g(\mathbf{p})] = \frac{\alpha_j}{S} E_{\boldsymbol{\alpha} + \mathbf{e}_j}[g(\mathbf{p})]$$

This is the key identity enabling recursive computation of the posterior moments.

### Property 2: Vacuous Observation Invariance
When all likelihoods are equal ($l_k = c$ for all $k$), the observation is vacuous and the updated opinion equals the prior opinion. *(p.71)*

### Property 3: Uncertainty Bounds
After T partial observations, the updated uncertainty satisfies: *(p.72)*
$$\frac{W}{S + T} \leq u^+ \leq u$$

The lower bound is achieved only when all observations are fully visible. The upper bound (no change) occurs only for vacuous observations.

### Property 4: Parameter Decrease
For a single partial observation (T=1), at least one Dirichlet parameter must decrease (unless the observation is vacuous or fully visible). Specifically, the parameter corresponding to the attribute with the smallest likelihood value will not increase. *(p.75)*

### Property 5: Noncentral Moment Bounds
The updated noncentral second moments satisfy: *(p.72)*
$$v_k^+ \leq v_k$$

Second moments never increase after a partial update.

## Trust Estimation Application

The paper applies partial observable updates to trust estimation in multi-agent systems. *(Section 7, pp.76-78)*

Setup: A trustor agent $A_0$ collects opinions about propositions from reporting agents $A_1, \ldots, A_N$. Some agents may manipulate their reported opinions. The trustor also directly observes some propositions.

The key insight is that comparing a reporter's opinion with the trustor's own observation yields a likelihood for the reporter being trustworthy vs. untrustworthy: *(pp.77-78, Eqs. 40-42)*

$$l_1^{(i)} = f(\omega_i | \text{trustworthy}) = B([\alpha_i^{(0)} + \alpha_i^{(i)}]) / [B(\alpha_i^{(0)}) B(\alpha_i^{(i)})]$$

where $\alpha_i^{(0)}$ and $\alpha_i^{(i)}$ are the Dirichlet parameters from the trustor's and reporter's opinions respectively.

The likelihood ratio $\Lambda_i = l_1 / l_2$ determines whether evidence favors trustworthy or untrustworthy behavior.

## Simulation Results

### Toy Problem (K=3 attributes)
- 300 partial observations, 1000 Monte Carlo runs *(p.78)*
- Partial observable update converges to ground truth probabilities
- Naive update produces biased estimates
- Monotonic update (Kaplan 2012) converges much slower due to artificially suppressed uncertainty
- Sequential update performs nearly as well as batch with much lower computation *(p.79)*

### Trust Estimation
- 5 agents, 500 propositions, varying manipulation probabilities *(pp.79-80)*
- Likelihood-based update converges to ground truth trustworthiness
- Outperforms thresholding baseline and TRAVOS binning method *(p.80)*
- Uncertainty from likelihood updates accurately reflects estimation confidence *(p.80)*

## Relation to Existing SL Operations

The partial observable update is a form of SL abduction where: *(p.82)*
- The partial observation $x$ is the consequent
- The hidden observation $z$ is the antecedent
- The likelihoods $f(x | z = i)$ are the conditionals

This differs from standard SL abduction (Josang 2008) where the antecedent is a proposition rather than a discrete observation. The paper's update is the special case where likelihood uncertainty is zero. *(p.82)*

## Implementation Relevance for Propstore

**High relevance.** This paper extends the SL opinion algebra (Josang 2001, already implemented in propstore) to handle a fundamental real-world case: when evidence is noisy or indirect. Key implementation implications:

1. **Evidence from classifiers/LLMs**: When propstore uses LLM outputs as evidence for claims, these are partial observations — the LLM's confidence scores map naturally to likelihood vectors. The partial observable update is the principled way to incorporate such evidence.

2. **Calibration bridge**: The existing calibration pipeline (Guo et al. 2017) produces calibrated probabilities that could serve as likelihood functions for partial observable updates, creating a clean integration path.

3. **Trust estimation**: The trust application directly applies to propstore's source reliability modeling — comparing what a source reports vs. what is independently observed.

4. **Sequential update is sufficient**: The T=1 sequential update (Eqs. 32-33) provides a practical, closed-form implementation with negligible quality loss.

5. **Corrects prior error**: The monotonic update bug from Kaplan 2012 is a cautionary tale — forcing parameters to only increase causes uncertainty to shrink too fast, violating the epistemic honesty principle.

## New Leads
- Kaplan et al. 2012 — "Fusion of classifiers: a subjective logic perspective" — conference precursor with the monotonic bug [ref 23]
- Oren, Norman, Preece 2007 — "Subjective logic and arguing with evidence" — SL in argumentation [ref 29]
- Sensoy et al. 2013 (TRIBE) — "Trust revision for information based on evidence" — applies SL to trust revision [ref 31/49]
- Josang 2008 — "Conditional reasoning with subjective logic" — SL abduction/deduction [ref 19]
- Josang & McAnally 2004 — "Multiplication and comultiplication of beliefs" — extended SL operators [ref 40]
- Muller & Schweitzer 2013 — "On beta models with trust chains" — trust chain modeling [ref 50]
- Kaplan et al. 2013 — "Reasoning under uncertainty: variations of subjective logic deduction" [ref 45]
- Josang & Sambo 2014 — "Inverting conditional opinions in subjective logic" [ref 48]
