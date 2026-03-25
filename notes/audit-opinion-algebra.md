# Audit: Subjective Logic / Opinion Algebra Implementation

**Date:** 2026-03-24
**Auditor:** Analyst (Gauntlet protocol)
**Scope:** `propstore/opinion.py`, `propstore/calibrate.py`, `propstore/sensitivity.py` and their test files
**Reference literature:** Josang 2001, Guo et al. 2017, Sensoy et al. 2018, Denoeux 2019

---

## Summary

The core opinion algebra is well-implemented and closely follows Josang 2001. The consensus, discounting, conjunction, disjunction, and negation operators match the paper formulas. However, there are several issues ranging from minor to significant, primarily around edge cases, missing invariant enforcement on operator outputs, and gaps in the calibration-to-argumentation pipeline.

---

## Findings

### FINDING 1 [MEDIUM]: Base rate `a` excludes boundary values 0 and 1, but Josang allows a in [0,1]

**File:** `C:/Users/Q/code/propstore/propstore/opinion.py`, line 37-38
**Code:** `if self.a <= 0.0 or self.a >= 1.0: raise ValueError`
**Paper says:** Josang 2001 Def 9 (p.7) specifies `0 <= a <= 1`. The restriction to open interval (0,1) is a design choice, not a paper requirement.
**Impact:** Prevents representing propositions that are certain a priori (a=1) or impossible a priori (a=0). The docstring on line 26 says `a in (0,1)` which is at least self-consistent, but the notes.md for the paper (line 208) also says `a: (0,1)`. This may be intentional to avoid division-by-zero in downstream formulas (e.g., uncertainty maximization). If intentional, it should be documented as a deliberate restriction with rationale, not implied to be the paper's definition.

### FINDING 2 [MEDIUM]: Operator outputs are not clamped or re-validated against the b+d+u=1 invariant

**File:** `C:/Users/Q/code/propstore/propstore/opinion.py`, lines 91-105 (conjunction, disjunction)
**Issue:** The `__and__` and `__or__` operators construct `Opinion(b, d, u, a)` which triggers `__post_init__` validation. However, floating-point arithmetic can cause the sum b+d+u to drift slightly from 1.0. The tolerance `_TOL = 1e-9` should catch most cases, but:
- No explicit clamping of negative values to 0 is performed. If floating-point error produces `b = -1e-12`, the constructor will reject it (the check is `val < -_TOL`). This means operations on extreme inputs could fail with a confusing `ValueError` from the constructor rather than being gracefully handled.
- The tolerance check allows values slightly outside [0,1] (up to `1e-9` out of bounds), but does not normalize them back in. This means an opinion could technically have `b = 1.0 + 5e-10` which passes validation but violates the mathematical invariant.

### FINDING 3 [LOW]: Consensus base rate fallback averages when both uncertainties are equal

**File:** `C:/Users/Q/code/propstore/propstore/opinion.py`, lines 176-179
**Code:** When `denom_a` (= `u_A + u_B - 2*u_A*u_B`) is near zero, the code averages base rates.
**Issue:** `denom_a = 0` happens when `u_A + u_B = 2*u_A*u_B`, i.e., `1/u_A + 1/u_B = 2`, which means `u_A = u_B = 1` (both vacuous). In this case averaging base rates is reasonable. But the condition `abs(denom_a) < _TOL` could also fire for near-equal non-vacuous uncertainties if `u_A*(1-u_B) + u_B*(1-u_A)` is tiny. The averaging fallback is a pragmatic choice but not documented as deviating from the paper formula.

### FINDING 4 [HIGH]: `CorpusCalibrator.to_opinion` uses full corpus size as effective sample size -- produces near-dogmatic opinions

**File:** `C:/Users/Q/code/propstore/propstore/calibrate.py`, lines 134-143
**Code:** `from_probability(p, float(self._n))` where `self._n` is the number of reference distances.
**Issue:** If the corpus has 10,000 reference distances, this creates an opinion with `n=10000`, giving `u = 2/(10000+2) = 0.0002`. This is extremely low uncertainty -- essentially dogmatic. But the 10,000 reference points tell you about the *corpus distribution*, not about the *truth of the current claim*. A corpus CDF calibration tells you "this distance is at the 30th percentile of my corpus," not "I have 10,000 pieces of evidence for this claim."

