# Derived Build File Deletion Rethink Workstream

Date: 2026-05-24

## Refactor Zen

This workstream exists because deleting `propstore/derived_build.py` and
`propstore/derived_build_plan.py` exposed that build orchestration was not
modular enough. The deletion is correct. Breakage from that deletion is not an
import-fix queue; it is a forced ownership and existence review for every
remaining reference.

If any production file contains a bad production class, function, helper,
alias, shim, fallback, duplicate model, duplicated metadata, compatibility
branch, wrong-owner surface, or renamed copy of a deleted responsibility, the
whole file is deleted first. Required capabilities are recreated only in real
owner files. If deleting one bad symbol breaks unrelated behavior, that is
evidence the old file mixed responsibilities and must not be preserved.

Field and schema shape is written once in Quire charters or the exact
Propstore semantic owner. Propstore must not restate storage fields in row
DTOs, kwargs builders, projection models, handwritten mapped models, manual
table registries, per-table construction helpers, or model-layer normalizers.
After an IO boundary has parsed input, typed domain objects carry meaning. No
generic coercion, loose mapping repair, shim, adapter, alias, bridge, fallback,
or old/new dual path is allowed.

Family placement is not enough. A duplicate fact moved into
`propstore.families` is still a duplicate fact. The family charter is the
single source of truth for the family contract: field names, field types,
database columns, primary keys, reference keys, indexes, FTS/vector/cache
metadata, validation hooks, and relational semantic callbacks. A family module
may own semantic methods and callbacks attached to the charter/model, but it
must not contain parallel schema construction, hardcoded table/field/index
registries, handwritten SQL projection strings, payload reconstitution helpers,
or per-field builders that restate charter metadata. The valid endpoint is
charter metadata plus generated Quire machinery, not old complexity under a
family package name.

## Goal

Finish the Phase 5 repair by removing the deleted derived-build files as
production surfaces and rehoming only the capabilities that still belong in the
target architecture.

Final state:

- `propstore/derived_build.py` is deleted.
- `propstore/derived_build_plan.py` is deleted.
- No production or test code imports `propstore.derived_build` or
  `propstore.derived_build_plan`.
- No replacement module recreates those files under a new name.
- No replacement family module recreates the deleted files by restating
  charter facts, table facts, projection SQL, or payload shapes under a
  better package name.
- Repository derived-store lifecycle and cache identity use Quire
  `DerivedStoreManager`/`DerivedStoreHandle` APIs directly from the owning
  repository/build owner.
- Build validation and build report construction stay in
  `propstore.compiler.workflows`.
- World sidecar opening and read-only query behavior stay in
  `propstore.world.model`/world owners.
- Family write materialization is owned by the family/compiler output that
  already owns the typed model objects, not by a central table-name batch plan.
- Quire owns generic SQLAlchemy store creation, writable sessions, schema
  catalog metadata, family main-model lookup, reference lookup, FTS/vector
  population hooks, and schema/cache hash mechanics.
- Propstore owns semantic policy: diagnostics, quarantine decisions,
  promotion-blocked behavior, embedding snapshot policy, grounding bundle
  semantics, compiler pass ordering, and user-facing reports.

## Scope

Repository: `C:\Users\Q\code\propstore`

Deleted files that must remain deleted:

- `propstore/derived_build.py`
- `propstore/derived_build_plan.py`

Current deletion fallout to review:

- `propstore.compiler.workflows`: repository build currently imports
  `materialize_world_sidecar`.
- `propstore.world.model`: `WorldQuery.__init__` and
  `WorldQuery.historical_query` currently import `materialize_world_sidecar`.
- `propstore.app.claims`, `propstore.app.sources`,
  `propstore.app.repository_history`, `propstore.app.concepts.display`,
  `propstore.app.concepts.embedding`, and `propstore.app.concepts.mutation`
  currently import `materialize_world_sidecar`.
