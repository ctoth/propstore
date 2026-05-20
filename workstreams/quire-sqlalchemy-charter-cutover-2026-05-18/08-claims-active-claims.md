# Quire SQLAlchemy Charter Cutover: Claims And Activation Cleanup

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

Replace the claim projection/read-model/storage-helper surface with typed
claim charter models backed by Quire SQLAlchemy sessions.

End state:

- `Claim` is the canonical mapped claim model for sidecar reads/writes.
- `ClaimConceptLink` is a SQLAlchemy association object that owns link payload
  columns such as role, ordinal, and binding metadata.
- `claim.concept_links: list[ClaimConceptLink]` is the primary persistence
  relationship.
- `claim.concepts` is permitted only as a SQLAlchemy association proxy over
  `claim.concept_links`; it is not the persistence owner.
- numeric, text, and algorithm payloads are typed payload components declared
  once in the claim charter.
- `ActiveClaim` is deleted. Activation is a query state over typed `Claim`
  objects, not a second claim object family.
- `ActiveClaimInput`, `coerce_active_claim`, and `coerce_active_claims` are
  deleted with the dict/mapping boundary they supported.
- `ActiveClaimVariable` is renamed/moved to
  `propstore/families/claims/stages.py::ClaimAlgorithmVariable`
  as `ClaimAlgorithmVariable`.

## Prerequisites

Complete these cutover workstreams before this slice starts:

Required phase file prerequisites: `00-index.md`, `inventory-matrix.md`,
`helper-ledger.md`, `01-quire-capability-and-charter.md`,
`02-quire-sqlalchemy-engine.md`, `03-quire-fts-vector.md`,
`04-propstore-build-orchestration.md`, `05-source-and-diagnostics.md`,
`06-forms-concepts-parameterizations.md`, `07-contexts-lifting.md`.

- Quire SQLAlchemy dependency and capability proof, including association
  object proof.
- Quire charter/schema IR.
- Quire SQLAlchemy table/mapping/session/catalog engine.
- Quire FTS and vector implementation.
- Propstore build orchestration cutover.
- Source vertical slice.
- Forms and sources cleanup closure.
- Concept/form/parameterization slice.
- Context/lifting slice.

Before implementation, verify the current repo state and prove the prerequisite
surface is already cut over:

```powershell
git status --short
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label claim-prereq tests/test_world_query.py tests/test_required_schema_completeness.py tests/test_fixture_schema_parity.py tests/test_resolution_helpers.py
rg -n -F -- "ProjectionTable" propstore/families/claims propstore/derived_build.py propstore/derived_build_plan.py tests
rg -n -F -- "ProjectionModel" propstore/families/claims tests
rg -n -F -- "sqlite3.Connection" propstore/families/claims propstore/core/active_claims.py tests
```

This slice is blocked until the first two searches have zero production hits
outside notes, workstreams, docs, and reports, except hits in the claim files
named as deletion targets below.

## Target Models

Declare these Propstore domain models through the Quire charter system:

- `Claim`
- `ClaimConceptLink`
- `ClaimNumericPayload`
- `ClaimTextPayload`
- `ClaimAlgorithmPayload`

Payload requirements:

- use typed payload components, not parallel row dictionaries;
- numeric/text/algorithm payloads are separate SQL tables declared once in the
  claim charter;
- generic schema code derives insert/query mapping from that declaration;
- no field-specific optional conversion helper survives;
- field metadata may name the storage/payload field once, but must not encode
  a second dynamic type system;
- no `coerce` policy metadata, broad model-layer normalizer, or
  `claim_model_from_payload`-style factory is allowed in the replacement path;
- authored YAML/JSON parsing and raw row decoding are IO-boundary work only;
  typed compiler stages and mapped claim models must receive already-typed
  values and fail hard when the boundary did not produce them.

## Claim Concept Links

Decision:

- `ClaimConceptLink` is an association object, not a secondary table hidden
  behind a plain many-to-many collection.
- `claim.concept_links: list[ClaimConceptLink]` is the persistence
  relationship.
- `ClaimConceptLink` owns role, ordinal, binding name, condition position, and
  other link payload metadata required by claim semantics.
- `claim.concepts` is allowed only as a convenience association proxy over
  `claim.concept_links`.
- Link payload data must remain visible to graph construction, render policy,
  source promotion, conflict detection, and worldline materialization.

## Inventory Rows

| Inventory surface | Current owner | Final owner | Required action |
| --- | --- | --- | --- |
| `propstore/families/claims/projection_model.py` claim-owned symbols | Claim split storage/read mapper plus a co-located justification residual | Claim charter plus association objects | Delete claim-owned symbols in this phase; the only permitted residual top-level definitions in this file after this phase are `_nullable_text`, `_claim_id`, `TEXT_CODEC`, `CLAIM_ID_CODEC`, `JUSTIFICATION_STORAGE_MODEL`, and `JUSTIFICATION_TABLE` |
| `propstore/families/claims/declaration.py` projection compiler/populator paths | Claim sidecar compiler, raw projection-row writes, claim diagnostic row writes | Claim model construction, typed write plans, Quire sessions, and diagnostic model construction | Delete `compile_claim_sidecar_rows`, `populate_claims`, claim-family `ProjectionRow` usage, and claim-family `BUILD_DIAGNOSTICS_PROJECTION` writes |
| `propstore/families/claims/storage.py` storage shaping | Loose claim row preparation/helpers | Claim charter generic conversion | Delete storage-shaped helpers |
| `propstore/families/claims/storage.py` semantic conversions | Raw-id canonicalization, concept-ref resolution, unit normalization, stance-resolution conversion | `propstore/families/identity/claims.py`, `propstore/source/claims.py`, `propstore/families/claims/references.py`, `propstore/families/claims/stages.py`, `propstore/families/relations/declaration.py`, and `propstore/families/diagnostics/declaration.py` | Move each named semantic to its exact owner before deleting the storage-shaped remainder |
| `propstore/core/active_claims.py` row coercion | Runtime row repair | Typed `Claim` model plus query-state filters | Delete projection-row coercion and the parallel active claim object family |

