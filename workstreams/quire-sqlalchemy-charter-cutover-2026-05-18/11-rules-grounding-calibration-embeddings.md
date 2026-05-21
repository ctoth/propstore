# Quire SQLAlchemy Charter Cutover: Rules, Grounding, Calibration, And Embeddings

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

Replace the rules, grounding, calibration, and embedding projection/vector
surfaces with Propstore domain models backed by Quire SQLAlchemy charters and
Quire vector APIs.

End state:

- grounded rule persistence uses typed `GroundedFact`,
  `GroundedEmptyPredicate`, and `GroundedBundleInput` models;
- calibration counts use typed `CalibrationCount` queries;
- embedding registry, status, vector search, and snapshot/restore paths use
  Quire vector/session APIs;
- rule, calibration, and embedding family declarations no longer import or
  declare `ProjectionTable` or `VecProjection`;
- grounding, calibration, and embedding runtime callers no longer open raw
  sidecar SQLite connections for owned reads and writes.

Binding notes from the 2026-05-20 update:

- Do not replace grounding, calibration, embedding, claim-similarity, or
  concept-similarity old helpers with per-family identity lookup wrappers,
  convenience methods, or renamed helper-shaped APIs.
- Rule, calibration, embedding, claim, and concept references must use generic
  Quire family reference/FK lookup and generic Quire main-model access. Missing
  generic lookup/main-model or vector/session capability is Quire work, not a
  Propstore family-specific workaround.
- Family semantics may live on typed ORM/domain objects when the behavior is
  domain-specific, including grounded-rule bundle semantics, calibration count
  meaning, embedding model identity, text source policy, entity resolution
  policy, and snapshot report semantics. Generic identity, FK, table, session,
  vector, and main-model lookup mechanics do not belong in these families.
- Current Phase 10 claim work has already deleted the claim-family embedding
  projection constants and claim row-model production surface. This phase must
  repair embedding code by deleting the old projection/vector handoff and using
  generic Quire vector/session APIs; it must not restore
  `CLAIM_EMBEDDING_STATUS_PROJECTION`, `CLAIM_VEC_PROJECTION`,
  claim embedding join constants, `select_claim_embedding_rows`,
  `CLAIM_ROW_MODEL`, or a claim-specific vector adapter.
- Claim and concept similarity must return typed search results from owner
  APIs over Quire vector/session data. Do not keep row-shaped similarity
  helpers, generic `from_mapping` constructors, direct sidecar connections, or
  per-family lookup wrappers as a transition path.
- No subsection of this phase is complete while any owned `ProjectionTable`,
  `VecProjection`, raw `sqlite3.Connection`, sidecar runtime row helper, vector
  store adapter, or projection constant remains in production.

Current old-surface findings from `rg` on 2026-05-20:

- `propstore/families/rules/declaration.py` still defines
  `GROUNDED_FACT_PROJECTION`,
  `GROUNDED_FACT_EMPTY_PREDICATE_PROJECTION`,
  `GROUNDED_BUNDLE_INPUT_PROJECTION`, the grounded projection row classes,
  `create_grounded_fact_table`, `populate_grounded_facts`,
  `_persist_bundle_inputs`, `_read_bundle_inputs`, `read_grounded_facts`, and
  `read_grounded_bundle`.
- `propstore/families/calibration/declaration.py` still defines
  `CALIBRATION_COUNTS_PROJECTION`, `CalibrationCountsProjectionRow`, and
  `load_calibration_counts` over a raw `sqlite3.Connection`.
- `propstore/families/embeddings/declaration.py` still imports embedding
  projection/vector declarations, defines `ensure_embedding_tables`,
  `SidecarEmbeddingRegistry`, `_SidecarEntityEmbeddingStore`,
  `SidecarClaimEmbeddingStore`, `SidecarConceptEmbeddingStore`, and
  `SidecarEmbeddingSnapshotStore`, and accepts raw `sqlite3.Connection` across
  embedding workflows.
- `propstore/families/claims/sidecar_runtime.py` and
  `propstore/families/concepts/sidecar_runtime.py` still open raw sidecar
  connections with `connect_sqlite_store`, set `row_factory`, and expose
  `find_similar_claim_rows`, `find_similar_concept_rows`, and
  `SidecarClaimRelationStore`.

Current audit update on 2026-05-20:

- Status: not started. This phase remains a future workstream and is blocked
  until the current Phase 10 claim queue is clean and Phases 11 and 12 are
  complete.
- Current Phase 10 queue from `uv run pyright propstore`: 25 package errors
  remain. The embedding-owned dependency is
  `propstore/families/embeddings/declaration.py` importing deleted
  `CLAIM_EMBEDDING_JOIN_COLUMNS`, `CLAIM_EMBEDDING_JOIN_SOURCE`,
  `CLAIM_EMBEDDING_STATUS_PROJECTION`, `CLAIM_VEC_PROJECTION`, and
  `select_claim_embedding_rows` from the claim family. This phase must not
  restore those deleted claim projection symbols; it must delete the old
  embedding projection/vector handoff and route through Quire vector/session
  APIs.
