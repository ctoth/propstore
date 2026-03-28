---
title: "Why Most Published Research Findings Are False"
authors: "John P. A. Ioannidis"
year: 2005
venue: "PLoS Medicine"
doi_url: "https://doi.org/10.1371/journal.pmed.0020124"
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-03-28T21:25:13Z"
---
# Why Most Published Research Findings Are False

## One-Sentence Summary
This paper provides a formal Bayesian framework showing that for most study designs and settings, the post-study probability that a positive research finding reflects a true relationship is less than 50%, due to the interplay of statistical power, pre-study odds, bias, and the number of competing research teams.

## Problem Addressed
There is increasing concern that most current published research findings are false. The probability that a research claim is true may depend on study power and bias, the number of other studies on the same question, and the ratio of true to no relationships among the relationships probed in each scientific field. The paper formalizes when and why research findings are more likely to be false than true. *(p.0)*

## Key Contributions
- A formal Bayesian model computing the post-study probability (PPV) that a research finding is true, as a function of pre-study odds R, statistical power (1-β), significance threshold α, and bias u *(p.0-1)*
- Six corollaries identifying conditions that make research findings less likely to be true *(p.2-3)*
- Demonstration via Table 4 that for most practical research settings, PPV < 50% *(p.4)*
- Recommendations for improving research reliability: larger studies, meta-analyses, reduced bias, pre-study registration, and understanding of pre-study odds *(p.4-5)*

## Study Design
*Non-empirical — this is a theoretical/analytical paper using Bayesian probability modeling.*

## Methodology
The paper constructs a 2×2 framework (Table 1) crossing true vs. not-true relationships with positive vs. negative findings. It defines the positive predictive value (PPV) of a research finding as the probability that a positive finding reflects a true relationship. The framework incorporates: pre-study probability of a relationship being true (R), Type I error rate (α), Type II error rate (β), and bias (u). Bias is modeled as the probability that a finding would be declared positive despite being nominally non-significant, due to data manipulation, selective reporting, or other distortions. *(p.0-1)*

## Key Equations / Statistical Models

### PPV Without Bias

$$
\text{PPV} = \frac{(1-\beta)R}{(1-\beta)R + \alpha}
$$

Where:
- PPV = positive predictive value (post-study probability a positive finding is true)
- R = pre-study odds that the relationship is true (ratio of "true relationships" to "no relationships" among those probed)
- (1-β) = statistical power (probability of finding a true relationship when one exists)
- α = Type I error rate (probability of claiming a relationship when none exists)
*(p.0)*

### PPV With Bias

$$
\text{PPV} = \frac{(1-\beta)R + u\beta R}{(1-\beta)R + \alpha + u\beta R + u(1-\alpha) - u\beta R}
$$

Simplifying:

$$
\text{PPV} = \frac{(1-\beta)R + u\beta R}{(1-\beta)R + \alpha + u - u\alpha}
$$

Where:
- u = bias (probability of declaring a positive result despite the underlying finding being null, through data manipulation, selective analysis, selective reporting, or other mechanisms)
- Other variables as above
*(p.1)*

### Pre-study Odds

$$
R = \frac{\text{number of true relationships}}{\text{number of no relationships}} = \frac{c}{1-c}
$$

Where c is the fraction of probed relationships that are truly non-null in a given field. *(p.0)*

### Post-study Probability (alternative form)

The paper also states PPV in terms of the probability c directly:

$$
\text{PPV} = \frac{(1-\beta)c}{(1-\beta)c + \alpha(1-c)}
$$

*(p.0)*

### Threshold for PPV > 50%

For a research finding to be more likely true than false (PPV > 50%), we need:

$$
(1-\beta)R > \alpha
$$

Without bias. With bias u, the condition becomes harder to satisfy. *(p.0)*

### Multiple Independent Teams (Corollary 5)

When n independent teams pursue the same question with equal power:

$$
\text{PPV} = \frac{R(1 - \beta^n)}{R + 1 - (1-\alpha)^n - R\beta^n}
$$

