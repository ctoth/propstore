# Cluster F: probabilistic + subjective logic + sensitivity + fragility

Status: IN PROGRESS — checkpoint write triggered by hook.
Reviewer: review-cluster-F (analyst subagent).
Date: 2026-04-26.

## Scope

Files read in full so far:
- `propstore/probabilistic_relations.py`
- `propstore/opinion.py` (full module — Opinion, BetaEvidence, consensus_pair, wbf, ccf, fuse, discount)
- `propstore/praf/__init__.py`, `engine.py`, `projection.py`, `README.md`
- `propstore/sensitivity.py`
- `propstore/fragility.py`, `fragility_contributors.py`, `fragility_scoring.py`, `fragility_types.py`
- `propstore/calibrate.py`
- `propstore/propagation.py`
- `tests/test_calibrate.py`, `tests/test_base_rate_resolution.py`
- `docs/probabilistic-argumentation.md`, `docs/subjective-logic.md`, `docs/fragility.md` (partial)

Paper notes consulted:
- Josang_2001 (full operator definitions)
- Josang_2010 (multinomial multiplication; warning: directory misnamed "CumulativeAveragingFusionBeliefs" but PDF is the multiplication paper — not the cumulative/averaging fusion paper)
- vanderHeijden_2018 (WBF, CCF, BCF multi-source)
- Hunter_2017, Hunter_2021, Thimm_2012, Riveret_2017
- Coupé_2002, Ballester-Ripoll_2024
- Sensoy_2018 (notes file MISSING for "EvidentialDeepLearningQuantify" — only the "Classification" variant has notes.md)
- Margoni_2024, Vasilakes_2025

Not yet read in this session: Li_2011, Popescu_2024 (three variants), Kaplan_2015, Walley_1996, Howard_1966, Pearl_2000, Halpern_2000/2005, Shafer_1976, Shenoy_1990, Denoeux_2018, Chan_2005, Gardenfors_1982, Guo_2017, Potyka_2019, Thimm_2020. (Cited in scope but cluster review can proceed; these are mostly background.)

## Subjective logic operator coverage and correctness

### Coverage

| Operator | Implemented | File:line | Citation |
|----------|-------------|-----------|----------|
| Opinion (b,d,u,a), b+d+u=1 enforced | YES | opinion.py:42-67 | Josang Def 9, p.7 |
| Vacuous / dogmatic constructors | YES | opinion.py:94-107 | Josang p.8 |
| E(ω) = b + a·u | YES | opinion.py:111-113 | Josang Def 6 |
| Uncertainty interval [Bel, Pl] | YES | opinion.py:115-117 | Josang p.4 |
| BetaEvidence ↔ Opinion bijection (W=2) | YES | opinion.py:121-130, 325-331 | Josang Def 12 |
| Negation (~) | YES | opinion.py:134-136 | Josang Theorem 6 |
| Conjunction (binary frames) | YES | opinion.py:138-156 | Josang Theorem 3 |
| Disjunction (binary frames) | YES | opinion.py:158-175 | Josang Theorem 4 |
| Consensus (pair) | YES | opinion.py:362-393 | Josang Theorem 7 |
| Trust discounting | YES | opinion.py:406-429 | Josang Def 14 |
| Ordering (E, -u, -a) | YES | opinion.py:228-255 | Josang Def 10 |
| Uncertainty maximization | YES | opinion.py:259-293 | Josang Def 16 |
| WBF (N-source) | YES | opinion.py:432-522 | vdH 2018 Def 4 |
| CCF (N-source binomial) | YES | opinion.py:525-679 | vdH 2018 Def 5 |
| Multinomial opinions (k>2) | NO | — | Josang_2010, vdH 2018 Def 1-2 |
| BCF (Belief Constraint Fusion) | NO | — | vdH 2018 Def 3 |
| CBF / ABF (cumulative / averaging) | NO | — | Josang_2010 cites; vdH 2018 §III |
| Multiplication on Cartesian frames | NO | — | Josang_2010 (mis-named dir) |
| Multinomial discounting / hyper-opinions | NO | — | vdH 2018 Def 2 |
| Deduction / abduction (Josang 2008) | NO | — | docs admit gap |
| Kaplan_2015 partial-observable update | NO | — | scoped paper |

