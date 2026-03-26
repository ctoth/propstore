# Gap Papers Research — Probabilistic Argumentation

Session: 2026-03-24

## Gap 2+4: PrAF Scalability and Approximation

### Paper 1: Fazzinga, Flesca & Parisi — Monte Carlo for Extension Probabilities

- **Title:** On Efficiently Estimating the Probability of Extensions in Abstract Argumentation Frameworks
- **Authors:** Bettina Fazzinga, Sergio Flesca, Francesco Parisi
- **Year:** 2013 (SUM conference), expanded 2015 (IJAR journal)
- **Conference version:** SUM 2013, Springer LNCS 8078, pp. 106–119
- **Journal version:** International Journal of Approximate Reasoning, 69, 2016, pp. 1–18
- **DOI (journal):** 10.1016/j.ijar.2015.11.006
- **URLs:**
  - https://link.springer.com/chapter/10.1007/978-3-642-40381-1_9
  - https://www.sciencedirect.com/science/article/pii/S0888613X15001760
- **Why it closes the gap:** This is the foundational paper on Monte Carlo sampling for probabilistic abstract argumentation. It proposes a sampling-based technique for estimating the probability that a set of arguments is an extension under various Dung semantics, directly addressing the #P-hardness barrier. The journal version includes convergence analysis and experimental evaluation showing significant computational savings over exact enumeration — exactly what we need for scaling PrAF to hundreds of arguments.

### Paper 2: Popescu & Wallner — Dynamic Programming on Tree-Decompositions

- **Title:** Advancing Algorithmic Approaches to Probabilistic Argumentation under the Constellation Approach
- **Authors:** Andrei Popescu, Johannes P. Wallner
- **Year:** 2024
- **URL:** https://arxiv.org/abs/2407.05058
- **Why it closes the gap:** This paper refines complexity results (extension probability is #P-complete, acceptability is #P^NP-complete) and proposes a dynamic programming algorithm on tree-decompositions for computing extension probabilities. Tree-decomposition is directly relevant to our connected-component decomposition strategy — frameworks with low treewidth (sparse graphs, which argumentation graphs often are) become tractable. Complements the Monte Carlo approach: use exact DP on low-treewidth components, fall back to sampling on dense ones.

### Paper 3 (supplementary): Liao, Xu & Huang — Subgraph Characterization

- **Title:** Formulating Semantics of Probabilistic Argumentation by Characterizing Subgraphs: Theory and Empirical Results
- **Authors:** Beishui Liao, Kang Xu, Huaxin Huang
- **Year:** 2016
- **URL:** https://arxiv.org/abs/1608.00302
- **Why it matters:** Proposes computing extension probabilities by characterizing subgraph properties rather than enumerating subgraphs. Shows fixed-parameter tractability under complete and preferred semantics. Performance improves as graph density or extension size increases — the opposite of naive approaches. Useful as a third strategy alongside Monte Carlo and tree-decomposition.

## Gap 7: Bridging LLM Extraction with Graded/Probabilistic Argumentation

### Paper 4: Freedman, Dejl, Gorur, Yin, Rago & Toni — ArgLLMs with QBAFs

- **Title:** Argumentative Large Language Models for Explainable and Contestable Claim Verification
- **Authors:** Gabriel Freedman, Adam Dejl, Deniz Gorur, Xiang Yin, Antonio Rago, Francesca Toni
- **Year:** 2025 (AAAI 2025)
- **URL:** https://arxiv.org/abs/2405.02079
- **Code:** https://github.com/CLArg-group/argumentative-llms
- **Why it closes the gap:** This paper directly bridges LLM outputs with graded argumentation. LLMs generate supporting and attacking arguments, each assigned a confidence score (base strength), which are assembled into Quantitative Bipolar Argumentation Frameworks (QBAFs). These QBAFs are then evaluated via gradual semantics (DF-QuAD algorithm) that propagate strengths through the attack/support graph to compute a final graded score. This is exactly the missing piece between Fang 2025's binary LLM-ASPIC+ and our need for graded confidence — it shows how to extract numerical argument strengths from LLMs and feed them into a formal quantitative framework. The AAAI venue and available code make this immediately actionable.

## Summary: Recommended Acquisitions

| Priority | Paper | Gap | Key technique |
|----------|-------|-----|---------------|
| HIGH | Fazzinga et al. 2013/2016 | 2+4 | Monte Carlo sampling for extension probabilities |
| HIGH | Freedman et al. 2025 | 7 | LLM confidence → QBAF → gradual semantics |
| MEDIUM | Popescu & Wallner 2024 | 2+4 | Tree-decomposition DP for exact computation |
| LOW | Liao et al. 2016 | 2+4 | Subgraph characterization, FPT results |

The two HIGH-priority papers together give us: (a) a practical approximation algorithm for PrAF at scale, and (b) a proven architecture for extracting graded beliefs from LLMs into quantitative argumentation frameworks.
