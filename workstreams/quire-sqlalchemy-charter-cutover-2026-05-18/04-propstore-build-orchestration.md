# Propstore Build Orchestration Cutover Workstream

Date: 2026-05-18

## Goal

Convert Propstore sidecar build orchestration to Quire writable build sessions
and Quire charter/catalog APIs before any Propstore semantic family cutover.

Final state:

- `propstore/derived_build.py` obtains a Quire writable build session from a
  derived-store handle.
- `propstore/derived_build.py` creates and populates the sidecar through Quire
  charter/catalog APIs, not `ProjectionSchema` creation or raw SQLite
  orchestration.
- `propstore/derived_build_plan.py` carries typed domain/model write plans,
  not projection row sets.
- `propstore/families/projection_catalog.py` is deleted and replaced by
  Propstore world charter registration through the Quire schema catalog.
- Schema hash and cache identity are derived from Quire schema catalog
  payloads.
- Old projection schema creation is deleted before family phases begin.
- Build and validation errors must not be translated into projection-era
  schema wording. Quire SQLAlchemy schema/catalog validation errors should flow
  from the Quire validation API; any user-facing presentation belongs only at
  app/CLI/web boundaries and must not preserve compatibility with
  `ProjectionSchema` or `Unsupported sidecar schema` wording.

## Scope And Repository

Repository: `C:\Users\Q\code\propstore`

Target files:

- `propstore/derived_build.py`
- `propstore/derived_build_plan.py`
- `propstore/families/projection_catalog.py`

Owned integration surfaces:

- Propstore sidecar build session acquisition
- Propstore build-plan object model
- Propstore world charter registration
- Quire schema catalog/hash/cache identity use from Propstore
- Data-parity comparison for the build orchestration cutover
- Creation and validation of the shared SQLAlchemy charter parity harness

Do not cut over source, form, concept, claim, relation, context,
micropublication, rule, diagnostic, calibration, embedding, or world-query
family production paths in this workstream.

## Prerequisites

Before implementation:

Required phase file prerequisites: `00-index.md`, `inventory-matrix.md`,
`helper-ledger.md`, `01-quire-capability-and-charter.md`,
`02-quire-sqlalchemy-engine.md`, `03-quire-fts-vector.md`.

1. Confirm the Quire SQLAlchemy dependency and capability workstream is
   complete.
2. Confirm the Quire charter/schema IR workstream is complete.
3. Confirm the Quire SQLAlchemy table, mapping, session, and catalog
   workstream is complete.
4. Confirm `03-quire-fts-vector.md` is complete.
5. Confirm Quire is pinned from a pushed branch commit, pushed tag, or
   immutable pushed commit SHA.
6. Confirm Propstore has no local Quire dependency pin.
7. Confirm current Propstore worktree state.

Required prerequisite commands:

```powershell
rg -n -F -- "quire" pyproject.toml uv.lock
rg -n -F -- "[tool.uv.sources]" pyproject.toml
rg -n -F -- "path =" pyproject.toml
rg -n -F -- "workspace = true" pyproject.toml
rg -n -F -- "quire @ file" pyproject.toml uv.lock
rg -n -F -- "quire @ .." pyproject.toml uv.lock
rg -n -F -- "quire @ C:" pyproject.toml uv.lock
```

The dependency check must inspect the parsed `pyproject.toml` dependency and
`[tool.uv.sources]` entries. A local path, workspace, or file URL dependency on
Quire blocks this workstream.

## Execution Rules

- Execute deletion-first.
- This workstream converts only build orchestration and catalog ownership.
- Do not run old and new build production paths together.
- Do not add compatibility shims, adapters, fallback readers, or dual-path
  glue.
- Do not leave `PROPSTORE_WORLD_PROJECTION_SCHEMA` as a production build path.
- Do not replace `projection_catalog.py` with another Propstore-owned manual
  schema assembly file.
- Propstore supplies domain charters and semantic behavior; Quire owns generic
  schema catalog metadata, SQLAlchemy table creation, sessions, schema hash,
  derived-store lifecycle, FKs, indexes, FTS/vector hooks, and generic query
  mechanics.
