---
tags: [uncertainty-quantification, dirichlet, subjective-logic, evidential-reasoning, deep-learning]
---
Proposes replacing softmax outputs in neural classifiers with Dirichlet distribution parameters, enabling single-forward-pass uncertainty quantification by treating predictions as subjective opinions grounded in Dempster-Shafer Theory of Evidence.
The network learns to output per-class evidence that parameterizes a Dirichlet, yielding both expected class probabilities and an explicit uncertainty mass that distinguishes epistemic ignorance from aleatoric ambiguity.
Directly relevant to propstore's need for principled uncertainty representations beyond bare-float probabilities, with natural connections to subjective logic opinions and evidence accumulation without premature commitment.
