# WS-O-ast: ast-equiv fixes — canonical AST + sympy bridge

**Status**: OPEN
**Repo**: `../ast-equiv` (sibling repo, MIT-licensed dependency)
**Depends on**: nothing internal
**Blocks**: WS-P (CEL / equation consumer relies on `compare()` and on `canonical_dump` as a cache key for canonicalized claim algorithms)
**Owner**: Codex implementation owner + human reviewer required (per Codex 2.1)
**Decisions applied**: D-14 (delete bytecode tier — locked-in, see `reviews/2026-04-26-claude/DECISIONS.md`).

---

## Resolved decisions

Per Codex 2.29: every implementation step below references decisions resolved in this section. Steps no longer carry the decision themselves. None of these are open. Each is locked here so downstream steps can quote them as fact.

### RD-1 — Real-domain symbol assumptions (was Open Question 1)

**Decision**: SymPy bridge constructs symbols with `real=True, finite=True` by default. Real-domain is the propstore-DSP / physics norm; complex callers opt in via an explicit `assume_complex=True` config flag on the bridge entry point.

Aligns with cluster G's domain-assumption requirement and overlaps WS-P 1.11. Every test that exercises a symbolic equivalence requiring a domain assumption (logs, sqrts, division definedness) names the assumption in the test name AND asserts it in the test body. Example: `test_S3_branch_cut_unsoundness.py` asserts `symbol.is_real is True` before relying on `simplify`.

Branch-cut expressions (`sqrt`, `log`, fractional powers) inherit the real default. `simplify(sqrt(x*y) - sqrt(x)*sqrt(y))` returns nonzero for unrestricted symbols; with `real=True, positive=True` it returns zero soundly. The bridge applies `positive=True` only when the source AST has a guarding domain assertion (e.g. `assert x > 0` in scope) — Step 7 implements the lookup.

This resolves Codex 2.29's first contradiction: the policy is locked, no longer scheduled.

### RD-2 — `extract_names` API shape (was Open Question 2)

**Decision**: rename and split. Two functions, honest names:

1. `extract_all_names(tree)` — what the current `extract_names` returns. All `ast.Name.id` and `ast.arg.arg` occurrences anywhere in the tree, including builtin shadows, function params, comprehension targets, local assignments. No semantic filtering. This is the broad API surface that some callers want (e.g. lexical-occurrence audits).

2. `extract_free_variables(tree)` — proper scope analysis. Walks the tree maintaining a binder stack: function params bind, `Lambda` params bind, comprehension targets bind, `with ... as x` binds, walrus `:=` binds, local assignments at the same scope bind. Builtins are NOT free (the `KNOWN_BUILTINS` set lives in ast-equiv as the authoritative builtin filter; propstore stops re-subtracting). Returns the set of names referenced in `Load` context that are not bound by any enclosing binder.

The current `extract_names` symbol is **deleted** (per `feedback_no_fallbacks.md` — no compat alias). Every caller updates in the same dep-bump commit. Propstore's unbound-name validation at `propstore/families/claims/passes/checks.py:788, :819-820` switches from `extract_names` minus `KNOWN_BUILTINS` to `extract_free_variables` directly. The duplicated re-subtraction smell disappears at the source.

This resolves Codex 2.29's second contradiction: the API is locked, no longer scheduled.

### RD-3 — `canonical_dump` cache key must be SymPy-version-independent (was "pin sympy <1.15")

**Decision**: the cache-key fragility is a real bug. The previously-proposed `sympy>=1.14.0,<1.15` cap is **rejected**. A defensive cap does not fix the bug; it freezes around it and defers the same fragility to whenever 1.15 ships. Per `feedback_no_fallbacks.md` and Q's "iterating to perfection" rule, the fix is to make the cache key SymPy-version-independent, not to pin SymPy. SymPy reserves the right to change `srepr` / `_print_*` output across minor versions; the bug is that `canonical_dump` ever consulted that output for a *cache key*.

**Components**:

