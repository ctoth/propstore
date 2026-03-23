---
title: "νZ - Maximal Satisfaction with Z3"
authors: "Nikolaj Bjørner, Anh-Dung Phan"
year: 2014
venue: "SCSS 2014 (Symbolic Computation in Software Science)"
doi_url: "https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/nbjorner-scss2014.pdf"
---

# νZ - Maximal Satisfaction with Z3

## One-Sentence Summary
This paper describes νZ, an optimization module for the Z3 SMT solver that supports weighted MaxSMT, linear arithmetic optimization, and multiple objective combination strategies (lexicographic, Pareto, box).

## Problem Addressed
SMT solvers are used in program analysis, verification, testing, and synthesis, but knowing whether a formula is satisfiable is not always sufficient. Applications need to find maximal or optimal satisfying assignments — e.g., soft constraints with weights, objective functions over numeric variables, or combinations thereof. *(p.1)*

## Key Contributions
- Integration of MaxSMT solving capabilities into Z3, combining a MaxSAT solver module with an OptiMathSAT module that optimizes linear arithmetic objectives *(p.2)*
- Two MaxSAT algorithms: WMax (iterative soft constraint approach) and MaxRes (Maximal Resolution based approach) *(p.2-4)*
- Optimization for linear arithmetic using dual Simplex and non-standard arithmetic for unbounded objectives *(p.5-6)*
- Three methods for combining multiple objectives: lexicographic, Pareto fronts, and independent box objectives *(p.7-8)*
- Core-based approach to linear arithmetic optimization using Farkas lemmas for bisection search *(p.6-7)*

## Methodology
νZ composes two main components: (1) a MaxSMT (MaxSAT solver) module that solves soft constraints, and (2) an OptiMathSAT module that optimizes linear arithmetic objective functions. These are combined by an engine layer that translates optimization objectives into suitable combinations of these sub-engines. *(p.2)*

## Key Equations

### Weighted MaxSMT Problem
Given a set of numeric weights $w_1, \ldots, w_n$ and formulas $F_1, \ldots, F_n$, find subset $U \subseteq \{1, \ldots, n\}$ such that:
1. $F_1 \land F_2 \land \cdots \land F_n$ is satisfiable
2. The sum $\sum_{i \in U} w_i$ is minimized (dually, cost/penalty for excluding $F_i$)
*(p.2)*

### WMax Core Update Rule
$$
F' \leftarrow F \setminus (s_1 \vee \cdots \vee s_k)
$$
$$
F' \leftarrow F' \cup \{s_1 \vee d, s_2 \vee \neg d\}
$$
Where: $s_1, \ldots, s_k$ are soft clauses from an unsatisfiable core, $d$ is a fresh propositional variable. Weights are split and reassigned to maintain the weighted sum invariant. *(p.3)*

### MaxRes Clause Production
Given a core $F_1, \ldots, F_k$ with weights $w_1, \ldots, w_k$, let $w = \min(w_1, \ldots, w_k)$. Create new soft constraints:
$$
F_1 \vee w_1, \ldots, F_k \vee w_1, F_1 \vee w_1 \leftarrow w_k, w_1 \leftarrow w_k
$$
And remove constraints with weight 0 (i.e., at least one is satisfied). *(p.3-4)*

### MaxRes Termination (Claim 1)
If $F_1, \ldots, F_n$ has a maximal satisfying assignment of weight $w$ and only if $F' \cdot F'_1, \ldots, F'_m$ has a maximal satisfying assignment of weight $w + c$. *(p.4)*

### Farkas Lemma Application for Tightening Bounds
Given T-lemmas $(A_i x \leq b_i \rightarrow t \leq \text{mid})$ for $i \in \mathcal{I}$:
$$
F \rightarrow \bigvee_i A_i x \leq b_i
$$
Let $r_i$ be Farkas coefficients such that $r_i A_i > r_i b_i$, $r_i A_i = t$:
$$
\text{hi} \leftarrow \max\{r_i b_i \mid i \in \mathcal{I}\}
$$
*(p.7)*

### Lexicographic Combination
For objectives $t_1, t_2$ subject to constraint $F$, find model $M$ such that $\langle M(t_1), M(t_2) \rangle$ is lexicographically maximal — no model $M'$ of $F$ has $M'(t_1) > M(t_1)$ or $M'(t_1) = M(t_1), M'(t_2) > M(t_2)$. *(p.7)*

### Pareto Front Constraint Update
$$
G \leftarrow G \wedge t_1 \geq v_1 \wedge t_2 \geq v_2 \wedge (t_1 > v_1 \vee t_2 > v_2)
$$
Where $v_1 = M(t_1)$, $v_2 = M(t_2)$ from the current satisfying model. *(p.8)*