- tests and remediation helpers currently import `export_sidecar`,
  `materialize_world_sidecar`, `world_sidecar_hash`,
  `_flush_promotion_blocked_claims`, `_add_write_batches`,
  `extract_embedding_snapshot_from_store`, and `_restore_embedding_snapshot`
  from `propstore.derived_build`.
- `scripts/compare_sqlalchemy_charter_parity.py` currently imports
  `export_sidecar` and `_source_branch_tips` from `propstore.derived_build`.

Known adjacent bad surfaces:

- `propstore.families.world_charters.world_record(table_name, values)` and
  `world_records(table_name, rows)` are table-name construction helpers. They
  are not allowed final owners.
- `propstore.families.world_charters._MODELS` and `_CLAIM_MODEL_TABLES`
  duplicate model-routing metadata and preserve a claim special case. They are
  not allowed final owners.
- If `propstore.families.world_charters.py` cannot be reduced to correct
  charter/domain ownership without those bad production surfaces, delete the
  whole file and recreate the remaining required charter registration in the
  correct owner files.

Out of scope:

- Adding a compatibility module named `propstore.derived_build`.
- Adding a renamed derived-build module.
- Replacing deleted functions with thin wrappers in app, CLI, tests, or world
  code.
- Broad family cutovers unrelated to derived-store build/open/write ownership,
  except when deletion exposes a bad file that must be removed.

## Required Inputs

Before implementation, read:

- `workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/00-index.md`
- `workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/04-propstore-build-orchestration.md`
- `C:\Users\Q\code\protocols-plugin\plugins\protocols\skills\cleanup-refactor\SKILL.md`
- current `propstore.repository`
- current `propstore.compiler.workflows`
- current `propstore.world.model`
- current `propstore.families.world_charters`
- every production file returned by the `propstore.derived_build` search gate

## Execution Rules

- Execute deletion-first.
- The already-deleted derived-build files are not restored.
- Breakage is reviewed per remaining reference, not repaired by imports.
- For every remaining reference, answer:
  - What capability did the deleted file provide?
  - Should that capability still exist?
  - If no, which caller path is deleted?
  - If yes, which existing owner already owns it?
  - If no owner exists, which owner layer is extended?
  - What proves the change is not a renamed copy of the deleted file?
- If a production caller file contains a bad production surface, delete the
  whole file first and use the resulting breakage as the next rethink queue.
- Use Quire generic capabilities directly. Do not add Propstore wrappers around
  Quire session, schema, model lookup, reference lookup, FTS, vector, or cache
  identity mechanics.
- Commit each kept deletion/reduction slice with explicit paths.

## Ordered Phases

### Phase 0 - Current Deletion Baseline

Confirm current state:

```powershell
git status --short -- propstore/derived_build.py propstore/derived_build_plan.py
rg -n -F -- "propstore.derived_build" propstore tests
rg -n -F -- "propstore.derived_build" scripts
rg -n -F -- "derived_build_plan" propstore tests
```

Expected state:

- `propstore/derived_build.py` is deleted.
- `propstore/derived_build_plan.py` is deleted.
- `derived_build_plan` has zero live code imports.
- `propstore.derived_build` has live references that become the Phase 1
  rethink queue.
- `scripts/compare_sqlalchemy_charter_parity.py` is part of the live rethink
  queue.

Phase 0 execution record, 2026-05-24:

- Branch: `master`.
- Current tracked deletion state:
  `D propstore/derived_build.py` and
  `D propstore/derived_build_plan.py`.
- `rg -n -F -- "derived_build_plan" propstore tests` returned zero live code
  hits.
- `rg -n -F -- "propstore.derived_build" propstore tests` found production
  callers in `propstore/compiler/workflows.py`, `propstore/world/model.py`,
  `propstore/app/claims.py`, `propstore/app/sources.py`,
  `propstore/app/repository_history.py`,
  `propstore/app/concepts/display.py`,
  `propstore/app/concepts/embedding.py`, and
  `propstore/app/concepts/mutation.py`, plus test/remediation callers.