1. **`ast`-only cache key.** `canonical_dump`-as-cache-key recomputes from a normalized `ast.AST` form constructed in `canonicalizer.py`, hashed via stdlib `hashlib`. No SymPy on the hashing path. SymPy is still allowed on the *equivalence-comparison* path (Tier.SYMPY); it is forbidden on the *cache-key* path.
2. **Semantic-equivalence version tag.** Cache key is `(SEMANTIC_EQUIVALENCE_VERSION, ast_canonical_hash)` where `SEMANTIC_EQUIVALENCE_VERSION: str = "1"` is a module-level constant we own. SymPy upgrades freely; the cache stays valid. When *we* change equivalence semantics (a new canonicalizer rule, a new tier, a fix to C-1/C-2/C-3) we bump the constant in the same commit, deterministically invalidating dependent caches.
3. **No upper bound on SymPy in `pyproject.toml`.** Keep `sympy>=1.14.0` as the lower bound; drop the `<1.15` cap entirely. No SemVer cap, no patch cap.
4. **Propstore-side pin of ast-equiv** still uses a git hash per `feedback_tags_immutable.md` — unchanged.

**Rationale**: of the three options on the table — (1) hash original source text, (2) hash an ast-only normalized form, (3) `(ast_canonical_hash, semantic-equivalence-version)` — option 3 wins. Option 1 is brittle to whitespace/comments. Option 2 is SymPy-stable but gives us no explicit invalidation knob when our own semantics change. Option 3 separates the two axes cleanly: SymPy is irrelevant to the key; our semantic version is the only deliberate invalidation.

**Migration discipline**: single commit. No dual-emission, no "old key as fallback," no shim. Caches built under the old SymPy-srepr-based key are invalidated; consumers regenerate. Per `feedback_no_fallbacks.md`.

This resolves Q's rejection of the previous RD-3 and Codex 2.29's third contradiction: the cache-key design is locked, the pin is rejected.

### RD-4 — `compare()` error-handling contract (was Codex 2.30)

**Decision**: `compare()` catches narrow per-tier exception classes internally and returns a typed `ComparisonResult` with `equivalent=None` (or a new `tier_failures` field) representing UNKNOWN. External callers do not catch tier-level exceptions because tier-level exceptions do not escape `compare()`.

Concretely:
- CANONICAL tier (`comparison.py:276`) catches `AlgorithmParseError` only.
- SYMPY tier (`comparison.py:296`) catches `AstToSympyError` only.
- Anything else (`MemoryError`, `RecursionError`, internal `RuntimeError`, etc.) propagates to the caller. Bare `except Exception` is gone.
- `ComparisonResult` gains a `tier_failures: dict[Tier, type[Exception]]` field so callers can see "SymPy tier was attempted and refused" vs "SymPy tier said no". Additive, no breaking signature change to the result type.

Consequence: external `AstToSympyError` catches in propstore are dead code. Step 12 deletes them — it is no longer the keep-or-delete-uncertainty step. Specifically:

- `propstore/world/value_resolver.py:524` — `except AstToSympyError` clause: deleted.
- `propstore/world/value_resolver.py:566` — `except AstToSympyError` clause: deleted.
- The import of `AstToSympyError` in `value_resolver.py` is removed.
- A test asserts (a) the symbol `AstToSympyError` is no longer imported in `value_resolver.py` (AST grep) and (b) `from ast_equiv import AstToSympyError; from propstore.world import value_resolver; assert "AstToSympyError" not in dir(value_resolver)` holds.

This resolves Codex 2.30: the contract is locked, no longer self-contradictory.

---

## Why this is foundation-grade for propstore

`ast-equiv` is an algorithm-equivalence library. After D-14 it exposes exactly four enum values: `NONE`, `CANONICAL`, `SYMPY`, and `PARTIAL_EVAL`. `CANONICAL`, `SYMPY`, and `PARTIAL_EVAL` are proof-strength equivalence tiers; `NONE` is the undecided fallback. Propstore consumes it in three load-bearing roles:

1. **Cross-claim conflict detection.** `propstore/world/value_resolver.py:517,555`, `propstore/conflict_detector/algorithms.py:46`, and `propstore/app/claims.py:193` call `compare()` to decide whether two algorithm-typed claims represent the same algorithm. A false-positive verdict here silently merges two contradictions into one — exactly the disagreement-collapse failure mode this project's design principle (`memory/project_design_principle.md`) forbids at the semantic core.
2. **Canonical-dump as cache key.** `propstore/sidecar/passes.py:473` and `propstore/sidecar/claim_utils.py:540` use `canonical_dump(...)` as a stable identifier. Cache keys must be deterministic across SymPy minor versions, Python versions, and re-canonicalization. Today they are not — `canonical_dump` is currently derived from SymPy printer output. Per RD-3 the fix is on the cache-key side: derive from an ast-only canonical hash plus a semantic-equivalence version tag we own. SymPy version drift becomes irrelevant.
3. **Free-variable extraction for unbound-symbol validation.** `propstore/families/claims/passes/checks.py:788, :819-820` uses `parse_algorithm`, the (current) broad `extract_names`, and `KNOWN_BUILTINS`. RD-2 collapses this into `extract_free_variables`.

