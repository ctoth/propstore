# bridgman — dep review (2026-04-20)

Reviewer: analyst subagent. Scope: `C:\Users\Q\code\bridgman` src, tests, README.
Cross-reference: propstore consumer surface under `C:\Users\Q\code\propstore\propstore`.

## Purpose & Public Surface

bridgman is a small pure-Python library for SI **dimension-exponent arithmetic**.
It is *not* a units library (no quantities, no conversions), *not* Buckingham-pi
(no nullspace / pi-groups computation despite the name), and *not* a CAS. It
operates on one data type:

```python
Dimensions = dict[str, int]   # e.g. {"M": 1, "L": 1, "T": -2}
```

Two modules, single file each:

- `bridgman.dimensions` (always available): `mul_dims`, `div_dims`, `pow_dims`,
  `dims_equal`, `is_dimensionless`, `verify_equation`, `format_dims`.
- `bridgman.symbolic` (optional; requires sympy): `dims_of_expr`, `verify_expr`,
  `DimensionalError`. The package `__init__` soft-imports these behind a bare
  `except ImportError: pass` (see Silent Failures #1).

`pyproject.toml` declares sympy as an *optional* extra (`[sympy]`) and dev-group
dep, not a hard runtime dep.

## API Contract Issues

### [Medium] Docstring claims integer power, runtime accepts float silently
`src/bridgman/dimensions.py:35` — `pow_dims(d: Dimensions, n: int)`. No isinstance
check. Passing `n=0.5` returns `dict[str, float]`, silently violating the
`Dimensions = dict[str, int]` contract and corrupting downstream `dims_equal`
behavior (since `1 == 1.0` holds but `-2 == -2.0` with float drift does not
survive serialization/JSON roundtrips via `world/model.py:986`).
Fix: `if not isinstance(n, int): raise TypeError`, or coerce via `Fraction` and
reuse `_pow_dims_frac`.

### [Medium] `verify_equation` has no length validation
`src/bridgman/dimensions.py:52-71`. Docstring says `len(ops) must equal
len(rhs_terms) - 1` but this invariant is never asserted. If `len(ops) >
len(rhs_terms) - 1`, the loop raises `IndexError` from `rhs_terms[i + 1]`. If
shorter, trailing terms are silently dropped.
Fix: early `if len(ops) != len(rhs_terms) - 1: raise ValueError(...)`.

### [Low] `DIM_ORDER` documents `THETA` but real consumer uses `Theta`
`src/bridgman/dimensions.py:5,11`. The docstring and `DIM_ORDER` list
`"THETA"` for temperature. Propstore (the only known consumer) normalizes
physgen's `Θ` to `"Theta"` (`propstore/unit_dimensions.py:24`) and all form
YAMLs use `Theta` (e.g. `temperature.yaml:6`, `molar_energy_per_temperature.yaml:10`).
`dims_equal` / `mul_dims` / `div_dims` are case-sensitive and treat `Theta`
as an opaque key (still correct for math), but `format_dims` sorts unknown keys
past `len(DIM_ORDER)` — so every propstore form with temperature renders with
`Theta` last regardless of authored order. Cosmetic but a documented-vs-actual
contract drift.
Fix: either canonicalize on `Theta` (matching ISO 80000 physgen) or add both
aliases to `DIM_ORDER`.

### [Low] No validation of dimension keys anywhere
`mul_dims({"BANANA": 1}, {"M": 1})` succeeds. Typos become silent phantom
dimensions that never cancel. The stated SI-base set
(`M/L/T/I/THETA/N/J`) is documented but never enforced.
Fix: optional `strict=True` mode that checks keys against a canonical set, or
at minimum a module-level `SI_BASE = frozenset(...)` with a `validate(d)` helper.

### [Low] `dims_of_expr(Eq)` returns lhs dims only
`src/bridgman/symbolic.py:97-99`. Silently returns `dims_of_expr(eq.args[0], ...)`
for an `Eq` input with a comment telling callers to use `verify_expr` instead.
No warning, no error. A consumer that mistakenly passes an `Eq` gets a plausible
dim dict from the lhs with no signal anything is wrong.
Fix: `raise TypeError("use verify_expr for Eq")`.

## Consumer Drift (propstore → bridgman)

Call sites grepped in `propstore/propstore/`:

| File:line | Symbol used | Status |
|---|---|---|
| `dimensions.py:166` | `verify_expr` | OK, sympy assumed present |
| `form_utils.py:177` | `format_dims` | OK (inside `try/except ImportError`) |
| `form_utils.py:201` | `dims_equal` | OK (inside `try/except ImportError`) |
| `unit_dimensions.py:16` | `dims_equal` | OK, hard import at module top |
| `world/model.py:976` | `dims_equal` | OK, lazy local import |
| `families/concepts/passes.py:18-19` | `mul_dims`, `div_dims`, `dims_equal`, `format_dims`, `verify_expr`, `dims_of_expr`, `DimensionalError` | OK, hard imports |
| `families/claims/passes/checks.py:8,750,773` | `bridgman.verify_expr`, `bridgman.DimensionalError` | OK only if sympy present |

All symbols exist and match signatures. Two drift risks:

### [High] propstore hard-imports sympy-gated symbols
`propstore/families/concepts/passes.py:19` unconditionally does
`from bridgman import verify_expr, dims_of_expr, DimensionalError`. These only
enter `bridgman.__all__` if sympy imports cleanly (see `src/bridgman/__init__.py:25-30`).
If sympy is missing or its import fails, propstore's concept pass module fails
to import, cascading to the entire concepts family. propstore should either
(a) make sympy a hard dep of bridgman, or (b) state it declaratively in
propstore's own pyproject.
Observation: `propstore/families/claims/passes/checks.py:773` catches
`bridgman.DimensionalError` in an `except` tuple — if that attribute is absent,
the except clause itself raises `AttributeError` at exception-handling time.
Fix: make sympy a hard dep in bridgman's `pyproject.toml` (move from
`[project.optional-dependencies]` to `dependencies`). The coverage of optional
is illusory since consumers hard-import it anyway.

