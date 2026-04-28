# Abstract

## Original Text (Verbatim)

We generalize the Bayes' theorem within the transferable belief model framework. The generalized Bayesian theorem (GBT) allows us to compute the belief over a space Theta given an observation x subset X when one knows only the beliefs over X for every theta_i in Theta. We also discuss the disjunctive rule of combination (DRC) for distinct pieces of evidence. This rule allows us to compute the belief over X from the beliefs induced by two distinct pieces of evidence when one knows only that one of the pieces of evidence holds. The properties of the DRC and GBT and their uses for belief propagation in directed belief networks are analyzed. The use of the discounting factors is justified. The application of these rules is illustrated by an example of medical diagnosis.

KEYWORDS: belief functions, Bayes' theorem, disjunctive rule of combination.

---

## Our Interpretation

Smets gives the Transferable Belief Model two new primitives — DRC (combine evidence under disjunction) and GBT (invert conditional belief functions to get parent-frame belief from child-frame observation) — and shows they form a closed pair: pl_X(x|theta) = pl_Theta(theta|x). The pair lets directed belief networks propagate forward and backward symmetrically with conditional belief functions, generalizes Bayes' theorem (recovers it exactly when conditionals and prior are probabilities), and absorbs Shafer's ad hoc discounting as a special case of GBT applied to a meta-frame. This is the formal substrate for honest "I don't know" priors in propstore's subjective-logic / argumentation layer.
