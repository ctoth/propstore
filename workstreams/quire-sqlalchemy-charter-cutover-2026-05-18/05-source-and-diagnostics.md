# 05 - Source And Diagnostics Workstream

Date: 2026-05-18

## Goal

Cut the Propstore source sidecar and source-status diagnostic paths from the
old projection layer to Quire SQLAlchemy charters.

This workstream owns:

- the source vertical slice;
- source status reads;
- source finalize/promote diagnostic writes and deletes;
- diagnostics helper work required by source status/finalize/promote;
- data parity for source rows and source-tied diagnostics.

It does not own forms, concepts, claims, world-query conversion, embeddings, or
generic Quire SQLAlchemy capability work. Missing generic Quire SQLAlchemy
capability blocks this workstream and returns to Phases 1-4; it is not
discovered or implemented here.

## Prerequisites

Complete the earlier cutover workstreams before starting implementation:

Required phase file prerequisites: `00-index.md`, `inventory-matrix.md`,
`helper-ledger.md`, `01-quire-capability-and-charter.md`,
`02-quire-sqlalchemy-engine.md`, `03-quire-fts-vector.md`,
`04-propstore-build-orchestration.md`.

1. Mechanical order check and current-state inventory confirmation.
2. Quire SQLAlchemy dependency and capability proof.
3. Quire charter/schema IR.
4. Quire SQLAlchemy table/mapping/session/catalog engine.
5. Quire FTS and vector implementation.
6. Propstore build orchestration cutover.

No Propstore source production cutover starts until the Quire and
build-orchestration prerequisites pass. Source is not a place to discover
whether SQLAlchemy can handle sessions, schema catalogs, JSON adapters, enum
conversion, data parity, or build orchestration.

Before implementation:

- reread `reports/code-inventory-2026-05-17.md`;
- reread `notes/architecture-wanted-outcome-2026-05-17.md`;
- confirm the Propstore and Quire worktree states;
- confirm Propstore is pinned to a pushed Quire commit, never a local path;
- run or update the phase-order checker proving this workstream follows the
  prerequisite workstreams.

## Inventory Rows

| Inventory surface | Current owner | Final owner | Required action |
| --- | --- | --- | --- |
| `propstore/families/sources/declaration.py` projection pieces | Source sidecar projection | Source charter plus Quire SQLAlchemy | Delete projection rows/tables/helpers |
| `propstore/source/status.py` | Source status SQL queries | Source owner query over Quire session | Replace raw SQL with model/session query |
| `propstore/source/finalize.py` and `propstore/source/promote.py` | Source promotion/finalize diagnostics into sidecar surfaces | Source subsystem plus diagnostic charter | Keep semantics; route diagnostics through typed diagnostic models |
| `propstore/families/diagnostics/declaration.py` projection pieces | Build diagnostics projection | Diagnostic charter plus typed diagnostics | Delete projection table plumbing required by source status/finalize/promote |
| `propstore/core/claim_values.py` source/trust payload constructors | Generic mapping constructors for source value objects | Explicit source document/JSON payload constructors | Rename to boundary-specific constructors; keep value validation |
| `propstore/derived_build.py` | Propstore sidecar build orchestration over projection tables | Propstore orchestration over Quire writable sessions and charters | Use charter-driven session writes for source and source diagnostics |
| `propstore/derived_build_plan.py` | Propstore row-oriented build plan | Propstore typed domain-object build plan | Carry typed source and diagnostic write plans |

## Execution Rules

Execute deletion-first. Do not keep old and new source production paths in
parallel.

Use this loop:

1. Read the source and diagnostics inventory entries plus current files.
2. List every current production caller that imports or consumes source
   projection rows, raw source-status SQL selectors, or diagnostic row helpers.
3. Name the target model classes in the phase notes or commit message.
4. Delete the old production projection/read-model surface first.
5. Run the smallest import/type/test command that exposes the next failures.
6. Fix only failures caused by the deletion in this workstream and the named
   caller list.
7. Replace raw SQLite access with Quire SQLAlchemy session/model access.
8. Replace loose dict/list/row payloads with typed model objects.
9. Delete field-specific coercers once generic charter conversion covers the
   field.
10. Run the source and diagnostics gates.
11. Run the old-path search gates.
12. Run the data-parity gate.
13. Commit only the source/diagnostics slice when executing this workstream.