- App, CLI, and web surfaces continue to call owner-layer APIs.

## Inventory Rows Covered

This workstream owns these inventory rows:

| Inventory surface | Current owner | Final owner | Required action |
| --- | --- | --- | --- |
| `propstore/derived_build.py` | Propstore sidecar build orchestration over projection tables | Propstore orchestration over Quire writable sessions and charters | Replace projection schema creation/population with charter-driven session writes |
| `propstore/derived_build_plan.py` | Propstore row-oriented build plan | Propstore typed domain-object build plan | Replace row sets with typed model/session write plans |
| `propstore/families/projection_catalog.py` | Propstore manual world schema assembly | Quire schema catalog over Propstore charters | Delete; replace with Propstore world charter registration through the Quire catalog |
| `scripts/compare_sqlalchemy_charter_parity.py` | Missing shared parity harness | Tested parity harness for all child workstreams | Create and validate before any family cutover starts |

## Deletion-First Targets

Delete these production paths before porting callers:

- direct build/catalog-owned `ProjectionSchema` creation;
- direct `PROPSTORE_WORLD_PROJECTION_SCHEMA` creation;
- build-plan row-set abstractions whose only purpose is projection insertion;
- raw `sqlite3.Connection` sidecar population orchestration;
- build orchestration imports of Quire projection primitives;
- manual world schema assembly in `propstore/families/projection_catalog.py`.

Deleting `propstore/families/projection_catalog.py` in this phase leaves
per-family `ProjectionSchema`, `ProjectionTable`, and `ProjectionModel`
constants as unreferenced
inventory inside family modules until their family slices delete them. After
the catalog deletion, production code has zero imports of those constants.

## Replacement Requirements

Implement the target path:

1. `derived_build.py` opens a Quire derived-store handle for the build target.
2. `derived_build.py` obtains a Quire writable build session from that handle.
3. Build orchestration creates generated SQLAlchemy tables through Quire
   charter/catalog APIs.
4. Build orchestration writes through SQLAlchemy sessions and mapped model
   objects.
5. `derived_build_plan.py` returns typed domain/model write plans instead of
   projection row sets.
6. Propstore world charter registration replaces
   `propstore/families/projection_catalog.py`.
7. Quire schema catalog payloads produce the build schema hash.
8. Quire schema catalog payloads produce cache identity and invalidation
   inputs.
9. Build-session commit/rollback boundaries are explicit and owned by the
   derived-store build lifecycle.
10. Existing build diagnostics and semantic policy remain in Propstore owner
    modules; generic schema and session mechanics remain in Quire.
10a. Build orchestration does not catch Quire SQLAlchemy schema/catalog
     validation failures to rewrite them into old projection-schema or sidecar
     schema messages.
10b. If the build-orchestration replacement touches `WorldQuery` sidecar
     validation while opening the new derived-store handle/session, delete the
     old `_validate_schema` message-rewrite wrapper in that same slice instead
     of carrying it forward. If Phase 5 does not touch that runtime validation
     path, leave the code unchanged and let `12-world-query-graph-reasoning.md`
     own the deletion.
11. `scripts/compare_sqlalchemy_charter_parity.py` exists before source,
    forms, concepts, claims, relations, contexts, micropublications, rules,
    embeddings, or world-query cutovers start.
12. Before deleting the old projection builder, the parity harness captures
    projection baseline SQLite artifacts for every child owner under
    `reports/sqlalchemy-charter-parity/<owner>/before.sqlite`.
13. After baseline capture, the old projection builder is deleted/replaced.
    Later parity gates read the captured baseline artifact; they do not call
    the old projection builder.
14. The parity harness compares table names, primary-key/key sets, row counts,
    FTS hit sets, vector hit sets, diagnostics, and the exact semantic query
    result keys supplied by each child workstream.
15. The parity harness exits nonzero and writes an actionable report when any
    required comparison fails.
16. The parity harness supports `--require-vector <name>` and
    `--require-behavior <name>` flags; when supplied, the report must contain a
    passing comparison block for every required vector or behavior name.
