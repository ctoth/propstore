# Cluster Q: bridgman dependency

Reviewer: Claude (analyst). Date: 2026-04-26. Repo under review: `C:\Users\Q\code\bridgman\` (package `bridgman` v0.1.0, MIT, no required deps, optional `sympy`).

## Scope and purpose

bridgman is a small leaf library doing one job: SI dimensional-exponent arithmetic. The name honours Percy Williams Bridgman, the operationalist whose 1922 *Dimensional Analysis* tied physical meaning to measurement procedure. Despite the operationalist gloss, the library does not encode any operational semantics — it is pure exponent algebra over a fixed alphabet of seven SI base dimensions: `M, L, T, I, Theta, N, J` (`src\bridgman\dimensions.py:11`).

Two modules:
- `dimensions.py` — pure-Python, no deps. Functions: `mul_dims`, `div_dims`, `pow_dims`, `dims_equal`, `is_dimensionless`, `verify_equation`, `format_dims`. Type alias `Dimensions = dict[str, int]`.
- `symbolic.py` — sympy-backed expression-tree walker. Functions: `dims_of_expr`, `verify_expr`. Exception: `DimensionalError`. Imported lazily in `__init__.py`; if sympy missing, stubs raise `SympyRequiredError`.

Tests: 23 in `test_dimensions.py`, 14 in `test_symbolic.py`, 1 in `test_optional_sympy.py`.

## API surface

Re-exported from `bridgman/__init__.py:21-52`:
```
Dimensions, mul_dims, div_dims, pow_dims, dims_equal,
is_dimensionless, verify_equation, format_dims,
SympyRequiredError, dims_of_expr, verify_expr, DimensionalError
```

README documents only `mul_dims`, `div_dims`, `verify_equation` (3 of 11). `pow_dims`, `dims_equal`, `is_dimensionless`, `format_dims`, `Dimensions`, the entire symbolic module, `SympyRequiredError`, and `DimensionalError` are undocumented. The 2026-03-23 notes log lists 7 functions and never mentions `symbolic.py` — symbolic was added later with no log entry.

## Where propstore consumes it

Eight call sites across six files:

1. `propstore\unit_dimensions.py:16` — `from bridgman import dims_equal`. Used by claim-validation to compare a claim's unit dimensions against its concept's form dimensions.
2. `propstore\families\concepts\passes.py:18-19` — imports `mul_dims, div_dims, dims_equal, format_dims, verify_expr, dims_of_expr, DimensionalError`. Heaviest user. Around lines 587-660 it does both sympy-tree verification (`verify_expr`) and a brute-force fallback that combinatorially applies `mul_dims`/`div_dims` over `itertools.product` to check whether some operator string lands on the output dims (passes.py:639-647). Catches `(DimensionalError, KeyError, TypeError, SyntaxError)` and falls through.
3. `propstore\families\claims\passes\checks.py:8` — `import bridgman`. At line 750 calls `bridgman.verify_expr(parsed, dim_map)` for equation claims. At line 773 catches `(KeyError, SyntaxError, bridgman.DimensionalError, TypeError)` and `pass`es silently.
4. `propstore\dimensions.py:166` — `from bridgman import verify_expr`. `verify_form_algebra_dimensions` parses an operation string with sympy and verifies dim_map.
5. `propstore\app\forms.py:166` — `from bridgman import format_dims` for CLI/UI display. Line 190 — `from bridgman import dims_equal` for filter matching. Lazy import wrapped in `try/except ImportError → str(dimensions)` fallback.
6. `propstore\world\model.py:1030` — `from bridgman import dims_equal` inside `forms_by_dimensions` SQL scan.

Net usage: `dims_equal` (4 sites), `verify_expr` (3), `format_dims` (2), `mul_dims`/`div_dims` (1), `DimensionalError` (2), `dims_of_expr` (imported but I did not see a direct call — only `verify_expr` is invoked; `dims_of_expr` is dead-imported in `families/concepts/passes.py:19`).

`pow_dims`, `is_dimensionless`, `Dimensions`, `verify_equation`, `SympyRequiredError` are **never imported by propstore**. `verify_equation` exists for the README example only.

## Bugs

### HIGH-1 — `verify_equation` silently ignores extra `rhs_terms` when `len(ops) != len(rhs_terms)-1`
`src\bridgman\dimensions.py:52-71`. Docstring says "len(ops) must equal len(rhs_terms) - 1" but no precondition check. `verify_equation(lhs, [a, b, c], ["mul"])` iterates only `enumerate(ops)` so `c` is never combined. Worse, `verify_equation(lhs, [a, b], [])` returns `dims_equal(lhs, a)` — comparing only the first term. Should `raise ValueError` if the lengths disagree. Currently no test covers this — the test file has no length-mismatch case.

### HIGH-2 — `dims_of_expr` raises `TypeError` for any unsupported sympy node, and propstore swallows it
`src\bridgman\symbolic.py:112` `raise TypeError(f"Unsupported sympy expression type: {type(expr).__name__}")`. Anything that is not `Symbol|Number|NumberSymbol|Mul|Pow|Add|Eq` hits this: `sin`, `cos`, `exp`, `log`, `Function('f')(t)`, `Derivative`, `Integral`, `Piecewise`, `Min`, `Max`, `Abs`, `KroneckerDelta`. Propstore at `families\claims\passes\checks.py:773` and `families\concepts\passes.py:633` swallows `TypeError`. Result: any equation claim involving a transcendental function silently *passes* dimensional check (no warning recorded). For a knowledge base meant to formalise physics, sin/cos/exp are not exotic — this is silent acceptance of unverified claims.

### HIGH-3 — `pow_dims` accepts non-int `n` and produces invalid Dimensions
`src\bridgman\dimensions.py:35-39`. Signature says `n: int`, no runtime guard. `pow_dims({"L": 1}, 0.5)` returns `{"L": 0.5}`, violating the type alias and breaking downstream `dims_equal` against `int` keys (still works because `0.5 != 1`, but `pow_dims({"L": 2}, 0.5)` returns `{"L": 1.0}` which `==` int 1 — silently mixes float/int dims). Symbolic path uses `_pow_dims_frac` which DOES guard via `denominator != 1 → DimensionalError`. The non-symbolic `pow_dims` is the one with the gap.

### MED-1 — Python 3.9 import failure: `Dimensions = dict[str, int]` at module top level
`src\bridgman\dimensions.py:6`. PEP 585 generic alias usage (`dict[str, int]`) at runtime requires Python 3.9+. Specifically, on Python 3.9 this works as a runtime expression, but on **3.8** would `TypeError`. pyproject says `requires-python = ">=3.9"` so this is technically fine — but `__init__.py` line 33 uses `from typing import TYPE_CHECKING` rather than committing to PEP 604. There is no `from __future__ import annotations` anywhere. This is consistent enough but fragile if `requires-python` ever floats below 3.9. Verdict: not a current bug; latent constraint that should be either documented or pinned with a CI job on 3.9.

### MED-2 — `test_temperature_dimension_symbol_uses_theta_spelling` is cwd-dependent and self-referential
`tests\test_dimensions.py:14-23`. Builds the forbidden token by string concatenation (`"THE" + "TA"`) to evade its own grep, then runs `git grep <forbidden>` against whatever working tree the test happens to be invoked from. Two failure modes:
1. If invoked from a parent directory or unrelated cwd, `git grep` runs against the wrong repo or fails outright. The test asserts `result.stdout == ""` — exit code is unchecked, so a non-git cwd that prints nothing to stdout would *pass*, masking a real violation.
2. If a downstream consumer vendors bridgman tests into their tree, the grep will scan their tree for the forbidden token and false-positive.

### MED-3 — `propstore\families\concepts\passes.py:632` flips `sympy_verified = True` after recording a warning
```
result.warnings.append(...)
sympy_verified = True  # skip brute-force, sympy gave definitive answer
```
This is propstore code, not bridgman, but it depends on a bridgman contract that does not exist: there is no documented guarantee that `verify_expr` returning False means "definitively wrong" rather than "could not establish". `verify_expr` returns `dims_equal(lhs, rhs)` and propagates only `DimensionalError`/`KeyError`/`TypeError` — but bridgman's `dims_of_expr` returns `{}` for any `Number|NumberSymbol`. So `verify_expr(Eq(F, 0))` returns False because `F` has dims and `0` is dimensionless. The warning fires and brute-force is skipped — fine. But `verify_expr(Eq(KE, 0))` would also flag, even though the equation is *vacuously true* for KE=0. Bridgman has no notion of "the constant happens to satisfy the equation".

### MED-4 — `propstore\families\claims\passes\checks.py:773` silently swallows `bridgman.DimensionalError`
```
except (KeyError, SyntaxError, bridgman.DimensionalError, TypeError):
    pass
