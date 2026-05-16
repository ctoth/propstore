# Generic Quire Projection Mapping Workstream

## Goal

Delete family-specific projection-row flattening boilerplate by making Quire own
generic projection mapping.

Claims are not privileged. `ClaimRow` is only the largest current example of a
general missing abstraction: typed nested/domain shapes are being manually
flattened into relational derived-store projections and manually rebuilt from
joined rows. That flattening pattern must become Quire-owned machinery and then
be applied across Propstore families.

The target state is:

- Quire owns projection mapping mechanics: path extraction, flattening,
  unflattening, enum coercion, JSON/text encoding, repeated child rows,
  reference/FK metadata, table generation, row decoding, and schema hashing.
- Propstore owns semantic declarations: what fields mean, what paths are
  projected, which references exist, and which query/search behavior is
  domain-specific.
- No Propstore family has a bespoke row class whose main job is to translate
  between nested semantic fields and flat derived-store columns.

## Non-Goals

- Do not special-case claims.
- Do not create a Propstore-local mapper DSL that Quire should own.
- Do not replace `ClaimRow` with `ClaimProjectionRow`, `ClaimMapper`, or another
  claim-shaped wrapper.
- Do not hide SQL strings or flattening callbacks behind prettier names while
  retaining the same handwritten per-family mapping decisions.
- Do not collapse authored artifact identity, source-local shape, runtime report
  shape, and derived-store projection shape into one confused object.

## Current Problem

Manual projection mapping exists because durable documents and runtime domain
objects are nested, typed, and semantic, while the derived store is relational,
indexed, and query-oriented.

Current examples:

- `propstore/families/claims/declaration.py`
  - `ClaimRow.from_mapping` manually rebuilds a typed row from flat/joined
    storage columns.
  - `ClaimRow.to_dict` manually flattens nested source, provenance, logical IDs,
    values, and context into storage/query keys.
  - `ClaimConceptLinkRow.from_mapping` repeats simple row decoding mechanics.
- `propstore/families/concepts/declaration.py`
  - `ConceptRow.from_mapping` and `ParameterizationRow.from_mapping` repeat
    known-field filtering, enum coercion, string coercion, and attribute-bucket
    behavior.
- `propstore/families/relations/declaration.py`
  - `RelationshipRow`, `StanceRow`, and `ConflictRow` repeat row decode/render
    patterns.
- projection declarations across `propstore/families/*/declaration.py`
  - table columns, row factories, FK edges, indexes, and row decode behavior are
    still too handwritten even after field descriptors moved to Quire.

The generic problem is not claim-shaped. It is:

```text
nested semantic path <-> one or more projection columns
nested/repeated semantic path <-> child projection table rows
typed reference path <-> family reference column and FK edge
enum/domain value <-> storage scalar
structured value <-> JSON/text column
flat storage row <-> typed row/domain view
```

## Target API

The first Quire implementation target is explicit enough to execute. Add a new
module:

- `../quire/quire/projection_mapping.py`
- `../quire/tests/test_projection_mapping.py`

Minimum public names:

```python
ProjectionCodec
ScalarPath
JsonPath
EnumPath
ReferencePath
RepeatedPath
ProjectionModel
```

Minimum callable behavior:

```python
model.to_row(source: object) -> Mapping[str, object]
model.from_row(row: Mapping[str, object]) -> object
model.child_rows(source: object) -> tuple[ProjectionRow, ...]
model.projection_tables() -> tuple[ProjectionTable, ...]
model.schema_hash_material() -> Mapping[str, object]
```

`ProjectionTable.row_factory` remains a Quire projection-table hook, but
Propstore row factories for this workstream must point at
`ProjectionModel.from_row` or a named Quire-generated decoder. Lambdas, local
closures, and Propstore-local `_decode_*_row` helpers fail the workstream.

Required path declarations:

- `ScalarPath(path=("source", "origin", "type"), column="source_origin_type")`
- `JsonPath(path=("logical_ids",), column="logical_ids_json")`
- `EnumPath(path=("type",), column="type", enum=...)`
- `ReferencePath(path=("context", "id"), family="context", column="context_id")`
- `RepeatedPath(path=("concept_links",), table="claim_concept_link", ...)`

Quire must provide:

