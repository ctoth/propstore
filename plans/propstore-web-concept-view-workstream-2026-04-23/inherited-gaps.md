# Inherited Gaps

These gaps were left open by the first web workstream and remain active here.

## Gap 1 - Repository-View Contract Mismatch

Current claim and neighborhood readers do not yet share one converged
repository-view contract.

This is not cosmetic. The web plan says computed pages must expose the state
that affects the answer. A reading surface must not accept branch or revision
state and then silently ignore it.

Required convergence in this workstream:

- one shared app-owned repository-view request;
- one honest handling path for supported and unsupported repository-view state;
- no leftover unused reading-surface fields.

## Gap 2 - Unused Reading-Surface Fields

The current neighborhood reader carries fields that are not part of a converged
reading-surface contract.

If a field is not needed for claim, neighborhood, concept, `/claims`, or
`/concepts` reading routes, delete it instead of carrying a speculative surface
forward.

## Gap 3 - Manual Accessibility Is Still Open

Automated checks exist, but live browser and screen-reader verification has not
been performed.

This does not block adding the next server-rendered reading pages, but it does
continue to block:

- React shell work;
- graph projection;
- chart projection;
- audio projection.

## Gap 4 - Presenter Path Has Not Converged

`propstore/web/html.py` is the active presenter path, but `propstore/web/templates/`
also exists.

Keeping both around as production surfaces is not convergence. This workstream
must pick one and delete the other.

## Gap 5 - Discovery Entry Routes Are Missing

The current web surface already has claim and neighborhood object routes, but
it still lacks `/claims` and `/concepts`.

That makes the surface navigable mainly for operators who already know IDs or
are arriving from the CLI.

This workstream treats those collection routes as required reading entrypoints,
not optional polish.
