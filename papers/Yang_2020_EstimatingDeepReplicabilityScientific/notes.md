---
title: "Estimating the deep replicability of scientific findings using human and artificial intelligence"
authors: "Yang Yang, Youyou Wu, Brian Uzzi"
year: 2020
venue: "Proceedings of the National Academy of Sciences"
doi_url: "https://doi.org/10.1073/pnas.1909046117"
produced_by:
  agent: "claude-opus-4-6"
  skill: "paper-reader"
  timestamp: "2026-03-28T21:06:47Z"
---
# Estimating the deep replicability of scientific findings using human and artificial intelligence

## One-Sentence Summary
This paper trains a machine learning model (narrative + statistics features from paper text) to predict whether a published study will replicate, achieving 0.65-0.78 accuracy across out-of-sample datasets from diverse disciplines.

## Problem Addressed
The majority of scientific papers fail replication, and failed papers circulate as quickly as replicating ones. Manual replication is expensive (average RPP study cost ~$45k, 17 months from claim to completion). Prediction markets and surveys work but are resource-intensive and unscalable. There is no accurate, scalable method for identifying findings at risk of replication failure. *(p.1)*

## Key Contributions
- A machine learning model that predicts replicability comparably to prediction markets (the best present-day method) while being far more scalable *(p.1)*
- Demonstration that text-based (narrative) features outperform reported-statistics-based features for predicting replication *(p.1, p.2)*
- Evidence that n-grams (higher-order word combinations) are the key discriminative features, not individual bias/novelty words *(p.1, p.5)*
- Out-of-sample validation across multiple disciplines (psychology, economics, social sciences, Nature/Science papers) *(p.3-4)*
- No evidence of bias based on topics, journals, disciplines, base rates of failure, persuasion words, or novelty words *(p.1, p.5)*

## Study Design
- **Type:** Supervised ML classification (logistic regression + word2vec features), validated on manually replicated study datasets
- **Population:** Training: 234 manually replicated studies from RPP, Many Labs 1, Many Labs 2 (132 replicated, 102 nonreplicated). Out-of-sample test sets: 5 independent datasets totaling ~417 additional studies. *(p.2, Table 1)*
- **Intervention(s):** Three model variants: (1) narrative-only (word2vec on abstracts), (2) reviewer metrics-only (reported statistics), (3) combined narrative + reviewer metrics *(p.2)*
- **Comparator(s):** Base rate of human reviewers, prediction markets, replication surveys *(p.1, p.3-4)*
- **Primary endpoint(s):** Accuracy (proportion correctly classified as replicate/nonreplicate) and top-k precision (proportion replicating among top-k ranked) *(p.2-3)*
- **Secondary endpoint(s):** AUC, sensitivity, specificity, F1, Cohen's kappa *(p.3)*
- **Follow-up:** Cross-validation within training set + 5 independent out-of-sample test sets *(p.2-4)*

## Methodology
Three-stage model development *(p.2)*:

**Stage 1 (word2vec training):** Trained word2vec (skip-gram, 200 dimensions) on 2 million abstracts from Microsoft Academic Graph (MAG) database to learn word embeddings for scientific vocabulary. Used window size of 5 and minimum word count of 10. Each paper's abstract represented by averaging its constituent word vectors into a single 200-dimensional vector. *(p.2)*

**Stage 2 (logistic regression on manually replicated studies):** Trained a logistic regression classifier on the 200-dimensional word2vec representations of manually replicated papers. Training set: RPP (96 studies from 3 psychology journals), Many Labs 1 (16 studies), and Many Labs 2 (28 studies) = 234 total (after excluding 6 ML2 studies also in RPP). Stratified 10-fold cross-validation repeated 100 times with random partitions. *(p.2)*

**Stage 3 (out-of-sample testing):** Tested on 5 independent datasets never seen during training *(p.3-4, Table 1)*:
- Test I: 16 economics experiments (Camerer et al. 2016) - 0.75 accuracy
- Test II: 57 pre-registered replications (SSRP, Camerer et al. 2018) - 0.65 accuracy
- Test III: 14 economics experiments (Camerer et al. 2016b) - 0.71 accuracy
- Test IV: 100 RPP papers scored by prediction markets (Dreber et al. 2015) - 0.74 accuracy (narrative+metrics combined)
- Test V: 130 high-impact papers from DARPA SCORE (Nature/Science papers) - 0.78 accuracy

