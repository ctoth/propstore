---
title: "µ-toksia: An Efficient Abstract Argumentation Reasoner"
authors: "Andreas Niskanen, Matti Järvisalo"
year: 2020
venue: "KR 2020 (17th International Conference on Principles of Knowledge Representation and Reasoning)"
doi_url: "https://doi.org/10.24963/kr.2020/82"
---

# µ-toksia: An Efficient Abstract Argumentation Reasoner

## One-Sentence Summary
Describes the µ-toksia system, a SAT-based argumentation reasoner that won first place in all main-track reasoning tasks at ICCMA 2019 and supports standard and dynamic abstract argumentation under all central semantics.

## Problem Addressed
Efficient computation of argumentation semantics (credulous/skeptical acceptance, enumeration of extensions) over standard and dynamic abstract argumentation frameworks, addressing the computational challenges across multiple semantics (complete, preferred, stable, semi-stable, stage, grounded, ideal). *(p.1)*

## Key Contributions
- Won first place in all reasoning tasks in the main track of ICCMA 2019 *(p.1)*
- Supports all tracks and reasoning tasks from ICCMA 2019: standard (DC, DS, SE, EE tasks) and dynamic tracks *(p.1)*
- Scales noticeably better on dynamic track tasks than competitors *(p.1)*
- Provides SAT-based algorithms for all central argumentation semantics *(p.2)*
- Implements unit propagation as a preprocessing technique for grounded semantics *(p.2)*
- Open-source C++ implementation with standard TGF/APX input formats *(p.3)*

## Methodology
The system is built entirely on SAT-based reasoning. For each argumentation semantics and reasoning task, µ-toksia constructs appropriate SAT encodings and uses iterative SAT solver calls to compute extensions, determine credulous/skeptical acceptance, and enumerate extensions. *(p.2)*

## Key Equations

### Argumentation Framework Definition
An argumentation framework (AF) is a pair $F = (A, R)$ where $A$ is a finite set of arguments and $R \subseteq A \times A$ is a set of attacks. An argument $a \in A$ is defended by a set $S \subseteq A$ iff for all $b \in A$, if $(b, a) \in R$ then there exists $c \in S$ such that $(c, b) \in R$. *(p.1)*

### Characteristic Function
$$
\Gamma_F(S) = \{a \in A \mid S \text{ defends } a\}
$$
Where: $\Gamma_F$ is the characteristic function of framework $F$, $S \subseteq A$ is a set of arguments. *(p.1)*

### Conflict-Free
A set $S \subseteq A$ is conflict-free iff there are no $a, b \in S$ with $(a, b) \in R$. *(p.1)*

### Admissibility
A conflict-free set $S$ is admissible iff $S \subseteq \Gamma_F(S)$ (i.e., $S$ defends all its members). *(p.1)*

### Complete Extension
An admissible set $S$ is a complete extension iff $\Gamma_F(S) = S$. *(p.2)*

### Grounded Extension
The grounded extension is the least fixed point of $\Gamma_F$, equivalently the intersection of all complete extensions. *(p.2)*

### Preferred Extension
A preferred extension is a $\subseteq$-maximal admissible set (equivalently a $\subseteq$-maximal complete extension). *(p.2)*

### Stable Extension
An admissible set $S$ is a stable extension iff $S$ attacks every $a \in A \setminus S$. *(p.2)*

### Semi-Stable Extension
A complete extension $S$ is semi-stable iff $S \cup S^+$ is $\subseteq$-maximal, where $S^+ = \{a \mid \exists b \in S: (b,a) \in R\}$ is the set attacked by $S$. *(p.2)*

### Stage Extension
A conflict-free set $S$ is a stage extension iff $S \cup S^+$ is $\subseteq$-maximal. *(p.2)*

### Ideal Extension
A set $S$ is ideal iff $S$ is admissible and $S \subseteq E$ for each preferred extension $E$; the ideal extension is the $\subseteq$-maximal ideal set. *(p.2)*

### SAT Encoding Variables
For each argument $a \in A$:
- $x_a$: argument $a$ is in the extension (accepted) *(p.2)*
- $r_a$: argument $a$ is attacked by a member of the extension (rejected) *(p.2)*

### Conflict-Free SAT Encoding
$$
\bigwedge_{(a,b) \in R} (\neg x_a \lor \neg x_b)
$$
*(p.2)*

