# Abstract

## Original Text (Verbatim)

We propose a distance measure between two probability distributions, which allows one to bound the amount of belief change that occurs when moving from one distribution to another. We contrast the proposed measure with some well known measures, including KL-divergence, showing some theoretical properties on its ability to bound belief changes. We then present two practical applications of the proposed distance measure: sensitivity analysis in belief networks and probabilistic belief revision. We show how the distance measure can be easily computed in these applications, and then use it to bound global belief changes that result from either the perturbation of local conditional beliefs or the accommodation of soft evidence. Finally, we show that two well known techniques in sensitivity analysis and belief revision correspond to the minimization of our proposed distance measure and, hence, can be shown to be optimal from that viewpoint.

---

## Our Interpretation

The paper addresses the problem of quantifying how much downstream beliefs can change when a probability distribution is locally perturbed. The key finding is the CD-distance metric, which provides tight worst-case bounds on odds ratio changes and is efficiently computable for Bayesian network parameter perturbations. This is relevant to propstore because it provides formal guarantees on output stability when probabilistic argumentation parameters are adjusted.