- `rg -n -F -- "propstore.derived_build" scripts` found
  `scripts/compare_sqlalchemy_charter_parity.py`; this script caller is now
  in scope for the rethink queue.

### Phase 1 - Capability Disposition Table

For every symbol formerly imported from `propstore.derived_build`, write a
disposition in this workstream before editing a caller:

| Deleted symbol | Capability | Required disposition |
| --- | --- | --- |
| `materialize_world_sidecar` | ensure/open a repository world derived store for a commit | The capability remains, but not as a helper. `propstore.compiler.workflows` owns build materialization during repository builds. `propstore.world.model` owns world query opening. App surfaces must call those owner APIs directly or delete the caller path. |
| `export_sidecar` | write a sidecar to a requested path | The capability remains only for the parity harness and tests that need an explicit SQLite output path. It belongs to the compiler/build owner, not a deleted helper module. |
| `world_sidecar_hash` / hash-input helpers | derived-store cache identity | Quire `derived_store_content_hash`, Quire schema catalog hash, and repository semantic tree/source branch inputs own this. Delete Propstore hash helper wrappers. The parity script computes semantic input hash in-script because it owns parity comparison, not cache identity. |
| `_source_branch_tips` | source branch semantic input enumeration | Parity comparison still needs this input. The script owns parity semantic-input hashing and must compute source branch tips directly from `repo.snapshot.iter_branches()`, not import a deleted private helper. |
| `_flush_promotion_blocked_claims` | promotion-blocked semantic policy write | Move to the claim/diagnostics semantic owner if still needed. It must not remain a build private helper. |
| `_add_write_batches` | central batch insertion | Delete. Family/compiler owners write typed models through Quire sessions directly. |
| `extract_embedding_snapshot_from_store` / `_restore_embedding_snapshot` | embedding snapshot policy | Extraction already belongs in `propstore.families.embeddings.declaration`. Restore behavior must move there too if still needed. No build-module private helper. |
| `_pass_diagnostic_records`, `_authoring_diagnostic_records`, `_quarantine_diagnostic_records`, `_quarantine_record`, `_embedding_restore_diagnostic_record`, `_build_exception_record` | build diagnostic model construction | Build diagnostic construction belongs in `propstore.families.diagnostics.declaration` or the compiler/build owner that emits the diagnostic. No central deleted build helper. |
| `_grounded_bundle_records`, `_grounded_bundle_input_records`, `build_grounding_sidecar` | grounding bundle persistence | Grounding semantics belong in rules/grounding owners. If explicit grounding sidecar output is still needed, it must be owned there; no derived-build private helper. |
| `run_claim_pipeline` monkeypatch target | compiler pass ordering | Tests must patch the compiler/family owner directly or be deleted if they test the deleted module shape. |

Phase 1 is complete only when this table has been updated with every remaining
symbol found by search and each row names delete, direct owner use, or owner
extension. No row may say `maybe`, `if appropriate`, `temporary`, `later`, or
`compatibility`.

Phase 1 execution record:

- Commit `8dedfd42 Move build diagnostics to diagnostics owner` moved build
  diagnostic construction into `propstore.families.diagnostics.declaration`.
- Deleted-module diagnostic helpers now have owner-layer replacements:
  `build_pass_diagnostics`, `build_authoring_diagnostics`,
  `build_quarantine_diagnostics`, `embedding_restore_diagnostic`, and
  `sidecar_build_exception_diagnostic`.
- Commit `1d9c5c8e Move embedding restore to embedding owner` moved vector
  snapshot restore behavior beside the existing embedding snapshot extraction
  owner as
  `propstore.families.embeddings.declaration.restore_embedding_snapshot_to_session`.
- Commit `e5bf4264 Delete old embedding snapshot symbol` renamed the embedding
  owner API to `extract_embedding_snapshot`, so the deleted
  `extract_embedding_snapshot_from_store` spelling is not preserved.

### Phase 2 - Production Caller File Deletion Review

For each production caller returned by:

```powershell
rg -n -F -- "propstore.derived_build" propstore
```

read the whole file and decide file disposition:

- Delete the file if it contains any bad production surface.
- If the whole file is a correct owner file, delete the bad import and use the
  real owner capability directly.
- If the file is presentation/app code, it may construct typed requests and
  call owner-layer APIs only.

Required first production files:

- `propstore/compiler/workflows.py`
- `propstore/world/model.py`
- `propstore/app/claims.py`
- `propstore/app/sources.py`
- `propstore/app/repository_history.py`
- `propstore/app/concepts/display.py`
- `propstore/app/concepts/embedding.py`
- `propstore/app/concepts/mutation.py`

Phase 2 execution record:

- Commit `796d990a Move world store build to compiler owner` removed the
  compiler production import of `propstore.derived_build`.
- `propstore.compiler.workflows.build_repository_world_store` now owns cached
  repository world-store materialization through Quire
  `DerivedStoreManager.materialize_with_report`.
- `propstore.compiler.workflows.write_repository_world_store` now owns explicit
  sidecar SQLite output for the parity harness and tests.
- The old central row-plan file is not recreated. Family compiler outputs are
  written as typed model objects directly through the Quire writable session.
- Grounding persistence uses the existing rules owner
  `persist_grounded_bundle`.
- Remaining Phase 2 production callers are `propstore/world/model.py`,
  `propstore/app/claims.py`, `propstore/app/sources.py`,
  `propstore/app/repository_history.py`,
  `propstore/app/concepts/display.py`,
  `propstore/app/concepts/embedding.py`, and
  `propstore/app/concepts/mutation.py`.
- Commit `f1b1efea Use compiler owner for world store opening` removed
  `propstore.derived_build` imports from `propstore/world/model.py`.
- Remaining Phase 2 production callers are now `propstore/app/claims.py`,
  `propstore/app/sources.py`, `propstore/app/repository_history.py`,
  `propstore/app/concepts/display.py`,
  `propstore/app/concepts/embedding.py`, and
  `propstore/app/concepts/mutation.py`.
- Commit `d9aef753 Use compiler owner in app sidecar callers` removed
  `propstore.derived_build` imports from all remaining app production callers.
- Remaining non-test caller is
  `scripts/compare_sqlalchemy_charter_parity.py`, which must use
  `write_repository_world_store` for explicit parity sidecar output and compute
  source branch tips directly from `repo.snapshot.iter_branches()`.
- Commit `f405af29 Use compiler owner in parity harness` removed the script
  imports of `propstore.derived_build`. Production and script searches for
  `propstore.derived_build` now return zero hits; remaining hits are tests and
  remediation helpers in Phase 4.

### Phase 3 - World Charter File Review

Run:

```powershell
rg -n -F -- "_MODELS" propstore/families/world_charters.py
rg -n -F -- "_CLAIM_MODEL_TABLES" propstore/families/world_charters.py
rg -n -F -- "def world_record" propstore/families/world_charters.py
rg -n -F -- "def world_records" propstore/families/world_charters.py
```

If any hit remains in production code, the file has failed the file-level
deletion gate. Delete `propstore/families/world_charters.py` and recreate only
the required charter registration or semantic model ownership in correct owner
files:

- field/schema metadata in Quire charters or family-owned charter declarations;
- behavior-only semantic methods on Propstore family/domain classes;
- generic model/reference lookup in Quire/family registry metadata;
- no table-name model registries in Propstore;
- no `world_record(table_name, values)` construction helper.

Phase 3 execution record:

- Commit `c7d62b8e Move promotion blocked writes to claim owner` removed
  `world_record(...)` from `propstore/families/claims/declaration.py`.
- Claim compilation now constructs `Claim`, `ClaimNumericPayload`,
  `ClaimTextPayload`, and `ClaimAlgorithmPayload` typed model objects
  directly.
- Promotion-blocked claim replacement is now owned by
  `propstore.families.claims.declaration.write_promotion_blocked_models`,
  with diagnostic deletion delegated to the diagnostics owner.
