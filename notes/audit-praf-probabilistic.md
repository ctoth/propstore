# PrAF Probabilistic Argumentation Audit

**Date:** 2026-03-24
**Analyst role (Gauntlet protocol)**
**Scope:** `propstore/praf.py`, `propstore/praf_dfquad.py`, `propstore/praf_treedecomp.py`, `propstore/propagation.py` (excluded -- unrelated SymPy evaluation), plus all test files.

---

## Finding 1: `mc_confidence` parameter is accepted but ignored [MEDIUM]

**File:** `C:/Users/Q/code/propstore/propstore/praf.py`, lines 105, 290, 395

The `compute_praf_acceptance` signature accepts `mc_confidence: float = 0.95` and passes it to `_compute_mc` as the `confidence` parameter. However:

1. The Agresti-Coull stopping criterion on line 375 uses the hardcoded formula `4.0 * p_hat * (1.0 - p_hat) / (epsilon ** 2) - 4.0` which implicitly assumes z=1.96 (95% confidence). The `confidence` parameter is never used to adjust z.
2. The CI half-width computation on line 395 hardcodes `1.96` regardless of the `confidence` parameter.

If a caller passes `mc_confidence=0.99` (z=2.576), the stopping criterion still uses z=1.96 internally, so the actual confidence level delivered does not match what was requested. The Agresti-Coull formula from Li 2012 Eq. 5 is derived specifically for z~2 (95% confidence). For other confidence levels, the formula should be `z^2 * p*(1-p) / epsilon^2` (Li 2012 Eq. 4).

**Impact:** Any non-default `mc_confidence` silently produces incorrect confidence guarantees.

---

## Finding 2: Agresti-Coull stopping checks only convergence of the worst argument, not all arguments [LOW]

**File:** `C:/Users/Q/code/propstore/propstore/praf.py`, lines 370-380

The stopping criterion iterates over arguments and breaks early at the first non-converged argument. This is correct -- it requires ALL arguments to converge before stopping. No issue here on closer inspection.

However, the stopping criterion uses `p_hat = counts[a] / n` which is the raw observed proportion, not the Agresti-Coull adjusted proportion `p_tilde = (counts[a] + 2) / (n + 4)`. Per Li et al. (2012, Eq. 5, p.7), the Agresti-Coull method adjusts the proportion by adding 2 successes and 2 failures. The implementation uses the raw `p_hat` in the stopping formula but calls it "Agresti-Coull." This is a hybrid: the stopping formula structure comes from Agresti-Coull (the `-4` term), but the proportion used is not adjusted.

**Impact:** Minor -- the `-4` correction partially compensates, and the difference only matters for extreme proportions near 0 or 1. But it is technically not a faithful Agresti-Coull implementation.

---

## Finding 3: COH constraint (Hunter & Thimm 2017) is neither enforced nor checked [MEDIUM]

**File:** `C:/Users/Q/code/propstore/propstore/praf.py`

Hunter & Thimm (2017, p.9) define the COH (coherence) constraint: if A attacks B, then P(A) + P(B) <= 1. The propstore implementation does not enforce or even check this constraint on acceptance probabilities.

The test `test_acceptance_probs_sum_constraint` in `test_praf.py` (line 378) explicitly acknowledges this:
```python
# P(a in grounded AND b in grounded) = P(neither defeat) > 0, so
# P(a) + P(b) can exceed 1.
```
The test then only checks `0.0 <= pa <= 1.0` -- it abandoned the COH check.

This is arguably correct for the constellations approach (Li 2012) because COH is a property of the *epistemic* approach (Hunter 2017), not the constellations approach. The two approaches compute fundamentally different things. But the CLAUDE.md lists both papers as grounding, and the code comments reference Hunter & Thimm (2017, Prop 18) for component decomposition. The lack of any COH enforcement or post-hoc validation means the system cannot detect outputs that violate epistemic rationality postulates.

**Impact:** The system may produce acceptance probabilities that are incoherent from Hunter's epistemic perspective. If downstream consumers assume COH holds, they will get wrong answers.

---

## Finding 4: DF-QuAD attribution mismatch -- Freedman 2025 vs Fang 2025 [LOW]

**File:** `C:/Users/Q/code/propstore/propstore/praf_dfquad.py`, lines 1-10

The module docstring and inline citations reference "Freedman et al. (2025, p.3)" throughout. The CLAUDE.md references "Fang et al. 2025" for DF-QuAD. The papers directory contains `Fang_2025_LLM-ASPICNeuro-SymbolicFrameworkDefeasible` (which is about LLM-ASPIC+, not DF-QuAD) and `Freedman_2025_ArgumentativeLLMsClaimVerification` (which IS about DF-QuAD/QBAFs).

