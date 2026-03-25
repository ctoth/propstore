# Propstore Deep Audit — Synthesis Report
**Date:** 2026-03-24

## Test Suite Baseline
**1249/1251 pass.** 2 failures: schema dimension-key pattern doesn't exclude control chars; flaky Hypothesis deadline on cold start.

---

## CRITICAL — Must Fix

### C1. `relate.py` writes LLM output directly to source-of-truth storage
**Source:** arch-analyst
**Location:** `propstore/relate.py:468-489`
**Issue:** `write_stance_file()` writes raw LLM stance classifications to `knowledge/stances/*.yaml`, which are then ingested by `build_sidecar.py` as source of truth. No proposal intermediary exists.
**Violation:** Core design principle — "heuristic output is PROPOSAL artifacts, never source mutations."
**Fix:** Write to a `proposals/` directory; require explicit user promotion to `knowledge/`.

### C2. `parse_expr` executes arbitrary Python from user YAML
**Source:** z3-analyst
**Location:** `propstore/equation_comparison.py:76,90`
**Issue:** SymPy's `parse_expr` can execute arbitrary code. Claim YAML files authored by users flow through this path.
**Fix:** Use `parse_expr(..., transformations=..., local_dict=...)` with restricted namespace, or switch to `sympify` with `evaluate=False`.

### C3. Corpus calibrator conflates corpus size with claim evidence
**Source:** opinion-analyst
**Location:** `propstore/calibrate.py:143`
**Issue:** `from_probability(p, float(self._n))` passes full corpus size (e.g., 10,000) as evidence count, producing u≈0.0002 — near-dogmatic certainty. Corpus size measures distribution coverage, not evidence for any individual claim.
**Violation:** "Honest ignorance over fabricated confidence" principle.
**Fix:** Use a per-claim evidence count, or cap `n` to reflect actual claim-level evidence.

### C4. MaxSAT `model.evaluate()` returns `z3.BoolRef`, not Python `bool`
**Source:** z3-analyst
**Location:** `propstore/maxsat_resolver.py:45`
**Issue:** `z3.BoolRef` truthiness is version-dependent. Some z3 versions raise `Z3Exception` on `bool(BoolVal(False))`.
**Fix:** Use `z3.is_true(model.evaluate(...))`.

### C5. LLM API failures indistinguishable from genuine "no relationship"
**Source:** error-analyst
**Location:** `propstore/relate.py:152-186`
**Issue:** API/JSON parse failures return `type: "none", confidence: 0.0` — same as a real negative. Downstream has no way to detect the failure.
**Fix:** Return a distinct error/failure type, or raise.

---

## MAJOR — Significant Correctness/Design Issues

### M1. No actual ASPIC+ argument construction
**Source:** aspic-analyst
**Location:** `propstore/structured_argument.py`
**Issue:** Arguments are flat 1:1 claim mappings. No strict/defeasible rules, no recursive building per Modgil & Prakken 2018 Def 5. `premise_claim_ids` always `()`, `subargument_ids` always `()`.
**Impact:** Last-link/weakest-link comparison (Defs 20-21) cannot be implemented without sub-argument structure.

### M2. Dixon 1993 cited but not implemented
**Source:** atms-analyst
**Location:** `propstore/world/atms.py`
**Issue:** CLAUDE.md lists Dixon 1993 as grounding for context switching = AGM operations. No entrenchment ordering, no AGM contraction/expansion, no context-switching algorithm exists. The engine docstring is honest, but project docs don't distinguish aspiration from implementation.

### M3. Grounded extension post-hoc attack-CF pruning is ad-hoc
**Source:** dung-analyst
**Location:** `propstore/dung.py:126-150`
**Issue:** After computing the least fixed point over defeats, code surgically removes attack-conflicting arguments and re-iterates. This is not a valid least fixed point of any well-defined characteristic function. Modgil & Prakken expect defeat to already encode preferences.

