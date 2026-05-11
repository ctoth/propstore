# Abstract

## Original Text (Verbatim)

There are several contexts of non-monotonic reasoning where a priority between rules is established whose purpose is preventing conflicts.

One formalism that has been widely employed for non-monotonic reasoning is the sceptical one known as Defeasible Logic. In Defeasible Logic the tool used for conflict resolution is a preference relation between rules, that establishes the priority among them.

In this paper we investigate how to modify such a preference relation in a defeasible logic theory in order to change the conclusions of the theory itself. We argue that the approach we adopt is applicable to legal reasoning where users, in general, cannot change facts or rules, but can propose their preferences about the relative strength of the rules.

We provide a comprehensive study of the possible combinatorial cases and we identify and analyse the cases where the revision process is successful.

After this analysis, we identify three revision/update operators and study them against the AGM postulates for belief revision operators, to discover that only a part of these postulates are satisfied by the three operators.

**Keywords.** Knowledge representation, non-monotonic reasoning, sceptical logics, belief revision.

---

## Our Interpretation

The paper formalises *preference revision* in Defeasible Logic — modifying the superiority/priority relation between rules (rather than facts or rules themselves) to change a theory's conclusions, motivated by legal reasoning where citizens cannot rewrite the law but can argue about which rule's priority should prevail. It introduces eight new auxiliary proof tags ($\pm\Sigma, \pm\sigma, \pm\omega, \pm\varphi$) that locate where in a derivation a `>` change can flip a conclusion, proves the general decision problem is NP-complete via a 3-SAT reduction, enumerates three canonical cases (contraction-like, revision-like, expansion-like) with per-instance algorithmic recipes, and audits the resulting operators against the AGM postulates — finding that only a subset hold and that both the Levi and Harper identities fail. The paper is directly relevant to propstore because it closes the static-priority limitation acknowledged by Al-Anbaki et al. (2019) and provides a literature-grounded, axiomatically-checked extension to propstore's existing `propstore.belief_set` AGM/iterated-revision lane.
