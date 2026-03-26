---
title: "On Calibration of Modern Neural Networks"
authors: "Chuan Guo, Geoff Pleiss, Yu Sun, Kilian Q. Weinberger"
year: 2017
venue: "ICML 2017 (Proceedings of the 34th International Conference on Machine Learning)"
doi_url: "https://proceedings.mlr.press/v70/guo17a.html"
---

# On Calibration of Modern Neural Networks

## One-Sentence Summary
Demonstrates that modern deep neural networks are significantly miscalibrated (overconfident), identifies depth/width/batch-norm/weight-decay as contributing factors, and shows that temperature scaling — a single-parameter post-hoc method — is the simplest and most effective calibration fix.

## Problem Addressed
Classification models in safety-critical applications (medical diagnosis, autonomous driving, pedestrian detection) require not just accurate predictions but reliable confidence estimates. Modern neural networks, despite higher accuracy than older models, produce poorly calibrated confidence scores — their predicted probabilities do not reflect true likelihoods. *(p.0)*

## Key Contributions
- Empirical demonstration that modern neural networks are miscalibrated, in contrast to older/shallower networks *(p.0)*
- Identification of network depth, width, batch normalization, and weight decay as factors affecting calibration *(p.2-3)*
- Comprehensive comparison of post-hoc calibration methods: histogram binning, isotonic regression, BBQ, Platt scaling, temperature scaling, matrix scaling, vector scaling *(p.4-5)*
- Demonstration that temperature scaling — a single parameter — is as effective or better than all other methods *(p.5-7)*
- Formal derivation that temperature scaling is the unique solution to the entropy maximization principle with an appropriate likelihood equation *(p.10)*

## Methodology
Extensive experiments on image classification (CIFAR-10, CIFAR-100, ImageNet, SVHN) and NLP tasks (20 Newsgroups, Reuters, SST Binary, SST Fine-Grained) using modern architectures (ResNet, DenseNet, Wide ResNet, LeNet, TreeLSTM). Measure ECE and MCE before and after applying various calibration methods on a held-out validation set. *(p.6)*

## Key Equations

### Expected Calibration Error (ECE)

$$
ECE = \sum_{m=1}^{M} \frac{|B_m|}{n} |acc(B_m) - conf(B_m)|
$$

Where: $B_m$ = set of samples in bin $m$, $n$ = total samples, $acc(B_m)$ = accuracy of bin $m$, $conf(B_m)$ = mean predicted confidence of bin $m$, $M$ = number of bins (typically 15).
*(p.1)*

### Maximum Calibration Error (MCE)

$$
MCE = \max_{m \in \{1,...,M\}} |acc(B_m) - conf(B_m)|
$$

Where: same variables as ECE. Used in high-stakes applications where worst-case calibration matters.
*(p.2)*

### Temperature Scaling

$$
\hat{q}_i = \max_k \sigma_{SM}(z_i / T)_k
$$

Where: $z_i$ = logit vector for sample $i$, $T$ = temperature (single scalar $> 0$), $\sigma_{SM}$ = softmax function, $k$ = class index.
*(p.5)*

$T$ is optimized with respect to NLL on the validation set:

$$
\min_T -\sum_{i} \log(\hat{\pi}(y_i | z_i, T))
$$

*(p.5)*

### Platt Scaling (Binary Extension)

$$
\hat{q}_i = \sigma(az_i + b)
$$

Where: $a, b$ = learned scalar parameters, $z_i$ = logit, $\sigma$ = sigmoid. For multiclass, this generalizes to matrix/vector scaling.
*(p.4)*

### Matrix Scaling

$$
\hat{q}_i = \max_k \sigma_{SM}(Wz_i + b)_k
$$

Where: $W \in \mathbb{R}^{K \times K}$ = weight matrix, $b \in \mathbb{R}^{K}$ = bias vector, $K$ = number of classes.
*(p.5)*

### Vector Scaling

$$
\hat{q}_i = \max_k \sigma_{SM}(diag(w) \cdot z_i + b)_k
$$

