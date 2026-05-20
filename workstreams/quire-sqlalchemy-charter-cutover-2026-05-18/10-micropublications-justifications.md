# 10 - Micropublications And Justifications Workstream

Date: 2026-05-18

## Refactor Zen

This workstream succeeds only if the refactor removes duplicate structure and
makes the project smaller, clearer, and more beautiful. Field and schema shape
is written once in Quire charters or in the exact Propstore semantic owner; do
not restate it in helper families, casts, kwargs builders, row DTOs, projection
models, or model-layer normalizers. After an IO boundary has parsed input, the
type system carries meaning: no generic coercion, loose mapping repair, shim,
adapter, alias, compatibility bridge, or old/new dual path is allowed. Delete
the old production surface first; compiler, type, test, and search failures are
the work queue. If a bridge feels necessary, stop and move parsing/validation
to the owning boundary or add the missing Quire generic capability.

## Goal

Cut micropublications and justifications from projection rows, row dictionaries,
and duplicate conversion schemas to typed Propstore domain models backed by
Quire SQLAlchemy charters.

Final state:

- `Justification` is the mapped justification model used for sidecar reads and
  writes.
- `Micropublication` is the mapped micropublication model used for sidecar
  reads and writes.
- `MicropublicationClaimLink` is the mapped association object for
  micropublication-to-claim links and owns link metadata.
- Authored `JustificationDocument` and `MicropublicationDocument` remain
  Propstore-authored document shapes.
- Micropublication evidence/context semantics remain in Propstore
  micropublication owners.
- The active-graph-derived justification surface is named and implemented as a
  semantic view, not as a duplicate schema or row-conversion layer.
- ASPIC and world justification projection behavior consumes typed
  justification and micropublication models or owner-layer views.
- `propstore/families/micropublications/declaration.py` no longer owns generic
  projection, table creation, row carrier, select, or population plumbing.
- `propstore/core/micropublications.py` no longer repairs projection rows or
  exposes generic mapping coercion.
- `propstore/core/justifications.py` no longer owns duplicated canonical
  schema/conversion behavior.

## Prerequisites

Complete the earlier cutover workstreams before starting implementation:

Required phase file prerequisites: `00-index.md`, `inventory-matrix.md`,
`helper-ledger.md`, `01-quire-capability-and-charter.md`,
`02-quire-sqlalchemy-engine.md`, `03-quire-fts-vector.md`,
`04-propstore-build-orchestration.md`, `05-source-and-diagnostics.md`,
`06-forms-concepts-parameterizations.md`, `07-contexts-lifting.md`,
`08-claims-active-claims.md`, `09-relations-stances-conflicts.md`.

1. Mechanical order check and current-state inventory confirmation.
2. Quire SQLAlchemy dependency and capability proof.
3. Quire charter/schema IR.
4. Quire SQLAlchemy table/mapping/session/catalog engine.
5. Quire FTS and vector implementation.
6. Propstore build orchestration cutover.
7. `05-source-and-diagnostics.md`.
8. `06-forms-concepts-parameterizations.md`.
9. `07-contexts-lifting.md`.
10. `08-claims-active-claims.md`.
11. `09-relations-stances-conflicts.md`.

Before implementation:

- reread `00-index.md`;
- reread `inventory-matrix.md`;
- reread this file;
- reread the justifications and micropublications phase in
  `workstreams/quire-sqlalchemy-charter-cutover-workstream-2026-05-18.md`;
- confirm Propstore and Quire worktree states;
- confirm Propstore is pinned to a pushed Quire commit, never a local path;
- run or update the phase-order checker proving this workstream follows its
  prerequisites.

This workstream is blocked until the prerequisite workstreams have delivered
Quire-generated charters, mappings, sessions, relationships, association
objects, JSON adapters, catalog metadata, and build orchestration over writable
sessions.

## Inventory Rows

| Inventory surface | Current owner | Final owner | Required action |
| --- | --- | --- | --- |
| `propstore/core/justifications.py` | Active graph justification view | Propstore semantic justification view | Keep semantic view; delete duplicate schema/conversion role |
| `propstore/families/claims/projection_model.py` justification residual | `JUSTIFICATION_STORAGE_MODEL` co-located in the old claim projection module | `Justification` charter plus justification owner APIs | Delete the residual and remove the file after Phase 8 has deleted claim-owned symbols |
| `propstore/families/micropublications/declaration.py` projection pieces | Micropub projection/query API | Micropub charter plus association object | Delete generic projection/query plumbing |

