---
tags: [smt-solver, optimization, maxsat, multi-objective]
---
OptiMathSAT extends the MathSAT5 SMT solver with Optimization Modulo Theories (OMT) capabilities, supporting single and multi-objective optimization over linear arithmetic, bit-vectors, and partial weighted MaxSMT. It provides lexicographic, Pareto, and minmax/maxmin multi-objective modes through SMT-LIBv2 syntax extensions and a C API. Relevant as the competing OMT approach to Z3's νZ optimizer, with a different encoding strategy for MaxSMT that may offer advantages for weighted argumentation constraint solving.