### Admissible SAT Encoding
$$
\text{CF}(F) \land \bigwedge_{a \in A} (x_a \rightarrow r_{a'} \text{ for all } a' \text{ attacking } a)
$$
Where CF(F) is the conflict-free encoding, plus defense constraints. *(p.2)*

### Stable Extension SAT Encoding
$$
\text{CF}(F) \land \bigwedge_{a \in A} (x_a \lor r_a)
$$
*(p.2)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Timeout | - | seconds | 600 | - | 4 | ICCMA 2019 competition setting |
| Memory limit | - | GB | 8 | - | 4 | RAM limit for benchmarks |
| CPU time limit (further eval) | - | seconds | 600 (ICCMA), 10 min stated | - | 4 | Additional evaluation timeout |

## Implementation Details
- Implemented in C++ using standard STL data structures *(p.3)*
- SAT solver interface via CaDiCaL (for standard static tasks; SAT competition winner) and CryptoMiniSAT *(p.3)*
- Makes extensive use of SAT solver API: assumptions, iterative calls, user propagators *(p.3)*
- Solver instance is initialized only once during a single execution (as SAT solver state is preserved across calls); iterative computations are done while keeping the state of the SAT solver through its API *(p.3)*
- Input formats: TGF (Trivial Graph Format) and APX *(p.3)*
- APIs: produces `v(y|n)` for skeptical/credulous acceptance, `w` for enumeration *(p.3)*
- Dynamic AFs: file with changes to attack structure *(p.3)*
- Available open-source at https://bitbucket.org/2-complement-ations/mu-toksia under MIT license *(p.3)*
- Also provides interfaces to Glucose (Audemard and Simon 2018) and CryptoMiniSAT (Soos, Nohl, and Castelluccia 2009) *(p.3)*
- SAT solver available for integration as an assumptions interface *(p.3)*

### Algorithmic Details by Semantics

#### Grounded Semantics
- Computed via unit propagation (not full SAT): simulate the process of iteratively accepting unattacked arguments, rejecting arguments they attack, and repeating *(p.2)*
- Uses `must_in_GR(F, p)` to decide whether argument $p$ is in the grounded extension *(p.2)*
- The grounded extension is computed in polynomial time *(p.2)*

#### Stable Semantics
- Direct SAT encoding: conflict-free plus every argument is either in or attacked *(p.2)*
- Credulous acceptance (DC-ST): check if there exists a stable extension containing the query *(p.2)*
- Skeptical acceptance (DS-ST): check if every stable extension contains the query *(p.2)*

#### Complete Semantics
- SAT encoding extends admissibility with additional constraints requiring that every defended argument is included *(p.2)*
- For credulous/skeptical: iterative SAT calls *(p.2)*

#### Preferred Semantics
- Credulous (DC-PR): equivalent to DC-CO (credulous complete) — just check admissibility *(p.2)*
- Skeptical (DS-PR): more complex, uses iterative approach *(p.2)*
- Single extension (SE-PR): find maximal admissible set via iterative SAT calls *(p.2)*
- Enumeration (EE-PR): enumerate all maximal complete extensions using blocking clauses *(p.2)*

#### Semi-Stable Semantics
- First check if a stable extension exists; if so, semi-stable = stable *(p.2)*
- Otherwise, maximize the range $S \cup S^+$ using iterative SAT with optimization *(p.2)*

#### Stage Semantics
- Similar to semi-stable but over conflict-free sets rather than complete extensions *(p.2)*

#### Ideal Semantics
- Compute complete extension, then intersect to find ideal *(p.2)*
- An argument is ideal iff it is admissibly contained in every preferred extension *(p.2)*

### Dynamic AF Support
- $x_{a,i}$ variables (for $i \in \{0, \ldots, t\}$) represent the status of the extension determined by the $x_a$ variables at time step $i$ *(p.2)*
- For credulous and skeptical acceptance, uses the ITEGAR algorithm framework *(p.2)*
- For stable semantics: first check if stable extension exists using assumptions $\hat{x}_{a,0}$ *(p.2)*
- In the positive case, invoke the algorithm for stable semantics *(p.2)*
- For semi-stable: check whether a complete extension maximizes $S \cup S^+$ *(p.2)*
- Dynamic changes to attack structure are represented as: `+att(c,a)` and `-att(c,b)` notation *(p.3)*
- Parameters: $t \geq 0$ and $i = 0, \ldots, t$ for time steps *(p.2)*

### Preprocessing: Unit Propagation
- Before computing credulous/skeptical acceptance, run grounded semantics unit propagation *(p.2)*
- If query $p$ is in grounded extension → immediately return YES for DC, YES for DS *(p.2)*
- For some semantics, check if argument is attacked by grounded arguments *(p.2)*

## Figures of Interest
- **Fig 1 (p.2):** SAT encodings used by µ-toksia — shows exact clauses for conflict-free, admissible, complete, preferred, stable, semi-stable, stage, grounded, and ideal semantics
- **Fig 2 (p.4):** Performance comparison scatter plots on selected tasks (DC-CO, SH-ST, DC-ST) comparing µ-toksia against Argmat-sat, AFGCL, and Aspartix — shows µ-toksia dominates on most instances

## Results Summary
- ICCMA 2019: µ-toksia ranked first in all reasoning tasks in the main track *(p.1, p.4)*
- Very easy for declarative approaches with almost no timeouts on the main track; the DC and DS benchmarks for static tasks were very easy for all solvers *(p.4)*
- On further evaluation (Table 1, Fig 2): µ-toksia accepts all files in all tasks, with best or near-best runtimes *(p.3-4)*
- Compared against: Argmat-sat (ICCMA 2017), Aspartix (version V19-04), AFGCL (2019), CoQuiAAS (ICCMA 2019) *(p.4)*
- On DC-CO, DS-PR-CO, DS-ST, SE-CO, DC-ST: µ-toksia solves all instances; other solvers time out on some *(p.4)*
- Argmat-sat solves more instances than µ-toksia on DS-PR (316 vs 312) — the one case where µ-toksia is not best *(p.4)*
- All solvers are essentially on par for SE-ST, EE-ST, SE-PR, and EE-PR *(p.4)*
- IL (ideal semantics) is particularly very close to the performance of the virtual best solver (VBS) *(p.4)*
- CryptoMiniSAT is used and makes the largest contribution to VBS on all tasks not on SE-ST *(p.4)*
- OS-DFS-argued reported incorrectly "365" on 128 as max, and some solvers crashed on specific instances *(p.4)*
- ON DS-ST:argol 2019 is also excluded due to noticeable numbers of incorrect answers across the datasets *(p.4)*

### Table 1 Results (p.3)
Number of solved instances, number of times contributed to VBS, cumulative time over solved instances for all solvers:

| Solver | DC-CO solved | DS-PR-CO solved | DS-ST solved | Notes |
|--------|-------------|----------------|-------------|-------|
| µ-toksia | All | All | All | Best or near-best on most tasks |
| Argmat-sat | Most | 316 (best DS-PR) | Most | Better on DS-PR |
| AFGCL | Some timeouts | Some timeouts | Some timeouts | |
| Aspartix | Some timeouts | Some timeouts | Some timeouts | |
| CoQuiAAS | Most | Most | Most | |

## Limitations
- On DS-PR, Argmat-sat solves slightly more instances (316 vs 312) *(p.4)*
- The ICCMA 2019 main track benchmarks were very easy for declarative approaches, making differentiation difficult *(p.4)*
- The paper focuses on the ICCMA benchmark instances; real-world argumentation graphs may differ *(p.4)*

## Arguments Against Prior Work
- µ-toksia scales noticeably better on dynamic track tasks than its current competitors *(p.1)*
- Prior systems (Argmat-sat, Aspartix, AFGCL, CoQuiAAS) have timeouts on tasks that µ-toksia solves completely *(p.4)*
- OS-DFS-argol has noticeable numbers of incorrect answers and was excluded from comparison *(p.4)*

## Design Rationale
- SAT-based approach chosen because SAT solvers are mature and highly optimized *(p.1)*
- Iterative SAT solving with persistent solver state avoids re-encoding overhead *(p.3)*
- Unit propagation for grounded semantics avoids unnecessary SAT overhead for polynomial-time tasks *(p.2)*
- CaDiCaL chosen as default SAT solver due to competition performance *(p.3)*
- Assumptions mechanism used for incremental solving (avoiding clause database rebuild) *(p.2)*

## Testable Properties
- Grounded extension can be computed by iterative unit propagation in polynomial time *(p.2)*
- Every stable extension is a complete extension: if stable exists, it is also preferred and semi-stable *(p.2)*
- Conflict-free encoding: for every attack $(a,b) \in R$, at most one of $x_a, x_b$ can be true *(p.2)*
- Admissible sets must be conflict-free and defend all their members *(p.2)*
- Complete extension: admissible plus includes all arguments it defends *(p.2)*
- Grounded extension = intersection of all complete extensions *(p.2)*
- The ideal extension is the unique maximal admissible set contained in every preferred extension *(p.2)*

## Relevance to Project
Directly relevant as a practical implementation reference for computing Dung-style argumentation semantics. The SAT encodings (Figure 1) provide concrete formulas for implementing credulous/skeptical acceptance and extension enumeration. The system architecture — persistent SAT solver with iterative calls — is a proven approach for the propstore's argumentation reasoning needs. Complements the theoretical paper by Dung (1995) already in the collection with implementation-level details and the SAT encoding paper by Mahmood (2025).

## Open Questions
- [ ] How does µ-toksia handle very large sparse vs dense argumentation graphs?
- [ ] What is the practical overhead of the dynamic AF support vs rebuilding from scratch?
- [ ] How does the CaDiCaL solver compare to z3 for these specific encoding patterns?

## Related Work Worth Reading
- Cerutti, Giacomin, and Vallati 2019: Argumentation reasoning via SAT (algorithm framework) *(p.1)*
- Alviano 2019: Aggregation reasoning via stable models (ASP-based alternative) *(p.1)*
- Niskanen and Järvisalo 2020 (extended): More details on dynamic track algorithms *(p.2)*
- Audemard and Simon 2018: Glucose SAT solver *(p.3)*

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — cited as [20]; µ-toksia implements SAT-based computation of all Dung semantics (complete, preferred, stable, semi-stable, stage, grounded, ideal). Dung defines the semantics; µ-toksia provides practical algorithms to compute them.

### New Leads (Not Yet in Collection)
- Cerutti, Giacomin, and Vallati (2019) — "How we designed winning planning-based argumentation solvers" — algorithmic framework underlying ITEGAR approach.
- Wallner, Weissenbacher, and Woltran (2013) — "Advanced SAT techniques for abstract argumentation" — SAT techniques that µ-toksia builds upon.
- Dvořák, Järvisalo, Wallner, Woltran (2014) — "Complexity-sensitive decision procedures for abstract argumentation" — theoretical foundation for per-semantics algorithm selection.

### Now in Collection (previously listed as leads)
- [[Charwat_2015_MethodsSolvingReasoningProblems]] — Comprehensive survey of SAT, ASP, CSP, labelling, dialogue game, and dynamic programming approaches for solving reasoning problems in abstract argumentation. Provides the landscape of solver methods that mu-toksia's SAT-based approach builds upon and advances.

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- [[Mahmood_2025_Structure-AwareEncodingsArgumentationProperties]] — cited as [38]; references µ-toksia as a practical ICCMA competition winner implementing SAT-based extension computation, contrasting its direct encoding approach with Mahmood's decomposition-guided structural encodings.

### Conceptual Links (not citation-based)
- **SAT-based argumentation computation:**
  - [[Mahmood_2025_Structure-AwareEncodingsArgumentationProperties]] — **Strong.** Both provide SAT encodings for computing Dung semantics. µ-toksia uses direct encodings with iterative solving for practical performance; Mahmood provides structure-aware encodings exploiting clique-width for theoretical tractability guarantees. Different approaches to the same computational problem.
  - [[Dung_1995_AcceptabilityArguments]] — **Strong.** µ-toksia is a direct implementation of Dung's theoretical framework. The SAT encodings in Figure 1 are formal translations of Dung's semantic definitions into propositional satisfiability.
- **Argumentation reasoning systems:**
  - [[Odekerken_2023_ArgumentationReasoningASPICIncompleteInformation]] — **Moderate.** Odekerken uses ASP (Clingo) for computing argumentation semantics under incomplete information; µ-toksia uses SAT for standard/dynamic AFs. SAT vs ASP represents the main solver paradigm divide in computational argumentation.
- **Encoding theory:**
  - [[Tang_2025_EncodingArgumentationFrameworksPropositional]] — **Strong.** Tang provides the theoretical foundation showing that encoding AF semantics into propositional logic systems, and choosing different logics (2-valued, 3-valued Kleene/Lukasiewicz, fuzzy), yields different semantics from the same formula structure. mu-toksia's 2-valued SAT encodings are the computational instantiation; Tang explains why they capture stable/complete semantics and how alternative logics could yield different or graded semantics.
- **Competition evaluation:**
  - [[Järvisalo_2025_ICCMA20235thInternational]] — **Strong.** ICCMA 2023 competition by the same authors (Järvisalo, Niskanen). mu-toksia (static and dynamic variants) competed in the Dynamic track, placing 2nd and 3rd behind CRUSTABRI. The competition provides empirical benchmarking context for mu-toksia's performance relative to other solver approaches.
