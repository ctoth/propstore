# Cut 30 Phase 04 Concepts Report

Workflow used: `workstreams/family-protocol-cutover-2026-05-24/prompts/codex-cut30-phase04-concepts.md`.

## Result

- Added `AUTHORED_CONCEPT_CHARTER` beside the existing compiled concept charters.
- Moved the authored LEMON concept document structs into `propstore/families/concepts/declaration.py` as `msgspec.Struct`.
- Replaced the handwritten `ConceptDocument` with `AUTHORED_CONCEPT_CHARTER.generated_document()`.
- Preserved the lexical-entry-at-least-one-sense invariant through the Quire charter `validators=` hook.
- Registered the authored concept charter in `world_catalog()` and moved the concepts family contract version to `AUTHORED_CONCEPT_FAMILY_CONTRACT_VERSION`.
- Deleted `propstore/families/concepts/documents.py`.
- Updated concept document importers to use `propstore.families.concepts.declaration`.
- Regenerated `propstore/_resources/contract_manifests/semantic-contracts.yaml`.

## Verification

- `uv run lint-imports` passed.
- `uv run pyright propstore` passed with 0 errors.
- `powershell -File scripts/run_logged_pytest.ps1 --label cut30-phase04-concepts-targeted-after-repair tests/test_lemon_concept_documents.py tests/test_no_privileged_namespace.py tests/test_artifact_identity_policy.py tests/test_contract_manifest.py tests/test_sidecar_form_projection.py tests/test_worldline_properties.py::TestContentHashDeterminism::test_content_hash_deterministic` passed: 21 passed.
- `powershell -File scripts/run_logged_pytest.ps1 --label cut30-phase04-concepts-full-after-repair` passed: 3526 passed, 4 skipped, 30 warnings.

## Notes

- The first full gate exposed an import-linter regression from moving authored concept structs into `concepts.declaration`; the fix keeps `concepts.declaration` out of the relations declaration path by emitting relation-edge mappings and constructing them through the Quire relation-edge family at write time.
- The same first full gate reported an xdist worker crash in `TestContentHashDeterminism::test_content_hash_deterministic`; the test passed in the targeted rerun and in the final full suite.
