# Citations

## Reference List

[1] M. Abadi, P. Barham, J. Chen, Z. Chen, A. Davis, J. Dean, M. Devin, S. Ghemawat, G. Irving, M. Isard, et al. Tensorflow: A system for large-scale machine learning. In OSDI, volume 16, pages 265-283, 2016.
[2] C. Blundell, J. Cornebise, K. Kavukcuoglu, and D. Wierstra. Weight uncertainty in neural networks. In ICML, 2015.
[3] Y. Chen, L. Fox, and C. Guestrin. Stochastic gradient Hamiltonian Monte Carlo. In ICML.
[4] D. Ciregan, A. Giusti, L. M. Gambardella, and J. Schmidhuber. Deep neural networks segment neuronal membranes in electron microscopy images. In NIPS, 2012.
[5] D. C. Ciresan, U. Meier, J. Masci, and J. Schmidhuber. Multi-column deep neural network for traffic sign classification. Neural Networks, 32:333-338, 2012.
[6] M. Welling, D. Kingma, T. Salimans. Variational dropout and the local reparameterization trick. In NIPS, 2015.
[7] Y. Gal and Z. Ghahramani. Bayesian convolutional neural networks with Bernoulli approximate variational inference. ICLR Workshop, 2016.
[8] Y. Gal and Z. Ghahramani. Dropout as a Bayesian approximation: Representing model uncertainty in deep learning. In ICML, 2016.
[9] I.J. Goodfellow, J. Shlens, and C. Szegedy. Explaining and harnessing adversarial examples. arXiv preprint arXiv:1412.6572, 2014.
[10] K. He, X. Zhang, S. Ren, and J. Sun. Deep residual learning for image recognition. In CVPR, 2016.
[11] N. Heaphy, F. Huszar, Z. Ghahramani, and J.M. Hernandez-Lobato. Collaborative Gaussian processes for preference learning. In NIPS, 2012.
[12] S. Ioffe and C. Szegedy. Batch normalization: Accelerating deep network training by reducing internal covariate shift. In ICML, 2015.
[13] A. Jøsang. Subjective Logic: A Formalism for Reasoning Under Uncertainty. Springer, 2016.
[14] M. Kandemir. Asymmetric transfer learning with deep Gaussian processes. In ICML, 2015.
[15] A. Kendall and Y. Gal. What uncertainties do we need in Bayesian deep learning for computer vision? In NIPS, 2017.
[16] D.P. Kingma and J. Ba. Adam: A method for stochastic optimization. In ICLR, 2015.
[17] D.P. Kingma, T. Salimans, and M. Welling. Variational dropout and the local reparameterization trick. In NIPS, 2015.
[18] S. Kuo, N. Balakrishnan, and N.L. Johnson. Continuous Multivariate Distributions, volume 1. Wiley, New York, 2000.
[19] A. Krizhevsky, I. Sutskever, and G.E. Hinton. ImageNet classification with deep convolutional neural networks. In NIPS, 2012.
[20] A. Malinin and M. Gales. Predictive uncertainty estimation via prior networks. In NIPS, 2018.
[21] B. Lakshminarayanan, A. Pritzel, and C. Blundell. Simple and scalable predictive uncertainty estimation using deep ensembles. In NIPS, 2017.
[22] Y. LeCun, P. Haffner, L. Bottou, and Y. Bengio. Object recognition with gradient-based learning. In Shape, Contour and Grouping in Computer Vision, 1999.
[23] Y. Li and Y. Gal. Dropout inference in Bayesian neural networks with alpha-divergences. In ICML, 2017.
[24] C. Louizos and M. Welling. Multiplicative normalizing flows for variational bayesian neural networks. In ICML, 2017.
[25] D.J. MacKay. Probable networks and plausible predictions - a review of practical Bayesian methods for supervised neural networks. Network: Computation in Neural Systems, 6(3):469-505, 1995.
[26] D. Molchanov, A. Ashukha, and D. Vetrov. Variational dropout sparsifies deep neural networks. In ICML, 2017.
[27] D. Molchanov, A. Ashukha, and D. Vetrov. Variational dropout sparsifies deep neural networks. In ICML, 2017.
[28] N. Papernot, N. Carlini, I. Goodfellow, R. Feinman, F. Faghri, A. Matyasko, K. Hambardzumyan, Y.-L. Juang, A. Kurakin, R. Sheatsley, et al. Cleverhans v2.0.0: An adversarial machine learning library. arXiv preprint arXiv:1610.00768, 2016.
[29] C.E. Rasmussen and C.I. Williams. Gaussian Processes for Machine Learning. MIT Press, 2006.
[30] N. Srivastava, G. Hinton, A. Krizhevsky, I. Sutskever, and R. Salakhutdinov. Dropout: A simple way to prevent neural networks from overfitting. Journal of Machine Learning Research, 15:1929-1958, 2016.
[31] D. Tran, R. Ranganath, and D. Blei. The variational Gaussian process. In ICLR, 2016.
[32] A.G. Wilson. Deep kernel learning. In AISTATS, 2016.

## Key Citations for Follow-up

- **[13] Jøsang 2016 — Subjective Logic book:** The formal framework for subjective opinions (belief, disbelief, uncertainty, base rate) that underpins the entire evidential approach. Essential for understanding how to integrate Dirichlet-based uncertainty into an argumentation system.
- **[8] Gal and Ghahramani 2016 — Dropout as Bayesian approximation:** The primary baseline and competing approach. Understanding its limitations helps justify when EDL is preferable.
- **[20] Malinin and Gales 2018 — Prior Networks:** Concurrent work also using Dirichlet outputs but with a different training objective (reverse KL to a target Dirichlet). Important to compare approaches.
- **[21] Lakshminarayanan et al. 2017 — Deep Ensembles:** Another major uncertainty quantification baseline that achieves strong results but at high computational cost.
- **[15] Kendall and Gal 2017 — What uncertainties do we need:** Distinguishes aleatoric vs epistemic uncertainty in Bayesian deep learning; provides the conceptual framework for uncertainty types.
