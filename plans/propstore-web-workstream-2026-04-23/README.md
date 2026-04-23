# propstore.web Workstream - 2026-04-23

## Purpose

Turn the exploratory `propstore.web` GUI notes into an executable workstream.

The target is not "the CLI in a browser" and not a dashboard. The target is a
web presentation adapter over `propstore.app`: a graphical shell and durable
reading surface for propstore's epistemic operating system.

This workstream deliberately starts with the app-owned report contracts that a
web surface needs. Web routes, React, graphs, charts, audio, and command streams
are only added after the owner-layer reports exist.

## Source Material

Primary input:

- `propstore-web-gui-vamp-2026-04-19.md`

Direct review findings incorporated here:

- `propstore.web` must be a presentation adapter peer to `propstore.cli`.
- The semantic navigator is the real core and must be app-owned.
- Current `propstore.app` request/report boundaries are promising but uneven.
- Command-journal and `command_id`-keyed report pages are not production-ready
  yet.
- The first surface must prove blind-native access before visual graph, chart,
  or audio projections are added.

Relevant existing architecture:

- `docs/application-layer-and-undo.md`
- `docs/worldlines.md`
- `docs/argumentation.md`
- `docs/event-semantics.md`
- `propstore/app/*`
- `propstore/cli/*`

## Target Architecture

```text
Browser
  owns focus, layout, local draft text, viewport, and presentation state

propstore.web
  owns HTTP routing, request parsing, content negotiation, rendering,
  static assets, and browser interaction affordances

propstore.app
  owns typed request/report contracts, command execution, journal identity,
  render-policy construction, and repository-bound use cases

Domain packages
  own compiler workflows, source lifecycle, world/ATMS/revision semantics,
  sidecar policy, merge semantics, and semantic object behavior
```

The web package must never own canonical claim status, conflict
classification, accepted extensions, provenance facts, branch state, source
lifecycle state, merge results, or persisted command results.

## Non-Negotiable Rules

- `propstore.web` is a presentation adapter only.
- No web route imports below `propstore.app` to obtain semantic behavior.
- No browser code computes claim acceptance, conflict classification, support
  strength, provenance truth, merge results, or source lifecycle state.
- No graph, canvas, SVG, WebGL, chart, or audio surface may be the only way to
  inspect an object.
- No blank rendering for unknown, vacuous, underspecified, blocked, missing, or
  not-applicable states.
- Every computed URL includes the state needed to make the answer reproducible:
  repository target, branch or revision, render policy, and relevant bindings.
- React, if introduced, remains domain-thin and server-authoritative.
- Do not add compatibility shims, fallback readers, dual paths, or old/new
  adapter glue.
- Do not implement `/report/{command_id}` or SSE command streams until the
  app-layer command journal exists in production code.

## Package Target

Initial package shape:

```text
propstore/web/
  __init__.py
  app.py
  routing.py
  requests.py
  serialization.py
  templates/
    base.html
    claim.html
    neighborhood.html
  static/
    web.css
  testsupport.py
```

Later package shape, after the server-rendered surface and app contracts are
working:

```text
propstore/web/
  api/
    claims.py
    concepts.py
    neighborhoods.py
    worldlines.py
  presenters/
    html.py
    json.py
    errors.py
  frontend/
    package.json
    src/
      shell/
      api/
      workbench/
      graph/
      charts/
      audio/
      reports/
```

`propstore/web/__init__.py` stays shallow. Importing `propstore.web` must not
import command families, world reasoners, graph libraries, React assets, or
unrelated web route modules.

## Workstream Files

- `README.md`: scope, rules, target architecture, and completion criteria.
- `app-contracts.md`: typed app-layer reports required before web behavior.
- `web-surface.md`: URL, rendering, accessibility, and state rules.
- `execution-slices.md`: ordered implementation slices with gates.
- `verification.md`: test, type, search, and manual accessibility gates.
- `review-findings.md`: proposal-review findings incorporated into the plan.

## Completion Criteria

The workstream is complete when:

- `propstore.app` owns typed reports for claim view and semantic neighborhood
  traversal.
- `propstore.app` owns render-policy request construction used by CLI and web.
- `propstore.web` serves a server-rendered read-only claim view and JSON view
  from the same app report.
- The first web surface works with JavaScript disabled.
- The first web surface renders every ignorance or blocked state literally.
- Web routes import only `propstore.app`, repository lookup, web-local
  presenter helpers, and framework/runtime dependencies.
- `uv run pyright propstore` passes.
- Focused logged pytest batches for the new app contracts and web routes pass.
- Search gates show no web-owned semantic computation.
- React, graph libraries, charts, audio, command streams, and report pages are
  either absent or backed by explicit app-owned report contracts.

## Out Of Scope Until Prerequisites Exist

- React workbench shell.
- Graph library selection or integration.
- Highcharts dashboards or sonification.
- `/report/{command_id}` pages.
- SSE command progress streams.
- Mutating web workflows.
- Auth/session design.
- Static HTML export.
- Public deployment.

These are not rejected. They are blocked on app-owned contracts and the first
blind-native server-rendered surface.
