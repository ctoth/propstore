# Cut 20 Phase 04 Sources Report

## Workflow Used

Executed `workstreams/family-protocol-cutover-2026-05-24/prompts/codex-cut20-phase04-sources.md`.

## Outcome

- Replaced the handwritten canonical `SourceDocument` in `propstore/families/documents/sources.py` with `SOURCE_CHARTER.generated_document()` in `propstore/families/sources/declaration.py`.
- Kept the 17 source-branch-only document structs in `propstore/families/documents/sources.py`; they have no canonical charters and were out of scope per audit section 3.12.
- Augmented `SOURCE_CHARTER` with document coverage for `metadata`, `document_name="id"` for `source_id`, enum-typed `kind`, and JSON parse-boundary struct fields for `origin`, `trust`, `metadata`, `quality`, and `derived_from`.
- Added source document encode/render/payload helpers owned by `propstore.families.sources.declaration` so generated `SourceDocument` preserves the old payload shape without reintroducing a handwritten document class.
- Updated production and test importers away from `propstore.families.documents.sources.SourceDocument`.
- Regenerated the semantic contract manifest and bumped the affected source contract versions.

No H-A halt was triggered: `SourceDocument` had `to_payload()` only and no `__post_init__` or validation behavior. The payload behavior is now represented by the source family owner helper instead of the document class.

## Verification

- `rg -n -F "class SourceDocument" propstore/families/documents/sources.py propstore/families/sources/declaration.py` -> only the `TYPE_CHECKING` static shape in `propstore/families/sources/declaration.py`.
- `rg -n -F "propstore.families.documents.sources.SourceDocument" propstore tests` -> no matches.
- `powershell -File scripts/run_logged_pytest.ps1 tests/test_artifact_store.py tests/test_prior_base_rate_is_opinion.py tests/test_repo_snapshot.py tests/test_quire_consumer_contracts.py tests/test_sidecar_source_projection.py tests/test_sidecar_projection_contract.py` -> 29 passed.
- `powershell -File scripts/run_logged_pytest.ps1 tests/test_contract_manifest.py::test_contract_manifest_changes_require_version_bumps_against_head` -> 1 passed after source-specific version bumps.
- `uv run pks contract-manifest --write` -> wrote `propstore\_resources\contract_manifests\semantic-contracts.yaml`.
- `uv run pyright propstore` -> 0 errors, 0 warnings, 0 informations.
- `uv run lint-imports` -> propstore six-layer architecture KEPT; Contracts: 1 kept, 0 broken.
- `powershell -File scripts/run_logged_pytest.ps1 tests/` -> 3526 passed, 4 skipped, 30 warnings.

## Logs

- Focused source regression log: `logs\test-runs\pytest-20260525-084139.log`
- Contract-manifest repair log: `logs\test-runs\pytest-20260525-085456.log`
- Full suite log: `logs\test-runs\pytest-20260525-085604.log`

Intermediate note: the first full-suite run failed only `tests/test_contract_manifest.py::test_contract_manifest_changes_require_version_bumps_against_head` (`logs\test-runs\pytest-20260525-084453.log`); the source-specific version bump repaired that gate before the final full-suite pass.
