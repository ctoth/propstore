---
tags: [nonmonotonic-reasoning, preferential-models, defeasibility, argumentation, conditional-logic]
---
KLM characterize five families of nonmonotonic consequence relations on conditional assertions α |~ β ("if α, normally β") via Gentzen-style inference rules and prove representation theorems linking each system (C, CL, P, CM, M) to a corresponding family of cumulative or preferential models.
The central system P (preferential reasoning) is axiomatized by Reflexivity, Left Logical Equivalence, Right Weakening, Cut, Cautious Monotonicity, and Or; it correctly handles the Nixon diamond and penguin triangle without "multiple extension" pathologies and is strictly more expressive than circumscription, default logic, or autoepistemic logic.
This paper is the formal foundation for propstore's defeasibility and belief-set layers: it tells us which inference rules a non-monotonic stance algebra may safely use, and supplies the model-theoretic semantics (smoothness, minimal states under a preference relation) that grounds render-time honest ignorance over fabricated confidence.
