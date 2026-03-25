# Audit: Dung AF Semantics Correctness

Date: 2026-03-24

## Scope

Formal correctness of `propstore/dung.py`, `propstore/dung_z3.py`, `propstore/argumentation.py`, and `propstore/preference.py` against Dung 1995 and Modgil & Prakken 2018.

## Files Reviewed

- `C:/Users/Q/code/propstore/propstore/dung.py`
- `C:/Users/Q/code/propstore/propstore/dung_z3.py`
- `C:/Users/Q/code/propstore/propstore/argumentation.py`
- `C:/Users/Q/code/propstore/propstore/preference.py`
- `C:/Users/Q/code/propstore/tests/test_dung.py`
- `C:/Users/Q/code/propstore/tests/test_dung_z3.py`
- `C:/Users/Q/code/propstore/tests/test_preference.py`
- `C:/Users/Q/code/propstore/tests/test_bipolar_argumentation.py`
- `C:/Users/Q/code/propstore/papers/Dung_1995_AcceptabilityArguments/notes.md`

---

## FINDING 1 [MAJOR]: Grounded extension post-hoc attack-CF pruning is not a valid least fixed point

**Location:** `dung.py` lines 126-150

**The problem:** After computing the least fixed point of F (which operates over defeats), the code removes arguments that are in mutual attack (pre-preference) and then re-iterates defense. This post-hoc pruning does NOT produce a valid grounded extension.

The grounded extension per Dung 1995 Def 20 is the least fixed point of F_AF. In a pure Dung AF, attacks=defeats, so this is unambiguous. When attacks and defeats diverge (Modgil & Prakken 2018), the correct approach is to define a NEW characteristic function that incorporates both relations -- not to compute the old F's fixed point and then surgically remove violations.

The post-hoc pruning can produce a set that is:
1. Not a fixed point of ANY well-defined characteristic function
2. Not necessarily admissible w.r.t. the combined attack/defeat structure
3. Dependent on the order of removal (the code removes all attacked-in-ext arguments at once, but different removal orders could yield different results in adversarial cases)

**Concrete scenario where this goes wrong:** Consider arguments {A, B, C} with defeats={(C, B)} and attacks={(A, B), (C, B)}. The defeat-based F converges to {A, C} (A and C are unattacked in defeats, B is defeated by C). Then the attack-CF check finds A attacks B but B is not in ext, so no removal. But now consider defeats={} and attacks={(A, B)}. F converges to {A, B}. The pruning removes B (attacked by A). Then re-defense of {A}: A has no attackers in defeats, so F({A}) = {A, B} again (B still has no attackers in defeats). The code would then loop: remove B, re-compute, get B back, remove B again... Actually examining the code more carefully: the re-defense at lines 143-149 computes `{a for a in s if defends(s, a, ...)}` where s is already pruned, so B would not be in s to defend. So it converges. But the result {A} is not the least fixed point of any standard characteristic function -- it is an ad-hoc construction.

**Deviation from literature:** Modgil & Prakken 2018 define structured argumentation where the attack/defeat distinction is built INTO the framework definitions from the ground up, not bolted on after. The ASPIC+ grounded extension is computed over the defeat relation with the understanding that the defeat relation already correctly encodes all preference information. The implementation's approach of maintaining two separate relations and post-hoc reconciling them is novel and unvalidated.

---

## FINDING 2 [MAJOR]: Z3 complete extension encoding has a subtle formula error for defense direction

**Location:** `dung_z3.py` lines 137-147 (defense constraints)

**The code:** For each argument `a` and each attacker `b` of `a`:
```python
defenders = [d for d in args if (d, b) in defeats]
```

This is correct -- it finds arguments that defeat `b`. However, the constraint:
```python
Implies(v[a], Or(*[v[d] for d in defenders]))
```

says "if a is in S, then some defender of a must also be in S." This encodes admissibility (self-defense), which is correct.

**But the completeness constraint (lines 152-172) has a logic gap.** The completeness constraint says: "if a is defended by S, then a must be in S." The encoding is:

```python
defended_a = And(*defended_parts)  # all attackers have a counter
Implies(defended_a, v[a])         # => a must be in
```

This correctly encodes `defended(a) => in(a)`. Combined with the admissibility constraint (`in(a) => defended(a)`), this gives `in(a) <=> defended(a)`, which is the fixed-point property. This is actually correct.

**However**, I note that the `defended_parts` computation shares the same `defenders` list construction with the admissibility block. If an attacker `b` of `a` has zero counter-attackers, the admissibility block forces `Not(v[a])`, and the completeness block sets `all_defended = False` and skips the implication. These are consistent. No formula error found on closer inspection.

