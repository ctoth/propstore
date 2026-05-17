# Source Generic Machinery Deletion Workstream - 2026-05-17

Status: executable.

Parent context:

- `workstreams/quire-explicit-projection-boundaries-workstream-2026-05-16.md`
- `workstreams/generic-quire-projection-mapping-workstream-2026-05-16.md`

Goal: delete generic workflow, import, retry, reference, projection, and export
machinery from `propstore.source` so that `propstore.source` owns only
source-local semantic policy.

This is deletion-first. A source cleanup is not complete if the old surface is
renamed inside `propstore.source`, wrapped in a compatibility module, or moved
to a same-shaped helper with the same ownership problem.

## Target Ownership

`propstore.source` keeps:

- source-local document policy;
- source-local concept, claim, justification, stance, micropub, finalize, and
  promotion semantics;
- source-local identity and source-local-to-canonical lowering decisions;
- source trust calibration policy;
- source status/report semantics.

`propstore.source` must not own:

- committed repository import pipeline mechanics;
- generic planned family writes;
- generic branch compare-and-swap retry mechanics;
- generic first-resolving reference chains;
- generic branch tree export/path traversal protection;
- claim/diagnostic projection-row compilation.

## Inventory

| Surface | Current owner | Target owner | Why |
| --- | --- | --- | --- |
| `SourceImportAuthoredWrites`, `SourceImportNormalizedWrites`, `SourceImportState`, `SourceImportNormalizePass`, `run_source_import_pipeline` | `propstore/source/stages.py`, `propstore/source/passes.py` | `propstore/importing` first; later Quire candidate for generic planned family writes | These are committed repository-import workflow objects, not source-branch authoring policy. |
| `PlannedSemanticWrite` | `propstore/source/stages.py` | `propstore/importing` first; later Quire candidate | Repository import uses it as the unit of planned writes. It is not source-local. |
| `_semantic_import_registry`, `_planned_write`, `_planned_claim_document_write` | `propstore/source/passes.py` | `propstore/importing` | They are import planning mechanics over semantic families. |
| `current_source_branch_head`, `is_stale_branch_error` | `propstore/source/common.py` | repository/Quire update primitive | Generic CAS/retry mechanics. Source proposal code should supply only the mutation policy. |
| 8-attempt proposal loops | `concepts.py`, `claims.py`, `relations.py` | repository/Quire update primitive | Repeated stale-head retry boilerplate. |
| `source_branch_name` wrapper | `propstore/source/common.py` | placement/address API | It only forwards to branch placement. Source code should use the owner. |
| `ImportedClaimHandle`, `imported_claim_handle_index`, `resolve_source_or_primary_claim_id` | `propstore/source/reference_indexes.py` | Quire/reference-chain owner or import/reference owner | Generic imported-handle and first-resolving reference behavior. |
| `compile_promotion_blocked_projection_rows`, `compile_all_source_promotion_blocked_projection_rows` | `propstore/source/promote.py` | claim/diagnostics projection owners | Source decides blocked facts; projection owners compile rows. |
| `sync_source_branch`, `_source_sync_target_path` | `propstore/source/promote.py` | repository/Quire export owner | Generic safe tree export. Source owns only default destination naming. |
| `alignment.py` module location | `propstore/source/alignment.py` | concept-alignment owner | Semantic concept-alignment policy, not source storage. |

## Load-Bearing Constraints

- Unicode source slugs are load-bearing. `source_paper_slug` must continue to
  match `SOURCE_BRANCH` safe-slug and collision-suffix behavior.
- CAS behavior is load-bearing. Proposal retries must use live branch heads, not
  cached snapshots.
- Partial promotion is load-bearing. Blocked claims still need mirror rows and
  diagnostics without promoting invalid claims.
- Canonical promotion must not leak `source_local_id`, source-local `concept`,
  or unresolved source handles.
- Promotion must validate prospective canonical claims before committing master.
- Source sync path traversal protection must remain exact or stricter.
- CLI lazy-import discipline still applies. Moving imports must not make the
  root CLI import unrelated command families.

## Phase 0: Baseline And Old-Path Inventory

Run:

```powershell
git status --short --branch
rg -n -F "propstore.source.passes" propstore tests
rg -n -F "PlannedSemanticWrite" propstore tests
rg -n -F "SourceImport" propstore tests
rg -n -F "current_source_branch_head" propstore tests
rg -n -F "is_stale_branch_error" propstore tests
rg -n -F "source_branch_name" propstore tests
rg -n -F "resolve_source_or_primary_claim_id" propstore tests
rg -n -F "imported_claim_handle_index" propstore tests
rg -n -F "compile_promotion_blocked_projection_rows" propstore tests
rg -n -F "compile_all_source_promotion_blocked_projection_rows" propstore tests
rg -n -F "sync_source_branch" propstore tests
rg -n -F "_source_sync_target_path" propstore tests
```

Required result:

- every old path above has an owner and a target deletion phase;
- no production edit starts with tracked dirty files.

## Phase 1: Repository Import Ownership

Delete first:

- `propstore.source.passes` as the committed repository-import owner;
- source-stage import workflow objects from `propstore/source/stages.py`.

Then implement:

- `propstore.importing.passes` for import normalization;
- `propstore.importing.stages` for import planned-write types;
- `propstore.importing.repository_import` imports from `propstore.importing`;
- tests that used `propstore.source.passes` updated to the new owner.

Old-path searches:

