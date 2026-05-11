# Quire Family CRUD Extraction Workstream

## Goal

Move the remaining generic family-storage mechanics from Propstore into `../quire`
without moving Propstore semantics.

The target architecture is:

- Quire owns generic typed Git/document storage, family CRUD, scannable placement
  patterns, branch-head compare-and-swap failures, and neutral loaded-artifact
  path recovery.
- Propstore owns semantic family declarations, Propstore document schemas,
  source promotion, proposal promotion, sidecar policy, worldline behavior,
  compiler workflows, and all user-facing CRUD workflows.

This is a two-repository workstream. Changes to `../quire` must land first.
Propstore dependency pins must never point at local filesystem paths. If Propstore
needs a Quire update, push Quire first and pin Propstore to a pushed remote tag or
immutable pushed commit SHA.

## Non-Goals

Do not move these into Quire:

- `PropstoreFamily` or `PROPSTORE_FAMILY_REGISTRY`
- claim/concept identity policy callbacks
- Propstore semantic foreign keys
- `semantic_*` helpers
- source finalization, promotion, proposal promotion, or import normalization
- sidecar writes, sidecar paths, or sidecar cleanup policy
- worldline journal capture or at-step projection
- CLI/application CRUD workflows such as add/remove concept, form, context,
  predicate, rule, source, or worldline

No Quire file may encode Propstore vocabulary such as `claim`, `concept`,
`source`, `sidecar`, `worldline`, `promotion`, `predicate`, `rule`, or
`declarations.yaml`, except in Quire tests as consumer-neutral examples using
dummy names.

## Workstream Order

The phases below are topologically ordered. Do not start a phase until its
dependencies are complete.

1. Quire typed stale-head error surface
2. Propstore stale-head parser deletion
3. Quire scannable placement primitives
4. Propstore custom placement deletion
5. Quire point-existence family API
6. Propstore existence-check replacements
7. Quire neutral loaded-artifact path protocol
8. Propstore loaded-path adaptation
9. Optional snapshot/storage cleanup
10. Contract and gate updates

## Phase 1 - Quire Typed Stale-Head Errors

Repository: `../quire`

Delete-first target in Propstore is blocked until this exists in Quire.

Add:

- `quire.git_store.HeadMismatchError`
  - fields: `branch: str`, `expected_head: str | None`, `actual_head: str | None`
  - message must be stable but callers must not parse it
- Quire write paths must raise `HeadMismatchError` instead of a bare
  `ValueError` for expected-head mismatches.

Update:

- `quire/git_store.py`
  - `GitStore.commit_batch`
  - any internal commit path currently producing the stale-head `ValueError`
- `quire/family_store.py`
  - preserve propagation through `DocumentFamilyStore.save`
  - preserve propagation through `DocumentFamilyTransaction.commit`
- `quire/tests/test_git_store.py`
- `quire/tests/test_family_store.py`
- `quire/tests/test_families.py`

Required gates:

- `uv run pytest tests/test_git_store.py tests/test_family_store.py tests/test_families.py`
- `uv run pytest`

Completion evidence:

- No Quire test asserts by parsing a head-mismatch message.
- Quire callers can catch a typed exception and inspect heads directly.

## Phase 2 - Propstore Stale-Head Parser Deletion

Repository: `propstore`

Delete first:

- `propstore/repository.py::_map_stale_head_error`

Then update failures:

- `propstore/repository.py::HeadBoundTransaction.commit_batch`
- `propstore/repository.py::HeadBoundTransaction.families_transact`
- tests that expected `StaleHeadError` or string-parsed stale-head details

Target shape:

- Propstore either imports/re-exports Quire's typed stale-head error as
  `StaleHeadError`, or updates callers/tests to use Quire's exact public error.
- `HeadBoundTransaction` stays in Propstore because it owns sidecar write
  deferral.
- No Propstore code reconstructs stale-head state from exception strings.

Search gate:

- `rg -F "_map_stale_head_error" propstore tests` returns no production refs.
- `rg -F "head mismatch" propstore tests` has no parser logic.

Required gates:

- `powershell -File scripts/run_logged_pytest.ps1 tests/test_branch_head_cas_matrix.py tests/test_repository_concurrency_boundary.py tests/test_artifact_store.py`
- `uv run pyright propstore`

## Phase 3 - Quire Scannable Placement Primitives

Repository: `../quire`

Add generic primitives only:

- A lossy template branch collision option on `BranchPlacement`
  - candidate API: `collision_suffix: Literal["none", "sha256"] = "none"`
  - applies when encoded value differs from raw value
  - appends `--<sha256(raw)>`
