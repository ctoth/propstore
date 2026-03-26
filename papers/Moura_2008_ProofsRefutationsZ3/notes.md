---
title: "Proofs and Refutations, and Z3"
authors: "Leonardo de Moura, Nikolaj Bjørner"
year: 2008
venue: "SMT 2008 workshop paper"
doi_url: ""
pages: "1-10"
---

# Proofs and Refutations, and Z3

## One-Sentence Summary
Explains how Z3 exposes proof and model objects on top of its simplifier, internalizer, SAT core, and theory solvers, with two main implementation ideas: implicit quotation to avoid auxiliary symbols and natural-deduction-style proof terms to support modular proof reconstruction. *(p.1-9)*

## Problem Addressed
SMT solvers are often treated as yes/no engines, but many applications need more than satisfiable/unsatisfiable: they need models for satisfiable formulas, invalid cores for non-valid formulas, and proof artifacts for valid formulas. The paper addresses how to make those proof/model products available in Z3 without destroying modular solver architecture or overwhelming proof reconstruction. *(p.1)*

The authors focus on proof-producing internals rather than non-ground proof objects. They explicitly aim for proof terms that can be extracted from a modular DPLL(T)-style solver and checked or consumed by downstream clients. *(p.1, p.3)*

## Key Contributions
- Introduces **implicit quotation**, a way to represent introduced auxiliary literals as quoted subterms instead of fresh variables, simplifying proof reconstruction for clausification and arithmetic internalization. *(p.1, p.4-5)*
- Encodes proof objects as **proof terms** with consequents, so inference rules can be represented directly as function symbols in Z3's term language. *(p.2)*
- Shows how to extract proofs from several Z3 subsystems: rewriting/simplification, Boolean DPLL(T) search, linear arithmetic simplex reasoning, congruence closure, and theory lemmas. *(p.3-8)*
- Describes a modular natural-deduction-style proof architecture using `hypothesis`, `lemma`, and `unit-resolution` so theory solvers can return independent explanation objects. *(p.6-8)*
- Summarizes Z3's model-generation interface and reports the runtime/memory overhead of enabling proofs on SMT-LIB benchmarks. *(p.8-9)*

## Methodology
Z3 first simplifies an input formula, internalizes it into a solver-friendly representation, then solves it using a SAT core plus theory solvers. Proof objects are produced as side effects of those modules and later composed into larger certificates. Instead of logging every low-level SAT step, Z3 delays proof analysis until a conflict clause is produced and then builds natural-deduction-style proof terms from the relevant propagations and theory explanations. *(p.3, p.6-8)*

## Key Equations

$$
\mathit{rewrite}(\ell \approx s,\ \ell,\ \mathit{rewrite}(\ell \leftrightarrow \psi)\ \leftrightarrow \phi)
$$

The paper uses a single `rewrite` axiom schema to record simplification steps that convert a term or formula `s` to `\phi`; the head function symbol of `s` determines which rewriting proof instance is being applied. *(p.3)*

$$
\mathrm{cnf}'(\varphi \lor \psi,\ F) = \mathrm{let}\ (\ell_1,F_1)=\mathrm{cnf}'(\varphi,F),\ (\ell_2,F_2)=\mathrm{cnf}'(\psi,F_1),\ p,\ F_1\land F_2 \land (\ell_1 \lor \ell_2 \lor \neg p)\land (p\lor \neg \ell_1)\land (p\lor \neg \ell_2)
$$

This is the key CNF-introduction rule for disjunction in the quoted clausification scheme: `p` is fresh, but in the implementation the fresh variable can often be replaced by the quoted term `|\varphi \lor \psi|`. *(p.4)*

$$
\forall x_j \in N,\ l_j \le \beta(x_j) \le u_j
$$

For linear arithmetic, every non-basic variable `x_j` is assigned by a valuation `\beta` within lower and upper bounds `l_j` and `u_j`; these bounds are maintained as a tableau invariant. *(p.5)*

$$
\forall x_j \in B,\ l_j \le \beta(x_j) \le u_j
$$