The DF-QuAD semantics was originally defined by Rago et al. (2016), "Discontinuity-Free Quantitative Argumentation Debate." Neither Freedman 2025 nor Fang 2025 originated DF-QuAD -- they both USE it. The code cites the user of the algorithm, not the original source.

**Impact:** Traceability only. Does not affect correctness.

---

## Finding 5: Support weights are ignored in DF-QuAD [MEDIUM]

**File:** `C:/Users/Q/code/propstore/propstore/praf_dfquad.py`, line 99

The `supports` parameter is typed as `dict[tuple[str, str], float]` where the float is a weight. However on line 99:
```python
for (src, tgt), _weight in supports.items():
```
The weight is explicitly discarded (`_weight`). The supporters_of adjacency list just records which arguments support which, but the weight is never used in the combine function. The `dfquad_combine` function receives `supporter_strengths` which are the *strengths of the supporting arguments*, not the support edge weights.

This means all support relations are treated as equally strong regardless of the weight provided. If the intent was for support weights to modulate the influence, this is a bug. If the weight was always intended to be ignored (using argument strength alone), the API is misleading by accepting a weight.

**Impact:** Support edge weights are silently discarded. This may produce incorrect strengths in bipolar argumentation frameworks where support relations have varying intensities.

---

## Finding 6: DF-QuAD cycle handling is not guaranteed to converge [LOW]

**File:** `C:/Users/Q/code/propstore/propstore/praf_dfquad.py`, lines 148-159

For cyclic arguments, the code uses iterative fixpoint with max 100 iterations and convergence threshold 1e-9. However:

1. Freedman et al. (2025) assumes acyclic QBAFs. The DF-QuAD aggregation function is only proven to satisfy its properties (monotonicity, contestability, boundedness) for acyclic frameworks.
2. The iterative fixpoint may oscillate for certain cycle structures. There is no guarantee of convergence for cyclic QBAFs under DF-QuAD semantics.
3. If convergence fails (max_delta never drops below 1e-9 within 100 iterations), the function silently returns the last computed values with no warning or error.

**Impact:** For cyclic QBAFs, results may be arbitrary depending on iteration order. No test covers the non-convergent case.

---

## Finding 7: Tree decomposition DP tracks full edge sets -- exponential blowup [MEDIUM]

**File:** `C:/Users/Q/code/propstore/propstore/praf_treedecomp.py`, lines 472-477

The DP table key includes `frozenset[tuple[str, str]]` for active_edges and `frozenset[str]` for present_forgotten. These grow unboundedly as the DP progresses up the tree. The claimed complexity is O(3^k * n) per Popescu & Wallner (2024, Theorem 7), but the actual implementation tracks ALL accumulated edges and ALL forgotten-but-present arguments in the key.

At the root, each row key contains the full set of active edges and all present arguments -- the number of distinct rows is bounded by 2^|defeats| * 2^|args|, which is the brute-force complexity. The tree decomposition is providing NO asymptotic improvement over brute-force enumeration.

The correct Popescu & Wallner DP uses I/O/U labels ONLY on bag arguments (3^k states per bag), with the labelling information from forgotten arguments already "folded in" during forget operations. The implementation here defers grounded labelling to the root (line 660-684), which means ALL configuration information must be preserved until the root -- defeating the purpose of the DP.

**Impact:** The "exact_dp" strategy has the same exponential complexity as "exact_enum". It works correctly (cross-validated by tests) but provides no performance benefit. For medium-sized AFs where auto-dispatch selects exact_dp (>13 args, low treewidth), the performance will be identical to or worse than brute-force due to frozenset overhead.

---

## Finding 8: Component decomposition in MC does not share RNG state correctly [LOW]

**File:** `C:/Users/Q/code/propstore/propstore/praf.py`, lines 304-403

In `_compute_mc`, a single RNG is created from the seed and used sequentially across components (line 362: `_sample_subgraph(comp_praf, rng, comp_args)`). The RNG is shared across components, meaning:

1. `total_samples = max(total_samples, n)` on line 389 takes the max across components, not the sum. This under-reports the true number of samples drawn.
2. Components are processed in `_connected_components` order, which depends on iteration order of `framework.arguments` (a frozenset). On different Python versions or runs, frozenset iteration order may differ, changing which RNG draws go to which component even with the same seed. However, frozensets with the same contents iterate in the same order within a single Python process, so this is only a cross-version concern.

