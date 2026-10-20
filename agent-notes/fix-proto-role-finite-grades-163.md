# Finite proto-role grades (#163)

## Goal
Fix https://github.com/propstore/propstore/issues/163 with a focused draft PR.
Reject non-finite grades through the existing scalar validator, preserve [0, 1]
and slot-owned bundles, and prove canonical registered Concept round trips.
Do not merge, mark ready, close the issue, deploy, use Ward, or expand into #162,
#26, or Quire PR 7.

## State
Implementation complete: the production diff imports/calls the scalar validator
and explicitly rejects bool before the existing [0, 1] check. The new focused module
covers direct construction, typed conversion/MessagePack, nested charter/YAML
decode for both bundle lists, rejected registered-family author/read attempts,
and valid numeric 0/0.0/0.5/1.0/1 canonical storage, sidecar, and repository import.
Draft PR: https://github.com/propstore/propstore/pull/330. The first reviewed
head was c2b6a0152637b4dbaf68d250973dc6fa4425ff53; parent then authorized the
boolean-integrity extension after identifying that adjacent round-trip hole.

Read global/repository AGENTS.md, repository CLAUDE.md, issue and comments,
scalar convergence notes, and the issue-delivery skill. Repository .agents is
empty and has no skills directory. Local master is 3a7726a6; unrelated authored
papers/docs/plans are dirty and remain untouched. Independent bare clone and
worktree live in task-8 on fix/proto-role-finite-grades-163.

## Decisions and why
Smallest production change: import validate_scalar_value and call it from
GradedEntailment.__post_init__ before the existing interval check (two lines).
The parent-authorized extension adds a two-line bool rejection at the same
float-grade owner. The generic scalar validator deliberately admits bool for
other scalar domains and remains unchanged. No coercion or decoder repair.
Use a focused new regression module for construction/typed decode, invalid
Concept author attempts, and registered-family YAML/read/iteration, JSON
sidecar, and repository import of valid boundary/interior grades. No new
production selector, filter, decoder repair, or representation.
Explicit task authorization covers implementation, tests, publication, CI,
and independent review. Dowty (1991) p.572 inspected as an original page image:
the contributing properties remain unchanged; [0, 1] is the existing project
grade contract, not a new claim about Dowty's numeric formalism.

## Surprises
Sandbox local clone failed Git ownership validation; elevated local clone
succeeded without changing global Git configuration or the source checkout.
The first test run exposed a missing required codec source argument in the
new test; corrected before recording the pre-fix reproduction below.

## Verification
- Corrected pre-fix regression: 24 failed, 3 passed in 7.28s, log
  logs/test-runs/proto-role-163-red-corrected-20261020-162533.log. NaN was authored
  successfully and registered-family load then failed with Expected float, got
  null at the slot proto-agent grade. Infinities already failed the interval
  check, but did not use the shared finite-scalar invariant.
- Focused project-init/lemon/concept-family/import suite: 94 passed in 14.52s,
  logs/test-runs/proto-role-163-focused-20261020-162605.log.
- Final expanded charter/YAML regression module: 33 passed in 6.33s,
  logs/test-runs/proto-role-163-charter-20261020-162821.log.
- Changed-file Ruff lint and formatting pass; git diff --check passes.
- uv run pyright propstore reports 14 errors, all in untouched
  propstore/merge/merge_commit.py:226-247. Clean detached base 3a7726a6 checked
  with the same interpreter reports the identical 14 errors. Do not change
  this unrelated merge code as part of #163. Parent confirmed these are already
  established baseline errors and not a new regression in #330. The bool change
  recheck produces the same 14 diagnostics.
- Original exact-head CI at c2b6a015: 2108 passed, 4 skipped in 74.22s, run
  https://github.com/propstore/propstore/actions/runs/39508537001.
- Independent Codex subagent /root/review_163 reviewed all original PR hunks at
  c2b6a015 twice with no actionable findings; existing review gate passed.
  The later bool extension requires follow-up review at its new head.
- Boolean test-first reproduction: both False and True were saved successfully
  through Repository.families.concept, then load failed with Expected float, got
  bool at the slot proto-agent grade. Four new regressions failed in 6.01s:
  logs/test-runs/proto-role-163-bool-red-20261020-163753.log.
- Updated focused project-init/lemon/Concept-family/import suite: 106 passed
  in 15.33s, including all 39 regression cases and numeric int/float boundaries:
  logs/test-runs/proto-role-163-bool-focused-20261020-163822.log.
- Import-linter recheck: 3 contracts kept, 0 broken. Changed-file Ruff lint
  passes; formatter requested a line wrap in the new authoring test.

## Next step
Push the boolean extension to the same draft, verify new exact-head full-suite
CI, and hand the new SHA to the parent for follow-up review. Keep draft status;
do not merge, close the issue, or post comments. Exact new head and external CI
results belong in the delivery handoff.