The Sensoy 2018 mapping (p.3-4) uses evidence counts that represent actual observations supporting a class. The corpus size is not evidence for the claim; it's evidence for the calibration of the distance metric. Using it as `n` in `from_probability` conflates calibration confidence with claim-level evidence.

**Consequence:** Claims processed through `CorpusCalibrator.to_opinion` will have artificially tiny uncertainty, making them appear near-dogmatic even when the underlying similarity judgment is weak.

### FINDING 5 [MEDIUM]: `from_probability(p, n)` does not validate p in [0,1] or n >= 0

**File:** `C:/Users/Q/code/propstore/propstore/opinion.py`, lines 157-162
**Issue:** The function `from_probability` accepts arbitrary floats. If `p > 1` or `p < 0`, the resulting evidence counts `r = p*n` or `s = (1-p)*n` could be negative, which `BetaEvidence.__post_init__` would catch for `s` (since `1-p < 0` when `p > 1`) but not for `r` when `p < 0` and `n > 0` (since `r` would be negative). The `calibrated_probability_to_opinion` wrapper in `calibrate.py` does validate, but the core `from_probability` function in `opinion.py` does not.

### FINDING 6 [LOW]: Discount operator b+d+u sum verification

**File:** `C:/Users/Q/code/propstore/propstore/opinion.py`, lines 196-202
**Verification:** `b + d + u = trust.b*source.b + trust.b*source.d + trust.d + trust.u + trust.b*source.u = trust.b*(source.b + source.d + source.u) + trust.d + trust.u = trust.b + trust.d + trust.u = 1`. This is correct.

### FINDING 7 [MEDIUM]: Disjunction base rate formula `a_x + a_y - a_x*a_y` is the independent-union formula, not Josang's Eq.4 relative atomicity

**File:** `C:/Users/Q/code/propstore/propstore/opinion.py`, line 104
**Issue:** The paper's Theorem 4 (p.14-15) says `a_{x OR y} = a_{x OR y}` (derived via Eq. 4 from the product frame). The code uses the inclusion-exclusion formula `a_x + a_y - a_x*a_y`. This is correct for independent binary frames with uniform prior (since the product frame has |Theta_X x Theta_Y| = 4 states and x OR y covers 3 of them, so a = 3/4 when a_x = a_y = 0.5, and indeed 0.5 + 0.5 - 0.25 = 0.75). However, the general Eq.4 formula involves weighted atomicities that may differ from this simple form when frames are not uniformly weighted. For the binary independent case the code is correct.

### FINDING 8 [LOW]: No `__repr__` or `__str__` on Opinion or BetaEvidence

**File:** `C:/Users/Q/code/propstore/propstore/opinion.py`
**Impact:** Debugging difficulty only. The `@dataclass(frozen=True)` provides a default repr.

### FINDING 9 [MEDIUM]: Sensitivity analysis has no connection to opinion algebra

**File:** `C:/Users/Q/code/propstore/propstore/sensitivity.py`
**Issue:** The sensitivity module computes partial derivatives and elasticities for SymPy parameterization formulas. It has no connection to subjective logic opinions. It operates on bare float values from claims. This means sensitivity analysis ignores uncertainty entirely: "concept1 has value 200 with high confidence" and "concept1 has value 200 with total ignorance" are treated identically. There is no propagation of opinion uncertainty through the sensitivity analysis.

### FINDING 10 [HIGH]: No schema-level enforcement of opinion invariants in SQLite

**File:** `C:/Users/Q/code/propstore/tests/test_opinion_schema.py`
**Issue:** The schema test verifies that opinion columns exist in `claim_stance` and that values round-trip. But there is no CHECK constraint in the schema enforcing `opinion_belief + opinion_disbelief + opinion_uncertainty = 1.0` or that values are in [0,1]. The columns accept NULL (for backward compat, which is correct) but when non-NULL, nothing prevents inserting `(b=0.9, d=0.9, u=0.9, a=0.5)` which violates b+d+u=1.