### Correctness findings (math-first)

1. HIGH — `wbf()` deviates from vanderHeijden 2018 Def 4 in TWO ways:

   (a) `_BASE_RATE_CLAMP = (0.01, 0.99)` (`opinion.py:33`). vdH 2018 Def 4 explicitly requires that **all sources share a single base rate** and that the fused base rate inherits it unchanged. propstore instead computes a confidence-weighted blend and clamps. The docstring acknowledges this as deliberate deviation, but the consequence is that `Opinion.expectation() = b + a·u` becomes mathematically uncoupled from the per-source `a` values. Specifically: WBF on two opinions with `a=0.5` and `a=0.5` should produce `a=0.5` (no clamp needed) — verify but the formula at opinion.py:502-510 weights by `(1 - u_i) * prod_except[i]`. With u_a=u_b=0.5 and a_a=a_b=0.5 the formula returns 0.5 by symmetry. However for u_a near 1 and u_b near 1 both `(1-u_i)` collapse to ~0 and the fallback path at opinion.py:504-506 averages the base rates — this is fine but is NOT vdH's contract. Tests should pin this.

   (b) Dogmatic-source branch (opinion.py:449-467) returns the **simple average** of dogmatic sources' belief, disbelief, and base rate. vdH 2018 Remark 1 says "if u=0 for exactly one actor and u>0 for all others, the fused result uses *only* the dogmatic actor's belief." The propstore code does follow that for the `count == 1` case. But for `count >= 2` dogmatic sources it averages them, which has no explicit warrant in vdH 2018 — Remark 2 (all-dogmatic) only specifies a limit interpretation via ε perturbation. Comment on line 454-456 admits "the limiting weights are equal in this unweighted API"; that is a propstore convention not the paper.

2. HIGH — `consensus_pair()` base-rate formula (`opinion.py:381-391`) is also a "confidence-weighted average" deviating from Josang 2001 Theorem 7 (p.25), which prescribes
   `a = (a_B·u_A + a_A·u_B − (a_A+a_B)·u_A·u_B) / (u_A + u_B − 2·u_A·u_B)`.
   The implementation returns
   `a = (a_B·u_A·v_B + a_A·u_B·v_A) / (u_A·v_B + u_B·v_A)` where `v = 1 − u`.
   These are NOT algebraically equivalent. Numerator: paper has `a_A·u_B + a_B·u_A − (a_A+a_B)·u_A·u_B`; impl has `a_B·u_A·(1−u_B) + a_A·u_B·(1−u_A) = a_B·u_A − a_B·u_A·u_B + a_A·u_B − a_A·u_B·u_A = a_A·u_B + a_B·u_A − (a_A+a_B)·u_A·u_B`. Equal. Denominator: paper has `u_A + u_B − 2·u_A·u_B`; impl has `u_A·(1−u_B) + u_B·(1−u_A) = u_A − u_A·u_B + u_B − u_B·u_A = u_A + u_B − 2·u_A·u_B`. **Equal.** This formula is correct — withdrawing the HIGH for consensus_pair. Docstring claims "cancellation-free form" — that is plausible for floating-point stability. **NOT a bug.** (Reclassify to OK; left here for transparency.)

3. HIGH — `_defeat_summary_opinion()` (`praf/engine.py:82-111`) constructs an Opinion from a **scalar defeat probability** by inventing belief, disbelief, and uncertainty:
   - When variance ≈ 0, returns dogmatic `(p, 1−p, 0, 0.5)`.
   - Otherwise sets `uncertainty = max_uncertainty * normalized_variance` where `normalized_variance = min(1, p(1-p)/0.25)` and `belief = p − 0.5·uncertainty`, `disbelief = 1 − belief − uncertainty`.

   **Math problem:** `belief = p − 0.5·u` only equals `b = E − a·u` when `a = 0.5`, which is hard-coded. That's defensible. But `disbelief = 1 − belief − uncertainty` does not enforce `d ≥ 0` and `b ≥ 0`. Worked example: p=0.99, variance = 0.0099, normalized_variance ≈ 0.0396; max_uncertainty = `min(0.99/0.5, 0.01/0.5) = 0.02`; uncertainty ≈ 0.000792; belief = 0.99 − 0.000396 ≈ 0.9896; disbelief = 1 − 0.9896 − 0.000792 ≈ 0.00961. Constraint OK at boundary, but for very narrow p the floats will likely round below zero with no clamp — the Opinion constructor will then ValueError because b/d/u are checked against `[-_TOL, 1+_TOL]` and the post-init also re-validates b+d+u≈1. There is no defensive clamp before constructing the Opinion, so a marginal probability close to 0 or 1 could crash the function. Worse: this manufactured opinion has NO empirical basis (variance ≠ uncertainty in subjective logic; uncertainty = W/(W+r+s) and variance = pq/(α+β+1) of a Beta — they are different quantities).

