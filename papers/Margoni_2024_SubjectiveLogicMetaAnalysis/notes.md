---
title: "Subjective logic as a complementary tool to meta-analysis to explicitly address second-order uncertainty in research findings: A case from infant studies"
authors: "Francesco Margoni, Neil Walkinshaw"
year: 2024
venue: "Infant Behavior and Development"
doi_url: "https://doi.org/10.1016/j.infbeh.2024.101978"
---

# Subjective logic as a complementary tool to meta-analysis to explicitly address second-order uncertainty in research findings

## One-Sentence Summary
Demonstrates how Josang's subjective logic can encode individual empirical findings as subjective opinions (belief, disbelief, uncertainty) and fuse them via Weighted Belief Fusion to produce aggregate assessments that explicitly represent second-order uncertainty — applied to infant prosociality meta-analysis data.

## Problem Addressed
Traditional meta-analysis produces point estimates and confidence intervals, but these do not explicitly represent *second-order uncertainty* — uncertainty about the uncertainty itself. Multiple factors (sample size, replication status, design quality, publication bias, experimenter bias) affect confidence in findings but are collapsed into a single pooled effect size. Subjective logic provides a formal framework where each finding's evidence strength is transparently encoded and uncertainty from multiple sources is explicitly preserved through aggregation. *(p.1-2)*

## Key Contributions
- Introduces subjective logic as a complementary tool to classical meta-analysis for empirical research synthesis *(p.1)*
- Provides a step-by-step method for encoding empirical findings as binomial subjective opinions *(p.6-8)*
- Demonstrates the Weighted Belief Fusion (WBF) operator for aggregating multiple opinions *(p.4-5)*
- Shows how to incorporate sources of second-order uncertainty (replication status, sample size, CI width, peer review, "same source" penalty) as modifiers of the uncertainty component *(p.6-8)*
- Applies the full pipeline to 67 findings from the Margoni & Surian (2018) infant prosociality meta-analysis *(p.5-10)*
- Visualizes fused opinions as barycentric triangles and beta distributions *(p.9-12)*
- Demonstrates that the approach can reveal heterogeneity masked by traditional meta-analysis *(p.10-12)*

## Study Design (empirical papers)
- **Type:** Methodological demonstration applied to existing meta-analysis data
- **Population:** 67 findings from 45 studies on infant social evaluation (prosocial agent preference), from the Margoni & Surian (2018) meta-analysis *(p.5)*
- **Intervention(s):** N/A — this is a re-analysis demonstrating a new method
- **Comparator(s):** Traditional meta-analysis pooled effect size
- **Primary endpoint(s):** Fused subjective opinion (belief, disbelief, uncertainty) about whether infants prefer prosocial agents *(p.5)*
- **Secondary endpoint(s):** Subgroup-level fused opinions (by age group, by mission group) *(p.10-12)*
- **Follow-up:** N/A

## Methodology
1. Each empirical finding is encoded as a binomial subjective opinion omega_x = (b_x, d_x, u_x, a_x) *(p.3)*
2. The base rate a_x is set to 0.5 (non-informative prior) *(p.3-4)*
3. Beta distributions parameterize the opinion via alpha and beta derived from evidence counts *(p.4)*
4. Multiple sources of second-order uncertainty are applied as multiplicative factors on the uncertainty component *(p.6-8)*
5. Opinions are fused using the Weighted Belief Fusion (WBF) operator *(p.4-5)*
6. Results are visualized via barycentric triangle plots and beta distribution plots *(p.9-12)*

## Key Equations / Statistical Models

### Binomial Subjective Opinion (Josang 2016)

$$
\omega_x = (b_x, d_x, u_x, a_x)
$$
Where: $b_x$ = belief, $d_x$ = disbelief, $u_x$ = uncertainty, $a_x$ = base rate (prior probability). Constraint: $b_x + d_x + u_x = 1$, with $b_x, d_x, u_x \geq 0$ and $0 \leq a_x \leq 1$.
*(p.3)*

### Projected Probability

$$
P(x) = b_x + a_x \cdot u_x
$$
Where: $P(x)$ is the projected probability (expectation). For $\omega_x = (0.40, 0.20, 0.40, 0.90)$: $P(x) = 0.40 + 0.90 \times 0.40 = 0.76$.
*(p.4)*

### Beta Distribution (for opinion visualization)

$$
f(x; \alpha, \beta) = \frac{1}{B(\alpha, \beta)} x^{\alpha - 1} (1-x)^{\beta - 1}, \quad 0 < x < 1
$$
Where: $\alpha > 0$, $\beta > 0$, and $B(\alpha, \beta)$ is the beta function. Opinions map to beta parameters via $\alpha = \frac{b_x^W}{u_x} + a_x \cdot W$ and $\beta = \frac{d_x^W}{u_x} + (1 - a_x) \cdot W$ where $W$ is the non-informative prior weight (set to $W = 2$ for non-informative prior, i.e., $a_x = 0.5$).
*(p.4)*

