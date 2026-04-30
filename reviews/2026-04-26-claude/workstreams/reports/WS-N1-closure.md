# WS-N1 Closure Report

Workstream id: WS-N1
Closing implementation commit: `41b1fdf7`

## Findings Closed

- T5.4 / Codex #38-#39: app-layer request objects no longer accept CLI-shaped JSON/string payloads, and owner-layer errors no longer name CLI flags.
- T5.5 / Codex #40: owner modules no longer render process streams or own argv parsing; CLI code renders the typed reports/failures.
- T5.6: local canonical JSON helpers were collapsed onto Quire's canonical JSON bytes surface.
- T5.8 / D-3: old-data shims and silent fallback surfaces were deleted with no aliases or compatibility path.
- D-4: `WorldModel` was renamed to `WorldQuery` with no legacy export.
- D-5: grounded-domain "verdict" prose was renamed to grounded classification terminology at the cited sites.
- Adjacent doc drift: stale root design notes moved to `docs/historical/`, and contradictory/silent-drop documentation was corrected.

## Red Tests First

The initial WS-N1 red run was `logs/test-runs/WS-N1-red-20260430-094917.log`: 12 failed, 1 passed, 1 xfailed. Failures covered CLI-shaped app requests, owner-layer CLI flag errors, owner process/argv ownership, local canonical JSON helpers, D-3 shim surfaces, `WorldModel` exports/usages, grounded-domain verdict prose, and stale docs.

## Logged Gates

- `logs/test-runs/WS-N1-app-request-slice-20260430-095522.log` — 18 passed.
- `logs/test-runs/WS-N1-owner-stream-slice-20260430-100020.log` — 15 passed.
- `logs/test-runs/WS-N1-canonical-json-slice-20260430-100220.log` — 25 passed.
- `logs/test-runs/WS-N1-old-shims-slice-20260430-100759.log` — 53 passed.
- `logs/test-runs/WS-N1-worldquery-slice-20260430-101129.log` — 31 passed.
- `logs/test-runs/WS-N1-verdict-slice-20260430-101232.log` — 37 passed.
- `logs/test-runs/WS-N1-doc-drift-slice-20260430-101425.log` — 3 passed.
- `logs/test-runs/WS-N1-preclose-20260430-101752.log` — 13 passed, 1 xfailed before the closure sentinel flip.
- `logs/test-runs/WS-N1-20260430-102046.log` — 14 passed after the closure sentinel flip.
- `logs/test-runs/WS-N1-full-20260430-102122.log` — exposed stale full-suite expectations after deleting the `active` status shim and owner-layer flag wording.
- `logs/test-runs/WS-N1-full-failures-20260430-102526.log` — 21 passed; covers the full-suite regression fixes.
- `logs/test-runs/WS-N1-full-rerun-20260430-102545.log` — 3489 passed, 2 skipped.

Static gates:

- `uv run pyright propstore` — 0 errors, 0 warnings, 0 informations.
- `uv run lint-imports` — 5 contracts kept, 0 broken.

## Property Gates

WS-N1 is an architecture hygiene workstream, not a paper-semantic workstream. Its gates are static and behavioral architecture assertions: AST scans for request payload shape, owner-layer process ownership, canonical JSON ownership, shim deletion, public naming, and doc drift.

## Files Changed

- CLI/app boundary: `propstore/app/forms.py`, `propstore/cli/form.py`, `propstore/app/concepts/mutation.py`, `propstore/cli/concepts.py`, `propstore/app/worldlines.py`, `propstore/cli/worldline/`, and `propstore/app/world_revision.py`.
- Owner presentation boundary: `propstore/sidecar/build.py`, `propstore/compiler/workflows.py`, `propstore/provenance/__init__.py`, `propstore/source/lifecycle.py`, `propstore/contracts.py`, and `propstore/cli/contracts.py`.
- Canonical JSON callers: `propstore/observatory.py`, `propstore/policies.py`, `propstore/epistemic_process.py`, and `propstore/support_revision/history.py`.
- Shim and naming surfaces: `propstore/core/concept_status.py`, `propstore/world/types.py`, `propstore/classify.py`, `propstore/world/model.py`, public exports, world query callers/tests, grounding prose, sidecar rules, and ATMS prose.
- Docs/tests: WS-N1 architecture gates, `docs/gaps.md`, this WS file, the workstream index, and this report.

## Remaining Risks

WS-N2 still owns the layered import-linter contract and the negative import-linter violation test. WS-K already moved heuristic logic under `propstore/heuristic/`; WS-N1 only cleaned the immediate hygiene prerequisites. Quire's canonical JSON semantics remain owned by the Quire/WS-J side; WS-N1 made propstore consume that single source.
