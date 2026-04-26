# Execution Slices

## Global Discipline

Work one slice at a time.

For each slice:

1. Define the final local interface.
2. Delete the duplicated or brittle production surface in the touched area.
3. Let tests, type checks, and searches expose remaining callers.
4. Update every caller in the touched surface.
5. Run the slice gates.
6. Keep the slice only if the gates pass and the simplification is real.
7. If the slice cannot converge, revert the slice and record the blocker.

Do not treat passing tests as completion while the old production path for the
active target still exists.

Do not broaden into React, graph, chart, audio, command, mutation, auth, or
deployment work.

## Slice 0 - Intake

### Target

Make this workstream the active control surface for web abstraction and
presentation hardening.

### Tasks

- Read this directory.
- Read the two earlier web workstream directories.
- Read current `propstore/web/*`.
- Read current app report builders touched by web routes:
  `claim_views.py`, `concept_views.py`, `neighborhoods.py`, `rendering.py`, and
  `repository_views.py`.
- Confirm dirty worktree and avoid unrelated files.

### Gates

```powershell
git status --short
rg -n -F "propstore.web" plans/propstore-web-workstream-2026-04-23 plans/propstore-web-concept-view-workstream-2026-04-23 plans/propstore-web-abstraction-workstream-2026-04-25
rg -n "from propstore\.(world|source|merge|sidecar|compiler|families|core)" propstore/web
rg -n "React|Vite|TanStack|ReactFlow|Cytoscape|GoJS|yFiles|Ogma|Highcharts|canvas|svg|webgl|audio|sonification" propstore/web pyproject.toml
```

The last two searches should return no production hits.

## Slice 1 - Typed Link Rows

### Problem

`propstore/web/html.py` uses `_link_table(link_column, href_column)` with row
tuples that hide the href in a positional cell. That is brittle presenter code
and makes table extensions easy to misalign.

### Target

Replace positional link-table rows with a typed web-local row shape.

Suggested local shape:

```python
class LinkRow(NamedTuple):
    link_text: str
    href: str
    cells: tuple[str, ...]
```

The link is always the first visible column. `cells` contains the remaining
visible cells in header order.

### Required Implementation Notes

- Keep the change inside `propstore/web/html.py`.
- Delete `link_column` and `href_column` parameters.
- Preserve empty-table fallback rendering.
- Assert or otherwise fail loudly if a row's cell count does not match the
  headers.
- Do not change app reports, route behavior, URLs, status codes, or JSON.

### Gates

```powershell
rg -n -F "link_column" propstore/web/html.py
rg -n -F "href_column" propstore/web/html.py
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label web-link-rows tests/test_web_claim_index_routes.py tests/test_web_concept_index_routes.py tests/test_web_concept_routes.py tests/test_web_accessibility.py
```

The `link_column` and `href_column` searches must return no hits.

## Slice 2 - Shared HTML Fragments

### Problem

`render_claim_page`, `render_concept_page`, and `render_neighborhood_page`
repeat the same layout structures for render policy, status text, filters, and
machine IDs.

### Target

Extract web-local layout helpers in `propstore/web/html.py`.

Suggested helpers:

- `_render_policy_rows(summary) -> list[tuple[str, str]]`
- `_render_policy_section(summary, *, repository_state: str | None = None) -> str`
- `_filter_section(rows: list[tuple[str, str]]) -> str`
- `_status_text(state: str, reason: str) -> str`
- `_machine_ids_section(...) -> str`

### Required Implementation Notes

- Keep helpers layout-only.
- Do not move app-owned sentence generation into `propstore.web`.
- Do not introduce `Any`, broad `getattr`, or a protocol unless the concrete
  app report type forces it.
- Keep heading IDs unique per page.
- Preserve existing visible text unless a focused accessibility test is updated
  for a deliberate wording improvement.

### Gates

```powershell
rg -n -F '"Reasoning backend", report.render_policy.reasoning_backend' propstore/web/html.py
rg -n -F '"Include drafts", _bool_text(report.render_policy.include_drafts)' propstore/web/html.py
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label web-html-fragments tests/test_web_claim_routes.py tests/test_web_neighborhood_routes.py tests/test_web_concept_routes.py tests/test_web_claim_index_routes.py tests/test_web_concept_index_routes.py tests/test_web_accessibility.py
```

The first two searches should not keep finding repeated per-page render-policy
row construction.

## Slice 3 - Visual System

### Problem

`propstore/web/static/web.css` is almost empty. The current pages are accessible
but visually underdesigned for repeated reading and comparison.

### Target

Add a restrained document-quality visual system for the current server-rendered
pages.

