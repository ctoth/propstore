# Literature vs Code Audit — 2026-03-25

## Files Read So Far
- propstore/opinion.py — Jøsang 2001 implementation
- propstore/dung.py — Dung 1995 AF + extensions
- propstore/argumentation.py — Claim-graph backend, Cayrol 2005, ASPIC+ bridge
- propstore/preference.py — Modgil & Prakken 2018 Def 9/19
- propstore/praf.py — Li 2012 PrAF, MC sampler, exact enum
- propstore/praf_dfquad.py — Freedman 2025 DF-QuAD
- propstore/calibrate.py — Guo 2017, Sensoy 2018

## Still Need to Read
- propstore/praf_treedecomp.py — Popescu 2024
- propstore/world/atms.py — de Kleer 1986
- propstore/world/labelled.py — de Kleer 1986 labels
- propstore/structured_argument.py — ASPIC+ projection

## Findings So Far

### Confirmed Bugs
1. **dung.py grounded_extension post-hoc pruning (lines 126-150)**: After computing the grounded fixpoint over defeats, the code removes arguments that attack each other via pre-preference attacks, then re-iterates defense. This is NOT how Dung 1995 or Modgil & Prakken 2018 define grounded extensions. The grounded extension is the least fixed point of F — period. The post-hoc attack-conflict-free pruning is a non-standard modification that can produce results that are neither the grounded extension of (Args, Defeats) nor of (Args, Attacks). The code's own design note at argumentation.py:117-122 acknowledges this.

2. **praf.py Agresti-Coull stopping criterion (line 387)**: The formula used is `N > 4*p*(1-p)/eps^2 - 4` but this doesn't incorporate the z-score/confidence level at all. Li 2012 Eq. 5 states the Agresti-Coull interval half-width is `z * sqrt(p'(1-p')/(n+z^2))` where p' = (x + z^2/2)/(n + z^2). The current stopping criterion ignores the confidence parameter entirely — it's hardcoded to some specific confidence level embedded in the "4" constants.

3. **praf.py exact_enum (line 486-488)**: When building sub_af for exact enumeration, the code does NOT pass the attacks parameter: `ArgumentationFramework(arguments=sampled_args, defeats=sampled_defeats)`. This means the sub-AF has attacks=None, so conflict-free checking falls back to defeats only. But the original AF may have had attacks != defeats. This inconsistency means exact_enum and MC may produce different results on the same PrAF when attacks != defeats.

### Likely Literature Misimplementations
1. **preference.py Def 19 elitist comparison**: The code implements `any(all(x < y for y in set_b) for x in set_a)` — "EXISTS x in A such that FORALL y in B, x < y". But Modgil & Prakken 2018 Def 19 elitist ordering states A <_e B iff the BEST element of A is strictly less than the BEST element of B (max comparison). Need to verify exact text.

2. **opinion.py disjunction base rate (line 104)**: `a = self.a + other.a - self.a * other.a`. Jøsang's disjunction base rate formula is more complex for general cases. Need to verify whether this is the independent-frame special case.

3. **praf_dfquad.py conflation of P_A with base score**: The design note at praf.py:543-544 already flags this. P_A (existence probability for MC sampling) is used as τ (intrinsic strength for DF-QuAD). These are conceptually distinct per Freedman 2025 and Li 2012.

### Missing/Misleading Citations
1. **argumentation.py line 1-7**: Claims "not full structured ASPIC+" but the module is still called from resolution paths that may claim ASPIC+ semantics to users.

2. **praf.py line 387**: Cites "Li 2012, Eq. 5, p.7" but the implemented formula doesn't match.

## Additional Files Read
- propstore/praf_treedecomp.py — Popescu 2024 tree decomp DP
- propstore/structured_argument.py — flat ASPIC+ projection
- propstore/world/labelled.py — de Kleer 1986 labels
- propstore/world/atms.py — ATMS engine
- papers/Josang_2001 notes — verified consensus, discount, conjunction, disjunction formulas
- papers/Cayrol_2005 notes — verified Def 3 (supported/indirect defeat)

## Verification Results
- RED tests (test_mc_confidence_affects_ci_width, test_component_praf_with_missing_p_defeats_keys, test_component_p_defeats_mismatch_direct) all PASS now — bugs were fixed
- test_render_time_filtering.py — all 14 PASS — vacuous pruning bug also fixed
- Jøsang consensus base rate formula: CODE MATCHES PAPER exactly (Theorem 7, p.25)
- Jøsang discount operator: CODE MATCHES PAPER exactly (Def 14, p.24)
- Jøsang conjunction/disjunction: CODE MATCHES PAPER for independent frames (Theorem 3-4, p.14-15)
- Cayrol Def 3 (supported/indirect defeat): code correctly implements both types with fixpoint

## Confirmed Bug: Cayrol derived defeats missing from attacks
argumentation.py:167-175 — derived defeats are added to `defeats` but NOT to `attacks`.
Cayrol 2005 Def 6 says conflict-free uses set-defeats (which includes derived defeats).
Modgil & Prakken 2018 Def 14 says conflict-free uses attacks (pre-preference).
Since derived defeats represent structural conflict through support chains, they should be in
the attacks set. Without this, dung.py's attack-based conflict-free check misses derived
conflicts. Same bug in structured_argument.py:183-184.

## Confirmed Bug: Agresti-Coull stopping ignores confidence
praf.py:387 — `required_n = (4.0 * p_hat * (1.0 - p_hat)) / (epsilon ** 2) - 4.0`
The "4" constants embed z²=4 (z=2), ignoring the mc_confidence parameter.
For mc_confidence=0.99 (z=2.576, z²=6.635), the stopping criterion is too lenient —
stops too early. The CI COMPUTATION at line 407-408 uses the correct z via
_z_for_confidence(), but the stopping criterion doesn't match. Result: the MC
terminates as if 95% confidence but reports a 99% CI width — the guarantee is violated.

## Confirmed Bug: exact_enum drops attacks
praf.py:485-488 — `ArgumentationFramework(arguments=sampled_args, defeats=sampled_defeats)`
does NOT pass attacks. MC sampling at line 291-294 DOES pass attacks. This means exact_enum
and MC can produce different results on the same PrAF when attacks != defeats.
Same issue in praf_treedecomp.py:447-450.

## Confirmed Issue: structured_argument.py vacuous pruning (lines 148-151)
Was a bug (violated "no gates before render time" design principle) but the tests now pass,
meaning this was fixed. The `argumentation.py` path never had this pruning.

## Verified Correct
- Jøsang Opinion: all operators match paper formulas
- de Kleer ATMS: label normalization (antichain, nogood filtering) correct per paper
- Dung extensions: grounded/preferred/stable/complete logic correct for pure Dung AF
- Cayrol derived defeats: fixpoint logic correct per Def 3
- Calibration: temperature scaling, ECE correct per Guo 2017
- Evidence-to-opinion: correct per Sensoy 2018 and Jøsang Def 12

## Remaining to Check
- dung.py post-hoc pruning (grounded extension with attacks≠defeats): is this ever triggered in practice?
- praf_dfquad.py P_A conflation with τ: documented but worth including in report
- Whether DF-QuAD combine function matches Freedman 2025 exactly (noisy-OR vs paper formula)
