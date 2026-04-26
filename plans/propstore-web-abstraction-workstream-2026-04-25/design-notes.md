# Design Notes

## Accepted Direction

### Keep Current Server-Rendered Surface

The current web surface is already server-rendered, route-tested, JSON-tested,
and accessible enough for automated structure checks. The next useful step is
not another object page. The next useful step is to make the existing surface
cleaner to extend.

### Keep Explicit Presenter Functions

`propstore/web/templates/` is no longer present in the current tree. The active
production presenter path is `propstore/web/html.py`.

This workstream keeps explicit presenter functions and improves them. It does
not reintroduce templates.

Reason:

- current presenters render typed app reports directly;
- helper extraction can remove duplication without adding a second rendering
  surface;
- switching to templates would be a separate replacement, not a local cleanup.

### Use Web-Local Layout Helpers

Repeated markup construction belongs in `propstore.web` when it is layout-only.

Examples:

- render-policy display rows;
- filter sections;
- machine-ID sections;
- table wrappers;
- status text formatting from already-app-owned state and reason fields.

These helpers must not generate semantic sentences that app reports should own.

### Improve Beauty As Reading Infrastructure

The visual pass is not decoration. It should make the current pages better for
long reading, scanning, comparison, and keyboard operation.

The right aesthetic is quiet, dense, and document-like:

- strong text hierarchy;
- clear tables;
- disciplined spacing;
- visible focus;
- resilient narrow-screen behavior;
- print-friendly defaults.

## Deferred Or Rejected Abstractions

### Do Not Unify App View State Types Now

`ClaimViewState`, `ConceptViewState`, and `SemanticState` overlap, but they are
owned by different app reports and carry different meanings. Unifying them now
would be a web-convenience abstraction, not an app-domain requirement.

Risk:

- future claim, concept, and neighborhood reports evolve jointly for no real
  reason;
- `unavailable`, `not_applicable`, and `missing` become easier to blur;
- web tidiness leaks pressure into owner-layer report shapes.

Keep state labels report-local until a real owner-layer convergence need
appears.

### Do Not Introduce AppReadContext Now

The repeated app builder shape is visible, but pre-opening a shared world model
or bundling request context would introduce lifetime and route behavior risks.

Risk:

- routes that do not need a world model start failing on world sidecar state;
- resource lifetime moves out of the owner that knows what it needs;
- a context object becomes a loose bag of route concerns.

Keep the current app-owned open points until another reading surface proves the
shared lifetime.

### Do Not Switch To FastAPI Depends Yet

FastAPI dependency validation is useful, but the current routes have a stable
error envelope and focused tests around it. Switching query parsing to
dependency validation would require a deliberate exception-handler slice.

Risk:

- invalid query errors become FastAPI `422` response bodies;
- `.json` suffix behavior becomes mixed with Accept-header or framework-level
  behavior;
- field-level message text changes without a product decision.

Manual parsing can remain until route error handling is centralized.

### Do Not Add Rich Frontend Libraries

React, graph libraries, charting, audio, SSE, and command-report pages remain
blocked by earlier plan rules and by open manual accessibility verification.

The current workstream must finish the server-rendered reading foundation
before opening any projection surface.

## External Critique Used

Claude Code CLI was used as a design-review tool during intake:

- first pass: identify high-leverage abstraction changes;
- adversarial pass: attack the proposal from abstraction-risk and architecture
  boundaries.

The critique was used to sharpen the workstream. It was not treated as local
verification. Local verification remains the `uv run pyright propstore`,
logged pytest, and search gates in `verification.md`.

## Starting Order

The safest execution order is:

1. typed link rows in `html.py`;
2. shared HTML fragments in `html.py`;
3. visual system in `web.css`;
4. centralized route error handling in `routing.py` and `requests.py`;
5. stale plan convergence notes.

Reason:

- the first three slices are local to the web presentation layer;
- route error handling has wider blast radius and should happen after the
  presenter surface is calmer;
- app-layer abstractions are explicitly deferred.
