# Issue 26: restore algorithm parse admission

## Goal
Restore the smallest well-specified part of #26: execute AlgorithmParseCheck
through the existing claim validator and family pass. Publish a small draft PR,
follow CI to a terminal result, and leave it draft/unmerged. No default push.

## State
- PR branch `fix/issue26-algorithm-parse-pr-20261019`, base `da0b48b4`.
- Main dirty research work and all other workers' branches remain untouched.
- Read global/root instructions, current #26/#19 and #19's decision comment,
  existing claim/compiler tests and pinned ast-equiv parser implementation.
- No matching existing PR found in current issue/semantic-check searches.

## Decisions and why
- Smallest change: approximately 15 production lines in `claim_contracts.py`,
  using ast-equiv's existing parse_algorithm/AlgorithmParseError, plus focused
  validator and repository compiler/build regressions. No new validator/API.
- This PR references #26; it does not claim to close the dimensional and
  unbound-name portions. Their contracts require separate scoped work.
- Preserve invalid authored claims and normal claim quarantine diagnostics.
- Use the existing installed environment read-only with uv --no-sync and no
  bytecode writes. Keep test artifacts in this isolated worktree.
- #19's later research comment resolves Q3/Q4 enough for raw uncalibrated
  judgments, but its generic invocation/judgment evidence owner (#215) and full
  directional proposal workflow are a larger slice; no improvised replacement.
- Only the actively written regression file runs locally; PR CI owns full-suite
  validation under the standing global instructions.

## Surprises
The text of #19 still lists Q3/Q4 as open, but its current comment explicitly
resolves them enough to proceed. Do not repeat the stale blocker claim.
The initial feature branch inherited the unrelated local notes-move commit.
Before PR creation, made the PR branch from GitHub master and carried only this
issue commit. The initial branch is preserved; no default branch was changed.

## Next step
Inspect and commit the three-file diff, publish the draft PR, and follow
exact-head CI. No merge or ready transition is authorized.

## Verification
- Initial uv invocation could not access its default cache. Redirected only
  UV_CACHE_DIR into this worktree; no dependencies were installed or synced.
- Red: 6 failures in `logs/test-runs/issue26-parse-red-20261019-170912.log`.
  Invalid bodies had no diagnostics and remained unblocked in the real compiler;
  AlgorithmParseCheck was deferred for valid as well as invalid bodies.
- Green: 6 passed in `logs/test-runs/issue26-parse-green-20261019-170950.log`.
  Regressions cover invalid syntax, no-function source, valid sync/async/local
  comprehension bodies, and repository compiler/validate/build quarantine with
  both exact authored claim documents retained.
- Existing shared venv used read-only via uv no-sync, PYTHONDONTWRITEBYTECODE,
  and explicit worktree PYTHONPATH. All test artifacts stayed in this worktree.
