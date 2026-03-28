---
title: "Evaluating replicability of laboratory experiments in economics"
authors: "Colin F. Camerer, Anna Dreber, Eskil Forsell, Teck-Hua Ho, Jurgen Huber, Magnus Johannesson, Michael Kirchler, Johan Almenberg, Adam Altmejd, Taizan Chan, Emma Heikensten, Felix Holzmeister, Taisuke Imai, Siri Isaksson, Gideon Nave, Thomas Pfeiffer, Michael Razen, Hang Wu"
year: 2016
venue: "Science"
doi_url: "https://doi.org/10.1126/science.aaf0918"
pages: "351, 1433-1436"
produced_by:
  agent: "Claude Opus 4.6 (1M context)"
  skill: "paper-reader"
  timestamp: "2026-03-28T20:20:53Z"
---
# Evaluating replicability of laboratory experiments in economics

## One-Sentence Summary
Systematic replication of 18 laboratory economics experiments from AER and QJE (2011-2014) finds 61% replicate at p<0.05, with mean replication effect sizes at 66% of originals, and prediction markets/surveys can anticipate which studies will replicate. *(p.1-2)*

## Problem Addressed
The replication crisis had been documented in psychology (Open Science Collaboration 2015) but systematic replication evidence was lacking for experimental economics. This study provides the first large-scale, pre-registered replication effort for high-impact lab economics experiments. *(p.1)*

## Key Contributions
- First systematic replication of economics lab experiments: 18 studies from AER and QJE published 2011-2014 *(p.1)*
- 11 of 18 (61%) replicated with significant effect in same direction at p<0.05 *(p.19)*
- Mean relative effect size of replications is 66% of originals *(p.15)*
- Prediction markets and surveys can predict replication outcomes with moderate accuracy *(p.8-9)*
- Comparison with psychology replication rates (36% in RPP) suggests economics replicates better *(p.10-11)*
- All materials, data, and replication reports publicly available at experimentaleconomics.com *(p.3)*

## Study Design
- **Type:** Systematic replication study with prediction markets and expert surveys
- **Population:** 18 between-subject experimental economics studies published in American Economic Review (AER) and Quarterly Journal of Economics (QJE) between 2011-2014. Selection criteria: (1) published or posted as accepted preprint at journal website by August 1, 2014; (2) at least 90% statistical power to detect original effect *(p.1-2)*
- **Intervention(s):** Direct replications of original experimental protocols, using same software and computer programs where possible. 13 original experiments in English replicated in English; 5 German-language experiments replicated in German. Replications conducted at 4 sites: Stockholm School of Economics, University of Innsbruck, CalTech, and National University of Singapore *(p.2-3)*
- **Comparator(s):** Original study results (effect sizes, p-values) *(p.19)*
- **Primary endpoint(s):** Replication success defined as significant effect (p<0.05) in the same direction as original *(p.2)*
- **Secondary endpoint(s):** (1) Relative effect size (replication r / original r); (2) Whether original effect within 95% CI of replication; (3) Meta-analytic estimate combining original and replication; (4) Prediction market prices; (5) Expert survey beliefs *(p.4-5)*
- **Follow-up:** Replication reports reviewed by original authors; all communications documented *(p.3)*

## Methodology
Each of the 18 studies was replicated with high statistical power (at least 90% to detect original effect at 5% significance). The most central between-subject treatment effect from each original paper was selected for replication. Replications used the same experimental software and protocols. All replications were carried out at least 90% power with predetermined sample sizes. Additionally, prediction markets and pre-market surveys were conducted among economics researchers to forecast replication outcomes. *(p.1-4)*

### Study Selection Protocol *(p.1-2)*
1. Most central result in the paper (among the between-subject treatment comparisons)
2. If more than one equally central result, picked the one related to efficiency (central to economics)
3. If several results still remained from different experiments, followed the RPP Psychology procedure and picked the last experiment
4. In several cases, included results that were also included between subjects and within subjects

### Replication Protocol *(p.2-3)*
- Each replication team wrote a Replication Report detailing the planned replication
- Power analysis: sample size determined for 90% power based on original effect
- Draft report sent to original authors for comments
- Replication Reports posted at experimentaleconomics.com
- All replications pre-registered
- Investments settled in beginning of 2016 according to actual results

## Key Equations / Statistical Models

$$
r_{standardized} = \frac{t}{\sqrt{t^2 + df}}
$$
Where: $t$ is the test statistic, $df$ is degrees of freedom. Used to convert original test statistics to standardized effect sizes (correlation coefficient r). *(p.4)*

$$
r_{relative} = \frac{r_{replication}}{r_{original}}
$$
Where: $r_{relative}$ is the relative effect size, expressing replication effect as fraction of original. *(p.4)*

