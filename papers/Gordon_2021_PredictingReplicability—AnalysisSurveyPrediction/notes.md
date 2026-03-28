---
title: "Predicting replicability — Analysis of survey and prediction market data from large-scale forecasting projects"
authors: "Michael Gordon, Domenico Viganola, Anna Dreber, Magnus Johannesson, Thomas Pfeiffer"
year: 2021
venue: "PLOS ONE"
doi_url: "https://doi.org/10.1371/journal.pone.0248780"
---

# Predicting replicability — Analysis of survey and prediction market data from large-scale forecasting projects

## One-Sentence Summary
Provides an empirical meta-analysis across four large-scale replication forecasting projects (RPP, EERP, ML1, ML2, SSRP) showing that prediction markets and surveys can predict replication outcomes with ~70-80% accuracy, and that p-values and effect sizes from original studies are informative predictors of replicability.

## Problem Addressed
The reproducibility of published research is a major concern in science policy. Multiple large-scale replication projects have been conducted, but the data from forecasting studies (surveys and prediction markets) associated with these projects had not been pooled and analyzed together to assess what predicts replicability and how well forecasting methods perform. *(p.1)*

## Key Contributions
- Pooled dataset from four large-scale forecasting projects covering 103 replication studies with prediction market and survey data *(p.1)*
- Shows prediction markets correctly identify replication outcomes 73% of the time (71% for surveys) *(p.1)*
- Both surveys and prediction markets can be used to elicit and aggregate forecasting information about replicability *(p.1)*
- Found a significant relationship between p-values of original findings and replication outcomes *(p.1)*
- Market and survey-based estimates are highly correlated with replication outcomes of the studies selected for replication *(p.1)*
- The pooled dataset is made available through the R package "pooledforecasts" *(p.1)*

## Study Design
- **Type:** Meta-analysis of forecasting data from replication projects
- **Population:** 103 published findings across social/behavioral sciences from four forecasting projects: RPP (n=36 with markets), EERP (n=18), ML2 (n=24), SSRP (n=21), plus an additional survey-only study ML1 *(p.2-4)*
- **Intervention(s):** Prediction markets and surveys used to forecast replication outcomes *(p.2-3)*
- **Comparator(s):** Actual replication outcomes (successful vs. unsuccessful) *(p.2)*
- **Primary endpoint(s):** Accuracy of prediction markets and surveys in forecasting replication success *(p.1)*
- **Secondary endpoint(s):** Correlation between forecasts and replication effect sizes; role of p-values as predictors *(p.6-7)*
- **Follow-up:** Cross-sectional (pooled analysis of completed projects) *(p.2)*

## Methodology
The authors pooled data from four replication forecasting projects (RPP, EERP, ML2, SSRP) that used prediction markets, plus ML1 which used surveys only. Each project had researchers forecast whether published findings would replicate, using either continuous trading prediction markets or surveys. The authors standardized definitions of replication success across projects, analyzed forecasting accuracy, and performed meta-analysis of prediction market and survey correlations with replication outcomes. *(p.1-5)*

### Replication projects included:
1. **RPP** (Reproducibility Project: Psychology) — 100 findings from 3 psychology journals (JPSP, JEP:LMC, PS), 36 had prediction market data *(p.2-3)*
2. **EERP** (Experimental Economics Replication Project) — 18 findings from AER and QJE *(p.3-4)*
3. **ML1** (Many Labs 1) — 13 findings, survey only (no prediction market), replicated at multiple sites *(p.4)*
4. **ML2** (Many Labs 2) — 28 findings, replicated across multiple sites with large samples *(p.4)*
5. **SSRP** (Social Sciences Replication Project) — 21 findings from Nature and Science published 2010-2015 *(p.5)*

### Forecasting study design common elements:
- Prediction markets: Participants traded contracts representing probability of replication success *(p.3)*
- Markets ran for 2 weeks in RPP and EERP, 2 weeks in ML2, information varied *(p.3)*
- Surveys: Participants rated probability of successful replication (0-100%) *(p.3)*
- Participants were researchers who participated in or were knowledgeable about replication projects *(p.3)*

## Key Equations / Statistical Models

$$
\text{Pearson } r = \text{cor}(\text{forecast}, \text{replication outcome})
$$
Where: forecast = final market price or mean survey response; replication outcome = relative effect size (replication effect / original effect) or binary success/failure
*(p.7)*

$$
\text{Logit}(P(\text{replication})) = \beta_0 + \beta_1 \cdot p\text{-value category}
$$
Where: p-value category = binary (p < 0.005 vs p >= 0.005) or continuous p-value; used to test whether original p-values predict replication success
*(p.10)*