### [Low] Temperature key inconsistency
See API Contract Issues §3. `format_dims` output will render differently than
propstore's DIM_ORDER expects. No functional break — display ordering only.

## Correctness

### Exponent algebra is correct
`mul_dims` (add), `div_dims` (subtract), integer `pow_dims` (multiply), and
`_clean` (strip zero exponents) form a correct free abelian group on dimension
symbols over Z. `dims_equal` is symmetric and zero-key-tolerant. No correctness
issue in the core algebra.

### Fractional exponents
`_pow_dims_frac` (`symbolic.py:25-40`) correctly requires the resulting
exponent to have denominator 1, else raises `DimensionalError`. This matches
the standard Bridgman-theorem constraint that physically meaningful dimensional
products raised to rational powers must yield integer exponents.

### Bridgman's pi-theorem is **not** implemented
Despite the name, the library does not compute Buckingham-pi groups,
nullspaces of dimension matrices, or non-dimensionalization. Naming is
aspirational. Not a bug, but a reader of `README.md` searching for pi-theorem
support will be disappointed. Consider clarifying the README's "Does one thing:
SI dimension exponent math" to explicitly say "no pi-theorem, no units, no
quantities".

## Silent Failures

### [High] `__init__.py` bare `except ImportError: pass`
`src/bridgman/__init__.py:29-30`. Any `ImportError` during symbolic import is
swallowed — not only "sympy missing" but also an in-tree syntax error in
`symbolic.py` (if raised as ImportError via a nested import), or sympy version
incompatibility that manifests as ImportError. Users see a silent absence of
`bridgman.verify_expr` and get `AttributeError` at call site with no
diagnostic. Narrow the except to the specific import (`from sympy import ...`)
and consider logging via `warnings.warn` so absence is observable.

### [Medium] Symbolic exponent raises uncaught TypeError
`src/bridgman/symbolic.py:78`. For a `Pow` node whose exponent is itself
non-numeric (e.g. `x**n` where `n` is a `Symbol`), `Fraction(float(exponent))`
calls `float()` on a Symbol and raises `TypeError: Cannot convert expression
to float` (confirmed experimentally with `uv run python -c "..."`). This
escapes `dims_of_expr` undocumented. Propstore's `dimensions.py:176` catches
only `(KeyError, ValueError, ImportError)` — a `TypeError` from this path
would crash form-algebra verification. The docstring's `Raises:` section lists
only KeyError and DimensionalError.
Fix: handle non-numeric `Pow` exponents explicitly (either raise
`DimensionalError` with a useful message, or compute `if
exponent.is_Number:` first).