### Weighted Belief Fusion (WBF) Operator

$$
\text{WBF}(\omega_1^A, \omega_2^A, \ldots, \omega_N^A) = \hat{\omega}^A
$$
The WBF of $N$ opinions $\omega_i^A = (b_i, d_i, u_i, a_i)$ for a finite set of agents. The WBF fuses opinions by giving specific weights to each opinion as a function of its relative confidence or certainty.
*(p.4-5)*

### Confidence Interval to Belief/Disbelief Mapping

For a finding with effect size and confidence interval:
- If CI lower bound > 0 (significant positive effect): $b_x = 1 - u_x$, $d_x = 0$ *(p.6)*
- If CI upper bound < 0 (significant negative effect): $b_x = 0$, $d_x = 1 - u_x$ *(p.6)*
- If CI crosses zero (non-significant): $b_x = 0$, $d_x = 0$, $u_x = 1$ *(implied, p.6)*

### Uncertainty Calculation from Sample Size

$$
u_x = 1 - \left(\frac{n}{n_{\max}}\right)
$$
Where: $n$ is the study sample size, $n_{\max}$ is the maximum possible sample size (set contextually; here $n_{\max} = 162$ from the largest study). This ensures $u_x$ inversely relates to sample size.
*(p.7)*

### TripTop Strategy for CI-based Uncertainty

$$
u_x = \text{median}(0, P_r, 1) = \text{median}\left(0, \frac{|CI_U - CI_L|}{R}, 1\right)
$$
Where: $P_r$ is the proportion of the CI width relative to range $R$. The authors use $R = 8$ (which is the estimate range for the $d$ effect size in their domain). When $u$ from this formula is low, the CI is narrow relative to the total range.
*(p.7)*

### "Same Source" Penalty Factor

When multiple findings come from the same lab:
$$
u_{\text{adjusted}} = \text{median}(0, u_{\text{base}} + \Delta, 1)
$$
Where $\Delta$ penalizes findings from labs that contributed multiple studies. The paper notes this could capture "researcher degrees of freedom" or systematic biases. Not formally defined as a single equation but described as a factor. *(p.7-8)*

### Peer Review Factor

$$
\text{If not peer reviewed: } u_x \leftarrow \text{median}(0, u_x + 0.1, 1)
$$
A fixed penalty of 0.1 added to uncertainty for non-peer-reviewed findings. *(p.7)*

### Replication Factor

$$
\text{factor}_{\text{rep}} = \begin{cases} 1.0 & \text{if independently replicated} \\ 1.44 & \text{if not replicated (Camerer et al. baseline)} \end{cases}
$$
The replication penalty is derived from Camerer et al. (2018): 65% of findings replicated, so unreplicated findings get uncertainty multiplied by $1/0.65 \approx 1.44$ (adjusted via domain-specific base rates). Actually stated as: if replicated $u = u$; if not replicated, $u$ is scaled up. The authors use $P_{\text{replicability}} = 0.50$ for this field. *(p.7)*

### Final Uncertainty Assembly

The final uncertainty score is computed by adding the base uncertainty (from CI or sample size) plus penalty terms for: (1) lack of peer review, (2) replication status, (3) "same source" bias. The result is clipped to $[0, 1]$. *(p.8)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Base rate (prior) | $a_x$ | - | 0.5 | [0, 1] | p.3-4 | Non-informative prior; W=2 ensures uniform beta |
| Non-informative prior weight | $W$ | - | 2 | - | p.4 | Josang (2016) convention |
| Max sample size | $n_{\max}$ | participants | 162 | - | p.7 | Largest study in the meta-analysis dataset |
| CI range denominator | $R$ | effect size units | 8 | - | p.7 | Range of effect size $d$ in domain |
| Peer review penalty | $\Delta_{\text{pr}}$ | - | 0.1 | - | p.7 | Added to $u$ if not peer reviewed |
| Replicability base rate | $P_{\text{rep}}$ | proportion | 0.50 | - | p.7 | Estimated replication rate for infant studies |
| Replication factor (unreplicated) | - | multiplier | ~1.44 | - | p.7 | Derived from 1/P_rep when P_rep=0.65 (Camerer) |
| Number of findings | $N$ | count | 67 | - | p.5 | From 45 studies in Margoni & Surian (2018) |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Fused opinion (all findings) | projected probability | 0.703 | - | - | All 67 findings, WBF | p.9 |
| Fused opinion (all findings) | belief | ~0.5 | - | - | All 67 findings | p.9 |
| Fused opinion (all findings) | uncertainty | ~0.4 | - | - | All 67 findings | p.9 |
| Fused opinion (young infants) | projected probability | lower than old | - | - | Age < 12 months | p.10-11 |
| Fused opinion (old infants) | projected probability | higher than young | - | - | Age >= 12 months | p.10-11 |
| Fused opinion (Hamlin lab) | uncertainty | high | - | - | Single lab subgroup | p.10 |
| Meta-analysis effect size (original) | Cohen's d | 0.39 | [0.20, 0.57] | - | Margoni & Surian 2018 | p.5 |

