# Declarative Derived Store Zero-Custom-Tables Workstream

## Goal

Replace Propstore's hand-authored sidecar table layer with declarative semantic
projection contracts materialized through a Quire-owned derived-store lifecycle.

The target state is precisely zero custom sidecar tables in production code:

- no bespoke `CREATE TABLE` or `CREATE VIRTUAL TABLE` strings for the Propstore
  world sidecar
- no positional `INSERT` tuples
- no `*InsertRow(values=...)` wrappers
- no separately maintained WorldQuery required-schema table
- no production `Repository.sidecar_path`
- no normal workflow where callers choose a sidecar output path

This does not mean zero physical SQLite tables. SQLite remains the backing store
for the derived world projection, including FTS5 and sqlite-vec virtual tables
where required. The difference is that every physical table, virtual table,
index, inserter, decoder, validator, and schema-hash input is generated from one
declarative projection contract.

The target architecture is:

- Quire owns generic derived-store lifecycle: commit binding, cache identity,
  cache root, atomic publish, locking, cleanup, opening, and GC.
- Propstore owns semantic projection contracts: row meaning, table relationships,
  FTS sources, vector sources, diagnostics, render-policy columns, grounding
  persistence, and world-query semantics.
- WorldQuery consumes a materialized derived-store handle, not a repository-local
  path.
- CLI/app layers adapt typed requests and reports; they do not own sidecar
  schema or build policy.

## Non-Goals

Do not move Propstore semantics into Quire:

- claim/concept/context/source/stance/justification semantics
- lifecycle meanings of `build_status`, `stage`, or `promotion_status`
- quarantine diagnostic kinds or render-policy behavior
- CEL, condition IR, dimensional algebra, grounding, context lifting,
  micropublication, conflict, opinion, or argumentation semantics
- embedding text construction or model identity semantics

Do not collapse load-bearing tables just because they look verbose. In
particular, do not merge claim payload tables unless a dedicated inventory proves
that the split is not semantically or operationally load-bearing.

Do not introduce Pydantic or SQLAlchemy ORM as a replacement architecture. The
projection contract may borrow declarative-table ideas, but the output remains
explicit SQLite because FTS5, sqlite-vec, generated schema hashes, and
sidecar-specific read models are first-class requirements.

Do not keep old and new production paths in parallel. Each phase deletes the old
path for the surface it replaces before repairing callers.

## Definitions

Physical table:

- a real SQLite table or virtual table produced in the derived store.

Custom table:

- a table whose DDL, insert SQL, decoder, validator, or schema hash is
  hand-authored separately from the declarative projection contract.

Projection contract:

- the single source of truth for a table or virtual table. It declares columns,
  types, defaults, primary keys, foreign keys, indexes, JSON encoders, virtual
  table kind, FTS source rules, vec source rules, schema hash contribution, and
  row decoder.

Derived store:

- the materialized SQLite database for a semantic projection at a specific
  repository commit and projection contract version.

## Current Load-Bearing Surfaces

These surfaces must be preserved unless a phase explicitly proves and deletes a
replacement:

- `propstore/sidecar/schema.py` owns the current physical schema.
- `propstore/sidecar/build.py` owns cache hash, build orchestration, atomic
  publish, embedding snapshot/restore, and exception diagnostics.
- `propstore/sidecar/passes.py` lowers checked semantic bundles into sidecar
  rows.
- `propstore/sidecar/stages.py` carries the current row-bundle handoff types.
- `propstore/sidecar/{claims,concepts,sources,micropublications,rules}.py` own
  current insert/read helpers for specific schema regions.
- `propstore/world/model.py` validates schema and reads the sidecar.
- `propstore/core/row_types.py` decodes query rows into runtime row objects.
- source promotion/status code writes and reads blocked sidecar rows.
- embedding code uses sqlite-vec virtual tables and current sidecar rows.
- grounding persists enough input to rehydrate and verify grounded bundles.

## Dependency Order

The phases below are topologically ordered.

