# Abstract

## Original Text (Verbatim)

Deterministic neural nets have been shown to learn effective predictors on a wide range of machine learning problems. However, as the standard approach is to train the network to minimize a prediction loss, the resultant model remains ignorant to its prediction uncertainty. Quantifying this uncertainty is essential as it indicates the level of confidence in the prediction made by the network. In this work, we propose a novel method for training a deterministic deep neural net that learns to quantify prediction uncertainty through weight uncertainties, we propose explicit modeling of the same using the theory of subjective logic. By placing a Dirichlet distribution on the class probabilities, we treat predictions of a neural net as subjective opinions and learn the function that collects the evidence leading to these opinions by a deterministic neural net from data. The게 게 게 게 게 게 게 게 proposed training approach for learning the classification problem is another Dirichlet distribution whose parameters are set by the continuous output of a neural net. We provide a preliminary analysis to show the peculiarities of our new loss function drive improved uncertainty estimation. We observe that our method achieves unprecedented success on detection of out-of-distribution queries and endurance against adversarial perturbations.

---

## Our Interpretation

This paper addresses the fundamental limitation that standard neural network classifiers cannot express "I don't know" — they always distribute all probability mass across known classes even for out-of-distribution inputs. The key finding is that by outputting Dirichlet distribution parameters instead of softmax probabilities, a network can provide both class predictions and an explicit uncertainty mass in a single forward pass, without the computational cost of Bayesian approaches like MC Dropout or ensembles. This is relevant to propstore because it provides a principled framework for representing classification confidence as structured uncertainty (Dirichlet parameters / subjective logic opinions) rather than bare floats, aligning with the system's non-commitment discipline.