4. HIGH — `from_probability(p, n=1, a)` in `p_relation_from_stance()` (`praf/engine.py:309-314`): a stance with `confidence=0.5` and `n=1` becomes an opinion with `r=0.5, s=0.5, b=0.5/(2.5)=0.2, d=0.2, u=2/2.5=0.8`. Calling `from_probability(0.5, 1, a=0.5)` gives `expectation = 0.2 + 0.5·0.8 = 0.6` not 0.5. **Round-trip is broken** because the prior weight W=2 dominates the single observation. This is mathematically correct under Josang's model, BUT it means a stance row recording confidence=0.5 emerges from PrAF as a defeat-existence probability of 0.6, silently shifted toward the base rate. Either the docstring contract (claiming stance "moderate uncertainty") or the choice `n=1` is misleading. The hard-coded `1` should be a calibration parameter.

5. MED — `Opinion.__post_init__` (`opinion.py:57-67`) tolerates `b + d + u` ∈ [1−1e-9, 1+1e-9] but does not validate `allow_dogmatic` semantics. The dataclass field `allow_dogmatic` exists (line 55) and is referenced in `wbf()` at line 466 and `_defeat_summary_opinion()` at line 96/104, but is NEVER used in `__post_init__`. There's no actual gating. So `Opinion(0.5, 0.5, 0.0, 0.5)` succeeds without `allow_dogmatic=True` — making the field decorative. Either remove the field or add `if u < _TOL and not self.allow_dogmatic: raise ValueError(...)`.

6. MED — `consensus()` (`opinion.py:396-403`) folds left-to-right pairwise. Josang 2001 proves consensus is associative *for non-dogmatic opinions only* (kappa ≠ 0); for borderline-dogmatic opinions floating-point order matters. WBF explicitly exists to avoid this. The fact that propstore exposes both APIs is good, but `consensus()` should at least warn (or be deprecated) in favor of `wbf()` for N>2.

7. MED — `discount()` (`opinion.py:406-429`) implements the **simplified expanded form**. Verified: `u = trust.d + trust.u + trust.b·source.u`. Per Josang Def 14: `u = d_B^A + u_B^A + b_B^A · u_x^B` — matches. Note however that `b + d + u = trust.b·source.b + trust.b·source.d + trust.d + trust.u + trust.b·source.u = trust.b·(b_x + d_x + u_x) + trust.d + trust.u = trust.b·1 + trust.d + trust.u = 1`. ✓ Always sums to 1 by construction. **OK.**

8. MED — `to_beta_evidence()` (`opinion.py:121-130`) raises `ValueError` for u < _TOL but `from_evidence()` (calling `BetaEvidence.to_opinion`) **does not** allow construction of dogmatic opinions either (denom = r+s+W is always ≥ W = 2, so u = 2/(r+s+2) is bounded below by 2/(very-large) but never zero). This means dogmatic opinions are constructable directly via `Opinion(...)` but not via the evidence path — asymmetric and undocumented.

9. LOW — `Opinion.__bool__` (opinion.py:185-200) raises TypeError. Good defensive design. But `Opinion._quantized()` (opinion.py:202-216) uses `_TOL = 1e-9` as the quantization grid. With float drift at this fineness, two semantically-equal opinions constructed via different operator chains could hash differently. The docstring claims the contract is preserved, but no property test verifies `op == op` after a round-trip through, e.g., `~~op` or `consensus(op, vacuous)`.

