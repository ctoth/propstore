# Ward Facts Refactor Notes

## Goal
Refactor ward to drop config.yaml, make facts individual files, build and install.

## Current State
- On branch `facts-per-file` in C:/Users/Q/code/ward
- Read all source files: guard.go, main.go, guard_test.go, adapters.go, adapters_test.go, README.md
- Read testdata/config.yaml — has 2 facts: git_branch, has_pyproject

## What needs to change

### guard.go
- Remove `Config` struct
- Remove `LoadConfig`, `MergeConfigs` functions
- Add `LoadFact(path)` and `LoadFactsFromDir(dir)` functions
- Add `mergeFacts(global, project map[string]Fact) map[string]Fact`
- Change `NewGuard` signature: `NewGuard(facts map[string]Fact, rules []Rule)`
- Change `Guard` struct: replace `Config Config` with `Facts map[string]Fact`
- Update `Evaluate` to use `guard.Facts` instead of `guard.Config.Facts`
- Hardcode default phase "planning" in `NewState` (already does this as default)

### main.go
- Remove `configPaths()` function
- Add `factsDirs()` function
- Rewrite `loadGuard()` to load facts from dirs instead of config
- Update `cmdEval` to use hardcoded "planning" instead of `guard.Config.DefaultPhase`
- Update `cmdValidate` to also validate facts
- Update help text to remove config.yaml references

### guard_test.go
- Remove `TestLoadConfig`, `TestLoadConfigMissing`, `TestMergeConfigs`
- Add `TestLoadFact`, `TestLoadFactsFromDir`, `TestMergeFacts`
- Update `loadTestGuard` to load from testdata/facts/
- Update tests that construct `Config{}` directly to use `map[string]Fact{}`

### testdata
- Create testdata/facts/ directory with individual fact files
- Remove testdata/config.yaml

### README.md
- Replace config.yaml section with facts section

## Done So Far
- guard.go: Removed Config struct, LoadConfig, MergeConfigs. Added LoadFact, LoadFactsFromDir, MergeFacts. Updated Guard struct (Facts field instead of Config). Updated NewGuard signature. Updated Evaluate to use guard.Facts. Added DefaultPhase constant.
- main.go: Removed configPaths(). Added factsDirs(). Rewrote loadGuard() to use fact dirs. Updated cmdEval to use DefaultPhase. Updated cmdValidate to validate facts too. Updated help text.
- testdata/facts/git_branch.yaml and has_pyproject.yaml created.

## Additional Done
- guard_test.go: Rewrote loadTestGuard, replaced TestLoadConfig/TestLoadConfigMissing/TestMergeConfigs with TestLoadFact/TestLoadFactMissingCommand/TestLoadFactsFromDir/TestLoadFactsFromDirMissing/TestMergeFacts. Updated all Config{} references to use nil or removed.
- testdata/config.yaml deleted.
- testdata/facts/git_branch.yaml and has_pyproject.yaml created.
- README.md: Replaced config.yaml section with Facts section.
- All 34 tests pass.

## Next Step
- Commit changes.
- Build and install binary.
- Verify `ward validate` works.
- Write report.