- Current old-path searches: `GROUNDED_FACT_PROJECTION` remains in
  `propstore/families/rules/declaration.py`; `MICROPUBLICATION_PROJECTION` and
  relation old paths remain earlier-phase work; `VecProjection` currently has
  no hits under `propstore/families/embeddings` or `tests`, but embedding code
  still imports Quire sqlite-vec projection-backed store types and raw
  sidecar connection APIs. A zero-hit `VecProjection` search alone is not a
  completion signal for this phase.
- Known dependency from completed Phase 10 work: claim embedding text and
  similarity callers must consume typed `Claim` fields and payload
  relationships. Do not reintroduce row-only claim fields such as `claim_id`,
  `claim_type`, `statement`, or `artifact_id`, and do not add a claim-specific
  lookup/vector wrapper to replace the deleted projection constants.

Diagnostics projection cleanup is owned by
`05-source-and-diagnostics.md`. This workstream depends on the typed
`BuildDiagnostic` service already existing for embedding restore diagnostics
and does not re-own diagnostics table deletion.

2026-05-21 execution update:

- The prior 2026-05-20 "not started / blocked until Phase 10, Phase 11, and
  Phase 12 are complete" audit note is superseded. `09-relations-stances-conflicts.md`,
  `10-micropublications-justifications.md`, and
  `10a-charter-generated-model-cleanup.md` have completed their prerequisite
  gates.
- `git status --short` has no tracked task-owned changes; unrelated untracked
  diagnostic/local paths remain outside this workstream.
- `uv run pyright propstore` passed with zero errors.
- `powershell -File scripts/run_logged_pytest.ps1 -Label support-family-prereq
  tests/test_world_query.py tests/test_opinion_schema.py
  tests/test_fixture_schema_parity.py
  tests/test_required_schema_completeness.py` passed with 161 tests and 29
  expected warnings; log:
  `logs/test-runs/support-family-prereq-20260521-084854.log`.
- The prerequisite `ProjectionTable(` search reports only the named rule and
  calibration deletion targets in `propstore/families/rules/declaration.py`
  and `propstore/families/calibration/declaration.py`.
- The prerequisite `VecProjection` search under `propstore/families/embeddings`
  and `tests` returned zero hits.
- The prerequisite `sqlite3.Connection` search reports only the named raw
  connection deletion/replacement targets in rules, calibration, and embedding
  owner files.

Implementation may start with Slice 1: grounding/rules charter and projection
deletion.

2026-05-21 Slice 1 execution update:

- Production commit `6d195be1` deleted the rule `ProjectionTable` constants,
  grounded projection row DTOs, raw grounded table creation helper, and raw
  grounded read/write helpers from `propstore/families/rules/declaration.py`.
  Grounded persistence now constructs typed `GroundedFact`,
  `GroundedFactEmptyPredicate`, and `GroundedBundleInput` models and writes
  them through a Quire `DerivedSession`.
- `propstore/world/model.py` now opens a Quire read-only SQLAlchemy session
  for `WorldQuery.grounding_bundle()` and loads the typed grounded bundle
  through the rule owner API. The old raw connection bundle read path is gone.
