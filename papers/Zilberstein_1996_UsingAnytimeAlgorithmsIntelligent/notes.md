---
title: "Using Anytime Algorithms in Intelligent Systems"
authors: "Shlomo Zilberstein"
year: 1996
venue: "AI Magazine 17(3):73-83"
doi_url: "https://doi.org/10.1609/aimag.v17i3.1232"
pages: "73-83"
affiliation: "University of Massachusetts at Amherst"
funding: "NSF grant IRI-9409827; Rome Laboratory, USAF, grant F30602-95-1-0012"
---

# Using Anytime Algorithms in Intelligent Systems

## One-Sentence Summary
Survey of metalevel control for systems built from anytime algorithms: defines quality metrics and desired properties, performance profiles (PP, conditional PP, dynamic PP), interruptible vs contract algorithms, offline compilation of composite systems (NP-complete in general; local compilation linear and optimal under stated assumptions), and three run-time monitoring strategies (fixed contract, marginal value of computation, Markov-process monitoring policies) with their optimality theorems. *(pp.73-82)*

## Problem Addressed
In domains such as signal interpretation, real-time diagnosis and repair, and mobile robot control, computing the optimal answer is computationally infeasible or economically undesirable, and the appropriate amount of deliberation depends on the situation. Systems composed of several anytime algorithms raise control problems: how to allocate time to components and when to stop, under uncertainty about both the algorithms' performance and the environment. *(p.73)*

## Key Contributions
- Taxonomy of quality metrics: certainty, accuracy, specificity *(p.74)*
- Seven desired properties of anytime algorithms from the metalevel-control standpoint *(p.74)*
- Definitions 1-3: PP Q(t), conditional PP Pr(q_out | q_in, t), dynamic PP Pr(q_j | q_i, Delta t) *(pp.75, 77)*
- Interruptible vs contract distinction and the constant-penalty contract-to-interruptible construction *(p.77)*
- The anytime algorithm composition problem, compilation, its complexity (Theorem 1) and local compilation (Theorems 2, 3) *(pp.78-79)*
- Monitoring: fixed-contract approach (Definition 4, Theorem 4), marginal value of computation (Theorem 5), Markov-model monitoring policies (Table 1) *(pp.80-82)*

## Methodology
Survey/position article summarizing the author's dissertation (Zilberstein 1993) and related work; illustrative experiment with randomized tour improvement for TSP to build a quality map and expected PP. Theorems are stated with citations to where they are proved, not proved here. *(pp.73-82)*

## Definitions and Concepts

**Anytime algorithm.** Algorithms "whose quality of results improves gradually as computation time increases." Term coined by Dean and Boddy in the mid-1980s for time-dependent planning; related notions are Horvitz's flexible computation, limited rationality (Russell and Wefald; Doyle; D'Ambrosio), and imprecise computation (Liu et al. 1991). *(p.73)* Anytime computation extends a computational procedure by allowing it to return many possible approximate answers to any given input; the binary notion of correctness is replaced by a multivalued quality measure associated with each answer. Related to approximate processing (Lesser, Pavlin, Durfee 1988) and satisficing (Simon 1982). *(p.73)*

**Quality metrics** (different anytime algorithms approach the exact result in different ways, so a single quality measure is not used): *(p.74)*
1. *Certainty* — degree of certainty that the result is correct; expressible as probabilities, fuzzy set membership, or other approaches.
2. *Accuracy* — how close the approximate result is to the exact answer; typically high quality guarantees error below an upper bound.
3. *Specificity* — level of detail of the result; the algorithm always produces correct results but detail increases over time.

