# Ward History Refactor Notes

## GOAL
Refactor ward State from bespoke counters to history-based pattern matching with custom CEL functions.

## Current State (read all files)

### Files to modify:
- `guard.go`: State struct, NewState, Update, ToMap, NewGuard (CEL env), CompileRule
- `guard_test.go`: TestNewState, TestStateUpdateCounters, TestStateUpdateEditsSinceCommit, TestEvaluateFlailingContext, TestEvaluateDenyVetoesContext, TestEvaluateContextAccumulates, TestStatePersistence
- `testdata/rules/flailing-reads.yaml`: uses `session.reads_since_bash >= 5`
- `testdata/rules/uncommitted-edits.yaml`: uses `session.edits_since_commit >= 2`
- `README.md`: CEL context table, example rules

### Key observations:
- State has: Phase, ToolCount, ToolCounts, LastTool, ReadsSinceBash, EditsSinceCommit, StartedAt
- Update() has counter increment logic and reset logic for Bash/commit
- ToMap() exposes all counters to CEL as int64
- 7 test rule files, 2 need updating (flailing-reads, uncommitted-edits)
- Tests that directly reference old fields: TestNewState, TestStateUpdateCounters, TestStateUpdateEditsSinceCommit, TestEvaluateFlailingContext, TestEvaluateDenyVetoesContext, TestEvaluateContextAccumulates, TestStatePersistence
- Need to add custom CEL functions `last()` and `since()` to cel.NewEnv in both NewGuard and CompileRule
- cel-go v0.27.0 is used

## Plan
1. Modify State struct + NewState + Update + ToMap + LoadState in guard.go
2. Add `last` and `since` CEL functions to NewGuard and CompileRule
3. Update testdata rules
4. Update tests
5. Update README
6. Run tests, commit atomically

## NEXT
Start implementing guard.go changes.