## Field Metadata Rule

The target architecture is one declaration of field shape, plus typed values
flowing through the compiler/runtime. Do not replace projection codecs with a
new generic coercion layer in Propstore.

Before the next Phase 10 code slice, read and satisfy
`duplicate-definition-audit-2026-05-20.md` and
`charter-field-metadata-spec-2026-05-20.md` and
`coercion-compatibility-audit-2026-05-20.md`. These files are binding for this
phase: no `*CompiledPayload`, `*_from_payload` replacement factory, scalar
field DTO, broad `**values` mapped-model constructor, mapping-repair input
union, or table-routing helper may be added as a substitute for deleted
projection surfaces. If existing Quire cannot construct/write mapped objects
from the charter field list as the single shape, return to the Quire workstream
and add that generic catalog/session capability before more Propstore claim
code is written.

Allowed:

- Quire charter field metadata that describes storage field names, nullability,
  primary keys, indexes, relationships, JSON/enum adapter identity, and FKs;
- Propstore field metadata that only names a source/storage field once when a
  typed boundary object genuinely needs a stable external spelling;
- IO-boundary constructors with boundary-specific names such as
  `from_yaml_payload`, `from_json_payload`, or `from_row_mapping`, when they
  are the actual boundary and return typed domain objects.

Forbidden in this phase:

- `metadata={"coerce": ...}` on claim model or claim compiler-stage fields;
- generic `_coerce_*` or `*_from_payload` factories that accept loose mappings
  and repair strings, ints, floats, ids, enums, JSON, or rows inside the model
  layer;
- direct `str(...)`, `int(...)`, or `float(...)` cleanup while constructing
  mapped `Claim`, `ClaimConceptLink`, `ClaimNumericPayload`,
  `ClaimTextPayload`, or `ClaimAlgorithmPayload` objects from compiler-stage
  values;
- moving old projection codec behavior into a new Propstore helper, adapter,
  wrapper, alias, or compatibility surface;
- keeping a helper because it is "generic" when Quire already owns generic
  schema/session mechanics or when the type system should carry the value.

If a field cannot be constructed without broad coercion at this point in the
pipeline, the next action is to move the parsing/validation to the proper
IO/semantic owner or add the missing Quire generic capability. Do not add a
Propstore workaround.

## Deletion Targets

Delete these old production surfaces first, then use import/type/test failures
as the work queue:

- claim-owned contents of `propstore/families/claims/projection_model.py`;
- `propstore/families/claims/declaration.py` sidecar compiler/populator paths;
- `compile_claim_sidecar_rows`;
- `populate_claims`;
- claim-family `ProjectionRow` import, annotations, and row-carrier plumbing;
- claim-family `BUILD_DIAGNOSTICS_PROJECTION` writes;
- `CLAIM_CORE_STORAGE_MODEL`;
- `CLAIM_CONCEPT_LINK_STORAGE_MODEL`;
- `CLAIM_NUMERIC_PAYLOAD_STORAGE_MODEL`;
- `CLAIM_TEXT_PAYLOAD_STORAGE_MODEL`;
- `CLAIM_ALGORITHM_PAYLOAD_STORAGE_MODEL`;
- `CLAIM_ROW_MODEL`;
- `CLAIM_ROW_QUERY_PLAN`;
- `CLAIM_FTS_PROJECTION`;
- `CLAIM_EMBEDDING_STATUS_PROJECTION`;
- `CLAIM_EMBEDDING_JOIN_SOURCE`;
- `CLAIM_EMBEDDING_JOIN_COLUMNS`;
- `CLAIM_VEC_PROJECTION`;
- `CLAIM_*_TABLE` projection constants;
- `ClaimSidecarRows` row-carrier fields that only aggregate projection rows;
- `RawIdQuarantineSidecarRows`;
- `PromotionBlockedSidecarRows`;
- `_optional_float_input`;
- `_optional_string`;
- `_optional_int`;
- claim projection codecs for concept id, claim type, algorithm stage, logical
  ids, provenance, source, and concept-link role;
- claim model `coerce` metadata;
- generic claim model payload factories;
- generic `_coerce_claim_model_value`-style normalizers;
- `propstore/core/active_claims.py` after `ClaimAlgorithmVariable` is moved to
  `propstore/families/claims/stages.py`;
- `ActiveClaim` row-repair coercion that duplicates the claim charter;
- `ActiveClaimInput`;
- `ActiveClaim.from_claim`;
- `ActiveClaim.from_mapping`;
- `ActiveClaimVariable`;
- generic claim `from_mapping` projection constructors;
- `coerce_active_claim`;
- `coerce_active_claims`;
- `SimpleNamespace` claim/link repair paths.

This phase does not own the final deletion of
`propstore/families/claims/projection_model.py` while
`JUSTIFICATION_STORAGE_MODEL` remains in that file. Phase 10 owns
`_nullable_text`, `_claim_id`, `TEXT_CODEC`, `CLAIM_ID_CODEC`,
`JUSTIFICATION_STORAGE_MODEL`, `JUSTIFICATION_TABLE`, and the final file
deletion after the justification charter/model replaces them.

`ClaimCheckedBundle` is not deleted by name: it is a semantic compiler-stage
bundle. Its final shape must not import `ProjectionRow`, contain sidecar row
carriers, or expose projection/dict storage fields.

## Helper Classification: Claim Storage

