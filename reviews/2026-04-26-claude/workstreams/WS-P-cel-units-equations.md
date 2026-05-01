# WS-P: CEL / units / equations

**Status**: CLOSED 99f2a666
**Depends on**: WS-O-bri (bridgman dimensional-error contract), WS-O-ast (ast-equiv free-variable + tier semantics post-D-14)
**Blocks**: none — terminal node
**Owner**: Codex implementation owner + human reviewer required

---

## Why this workstream exists

CEL conditions, dimensional units, and equation comparison sit at the semantic core of propstore. Every non-commitment guarantee in the project's design principle ("never collapse disagreement in storage unless user explicitly requests migration") requires that two claims with the same logical content be recognized as the same, and two claims with different logical content be kept distinct. Cluster G demonstrates that today the system fails both directions:

- **False negatives on equivalence**: `log(x*y)` vs `log(x)+log(y)` returns `DIFFERENT` *even when the domain `x>0, y>0` is asserted*. `200 Hz` vs `0.2 kHz` is reported as a parameter conflict. `x = y` and `y = x` produce different equation signatures. Two papers asserting the same equation under reversed dependent/independent labelling never reach the equivalence check at all.
- **False positives on inconsistency** that masquerade as soundness: `cond ? "x" : 1` type-checks as STRING; `delta_T = 5 degC` is silently shifted by 273.15 K; `enabled || (1/x > 0)` is unsatisfiable in Z3 when `x == 0` even though the OR's left disjunct is true.

These are not edge cases. They are systematic gaps where the implemented procedure is *not* a decision procedure for the equational theory it claims to handle, but the return type pretends it is. There is no `UNKNOWN` / `INCOMPARABLE-due-to-undecidability` channel, so callers cannot tell a real disagreement from a normalization gap, and there is no domain-assumption channel, so callers cannot tell a domain-restricted true equivalence from an unconditional one.

Both reviewers — Claude cluster G and Codex ws-04 — independently flagged the same four anchor findings (T2.4 ternary, T2.12 Z3 guards, T2.13 parser gaps, parameter-unit raw comparison). The corroboration is what graduates this workstream from "tidy up CEL" to "Tier 2 math correctness."

## Review findings covered

This workstream closes ALL of the following. "Done means done" — every finding listed has a green test gating it before WS-P merges.

### Anchor findings (corroborated by both reviewers)

| Finding | Source | Citation | Description |
|---|---|---|---|
| **T2.4** | REMEDIATION-PLAN Tier 2 | `propstore/cel_checker.py:586-590` | CEL ternary type-rule unsound — no boolean check on condition, no branch-type unification. |
| **Codex #30** | `reviews/2026-04-26-codex/workstreams/ws-04-formal-expressions-units-equations.md` (line 7) | same | Same finding from Codex independently. |
| **T2.12** | REMEDIATION-PLAN Tier 2 | `propstore/z3_conditions.py:252-260,410-418`; `propstore/core/conditions/z3_backend.py:33-35,121-125` | Z3 division-by-zero guards conjoined globally, not scoped per subexpression. Boolean and ternary semantics are silently strengthened. |
| **Codex #29** | ws-04 (line 8) | same | Same finding. |
| **T2.13** | REMEDIATION-PLAN Tier 2 | `propstore/cel_checker.py:183, :209` (parser gaps) | CEL float literals reject exponent notation; string escapes only handle three of N. Overlap with WS-D — coordinate. |

### Codex-only findings folded in

| Finding | Citation | Description |
|---|---|---|
| **Codex #28** | `propstore/conflict_detector/parameter_claims.py:112,162,231` calling `propstore/value_comparison.py:97` | Parameter conflict detection compares raw values, never threads `forms`/`concept_form`, so the SI-normalisation branch in `_values_compatible` is unreachable from this path. `200 Hz` vs `0.2 kHz` is reported as a conflict. |
| **Codex #31** | `propstore/equation_comparison.py:108-112,176-184` | Equation equivalence is orientation-sensitive: `cancel(expand(lhs - rhs))` differs from `cancel(expand(rhs - lhs))` only by sign, and the canonical form is `str(diff)` so `x - y` and `y - x` compare unequal. |
| **Codex #32** | `propstore/sympy_generator.py:54-91` | `generate_sympy_with_error` calls `text.split("=", 1)[1]` and silently discards the LHS. If callers use it for equation identity, two equations with the same RHS and different LHS hash equal. |
| **Codex #33** | `propstore/conflict_detector/algorithms.py:55` | Algorithm conflict path treats anything not in the post-D-14 acceptance set as a conflict — including `Tier.SYMPY` equivalence proofs. ast-equiv's "yes, equivalent under sympy" is recoded as "yes, conflicting." (Per D-14 the post-D-14 ast-equiv tier set is `{NONE, CANONICAL, SYMPY, PARTIAL_EVAL}`. The conflict-suppression whitelist is `{CANONICAL, SYMPY, PARTIAL_EVAL}` — all three are proof-strength enough to suppress a conflict (true equivalence). `NONE` is the "couldn't decide" fallback and does NOT suppress a conflict.) |
| **Codex #34** | `propstore/families/claims/passes/checks.py:819-827` | `extract_names(tree)` returns *every* `ast.Name.id` and `ast.arg.arg` — including loop variables, comprehension targets, and locally-assigned temporaries. The pass treats this as a free-variable set and warns on each as undeclared. Verified by reading `../ast-equiv/ast_equiv/canonicalizer.py:47-55`. |

### Cluster G HIGH-severity findings folded in

| Finding | Citation | Description |
|---|---|---|
| **G-H1** | `propstore/cel_checker.py:586-590` | Ternary type-rule unsound (same as T2.4). |
| **G-H2** | `propstore/dimensions.py:80-81`, form schema | Affine temperature units (`degC`, `degF`) treated as linear for deltas. A claim `delta_T = 5 degC` normalises to `5*1.0 + 273.15 = 278.15 K`, ~273 K silent error. Pint distinguishes `degC` from `delta_degC`; propstore's form schema does not. |
| **G-H3** | `propstore/equation_comparison.py:169-188` | `cancel(expand(diff))` is complete only for rational polynomial identity. `log(x*y)` vs `log(x)+log(y)` returns `DIFFERENT`. No `INCOMPARABLE-due-to-undecidability` state — `EquationComparisonStatus.INCOMPARABLE` is reserved for parse failure (line 103-107). Domain-restricted identities (e.g. `log(x*y) = log(x)+log(y)` valid only on `x>0 ∧ y>0`) have nowhere to declare those assumptions. |
| **G-H4** | `propstore/z3_conditions.py:252-260,410-418` | Division-by-zero guards live on `self._current_guards` and are reset only inside `_condition_to_z3`. Not thread-safe; not protected against re-entrant translation; semantically wrong for OR-short-circuit and ternary (same as T2.12). |

