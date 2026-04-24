# Execution Slices

## Global Discipline

Work one slice at a time.

For each slice:

1. Define the final interface.
2. Delete the duplicated or inconsistent production surface in the touched
   area.
3. Let type checks, tests, and search expose the remaining callers.
4. Update every touched caller to the target surface.
5. Run the slice gates.
6. Keep the slice only if the gates pass.
7. If the slice cannot converge, revert it and record the blocker honestly.

Do not treat passing tests as completion while known old production paths still
exist for the active target surface.

## Slice 0 - Intake

### Target

Keep this directory and the inherited-gaps file as the active control surface.

### Tasks

- Read all files in this directory.
- Reread `plans/propstore-web-workstream-2026-04-23/`.
- Confirm dirty worktree and avoid unrelated files.
- Read current concept app and CLI surfaces.

### Gates

```powershell
git status --short
rg -n -F "ConceptShowReport" propstore/app propstore/cli tests
```

## Slice 1 - Repository View Convergence

### Problem

Claim and neighborhood readers do not yet share one converged repository-view
contract. Concept work must not stack another inconsistent reader on top.

### Target

Add a shared app-owned repository-view request and update claim and
neighborhood readers to use it.

### Required Implementation Notes

- Delete unused reading-surface `bindings` fields if the current readers do not
  depend on them.
- Delete per-view raw branch/revision handling once the shared contract exists.
- A route must not silently accept unsupported repository-view state.

### Gates

```powershell
rg -n -F "branch:" propstore/app/claim_views.py propstore/app/neighborhoods.py
rg -n -F "revision:" propstore/app/claim_views.py propstore/app/neighborhoods.py
rg -n -F "bindings:" propstore/app/neighborhoods.py
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label web-concept-repository-view tests/test_claim_views.py tests/test_neighborhoods.py tests/test_web_claim_routes.py tests/test_web_neighborhood_routes.py
```

The search gates may still find the shared repository-view contract after this
slice. They must not keep finding stale duplicated reader-local fields.

## Slice 2 - Typed Concept View Report

### Problem

`ConceptShowReport(rendered: str)` is not a durable web/API report.

### Target

Add `propstore/app/concept_views.py` with `ConceptViewRequest`,
`ConceptViewReport`, and explicit supporting dataclasses.

### Required Implementation Notes

- Reuse existing owner logic where it exists.
- Do not move HTML or JSON rendering into `propstore.app`.
- Do not emit dict-shaped semantic payloads.
- Do not silently reuse the YAML string report as the concept page contract.
- Keep current YAML-oriented concept show behavior only if untouched callers
  still need it; do not conflate it with the new concept view contract.

### Gates

```powershell
rg -n "class ConceptView|ConceptViewReport|ConceptViewRequest" propstore/app tests
rg -n "dict\\[str, object\\]|Mapping\\[str, object\\]|: object" propstore/app/concept_views.py
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label web-concept-app tests/test_concept_views.py
```

## Slice 3 - Presenter Path Convergence

### Problem

The current web package contains both string presenters and a template file.

### Target

Choose one production presenter path and delete the unused one.

### Required Implementation Notes

- If templates are adopted, claim and neighborhood presenters must move too.
- If explicit presenter functions remain the target, delete the dead template
  files.
- Do not leave dead production paths in place.

### Gates

```powershell
Get-ChildItem -Recurse -File propstore/web/templates
rg -n -F "render_claim_page(" propstore/web
rg -n -F "render_neighborhood_page(" propstore/web
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label web-concept-presenters tests/test_web_accessibility.py tests/test_web_skeleton.py
```

## Slice 4 - Entry Routes

### Problem

The current web surface has object pages but weak discovery. Readers who do not
already know an ID need collection entrypoints.

### Target

Implement:

```text
GET /claims
GET /claims.json
GET /concepts
GET /concepts.json
```

### Required Implementation Notes

- Prefer one route family per object kind with query-parameter filtering and
  search, rather than multiplying route variants.
- Use existing app-owned list/search reports where they are sufficient.
- If an entry page needs a missing field, add it to the app report instead of
  deriving it in web.
- HTML and JSON must stay report-symmetric.

### Gates

```powershell
rg -n -F '"/claims"' propstore/web tests
rg -n -F '"/concepts"' propstore/web tests
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label web-entry-routes tests/test_web_claim_index_routes.py tests/test_web_concept_index_routes.py tests/test_web_accessibility.py tests/test_cli_web.py
```

## Slice 5 - Concept Routes

### Problem

The next reading surface needs real routes, not just an app report.

### Target

Implement:

```text
GET /concept/{concept_id}
GET /concept/{concept_id}.json
```

### Required Implementation Notes

- HTML and JSON must render from the same app report.
- Web request parsing must build only app-owned request dataclasses.
- No semantic grouping or classification in routes or presenters.
- Error pages and JSON errors must remain literal and accessible.

### Gates

```powershell
rg -n -F "/concept/{concept_id}" propstore/web tests
rg -n -F "build_concept_view" propstore/web tests
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label web-concept-routes tests/test_web_concept_routes.py tests/test_web_accessibility.py tests/test_cli_web.py
```

## Slice 6 - Demo Fixture Extension

### Problem

The concept page needs a known fixture that exercises grouped claims, blocked
visibility, uncertainty, and provenance coverage.

### Target

Extend the focused web demo fixture or add a similarly tight replacement.

### Required Implementation Notes

- Prefer extending `tests/web_demo_fixture.py`.
- Keep the fixture small and typed.
- Do not introduce a broad demo corpus.

### Gates

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label web-concept-demo tests/test_web_demo_fixture.py tests/test_concept_views.py tests/test_web_concept_routes.py
uv run pyright propstore
```

## Slice 7 - Accessibility And Verification Update

### Problem

The concept page must meet the same document-quality and honesty standards as
the first web pages.

### Target

Add explicit automated accessibility checks and update manual notes honestly.

### Required Implementation Notes

- concept page must have one useful `h1`;
- inventories must use table headers;
- link text must be meaningful;
- literal state labels must remain visible;
- manual notes must say what was not verified.

### Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label web-concept-accessibility tests/test_web_accessibility.py tests/test_web_concept_routes.py
```

## Full Workstream Gate

Run after every required slice above is complete:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label propstore-web-concept-workstream tests/test_claim_views.py tests/test_neighborhoods.py tests/test_concept_views.py tests/test_web_claim_routes.py tests/test_web_neighborhood_routes.py tests/test_web_claim_index_routes.py tests/test_web_concept_index_routes.py tests/test_web_concept_routes.py tests/test_web_accessibility.py tests/test_web_demo_fixture.py tests/test_cli_web.py
rg -n "from propstore\\.(world|source|merge|sidecar|compiler|families|core)" propstore/web
rg -n "React|Vite|TanStack|ReactFlow|Cytoscape|GoJS|yFiles|Ogma|Highcharts|canvas|svg|webgl|audio" propstore/web pyproject.toml
```
