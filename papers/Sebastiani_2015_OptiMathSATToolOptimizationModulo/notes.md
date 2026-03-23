---
title: "OptiMathSAT: A Tool for Optimization Modulo Theories"
authors: "Roberto Sebastiani and Patrick Trentin"
year: 2015
venue: "International Conference on Automated Deduction (CADE-25)"
doi_url: "https://doi.org/10.1007/s10817-018-09508-6"
---

# OptiMathSAT: A Tool for Optimization Modulo Theories

## One-Sentence Summary
OptiMathSAT extends the MathSAT5 SMT solver with optimization capabilities over linear arithmetic, bit-vectors, and MaxSMT, supporting single-objective, multi-objective (lexicographic, Pareto, minmax), and combined optimization problems.

## Problem Addressed
Many SMT problems require not just satisfiability checking but finding models that are optimal w.r.t. some objective function. These problems are grouped under Optimization Modulo Theories (OMT). OptiMathSAT provides a unified OMT tool extending MathSAT5. *(p.1)*

## Key Contributions
- OMT tool extending MathSAT5 for optimization over the Boolean, the rational and the integer domains, and their combinations *(p.1)*
- Support for multiple objective functions handled independently or lexicographically, via minmax, or via Pareto optimization *(p.1)*
- Partial Weighted MaxSMT via Pseudo-Boolean Objective optimization *(p.3)*
- Extended SMT-LIBv2 syntax for optimization commands *(p.5)*
- Incremental interfaces through C API with Python/Java wrappers *(p.4)*

## Methodology
OptiMathSAT is written in C++ as an extension of MathSAT5, which implements the standard lazy SMT paradigm. The OMT algorithm is based on an offline architecture: the SMT solver is incrementally called, adding constraints via a block-and-refine approach — each satisfying model is used to tighten the search for better solutions. *(p.2)*

