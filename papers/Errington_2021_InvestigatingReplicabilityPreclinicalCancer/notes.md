---
title: "Investigating the replicability of preclinical cancer biology"
authors: "Timothy M Errington, Maya Mathur, Courtney K Soderberg, Alexandria Denis, Nicole Perfito, Elizabeth Iorns, Brian A Nosek"
year: 2021
venue: "eLife"
doi_url: "https://doi.org/10.7554/eLife.71601"
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-03-28T20:23:09Z"
---
# Investigating the replicability of preclinical cancer biology

## One-Sentence Summary
This paper reports the results of the Reproducibility Project: Cancer Biology (RPCB), which systematically replicated 50 experiments from 23 high-impact preclinical cancer biology papers, finding that replication effect sizes were approximately 85% smaller than original effect sizes and that replicability varied substantially depending on which of seven criteria was used to assess it. *(p.1)*

## Problem Addressed
Replicability is an important feature of scientific research, but aspects of contemporary research culture (emphasis on novelty) may make replicability seem less important than it should be. The RPCB was set up to provide evidence about the replicability of preclinical research in cancer biology by repeating selected experiments from high-impact articles. Prior to this, there was limited systematic evidence about how well preclinical cancer biology findings replicate. *(p.1)*

## Key Contributions
- Conducted systematic replications of 50 experiments from 23 high-impact preclinical cancer biology papers, generating 158 effects across 188 total outcomes *(p.1)*
- Applied seven distinct replication criteria and showed that replication rates range from 3% to 82% depending on which criterion is used *(p.1, p.4)*
- Demonstrated that replication effect sizes were approximately 85% smaller than original effect sizes on average *(p.1)*
- Found none of five candidate moderators showed a consistent, significant association with replication success *(p.14)*
- Provided evidence that smaller effects were less likely to replicate, and animal experiments were less likely to replicate than non-animal experiments *(p.12, p.16)*
- Combined original and replication data via meta-analysis to produce updated estimates of effect sizes *(p.10-11)*

## Study Design
- **Type:** Systematic replication study (multi-site, pre-registered replications) *(p.1)*
- **Population:** 50 experiments from 23 papers selected from 53 high-impact papers published 2010-2012 in cancer biology; original selection was based on top-cited papers in the field from 2010 to 2012 *(p.1, p.22)*
- **Intervention(s):** Independent replication of selected experiments following Registered Reports with pre-registered protocols reviewed by original authors *(p.2, p.22)*
- **Comparator(s):** Original experimental results from the 23 papers *(p.2)*
- **Primary endpoint(s):** Seven replication criteria applied to 158 effects: (1) same direction, (2) direction and statistical significance, (3) original ES in replication CI, (4) replication ES in original CI, (5) replication ES in prediction interval, (6) replication ES >= original ES, (7) meta-analysis p < 0.05 *(p.3)*
- **Secondary endpoint(s):** Moderator analysis (animal vs non-animal, CRO lab, core lab, materials shared, clarifications quality); effect size comparisons; null hypothesis significance testing *(p.14, p.5-6)*
- **Follow-up:** N/A (single replication attempt per experiment) *(p.22)*

