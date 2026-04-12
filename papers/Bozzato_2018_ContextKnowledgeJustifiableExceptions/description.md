---
tags: [defeasible-reasoning, contextualized-knowledge, description-logics, datalog, non-monotonic-reasoning]
---
Presents Contextualized Knowledge Repositories (CKRs) with defeasible axioms, enabling local contexts to override inherited global knowledge through justified exceptions backed by clashing assumption sets.
Provides a complete datalog translation for reasoning over CKRs with defeasible axioms under SROIQ-RL, with model checking in P and entailment in coNP, plus a CKRev prototype with scalability experiments.
Directly relevant to propstore's context layer and argumentation layer: the CKR coverage relation formalizes context inheritance, clashing assumptions provide evidence-based exception handling aligned with propstore's non-commitment discipline, and the datalog translation is implementable atop existing infrastructure.
