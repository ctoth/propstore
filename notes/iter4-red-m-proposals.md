# Iter4 Red M — Proposals Infrastructure Tests
## Date: 2026-03-25

## GOAL
Write 3 failing tests for proposals infrastructure (F17, F18): write_stance_file target path, write_yaml_file in data_utils, promote CLI command.

## OBSERVATIONS
- `relate.py:468-489`: `write_stance_file()` takes `stances_dir: Path` as arg, writes to it directly. The caller (cli/claim.py) passes `knowledge/stances/`. The function itself doesn't hardcode the path — but it currently writes to whatever dir is passed. Test should verify output contains `proposals/stances/`.
- `relate.py:15`: imports `write_yaml_file` from `propstore.cli.helpers` (layer violation)
- `propstore.data_utils` does not exist yet — import will fail
- `promote` command is not registered in `propstore/cli/__init__.py` — only: concept, context, claim, form, validate, build, query, export_aliases, import_papers, init, world, worldline
- Existing test files exist at all 3 paths — need to APPEND new tests

## FILES
- `propstore/relate.py` — write_stance_file at line 468
- `propstore/cli/helpers.py` — write_yaml_file at line 160
- `propstore/cli/__init__.py` — cli.add_command registrations
- `tests/test_relate_opinions.py` — existing tests (11 tests, 505 lines)
- `tests/test_helpers.py` — existing tests (7 tests, 113 lines)
- `tests/test_cli.py` — existing tests (large file)

## NEXT
Write the 3 failing tests, run them, commit.
