# WS-N2 Closure Report

Closed: 2026-04-30
Closure commit: `05f9f482`

## Scope Closed

- Replaced the old import-linter spot checks with one six-layer `layers` contract.
- Removed the four vacuous `forbidden` contracts instead of preserving them as comments or fallbacks.
- Added a fail-closed negative harness that injects every lower-to-higher layer violation and requires import-linter to reject it.
- Tightened the existing remediation gate so it asserts the layered contract shape, absence of legacy forbidden contracts, and absence of a residual allowlist.
- Removed the `BoundWorld.fragility` world-layer adapter; the public fragility boundary is `propstore.fragility.query_fragility`.

## Implementation Notes

The landed `.importlinter` contract uses `containers = propstore` with relative package names. Same-row modules use `:` rather than `|` because import-linter treats `|` as independent same-row layers and rejects imports among them. `:` preserves the six vertical README rows without imposing extra intra-row independence.

The final rows are:

1. `web : cli`
2. `app`
3. `argumentation : aspic_bridge : world : belief_set`
4. `heuristic`
5. `source`
6. `storage`

## Evidence

- Red gate: `logs/test-runs/WS-N2-red-20260430-144657.log` failed before the contract replacement.
- Contract gate: `uv run lint-imports` passes with `propstore six-layer architecture KEPT`.
- Type gate: `uv run pyright propstore` passed with 0 errors.
- Targeted closure: `logs/test-runs/WS-N2-20260430-150618.log` passed 6 tests.
- Full suite: `logs/test-runs/WS-N2-full-rerun-20260430-151015.log` passed `3495 passed, 2 skipped`.

## Follow-up From Verification

The first full-suite run found one stale test expecting `BoundWorld.fragility`. That expectation was wrong under the final layer contract because keeping it would reintroduce an upward import from the world layer into the fragility orchestrator. The test now locks the intended boundary: `query_fragility` remains callable and `BoundWorld` does not own a fragility adapter.
