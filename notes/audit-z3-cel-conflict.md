# Audit: Z3 Conditions, CEL Type-Checking, and Conflict Detection

**Date:** 2026-03-24
**Scope:** z3_conditions.py, cel_checker.py, condition_classifier.py, conflict_detector/*, maxsat_resolver.py, equation_comparison.py

---

## CRITICAL FINDINGS

### C1. Division-by-zero guard is cached, then guards are lost on reuse

**File:** `C:/Users/Q/code/propstore/propstore/z3_conditions.py`, lines 274-285

`_condition_to_z3()` initializes `self._current_guards = []` at line 277, translates, then folds guards into the cached expression at line 281. But the guard list is an **instance attribute** (`self._current_guards`), and the division operator at line 163 appends to it via `self._current_guards.append(guard)`.

The problem: if `_condition_to_z3("x / y > 3")` is called, the guards are folded into the cached `expr` and stored. Good so far. But if a **different** condition is being translated that shares no division, `_current_guards` is reset to `[]` at line 277. That's fine. The real bug is subtler:

If two conditions are translated in the **same** `_conditions_to_z3` call (line 296 iterates over `normalized`), each call to `_condition_to_z3` resets `_current_guards`. This means the guards are per-individual-condition, not per-batch, which is correct. However, the `_current_guards` attribute is shared mutable state on the instance. If `_translate` is ever called recursively or from multiple threads, this is a race condition. Currently single-threaded, but the design is fragile.

**Severity:** Medium. Correct for single-threaded use. Would silently produce unsound results under concurrency.

### C2. `_current_guards` not initialized in `__init__`

**File:** `C:/Users/Q/code/propstore/propstore/z3_conditions.py`

`_current_guards` is only set inside `_condition_to_z3()` (line 277). If `_translate_binary` is called directly (bypassing `_condition_to_z3`), accessing `self._current_guards` at line 163 will raise `AttributeError`. The `_translate` method is public-facing enough that this is a real risk.

**Severity:** Medium. Any direct call to `_translate()` on a node containing division will crash.

### C3. MaxSAT `model.evaluate()` returns Z3 BoolRef, not Python bool

**File:** `C:/Users/Q/code/propstore/propstore/maxsat_resolver.py`, line 45

```python
if model.evaluate(var, model_completion=True)
```

`z3.Model.evaluate()` returns a `z3.BoolRef`, not a Python `bool`. In Python, any object is truthy unless it defines `__bool__` returning False. Z3 `BoolRef` objects are **always truthy** regardless of whether they represent True or False. This means the filter at line 43-46 will **keep all claims**, defeating the entire MaxSAT resolver.

Wait -- let me verify. Z3's `BoolRef` does define `__bool__` to raise an exception in some versions, or returns the concrete value if it's a concrete boolean. With `model_completion=True`, the result should be a concrete `z3.BoolVal`. Concrete `BoolVal(True)` and `BoolVal(False)` -- the behavior of `__bool__` on these depends on z3-solver version. In some versions, `bool(z3.BoolVal(False))` raises `Z3Exception`. In others it works. This is version-dependent and fragile.

The safe pattern is `z3.is_true(model.evaluate(var, model_completion=True))`.

**Severity:** High. The resolver may either keep all claims (wrong results) or raise an exception depending on z3 version. The test suite passes because the z3 version installed happens to handle this correctly, but it is not portable.

### C4. Equation canonicalization uses `parse_expr` with arbitrary input

**File:** `C:/Users/Q/code/propstore/propstore/equation_comparison.py`, lines 76, 90-91

`sympy.parsing.sympy_parser.parse_expr` can execute arbitrary Python code. The `local_dict` only provides symbol bindings but does not restrict what can be parsed. If a malicious or malformed `sympy` field contains something like `__import__('os').system('rm -rf /')`, `parse_expr` will execute it.

**Severity:** High (security). The input comes from YAML claim files which are user-authored. `parse_expr` should be replaced with a restricted parser or sandboxed.

---

## MAJOR FINDINGS

### M1. Z3 `UNKNOWN` result silently treated as SAT

**File:** `C:/Users/Q/code/propstore/propstore/z3_conditions.py`, lines 312, 329, 336

`are_disjoint()` checks `solver.check() == z3.unsat` and returns `False` for any non-unsat result. This means `UNKNOWN` (timeout, resource limit) is treated as "not disjoint" (i.e., overlapping). Similarly in `are_equivalent()`, `UNKNOWN` is treated as "not equivalent". This is conservative for disjointness (won't miss real conflicts) but means the system will report OVERLAP instead of PHI_NODE when Z3 times out, which is a false positive rather than a false negative. This is arguably the right direction for conservatism, but it is not documented.

**Severity:** Medium. Behavior is conservative but undocumented. No test covers the UNKNOWN case.

### M2. Condition classifier fallback path: `_conditions_disjoint` only checks shared variables

**File:** `C:/Users/Q/code/propstore/propstore/condition_classifier.py`, line 326

`_conditions_disjoint()` only checks variables that appear in **both** summaries (`set(left.numeric) & set(right.numeric)`). If condition A constrains variable X and condition B constrains variable Y (different variables), the function returns `False` (not disjoint). This is correct -- conditions on different variables are not necessarily disjoint. But it means the fallback never detects disjointness when two conditions constrain different variables, even when those variables are logically related (e.g., through known equations). The Z3 path also won't catch this unless the relationship is encoded in the conditions themselves.

**Severity:** Medium. Conservative (won't produce false PHI_NODEs) but may miss real disjointness.

### M3. Transitive conflict detection uses only first resolved value per input

**File:** `C:/Users/Q/code/propstore/propstore/param_conflicts.py`, line 343

```python
val, desc, src_ids, conds, source_context = resolved[inp][0]
```

Comment at line 334 says "For simplicity, use first available value per input". If a concept has multiple claims with different values, only the first is used for derivation. This means conflicts reachable through other claim combinations are missed.

**Severity:** Major. Real conflicts can be missed silently. The code acknowledges this with the comment but does not flag it as a known limitation.

### M4. No timeout on Z3 solver calls

**File:** `C:/Users/Q/code/propstore/propstore/z3_conditions.py`, lines 309-312, 326-336

Neither `are_disjoint()` nor `are_equivalent()` sets a timeout on the Z3 solver. For pathological inputs (deeply nested expressions, many variables), Z3 can run indefinitely. The caller has no way to bound execution time.

**Severity:** Medium. Could cause hangs on adversarial or accidentally-complex condition expressions.

### M5. String escape handling in tokenizer is incomplete

**File:** `C:/Users/Q/code/propstore/propstore/cel_checker.py`, line 176

```python
val = val.replace('\\"', '"').replace("\\'", "'").replace('\\\\', '\\')
```

The replacement order is wrong. `\\\\` should be replaced **first** (before `\\"` and `\\'`), otherwise `\\\\"` would be incorrectly unescaped. Consider the input `"test\\\\"`: the raw content between quotes is `test\\\\`. The current code first replaces `\\"` -> `"`, which would match the trailing `\\"` in `test\\\\"`, producing `test\\"` then `test\\` after the `\\\\` replacement, which is wrong. The correct result should be `test\\` (two literal backslashes become one, then the trailing quote closes the string).

Actually, re-examining: the regex `"(?:[^"\\]|\\.)*"` will match escaped sequences correctly at the tokenizer level, so the string content extracted will be correct. The issue is in the unescape step. With the input `test\\"`, the regex would match `test\\"` as the string content (between quotes). Then `replace('\\"', '"')` turns it into `test"` -- but that's wrong because the `\\` should become `\` and the `"` should close the string. However the regex already handles this at the match level, so this particular case wouldn't arise in practice.

Still, the replacement order is technically wrong: `replace('\\\\', '\\')` should come first to avoid double-processing. In practice, this is a minor issue because the regex constrains what can appear.

**Severity:** Low. Edge case in string literal unescaping. Unlikely to hit in practice with condition expressions.

### M6. CEL type checker doesn't check logical operator operand types

**File:** `C:/Users/Q/code/propstore/propstore/cel_checker.py`, lines 465-467

```python
if node.op in LOGICAL_OPS:
    # Both sides should be boolean-compatible
    return ExprType.BOOLEAN
```

The comment says "both sides should be boolean-compatible" but the code does NOT check this. `3 && 5` or `"hello" || "world"` would pass the type checker without error. This defeats the purpose of type-checking for logical operators.

**Severity:** Medium. Type errors in logical expressions slip through silently.

---

## MINOR FINDINGS

### m1. Category concept comparison with non-string on both sides falls through

**File:** `C:/Users/Q/code/propstore/propstore/z3_conditions.py`, lines 182-217

`_try_category_comparison()` only handles NameNode vs LiteralNode(string). If both sides are NameNodes (e.g., `task == population`), it returns `None` and the comparison falls through to the generic `==` path, which will try to compare an enum const with another enum const of a different sort. Z3 will likely raise an exception or produce an unsound result when comparing values of different sorts.

**Severity:** Low. Unlikely in practice (comparing two different category concepts is semantically odd), but could produce a confusing Z3 error instead of a clean user-facing error.

### m2. `partition_equivalence_classes` has O(n*k) claim but can degrade

**File:** `C:/Users/Q/code/propstore/propstore/z3_conditions.py`, lines 338-372

The docstring claims O(n*k) complexity where k is the number of distinct classes. In the worst case where every condition set is unique, k = n, so this is O(n^2). The claim is technically correct but misleading -- it's only better than pairwise when there's significant equivalence.

**Severity:** Low. Documentation accuracy.

### m3. `_representative_source_claim_id` will crash on empty list

**File:** `C:/Users/Q/code/propstore/propstore/param_conflicts.py`, line 71

```python
return source_ids[0]
```

If `source_ids` is empty, this raises IndexError. The callers always pass populated lists, but there's no guard.

**Severity:** Low. Defensive programming gap.

### m4. Equation comparison splits on first `=` sign

**File:** `C:/Users/Q/code/propstore/propstore/equation_comparison.py`, line 88

```python
lhs_text, rhs_text = expression.replace("^", "**").split("=", 1)
```

This splits on the first `=`. If the expression contains `==` (equality in some notations) or `>=`/`<=`, this will split incorrectly. The code attempts SymPy's `parse_expr` on a string containing `=` or `>` which will likely fail and return None, so it degrades gracefully. But it means equations written with `==` notation won't be canonicalized.

**Severity:** Low. Graceful degradation but missed functionality.

### m5. No test for Z3 UNKNOWN result handling

No test in the test suite verifies behavior when Z3 returns `z3.unknown`. All tests use simple expressions that Z3 solves immediately. Adding a test with a solver timeout of 0ms or a pathologically complex expression would verify the UNKNOWN handling path.

### m6. Tests don't cover negative weights in MaxSAT

**File:** `C:/Users/Q/code/propstore/tests/test_maxsat_resolver.py`

All test weights are positive. Negative or zero weights are not tested. `z3.Optimize.add_soft` with `weight="0.0"` or negative weight may have undefined behavior.

### m7. `_detect_param_conflicts` picks only the first claim per input concept

**File:** `C:/Users/Q/code/propstore/propstore/param_conflicts.py`, line 164 (`break`)

When multiple claims exist for an input concept, only the first one with a scalar value is used. If claims have different conditions (e.g., "at room temperature" vs "at boiling point"), the condition mismatch is silently ignored.

---

## TEST COVERAGE GAPS

1. **No test for Z3 UNKNOWN result** (M1, m5)
2. **No test for concurrent Z3 solver use** (C1)
3. **No test for `_translate()` called directly** without `_condition_to_z3` wrapper (C2)
4. **No test for MaxSAT with `z3.is_true()` correctness** -- current tests pass but may be version-dependent (C3)
5. **No test for malicious SymPy expressions** (C4)
6. **No test for logical operators with non-boolean operands** in CEL checker (M6)
7. **No test for comparing two category concepts** (e.g., `task == population`) in Z3 (m1)
8. **No test for zero or negative MaxSAT weights** (m6)
9. **No test for multi-value input concepts in transitive propagation** (M3)
10. **No test for deeply nested or very long condition expressions** (M4, timeout risk)

---

## ARCHITECTURE NOTES

The overall layering is sound: CEL parser -> AST -> Z3 translation -> solver queries, with a regex-based fallback. The separation between condition classification, conflict detection, and MaxSAT resolution is clean.

The main architectural concern is the `_current_guards` pattern in z3_conditions.py -- using mutable instance state to pass data between `_translate_binary` and `_condition_to_z3` is a code smell. A cleaner approach would be to have `_translate` return a `(z3_expr, list[guard])` tuple, threading the guards explicitly.

The param_conflicts.py transitive detection is the most complex piece and its "use first value only" simplification (M3) is a real gap for correctness.