Cluster T's analyst review found eight HIGH findings, six MED, and a handful of LOW. The corpus that drove the "flipped pairs" recovery campaign closed the recall gap (24 of 46 pairs recovered) without ever building an adversarial false-positive corpus. Pass-rate is at 172/172 in ast-equiv and 544/544 in propstore — an oracle that proves only that the existing tests don't trip the existing transforms. Soundness is unmeasured. This workstream closes that gap.

## Review findings covered

This workstream closes ALL of the following. "Done means done" — every finding is gone from `gaps.md` and has a green test gating it.

### HIGH — soundness bugs

| ID | Citation | Description |
|---|---|---|
| **C-1** | `../ast-equiv/ast_equiv/canonicalizer.py:374-388`; comment at `:408` | Identity elimination (`x+0`, `0+x`, `x*1`, `1*x`, `x-0`) has no type guard. The canonicalizer's own author excluded `Add` from commutative sort with the comment "+ is overloaded for lists/strings (not commutative)" — the same overloading invalidates `x+0->x` for non-numeric `x`. |
| **C-2** | `../ast-equiv/ast_equiv/canonicalizer.py:203-230, 396-405` | Repeated-mult-to-power (`f() * f() -> f() ** 2`) compares operands by `ast.dump` only, with no purity check. For any side-effecting call this changes execution count from N to 1. |
| **C-3** | `../ast-equiv/ast_equiv/canonicalizer.py:530-593` | `WhileToForNormalizer` inspects only the **last** body statement for `var += 1`. Misses `break`/`continue`, body reassignments of `var`, body reassignments of bound `n`, non-int `init_val`. |
| **X-1** | `../ast-equiv/ast_equiv/comparison.py:276, 286, 296` | `compare()` uses bare `except Exception: pass`. After D-14 two blocks remain — CANONICAL and SYMPY. Resolved per RD-4. |
| **S-1** | `../ast-equiv/ast_equiv/sympy_bridge.py:84-87` | `math.log(x, base)` two-argument form is rejected. `math.log10` is handled, `math.log2` is not. |
| **S-2** | `../ast-equiv/ast_equiv/sympy_bridge.py:58-71` | Bridge handles `Add/Sub/Mult/Div/Pow` but not `FloorDiv`, `Mod`, or any bitwise op. |
| **S-3** | `../ast-equiv/ast_equiv/sympy_bridge.py:132` | `sympy.simplify(a - b) == 0` is unsound for branch-cut expressions when symbols default to complex. Resolved per RD-1: real-domain default. |

### MED — corroborated quality findings

| ID | Citation | Description |
|---|---|---|
| **X-4** | `../ast-equiv/ast_equiv/comparison.py:33-72`, `:250-253`; `../ast-equiv/README.md:7-10` | Three different tier numberings depending on where you look. README references `Tier.STRUCTURAL_SIMILARITY` (does not exist) and `Bytecode` (deleted by Step 5). After D-14 the surviving enum is exactly `{NONE, CANONICAL, SYMPY, PARTIAL_EVAL}`. |
| **X-6** | `../ast-equiv/tests/test_properties.py:30-45` | Property tests are toy. Per `feedback_hypothesis_property_tests.md`: prefer formal-property generators over example tests. |
| **Flipped-pairs** | `../ast-equiv/notes-fix-flipped-pairs.md` | The 24-of-46 recall recovery campaign was corpus-driven, not soundness-driven. No commit adds a *negative* test for a wrongful equivalence. |
| **`canonical_dump` cache-key fragility** | `../ast-equiv/pyproject.toml:13`; `../ast-equiv/ast_equiv/canonicalizer.py:858`; `propstore/sidecar/passes.py:473`; `propstore/sidecar/claim_utils.py:540` | `canonical_dump` derives from SymPy printer output (`srepr`/`_print_*`), which SymPy is allowed to change across minor versions. Resolved per RD-3 by making the cache key SymPy-version-independent (ast-only hash + semantic-equivalence version tag). The previously-proposed `<1.15` upper bound was rejected. |

### Propstore-side dead-code findings

