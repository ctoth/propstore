# Abstract

## Original Text (Verbatim)

Satisfiability Modulo Theories (SMT) problem is a decision problem for logical first-order formulas with respect to combinations of background theories such as: arithmetic, bit-vectors, arrays, and uninterpreted functions. Z3 is a new and efficient SMT Solver freely available from Microsoft Research. It is used in various software verification and analysis applications.

---

## Our Interpretation

Z3 is a foundational SMT solver that combines a modern SAT solver with specialized theory solvers for arithmetic, bit-vectors, arrays, and tuples, using E-matching for quantifier handling. It provides the base solver that νZ extends with optimization, and is the engine underlying propstore's Z3 backend for argumentation constraint solving.
