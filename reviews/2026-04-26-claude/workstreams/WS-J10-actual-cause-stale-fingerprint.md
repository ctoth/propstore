# WS-J10: Actual-Cause Result Staleness Fingerprints

**Status**: OPEN
**Depends on**: WS-J2
**Blocks**: materialized actual-cause cache safety.

## Scope

Add a cheap fingerprint for materialized actual-cause verdicts. WS-J2 returns pure in-memory verdicts and records the need for content-addressable result staleness; this stream owns the cache key, dependency set, and invalidation behavior for persisted actual-cause results.

## First Tests

- Changing an SCM equation dependency changes the actual-cause fingerprint.
- Changing an irrelevant claim outside the SCM dependency set leaves the fingerprint stable.
- Changing witness-search policy or `max_witnesses` changes the fingerprint.
- Fingerprint comparison agrees with full recomputation on generated finite SCMs.

## Done Means Done

Persisted actual-cause verdicts carry a typed dependency fingerprint over the SCM, effect identity, candidate cause, and search policy, and stale checks do not require full AC2 re-enumeration for ordinary cache validation.
