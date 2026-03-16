# D2: Form Schema and Explicit Dimensionless Field

## Summary

Created a JSON Schema for form YAML files and replaced the fragile `is_dimensionless` heuristic in `form_utils.py` with an explicit `dimensionless` boolean field read from each form file.

## Changes

### 1. Form YAML files -- added `dimensionless` field

All 11 form files in `forms/` now carry an explicit `dimensionless: true|false` field:

| Form | dimensionless |
|---|---|
| amplitude_ratio | true |
| dimensionless_compound | true |
| duration_ratio | true |
| level | true |
| category | false |
| flow | false |
| flow_derivative | false |
| frequency | false |
| pressure | false |
| structural | false |
| time | false |

### 2. JSON Schema (`schema/generated/form.schema.json`)

New file. Validates:
- `name` (required, lowercase snake_case pattern)
- `dimensionless` (required, boolean)
- `base`, `unit_symbol`, `qudt`, `parameters`, `common_alternatives`, `note` (optional, typed)
- `common_alternatives` items validated with required `unit`, `type`, `multiplier`
- `additionalProperties: false` catches typos

### 3. `compiler/form_utils.py`

- Added `import json` and `import jsonschema`
- `load_form()` now reads the explicit `dimensionless` field from YAML data. Falls back to the old heuristic if the field is absent (backward compatibility for any form files not yet updated).
- Added `validate_form_files(forms_dir)` function that loads each `forms/*.yaml`, validates against the JSON Schema, and cross-checks that `name` matches the filename stem.

### 4. `compiler/cli/compiler_cmds.py`

- `validate` command: runs `validate_form_files()` before concept validation; form errors count toward the total.
- `build` command: runs `validate_form_files()` as Step 0; aborts build on any form schema error.

### 5. `tests/test_cli.py`

- Updated the `workspace` fixture to include `dimensionless` in generated form YAML files so the schema validation passes in test environments.

## Files modified

- `forms/amplitude_ratio.yaml`
- `forms/category.yaml`
- `forms/dimensionless_compound.yaml`
- `forms/duration_ratio.yaml`
- `forms/flow.yaml`
- `forms/flow_derivative.yaml`
- `forms/frequency.yaml`
- `forms/level.yaml`
- `forms/pressure.yaml`
- `forms/structural.yaml`
- `forms/time.yaml`
- `schema/generated/form.schema.json` (new)
- `compiler/form_utils.py`
- `compiler/cli/compiler_cmds.py`
- `tests/test_cli.py`

## Test results

All 321 tests pass.
