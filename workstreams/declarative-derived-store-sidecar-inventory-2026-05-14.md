# Declarative Derived Store Sidecar Inventory

## Scope

This is Phase 1 of
`workstreams/declarative-derived-store-zero-custom-tables-workstream-2026-05-14.md`.

The goal of this document is to inventory every current physical sidecar table
and virtual table before implementation work begins. Unknown table splits are
treated as load-bearing until a later phase proves otherwise.

## Gate Result

Phase 1 gate status: passed.

Every required current table is classified below as `derive from contract`,
`keep as generated physical table`, or `delete candidate after proof`. There
are no `unknown` classifications. `delete candidate after proof` does not
authorize deletion in this phase; it means the table remains generated from a
contract until a later phase proves the replacement and deletes the old
surface.

## Current Common Inputs

All current sidecar schema material participates in the sidecar cache hash
through `propstore.sidecar.build._sidecar_content_hash`, which includes:

- source commit
- `propstore.sidecar.schema.SCHEMA_VERSION`
- semantic pass versions
- generated schema digest
- family contract versions
- selected dependency pins
- `PROPSTORE_SIDECAR_CACHE_BUST`

The declarative projection contract must replace hand-authored schema material
as the schema-hash input. It must not silently remove any of the existing hash
inputs.

## Consumer Buckets

The table inventory uses these reader buckets:

- `WorldQuery`: `propstore/world/model.py`
- `Embeddings`: `propstore/sidecar/embedding_store.py` and embedding app code
- `SourceStatus`: `propstore/source/status.py`
- `SourcePromote`: `propstore/source/promote.py`
- `SidecarQuery`: `propstore/sidecar/query.py`
- `Grounding`: `propstore/sidecar/rules.py`
- `Tests`: table-shape assertions in `tests/test_build_sidecar.py`,
  `tests/test_world_query.py`, `tests/test_form_algebra.py`,
  `tests/test_sidecar_grounded_facts.py`, render-policy tests, and remediation
  tests under `tests/remediation/phase_*`

## Inventory