Delete a helper when its body is a table-shaped `SELECT`, `COUNT`, `INSERT`,
`DELETE`, row attachment, row coercion, or projection-model wrapper with no
Propstore semantic policy. Keep and move semantic code when it owns
source-local lowering, quarantine/blocked policy, authored-document identity,
or diagnostic meaning. After moving kept semantics, delete the original
helper-shaped production path.

## Target Models

Source models:

- `Source`
- `SourceOrigin`
- `SourceTrust`

Diagnostic model needed by source/status/finalize/promote:

- `BuildDiagnostic`

Source storage columns for nested data:

- `origin`
- `trust`
- `quality`
- `derived_from`

No `_json` suffixes are permitted in source storage columns.

## Deletion Targets

Source deletion-first targets:

- `SourceProjectionRow`;
- `SOURCE_PROJECTION`;
- source-specific opinion JSON helper code that generic JSON storage replaces;
- generic source/trust `from_mapping` constructors in
  `propstore/core/claim_values.py`;
- source `sqlite3.Connection` insertion helpers;
- source row-carrier objects whose only job is to aggregate projection rows.

Diagnostics deletion/replacement targets tied to source/status/finalize/promote:

- diagnostics projection table declarations used for source status;
- raw diagnostic insert/delete/select helpers used by finalize/promote/status;
- `SourceStatusDiagnosticRow`;
- `QuarantinableWriter`;
- `Written` and `Quarantined` row-coupled reports;
- `has_build_diagnostics_table`;
- raw promotion-blocked diagnostic row compilation.

Do not delete diagnostic semantics. Diagnostic meaning remains in Propstore and
writes through typed diagnostic models.

## Caller And Update Surfaces

Update these source callers:

- `propstore/derived_build.py`;
- `propstore/derived_build_plan.py`;
- `propstore/source/status.py`;
- `propstore/source/finalize.py`;
- `propstore/source/promote.py`;
- app and CLI source/status callers that read source sidecar status.

Update these diagnostics callers where they are tied to source
status/finalize/promote:

- `propstore/families/diagnostics/declaration.py`;
- source finalize/promote paths that record promotion-blocked diagnostics;
- source status paths that read build diagnostics;
- build orchestration paths that record source authoring/pass/quarantine
  diagnostics.

## Helper Classification

File: `propstore/families/sources/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `SourceProjectionRow` | delete | Replace with `Source` model. |
| `_opinion_json` | delete | Generic typed JSON storage belongs to Quire JSON adapter. |
| `compile_source_sidecar_rows` | replace | Replace with `Source` model construction. |
| `populate_sources` | delete | Replace with SQLAlchemy session add/flush. |

File: `propstore/core/claim_values.py`.

| Helper/surface | Classification | Required final owner/action |
| --- | --- | --- |
| `_opinion_from_mapping` | replace | Replace with boundary-specific source/trust payload conversion or direct typed construction. |
| `SourceOrigin.from_mapping` | replace | Rename to an explicit boundary constructor such as `from_json_payload` or construct directly from typed source values. |
| `SourceTrust.from_mapping` | replace | Rename to an explicit boundary constructor such as `from_json_payload` or construct directly from typed source values. |
| `ClaimSource.from_mapping` | replace | Rename to an explicit boundary constructor such as `from_json_payload` or construct directly from typed source values. |

File: `propstore/families/diagnostics/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `QuarantineDiagnostic` | keep-boundary | Keep as semantic diagnostic input value object with no row coupling. |
| `Written` | replace | Replace with typed write/quarantine report not tied to projection insertion. |
| `Quarantined` | replace | Replace with typed write/quarantine report not tied to projection insertion. |
| `SourceStatusDiagnosticRow` | replace | Replace with typed source-status diagnostic view over `BuildDiagnostic`. |
| `QuarantinableWriter` | replace | Replace raw insert writer with diagnostic service using SQLAlchemy session. |
| `record_build_exception` | replace | Replace raw insert with diagnostic service/session add. |
| `record_embedding_restore_diagnostic` | replace | Replace raw insert with diagnostic service/session add. |
| `record_pass_diagnostics` | move | Keep diagnostic mapping semantics; write through diagnostic service/session. |
| `record_authoring_diagnostics` | move | Keep authoring diagnostic semantics; write through diagnostic service/session. |
| `record_quarantine_diagnostics` | move | Keep quarantine diagnostic semantics; write through diagnostic service/session. |
| `compile_promotion_blocked_diagnostic_rows` | replace | Replace projection rows with `BuildDiagnostic` model construction. |
| `has_build_diagnostics_table` | delete | Schema presence validation belongs to Quire catalog validation. |
| `select_build_diagnostics` | replace | Replace with SQLAlchemy query over `BuildDiagnostic`. |
| `select_source_status_diagnostic_rows` | replace | Replace with typed source-status diagnostic query. |
| `delete_promotion_blocked_diagnostics` | replace | Replace with SQLAlchemy delete/query scoped to `BuildDiagnostic`. |

