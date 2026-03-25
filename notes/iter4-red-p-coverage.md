# Iter4 Red Phase P — Coverage Gap Tests
**Date:** 2026-03-25

## GOAL
Write two tests: (1) HypotheticalWorld + ATMS backend crash (F30), (2) build_praf() coverage (F31).

## OBSERVATIONS

### Test 1: HypotheticalWorld + ATMS (F30)
- `HypotheticalWorld` in `propstore/world/hypothetical.py` has NO `atms_engine()` method
- `_resolve_atms_support()` in `propstore/world/resolution.py` line 273 does `getattr(view, "atms_engine", None)` and raises `NotImplementedError` if not callable
- So it won't be `AttributeError` — it will be `NotImplementedError("ATMS backend requires a bound world with an ATMS engine")`
- Resolution path: `resolved_value()` → `resolve()` → when `reasoning_backend == ReasoningBackend.ATMS`, calls `_resolve_atms_support()` which checks for `atms_engine`
- `HypotheticalWorld.resolved_value()` passes `self._base._policy` — need to check if policy can be ATMS
- Need to import `ReasoningBackend` from `propstore.world.types`

### Test 2: build_praf() (F31)
- `build_praf()` lives in `propstore/argumentation.py` line 171-225
- Takes `store: ArtifactStore` and `active_claim_ids: set[str]`
- Returns `ProbabilisticAF`
- Existing `test_praf_integration.py` has `_MockStore` class that could be reused/adapted
- `build_praf` calls `build_argumentation_framework()`, `store.claims_by_ids()`, `store.stances_between()`
- The mock needs: `claims_by_ids()`, `stances_between()`, `has_table()`, `claims_for()`, `get_concept()`

### Existing test patterns
- `tests/test_world_model.py` uses real sidecar DB via `build_sidecar` fixture
- `tests/test_praf_integration.py` uses `_MockStore` and `_MockBeliefSpace` mocks
- World model tests import from `propstore.world`

## NEXT
- Write Test 1 in `tests/test_world_model.py` — create HypotheticalWorld, attempt ATMS resolution, expect NotImplementedError
- Write Test 2 in `tests/test_praf_integration.py` — call `build_praf()` with mock store, verify ProbabilisticAF output
