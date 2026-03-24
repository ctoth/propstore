---
title: "Evidential Deep Learning to Quantify Classification Uncertainty"
authors: "Murat Sensoy, Lance Kaplan, Melih Kandemir"
year: 2018
venue: "NeurIPS 2018 (32nd Conference on Neural Information Processing Systems)"
doi_url: "https://doi.org/10.48550/arXiv.1806.01768"
---

# Evidential Deep Learning to Quantify Classification Uncertainty

## One-Sentence Summary
Replaces softmax outputs with Dirichlet distribution parameters learned via a novel loss function, enabling a neural network to output both class probabilities and per-prediction uncertainty (epistemic vs aleatoric) in a single forward pass without sampling or ensembles.

## Problem Addressed
Standard deep learning classifiers output softmax probabilities that cannot distinguish between confident predictions and uncertain ones — a network trained on digits cannot say "I don't know" when shown an anomalous input, it just picks the highest softmax value. Bayesian approaches (MC Dropout, ensembles) address this but require multiple forward passes. This paper provides uncertainty quantification in a single forward pass by treating predictions as subjective opinions grounded in Dempster-Shafer Theory of Evidence and Subjective Logic. *(p.1)*

## Key Contributions
- Places a Dirichlet distribution over class probabilities instead of outputting point estimates, enabling principled uncertainty quantification *(p.1)*
- Connects neural network outputs to subjective logic opinions via belief masses and uncertainty mass *(p.3)*
- Proposes a novel loss function (Type II Maximum Likelihood / Bayes risk with SSE) that trains the network to output evidence for Dirichlet parameters *(p.4-5)*
- Adds a KL divergence regularizer that shrinks evidence for incorrect classes toward zero *(p.6)*
- Demonstrates improved out-of-distribution detection and adversarial robustness compared to standard softmax and dropout-based methods *(p.7-8)*

## Methodology

### From Softmax to Dirichlet

**Standard approach:** For K-class classification, a neural network outputs logits passed through softmax to get class probabilities $p_k$. The likelihood is multinomial, and the loss is cross-entropy. *(p.2)*

**This paper's approach:** Instead of predicting class probabilities directly, predict the *parameters of a Dirichlet distribution* over class probabilities. The network outputs *evidence* for each class, which parameterizes a Dirichlet. *(p.3-4)*

### Dempster-Shafer Theory of Evidence (DST) and Subjective Logic

DST generalizes Bayesian theory to subjective frames of discernment. A belief mass assignment over K mutually exclusive classes has: *(p.3)*
- **Belief mass** $b_k$ for each class $k = 1, \ldots, K$
- **Uncertainty mass** $u$
- Constraint: $u + \sum_{k=1}^{K} b_k = 1$

Subjective Logic (SL) connects this to Dirichlet distributions: a subjective opinion corresponds to a Dirichlet distribution $\text{Dir}(\mathbf{p} | \boldsymbol{\alpha})$ with parameters $\alpha_k$. *(p.3)*

### The Key Mapping: Evidence to Dirichlet to Opinion

The network outputs non-negative *evidence* $e_k \geq 0$ for each class. The Dirichlet parameters are: *(p.3)*

$$
\alpha_k = e_k + 1
$$

The total Dirichlet strength is:

$$
S = \sum_{k=1}^{K} \alpha_k = \sum_{k=1}^{K} (e_k + 1) = K + \sum_{k=1}^{K} e_k
$$

The belief mass and uncertainty are: *(p.3)*

$$
b_k = \frac{e_k}{S} = \frac{\alpha_k - 1}{S}
$$

$$
u = \frac{K}{S}
$$

Where:
- $e_k$: evidence for class $k$ (non-negative network output)
- $\alpha_k$: Dirichlet concentration parameter for class $k$
- $S$: Dirichlet strength (sum of all $\alpha_k$)
- $b_k$: belief mass for class $k$
- $u$: uncertainty mass
- $K$: number of classes
*(p.3)*

**Critical insight:** When total evidence is zero ($e_k = 0$ for all $k$), then $S = K$, $b_k = 0$ for all $k$, and $u = 1$ (maximum uncertainty). As evidence grows, uncertainty shrinks. *(p.3)*