- Remaining Phase 3 work: `propstore/families/world_charters.py` still must
  pass the file-level gate for `_MODELS`, `_CLAIM_MODEL_TABLES`,
  `world_record`, and `world_records`.
- Commit `1d7f6bba Delete world charter construction helpers` deleted and
  recreated `propstore/families/world_charters.py` as charter/catalog
  registration only.
- `WorldMeta` remains in `propstore.families.world_charters` because it is
  world-store metadata. Support model marker classes moved to semantic owners:
  grounded rule rows to `propstore.families.rules.declaration`,
  calibration counts to `propstore.families.calibration.declaration`,
  embedding status/model rows to `propstore.families.embeddings.declaration`,
  and build diagnostics to `propstore.families.diagnostics.declaration`.
- Production and test callers no longer import or call
  `world_record(table_name, values)` or `world_records(table_name, rows)`.
  Production synthetic-claim graph projection now constructs typed claim
  owner models directly.
- Phase 3 gates for `_MODELS`, `_CLAIM_MODEL_TABLES`, `def world_record`,
  `def world_records`, and `world_record` returned zero hits in
  `propstore`, `tests`, and `scripts`.
- Focused verification:
  `uv run pyright propstore\families\world_charters.py propstore\families\rules\declaration.py propstore\families\calibration\declaration.py propstore\families\embeddings\declaration.py propstore\families\diagnostics\declaration.py propstore\families\claims\declaration.py propstore\families\claims\graph.py`
  passed with 0 errors.
- Focused tests:
  `powershell -File scripts/run_logged_pytest.ps1 -Label world-charters-owner-cleanup ...`
  ran 89 selected tests; 88 passed and one direct-constructor fixture failure
  exposed a missing optional `conditions_ir` field.
- Corrected verification:
  `powershell -File scripts/run_logged_pytest.ps1 -Label world-charters-owner-cleanup-recheck tests/test_labelled_core.py::test_derived_value_combines_input_labels tests/test_semantic_core_phase0.py::test_binding_order_does_not_change_active_or_resolved_semantics`
  passed 2 tests.

### Phase 4 - Test Caller Rethink

For each test returned by:

```powershell
rg -n -F -- "propstore.derived_build" tests
```

apply the same breakage review:

- tests that assert deleted helper shape are deleted or rewritten to assert the
  real owner contract;
- tests that monkeypatch deleted private helpers are deleted or rewritten to
  patch the real owner boundary;
- fixtures that need a built sidecar use the owner-layer build/export API;
- tests must not import a replacement wrapper.

Phase 4 execution record:

- Commit `e6c62bcf Rewrite tests to build owner APIs` removed test and
  remediation imports of `propstore.derived_build`.
- Test fixtures that need cached repository world stores now call
  `propstore.compiler.workflows.build_repository_world_store`.
- Tests and remediation helpers that need explicit SQLite output now call
  `propstore.compiler.workflows.write_repository_world_store`.
- Cache-hash tests now exercise the compiler owner cache input and content
  hash functions directly; no Propstore hash wrapper remains.
- Promotion-blocked remediation helpers now call
  `propstore.families.claims.declaration.write_promotion_blocked_models`.
- Deleted private-helper monkeypatches now patch real owner boundaries:
  compiler pass ordering, compiler FTS population, embedding owner restore,
  and compiler world-store build/open behavior.
- Search gates over tests for `propstore.derived_build`,
  `derived_build_plan`, `materialize_world_sidecar`, `export_sidecar`,
  `world_sidecar_hash`, `_add_write_batches`,
  `_flush_promotion_blocked_claims`,
  `extract_embedding_snapshot_from_store`, and
  `_restore_embedding_snapshot` returned zero hits.
- Focused verification:
  `powershell -File scripts/run_logged_pytest.ps1 -Label derived-build-test-callers ...`
  ran 136 selected tests; 134 passed and two owner-boundary test injections
  failed because they patched the outer writer instead of the real failure
  point.