**Desired properties** (from the standpoint of metalevel control): *(p.74)*
1. *Measurable quality* — quality of an approximate result can be determined precisely (e.g., distance to the correct result, measurable when the correct result can be determined).
2. *Recognizable quality* — quality can easily be determined at run time, within constant time. In combinatorial optimization (e.g., path planning), quality may be measurable but not recognizable.
3. *Monotonicity* — quality is a nondecreasing function of time and input quality. When quality is recognizable, monotonicity can be guaranteed by returning the best result so far rather than the last.
4. *Consistency* — quality correlated with computation time and input quality; algorithms generally do not guarantee deterministic output quality for given time, but narrow variance is important for quality prediction.
5. *Diminishing returns* — improvement larger at early stages, diminishing over time.
6. *Interruptibility* — can be stopped at any time and provide some answer. Originally the primary characteristic; noninterruptible contract algorithms are also useful.
7. *Preemptability* — can be suspended and resumed with minimal overhead.
These properties have a major effect on composition and monitoring complexity and are summarized by the PP. *(p.74)*

**Example programming techniques producing anytime algorithms:** iterative deepening search, variable precision logic, randomized techniques such as Monte Carlo and fingerprinting algorithms (survey in Zilberstein 1993). Not every algorithm producing a series of approximate answers is well-behaved. *(p.74)*

**Definition 1.** A PP of an anytime algorithm, Q(t), denotes the expected output quality with execution time t. *(p.75)* (Boddy and Dean 1989 used PPs for an anytime path planner; Horvitz 1987 used a similar construct for the object-related value of flexible computation.)

**Quality map.** Raw data of the particular quality of results generated at particular times over many input instances; PPs are typically built empirically from it. *(p.75)*

**Definition 2.** A CPP of an anytime algorithm, Pr(q_out | q_in, t), denotes the probability of getting a solution of quality q_out when the algorithm is activated with input of quality q_in and execution time t. (Printed text on p.75 literally reads "with input of quality q_out", an evident typo for q_in given the notation.) CPPs extend PPs in two ways: dependence on input quality as well as run time, and a probability distribution of output quality rather than an expected value. *(p.75)*

**Statistical performance profile** (Pos 1993): records upper and lower bounds and expected output quality for any time allocation. *(p.77)*

**Definition 3.** A dynamic performance profile (DPP), Pr(q_j | q_i, Delta t), denotes the probability of getting a solution of quality q_j by resuming the algorithm for time interval Delta t when the currently available solution has quality q_i. Motivation: quality improvement is better predicted at run time when the current result's quality is taken into account; behavior modeled as a Markov process whose discrete states are output qualities; quality at t+1 depends on quality at t and current time; constructed empirically (Hansen and Zilberstein 1996). *(p.77)*

**Representing PPs.** PPs are typically monotone in time and approximated by a function family via curve fitting; CPPs by a family of distributions, or by a table representing a discrete probability distribution whose size is a system parameter controlling accuracy. *(p.77)*

**Interruptible vs contract algorithms** (Russell and Zilberstein 1991). An interruptible algorithm can be interrupted at any time to produce results whose quality is described by its PP. A contract algorithm offers a similar trade-off but the total allocation must be known in advance; if interrupted before the contract time it might not yield useful results. Interruptible algorithms are often more appropriate but harder to construct. A simple, general construction produces an interruptible version of any contract algorithm with only a small, constant penalty; this lets one build contract algorithms for complex tasks and convert them. For many applications contract algorithms are the desired end product. *(p.77)*

**Anytime algorithm composition problem.** How much time to allocate to each component of a modular system to maximize output quality of the complete system (Zilberstein 1993); a large part can be solved offline by analyzing component PPs. *(p.78)*

**Definition 4.** A domain is said to have predictable utility if the utility of a result can be determined for any future time once the current state of the domain is known. The domain state may change (even unpredictably) while utility is predictable. *(p.80)*

**Marginal value of computation.** The expected utility gain as a result of an additional computation step (Russell and Wefald 1989). The monitor computes the difference between expected utility after one time increment (accounting for quality improvement and environment change) and current expected utility; deliberation is interrupted once this becomes negative (myopic). *(pp.81)*

## Key Equations

