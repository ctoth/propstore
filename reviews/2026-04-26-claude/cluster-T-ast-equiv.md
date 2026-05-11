# Cluster T: ast-equiv dependency

Reviewer: analyst subagent (Claude). Read every source file in scope, all four test files, the flipped-pairs notes, README, pyproject, and the relevant report. Greppped propstore for consumers.

## Scope and purpose

`ast-equiv` is a four-tier algorithm-equivalence library used by propstore to decide when two Python algorithm implementations are "the same." Public surface (`ast_equiv/__init__.py:2-21`):

- `parse_algorithm`, `extract_names`, `normalize_to_concepts`, `canonicalize`, `canonical_dump`, `structural_match`, `KNOWN_BUILTINS`, `AlgorithmParseError`
- `compare`, `ComparisonResult`, `Tier`, `normalized_bytecode`, `bytecode_match`, `partial_eval_bytecode`, `partial_eval_match`, `structural_similarity`

Tier ladder in `compare()` (`comparison.py:243-307`): canonical AST match → SymPy algebraic equivalence → bytecode match → partial-eval bytecode match (only if `known_values` provided). Each tier is reached only if the previous tier said "not equivalent."

Propstore consumers (full list from grep):
- `propstore/world/value_resolver.py:12-13,517,555` — `compare`, `AstToSympyError`
- `propstore/conflict_detector/algorithms.py:9,46` — `compare` for cross-claim conflict detection
- `propstore/families/claims/passes/checks.py:10,788,819-820` — `parse_algorithm`, `extract_names`, `KNOWN_BUILTINS` for "are all referenced names declared?"
- `propstore/sidecar/passes.py:9-10,473` — `canonical_dump` for cache key
- `propstore/sidecar/claim_utils.py:12,540` — `canonical_dump` for cache key
- `propstore/app/claims.py:176,193` — `compare` (lazy import)
- `scripts/verify_ast_equiv.py:2`, `tests/test_conflict_detector.py:878,1295`

Notably both `value_resolver.py:524` and `value_resolver.py:566` catch `AstToSympyError`, but `AstToSympyError` is **not** raised from `compare()` directly — `comparison.py:276` swallows it inside the SymPy tier. Catching it externally is dead code, suggesting confusion about where the exception escapes. (See HIGH-3.)

## Canonicalizer correctness

The canonicalizer is `ast.NodeTransformer`-based and applies, in order (`canonicalize()` at `canonicalizer.py:831-847`): `Canonicalizer` (docstring strip + dead-code-after-return + AugAssign normalization + commutative sort + identity elimination + repeated-mult-to-power + range normalization + bool-comparison normalization + chained comparison collapse) → `ConstantComparisonFolder` → `DeadBranchEliminator` → `TempVariableInliner`. Plus `WhileToForNormalizer` outside `canonicalize()` in `canonical_dump()` (`canonicalizer.py:858`).

What is correct:

- `_is_constant_value` (`canonicalizer.py:486-488`) explicitly guards `bool` vs `int` via `type(node.value) == type(value)`. Prevents `True * 1 -> True` being collapsed via `1 * x -> x` mismatch.
- Range normalization (`canonicalizer.py:309-322`) requires `start is 0` (identity check via `_is_constant`) and `step is 1`. `0.0 == 0` would fail `is`, so `range(0.0, n)` (illegal anyway) is not folded. Correct.
- Constant folding catches `ZeroDivisionError, OverflowError, ValueError` (`canonicalizer.py:369`). Conservative — leaves the BinOp alone if folding fails.
- Boolean rewrite (`visit_Compare`, `canonicalizer.py:324-336`) only fires when LHS is bool-typed via static annotation tracking (`_function_bool_names`). Test at `test_canonicalizer.py:102-114` proves both branches.
- Mult-to-power chain detection (`_collect_mult_power_chain`, `canonicalizer.py:203-230`) handles already-collapsed cases like `x**2 * x -> x**3`.

What is wrong or fragile:

