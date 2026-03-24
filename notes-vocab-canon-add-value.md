# Notes: vocab-canon-add-value task

## Goal
Add `pks concept add-value` command (TDD) - extends category concept value sets.

## What I know
- test_cli.py has 1127 lines, ends with TestConceptCategories class
- workspace fixture creates `task` (category, values=["speech","singing"], extensible=True) and `fundamental_frequency` (frequency form)
- `find_concept()` in helpers.py takes (id_or_name, cdir) and returns Path|None
- `load_concept_file()` returns dict, `write_concept_file()` writes dict to yaml
- The `alias` command (line 210) is the pattern: find_concept -> load -> modify -> write
- CEL checker already handles category values with extensible/non-extensible distinction
- `build_cel_registry` and `check_cel_expression` already imported in test_cel_checker.py
- test_cel_checker.py ends at line 527

## Plan
1. Add TestConceptAddValue class with 4 tests to test_cli.py (after line 1128)
2. Add test_category_from_cli_round_trip to test_cel_checker.py (after line 527)
3. Run RED tests
4. Implement add-value command in concept.py
5. Run GREEN tests + full suite
6. Commit

## Key observation
- The `alias` command uses `find_concept(concept_id, repo.concepts_dir)` which returns a Path
- But the prompt's implementation uses `load_concepts` + `find_concept(concepts, concept_name)` differently
- I need to follow the EXISTING pattern: find_concept returns Path, then load_concept_file
