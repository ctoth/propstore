# Reading Denoeux 2019 - Decision-Making with Belief Functions

## GOAL
Read all 39 pages, extract implementation-focused notes for propstore render-time decision making.

## STATUS
All 39 pages read. Now writing paper artifacts.

## COMPLETE FINDINGS

### Paper Structure
- Section 1: Introduction (p.1)
- Section 2: Classical Decision Theories (p.2-10)
- Section 3: Theory of Belief Functions (p.11-12)
- Section 4: Extensions of Classical Criteria (p.15-22)
  - 4.1 Upper/Lower Expected Utilities
  - 4.2 Generalized Hurwicz
  - 4.3 Pignistic Criterion
  - 4.4 Generalized OWA
  - 4.5 Generalized Minimax Regret
  - 4.6 Jaffray's and related axioms
  - 4.7 Dropping completeness requirement
- Section 5: Imprecise-Probability View (p.25-27)
  - 5.1 Maximality criterion
  - 5.2 E-admissibility
- Section 6: Shafer's Constructive Decision Theory (p.29-33)
  - 6.1 Formulation using Goals
  - 6.2 Evaluating Acts
- Section 7: Conclusions (p.33-34)
- References (p.35-39)

### Key new findings (pages 20-38)

**Jaffray's axioms (p.21-22):**
- Extended VNM axioms to evidential lotteries
- Key: preference on evidential lotteries representable by linear utility iff transitivity, completeness, continuity, independence
- Utility of evidential lottery: U(p) = sum p_l * (alpha * U(c_A) + (1-alpha) * U(c_B)) — pessimism index alpha
- Hurwicz criterion (Eq 42) corresponds to alpha(sigma) = constant (ambiguity aversion)

**Dropping completeness (p.23-24):**
- Strong dominance: f >_SD g iff E_lower(f) >= E_lower(g) AND E_upper(f) >= E_upper(g)
- Interval bound dominance: weaker, based on Hurwicz for any alpha
- Stochastic dominance extensions to DS setting
- 4 ordering relations based on Bel/Pl stochastic dominance

**Imprecise probability view (p.25-27):**
- Lower/upper expectations can be seen as bounds over credal set P(m)
- Maximality criterion: X >_max Y iff E_lower(X - Y) > 0 (lower expectation of difference is positive)
- Strict preference only when ALL compatible probabilities agree
- E-admissibility: gamble X in choice set if there EXISTS P in P(m) such that E_P(X) >= E_P(Y) for all Y
- E-admissibility can be computed via linear programming
- Choice set from maximality is included in that from E-admissibility

**Shafer's constructive decision theory (p.29-33):**
- Rejects bare probability/utility; constructs them from goals
- Frame of discernment = goals A_1...A_n with weights w_1...w_n
- Score of act f: U(f) = sum w_i * (Bel_f(A_i) + Pl_f(A_i))
- u+(f) = sum w_i * Bel_f(A_i) = expected weight of goals achieved
- u-(f) = sum w_i * Bel_f(A_i_complement) = expected weight of goals precluded
- When m_f is Bayesian, reduces to MEU
- Classification application: goals = correct class, mass function from classifier
- Score U(f) = Bel(C) + Pl(C) for selecting class C

**Conclusions (p.33-34):**
- All methods reduce to MEU when belief function is Bayesian
- Most important distinction: whether they produce complete or partial preference
- Pignistic: most widely used in applications, supported by Smets' arguments
- Main arguments for pignistic: avoidance of Dutch books, linearity property
- Hurwicz/OWA: parameterize attitude toward ambiguity
- Imprecise probability approach: partial preferences, more conservative
- Shafer's constructive: different path, builds utility from goals
- Open: decision criteria for DS setting on real line (imprecise probability framework)

## FILES
- Paper dir: papers/Denoeux_2018_Decision-MakingBeliefFunctionsReview/
- 39 page PNGs in pngs/ subdir

## NEXT
Write notes.md, description.md, abstract.md, citations.md, update index.md
