---
tags: [nonmonotonic-reasoning, description-logics, rational-closure, defeasible-reasoning, alc]
---
Reformulates Lehmann–Magidor rational closure as a default-assumption construction over a propositional or ALC knowledge base, requiring only classical entailment tests and producing a linearly ordered default sequence ⟨δ_0,…,δ_n⟩ such that any defeasible query reduces to a single ⊨ check.
Shows the construction produces a rational consequence relation, gives an EXPTIME-complete decision procedure for C |~ D in ALC and a PSPACE-complete one for K ⊩_s a:C with unfoldable TBoxes, and inherits the underlying DL's complexity (so polynomial for EL).
Provides propstore's argumentation/defeasibility layer with a directly implementable rational-closure recipe that fits the "lazy until rendering" principle — once ⟨T̃, Δ̃⟩ is computed, render-time queries are single classical entailment tests.