- path extraction from typed structs/dataclasses/mappings;
- path assignment or row construction into typed result objects;
- enum coercion by declared enum type;
- JSON/text scalar encoding and decoding;
- optional missing-path behavior with declared policy;
- repeated child-row expansion and decoding;
- family-reference column and FK derivation when a reference family is declared;
- table/index/FK generation from one mapping declaration;
- generated row decoder usable as `ProjectionTable.row_factory`;
- stable schema-hash material including mapping paths and codecs;
- explicit unknown-key policy: default is hard failure, attribute buckets exist
  only when declared by name.

Quire must not provide:

- claim-only callbacks;
- hidden multi-source merge logic;
- "accept anything" unknown-key buckets;
- a row-factory type that allows arbitrary Propstore closures to masquerade as
  generated mapping.

Propstore must provide:

- semantic owner declarations and field meaning;
- path names and field roles;
- source-local versus canonical visibility decisions;
- domain-specific validation and reasoning;
- domain-specific query behavior that is not generic storage mapping.

## Design Judgment: Necessary Versus Bad Complexity

Necessary complexity:

- Quire needs a real typed projection mapping kernel because the system has
  multiple legitimate representations: authored artifacts, source-local state,
  runtime/domain objects, and query-index rows.
- Derived indexes need relational columns, child tables, FKs, indexes, schema
  hashes, FTS source plans, and eventually vector/search plans. Those are real
  storage concerns, not accidental complexity.
- Propstore must keep semantic declarations because Quire cannot know what a
  concept, stance, context, source, micropublication, or claim means.
- Some SQL remains necessary until there is a Quire-owned query-plan layer.
  Join shape and FTS population are not automatically solved by row mapping.

Bad design to delete:

- Family-specific row classes that mostly flatten/unflatten fields.
- `from_mapping` and `to_dict` bodies that repeat path lookup, enum coercion,
  JSON parsing/rendering, unknown-key filtering, or attribute-bucket handling.
- `coerce_*_row`, `_decode_*_row`, `_load_*_row`, `build_*_row`, and
  `make_*_row` helper families whose only job is row decoding.
- Repeated field declarations where the same column, path, type, FK, and schema
  hash fact are manually spelled in more than one place.
- Attribute buckets that silently bless unknown shape instead of being declared
  as a deliberate typed metadata surface.
- Claim-shaped logic being treated as architecture. Claims are one family using
  the same projection machinery as relations, concepts, contexts, sources, and
  micropublications.

The beautiful abstraction is a single semantic projection declaration per
family-owned projected object. That declaration is the source for:

- row encode/decode;
- child-row encode/decode;
- projection table columns;
- FK/reference metadata;
- index/search metadata when it is generic;
- schema-hash material;
- unknown-key policy;
- typed result construction.

If an implementation adds a second declaration or moves row decoding into a new
Propstore helper, it has failed the design even if tests pass.

### Explicit Non-Mapping Surfaces

The following are not solved by the first projection-mapping kernel and may not
be quietly relabeled as completed mapping work:

- `claim_select_sql()` and other hand-written cross-table join query plans.
- Claim nested-source versus flat-source reconciliation. If a nested `source`
  mapping and flat `source_*` columns both exist, that is a multi-source merge
  surface, not a simple path mapping.
- FTS source SQL and generated FTS population plans.
- Runtime/wire report rendering.

These surfaces must be inventoried and reported, but they do not block the
first simple-row deletion slices.

## Hard Rules

1. Deletion-first:
   - For each slice, delete the old handwritten production mapping surface first.
   - Use type, test, and search failures as the work queue.
   - Do not add wrappers, aliases, bridges, fallbacks, or old/new dual paths.

2. Quire-first:
   - If generic mapping mechanics are missing, implement them in Quire first.
   - Push Quire before pinning Propstore.
   - Never pin Propstore to a local Quire path or local repository URL.

3. Claims are not special:
   - Any Quire API introduced for `ClaimRow` must be demonstrated on at least one
     non-claim row family before the claim slice is considered complete.
   - Quire tests must include one nested-path model and one repeated-child model
     that are not claim models.
   - A claim-only abstraction fails this workstream.

4. No semantic collapse:
   - Authored artifact schemas, source-local authoring schemas, runtime reports,
     and derived-store projection rows remain distinct owner categories.
   - Generic mapping may connect them only through explicit typed declarations.

