# Abstract

## Original Text (Verbatim)

Smets, P. and R. Kennes, The transferable belief model, Artificial Intelligence 66 (1994) 191-234.

We describe the transferable belief model, a model for representing quantified beliefs based on *belief functions*. Beliefs can be held at two levels: (1) a credal level where beliefs are entertained and quantified by belief functions, (2) a pignistic level where beliefs can be used to make decisions and are quantified by probability functions. The relation between the belief function and the probability function when decisions must be made is derived and justified. Four paradigms are analyzed in order to compare Bayesian, upper and lower probability, and the transferable belief approaches.

*Keywords.* Belief function; Dempster–Shafer theory; quantified beliefs.

---

## Our Interpretation

The TBM separates *what an agent believes* (credal level, quantified by a belief function over a Boolean algebra of propositions, updated by Dempster's rule of conditioning) from *what an agent bets* (pignistic level, a probability `BetP` derived from `m` only when a forced decision requires it). The pignistic transformation `BetP(x;m) = Σ_{x⊆A} m(A)/|A|` is uniquely fixed by four axioms (linearity in mass, continuity, anonymity, impossible-atom irrelevance) and is the only mapping that makes "average beliefs then betP" agree with "betP then average". Four paradigms — Mr. Jones, guards-and-posts, translators, unreliable sensor — show that TBM gives empirically different answers than Bayesian, upper/lower probability, likelihood, and fiducial models, and that Dutch books cannot be raised against TBM users because betting forces them to fix a betting frame and apply the pignistic transformation. The paper is the canonical reference for "honest ignorance" — vacuous belief — and for the discipline of not fabricating probabilities the evidence does not justify.
