# App Contracts

## Goal

Make the web surface consume stable typed app-layer reports instead of
assembling semantic meaning in routes or browser code.

`propstore.web` may parse HTTP requests and render reports. It must not own the
report's semantic content.

## Current App-Layer Gaps

Current `propstore.app` has many useful request/report dataclasses, but the
surface is not yet a stable browser/API contract:

- Some reports use `object` fields where the web needs explicit domain meaning.
- Some app functions return lower-level workflow objects directly.
- Some workflows still accept loose `Mapping[str, object]` request payloads.
- Render-policy construction is not yet one shared app-owned request boundary.
- No first-class semantic neighborhood report exists.
- No production command journal exists for durable command result pages.

This workstream fixes only the app contracts needed for the first web surface.
It does not attempt to finish the entire application-layer-and-undo design.

## Contract 1 - Render Policy Request

### Problem

Web URLs need to expose render policy. CLI flags and HTTP query strings must not
be separate policy builders.

### Target

Add an app-owned request and builder:

```text
propstore/app/rendering.py
```

Types:

```python
@dataclass(frozen=True)
class AppRenderPolicyRequest:
    reasoning_backend: str = "claim_graph"
    strategy: str | None = None
    semantics: str = "grounded"
    set_comparison: str = "elitist"
    decision_criterion: str = "pignistic"
    pessimism_index: float = 0.5
    praf_strategy: str = "auto"
    praf_epsilon: float = 0.01
    praf_confidence: float = 0.95
    praf_seed: int | None = None
    include_drafts: bool = False
    include_blocked: bool = False
    show_quarantined: bool = False
```

Functions:

```python
def build_render_policy(request: AppRenderPolicyRequest) -> RenderPolicy:
    ...
```

The app layer owns normalization, validation, and error messages for policy
values. CLI and web both build `AppRenderPolicyRequest` and call the same
function.

### Required Deletions

- Delete duplicated render-policy construction in any CLI command family touched
  by this workstream.
- Do not add a `web_render_policy` helper.
- Do not add a query-string-specific policy builder.

## Contract 2 - Claim View

### Problem

`ClaimShowReport` is too raw for a durable web reading page. It exposes many
`object` fields and does not include enough context for a blind-native
document-quality view.

### Target

Add an app-owned claim view report:

```text
propstore/app/claim_views.py
```

Initial request:

```python
@dataclass(frozen=True)
class ClaimViewRequest:
    claim_id: str
    render_policy: AppRenderPolicyRequest = field(default_factory=AppRenderPolicyRequest)
    branch: str | None = None
    revision: str | None = None
```

Initial report:

```python
@dataclass(frozen=True)
class ClaimViewReport:
    claim_id: str
    logical_id: str | None
    artifact_id: str | None
    version_id: str | None
    heading: str
    claim_type: str
    statement: str | None
    concept: ClaimViewConcept | None
    value: ClaimViewValue | None
    uncertainty: ClaimViewUncertainty
    condition: ClaimViewCondition
    provenance: ClaimViewProvenance
    render_policy: RenderPolicySummary
    status: ClaimViewStatus
```

Supporting objects must be explicit dataclasses. They must not be
`dict[str, object]` in the core report.

Required literal states:

- `unknown`
- `vacuous`
- `underspecified`
- `blocked`
- `missing`
- `not_applicable`

These states must be represented as values in typed fields, not as empty
strings, `None` without explanation, or presenter-only labels.

### Required Behavior

- The report contains enough information to render a useful claim page without
  additional semantic route calls.
- The report can be serialized to JSON through a web-local serializer without
  losing state labels.
- The report does not include Click, Rich, HTML, CSS, FastAPI, or presentation
  types.

## Contract 3 - Semantic Neighborhood

### Problem

The proposal's central GUI object is a semantic graph navigator, but no app
report owns the traversal surface.

### Target

Add an app-owned report family:

```text
propstore/app/neighborhoods.py
```

Initial request:

```python
@dataclass(frozen=True)
class SemanticNeighborhoodRequest:
    focus_kind: Literal["claim", "concept", "source", "worldline"]
    focus_id: str
    render_policy: AppRenderPolicyRequest = field(default_factory=AppRenderPolicyRequest)
    branch: str | None = None
    revision: str | None = None
    bindings: Mapping[str, str] = field(default_factory=dict)
    limit: int = 50
```

Initial report:

```python
@dataclass(frozen=True)
class SemanticNeighborhoodReport:
    focus: SemanticFocus
    render_policy: RenderPolicySummary
    status: SemanticFocusStatus
    moves: tuple[SemanticMove, ...]
    nodes: tuple[SemanticNode, ...]
    edges: tuple[SemanticEdge, ...]
    table_rows: tuple[SemanticNeighborhoodRow, ...]
    prose_summary: str
```

Required move kinds for claim focus:

- supporters
- attackers
- assumptions
- conditions
- provenance
- shared_concept
- policy_alternatives

Every `SemanticEdge` must include a domain sentence. Generic labels like
`edge`, `link`, `related`, or `connected` are not enough.

### Required Behavior

- The same report can render a heading outline, table, textual navigator, graph
  projection, and audio projection.
- Web presenters must not derive supporter/attacker membership by comparing raw
  graph rows.
- Browser code must not compute accepted extension membership or conflict
  classification.

## Contract 4 - Serialization Boundary

### Problem

Dataclasses are usable internally, but web JSON needs a stable conversion
boundary.

### Target

Add web-local serialization helpers that convert app reports to JSON-compatible
values:

```text
propstore/web/serialization.py
```

Rules:

- The serializer may inspect dataclasses, enums, tuples, paths, and primitive
  values.
- The serializer must not reinterpret domain fields.
- The serializer must preserve literal ignorance states.
- The serializer must fail loudly on unsupported values.
- The serializer must not silently stringify arbitrary objects.

If a report cannot serialize cleanly, fix the app report type. Do not add a
special-case web normalizer that hides the bad type.

## Contract 5 - Future Command Reports

Do not implement this contract in the first web slice.

When the production command journal exists, add app-owned command report
contracts:

```text
propstore/application/commands.py
propstore/application/journal.py
propstore/app/command_reports.py
```

Only then may web add:

- `/report/{command_id}`
- command progress streams
- command journal pages
- undo/redo pages

Until then, every command-report route is out of scope.