### M4. Tree decomposition DP has brute-force complexity
**Source:** praf-analyst
**Location:** `propstore/praf_treedecomp.py`
**Issue:** DP tracks full edge sets and forgotten arguments in table keys — row count bounded by 2^|defeats| × 2^|args|. Zero asymptotic improvement over brute-force enumeration.

### M5. P_A conflated with DF-QuAD base score
**Source:** praf-analyst
**Location:** `propstore/praf_dfquad.py`
**Issue:** Li 2012's P_A (existence probability for MC sampling) is used as Rago 2016's τ (intrinsic strength for DF-QuAD). A rarely-existing argument ≠ a weak argument.

### M6. HypotheticalWorld + ATMS backend will crash
**Source:** atms-analyst
**Location:** `propstore/world/hypothetical.py`
**Issue:** `HypotheticalWorld` has no `atms_engine()` method. ATMS-backend resolution path calls `view.atms_engine()` → `AttributeError`.

### M7. Vacuous-opinion pruning at AF construction is a pre-render gate
**Source:** arch-analyst
**Location:** `propstore/argumentation.py:137`
**Issue:** Filtering vacuous opinions during AF construction violates design checklist item 3: "Does this add a gate anywhere before render time? If yes → WRONG."

### M8. No schema-level enforcement of opinion invariant b+d+u=1
**Source:** opinion-analyst
**Location:** SQLite `claim_stance` table
**Issue:** Nothing prevents inserting `(b=0.9, d=0.9, u=0.9)`. Invariant only checked in Python `Opinion.__init__`.

### M9. `mc_confidence` parameter accepted but ignored
**Source:** praf-analyst
**Location:** `propstore/praf.py`
**Issue:** z=1.96 hardcoded in both stopping criterion and CI computation. Non-default confidence levels silently produce wrong statistical guarantees.

---

## MODERATE — Should Fix

### Mod1. `relate.py` imports upward from CLI layer
`propstore/relate.py:15` → `from propstore.cli.helpers import write_yaml_file`. Heuristic layer reaching into agent workflow layer.

### Mod2. `praf.py` ↔ `praf_treedecomp.py` circular import
Runtime function-body imports. Works via deferred resolution but fragile.

### Mod3. WorldModel runtime-imports CLI Repository
`world/model.py:46` → `from propstore.cli.repository import Repository`. Layer 5 pulling Layer 6.

### Mod4. Float equality on MC-sampled probabilities
`world/resolution.py:248` uses `p == best_prob` on Monte Carlo results. FP differences create false ties/winners.

### Mod5. Float inequality in hypothetical conflict detection
`world/hypothetical.py:143` uses `val_a != val_b` instead of tolerance-based comparison.

### Mod6. `embed.py` swallows all sqlite3.OperationalError
Lines 198, 368, 443, 526-573. Intended for "table doesn't exist" but catches disk full, corruption, permission denied.

### Mod7. Global mutable caches without invalidation
`form_utils.py:56` (`_form_cache`) and `unit_dimensions.py:33` (`_symbol_table`). Cross-test contamination, stale data in long-running processes.

### Mod8. Thread-unsafe `_current_guards` in z3_conditions.py
Instance attribute set during translation, never initialized in `__init__`. Concurrent callers corrupt each other.

### Mod9. No Z3 solver timeout
Pathological inputs can hang indefinitely. No `solver.set("timeout", ...)`.

### Mod10. Logarithmic unit conversions have no zero/domain guards
`form_utils.py:176,199` — `divisor==0`, `reference==0`, `base==1` produce runtime math errors.

### Mod11. `float(raw_value)` with no try/except in sidecar build
`build_sidecar.py:1165` — A single "N/A" value aborts the entire build.

### Mod12. No nogoods for derived-vs-derived conflicts
Two derived ATMS nodes for the same concept can hold contradictory values with overlapping support. Nogoods only from sidecar claim-to-claim conflicts.

