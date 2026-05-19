# Quire SQLAlchemy Charter Cutover: Claims And Active Claims

Date: 2026-05-18

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
- `ActiveClaim` no longer repairs projection rows or duplicates the claim
  charter. Active runtime behavior remains only as an explicitly named view
  over typed `Claim` data or as owner-layer rendering/adaptation.

## Prerequisites

Complete these cutover workstreams before this slice starts:

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
- no field-specific optional conversion helper survives.

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
| `propstore/families/claims/projection_model.py` | Claim split storage/read mapper | Claim charter plus association objects | Delete |
| `propstore/families/claims/storage.py` storage shaping | Loose claim row preparation/helpers | Claim charter generic conversion | Delete storage-shaped helpers |
| `propstore/families/claims/storage.py` semantic conversions | Raw-id canonicalization, concept-ref resolution, unit normalization, stance-resolution conversion | Claim semantic owner modules | Move semantics to claim stages/passes/identity/relation owner modules before deleting storage-shaped remainder |
| `propstore/core/active_claims.py` row coercion | Runtime row repair | Typed `Claim` model and explicit active-claim view model | Delete projection-row coercion; keep only named active runtime view behavior |
| `propstore/families/claims/sidecar_runtime.py` | Claim embedding/relation runtime over raw sidecar connection | Claim runtime over Quire session/vector APIs | Replace raw derived-store connection usage |

## Deletion Targets

Delete these old production surfaces first, then use import/type/test failures
as the work queue:

- `propstore/families/claims/projection_model.py`;
- `CLAIM_CORE_STORAGE_MODEL`;
- `CLAIM_CONCEPT_LINK_STORAGE_MODEL`;
- `CLAIM_NUMERIC_PAYLOAD_STORAGE_MODEL`;
- `CLAIM_TEXT_PAYLOAD_STORAGE_MODEL`;
- `CLAIM_ALGORITHM_PAYLOAD_STORAGE_MODEL`;
- `CLAIM_ROW_MODEL`;
- `CLAIM_ROW_QUERY_PLAN`;
- `CLAIM_FTS_PROJECTION`;
- `CLAIM_EMBEDDING_STATUS_PROJECTION`;
- `CLAIM_VEC_PROJECTION`;
- `CLAIM_*_TABLE` projection constants;
- `ClaimSidecarRows` row-carrier fields that only aggregate projection rows;
- `_optional_float_input`;
- `_optional_string`;
- `_optional_int`;
- claim projection codecs for claim id, concept id, claim type, algorithm
  stage, logical ids, provenance, source, and concept-link role;
- `ActiveClaim` row-repair coercion that duplicates the claim charter;
- `ActiveClaim.from_mapping`;
- generic claim `from_mapping` projection constructors;
- `coerce_active_claim`;
- `coerce_active_claims`;
- `SimpleNamespace` claim/link repair paths.

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
| `coerce_stance_resolution` | move | Move stance resolution validation to the relation/stance semantic owner. |
| `resolution_opinion_columns` | move | Move opinion extraction to a typed stance-resolution value object. |
| `canonicalize_claim_for_storage` | move | Split raw-id/logical/artifact identity into claim identity/source promotion owners; split concept-reference lowering into claim semantic normalization; delete the storage function. |
| `extract_numeric_claim_fields` | replace | Replace with typed claim payload construction from claim contracts. |
| `extract_typed_claim_fields` | replace | Replace with typed claim payload construction from claim contracts. |
| `resolve_equation_sympy` | move | Move equation Sympy generation to claim semantic compilation. |
| `resolve_algorithm_storage` | move | Move algorithm body/canonical AST/stage handling to claim semantic compilation. |
| `extract_deferred_stance_rows_with_diagnostics` | move | Move embedded-stance validation/quarantine semantics to relation/stance owner; replace tuple rows with `Stance` models. |
| `prepare_claim_insert_row` | delete | Replace with `Claim` model construction and SQLAlchemy session add. |
| `prepare_claim_concept_link_rows` | delete | Replace with `ClaimConceptLink` association objects and SQLAlchemy relationship persistence. |

