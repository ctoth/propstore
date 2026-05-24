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

### Phase 6 - Runtime Gates

Run:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label derived-build-deletion-rethink tests/test_build_sidecar.py tests/test_sidecar_projection_contract.py tests/test_fixture_schema_parity.py
powershell -File scripts/run_logged_pytest.ps1 -Label derived-build-remediation tests/remediation/phase_1_crits tests/remediation/phase_2_gates tests/remediation/phase_7_race_atomicity
uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --before reports/sqlalchemy-charter-parity/build-orchestration/before.sqlite --build-after sqlalchemy-charter --after reports/sqlalchemy-charter-parity/build-orchestration/after.sqlite --owner build-orchestration --workstream workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/04-propstore-build-orchestration.md --out reports/sqlalchemy-charter-parity/build-orchestration.json
```

After these pass, run the full Propstore gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label derived-build-deletion-full
```

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
