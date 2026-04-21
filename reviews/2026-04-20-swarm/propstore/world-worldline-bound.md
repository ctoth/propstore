# world / worldline / bound supplement

Date: 2026-04-20
Reviewer: Codex execution pass
Scope: `propstore/world/bound.py` and all `propstore/worldline/` modules.

## Coverage

Fully read in this supplement:

- `propstore/world/bound.py`
- `propstore/worldline/__init__.py`
- `propstore/worldline/argumentation.py`
- `propstore/worldline/definition.py`
- `propstore/worldline/hashing.py`
- `propstore/worldline/interfaces.py`
- `propstore/worldline/resolution.py`
- `propstore/worldline/result_types.py`
- `propstore/worldline/revision_capture.py`
- `propstore/worldline/revision_types.py`
- `propstore/worldline/runner.py`
- `propstore/worldline/trace.py`

No tests were run for this supplement; it is the survey-only T0.1 artifact.

## Additional Findings

**BW-L1 - `BoundWorld` is a second public entrypoint for the forbidden support_revision AGM surface.**
- File: `C:/Users/Q/code/propstore/propstore/world/bound.py:490-578`
- The earlier `world-worldline-support.md` report identified `support_revision` as exporting AGM/DP semantics despite its package disclaimer. `BoundWorld` makes that drift part of the world API through `revision_base`, `revision_entrenchment`, `expand`, `contract`, `revise`, `revision_explain`, `epistemic_state`, and `iterated_revise`. These methods import directly from `propstore.support_revision.*`.
- This is not just a package-boundary issue inside `support_revision`: world callers can reach the AGM-shaped behavior without importing `belief_set`.
- Severity: HIGH
- Workstream mapping: Phase 4 T4.5 should update `BoundWorld` as well as `worldline/revision_capture.py`; deleting the `support_revision` AGM exports alone is incomplete while this facade remains.

**BW-B1 - `BoundWorld.iterated_revise` defaults to the false restrained operator.**
- File: `C:/Users/Q/code/propstore/propstore/world/bound.py:572`
- The default `operator="restrained"` routes worldline revision through the function reported in `belief_set.md` as byte-identical to plain revise while citing Booth-Meyer 2006. Until T1.3 implements real restrained revision or deletes the false surface, the worldline default advertises stronger semantics than it executes.
- Severity: HIGH
- Workstream mapping: Phase 1 T1.3 must include the `BoundWorld.iterated_revise` call path in its caller audit.

**WL-B7 - Unknown overrides are traced but not diagnosed as unresolved.**
- File: `C:/Users/Q/code/propstore/propstore/worldline/runner.py:51-56`
- `run_worldline` resolves overrides by concept name and silently omits any unresolved concept from `override_concept_ids`. The trace still records the author-supplied override later, so the result can show an override step that had no effect on resolution. That is distinct from the already-reported unknown target behavior because overrides are user-authored interventions.
- Severity: MEDIUM
- Suggested fix: record an unresolved-override diagnostic or fail at the authoring boundary; do not let a no-op override look applied.

**WL-B8 - Sensitivity capture has the same hash-contaminating broad exception path as argumentation/revision capture.**
- File: `C:/Users/Q/code/propstore/propstore/worldline/runner.py:198-205`
- `_capture_sensitivity` catches every `Exception` and stores `f"sensitivity analysis failed: {exc}"` in the materialized result. That result is included in `compute_worldline_content_hash`, so volatile exception text can change staleness decisions. The existing report called this out for argumentation and revision capture; sensitivity has the same failure mode.
- Severity: MEDIUM
- Suggested fix: narrow expected exceptions and store a stable typed failure code outside the hash-sensitive payload, or canonicalize the diagnostic before hashing.

**WL-B9 - `WorldlineResult.from_dict` silently drops malformed step entries.**
- File: `C:/Users/Q/code/propstore/propstore/worldline/definition.py:240-244`
- `from_dict` builds `steps` with `if isinstance(step, dict)`. Non-dict entries are ignored without an error, which can erase provenance from persisted worldline results. Other worldline parsing paths fail hard on wrong shapes, so this one is inconsistent with the boundary-hardening rule.
- Severity: MEDIUM
- Suggested fix: validate every step item and raise `ValueError` with the failing index.

**WL-B10 - `WorldlineDefinition.is_stale` treats a definition with no result as not stale.**
- File: `C:/Users/Q/code/propstore/propstore/worldline/definition.py:360-363`
- If `self.results is None`, `is_stale` returns `False`. A never-materialized worldline is therefore reported as not stale even though there is no stored content to compare. If callers use `False` as "no refresh needed", this suppresses first materialization.
- Severity: LOW-MEDIUM
- Suggested fix: either return `True` for missing results or rename/split the API so "not materialized" is distinct from "materialized and current".

**WL-B11 - Hashing falls back to `default=str` for non-JSON payloads.**
- File: `C:/Users/Q/code/propstore/propstore/worldline/hashing.py:36-42`
- The content hash accepts arbitrary non-JSON values by stringifying them. If any nested result carries an object with a memory-address-bearing repr, the same semantic worldline can hash differently across runs. `active_stance_dependencies` has a parallel `default=str` concern, but the content hash path is broader and applies to every materialized field.
- Severity: LOW-MEDIUM
- Suggested fix: require every `to_dict` payload to be JSON-native and raise on unexpected types before hashing.

**WL-L3 - Revision result types import support_revision internals directly.**
- File: `C:/Users/Q/code/propstore/propstore/worldline/revision_types.py:8-10`, `propstore/worldline/revision_capture.py:5-6`
- `worldline` result DTOs depend on `support_revision.explanation_types`, `snapshot_types`, and `state`. If Phase 4 removes AGM exports from `support_revision`, these DTOs still pin worldline to the support-revision representation. The owner boundary should be inverted: worldline should depend on stable belief/revision domain DTOs, not support-incision internals.
- Severity: MEDIUM
- Workstream mapping: Phase 4 T4.5 should move or replace these DTO imports as part of the caller update.

## Positive Observations

**POS-1 - `BoundWorld` keeps conflict registry caching instance-local.**
- File: `C:/Users/Q/code/propstore/propstore/world/bound.py:236-247`, `propstore/world/bound.py:727-742`
- The conflict input cache is explicitly instance-local and avoids sharing cached registry state across hypothetical overlay stores. This matches the comments and avoids a stale-overlay bug.

**POS-2 - Worldline parsing mostly fails hard on wrong top-level shapes.**
- File: `C:/Users/Q/code/propstore/propstore/worldline/definition.py`, `propstore/worldline/result_types.py`, `propstore/worldline/revision_types.py`
- Most `from_mapping` and `from_dict` boundaries reject non-mapping payloads with explicit `ValueError`. `WL-B9` is an exception to an otherwise good pattern.

## Summary

The unread `BoundWorld` surface confirms that the `support_revision` / AGM leak is larger than the original report showed: `BoundWorld` itself exposes the false or misplaced revision operators, and worldline result/capture types depend on support-revision internals. The unread worldline files add three more honesty/stability issues: no-op overrides are traced as if applied, sensitivity failures contaminate content hashes, and malformed persisted steps can be silently dropped.