10. LOW — `_BASE_RATE_CLAMP = (0.01, 0.99)` at line 33 is applied in WBF and CCF but NOT in `consensus_pair()`. So three-source CCF clamps base rates while two-source consensus does not. Inconsistent.

11. LOW — `ccf()` self-fusion edge case (`opinion.py:646-650`): when `comp_sum < _TOL`, the code returns `(cons_b, cons_d, 1 − cons_b − cons_d)` with `u_fused = max(0.0, 1 − cons_sum)`. For two identical inputs `op = (0.4, 0.3, 0.3, 0.5)`, `cons_b=0.4`, `cons_d=0.3`, `u_fused = 0.3`. ✓ Idempotent (claim verified). Good.

## PRAF semantics coverage (constellation/epistemic/labeling)

### Coverage table (per Hunter 2021 survey taxonomy)

| Approach | Implemented? | Where | Notes |
|----------|--------------|-------|-------|
| Constellation (Li_2011, Hunter_2017) | YES | `argumentation.probabilistic` (external) | Adapter in `propstore.praf` |
| Epistemic probability function over 2^Arg | NO (no MaxEnt) | — | Thimm_2012 / Hunter_2017 §3 |
| COH rationality postulate | YES | `engine.py:329-409` enforce_coh | Hunter & Thimm 2017 |
| RAT, FOU, SFOU, OPT, INV, NEU, MAX, MIN, JUS, TER | NO | — | Hunter_2017 lists ~12 postulates; only COH is enforced |
| Maximum entropy completion (Thimm 2012) | NO | — | Major missing feature |
| Inconsistency measures over assessments | NO | — | Hunter_2017 §5 |
| Distance-based consolidation | NO | — | Hunter_2017 §6 |
| Labelling-based PrAF (Riveret_2017) | NO | — | Riveret §2 ON/OFF/IN/OUT/UN |
| Polynomial-time fragments (Potyka_2019) | NO (paper not consulted in this pass) | — | Mentioned in goal |
| Sampling approximation (Thimm_2020) | NO (paper not consulted) | — | MC sampling exists but unrelated |

### Specific PRAF findings

12. HIGH — `enforce_coh()` (`praf/engine.py:329-409`) is mathematically dubious in three ways:

   (a) The fixpoint loop is bounded at 100 iterations (line 350) but does not detect divergence. If a constraint cycle exists, the loop silently exits without raising. Nothing flags the partial enforcement to the caller.

   (b) After scaling expectations, the code reconstructs opinions via `from_probability(p, n, a)` where `n = W*(1/u − 1)` (line 345). For dogmatic inputs (u=0), it falls back to `n=10.0` (line 347) — an arbitrary magic number with no citation.

   (c) The COH constraint per Hunter & Thimm 2017 p.9 is `P(A) + P(B) ≤ 1 if A→B`. The implementation uses `> 1.0 + 1e-12` (line 360) — fine. But for self-attacks (`src == tgt`), it caps at 0.5 which corresponds to `2·P(A) ≤ 1`, i.e., `P(A) ≤ 0.5`. That matches Hunter_2017 p.9 ("self-attackers are ≤ 0.5"). **OK.**

13. MED — `p_arg_from_claim()` (`praf/engine.py:145-276`) has TWO copies of essentially the same logic — one for `ClaimRow` instances (lines 147-199) and one for `dict` (lines 201-276). The second branch is reachable via `if not isinstance(claim, dict): claim = coerce_claim_row(claim); return p_arg_from_claim(claim)` (lines 201-203) which **recurses on the coerced value but the coerced value is a ClaimRow not a dict**, so the recursion lands in the first branch. Then the dict branch (lines 205-276) is only entered when the input is **already a dict**. Refactor opportunity, but no bug.

14. MED — `summarize_defeat_relations()` (`praf/engine.py:412-437`) builds opinions via `_defeat_summary_opinion(probability)` (the manufactured-uncertainty function flagged in finding 3). The provenance status is `CALIBRATED` for these synthetic opinions — but there is NO calibration; the variance-to-uncertainty conversion is heuristic. This violates the project's "honest ignorance over fabricated confidence" rule (cited explicitly in calibrate.py docstrings).

