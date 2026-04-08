---
paper: Potyka_2019_PolynomialTimeEpistemicProbabilistic
title: "A Polynomial-time Fragment of Epistemic Probabilistic Argumentation"
authors: [Nico Potyka]
year: 2019
venue: "International Journal of Approximate Reasoning"
doi: "10.1016/j.ijar.2019.10.005"
arxiv_id: "1811.12083"
tags: [probabilistic-argumentation, complexity, epistemic-probability, linear-programming, tractability]
status: complete
read_date: 2026-03-30
provenance: "PDF from arxiv.org/abs/1811.12083, 15 pages, read via pymupdf text extraction"
---

# Notes: A Polynomial-time Fragment of Epistemic Probabilistic Argumentation

## Overview

This paper identifies a tractable fragment of epistemic probabilistic argumentation -- the approach where probability functions P: 2^A -> [0,1] over possible worlds assign belief degrees to arguments. The key problem is that |2^A| is exponential in |A|, making naive computation intractable. *(p.1)*

The central insight: when constraints are **linear atomic** (only reference P(A) for individual arguments, not P(F) for complex formulas), probability functions can be replaced by **probability labellings** L: A -> [0,1] of linear size. Both PArgAtSAT and PArgAtENT reduce to linear programs solvable in polynomial time. *(pp.1, 3-5)*

## Section 2: Background -- Epistemic Probabilistic Argumentation *(pp.1-2)*

**Bipolar argumentation frameworks** (BAFs): (A, R, S) with arguments A, attack R, support S. *(p.2)*

**Possible world**: w subset of A (arguments accepted in that state). *(p.2)*

**Probability function**: P: 2^A -> [0,1] with sum = 1. P(A) = sum over worlds containing A. *(p.2)*

**Semantic constraints for attacks** *(p.2)*:
- **COH** (coherent): P(B) <= 1 - P(A) for all (A,B) in R
- **SFOU** (semi-founded): P(A) >= 0.5 for unattacked A
- **FOU** (founded): P(A) = 1 for unattacked A
- **SOPT** (semi-optimistic): P(A) >= 1 - sum P(B) for B attacking A, when attacked
- **OPT** (optimistic): P(A) >= 1 - sum P(B) for B attacking A
- **JUS** (justifiable): coherent AND optimistic

**Computational problems** from Hunter & Thimm 2016 [31] *(p.2)*:
1. Satisfiability: does a probability function satisfying constraints exist?
2. Entailment: compute lower/upper bounds on P(A) among satisfying functions
3. Decision variant: do given bounds hold?

All conjectured intractable due to similarity to probabilistic reasoning problems. **This paper shows they are polynomial-time.** *(p.2)*

## Section 3: Linear Atomic Constraints *(pp.2-3)*

**Def 3.1**: Linear atomic constraint: sum(c_i * pi(A_i)) <= c_0. *(p.2)*

Can express >=, = via negation/pairs. Captures all semantic constraints from [31]. *(p.3)*

**PArgAtSAT**: Given constraints C, decide satisfiability. *(p.3)*
**PArgAtENT**: Given satisfiable C and argument A, compute min/max P(A) subject to C. *(p.3)*

**Support constraints** (dual to attack) *(p.3)*:
- **S-COH** (support-coherent): P(B) >= P(A) for (A,B) in S
- **SSCE** (semi-sceptical): P(A) <= 0.5 for unsupported A
- **SCE** (sceptical): P(A) = 0 for unsupported A
- **SPES** (semi-pessimistic): P(A) <= sum P(B) for B supporting A, when supported
- **PES** (pessimistic): P(A) <= sum P(B) for B supporting A

## Section 4: Polynomial-time Algorithms *(pp.3-5)*

**Probability labelling**: L: A -> [0,1], assigns belief degrees directly. *(p.3)*

**Atomic equivalence**: P1 equiv P2 iff P1(A) = P2(A) for all A. *(p.3)*

**Lemma 4.1**: Bijection r: PA/equiv -> LA. Crucially, for any labelling L, construct PL(w) = prod_{A in w} L(A) * prod_{A not in w} (1-L(A)) -- this IS a probability function with PL(A) = L(A). *(pp.3-4)*

**Lemma 4.2**: P satisfies a linear atomic constraint iff LP = r([P]) satisfies it. *(p.4)*

**Theorem 4.3 (PArgAtSAT in P)**: Reduce to LP: minimize sum of slack variables s_j subject to sum(c_i * x_i) <= c_0^j + s_j, 0 <= x <= 1, s >= 0. Satisfiable iff minimum = 0. *(p.4)*

**Theorem 4.4 (PArgAtENT in P)**: LP: min/max x_k subject to constraints, 0 <= x <= 1. Directly gives bounds. *(p.5)*

Both have n+m variables (n arguments, m constraints) -- polynomial by LP theory. *(p.4)*

## Section 5: Complex Formulas and k-th Order Labellings *(pp.5-7)*

**k-th order labellings** assign probabilities to k-valuations. Size 2^k * C(|A|,k) -- polynomial for fixed k. *(pp.5-6)*

**Problem**: Not every k-th order labelling corresponds to a probability function (Example 5.5). Normalization + marginal consistency are necessary but insufficient for k > 1. *(pp.6-7)*

**Proposition 5.6**: If P != NP, no polynomial set of linear constraints can ensure k-th order labellings (k>1) correspond to probability functions. Proof via reduction from 2PSAT. *(p.7)*

## Section 6: Complex Constraints -- Intractability Boundary *(pp.7-8)*