File: `propstore/families/claims/storage.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `TypedClaimFields` | replace | Replace with `ClaimNumericPayload`, `ClaimTextPayload`, and `ClaimAlgorithmPayload`; delete the storage DTO. |
| `_optional_string` | delete | Generic nullable string conversion belongs to Quire charter conversion. |
| `_optional_float_input` | delete | Generic nullable numeric conversion belongs to Quire charter conversion. |
| `_optional_int` | delete | Generic nullable integer conversion belongs to Quire charter conversion. |
| `claim_version_id` | delete | Claim version identity comes from claim identity/domain model, not row preparation. |
| `_iter_claim_concept_link_values` | replace | Construct `ClaimConceptLink` association objects from claim contracts; delete tuple-row generation. |
| `_claim_concept_link_values_for_declaration` | replace | Construct `ClaimConceptLink` association objects from claim contracts; delete tuple-row generation. |
| `normalize_conditions_differ` | delete | Condition-difference serialization belongs to the relation/stance model JSON adapter. |
| `coerce_stance_resolution` | move | Move stance resolution validation to `propstore/families/relations/declaration.py::coerce_stance_resolution_payload`. |
| `resolution_opinion_columns` | move | Move opinion extraction to `propstore/families/relations/declaration.py::StanceResolutionOpinion.from_payload`. |
| `canonicalize_claim_for_storage` | move | Split raw-id/logical/artifact identity into `propstore/families/identity/claims.py`, source-local support into `propstore/source/claims.py`, and concept-reference lowering into `propstore/families/claims/references.py::resolve_first_claim_reference_id`; delete the storage function. |
| `extract_numeric_claim_fields` | replace | Replace with typed claim payload construction from claim contracts. |
| `extract_typed_claim_fields` | replace | Replace with typed claim payload construction from claim contracts. |
| `resolve_equation_sympy` | move | Move equation Sympy generation to `propstore/families/claims/stages.py::compile_claim_equation`. |
| `resolve_algorithm_storage` | move | Move algorithm body/canonical AST/stage handling to `propstore/families/claims/stages.py::compile_claim_algorithm`. |
| `extract_deferred_stance_rows_with_diagnostics` | move | Move embedded-stance validation/quarantine semantics to `propstore/families/relations/declaration.py::compile_embedded_stance_models`; replace tuple rows with `Stance` models. |
| `prepare_claim_insert_row` | delete | Replace with `Claim` model construction and SQLAlchemy session add. |
| `prepare_claim_concept_link_rows` | delete | Replace with `ClaimConceptLink` association objects and SQLAlchemy relationship persistence. |

File: `propstore/families/claims/stages.py`.

| Helper/surface | Classification | Required final owner/action |
| --- | --- | --- |
| `ClaimCheckedBundle` | keep-boundary | Keep as the checked semantic compiler-stage bundle; remove any projection-row or sidecar-row coupling from its reachable fields. |
| `ClaimSidecarRows` | delete | Replace with typed write plans and SQLAlchemy session adds. |
| `RawIdQuarantineSidecarRows` | delete | Replace with typed quarantine claim/diagnostic models written through claim and diagnostic owners. |
| `PromotionBlockedSidecarRows` | delete | Replace with typed promotion-blocked claim/diagnostic models written through claim and diagnostic owners. |

## Helper Classification: Active Claims

File: `propstore/core/active_claims.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `ActiveClaimVariable` | move | Rename/move to `propstore/families/claims/stages.py::ClaimAlgorithmVariable`; delete the `Active*` spelling. |
| `ClaimAlgorithmVariable` payload metadata | clean | Keep only stable payload field names if needed; delete `coerce` metadata and any model-layer broad coercion introduced by the move. Construction must receive typed `ConceptId`/strings from the boundary or fail at the boundary. |
| `_parse_conditions` | delete | Replaced by typed checked-condition fields on `Claim`; no row JSON repair. |
| `_parse_variables` | move | Move to `propstore/families/claims/stages.py::parse_claim_algorithm_variables`; delete runtime row parser. |
| `_parse_checked_conditions` | delete | Quire JSON adapter plus claim model owns checked-condition loading. |
| `_require_claim_concept_link_role` | delete | SQLAlchemy `ClaimConceptLink.role` uses typed enum validation. |
| `_coerce_claim_concept_link` | delete | `SimpleNamespace` link repair is deleted; `ClaimConceptLink` is the object. |
| `ActiveClaim` | delete | Replace with typed `Claim` plus activation query results; delete the parallel active claim object family. |
| `ActiveClaimInput` | delete | Runtime receives typed `Claim`; dict/mapping input unions are deleted. |
| `ActiveClaim.from_claim` | delete | Projection/dict coercion constructor is deleted. |
| `ActiveClaim.from_mapping` | delete | Projection-row construction path is deleted. |
| `ActiveClaim.to_dict` | replace | Replace with explicit view/document payload rendering that does not import `CLAIM_ROW_MODEL`. |
| `ActiveClaim.to_source_claim_payload` | move | Move conflict-detector payload rendering to `propstore/conflict_detector/collectors.py::conflict_claim_from_active_claim`; delete the `ActiveClaim` method. |
| `coerce_active_claim` | delete | Runtime receives typed `Claim`, not mappings. |
| `coerce_active_claims` | delete | Runtime receives typed `Claim`, not mappings. |

## Helper Classification: Projection Model Family

File: `propstore/families/claims/projection_model.py`.

