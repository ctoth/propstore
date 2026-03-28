---
title: "Evaluating the replicability of social science experiments in Nature and Science between 2010 and 2015"
authors: "Colin F. Camerer, Anna Dreber, Felix Holzmeister, Teck-Hua Ho, Jurgen Huber, Magnus Johannesson, Michael Kirchler, Gideon Nave, Brian A. Nosek, Thomas Pfeiffer, Adam Altmejd, Nick Buttrick, Taizan Chan, Yiling Chen, Eskil Forsell, Anup Gampa, Emma Heikensten, Lily Hummer, Taisuke Imai, Siri Isaksson, Dylan Manfredi, Julia Rose, Eric-Jan Wagenmakers, Hang Wu"
year: 2018
venue: "Nature Human Behaviour"
doi_url: "https://doi.org/10.1038/s41562-018-0399-z"
pages: 68
produced_by:
  agent: "Claude Opus 4.6 (1M context)"
  skill: "paper-reader"
  timestamp: "2026-03-28T20:22:12Z"
---
# Evaluating the replicability of social science experiments in Nature and Science between 2010 and 2015

## One-Sentence Summary
A systematic replication of 21 experimental social science studies published in Nature and Science (2010-2015), finding that 13/21 (62%) replicated with effect sizes on average 50% smaller than originals, combined with prediction markets that accurately forecast replication outcomes.

## Problem Addressed
The replication crisis in social science: whether high-profile experimental findings published in the two most prestigious general science journals (Nature and Science) can be independently reproduced, and whether peer beliefs (via prediction markets and surveys) can predict which studies will replicate. *(p.2)*

## Key Contributions
- Replicated 21 social science experiments from Nature and Science (2010-2015) using high-powered designs (90% power to detect 75% of original effect in Stage 1, 50% in Stage 2) *(p.2-4)*
- Found 13/21 (62%) replicated by statistical significance criterion (p < 0.05, same direction) *(p.53)*
- Demonstrated that replication effect sizes are on average 50% of original effect sizes (mean relative effect size = 0.462, 95% CI = 27.0%-65.5%) *(p.62)*
- Showed prediction markets and surveys by academic peers can predict replication outcomes with high accuracy (Spearman rho = 0.842 for markets, 0.643 for surveys after Stage 2) *(p.30-32)*
- Compared results with RPP (psychology) and EERP (experimental economics) replication projects *(p.33, 67)*
- Provided Bayesian mixture model estimates of true positive rate (0.673, 95% HDI: 0.43-0.92) and replication deflation factor (0.708, 95% HDI: 0.58-0.83) *(p.63)*

## Study Design
- **Type:** Systematic multi-site replication study with prediction markets *(p.2)*
- **Population:** N=21 experimental studies from Nature and Science, social sciences, 2010-2015. Five replication teams across Caltech/Wharton, COS/University of Virginia, Stockholm School of Economics, National University of Singapore, and University of Innsbruck *(p.7)*
- **Intervention(s):** Direct replications following original protocols as closely as possible, with original author consultation on replication plans *(p.7, 10)*
- **Comparator(s):** Original study effect sizes and p-values *(p.53-54)*
- **Primary endpoint(s):** Statistical significance of replication (p < 0.05 in same direction as original) *(p.4)*
- **Secondary endpoint(s):** Relative effect size, meta-analytic effect size, prediction interval indicator, Small Telescopes approach, default and replication Bayes factors, prediction market beliefs, survey beliefs *(p.16-21)*
- **Follow-up:** Two-stage design: Stage 1 data collection, then Stage 2 if Stage 1 fails to replicate *(p.15)*

