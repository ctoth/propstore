# Abstract

## Original Text (Verbatim)

There has been increasing concern within the machine learning community that we are in a reproducibility crisis. As many have begun to work on this problem, all work so far has been qualitative in nature, e.g., discussing what properties a paper/code should have to be reproducible. Instead, we attempt to quantitatively measure reproducibility by treating it as a survival analysis problem. We note that this perspective opens a number of new avenues to understanding the nature of reproducibility that were previously inaccessible. In this work we use our data to produce a linear model and a non-linear model of reproducibility that allows us to get new insights that were not previously available. The data used in this work comes from our efforts spanning 7 years, in which we attempted to reproduce 255 papers, and they provided features and public data to begin answering questions about the factors of reproducibility in a quantitative manner. Their work, like all efforts of which we are aware, evaluated reproducibility using a binary outcome of reproducible or not reproducible and uses it to perform a survival analysis. In this case, we defined the hazard function h(x), which produces the likelihood of an event (i.e., reproduction) occurring at time t, given features about the paper x. In a survival analysis, we want to model the likely amount of time for an event to occur, and this is common in medicine where we want to understand what factors will prolong a life (i.e., increase survival) and what factors may lead to an early death.

---

## Our Interpretation

This paper addresses the ML reproducibility crisis by treating reproduction as a time-to-event (survival) problem rather than just a binary success/failure classification. Using 255 papers over 7 years, the author builds Cox PH and XGBoost models to identify paper readability, pseudo code, and equation density as the strongest predictors of reproducibility. The quantitative approach and specific feature importance rankings provide actionable guidance for improving research reproducibility and could inform evidence quality assessment in argumentation systems.
