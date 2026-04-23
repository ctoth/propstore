# Review Findings Incorporated

## Strong Findings

The exploratory proposal has the right core shape:

- `propstore.web` should be a presentation adapter over `propstore.app`.
- The browser should own attention and arrangement, not meaning.
- Accessibility should be the native I/O model, not a compliance pass.
- The semantic navigator is more important than the visual graph library.
- Durable reading pages and expert workbench behavior should share app-owned
  reports.

These ideas remain in the workstream.

## Required Corrections

### Command Journal Assumptions

The proposal's stable command result pages and SSE streams require production
command journal infrastructure. The current repo has a strong architecture
document for that system, but not the production package.

Correction:

- `/report/{command_id}` is out of scope.
- SSE command streams are out of scope.
- Command journal pages are out of scope.
- Undo/redo web surfaces are out of scope.

They return only after the command journal exists as production app-layer code.

### Semantic Navigator Ownership

The proposal describes graph moves such as supporters, attackers, assumptions,
provenance, and policy alternatives. Those are semantic operations.

Correction:

- Add `propstore.app.neighborhoods`.
- Web renders `SemanticNeighborhoodReport`.
- Browser code never derives graph meaning from raw rows.

### Computed URL State

Routes like `/conflict/{id}` are attractive but dangerous. A conflict is not
just an object ID; it depends on branch, revision, bindings, and render policy.

Correction:

- Initial routes are claim routes only.
- Computed routes must expose branch/revision and render policy in the URL.
- Future conflict URLs require an app-owned identity model or policy-qualified
  URL contract.

### False Accessibility

Graph libraries and chart libraries can provide useful accessibility features,
but they do not make propstore's epistemic content accessible by themselves.

Correction:

- First route is server-rendered and JavaScript-free.
- Neighborhood is table/text first.
- Visual graph, chart, and audio projections are later slices backed by the
  same app report.
- Manual screen-reader gates are required before frontend projections.

### Frontend Build Blast Radius

React, Vite, TanStack Query, React Flow, Highcharts, and commercial graph
libraries introduce package management, CI, licensing, and caching concerns.

Correction:

- No frontend build pipeline in the initial slices.
- A later React decision must name package manager, lockfile, build/test
  commands, artifact location, and license constraints.

## External Library Notes

These notes are informational. They do not authorize using the libraries before
the app contracts exist.

- React Flow documents keyboard and screen-reader support, focusable
  nodes/edges, automatic panning, and configurable accessibility labels.
- Highcharts documents an accessibility module and sonification module.
- GoJS documents keyboard control and screen-reader support, but says diagrams
  need app-specific descriptions.
- yFiles has an accessibility demo using ARIA/live regions and also documents
  screen-reader/browser caveats.

Workstream interpretation:

- React Flow may be useful after the semantic neighborhood report exists.
- Highcharts may be useful after app-owned quantitative reports exist.
- GoJS/yFiles/Ogma licensing must be decided before use.
- Cytoscape/Sigma-style renderers still require the propstore semantic
  navigator.

## Second-Opinion Critique

Claude Code was used as an architectural critique tool during review. Its
findings matched the direct inspection:

- semantic navigator needs an app owner;
- command-journal routes are premature;
- render policy should be built by `propstore.app`;
- `ClaimShowReport` is not enough for a durable web view;
- a stricter first slice should be server-rendered, JavaScript-free, and
  report-driven.

This directory adopts those findings as execution constraints.
