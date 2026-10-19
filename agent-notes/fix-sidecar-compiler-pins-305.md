# World-sidecar compiler identity (#305)

## Goal
Deliver a focused fix, regression coverage and a draft PR for #305; follow CI to a terminal result. No merge or ready-for-review transition is authorized.

## State
- Read global/project instructions, prior audit notes, #303/#305 and current PR searches. Neither issue has an existing PR.
- Isolated branch `fix/sidecar-compiler-pins-305`, based on fetched `origin/master` at `da0b48b4`.
- Main checkout and other audit worktrees remain untouched.
- Production change is 33 added/9 removed lines; the existing test file gains focused version/revision, missing-pin and existing-cache regressions.
- Edited-file baseline after the production fix: 36 passed (`logs/test-runs/issue305-green-path-20261019-171055.log`). Four Git-revision cases were then added and cache rebuild cases changed to Git revisions where applicable: all seven new/changed cases passed (`logs/test-runs/issue305-git-pins-20261019-171211.log`).
- Scoped whitespace diff check passed. No other package environment was modified.
- Draft PR: https://github.com/ctoth/propstore/pull/309, implementation commit `91c853bed3ee33691e43a49142025a25a64839d5`.
- Full PR CI completed successfully: https://github.com/ctoth/propstore/actions/runs/39340227393 — 1848 passed, 4 skipped in 106.01s. Draft/open state and exact tested head verified afterward.

## Decisions and why
- Smallest change: correct/complete the explicit compiler/solver/serialization dependency selection, reject a missing selected pin, retain Quire caching unchanged. Approximately 35 production lines plus focused tests in the existing derived-build test file.
- Tests substitute lockfile fixtures, not installed dependencies; prove pin sensitivity, unchanged unrelated dependencies, missing-pin rejection and rebuild against an existing sidecar.
- Existing environment may be used without sync/install. Run only the test file being edited locally through the logged runner; PR CI runs the repository suite.
- #303 is independent and remains paused for a semantic decision. An unchanged incoming reference to `c` does not specify whether it follows either changed version or both. Choosing one, indiscriminately duplicating it, retaining a fictitious third claim or dropping it would change semantics. Parent needs this decision before source changes for #303.

## Surprises
- The first focused regression failed specifically on the absent distribution name `argumentation` (log issue305-red-20261019-170925.log).
- I supplied a nested pytest basetemp without creating its parent. The first full edited-file run had 5 passes and 31 fixture-setup errors for that path, not source assertions. Correct the invocation to a fresh directory directly under the worktree; no test/source workaround is needed.

## Next step
Publish this handoff-only update and follow its CI to terminal, then return draft PR #309, tested commit and CI results to the parent. Keep the PR draft and unmerged. #303 remains a pending semantic decision, with no source changes: an existing artifact-level relation has no field declaring which rival version its evidence follows. Its branch occurrences are available to a merge plan, but treating them as version-bound evidence and recomputing dependent family identities requires an explicit semantic choice and family-owned remapping support.