## Implementation Requirements

- Define the source charter in the source family declaration.
- Derive YAML/document IO and SQLAlchemy mapping from that charter.
- Build inserts source records through a Quire SQLAlchemy session.
- Runtime reads source objects through the session.
- Source status queries typed `Source` and `BuildDiagnostic` models through
  owner-layer APIs, not raw SQL or sidecar connections.
- Finalize/promote keep source-local authoring and promotion semantics, but
  create/delete diagnostics through the typed diagnostic service/session.
- Canonical/master surfaces reject source-local-only fields and shapes.
- Source-local handles are lowered explicitly inside the source subsystem
  before canonical writes.
- Do not introduce source-specific JSON helper names when the generic Quire
  JSON adapter owns conversion.

## Data-Parity Gate

```powershell
uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --before reports/sqlalchemy-charter-parity/source-diagnostics/before.sqlite --build-after sqlalchemy-charter --after reports/sqlalchemy-charter-parity/source-diagnostics/after.sqlite --owner source-diagnostics --workstream workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/05-source-and-diagnostics.md --out reports/sqlalchemy-charter-parity/source-diagnostics.json
```

Compare the captured projection baseline against the charter-generated sidecar
for this workstream.

Compare:

- source table names, primary keys, row counts, and key sets;
- source-status diagnostic table names, primary keys, row counts, and key sets;
- `inspect_source_status` output for the source-status fixtures exercised by
  `tests/test_cli_source_status.py` and
  `tests/remediation/phase_7_race_atomicity/test_T7_5c_source_status_like_escape.py`;
- `finalize_source_branch` diagnostic output for the micropublication finalize
  fixture exercised by `tests/test_finalize_micropub_required.py`;
- `promote_source_branch`, `collect_source_promotion_blocked_facts`, and
  `collect_all_source_promotion_blocked_facts` outputs for the source
  promotion fixtures exercised by `tests/test_source_promotion_alignment.py`
  and `tests/test_source_promote_dangling_refs.py`;
- promotion-blocked diagnostic delete behavior;
- exact column and table names.

Fail the phase when a source row, source key, diagnostic row, diagnostic key,
or source-status semantic result disappears. The only accepted disappearance
is a table, helper, or column already named as a deletion target in this file.

Accepted parity difference allowlist:

- deleted source projection constants, row classes, row carriers, table
  helpers, diagnostic table helpers, and raw sidecar selectors named in this
  file's deletion targets;
- source storage columns `origin_type`, `origin_value`, `origin_retrieved`,
  and `origin_content_ref` are collapsed into the typed JSON value-object
  column `origin`; the stored semantic payload must still match the captured
  baseline;
- source storage column `prior_base_rate` is collapsed into the typed JSON
  value-object column `trust` together with the source trust status; the stored
  semantic payload must still match the captured baseline;
- source storage columns `quality_json` and `derived_from_json` are renamed to
  `quality` and `derived_from` because this workstream's target model forbids
  `_json` suffixes in source storage columns; the stored semantic payloads must
  still match the captured baseline;
- no other column rename, table rename, source row disappearance, source key
  disappearance, diagnostic row disappearance, diagnostic key disappearance,
  or source-status semantic-result disappearance is allowed.

## Required Gates

