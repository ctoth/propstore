# Abstract

## Original Text (Verbatim)

Confidence calibration — the problem of predicting probability estimates representative of the true correctness likelihood — is important for classification models in many applications. We discover that modern neural networks, unlike those from a decade ago, are poorly calibrated. Through extensive experiments, we observe that depth, width, and Batch Normalization are important factors influencing calibration. We evaluate the performance of various post-processing calibration methods on state-of-the-art architectures with image and document classification datasets. Our analysis and experiments are not only offer insights into neural network learning, but also provide a simple and straightforward recipe for practical settings: on most datasets, temperature scaling — a single-parameter variant of Platt Scaling — is surprisingly effective at calibrating predictions.

---

## Our Interpretation

This paper demonstrates that modern deep neural networks systematically produce overconfident predictions — their softmax outputs are not calibrated probabilities. The core finding is that network depth, width, and batch normalization (features of all modern architectures) directly cause miscalibration. The paper's key practical contribution is temperature scaling: dividing logits by a single learned scalar T before softmax, optimized on a validation set, which is the simplest and most effective post-hoc calibration method tested. This is directly relevant to propstore because it establishes that raw neural network confidence scores (from NLI models, classifiers, etc.) cannot be interpreted as probabilities without calibration — validating the design decision to not collapse bare-float scores into probability semantics at storage time.