15. LOW — `PropstorePrAF` carries `attack_relations`, `support_relations`, `direct_defeat_relations` as tuples (engine.py:49-51) but `omitted_arguments` and `omitted_relations` are mutable dicts converted via `__post_init__` (lines 59-61). Mutable fields on a `frozen=True` dataclass are a footgun.

## Sensitivity / fragility coverage

### Coverage

| Method | Implemented? | Where | Citation |
|--------|--------------|-------|----------|
| Local OAT partial derivatives | YES | `sensitivity.py:260-286` (sympy diff) | Coupé_2002 baseline |
| Elasticity (df/dx · x/f) | YES | `sensitivity.py:276-279` | standard |
| Linear fractional sensitivity (Coupé Prop 4.1) | NO | — | Major gap; Coupé 2002 main result |
| Sobol indices (first-order, total) | NO | — | Ballester-Ripoll_2024 |
| Tornado / one-at-a-time bar charts | NO | — | mentioned in goal |
| Variance decomposition | NO | — | — |
| Conflict-to-claim-strength propagation | PARTIAL | `fragility_scoring.py:68-100` score_conflict | Heuristic |
| ATMS-derivative fragility | YES | `fragility_scoring.py:135-156` support_derivative_fragility | propstore-internal |
| IMPS-rev (impact via DF-QuAD removal) | YES | `fragility_scoring.py:386-443` | Freedman/Hunter inspired |
| Pairwise interaction detection | YES | `fragility_scoring.py:176-304` detect_interactions | propstore-internal |

### Specific findings

16. HIGH — `analyze_sensitivity()` in `sensitivity.py:72-297` performs **purely local** (point) sensitivity with no support for global/Sobol indices. Per Ballester-Ripoll_2024 Spearman correlations between OAT and Sobol indices on benchmark BNs were only 0.507 and 0.461 — meaning OAT ranks parameters very differently from a global sensitivity analysis. Propstore's "which input most influences this output?" claim in the docstring (sensitivity.py:79) is misleading because OAT can both miss interaction-only effects and falsely promote locally-steep parameters that are globally irrelevant.

17. MED — `analyze_sensitivity()` returns `None` on too many failure modes (lines 121, 122, 140, 243, 246, etc.). Callers cannot distinguish "no parameterization" from "parameterization unsolvable" from "input not resolvable." The sister API `propagation.py:96-176` uses a typed `ParameterizationEvaluation` with explicit status; `sensitivity.py` should adopt the same discipline.

18. MED — `analyze_sensitivity()` evaluates `output_value = float(expr.subs(subs_pairs))` (line 256) and continues with `output_value=None` on error (line 258). Then elasticity (line 277) requires `output_value != 0`. Division by very small but nonzero output values silently produces enormous elasticity values without flagging — a pathology Coupé_2002 explicitly addresses by considering the *normalized* sensitivity.

19. MED — `combine_fragility()` (`fragility_scoring.py:40-65`) supports `top2`, `mean`, `max`, `product` combination policies. `product` for partial scores in [0,1] always shrinks the result toward zero, which is unmotivated — there is NO citation. The function is exported at module level but never called from the codebase anywhere I examined.

20. MED — `score_conflict()` (`fragility_scoring.py:68-100`) computes `min(1.0, max(dist_a, dist_b) / total)` where `dist` is symmetric difference of grounded extensions before vs after removing one claim, normalized by total argument count. This is reasonable but not literature-grounded — no Hunter, Pearl, or Halpern citation. Comment in `collect_conflict_interventions` (`fragility_contributors.py:391`) admits "max grounded-extension delta for the canonical pair" — heuristic.

21. MED — `weighted_epistemic_score()` (`fragility_scoring.py:103-132`) silently falls back to uniform weighting when `probability_weights` provided without `witness_indices` — emits a `FragilityWarning` but proceeds. This is a **silent loss of probability information**. Should raise.