$$
\text{MAE} = \frac{1}{N}\sum_{i=1}^{N} |f_i - o_i|
$$
Where: $f_i$ = forecast (market price or survey mean), $o_i$ = replication outcome (1 = success, 0 = failure); Mean Absolute Error used to assess calibration
*(p.8)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of forecasted studies | N | count | 103 | — | p.6 | Total across four forecasting studies |
| RPP market sample | — | count | 36 | — | p.3 | Studies with prediction market data |
| EERP sample | — | count | 18 | — | p.3 | Experimental economics replications |
| ML1 sample | — | count | 13 | — | p.4 | Survey only |
| ML2 sample | — | count | 28 | — | p.4 | Multi-site replications |
| SSRP sample | — | count | 21 | — | p.5 | Nature/Science replications |
| Overall replication rate | — | % | 49% | 36-85% | p.6 | Varies by project |
| Prediction market accuracy (binary) | — | % | 73 | 71-86 | p.6 | Correct classification rate |
| Survey accuracy (binary) | — | % | 71 | 67-86 | p.6 | Correct classification rate |
| Mean market price (repl. studies) | — | — | 0.641 | — | p.6 | For studies that replicated |
| Mean market price (non-repl. studies) | — | — | 0.352 | — | p.6 | For studies that did not replicate |
| Mean survey (repl. studies) | — | — | 0.631 | — | p.6 | Mean survey estimate |
| Mean survey (non-repl. studies) | — | — | 0.417 | — | p.6 | Mean survey estimate |
| Number of trades (market) | — | count | — | 76-532 | p.9 | Range across projects |
| Market duration | — | days | — | 7-42 | p.9 | Varies by project |
| Replication rate at p < 0.005 | — | % | 76 | — | p.10 | For original findings with p < 0.005 |
| Replication rate at p >= 0.005 | — | % | 18 | — | p.10 | Drops dramatically |
| Market mean absolute error | MAE | — | — | 0.341-0.410 | p.8 | Varies by project |
| Survey mean absolute error | MAE | — | — | 0.370-0.485 | p.8 | Varies by project |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Successful replication rate (overall) | proportion | 0.49 | — | — | All 103 studies | p.6 |
| RPP replication rate | proportion | 0.36 | — | — | 36 studies | p.6 |
| EERP replication rate | proportion | 0.61 | — | — | 18 studies | p.3 |
| ML2 replication rate | proportion | 0.54 | — | — | 28 studies | p.6 |
| SSRP replication rate | proportion | 0.62 | — | — | 21 studies | p.6 |
| ML1 replication rate | proportion | 0.85 | — | — | 13 studies | p.6 |
| Market price vs. replication (Pearson r) | correlation | 0.491 | 0.303-0.645 | <0.001 | 99 studies (excl. ML1) | p.7 |
| Survey vs. replication (Pearson r) | correlation | 0.481 | 0.315-0.619 | <0.001 | 103 studies | p.7 |
| Market-survey correlation (Pearson r) | correlation | 0.843 | 0.14-0.042 | <0.001 | 99 studies | p.7 |
| Market accuracy (binary classification) | accuracy | 0.73 | — | — | All 103 market studies | p.6 |
| Survey accuracy (binary classification) | accuracy | 0.71 | — | — | All 103 studies | p.6 |
| Prediction market meta-analysis (Fisher z) | z | 0.55 | 0.37-0.72 | — | Random effects | p.7 |
| t-test market prices (repl vs non-repl) | t | — | — | <0.001 | 99 market studies | p.6 |
| t-test survey (repl vs non-repl) | t | — | — | <0.001 | 103 studies | p.6 |
| p-value < 0.005 replication rate | proportion | 0.76 | — | — | 2-category split | p.10 |
| p-value >= 0.005 replication rate | proportion | 0.18 | — | — | 2-category split | p.10 |
| Combined p-value + market logistic | OR | 26.15 | — | <0.001 | Logistic regression | p.10 |
| Heterogeneity between studies (market r) | I² | — | — | 0.467 | Meta-analysis | p.7 |