## Methodology
Two-stage replication procedure with pre-registered protocols:
1. Stage 1: Sample size chosen for 90% power to detect 75% of the original effect size (correlation coefficient r) at 5% significance level in a two-sided test *(p.16)*
2. If Stage 1 fails (p >= 0.05 or effect in wrong direction), Stage 2 data collection added to achieve 90% power to detect 50% of original effect size *(p.15)*
3. Replications pre-registered at OSF (https://osf.io/pfdyw/) *(p.2)*
4. Five replication teams, with all online AMT experiments replicated by Stockholm team *(p.7)*
5. Same statistical tests as original studies used *(p.7)*
6. Prediction markets and surveys conducted with 397 academic participants before replication results known *(p.26)*

## Key Equations / Statistical Models

$$
r_{\text{replication}} = \frac{r_{\text{original}} \cdot \text{relative effect size}}{1}
$$
Where: r = correlation coefficient (effect size measure), relative effect size = ratio of replication to original standardized effect sizes
*(p.18)*

$$
\text{False positive rate (two-stage)} = 0.025
$$
Where: Two-stage procedure inflates nominal 5% false positive rate only to 2.5% total, because replications are directional (effect must be in same direction) and two tests are conducted only if Stage 1 fails
*(p.16)*

$$
\text{Bayes Factor} = \frac{P(D|H_1)}{P(D|H_0)}
$$
Where: One-sided default Bayes factor using folded Cauchy distribution with scale 0.707 as prior on effect size under H1; H0 = null hypothesis of no effect
*(p.20)*

$$
\text{Bayesian mixture model: } \Phi \sim \text{Beta}(\alpha_\Phi, \beta_\Phi), \quad d \sim \text{Beta}(\alpha_d, \beta_d)
$$
Where: Phi = true positive rate, d = replication deflation factor (degree to which true effects are overestimated in originals vs replications)
*(p.22, 63)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of studies replicated | n | - | 21 | - | 2 | All social science experiments meeting inclusion criteria |
| Statistical significance threshold | alpha | - | 0.05 | - | 4 | Two-sided test |
| Stage 1 power target | - | - | 0.90 | - | 16 | To detect 75% of original effect |
| Stage 2 power target | - | - | 0.90 | - | 15 | To detect 50% of original effect |
| False positive rate (two-stage) | - | - | 0.025 | - | 16 | Total false positive rate with two-stage procedure |
| Replication rate (significance criterion) | - | - | 13/21 (0.619) | - | 53 | Studies with p < 0.05 in same direction |
| Mean relative effect size (all studies) | - | - | 0.462 | 0.270-0.655 | 62 | 95% CI |
| Mean relative effect size (replicated) | - | - | 0.745 | 0.601-0.889 | 62 | 95% CI, for 13 replicated studies |
| Mean relative effect size (non-replicated) | - | - | 0.003 | -0.124-0.131 | 62 | 95% CI, for 8 non-replicated studies |
| Mean standardized effect size (original) | r | - | 0.459 | SD=0.229 | 62 | Correlation coefficient |
| Mean standardized effect size (replication) | r | - | 0.249 | SD=0.283 | 62 | Correlation coefficient |
| Spearman correlation (original vs replication effect sizes) | rho | - | 0.574 | - | 62 | p = 0.007, 95% CI = (18.9%, 80.6%) |
| Prediction market correlation with replication (Stage 2) | rho | - | 0.842 | - | 30 | p < 0.001, n=21 |
| Survey belief correlation with replication (Stage 2) | rho | - | 0.643 | - | 30 | p < 0.001, n=21 |
| Mean prediction market belief (replicating, Stage 2) | - | - | 0.569 | range 0.213-0.799 | 30 | For studies expected to replicate |
| True positive rate (Bayesian mixture) | Phi | - | 0.673 | 0.43-0.92 | 63 | 95% HDI |
| Replication deflation factor (Bayesian mixture) | d | - | 0.708 | 0.58-0.83 | 63 | 95% HDI |
| Default Bayes factor scale | - | - | 0.707 | - | 20 | Folded Cauchy prior |
| Prediction market participants | - | - | 397 | - | 26 | Total signed up |
| Mean absolute prediction error (markets) | - | - | 0.308 | - | 32 | For prediction markets |
| Mean absolute prediction error (surveys) | - | - | 0.349 | - | 32 | For survey beliefs |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Overall replication rate | Proportion | 13/21 = 0.619 | - | - | All 21 studies | 53 |
| Mean relative effect size (all) | r_rep/r_orig | 0.462 | 0.270-0.655 | - | All 21 studies | 62 |
| Mean relative effect size (replicated) | r_rep/r_orig | 0.745 | 0.601-0.889 | - | 13 replicated | 62 |
| Mean relative effect size (non-replicated) | r_rep/r_orig | 0.003 | -0.124-0.131 | - | 8 non-replicated | 62 |
| Original vs replication effect sizes | Wilcoxon z | 3.667 | - | <0.001 | n=21 | 62 |
| Prediction markets vs replication | Spearman rho | 0.842 | - | <0.001 | Treatment 2, n=21 | 30 |
| Survey beliefs vs replication | Spearman rho | 0.643 | - | <0.001 | Treatment 2, n=21 | 30 |
| Markets vs surveys correlation | Spearman rho | 0.894 | - | <0.001 | n=21 | 65 |
| True positive rate | Posterior mean | 0.673 | 0.43-0.92 (HDI) | - | Bayesian mixture model | 63 |
| Replication deflation factor | Posterior mean | 0.708 | 0.58-0.83 (HDI) | - | Bayesian mixture model | 63 |
| Market belief for replicated studies (Stage 1) | Mean | 0.569 | 0.213-0.799 | - | Treatment 1 | 30 |
| Original p-value vs replication | Spearman rho | -0.405 | - | 0.069 | n=21, negative correlation | 57 |
| Meta-analytic estimate (all replicated) | r | 0.232 | - | - | Robustness test, 13 studies | 25 |
| Replication rate (Small Telescopes) | Proportion | 12/21 | - | - | Alternative criterion | 60 |
| Replication rate (prediction interval) | Proportion | 14/21 | - | - | Alternative criterion | 60 |
| SSRP vs RPP replication rate | Proportion | 62% vs 36% | - | - | Comparison of projects | 67 |
| SSRP vs EERP replication rate | Proportion | 62% vs 61% | - | - | Comparison of projects | 67 |

## Methods & Implementation Details
- Inclusion criteria: (i) Nature or Science, 2010-2015, (ii) between- or within-subjects treatment comparisons, (iii) experiments using students or easily accessible adult subjects (AMT included, field experiments excluded), (iv) equipment available in standard lab, (v) results with at least one statistically significant finding (p < 0.05) *(p.2-4)*
- Did not exclude studies already subject to replication attempts *(p.4)*
- For papers with multiple studies, selected first study reporting significant treatment effect; if equally central, randomly selected *(p.4-5)*
- Used same statistical tests as originals; did not test distributional assumptions *(p.7)*
- All p-values based on two-sided tests *(p.7)*
- Replication reports pre-registered at OSF before data collection *(p.10)*
- Five replication teams: Caltech/Wharton (4 replications), COS/UVA (5), Stockholm (5), NUS (3), Innsbruck (4) *(p.7)*
- Sample sizes in replications generally larger than planned due to difficulty predicting exact exclusions *(p.16)*
- Standardized effect sizes computed using Fisher transformation of correlation coefficients (r) *(p.18)*
- Meta-analytic effect size using fixed-effect weighted meta-analysis *(p.18)*
- Prediction intervals from Patil, Peng, and Leek (2016) *(p.19)*
- Small Telescopes approach from Simonsohn (2015): replication effect size significantly smaller than "small effect size" the original could have detected with 33% power *(p.20)*
- Bayesian analysis: one-sided default Bayes factor with folded Cauchy scale 0.707; also computed replication Bayes factors *(p.20-21)*
- Bayesian mixture model with two components: (1) null hypothesis (expected effect = 0), (2) true positive (expected effect = proportion of original) *(p.22)*
- Original author feedback solicited on all replication reports before data collection *(p.10)*
- Prediction market platform used web-based trading with logarithmic market scoring rule (LMSR) *(p.27-28)*
- Treatment 1: binary market (replicate in Stage 1 yes/no); Treatment 2: three-outcome market (replicate Stage 1 / replicate Stage 2 / no replication) *(p.28)*
- Markets endowed with 100 Tokens, converted at 0.5 USD per Token *(p.29)*

## Figures of Interest
- **Supp. Fig 1 (p.59):** Replication results after Stage 1 and Stage 2 with robustness tests (t-tests and F-tests). Standardized effect sizes normalized to 1 = original. Stage 1: 12/21 replicate. Stage 2: 13/21 replicate. Meta-analysis: 15/21 significant.
- **Supp. Fig 2 (p.60):** Prediction intervals and Small Telescopes approach. 14/21 within 95% prediction interval. Small Telescopes: 12/21 replicate.
- **Supp. Fig 3 (p.61):** Replication Bayes factors for 21 studies on Jeffreys evidence scale (extreme H0 support to extreme H1 support).
- **Supp. Fig 4 (p.62):** Original vs replication effect sizes (correlation coefficients r). Clear regression to mean pattern. Spearman rho = 0.574.
- **Supp. Fig 5 (p.63):** Bayesian mixture model posteriors. True positive rate mean = 0.673. Deflation factor mean = 0.708.
- **Supp. Fig 7 (p.65):** Prediction market and survey beliefs vs replication outcome. Markets and surveys highly correlated (rho = 0.894).
- **Supp. Fig 8 (p.66):** Market/survey beliefs vs relative effect size. Positive correlation (rho ~ 0.60 for both).
- **Supp. Fig 9 (p.67):** Comparison of SSRP, EERP, and RPP replication rates and relative effect sizes.

## Results Summary
- 13 of 21 (62%) studies replicated by statistical significance criterion (p < 0.05 in same direction as original) *(p.53)*
- Replication effect sizes are substantially smaller than originals: mean standardized effect size r = 0.249 vs 0.459, a significant difference (Wilcoxon z = 3.667, p < 0.001) *(p.62)*
- Mean relative effect size of all replications is 46.2% [95% CI: 27.0%-65.5%] *(p.62)*
- For the 13 studies that replicated: mean relative effect size = 74.5% [95% CI: 60.1%-88.9%] *(p.62)*
- For the 8 that did not replicate: mean relative effect size = 0.3% [95% CI: -12.4%-13.1%] *(p.62)*
- Prediction markets strongly predict replication outcomes: Spearman rho = 0.842 (p < 0.001) after Stage 2 *(p.30)*
- Survey beliefs also predict but less accurately: Spearman rho = 0.643 (p < 0.001) *(p.30)*
- Markets outperform surveys: mean absolute prediction error 0.308 vs 0.349 *(p.32)*
- Bayesian mixture model: true positive rate = 0.673 (95% HDI: 0.43-0.92), replication deflation factor = 0.708 (95% HDI: 0.58-0.83) *(p.63)*
- Original p-value is weakly negatively correlated with replication success (smaller original p-values somewhat more likely to replicate) but not significantly (rho = -0.405, p = 0.069) *(p.57)*
- Comparison with other projects: SSRP 62% replication rate is higher than RPP (36%) but similar to EERP (61%) *(p.67)*

## Limitations
- Only 21 studies -- small sample for drawing general conclusions about replicability *(p.2)*
- PDF obtained is supplementary information only; main article text was not in this PDF. Some findings are known from the main text but not fully documented here.
- Inclusion criteria limit generalizability: only between/within-subjects experiments, lab-feasible, with students/AMT subjects *(p.3)*
- Selection of which study/result to replicate from multi-study papers introduces arbitrariness *(p.4-5)*
- Some replications had unintended protocol deviations (e.g., Ackerman et al., Sparrow et al., Lee & Schwarz) *(p.36-39)*
- Original effect sizes may be inflated by publication bias -- power calculations based on inflated estimates may still be insufficient *(p.17)*
- Did not test distributional assumptions of statistical tests used *(p.7)*
- Some original authors did not respond to requests for materials/feedback *(p.9, 52)*
- AMT subject pool may have changed between original and replication *(p.13-14)*

## Arguments Against Prior Work
- Challenges the implicit assumption that results in top journals are robust: 38% of tested studies failed to replicate *(p.53)*
- Higher replication rate (62%) than RPP's psychology replication (36%), suggesting Nature/Science social science may be somewhat more reliable than psychology broadly, or that methodological improvements in this project helped *(p.67)*
- Effect sizes in original studies are consistently inflated relative to replications, consistent with publication bias and winner's curse *(p.62)*
- Original authors' rebuttals to non-replication (methodology differences, changed subject pools, etc.) are documented but the authors note these explanations are often ad hoc *(p.11-13)*

## Design Rationale
- Focused on Nature and Science because they are the two most prestigious general science journals, so findings are considered exciting, innovative, and important *(p.2)*
- Two-stage design chosen to balance power against cost: Stage 1 catches large effects; Stage 2 provides additional power for smaller effects *(p.15)*
- Pre-registered replication reports to prevent post-hoc flexibility *(p.10)*
- Prediction markets used because they aggregate private information and beliefs efficiently and have been successfully applied to replication prediction *(p.25)*
- Two treatment conditions for prediction markets to compare simple (Stage 1 only) vs complex (three-outcome) market designs *(p.25-26)*
- Original author consultation to ensure replications are as faithful as possible, reducing "hidden moderator" explanations for non-replication *(p.10)*

## Testable Properties
- Replication rate of social science experiments in top journals: ~62% (13/21) by p < 0.05 criterion *(p.53)*
- Mean relative effect size of replications: ~50% of original (0.462, 95% CI: 0.270-0.655) *(p.62)*
- Prediction market beliefs correlate with replication outcome: Spearman rho > 0.80 *(p.30)*
- Survey beliefs correlate with replication outcome but less than markets: rho ~ 0.64 *(p.30)*
- Prediction markets and surveys are highly correlated with each other: rho ~ 0.89 *(p.65)*
- True positive rate for published findings estimated at ~67% (95% HDI: 43-92%) *(p.63)*
- Original p-value is weakly predictive of replication: smaller p slightly more likely to replicate (rho ~ -0.40, p ~ 0.07) *(p.57)*
- False positive rate under two-stage procedure: ~2.5% *(p.16)*
- Replication rates comparable across SSRP and EERP (~61-62%), both higher than RPP (~36%) *(p.67)*

## Relevance to Project
This paper provides empirical base rates for replication in social science, which are critical for calibrating uncertainty in the propstore argumentation system. Key relevance:
1. **Base rates for belief strength:** When encoding published claims, the prior probability that a social science finding from a top journal is a true positive is ~67% (Bayesian mixture model), not 95%+. This directly informs opinion formation in Subjective Logic.
2. **Effect size deflation:** Even replicated findings show ~50% effect size deflation. Claims about effect magnitudes should carry substantial uncertainty.
3. **Prediction markets as calibration source:** The strong correlation between peer prediction and actual replication suggests that expert belief aggregation (analogous to argumentation) is a valid signal.
4. **Multiple replicability indicators:** The paper demonstrates that different operationalizations of "replication" (p-value, effect size, prediction interval, Small Telescopes, Bayes factor) give different answers -- relevant to propstore's non-commitment principle of holding multiple assessments.

## Open Questions
- [ ] Main article text not in this PDF -- should retrieve the actual Nature letter for complete analysis
- [ ] How do these base rates compare with more recent replication projects (post-2018)?
- [ ] Could the Bayesian mixture model parameters be directly used as priors in propstore's opinion algebra?

## Collection Cross-References

### Already in Collection
- [[Aarts_2015_EstimatingReproducibilityPsychologicalScience]] -- the RPP psychology replication project (100 studies, 36% replication rate). This paper directly compares its results with RPP (Supp. Fig 9, p.67), finding higher replication rate (62% vs 36%) possibly due to journal prestige or methodological improvements.
- [[Camerer_2016_EvaluatingReplicabilityLaboratoryExperiments]] -- EERP economics replication (18 studies, 61% rate). Companion study by same lead authors; nearly identical replication rate (61% vs 62%), suggesting convergence across social science fields at Nature/Science level.

### New Leads (Not Yet in Collection)
- Dreber et al. (2015) -- "Using prediction markets to estimate the reproducibility of scientific research." PNAS 112, 15343-15347. Prediction markets for RPP replication forecasting.
- Patil, Peng & Leek (2016) -- "What should researchers expect when they replicate studies?" Perspectives on Psychological Science. Prediction interval method.
- Simonsohn (2015) -- "Small Telescopes: detectability and the evaluation of replication results." Psychol Sci. Alternative replication criterion.

### Conceptual Links (not citation-based)
- [[Aarts_2015_EstimatingReproducibilityPsychologicalScience]] -- Both provide empirical base rates for propstore's opinion calibration. Together they bracket the replication rate: 36% (broad psychology) to 62% (top journals, social science). The convergence on ~50% effect size deflation across both projects is a strong empirical regularity.

## Related Work Worth Reading
- Open Science Collaboration (2015). "Estimating the reproducibility of psychological science." Science 349, aac4716. (RPP -- the landmark psychology replication project) -> NOW IN COLLECTION: [[Aarts_2015_EstimatingReproducibilityPsychologicalScience]]
- Camerer et al. (2016). "Evaluating replicability of laboratory experiments in economics." Science 351, 1433-1436. (EERP -- the economics counterpart) -> NOW IN COLLECTION: [[Camerer_2016_EvaluatingReplicabilityLaboratoryExperiments]]
- Dreber et al. (2015). "Using prediction markets to estimate the reproducibility of scientific research." PNAS 112, 15343-15347.
- Patil, Peng, & Leek (2016). "What should researchers expect when they replicate studies?" Perspectives on Psychological Science.
- Simonsohn (2015). "Small Telescopes: detectability and the evaluation of replication results." Psychological Science 26, 559-569.
