# Abstract

## Original Text (Verbatim)

Argumentation is a widely applied framework for modeling and evaluating arguments and its reasoning with various applications. Popular frameworks are abstract argumentation (Dung's framework) or logic-based argumentation (Besnard-Hunter's framework). Their computational complexity has been studied quite in-depth. Incorporating treewidth into the complexity analysis is particularly interesting, as solvers oftentimes employ SAT-based solvers, which can solve instances of low treewidth fast. In this paper, we address whether one can design reductions from argumentation problems to SAT-problems while linearly preserving the treewidth, which results in decomposition-guided (DG) reductions. It turns out that the linear treewidth overhead caused by our DG reductions, cannot be significantly improved under reasonable assumptions. Finally, we consider logic-based argumentation and establish new upper bounds using DG reductions and lower bounds.

---

## Our Interpretation

The paper tackles the question of whether argumentation problems can be efficiently reduced to SAT/QBF without destroying the treewidth structure that makes instances tractable. The key finding is that decomposition-guided reductions achieve O(k) treewidth overhead for all standard semantics, and this is provably optimal under ETH. This is relevant because it provides the theoretical justification for why SAT-based argumentation solvers can efficiently handle instances with low treewidth, and extends the analysis to logic-based argumentation where no treewidth-parameterized results existed before.