- `SubdirFixedFilePlacement`
  - layout: `<namespace>/<ref-dir>/<filename>`
  - scannable via `iter_refs` and `iter_artifacts`
  - ref recovery from locator
- `NestedFlatYamlPlacement`
  - layout: `<namespace>/<dir>/<stem>.yaml`
  - scannable via `iter_refs` and `iter_artifacts`
  - ref recovery from locator
  - supports configurable codecs for each ref component where needed

Update:

- `quire/artifacts.py`
- `quire/tests/test_artifacts.py` or new placement-focused tests
- contract body tests, if present

Do not add:

- Propstore-specific filenames
- Propstore-specific branch names
- Propstore-specific ref classes

Required gates:

- `uv run pytest tests/test_artifacts.py tests/test_family_store.py tests/test_families.py`
- `uv run pytest`

## Phase 4 - Propstore Custom Placement Deletion

Repository: `propstore`

Delete first from `propstore/families/registry.py`:

- `SourceBranchPlacement`
- `PredicateProposalPlacement`
- `RuleProposalPlacement`

Then update failures by using the Quire primitives:

- `SOURCE_BRANCH`
  - use Quire `BranchPlacement` collision-suffix support
  - keep `template="source/{stem}"`, `ref_field="name"`, and
    `codec="safe_slug"` in Propstore
- `PROPOSAL_PREDICATE_PLACEMENT`
  - use Quire `SubdirFixedFilePlacement`
  - keep `namespace="predicates"` and `filename="declarations.yaml"` in
    Propstore
- `PROPOSAL_RULE_PLACEMENT`
  - use Quire `NestedFlatYamlPlacement`
  - keep `namespace="rules"` in Propstore

Update tests:

- `tests/test_proposal_predicates_family.py`
- `tests/test_proposal_rules_family.py`
- `tests/test_semantic_family_registry.py`
- `tests/test_contract_manifest.py`
- any source-branch slug/collision tests

Contract updates:

- Bump affected Propstore contract versions only after production behavior is
  updated.
- Regenerate `propstore/_resources/contract_manifests/semantic-contracts.yaml`
  only if placement `contract_body()` changes.

Search gates:

- `rg -F "class SourceBranchPlacement" propstore tests` returns no refs.
- `rg -F "class PredicateProposalPlacement" propstore tests` returns no refs.
- `rg -F "class RuleProposalPlacement" propstore tests` returns no refs.
- `rg -F "declarations.yaml" ..\quire\quire` returns no refs.

Required gates:

- `powershell -File scripts/run_logged_pytest.ps1 tests/test_semantic_family_registry.py tests/test_proposal_predicates_family.py tests/test_proposal_rules_family.py tests/test_contract_manifest.py`
- `uv run pyright propstore`

## Phase 5 - Quire Point-Existence Family API

Repository: `../quire`

Add:

- `DocumentFamilyStore.exists(family, ref, *, branch=None, commit=None) -> bool`
- `BoundFamily.exists(ref, *, branch=None, commit=None) -> bool`
- `PinnedBoundFamily.exists(ref) -> bool`

Implementation:

- Resolve the family address.
- Use backend `exists(path, commit=...)`.
- Do not decode the document.
- Preserve branch/commit pin semantics.

Update:

- `quire/family_store.py`
- `quire/families.py`
- `quire/tests/test_family_store.py`
- `quire/tests/test_families.py`

Required gates:

- `uv run pytest tests/test_family_store.py tests/test_families.py`
- `uv run pytest`

## Phase 6 - Propstore Existence-Check Replacements

Repository: `propstore`

Replace only checks where the document is not otherwise used.

Good candidates:

- `propstore/app/forms.py::add_form`
- `propstore/app/forms.py::remove_form`
- `propstore/app/contexts.py::add_context`
- `propstore/app/worldlines.py::create_worldline`
- `propstore/app/worldlines.py::delete_worldline`
- narrow proposal-planning checks where only promoted/existing status is needed

Do not replace:

- checks that immediately use the loaded document
- checks where schema errors are intentionally surfaced by loading
- source promotion/finalize code where semantic documents are required

Search work queue:

- `rg -F ".load(" propstore/app propstore/source propstore/proposals.py propstore/proposals_predicates.py propstore/proposals_rules.py`

Required gates:

- `powershell -File scripts/run_logged_pytest.ps1 tests/test_form_workflows.py tests/test_context_workflows.py tests/test_artifact_store.py tests/test_worldline.py`
- `uv run pyright propstore`

