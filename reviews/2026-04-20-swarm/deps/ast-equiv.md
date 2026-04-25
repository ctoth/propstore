# ast-equiv review (2026-04-20)

Reviewer: gauntlet analyst subagent. Scope: `C:\Users\Q\code\ast-equiv\ast_equiv\` source, `tests/` contract surface (read, not re-run), `README.md`, `notes-fix-flipped-pairs.md`, and propstore consumer sites found by `grep "from ast_equiv"` in `C:\Users\Q\code\propstore\propstore\`.

## Purpose & Public Surface

`ast-equiv` is a tiered equivalence comparator for Python function bodies packaged as algorithm claims. Public API (`ast_equiv/__init__.py`, plus the consumer-visible `sympy_bridge.AstToSympyError`):

- `parse_algorithm(body: str) -> ast.Module` (`canonicalizer.py:28`). Strict: requires a module with at least one top-level `FunctionDef`/`AsyncFunctionDef`. Raises `AlgorithmParseError` on empty body, syntax error, or missing function.
- `extract_names(tree) -> set[str]` (`canonicalizer.py:47`). Walks every `Name.id` and `arg.arg`, scope-blind.
- `normalize_to_concepts(body, bindings) -> str` (`canonicalizer.py:175`) — in-place rename via `ConceptNormalizer`, then unparse.
- `canonicalize(tree) -> ast.Module` (`canonicalizer.py:732`) and `canonical_dump(body, bindings) -> str` (`canonicalizer.py:751`).
- `structural_match(dump_a, dump_b) -> bool` (`canonicalizer.py:767`) — string equality over `ast.dump`.
- `KNOWN_BUILTINS` (`canonicalizer.py:12`).
- `AlgorithmParseError` (`canonicalizer.py:7`).
- `ComparisonResult(equivalent, tier, similarity, details)` (`comparison.py:32`).
- `compare(body_a, bindings_a, body_b, bindings_b, known_values=None)` (`comparison.py:198`).
- Lower-tier helpers: `normalized_bytecode`, `bytecode_match`, `partial_eval_bytecode`, `partial_eval_match`, `structural_similarity`.
- `ast_equiv.sympy_bridge.AstToSympyError` (`sympy_bridge.py:23`) — imported directly by `propstore/world/value_resolver.py:13`.

Pipeline (canonical path) — `comparison.py:41-53` and `canonicalizer.py:751-764`:
1. Parse → `ConceptNormalizer` (rename locals to concept ids, rename function name to `"algorithm"`).
2. `PositionalRenamer.rename` (rename remaining names to `_v0`, `_v1`, …).
3. `WhileToForNormalizer` (init+while+increment → for range).
4. `TempVariableInliner` (inline single-store/single-load locals).
5. `Canonicalizer` (strip docstring, drop statements after Return in top-level body, lower AugAssign, fold constants, eliminate identities, collapse repeated Mult → Pow, sort Mult operands by `ast.dump`, collapse chained compares, rewrite `x == True`/`x == False`, etc.).
6. `ConstantComparisonFolder` + `DeadBranchEliminator`.
7. Re-run `TempVariableInliner` once.

Ladder (`compare()`, `comparison.py:198-262`):
1. Canonical dump equality → `tier=1`.
2. SymPy algebraic equivalence of canonicalized trees (`sympy_bridge.sympy_expressions_equivalent`) → `tier=2`.
3. Bytecode match on canonicalized+recompiled source → `tier=2` (SAME tier as SymPy — numbering collision).
4. Partial-eval bytecode match (only when caller supplies `known_values`) → `tier=3`.
5. A fourth structural-similarity tier is documented but explicitly disabled (`comparison.py:255-257`); README still advertises four tiers.

Notes file (`notes-fix-flipped-pairs.md`) confirms the ladder is really "AST canonicalization → SymPy → partial eval" and that "Tier 2 (bytecode) resolves 0 pairs that Tier 1 doesn't" — bytecode is known dead weight but still shipped.

## Equivalence Semantics Audit

There is no written spec. README lists tiers in one sentence; no docstring defines what `equivalent=True` means or what soundness/completeness the caller may rely on. Consumers (`conflict_detector/algorithms.py`, `world/value_resolver.py`, `app/claims.py`) treat a `True` verdict as ground truth. What the implementation actually provides:

- **Alpha equivalence**: yes, for parameter and local names, via `PositionalRenamer` — `def f(x): return x+1` and `def g(y): return y+1` canonicalize identically (see `test_canonicalizer.py:103-117`).
- **Concept-relative equivalence**: parameters bound to the same concept id compare equal; parameters bound to different concept ids compare unequal even if the bodies are isomorphic.
- **Commutativity**: inconsistent. `Mult` operands get sorted by `ast.dump` (`canonicalizer.py:372-376`), but `Add` is explicitly skipped with the rationale that `+` is overloaded for lists/strings. Consequence: `a + b` and `b + a` are NOT tier-1 equivalent even for obviously numeric bodies. SymPy tier can recover this only when every node in both expressions lies in the tiny supported fragment (`sympy_bridge.ast_to_sympy`: Constant int/float, Name, USub/UAdd, Add/Sub/Mult/Div/Pow, `math.pi`, `abs`, `math.{exp,cos,sin,log,sqrt,log10}`, tuples). Anything else — `BoolOp`, `Compare`, `Subscript`, list/dict literals, any other attribute access — silently fails SymPy and bypasses the tier.
- **Associativity**: NOT normalized. `(a*b)*c` vs `a*(b*c)` canonicalizes differently unless SymPy reaches it.
- **Identity elimination**: `x+0`, `0+x`, `x*1`, `1*x`, `x-0`, `x**1` (`canonicalizer.py:337-355`). Absent: `x*0`, `x-x`, `x/x`, `x+(-y) → x-y`.
- **Boolean rewrite is unsound** (`canonicalizer.py:291-298`): `x == True` becomes `x`, `x == False` becomes `not x`. For non-bool `x` this changes the expression's value. `(1 == True) + (2 == True)` would evaluate to `2` but canonicalize to `1 + 2` = `3`. This is a semantic rewrite masquerading as canonicalization.
- **AugAssign lowering** (`canonicalizer.py:257-269`): `x += y` → `x = x + y`. Does not deepcopy `node.value`; the new BinOp and the soon-discarded original AugAssign share the RHS subtree. Currently safe because the original is dropped on return, but fragile.
- **Dead-code-after-Return** (`canonicalizer.py:243-249`) is applied only at the outer function body. Returns nested inside `if:` blocks do NOT get their trailing statements pruned. Canonicalization is asymmetric between flat and nested returns.
- **Dead branch elimination** (`DeadBranchEliminator`) runs post-order and is sound for constant-test `If` nodes.
- **Temp-variable inlining is unsound under side effects.** `TempVariableInliner` (`canonicalizer.py:619-729`) inlines any single-store/single-load local whose RHS does not self-reference. Effects are ignored: `t = f(); g(); use(t)` is rewritten to `g(); use(f())`, reordering `f()` and `g()`. If `f` or `g` has side effects (file writes, dict mutation, print), the canonical form no longer matches the original semantics, but ast-equiv will declare the two equivalent.
- **Commutative Mult sort reorders impure calls** (`canonicalizer.py:372-376`). `a() * b()` → `b() * a()`, violating Python's left-to-right evaluation guarantee.
- **Chained-compare collapse reduces call count** (`canonicalizer.py:307-320`). `a < f(x) and f(x) < b` → `a < f(x) < b`, halving `f` calls. Because the guard is `ast.dump(mid1) == ast.dump(mid2)`, any pure structural match triggers it regardless of purity.
- **Symmetry is not guaranteed.** `_reduce_stmts` (`sympy_bridge.py:147-183`) reduces only the LONGER side. The choice of which side to reduce depends on argument order, and the inlining substitutes into all subsequent statements. `_stmts_equivalent(a, b)` can differ from `_stmts_equivalent(b, a)`. `compare()` is therefore not guaranteed symmetric. The existing property test `test_symmetry` (`test_properties.py:28-35`) compares `body` to itself twice — it does NOT test `compare(a,b)` vs `compare(b,a)`.
- **Dual-pipeline divergence.** `canonical_dump` (`canonicalizer.py:758`) passes `concept_names=frozenset(bindings.values())` into `PositionalRenamer.rename` to preserve concept ids. `_normalize_and_canonicalize` in `comparison.py:47` passes nothing, so concept names CAN be renamed by positional renaming. The same `body`+`bindings` pair therefore produces two different canonicalized trees depending on which path reached it. `compare()` uses tier-1 from one pipeline and tier-2/3 from the other — a pair that matches one may fail the other silently.
- **Bytecode tier** (`comparison.py:89-99`) serializes `ast.unparse` then `compile`. `ast.unparse` loses some structure (e.g., `ast.Name("_v0")` vs the original), but the two sides go through the same unparse so it's deterministic. Confirmed dead-weight by `notes-fix-flipped-pairs.md`.

## Consumer Drift (propstore → ast_equiv)

Consumer sites (from `grep` in `propstore/propstore/`):

- `propstore/app/claims.py:247,264-270` — `ast_compare(body_a, bindings_a, body_b, bindings_b, known_values=…)`. No exception handling. `canonical_dump` is called twice inside `compare()`; an `AlgorithmParseError` from a malformed body will propagate out and fail the `compare_algorithm_claims` request with no typed reporting.
- `propstore/conflict_detector/algorithms.py:9,45-54` — catches only `(ValueError, SyntaxError)`. `AlgorithmParseError` inherits from `Exception`, not `ValueError`, so parse failures crash the detector. `RecursionError` likewise. Drift: the `AlgorithmParseError` type is in the public API but this caller does not import or handle it.
- Same file, line 55: gates on `result.equivalent and result.tier <= 2`. Because tiers 2-SymPy and 2-bytecode share a number, this gate conflates the two. It also excludes partial-eval (tier 3) — ambiguous whether that is intended. If the intent was "canonical or bytecode only," the SymPy tier (newly added per the notes) now silently slips through the gate with tier=2, widening what counts as a conflict vs. before the SymPy change.
- `propstore/families/claims/passes/checks.py:10,787-820` — uses `parse_algorithm`, `extract_names`, `AlgorithmParseError`, `KNOWN_BUILTINS`. `extract_names` is scope-blind: names defined only inside a nested function or comprehension body are treated as outer references, which can produce false positives in the unbound-name validator when a claim has nested defs.
- `propstore/sidecar/claim_utils.py:12,464` — calls `canonical_dump(body, bindings)` with no try/except. A malformed body propagates `AlgorithmParseError` up and aborts sidecar row construction.
- `propstore/sidecar/passes.py:9,436-438` — correctly wraps `canonical_dump` in `except AlgorithmParseError: canonical_operation = operation`. OK.
- `propstore/world/value_resolver.py:12-13,517-568` — imports `AlgorithmParseError` top-level and `AstToSympyError` from `ast_equiv.sympy_bridge`. Catches `(ValueError, SyntaxError, AlgorithmParseError, AstToSympyError)`. But `AstToSympyError` is never raised OUT of `compare()`: the SymPy bridge catches it inside `_sympy_expr_equal` (`sympy_bridge.py:122-123`) and `compare()` wraps the SymPy call in `except Exception: pass` (`comparison.py:231`). The `AstToSympyError` in the consumer's except tuple is dead code — it will never fire. `RecursionError` is still uncaught.

Exception handling across consumers is inconsistent: two sites catch `AlgorithmParseError`, two don't. No site catches `RecursionError`. No site inspects `details` or distinguishes tiers beyond one `<=` gate.

## Known-Bug Followups (from notes)

`notes-fix-flipped-pairs.md` is dated recent and marked COMPLETE: 172/172 ast-equiv, 544/544 propstore. Residual issues acknowledged by the notes:
- Three pair categories declared "beyond scope": loop-to-comprehension, loop index offset, multi-use inlining. For these cases `compare()` will return `equivalent=False` for genuinely equivalent algorithms — which means `propstore/conflict_detector/algorithms.py:55` records FALSE CONFLICTS between semantically identical claims.
- Bytecode tier is admitted "dead weight" but retained. Any consumer using `result.tier == 2` (or `<=2`) as a business signal is relying on a tier that never independently fires.
- SymPy algebraic tier was added in commit `9033d04` with its own tier name ("Tier 1.5" in comments) but shares the `tier=2` integer with bytecode. Upstream policy gates cannot distinguish them.
- Notes do NOT address: the `x == True` rewrite, the symmetry violation in `_reduce_stmts`, the side-effect-unsafe Mult sort / chained-compare collapse / temp inlining, recursion depth, or the `PositionalRenamer.rename` concept-name argument divergence between pipelines.

## Silent Failures

- `comparison.py:225-232` — `except Exception: pass` around SymPy tier. Any failure (including `RecursionError` or hung `sympy.simplify`) is treated as "tier miss."
- `comparison.py:234-242` — `except Exception: pass` around bytecode tier.
- `comparison.py:244-253` — `except Exception: pass` around partial-eval tier.
- `canonicalizer.py:329-333` — silent swallow of `ZeroDivisionError, OverflowError, ValueError` in constant folding. Acceptable, but produces asymmetric canonicalization if one side of `compare()` folds and the other raises.
- `sympy_bridge.py:122-123` — `AstToSympyError` inside `_sympy_expr_equal` returns `False`, so "unsupported expression" and "genuinely inequivalent" are indistinguishable to the caller.
- `sympy.simplify(a - b) == 0` (`sympy_bridge.py:132`) has no timeout. Pathological expressions can hang until the outer `except Exception` never triggers.
- `ComparisonResult.details` carries a short string but tells the caller nothing about *why* lower tiers failed — no structured failure reporting.

## Bugs

- **HIGH** — `ast_equiv/comparison.py:227, 238`. Tier number `2` is returned by both the SymPy branch and the bytecode branch. Consumers that branch on `result.tier` cannot distinguish them, and the tier number no longer maps 1:1 to a semantic guarantee. **Fix**: give SymPy its own tier integer (e.g., `2` for SymPy, `3` for bytecode, renumber partial-eval to `4`), update tests and propstore's `result.tier <= 2` gate in `conflict_detector/algorithms.py:55`.
- **HIGH** — `ast_equiv/canonicalizer.py:291-298`. `x == True` is rewritten to `x`, `x == False` to `not x`. Unsound when `x` is a non-boolean whose integer value differs from its truthiness (`1 == True` is `True` but `2 == True` is `False`). **Fix**: delete the rewrite, or guard it to `isinstance(node.left, ast.BoolOp)` / known-bool contexts (rare in algorithm claim bodies). Add a regression test: `def f(x): return x == True` vs `def f(x): return x` must NOT canonicalize equal.
- **HIGH** — `ast_equiv/sympy_bridge.py:147-183`. `_reduce_stmts` is one-sided; `_stmts_equivalent(a, b) != _stmts_equivalent(b, a)` when one side has inlinable assignments and the other has reduced form. **Fix**: attempt reduction in both directions; return True if either succeeds. Add a property test comparing `compare(a, b).equivalent` to `compare(b, a).equivalent`.
- **HIGH** — `ast_equiv/canonicalizer.py:619-729` (`TempVariableInliner`). Reorders side-effectful statements: `t = f(); g(); use(t)` becomes `g(); use(f())`. Same bug applies to `_VarSubstituter` paths used inside canonicalize. **Fix**: gate on RHS being effect-free (no `Call`, `Await`, `Yield`, `Subscript` store, `Attribute` store, `Raise`) AND no effect-bearing statement between write and read site. Or restrict inlining to RHS that is `Name`/`Constant`/pure arithmetic thereof.
- **HIGH** — `ast_equiv/canonicalizer.py:372-376`. Unconditional Mult sort reorders operands regardless of purity. `a() * b()` → `b() * a()` violates Python evaluation order. **Fix**: sort only when both operands are leaf expressions (Name / Constant) or contain no `Call`/`Await`/`Yield`.
- **MEDIUM** — `ast_equiv/canonicalizer.py:307-320`. Chained-compare collapse halves call count when the middle operand is a `Call` that happens to appear on both sides. **Fix**: gate on `mid1` being a pure expression tree.
- **MEDIUM** — `ast_equiv/canonicalizer.py:693-721`. `_find_inline_candidates` uses `ast.walk(ast.Module(body=stmts))`, which descends into nested `FunctionDef`/`Lambda`/comprehensions. A name assigned once in the outer scope and loaded once in the outer scope can have inflated load/store counts due to inner scope references of the same name. This causes otherwise-inlinable vars to be skipped, or inner-scope-only vars to be mistakenly inlined against outer state. **Fix**: walk only the supplied statement list without descending into nested scopes; use a dedicated visitor that short-circuits on scope boundaries.
- **MEDIUM** — `ast_equiv/canonicalizer.py:236-252`. Dead-code-after-Return is applied only to the outer function body. `if cond: return x; stray` keeps `stray`. **Fix**: apply in every statement list (recurse into If bodies, For bodies, While bodies, With bodies, Try bodies).
- **MEDIUM** — `ast_equiv/canonicalizer.py:12-25`. `KNOWN_BUILTINS` contains `"True"`, `"False"`, `"None"` (dead — these are `ast.Constant` values in 3.8+, never `ast.Name`) and exception class names. The consumer at `families/claims/passes/checks.py:820` subtracts this set from `ast_names` before flagging unbound names, so any exception class name used in a body (e.g., `raise MyDomainError(...)`) that should have been declared in `variables` is silently accepted if its class name collides with a stdlib exception. **Fix**: split into `KNOWN_BUILTIN_FUNCTIONS`, `KNOWN_BUILTIN_EXCEPTIONS`, let the consumer decide which to allow.
- **MEDIUM** — `propstore/conflict_detector/algorithms.py:47`. Only `(ValueError, SyntaxError)` caught; `AlgorithmParseError` and `RecursionError` escape. Deep ASTs or malformed bodies crash conflict detection mid-loop, aborting all remaining pair comparisons. **Fix**: add `AlgorithmParseError` and `RecursionError` to the except tuple.
- **MEDIUM** — `propstore/sidecar/claim_utils.py:464`. `canonical_dump` called without try/except. Malformed bodies will abort sidecar compilation. **Fix**: wrap like `propstore/sidecar/passes.py:436-438` does.
- **MEDIUM** — `propstore/conflict_detector/algorithms.py:55`. Gate `result.tier <= 2` now silently admits SymPy matches (tier=2, added after this gate was written). Depending on intent, the detector either wanted SymPy included (fine, but should be explicit) or wanted only canonical+bytecode (broken). **Fix**: decide intent, use named tier constants exported from `ast_equiv`.
- **LOW** — `ast_equiv/canonicalizer.py:444-446` (`_is_constant`). Uses `is` identity rather than equality; works for `0`/`1`/small ints/`True`/`False`/`None` only by CPython interning accident. **Fix**: replace with `_is_constant_value` (already defined at line 449).
- **LOW** — `ast_equiv/canonicalizer.py:257-269` (`visit_AugAssign`). Shares `node.value` by reference with the freshly built BinOp. A later NodeTransformer that mutates the BinOp's RHS also mutates the original. Currently harmless (original node is discarded via return) but fragile. **Fix**: `copy.deepcopy(node.value)`.
- **LOW** — `ast_equiv/comparison.py:47` vs `ast_equiv/canonicalizer.py:758`. `_normalize_and_canonicalize` calls `PositionalRenamer.rename(tree)` with no `concept_names`, while `canonical_dump` passes `frozenset(bindings.values())`. Same inputs → different renamed trees across the two pipelines used by `compare()`. Possible symptom: a pair matches tier 1 but fails tier 2, or vice versa, because the bytecode/SymPy path saw concept names rewritten as `_v*`. **Fix**: pass `concept_names` consistently in `_normalize_and_canonicalize` and delete the one-off parameter drift.
- **LOW** — `ast_equiv/comparison.py:64-86` (`_compile_to_bytecode`). `for const in code.co_consts: if hasattr(const, 'co_code'): func_code = const; break` takes the first code object constant, which may not be the target `algorithm` function if the body contains nested defs or lambdas. **Fix**: specifically look for the code object whose `co_name == "algorithm"`.
- **LOW** — `ast_equiv/comparison.py:198-262` (`compare`). `details` string is free-form, no tier-miss reasons recorded. Consumers that want to distinguish "genuinely inequivalent" from "unsupported by this tool" can't. **Fix**: structure `details` as a list of `(tier, outcome, reason)` records, or add a `tier_misses` field on `ComparisonResult`.
- **LOW** — No recursion-depth guard anywhere. Deeply nested ASTs (generated code, long BinOp chains) hit `RecursionError` in `_collect_mult_power_chain._walk`, any NodeTransformer, or `ast.walk`. Only partially contained by `except Exception: pass` inside `compare()`. Consumers see either a "`equivalent=False`" tier-0 verdict (if the outer `try` covers it) or a raw crash (if it happens inside `canonical_dump` which is not wrapped). **Fix**: `sys.setrecursionlimit` bump with a ceiling, or convert `_walk` to an iterative traversal.

## Dead Code

- `ast_equiv/comparison.py:255-257` — Tier 4 docstring and comment describe a structural-similarity tier that is explicitly disabled in code; README still advertises four tiers. Remove from docs or reinstate.
- `ast_equiv/canonicalizer.py:200` — `_COMMUTATIVE_OPS = (ast.Add, ast.Mult)` defined but never referenced.
- `ast_equiv/canonicalizer.py:591-617` — `_VarCounter` class defined but never instantiated. Superseded by the inline counting in `TempVariableInliner._find_inline_candidates`.
- `ast_equiv/canonicalizer.py:12-25` — `KNOWN_BUILTINS` entries `"True"`, `"False"`, `"None"` are unreachable (see HIGH/MEDIUM bugs above) — they describe `ast.Constant` values, not `ast.Name`.
- `ast_equiv/__init__.py:5` — `normalize_to_concepts` exported but not referenced by any propstore consumer. Keep only if public API contract requires it.
- `propstore/world/value_resolver.py:524,566` — `AstToSympyError` listed in except tuples but never raised out of `compare()` (swallowed internally). Dead branch of the except.

## Positive Observations

- Public surface is small and well-typed (`ast.Module`, `str`, `dict[str, str]`, a dataclass result, a named exception).
- `AlgorithmParseError` is a public, named exception — correct pattern rather than leaking raw `SyntaxError`.
- Pipeline is linear and readable: parse → concept-rename → positional-rename → while→for → temp-inline → canonicalize.
- `ConstantComparisonFolder` and `DeadBranchEliminator` are small and sound.
- Property tests cover self-equivalence, determinism, and similarity bounds (`tests/test_properties.py`).
- `_compile_to_bytecode` normalizes Python 3.11+ instructions (`RESUME`, `PUSH_NULL`, `CACHE`) and the augmented-assign BINARY_OP offset — shows awareness of CPython version drift.
- The notes file (`notes-fix-flipped-pairs.md`) honestly records that bytecode tier adds no value — transparent engineering log rather than marketing.
- Consumer `propstore/sidecar/passes.py:436-438` demonstrates the correct error-handling pattern for `canonical_dump` that other consumers should copy.
- `ConceptNormalizer` renames the function itself to `"algorithm"`, giving concept-relative alpha equivalence without depending on author-chosen function names.

## Summary

Three issues stand out as real correctness risks for propstore:

1. `x == True` rewrite in `canonicalizer.py:291-298` is unsound and will collapse genuinely-distinct algorithm claims to equivalent.
2. `_reduce_stmts` asymmetry in `sympy_bridge.py:147-183` means `compare(a, b).equivalent` is not guaranteed to equal `compare(b, a).equivalent`. Conflict detection iterates `i < j` pairs only, so the asymmetry picks a winner implicitly.
3. `TempVariableInliner` + Mult sort + chained-compare collapse silently reorder side-effectful statements/expressions. If an algorithm claim ever contains an impure call, canonicalization is not a semantic identity.

Secondary: tier-number collision (`2` = SymPy = bytecode) invalidates the `result.tier <= 2` policy gate in `conflict_detector/algorithms.py:55`, and the dual pipeline drift in `PositionalRenamer` concept-name handling is a latent source of inconsistency between tier-1 and tier-2 verdicts on the same pair.

None of the above are currently covered by tests in `tests/`.