### FINDING 11 [MEDIUM]: ECE binning edge case for confidence = 1.0

**File:** `C:/Users/Q/code/propstore/propstore/calibrate.py`, line 273
**Code:** `idx = min(int(conf * n_bins), n_bins - 1)`
**Issue:** This correctly handles `conf = 1.0` by clamping to the last bin. However, `conf = 0.0` maps to bin 0 which is correct. The edge case `conf = 1.0/n_bins` maps to `int(1.0) = 1` which is bin 1, but it should arguably be in bin 0 since the bin boundaries are `[0, 1/n_bins)`. This is the standard binning ambiguity and is fine for practical purposes.

### FINDING 12 [MEDIUM]: Temperature scaling `fit()` search range is hardcoded to [0.01, 10.0]

**File:** `C:/Users/Q/code/propstore/propstore/calibrate.py`, line 79
**Issue:** If the optimal temperature is outside [0.01, 10.0], the fit will silently return a suboptimal result. For severely miscalibrated models (e.g., very high logit magnitudes), T > 10 may be needed. The function gives no warning when the optimum is at a boundary.

### FINDING 13 [LOW]: `fit()` assumes NLL is unimodal in [0.01, 10.0]

**File:** `C:/Users/Q/code/propstore/propstore/calibrate.py`, lines 64-97
**Issue:** Golden section search is correct for unimodal functions. Guo et al. 2017 (p.5) notes that NLL w.r.t. T is convex, so this is fine. But the code uses `max(p, 1e-15)` clipping which slightly modifies the function at extremes.

### FINDING 14 [MEDIUM]: `categorical_to_opinion` hard-codes category set and base rates

**File:** `C:/Users/Q/code/propstore/propstore/calibrate.py`, lines 151-156
**Code:** `_DEFAULT_BASE_RATES = {"strong": 0.7, "moderate": 0.5, "weak": 0.3, "none": 0.1}`
**Issue:** These base rates are undocumented -- they are not derived from any paper. The Josang framework says base rate should reflect prior probability. These magic numbers would need empirical justification. The docstring says "corpus frequency priors" but there is no evidence of corpus frequency measurement.

### FINDING 15 [HIGH]: Consensus fusion with one vacuous opinion should return the other opinion (identity element), but does not exactly

**File:** `C:/Users/Q/code/propstore/propstore/opinion.py`, lines 165-183
**Verification by formula:** Let A be vacuous: `(0, 0, 1, a_A)`. Then:
- `kappa = 1 + u_B - 1*u_B = 1`
- `b = (0*u_B + b_B*1) / 1 = b_B`  (correct)
- `d = (0*u_B + d_B*1) / 1 = d_B`  (correct)
- `u = (1*u_B) / 1 = u_B`  (correct)
- `denom_a = 1 + u_B - 2*1*u_B = 1 - u_B`
- If u_B != 1: `a = (a_B*1 + a_A*u_B - (a_A + a_B)*u_B) / (1 - u_B) = (a_B + a_A*u_B - a_A*u_B - a_B*u_B) / (1 - u_B) = a_B*(1 - u_B) / (1 - u_B) = a_B`  (correct)
- If u_B == 1 (both vacuous): denom_a = 0, falls to average. This means fusing two vacuous opinions with different base rates averages their base rates, which is reasonable.

So the identity element property holds. Good -- no issue here. Retracting this as a finding.

---

## Test Coverage Gaps

### GAP 1: No test for consensus with vacuous opinion as identity element

**Files:** `C:/Users/Q/code/propstore/tests/test_opinion.py`
**Missing:** `consensus_pair(vacuous, x) == x` and `consensus_pair(x, vacuous) == x`. The tests check discounting with vacuous trust but not consensus with vacuous operand as identity.

### GAP 2: No test for conjunction/disjunction with vacuous opinions

**Missing:** What does `vacuous & x` produce? What does `vacuous | x` produce? These are important edge cases for the argumentation layer where some propositions may lack evidence.

### GAP 3: No test for conjunction/disjunction b+d+u=1 invariant after operation

**Missing:** While `test_conjunction_produces_valid_opinion` and `test_disjunction_produces_valid_opinion` exist, they only test one case each. No systematic property-based testing.

