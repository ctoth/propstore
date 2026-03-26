# CLI Phase 1: form show — unit conversions display

## GOAL
Add unit conversions display to `pks form show` command.

## OBSERVATIONS
- `form.py` show command at line 92-129: reads YAML, prints it, then shows algebra from sidecar
- `FormDefinition` has `conversions: dict[str, UnitConversion]` field
- `UnitConversion` dataclass: unit, type (multiplicative/affine/logarithmic), multiplier, offset, base, divisor, reference
- `load_form()` builds conversions from `common_alternatives` in YAML
- workspace fixture creates form YAMLs but WITHOUT common_alternatives — need to add them for tests
- frequency.yaml resource has kHz/MHz/GHz (multiplicative)
- temperature.yaml resource has C/F (affine)
- Tests invoke cli via `runner.invoke(cli, ["form", "show", "frequency"], obj={"start": workspace})`
  - Wait: need to check how obj is used. The show command uses `obj["repo"]` not `obj["start"]`

## DECISION POINT
The prompt says `obj={"start": workspace}` but the show command does `repo: Repository = obj["repo"]`. Need to check how the CLI sets up obj.

## NEXT
1. Check CLI setup to understand how obj flows
2. Write tests with proper fixture forms that have common_alternatives
3. RED phase
4. GREEN phase
