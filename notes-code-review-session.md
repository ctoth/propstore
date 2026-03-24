# Code Review Fix Session — 2026-03-23

## GOAL
Fix all 14 code review issues via TDD, Foreman protocol.

## COMPLETE — ALL ISSUES RESOLVED

| Group | Commit | Tests | Description |
|-------|--------|-------|-------------|
| 1 | `61b8aee` | 824→824 | conftest.py extraction, time.sleep fix |
| 2 | `947b34b` | →832 | Narrow 4 bare except Exception (+8 tests) |
| 3 | `ac922bc` | →834 | claim_strength normalization (+2 tests) |
| 4 | `b6bb887` | →837 | Cache _has_table/conflicts, fix O(n^2) embed (+3 tests) |
| 5+6 | `6d4d5ed` | →839 | Make 5 methods public, fix CEGAR docstring (+2 tests) |
| 7 | `cdb8fbe` | →841 | 33-col INSERT → named dict (+2 tests) |
| 8 | `109e643` | →841 | repo: Repository typing, remove type: ignore |
| cleanup | `f0be41e` | →842 | parameters.py:213 exception + validate_claims typing |

**Total: 18 new tests, 824→842, 0 regressions, 9 commits**

## REMAINING (out of scope, for future consideration)
7 bare `except Exception` in files not covered by the original review:
- build_sidecar.py:250 (embedding snapshot — arguably justified)
- cli/helpers.py:57 (YAML parse)
- embed.py:226 (litellm API)
- param_conflicts.py:147 (SymPy eval)
- relate.py:154 (litellm API)
- sympy_generator.py:50 (parse_expr)
- world/value_resolver.py:162 (Z3 equivalence)