### Expected Class Probabilities

The expected probability for class $k$ under the Dirichlet is: *(p.3)*

$$
\hat{p}_k = \frac{\alpha_k}{S}
$$

This is the mean of the Dirichlet distribution for class $k$.

## Key Equations

### Dirichlet PDF

$$
D(\mathbf{p} | \boldsymbol{\alpha}) = \frac{\Gamma\left(\sum_{k=1}^{K} \alpha_k\right)}{\prod_{k=1}^{K} \Gamma(\alpha_k)} \prod_{k=1}^{K} p_k^{\alpha_k - 1}
$$

Where: $\mathbf{p}$ is on the K-dimensional unit simplex, $\alpha_k > 0$ for all $k$, $\Gamma$ is the gamma function.
*(p.3)*

### Loss Function: Type II Maximum Likelihood (Bayes Risk with SSE)

The paper evaluates three loss functions and recommends the **sum of squares** (SSE) variant of the Bayes risk, called the Type II ML loss: *(p.4-5)*

$$
\mathcal{L}_i = \sum_{j=1}^{K} (y_{ij} - \hat{p}_{ij})^2 + \frac{\hat{p}_{ij}(1 - \hat{p}_{ij})}{S_i + 1}
$$

Where:
- $y_{ij}$: one-hot label (1 if sample $i$ belongs to class $j$, else 0)
- $\hat{p}_{ij} = \alpha_{ij} / S_i$: expected probability for class $j$
- $S_i = \sum_k \alpha_{ik}$: Dirichlet strength for sample $i$
- First term: squared prediction error
- Second term: variance of the Dirichlet — penalizes flat distributions
*(p.5)*

This decomposes into minimizing both prediction error AND the variance of the Dirichlet experienced by the neural net for each sample. *(p.5)*

**Proposition 1.** The variance-based loss $L^{var}$ is always less than the error-based loss $L^{err}$ for $\alpha_{ij} \geq 1$, making SSE the preferred choice. *(p.5, p.12)*

### KL Divergence Regularizer

To prevent the network from assigning high evidence to incorrect classes, a KL divergence term penalizes deviation from a uniform Dirichlet for non-target classes: *(p.6)*

$$
\mathcal{L} = \sum_{i=1}^{N} \mathcal{L}_i^{err} + \lambda_t \text{KL}\left[\text{Dir}(\mathbf{p}_i | \tilde{\boldsymbol{\alpha}}_i) \| \text{Dir}(\mathbf{p}_i | \mathbf{1})\right]
$$

Where: $\tilde{\boldsymbol{\alpha}}_i = \mathbf{y}_i + (1 - \mathbf{y}_i) \odot \boldsymbol{\alpha}_i$ is the Dirichlet parameters after removing evidence for the correct class. *(p.6)*

The KL divergence between two Dirichlet distributions is computed as: *(p.6)*

$$
\text{KL}\left[\text{Dir}(\mathbf{p} | \boldsymbol{\alpha}) \| \text{Dir}(\mathbf{p} | \boldsymbol{\beta})\right] = \ln \frac{\Gamma(\sum_k \alpha_k)}{\Gamma(\sum_k \beta_k)} + \sum_{k=1}^{K} \ln \frac{\Gamma(\beta_k)}{\Gamma(\alpha_k)} + \sum_{k=1}^{K} (\alpha_k - \beta_k)\left[\psi(\alpha_k) - \psi\left(\sum_j \alpha_j\right)\right]
$$

Where: $\psi$ is the digamma function. $\boldsymbol{\beta} = \mathbf{1}$ (uniform Dirichlet). *(p.6)*

### Annealing Coefficient

$\lambda_t$ gradually increases during training: *(p.6)*

$$
\lambda_t = \min\left(1.0, \frac{t}{10}\right)
$$

Where: $t$ is the current training epoch. This allows the model to explore the parameter space early and avoid premature convergence to uniform distributions. *(p.6)*

### Entropy of Predictive Distribution (Uncertainty Metric)

$$
H = -\sum_{k=1}^{K} \hat{p}_k \ln \hat{p}_k
$$

