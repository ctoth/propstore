---
title: "Subjective Logic Encodings for Training Neural Networks with Limited Data"
authors: "Jake Vasilakes, Chrysoula Zerva, Sophia Ananiadou"
year: 2025
venue: "arXiv preprint"
doi_url: "https://arxiv.org/abs/2502.12225"
produced_by:
  agent: "Claude Opus 4.6 (1M context)"
  skill: "paper-reader"
  timestamp: "2026-03-28T22:04:53Z"
---
# Subjective Logic Encodings for Training Neural Networks with Limited Data

## One-Sentence Summary

Proposes Subjective Logic Encodings (SLEs), a method for encoding multiple annotator labels as Dirichlet distributions via Subjective Logic opinions, then training classifiers to predict those distributions using KL divergence loss — explicitly separating annotator confidence from annotator reliability.

## Problem Addressed

Existing approaches for learning from labeled data assume gold-standard labels exist. Annotator disagreement is typically treated as noise to be removed (adjudication, label filtering). But annotator disagreement can't be neatly resolved, especially for subjective tasks like sentiment analysis or hate speech detection where disagreement is natural. This paper seeks to leverage inter-annotator disagreement to learn models that stay true to the inherent uncertainty of the task by treating annotations as *opinions* of the annotators, rather than gold-standard labels. *(p.1)*

## Key Contributions

- Introduces Subjective Logic Encodings (SLEs): a flexible framework for constructing classification targets that explicitly encode annotator opinions as Dirichlet distributions *(p.1)*
- SLEs encode labels as Dirichlet distributions with separate dimensions for first- and second-order uncertainty *(p.1)*
- Provides principled methods for encoding and aggregating various types of annotation uncertainty — annotator confidence, annotator reliability, and disagreements — into the targets *(p.1)*
- Shows how to train neural networks to predict Dirichlet distributions using KL divergence loss *(p.1)*
- Demonstrates SLEs are a generalization of other types of label encodings (hard, soft) *(p.4)*
- Makes code publicly available at https://github.com/jvasilakes/SLEs *(p.1)*

## Methodology

The paper decomposes annotation uncertainty into three sources *(p.2)*:

1. **Annotator Reliability**: An annotator may be highly confident but still incorrect — low reliability indicates measurement noise. Simple measures include inter-annotator agreement (Krippendorff's alpha, Fleiss' kappa, Grades of Evidence) *(p.2)*
2. **Annotator Confidence**: Borderline examples or unclear annotation guidelines can influence uncertainty in assigned labels. Individual annotator confidence is an indicator of measurement noise *(p.2)*
3. **Inter-Annotator Disagreement**: Even assuming perfect annotator reliability and confidence, multiple annotators may still assign different labels to the same event, indicating an inherent more fundamental source of uncertainty *(p.2)*

The authors model each annotator's label as a Subjective Logic opinion, aggregate opinions using cumulative belief fusion and trust discounting, then use the resulting Dirichlet distributions as training targets instead of one-hot encodings. *(p.3-4)*

## Key Equations / Statistical Models

### Opinion Representation (Jøsang 2016)

An SL subjective opinion regarding item $i$ according to agent $m$ over domain $K$:

$$
\omega_m^{(i)} = (\mathbf{b}_m^{(i)}, u_m^{(i)}, \mathbf{a}_m)
$$

Where: $\mathbf{b}_m^{(i)} \in [0,1]^K$ is a belief vector, $u_m^{(i)} \in [0,1]$ is uncertainty, $\mathbf{a}_m \in [0,1]^K$ is the base rate vector of prior probabilities over the event space. Parameters are subject to $u_m^{(i)} + \sum_{k=1}^{K} b_{m,k}^{(i)} = 1$. *(p.3)*

### Mapping to Dirichlet

$$
\alpha_k = \frac{b_{m,k}^{(i)} \cdot K \cdot w}{u_m^{(i)}} + a_{m,k} \cdot K
$$

