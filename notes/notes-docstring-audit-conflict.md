# Docstring Audit: propstore/conflict_detector/

Audited 2026-03-24. All 9 files in the conflict_detector package.

---

## 1. `__init__.py`

### Finding 1.1 -- Module docstring is vacuous
- **File/Line:** `__init__.py:1`
- **Docstring:** `"Conflict detector package."`
- **Actual behavior:** This module is the public API surface. It re-exports `detect_conflicts`, `detect_transitive_conflicts`, all four collector functions, all three context helpers, and the models. It also performs a lazy import of `propstore.param_conflicts.detect_transitive_conflicts` for the transitive variant. The docstring says nothing about what the package does or what it exports.
- **Severity:** OMISSION -- The docstring hides that this is the public facade with lazy imports to two different backend modules (orchestrator.py and param_conflicts).

### Finding 1.2 -- `detect_transitive_conflicts` has no docstring at all
- **File/Line:** `__init__.py:40-54`
- **Actual behavior:** Delegates to `propstore.param_conflicts.detect_transitive_conflicts`. No docstring, no hint about what "transitive" means here or how it differs from `detect_conflicts`.
- **Severity:** OMISSION

### Finding 1.3 -- `detect_conflicts` wrapper has no docstring
- **File/Line:** `__init__.py:26-37`
- **Actual behavior:** Thin wrapper that lazy-imports and delegates to `orchestrator.detect_conflicts`. No documentation at all.
- **Severity:** OMISSION

---

## 2. `algorithms.py`

### Finding 2.1 -- Module docstring is accurate but incomplete
- **File/Line:** `algorithms.py:1`
- **Docstring:** `"Algorithm-claim conflict detection."`
- **Actual behavior:** The module detects conflicts between algorithm claims that share a concept. It uses AST comparison (`ast_equiv.compare`) to determine structural equivalence, and only flags pairs as conflicting when they are NOT equivalent (or equivalence is low-tier). The docstring omits the AST-equivalence mechanism entirely.
- **Severity:** OMISSION -- The key mechanism (AST structural comparison with tiers and similarity scores) is invisible from the docstring.

### Finding 2.2 -- `detect_algorithm_conflicts` has no docstring
- **File/Line:** `algorithms.py:22-89`
- **Actual behavior:** Complex function that: collects algorithm claims, groups by concept, does pairwise AST comparison, skips equivalent pairs at tier <= 2, tries context-based classification first, falls back to condition classification. None of this is documented.
- **Severity:** OMISSION

### Finding 2.3 -- `_bindings_for_algorithm_claim` has no docstring
- **File/Line:** `algorithms.py:92-101`
- **Actual behavior:** Extracts a name-to-concept mapping from a claim's `variables` list, using either `name` or `symbol` as the key. Undocumented.
- **Severity:** OMISSION

---

## 3. `collectors.py`

