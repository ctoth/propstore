---
title: "A Step Toward Quantifying Independently Reproducible Machine Learning Research"
authors: "Edward Raff"
year: 2021
venue: "AAAI Conference on Artificial Intelligence"
doi_url: "https://arxiv.org/abs/2012.09932"
---

# A Step Toward Quantifying Independently Reproducible Machine Learning Research

## One-Sentence Summary
An empirical survival analysis of 255 ML papers quantifying which paper-level features predict independent reproducibility, finding that paper readability, pseudo code availability, and number of equations are the strongest predictors. *(p.1)*

## Problem Addressed
There is increasing concern about a reproducibility crisis in ML/AI research, but most discussion has been qualitative. Unlike psychology (which has large-scale replication projects like Aarts et al. 2015), ML lacks systematic quantitative study of what makes papers reproducible. This paper treats reproducibility as a survival analysis problem: a paper is either reproducible or not, and the time it takes to reproduce it is the outcome variable. *(p.1)*

## Key Contributions
- First quantitative survival analysis of ML reproducibility using 255 papers with binary reproducibility outcomes and time-to-reproduce data *(p.1)*
- Cox proportional hazard model identifying statistically significant features that predict reproducibility *(p.3)*
- XGBoost + SHAP analysis providing non-linear feature importance and interaction effects *(p.4-6)*
- Finding that paper readability (Cix metric) is the single most impactful feature, followed by pseudo code availability *(p.5-6)*
- Robustness analysis showing results hold under mean vs median imputation *(p.10)*

## Study Design
- **Type:** Retrospective cohort / survival analysis *(p.1)*
- **Population:** N=255 ML papers spanning multiple venues and years, with 162 successfully reproduced and 93 not reproduced *(p.2)*
- **Intervention(s):** N/A (observational study of paper features)
- **Comparator(s):** Reproduced vs not-reproduced papers
- **Primary endpoint(s):** Binary reproducibility outcome (reproduced or not) and time to reproduce *(p.2)*
- **Secondary endpoint(s):** Feature importance rankings via SHAP values
- **Follow-up:** Variable; reproduction attempts span from days to years *(p.2)*

## Methodology
The author attempted to independently reproduce 255 ML papers over several years, recording binary outcomes (success/failure) and time spent. Papers that were not reproduced are right-censored in the survival model (time spent is a lower bound). Features were extracted from each paper including: readability metrics, structural features (equations, tables, figures, proofs, pages, references), metadata (year published, year attempted, venue), and qualitative assessments (algorithm difficulty, rigor vs empirical, looks intimidating, pseudo code availability, code/data availability). *(p.1-2)*

Two modeling approaches used:
1. Cox Proportional Hazard (PH) model - semi-parametric survival model *(p.3)*
2. XGBoost with SHAP interaction values for non-linear analysis *(p.4-6)*

For non-reproduced papers, time is right-censored: the actual time to failure is >= the observed time. The author uses mean imputation for non-reproduced papers' time values in the main analysis, with median imputation as robustness check. *(p.2)*

## Key Equations / Statistical Models

$$
h(t | x) = h_0(t) \exp(\beta^T x)
$$
Where: $h(t|x)$ is the hazard function at time $t$ given covariates $x$, $h_0(t)$ is the baseline hazard, $\beta$ are the coefficients, $x$ are the feature values.
*(p.3)*

The Cox model provides a number of benefits: it does not require distributing assumptions about the baseline hazard $h_0(t)$, it allows right-censoring naturally, and it allows estimation of feature importance via $\beta$ coefficients. *(p.3)*

