---
title: "ICCMA 2023: 5th International Competition on Computational Models of Argumentation"
authors: "Matti Järvisalo, Tuomo Lehtonen, Andreas Niskanen"
year: 2025
venue: "Artificial Intelligence"
doi_url: "https://doi.org/10.1016/j.artint.2025.104311"
---

# ICCMA 2023: 5th International Competition on Computational Models of Argumentation

## One-Sentence Summary
This paper provides a comprehensive overview of the 5th ICCMA competition (2023), documenting the argumentation formalisms (AF and ABA), competition tracks, benchmark generation, solver implementations, and empirical results that establish the state of the art in computational argumentation solvers.

## Problem Addressed
The study of computational argumentation requires practical solver implementations, but there is no standardized way to evaluate and compare these solvers. ICCMA provides a recurring competition framework that drives development of efficient algorithms for reasoning over abstract argumentation frameworks (AFs) and assumption-based argumentation (ABA) frameworks. *(p.1)*

## Key Contributions
- First inclusion of assumption-based argumentation (ABA) as a competition track alongside abstract argumentation frameworks (AFs) *(p.1)*
- Introduction of a new compact input format (ICCMA23 format) replacing the older trivial graph format (TGF) and APX format *(p.1)*
- Addition of a "no-limits" track allowing solvers to use multiple CPU cores and arbitrary memory *(p.5)*
- New ICCMA23 benchmark AF generators and updated benchmark methodology *(p.12)*
- Comprehensive empirical analysis of 14 AF solvers and 5 ABA solvers across multiple semantics and reasoning tasks *(p.13-18)*
- Detailed analysis of solver performance including PAR-2 scoring, runtime distributions, and correlation analysis *(p.19-24)*

## Methodology

### Argumentation Formalisms

**Abstract Argumentation Framework (AF):** An AF is a pair F = (A, R) where A is a set of arguments and R ⊆ A × A is an attack relation. *(p.2)*

**Semantics covered:** Complete (CO), Preferred (PR), Stable (ST), Semi-stable (SST), Stage (STG), Ideal (ID) *(p.2-3)*

**Reasoning tasks for AFs:** *(p.3)*
- DC (credulous acceptance): Is a given argument credulously accepted under σ-semantics?
- DS (skeptical acceptance): Is a given argument skeptically accepted under σ-semantics?
- SE (single extension): Compute one σ-extension
- EE (extension enumeration): Enumerate all σ-extensions

**Assumption-Based Argumentation (ABA):** An ABA framework is a tuple F = (L, R, A, ‾) where L is a language, R is a set of rules, A ⊆ L is a set of assumptions, and ‾ : A → L is a contrariness function mapping each assumption to its contrary. *(p.3)*

**ABA semantics:** Conflict-free, admissible, complete, preferred, stable, grounded, ideal *(p.4)*

**ABA reasoning tasks:** Same as AF (DC, DS, SE, EE) but applied to assumption sets rather than argument sets *(p.4)*

### Competition Tracks *(p.5)*

1. **Main track:** Core AF reasoning problems (DC-CO, DC-ST, DC-SST, DC-STG, DC-ID, DS-CO, DS-ST, DS-SST, DS-STG, SE-CO, SE-ST, SE-SST, SE-STG, SE-PR, SE-ID) *(p.5)*
2. **No-limits track:** Same subtracks as Main but allowing parallel/multi-core computation *(p.5)*
3. **Approximate track:** DC and DS subtracks only, focused on approximate solvers *(p.5)*
4. **Dynamic track:** AF reasoning with incremental changes (additions/deletions of arguments and attacks) *(p.5)*
5. **ABA track:** Assumption-based argumentation reasoning *(p.5)*

### Solver Correctness Verification *(p.6-7)*

Fuzz testing procedure:
1. Generate random AFs with |A| = {4, 8} arguments, edge probability 0.02-0.5 *(p.7)*
2. For each AF, 100 iterations of random testing *(p.7)*
3. For acceptance tasks (DC/DS), check by intersection of all extensions *(p.7)*
4. For extension tasks (SE/EE), verify subset/superset checking, conflict-freeness, and semantic-specific properties *(p.7)*
5. VBS (virtual best solver) used as reference for cross-validation *(p.7)*

