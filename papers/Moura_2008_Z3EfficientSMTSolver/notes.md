---
title: "Z3: An Efficient SMT Solver"
authors: "Leonardo de Moura and Nikolaj Bjørner"
year: 2008
venue: "TACAS 2008, LNCS 4963"
doi_url: "https://doi.org/10.1007/978-3-540-78800-3_24"
---

# Z3: An Efficient SMT Solver

## One-Sentence Summary
Z3 is a high-performance SMT solver from Microsoft Research integrating a DPLL-based SAT solver with theory solvers for linear arithmetic, bit-vectors, arrays, tuples, and quantifiers via E-matching, serving as the foundational solver that later extensions like νZ build upon.

## Problem Addressed
Satisfiability Modulo Theories (SMT) is a decision problem for logical first-order formulas with respect to combinations of background theories expressed in classical first-order logic with equality. Z3 is a tool for deciding the satisfiability (or duality) of formulas in these theories, targeting software verification applications. *(p.1)*

## Key Contributions
- New and efficient SMT solver freely available from Microsoft Research *(p.1)*
- Integration of modern DPLL-based SAT solver with multiple theory solvers *(p.2)*
- Novel E-matching engine for quantifier instantiation *(p.3)*
- Model-based quantifier instantiation (MBQI) *(p.4)*
- Won 4 first places and 7 second places in SMT-COMP 2007 *(p.1)*

## Architecture *(p.2)*

Z3 integrates five major components:

### 1. Simplifier
Input formulas are first processed using an inexpensive but efficient simplification. The simplifier applies standard algebraic reduction rules such as `x + 0 → x`, plus also performs limited contextual simplification (e.g., simplifying expressions within a context) and estimates formula sizes using a DAG representation. Formulas with a satisfiable conjunct `p ∧ ¬p` are not compiled into the core, but kept aside for when the main problem is satisfiable. *(p.3)*

### 2. Compiler
The simplified abstract syntax tree representation is compiled into an efficient internal format using small clauses similar to those used in Chaff-like SAT solvers. *(p.3)*

### 3. Congruence Closure Core
The congruence closure core receives truth assignments from the SAT solver. Atoms using range equalities and theories in the SAT solver are propagated by the congruence closure core using a data structure that can be seen as an E-graph. When two nodes are merged, the set of theory solver references are merged, and the merge is propagated to the theory solvers in the intersection of the sets of active references. The core also propagates the effects of the theory solver — equalities that are not produced and atoms inferred as true or false. *(p.3)*

### 4. SAT Solver
Boolean case splits are controlled using a state-of-the-art SAT solver. Integrates standard search pruning methods including conflict clauses, phase caching for guiding case splits, and non-chronological backtracking. *(p.3)*

### 5. Theory Solvers (Satellite Solvers)
- **Linear arithmetic** — handles LA constraints *(p.2)*
- **Bit-vectors** — handles fixed-width bit-vector operations *(p.2)*
- **Arrays** — handles array read/write operations *(p.2)*
- **Tuples** — handles tuple/record operations *(p.2)*

### 6. E-matching Engine
Receives equalities from congruence closure core, produces clauses for the SAT solver. Used for quantifier instantiation. *(p.2)*

## Key Techniques

### Deleting Clauses
Quantifier instantiation has a side-effect of producing new clauses. Thus Z3 must garbage collect lemmas, quantifier instantiations together with their atoms and terms. Terms with no outgoing clauses get freed, then clauses, and then literals. On the other hand, ad-hoc solver-specific quantifier instantiations that were useful in producing conflicts are retained as auxiliary lemmas. *(p.3)*

### Relevancy Propagation
DPLL-based solvers assign a Boolean value to potentially all atoms appearing in a goal. In presence of non-CNF goals, many assignments are irrelevant ("don't cares"). Z3 ignores clause atoms for degenerate theories (such as bit-vectors and arbitrary solvers) such as quantifier instantiations. The algorithm used for determining relevant atoms from don't-cares is described in [4]. *(p.3)*

### Quantifier Instantiation via E-matching
Z3 uses a well-known approach to quantifier reasoning using E-graphs: it instantiates quantified variables using terms from the E-graph. New algorithms for efficiently matching on E-graphs incrementally and efficiently are described in companion papers [5, 6]. *(p.3-4)*

### Model-based Quantifier Instantiation (MBQI)
Z3 also uses a linear arithmetic solver based on the algorithm used in Yices. Z3 also provides an interpolation engine of sorts. The bit-vectors library applies bit-blasting to all bit-vector operators but equalities. *(p.4)*