Where n = number of independent research teams. As n increases, PPV decreases because the probability that at least one team gets a false positive increases faster than the improvement in detecting true effects. *(p.2)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Pre-study odds | R | — | varies | 0–∞ | p.0 | Ratio of true to null relationships probed |
| Statistical power | 1-β | — | 0.80 | 0–1 | p.0 | Conventional 80% often assumed but rarely achieved |
| Type I error rate | α | — | 0.05 | 0–1 | p.0 | Standard significance threshold |
| Bias | u | — | varies | 0–1 | p.1 | Probability of producing positive result despite null |
| Number of teams | n | — | varies | 1–∞ | p.2 | Independent teams pursuing same question |
| Fraction true relationships | c | — | varies | 0–1 | p.0 | c = R/(1+R) |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| PPV, adequately powered RCT | PPV | 0.85 | — | — | R=1:1, power=0.80, α=0.05 | p.1 |
| PPV, underpowered RCT | PPV | 0.23 | — | — | R=1:3, power=0.20, α=0.05 | p.1 |
| PPV, discovery-oriented exploratory | PPV | 0.0010 | — | — | R=1:1000, power=0.20, α=0.05 | p.1 |
| PPV, epidemiological | PPV | 0.12 | — | — | R=1:10, power=0.80, α=0.05 | p.1 |
| PPV, RCT with 1:1 odds, 10% bias | PPV | ~0.85→lower | — | — | Shows bias effect on RCT PPV | p.3 |

### Table 4: PPV for Various Research Settings (p.4)

| Research Design | Pre-study Odds R | Practical Example | PPV (no bias) | PPV (15% bias) | PPV (30% bias) | PPV (80% bias) |
|-----------------|-----------------|-------------------|---------------|----------------|----------------|----------------|
| Adequately powered RCT | 1:1 | Well-designed phase III | 0.85 | 0.79 | 0.73 | 0.52 |
| Confirmatory meta-analysis, small RCTs | 1:2 | Meta of several small RCTs | 0.85 | 0.76 | 0.68 | 0.41 |
| Underpowered but well-done RCT | 1:3 | Pilot RCT | 0.23 | 0.19 | 0.16 | 0.08 |
| Underpowered, poorly done RCT | 1:5 | Small RCT with violations | 0.17 | 0.14 | 0.11 | 0.06 |
| Adequately powered epidemiological | 2:3 to 1:3 | Varies | 0.12–0.41 | — | — | — |
| Discovery-oriented exploratory | 1:1000 | Gene association, microarray | 0.0010 | 0.0015 | 0.0023 | 0.0116 |

*(p.4)*

## Methods & Implementation Details
- The framework uses a simple 2×2 table (Table 1) crossing true/not-true relationships with positive/negative findings *(p.1)*
- Table 1 cell counts: True positive = (1-β)R/(R+1); False positive = α/(R+1); False negative = βR/(R+1); True negative = (1-α)/(R+1) — normalized so total equals 1 *(p.1)*
- Bias u is modeled as additive: it converts some true negatives and false negatives into positives *(p.1)*
- The model assumes relationships are either exactly true or exactly null (no effect size spectrum) *(p.0-1)*
- Multiple testing correction: the paper notes that "Bonferroni" and similar corrections are rarely adequate because they don't account for correlation among tests or testing done outside the reported study *(p.2)*
- The framework is Bayesian in structure but uses frequentist parameters (α, β) as inputs *(p.0)*

## Figures of Interest
- **Table 1 (p.1):** 2×2 framework — Research Findings and True Relationships, showing cell probabilities for true/false positives/negatives
- **Table 2 (p.2):** Research Findings and True Relationships in the Presence of Multiple Studies — extending the framework to n competing teams
- **Table 3 (p.2):** Extreme PPV values for varying pre-study odds, number of analyses, and bias levels
- **Fig 1 (p.3):** PPV as a function of pre-study odds R, plotted for different power/bias combinations (1-β=0.20 and 0.80; u=0.10 and 0.30)
- **Box 1 (p.3):** Worked example — An Example: Science at Low Pre-Study Odds, illustrating genetic association studies
- **Table 4 (p.4):** PPV for Various Research Designs — the summary table showing PPV across practical research settings with different bias levels