$$
\text{Power formula: } n = \left(\frac{z_{1-\alpha/2} + z_{1-\beta}}{r}\right)^2 + 3
$$
Where: sample size needed per group based on Fisher transformation of correlation coefficient $r$, with $\alpha=0.05$ and power $1-\beta=0.90$. *(p.4)*

$$
\text{Meta-analytic effect} = \text{Fixed-effect weighted mean using Fisher z-transformation}
$$
Both original and replication studies combined with inverse-variance weighting. *(p.4)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Significance threshold | alpha | - | 0.05 | - | 2 | Two-sided test |
| Statistical power target | 1-beta | - | 0.90 | - | 2 | Minimum power for replications |
| Number of studies replicated | N | count | 18 | - | 1 | From AER and QJE 2011-2014 |
| Replication rate (p<0.05) | - | proportion | 0.611 | - | 19 | 11/18 replicated |
| Mean original effect size | r_orig | correlation | 0.474 | SD=0.239 | 15 | Standardized r |
| Mean replication effect size | r_rep | correlation | 0.279 | SD=0.234 | 15 | Standardized r |
| Mean relative effect size | r_rel | ratio | 0.659 | 95% CI: 0.372-0.947 | 15 | Replication/original |
| Prediction market participants | - | count | 97 | - | 6 | Traders in prediction markets |
| Survey participants | - | count | 140 | - | 6 | Filled in pre-market survey |
| Market endowment | - | Tokens | 100 | - | 7 | Per participant per market |
| Liquidity parameter | P | - | 0.65 | - | 7 | Logarithmic market scoring |
| Number of replication sites | - | count | 4 | - | 2-3 | Stockholm, Innsbruck, CalTech, NUS |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Replication rate (same direction p<0.05) | proportion | 11/18 (61.1%) | - | - | All 18 studies | 19 |
| Original within replication 95% CI | proportion | 12/18 (66.7%) | - | - | All 18 studies | 11 |
| Meta-estimate p<0.05 | proportion | 15/18 (83.3%) | - | - | All 18 studies | 11 |
| Effect size decline (original vs replication) | Wilcoxon z | z=-2.98 | - | 0.003 | n=18 | 15 |
| Mean relative effect size | ratio | 65.9% | 37.2%-94.7% | - | All 18 studies | 15 |
| Spearman: original r vs replication r | rho | 0.48 | - | 0.043 | n=18 | 15 |
| Spearman: market belief vs replicated | rho | 0.297 | - | 0.232 | n=18 | 24 |
| Spearman: survey belief vs replicated | rho | 0.516 | - | 0.028 | n=18 | 24 |
| Spearman: market belief vs relative effect | rho | 0.28 | - | 0.268 | n=18 | 18 |
| Spearman: survey belief vs relative effect | rho | 0.51 | - | 0.030 | n=18 | 18 |
| Spearman: original p-value vs replicated | rho | -0.572 | - | 0.013 | n=18 | 24 |
| Spearman: original sample size vs replicated | rho | 0.627 | - | 0.005 | n=18 | 24 |
| Prediction within 95% prediction intervals | proportion | 15/18 (83.3%) | - | - | All 18 studies | 14 |
| Prediction market correct (>50% threshold) | proportion | >50% | - | - | All 18 studies | 9 |

### Individual Study Results (Table S1, p.19)

| Study | Original r | Replication r | Replicated | Relative r |
|-------|-----------|--------------|------------|------------|
| Abeler et al. (AER 2011) | 0.18 | 0.08 | No | 0.43 |
| Ambrus and Greiner (AER 2012) | 0.31 | 0.23 | Yes | 0.74 |
| Bartling et al. (AER 2012) | 0.72 | 0.66 | Yes | 0.91 |
| Charness and Dufwenberg (AER 2011) | 0.38 | 0.36 | Yes | 0.95 |
| Chen and Chen (AER 2011) | 0.84 | 0.17 | No | 0.20 |
| de Clippel et al. (AER 2014) | 0.12 | 0.27 | Yes | 2.26 |
| Duffy and Puzzello (AER 2014) | 0.76 | -0.12 | No | -0.15 |
| Dulleck et al. (AER 2011) | 0.72 | 0.73 | Yes | 1.01 |
| Ericson and Fuster (QJE 2011) | 0.21 | 0.12 | No | 0.58 |
| Fehr et al. (AER 2013) | 0.45 | 0.31 | Yes | 0.69 |
| Friedman and Oprea (AER 2012) | 0.64 | 0.44 | Yes | 0.68 |
| Fudenberg et al. (AER 2012) | 0.30 | 0.33 | Yes | 1.08 |
| Huck et al. (AER 2011) | 0.83 | 0.37 | No | 0.44 |
| Ifcher and Zarghamee (AER 2011) | 0.28 | -0.01 | No | -0.02 |
| Kessler and Roth (AER 2012) | 0.49 | 0.34 | Yes | 0.71 |
| Kirchler et al. (AER 2012) | 0.66 | 0.53 | Yes | 0.80 |
| Kogan et al. (AER 2011) | 0.32 | 0.30 | Yes | 0.94 |
| Kuziemko et al. (QJE 2014) | 0.28 | -0.12 | No | -0.42 |