**HIGH C-1: Identity elimination is unsound for non-numeric types.** `visit_BinOp` (`canonicalizer.py:374-392`) rewrites `x + 0 -> x`, `0 + x -> x`, `x * 1 -> x`, etc. with no type check. If `x` is a string, list, tuple, or any type that doesn't support `+ 0`, the original code raises `TypeError` at runtime; the canonicalized version does not. Algorithm-equivalence wise, two implementations that both crash are "equivalent." But a crashing function and a working function would be reported equivalent. Worse, the comment at `canonicalizer.py:408` explicitly notes Add commutative sort is excluded "because + is overloaded for lists/strings (not commutative)" — yet identity elimination on Add does **not** have the same guard. Inconsistent.

**HIGH C-2: Repeated-mult-to-power is semantics-changing for side-effecting expressions.** `_collect_mult_power_chain` (`canonicalizer.py:203-230`) compares operands by `ast.dump` only. If the operand is `f()`, then `f() * f() -> f() ** 2`, which calls `f` once instead of twice. For pure expressions this is fine; for any call with side effects it changes execution count. Since the bridge later sees these inside Return values that often contain `math.exp(...)` calls, the risk is theoretical for math.* (pure) but real for arbitrary user calls.

**HIGH C-3: `WhileToForNormalizer` is unsound w.r.t. `break`/`continue`/mid-body increments.** `_try_convert` (`canonicalizer.py:530-593`) only inspects the **last** body statement for `var = var + 1` / `var += 1`. It does not check:
   - Whether `var` is reassigned anywhere else in the body (`while i < n: i += 5; ...; i += 1` would be wrongly converted, dropping the `+= 5`).
   - Whether the body contains `break` (semantics change: `for` consumes the iterator differently — actually equivalent here for `range`, OK) or `continue` that would skip the increment in `while` semantics. In `while x < n: ...; if cond: continue; i += 1`, a `continue` skips the increment and the loop hangs; `for i in range(n)` does not. The canonicalized form silently changes a non-terminating program into a terminating one.
   - Whether body modifies `n` (the bound). `range(n)` snapshots `n`; `while i < n` re-reads.
   - Whether `init_val` is integer. `_transform_stmts` accepts `int` or `float` (`canonicalizer.py:515`), but `range` requires int. `init_val=2.5` builds `range(2.5, n)` → runtime `TypeError`. Bug.

**MED C-4: `TempVariableInliner` `_is_safe_inline_expr` allows `math.*` calls and arithmetic on Names** (`canonicalizer.py:778-828`). Moving `math.sqrt(-1)` (raises `ValueError`) past intervening statements changes when the exception fires. The whitelist trades soundness for corpus coverage. The docstring at `canonicalizer.py:825-827` acknowledges this. Plus: `_find_inline_candidates` walks `ast.Module(body=stmts)` synthetic wrapper to count loads/stores (`canonicalizer.py:740`), which descends into nested function defs. A nested function that uses `var` will inflate the load count and falsely block inlining; symmetrically, a name shadowed by a nested function can be miscounted. Edge case, probably not hit in practice.

**MED C-5: Constant folding silently changes types.** `1 / 2 -> 0.5` (float replaces int/int division). Two algorithms `a = 1/2` and `a = 0.5` are now indistinguishable; that's intended. But `1 // 2` is folded to `0` (int) via `floordiv`, while `1.0 // 2 -> 0.0` (float). Type-sensitive downstream comparisons (e.g., `isinstance(result, int)`) would be wrong post-canonicalization. The test suite never exercises this.

**MED C-6: Mult commutative sort is pairwise, not flat.** `visit_BinOp` (`canonicalizer.py:409-413`) only swaps `node.left` and `node.right` of a single BinOp. It does not flatten a `*` chain and re-sort. So `(a*c)*b` and `a*(b*c)` may not canonicalize to the same form. Knuth-Bendix-style associative-commutative completion would flatten first. The flipped-pairs notes claim 24 pairs were recovered with the existing transforms; this likely understates the false-negative rate on more complex AC expressions. Add is excluded from sort entirely (per the line 408 comment), so `a + b` and `b + a` only match if SymPy tier rescues them. Tested case at `test_canonicalizer.py:95-100` (`2 * 3 * n` vs `6 * n`) works only because constant folding collapses `2*3` first.

**LOW C-7: Constant folding has no `TypeError` guard.** `canonicalizer.py:369` excludes `TypeError`. `ast.Constant("a") + ast.Constant(1)` would crash the canonicalizer with an uncaught `TypeError`. Reachable only with a literal `"a" + 1` in source, which is also a runtime error — so input is already malformed. Still defensive coding lapse.