## Methods & Implementation Details
- Replication defined as: (a) statistically significant effect in same direction as original, AND (b) p < 0.05 one-tailed *(p.2)*
- For RPP and SSRP: also required replication within original 95% CI *(p.2)*
- EERP definition: successful if found a "significant effect in the same direction of the original study (1:1; 1:6 for ML2)" *(p.2)*
- ML2 replications conducted at multiple sites with large samples — power typically higher than original *(p.2)*
- Statistical power of replications typically >80% to find original effect size, some >90% *(p.2)*
- Prediction markets: continuous double auction format *(p.3)*
- Participants received $50 endowment for market trading (varied by project) *(p.3)*
- Surveys used Likert-type probability scales (0-100%) *(p.3)*
- The Harvey-Kemp-Salk likelihood method used to account for small number of studies in meta-analysis *(p.6)*
- Random effects meta-analysis for combining correlations across studies *(p.7)*
- Mean absolute error (MAE) used as calibration metric — does not require a cutoff *(p.8)*
- Absolute deviation defined as |forecast - outcome| where outcome is binary (1/0) *(p.8)*
- Simple, variance-weighted, and "mean aggregation" methods compared for surveys *(p.8)*
- Mean aggregation performs best for surveys (MAE: M = 0.63, SD = 0.17) vs simple (M = 0.56, SD = 0.37) *(p.8)*
- Aggregation method matters: mean performs best overall *(p.8)*

## Figures of Interest
- **Fig 1 (p.7):** Market beliefs — final prices of 103 markets ordered by price. Green = successful replication, red = unsuccessful. Studies that replicate cluster above 0.5 threshold; non-replicating below.
- **Fig 2 (p.7):** Market price and replication outcome correlation with meta-analysis forest plot. Pearson r pooled = 0.491 [0.303-0.645]. Some heterogeneity between studies (I² = 0.467).
- **Fig 3 (p.8):** Market and survey correlations scatter plot. Shows prediction market and survey forecasts are highly correlated (r = 0.843). Quadrants show agreement/disagreement between methods.
- **Fig 4 (p.10):** Market dynamics — MAE of markets as function of number of trades and hours after market start. Error reduction occurs within first ~100 trades / first few days.
- **Fig 5 (p.10):** p-value and replication outcomes. Shows strong relationship: p < 0.005 studies replicate at ~76% vs ~18% for p >= 0.005.

## Results Summary
- Overall replication rate: 49% across 103 studies *(p.6)*
- Prediction markets correctly classify 73% of outcomes (using 0.5 threshold); surveys 71% *(p.6)*
- Market prices significantly higher for studies that replicated (M = 0.641) vs. did not (M = 0.352), p < 0.001 *(p.6)*
- Survey means also significantly different: 0.631 (replicated) vs. 0.417 (did not), p < 0.001 *(p.6)*
- Pearson correlation between market price and replication outcome: r = 0.491 [0.303-0.645] *(p.7)*
- Market and survey forecasts highly correlated with each other: r = 0.843 *(p.7)*
- Meta-analysis shows no statistically significant heterogeneity between studies, but I² = 0.467 *(p.7)*
- Mean absolute error: SSRP had lowest (best calibrated); RPP worst *(p.8)*
- Markets converge quickly — most error reduction in first ~100 trades and first few days *(p.9)*
- Original p-values strongly predict replication: two-category split (p < 0.005 vs >=) provides significant logistic relationship (OR = 26.15, p < 0.001) *(p.10)*
- Combining p-value category AND market price improves prediction *(p.10)*
- P-values serve as informative predictors in machine learning algorithms *(p.10)*

## Limitations
- Small number of studies overall (103) and per project (13-36) limits statistical power for comparing forecasting methods *(p.11)*
- Selection bias: only "important" or high-impact findings were selected for replication, not representative of all published research *(p.11)*
- Heterogeneity between replication projects in design, incentives, and field of study *(p.11)*
- The p-value relationship may partly be due to replication designs targeting higher power for studies with smaller original p-values *(p.10)*
- Differences in study design across projects make direct comparison difficult *(p.4-5)*
- Only social and behavioral sciences represented *(p.11)*
- Prediction markets may have negative evidence of heterogeneity (I² not significant but moderate at 0.467) *(p.7)*

## Arguments Against Prior Work
- Prior individual replication project analyses examined forecasting in isolation — this paper argues for pooling to increase statistical power *(p.1)*
- Some prior work assumed surveys alone are sufficient — this paper shows prediction markets provide a "significantly better predictor" for some metrics, though differences are modest *(p.8)*
- Prior claims that p-values alone cannot predict replicability are partially rebutted — p-values below 0.005 strongly predict successful replication (76% vs 18%) *(p.10)*

## Design Rationale
- Pooled analysis chosen because individual projects have too few studies for robust comparison of forecasting methods *(p.1)*
- Used both binary classification accuracy AND continuous correlation because each captures different aspects of forecasting quality *(p.6-7)*
- MAE used as calibration metric because it does not require choosing a threshold (unlike binary accuracy) *(p.8)*
- p-value threshold of 0.005 chosen based on Benjamin et al. (2018) suggestion for redefining statistical significance *(p.10)*