**Downgrade:** This finding is NOT a bug. The Z3 encoding is correct for pure Dung AFs.

---

## FINDING 3 [MAJOR]: Z3 encoding does not use the attacks relation for conflict-free

**Location:** `dung_z3.py` lines 27-37

The `_conflict_free_constraints` function correctly dispatches to `framework.attacks` when available. This is correct.

**But:** The `z3_complete_extensions` and `z3_stable_extensions` functions use `framework.defeats` for defense/stability checks. This matches the brute-force implementation. However, `z3_complete_extensions` does NOT incorporate the `attacks` relation for the fixed-point/completeness constraints. The defense and completeness constraints at lines 137-172 all use `defeats`. This means the Z3 path and the brute-force path should agree, but both share the same conceptual issue as Finding 1 when attacks diverges from defeats.

The Hypothesis property tests (`test_dung_z3.py` lines 91-113) generate frameworks with `attacks=None` (the `argumentation_frameworks` strategy only sets `defeats`), so the Z3-vs-brute-force equivalence is only tested for pure Dung AFs where attacks=defeats=None. The attack/defeat divergence path is NOT property-tested.

---

## FINDING 4 [MODERATE]: Grounded extension iteration uses assignment, not accumulation

**Location:** `dung.py` lines 119-124

```python
s: frozenset[str] = frozenset()
while True:
    next_s = characteristic_fn(s, framework.arguments, framework.defeats)
    if next_s == s:
        break
    s = next_s
```

Per Dung 1995 Theorem 25, the grounded extension is the least fixed point of F, computed as the limit of the sequence F^0({}) = {}, F^1({}) = F({}), F^2({}) = F(F({})), etc. The code does `s = next_s` (replacement), not `s = s | next_s` (accumulation).

For monotone F, this is equivalent because F is monotone (Lemma 19 in Dung 1995): {} <= F({}) <= F(F({})) <= ... Since the sequence is ascending, F^{n+1}({}) is always a superset of F^n({}), so replacement and accumulation produce the same result.

**This is correct.** The property test at `test_dung.py` line 393-400 verifies monotonicity.

---

## FINDING 5 [MODERATE]: Elitist comparison with empty set_b is semantically inverted

**Location:** `preference.py` lines 27-28

`strictly_weaker([1, 2], [], "elitist")` returns `True` because `all(x < y for y in [])` is vacuously true. This means any non-empty strength set is "strictly weaker" than an empty strength set under elitist comparison.

In `defeat_holds`, `rebuts` and `undermines` succeed iff the attacker is NOT strictly weaker. So if the attacker has strengths `[1.0]` and the target has `[]`, the attacker IS strictly weaker (vacuously), so the attack is BLOCKED.

`claim_strength` returns `[1.0]` for empty claims, so `[]` is unreachable from real claim data. But the edge case is tested and accepted (`test_preference.py` line 79), which means the API contract allows it. Any caller passing `[]` as a strength set will get counterintuitive results.

---

## FINDING 6 [MODERATE]: No tests for attacks/defeats divergence in property tests

**Location:** `tests/test_dung.py` lines 34-54

The `argumentation_frameworks` Hypothesis strategy generates AFs with `attacks=None`. All property tests therefore only cover pure Dung AFs. The Modgil & Prakken extension (attacks != defeats) is tested only with concrete examples in `test_bipolar_argumentation.py`, not with property-based testing.

Properties that SHOULD hold but are NOT tested when attacks != defeats:
- Grounded extension is conflict-free w.r.t. attacks
- Grounded extension is a subset of every preferred extension
- Complete extensions are admissible w.r.t. attacks
- Preferred extensions are maximal admissible w.r.t. attacks

---

## FINDING 7 [MODERATE]: Brute-force backends have no size guard

**Location:** `dung.py` lines 172-180, 222-233

The brute-force `complete_extensions` and `stable_extensions` enumerate all 2^n subsets. For n=25 arguments, that is 33 million subsets. For n=30, over 1 billion. No warning, no size limit, no automatic fallback to Z3.

The default backend for `complete_extensions` and `stable_extensions` is `"z3"`, which mitigates this. But `preferred_extensions` and `stable_extensions` accept `backend="brute"` and the brute-force path has no guard. The `grounded_extension` function has no backend parameter at all and always uses the iterative approach (which is fine since iteration is polynomial).

---

## FINDING 8 [MODERATE]: Preference comparison dimensions are not comparable across claims

**Location:** `preference.py` lines 56-89

`claim_strength` returns a list whose LENGTH varies based on which metadata fields are present. A claim with only `sample_size` gets `[log1p(n)]`. A claim with `sample_size` and `confidence` gets `[log1p(n), conf]`. A claim with only `confidence` gets `[conf]`.

