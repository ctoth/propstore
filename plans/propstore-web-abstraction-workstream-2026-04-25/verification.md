# Verification

## Required Command Style

Use the project pytest wrappers:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label <label> <tests...>
```

Use the package-surface type gate:

```powershell
uv run pyright propstore
```

Do not use bare `pytest`, bare `python`, or bare `pip`.

## Required Evidence

Before declaring this workstream complete, collect:

- final `uv run pyright propstore` result;
- path to the final logged pytest run;
- import-boundary search results;
- no-frontend/no-projection search results;
- `git status --short`;
- manual accessibility note stating what was and was not verified.

## Focused Test Gates

The minimum focused web gate is:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label propstore-web-abstraction-workstream tests/test_web_skeleton.py tests/test_web_claim_routes.py tests/test_web_neighborhood_routes.py tests/test_web_claim_index_routes.py tests/test_web_concept_index_routes.py tests/test_web_concept_routes.py tests/test_web_accessibility.py tests/test_web_demo_fixture.py tests/test_cli_web.py
```

Slice-specific gates may run a narrower subset first, but the full focused web
gate must pass before the workstream is complete.

## Type Gate

Run after every production slice:

```powershell
uv run pyright propstore
```

Expected result: zero errors.

## Import Boundary Gates

`propstore.web` must continue importing only app-owned, repository lookup,
web-local, and framework/runtime surfaces.

```powershell
rg -n "from propstore\.(world|source|merge|sidecar|compiler|families|core)" propstore/web
rg -n "import propstore\.(world|source|merge|sidecar|compiler|families|core)" propstore/web
```

Expected production result: no hits.

## No-Frontend Gates

This workstream does not open frontend work or rich projections:

```powershell
rg -n "React|Vite|TanStack|ReactFlow|Cytoscape|GoJS|yFiles|Ogma|Highcharts" propstore/web pyproject.toml
rg -n "canvas|svg|webgl|audio|sonification" propstore/web pyproject.toml
```

Expected production result: no hits.

## HTML Structure Gates

Automated tests must continue checking:

- one useful `<h1>`;
- non-empty `<title>`;
- one `main` landmark;
- section headings for major page areas;
- table headers for inventory and graph-projection tables;
- no blank semantic cells;
- meaningful link text;
- literal state rendering for relevant absence and ignorance states;
- no required hover-only or pointer-only interaction.

The visual-system slice should add or preserve checks for:

- visible focus style;
- responsive table overflow behavior where testable without a browser engine;
- no hover or pointer dependency.

## Error Contract Gates

Route error centralization must preserve:

- current URL set;
- current HTTP status codes;
- JSON error envelope:

```json
{"error": {"title": "...", "message": "...", "status_code": 400}}
```

- accessible HTML error page with one useful `<h1>`.

Focused tests must cover:

- invalid boolean query;
- invalid numeric query;
- invalid limit;
- unsupported repository view;
- unknown claim;
- unknown concept;
- missing sidecar.

## Manual Accessibility Gates

Manual checks remain required before any React, graph, chart, or audio slice:

- load claim, neighborhood, concept, `/claims`, and `/concepts` pages with
  JavaScript disabled;
- navigate by headings and landmarks;
- navigate links and tables by keyboard only;
- confirm absence and ignorance states are spoken literally;
- confirm a blind operator can explain the concept and neighborhood pages from
  screen-reader output alone.

If these are not run, say they were not run. Do not imply automated checks are
equivalent to screen-reader verification.

## Completion Checklist

- [ ] Slice 1 link-row cleanup complete.
- [ ] Slice 2 shared HTML fragment cleanup complete.
- [ ] Slice 3 visual system complete.
- [ ] Slice 4 centralized route error handling complete.
- [ ] Slice 5 plan convergence notes complete.
- [ ] `uv run pyright propstore` passed.
- [ ] Full focused logged web test gate passed.
- [ ] Import-boundary searches clean.
- [ ] No-frontend/no-projection searches clean.
- [ ] Manual accessibility notes updated honestly.
