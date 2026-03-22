---
title: "Building Problem Solvers"
authors: "Kenneth D. Forbus, Johan de Kleer"
year: 1993
venue: "MIT Press (A Bradford Book)"
---

# Building Problem Solvers

## One-Sentence Summary
A comprehensive textbook that teaches the design and implementation of AI reasoning systems -- particularly three families of truth maintenance systems (JTMS, LTMS, ATMS), pattern-directed inference engines, constraint languages, qualitative physics simulators, model-based diagnosis engines, and symbolic relaxation systems -- all implemented in Common Lisp with complete source code.

## Problem Addressed
AI problem-solving requires maintaining beliefs, managing assumptions, recovering from inconsistencies, caching inferences, and guiding backtracking -- capabilities that individual programs repeatedly reinvent. This book fills the gap between AI theory and practical implementation by providing reusable, composable reasoning infrastructure centered on truth maintenance systems, showing how they combine with inference engines and constraint languages to build powerful problem solvers.

## Key Contributions
- Complete implementations of three TMS families: JTMS (justification-based), LTMS (logic-based with BCP), ATMS (assumption-based with multi-context labels)
- Pattern-directed inference engines: TRE (basic), FTRE (fast, compiled, with context mechanism), JTRE (JTMS-backed), LTRE (LTMS-backed), ATRE (ATMS-backed)
- Constraint languages: TCON (single-context) and ATCON (ATMS-backed, multi-context)
- Qualitative Process Theory implementation (TGIZMO) for measurement interpretation
- Model-based diagnosis engine (TGDE) using ATMS for conflict detection and diagnosis construction
- Symbolic relaxation engine (WALTZER) for constraint satisfaction problems including scene labeling and temporal reasoning
- Boolean Constraint Propagation (BCP) algorithm and prime implicate computation for improving TMS completeness
- Formal treatment of well-founded support, soundness, completeness, and minimality properties across all TMS families

## Book Structure

**Ch 1-2: Preface and Introduction** *(p.18-35)*: Motivation for the book; five desiderata for AI programs (efficiency, coherence, flexibility, additivity, explicitness); design space axes for problem solvers (knowledge model, reference mechanism, procedure model, execution strategy, dependency model).

**Ch 3: Classical Problem Solving (CPS)** *(p.36-84)*: Problem space model; breadth-first, depth-first, best-first, beam search; Boston subway navigation and algebra problem examples; pattern matching with element and segment variables; simplification via rewrite rules.

**Ch 4: Pattern-Directed Inference Systems** *(p.86-124)*: The PDIS model (assertions + rules); TRE implementation with class indexing; unification; KM* natural deduction system; forward and backward chaining.

**Ch 5: Extending Pattern-Directed Inference Systems** *(p.126-166)*: FTRE with rule compilation, open-coded unification, stack-based context mechanism; N-queens example; full KM* implementation with indirect proof.

**Ch 6: Introduction to Truth Maintenance Systems** *(p.167-186)*: Five motivations for TMS (explanation, inconsistency recovery, caching, backtracking guidance, default reasoning); TMS = dependency network of nodes + justifications; 2x2 TMS family classification (label complexity x constraint type).

**Ch 7: Justification-Based TMS (JTMS)** *(p.187-211)*: JTMS node properties (premise, contradiction, assumption); well-founded support; IN/OUT vs true/false (four-valued logic via paired nodes); enabling assumptions, adding justifications, retracting assumptions (two-phase algorithm).

**Ch 8: Putting the JTMS to Work** *(p.214-278)*: JTRE design and implementation; consumer architecture for rule execution; dependency-directed search for N-queens; JSAINT integration system (AND/OR graph, controller, integration library).

**Ch 9: Logic-Based TMS (LTMS)** *(p.281-323)*: Motivation from negation representation; LTMS labels (TRUE/FALSE/UNKNOWN); BCP algorithm; clause encoding; BCP soundness and incompleteness; nogood clauses.

**Ch 10: Putting the LTMS to Work** *(p.325-362)*: LTRE design with direct translation strategy; indirect proof mechanism; closed-world assumptions and set construals; dependency-directed search facility.

**Ch 11: Qualitative Process Theory (TGIZMO)** *(p.364-440)*: QP ontology (quantities, quantity spaces, landmarks, qualitative proportionalities, direct/indirect influences); view and process definitions; influence resolution; inequality reasoning via graph cycles; measurement interpretation algorithm.

**Ch 12: Assumption-Based TMS (ATMS)** *(p.441-469)*: ATMS labels as sets of environments; four label properties (soundness, consistency, completeness, minimality); PROPAGATE/UPDATE/WEAVE/NOGOOD algorithms; solution construction via GOAL node and interpretations procedure; default reasoning.

**Ch 13: Improving TMS Completeness** *(p.471-509)*: Prime implicates and consensus algorithm; formula BCP; full LTMS (eager and lazy variants); Clause Management System (CMS) extending ATMS to arbitrary clauses; Tison's method; discrimination tries for efficient subsumption.