```
A DimensionalError from bridgman is *signal*, not noise — it means the symbolic walker proved an inconsistency (e.g. addition of mismatched dims). Dropping it on the floor means propstore's claim validator never reports the very thing bridgman exists to detect. This is strictly drift between bridgman's intent and propstore's consumption.

### LOW-1 — `format_dims` ordering for unknown keys is implementation-defined
`src\bridgman\dimensions.py:80-85`. Unknown dimension symbols all get sort key `len(DIM_ORDER) == 7`, then `sorted` is stable on equal keys → preserves dict insertion order. For determinism in serialisation contexts this should be a secondary sort by symbol name. propstore uses `format_dims` only for human display, so this is cosmetic, but `dims_signature` in `propstore\dimensions.py:180` does its own canonical sort — good, but note that bridgman's own `format_dims` is NOT a canonical signature.

### LOW-2 — Two distinct `DimensionalError` classes when sympy is absent
`__init__.py:43` defines a stub `DimensionalError(Exception)` inside the no-sympy branch. When sympy IS installed, `DimensionalError` is `bridgman.symbolic.DimensionalError`. These are not the same class — `isinstance(e, bridgman.DimensionalError)` always works (because it's the currently-bound name), but pickling, subclass checks across import contexts, or mocked `sys.modules` swaps could observe two distinct classes. Cosmetic in normal use.

### LOW-3 — `_pow_exponent_fraction` uses `Fraction(float(exponent))` fallback
`src\bridgman\symbolic.py:43-51`. For an exponent that is a sympy `Float`, `float()` lossily converts. `Float('0.3333333333')` becomes `Fraction(6004799503160661, 18014398509481984)` — denominator != 1 → DimensionalError. Fine for guard, but means `expr.args[1]` of type `Float(2.0)` works only by luck (it round-trips to exactly `Fraction(2,1)`). Document that exponents should be `Rational`/`Integer`, not `Float`.

### LOW-4 — `dims_of_expr` ignores `Eq` in non-top contexts unhelpfully
`src\bridgman\symbolic.py:108-110` returns dims of LHS for `Eq`, with comment "caller should use verify_expr instead". A nested `Eq` inside a `Mul` (rare but legal) would silently return only the LHS dims. Should probably raise.

## Missing features / drift

- **No dimensionless wrapping for transcendentals.** `sin(x)` in physics requires `x` dimensionless. bridgman has no rule for this — it just refuses with TypeError. A useful library would dispatch a dictionary of `dimensionless_arg_functions` and verify the argument is dimensionless, returning `{}` for the result. Without this, propstore cannot dimensionally validate any claim mentioning `sin`, `cos`, `exp`, `log`, `tanh`, etc. For an ontology of physics, this is a significant gap.
- **No `sub_dims` / no addition support outside expression trees.** `verify_equation` cannot express `lhs == a + b`; only multiplicative combinations. Add sympy or hand-roll an "add"-aware version.
- **No `verify_equation` op for power.** Workaround in propstore: brute-force product enumeration (`families\concepts\passes.py:641`). Either deprecate `verify_equation` in favour of the symbolic API, or extend it.
- **No serialization helper.** propstore re-implements `dims_signature` (`propstore\dimensions.py:180`). This canonical-string formatter belongs in bridgman.
- **No `dims_of_unit` registry.** propstore ships `physgen_units.json` and re-implements unit-symbol resolution in `unit_dimensions.py`. bridgman could provide a `parse_unit("kPa")` → `{M:1, L:-1, T:-2}` API, but currently does not.
- **Theta normalization is propstore's burden.** `propstore\unit_dimensions.py:24-27` maps `Θ`/`θ` → `Theta`. bridgman accepts whatever string keys you hand it. If two consumers normalise differently, `dims_equal` silently lies. Bridgman should either (a) define a canonical Theta spelling in API contract or (b) provide a `normalize_dims` helper.
- **No tests for**: `verify_equation` length-mismatch, `pow_dims` non-int input, `dims_of_expr` on unsupported nodes (sin/cos/exp), `format_dims` with foreign keys, sympy `Float` exponent edge cases.
- **README drift.** README documents 3/11 exports. Symbolic API not mentioned at all. Consumers (propstore) rely on the symbolic API far more than the documented dict API.
- **Docstring drift.** `verify_equation` docstring states a precondition that is not checked (HIGH-1).
- **No CHANGELOG / no version strategy.** v0.1.0 with breaking-shape API surface (Dimensions = `dict[str, int]`) is fine, but propstore pins by path-dep rather than version, so semver is moot until publishing.

## Open questions for Q

1. **Should bridgman handle transcendental functions** (sin/cos/exp/log/sqrt-of-dimensionless), or is propstore expected to pre-normalise expressions before calling `verify_expr`? Currently propstore swallows the TypeError and accepts the claim — that is almost certainly not what you want.
2. **Should propstore stop swallowing `bridgman.DimensionalError`** at `families\claims\passes\checks.py:773`? It looks like dimensional inconsistencies that bridgman detects are silently dropped instead of being recorded as warnings/errors.
3. **`dims_of_expr` is imported in `families\concepts\passes.py:19` but I did not find a direct call** — only `verify_expr` is invoked. Is the `dims_of_expr` import dead, or am I missing a call site? (Suggest `grep "dims_of_expr(" propstore/`.)
4. **Theta canonicalisation:** is the contract that all Dimensions dicts use ASCII `"Theta"` (per `DIM_ORDER` and the `forbidden = "THETA"` test)? If yes, bridgman should expose a `canonicalize_dims()` so consumers stop reinventing it.
5. **`verify_equation` vs. `verify_expr`:** the `verify_equation`/op-string API exists only for the README. propstore brute-forces product enumeration around the same idea (`passes.py:641`). Should `verify_equation` be removed in favour of always going through sympy, or extended with `pow`/`add` and a precondition check (HIGH-1)?
6. **`Dimensions` typed-dict vs free dict:** all consumer code currently treats it as a free dict. Worth making it a `TypedDict` with the seven SI keys to catch typos at type-check time? Cost: closes the door on extending to non-SI dimensions (e.g. information bits, currency).
7. **Bridgman as a CDT (Bridgman 1927) operationalist nod is decorative only** — the library performs no operational-definition tracking. If propstore ever wants to encode "what counts as measuring this quantity", that goes elsewhere. Just confirming this is the intended scope.

Statement: Review complete, master. The meatbag-code is short, but the silent-acceptance pattern between bridgman's TypeError and propstore's bare `except` is the kind of thing that builds confidence in claims that were never actually verified.