**Three model variants:**
1. **Narrative-only model:** Uses only word2vec features from paper abstracts *(p.2)*
2. **Reviewer metrics-only model:** Uses 8 reported statistics (p-value, effect size, sample size, etc.) that quantitatively represent a paper's findings *(p.2)*
3. **Combined model (narrative + reviewer metrics):** Both feature sets together *(p.2)*

## Key Equations / Statistical Models

The core model is logistic regression on word2vec features:

$$
P(\text{replicate}) = \sigma(\mathbf{w}^T \mathbf{x} + b)
$$
Where: $\sigma$ is the sigmoid function, $\mathbf{x}$ is the 200-dimensional word2vec representation of a paper's abstract (average of constituent word vectors), $\mathbf{w}$ is the learned weight vector, $b$ is the bias term.
*(p.2)*

Word2vec representation of a paper:

$$
\mathbf{x}_{\text{paper}} = \frac{1}{N} \sum_{i=1}^{N} \mathbf{v}_{w_i}
$$
Where: $\mathbf{v}_{w_i}$ is the word2vec embedding for word $w_i$ in the abstract, $N$ is the number of words in the abstract.
*(p.2)*

Top-k precision:

$$
\text{top-}k\text{ precision} = \frac{\text{number replicating in top-}k\text{ ranked}}{k}
$$
Where: papers are ranked by model's predicted probability of replication, and precision is measured among the $k$ highest-ranked papers.
*(p.2-3)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Word2vec dimensions | d | - | 200 | - | 2 | Also tested 100, 300; similar results |
| Word2vec window size | - | - | 5 | - | 2 | Skip-gram model |
| Word2vec min word count | - | - | 10 | - | 2 | Words appearing <10 times excluded |
| Training corpus size | - | abstracts | 2,000,000 | - | 2 | From MAG database |
| Training set size (total) | - | studies | 234 | - | 2 | 132 replicated, 102 nonreplicated |
| RPP studies | - | studies | 96 | - | 2 | From 3 psychology journals |
| Many Labs 1 studies | - | studies | 16 | - | 2 | |
| Many Labs 2 studies | - | studies | 28 | - | 2 | After excluding 6 overlapping with RPP |
| Cross-validation folds | k | - | 10 | - | 2 | Stratified |
| CV repetitions | - | - | 100 | - | 2 | Random partition each time |
| Base rate (reviewer threshold) | - | - | 0.56 | - | 3 | 56 of 96 RPP studies failed = 56/96 |
| Reviewer metrics count | - | features | 8 | - | 2 | p-value, effect size, sample size, etc. |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| In-sample accuracy (narrative-only) | Accuracy | 0.69 | - | - | 10-fold CV, training set | 2 |
| In-sample accuracy (metrics-only) | Accuracy | 0.67 | - | - | 10-fold CV, training set | 3 |
| In-sample accuracy (combined) | Accuracy | 0.71 | - | - | 10-fold CV, training set | 3 |
| In-sample top-k precision (combined) | Top-5 precision | 0.78 | - | - | Training set | 2 |
| In-sample top-k precision (combined) | Top-6 precision | 0.73 | - | - | Training set | 2 |
| Combined vs metrics-only improvement | Accuracy diff | +0.03 | - | p < 0.01 (binomial) | Training set | 3 |
| Combined vs metrics-only improvement | Top-k precision diff | +0.05 | - | p < 0.01 (binomial) | Training set | 3 |
| Test I accuracy (economics) | Accuracy | 0.75 | - | - | Camerer 2016, n=16 | 3 |
| Test I top-6 precision | Top-6 precision | 0.67 | - | - | Camerer 2016 | 3 |
| Test II accuracy (SSRP) | Accuracy | 0.65 | - | - | Camerer 2018, n=57 pre-reg | 3-4 |
| Test II top-6 precision | Top-6 precision | 0.71 | - | - | SSRP | 4 |
| Test III accuracy (economics) | Accuracy | 0.71 | - | - | n=14 | 4 |
| Test IV accuracy (narrative+metrics) | Accuracy | 0.74 | - | - | 100 RPP papers w/ prediction markets | 4 |
| Test IV top-6 precision (narrative+metrics) | Top-6 precision | 0.73 | - | - | RPP w/ prediction markets | 4 |
| Test V accuracy (DARPA SCORE) | Accuracy | 0.78 | - | - | 130 Nature/Science papers | 4 |
| Prediction market accuracy (Test IV) | Accuracy | 0.71 | - | - | Dreber et al. 2015 | 4 |
| Survey accuracy (Test IV) | Accuracy | 0.74 | - | - | Dreber et al. 2015 | 4 |
| ML vs prediction market (Test IV) | Accuracy diff | +0.03 | - | - | ML: 0.74 vs market: 0.71 | 4 |
| Prediction market accuracy (Test V) | Accuracy | 0.74 | - | - | DARPA SCORE | 4 |
| ML accuracy (Test V) | Accuracy | 0.78 | - | - | DARPA SCORE | 4 |
| Citation rate difference | - | indistinguishable | - | - | Replicating vs nonreplicating papers | 1 |