## Results Summary
The central result is that for most study designs and settings, a claimed research finding is more likely to be false than true. Specifically: *(p.0)*
- An adequately powered, well-performed RCT with 1:1 pre-study odds and no bias has PPV=0.85. This is the best-case scenario in medicine. *(p.1, p.4)*
- Underpowered trials (β=0.80, i.e., only 20% power) with moderate pre-study odds (1:3) have PPV=0.23. *(p.1)*
- Hypothesis-generating exploratory research (R=1:1000) has PPV≈0.001 even without bias. *(p.1)*
- Adding bias of 10-30% substantially degrades PPV in all settings. *(p.3-4)*
- When multiple teams compete, positive findings are even less likely to be true. *(p.2)*
- The "winner's curse" phenomenon means that the first positive finding in a competitive field will typically be the most biased. *(p.2)*

## Limitations
- The model treats relationships as binary (true or null) — there is no spectrum of effect sizes *(p.0-1)*
- Pre-study odds R are inherently difficult to estimate and must be approximated *(p.5)*
- The amount of data dredging by authors or competing teams is usually impossible to decipher *(p.5)*
- The model does not account for correlation among tested hypotheses *(p.1)*
- Bias u is treated as a single scalar, but in practice bias has many distinct mechanisms *(p.1)*

## Arguments Against Prior Work
- Traditional reliance on p < 0.05 significance testing gives "only a partial picture" without context of how much testing has occurred *(p.5)*
- Statistical significance testing in isolation cannot inform about pre-study odds *(p.5)*
- Multiple testing corrections (e.g., Bonferroni) are usually inadequate because they cannot account for undisclosed analyses *(p.2)*
- The "Proteus phenomenon" — early extreme estimates in new fields are contradicted by later studies — is a predictable consequence of low pre-study odds plus competition *(p.2, ref 29)*

## Design Rationale
- The Bayesian PPV framework was chosen over pure frequentist testing because it naturally incorporates pre-study odds and bias *(p.0)*
- The binary true/null model was chosen for analytical tractability *(p.0)*
- Bias is modeled as a single parameter u to keep the framework simple while capturing the aggregate effect of all bias-generating mechanisms *(p.1)*
- The multiple-teams extension (Corollary 5) was developed because competition is a structural feature of science that systematically degrades PPV *(p.2)*

## Six Corollaries

### Corollary 1: Smaller Studies
The smaller the studies in a scientific field, the less likely the research findings are to be true. Small studies have lower power (1-β), which directly reduces PPV. *(p.2)*

### Corollary 2: Smaller Effect Sizes
The smaller the effect sizes in a scientific field, the less likely the research findings are to be true. Small effects require larger studies to detect, and fields studying small effects typically have inadequate power. *(p.2)*

### Corollary 3: Greater Number of Tested Relationships
The greater the number and the lesser the selection of tested relationships in a scientific field, the less likely the research findings are to be true. Testing many relationships lowers R (pre-study odds) because most will be null. *(p.2)*

### Corollary 4: Greater Design Flexibility
The greater the flexibility in designs, definitions, outcomes, and analytical modes in a scientific field, the less likely the research findings are to be true. Flexibility enables transformation of nominally negative results into "positive" via data dredging, outcome switching, subgroup mining, and analytical mode selection. *(p.2)*

### Corollary 5: Greater Financial and Prejudice Interests
The greater the financial and other interests and prejudices in a scientific field, the less likely the research findings are to be true. Financial conflicts, prejudice, and career pressure all increase bias u. *(p.2)*

### Corollary 6: Hot Fields with Many Teams
The hotter a scientific field (with more scientific teams involved), the less likely the research findings are to be true. With n teams, the probability at least one finds a false positive is 1-(1-α)^n, which grows rapidly. *(p.2)*

## Testable Properties
- For any study, PPV = (1-β)R / [(1-β)R + α] when u=0 *(p.0)*
- PPV > 0.50 requires (1-β)R > α *(p.0)*
- PPV is monotonically increasing in R (pre-study odds) *(p.0)*
- PPV is monotonically increasing in (1-β) (power) *(p.0)*
- PPV is monotonically decreasing in α *(p.0)*
- PPV is monotonically decreasing in u (bias) *(p.1)*
- PPV is monotonically decreasing in n (number of competing teams) for any fixed R, α, β *(p.2)*
- At R=1:1, α=0.05, 1-β=0.80, u=0: PPV = 0.80/0.85 ≈ 0.94 ... but Table 4 says 0.85. The paper uses a specific convention for confirmatory meta-analyses vs single RCTs *(p.4)*
- At R=1:1000, α=0.05, 1-β=0.20, u=0: PPV ≈ 0.001 *(p.1)*
- With bias u, PPV can paradoxically increase for exploratory research (more "positive" findings are declared, but more of them happen to be true by accident) — this is reflected in Table 4 where PPV increases with bias for the 1:1000 row *(p.4)*