### Cluster G MED-severity findings folded in

| Finding | Citation | Description |
|---|---|---|
| **G-M1** | `propstore/cel_checker.py:720-721` | `UNKNOWN` ExprType is a silent absorbing element in `_check_comparison_type_mismatch`. Single typo masks all downstream type errors in the same expression. |
| **G-M2** | `propstore/cel_checker.py:566-578` | Unary `!` returns BOOLEAN and unary `-` returns NUMERIC even after the operand failed type-check. Coercive subsumption with no semantic basis. |
| **G-M3** | `propstore/z3_conditions.py:124,171` | EnumSort cached against mutable registry; `dict[str, ConceptInfo]` without defensive copy at construction. |
| **G-M4** | `propstore/dimensions.py:25` and `propstore/unit_dimensions.py:33-59` | Pint registry singleton; `register_form_units` writes into a separate `_symbol_table` cache and does not update pint. Form-declared custom units are visible to bridgman but invisible to `can_convert_unit_to`. |
| **G-M5** | `propstore/cel_checker.py:183` | CEL float literals reject exponent notation `1e9`. Inconsistent with the equation parser, which accepts `[eE][+-]?\d+`. |
| **G-M6** | `propstore/cel_checker.py:209` | CEL string-literal escape handling recognises only `\"`, `\'`, `\\`. `\n`, `\t`, `\u`, `\x` survive unprocessed. |
| **G-M7** | `propstore/cel_types.py:91-105` | `_normalize_checked_conditions` deduplicates by `str(condition.source)` only. `a < b` and `b > a` are distinct keys; semantically equivalent conditions are not merged. |
| **G-M8** | `propstore/equation_comparison.py:53-73` | `equation_signature` includes `dependent`/`independent` role labels in the grouping key. Two papers asserting the same equation under reversed labelling never enter the equivalence check. |

Adjacent items intentionally NOT pulled into WS-P (out of scope; flagged for triage):

- L1 `_PINT_ALIASES` rounding for degF (10⁻⁵ round-trip error). Cosmetic.
- L13/L14 `value_comparison` tolerance and list-equality mismatch — that's WS-O-vc territory.
- Q4 paper notes.md absence — covered by separate paper-faithful workflow stream, not WS-P.

## Code references (verified by direct read)

### CEL ternary (T2.4 / Codex #30 / G-H1)

`propstore/cel_checker.py:586-590`:
```python
if isinstance(node, TernaryNode):
    _check_node(node.condition, expr, registry, errors)
    t1 = _resolve_type(node.true_branch, expr, registry, errors)
    _resolve_type(node.false_branch, expr, registry, errors)
    return t1
```
- `_check_node` on the condition only resolves type; never asserts the type is BOOLEAN. `1 ? true : false` type-checks.
- The false branch's type (`_resolve_type` return) is discarded. The expression's type is unconditionally `t1`. `cond ? "x" : 1` types as STRING.
- Pierce TaPL §11.8 T-If: `t1 : Bool, t2 : T, t3 : T ⊢ if t1 then t2 else t3 : T`. Both premises absent.

### Z3 division guards (T2.12 / Codex #29 / G-H4)

`propstore/z3_conditions.py:252-260`:
```python
if node.op == "/":
    zero = z3.RealVal(0, self._ctx)
    guard = right != zero
    self._current_guards.append(guard)
    return left / right
```

`propstore/z3_conditions.py:405-417` (the only reset point):
```python
def _condition_to_z3(self, condition: CelExpr | CheckedCelExpr) -> Any:
    ...
    expr = self._condition_expr_cache.get(key)
    if expr is None:
        self._current_guards: list[Any] = []
        translated = self._translate(checked.ast)
        if self._current_guards:
            expr = z3.And(translated, *self._current_guards)
        else:
            expr = translated
        self._condition_expr_cache[key] = expr
    return expr
```

`propstore/core/conditions/z3_backend.py:33-35,121-125` confirms the same pattern in the IR-level backend: division emits a guard tuple via `_Projection`, those tuples bubble up through every parent including OR / Choice, and the top-level `condition_ir_to_z3` conjuncts them all with `z3.And(*projection.guards, projection.term)`.

The semantic consequence: `enabled || (1/x > 0)` is encoded as `Or(enabled, 1/x > 0) ∧ x != 0`. Querying with `enabled == true ∧ x == 0` returns UNSAT. The boolean interpretation says it should be SAT — the OR's left disjunct is independently true and the right disjunct's denominator is never evaluated. Same defect for ternary `cond ? a : (1/x > 0)` when `cond == true`.

This is `if let p = a in p else true` semantically silent strengthening — the formula is provably stronger than the surface CEL, and propstore has no warning in place.

### Equation orientation (Codex #31)

`propstore/equation_comparison.py:108-112`:
```python
status = (
    EquationComparisonStatus.EQUIVALENT
    if left.canonical == right.canonical
    else EquationComparisonStatus.DIFFERENT
)
```
`propstore/equation_comparison.py:176-184`:
```python
lhs = _expr_to_sympy(parsed.lhs, sympy)
rhs = _expr_to_sympy(parsed.rhs, sympy)
diff = sympy.cancel(sympy.expand(lhs - rhs))
...
return EquationNormalization(canonical=str(diff), ...)
```
`x = y` produces canonical `"x - y"`. `y = x` produces `"-x + y"`. SymPy's `str` ordering is deterministic but not sign-normalised. The two forms compare unequal. Conflict-detection callers receive `DIFFERENT` for what is the same equation.

### Equation theory completeness (G-H3)

Same `cancel(expand(...))` at line 178. This decides rational-polynomial identity (Knuth 1970 simple word problems → AC1-completion is in scope here), but `log`, `exp`, `sqrt` traverse `_expr_to_sympy` at line 213-221 unwrapped — no `logcombine`, no `simplify`, no domain assumption. The pipeline returns `EQUIVALENT` or `DIFFERENT` deterministically with no third value for "couldn't decide." `EquationComparisonStatus.INCOMPARABLE` is wired to `EquationFailure` only (line 102-107).

### Equation signature includes role labels (G-M8)

`propstore/equation_comparison.py:53-73`:
```python
def equation_signature(claim: ConflictClaim) -> tuple[str, tuple[str, ...]] | None:
    ...
    dependent_concepts = [
        variable.concept_id
        for variable in variables
        if variable.role == "dependent" and variable.concept_id
    ]
    if len(dependent_concepts) != 1:
        return None
    dependent_concept = dependent_concepts[0]
    independent_concepts = sorted(
        variable.concept_id
        for variable in variables
        if variable.concept_id and variable.concept_id != dependent_concept
    )
    return dependent_concept, tuple(independent_concepts)
```
This is the conflict-detector grouping key. Two papers describing `F = m * a` — one author marking `F` dependent, another marking `m` dependent — produce different signatures and never meet in the equivalence loop. Cross-paper same-equation detection silently fails on author-intent differences.