A tableau is satisfied when the same lower/upper-bound condition also holds for all basic variables. Violations trigger pivoting or conflict extraction. *(p.5)*

$$
\operatorname{sup}(a_r) := \sum_{x_j \in N^+} a_{rj}u_j + \sum_{x_j \in N^-} a_{rj}l_j
$$

$$
\operatorname{inf}(a_r) := \sum_{x_j \in N^+} a_{rj}l_j + \sum_{x_j \in N^-} a_{rj}u_j
$$

These summarize the maximum and minimum value implied by a tableau row `r`; they are used to detect an infeasible row and extract a theory conflict clause. *(p.5)*

## Parameters

The paper does not define tunable algorithm parameters. Its main quantitative data are benchmark-level proof overhead measurements: *(p.9)*

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Proof slowdown factor | - | x | - | 1.1-3.0 | 9 | Across the reported SMT-LIB benchmarks, enabling proofs slowed solving by about 10% to 3x. |
| Memory overhead with proofs | - | MB | - | 15.5-426 | 9 | Table 3 reports large benchmark-dependent overhead. |

## Proof-Producing Pipeline
The main solver architecture is:
1. input formula
2. simplifier
3. internalizer
4. SAT solver
5. theory core

Proof terms are produced by those modules as they transform or explain the formula. The paper emphasizes that Z3 does **not** attempt to emit proof objects for non-ground formulas in this version; the proof machinery described is for ground or quasi-satisfiability judgments after internalization. *(p.3)*

## Core Definitions

### Terms, Formulas, and Proof Sort
Z3 uses many-sorted first-order terms. Formulas are Boolean-sorted terms, and the solver includes a dedicated `Proof` sort whose values are proof terms. Quantifiers are represented using patterns that control instantiation, and proof terms can be manipulated directly inside the term language. *(p.2)*

### Proof Terms
A proof object is itself a term whose last argument is the proved formula, called the **consequent**. For example, `modus_ponens p q` is a proof term for `\psi` when `p` proves `\phi \rightarrow \psi` and `q` proves `\phi`; `con(mp(p,q)) = \psi`. *(p.2)*

### Internalization
Internalization converts an arbitrary formula into a normal form suitable for proof-search procedures. The paper discusses two main cases: clausification for Boolean structure and conversion of arithmetic constraints into a global simplex-tableau form. *(p.3-5)*

## Proof Rules and Algorithms

### Simplification Rewriting
The simplifier rewrites formulas according to supported-theory identities, such as normalizing arithmetic expressions into sums of monomials. Each simplification step can be justified by a `rewrite` proof object rather than by a giant explicit axiom set for every built-in theory. *(p.3)*

### Implicit-Quotation Clausification
Instead of introducing an ordinary fresh Boolean variable for every subformula during CNF conversion, Z3 can reuse the term `|\varphi \lor \psi|` as a quoted proxy for that subformula. This preserves equi-satisfiability while making the proof correspondence more direct: the auxiliary clauses are justified by a propositional tautology together with a proof term tagged as `definition`. *(p.4)*

### Arithmetic Internalization and Conflict Extraction
Arithmetic constraints are reduced to simplex-tableau rows with slack variables and bounds. Proofs are extracted directly from the translated tableau by computing row-level `sup` and `inf` values, identifying infeasible rows, and accumulating the bound literals responsible for the contradiction into a theory conflict clause. A single `lemma` proof can then summarize the needed arithmetic reasoning. *(p.4-6)*

### Modular Natural-Deduction Proofs
The modular proof language centers on:
- `hypothesis(p)` for introducing an assumption `p`
- `lemma(p,\ \neg\varphi_1 \lor ... \lor \neg\varphi_n)` for closing a proof branch when the antecedent proof shows falsity
- `unit-resolution(p_0,p_1,...,p_n)` for clause-based propagation

These rules let theory solvers return compact explanations that fit into a shared DPLL(T) proof discipline. A proof term is **closed** when every path ending in a hypothesis also applies a `lemma`; otherwise it is open. *(p.6)*

