---
tags: [dempster-shafer, decision-theory, belief-functions, imprecise-probabilities, uncertainty-reasoning]
---
Reviews the full landscape of decision criteria available when uncertainty is represented by Dempster-Shafer belief functions, organizing them into three families: extensions of classical criteria (Hurwicz, pignistic, OWA, minimax regret), imprecise-probability methods (maximality, E-admissibility), and Shafer's constructive approach based on goals.
All criteria reduce to Maximum Expected Utility when the belief function is Bayesian; the key distinctions are complete vs. partial preference orderings and the role of a pessimism/ambiguity parameter.
Directly relevant to propstore's render-time decision problem: pignistic transformation provides principled point estimates, belief/plausibility intervals provide uncertainty bounds, and E-admissibility (computable via LP) yields choice sets that implement the non-commitment discipline.
