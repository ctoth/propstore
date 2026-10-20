# Aspirin dependency demo and canonical justification connection

## Goal
Build the approved narrow end-to-end demonstration using disposable stores,
preserving the original corpus and other active fixes. No push/publication while
the parent coordinates the repository organization transfer.

## State
Isolated branch `demo/aspirin-dependencies-local`, based on 24e205ba.
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
- Existing logged test wrapper is used; no full CI gate is run locally.

## Decisions and evidence
Existing issue coverage: #21 reader/mirror, #55 explicit targets, #56 stance
evidence, #123 contract, #155 overlay snapshot. No duplicate issue creation.
Old aspirin schema migration is outside scope; use fresh current charters.

## Next step
Commit the verified slice locally and await migration/publication authorization.
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
