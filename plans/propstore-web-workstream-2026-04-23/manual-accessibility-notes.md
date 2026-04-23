# Manual Accessibility Notes

Date: 2026-04-23

## Scope

Pages covered by Slice 7:

- `GET /claim/{claim_id}`
- `GET /claim/{claim_id}/neighborhood`
- HTML error responses for the same route family

## Automated Checks Added

`tests/test_web_accessibility.py` checks:

- exactly one useful `h1` on claim, neighborhood, and error pages;
- non-empty page titles that name the focus object or error;
- one `main` landmark;
- section headings for major page areas;
- table headers for neighborhood tables;
- no blank data cells in rendered neighborhood tables;
- meaningful link text;
- literal rendering of `unknown`, `vacuous`, `blocked`, `missing`,
  `not applicable`, and `unavailable` states;
- absence of CSS hooks that would make hover or pointer position required.

## Manual Checks Performed

No browser or screen-reader manual checks were performed in this execution
environment.

I did not verify:

- JavaScript-disabled page loading in a browser;
- keyboard-only navigation in a browser;
- heading navigation in a screen reader;
- landmark navigation in a screen reader;
- table navigation in a screen reader;
- NVDA with Firefox;
- NVDA with Chrome;
- Windows Narrator with Edge;
- blind-operator comprehension from live screen-reader output;
- sighted-collaborator comprehension without color, graph position, hover, or
  tooltip cues.

## Current Manual-Gate Status

The first web surface remains eligible for server-rendered claim and
neighborhood work. React, graph, chart, and audio slices must not start until
the manual checks above are actually performed or explicitly deferred by the
user.
