# Semantic Foundations Review — 2026-03-23

## GOAL
Review the semantic-foundations-impl branch for semantic correctness, regression risk, plan-completion integrity, and test adequacy.

## Observations So Far

### Plan scope (7 rounds, R0–R6, all marked completed)
- R0: Plan + contract artifacts
- R1: Context-aware WorldModel.bind(), effective assumptions, context-aware conflict classification
- R2: Stance target validation, stance-type validation, FK enforcement, contradicts→rebuts rename
- R3: Measurement visibility via target_concept, graph-export claim ownership, algorithm conflict ownership
- R4: Draft/final boundary for plugin extraction
- R5: Sidecar invalidation covers contexts, forms, stances, semantic version marker
- R6: Hypothesis property tests for context semantics

### Final gate: 814 passed, 212 warnings (local), 50 passed (plugin repo)

### Changes reviewed (19 files, +1509 -57)

**Source files:**
1. `propstore/world/model.py` — _load_context_hierarchy(), claims_for() now includes target_concept, bind() wires hierarchy
2. `propstore/world/types.py` — added effective_assumptions to Environment
3. `propstore/world/bound.py` — effective_assumptions injected into binding_conds
4. `propstore/conflict_detector.py` — _classify_pair_context gets exclusion support, _append_context_classified_record helper, algorithm grouping by declared output concept, context_hierarchy threaded through detect_conflicts and detect_transitive_conflicts
5. `propstore/build_sidecar.py` — _content_hash covers contexts/forms/stances/version, FK enforcement (PRAGMA foreign_keys=ON), stance validation (type + target existence), context_hierarchy passed to _populate_conflicts
6. `propstore/validate_claims.py` — VALID_STANCE_TYPES imported from stances.py (single source), _validate_stances(), all_claim_ids collection
7. `propstore/graph_export.py` — _claim_concept_id helper uses concept_id || target_concept
8. `propstore/param_conflicts.py` — context tracking through transitive chains, _merge_contexts_for_derivation
9. `propstore/relate.py` — minor (stances import)
10. `propstore/z3_conditions.py` — string fallback for unknown concepts in CEL conditions

**Test files:**
11-19. Tests for all above, including Hypothesis property tests in test_contexts.py and test_build_sidecar.py

### Potential Issues Identified

1. **`_content_hash` signature change** — Now takes `repo=` and `context_files=` kwargs. Need to verify all callers pass these or defaults are safe.

2. **`_load_context_hierarchy` caching** — Uses `_context_hierarchy_loaded` flag. If the sidecar is rebuilt while WorldModel is open, the cached hierarchy could be stale. Low risk since WorldModel is typically short-lived.

3. **`claims_for()` column check via pragma** — `pragma_table_info('claim')` used to check if `target_concept` column exists. This is defensive but adds a query per call. Not cached.

4. **`_append_context_classified_record` repetition** — Called at 7 different conflict sites in conflict_detector.py. The pattern is consistent but the duplication is mechanical, not semantic.

5. **`z3_conditions.py` string fallback** — When concept info is None, falls back to z3.String comparison. This silently changes semantics for unknown concepts from "skip" to "string equality". Need to verify this doesn't produce false satisfiability results.

6. **`contradicts` → `rebuts` rename** — Applied in test fixtures but need to verify no production YAML files still use `contradicts`.

7. **`effective_assumptions` added to bound.py binding_conds** — Assumptions appended if not already present. Order-dependent? The append-if-not-present check uses `not in` on a list, which is O(n) but lists are small.

## Verified Items

1. **`contradicts` in knowledge/** — All 19 hits are in free-text `note` fields, NOT in `type:` fields. `grep 'type:\s*contradicts'` returns nothing. No build breakage.

2. **`VALID_STANCE_TYPES`** — Defined in `propstore/stances.py` as `frozenset({"rebuts", "undercuts", "undermines", "supports", "explains", "supersedes", "none"})`. Single source of truth, imported by both `validate_claims.py` and `build_sidecar.py`. Correct.

3. **`_content_hash` signature** — `repo=None` and `context_files=None` are keyword-only with safe defaults. Old callers that don't pass them get the pre-existing behavior (no forms/stances/contexts hashing). New callers in `build_sidecar()` pass both. Safe.

4. **`_SEMANTIC_INPUT_VERSION`** — Set to `"semantic-input-v1"`. Any schema/semantic change bumps this, forcing rebuild. Present and hashed.

5. **`are_excluded` symmetry** — Uses `frozenset([ctx_a, ctx_b])`, so direction doesn't matter. Exclusions stored one-directionally in sidecar (`context_a → context_b`), but `ContextHierarchy.__init__` also uses `frozenset`, so lookup is symmetric. Correct.

6. **`_classify_pair_context` and `_append_context_classified_record` logic** — Verified at all 7 call sites. Pattern is `if _append_...: continue` which correctly skips normal classification when context already classified as PHI_NODE, and falls through to normal classification when returns False. Semantically correct.

7. **`_merge_contexts_for_derivation`** (param_conflicts.py) — Sentinel `_INCOHERENT_CONTEXT = object()` used when transitive chain inputs come from excluded contexts. Prevents false transitive conflicts across incompatible belief spaces. Sound.

8. **`z3_conditions.py` string fallback** — When concept info is None (unknown concept), now falls back to z3.String comparison instead of returning None. This means unknown-concept conditions now participate in satisfiability checks (as unconstrained strings) rather than being silently ignored. This is MORE correct than before — previously, conditions mentioning unknown concepts were simply dropped, potentially declaring disjoint conditions as overlapping. The string fallback is conservative: two conditions on the same unknown concept with different values will correctly be detected as disjoint.

9. **`effective_assumptions` injection in bound.py** — Appends to `_binding_conds` list if not already present. O(n) `not in` check on small lists (assumptions are typically 0-5 items). No semantic issue.

10. **`claims_for()` pragma check** — Not cached, runs per call. Performance concern for hot paths but not a semantic bug. The defensive check ensures backward compatibility with older sidecars that lack `target_concept`.

## Remaining Concerns (for report)

### Important (not critical)
- **Exclusion loading in `_load_context_hierarchy`**: Only loads exclusions where `context_a` matches. If context Y excludes X, but only the row `(Y, X)` is stored, then when loading context X's excludes, the exclusion won't appear in X's `excludes` list. BUT this is fine because `ContextHierarchy.__init__` processes ALL loaded contexts and builds the frozenset-based `_exclusions` set. The load gathers excludes from whichever side declared them, and the frozenset handles symmetry. Verified correct.

- **`claims_for()` pragma per call** — Minor perf concern. Could cache result of column existence check.

## NEXT
- Run test suite to verify current state
- Write final report
