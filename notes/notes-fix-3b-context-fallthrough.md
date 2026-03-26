# Fix 3B: CONTEXT_PHI_NODE Fallthrough

## GOAL
Fix bug where unrelated contexts fallthrough to CONTEXT_PHI_NODE, suppressing real conflicts.

## OBSERVATIONS
- Bug is at line 31 of `propstore/conflict_detector/context.py`: `return ConflictClass.CONTEXT_PHI_NODE`
- This fallthrough catches any two contexts that are not excluded and not visible to each other
- Correct behavior: return `None` so condition analysis handles it
- Caller `_append_context_classified_record` already handles `None` (returns `False`, meaning "no context classification, proceed normally")
- Existing test at line 822 `test_transitive_conflicts_in_unrelated_contexts_exit_as_context_phi_node` ASSERTS the buggy behavior (expects CONTEXT_PHI_NODE for unrelated contexts)
- That test will need updating when the fix lands

## FILES
- `propstore/conflict_detector/context.py` — the bug (line 31)
- `propstore/conflict_detector/models.py` — ConflictClass enum
- `tests/test_conflict_detector.py` — existing tests, add new test here
- `propstore/validate_contexts.py` — ContextHierarchy, LoadedContext

## PLAN (TDD)
1. RED: Add test for `detect_conflicts` (not transitive) with unrelated contexts, assert NOT CONTEXT_PHI_NODE
2. GREEN: Change line 31 from `return ConflictClass.CONTEXT_PHI_NODE` to `return None`
3. Update existing test at line 822 that asserts the buggy behavior
4. Run full suite, verify green
5. Commit

## DONE
- RED: Wrote failing test `test_unrelated_contexts_do_not_suppress_direct_conflicts` — confirmed fails with CONTEXT_PHI_NODE
- GREEN: Changed fallthrough in context.py line 31 from `return ConflictClass.CONTEXT_PHI_NODE` to `return None`

## PROGRESS
- Full suite: 987 passed, 3 failed — all failures are tests asserting old buggy behavior
- Fixed transitive test in test_conflict_detector.py (now expects PARAM_CONFLICT)
- Fixed 1 of 3 tests in test_contexts.py (unit test now expects None)
- Still need to fix 2 integration tests in test_contexts.py (lines 836, 883)

## NEXT
Fix remaining 2 tests in test_contexts.py, run full suite, commit
