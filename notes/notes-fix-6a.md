# Fix 6A: Form Algebra Filter

## GOAL
Stop build-time filtering of form algebra entries. Store all entries with `dim_verified` flag instead of dropping.

## DONE
- RED: Added TestFormAlgebraDimVerified with 2 tests — both fail as expected
- GREEN: Implementation complete:
  - Added `dim_verified INTEGER NOT NULL DEFAULT 1` to form_algebra CREATE TABLE
  - Replaced `continue` branches with `dim_verified = 0` — entries stored, not dropped
  - Replaced bare `except Exception: continue` with specific `except (KeyError, ValueError)` and `except ImportError`
  - Updated INSERT to include dim_verified column
  - bridgman exports DimensionalError but it inherits from ValueError, so catching ValueError covers it

## NEXT
- Run tests to verify GREEN
- Run full suite
- Commit

## FILES
- `propstore/build_sidecar.py` — the fix target
- `tests/test_build_sidecar.py` — test target
