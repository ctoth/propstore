# Verification

## Required Command Style

Use the project wrappers for pytest:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label web-slice-name tests
```

Use the package-surface Pyright gate:

```powershell
uv run pyright propstore
```

Do not use bare `pytest`, bare `python`, or bare `pip`.

## Core Automated Gates

Every implementation slice that changes production code must run:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label <slice-label> <focused tests>
```

Broaden to:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label propstore-web-workstream tests
```

after the claim and neighborhood routes both exist.

## Import Boundary Gates

Web must not import semantic owners directly:

```powershell
rg -n "from propstore\\.(world|source|merge|sidecar|compiler|families|core)" propstore/web
rg -n "import propstore\\.(world|source|merge|sidecar|compiler|families|core)" propstore/web
```

Expected result: no production imports.

Allowed imports:

- `propstore.app.*`
- `propstore.repository` for repository lookup only
- web-local modules
- framework/runtime dependencies
- standard library modules

If a route appears to need a forbidden import, extract an app report first.

## Client-Semantics Gates

Browser code and templates must not compute semantic truth:

```powershell
rg -n "accepted|extension|defeated|supporter|attacker|conflict|provenance kind|source lifecycle|merge result" propstore/web
```

Expected result:

- presenter labels are allowed;
- route or browser computation is not allowed;
- no reducer, callback, template branch, or serializer may classify semantic
  state from raw rows.

## Initial No-Frontend Gates

Until a later decision note opens a frontend slice:

```powershell
rg -n "React|Vite|TanStack|ReactFlow|Cytoscape|GoJS|yFiles|Ogma|Highcharts" propstore/web pyproject.toml
rg -n "canvas|svg|webgl|sonification|audio" propstore/web
```

Expected result: no production hits except historical comments in this
workstream directory if the search is broadened.

## HTML Accessibility Gates

Automated tests should check each rendered page for:

- exactly one `<h1>`;
- non-empty `<title>`;
- `main` landmark;
- section headings;
- table headers for every data table;
- no semantic blank cells;
- literal rendered text for unknown/vacuous/blocked/missing/not-applicable
  values;
- same app report behind HTML and JSON routes.

Suggested test assertions:

```text
HTML contains "unknown" when the report state is unknown.
HTML contains "vacuous" when the report state is vacuous.
HTML contains "blocked" when the report state is blocked.
HTML contains "missing" when the report state is missing.
HTML contains "not applicable" when the report state is not applicable.
HTML does not contain empty semantic table cells.
JSON contains the same state token as HTML.
```

## Manual Accessibility Gates

These gates are required before adding React, graph, chart, or audio slices.

Manual page checks:

- Load the claim page with JavaScript disabled.
- Load the neighborhood page with JavaScript disabled.
- Navigate by headings.
- Navigate by landmarks.
- Navigate all links and tables by keyboard only.
- Confirm every table has enough header context to make a row meaningful.
- Confirm every absence or ignorance state is spoken as a literal state, not
  silence.
- Confirm a sighted collaborator can understand the page without using color,
  graph position, hover, or tooltip.
- Confirm a blind operator can explain the epistemic position from the page
  without seeing a visual projection.

Screen reader/browser combinations to use when available:

- NVDA with Firefox on Windows.
- NVDA with Chrome on Windows.
- Windows Narrator with Edge as a sanity check.

Do not claim these gates passed unless they were actually performed.

## Error Handling Gates

Tests should cover:

- unknown claim ID;
- missing sidecar;
- invalid render policy parameter;
- invalid branch/revision state if implemented;
- JSON error response;
- HTML error response.

Error responses must:

- identify the requested object or invalid parameter;
- avoid empty generic "not found" pages when the app error is more specific;
- preserve expected status codes;
- render accessible headings.

## Serialization Gates

The serializer must:

- handle dataclasses;
- handle tuples and lists;
- handle enums;
- handle `Path` only when an app report intentionally exposes a path;
- preserve `None` only when the report field's meaning is documented;
- fail on unsupported arbitrary objects.

Tests must include at least one unsupported-object failure. Do not silently
stringify unknown objects.

## Dependency Gates

When adding FastAPI or templating dependencies:

```powershell
rg -n "fastapi|starlette|jinja" pyproject.toml uv.lock
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label web-dependencies tests
```

If a frontend package manager is introduced in a later slice, the decision note
must name:

- package manager;
- lockfile;
- build command;
- test command;
- CI gate;
- artifact location;
- license constraints.

## Completion Evidence

Before declaring the workstream complete, collect:

- path to the final logged pytest run;
- result of `uv run pyright propstore`;
- result of import-boundary searches;
- result of no-frontend/no-graph searches;
- manual accessibility notes, including what was and was not verified;
- the `next-surface-decision.md` file if Slice 9 is complete.

If a gate was not run, say it was not run. Do not claim verification without
evidence.