**LOW C-8: Dead-code-after-return** (`canonicalizer.py:276-281`) only acts at the function-body level. `if cond: return; print("unreachable")` does not strip the print, but `return; print("x")` in a top-level body would. The comment says "remove statements after Return" — works as advertised, but doesn't handle nested unreachable code. Acceptable.

**LOW C-9: AugAssign normalization** (`canonicalizer.py:293-305`) constructs the synthetic `BinOp` then calls `self.visit_BinOp(binop)`, but does not call `generic_visit` on the new node first. The repeated-mult-to-power and identity rules will fire (good); the children are already-visited so this is fine. But `target_copy` is constructed unconditionally (`isinstance(node.target, ast.Name)` else `node.target`) — if target is a `Subscript` or `Attribute`, the original target object is reused on both LHS and RHS. Mutating either mutates both, since this is the same Python object. Subtle aliasing risk in subsequent transforms.

## Comparison soundness/completeness

`compare()` (`comparison.py:243-307`):

**HIGH X-1: All exceptions in tier evaluation are silently swallowed.** Lines 276-277, 286-287, 296-297 use bare `except Exception: pass`. This catches `MemoryError`, malformed-input bugs, internal logic errors, etc., and proceeds as if the tier returned False. A canonicalizer crash on novel input becomes a "no equivalence found" verdict instead of a visible failure. Propstore catches narrow exceptions externally (`value_resolver.py:524`, `algorithms.py:47`) — those would have been more informative if `compare` re-raised.

