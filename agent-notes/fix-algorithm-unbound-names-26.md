# Issue 26: execute algorithm free-name admission

## Goal
Complete one remaining #26 capability after merged #308: use ast-equiv's
scoped free-variable analysis in the existing claim validator and quarantine
undeclared names through the claim CHECKED pass. Open a draft PR; no merge,
ready transition, or existing issue/PR edits. Stay outside #303 merge code.

## State
- Published draft PR: https://github.com/propstore/propstore/pull/327.
  Implementation commit: `33728ab9fe70c2c2699271be3392c0b3e8b2963c`.
- Isolated branch `fix/algorithm-unbound-names-26`, base `5c62b8d1` from
  freshly fetched `origin/master`; dirty main checkout untouched.
- Local origin is `git@github.com:ctoth/propstore.git`; GitHub resolves it to
  `propstore/propstore`. #26 remains OPEN; #308 merged as `62d4e3ad`.
- Read global/repo AGENTS.md, CLAUDE.md, prior #308 task notes, live #26/#308,
  current claim validator/pass, ClaimVariable charter, algorithm binding readers,
  and pinned ast-equiv free-variable implementation. Main `.agents` is empty;
  no tracked/nested AGENTS.md or relevant local skill there.
- Relevant local memory rechecked against current code; cloud personal context
  was unavailable. No memory writes.
- Implemented the direct ast-equiv call. Red regression: 12 failed/3 passed;
  initial green: 15 passed. Initial full suite: 2001 passed/4 skipped.
- Found and reproduced an import-binding false rejection in pinned ast-equiv;
  fixed its owner in isolated `../ast-equiv-bindings`, commit
  `f27924d993ac91d469f52bae08707b5b2afde89b`, draft PR
  https://github.com/propstore/ast-equiv/pull/4. Owner validation: 14 focused and
  229 full tests passed; package typing has 0 errors. Propstore pins that exact
  pushed commit; only its two lockfile revision references changed.
- Final integration focused run: 18 passed in 7.01s, including imported names.
- Final full suite after the exact owner pin: 2004 passed, 4 skipped, 8 warnings
  in 147.18s. Warnings are FastAPI/Starlette TestClient deprecations.
- Full package typing reports 14 errors at `merge/merge_commit.py:245-266`,
  all reproduced on a clean detached `5c62b8d1` baseline worktree with the same
  dependency environment. No merge-family edits were made.

## Decisions and why
- Smallest change: roughly 20-30 production lines in `claim_contracts.py`,
  directly calling `extract_free_variables` on the existing parsed AST, subtracting
  declared `variable.name or variable.symbol` bindings (same policy as world and
  conflict readers), then emitting ordinary typed body diagnostics.
- The missing edge is an already-owned capability that must use its true owner
  directly; no local scope walker or parallel validator.
- Reuse parsing once; skip free-name execution after parse failure, whose normal
  diagnostic already blocks admission. Deterministically sort undeclared names.
- Expand the existing admission regression file with negative and valid binding,
  scope, builtin, and repository compiler/build cases. User explicitly requests
  focused and full applicable tests, overriding the local full-suite restriction.
- Dimension validation remains a separate #26 slice with checked-form/Bridgman
  contracts; this branch changes algorithm admission only.
- Visually read Pierce (2002), section 5.1 scope and definition 5.3.2 (local PDF
  pages 61 and 72), and Sarkar/Waddell/Dybvig (2004), pp. 201-202. Bound names
  are excluded from free variables; fine-grained passes own individual checks.
  Current ClaimVariable and runtime readers define the concept-binding policy.

## Surprises
- PDFs are ignored and absent in worktrees. Use the main checkout's original
  paper PDFs, rendered to images in the task workspace; do not extract text.
- Normal sandbox network cannot access GitHub; approved escalated read/fetch and
  worktree creation succeeded. No automatic approval rejection so far.
- Shared main venv failed collection with older Quire `transport_identity` API;
  synced this worktree's locked environment instead. Pytest's default existing
  temp root was inaccessible; all subsequent runs use fresh worktree basetemps.
- uv lock refreshed unrelated wheel metadata; reversed those unrelated hunks
  with apply_patch. Locked sync accepted the resulting minimal lockfile.

## Next step
Implementation, local validation, and draft publication are complete. Parent
owns independent review and any later merge decision. Read the final-head CI
result before reporting. Do not merge either PR or mark either ready. The only
package-type failures are the reproduced pre-existing #303-area errors above.

## Evidence logs
- `logs/test-runs/issue26-unbound-red-workspace-20261020-135128.log`
- `logs/test-runs/issue26-unbound-green-20261020-135216.log`
- `logs/test-runs/issue26-unbound-full-20261020-135257.log`
- `logs/test-runs/issue26-final-focused-20261020-140136.log`
- `logs/test-runs/issue26-final-full-20261020-140132.log`

