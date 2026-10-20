# Aspirin dependency demo and canonical justification connection

## Goal
Build the approved narrow end-to-end demonstration using disposable stores,
preserving the original corpus and other active fixes. Q has now authorized a
focused draft PR in the verified transferred propstore/propstore repository.

## State
Focused publication branch `demo/aspirin-dependencies-public`, integrating
master db85b89bf770b63514f19f420466ff87d0be0f63, including merged #309/#310.
Runtime dependencies are the existing main checkout's installed environment;
tests must import this worktree, with sync/network installation disabled.

## Target architecture and slice
Canonical `families.justifications.Justification` must flow from Git/sidecar to
WorldQuery, the compiled graph, and ASPIC. It already owns the semantic fields.
The mirror `core.justifications.CanonicalJustification` and optional protocol
fallback are forbidden. Their consumers must use the charter directly.
Stance support is a relation; it must not masquerade as authored inference.

## Classification and disposition
- Justification charter: keep, existing family/domain owner.
- CanonicalJustification: duplicate representation; delete the file and rewrite
  bridge/fragility/merge consumers to the charter owner directly.
- Optional AuthoredJustificationStore fallback: delete silent omission; carry
  authored justifications as part of the compiled world snapshot.
- WorldQuery: valid reader capability missing; add charter-native selection.
- Reported-premise synthesis: rewrite so inferred conclusions are not also
  unconditional premises. Explicit reported licences can preserve an independent
  report; absent such a licence, authored inference premises control its support.

