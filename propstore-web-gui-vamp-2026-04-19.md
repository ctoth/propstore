# propstore.web GUI Vamp Notes - 2026-04-19

## Status

Exploratory notes only.

This is not a workstream, not a build plan, and not an implementation commitment.
It is a place to vamp on the shape of `propstore.web`: what it wants to be,
what would make it serious, what would make it beautiful, and what questions
are worth exploring before turning anything into scoped work.

## Core Frame

Propstore is an epistemic operating system. Right now it is text-only. It has
an excellent CLI, but it wants a GUI. The web surface should not be "the CLI in
a browser" and it should not be a dashboard. It should be the graphical shell
for the epistemic OS.

Useful analogy:

```text
propstore CLI     -> shell
propstore.app     -> system calls / application services
knowledge repo    -> filesystem
sidecar           -> index / compiled runtime
command journal   -> process/history log
worldlines        -> saved workspaces / reproducible sessions
branches          -> alternate epistemic states
render policy     -> display policy / view mode
argumentation     -> reasoner / scheduler of belief
propstore.web     -> graphical shell / desktop environment
```

The CLI remains the expert operating console. The web GUI exists to make the
system legible and shareable to people who are not CLI-native, and to make
interactions possible that text-only interfaces cannot carry: synchronized graph
and provenance navigation, sonification, policy comparison, tactile/exportable
charts, guided conflict traversal, and rich exploration surfaces.

## Design Principle

The client owns attention and arrangement. `propstore.app` owns truth.

React, if used, is not the reasoning engine and not a domain store. It is a GUI
projection layer over typed `propstore.app` reports and command state.

Allowed client state:

- focused pane
- selected node or row
- open windows and panel layout
- current graph viewport
- command palette query
- audio playback position
- active sonification mapping
- keyboard navigation cursor
- local draft input before submission

Forbidden client-owned state:

- canonical claim status
- conflict classification
- accepted extension
- provenance facts
- branch state
- source lifecycle state
- merge result
- persisted command result
- anything that could disagree with `propstore.app`

Working slogan:

```text
React owns experience.
propstore.app owns meaning.
```

## Accessibility Is Native

The target user is not an abstraction. This tool is being designed by and for a
blind expert operator, and should also be shareable with sighted and non-CLI
users. Accessibility is not a post-pass or compliance layer. It is the native
I/O model of the GUI.

A visual graph with ARIA patched onto it is not enough. The primary object must
be a semantic graph/navigation model, with multiple projections:

- visual graph
- structured keyboard navigator
- text/prose explanation
- tables
- sonified traversal
- exportable/shareable report

A graph surface is only acceptable if the semantic navigator still works when
the visual projection is removed.

Non-negotiables:

- Every visual graph has a first-class nonvisual navigator.
- Every node and edge has a domain sentence, not a generic label.
- Every screen has a useful heading outline.
- Major regions are reachable by landmarks and shortcuts.
- Every command has a stable result/report page.
- Every mutation is explicit, journaled, and reviewable before commit.
- Every chart has a table and textual takeaway.
- Every conflict can be traversed structurally: claim, counterclaim,
  conditions, provenance, policy result.
- Unknown, vacuous, underspecified, and blocked states are spoken honestly.
- No canvas, SVG, or WebGL surface is the only way to inspect anything.

## Product Shape, Without Calling It A Product

There is no commercial product brief here. There is a person building a serious
tool that is not quite like anything else. The web surface exists to share it,
to explore it, and to make it amazing as an instrument.

Three modes seem useful:

### Shareable Reading Mode

For people who are not CLI-native.

Stable URLs, beautiful documents, no command grammar required:

- `/concept/{id}`
- `/claim/{id}`
- `/source/{id}`
- `/worldline/{id}`
- `/conflict/{id}`
- `/merge/{id}`
- `/report/{command_id}`

These pages explain what the system knows, why it believes it, what disagrees,
and where evidence came from. They should be durable knowledge artifacts:
headings, landmarks, print/export, tables, citations, copyable IDs, and stable
links.

### Guided Exploration Mode

For safe movement around the epistemic structure.

Start at a claim, concept, source, or worldline. Then choose moves:

- Why?
- What disagrees?
- What supports this?
- What attacks this?
- What depends on this?
- What changes under another policy?
- What is the provenance?
- What happens across branches?
- What does this sound like?

The user should not need to know `pks world ...` command forms to make these
moves.

### Expert Web Workbench

For powerful GUI operation:

- command palette
- branch/source/status panels
- build/validate/run command streams
- graph navigator
- sonification controls
- Highcharts quantitative views
- worldline diff explorer
- conflict debugger
- ATMS/revision explorer