## Methods & Implementation Details
- Word2vec trained with skip-gram architecture on MAG abstracts *(p.2)*
- Used standard word2vec settings with 200 dimensions; tested 100 and 300 dimensions with similar cross-validation results *(p.2)*
- Paper representation: average of all word vectors in abstract *(p.2)*
- Logistic regression classifier (not deep learning) *(p.2)*
- Stratified 10-fold cross-validation repeated 100 times to assess in-sample stability *(p.2)*
- Reviewer metrics (8 features): P-values and effect size, also known as "reviewer metrics", prediction markets, and surveys *(p.1)*
- The 8 reviewer metrics were used with standard settings to quantitatively represent a paper's findings; the model used every other word in the corpus of words in the training set *(p.2)*
- Model comparison tests used Kolmogorov-Smirnov (KS), Wilcoxon rank-sum, Cohen's kappa, and Anderson-Darling tests *(p.3)*
- For DARPA SCORE test (Test V), averaged each paper's average prediction from its 100 random cross-validation runs *(p.4)*

## Figures of Interest
- **Fig 1 (p.1):** Citation rates of replicating and nonreplicating studies are indistinguishable. Measured direct citations and second-degree citations. Of 47 RPP papers that failed replication, many are cited at the same yearly rate as papers that successfully replicated.
- **Fig 2 (p.2):** Visualizes the raw prediction data for the narrative-only ML model. Shows accuracy levels plotting each paper's average prediction across 100 stratified 10-fold CV runs. Vertical bars are 80% CIs calculated by bootstrapping 100 random selections.
- **Fig 3 (p.3):** Accuracy and top-k precision results of four out-of-sample tests (Tests I-IV). Shows barplots of accuracy and top-6 precision for linear, naive Bayes, and SVM classifiers alongside the logistic regression model. Also includes narrative-only, metrics-only, and combined (narrative+metrics) model comparisons.
- **Table 1 (p.2):** Training and out-of-sample test datasets. Lists all datasets (RPP, ML1, ML2, and 5 test sets) with number of studies, categories, original and replication methods/sample sizes.
- **Table 2 (p.5):** Tests of inherited bias in the machine learning model. Lists 10 categories of potential bias (e.g., field of study, journal prestige, sample size, persuasion words) and shows none significantly affected accuracy.

## Results Summary
The combined narrative+metrics model achieved the best in-sample accuracy of 0.71 and top-5 precision of 0.78. *(p.2-3)* The narrative-only model (0.69 accuracy) outperformed the reviewer metrics-only model (0.67 accuracy). *(p.3)* In out-of-sample tests, the model achieved accuracy of 0.65-0.78 across 5 diverse test sets spanning psychology, economics, social sciences, and high-impact Nature/Science papers. *(p.3-4)* The model's accuracy was comparable to prediction markets (0.71-0.74) and surveys (0.74) but far more scalable. *(p.4)* For DARPA SCORE papers (Test V, highest impact), the model achieved its best accuracy of 0.78, outperforming prediction markets (0.74). *(p.4)*