Where: $w$ is a non-informative prior weight. *(p.3)* — Eq. (1)

### Expectation of Dirichlet from SL opinion parameters

$$
P_k^{(i)} = b_{m,k}^{(i)} + a_{m,k} \cdot u_m^{(i)}
$$

*(p.3)* — Eq. (2)

### Cumulative Belief Fusion

Cumulative belief fusion (denoted $\oplus$) combines two opinions regarding a single event — each as evidence of the true label distribution. *(p.3)*

$$
\omega_{A \oplus B}^{(i)} = \omega_A^{(i)} \oplus \omega_B^{(i)}
$$

Cumulative fusion reduces uncertainty $u$ by contributing evidence. As more opinions are fused, the uncertainty tends towards zero and the resulting Dirichlet approaches zero variance, equivalent to a categorical probability. *(p.3)* — Eq. (3)

### Trust Discounting

The trust discounting operator (denoted $\otimes$) increases the uncertainty of an opinion according to a separate opinion of the reliability of that annotator. *(p.3)*

$$
\omega_{\otimes}^{(i)} = \omega_r^{(m)} \otimes \omega_m^{(i)}
$$

Where $\omega_r^{(m)}$ is an opinion of the reliability of the subjective opinion $\omega_m^{(i)}$. *(p.3)* — Eq. (4)

### Constructing SLEs

Given a dataset of $N$ annotated examples $D = \{x^i, y^{(i)}\}$ where $x^i \in \mathbb{R}^F$ is the input space and $Y \in \{1,...,K\}^M$ is the label space over $K$ labels and $M$ annotators: *(p.3-4)*

1. Encode each individual judgment taking into account each of the sources of uncertainty described above *(p.4)*
2. Define a method for aggregating individual encoded judgments into a target distribution for training a classification model that accounts for label disagreement *(p.4)*

For annotator $m$, the opinion of the $i$-th example is $\omega_m^{(i)} = (\mathbf{b}_m^{(i)}, u_m^{(i)}, \mathbf{a}_m)$ where: *(p.4)*

$$
\mathbf{b}_m^{(i)} = c_m \cdot \mathbf{e}_{y_m^{(i)}}
$$

Where $\mathbf{e}_{y_m^{(i)}}$ is the one-hot encoding of the assigned label, $c_m$ is annotator confidence. *(p.4)* — Eq. (5)

The SLE aggregation for a given example $x^{(i)}$ uses cumulative fusion over all annotators then trust discounting: *(p.4)*

$$
\omega_\diamond^{(i)} = \bigoplus_{m=1}^{M} \left( \omega_r^{(m)} \otimes \omega_m^{(i)} \right)
$$

*(p.4)* — Eq. (6)

### Special Cases

When there is no information regarding reliability ($c_m = 1$ or uncertainty $u_m = 0$), the result is a dogmatic opinion $\omega_m^{(i)} = (\mathbf{1}_{y_m}, 0, 1/K)$ which is equivalent to a categorical probability (i.e., one-hot encoding). When there is no disagreement between annotators, the resulting opinion is equivalent to a one-hot encoded target. *(p.4)*

### Model Estimation (KL Divergence Loss)

The model predicts Dirichlet parameters $\hat{\alpha}$ from inputs. The loss is KL divergence between target distribution $\hat{P}$ and predicted distribution $\hat{D}$: *(p.7)*

$$
\mathcal{L}_d = D_{KL}(P \| \hat{D})
$$

*(p.7)* — Eq. (9)

Since the entropy term in Eq. 9 is a constant that depends only on the target distribution, minimization of cross-entropy is equivalent to minimization of KL divergence. The target loss function to simply the KL divergence: *(p.7)*

$$
\mathcal{L}_d = \sum_k \hat{\alpha}_k \log \frac{\hat{\alpha}_k}{\alpha_k}
$$

*(p.7)* — Eq. (10)

This is essentially the same loss function as Malinin & Gales (2019), without the additional KL term for out-of-distribution detection. *(p.7)*