Required coverage:

- readable page width and spacing;
- clear heading hierarchy;
- dense, scannable tables;
- robust table overflow on narrow screens;
- visible keyboard focus;
- print-friendly defaults;
- literal state text remains text, not color-only meaning;
- no hover-only or pointer-only required interaction.

### Required Implementation Notes

- Do not add JavaScript.
- Do not add images, gradients, decorative blobs, chart placeholders, or graph
  placeholders.
- Avoid a one-note palette.
- Keep layout responsive without viewport-scaled fonts.
- Preserve current semantic HTML structure.

### Gates

```powershell
rg -n ":hover|pointer-events|cursor:" propstore/web/static/web.css
rg -n "linear-gradient|radial-gradient|canvas|svg|webgl" propstore/web/static/web.css propstore/web/html.py
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label web-visual-system tests/test_web_skeleton.py tests/test_web_accessibility.py tests/test_web_claim_routes.py tests/test_web_neighborhood_routes.py tests/test_web_concept_routes.py tests/test_web_claim_index_routes.py tests/test_web_concept_index_routes.py
```

The hover/pointer search must return no required-interaction CSS. The
gradient/canvas/SVG/WebGL search should return no production hits for this
slice.

## Slice 4 - Route Error Handling

### Problem

`propstore/web/routing.py` repeats try/except chains across report helpers.
This makes new routes noisy and easy to keep inconsistent.

### Target

Centralize route error mapping while preserving the current route behavior and
error response envelope.

Required behavior:

- `.json` routes still return:

```json
{"error": {"title": "...", "message": "...", "status_code": 400}}
```

- HTML routes still render an accessible error page.
- Existing status codes remain unchanged.

### Required Implementation Notes

- Introduce a typed web query parsing failure instead of catching arbitrary
  owner-layer `ValueError`.
- Map known app/web errors in one place.
- Keep suffix-based JSON/HTML behavior. Do not add Accept-header negotiation in
  this slice.
- Do not convert query parsing to FastAPI dependency validation in this slice.
- Do not swallow unexpected exceptions.

### Gates

```powershell
rg -n "except ValueError as exc" propstore/web/routing.py propstore/web/requests.py
rg -n "except RenderPolicyValidationError as exc|except RepositoryViewUnsupportedStateError as exc|except WorldSidecarMissingError as exc" propstore/web/routing.py
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label web-route-errors tests/test_web_claim_routes.py tests/test_web_neighborhood_routes.py tests/test_web_concept_routes.py tests/test_web_claim_index_routes.py tests/test_web_concept_index_routes.py tests/test_web_skeleton.py
```

The repeated per-route exception searches should shrink to the centralized
mapping only.

## Slice 5 - Plan Convergence Notes

### Problem

Earlier web workstream notes still mention stale or already-converged surfaces,
including template-path convergence and missing entry routes.

### Target

Update plan notes so future implementation starts from the current repo state.

### Required Implementation Notes

- Do not rewrite history-heavy rationale.
- Mark resolved gaps as resolved with concrete evidence.
- Keep unresolved manual accessibility checks explicit.
- Do not claim the missing `propstore-web-gui-vamp-2026-04-19.md` was read.

### Gates

```powershell
rg -n -F "templates/" plans/propstore-web-concept-view-workstream-2026-04-23 plans/propstore-web-abstraction-workstream-2026-04-25
rg -n -F "manual accessibility" plans/propstore-web-concept-view-workstream-2026-04-23 plans/propstore-web-abstraction-workstream-2026-04-25
uv run pyright propstore
```

Template references may remain only as historical notes that clearly say the
surface is already converged. Manual accessibility references must remain
honest about unverified checks.

## Full Workstream Gate

Run after every required slice above is complete:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label propstore-web-abstraction-workstream tests/test_web_skeleton.py tests/test_web_claim_routes.py tests/test_web_neighborhood_routes.py tests/test_web_claim_index_routes.py tests/test_web_concept_index_routes.py tests/test_web_concept_routes.py tests/test_web_accessibility.py tests/test_web_demo_fixture.py tests/test_cli_web.py
rg -n "from propstore\.(world|source|merge|sidecar|compiler|families|core)" propstore/web
rg -n "import propstore\.(world|source|merge|sidecar|compiler|families|core)" propstore/web
rg -n "React|Vite|TanStack|ReactFlow|Cytoscape|GoJS|yFiles|Ogma|Highcharts|canvas|svg|webgl|audio|sonification" propstore/web pyproject.toml
git status --short
```

Expected production search result: no forbidden web imports and no frontend or
projection libraries.