$$
Cost(c,f) + Cost(d,a) < Cost(c,d) + Cost(f,a)
$$
Where: (1), the tour-improvement condition for exchanging edges (c,d) and (f,a) in a TSP tour; Cost(i,j) is the cost of traveling directly from city i to city j. *(p.75)*

$$
Q(t) = 1 - e^{-\lambda t}
$$
Where: function family used by Boddy and Dean (1989) to model the expected performance of their anytime planner; lambda is a rate parameter. *(p.77)*

$$
Q(t) = E[\text{quality} \mid t]
$$
Where: Definition 1, expected output quality at execution time t. *(p.75)*

$$
\Pr(q_{out} \mid q_{in}, t)
$$
Where: Definition 2, conditional performance profile. *(p.75)*

$$
\Pr(q_j \mid q_i, \Delta t)
$$
Where: Definition 3, dynamic performance profile. *(p.77)*

## Parameters

| Name | Symbol | Units | Default | Range | Page | Notes |
|------|--------|-------|---------|-------|------|-------|
| TSP instance size in quality-map experiment | n | cities | 50 | - | 75 | Randomly generated inputs |
| Edges exchanged per tour-improvement step | r | edges | 2 | general r | 74-75 | Example exchanges 2 edges |
| Quality (TSP) | q | fraction | - | 0.00-~0.58 (Fig. 2) | 75-76 | Percent tour-length reduction vs initial tour |
| Run time axis (Fig. 2) | t | (unlabeled time units) | - | 0-~3.3 | 76 | Quality map |
| Expected PP quality at t=2.5 (Fig. 3) | Q(2.5) | fraction | ~0.48 | - | 77 | Read from figure |
| Boddy-Dean PP rate | lambda | 1/time | - | - | 77 | Q(t)=1-e^{-lambda t} |
| CPP table size | - | entries | - | system parameter | 77 | Controls accuracy of performance info |
| Total time allocation | B | time | - | - | 78 | Compilation decision problem |
| Quality threshold | K | quality | - | - | 78 | Compilation decision problem |

## Algorithms

### Randomized tour improvement (TSP) *(pp.74-75)*
1. Start with a random tour (random ordering of the cities).
2. Repeatedly select r edges (example: two random edges (c,d) and (f,a)) and exchange them for r edges not in the solution, as long as the result remains a tour.
3. Accept if the new tour's cost is lower than the previous (condition (1) in the 2-edge case). Example: tour a,b,c,d,e,f becomes a,b,c,f,e,d (Fig. 1).
Naturally yields an interruptible anytime algorithm (Lawler et al. 1987).

### Compilation *(p.78)*
Offline (Zilberstein and Russell 1996; Zilberstein 1993): given a system composed of anytime algorithms, (1) determine the optimal PP of the complete system and (2) prepare additional control information to simplify run-time monitoring. Its solution and complexity depend on: composite program structure (programming operators used); type of PPs; type of anytime algorithms used as input and of the resulting system; type of run-time monitoring; quality of intermediate results (access by monitor, recognizability). *(p.78)*

**Theorem 1.** The compilation of composite expressions is NP-complete in the strong sense. Decision variant: given a composite expression, the CPPs of its components, and total allocation B, does a schedule exist yielding output quality >= K? Proof by reduction from the partially ordered knapsack problem (Zilberstein 1993). Implication: compilation limited to small programs. *(p.78)*

### Local compilation *(pp.78-79)*
Find the best PP of a module from the PPs of its immediate components; if components are not elementary, determine their PPs by local compilation recursively. Replaces the global optimization with simpler local ones. Requires:
- **Assumption 1 (tree structured):** the input expression has no repeated subexpressions, so its DAG is a tree.
- **Assumption 2 (bounded degree):** the number of inputs to each module is bounded by a small constant.
Under these and a compact tabular PP representation, local compilation is constant time per module and overall compilation is linear in program size (Zilberstein 1993). *(p.79)*

**Theorem 2** (optimality of local compilation of deterministic CPPs). Local compilation of an arbitrary composite expression with deterministic PPs is globally optimal when each PP satisfies the input monotonicity assumption (output quality of each module increases when input quality improves). *(p.79)*

