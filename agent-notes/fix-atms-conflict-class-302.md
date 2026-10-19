# Fix ATMS conflict classifications (#302)

## Goal
Preserve every conflict record while allowing only proven conflicts to induce
ATMS nogoods. Deliver one draft PR; do not merge or modify the user's checkout.

## State
Isolated branch `fix/atms-conflict-class-302`, based on da0b48b4. Source change
adds the classification check at nogood construction. Focused regression file
covers all classifications and repository-backed context-separated parameters.
Published draft PR: https://github.com/ctoth/propstore/pull/307.
Implementation commit e97661feece92ef3d98ad936fad247fcaf8a7541 passed full CI:
https://github.com/ctoth/propstore/actions/runs/39340001227,
1825 passed, 4 skipped in 100.94 seconds. No full suite was run locally.

## Decisions and why
The existing argumentation owner recognizes CONFLICT, OVERLAP and PARAM_CONFLICT.
Apply that same semantic distinction where ATMS constructs nogoods; retain all
records and existing derived-value contradiction handling. Smallest change is
about seven production lines plus focused tests. No feature removal.

## Current-default integration
Merged default 62d4e3ad48717d793383dcf4fba2e8ce16b4a10c (PR308 parser
restoration) without conflicts or production edits. claim_contracts.py and the
restored test_algorithm_parse_admission.py exactly match that default commit.
The focused integration run passed 14 tests in 5.74 seconds:
logs/test-runs/issue-302-integrate-308-20261019-172629.log. The merge commit
will receive fresh full PR CI. Neither #307 nor #310 depends on the other;
each independently integrates the same default restoration.

## Surprises
The first authored integration test used bind({}) instead of bind(), then
requested zero future queryables (which correctly yields zero future entries).
Both test mistakes are corrected. The logged focused run passed all 8 tests:
logs/test-runs/issue-302-20261019-170945.log (4.68 seconds). It used the existing
environment through uv --no-sync, with PYTHONPATH set to this worktree.

## Next step
Keep the PR in draft; do not merge. This documentation update records the
completed implementation and terminal CI result. No source or dependency changes
outside this worktree. No implementation work remains for #302.
