# Family Declaration Phase 2.4 Executable Workstream - 2026-05-17

Status: executable for the single current slice only.

Parent context:

- `workstreams/family-declaration-cleanup-workstream-2026-05-17.md`
- `workstreams/family-declaration-cleanup-inventory-2026-05-17.md`

## Goal

Delete claim-owned justification and conflict-witness storage/query helper
surfaces. Claims are not the owner of authored justifications or relation
conflict witnesses.

This workstream is intentionally small. Future family cleanup candidates remain
in the inventory file and are not part of this executable control surface.

## Current Baseline

Measured before implementation on 2026-05-17:

- `cloc .\propstore`: Python code `77548`.
- `uv run scripts/typed_metadata_inventory.py --format json --emit-row-mapping-metrics`:
  `raw_sql_score` `270`, `propstore_raw_sql_score` `274`,
  `cross_table_select_sql` `5`, `child_row_assembly_loops` `0`.
- Old claim-owned production hits:

```powershell
rg -n -F -e "select_authored_justifications" -e "count_authored_justifications" -e "_canonical_justification_from_row" -e "_decode_justification_premises" -e "_decode_justification_provenance" -e "compile_authored_justification_sidecar_rows" -e "compile_authored_justification_sidecar_rows_with_diagnostics" -e "populate_authored_justifications" -e "compile_conflict_sidecar_rows" -e "populate_conflicts" -e "JUSTIFICATION_STORAGE_MODEL" -e "JUSTIFICATION_TABLE" -e "CONFLICT_WITNESS_TABLE" propstore/families/claims propstore/derived_build.py propstore/derived_build_plan.py propstore/world/model.py propstore/families/projection_catalog.py propstore/families/relations --glob "*.py"
```

## Deletion-First Rule For This Slice

The first production edit must delete the old claim-owned surface. Do not add
`propstore/families/justifications`, relation compile helpers, replacement
query plans, wrappers, aliases, or moved copies before this deletion edit.

If the first production diff adds replacement code while these old claim-owned
names still exist, the diff is invalid.

## Exact First Deletions

Delete these from `propstore/families/claims/declaration.py`:

- `select_authored_justifications`
- `count_authored_justifications`
- `_canonical_justification_from_row`
- `_decode_justification_premises`
- `_decode_justification_provenance`
- `compile_authored_justification_sidecar_rows`
- `compile_authored_justification_sidecar_rows_with_diagnostics`
- `compile_conflict_sidecar_rows`
- `populate_authored_justifications`
- `populate_conflicts`
- imports used only by those names:
  `detect_conflicts`, `detect_transitive_conflicts`,
  `conflict_claims_from_claim_files`, `FamilyReferenceIndex`,
  `JustificationDocument`, `CONFLICT_WITNESS_TABLE`, `JUSTIFICATION_TABLE`,
  and `CanonicalJustification` / `ProvenanceRecord` type-checking imports if
  no longer used.

Delete these from `propstore/families/claims/projection_model.py`:

- `JUSTIFICATION_STORAGE_MODEL`
- `JUSTIFICATION_TABLE`
- `JUSTIFICATION_TABLE` membership in `CLAIM_STORAGE_TABLES`

Do not edit replacement owner modules in the same first deletion edit.

## Required Repair After Deletion

Use the resulting `pyright`, tests, and literal `rg` failures as the work queue.
The allowed owner repairs are semantic ownership repairs only:

- authored justification semantic lowering belongs under
  `propstore.families.justifications`;
- conflict witness semantic lowering belongs under `propstore.families.relations`;
- `derived_build_plan.py`, `derived_build.py`, `world/model.py`, and
  `families/projection_catalog.py` may import only from those owner modules for
  this slice;
- no claim-owned forwarding functions, aliases, re-exports, fallback readers,
  or compatibility shims.

Do not recreate the deleted claim-owned SQL/projection/read/populate boilerplate
under a new propstore family. Generic projection operations are owned by Quire:

- creating the projection table from a model;
- converting a model instance or mapping into a projection row;
- inserting projection rows into the model table;
- selecting rows through a `ProjectionQueryPlan`;
- counting rows for the model table;
- decoding selected rows through the model.

If the repair requires any of those operations and Quire does not expose the
needed primitive, implement the primitive in Quire first, then use it from
propstore. Propstore family modules may declare semantic projection models and
semantic lowering functions; they must not own generic SQLite execution helpers
whose only variable input is the model/table/query plan.

## Expected Reduction

The first deletion removes roughly 230 lines from claim declaration/storage
ownership and roughly 25 lines from claim projection-model ownership.

The kept slice must satisfy all of these:

- `propstore/families/claims/declaration.py` has no hits for the deleted
  helper names;
- `propstore/families/claims/projection_model.py` has no
  `JUSTIFICATION_STORAGE_MODEL` or `JUSTIFICATION_TABLE`;
- no new propstore family module contains a per-family copy of generic
  select-all, count-table, insert-rows, or query-plan execution helpers;
- `cloc .\propstore` Python code is not higher than `77548`;
- scanner `raw_sql_score` is below `270` or scanner `cross_table_select_sql`
  is below `5`;
- the final commit removes more claim-owned boilerplate than it adds as
  replacement owner code, and any generic replacement machinery lives in Quire.

If these cannot be met, the slice is not complete and must not be committed as
an implementation slice.

## Commands

Before production edits:

```powershell
git status --short --branch
rg -n -F -e "select_authored_justifications" -e "count_authored_justifications" -e "_canonical_justification_from_row" -e "_decode_justification_premises" -e "_decode_justification_provenance" -e "compile_authored_justification_sidecar_rows" -e "compile_authored_justification_sidecar_rows_with_diagnostics" -e "populate_authored_justifications" -e "compile_conflict_sidecar_rows" -e "populate_conflicts" -e "JUSTIFICATION_STORAGE_MODEL" -e "JUSTIFICATION_TABLE" -e "CONFLICT_WITNESS_TABLE" propstore/families/claims propstore/derived_build.py propstore/derived_build_plan.py propstore/world/model.py propstore/families/projection_catalog.py propstore/families/relations --glob "*.py"
```

After the deletion edit, run:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label family-2-4-delete-smoke tests/test_build_sidecar.py::TestClaimTable::test_proper_bounds_without_value
```

After repair, run:

```powershell
git diff --check -- propstore workstreams
rg -n -F -e "select_authored_justifications" -e "count_authored_justifications" -e "compile_authored_justification_sidecar_rows" -e "compile_conflict_sidecar_rows" -e "populate_authored_justifications" -e "populate_conflicts" propstore/families/claims propstore/derived_build.py propstore/derived_build_plan.py propstore/world/model.py
rg -n -F -e "JUSTIFICATION_STORAGE_MODEL" -e "JUSTIFICATION_TABLE" propstore/families/claims propstore/families/projection_catalog.py
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label family-claims-2-4 tests/test_claim_roundtrip_fixtures.py tests/test_claim_views.py tests/test_build_sidecar.py tests/test_world_query.py tests/test_source_claims.py tests/test_relate_opinions.py
uv run scripts/typed_metadata_inventory.py --format json --emit-row-mapping-metrics
cloc .\propstore
```

After every implementation commit and after every passing substantial targeted
test run, reread this file before selecting the next action.

## Completion

Complete means:

- the old claim-owned production names are gone;
- the schema still includes `justification` and `conflict_witness` through their
  true owner modules;
- behavior gates pass;
- the measured reduction gates above pass;
- the commit message names this workstream and the final old-path `rg` command.