Where: $w \in \mathbb{R}^{K}$ = per-class weight vector (diagonal matrix), $b \in \mathbb{R}^{K}$ = per-class bias.
*(p.5)*

### ECE as Riemann-Stieltjes Sum (Supplementary)

$$
E[\hat{p} | \hat{p} \in I_m] \cdot P(\hat{p} \in I_m) \approx \int_{I_m} r \, dp(r)
$$

ECE using $M$ bins converges to the $L_1$ norm Riemann-Stieltjes sum of the cumulative distribution function of $\hat{p}$ over [0,1]. Hence ECE is the primary empirical metric for measuring miscalibration.
*(p.10)*

### Temperature Scaling Derivation from Entropy Maximization

Given a sample's logit vector $z_1, ..., z_K$ and class labels $y_1, ..., y_n$, temperature scaling is the unique solution to the entropy maximization problem:

$$
\max_{T} \quad H(\hat{\pi}) = -\sum_k \hat{\pi}_k \log \hat{\pi}_k
$$

subject to:

$$
\sum_k \hat{\pi}_k = 1
$$

$$
\sum_k \hat{\pi}_k z_k = c
$$

Where $c$ is a constant determined by the constraint. This recovers $\hat{\pi}_k \propto e^{z_k / T}$.
*(p.10)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Temperature | T | - | 1.0 | > 0 | p.5 | Single scalar; T > 1 softens distribution, T < 1 sharpens |
| Number of ECE bins | M | - | 15 | 10-20 | p.1 | Used for reliability diagrams and ECE computation |
| Platt scaling slope | a | - | learned | - | p.4 | Logistic regression parameter on logits |
| Platt scaling intercept | b | - | learned | - | p.4 | Logistic regression bias parameter |
| Matrix scaling weights | W | - | learned | $\mathbb{R}^{K \times K}$ | p.5 | Full linear transformation of logits |
| Vector scaling weights | w | - | learned | $\mathbb{R}^{K}$ | p.5 | Per-class scaling of logits |
| Vector/matrix scaling bias | b | - | learned | $\mathbb{R}^{K}$ | p.5 | Per-class additive bias |

## Implementation Details

### Temperature Scaling Implementation *(p.7)*
- After training the neural network, freeze all parameters
- Add single scalar parameter $T$ initialized to 1.0
- Divide logits by $T$ before softmax
- Optimize $T$ on validation set w.r.t. NLL using a simple gradient solver (e.g., LBFGS or conjugate gradient)
- Since this is a 1D convex optimization, it can be found via line search
- Temperature scaling does NOT change the model's predictions (argmax preserved) — only the confidence values change
- $T > 1$: raises entropy (softens), makes model less confident — typical case for modern overconfident nets
- $T < 1$: lowers entropy (sharpens), makes model more confident

### BBQ Implementation *(p.4)*
- Extension of histogram binning using Bayesian model averaging
- Considers multiple binning schemes and scores each using Bayesian score
- Produces a single calibrated prediction as weighted combination

### Platt Scaling for Multiclass *(p.4-5)*
- Original Platt scaling is for binary classification
- Extension to multiclass: matrix scaling (full $W$ matrix) or vector scaling (diagonal $W$)
- Matrix scaling has $K^2 + K$ parameters — computationally complex for large $K$
- Vector scaling has $2K$ parameters — scales linearly with number of classes
- Temperature scaling is the special case where $W = (1/T) \cdot I$ and $b = 0$

### Practical Recipe *(p.7)*
- BBQ is the most effective binning method
- Temperature scaling and matrix/vector scaling are the most effective parametric methods
- Temperature scaling wins due to simplicity: 1 parameter vs $K^2+K$ or $2K$
- For implementation: train model normally, then apply temperature scaling on validation set
- Setting $T = 1$ during training, find optimal $T$ on validation, apply at inference

