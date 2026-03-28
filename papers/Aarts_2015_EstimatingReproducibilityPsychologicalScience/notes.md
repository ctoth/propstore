---
title: "Estimating the reproducibility of psychological science"
authors: "Open Science Collaboration (270+ contributors; coordinated by Brian A. Nosek)"
year: 2015
venue: "Science"
doi_url: "https://doi.org/10.1126/science.aac4716"
pages: 10
produced_by:
  agent: "Claude Opus 4.6 (1M context)"
  skill: "paper-reader"
  timestamp: "2026-03-28T20:19:32Z"
---
# Estimating the reproducibility of psychological science

## One-Sentence Summary
A large-scale direct replication of 100 experimental and correlational studies from three psychology journals finds that replication effect sizes are roughly half the originals and only 36% of replications achieve statistical significance, providing the first systematic empirical estimate of reproducibility rates in psychological science.

## Problem Addressed
Reproducibility is a defining feature of science, but until this study no systematic, large-scale attempt had been made to estimate the rate at which published psychological findings actually replicate. Prior concerns were based on theoretical arguments (publication bias, underpowered studies, analytic flexibility) rather than direct empirical evidence. *(p.1)*

## Key Contributions
- First large-scale, pre-registered, direct replication attempt of 100 studies from three major psychology journals *(p.1)*
- Multiple convergent indicators of reproducibility (significance, effect size, confidence intervals, subjective assessment, meta-analytic combination) *(p.1)*
- Identification of predictors of replication success: original p-value strength and effect size magnitude *(p.5-6)*
- Demonstrated that cognitive psychology replicates at higher rates than social psychology *(p.5-6)*
- Open materials: all protocols, data, and analysis scripts publicly available via Open Science Framework *(p.2)*

## Study Design (empirical papers)
- **Type:** Large-scale direct replication study (systematic replication of 100 published experiments) *(p.1-2)*
- **Population:** 100 studies sampled from three journals — Journal of Personality and Social Psychology (JPSP), Journal of Experimental Psychology: Learning, Memory, and Cognition (JEP:LMC), and Psychological Science (PSCI) — all published in 2008. One key effect per article selected. *(p.2)*
- **Intervention(s):** Each replication closely followed the original study's methods; replication protocols vetted by original authors when possible. *(p.2)*
- **Comparator(s):** Original study results served as comparators. *(p.2)*
- **Primary endpoint(s):** Statistical significance of replication (p < .05), replication effect size (r), whether original effect CI contains replication effect. *(p.2-3)*
- **Secondary endpoint(s):** Subjective replication assessment, meta-analytic combination of original + replication. *(p.3-4)*
- **Follow-up:** N/A (cross-sectional replication study).

## Methodology
Replications were designed as close/direct replications: same procedures, materials, and samples as feasible. Replication protocols were reviewed by original authors when available. Each replication used the same statistical test as the original. Power analysis targeted 80% power at the original effect size for most replications; when this required infeasible sample sizes, replications used at least the original N or 80% power at a "small" effect size. *(p.2)*

Five indicators of reproducibility were used *(p.2-3)*:
1. **Significance and direction:** Does the replication achieve p < .05 in the same direction?
2. **Effect size comparison:** How large is the replication effect relative to the original?
3. **Subjective assessment:** Replication team's judgment of whether the effect replicated.
4. **Meta-analytic estimate:** Combining original and replication with fixed-effect meta-analysis — is the combined result significant?
5. **Confidence interval inclusion:** Does the 95% CI of the original effect contain the replication point estimate?

Statistical analyses used Spearman rank correlations, Fisher z-transformations, Wilcoxon signed-rank tests, and comparison of P-value distributions (Q-Q plots). *(p.3-4)*

## Key Equations / Statistical Models

$$
r = \sqrt{\frac{F(1, N-2)}{F(1, N-2) + (N-2)}}
$$
Where: r = correlation coefficient converted from F-statistic; F = F-test value; N = sample size. Used to convert all test statistics to a common effect size metric. *(p.2)*

$$
r = \sqrt{\frac{t^2}{t^2 + df}}
$$
Where: r = correlation coefficient converted from t-statistic; t = t-test value; df = degrees of freedom. *(p.2)*