### Overcoming KL Divergence Issues

Two issues with KL divergence objective: (1) KL divergence error surface is poorly suited to optimization when target distributions are sparse "near-flat" distributions; (2) "reverse" KL divergence produces $Q_k$ much less than $P$ is very small, which results in $Q$ that covers a majority of the space and is a poor predictor. *(p.7)*

Solutions applied: *(p.7-8)*
1. Follow Malinin & Gales (2019) and smooth dogmatic target opinions by redistributing a small $\varepsilon$ amount of belief mass to the uncertainty parameter, adding a small amount of density to the other corners of the probability simplex — Eq. (11)
2. Follow Malinin & Gales (2019) and use the reverse KL divergence — Eq. (12)

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of training samples | $N$ | — | — | — | 3 | Dataset size |
| Number of annotators | $M$ | — | — | — | 3 | Per example |
| Number of class labels | $K$ | — | — | — | 3 | Classification target dimension |
| Annotator confidence | $c_m$ | — | — | [0,1] | 4 | Per-annotator, controls belief mass |
| Annotator reliability | $r_m$ | — | — | [0,1] | 4 | Per-annotator, controls trust discounting |
| Base rate / prior | $\mathbf{a}_m$ | — | 1/K | [0,1]^K | 3 | Prior probability vector; learnable in §6 |
| Belief mass smoothing | $\varepsilon$ | — | small | — | 7 | Redistributed to uncertainty for near-dogmatic opinions |
| Synthetic confidence alpha | $\alpha$ | — | — | {1, 10} | 4 | Beta distribution parameter for synthetic confidence |
| Synthetic confidence beta | $\beta$ | — | — | {0, 1, 10} | 4 | Beta distribution parameter for synthetic confidence |
| Synthetic reliability alpha' | $\alpha'$ | — | — | {1, 10} | 4 | Beta distribution parameter for synthetic reliability |
| Synthetic reliability beta' | $\beta'$ | — | — | {0, 1, 10} | 4 | Beta distribution parameter for synthetic reliability |
| Non-informative prior weight | $w$ | — | — | — | 3 | Used in Dirichlet parameter mapping |

## Effect Sizes / Key Quantitative Results

| Outcome | Measure | Value | CI | p | Population/Context | Page |
|---------|---------|-------|----|---|--------------------|------|
| Synthetic (a) vary reliability | F1 | 0.837-0.872 | — | — | SLE best across all conditions | 13 |
| Synthetic (a) vary reliability | JSD↓ | 0.130-0.127 | — | — | SLE best across all conditions | 13 |
| Synthetic (a) vary reliability | NES↑ | 0.989-0.990 | — | — | SLE best across all conditions | 13 |
| CIFAR-10S (gold+crowd) | F1 | 0.643 | — | — | SLE | 9 |
| CIFAR-10S (gold+crowd) | NES↑ | 0.923 | — | — | SLE | 9 |
| MFRC (gold+crowd) | F1 | 0.438 | — | — | SLE | 9 |
| MFRC (crowd only) | F1 | 0.417 | — | — | SLE | 9 |
| CrowdTruth (gold+crowd) | NES↑ | 0.528 | — | — | SLE | 9 |
| Corn Abuse (crowd only) | F1 | 0.153 | — | — | SLE | 9 |
| RTE (crowd only) | F1 | 0.437 | — | — | SLE tied | 9 |

## Methods & Implementation Details

