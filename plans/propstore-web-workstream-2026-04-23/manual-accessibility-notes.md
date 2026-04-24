# Manual Accessibility Notes

Date: 2026-04-23

## Scope

Pages covered by Slice 7:

- `GET /claim/{claim_id}`
- `GET /claim/{claim_id}/neighborhood`
- `GET /concept/{concept_id}`
- HTML error responses for the same route family

## Automated Checks Added

`tests/test_web_accessibility.py` checks:

- exactly one useful `h1` on claim, neighborhood, concept, and error pages;
- non-empty page titles that name the focus object or error;
- one `main` landmark;
- section headings for major page areas;
- table headers for neighborhood and concept tables;
- no blank data cells in rendered neighborhood and concept tables;
- meaningful link text;
- literal rendering of `unknown`, `vacuous`, `blocked`, `missing`,
  `not applicable`, and `unavailable` states;
- absence of CSS hooks that would make hover or pointer position required.

## Manual Checks Performed

No browser or screen-reader manual checks were performed in this execution
environment.

I did not verify:

- JavaScript-disabled page loading in a browser;
- JavaScript-disabled loading of the concept page in a browser;
- keyboard-only navigation in a browser;
- keyboard-only navigation across concept claim tables and related-claim links;
- heading navigation in a screen reader;
- landmark navigation in a screen reader;
- table navigation in a screen reader, including concept claim-group tables;
- NVDA with Firefox;
- NVDA with Chrome;
- Windows Narrator with Edge;
- blind-operator comprehension from live screen-reader output;
- sighted-collaborator comprehension without color, graph position, hover, or
  tooltip cues.

## Current Manual-Gate Status

The current server-rendered web surface now includes claim, neighborhood, and
concept pages. React, graph, chart, and audio slices must not start until the
manual checks above are actually performed or explicitly deferred by the user.