**Theorem 3** (optimality of local compilation of probabilistic CPPs). Local compilation of an arbitrary composite expression with probabilistic PPs is globally optimal when each PP satisfies the input linearity assumption (output quality improves linearly with input quality) (Zilberstein 1995). Input linearity is "a stronger (and not very realistic) assumption"; piecewise linear approximation of CPPs allows local compilation with near-optimal results. *(p.79)*

### Approximate compilation *(pp.79-80)*
Tree-structured assumption excludes repeated subexpressions. Example F = E(D(B(A(x)), C(A(x)))): B and C are D's components whose allocations cannot be considered independently because both use A(x). Local compilation requires repeatedly breaking a program into subprograms with disjoint execution intervals. Approximate techniques (Zilberstein 1993): some work efficiently on DAGs with near-optimal schedules; others guarantee optimality when the number of repeated subexpressions is small; conditional statements and loops have also been analyzed. *(pp.79-80)*

### Run-time monitoring *(p.80)*
Purpose: reduce the effect of uncertainty. Two sources: internal (unpredictable system behavior -> variability in solution quality, characterized by the CPP) and external (unpredictable environment changes, characterized by the environment model). Questions studied: (1) time allocation per component to maximize utility; (2) how much performance variance justifies run-time monitoring over a fixed running time; (3) how variance and monitoring cost affect monitoring frequency; (4) what degree of approximation the monitor should use when quality is hard to compute, and how that degrades effectiveness; (5) periodic monitoring vs more frequent monitoring near expected stopping time. Three general strategies follow. *(p.80)*

**Fixed-contract approach.** Compute the best allocation before activation; usable when the complete system is compiled into a contract algorithm and variance is small. *(p.80)*
**Theorem 4** (optimality of monitoring of contract algorithms). The fixed-contract monitoring strategy is optimal when the domain has predictable utility and the system has a deterministic PP. *(p.80)*
Two modifications for near-predictable-utility domains (Zilberstein 1993): *(pp.80-81)*
- *Reallocation of residual time:* monitoring is only possible between activations of elementary contract components; executing a component transforms a computational node into an external input of known quality; based on actual quality, remaining time under the global contract is reallocated among remaining components.
- *Adjusting the contract time:* treat a finished component's output as input to a smaller residual system and recompute a new contract time for it. Related: design-to-time scheduling (Garvey and Lesser 1993).

**Marginal value of computation** (interruptible algorithms; domains whose utility function is not predictable, characterized by nondeterministic rapid change, e.g., ICU medical diagnosis, stock trading, highway vehicle control). *(p.81)*
**Theorem 5** (optimality of monitoring of interruptible algorithms). Monitoring interruptible algorithms using the value-of-computation criterion is optimal when the PP is monotonically increasing and concave down, and the cost of time is monotonically increasing and concave up (Zilberstein 1993). I.e., diminishing quality improvement and cost of delay increasing over time. *(p.81)*

**Monitoring policies** (Hansen and Zilberstein 1996). Accounts for the cost of monitoring when estimating environment state and solution quality is expensive. Model the interruptible algorithm's progress as a Markov process: states = solution qualities, transitions = quality improvement after a small time increment, with transition probabilities from the DPP. Compute an offline policy giving, for each solution quality, one of: (1) resume for a time interval then monitor again; (2) resume for a time interval then stop; (3) stop. When quality cannot be determined at run time, a similar policy based on estimated quality can be developed. *(pp.81-82)*

