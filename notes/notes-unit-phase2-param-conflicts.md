# Unit Phase 2: Wire normalize_to_si into param_conflicts

## GOAL
Wire unit normalization into param_conflicts.py so claim values are normalized to SI before comparison.

## OBSERVATIONS

### param_conflicts.py structure
- `_detect_param_conflicts()` extracts intervals from claims via `_extract_interval(claim)` or `_parse_numeric_values(claim.get("value", []))`
- Claims are dicts with keys: id, value, conditions, and potentially "unit"
- No current unit handling — values compared as-is
- `detect_transitive_conflicts()` similarly extracts scalar values without unit normalization

### form_utils.py (Phase 1 complete)
- `normalize_to_si(value, unit, form)` exists and works
- `FormDefinition` has `conversions: dict[str, UnitConversion]`
- `UnitConversion` supports multiplicative, affine, logarithmic
- `load_form()` builds conversions from `common_alternatives` in YAML

### test_param_conflicts.py
- One existing test: `test_detect_param_conflicts_handles_equality_parameterizations_without_warning`
- Uses `by_concept` dict with claims, `concept_registry` dict, `LoadedClaimFile`
- Claims have `value` as list (e.g. `[10.0]`), `id`, `conditions`

### Plan per prompt
- Need to add `forms: dict[str, FormDefinition] | None = None` param to both functions
- After extracting intervals, normalize using `normalize_to_si()` if forms + unit info available
- Tests need: frequency FormDefinition with kHz conversion (multiplier=1000)

## DONE
- Wrote 3 failing tests in test_param_conflicts.py (RED confirmed - all 3 fail with TypeError)
- Added `_normalize_claim_value()` helper to param_conflicts.py
- Added `forms` kwarg to `_detect_param_conflicts()` signature
- Wired normalization into `_detect_param_conflicts()` value extraction (both interval and legacy paths)

## STATUS: COMPLETE
- Commit: 043de92
- All 4 param_conflicts tests pass
- Full suite: 1042 passed, 1 pre-existing failure
- Report written to reports/unit-phase2-param-conflicts-report.md