Run:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label source-charter tests/test_fixture_schema_parity.py tests/test_sidecar_projection_contract.py tests/test_required_schema_completeness.py
```

Run source old-path searches:

```powershell
rg -n -F -- "SourceProjectionRow" propstore tests
rg -n -F -- "SOURCE_PROJECTION" propstore tests
rg -n -F -- "quality_json" propstore tests
rg -n -F -- "derived_from_json" propstore tests
rg -n -F -- "_opinion_from_mapping" propstore/core/claim_values.py tests
rg -n -F -- "from_mapping" propstore/core/claim_values.py tests
```

Run diagnostics old-path searches for this slice:

```powershell
rg -n -F -- "SourceStatusDiagnosticRow" propstore tests
rg -n -F -- "QuarantinableWriter" propstore tests
rg -n -F -- "compile_promotion_blocked_diagnostic_rows" propstore tests
rg -n -F -- "has_build_diagnostics_table" propstore tests
rg -n -F -- "select_source_status_diagnostic_rows" propstore tests
rg -n -F -- "BUILD_DIAGNOSTICS_PROJECTION" propstore/families/diagnostics tests
rg -n -F -- "ProjectionTable(" propstore/families/sources propstore/families/diagnostics tests
```

`SourceProjectionRow`, `SOURCE_PROJECTION`, `SourceStatusDiagnosticRow`,
`QuarantinableWriter`, `compile_promotion_blocked_diagnostic_rows`,
`has_build_diagnostics_table`, `select_source_status_diagnostic_rows`,
`BUILD_DIAGNOSTICS_PROJECTION` under `propstore/families/diagnostics`, and
`ProjectionTable(` under source/diagnostic paths are zero-hit gates outside
notes, workstreams, docs, and reports. Claim-family diagnostic writes are owned
by `08-claims-active-claims.md`.

`quality_json` and `derived_from_json` are zero-hit gates for production
Propstore code.

## Completion Gate

This workstream is complete only when:

- `Source`, `SourceOrigin`, `SourceTrust`, and source-tied `BuildDiagnostic`
  reads/writes are mapped through Quire SQLAlchemy charters;
- source build writes use Quire writable sessions;
- source status uses owner-layer model/session queries;
- finalize/promote diagnostic semantics are preserved and no longer write raw
  diagnostic rows;
- all deletion targets in this file are gone from production code;
- source and source-diagnostic data parity passes;
- the required pyright, pytest, and search gates pass.

## Phase 6 Execution Record

Recorded 2026-05-20.

Prerequisites:

- Reread `reports/code-inventory-2026-05-17.md`; it exists and remains the
  controlling code inventory.
- Reread `notes/architecture-wanted-outcome-2026-05-17.md`; it says Quire owns
  the generic charter/schema engine, SQLAlchemy mapping/session machinery,
  schema catalog, derived SQLite lifecycle, and query/index mechanics, while
  Propstore owns source semantics.
- Propstore current branch: `master`; tracked task-owned files clean before
  Phase 6 edits; unrelated untracked files present.
- Quire current branch: `master`; tracked files clean; unrelated untracked
  notes/reports/prompts/reviews paths present.
- Order checker passed:
  `uv run scripts/check_workstream_order.py workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/00-index.md`
  returned `workstream order ok`.
- Quire pin: `pyproject.toml` and `uv.lock` resolve `quire` from pushed commit
  `65df665b85053c1741dcd22d3a12deb15f35a4be`.
- Local dependency-pin searches for `path =`, `workspace = true`,
  `quire @ file`, `quire @ ..`, and `quire @ C:` returned no hits.
- Read current source/diagnostics files:
  `propstore/families/sources/declaration.py`,
  `propstore/families/diagnostics/declaration.py`,
  `propstore/source/status.py`, `propstore/source/finalize.py`,
  `propstore/source/promote.py`, `propstore/core/claim_values.py`,
  `propstore/derived_build_plan.py`, `propstore/derived_build.py`, and
  `propstore/families/world_charters.py`.
- Current caller inventory found source projection usage in
  `propstore/derived_build_plan.py`, `propstore/families/sources/declaration.py`,
  `propstore/families/claims/declaration.py`, and
  `tests/test_sidecar_source_projection.py`; diagnostics projection usage in
  `propstore/families/diagnostics/declaration.py`,
  `propstore/families/claims/declaration.py`, and source status/finalize/promote
  paths; and source `_json` storage columns in `propstore/families/world_charters.py`,
  `propstore/families/sources/declaration.py`, claim projection compatibility
  code, and source projection tests.
- Workstream parity contradiction repaired before implementation: the target
  model forbids source `_json` storage suffixes, so the allowlist now permits
  only `quality_json` -> `quality` and `derived_from_json` -> `derived_from`
  while requiring payload parity and forbidding every other column/table/row/key
  disappearance.
- Verified Quire generic charter conversion before source edits:
  `quire/charters.py` exposes `CharterField(json_value_object=True)`,
  `quire/sql_types.py` lowers it to `JsonValueObject`, and
  `quire/sqlalchemy_schema.py` serializes dataclass/mapping payloads through
  `JsonValueObject` without Propstore field-specific JSON helper names.
- Target source model classes for the deletion-first source slice:
  `Source`, `SourceOrigin`, and `SourceTrust`. The source charter stores
  nested source payloads in `origin`, `trust`, `quality`, and `derived_from`.
- Workstream parity allowlist refined after verifying the target source shape:
  old flat origin columns collapse into `origin`, `prior_base_rate` collapses
  into `trust`, and `quality_json`/`derived_from_json` become
  `quality`/`derived_from`; source keys, row counts, and semantic payloads
  remain non-negotiable.
- Commit `cf305578` deleted the source projection production surface:
  `SourceProjectionRow`, `SOURCE_PROJECTION`, `_opinion_json`,
  `compile_source_sidecar_rows`, and `populate_sources` are gone from
  `propstore/families/sources/declaration.py`.
- Commit `cf305578` defines the source-owned charter and mapped source models
  in `propstore/families/sources/declaration.py`: `Source`, `SourceOrigin`,
  `SourceTrust`, plus the `quality` value object required for the named
  storage column.
- Commit `cf305578` updates `propstore/families/world_charters.py` to consume
  `source_charter()`, updates `propstore/derived_build_plan.py` to carry
  typed source models, and updates `propstore/derived_build.py` so Quire maps
  the source model before build-plan construction.
- Focused source-charter gate passed:
  `powershell -File scripts/run_logged_pytest.ps1 -Label source-charter-focused tests/test_sidecar_source_projection.py tests/test_sidecar_projection_contract.py`
  returned `9 passed`; log:
  `logs/test-runs/source-charter-focused-20260520-115803.log`.
- Commit `c1864f55` removed the remaining `SOURCE_PROJECTION` production
  import by changing the claim read-plan's temporary source join metadata to
  the new charter source columns. This is a Phase 6 source-column follow-up,
  not the Phase 8 claim projection cutover.
- Focused source old-path checks after `c1864f55`: `SOURCE_PROJECTION`,
  `quality_json`, and `derived_from_json` returned zero production/test hits;
  focused pyright over `propstore/families/claims/declaration.py` and
  `propstore/families/claims/projection_model.py` returned 0 errors.
- Commit `90dac376` deleted the diagnostic projection table surface needed by
  Phase 6 source status/finalize/promote: `BUILD_DIAGNOSTICS_PROJECTION`,
  `SourceStatusDiagnosticRow`, `QuarantinableWriter`, `Written`,
  `Quarantined`, `has_build_diagnostics_table`,
  `select_source_status_diagnostic_rows`, and
  `compile_promotion_blocked_diagnostic_rows` are gone from
  `propstore/families/diagnostics/declaration.py`.
- Commit `90dac376` routes source-status diagnostics through Quire
  SQLAlchemy sessions and the mapped `BuildDiagnostic` model, updates
  `WorldQuery.build_diagnostics()` to query through the derived store session,
  and keeps source promotion-blocked diagnostic semantics as typed diagnostic
  objects.
- Focused diagnostics pyright passed:
  `uv run pyright propstore/families/diagnostics/declaration.py propstore/source/status.py propstore/world/model.py propstore/derived_build.py propstore/families/claims/declaration.py propstore/families/claims/stages.py`
  returned 0 errors.
- Focused diagnostics/source-status gate passed:
  `powershell -File scripts/run_logged_pytest.ps1 -Label source-diagnostics-focused tests/test_cli_source_status.py tests/remediation/phase_7_race_atomicity/test_T7_5c_source_status_like_escape.py tests/remediation/phase_2_gates/test_T2_1_quarantine_writer.py`
  returned `7 passed`; log:
  `logs/test-runs/source-diagnostics-focused-20260520-121239.log`.
- Commit `152add0c` renamed the source/trust generic mapping constructors in
  `propstore/core/claim_values.py` to boundary-specific JSON payload
  constructors: `SourceOrigin.from_json_payload`,
  `SourceTrust.from_json_payload`, `ClaimSource.from_json_payload`, and
  `_opinion_from_json_payload`.
- Direct old-name searches after `152add0c` returned no hits in production or
  tests for `SourceOrigin.from_mapping`, `SourceTrust.from_mapping`,
  `ClaimSource.from_mapping`, and `_opinion_from_mapping`.
- Focused source/trust payload pyright passed:
  `uv run pyright propstore/core/claim_values.py propstore/families/claims/projection_model.py`
  returned 0 errors.
- Focused source/trust payload gate passed:
  `powershell -File scripts/run_logged_pytest.ps1 -Label source-trust-payload tests/test_prior_base_rate_is_opinion.py tests/test_sidecar_projection_contract.py`
  returned `12 passed`; log:
  `logs/test-runs/source-trust-payload-20260520-121521.log`.
- Commit `668ea5f9` removed the remaining generic `from_mapping` boundary
  constructor spelling from `propstore/core`, `propstore/families`,
  `propstore/world`, `propstore/worldline`, `propstore/support_revision`, and
  tests by renaming row-shaped constructors to `from_row_mapping` and
  payload-shaped constructors to `from_json_payload`.
- Commit `668ea5f9` also restored current Quire SQLAlchemy store validation
  semantics in `WorldQuery`: schema table/column validation reports
  `Unsupported SQLAlchemy store`, and Propstore-owned semantic meta
  row/version checks remain explicit.
- Exact required `from_mapping` gate passed:
  `rg -n -F -- "from_mapping" propstore/core propstore/families propstore/world propstore/worldline propstore/support_revision tests`
  returned no hits.
- Affected-package pyright passed:
  `uv run pyright propstore/core propstore/families propstore/world propstore/worldline propstore/support_revision`
  returned 0 errors.
- Focused schema-validation repair gate passed:
  `powershell -File scripts/run_logged_pytest.ps1 -Label worldquery-schema-validation tests/test_world_query.py::TestWorldQuerySidecarPath::test_worldmodel_rejects_partial_sidecar_schema tests/test_world_query.py::TestWorldQuerySidecarPath::test_worldmodel_rejects_unsupported_schema_version tests/test_world_query.py::TestWorldQuerySidecarPath::test_worldmodel_rejects_boundary_schema_breakage`
  returned `5 passed`; log:
  `logs/test-runs/worldquery-schema-validation-20260520-122041.log`.
- Focused boundary-constructor rename gate passed:
  `powershell -File scripts/run_logged_pytest.ps1 -Label boundary-constructor-rename tests/support_revision/revision_assertion_helpers.py tests/remediation/phase_3_ignorance/test_T3_5_activation_unknown_cel.py tests/architecture/test_argumentation_pin_aba_adf.py tests/test_core_graph_types.py tests/test_defeasible_conformance_tranche.py tests/test_epistemic_history.py tests/test_lifting_blocked_in_provenance.py tests/test_mapping_boundary_failures.py tests/test_pls_property.py tests/test_resolution_helpers.py tests/test_revision_event_contract.py tests/test_worldline_result_boundaries.py tests/test_worldline_revision_event_capture.py tests/test_world_query.py`
  returned `219 passed`; log:
  `logs/test-runs/boundary-constructor-rename-20260520-122103.log`.
- Final Phase 6 source old-path searches passed with zero hits:
  `SourceProjectionRow`, `SOURCE_PROJECTION`, `quality_json`,
  `derived_from_json`, `_opinion_from_mapping`, and `from_mapping` under the
  required source paths.
- Final Phase 6 diagnostics old-path searches passed with zero hits:
  `SourceStatusDiagnosticRow`, `QuarantinableWriter`,
  `compile_promotion_blocked_diagnostic_rows`, `has_build_diagnostics_table`,
  `select_source_status_diagnostic_rows`, `BUILD_DIAGNOSTICS_PROJECTION` under
  `propstore/families/diagnostics`, and `ProjectionTable(` under source,
  diagnostics, and tests.
- Required Phase 6 pyright passed:
  `uv run pyright propstore` returned 0 errors.
- Required Phase 6 pytest gate passed:
  `powershell -File scripts/run_logged_pytest.ps1 -Label source-charter tests/test_fixture_schema_parity.py tests/test_sidecar_projection_contract.py tests/test_required_schema_completeness.py`
  returned `12 passed`; log:
  `logs/test-runs/source-charter-20260520-122523.log`.
- Required Phase 6 parity gate passed:
  `uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --before reports/sqlalchemy-charter-parity/source-diagnostics/before.sqlite --build-after sqlalchemy-charter --after reports/sqlalchemy-charter-parity/source-diagnostics/after.sqlite --owner source-diagnostics --workstream workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/05-source-and-diagnostics.md --out reports/sqlalchemy-charter-parity/source-diagnostics.json`
  exited 0. The report recorded no failures, row-count and key-set pass
  statuses for `source` and `build_diagnostics`, and the generated
  `after.sqlite` source schema was verified directly with
  `PRAGMA table_info(source)` to use `origin`, `trust`, `quality`, and
  `derived_from`.
- Phase 6 completion gate is satisfied: source build writes use Quire
  writable sessions, source status reads through owner-layer
  model/session queries, finalize/promote diagnostics route through typed
  `BuildDiagnostic` objects, all named deletion targets are gone from
  production code, parity passes, and the required type/test/search gates pass.
