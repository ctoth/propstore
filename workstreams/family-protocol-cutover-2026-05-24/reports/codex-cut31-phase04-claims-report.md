# Cut 31 Phase 04 Claims Report

## Workflow Used

Executed `workstreams/family-protocol-cutover-2026-05-24/prompts/codex-cut31-phase04-claims.md` as the control surface.

## Outcome

Completed the Phase 04 claims family cutover.

- Added `AUTHORED_CLAIM_CHARTER` in `propstore/families/claims/declaration.py` alongside the existing compiled claim sibling charters.
- Added `AUTHORED_CLAIM_FAMILY_CONTRACT_VERSION = VersionId("2026.05.25")`.
- Replaced the handwritten `ClaimDocument` with `AUTHORED_CLAIM_CHARTER.generated_document()`.
- Moved the nested claim document structs and `ClaimTypeContract` registry behavior into the claims declaration surface.
- Deleted `propstore/families/claims/documents.py`.
- Registered the authored claim charter in `world_catalog()` and updated the claims family contract version.
- Updated claim document importers and payload call sites to use the generated-document path and `document_to_payload()`/owner helpers where needed.
- Regenerated `propstore/_resources/contract_manifests/semantic-contracts.yaml`.

## Verification

- `Test-Path propstore\families\claims\documents.py`: `False`
- `rg -F "propstore.families.claims.documents" propstore tests workstreams\family-protocol-cutover-2026-05-24\prompts workstreams\family-protocol-cutover-2026-05-24\reports`: no matches
- `uv run pks contract-manifest --write`: passed
- `uv run pyright propstore`: passed with `0 errors, 0 warnings, 0 informations`
- `powershell -File scripts/run_logged_pytest.ps1 tests/test_claim_roundtrip_fixtures.py tests/test_source_propose.py::test_propose_claim_observation tests/test_import_repo.py::test_plan_repository_import_uses_committed_head_snapshot tests/test_ws7_grounding_completion.py::test_ws7_extract_facts_materializes_claim_structural_sources`: `10 passed`
  - Log: `logs\test-runs\pytest-20260525-144919.log`
- `powershell -File scripts/run_logged_pytest.ps1 tests/test_source_promotion_alignment.py tests/test_source_relations.py tests/test_source_promote_properties.py tests/test_source_trust.py tests/test_cli_source_status.py tests/test_import_repo.py tests/test_cli.py::TestValidate::test_accepts_valid_canonical_claim_reference tests/test_cli.py::TestClaimValidate::test_uses_concepts_dir_override tests/test_cli.py::TestClaimValidateFile::test_clean_file_exits_zero`: `62 passed`
  - Log: `logs\test-runs\pytest-20260525-145021.log`
- `powershell -File scripts/run_logged_pytest.ps1 tests/test_source_claims.py::test_normalized_source_claim_ids_are_content_stable tests/test_provenance_foundations.py::test_resolution_uses_single_opinion_document_with_provenance tests/test_authoring_roundtrip_contract.py::test_source_authoring_to_aspic_extensions_round_trip tests/test_build_sidecar.py::TestClaimTable::test_world_query_loads_authored_justifications_as_domain_objects tests/test_contract_manifest.py::test_contract_manifest_changes_require_version_bumps_against_head tests/remediation/phase_4_layers/test_T4_1_importlinter_layers.py::test_importlinter_layer_contracts_are_clean`: `6 passed`
  - Log: `logs\test-runs\pytest-20260525-150757.log`
- `powershell -File scripts/run_logged_pytest.ps1`: `3526 passed, 4 skipped, 30 warnings in 425.63s`
  - Log: `logs\test-runs\pytest-20260525-150828.log`

## Hard Stops

No prompt hard-stop condition triggered.