Where $\hat{p}_k = \alpha_k / S$. Maximum entropy = $\ln K$. Used for OOD detection. *(p.7)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of classes | $K$ | - | - | $\geq 2$ | 3 | Determines Dirichlet dimensionality |
| Evidence for class k | $e_k$ | - | - | $\geq 0$ | 3 | Network output after activation (ReLU/exp/softplus) |
| Dirichlet parameter | $\alpha_k$ | - | - | $\geq 1$ | 3 | $\alpha_k = e_k + 1$ |
| Dirichlet strength | $S$ | - | - | $\geq K$ | 3 | $S = \sum_k \alpha_k$ |
| Belief mass | $b_k$ | - | - | $[0, 1]$ | 3 | $b_k = e_k / S$ |
| Uncertainty mass | $u$ | - | - | $(0, 1]$ | 3 | $u = K/S$; 1 = total ignorance |
| KL annealing coefficient | $\lambda_t$ | - | $\min(1, t/10)$ | $[0, 1]$ | 6 | Ramps over first 10 epochs |
| Uncertainty threshold (EDL) | - | - | 1.1 | - | 7 | Entropy threshold for "uncertain" classification |
| LeNet filter sizes | - | pixels | 20, 50 | - | 7 | First and second conv layers for MNIST |
| LeNet hidden units | - | - | 500 | - | 7 | Fully connected layer |

## Implementation Details

### Network Architecture
- Standard classification architectures work (LeNet, VGG) — only the final layer changes *(p.4)*
- Replace softmax with a non-negative activation (ReLU, softplus, or exponential) to produce evidence *(p.4)*
- Evidence vector $\mathbf{e} = f(\mathbf{x} | \Theta)$ where $f$ is the network, mapped to Dirichlet params via $\alpha_k = e_k + 1$ *(p.4)*
- The output layer has K neurons (one per class), same as softmax *(p.4)*

### Activation Function for Evidence
- Network outputs must be non-negative to serve as evidence *(p.4)*
- Paper uses ReLU as the evidence activation in experiments *(p.6)*
- Alternatives: softplus, exponential *(p.4)*

### Training Procedure
1. Forward pass: compute evidence $\mathbf{e} = f(\mathbf{x} | \Theta)$ *(p.4)*
2. Compute Dirichlet params: $\alpha_k = e_k + 1$ *(p.3)*
3. Compute loss: SSE-based Bayes risk + annealed KL regularizer *(p.5-6)*
4. Backpropagate and update weights *(p.4)*

### Loss Function Selection
Three options evaluated *(p.4-5)*:
- **Cross-entropy based** (Eq. 3): $\mathcal{L} = \sum_j -y_{ij}(\psi(\alpha_{ij}) - \psi(S_i))$ — generates excessively high belief for classes, less stable *(p.5)*
- **SSE / Type II ML** (Eq. 5, RECOMMENDED): Minimizes prediction error + Dirichlet variance — best empirical performance *(p.5)*
- **Log-likelihood based** (Eq. 4): Also applies sum of squares to log-space — not preferred *(p.5)*

### KL Regularization Details
- Removes evidence for the *correct* class before computing KL: $\tilde{\alpha}_k = y_k + (1 - y_k) \cdot \alpha_k$ *(p.6)*
- This means: for the correct class, $\tilde{\alpha}_j = 1$ (uniform prior); for incorrect classes, $\tilde{\alpha}_k = \alpha_k$ *(p.6)*
- KL divergence then penalizes non-uniform Dirichlet for wrong classes → drives wrong-class evidence toward zero *(p.6)*
- Annealing $\lambda_t$ is critical: without it, network converges to uniform Dirichlet too early *(p.6)*

### Inference
- Single forward pass gives evidence → Dirichlet params → belief masses + uncertainty *(p.4)*
- Classification: $\hat{y} = \arg\max_k \hat{p}_k = \arg\max_k \alpha_k$ *(p.3)*
- Uncertainty: $u = K/S$ or entropy $H = -\sum_k \hat{p}_k \ln \hat{p}_k$ *(p.3, p.7)*
- No sampling, no ensembles, no multiple forward passes required *(p.1)*

