# CLI Phase 3: pks claim show — Session Notes

## GOAL
Add `pks claim show <claim_id>` command with TDD (red-green-refactor).

## OBSERVATIONS SO FAR

### Existing structure
- `propstore/cli/claim.py` — has `validate`, `validate-file`, `conflicts`, `compare`, `embed`, `similar`, `relate` commands. No `show` yet.
- `tests/test_cli.py` — 1272 lines, uses `workspace` fixture (tmp_path with knowledge/concepts/forms). No `freq_workspace` fixture.
- `tests/conftest.py` — has `create_argumentation_schema`, `make_parameter_claim`, `make_concept_registry` helpers (not pytest fixtures).

### Claim table schema (from build_sidecar.py:786)
Key columns: id, type, concept_id, value, lower_bound, upper_bound, uncertainty, uncertainty_type, sample_size, unit, conditions_cel, statement, source_paper, provenance_page, value_si, lower_bound_si, upper_bound_si, context_id

### Concept table schema (from build_sidecar.py:343)
Has `unit_symbol` column — this is the canonical unit for the form.

### WorldModel
- `WorldModel(repo)` opens sidecar sqlite, provides `get_claim(id)` returning dict or None.
- `get_concept(concept_id)` returns dict with unit_symbol field.

### CLI obj pattern
- `ctx.obj["repo"]` is a Repository found by `Repository.find(start)`
- Repository.sidecar_path = `root / "sidecar" / "propstore.sqlite"`
- Repository.find walks up looking for knowledge/ dir with concepts/ subdir

### Claim YAML format
- These are observation/statement claims (no value/unit fields typically)
- For parameter claims I need to create my own fixture data

## PLAN
1. Create `freq_workspace` fixture in test_cli.py that:
   - Reuses existing `workspace` fixture setup
   - Adds a claim YAML with a parameter claim (value=0.2, unit=kHz, concept=concept1/frequency)
   - Runs `pks build` to create sidecar
   - The sidecar will have value_si computed by build (0.2 kHz = 200 Hz)
2. Write TestClaimShow tests — expect "No such command 'show'" failure
3. Implement `claim show` command
4. Run full suite

## DONE
1. RED: Wrote 3 tests in TestClaimShow class + freq_workspace fixture in tests/test_cli.py
   - test_claim_show_exists: confirms command exists, shows claim ID
   - test_claim_show_displays_si_values: confirms 0.2, 200, kHz in output
   - test_claim_show_not_found: confirms error on missing claim
   - All 3 failed with "No such command 'show'" (2 real failures, 1 vacuous pass)
2. GREEN: Implemented `claim show` command in propstore/cli/claim.py
   - Opens WorldModel, fetches claim by ID
   - Shows all fields as key-value pairs
   - SI values shown only when they differ from raw values
   - Gets canonical_unit from concept's unit_symbol
   - All 3 tests pass

## ISSUE FOUND
- There was already a `freq_workspace` fixture at line 117 that builds via `pks build` with claim ID `freq_claim1`
- My initial edit added a DUPLICATE fixture at the bottom — this shadowed the original
- Fixed: removed my duplicate, updated TestClaimShow to use `freq_claim1` and rely on the existing fixture
- The existing fixture uses `workspace` base which does monkeypatch.chdir, so no `-C` flag needed

## PRE-EXISTING FAILURES (not mine)
- test_atms_cli_surfaces_interventions_and_next_queries: "No such command 'atms-interventions'" — unimplemented command
- TestWorldQuerySIValues::test_world_bind_shows_si_value: JSONDecodeError — pre-existing, uses freq_workspace

## FILES CHANGED
- `propstore/cli/claim.py` — added `show` command
- `tests/test_cli.py` — added TestClaimShow class (3 tests)

## NEXT
Run tests to confirm green, then commit.