### Box-Maximal Front Update
$$
F \leftarrow F \wedge (t_1 > v_1 \vee t_2 > v_2) \wedge \neg \bigwedge L
$$
Where $L$ is the set of literals from the current model, preventing revisiting the same solution region. *(p.8)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Soft constraint weight | $w_i$ | - | 1 | $> 0$ | 2 | Weight for each soft constraint in MaxSMT |
| Objective value | $t$ | - | - | $(-\infty, \infty)$ | 5 | Linear arithmetic term to maximize |
| Lower bound | lo | - | $-\infty$ | - | 5 | Current lower bound on objective |
| Upper bound | hi | - | $\infty$ | - | 5 | Current upper bound on objective |
| Bisection midpoint | mid | - | - | (lo, hi) | 7 | Midpoint for bisection search |
| min_cost | - | - | 0 | $\geq 0$ | 3 | Running cost of excluded soft constraints |
| Farkas coefficients | $r_i$ | - | - | - | 7 | Coefficients for T-lemma tightening |

## Implementation Details
- νZ is implemented as a satellite theory solver in Z3's SMT core, inter-operating with other theories via lazy arithmetic, bit-vectors, arrays, and algebraic data types *(p.3)*
- WMax maintains a cost variable `min_cost` initialized to 0, and a `max_cost` that is set to `∞`; the process blocks unsatisfiable cores and adds correcting constraints *(p.3)*
- The approach is implemented on a modified DPLL engine which maintains a satisfying trail and uses the dual Simplex method *(p.5)*
- For unbounded objectives, non-standard arithmetic is used: variables can take value $\epsilon$ (infinitesimal) to detect unboundedness *(p.6)*
- MaxRes creates sub-formulas in a number bounded by the number of different soft clauses; the process terminates because each core extraction reduces the remaining clauses *(p.4)*
- SMT-LIB syntax extensions: `(maximize t)`, `(minimize t)`, `(assert-soft F :weight w)`, `(assert-soft F [:id] [:weight w])` *(p.2)*
- νZ is available via Z3 as a tool and as a service (http://rise4fun.com/z3opt/tutorial) *(p.1)*
- Farkas coefficients in bisection search provide tighter bounds than binary search alone by extracting linear combination information from infeasibility proofs *(p.6-7)*

## Figures of Interest
- **Algorithm 1 (p.5):** Sequential search — iteratively finds satisfying assignments and tightens the bound on the objective
- **Algorithm 2 (p.6):** Finding unbounded objectives using non-standard arithmetic — extends standard Simplex with epsilon values
- **Algorithm 3 (p.7):** Bisection Search with Farkas Lemmas — combines bisection with T-lemma analysis for tighter bounds
- **Algorithm 4 (p.8):** Guided Improvement Algorithm for finding Pareto fronts — iteratively discovers non-dominated solutions
- **Algorithm 5 (p.8):** Finding independent upper bounds (box-maximal front) — maximizes each objective independently

## Results Summary
- νZ solves MaxSAT competition benchmarks and integrates with Z3's existing theory solvers *(p.1)*
- MaxRes shows significantly better performance than WMax on many larger instances *(p.4)*
- The Farkas-based bisection approach provides tighter upper bounds than simple binary search *(p.6-7)*
- Core-based approach for linear arithmetic can sometimes find optimal values faster than Simplex for problems with many clauses *(p.6)*
- The experience with core-based linear optimization is "so far not been as good as the more straightforward approach" from Algorithms 1-2, as Z3 spends time refining infeasible bounds *(p.6)*

## Limitations
- Core-based optimization for linear arithmetic (Algorithm 3) does not always outperform sequential search (Algorithms 1-2) *(p.6)*
- νZ was at the time of writing still in active development *(p.7)*
- The paper focuses on linear arithmetic; extension to non-linear objectives is not covered *(p.7)*
- A tool demonstration presentation is deferred to another paper *(p.1)*

## Arguments Against Prior Work
- Standard SMT solvers only determine satisfiability, not optimality — insufficient for applications needing maximal/optimal solutions *(p.1)*
- Simple binary search for optimization bounds is suboptimal; Farkas lemma-based approaches can extract tighter bounds from infeasibility proofs *(p.6-7)*
- WMax (the traditional iterative MaxSAT approach) performs worse than MaxRes on larger instances *(p.4)*

## Design Rationale
- The two-component architecture (MaxSMT + OptiMathSAT) allows independent optimization of propositional soft constraints and linear arithmetic objectives *(p.2)*
- MaxRes is preferred over WMax because it creates a bounded number of sub-formulas while WMax can create many auxiliary variables *(p.4)*
- Non-standard arithmetic with epsilon values enables detection of unbounded objectives without special-casing *(p.6)*
- Lexicographic combination is chosen as the default for multiple objectives because it produces a single deterministic answer *(p.7)*

## Testable Properties
- For any weighted MaxSMT instance, the sum of weights of unsatisfied soft constraints in νZ's solution equals the minimum possible *(p.2)*
- WMax terminates: each iteration either finds a satisfying assignment (reducing `max_cost`) or extracts a core (increasing `min_cost`) *(p.3)*
- MaxRes terminates: each core extraction reduces the number of remaining soft clauses, and the number of generated sub-formulas is bounded *(p.4)*
- Algorithm 1 (sequential search) terminates: each iteration strictly reduces the gap between current value and optimal *(p.5)*
- If Algorithm 2 returns $\infty$, the objective is truly unbounded in the feasible region *(p.6)*
- Pareto front solutions are non-dominated: for each yielded $(v_1, v_2)$, no feasible solution has both $t_1 \geq v_1$ and $t_2 \geq v_2$ with at least one strict inequality *(p.7-8)*
- Box-maximal values are independent upper bounds: each $v_i$ is the maximum achievable for $t_i$ regardless of the other objective *(p.8)*

## Relevance to Project
This paper describes optimization extensions to SMT solving, which is tangentially related to the project's focus on argumentation frameworks. The optimization techniques (MaxSMT, Pareto fronts) could potentially be used to compute preferred extensions or optimal argument labellings in weighted argumentation frameworks, but the paper does not directly address argumentation.

## Open Questions
- [ ] How does νZ performance compare to dedicated MaxSAT solvers on standard benchmarks?
- [ ] Can the Pareto front algorithm scale to problems with many objectives (>2)?
- [ ] What is the relationship between MaxSMT soft constraints and argumentation framework preferences?

## Related Work Worth Reading
- [4] Cimatti et al. - OptiMathSAT: mathematical optimization in SMT (TACAS 2015) *(p.9)*
- [7] Heras, Larrosa, Oliveras - MiniMaxSAT: a new weighted MaxSAT solver *(p.9)*
- [14] Nieuwenhuis, Oliveras - On SAT Modulo Theories and Optimization Problems (SAT 2006) *(p.9)*
- [8] Leonardo de Moura and Nikolaj Bjørner - Z3: An Efficient SMT Solver (TACAS 2008) *(p.9)*

## Collection Cross-References

### Already in Collection
- (none — no cited papers are in the collection)

### New Leads (Not Yet in Collection)
- (none remaining)

### Now in Collection (previously listed as leads)
- [[Sebastiani_2015_OptiMathSATToolOptimizationModulo]] — Competing OMT tool extending MathSAT5. Encodes MaxSMT as Pseudo-Boolean optimization over linear arithmetic (unlike νZ's specialized MaxSAT module). Supports lexicographic, Pareto, and minmax multi-objective optimization.
- [[Moura_2008_Z3EfficientSMTSolver]] — The foundational Z3 SMT solver that νZ extends. Describes the DPLL-based SAT solver + congruence closure core + satellite theory solvers architecture.

### Now in Collection (previously listed as leads)
- [[Sebastiani_2015_OptiMathSATToolOptimizationModulo]] — Competing OMT tool extending MathSAT5. Encodes MaxSMT as Pseudo-Boolean optimization over linear arithmetic (unlike νZ's specialized MaxSAT module). Supports lexicographic, Pareto, and minmax multi-objective optimization. νZ's notes describe it as having an "OptiMathSAT module" — this is actually the standalone tool that νZ's linear arithmetic optimization component was inspired by/compared against.

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)
- [[Mahmood_2025_Structure-AwareEncodingsArgumentationProperties]] — Mahmood provides SAT/QSAT encodings for Dung argumentation semantics and explicitly mentions Z3 as an implementation target; νZ's MaxSMT capabilities could extend these encodings to weighted/preference-based argumentation where soft constraints encode argument preferences
- [[Niskanen_2020_ToksiaEfficientAbstractArgumentation]] — Niskanen's mu-toksia uses SAT solving for argumentation reasoning with iterative solver architecture; νZ's optimization layer could enable extension of this approach to find optimal (e.g., minimum-weight or preferred) extensions rather than just enumerating all extensions
- [[Tang_2025_EncodingArgumentationFrameworksPropositional]] — Tang generalizes AF encodings to multi-valued logics; νZ's support for optimization over SMT formulas provides a computational engine for finding optimal solutions in such enriched encodings
