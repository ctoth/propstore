# Web Surface

## Goal

Define the first durable web surface without allowing the browser or route layer
to become a semantic owner.

The first surface is read-only, server-rendered, and useful with JavaScript
disabled.

## Initial Route Set

Only implement these routes in the first web slice:

```text
GET /claim/{claim_id}
GET /claim/{claim_id}.json
GET /claim/{claim_id}/neighborhood
GET /claim/{claim_id}/neighborhood.json
```

Each route accepts the same state parameters:

```text
branch
rev
reasoning_backend
strategy
semantics
set_comparison
decision_criterion
pessimism_index
praf_strategy
praf_epsilon
praf_confidence
praf_seed
include_drafts
include_blocked
show_quarantined
```

The route parses these parameters into app request dataclasses and calls
`propstore.app`. It does not assemble semantic answers from lower-level modules.

## URL State Rules

URLs for computed views must expose the state that affects the answer.

Required state:

- repository target if the server can expose more than one repo;
- branch or revision;
- render policy;
- bindings when a view depends on environment;
- focus object kind and ID.

Do not store semantic state only in:

- browser local storage;
- React state;
- TanStack Query cache;
- session variables;
- hidden form fields;
- server-global mutable state.

Those may hold presentation state only.

## HTML Rendering Rules

Every HTML page must include:

- one useful `<h1>`;
- stable heading outline;
- landmark regions;
- a visible render-policy summary;
- a visible branch/revision summary;
- copyable object IDs;
- tables for structured values;
- literal text for every unknown, vacuous, underspecified, blocked, missing, or
  not-applicable state;
- no empty table cells for semantic values;
- no semantic information available only through color, position, graph shape,
  tooltip, chart, audio, canvas, SVG, or WebGL.

The first page must work without JavaScript.

## Claim Page Shape

```text
main
  h1: Claim {display id}

  section: Summary
    status
    claim type
    statement or literal absence
    concept
    value / unit / SI value
    uncertainty
    condition regime

  section: Render State
    branch or revision
    render policy
    lifecycle visibility

  section: Provenance
    source
    provenance kind
    page/locator if known
    confidence/trust fields if present

  section: Neighborhood
    link to neighborhood page
    short literal summary

  section: Machine IDs
    logical id
    artifact id
    version id
```

If a field is absent, render the reason. Examples:

- `Value: not applicable for statement claim`
- `Uncertainty: missing`
- `Condition regime: unknown`
- `Source locator: not provided`
- `Status: blocked under current render policy`

Do not render `-`, `N/A`, blank cells, or icon-only absence.

## Neighborhood Page Shape

```text
main
  h1: Neighborhood for Claim {display id}

  section: Focus
    focus sentence
    status under current render policy

  section: Available Moves
    table of move kind, target count, sentence, URL

  section: Supporters
    table of supporting claim IDs and domain sentences

  section: Attackers
    table of attacking claim IDs and domain sentences

  section: Assumptions
    table of assumptions and status

  section: Conditions
    table of overlapping or governing conditions

  section: Provenance
    table of source/provenance links

  section: Raw Graph Projection
    table of nodes and edges
```

The "Raw Graph Projection" is still a table first. A visual graph may be added
later from the same `SemanticNeighborhoodReport`, but it is not part of the
initial slice.

## JSON Rendering Rules

JSON routes return the same app report content as the HTML route.

Rules:

- use the same app request as the HTML route;
- use the same app report as the HTML route;
- preserve literal state values;
- include no HTML;
- include no display-only CSS class names;
- fail loudly if a report cannot be serialized.

## Framework Choice

FastAPI remains the preferred target because it fits typed request/report
boundaries and can serve JSON and HTML. This workstream must still treat the
framework as a web adapter dependency.

If implementation discovers a strong reason to use Starlette directly, write
that reason into this directory before changing the target. Flask is not the
target for this workstream.

## Frontend Rule

No React in the initial slice.

React may be introduced only after:

- server-rendered claim and neighborhood pages pass their gates;
- the corresponding JSON reports are stable;
- the app-owned semantic neighborhood report exists;
- the workstream adds an explicit React shell slice with gates.

When React is introduced:

- React owns only presentation state;
- TanStack Query caches server reports but cannot be treated as source of truth;
- every mutation invalidates through app-owned command/journal identity;
- no client reducer computes epistemic meaning.

## Graph Rule

No graph library in the initial slice.

A graph projection may be added after the semantic neighborhood report exists
and the table/text navigator is already useful.

Graph libraries render `SemanticNode` and `SemanticEdge` values. They do not
derive those values.

## Chart And Audio Rule

No chart or audio projection in the initial slice.

Highcharts and sonification may be added after app-owned reports provide the
frames to render. Browser callbacks must not compute conflict pressure, support
strength, accepted extension, uncertainty class, or provenance kind from raw
claims.

Future audio projections need typed report frames such as:

```python
@dataclass(frozen=True)
class SonificationFrame:
    subject_id: str
    subject_sentence: str
    pitch_value: float | None
    timbre_kind: str
    channel: str
    duration_ms: int
    roughness: float | None
    volume: float
    state: Literal["known", "unknown", "vacuous", "blocked", "missing"]
```

Do not map multiple epistemic states to one indistinguishable sound without a
separate spoken or textual cue.

## Error Pages

Web-local error presenters map typed app failures to HTTP responses.

Rules:

- missing sidecar errors explain the required build step;
- unknown claim errors identify the requested claim;
- invalid render policy errors identify the invalid parameter;
- unexpected exceptions remain unexpected and must not be collapsed into
  "not found";
- error pages use headings and literal text;
- JSON error responses use a typed error payload.

## Static Export

Static export is out of scope for the initial slice.

When added, static export must render from the same app reports and presenters.
It must not introduce a separate report-generation path.
