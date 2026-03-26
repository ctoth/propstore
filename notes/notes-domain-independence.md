# Domain Independence Implementation Notes

Session: 2026-03-17

## Baseline
- 529 passed, 1 failed (hypothesis deadline flaky), 188 warnings
- Branch: modularize-world-model

## Plan Phases
1. kind field + dedup (_FORM_TO_KIND removal)
2. condition labels + init + cosmetics
3. measure types
4. domain units

## All Phases Complete

### Phase 1 — kind field + dedup
- [x] form.schema.json: added `kind` enum
- [x] form_utils.py: read `kind` from YAML, fallback to name-based
- [x] form_utils.py: removed hardcoded `form_name in ("level", "dimensionless_compound")`
- [x] world/model.py: deleted _FORM_TO_KIND, uses sidecar kind_type directly
- [x] conflict_detector.py: deleted _FORM_TO_KIND, uses form_utils

### Phase 2 — condition labels + init + cosmetics
- [x] description_generator.py: replaced _CONDITION_LABELS with generic formatting
- [x] cli/init.py: reduced _FALLBACK_FORMS to category/boolean/structural
- [x] cli/concept.py: updated help text
- [x] cli/compiler_cmds.py: replaced task=speech with domain=example
- [x] unit_dimensions.py: updated docstring
- [x] Updated tests

### Phase 3 — measure types
- [x] validate_claims.py: deleted _VALID_MEASURE_TYPES, measure is free string
- [x] claim.linkml.yaml: marked MeasureType as non-binding
- [x] claim.schema.json: measure field uses string type

### Phase 4 — domain units
- [x] FormDefinition.extra_units field added
- [x] load_form() reads extra_units from YAML
- [x] _SPEECH_UNITS split into _COMMON_UNITS + _LEGACY_DOMAIN_UNITS
- [x] register_form_units() function added
- [x] LEVEL_UNITS removed, dimensionless validation uses form's extra_units
- [x] form.schema.json: added extra_units array
