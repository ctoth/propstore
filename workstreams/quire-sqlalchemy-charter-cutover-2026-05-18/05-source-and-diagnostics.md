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
generic Quire SQLAlchemy capability work except where a source gate exposes a
missing prerequisite.

## Prerequisites

Complete the earlier cutover workstreams before starting implementation:

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
uv run scripts/compare_sqlalchemy_charter_parity.py --before <old-sidecar.sqlite> --after <new-sidecar.sqlite> --owner source-diagnostics --out reports/sqlalchemy-charter-parity/source-diagnostics.json
```

Build the sidecar from the same repository snapshot before and after this
workstream.

Compare:

- source table names, primary keys, row counts, and key sets;
- source-status diagnostic table names, primary keys, row counts, and key sets;
- representative source status results;
- representative finalize/promote diagnostic results;
- promotion-blocked diagnostic delete behavior;
- accepted column/table renames, explicitly listed in the commit message.

Fail the phase when a source row, source key, diagnostic row, diagnostic key,
or source-status semantic result disappears. The only accepted disappearance
is a table, helper, or column already named as a deletion target in this file.

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
rg -n -F -- "BUILD_DIAGNOSTICS_PROJECTION" propstore tests
rg -n -F -- "ProjectionTable(" propstore/families/sources propstore/families/diagnostics tests
```

`SourceProjectionRow`, `SOURCE_PROJECTION`, `SourceStatusDiagnosticRow`,
`QuarantinableWriter`, `compile_promotion_blocked_diagnostic_rows`,
`has_build_diagnostics_table`, `select_source_status_diagnostic_rows`,
`BUILD_DIAGNOSTICS_PROJECTION`, and `ProjectionTable(` are zero-hit gates
outside notes, workstreams, docs, and reports.

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
