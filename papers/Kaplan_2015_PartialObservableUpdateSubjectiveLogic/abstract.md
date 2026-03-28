# Abstract

## Original Text (Verbatim)

Subjective Logic (SL) is a type of probabilistic logic, which is suitable for reasoning about situations with uncertainty and incomplete knowledge. In recent years, SL has drawn a significant amount of attention from the multi-agent systems community as it connects beliefs and uncertainty in propositions to a rigorous statistical characterization via Dirichlet distributions. However, one serious limitation of SL is that the belief updates are done only based on completely observable evidence. This work extends SL to incorporate belief updates from partially observable evidence. Normally, the belief updates in SL presume that the current evidence for a proposition points to only one of its mutually exclusive attribute states. Instead, this work considers that the current attribute state may not be completely observable, and instead, one is only able to obtain a measurement that is statistically related to this state. In other words, the SL belief is updated based upon the likelihood that one of the attributes was observed. The paper then illustrates properties of the partial observable updates as a function of the state likelihood and illustrates the use of these likelihoods for a trust estimation application. Finally, the paper demonstrates the robustness of the approach as well as notable advantages over naive heuristic methods through simulations.

---

## Our Interpretation

Standard SL requires evidence to be fully observable — each observation must reveal exactly which attribute state occurred. This paper removes that restriction by introducing likelihood-based partial observations, where the true state is hidden and only a noisy measurement is available. The key technical contribution is a Dirichlet moment-matching algorithm that computes the updated opinion from prior and likelihood vectors, with formal properties bounding uncertainty change. This is directly relevant to propstore because evidence from LLMs and classifiers is inherently partial — calibrated confidence scores are exactly the likelihood vectors this paper's update rule expects.