$$
r = \sqrt{\frac{\chi^2}{N}}
$$
Where: r = correlation coefficient converted from chi-squared; chi-squared = test statistic; N = sample size. *(p.2)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of studies replicated | N | count | 100 | — | 1 | From 3 journals published in 2008 |
| Original significance rate | — | % | 97 | — | 1 | Percentage of original studies with p < .05 |
| Replication significance rate | — | % | 36 | — | 1 | Percentage of replications with p < .05 |
| Mean original effect size | r | — | 0.403 | — | 4 | Mean correlation coefficient across originals |
| Mean replication effect size | r | — | 0.197 | — | 4 | Mean correlation coefficient across replications |
| Median original effect size | r | — | 0.374 | — | 4 | Median correlation coefficient across originals |
| Median replication effect size | r | — | 0.129 | — | 4 | Median correlation coefficient across replications |
| Original-replication effect size correlation | r | — | 0.51 | — | 5 | Spearman correlation between original and replication r values |
| CI overlap rate | — | % | 47 | — | 1 | Percentage of original 95% CIs containing replication effect |
| Subjective replication rate | — | % | 39 | — | 1 | Percentage rated as replicated by replication teams |
| Meta-analytic significance rate | — | % | 68 | — | 1 | Combined original+replication significance rate |
| Replication power (at original effect) | — | % | 92 | — | 4 | Mean statistical power of replications for detecting original effect sizes |
| Studies from JPSP | — | count | 55 | — | 2 | Journal of Personality and Social Psychology |
| Studies from PSCI | — | count | 27 | — | 2 | Psychological Science |
| Studies from JEP:LMC | — | count | 18 | — | 2 | Journal of Experimental Psychology: Learning, Memory, and Cognition |
| Cognitive psychology replication significance rate | — | % | 50 | — | 5 | 21 of 42 cognitive studies replicated |
| Social psychology replication significance rate | — | % | 25 | — | 5 | 14 of 55 social studies replicated |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Replication significance rate | proportion | 0.36 | — | — | All 100 studies | 1 |
| Mean effect size decline | difference in r | -0.206 | — | — | Original r=0.403 vs replication r=0.197 | 4 |
| Effect size correlation (orig vs rep) | Spearman r | 0.51 | — | p < .001 | All 100 studies | 5 |
| Cognitive replication rate | proportion | 0.50 | — | — | 42 cognitive studies | 5 |
| Social replication rate | proportion | 0.25 | — | — | 55 social studies | 5 |
| Meta-analytic significance rate | proportion | 0.68 | — | — | Combined original+replication | 1 |
| CI overlap rate | proportion | 0.47 | — | — | Replication r within original 95% CI | 1 |
| Surprising findings replication rate | proportion | 0.24 | — | — | Self-rated "surprising" originals | 6 |
| Non-surprising findings replication rate | proportion | 0.28 | — | — | Self-rated "not surprising" originals | 6 |
| Experienced team replication rate vs inexperienced | comparison | no significant difference | — | — | Team domain expertise | 6 |

## Methods & Implementation Details
- Effect sizes converted to correlation coefficients (r) using standard formulas for F, t, chi-squared, and z statistics *(p.2)*
- For replications where original effect size would require infeasible N for 80% power, used original N or 80% power at small effect as minimum *(p.2)*
- Original authors contacted for materials and protocol review; most cooperated *(p.2)*
- Statistical significance defined as p < .05, same direction as original *(p.2)*
- Test statistics extracted from original papers; when not reported, computed from available statistics *(p.2)*
- Fisher z-transformation applied before averaging correlation coefficients *(p.2)*
- Wilcoxon signed-rank test used to compare original vs replication P-value distributions *(p.3)*
- Q-Q plot used to visualize P-value distributions *(p.4, Fig.1)*
- Replication protocols pre-registered on Open Science Framework before data collection *(p.2)*
- Each replication team included at least one experienced researcher in the relevant domain *(p.2)*

## Figures of Interest
- **Fig 1 (p.1):** Original study effect size vs replication effect size (correlation coefficients). Diagonal = perfect replication. Shows systematic shrinkage toward zero.
- **Fig 1 inset (p.1):** Effect sizes sorted by original effect size with 95% CIs for both original and replication.
- **Fig 2 (p.5):** Scatterplot of original and replication P-values for three reproducibility indicators, with power of replication based on original effect size. Shows most replications fall short.
- **Fig 3 (p.6):** Original effect size vs. replication effect size estimation (correlation coefficients). Diagonal line shows where replications would fall if effect sizes were identical. Dotted line is the regression fit.
- **Table 1 (p.3):** Summary of reproducibility rates and effect sizes for original and replication studies overall and by journal/discipline.
- **Table 2 (p.3):** Spearman rank correlations of reproducibility indicators with summary original and replication study characteristics. Key finding: original P-value and effect size are the best predictors of replication success.

## Results Summary
Across all five reproducibility indicators, the evidence consistently shows a substantial decline in reproducibility *(p.4-5)*:
- Only 36% of replications achieved p < .05 (vs 97% of originals) *(p.1)*
- Mean replication effect size was roughly half the original (r = 0.197 vs 0.403) *(p.4)*
- 47% of original 95% CIs contained the replication effect size *(p.1)*
- 39% of replications were subjectively rated as successful *(p.1)*
- Combining original and replication via meta-analysis, 68% remained significant *(p.1)*
- Replication success was predicted by strength of original evidence: lower original P-values and larger effect sizes predicted successful replication *(p.5)*
- Cognitive psychology replicated at twice the rate of social psychology (50% vs 25%) *(p.5)*
- Surprising findings did not replicate at significantly different rates from non-surprising ones (24% vs 28%) *(p.6)*
- Replication team expertise and experience did not significantly predict replication success *(p.6)*