**Impact:** `PrAFResult.samples` reports max-per-component rather than total samples consumed, which is misleading for performance analysis. Reproducibility is maintained within a single Python version.

---

## Finding 9: Exact enumeration counts acceptance of absent arguments [CORRECT]

**File:** `C:/Users/Q/code/propstore/propstore/praf.py`, lines 477-480

In `_compute_exact_enumeration`, line 478: `for a in sampled_args: if a in ext:`. This correctly only counts acceptance for arguments that are present in the sampled sub-framework. Arguments absent from `sampled_args` are correctly excluded from the extension check. This is correct per Li 2012 Def 3.

No issue here.

---

## Finding 10: No test for P_A < 1 in MC sampling [MEDIUM]

**File:** `C:/Users/Q/code/propstore/tests/test_praf.py`

All MC tests use `p_args = {a: Opinion.dogmatic_true() for a in af.arguments}` -- meaning P_A = 1 for all arguments. The MC sampler's argument sampling path (line 258-260 of praf.py: `if rng.random() < p_a: sampled_args.add(a)`) is never exercised with sub-unity argument probabilities in the MC tests.

The tree decomposition tests (`test_treedecomp.py`, `test_uncertain_args`) do test P_A < 1 via exact_dp and exact_enum cross-validation, but the MC path is untested for this case.

**Impact:** If the MC sampling of arguments has a bug (e.g., the < vs <= boundary), it would not be caught by existing tests. The interaction between argument sampling and defeat sampling (defeats filtered by sampled arguments) is also untested under MC for P_A < 1.

---

## Finding 11: `_evaluate_semantics` uses credulous acceptance for multi-extension semantics [OBSERVATION]

**File:** `C:/Users/Q/code/propstore/propstore/praf.py`, lines 181-202

For preferred/stable/complete semantics, the function returns the UNION of all extensions (credulous acceptance). Li et al. (2012, p.4) defines `xi^S(AF, X) = true iff X is justified under S in AF`. The paper considers sets of arguments, but the implementation converts to per-argument acceptance by checking membership in the union.

This means:
- Skeptical acceptance (argument in ALL extensions) is not available.
- For grounded semantics (unique extension), credulous = skeptical, so no issue.
- For preferred/stable, credulous acceptance may over-count: an argument in ANY preferred extension gets credit, even if other preferred extensions exclude it.

This is a design choice, not a bug, but it means the `semantics` parameter behaves differently than Li et al.'s per-set evaluation. The docstring on line 186 correctly documents "credulous acceptance."

---

## Finding 12: Attacks vs Defeats confusion in sampling [LOW]

**File:** `C:/Users/Q/code/propstore/propstore/praf.py`, lines 271-282

`_sample_subgraph` samples defeats probabilistically (correct per Li 2012) but then ALSO filters attacks deterministically (lines 271-277: attacks are included if both endpoints are present, with no probability). Attacks are not in the PrAF definition -- PrAF = (A, P_A, D, P_D) has only defeats.

The `attacks` field on `ArgumentationFramework` appears to be a propstore-specific extension (possibly for ASPIC+ attack/defeat distinction). Since attacks have no P_D entry, they are always included when both endpoints are present. This means attacks are treated as certain, which may or may not be intended.

**Impact:** If the system ever has uncertain attacks (distinct from defeats), they would be silently treated as certain.

---

## Finding 13: No validation that P_D keys match framework.defeats [MEDIUM]

**File:** `C:/Users/Q/code/propstore/propstore/praf.py`, lines 28-42

`ProbabilisticAF` is a frozen dataclass with no `__post_init__` validation. There is no check that:
1. `p_args.keys() == framework.arguments`
2. `p_defeats.keys() == framework.defeats` (or is a superset)

In `_sample_subgraph` line 267: `p_d = praf.p_defeats[(f, t)]` will raise `KeyError` if a defeat exists in the framework but has no corresponding P_D entry.

In `_compute_mc` line 333-336:
```python
comp_p_defeats = {
    d: praf.p_defeats[d] for d in comp_defeats
    if d in praf.p_defeats
}
```
This silently drops defeats that are missing from `p_defeats`. But then `_sample_subgraph` on the component PrAF would still iterate over `comp_praf.framework.defeats` and try to look up `p_defeats[(f,t)]` -- which would raise `KeyError` for any defeat present in the framework but absent from p_defeats.