5. Reread discipline:
   - Reread this workstream after every implementation commit.
   - Reread the active inventory or scanner output after every passing
     substantial targeted test run and after every passing full-suite run.

6. No renamed boilerplate:
   - Functions named like `_decode_*_row`, `_load_*_row`, `build_*_row`, or
     `make_*_row` in Propstore family modules count as row-mapping boilerplate.
   - A slice only completes when the measured Propstore mapping LOC decreases.
   - If mapping logic moves into another Propstore file, the slice is reverted.

7. Query-plan honesty:
   - Cross-table select SQL is measured separately.
   - A row-mapping slice cannot claim completion of query-plan cleanup.
   - If the old row decoder depends on a hand-shaped joined row, the joined-row
     query remains a named unfinished surface until a Quire query-plan
     workstream handles it.

## Phase 0a: Scanner Capability

Status: pending.

Extend `scripts/typed_metadata_inventory.py` before any baseline command depends
on new flags.

Required new CLI:

```powershell
uv run scripts/typed_metadata_inventory.py --format json --emit-row-mapping-metrics
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric row_class_from_mapping_loc
```

The scanner must report:

- handwritten row classes in `propstore/families/*/declaration.py`;
- `from_mapping`, `to_dict`, and `coerce_*_row` methods by file/class;
- LOC for each row class `from_mapping` body;
- LOC for each row class `to_dict` body;
- projection tables with `row_factory`;
- row-factory target names, with lambdas/local functions called out;
- projection tables without generated row decoders;
- repeated flat-column path families such as `source_*`, `provenance_*`,
  `logical_ids_json`, `conditions_*`, `*_id`, `opinion_*`;
- row classes with `attributes: Mapping[str, Any]`;
- every key that can currently land in each `attributes` dict, measured from
  static writers and available fixture/branch data;
- manual child-row assembly loops;
- cross-table select SQL and `JOIN` SQL in production Python;
- multi-source merge methods that mention nested mappings and flat columns in
  the same body;
- nested-document codec methods such as `ClaimSource.from_mapping`,
  `SourceTrust.from_mapping`, `ProvenanceRecord.from_mapping`, and
  `ActiveMicropublication.from_mapping`;
- explicit constructor-based nested decode sites such as `SourceOrigin(...)` and
  `LogicalId(...)` inside row decoders;
- `quire.projection_mapping` imports by file;
- Propstore-local row decoder helper names matching
  `coerce_*_row`, `_decode_*_row`, `_load_*_row`, `build_*_row`, or
  `make_*_row`;
- handwritten `ProjectionTable`, `ProjectionForeignKey`, and `ProjectionIndex`
  declarations still present after the prior field-descriptor workstream.

Inventory must cover at least:

- `propstore/families/calibration/declaration.py`
- `propstore/families/claims/declaration.py`
- `propstore/families/concepts/declaration.py`
- `propstore/families/contexts/declaration.py`
- `propstore/families/diagnostics/declaration.py`
- `propstore/families/micropublications/declaration.py`
- `propstore/families/relations/declaration.py`
- `propstore/families/rules/declaration.py`
- `propstore/families/sources/declaration.py`

Required JSON summary metric names:

- `row_class_from_mapping_loc`
- `row_class_to_dict_loc`
- `coerce_row_helpers`
- `row_decoder_helper_count`
- `attributes_bucket_classes`
- `flat_source_column_refs`
- `nested_source_dict_refs`
- `cross_table_select_sql`
- `projection_table_column_count`
- `row_factory_targets`
- `child_row_assembly_loops`
- `multi_source_merge_methods`
- `nested_document_from_mapping_methods`
- `nested_constructor_decode_sites`
- `quire_projection_mapping_imports`
- `projection_declarations_count`
- `ddl_hash`
- `fts_ddl_hash`
- `fts_population_sql_hash`

Gate:

```powershell
uv run scripts/typed_metadata_inventory.py --format json --emit-row-mapping-metrics
uv run scripts/typed_metadata_inventory.py --diff workstreams/nonexistent.json --metric row_class_from_mapping_loc
uv run pyright propstore
```

`--diff` may fail because the baseline file is missing, but it must fail with a
clear missing-file diagnostic after proving the option exists. Commit this
scanner slice before Phase 0b.

## Phase 0b: Baseline Emission

