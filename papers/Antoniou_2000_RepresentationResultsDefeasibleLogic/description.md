---
tags: [defeasible-logic, nonmonotonic-reasoning, proof-theory, representation-results, transformations]
---
Establishes representation theorems for Antoniou-Billington-Governatori-Maher Defeasible Logic, showing that facts, defeaters, and the superiority relation are all eliminable by modular or incremental transformations while preserving the four-tagged conclusion set (+Δ, -Δ, +∂, -∂) on the original language.
The paper classifies per-literal outcomes into six classes A-F and per-pair (p, ¬p) outcomes into 16 acyclic-realizable cases (21 total), proves negative results showing strict and defeasible rules cannot be eliminated, gives explicit transformations `normal`, `elim_sup`, `elim_dft` with linear blow-up factors 3/4/3, and concludes with a simplified proof theory for the post-transformation normal form that underpins the Delores linear-time consequence engine.
Foundational for propstore's defeasibility layer and ASPIC+ bridge: justifies normalizing input theories to strict-plus-defeasible-only form, drops superiority and defeater overhead, and bounds the asymptotic cost of consequence computation to linear in theory size.