| ID | Citation | Description |
|---|---|---|
| **PV-1** | `propstore/world/value_resolver.py:524, :566` | Dead `except AstToSympyError` clauses. Resolved per RD-4: deleted. |
| **PV-2** | `propstore/conflict_detector/algorithms.py:47` | Catches `RecursionError`. `propstore/world/value_resolver.py:524` and `propstore/app/claims.py:193` do not. Inconsistent. |

### Adjacent items closed in same WS

| Finding | Citation | Why included |
|---|---|---|
| `extract_names` returns builtins | `../ast-equiv/tests/test_canonicalizer.py:41-44`; `propstore/families/claims/passes/checks.py:819-820` | Resolved per RD-2: split into `extract_all_names` + `extract_free_variables`. |
| Duplicated `_extract_function` | `../ast-equiv/ast_equiv/comparison.py:100-105`; `../ast-equiv/ast_equiv/sympy_bridge.py:287-292` | Two copies of the same function. Collapse to one. |

## Resolved decision: D-14 — bytecode tier

**Decision** (locked in by Q in `reviews/2026-04-26-claude/DECISIONS.md`): **delete `_compile_to_bytecode` and `Tier.BYTECODE` enum value**. Recovery path preserved in git history; the deletion commit message references the deleted symbols by full path.

Cluster T's HIGH X-2 and X-3 dissolve, not fixed: both findings disappear because the code disappears. `Tier` enum collapses from five members to four. README's tier list (X-4) must list the surviving four exactly.

## Code references (verified by direct read)

`../ast-equiv/ast_equiv/canonicalizer.py`: `:47-54` `parse_algorithm`; `:203-230` `_collect_mult_power_chain` (C-2); `:361-413` `visit_BinOp` — `:374-388` identity elim (C-1), `:396-405` mult-to-power (C-2), `:408` Add-overloading comment, `:409-413` pairwise Mult sort; `:486-488` correct bool/int guard; `:530-593` `WhileToForNormalizer._try_convert` (C-3); `:778-828` `TempVariableInliner._is_safe_inline_expr`; `:831-847` `canonicalize()`; `:858` `canonical_dump()`.

`../ast-equiv/ast_equiv/comparison.py`: `:23-30` `SKIP_OPS` / `_INPLACE_OFFSET=13` (deleted by Step 5); `:33-72` `Tier` enum (collapses by Step 5); `:100-105` `_extract_function` (dup); `:113-118` `_compile_to_bytecode` (deleted by Step 5); `:243-307` `compare()`; `:250-253` "Tier 1.5"/"Tier 2" comments (X-4); `:276,286,296` bare excepts — `:286` deleted with bytecode tier; `:276` and `:296` survive and get fixed by Step 4 per RD-4.

`../ast-equiv/ast_equiv/sympy_bridge.py`: `:28-114` `ast_to_sympy`; `:58-71` BinOp coverage (S-2); `:84-87` `math.log` 1-arg only (S-1); `:117-132` `_sympy_expr_equal`, `:132` `simplify(a-b)==0` (S-3); `:287-292` `_extract_function` (dup).

`../ast-equiv/pyproject.toml:13`: `sympy>=1.14.0` — open upper bound. Per RD-3 the upper bound is **not** added; the fix is on the cache-key side, not the dependency-pin side.

Propstore consumers: `propstore/world/value_resolver.py:12-13,517,524,555,566`; `propstore/conflict_detector/algorithms.py:9,46-47`; `propstore/families/claims/passes/checks.py:10,788,819-820`; `propstore/sidecar/passes.py:9-10,473`; `propstore/sidecar/claim_utils.py:12,540`; `propstore/app/claims.py:176,193`.

## First failing tests (write these first; they MUST fail before any production change)

All in `../ast-equiv/tests/` unless marked propstore-side. Each test docstring cites the cluster T finding ID.

1. **`test_C1_identity_elimination_typed.py`** — `def f(x): return x + 0` and `def g(x): return x` are NOT equivalent for non-numeric `x`. Assert `compare` returns False or rewrite refuses.

2. **`test_C2_repeated_mult_call_count.py`** — `g(x) * g(x)` (g side-effecting) vs `g(x) ** 2`. Assert `compare(...).equivalent is False`.

3. **`test_C3_while_to_for_break.py`** — Four sub-cases per the cluster T finding: break, continue, mid-body reassign, non-int init.