## Methodology
The Reproducibility Project: Cancer Biology initially identified 193 experiments from 53 high-impact papers published 2010-2012. Due to challenges (barriers in documentation, methodological difficulties, resource constraints), only 50 experiments from 23 papers were completed. Replications were conducted by contract research organizations (CROs) or academic core labs, following pre-registered Registered Report protocols that were peer-reviewed and included input from original authors. Each replication used a pre-specified power analysis (80% power to detect the original effect size). Seven criteria were used to assess replication success. Effect sizes were calculated as standardized mean differences (SMD/Cohen's d). Meta-analyses combined original and replication data using robust variance estimation. *(p.1-2, p.22-23)*

The study distinguished between "original positive results" (where original authors interpreted data as showing a relationship) and "original null results" (no evidence for a relationship). Of 158 effects reported in the original papers, 136 (86%) were positive and 22 (14%) were null. *(p.3)*

## Key Equations / Statistical Models

$$
p_{\text{orig}}
$$
Where: $p_{\text{orig}}$ is the p-value from the original study, used to construct a 95% prediction interval for the replication effect size, assuming the original effect is the true effect and the replication is adequately powered. *(p.6-7)*

$$
\hat{\mu}_{\text{meta}} = f(\text{ES}_{\text{orig}}, \text{ES}_{\text{rep}}, \text{SE}_{\text{orig}}, \text{SE}_{\text{rep}})
$$
Where: $\hat{\mu}_{\text{meta}}$ is the meta-analytic combined effect size from robust variance estimation combining original and replication effect sizes with appropriate standard errors. The hierarchical model accounts for correlated outcomes within papers, experiments, and effects. *(p.8, p.23)*

The authors used robust variance estimation (RVE) with correlated effects working model to handle the hierarchical structure: effects nested within experiments, experiments nested within papers. The meta-analytic model used small-sample corrections (Satterthwaite degrees of freedom). *(p.23)*

For moderator analysis, point-biserial correlations were computed between five binary candidate moderators and replication success metrics. A mixed-effects meta-regression was also fitted with all five moderators simultaneously. *(p.14, p.24)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of papers replicated | — | count | 23 | — | 1 | From original 53 selected |
| Number of experiments replicated | — | count | 50 | — | 1 | From original 193 identified |
| Number of effects (total outcomes) | — | count | 188 | — | 4 | Across all replications |
| Number of effects analyzed | — | count | 158 | — | 4 | Excluding effects where criteria could not be applied |
| Original positive effects | — | count | 136 | — | 3 | 86% of 158 |
| Original null effects | — | count | 22 | — | 3 | 14% of 158 |
| Original positive effect size median (SMD) | — | d | 0.63 | IQR 0.15-1.80 | 9 | Standardized mean difference |
| Replication effect size median (SMD) | — | d | 0.30 | IQR 0.01-0.96 | 9 | For original positive effects |
| Mean original-replication effect size (original positive, SMD) | — | d | 1.38 | SD 1.85 | 9 | Original positive numerical results |
| Mean replication effect size (original positive, SMD) | — | d | 0.58 | SD 0.87 | 9 | Numerical results only |
| Original effect size median (all) | — | d | 2.96 | IQR 0.71-15.26 | 10 | Comparing means, value for original |
| Replication effect size median (all) | — | d | 0.63 | IQR 0.15-15.26 | 10 | Comparing means, value for replication |
| Aggregated p-value (meta) | p_meta | — | 0.0005 | — | 8 | Evidence of nonzero meta-analytic effects |
| Power for original effect size detection | — | % | 80 | — | 22 | Pre-specified in registered protocols |
| Median [IQR] original sample size (original positive) | — | N | 16.0 | 8.0-25.0 | 4 | Per experiment |
| Median [IQR] replication sample size (original positive) | — | N | 24.0 | 16.0-69.0 | 4 | Per experiment |
| Median [IQR] original sample size (original null) | — | N | 18.0 | 8.0-51.4 | 4 | Per experiment |
| Median [IQR] replication sample size (original null) | — | N | 24.0 | 16.0-57.3 | 4 | Per experiment |
| Animal effects (of 158) | — | count | 36 | — | 13 | Subset of effects |
| Non-animal effects (of 158) | — | count | 122 | — | 13 | Subset of effects |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Same direction | Replication rate | 82% | — | — | All 116 outcomes with positive originals | 4 |
| Direction + statistical significance | Replication rate | 39% | — | — | All 112 outcomes | 4 |
| Original ES in replication CI | Replication rate | 23% | — | — | All 112 outcomes | 4 |
| Replication ES in original CI | Replication rate | 45% | — | — | All 112 outcomes | 4 |
| Replication ES in prediction interval | Replication rate | 60% | — | — | All 112 outcomes | 4 |
| Replication ES >= original ES | Replication rate | 3% | — | — | All 112 outcomes | 4 |
| Meta-analysis p < 0.05 | Replication rate | 67% | — | — | All 112 outcomes | 4 |
| Effect size ratio (replication/original) | Proportion | ~15% | — | — | Median replication ES ~85% smaller | 1 |
| Same direction (animal) | Replication rate | 63% | — | — | 27 animal original positive effects | 13 |
| Same direction (non-animal) | Replication rate | 85% | — | — | 74 non-animal original positive effects | 13 |
| Direction+sig (animal) | Replication rate | 12% | — | — | 25 animal experiments | 13 |
| Direction+sig (non-animal) | Replication rate | 54% | — | — | 72 non-animal experiments | 13 |
| Meta-analysis p<0.05 (animal) | Replication rate | 52% | — | — | 25 animal experiments | 13 |
| Meta-analysis p<0.05 (non-animal) | Replication rate | 65% | — | — | 72 non-animal experiments | 13 |
| Replication ES in PI (animal) | Replication rate | 44% | — | — | 25 animal experiments | 13 |
| Replication ES in PI (non-animal) | Replication rate | 63% | — | — | 72 non-animal experiments | 13 |
| NHST original vs replication p-values | Fisher's exact | t(118) = 1.03 | — | p = 0.127 | All data | 6 |
| NHST original positive vs replication | Fisher's exact | t(118) = 1.03 | — | p = 0.127 | Original positive results | 6 |
| NHST representative images | Fisher's exact | t(118) = 1.03 | — | p = 0.163 | Representative image effects | 6 |
| Combined meta-analytic effect (positive effects) | SMD | varies | — | p_meta = 0.0005 | 97 original positive effects | 8 |
| Original effect size (mean, original positive, numerical) | Cohen's d | 1.38 | SD 1.85 | — | 19 papers | 9 |
| Replication effect size (mean, original positive, numerical) | Cohen's d | 0.58 | SD 0.87 | — | Replications | 9 |
| Median effect size ratio (rep/orig) | ratio | 0.30/0.63 | — | — | Original positive effects | 9 |

## Methods & Implementation Details
- Experiments selected from 53 high-impact cancer biology papers published 2010-2012; selection identified 193 experiments from these papers, but only 50 from 23 papers were completed *(p.1, p.22)*
- Registered Reports protocol: each replication was pre-registered, peer-reviewed, and included original author input on experimental design *(p.2)*
- Replications conducted by CROs or academic core labs, not by original authors *(p.2, p.14)*
- Effect sizes calculated as standardized mean differences (SMD, Cohen's d) *(p.22)*
- For representative images, the original image was treated as a representative value; replication images were compared qualitatively *(p.3)*
- Seven criteria applied to assess replication: (1) same direction, (2) direction and statistical significance, (3) original ES in replication 95% CI, (4) replication ES in original 95% CI, (5) replication ES in 95% prediction interval, (6) replication ES >= original ES, (7) meta-analysis combining original and replication ES gives p < 0.05 *(p.3)*
- The "same direction" criterion is a low bar; the "replication ES >= original ES" criterion is the most stringent *(p.3)*
- Hierarchical structure: effects nested in experiments nested in papers. Robust variance estimation with correlated effects working model and Satterthwaite small-sample corrections *(p.23)*
- Statistical software: R (R Project for Statistical Computing) with metafor package, robumeta package *(p.24)*
- Five candidate moderators examined: (i) animal vs non-animal experiment, (ii) CRO lab vs not, (iii) core lab vs not, (iv) materials shared by original authors, (v) quality of methodological clarifications *(p.14, p.24)*
- Moderator variables coded as binary; point-biserial correlations computed; mixed-effects meta-regression with all five moderators simultaneously *(p.24)*
- Sensitivity analysis: heterogeneity assessed but found to be small relative to original and replication standard errors *(p.24)*

## Figures of Interest
- **Fig 1 (p.6):** p-value density plots for original and replication results. Shows original studies had more small p-values; replications had flatter distribution. Separate panels for all data, original positive, experiments, representative images.
- **Fig 2 (p.10):** Replication effect sizes compared with original effect sizes (scatter plot). Each circle = one SMD effect size pair. Gray line = identity (replication = original). Dashed line = replication = 0. Shows most replication effects below identity line.
- **Fig 3 (p.11):** Effect size density plots for original and replication findings. Shows replication distributions shifted toward zero. Panels by individual outcomes, effects, experiments, papers.
- **Fig 4 (p.14):** Correlation matrix of five candidate moderators. Point-biserial correlations among moderators for 97 original positive effects. None consistently associated with replication success.
- **Fig 5 (p.16):** Replication effect sizes compared with original effect sizes for animal vs non-animal experiments. Shows animal experiments tended to have larger original effects and smaller replication effects.
- **Fig 6 (p.17):** Replication rates across five criteria for individual papers. Bar chart showing each paper's success count across criteria. High variability.
- **Fig 7 (p.19):** Correlations between five replication criteria. All positively correlated with each other (range 0.15-0.78). Dir & Sig most strongly correlated with Meta sig (r=0.70).
- **Table 1 (p.4):** Replication rates according to seven criteria, broken down by papers/experiments/effects/all outcomes and by original positive vs null results and numerical vs representative image data.
- **Table 2 (p.8):** Null hypothesis significance testing results by criteria.
- **Table 3 (p.9):** Comparing original and replication effect sizes (means, medians, IQRs) for original positive and null results.
- **Table 4 (p.13-14):** Replication rates for animal vs non-animal experiments across all seven criteria.
- **Table 5 (p.15):** Effect sizes for animal and non-animal experiments.
- **Table 6 (p.17):** Assessing replications of positive and null results across five criteria for each paper.

## Results Summary

**Replication rates by criterion (original positive results, all outcomes):** Same direction: 95/116 (82%); direction+significance: 44/112 (39%); original ES in replication CI: 26/112 (23%); replication ES in original CI: 50/112 (45%); replication ES in PI: 67/112 (60%); replication ES >= original: 3/112 (3%); meta-analysis p<0.05: 75/112 (67%). *(p.4)*

**Effect size shrinkage:** Replication effect sizes were substantially smaller than originals. Median original positive effect size was 0.63 (IQR 0.15-1.80), median replication was 0.30 (IQR 0.01-0.96). Mean original was 1.38 (SD 1.85), mean replication was 0.58 (SD 0.87). Only 3% of replications had effect sizes as large or larger than originals. *(p.9)*

**Null hypothesis testing:** Of 112 original positive effects with replication data, 45% (50/112) had replications that were statistically significant in the same direction. 67% (75/112) had meta-analytic p < 0.05 when original and replication data were combined. *(p.4-5, p.8)*

**Animal vs non-animal:** Animal experiments replicated less well. Same direction: 63% animal vs 85% non-animal. Direction+significance: 12% animal vs 54% non-animal. Meta-analysis p<0.05: 52% animal vs 65% non-animal. Animal experiments tended to have larger original effect sizes and smaller replication effect sizes. *(p.12-13)*

**Moderator analysis:** None of five candidate moderators (animal experiment, CRO lab, core lab, materials shared, clarifications quality) showed a consistent, significant association with replication rate across criteria. The clearest predictor was that smaller effects were less likely to replicate, consistent with findings in other disciplines. *(p.14, p.19)*

**Original null results:** Of 22 original null results, 10 of 20 (50%) replications were in the same direction as the original and statistically significant. This suggests some original null findings may have been false negatives or underpowered. *(p.4-5)*

## Limitations
- Only 50 of 193 originally planned experiments were completed due to resource constraints, documentation barriers, and methodological challenges *(p.1, p.21)*
- Selection based on highly cited papers may not generalize to all preclinical cancer biology *(p.21)*
- Papers were selected from 2010-2012, so findings reflect practices of that era *(p.22)*
- Replications were conducted at single labs (CROs or core labs); a single failed replication does not definitively confirm non-replicability *(p.16)*
- Quality of methodological clarifications from original authors varied; some did not respond to requests *(p.2)*
- Cannot determine whether specific failures are due to false positives in originals, false negatives in replications, or legitimate contextual differences *(p.16-17)*
- The heterogeneity analysis sensitivity was limited; future research could directly estimate heterogeneity *(p.24)*
- Representative image comparisons are inherently subjective and qualitative *(p.3)*

## Arguments Against Prior Work
- Challenges the assumption that high-impact, highly-cited preclinical cancer biology findings are reliably replicable *(p.1, p.16)*
- Provides empirical evidence against the claim that replication failures are primarily due to lack of expertise by replicators; replications used CROs and core labs with relevant expertise and pre-registered protocols with original author input *(p.2, p.17)*
- Argues against exclusive reliance on any single replication criterion; demonstrates that different criteria yield replication rates ranging from 3% to 82%, making the question "did it replicate?" dependent on the criterion chosen *(p.3, p.15)*
- Criticizes the practice of selective reporting, p-hacking, and inflated effect sizes, noting that the ~85% shrinkage in effect sizes is consistent with publication bias inflating original estimates *(p.10-11, p.16)*
- Challenges prior claims (e.g., Begley and Ellis 2012, which reported only 11% replication) as potentially conflating replicability with other quality measures *(p.1)*

## Design Rationale
- Used Registered Reports protocol to maximize transparency and minimize bias in the replication process; pre-registration prevents post-hoc hypothesis adjustment *(p.2, p.22)*
- Used seven replication criteria rather than a single criterion because no single method captures all aspects of replicability; the criteria range from very lenient (same direction) to very strict (replication ES >= original ES) *(p.3)*
- Used CROs and core labs rather than original labs to test whether results generalize beyond the original experimental context *(p.2)*
- Sought original author input on protocols to minimize methodological deviations, while maintaining independence *(p.2)*
- Used SMD (Cohen's d) as a common effect size metric to enable cross-experiment comparison *(p.22)*
- Employed robust variance estimation to handle the hierarchical data structure (effects within experiments within papers) *(p.23)*

## Testable Properties
- Replication effect sizes in preclinical cancer biology are approximately 85% smaller than original effect sizes on average *(p.1)*
- Same-direction replication rate for original positive findings is approximately 82% *(p.4)*
- Direction-and-significance replication rate is approximately 39% *(p.4)*
- Meta-analytic combined significance (p<0.05) replication rate is approximately 67% *(p.4)*
- Only ~3% of replications produce effect sizes as large or larger than the original *(p.4)*
- Animal experiments replicate at lower rates than non-animal experiments across all criteria *(p.12-13)*
- Smaller original effect sizes are associated with lower replication success *(p.19)*
- None of five candidate moderators (animal, CRO, core lab, materials shared, clarifications quality) individually predicts replication success consistently *(p.14)*
- The five replication criteria are all positively correlated with each other (r = 0.15 to 0.78) *(p.19)*
- Original positive effect sizes and replication effect sizes have similar p-value distributions when examining all data (t(118) = 1.03, p = 0.127) *(p.6)*

## Relevance to Project
This paper provides empirical base rates for replicability in preclinical cancer biology, which can be used to calibrate uncertainty in propstore's argumentation framework. The finding that replication rates range from 3% to 82% depending on criterion choice is directly relevant to how propstore handles competing evidence assessments. The systematic shrinkage of effect sizes (~85%) provides a concrete prior for adjusting claim confidence based on replication status. The moderator analysis (none significant) cautions against overconfident causal claims about what drives replicability.

## Open Questions
- [ ] How to calibrate propstore opinion uncertainty using the 7-criterion replication rate spectrum
- [ ] Whether the ~85% effect size shrinkage should be applied as a default deflation factor for unreplicated claims
- [ ] How to incorporate the animal vs non-animal replication differential into domain-specific priors

## Related Work Worth Reading
- Open Science Collaboration, 2015 (Estimating the reproducibility of psychological science) - foundational comparison study
- Begley and Ellis, 2012 (Drug development: raise standards for preclinical cancer research) - prior estimate (11% replication) this paper contextualizes
- Nosek et al., 2021 (Replicability, robustness, and reproducibility in psychological science) - cross-discipline comparison
- Camerer et al., 2016 and 2018 (Evaluating replicability in social sciences/economics) - similar methodology in other fields
- Ioannidis, 2005 (Why most published research findings are false) - theoretical framework for publication bias
- Mathur and VanderWeele, 2020b (New statistical metrics for multisite replication projects)
- Patil, Peng, and Leek, 2016 (What should researchers expect when they replicate?) - prediction interval methodology

## Collection Cross-References

### Already in Collection
- [[Aarts_2015_EstimatingReproducibilityPsychologicalScience]] — foundational comparison study (Open Science Collaboration); Errington 2021 directly extends this methodology to preclinical cancer biology
- [[Camerer_2016_EvaluatingReplicabilityLaboratoryExperiments]] — parallel replication effort in experimental economics; Errington cites this as methodological precedent
- [[Camerer_2018_EvaluatingReplicabilitySocialScience]] — parallel replication effort in social science; uses similar multi-criterion assessment approach

### Cited By (in Collection)
- [[Camerer_2016_EvaluatingReplicabilityLaboratoryExperiments]] — lists Errington as related replication effort in cancer biology
- [[Aarts_2015_EstimatingReproducibilityPsychologicalScience]] — lists Errington as related replication study in preclinical cancer research

### New Leads (Not Yet in Collection)
- Begley and Ellis (2012) — "Drug development: raise standards for preclinical cancer research" — prior estimate of 11% replication rate that this paper contextualizes
- Ioannidis (2005) — "Why Most Published Research Findings Are False" — theoretical framework for publication bias and inflated effect sizes
- Nosek et al. (2021) — "Replicability, robustness, and reproducibility in psychological science" — cross-discipline review
- Mathur and VanderWeele (2020b) — "New statistical metrics for multisite replication projects" — methodological foundation for replication assessment

### Supersedes or Recontextualizes
- (none)

### Now in Collection (previously listed as leads)
- [[Gordon_2021_PredictingReplicability—AnalysisSurveyPrediction]] — Pools prediction market and survey data from RPP, EERP, ML2, SSRP (103 studies). Markets classify replication outcomes at 73% accuracy; p < 0.005 threshold predicts 76% replication rate. Cited in Errington's reference list (ref 23).

### Conceptual Links (not citation-based)
- [[Aarts_2015_EstimatingReproducibilityPsychologicalScience]] — **Strong.** Direct methodological parallel: both are large-scale systematic replication projects applying multiple criteria. Errington finds 39% direction+significance replication (vs Aarts' 36% in psychology), ~85% effect size shrinkage (vs ~50% in psychology). The cross-domain convergence on effect size inflation is a key finding.
- [[Camerer_2016_EvaluatingReplicabilityLaboratoryExperiments]] — **Strong.** Same replication methodology family. Camerer found 61% replication rate in economics (11/18 studies). Errington's multi-criterion approach reveals that the "replication rate" depends entirely on which criterion is used (3-82%), complicating direct cross-domain comparison.
- [[Camerer_2018_EvaluatingReplicabilitySocialScience]] — **Strong.** Extension of Camerer 2016 to social science. Found 62% replication rate (13/21). Together these three projects (psychology, economics, social science, cancer biology) form a cross-domain replicability evidence base.
- [[Gordon_2021_PredictingReplicability—AnalysisSurveyPrediction]] — **Strong.** Gordon pools forecasting data from the same replication projects that Errington's work complements. Gordon provides the meta-analytic forecasting accuracy (73% market, 71% survey) and shows p < 0.005 strongly predicts replication. Errington's cancer biology data is from a different domain but addresses the same fundamental question of whether replication outcomes are predictable.
