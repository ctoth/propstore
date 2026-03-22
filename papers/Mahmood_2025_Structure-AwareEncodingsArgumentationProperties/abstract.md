# Abstract

## Original Text (Verbatim)

Structural measures of graphs, such as treewidth, are central tools in computational complexity resulting in efficient algorithms when exploiting the parameter. It is even known that modern SAT solvers work efficiently on instances of small treewidth. Since these solvers are widely applied, research focuses in compactly encoding into (Q)SAT for solving and to understand encoding limitations. Even more general is the graph parameter clique-width, which unlike treewidth can be small for dense graphs. Although algorithms are available for clique-width, little is known about encodings. We initiate the quest to understand encoding capabilities with clique-width by considering abstract argumentation, which is a vibrant framework for reasoning with conflicting arguments. It is based on directed graphs and asks for computationally challenging properties, making it a natural candidate to study computational properties. We design novel reductions from argumentation problems to (Q)SAT. Our reductions linearly preserve the clique-width, resulting in directed decomposition-guided (DDG) reductions. We establish novel results for all argumentation semantics, including counting. Notably, the overhead caused by our DDG reductions cannot be significantly improved under reasonable assumptions.

---

## Our Interpretation

The paper solves the problem of efficiently encoding argumentation framework semantics (stable, admissible, complete, preferred, semi-stable, stage extensions) into SAT/QSAT formulas while preserving the structural complexity measure of clique-width. The key finding is that these encodings achieve tight complexity bounds — they are provably optimal under the Exponential Time Hypothesis. This is relevant to propstore because it provides the theoretical foundation and concrete Boolean formulas for computing all extension-based semantics using SAT/SMT solvers like z3, which propstore already uses for condition analysis.
