# WS-E Closure Report

Workstream: WS-E source-promote correctness
Closing implementation commit: `34d0a459`
Status file: `reviews/2026-04-26-claude/workstreams/WS-E-source-promote.md`

## Findings Closed

- T3.5 / Cluster A HIGH-1 / Codex 1.14: promote justification references must resolve to the current promotion batch or the captured primary-branch artifact snapshot.
- T3.6 / Cluster A HIGH-3: conflicting source concept proposals classify as attacks by default.
- T3.7 / Cluster A HIGH-4: concept alias collisions raise instead of silently merging.
- T3.8 / Cluster A HIGH-5: contextless finalized claims block finalize through `micropub_coverage_errors`.
- T1.6 / Cluster A HIGH-2 source-promote half: promote consumes WS-C atomicity and WS-Q-cas branch-head CAS behavior.
- Cluster A MED M1/M2/M4/M5/M7: stance target guard, transaction SHA lifetime, proposed-by-default concept imports, local-handle collision blocking, and no in-place promoted-claim mutation.
- Adjacent datetime/rule validation: source extraction provenance timestamps are timezone-aware and justification rule fields are validated.

## Tests Written First

- `tests/test_source_promote_dangling_refs.py` failed because the old filter admitted source-local-only justification references and did not model the valid master-reference case.
- `tests/test_alignment_default_classification.py` failed because conflicting proposals defaulted to `non_attack`; the same file covers the dead shared-reference branch.
- `tests/test_alias_collision_rejected.py` failed first at import time because no `ConceptAliasCollisionError` existed, then passed after collision detection replaced `setdefault`.
- `tests/test_finalize_micropub_required.py` failed because finalize returned `ready` while contextless claims skipped micropub composition.
- `tests/test_transaction_commit_sha_lifetime.py` failed because finalize, promote, and repository import read transaction SHAs after context exit.
- `tests/test_concept_import_status_proposed.py` failed because imported concepts defaulted to `accepted`.
- `tests/test_local_handle_collision_blocks_commit.py` failed because repository import warnings did not block commit.
- `tests/test_promote_claim_immutability.py` failed because promote used `claim.clear()` / `claim.update()`.
- `tests/test_extraction_provenance_aware_timestamps.py` and `tests/test_justification_rule_kind_validated.py` failed because source extraction used naive UTC and accepted bogus rule kinds.
- `tests/test_workstream_e_done.py` failed against the open workstream status before closeout.

## Logged Verification

- Red dangling refs: `logs/test-runs/WS-E-dangling-refs-red-20260428-025133.log`
- Green dangling refs: `logs/test-runs/WS-E-dangling-refs-green-20260428-025242.log`
- Red alignment defaults: `logs/test-runs/WS-E-alignment-red-20260428-025453.log`
- Green alignment defaults: `logs/test-runs/WS-E-alignment-green-20260428-025556.log`
- Red alias collision: `logs/test-runs/WS-E-alias-red-20260428-025704.log`
- Green alias collision: `logs/test-runs/WS-E-alias-green-20260428-025754.log`
- Red required micropubs: `logs/test-runs/WS-E-micropub-required-red-20260428-025932.log`
- Green required micropubs: `logs/test-runs/WS-E-micropub-required-green-20260428-030116.log`
- Red commit SHA lifetime: `logs/test-runs/WS-E-commit-sha-red-20260428-030247.log`
- Green commit SHA lifetime: `logs/test-runs/WS-E-commit-sha-green-20260428-030529.log`
- Red concept import status: `logs/test-runs/WS-E-import-status-red-20260428-030637.log`
- Green concept import status: `logs/test-runs/WS-E-import-status-green-20260428-030720.log`
- Red local handle collision: `logs/test-runs/WS-E-local-handle-red-20260428-030841.log`
- Green local handle collision: `logs/test-runs/WS-E-local-handle-green-20260428-030934.log`
- Red claim immutability: `logs/test-runs/WS-E-claim-immutability-red-20260428-031026.log`
- Green claim immutability: `logs/test-runs/WS-E-claim-immutability-green-20260428-031119.log`
- Red provenance/rule validation: `logs/test-runs/WS-E-step7-red-20260428-031420.log`
- Green provenance/rule validation: `logs/test-runs/WS-E-step7-green-20260428-031653.log`
- Targeted preclose: `logs/test-runs/WS-E-targeted-preclose-20260428-031736.log` (`18 passed`)
- Sentinel red: `logs/test-runs/WS-E-sentinel-red-20260428-032058.log`
- Property companion: `logs/test-runs/WS-E-properties-20260428-032542.log` (`2 passed`)
- Pyright: `uv run pyright propstore` passed with 0 errors.
- Import linter: `uv run lint-imports` passed with 4 contracts kept and 0 broken.

Final sentinel, targeted acceptance, and full-suite logs are recorded in the final evidence commit after this report exists.

## Property Gates

- Branch-head linearizability is covered by WS-Q-cas properties and consumed here: `tests/test_branch_head_cas_properties.py`.
- Re-promote generated content is covered by `tests/test_source_promote_properties.py::test_ws_e_generated_repromote_preserves_claim_artifacts`.
- Generated source-local fields cannot enter canonical promoted claim payloads: `tests/test_source_promote_properties.py::test_ws_e_generated_source_local_fields_do_not_enter_canonical_claims`.
- The `sameAs` provenance property is explicitly moved to WS-L because WS-L owns the sameAs representation; WS-E has no sameAs production surface to test.

## Files Changed

- `propstore/source/promote.py`
- `propstore/source/alignment.py`
- `propstore/source/registry.py`
- `propstore/source/finalize.py`
- `propstore/source/passes.py`
- `propstore/source/claims.py`
- `propstore/source/relations.py`
- `propstore/families/documents/sources.py`
- `propstore/storage/repository_import.py`
- `tests/test_source_promote_dangling_refs.py`
- `tests/test_alignment_default_classification.py`
- `tests/test_alias_collision_rejected.py`
- `tests/test_finalize_micropub_required.py`
- `tests/test_transaction_commit_sha_lifetime.py`
- `tests/test_concept_import_status_proposed.py`
- `tests/test_local_handle_collision_blocks_commit.py`
- `tests/test_promote_claim_immutability.py`
- `tests/test_extraction_provenance_aware_timestamps.py`
- `tests/test_justification_rule_kind_validated.py`
- `tests/test_source_promote_properties.py`
- `tests/test_workstream_e_done.py`
- `docs/gaps.md`
- `reviews/2026-04-26-claude/workstreams/WS-E-source-promote.md`
- `reviews/2026-04-26-claude/workstreams/INDEX.md`

## Remaining Risks / Successors

- The sameAs provenance property remains WS-L work because sameAs is not a WS-E-owned representation.
- Broader blocked-micropub promotion filtering remains WS-L per the WS-E non-goals.
- Heuristic-side in-place mutation cleanup remains WS-K.
- Undercutter `target_justification_id` integrity remains WS-F.