**Ch 14: Putting the ATMS to Work** *(p.512-549)*: ATRE design; many-worlds vs focused strategies; STRIPS-style planning with ATMS (blocks world envisioner); focused problem solving with natural deduction.

**Ch 15: Antecedent Constraint Languages (TCON)** *(p.551-603)*: Constraint model; primitive and compound constraints; value propagation; constraint suspension for diagnosis; local propagation incompleteness.

**Ch 16: Assumption-Based Constraint Languages (ATCON)** *(p.605-634)*: ATCON cells with ATMS backing; assume-constraint for default assumptions; context-free computation; ripple-carry adder example.

**Ch 17: A Tiny Diagnosis Engine (TGDE)** *(p.635-661)*: Model-based diagnosis formalization; system = (SD, COMPS, OBS); AB predicate; conflicts and diagnoses; IAB condition; minimal diagnosis hypothesis; sequential diagnosis with measurement selection.

**Ch 18: Symbolic Relaxation (WALTZER)** *(p.663-694)*: CSP formalization; node/arc/k-consistency; exclude/pick/update operations; scene labeling (Waltz filtering); Allen's temporal logic with 13 interval relationships and transitivity tables.

**Ch 19: Some Frontiers** *(p.697-706)*: Constraint logic programming; scaling up knowledge bases; embedded problem solvers; integrated architectures; cognitive modeling.

## Key Equations

**Propositional specification of JTMS** *(p.182-183)*: Every justification $n_1, \ldots, n_k \rightarrow n$ is a definite clause. The JTMS computes which nodes are derivable from enabled assumptions and justifications.

**Well-founded support** *(p.189)*: A sequence of justifications $J_1, \ldots, J_k$ where $J_1$ justifies node $n$; all antecedents of $J_i$ are justified earlier in the sequence or are enabled assumptions; no node has more than one justification in the sequence.

**BCP algorithms** *(p.290-291)*:
- BCP: Pop clause $c$ from stack $S$; if $c$ is unit open, SET the unknown literal $l$ that satisfies $c$
- SET($l$): Label node of $l$, push every unit-open clause containing $\neg l$ onto $S$, push violated clauses onto $S$
- ADD($c$): Add clause, check if violated/unit-open, call BCP

**ATMS label properties** *(p.448)*:
1. Soundness: $n$ holds in each $E_i$
2. Consistency: $\bot$ cannot be derived from any $E_i$ given $C$
3. Completeness: every consistent environment $E$ in which $n$ holds is a superset of some $E_i$
4. Minimality: no $E_i$ is a proper subset of any other

**ATMS label computation** *(p.448-449)*: Tentative label $E' = \bigcup_k \{ \bigcup_i e_i \mid e_i \in L_{ik} \}$ for all justifications $k$, then remove nogoods and subsumed environments.

**Consensus rule** *(p.476)*: Given $x \lor \beta$ and $\neg x \lor \gamma$, the consensus is $\beta \lor \gamma$ (with duplicate literals removed; discarded if tautologous).

**Diagnosis formalization** *(p.653)*: $D(Cp, Cn) = \bigwedge_{c \in Cp} AB(c) \wedge \bigwedge_{c \in Cn} \neg AB(c)$. A diagnosis for $(SD, COMPS, OBS)$ is $D(\Delta, COMPS - \Delta)$ such that $SD \cup OBS \cup \{D(\Delta, COMPS - \Delta)\}$ is satisfiable.

**Minimal diagnosis characterization (Theorem 17.3)** *(p.657)*: $D(\Delta, COMPS - \Delta)$ is a minimal diagnosis iff $\bigwedge_{c \in \Delta} AB(c)$ is a prime implicant of the set of positive minimal conflicts.

**Measurement scoring** *(p.649)*: Best measurement maximizes $\sum_i c_i \log c_i$ where $c_i$ is the number of diagnoses predicting the $i$th outcome.

**Arc consistency** *(p.666)*: $\forall x \in D_1 \exists y \in D_2, R(x,y)$

**Qualitative proportionality** *(p.371)*: $Q_+ \propto_{Q_+} Q$ means there exists some function that determines $Q$, depends at least on $Q$, and is increasing monotonic in $Q$.

**Direct influence** *(p.372)*: $I+(Q_1, Q_2)$ means process directly increases $Q_1$ through rate $Q_2$; $I-(Q_1, Q_2)$ means directly decreases.

**Diagnosis probability** *(p.646)*: $p(D) = \epsilon^{|D|} \cdot (1 - \epsilon)^{n-|D|}$ where $n$ is number of components and $|D|$ is number faulted.

## Parameters
- FTRE `max-depth`: maximum assumption stack depth *(p.140)*
- JTMS `checking-contradictions`: flag controlling whether contradiction detection is active *(p.194)*
- LTMS `complete`: three modes -- `nil` (BCP only), `:DELAY` (lazy full LTMS), `t` (complete full LTMS) *(p.498)*
- ATCON `delay`: controls whether rule execution checks for external support before firing *(p.631)*
- WALTZER `timestamp`: global clock for tracking propagation sequence *(p.671)*
- JSAINT resource bounds: CPU time, memory, derivation depth *(p.258)*
- N-queens beam width: optional parameter `n` to `beam-solve` *(p.51)*