- Corrected verification:
  `powershell -File scripts/run_logged_pytest.ps1 -Label derived-build-test-callers-recheck tests/test_repository_concurrency_boundary.py::test_sidecar_build_serializes_with_source_promote tests/remediation/phase_1_crits/test_T1_2_sidecar_survives_exception.py::test_sidecar_not_deleted_on_build_exception`
  passed 2 tests.

### Phase 5 - Search Gates

All of these are zero-hit gates outside this workstream file, notes, reports,
and docs:

```powershell
rg -n -F -- "propstore.derived_build" propstore tests scripts
rg -n -F -- "derived_build_plan" propstore tests scripts
rg -n -F -- "materialize_world_sidecar" propstore tests scripts
rg -n -F -- "export_sidecar" propstore tests scripts
rg -n -F -- "world_sidecar_hash" propstore tests scripts
rg -n -F -- "_add_write_batches" propstore tests scripts
rg -n -F -- "_flush_promotion_blocked_claims" propstore tests scripts
rg -n -F -- "extract_embedding_snapshot_from_store" propstore tests scripts
rg -n -F -- "_restore_embedding_snapshot" propstore tests scripts
rg -n -F -- "def world_record" propstore tests scripts
rg -n -F -- "def world_records" propstore tests scripts
rg -n -F -- "_CLAIM_MODEL_TABLES" propstore tests scripts
```

Phase 5 execution record:

- Commit `c37bb814 Delete derived build production files` committed deletion
  of `propstore/derived_build.py` and `propstore/derived_build_plan.py`
  with 1093 removed lines.
- `rg -n -F -- "propstore.derived_build" propstore tests scripts`
  returned zero hits.
- `rg -n -F -- "derived_build_plan" propstore tests scripts`
  returned zero hits.
- `rg -n -F -- "materialize_world_sidecar" propstore tests scripts`
  returned zero hits.
- `rg -n -F -- "export_sidecar" propstore tests scripts`
  returned zero hits.
- `rg -n -F -- "world_sidecar_hash" propstore tests scripts`
  returned zero hits.
- `rg -n -F -- "_add_write_batches" propstore tests scripts`
  returned zero hits.
- `rg -n -F -- "_flush_promotion_blocked_claims" propstore tests scripts`
  returned zero hits.
- `rg -n -F -- "extract_embedding_snapshot_from_store" propstore tests scripts`
  returned zero hits.
- `rg -n -F -- "_restore_embedding_snapshot" propstore tests scripts`
  returned zero hits.
- `rg -n -F -- "def world_record" propstore tests scripts`
  returned zero hits.
- `rg -n -F -- "def world_records" propstore tests scripts`
  returned zero hits.
- `rg -n -F -- "_CLAIM_MODEL_TABLES" propstore tests scripts`
  returned zero hits.

### Phase 6 - Runtime Gates

Run:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label derived-build-deletion-rethink tests/test_build_sidecar.py tests/test_sidecar_projection_contract.py tests/test_fixture_schema_parity.py
powershell -File scripts/run_logged_pytest.ps1 -Label derived-build-remediation tests/remediation/phase_1_crits tests/remediation/phase_2_gates tests/remediation/phase_7_race_atomicity
uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --before reports/sqlalchemy-charter-parity/build-orchestration/before.sqlite --build-after sqlalchemy-charter --after reports/sqlalchemy-charter-parity/build-orchestration/after.sqlite --owner build-orchestration --workstream workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/04-propstore-build-orchestration.md --out reports/sqlalchemy-charter-parity/build-orchestration.json
```

Phase 6 execution record:

- `uv run pyright propstore` passed with 0 errors.
- `powershell -File scripts/run_logged_pytest.ps1 -Label derived-build-deletion-rethink tests/test_build_sidecar.py tests/test_sidecar_projection_contract.py tests/test_fixture_schema_parity.py`
  passed 105 tests in 52.36s; log:
  `logs\test-runs\derived-build-deletion-rethink-20260524-145235.log`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label derived-build-remediation tests/remediation/phase_1_crits tests/remediation/phase_2_gates tests/remediation/phase_7_race_atomicity`
  first failed 2 tests because claim-pipeline diagnostics were emitted twice
  after preflight failure and `DocumentSchemaError` from direct materialization
  escaped instead of becoming a claim-validation diagnostic.