`strictly_weaker` compares these lists element-by-element, but the elements have NO alignment. `claim_strength({"sample_size": 100})` = `[log1p(100)]` = `[4.62]`. `claim_strength({"confidence": 0.9})` = `[0.9]`. Now `strictly_weaker([4.62], [0.9], "elitist")` = False (4.62 > 0.9), so the sample-size-only claim is NOT weaker. But these are comparing log-scaled sample size against raw confidence -- apples vs oranges.

When both claims have the SAME metadata fields, the dimensions align and comparison is meaningful. When they have DIFFERENT fields, the comparison is semantically nonsensical but will still produce a result without warning.

This is documented implicitly ("Missing signals are omitted -- only dimensions with data are included") but the implication for cross-claim comparison is not addressed.

---

## FINDING 9 [MINOR]: `_extract_extension` may mishandle z3 don't-care variables

**Location:** `dung_z3.py` lines 40-45

```python
return frozenset(a for a, var in v.items() if model[var])
```

When Z3 does not assign a value to a variable (don't-care), `model[var]` returns `None`, which is falsy. This means don't-care arguments are excluded from extensions. For stable and complete extensions, all variables should be forced by constraints, so this is unlikely to matter. But it is fragile -- a missing constraint could silently produce wrong results by excluding arguments that should be included.

---

## FINDING 10 [MINOR]: `_block_solution` produces empty Or when no arguments exist

**Location:** `dung_z3.py` lines 48-60

When `v` is empty (no arguments), `clause_parts` is empty, and `Or(*[])` is called. Z3 handles `Or()` with no arguments by returning `False`, which would make the solver unsatisfiable immediately after the first (empty) solution. This is actually correct behavior for an empty AF (one solution: empty set, then block it, then no more solutions). But it relies on Z3 implementation behavior.

The functions guard for empty AFs at the top (`if not framework.arguments: return [frozenset()]`), so this path is unreachable.

---

## FINDING 11 [MINOR]: Missing `grounded` semantics in Z3 acceptance queries

**Location:** `dung_z3.py` lines 239-252

`_extensions_for_semantics` dispatches to stable, complete, and preferred but not grounded. Calling `credulously_accepted(af, "A", semantics="grounded")` raises `ValueError`. The grounded extension is always unique, so credulous/skeptical collapse to the same check, but the API is incomplete.

---

## FINDING 12 [INFO]: Cayrol derived defeats now iterate to fixpoint

**Location:** `argumentation.py` lines 73-97

The prior analyst review (in `notes-analyst-dung-review.md`, Finding 4) flagged Cayrol derived defeats as single-pass. The current code has a `while True` loop with `working_defeats` accumulation and a `if not new_derived: break` termination. The test at `test_bipolar_argumentation.py` line 130-140 (`test_cayrol_derived_defeats_chain_transitively`) now asserts that `("A", "D")` IS in derived, confirming multi-pass chaining works. This prior finding appears to be resolved.

---

## FINDING 13 [INFO]: Complete extension definition reference is wrong

**Location:** `dung.py` line 162

The docstring says "Reference: Dung 1995, Definition 10." Dung 1995 Definition 10 is actually about "admissible sets containing at least one preferred extension" (or similar). The complete extension is Definition 23 (p.329). The paper notes confirm: "Definition 23: Complete Extension" on p.329.

---

## Summary

| # | Severity | Description |
|---|----------|-------------|
| 1 | MAJOR | Grounded extension post-hoc attack-CF pruning is ad-hoc, not a valid least fixed point |
| 2 | -- | (Downgraded: Z3 defense encoding is actually correct) |
| 3 | MAJOR | Z3 path and brute-force path share attack/defeat divergence issue; property tests don't cover it |
| 4 | -- | (Grounded iteration is correct: monotone F makes replacement=accumulation) |
| 5 | MODERATE | Elitist comparison with empty set_b is vacuously true (unreachable but API-visible) |
| 6 | MODERATE | No property tests for attacks!=defeats divergence |
| 7 | MODERATE | Brute-force backends have no size guard (2^n enumeration) |
| 8 | MODERATE | claim_strength dimensions are not aligned across claims with different metadata |
| 9 | MINOR | Z3 model extraction relies on None being falsy for don't-care vars |
| 10 | MINOR | Empty Or in _block_solution (unreachable due to guard) |
| 11 | MINOR | Z3 acceptance queries missing grounded semantics |
| 12 | INFO | Cayrol fixpoint iteration is now correct (prior finding resolved) |
| 13 | INFO | Complete extension docstring references wrong definition number |