### DPLL(T)-Based Boolean Proofs
Z3's Boolean engine follows DPLL(T). Instead of logging every resolution step, it constructs proof objects from conflict clauses and the justifications of propagated literals. This still yields a resolution-style proof, but with proof construction delayed until the information actually needed for the conflict is known. The approach avoids direct logging overhead but does not emit a pure resolution proof term. *(p.6-7)*

### Congruence Proofs
Equality reasoning is implemented through congruence closure. The paper uses proof terms for:
- `refl`
- `symm`
- `trans`
- `monotonicity`
- a specialized `comm` rule for commutative functions

Equalities are treated as function applications and inserted into the congruence table; proof objects record how an equality between compound terms follows from equalities between their arguments. *(p.7-8)*

### Theory Lemmas
Theory solvers also emit `th-lemma(p_1,...,p_n,\varphi)` terms whose antecedents encode a `T`-inconsistent set of asserted literals. This gives a common proof interface for non-Boolean theory explanations. *(p.8)*

## Figures and Tables of Interest
- **Figure 1 (p.3):** The overall proof-producing architecture: input formula -> simplifier -> internalizer -> SAT solver/theory core, with proof production distributed across modules.
- **Table 1 (p.9):** Benchmark overhead of enabling proofs, including several SMT-LIB examples with and without proof generation.

## Results Summary
- Proof generation on the sampled SMT-LIB benchmarks adds slowdown between about **1.1x and 3x** and increases memory usage substantially. *(p.9)*
- For example, `NEQ016.siz67` goes from 26.01s / 9.1MB without proofs to 39.84s / 426MB with proofs. *(p.9)*
- `cache.inv16` increases from 15.99s / 11MB to 24.61s / 159MB with proofs, showing that proof memory blow-up can dominate runtime cost. *(p.9)*
- The authors still judge the feature useful because the resulting proof objects support debugging, external checking, and proof-based downstream tools. *(p.8-9)*

## Model Generation
Besides proofs, Z3 can emit models for satisfiable formulas. Models assign values to constants in the input and finite graphs to predicates and functions; a model component for a sort is printed as a partition where each partition element has an associated witness value. For free functions, Z3 can produce compact full interpretations, with an option to avoid assigning interpretations to functions whose values do not influence the satisfying assignment. *(p.8-9)*

Applications mentioned include program exploration and test-case generation for Pex and SAGE, improved debugging in `cpdiff`, and bounded model checking of model programs. *(p.9)*

## Limitations
- The paper does **not** elaborate proof objects for non-ground formulas; it concentrates on the internal proof objects used after internalization. *(p.3)*
- The simplifier relies on a proof checker capable of replaying a limited set of inferences rather than providing a maximally fine-grained proof for every built-in-theory rewrite. The authors note this as a trade-off whose sufficiency depends on the checker context. *(p.2-3)*
- The proof objects are often too large to display effectively, so visualization is acknowledged as a separate challenge. *(p.8)*
- The models section is only a brief summary; more complete model-generation details are deferred to external online material. *(p.8-9)*
- Z3 version 2 can report that a non-ground input is satisfiable after finitely saturating clauses, but it cannot extract additional information from the saturated clause set. *(p.9)*

## Arguments Against Prior Work
- Existing proof-producing SAT systems often log every resolution step. Z3's architecture avoids that logging burden and instead builds proof objects during conflict resolution. *(p.6-7)*
- Standard CNF conversion with fresh variables complicates proof extraction because the proof has to explain those introduced symbols. The implicit-quotation scheme is proposed specifically to avoid that reconstruction burden. *(p.4-5)*
- Arithmetic proof extraction approaches that introduce dedicated explanation variables for every arithmetic subterm are contrasted with the quotation-based strategy, which keeps those equalities trivial and proof-friendly. *(p.5)*