## Core Systems and Data Structures

### JTMS (Justification-Based TMS)

**Data structures** *(p.202-204)*:
- `jtms` struct: `title`, `node-counter`, `just-counter`, `nodes` (list), `justs` (list), `debugging`, `contradictions` (list), `assumptions` (list), `checking-contradictions`, `node-string`
- `tms-node` struct: `index`, `datum`, `label` (`:IN`/`:OUT`), `support` (nil, justification, or `:ENABLED-ASSUMPTION`), `justifications`, `consequences`, `contradictory?`, `assumption?`
- `just` struct: `index`, `informant`, `consequence`, `antecedents`

**Key algorithms**:
- *Enable assumption* *(p.199)*: Mark as enabled, check if already IN; if not, check if any justification using it as antecedent is now satisfied; recursively propagate inness. Only changes OUT->IN; finite nodes guarantee termination.
- *Add justification* *(p.200)*: Add to dependency network; if consequence already IN, return; otherwise check if satisfied, label consequence IN, propagate recursively.
- *Retract assumption (two-phase)* *(p.200, 207)*: Phase 1: label all nodes whose well-founded explanation contains the retracted assumption as OUT (via `propagate-outness`). Phase 2: for each retracted node, search for alternative support (via `find-alternative-support`). Two phases prevent circular support.
- *Contradiction handling* *(p.207-208)*: When contradiction node becomes IN, call inference-engine-supplied handler with JTMS and contradictory nodes. Handler can retract assumptions, do nothing, or throw.

**Key properties**:
- Logically very weak: only definite (Horn) clauses *(p.190)*
- Cannot deduce negation of any node; OUT means "not derivable" or "negation derivable" *(p.190)*
- Four-valued logic via paired nodes (P, ~P): both IN = contradiction, P IN/~P OUT = true, P OUT/~P IN = false, both OUT = unknown *(p.190-191)*
- Operations cannot be safely aborted or interleaved *(p.201)*

**Interface** *(p.193-196)*: `create-jtms`, `tms-create-node`, `assume-node`, `enable-assumption`, `retract-assumption`, `make-contradiction`, `justify-node`, `in-node?`, `out-node?`, `supporting-justification-for-node`, `assumptions-of-node`

**Files**: `jtms.lisp` (standalone TMS code) *(p.201)*

### LTMS (Logic-Based TMS)

**Data structures** *(p.312-315)*:
- `ltms` struct: `title`, `node-counter`, `clause-counter`, `nodes` (hash table keyed by datum), `clauses`, `debugging`, `checking-contradictions`, `node-string`, `contradiction-handler` (stack), `pending-contradictions`, `enqueue-procedure`, `complete`, `violated-clauses`, `queue`, `conses`, `delay-sat`, `cons-size`
- `tms-node` struct: `index`, `datum`, `label` (`:TRUE`/`:FALSE`/`:UNKNOWN`), `support` (nil, `:ENABLED-ASSUMPTION`, or supporting clause), `true-clauses`, `false-clauses`, `mark`, `assumption?`, `true-rules`, `false-rules`, `ltms`, `true` (cons cell for positive literal), `false` (cons cell for negative literal)
- `clause` struct: `index`, `informant`, `literals` (list of node-label pairs), `pvs` (potential violator count), `length`, `sats` (satisfying literal count), `status`

**BCP algorithm** *(p.289-291, 309-310)*:
- Maintains pending stack $S$ and violated set $V$
- Processes clauses one at a time; if unit-open, forces the unknown literal
- Counter-based: `pvs` counts potential violators; when pvs drops to 0, clause is violated; when pvs is 1, clause forces a label
- Retraction: two-phase like JTMS -- propagate unknownness, then find alternative support

**Key properties**:
- BCP is sound but logically incomplete *(p.296)*
- BCP is P-complete; full propositional satisfiability is NP-complete *(p.296)*
- Formal incompleteness (fails to label) and relaxation incompleteness (fails to detect contradictions) *(p.296)*
- Literal-complete for positive literals in Horn clause sets *(p.297)*
- LTMS shifts propositional reasoning burden from inference engine to TMS *(p.285, 325)*
- No contradiction nodes; uses clauses directly *(p.287)*

**Interface** *(p.300-307)*: `create-ltms`, `tms-create-node`, `enable-assumption`, `retract-assumption`, `add-formula`, `compile-formula`, `add-clause`, `true-node?`, `false-node?`, `unknown-node?`, `support-for-node`, `assumptions-of-node`, `assumptions-of-clause`, `with-contradiction-handler`, `with-assumptions`

**Full LTMS (Ch 13)** *(p.483-499)*: Computes prime implicates via consensus; BCP on prime implicates is logically complete (Theorem 13.3). Lazy variant delays consensus of satisfied clauses. Uses discrimination tries for efficient subsumption checking. Three modes: nil (BCP only), :DELAY (lazy), t (eager).

**Files**: `ltms.lisp` (basic), plus full LTMS extensions *(p.311)*

### ATMS (Assumption-Based TMS)

