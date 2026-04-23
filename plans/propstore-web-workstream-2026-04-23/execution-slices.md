# Execution Slices

## Global Discipline

Work one slice at a time.

For each slice:

1. Define the final interface.
2. Delete or replace the old duplicated surface in the touched area.
3. Let type checks, tests, and search expose broken callers.
4. Update every touched caller to the target surface.
5. Run the slice gates.
6. Keep the slice only if the gates pass.
7. If the slice cannot converge, revert that slice and record the blocker.

Do not treat passing tests as completion while old production paths remain for
the active target surface.

Do not broaden into React, graphs, charts, audio, command streams, or mutations
until the previous slices are complete.

## Slice 0 - Workstream Intake

### Target

Keep this directory as the active control surface for web implementation.

### Tasks

- Read all files in this directory.
- Read `propstore-web-gui-vamp-2026-04-19.md`.
- Read current app surfaces that the slice touches.
- Confirm current dirty worktree and avoid unrelated files.

### Gates

```powershell
git status --short
rg -n -F "propstore.web" plans/propstore-web-workstream-2026-04-23 propstore-web-gui-vamp-2026-04-19.md
```

## Slice 1 - App-Owned Render Policy Builder

### Problem

Render-policy construction is repeated close to presentation concerns. Web
would otherwise add another query-string-specific builder.

### Target

Add:

```text
propstore/app/rendering.py
```

with:

- `AppRenderPolicyRequest`
- `RenderPolicySummary`
- `build_render_policy`
- `summarize_render_policy`
- typed app-layer validation failures

Update touched CLI world/reasoning callers to use the app builder instead of
duplicating `RenderPolicy` construction.

### Required Implementation Notes

- Do not create `propstore.web.render_policy`.
- Do not add query-string-specific policy normalization.
- Do not silently coerce invalid values.
- Keep `RenderPolicy` itself in its current domain owner.
- The app builder returns the domain `RenderPolicy`; it does not replace it.

### Gates

```powershell
rg -n -F "RenderPolicy(" propstore/app propstore/cli
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label web-render-policy tests
```

The `rg` gate may still find legitimate domain-owner construction and app
builder construction. It must not find duplicate CLI or future web builders for
the same request surface.

## Slice 2 - Typed Claim View Report

### Problem

`ClaimShowReport` is too raw for a durable web page and JSON API.

### Target

Add:

```text
propstore/app/claim_views.py
```

with:

- `ClaimViewRequest`
- `ClaimViewReport`
- supporting explicit dataclasses for concept, value, uncertainty, condition,
  provenance, render-policy summary, and status
- `build_claim_view(repo, request)`

The report must include literal state values for absence and ignorance.

### Required Implementation Notes

- Reuse existing lower-level claim/world behavior through app/domain owners.
- Do not move HTML or JSON rendering into `propstore.app`.
- Do not leave web-critical fields typed as `object`.
- Do not add a dict-shaped payload report.
- Do not remove `ClaimShowReport` unless every current caller is converted in
  the same slice. It may remain as a separate existing CLI report until a later
  claim-app convergence slice.

### Gates

```powershell
rg -n "class ClaimView|ClaimViewReport|ClaimViewRequest" propstore/app tests
rg -n "dict\\[str, object\\]|Mapping\\[str, object\\]|: object" propstore/app/claim_views.py
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label claim-view tests
```

The second `rg` gate should return no loose core report fields. If it returns
hits in IO-bound helper code, document why they are not part of the semantic
pipeline before keeping them.

## Slice 3 - Semantic Neighborhood Report

### Problem

The web proposal's central interaction model has no owner-layer report.

### Target

Add:

```text
propstore/app/neighborhoods.py
```

with:

- `SemanticNeighborhoodRequest`
- `SemanticNeighborhoodReport`
- `SemanticFocus`
- `SemanticFocusStatus`
- `SemanticMove`
- `SemanticNode`
- `SemanticEdge`
- `SemanticNeighborhoodRow`
- `build_semantic_neighborhood(repo, request)`

Implement claim-focused neighborhoods first.

### Required Implementation Notes

- Every edge has a domain sentence.
- Every move has a stable kind and count.
- Supporters and attackers are computed by owner-layer/domain logic, not by web.
- If existing domain surfaces cannot answer a required move, return an explicit
  unavailable/unknown state in the app report; do not make the web infer it.
- Do not add visual graph code in this slice.

### Gates

```powershell
rg -n "class Semantic|SemanticNeighborhood" propstore/app tests
rg -n "supporter|attacker|accepted|extension|conflict" propstore/web
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label semantic-neighborhood tests
```

The second `rg` gate should have no hits until web exists. After web exists, any
hits must be presenter labels only, not semantic computation.

## Slice 4 - Web Dependency And Skeleton

### Problem

The repo has no web package or web dependency declaration.

### Target

Add FastAPI as the web framework dependency and create a shallow package:

```text
propstore/web/
  __init__.py
  app.py
  routing.py
  requests.py
  serialization.py
  templates/
  static/
```

### Required Implementation Notes

