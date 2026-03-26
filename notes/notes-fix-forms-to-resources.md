# Fix forms-to-resources session notes

## GOAL
Move `forms/` from repo root into `propstore/_resources/forms/` so they ship with pip install.

## OBSERVATIONS

### Files that reference repo-root forms (NEED UPDATING):
1. `propstore/cli/init.py:25` — `Path(__file__).resolve().parents[2] / "forms"` — THE BUG
2. `scripts/write_physics_forms.py:5` — `Path(__file__).parent.parent / "forms"` — dev script
3. `tests/test_form_utils.py:20` — `Path(__file__).parent.parent / "forms"` — test fixture
4. `tests/test_form_dimensions.py:45` — `Path(__file__).parent.parent / "forms"` — test fixture

### Files using `repo.forms_dir` (user's project forms — DO NOT TOUCH):
- All build_sidecar.py, validate.py, validate_claims.py, cli/form.py, cli/claim.py, cli/concept.py, cli/compiler_cmds.py references
- All test files that create tmp_path forms dirs

### Existing resource pattern:
- `propstore/resources.py` has `_get_resource_root()` and `load_resource_text()`
- Currently serves `physgen_units.json` from `propstore/_resources/`

## PLAN
1. `git mv forms propstore/_resources/forms`
2. Update init.py line 25 to use `_resources` path
3. Update scripts/write_physics_forms.py line 5
4. Update tests/test_form_utils.py line 20
5. Update tests/test_form_dimensions.py line 45
6. Check pyproject.toml for package-data
7. Run tests
8. Commit

## STATUS
Starting execution