This is where React is easiest to justify. It is not "pages"; it is an
interactive graphical shell.

## GUI Objects

Design around OS-like objects, not around CLI commands:

- Repository
- Branch
- Source
- Claim
- Concept
- Context
- Stance
- Conflict
- Argument
- Worldline
- Command
- Policy
- Evidence
- Revision

Each important object should have:

- canonical document view
- inspector view
- graph projection
- command menu
- provenance trail
- share URL
- keyboard shortcuts
- accessible summary

## Visual And Interaction References

The vibe should be closer to:

- Smalltalk browser
- HyperCard
- Mathematica notebook
- NeXTSTEP workspace
- early Mac Finder
- expert scientific workbench
- serious audio-capable instrument

And less like:

- SaaS dashboard
- CRUD admin
- marketing site
- graph-viz toy
- Notion clone
- Linear clone

The beauty should come from orientation, not decoration. The user should always
know:

- where they are in the epistemic structure
- why a result holds
- what could change it
- what evidence supports it
- what disagrees
- what command would move the system

## Backend Shape

`propstore.web` should be a presentation adapter over `propstore.app`, peer to
`propstore.cli`.

It owns:

- HTTP routing
- auth/session if needed
- request parsing
- content negotiation
- response rendering
- static assets
- command progress streams
- browser interaction affordances

It does not own:

- compiler workflows
- repository mutation semantics
- source promotion/finalization semantics
- world/ATMS/revision semantics
- sidecar SQL policy
- claim/concept/context mutation logic
- merge semantics

If the web surface needs behavior that does not exist in `propstore.app`, add
or extract the typed `propstore.app` owner API first. Do not punch through from
web routes into lower layers just because a view needs data.

Candidate backend:

```text
FastAPI
  JSON endpoints over typed propstore.app reports
  HTML/report presenters where useful
  SSE command streams keyed by command_id
```

FastAPI is attractive because propstore already wants typed request/report
boundaries. Flask is viable but makes more schema/API contract work manual.
Starlette is lower-level and would likely become hand-rolled FastAPI.

## Frontend Shape

There are two plausible directions:

### A. React Workbench With Document-Quality Views

Use React as the GUI shell:

- Vite + React + TypeScript
- TanStack Query for server report caching/invalidation
- React Flow or a commercial graph library for graph projections
- Highcharts for quantitative charts and sonification
- React Aria / Ariakit / Radix only where native controls are insufficient
- plain CSS or CSS modules with serious design tokens

Avoid:

- Next.js
- Redux
- client-side epistemic stores
- optimistic semantic truth
- GraphQL unless REST becomes genuinely painful
- component libraries that fight native semantics

This is defensible if the web GUI is a serious graphical shell, not a set of
mostly static documents.

### B. Hybrid HTML + React Islands

Server-render the shareable document/report pages and use React for the
workbench/exploration routes.

This keeps durable knowledge artifacts close to HTML and limits frontend code,
but it risks having two UI idioms. It is best if reading/reporting stays more
important than workbench operation.

Current leaning from the conversation: if propstore is getting a GUI shell, eat
the React tax deliberately, but keep React server-authoritative and domain-thin.

## Graph Libraries To Explore

No library removes the need for a propstore-native semantic navigator. Libraries
can help render, focus, and announce. They cannot know what a propstore edge
means.

Promising candidates:

- GoJS: strong keyboard and screen-reader documentation, focus navigation,
  virtual pointer support, custom descriptions. Commercial.
- yFiles for HTML: strong graph/layout product with ARIA/live-region demo and
  explicit screen-reader caveats. Commercial.
- React Flow: good current accessibility docs, focusable nodes/edges, keyboard
  operation, auto-pan on focus, ARIA descriptions, live regions. React-native.
- Ogma: serious graph investigation library with an accessibility example using
  menu, graph traversal, and camera modes. Commercial/proprietary ecosystem.
- Cytoscape.js: excellent open-source graph engine, but not an accessibility
  solution by itself. Would require custom navigator, text outline, search,
  roving focus, live region, tables, and export.
- Sigma.js: good for large WebGL networks, weaker fit for a11y-first semantic
  graph exploration unless graph size forces it.

Possible split:

- argument trees / dependency DAGs / workbench flows: React Flow or GoJS
- dense claim/concept networks: Cytoscape.js with custom navigator, or yFiles /
  Ogma if commercial is acceptable
- quantitative charts: Highcharts

## Highcharts And Sonification

