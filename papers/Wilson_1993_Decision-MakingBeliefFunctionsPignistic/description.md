---
tags: [belief-functions, dempster-shafer, decision-theory, imprecise-probability, pignistic]
---
Wilson formally compares two decision procedures over Dempster-Shafer belief functions: the standard upper/lower-probability envelope ([Bel, Pl]) approach versus Smets' pignistic-probability approach.
He proves that taking the set of pignistic transforms over all refinements of the frame of discernment yields the same lower and upper expected utilities — and therefore the same decisions — as the envelope approach, with closed-form E_*[U]=Σm(B)min_{y∈B}U(y) computable by Monte-Carlo over m.
Provides direct theoretical grounding for propstore's non-commitment discipline: belief should remain an imprecise-probability interval at storage time, and any single-probability projection (pignistic, expected, etc.) is a render-time policy choice that does not change decisions when frame refinements are allowed.
