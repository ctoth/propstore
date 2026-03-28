---
title: "Predicting the replicability of social science lab experiments"
authors: "Adam Altmejd, Anna Dreber, Eskil Forsell, Juergen Huber, Taisuke Imai, Magnus Johannesson, Michael Kirchler, Gideon Nave, Colin Camerer"
year: 2019
venue: "PLOS ONE"
doi_url: "https://doi.org/10.1371/journal.pone.0225826"
---

# Predicting the replicability of social science lab experiments

## One-Sentence Summary
Uses machine learning (LASSO, Random Forest, logistic regression) on features of original studies from four large-scale replication projects to predict binary replication success at 70% accuracy (AUC 0.77), validated out-of-sample at 71% (AUC 0.73), identifying original effect size, p-value, and sample size as the strongest predictors.

## Problem Addressed
Replication is expensive and slow; there is no cheap, scalable way to triage which findings are likely to replicate. Prediction markets and surveys achieve ~70% accuracy but require expert time. This paper asks whether statistical features of the original paper alone can match that accuracy via ML models. *(p.1)*

## Key Contributions
- Train ML models on 131 replication attempts from RPP, EERP, ML1, and ML2 to predict binary replication and relative effect size *(p.1)*
- Cross-validated accuracy of 70% (AUC 0.77) for binary replication; Spearman rho = 0.38 for relative effect sizes *(p.1)*
- Pre-registered out-of-sample validation on SSRP: 71% accuracy (AUC 0.73), rho = 0.25 *(p.1)*
- Identify that basic statistical features (original effect size, p-value, sample size, whether effect is interaction vs main) drive most predictive power *(p.1, p.9)*
- Demonstrate that ML predictions match prediction market accuracy (~70%) without requiring expert panels *(p.6, p.10)*

## Study Design
- **Type:** Meta-analytic prediction study (training ML models on replication outcomes)
- **Population:** 131 replication attempts from 4 projects: RPP (N=97), EERP (N=18), ML1 (N=13), ML2 (N=3 usable from 28 after deduplication); validated on SSRP (N=21) *(p.3)*
- **Intervention(s):** N/A — observational/predictive study
- **Comparator(s):** Prediction markets and survey beliefs from peer scientists *(p.1, p.6)*
- **Primary endpoint(s):** Binary replication success (did the replication produce a statistically significant effect in the same direction as original?) *(p.3)*
- **Secondary endpoint(s):** Relative effect size = replication effect size / original effect size *(p.3)*
- **Follow-up:** N/A

## Methodology
Data from four large-scale replication projects (RPP, EERP, ML1, ML2) are combined. 131 studies with replication outcomes form the training set. The authors define two outcome variables: (1) binary replication (significant p < 0.05 in same direction), and (2) relative effect size (replication ES / original ES). They assemble a feature set of ~60 variables describing the original study's statistical properties, study design, and author/journal characteristics. They use nested cross-validation (5-fold outer, 10-fold inner with hyperparameter tuning) to train LASSO, Random Forest, and logistic/linear regression models. The best model (Random Forest for classification, LASSO for continuous) is validated out-of-sample on the pre-registered SSRP dataset. *(p.2-5)*

## Key Equations / Statistical Models

$$
\text{Replicated} = \begin{cases} 1 & \text{if } p < 0.05 \text{ and effect in same direction} \\ 0 & \text{otherwise} \end{cases}
$$
Where: binary replication outcome variable.
*(p.3)*

$$
\text{Relative Effect Size Estimate} = \frac{\text{replication effect size (r)}}{\text{original effect size (r)}}
$$
Where: continuous outcome variable measuring replication fidelity; values near 1 indicate full replication.
*(p.3)*

The Random Forest model uses the binary classification setup with mtry (number of features at each split) and ntree (number of trees) tuned via inner cross-validation. *(p.4)*

