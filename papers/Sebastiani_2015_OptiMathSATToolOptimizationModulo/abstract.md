# Abstract

## Original Text (Verbatim)

Many SMT problems of interest may require the capability of finding models that are optimal wrt. some objective function. These problems are grouped under the umbrella term of Optimization Modulo Theories — OMT. In this paper we present OptiMathSAT, an OMT tool extending the MathSAT5 SMT solver. OptiMathSAT allows to solve a list of optimization problems on SMT formulas with linear objective functions — on the Boolean, the rational and the integer domains, and on their combinations thereof, including MaxSMT. Multiple objective functions can be combined together and handled either independently, or lexicographically, or via a min-max/max-min fashion. We present its functionalities and interfaces in extended SMT-LIBv2 input syntax and C API bindings, and it preserves the incremental attitude of its predecessor MathSAT5.

---

## Our Interpretation

OptiMathSAT adds optimization capabilities to MathSAT5, enabling users to find optimal models rather than just satisfying ones. It supports combining multiple objective functions via lexicographic, Pareto, and minmax strategies, and encodes MaxSMT as Pseudo-Boolean optimization over linear arithmetic. Relevant as an alternative to Z3's νZ for optimization in argumentation constraint problems.