Key finding: the narrative text of papers carries stronger replication signals than reported statistics. N-grams (higher-order word combinations) correlate with replication outcomes, though individual "persuasion" or "novelty" words do not. *(p.5)*

## Limitations
- The model's accuracy is higher when trained on text rather than reported statistics, but the reasons why text is more predictive are not fully understood *(p.5)*
- N-grams are difficult for humans to interpret -- they capture higher-order word combinations that humans have difficulty processing *(p.1, p.5)*
- The model cannot identify specific methodological flaws; it provides a probability estimate, not a diagnosis *(p.5)*
- Small training set (234 studies) relative to the complexity of scientific literature *(p.2)*
- Training data limited primarily to psychology with some economics; generalizability to other fields needs further validation *(p.2, Table 1)*
- The model was tested on abstracts only, not full paper text *(p.2)*
- Out-of-sample test sets are relatively small (14-130 studies) *(Table 1)*

## Arguments Against Prior Work
- Manual replication is too expensive and slow to scale (average $45k and 17 months per RPP study) *(p.1)*
- Prediction markets, while accurate, require extensive human resources and are not scalable to the volume of publications *(p.1)*
- Prior work found only positive correlations between reviewer metrics and replicability but did not combine metrics into a single model *(p.3)*
- Reviewer metrics alone (p-values, effect sizes, sample sizes) produce lower accuracy than text-based features, suggesting reported statistics may not capture all relevant signals *(p.3)*
- Prior approaches that use "red flag" words (persuasion language, novelty words like "remarkable" or "unexpected") did not find these to be predictive of replication failure *(p.5, Table 2)*

## Design Rationale
- **Word2vec over bag-of-words:** Word2vec captures semantic relationships and inter-dependencies among words, whereas bag-of-words misses context. The 200-dimensional embedding nominally represents these interdependencies. *(p.2)*
- **Abstract text over full paper:** Abstracts are consistently available and structured; full papers vary in format. The abstract condenses the key narrative. *(p.2)*
- **Logistic regression over complex classifiers:** Tested linear, naive Bayes, and SVM classifiers; logistic regression performed comparably or better. Simpler model reduces overfitting risk on small training set. *(p.3, Fig 3)*
- **Combined model over narrative-only:** Adding reviewer metrics to narrative features improved accuracy by 3% and top-k precision by 5% (both p < 0.01). *(p.3)*
- **Three separate model variants:** To disentangle whether predictive power comes from narrative features, statistical features, or their combination. *(p.2)*

## Testable Properties
- The narrative-only model should achieve accuracy > base rate (0.56) on RPP-like datasets *(p.2-3)*
- Combined model accuracy should exceed metrics-only model accuracy *(p.3)*
- Word2vec dimensions of 100, 200, 300 should produce similar cross-validation results *(p.2)*
- Citation rates of replicating vs nonreplicating papers should be statistically indistinguishable *(p.1)*
- No single bias category (topic, journal, discipline, sample size, persuasion words, novelty words) should significantly predict model accuracy when tested independently *(p.5, Table 2)*
- The model trained on text should outperform the model trained on reported statistics alone *(p.3)*
- Out-of-sample accuracy should be in range 0.65-0.78 across diverse test sets *(p.3-4)*
- N-gram features should show higher correlation with replication than unigrams *(p.5)*

## Relevance to Project
This paper is directly relevant to propstore's argumentation and evidence assessment layers. It provides:
1. **Replicability as a meta-property of claims:** The model's replication probability could serve as a weight or uncertainty factor on claims derived from empirical studies.
2. **Evidence quality assessment:** The finding that narrative text predicts replication better than reported statistics suggests that surface-level statistical summaries may not capture true evidence quality.
3. **Calibration relevance:** The model outputs probabilities that could feed into the subjective logic opinion algebra (Josang 2001) as evidence-based belief/disbelief values with appropriate calibration.
4. **Argumentation framework input:** Replication probability could inform defeat relations -- a claim from a study with low replication probability might be undercut by a meta-claim about its replicability.