### Uncertainty Types
- **Vacuity (epistemic uncertainty):** $u = K/S$ — high when total evidence is low (model hasn't seen similar data) *(p.3)*
- **Dissonance (aleatoric-like):** When evidence is spread across multiple classes — captured by entropy of the expected probabilities *(p.3)*
- **Key distinction from softmax:** Softmax always sums to 1 and can't distinguish "confident class A" from "uncertain between A and B." EDL's uncertainty mass $u$ provides this missing signal. *(p.1-2)*

### Experimental Setup
- **MNIST:** LeNet with 20, 50 filters, 500 hidden units, trained with Adam *(p.6-7)*
- **CIFAR-10:** VGG-16 architecture *(p.6)*
- **Baselines compared:** Standard softmax, MC Dropout, Deep Ensembles *(p.7)*
- **OOD detection:** Tested on notMNIST (letters) for MNIST-trained model; last 5 categories of CIFAR-10 for CIFAR-5-trained model *(p.7-8)*
- **Adversarial:** FGSM and Cleverhans library attacks with varying perturbation $\epsilon$ *(p.8)*
- **Code available at:** https://muratsensoy.github.io/uncertainty.html *(p.6)*

## Figures of Interest
- **Fig 1 (p.2):** Rotating digit classified by softmax vs EDL — softmax always confident, EDL shows high uncertainty at ambiguous angles
- **Fig 2 (p.7):** Accuracy vs uncertainty threshold — EDL accuracy increases as uncertain predictions are filtered out
- **Fig 3 (p.8):** Empirical CDF of entropy — EDL assigns much higher entropy to OOD samples than other methods
- **Fig 4 (p.8):** Accuracy and entropy vs adversarial perturbation $\epsilon$ on MNIST — EDL maintains uncertainty awareness under attack
- **Fig 5 (p.9):** Accuracy and entropy vs adversarial perturbation $\epsilon$ on CIFAR5

## Results Summary
- EDL achieves comparable classification accuracy to standard networks (99.1% MNIST, 81.2% CIFAR-10) *(p.7)*
- Significantly better OOD detection: EDL associates high uncertainty with OOD samples while Dropout does not reliably *(p.7-8)*
- Better adversarial robustness: EDL's uncertainty increases with adversarial perturbation strength, providing a natural defense signal *(p.8)*
- Dropout places high confidence on wrong predictions; EDL associates higher uncertainty with wrong predictions *(p.8)*
- Table 1: EDL accuracy on MNIST 99.1%, CIFAR-10 81.2%; comparable to baselines *(p.7)*

## Limitations
- Authors acknowledge the cross-entropy variant of the loss produces excessively high beliefs *(p.5)*
- The KL regularizer can be too strong without annealing — needs careful scheduling *(p.6)*
- Only evaluated on image classification (MNIST, CIFAR) — no text, tabular, or other modalities *(p.7)*
- Comparison limited to Dropout and standard softmax; later work would compare to more recent methods *(p.7)*
- The uncertainty threshold of 1.1 for entropy is dataset-specific *(p.7)*

## Arguments Against Prior Work
- **Against standard softmax:** Cannot represent uncertainty — always assigns all probability mass to classes, no "I don't know" option. A network can say "I don't know" only by outputting near-uniform probabilities, which is indistinguishable from a genuinely ambiguous input. *(p.1-2)*
- **Against MC Dropout:** Requires multiple forward passes (computationally expensive), and still places high confidence on adversarial examples because dropout uncertainty comes from weight perturbation, not evidence absence. *(p.1, p.8)*
- **Against Deep Ensembles:** Requires training and maintaining multiple models; expensive. *(p.1)*
- **Against Gaussian Processes:** Don't scale to large datasets; GP uncertainty modeling limited to specific function classes. *(p.9)*
- **Against BNN with variational inference:** Calculating the resultant posterior predictive distribution of BNNs cannot be calculated in closed form; requires Monte Carlo integration. *(p.9)*

## Design Rationale
- **Why Dirichlet over softmax?** Dirichlet is a distribution *over* probability distributions — it naturally captures second-order uncertainty (uncertainty about the probabilities themselves). Softmax is a point estimate. *(p.3-4)*
- **Why SSE loss over cross-entropy loss?** Cross-entropy variant generates excessively high Dirichlet parameters; SSE decomposes cleanly into prediction error + variance minimization. *(p.5)*
- **Why KL regularizer?** Without it, the network can achieve low loss by assigning high evidence to multiple classes simultaneously. KL term forces non-target evidence toward zero. *(p.6)*
- **Why anneal $\lambda_t$?** Starting with full KL regularization causes premature convergence to uniform Dirichlet (all $\alpha_k = 1$, maximum uncertainty). Annealing lets the network first learn discriminative features, then refine evidence allocation. *(p.6)*
- **Why evidence = ReLU output?** Evidence must be non-negative (you can't have negative evidence for a class). ReLU naturally provides this. *(p.4)*

## Testable Properties
- **Uncertainty bounds:** $u \in (0, 1]$ where $u = K/S$; $u = 1$ when all $e_k = 0$. *(p.3)*
- **Belief-uncertainty sum:** $\sum_k b_k + u = 1$ must hold for all predictions. *(p.3)*
- **Evidence-Dirichlet monotonicity:** Increasing $e_k$ must increase $\alpha_k$ and decrease $u$. *(p.3)*
- **Proposition 1:** $L_i^{var} < L_i^{err}$ for any $\alpha_{ij} \geq 1$. *(p.5, p.12)*
- **Proposition 2:** For correct class $j$, loss decreases when new evidence is added to $\alpha_{ij}$ and increases when evidence is removed. *(p.5, p.12)*
- **Proposition 3:** For correct class $j$, loss decreases when evidence is removed from the *largest incorrect* Dirichlet parameter $\alpha_{il}$ such that $l \neq j$. *(p.5, p.12)*
- **OOD entropy:** Predictions on OOD data should have entropy approaching $\ln K$ (uniform). *(p.7-8)*
- **KL regularizer effect:** With $\lambda_t > 0$, incorrect-class evidence should converge toward 0. *(p.6)*

## Relevance to Project
This paper is directly relevant to propstore's need for alternatives to bare-float probability mapping. Key applications:

1. **Replacing point probabilities in stance/claim confidence:** Instead of storing a single float "probability" for a claim or stance, store Dirichlet parameters ($\alpha_k$ values) that represent both the expected probability AND the uncertainty about that probability. This fits propstore's non-commitment discipline — the Dirichlet carries more information than a point estimate.

2. **Subjective Logic connection:** The paper's belief mass / uncertainty framework maps directly to subjective logic opinions, which can integrate with the argumentation layer (Dung AF, ASPIC+). An argument's strength could be a subjective opinion $(b, d, u, a)$ rather than a bare float.

3. **Evidence accumulation without commitment:** New evidence increases Dirichlet parameters without collapsing to a single answer — perfectly aligned with the "lazy until rendering" principle. Evidence from multiple sources can be combined (Dempster's rule or Dirichlet parameter addition) and the render layer decides how to interpret the resulting distribution.

4. **Uncertainty-aware filtering:** The render layer can filter by uncertainty mass $u$ — showing only claims/stances where the system has sufficient evidence, while preserving uncertain ones in storage.

## Open Questions
- [ ] How does Dempster-Shafer combination rule interact with multiple evidence sources in propstore's context? [Addressed by Josang_2001_LogicUncertainProbabilities — the consensus operator (Theorem 7) combines opinions from independent sources, reducing uncertainty; it is commutative, associative, and resolves Zadeh's paradox where standard Dempster's rule fails]
- [ ] Can Dirichlet parameters from different models/sources be meaningfully combined? [Addressed by Josang_2001_LogicUncertainProbabilities — evidence counts (r, s) simply add when combining via consensus in the evidence space (Def 13), which corresponds to adding Dirichlet alpha parameters]
- [ ] What is the relationship between this paper's uncertainty and the ATMS assumption-based framework?
- [ ] How to handle non-categorical (continuous) parameters — would a Normal-inverse-gamma distribution be the analog?
- [ ] The paper uses ReLU for evidence — what happens with very large evidence values in practice (numerical stability)?

## Related Work Worth Reading
- **Jøsang (2016):** Subjective Logic — the formal framework for opinions, referenced extensively *(p.3)*
- **Dempster (1968):** Original Dempster-Shafer theory of evidence *(p.3)*
- **Gal and Ghahramani (2016):** Dropout as a Bayesian approximation — the main baseline compared against *(p.9)*
- **Lakshminarayanan et al. (2017):** Deep Ensembles — another uncertainty quantification baseline *(p.10)*
- **Malinin and Gales (2018):** Predictive uncertainty estimation via prior networks — related concurrent work using Dirichlet outputs *(p.9)*

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — not directly cited, but the subjective logic opinions produced by EDL feed naturally into Dung-style argumentation frameworks as argument strengths

### New Leads (Not Yet in Collection)
- Jøsang (2016) — "Subjective Logic: A Formalism for Reasoning Under Uncertainty" — the formal framework underpinning EDL's opinion mapping; essential for implementing belief mass / uncertainty in propstore -> NOW IN COLLECTION (foundational version): [[Josang_2001_LogicUncertainProbabilities]]
- Gal and Ghahramani (2016) — "Dropout as a Bayesian Approximation" — primary competing uncertainty method; needed for comparison
- Malinin and Gales (2018) — "Predictive Uncertainty Estimation via Prior Networks" — concurrent Dirichlet-output approach with different training objective (reverse KL)
- Lakshminarayanan et al. (2017) — "Simple and Scalable Predictive Uncertainty Estimation Using Deep Ensembles" — ensemble baseline for uncertainty quantification

### Now in Collection (previously listed as leads)
- [[Josang_2001_LogicUncertainProbabilities]] — The foundational 2001 paper defining subjective logic's opinion algebra (b, d, u, a), which the 2016 book cited by Sensoy extends. Provides the core bijective mapping between opinions and Beta distributions (Def 12) that underpins EDL's Dirichlet-to-opinion bridge, plus the consensus operator for combining evidence from multiple sources and the discounting operator for trust transitivity.

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)
- [[Falkenhainer_1987_BeliefMaintenanceSystem]] — **Strong.** Both build on Dempster-Shafer theory for evidence combination: Falkenhainer applies DS to TMS-style dependency networks with continuous belief propagation, while Sensoy applies DS to neural network outputs via the Dirichlet/subjective-logic bridge. Together they represent the symbolic (BMS) and connectionist (EDL) approaches to the same problem of graded evidence tracking. Falkenhainer's BMS could serve as the propagation substrate for EDL-produced belief masses in propstore.
- [[Guo_2017_CalibrationModernNeuralNetworks]] — **Strong.** Problem-solution pair: Guo demonstrates that softmax outputs are systematically miscalibrated (overconfident), establishing the problem that Sensoy's EDL addresses structurally by replacing softmax with Dirichlet outputs. Guo's temperature scaling is a post-hoc fix; EDL is an architectural fix. For propstore, this means: if using standard classifiers, apply Guo's calibration; if redesigning, consider EDL's Dirichlet approach.
- [[Josang_2001_LogicUncertainProbabilities]] — **Strong.** Josang 2001 defines the opinion algebra (b, d, u, a) and proves the bijection between opinions and Beta distributions that Sensoy's EDL exploits via the Dirichlet generalization. Sensoy's evidence parameters alpha_k correspond to Josang's (r, s) evidence counts. Josang provides the consensus and discounting operators that EDL does not address — combining opinions from multiple EDL models or propagating trust through recommendation chains.
- [[Josang_2010_CumulativeAveragingFusionBeliefs]] — **Strong.** Formally defines the multinomial opinion representation that EDL's Dirichlet-to-opinion bridge implicitly uses. EDL outputs K evidence values mapped to Dirichlet parameters; this paper defines the corresponding multinomial opinion triple (b_vec, u, a_vec) with the constraint u + sum(b) = 1. The multiplication operator defined here enables combining EDL outputs from sensors/models observing orthogonal aspects of the same entity.
