# Web Surface

## Goal

Define the concept reading surface without allowing routes or presenters to
become semantic owners.

The concept page remains read-only, server-rendered, and useful with
JavaScript disabled.

## Route Set

This workstream adds:

```text
GET /claims
GET /claims.json
GET /concepts
GET /concepts.json
GET /concept/{concept_id}
GET /concept/{concept_id}.json
```

The collection routes render app-owned list/search reports. The concept object
routes render one parsed app request and one app report.

## Collection Entry Shapes

### `/claims`

`/claims` is the claim discovery page.

It should support query-parameter filtering over app-owned request types, for
example:

- `concept`
- `limit`
- `q` if the claim search route is unified into the same page
- existing render-policy flags

The page should provide:

- a useful heading;
- current filter summary;
- a table of visible claims;
- claim type;
- value display;
- condition display;
- status summary;
- links to claim pages.

### `/concepts`

`/concepts` is the concept discovery page.

It should support query-parameter filtering over app-owned request types, for
example:

- `domain`
- `status`
- `limit`
- `q` if the concept search route is unified into the same page

The page should provide:

- a useful heading;
- current filter summary;
- a table of concepts;
- canonical name;
- status;
- links to concept pages.

## URL State Rules

The concept page must expose the state that affects the answer.

Required URL state:

- focus concept handle;
- branch or revision, once repository-view support exists;
- render policy fields already used by claim and neighborhood reading pages.

Do not introduce hidden browser-only state for semantic answers.

If branch/revision support is not implemented yet at a given slice, the route
must reject it honestly and consistently through the shared repository-view
contract. It must not accept and silently ignore it.

## Page Shape

```text
main
  h1: Concept {display name}

  section: Summary
    canonical name
    concept kind
    domain
    definition
    form
    unit / dimension discipline
    concept state

  section: Render State
    repository state
    render policy

  section: Claim Inventory
    grouped table of visible claims by claim type
    visibility and blocked-state literals where needed
    links to claim pages

  section: Value Summary
    parameter/measurement coverage
    value summary sentence
    uncertainty summary sentence

  section: Provenance Summary
    source coverage
    provenance coverage
    literal missing or mixed states

  section: Related Reading
    claim links
    neighborhood links when appropriate

  section: Machine IDs
    concept id
    logical id
    artifact id
    version id
```

## Rendering Rules

- exactly one useful `<h1>`;
- non-empty `<title>`;
- one `main` landmark;
- section headings for major regions;
- tables with headers for structured inventories;
- no semantic blank cells;
- literal rendering for `unknown`, `blocked`, `missing`, `vacuous`,
  `underspecified`, and `not applicable` where applicable;
- no semantic information available only through color, position, icon, chart,
  graph, tooltip, canvas, SVG, or WebGL.

## JSON Rules

- JSON route returns the same app report content as HTML;
- no HTML in JSON;
- no CSS-class leakage;
- same literal state labels as HTML;
- fail loudly on unsupported values.

## Presenter Convergence

Status: resolved in current production code.

Current production rendering is in `propstore/web/html.py`.
`propstore/web/templates/` is not present in the current tree.

The converged surface keeps explicit presenter functions. A future move to a
template language would be a replacement workstream: change the presenter
interface, update every caller, and delete the old presenter path in the same
slice.

Do not keep both explicit presenter functions and templates as production
surfaces.

## Explicit Non-Goals

- no React;
- no graph projection;
- no chart or audio projection;
- no mutation form;
- no browser-side grouping or summarization logic.
