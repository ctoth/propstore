# 13 - Final Deletion Gates

Date: 2026-05-18

## Goal

Close the Quire SQLAlchemy charter cutover after all family and world-query
child workstreams have moved their consumers to Quire SQLAlchemy sessions and
typed Propstore models.

This file owns final verification, old-path search gates, dependency-pin
closure, inventory closure, and completion criteria. It does not authorize a
production cutover before the prerequisite child gates pass.

## Prerequisite Gate Dependencies

Check these before starting final deletion work:

| Dependency | Required evidence |
| --- | --- |
| `00-index.md` | Phase-order checker has passed for the split directory. |
| `inventory-matrix.md` | Every row has a delete, replace, move, or keep-as-semantic-owner closure entry. |
| `01-quire-capability-and-charter.md` | SQLAlchemy capability proof, charter/schema IR, Quire gates, and pushed Quire pin are complete. |
| `02-quire-sqlalchemy-engine.md` | SQLAlchemy table/mapping/session/catalog engine gates are complete. |
| `03-quire-fts-vector.md` | FTS/vector gates are complete and no Propstore workaround owns generic FTS/vector behavior. |
| `04-propstore-build-orchestration.md` | Build orchestration uses Quire writable sessions and charter catalogs. |
| `05-source-and-diagnostics.md` | Source and source-diagnostic old paths are deleted and parity passed. |
| `06-forms-concepts-parameterizations.md` | Form, concept, parameterization, FTS, and concept runtime old paths are deleted and parity passed. |
| `07-contexts-lifting.md` | Context/lifting projection paths are deleted and parity passed. |
| `08-claims-active-claims.md` | Claim projection/storage/active-claim row paths are deleted and parity passed. |
| `09-relations-stances-conflicts.md` | Relation, stance, and conflict row-model paths are deleted and parity passed. |
| `10-micropublications-justifications.md` | Micropub/justification projection paths are deleted and parity passed. |
| `11-rules-grounding-calibration-embeddings.md` | Support-family projection/vector duplicates are deleted and parity passed. |
| `12-world-query-graph-reasoning.md` | `WorldQuery`, graph, worldline, support-revision, and ASPIC callers use typed session/model APIs. |
| `helper-ledger.md` | Every ledger row has a closure entry or is covered by the owning child workstream's closure report. |

## Phase 15: Delete Quire Projection Modules

Repository: `C:\Users\Q\code\quire`.

### Deletion Checklist

- [ ] Confirm all Propstore and Quire consumers have moved away from Quire
  projection primitives.
- [ ] Delete `quire/projection_mapping.py`.
- [ ] Delete `quire/projections.py`.
- [ ] Delete public exports for projection classes from `quire/__init__.py`.
- [ ] Delete tests that only test deleted projection primitives.
- [ ] Confirm replacement coverage exists for charter IR, SQLAlchemy mapping,
  schema catalog, FTS/vector extension, and derived-store sessions.

### Quire Search Gates

Run from `C:\Users\Q\code\quire`:

```powershell
rg -n -F -- "ProjectionTable" quire tests
rg -n -F -- "ProjectionModel" quire tests
rg -n -F -- "ProjectionCodec" quire tests
rg -n -F -- "ScalarPath" quire tests
rg -n -F -- "ReferencePath" quire tests
rg -n -F -- "FtsProjection" quire tests
rg -n -F -- "VecProjection" quire tests
```

Gate: zero production hits. Documentation hits are limited to notes,
workstreams, docs, and reports.

## Phase 16: Delete Propstore Projection And Helper Leftovers

Repository: `C:\Users\Q\code\propstore`.

### Deletion Checklist

- [ ] Delete `propstore/families/claims/projection_model.py`.
- [ ] Delete `propstore/families/concepts/projection_model.py`.
- [ ] Delete `propstore/families/relations/projection_model.py`.
- [ ] Delete `propstore/families/projection_catalog.py`.
- [ ] Delete embedded projection declarations in family declaration modules.
- [ ] Delete row classes that duplicate domain models.
- [ ] Delete manual select/count/insert/decode/attached-row helpers that are
  generic DB plumbing.
- [ ] Delete manual field coercers now owned by the charter engine.
- [ ] Confirm remaining IO boundary constructors use names such as
  `from_yaml_payload`, `from_json_payload`, or `from_row_mapping`.
- [ ] Confirm `from_mapping` is absent from core, families, world, worldline,
  support-revision, and tests.

### Helper Deletion Predicate

- [ ] Delete helpers whose body is table-shaped `SELECT`, `COUNT`, `INSERT`,
  `DELETE`, row attachment, row coercion, or projection-model wrapping with no
  Propstore semantic policy.
- [ ] Preserve semantic behavior that owns concept-id precedence, alias
  resolution, source-local lowering, quarantine/blocked policy, form/unit
  validation, visibility/render policy, context/lifting semantics,
  argumentation semantics, revision semantics, or authored-document identity.
- [ ] After semantic behavior is moved to its owner, delete the original
  helper-shaped production path.

### Propstore Search Gates

Run from `C:\Users\Q\code\propstore`:

```powershell
rg -n -F -- "ProjectionTable" propstore tests
rg -n -F -- "ProjectionModel" propstore tests
rg -n -F -- "ProjectionCodec" propstore tests
rg -n -F -- "ProjectionRow" propstore tests
rg -n -F -- "ScalarPath" propstore tests
rg -n -F -- "ReferencePath" propstore tests
rg -n -F -- "FtsProjection" propstore tests
rg -n -F -- "VecProjection" propstore tests
rg -n -F -- "CLAIM_ROW_MODEL" propstore tests
rg -n -F -- "CONCEPT_ROW_MODEL" propstore tests
rg -n -F -- "STANCE_ROW_MODEL" propstore tests
rg -n -F -- "RELATIONSHIP_ROW_MODEL" propstore tests
rg -n -F -- "SOURCE_PROJECTION" propstore tests
rg -n -F -- "PROPSTORE_WORLD_PROJECTION_SCHEMA" propstore tests
rg -n -F -- "_optional_float_input" propstore tests
rg -n -F -- "_optional_string" propstore tests
rg -n -F -- "_optional_int" propstore tests
rg -n -F -- "_claim_optional_float" propstore tests
rg -n -F -- "_nullable_text" propstore tests
rg -n -F -- "_nullable_int" propstore tests
rg -n -F -- "_nullable_float" propstore tests
rg -n -F -- "_optional_numeric" propstore tests
rg -n -F -- "_optional_float" propstore tests
rg -n -F -- "_parse_string_tuple" propstore tests
rg -n -F -- "coerce_active_micropublication" propstore tests
rg -n -F -- "propstore.core.active_claims" propstore tests
rg -n -F -- "ActiveClaim" propstore tests
rg -n -F -- "ActiveClaimInput" propstore tests
rg -n -F -- "ActiveMicropublicationInput" propstore tests
rg -n -F -- "ActiveClaimVariable" propstore tests
rg -n -F -- "ActiveClaimResolver" propstore tests
rg -n -F -- "ActiveWorldGraph" propstore tests
rg -n -F -- "ActiveClaim(" propstore tests
rg -n -F -- "ActiveMicropublication" propstore tests
rg -n -F -- "from_mapping" propstore/core propstore/families propstore/world propstore/worldline propstore/support_revision tests
```

Gate: zero production hits. Documentation hits are limited to notes,
workstreams, docs, and reports.

## Phase 17: Full Gates And Dependency Pin

### Quire Full Gates

Run from `C:\Users\Q\code\quire`:

```powershell
uv run pyright
uv run pytest -vv
```

### Propstore Full Gates

Run from `C:\Users\Q\code\propstore`:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label sqlalchemy-charter-full
```

### Dependency Pin Checklist

- [ ] Push Quire first.
- [ ] Pin Propstore to the pushed Quire commit or tag.
- [ ] Update `uv.lock`.
- [ ] Inspect parsed `pyproject.toml` dependencies and `[tool.uv.sources]`.
- [ ] Confirm no Quire dependency entry resolves only from the local
  filesystem.

### Dependency Search Gates

Run from `C:\Users\Q\code\propstore`:

```powershell
rg -n -F -- "quire @ file" pyproject.toml uv.lock
rg -n -F -- "quire @ .." pyproject.toml uv.lock
rg -n -F -- "quire @ C:" pyproject.toml uv.lock
rg -n -F -- "[tool.uv.sources]" pyproject.toml
rg -n -F -- "path =" pyproject.toml
rg -n -F -- "workspace = true" pyproject.toml
```

Gate: no local path, workspace, or file URL Quire dependency.

## Completion Checklist

The cutover is complete only when every item is checked:

- [ ] Quire has a SQLAlchemy-backed charter/schema engine.
- [ ] Quire derived-store handles open read-only SQLAlchemy sessions.
- [ ] Quire schema catalogs describe the derived store from the same charters
  that generated the mappings.
- [ ] Quire charters compose with existing `ArtifactFamily`, document-store,
  placement, and reference/FK APIs.
- [ ] Quire projection modules and projection public exports are deleted.
- [ ] Propstore supplies domain charters for every sidecar family.
- [ ] `propstore/derived_build.py` and `propstore/derived_build_plan.py` use
  Quire writable sessions and charter catalogs.
- [ ] Propstore no longer imports Quire projection primitives.
- [ ] Propstore has no family `projection_model.py` files.
- [ ] Propstore has no duplicate `*Row` model layer for domain objects.
- [ ] `claim.concept_links` is the primary relationship.
- [ ] `ClaimConceptLink` owns role, ordinal, and binding metadata.
- [ ] Micropublication claim links, aliases, parameterizations, context
  lifting records, stances, and conflicts are typed models or association
  objects.
- [ ] Source-local and canonical states are explicit charter/lifecycle states.
- [ ] Manual helper/coercer families listed in the search gates are deleted.
- [ ] Remaining IO boundary constructors use boundary-specific names and do
  not use the generic `from_mapping` name.
- [ ] `WorldQuery` uses Quire sessions and typed model queries.
- [ ] Every row in `inventory-matrix.md` has a final delete, move, replace, or
  keep-as-semantic-owner outcome in a commit message or final closure report.
- [ ] Every family cutover has a passing data-parity gate for row counts, key
  sets, representative owner-layer queries, FTS, vector, and diagnostics where
  applicable.
- [ ] App/CLI/web surfaces call owner-layer APIs.
- [ ] Quire and Propstore full gates pass.
- [ ] Propstore is pinned to a pushed Quire commit or tag, never a local
  checkout.