Status: pending.

Run only after Phase 0a is committed and this workstream has been reread.

Baseline commands:

```powershell
uv run scripts/typed_metadata_inventory.py --format markdown --limit 120
uv run scripts/typed_metadata_inventory.py --format json --emit-row-mapping-metrics > workstreams/quire-projection-mapping-baseline-2026-05-16.json
uv run scripts/render_sidecar_ddl_baseline.py --output workstreams/quire-projection-mapping-ddl-baseline-2026-05-16.json
Get-FileHash workstreams/quire-projection-mapping-ddl-baseline-2026-05-16.json -Algorithm SHA256 | Format-List > workstreams/quire-projection-mapping-ddl-hash-2026-05-16.txt
rg -n "class .*Row|from_mapping|to_dict|coerce_.*_row|ProjectionTable\\(|ProjectionForeignKey\\(|ProjectionIndex\\(" propstore/families --glob "declaration.py"
rg -n "source_[a-z_]+|provenance_[a-z_]+|logical_ids_json|conditions_cel|conditions_ir|opinion_[a-z_]+" propstore/families --glob "declaration.py"
rg -n "LEFT JOIN|\\bJOIN\\b" propstore --glob "*.py"
rg -n "from_mapping\\(.*\\bsource\\b" propstore --glob "*.py"
rg -nP "isinstance\\([^,]+,\\s*Mapping\\)" propstore/families --glob "declaration.py"
```

If FTS DDL or FTS population SQL is not represented in
`workstreams/quire-projection-mapping-ddl-baseline-2026-05-16.json`, record that
as a Phase 8 blocker instead of inventing an unverified hash file.

Gate:

- Commit a JSON baseline artifact under `workstreams/` with the metrics above.
- Commit the DDL hash file, or commit a blocker note naming the missing DDL
  output path.
- Verify the scanner diff command can compare the committed baseline against
  the current tree for at least these metrics:
  `row_class_from_mapping_loc`, `row_class_to_dict_loc`,
  `coerce_row_helpers`, `row_decoder_helper_count`,
  `attributes_bucket_classes`, `child_row_assembly_loops`,
  `multi_source_merge_methods`, and
  `nested_document_from_mapping_methods`.
- No Quire or Propstore production code edit may start until the baseline
  exists.

## Phase 0c: Nested Codec Ownership Decision

Status: pending.

Before writing Quire mapping code, decide and commit one answer:

1. Quire codecs absorb nested-document decode/encode mechanics such as
   `ClaimSource.from_mapping`, `SourceTrust.from_mapping`,
   `ProvenanceRecord.from_mapping`, and `ActiveMicropublication.from_mapping`;
   or
2. domain nested types own their own parse/render, and the workstream treats
   them as semantic domain codecs rather than projection-row mapping.

The decision must name which current methods are in scope for deletion and which
are not. Without this decision, Phase 6 is blocked because deleting
`ClaimRow.from_mapping` could leave a hidden second codec layer underneath it.

## Phase 1: Quire Projection Mapping Kernel

Status: pending.

Owner repo: `../quire`.

Deliverables:

- add `quire/projection_mapping.py`;
- add `tests/test_projection_mapping.py`;
- implement `ProjectionCodec`, `ScalarPath`, `JsonPath`, `EnumPath`,
  `ReferencePath`, `RepeatedPath`, and `ProjectionModel`;
- support mapping from typed object or mapping to projection row values;
- support mapping from flat row mapping plus child rows to typed result object;
- support declared unknown-key and attribute-bucket behavior;
- support generated row decoder usable as `ProjectionTable.row_factory`;
- support schema-hash material that includes mapping path declarations and
  codec names.

Required Quire tests:

- `test_scalar_path_round_trip_flat_dataclass`
- `test_scalar_path_round_trip_nested_dataclass`
- `test_enum_path_coerces_in_both_directions`
- `test_json_path_round_trips_lists_and_dicts`
- `test_optional_missing_path_returns_none_by_default`
- `test_repeated_path_expands_into_child_rows_with_parent_keys`
- `test_repeated_path_decodes_children_into_typed_tuple`
- `test_reference_path_emits_column_and_foreign_key`
- `test_unknown_keys_raise_when_no_attribute_bucket_declared`
- `test_attribute_bucket_only_when_declared`
- `test_schema_hash_changes_when_path_changes_but_column_does_not`
- `test_schema_hash_unchanged_when_only_field_order_differs`
- `test_two_unrelated_models_share_zero_model_specific_code`
- `test_relationship_shaped_fixture_uses_generic_projection_model`

