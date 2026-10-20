# Reviewed dependency integration

## Goal
Integrate exactly the reviewed Quire, Doxa, and assignment-selection fixes in
one draft PR. Do not merge or mark ready. Keep semantic issues #303/#306 out of scope.

## State
Implementation and focused verification complete. Independent bare clone and
worktree created inside task-20; Q's dirty checkout,
shared remotes, and all other workers are untouched. Remote HEAD/master verified:
Propstore f3c21bc5c9070d0bfa16b437f28ab41ee1e6ca2d;
Quire d1daeed8b361fff227fb0cbf915f9a2049f1bbf0;
Doxa ef12c894a6760d9dd86ebcd2c45da679c8928059;
assignment-selection 5816c20b8247898fa96e02e6e42e66b69987dfc7.
Global and repository AGENTS.md/CLAUDE.md and issue-delivery skill read.

## Decisions and why
Smallest change: three exact dependency pins, normal `uv lock` regeneration,
and approximately 150–250 lines of integration regressions using existing
Propstore owners. Canonical URLs only for those three dependencies. No new
production abstraction, semantic policy, broad upgrade, or repository migration.
The explicit delegation authorizes this implementation and full validation.

## Surprises
Network access needs sandbox escalation. GitHub verified all supplied heads.
The current CI workflow runs full logged pytest only; type and lint checks need
separate execution. Existing open PRs are unrelated Dependabot updates.

`uv lock` changed exactly the three package sources and their three matching
requires-dist entries; no unrelated package versions changed.
The new integration module exercises incoming/outgoing FK rejection, direct and
transactional normalized claim moves, explicit null form parameters, 16/400-input
Doxa fuse/WBF/CCF through persisted stance opinions and rendering, and adjacent
large-integer selection through the real Propstore merge entrypoint.

## Verification
- Logged focused suite: 15 passed in 23.20s;
  logs/test-runs/reviewed-dependencies-20261019-195206.log.
- `uv run pyright propstore`: 0 errors, 0 warnings, 0 informations.
- `uv run ruff check propstore tests`: all checks passed.
- `uv run lint-imports --no-cache`: 3 contracts kept, 0 broken.
- `git diff --check`: clean.
- Optional full formatting check found three unchanged baseline files:
  propstore/world/atms.py, tests/test_algorithm_parse_admission.py,
  tests/test_derived_build.py. The added integration module is formatted.
- Quire PRs 13/14/15/16/18 all verified closed and merged through GitHub.
- Propstore history confirms merges 307/308/309/310/311 are in the base.

## Next step
Commit the four scoped files, push the isolated task branch, open one draft PR,
and read fresh full logged-test CI for its exact head. Preserve draft status and
do not merge. Parent performs final review/merge after CI succeeds.