## Figures and Tables of Interest
- **Fig. 1 (p.75):** Tour improvement example; (a) tour a-b-c-d-e-f with edges (c,d), (f,a) marked; (b) improved tour a-b-c-f-e-d.
- **Fig. 2 (p.76):** Quality map of randomized tour improvement: scatter of (t, q) over many 50-city instances; quality rises steeply then flattens toward ~0.5-0.58 by t ~3.3.
- **Fig. 3 (p.77):** Expected PP from the quality map; concave increasing curve from 0 to ~0.48 at t=2.5.
- **Fig. 4 (p.79):** Composite speech recognizer: classify speaker (gender, accent), recognize utterance, linguistic validity (keyword, syntax, meaning).
- **Table 1 (p.82):** Optimal monitoring policy based on actual solution quality: for each quality (0-5) and time step, additional time to allocate; M marks monitoring afterward.

### Table 1 transcription *(p.82)*

| quality | start | 5 | 6 | 7 | 8 | 9 | 10 | 11 |
|---------|-------|---|---|---|---|---|----|----|
| 5 | | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 4 | | 1M | 1M | 1M | 1M | 1M | 1 | 0 |
| 3 | | 1M | 1M | 1M | 1M | 1M | 1 | 0 |
| 2 | | 3M | 3M | 3M | 3M | 2 | 1 | 0 |
| 1 | | 4M | 5 | 4 | 3 | 2 | 1 | 0 |
| 0 | 5M | 6 | 5 | 4 | 3 | 2 | 1 | 0 |

(Columns between start and time-step 5 are elided with "..." in the original.)

## Results Summary
- Fig. 2/3 illustrate that randomized tour improvement yields a well-behaved anytime algorithm with diminishing returns. *(pp.75-77)*
- Global compilation is strongly NP-complete; local compilation is linear-time and optimal under tree structure, bounded degree, and input monotonicity (deterministic) or input linearity (probabilistic). *(pp.78-79)*
- Fixed-contract monitoring optimal under predictable utility + deterministic PP; myopic value-of-computation monitoring optimal under concave PP and convex time cost. *(pp.80-81)*
- Conclusion: decision-theoretic composition and monitoring separate design of performance components from optimization of performance, mechanize composition and monitoring, and facilitate machine-independent systems that adjust resource allocation automatically. *(p.82)*

## Limitations
- Compilation is limited to small programs because of NP-completeness. *(p.78)*
- Local compilation cannot be applied to every composite expression (needs tree structure and bounded degree). *(p.79)*
- Input linearity is not very realistic. *(p.79)*
- The fixed-contract approach fails in domains with unpredictable utility. *(p.81)*
- The value-of-computation approach ignores monitoring time; justified only when computing marginal value is simple and fast. *(p.81)*
- Contract algorithms may yield no useful result if interrupted before the contract time. *(p.77)*

## Arguments Against Prior Work
- Traditional design methodologies require performance components to meet time constraints that are hard to derive at design time in complex intelligent systems, leading to hand-tuning that may not culminate in a working system. *(p.78)*
- A single unified quality measure for all anytime algorithms would simplify metalevel control, but in practice different algorithms approach the exact result in completely different ways. *(pp.73-74)*

## Design Rationale
- Anytime components avoid "commitment to a particular performance level that might fail the system"; they introduce modularity separating component development from performance optimization. *(p.78)*
- Build contract algorithms (easier) and convert to interruptible via the general construction. *(p.77)*
- CPPs over PPs: probability distributions conditioned on input quality enable better composition and monitoring. *(p.75)*
- Return best-so-far to guarantee monotonicity when quality is recognizable. *(p.74)*
- Tooling: programming environments need automatic PP construction plus composition, activation and monitoring tools; an anytime library keeps the metalevel information (Grass and Zilberstein 1996). *(p.77)*

## Testable Properties
- Monotonicity: a best-so-far anytime algorithm's reported quality is nondecreasing in time. *(p.74)*
- PPs are typically monotone functions of time; Q(t) = 1 - e^{-lambda t} is monotone increasing and concave. *(p.77)*
- Interruptible-from-contract construction costs only a small constant penalty factor. *(p.77)*
- Under Assumptions 1-2 with tabular PPs, compilation time is linear in program size. *(p.79)*
- Under predictable utility and deterministic PP, no run-time monitoring policy beats the fixed contract. *(p.80)*
- With concave-down increasing PP and concave-up increasing time cost, stopping when marginal value of computation turns negative is optimal. *(p.81)*
- In Table 1, quality 5 always gets 0 additional time, and allocations decrease to 0 by time step 11. *(p.82)*

