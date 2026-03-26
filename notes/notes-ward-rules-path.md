# Ward Rules Path Implementation Notes

## GOAL
Add WARD_RULES_PATH and WARD_FACTS_PATH env var support to ward.

## DONE
- Added `envPathDirs()` helper in main.go that splits env var by `os.PathListSeparator`
- Modified `loadGuard()` to load rules/facts in order: global -> env path dirs -> project
- Updated `cmdValidate()` to show labeled directories (global/WARD_RULES_PATH/project)
- Updated help text for validate command
- Added env var constants and help text in main usage
- Added 8 tests in guard_test.go covering:
  - Single dir, multiple dirs, nonexistent dir, empty env, unset env (for rules)
  - Single dir, nonexistent dir (for facts)
  - Integration test via loadGuard()
- All tests pass (go test returns exit 0)

## FILES
- C:/Users/Q/code/ward/main.go — all implementation changes
- C:/Users/Q/code/ward/guard_test.go — new tests

## NEXT
- Commit changes
- Write report to C:/Users/Q/code/propstore/reports/ward-rules-path.md
