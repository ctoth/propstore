# Group 4: Performance Fixes Session

## GOAL
Fix 4 performance issues: uncached _has_table, uncached conflicts, O(n^2) embedding scan, O(n*m) list conversion.

## BASELINE
834 passed, 212 warnings in 40.68s

## DONE
- Read all source files: model.py, bound.py, embed.py, relate.py, test_world_model.py
- Understood code structure and fixtures

## OBSERVATIONS

### 4a: _has_table cache (model.py)
- `_has_table` at line 319 queries sqlite_master every call
- `__init__` at line 40, needs `_table_cache` dict added
- Called many times: claims_for, stats, all_parameterizations, etc.

### 4b: conflicts cache (bound.py)
- `BoundWorld.conflicts()` at line 278 recomputes every call
- `__init__` at line 106, needs `_conflicts_cache` dict added
- TestBoundConflicts at line 653 shows how to set up: `world.bind(task="speech")` then `bound.conflicts("concept1")`
- `world` fixture at line 393 builds sidecar from concept_dir

### 4c: O(n^2) embedded_at scan (embed.py)
- Lines 634-635: `next((s["embedded_at"] for s in snapshot.claim_statuses if ...))` inside restore loop
- Lines 677-678: same pattern for concept_statuses
- Need to pre-build lookup dicts before the loops

### 4d: O(n*m) list conversion (relate.py)
- Lines 302-306: `first_pass_results = list(first_pass_results)` called INSIDE the loop for each second_task
- `first_pass_results` starts as a tuple from `asyncio.gather`, gets converted to list repeatedly
- Fix: convert once before the loop

## FILES
- `propstore/world/model.py` - _has_table cache
- `propstore/world/bound.py` - conflicts cache
- `propstore/embed.py` - O(n^2) scan fix
- `propstore/relate.py` - O(n*m) list fix
- `tests/test_world_model.py` - new tests

## PROGRESS
- [x] RED tests added for 4a: test_has_table_caches FAILED as expected, test_has_table_consistent passed
- [x] RED test added for 4b: test_conflicts_cached passed (equality check, cache is perf optimization)
- [x] GREEN fix 4a: Added _table_cache dict to __init__, cache check in _has_table
- [x] GREEN fix 4b: Added _conflicts_cache dict to __init__, cache check/store in conflicts()
- [x] GREEN fix 4c: Pre-built claim_at_lookup and concept_at_lookup dicts in restore_embeddings
- [ ] GREEN fix 4d: Need to fix list() inside loop in relate.py
- [ ] Run full suite
- [ ] Commit
- [ ] Write report

## NEXT
1. Fix 4d in relate.py (lines 302-306)
2. Run full test suite
3. Commit and write report