## Methods & Implementation Details
- Subjective opinions encoded from each finding's statistical results (effect size, CI, sample size) *(p.6)*
- The TripTop strategy (Josang 2016) used as one option for mapping CI width to uncertainty *(p.7)*
- Sample-size-based uncertainty: $u = 1 - n/n_{\max}$ where $n_{\max} = 162$ (largest study) *(p.7)*
- The CI-based approach uses the CI width relative to the plausible range $R = 8$ *(p.7)*
- "Same source" penalty addresses studies from same lab contributing multiple findings *(p.7-8)*
- Peer review adds fixed 0.1 uncertainty penalty if study is not peer reviewed *(p.7)*
- Replication factor adjusts uncertainty based on whether finding has been independently replicated *(p.7)*
- WBF operator fuses all individual opinions into aggregate opinion *(p.4-5)*
- All data, analysis code, and supplementary materials on OSF (https://osf.io/) *(p.15)*
- Beta distributions visualize individual opinions as probability distributions *(p.9-10)*
- Barycentric triangle plots show opinions in (belief, disbelief, uncertainty) space *(p.4, 9-12)*
- The approach produces one fused opinion per subgroup, enabling comparison of belief/disbelief/uncertainty across groups *(p.10-12)*

## Figures of Interest
- **Fig 1 (p.3):** Barycentric triangle visualization of subjective opinion space. Panel (a) shows basic geometry; panels (b)-(f) show special cases: certain opinion, vacuous opinion, dogmatic opinion, partially uncertain opinion
- **Fig 2 (p.4):** Barycentric triangle with all 67 findings from Margoni & Surian (2018) plotted; color legend in Fig 3
- **Fig 3 (p.9):** Subjective opinions visualized as beta distributions for all findings. Numbers = study indices. Shows variation in distribution shapes (peaked vs flat)
- **Fig 4 (p.10):** Barycentric triangle and beta distributions of the *fused* subjective opinion from all findings. Shows the aggregate opinion with uncertainty component
- **Fig 5 (p.11):** Fused opinions for Young and Old age groups — both barycentric triangles and beta distributions
- **Fig 6 (p.12):** Fused opinions from findings in Margoni & Surian meta-analysis by age groups — shows how heterogeneity across subgroups is visible in the opinion space
- **Fig 7 (p.13):** Fused opinions from findings by Research and Help Mission groups — further subgroup decomposition

## Results Summary
- The fused subjective opinion for all 67 findings yields projected probability ~0.703 — supporting the hypothesis that infants prefer prosocial agents, but with substantial residual uncertainty (~0.4) *(p.9)*
- Beta distribution of fused opinion is "somewhat peaked" but not sharply so, indicating moderate evidence *(p.9-10)*
- Subgroup analysis by age reveals that older infants (>=12 months) show stronger preference (lower uncertainty, higher belief) than younger infants *(p.10-11)*
- Findings from a single lab (Hamlin lab) show high uncertainty when viewed separately *(p.10)*
- The approach makes heterogeneity across studies immediately visible in the barycentric triangle — studies cluster in different regions indicating genuine disagreement *(p.9-10)*
- Different factor combinations (CI width, sample size, replication, peer review, same-source) visibly shift the fused opinion's uncertainty component *(p.8-10)*

## Limitations
- The authors note the approach is *complementary* to meta-analysis, not a replacement *(p.12-13)*
- The mapping from effect sizes/CIs to opinions involves choices (e.g., R=8 for CI range, n_max=162) that are domain-specific and subjective *(p.7)*
- The same-source penalty and replication factor require domain knowledge to calibrate *(p.7-8)*
- Subjective logic is flexible but this means researchers must justify their parameter choices transparently *(p.12-13)*
- The case study focuses on a binary question (prefer prosocial vs antisocial agent), which maps naturally to binomial opinions; non-binary outcomes would require multinomial opinions *(p.3)*
- The paper acknowledges that establishing prior probability is flexible and could be adjusted in ways that change the result *(p.9)*
- The approach does not capture all sources of uncertainty — e.g., measurement error within studies, publication bias corrections *(p.12-13)*

## Arguments Against Prior Work
- Traditional meta-analysis collapses uncertainty into confidence intervals, which do not distinguish first-order from second-order uncertainty *(p.1-2)*
- Bayesian meta-analysis can accommodate some uncertainty but does not provide the transparent, per-factor decomposition that subjective logic offers *(p.2)*
- Prediction intervals in meta-analysis capture heterogeneity but do not attribute uncertainty to specific factors *(p.1-2)*
- Replication crisis literature (OSC 2015, Camerer et al. 2016, 2018) demonstrates that point estimates from individual studies are unreliable, motivating explicit uncertainty modeling *(p.2)*

## Design Rationale
- Binomial opinions chosen because the research question is binary (infants prefer prosocial: yes/no) *(p.3)*
- WBF chosen over other fusion operators because it weights by certainty — more certain opinions contribute more *(p.4-5)*
- Base rate $a_x = 0.5$ chosen as non-informative (maximum ignorance) prior *(p.3-4)*
- $W = 2$ ensures beta distribution is uniform when opinion is vacuous *(p.4)*
- Multiple uncertainty factors are additive/multiplicative rather than combined into a single score, preserving transparency about which factors contribute to total uncertainty *(p.6-8)*
- Sample size uncertainty uses $n_{\max}$ from the dataset rather than an arbitrary threshold, grounding the scale in the actual evidence base *(p.7)*

## Testable Properties
- For any opinion $\omega = (b, d, u, a)$: $b + d + u = 1$, $b \geq 0$, $d \geq 0$, $u \geq 0$, $0 \leq a \leq 1$ *(p.3)*
- Projected probability $P(x) = b + a \cdot u$ must equal the expectation of the corresponding beta distribution *(p.4)*
- WBF of opinions with higher certainty (lower $u$) should dominate the fused result *(p.4-5)*
- A vacuous opinion $\omega = (0, 0, 1, a)$ should not shift the fused opinion (acts as identity element for WBF) *(p.3)*
- Increasing sample size $n$ must decrease uncertainty $u$ when using $u = 1 - n/n_{\max}$ *(p.7)*
- Adding the peer-review penalty must increase uncertainty by exactly 0.1 (clipped to [0,1]) *(p.7)*
- The fused projected probability should be between the minimum and maximum individual projected probabilities (convexity) *(implied, p.9)*
- Beta distribution with $\alpha = 1, \beta = 1$ (uniform) corresponds to vacuous opinion *(p.4)*

## Relevance to Project
This paper is **directly relevant** to propstore's uncertainty and opinion algebra implementation. It provides:
1. A concrete worked example of mapping empirical findings to Josang subjective opinions — validates propstore's Josang 2001 implementation
2. A demonstration of WBF for aggregating multiple opinions — directly usable in propstore's fusion operators
3. A methodology for encoding second-order uncertainty from multiple sources (sample size, replication, peer review) as modifiers of the uncertainty component — could inform propstore's calibration pipeline
4. Evidence that barycentric triangle and beta distribution visualizations make uncertainty interpretable — useful for propstore's render layer
5. The paper's per-factor uncertainty decomposition aligns with propstore's non-commitment principle: store each uncertainty source separately, fuse at render time

## Open Questions
- [ ] How does WBF compare to Josang's cumulative belief fusion (CBF) for this use case?
- [ ] Can the per-factor uncertainty approach be generalized to non-binary (multinomial) opinions?
- [ ] How sensitive is the fused opinion to the choice of $n_{\max}$ and $R$?
- [ ] What is the formal relationship between WBF-fused opinions and Bayesian posterior updating?
- [ ] How does this relate to Sensoy et al. (2018) evidential deep learning approach already in propstore?

## Related Work Worth Reading
- Josang, A. (2016). *Subjective Logic: A Formalism for Reasoning Under Uncertainty.* Springer. — The comprehensive reference for all SL operators
- Walkinshaw, N., & Hierons, R. (2023). Modelling second-order uncertainty in state machines. IEEE TSE. — Same second author, extends SL to state machines
- Walkinshaw, N., & Shepperd, M. (2020). Reasoning about uncertainty in empirical results. EASE 2020. — Predecessor work on uncertainty in empirical SE
- Camerer, C. F., et al. (2018). Evaluating the replicability of social science experiments. Nature Human Behaviour. — Source of replication base rates
- Open Science Collaboration (2015). Estimating the reproducibility of psychological science. Science. — Motivating context for replication crisis
- Josang, A., & McAnally, D. (2004). Multiplication and comultiplication of beliefs. — Extended SL operators not used here but relevant to propstore
