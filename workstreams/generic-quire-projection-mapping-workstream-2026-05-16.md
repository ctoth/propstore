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

## Target Abstraction

Add Quire projection mapping declarations capable of expressing:

```text
ProjectionModel(
  name=...,
  source_type=...,
  row_type=...,
  tables=...,
  fields=[
    ScalarPath(path="source.origin.type", column="source_origin_type", codec=...),
    JsonPath(path="logical_ids", column="logical_ids_json", primary=...),
    ReferencePath(path="context.id", family="context", column="context_id"),
    RepeatedPath(path="concept_links", table="claim_concept_link", fields=...),
  ],
)
```

This sketch is not the API. It describes the capability boundary.

Quire must provide:

- path extraction from typed structs/dataclasses/mappings;
- path assignment/unflattening into typed result objects;
- enum coercion by declared type or codec;
- JSON/text scalar encoding and decoding;
- one-to-one, optional, and repeated child-row mapping;
- family-reference column and FK derivation;
- table/index/FK generation from one declaration;
- row decoder generation;
- stable schema-hash material;
- inventory metadata so consumers can gate handwritten mapping deletion.

Propstore must provide:

- semantic owner declarations and field meaning;
- path names and field roles;
- source-local versus canonical visibility decisions;
- domain-specific validation and reasoning;
- domain-specific query behavior that is not generic storage mapping.

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
   - A claim-only abstraction fails this workstream.

4. No semantic collapse:
   - Authored artifact schemas, source-local authoring schemas, runtime reports,
     and derived-store projection rows remain distinct owner categories.
   - Generic mapping may connect them only through explicit typed declarations.

5. Reread discipline:
   - Reread this workstream after every implementation commit.
   - Reread the active inventory or scanner output after every passing
     substantial targeted test run and after every passing full-suite run.

## Phase 0: Inventory And Baselines

Status: pending.

Create or extend a scanner that reports:

- handwritten row classes in `propstore/families/*/declaration.py`;
- `from_mapping`, `to_dict`, and `coerce_*_row` methods by file/class;
- projection tables with `row_factory`;
- projection tables without generated row decoders;
- repeated flat-column path families such as `source_*`, `provenance_*`,
  `logical_ids_json`, `conditions_*`, `*_id`, `opinion_*`;
- row classes with `attributes: Mapping[str, Any]`;
- manual child-row assembly loops;
- handwritten `ProjectionTable`, `ProjectionForeignKey`, and `ProjectionIndex`
  declarations still present after the prior field-descriptor workstream.

Baseline commands:

```powershell
uv run scripts/typed_metadata_inventory.py --format markdown --limit 80
uv run scripts/typed_metadata_inventory.py --format json
rg -n "class .*Row|from_mapping|to_dict|coerce_.*_row|ProjectionTable\\(|ProjectionForeignKey\\(|ProjectionIndex\\(" propstore/families --glob "declaration.py"
rg -n "source_[a-z_]+|provenance_[a-z_]+|logical_ids_json|conditions_cel|conditions_ir|opinion_[a-z_]+" propstore/families --glob "declaration.py"
```

Gate:

- Commit a JSON baseline artifact under `workstreams/` with the metrics above.
- No production code edit may start until the baseline exists.

## Phase 1: Quire Projection Mapping Kernel

Status: pending.

Owner repo: `../quire`.

Deliverables:

- typed projection path declarations;
- scalar, enum, JSON, optional, reference, and repeated-child mapping specs;
- mapper from typed object or mapping to projection row values;
- mapper from flat row mapping to typed result object;
- declared unknown/attribute bucket behavior;
- generated row decoder usable as `ProjectionTable.row_factory`;
- schema-hash material that includes mapping declarations;
- tests in Quire proving the same mapping works for at least two unrelated
  model shapes.

Required Quire tests:

- scalar path extraction and unflattening;
- enum coercion both directions;
- nested path flattening;
- JSON text encoding/decoding;
- optional missing path behavior;
- repeated child row expansion;
- reference field and FK metadata derivation;
- attribute bucket behavior only when explicitly declared;
- stable schema hash.

Gate:

```powershell
cd ..\quire
uv run pytest tests/test_derived_store.py tests/test_projection_mapping.py
uv run pyright quire
git status --short -- quire tests pyproject.toml uv.lock
```

Then push Quire and record the pushed commit SHA.

## Phase 2: Propstore Pin And Small Non-Claim Vertical

Status: pending.

Pin Propstore to the pushed Quire commit. Do not use a local path pin.

Start with a small non-claim row surface so the abstraction is proven not to be
claim-specific.

Candidate target:

- `propstore/families/relations/declaration.py`
  - delete `coerce_relationship_row`, `coerce_stance_row`,
    `coerce_conflict_row`;
  - route row decoding through Quire-generated row decoders;
  - keep opinion invariants and domain-specific diagnostic logic.

Alternative target:

