---
tags: [subjective-logic, partial-observations, dirichlet-distributions, trust-estimation, belief-update]
---
Extends Subjective Logic to incorporate belief updates from partially observable evidence via likelihood functions, deriving a Dirichlet moment-matching algorithm (Algorithm 1) with three computation methods and formal bounds on uncertainty change. Demonstrates that sequential single-observation updates achieve near-optimal performance, corrects the monotonic update error from Kaplan et al. 2012, and applies the framework to trust estimation via likelihood ratios comparing reported and observed opinions. Directly relevant to propstore's opinion algebra as the principled method for incorporating noisy evidence (LLM outputs, classifier scores) into SL opinions.