### Mod13. Unbound queries treat all conditional claims as active
`world/bound.py:186` returns `True` for all claims when no bindings exist.

### Mod14. Support weights silently discarded in DF-QuAD
API accepts weights in `supports.items()` but `_weight` is explicitly ignored.

### Mod15. Missing `p_defeats` keys cause KeyError in component PrAFs
`praf.py:335-336` filters defeats creating mismatched keys between `framework.defeats` and `p_defeats`.

### Mod16. No assumption retraction in ATMS
Context switching per Dixon 1993 (removing assumptions) is impossible. Future analysis is additive-only.

### Mod17. Sensitivity module entirely disconnected from opinion algebra
No integration between the two despite both being in the uncertainty domain.

### Mod18. `equation_comparison.py` appears dead
No propstore module imports it. (But contains the `parse_expr` injection vulnerability.)

### Mod19. Elitist comparison vacuous truth
`preference.py:28` — `strictly_weaker(anything, [], "elitist")` returns True, blocking attacks. Unreachable from `claim_strength` but exposed in API.

### Mod20. CEL type checker doesn't validate operand types for &&/||
`3 && 5` passes without error.

### Mod21. Worldline runner silently swallows sensitivity/argumentation failures
`worldline_runner.py:179,266` — `except Exception` drops errors with no indication.

### Mod22. Assert used as runtime type check
`param_conflicts.py:180` — `assert isinstance(...)` caught by downstream `except AssertionError`. Disabled under `python -O`.

---

## MISSING HYPOTHESIS PROPERTIES / TEST GAPS

### From opinion algebra:
- Consensus fusion commutativity: `a ⊕ b == b ⊕ a`
- Consensus with vacuous opinion is identity: `a ⊕ (0,0,1,a) == a`
- Conjunction/disjunction with vacuous inputs
- Discount with full trust as identity
- `from_probability` with invalid inputs (negative, >1)
- Schema-level b+d+u=1 enforcement

### From Dung AF:
- Property tests with attacks≠defeats (Hypothesis strategy always sets `attacks=None`)
- Grounded semantics in Z3 acceptance queries
- Brute-force size guard (2^n enumeration unlimited)

### From PrAF:
- MC tests with P_A < 1 (all use dogmatic_true)
- `build_praf()` has zero test coverage
- DF-QuAD with non-trivial support weights

### From ASPIC+:
- Mixed-dimensionality claim_strength comparisons
- Cyclic support chains
- Missing stance records between contradictory claims
- Structured projection with preference-filtered attacks

### From Z3/CEL:
- Z3 UNKNOWN results
- Concurrent solver use
- Malicious SymPy expressions
- Logical ops with non-boolean operands
- Zero/negative MaxSAT weights
- Solver timeouts

### From ATMS:
- HypotheticalWorld with ATMS backend
- Derived-vs-derived conflict detection
- Assumption retraction

---

## ARCHITECTURE SUMMARY

**What works well:**
- Core Dung AF semantics (characteristic function, admissibility, complete/preferred/stable) are correctly implemented
- Opinion algebra (consensus, discounting, conjunction, disjunction, negation) matches Jøsang 2001
- ATMS label minimality, normalization, nogood pruning are sound against de Kleer 1986
- Resolution is correctly render-time per design principle
- Cayrol derived defeats correctly iterate to fixpoint
- Preference filtering matches Modgil & Prakken Def 9

**What's structurally broken:**
- `relate.py` crosses three architectural layers (render, heuristic, storage) — should be split
- CLI helpers contain mislocated business logic that other layers depend on
- The calibration pipeline produces fabricated confidence, undermining the entire uncertainty story
- ASPIC+ is a naming convention, not a real implementation — no rules, no sub-arguments
- Tree decomposition provides zero benefit over brute force
- Two cited papers (Dixon 1993, Denoeux 2019) are aspirational, not implemented
