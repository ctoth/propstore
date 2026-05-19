# Quire SQLAlchemy Charter Cutover: Rules, Grounding, Calibration, And Embeddings

Date: 2026-05-18

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

Diagnostics projection cleanup is owned by
`05-source-and-diagnostics.md`. This workstream depends on the typed
`BuildDiagnostic` service already existing for embedding restore diagnostics
and does not re-own diagnostics table deletion.

## Prerequisites

Complete these cutover workstreams before this slice starts:

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
- embedding projection declarations using `ProjectionTable`;
- embedding vector declarations using `VecProjection`;
- raw embedding table setup;
- raw embedding registry, entity store, vector search, and snapshot store
  implementations;
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
| `SidecarClaimEmbeddingStore` | replace | Replace with claim-specific adapter over Quire vector entity store. |
| `SidecarConceptEmbeddingStore` | replace | Replace with concept-specific adapter over Quire vector entity store. |
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

## Data-Parity And Metric Gates

```powershell
uv run scripts/compare_sqlalchemy_charter_parity.py --before <old-sidecar.sqlite> --after <new-sidecar.sqlite> --owner rules-grounding-calibration-embeddings --out reports/sqlalchemy-charter-parity/rules-grounding-calibration-embeddings.json
```

Build the sidecar from the same repository snapshot before and after this
slice and compare:

- grounded fact, grounded empty predicate, and grounded bundle input table
  names, primary keys, row counts, and key sets;
- representative grounded bundle assembly results;
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
disappears. The only accepted disappearances are the table constants,
projection rows, vector declarations, and helper paths named as deletion
targets in this file. Accepted column/table renames must be listed in the
implementation closure report or commit message.

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