1. Inventory and invariants
2. SQLite feature spike
3. Projection metamodel
4. Generated schema validation
5. First production table cut: `source`
6. Low-risk table cuts
7. FTS declaration support
8. Concept/form projection cuts
9. Context and lifting projection cuts
10. Claim and relation projection cuts
11. Diagnostics projection cut
12. Grounding projection cut
13. Micropublication projection cut
14. Embedding and sqlite-vec projection cut
15. Quire derived-store lifecycle
16. Propstore handle cutover
17. Final deletions and gates

## Phase 1: Inventory and Invariants

Repository: `propstore`

Create an inventory document before implementation work.

Target file:

- `workstreams/declarative-derived-store-sidecar-inventory-2026-05-14.md`

For every current physical sidecar table or virtual table, record:

- table name
- physical kind: table, FTS5 virtual table, sqlite-vec virtual table
- semantic owner
- source families
- writer function
- reader functions
- row type or decoded runtime type
- foreign keys and cross-table assumptions
- tests that assert the table shape
- schema-hash input requirements
- whether the table is source, derived, diagnostic, search, vector, or cache
- whether the current table split is known load-bearing, likely accidental, or
  unknown

Required current tables include at least:

- `meta`
- `source`
- `concept`
- `alias`
- `relationship`
- `relation_edge`
- `parameterization`
- `parameterization_group`
- `form`
- `form_algebra`
- `concept_fts`
- `context`
- `context_assumption`
- `context_lifting_rule`
- `context_lifting_materialization`
- `claim_core`
- `claim_concept_link`
- `claim_numeric_payload`
- `claim_text_payload`
- `claim_algorithm_payload`
- `claim_fts`
- `conflict_witness`
- `justification`
- `calibration_counts`
- `build_diagnostics`
- `micropublication`
- `micropublication_claim`
- `grounded_fact`
- `grounded_fact_empty_predicate`
- `grounded_bundle_input`
- `embedding_model`
- `embedding_status`
- `concept_embedding_status`
- dynamic `claim_vec_{model_identity_hash}`
- dynamic `concept_vec_{model_identity_hash}`

Required gate:

- every table above is classified as `keep`, `delete`, or `derive from
  contract`; `unknown` classifications block Phase 3.

## Phase 2: SQLite Feature Spike

Repository: `propstore`

Write focused tests or scripts that establish runtime constraints before
abstracting the store.

Required questions:

- Does read-only URI mode avoid creating `-wal` and `-shm` files for sidecar
  query?
- Does FTS5 require writable setup only at build time?
- Does sqlite-vec require a real filesystem path, or can it work from an
  in-memory or temporary connection?
- Can a fully checkpointed SQLite file be atomically published on Windows
  without leaving stale WAL/SHM siblings?
- Can embedding vector tables be copied/restored from a separate cache database
  without reading a previous sidecar at the same path?

Target tests:

- `tests/test_sidecar_sqlite_runtime_contract.py`
- `tests/test_sidecar_projection_fts_contract.py`
- `tests/test_sidecar_projection_vec_contract.py`

Required gate:

- targeted tests pass through `powershell -File scripts/run_logged_pytest.ps1`
  with a label.

## Phase 3: Projection Metamodel

Repository: `propstore`

Add the Propstore-side projection declaration layer. This phase must not change
existing sidecar behavior.

Candidate module:

- `propstore/sidecar/projection.py`

Candidate concepts:

```python
ProjectionSchema
ProjectionTable
ProjectionColumn
ProjectionIndex
ProjectionForeignKey
ProjectionRow
ProjectionEncoder
ProjectionDecoder
FtsProjection
VecProjection
SemanticProjection
```

Required capabilities:

- declare ordinary SQLite tables
- declare composite primary keys
- declare nullable and non-null columns
- declare defaults and checks
- declare foreign keys
- declare indexes
- declare JSON/text/blob codecs
- declare FTS5 virtual tables
- declare sqlite-vec virtual tables with dynamic table names
- generate deterministic DDL
- generate named `INSERT` statements
- validate required schema from the same contract
- compute deterministic schema-hash material
- decode SQLite rows to typed runtime row objects or declared projection rows

Prohibited:

- no table-specific SQL strings outside tests
- no positional insert tuples in new code
- no dependency on Pydantic or SQLAlchemy ORM

Required gates:

- unit tests for DDL generation
- unit tests for named inserts
- unit tests for schema validation
- unit tests for row decoding
- `uv run pyright propstore`

## Phase 4: Generated Schema Validation

Repository: `propstore`

Move schema validation out of `propstore/world/model.py` and into the projection
contract.

Deletion-first step:

- delete `_REQUIRED_SCHEMA` as the source of truth from `WorldQuery`

Replacement:

- `WorldQuery` asks the Propstore world projection contract to validate the
  opened derived store.

Required behavior:

- same error quality for missing meta row, schema version mismatch, missing
  table, and missing column
- no duplicated hard-coded required-column sets

Required gates:

- existing world schema tests still pass
- search gate: no `_REQUIRED_SCHEMA` production definition remains

## Phase 5: First Production Table Cut: `source`

Repository: `propstore`

Convert `source` first because it is isolated and lower risk.

Deletion-first step:

- delete `SourceInsertRow(values=...)` and `SourceSidecarRows` as production
  row wrappers for `source`

Replacement:

- declare `SourceProjectionRow`
- generate `source` DDL
- generate named insert
- decode source rows through the projection contract where needed

Required behavior:

- `source.slug` remains primary key
- source trust fields round-trip unchanged
- `artifact_code` remains available

Required gates:

- targeted sidecar source tests
- `tests/test_build_sidecar.py` source-related cases
- schema hash changes only if the generated contract intentionally changes the
  canonical schema material

## Phase 6: Low-Risk Table Cuts

Repository: `propstore`

Convert simple tables one family at a time.

Order:

1. `form`
2. `form_algebra`
3. `alias`
4. `parameterization_group`
5. `calibration_counts`

For each table:

- delete old insert wrapper
- delete old hand-authored DDL for that table
- replace with projection contract
- update populator to emit named rows
- verify row equivalence
- commit before moving to the next table

Required gates per table:

- targeted tests for the table
- `uv run pyright propstore`

## Phase 7: FTS Declaration Support

Repository: `propstore`

Add declarative FTS support before converting concept or claim FTS.

Required FTS contract shape:

```python
FtsProjection(
    table="concept_fts",
    key_column="concept_id",
    columns=(...),
    source_query=...,
)
```

The contract must generate:

- `CREATE VIRTUAL TABLE ... USING fts5(...)`
- deterministic population query or row-generation plan
- search column validation

Required FTS invariants:

- generated FTS DDL is deterministic
- FTS population is deterministic
- concept search by canonical name, alias, definition, and condition remains
  unchanged
- claim search by statement, condition, and expression remains unchanged

Required gates:

- `tests/test_cli.py` sidecar query/search cases
- `tests/test_build_sidecar.py` FTS cases
- `tests/test_sidecar_query_read_only.py`

## Phase 8: Concept/Form Projection Cuts

Repository: `propstore`

Convert concept-related tables.

Tables:

- `concept`
- `parameterization`
- concept `relation_edge` rows
- `concept_fts`

Decision point:

- use `relation_edge` as the canonical concept relation read surface if the
  inventory proves `relationship` is redundant
- otherwise keep both as declared projections until a separate deletion phase
  proves one can be removed

Deletion-first requirements:

- delete `ConceptInsertRow(values=...)`
- delete `ConceptParameterizationInsertRow(values=...)`
- delete `ConceptFtsInsertRow(values=...)`
- delete hand-authored concept DDL
- delete custom concept FTS DDL

Required gates:

- concept sidecar tests
- concept search tests
- form algebra tests
- graph build/export tests that read concept rows

## Phase 9: Context and Lifting Projection Cuts

Repository: `propstore`

Convert context tables.

Tables:

- `context`
- `context_assumption`
- `context_lifting_rule`
- `context_lifting_materialization`

Preserve:

- context lifting materialization semantics
- invalid lifting-row quarantine behavior
- WorldQuery lifting-system reconstruction

Deletion-first requirements:

- delete context insert tuple wrappers
- delete hand-authored context DDL
- replace `_filter_invalid_context_lifting_rows` inputs with typed projection
  rows or named mappings

Required gates:

- context sidecar tests
- context lifting tests
- world query context tests

## Phase 10: Claim and Relation Projection Cuts