### I/O Format: ICCMA23 Format *(p.8-9)*

**AF input format:**
- First line: `p af <n>` where n is the number of arguments
- Arguments are consecutively numbered 1 to n
- Attacks specified as `<attacker> <target>` on separate lines *(p.8)*

**ABA input format:**
- First line: `p aba <n>` where n is the number of atoms
- Lines starting with `a` declare assumptions
- Lines starting with `c` declare contraries (e.g., `c 1 6` means contrary of atom 1 is atom 6)
- Lines starting with `r` declare rules (e.g., `r 4 5 1` means rule with head 4 and body {5, 1}) *(p.9-10)*

**Output formats:** *(p.10)*
- DC: "YES" + witness extension, or "NO"
- DS: "NO" + counterexample extension, or "YES"
- SE: extension on `w` line, or "NO" if none exists
- EE: multiple extensions, each on `w` line

### Dynamic Track API (IPAAF) *(p.11)*

IPAAF (Incremental/Proactive API for Abstract Argumentation Frameworks) provides:
- `ipaaf_init_solver()` - initialize solver
- `ipaaf_add_argument(a)` - add argument a
- `ipaaf_del_argument(a)` - delete argument a
- `ipaaf_add_attack(a,b)` - add attack (a,b)
- `ipaaf_del_attack(a,b)` - delete attack (a,b)
- `ipaaf_assume(a)` - set assumption on argument a
- `ipaaf_query(a)` - query acceptance of argument a

Two modes: credulous (DC) and skeptical (DS), returning 0/1/20/10 for acceptance/rejection/undecided/error *(p.11)*

### Hardware and Runtime *(p.7-8)*

- Cluster at University of Helsinki, Finland *(p.7)*
- Benchmark homogeneous specifications: 2.60 GHz Intel Xeon E5-2670 (8 cores), 64 GB RAM *(p.7)*
- Main/Approximate track time limit: 600 seconds per instance *(p.7)*
- No-limits track time limit: 1200 seconds with clock-wall time *(p.7)*
- Single core for Main track; multiple cores allowed for No-limits *(p.5)*
- Resource limits enforced via runsolver *(p.7)*

## Key Equations

No novel equations introduced. The paper uses standard definitions from Dung's AF theory:

$$
F^+(S) = \{a \in A \mid S \text{ attacks } a\}
$$
Where: F is the AF, S is a set of arguments, F^+(S) is the set of arguments attacked by S
*(p.2)*

$$
F^-(S) = \{a \in A \mid a \text{ attacks some } b \in S\}
$$
Where: F^-(S) is the set of arguments that attack S
*(p.2)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| Number of arguments | \|A\| | count | - | 301-89425 (benchmarks) | 27 | Benchmark AF sizes |
| Number of attacks | \|R\| | count | - | 816-21800790 (benchmarks) | 27 | Benchmark attack counts |
| Time limit (Main) | - | seconds | 600 | - | 7 | Per-instance timeout |
| Time limit (No-limits) | - | seconds | 1200 | - | 7 | Per-instance wall-clock timeout |
| Fuzz test AF size | \|A\| | count | 4,8 | {4, 8} | 7 | For correctness testing |
| Edge probability (fuzz) | - | - | - | 0.02-0.5 | 7 | For random AF generation |
| Fuzz iterations per AF | - | count | 100 | - | 7 | Testing iterations |
| PAR-2 penalty | - | seconds | 1200 | - | 16 | 2x time limit for unsolved instances |
| Benchmark instances per subtrack | - | count | 326-350 | - | 12 | Main track benchmarks |

## Implementation Details

### Benchmark Generators *(p.12-13)*

- **AFBenchGen2:** Random graph model, parameter-controlled density *(p.12)*
- **GroundedGenerator:** Generates AFs with large grounded extensions *(p.12)*
- **KwtGenerator:** Generates AFs with many strongly connected components *(p.12)*
- **StableGenerator:** Generates AFs with many stable extensions (and bonus: many preferred and complete extensions) *(p.12)*
- **Barabasi-Albert:** AFs generated using AFGenSel according to Barabasi-Albert graph model *(p.12)*
- **Traffic:** AFs from real-world traffic scenarios *(p.12)*
- **Water-transport:** AFs generated using AFGenSel according to Watts-Strogatz graph model *(p.12)*
- **ICCMA 2015/2017 benchmarks:** Reused from previous competitions *(p.12)*
- **ABA benchmarks:** Generated via translation from AFs (ABA3SAT generator) *(p.13)*

