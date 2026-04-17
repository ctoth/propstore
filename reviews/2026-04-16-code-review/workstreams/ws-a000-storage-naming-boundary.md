# Workstream A000 - Storage Naming Boundary

Date: 2026-04-17
Status: complete
Blocks: `ws-a-semantic-substrate.md` phase 3 canonical document work
Review context: `ws-a0-repository-artifact-boundary.md`, `ws-a00-repository-naming-boundary.md`, `../axis-2-layer-discipline.md`

## Problem

WS-A0 moved the high-level repository facade out of CLI, and WS-A00 moved it to `propstore.repository.Repository`. That still leaves a confusing `propstore.repo` package and public `Repo*` types:

- `propstore.repository.Repository` is the canonical knowledge repository facade.
- `propstore.storage.GitStore` is the low-level git storage carrier.
- `RepoSnapshot`, `RepoMergeFramework`, and `RepoImport*` keep "repo" as a second public vocabulary.

The code no longer has two `Repository` classes, but it still asks readers to distinguish `repo`, `repository`, and storage by convention. That is the same boundary problem in a smaller form.

## Target Shape

- `propstore.repository.Repository` remains the only repository facade.
- Git-backed persistence and merge primitives live under `propstore.storage`.
- The `propstore.repo` package is deleted, not re-exported.
- Public production classes do not use the `Repo*` prefix.
- Existing CLI commands may keep user-facing command names where they describe the command, but production Python import and type surfaces must use repository/storage vocabulary precisely.

## Gates

- A structural test rejects `propstore/repo/`.
- A structural test rejects production imports of `propstore.repo`.
- A structural test verifies `propstore.storage.GitStore` is the canonical low-level storage carrier.
- A structural test rejects propstore-owned production classes with a `Repo` prefix.

## Execution Plan

1. Add failing boundary gates for the remaining ambiguous names.
2. Move `propstore/repo/` to `propstore/storage/` and update imports directly.
3. Rename public `Repo*` classes to `Repository*` or storage-specific names.
4. Update affected tests and docs. Do not add aliases, compatibility imports, or fallback modules.
5. Run the naming gates and affected storage/repository suites through `scripts/run_logged_pytest.ps1`.
6. Commit and push only explicit source/test/workstream files.

## Progress Log

- 2026-04-17: Workstream opened after the repository question exposed that WS-A00 still left `propstore.repo` as a public storage package and `Repo*` as public production type vocabulary.
- 2026-04-17: Completed. Git-backed storage and merge primitives now live under `propstore.storage`; `propstore/repo/` is deleted; public `Repo*` production types were renamed to `RepositorySnapshot`, `RepositoryMergeFramework`, `RepositoryImportPlan`, and `RepositoryImportResult`; repository import helpers are `plan_repository_import` / `commit_repository_import`; `pks import-repository` uses the repository vocabulary. Final verification passed: storage naming/world boundary plus affected storage/import/merge/source/worldline suite (`263 passed`), including GitStore Hypothesis properties; `uv run pyright propstore/storage propstore/repository.py propstore/cli/repository_import_cmd.py` passed with `0 errors`.