| Helper family | Classification | Required final owner/action |
| --- | --- | --- |
| nullable scalar codecs such as `_nullable_int`, `_nullable_float`, `_optional_float`, `_optional_int` | delete | Quire charter conversion owns generic scalar/null handling; `_nullable_text` remains only as a Phase 10 justification residual. |
| id coercion codecs such as `_concept_id`, `_context_id`, `_justification_id` | delete | SQLAlchemy mapped model fields use typed id constructors at model/document boundaries; `_claim_id` remains only as a Phase 10 justification residual. |
| enum value codecs such as `_role_value`, `_claim_type_value`, `_algorithm_stage_value` | delete | Enum storage adapters are generic Quire SQLAlchemy adapters. |
| JSON/render helpers such as `_logical_ids_payload`, `_logical_ids_from_value`, `_logical_ids_to_columns`, `_logical_ids_from_columns`, `_provenance_to_columns`, `_provenance_from_columns`, `_source_to_columns`, `_source_from_columns`, `_normalize_conditions_differ` | replace | Replace with typed value objects and Quire JSON adapter; semantic payload rendering moves to document/view boundaries. |
| query-plan builders such as `claim_row_query_plan`, `_edge_column`, `claim_stance_policy_query_plan` | delete | SQLAlchemy relationships/session query construction replaces projection query-plan helpers. |

## Caller And Update Surfaces

Update every caller that imports or consumes claim projection rows, projection
models, raw SQLite selectors, storage-shaped row helpers, or ActiveClaim
row-repair helpers:

- `propstore/app/claim_views.py`;
- `propstore/app/claims.py`;
- `propstore/core/activation.py`;
- `propstore/core/active_claims.py`;
- `propstore/core/graph_build.py`;
- `propstore/core/analyzers.py`;
- `propstore/claim_graph.py`;
- `propstore/defeasibility.py`;
- `propstore/fragility.py`;
- `propstore/fragility_contributors.py`;
- `propstore/graph_export.py`;
- `propstore/relation_analysis.py`;
- `propstore/structured_projection.py`;
- `propstore/support_revision/projection.py`;
- `propstore/aspic_bridge/extract.py`;
- `propstore/aspic_bridge/translate.py`;
- `propstore/world/model.py`;
- `propstore/world/bound.py`;
- `propstore/world/overlay.py`;
- `propstore/world/atms.py`;
- `propstore/world/resolution.py`;
- `propstore/worldline/resolution.py`.

Required caller final state:

- app and claim view code render typed claim/view payloads without importing
  `CLAIM_ROW_MODEL`;
- Phase 11 owns claim sidecar runtime migration to Quire session/vector APIs;
- graph, analyzer, export, relation, support-revision, ASPIC, world, and
  worldline code consume typed `Claim`, `ClaimConceptLink`, payload, stance,
  and relation models;
- activation and active-claim code receives typed `Claim` objects, not
  mappings.

## Semantic Moves

Keep and move these Propstore claim semantics before deleting storage-shaped
helpers:

- claim type contracts;
- claim semantic checks;
- raw-id quarantine policy;
- draft/blocking diagnostics;
- source-local claim support;
- artifact/version/logical identity derivation;
- CEL checking and checked-condition IR;
- Sympy/algorithm canonicalization;
- unit/form compatibility checks;
- promotion-blocked diagnostics;
- raw-id canonicalization;
- concept-reference lowering and resolution;
- unit normalization;
- stance-resolution conversion;
- embedded-stance validation/quarantine semantics.

Target owners:

- `propstore/families/identity/claims.py` receives raw-id, logical id, and
  artifact/version identity helpers;
- `propstore/source/claims.py` receives source-local claim support;
- `propstore/families/claims/references.py::resolve_first_claim_reference_id`
  receives concept-reference lowering;
- `propstore/families/claims/stages.py::compile_claim_payload_models`
  receives unit/form compatibility checks, CEL, checked-condition IR, Sympy,
  and algorithm canonicalization;
- `propstore/families/claims/declaration.py::compile_claim_models` receives
  claim model, claim payload, claim-link, embedded-stance, and claim diagnostic
  model assembly from authored claim documents;
- `propstore/families/relations/declaration.py::coerce_stance_resolution_payload`,
  `StanceResolutionOpinion.from_payload`, and
  `compile_embedded_stance_models` receive stance-resolution validation,
  opinion extraction, condition-difference serialization, and embedded-stance
  quarantine semantics;
- `propstore/families/diagnostics/declaration.py::claim_diagnostics_to_models`
  receives draft/blocking, quarantine, and promotion-blocked diagnostic model
  construction for claim compilation;
- `propstore/conflict_detector/collectors.py::conflict_claim_from_active_claim`
  receives source-claim payload rendering that used to live on
  `ActiveClaim.to_source_claim_payload`.

Generic null, enum, JSON, table, query-plan, insert-row, and row-carrier
behavior moves to Quire charter/session/catalog machinery or disappears.

## Execution Loop

1. Read the current claim inventory entry and claim family files.
2. List all current production callers from the caller/update surface above.
3. Name the target models and the `claim.concept_links` association-object
   decision in the implementation notes or commit message.
4. Delete the old claim projection/read-model surface first.
5. Run the smallest import/type/test command that exposes the next failures.
6. Fix only failures caused by this slice's deletion and named caller list.
7. Replace raw SQLite access with Quire SQLAlchemy session/model access.
8. Replace loose dict/list/row payloads with typed claim, payload, and
   association objects.
9. Use Rope for the `ActiveClaimVariable` to `ClaimAlgorithmVariable` move or
   rename before hand-fixing imports and call sites. Verify with the named `rg`
   gates; Rope's model is not accepted as the final reference inventory.
10. Delete field-specific optional, enum, id, JSON, and row coercers once
   Quire charter conversion covers storage mechanics or the typed IO boundary
   owns parsing. Do not add Propstore `coerce` metadata, broad normalizer
   helpers, or model-layer loose-mapping factories while deleting them.
11. Run the family gates.
12. Run the old-path search gates.
13. Run the data-parity gate.

No Propstore workaround is allowed for a missing Quire generic feature. A
missing SQLAlchemy charter, association object, JSON, enum, relationship,
catalog, FTS, vector, or session capability returns the work to the Quire owner
workstream.

## Data-Parity Gate

