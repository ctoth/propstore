---
tags: [belief-functions, dempster-shafer, transferable-belief-model, bayesian-inference, belief-networks]
---
Smets introduces the Disjunctive Rule of Combination (DRC) and Generalized Bayesian Theorem (GBT) within the Transferable Belief Model, providing closed-form forward and backward propagation of belief functions over directed networks built from conditional belief functions bel_X(.|theta_i).
The paper shows GBT generalizes Bayes' theorem (recovers it exactly when conditionals and prior are probabilities), justifies Shafer's discounting as GBT applied to a meta-frame, and demonstrates exponential storage savings (|Theta|*2^|X| versus 2^{|X|*|Theta|}) over Shafer-Shenoy-Mellouli; Pearl's compatibility counterexamples to DS theory dissolve once GBT replaces naive Dempster combination.
This is the canonical formal substrate for honest "I don't know" priors, vacuous opinions, and conditional belief inversion in propstore's subjective-logic and probabilistic argumentation layers, and operationalizes the open-world m(empty)>=0 stance the project relies on.
