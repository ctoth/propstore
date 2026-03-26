# Fix 5B: Resolution Tie-Breaking — Session Notes

## GOAL
Fix nondeterministic tie-breaking in `_resolve_recency` and `_resolve_sample_size` — when claims tie, return "conflicted" with all tied claims instead of arbitrary winner.

## OBSERVATIONS
- `propstore/world/resolution.py` lines 22-54: both `_resolve_recency` and `_resolve_sample_size` use strict `>` — first-encountered wins ties
- Return type is `tuple[str | None, str | None]` — (winner_id, reason). Returning `None` for winner_id causes `resolve()` to return "conflicted" status (line 306-310)
- `ResolvedResult` has `claims: list[dict]` which already carries all active claims when status is "conflicted"
- Existing tests at lines 1087-1118 in `test_world_model.py` test the happy path (unique winners)
- The `resolve()` wrapper at line 306 already handles `winner_id is None` → conflicted. So the fix just needs the helpers to return `(None, reason)` on ties.

## PLAN (TDD)
1. RED: Add tests calling `_resolve_recency` and `_resolve_sample_size` directly with tied claims
2. GREEN: Fix both functions to detect ties and return None
3. VERIFY: Full test suite
4. COMMIT

## FILES
- `propstore/world/resolution.py` — the fix target
- `tests/test_world_model.py` — test target
- `propstore/world/types.py` — ResolvedResult dataclass (read-only reference)
