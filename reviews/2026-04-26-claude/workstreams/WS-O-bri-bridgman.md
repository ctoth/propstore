# WS-O-bri: bridgman fixes — dimensional algebra

**Status**: CLOSED 69241ae1
**Depends on**: nothing internal
**Blocks**: WS-P (CEL/units consumer); also unblocks correct dimensional checking in propstore claim and concept passes.
**Owner**: Codex implementation owner + human reviewer required (per Codex 2.1).
**Repo under change**: `C:\Users\Q\code\bridgman\` (package `bridgman` v0.1.0). Propstore-side changes: (a) deleting one dead import, (b) migrating callers from `verify_equation` to `verify_expr`, (c) splitting two `except` clauses that swallow `bridgman.DimensionalError` / `TypeError`, (d) bumping the bridgman pin in the same PR window as the bridgman release that deletes `verify_equation`.

---

## Why this exists

bridgman is a tiny leaf library doing SI dimensional-exponent arithmetic over `M, L, T, I, Theta, N, J`. Eight propstore call sites depend on it. The HIGH findings are not "the algebra is wrong" — they are **silent acceptance**: bridgman raises `TypeError` for unsupported sympy nodes, propstore catches `TypeError` and `pass`es, and equations involving transcendentals or fractional powers pass dimensional verification without ever being checked. `dims_of_expr` saying "I don't know" reads as "OK" at the call site. That is the bug class this workstream closes.

Per **D-13** (`reviews/2026-04-26-claude/DECISIONS.md`) + **Codex 2.27** + Q's "no old repos" rule + `feedback_no_fallbacks.md`: bridgman exposes one canonical dim-checking entry point (`verify_expr` / `dims_of_expr`); `verify_equation` is **deleted in the same release as the propstore caller migration** — no deprecation period, no `DeprecationWarning` window, no two-version shuffle. Bridgman v0.2.0 ships with `verify_equation` already gone; propstore's pin bumps to v0.2.0 in the same PR window.

## Review findings covered

Every Cluster-Q HIGH and MED finding (`reviews/2026-04-26-claude/cluster-Q-bridgman.md`), plus the dead import in propstore. "Done means done": every finding listed is gone or has a green test gating it.

| Finding | Citation | One-line description |
|---|---|---|
| **HIGH-1** | `bridgman/src/bridgman/dimensions.py:52-71` | `verify_equation` doesn't enforce `len(ops) == len(rhs_terms) - 1`; extra terms silently dropped. Closes by deletion. |
| **HIGH-2** | `bridgman/src/bridgman/symbolic.py:112`; `propstore/families/claims/passes/checks.py:773`; `propstore/families/concepts/passes.py:633` | `dims_of_expr` raises `TypeError` for sympy nodes outside `Symbol|Number|NumberSymbol|Mul|Pow|Add|Eq`; propstore swallows. **Gates the verify_equation deletion** — `verify_expr` must cover `Pow`/`Add`/transcendentals first. |
| **HIGH-3** | `bridgman/src/bridgman/dimensions.py:35-39` | `pow_dims(d, n)` declares `n: int` with no runtime guard; `pow_dims({"L": 2}, 0.5)` returns `{"L": 1.0}`. |
| **MED-1** | `bridgman/tests/test_dimensions.py:14-23` | Theta-glyph test shells `git grep`, ignores returncode; passes vacuously outside a git checkout. |
| **MED-2** | `bridgman/README.md` | README documents 3 of 11 exports; symbolic API undocumented. |
| **MED-3** | `propstore/families/concepts/passes.py:632` | `sympy_verified = True` after warning assumes a "definitively wrong" contract bridgman never documented. |
| **MED-4** | `propstore/families/claims/passes/checks.py:773` | `bridgman.DimensionalError` is signal (proven inconsistency in `Add`); propstore catches and `pass`es. |
| **Missing-1** | n/a | No dimensionless-arg dispatch for transcendentals; without it HIGH-2 can't be fixed at call sites. |
| **Missing-2** | n/a | `verify_equation` had only `mul`/`div`; coverage lives on `verify_expr` instead, callers migrate, function deletes. |
| **Missing-3** | `propstore/dimensions.py:180` | Canonical dim-signature reinvented in propstore. |
| **Missing-4** | `propstore/unit_dimensions.py` | Unit-symbol parsing reinvented in propstore. Design decision in README, no code move here. |
| **Missing-5** | `propstore/unit_dimensions.py:24-27` | Theta canonicalisation (`Θ`/`θ` → `Theta`) is propstore's burden; two consumers normalising differently make `dims_equal` lie. |
| **Dead-import** | `propstore/families/concepts/passes.py:19` | `dims_of_expr` imported but never called. |

Adjacent LOWs folded in: LOW-1 (format_dims unknown-key ordering) closes implicitly via Missing-3's canonical signature; LOW-3 (`Float` exponent) becomes a one-line README rule under step 9; LOW-4 (nested `Eq` returning LHS dims) folds into the HIGH-2 fix as one more `DimensionalError`-not-`TypeError` case. LOW-2 (two `DimensionalError` classes when sympy absent) is cosmetic and deferred.

## Code references (verified by direct read)

bridgman side:

- `bridgman/src/bridgman/dimensions.py:35-39` — `pow_dims`: no type guard on `n` (HIGH-3).
- `bridgman/src/bridgman/dimensions.py:52-71` — `verify_equation`; precondition in docstring, not enforced (HIGH-1). Target of deletion.
- `bridgman/src/bridgman/symbolic.py:112` — `raise TypeError(f"Unsupported sympy expression type: ...")` (HIGH-2 source).
- `bridgman/src/bridgman/symbolic.py:97-106` — `Add` branch raises `DimensionalError` on mismatch (the signal MED-4 says propstore swallows).
- `bridgman/src/bridgman/__init__.py:33-52` — symbolic API re-exported via `try/except ImportError` shim when sympy absent.
- `bridgman/tests/test_dimensions.py:14-23` — runs `git grep`, asserts only `stdout == ""` (MED-1).
- `bridgman/README.md` — 31 lines, documents 3 of 11 exports (MED-2).

propstore side:

- `propstore/families/claims/passes/checks.py:750, :773` — calls `bridgman.verify_expr`; `except (KeyError, SyntaxError, bridgman.DimensionalError, TypeError): pass` (MED-4, HIGH-2 swallow).
- `propstore/families/concepts/passes.py:19` — imports `dims_of_expr` (dead; `grep "dims_of_expr(" propstore/` returns no matches).
- `propstore/families/concepts/passes.py:619-633` — sets `sympy_verified = True` after recorded warning (MED-3); `except (DimensionalError, KeyError, TypeError, SyntaxError): pass` (HIGH-2 swallow).
- `propstore/families/concepts/passes.py:639-647` — brute-force `itertools.product` over `[mul_dims, div_dims]`; deletion lives in WS-D.
- `propstore/dimensions.py:180-187` — duplicate `dims_signature` (Missing-3).
- `propstore/unit_dimensions.py:24-27` — `_DIM_KEY_NORMALIZE` Theta map (Missing-5).
- `propstore/unit_dimensions.py:81-102` — `resolve_unit_dimensions` reinvents unit-symbol parsing (Missing-4).

Direct callers of `verify_equation` in propstore — verified by read-only inspection. All migrate to `verify_expr` in the same PR that deletes the function in bridgman (step 7). Read-only on production until step 7 lands.

## First failing tests (write these first; they MUST fail before any production change)

Tests are bridgman-side unless noted. Each must fail today, green after its step lands. Per Codex 2.28: every check is a `tests/`-resident file run via `uv run pytest` (bridgman) or `scripts/run_logged_pytest.ps1` (propstore) — no bare `python -c` one-liners.

1. **`bridgman/tests/test_pow_dims_integer_guard.py`** (HIGH-3) — `pow_dims({"L": 2}, 0.5)` raises `TypeError`; `pow_dims({"L": 2}, 3)` returns `{"L": 6}`; `pow_dims(d, 0)` returns `{}`. Today the float case silently returns `{"L": 1.0}`.

2. **`bridgman/tests/test_transcendentals.py`** (HIGH-2 + Missing-1 + LOW-4) — parametrized over `sin, cos, tan, exp, log, sinh, cosh, tanh`: dimensionless arg returns `{}`; dimensional arg raises `DimensionalError` naming function and offending dims. Unsupported nodes (`Derivative`, `Integral`, `Piecewise`, `Min`, `Max`, `Abs`, `KroneckerDelta`) and nested `Eq` raise `DimensionalError`, not `TypeError`. Today everything hits `TypeError` at `symbolic.py:112`.

3. **`bridgman/tests/test_theta_glyph_source_scan.py`** (MED-1) — reads `bridgman/src/` via `pathlib`, asserts forbidden glyph absent. No `subprocess`, no cwd dependency.

4. **`bridgman/tests/test_dimensions_canonical_signature.py`** (Missing-3) — `dims_signature` and `parse_dims_signature` exist, order-insensitive, round-trip.

5. **`bridgman/tests/test_canonicalize_theta.py`** (Missing-5) — `canonicalize_dims({"Θ": 1}) == canonicalize_dims({"θ": 1}) == {"Theta": 1}`.

6. **`bridgman/tests/test_verify_equation_deleted.py`** (D-13 + Codex 2.27 — replaces the prior "deprecated" test) — Asserts: `from bridgman import verify_equation` raises `ImportError`; `"verify_equation" not in dir(bridgman)`; `"verify_equation" not in bridgman.__all__`; AST-grep over `bridgman/src/` finds zero `def verify_equation(` and zero `verify_equation(` call sites. The propstore-side `verify_equation(` AST-grep lives in test #7.

7. **propstore-side: `tests/test_bridgman_signal_propagation.py`** (MED-3, MED-4, HIGH-2 propagation, dead-import, D-13 caller deletion) — `bridgman.DimensionalError` produces `_record(level="error", ...)`, not silent `pass`. `Eq(theta, sp.sin(omega*t))` with dimensionless `omega*t` passes; `Eq(theta, sp.sin(L))` (where `L` is dimensioned) **raises `bridgman.DimensionalError` and is recorded as `_record(level="error", ...)`** — NOT a warning (per Codex re-review #16 and `feedback_no_fallbacks`: invalid dimensional expressions are errors, not advisory diagnostics). Warnings are reserved for advisory non-fatal checks; a transcendental applied to a dimensioned argument is a hard contract violation per the HIGH-2 dispatch (Step 2). AST-walk asserts (a) `dims_of_expr` not in any `from bridgman import ...`, (b) zero `verify_equation(` call sites under `propstore/`, (c) zero `from bridgman import verify_equation` lines under `propstore/`. Today all three AST assertions fail and the `sin(L)` case is silently swallowed instead of recorded as ERROR.

8. **`bridgman/tests/test_workstream_o_bri_done.py`** — sentinel; `xfail` until close.

## Production change sequence

Each step is one commit prefixed `WS-O-bri step N — <slug>`. Steps 1-6 and 8-9 are bridgman-side; step 7 is propstore-side. **Ordering is load-bearing**: HIGH-2 (step 2) MUST land before the `verify_equation` deletion (step 6 / migration step 7), because `verify_expr` cannot replace `verify_equation` until it covers `Pow`/`Add`/transcendentals. Step 6 (delete) and step 7 (migrate + bump pin) land together in the same PR window — no deprecation period bridges the two.

1. **`pow_dims` integer guard (HIGH-3)** — `dimensions.py:35-39`: `if not isinstance(n, int) or isinstance(n, bool): raise TypeError(...)`. `TypeError`, not `DimensionalError` — type discipline, not proven inconsistency.

2. **Transcendental dispatch (HIGH-2 + Missing-1 + LOW-4) — GATE for step 6/7** — `symbolic.py`: add `_DIMENSIONLESS_ARG_FUNCTIONS` keyed by sympy class (`sin`, `cos`, `tan`, `exp`, `log`, `sinh`, `cosh`, `tanh`, `atan2`). Dispatched func asserts each arg is dimensionless (else `DimensionalError`) and returns `{}`; nested `Eq` raises `DimensionalError`; catch-all changes from `TypeError` to `DimensionalError`. `TypeError` reserved for "wrong python type." After this step `verify_expr` covers everything `verify_equation` covered plus the cases it never could — precondition for the deletion.

3. **Theta-glyph test rewrite (MED-1)** — replace `test_dimensions.py:14-23` with `test_theta_glyph_source_scan.py`.

4. **Canonical dimension signature (Missing-3)** — add `dims_signature` and `parse_dims_signature` to `dimensions.py`; export; document. Propstore-side delete of the duplicate body ships in step 7.

5. **Theta canonicaliser (Missing-5)** — add `canonicalize_dims` to `dimensions.py`; document the `Θ`/`θ` → `Theta` mapping in README. Propstore-side delete of `_DIM_KEY_NORMALIZE` ships in step 7.

6. **bridgman: delete `verify_equation` (D-13 + Codex 2.27)** — `dimensions.py`: delete `verify_equation` and any helpers used only by it. `__init__.py`: drop the export from `__all__` and the import line. Delete the existing `bridgman/tests/test_verify_equation*.py` files (replaced by Test #6). No `DeprecationWarning`, no shim, no comment carcass. **This commit is the bridgman v0.2.0 release commit.**

7. **propstore: migrate callers, stop swallowing, drop dead import, bump pin — coordinated with step 6 in the same PR window** — bump bridgman pin to v0.2.0; in the same propstore PR:
   - Migrate every propstore `verify_equation` call site to `verify_expr(sp.Eq(lhs, rhs), symbol_dims)`. AST scan asserts no `verify_equation(` call survives.
   - `propstore/families/concepts/passes.py:19`: drop `dims_of_expr` from the `from bridgman import` line.
   - `propstore/families/concepts/passes.py:632-633`: remove `sympy_verified = True` after recorded warning (MED-3); narrow the `except` so `DimensionalError` is **not** caught silently — record at `_record(level="error", ...)`. Per Codex re-review #16: a `DimensionalError` from bridgman (e.g. `sin(L)` where `L` is dimensioned) is a proven inconsistency and must surface as ERROR severity, never WARNING. Brute-force still runs after a recorded warning because bridgman makes no "definitively wrong" promise for non-`DimensionalError` paths.
   - `propstore/families/claims/passes/checks.py:773`: split `bridgman.DimensionalError` into its own `except` recording an **error** diagnostic at `_record(level="error", ...)` (MED-4 + Codex re-review #16). Warnings stay reserved for advisory non-fatal checks; proven dimensional inconsistencies are errors.
   - Delete `propstore/dimensions.py:180-187` `dims_signature`; delegate to `bridgman.dims_signature`.
   - Delete `propstore/unit_dimensions.py:24-27` `_DIM_KEY_NORMALIZE`; delegate to `bridgman.canonicalize_dims`.
   - Brute-force fallback at `propstore/families/concepts/passes.py:639-647` stays; its deletion lives in WS-D.
   - **Bridgman-pin assertion** (Codex 2.28 — substantive check, not `python -c`): new file `tests/test_bridgman_pin_post_deletion.py` imports `bridgman`, asserts `bridgman.__version__ >= "0.2.0"`, `not hasattr(bridgman, "verify_equation")`, and `from bridgman import verify_equation` raises `ImportError`. Run via `scripts/run_logged_pytest.ps1`.

   This step is the single release boundary at which `verify_equation` ceases to exist anywhere.

8. **README + CHANGELOG (MED-2 + LOW-3)** — rewrite `bridgman/README.md` with two sections:
   - **Dict API**: `Dimensions`, `mul_dims`, `div_dims`, `pow_dims`, `dims_equal`, `is_dimensionless`, `format_dims`, `dims_signature`, `canonicalize_dims`. (`verify_equation` is gone — no banner, no "Deprecated" section, no carcass.)
   - **Symbolic API** (requires `bridgman[sympy]`; the canonical dim-checking entry point per D-13): `dims_of_expr`, `verify_expr`, `DimensionalError`, `SympyRequiredError`. Document the transcendental dispatch list, the unsupported-node `DimensionalError` contract, and the rule that exponents must be `Rational`/`Integer`, not `Float` (LOW-3).
   Add `CHANGELOG.md` with a v0.2.0 entry naming: HIGH-2 (transcendentals), HIGH-3 (`pow_dims` guard), Missing-3 (`dims_signature`), Missing-5 (`canonicalize_dims`), and the **deletion** of `verify_equation` (one-shot removal). Cite D-13 + Codex 2.27.

9. **Close out** — flip `test_workstream_o_bri_done.py` from `xfail` to `pass`; update `propstore/docs/gaps.md` (close all Cluster-Q rows; record D-13 + Codex 2.27 with bridgman v0.2.0 as the deletion version); update STATUS line to `CLOSED <sha>`.

## Acceptance gates

All must hold before declaring WS-O-bri done. Every check runs via `uv run` or the logged-pytest wrapper — no bare `python -c` (Codex 2.28).

- [x] `cd ../bridgman && uv run pytest` — `82 passed`.
- [x] `cd ../bridgman && uv run pyright` — `0 errors, 0 warnings, 0 informations`.
- [x] `cd ../bridgman && uv run pytest tests/test_verify_equation_deleted.py -q` — `3 passed`.
- [x] `uv run pyright propstore` — `0 errors, 0 warnings, 0 informations`.
- [x] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-O-bri-post-property-pin tests/test_bridgman_signal_propagation.py tests/test_bridgman_pin_post_deletion.py` — `5 passed`; log `logs/test-runs/WS-O-bri-post-property-pin-20260430-161545.log`.
- [x] Full propstore suite via `powershell -File scripts/run_logged_pytest.ps1 -Label WS-O-bri-final-full` — `3500 passed, 2 skipped`; log `logs/test-runs/WS-O-bri-final-full-20260430-161616.log`.
- [x] `bridgman/README.md` documents all live exports; `bridgman/CHANGELOG.md` exists, names v0.2.0 as the release that bundled HIGH-2/HIGH-3/Missing-3/Missing-5 fixes AND deleted `verify_equation`, citing D-13 + Codex 2.27.
- [x] `propstore/docs/gaps.md` has no open Cluster-Q rows.
- [x] `propstore/dimensions.py:180-187` no longer hand-writes `dims_signature`; `propstore/unit_dimensions.py:24-27` no longer contains `_DIM_KEY_NORMALIZE`; `propstore/families/concepts/passes.py:19` no longer imports `dims_of_expr`.
- [x] STATUS line at top of this file is `CLOSED 69241ae1`.

No follow-up v0.3.0 gate. Close-out and deletion are the same release.

## Done means done

Every finding in the table at the top has either a green test gating it or a code-deletion confirming it. D-13 + Codex 2.27 is a **one-version process**: bridgman v0.2.0 deletes `verify_equation` and propstore migrates to `verify_expr` in the same PR window. No deprecation, no two-step. If any item from HIGH-1 (closes by deletion), HIGH-2, HIGH-3, MED-1..4, Missing-1..5, or Dead-import is not closed, WS-O-bri stays OPEN.

## Papers / specs referenced

- **`papers/Hobbs_1985_OntologicalPromiscuity/notes.md`** (`p.62`) — `Dimensions = dict[str, int]` is promiscuous by design (any string is an entity-kind name); the consumer's burden is to canonicalise *into* the SI alphabet. `canonicalize_dims` (Missing-5) operationalises that contract; the MED-1 forbidden-glyph test enforces it lexically.
- **`papers/Pustejovsky_1991_GenerativeLexicon/notes.md`** (`p.16-21`) — Qualia *telic* role frames HIGH-2 / Missing-1: `sin`'s telic role is "produce a dimensionless number from a dimensionless angle." The dimensionless-arg dispatch encodes Pustejovsky's type-coercion mechanism: if coercion to dimensionless fails, the function raises `DimensionalError`. More principled than ad-hoc whitelisting; gives a fixed authoring rule for new entries.

The Bridgman 1922 operationalist nod is decorative; Cluster-Q open question 7 confirms the library tracks no operational definitions. Out of scope.

## Cross-stream notes

- Blocks WS-P (CEL/units consumer): WS-P relies on `dims_signature`, `canonicalize_dims`, and `verify_expr`. Closing WS-O-bri first prevents WS-P from binding to a function that no longer exists.
- Independent of WS-A: bridgman is a leaf dep, can land in parallel.
- Touches WS-D: brute-force enumeration at `propstore/families/concepts/passes.py:639-647` becomes a deletion candidate once callers are on `verify_expr`. Out of scope here.
- No interaction with WS-O-{arg, gun, qui, ast}.

## What this WS does NOT do

- Does NOT extend `verify_equation` with `Pow`/`Add` support — D-13 + Codex 2.27 delete it.
- Does NOT introduce a deprecation period — Codex 2.27 + Q's "no old repos" rule + `feedback_no_fallbacks.md` forbid it.
- Does NOT use bare `python -c` for any acceptance check (Codex 2.28).
- Does NOT move `propstore/unit_dimensions.py:resolve_unit_dimensions` into bridgman (Missing-4; design-decision-only here).
- Does NOT add a `TypedDict` over the seven SI keys.
- Does NOT delete the propstore brute-force fallback at `propstore/families/concepts/passes.py:639-647` (WS-D).
- Does NOT add a `verify_expr_with_brute_force` convenience.
- Does NOT change `pyproject.toml requires-python`.
