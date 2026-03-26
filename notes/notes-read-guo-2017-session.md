# Reading Session: Guo et al. 2017 — On Calibration of Modern Neural Networks

## GOAL
Read all 14 pages, create notes/abstract/citations/description per paper-reader skill.

## DONE
- Confirmed paper dir exists at papers/Guo_2017_CalibrationModernNeuralNetworks/
- Converted 14 pages to PNGs
- Read pages 0-6 (7 of 14)

## KEY FINDINGS SO FAR (pages 0-6)

### Core Problem (p.0-1)
- Modern neural networks are poorly calibrated — confidence does not match accuracy
- Older networks (e.g., LeNet 5-layer) were well-calibrated; modern deep nets (ResNet 110-layer) are NOT
- Miscalibration has increased with depth, width, batch normalization, weight decay changes

### Definitions (p.1-2)
- Perfect calibration: P(Y=y | p_hat = p) = p for all p in [0,1]
- ECE (Expected Calibration Error): bin predictions into M groups, weighted avg of |acc(B_m) - conf(B_m)|
- MCE (Maximum Calibration Error): max over bins of |acc - conf|
- NLL is minimized iff model recovers true conditional distribution
- Reliability diagrams: bar chart of accuracy vs confidence per bin

### Causes of Miscalibration (p.2-3)
- Model capacity: increased depth and width increase miscalibration
- Batch normalization: improves accuracy but hurts calibration
- Weight decay: less weight decay (modern practice) hurts calibration
- NLL can be used to calibrate but overfits — training NLL decreases while test NLL increases (overfitting to confidence)

### Calibration Methods (p.4-5)
1. **Histogram binning** (Zadrozny & Elkan 2001): assign predictions to bins, calibrate per bin
2. **Isotonic regression** (Zadrozny & Elkan 2002): piecewise constant function, most common non-parametric method
3. **Bayesian Binning into Quantiles (BBQ)** (Naeini et al. 2015): Bayesian extension of histogram binning
4. **Platt scaling** (Platt 1999): logistic regression on logits — learns scalar a,b: q = sigma(az+b)
5. **Temperature scaling**: SINGLE parameter T dividing logits: q = max_k sigma(z/T). Simplest and most effective.
6. **Matrix scaling**: W matrix and bias on logits (full or class-wise)
7. **Vector scaling**: diagonal W (per-class) + bias on logits

### Temperature Scaling Details (p.5)
- Single scalar T > 0 for all classes
- For logit vector z, new confidence: q = max_k sigma_SM(z/T)_k
- T is optimized w.r.t. NLL on validation set
- Does NOT change the maximum of softmax (preserves accuracy)
- Only changes the softmax entropy — "softens" the distribution
- T called "temperature" and a "softened" softmax raises entropy

### Experiments (p.6)
- Image classification: CIFAR-10/100 with various ResNets, Wide ResNets, DenseNets, LeNet
- Document classification: 20 Newsgroups, Reuters
- NLP datasets: SST, various text classification
- Compared all calibration methods

## NEXT
- Read pages 7-13 (results tables, more experiments, supplementary)
- Write notes.md, abstract.md, citations.md, description.md