- **Dirichlet Neural Networks**: Use Malinin & Gales (2019) Prior Networks — predict Dirichlet parameters directly. Each data point modeled as a sample from a categorical distribution parameterized by a Dirichlet. *(p.6)*
- **Model Architecture for CIFAR-10S**: ResNet-12 model with a single linear output layer. *(p.8)*
- **Model for MRE**: Same model and training procedure as Fan et al. (2019) — a fine-tuned BERT sentence classifier with a single linear output layer. *(p.8)*
- **Model for CrowdTruth**: BERT sentence classifier with a graph convolutional network output layer as in Fang et al. (2023). *(p.8)*
- **Model for MFRC**: BERT sentence classifier with a single linear output layer. *(p.8)*
- **Softmax replaced by**: A new output layer to compute the belief and uncertainty parameters, and use of the KL-divergence objective function. *(p.10)*
- **Learning SLEs**: Rather than using annotator uncertainty from data, use a Dirichlet latent variable model trained using variational inference to recover a prior over the predicted class probabilities given gold-standard labels. *(p.7)*
- **Learnable base rates $\mathbf{a}_m$**: The base rate (prior) can be learned as part of the estimation process, as opposed to being fixed at $1/K$. *(p.7)*
- **Synthetic data generation**: $N$ $K$-class samples with $M=10$ annotators. Confidence and reliability drawn from Beta distributions with varying parameters. Algorithm 1 on p.5 gives the generative process. *(p.4-5)*

### Algorithm 1: Synthetic Data Generation Process *(p.5)*

**Require:** Two sets of Beta distribution parameters $(\alpha, \beta)$ and $(\alpha', \beta')$
1. for $i = 1$ to $N$ do
2. $c = \text{Beta}(\alpha, \beta)$ — Sample single annotator confidence
3. $r = \text{Beta}(\alpha', \beta')$ — Sample single annotator reliability
4. for $m = 1$ to $M$ do
5. $g = \text{permute}(y, r)$ — Permute $y$ with probability $r$
6. $y_m^{(i)} = \text{randomflip}(g, c)$ — Flip label with probability $c$

## Figures of Interest

- **Fig 1 (p.6):** F1, JSD, and NES results for MV, Soft, SLE cumulative fusion, and SLE with filtered annotations on synthetic data across different ranges of uncertainty. Shows SLE consistently outperforms baselines across varying confidence and reliability. CrowdTruth results nearly identical to Soft.

## Results Summary

### Synthetic Data *(p.5-6)*
SLEs are better able to recover the true distribution from crowd annotations than MV and Soft, particularly when information regarding annotator confidence and reliability improves results for all methods. The difference in JSD and NES between unfiltered and filtered SLEs is much less than MV and Soft, suggesting SLEs are better able to capture the true distribution even in the presence of noisy labels. *(p.5)*

### Real-World Data *(p.8-9)*
Datasets: CIFAR-10S (image classification, 10 classes, 5 annotators per example, crowd annotations unreliable), MFRC (4000 sentences from PubMed, cause-or-event relation, annotated by 15 annotators), CrowdTruth (3000 sentences from different medical corpora, 8 annotators for variety of abuse types), RTE (800 sentence pairs, semantic similarity, 10 annotators). *(p.8)*

Comparison of methods in SLEs: MV, CE, KL, CrowdTruth, MTLSL, SLE. Only CE and KL are able to learn from annotator confidence, but only via probabilistic labels, and only CrowdTruth is able to learn from annotator reliability. SLEs, on the other hand, are able to incorporate all three sources of annotation uncertainty and do so without large changes to the model architecture — only modifying the final output layer. *(p.9)*

SLE achieves best or near-best F1 and NES across datasets. *(p.9)*

## Limitations

- Real-world datasets contain limited sources of uncertainty. CIFAR-10S is the only dataset with both annotator confidence and crowd annotations *(p.9)*
- Results on real-world datasets with gold labels generally mixed; SLEs with gold labels generally outperform standard cross-entropy training on gold labels as well as MTLSL, but this improvement may be an artifact of the different objective function (KL vs CE) *(p.10)*
- CE and KL tend to outperform all other methods, although SLEs perform best on datasets that contain more sources of uncertainty *(p.10)*
- Hard and soft metrics don't always agree in rankings *(p.10)*
- "Reverse" KL has issues with sparse target distributions *(p.7)*
- This work focuses on inducing predictive uncertainty of the model given gold-standard labels — does not add support for OOD data using additional KL term *(p.7)*