## Phase 7 - Quire Neutral Loaded-Artifact Path Protocol

Repository: `../quire`

Problem:

- `quire/artifacts.py` currently duck-types Propstore-shaped attributes such as
  `source_path` and `knowledge_root`.

Delete first:

- Propstore-shaped attribute handling inside Quire path recovery.

Add one neutral surface:

- candidate protocol: `LoadedArtifactPath`
  - `artifact_path`
  - optional `store_root`
- or change `ref_from_loaded`/path recovery to accept an explicit path adapter.

Update:

- `quire/artifacts.py`
- `quire/tests/test_artifacts.py`
- `quire/tests/test_family_store.py`

Search gates:

- `rg -F "knowledge_root" ..\quire\quire` returns no refs.
- `rg -F "source_path" ..\quire\quire` returns no Propstore-shaped path
  recovery refs.

Required gates:

- `uv run pytest tests/test_artifacts.py tests/test_family_store.py tests/test_families.py`
- `uv run pytest`

## Phase 8 - Propstore Loaded-Path Adaptation

Repository: `propstore`

Update callers/tests that pass Propstore loaded objects into Quire ref recovery.

Known starting points:

- `tests/test_artifact_store.py::test_artifact_store_derives_refs_from_paths_and_loaded_objects`
- any `LoadedConcept`, `LoadedContext`, or loaded-document structures passed to
  `repo.families.*.ref_from_loaded`

Target shape:

- Propstore adapts its semantic loaded-document objects to Quire's neutral
  loaded-artifact path protocol.
- Quire does not know the terms `knowledge_root` or `source_path`.

Required gates:

- `powershell -File scripts/run_logged_pytest.ps1 tests/test_artifact_store.py tests/test_semantic_family_registry.py`
- `uv run pyright propstore`

## Phase 9 - Optional Snapshot/Storage Cleanup

Repository: `propstore` and maybe `../quire`

Only do this after Phases 1-8 are complete. This phase is optional because it is
less directly tied to family CRUD.

Candidates to move into Quire if still duplicated:

- generic read typed document from Git path at branch/commit
- generic walk multiple roots as `(relpath, bytes)`
- generic ignored-runtime-path predicate exposed by Quire

Keep in Propstore:

- `RepositorySnapshot` branch taxonomy
- materialization policy using `semantic_init_roots()`
- sidecar/runtime output policy values
- `Repository` bootstrap/config/discovery

Delete-first targets must be named before starting this phase. Do not move
`RepositorySnapshot` wholesale.

Required gates depend on selected deletion target.

## Phase 10 - Contract and Full Gates

Propstore final gates:

- `powershell -File scripts/run_logged_pytest.ps1 tests/test_artifact_store.py tests/test_semantic_family_registry.py tests/test_contract_manifest.py tests/test_repository_artifact_boundary_gates.py`
- `powershell -File scripts/run_logged_pytest.ps1 tests/test_branch_head_cas_matrix.py tests/test_repository_concurrency_boundary.py`
- `uv run pyright propstore`

Quire final gates:

- `uv run pytest`

Cross-repo search gates:

- `rg -F "class SourceBranchPlacement" C:\Users\Q\code\propstore\propstore C:\Users\Q\code\propstore\tests`
- `rg -F "class PredicateProposalPlacement" C:\Users\Q\code\propstore\propstore C:\Users\Q\code\propstore\tests`
- `rg -F "class RuleProposalPlacement" C:\Users\Q\code\propstore\propstore C:\Users\Q\code\propstore\tests`
- `rg -F "_map_stale_head_error" C:\Users\Q\code\propstore\propstore C:\Users\Q\code\propstore\tests`
- `rg -F "knowledge_root" C:\Users\Q\code\quire\quire`
- `rg -F "source_path" C:\Users\Q\code\quire\quire`
- `rg -F "declarations.yaml" C:\Users\Q\code\quire\quire`
- `rg -F "sidecar" C:\Users\Q\code\quire\quire`

## Commit Discipline

Use small commits, one repository at a time.

Suggested commit order:

1. Quire typed stale-head error
2. Propstore stale-head parser deletion
3. Quire scannable placement primitives
4. Propstore placement class deletion and registry update
5. Quire family exists API
6. Propstore selected exists replacements
7. Quire neutral loaded-artifact path protocol
8. Propstore loaded-path adaptation
9. Optional snapshot/storage cleanup
10. Contract manifest and final gate updates

Each commit should include only the files owned by that slice. Do not commit
generated diagnostic artifacts. Commit generated contract manifests only in the
slice that explicitly updates the contract surface.
