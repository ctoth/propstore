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

- direct `ProjectionSchema` creation;
- direct `PROPSTORE_WORLD_PROJECTION_SCHEMA` creation;
- build-plan row-set abstractions whose only purpose is projection insertion;
- raw `sqlite3.Connection` sidecar population orchestration;
- build orchestration imports of Quire projection primitives;
- manual world schema assembly in `propstore/families/projection_catalog.py`.

Deleting `propstore/families/projection_catalog.py` in this phase may leave
per-family `ProjectionTable` and `ProjectionModel` constants defined inside
family modules until their family slices delete them. That temporary state is
permitted only when no production code imports those constants after the
catalog deletion.

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
11. `scripts/compare_sqlalchemy_charter_parity.py` exists before source,
    forms, concepts, claims, relations, contexts, micropublications, rules,
    embeddings, or world-query cutovers start.
12. The parity harness compares table names, primary-key/key sets, row counts,
    FTS hit sets, vector hit sets, diagnostics, and the exact semantic query
    result keys supplied by each child workstream.
13. The parity harness exits nonzero and writes an actionable report when any
    required comparison fails.
14. The parity harness supports `--require-vector <name>` and
    `--require-behavior <name>` flags; when supplied, the report must contain a
    passing comparison block for every required vector or behavior name.
15. `tests/test_sqlalchemy_charter_parity_harness.py` proves one passing
    comparison and one failing comparison for owner slug `harness-self-test`.

## Data-Parity Gate

Build both sidecars from the same repository snapshot:

```powershell
uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --build-before projection --before reports/sqlalchemy-charter-parity/build-orchestration/before.sqlite --build-after sqlalchemy-charter --after reports/sqlalchemy-charter-parity/build-orchestration/after.sqlite --owner build-orchestration --out reports/sqlalchemy-charter-parity/build-orchestration.json
```

1. Build the current mainline sidecar.
2. Build the charter-generated sidecar.
3. Compare table names.
4. Compare primary keys.
5. Compare row counts.
6. Compare key sets.
7. Compare build diagnostics emitted by the build path.
8. Compare catalog/schema hash inputs and recorded schema identity.
9. Record explicit column rename allowances in the phase commit message or
   workstream report.
10. Fail on any dropped table, dropped key, missing diagnostic, missing FTS
    hit, missing vector hit, or missing semantic query result. The only
    accepted drop is a table already named as a deletion target in this
    workstream.

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
rg -n -F -- "ProjectionSchema" propstore tests
rg -n -F -- "ProjectionTable" propstore/derived_build.py propstore/derived_build_plan.py propstore/families/projection_catalog.py tests
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
- The data-parity gate passes from the same repository snapshot.
- The type gate, logged pytest gate, and old-path search gates pass.
- Propstore remains pinned to a pushed Quire reference, never a local checkout.