The broader world, graph, ASPIC, and worldline conversion rows remain owned by
the later WorldQuery/graph/reasoning workstream. This slice updates those
callers only when deletion of the micropublication or justification projection
surface exposes a direct import/type failure in the current family cutover.

## Target Models

Declare these Propstore domain models through the Quire charter system:

- `Justification`
- `Micropublication`
- `MicropublicationClaimLink`

Model requirements:

- `MicropublicationClaimLink` is an association object, not a hidden secondary
  table;
- link role, ordinal, evidence/context binding, and related payload metadata
  are typed fields on the association object;
- justification links to typed claim, stance, argumentation, or
  micropublication identities through Quire reference/FK APIs;
- generic string tuple parsing, null conversion, JSON conversion, table
  creation, population, and row selection belong to Quire charter/session
  machinery;
- document boundary constructors use boundary-specific names and do not use
  generic `from_mapping` in core/family runtime paths.

## Deletion Targets

Delete these old production surfaces first, then use import/type/test failures
as the work queue:

- micropublication projection tables/models/query plans;
- residual `propstore/families/claims/projection_model.py` after claim-owned
  symbols have been deleted by Phase 8;
- micropublication `*ProjectionRow` classes;
- `MicropublicationProjectionRow`;
- `MicropublicationClaimProjectionRow`;
- `MicropublicationSidecarRows`;
- `ActiveMicropublication`;
- `ActiveMicropublicationInput`;
- `MICROPUBLICATION_PROJECTION`;
- `MICROPUBLICATION_CLAIM_PROJECTION`;
- `MICROPUBLICATION_ROW_MODEL`;
- `JUSTIFICATION_STORAGE_MODEL`;
- `ActiveMicropublication.from_mapping`;
- `coerce_active_micropublication`;
- `_parse_string_tuple`;
- `compile_micropublication_sidecar_rows`;
- `compile_micropublication_sidecar_rows_with_diagnostics` row output;
- `create_micropublication_tables`;
- `populate_micropublications`;
- `select_all_micropublications`;
- justification row dictionaries;
- duplicated `CanonicalJustification` schema/conversion role;
- generic `from_mapping` constructors in
  `propstore/core/justifications.py`.

This phase owns final deletion of `propstore/families/claims/projection_model.py`.
At the start of this phase, the only permitted top-level definitions remaining
in that file are `_nullable_text`, `_claim_id`, `TEXT_CODEC`,
`CLAIM_ID_CODEC`, `JUSTIFICATION_STORAGE_MODEL`, and `JUSTIFICATION_TABLE`.
If any other top-level definition remains in that file, Phase 8 is incomplete
and this phase is blocked.

## Helper Classification

