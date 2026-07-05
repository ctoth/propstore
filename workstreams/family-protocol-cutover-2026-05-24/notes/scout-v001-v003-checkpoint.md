# Scout V001-V003 Checkpoint Notes

Date: 2026-05-24
Scout: scout-v001-v003-typed-claim-api

## Status

DELIVERABLE WRITTEN. Report at `workstreams/family-protocol-cutover-2026-05-24/reports/scout-v001-v003-typed-claim-api.md`. All 10 sections filled. Read-only. No commit (per prompt). No blocker.

## Tree state

HEAD: `e13e302d195ddf38bbde5c965744e992ae57166b`. Slice A's ~60 modified files + 3 untracked NOT touched. Three consumer files (preference.py, praf/engine.py, world/resolution.py) NOT touched. graph_types.py NOT touched.

## Key findings recorded in deliverable

1. Deleted module `claim_metadata_value` was dual-shaped — ClaimNode branch routes through `attribute_value(key)` (dynamic bag); Claim branch routes through `getattr(claim, key)` then `getattr(claim.numeric_payload, key)`.

2. Typed columns DO exist for:
   - `sample_size`, `uncertainty` on both `ClaimNode` (graph_types.py:259,261) and `ClaimNumericPayload` (declaration.py:489,491)
   - `confidence` on `ClaimNumericPayload` (declaration.py:492) — but NOT on ClaimNode
   - `id` / `claim_id` collapse cleanly to `ClaimNode.claim_id` / `Claim.id`

3. Typed columns DO NOT exist for:
   - `opinion_belief/disbelief/uncertainty/base_rate` on Claim or ClaimNode
   - `claim_probability`, `effective_sample_size`, `source_prior_base_rate`, `source_quality_opinion`, `source` (dict shape)
   These all live in `ClaimNode.attributes` dynamic bag today.

4. Production callsites in praf/engine.py and world/resolution.py always receive `ClaimNode` (via `SharedAnalyzerInput.claims_by_id: dict[str, ClaimNode]` at argumentation.py:71). Claim branch is test-only.

5. Provenance is constructed at the consumer site (preference/engine wrap floats in `Opinion(...)` / `NoCalibration(...)` with explicit `ProvenanceStatus`). Raw extraction layer doesn't need to carry provenance; rewrite must preserve `None` returns so vacuous fallback continues.

6. **REQUIRES Q DECISION** marked in report for: (a) whether ClaimNode should sprout typed `opinion_*` and `confidence` fields (recommended option 2b in hazard #2), and (b) whether dict-shaped `source`/`source_prior_base_rate`/`source_quality_opinion` should be deferred to a later slice.

7. No collision with Slice A's uncommitted work — disjoint file sets.

## Notable hazard flagged

Hazard #6: `ClaimNode.attributes` may carry frozen tuple-of-pairs (per `_normalize_pairs` at graph_types.py:281). The deleted module's `_unfreeze_metadata_value` thawed those back to dicts. The simple `claim.attribute_value("source")` rewrite skips that thaw — if attributes are ever frozen, `isinstance(source, dict)` guard breaks silently. Coder MUST check.

## Done.
