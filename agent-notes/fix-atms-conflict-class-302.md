# Fix ATMS conflict classifications (#302)

## Goal
Preserve every conflict record while allowing only proven conflicts to induce
ATMS nogoods. Deliver one draft PR; do not merge or modify the user's checkout.

## State
Isolated branch `fix/atms-conflict-class-302`, based on da0b48b4. Source change
adds the classification check at nogood construction. Focused regression file
covers all classifications and repository-backed context-separated parameters.

## Decisions and why
The existing argumentation owner recognizes CONFLICT, OVERLAP and PARAM_CONFLICT.
Apply that same semantic distinction where ATMS constructs nogoods; retain all
records and existing derived-value contradiction handling. Smallest change is
about seven production lines plus focused tests. No feature removal.

## Surprises
The first authored integration test used bind({}) instead of bind(), then
requested zero future queryables (which correctly yields zero future entries).
Both test mistakes are corrected. The logged focused run passed all 8 tests:
logs/test-runs/issue-302-20261019-170945.log (4.68 seconds). It used the existing
environment through uv --no-sync, with PYTHONPATH set to this worktree.

## Next step
Commit/push the isolated branch, open a draft PR, and follow CI to a terminal
result. No source or dependency changes outside this worktree.
