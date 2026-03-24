# Notes: Processing "νZ - Maximal Satisfaction with Z3" paper

## Goal
Process the paper "νZ - Maximal Satisfaction with Z3" by Bjorner & Phan (2014) into propstore.
URL: https://www.microsoft.com/en-us/research/wp-content/uploads/2016/02/nbjorner-scss2014.pdf

## Status
- fetch_paper.py failed: "Could not resolve metadata" — direct Microsoft URL not supported
- search_papers.py launched but output appears empty or still running
- Background task IDs: bfwvcuui0, b1crnno0z — both seem to produce no output

## Observations
- search_papers.py with --source s2 hangs/produces no output
- search_papers.py with --source arxiv works but doesn't find this paper (not on arxiv)
- The paper is a 2014 SCSS workshop paper, likely only available via Microsoft Research

## Progress
- PDF downloaded successfully: papers/Bjorner_2014_MaximalSatisfactionZ3/paper.pdf (366KB)
- metadata.json created manually with title, authors, year, venue
- Step 1 (retrieval) DONE
- Step 2 (paper-reader) IN PROGRESS - need to convert PDF to page images, then read all pages

## Paper Content Summary (all 10 pages read)
- p.1: Title, abstract, Section 1 (SMT and Optimization) - motivation for optimization in SMT
- p.2: Section 1.1 (Stating objectives in SMT-LIB), Section 1.2 (nuZ Composition) - MaxSMT and OptiMathSAT
- p.3: Section 2 (Weighted MaxSMT), Section 2.1 (WMax) - iterative approach using SMT core
- p.4: Section 2.2 (MaxRes) - Maximal Resolution based approach, Farkas lemma usage
- p.5: Section 3 (nuZ for Linear Arithmetic) - Simplex-based optimization, Algorithms 1&2
- p.6: Section 3.1 (Dual/Simplex Optimization), Section 3.2 (Unbounded Objectives), Section 3.3 (Experiment with Core-based optimization) - bisection search
- p.7: Algorithm 3 (Bisection Search with Farkas Lemmas), Section 4 (Combining Objectives) - lexicographic, Pareto, box objectives
- p.8: Algorithms 4 & 5 (Pareto fronts, box-maximal front), Section 5 (Conclusion), References start
- p.9: References continued [1]-[15]
- p.10: Reference [15] continued, rest is blank

## Key Algorithms
1. Algorithm 1: Sequential search (WMax/MaxSAT approach)
2. Algorithm 2: Finding unbounded objectives using non-standard arithmetic
3. Algorithm 3: Bisection Search with Farkas Lemmas
4. Algorithm 4: Guided Improvement for Pareto fronts
5. Algorithm 5: Box-maximal front (independent upper bounds)

## Files Written
- notes.md DONE
- description.md DONE
- abstract.md DONE
- citations.md DONE
- pngs/ DONE (10 pages)

## Completed Steps
- index.md updated with entry
- Reconcile done: no forward/reverse citation matches, 3 conceptual links (Mahmood, Niskanen, Tang)
- Concept registration: registered smt_solver, weighted_maxsmt, maxsat_algorithm, pareto_front, linear_arithmetic_optimization, farkas_lemma, soft_constraint (concept413-419)
- Had to remove stale answer_set_programming.yaml (deleted on branch but file still present) which collided with concept419
- Still need: lexicographic_optimization, dual_simplex concepts, then extract claims, write report

## All Steps Complete
- Concept collision resolved (removed stale answer_set_programming.yaml)
- lexicographic_optimization (concept421) and dual_simplex (concept422) registered
- claims.yaml written: 14 claims (3 observation, 5 mechanism, 2 comparison, 2 limitation)
- Final report written to reports/paper-process-batch-Bjorner_2014_MaximalSatisfactionZ3-report.md
- All paper-reader deliverables complete: notes.md, description.md, abstract.md, citations.md, pngs/, index.md updated, cross-references added