## Smallest change
About 150 production lines across existing graph/reader/bridge owners, mechanical
caller updates, one focused regression file, and a roughly 200-line demo runner.
Specific attack targets are a separate owner slice (#55), not a demo adapter.

## Search and runtime gates
- `rg CanonicalJustification propstore tests` must have no hits.
- No optional protocol fallback may silently omit canonical justifications.
- Focused disposable-store regression proves stored licence use, withdrawal,
  context, competing support, and actual argumentation output.
- Existing logged test wrapper is used. The parent explicitly authorized full
  local validation for this isolated delivery after the focused checks.

## Decisions and evidence
Existing issue coverage: #21 reader/mirror, #55 explicit targets, #56 stance
evidence, #123 contract, #155 overlay snapshot. No duplicate issue creation.
Old aspirin schema migration is outside scope; use fresh current charters.

## Next step
The first slice is committed as 94ddfdc95dec31264dce0efddb382e6a34d9cf7b.
Keep the publication PR as a draft and await review. Do not merge or mark ready.
Specific multi-justification attack targeting (#55) remains unresolved; do not
claim it fixed or close that issue.

## Progress 2026-10-19 17:50 UTC
- Canonical Justification now reaches WorldQuery/compiled graph/ASPIC. The mirror
  module and optional fallback were deleted; consumers use the charter directly.
- Real-store regressions execute evidence withdrawal, unchanged base query, and
  independent reported support. One initial fixture omitted all concepts, so the
  compiler returned an empty claim projection; inspection showed `claims []`.
  The fixture now declares its concept, matching the successful first case.
- Logged focused run: 32 passed in 6.37s across test_core_justifications.py,
  test_aspic_bridge.py, test_defeasibility_aspic_integration.py,
  test_lifting_exception_justification.py, test_projection_boundary_ws6.py.
  Log: logs/test-runs/canonical-justification-20261019-174953.log.
- Plugin contribution is established: author-rules taught empirical outcomes
  from strict study-setting facts. Local prompt correction and report/inference
  separation are implemented; its affected contract file passes 19 tests.
- No push, issue creation, PR creation, or other remote mutation occurred.

## Verified executable slice
- Final focused run: 34 passed in 7.16s; log
  logs/test-runs/canonical-owner-final-20261019-180142.log.
- Includes a source proposal/finalize/promotion round trip whose actual inference
  loses support after its evidence is withdrawn, active-graph and graph-delta
  licence preservation, independent report support, and ambiguous context IDs.
- Forbidden source/test searches for CanonicalJustification,
  core.justifications, AuthoredJustificationStore are zero-hit.
- Both in-memory store fixtures are rewritten to the required canonical
  justification inventory; no optional missing-method fallback was restored.
- The two affected store-consumer files passed 13 tests in 3.52s. Log:
  logs/test-runs/justification-store-consumers-20261019-180442.log.
- The sibling standalone `../aspirin-demo/demo.py` completed with exit 0. It
  executes context, premise withdrawal, source promotion, real two-parent merge,
  undercut and objection withdrawal through actual ASPIC/grounded arguments.
  Its exact run is saved in ../aspirin-demo/run-output.txt.

## Remaining bounded limitations
- #55 generic specific-justification/premise targeting is not implemented. The
  demo honestly has one challenged licence; it does not pretend to solve #55.
- #123 semantic/identity totality and #56 broader stance evidence preservation
  remain existing independent issues. No duplicate issues were created.
- Context CLI mutation is unavailable today. The plugin corrections report it;
  the demo intentionally uses current owner APIs, not the plugin CLI workflow.
- The historical corpus remains unmigrated and unchanged. No paper was copied.

## Local draft description
Title: Read authored justifications through world argumentation

A promoted inference previously remained invisible to WorldQuery/ASPIC, while
its conclusion entered as an unconditional reported premise. Read canonical
Justification charters into the graph and argumentation path, delete the mirror
and optional omission, and keep derived support dependent on its actual premises.
Explicit independent reports remain possible. Addresses #21, not the separate
argument-target and evidence-identity workstreams. Validation is the focused
logged regression run and the disposable applicability demonstration.

## Fixed-point disposition
Kept owners: Justification charter, WorldQuery, graph mechanics, existing ASPIC
translation/projection, and current source-promotion identity. Rewritten edges:
canonical sidecar selection, required inventory protocol, graph/delta/overlay
carriage, bridge rule/KB construction, fragility inputs, and merge's reported
premise input. Removed surfaces: duplicate CanonicalJustification class/module,
attribute/to_dict scaffold, optional authored-reader protocol and omission, and
support-relation-to-justification impersonation. Mechanical test consumers now
use the charter. No compatibility alias, adapter, migration, or old reader added.

Commit message: Read canonical justifications through world argumentation.
The bounded #21 connection slice reached its search/runtime fixed point; the
separate #55/#56/#123 issues remain outside this slice.

## Full validation and review correction
- The first full owner and merged-base compatibility runs found exactly three
  resolution tests failing: their _ArgumentationWorld fixture lacked the newly
  required all_justifications inventory. Added an empty canonical inventory to
  that fixture, preserving the skeptical-outcome, policy-forwarding and error
  propagation assertions. The production requirement remains mandatory.
- Three typing findings were introduced by this slice: a private helper import
  and two redundant None comparisons. Support-stance translation now lives in
  the existing translation owner; redundant comparisons were removed.
- Final full owner suite: **1832 passed, 1 skipped**, exit 0, 94.23s.
  Log: logs/test-runs/full-owner-revised-20261019-181754.log.
- Exact base is 24e205bac9650b562a8a1cae7b8d8edb2e6f4159. Merged #308
  (62d4e3ad48717d793383dcf4fba2e8ce16b4a10c) and #307
  (dac0a7262dfddc455d0367d6ad45c644a100a80f) are not ancestors of this
  branch. A separate detached ../propstore-compat-307-308 worktree at dac0a726
  carries only this delivery's patch, without rebasing or changing this branch.
- Full compatibility suite: **1846 passed, 1 skipped**, exit 0, 94.78s.
  Log in that worktree:
  logs/test-runs/compat-307-308-revised-20261019-181758.log.
- Owner and compatibility pyright: 0 errors, 0 warnings. Both passed ruff check
  and import-linter (3 contracts kept, 0 broken). Owner formatting: all 611
  files formatted. Compatibility formatting finds one unchanged base file,
  tests/test_algorithm_parse_admission.py, introduced by 2eeca9fc2d006e5fa947b6ddfe505aaa6f974e2c
  in the #308 history; git diff HEAD for that path is empty. It was not edited.
- Pytest emitted a non-fatal cache warning: its pre-existing .pytest_cache
  directories denied nodeids writes. Disposable test data used separate
  --basetemp paths under ../test-output; no dependency installation occurred.
- #310 head eb229b84811ef272407ce183fb4d2b8242e677ce remains excluded. It
  is still OPEN in the final read-only GitHub metadata check. No unreviewed
  changes from it were integrated.

Commands (from each corresponding worktree):
```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
$env:UV_OFFLINE='1'
$env:UV_NO_SYNC='1'
$env:UV_CACHE_DIR='C:/Users/Q/Documents/Codex/2026-10-19/task-18/test-output/uv-cache'
uv run --offline --no-sync --project C:/Users/Q/code/propstore python C:/Users/Q/code/propstore/scripts/run_logged_pytest.py --label full-owner-revised -- tests --basetemp=C:/Users/Q/Documents/Codex/2026-10-19/task-18/test-output/owner-revised -q
uv run --offline --no-sync --project C:/Users/Q/code/propstore python C:/Users/Q/code/propstore/scripts/run_logged_pytest.py --label compat-307-308-revised -- tests --basetemp=C:/Users/Q/Documents/Codex/2026-10-19/task-18/test-output/compat-revised -q
uv run --offline --no-sync --project C:/Users/Q/code/propstore pyright --pythonpath C:/Users/Q/code/propstore/.venv/Scripts/python.exe propstore
uv run --offline --no-sync --project C:/Users/Q/code/propstore ruff check propstore tests
uv run --offline --no-sync --project C:/Users/Q/code/propstore ruff format --check propstore tests
uv run --offline --no-sync --project C:/Users/Q/code/propstore lint-imports --no-cache
```

## Publication integration and final validation
The original isolated branch and all its changes are preserved at 65a616e5.
Its original local base included 25 unrelated agent-note additions, so the
focused publication worktree starts at verified remote master and carries only
the two reviewed task commits. Those unrelated notes are excluded from the PR.
The newly merged #310 was then merged cleanly at ccc71568. #309 is not imported.

Added the requested equation/justification interaction coverage to the existing
equation-applicability test owner. A real stored equation and input support an
application via a canonical justification. Withdrawing the equation removes
both its derived value and the application's accepted ASPIC argument while the
canonical licence stays stored. This passes under claim-graph and ATMS policies.
No production adjustment was needed for the #310 integration.

- Final full suite: **1861 passed, 1 skipped**, exit 0, 83.71s.
  Log: logs/test-runs/publication-owner-final-20261019-190735.log.
- Equation/canonical-justification focused run: 18 passed, exit 0, 13.52s.
  Log: logs/test-runs/equation-justification-interaction-20261019-190631.log.
- Integrated package pyright: 0 errors, 0 warnings; ruff check passed;
  import-linter: 3 contracts kept, 0 broken.
- The unchanged standalone demo completed all nine transitions on this
  integrated implementation with exit 0.
- Publication command uses the existing authenticated Git/gh route. No new
  permissions, credentials, dependency-repository writes, merge or ready
  transition are part of this delivery.

## Stabilized master and published draft
Draft PR: https://github.com/propstore/propstore/pull/311.
The parent's last planned core merge, #309 at db85b89, is merged normally into
this branch. No published history is rewritten. The initial offline full run
passed 1895 tests but its wheel probe could not resolve Hatchling from the empty
isolated build cache. Populating the project-declared build backend in this
task's cache fixed that execution cause; the shared environment was unchanged.

The new #309 JSON-origin local also produced four Unknown typing errors.
Classification: IO-boundary-only decoded carrier, consumed entirely inside
_sidecar_dependency_pins. Disposition: keep it at that IO boundary with an
explicit dict[str, Any] annotation. Only canonical string pins leave the
function; no parser mirror, fallback or runtime cache behavior was added.

Final stable-base evidence:
- Full suite: **1896 passed, 1 skipped**, exit 0, 87.24s.
  Log: logs/test-runs/publication-owner-stable-final-20261019-191504.log.
- Derived-build/wheel suite: **44 passed**, exit 0, 23.55s.
  Log: logs/test-runs/publication-wheel-final-20261019-191416.log.
- Pyright: 0 errors, 0 warnings. Ruff lint passed; 3 import contracts passed.
- All nine demo transitions completed after the #309 merge, exit 0.

Keep #311 draft and unmerged. The separate demo repository will pin this
published owner-fix history explicitly rather than claiming it is in master.