LASSO regression is used for continuous relative effect size prediction, with shrinkage parameter lambda tuned via inner CV. Cost parameter C is tuned for LASSO classification. For GBM, the number of splits performed in each tree is the key hyperparameter. *(p.4, p.14)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Training set size | N | studies | 131 | — | 3 | From RPP (97) + EERP (18) + ML1 (13) + ML2 (3) |
| Out-of-sample test set size | N | studies | 21 | — | 8 | SSRP replication studies |
| Cross-validation outer folds | K_outer | — | 5 | — | 4 | Outer loop for performance estimation |
| Cross-validation inner folds | K_inner | — | 10 | — | 4 | Inner loop for hyperparameter tuning |
| Inner loop repetitions | — | — | 10 | — | 4 | Each inner tuning repeated 10 times |
| CV outer repetitions | — | — | 100 | — | 4 | 100 random outer CV partitions averaged |
| Training/test split (outer) | — | % | 80/20 | — | 4 | 4 folds train, 1 fold test |
| Number of candidate features | — | — | ~60 | — | 3 | After removing redundant transformations |
| RF classification accuracy (CV) | — | % | 70 | — | 6 | Best model on training set |
| RF classification AUC (CV) | — | — | 0.77 | — | 6 | Cross-validated |
| RF replication threshold (optimal) | — | probability | 0.50 | — | 6 | 50th percentile threshold |
| LASSO regression Spearman rho (CV) | rho | — | 0.38 | — | 1 | For relative effect size |
| SSRP out-of-sample accuracy | — | % | 71 | — | 8 | Pre-registered validation |
| SSRP out-of-sample AUC | — | — | 0.73 | — | 8 | Pre-registered validation |
| SSRP out-of-sample Spearman rho | rho | — | 0.25 | — | 8 | For relative effect sizes |
| Prediction market accuracy (benchmark) | — | % | ~70 | — | 6 | From Dreber et al., Camerer et al. |
| Base rate replication success | — | % | ~55 | — | 6 | In training data |
| Random Forest ntree | — | trees | 500 | — | 14 | S4 Fig description |
| LASSO shrinkage/cost | lambda/C | — | tuned | — | 4 | Via inner CV |
| Absolute deviation threshold | — | r | 0.08 | — | 10 | Mean absolute deviation of SSRP predictions |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Binary replication prediction | Accuracy | 70% | — | — | CV on 131 training studies | 6 |
| Binary replication prediction | AUC | 0.77 | — | — | CV on 131 training studies | 6 |
| Relative effect size prediction | Spearman rho | 0.38 | — | — | CV on 131 training studies | 1 |
| Binary replication (SSRP OOS) | Accuracy | 71% | — | — | 21 SSRP studies | 8 |
| Binary replication (SSRP OOS) | AUC | 0.73 | — | — | 21 SSRP studies | 8 |
| Relative effect size (SSRP OOS) | Spearman rho | 0.25 | — | — | 21 SSRP studies | 8 |
| SSRP market prediction accuracy | Accuracy | 71% | — | — | 21 SSRP studies (pre-registered) | 8 |
| SSRP survey prediction accuracy | Accuracy | ~67% | — | — | 21 SSRP studies | 8 |
| Continuous model correlation (CV) | Pearson r | 0.27 | — | — | Between predicted and actual r values | 6 |
| Linear model RMSE (CV) | RMSE | 0.25 | — | — | Relative effect size | 6 |
| Linear model correlation (SSRP) | Pearson r | 0.23 | — | — | Out-of-sample | 10 |
| Random Forest AUROC (best model) | AUROC | 0.71 | — | — | Training CV, Random Forest classifier | 5 |
| LASSO classifier AUC | AUC | 0.71 | — | — | Cross-validated | 5 |
| Simple model (p-value + ES only) | Accuracy | ~65% | — | — | Approximate from discussion | 7 |
| Prediction market Spearman rho (SSRP) | rho | 0.30 | — | — | For relative effect sizes | 8 |