### Participating Solvers - Main/No-limits Track *(p.13-15)*

| Solver | Language | Approach | Tracks |
|--------|----------|----------|--------|
| AFGCNv2 | Python | Graph neural networks (GCN) | Main, Approx |
| ARIPOTER (degrees/hcat) | Java/Python | SAT-based | Main, No-limits, Approx |
| ASPARTIX-DL | Prolog/Python | ASP (clingo) | Main, ABA |
| ASPFORABA | Python | ASP (clingo) | ABA |
| ASTRA | - | ASP | ABA |
| CRUSTABRI | Rust | Labeling-based | Dynamic, ABA |
| FARGO-LIMITED | C++ | SAT-based (CaDiCaL) | Main, No-limits, Approx |
| FLEXABLE | - | - | ABA |
| HARPER++ | C++ | SAT-based | Main, No-limits, Approx |
| mu-TOKSIA (static/dynamic) | Python/C++ | SAT-based (Kissat/CaDiCaL) | Main, No-limits, Dynamic |
| kappa-SOLUTIONS | - | SAT-based | Dynamic |
| AFGCN-HCAT | Python | Hybrid GNN + SAT | Main |
| FUDGE | Python | GNN | Main |
| PORTSAT | Python | SAT-based | Main |

### Key Results - Main Track *(p.16)*

Top performers by subtrack:
- **DC tasks:** FARGO-LIMITED and HARPER++ dominated, with HARPER++ best on DC-CO, DC-STG, and DC-ID *(p.16)*
- **DS tasks:** HARPER++ ranked first in most DS subtracks *(p.16)*
- **SE tasks:** HARPER++ dominated SE-CO, SE-PR, SE-ST, SE-SST, SE-STG; FARGO-LIMITED best on SE-ID *(p.16)*
- **Overall:** HARPER++ achieved first place in 10 of 15 subtracks; FARGO-LIMITED won 4 subtracks *(p.16)*

### Key Results - Approximate Track *(p.17)*

- HARPER++ ranked first in DC-PR and most DS subtracks *(p.17)*
- FARGO-LIMITED ranked first in DC-CO, DC-ID, DC-SST, DC-STG *(p.17)*
- The approximate track had lower participation than Main track *(p.17)*

### Key Results - Dynamic Track *(p.18)*

- CRUSTABRI dominated all Dynamic track subtracks (DC-CO, DC-ST, DS-ST) *(p.18)*
- mu-TOKSIA variants placed second and third *(p.18)*

### Key Results - ABA Track *(p.18-19)*

- ASPFORABA dominated, ranking first in DC-CO, DC-ST, DS-PR, DS-ST, SE-PR, SE-ST *(p.19)*
- ACBAR placed second in most subtracks *(p.19)*
- CRUSTABRI was disqualified from ABA track due to erroneous output *(p.19)*

## Figures of Interest
- **Fig 1 (p.2):** Example abstract argumentation framework with 5 arguments
- **Fig 2 (p.11):** Functions declared in the IPAAF header for Dynamic track API
- **Fig 3 (p.16):** Main and No-limits track PAR-2 scores bar chart showing solver performance
- **Fig 4 (p.17):** Approximate track number of solved instances
- **Fig 5 (p.18):** Dynamic track PAR-2 scores
- **Fig 6 (p.19):** ABA track PAR-2 scores
- **Fig 7 (p.21):** Number of instances solved by each solver under given time limits (cactus plots)
- **Fig 8 (p.22):** Pairwise Pearson correlation coefficient of solver runtimes in Main track
- **Fig A.9 (p.26):** Runtime distribution plots for all subtracks
- **Fig A.10 (p.28):** Pairwise correlation heatmaps for additional subtracks

## Results Summary

### Overall Competition Findings *(p.16-25)*

