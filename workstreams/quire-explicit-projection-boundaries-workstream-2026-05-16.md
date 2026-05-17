# Quire Explicit Projection Boundaries Workstream - 2026-05-16

Status: draft, executable after Phase 0 is complete.

Parent workstream:

- `workstreams/generic-quire-projection-mapping-workstream-2026-05-16.md`

This workstream exists because Phase 7 of the parent workstream is blocked.
The attempted relation-edge deletion proved that moving a handwritten table
literal into another Propstore projection model is not cleanup. It changed
schema-hash material, regressed scanner metrics, and preserved the real problem:
loose joined rows whose source tables, aliases, discriminators, attached child
rows, and render-only fields are not declared as first-class boundaries.

The target is Quire-owned typed projection plans:

- physical storage tables;
- typed row views over one or more physical tables;
- typed join plans;
- typed attached-child plans;
- typed render/output views;
- typed metadata components;
- one declaration graph for field and column identity.

Claims are not special. `ClaimRow` is the largest current forcing example.
`relation_edge` is the polymorphic-table forcing example.

## Verified Current State

Read-only verification performed before this workstream was written:

- `CompositePath`
  - Quire definitions/tests:
    - `C:/Users/Q/code/quire/quire/projection_mapping.py`
    - `C:/Users/Q/code/quire/tests/test_projection_mapping.py`
  - Propstore production uses:
    - `propstore/families/claims/projection_model.py`
    - logical IDs: `primary_logical_id`, `logical_ids_json`;
    - provenance: `source_paper`, `provenance_page`, `provenance_json`.
  - Verdict: load-bearing until Quire has a declared multi-column component
    boundary.

- `DerivedPath`
  - Quire definitions/tests:
    - `C:/Users/Q/code/quire/quire/projection_mapping.py`
    - `C:/Users/Q/code/quire/tests/test_projection_mapping.py`
  - Propstore production uses:
    - `propstore/families/claims/projection_model.py`
    - `propstore/families/concepts/projection_model.py`
  - Current purpose:
    - render-only `logical_id`;
    - render-only `logical_ids`.
  - Verdict: load-bearing until Quire has a declared render/output view.

- `attribute_bucket`
  - Quire definitions/tests:
    - `C:/Users/Q/code/quire/quire/projection_mapping.py`
    - `C:/Users/Q/code/quire/tests/test_projection_mapping.py`
  - Propstore production uses:
    - `propstore/families/relations/projection_model.py`
    - `propstore/families/claims/projection_model.py`
    - `propstore/families/concepts/projection_model.py`
  - Downstream relation uses include:
    - `propstore/world/queries.py`
    - `propstore/relation_analysis.py`
    - `propstore/core/graph_build.py`
    - `propstore/aspic_bridge/extract.py`
  - Verdict: load-bearing. For relations, fields currently stored in
    `StanceRow.attributes` are semantically typed stance metadata and must be
    declared as typed fields or a typed metadata component.

- `ignored_columns`
  - Quire definitions/tests:
    - `C:/Users/Q/code/quire/quire/projection_mapping.py`
    - `C:/Users/Q/code/quire/tests/test_projection_mapping.py`
  - Propstore production use:
    - `propstore/families/claims/projection_model.py`
  - Current purpose:
    - suppress joined source columns while decoding `ClaimRow`.
  - Verdict: load-bearing only because the claim/source joined-row boundary is
    implicit. Must be deleted by declaring the joined source component.

- `RepeatedPath.decode_key`
  - Quire definitions/tests:
    - `C:/Users/Q/code/quire/quire/projection_mapping.py`
    - `C:/Users/Q/code/quire/tests/test_projection_mapping.py`
  - Propstore production use:
    - `propstore/families/claims/projection_model.py`
  - Current purpose:
    - `select_claim_rows()` attaches `claim_concept_link` rows under
      `concept_links`.
  - Verdict: load-bearing until Quire has an attached-child boundary whose
    attachment key is declared, not smuggled through `RepeatedPath`.

- `decode_columns`
  - Quire definitions/tests:
    - `C:/Users/Q/code/quire/quire/projection_mapping.py`
    - `C:/Users/Q/code/quire/tests/test_projection_mapping.py`
  - Propstore production use:
    - `propstore/families/claims/projection_model.py`
  - Current purpose:
    - joined/select alias tolerance for `artifact_id`, `claim_type`,
      `logical_id`, and `logical_ids`.
  - Verdict: conceptually an alias boundary. It should not gain a parallel
    `aliases` field. Replace in place with a typed alias reference model.

