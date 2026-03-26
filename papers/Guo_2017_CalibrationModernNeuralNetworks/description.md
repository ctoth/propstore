---
tags: [calibration, neural-networks, uncertainty, temperature-scaling]
---
Demonstrates that modern deep neural networks are poorly calibrated — their softmax confidence scores are systematically overconfident — and identifies depth, width, and batch normalization as key factors. Evaluates post-hoc calibration methods and finds that temperature scaling (a single learned parameter dividing logits before softmax) is the simplest and most effective approach, reducing Expected Calibration Error from 3-15% to under 2% across architectures. Directly relevant to propstore's treatment of model output scores: establishes that raw neural network outputs are not calibrated probabilities and should not be treated as such without post-hoc correction.
