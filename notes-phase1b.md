# Phase 1b: Consolidate _build_cel_registry

## Goal
Merge three copies of CEL registry-building logic into one function in cel_checker.py.

## Observations

### Three implementations:
1. **validate.py:62-90** `_build_cel_registry(concepts: list[LoadedConcept])` — iterates LoadedConcept objects, gets `c.data` dict, uses `data.get("id")` for cid
2. **validate_claims.py:64-92** `_build_cel_registry_from_concepts(concept_registry: dict[str, dict])` — iterates dict items, uses key as cid. Skips entries with no name or kind_type is None.
3. **conflict_detector.py:246-266** `_build_cel_registry(concept_registry: dict[str, dict])` — iterates dict items, uses key as concept_id. DIFFERS: uses `canonical or concept_id` fallback, defaults kind to QUANTITY instead of skipping, and doesn't gate on `kind_type is None`.

### Key differences in conflict_detector version:
- `canonical = data.get("canonical_name", concept_id)` — falls back to concept_id if no canonical_name
- `kind = kind_type_from_form_name(form) or KindType.QUANTITY` — defaults to QUANTITY instead of skipping
- Doesn't check `if not name or kind_type is None: continue`
- Gets form_params without `or {}` fallback but checks `isinstance(form_params, dict)`

### Call sites:
- validate.py:134 — `cel_registry = _build_cel_registry(concepts)` where concepts is list[LoadedConcept]
- validate_claims.py:146 — `cel_registry = _build_cel_registry_from_concepts(concept_registry)`
- conflict_detector.py:707 — `cel_registry = _build_cel_registry(concept_registry)`

### Imports already present:
- validate.py: imports ConceptInfo, KindType from cel_checker; kind_type_from_form_name from form_utils
- validate_claims.py: imports ConceptInfo, KindType from cel_checker; kind_type_from_form_name from form_utils
- conflict_detector.py: imports ConceptInfo, KindType from cel_checker; kind_type_from_form_name from form_utils

### Line counts before:
- validate.py: 396
- validate_claims.py: 577
- conflict_detector.py: 1209
- cel_checker.py: 550

## Plan
1. Add `build_cel_registry(concept_registry: dict[str, dict]) -> dict[str, ConceptInfo]` to cel_checker.py
   - Use the validate.py/validate_claims.py behavior (skip if no name or kind_type is None) as the canonical version
   - The conflict_detector version is slightly different — need to decide. Will match the majority (skip entries).
2. Write test in test_cel_checker.py
3. Update all three call sites
4. Remove old implementations
5. Run tests

## Progress
- [x] Added `build_cel_registry()` and `build_cel_registry_from_loaded()` to cel_checker.py
- [x] Wrote 7 tests in test_cel_checker.py — all pass
- [x] Updated validate.py: removed old function, updated call site and imports
- [x] Updated validate_claims.py: added build_cel_registry import
- [ ] Remove old function from validate_claims.py, update call site
- [ ] Update conflict_detector.py
- [ ] Run full test suite
- [ ] Commit

## Note: kind_type_from_form_name usage
- validate.py: still used on line 276 (outside removed function) — kept import
- validate_claims.py: only used inside the old function being removed — can remove from imports

## Line counts
| File | Before | After | Delta |
|------|--------|-------|-------|
| validate.py | 396 | 368 | -28 |
| validate_claims.py | 577 | 548 | -29 |
| conflict_detector.py | 1209 | 1185 | -24 |
| cel_checker.py | 550 | 604 | +54 |
| **Total** | **2732** | **2705** | **-27** |

Net: removed 81 lines of duplicated code, added 54 lines (consolidated function + wrapper). Net -27 lines.

## Test results
- 219/219 pass, 1 deselected (pre-existing failure: TestEmptyClaimFiles::test_missing_claims_key_errors — unrelated to CEL registry, it's a schema validation test)

## Status: Ready to commit and write report
