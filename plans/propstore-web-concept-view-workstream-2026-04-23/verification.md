# Verification

## Required Command Style

Use the project wrappers for pytest:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label <label> <tests...>
```

Use the package-surface type gate:

```powershell
uv run pyright propstore
```

Do not use bare `pytest`, bare `python`, or bare `pip`.

## Automated Gates

Every production slice in this workstream should run:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label <slice-label> <focused tests>
```

## Required Test Areas

At minimum, this workstream must add or update tests covering:

- shared repository-view contract behavior for claim and neighborhood readers;
- typed concept view report construction;
- `/claims` entry HTML and JSON routes;
- `/concepts` entry HTML and JSON routes;
- unknown concept and sidecar-missing failures;
- concept HTML route;
- concept JSON route;
- literal rendering of missing/unknown/blocked/not-applicable states;
- same report behind concept HTML and JSON routes;
- no blank semantic cells on the concept page;
- focused demo fixture coverage for the concept view.

## Import Boundary Gates

Web must continue importing only app-owned and web-local surfaces:

```powershell
rg -n "from propstore\\.(world|source|merge|sidecar|compiler|families|core)" propstore/web
rg -n "import propstore\\.(world|source|merge|sidecar|compiler|families|core)" propstore/web
```

Expected production result: no hits.

## No-Frontend Gates

This workstream does not open React or rich projection work:

```powershell
rg -n "React|Vite|TanStack|ReactFlow|Cytoscape|GoJS|yFiles|Ogma|Highcharts" propstore/web pyproject.toml
rg -n "canvas|svg|webgl|audio|sonification" propstore/web pyproject.toml
```

Expected production result: no hits.

## HTML Accessibility Gates

Automated assertions should verify:

- one useful `<h1>`;
- non-empty `<title>`;
- one `main` landmark;
- section headings for major page areas;
- table headers for inventory tables;
- no blank semantic cells;
- meaningful link text;
- literal state rendering for all relevant ignorance/absence states;
- no required hover- or pointer-only interaction.

## Manual Accessibility Gates

Manual checks remain required before any React, graph, chart, or audio slice:

- load claim, neighborhood, and concept pages with JavaScript disabled;
- navigate by headings and landmarks;
- navigate links and tables by keyboard only;
- confirm absence and ignorance states are spoken literally;
- confirm a blind operator can explain the concept page from screen-reader
  output alone.

If these are not run, say they were not run.

## Completion Evidence

Before declaring this workstream complete, collect:

- path to the final logged pytest run;
- result of `uv run pyright propstore`;
- import-boundary search results;
- no-frontend search results;
- updated manual accessibility notes;
- the exact files that carried the shared repository-view convergence.
