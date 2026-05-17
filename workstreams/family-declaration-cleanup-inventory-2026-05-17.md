# Family Declaration Cleanup Inventory - 2026-05-17

Status: current inventory for the next broader typed-metadata cleanup.

Parent workstreams:

- `workstreams/repo-wide-typed-metadata-cleanup-workstream-2026-05-14.md`
- `workstreams/generic-quire-projection-mapping-workstream-2026-05-16.md`
- `workstreams/quire-explicit-projection-boundaries-workstream-2026-05-16.md`
- `workstreams/source-generic-machinery-deletion-workstream-2026-05-17.md`

## Current Verified Shape

The source-specific cleanup is complete and should not be treated as the main
remaining surface. Current scanner output from:

```powershell
uv run scripts/typed_metadata_inventory.py --format markdown --limit 80
```

shows:

| Package | Lines | Projection Columns | Raw SQL Score | Codec Methods | Mapping Hints | Class Surfaces |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `families` | 16472 | 18 | 273 | 57 | 83 | 24 |
| `world` | 11186 | 0 | 4 | 2 | 26 | 52 |
| `app` | 10215 | 0 | 0 | 5 | 52 | 179 |
| `core` | 9109 | 0 | 0 | 45 | 26 | 7 |
| `source` | 3589 | 0 | 0 | 0 | 12 | 3 |

The next problem is family-owned derived-store declaration/query/mapping
boilerplate, not more source-local cleanup.

Old explicit-boundary surfaces are currently absent in the searched production
and test surfaces:

- `decode_columns`
- `CompositePath`
- `DerivedPath`
- `attribute_bucket`
- `decode_key`
- `ignored_columns`
- `claim_select_sql`
- `STANCE_SELECT_COLUMNS`
- `claim_stance_projection_row`

## Cleanup Target

For each family, one semantic declaration must own:

- projection table/column/FK/index identity;
- row encode/decode shape;
- typed query/read-model rows;
- FTS source plans;
- vector/status source plans;
- family reference boundaries;
- source-local versus canonical visibility;
- diagnostics/quarantine facts if that family owns them.

Quire owns the generic execution of those declarations. Propstore owns semantic
meaning. Propstore must not keep hand-written table/query/mapping boilerplate
once the declaration can express it.

## Family Inventory

