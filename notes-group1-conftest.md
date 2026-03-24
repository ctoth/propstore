# Group 1: conftest.py extraction — Working Notes

## GOAL
Extract shared test helpers into tests/conftest.py, fix time.sleep in test_build_sidecar.py.

## Baseline
824 passed, 0 failures

## Design Decisions (final)

### `_create_schema(conn)` -> `create_argumentation_schema(conn)`
All 3 files identical. Safe to extract. Rename from `_create_schema` to `create_argumentation_schema`.

### `make_parameter_claim` — unified version
Two variants:
- **Variant A** (conflict_detector, z3_conditions): `(id, concept_id, value, unit="Hz", conditions=None)` — list-wraps value, adds conditions always, paper="test"
- **Variant B** (claim_notes, validate_claims): `(id, concept, value, unit, page=1, **kwargs)` — no list-wrap, no conditions default, paper="test_paper", supports kwargs

Unified design:
```python
def make_parameter_claim(id, concept_id, value, unit="Hz", *, conditions=None, page=1, paper="test", **kwargs):
    c = {"id": id, "type": "parameter", "concept": concept_id,
         "value": value if isinstance(value, list) else [value],
         "unit": unit, "provenance": {"paper": paper, "page": page}}
    if conditions is not None:
        c["conditions"] = conditions
    c.update(kwargs)
    return c
```

PROBLEM: variant B callers pass scalar values that go through YAML roundtrip. List-wrapping would change YAML content from `value: 440.0` to `value:\n- 440.0`. Validation doesn't care (just checks not-None), but this IS a behavior change in the data flowing through the system.

DECISION: Keep variant A local in test_conflict_detector.py and test_z3_conditions.py. Extract variant B as the shared version. This follows the prompt's escape hatch: "If any file's helper has a meaningful variation that the shared version doesn't cover, keep the local version."

Actually wait — re-reading prompt: "create a unified version that supports BOTH calling patterns." Let me try: I can NOT list-wrap by default and update the 2 variant-A callers that pass scalar values... but there are ~40+ call sites. Too much churn for "zero behavior change" refactoring.

FINAL DECISION: Extract variant B as shared (supports kwargs, page, paper). Keep variant A local in conflict_detector and z3_conditions (they need list-wrapping which is a real behavioral difference). Extract make_concept_registry from all 4 files.

### `make_concept_registry` — unified version
4 files. Differences: claim_notes has 2 concepts, others have 3. validate_claims has "whisper" in concept3.
Using the superset (3 concepts with whisper). Extra concepts don't affect any tests.

### `make_claim_file` — also duplicated
conflict_detector and z3_conditions both have identical `make_claim_file`. claim_notes has `make_claim_file_data` + `write_claim_file` (different pattern). validate_claims has `make_claim_file_data` + `write_claim_file` (same as claim_notes).

The prompt doesn't ask me to extract make_claim_file/make_claim_file_data. Only the 3 specified helpers.

### time.sleep fix
Lines 396, 407 in test_build_sidecar.py. Set sidecar mtime backward with os.utime instead of sleeping.

## FILES to modify
1. tests/conftest.py (CREATE) — create_argumentation_schema, make_parameter_claim (variant B), make_concept_registry
2. tests/test_argumentation_integration.py — remove _create_schema, import create_argumentation_schema
3. tests/test_bipolar_argumentation.py — remove _create_schema, import create_argumentation_schema
4. tests/test_render_time_filtering.py — remove _create_schema, import create_argumentation_schema
5. tests/test_claim_notes.py — remove make_parameter_claim + make_concept_registry, import from conftest
6. tests/test_validate_claims.py — remove make_parameter_claim + make_concept_registry, import from conftest
7. tests/test_conflict_detector.py — remove make_concept_registry only, keep make_parameter_claim local
8. tests/test_z3_conditions.py — remove make_concept_registry only, keep make_parameter_claim local
9. tests/test_build_sidecar.py — fix time.sleep

## NEXT
Create conftest.py and start updating files.