$$
S(t) = \exp\left(-\int_0^t h(u) du\right)
$$
Where: $S(t)$ is the survival function (probability of not being reproduced by time $t$).
*(p.1)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of papers | N | count | 255 | - | 2 | Total dataset size |
| Reproduced papers | - | count | 162 | - | 2 | 63.5% success rate |
| Not reproduced | - | count | 93 | - | 2 | Right-censored observations |
| Significance threshold | alpha | - | 0.05 | - | 3 | Also consider 0.1 for marginal |
| XGBoost eta | eta | - | 0.0213 | - | 10 | Learning rate |
| XGBoost max_depth | - | - | 8 | - | 10 | Tree depth |
| XGBoost subsample | - | - | 0.202 | - | 10 | Row sampling |
| XGBoost colsample_bytree | - | - | 0.370 | - | 10 | Column sampling per tree |
| XGBoost colsample_bylevel | - | - | 0.709 | - | 10 | Column sampling per level |
| XGBoost lambda | - | - | 1.498 | - | 10 | L2 regularization |
| XGBoost boost_rounds | - | - | 120 | - | 10 | Number of boosting rounds |
| Cross-validated concordance (mean) | - | - | 0.77 | - | 4 | XGBoost model |
| Cross-validated concordance (median) | - | - | 0.76 | - | 10 | XGBoost model with median imputation |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Paper Readability -> reproducibility | Cox coeff (log-HR) | significant | - | <0.005 | All 255 papers, mean imputation | 4 |
| Pseudo Code -> reproducibility | Cox coeff (log-HR) | significant | - | <0.005 | All 255 papers, mean imputation | 4 |
| Rigor vs Empirical -> reproducibility | Cox coeff (log-HR) | significant | - | 0.02 | All 255 papers, mean imputation | 4 |
| Algorithm Difficulty -> reproducibility | Cox coeff (log-HR) | significant | - | 0.03 | All 255 papers, mean imputation | 4 |
| Has Appendix -> reproducibility | Cox coeff (log-HR) | marginal | - | 0.07 | All 255 papers, mean imputation | 4 |
| Year Attempted -> reproducibility | Cox coeff (log-HR) | significant | - | 0.02 | All 255 papers, mean imputation | 4 |
| Normalized Num Equations (linear) | Cox p-value | 4.30 | - | 0.18 | Linear model test | 3 |
| Year Attempted (linear) | Cox p-value | 5.78 | - | 0.02 | Linear model test | 3 |
| Paper readability (linear Cox) | p-value | - | - | <0.005 | Mean and median imputation | 10 |
| Pseudo Code (linear Cox) | p-value | - | - | <0.005 | Mean and median imputation | 10 |

## Methods & Implementation Details
- Features extracted from each paper include 23 variables: Year Published, Year Attempted, Has Appendix, Uses Exemplary Toy Problem, Looks Intimidating, Exact Compute Used, Data Available, Code Available, Number of Authors, Pages, Num References, Number of Equations, Number of Proofs, Number of Tables, Number of Graphs/Plots, Number of Other Figures, Conceptualization Figures, Hyperparameters Specified, Algorithm Difficulty, Paper Readability (Cix), Pseudo Code, Compute Needed, Rigor vs Empirical *(p.2-3)*
- Paper readability measured using the Cix metric (Coleman-Liau index variant) *(p.3)*
- Numeric features normalized by dividing by number of pages (e.g., "Normalized Number of Equations" = equations/pages) *(p.3)*
- Cox PH model tested for proportional hazard assumption using Schoenfeld residuals; only "Normalized Number of Equations" and "Year Attempted" violated the assumption *(p.3)*
- Kaplan-Meier curves and log-rank tests used for categorical features *(p.3)*
- XGBoost hyperparameters tuned via Optuna with cross-validation *(p.9-10)*
- Concordance index used as evaluation metric (analogous to AUC for survival models) *(p.4)*
- SHAP interaction values used for interpretability, showing both main effects and pairwise feature interactions *(p.5)*
- Data and code made available as part of the JSAT library *(p.2)*

## Figures of Interest
- **Fig 1 (p.2):** Histogram of time taken to reproduce papers. Dark blue = Kaplan-Meier estimate of density. Dashes on x-axis indicate specific paper values.
- **Fig 2 (p.5):** SHAP individual features (change in log-hazard ratio) for numeric features. Each subplot shows feature value on x-axis, SHAP value on y-axis, colored by highest-interaction second feature. Covers: Equations, Pages, Proofs, References, Tables, Graphs, Year of Publication, Year Attempted, Conceptualization Figures.
- **Fig 3 (p.6):** SHAP results for all features showing log-hazard change. Includes both numeric and categorical features.
- **Fig 4 (p.9):** Residual errors for Normalized Number of Equations and Year Attempted showing non-linear relationship that violated Cox PH assumptions.
- **Fig 5 (p.11):** SHAP individual features comparing mean vs median imputation for equations, pages, proofs, references.
- **Fig 6 (p.12):** Continuation of Fig 5 for tables, graphs, year published, year attempted, conceptualization figures.

## Results Summary
The most important finding is that **paper readability** (measured by the Cix index) is the single most impactful feature for ML reproducibility. Papers that are more readable are significantly more likely to be reproduced. *(p.5-6)*

**Pseudo code** availability is the second most important factor (p < 0.005 in both mean and median Cox models). *(p.4, 10)*