4. **`test_X1_compare_propagates_internal_errors.py`** — Per RD-4: monkey-patch a transform to raise `RuntimeError("synthetic")`; assert `compare()` raises (does not silently return `equivalent=False`). Two surviving tier blocks (CANONICAL `:276`, SYMPY `:296`) catch only their narrow class.

5. **`test_S1_log_two_arg.py`** — `math.log(x, 2)` vs `math.log(x) / math.log(2)`. Equivalent under SymPy tier. Per RD-1, symbols carry `real=True` and the test name says `_real_domain`.

6. **`test_S2_floordiv_mod.py`** — `x // 2` vs `(x - x % 2) // 2` with `integer=True` symbols. Per RD-1, the test name includes `_integer_domain` and the body asserts symbols carry the assumption.

7. **`test_S3_branch_cut_real_domain.py`** — Per RD-1: symbols default `real=True`; `simplify(sqrt(x*y) - sqrt(x)*sqrt(y))` is nonzero. With `positive=True` (added by domain assertion in source), it's zero. Test name and assertion both encode the assumption.

8. **`test_X4_tier_naming_consistency.py`** — Mechanical. README and `Tier` enum agree on `{NONE, CANONICAL, SYMPY, PARTIAL_EVAL}`; `BYTECODE` and `STRUCTURAL_SIMILARITY` absent from both.

9. **`test_X6_property_canonicalize_idempotent.py`** — Hypothesis property: `canonicalize(canonicalize(t)) == canonicalize(t)`.

10. **`test_X6_property_compare_transitive.py`** — Hypothesis property: triples under controlled mutation. `equivalent(a,b) ∧ equivalent(b,c) ⇒ equivalent(a,c)`.

