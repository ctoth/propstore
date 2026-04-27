# WS-04: Formal expressions, units, equations, and algorithms

## Review findings covered

- Parameter conflict detection compares raw values rather than canonical units.
- Z3 division guards are conjoined globally, changing `||` and ternary semantics.
- CEL ternary type checking does not enforce boolean tests or branch type agreement.
- Equation equivalence is orientation-sensitive.
- SymPy generation drops the equation left-hand side.
- Algorithm conflict detection treats `ast-equiv` SymPy equivalence as conflict.
- Algorithm unbound-name validation uses all-name extraction as if it were free-variable analysis.
- Bridgman dimensional exceptions are not handled consistently in all propstore call sites.

## Dependencies

- Depends on `ws-02-schema-and-test-infrastructure.md`.
- Should finish before semantic reasoning streams that rely on conditions, parameter conflicts, or equation identity.

## First failing tests

1. Unit-normalized parameter conflicts:
   - Build two parameter claims for the same concept:
     - `200 Hz`
     - `0.2 kHz`
   - Run the main conflict detector path, not only `_values_compatible`.
   - Expected: no conflict after canonical unit normalization.
   - Add the inverse case with genuinely different SI values and assert conflict.

2. Z3 scoped division guard:
   - Condition: `enabled || (1 / x > 0)`.
   - Ask satisfiability/overlap with `enabled == true` and `x == 0`.
   - Expected: satisfiable if the division branch is not evaluated.
   - Add ternary equivalent if CEL supports it: `enabled ? true : (1 / x > 0)`.

3. CEL ternary typing:
   - Non-boolean test: `1 ? true : false` should fail in `check_cel_expr`.
   - Mismatched branches: `cond ? 1 : "x"` should fail in `check_cel_expr`.
   - A valid ternary should still lower to IR/Z3.

4. Equation orientation:
   - `x = y` and `y = x` should normalize to the same semantic key.
   - Conflict detection should not report a conflict for orientation-only reversal.
   - Add a non-equivalent equation pair to prove conflicts still fire.

5. SymPy generator identity:
   - `y = f(x)` and `z = f(x)` must not produce the same equation identity if the caller is comparing full equations.
   - Decide whether `generate_sympy_with_error` is RHS-only by contract; if so, rename/scope it and stop callers from using it as equation identity.

6. Algorithm equivalence:
   - Use an algorithm pair that `ast-equiv` marks `equivalent=True, tier=SYMPY`.
   - Expected: no conflict, unless propstore explicitly documents a stricter "only canonical/bytecode accepted" policy.
   - If stricter policy is desired, rename the result and report "equivalent but not accepted", not a semantic conflict.

7. Free-variable validation:
   - Algorithm body with local temporary assignment:
     - declared inputs: `x`
     - local temp: `y = x + 1`
   - Expected: `y` is not warned as undeclared input.

8. Bridgman exception handling:
   - Feed a mismatched-dimension expression through every propstore dimensions call site.
   - Expected: typed validation diagnostic, not uncaught `DimensionalError`/`TypeError`.

## Production change sequence

1. Unit conflict path:
   - Thread concept form/unit metadata or canonical SI values into `ConflictClaim`.
   - Prefer using already-computed sidecar canonical values if available.
   - Remove raw-value comparison from the main path when units are known.

2. Z3 guard semantics:
   - Represent partial-operation guards inside expression structure, not as a global conjunction.
   - For `and`/`or`, guard only evaluated branches according to logical semantics.
   - For ternary, guard only the selected branch.
   - If that is too complex, reject division in boolean conditions at authoring; do not silently strengthen formulas.

3. CEL checker:
   - Enforce ternary test is boolean.
   - Unify branch types or reject.
   - Make checked CEL the hard boundary before IR/Z3.

4. Equation canonicalization:
   - Canonicalize equation zero sets independent of orientation.
   - Avoid raw `str(sympy_expr)` as the sole semantic key unless sign-normalized and symbol-order-normalized.
   - Keep structural signatures as diagnostics, not the semantic equivalence key.

5. SymPy generation:
   - Split RHS-expression generation from full-equation normalization.
   - Rename APIs if needed so callers cannot mistake RHS text for equation identity.

6. Algorithm equivalence:
   - Treat any dependency result with `equivalent=True` as non-conflict, or introduce a separate policy layer for accepted equivalence tiers.
   - Replace `extract_names` use with a real free-variable extractor from `ast-equiv` or propstore-owned AST analysis.

7. Dimensional validation:
   - Normalize exception handling around `bridgman.DimensionalError`, `TypeError`, and parse errors.
   - Convert them to typed diagnostics at the IO/validation boundary.

## Acceptance gates

- Targeted logged pytest:
  - `powershell -File scripts/run_logged_pytest.ps1 -Label formal-expressions tests/test_conflict_detector.py tests/test_value_comparison_units.py tests/test_cel_checker.py tests/test_equation_comparison.py tests/test_equation_comparison_properties.py`
  - Add focused tests for Z3 scoped guards and algorithm free variables.
- `uv run pyright propstore`
- `uv run lint-imports` if dependency boundary wrappers move.

## Done means

- Parameter conflicts are unit-aware in the main detector.
- CEL checker rejects invalid ternaries before Z3.
- Z3 encoding preserves boolean/branch semantics.
- Equation and algorithm equivalence no longer produce false conflicts.
- Dimensional errors become diagnostics, not uncaught dependency exceptions.
