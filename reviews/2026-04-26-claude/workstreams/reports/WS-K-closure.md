# WS-K Closure Report

Workstream: **WS-K - Heuristic discipline, layer-3 boundary, embedding identity**

Closing implementation commit: `3c40537b` (`WS-K stabilize final acceptance gates`)

Status: closed 2026-04-29.

## Findings Closed

- T3.1 / H9: `dedup_pairs` no longer collapses bidirectional distance to a minimum; directed pair distances are preserved.
- T5.1 / Cluster U U#1: top-level heuristic modules were removed; heuristic logic now lives under `propstore/heuristic/`.
- T5.2 / H1 / H3 / H12: `derive_source_document_trust` was deleted; source trust calibration moved to `propstore/source_trust_argumentation`.
- H2: import-linter now has a negative scaffold for the heuristic/source boundary.
- H5: source trust prior base rate is modeled as `Opinion | None` at the document/runtime boundary.
- H6: source trust calibration returns typed, provenanced `SourceTrustResult` output.
- H7: classifier failure is explicit instead of silently treating calibration failure as `confidence = 0.0`.
- H8: the old `CALIBRATED` to `DEFAULTED` downgrade path was deleted with the old source-trust heuristic.
- H10: `classify_stance_async` makes independent forward and reverse LLM calls and stores separate provenance.
- H11: `relate_all_async` files perspective-specific stances under the corresponding source claim.
- H14: stance proposal commit SHA is captured inside the active transaction scope.
- H15: stance proposal promotion is idempotent by default and requires `force=True` to re-promote.
- H16: proposal promotion rejects unknown proposal paths instead of silently dropping them.
- H17: proposal path planning no longer depends on placeholder repository owners.
- H18: empty proposal input is handled consistently by the owner-layer proposal API and CLI/app callers.
- D-19: embedding registry identity is a typed provider/model/version/spec tuple; `_sanitize_model_key` was deleted.
- Layering: `propstore/artifact_verification.py` owns artifact verification paths that need world imports, so artifact code identity stays below world/query layers.
- Acceptance stability: document schema contract versions and import-linter test serialization were added after the full-suite rerun exposed those gaps.

## Tests Written First

- `tests/test_heuristic_package_layout.py` failed while top-level `embed.py`, `classify.py`, `relate.py`, and `calibrate.py` still existed.
- `tests/test_dedup_pairs_preserves_mirror.py` failed while mirror pairs collapsed to one minimum-distance edge.
- `tests/test_no_embedding_key_collision.py` failed while model IDs were sanitized strings with collisions.
- `tests/test_no_derive_source_document_trust.py` failed while the old source-trust derivation path existed.
- `tests/test_prior_base_rate_is_opinion.py` failed while prior base rate was a raw float.
- `tests/test_source_trust_argumentation.py` failed before the typed argumentation calibration pipeline existed.
- `tests/test_trust_calibration_runs_at_promote.py` failed before source promotion invoked trust calibration after the git transaction.
- `tests/test_classify_forward_reverse_independent.py` failed while one LLM response supplied both directions.
- `tests/test_relate_perspective_isolation.py` failed while reverse stances were filed under the forward source claim.
- `tests/test_classify_no_silent_fallback.py` failed while classifier fallback paths fabricated zero-confidence outputs.
- `tests/test_commit_stance_proposals_commit_sha_inside_with.py` failed while proposal commit SHA was read after the transaction exited.
- `tests/test_plan_stance_proposal_promotion_typo_path.py` failed while typo paths were ignored.
- `tests/test_promote_stance_proposals_idempotency.py` failed while repeated promotion duplicated proposal effects.
- `tests/test_proposal_paths_no_placeholder_owner.py` failed while proposal path planning required placeholder repository objects.
- `tests/test_commit_stance_proposals_empty_input.py` failed while empty proposal handling diverged between owner and app layers.
- `tests/architecture/test_import_linter_negative.py` failed before the boundary contract could detect a heuristic import of `source.finalize`.
- `tests/test_workstream_k_done.py` failed until all WS-K sentinel conditions were true.

## Logged Test Evidence

