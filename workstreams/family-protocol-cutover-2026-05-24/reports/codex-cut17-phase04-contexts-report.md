# Cut 17 Phase 04 Contexts Report

## Workflow Used

Executed `workstreams/family-protocol-cutover-2026-05-24/prompts/codex-cut17-phase04-contexts.md`.

## Outcome

- Replaced the handwritten contexts document module with declaration-owned generated documents.
- Deleted `propstore/families/contexts/documents.py`.
- Flattened context documents from `structure.assumptions` / `structure.parameters` / `structure.perspective` to top-level `assumptions` / `parameters` / `perspective`.
- Replaced lifting rule documents with `CONTEXT_LIFTING_RULE_CHARTER.generated_document()`.
- Kept `ContextReferenceDocument` as a small declaration-owned reference `msgspec.Struct`.
- Added generated context assumption and context document surfaces in `propstore/families/contexts/declaration.py`.
- Updated production and test importers away from `propstore.families.contexts.documents`.
- Regenerated the semantic contract manifest.

## Verification

- `Test-Path "propstore/families/contexts/documents.py"` -> `False`
- `rg -n -F -- "propstore.families.contexts.documents" propstore tests` -> no matches
- `rg -n -F -- "ContextStructureDocument" propstore tests` -> no matches
- `powershell -File scripts/run_logged_pytest.ps1 tests/test_quire_boundary.py::test_propstore_quire_imports_are_public tests/test_git_backend.py::test_load_contexts_from_git_tree tests/test_git_backend.py::test_context_add_writes_structured_context_to_git_head tests/test_build_sidecar.py::TestRebuildSkipping::test_rebuild_when_contexts_change tests/test_build_sidecar.py::TestRebuildSkipping::test_content_hash_changes_when_context_semantics_change tests/test_cel_validation.py::test_build_rejects_structural_in_cel` -> 6 passed
- `uv run pyright propstore` -> 0 errors, 0 warnings, 0 informations
- `uv run lint-imports` -> propstore six-layer architecture KEPT; Contracts: 1 kept, 0 broken
- `powershell -File scripts/run_logged_pytest.ps1 tests/` -> 3526 passed, 4 skipped, 30 warnings

## Logs

- Targeted regression log: `logs\test-runs\pytest-20260525-072444.log`
- Full suite log: `logs\test-runs\pytest-20260525-072544.log`
