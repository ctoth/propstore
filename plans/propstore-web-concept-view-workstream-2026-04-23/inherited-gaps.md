# Inherited Gaps

These gaps were left open by the first web workstream. Current status notes were
updated during the 2026-04-25 web abstraction workstream.

## Gap 1 - Repository-View Contract Mismatch

Status: resolved in current production code.

Current claim and neighborhood readers do not yet share one converged
repository-view contract.

This is not cosmetic. The web plan says computed pages must expose the state
that affects the answer. A reading surface must not accept branch or revision
state and then silently ignore it.

Required convergence in this workstream:

- one shared app-owned repository-view request;
- one honest handling path for supported and unsupported repository-view state;
- no leftover unused reading-surface fields.

Current evidence:

- `propstore/app/repository_views.py` defines `AppRepositoryViewRequest`.
- Claim, neighborhood, concept, `/claims`, and `/concepts` routes build and pass
  that shared request.
- Unsupported branch or revision state is rejected through
  `RepositoryViewUnsupportedStateError`.

## Gap 2 - Unused Reading-Surface Fields

Status: resolved for the current claim, neighborhood, concept, `/claims`, and
`/concepts` surfaces.

The current neighborhood reader carries fields that are not part of a converged
reading-surface contract.

If a field is not needed for claim, neighborhood, concept, `/claims`, or
`/concepts` reading routes, delete it instead of carrying a speculative surface
forward.

Current evidence:

- `SemanticNeighborhoodRequest` carries focus kind, focus ID, render policy,
  repository view, and limit.
- It no longer carries a speculative `bindings` field.

## Gap 3 - Manual Accessibility Is Still Open

Status: still open.

Automated checks exist, but live browser and screen-reader verification has not
been performed.

This does not block adding the next server-rendered reading pages, but it does
continue to block:

- React shell work;
- graph projection;
- chart projection;
- audio projection.

## Gap 4 - Presenter Path Has Not Converged
 
Status: resolved in current production code.

Original gap statement: `propstore/web/html.py` was the active presenter path
while `propstore/web/templates/` also existed.

Keeping both around as production surfaces is not convergence. This workstream
must pick one and delete the other.

Current evidence:

- `propstore/web/html.py` is the active production presenter path.
- `propstore/web/templates/` is not present in the current tree.
- The 2026-04-25 web abstraction workstream keeps explicit presenter functions
  and does not reintroduce templates.

## Gap 5 - Discovery Entry Routes Are Missing

Status: resolved in current production code.

The current web surface already has claim and neighborhood object routes, but
it still lacks `/claims` and `/concepts`.

That makes the surface navigable mainly for operators who already know IDs or
are arriving from the CLI.

This workstream treats those collection routes as required reading entrypoints,
not optional polish.

Current evidence:

- `propstore/web/routing.py` registers `/claims`, `/claims.json`, `/concepts`,
  and `/concepts.json`.
- `tests/test_web_claim_index_routes.py` and
  `tests/test_web_concept_index_routes.py` cover those routes.
