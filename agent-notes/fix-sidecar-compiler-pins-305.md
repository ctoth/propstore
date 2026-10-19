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
- Follow-up CI at note head `7fe5d963` also passed: https://github.com/ctoth/propstore/actions/runs/39340643967 — 1848 passed, 4 skipped.
- Parent authorized integrating default after PR #308 merged. Merge commit `d370eb72eb5f764648e604fc2b0a6a3ab0d22a1b` has parents `7fe5d9637e37268e3fff39348c2518338e1276f1` and `62d4e3ad48717d793383dcf4fba2e8ce16b4a10c`; no conflicts. Parser-admission source/tests equal default, and cache-identity source/tests equal the prior PR head.
- Integrated-head CI at `80169e3d` passed: https://github.com/ctoth/propstore/actions/runs/39341784126 — 1854 passed, 4 skipped.
- Default then advanced through PR #307. Merge commit `db30b3a227cdbbad40b1504f88aaa1d97be06ba0` has parents `80169e3d56a406e80fc3bc5e39d8c5be1d9b956a` and `dac0a7262dfddc455d0367d6ad45c644a100a80f`; no conflicts. Both incoming parser/ATMS fixes equal default, and cache source/tests remain unchanged. PR #310 was verified open/unmerged and is not included.
- Wheel repair verified locally: `UV_OFFLINE=1 uv run --no-project -- <existing .venv python> scripts/run_logged_pytest.py --label issue305-wheel -- tests/test_derived_build.py -n 0 --basetemp .tmp-issue305-wheel` passed **44 tests in 33.91s**. Evidence: `logs/test-runs/issue305-wheel-20261019-174125.log`. Real Hatch wheel building used an isolated temporary build environment and cached build dependencies; the shared project environment was not changed.
- Whitespace diff check passed. Relative to the integrated default, only the task note, derived-build owner module, packaging config and its test file differ. #307/#308 remain intact; no #310 changes. No remote writes occurred during the migration pause.
- Automatic approval review initially rejected the entire local add/commit/status command before execution, citing the original audit's no-code restriction. Parent supplied trusted transcript evidence of Q's later instruction to implement fixes and explicitly authorized one retry. That retry succeeded: the verified wheel repair is committed locally on `fix/sidecar-compiler-pins-305`. No remote mutation occurred; publication remains paused during migration.

## Decisions and why
- Migration pause: no pushes, merges, transfers, remote URL edits or other remote mutations until parent verifies the new destination. Published head remains `091fc55a892db99030668ebca6829449c08c87a1`; its CI passed 1862 tests with 4 skipped (run 39342325562).
- Parent authorized fixing the wheel regression locally in this branch. Smallest packaging change: Hatch's existing force-include bundles the root lock as `propstore/_compiler_dependencies.lock`; approximately 20 runtime/config lines select it, or select the current source lock only with adjacent Propstore project metadata. Quire retains sole ownership of lock-pin parsing/hash/cache behavior. No build hook, second dependency list or custom identity serialization.
- A real wheel built with the existing cached backend had no lockfile and failed sidecar materialization with all selected pins absent. The new regression builds a wheel in an isolated temporary build environment, extracts/imports it in a fresh process, checks source/wheel pin equality, ignores an unrelated adjacent lock and materializes/reuses a real sidecar. Source-mode tests cover live pin changes and strict missing-pin rejection.
- Smallest change: correct/complete the explicit compiler/solver/serialization dependency selection, reject a missing selected pin, retain Quire caching unchanged. Approximately 35 production lines plus focused tests in the existing derived-build test file.
- Tests substitute lockfile fixtures, not installed dependencies; prove pin sensitivity, unchanged unrelated dependencies, missing-pin rejection and rebuild against an existing sidecar.
- Existing environment may be used without sync/install. Run only the test file being edited locally through the logged runner; PR CI runs the repository suite.
- #303 is independent and remains paused for a semantic decision. An unchanged incoming reference to `c` does not specify whether it follows either changed version or both. Choosing one, indiscriminately duplicating it, retaining a fictitious third claim or dropping it would change semantics. Parent needs this decision before source changes for #303.

## Surprises
- The first focused regression failed specifically on the absent distribution name `argumentation` (log issue305-red-20261019-170925.log).
- I supplied a nested pytest basetemp without creating its parent. The first full edited-file run had 5 passes and 31 fixture-setup errors for that path, not source assertions. Correct the invocation to a fresh directory directly under the worktree; no test/source workaround is needed.

## Next step
Return the local commit for parent review. Wait for parent to verify the migrated repository destination and authorize publication before any remote mutation. Keep PR #309 draft/unmerged; its published CI predates the local wheel repair. #303 remains paused for its semantic decision.