### GAP 4: No test for `from_probability` with invalid inputs (p < 0, p > 1, n < 0)

**File:** `C:/Users/Q/code/propstore/tests/test_opinion.py`
**Missing:** The function `from_probability` in `opinion.py` does not validate inputs. No test verifies behavior for invalid inputs.

### GAP 5: No test for ECE with empty input

**File:** `C:/Users/Q/code/propstore/tests/test_calibrate.py`
**Partial:** The code returns 0.0 for empty input (line 263-264 of calibrate.py), but no test covers this.

### GAP 6: No test for `CorpusCalibrator` with single reference distance

**Missing:** Edge case where the corpus has exactly one reference point.

### GAP 7: No test for consensus associativity with different base rates

**File:** `C:/Users/Q/code/propstore/tests/test_opinion.py`
**Missing:** The associativity test (class `TestConsensusAssociative`) only tests opinions with `a=0.5`. When base rates differ, associativity of the base rate fusion formula is worth verifying separately.

### GAP 8: No test for discount with full trust (b=1, d=0, u=0)

**Missing:** `discount(dogmatic_true, source)` should return source unchanged. This is a key identity property.

### GAP 9: No negative-path test for `TemperatureScaler.fit()` with mismatched lengths

**Missing:** The code validates `len(logits_list) != len(labels)` but no test covers this error path.

### GAP 10: No test for sensitivity analysis with zero output value (elasticity undefined)

**File:** `C:/Users/Q/code/propstore/tests/test_sensitivity.py`
**Missing:** When `output_value == 0`, elasticity computation skips (returns None). No test verifies this edge case.

---

## Architecture Assessment

### Good

1. `opinion.py` is a pure leaf module with zero propstore imports -- clean dependency structure.
2. Frozen dataclasses prevent mutation of opinion tuples after construction.
3. The consensus formula correctly matches Josang 2001 Theorem 7 (p.25).
4. The discounting formula correctly matches Josang 2001 Def 14 (p.24).
5. The BetaEvidence mapping correctly matches Josang 2001 Def 12 (p.20-21) with W=2.
6. The negation operator correctly matches Josang 2001 Theorem 6 (p.18).
7. The expectation formula correctly matches Josang 2001 Def 6 (p.5).
8. The temperature scaling correctly implements Guo et al. 2017 (p.5).
9. The ECE computation correctly implements Guo et al. 2017 (p.1).
10. Edge case handling for two dogmatic opinions in consensus (raises ValueError) is correct per Josang.

### Concerning

1. **The calibration-to-opinion pipeline conflates corpus statistics with claim evidence** (Finding 4). This is the most architecturally significant issue. A corpus of 10,000 distance measurements is not 10,000 observations supporting a claim.
2. **No opinion propagation through sensitivity analysis** (Finding 9). The sensitivity module is entirely disconnected from the opinion algebra, meaning it cannot answer "how does uncertainty in input X affect uncertainty in output Y?"
3. **Magic base rates in categorical mapping** (Finding 14). The numbers 0.7, 0.5, 0.3, 0.1 are unjustified. Per Josang 2001 (p.8) and the CLAUDE.md principle of honest ignorance, fabricating confidence numbers is exactly what this system is supposed to avoid.
4. **No Denoeux decision criteria implemented**. The Denoeux 2019 paper is cited in CLAUDE.md as grounding the render layer decision criteria (pignistic, Hurwicz, interval), but no such criteria are implemented. Only `expectation()` (which corresponds to the pignistic transform for binary opinions) exists.

---

## Severity Summary

| Severity | Count | Key Issues |
|----------|-------|------------|
| HIGH | 2 | Corpus size as evidence count (F4), No schema constraints (F10) |
| MEDIUM | 6 | a boundary exclusion (F1), no output clamping (F2), sensitivity disconnected (F9), magic base rates (F14), from_probability no validation (F5), hardcoded T range (F12) |
| LOW | 3 | Consensus fallback undocumented (F3), no repr (F8), NLL unimodality assumption (F13) |
| Test Gaps | 10 | See GAP 1-10 above |