## Figures of Interest
- **Fig 1 (p.0):** Reliability diagrams comparing a 5-layer LeNet (well-calibrated, ECE=3.27%) vs 110-layer ResNet (miscalibrated, ECE=14.4%) on CIFAR-100. The ResNet is visibly overconfident — bars shifted right of the diagonal.
- **Fig 2 (p.2):** Effect of depth, width, batch normalization, and weight decay on accuracy vs. ECE. Deeper/wider models are more accurate but less calibrated. Batch norm improves accuracy but worsens calibration. More weight decay improves calibration.
- **Fig 3 (p.3):** NLL overfitting: training NLL continues to decrease while test NLL increases even as test error improves. Models overfit to NLL without improving calibration.
- **Fig 4 (p.7):** Reliability diagrams for CIFAR-100 before/after calibration with 4 methods. Temperature scaling achieves the best-calibrated reliability diagram.
- **Fig S1 (p.11):** Entropy and NLL on CIFAR-100 showing pre-calibration entropy decreasing during training. Temperature scaling raises entropy to the optimal level. Shows T selected at validation NLL minimum.
- **Fig S2-S4 (p.13):** Reliability diagrams for all datasets — temperature scaling consistently produces the most calibrated results.

## Results Summary

### ECE Results (Table 1, p.6; Table S1, p.11)
- Before calibration: ECE ranges from 3-15% depending on model/dataset
- Temperature scaling reduces ECE to 0.8-2% across almost all configurations
- Temperature scaling matches or beats all other methods on nearly every dataset/model combination
- On CIFAR-100 with ResNet-110: uncalibrated ECE=14.40%, temperature scaling reduces to 1.34%
- On ImageNet with DenseNet-161: uncalibrated ECE=6.34%, temperature scaling reduces to 1.38%
- BBQ is a close competitor among binning methods but has more parameters

### NLP Results *(p.6-7)*
- NLP models (TreeLSTM on SST) also benefit from calibration
- Temperature scaling effective on text classification as well
- ECE on SST Fine-Grained: uncalibrated 9.18%, temperature scaling reduces to 3.90%

### MCE Results (Table S1, p.11)
- Temperature scaling also achieves best or near-best MCE
- MCE is more sensitive to binning scheme than ECE

### Key Quantitative Finding *(p.7)*
- Matrix and vector scaling perform similarly on small-class problems but scale poorly to hundreds of classes (ImageNet)
- Temperature scaling's single parameter avoids overfitting even on small validation sets
- Histogram binning improves calibration on most datasets but does not outperform temperature scaling

## Limitations
- ECE depends on binning scheme — number of bins $M$ affects the metric *(p.1)*
- MCE is sensitive to the binning scheme *(p.11)*
- Calibration methods evaluated only on classification (not regression, generation, or structured prediction) *(p.6)*
- Temperature scaling does not change accuracy — if the model makes wrong predictions with high confidence, those remain wrong *(p.5)*
- All calibration methods require a held-out validation set *(p.4-5)*
- Results may not transfer directly to tasks beyond classification *(p.7)*
- Measurements may be affected by dataset splits and the particular binning scheme *(p.6)*

## Arguments Against Prior Work
- Modern training practices (deeper models, batch normalization, reduced weight decay) have inadvertently caused miscalibration — prior work on calibration focused on older, shallower models that were naturally better calibrated *(p.0, p.2-3)*
- NLL minimization, the standard training objective, does NOT guarantee calibration on test data — NLL is a proper scoring rule only when the model perfectly recovers the true distribution *(p.1, p.3)*
- Histogram binning and isotonic regression are non-parametric and require more data to be effective; they cannot be as easily applied in the multiclass setting *(p.5, p.7)*
- Matrix scaling and vector scaling, while effective, have too many parameters for large-class problems and can overfit *(p.5, p.7)*