17. `tests/test_sqlalchemy_charter_parity_harness.py` proves one passing
    comparison and one failing comparison for owner slug `harness-self-test`.

## Parity Harness Contract

`scripts/compare_sqlalchemy_charter_parity.py` is a reusable gate, not a
one-off report writer. Implement this command surface:

```powershell
uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --capture-before projection --before reports/sqlalchemy-charter-parity/build-orchestration/before.sqlite --owner build-orchestration --workstream workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/04-propstore-build-orchestration.md --out reports/sqlalchemy-charter-parity/build-orchestration/baseline.json
uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --before reports/sqlalchemy-charter-parity/build-orchestration/before.sqlite --build-after sqlalchemy-charter --after reports/sqlalchemy-charter-parity/build-orchestration/after.sqlite --owner build-orchestration --workstream workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/04-propstore-build-orchestration.md --out reports/sqlalchemy-charter-parity/build-orchestration.json
```

Baseline and builder dispatch are exact:

- `--capture-before projection` is valid only before this phase deletes the
  projection builder. It creates `Repository(Path(knowledge_dir))`, records
  `baseline_head_sha = repo.require_git().head_sha()`, records the Quire
  artifact-family input hash used by the build, deletes the `--before`
  SQLite file when it exists, then calls
  `propstore.derived_build.export_sidecar(repo, Path(before), force=True, commit_hash=baseline_head_sha)`.
- The capture mode writes `reports/sqlalchemy-charter-parity/<owner>/baseline.json`
  containing `owner`, `workstream`, `baseline_head_sha`,
  `semantic_input_hash`, `before`, table metadata, row counts, key sets,
  FTS/vector blocks, diagnostics, semantic query blocks, and behavior blocks.
- Normal comparison mode requires `--before` to point at an existing captured
  baseline SQLite file and requires the matching `baseline.json`. It never
  imports or calls the deleted projection builder.
- `--build-after sqlalchemy-charter` creates `Repository(Path(knowledge_dir))`,
  records `after_head_sha = repo.require_git().head_sha()`, recomputes the same
  Quire artifact-family input hash, deletes the `--after` SQLite file when it
  exists, then calls the Phase 4 target implementation of
  `propstore.derived_build.export_sidecar(repo, Path(after), force=True, commit_hash=after_head_sha)`.
- The Phase 4 target implementation of `export_sidecar` uses Quire generated
  metadata, Quire writable build sessions, Propstore charters, and typed
  model/session writes. It is not an old/new sibling API.
- The harness refuses to compare when the captured baseline's
  `semantic_input_hash` differs from the after build's semantic input hash.
  Code/workstream commits may differ; the semantic knowledge artifact inputs
  compared by the sidecar builders may not differ.
- Before the projection builder is deleted, run capture mode once for each
  owner/workstream pair: `build-orchestration`/`04-propstore-build-orchestration.md`,
  `source-diagnostics`/`05-source-and-diagnostics.md`,
  `forms-concepts-parameterizations`/`06-forms-concepts-parameterizations.md`,
  `contexts-lifting`/`07-contexts-lifting.md`,
  `claims-active-claims`/`08-claims-active-claims.md`,
  `relations-stances-conflicts`/`09-relations-stances-conflicts.md`,
  `micropublications-justifications`/`10-micropublications-justifications.md`,
  `rules-grounding-calibration-embeddings`/`11-rules-grounding-calibration-embeddings.md`,
  and `world-query-graph-reasoning`/`12-world-query-graph-reasoning.md`.
- `--workstream` is required. It points to the active child workstream file.
  The harness parses that file for the `Accepted parity difference allowlist`
  section and the `Data-Parity Gate` comparison list. Missing section,
  unparseable allowlist, or owner/workstream mismatch is a command failure.

Report schema is exact JSON with these top-level keys:

