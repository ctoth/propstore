# WS-M Closure Report

Workstream id: WS-M
Closing implementation commit: `623f892d`

## Findings Closed

- T4.1 / Cluster M HIGH-1: gunray trace crosses the propstore boundary; sidecar rehydrates source rules, source facts, and arguments.
- T4.2 / Cluster M HIGH-3: fake SHA-1 Trusty URI templating deleted; SHA-256 `ni:///` compute/verify gate added.
- T4.3 / Cluster M HIGH-4: one-way PROV-O JSON-LD export added for typed provenance records.
- T4.4: repository import writes a provenance note on the import commit.
- T4.5 / MED-2: `compose_provenance` preserves causal operation order.
- T4.6 / MED-1: `WhySupport.subsumes` renamed to `is_subsumed_by`.
- T4.7: label combination preserves semiring polynomial coefficients.
- T4.8 / D-20: production digest-slice identity audit is green; identity paths store full hashes.
- Cluster M HIGH-2: source promotion writes a provenance note on the promote commit.
- Cluster M MED-3: witness dedupe uses the single `_witness_key` order.
- Cluster M MED-6: WS-M consumes WS-CM micropub `ni:///sha-256` identity unchanged.

## Red Tests First

The initial WS-M red run was `logs/test-runs/WS-M-red-20260430-014826.log`: 22 failed, 1 passed. Failures covered missing `propstore.provenance.trusty`, missing `propstore.provenance.prov_o`, truncated digest identity sites, causal-order sorting, witness-key mismatch, old WhySupport naming, polynomial coefficient collapse, missing grounded-bundle sidecar inputs, missing gunray budget/default trace behavior, and missing repository-import/promote notes.

## Logged Tests

- `logs/test-runs/WS-M-step1-rerun-20260430-015614.log` — 6 passed.
- `logs/test-runs/WS-M-step2-20260430-015821.log` — 5 passed.
- `logs/test-runs/WS-M-step3-20260430-015910.log` — 4 passed.
- `logs/test-runs/WS-M-step4-20260430-020008.log` — 2 passed.
- `logs/test-runs/WS-M-step5-rerun-20260430-020121.log` — 1 passed.
- `logs/test-runs/WS-M-step6-rerun-20260430-020437.log` — 37 passed.
- `logs/test-runs/WS-M-step7-20260430-020549.log` — 18 passed.
- `logs/test-runs/WS-M-step8-20260430-020732.log` — 12 passed.
- `logs/test-runs/WS-M-preclose-20260430-020753.log` — 22 passed.
- `logs/test-runs/WS-M-final-targeted-20260430-021537.log` — 23 passed.
- `logs/test-runs/WS-M-full-failure-set-rerun-20260430-023309.log` — 9 passed; covers the post-full regression fixes for causal operation order, JSON sidecar input persistence, reasoning demo build/run, and contract manifest drift.
- `logs/test-runs/WS-M-full-rerun-20260430-023410.log` — 3473 passed, 2 skipped.

Static gates:

- `uv run pyright propstore` — 0 errors, 0 warnings.
- `uv run lint-imports` — 5 contracts kept, 0 broken.

## Property Gates

Hypothesis gates added for SHA-256 `ni` URI round-trip, WhySupport inclusion semantics, and polynomial coefficient preservation through `combine_labels`.

## Files Changed

Core provenance, URI wrappers, PROV-O export, full-hash identity sites, grounder/bundle/sidecar persistence, repository import, source promote, source-branch contract manifests, and WS-M tests were changed. `docs/gaps.md`, this WS file, and the workstream index record closure.

## Remaining Risks

PROV-O is shape-validated only; full W3C OWL/SHACL validation remains pending on the external PROV spec retrieval noted in the workstream. Nanopublication three-graph emission, SWP signing, typed provenance tables for sidecar claim rows, and additional semiring projections remain successor workstreams explicitly outside WS-M.