## Open Questions
- [ ] Could the word2vec + logistic regression approach be applied to propstore's claim text to estimate claim reliability?
- [ ] How does the 200-dim word2vec representation relate to modern transformer embeddings -- would BERT/SciBERT improve accuracy?
- [ ] Could the model's features inform the argumentation layer's preference ordering (more replicable studies get higher preference)?
- [ ] The paper uses abstracts only -- would full-text features from propstore's paper collection improve predictions?

## Collection Cross-References

### Already in Collection
- [[Aarts_2015_EstimatingReproducibilityPsychologicalScience]] — RPP dataset provides the primary training data (96 studies from 3 psychology journals)
- [[Altmejd_2019_PredictingReplicabilitySocialScience]] — Direct predecessor using statistical features to predict replication; Yang extends with narrative text features and shows text outperforms statistics
- [[Camerer_2016_EvaluatingReplicabilityLaboratoryExperiments]] — Provides Test I and Test III out-of-sample datasets (economics experiments)
- [[Camerer_2018_EvaluatingReplicabilitySocialScience]] — Provides Test II out-of-sample dataset (SSRP, 21 Nature/Science replications)
- [[Begley_2012_DrugDevelopmentRaiseStandards]] — Cited as evidence of replication crisis in preclinical cancer research (ref 5)
- [[Errington_2021_InvestigatingReplicabilityPreclinicalCancer]] — Related replication study in cancer biology; provides ground-truth replication rates that could validate Yang's model in biomedical domain

### New Leads (Not Yet in Collection)
- Dreber et al. (2015) — "Using Prediction Markets to Estimate the Reproducibility of Scientific Research" — the primary prediction market comparator (Test IV dataset)

### Cited By (in Collection)
- [[Altmejd_2019_PredictingReplicabilitySocialScience]] — cites Yang 2020 as direct successor combining human and AI predictions (ref 35)
- [[Gordon_2021_PredictingReplicability—AnalysisSurveyPrediction]] — cites Yang 2020 as extending forecasting with machine learning (ref 33)

### Supersedes or Recontextualizes
- Extends [[Altmejd_2019_PredictingReplicabilitySocialScience]] by demonstrating that narrative text features outperform the statistical features Altmejd used, and achieves comparable accuracy to prediction markets without requiring human participants

### Conceptual Links (not citation-based)
- [[Border_2019_NoSupportHistoricalCandidate]] — **Strong.** Border demonstrates a high-profile replication failure (candidate gene studies for depression). Yang's model could have flagged these studies as at-risk based on their narrative text, providing a concrete test case for the model's utility.
- [[Errington_2021_InvestigatingReplicabilityPreclinicalCancer]] — **Strong.** Both study replication empirically but in different domains. Errington's cancer biology replication rates (3-82% depending on criterion) provide an independent validation domain for Yang's text-based prediction model, which was trained primarily on psychology/economics.
- [[Gordon_2021_PredictingReplicability—AnalysisSurveyPrediction]] — **Strong.** Gordon pools prediction market and survey data across replication projects and finds market accuracy of 73% and survey accuracy of 71%. Yang achieves 0.65-0.78 with ML alone, directly comparable. Gordon's DARPA SCORE dataset is Yang's Test V.

## Related Work Worth Reading
- Open Science Collaboration 2015: "Estimating the reproducibility of psychological science" (the RPP study, ground truth dataset) *(ref 1)*
- Camerer et al. 2016: "Evaluating replicability of laboratory experiments in economics" (Test I and III datasets) *(ref 11)*
- Camerer et al. 2018: "Evaluating the replicability of social science experiments in Nature and Science" (Test II dataset, SSRP) *(ref 12)*
- Dreber et al. 2015: "Using prediction markets to estimate the reproducibility of scientific research" (Test IV, prediction market comparison) *(ref 8)*
- Gordon et al. 2021: DARPA SCORE project (Test V dataset) *(ref 9)*
- Altmejd et al. 2019: "Predicting the replicability of social science lab experiments" (prediction + survey methods) *(ref 10)*