## Design Constraints

1. Deletion-first:
   - Delete an old production surface before adding a same-shaped spelling.
   - Use type/search/test failures as the work queue.
   - Do not preserve old and new paths in parallel.

2. No duplicate field-name strings:
   - A physical column name is owned by one declaration.
   - A semantic field name is owned by one declaration.
   - Views, joins, child attachments, and render outputs reference declarations,
     not raw strings, except inside the owner declaration.

3. No second Propstore DSL:
   - Quire owns the generic declaration graph and projection mechanics.
   - Propstore owns semantic declarations and semantic metadata meaning.
   - Propstore must not invent local generic wrappers around Quire.

4. Physical table identity remains physical:
   - Do not rename `ProjectionTable` to `BaseProjectionTable`.
   - `ProjectionTable` already owns durable DDL.
   - New view/query abstractions reference `ProjectionTable`; they do not replace
     it.

5. Query-plan honesty:
   - Join SQL and FTS source plans are real query-plan surfaces.
   - A mapping slice cannot claim query-plan cleanup unless it declares and
     deletes the query-plan surface.

6. Typed boundaries beat catchalls:
   - Unknown joined columns must not be silently ignored.
   - Unknown decoded columns must not be dumped into `attributes` unless the
     target type declares a typed metadata component.

## Target Quire Abstractions

Names are no longer provisional after the Phase 1 reread pass. Quire already
owns the physical projection layer. Do not add duplicate definition objects for
things Quire already has.

Existing Quire owners that must be reused:

- `ProjectionField`: reusable typed storage-role descriptor.
- `ProjectionColumn`: concrete physical column identity, DDL policy, codec
  hooks, and schema-hash material.
- `ProjectionTable`: durable table identity, columns, FKs, indexes, row
  factories, DDL, inserts, selects, and row decoding.
- `ProjectionForeignKey` and `ProjectionIndex`: physical table constraints.
- `FtsProjection`: FTS table identity, source population SQL, search-column
  validation, DDL, and schema-hash material.
- `VecProjection`: vector table identity, dynamic table naming, rowid
  insert/delete/search SQL, DDL, and schema-hash material.
- `ProjectionSchema` and `ProjectionRuntimeCatalog`: projection collection,
  validation, DDL emission, runtime catalog, and schema-hash material.
- `ProjectionBuildStep` and `order_projection_steps`: derived-store build-step
  dependency ordering.

Do not introduce:

- `ProjectionColumnDef`;
- `ProjectionFieldDef`;
- a second column/field descriptor layer inside `projection_mapping.py`;
- Propstore-local equivalents of any of the existing Quire projection
  primitives.

### `ProjectionBinding`

Declares a mapping between a semantic path and an existing physical projection
primitive:

- semantic path;
- `ProjectionField` reference when the binding is to a reusable field role;
- `ProjectionColumn` reference when the binding is to a concrete column;
- field-level codec only when it is not already represented by the existing
  field or column codec;
- read alias, if the query result uses an alias;
- missing policy.

This replaces free `decode_columns`. It must not duplicate SQL type,
nullability, insertability, default SQL, check SQL, or physical codec facts that
already live on `ProjectionField` or `ProjectionColumn`.

### `ProjectionComponent`

Declares a typed multi-column component:

- component semantic path;
- ordered child bindings;
- encoder/decoder;
- all source columns referenced through `ProjectionBinding`.

This replaces `CompositePath` only after all production uses can be expressed by
components. Initial required components:

- claim logical IDs;
- claim provenance.

### `ProjectionRenderView`

Declares output-only fields:

- source bindings or component references;
- output semantic keys;
- renderer/codec;
- omission policy.

This replaces `DerivedPath`.

Initial required render outputs:

- claim `logical_id`;
- claim `logical_ids`;
- concept `logical_id`;
- concept `logical_ids`.

### `ProjectionAttachedRows`

Declares child-row attachment:

- parent view/table;
- child table;
- parent key binding;
- child row type/model;
- attachment field reference;
- child ordering.

This replaces `RepeatedPath.decode_key` and the manual
`row_dict["concept_links"] = ...` attachment shape.

Initial required attachment:

- `ClaimRow.concept_links` from `claim_concept_link`.