**Data structures** *(p.460-462)*:
- `atms` struct: `title`, `node-counter`, `just-counter`, `env-counter`, `nodes`, `justs`, `contradictions`, `assumptions`, `debugging`, `nogood-table`, `contra-node`
- `tms-node` struct: `index`, `datum`, `label` (list of environments), `justs`, `consequences`, `nogood?`, `assumption?`, `rules`, `atms`
- `just` struct: `index`, `informant`, `consequence`, `antecedents`
- `env` struct: `index`, `count`, `assumptions` (sorted), `nodes`, `nogood?`, `rules`

**Label update algorithms** *(p.448-451)*:
- PROPAGATE: Given new justification, compute incremental label via WEAVE, then UPDATE
- UPDATE(L, n): Detect nogoods; update label ensuring minimality (remove subsumed environments in both directions); propagate to consequences
- WEAVE: Cross-product of antecedent labels, removing nogoods and subsumed environments
- NOGOOD(E): Mark environment as nogood, remove from all node labels

**Key properties**:
- No current context; all contexts simultaneously represented *(p.441)*
- Labels can grow exponentially in number of assumptions *(p.443)*
- Empty label = node holds in no consistent environment *(p.445-446)*
- No enable/retract; no contradiction handling needed for label maintenance *(p.441, 446)*
- Context switching is free (cost paid upfront in label computation) *(p.441)*
- Assumptions: initial label = singleton environment containing itself; other nodes: initial label = empty *(p.448)*

**Solution construction** *(p.452-454, 466)*:
- Via GOAL node: label of GOAL = all solutions
- Via `interpretations` procedure: given choice sets and defaults, returns maximal consistent environments
- Defaults: solutions must be maximal -- no default can be added without inconsistency *(p.454)*

**Interface** *(p.456-458)*: `create-atms`, `tms-create-node`, `assume-node`, `make-contradiction`, `justify-node`, `in-node?`, `true-node?`, `out-node?`, `node-consistent-with?`, `interpretations`, `explain-node`

**Files**: `atms.lisp` *(p.459)*

### Pattern-Directed Inference (TRE/FTRE)

**Core design** *(p.87-99, 126-149)*:
- Assertions (list-structured data) stored in database indexed by class (leftmost constant symbol)
- Rules have trigger patterns and bodies; when an assertion matching a trigger enters the database, the rule fires
- Class indexing partitions assertions and rules into dbclasses for efficient retrieval
- Two-stage fetch: get candidates by dbclass, then unify each candidate

**TRE** *(p.100-108)*: 5 files (tinter, tdata, rules, unify, treex). Global `*TRE*`. Fields: title, dbclass-table (hash), debugging, rule-counter, rules-run.

**FTRE** *(p.140-149)*: Extends TRE with rule compilation (match + body procedures), open-coded unification, stack-based context mechanism (depth, max-depth, normal-queue, assume-queue, local-rules, local-data). `seek-in-context` pushes new context; `try-in-context` proves goal within context.

**JTRE** *(p.225-231)*: JTMS-backed. Consumer architecture: rule instantiations stored as consumers on TMS nodes, fired on label changes. Trigger syntax: `(:condition :pattern :options)` where condition is `:INTERN`/`:IN`/`:OUT`. Datum struct links assertions to TMS nodes bidirectionally.

**LTRE** *(p.336-339)*: LTMS-backed. Direct translation of logical connectives into clauses. Supports `:NOT`, `:AND`, `:OR`, `:IMPLIES`, `:IFF`, `:TAXONOMY`. Includes indirect proof and closed-world assumption mechanisms.

**ATRE** *(p.518-521)*: ATMS-backed. Three rule execution strategies: `in-rules` (believed in focus), `imp-rules` (implied by focus), `intern-rules` (any assertion). Focus environment mechanism. Localized contradiction handlers per environment.

### Constraint Languages (TCON/ATCON)

**TCON** *(p.558-593)*: Single-context constraint language. Primitive constraints define cells and formulae (set/use/body). Value propagation: when a cell receives a value, rules depending on it fire. No TMS -- values overwritten on context switch. Supports compound constraints and constraint suspension for diagnosis.

**ATCON** *(p.605-634)*: ATMS-backed constraint language. Cells can hold multiple values simultaneously (one per environment). `assume-constraint` creates default assumptions for components. Rule execution via ATMS enqueue mechanism. No context switching needed. Key fields: `cells`, `queue`, `constraints`, `atms`, `disjunction`, `delay`. Cell domain restricts allowable values; violations create ATMS nogoods.

**Key difference** *(p.617-620)*: TCON recomputes on context switch; ATCON caches all results across all contexts. ATCON eliminates duplicate rule executions. Trade-off: ATCON has higher bookkeeping cost but wins when many context switches or expensive rule executions.

### Qualitative Process Theory (TGIZMO)