- Commit `f2c5dda9 Keep claim pipeline diagnostics single pass` kept the
  repair in the compiler workflow owner: preflight diagnostics are consumed
  once, and direct materialization maps claim schema exceptions into typed
  claim-validation diagnostics.
- `uv run pyright propstore\compiler\workflows.py` passed with 0 errors.
- `powershell -File scripts/run_logged_pytest.ps1 -Label derived-build-remediation-recheck tests/remediation/phase_2_gates/test_T2_2p_compiler_claim_pipeline_output_quarantine.py::test_build_repository_claim_pipeline_none_quarantines_not_raises tests/remediation/phase_2_gates/test_T2_2q_compiler_claim_pipeline_schema_exception_quarantine.py::test_build_repository_claim_pipeline_schema_exception_quarantines_not_raises`
  passed 2 tests in 6.84s; log:
  `logs\test-runs\derived-build-remediation-recheck-20260524-145544.log`.
- Corrected remediation gate:
  `powershell -File scripts/run_logged_pytest.ps1 -Label derived-build-remediation tests/remediation/phase_1_crits tests/remediation/phase_2_gates tests/remediation/phase_7_race_atomicity`
  passed 39 tests in 10.77s; log:
  `logs\test-runs\derived-build-remediation-20260524-145603.log`.
- `uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --before reports/sqlalchemy-charter-parity/build-orchestration/before.sqlite --build-after sqlalchemy-charter --after reports/sqlalchemy-charter-parity/build-orchestration/after.sqlite --owner build-orchestration --workstream workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/04-propstore-build-orchestration.md --out reports/sqlalchemy-charter-parity/build-orchestration.json`
  passed. The report recorded `after_head_sha`
  `444ea1b2168551053976ce90ce5022e5b82728f6`, no failures, and pass status
  for row counts, key sets, diagnostics, FTS, vectors, and table/schema checks.
  The named parity artifacts were unchanged after the run.

After these pass, run the full Propstore gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label derived-build-deletion-full
```

Full gate execution record, 2026-05-24:

- `uv run pyright propstore` passed with 0 errors.
- `powershell -File scripts/run_logged_pytest.ps1 -Label derived-build-deletion-full`
  failed after 3519 passed, 4 skipped, and 1 failed in 433.40s; log:
  `logs\test-runs\derived-build-deletion-full-20260524-145913.log`.
- The failing test was
  `tests/remediation/phase_4_layers/test_T4_1_importlinter_layers.py::test_importlinter_layer_contracts_are_clean`.
- The broken import-linter path is direct evidence that the family placement
  rule above was violated:
  `propstore.source.status -> propstore.families.world_charters ->
  propstore.families.embeddings.declaration -> propstore.heuristic.embed` and
  `propstore.heuristic.embedding_identity`.
- This workstream is not complete. The next repair queue is not an import
  allow-list change; it is deletion-first removal of the replacement family
  surface that recreated generic world/embedding wiring in the wrong owner.

## Completion Criteria

This workstream is complete only when:

- the two deleted files remain deleted and committed;
- every `propstore.derived_build` and `derived_build_plan` reference is gone
  from production and tests;
- every capability formerly supplied by the deleted files has a recorded
  delete/direct-owner/owner-extension disposition;
- no replacement helper module recreates the deleted responsibilities;
- no bad production file encountered during the slice remains merely patched;
- table-name construction helpers and claim-special model routing are deleted
  or the owning file has been deleted and replaced with correct owners;
- search gates pass;
- runtime gates pass;
- the final commit message names the governing principles:
  - bad production symbol means bad file;
  - deletion breakage is rethink, not import repair;
  - Quire owns generic storage/session/schema/model/reference mechanics;
  - Propstore owns semantic behavior only at the real family/domain owner.