Hard failure conditions:

- any Quire test fixture is claim-shaped;
- the relationship-shaped fixture cannot round-trip the same scalar, enum,
  reference, and optional fields currently used by Propstore relation rows;
- generated row decoders are arbitrary closures instead of inspectable mapping
  products;
- unknown keys are accepted without a named attribute bucket;
- repeated children can encode but cannot decode;
- schema-hash material omits path, codec, reference family, optional policy, or
  repeated-child table metadata.

Gate:

```powershell
cd ..\quire
uv run pytest tests/test_derived_store.py tests/test_projection_mapping.py
uv run pyright quire
git status --short -- quire tests pyproject.toml uv.lock
```

Then push Quire and record the pushed commit SHA.

## Phase 2: Propstore Pin And Workstream Reset

Status: pending.

Pin Propstore to the pushed Quire commit. Do not use a local path pin.

Propstore projection model placement:

- each converted family owns projection declarations in
  `propstore/families/<family>/projection_model.py`;
- each projected row shape has exactly one exported `ProjectionModel`;
- family `declaration.py` imports those models and attaches them to projection
  tables, indexes, and row factories;
- after a family slice lands, `ScalarPath(`, `JsonPath(`, `EnumPath(`,
  `ReferencePath(`, and `RepeatedPath(` constructors may appear only in that
  family's `projection_model.py` and tests.

Before editing production code:

```powershell
git status --short --branch
uv run scripts/typed_metadata_inventory.py --format json --emit-row-mapping-metrics
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric row_class_from_mapping_loc --metric row_class_to_dict_loc --metric coerce_row_helpers --metric row_decoder_helper_count --metric attributes_bucket_classes --metric child_row_assembly_loops --metric multi_source_merge_methods
```

Gate:

- working tree has no tracked dirty files except the intentional dependency pin;
- Quire dependency resolves from a pushed remote commit or tag;
- baseline metrics can be re-read after the pin;
- this workstream is reread after the pin commit.

## Phase 3: Slice A, Relations Row Decoders

Status: pending.

Owned files:

- `propstore/families/relations/declaration.py`
- tests directly updated for the deleted relation helper API, if any.

Delete first:

- `RelationshipRow.from_mapping`
- `RelationshipRow.to_dict`
- `StanceRow.from_mapping`
- `StanceRow.to_dict`
- `ConflictRow.from_mapping`
- `ConflictRow.to_dict`
- `coerce_relationship_row`
- `coerce_stance_row`
- `coerce_conflict_row`
- relation `select_*` decoder loops shaped like
  `[RelationshipRow.from_mapping(dict(row)) for row in rows]`;
- stance/conflict `select_*` decoder loops shaped like
  `[StanceRow.from_mapping(dict(row)) for row in rows]` or
  `[ConflictRow.from_mapping(dict(row)) for row in rows]`.

Then use compiler, type, and search failures to update callers to the
Quire-generated decoder/model path.

Preserve in Propstore:

- relationship semantic validation;
- stance/opinion meaning;
- conflict diagnostics;
- graph/reasoning behavior.

Old-path searches:

```powershell
rg -n "RelationshipRow\\.from_mapping|StanceRow\\.from_mapping|ConflictRow\\.from_mapping" propstore tests
rg -n "RelationshipRow\\.to_dict|StanceRow\\.to_dict|ConflictRow\\.to_dict" propstore tests
rg -n "coerce_relationship_row|coerce_stance_row|coerce_conflict_row" propstore tests
rg -n "RelationshipRow\\.from_mapping\\(dict\\(row\\)\\)|StanceRow\\.from_mapping\\(dict\\(row\\)\\)|ConflictRow\\.from_mapping\\(dict\\(row\\)\\)" propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label quire-mapping-relations tests/test_sidecar_relation_edge_projection.py tests/test_relate_opinions.py tests/test_graph_build.py
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric row_class_from_mapping_loc --metric row_class_to_dict_loc --metric coerce_row_helpers --metric row_decoder_helper_count --metric multi_source_merge_methods
```

