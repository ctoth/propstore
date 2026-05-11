# Abstract

## Original Text (Verbatim)

Recently there has been increased interest in logic programming-based default reasoning approaches which are not using negation-as-failure in their object language. Instead, default reasoning is modelled by rules and a priority relation among them. In this paper we compare the expressive power of two approaches in this family of logics: Defeasible Logic, and sceptical Logic Programming without Negation as Failure (LPwNF). Our results show that the former has a strictly stronger expressive power. The difference is caused by the latter logic's failure to capture the idea of teams of rules supporting a specific conclusion. © 2000 Published by Elsevier Science Inc. All rights reserved.

*Keywords:* Defeasible logic; Logic programming

---

## Our Interpretation

Antoniou, Maher, and Billington formally compare two logic-programming-style nonmonotonic frameworks that both use rule priorities (instead of negation-as-failure) and shows Defeasible Logic strictly subsumes sceptical LPwNF. The driving distinction is that DL aggregates *teams* of rules with the same head when assessing whether a conclusion is supported, whereas LPwNF treats each rule individually and cannot transitively chain counter-attacks. This is the canonical reference for the four-tag `±Δ / ±∂` proof system reused throughout subsequent defeasible-logic literature, and it grounds propstore's `propstore.defeasibility` design: the team-trumping clause is exactly the formal pattern needed to decide `ist(c, p)` applicability without descending into the LPwNF-style infinite-regress trap.