```powershell
uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --before reports/sqlalchemy-charter-parity/claims-active-claims/before.sqlite --build-after sqlalchemy-charter --after reports/sqlalchemy-charter-parity/claims-active-claims/after.sqlite --owner claims-active-claims --workstream workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/08-claims-active-claims.md --out reports/sqlalchemy-charter-parity/claims-active-claims.json
```

Compare the captured projection baseline against the charter-generated sidecar
for this slice and compare:

- row counts for claim core, claim concept links, numeric payloads, text
  payloads, algorithm payloads, claim embedding source rows, and claim-linked
  diagnostics;
- primary-key/key-set coverage for every claim table this slice owns;
- claim lookup results by claim id, version id, logical id, and source-local
  identity;
- concept-link role, ordinal, and binding metadata;
- blocked/quarantine materialization;
- visibility filters and render policy output;
- FTS results for claim search surfaces;
- embedding source row coverage for claim embedding workflows;
- graph construction results;
- conflict resolution inputs and outputs;
- source claim promotion outputs;
- worldline materialization outputs.

The phase fails when a row, key, diagnostic, FTS hit, vector hit, semantic
query result, graph edge, conflict result, source promotion output, or
worldline materialization disappears.

Accepted parity difference allowlist:

- deleted projection constants, projection rows, row helpers, and coercion
  paths named in this file's deletion targets;
- no column rename, table rename, row disappearance, key disappearance,
  diagnostic disappearance, FTS-result disappearance, vector-result
  disappearance, semantic-query disappearance, graph-edge disappearance,
  conflict-result disappearance, source-promotion disappearance, or
  worldline-materialization disappearance is allowed.