**HIGH X-2: `_compile_to_bytecode` picks the wrong code object for nested functions.** `comparison.py:113-118` iterates `code.co_consts` and picks the **first** thing with `co_code`. For source containing multiple functions or a lambda, the first-found const may be the lambda. Bytecode tier becomes nondeterministic w.r.t. source layout. Propstore feeds single-function bodies (per `parse_algorithm`'s requirement at `canonicalizer.py:37-42`), so the field impact is limited — but `parse_algorithm` only checks for one function at module level; a nested helper inside the function body would trigger the bug.

**MED X-3: Bytecode tier comparison is brittle to Python version.** `comparison.py:30, 127-128` hardcodes the `_INPLACE_OFFSET = 13` for normalizing augmented BINARY_OP. Python 3.13 (`pyproject.toml` requires 3.11+) reworked binary ops; the offset may shift. `SKIP_OPS` (`comparison.py:23-26`) lists 3.11-era opcodes only. Future Python upgrades will silently break the bytecode tier, returning false negatives.

**MED X-4: `Tier` enum exposes inconsistent labels.** `comparison.py:33-72` defines NONE, CANONICAL, SYMPY, BYTECODE, PARTIAL_EVAL with ranks 0-4. The `Tier` value `BYTECODE` has rank 3, but comments at `comparison.py:250-253` call SymPy "Tier 1.5" and bytecode "Tier 2", and the README (`README.md:7-10`) lists tiers as canonical/bytecode/partial-eval/structural-similarity — which doesn't even mention SymPy. Three different tier numberings depending on where you look. The flipped-pairs notes confirm the bytecode tier "resolves 0 pairs that Tier 1 doesn't — dead weight." Yet it remains in production. README is also out of date — says "four-tier" but there are five Tier values.

**MED X-5: Comparison is not transitive.** With each tier's ad-hoc admission rules (especially SymPy with `simplify`), `compare(a,b).equivalent and compare(b,c).equivalent` does not imply `compare(a,c).equivalent`. Property test `test_properties.py:30-35` only tests symmetry-of-self, not real symmetry between distinct inputs. There is **no transitivity test, no false-positive corpus test for sympy_bridge involving branch cuts, and no test of compare on inputs with side-effecting calls.**

**MED X-6: Property tests are toy.** `tests/test_properties.py` generates only `def f(x): return x OP CONST` for OP ∈ {+,-,*}, CONST ∈ [0,100]. This does not exercise the canonicalizer's interesting paths. Hypothesis is in the dev dependencies but barely used.

**LOW X-7: `_extract_function` (`comparison.py:100-105` and `sympy_bridge.py:287-292`) returns the first FunctionDef found via `ast.walk`.** For a module containing `def outer(): def inner(): ...`, this picks `outer` as expected. Behavior matches `parse_algorithm` enforcement of one top-level function — but the duplicated `_extract_function` definitions across two modules is dead code/duplication.

## sympy_bridge round-trip

`ast_to_sympy` (`sympy_bridge.py:28-114`) covers: int/float Constants, Names→Symbols, USub/UAdd, Add/Sub/Mult/Div/Pow, `math.pi`, `math.exp/cos/sin/log/sqrt/log10`, `abs(x)`, Tuples. Anything else raises `AstToSympyError`. Conservative (incomplete → false negatives only, sound for what it covers).

**HIGH S-1: `math.log(x, base)` two-argument form is rejected.** `sympy_bridge.py:84-87` requires `len(node.args) == 1`. So `math.log(x, 2)` raises `AstToSympyError`. `math.log10` is handled but `math.log2` is not. Coverage hole, paper-faithfulness aside.

**HIGH S-2: Floor division `//` is not handled.** `sympy_bridge.py:58-71` covers Add/Sub/Mult/Div/Pow but not FloorDiv, Mod, BitAnd, BitOr, BitXor, LShift, RShift. The canonicalizer permits these in source via `_SAFE_OPS`. So `x // 2` and `x // 2` get exact-AST match in `_expr_equiv` (line 196), but `x // 2` vs `(x - x % 2) // 2` (mathematically equivalent for ints) cannot be detected. Propstore DSP code uses `//` for sample indices (mentioned in the SymPy report `reports/sympy-vs-egglog-report.md:118-119`). Outstanding gap acknowledged in the report but not fixed in code.

**HIGH S-3: `sympy.simplify(a - b) == 0` can be unsound for branch-cut expressions.** `sympy_bridge.py:132`. With assumptions that Symbols are unrestricted complex (default for `sympy.Symbol`), `simplify` may treat `sqrt(x*y)` and `sqrt(x)*sqrt(y)` as equal even though they differ for `x, y < 0`. Same for `log(x*y)` vs `log(x) + log(y)`. For real-valued physics/DSP code this is "morally correct" but for general algorithm equivalence it is unsound. There is no `positive=True` annotation on the symbols anywhere. **Untested.**

**MED S-4: `sympy.simplify` is non-canonical and non-deterministic across versions.** `simplify` is famously heuristic. Different SymPy versions produce different `simplify` results. Pinning is `sympy>=1.14.0` (`pyproject.toml:13`) — open upper bound. Future SymPy upgrades may flip pair verdicts.

**MED S-5: `_reduce_stmts` (`sympy_bridge.py:147-183`) inlines blindly.** When statement counts differ, it inlines simple non-self-referencing assignments. It does not check `_is_safe_inline_expr` like the canonicalizer does. So a `t = produce()` followed by `g(); use(t)` would inline `produce()` past `g()`, reordering side effects. The canonicalizer's `TempVariableInliner` has the corresponding test at `test_canonicalizer.py:116-125` — but `_reduce_stmts` reproduces the inlining logic without the safety. **Bug parity violation.**

**MED S-6: Statement equivalence does not use SymPy on `If.test`, `While.test`, `For.iter`, `For.target`.** `sympy_bridge.py:255-276` requires `ast.dump` exact match for predicates. So `if x > 0:` vs `if 0 < x:` would fail despite being equivalent. Inconsistent with the design (SymPy on assignment RHS, not on tests).

**LOW S-7: Booleans rejected** at `sympy_bridge.py:39-40` — fine for the math domain. But `True` and `False` constants flowing through canonicalizer post-bool-rewrite hit this and silently fall through.

**LOW S-8: `sympy.Float(v)` from a `float` Constant** (`sympy_bridge.py:44`). SymPy Float carries precision; `Float(0.1)` and `Float(0.1)` compare equal but `Float(0.1) == Rational(1, 10)` is false. `0.1 + 0.2` (= 0.30000000000000004 in IEEE) folded to `0.30000000000000004` then converted to `Float` will not equal a literal `Float(0.3)`. Correct (no false positive), but a source of mysterious false negatives in user-facing comparisons.

## "Flipped pairs" history — verified or still risky?

`notes-fix-flipped-pairs.md` declares the work done: "ast-equiv: 172/172 pass. propstore: 544/544 pass." Of 46 flipped pairs:
- 24 recovered by 6 transforms + SymPy tier + 1 reclassification
- 3 accepted as out of scope (loop-to-comprehension, loop index offset, multi-use inlining)
- 19 remain as intended-False

The transforms added (per the commits table in the notes): dead-branch elimination, chained-compare collapse, positional alpha-rename, repeated-mult-to-power, while-to-for, temp-inlining, SymPy tier. Each is observably present in `canonicalizer.py` and `comparison.py`.

What the notes do **not** address:

1. The transforms restored corpus passes but added the soundness risks documented above (HIGH C-2, C-3, S-3, S-5). The flipped-pairs work was driven by corpus pass-rate, not by Knuth-Bendix-style proof of confluence. There is no test that the canonicalizer is **idempotent** (`canonicalize(canonicalize(t)) == canonicalize(t)`); `test_properties.py:38-45` tests only that the dump is deterministic for the **same** input.
2. The notes claim "Tier 2 (bytecode) resolves 0 pairs that Tier 1 doesn't — dead weight." Yet the bytecode tier is still in `compare()` and is the slowest path that requires `compile()`. Not removed. Performance/maintenance liability.
3. "9 commits, 24 recovered" — the trade-off was rapidly adding transforms to push pass-rate up. No commit added a **negative test** for a wrongful equivalence. The corpus is the only soundness check. If you don't have a representative adversarial corpus, you've optimized for the cases you happen to have.
4. WhileToFor (`7b44e2a`) recovered "7 pairs" but, as analyzed in C-3, is unsound on `break`/`continue` and mid-body mutations of the loop variable. Highly likely to produce false positives on real-world DSP loops with conditional breaks.

Verdict on the fix history: **the corpus passes, the underlying canonicalizer has new soundness gaps, and there is no adversarial corpus to catch them.**

## Boundary with propstore

Propstore consumes ast-equiv with these patterns:

1. **`compare()` for cross-claim conflict detection** (`conflict_detector/algorithms.py:46`, `value_resolver.py:517,555`, `app/claims.py:193`). A false-positive equivalence here means two genuinely different algorithms are reported as the same; conflicts get silently merged. Given HIGH C-1, C-2, C-3, S-3 above, real false positives are possible — particularly on algorithms with `break` in `while` loops or branch-cut math.

2. **`canonical_dump` as a cache key** (`sidecar/passes.py:473`, `sidecar/claim_utils.py:540`). Cache keys must be **stable** and **collision-free.** Stability fails if SymPy version changes (`Float` repr) or Python version changes the `ast.dump` format. Collision risk follows from any false-positive canonicalization.

3. **`extract_names` for unbound-name validation** (`families/claims/passes/checks.py:819-820`). Fine — pure read-only walk.

4. **Exception hygiene mismatch:** `value_resolver.py:524,566` catches `(ValueError, SyntaxError, AlgorithmParseError, AstToSympyError)`. `compare()` swallows `AstToSympyError` internally (`comparison.py:276`), so catching it externally is dead. `compare()` does NOT raise `ValueError` or `SyntaxError` after the initial parse (which raises `AlgorithmParseError`). The external `except` clause is mostly defensive theater. Meanwhile, `RecursionError` from deeply nested AST is caught only at `conflict_detector/algorithms.py:47`, not in `value_resolver.py` or `app/claims.py:193`. **Inconsistent error handling across consumers.**

5. **No version pin on ast-equiv.** Per the git status note (`build: pin argumentation package to github`) the project recently pinned argumentation. ast-equiv's `pyproject.toml` ships as `version = "0.1.0"` and propstore presumably pulls it via path or an unpinned dep. Subagent did not check propstore's pyproject — flagging as an open question.

## Bugs (HIGH/MED/LOW)

HIGH:
- **C-1** Identity elimination unsound for non-numeric types (no type guard on `x + 0 -> x`). `canonicalizer.py:374-388`.
- **C-2** Repeated-mult-to-power changes call-count for side-effecting operands. `canonicalizer.py:203-230, 396-405`.
- **C-3** WhileToForNormalizer ignores `break`/`continue`/mid-body mutation of loop var; accepts non-int init values. `canonicalizer.py:530-593`.
- **X-1** `compare()` swallows all exceptions in three tiers, hiding real bugs as "not equivalent." `comparison.py:276,286,296`.
- **X-2** `_compile_to_bytecode` picks first const with `co_code`, picks wrong function in nested-def cases. `comparison.py:113-118`.
- **S-1** `math.log(x, base)` 2-arg form rejected. `sympy_bridge.py:84-87`.
- **S-2** No FloorDiv/Mod/bitwise support in SymPy bridge despite canonicalizer accepting them. `sympy_bridge.py:58-71`.
- **S-3** `sympy.simplify(a-b) == 0` is unsound for branch-cut expressions; Symbols default to complex. `sympy_bridge.py:132`.

MED:
- **C-4** TempVariableInliner whitelists `math.*` calls, can move exception-raising calls past statements. `canonicalizer.py:778-828`. Load/store counter walks into nested defs.
- **C-5** Constant folding silently changes int↔float types.
- **C-6** Mult commutative sort is pairwise not flat; AC normalization incomplete. `canonicalizer.py:409-413`.
- **X-3** Bytecode tier brittle to Python version (`_INPLACE_OFFSET=13`, fixed `SKIP_OPS`). `comparison.py:23-30`.
- **X-4** Three different tier numberings (enum, code comment, README). README still says "four-tier ladder" with no SymPy mention.
- **X-5** No transitivity test; property tests don't exercise comparison across distinct inputs.
- **X-6** Hypothesis property tests are toy — only `def f(x): return x OP CONST` for arithmetic-only ops.
- **S-5** `_reduce_stmts` inlines without `_is_safe_inline_expr` check; reorders side effects. `sympy_bridge.py:147-183`.
- **S-6** SymPy bridge requires exact `ast.dump` match on predicates / for-loop iterators; inconsistent with using SymPy on RHS.
- **S-4** `sympy.simplify` non-canonical across versions; open upper bound on dep. Verdicts can flip on `pip upgrade`.

LOW:
- **C-7** Constant folding has no `TypeError` guard.
- **C-8** Dead-code-after-return only at function-body level.
- **C-9** AugAssign normalization aliases the target node when it's a Subscript/Attribute.
- **X-7** Duplicated `_extract_function` in `comparison.py` and `sympy_bridge.py`.
- **S-7** Boolean Constants explicitly rejected — silently falls through if they reach the bridge.
- **S-8** `sympy.Float` precision matters; `0.1+0.2` folded then bridged will not equal `0.3`.

## Open questions for Q

1. **Is the corpus the only soundness oracle, or is there a hidden adversarial test set?** If only the 134-pair corpus, then C-3 (while-to-for unsoundness) is a real production risk on any DSP loop with `break`. Suggest building an adversarial corpus that pairs (truly-different-but-canonicalizes-the-same) algorithms.
2. **Should the bytecode tier be removed?** The flipped-pairs notes explicitly say it adds zero recoveries. Keeping it adds Python-version brittleness (X-3) and masks bugs (X-1).
3. **Was branch-cut soundness considered for SymPy?** Should symbols be declared `positive=True` for DSP/physics where that's true, vs. fully general for arbitrary algorithms? Different downstream domains may need different bridges.
4. **Should propstore pin ast-equiv to a hash?** The `Float`-precision bridge plus `simplify` heuristics make verdicts version-fragile; cache keys built from `canonical_dump` will silently invalidate or — worse — collide.
5. **Is `extract_names`'s inclusion of `KNOWN_BUILTINS` intentional?** `test_canonicalizer.py:41-44` tests that `len` is in `extract_names` output, but `KNOWN_BUILTINS` is then subtracted by every consumer (`checks.py:820`). The set inclusion in the API forces every caller to repeat the subtraction. Smell — should `extract_names` exclude builtins by default?
6. **Should `WhileToFor` be guarded by absence of `break`/`continue`?** Trivial AST scan; would convert HIGH-C-3 from a soundness bug to a missed-recovery (acceptable).
7. **Where does the README's "Tier 4 — Structural similarity" claim come from?** The actual `compare()` does not return `Tier.STRUCTURAL_SIMILARITY` (it doesn't exist). README is wrong. Should it be deleted or re-added as an actual tier?