Files: `propstore/core/micropublications.py` and
`propstore/families/micropublications/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `_parse_string_tuple` | delete | Generic row string parsing is deleted. |
| `ActiveMicropublication` | delete | Replace with typed `Micropublication` plus `MicropublicationClaimLink`; active is a query state, not a second object family. |
| `ActiveMicropublicationInput` | delete | Runtime receives typed `Micropublication`; dict/mapping input unions are deleted. |
| `ActiveMicropublication.from_mapping` | delete | Projection-row construction path is deleted. |
| `coerce_active_micropublication` | delete | Runtime receives typed `Micropublication`; mapping coercion is deleted. |
| `MicropublicationProjectionRow` | delete | Replace with `Micropublication` model. |
| `MicropublicationClaimProjectionRow` | delete | Replace with `MicropublicationClaimLink` association object. |
| `MicropublicationSidecarRows` | delete | Replace with typed write plan/session adds. |
| `compile_micropublication_sidecar_rows` | replace | Replace with typed `Micropublication` and link model construction. |
| `compile_micropublication_sidecar_rows_with_diagnostics` | move | Keep missing-claim quarantine semantics in micropublication owner; delete row output. |
| `create_micropublication_tables` | delete | Quire charter creates tables. |
| `populate_micropublications` | delete | Replace with SQLAlchemy session add/flush. |
| `select_all_micropublications` | replace | Replace with SQLAlchemy session query. |

File: `propstore/core/justifications.py`.

| Helper/surface | Classification | Required final owner/action |
| --- | --- | --- |
| active-graph-derived justification view | move | Keep as explicitly named semantic view over typed graph/justification models. |
| justification row dictionaries | delete | Replace with typed `Justification` model or explicit view payloads. |
| duplicated `CanonicalJustification` schema/conversion role | delete | Authored documents and typed `Justification` model own justification shape. |
| generic `from_mapping` constructors | delete | Use boundary-specific constructors for document/JSON boundaries. |

Generic SQL/helper deletion predicate for this slice:

- delete helpers whose body is table-shaped `SELECT`, `INSERT`, row
  attachment, row coercion, projection-model wrapping, or projection-row
  population with no Propstore semantic policy;
- keep and move semantic code that owns authored justification documents,
  authored micropublication documents, micropublication evidence/context
  semantics, missing-claim quarantine diagnostics, active-graph justification
  views, or ASPIC/world justification projection behavior;
- after moving kept semantics, delete the original helper-shaped production
  path.

## Caller And Update Surfaces

Update every caller that imports or consumes micropublication projection rows,
active micropublication mapping coercion, justification row dictionaries, or
duplicated canonical justification conversion:

- `propstore/core/justifications.py`;
- `propstore/core/analyzers.py`;
- `propstore/aspic_bridge/extract.py`;
- `propstore/aspic_bridge/translate.py`;
- `propstore/world/model.py`;
- `propstore/worldline/argumentation.py`.

Required caller final state:

- `propstore/core/justifications.py` exposes a semantic justification view over
  typed model data and does not duplicate canonical schema/conversion;
- analyzer code consumes typed justification and micropublication data or
  owner-layer views;
- ASPIC bridge code consumes typed justification/micropublication owner APIs
  for the fields this slice deletes from projection rows;
- world and worldline callers no longer import micropublication projection
  rows, active micropublication mapping coercion, justification row
  dictionaries, or generic `from_mapping` constructors.

The later WorldQuery/graph/reasoning workstream still owns the full conversion
of raw sidecar world access to Quire read-only sessions.

## Semantic Moves

Preserve these behaviors as Propstore micropublication and justification owner
code:

- authored `JustificationDocument`;
- authored `MicropublicationDocument`;
- micropublication evidence/context semantics;
- missing-claim quarantine diagnostics;
- active-graph-derived justification view, named as a view;
- ASPIC/world justification projection behavior.

Target owners:

- micropublication owner receives authored micropublication validation,
  evidence/context semantics, missing-claim quarantine diagnostics, typed
  `Micropublication` construction, and `MicropublicationClaimLink`
  construction;
- justification owner receives authored justification validation and typed
  `Justification` construction;
- graph/argumentation owner receives the active-graph-derived justification
  view over typed models;
- ASPIC/world owner receives projection behavior over typed justification and
  micropublication owner APIs.

Generic string parsing, null conversion, JSON conversion, table creation,
population, selection, row dictionaries, row-carrier behavior, and generic
mapping constructors move to Quire charter/session/catalog machinery or are
deleted.

## Execution Loop

1. Read the micropublication and justification inventory entries and current
   family/core files.
2. List all current production callers from the caller/update surface above.
3. Name `Justification`, `Micropublication`, `MicropublicationClaimLink`, and
   the association-object decision in the implementation notes or commit
   message.
4. Delete the old micropublication projection/read-model surface first.
5. Delete duplicated justification schema/conversion paths immediately after
   the old micropublication surface deletion; preserve semantic requirements in
   the target owner notes above, not by keeping the duplicate production path.
6. Run the smallest import/type/test command that exposes the next failures.
7. Repair those failures by implementing the typed `Justification` model and
   named semantic view.
8. Fix only failures caused by this slice's deletion and named caller list.
9. Replace raw SQLite access with Quire SQLAlchemy session/model access.
10. Replace loose dict/list/row payloads with typed justification,
   micropublication, and association objects.
11. Delete field-specific string tuple, JSON, id, mapping, and row coercers
    once generic charter conversion covers the field.
12. Run the family gates.
13. Run the old-path search gates.
14. Run the data-parity gate.

No Propstore workaround is allowed for a missing Quire generic feature. A
missing SQLAlchemy charter, association object, JSON, enum, relationship,
catalog, reference/FK, or session capability returns the work to the Quire
owner workstream.

## Data-Parity Gate

```powershell
uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --before reports/sqlalchemy-charter-parity/micropublications-justifications/before.sqlite --build-after sqlalchemy-charter --after reports/sqlalchemy-charter-parity/micropublications-justifications/after.sqlite --owner micropublications-justifications --workstream workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/10-micropublications-justifications.md --out reports/sqlalchemy-charter-parity/micropublications-justifications.json
```

Compare the captured projection baseline against the charter-generated sidecar
for this slice and compare:

- row counts for micropublication, micropublication claim link, and
  justification tables;
- primary-key/key-set coverage for every micropublication and justification
  table this slice owns;
- micropublication lookup results and all-micropublication query results;
- micropublication-to-claim link role, ordinal, evidence/context binding, and
  link metadata;
- missing-claim quarantine diagnostics;
- active-graph-derived justification view output;
- analyzer justification inputs and outputs;
- ASPIC extraction and translation inputs for justification-owned fields;
- world/worldline justification query and argumentation results that depend on
  micropublication or justification data.

The phase fails when a row, key, diagnostic, semantic query result,
micropublication link, justification view result, analyzer result, ASPIC input,
or worldline argumentation result disappears.

Accepted parity difference allowlist:

- deleted projection rows, row carriers, row dictionaries, mapping coercers,
  duplicated canonical conversion role, table helpers, and generic helper paths
  named in this file's deletion targets;
- final deletion of `_nullable_text`, `_claim_id`, `TEXT_CODEC`,
  `CLAIM_ID_CODEC`, `JUSTIFICATION_STORAGE_MODEL`, `JUSTIFICATION_TABLE`, and
  `propstore/families/claims/projection_model.py`;
- no column rename, table rename, row disappearance, key disappearance,
  diagnostic disappearance, semantic-query disappearance, micropublication-link
  disappearance, justification-view disappearance, analyzer-result
  disappearance, ASPIC-input disappearance, or worldline-argumentation
  disappearance is allowed.

## Required Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label micropub-justification-charter tests/test_world_query.py tests/test_graph_export.py
rg -n -F -- "MicropublicationProjectionRow" propstore tests
rg -n -F -- "MicropublicationClaimProjectionRow" propstore tests
rg -n -F -- "MicropublicationSidecarRows" propstore tests
rg -n -F -- "ActiveMicropublication" propstore tests
rg -n -F -- "ActiveMicropublicationInput" propstore tests
rg -n -F -- "MICROPUBLICATION_PROJECTION" propstore tests
rg -n -F -- "MICROPUBLICATION_CLAIM_PROJECTION" propstore tests
rg -n -F -- "MICROPUBLICATION_ROW_MODEL" propstore tests
rg -n -F -- "JUSTIFICATION_STORAGE_MODEL" propstore tests
rg -n -F -- "propstore.families.claims.projection_model" propstore tests
rg -n -F -- "ActiveMicropublication.from_mapping" propstore tests
rg -n -F -- "coerce_active_micropublication" propstore tests
rg -n -F -- "_parse_string_tuple" propstore tests
rg -n -F -- "compile_micropublication_sidecar_rows" propstore tests
rg -n -F -- "compile_micropublication_sidecar_rows_with_diagnostics" propstore tests
rg -n -F -- "create_micropublication_tables" propstore tests
rg -n -F -- "populate_micropublications" propstore tests
rg -n -F -- "select_all_micropublications" propstore tests
rg -n -F -- "CanonicalJustification(" propstore tests
rg -n -F -- "from_mapping" propstore/core/justifications.py tests
```