- SAT-based approaches dominate abstract argumentation solving, with HARPER++ and FARGO-LIMITED as clear leaders *(p.16)*
- GNN-based approaches (AFGCNv2, FUDGE) are competitive for approximate reasoning but lag behind SAT-based solvers for exact computation *(p.17)*
- For Dynamic track, specialized incremental solvers (CRUSTABRI) significantly outperform static solvers *(p.18)*
- ABA solving is less mature; ASP-based approaches (ASPFORABA, ASPARTIX-DL) dominate *(p.19)*
- The YES/NO distribution across benchmarks is fairly balanced except DS-ST (heavily YES-biased, ~96% YES in Main track) *(p.19-20)*
- VBS (virtual best solver) analysis shows significant room for improvement via portfolio approaches *(p.20)*
- Solver runtimes are quite correlated within tracks but less so across different semantics *(p.21-22)*
- Benchmark parameter analysis shows number of atoms is the primary scaling parameter *(p.23)*

### Solver Correctness Issues *(p.7, 11-12)*

- Fuzz testing found issues in several solvers during evaluation *(p.7)*
- CRUSTABRI produced erroneous output in ABA track, leading to disqualification *(p.19)*
- Some solvers did not properly implement all subtracks *(p.7)*

## Limitations
- Benchmark AFs are synthetically generated and may not represent real-world argumentation scenarios *(p.25)*
- The ABA track benchmarks were generated from AF translations, not from natural ABA problems *(p.13)*
- Dynamic track had only 4 participating solvers *(p.18)*
- No structured argumentation formalisms (ASPIC+, Deductive) were included as competition tracks *(p.24)*
- The competition does not test solver scalability beyond the specific benchmark sizes used *(p.23)*

## Arguments Against Prior Work
- Prior ICCMA competitions used TGF and APX formats which were verbose and lacked compact representation; the new ICCMA23 format addresses this *(p.8)*
- Previous competitions did not include ABA, limiting scope to abstract argumentation only *(p.1, 24)*
- Earlier Dynamic track implementations used file-based I/O rather than an API, making incremental solving artificially harder *(p.11)*

## Design Rationale
- The ICCMA23 format was designed to be more compact while remaining human-readable, using integer-indexed arguments rather than string names *(p.8)*
- The no-limits track was added to investigate whether parallel computation provides significant speedups for argumentation solving *(p.5)*
- Fuzz testing was chosen over formal verification for solver correctness due to the difficulty of producing verified reference implementations for all semantics *(p.7)*
- Multiple benchmark generators were used to ensure diverse problem characteristics *(p.12)*

## Testable Properties
- For any AF, the grounded extension is always a subset of every complete extension *(p.2)*
- Every stable extension is also a preferred extension, but not vice versa *(p.3)*
- For every semi-stable extension, any preferred extension that is not semi-stable has a strictly smaller range *(p.3)*
- If a stable extension exists, the semi-stable extensions equal the stable extensions *(p.3)*
- The ideal extension is always unique and is a subset of every preferred extension *(p.3)*
- DC-CO is equivalent to DC-PR (credulous acceptance under complete = credulous acceptance under preferred) *(p.3)*
- DS-CO is equivalent to DS-GR (skeptical acceptance under complete = membership in grounded extension) *(p.3)*
- In the Dynamic track, CRUSTABRI achieves PAR-2 scores roughly half those of the next-best solver *(p.18)*

## Relevance to Project
This paper is directly relevant to the propstore project's focus on computational argumentation. It documents:
- The state of the art in AF and ABA solver implementations
- Standard I/O formats for argumentation problems (ICCMA23 format)
- Benchmark generation methodologies for testing argumentation solvers
- The relative strengths of SAT-based vs. ASP-based vs. GNN-based approaches
- Performance baselines for credulous/skeptical acceptance and extension computation tasks

## Open Questions
- [ ] How do structured argumentation formalisms (ASPIC+) compare computationally to abstract AFs?
- [ ] Can GNN-based approaches be made competitive with SAT-based solvers for exact reasoning?
- [ ] What benchmark characteristics best discriminate between solver approaches?
- [ ] How would real-world argumentation problems (from law, medicine, debate) perform compared to synthetic benchmarks?

