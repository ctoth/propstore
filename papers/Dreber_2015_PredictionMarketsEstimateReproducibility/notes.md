---
title: "Using prediction markets to estimate the reproducibility of scientific research"
authors: "Anna Dreber, Thomas Pfeiffer, Johan Almenberg, Siri Isaksson, Brad Wilson, Yiling Chen, Brian A. Nosek, Magnus Johannesson"
year: 2015
venue: "Proceedings of the National Academy of Sciences"
doi_url: "https://doi.org/10.1073/pnas.1516179112"
---

# Using prediction markets to estimate the reproducibility of scientific research

## One-Sentence Summary
Demonstrates that prediction markets among psychology researchers can forecast which published findings will replicate, achieving 71% accuracy and providing well-calibrated probability estimates of reproducibility.

## Problem Addressed
The reproducibility of scientific research has been questioned across many fields, but there was no established method for estimating the probability that a specific finding would replicate before conducting an expensive replication study. Prior approaches (informal polls, expert surveys) existed but prediction markets — which aggregate information through incentivized trading — had not been applied to this problem. *(p.1)*

## Key Contributions
- First application of prediction markets to predict reproducibility of published psychology studies *(p.1)*
- Showed prediction market prices correctly predicted outcomes for 71% of 41 replications (vs. 58% for a pre-market survey) *(p.2)*
- Demonstrated that market prices are well-calibrated as probabilities of replication *(p.2-3)*
- Established prediction markets as a tool for prioritizing which studies to replicate *(p.3)*

## Study Design (empirical papers)
- **Type:** Prediction market experiment embedded within Reproducibility Project: Psychology (RPP) *(p.1)*
- **Population:** N=44 studies selected from RPP (3 top psychology journals, 2008 issues); 41 completed replications used for analysis; up to 47 participants (psychology researchers) traded in the markets *(p.1-2)*
- **Intervention(s):** Two rounds of prediction markets. Round 1: Oct-Dec 2014 (before replication results known). Round 2: smaller set of 23 studies where replication result was later verified *(p.2)*
- **Comparator(s):** Pre-market survey of participants' beliefs about replication probability *(p.2)*
- **Primary endpoint(s):** Whether prediction market prices predict replication outcomes (defined as original effect replicated at p < 0.05 in same direction) *(p.1-2)*
- **Secondary endpoint(s):** Calibration of market prices as probabilities; comparison of market vs. survey predictive performance *(p.2-3)*
- **Follow-up:** Markets ran for minimum 2 weeks per study; 41 of 44 studies completed replication *(p.2)*

## Methodology
44 studies from RPP were selected for prediction markets. Each study had a contract that paid $1 if the replication succeeded (p < 0.05 in same direction as original) and $0 otherwise. Researchers traded using real money (endowment $50 per market set). Market prices aggregated traders' beliefs about replication probability. Two rounds of markets were conducted. Results compared to a pre-market survey where participants rated replication probability on a 0-100% scale. *(p.1-2)*

Markets used a continuous double-auction mechanism with an automated market maker implementing a logarithmic market scoring rule (LMSR). Trading occurred through a web-based interface provided by Consensus Point. *(p.2)*

## Key Equations / Statistical Models

$$
P(\text{replication}) = \beta_0 + \beta_1 \cdot \text{market\_price}
$$
Where: market_price is the final prediction market price (0-1 scale), P(replication) is the probability of successful replication. Linear probability model.
*(p.2)*

$$
\text{logit}(P(\text{replication})) = \alpha + \beta \cdot \text{market\_price}
$$
Where: Logistic regression model for binary replication outcome on market price.
*(p.2)*