### `ProjectionJoin`

Declares a typed join edge:

- left table reference;
- left column reference;
- right table reference;
- right column reference;
- join kind;
- component/view target.

This replaces implicit joined source spillover and begins the deletion of
`ignored_columns`.

Initial required joins:

- claim core to numeric payload;
- claim core to text payload;
- claim core to algorithm payload;
- claim core to source.

### `ProjectionQueryPlan`

Declares a typed row-producing query:

- base table;
- joins;
- selected bindings/components;
- discriminators;
- attached rows;
- target type;
- ordering;
- optional externally supplied predicates.

This is the true owner of `claim_select_sql()` and relation stance select-column
lists.

### `ProjectionDiscriminator`

Declares structured discriminator constants:

- column reference;
- literal value;
- codec;
- where predicate generation;
- write-time insertion.

Initial required discriminators:

- `relation_edge.source_kind = "claim"`;
- `relation_edge.target_kind = "claim"`;
- `relation_edge.source_kind = "concept"`;
- `relation_edge.target_kind = "concept"`.

### Typed Metadata Component

A named metadata component is allowed only when the metadata shape is declared:

- component name;
- allowed fields;
- field codecs;
- target dataclass or mapping type;
- schema-hash material.

This replaces untyped `attribute_bucket`.

Initial required metadata:

- stance metadata currently read from `StanceRow.attributes`;
- claim runtime/status metadata currently read from `ClaimRow.attributes`;
- concept/parameterization extras only if still proven load-bearing after
  queries are explicit.

## Phase 0: Complete Inventory And Baselines

Status: complete.

Goal: prove the exact deletion set before implementation.

Read-only commands:

```powershell
git status --short
rg -n -F "CompositePath" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
rg -n -F "DerivedPath" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
rg -n -F "attribute_bucket" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
rg -n -F "ignored_columns" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
rg -n -F "decode_key" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
rg -n -F "decode_columns=" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
rg -n "claim_select_sql|STANCE_SELECT_COLUMNS|LEFT JOIN|row_dict\[\"concept_links\"\]" propstore tests
uv run scripts/render_sidecar_ddl_baseline.py --output workstreams/explicit-boundaries-ddl-baseline-2026-05-16.json
uv run scripts/typed_metadata_inventory.py --format json --emit-row-mapping-metrics > workstreams/explicit-boundaries-metrics-baseline-2026-05-16.json
```

Required result:

- inventory table in this workstream updated with every production use;
- each use mapped to one target Quire abstraction;
- no "candidate" language remains;
- all unresolved uses are marked blocked with the exact missing abstraction.

Do not continue to Phase 1 until this phase is complete.

### Phase 0 Inventory

Baseline artifacts:

- `workstreams/explicit-boundaries-ddl-baseline-2026-05-16.json`
- `workstreams/explicit-boundaries-metrics-baseline-2026-05-16.json`

Baseline summary metrics:

- `row_class_from_mapping_loc`: 78
- `row_class_to_dict_loc`: 78
- `row_decoder_helper_count`: 1
- `attributes_bucket_classes`: 6
- `child_row_assembly_loops`: 3
- `cross_table_select_sql`: 7
- `multi_source_merge_methods`: 10
- `nested_document_from_mapping_methods`: 4
- `projection_declarations_count`: 79
- `row_factory_targets`: 3