## Related Work Worth Reading
- Dung 1995: The foundational paper on abstract argumentation frameworks [already in collection]
- Bondarenko et al. 1997: Assumption-based argumentation framework (ABA) foundations [26]
- Thimm & Villata 2017: First ICCMA competition paper [137]
- Lagniez et al. 2022: CoQuiAAS v2 solver system description [97]
- Niskanen & Järvisalo 2020: mu-toksia solver [119] -> NOW IN COLLECTION: [[Niskanen_2020_ToksiaEfficientAbstractArgumentation]]
- Dvořák et al. 2024: ASPARTIX system [55]
- Hecking et al. 2023: FARGO solver [80]

## Collection Cross-References

### Already in Collection
- [[Dung_1995_AcceptabilityArguments]] — Foundational paper defining AFs and the semantics (admissible, preferred, stable, grounded, complete) that ICCMA competition tasks are based on
- [[Modgil_2014_ASPICFrameworkStructuredArgumentation]] — ASPIC+ framework; ICCMA 2023 recommends future tracks for structured argumentation formalisms like ASPIC+
- [[Modgil_2018_GeneralAccountArgumentationPreferences]] — Full technical treatment of ASPIC+; relevant to future ICCMA structured argumentation tracks
- [[Odekerken_2023_ArgumentationReasoningASPICIncompleteInformation]] — ASP-based ASPIC+ reasoning with incomplete information; uses similar ASP technology (Clingo) as ABA track solvers ASPFORABA and ASPARTIX-DL
- [[Niskanen_2020_ToksiaEfficientAbstractArgumentation]] — mu-toksia solver by Niskanen and Järvisalo; competed in ICCMA 2023 Dynamic track (mu-toksia static and dynamic variants)
- [[Cayrol_2005_AcceptabilityArgumentsBipolarArgumentation]] — Bipolar AFs with support relations; ICCMA only covers attack-based AFs, bipolar could be a future track

### Now in Collection (previously listed as leads)
- [[Niskanen_2020_ToksiaEfficientAbstractArgumentation]] — mu-toksia SAT-based solver for abstract argumentation, competed in ICCMA 2023 Dynamic track placing 2nd/3rd

### New Leads (Not Yet in Collection)
- Bondarenko et al. (1997) — "An abstract, argumentation-theoretic approach to default reasoning" — foundational ABA paper needed for understanding the ABA track formalism
- Thimm & Villata (2017) — Previous ICCMA competition overview (ICCMA 2017), provides historical comparison
- Lagniez et al. (2022) — CoQuiAAS v2 solver system, relevant SAT-based approach

### Supersedes or Recontextualizes
- (none — this is a competition overview, not a revision of prior theoretical work)

### Conceptual Links (not citation-based)
- **Computational complexity of argumentation:**
  - [[Mahmood_2025_Structure-AwareEncodingsArgumentationProperties]] — Provides the theoretical SAT/QSAT encodings and complexity bounds that underpin the SAT-based solvers (HARPER++, FARGO-LIMITED, mu-toksia) dominating ICCMA 2023. The competition results empirically validate that SAT-based approaches are practical for the semantics Mahmood encodes.
  - [[Dvorak_2012_FixedParameterTractableAlgorithmsAbstractArgumentation]] — FPT algorithms for abstract argumentation; ICCMA benchmarks could test whether FPT approaches are competitive with SAT-based solvers on structured instances
  - [[Fichte_2021_Decomposition-GuidedReductionsArgumentationTreewidth]] — Treewidth-based decomposition reductions for argumentation; relevant to understanding why certain benchmark families are harder for different solver approaches
  - [[Tang_2025_EncodingArgumentationFrameworksPropositional]] — Propositional encodings of AFs; directly related to the SAT-based solver technology that dominates ICCMA 2023
- **Solving methodology surveys:**
  - [[Charwat_2015_MethodsSolvingReasoningProblems]] — Survey of methods for solving argumentation reasoning problems; provides the theoretical landscape that ICCMA 2023 empirically evaluates
- **Argumentation formalism evaluation:**
  - [[Caminada_2007_EvaluationArgumentationFormalisms]] — Evaluation of argumentation formalisms; complements ICCMA's empirical evaluation with theoretical formalism comparison
  - [[Prakken_2010_AbstractFrameworkArgumentationStructured]] — Abstract framework for structured argumentation; relevant to ICCMA's recommendation for future structured argumentation tracks

### Cited By (in Collection)
- (none found)
