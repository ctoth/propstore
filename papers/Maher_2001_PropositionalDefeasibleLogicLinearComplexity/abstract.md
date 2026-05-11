# Abstract

## Original Text (Verbatim)

Defeasible logic is a rule-based nonmonotonic logic, with both strict and defeasible rules, and a priority relation on rules. We show that inference in the propositional form of the logic can be performed in linear time. This contrasts markedly with most other propositional nonmonotonic logics, in which inference is intractable.

---

## Our Interpretation

Maher addresses the practical-applicability gap in non-monotonic reasoning: most expressive NMR languages (default logic, autoepistemic, circumscription, stable-model and Clark-completion logic programs) have intractable propositional inference, blocking large-rule-set applications. The paper proves that defeasible logic — despite its expressive features (strict + defeasible rules, defeaters, acyclic programmable superiority) — admits a linear-time inference algorithm via a transition system, auxiliary tags `+σ, −σ`, and linear-blowup transformations that reduce arbitrary defeasible theories to basic form. The bound is directly relevant to propstore because propstore commits to defeasible logic as the substrate of its argumentation/reasoning layer; this paper is the complexity ceiling and the reusable proof technique.