**QP ontology** *(p.366-385)*:
- Quantities: amount $A(q)$ and derivative $D_s(q)$, each mapping to reals
- Quantity spaces: ordinal relationships between quantities and landmark values
- Qualitative proportionalities ($Q_+$, $Q_-$): monotonic functional dependencies
- Direct influences ($I+$, $I-$): only from physical processes (sole mechanism assumption)
- Indirect influences: propagated via qualitative proportionalities
- Views: define types of physical configurations (e.g., Contained-Stuff)
- Processes: define causal mechanisms with influences (e.g., Heat-Flow, Fluid-Flow)

**Implementation** *(p.395-430)*:
- Built on LTRE; TGIZMO struct with fields for quantities, comparisons, comp-cycles, influence-order, states
- Modeling language: `defView`, `defProcess`, `defEntity`, `defPredicate`
- Influence resolution: sort influences by sign, cancel opposing direct influences, flag ambiguities
- Inequality reasoning: graph-based cycle detection; only comparisons in domain theory are tracked; transitivity inferred only in cycles
- Measurement interpretation: `search-pps` finds consistent view/process structures; `resolve-completely` resolves influences via DDS; states cached as snapshots

**Files** *(p.395-399)*: defs.lisp, mblang.lisp, gpvs.lisp, resolve.lisp, ineqs.lisp, states.lisp, mi.lisp, laws.lisp, debug.lisp

### Diagnosis Engine (TGDE)

**Formalization** *(p.652-658)*:
- System = $(SD, COMPS, OBS)$ where SD is system description, COMPS is components, OBS is observations
- Diagnosis: $D(\Delta, COMPS - \Delta)$ such that $SD \cup OBS \cup \{D\}$ is satisfiable
- Minimal diagnosis: no proper subset of faulted components is also a diagnosis
- Conflict: AB-clause entailed by $SD \cup OBS$; minimal conflict = no proper sub-clause is a conflict
- IAB condition: AB only occurs negatively; guarantees minimal diagnosis hypothesis holds (Theorem 17.2)
- Characterization: minimal diagnoses = prime implicants of positive minimal conflicts (Theorem 17.3)

**Implementation** *(p.638-649)*:
- Uses ATCON with `assume-constraint` for each component (default OK assumption)
- Conflicts detected via ATMS nogoods when observed values contradict predicted values
- Minimal diagnoses constructed by ATMS `interpretations` with OK assumptions as defaults
- Sequential diagnosis: iteratively measure, update conflicts, until single minimal-cardinality diagnosis remains
- Measurement selection: maximize $\sum_i c_i \log c_i$ to most evenly split diagnoses

### Symbolic Relaxation (WALTZER)

**CSP formalization** *(p.664-667)*:
- Variables $v_1, \ldots, v_n$ with domains $D_1, \ldots, D_n$; relations $R_1, \ldots, R_m$
- Node consistency: $\forall x \in D, R(x)$
- Arc consistency: $\forall x \in D_1 \exists y \in D_2, R(x,y)$
- k-consistency generalizes but cost rises exponentially with k
- Best trade-off: arc consistency + backtracking search

**Implementation** *(p.670-676)*:
- Network struct: cells, constraints, cell-queue, constraint-queue, timestamp, status (NEW/QUIESCENT/IN-PROGRESS/OVERCONSTRAINED)
- Cell struct: name, value (current possibilities), constraints, possible-values, out-reasons (dependency record)
- Constraint struct: name, parts (cells), update-procedure
- Operations: `exclude` (remove value from cell domain), `pick` (force value), `update` (run constraint)
- Cell operations have priority over constraint updates
- Backtracking via cell property `:STACK` (saves/restores value and out-reasons)

**Applications**:
- Scene labeling (Waltz filtering): junction catalog, line interpretations (convex, concave, boundary, occluding) *(p.676-683)*
- Temporal reasoning: Allen's 13 interval relationships, transitivity tables, temporal database *(p.684-690)*

## Implementation Details

**Common Lisp conventions** *(p.20-21, 42-43)*:
- No CLOS (not standardized when written); structs with `defstruct` and `CONS-NAME` for field abbreviation
- Global variable convention: `*variable-name*`
- `kaux`/`setq` style over `let` to reduce indentation
- `#+ reader` macros for cross-platform loading
- Programs known to run on Symbolics, Lucid CL, GCLisp, MCL

**File organization** *(p.707-708)*: Each system has a loader file; subdirectories: `cps`, `tre`, `ftre`, `jtms`, `ltms`, `tgizmo`, `atms`, `tcon`, `gde`, `waltx`, `utils`

**Cross-cutting patterns**:
- Inference engine + TMS decomposition: TMS handles beliefs/dependencies, inference engine handles domain reasoning *(p.173-174)*
- Consumer architecture (JTRE): rule instantiations passed to TMS, fired on label changes *(p.219-221)*
- Class indexing: partitions assertions/rules by leftmost constant symbol; one-level discrimination tree *(p.96-97, 131)*
- Contradiction handlers: stack-based, `unwind-protect` for restoration *(p.208, 301, 319)*
- Factory pattern for DDS: creates closures over choice sets and handlers *(p.355)*
- Debug flags: fine-grained control via lists of symbols (especially in TGIZMO) *(p.396)*

## Figures of Interest

