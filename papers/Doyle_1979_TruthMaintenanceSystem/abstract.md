# Abstract

## Original Text (Verbatim)

To choose their actions, reasoning programs must be able to make assumptions and subsequently revise their beliefs when discoveries contradict these assumptions. The Truth Maintenance System (TMS) is a problem solver subsystem for performing these functions by recording and maintaining the reasons for program beliefs. Such recorded reasons are useful in constructing explanations of program actions and in guiding the course of action of a problem solver. This paper describes (1) the representations and structure of the TMS, (2) the mechanisms used to revise the current set of beliefs, (3) how dependency-directed backtracking changes the current set of assumptions, (4) techniques for summarizing explanations of beliefs, (5) how to organize problem solvers into "dialectically arguing" modules, (6) how to revise models of the belief systems of others, and (7) methods for embedding control structures in patterns of assumptions. We stress the need of problem solvers to choose between alternative systems of beliefs, and outline a mechanism by which a problem solver can employ rules guiding choices of what to believe, what to want, and what to do.

---

## Our Interpretation

The paper addresses the fundamental problem that AI reasoning systems need to handle non-monotonic belief revision: making assumptions, discovering contradictions, and revising beliefs accordingly. The key contribution is the TMS itself, a subsystem that records justifications for every belief and incrementally maintains the set of current beliefs as assumptions change, including a dependency-directed backtracking mechanism for resolving contradictions. This is directly foundational for the propstore project because it establishes the core concepts (justifications, support status, dependency tracking, nogoods, assumption retraction) that de Kleer's ATMS later builds upon and that the propstore's world model uses for managing competing claims and hypothetical reasoning.