## Review correction
- Parent requested reproduction of five source-traced findings against old heads
  `8f3d87945d6606d106250c31cb154f35578fa02e` / ast-equiv
  `f27924d993ac91d469f52bae08707b5b2afde89b`. All five were reproduced by owner
  tests: 11 failed/1 passed. Do not treat the old passing suite as scope evidence.
- The owner fix deletes the custom scope visitor and queries Python's symtable
  compiler analysis. This fixes class isolation, store subscript loads, lexical
  bindings independent of statement order, exception aliases, and builtins.
  Runtime reachability/definite-assignment analysis remains outside the contract.
- Exact updated owner pin: `88525a0707b6af18efa2923206527ca645f52200`, pushed
  to existing draft ast-equiv #4. Owner full suite: 242 passed; typing: 0 errors.
- Propstore catches the owner's typed binding-syntax error through existing body
  diagnostics, including a real repository invalid-nonlocal regression.
- Expanded admission suite: 25 passed in 12.21s, with real repository coverage
  for both newly rejected and newly admitted cases. Full checks are running.
- Latest focused log: `logs/test-runs/review-admission-focused-20261020-142125.log`.
- No edits to existing PR descriptions; both PRs remain draft. Next: finish full
  checks, commit/push Propstore, read exact-head CI, and return both full SHAs for
  parent re-review. No merge or ready transition is authorized.
- Final owner pin supersedes the intermediate `88525a0` pin above:
  `b4efa217744b5dc93cb69dd18e15e50e0213374b`. Complete builtin lookup is confined
  to free-name analysis; existing positional-renaming policy is preserved after
  a directly reproduced comparison regression. Final owner full suite: 243
  passed; typing: 0 errors.
- Propstore full suite on the intermediate owner pin passed 2011 tests with
  4 skipped; final owner pin validation is next. Typing still reports exactly the
  same 14 baseline merge-code errors, with no merge-family changes.
- Claude review report at `task-13/propstore-history/reports/algorithm-327-ast4-adjudication.md`
  supplied a sixth case: a valid 600-term addition body aborts compilation with
  RecursionError. Reproduced on final owner b4efa21: 1221 bytes, parses as Module,
  recursion limit 1000, ast.unparse raises through validate_claim. Real repository
  regressions for 600 and 800 operands both failed with uncaught RecursionError
  (`review-recursion-red-20261020-142947.log`).
- Smallest correction: add RecursionError to the existing expected exception
  handling for parse and binding checks, matching app/claims.py:99 and conflict
  algorithms.py:77. Keep the owner's existing exception contract; convert the
  expected analysis limit into ordinary typed body diagnostics and quarantine.
  Source is never executed, recursion limits are unchanged, and no inputs drop.
- With the recursion correction, all 27 focused admission tests pass (12.11s):
  `logs/test-runs/review-recursion-green-20261020-143038.log`. Both deep-body
  cases complete compiler/validate/build with normal quarantine and preserve the
  exact authored documents. Full-suite/type/CI final results go in the task
  response; parent owns re-review of the final paired heads.

## Anonymous namespace follow-up
- Parent's exact-head re-review identified genexpr falsely accepted due to an
  anonymous child table conferring is_namespace=True on the unbound global.
- Reproduced with compiler metadata only, then a real repository regression:
  the old b4efa217 pin leaves `sum(x for x in xs) + genexpr` unblocked.
  Log `namespace-consumer-red-20261020-145445.log` has 1 failed/32 deselected.
- Owner now requires actual assigned/imported binding flags, preserving named
  functions/classes and assigned lambdas. Full owner suite: 249 passed;
  package typing: 0 errors. Exact new pin:
  `a4680232b6e19c8952262501f80da7514af05332`.
- Consumer regressions cover genexpr/listcomp/setcomp/dictcomp labels, lambda
  expressions, and real named namespace bindings through compiler admission and
  artifact-retaining quarantine. Analysis never executes authored bodies.
- Separate CI #5 remains at d6d6904aa5fe39265ee2e54efb084ee832bf81e9, hosted
  run 39494960286 green (220 tests, typing, builds). Do not mix this owner fix
  with that CI branch; parent reviews/merges CI before the later #4 rebase.
- Repinned consumer focused suite: all 33 passed (39.55s), including all label
  cases, real named bindings, and both recursion-limit retention cases. Log:
  `logs/test-runs/namespace-consumer-green-20261020-145658.log`.
- Next: final full/type checks and exact-head consumer CI, then return paired
  fix heads and the unchanged green separate CI head to parent for re-review.