## Limitations
- Only sampled from three journals in one year (2008), limiting generalizability *(p.6)*
- Each study replicated only once — a single failure does not definitively establish non-reproducibility *(p.6)*
- "Direct" replications are never exact — differences in samples, settings, and minor procedural details could account for some failures *(p.6)*
- Replications typically used American or online samples that may differ from original populations *(p.6)*
- Selection bias: only one effect per article selected, and articles with simpler designs may have been preferentially chosen *(p.2)*
- Cannot distinguish between false positives in originals vs contextual sensitivity (true effects that depend on specific conditions) *(p.6)*
- Although protocols were pre-registered and vetted, fidelity to original methods was variable *(p.6)*
- The study cannot determine the rate of false positives vs true but context-dependent effects *(p.7)*

## Arguments Against Prior Work
- Challenges the assumption that published results in top journals are reliable. The 97% significance rate in originals is "unrealistically high" and is itself evidence of selection bias in publication *(p.4)*
- Argues against the view that non-replication is primarily due to "hidden moderators" — surprising findings (which might invoke such moderators) did not replicate at different rates than non-surprising ones *(p.6)*
- Criticizes publication and reporting practices that inflate false positive rates: publication bias, underpowered studies, P-hacking, HARKing *(p.1, p.6-7)*

## Design Rationale
- Chose direct/close replication rather than conceptual replication to isolate reproducibility from construct validity issues *(p.2)*
- Pre-registered protocols to prevent analytic flexibility in replications *(p.2)*
- Used multiple indicators of reproducibility because no single indicator is definitive *(p.2)*
- Converted all effect sizes to r for comparability across different statistical tests *(p.2)*
- Included original author review of protocols to maximize fidelity *(p.2)*
- Targeted 80% power at original effect size to give adequate chance of detecting the effect if real *(p.2)*

## Testable Properties
- Replication significance rate for psychology studies is approximately 36% (at p < .05 threshold) *(p.1)*
- Mean replication effect size is approximately half the original effect size (r = 0.197/0.403 ≈ 0.49) *(p.4)*
- Original P-value is a significant predictor of replication success: lower original P predicts higher replication probability *(p.5)*
- Original effect size magnitude is a significant predictor of replication success *(p.5)*
- Cognitive psychology replicates at approximately 2x the rate of social psychology *(p.5)*
- Team expertise does not significantly predict replication success *(p.6)*
- Surprising vs non-surprising findings do not differ in replication rates *(p.6)*
- Combining original + replication via meta-analysis yields approximately 68% significance rate *(p.1)*
- If original effect is real, combining original and replication should increase rather than decrease evidence *(p.5)*

## Relevance to Project
This paper provides empirical base rates for the reliability of published scientific claims. For a propstore system that ingests claims from scientific literature, these findings establish that:
1. Approximately 36-47% of published psychology findings may not replicate, meaning claims extracted from papers carry substantial uncertainty.
2. Strength of original evidence (P-value, effect size) is the best available predictor of claim reliability.
3. Domain matters: cognitive claims are more reliable than social psychology claims.
4. These base rates can inform prior probabilities in the opinion algebra (Josang 2001) — a published claim without replication evidence should carry substantial uncertainty (u ≈ 0.5-0.6).

## Open Questions
- [ ] How do replication rates vary across other scientific disciplines (medicine, economics, biology)?
- [ ] Can the predictors identified (original P-value, effect size) be used to build a calibrated reliability prior for claims?
- [ ] How should meta-analytic combination of original + replication map onto subjective logic opinion fusion?
- [ ] What is the appropriate base rate to use for claims from journals not sampled in this study?

## Collection Cross-References

### Already in Collection (not yet indexed)
- Begley_2012_DrugDevelopmentRaiseStandards — cited as preclinical biology replication study (11% replication rate)
- Camerer_2016_EvaluatingReplicabilityLaboratoryExperiments — cited as economics replication extension (61% replication rate)
- Camerer_2018_EvaluatingReplicabilitySocialScience — related replication study in social sciences
- Errington_2021_InvestigatingReplicabilityPreclinicalCancer — related replication study in preclinical cancer research

### New Leads (Not Yet in Collection)
- Ioannidis (2005) — "Why most published research findings are false" — theoretical framework for replication failure rates
- Simmons, Nelson & Simonsohn (2011) — "False-positive psychology" — demonstrates P-hacking mechanism
- Klein et al. (2014) — "Many Labs" replication project — multi-site replication of 13 classic effects
- Button et al. (2013) — "Power failure" in neuroscience — systematic underpowering documentation
- Cumming (2014) — "The new statistics: why and how" — statistical reform proposals

## Related Work Worth Reading
- Camerer et al. (2016) "Evaluating replicability of laboratory experiments in economics" — extends to economics
- Ioannidis (2005) "Why most published research findings are false" — theoretical framework for these results
- Begley & Ellis (2012) "Drug development: raise standards for preclinical cancer research" — 11% replication in preclinical biology
- Simmons, Nelson & Simonsohn (2011) "False-positive psychology" — demonstrates P-hacking
- Cumming (2014) "The new statistics: why and how" — reform proposals
- Nosek et al. (2015) "Promoting an open research culture" — Transparency and Openness Promotion guidelines