| Table | Kind | Owner | Source Families | Writers | Readers | Invariants and Cross-Table Assumptions | Table-Shape Tests | Category | Classification |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `meta` | ordinary table | sidecar schema/version | projection contract | `write_schema_metadata` | `WorldQuery._validate_schema` | one metadata row for `SIDECAR_META_KEY`; schema version must equal current projection version | `tests/test_build_sidecar.py`, world schema tests | derived metadata | derive from contract |
| `source` | ordinary table | source projection | sources | `populate_sources` from `SourceSidecarRows` | `WorldQuery._claim_select_sql`, concept/source apps, tests | `slug` primary key; joined by `claim_core.source_slug`; trust fields remain JSON text | build-sidecar source tests, render fixtures | semantic source index | derive from contract |
| `concept` | ordinary table | concept projection | concepts, forms | `populate_concept_sidecar_rows` | `WorldQuery`, concept apps, embeddings, FTS population, graph tests | `id` primary key; `seq` stable for vector rowids; logical id and form fields required by registry/query paths | concept, graph, CLI, embedding tests | semantic entity index | derive from contract |
| `alias` | ordinary table | concept projection | concepts | `populate_concept_sidecar_rows` | concept search, embeddings | FK to `concept.id`; aliases aggregate into concept embedding/FTS text | concept FTS/search tests | search support | derive from contract |
| `relationship` | ordinary table | concept projection | concepts | `populate_concept_sidecar_rows` | direct tests; some legacy concept relationship assertions | FK from source/target concepts; currently overlaps with concept rows in `relation_edge` | `tests/test_build_sidecar.py` relationship tests | relation index | delete candidate after proof; derive until proven redundant |
| `relation_edge` | ordinary table | relation projection | concepts, stances, merge/resolution outputs | `populate_concept_sidecar_rows`, `populate_stances`, source promote/status helpers in related paths | `WorldQuery.all_relationships`, stances, render policy, graph tests, opinion tests | polymorphic source/target; claim stances require claim-core joins; opinion columns enforce subjective-logic checks | opinion, render-policy, world-query, graph tests | shared relation index | derive from contract |
| `parameterization` | ordinary table | concept/form projection | concepts, forms | `populate_concept_sidecar_rows` | `WorldQuery.all_parameterizations`, derivation/resolution paths | `output_concept_id` references concept; `conditions_ir` required by query logic | `tests/test_form_algebra.py`, world query tests | derived concept algebra | derive from contract |
| `parameterization_group` | ordinary table | concept projection | concepts | `populate_concept_sidecar_rows` | `WorldQuery.concept_ids_for_group`, group lookup tests | group membership by concept; used for parameterization grouping queries | build-sidecar parameterization group tests | derived grouping | derive from contract |
| `form` | ordinary table | form projection | forms | `populate_concept_sidecar_rows` | form algebra queries, WorldQuery stats/forms | `name` primary key; dimensions JSON and `is_dimensionless` are load-bearing | `tests/test_form_algebra.py` | semantic form index | derive from contract |
| `form_algebra` | ordinary table | form/concept projection | concepts, forms | `populate_concept_sidecar_rows` | form algebra queries | derived from parameterizations; source concept/formula remain inspectable | `tests/test_form_algebra.py` | derived form algebra | derive from contract |
| `concept_fts` | FTS5 virtual table | concept search projection | concepts, aliases, relationships | `populate_concept_sidecar_rows` custom FTS DDL and inserts | concept search app, `WorldQuery.search`, raw sidecar query tests | search by canonical name, alias, definition, conditions; no custom DDL in final state | CLI/search/build-sidecar FTS tests | search index | keep as generated physical FTS table |
| `context` | ordinary table | context projection | contexts | `populate_contexts` | `WorldQuery._load_lifting_system`, context tests, micropub FK | `id` primary key; context ids bind assumptions, lifting rules, micropublications | context and lifting tests | semantic context index | derive from contract |
| `context_assumption` | ordinary table | context projection | contexts | `populate_contexts` | `WorldQuery._load_lifting_system` | ordered assumptions by `seq`; FK to context | context tests | semantic context support | derive from contract |
| `context_lifting_rule` | ordinary table | context projection | contexts | `populate_contexts` after invalid-row filter | `WorldQuery._load_lifting_system`, lifting tests | source/target context FKs; invalid rows must quarantine rather than corrupt load | context lifting remediation tests | semantic lifting index | derive from contract |
| `context_lifting_materialization` | ordinary table | context lifting projection | contexts, authored ist assertions | `populate_contexts` | context lifting materialization tests | preserves lifted assertion status, exception id, provenance JSON | context lifting tests | derived lifting materialization | derive from contract |
| `claim_core` | ordinary table | claim projection | claims, sources, contexts | `populate_claims`, raw-id quarantine, source promotion blocked mirror | `WorldQuery`, render policy, SourceStatus, SourcePromote, embeddings, many tests | `id` primary key; `seq` stable for vectors; `build_status`, `stage`, `promotion_status` are orthogonal and load-bearing | build-sidecar, render-policy, source promotion, world-query tests | semantic claim core index | derive from contract |
| `claim_concept_link` | ordinary table | claim projection | claims, concepts | `populate_claims`, fixtures | `WorldQuery._claim_rows`, graph/build tests, embeddings | composite key; FK to claim/concept; role and ordinal preserve concept-link contract | build-sidecar, graph, world-query tests | semantic claim relation index | derive from contract |
| `claim_numeric_payload` | ordinary table | claim projection | claims, forms | `insert_claim_row`, raw fixtures | `WorldQuery._claim_select_sql`, embedding/text not direct, numeric reasoning | one row per claim; SI-normalized values are load-bearing | build-sidecar numeric/SI tests, graph/world tests | semantic numeric payload | derive from contract |
| `claim_text_payload` | ordinary table | claim projection | claims | `insert_claim_row`, raw fixtures | `WorldQuery._claim_select_sql`, claim FTS, embeddings | condition CEL/IR, statement/expression/sympy text, notes, summaries; one row per claim | claim notes, build-sidecar, embedding tests | semantic text payload/search source | derive from contract |
| `claim_algorithm_payload` | ordinary table | claim projection | claims | `insert_claim_row`, raw fixtures | `WorldQuery._claim_select_sql`, algorithm tests | `algorithm_stage` distinct from `claim_core.stage`; canonical AST/body load-bearing | algorithm claim tests | semantic algorithm payload | derive from contract |
| `claim_fts` | FTS5 virtual table | claim search projection | claims | `populate_claim_fts_rows` | raw SQL tests, future search consumers | search statement, conditions, expression; final DDL generated by FTS contract | build-sidecar FTS tests | search index | keep as generated physical FTS table |
| `conflict_witness` | ordinary table | conflict projection | claims, concepts, conflict detector | `populate_conflicts` | `WorldQuery.conflicts`, stats, graph tests | records warning class and witness pair; conflict rows are derived and inspectable | conflict tests, build stats tests | derived diagnostic/reasoning index | derive from contract |
| `justification` | ordinary table | justification projection | justifications, claims | `populate_authored_justifications` | `WorldQuery.all_authored_justifications`, source relation tests | premise list JSON must decode to list; rule strength default preserved | source relation and render tests | semantic reasoning index | derive from contract |
| `calibration_counts` | ordinary table | calibration/relation projection | relation calibration flows | current schema only; populated by related workflows when present | relation/opinion paths as available | composite key `(pass_number, category)` | opinion/calibration-adjacent tests if present | derived calibration support | derive from contract |
| `build_diagnostics` | ordinary table | diagnostic projection | all semantic build paths | quarantine writer, build exception recorder, promotion mirror | `WorldQuery.build_diagnostics`, SourceStatus, tests | stores row- or source-scoped diagnostics; `blocking` controls render policy | remediation phase 1/2/7 tests, render-policy tests | diagnostic index | derive from contract |
| `micropublication` | ordinary table | micropublication projection | micropubs, contexts, sources | `populate_micropublications` | `WorldQuery.all_micropublications` | id derived from canonical payload; first-writer dedupe is current behavior | micropublication and duplicate remediation tests | semantic micropub index | derive from contract |
| `micropublication_claim` | ordinary table | micropublication projection | micropubs, claims | `populate_micropublications` | `WorldQuery.all_micropublications` | composite key; ordered claim links by `seq`; FK to micropub and claim | micropublication tests | semantic micropub link index | derive from contract |
| `grounded_fact` | ordinary table | grounding projection | rules, predicates, facts | `populate_grounded_facts` | `read_grounded_facts`, `read_grounded_bundle`, WorldQuery grounding | composite key enforces set semantics per section; duplicates raise | `tests/test_sidecar_grounded_facts.py` | grounded reasoning materialization | derive from contract |
| `grounded_fact_empty_predicate` | ordinary table | grounding projection | rules, predicates, facts | `populate_grounded_facts` | `read_grounded_facts` | preserves empty predicate presence separately from zero rows | sidecar grounded facts tests | grounded reasoning materialization | derive from contract |
| `grounded_bundle_input` | ordinary table | grounding projection | rules, superiority, facts, arguments | `_persist_bundle_inputs` | `read_grounded_bundle` | payload BLOB is deterministic JSON bytes; required to verify stored grounding | grounding loading/tests | grounding rehydration support | derive from contract |
| `embedding_model` | ordinary table | embedding projection/cache | embedding model identities | `ensure_embedding_tables`, embedding stores | embedding registry/snapshot | model identity primary key; dimensions drive vec table DDL | embedding tests | vector metadata/cache | derive from contract or separate embedding derived store |
| `embedding_status` | ordinary table | embedding projection/cache | claims, embedding model identities | claim embedding store | embedding restore/search | composite key by model and claim; content hash detects stale vectors | embedding tests | vector status/cache | derive from contract or separate embedding derived store |
| `concept_embedding_status` | ordinary table | embedding projection/cache | concepts, embedding model identities | concept embedding store | embedding restore/search | composite key by model and concept; content hash detects stale vectors | embedding tests | vector status/cache | derive from contract or separate embedding derived store |
| `claim_vec_{model_identity_hash}` | sqlite-vec virtual table | embedding projection/cache | claims, embedding vectors | claim embedding store dynamic DDL | claim similarity search | rowid is claim `seq`; dimensions from embedding model; dynamic table name | sqlite-vec/embedding tests | vector index | keep as generated physical vec table or move to separate embedding store |
| `concept_vec_{model_identity_hash}` | sqlite-vec virtual table | embedding projection/cache | concepts, embedding vectors | concept embedding store dynamic DDL | concept similarity search | rowid is concept `seq`; dimensions from embedding model; dynamic table name | sqlite-vec/embedding tests | vector index | keep as generated physical vec table or move to separate embedding store |