## Design Rationale
- Temperature scaling chosen as a special case of Platt/matrix/vector scaling because it has minimum parameters (1 vs $K^2+K$) and thus maximum resistance to overfitting *(p.5)*
- Post-hoc calibration chosen over calibration-aware training because it is orthogonal to training and requires no retraining *(p.4)*
- NLL chosen as the optimization objective for temperature scaling because it is a proper scoring rule — minimizing NLL on the validation set produces calibrated predictions *(p.5)*
- ECE chosen as the primary metric rather than NLL because ECE directly measures the gap between confidence and accuracy, which is the practical concern *(p.1-2)*

## Testable Properties
- Temperature scaling must not change the model's top-1 predictions (argmax invariant under positive scalar division) *(p.5)*
- $T > 1$ must increase softmax entropy (soften the distribution) *(p.5)*
- $T < 1$ must decrease softmax entropy (sharpen the distribution) *(p.5)*
- ECE must decrease monotonically as calibration improves (by construction, ECE = 0 iff perfectly calibrated) *(p.1)*
- On a well-calibrated model, the reliability diagram bars should match the diagonal *(p.0)*
- Training NLL continues to decrease even as test NLL increases — overfitting to confidence *(p.3)*
- Deeper models should have higher ECE than shallower models with comparable accuracy *(p.2)*
- Batch normalization should improve accuracy but worsen ECE *(p.2)*
- More weight decay should improve calibration (lower ECE) *(p.2)*

## Relevance to Project
This paper is directly relevant to propstore's handling of neural network output scores. Key implications:

1. **Raw softmax scores from NLI models and embedding similarity are NOT calibrated probabilities.** They cannot be treated as probability estimates without post-hoc calibration. This validates the need for propstore to NOT treat bare floats as ground-truth probabilities.

2. **Temperature scaling provides a simple, principled way to recalibrate scores** if propstore needs to convert model outputs to something more probability-like. A single parameter T, optimized on validation data, is sufficient.

3. **The degree of miscalibration varies by model architecture** — deeper/wider models with batch normalization (i.e., essentially all modern transformer-based models) are expected to be overconfident. This means NLI confidence scores and embedding similarity scores are systematically biased upward.

4. **For the argumentation layer**: when using model confidence to weight arguments or set defeat thresholds, raw scores will systematically overstate certainty. Any threshold-based reasoning over uncalibrated scores will produce different results than threshold-based reasoning over calibrated scores.

5. **The non-commitment principle is validated**: storing raw scores with provenance (model, method, calibration status) and deferring interpretation to render time is the correct architecture, since calibration is a post-hoc transformation that may change.

## Open Questions
- [ ] How does miscalibration manifest in modern transformer/LLM architectures (paper predates transformers)?
- [ ] Does temperature scaling work for NLI entailment/contradiction/neutral three-way classification?
- [ ] What is the relationship between calibration and embedding cosine similarity (which is not a softmax output)?
- [ ] Can temperature scaling be applied per-task in a multi-task model?
- [ ] What validation set size is needed for reliable T estimation?

## Related Work Worth Reading
- Zadrozny & Elkan 2001, 2002 — Histogram binning and isotonic regression for calibration
- Naeini et al. 2015 — Bayesian Binning into Quantiles (BBQ)
- Platt 1999 — Platt scaling (original logistic calibration)
- Niculescu-Mizil & Caruana 2005 — Predicting good probabilities with supervised learning (calibration comparison)
- Lakshminarayanan et al. 2017 — Deep ensembles for uncertainty estimation
- Kuleshov et al. 2018 — Reliable confidence estimation via online learning
- Vaicenavicius et al. — Statistical tests for calibration
- DeGroot & Fienberg 1983 — Comparison and evaluation of forecasters (reliability diagrams origin)

## Collection Cross-References

### Conceptual Links (not citation-based)
- [[Sensoy_2018_EvidentialDeepLearningQuantifyClassification]] -- **Strong.** Problem-solution pair: Guo demonstrates that softmax outputs are systematically miscalibrated (overconfident), establishing the problem that Sensoy's Evidential Deep Learning addresses structurally by replacing softmax with Dirichlet distribution outputs. Guo's temperature scaling is a post-hoc fix; EDL is an architectural fix that outputs both class probabilities and explicit uncertainty mass.
