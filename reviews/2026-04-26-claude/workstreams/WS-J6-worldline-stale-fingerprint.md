# WS-J6: Cheap Worldline Staleness Fingerprints

**Status**: OPEN
**Depends on**: WS-J
**Blocks**: scalable list-stale workflows.

## Scope

Replace `WorldlineDefinition.is_stale()` full rematerialization with a dependency fingerprint path that can compare the relevant claims, stances, contexts, assumptions, lifting rules, blocked exceptions, parameterizations, and policy inputs without rerunning the whole worldline.

## First Tests

- A claim dependency change flips the fingerprint and reports stale without evaluating unrelated targets.
- A nondependency change leaves the fingerprint stable.
- Context assumptions, lifting-rule changes, blocked exceptions, and stance changes are each represented in the fingerprint.

## Done Means Done

`is_stale()` no longer calls `run_worldline()` for ordinary stale checks; it computes and compares a typed fingerprint whose coverage is property-tested against the full materialization hash on generated dependency graphs.