$$
P(\text{replication}) = \beta_0 + \beta_1 \cdot \text{survey\_mean}
$$
Where: survey_mean is the mean subjective probability from the pre-market survey. Linear probability model for survey-based prediction.
*(p.2)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of studies in RPP sample | N | count | 44 | — | 1 | 3 did not complete replication, 41 used |
| Number of active traders | — | count | — | 20-100 (mean 56) per market round 1; 10-40 round 2 | 2 | Up to 47 individuals total |
| Endowment per market set | — | USD | 50 | — | 2 | Real money incentive |
| Contract payout (success) | — | USD | 1 | — | 1 | Binary contract |
| Contract payout (failure) | — | USD | 0 | — | 1 | Binary contract |
| Trading period | — | weeks | ≥2 | — | 2 | Each market ran at least 2 weeks |
| Mean final market price (all 44) | — | — | 0.553 | — | 2 | Prior to replication results |
| Median final market price (all 44) | — | — | 0.55 | — | 2 | — |
| Market prediction accuracy (>0.5 threshold) | — | % | 71 | — | 2 | 29/41 correct |
| Survey prediction accuracy (>0.5 threshold) | — | % | 58 | — | 2 | 24/41 correct |
| Replication rate in RPP | — | proportion | 0.39 | — | 1 | 16/41 replicated at p<0.05 |
| LPM coefficient on market price | beta_1 | — | 0.966 | — | 2 | Not sig. diff from 1 (p=0.943) |
| LPM intercept | beta_0 | — | 0.049 | — | 2 | Not sig. diff from 0 (p=0.824) |
| Logistic coefficient on market price | beta | — | 4.32 | — | 2 | — |
| Logistic intercept | alpha | — | -2.55 | — | 2 | — |
| Weighted survey coefficient | — | — | 0.728 | — | 2 | Not sig. diff from 1 (p=0.477) |
| Prior probability (base rate) | pi_0 | — | — | 0.10-1.00 | 3 | Range explored in Bayesian analysis |
| Posterior probability (replicated, given observed) | — | — | — | 0.925-0.975 (median 0.95) | 3 | For 16 replicated studies |
| Posterior probability (not replicated, given observed) | — | — | — | 0.13-0.65 (median 0.635) | 3 | For 25 non-replicated studies |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Market prediction accuracy | % correct | 71% | — | — | 41 replications, >50% threshold | 2 |
| Survey prediction accuracy | % correct | 58% | — | — | 41 replications, >50% threshold | 2 |
| Market predicts replications | LPM beta | 0.966 | — | 0.943 (H0: beta=1) | 41 studies | 2 |
| Market predicts replications | Logistic beta | 4.32 | — | — | 41 studies | 2 |
| Survey predicts replications | Weighted LPM beta | 0.728 | — | 0.477 (H0: beta=1) | 41 studies | 2 |
| Replication rate | proportion | 0.39 | — | — | 41 RPP studies | 1 |
| Mean market price (replicated) | market price | 0.731 | — | — | 16 replicated studies | 2 |
| Mean market price (not replicated) | market price | 0.436 | — | — | 25 non-replicated studies | 2 |
| Prediction error (market) | absolute | lower | — | — | vs. survey for both replicated and not | 2 |

## Methods & Implementation Details
- Prediction markets implemented Oct 2014 - end of Dec 2014 *(p.2)*
- Each replication result was described in a short paragraph with original study information *(p.2)*
- Market used continuous double-auction with automated market maker (LMSR) *(p.2)*
- Participants sent email list of Open Science Collaboration, plus direct contacts *(p.2)*
- Participants endowed with shares worth $50 per market set; allowed to bet in markets they were involved in *(p.2)*
- Two sets of markets: Set 1 (21 studies) and Set 2 (23 studies) due to incomplete replications at time of market creation *(p.2)*
- Pre-market survey: participants rated "How likely do you think it is that this hypothesis will be replicated on a scale from 0% to 100%?" *(p.2)*
- Survey also asked expertise and confidence *(p.2)*
- Replication success defined as: p-value < 0.05 in the same direction as original *(p.1-2)*
- Alternative replication criteria also examined: effect size within 95% CI, subjective assessment *(p.2)*
- Trading platform: web-based, provided by Consensus Point *(p.2)*
- For Bayesian analysis: posterior probability computed using observed replication rate and prior base rate pi_0 *(p.3)*

## Figures of Interest
- **Fig 1 (p.2):** Prediction market performance. Final market prices and survey means for each study, grouped by replicated/not replicated. Shows market prices discriminate better than survey means.
- **Fig 2 (p.2):** Scatterplot of market price vs. survey mean, colored by replication outcome. Shows positive correlation but market prices more extreme (better discrimination).
- **Fig 3 (p.3):** Detailed breakdown of replication outcomes by study, showing original p-value, effect size, market price, and survey mean.