- Test commit `7c44207a` migrated the grounding rule persistence tests from
  raw in-memory SQLite/projection helpers to charter-created SQLAlchemy stores,
  typed sessions, `persist_grounded_bundle`, `load_grounded_sections`, and
  `load_grounded_bundle`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label
  typed-grounded-rules tests/test_sidecar_grounded_facts.py
  tests/test_grounded_bundle_round_trip.py
  tests/test_ws7_grounding_completion.py` passed with 16 tests; log:
  `logs/test-runs/typed-grounded-rules-20260521-090429.log`.
- Grounding helper old-path searches for `GroundedFactProjectionRow`,
  `GroundedFactEmptyPredicateProjectionRow`,
  `GroundedBundleInputProjectionRow`, `create_grounded_fact_table`,
  `populate_grounded_facts`, `_persist_bundle_inputs`,
  `_read_bundle_inputs`, `read_grounded_facts`, and
  `read_grounded_bundle` returned zero hits under `propstore` and `tests`.
- `uv run pyright propstore` passed with zero errors after the grounded-rule
  production and test migration.

2026-05-21 Slice 2 caller migration update:

- Caller inventory found no deleted raw grounded persistence helper imports in
  `propstore/grounding`, `propstore/app`, `propstore/world`,
  `propstore/fragility_contributors.py`, or the grounding tests.
- `propstore/world/model.py` is already migrated by commit `6d195be1` and
  reads persisted grounded bundles through a Quire read-only SQLAlchemy
  session plus typed rule owner API.
- `propstore/grounding/inspection.py`, `propstore/grounding/loading.py`,
  `propstore/app/grounding.py`, `propstore/fragility_contributors.py`, and
  `propstore/merge/structured_merge.py` do not consume the deleted rule
  persistence helpers; they either build semantic runtime bundles from
  repository authoring or consume already-typed bundle objects.
- Searches for `create_grounded_fact_table`, `populate_grounded_facts`,
  `read_grounded_facts`, and `read_grounded_bundle` across the grounding,
  app, world, fragility, and test caller surfaces returned zero hits.
- `sqlite3.Connection` returned zero hits under `propstore/families/rules`,
  `propstore/grounding`, and `tests`.

Slice 2 is complete. Continue with Slice 3: calibration charter and query
cutover.

2026-05-21 Slice 3 calibration execution update:

- Production commit `6ca7d15a` deleted
  `CALIBRATION_COUNTS_PROJECTION`, `CalibrationCountsProjectionRow`, and the
  raw `sqlite3.Connection` loader from
  `propstore/families/calibration/declaration.py`.
- Calibration reads now use `calibration_counts_by_key(derived)` over a Quire
  `DerivedSession` and typed `CalibrationCount` models.
- `propstore/families/world_charters.py` now exposes the methods-only
  `CalibrationCount` `FamilyModel` subclass for the `calibration_counts`
  charter. Storage field shape remains only in charter metadata.
- `uv run pyright propstore` passed with zero errors after the production
  deletion.
- Test commit `e63556a1` migrated
  `tests/test_sidecar_calibration_counts_projection.py` and the calibration
  infrastructure tests in `tests/test_calibrate.py` to charter-created
  SQLAlchemy stores, Quire sessions, typed `CalibrationCount` inserts, and
  `calibration_counts_by_key`.
- `powershell -File scripts/run_logged_pytest.ps1 -Label
  typed-calibration-counts tests/test_sidecar_calibration_counts_projection.py
  tests/test_calibrate.py` passed with 35 tests; log:
  `logs/test-runs/typed-calibration-counts-20260521-091159.log`.
- Calibration old-path searches for `CALIBRATION_COUNTS_PROJECTION`,
  `CalibrationCountsProjectionRow`, `load_calibration_counts`, and
  `sqlite3.Connection` under the calibration family and tests returned zero
  hits.

Slice 3 is complete. Continue with Slice 4: embedding vector backend handoff
to Quire APIs.

2026-05-21 Slice 4 embedding vector backend execution update:

- Production commit `333ab15d` deleted `load_vec_extension`,
  `_require_sqlite_vec`, `ensure_embedding_tables`,
  `_SidecarEntityEmbeddingStore`, `SidecarClaimEmbeddingStore`, and
  `SidecarConceptEmbeddingStore` from
  `propstore/families/embeddings/declaration.py`.
- Embedding workflows now use Quire `SqlAlchemyVecRegistry`,
  `SqlAlchemyVecEntityStore`, and `SqlAlchemyVecSnapshotStore` through
  Quire SQLAlchemy sessions and charter-declared vector caches.
- `propstore/heuristic/embed.py` no longer takes sidecar store objects. It
  operates on typed `EmbeddingEntity` values plus explicit vector-cache
  operations, so the old store class handoff is not needed.
- Concept embedding identity lookup now uses Quire family reference metadata:
  `propstore/families/world_charters.py` declares `primary_logical_id` and
  `canonical_name` as concept reference keys, and embedding lookup calls
  Quire `require_reference_id` plus the family identity field.
- `propstore/families/claims/sidecar_runtime.py` no longer imports the
  deleted explicit vector-extension loader. Quire sessions load vector
  support from schema vector-cache metadata.
- `uv run pyright propstore` passed with zero errors after the production
  deletion.
- Production searches for `load_vec_extension`, `ensure_embedding_tables`,
  `SidecarClaimEmbeddingStore`, `SidecarConceptEmbeddingStore`, and
  `_SidecarEntityEmbeddingStore` across the edited production files returned
  zero hits.
- Test commit `7333badd` migrated embedding vector tests to the Quire
  SQLAlchemy/vector path:
  `tests/test_embed_operational_error.py` now exercises explicit typed
  `EmbeddingEntity` plus callback operations instead of old store protocol
  objects; `tests/test_no_embedding_key_collision.py` now creates the
  charter-backed SQLAlchemy store and typed `EmbeddingModel` rows directly;
  `tests/test_world_query.py` no longer monkeypatches the deleted explicit
  vector-extension loader.
- `powershell -File scripts/run_logged_pytest.ps1 -Label
  embedding-vector-handoff tests/test_embed_operational_error.py
  tests/test_no_embedding_key_collision.py tests/test_world_query.py` passed
  with 156 tests and 29 expected warnings; log:
  `logs/test-runs/embedding-vector-handoff-20260521-092929.log`.

Slice 4 is complete. Continue with Slice 5: claim and concept embedding
runtime migration, starting with deletion of `SidecarClaimRelationStore`,
`find_similar_claim_rows`, and `find_similar_concept_rows`.

2026-05-21 Slice 5 claim/concept embedding runtime execution update:

- Production/test commit `4b47a68e` deleted `SidecarClaimRelationStore`,
  `find_similar_claim_rows`, `find_similar_concept_rows`, and the
  `from_search_row` similarity-result constructors.
- Claim relation classification no longer receives a sidecar store wrapper or
  explicit vector-extension hook. `propstore/heuristic/relate.py` now receives
  typed callback operations for registered models, claim text policy, claim ID
  enumeration, and typed `ClaimSimilarityHit` results.
- `propstore/families/claims/sidecar_runtime.py` no longer opens raw sidecar
  SQLite connections for relation workflows. Claim text source policy reads
  typed `Claim`/`ClaimTextPayload` models through Quire sessions, and relation
  workflows pass Quire vector/session-backed owner operations directly.
- `propstore/families/concepts/sidecar_runtime.py` no longer uses
  `WorldQuery.resolve_concept` for concept embedding request lowering; it uses
  Quire generic family reference lookup through `schema.require_reference_id`.
- Embedding similarity owner APIs now return typed `ClaimSimilarityHit` and
  `ConceptSimilarityHit` values. App and WorldQuery callers consume those
  typed hits instead of row dictionaries.
- `uv run pyright propstore` passed with zero errors after the migration.
- `powershell -File scripts/run_logged_pytest.ps1 -Label
  embedding-runtime-migration tests/test_relate_bulk.py
  tests/test_claim_workflows.py tests/test_concept_workflows.py
  tests/test_world_query.py` passed with 161 tests and 29 expected warnings;
  log: `logs/test-runs/embedding-runtime-migration-20260521-094249.log`.
- Searches for `SidecarClaimRelationStore`, `find_similar_claim_rows`,
  `find_similar_concept_rows`, and `from_search_row` across `propstore` and
  `tests` returned zero hits.
- Searches for `connect_sqlite_store`, `connect_sqlite_store_readonly`,
  `sqlite3.Connection`, and `row_factory` in the claim/concept sidecar runtime
  files returned zero hits.
- The `from_mapping` gate is still not closed because
  `tests/claim_model_helpers.py` exposes `claim_model_from_mapping` and its
  callers. Slice 6 must delete or rename that test helper instead of treating
  the focused Slice 5 migration as phase completion.

Slice 5 production migration is complete. Continue with Slice 6: data parity,
vector parity, remaining search gates, and completion gates.

## Prerequisites

Complete these cutover workstreams before this slice starts:

Required phase file prerequisites: `00-index.md`, `inventory-matrix.md`,
`helper-ledger.md`, `01-quire-capability-and-charter.md`,
`02-quire-sqlalchemy-engine.md`, `03-quire-fts-vector.md`,
`04-propstore-build-orchestration.md`, `05-source-and-diagnostics.md`,
`06-forms-concepts-parameterizations.md`, `07-contexts-lifting.md`,
`08-claims-active-claims.md`, `08a-typed-claim-graph-projection.md`,
`09-relations-stances-conflicts.md`,
`10-micropublications-justifications.md`,
`10a-charter-generated-model-cleanup.md`.

- Quire SQLAlchemy dependency and capability proof.
- Quire charter/schema IR.
- Quire SQLAlchemy table/mapping/session/catalog engine.
- Quire FTS and vector implementation.
- Propstore build orchestration cutover.
- Source and diagnostics cutover.
- Forms, concepts, and parameterizations cutover.
- Contexts and lifting cutover.
- Claims and active claims cutover.
- Relations, stances, and conflicts cutover.
- Justifications and micropublications cutover.
- Charter-generated model cleanup.

Before implementation, verify the current repo state and prove the
prerequisite surface is already cut over:

```powershell
git status --short
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label support-family-prereq tests/test_world_query.py tests/test_opinion_schema.py tests/test_fixture_schema_parity.py tests/test_required_schema_completeness.py
rg -n -F -- "ProjectionTable(" propstore/families/rules propstore/families/calibration propstore/families/embeddings tests
rg -n -F -- "VecProjection" propstore/families/embeddings tests
rg -n -F -- "sqlite3.Connection" propstore/families/rules propstore/families/calibration propstore/families/embeddings propstore/grounding tests
```

Implementation starts after the first two searches report only the files and
helpers named as deletion targets in this workstream. Production hits outside
those targets block implementation.

## Target Models

Declare these Propstore domain models through the Quire charter system:

- `GroundedFact`
- `GroundedEmptyPredicate`
- `GroundedBundleInput`
- `CalibrationCount`
- `EmbeddingModel`
- `ClaimEmbeddingStatus`
- `ConceptEmbeddingStatus`
- `EmbeddingVector`

Quire owns generic table creation, mapping, session lifecycle, JSON/null
conversion, vector registration, vector storage, vector search, and vector
snapshot mechanics. Propstore owns grounded-rule bundle semantics, calibration
meaning, embedding entity policy, embedding text source policy, and embedding
snapshot report semantics.

## Inventory Rows

| Inventory surface | Current owner | Final owner | Required action |
| --- | --- | --- | --- |
| `propstore/families/rules/declaration.py` projection pieces | Grounding sidecar persistence | Grounding charter plus semantic persistence | Delete generic projection table plumbing |
| `propstore/families/calibration/declaration.py` | Calibration count projection/query | Calibration charter plus typed query | Delete projection table plumbing |
| `propstore/families/embeddings/declaration.py` projection/vector pieces | Embedding sidecar/vector cache | Quire vector cache plus Propstore entity policy | Delete projection/vector duplication |
| `propstore/families/claims/sidecar_runtime.py` | Claim embedding/relation runtime over raw sidecar connection | Claim runtime over Quire session/vector APIs | Replace raw derived-store connection usage for embedding paths |
| `propstore/families/concepts/sidecar_runtime.py` | Concept embedding runtime over raw sidecar connection | Concept runtime over Quire session/vector APIs | Replace raw derived-store connection usage for embedding paths |

## Deletion Targets

Delete these old production surfaces first, then use import/type/test failures
as the work queue:

- `GROUNDED_FACT_PROJECTION`;
- `GROUNDED_FACT_EMPTY_PREDICATE_PROJECTION`;
- `GROUNDED_BUNDLE_INPUT_PROJECTION`;
- rule projection tables based on Quire `ProjectionTable`;
- raw grounded-fact and bundle-input row classes;
- raw grounded bundle read/write helpers;
- `CALIBRATION_COUNTS_PROJECTION`;
- calibration projection table declarations;
- raw calibration count SQL/table-missing reads;
- `EMBEDDING_MODEL_PROJECTION`;
- `CLAIM_EMBEDDING_STATUS_PROJECTION`;
- `CONCEPT_EMBEDDING_STATUS_PROJECTION`;
- `CONCEPT_VEC_PROJECTION`;
- embedding projection declarations using `ProjectionTable`;
- embedding vector declarations using `VecProjection`;
- raw embedding table setup;
- raw embedding registry, entity store, vector search, and snapshot store
  implementations;
- row-shaped claim/concept similarity runtime helpers, including
  `SidecarClaimRelationStore`, `find_similar_claim_rows`, and
  `find_similar_concept_rows`;
- generic similarity result `from_mapping` constructors in
  `propstore/core/store_results.py`;
- direct sidecar opening in embedding extraction and restoration.

## Helper Classification: Grounding And Rules

File: `propstore/families/rules/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `GroundedFactProjectionRow` | delete | Replace with `GroundedFact` model. |
| `GroundedFactEmptyPredicateProjectionRow` | delete | Replace with typed `GroundedEmptyPredicate` model. |
| `GroundedBundleInputProjectionRow` | delete | Replace with `GroundedBundleInput` model. |
| `create_grounded_fact_table` | delete | Quire charter creates tables. |
| `populate_grounded_facts` | replace | Replace with model construction/session writes while preserving four-valued bundle semantics. |
| `_persist_bundle_inputs` | replace | Replace raw row persistence with `GroundedBundleInput` model writes. |
| `_read_bundle_inputs` | replace | Replace raw row reads with `GroundedBundleInput` model queries. |
| `_encode_bundle_input` | keep-boundary | Keep as explicit grounding document/value serialization boundary. |
| `_decode_bundle_input` | keep-boundary | Keep as explicit grounding document/value serialization boundary. |
| `_bundle_input_payload` | keep-boundary | Keep as grounding payload conversion, not DB row helper. |
| `_is_json_value` | keep-boundary | Keep only inside grounding payload serialization. |
| `_encode_gunray_atom` | keep-boundary | Keep as Gunray payload serialization boundary. |
| `_decode_gunray_atom` | keep-boundary | Keep as Gunray payload serialization boundary. |
| `_encode_gunray_rule` | keep-boundary | Keep as Gunray payload serialization boundary. |
| `_decode_gunray_rule` | keep-boundary | Keep as Gunray payload serialization boundary. |
| `_rule_key` | keep-boundary | Keep as deterministic grounding ordering helper. |
| `read_grounded_facts` | replace | Replace raw SQL read with typed model query and bundle assembly. |
| `read_grounded_bundle` | replace | Replace raw SQL read with typed model query and bundle assembly. |
| `build_runtime_grounded_bundle` | keep-boundary | Keep semantic bundle assembly API; internally use typed model queries. |
| `_read_source_rules` | replace | Replace raw row read with `GroundedBundleInput` query plus payload decoder. |
| `_read_source_superiority` | replace | Replace raw row read with `GroundedBundleInput` query plus payload decoder. |
| `_read_source_facts` | replace | Replace raw row read with `GroundedBundleInput` query plus payload decoder. |