11. **`test_cache_key_sympy_version_independent.py`** — Per RD-3: simulate a SymPy version bump (e.g. `monkeypatch.setattr(sympy, "__version__", "1.99.0")`, plus monkeypatching `sympy.srepr` to a perturbed implementation that returns differently-formatted-but-semantically-equivalent strings). For a fixed source AST, assert `canonical_dump(...)` returns a byte-identical key before and after the perturbation. Also assert the resulting key contains the literal string `SEMANTIC_EQUIVALENCE_VERSION` value (e.g. `"1"`) so the test is self-evidently coupled to the version tag, and assert that `sympy` is **not** imported by the cache-key derivation module path (AST-grep on the canonicalizer's hashing module).

11a. **`test_cache_key_invalidates_on_semantic_change.py`** — Per RD-3: build a populated cache keyed by `canonical_dump(...)` for a fixed source AST under `SEMANTIC_EQUIVALENCE_VERSION = "1"`. Monkeypatch `SEMANTIC_EQUIVALENCE_VERSION = "2"`. Recompute `canonical_dump(...)` for the same source AST. Assert the new key differs and that a lookup against the previously-populated cache misses. This proves we retain a single, deliberate knob for explicit cache invalidation when our semantics change.

11b. **`test_pyproject_no_sympy_upper_bound.py`** — Per RD-3 (acceptance gate): parse `../ast-equiv/pyproject.toml` and assert the `sympy` requirement string contains `>=1.14.0` and contains no `<` clause. Mechanical guard against accidental re-introduction of the rejected upper bound.

12. **`test_D14_bytecode_tier_deleted.py`** — Mechanical, asserts D-14 deletion.

13. **Removed-tests audit** — Grep `tests/` for `Tier\.BYTECODE`; zero hits after Step 5.

14. **`tests/algorithm_corpus/adversarial/` + `test_corpus_adversarial_negatives.py`** — ≥20 hand-curated `(a, b, expected_equivalent=False)` pairs.

15. **`test_extract_names_split.py`** — Per RD-2: assert `extract_all_names` and `extract_free_variables` exist; assert old `extract_names` does not (`AttributeError`); assert `extract_free_variables` excludes builtins, function params, comprehension targets, and local assignments; assert it includes free references.

16. **Propstore: `tests/test_T_value_resolver_dead_except_deleted.py`** — Per RD-4: AST-walk `propstore/world/value_resolver.py`, assert no `except AstToSympyError` clause, assert `AstToSympyError` is not imported. Confirms PV-1 dead clauses are gone.

17. **Propstore: `tests/test_T_canonical_dump_stability.py`** — Per RD-3: for a fixed corpus of source bodies, `canonical_dump(...)` produces byte-identical output to a checked-in golden file. The golden is keyed off `SEMANTIC_EQUIVALENCE_VERSION = "1"`. Test asserts the version constant is still `"1"` — if a future commit bumps the version, this test must be updated in the same commit (deliberate cache-invalidation discipline). The test does **not** vary on SymPy version; its golden survives SymPy upgrades.

18. **Propstore: `tests/test_T_extract_free_variables_migration.py`** — Per RD-2: `propstore/families/claims/passes/checks.py` uses `extract_free_variables` and no longer subtracts `KNOWN_BUILTINS` post-hoc. Grep gate.

19. **Propstore: `tests/test_workstream_o_ast_done.py`** — Gating sentinel; `xfail` until close.

## Production change sequence

Each step lands in its own commit on a `ws-o-ast` branch in `../ast-equiv`. Last steps land in propstore.

**Step 1 — Type-narrowed identity elimination (C-1).** `canonicalizer.py:374-388`. Extend annotation tracker to track NUMERIC bindings. Rewrite fires only when the variable side is statically NUMERIC; unannotated `Name` defaults to do-not-rewrite.

**Step 2 — Pure-call gate on repeated-mult-to-power (C-2).** `canonicalizer.py:203-230, 396-405`. Restrict to operands that are `Name`/`Attribute`/`Subscript`/`Constant` OR a `Call` to a hardcoded `_PURE_CALLS` allowlist.

**Step 3 — Conservative WhileToForNormalizer (C-3).** `canonicalizer.py:530-593`. Pre-conditions per cluster T finding: refuse on Break/Continue, body-reassign-of-loop-var, body-reassign-of-bound-name, non-int init.

**Step 4 — Tier-failure propagation in `compare()` per RD-4.** `comparison.py:276, 296`. CANONICAL tier catches `AlgorithmParseError` only; SymPy tier catches `AstToSympyError` only. Anything else propagates. Add `tier_failures: dict[Tier, type[Exception]]` field to `ComparisonResult` (additive).

**Step 5 — Delete bytecode tier (D-14).** Remove `Tier.BYTECODE`, `_compile_to_bytecode`, `SKIP_OPS`, `_INPLACE_OFFSET`, the `:286` bytecode tier-evaluation block. Grep `tests/` for `Tier\.BYTECODE` and `_compile_to_bytecode`; delete every match. Commit message includes the recovery-path template referencing parent SHA. Run 172-pair corpus — must remain 172/172.

**Step 6 — SymPy bridge: log/floordiv/mod (S-1, S-2).** `sympy_bridge.py:84-87, :58-71`. Accept `math.log(x)`, `math.log(x, base)`, `math.log2(x)`, `math.log10(x)`; map two-arg `log(x, base) -> sympy.log(x) / sympy.log(base)`. Add FloorDiv → `sympy.floor(a / b)`; Mod → `sympy.Mod(a, b)`. Bitwise rejected with explicit error.

**Step 7 — SymPy symbol assumptions per RD-1.** `sympy_bridge.py`. Construct `sympy.Symbol(name, real=True, finite=True)` by default. Implement domain-assertion lookup: if the source AST contains `assert x > 0` (or analogous) in scope, upgrade that symbol to `positive=True`. Document config flag `assume_complex=False`.

**Step 8 — Tier numbering / README (X-4).** README rewrite: list four values exactly — NONE, CANONICAL, SYMPY, PARTIAL_EVAL. Drop "Structural similarity" and "Bytecode". `comparison.py:250-253`: replace "Tier 1.5"/"Tier 2" comments with `Tier` member names. Add a sentence noting `Tier.BYTECODE` removed in WS-O-ast (D-14).

**Step 9 — Adversarial corpus + property tests (X-6, flipped-pairs).** Add `tests/algorithm_corpus/adversarial/` with ≥20 hand-curated negative pairs. Rewrite `tests/test_properties.py` to drive Hypothesis at identifiers/calls/aug-assigns/while loops/conditional bodies. Add idempotence and transitivity properties. All decorated `@pytest.mark.property`.

**Step 10 — SymPy-version-independent `canonical_dump` cache key per RD-3.** Refactor `canonical_dump` (`ast_equiv/canonicalizer.py:858`) so the cache-key output derives from the canonicalized `ast.AST` plus a module-level `SEMANTIC_EQUIVALENCE_VERSION: str = "1"`. The hashing path uses only stdlib (`ast`, `hashlib`) — no `sympy.srepr`, no SymPy printer, no SymPy import. Specifically:

1. Add `SEMANTIC_EQUIVALENCE_VERSION = "1"` at module scope with a docstring: "Bump in the same commit as any canonicalization-rule, tier-set, or equivalence-semantics change. SymPy version is irrelevant to this constant."
2. Add `_ast_canonical_hash(tree: ast.AST) -> str`: deterministic ordered serialization of the canonicalized AST (node type, fields, child order), hashed via `hashlib.sha256`.
3. Rewrite `canonical_dump(tree)` to return `f"{SEMANTIC_EQUIVALENCE_VERSION}:{_ast_canonical_hash(tree)}"`. The `version:hash` shape self-documents cache scope.
4. Drop the `<1.15` upper bound from `pyproject.toml:13`.
5. Per `feedback_no_fallbacks.md`: no dual-emission, no "old key as fallback." Existing caches under the old key are invalidated; consumers regenerate.

Acceptance: `test_cache_key_sympy_version_independent.py`, `test_cache_key_invalidates_on_semantic_change.py`, and `test_pyproject_no_sympy_upper_bound.py` green. SymPy is not imported by any module on the cache-key derivation path.

**Step 11 — `extract_names` rename and split per RD-2.** Implement `extract_all_names` (rename of current `extract_names`) and `extract_free_variables` (new, with proper scope analysis). Delete the `extract_names` symbol entirely. Update ast-equiv internal callers. No compat alias.

**Step 12 — Propstore consumer cleanup per RD-4 + RD-2.** Coordinated propstore-side commit:
1. `propstore/world/value_resolver.py:524`: delete the `except AstToSympyError` clause.
2. `propstore/world/value_resolver.py:566`: delete the `except AstToSympyError` clause.
3. Remove the `AstToSympyError` import from `value_resolver.py`.
4. Add `RecursionError` catches at `value_resolver.py:524, :566` and `app/claims.py:193` to match `conflict_detector/algorithms.py:47` (closes PV-2).
5. `propstore/families/claims/passes/checks.py:788, :819-820`: switch from `extract_names` minus `KNOWN_BUILTINS` to `extract_free_variables`. Drop the post-hoc subtraction.
6. `propstore/sidecar/passes.py:473` and `propstore/sidecar/claim_utils.py:540`: confirm both consumers continue to call `canonical_dump(...)` and treat its return as an opaque string key. No code change is required at the call sites — the key derivation changes inside ast-equiv per RD-3 — but the migration commit explicitly invalidates existing on-disk cache entries (see Step 13).
7. Run propstore full suite — must remain green vs `logs/test-runs/pytest-20260426-154852.log` baseline.

**Step 13 — Propstore pin + `canonical_dump` golden + cache invalidation per RD-3.** Bump propstore's ast-equiv pin to the WS-O-ast merge sha (git-hash, not PyPI label, per `feedback_tags_immutable.md`). Add `tests/test_T_canonical_dump_stability.py` with a checked-in golden file derived from the new pin. The golden is bound to `SEMANTIC_EQUIVALENCE_VERSION = "1"`; a future bump of the version constant requires regenerating the golden in the same commit. As part of this commit, invalidate any propstore-side on-disk cache directory whose entries were keyed by the SymPy-srepr-derived `canonical_dump` (delete the cache directory contents in the migration script; consumers regenerate). No dual-key fallback. SymPy version drift is no longer an invalidation trigger.

**Step 14 — Close gaps and gate.** Update `docs/gaps.md` to remove the cluster-T HIGH and MED entries (including dissolved X-2/X-3); add `# WS-O-ast closed <sha>` line. Flip `tests/test_workstream_o_ast_done.py` from `xfail` to `pass`. Update STATUS to `CLOSED <sha>`.

## Acceptance gates

ALL must hold before declaring WS-O-ast done:

- [ ] `cd ../ast-equiv && uv run pytest` — green, including all new tests.
- [ ] `cd ../ast-equiv && uv run pyright` — 0 errors.
- [ ] `tests/test_corpus.py` — 172/172 corpus pairs still pass.
- [ ] propstore full suite — green; no NEW failures vs baseline.
- [ ] `Tier.BYTECODE` and `_compile_to_bytecode` absent from `ast_equiv/comparison.py`; no test references either.
- [ ] `propstore/world/value_resolver.py` — no `except AstToSympyError` clauses; no `AstToSympyError` import; `RecursionError` consistent across `value_resolver.py`, `conflict_detector/algorithms.py:47`, `app/claims.py:193`.
- [ ] `../ast-equiv/pyproject.toml` `sympy` requirement is `>=1.14.0` with **no** upper bound (per RD-3).
- [ ] `ast_equiv/canonicalizer.py` exports `SEMANTIC_EQUIVALENCE_VERSION = "1"`; `canonical_dump` derives its key from `(SEMANTIC_EQUIVALENCE_VERSION, _ast_canonical_hash(tree))` only; no `sympy` import on the cache-key derivation path (AST-grep gate).
- [ ] `test_cache_key_sympy_version_independent.py` green; `test_cache_key_invalidates_on_semantic_change.py` green; `test_pyproject_no_sympy_upper_bound.py` green.
- [ ] README tier list is exactly `{NONE, CANONICAL, SYMPY, PARTIAL_EVAL}`.
- [ ] `extract_names` symbol absent from `ast_equiv` public API; `extract_all_names` and `extract_free_variables` present.
- [ ] `propstore/families/claims/passes/checks.py` uses `extract_free_variables`; no `KNOWN_BUILTINS` post-hoc subtraction.
- [ ] propstore pin updated to merge sha; `canonical_dump` golden file checked in.
- [ ] `docs/gaps.md` has no open rows for cluster-T findings.
- [ ] STATUS line `CLOSED <sha>`.

## Done means done

Done when **every finding in the tables at the top is closed**. C-1/C-2/C-3 typed tests + corpus regression green; X-1 propagates correctly per RD-4 across the two surviving tier blocks; X-2/X-3 dissolved by Step 5; S-1/S-2/S-3 bridge handles `log(x, base)`, FloorDiv, Mod, with `real=True` symbols per RD-1; X-4 README/enum/comments agree; X-6 idempotence and transitivity gated; ≥20-pair adversarial corpus exists; bytecode tier deleted with recovery-path commit message; PV-1 dead-except clauses deleted per RD-4; PV-2 `RecursionError` consistency closed; `extract_names` split per RD-2; `canonical_dump` cache key is SymPy-version-independent per RD-3, derived from an ast-only canonical hash plus `SEMANTIC_EQUIVALENCE_VERSION`, with **no** upper bound on SymPy in `pyproject.toml` and no compat fallback for the old SymPy-srepr-keyed cache.

## Papers / specs referenced

- **Knuth 1970, "Simple Word Problems in Universal Algebras"** — relevant to AC-flat normalization and confluence as the property X-6 idempotence aspires to.
- **Pierce 2002, "Types and Programming Languages"** — §6.3 α-equivalence; document the gap with `PositionalRenamer`.
- **Bachmair & Ganzinger 2001, "Resolution Theorem Proving"** — citation for Step 9 adversarial corpus methodology.

Each must have a `notes.md` before close (cluster G L11 promotion).

## Cross-stream notes

- **WS-P** is gated on this WS. WS-P depends on `compare()` being sound and on `canonical_dump`'s cache key being SymPy-version-independent per RD-3 (ast-only hash + `SEMANTIC_EQUIVALENCE_VERSION`). Both addressed.
- **WS-P tier-acceptance contract (Codex re-review #15)**: WS-P's algorithm-conflict-suppression whitelist is `{Tier.CANONICAL, Tier.SYMPY, Tier.PARTIAL_EVAL}` against the post-D-14 ast-equiv tier set `{NONE, CANONICAL, SYMPY, PARTIAL_EVAL}`. PARTIAL_EVAL is a true-equivalence proof and suppresses conflict alongside CANONICAL and SYMPY; NONE is the "couldn't decide" fallback and does NOT suppress conflict. WS-O-ast preserves the four-value enum in this exact shape; renaming or removing PARTIAL_EVAL would break WS-P's contract and requires coordination.
- **WS-A** is independent; this WS can run in parallel.
- **WS-O-{arg,gun,qui,bri}** sibling streams are independent.
- `propstore/sidecar/passes.py:473` and `propstore/sidecar/claim_utils.py:540` use `canonical_dump` as cache keys. Step 13's golden file + the on-disk cache invalidation gate cache-correctness discipline; SymPy version drift is no longer a re-baselining trigger.

## What this WS does NOT do

Does NOT implement structural-similarity tier (drop README claim instead). Does NOT add unit/dimension tracking (WS-O-bri / WS-P). Does NOT change public API except: additive `tier_failures` on `ComparisonResult`; subtractive removal of `Tier.BYTECODE` (D-14); subtractive removal and replacement of `extract_names` per RD-2. No back-compat aliases (per `feedback_no_fallbacks.md`).