## Required Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label claim-charter tests/test_world_query.py tests/test_resolution_helpers.py tests/test_render_policy_filtering.py
```

The final claim gate must prove: build, blocked/quarantine materialization,
claim lookup, concept-link roles, visibility filters, render policy, FTS,
embedding source rows, graph construction, conflict resolution, source claim
promotion, and worldline materialization.

Additional required searches:

```powershell
rg -n -F -- "CLAIM_CORE_STORAGE_MODEL" propstore tests
rg -n -F -- "CLAIM_CONCEPT_LINK_STORAGE_MODEL" propstore tests
rg -n -F -- "CLAIM_NUMERIC_PAYLOAD_STORAGE_MODEL" propstore tests
rg -n -F -- "CLAIM_TEXT_PAYLOAD_STORAGE_MODEL" propstore tests
rg -n -F -- "CLAIM_ALGORITHM_PAYLOAD_STORAGE_MODEL" propstore tests
rg -n -F -- "CLAIM_ROW_MODEL" propstore tests
rg -n -F -- "CLAIM_ROW_QUERY_PLAN" propstore tests
rg -n -F -- "CLAIM_FTS_PROJECTION" propstore tests
rg -n -F -- "CLAIM_EMBEDDING_STATUS_PROJECTION" propstore tests
rg -n -F -- "CLAIM_EMBEDDING_JOIN_SOURCE" propstore tests
rg -n -F -- "CLAIM_EMBEDDING_JOIN_COLUMNS" propstore tests
rg -n -F -- "CLAIM_VEC_PROJECTION" propstore tests
rg -n -F -- "CLAIM_CORE_TABLE" propstore tests
rg -n -F -- "CLAIM_CONCEPT_LINK_TABLE" propstore tests
rg -n -F -- "CLAIM_NUMERIC_PAYLOAD_TABLE" propstore tests
rg -n -F -- "CLAIM_TEXT_PAYLOAD_TABLE" propstore tests
rg -n -F -- "CLAIM_ALGORITHM_PAYLOAD_TABLE" propstore tests
rg -n -F -- "CLAIM_STORAGE_TABLES" propstore tests
rg -n -F -- "compile_claim_sidecar_rows" propstore tests
rg -n -F -- "populate_claims" propstore tests
rg -n -F -- "ProjectionRow" propstore/families/claims
rg -n -F -- "BUILD_DIAGNOSTICS_PROJECTION" propstore/families/claims tests
rg -n -F -- "ClaimSidecarRows" propstore tests
rg -n -F -- "RawIdQuarantineSidecarRows" propstore tests
rg -n -F -- "PromotionBlockedSidecarRows" propstore tests
rg -n -F -- "_optional_float_input" propstore tests
rg -n -F -- "_optional_string" propstore tests
rg -n -F -- "_optional_int" propstore tests
rg -n -F -- "TypedClaimFields" propstore tests
rg -n -F -- "prepare_claim_insert_row" propstore tests
rg -n -F -- "prepare_claim_concept_link_rows" propstore tests
rg -n -F -- "_iter_claim_concept_link_values" propstore tests
rg -n -F -- "_claim_concept_link_values_for_declaration" propstore tests
rg -n -F -- "canonicalize_claim_for_storage" propstore tests
rg -n -F -- "extract_numeric_claim_fields" propstore tests
rg -n -F -- "extract_typed_claim_fields" propstore tests
rg -n -F -- "resolve_equation_sympy" propstore tests
rg -n -F -- "resolve_algorithm_storage" propstore tests
rg -n -F -- "extract_deferred_stance_rows_with_diagnostics" propstore tests
rg -n -F -- "propstore.core.active_claims" propstore tests
rg -n -F -- "ActiveClaimInput" propstore tests
rg -n -F -- "ActiveClaimVariable" propstore tests
rg -n -F -- "ActiveClaim.from_claim" propstore tests
rg -n -F -- "ActiveClaim.from_mapping" propstore tests
rg -n -F -- "ActiveClaim(" propstore tests
rg -n -F -- "coerce_active_claim" propstore tests
rg -n -F -- "coerce_active_claims" propstore tests
rg -n -F -- "_coerce_claim_concept_link" propstore tests
rg -n -F -- "_require_claim_concept_link_role" propstore tests
rg -n -F -- "SimpleNamespace" propstore/families/claims propstore/core tests
rg -n -F -- "metadata={\"coerce\"" propstore/families/claims propstore/core tests
rg -n -F -- "\"coerce\":" propstore/families/claims propstore/core tests
rg -n -F -- "_coerce_claim_model_value" propstore tests
rg -n -F -- "claim_model_from_payload" propstore tests
```

All searches are zero-hit gates outside notes, workstreams, docs, and reports.

## Completion Criteria

This slice is complete only when:

- the claim charter declares `Claim`, `ClaimConceptLink`,
  `ClaimNumericPayload`, `ClaimTextPayload`, and `ClaimAlgorithmPayload`;
- `claim.concept_links` is the primary persistence relationship;
- `ClaimConceptLink` owns role, ordinal, binding name, and link metadata;
- `claim.concepts` exists only as a convenience association proxy over
  `claim.concept_links`;
- claim payloads are typed components persisted through the charter;
- claim population writes typed model objects through a Quire SQLAlchemy
  session;
- claim lookup, graph construction, conflict resolution, source promotion,
  render policy, FTS, embedding source rows, and worldline materialization use
  typed model/session APIs;
- every semantic move listed above has a final target module/function;
- `ActiveClaim`, `ActiveClaimInput`, `ActiveClaimVariable`,
  `coerce_active_claim`, and `coerce_active_claims` are absent from production
  code and tests;
- activation-specific claim behavior is expressed as typed `Claim` queries or
  owner-layer result objects, not a second claim class;
- every named caller/update surface no longer imports claim projection rows,
  storage models, table constants, raw SQLite selectors, or row dictionaries;
- the data parity gate passes;
- all required tests pass through the logged pytest wrapper;
- all old-path search gates above are zero-hit outside notes, workstreams,
  docs, and reports.

## Phase 10 Execution Record

Recorded 2026-05-20.

- Prerequisite state: `git status --short` showed only unrelated untracked
  paths outside this slice; `uv run pyright propstore` passed with 0 errors;
  `powershell -File scripts/run_logged_pytest.ps1 -Label claim-prereq
  tests/test_world_query.py tests/test_required_schema_completeness.py
  tests/test_fixture_schema_parity.py tests/test_resolution_helpers.py`
  passed with 166 tests in
  `logs/test-runs/claim-prereq-20260520-141305.log`.
- Prerequisite searches: `ProjectionTable`, `ProjectionModel`, and
  `sqlite3.Connection` still hit the claim projection/read-model deletion
  targets in `propstore/families/claims/projection_model.py`,
  `propstore/families/claims/declaration.py`, and
  `propstore/families/claims/sidecar_runtime.py`.
- Rope runner repair: `50294987` updated `scripts/rope_rename.py` to ignore
  generated and diagnostic roots such as `.tmp`, `.venv`, `logs`, `reports`,
  and `out`; the first Rope attempt failed by scanning generated `.tmp`
  Python files, and the repaired runner applied the required rename.
- Variable move commit: `75ae67a8` used Rope for
  `ActiveClaimVariable -> ClaimAlgorithmVariable`, moved the variable object
  and variable JSON parsing to `propstore/families/claims/stages.py`, and left
  `propstore/core/active_claims.py` importing the claim-stage owner API while
  the broader `ActiveClaim` deletion remains in progress.
- Metadata correction: the moved claim algorithm variable payload keys and
  coercion policy were moved onto `ClaimAlgorithmVariable` field metadata in
  `75ae67a8`; this is now classified as an incorrect replacement shape. The
  payload field names may remain only if they avoid duplicate external
  spelling. The `coerce` metadata and parser-side broad value repair must be
  deleted before the next claim replacement slice proceeds.
- Focused verification: `uv run pyright propstore/core/active_claims.py
  propstore/families/claims/stages.py` passed with 0 errors; `rg -n -F --
  "ActiveClaimVariable" propstore tests` returned zero hits.
- Aborted replacement review: an uncommitted draft attempted to replace claim
  projection write rows with `Claim`/payload dataclasses plus generic
  `metadata={"coerce": ...}` and a `claim_model_from_payload` factory. That
  draft was rejected as carrying the old projection codec behavior forward
  under a new name. The draft was removed from the worktree on 2026-05-20 and
  must not be revived.
- Claim variable cleanup: `472b2a60` removed `ClaimAlgorithmVariable` `coerce`
  field metadata, removed its generic kwargs repair helper, and kept only
  stable payload-name metadata. The parser now rejects non-string algorithm
  variable payload fields at that boundary instead of repairing them inside the
  model layer.
- Claim variable cleanup verification: `uv run pyright
  propstore/families/claims/stages.py propstore/core/active_claims.py` passed
  with 0 errors. `Select-String -SimpleMatch` searches for
  `metadata={"coerce"`, `"coerce":`, `_coerce_claim_model_value`, and
  `claim_model_from_payload` across `propstore/families/claims`,
  `propstore/core`, and `tests` returned no hits.
- Claim model charter slice: added the Phase 10 target classes `Claim`,
  `ClaimConceptLink`, `ClaimNumericPayload`, `ClaimTextPayload`, and
  `ClaimAlgorithmPayload` in `propstore/families/claims/declaration.py`;
  replaced the claim placeholder world records with those owner classes in
  `propstore/families/world_charters.py`; and declared
  `claim.concept_links` as the Quire SQLAlchemy association-object
  relationship over `ClaimConceptLink`.
- Claim model charter verification: `uv run pyright
  propstore/families/world_charters.py
  propstore/families/claims/declaration.py` passed with 0 errors, and
  `powershell -File scripts/run_logged_pytest.ps1 -Label claim-model-schema
  tests/test_required_schema_completeness.py` passed with 2 tests in
  `logs/test-runs/claim-model-schema-20260520-145308.log`.
- Typed claim compiler slice: replaced production
  `compile_claim_sidecar_rows` with `compile_claim_models`, replaced
  production `ClaimSidecarRows` usage with `ClaimWriteModels`, moved duplicate
  claim-version and duplicate concept-link handling into typed claim
  compilation, and changed the temporary concept-link compiler boundary to
  return typed `ClaimConceptLinkRole` values instead of role strings.
- Typed claim compiler verification: `uv run pyright
  propstore/families/claims/declaration.py
  propstore/families/claims/storage.py propstore/families/claims/stages.py
  propstore/derived_build_plan.py` passed with 0 errors, and `powershell -File
  scripts/run_logged_pytest.ps1 -Label claim-write-models
  tests/test_required_schema_completeness.py tests/test_fixture_schema_parity.py`
  passed with 4 tests in
  `logs/test-runs/claim-write-models-20260520-145752.log`.
- Typed claim compiler searches: `rg -n -F -- "compile_claim_sidecar_rows"
  propstore tests` returned zero hits. `rg -n -F -- "ClaimSidecarRows"
  propstore tests` has no production hits and still hits only the two
  old-`populate_claims` tests that must be removed or rewritten when
  `populate_claims` is deleted in this phase.
- Raw populator deletion slice: deleted `populate_claims`, rewrote the
  duplicate-claim regression tests to target `compile_claim_models` typed
  output, updated the sidecar exception test to fail the current
  SQLAlchemy write-batch path, and added the missing
  `ClaimConceptLink.claim` relationship in the claim concept-link charter.
- Raw populator deletion verification: `uv run pyright
  propstore/families/claims/declaration.py
  propstore/families/world_charters.py propstore/derived_build.py` passed with
  0 errors, and `powershell -File scripts/run_logged_pytest.ps1 -Label
  claim-populate-delete tests/test_codex2_claim_dedupe_diverges_on_version.py
  tests/remediation/phase_7_race_atomicity/test_T7_5f_sidecar_build_duplicate_claim.py
  tests/remediation/phase_1_crits/test_T1_2_sidecar_survives_exception.py
  tests/remediation/phase_7_race_atomicity/test_T7_5e_promotion_blocked_fk_payload.py`
  passed with 5 tests in
  `logs/test-runs/claim-populate-delete-20260520-150252.log`.
- Raw populator deletion searches: `rg -n -F -- "populate_claims" propstore
  tests`, `rg -n -F -- "ClaimSidecarRows" propstore tests`, and `rg -n -F --
  "compile_claim_sidecar_rows" propstore tests` all returned zero hits.
- Blocked/quarantine model slice: replaced `RawIdQuarantineSidecarRows` with
  `RawIdQuarantineModels`, replaced `PromotionBlockedSidecarRows` with
  `PromotionBlockedModels`, renamed the raw-id and promotion-blocked compilers
  to model-returning APIs, deleted their raw SQLite populators, and moved the
  promotion-blocked tests onto the SQLAlchemy typed flush path.
- Blocked/quarantine model verification: `uv run pyright
  propstore/families/claims/declaration.py
  propstore/families/claims/stages.py propstore/derived_build.py
  propstore/derived_build_plan.py` passed with 0 errors, and `powershell -File
  scripts/run_logged_pytest.ps1 -Label claim-blocked-models
  tests/remediation/phase_7_race_atomicity/test_T7_5b_promotion_diagnostic_scope.py
  tests/remediation/phase_7_race_atomicity/test_T7_5d_promotion_blocked_id_collision.py
  tests/remediation/phase_7_race_atomicity/test_T7_5e_promotion_blocked_fk_payload.py
  tests/remediation/phase_7_race_atomicity/test_T7_5f_sidecar_build_duplicate_claim.py
  tests/test_codex2_claim_dedupe_diverges_on_version.py` passed with 6 tests
  in `logs/test-runs/claim-blocked-models-20260520-150830.log`.
- Blocked/quarantine model searches: `rg -n -F --
  "RawIdQuarantineSidecarRows" propstore tests`, `rg -n -F --
  "PromotionBlockedSidecarRows" propstore tests`, `rg -n -F --
  "compile_raw_id_quarantine_sidecar_rows" propstore tests`, `rg -n -F --
  "compile_promotion_blocked_sidecar_rows" propstore tests`, and `rg -n -F --
  "populate_promotion_blocked_claims" propstore tests` all returned zero hits.
- Remaining Phase 10 work: delete the remaining claim projection/read-model,
  storage-helper, row-carrier, and active-claim compatibility surfaces; run
  the family gates, old-path searches, and data-parity gate.
- Duplicate-definition audit: `c92e57b9` added
  `duplicate-definition-audit-2026-05-20.md` after the uncommitted
  `ClaimCompiledPayload` draft was reverted. The audit records committed
  places where this execution introduced or left duplicate field/state
  definitions, mapping repair paths, broad kwargs constructors, and
  table-routing helpers. It must be read and satisfied before the next Phase 10
  code slice.
- Charter metadata specification: `charter-field-metadata-spec-2026-05-20.md`
  records the exact split between Quire charter metadata, Propstore semantic
  owner code, IO parsing, and missing Quire catalog/session capability. The
  spec says the replacement is not "put everything in metadata"; generic
  model construction and table routing must be Quire capability, and the claim
  slice must return to Quire if that capability is not present.
- Coercion/compatibility audit: `coercion-compatibility-audit-2026-05-20.md`
  requires classification of every `coerce`, `from_row_mapping`, old-shape,
  fallback, and compatibility path into real IO boundary, semantic lowering,
  or illegal compatibility shim before Phase 10 resumes. Known claim illegal
  surfaces include `ActiveClaim.from_row_mapping`, `coerce_active_claim`,
  `coerce_active_claims`, `ActiveClaimInput`, `CLAIM_ROW_MODEL.coerce`,
  `prepare_claim_insert_row`, `canonicalize_claim_for_storage` as a storage
  repair surface, `_optional_*`, and typed-claim field extraction helpers.
- Deletion-first restart: commits `503d6ec2`, `21108179`, `afa2bd94`,
  `0f8af73d`, and `08fcc4f3` deleted `propstore/core/active_claims.py`, the
  claim row-preparation helper family in `claims/storage.py`, `CLAIM_ROW_MODEL`,
  all claim-owned definitions in `claims/projection_model.py` except the
  justification residual, and the declaration-level claim projection query/FTS/
  embedding constants. These deletions intentionally made pyright fail so the
  old callers became the work queue.
- Quire capability repair: Quire commit `8a84f20` added charter-driven
  SQLAlchemy model construction and family write routing on `SqlAlchemySchema`
  and `DerivedSession`; Quire test gate `uv run pytest
  tests/test_sqlalchemy_engine.py` passed with 10 tests. Propstore commit
  `8b1daac7` pins Quire to pushed SHA
  `8a84f2014e6b3c7e844eb8b182f3b0c2c88a51c8`.
- Claim constructor/fake-row deletion: commits `10b2b748`, `64a25f57`, and
  `2fe0d1af` routed `world_record` through Quire construction, deleted broad
  `**values` constructors from `Claim` and claim payload models, and deleted
  fake `type="quarantine"` / `type="promotion_blocked"` claim rows. Blocked
  and quarantine state now remains diagnostic/status data instead of fake claim
  types.
- Current fix queue from `uv run pyright propstore`: Phase 10-local
  `prepare_claim_insert_row` is gone and `compile_claim_models` now constructs
  claim objects through Quire-backed `world_record` in commit `39e00ffb`.
  Remaining package errors are old callers of deleted `ActiveClaim`,
  `ActiveClaimInput`, `coerce_active_claim*`, `CLAIM_ROW_MODEL`, deleted claim
  embedding projection constants, and the relation policy import of deleted
  `CLAIM_CORE_TABLE`. Commits `45b97836`, `ee910916`, `ca253848`,
  `8e7a4127`, and `48367543` have started deleting those caller dependencies
  by moving direct users to typed `Claim` or deleting old active-claim paths.
- Typed claim caller deletion continued in commits `2e374684`, `5c4926f8`,
  `ec6d3dfd`, `d1811a66`, `6f388498`, `1f319925`, `6e60930a`, and
  `c8fcee5c`. These commits moved support-revision projection, worldline
  trace, worldline argumentation, world bridge protocols, journal replay,
  analyzers, graph build, and worldline runner off `ActiveClaim`,
  `coerce_active_claim*`, or `CLAIM_ROW_MODEL` where those callers only needed
  typed claim identity/core/link fields. Payload-derived scalar, condition, and
  algorithm-body behavior was not reintroduced through a helper or shim; those
  remaining paths must wait for typed payload relationships or be deleted.
- Current old-path search queue: `rg -n -F --
  "propstore.core.active_claims" propstore` still reports active callers in
  `aspic_bridge`, `app/concept_views.py`, `app/world_reasoning.py`,
  `preference.py`, `praf/engine.py`, `support_revision`, and `world`.
  `rg -n -F -- "CLAIM_ROW_MODEL" propstore` still reports callers in
  `app/claims.py`, `praf/engine.py`, `world/atms.py`, `world/overlay.py`,
  `world/queries.py`, and `worldline/resolution.py`. These hits remain the
  deletion work queue; no alias module or replacement row-model helper is
  allowed.
- Support revision state deletion: commit `c52eb16e` removed
  `coerce_active_claim` from `support_revision/state.py` and made
  `AssertionAtom.source_claims` accept typed `Claim` objects only. Snapshot
  decoding still has an old mapping-to-active-claim repair path and remains in
  the deletion queue; it must not be replaced with another mapping normalizer.
- Support revision snapshot deletion: commit `bacd01e9` removed
  `coerce_active_claim` from `support_revision/snapshot_types.py`. Snapshot
  decoding now rejects embedded `source_claims` mappings instead of rebuilding
  active-claim rows, and serialization records `source_claim_ids` rather than
  duplicating full claim mappings. The remaining support-revision active-claim
  hit is `support_revision/af_adapter.py`.
- Support revision argumentation deletion: commit `4ea9d47b` removed the last
  `propstore.core.active_claims` import under `support_revision`. The revision
  argumentation overlay now stores typed `Claim` objects directly and derives
  the concept id from the claim association-object links or `target_concept`.
  The refreshed active-claim import search now reports only `aspic_bridge`,
  `app`, `preference.py`, `praf/engine.py`, `world`, and
  `worldline/resolution.py`.
- Preference deletion: commit `699590f8` removed the active-claim branch from
  `preference.py`; preference scoring now consumes the mapping-shaped graph
  metadata already passed by analyzers and tests. The refreshed active-claim
  import search now reports `aspic_bridge`, `app`, `praf/engine.py`, `world`,
  and `worldline/resolution.py`.
- Concept-view deletion: commit `9b4c5791` removed the `ActiveClaim` import
  from `app/concept_views.py`, switched visible claim rendering to typed
  `Claim` identity/type/source/link fields, and deleted scalar/unit/
  uncertainty/condition/provenance-object reads instead of recreating them
  through a row helper. The refreshed active-claim import search now reports
  only `aspic_bridge`, `app/world_reasoning.py`, `praf/engine.py`, `world`,
  and `worldline/resolution.py`.
- App world-reasoning deletion: commit `1bc0369b` removed
  `coerce_active_claims` from `app/world_reasoning.py`; the app extension
  report now requires `bound.active_claims()` to return typed `Claim` objects
  and drops payload-row fields from the report lines. The refreshed
  active-claim import search now reports only `aspic_bridge`, `praf/engine.py`,
  `world`, and `worldline/resolution.py`.