- `propstore/families/concepts/declaration.py`
  - delete `coerce_parameterization_row`;
  - replace `ParameterizationRow.from_mapping` with Quire mapping where legacy
    key handling is explicitly declared.

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label quire-mapping-non-claim tests/test_sidecar_relation_edge_projection.py tests/test_relate_opinions.py tests/test_graph_build.py
rg -n "coerce_relationship_row|coerce_stance_row|coerce_conflict_row|coerce_parameterization_row" propstore/families --glob "declaration.py"
```

Required result:

- at least one non-claim handwritten row coercion family deleted;
- no DDL change unless intentionally recorded;
- no new Propstore-local generic mapping DSL.

## Phase 3: Concept Mapping Vertical

Status: pending.

Target:

- `ConceptRow.from_mapping`;
- `ConceptRow.to_dict`;
- `ParameterizationRow.from_mapping`;
- `ParameterizationRow.to_dict`;
- projection `row_factory` declarations for concept and parameterization rows.

Required behavior to preserve:

- `ConceptStatus` coercion;
- `ConceptId` normalization;
- logical ID parsing/rendering;
- `logical_id` compatibility render field if still required by caller tests;
- explicit unknown attribute bucket behavior if still needed;
- existing concept projection DDL and inserts.

Deletion rule:

- Delete the old method body before adding the Quire mapping replacement.
- If compatibility render fields such as `logical_id` are still required, model
  them as explicit derived render fields, not hidden row-class behavior.

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label quire-mapping-concept tests/test_sidecar_concept_projection.py tests/test_sidecar_parameterization_projection.py tests/test_graph_build.py tests/test_world_query.py
uv run scripts/typed_metadata_inventory.py --format json
```

Required result:

- concept row handwritten mapping LOC decreases;
- old concept row mapping methods are absent or reduced to semantic-only
  methods not expressible by Quire;
- DDL byte-equivalence holds.

## Phase 4: Claim Mapping Vertical Without Claim Privilege

Status: pending.

Open only after at least one non-claim vertical passes.

Target:

- `ClaimConceptLinkRow.from_mapping` and `to_dict`;
- parts of `ClaimRow.from_mapping` and `to_dict` that are generic projection
  mapping:
  - `logical_ids` <-> `primary_logical_id` and `logical_ids_json`;
  - `source.origin.*` <-> `source_origin_*`;
  - `source.trust.*` <-> `source_prior_base_rate`, `source_quality_json`,
    `source_derived_from_json`;
  - `provenance` <-> `provenance_page`, `source_paper`, `provenance_json`;
  - enum fields such as `type`, `algorithm_stage`, and `source_kind`;
  - repeated `concept_links` child rows.

Semantic behavior that may remain in Propstore:

- claim-type validation;
- payload-family meaning;
- SI value derivation;
- artifact identity and canonicalization;
- source-local rejection/normalization;
- domain-specific query/report decisions.

Required abstraction test:

- The same Quire mapping mechanism used here must still be used by the previous
  non-claim vertical. No claim-only escape hatch is allowed.

Gate:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label quire-mapping-claim tests/test_claim_roundtrip_fixtures.py tests/test_build_sidecar.py tests/test_world_query.py tests/test_relate_opinions.py tests/test_source_claims.py
uv run scripts/typed_metadata_inventory.py --format json
```

Required result:

- `ClaimConceptLinkRow` handwritten mapping deleted;
- `ClaimRow` loses generic flatten/unflatten code;
- any remaining `ClaimRow` methods are explicitly semantic and documented as
  not generic projection mapping.

## Phase 5: Projection Declaration Compression

Status: pending.

Only after Quire mapping specs can generate row decoders and table metadata.

Target:

- reduce verbose `ProjectionTable`, `ProjectionForeignKey`, and
  `ProjectionIndex` blocks in family declarations where they can be derived
  from projection mapping specs;
- keep domain-specific checks, FTS query semantics, and custom lifecycle code
  unless Quire has corresponding generic machinery.

Do not begin with claims. Prove this on relations, concepts, contexts, or
micropublications first.

Gate:

```powershell
uv run scripts/render_sidecar_ddl_baseline.py
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label quire-mapping-declarations tests/test_sidecar_projection_contract.py tests/test_build_sidecar.py tests/test_world_query.py
rg -n "ProjectionTable\\(|ProjectionForeignKey\\(|ProjectionIndex\\(" propstore/families --glob "declaration.py"
```

Required result:

- fewer handwritten projection declaration sites;
- DDL/FTS/vector output byte-equals baseline unless an intentional semantic diff
  is explicitly recorded;
- no Propstore-local generic declaration framework.

## Phase 6: FTS And Query-Plan Follow-Up

Status: blocked until separately specified.

FTS source SQL is not solved by row mapping alone. It needs a real Quire-owned
query-plan or FTS-source abstraction.

Do not hide existing FTS SQL strings inside helper functions and call that a
cleanup.

Open a separate workstream for:

- structured FTS source plans;
- generated FTS population SQL;
- search column validation from typed metadata;
- byte-equivalent FTS DDL and population behavior.

## Final Gates

Run:

```powershell
uv run scripts/typed_metadata_inventory.py --format markdown --limit 80
uv run scripts/typed_metadata_inventory.py --format json
uv run scripts/typed_metadata_inventory.py --gates --ledger workstreams/typed-metadata-owner-ledger-2026-05-15.csv
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label quire-projection-mapping-targeted tests/test_build_sidecar.py tests/test_world_query.py tests/test_sidecar_projection_contract.py tests/test_relate_opinions.py tests/test_graph_build.py
powershell -File scripts/run_logged_pytest.ps1 -Label quire-projection-mapping-full
```

Final report must include:

- baseline and final handwritten row mapping method counts;
- baseline and final `coerce_*_row` helper counts;
- baseline and final handwritten `ProjectionTable`/FK/index declaration counts;
- baseline and final Propstore Python LOC;
- baseline and final family declaration LOC;
- list of remaining row mapping methods and why each is semantic rather than
  generic mapping;
- Quire commit SHA used by Propstore.

Completion requires:

- Quire owns generic projection mapping mechanics;
- Propstore proves the mechanism on at least one non-claim family and then on
  claim mapping;
- no claim-only mapper or compatibility bridge remains;
- target metrics decrease;
- pyright, targeted tests, and full suite pass.
