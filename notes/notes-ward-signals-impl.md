# Ward Signals Implementation Session

## GOAL
Implement signals feature for ward per `C:/Users/Q/code/ward/docs/signals-design.md`.

## OBSERVATIONS

### Codebase Structure (ward repo)
- Single Go package (`package main`) in root
- Key files: `guard.go` (State, Rule, Guard, evaluation), `main.go` (CLI commands), `parse.go` (shell parsing), `adapters.go` (agent detection)
- Tests: `guard_test.go`, `adapters_test.go`, `parse_test.go`
- Testdata: `testdata/rules/`, `testdata/facts/`, `testdata/signals/` (already has persistent-signal.yaml and no-force-push-with-signal.yaml)

### Current State struct (guard.go:272)
- `Phase string`, `History []string`, `StartedAt time.Time`
- No `Signals` field yet

### Current EvaluateVerbose signature (guard.go:401)
- Returns `(*Result, error)` — needs to return `(*Result, map[string]bool, error)` per design

### Current Evaluate signature (guard.go:396)
- Wrapper around EvaluateVerbose, returns `(*Result, error)`

### CLI commands (main.go)
- `eval`, `set`, `validate` — need to add `allow` and `revoke`

### Existing testdata already prepared
- `testdata/rules/no-force-push-with-signal.yaml` — rule using `!session.signals.contains("force-push")`
- `testdata/signals/persistent-signal.yaml` — `one_time_use: false`

### Test count
- `TestLoadRulesFromDir` expects 7 rules (currently 7 YAML files in testdata/rules, but no-force-push-with-signal.yaml is 8th — wait, need to verify count)
- Actually: 8 files listed. Test says 7. Need to check if test was already updated or if the signal rule was added before updating the test count.

## IMPLEMENTATION ORDER (from design doc section 10)
1. State changes: Add `Signals` to `State`, update `NewState`, `LoadState`, `ToMap`
2. `ward allow` / `ward revoke`: CLI commands, signal name validation
3. Signal definition loading: YAML schema, file loading, directory scanning
4. Consumption logic: `signalRefRe`, `ConsumeSignals`, integration into `cmdEval` (EvaluateVerbose signature change)
5. Validate updates: Add signal definition scanning to `cmdValidate`
6. Update help text
7. Tests

## DONE
- Baseline tests: 1 failure (TestLoadRulesFromDir expected 7, got 8 due to pre-existing signal rule). Fixed count to 8.
- Step 1 (State changes): Signal struct, State.Signals field, NewState, LoadState, ToMap, ConsumeSignals — all done in guard.go
- Step 4 partial (Consumption logic): signalRefRe regex, EvaluateVerbose signature change to return matchedSignals, signal extraction in eval loop — done in guard.go
- Evaluate() signature also updated to match

## IN PROGRESS
- Need to add: SignalDef, LoadSignalDef, LoadSignalDefsFromDir, validSignalName, signalsReferencedByRules to guard.go
- Need to add: cmdAllow, cmdRevoke, resolveSignalDef, help text, validate updates to main.go
- Need to update: all callers of Evaluate/EvaluateVerbose (main.go cmdEval, guard_test.go tests)
- Need to add: all tests from design doc section 9

## BLOCKER
- None. In the middle of implementation.

## NEXT
1. Add SignalDef types and loading functions to guard.go
2. Update main.go (cmdAllow, cmdRevoke, cmdEval consumption, cmdValidate, help)
3. Fix all Evaluate() callers in tests
4. Add signal-specific tests
5. Compile and test