## Architecture
- Built on MathSAT5's CDCL(T) framework *(p.2)*
- Internal SAT solver modified to handle the search for optimizing total truth assignments *(p.2)*
- Runs only once (no restarts from scratch for each candidate) *(p.2)*
- Showed better performance than νZ (Z3's optimizer) on some benchmarks *(p.2)*

## Optimization Functionalities

### Single-Objective Optimization *(p.3)*

**Linear Arithmetic Optimization over CRA, CIA, and CRA:**
Given a term obj on CRA, OptiMathSAT finds a solution (if any) which makes the term obj minimum/maximum. Based on a combination of SAT-based optimization with a theory-specific optimization procedure. *(p.3)*

**Partial Weighted MaxSMT with Pseudo-Boolean Objective:**
For a partial weighted MaxSMT with hard constraints φ and soft constraints ψ_i with positive weights w_i, the goal is to find a model of φ that maximizes the sum of weights of satisfied soft constraints:

$$
\sum_{i} w_i \cdot \psi_i
$$

where w_i are numerical constants and ψ_i are soft constraints. *(p.3)*

OptiMathSAT reduces Partial Weighted MaxSMT to a Pseudo-Boolean Objective function in the form Σ w_i·ψ_i, where ψ_i are numerical constants or unit-coefficient terms. *(p.3)*

Unlike the procedures in νZ/Z3, which use specialized algorithms for MaxSAT/PB-SMT, OptiMathSAT works by encoding the problem as optimization of a linear-arithmetic objective, combining MaxSMT terms with other objectives. *(p.3)*

### Multi-Objective Optimization *(p.4)*

**Multiple Independent Objectives (Boxed Optimization):**
N objectives independently optimized. Equivalent to solving N single-objective problems. Default mode. *(p.4)*

**Lexicographic Optimization:**
Optimizes objectives obj_1, ..., obj_N by decreasing priority. Finds model optimizing obj_1 first, then among optimal obj_1 models, optimizes obj_2, etc. *(p.4)*

**Minmax and Maxmin:**
Goal: find model minimizing max{obj_1, ..., obj_N} (or maximizing min). With a fresh variable t, this reduces to minimize t subject to t ≥ obj_i for all i. OptiMathSAT provides syntactic sugar via minmax/maxmin commands. *(p.4)*

**Linear Combinations:**
Can create objectives that are linear combinations of other objectives, e.g., obj_k = Σ a_i · obj_i. *(p.4)*

**Pareto Optimization:**
A model m₁ Pareto-dominates m₂ if m₁ is at least as good on every objective and strictly better on at least one. OptiMathSAT enumerates all Pareto-optimal models. *(p.4)*

All above combinations hold for obj_i over cost functions over integers, rationals, and Pseudo-Boolean objectives. Can combine MaxSMT with OMT optimization over Integer or Real objectives. *(p.4)*

## Interfaces *(pp.4-5)*

### Input Language
- SMT-LIBv2 extensions via `(assert-soft ...)` for soft clauses and `(minimize|maximize ...)` for objectives *(p.5)*
- Multi-objective mode set via `(set-option :opt.priority box|lex)` *(p.5)*
- Stack-based model retrieval: `(set-model <numeral>)` then `(get-model)` *(p.5)*

### C API
- All MathSAT5 functions available plus OMT-specific optimization functions *(p.4)*
- Each objective associated with the assert call creating it *(p.4)*
- Allows for arbitrary composition of MathSAT5 objectives with inline linear arithmetic functions *(p.4)*
- Useful to particularize contexts (for instance, to build obj functions on mixed Boolean/numeric domains via Linear Generalized Disjunctive Programming) *(p.4)*

### Incremental Interface
- If N input problems are independent, the local bounds of previous model become global bounds for the next objective *(p.4)*
- Optimization can be restarted without overhead, as if N problems were solved separately *(p.4)*

## SMT-LIBv2 Syntax Extensions *(p.5)*

```
(assert-soft <term> [:weight <numeral>] [:id <string>])
(assert-soft <term> [:dweight <decimal>] [:id <string>])
(minimize|maximize <term> [:local-lb <decimal>] [:local-ub <decimal>])
(minmax|maxmin <term>...<term> [:local-lb ...] [:local-ub ...])
(set-option :opt.priority box|lex)
(check-sat)
(set-model <numeral>)
(get-model)
(get-value <VAR>)
```
*(p.5)*

## Example: Supplier Selection *(p.6)*

A toy problem illustrating multi-objective lexicographic optimization:
- Company purchasing 250 units from 4 suppliers with varying prices and quantities
- Goal (A): minimize total cost `(+ q1*23 + q2*21 + q3*20 + q4*10)`
- Goal (B): minimize number of ignored suppliers
- Lexicographic optimization finds cost-optimal solution first, then minimizes suppliers *(p.6)*

## Applications *(pp.6-7)*

### Structured Learning Modulo Theories
Machine learning application: performing inference and learning in hybrid domains characterized by both continuous and Boolean/discrete variables. Structured Learning Modulo Theories (SLMT) addresses this by combining (Structured-Output) Support Vector Machines (SVMs) with SMT, using OptiMathSAT to find the difference and equivalence oracle for the learner. The tool LSMT implementing the SLMT method uses OptiMathSAT as backend OMT engine. *(p.6-7)*

### Automated Reasoning on Constrained Goal Models
Goal Models (CGMs) in Requirements Engineering represent software requirements, objectives, and design qualities. Constrained Goal Models add cross-cutting constraints. OptiMathSAT is used for automatically verifying the realizability of a CGM and for finding optimal realizations to meet quality goals. *(p.7)*

## Future Directions *(p.7)*
- Extending to support objective functions extending to other theories (non-linear) *(p.7)*
- Generalizing implementation to support objective functions on currently unsupported theories *(p.7)*
- Considering combining multiple objectives for Pareto optimization *(p.7)*
- Porting to exploit multi-core architectures of modern CPUs *(p.7)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Soft clause weight | w_i | - | 1 | positive reals | p.3 | Weight for partial weighted MaxSMT |
| Local lower bound | local-lb | - | -∞ | any decimal | p.5 | Per-objective lower bound |
| Local upper bound | local-ub | - | +∞ | any decimal | p.5 | Per-objective upper bound |
| Optimization priority | opt.priority | - | box | box, lex | p.5 | Multi-objective mode selector |

## Figures of Interest
- **Fig 1 (p.5):** SMT-LIBv2 Optimization Extensions syntax — shows the complete API for asserting soft clauses, setting objectives, and retrieving models
- **Fig 2 (p.5):** SMT-LIBv2 encoding of the supplier selection problem — complete worked example

## Results Summary
OptiMathSAT showed better performance than νZ (Z3's optimizer) on the benchmarks tested in the extended version [20]. Available from the OptiMathSAT web page. *(p.2)*

## Limitations
- Only supports linear arithmetic objectives (LRA, LIA) and bit-vectors; no non-linear arithmetic *(p.7)*
- No multi-core support *(p.7)*
- Pareto optimization is noted as future work for combining with multiple objectives *(p.7)*

## Arguments Against Prior Work
- νZ/Z3 uses specialized algorithms for MaxSAT/PB-SMT, while OptiMathSAT encodes these as linear arithmetic optimization — claims this enables more flexible combinations *(p.3)*
- OptiMathSAT showed better performance than νZ on some benchmarks *(p.2)*

## Design Rationale
- Building on MathSAT5 rather than standalone: inherits robust SMT infrastructure, incremental solving, and theory combination *(p.2)*
- Encoding MaxSMT as Pseudo-Boolean Objective rather than specialized algorithm: allows combining MaxSMT terms with other optimization objectives seamlessly *(p.3)*
- Offline architecture (single solver run with tightening constraints): avoids restart overhead *(p.2)*

## Testable Properties
- Lexicographic optimization must find the same optimal value for obj_1 as single-objective optimization of obj_1 *(p.4)*
- Pareto-optimal models: no model in the solution set may be dominated by another *(p.4)*
- Minmax result t must satisfy t ≥ obj_i for all i, and no smaller t exists *(p.4)*
- MaxSMT: the sum of weights of satisfied soft constraints must be maximal among all models satisfying hard constraints *(p.3)*

## Relevance to Project
OptiMathSAT provides the competing OMT approach to νZ (Z3's optimizer) already used in propstore. Understanding its architecture and API differences is valuable for:
1. Comparing optimization strategies for argumentation-based constraint solving
2. The Pseudo-Boolean MaxSMT encoding may be relevant for weighted argumentation problems
3. Multi-objective optimization (lexicographic, Pareto) directly relevant to multi-criteria extension computation

## Open Questions
- [ ] How does OptiMathSAT's performance compare to νZ on argumentation-specific encodings?
- [ ] Can the Pseudo-Boolean encoding be leveraged for weighted defeat relations?

## Collection Cross-References

### Already in Collection
- [[Bjorner_2014_MaximalSatisfactionZ3]] — cited as ref [2]; νZ is the competing Z3-based OMT solver. νZ uses a two-component architecture (MaxSAT + linear arithmetic optimization) while OptiMathSAT unifies MaxSMT into Pseudo-Boolean objective optimization.

### New Leads (Not Yet in Collection)
- Sebastiani & Tomasi (2015) — "Optimization modulo theories with linear rational costs" — full journal treatment of OMT theory
- Teso, Sebastiani, Passerini (2015) — "Structured learning modulo theories" — key ML+SMT application

### Cited By (in Collection)
- [[Bjorner_2014_MaximalSatisfactionZ3]] — cites OptiMathSAT as competing OMT approach and names its linear arithmetic optimization module after it

### Conceptual Links (not citation-based)
- [[Mahmood_2025_Structure-AwareEncodingsArgumentationProperties]] — OptiMathSAT's multi-objective optimization could extend Mahmood's SAT/QSAT argumentation encodings to weighted/preference-based settings
- [[Tang_2025_EncodingArgumentationFrameworksPropositional]] — Tang's multi-valued logic encodings could be optimized via OptiMathSAT's linear arithmetic objectives
- [[Niskanen_2020_ToksiaEfficientAbstractArgumentation]] — OptiMathSAT's Pareto optimization could enable finding Pareto-optimal extensions in multi-criteria argumentation

## New Leads
- Sebastiani & Tomasi (2015) — "Optimization modulo theories with linear rational costs" — ACM Trans. Comput. Logics 16(2), doi:10.1145/2699915 — the journal version with full theoretical treatment *(ref [19], p.7)*
- Sebastiani & Trentin (2015) — "Pushing the envelope of optimization modulo theories with linear-arithmetic cost functions" — TACAS 2015 — extends optimization envelope *(ref [20], p.7-8)*
- Teso, Sebastiani, Passerini (2015) — "Structured learning modulo theories" — key application paper *(ref [21], p.7)*