## Arguments Against Prior Work

- Majority Voting discards minority opinions and disagreement information, treating it as noise *(p.1)*
- Label adjudication and filtering methods assume disagreement should be resolved, not preserved *(p.1)*
- Existing methods under "data perspectivism" mostly encode only one source of uncertainty — annotator disagreement — treating it as inter-annotator variation. They don't separate annotator confidence from reliability *(p.2)*
- Soft voting (probabilistic labels from frequency) conflates reliability with confidence *(p.2)*
- CrowdTruth can only learn from annotator reliability, not confidence *(p.9)*
- CE and KL methods can only learn from confidence via probabilistic labels, not reliability *(p.9)*
- Sensoy et al. (2018) propose a Dirichlet neural network for modeling prediction uncertainty that is related but focuses on inducing predictive uncertainty of the model given gold-standard labels, not on learning from annotation uncertainty *(p.6)*

## Design Rationale

- Choice of Subjective Logic over raw Dirichlet: SL provides a principled decomposition of belief, uncertainty, and base rates with well-defined fusion and discounting operators *(p.3)*
- Cumulative fusion chosen over averaging fusion: cumulative fusion treats each annotation as independent evidence, reducing uncertainty as more opinions are fused *(p.3)*
- Trust discounting applied before fusion: allows per-annotator reliability weighting before aggregation *(p.4)*
- KL divergence loss instead of cross-entropy: KL divergence is the natural loss for Dirichlet target distributions; cross-entropy is equivalent when targets are fixed *(p.7)*
- Reverse KL chosen over forward KL: better handles sparse/near-flat target distributions *(p.7-8)*
- Base rates as learnable parameters: allows the model to learn task-specific priors rather than assuming uniform *(p.7)*

## Testable Properties

- When all annotators agree and have perfect confidence/reliability, SLE reduces to one-hot encoding *(p.4)*
- Cumulative fusion of $M$ opinions with $c_m=1$ and $r_m=1$ for all $m$ yields a dogmatic opinion equivalent to majority voting *(p.4)*
- Adding trust discounting with low reliability increases uncertainty in the fused opinion *(p.3)*
- SLE with filtered annotations should outperform SLE with unfiltered annotations when noise is high *(p.5)*
- SLE should match or outperform soft voting on JSD and NES metrics *(p.5-6)*
- The Dirichlet parameters from SLE should have higher entropy than one-hot targets when disagreement exists *(p.4)*
- Learnable base rates should improve over fixed uniform base rates *(p.7)*

## Relevance to Project

**Highly relevant.** This paper directly addresses the propstore project's use of Subjective Logic (Jøsang 2001) and evidential deep learning (Sensoy et al. 2018). Key connections:

1. **Opinion representation**: propstore already implements SL opinions with $(b,d,u,a)$. This paper shows how to construct opinions from annotator labels and use them as ML training targets — extending the pipeline from "opinions as reasoning artifacts" to "opinions as learning signals."
2. **Cumulative fusion and trust discounting**: propstore implements these operators (Jøsang 2001). This paper provides concrete use cases for applying them to aggregate multi-source evidence.
3. **Dirichlet-SL bridge**: The mapping between SL opinions and Dirichlet distributions (Eq. 1) is the same bridge used in propstore's Sensoy 2018 implementation. This paper validates that bridge in a training context.
4. **Learnable base rates**: propstore's current base rate $a$ is fixed. This paper provides a principled way to learn it from data.
5. **Annotation uncertainty decomposition**: The three-way decomposition (confidence, reliability, disagreement) maps directly to propstore's provenance tracking.

## Open Questions

- [ ] How does the learnable base rate $\mathbf{a}_m$ interact with propstore's existing opinion algebra?
- [ ] Can the SLE framework be applied to propstore's claim extraction pipeline where multiple LLM "annotators" produce stance labels?
- [ ] How does the KL divergence loss compare to propstore's existing calibration (Guo et al. 2017)?
- [ ] The paper assumes all annotators label the same examples — how to handle sparse/partial annotation matrices?