## Methods & Implementation Details
- **Feature engineering:** Features include original p-value, effect size (r), sample size, whether effect is interaction or main, number of authors, author citations, discipline (social psych, cognitive psych, economics), compensation type, whether same country/language/lab/subjects/online, paper length, journal, seniority of replication team *(p.3-4)*
- **Only standardized transformations used:** log(sample size), log(p-value), and all linear transformations of each other; no feature-specific domain transformations to avoid overfitting *(p.4)*
- **Nested cross-validation:** 5-fold outer × 10-fold inner × 10 repetitions × 100 random partitions. Inner loop tunes hyperparameters. Outer loop evaluates. Each outer fold trains on 80%, tests on 20%. *(p.4)*
- **Algorithms compared:** Random Forest (best for classification), LASSO (best for continuous), logistic regression, GBM, linear regression *(p.4-5)*
- **Variable importance:** Random Forest variable importance and LASSO coefficient magnitudes both show post-hoc power, p-value, original effect size, and number of authors as top predictors *(p.8-9)*
- **Pre-registration:** SSRP out-of-sample test was pre-registered — predictions submitted before SSRP results were known *(p.8)*
- **Prediction market comparison:** The model achieves 0.77 AUC vs markets at 0.71 AUC (within-sample); on SSRP, model = 0.73, market = 0.83 *(p.8)*
- **SSRP had two-stage design:** First collection stage used 5× original sample, then a second data collection at ~10× for studies that were close *(p.14)*
- **Threshold sensitivity:** At 0.65 predicted probability threshold, only 10% of replicable studies would pass through (too strict). The model's optimal threshold (~50th percentile) produces ~70% accuracy. *(p.12)*

## Figures of Interest
- **Fig 1 (p.4):** Effect sizes and correlations — scatter plot of original vs replication effect sizes across 4 datasets, color-coded by replication project. Shows replications cluster below the diagonal (smaller than original).
- **Fig 2 (p.4):** Nested cross-validation schema — 5-fold outer with 10-fold inner hyperparameter tuning diagram.
- **Fig 3 (p.5):** Interquartile range (IQR) of Random Forest classifier (left) and regression (right) validation set performance. Random Forest achieves median AUC ~0.71 for binary classification.
- **Fig 4 (p.9):** Variable importance chart — post-hoc power, p-value, effect size, number of authors, discipline are the most important features for both classification and regression Random Forest models. Left side shows LASSO marginal effects.
- **Fig 5 (p.10):** Predicted vs actual results of SSRP out-of-sample test. Triangles = predicted replication, circles = predicted failure. Good separation but some misclassifications.
- **Fig 6 (p.12):** ROC curves for Random Forest on CV and SSRP validation. AUC = 0.71 (CV), 0.78 (SSRP validation).

## Results Summary
The Random Forest model predicts binary replication with 70% cross-validated accuracy (AUC 0.77) on 131 training studies from RPP, EERP, ML1, ML2. The LASSO regression predicts relative effect sizes with Spearman rho = 0.38. The most important predictive features are post-hoc power of the original study, the original p-value, the original effect size, and whether the effect is a main effect vs interaction. On the pre-registered SSRP out-of-sample test (21 studies), accuracy = 71% (AUC 0.73), comparable to prediction markets (71%) and surveys (~67%). The model's predictions are correlated with but not identical to market predictions. Effect size predictions have rho = 0.25 out of sample. The model performs comparably to or slightly worse than prediction markets on SSRP, but it requires no expert time. *(p.6, 8, 10)*

## Limitations
- Small training set (N=131) limits model complexity and generalizability *(p.10)*
- Does not generalize beyond lab experiments in psychology and economics — field experiments, observational studies not tested *(p.11)*
- Cannot capture changes in replication practice over time (increasing power, pre-registration) *(p.11)*
- Interactions between features may not be well captured with only 131 observations *(p.11)*
- The model cannot separate the power increase from increased sample size vs the mechanical increase of replicability from increased sample size *(p.14)*
- Correlation between predicted and actual effect sizes is moderate (r = 0.27 in CV, 0.23 on SSRP) *(p.6, 10)*
- The continuous model produces a ratio of predicted to original effect that has mean absolute deviation of 0.08 on SSRP *(p.10)*
- Sample size of SSRP validation is only 21 studies *(p.8)*