## Results Summary
Of 41 completed replications, 16 (39%) replicated successfully at p < 0.05 in same direction. Prediction market prices correctly predicted 71% of outcomes using a >50% threshold (29/41), compared to 58% for the pre-market survey (24/41). Market prices were well-calibrated as probabilities: a linear probability model with market price as sole predictor yielded coefficient 0.966 (not significantly different from 1) and intercept 0.049 (not significantly different from 0). Studies with higher original effect sizes and lower original p-values tended to have higher market prices. The prediction error was lower for markets than surveys for both replicated and non-replicated studies. *(p.2-3)*

Bayesian analysis showed that for the 16 replicated studies, the posterior probability that the research hypothesis is true ranged from 92.5% to 97.5% (median 95%). For the 25 non-replicated studies, posterior probability ranged from 13% to 65% (median 63.5%), indicating that even non-replication does not necessarily mean the hypothesis is false. *(p.3)*

## Limitations
- Sample limited to 44 studies from three psychology journals (JPSP, JEP:LMC, Psych Science) in 2008 *(p.3)*
- Replication success defined narrowly as p < 0.05 in same direction — does not capture partial replications or effect size comparisons *(p.3)*
- Market participants were psychology researchers who may have had prior information about some studies *(p.2)*
- Trading was not dominated by a small number of traders, but participation was broad *(p.2)*
- Prediction markets cannot replace direct replication *(p.3)*
- Authors note common but incorrect interpretation that p < 0.05 implies 95% probability of replication *(p.3)*

## Arguments Against Prior Work
- Argues that informal assessments of reproducibility are insufficient — prediction markets provide a more rigorous, incentivized mechanism *(p.1)*
- Challenges the notion that replication is the only way to assess credibility — prediction markets can provide advance information about likely outcomes *(p.1)*
- Notes that survey-based approaches, while informative, are less accurate than markets (58% vs 71%) because markets aggregate information more efficiently through price mechanisms *(p.2-3)*

## Design Rationale
- Binary contract design ($1/$0) chosen so price directly interpretable as probability *(p.1-2)*
- Real money used (vs hypothetical) to ensure incentive compatibility *(p.2)*
- LMSR automated market maker ensures liquidity even with small trader pool *(p.2)*
- Pre-market survey conducted to establish baseline and avoid survey responses being influenced by market prices *(p.2)*
- Two market sets used because not all replications were complete when markets launched *(p.2)*

## Testable Properties
- Prediction market price > 0.5 should predict replication success with >50% accuracy (observed: 71%) *(p.2)*
- Linear probability model of replication on market price: slope should not be significantly different from 1 for well-calibrated markets *(p.2)*
- Linear probability model intercept should not be significantly different from 0 for well-calibrated markets *(p.2)*
- Market prices should have lower prediction error than survey means for replication outcomes *(p.2)*
- Studies with larger original effect sizes should have higher prediction market prices *(p.2)*
- Studies with smaller original p-values should have higher prediction market prices *(p.2)*

## Relevance to Project
This paper is directly relevant to propstore's uncertainty representation. Prediction markets provide empirically calibrated probabilities of reproducibility that could serve as evidence inputs to the opinion algebra. The finding that market prices are well-calibrated as probabilities (coefficient ~1, intercept ~0) means prediction market prices can be treated as calibrated belief evidence in the Jøsang subjective logic framework without additional calibration. The paper also demonstrates that base rates of replication (39% for psychology) are critical priors — relevant to propstore's handling of prior probabilities in the argumentation layer.

## Open Questions
- [ ] How do prediction market results compare for non-psychology fields?
- [ ] Can the calibration finding (slope ~1) be used to validate propstore's calibration pipeline?
- [ ] What is the relationship between prediction market prices and the Sensoy et al. 2018 evidence-to-opinion mapping?

## Related Work Worth Reading
- Open Science Collaboration (2015) "Estimating the reproducibility of psychological science" — the RPP project this paper's markets were based on (already in collection as Aarts_2015)
- Camerer et al. (2016) "Evaluating replicability of laboratory experiments in economics" — follow-up using prediction markets for economics replications (already in collection as Camerer_2016)
- Camerer et al. (2018) "Evaluating the replicability of social science experiments in Nature and Science" — larger-scale follow-up
- Gordon et al. (2020) "Are replication rates the same across academic fields?" — machine learning approach to predicting replication
- Altmejd et al. (2019) "Predicting the replicability of social science lab experiments" — prediction model follow-up