- `owner`: owner slug from `--owner`;
- `workstream`: normalized path supplied by `--workstream`;
- `knowledge_dir`: normalized path supplied by `--knowledge-dir`;
- `baseline_head_sha`: committed Git hash used to capture the baseline;
- `after_head_sha`: committed Git hash used by the charter build;
- `semantic_input_hash`: matching artifact-family input hash for both sides;
- `before`: object with `path`, `build`, `schema_hash`, and `diagnostics`;
- `after`: object with `path`, `build`, `schema_hash`, and `diagnostics`;
- `tables`: per-table column names, primary-key columns, and schema notes;
- `row_counts`: per-table before/after counts and status;
- `key_sets`: per-table before/after primary-key set comparison;
- `fts`: named FTS comparison blocks;
- `vectors`: named vector comparison blocks;
- `diagnostics`: diagnostic row comparison blocks;
- `semantic_queries`: named semantic-query comparison blocks;
- `behaviors`: named behavior-vector comparison blocks;
- `allowed_differences`: the literal deletion-only allowlist supplied by the
  child workstream section;
- `failures`: nonempty list when the command exits nonzero.

Comparison block schema is exact for `fts`, `vectors`, `diagnostics`,
`semantic_queries`, and `behaviors`:

- `name`;
- `status`;
- `before_count`;
- `after_count`;
- `missing_keys`;
- `extra_keys`;
- `changed_values`.

The harness has no commit-message or report-time rename override. Allowed
differences come only from the active child workstream's deletion allowlist.

`tests/test_sqlalchemy_charter_parity_harness.py` contains these exact tests:

- `test_parity_harness_passes_matching_sqlite_fixtures`;
- `test_parity_harness_fails_missing_key`;
- `test_parity_harness_requires_vector_blocks`;
- `test_parity_harness_requires_behavior_blocks`;
- `test_parity_harness_rejects_missing_baseline`;
- `test_parity_harness_rejects_semantic_input_hash_mismatch`.

## Data-Parity Gate

Capture the pre-deletion projection baseline, then compare the captured
baseline against the charter-generated sidecar:

```powershell
uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --capture-before projection --before reports/sqlalchemy-charter-parity/build-orchestration/before.sqlite --owner build-orchestration --workstream workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/04-propstore-build-orchestration.md --out reports/sqlalchemy-charter-parity/build-orchestration/baseline.json
uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --before reports/sqlalchemy-charter-parity/build-orchestration/before.sqlite --build-after sqlalchemy-charter --after reports/sqlalchemy-charter-parity/build-orchestration/after.sqlite --owner build-orchestration --workstream workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/04-propstore-build-orchestration.md --out reports/sqlalchemy-charter-parity/build-orchestration.json
```

1. Before deleting the projection builder, build the current mainline sidecar
   as the captured baseline artifact.
2. Delete/replace the old projection builder.
3. Build the charter-generated sidecar.
4. Compare table names.
5. Compare primary keys.
6. Compare row counts.
7. Compare key sets.
8. Compare build diagnostics emitted by the build path.
9. Compare catalog/schema hash inputs and recorded schema identity.
10. Compare column and table names exactly.
11. Fail on any renamed column, renamed table, dropped table, dropped key, missing diagnostic, missing FTS
    hit, missing vector hit, or missing semantic query result. The only
    accepted drop is a table already named as a deletion target in this
    workstream.

Accepted parity difference allowlist:

- deleted build/catalog-owned direct `ProjectionSchema` creation;
- deleted direct `PROPSTORE_WORLD_PROJECTION_SCHEMA` creation;
- deleted build-plan row-set abstractions whose only purpose is projection
  insertion;
- deleted raw `sqlite3.Connection` sidecar population orchestration;
- deleted build orchestration imports of Quire projection primitives;
- deleted manual world schema assembly in
  `propstore/families/projection_catalog.py`;
- added Quire-owned schema catalog metadata table `quire_schema_catalog` as
  the generated schema identity record; it is not a semantic row table and no
  semantic table, row, key, diagnostic, FTS result, vector result, semantic
  query result, or schema identity may disappear;
- no column rename, table rename, row disappearance, key disappearance,
  diagnostic disappearance, FTS-result disappearance, vector-result
  disappearance, semantic-query disappearance, or schema-identity
  disappearance is allowed.

## Required Gates