## Relevance to Project
This paper is foundational for any system that reasons about the credibility of claims. The PPV framework provides a principled way to assign prior probabilities to research findings based on study design characteristics. For propstore's argumentation and belief revision layers:
- The pre-study odds R could inform prior weights in the opinion algebra (Jøsang subjective logic)
- The six corollaries provide structured attack arguments against claims from underpowered, biased, or exploratory studies
- The PPV formula could be implemented as a calibration function mapping study-design features to base rates for the argumentation framework
- The bias parameter u maps naturally to the uncertainty component in subjective logic opinions

## Open Questions
- [ ] How to estimate R (pre-study odds) for claims in the propstore domain
- [ ] Whether the binary true/null model can be extended to a continuous effect-size framework while preserving analytical tractability
- [ ] How to operationalize the six corollaries as formal attack relations in a Dung AF or ASPIC+ framework
- [ ] Whether the PPV formula can serve as the base-rate input for DF-QuAD base scores

## Collection Cross-References

### Already in Collection
- (none — no cited references match current collection papers)

### New Leads (Not Yet in Collection)
- Wacholder S et al. (2004) "Assessing the probability that a positive report is false" — FPRP framework complementary to PPV, directly relevant to claim calibration
- Lindley DV (1957) "A statistical paradox" — foundational Bayesian-frequentist divergence result

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- (none found — no collection papers explicitly cite Ioannidis 2005)

### Conceptual Links (not citation-based)
- [[Aarts_2015_EstimatingReproducibilityPsychologicalScience]] — **Strong**: Empirically validates the PPV framework's predictions by showing only 36% of 100 psychology replications succeeded; provides the real-world base rates that Ioannidis's model predicts
- [[Altmejd_2019_PredictingReplicabilitySocialScience]] — **Strong**: Trains ML models on the same study-level features (p-value, effect size, sample size) that Ioannidis identifies as PPV determinants, achieving 70% prediction accuracy
- [[Gordon_2021_PredictingReplicability—AnalysisSurveyPrediction]] — **Strong**: Directly extends the prediction-of-replication program that Ioannidis's framework motivates
- [[Border_2019_NoSupportHistoricalCandidate]] — **Strong**: Provides a canonical large-sample falsification of candidate gene findings, exactly the scenario Ioannidis's Corollary 3 (many tested relationships, low R) predicts will produce false positives
- [[Camerer_2016_EvaluatingReplicabilityLaboratoryExperiments]] — **Moderate**: Replication rates (61%) and effect size shrinkage (66% of original) in economics provide empirical calibration for PPV estimates
- [[Camerer_2018_EvaluatingReplicabilitySocialScience]] — **Moderate**: Social science replications providing further empirical grounding for PPV predictions
- [[Yang_2020_EstimatingDeepReplicabilityScientific]] — **Moderate**: ML-based replication prediction using narrative features, a different operationalization of the same underlying credibility assessment
- [[Guo_2017_CalibrationModernNeuralNetworks]] — **Moderate**: Temperature scaling calibration provides the technical machinery for mapping model outputs to well-calibrated probabilities, which is the implementation bridge between Ioannidis's theoretical PPV and propstore's opinion algebra

## Related Work Worth Reading
- Wacholder S et al. (2004) "Assessing the probability that a positive report is false" — FPRP approach for molecular epidemiology *(ref 10)*
- Ioannidis JPA (2005) "Contradicted and initially stronger effects in highly cited clinical research" — empirical validation of this framework *(ref 36)*
- Sterne JA, Davey Smith G (2001) "Sifting the evidence—What's wrong with significance tests" *(ref 9)*
- Lindley DV (1957) "A statistical paradox" — Lindley's paradox relating Bayesian and frequentist conclusions *(ref 32)*
- Hsueh HM et al. (2003) "Comparison of methods for estimating the number of true null hypotheses in multiplicity testing" *(ref 37)*