## Relevance to Project
Directly relevant to propstore's argumentation and render layers where extension computation or solver calls may be resource-bounded: the recent "propagate computation status" / "refuse incomplete argumentation results" commits deal with exactly the interruptible-vs-complete distinction. Zilberstein's framework gives vocabulary for honest partial results: an interrupted computation returns a result with an explicitly measured or recognizable quality rather than pretending completeness, and contract vs interruptible semantics determine whether a partial result is usable at all. Performance profiles as conditional distributions also align with the "honest ignorance" discipline (calibrated rather than fabricated confidence).

## Open Questions
- [ ] The interruptible-from-contract construction and its exact penalty constant are only cited (Russell and Zilberstein 1991), not given here.
- [ ] Table 1's underlying DPP and cost model are not specified in the article.

## Related Work Worth Reading
- Zilberstein 1993, Operational Rationality through Compilation of Anytime Algorithms (PhD diss., Berkeley) — proofs of Theorems 1, 2, 4, 5.
- Zilberstein and Russell 1996, Optimal Composition of Real-Time Systems, AIJ 82(1-2) — compilation.
- Russell and Zilberstein 1991, Composing Real-Time Systems, IJCAI-91 — interruptible vs contract.
- Hansen and Zilberstein 1996, Monitoring the Progress of Anytime Problem Solving, AAAI-96 — DPP and monitoring policies.
- Zilberstein 1995, Optimizing Decision Quality with Contract Algorithms, IJCAI-95 — Theorem 3.
- Boddy and Dean 1994, Deliberation Scheduling, AIJ 67(2); Dean and Boddy 1988, AAAI-88.
- Russell and Wefald 1991, Do the Right Thing; 1989, Principles of Metareasoning.
- Horvitz 1987, 1990 — flexible computation.

## Collection Cross-References

### Already in Collection
- (none - the collection's Doyle paper is the 1979 truth maintenance system, not the cited Doyle 1990 "Rationality and Its Roles in Reasoning")

### New Leads (Not Yet in Collection)
- Russell and Zilberstein (1991) - "Composing Real-Time Systems" - interruptible vs contract algorithms and the conversion construction
- Zilberstein and Russell (1996) - "Optimal Composition of Real-Time Systems" - compilation of anytime-algorithm compositions
- Hansen and Zilberstein (1996) - "Monitoring the Progress of Anytime Problem Solving" - dynamic performance profiles and monitoring policies
- Boddy and Dean (1994) - "Deliberation Scheduling for Problem Solving in Time-Constrained Environments" - deliberation scheduling with anytime algorithms
- Russell and Wefald (1991) - "Do the Right Thing: Studies in Limited Rationality" - value of computation and metareasoning
- Horvitz (1987; 1990) - flexible computation under bounded resources
- Wallace and Freuder (1995) - "Anytime Algorithms for Constraint Satisfaction and SAT Problems" - anytime CSP/SAT
- Doyle (1990) - "Rationality and Its Roles in Reasoning" - rationality in reasoning control

### Supersedes or Recontextualizes
- (none)

### Cited By (in Collection)
- (none found)

### Conceptual Links (not citation-based)
- [Approximate Reasoning with ASPIC+ by Argument Sampling](../Thimm_2020_ApproximateReasoningASPICArgumentSampling/notes.md) - Moderate. Thimm et al.'s sampling solvers trade answer accuracy (at least 99% on their benchmarks) for runtime by building only part of the argument graph. Zilberstein's quality metrics and performance profiles are the vocabulary for characterizing such a solver as an anytime or contract algorithm; Thimm et al.'s notes record per-dataset accuracy/runtime results and list formal approximation guarantees as an open question.