All searches are zero-hit gates outside notes, workstreams, docs, and reports.

## Completion Criteria

This slice is complete only when:

- the micropublication/justification charter declares `Justification`,
  `Micropublication`, and `MicropublicationClaimLink`;
- `MicropublicationClaimLink` is the persistence owner for
  micropublication-to-claim link metadata;
- `ActiveMicropublication`, `ActiveMicropublicationInput`, and
  `coerce_active_micropublication` are absent from production code and tests;
- ATMS and world code consume typed `Micropublication` and
  `MicropublicationClaimLink` objects;
- micropublication and justification population writes typed model objects
  through a Quire SQLAlchemy session;
- micropublication lookup, justification views, analyzer inputs, ASPIC
  projection, world queries, and worldline argumentation use typed
  model/session APIs or named owner-layer views;
- authored `JustificationDocument`, authored `MicropublicationDocument`,
  evidence/context semantics, missing-claim quarantine diagnostics, and
  active-graph justification view behavior have final Propstore owners;
- every named caller/update surface no longer imports micropublication
  projection rows, row carriers, active mapping coercers, justification row
  dictionaries, duplicated canonical conversion, or generic `from_mapping`
  constructors;
- the data parity gate passes;
- all required tests pass through the logged pytest wrapper;
- all old-path search gates above are zero-hit outside notes, workstreams,
  docs, and reports.