## Methods & Implementation Details
- Replications used between-subject treatment comparisons only, as this is the "gold standard" design in economics *(p.1)*
- RCT is a between-subjects treatment comparison, but also common in experimental economics (although not always random allocation) *(p.1)*
- Within-subject designs also used but not the focus of this replication study *(p.2)*
- Same software and computer programs as in original experiments were used to conduct replications, except for replications of Regan et al. (49) where an online application was used *(p.3)*
- Replication teams at each stage: 177 individuals signed up to participate; 140 filled in pre-market survey; 97 participated on prediction market; 79 participated in post-market survey *(p.6)*
- Two largest groups of participants were PhD students and PostDocs (34.4% and 19.8% respectively) *(p.6)*
- Average time spent in academia: 7 years (SD=0.853) *(p.6)*
- Majority of participants in Europe (54.8%) and North America (30.9%) *(p.6)*
- Trading platform: custom web-based with market overview and trading pages *(p.7)*
- Market scoring rule: logarithmic with liquidity parameter P=0.65 *(p.7)*
- 100 Tokens endowment per participant per market; single share price 0.50 to about 0.55 *(p.7)*
- Markets open 2 weeks; pre-market survey completed before 20th; post-market survey had no deadline *(p.6)*
- Investments settled in 2016 according to actual replication results *(p.7-8)*
- All replications carried out with at least 90% statistical power *(p.4)*
- Sample sizes generally larger than originals (some cases actual was somewhat higher than planned) *(p.22)*

## Figures of Interest
- **Fig S1 (p.13):** Forest plot of all 18 replications — Panel A: 95% CIs of standardized replication effect sizes; Panel B: meta-analytic estimates combining original and replication
- **Fig S2 (p.14):** 95% prediction intervals for standardized original effect sizes; 15/18 (83.3%) of replications fall within intervals
- **Fig S3 (p.15):** Scatter plot of original vs replication effect sizes (correlation r); blue dots = replicated (p<0.05), red dots = not replicated; diagonal = equal effect
- **Fig S4 (p.16):** Trading interface screenshots — market overview and individual market trading page
- **Fig S5 (p.17):** Heat map of final positions per participant and market; most traders had broad portfolios across multiple markets
- **Fig S6 (p.18):** Scatter plot of prediction market and survey beliefs vs relative standardized effect size

## Results Summary
11 of 18 (61.1%) replications achieved a statistically significant effect in the same direction as the original at p<0.05. The mean standardized effect size (r) in replications was 0.279 (SD=0.234) compared to 0.474 (SD=0.239) in originals, a significant decline (Wilcoxon z=-2.98, P=0.003). The mean relative effect size was 65.9% (95% CI: 37.2%, 94.7%). Using the broader criterion of whether the original effect falls within the 95% CI of the replication, 12/18 (66.7%) replicated. Meta-analytic combination of original and replication yields 15/18 (83.3%) significant. *(p.15, 19)*

Prediction markets (97 traders) and surveys (140 respondents) were moderately predictive. Survey beliefs correlated with replication outcomes (Spearman rho=0.516, p=0.028) more strongly than market beliefs (rho=0.297, p=0.232). Both correlated with relative effect size (survey: rho=0.51, p=0.030; market: rho=0.28, p=0.268). *(p.9, 18, 24)*

Original p-value negatively correlated with replication success (rho=-0.572, p=0.013) and original sample size positively correlated (rho=0.627, p=0.005), suggesting studies with smaller samples and marginal significance are less likely to replicate. *(p.24)*

## Limitations
- Only 18 studies — small sample limits power of between-study correlations *(p.10)*
- PDF obtained is Supplementary Materials only; main article text (4 pages in Science) not included in this PDF
- Only between-subject treatment effects replicated; within-subject and other designs excluded *(p.1-2)*
- Selection restricted to AER and QJE 2011-2014 — may not generalize to other journals, time periods, or field experiments *(p.1)*
- Comparison with psychology replication (RPP) is imperfect due to different study selection, journals, and time periods *(p.10-11)*
- Prediction market sample size for between-study correlations is only 18 observations *(p.9-10)*