## Helper Classification: Active Claims

File: `propstore/core/active_claims.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `ActiveClaimVariable` | move | Keep as algorithm variable value object only when the `Claim`/algorithm payload model uses it directly; otherwise move to claim algorithm payload model. |
| `_parse_conditions` | delete | Replaced by typed checked-condition fields on `Claim`; no row JSON repair. |
| `_parse_variables` | move | Move to algorithm payload document/model boundary; delete runtime row parser. |
| `_parse_checked_conditions` | delete | Quire JSON adapter plus claim model owns checked-condition loading. |
| `_require_claim_concept_link_role` | delete | SQLAlchemy `ClaimConceptLink.role` uses typed enum validation. |
| `_coerce_claim_concept_link` | delete | `SimpleNamespace` link repair is deleted; `ClaimConceptLink` is the object. |
| `ActiveClaim.from_mapping` | delete | Projection-row construction path is deleted. |
| `ActiveClaim.to_dict` | replace | Replace with explicit view/document payload rendering that does not import `CLAIM_ROW_MODEL`. |
| `ActiveClaim.to_source_claim_payload` | move | Move conflict-detector payload rendering to a conflict-detector input adapter; delete the `ActiveClaim` method. |
| `coerce_active_claim` | delete | Runtime receives typed `Claim` or named active view models, not mappings. |
| `coerce_active_claims` | delete | Runtime receives typed `Claim` or named active view models, not mappings. |

## Helper Classification: Projection Model Family

File: `propstore/families/claims/projection_model.py`.

| Helper family | Classification | Required final owner/action |
| --- | --- | --- |
| nullable scalar codecs such as `_nullable_text`, `_nullable_int`, `_nullable_float`, `_optional_float`, `_optional_int` | delete | Quire charter conversion owns generic scalar/null handling. |
| id coercion codecs such as `_claim_id`, `_concept_id`, `_context_id`, `_justification_id` | delete | SQLAlchemy mapped model fields use typed id constructors at model/document boundaries. |
| enum value codecs such as `_role_value`, `_claim_type_value`, `_algorithm_stage_value` | delete | Enum storage adapters are generic Quire SQLAlchemy adapters. |
| JSON/render helpers such as `_logical_ids_payload`, `_logical_ids_from_value`, `_logical_ids_to_columns`, `_logical_ids_from_columns`, `_provenance_to_columns`, `_provenance_from_columns`, `_source_to_columns`, `_source_from_columns`, `_normalize_conditions_differ` | replace | Replace with typed value objects and Quire JSON adapter; semantic payload rendering moves to document/view boundaries. |
| query-plan builders such as `claim_row_query_plan`, `_edge_column`, `claim_stance_policy_query_plan` | delete | SQLAlchemy relationships/session query construction replaces projection query-plan helpers. |

## Caller And Update Surfaces

Update every caller that imports or consumes claim projection rows, projection
models, raw SQLite selectors, storage-shaped row helpers, or ActiveClaim
row-repair helpers:

- `propstore/app/claim_views.py`;
- `propstore/app/claims.py`;
- `propstore/families/claims/sidecar_runtime.py`;
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
- claim sidecar runtime uses Quire session/vector APIs, not raw derived-store
  connections;
- graph, analyzer, export, relation, support-revision, ASPIC, world, and
  worldline code consume typed `Claim`, `ClaimConceptLink`, payload, stance,
  and relation models;
- activation and active-claim code receives typed `Claim` objects or named
  active view models, not mappings.

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

- claim identity/source promotion owners receive raw-id, logical id,
  artifact/version identity, and source-local support;
- claim semantic normalization receives concept-reference lowering and
  unit/form compatibility checks;
- claim semantic compilation receives CEL, checked-condition IR, Sympy, and
  algorithm canonicalization;
- relation/stance owner receives stance-resolution validation, opinion
  extraction, condition-difference serialization, and embedded-stance
  quarantine semantics;
- diagnostics owner receives draft/blocking and promotion-blocked diagnostics;
- conflict-detector input adapter receives source-claim payload rendering that
  used to live on `ActiveClaim.to_source_claim_payload`.

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
9. Delete field-specific optional, enum, id, JSON, and row coercers once
   generic charter conversion covers the field.
10. Run the family gates.
11. Run the old-path search gates.
12. Run the data-parity gate.

No Propstore workaround is allowed for a missing Quire generic feature. A
missing SQLAlchemy charter, association object, JSON, enum, relationship,
catalog, FTS, vector, or session capability returns the work to the Quire owner
workstream.

## Data Parity Gate

```powershell
uv run scripts/compare_sqlalchemy_charter_parity.py --before <old-sidecar.sqlite> --after <new-sidecar.sqlite> --owner claims-active-claims --out reports/sqlalchemy-charter-parity/claims-active-claims.json
```

Build the sidecar from the same repository snapshot before and after this
slice and compare:

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
worldline materialization disappears. The only accepted disappearances are the
table constants, projection rows, row helpers, and coercion paths named as
deletion targets in this file. Accepted column/table renames must be listed in
the implementation closure report or commit message.

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
rg -n -F -- "propstore.families.claims.projection_model" propstore tests
rg -n -F -- "CLAIM_CORE_STORAGE_MODEL" propstore tests
rg -n -F -- "CLAIM_CONCEPT_LINK_STORAGE_MODEL" propstore tests
rg -n -F -- "CLAIM_NUMERIC_PAYLOAD_STORAGE_MODEL" propstore tests
rg -n -F -- "CLAIM_TEXT_PAYLOAD_STORAGE_MODEL" propstore tests
rg -n -F -- "CLAIM_ALGORITHM_PAYLOAD_STORAGE_MODEL" propstore tests
rg -n -F -- "CLAIM_ROW_MODEL" propstore tests
rg -n -F -- "CLAIM_ROW_QUERY_PLAN" propstore tests
rg -n -F -- "CLAIM_FTS_PROJECTION" propstore tests
rg -n -F -- "CLAIM_EMBEDDING_STATUS_PROJECTION" propstore tests
rg -n -F -- "CLAIM_VEC_PROJECTION" propstore tests
rg -n -F -- "CLAIM_CORE_TABLE" propstore tests
rg -n -F -- "CLAIM_CONCEPT_LINK_TABLE" propstore tests
rg -n -F -- "CLAIM_NUMERIC_PAYLOAD_TABLE" propstore tests
rg -n -F -- "CLAIM_TEXT_PAYLOAD_TABLE" propstore tests
rg -n -F -- "CLAIM_ALGORITHM_PAYLOAD_TABLE" propstore tests
rg -n -F -- "CLAIM_STORAGE_TABLES" propstore tests
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
rg -n -F -- "ActiveClaim.from_mapping" propstore tests
rg -n -F -- "coerce_active_claim" propstore tests
rg -n -F -- "coerce_active_claims" propstore tests
rg -n -F -- "_coerce_claim_concept_link" propstore tests
rg -n -F -- "_require_claim_concept_link_role" propstore tests
rg -n -F -- "SimpleNamespace" propstore/families/claims propstore/core tests
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
- every semantic move listed above has a final Propstore owner;
- `ActiveClaim` no longer owns mapping repair, row JSON parsing, source-claim
  payload rendering, or projection-row coercion;
- every named caller/update surface no longer imports claim projection rows,
  storage models, table constants, raw SQLite selectors, or row dictionaries;
- the data parity gate passes;
- all required tests pass through the logged pytest wrapper;
- all old-path search gates above are zero-hit outside notes, workstreams,
  docs, and reports.