| Old surface | Verified production use | Target Quire abstraction | Blocker before deletion |
| --- | --- | --- | --- |
| `ScalarPath.decode_columns` | `propstore/families/claims/projection_model.py`: `artifact_id` reads joined `id`; `claim_type` reads `claim_type`; logical ID component reads `logical_id` and `logical_ids`. | `ProjectionBinding` read alias that references a declared field and declared column. | Phase 1 must make field/column definitions referenceable; Phase 2 deletes `decode_columns`. |
| `CompositePath` | `propstore/families/claims/projection_model.py`: claim logical IDs from `primary_logical_id` and `logical_ids_json`; claim provenance from `source_paper`, `provenance_page`, and `provenance_json`. | `ProjectionComponent` with ordered child bindings and typed encoder/decoder. | Phase 1 definitions and Phase 2 aliases must exist; Phase 3 deletes `CompositePath`. |
| `DerivedPath` | `propstore/families/claims/projection_model.py`: render `logical_id` and `logical_ids`; `propstore/families/concepts/projection_model.py`: render `logical_id` and `logical_ids`. | `ProjectionRenderView` output-only fields referencing declared source fields. | Phase 3 components must exist for logical IDs; Phase 4 deletes `DerivedPath`. |
| `RepeatedPath.decode_key` | `propstore/families/claims/projection_model.py`: `CLAIM_CONCEPT_LINKS_PATH` attaches selected `claim_concept_link` rows under `concept_links`; `propstore/families/claims/declaration.py` manually writes `row_dict["concept_links"]`. | `ProjectionAttachedRows` with parent key, child model, attachment field, and ordering. | Phase 4 render views must land; Phase 5 deletes `decode_key` and the manual attachment loop. |
| `ProjectionModel.attribute_bucket` | `propstore/families/relations/projection_model.py`: `RelationshipRow`, `StanceRow`, `ConflictRow`; `propstore/families/concepts/projection_model.py`: `ConceptRow`, `ParameterizationRow`; `propstore/families/claims/projection_model.py`: `ClaimRow`. | Typed metadata component, or declared typed fields where metadata is semantically fixed. | Phase 5 attached rows must land; Phase 6 deletes untyped `attribute_bucket`. |
| Relation stance metadata in `attributes` | `propstore/world/queries.py`, `propstore/relation_analysis.py`, `propstore/core/graph_build.py`, and `propstore/aspic_bridge/extract.py` read stance metadata now carried by `StanceRow.attributes`. | Typed metadata component or typed stance fields for `strength`, `conditions_differ`, `note`, `resolution_method`, `resolution_model`, `embedding_model`, `embedding_distance`, `pass_number`, `confidence`, `opinion_belief`, `opinion_disbelief`, `opinion_uncertainty`, and `opinion_base_rate`. | Phase 6 must define the allowed metadata shape and update readers to typed access. |
| `ProjectionModel.ignored_columns` | `propstore/families/claims/projection_model.py`: ignores joined source columns `source`, `source_slug`, `source_id`, `source_kind`, `source_origin_type`, `source_origin_value`, `source_origin_retrieved`, `source_origin_content_ref`, `source_prior_base_rate`, `source_quality_json`, `source_quality_opinion`, and `source_derived_from_json`. | `ProjectionJoin` plus `ProjectionQueryPlan` with explicit claim/source joined component. | Phase 6 typed metadata must land; Phase 7 deletes `ignored_columns`. |
| `claim_select_sql()` and claim `LEFT JOIN` SQL | `propstore/families/claims/declaration.py`: `claim_select_sql()`, payload/source joins, query call sites, and claim-link query SQL. Tests contain matching expected SQL. | `ProjectionQueryPlan` with declared payload joins, source join, selected bindings, attached rows, ordering, and predicates. | Phase 7 must make the claim joined-row boundary explicit and preserve DDL/query behavior. |
| Relation select-column constants | `propstore/families/relations/declaration.py`: `STANCE_SELECT_COLUMNS`, `STANCE_SELECT_COLUMNS_WITH_PERSPECTIVE`, select SQL call sites. | `ProjectionQueryPlan` plus view-level field bindings for stance rows. | Phase 8 must delete handwritten select-column lists. |
| Relation-edge polymorphic physical/view split | `propstore/families/relations/declaration.py`: relation edge physical table supports concept relationships and claim stances with different semantic row types. | `ProjectionDiscriminator` and view-level codecs over one physical `ProjectionTable`. | Phase 8 must declare source/target kind discriminators and preserve relation-edge DDL byte equality. |
| Remaining Propstore handwritten declaration sites | Baseline scanner reports `projection_declarations_count = 79` and `row_factory_targets = 3`. | Quire declaration graph and query plan outputs sourced from the same definitions as row mapping. | Parent Phase 7 reentry remains blocked until this workstream deletes the explicit old surfaces above. |

### Quire Reread Findings

Phase 1 reread covered the Quire package surface before implementation:

- `quire/projections.py` already owns physical projection primitives:
  `ProjectionField`, `ProjectionColumn`, `ProjectionTable`,
  `ProjectionForeignKey`, `ProjectionIndex`, `FtsProjection`, `VecProjection`,
  `ProjectionSchema`, and `ProjectionRuntimeCatalog`.
- `quire/projection_mapping.py` owns the newer row mapping path layer:
  `ProjectionCodec`, `ScalarPath`, `JsonPath`, `EnumPath`, `ReferencePath`,
  `CompositePath`, `RepeatedPath`, `DerivedPath`, and `ProjectionModel`.