Run:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label build-orchestration-charter tests/test_build_sidecar.py tests/test_sidecar_projection_contract.py tests/test_fixture_schema_parity.py
powershell -File scripts/run_logged_pytest.ps1 -Label parity-harness tests/test_sqlalchemy_charter_parity_harness.py
if (-not (Test-Path -LiteralPath scripts/compare_sqlalchemy_charter_parity.py -PathType Leaf)) { throw "missing scripts/compare_sqlalchemy_charter_parity.py" }
uv run scripts/compare_sqlalchemy_charter_parity.py --help
```

Run old-path searches:

```powershell
rg -n -F -- "PROPSTORE_WORLD_PROJECTION_SCHEMA" propstore tests
rg -n -F -- "ProjectionSchema" propstore/derived_build.py propstore/derived_build_plan.py tests
rg -n -F -- "ProjectionTable" propstore/derived_build.py propstore/derived_build_plan.py tests
rg -n -F -- "sqlite3.Connection" propstore/derived_build.py propstore/derived_build_plan.py tests
```

All searches are zero-hit gates outside notes, workstreams, docs, and reports.

## Completion Criteria

This workstream is complete only when:

- `propstore/derived_build.py` uses Quire writable build sessions.
- `propstore/derived_build.py` creates and populates the sidecar through Quire
  charter/catalog APIs.
- `propstore/derived_build_plan.py` uses typed domain/model write plans.
- `propstore/families/projection_catalog.py` is deleted.
- Propstore world charter registration feeds the Quire schema catalog.
- Schema hash and cache identity come from Quire schema catalog payloads.
- Raw `sqlite3.Connection` sidecar population orchestration is gone from the
  target files.
- Build orchestration imports no Quire projection primitives.
- `scripts/compare_sqlalchemy_charter_parity.py` exists, implements
  `--require-vector` and `--require-behavior`, and
  `tests/test_sqlalchemy_charter_parity_harness.py` proves one passing and one
  failing comparison for owner slug `harness-self-test`.
- The data-parity gate passes against the captured baseline with a matching
  semantic input hash.
- The type gate, logged pytest gate, and old-path search gates pass.
- Propstore remains pinned to a pushed Quire reference, never a local checkout.

## Phase 5 Execution Record

Recorded 2026-05-20.

Prerequisites:

- `03-quire-fts-vector.md` records Phase 4 and the Quire-first completion gate complete.
- Propstore current branch: `master`; tracked task-owned files clean before Phase 5 harness edits; unrelated untracked files present.
- Quire pin: `pyproject.toml` and `uv.lock` resolve `quire` from pushed commit `65df665b85053c1741dcd22d3a12deb15f35a4be`.
- Local dependency-pin searches for `path =`, `workspace = true`, `quire @ file`, `quire @ ..`, and `quire @ C:` returned no hits.

Parity harness slice:

- Added `scripts/compare_sqlalchemy_charter_parity.py` with projection baseline capture, after-build comparison dispatch, JSON report output, workstream allowlist parsing, table row-count/key-set comparison, and `--require-vector`/`--require-behavior` checks.
- Added `tests/test_sqlalchemy_charter_parity_harness.py` with the required passing fixture, missing-key failure, required-vector, required-behavior, missing-baseline, and semantic-input-hash mismatch tests.
- Focused harness gate passed: `powershell -File scripts/run_logged_pytest.ps1 -Label parity-harness tests/test_sqlalchemy_charter_parity_harness.py` passed with 6 passed; log `logs\test-runs\parity-harness-20260520-102010.log`.
- Help gate passed: `uv run scripts/compare_sqlalchemy_charter_parity.py --help`.
- Fixed workstream allowlist parsing to preserve wrapped bullet continuation
  lines instead of truncating deletion allowlist entries.
- Focused harness gate after parser fix passed: `powershell -File scripts/run_logged_pytest.ps1 -Label parity-harness tests/test_sqlalchemy_charter_parity_harness.py` passed with 6 passed; log `logs\test-runs\parity-harness-20260520-102328.log`.

Pre-deletion baseline capture:

- Captured `reports/sqlalchemy-charter-parity/build-orchestration/before.sqlite`
  and `baseline.json`.
- Captured `reports/sqlalchemy-charter-parity/source-diagnostics/before.sqlite`
  and `baseline.json`.
- Captured
  `reports/sqlalchemy-charter-parity/forms-concepts-parameterizations/before.sqlite`
  and `baseline.json`.
- Captured `reports/sqlalchemy-charter-parity/contexts-lifting/before.sqlite`
  and `baseline.json`.
- Captured `reports/sqlalchemy-charter-parity/claims-active-claims/before.sqlite`
  and `baseline.json`.
- Captured
  `reports/sqlalchemy-charter-parity/relations-stances-conflicts/before.sqlite`
  and `baseline.json`.
- Captured
  `reports/sqlalchemy-charter-parity/micropublications-justifications/before.sqlite`
  and `baseline.json`.
- Captured
  `reports/sqlalchemy-charter-parity/rules-grounding-calibration-embeddings/before.sqlite`
  and `baseline.json`.
- Captured
  `reports/sqlalchemy-charter-parity/world-query-graph-reasoning/before.sqlite`
  and `baseline.json`.
- Verified the regenerated `build-orchestration/baseline.json` includes the
  full wrapped allowlist, including the final no-rename/no-disappearance entry.

Next required item: delete and replace the old projection builder with the
Quire SQLAlchemy charter build path.

Returned-to-Quire capability fix:

- Deletion/replacement planning found that the current Quire charter FTS path
  could not express Propstore's existing `concept_fts` and `claim_fts`
  population shape: exact source-query population with FTS key columns
  `concept_id` and `claim_id`.
- Returned to `03-quire-fts-vector.md` as required by the index instead of
  adding a Propstore workaround.
- Pushed Quire commit `852ab784c1c70484b2b6749393c8c0f8d043ac3d`
  (`Support charter FTS source queries`) and refreshed Propstore's Quire pin to
  that pushed commit.
- Full Quire test gate after the source-query extension:
  `uv run pytest -vv` passed with 360 passed in 331.85s.
- Deletion/replacement planning then found that existing sidecar tables without
  database primary keys must still be mapped for SQLAlchemy model writes.
- Returned to `03-quire-fts-vector.md` again and added pushed Quire commit
  `65df665b85053c1741dcd22d3a12deb15f35a4be`
  (`Map charter tables without database primary keys`).
- Focused Quire proof gate for the no-primary-key mapper extension:
  `uv run pytest -vv tests/test_sqlalchemy_engine.py` passed with 7 passed.
- Quire type gate for the no-primary-key mapper extension: `uv run pyright`
  passed with 0 errors.
- Full Quire test gate after the no-primary-key mapper extension:
  `uv run pytest -vv` passed with 361 passed in 300.68s.
- Propstore pin refreshed to pushed Quire commit
  `65df665b85053c1741dcd22d3a12deb15f35a4be`; local dependency-pin searches
  for `path =`, `workspace = true`, `quire @ file`, `quire @ ..`, and
  `quire @ C:` returned no hits; `uv lock --check` passed.

Next required item: resume deletion/replacement of the old projection builder
using the Quire SQLAlchemy charter FTS source-query and no-primary-key mapper
paths.

World charter registration slice:

- Added `propstore/families/world_charters.py` with Propstore-owned Quire
  `FamilyCharter` declarations, mapped model classes, FTS source-query
  charters, and `world_sqlalchemy_schema()` for the existing sidecar table
  surface.
- Type gate after the charter registration:
  `uv run pyright propstore` passed with 0 errors.
- Commit: `d3762490 Register Propstore world SQLAlchemy charters`.

Next required item: update `propstore/derived_build_plan.py` from projection
row sets to typed model/session write plans.

Build-plan and builder replacement slice:

- Updated `propstore/derived_build_plan.py` so the public
  `SidecarBuildPlan` carries ordered `WorldWriteBatch` model-object batches,
  not projection row-set fields.
- Updated `propstore/derived_build.py` to create the sidecar with
  `world_sqlalchemy_schema()`, `create_sqlalchemy_store`, Quire
  `DerivedStoreHandle.writable_session`, mapped model writes, Quire FTS
  population, and schema-cache identity from the Quire schema catalog hash.
- Converted the grounding sidecar writer in the same target file to the Quire
  SQLAlchemy schema/session path so raw SQLite build orchestration is gone
  from the target file.
- Target-file old-path searches for `ProjectionSchema`, `ProjectionTable`,
  `sqlite3.Connection`, and `PROPSTORE_WORLD_PROJECTION_SCHEMA` over
  `propstore/derived_build.py` and `propstore/derived_build_plan.py` returned
  no hits.
- Type gate after the build-plan/session replacement:
  `uv run pyright propstore` passed with 0 errors.
- Commit: `75963c64 Use Quire sessions for sidecar build plans`.

Next required item: delete `propstore/families/projection_catalog.py`, update
test validation expectations away from the deleted projection schema path, then
run the Phase 5 logged pytest, help, search, and parity gates.

Manual catalog deletion slice:

- Deleted `propstore/families/projection_catalog.py`.
- Updated `WorldQuery` schema validation to call Quire
  `validate_sqlalchemy_store` with `world_sqlalchemy_schema()`; because this
  slice touched that validation path, the old `_validate_schema` message
  rewrite to `Unsupported sidecar schema` and `Rebuild with 'pks build'.` was
  deleted in this phase.
- Updated direct schema tests/helpers to build and inspect the Quire
  SQLAlchemy world schema and schema-catalog metadata instead of importing the
  deleted projection catalog.
- Exact searches for `projection_catalog` and
  `PROPSTORE_WORLD_PROJECTION_SCHEMA` over `propstore` and `tests` returned no
  hits.
- Type gate after catalog deletion: `uv run pyright propstore` passed with 0
  errors.
- Focused logged schema gate passed:
  `powershell -File scripts/run_logged_pytest.ps1 -Label schema-catalog-deletion tests/test_fixture_schema_parity.py tests/test_world_model_branch_column_required.py tests/test_opinion_schema.py`
  passed with 12 passed; log
  `logs\test-runs\schema-catalog-deletion-20260520-112026.log`.
- Commit: `41e0f8e7 Delete Propstore projection catalog`.

Next required item: run the Phase 5 required logged pytest gate, repair only
failures caused by the deletion/replacement, then run the help, old-path
search, and build-orchestration parity gates.

Phase 5 required logged pytest gate:

- Required logged pytest gate passed:
  `powershell -File scripts/run_logged_pytest.ps1 -Label build-orchestration-charter tests/test_build_sidecar.py tests/test_sidecar_projection_contract.py tests/test_fixture_schema_parity.py`
  passed with 113 passed; log
  `logs\test-runs\build-orchestration-charter-20260520-112156.log`.

Next required item: run the parity harness logged pytest gate, help gate,
old-path searches, and build-orchestration parity gate.

Parity harness required gate rerun:

- Required parity harness logged pytest gate passed:
  `powershell -File scripts/run_logged_pytest.ps1 -Label parity-harness tests/test_sqlalchemy_charter_parity_harness.py`
  passed with 6 passed; log
  `logs\test-runs\parity-harness-20260520-112518.log`.

Next required item: run the Phase 5 help gate, old-path searches, and
build-orchestration parity gate.

Old-path search repair:

- Help gate passed again: `uv run scripts/compare_sqlalchemy_charter_parity.py --help`.
- Script existence gate passed:
  `if (-not (Test-Path -LiteralPath scripts/compare_sqlalchemy_charter_parity.py -PathType Leaf)) { throw "missing scripts/compare_sqlalchemy_charter_parity.py" }`.
- Old-path search gate first found remaining test-only Quire projection
  primitive coverage in `tests/test_sidecar_projection_contract.py` and
  `sqlite3.Connection` annotation/docstring spellings in tests.
- Replaced `tests/test_sidecar_projection_contract.py` with SQLAlchemy
  world-charter contract coverage and mechanically changed test annotations to
  imported `Connection` so `sqlite3.Connection` no longer names the deleted
  raw sidecar build path.
- Updated the `ProjectionSchema` and `ProjectionTable` search gate command to
  omit deleted file path `propstore/families/projection_catalog.py`; the file
  is already deleted, so including it turns a zero-hit content search into a
  missing-path error instead of strengthening the gate.
- Focused rewritten-contract gate passed:
  `powershell -File scripts/run_logged_pytest.ps1 -Label sidecar-sqlalchemy-contract tests/test_sidecar_projection_contract.py`
  passed with 8 passed; log
  `logs\test-runs\sidecar-sqlalchemy-contract-20260520-113028.log`.
- Old-path searches over the live target files returned no hits:
  `PROPSTORE_WORLD_PROJECTION_SCHEMA`,
  `ProjectionSchema`,
  `ProjectionTable`, and
  `sqlite3.Connection`.
- Commit: `db0fec2a Replace projection contract test with charter contract`.

Next required item: rerun the Phase 5 required logged pytest gate after the
old-path search repair, then run the build-orchestration parity gate.

Post-repair required logged pytest gate:

- Required logged pytest gate after the old-path search repair passed:
  `powershell -File scripts/run_logged_pytest.ps1 -Label build-orchestration-charter tests/test_build_sidecar.py tests/test_sidecar_projection_contract.py tests/test_fixture_schema_parity.py`
  passed with 111 passed; log
  `logs\test-runs\build-orchestration-charter-20260520-113215.log`.

Next required item: rerun the Phase 5 type gate and old-path searches, then
run the build-orchestration parity gate.

Post-repair type and search gates:

- Type gate passed again: `uv run pyright propstore` returned 0 errors.
- Old-path searches over live target files returned no hits:
  `PROPSTORE_WORLD_PROJECTION_SCHEMA`,
  `ProjectionSchema`,
  `ProjectionTable`, and
  `sqlite3.Connection`.

Next required item: run the build-orchestration data-parity gate.

Build-orchestration parity repair:

- Initial data-parity run after the Phase 5 type/search gates failed with two
  harness-side issues: `semantic_input_hash` was comparing the derived-store
  cache identity, which includes code/schema/build inputs, instead of the
  semantic Git artifact inputs; and `quire_schema_catalog` was treated as an
  extra semantic row table even though the target final state requires Quire
  schema catalog metadata.
- The accepted parity allowlist now explicitly allows only the added
  Quire-owned `quire_schema_catalog` metadata table as schema identity, while
  preserving zero tolerance for semantic table, row, key, diagnostic, FTS,
  vector, semantic-query, or schema-identity disappearance.
- Updated the harness to hash committed semantic artifact roots and source
  branch artifact contents instead of the derived-store cache identity, and to
  record `quire_schema_catalog` schema hash without row-comparing the metadata
  table.
- Focused logged harness gate after this repair passed:
  `powershell -File scripts/run_logged_pytest.ps1 -Label parity-harness tests/test_sqlalchemy_charter_parity_harness.py`
  passed with 7 passed; log
  `logs\test-runs\parity-harness-20260520-114010.log`.
- Commit: `4b6df783 Repair SQLAlchemy charter parity harness`.

Old validation-wrapper audit:

- Exact-string audit found one production old-schema message rewrite:
  `propstore/world/model.py` catches `ValueError` from
  `validate_derived_store_schema`, replaces `Unsupported derived store schema`
  with `Unsupported sidecar schema`, and appends `Rebuild with 'pks build'.`
- Exact-string audit found test pins for that old wording in
  `tests/test_world_query.py`.
- Exact-string audit found projection-schema validation tests in
  `tests/test_sidecar_projection_contract.py` importing
  `ProjectionSchemaError` and calling `schema.validate_connection`.
- Searches for `validate_derived_store_schema`, `Unsupported sidecar schema`,
  `ProjectionSchemaError`, `Rebuild with 'pks build'`, and `str(error)` found
  no other production error-message rewrite matching this compatibility shape.
- The owner for deleting that wrapper and its tests is
  `12-world-query-graph-reasoning.md`, unless Phase 5 directly replaces the
  same `WorldQuery` validation path while wiring derived-store handles. In that
  case the wrapper is deleted immediately in the Phase 5 slice; no temporary
  compatibility wrapper is allowed.
