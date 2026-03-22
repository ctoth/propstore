---
tags: [smt-solving, optimization, maxsat, z3]
---
This paper presents νZ, an optimization module for the Z3 SMT solver that supports weighted MaxSMT, linear arithmetic optimization via dual Simplex and Farkas lemma-based bisection, and multiple objective combination through lexicographic, Pareto front, and box-maximal strategies.
The key contributions include two MaxSAT algorithms (WMax and MaxRes), non-standard arithmetic for detecting unbounded objectives, and algorithms for multi-objective optimization.
The optimization techniques could potentially apply to computing preferred solutions in weighted constraint-based reasoning systems, though the paper does not directly address argumentation.
