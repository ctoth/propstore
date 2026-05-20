# Charter Field Metadata Specification

Date: 2026-05-20

## Verdict

The replacement is not "put everything in field metadata." That would be
another dynamic type system.

The replacement is:

- schema shape is declared once in Quire `FamilyCharter` / `CharterField` /
  `CharterRelationship` / `CharterFtsIndex` / `CharterVectorCache`;
- semantic compilation remains in the exact Propstore owner;
- authored YAML/JSON parsing remains at the IO boundary;
- generic object construction and table routing must be Quire catalog/session
  capability, not Propstore helper code;
- Propstore must not add DTOs, mapping repair helpers, broad `**values`
  constructors, or `metadata={"coerce": ...}` to fill gaps.

## Existing Quire Metadata Carriers

Read from `C:\Users\Q\code\quire\quire\charters.py`,
`schema_ir.py`, `sql_types.py`, `sqlalchemy_schema.py`, and
`sqlalchemy_store.py`.

`CharterField` currently supports only these schema facts:

- `name`
- `python_type`
- `nullable`
- `primary_key`
- `foreign_key`
- `index`
- `unique`
- `generated`
- `default`
- `default_sql`
- `json_value_object`
- `enum_type`
- `search`
- `vector_dimensions`
- `source_local_only`
- `canonical_only`
- `metadata`

`CharterRelationship` supports:

- relationship name;
- target family;
- FK field;
- `back_populates`;
- `uselist`;
- association-object marker;
- metadata.

`FamilyCharter` supports:

- family/model identity;
- fields;
- lifecycle states;
- indexes;
- FTS indexes;
- vector caches;
- relationships;
- semantic metadata.

`metadata` is not a coercion or conversion slot. It may carry stable semantic
labels that Quire preserves into schema catalogs and SQLAlchemy column `info`.
It must not carry parser functions, coercers, source-to-storage rewriting
rules, old field aliases, or dynamic value repair policy.

## Missing Quire Capability Before Full Single-Definition Closure

The current Quire engine generates tables, mappings, sessions, schema catalogs,
FTS tables, vector caches, enum adapters, JSON value-object adapters, and
relationships.

It does not yet provide a catalog-owned model construction/write-routing API
that lets Propstore remove all mapped-model constructor field lists and
per-family `_claim_batches` / `_concept_batches` routing.

Required Quire capability before deleting the broad constructors and table
routing everywhere:

- Given a family key, return the family charter, main mapped model class, and
  primary identity field from the catalog.
- Given a family key and reference value, resolve the canonical identity using
  declared reference surfaces such as primary identity, primary logical id,
  logical ids, aliases, local ids, slugs, tags, or other charter-declared
  alternate keys.
- Given `(family_name, typed_values)`, construct a mapped object using the
  charter field list as the only accepted field list.
- Reject unknown fields.
- Reject missing non-null, non-default fields before write.
- Preserve enum and JSON value-object fields without Propstore coercion.
- Given typed objects grouped by family, route writes through the catalog
  family/table mapping without Propstore per-family table-name helper
  functions.

If this capability is not present when a deletion slice reaches it, execution
returns to the Quire workstream. Do not replace it with Propstore DTOs or
kwargs helpers.

Per-family identity lookup wrappers are not an acceptable substitute for this
capability. `resolve_claim`, `resolve_concept`, `resolve_alias`,
`resolve_*_id`, and equivalent thin methods must be deleted rather than moved
or rebuilt. Family-local semantic methods are allowed on typed ORM/domain
objects only when they interpret already-loaded typed fields and relationships.

## Claim Helper Responsibility Map