**Proposition 6.1**: Satisfiability for linear 2DN constraints (disjunctions of 2 literals) is NP-complete. Via 2PSAT reduction. *(p.7)*

**Proposition 6.2**: Satisfiability for linear 2CN constraints (conjunctions of 2 literals) is NP-complete. Via reduction from 2DN. *(pp.7-8)*

**Proposition 6.3**: Satisfiability for 2D linear atomic constraints (disjunctions of two atomic constraints) is NP-complete. Via 3SAT reduction. *(p.8)*

**Open question**: Disjunctions of single-variable constraints (pi(A1) <= c1 OR pi(A2) <= c2) -- might be polynomial via 2SAT ideas. Would allow expressing RAT (rationality) constraint. *(p.8)*

## Section 7: Complex Queries *(pp.8-13)*

**Proposition 7.1**: Deciding non-zero upper bound for 3CNF-queries is NP-complete. *(pp.8-9)*

### 7.1: Maximum Entropy + Conjunctive Queries *(pp.9-10)*

**Entropy of labelling**: H(L) = sum(-L(A)*log L(A) - (1-L(A))*log(1-L(A))). *(p.9)*

**Proposition 7.3**: PL maximizes entropy within equivalence class [PL]. H(PL) = H(L). Proof via KL-divergence. *(p.9)*

**Proposition 7.4**: Max-entropy labelling L* computable in polynomial time (convex optimization, n variables). *(p.10)*

**Proposition 7.5 (KEY)**: Under max-entropy with atomic constraints, conjunctive queries: P*(conjunction of A_i^{b_i}) = product of L*(A_i)^{b_i} * (1-L*(A_i))^{1-b_i}. Polynomial time. *(p.10)*

**Proposition 7.6**: 3CNF-queries under max-entropy are #P-hard. *(p.10)*

### 7.2-7.3: Independence Assumptions *(pp.11-13)*

Max-entropy with atomic constraints implies **stochastic independence between all arguments**. *(p.11)*

**Corollary 7.10**: P*(chi2 | chi1) = P*(chi2) -- conditioning is meaningless. *(p.12)*

**Workaround**: Simulate conditioning by adding constraints pi(A) = 1, recompute P*. *(p.12)*

**Proposition 7.11**: Under COH, P*(A AND B AND chi) <= min{0.25, 1-P*(A)} when A attacks B. Attack strength determined by belief in source. *(p.12)*

**Proposition 7.12**: Under S-COH, P*(A AND NOT B AND chi) <= min{0.25, 1-P*(A)} when A supports B. Dual to Prop 7.11. *(p.12)*

**Proposition 7.13**: Under COH + S-COH with (A,C) in R and (B,C) in S: P*(A)+P*(B) <= 1, and conjunction bounds <= min{0.25, 1-P*(source)}. *(p.13)*

## Section 8: Related Work *(pp.13-14)*

- Dung & Thang 2010 [19]: probability via probabilistic rules, not constraint-based
- Li et al. 2011 [38]: probability on subgraphs, MC approximation (exponential subgraphs)
- Rienstra 2012 [53]: probabilistic extension of ASPIC-style rules
- Riveret et al. 2018 [55]: general labelling framework for probabilistic argumentation (conceptual, no computational focus)
- Equivalence class idea relates to probabilistic logic work [22,23,35,47], but those partition worlds (can still be exponential), whereas this partitions functions (always linear)
- Hunter & Thimm 2016 [31]: original problems shown tractable here
- ProBabble implementation: thousands of arguments in hundreds of ms

## Section 9: Discussion *(p.14)*

- Constraint language cannot be extended significantly without losing tractability
- Open: disjunctions of single-variable constraints (RAT expressibility)
- Open: conjunctive queries for entailment WITHOUT max-entropy
- Worst-case cubic via interior-point; simplex usually linear in variables, quadratic in constraints
- ProBabble: thousands of args in ~100ms; without labellings, same time for 10-15 args

## Implementation Relevance to propstore

1. **Probability labellings = opinion base scores**: propstore already assigns [0,1] values to arguments via Subjective Logic opinions. The labelling L: A -> [0,1] is isomorphic.
2. **LP for satisfiability/entailment**: Could replace/complement MC sampling (Li et al. 2012) for the atomic constraint fragment. LP gives exact bounds in polynomial time vs. MC approximation.
3. **COH constraint**: Already implemented in propstore (praf.py, opt-in via enforce_coh). This paper proves COH is within the tractable fragment.
4. **Max-entropy independence caveat**: Important warning for propstore -- if using max-entropy labelling approach, arguments become stochastically independent. This is fine for marginal queries but misleading for conjunctive/conditional queries without extra constraints.
5. **Tractability boundary**: Any extension beyond atomic constraints (even 2-literal formulas) hits NP-completeness. This precisely delineates what propstore can compute efficiently.

## New Leads

- Hunter & Thimm 2016 [31]: "On Partial Information and Contradictions in Probabilistic Abstract Argumentation" (KR) -- original problems
- Hunter, Polberg & Thimm 2018 [29]: "Epistemic Graphs for Representing and Reasoning with Positive and Negative Influences of Arguments" -- general constraint language
- Hunter, Polberg & Potyka 2018 [28]: "Updating Belief in Arguments in Epistemic Graphs" (KR)
- Potyka, Polberg & Hunter 2019: "Polynomial-time Updates of Epistemic States..." (found in search, arxiv 1906.05066) -- extends this work to updates
- Riveret et al. 2018 [55]: Already in collection
- Freedman et al. approach to DF-QuAD connects to weighted BAF discussion
