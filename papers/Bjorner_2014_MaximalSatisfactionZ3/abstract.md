# Abstract

## Original Text (Verbatim)

Satisfiability Modulo Theories, SMT, solvers are used in many applications. These applications benefit from the power of sound and scalable theorem proving technologies for expressive logics and quantified theory solvers. SMT solvers are primarily used to determine whether formulas are satisfiable. Furthermore, when formulas are satisfiable, many applications need suitable models that assign values to free variables. Yet, in many cases applications are interested in finding models that are not only satisfying, but also optimal with respect to objective functions. In fact, uses of Z3, an SMT solver from Microsoft Research, both include uses in combination with external objective function minimizers with ν (or νZ, or one νZ), an extension within Z3 that uses formulas objective functions directly with Z3. Under the hood there is a portfolio of approaches for solving linear optimization problems over SMT formulas, MaxSMT, and their combinations. Objective functions are combined as either Pareto fronts, lexicographically, or each objective is optimized independently.

---

## Our Interpretation

νZ extends the Z3 SMT solver with optimization capabilities, enabling not just satisfiability checking but finding optimal satisfying assignments with respect to objective functions. The paper presents algorithms for weighted MaxSMT (WMax and MaxRes), linear arithmetic optimization via Simplex and Farkas lemma bisection, and multi-objective combination strategies. This is relevant as infrastructure for computing optimal solutions in formal reasoning systems that can be expressed as constrained optimization problems.