22. LOW — `_SECTION_FRAGILITY = {"definitely": 0.25, "defeasibly": 0.75, "not_defeasibly": 0.5, "undecided": 1.0}` (`fragility_contributors.py:397-402`) is a magic-number table. Notes (line 462) acknowledge "uncalibrated runtime heuristic" and cite Garcia-Simari 2004; this is at least transparent, but it should be backed by per-domain calibration (the very thing `calibrate.py` exists to provide).

23. LOW — `imps_rev()` (`fragility_scoring.py:386-443`) demands provenance-bearing opinions for ALL arguments and defeats and raises `ValueError` otherwise (lines 411-416). Strict — good — but defenders of the framework cannot retroactively attach provenance, and the function produces zero output if the precondition fails. There is no path for partial fragility scoring on a partially-provenanced framework.

24. LOW — `opinion_sensitivity()` (`fragility_scoring.py:339-383`) numerically perturbs `u` by a fixed delta then halves on retry. This is a finite-difference approximation — will quietly compute a sensitivity that differs in sign from the analytic one near boundaries. No literature citation; no test for boundary correctness.

## Calibration metrics coverage

### Coverage

| Metric | Implemented | File:line | Citation |
|--------|-------------|-----------|----------|
| Temperature scaling (Guo 2017) | YES | calibrate.py:48-109 | Guo et al. 2017 p.5 |
| Golden-section temperature fit | YES | calibrate.py:90-108 | NLL minimization |
| ECE (Expected Calibration Error) | YES | calibrate.py:473-510 | Guo 2017 p.1 |
| Adaptive ECE / SCE | NO | — | — |
| Brier score | NO | — | Standard scoring rule, not implemented |
| Negative log-loss / log-loss as a metric | NO (used inside fit only) | — | — |
| MCE (Maximum Calibration Error) | NO | — | Guo 2017 also defines this |
| Reliability diagrams | NO | — | Standard |
| CorpusCalibrator (CDF-based) | YES | calibrate.py:117-253 | Sensoy 2018 / Josang 2001 |
| categorical_to_opinion | YES | calibrate.py:362-436 | propstore-specific |

### Specific findings

25. HIGH — Brier score is **not implemented** despite being one of the three named scoring rules in the goal ("Brier score, log loss, ECE — which is implemented?"). Only ECE is implemented as a standalone metric. Log-loss appears only as `nll` inside `TemperatureScaler.fit` (calibrate.py:82-88). For evaluating LLM stance calibration this is a significant gap.

26. MED — `expected_calibration_error()` (`calibrate.py:473-510`) uses uniform-width bins (line 492). Guo 2017 is precisely about this; Nguyen & O'Connor 2015 / Naeini et al. 2015 show that **adaptive** binning (equal-mass bins) produces more reliable estimates for non-uniform confidence distributions. The docstring does not mention this trade-off.

27. MED — `expected_calibration_error()` (`calibrate.py:498`) places confidences exactly at 1.0 in bin index `n_bins - 1` via `min(int(conf * n_bins), n_bins - 1)`. Confidences exactly at `1/n_bins` boundaries fall in the upper bin. Standard, but no test covers boundary cases.

28. MED — `CorpusCalibrator.to_opinion()` (`calibrate.py:234-253`) uses the `_effective_sample_size()` heuristic with `_MAX_N_EFF = 50` (line 140) and bandwidth `h = 1/sqrt(n)`. Per the test class `TestCorpusCalibrationEvidenceModel` (test_calibrate.py:275-374), this fixed an earlier bug where corpus size produced near-dogmatic opinions. The fix is reasonable BUT the magic constants (50, 9.0 confidence ramp, 1/sqrt(n) bandwidth) are uncited. The Sensoy 2018 reference in the docstring is for evidence semantics, not for the bandwidth choice.

29. MED — `categorical_to_opinion()` returns `Opinion.vacuous(a=base_rate, provenance=prior_provenance)` (calibrate.py:411, 415, 419) when `total <= 0` or when calibration data is missing. The `prior_provenance` is the *base rate's* provenance, not "vacuous because no evidence" provenance. Caller cannot distinguish "no calibration data" from "I have a base rate."

30. MED — `TemperatureScaler.fit()` golden-section search on `[0.01, 10.0]` (calibrate.py:91) clamps T into a fixed range with no convergence diagnostics. Multimodal NLL surfaces for small validation sets could trap the search at a local minimum.