### Finding 3.1 -- Module docstring is misleading
- **File/Line:** `collectors.py:1`
- **Docstring:** `"Claim grouping helpers for conflict detection."`
- **Actual behavior:** The word "grouping" is accurate -- each function groups claims by a different key. However the docstring says "helpers" which undersells the role. These are the data-shaping functions that determine what gets compared to what. The grouping keys are substantively different per claim type:
  - measurements: `(target_concept, measure)` tuple
  - parameters: `concept` string
  - equations: `(dependent_concept, tuple_of_independent_concepts)` from `equation_signature()`
  - algorithms: `concept` string (with fallback to first variable's concept)
- **Severity:** HALF-TRUTH -- "Grouping helpers" is vague enough to be true but hides the critical detail that each collector uses a fundamentally different grouping key, which determines what pairs are even considered for conflict.

### Finding 3.2 -- `_collect_algorithm_claims` hides fallback behavior
- **File/Line:** `collectors.py:54-78`
- **Actual behavior:** No docstring, but the function name suggests it simply collects algorithm claims. In reality it has a two-tier grouping strategy: first tries `claim["concept"]`, and only if that's absent, falls back to the first variable's concept from `claim["variables"]`. This fallback could group unrelated algorithms together if they happen to share a first variable concept.
- **Severity:** OMISSION

### Finding 3.3 -- All four collector functions lack docstrings
- **File/Lines:** `collectors.py:12`, `collectors.py:28`, `collectors.py:39`, `collectors.py:54`
- **Severity:** OMISSION -- The return types are visible in signatures but the grouping semantics (what constitutes "same group") are not documented.

---

## 4. `context.py`

### Finding 4.1 -- Module docstring is accurate
- **File/Line:** `context.py:1`
- **Docstring:** `"Shared context-aware conflict classification helpers."`
- **Actual behavior:** Provides context classification for conflict detection. Accurate.
- **Severity:** None.

### Finding 4.2 -- `_classify_pair_context` docstring is a HALF-TRUTH
- **File/Line:** `context.py:18`
- **Docstring:** `"Check if two claims' contexts make them non-conflicting."`
- **Actual behavior:** The function returns `ConflictClass.CONTEXT_PHI_NODE` or `None`. The docstring says it checks if contexts make claims "non-conflicting," implying the return value means "yes, non-conflicting." But the function returns `CONTEXT_PHI_NODE` when claims ARE in different contexts (excluded or non-visible) -- which is a conflict classification, not a non-conflict signal. And it returns `None` when contexts don't resolve the conflict (same context, one is None, or one is visible from the other). So:
  - `None` = "contexts don't help, still potentially conflicting" (not "non-conflicting")
  - `CONTEXT_PHI_NODE` = "these are in separate contexts" (a phi-node, which IS a kind of non-conflict -- but is recorded as a conflict record anyway)

  The docstring's framing is backwards from what the caller actually does with the return value. The caller (`_append_context_classified_record`) appends a record when the result is NOT None and skips when it IS None. So `CONTEXT_PHI_NODE` means "create a record with this softer classification" -- NOT "non-conflicting, skip entirely."
- **Severity:** HALF-TRUTH -- The docstring describes the intent but inverts the mental model of what the return values mean. A reader would expect `True`/`False` semantics ("are they non-conflicting?") but gets an enum-or-None where None means "unknown/irrelevant" and the enum means "classified as context-separated."

### Finding 4.3 -- `_claim_context` has no docstring
- **File/Line:** `context.py:34-41`
- **Actual behavior:** Extracts a context string from a claim dict, checking `context` first then `context_id` as fallback. Returns None if neither is present or non-empty. Undocumented.
- **Severity:** OMISSION

### Finding 4.4 -- `_append_context_classified_record` has no docstring
- **File/Line:** `context.py:44-73`
- **Actual behavior:** Tries to classify a pair via context; if classification succeeds, appends a CONTEXT_PHI_NODE record and returns True (meaning "handled, skip further classification"). If classification returns None, returns False (meaning "not handled, caller must classify"). This is the central dispatch mechanism for context-aware conflict detection and it has zero documentation.
- **Severity:** OMISSION -- This is arguably the most important function in context.py since it's called by every detector module, and its boolean return value controls the flow of all four detection paths.

---

## 5. `equations.py`

### Finding 5.1 -- Module docstring is accurate but incomplete
- **File/Line:** `equations.py:1`
- **Docstring:** `"Equation-claim conflict detection."`
- **Actual behavior:** Detects conflicts between equation claims that share the same signature (dependent concept + independent concepts), using canonical form comparison. The docstring omits the canonicalization mechanism.
- **Severity:** OMISSION

### Finding 5.2 -- `detect_equation_conflicts` has no docstring
- **File/Line:** `equations.py:21-79`
- **Actual behavior:** Groups equations by signature, canonicalizes each, does pairwise comparison of canonical forms, tries context classification first, falls back to condition classification. Undocumented.
- **Severity:** OMISSION

---

## 6. `measurements.py`

### Finding 6.1 -- Module docstring is accurate but incomplete
- **File/Line:** `measurements.py:1`
- **Docstring:** `"Measurement-claim conflict detection."`
- **Actual behavior:** Detects conflicts between measurement claims grouped by `(target_concept, measure)`. Has special-case logic for `listener_population` that upgrades conflicts to PHI_NODE when populations differ. This population-aware behavior is completely invisible from the docstring.
- **Severity:** OMISSION -- The `listener_population` special case (lines 62-73) is a significant behavioral wrinkle. Two measurements with different listener populations are classified as PHI_NODE rather than going through normal condition classification. This policy decision is undocumented.

### Finding 6.2 -- `detect_measurement_conflicts` has no docstring
- **File/Line:** `measurements.py:24-85`
- **Severity:** OMISSION

---

## 7. `models.py`

### Finding 7.1 -- Module docstring is accurate
- **File/Line:** `models.py:1`
- **Docstring:** `"Shared conflict detector models."`
- **Actual behavior:** Defines `ConflictClass` enum and `ConflictRecord` dataclass. Accurate.
- **Severity:** None.

### Finding 7.2 -- `ConflictClass` enum values are undocumented
- **File/Line:** `models.py:9-15`
- **Actual behavior:** Six enum values: COMPATIBLE, PHI_NODE, CONFLICT, OVERLAP, PARAM_CONFLICT, CONTEXT_PHI_NODE. No docstrings on any of them. The semantic differences between PHI_NODE vs CONTEXT_PHI_NODE, CONFLICT vs OVERLAP, and when PARAM_CONFLICT is used vs CONFLICT are all left to the reader to infer from usage across the codebase.
- **Severity:** OMISSION -- These are the core output vocabulary of the entire conflict detection system and none of them are defined.

### Finding 7.3 -- `ConflictRecord` dataclass is undocumented
- **File/Line:** `models.py:18-28`
- **Severity:** OMISSION

---

## 8. `orchestrator.py`

### Finding 8.1 -- Module docstring is accurate
- **File/Line:** `orchestrator.py:1`
- **Docstring:** `"Top-level conflict detection orchestration."`
- **Actual behavior:** Orchestrates all four conflict detectors and also invokes transitive param conflict detection. Accurate.
- **Severity:** None.

### Finding 8.2 -- `detect_conflicts` docstring is a HALF-TRUTH
- **File/Line:** `orchestrator.py:26`
- **Docstring:** `"Detect conflicts between claims binding to the same concept."`
- **Actual behavior:** This is partially true for parameters and algorithms (which group by concept), but:
  1. **Measurements** group by `(target_concept, measure)` -- same concept but different measure will NOT be compared. The docstring implies any two claims on the same concept would be compared.
  2. **Equations** group by signature `(dependent_concept, independent_concepts)` -- same dependent concept but different independent variables will NOT be compared.
  3. The function also calls `_detect_param_conflicts` from `propstore.param_conflicts` (line 63-65), which does TRANSITIVE conflict detection across concepts connected by equations. This is fundamentally NOT "claims binding to the same concept" -- it's claims on DIFFERENT concepts that are mathematically related.
- **Severity:** HALF-TRUTH -- The docstring describes only the simplest case and completely omits the transitive cross-concept detection, which is arguably the most sophisticated part of what this function does.

### Finding 8.3 -- `_build_condition_solver` has no docstring
- **File/Line:** `orchestrator.py:69-74`
- **Actual behavior:** Attempts to import and instantiate Z3ConditionSolver; returns None if z3 is not installed. Undocumented.
- **Severity:** OMISSION

---

## 9. `parameters.py`

### Finding 9.1 -- Module docstring is accurate but incomplete
- **File/Line:** `parameters.py:1`
- **Docstring:** `"Parameter-claim conflict detection."`
- **Actual behavior:** Detects parameter conflicts using a sophisticated three-path strategy: (1) if Z3 is available and there are >2 claims, partition into equivalence classes, then detect within-class and cross-class conflicts separately; (2) otherwise fall back to naive pairwise comparison. The docstring reveals none of this architectural complexity.
- **Severity:** OMISSION -- This is the most complex module in the package with three distinct detection strategies, Z3 integration, and equivalence class partitioning. "Parameter-claim conflict detection" is technically true but profoundly uninformative.

### Finding 9.2 -- `detect_parameter_conflicts` return type undocumented
- **File/Line:** `parameters.py:33-92`
- **Actual behavior:** Returns `tuple[list[ConflictRecord], dict[str, list[dict]]]` -- a tuple of records AND the by_concept grouping dict. Every other detect function in this package returns only `list[ConflictRecord]`. This extra return value is consumed by the orchestrator (line 31) to pass into `_detect_param_conflicts` for transitive detection. This asymmetry is completely undocumented.
- **Severity:** OMISSION -- The return type signature is visible but the reason for returning `by_concept` alongside records is not explained anywhere.

### Finding 9.3 -- `_build_z3_solver` is dead code (or redundant)
- **File/Line:** `parameters.py:25-30`
- **Actual behavior:** This function duplicates `_build_condition_solver` in orchestrator.py (lines 69-74). The orchestrator already builds a solver and passes it in via the `solver` kwarg. `_build_z3_solver` is only called on line 42 when `solver is None`, which would happen if someone calls `detect_parameter_conflicts` directly without a solver. No docstring.
- **Severity:** OMISSION -- Not a docstring lie per se, but the existence of two identical solver-building functions across the package is an undocumented design smell.

### Finding 9.4 -- `_detect_pairwise_parameter_conflicts` has no docstring
- **File/Line:** `parameters.py:95-142`
- **Severity:** OMISSION

### Finding 9.5 -- `_detect_equivalent_parameter_conflicts` has no docstring
- **File/Line:** `parameters.py:145-187`
- **Actual behavior:** Detects conflicts within Z3 equivalence classes. Claims in the same class have logically equivalent conditions, so any value disagreement is a hard CONFLICT (line 182). Undocumented.
- **Severity:** OMISSION

### Finding 9.6 -- `_detect_cross_class_parameter_conflicts` has no docstring
- **File/Line:** `parameters.py:190-256`
- **Actual behavior:** Compares claims across Z3 equivalence classes using disjointness checks. If conditions are disjoint, classifies as PHI_NODE; otherwise OVERLAP. Falls back to `_classify_conditions` on Z3 failure. Undocumented.
- **Severity:** OMISSION

---

## Summary

| Severity | Count |
|----------|-------|
| LIE | 0 |
| HALF-TRUTH | 3 |
| STALE | 0 |
| OMISSION | 22 |

### Key HALF-TRUTH findings (the ones that actively mislead):

1. **`context.py:18`** -- `_classify_pair_context` says "Check if two claims' contexts make them non-conflicting" but the function's return semantics are inverted from what this description implies. `None` means "not resolved" and the enum value means "classified as context-separated" (which still produces a record).

2. **`orchestrator.py:26`** -- `detect_conflicts` says "Detect conflicts between claims binding to the same concept" but the function also performs transitive cross-concept conflict detection via `_detect_param_conflicts`, and measurement/equation grouping is more specific than just "same concept."

3. **`collectors.py:1`** -- "Claim grouping helpers" hides that each collector uses a fundamentally different grouping key, which is the most consequential design decision in the whole conflict detection pipeline.

### The big picture:

The package has exactly THREE docstrings with actual content (as opposed to module-level one-liners): the `__init__.py` module docstring, the `_classify_pair_context` function docstring, and the `detect_conflicts` orchestrator docstring. Of those three, two are half-truths. The remaining ~20 functions and classes have no docstrings at all. The module-level one-liners are technically accurate but so vague as to be nearly useless -- they describe the file's topic but never its mechanism, assumptions, or important edge cases.