### SymPy generator drops LHS (Codex #32)

`propstore/sympy_generator.py:67-69`:
```python
if "=" in text:
    parts = text.split("=", 1)
    text = parts[1].strip()
```
There is no contract documented saying "this returns RHS only." Callers using `generate_sympy_with_error(...).expression` as an equation identity hash — and there are such callers, per Codex's audit — collide on RHS.

### Parameter conflict raw-value comparison (Codex #28)

`propstore/conflict_detector/parameter_claims.py:112` (also :162, :231):
```python
if _values_compatible(value_a, value_b, claim_a=claim_a, claim_b=claim_b):
    continue
```
The `_values_compatible` import alias resolves to `propstore/value_comparison.py:71-110`. The unit-aware branch at lines 95-104 fires only when `forms` and `concept_form` are passed; these are not. Confirmed via grep: every call site in `conflict_detector/` passes neither argument. The function falls through to:
```python
if isinstance(value_a, (int, float)) and isinstance(value_b, (int, float)):
    return abs(float(value_a) - float(value_b)) < tolerance
```
i.e. raw scalar diff with `1e-9` tolerance, no SI normalisation. `200 Hz` vs `0.2 kHz` triggers a conflict every time. This is not subtle — it is the main parameter-conflict path.

### Algorithm tier-collapse (Codex #33; reframed under D-14)

`propstore/conflict_detector/algorithms.py:55-56` currently whitelists a tier set that excludes `Tier.SYMPY` and `Tier.PARTIAL_EVAL`. Per D-14 the BYTECODE tier is deleted entirely from ast-equiv (commit message preserves recovery path). Post-D-14 the ast-equiv enum is `{Tier.NONE, Tier.CANONICAL, Tier.SYMPY, Tier.PARTIAL_EVAL}`; `Tier.BYTECODE` is no longer a valid enum value.

WS-P's fix targets the post-D-14 enum: **the algorithm conflict-suppression whitelist is `{Tier.CANONICAL, Tier.SYMPY, Tier.PARTIAL_EVAL}`** — each of these tiers represents a true-equivalence proof and suppresses a conflict. `Tier.NONE` is the unknown fallback (ast-equiv could not decide); it does NOT suppress a conflict, and conflict-detector treats `NONE` results as undecided rather than as evidence of agreement or disagreement. There is no documented rationale for the historical exclusion of SYMPY and PARTIAL_EVAL; the comment is silent. ast-equiv's tier hierarchy is being inverted by the current code — the symbolic and partial-evaluation tiers are stronger mathematical proofs than CANONICAL alone, but propstore treats them as unaccepted.

### `extract_names` misuse (Codex #34)

`propstore/families/claims/passes/checks.py:10` imports `extract_names` from `ast_equiv`. `propstore/families/claims/passes/checks.py:819-827`:
```python
ast_names = extract_names(tree)
unbound = ast_names - KNOWN_BUILTINS - declared_names
for name in sorted(unbound):
    _record(diagnostics, level="warning",
        message=(f"algorithm claim '{cid}' body references "
                 f"name '{name}' not declared in variables"), ...)
```

`../ast-equiv/ast_equiv/canonicalizer.py:47-55`:
```python
def extract_names(tree: ast.Module) -> set[str]:
    """Walk AST and collect all Name node ids, plus function argument names."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.arg):
            names.add(node.arg)
    return names
```
`extract_names` returns *every* identifier — assignment targets, loop variables, comprehension targets, function parameters, locally-assigned temporaries, the lot. Nothing is removed for binding scope. A body like
```python
def algorithm(x):
    y = x + 1
    return y
```
emits `{"algorithm", "x", "y"}`. After subtracting builtins and declared inputs `{"x"}`, `y` shows up as "name not declared in variables." The pass is structurally unable to perform free-variable analysis; it needs a proper scope walker (or the soon-to-exist ast-equiv free-vars helper from WS-O-ast).

### Affine temperature delta (G-H2)

`propstore/dimensions.py:80-81`:
```python
if conv.type == "affine":
    return value * conv.multiplier + conv.offset
```
For a form with `degC` conversion `multiplier=1.0, offset=273.15`, the function is correct for absolute temperatures (5 °C → 278.15 K) but wrong for differences (Δ5 °C should be 5 K, not 278.15 K). Pint distinguishes `degC` (absolute) from `delta_degC` (differential). Propstore's form schema has only the absolute form. Any claim describing a temperature *change* in Celsius normalises to a quantity ~273 K too large.

### EnumSort cached against mutable registry (G-M3)

`propstore/z3_conditions.py:124,171`. The solver constructor stores `self._registry = registry` directly. `dict[str, ConceptInfo]` is mutable and not snapshotted. Once an `EnumSort` is built and cached, mutating `info.category_values` for the underlying concept does not invalidate the cache. The fingerprint check at the call boundary catches `CheckedCelExpr` with stale fingerprint, but raw `CelExpr` paths re-check against the current registry, succeed, and are then translated using the stale enum.

### `_normalize_checked_conditions` source-string dedup (G-M7)

`propstore/cel_types.py:91-105`:
```python
def _normalize_checked_conditions(conditions: Iterable[CheckedCelExpr]) -> tuple[CheckedCelExpr, ...]:
    by_source: dict[str, CheckedCelExpr] = {}
    for condition in conditions:
        source = str(condition.source)
        ...
```
Equivalent conditions like `a < b` and `b > a` are stored as distinct keys. The fingerprint check at line 99 only catches registry mismatch on identical source strings; it does not perform any logical normalisation. Downstream Z3 treats them as distinct conjuncts; no logical deduplication happens at any layer.

## First failing tests (write these first; they MUST fail before any production change)

Naming convention: every symbolic-equivalence test that depends on a mathematical domain encodes that domain in its filename via `test_<identity>_under_<domain>.py`, and the assertion body asserts BOTH (a) the equivalence holds when the domain is asserted AND (b) the comparison returns `UNKNOWN` (not `EQUIVALENT`, not `DIFFERENT`) when the domain is not asserted. This convention is mandatory; new equivalence tests added during WS-P implementation must follow it.

1. **`tests/test_cel_ternary_unification.py`** (new) — first failing test for WS-P
   - `1 ? true : false` → `check_cel_expr` returns errors (condition not boolean).
   - `cond ? 1 : "x"` (where `cond` is a registered BOOLEAN concept) → `check_cel_expr` returns errors (branch type mismatch).
   - `cond ? F0 : F1` where both F0 and F1 are QUANTITY → no error; returns NUMERIC.
   - `cond ? "a" : "b"` where both are STRING → no error; returns STRING.
   - **Must fail today**: `cel_checker.py:586-590` does no boolean check on condition and discards false-branch type.

