# Ward Shell Parser Implementation Notes

## GOAL
Add shell AST parsing to ward using mvdan.cc/sh/v3 so rules match actual commands, not raw text.

## Current State - Read Complete

### Files in ward:
- `adapters.go` — DetectAndParse, parseClaude/Gemini/Codex, FormatResponse
- `guard.go` — Rule/Guard/State, CEL env, Evaluate, custom functions (last, since)
- `main.go` — eval/set/validate commands, loadGuard
- `adapters_test.go` — 8 tests for detect/format
- `guard_test.go` — 16 tests for rules/facts/state/evaluation

### Rules that match on `input.command` (need updating):
**testdata/rules/ (7 rules):**
- no-python-c.yaml: `input.command.matches("python[3]?\\s+-c")`
- no-bare-python.yaml: `input.command.matches("^python[3]?\\s") && facts.has_pyproject`
- no-git-stash.yaml: `input.command.matches("git\\s+stash")`
- no-git-add-all.yaml: `input.command.matches("git\\s+add\\s+(\\.|--all|-A)")`
- flailing-reads.yaml: no command match (session history only)
- no-edit-in-planning.yaml: no command match (phase check)
- uncommitted-edits.yaml: no command match (history only)

**~/.ward/rules/ (9 rules):**
- no-python-c.yaml: same
- uv-not-python.yaml: `input.command.matches("^python[3]?\\s") && facts.has_pyproject`
- no-git-stash.yaml: same
- no-git-add-all.yaml: same
- no-git-reset-hard.yaml: `input.command.matches("git\\s+reset\\s+--hard")`
- no-force-push.yaml: `input.command.matches("git\\s+push\\s+.*--force")`
- no-tskill.yaml: `input.command.matches("tskill")`
- flailing-reads.yaml: no command match
- uncommitted-edits.yaml: no command match

### Key design:
- `input` is `map[string]any` — adding `commands` as `[]map[string]any` where each has `name` and `full` fields
- Enrichment happens in adapters.go after parsing
- Rules change from `input.command.matches(...)` to `input.commands.exists(c, c.full.matches(...))`
- For simple name-only checks can use `c.name == "git"`

### Test cases to add:
1. Heredoc: `git commit -m "$(cat <<'EOF'\npython -c blah\nEOF\n)"` → NOT trigger python-c
2. Pipe: `echo foo | python -c "import sys"` → SHOULD trigger
3. Chain: `cd /tmp && python -c "print(1)"` → SHOULD trigger
4. Safe args: `echo "git stash is bad"` → NOT trigger git-stash

## PLAN
1. `go get mvdan.cc/sh/v3@latest`
2. Create `parse.go` with ParseCommands function
3. Create `parse_test.go` with unit tests
4. Modify `adapters.go` to enrich Bash events with `commands`
5. Update all rules (testdata + ~/.ward)
6. Update guard_test.go tests that use inline rules
7. Update test_ward_rules.sh
8. Update README
9. Run tests, commit, push

## DONE
- Read all source files
- Read all rules
- Read test script
- Read test fixtures
- Created branch `shell-ast-parsing`
- Added mvdan.cc/sh/v3@v3.13.0 dependency (committed)
- Created parse.go with ParseCommands function (committed)
- Created parse_test.go with 13 tests (committed)
- Fixed ArithExp -> ArithmExp typo
- All parse tests pass (go test -run TestParse -v → ok)

## OBSERVATIONS
- Parse tests all pass
- Build succeeds with enrichment in adapters.go
- Updated 4 testdata rules (no-python-c, no-bare-python, no-git-stash, no-git-add-all)
- The other 3 testdata rules (flailing-reads, no-edit-in-planning, uncommitted-edits) don't match on input.command — no change needed

## OBSERVATIONS (round 2)
- All tests pass (verified with -count=1 -v, all 48 tests including 5 new integration tests)
- Added bashEvent() helper in guard_test.go that calls enrichBashCommands
- Updated inline rule in TestEvaluateDenyVetoesContext to new syntax
- The `-v` without `-count=1` was returning cached results (no verbose output)

## DONE (round 2)
- Updated 4 testdata rules to new syntax (committed)
- Updated guard_test.go with bashEvent helper + 5 new tests (committed in 2 commits)
- Updated all 7 home rules (~/.ward/rules/) to new syntax
- `ward validate` shows all 11 files OK, 0 errors
- Installed new ward binary via `go install`

## DONE (round 3)
- Integration test: 30/30 pass (added 5 AST parsing tests to script)
- Updated README intro paragraph with AST parsing description (committed)
- Updated README CEL context table to mention input.commands
- Still need to: update README example rules to new syntax, add input.commands docs section
- Still need to: commit README, push ward branch, write report

## REMAINING
- Finish README updates (example rules section uses old syntax)
- Commit remaining README changes
- Push ward branch to origin
- Write report to propstore/reports/ward-shell-parser-report.md
