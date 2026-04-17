# Workstream A0 - Repository / Artifact Boundary Prerequisite

Date: 2026-04-17
Status: planned, prerequisite for WS-A phase 2 document-boundary work
Depends on: `disciplines.md`, `judgment-rubric.md`, `../axis-2-layer-discipline.md`, `../SYNTHESIS.md`
Blocks: WS-A phase 2 hard `ConceptDocument` lemon boundary, and any later artifact-family rewrite that assumes repository access is layer-clean

## Why this exists

WS-A phase 2 started correctly by adding the lemon core and deleting the Jaccard alignment fallback. The next natural step, making canonical `ConceptDocument` lemon-shaped, exposed a prior architectural violation: production layers below CLI import `propstore.cli.repository.Repository`, and core concept loading decodes canonical concept YAML directly instead of entering through the artifact-store family boundary.

That is exactly the class of violation called out by `axis-2-layer-discipline.md` and the synthesis: the repository object is a filesystem/artifact primitive, not a CLI type. Continuing WS-A phase 2 without fixing it would either add a hidden compatibility normalizer inside the artifact path or preserve two production concept-loading paths. Both are forbidden by the project rules.

## Target architecture

- `Repository` and `RepositoryNotFound` live in a layer-1 module, either `propstore/repository.py` or `propstore/repo/repository.py`.
- `propstore/cli/` consumes the repository facade; it does not own it.
- `propstore/cli/repository.py` is removed or reduced to no repository facade definitions. Do not leave an import alias, compatibility shim, or re-export.
- Non-CLI production modules do not import `propstore.cli.repository`.
- The repository facade may expose path, git, artifact-store, and snapshot access. It must not import `propstore.world` and must not expose `Repository.store`; render/world construction belongs at render/CLI call sites.
- `ArtifactStore` depends on a layer-clean repository facade or protocol. It must not type against CLI.
- Canonical concept loading enters through artifact families/store. `propstore/core/concepts.py` must not directly decode `ConceptDocument` files with `load_document(...)` as a separate production path.
- The lemon document-boundary change in WS-A phase 2 may proceed only after the above boundary is enforced.

## TDD gates

The initial red gates are in `tests/test_repository_artifact_boundary_gates.py`. They are marked `xfail(strict=True)` until this workstream is actively implemented. Strict xfail is intentional: the tests demonstrate the present violation now, and once a slice fixes a violation the unexpected pass forces the implementer to remove the marker and promote the test to an active gate.

Required gate promotions during this workstream:

- Promote `test_non_cli_production_modules_do_not_import_cli_repository` when all non-CLI imports have moved to the new repository facade.
- Promote `test_cli_repository_module_no_longer_defines_repository_facade` when the CLI module no longer owns `Repository` or `RepositoryNotFound`.
- Promote `test_repository_facade_does_not_depend_on_world_model` when repository/world coupling is removed.
- Promote `test_core_concept_loading_does_not_decode_concept_documents_directly` when canonical concept loading goes through artifact families/store.

The tests must stay precise. Do not replace them with broad snapshots or grep-only checks that cannot explain the violation.

## Implementation sequence

1. Move repository facade types to the selected layer-1 module. Update all imports in one pass. Delete the CLI-owned facade path rather than re-exporting it.
2. Remove `Repository.store`. Update CLI/render callers to construct `WorldModel(repo)` explicitly where a world model is actually required.
3. Make `ArtifactStore` and artifact helper protocols type against the layer-1 facade, not `propstore.cli.repository`.
4. Route canonical concept loading through the artifact family/store boundary. Remove the direct `load_document(..., ConceptDocument, ...)` production path from `core/concepts.py`.
5. Remove each strict xfail marker as its violation is eliminated. Keep the gate test as a permanent regression test.
6. Rerun the affected suites through `scripts/run_logged_pytest.ps1`, then reread WS-A phase 2 before continuing the lemon document-boundary conversion.

## Explicit non-goals

- No old repository migration.
- No backfill command.
- No compatibility reader for pre-WS-A concept YAML.
- No artifact-store fallback normalizer that silently rewrites old concept shapes.
- No CLI re-export preserving `from propstore.cli.repository import Repository`.

Existing pre-workstream knowledge repositories are not a compatibility target. New data must use the target shape directly, and old shapes should fail at the boundary once WS-A phase 2 resumes.

## Exit criteria

- All four boundary tests in `tests/test_repository_artifact_boundary_gates.py` are active, not xfailed, and pass.
- `rg -F "propstore.cli.repository" propstore` finds only CLI-owned code if any CLI helper remains, and no non-CLI production modules.
- No `Repository.store` property exists.
- Concept artifact reads for canonical concept data go through artifact families/store.
- Targeted affected tests pass through `scripts/run_logged_pytest.ps1`.
- WS-A phase 2 workstream notes are reread and updated before the `ConceptDocument` lemon boundary is attempted again.