```powershell
rg -n -F "propstore.source.passes" propstore tests
rg -n -F "from propstore.source.stages import" propstore tests
rg -n -F "SourceImport" propstore/source propstore tests
rg -n -F "PlannedSemanticWrite" propstore/source propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label source-import-owner tests/test_import_repo.py tests/test_source_claim_concept_rewrite.py
```

Required result:

- zero `propstore.source.passes` references;
- import workflow names live outside `propstore.source`;
- `propstore.source` no longer imports repository-import pipeline machinery.

## Phase 2: Source Retry/CAS Primitive

Delete first:

- `current_source_branch_head`;
- `is_stale_branch_error`;
- handwritten 8-attempt stale-head loops in `concepts.py`, `claims.py`, and
  `relations.py`.

Then implement:

- a repository or Quire-owned update/retry primitive whose inputs are typed load,
  edit, normalize, and save callbacks;
- source proposal functions call the primitive with source semantic policy only.

Old-path searches:

```powershell
rg -n -F "current_source_branch_head" propstore tests
rg -n -F "is_stale_branch_error" propstore tests
rg -n -F "for attempt in range(8)" propstore/source tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label source-cas tests/test_source_propose.py tests/test_source_claims.py tests/test_source_relations.py
```

Required result:

- no source-local stale-head helper remains;
- retries still use live branch heads;
- proposal behavior and stale-head tests still pass.

## Phase 3: Branch Placement Helper Deletion

Delete first:

- `source_branch_name` wrapper.

Then implement:

- direct use of the placement/family branch owner, or a Quire-owned branch
  lookup API if existing placement cannot express this cleanly.

Old-path search:

```powershell
rg -n -F "source_branch_name" propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label source-branch-placement tests/test_source_promotion_alignment.py tests/test_source_cli.py tests/test_source_list_and_context.py
```

Required result:

- zero `source_branch_name` references;
- Unicode branch/paper slug alignment remains unchanged.

## Phase 4: Reference Chain Cleanup

Delete first:

- `ImportedClaimHandle`;
- `imported_claim_handle_index`;
- `resolve_source_or_primary_claim_id`.

Then implement:

- generic imported-handle/reference-chain machinery in a non-source owner;
- source keeps only `SOURCE_CLAIM_REFERENCE_KEYS` and source-claim index policy.

Old-path searches:

```powershell
rg -n -F "ImportedClaimHandle" propstore tests
rg -n -F "imported_claim_handle_index" propstore tests
rg -n -F "resolve_source_or_primary_claim_id" propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label source-reference-chain tests/test_source_relations.py tests/test_source_promote_dangling_refs.py tests/test_source_claim_concept_rewrite.py
```

Required result:

- generic reference-chain behavior no longer lives under `propstore.source`;
- source claim reference keys stay source-owned.

## Phase 5: Promotion Projection Split

Delete first:

- `compile_promotion_blocked_projection_rows`;
- `compile_source_promotion_blocked_projection_rows`;
- `compile_all_source_promotion_blocked_projection_rows` from
  `propstore.source.promote`.

Then implement:

- source promotion emits typed blocked-claim facts;
- claim and diagnostics projection owners compile `claim_core` and
  `build_diagnostics` rows.

Old-path searches:

```powershell
rg -n -F "compile_promotion_blocked_projection_rows" propstore tests
rg -n -F "compile_source_promotion_blocked_projection_rows" propstore tests
rg -n -F "compile_all_source_promotion_blocked_projection_rows" propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label source-promotion-projection tests/test_cli_source_status.py tests/test_source_promote_dangling_refs.py tests/test_build_sidecar.py
```

Required result:

- no projection-row compilation remains in `propstore.source.promote`;
- blocked claim sidecar rows and diagnostics are byte-compatible.

## Phase 6: Source Branch Export Owner

Delete first:

- `sync_source_branch`;
- `_source_sync_target_path`.

Then implement:

- generic safe tree export in repository/Quire owner;
- source-facing function only chooses the default destination and calls the
  generic exporter.

Old-path searches:

```powershell
rg -n -F "sync_source_branch" propstore tests
rg -n -F "_source_sync_target_path" propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label source-export tests/test_source_cli.py tests/remediation/phase_1_crits/test_T1_5_zip_slip.py
```

Required result:

- generic path traversal guard no longer lives in source promotion;
- source sync behavior is unchanged.

## Final Gates

Run:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label source-cleanup-targeted tests/test_import_repo.py tests/test_source_claim_concept_rewrite.py tests/test_source_propose.py tests/test_source_claims.py tests/test_source_relations.py tests/test_source_promote_dangling_refs.py tests/test_cli_source_status.py tests/test_source_cli.py
rg -n -F "propstore.source.passes" propstore tests
rg -n -F "from propstore.source.stages import" propstore tests
rg -n -F "current_source_branch_head" propstore tests
rg -n -F "is_stale_branch_error" propstore tests
rg -n -F "source_branch_name" propstore tests
rg -n -F "resolve_source_or_primary_claim_id" propstore tests
rg -n -F "imported_claim_handle_index" propstore tests
rg -n -F "compile_promotion_blocked_projection_rows" propstore tests
rg -n -F "compile_all_source_promotion_blocked_projection_rows" propstore tests
rg -n -F "sync_source_branch" propstore tests
rg -n -F "_source_sync_target_path" propstore tests
```

Completion requires:

- all listed old production owners are gone or explicitly blocked in this file
  with a concrete missing owner;
- `propstore.source` owns source-local semantics, not generic workflow plumbing;
- pyright and targeted source/import gates pass.
