# Cluster G: CEL, units, equations, Z3, sympy

Reviewer: review-cluster-G-claude
Date: 2026-04-26
Method: file-by-file read with cross-reference to ast-equiv source. Tests were read but not run. Paper PDFs are present in the repo but no `notes.md` files exist for the listed papers (Pierce 2002, Kennedy 1997, Pustejovsky 1991/2013, Hobbs 1985, Knuth 1970, Bjorner 2014, Moura 2008, Sebastiani 2015, Docef 2023, Cousot 1977) — paper-faithful checks below rely on the standard published content of those works as well as the in-tree docstring claims, and that gap is itself a finding.

## Scope

In propstore: cel_bindings.py, cel_checker.py, cel_registry.py, cel_types.py, cel_validation.py, dimensions.py, unit_dimensions.py, equation_comparison.py, equation_parser.py, sympy_generator.py, value_comparison.py, z3_conditions.py.
In ast-equiv: canonicalizer.py, comparison.py, sympy_bridge.py.
Tests read: tests/test_cel_checker.py, test_cel_types.py, test_cel_validation.py, test_checked_condition_ir.py.
Docs read: docs/cel-typed-expressions.md, docs/units-and-forms.md, docs/qualia-and-proto-roles.md.

## CEL type system: soundness status

There is no soundness theorem to be had in the Pierce TaPL sense, because there is no operational semantics for CEL inside the checker. `cel_checker.py` is a syntactic well-formedness pass that maps each AST node to one of `ExprType.{NUMERIC, STRING, BOOLEAN, UNKNOWN}` and emits errors. The runtime evaluator (celpy or whatever lives downstream — not in cluster-G files) is decoupled. So:

- No "preservation" can be stated: there is no reduction relation in this module. The checker is a relation `Γ ⊢ e : τ` over a type ladder it invented. Whether celpy's evaluation of `e` produces a value of type `τ` is left to the third party.
- No "progress" can be stated either: there are no values, no eval rules.

That is OK if you don't *claim* soundness. The docs (cel-typed-expressions.md) carefully say "registry-aware validation constructs `CheckedCelExpr`" without claiming soundness. Good. But several invariants the rest of the system relies on are not enforced:

1. **`UNKNOWN` is a silent absorbent element.** `_check_comparison_type_mismatch` returns immediately when either side is `UNKNOWN` (cel_checker.py:720-721). After the first error in a sub-expression, downstream type checks are skipped. A single typo can mask multiple real errors.

2. **Ternary is unsoundly typed.** `_resolve_type` for `TernaryNode` (cel_checker.py:586-590) returns the type of the *true* branch and never compares it against the false branch's type. `cond ? "x" : 1` type-checks as STRING, then arithmetic on it later may or may not error depending on AST shape. Pierce TaPL §11.8 ("The Conditional") requires `T-If: t1 : Bool, t2 : T, t3 : T ⊢ if t1 then t2 else t3 : T` — the two-branch type identity is the textbook rule and is missing here.

3. **Unary minus always returns NUMERIC even after recording a type error.** `_resolve_type` for `UnaryOpNode` op `-` (cel_checker.py:572-578) records an error if the operand is STRING/BOOLEAN, then returns `ExprType.NUMERIC`. The "type" of an erroneous expression is treated as if the cast succeeded — a coercive subsumption with no semantic basis. Pierce ch. 22 (subtyping) makes coercive interpretations explicit; this one is not. Same for `!`: returns BOOLEAN unconditionally.

4. **Logical operators previously accepted any operand.** `TestLogicalOperatorTypeValidation` (test_cel_checker.py:651-702) marks the bug "currently PASSES silently" and asserts the corrected behavior. Reading `_check_binary` at cel_checker.py:599-606, the current implementation *does* check: it errors when either operand's type is not in `{BOOLEAN, UNKNOWN}`. So either the test docstring is stale or the fix was applied without updating the comment. The fact that `UNKNOWN` is in the accepted set means a bare `nonexistent_concept && true` will report only the "Undefined concept" error, not the operand-type error — this is consistent with #1 above and is at least defensible.

5. **`in [list]` element type is not checked against the LHS type for non-categories.** `_check_in` only validates category value sets (cel_checker.py:653-682). A `quantity in ['a','b']` errors on each string element (line 681), but a `boolean in ['true', 'false']` is reported as a "boolean cannot be used with 'in'" error (line 676) — fine — yet `numeric in ['a', 'b']` for a non-NameNode LHS (e.g. `(F0+1) in [...]`) silently passes without value-type check.