Repository: `propstore`

Convert claim and relation tables without changing their semantics.

Tables:

- `claim_core`
- `claim_concept_link`
- `claim_numeric_payload`
- `claim_text_payload`
- `claim_algorithm_payload`
- claim `relation_edge` rows
- `claim_fts`
- `conflict_witness`
- `justification`

Preserve:

- `build_status`, `stage`, and `promotion_status` as orthogonal columns
- `claim_core.stage` distinct from `claim_algorithm_payload.algorithm_stage`
- source-local branch and promotion-status behavior
- duplicate claim/version diagnostics
- render-policy behavior
- all current `ClaimRow.from_mapping` behavior until the row decoder is
  generated from contract

Deletion-first requirements:

- delete `ClaimInsertRow(values=...)`
- delete `ClaimConceptLinkInsertRow(values=...)`
- delete `ClaimStanceInsertRow(values=...)`
- delete `ClaimFtsInsertRow(values=...)`
- delete `ConflictWitnessInsertRow(values=...)`
- delete `JustificationInsertRow(values=...)`
- delete positional claim insert SQL

Do not collapse payload tables in this phase. A collapse requires a later
workstream with evidence from Phase 1.

Required gates:

- build-sidecar claim tests
- render-policy tests
- source promotion/status tests
- graph build/export tests
- world query tests
- race/atomicity remediation tests touching claim payload rows

## Phase 11: Diagnostics Projection Cut

Repository: `propstore`

Convert `build_diagnostics` to a declared diagnostic projection.

Preserve:

- claim-scoped and source-ref-scoped diagnostics
- severity
- blocking flag
- detail JSON
- build-exception diagnostic behavior
- render-policy opt-in behavior

Deletion-first requirements:

- delete `BuildDiagnosticInsertRow(values=...)`
- delete custom build-diagnostics DDL
- delete custom quarantine insert SQL where replaced by projection writer

Required gates:

- all remediation phase 2 quarantine tests
- render-policy diagnostics tests
- source status diagnostic tests

## Phase 12: Grounding Projection Cut

Repository: `propstore`

Convert grounding tables.

Tables:

- `grounded_fact`
- `grounded_fact_empty_predicate`
- `grounded_bundle_input`

Preserve:

- all four answer sections: `yes`, `no`, `undecided`, `unknown`
- empty-predicate markers
- deterministic row insertion order
- duplicate ground atom failure behavior
- `read_grounded_bundle` verification that persisted facts match grounded
  inputs

Deletion-first requirements:

- delete custom grounding DDL
- replace custom inserts with projection-generated named inserts

Required gates:

- `tests/test_sidecar_grounded_facts.py`
- `tests/test_grounding_loading.py`
- world grounding tests

## Phase 13: Micropublication Projection Cut

Repository: `propstore`

Convert micropublication tables.

Tables:

- `micropublication`
- `micropublication_claim`

Preserve:

- content-derived micropublication id semantics
- first-writer-wins duplicate id behavior, unless Phase 1 proves it should move
  into a family pipeline diagnostic
- link dedupe on `(micropublication_id, claim_id)`
- WorldQuery active micropublication decoding

Deletion-first requirements:

- delete `MicropublicationInsertRow(values=...)`
- delete `MicropublicationClaimInsertRow(values=...)`
- delete custom micropublication DDL and insert SQL

Required gates:

- micropublication sidecar tests
- duplicate micropublication remediation tests

## Phase 14: Embedding and sqlite-vec Projection Cut

Repository: `propstore`

Convert embedding metadata and vector tables after Phase 2 proves runtime
constraints.

Tables:

- `embedding_model`
- `embedding_status`
- `concept_embedding_status`
- dynamic `claim_vec_{model_identity_hash}`
- dynamic `concept_vec_{model_identity_hash}`

Required decision:

- either keep embeddings inside the materialized world store with projection
  contracts, or split persistent embeddings into a separate derived embedding
  store keyed by model identity and entity content hash

Preserve:

- existing model identity behavior
- vector search behavior
- stale/orphan restore diagnostics
- entity text construction

Required gates:

- embedding operational tests
- sqlite-vec spike tests
- similarity search tests

