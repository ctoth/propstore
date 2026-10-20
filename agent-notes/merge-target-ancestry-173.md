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
First focused run20 passed; CLI race follow-up22 passed. Final actively edited
target/nonclaim files: 84 passed in66.48s, log
issue173-review-followup-20261020-164311.log.
Draft PR332 source head5a0de23e5eeb5711767c66c50241a63a30ae8320;
CI39510208189 success: 2103 passed, 4 skipped, 4 warnings in121.23s.
Actual Claude Opus5.5 review exit0, gate complete; no admission/CAS correctness
defect. Follow-ups: strict ancestor of only one parent (added both directions),
preview's existing ambiguous-base refusal documented/tested, API/CLI docs updated.
Fresh full-range Claude review at5a0de23e also found no production defect, with
two doc-signature findings. Author's earlier imprecise patch context changed the
wrong first-parameter snippet; fixed exact headings/definitions against source:
repository framework owner/name/branch_commits and create_merge_commit repo arg.

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
suppression or environment modification. Post-publication package Pyright1.1.407
with the existing interpreter and explicit source paths: exit0, 0errors0warnings.

## Next step
Publish docs-only correction, get terminal CI and resumed actual Claude
verification/complete updated hunk ledger, then return exact PR/head to parent.
Remain draft pending parent coordination; no merge/ready/issue edits.