6. **TIMEPOINT is collapsed into NUMERIC.** `_resolve_type` (cel_checker.py:558) maps both QUANTITY and TIMEPOINT to `ExprType.NUMERIC`. Consequently `valid_from + temperature` type-checks. In the dimensions semantics this is a category mistake: time + temperature is undefined. Pierce TaPL has nothing to say here, but Kennedy 1997 §2 ("Units of Measure") gives a parametric type system over dimension exponents that forbids this. Propstore bypasses it at the CEL layer; only Z3 will model these as separate `Real` symbols (which doesn't constrain incompatible mixing either).

7. **No unit/dimension propagation through arithmetic.** `pressure_kpa < temperature_celsius` is well-typed (both NUMERIC) per the CEL checker. The unit dimensions pipeline (unit_dimensions.py / dimensions.py) checks units of *claim values*, not of CEL expressions. Kennedy's Hindley-Milner-with-units construction is not in the system anywhere.

**Verdict:** the checker is a useful syntactic gate but its name "type checker" is too strong. Soundness in Pierce's sense is not even formulable here; in Kennedy's sense it is denied (no dimensions in the type system). Tests cover the rules that are implemented but do not cover the absent rules (#2, #5, #6, #7). The branch-type bug (#2) deserves a failing test that the suite does not contain.

## Unit/dimension coverage

- Pint registry is module-level in `dimensions.py:25` (`ureg = pint.UnitRegistry()`). One process-wide registry. If two threads/test processes ever register conflicting `extra_units` via `unit_dimensions.register_form_units` (which writes into a separate `_symbol_table` dict, not into pint), pint definitions cannot drift, but the `_symbol_table` cache is mutable and not protected. `clear_symbol_table()` exists but is not invoked anywhere I read; tests that mutate the table risk leaking state.

- Affine units (degC, degF) are routed through the per-form `conversions` table when present: `value * multiplier + offset` (dimensions.py:81). This is wrong for *temperature differences*. A claim of `delta_T = 5 degC` would be normalized as `5*1.0 + 273.15 = 278.15 K` — a mismatch from the actual delta of 5 K. Pint distinguishes `degC` (absolute) from `delta_degC` (relative); the form YAML schema does not. The temperature.yaml entry uses `multiplier: 1.0` for degC (matches Kelvin scale) and `offset: 273.15` (correct for absolute); but for degF the pattern uses `multiplier: 0.5556, offset: 255.372` — that's only correct for absolute, and the multiplier is rounded (true value is 5/9 = 0.5555…). Round-tripping a value through `normalize_to_si` then `from_si` will accumulate ~10⁻⁵ error per round trip because of this rounding.

- Logarithmic conversions are computed in pure Python (dimensions.py:77): `reference * base ** (value / divisor)`. No domain check that `value` is real and finite; passing NaN or -inf will silently produce NaN/0/inf without an error.

- `_PINT_ALIASES` (dimensions.py:29-37) hard-codes a small mapping. `µ` -> `u` is brittle: pint accepts "micro" prefix; mapping the symbol `µ` to the literal letter `u` only works because pint also has a unit named `u` (the atomic mass unit). Translating `µm` would map to `um` which pint reads as either "micrometer" or fails depending on parser mode — no test covers this.

- `forms_with_dimensions` returns `None` if any input lacks dimensions, then `verify_form_algebra_dimensions` returns `False` (dimensions.py:153-177). False is also returned on `KeyError, ValueError, ImportError`, conflating "not dimensionally consistent", "couldn't determine", and "bridgman not installed" — the caller cannot tell which.

- `dims_signature` (dimensions.py:180) strips zero exponents and sorts. Good. But it returns `""` for dimensionless and `None` for missing-dimensions — one `None` check site that uses `==` would silently treat the two as different, which is correct, but downstream string concatenation would `TypeError` if a caller forgets the None check.

- `unit_dimensions._normalize_dim_key` only normalizes Greek theta (Θ/θ -> "Theta"). Other Greek-letter dimension keys (some authors use Φ for luminous flux) silently survive, then `dims_equal` from bridgman compares dicts by exact keys, so equal dimensions written with different glyphs compare unequal.

- Compound units, prefixes: pint handles these natively but the propstore wrappers do not advertise it, and `can_convert_unit_to` swallows `TypeError, ValueError` in addition to pint's own exceptions (dimensions.py:124-128) — a pint internal change in error type would not be noticed.

- Temperature affine: confirmed wrong for deltas. No "delta_" form variant.

## Equation comparison: completeness analysis

The pipeline (equation_comparison.py + equation_parser.py):

1. Parse via Lark grammar (`_GRAMMAR` at equation_parser.py:77) — straightforward arithmetic + power + `log/ln/exp/sqrt`.
2. Build a typed AST (NumberExpr, SymbolExpr, UnaryExpr, BinaryExpr, FunctionExpr).
3. `structural_signature` does positional renaming (equation_parser.py:239-266).
4. `_normalize_parsed_equation` (equation_comparison.py:169-188) builds `sympy.cancel(sympy.expand(lhs - rhs))` and uses `str(diff)` as the canonical form. Equality is `left.canonical == right.canonical` (line 110-112).

Holes:

- **No semantic equivalence beyond rational polynomial.** `expand` then `cancel` is a complete decision procedure for rational polynomial identity over the rationals (Knuth 1970, simple-word-problems, addresses term rewriting; Knuth-Bendix completion for the abelian-group-with-distributivity word problem is needed). For expressions with `sqrt`, `log`, `exp`, this fails. Two equivalent equations like `log(x*y) = log(x) + log(y)` would be reported as `DIFFERENT` by `cancel(expand(log(x*y) - log(x) - log(y)))` (sympy returns the unsimplified form). No `sympy.simplify` or `logcombine` step. The system has no "couldn't decide" status — it returns `EQUIVALENT` or `DIFFERENT` deterministically, mislabeling the second case.

- **`EquationComparisonStatus.INCOMPARABLE` is reserved only for parse failure** (equation_comparison.py:103-107), not for semantic uncertainty. There is no third value for "syntactically distinct but semantically undecided".

- **Number tokens become `Rational` via `Decimal`.** `_sympy_number` (equation_comparison.py:225-228) uses `sympy.Rational(str(Decimal(token)))`. So `0.1` is exactly 1/10, not the float 0.1. `0.1 + 0.2 == 0.3` will report EQUIVALENT, which the user wants for symbolic comparison but contradicts naive numeric intuition. This is correct-as-designed but worth flagging because `value_comparison.py` uses `float(...)` and `1e-9` tolerance — two incompatible numeric models in the same package.

- **`structural_signature` is order-sensitive across all binary operators including `+` and `*`.** `bin:+(sym:v0,sym:v1)` and `bin:+(sym:v1,sym:v0)` get different signatures (equation_parser.py:259-260). For commutative ops this approximates α-equivalence only when terms appear in the same order. Two papers with `F = m * a` and `F = a * m` get different structural_signatures but the same canonical form (sympy normalizes). The pipeline still calls them EQUIVALENT via the canonical compare, so the structural signature is just a hash for grouping — but the `equation_signature` function (line 53) is used as a *coarse grouping key* in conflict_detector and *that* depends on dependent/independent role labels, which depend on author intent.

- **`@lru_cache(maxsize=4096)` on `_normalize_equation_text` keyed on (source_text, bindings).** `EquationSymbolBinding` includes `role`. So the same equation text with different role labellings produces *different* normalized objects, but since `_normalize_parsed_equation` ignores roles entirely, the two cache entries store identical results. Cache pollution, not correctness, but on a long-running process the cache will hold dup entries.

- **Decimal token rendering can lose precision.** `normalized_number_token("0.10")` returns `"0.1"` (equation_parser.py:233-236). `format(Decimal("1e9").normalize(), "f")` returns `"1000000000"`. `1.0e-15` → `"0.000000000000001"`. For very small or very large magnitudes the rendered string explodes; if used as a hash key this is fine, but if displayed it's ugly. Not a correctness bug.

- **No support for inequalities.** `split_equation_relation` (equation_parser.py:203-226) explicitly rejects any of `==, <=, >=, <, >`. Equation claims with bounds (e.g. `F0 > 200`) cannot use the equation pipeline. Conflict detection between an equation and a bound never happens.

- **No α-equivalence for free variables across two equations with different concept_id bindings.** Two papers may use symbols `x, y` for the same two concepts but in opposite roles. The `SymbolExpr.concept_id` is what becomes the sympy `Symbol`; if concept_ids match, ordering doesn't matter (sympy will normalize). If concept_ids differ, the equations are different even when "really" the same.

- **No Knuth-Bendix completion or any AC-rewriting.** Knuth 1970 establishes that for Abelian groups one can compute a confluent rewrite system. The codebase delegates to `sympy.cancel(sympy.expand(...))`, which handles rational expressions but not richer theories. There is no acknowledgement of which equational theory is decided and which isn't.

## Z3 integration concerns

`z3_conditions.py` is the strongest module in the cluster — it has typed result objects (`SolverSat`, `SolverUnsat`, `SolverUnknown`), explicit timeout handling, registry-fingerprint pinning, division-by-zero guards, and temporal interval ordering constraints. But:

- **`SolverUnknown` is correctly distinguished from sat/unsat.** `solver_result_from_z3` reads `solver.reason_unknown()` and classifies it. `_require_decided` (line 109-112) raises `Z3UnknownError` for two-valued callers, so legacy boolean `are_disjoint`/`are_equivalent` paths still surface unknown as an exception rather than silently returning False. Good — this is exactly the soundness discipline Bjorner & Phan 2014 advocate (incompleteness must be observable).

- **Division-by-zero guards collected via `self._current_guards`** (z3_conditions.py:255-260). The pattern is: for every `/`, append `right != 0` to a list; conjunct after translation. Bug risk: `_translate_binary` mutates instance state during translation. The list is reset only inside `_condition_to_z3` (line 410). If `_translate` is ever called outside `_condition_to_z3` (no callers I see, but the method is not private) the guards either leak across translations or are lost. Race condition if the solver is shared across threads — not declared as thread-safe, but also not declared single-threaded.

- **Division semantics in Z3.** Z3 treats `Real` division as a total function with `x/0` an unspecified value. Adding `right != 0` to the conjunction means a condition `x/y > 0` is interpreted as `x/y > 0 ∧ y != 0`. That's correct for "the expression is well-defined and true." But if the *negation* side of an equivalence query is `¬(x/y > 0 ∧ y != 0)` ≡ `x/y ≤ 0 ∨ y == 0`, then the negation includes `y == 0` as a satisfying case, and `are_equivalent` may report SAT (i.e. not equivalent) because of the y=0 ghost case. Looking at `are_equivalent_result` (line 583-605): it asserts `expr_a` and `Not(expr_b)`. `expr_a` includes guards from translation of `a`; `Not(expr_b)` includes the negation of guards from translation of `b`. So `y == 0` in B's denominator becomes a witness. The two condition sets `x/y > 0` (from A) and `x/y > 0` (from B) should be equivalent, but their guard lists are independent: cache hit via `_condition_expr_cache` should make them identical; verify by reading line 405-418 — yes, the cache is keyed on `(fingerprint, source)`, so identical sources reuse the cached expression including guards. Good. But two *different* sources with the same denominator concept (e.g. `x/y > 0` vs `x/y >= 0`) could still produce slightly different guard placement. Worth a property test.

- **Quantifiers: none.** No `ForAll`, `Exists`. CEL conditions are quantifier-free over the registry. This avoids Z3's quantifier-instantiation incompleteness (Moura & Bjørner 2008 §5) entirely. Good.

- **String semantics for extensible categories** uses `z3.String` (z3_conditions.py:157-160). Z3's string theory is decidable for word equations with regular constraints (Bjorner et al. 2017) but interactions with `EnumSort` are limited. The code carefully uses Strings only for extensible categories and Enum only for closed ones — sound. Mixing `String == StringVal` (line 295) and `Const == EnumVal` (line 310) in the same condition set is fine because they touch disjoint sorts.

- **EnumSort is created lazily and tied to the solver context** (line 171). If `_get_enum` is called twice with different `info.category_values` (e.g. registry mutation between calls), the second call reuses the cached sort with stale values. The fingerprint check should catch this at the call boundary, but only if the caller passes a `CheckedCelExpr` — raw `CelExpr` paths re-check via `check_cel_expr` against the *current* registry, which has changed; the cached enum sort still encodes the old values. Defensive fix: invalidate caches on registry change (which the API doesn't allow but doesn't prevent either; `self._registry` is `dict[str, ConceptInfo]`, mutable).

- **Temporal interval ordering** (`_temporal_ordering_constraints`, line 462-497) is added eagerly. Detection is by name suffix `_from`/`_until` with matching prefix. **Bug:** if a registry has `_until` but no matching `_from` (or vice versa), the function silently emits no constraint (line 488-489) — fine. But it materializes the Z3 vars with `_get_real(from_name)` even when only the until is checked, creating spurious free variables that Z3 will instantiate. Then it adds the constraint — wait, line 488 returns `continue` before materialization in the unmatched case. Re-read: line 487 `until_name = until_concepts.get(prefix)`; if None, continue; only matched pairs materialize and add the constraint. OK.

- **Naming convention as semantics is fragile.** A concept named `valid_from` is treated as a temporal interval start by string match. If a user names a quantity concept `pressure_from`, it gets interval treatment if it's TIMEPOINT — only TIMEPOINT triggers (line 479). So the trigger requires both kind=TIMEPOINT and suffix match. Reasonable, but should be documented as a *contract* not a heuristic.

- **`partition_equivalence_classes` is O(n*k)** where k is class count (line 640-675). It calls `are_equivalent`, which raises on unknown. If any pair returns UNKNOWN mid-partition, the whole partition aborts. For robustness this should fall back to "treat as distinct class" with logging.

- **Timeout default 30 s** (line 44). Per-query, not per-batch. A partition over 100 sets with 10 classes does up to 1000 SAT calls × 30 s = 8 hours worst case. No batch-level budget.

- **`is_condition_satisfied` (line 514-523) accepts `bindings: Mapping[str, Any]`.** `_binding_to_z3` does `z3.RealVal(value, ...)` for QUANTITY/TIMEPOINT (line 445). If `value` is a string `"3.14"`, RealVal parses it; if it's `None`, Z3 raises a TypeError uncaught. No explicit type validation against the concept's declared kind.

## ast-equiv coupling (and bugs)

ast-equiv lives in a sibling repo (`../ast-equiv/ast_equiv/`) and is consumed by propstore (per cluster scope). I did not find an actual import of ast-equiv from propstore in the cluster-G files — value_comparison, equation_comparison, sympy_generator do not import it. The coupling, if it exists, is at a layer outside cluster G. Reading it for soundness anyway:

- **Commutative sort excludes Add.** `Canonicalizer.visit_BinOp` (canonicalizer.py:407-413) sorts only `Mult` operands, not `Add`. The comment says "+ is overloaded for lists/strings (not commutative)". That's defensive but also blocks normalization of `a + b` vs `b + a` in equation contexts. For equation_comparison (which does its own sympy expand), this doesn't matter. But anyone using ast-equiv directly for math gets asymmetric treatment.

- **Sympy bridge does not handle subtraction-as-flip.** `_sympy_expr_equal` (sympy_bridge.py:117-132) calls `sympy.simplify(sym_a - sym_b) == 0`. `simplify` is documented as heuristic, not a decision procedure. Returns False for many true equivalences involving piecewise or special functions. `sympy_expressions_equivalent` swallows all exceptions (comparison.py:276-277).

- **`_reduce_stmts` mutates `stmts` in-place via deepcopy at the top** (sympy_bridge.py:156). Safe within the function but iterates `while len(stmts) > target_count` and breaks only when `inlined` stays False. If two assignments are mutually-recursive `x = y; y = x`, both fail the `_references_var` check trivially (each RHS doesn't reference its own LHS), so each is inlinable, and the loop will inline both producing nonsense. Actually `_references_var` checks if RHS references the LHS being inlined; `x = y` has RHS `y`, does not reference `x`, so it's inlinable. Then `y` gets substituted with `y` (no-op), the assignment `x = y` is removed, then `y = x` remains; iteration finds `y = x` inlinable; but `x` no longer exists as an assignment after step 1. Net effect: probably benign but worth a hypothesis test.

- **`_NameCollector` excludes "attr roots that are never assigned and not params" from positional rename** (canonicalizer.py:117-119). Heuristic: assumes an unassigned attribute root is a module like `math`. Breaks for class attributes used the same way (e.g. `cls.foo`). For algorithm comparison where the corpus is mostly free functions this is fine.

- **`PositionalRenamer` produces `_v0, _v1, ...`** (canonicalizer.py:152). Two functions with the same body but different parameter order get different mappings — that's intended (parameter order is semantically meaningful). But there's no canonicalization-by-equivalence-class here; it's a positional rename.

- **`Canonicalizer.visit_BinOp` repeated-mult-to-power transform** (canonicalizer.py:396-405): `x * x * x → x ** 3`. The `_collect_mult_power_chain` walker accepts mixed `x**2 * x` and reconstructs `x ** 3`. Correctness depends on the base nodes having identical `ast.dump`. For floats this is fine; for arbitrary expressions like `(a+b) * (a+b)` it works only if both sides canonicalize to the same dump first — which the visitor traversal order does provide via `generic_visit` first (line 361). OK.

- **`DeadBranchEliminator` returns lists** (canonicalizer.py:467-478). Returning `[]` for a removed-If is unusual `NodeTransformer` behavior; `ast.NodeTransformer.generic_visit` accepts list returns from a visitor and splices them in. Verified: yes, NodeTransformer supports this. Fine.

- **`compare()` swallows all exceptions** in tier 1.5 sympy and tier 2 bytecode (comparison.py:276-277, 286-287). Any exception in those tiers degrades silently to "no equivalence found," masking real bugs. Should at minimum log.

- **Bytecode comparison strips augmented assignment offset** (comparison.py:127-129): `argval - 13`. Magic number, version-dependent: comment says "Python 3.11+" for PUSH_NULL but does not document which Python version's BINARY_OP encoding is assumed for the `_INPLACE_OFFSET = 13`. Brittle across Python releases.

## Pustejovsky / Kennedy / Knuth gap analysis

**Pustejovsky 1991 (Generative Lexicon, qualia structure).** The codebase has `propstore.core.lemon.qualia` (per docs/qualia-and-proto-roles.md) implementing the four qualia roles. None of cluster G's files (cel_bindings, cel_types, cel_checker) reference qualia. The CEL "binding names" (`source`, `domain`, `source_kind`, `origin_type`, `name`, `framework`, `variant`) are provenance/metadata bindings — not qualia. So the Pustejovsky structural distinction (formal/constitutive/telic/agentive) has *not* made it into the CEL type system; it lives in a parallel lexical layer. CEL conditions cannot mention or constrain qualia roles. This is a deliberate architectural separation per docs, not necessarily a bug, but the cluster-G prompt asked specifically: the answer is "no, qualia are not in CEL types."

**Pustejovsky 2013 (Dynamic Event Structure / Habitat).** No reference in cluster-G files. Habitat / dynamic event structure does not appear in CEL or the equation pipeline.

**Hobbs 1985 (Ontological Promiscuity).** Hobbs's argument is that one should reify everything, including events, properties, and abstract entities, and use coreference rather than typed sorts. Propstore's CEL is *not* ontologically promiscuous — it has a fixed `KindType` enum (QUANTITY/CATEGORY/BOOLEAN/STRUCTURAL/TIMEPOINT). Per the global memory note "imports are opinions, no source is privileged," the CEL kind system is the one privileged taxonomy. That is an explicit architectural choice that conflicts with Hobbs's recommendation; the architecture decision is *defensible* (decidability) but the conflict isn't documented.

**Kennedy 1997 (Relational Parametricity, Units of Measure).** Kennedy gives an ML-style unit polymorphism: `'a m^2 -> 'a m^2 -> 'a m^4` etc. Propstore: zero unit polymorphism in the type system. Units exist on *claim values* and forms, never on CEL expressions or equation symbols. `pressure_kpa - temperature_K` type-checks. Major unimplemented theorem — though to be fair, no propstore doc claims to implement Kennedy.

**Knuth 1970 (Simple Word Problems / Knuth-Bendix Completion).** equation_comparison.py uses `sympy.cancel(sympy.expand(...))`. This is *one* normalization for one equational theory (rational polynomial). It is *not* Knuth-Bendix. There is no rewrite system, no completion procedure, no termination analysis. The system makes no completeness claim, but the code is named `canonical_form` — an overstatement.

**Bjorner 2014 / Moura 2008 (Z3, MaxSAT).** z3_conditions.py uses standard Z3 SAT/UNSAT/UNKNOWN tri-valued logic correctly with explicit `SolverUnknown`. No use of MaxSAT optimization. Per Bjorner & Phan 2014, MaxSAT is what you'd want for *partial* satisfaction queries (e.g. "which subset of conditions is jointly satisfiable") — propstore does not do this; it only checks UNSAT/SAT for full conjunctions.

**Sebastiani 2015 (OptiMathSAT / Optimization Modulo Theories).** No optimization queries in cluster G. Z3 is used as a decision procedure only.

**Docef 2023 (Z3 for fragments of linear logic).** No linear-logic encoding visible in z3_conditions.py.

**Cousot 1977 (Abstract Interpretation).** No abstract domain in `cel_checker.py`. The `ExprType` enum is a fixed three-valued type lattice (ignoring UNKNOWN), not a Galois-connected abstraction. Checker is concrete syntactic, not abstract-interpretive.

**Pierce 2002 (TaPL).** Discussed above: no operational semantics, so no soundness theorem; ternary type rule absent; coercive subsumption hidden in unary minus.

**In-tree paper notes.** None of the listed `papers/<paper>/notes.md` files exist (verified for Pierce, Kennedy, Knuth — only `paper.pdf` and `metadata.json`). The cluster-G prompt asks me to compare against `notes.md`. There is nothing to compare against. **This is itself a gap:** if the project is supposed to be paper-faithful and the notes layer is the bridge, the notes are missing for the most foundational works in this cluster.

## Bugs (HIGH/MED/LOW)

### HIGH

H1. **CEL ternary type rule unsound** — `_resolve_type` for TernaryNode returns true-branch type without checking equality with false-branch type (cel_checker.py:586-590). `cond ? "a" : 1` type-checks. No test in test_cel_checker.py covers this — `TestComplexExpressions::test_ternary_valid` only checks the homogeneous case `phonation_present ? F0 > 200 : true` (boolean/boolean) — wait, that's boolean true vs boolean F0>200, also homogeneous. No mixed-branch test exists.

H2. **Affine unit conversion wrong for temperature differences** (dimensions.py:81). Treating delta-degC as absolute degC adds 273.15 K. Pint distinguishes `delta_degC`; propstore doesn't. Any claim of a temperature *change* in degC will be silently wrong by ~273 K after SI normalization.

H3. **Equation comparison reports DIFFERENT for true equivalences involving log/exp/sqrt.** `cancel(expand(diff))` is not a complete decision procedure for these theories. `log(x*y)` vs `log(x)+log(y)` returns DIFFERENT. No INCOMPARABLE/UNKNOWN third state.

H4. **Z3 division-by-zero guards depend on per-instance mutable state** (`self._current_guards`, z3_conditions.py:140, reset at line 410). Not thread-safe and not protected against re-entrant translation. If a future code path calls `_translate` directly on a sub-AST (e.g. for symbolic execution or evaluation), guards are silently dropped or merged across calls.

### MED

M1. **`UNKNOWN` ExprType silently absorbs follow-on errors** (cel_checker.py:720-721). Single typo masks all downstream type errors in the same expression. No test verifies error count for cascading errors.

M2. **Unary minus / not return their nominal type even after operand type error** (cel_checker.py:572-578, 567-571). `-(true)` reports an error and types as NUMERIC; `! 5` reports an error and types as BOOLEAN. Coercive subsumption with no semantic basis.

M3. **EnumSort cached against mutable registry.** `Z3ConditionSolver._registry` is a `dict[str, ConceptInfo]` not frozen (z3_conditions.py:124). Mutating `category_values` after first translation leaves stale enum sorts cached. No defensive copy at construction.

M4. **Pint registry is module-level singleton** (dimensions.py:25). `register_form_units` writes into a separate cached `_symbol_table` dict (unit_dimensions.py) but does not update pint. Domain units declared in form YAMLs are visible to bridgman but invisible to pint, so `can_convert_unit_to("custom_unit", "m")` returns False even for dimensionally compatible custom units.

M5. **CEL float literals do not support exponent notation** (cel_checker.py:183). `1e9` tokenizes as INT_LIT 1 followed by NAME `e9`, then parses as `1 * e9` if `e9` is a registered concept, else "Undefined concept e9". The equation parser supports `[eE][+-]?\d+`. Inconsistent.

M6. **CEL string escape handling only recognizes `\"`, `\'`, `\\`** (cel_checker.py:209). `\n`, `\t`, `\u`, `\x` survive unprocessed. Inconsistent with CEL spec and with celpy semantics.

M7. **`_normalize_checked_conditions` deduplicates by source string only** (cel_types.py:91-105). `a < b` and `b > a` are treated as distinct conditions. No semantic dedup. The fingerprint contract guarantees registry consistency but not condition-set logical normalization.

M8. **`equation_signature` uses role labels as part of the grouping key** (equation_comparison.py:53-73). Two papers asserting the same equation but disagreeing on dependent/independent labelling produce different signatures, so they never reach the equivalence check. Conflict detection misses these cases.

M9. **`_normalize_equation_text` lru_cache pollution.** Cache key includes `EquationSymbolBinding.role`, but the normalization ignores roles. Duplicate cache entries for the same actual equation. Memory leak, not correctness.

M10. **`canonicalize_equation` returns a single canonical form per source text without recording sympy version.** Different sympy versions canonicalize differently. Cross-version comparison may report DIFFERENT for equivalent expressions if a normalization rule changed between releases.

M11. **`partition_equivalence_classes` aborts on UNKNOWN** (z3_conditions.py:640-675). One UNKNOWN result aborts the entire partition with `Z3UnknownError`. For batch reasoning, should fall back to "isolate as singleton class" with logging.

M12. **`Z3ConditionSolver` has no timeout-budget per batch.** Per-query timeout only (line 144). A pathological corpus could spend hours in `partition_equivalence_classes`.

M13. **`is_condition_satisfied` does not validate binding values against concept kind.** `_binding_to_z3` will pass arbitrary `Any` to `z3.RealVal` / `z3.BoolVal` / `z3.StringVal`. No type guard.

### LOW

L1. **`_PINT_ALIASES` rounding for degF** (dimensions.py:31): `0.5556` instead of `5/9`. Round-trip error 10⁻⁵ per cycle.

L2. **`unit_dimensions._normalize_dim_key` only handles theta** (unit_dimensions.py:24). Other Greek glyphs left as-is; equality compare across glyph variants fails.

L3. **`dims_signature` returns `""` for dimensionless and `None` for missing** (dimensions.py:180-187). Two distinct sentinels with similar meaning. Caller bug risk.

L4. **`forms_with_dimensions` returns False for three different conditions** (dimensions.py:153-177): not consistent, can't decide, not installed. Caller cannot distinguish.

L5. **`CheckedCelExpr._create` is a class method, not module-private.** Anyone with the import can construct a `CheckedCelExpr` bypassing the checker. Sentinel token (cel_types.py:16) only blocks naive `CheckedCelExpr(...)` construction. Module-level privacy is the actual gate, but the convention is informal.

L6. **`cel_validation.iter_*` skips empty / non-string conditions silently** (cel_validation.py:106). A `None` in the conditions list slips through ingest without record. Schema bug upstream would not be caught here.

L7. **Bytecode `_INPLACE_OFFSET = 13` is Python-version-dependent magic** (comparison.py:30). No version guard.

L8. **`compare()` swallows all exceptions in tiers 1.5 and 2** (comparison.py:276-277, 286-287). Real bugs degrade silently.

L9. **`sympy_expressions_equivalent` returns False if sympy not installed** (sympy_bridge.py:308-309). No way for a caller to distinguish "not equivalent" from "tool unavailable."

L10. **CEL parser error messages contain raw `expr[pos:]!r`** (cel_checker.py:219). Authored CEL with secrets in string literals could leak via error messages — small risk.

L11. **No paper notes.md files exist** for the foundational works in scope (Pierce, Kennedy, Knuth, Pustejovsky, Hobbs, Bjorner/Moura, Sebastiani, Docef, Cousot). Verified via Bash listings: only `paper.pdf` and `metadata.json` are present. The "paper-faithful" workflow lacks its bridge layer.

L12. **`generate_sympy_with_error` rewrites `^` to `**` then takes RHS of `=`** (sympy_generator.py:62-69). If an expression has `=` inside a function call (it can't in valid math, but could via authored typo), the split silently discards LHS. Defensive but quiet.

L13. **`value_comparison.intervals_compatible` uses `1e-9` absolute tolerance** (value_comparison.py:11). For SI-normalized pressures (Pa = ~10⁵), this tolerance is meaningless; for SI-normalized atomic distances (m = ~10⁻¹⁰), it's larger than the values. Should be relative/scaled.

L14. **`value_comparison.values_compatible` falls through to `value_a == value_b`** for non-numeric (line 110). Comparing two list values uses Python list equality — order-sensitive. Two equal multisets disagree.

## Open questions for Q

Q1. **Is CEL "type checker" intended to be sound, or only a syntactic gate?** If sound, the ternary bug (H1) and the unary-cast bug (M2) need fixing. If only a gate, the docs should rename the module and stop using "type-check" verbiage. Pierce-style soundness requires either an operational semantics in propstore or a formal mapping to celpy's semantics — which doesn't exist.

Q2. **Should units of measure be in the CEL type system (Kennedy 1997) or remain a parallel claim-value validation?** Current architecture: parallel. Consequence: `pressure_kpa < temperature_K` type-checks. Acceptable?

Q3. **Should equation_comparison have an INCOMPARABLE-due-to-undecidability return value?** Currently INCOMPARABLE means parse failure only. For `log(x*y) = log(x)+log(y)`, the system reports DIFFERENT (a false negative on equivalence). Adding a third "couldn't decide" state would surface these to callers.

Q4. **Are paper notes.md files supposed to exist for cluster-G papers?** None do. The foundational papers (Pierce, Kennedy, Knuth) have only PDFs. The reviewer protocol asks for paper-faithful checks; without notes.md the comparison is against my reading of the published works, which the project cannot version-control.

Q5. **Should Z3ConditionSolver hold an immutable (frozen) registry?** Currently mutable; cached enum sorts can go stale (M3). A `Mapping[str, ConceptInfo]` snapshot at construction would close this hole.

Q6. **Should `partition_equivalence_classes` degrade on UNKNOWN to singleton classes (with logging) instead of aborting?** Current behavior is fail-fast. For batch conflict detection this means one undecided pair kills the whole partition.

Q7. **Should temperature affine forms split into `degC` vs `delta_degC`?** If propstore claims to support temperature differences (which it must, e.g. for ΔT measurements), the schema needs the distinction. Pint has it; propstore's form schema does not.

Q8. **Is the lack of qualia integration into CEL bindings intentional?** The CEL `_STANDARD_SYNTHETIC_BINDING_NAMES` are provenance fields, not Pustejovsky qualia. The qualia layer in `propstore.core.lemon.qualia` exists in parallel but cannot be referenced from CEL conditions. Was this the intended architecture, or a not-yet-done integration?

Q9. **Does ast-equiv have any actual caller in propstore?** I could not find an import of `ast_equiv` from any cluster-G file. The cluster prompt lists it as "propstore depends on this." Where is the dependency edge?

Q10. **Why are equation_comparison and value_comparison using different numeric semantics?** equation_comparison uses exact rationals via Decimal+Rational; value_comparison uses floats with 1e-9 tolerance. A claim's value and an equation's coefficient for "the same number" can compare unequal between the two pipelines.