**More equations** correlate with higher reproducibility, but the relationship is non-linear — there are diminishing returns, and the SHAP analysis reveals interactions with readability. *(p.5-6)*

**Longer papers** (more pages) tend to have reduced reproduction time, suggesting more detail helps reproducers. However, the relationship is also non-linear. *(p.6)*

**Tables per page** have a narrow range in which they reduce reproduction time, after which the value decays. *(p.6)*

**Code availability** did NOT find evidence of being a significant factor in the Cox model (p=0.18 mean, p=0.28 median), though the SHAP analysis shows some positive contribution. *(p.4, 10)*

**Year Attempted** is significant — later reproduction attempts are easier, possibly due to improved tooling and frameworks. *(p.3-4)*

Results are robust to using median instead of mean imputation for right-censored observations. *(p.10)*

## Limitations
- Single reproducer (the author), introducing potential bias — results may be influenced by author's specific expertise and background *(p.7)*
- Dataset of 255 papers may not be representative of all ML research *(p.7)*
- Readability measured only within "the context of the main paper" — pseudo code and equations counted separately *(p.6)*
- The Cox model's proportional hazard assumption is violated for two features (Normalized Number of Equations and Year Attempted), requiring careful interpretation *(p.3, 9)*
- Non-reproduced papers' time values are right-censored — the actual time needed could be much longer *(p.2)*
- Binary outcome (reproduced/not) doesn't capture degrees of reproducibility *(p.1)*
- Author acknowledges this is "a step toward" — larger multi-person studies needed *(p.7)*

## Arguments Against Prior Work
- Prior reproducibility discussions in ML have been qualitative, lacking systematic quantitative analysis *(p.1)*
- Psychology's reproducibility projects (Aarts et al. 2015, Camerer et al. 2016, 2018) provided inspiration but ML needed its own quantitative approach *(p.1)*
- Existing surveys about reproducibility factors (e.g., Gundersen & Kjensmo 2018) asked questions without building predictive models *(p.2)*

## Design Rationale
- Survival analysis chosen because it naturally handles right-censoring of non-reproduced papers — we know the attempt lasted at least X days, but don't know the true time to reproduce *(p.1)*
- Cox PH model chosen because it doesn't require distributional assumptions about the baseline hazard, only that features have proportional effects *(p.3)*
- XGBoost + SHAP used as complement to Cox model to capture non-linear feature interactions that the Cox model cannot *(p.4)*
- Features normalized by page count to control for paper length effects *(p.3)*
- Both mean and median imputation tested to demonstrate robustness *(p.10)*

## Testable Properties
- Paper readability (Cix) should have p < 0.005 in Cox PH model predicting reproducibility *(p.4)*
- Pseudo code availability should have p < 0.005 in Cox PH model *(p.4)*
- Increasing number of equations per page should increase reproducibility probability (up to a point) *(p.5)*
- Code availability alone is NOT a significant predictor of reproducibility (p > 0.1) *(p.4)*
- XGBoost concordance index for reproducibility prediction should be ~0.77 *(p.4)*
- Results should be qualitatively similar under mean vs median imputation *(p.10)*
- Rigor vs Empirical orientation should be significant at p < 0.05 *(p.4)*

## Relevance to Project
This paper provides empirical evidence about what makes research reproducible — directly relevant to meta-scientific reasoning about evidence quality. The survival analysis methodology and the specific features identified (readability, pseudo code, equations) could inform how propstore weights evidence quality or assesses claim reliability. The paper's treatment of reproducibility as a measurable, predictable property aligns with propstore's goal of formal reasoning about evidence.

## Open Questions
- [ ] How does the Cix readability metric specifically work? Coleman-Liau index variant details not fully specified
- [ ] Would the results hold with a larger, multi-author reproducibility study?
- [ ] How do these findings interact with domain-specific factors (e.g., NLP vs computer vision vs reinforcement learning)?

## Related Work Worth Reading
- Aarts et al. 2015 — "Estimating the reproducibility of psychological science" (large-scale replication project) — already in collection
- Camerer et al. 2016, 2018 — Replication studies in economics/social science — already in collection
- Gundersen & Kjensmo 2018 — State of reproducibility in AI
- Begley & Ellis 2012 — Drug development reproducibility — already in collection
- Altmejd et al. 2019 — Predicting replication outcomes — already in collection
- Pineau et al. 2020 — ML reproducibility checklist
- Henderson et al. 2018 — Deep RL reproducibility issues
