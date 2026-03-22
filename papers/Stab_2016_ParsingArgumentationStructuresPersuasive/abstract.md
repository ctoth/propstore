# Abstract

## Original Text (Verbatim)

In this article, we present a novel approach for parsing argumentation structures. We identify argument components using sequence labeling at the token level and apply a new joint model for detecting argumentation structures. The proposed model globally optimizes argument component types and argumentative relations using integer linear programming. We show that our model considerably improves the performance of base classifiers and significantly outperforms challenging heuristic baselines. Moreover, we introduce a novel corpus of persuasive essays annotated with argumentation structures. We show that our annotation scheme and annotation guidelines successfully guide human annotators to substantial agreement. This corpus and the annotation guidelines are freely available for ensuring reproducibility and to encourage future research in computational argumentation.

---

## Our Interpretation

The paper addresses the problem of automatically extracting complete argumentation structures from persuasive essays, including identifying argument components (major claims, claims, premises) and their relations (support, attack). The key contribution is an ILP joint model that enforces global structural constraints (tree structure, one outgoing relation per premise) to improve over pipeline approaches. The annotated corpus of 402 essays and the empirical demonstration that structural and discourse features are most effective for argumentation parsing provide practical grounding for claim extraction systems.
