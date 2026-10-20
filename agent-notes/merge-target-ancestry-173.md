# Merge target ancestry (#173)

## Goal
Preserve an existing target's reachable history when publishing a two-parent
merge, with consistent target admission in inspect and commit.

## State
Branch `fix/merge-target-ancestry-173`, base `3a7726a65e332290fbfe0f4b6e646402971a6551`.
Baseline test failed with DID NOT RAISE ValueError: unchanged writer admitted a
stationary third divergent target. Log issue173-baseline-20261020-162841.log.
Implementation uses frozen MergeCommitPlan, plan_merge_commit, and one publisher
on the plan. Existing create_merge_commit remains the one-shot public operation;
app captures the same plan to report the actual target lease. Inspect gains typed
request/report and --target-branch. No overlapping merge PR (330 grades/331
dimensions are other workers).
First focused run: 20 passed, issue173-admission-20261020-163152.log. Final focused
run including CLI stale-target races: 22 passed in 16.48s,
issue173-cli-races-20261020-163331.log.
Draft PR332 head2ceb3a820d3e79a1d208d1221767c3a9c2e53c7b; CI39509173313
success: 2093 passed, 4 skipped, 4 warnings in 96.65s.
Actual Claude Opus5.5 review exit0, gate complete; no admission/CAS correctness
defect. Follow-ups: strict ancestor of only one parent (added both directions),
preview's existing ambiguous-base refusal documented/tested, API/CLI docs updated.

## Decisions and why
Active workflow: protocols:cleanup-refactor. The broken branch-name request to
publication edge is a valid capability with the wrong representation. Rewrite
it around one immutable owner plan containing exact input heads, target head
(None for absence), and target admission. Quire's ancestor_distances already owns
graph reachability. Keep one publisher, existing exact-head CAS, and two parents.
App owns typed inspect/commit requests and reports; CLI only constructs/renders.
Smallest estimate: 100–150 production lines and one focused regression file;
no dependency, third parent, overlay, rebase, retry, or new locking machinery.
Keep #194 unrelated-history admission and #41 post-commit report rescan separate.
Git's documented merge model records two parent tips and requires the current
history to be represented by those tips; reachability is graph-based, not time.
References: https://git-scm.com/docs/git-merge and
https://git-scm.com/docs/git-merge-base .

## Surprises
Current CI runs aggregate logged pytest but no Pyright step. Post-publication
package Pyright found identical 14 errors on base3a7726a and head2ceb3a82 from
the untyped occurrences list in family transport. Added the canonical Quire
ArtifactHandle/CharterDoc collection annotation; no behavior change, cast,
suppression or environment modification. Pending acceptance recheck.

## Next step
Run actively edited focused files, publish draft/CI, and obtain actual independent
Claude review of the PR's complete pinned range. Return exact PR/head to parent
before merge. No issue edits.