## Load-Bearing Table Splits

These splits must not be collapsed in this workstream without a later proof:

- `claim_core` vs `claim_numeric_payload` vs `claim_text_payload` vs
  `claim_algorithm_payload`. Numeric SI data, text/condition/sympy data, and
  algorithm AST/stage data have distinct semantics and consumers.
- `claim_core.stage` vs `claim_algorithm_payload.algorithm_stage`. These are
  different lifecycle axes.
- `build_diagnostics` separate from semantic rows. Render policy relies on
  opt-in diagnostics without dropping quarantined rows.
- `grounded_fact` vs `grounded_fact_empty_predicate`. Empty predicate presence
  is semantically distinct from absence.
- embedding status tables vs dynamic vec tables. Status rows track content
  freshness; vec tables store model-specific vectors.

## Deletion Candidates Requiring Later Proof

These are not deleted by this inventory:

- `relationship` may be redundant with concept `relation_edge` rows, but tests
  still assert the table directly. It remains generated until a later phase
  proves replacement and deletes direct readers/tests.
- embedding tables may belong in a separate derived embedding store rather than
  the world projection. Phase 14 decides this after the sqlite-vec runtime
  spike.

## Phase 1 Follow-Up Work

Phase 2 must answer the SQLite runtime questions before any derived-store
abstraction is implemented. Phase 3 may begin only because this inventory has no
`unknown` classifications; if later evidence contradicts a classification, the
inventory must be updated and committed before implementation proceeds.