- **Fig 4.1** *(p.95)*: Antecedent architecture cycle: assertions/rules -> database -> queue -> derived assertions/rules
- **Fig 6.5** *(p.174)*: Problem solver = inference engine + TMS (fundamental architecture)
- **Fig 6.6** *(p.178)*: Dependency network graphical notation (justification triangles, node types)
- **Fig 6.10** *(p.184)*: TMS family classification grid (JTMS/ATMS/LTMS/CMS)
- **Fig 7.1** *(p.191)*: Four-valued logic via paired nodes P and ~P
- **Fig 8.5** *(p.244)*: JSAINT architecture (AND/OR graph + controller + integration library)
- **Fig 9.2** *(p.283)*: Encoding A v B v C in JTMS (6 nodes, 6 justifications vs 1 LTMS clause)
- **Fig 11.2** *(p.374)*: QP theory causal account (influences, proportionalities, flows)
- **Fig 12.1-12.3** *(p.444-446)*: ATMS labels and environments illustrated
- **Fig 14.1** *(p.516)*: Venn diagram of ATMS rule execution strategies (intern > in > implied-by)
- **Fig 17.5-17.6** *(p.643-644)*: Diagnosis lattice with conflict-based elimination
- **Fig 18.7** *(p.685)*: Allen's 13 temporal interval relationships

## Results Summary

- **N-queens (FTRE vs JTRE)** *(p.154, 221-223)*: N=8: FTRE uses 15,720 assumptions in 95s; JTRE uses 2,514 assumptions in 154s. Dependency-directed search makes far fewer assumptions but each is more expensive. Both strategies are exponential.
- **Pressure regulator prime implicates** *(p.485-486)*: 3 qualitative equations yield 2,814 prime implicates; reducing to input-output variables gives only 21, of which all are definite clauses. Demonstrates compilation of qualitative models into simple BCP-compatible form.
- **TGIZMO measurement interpretation** *(p.423-429)*: Two containers yields 8 states; three containers yields multiple states requiring disambiguation of Ds values.
- **BCP complexity** *(p.296)*: BCP is linear per propagation; search with nogood recording is exponential. P-complete for the circuit value problem.
- **CSP arc consistency** *(p.666-667)*: Enforceable in linear time; k-consistency cost rises exponentially with k.

## Limitations

- **JTMS**: Only definite clauses; cannot represent negation directly; logically very weak *(p.190)*
- **BCP incompleteness**: Sound but incomplete; cannot always detect contradictions or determine labels *(p.296)*
- **ATMS label explosion**: Labels can grow exponentially in number of assumptions *(p.443)*
- **Prime implicate explosion**: Number of prime implicates often exponential in formula size *(p.484)*
- **TGIZMO**: Single time period only; lacks many features of full QP theory *(p.386, 429)*
- **TGDE**: Cannot model all fault types (violates IAB for short circuits etc.); cannot represent negations or disjunctions of variable assignments *(p.658)*
- **WALTZER**: Adding values or removing constraints typically requires full reinitialization *(p.691)*
- **Stack-based context (FTRE)**: No caching of rule firings; forced depth-first search; no result sharing across contexts *(p.160)*
- **All TMS implementations**: Not safe for concurrent access, interleaving, or abort *(p.201, 459)*

## Arguments Against Prior Work

