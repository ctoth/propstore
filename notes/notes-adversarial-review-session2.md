# Adversarial Review — semantic-foundations-impl branch

Session date: 2026-03-23

## GOAL
Review implementation for bugs, regressions, semantic mismatches with plan, missing tests, compatibility risks.

## TEST STATE
- 1 FAILING: `test_contexts.py::TestContextAwareConflicts::test_unrelated_context_conflicts_always_exit_as_context_phi_node`
- 360 passed, 212 warnings
- Plugin: 50 passed

## ROOT CAUSE OF FAILURE
`assume(value_a != value_b)` with Hypothesis floats. Falsifying example: `value_a=1.0, value_b=1.0000000000000002`. Python `!=` is True but `_values_compatible` treats them as equal (tolerance 1e-9). No conflict record produced → assertion `len(records) == 1` fails.

## CRITICAL FINDINGS

### C1: Failing Hypothesis test (test_contexts.py:919)
Fix: `assume(abs(value_a - value_b) > 1e-9)` or use integer strategy.

### C2: Two callers of detect_conflicts() missing context_hierarchy
- `propstore/argumentation.py:268` — no context_hierarchy passed
- `propstore/cli/claim.py:130` — no context_hierarchy passed
Both silently revert to pre-R1 behavior (no context-aware classification). The argumentation.py path already filters on conflict_types excluding phi-nodes (line 271), so functionally safe but semantically incomplete. The CLI path reports all conflicts without context awareness.

## IMPORTANT FINDINGS

### I1: `_load_context_hierarchy` typed as `object | None` everywhere
No type checker can verify `.ancestors()`, `.effective_assumptions()`, `.is_visible()` calls. All accessed via `type: ignore[union-attr]`. Should be `ContextHierarchy | None`.

### I2: `claims_for()` probes schema on every call (model.py:191-192)
`pragma_table_info` query runs every time. Should be cached.

### I3: Copy-pasted context phi-node block (6x in conflict_detector.py)
Same 10-line pattern (classify, check, append, continue) at lines ~234-250, ~288-304, ~328-344, ~375-391, ~435-451, ~510-527. Should be a helper function.

### I4: Missing contract proof obligations
- Measurement visibility invariant under claim ordering — no permutation test
- Algorithm attribution invariant under variable ordering — no property test

### I5: z3_conditions.py string fallback (line 183-190)
When concept is not in registry, falls back to z3.String comparison. This is a reasonable defensive change but creates a different Z3 sort from the enum path, meaning disjointness checks between string-based and enum-based conditions for the same concept name could behave inconsistently.

## COMPATIBILITY OBSERVATIONS (NO ISSUES)
- VALID_STANCE_TYPES migration from relate.py to stances.py: complete, no stale imports
- No production data uses `contradicts` stance type
- WorldModel.bind() callers all use keyword args, safe
- Plugin tests pass (50 passed)

## DONE
- Review delivered
