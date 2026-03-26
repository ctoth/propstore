# Abstract

## Original Text (Verbatim)

Approaches to decision-making under uncertainty in the belief function framework are reviewed. Most methods are shown to blend criteria for decision under ignorance with the maximum expected utility principle of Bayesian decision theory. A distinction is made between methods that construct a complete preference relation among acts, and those that allow incomparability of some acts due to lack of information. Methods developed in the imprecise probability framework are applicable in the Dempster-Shafer context and are also reviewed. Shafer's constructive decision theory, which substitutes the notion of goal for that of utility, is described and contrasted with other approaches. The paper ends by pointing out the need to carry out deeper investigation of fundamental issues related to decision-making with belief functions and to assess the descriptive, normative and prescriptive values of the different approaches.

---

## Our Interpretation

The paper provides a complete taxonomy of how to make decisions when uncertainty is represented by Dempster-Shafer belief functions (mass functions on power sets) rather than single probability distributions. The central finding is that all approaches blend classical decision-under-ignorance criteria with expected utility, differing mainly in whether they force a total ordering of acts or permit incomparability. This is directly relevant to propstore's render layer, which must select among competing claims with imprecise evidence — the paper maps out exactly which decision rule to use depending on whether you want point estimates (pignistic), uncertainty bounds (lower/upper EU), parameterized risk attitude (Hurwicz/OWA), or honest incomparability (E-admissibility).