## Arguments Against Prior Work
- Psychology replication rate (36% in RPP, Open Science Collaboration 2015) is lower than economics replication rate (61%), but direct comparison is complicated by different methods and selection criteria *(p.10-11)*
- Prior claims about the unreliability of scientific findings (Ioannidis 2005) apply unevenly across disciplines *(p.24-25)*

## Design Rationale
- Between-subject treatment comparisons chosen because they represent the "gold standard" in economics — the same design used in medicine (RCTs) *(p.1)*
- 90% power threshold chosen to ensure replications are definitive — not ambiguous non-replications due to low power *(p.2)*
- Prediction markets used as aggregation mechanism because prior literature (Arrow et al. 2008, Dreber et al. 2015) suggests markets can aggregate dispersed beliefs about replication *(p.5-6)*
- Pre-registered design with replication reports reviewed by original authors to ensure fidelity *(p.3)*

## Testable Properties
- Replication rate of economics lab experiments should be approximately 61% (11/18) at p<0.05 threshold *(p.19)*
- Mean replication effect sizes should be approximately 66% of original effect sizes *(p.15)*
- Original p-value should be negatively correlated with replication success (lower original p = more likely to replicate) *(p.24)*
- Original sample size should be positively correlated with replication success *(p.24)*
- Prediction markets and expert surveys should predict replication outcomes above chance *(p.8-9)*
- 83% of replications should fall within the 95% prediction interval of original effect sizes *(p.14)*
- Meta-analytic combination of original and replication should yield ~83% significant effects *(p.11)*

## Relevance to Project
This paper provides empirical base rates for replication in economics — critical calibration data for any system reasoning about the reliability of scientific claims. The replication rates, effect size shrinkage patterns, and prediction market data could inform prior probabilities in an argumentation framework when assessing the strength of evidence from economics experiments. The correlation between original p-values/sample sizes and replication success provides concrete evidence for weighing claim strength based on study characteristics.

## Open Questions
- [ ] How do these economics replication rates compare with more recent replication efforts (e.g., Camerer et al. 2018 for social sciences in Nature)?
- [ ] Can the prediction market methodology be used to calibrate prior beliefs about claim reliability in propstore?
- [ ] Would the p-value/sample-size predictors of replication success be useful as features in claim strength estimation?

## Related Work Worth Reading
- Open Science Collaboration (2015). "Estimating the reproducibility of psychological science." Science 349, aac4716. (DOI: 10.1126/science.aac4716) — The psychology replication project that motivated this study *(p.25)*
- Dreber et al. (2015). "Using prediction markets to estimate the reproducibility of scientific research." PNAS 112, 15343-15347. — Prediction markets for RPP psychology replications *(p.26)*
- Ioannidis (2005). "Why most published research findings are false." PLOS Medicine 2, e124. — Foundational paper on publication bias and false findings *(p.25)*
- Cumming (2008). "Replication and p intervals: p values predict the future only vaguely, but confidence intervals do much better." Perspect. Psychol. Sci. 3, 286-300. *(p.25)*
- Simonsohn (2015). "Small telescopes: Detectability and the evaluation of replication results." Psychol. Sci. 26, 559-569. *(p.25)*

## Collection Cross-References

### Papers in collection cited by this paper
- **Aarts_2015_EstimatingReproducibilityPsychologicalScience** — Cited as ref 19 (Open Science Collaboration 2015). The psychology replication project (RPP) that directly motivated this economics replication study. Camerer et al. compare their 61% replication rate to RPP's 36%.
- **Begley_2012_DrugDevelopmentRaiseStandards** — Cited as ref 4 (Begley & Ellis 2012). Motivating context for the replication crisis in preclinical cancer research.
- **Guo_2017_CalibrationModernNeuralNetworks** — Not directly cited, but methodologically related through calibration concepts.

### Collection papers that cite or follow up on this paper
- **Camerer_2018_EvaluatingReplicabilitySocialScience** — Follow-up study by same lead author extending replication methodology to social science experiments published in Nature and Science.
- **Errington_2021_InvestigatingReplicabilityPreclinicalCancer** — Related replication effort in preclinical cancer biology.

### New Leads
- Dreber et al. (2015). "Using prediction markets to estimate the reproducibility of scientific research." PNAS 112, 15343-15347. DOI: 10.1073/pnas.1516179112
- Ioannidis (2005). "Why most published research findings are false." PLOS Medicine 2, e124. DOI: 10.1371/journal.pmed.0020124
- Simonsohn (2015). "Small telescopes." Psychol. Sci. 26, 559-569. DOI: 10.1177/0956797614567341