- Step 3 identity green: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-K-step3-identity-green-rerun ...`; log `logs/test-runs/WS-K-step3-identity-green-rerun-20260429-173431.log`.
- Step 4 delete trust green: log `logs/test-runs/WS-K-step4-delete-trust-green-20260429-173657.log`.
- Step 5 prior opinion green: log `logs/test-runs/WS-K-step5-affected-green-20260429-175037.log`.
- Step 6 source-trust argumentation green: log `logs/test-runs/WS-K-step6-source-trust-arg-green-rerun-20260429-175821.log`.
- Step 7 promote calibration green: logs `logs/test-runs/WS-K-step7-promote-calibration-green-20260429-180228.log` and `logs/test-runs/WS-K-step7-affected-20260429-180248.log`.
- Step 8 independent classifier green: logs `logs/test-runs/WS-K-step8-independent-llm-green-20260429-180613.log`, `logs/test-runs/WS-K-step8-classify-existing-rerun-20260429-180821.log`, and `logs/test-runs/WS-K-step8-relate-affected-20260429-180857.log`.
- Step 9 perspective filing green: logs `logs/test-runs/WS-K-step9-perspective-green-rerun-20260429-181745.log`, `logs/test-runs/WS-K-step9-failed-subset-20260429-182048.log`, and `logs/test-runs/WS-K-step9-affected-green-20260429-182118.log`.
- Step 10 classifier fallback green: log `logs/test-runs/WS-K-step10-affected-green-20260429-182911.log`.
- Step 11a proposal commit SHA green: log `logs/test-runs/WS-K-step11a-commit-sha-green-final2-20260429-183413.log`.
- Step 11b unknown proposal path green: log `logs/test-runs/WS-K-step11b-typo-path-green-20260429-183608.log`.
- Step 11c idempotency green: log `logs/test-runs/WS-K-step11c-idempotency-green-rerun-20260429-184052.log`.
- Step 11d no placeholder owner green: log `logs/test-runs/WS-K-step11d-placeholder-green-20260429-184605.log`.
- Step 11e empty proposal handling green: log `logs/test-runs/WS-K-step11e-empty-green-20260429-184910.log`.
- Step 12 import boundary green: log `logs/test-runs/WS-K-step12-import-negative-green-20260429-185545.log`.
- Property gates green: log `logs/test-runs/WS-K-property-gates-rerun-20260429-190009.log`.
- Sentinel/source-trust green: log `logs/test-runs/WS-K-step13-sentinel-green-rerun-20260429-190617.log`.
- Final targeted WS-K run: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-K-final-targeted -n 0 ...`; 30 passed; log `logs/test-runs/WS-K-final-targeted-20260429-190721.log`.
- First full suite after closure exposed three acceptance gaps; log `logs/test-runs/WS-K-final-full-20260429-190802.log`.
- Acceptance fix subset: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-K-full-failure-fixes -n 0 tests/remediation/phase_4_layers/test_T4_1_importlinter_layers.py tests/architecture/test_import_linter_negative.py tests/test_contract_manifest.py`; 10 passed; log `logs/test-runs/WS-K-full-failure-fixes-20260429-191319.log`.
- Final full suite: `powershell -File scripts/run_logged_pytest.ps1 -Label WS-K-final-full-rerun -n auto`; 3393 passed, 2 skipped; log `logs/test-runs/WS-K-final-full-rerun-20260429-191411.log`.
- Type gate: `uv run pyright propstore`; 0 errors.
- Import gate: `uv run lint-imports`; 5 kept, 0 broken.

## Property-Based Gates

- `tests/test_no_embedding_key_collision.py::test_embedding_model_identity_hash_is_injective_over_generated_tuples`.
- `tests/test_classify_forward_reverse_independent.py::test_classify_preserves_generated_directional_perspectives`.
- `tests/test_source_trust_argumentation.py::test_generated_source_trust_rules_emit_provenanced_argumentation_output`.
- Existing mirror-preservation property retained in `tests/test_dedup_pairs_preserves_mirror.py`.

No WS-K property gate was moved to a successor workstream.

## Files Changed

- Architecture/docs: `.importlinter`, `docs/gaps.md`, `reviews/2026-04-26-claude/workstreams/WS-K-heuristic-discipline.md`.
- Heuristic package: `propstore/heuristic/calibrate.py`, `propstore/heuristic/classify.py`, `propstore/heuristic/embed.py`, `propstore/heuristic/embedding_identity.py`, `propstore/heuristic/relate.py`, `propstore/heuristic/source_trust.py`.
- Source trust: `propstore/source_trust_argumentation/__init__.py`, `propstore/source/promote.py`.
- Proposal lifecycle: `propstore/proposals.py`.
- Schema/contracts/sidecar: `propstore/contracts.py`, `propstore/contract_manifests/semantic-contracts.yaml`, `propstore/families/documents/sources.py`, `propstore/families/documents/stances.py`, `propstore/sidecar/build.py`, `propstore/sidecar/claim_utils.py`, `propstore/sidecar/embedding_store.py`, `propstore/sidecar/passes.py`, `propstore/sidecar/schema.py`.
- App/CLI/workflows: `propstore/app/claims.py`, `propstore/app/concepts/embedding.py`, `propstore/app/concepts/mutation.py`, `propstore/app/sources.py`, `propstore/app/verify.py`.
- Core/reasoning support: `propstore/artifact_codes.py`, `propstore/artifact_verification.py`, `propstore/core/claim_values.py`, `propstore/core/row_types.py`, `propstore/praf/engine.py`, `propstore/world/model.py`.
- Tests: WS-K sentinel, heuristic, classification, relation, source trust, proposal, import-linter, sidecar, app, CLI, and affected integration/property tests under `tests/`.

## Remaining Risks / Successors

- H13 model admission control is explicitly out of scope for WS-K and remains a future low-priority workstream.
- WS-K2 still owns extraction of meta-paper trust rules into `knowledge/rules/<paper>/`; WS-K uses hand-stubbed rule fixtures to prove the pipeline shape independently.
- WS-N2 still owns replacing the current forbidden import-linter contracts with the final layered contract.
- Bulk migration of historical sanitized-key embedding rows remains out of scope.