- **Expert system shells** *(p.20-21)*: Deep understanding of tools gives better chance of using them; commercial tools hide internals; state of the art is not static.
- **OPS-like retraction** *(p.175)*: TMSs enforce rational retraction (only retract facts without justification); OPS-style arbitrary retraction leads to inefficiency with TMSs since old justifications accumulate.
- **Chronological backtracking** *(p.170-172)*: Wastes computation by rediscovering known contradictions and exploring provably futile branches. Dependency-directed backtracking (enabled by TMS) jumps to relevant choice points.
- **Procedural deduction systems** *(p.93)*: MicroPlanner, Conniver, Schemer received less attention and have not seen widespread application.
- **Search as the essence of intelligence** *(p.79)*: Search is just a component; domain-specific control knowledge (Bundy's methods) reduces search dramatically.

## Design Rationale

- **Problem solver = inference engine + TMS**: Natural partitioning allows each to focus on its strengths; inference engine handles domain reasoning, TMS handles belief management *(p.173-174)*
- **Consumer vs probing strategy**: Consumer architecture (pass rule instantiations to TMS) is simpler than inference engine polling TMS for label changes *(p.219)*
- **Direct translation over multilevel expansion**: Fewer assertions, clearer explanations, more efficient *(p.331)*
- **Rule compilation**: Eliminate runtime interpretation; match and body become compiled procedures *(p.135-136)*
- **Prototype with rules, then hardcode**: Natural migration path -- prototype flexibility in pattern-directed rules, then move critical operations to compiled procedures for performance *(p.430)*
- **Class indexing**: Simple but effective one-level discrimination tree; partitions by leftmost constant symbol *(p.96-97)*
- **JTMS vs LTMS vs ATMS selection**: Use simplest TMS that matches the task; more complex TMSs waste computation on irrelevant aspects *(p.185)*
- **Many-worlds vs focused**: Many-worlds (ATMS) for small problems or when all solutions needed; focused for large problems with single-solution goals *(p.512-513)*
- **Inequality reasoning via graph cycles**: Only relevant comparisons tracked; transitivity only in cycles; far more efficient than naive transitive closure *(p.392-393)*

## Testable Properties

1. **JTMS well-founded support**: Every IN node has a well-founded support traceable to enabled assumptions with no cycles *(p.189)*
2. **JTMS retraction correctness**: After retracting an assumption, no IN node depends (transitively) on the retracted assumption *(p.200)*
3. **BCP soundness**: BCP never labels a node TRUE/FALSE incorrectly, nor signals a false contradiction *(p.296)*
4. **ATMS label soundness**: Every environment in a node's label actually supports that node *(p.448)*
5. **ATMS label consistency**: No environment in any label is a nogood *(p.448)*
6. **ATMS label completeness**: Every consistent supporting environment is a superset of some label environment *(p.448)*
7. **ATMS label minimality**: No label environment is a proper subset of another *(p.448)*
8. **Justification monotonicity**: The set of justifications grows monotonically (never removed) *(p.188)*
9. **LTMS clause satisfaction**: A satisfied clause has `sats` > 0 *(p.314-315)*
10. **Order independence**: Rules and assertions in any order produce same consequences *(p.92)*
11. **IAB condition implies minimal diagnosis hypothesis** *(p.656)*: If all AB literals occur only negatively in antecedents, every superset of a diagnosis is also a diagnosis
12. **Arc consistency**: After enforcement, for every value in one cell's domain, a compatible value exists in every connected cell's domain *(p.666)*

## Relevance to Project

This book is directly relevant to propstore in several ways:

- **Truth maintenance for belief management**: The JTMS/LTMS/ATMS family provides the foundation for tracking which beliefs are supported, detecting contradictions among claims, and managing assumption-based reasoning -- core requirements for a system that maintains propositions from multiple sources.
- **Dependency networks for provenance**: The justification structures (informant + antecedents -> consequence) directly model how conclusions depend on premises, mapping to propstore's need to track claim lineage and argumentation chains.
- **Well-founded support for argumentation**: The formal notion of well-founded support (no circular dependencies, traceable to assumptions) aligns with admissibility criteria in abstract argumentation frameworks (Dung 1995).
- **Default reasoning**: The ATMS `interpretations` procedure with defaults parallels the computation of preferred/stable extensions in argumentation -- maximal consistent sets of assumptions.
- **Contradiction handling**: TMS contradiction detection and resolution maps to attack relations and defeat in argumentation frameworks.
- **BCP for constraint propagation**: The LTMS BCP algorithm could be applied to propagate acceptance/rejection labels through argumentation graphs, analogous to labelling-based semantics.
- **Model-based diagnosis**: TGDE's conflict/diagnosis duality mirrors the relationship between attacks and extensions in argumentation -- conflicts constrain which sets of arguments can be jointly accepted.

## Open Questions

1. How does the CMS (Clause Management System) compare to modern SAT solvers in terms of the prime implicate approach vs. DPLL/CDCL?
2. The book uses definite clauses for JTMS/ATMS -- how would extending to full clauses (as in CMS) affect performance on argumentation-scale problems?
3. Can the ATMS `interpretations` procedure be adapted to compute Dung-style extensions efficiently, or is the overhead of full label computation too high?
4. The IAB condition ensures the minimal diagnosis hypothesis holds -- is there an analogous condition for argumentation frameworks that would simplify extension computation?
5. How do the TMS retraction algorithms compare to modern incremental belief revision approaches?
6. TGIZMO's inequality reasoning via graph cycles -- could a similar technique accelerate preference-based argumentation?

## Related Work Worth Reading

- Doyle, J. "A truth maintenance system." *Artificial Intelligence* 12, 1979. (Original JTMS) *(p.186)*
- de Kleer, J. "An assumption-based TMS." *Artificial Intelligence* 28, 1986. (Original ATMS) *(p.469)*
- de Kleer, J. "Problem solving with the ATMS." *Artificial Intelligence* 28, 1986. *(p.469)*
- McAllester, D. "An outlook on truth maintenance." AI Memo 551, MIT, 1980. *(p.186)*
- Reiter, R. "A theory of diagnosis from first principles." *Artificial Intelligence* 32, 1987. *(p.661)*
- de Kleer, J. and Williams, B. "Diagnosing multiple faults." *Artificial Intelligence* 32, 1987. *(p.661)*
- Allen, J. "Maintaining knowledge about temporal intervals." *CACM* 26, 1983. *(p.694)*
- Waltz, D. "Understanding line drawings of scenes with shadows." In *The Psychology of Computer Vision*, 1975. *(p.694)*
- Mackworth, A. "Consistency in networks of relations." *Artificial Intelligence* 8, 1977. *(p.694)*
- Kalish, D. and Montague, R. *Logic: Techniques of Formal Reasoning*. Harcourt Brace, 1964. *(p.124)*
- Bundy, A. *The Computer Modelling of Mathematical Reasoning*. Academic Press, 1983. *(p.84)*
- Slagle, J. "A heuristic program that solves symbolic integration problems in freshman calculus." *JACM* 10, 1963. (SAINT) *(p.278)*
- Stallman, R. and Sussman, G. "Forward reasoning and dependency-directed backtracking." AI Memo 380, MIT, 1977. *(p.278)*
- Tison, P. "Generalization of consensus theory and application to the minimization of Boolean functions." *IEEE Trans. Electronic Computers* EC-16(4), 1967. *(p.509)*

## Collection Cross-References

### Already in Collection
- [[Doyle_1979_TruthMaintenanceSystem]] — BPS Ch6-8 implement and extend Doyle's original TMS as the JTMS; the book provides the definitive implementation guide for this system
- [[deKleer_1984_QualitativePhysicsConfluences]] — BPS Ch11 implements TGIZMO, a full qualitative process theory simulator based on this work's confluence equations and envisionment framework
- [[deKleer_1986_AssumptionBasedTMS]] — BPS Ch12-13 implement the ATMS from this paper with complete label algorithms, the four label invariants, and the consensus-based CLTMS extension
- [[deKleer_1986_ProblemSolvingATMS]] — BPS Ch14 implements the control regime, consumer architecture, and constraint language from this companion paper
- [[Reiter_1980_DefaultReasoning]] — BPS Ch6 discusses default reasoning as a motivation for TMS; the LTMS (Ch9-10) provides a propositional substrate for default reasoning via closed-world assumptions

### New Leads (Not Yet in Collection)
- de Kleer, J. and Williams, B. "Diagnosing multiple faults." *Artificial Intelligence* 32, 1987 — key diagnosis paper, BPS Ch17 implements a simplified version
- Allen, J. "Maintaining knowledge about temporal intervals." *CACM* 26, 1983 — BPS Ch18 implements Allen's temporal reasoning with WALTZER
- Mackworth, A. "Consistency in networks of relations." *Artificial Intelligence* 8, 1977 — foundational CSP/arc-consistency paper, BPS Ch18 implements these algorithms
- Stallman, R. and Sussman, G. "Forward reasoning and dependency-directed backtracking." AI Memo 380, MIT, 1977 — original dependency-directed backtracking work predating Doyle's TMS

### Conceptual Links (not citation-based)
- [[Dixon_1993_ATMSandAGM]] — **Strong.** Dixon proves ATMS context switching is behaviourally equivalent to AGM revision. BPS provides the definitive ATMS implementation that Dixon's theoretical results apply to. Together they bridge implementation (BPS) and theory (Dixon).
- [[Falkenhainer_1987_BeliefMaintenanceSystem]] — **Strong.** BMS generalizes the JTMS (which BPS implements in Ch7-8) to continuous-valued beliefs via Dempster-Shafer. BPS provides the baseline Boolean TMS that BMS extends.
- [[Shapiro_1998_BeliefRevisionTMS]] — **Strong.** Shapiro bridges belief revision theory and TMS practice. BPS provides the implementation substrate (JTMS/LTMS/ATMS) that Shapiro's theoretical analysis covers.
- [[McAllester_1978_ThreeValuedTMS]] — **Strong.** McAllester's three-valued TMS is an early variant in the TMS family tree. BPS Ch6 discusses the TMS family classification that positions McAllester's work.
- [[Martins_1983_MultipleBeliefSpaces]] — **Moderate.** Multiple belief spaces relate to the ATMS's multiple-world reasoning. BPS's ATMS (Ch12-14) provides a different mechanism for the same goal.
- [[Martins_1988_BeliefRevision]] — **Moderate.** Belief revision in the SNePS tradition connects to BPS's treatment of assumption retraction and contradiction handling across all TMS variants.
- [[McDermott_1983_ContextsDataDependencies]] — **Strong.** McDermott's context mechanism directly relates to BPS Ch5's stack-oriented context mechanism in FTRE and the ATMS's environment-based contexts.
- [[Ginsberg_1985_Counterfactuals]] — **Moderate.** Counterfactual reasoning via three-valued logic connects to BPS's LTMS three-valued labels (:TRUE/:FALSE/:UNKNOWN) and assumption-based hypothetical reasoning.
- [[Alchourron_1985_TheoryChange]] — **Moderate.** AGM theory provides the formal criteria for belief change. BPS implements the computational machinery (TMS family) that Dixon later proved equivalent to AGM operations.
- [[Dung_1995_AcceptabilityArguments]] — **Moderate.** Dung's abstract argumentation semantics (grounded, preferred, stable extensions) can be computed using the dependency networks and label propagation algorithms that BPS implements in detail.
- [[Bondarenko_1997_AbstractArgumentation-TheoreticApproachDefault]] — **Moderate.** Bondarenko et al. show default reasoning (which BPS supports via LTMS/ATMS) is a form of assumption-based argumentation.
- [[Toni_2014_TutorialAssumption-basedArgumentation]] — **Moderate.** ABA uses assumptions as the basis for argumentation, directly paralleling the ATMS's assumption-based approach that BPS implements.

### Cited By (in Collection)
- (none found — no collection papers cite Forbus & de Kleer 1993 directly)