### Model Generation
Z3 has the ability to generate models as part of its output. Models assign values to the constraints in the input and generates partial function graphs for predicates and function symbols. *(p.4)*

## Clients *(pp.1-2)*

### VCC (Verifier for Concurrent C)
Deductive verifier targeting low-level concurrent systems code. Uses Z3 to verify correctness of concurrent C programs. *(p.1)*

### Spec#/Boogie3
Generates logical verification conditions from Spec# programs (C# extension). Uses Z3 to analyze verification conditions. Spec# replaced the Simplify theorem prover with Z3 in May 2007, resulting in substantial performance improvements. *(p.1-2)*

### Pex (Program EXploration)
Intelligent assistant for automatic unit test generation. Uses Z3 to produce test cases with maximal code coverage. Formulas contain fixed-sized bit-vectors, tuples, arrays, and quantifiers. *(p.2)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| SMT-COMP categories won | - | - | 4 | - | p.1 | 2007 competition results |
| SMT-COMP second places | - | - | 7 | - | p.1 | 2007 competition results |

## Figures of Interest
- **Fig 1 (p.2):** Z3 system architecture diagram — shows SMT-LIB/Simplify/Native text/C/.NET/OCaml inputs → Simplifier → Compiler → Congruence closure core ↔ SAT solver ↔ Theory Solvers (LA, BV, Arrays, Tuples) ↔ E-matching engine

## Results Summary
Z3 won 4 first places and 7 second places at SMT-COMP 2007. Being used in several projects at Microsoft since February 2007 including extended static checking, test case generation, and predicate abstraction. *(p.1, p.4)*

## Limitations
- Short tool paper (4 pages) — detailed algorithms are in companion papers [4, 5, 6] *(throughout)*
- This is the 2008 version; Z3 has evolved substantially since then

## Arguments Against Prior Work
- Z3 replaced the Simplify theorem prover in Spec#/Boogie3, resulting in "substantial performance improvements during theorem proving" *(p.2)*

## Design Rationale
- Modular satellite solver architecture: each theory solver is independent, communicates with core via congruence closure *(p.2)*
- E-matching for quantifiers rather than full first-order reasoning: practical tradeoff for software verification applications *(p.3)*
- Relevancy propagation to avoid wasted work on don't-care atoms in non-CNF goals *(p.3)*

## Testable Properties
- SAT solver should produce UNSAT proofs that are independently checkable *(implied, p.3)*
- Model generation: output models must satisfy all input constraints *(p.4)*
- Congruence closure: merging two nodes must propagate to all theory solvers in the intersection *(p.3)*

## Relevance to Project
Z3 is the foundational SMT solver used in propstore's Z3 backend for argumentation constraint solving. Understanding its architecture (especially the congruence closure core, theory solver integration, and E-matching) is essential for understanding the capabilities and limitations of the Z3 backend. νZ (Bjorner_2014) extends this solver with optimization capabilities.

## Open Questions
- [ ] How has Z3's architecture changed since 2008? (The current Z3 is substantially more capable)
- [ ] Which theory solvers are most relevant for argumentation encodings?

## Collection Cross-References

### Already in Collection
- [[Bjorner_2014_MaximalSatisfactionZ3]] — νZ extends Z3 with optimization (MaxSMT, linear arithmetic objectives). This paper describes the base solver that νZ builds upon.
- [[Sebastiani_2015_OptiMathSATToolOptimizationModulo]] — Competing OMT tool; OptiMathSAT is built on MathSAT5 rather than Z3.

### Cited By (in Collection)
- [[Bjorner_2014_MaximalSatisfactionZ3]] — Z3 is the base solver that νZ extends

### Conceptual Links (not citation-based)
- [[Mahmood_2025_Structure-AwareEncodingsArgumentationProperties]] — Mahmood's SAT/QSAT encodings for argumentation target Z3 as implementation platform
- [[Tang_2025_EncodingArgumentationFrameworksPropositional]] — Tang's propositional logic encodings of AFs can be solved via Z3's SAT engine
- [[Niskanen_2020_ToksiaEfficientAbstractArgumentation]] — mu-toksia uses SAT solving for argumentation; Z3's SAT+theory combination offers richer encoding possibilities

## New Leads
- de Moura & Bjørner (2007) — "Efficient E-Matching for SMT Solvers" [5] — details the E-matching algorithm *(p.4)*
- de Moura & Bjørner (2007) — "Engineering DPLL(T) + Saturation" [6] — theory combination details *(p.4)*
- Ge & de Moura (2009) — "Complete Instantiation for Quantified SMT" [8] — MBQI algorithm *(p.4)*