2. **`tests/test_z3_division_definedness.py`** (new) — replaces the FreshConst-based draft
   - Build CEL `enabled || (1 / x > 0)` with `enabled: BOOLEAN`, `x: QUANTITY`.
   - Query `is_condition_satisfied` with `bindings={"enabled": True, "x": 0.0}`.
   - Expected: SAT regardless of `x` (no `x != 0` precondition required when `enabled=true`). Today returns UNSAT because `x != 0` is conjuncted globally.
   - Add ternary version: `enabled ? true : (1 / x > 0)` — same expectation.
   - Add positive-direction case: `1/x > 0 ∧ x == 0` must be UNSAT (the definedness predicate forbids the formula from being satisfied through an undefined denominator).
   - Add CEL-error-policy case: `(1/x > 0) || true` must be SAT under `x == 0` (right disjunct true; left disjunct's definedness is irrelevant).
   - **Must fail today**: per `z3_conditions.py:410-414` and `core/conditions/z3_backend.py:33-35`.

3. **`tests/test_parameter_conflict_unit_aware.py`** (new)
   - Two parameter claims for the same QUANTITY concept with form `frequency`:
     - claim_a: `value=200, unit="Hz"`
     - claim_b: `value=0.2, unit="kHz"`
   - Run `detect_parameter_conflicts` (the orchestrator-level path, not `_values_compatible` directly).
   - Expected: no conflict.
   - Inverse: `200 Hz` vs `300 Hz` → conflict.
   - **Must fail today**: `parameter_claims.py:112` does not thread forms; raw float diff > 1e-9 fires.

4. **`tests/test_equation_orientation.py`** (new)
   - `x = y` and `y = x` → `compare_equation_claims` returns `EQUIVALENT`.
   - `x = y` and `x = z` → `DIFFERENT`.
   - `x = y` and `2*y = 2*x` → `EQUIVALENT`.
   - **Must fail today**: `equation_comparison.py:108-112` compares `str(diff)`; sign-flipped equations differ.

5. **`tests/test_log_product_under_positive_reals.py`** (new) — Codex 1.11 domain-aware identity
   - With domain assumption `x > 0 ∧ y > 0` declared on the comparison call: `log(x*y) = log(x) + log(y)` → `EQUIVALENT`.
   - Without domain assumption: `log(x*y) = log(x) + log(y)` → `UNKNOWN` (must NOT be `EQUIVALENT`; must NOT be `DIFFERENT`).
   - With domain assumption `x > 0 ∧ y > 0`: `log(x*y) = log(x) - log(y)` → `DIFFERENT`.
   - **Must fail today**: there is no domain-assumption channel on `compare_equation_claims`; the `cancel(expand(...))` pipeline does not commute log/product even when assumptions would make it valid; and there is no `UNKNOWN` enum to return.

6. **`tests/test_exp_sum_under_reals.py`** (new) — Codex 1.11 domain-aware identity
   - With `a, b ∈ ℝ` (default real-number domain assertion): `exp(a + b) = exp(a) * exp(b)` → `EQUIVALENT`.
   - Without explicit real-domain assertion (e.g. complex variables possible per assumption): comparison returns `UNKNOWN`. (sympy's default symbol domain is complex; the test asserts the comparison call respects the explicit assumption channel rather than relying on sympy default symbol kinds.)
   - **Must fail today**: same reasons as test 5.

7. **`tests/test_sqrt_square_under_nonnegative_reals.py`** (new) — Codex 1.11 domain-aware identity
   - With domain assumption `x ≥ 0`: `sqrt(x*x) = x` → `EQUIVALENT`.
   - Without: `sqrt(x*x) = x` → `UNKNOWN` (the correct algebraic answer is `|x|`, not `x`, over reals).
   - With domain assumption `x ∈ ℝ` only (no sign constraint): `sqrt(x*x) = abs(x)` → `EQUIVALENT`.
   - Without any domain assumption: same → `UNKNOWN`.
   - **Must fail today**: same reasons.

8. **`tests/test_equation_signature_role_invariance.py`** (new)
   - Build two ConflictClaim objects with identical equation text and identical concept ids on each variable, but `role="dependent"` swapped between them.
   - Call `equation_signature` on each.
   - Expected: equal signatures.
   - **Must fail today**: `equation_comparison.py:59-66` uses role to pick the dependent concept.

9. **`tests/test_sympy_generator_no_lhs_drop.py`** (new)
   - `generate_sympy_with_error("y = f(x)")` and `generate_sympy_with_error("z = f(x)")` must NOT compare equal at any callsite that uses the result as an equation identity.
   - Either:
     - (a) the function is renamed to `generate_sympy_rhs` and a new `generate_sympy_equation` is the equation-identity API, OR
     - (b) the function returns a structured object that includes the LHS.
   - **Must fail today**: trivially. `generate_sympy("y = f(x)") == generate_sympy("z = f(x)") == "f(x)"`.

10. **`tests/test_algorithm_sympy_tier_not_conflict.py`** (new)
    - Use a known algorithm pair where ast-equiv returns `equivalent=True, tier=Tier.SYMPY`.
    - Run `detect_algorithm_conflicts`.
    - Expected: no conflict record (or a non-conflict record with reason "equivalent under sympy tier"). What WS-P forbids is the current behaviour: full conflict record.
    - Add a parallel sub-case: `equivalent=True, tier=Tier.PARTIAL_EVAL` — same expectation (no conflict). PARTIAL_EVAL is proof-strength enough to suppress conflict.
    - Add a negative sub-case: `equivalent=False, tier=Tier.NONE` — conflict record IS produced (NONE does NOT suppress conflict; it means undecided).
    - Test fixture must NOT reference `Tier.BYTECODE` — that enum value is gone post-D-14.
    - **Must fail today**: `algorithms.py:55` whitelists only the historical CANONICAL+BYTECODE set; SYMPY and PARTIAL_EVAL excluded.

11. **`tests/test_algorithm_free_variable_locals.py`** (new)
    - Algorithm body `def algorithm(x):\n    y = x + 1\n    return y`, declared variables `[{"symbol": "x", ...}]`.
    - Run the algorithm-claim validation pass.
    - Expected: no warning about `y`.
    - **Must fail today**: `checks.py:819` calls `extract_names` which includes `y`.

12. **`tests/test_temperature_delta_unit.py`** (new)
    - Form schema gains `delta_degC` / `delta_degF` variants.
    - Claim `value=5, unit="delta_degC"` normalises to 5 K.
    - Claim `value=5, unit="degC"` normalises to 278.15 K.
    - **Must fail today**: schema does not have the variant; affine path silently mishandles deltas.

13. **`tests/test_cel_float_exponent.py`** (new — overlap with WS-D)
    - `check_cel_expr("F0 > 1e9", registry)` parses successfully.
    - **Must fail today**: per `cel_checker.py:183`, `1e9` tokenises as INT_LIT 1 followed by `e9`.

14. **`tests/test_cel_string_escapes.py`** (new — overlap with WS-D)
    - `"line1\nline2"` produces a STRING value containing a newline; `"°"` produces "°".
    - **Must fail today**: per `cel_checker.py:209` only `\"`, `\'`, `\\` are recognised.

15. **`tests/test_workstream_p_done.py`** (new — gating sentinel)
    - `xfail` until WS-P closes; flips on the final commit.

## Production change sequence

Each step lands in its own commit with `WS-P step N — <slug>`.

### Step 1 — CEL ternary type-rule enforced
Edit `propstore/cel_checker.py:586-590`:
- Resolve the condition's type. If not in `{BOOLEAN, UNKNOWN}`, append a `CelError`.
- Resolve both branch types. If not equal (and neither is UNKNOWN), append a `CelError`. The ternary type is the unified type, defaulting to UNKNOWN on mismatch (per Pierce TaPL §11.8 T-If).
- For `STRING` branches against extensible-category mismatched values, defer to the existing `_check_category_value` rule.

Acceptance: `tests/test_cel_ternary_unification.py` turns green.

### Step 2 — Z3 division semantics via explicit definedness predicate (Codex 1.10)

The earlier draft proposed `If(right == 0, FreshConst(undef), left/right)`. That encoding is **unsound**: an unconstrained `FreshConst` lets Z3 pick *any* value at the undefined point, which makes formulas containing the divided expression satisfiable through a chosen "convenient" undefined value. Z3 will treat the `FreshConst` as an existential the solver can instantiate freely. This does not preserve CEL's runtime/error semantics — it manufactures satisfiability where the underlying expression has no defined value.

The correct encoding models definedness explicitly. Every translated subexpression carries (or has lifted around it) a Boolean `defined` predicate. Boolean combinators short-circuit on `defined=False` per CEL's error policy. The top-level constraint is rewritten so that, when an operand is undefined, the constraint behaves the way CEL says it does — never as "any value the solver wants."

**Encoding contract (binding rule per Codex 1.10):**

For every translated CEL subexpression, the backend produces a pair `(value, defined)` where:
- `value` is a Z3 term of the surface CEL type (Real, Int, Bool, EnumSort, etc.).
- `defined` is a Z3 Bool term over the free variables of the subexpression.
- `defined=True` is the constant `BoolVal(True)` for total operators (constants, declared variables, addition, multiplication, comparisons of total values, AND/OR/NOT of total Booleans).
- `defined` for `a / b` is `(b != 0) ∧ defined(a) ∧ defined(b)`.
- `defined` for `a % b` follows the same rule.
- `defined` for any partial CEL operation (e.g. a future `nth(list, i)`) follows the operation's spec.

Combinators on `(value, defined)`:
- Arithmetic `op(a, b) = (a.value op b.value, a.defined ∧ b.defined)`.
- Comparison `cmp(a, b) = (a.value cmp b.value, a.defined ∧ b.defined)`.
- Boolean AND with CEL's commutative-error policy: `and(a, b).defined = (a.value=false ∧ a.defined) ∨ (b.value=false ∧ b.defined) ∨ (a.defined ∧ b.defined)`. `and(a, b).value = a.value ∧ b.value` (the value is irrelevant when `defined=False`).
- Boolean OR mirror: `or(a, b).defined = (a.value=true ∧ a.defined) ∨ (b.value=true ∧ b.defined) ∨ (a.defined ∧ b.defined)`.
- Ternary: `if c then t else f`.`defined = c.defined ∧ ((c.value ∧ t.defined) ∨ (¬c.value ∧ f.defined))`. Value picks the appropriate branch.
- NOT: passes `defined` through, negates `value`.

Top-level constraint emitted to Z3:

```
constraint = If(defined(top), value(top), True)   # for top-level Bool conditions
```

The reading: when the surface formula is undefined, the constraint trivially holds (no spurious unsatisfiability). When defined, the constraint is the CEL value. This is an asymmetric encoding deliberately — undefinedness must not contradict the formula, but it must also not satisfy a stronger surface claim. For surface formulas that are *required* to be defined (assertions, unit tests of denominator non-zeroness), callers explicitly query `solver.add(defined(top))` separately.

**Z3 must NOT use unconstrained fresh constants as a stand-in for "undefined."** Codex 1.10's failure mode (FreshConst lets Z3 pick any value) is forbidden. Each `defined` predicate is a Boolean term constructed from observable facts about its operands; nowhere does the encoding introduce a free real-valued existential at an undefined point.

**Implementation locations:**
- `propstore/core/conditions/z3_backend.py:33-35,121-125`: replace `_Projection.guards: list[Bool]` with `_Projection.defined: Bool`. Every `_Projection` constructor computes `defined` per the rules above. The terminal projection-to-constraint step at `condition_ir_to_z3` becomes `If(projection.defined, projection.term, BoolVal(True))`.
- `propstore/z3_conditions.py:252-260, 405-418`: same rewrite in the legacy translator. Drop `self._current_guards`; pair each translated AST node with its `defined` predicate; combine per the rules above.
- `propstore/z3_conditions.py:124,171`: unaffected by Step 2; covered by Step 12.

**Tests gating Step 2:**
- `tests/test_z3_division_definedness.py` (test 2 above) — green.
- Existing Z3 tests stay green (regression gate).
- New negative test: a fixture builds `(1/x > 0)` and asserts that querying `defined(formula) ∧ x == 0` is UNSAT (denominator non-zero is observable from the definedness predicate, not silently conjuncted).

### Step 3 — Parameter conflicts unit-aware in main path
`propstore/conflict_detector/parameter_claims.py:112,162,231`: thread `forms=` and `concept_form=` through the call. Plumb forms in via `orchestrator.py` and `concept_form` from `ConflictClaim` (extend the dataclass if needed; ConflictClaim already has `unit` per `models.py:53`, but no concept-form pointer).

If sidecar canonical SI values are already computed at ingest, prefer them. Codex ws-04 production-change item 1 prescribes this.

Remove raw-value comparison from the main path when units are known. Keep the scalar-fallback only for unit-free numeric concepts.

Acceptance: `tests/test_parameter_conflict_unit_aware.py` turns green.

### Step 4 — Equation orientation invariance
`propstore/equation_comparison.py:178`: replace `str(diff)` with a sign-normalised canonical. Two options:
- **4a**: `diff = sympy.cancel(sympy.expand(lhs - rhs))`; if `diff` has a leading negative monomial (per `diff.as_ordered_terms()[0].could_extract_minus_sign()`), use `-diff` instead. Then `str(-diff)`.
- **4b**: canonical is the pair `frozenset({str(diff), str(-diff)})`. Equality is set equality.

Either is correct; 4a is shorter. Symbol ordering inside `str` is stable per sympy's deterministic ordering; reverse the symbol list and pick whichever string is lexicographically smaller, if needed.

Acceptance: `tests/test_equation_orientation.py` turns green.

### Step 5 — Domain-aware equivalence with explicit `UNKNOWN` (Codex 1.11)

**The principle (Codex 1.11):** No algebraic identity is accepted outside its mathematical domain. `log(x*y) = log(x) + log(y)` is true on `x > 0 ∧ y > 0` and *not* true (as an equation over the reals) without that constraint. The current `cancel(expand(...))` pipeline cannot decide either form; even a richer `simplify`/`logcombine` pipeline can only return `EQUIVALENT` honestly when the domain is asserted. Without the domain, the correct answer is `UNKNOWN` — never `EQUIVALENT` (because the unrestricted identity is false), never `DIFFERENT` (because the identity holds on a substantial subset of the domain).

**Status enum change:** Add `EquationComparisonStatus.UNKNOWN` (or rename the existing `INCOMPARABLE`-for-parse-error to `PARSE_ERROR` and reuse `INCOMPARABLE` for "couldn't decide"). WS-P picks the additive change: introduce `UNKNOWN` as a distinct value; keep `INCOMPARABLE` for parse failure; document both in `EquationComparisonStatus`'s docstring.

**Domain channel:** `compare_equation_claims` gains a `domain_assumptions: Sequence[DomainAssumption]` keyword argument. Each `DomainAssumption` is a typed declaration: `Positive("x")`, `NonNegative("y")`, `Real("a")`, `Integer("n")`, etc. Internally these map to sympy assumptions on the corresponding `Symbol`s before the simplify pipeline runs.

Pipeline:
1. Parse both sides; build sympy expressions with assumption-tagged symbols (default: complex).
2. Apply caller-provided domain assumptions.
3. Compute `diff = simplify(logcombine(powsimp(lhs - rhs)))`.
4. If `diff == 0` under the asserted assumptions: return `EQUIVALENT`.
5. If `diff` is a nonzero rational polynomial in the asserted-assumption symbols: return `DIFFERENT`.
6. Otherwise: return `UNKNOWN`.

**Why steps 4 and 5 are honest:** `simplify` over real-positive symbols is complete enough for the textbook log-laws and exponent-laws tests in tests 5–7; it is not complete in general. When `simplify(diff)` returns a nonzero transcendental expression with assumption-tagged symbols, the procedure cannot conclude `DIFFERENT` (the expression might be zero on the asserted domain but the engine can't prove it). Hence `UNKNOWN`.

**Test naming convention (Codex 1.11):** Every domain-dependent equivalence test follows `test_<identity>_under_<domain>.py`. Files added by Step 5: `test_log_product_under_positive_reals.py`, `test_exp_sum_under_reals.py`, `test_sqrt_square_under_nonnegative_reals.py`. Each asserts BOTH:
- The equivalence holds when the domain is asserted (`EQUIVALENT`).
- The comparison returns `UNKNOWN` (not `EQUIVALENT`, not `DIFFERENT`) when the domain is not asserted.

This convention applies to every symbolic-equivalence test added to the suite from this step forward, not just the three named here. Future identities (e.g. `cos²(x)+sin²(x) = 1`, which is unconditional over reals but undefined for symbolic complex-with-NaN values) follow the same naming and assertion shape.

Acceptance: `tests/test_log_product_under_positive_reals.py`, `tests/test_exp_sum_under_reals.py`, `tests/test_sqrt_square_under_nonnegative_reals.py` all green; `EquationComparisonStatus.UNKNOWN` exists and is documented; `compare_equation_claims` accepts `domain_assumptions=`; no test in the suite asserts `EQUIVALENT` for an algebraic identity that requires a domain not declared on that test.

### Step 6 — Equation signature role-invariance
`propstore/equation_comparison.py:53-73`: drop the `role == "dependent"` partition. Signature becomes the multiset of concept ids (sorted tuple). If the conflict-detector relied on the role separation for any operational reason — verify by reading every caller of `equation_signature` — replace that dependency with the orientation-invariant canonical from Step 4.

Acceptance: `tests/test_equation_signature_role_invariance.py` turns green; no caller of `equation_signature` depends on the dependent/independent split.

### Step 7 — SymPy generator: split RHS from equation identity
- Rename `generate_sympy_with_error` and `generate_sympy` to `generate_sympy_rhs_with_error` and `generate_sympy_rhs`. Per Q's "no fallbacks / no shims" rule (`feedback_no_fallbacks.md`), no alias.
- Add `generate_sympy_equation(text)` returning a structured object with both LHS and RHS sympy expressions. Equation-identity callers migrate to this.
- Audit every caller of the old name — fix every one. Rip out the old interface.

Acceptance: `tests/test_sympy_generator_no_lhs_drop.py` turns green; grep confirms no remaining caller treats `generate_sympy_rhs` output as equation identity.

### Step 8 — Algorithm tier semantics (post-D-14)

Per D-14 the BYTECODE tier is deleted from ast-equiv. The post-D-14 ast-equiv tier set is `{Tier.NONE, Tier.CANONICAL, Tier.SYMPY, Tier.PARTIAL_EVAL}` — `Tier.BYTECODE` no longer exists as an enum value.

`propstore/conflict_detector/algorithms.py:55`:
- Replace the historical whitelist with **`{Tier.CANONICAL, Tier.SYMPY, Tier.PARTIAL_EVAL}`** — the three proof-strength tiers that suppress conflict via true equivalence. `Tier.NONE` (the unknown fallback per WS-O-ast post-D-14) does NOT suppress conflict.
- Document the policy in the dataclass docstring of `ConflictRecord`: "Conflict is suppressed when ast-equiv returns `equivalent=True` at tier CANONICAL, SYMPY, or PARTIAL_EVAL — each is a true-equivalence proof. NONE indicates ast-equiv could not decide; conflict is not suppressed in that case." Cite ast-equiv's post-D-14 tier hierarchy.
- If propstore decides to surface tier-SYMPY or tier-PARTIAL_EVAL equivalence as a *non-conflict diagnostic* (e.g. "equivalent but not lexically identical"), the result is a separate record type, not a `ConflictRecord`.
- Audit every other `Tier.BYTECODE` reference in the propstore codebase — there must be none after this step. Grep gate: `git grep "Tier\.BYTECODE" propstore/` returns zero hits. Same grep against `tests/` returns zero hits.

Acceptance: `tests/test_algorithm_sympy_tier_not_conflict.py` turns green (covering both SYMPY and PARTIAL_EVAL sub-cases plus the NONE negative); no `Tier.BYTECODE` reference remains anywhere in `propstore/` or `tests/`.

### Step 9 — Free-variable validation
- WS-O-ast resolved the API as `extract_free_variables(tree)` exported from ast-equiv. Import it directly.
- Replace `ast_names = extract_names(tree)` at `checks.py:819` with `ast_free = extract_free_variables(tree)` and use `ast_free` as the free-variable set (no further subtraction of bound names needed — `extract_free_variables` already excludes loop variables, comprehension targets, function parameters, and locally-assigned temporaries by construction).

Depends on WS-O-ast pin bump to a version that exports `extract_free_variables`.

Acceptance: `tests/test_algorithm_free_variable_locals.py` turns green.

### Step 10 — Temperature affine deltas
- Extend the form YAML schema to include a `delta_unit` block alongside `unit`. `delta_degC`, `delta_degF` map to `delta_K` with `multiplier=1.0` (degC) or `5/9` (degF), `offset=0`.
- `dimensions.py:normalize_to_si` checks `unit` against `form.delta_conversions` first, then `form.conversions`. No fallthrough.
- Add `pint`-side: register `delta_degC`/`delta_degF` so `can_convert_unit_to` agrees.

Acceptance: `tests/test_temperature_delta_unit.py` turns green.

### Step 11 — CEL float exponent + escapes (overlaps with WS-D)
- `cel_checker.py:183` lexer regex extended to `\d+(\.\d+)?([eE][+-]?\d+)?`.
- `cel_checker.py:209` escape table extended to `\n`, `\t`, `\r`, `\u{...}`/`\uXXXX`, `\xXX`, `\0` by reading the local CEL spec checkout at `~/src/cel-spec` during implementation. Document any explicit decision to *not* support `\u` if the local CEL language reference is silent.
- Coordinate with WS-D: if WS-D rewrites the CEL parser entirely, this step folds into WS-D and WS-P inherits a passing test.

Acceptance: `tests/test_cel_float_exponent.py`, `tests/test_cel_string_escapes.py` green.

### Step 12 — Defensive registry snapshot in Z3 solver
`propstore/z3_conditions.py:124`: `self._registry = MappingProxyType(dict(registry))` at construction. If callers want to reflect registry mutations, they must build a new solver — which is correct because the EnumSort cache is keyed by content.

Acceptance: a property test mutating the original dict after solver construction does not affect the solver's enum sorts.

### Step 13 — Pint registry / form-units sync
`propstore/unit_dimensions.py:register_form_units` writes into `_symbol_table` only. Add a parallel `pint`-side write: define each `extra_units` entry on the module-level `ureg`. Conflict handling: if a unit symbol is already defined with different dimensions, raise — Q's "imports are opinions" rule says we never silently merge.

Acceptance: a property test asserts that any unit declared on a form is also `can_convert_unit_to(unit, target_unit_with_same_dims)` → True.

### Step 14 — Close gaps and gate
- `docs/gaps.md`: remove entries for the closed findings; add `# WS-P closed <sha>`.
- Flip `tests/test_workstream_p_done.py` from xfail to pass.
- Update STATUS line in this file to `CLOSED <sha>`.

## Acceptance gates

Before declaring WS-P done, ALL must hold:

- [x] `uv run pyright propstore` — passed with 0 errors.
- [x] `uv run lint-imports` — passed.
- [x] `powershell -File scripts/run_logged_pytest.ps1 -Label WS-P tests/test_cel_ternary_unification.py tests/test_z3_division_definedness.py tests/test_parameter_conflict_unit_aware.py tests/test_equation_orientation.py tests/test_log_product_under_positive_reals.py tests/test_exp_sum_under_reals.py tests/test_sqrt_square_under_nonnegative_reals.py tests/test_equation_signature_role_invariance.py tests/test_sympy_generator_no_lhs_drop.py tests/test_algorithm_sympy_tier_not_conflict.py tests/test_algorithm_free_variable_locals.py tests/test_temperature_delta_unit.py tests/test_cel_float_exponent.py tests/test_cel_string_escapes.py tests/test_workstream_p_done.py` — passed, log `logs/test-runs/WS-P-20260430-180542.log`.
- [x] Existing focused suites stay green: `tests/test_cel_checker.py`, `tests/test_cel_types.py`, `tests/test_cel_validation.py`, `tests/test_checked_condition_ir.py`, `tests/test_value_comparison_units.py`, `tests/test_equation_comparison.py`, `tests/test_equation_comparison_properties.py`, `tests/test_conflict_detector.py` — passed, log `logs/test-runs/WS-P-focused-20260430-180610.log`.
- [x] Full suite — passed, `3547 passed, 2 skipped`, log `logs/test-runs/WS-P-full-final-20260430-182050.log`.
- [x] `tests/conftest.py` does not pull in any deleted symbol.
- [x] `git grep "Tier\.BYTECODE" -- propstore tests` returns zero hits.
- [x] `git grep "FreshConst" -- propstore` returns zero hits.
- [x] Every symbolic equivalence test added by WS-P follows `test_<identity>_under_<domain>.py` naming and asserts BOTH the in-domain `EQUIVALENT` and out-of-domain `UNKNOWN` cases.
- [x] WS-P property-based gates from `PROPERTY-BASED-TDD.md` are included in the logged WS-P run or focused companion runs.
- [x] `docs/gaps.md` has no open rows for the findings listed above; closure is recorded under Closed gaps.
- [x] STATUS line is `CLOSED 99f2a666`.

## Done means done

WS-P is done when:
- T2.4 / Codex #30 / G-H1 (CEL ternary): green test gating boolean-condition AND branch-type unification.
- T2.12 / Codex #29 / G-H4 (Z3 division semantics): green test for `enabled || (1/x>0)` SAT under `x=0` via the definedness-predicate encoding (Codex 1.10).
- Codex #28 (parameter unit-aware conflict): green test for 200 Hz vs 0.2 kHz.
- Codex #31 (equation orientation): green test.
- Codex #32 (sympy LHS drop): renamed APIs and migrated callers.
- Codex #33 (algorithm tier collapse) + Codex 1.9 / D-14 (bytecode tier deletion): SYMPY tier accepted; BYTECODE references gone everywhere.
- Codex #34 (extract_names misuse): replaced with real free-variable analysis.
- G-H2 (delta-degC): schema variant + green test.
- G-H3 + Codex 1.11 (domain-aware equivalence): `UNKNOWN` enum exists, `domain_assumptions` parameter exists, every symbolic-equivalence test follows the `test_<identity>_under_<domain>.py` convention with both in-domain and out-of-domain assertions.
- G-M1..M8 (cluster G MED): each has either a green test or a documented in-source rationale why it remains.
- T2.13 / G-M5 / G-M6 (CEL parser gaps): float exponent + standard escapes accepted.

If any one is not true, WS-P stays OPEN. No "we'll get the parser gaps in a follow-up." Either it's in scope and closed, or it's explicitly removed from this WS in this file (and moved to a successor WS) before declaring done.

## Papers / specs referenced

### In repo (PDFs present, notes.md absent — flagged as a separate bug, see L11)

- `papers/Pierce_2002_TypesProgrammingLanguages` — TaPL §11.8 (conditional T-If rule), §22 (subtyping/coercion). Cited for ternary type unification (Step 1) and for the absence of legitimate coercive subsumption in unary `-`/`!` (G-M2).
- `papers/Kennedy_1997_RelationalParametricityUnitsMeasure` — Hindley-Milner extended with unit polymorphism. Cited for the architectural-question Q2 (units in CEL types vs parallel claim-value validation). WS-P does NOT add Kennedy-style polymorphism; that is a separate decision.
- `papers/Knuth_1970_SimpleWordProblems` — Knuth-Bendix completion. Cited for theory completeness of `cancel(expand(...))` — it is an instance of one rewrite system for one theory (rational polynomials), not a completion procedure. WS-P Step 5 acknowledges incompleteness honestly via `UNKNOWN` and forces every domain-restricted identity to declare its domain assumptions explicitly.
- `papers/Pustejovsky_1991_GenerativeLexicon`, `papers/Pustejovsky_2013_DynamicEventStructureHabitat` — Q8 (qualia not in CEL bindings). WS-P does NOT integrate qualia; flagged as architectural decision for Q.
- `papers/Bjorner_2014_MaximalSatisfactionZ3`, `papers/Moura_2008_Z3EfficientSMTSolver` — UNKNOWN tri-valued logic discipline. WS-P preserves the existing `SolverUnknown` discipline (already correct in z3_conditions.py); Step 12 strengthens against registry-mutation re-entry. Step 2's definedness-predicate encoding follows the standard SMT pattern of explicit partiality (the alternative "uninterpreted with side condition" pattern is what `FreshConst` would have given us, and is rejected per Codex 1.10).
- `papers/Sebastiani_2015_OptiMathSATToolOptimizationModulo` — Optimization modulo theories. NOT used in WS-P; cluster G confirmed propstore has no optimization queries.
- `papers/Docef_2023_UsingZ3VerifyInferencesFragmentsLinearLogic` — linear-logic encoding. NOT used in WS-P.
- `papers/Cousot_1977_AbstractInterpretation` — abstract interpretation. NOT used; cel_checker is concrete-syntactic, not abstract.
- `papers/Bachmair_2001_ResolutionTheoremProving` — newly retrieved KB. Background only; not directly applied.

### Pending external retrieval (declared dependency)

- **Google CEL specification** (`~/src/cel-spec`, including language and type-system docs). Per D-28 this is an implementation reference, not a prerequisite workstream. The WS-P engineer reads the local language reference while implementing string escapes, float exponents, ternary typing, and Boolean combinator behavior. CEL ternary semantics in Step 1 follow the documented conditional rule; CEL's documented commutative-error policy for AND/OR is what Step 2's Boolean combinator rules implement.

### Why no `notes.md` for these papers

Confirmed: `papers/Pierce_2002_TypesProgrammingLanguages/`, `papers/Kennedy_1997_RelationalParametricityUnitsMeasure/`, and `papers/Knuth_1970_SimpleWordProblems/` contain only `paper.pdf` and `metadata.json`. No `notes.md`. Cluster G's L11 finding documents this. WS-P does not write the notes — that is a paper-faithful workflow concern outside this stream — but the absence is the reason WS-P's paper-faithfulness arguments cite the published works directly rather than version-controlled summaries. If notes.md files appear before WS-P merges, cite them inline.

## Cross-stream notes

- **WS-O-bri (bridgman)**: WS-P Step 10 (delta units) and Step 13 (form-units / pint sync) ride on a stable `bridgman.dims_of_expr` interface. Codex finding (cluster Q-bridgman cross-link) flags inconsistent `DimensionalError` handling at propstore call sites — that's WS-O-bri scope. WS-P assumes WS-O-bri lands first; if not, WS-P must include defensive `try/except DimensionalError` at every dimensions-call site touched here, with the explicit comment `# TEMP: WS-O-bri unblocks principled handling`.
- **WS-O-ast (ast-equiv)**: WS-P Step 9 (free-variable analysis) consumes the resolved `extract_free_variables(tree)` helper exported from ast-equiv (per WS-O-ast). Step 9 is a one-line import change once the ast-equiv pin is bumped to a version that exports it. WS-P Step 8 depends on the post-D-14 ast-equiv tier enum — `Tier.BYTECODE` is gone; the propstore-side fix lands only after the ast-equiv pin is bumped to a version with that enum value removed.
- **WS-D (CEL parser)**: WS-P Steps 11 and Step 1 touch `cel_checker.py`. If WS-D rewrites the lexer/parser entirely, WS-P Step 11 folds into WS-D. Step 1 (ternary type rule) lives in `_resolve_type` and is independent of parser shape.
- **WS-A (schema fidelity)**: foundational. WS-P's full-suite acceptance gate uses the WS-A-rebased baseline.
- **WS-N (architecture)**: WS-P does not change `forbidden`/`layered` import-linter contracts. If WS-N reshuffles `propstore/conflict_detector/` or `propstore/families/claims/passes/`, WS-P's call-site edits in Steps 3, 8, 9 may need rebase but the logic is unchanged.

## What this WS does NOT do

- Does NOT add Kennedy-style unit polymorphism to the CEL type system. Q2 stays open as an architectural question for Q.
- Does NOT integrate Pustejovsky qualia roles into CEL bindings (Q8). The CEL bindings remain provenance/metadata-only.
- Does NOT add MaxSAT or OptiMathSAT optimisation queries.
- Does NOT add quantifiers to CEL — the quantifier-free fragment is a deliberate decidability decision.
- Does NOT rewrite the CEL parser. Targeted lexer extensions only (Step 11).
- Does NOT close `partition_equivalence_classes` UNKNOWN-graceful-degradation (G-M11) — that's a Z3 batch-policy item; flagged for a follow-up WS.
- Does NOT add per-batch timeout budget (G-M12). Same reason.
- Does NOT change `value_comparison.intervals_compatible` tolerance scaling (L13). That's WS-O-vc territory.
- Does NOT add a `bridgman` exception-handling normalisation pass at every propstore call site — that is WS-O-bri's scope. WS-P only consumes the stable interface WS-O-bri produces.
- Does NOT rename `cel_checker` to "syntactic gate" or downgrade its docs (Q1) — that documentation decision is for the architecture stream once the type-rule fixes here land.
- Does NOT use unconstrained `FreshConst` values to model partial functions in Z3 (Codex 1.10). Definedness predicates only.
- Does NOT accept any algebraic identity outside its mathematical domain (Codex 1.11). Domain-restricted equivalences require explicit `domain_assumptions=` declarations; without them the comparison returns `UNKNOWN`.
- Does NOT reference `Tier.BYTECODE` anywhere (Codex 1.9 / D-14). The enum value is deleted upstream; propstore enforces zero remaining references at the acceptance gate.
