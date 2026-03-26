# Code vs Literature Audit — 2026-03-26

## GOAL
Find concrete implementation bugs, literature divergences, and missing Hypothesis properties.

## FILES READ
- propstore/preference.py (87 lines) — claim strength comparison
- propstore/opinion.py (210 lines) — subjective logic
- propstore/praf.py (931 lines) — probabilistic argumentation
- propstore/argumentation.py (400+ lines) — claim-graph backend
- propstore/dung.py (327 lines) — abstract argumentation
- All test files via subagent (61 files)
- All paper notes via subagent (15+ priority papers)

## KEY FINDINGS

### High-Severity

1. **Grounded extension post-hoc pruning is not a standard semantics** (dung.py:156-213)
   - After computing grounded fixpoint via F_AF on defeats, code removes arguments that attack each other via the attacks relation, then re-iterates.
   - This is not Dung 1995's grounded extension. The standard grounded extension is the least fixpoint of F_AF. Modgil & Prakken 2018 Def 14 says conflict-free should be w.r.t. attacks, but their framework defines F_AF over the defeat relation where defeats already encode preferences. The post-hoc pruning is an ad-hoc reconciliation.
   - Failure mode: Can shrink the grounded extension below the actual least fixpoint. An argument that IS defended by the grounded set w.r.t. defeats gets removed because it attack-conflicts with another grounded member, then the removal cascades.

2. **MC stopping criterion ignores z-score** (praf.py:729-730)
   - Li 2012 Eq. 5: N > z² * p'(1-p') / ε²  (with Agresti-Coull adjustment)
   - Code uses: N > 4 * p'(1-p') / ε² - 4
   - The factor 4 = z²|_{z=1.96≈2}, but the code accepts configurable mc_confidence (0.90, 0.95, 0.99) and computes z via _z_for_confidence() — yet never uses z in the stopping formula.
   - At confidence=0.99, z=2.576, z²=6.635, but code still uses 4. The CI half-width reported uses z correctly (line 751), but stopping uses the wrong threshold.

3. **Exact enumeration double-counts argument-absent worlds** (praf.py:763-815)
   - _compute_exact_enumeration enumerates 2^n_args argument subsets, then for each calls _enumerate_worlds which enumerates 2^|attacks|+|supports| edge configs.
   - But _enumerate_worlds only yields edge configs for edges where BOTH endpoints are in sampled_args. For edges where one endpoint is absent, the probability contribution (1-p) is NOT accumulated.
   - Result: sum of all world probabilities < 1.0 for any PrAF with probabilistic attacks. The acceptance probabilities will be systematically too low.

4. **Opinion conjunction base rate a_{x∧y} = a_x * a_y is wrong for non-independent frames** (opinion.py:98-104)
   - Jøsang 2001 Theorem 3 gives conjunction for independent frames. The code applies it unconditionally. If frames overlap, this silently produces incorrect results.
   - More critically: b + d + u constraint. Let's verify: b = b_x*b_y, d = d_x+d_y-d_x*d_y, u = b_x*u_y + u_x*b_y + u_x*u_y. Sum = b_x*b_y + d_x+d_y-d_x*d_y + b_x*u_y+u_x*b_y+u_x*u_y. This should equal 1.0 given b_x+d_x+u_x=1 and b_y+d_y+u_y=1. Let me check... Actually this IS correct for the independent case. But the code has no guard or warning for dependent frames.

### Medium-Severity

5. **Consensus base rate formula edge case** (opinion.py:183-188)
   - When u_A ≈ u_B (equal uncertainty), denom_a → 0 and code falls back to averaging.
   - But the original Jøsang formula (Theorem 7) for base rate fusion has a different structure. The equal-uncertainty case should use relative atomicity weighting, not simple average. For a_A ≠ a_B with equal u, the average is ad-hoc.

6. **claim_strength defaults create phantom equality** (preference.py:60-86)
   - When a claim has no metadata (no sample_size, no uncertainty, no confidence), it gets [0.0, 1.0, 0.5].
   - Two unrelated claims with no metadata will appear equally strong, so rebuts between them will always succeed (neither strictly weaker). This is defensible but means metadata-free claims always defeat each other on rebuttal, which may not be intended.

7. **COH enforcement is iterative but not guaranteed to converge** (praf.py:137-221)
   - enforce_coh uses proportional scaling with max 100 iterations. For complex attack graphs, proportional scaling can oscillate. No convergence proof. The function silently returns after 100 iterations even if violations remain.

8. **_evaluate_semantics uses credulous acceptance for preferred/stable/complete** (praf.py:518-539)
   - Union of all extensions means an argument is "accepted" if it's in ANY extension. This is credulous, not skeptical. Li 2012 doesn't specify which — but the choice significantly affects acceptance probabilities and is not configurable or documented in the API.

### Literature Divergences

9. **Cayrol derived defeats use fixpoint but reachability is pre-computed once** (argumentation.py:52-112)
   - support_reach is computed once from the original support set (line 72-73). The fixpoint loop adds new defeats but never recomputes support_reach. This is correct because support relations don't change — only defeats grow. But the docstring says "derived defeats can chain" which is about defeat-then-support chains, and those ARE handled by the fixpoint. OK, this is actually correct.

10. **P_A conflated with τ in DF-QuAD** (praf.py:898-930, documented)
    - Li 2012's P_A (argument existence probability) is used as Rago 2016's τ (intrinsic base score) for DF-QuAD. These are conceptually distinct. Documented in code comment but still a semantic error.

## STUCK
- Need to verify exact enumeration probability summation more carefully
- Need to check aspic.py transposition closure against Prakken 2010 Def 12

## NEXT
- Read aspic.py for transposition closure bugs
- Read praf_dfquad.py for DF-QuAD formula verification
- Read calibrate.py for calibration issues
- Compile final four-section report
