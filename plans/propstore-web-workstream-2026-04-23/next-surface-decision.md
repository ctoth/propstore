# Next Surface Decision

Decision: concept view.

## App-Owned Contract First

The next surface must start in `propstore.app` with a typed
`ConceptViewRequest` and `ConceptViewReport`.

The report should include:

- focus concept identity, canonical name, domain, definition, form, and unit;
- concept state using explicit literals for known, unknown, blocked, missing,
  vacuous, underspecified, and not applicable where each applies;
- render-policy summary;
- claim inventory grouped by claim type and visibility under policy;
- value/uncertainty summary for visible parameter or measurement claims;
- source/provenance summary for claims attached to the concept;
- semantic neighborhood link targets for claims sharing the concept;
- machine IDs and logical IDs needed for reproducible URLs.

## Why This Surface

The first claim and neighborhood pages already prove object reading and
semantic navigation. A concept view is the smallest next axis that uses those
pages without introducing visual graph, chart, audio, command-journal, or
mutation prerequisites.

## Explicit Non-Decisions

Not selected now:

- source view;
- worldline view;
- conflict view;
- static export;
- React shell foundation;
- graph projection;
- chart projection;
- audio projection.

React, graph, chart, and audio work remain blocked until their app-owned
contracts exist and the manual accessibility gates are actually performed or
explicitly deferred by the user.