## Phase 15: Quire Derived-Store Lifecycle

Repository: `../quire`

Only after Propstore has a real projection contract, add generic derived-store
lifecycle mechanics to Quire.

Candidate API:

```python
handle = derived_store.materialize(
    projection_id="propstore.world",
    source_commit=sha,
    content_hash=hash_value,
    build=builder,
)
```

Quire owns:

- cache root
- content-addressed path
- temp path allocation
- process-safe publish lock
- atomic publish
- cleanup of failed publishes
- opening a materialized store read-only
- cache GC

Quire does not own:

- Propstore projection schema
- Propstore cache-key ingredients
- Propstore diagnostics policy
- Propstore table names or column names

This is a two-repository phase. Quire changes land first. Propstore must never
pin Quire to a local filesystem path or local repository URL.

Required gates in `../quire`:

- targeted derived-store lifecycle tests
- full Quire test suite

## Phase 16: Propstore Handle Cutover

Repository: `propstore`

Replace repository-local sidecar path usage with derived-store handles.

Deletion-first requirements:

- delete production `Repository.sidecar_dir`
- delete production `Repository.sidecar_path`
- delete normal `pks build --output` sidecar workflow
- delete production `WorldQuery(sidecar_path=...)`

Replacement:

```python
handle = repo.derived_stores.materialize("propstore.world", commit=commit)
world = WorldQuery(repo, derived_store=handle)
```

Preserve explicit external export only if needed as a separate copy/export
command, not as the primary build path.

Required gates:

- `pks build` materializes a derived store and reports the handle
- `pks sidecar query` queries the derived store
- `WorldQuery(repo)` works without prior explicit path management
- historical queries materialize by commit without checking out the worktree
- no `knowledge/sidecar` directory is created by production build/query paths

## Phase 17: Final Deletions and Gates

Repository: `propstore`

Delete the old custom-table surface.

Required deletions:

- `propstore/sidecar/stages.py`, if all row wrappers are gone
- custom sidecar DDL functions in `propstore/sidecar/schema.py`
- custom `CREATE VIRTUAL TABLE` sidecar strings
- positional insert helpers
- duplicate schema validation in `WorldQuery`
- production `repo.sidecar_path`
- production output-path-driven sidecar build path

Required search gates:

- `rg -F "CREATE TABLE" propstore/sidecar propstore/world` returns no bespoke
  Propstore world-sidecar DDL outside projection generator tests
- `rg -F "CREATE VIRTUAL TABLE" propstore/sidecar propstore/world` returns no
  bespoke FTS or vec DDL outside projection generator tests
- `rg -F "values: tuple[Any" propstore/sidecar propstore/core propstore/world`
  returns no sidecar row-wrapper definitions
- `rg -F "sidecar_path" propstore` returns no production path ownership surface
  except explicitly named external export code, if any
- `rg -F "_REQUIRED_SCHEMA" propstore` returns no production duplicate schema
  contract

Required project gates:

- `uv run pyright propstore`
- logged targeted sidecar suite through `scripts/run_logged_pytest.ps1`
- logged full suite through `scripts/run_logged_pytest.ps1`

## Acceptance Criteria

The workstream is complete only when all of the following are true:

- every Propstore world-sidecar physical table is generated from a projection
  contract
- FTS5 virtual tables are generated from FTS projection contracts
- sqlite-vec virtual tables are generated from vector projection contracts or
  moved to a declared embedding derived store
- no production table has separate hand-authored DDL, insert SQL, schema
  validation, and decoder definitions
- WorldQuery opens through a derived-store handle
- build/query/history workflows do not depend on `knowledge/sidecar`
- quarantine, render policy, grounding, source promotion, and embedding behavior
  are unchanged unless a specific phase deliberately changes and tests them
- every phase has an atomic commit before the next table family or task slice
  starts

## Execution Notes

This workstream is deliberately long because the current sidecar is
load-bearing. Do not batch multiple table families into one implementation
slice. Each slice must delete one old surface, repair callers, run focused
tests, and commit before moving on.

If a table's current split is not understood, stop at the inventory result and
do not simplify it. Unknown complexity is treated as load-bearing until proven
otherwise.