| Old responsibility | Final owner/spec | Metadata? | Required action |
| --- | --- | --- | --- |
| `TypedClaimFields` scalar DTO | Claim payload charters: `claim_numeric_payload`, `claim_text_payload`, `claim_algorithm_payload` | No custom metadata | Delete DTO; use typed `ClaimDocument` and exact model fields. |
| `_optional_string`, `_optional_float_input`, `_optional_int` | IO boundary plus Quire nullable scalar field handling | `nullable=True/False`, `python_type` only | Delete helpers. Do not replace with field metadata coercers. |
| `claim_version_id` | Claim identity/domain model | No | Delete helper; `version_id` is required typed claim identity before sidecar compilation. |
| `canonicalize_claim_for_storage` raw-id/logical/version identity | `propstore/families/identity/claims.py` and source-local claim owner | No | Move semantic identity derivation; sidecar compiler receives typed resolved claim identity. |
| `canonicalize_claim_for_storage` concept-reference lowering | `propstore/families/claims/references.py` / checked claim pipeline | No | Move/use typed reference resolution before model construction. |
| `extract_numeric_claim_fields` | typed claim document plus numeric payload charter fields | No | Delete row DTO extraction. Numeric fields are already `ClaimDocument` fields and `claim_numeric_payload` charter fields. |
| `extract_typed_claim_fields` claim-type field selection | claim type contracts in `families/claims/documents.py` plus direct typed document access | No | Delete helper; do not create a second field-selection table. |
| `resolve_equation_sympy` | `propstore/families/claims/stages.py::compile_claim_equation` | No | Move semantic compilation. Output fields remain `sympy_generated`, `sympy_error` in text payload charter. |
| `resolve_algorithm_storage` | `propstore/families/claims/stages.py::compile_claim_algorithm` | No | Move semantic compilation. Output fields remain `body`, `canonical_ast`, `variables_json`, `algorithm_stage` in algorithm payload charter. |
| `_iter_claim_concept_link_values` / `_claim_concept_link_values_for_declaration` | `ClaimTypeContract.concept_links` plus `ClaimConceptLink` association object | No extra metadata | Delete tuple-row helpers; construct association objects from typed checked claim contract data. |
| `prepare_claim_concept_link_rows` | `ClaimConceptLink` association-object persistence | `CharterRelationship(... association_object=True ...)` and FK fields | Delete row helper. |
| `normalize_conditions_differ` | relation/stance JSON adapter or exact relation semantic owner | No claim metadata | Move to relation phase owner; do not keep in claim storage. |
| `coerce_stance_resolution` | relation declaration owner | No claim metadata | Move to relation owner; if IO parsing is needed, boundary-specific parser. |
| `resolution_opinion_columns` | relation declaration owner value object | No claim metadata | Move to relation owner. |
| `extract_deferred_stance_rows_with_diagnostics` | relation declaration owner, returning typed stance/relation models and diagnostics | No claim metadata | Move/delete tuple-row surface. |
| `prepare_claim_insert_row` | direct typed claim/payload model creation from checked semantic claim plus Quire catalog-owned constructor | Charter fields and missing Quire constructor | Delete helper. If direct construction requires duplicate field lists, return to Quire. |

## Exact Claim Charter Shape

The claim sidecar schema facts belong in `world_charters.py` charters, not in
Propstore helper metadata.

`claim_core` fields:

- `id`: `str`, primary key, non-null.
- `primary_logical_id`: `str`, non-null, default SQL `''`.
- `logical_ids_json`: `str`, non-null, default SQL `'[]'`.
- `version_id`: `str`, non-null, default SQL `''`.
- `content_hash`: `str`, non-null, default SQL `''`.
- `seq`: `int`, non-null.
- `type`: `ClaimType`, non-null, enum text through Quire enum adapter.
- `target_concept`: `str | null`.
- `source_slug`: `str | null`.
- `source_paper`: `str`, non-null.
- `provenance_page`: `int`, non-null.
- `provenance_json`: `str | null`.
- `context_id`: `str | null`.
- `premise_kind`: `str`, non-null, default SQL `'ordinary'`.
- `branch`: `str | null`.
- `build_status`: `str`, non-null, default SQL `'ingested'`.
- `stage`: `str | null`.
- `promotion_status`: `str | null`.

`claim_core` indexes:

- `target_concept`
- `type`
- `primary_logical_id`
- `build_status`
- `stage`
- `promotion_status`

`claim_core` relationships:

- `concept_links` to `claim_concept_link`, FK `claim_id`,
  `back_populates="claim"`, association object.

`claim_concept_link` fields:

- `claim_id`: `str`, primary key, non-null, FK to `claim_core`.
- `concept_id`: `str`, primary key, non-null, FK to `concept`.
- `role`: `ClaimConceptLinkRole`, primary key, non-null, enum text through
  Quire enum adapter.
- `ordinal`: `int`, primary key, non-null.
- `binding_name`: `str | null`.

`claim_concept_link` relationships:

- `claim` to `claim_core`, FK `claim_id`, `back_populates="concept_links"`,
  scalar.

`claim_numeric_payload` fields:

- `claim_id`: `str`, primary key, non-null, FK to `claim_core`.
- `value`: `float | null`.
- `lower_bound`: `float | null`.
- `upper_bound`: `float | null`.
- `uncertainty`: `float | null`.
- `uncertainty_type`: `str | null`.
- `sample_size`: `int | null`.
- `unit`: `str | null`.
- `value_si`: `float | null`.
- `lower_bound_si`: `float | null`.
- `upper_bound_si`: `float | null`.

`claim_text_payload` fields:

- `claim_id`: `str`, primary key, non-null, FK to `claim_core`.
- `conditions_cel`: `str | null`.
- `conditions_ir`: `str | null`.
- `statement`: `str | null`.
- `expression`: `str | null`.
- `sympy_generated`: `str | null`.
- `sympy_error`: `str | null`.
- `name`: `str | null`.
- `measure`: `str | null`.
- `listener_population`: `str | null`.
- `methodology`: `str | null`.
- `notes`: `str | null`.
- `description`: `str | null`.
- `auto_summary`: `str | null`.

`claim_algorithm_payload` fields:

- `claim_id`: `str`, primary key, non-null, FK to `claim_core`.
- `body`: `str | null`.
- `canonical_ast`: `str | null`.
- `variables_json`: `str | null`.
- `algorithm_stage`: `str | null`.

`claim_algorithm_payload` indexes:

- `algorithm_stage`.

Claim FTS:

- `claim_fts`, entity id `claim_id`, fields `statement`, `conditions`,
  `expression`, populated from the existing source query joining
  `claim_core` and `claim_text_payload`.

Claim vector/embedding:

- Do not encode claim embedding joins as Propstore constants once Quire vector
  cache metadata can own them. Until then, existing constants are old-path
  deletion targets, not a place for new metadata.

## State Specification

State names are not coercion metadata.

Claim lifecycle/state surfaces that must be explicit:

- authored/checking/canonical lifecycle belongs in `FamilyCharter.lifecycle_states`
  or exact semantic owner objects.
- build/render state (`build_status`) is a sidecar/runtime field because it is
  queried at render/build time.
- source promotion state (`promotion_status`) is a source/promotion lifecycle
  field and must not be faked through claim type strings.
- algorithm stage is claim algorithm semantic state and remains a typed
  boundary value before being stored in `claim_algorithm_payload.algorithm_stage`.

The current synthetic `type="quarantine"` and `type="promotion_blocked"`
pattern is not valid if `type` is the `ClaimType` enum field. Quarantine and
promotion-blocked status must be represented through explicit state fields and
diagnostic records, not fake claim types.

## What Must Not Be Added

Do not add:

- `metadata={"coerce": ...}`;
- any metadata that names parser/converter callables;
- any metadata that lists old input aliases for compatibility;
- `*CompiledPayload`;
- `*_from_payload` model factories in the replacement path;
- `from_row_mapping` repair constructors for runtime models;
- `Input = Model | Mapping[...]` unions in core/runtime;
- broad `**values` mapped-model constructors;
- new per-family table routing helpers.

## Required Workstream Consequence

Before Phase 10 can resume, either:

1. prove existing Quire can construct/write mapped objects from charter fields
   without Propstore duplicate constructors or per-family routing, or
2. return to the Quire workstream and add that generic catalog/session
   capability first.

No Propstore claim code may be written that depends on a second field list
while this is unresolved.