## Testable Properties
- Prediction markets should correctly classify replication outcomes ~73% of the time using 0.5 price threshold *(p.6)*
- Survey means should correctly classify replication outcomes ~71% of the time using 0.5 threshold *(p.6)*
- Market prices and survey means should correlate at r > 0.8 with each other *(p.7)*
- Studies with original p < 0.005 should replicate at ~76% vs ~18% for p >= 0.005 *(p.10)*
- Market prices for studies that replicate should be significantly higher than for those that do not (expected difference ~0.29) *(p.6)*
- Adding p-value information to market forecasts should improve prediction accuracy *(p.10)*
- Markets should converge within ~100 trades / first few days — most error reduction is early *(p.9)*

## Relevance to Project
This paper provides empirical calibration data for how well human forecasters and prediction markets predict replication outcomes. For propstore's argumentation and uncertainty layers, the key insight is that prior p-values and crowd-sourced beliefs are informative but imperfect signals of claim reliability. The ~73% accuracy rate provides a concrete base rate for calibrating confidence in published findings. The p-value threshold finding (0.005) is directly relevant to setting evidence strength thresholds in the opinion/belief layer.

## Open Questions
- [ ] How do these forecasting accuracy rates generalize outside social/behavioral sciences?
- [ ] Would Bayesian updating of market prices with p-value information improve calibration beyond the simple logistic model?
- [ ] Can the pooled dataset be used to calibrate propstore's opinion algebra for claim strength?

## Related Work Worth Reading
- Camerer CF, Dreber A, Holzmeister F, et al. Evaluating the replicability of social science experiments in Nature and Science (SSRP) — ref [11]
- Dreber A, Pfeiffer T, Almenberg J, et al. Using prediction markets to estimate the reproducibility of scientific research — ref [9]
- Benjamin DJ, Berger JO, et al. Redefine statistical significance — ref [30]
- Yang Y, Youyou W, Uzzi B. Estimating the deep replicability of scientific findings using human and AI — ref [33]
- Altmejd A, Dreber A, Forsell E, et al. Predicting the replicability of social science lab experiments — ref [34]
- Pawel S, Held L. Probabilistic forecasting of replication studies — ref [40]

## Collection Cross-References

### Already in Collection
- [[Camerer_2016_EvaluatingReplicabilityLaboratoryExperiments]] — This is the EERP (Experimental Economics Replication Project), one of the four forecasting projects pooled in this paper. Gordon et al. use EERP's 18 studies with prediction market data.
- [[Camerer_2018_EvaluatingReplicabilitySocialScience]] — This is the SSRP (Social Sciences Replication Project), another of the four forecasting projects pooled here. Gordon et al. use SSRP's 21 studies.
- [[Aarts_2015_EstimatingReproducibilityPsychologicalScience]] — This is the RPP (Reproducibility Project: Psychology). Gordon et al. use 36 RPP studies that had prediction market data.
- [[Begley_2012_DrugDevelopmentRaiseStandards]] — Background on reproducibility crisis in preclinical research; not directly pooled but contextualizes the problem.

### Cited By (in Collection)
- [[Errington_2021_InvestigatingReplicabilityPreclinicalCancer]] — cites Gordon et al. 2021 in reference list (ref 23) as related forecasting study

### New Leads (Not Yet in Collection)
- Yang, Youyou & Uzzi (2020) — "Estimating the deep replicability of scientific findings using human and AI" — extends forecasting with machine learning
- Altmejd, Dreber, Forsell et al. (2019) — "Predicting the replicability of social science lab experiments" — predecessor with Forsell as coauthor
- Pawel & Held (2020) — "Probabilistic forecasting of replication studies" — Bayesian approach to replication forecasting
- Benjamin et al. (2018) — "Redefine statistical significance" — proposes p < 0.005 threshold validated here

### Supersedes or Recontextualizes
- (none — this paper pools existing project data rather than superseding individual studies)

### Conceptual Links (not citation-based)
- [[Errington_2021_InvestigatingReplicabilityPreclinicalCancer]] — **Strong.** Both study replication outcomes empirically. Gordon provides forecasting accuracy rates (73% market, 71% survey) across social/behavioral science; Errington provides ground-truth replication rates in cancer biology (3-82% depending on criterion). Together they bracket the question: how well can we predict replication, and what are actual base rates? Gordon's p-value threshold finding (p < 0.005 -> 76% replication) could be tested against Errington's data.
- [[Guo_2017_CalibrationModernNeuralNetworks]] — **Moderate.** Gordon's paper is fundamentally about calibration — how well do forecasts (market prices, survey means) track binary outcomes? Guo's temperature scaling for neural network calibration addresses the same question for model outputs. The MAE and accuracy metrics Gordon uses are analogous to ECE in Guo's framework.
