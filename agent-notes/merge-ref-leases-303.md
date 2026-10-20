# Merge source and target branch leases (#303)

## Goal
Prevent publication from a stale source or overwriting a concurrently created target. Preserve family transport and nonclaim semantics. Publish a tested draft for independent review, never ready/merge/comment this turn.

## State
Fresh branch `fix/merge-ref-leases-303` at default `8429ef6abc4f8655e7b5a09bb3fcca81031078ee`. Global/project instructions, issue303 acceptance, current merge readers/materialization and Quire transaction contracts read. Original user branches and previous task evidence preserved.

Reproduction on unchanged production code: **5 failed, 1 passed**, `logs/test-runs/merge-ref-race-reproduction-20261020-002104.log`. Three interleavings published stale-source merges; peer movement during the first claim read instead raised `ForeignKeyValidationError: unknown source occurrence: claim 'late'` from mixing newer claims with captured parent indexes; absent target was clobbered; existing-target CAS already rejected correctly. Raw reproduction repositories remain in `.tmp-ref-race-reproduction/`. Stale-source bad merge `3d2f24fe3265eac1ee5801b4d125cb6ea684ac01` has left parent `3816a15d15c7cfba8e5cf9e83ebb1deea858a5d6` while master already points to `719595dd11bbd72033714325c8ea1ad08a60552c`. Absent-target bad merge `f39508a097863be20c554845b5352ceccfd73fcb` overwrote the concurrent authoring branch.

Corrected focused file passed **10 tests in 8.35s**, `logs/test-runs/merge-ref-leases-20261020-002326.log`. Covers both sources moving during read/publication, absent/existing targets, immutable claim/base reads, successful target aliases and exact parents/rivals. Quire owner file passed 16 tests. No dependencies installed or shared environments modified.

Initial un-escalated GitHub branch probes failed at the execution sandbox socket boundary. Parent explicitly authorized the supported escalation for those same reads and continued the bounded draft workflow. Escalated reads succeeded: both defaults unchanged at the recorded bases. No approval denial, alternate route, security-setting change or secret access. Consumer manifest/lock still point to merged Quire base until the corrected owner commit is published; pin all three references to that actual commit before consumer publication. Full suites run on the PRs under the existing repository CI policy.

Quire draft https://github.com/propstore/quire/pull/21 is OPEN/DRAFT at published `0e961ccb77d772af61254b34dc87f3a32d953611`. Its PR/push full CI matrix runs `39380651728`/`39380627834` are in progress. Pinned this exact commit in consumer manifest and both lock references, changing no other dependency. Consumer draft publication next; no ready/merge/review/comment authorized.

## Decisions and why
Smallest change (~25 consumer lines plus ~35 generic Quire lines): pass captured branch-to-commit snapshots to framework construction, compute base from immutable parents, and pass source/target expectations (including absent target) to the actual Quire publication call. Deterministic production-path tests interleave real family authoring between reads/planning/publication; no sleeps. No merge policy changes.

Cleanup-refactor is active. Re-resolving source branches is a valid workflow capability using the wrong representation (mutable ref instead of captured commit). Rewrite that edge to the existing typed family commit reader. Ref mechanics remain Quire-owned. Current Quire mutation guard protects final checks/publication against Quire writers; arbitrary external Git multi-ref transactions are outside this small repair.

## Surprises
None yet.

## Next step
Commit/publish Quire draft first, pin its exact commit in manifest and both lock references, publish consumer draft, verify both full CI results. Do not mark ready, merge or post comments/reviews. Keep #303 open; broad nonclaim semantics remain outside this slice.
