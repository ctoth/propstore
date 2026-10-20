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