| Family | Current files | Remaining custom surfaces | Why it matters | First old-path searches |
| --- | --- | --- | --- | --- |
| contexts and lifting | `propstore/families/contexts/declaration.py`, `propstore/context_lifting.py`, `propstore/compiler/context.py`, world query context reconstruction | `CONTEXT_*_PROJECTION`, `ContextSidecarRows`, raw `SELECT` over context tables, lifting materialization validation | Context references are shared by claims, micropublications, relations, diagnostics, and lifting. Cleaning this establishes the reference/cardinality pattern. | `FROM context`, `FROM context_assumption`, `FROM context_lifting_rule`, `FROM context_lifting_materialization`, `CONTEXT_.*PROJECTION` |
| claims | `propstore/families/claims/declaration.py`, `propstore/families/claims/projection_model.py`, `propstore/families/claims/storage.py`, `propstore/families/claims/stages.py` | `ClaimRow`, `ClaimConceptLinkRow`, `SourcePromotionClaimRow`, `CLAIM_*_PROJECTION`, `CONFLICT_WITNESS_PROJECTION`, `JUSTIFICATION_PROJECTION`, claim FTS/vector/status declarations, raw `SELECT`/`JOIN` over claim tables, promotion blocked row compilation | Claims are large but not special. They must be included as a full family vertical, not deferred indefinitely. The claim split into core/link/numeric/text/algorithm/justification/conflict/FTS/vector is load-bearing until proven otherwise. | `ClaimRow`, `ClaimConceptLinkRow`, `SourcePromotionClaimRow`, `FROM claim_core`, `FROM claim_concept_link`, `FROM claim_text_payload`, `CLAIM_.*PROJECTION`, `claim_fts`, `claim_vec` |
| concepts/forms/parameterization | `propstore/families/concepts/declaration.py`, `propstore/families/concepts/projection_model.py`, concept app/query callers | `ConceptRow`, `ParameterizationRow`, `ConceptRelationshipProjectionRow`, `CONCEPT_PROJECTION`, `FORM_PROJECTION`, `FORM_ALGEBRA_PROJECTION`, alias/parameterization/group declarations, concept FTS/vector/status declarations, many concept SQL queries | This is the densest query family after claims. It owns search, forms, aliases, and concept relationship surfaces. | `ConceptRow`, `ParameterizationRow`, `FROM concept`, `FROM alias`, `FROM parameterization`, `CONCEPT_.*PROJECTION`, `concept_fts`, `concept_vec` |
| relations and opinions | `propstore/families/relations/declaration.py`, `propstore/families/relations/projection_model.py`, `propstore/relation_analysis.py`, `propstore/world/queries.py`, graph/ASPIC readers | `RelationshipRow`, `StanceRow`, `ConflictRow`, relation-edge query APIs, conflict witness query APIs, opinion fields | Relation edge is the polymorphic physical table and is the main proof that claims are not privileged. Opinion metadata must be typed, not hidden in loose row surfaces. | `RelationshipRow`, `StanceRow`, `ConflictRow`, `FROM relation_edge`, `FROM conflict_witness`, `RELATION_EDGE_TABLE`, `opinion_` |
| sources | `propstore/families/sources/declaration.py`, source app/status/promote readers | `SOURCE_PROJECTION`, `SourceProjectionRow`, source query helpers, source trust projection fields | Canonical sources and source-local documents must stay separated. Source cleanup removed generic source machinery, but family source projection remains a family vertical. | `SOURCE_PROJECTION`, `SourceProjectionRow`, `FROM source`, `source_quality`, `source_prior_base_rate` |
| diagnostics and quarantine | `propstore/families/diagnostics/declaration.py`, authoring lints, source status, compiler diagnostics | `BUILD_DIAGNOSTICS_PROJECTION`, `SourceStatusDiagnosticRow`, `QuarantinableWriter`, raw diagnostics select/delete helpers | Diagnostics are cross-family but should still be a typed diagnostic declaration, not a custom SQL island. | `BUILD_DIAGNOSTICS_PROJECTION`, `FROM build_diagnostics`, `SourceStatusDiagnosticRow`, `QuarantinableWriter` |
| micropublications | `propstore/families/micropublications/declaration.py`, micropublication documents, world query readers | `MICROPUBLICATION_PROJECTION`, `MICROPUBLICATION_CLAIM_PROJECTION`, `MicropublicationProjectionRow`, `MicropublicationClaimProjectionRow`, raw select with nested claim aggregation | Micropublications tie contexts and claims together and exercise many-to-many child rows. | `MICROPUBLICATION_.*PROJECTION`, `FROM micropublication`, `FROM micropublication_claim`, `MicropublicationProjectionRow` |
| grounded rules | `propstore/families/rules/declaration.py`, grounding build/inspection/query paths | `GROUNDED_FACT_PROJECTION`, `GROUNDED_FACT_EMPTY_PREDICATE_PROJECTION`, `GROUNDED_BUNDLE_INPUT_PROJECTION`, three projection row classes, raw select reconstruction | Grounding persists enough input to rehydrate grounded bundles; it needs typed projection rows, not table-specific helpers. | `GROUNDED_.*PROJECTION`, `FROM grounded_fact`, `FROM grounded_bundle_input`, `GroundedFactProjectionRow` |
| calibration | `propstore/families/calibration/declaration.py`, trust calibration readers | `CALIBRATION_COUNTS_PROJECTION`, `CalibrationCountsProjectionRow`, raw select helper | Smallest vertical; useful as a low-risk proof for declaration compression after harder shared patterns are known. | `CALIBRATION_COUNTS_PROJECTION`, `FROM calibration_counts`, `CalibrationCountsProjectionRow` |
| embeddings/vector | `propstore/families/embeddings/declaration.py`, claim/concept declarations, heuristic/app embedding callers | embedding model/status projections, dynamic vec table declarations, snapshot/restore plumbing | Vector storage is generic machinery plus semantic text identity. Quire owns vector mechanics; families own text/source meaning. | `embedding_status`, `concept_embedding_status`, `claim_vec`, `concept_vec`, `rowid_vec_projection`, `embedding_status_projection` |

## Cross-Family Repeated Surfaces

These are not separate verticals. They are repeated patterns that each family
vertical must reduce when it touches the owner:

- row dataclasses whose main job is projection storage shape;
- raw `conn.execute(...)` with table-name SQL in family declarations;
- hand-authored `ProjectionTable`, `ProjectionForeignKey`, and
  `ProjectionIndex` lists not generated from the family projection model;
- FTS `source_query` SQL strings not declared through a Quire FTS source plan;
- vector/status declaration calls not sourced from one family semantic
  embedding declaration;
- sidecar row bundle classes that only package projection rows;
- typed app/world request/report rows that merely restate family fields.

## Required Per-Family Inventory Before Edits

For each family vertical, append a short section to this inventory before
editing production code:

- exact old-path search commands;
- exact files owned by the slice;
- row classes to delete;
- projection constants to delete or move under generated/declaration ownership;
- raw SQL query helpers to delete or replace with generated typed query APIs;
- FTS/vector declarations involved;
- tests that prove behavior;
- scanner metrics expected to decrease;
- any load-bearing table split that is deliberately retained.

## Initial Execution Order

The workstream must include claims. The order is:

1. contexts and lifting;
2. claims, first inventory then split into sub-slices if needed;
3. relations and opinions;
4. concepts/forms/parameterization;
5. diagnostics/quarantine;
6. micropublications;
7. grounded rules;
8. sources;
9. calibration;
10. embeddings/vector.

Claims are second so they are neither privileged as the only architecture driver
nor avoided because they are large.