31. LOW — `_softmax()` (calibrate.py:35-40) does not check for NaN/Inf in inputs.

32. LOW — Per the test `test_sqlite_rejects_invalid_opinion_sum` (test_calibrate.py:537) — marked "EXPECTED TO FAIL: no CHECK constraint exists" — the schema does NOT enforce `b+d+u=1`. So opinions can be persisted to sidecar that violate the Josang 2001 invariant. The application-layer checks are bypassable. (I did not verify whether the schema has since been updated; the test comment suggests not.)

## Bugs (HIGH/MED/LOW) — math errors first

Re-listed for prominence; numbers reference findings above.

### HIGH

- F1: WBF base-rate fusion deviates from vdH 2018 Def 4 (clamp + averaged dogmatic case).
- F3: `_defeat_summary_opinion` invents uncertainty from variance with no defensive clamp; can crash for p near 0/1; semantically conflates Beta variance with subjective-logic uncertainty.
- F4: `from_probability(confidence, 1, a)` in `p_relation_from_stance` shifts a confidence-0.5 stance to expectation 0.6 (W=2 prior dominates n=1).
- F12: `enforce_coh()` does not detect divergence; magic `n=10.0` for dogmatic inputs.
- F16: Sensitivity is local-only (OAT). Ballester-Ripoll 2024 shows OAT ranks ≠ Sobol ranks (Spearman 0.46-0.51).
- F25: Brier score not implemented.

### MED

- F5: `allow_dogmatic` field is decorative (never enforced in __post_init__).
- F6: `consensus()` left-fold for N>2 is order-sensitive at floating-point precision.
- F8: `to_beta_evidence` rejects dogmatic; `from_evidence` cannot produce them. Asymmetric.
- F13: Duplicate code paths in `p_arg_from_claim`.
- F14: Provenance status `CALIBRATED` lied for synthetic defeat-summary opinions.
- F17: `analyze_sensitivity` returns None for many distinct failure modes.
- F18: Elasticity blows up near zero output.
- F19: `combine_fragility(product)` unmotivated.
- F20: `score_conflict()` heuristic, no citation.
- F21: `weighted_epistemic_score` silently falls back to uniform on missing indices.
- F26: ECE uses fixed-width bins only.
- F28: `CorpusCalibrator` magic constants.
- F29: `categorical_to_opinion` provenance bookkeeping for vacuous cases.
- F30: `TemperatureScaler.fit` no diagnostics.

### LOW

- F2 (downgraded): consensus_pair base rate IS algebraically equivalent — not a bug.
- F7: `discount` math correct.
- F9: `_quantized` hash invariance not property-tested.
- F10: `_BASE_RATE_CLAMP` inconsistent across consensus / WBF / CCF.
- F11: `ccf` self-fusion edge case correct.
- F15: `PropstorePrAF` mutable fields on frozen dataclass.
- F22: `_SECTION_FRAGILITY` magic table.
- F23: `imps_rev` strict precondition.
- F24: `opinion_sensitivity` finite-difference correctness.
- F27: ECE bin boundary handling.
- F31: `_softmax` no NaN guard.
- F32: SQLite schema has no `b+d+u=1` CHECK.

## Missing features

Drift from cited literature:

- **Multinomial opinions** — Josang_2010, Vasilakes_2025, vdH 2018 all use k-nomial opinions. propstore is binomial-only. Means propstore cannot represent claims with >2 categories without splitting. The Vasilakes_2025 SLE work is directly applicable to LLM annotator-disagreement encoding (ground for many propstore use cases) and is not implemented.
- **CBF / ABF / BCF** — vdH 2018 corrected three multi-source operators. Only WBF and CCF implemented.
- **Cumulative belief fusion (Vasilakes Eq. 3)** — explicitly cited in subjective-logic.md but not implemented.
- **Maximum entropy probability function (Thimm_2012, Hunter_2017)** — central probabilistic-AF construction; not implemented.
- **Epistemic rationality postulates beyond COH** (RAT, FOU, SFOU, OPT, INV, NEU, MAX, MIN, JUS, TER) — none enforceable.
- **Inconsistency measures + consolidation** (Hunter_2017 §5-6) — not implemented.
- **Riveret_2017 ON/OFF/IN/OUT/UN labelling** — not implemented; project uses standard Dung labels with separate existence probabilities.
- **Sobol indices / global sensitivity** (Ballester-Ripoll_2024).
- **Linear fractional sensitivity** (Coupé_2002 Prop 4.1) — even local sensitivity could exploit this for closed-form a/b/c/d constants from 3 BN evaluations; instead propstore uses sympy `diff`.
- **Brier score, log-loss, MCE, reliability diagrams, adaptive ECE** (Guo_2017 + standard).
- **Kaplan_2015 partial-observable update** — not implemented.
- **Trust transitivity chains** — `discount()` is single-hop; multi-hop chains require recursive discounting or matrix forms.
- **Hyper-opinions** (vdH 2018 Def 2) — needed to handle reduced-power-set focal elements.
- **Causal sensitivity** (Pearl_2000, Halpern_2000/2005, Chan_2005) — none of the causal-influence machinery is wired into the sensitivity analyzer.
- **Information value / Howard_1966** — value-of-information for prioritizing measurements is missing; `collect_missing_measurement_interventions` uses a downstream-count heuristic instead.
- **Walley_1996 imprecise probability** — propstore's `_BASE_RATE_CLAMP` is essentially a poor-man's interval probability; the principled solution would be Walley's framework.
- **Gardenfors_1982 unreliable probabilities** — relevant for opinion ordering policies; not cited in code.
- **Shafer_1976 / Shenoy_1990** — Dempster-Shafer foundations; only the consensus operator inherits from this lineage. No belief-function propagation engine.
- **Denoeux_2018 decision-making** — `apply_decision_criterion` covers pignistic / lower / upper / hurwicz but NOT interval dominance, E-admissibility, or maximin regret. Doc admits this (subjective-logic.md:234).

## Open questions for Q

1. Is the `_BASE_RATE_CLAMP = (0.01, 0.99)` deviation from vdH 2018 Def 4 acceptable as project convention, or should fusion REQUIRE a shared base rate (raising on mismatch) to follow the paper exactly? It currently silently re-prioritizes claims toward the average prior.

2. Should `_defeat_summary_opinion()` exist at all? It manufactures (b, d, u) from a scalar p without empirical evidence — directly contradicts the "honest ignorance over fabricated confidence" principle the calibrate module insists on. The natural alternative is to return `Opinion.vacuous(a=p)` and let downstream callers compute `expectation = p` directly.

3. Should `from_probability(confidence, 1, a)` in `p_relation_from_stance()` use `n=1` (fixed) or expose effective sample size as a stance-level field? Currently a stance with confidence=0.5 emits expectation=0.6, which is mathematically correct but operationally surprising.

4. Multinomial / hyper-opinion support: is propstore's binomial-only restriction permanent, or should we plan migration to k-nomial via the Vasilakes_2025 / vdH 2018 framework?

5. Should `enforce_coh()` raise (or surface a `COHNotConverged` result) when the 100-iteration fixpoint exits without convergence, instead of silently returning a partially-enforced PrAF?

6. Brier score and log-loss (as standalone calibration metrics) — gap, or intentional? Both are trivial to add and standard in calibration practice.

7. Sobol / global sensitivity — there's a paper with notes (Ballester-Ripoll_2024) but no code. Was a planning artifact already drafted?

8. The directory `papers/Josang_2010_CumulativeAveragingFusionBeliefs/` contains the **multiplication** paper, not the cumulative/averaging fusion paper (notes.md line 6 explicitly warns). The actual cumulative/averaging fusion paper is missing from the corpus, yet `wbf()` documentation references vdH 2018 which itself corrects Josang 2010 CBF/ABF formulas — so there is a bibliography hole.

9. Is the `allow_dogmatic` field meant to be an enforced gate or just provenance metadata? Currently it is referenced in three constructors but never validated by `__post_init__`.

10. `combine_fragility()` is exported at the module top level (`fragility.py:259`) but never called within the codebase. Dead API or planned future use?

---
End of cluster-F review.