## Design Rationale
- **Why proof terms as ordinary terms?** So proof objects can be stored, manipulated, and combined uniformly inside Z3's existing term infrastructure. *(p.2)*
- **Why implicit quotation?** To avoid auxiliary variables while still using definitional extensions, making clausification and arithmetic proofs easier to reconstruct. *(p.1, p.4-5)*
- **Why modular proof rules?** Because theory solvers should be able to produce independent explanation objects that compose cleanly with the DPLL(T) architecture. *(p.6)*
- **Why delayed conflict-proof construction instead of logging?** To keep the SAT engine efficient while still recovering useful proof terms when a contradiction is discovered. *(p.6-7)*
- **Why include models in the same interface story?** Because many client applications need both certificates of unsatisfiability/validity and concrete satisfying assignments from the same solver architecture. *(p.1, p.8-9)*

## Testable Properties
- If a proof term `p` proves formula `\psi`, then the consequent is always the last argument of `p`, retrievable as `con(p)`. *(p.2)*
- The quoted clausification of a disjunction should be equi-satisfiable with the source formula and justifiable by propositional tautologies once quotation terms are interpreted as literals. *(p.4)*
- For any tableau row, if `u_r < inf(a_r)` with `x_r \le u_r` asserted, or `l_r > sup(a_r)` with `l_r \le x_r` asserted, the row is infeasible and yields a theory conflict clause. *(p.5-6)*
- A proof term is closed iff every branch that ends with a hypothesis also contains a `lemma` application. *(p.6)*
- Enabling proofs in Z3 should add measurable but non-zero runtime and memory overhead on SMT-LIB benchmarks. *(p.9)*

## Relevance to Project
This paper is directly useful if the project cares about solver explanations rather than only final SAT/UNSAT answers. It shows how to keep proof production aligned with a modular SMT architecture instead of treating certificates as an afterthought. The two most reusable ideas are:
1. represent proof artifacts as first-class structured objects rather than opaque logs
2. keep proof extraction local to the module that knows the semantic reason for the step, then compose those proof objects at the conflict boundary

It is also relevant to any propstore path that wants model production and proof/explanation production to coexist in one backend. *(p.1-9)*

## Open Questions
- [ ] How would this proof-term architecture interact with modern incremental SMT workflows and proof logging standards? *(p.1-9)*
- [ ] Can the implicit-quotation trick be generalized cleanly to richer quantified reasoning or higher-order encodings? *(p.4-5)*
- [ ] What proof-object compression or visualization layer would make these large proof terms practical for humans? *(p.8)*

## Related Work Worth Reading
- [[Moura_2008_Z3EfficientSMTSolver]] — the core Z3 architecture paper that this proof/model paper builds on conceptually. *(p.8, ref.3)*
- Nieuwenhuis and Oliveras (2005, 2006) — proof-producing congruence closure and paramodulation-based theorem proving, which underpin the congruence-proof discussion. *(p.7-8, refs.11-12)*
- McPeak (2004) and Sutcliffe (2006) — proof visualization and semantic derivation verification, both cited as relevant downstream uses of proof artifacts. *(p.8, refs.17,20)*

## Collection Cross-References

### Already in Collection
- [[Moura_2008_Z3EfficientSMTSolver]] — companion Z3 engineering paper; this note adds the proof/model-production layer rather than the base SMT architecture. *(p.1, p.8, ref.3)*
- [[Bjorner_2014_MaximalSatisfactionZ3]] — later Z3 engineering work showing how the platform continued to grow beyond the proof/model core described here. *(conceptual)*
- [[Sebastiani_2015_OptiMathSATToolOptimizationModulo]] — another SMT-solver engineering paper that is useful as a contrast in how solver services are exposed to clients. *(conceptual)*

### New Leads (Not Yet in Collection)
- Bradley and Manna (2006), *The Calculus of Computation*, for the DPLL(T) background. *(ref.5)*
- Harrison (1996), *Inductive Proofs of Refutations*, for proof checking in HOL. *(ref.21)*
- Lakatos (1976), *Proofs and Refutations*, for the conceptual framing borrowed by the title/introduction. *(ref.7)*

### Cited By (in Collection)
- (none found)