- `propstore.web.__init__` remains shallow.
- `create_app` lives in `propstore.web.app`.
- Route registration is lazy enough that importing `propstore.web` does not
  import world command families or unrelated app workflows.
- Web-local request parsing converts HTTP input into app request dataclasses.
- Web-local serialization preserves typed report state and fails loudly on
  unsupported objects.
- Do not add React, frontend build tools, graph libraries, Highcharts, SSE, or
  auth in this slice.

### Gates

```powershell
rg -n "FastAPI|starlette|jinja" pyproject.toml propstore/web tests
rg -n "from propstore\\.(world|source|merge|sidecar|compiler|families|core)" propstore/web
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label web-skeleton tests
```

The import gate must return no semantic-owner imports. If framework internals
or type-only imports cause false positives, narrow the search and document the
reason in the slice notes.

## Slice 5 - Claim HTML And JSON Routes

### Problem

The first useful web page must prove report-driven rendering and JavaScript-free
accessibility.

### Target

Implement:

```text
GET /claim/{claim_id}
GET /claim/{claim_id}.json
```

Both routes call `build_claim_view` with the same parsed app request.

### Required Implementation Notes

- HTML renders from `ClaimViewReport`.
- JSON serializes the same `ClaimViewReport`.
- Templates contain no semantic computation.
- Every unknown/vacuous/blocked/missing/not-applicable value renders literally.
- No JavaScript required.
- No chart or graph.

### Gates

```powershell
rg -n "GET /claim|claim_id" propstore/web tests
rg -n ">\\s*</td>|>\\s*</dd>|>\\s*</span>" propstore/web/templates
rg -n "unknown|vacuous|underspecified|blocked|missing|not applicable" propstore/web/templates tests
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label web-claim-route tests
```

The empty-cell gate must return no semantic blank cells. Whitespace-only
template syntax around structural tags is acceptable only if tests prove absent
semantic values render literal text.

## Slice 6 - Neighborhood HTML And JSON Routes

### Problem

The first route proves object reading. The second proves semantic navigation
without a visual graph.

### Target

Implement:

```text
GET /claim/{claim_id}/neighborhood
GET /claim/{claim_id}/neighborhood.json
```

Both routes call `build_semantic_neighborhood`.

### Required Implementation Notes

- Render move table, supporter table, attacker table, condition table,
  provenance table, and node/edge table.
- Every edge sentence comes from the app report.
- No visual graph.
- No browser-side traversal logic.
- No JavaScript required.

### Gates

```powershell
rg -n "neighborhood" propstore/web tests
rg -n "ReactFlow|Cytoscape|GoJS|yFiles|Highcharts|canvas|svg|webgl" propstore/web pyproject.toml
rg -n "supporter|attacker|accepted|extension|conflict" propstore/web
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label web-neighborhood-route tests
```

The graph-library gate must return no production hits in this slice.

## Slice 7 - Accessibility And Presentation Hardening

### Problem

Passing route tests is not enough to prove blind-native usefulness.

### Target

Add explicit tests and manual-check documentation for the first two pages.

### Required Implementation Notes

- Every page has one useful `h1`.
- Major page areas are represented as sections with headings.
- Tables have headers.
- Links have meaningful text.
- Page title matches the focus object.
- Error pages have headings and literal messages.
- No required behavior depends on hover, pointer position, or visual graph
  layout.

### Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label web-accessibility tests
```

Manual gates are listed in `verification.md`.

## Slice 8 - First Demo Fixture

### Problem

The web surface needs a known demo object that exercises uncertainty,
provenance, supporters, attackers, and policy state.

### Target

Create or identify one repository fixture for a claim with a meaningful
neighborhood.

### Required Implementation Notes

- Prefer an existing fixture if it already exercises the needed states.
- If a new fixture is necessary, keep it focused and typed.
- Do not use external paper text extraction.
- Do not add a broad demo corpus in this slice.

### Gates

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label web-demo-fixture tests
uv run pyright propstore
```

## Slice 9 - Decide Next Surface

### Problem

After the first two pages work, the project must choose one next axis instead
of starting every exciting surface at once.

### Target

Write a short decision note in this directory choosing exactly one:

- concept view;
- source view;
- worldline view;
- conflict view;
- static export;
- React shell foundation;
- graph projection;
- chart projection;
- audio projection.

### Required Implementation Notes

- The chosen surface must identify its app-owned report contract first.
- If the chosen surface is visual, the text/table navigator must already exist.
- If the chosen surface is command-related, the command journal must exist.

### Gates

```powershell
Test-Path plans/propstore-web-workstream-2026-04-23/next-surface-decision.md
```

## Full Workstream Gate

Run after every required slice above is complete:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label propstore-web-workstream tests
rg -n "from propstore\\.(world|source|merge|sidecar|compiler|families|core)" propstore/web
rg -n "ReactFlow|Cytoscape|GoJS|yFiles|Highcharts|canvas|webgl" propstore/web pyproject.toml
```

The graph/chart gate must remain empty unless a later decision note explicitly
opens that slice and adds the corresponding app report contract.