Required result:

- relation helper names have zero production references;
- relation row mapping LOC decreases from baseline;
- no new Propstore-local decode helper appears;
- `multi_source_merge_methods` does not increase.

If caller volume is larger than expected, keep this slice open and update every
caller. Do not leave compatibility helpers behind.

## Phase 4: Slice B, Concepts And Parameterizations

Status: pending.

Owned files:

- `propstore/families/concepts/declaration.py`
- tests directly updated for deleted concept helper APIs, if any.

Delete first:

- `ConceptRow.from_mapping`
- `ConceptRow.to_dict`
- `ParameterizationRow.from_mapping`
- `ParameterizationRow.to_dict`
- `coerce_concept_row`
- `coerce_parameterization_row`

Then rebuild through a single Quire projection declaration.

Required behavior to preserve:

- `ConceptStatus` coercion through `EnumPath`;
- `ConceptId` normalization through declared scalar codec or typed constructor;
- logical ID parsing/rendering through declared JSON/derived render fields;
- `logical_id` compatibility key only if it is declared as a derived field in
  the projection model;
- explicit attribute bucket only if the concept declaration names one;
- byte-equivalent concept and parameterization projection DDL.

Old-path searches:

```powershell
rg -n "ConceptRow\\.from_mapping|ConceptRow\\.to_dict|ParameterizationRow\\.from_mapping|ParameterizationRow\\.to_dict" propstore tests
rg -n "coerce_concept_row|coerce_parameterization_row" propstore tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label quire-mapping-concepts tests/test_sidecar_concept_projection.py tests/test_sidecar_parameterization_projection.py tests/test_graph_build.py tests/test_world_query.py
uv run scripts/render_sidecar_ddl_baseline.py
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric row_class_from_mapping_loc --metric row_class_to_dict_loc --metric coerce_row_helpers --metric attributes_bucket_classes --metric projection_table_column_count
```

Required result:

- concept helper names have zero production references;
- concept row mapping LOC decreases from baseline;
- no Propstore postprocessor exists for `logical_id`;
- DDL byte-equivalence holds unless a deliberate semantic diff is committed and
  explained.

## Phase 5: Slice C, Repeated Child Rows

Status: pending.

Owned files:

- `propstore/families/claims/declaration.py`
- claim tests directly updated for deleted child-row helper APIs, if any.

Delete first:

- `ClaimConceptLinkRow.from_mapping`
- `ClaimConceptLinkRow.to_dict`

Then use `RepeatedPath` child-table machinery from Quire. This slice is about
the generic repeated-child mechanism, not about claim semantics.

`RepeatedPath` must declare the child fetch plan. For current claim concept
links that means a parent-keyed child table fetch, not an implicit joined-row
decode:

```python
RepeatedPath(
    path=("concept_links",),
    table="claim_concept_link",
    fetch="parent_keyed_select",
    parent_fk="claim_id",
)
```

If Quire only supports joined child rows, Phase 5 is blocked until Quire supports
parent-keyed child fetches.

Old-path searches:

```powershell
rg -n "ClaimConceptLinkRow\\.from_mapping|ClaimConceptLinkRow\\.to_dict" propstore tests
rg -n "select_claim_concept_links_by_claim_id|concept_links|claim_concept_link" propstore/families/claims propstore/sidecar tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label quire-mapping-child-rows tests/test_claim_roundtrip_fixtures.py tests/test_build_sidecar.py tests/test_world_query.py
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric row_class_from_mapping_loc --metric row_class_to_dict_loc --metric child_row_assembly_loops --metric projection_table_column_count
```

Required result:

- `ClaimConceptLinkRow` handwritten mapping is gone;
- child row assembly uses Quire repeated-child declarations;
- no Propstore-local child-row fetcher or decoder is introduced.

If Quire cannot decode repeated children back into typed tuples, return to
Phase 1 and finish that capability. Do not solve it in Propstore.

## Phase 6: Slice D, Claim Generic Fields

Status: pending.

Open only after Phases 3 and 5 pass. Claims are not the proving ground.

Owned files:

- `propstore/families/claims/declaration.py`
- tests directly updated for deleted claim row helper APIs, if any.

Delete first from `ClaimRow.from_mapping` and `ClaimRow.to_dict` only the parts
that are generic projection mapping:

- `logical_ids` <-> `primary_logical_id` and `logical_ids_json`;
- `provenance` <-> `provenance_page`, `source_paper`, `provenance_json`;
- enum fields such as `type`, `algorithm_stage`, and `source_kind`;
- scalar projection paths for context, values, units, bounds, confidence, and
  status fields.

Do not claim these are solved in this slice:

- `claim_select_sql()`;
- joined-row shape;
- nested `source` mapping plus flat `source_*` reconciliation;
- `source.origin.*` and `source.trust.*` flat-column mapping until the
  nested/flat source reconciliation strategy is decided;
- FTS source SQL;
- runtime/wire report rendering;
- source-local authoring normalization.

Source field strategy:

- If Phase 0c chooses Quire-owned nested codecs and a typed assignment-selection
  merge, then delete the dual-source body before mapping `source_*` columns.
- If Phase 0c leaves nested source parsing in Propstore, freeze `source_*` as a
  named non-mapping surface for a later source-reconciliation slice.
- Do not map `source_*` columns into a Quire model while leaving the old
  nested/flat merge in place underneath it.

Old-path searches:

```powershell
rg -n "ClaimRow\\.from_mapping|ClaimRow\\.to_dict|coerce_claim_row" propstore tests
rg -n "source_origin_|source_trust_|source_quality_json|source_derived_from_json|provenance_json|logical_ids_json" propstore/families/claims propstore/sidecar tests
rg -n "claim_select_sql|select_claim_rows|LEFT JOIN|\\bJOIN\\b" propstore/families/claims propstore/sidecar tests
```

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label quire-mapping-claim-generic tests/test_claim_roundtrip_fixtures.py tests/test_build_sidecar.py tests/test_world_query.py tests/test_relate_opinions.py tests/test_source_claims.py
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric row_class_from_mapping_loc --metric row_class_to_dict_loc --metric flat_source_column_refs --metric nested_source_dict_refs --metric multi_source_merge_methods --metric cross_table_select_sql
```

Required result:

- `ClaimRow.from_mapping` LOC drops by at least 60 percent from the Phase 0
  baseline, or the remaining body is line-item classified as non-generic;
- if the LOC drop is under 30 percent, the slice fails and must be redesigned;
- no claim-only Quire API is added;
- cross-table SQL and multi-source merge metrics are reported honestly as
  remaining surfaces if still present.

## Phase 7: Slice E, Projection Declaration Compression

Status: pending.

Only after Quire mapping specs can generate row decoders and table metadata.

Order:

1. relations;
2. contexts;
3. concepts;
4. micropublications;
5. claims only after the prior families pass.

Delete first:

- handwritten `ProjectionTable` column lists that can be derived from a
  projection model;
- handwritten `ProjectionForeignKey` declarations that duplicate
  `ReferencePath`;
- handwritten `ProjectionIndex` declarations that duplicate declared indexed
  paths.

Keep in Propstore:

- semantic declaration ownership;
- FTS query semantics until Phase 8;
- custom lifecycle code;
- domain validation;
- import ordering and family initialization meaning.

Gate:

```powershell
uv run scripts/render_sidecar_ddl_baseline.py
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label quire-mapping-declarations tests/test_sidecar_projection_contract.py tests/test_build_sidecar.py tests/test_world_query.py
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric projection_table_column_count --metric row_factory_targets --metric quire_projection_mapping_imports
rg -n "ProjectionTable\\(|ProjectionForeignKey\\(|ProjectionIndex\\(" propstore/families --glob "declaration.py"
```

Required result:

- fewer handwritten projection declaration sites;
- no second Propstore projection declaration DSL;
- DDL/FTS/vector output byte-equals baseline unless an intentional semantic diff
  is explicitly recorded;
- every compressed declaration is sourced from the same single projection model
  used for row mapping.

## Phase 8: FTS And Query-Plan Workstream

Status: blocked until row mapping and declaration compression land.

FTS source SQL and cross-table query plans are real remaining complexity. They
are not solved by row mapping alone and must not be hidden inside helper
functions.

Open a separate executable workstream for:

- Quire-owned structured FTS source plans;
- generated FTS population SQL;
- typed search-column validation;
- query-plan declarations for common joins;
- byte-equivalent FTS DDL and population behavior;
- measured deletion of hand-written `claim_select_sql()` and similar query-plan
  surfaces.

## Anti-Cheat Checks

The workstream is not complete if any of these happen:

- deleted row mapping reappears as `_decode_*_row`, `_load_*_row`,
  `build_*_row`, `make_*_row`, a lambda row factory, or a local closure;
- Propstore gains a generic mapper DSL parallel to Quire;
- `ProjectionModel` is introduced beside `ProjectionTable` but table columns,
  FK metadata, row decoding, and schema hashing still need separate manual
  declarations;
- a converted family has `ScalarPath(`, `JsonPath(`, `EnumPath(`,
  `ReferencePath(`, or `RepeatedPath(` outside
  `propstore/families/<family>/projection_model.py` and tests;
- `attributes` buckets continue accepting unknown columns without a declared
  bucket name and type;
- `logical_id` or similar compatibility keys are rendered by postprocessing
  helpers instead of declared derived fields;
- claims receive an API that relations, concepts, contexts, or
  micropublications cannot use;
- generated code increases Propstore LOC while scanner metrics for old mapping
  surfaces fail to decrease;
- FTS or join SQL is renamed as a mapping surface instead of left as a named
  query-plan follow-up;
- tests pass while old production mapping paths still coexist with the Quire
  path.

## Reread And Commit Discipline

After every implementation commit:

1. Reread this workstream.
2. Identify the next unchecked phase or slice by name.
3. Run the relevant old-path searches before editing.
4. Commit only the current slice's owned paths.
5. Do not move to the next slice with tracked dirty files.

After every passing substantial targeted test run and after every passing full
suite:

1. Reread this workstream.
2. Rerun the scanner diff for the active metrics.
3. Continue with the next unchecked phase unless blocked.

## Final Gates

Run:

```powershell
uv run scripts/typed_metadata_inventory.py --format markdown --limit 80
uv run scripts/typed_metadata_inventory.py --format json --emit-row-mapping-metrics
uv run scripts/typed_metadata_inventory.py --diff workstreams/quire-projection-mapping-baseline-2026-05-16.json --metric row_class_from_mapping_loc --metric row_class_to_dict_loc --metric coerce_row_helpers --metric row_decoder_helper_count --metric attributes_bucket_classes --metric flat_source_column_refs --metric nested_source_dict_refs --metric cross_table_select_sql --metric projection_table_column_count --metric row_factory_targets --metric child_row_assembly_loops --metric multi_source_merge_methods --metric nested_document_from_mapping_methods --metric quire_projection_mapping_imports
uv run scripts/typed_metadata_inventory.py --gates --ledger workstreams/typed-metadata-owner-ledger-2026-05-15.csv
uv run scripts/render_sidecar_ddl_baseline.py --output workstreams/quire-projection-mapping-ddl-baseline-final.json
Get-FileHash workstreams/quire-projection-mapping-ddl-baseline-final.json -Algorithm SHA256
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label quire-projection-mapping-targeted tests/test_build_sidecar.py tests/test_world_query.py tests/test_sidecar_projection_contract.py tests/test_relate_opinions.py tests/test_graph_build.py
powershell -File scripts/run_logged_pytest.ps1 -Label quire-projection-mapping-full
```

Final report must include:

- baseline and final handwritten row mapping method counts;
- baseline and final `coerce_*_row` helper counts;
- baseline and final row decoder helper counts;
- baseline and final attribute bucket counts;
- baseline and final child-row assembly loop counts;
- baseline and final multi-source merge method counts;
- baseline and final nested-document codec method counts, with owner decision;
- baseline and final cross-table SQL counts;
- baseline and final handwritten `ProjectionTable`/FK/index declaration counts;
- baseline and final scanner-owned row mapping LOC;
- baseline and final family declaration LOC;
- baseline and final DDL hash, plus any explicitly blocked FTS/vector hash;
- list of remaining row mapping methods and why each is semantic rather than
  generic mapping;
- list of remaining `attributes` buckets and the declared key policy for each;
- Quire commit SHA used by Propstore.

Completion requires:

- Quire owns generic projection mapping mechanics;
- Propstore proves the mechanism on at least one non-claim family and then on
  claim mapping;
- no claim-only mapper or compatibility bridge remains;
- target metrics decrease;
- pyright, targeted tests, and full suite pass.