## Arguments Against Prior Work
- Prior approaches to predicting replication rely on expensive expert panels (prediction markets, surveys) requiring significant time investment *(p.1)*
- Simple heuristics like "p-value close to 0.05 won't replicate" capture some but not all predictive power — the ML model adds value beyond single-variable rules *(p.7)*
- The authors argue their model could supplement, not replace, prediction markets by providing a baseline that is nearly free to compute *(p.10)*

## Design Rationale
- **Nested cross-validation:** Avoids overfitting that single-split validation would produce with N=131 *(p.4)*
- **Random Forest chosen over LASSO for classification** because it performed slightly better and handles non-linear interactions *(p.5-6)*
- **LASSO chosen for continuous prediction** because it achieves the highest Spearman correlation *(p.5)*
- **No domain-specific feature transformations beyond log:** To avoid overfitting on small sample; feature space should grow slowly *(p.4)*
- **Used correlation coefficient r as common effect size metric** across all studies to enable pooling across heterogeneous study designs *(p.3)*
- **Asymmetric cost not applied:** Authors note it could be introduced for specific use cases (e.g., funder perspective vs researcher perspective) *(p.12)*
- **Deliberately excluded prediction market data from features** to test what statistical features alone can do *(p.3)*

## Testable Properties
- ML models trained on original study features predict binary replication with accuracy >= 65% on held-out data *(p.6)*
- Original p-value and effect size are among the top 5 most important features for replication prediction *(p.9)*
- Interaction effects replicate at lower rates than main effects *(p.9, p.11)*
- Studies with larger original sample sizes are more likely to replicate *(p.9)*
- The model's predicted replication probabilities correlate positively with prediction market beliefs *(p.10)*
- Adding discipline-specific features (social psych vs cognitive psych vs economics) improves prediction *(p.7, p.9)*
- AUC >= 0.70 achievable with basic statistical features alone (effect size, p-value, sample size) *(p.6)*
- The base rate of replication in the training data is approximately 55% *(p.6)*

## Relevance to Project
This paper is directly relevant to propstore's probabilistic argumentation and belief revision framework. The replication prediction models provide empirical base rates and feature importance rankings that could inform prior probabilities in the argumentation layer. Specifically: (1) the predictive features (effect size, p-value, sample size, interaction vs main) could serve as evidence weights when evaluating competing claims from different studies; (2) the ~70% accuracy ceiling for ML-based replication prediction establishes a calibration benchmark; (3) the comparison with prediction markets provides a cross-validation of belief aggregation methods relevant to the opinion algebra.

## Open Questions
- [ ] How would the model perform on post-2019 replication projects with different norms?
- [ ] Can the model's predicted probabilities serve as priors in Bayesian belief updating for propstore claims?
- [ ] What is the relationship between this model's predictions and subjective logic uncertainty (the u parameter)?

## Related Work Worth Reading
- Open Science Collaboration (2015) RPP — the largest replication project in psychology [ref 1] — already in collection as Aarts_2015
- Camerer et al. (2016) EERP — replication of 18 economics experiments [ref 2] — already in collection as Camerer_2016
- Camerer et al. (2018) SSRP — 21 social science replications [ref 3] — already in collection as Camerer_2018
- Dreber et al. (2015) — prediction markets for RPP replications [ref 5]
- Forsell et al. (2018) — prediction markets and surveys for EERP [ref 6]
- Ioannidis (2005) "Why Most Published Research Findings Are False" [ref 15]
- Begley & Ellis (2012) — drug development replication crisis [ref 18] — already in collection as Begley_2012
- Yang et al. (2020) — estimating replicability using multiple data sources [ref 37]
