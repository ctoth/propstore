# propstore.web Abstraction Workstream - 2026-04-25

## Purpose

Before `propstore.web` grows another surface, converge the current server-rendered
web adapter around better local abstractions, less duplication, and a more
deliberate reading UI.

This is not a feature-expansion workstream. It does not open React, visual
graphs, charts, audio, mutation workflows, or command streams. It hardens the
existing read-only claim, concept, neighborhood, and discovery pages so future
work does not freeze brittle routing and presenter shapes.

## Current State

Implemented already:

- typed app-owned claim view reports;
- typed app-owned semantic neighborhood reports;
- typed app-owned concept view reports;
- server-rendered and JSON claim, neighborhood, concept, `/claims`, and
  `/concepts` routes;
- strict web JSON serialization;
- focused automated accessibility tests;
- a small web demo fixture;
- presenter-path convergence onto `propstore/web/html.py`.

Verified during workstream intake:

- `uv run pyright propstore` passed.
- `powershell -File scripts/run_logged_pytest.ps1 -Label web-design-intake ...`
  passed for the focused web route/accessibility/demo/CLI tests.
- Import-boundary and no-frontend searches were clean.
- Manual browser and screen-reader accessibility checks were not performed.

Known caveat:

- `propstore-web-gui-vamp-2026-04-19.md` is referenced by earlier plans but was
  not present at the repository root during intake.

## Target

Keep `propstore.web` a presentation adapter while making it easier to extend:

- replace positional table-link rendering with typed presenter rows;
- extract repeated HTML layout fragments without moving semantic sentence
  generation into the web layer;
- add a restrained, document-quality visual system for the current read-only
  pages;
- centralize route error handling while preserving the current JSON/HTML error
  contract;
- update stale plan notes so future work starts from the current repo state.

## Non-Negotiable Rules

- `propstore.web` remains a presentation adapter only.
- No web route imports below `propstore.app` for semantic behavior.
- No browser-side computation of claim acceptance, conflict classification,
  supporter/attacker membership, provenance truth, merge results, or source
  lifecycle state.
- No React, graph, chart, audio, SSE, mutation, or command-report work in this
  workstream.
- Do not unify app-layer state vocabularies just to make web rendering tidier.
- Do not introduce an app read-context abstraction until a real cross-owner
  lifetime need exists.
- Do not switch query parsing to FastAPI dependency validation unless the
  current error envelope is preserved in the same slice.
- Keep HTML helper extraction layout-only. App-owned reports continue to own
  semantic sentences.
- Every slice must either keep a measured simplification or be reverted.

## Workstream Files

- `README.md`: scope, current state, target, and completion criteria.
- `execution-slices.md`: ordered implementation slices and gates.
- `verification.md`: test, type, search, and manual accessibility gates.
- `design-notes.md`: design decisions and rejected abstractions.

## Completion Criteria

The workstream is complete when:

- `propstore/web/html.py` no longer uses positional href/link-column table
  tuples.
- repeated render-policy, filter, status, and machine-ID layout fragments are
  deduplicated in web-local helpers.
- `propstore/web/static/web.css` provides a usable document-quality visual
  system for the current read-only pages.
- repeated route try/except blocks are centralized without changing the
  existing URL set, status codes, or error envelope.
- focused logged web tests pass.
- `uv run pyright propstore` passes.
- import-boundary and no-frontend searches remain clean.
- manual accessibility notes are updated honestly with what was and was not
  verified.