- `quire/derived_store.py` owns materialization, cache keys, build-step
  topological ordering, and derived-store file lifecycle.
- `quire/derived_runtime.py` owns SQLite connection policy and schema
  validation for derived stores.
- `quire/sqlite_vec_store.py` owns generic vector-status and vector-table
  primitives over `ProjectionTable` and `VecProjection`.

Therefore Phase 1 must not add a new column/field definition layer. The missing
abstraction is not physical identity; it is the binding/query/view layer that
connects semantic paths and typed row views to existing physical projection
owners.

## Phase 1: Quire Declaration Graph

Status: ready after Phase 0 and Quire reread.

Owned repo:

- `C:/Users/Q/code/quire`

Delete first:

- any Phase 1 wording, tests, or implementation that introduces
  `ProjectionColumnDef`, `ProjectionFieldDef`, or another duplicate field/column
  descriptor;
- any test that treats a query alias as an ad hoc alternate string rather than
  as a read-name on a binding to an existing `ProjectionField`/`ProjectionColumn`
  owner.

Implement:

- `ProjectionBinding` as the missing semantic-path to physical-projection
  boundary;
- binding support for existing `ProjectionField` and `ProjectionColumn`;
- schema-hash material for binding references without duplicating physical
  column facts;
- validation that a binding references exactly one existing physical owner;
- tests proving `ProjectionField` and `ProjectionColumn` remain the only
  physical field/column definition owners.

Hard gates:

```powershell
uv run pytest tests/test_projection_mapping.py
uv run pytest tests/test_derived_store.py
uv run pyright quire
rg -n -F "cast(" quire/projection_mapping.py
rg -n "ProjectionColumnDef|ProjectionFieldDef" quire tests
```

Required result:

- no casts in `quire/projection_mapping.py`;
- zero `ProjectionColumnDef` or `ProjectionFieldDef` references;
- no duplicate physical column/field definition layer;
- existing `ProjectionModel` tests still pass.

Commit and push Quire. Pin Propstore to the pushed SHA. Reread this workstream
after the pin commit.

## Phase 2: Alias Boundary, Replacing `decode_columns`

Status: blocked until Phase 1 lands.

Delete first:

- `ScalarPath.decode_columns`.

Then implement:

- alias/read-name support through `ProjectionBinding`;
- Quire tests proving aliases reference declared fields/columns;
- Propstore updates for claim `artifact_id`, `claim_type`, `logical_id`, and
  `logical_ids`.

Old-path search:

```powershell
rg -n -F "decode_columns" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label explicit-boundaries-aliases tests/test_claim_roundtrip_fixtures.py tests/test_build_sidecar.py tests/test_source_claims.py
uv run scripts/typed_metadata_inventory.py --diff workstreams/explicit-boundaries-metrics-baseline-2026-05-16.json --metric row_class_from_mapping_loc --metric row_class_to_dict_loc
```

Required result:

- zero `decode_columns` references;
- no Propstore local alias helper;
- no schema DDL drift.

## Phase 3: Multi-Column Components, Replacing `CompositePath`

Status: blocked until Phase 2 lands.

Delete first:

- Quire `CompositePath`;
- Propstore imports of `CompositePath`.

Then implement:

- `ProjectionComponent`;
- claim logical-ID component;
- claim provenance component;
- tests for component encode/decode and schema hash.

Old-path search:

```powershell
rg -n -F "CompositePath" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label explicit-boundaries-components tests/test_claim_roundtrip_fixtures.py tests/test_build_sidecar.py tests/test_world_query.py
```

Required result:

- zero `CompositePath` references;
- logical IDs and provenance still round-trip;
- no local claim helper reintroduces multi-column mapping outside declarations.

## Phase 4: Render Views, Replacing `DerivedPath`

Status: blocked until Phase 3 lands.

Delete first:

- Quire `DerivedPath`;
- Propstore imports of `DerivedPath`.

Then implement:

- `ProjectionRenderView`;
- claim logical render fields;
- concept logical render fields;
- explicit render tests.

Old-path search:

```powershell
rg -n -F "DerivedPath" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label explicit-boundaries-render tests/test_claim_roundtrip_fixtures.py tests/test_concept_views.py tests/test_cli.py
```

Required result:

- zero `DerivedPath` references;
- render-only fields are not present in physical table column lists;
- `logical_id` and `logical_ids` outputs remain present where callers expect
  them.

## Phase 5: Attached Child Rows, Replacing `RepeatedPath.decode_key`

Status: blocked until Phase 4 lands.

Delete first:

- `RepeatedPath.decode_key`;
- claim-side dependence on attaching child rows under a table-name mismatch.

Then implement:

- `ProjectionAttachedRows`;
- claim concept-link attachment;
- typed child ordering and parent key binding.

Old-path search:

```powershell
rg -n -F "decode_key" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
rg -n -F "row_dict[\"concept_links\"]" propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label explicit-boundaries-attached-rows tests/test_claim_roundtrip_fixtures.py tests/test_build_sidecar.py tests/test_graph_build.py
```

Required result:

- zero `decode_key` references;
- claim concept links still decode as typed `ClaimConceptLinkRow`;
- no manual child-row attachment loop remains in claim query code.

## Phase 6: Typed Metadata Components, Replacing `attribute_bucket`

Status: blocked until Phase 5 lands.

Delete first:

- `ProjectionModel.attribute_bucket`.

Then implement:

- typed metadata components in Quire;
- relation stance metadata component or typed fields;
- claim runtime/status metadata component or typed fields;
- concept/parameterization metadata components only if still verified
  load-bearing after earlier phases.

Known relation metadata currently read through `StanceRow.attributes`:

- `strength`;
- `conditions_differ`;
- `note`;
- `resolution_method`;
- `resolution_model`;
- `embedding_model`;
- `embedding_distance`;
- `pass_number`;
- `confidence`;
- `opinion_belief`;
- `opinion_disbelief`;
- `opinion_uncertainty`;
- `opinion_base_rate`.

Old-path search:

```powershell
rg -n -F "attribute_bucket" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
rg -n "stance\.attributes|claim\.attributes|concept\.attributes|attributes\.get\(" propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label explicit-boundaries-metadata tests/test_world_query.py tests/test_relation_analysis.py tests/test_graph_build.py tests/test_build_sidecar.py
```

Required result:

- zero `attribute_bucket` references;
- downstream stance/claim/concept metadata reads are typed;
- no unknown-column catchall remains in projection decoding.

## Phase 7: Joined Claim Query Boundary, Replacing `ignored_columns`

Status: blocked until Phase 6 lands.

Delete first:

- `ProjectionModel.ignored_columns`;
- claim ignored source-column list.

Then implement:

- `ProjectionJoin`;
- `ProjectionQueryPlan` for `ClaimRow`;
- explicit source join component;
- explicit payload joins;
- source-local/canonical boundary validation.

Old-path search:

```powershell
rg -n -F "ignored_columns" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
rg -n -F "claim_select_sql" propstore tests
rg -n -F "LEFT JOIN source AS src" propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label explicit-boundaries-claim-query tests/test_claim_roundtrip_fixtures.py tests/test_build_sidecar.py tests/test_source_claims.py tests/test_world_query.py
uv run scripts/render_sidecar_ddl_baseline.py --output .tmp/explicit-boundaries-ddl-after.json
```

Required result:

- zero `ignored_columns` references;
- claim/source/payload joins are declared, not hidden in `claim_select_sql()`;
- DDL byte-equals baseline;
- source-local-only fields do not leak into canonical identity.

## Phase 8: Relation-Edge Polymorphic View Boundary

Status: blocked until Phases 1, 2, 6, and 7 land.

Delete first:

- handwritten `RELATION_EDGE_PROJECTION`;
- `STANCE_SELECT_COLUMNS`;
- `STANCE_SELECT_COLUMNS_WITH_PERSPECTIVE`;
- `claim_stance_projection_row`;
- local stance/relationship select-column decode loops that hand-shape rows.

Then implement:

- `ProjectionDiscriminator`;
- `ProjectionQueryPlan` for claim stance rows;
- `ProjectionQueryPlan` for concept relationship rows;
- relation-edge physical table declaration sourced from shared column defs;
- relation-edge typed views referencing the same column/field declarations.

Important design decision:

- Keep `ProjectionTable`; do not rename it.
- The physical table has no single semantic row type.
- View-level codecs decode `relation_type` differently for concept
  relationships and claim stances.

Old-path search:

```powershell
rg -n "RELATION_EDGE_PROJECTION|STANCE_SELECT_COLUMNS|claim_stance_projection_row" propstore tests
rg -n "ProjectionTable\(|ProjectionForeignKey\(|ProjectionIndex\(" propstore/families/relations/declaration.py
```

Gate:

```powershell
uv run scripts/render_sidecar_ddl_baseline.py --output .tmp/relation-edge-after.json
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label explicit-boundaries-relation-edge tests/test_sidecar_relation_edge_projection.py tests/test_relate_opinions.py tests/test_graph_build.py tests/test_world_query.py
uv run scripts/typed_metadata_inventory.py --diff workstreams/explicit-boundaries-metrics-baseline-2026-05-16.json --metric projection_table_column_count --metric row_factory_targets --metric quire_projection_mapping_imports
```

Required result:

- relation-edge DDL byte-equals baseline;
- fewer handwritten declaration sites;
- no `row_factory_targets` regression;
- no local Propstore relation-row decoder helper appears.

## Phase 9: Parent Phase 7 Reentry

Status: blocked until Phase 8 lands.

Return to:

- `workstreams/generic-quire-projection-mapping-workstream-2026-05-16.md`
  Phase 7.

Run the parent Phase 7 gate exactly:

```powershell
uv run scripts/render_sidecar_ddl_baseline.py
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label quire-mapping-declarations tests/test_sidecar_projection_contract.py tests/test_build_sidecar.py tests/test_world_query.py
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric projection_table_column_count --metric row_factory_targets --metric quire_projection_mapping_imports
rg -n "ProjectionTable\(|ProjectionForeignKey\(|ProjectionIndex\(" propstore/families --glob "declaration.py"
```

Required result:

- parent Phase 7 can proceed without relation-edge blocker;
- this workstream remains the source of truth for explicit boundary deletion.

## Anti-Cheat Checks

This workstream fails if any of these happen:

- Quire gains aliases while `decode_columns` remains.
- Quire gains a new view layer while `CompositePath`, `DerivedPath`,
  `attribute_bucket`, `ignored_columns`, or `RepeatedPath.decode_key` remains
  without a later phase explicitly proving why it is still blocked.
- Propstore gains generic mapping helpers parallel to Quire.
- Raw field/column strings are repeated across view/query/render declarations
  instead of referenced through definition objects.
- `ProjectionTable` is renamed or wrapped just to call it a base table.
- Tests pass while old production mapping/query surfaces still coexist with the
  new boundary.
- DDL/schema hash drift is accepted without an explicit semantic-diff record.
- `attributes` remains an untyped dumping ground for unknown columns.
- Query SQL is renamed as a mapping surface instead of declared as a query plan.
- A slice ends with generated diagnostics committed merely because they changed.

## Reread And Commit Discipline

After every implementation commit:

1. Reread this workstream.
2. Reread the parent workstream.
3. Identify the next unchecked phase by name.
4. Run the relevant old-path searches before editing.
5. Commit only the current slice's owned paths.
6. Do not move to the next slice with tracked dirty files.

After every passing substantial targeted test run and after every passing full
suite:

1. Reread this workstream.
2. Rerun the scanner diff for the active metrics.
3. Continue with the next unchecked phase unless blocked.

## Final Gates

Run:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label explicit-boundaries-full
uv run scripts/render_sidecar_ddl_baseline.py --output .tmp/explicit-boundaries-final-ddl.json
uv run scripts/typed_metadata_inventory.py --diff workstreams/explicit-boundaries-metrics-baseline-2026-05-16.json --metric row_class_from_mapping_loc --metric row_class_to_dict_loc --metric coerce_row_helpers --metric row_decoder_helper_count --metric projection_table_column_count --metric row_factory_targets --metric quire_projection_mapping_imports
rg -n -F "decode_columns" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
rg -n -F "CompositePath" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
rg -n -F "DerivedPath" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
rg -n -F "attribute_bucket" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
rg -n -F "ignored_columns" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
rg -n -F "decode_key" C:/Users/Q/code/quire/quire C:/Users/Q/code/quire/tests propstore tests
```

Final required result:

- zero old-path references listed above;
- DDL byte-equals baseline unless a committed semantic diff says otherwise;
- Propstore projection LOC and old mapping metrics decrease;
- relation-edge declaration compression is unblocked and complete;
- no custom Propstore table/view/query DSL exists beside Quire.