Wait -- actually no. The `comp_p_defeats` dict is constructed by filtering, and `comp_praf.framework.defeats = comp_defeats`. If a defeat `d` is in `comp_defeats` but `d not in praf.p_defeats`, it will NOT be in `comp_p_defeats`. Then when `_sample_subgraph` iterates over `comp_praf.framework.defeats` and looks up `praf.p_defeats[(f,t)]` -- it uses the ORIGINAL praf, not comp_praf. Wait, line 362: `_sample_subgraph(comp_praf, rng, comp_args)` -- it passes `comp_praf`, so line 267 would access `comp_praf.p_defeats[(f,t)]` which would raise KeyError.

Actually, re-reading more carefully: `_sample_subgraph` iterates `praf.framework.defeats` (line 265), not the arg_subset's defeats. So for comp_praf, it iterates ALL of comp_praf.framework.defeats. If any defeat is missing from comp_praf.p_defeats, KeyError.

**Impact:** If `p_defeats` is constructed with missing entries (which the filtering on line 335 enables), `_sample_subgraph` will crash. The `if d in praf.p_defeats` guard on line 335-336 creates an inconsistency between framework.defeats and p_defeats that will cause KeyError downstream.

---

## Finding 14: No test for empty AF or single-argument AF in main praf.py tests [LOW]

**File:** `C:/Users/Q/code/propstore/tests/test_praf.py`

No test for edge cases:
- Empty AF (no arguments)
- Single argument with no defeats
- Self-attacking argument

These are covered in `test_toy_dp.py` for the toy DP implementation but not for the main `compute_praf_acceptance` dispatch.

---

## Finding 15: DF-QuAD base scores come from P_A, conflating existence probability with intrinsic strength [DESIGN]

**File:** `C:/Users/Q/code/propstore/propstore/praf_dfquad.py`, lines 88-90

```python
base_scores[arg] = praf.p_args[arg].expectation()
```

In Li et al. (2012), P_A(a) is the probability that argument `a` EXISTS. In DF-QuAD (Rago et al. 2016, Freedman 2025), the base score tau(a) is the INTRINSIC STRENGTH of argument `a` (how convincing it is on its own). These are fundamentally different quantities:
- P_A = 0.3 means "this argument probably does not exist"
- tau = 0.3 means "this argument exists but is weak"

Using P_A as the base score means a rarely-occurring argument is treated as an inherently weak argument, which conflates ontological uncertainty with epistemic quality.

**Impact:** DF-QuAD strengths will be wrong for any framework where argument existence probabilities are sub-unity. The DF-QuAD semantics is designed for QBAFs with intrinsic base scores, not for PrAFs with existence probabilities.

---

## Test Coverage Summary

**Well covered:**
- Exact enumeration vs brute force cross-validation (extensive in test_treedecomp.py, test_toy_dp.py)
- DF-QuAD unit tests for aggregate/combine functions
- Property-based testing with Hypothesis (test_toy_dp.py)
- MC convergence and reproducibility
- Component decomposition independence

**Gaps:**
- MC with P_A < 1 (Finding 10)
- DF-QuAD with cycles that do not converge (Finding 6)
- Empty/single-argument AFs through main dispatch (Finding 14)
- Non-default mc_confidence values (Finding 1)
- Support weights actually influencing DF-QuAD output (Finding 5)
- Large AF where exact_dp is selected by auto-dispatch and must perform better than brute force (Finding 7)

---

## Severity Summary

| # | Finding | Severity |
|---|---------|----------|
| 1 | mc_confidence parameter ignored | MEDIUM |
| 2 | Agresti-Coull uses raw p_hat not adjusted p_tilde | LOW |
| 3 | COH constraint not enforced or checked | MEDIUM |
| 4 | DF-QuAD citation mismatch | LOW |
| 5 | Support weights silently discarded | MEDIUM |
| 6 | Cycle convergence not guaranteed, silent failure | LOW |
| 7 | Tree decomposition DP has brute-force complexity | MEDIUM |
| 8 | MC sample count under-reported (max not sum) | LOW |
| 9 | (No issue -- correct) | N/A |
| 10 | No MC test with P_A < 1 | MEDIUM |
| 11 | Credulous acceptance for multi-extension semantics | OBSERVATION |
| 12 | Attacks treated as certain in sampling | LOW |
| 13 | Missing p_defeats keys cause KeyError | MEDIUM |
| 14 | No empty/single-arg test through main dispatch | LOW |
| 15 | P_A conflated with DF-QuAD base score | DESIGN |
