# WS-O-qui Closure Report

Date: 2026-04-28

## Result

WS-O-qui is closed.

Quire release:
- Pushed repository: `git@github.com:ctoth/quire.git`
- Release tag: `v0.2.0`
- Release commit: `23bbac27e83fef8c69817c945c8ba72b3941be83`

Propstore integration:
- Propstore pin commit: `a27b3cbc`
- Pin target: `git+https://github.com/ctoth/quire@23bbac27e83fef8c69817c945c8ba72b3941be83`

## Closed Findings

- S-H1/S-H2: canonical hashing now shares quire contract normalization and rejects non-JSON floats.
- S-H3: transaction head precheck is explicitly advisory; GitStore CAS remains authoritative.
- S-H4: stale-head races do not write failed blobs before the final branch-head assertion; dry-run GC reports unreachable objects.
- S-H5: filesystem-backed repo mutations use a cross-process lock.
- S-M1: family and registry contract-version slots reject placeholder versions.
- S-M2: ambiguous reference IDs raise `AmbiguousReferenceError`.
- S-M3: `ForeignKeySpec.required` and `many` are executable through `validate_foreign_key`.
- S-M4: `materialize_worktree()` refreshes the on-disk index.
- S-M5/S-M6: unsupported placement scans fail through typed placement errors.
- S-M7: `merge_base()` uses Dulwich's native implementation.
- S-Boundary: propstore's quire imports are covered by the quire public surface.

## Verification

- Quire full suite: `uv run pytest -q` passed, `207 passed`.
- Propstore boundary: `logs/test-runs/quire-boundary-20260428-011134.log`, `1 passed`.
- Propstore pyright: `uv run pyright propstore`, `0 errors`.
- Propstore import linter: `uv run lint-imports`, 4 contracts kept.
- Propstore full suite: `logs/test-runs/WS-O-qui-full-20260428-011234.log`, `3031 passed`.