## Related Work Worth Reading

- Malinin & Gales (2019) — Prior Networks for predictive uncertainty estimation via Dirichlet outputs
- Uma et al. (2020) — "A Case for Soft Loss Functions" — AAAI workshop on learning from disagreement
- Uma et al. (2021) — "Learning from Disagreement: A Survey" — comprehensive survey of the area
- Davani et al. (2022) — Dealing with disagreements in computational linguistics
- Fang et al. (2023) — CrowdTruth method for aggregating crowd annotations
- Fan & Toni (2015) — Referenced for MRE model architecture

## Collection Cross-References

### Already in Collection
- [[Josang_2001_LogicUncertainProbabilities]] — foundational SL paper; Vasilakes uses Jøsang 2016 textbook operators (cumulative fusion, trust discounting) which extend the 2001 core
- [[Josang_2010_CumulativeAveragingFusionBeliefs]] — defines the cumulative and averaging fusion operators used as aggregation methods in SLE construction
- [[Sensoy_2018_EvidentialDeepLearningQuantifyClassification]] — Dirichlet neural networks for uncertainty quantification; Vasilakes explicitly extends this by learning from annotation uncertainty rather than just modeling prediction uncertainty
- [[Guo_2017_CalibrationModernNeuralNetworks]] — calibration of neural network outputs; related to the KL divergence training objective and Dirichlet output calibration
- [[Kaplan_2015_PartialObservableUpdateSubjectiveLogic]] — partial observation updates in SL; relevant to the learnable base rate extension
- [[vanderHeijden_2018_MultiSourceFusionOperationsSubjectiveLogic]] — multi-source fusion operators in SL; directly relevant as SLEs aggregate multiple annotator opinions via fusion
- [[Margoni_2024_SubjectiveLogicMetaAnalysis]] — applies SL fusion to meta-analysis; parallel application of the same operators to a different aggregation problem

### New Leads (Not Yet in Collection)
- Malinin & Gales (2019) — "Reverse KL Divergence Training of Prior Networks" — the loss function SLEs use is essentially theirs; Prior Networks predict Dirichlet distributions directly
- Uma et al. (2021) — "Learning from Disagreement: A Survey" — comprehensive survey of disagreement-aware learning methods
- Jøsang (2016) — SL textbook; the comprehensive reference for all operators used in this paper → NOW IN COLLECTION: [Subjective Logic: A Formalism for Reasoning Under Uncertainty](../Josang_2016_SubjectiveLogic/notes.md)

### Now in Collection (previously listed as leads)
- [Subjective Logic: A Formalism for Reasoning Under Uncertainty](../Josang_2016_SubjectiveLogic/notes.md) — Jøsang 2016 textbook. Vasilakes uses operators (cumulative fusion, trust discounting) defined in Ch. 12 / 14 of this book. The 2016 book is the comprehensive reference; Josang 2001 is the seed paper.

### Conceptual Links (not citation-based)
- [[Sensoy_2018_EvidentialDeepLearningQuantifyClassification]] — Sensoy maps evidence counts to Dirichlet parameters for prediction uncertainty; Vasilakes maps annotator opinions to Dirichlet parameters for training targets. Same mathematical bridge (SL opinion ↔ Dirichlet), different direction of application.
- [[Josang_2010_CumulativeAveragingFusionBeliefs]] — Vasilakes' SLE aggregation is a direct application of cumulative fusion from this paper, with trust discounting applied per-annotator before fusion. The fusion properties (monotonic uncertainty reduction with more evidence) are exactly why SLEs converge to categorical distributions when annotators agree.
- [[Margoni_2024_SubjectiveLogicMetaAnalysis]] — Both papers apply SL fusion to aggregate multiple sources of evidence (annotators vs. studies). The three-way uncertainty decomposition (confidence, reliability, disagreement) in Vasilakes parallels the distinction between within-study and between-study uncertainty in meta-analysis.