### [Medium] Float exponent coercion is lossy
`src/bridgman/symbolic.py:78`. `Fraction(float(exponent))` for a sympy `Float`
goes through IEEE-754 before reaching `Fraction`, producing the exact binary
representation, not the mathematical intent. `Float(0.5)` happens to be exact;
`Float(1.0/3.0)` yields a denominator of `3602879701896397` which will fail
the `denominator == 1` check via `_pow_dims_frac` but with a misleading error
message containing the raw binary-approximated fraction. Worse: `Float(2.0)`
succeeds, `Float(2.0 + 1e-16)` silently fails even though the user probably
meant `2`.
Fix: route Float through `sympy.nsimplify` or require `Rational` powers and
reject Float outright.

### [Low] `dims_of_expr` returns `{}` for all numeric constants
`symbolic.py:63-65`. Correct for dimensional analysis but note: `NumberSymbol`
includes `pi`, `E`, `EulerGamma`, etc. which are conventionally dimensionless
— fine — but any user-subclassed `NumberSymbol` with physical meaning would
also be silently dimensionless. Edge case, unlikely in practice.

## Bugs

### [Medium] verify_equation length drift
See API Contract Issues §2. Can raise `IndexError` (not `ValueError`) on
malformed input. `src/bridgman/dimensions.py:63-68`.

### [Medium] pow_dims float leakage
See API Contract Issues §1. Integer contract violated without runtime check.
`src/bridgman/dimensions.py:35-39`.

### [Medium] symbolic.py TypeError path
See Silent Failures §2. `src/bridgman/symbolic.py:78`.

### [Low] `_clean` copies even when no zeros present
`src/bridgman/dimensions.py:14-16`. Minor perf; allocates a new dict on every
mul/div even when input is already clean. Not a bug, noted as a hot-path
concern if called in tight loops (propstore's `concepts/passes.py:631-639`
calls `mul_dims`/`div_dims` in a `product()` cartesian sweep over all op
combinations, which is already O(2^(n-1))).

## Dead Code

### [Low] `DIM_ORDER` entry `"THETA"` unreachable from consumers
Since propstore exclusively uses `"Theta"`, the `"THETA"` slot in
`DIM_ORDER` never matches. Not strictly dead — another consumer could use it
— but given propstore is the only known consumer, it is effectively dead.

No other dead code observed. 97 + 119 lines; nothing vestigial.

## Positive Observations

- **Minimal surface.** Eight top-level functions (plus three symbolic), one
  type alias, one exception. No hidden config, no global state beyond
  `DIM_ORDER`/`SUPERSCRIPT` constants.
- **Pure functions.** Every public function is pure; no hidden side effects,
  no I/O, no mutation of inputs (`dict(d1)` copy in mul/div).
- **`py.typed` marker present.** Consumers get static typing.
- **Zero hard dependencies.** `pyproject.toml` declares no runtime deps;
  sympy is correctly isolated to the optional `symbolic` module. (This is also
  the source of the Consumer Drift §1 issue, but the *intent* is sound.)
- **Test coverage of core algebra is thorough.** 18 tests for dimensions,
  13 for symbolic, covering F=ma, E=mc², P=IV, KE=½mv², Newton's gravity,
  Maxwell speed-of-light identity, and sqrt of permittivity·permeability.
- **Fractional exponents handled via `Fraction`, not float.** (Except for the
  Float-exponent edge case flagged above.) `_pow_dims_frac` correctly
  enforces integer-valued resulting exponents.
- **Good naming.** `mul_dims`/`div_dims`/`pow_dims` are unambiguous.
  `format_dims` using Unicode superscripts is ergonomic.
- **Sensible `is_dimensionless` semantics.** `{}`, `{"L": 0}`, and
  `{"L": 0, "T": 0}` all return True.

## Summary

bridgman is a small, well-scoped, correctly implemented exponent-algebra
library with a clean API. The real issues cluster in three places:

1. **Optional-sympy fiction** — propstore hard-imports sympy-gated symbols;
   bridgman should just declare sympy as a hard dep.
2. **Defensive coding gaps** — `verify_equation` length, `pow_dims` int check,
   symbolic `Pow` TypeError, Float exponent lossy coercion.
3. **Documentation / consumer drift** — `THETA` vs `Theta`, Bridgman-pi
   implied by the name but not implemented.

None of these are blockers for propstore's current usage. The highest-risk
item is the sympy-availability assumption (Consumer Drift §1): a broken sympy
install would take down the concepts pass module with a confusing
`AttributeError` instead of a clear `ImportError`.