Highcharts is attractive for quantitative projections because its accessibility
work is serious relative to most chart libraries, and because sonification can
be first-class rather than decorative.

Good uses:

- fragility and sensitivity charts
- acceptance probability distributions
- uncertainty views
- worldline time-series or comparison views
- build/validation diagnostics over time
- source/corpus composition charts
- parameter/value comparisons across claims
- branch deltas

For propstore, sonification should be semantic, not merely "play the chart".

Possible mappings:

```text
Pitch          -> resolved value
Timbre         -> provenance kind
Stereo channel -> branch or rival claim
Duration       -> uncertainty width
Roughness      -> conflict pressure
Volume         -> support strength
Pause/break    -> missing, vacuous, unknown, or blocked state
```

This is one of the key reasons `propstore.web` should exist. The CLI can print
tables and structured results. It cannot naturally let someone hear uncertainty,
conflict, branch movement, or worldline changes.

## Semantic Navigator

This is probably the real core, more important than the visual graph library.

Example navigation frame:

```text
You are on claim X.
Claim X is supported by 3 claims, attacked by 2 claims, and depends on 4 assumptions.
Current render policy: grounded, drafts hidden, quarantined hidden.
Status: accepted.
Primary conflict: claim Y under overlapping condition C.
Available moves:
  parents
  children
  attackers
  supporters
  shared concept
  same source
  same condition regime
  provenance
  policy alternatives
  worldline impact
```

The navigator should expose graph movement as meaningful commands, not as
pixel movement:

- next attacker
- previous attacker
- first supporter
- next assumption
- explain edge
- jump to source
- compare policy
- expand provenance
- show rivals
- sonify neighborhood
- pin to inspector
- open as report

This could become the common model behind visual, textual, tabular, and audio
projections.

## Possible Package Shape

Sketch only:

```text
propstore/web/
  __init__.py
  app.py              # FastAPI construction
  api/
    claims.py
    concepts.py
    world.py
    worldlines.py
    commands.py
    reports.py
  presenters/
    html.py
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

Keep Python package `__init__.py` shallow. Do not import unrelated command
families just to start the web server.

## Questions To Explore

- Is the first surface a shareable read-only report, or the workbench shell?
- Does `propstore.app` already expose enough typed reports for a credible
  browsing GUI, or does the web design force app-layer extraction first?
- Should the semantic navigator be a first-class `propstore.app` report family?
- What graph library is acceptable given licensing and accessibility needs?
- How far can Highcharts sonification go before propstore needs its own audio
  projection model?
- What is the minimal object set for a first impressive demo: claim, concept,
  conflict, source, worldline?
- How should render policy appear globally in the shell?
- What belongs in URL state versus local workspace state?
- What does a command journal page look like for non-CLI users?
- How should a blind-native graph traversal teach sighted collaborators what
  the system is doing?
- Do we need static HTML export for sharing outside a running server?
- What is the auth story: local single-operator, shared lab, or public read-only?

## Candidate First Demo

Not a plan. Just a possible object to think with.

Build a read/explore surface for one conflict:

- canonical conflict URL
- two or more rival claims
- condition overlap explanation
- provenance for each claim
- current render policy and result
- supporters/attackers as semantic navigator moves
- visual graph projection
- node/edge table
- Highcharts view for value/uncertainty if numeric
- sonification of rival values and uncertainty
- shareable report

If this surface feels serious, accessible, and beautiful, the architecture is
probably pointed in the right direction.

## Notes From External Library Recon

Highcharts:

- Accessibility module supports screen-reader descriptions, keyboard
  navigation, ARIA roles/attributes, linked descriptions, data export, and data
  table flows.
- Their docs emphasize visible descriptions as beneficial for everyone, not
  only hidden screen-reader text.
- Their compliance page is appropriately honest: Highcharts helps create
  accessible charts, but final compliance depends on the developer's content,
  colors, configuration, and custom functionality.

Graph libraries:

- GoJS and yFiles have the strongest explicit graph accessibility stories found
  so far.
- React Flow has good built-in keyboard/screen-reader features and is attractive
  if React is already accepted for the workbench.
- Cytoscape.js is strong for graph rendering and algorithms, but propstore would
  own accessibility.
- Data Navigator is worth reading as a conceptual influence: it treats
  visualization accessibility as a navigable semantic structure problem rather
  than an SVG-labeling problem.

## Open Taste Question

What should this feel like?

Current answer:

```text
An epistemic instrument, not a dashboard.
A graphical shell, not a web clone of the CLI.
A blind-native workbench with visual projections, not an accessible version of
a sighted-only app.
```