## Helper Classification: Calibration

File: `propstore/families/calibration/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `CalibrationCountsProjectionRow` | delete | Replace with `CalibrationCount` model. |
| `load_calibration_counts` | replace | Replace raw SQL/table-missing behavior with typed optional query over `CalibrationCount`. |

## Helper Classification: Embeddings

File: `propstore/families/embeddings/declaration.py`.

| Helper | Classification | Required final owner/action |
| --- | --- | --- |
| `_require_sqlite_vec` | move | Move extension loading policy to Quire vector backend. |
| `load_vec_extension` | move | Move extension loading policy to Quire vector backend. |
| `EmbeddingSnapshot` | keep-boundary | Keep as Propstore embedding snapshot value object. |
| `EmbeddingSnapshotReport` | keep-boundary | Keep as Propstore embedding snapshot report value object. |
| `ensure_embedding_tables` | delete | Quire vector/charter machinery creates tables. |
| `SidecarEmbeddingRegistry` | replace | Replace with Quire vector registry/session API. |
| `_SidecarEntityEmbeddingStore` | replace | Replace with Quire vector entity store over SQLAlchemy session. |
| `SidecarClaimEmbeddingStore` | delete | Replace with generic Quire vector cache/entity APIs parameterized by family metadata. Do not keep a claim-specific embedding adapter. |
| `SidecarConceptEmbeddingStore` | delete | Replace with generic Quire vector cache/entity APIs parameterized by family metadata. Do not keep a concept-specific embedding adapter. |
| `SidecarEmbeddingSnapshotStore` | replace | Replace with Quire vector snapshot store plus Propstore snapshot report mapping. |
| `get_registered_models` | replace | Replace with Quire vector registry query. |
| `embed_claims` | replace | Keep workflow API, but route through Quire vector/session APIs. |
| `embed_concepts` | replace | Keep workflow API, but route through Quire vector/session APIs. |
| `find_similar` | replace | Replace raw vector SQL with Quire vector query API. |
| `find_similar_concepts` | replace | Replace raw vector SQL with Quire vector query API. |
| `find_similar_agree` | replace | Replace raw vector SQL with Quire vector query API. |
| `find_similar_disagree` | replace | Replace raw vector SQL with Quire vector query API. |
| `find_similar_concepts_agree` | replace | Replace raw vector SQL with Quire vector query API. |
| `find_similar_concepts_disagree` | replace | Replace raw vector SQL with Quire vector query API. |
| `extract_embeddings` | replace | Replace raw snapshot extraction with Quire vector snapshot API. |
| `extract_embedding_snapshot_from_store` | replace | Replace raw sidecar opening with Quire vector snapshot API. |
| `restore_embeddings` | replace | Replace raw restore with Quire vector snapshot API. |
| `restore_embedding_snapshot` | replace | Replace raw sidecar opening with Quire vector snapshot API. |

Files: `propstore/families/claims/sidecar_runtime.py`,
`propstore/families/concepts/sidecar_runtime.py`, and
`propstore/core/store_results.py`.

| Helper/surface | Classification | Required final owner/action |
| --- | --- | --- |
| `SidecarClaimRelationStore` | delete | Replace raw sidecar relation/vector access with claim owner APIs over Quire sessions/vector APIs. |
| `find_similar_claim_rows` | delete | Replace row-shaped claim similarity API with typed claim similarity query over Quire vector/session APIs. |
| `find_similar_concept_rows` | delete | Replace row-shaped concept similarity API with typed concept similarity query over Quire vector/session APIs. |
| `ConceptSearchHit.from_mapping` | replace | Rename to a boundary-specific constructor such as `from_json_payload` or construct directly from typed query results. |
| `ClaimSimilarityHit.from_mapping` | replace | Rename to a boundary-specific constructor such as `from_json_payload` or construct directly from typed query results. |
| `ConceptSimilarityHit.from_mapping` | replace | Rename to a boundary-specific constructor such as `from_json_payload` or construct directly from typed query results. |

## Caller And Update Surfaces

Update every caller that imports or consumes rule, calibration, embedding,
raw SQLite, or vector projection helpers:

- `propstore/grounding/inspection.py`;
- `propstore/grounding/loading.py`;
- `propstore/families/claims/sidecar_runtime.py`;
- `propstore/families/concepts/sidecar_runtime.py`;
- `propstore/app/claims.py`;
- `propstore/app/concepts/embedding.py`;
- `propstore/app/grounding.py`;
- `propstore/world/model.py`;
- `propstore/fragility_contributors.py`.

Required caller final state:

- grounding inspection/loading reads grounded facts and bundle inputs through
  typed owner APIs or Quire sessions;
- claim and concept embedding runtimes use Quire vector/session APIs;
- app embedding workflows keep workflow/presentation ownership and call the
  owner-layer runtime API;
- world and fragility callers consume typed grounded bundle, calibration, and
  embedding results without importing projection declarations;
- embedding restore diagnostics write through the typed diagnostic service
  owned by `05-source-and-diagnostics.md`.

## Semantic Boundaries

Preserve these Propstore-owned behaviors:

- grounded-rule bundle semantics;
- four-valued grounded fact sections;
- deterministic bundle input persistence and ordering;
- Gunray payload serialization;
- calibration count meaning;
- embedding model identity;
- embedding snapshot and restore report semantics;
- claim and concept embedding text source policy;
- embedding entity resolution policy in claim and concept owners.

Generic table creation, vector extension loading, vector table setup, raw SQL
selection, raw SQL vector search, row coercion, and projection declaration
behavior moves to Quire charter/session/vector machinery or disappears.

## Slice Order

Execute in this order:

1. Grounding/rules charter and projection deletion.
2. Grounding caller migration.
3. Calibration charter and query cutover.
4. Embedding vector backend handoff to Quire APIs.
5. Claim and concept embedding runtime migration.
6. Data parity, vector parity, search gates, and completion gates.

## Execution Loop

1. Read the inventory rows in this file and the current family files.
2. List all current production callers from the caller/update surface above.
3. Name the target models and Quire vector APIs in the implementation notes or
   commit message.
4. Delete the old grounding, calibration, and embedding projection/read-model
   surfaces first.
5. Run the smallest import/type/test command that exposes the next failures.
6. Fix only failures caused by this slice's deletion and named caller list.
7. Replace raw SQLite access with Quire SQLAlchemy session/model access.
8. Replace raw vector SQL with Quire vector query/snapshot APIs.
9. Replace loose dict/list/row payloads with typed grounding, calibration, and
   embedding model objects.
10. Delete field-specific row/vector/table helpers once generic charter and
    vector conversion covers the field.
11. Run the family gates.
12. Run the old-path search gates.
13. Run the data-parity and vector-parity gates.

Implementation starts only after Quire SQLAlchemy charter, JSON, catalog,
session, FTS, and vector capabilities are complete.

## Data-Parity Gate

This gate includes the metric/vector comparisons required by this phase.

```powershell
uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --before reports/sqlalchemy-charter-parity/rules-grounding-calibration-embeddings/before.sqlite --build-after sqlalchemy-charter --after reports/sqlalchemy-charter-parity/rules-grounding-calibration-embeddings/after.sqlite --owner rules-grounding-calibration-embeddings --workstream workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/11-rules-grounding-calibration-embeddings.md --out reports/sqlalchemy-charter-parity/rules-grounding-calibration-embeddings.json
uv run scripts/compare_sqlalchemy_charter_parity.py --knowledge-dir . --before reports/sqlalchemy-charter-parity/rules-grounding-calibration-embeddings/before.sqlite --build-after sqlalchemy-charter --after reports/sqlalchemy-charter-parity/rules-grounding-calibration-embeddings/after.sqlite --owner rules-grounding-calibration-embeddings --workstream workstreams/quire-sqlalchemy-charter-cutover-2026-05-18/11-rules-grounding-calibration-embeddings.md --out reports/sqlalchemy-charter-parity/rules-grounding-calibration-embeddings-vector.json --require-vector claim-similarity --require-vector concept-similarity --require-vector claim-agree-disagree --require-vector concept-agree-disagree --require-vector embedding-snapshot-restore
```

Compare the captured projection baseline against the charter-generated sidecar
for this slice and compare:

- grounded fact, grounded empty predicate, and grounded bundle input table
  names, primary keys, row counts, and key sets;
- grounded bundle outputs for typed grounded-fact model queries, typed grounded
  bundle assembly, and `build_runtime_grounded_bundle` over the fixtures exercised by
  `tests/test_sidecar_grounded_facts.py` and `tests/test_world_query.py`;
- four-valued grounded fact section contents;
- deterministic bundle input ordering;
- calibration count table names, primary keys, row counts, key sets, and
  optional-query results;
- embedding model and embedding status table names, primary keys, row counts,
  and key sets;
- claim and concept embedding source coverage;
- registered embedding model results;
- vector nearest-neighbor hit sets for claim and concept similarity queries;
- agree/disagree vector query hit sets;
- embedding snapshot extraction and restore report results;
- embedding restore diagnostic results through the typed diagnostic service.

The phase fails when a row, key, diagnostic, vector hit, embedding source
entity, grounded bundle result, calibration result, or semantic query result
disappears.

Accepted parity difference allowlist:

- deleted table constants, projection rows, vector declarations, and helper
  paths named in this file's deletion targets;
- no column rename, table rename, row disappearance, key disappearance,
  diagnostic disappearance, vector-hit disappearance, embedding-source-entity
  disappearance, grounded-bundle-result disappearance, calibration-result
  disappearance, or semantic-query disappearance is allowed.

## Required Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label derived-support-charter tests/test_world_query.py tests/test_opinion_schema.py tests/test_fixture_schema_parity.py tests/test_required_schema_completeness.py
rg -n -F -- "GROUNDED_FACT_PROJECTION" propstore tests
rg -n -F -- "GROUNDED_FACT_EMPTY_PREDICATE_PROJECTION" propstore tests
rg -n -F -- "GROUNDED_BUNDLE_INPUT_PROJECTION" propstore tests
rg -n -F -- "CALIBRATION_COUNTS_PROJECTION" propstore tests
rg -n -F -- "EMBEDDING_MODEL_PROJECTION" propstore tests
rg -n -F -- "CLAIM_EMBEDDING_STATUS_PROJECTION" propstore tests
rg -n -F -- "CONCEPT_EMBEDDING_STATUS_PROJECTION" propstore tests
rg -n -F -- "CONCEPT_VEC_PROJECTION" propstore tests
rg -n -F -- "GroundedFactProjectionRow" propstore tests
rg -n -F -- "GroundedFactEmptyPredicateProjectionRow" propstore tests
rg -n -F -- "GroundedBundleInputProjectionRow" propstore tests
rg -n -F -- "CalibrationCountsProjectionRow" propstore tests
rg -n -F -- "create_grounded_fact_table" propstore tests
rg -n -F -- "populate_grounded_facts" propstore tests
rg -n -F -- "_persist_bundle_inputs" propstore tests
rg -n -F -- "_read_bundle_inputs" propstore tests
rg -n -F -- "read_grounded_facts" propstore tests
rg -n -F -- "read_grounded_bundle" propstore tests
rg -n -F -- "load_calibration_counts" propstore tests
rg -n -F -- "ensure_embedding_tables" propstore tests
rg -n -F -- "SidecarEmbeddingRegistry" propstore tests
rg -n -F -- "_SidecarEntityEmbeddingStore" propstore tests
rg -n -F -- "SidecarClaimEmbeddingStore" propstore tests
rg -n -F -- "SidecarConceptEmbeddingStore" propstore tests
rg -n -F -- "SidecarEmbeddingSnapshotStore" propstore tests
rg -n -F -- "SidecarClaimRelationStore" propstore tests
rg -n -F -- "find_similar_claim_rows" propstore tests
rg -n -F -- "find_similar_concept_rows" propstore tests
rg -n -F -- "from_mapping" propstore/core/store_results.py tests
rg -n -F -- "connect_sqlite_store" propstore/families/claims/sidecar_runtime.py propstore/families/concepts/sidecar_runtime.py tests
rg -n -F -- "connect_sqlite_store_readonly" propstore/families/claims/sidecar_runtime.py propstore/families/concepts/sidecar_runtime.py tests
rg -n -F -- "sqlite3.Connection" propstore/families/claims/sidecar_runtime.py propstore/families/concepts/sidecar_runtime.py tests
rg -n -F -- "row_factory" propstore/families/claims/sidecar_runtime.py propstore/families/concepts/sidecar_runtime.py tests
rg -n -F -- "VecProjection" propstore/families/embeddings tests
rg -n -F -- "ProjectionTable(" propstore/families/rules propstore/families/calibration propstore/families/embeddings tests
rg -n -F -- "sqlite3.Connection" propstore/families/rules propstore/families/calibration propstore/families/embeddings propstore/grounding tests
```

All searches are zero-hit gates outside notes, workstreams, docs, and reports.

## Completion Criteria

This slice is complete only when:

- the grounding charter declares `GroundedFact`, `GroundedEmptyPredicate`, and
  `GroundedBundleInput`;
- grounded fact and bundle input writes use typed model objects through a Quire
  SQLAlchemy session;
- grounded bundle reads use typed model queries and preserve bundle semantics;
- the calibration charter declares `CalibrationCount`;
- calibration reads use typed optional queries over `CalibrationCount`;
- embedding registry, status, vector search, and snapshot/restore use Quire
  vector/session APIs;
- embedding model identity, text source policy, entity resolution policy, and
  snapshot report semantics stay in Propstore owners;
- every named caller/update surface no longer imports rule, calibration, or
  embedding projection rows, table constants, raw SQLite selectors, or vector
  projection declarations;
- the data-parity and vector-parity gates pass;
- all required tests pass through the logged pytest wrapper;
- all old-path search gates above are zero-hit outside notes, workstreams,
  docs, and reports.
