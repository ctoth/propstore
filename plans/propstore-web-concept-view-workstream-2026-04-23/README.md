# propstore.web Concept View Workstream - 2026-04-23

## Purpose

Turn the concept-view decision into an executable workstream.

This workstream extends the first `propstore.web` reading surface with:

- server-rendered and JSON concept pages backed by a typed app-owned concept
  view report; and
- server-rendered and JSON collection entrypoints for `/concepts` and
  `/claims`, so the web surface is navigable without starting from a known ID.

It also keeps the inherited unfinished work from the first web slice on the
active control surface, instead of pretending the claim/neighborhood surface is
fully converged when key repository-state and manual accessibility gates remain
open.

## Preconditions And Current State

Implemented already:

- typed app-owned claim view report;
- typed app-owned semantic neighborhood report;
- server-rendered and JSON claim routes;
- server-rendered and JSON neighborhood routes;
- focused demo fixture and automated accessibility tests;
- next-surface decision selecting concept view.

Still unfinished:

- no typed app-owned concept page report exists;
- current concept show surface is `ConceptShowReport(rendered: str)`, which is
  CLI/YAML-oriented and not a durable web/API contract;
- claim and neighborhood repository-state handling has not converged;
- manual browser and screen-reader verification has not been performed.

## Source Material

- `plans/propstore-web-workstream-2026-04-23/README.md`
- `plans/propstore-web-workstream-2026-04-23/next-surface-decision.md`
- `plans/propstore-web-workstream-2026-04-23/manual-accessibility-notes.md`
- `propstore-web-gui-vamp-2026-04-19.md`
- `propstore/app/concepts/*`
- `propstore/cli/concept/*`
- `propstore/web/*`

## Target

Add the next reading surfaces:

```text
GET /claims
GET /claims.json
GET /concepts
GET /concepts.json
GET /concept/{concept_id}
GET /concept/{concept_id}.json
```

The collection pages provide discovery and navigation entrypoints. The concept
page provides the next object-level durable reading surface.

The target is not a concept YAML dump in a browser. The target is a durable,
typed, report-driven concept reading page that can explain:

- what concept is in focus;
- what kind of concept it is;
- what its form and unit discipline are;
- which visible claims instantiate or refer to it;
- what value, uncertainty, and provenance surface is available around it;
- which claim pages a reader should traverse next.

The target is also not an ID-only web surface. `/claims` and `/concepts` should
be treated as primary entrypoints for readers who do not already know a claim
or concept handle.

## Non-Negotiable Rules

- `propstore.web` remains a presentation adapter only.
- `propstore.app` owns typed concept view meaning.
- No concept page route may import below `propstore.app` for semantic behavior.
- No concept HTML presenter may infer claim visibility, claim grouping,
  provenance kind, or value-class semantics from raw rows.
- Do not add React, graph, chart, audio, or mutation work in this workstream.
- Do not leave the current claim/neighborhood repository-state mismatch in
  place while adding a third inconsistent view surface.
- Do not preserve both dead template surfaces and active string presenters in
  parallel. Pick one production presenter path and delete the unused one.

## Workstream Files

- `README.md`: scope, prerequisites, and completion criteria.
- `app-contracts.md`: app-owned repository-view and concept-view contracts.
- `web-surface.md`: route, URL-state, and page-shape rules.
- `execution-slices.md`: ordered implementation slices and gates.
- `verification.md`: test, type, search, and manual verification requirements.
- `inherited-gaps.md`: unfinished work carried forward from the first web slice.

## Completion Criteria

This workstream is complete when:

- `propstore.app` owns a typed `ConceptViewRequest` and `ConceptViewReport`.
- app-owned repository-view state is shared across claim, neighborhood, and
  concept reading surfaces.
- current unused or inconsistent repository-view fields are deleted.
- `propstore.web` serves server-rendered and JSON concept routes from the same
  app report.
- `propstore.web` serves server-rendered and JSON `/claims` and `/concepts`
  entry routes from app-owned list/search reports.
- the concept page renders literal ignorance and absence states.
- the entry routes support useful discovery without requiring command syntax or
  prior IDs.
- the concept page links into the claim and neighborhood reading surfaces.
- dead or unused production presenter paths in `propstore.web` are deleted.
- focused logged pytest batches and `uv run pyright propstore` pass.
- import-boundary and no-frontend searches remain clean.
- manual accessibility notes are updated honestly with what was and was not
  verified.

## Out Of Scope

- React shell work.
- Graph projection.
- Chart projection.
- Audio projection.
- Source, worldline, and conflict pages.
- `/report/{command_id}` pages.
- SSE command streams.
- Mutating concept workflows in the browser.

Those may become future workstreams. They are not opened here.
