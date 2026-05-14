# Quire-Owned Derived Store Machinery Workstream

## Goal

Move generic derived-store projection machinery out of Propstore and into Quire
so Propstore becomes smaller, not merely differently shaped.

The previous zero-custom-tables workstream improved the architecture, but the
tracked `propstore/` tree still grew. From the pre-workstream baseline
`11ce4e42^` to the current starting point, `propstore/` changed by:

- `3400 insertions`
- `2069 deletions`
- net `+1331` lines

The starting commit for this workstream's future implementation slices is
`fad271ec42c5711b5a93b25d1351d2b7522a4bc5`.

This workstream pays down that growth. Completion requires a measured reduction
in tracked `propstore/` source lines from this workstream's starting commit.

Target architecture:

- Quire owns generic derived-store machinery: projection metamodel, declaration
  validation, generated SQLite DDL, generated insert/read plumbing, FTS5 and
  sqlite-vec declaration primitives, build diagnostics shape, projection
  dependency ordering, schema hashing, and derived-store lifecycle.
- Propstore owns semantic declarations: family meaning, domain field meaning,
  extraction from Propstore artifacts, semantic search text, semantic embedding
  text, and Propstore-specific query behavior.
- Propstore projection modules become thin semantic declarations or disappear.
- Propstore does not keep local wrappers around Quire APIs unless the wrapper
  adds real Propstore semantic policy.

## Non-Goals

Do not move Propstore semantics into Quire:

- claim, concept, context, source, relation, micropublication, grounding, or
  worldline meaning
- source promotion/status semantics
- render-policy semantics
- CEL, condition IR, form algebra, context lifting, grounded-rule, or
  argumentation semantics
- embedding text construction policy

Do not relocate entire Propstore modules into Quire. The objective is generic
machinery in Quire and less Propstore code, not the same code under a different
repository.

Do not add compatibility layers, aliases, fallback readers, dual projection
paths, bridge normalizers, or old/new shims. We control both repositories; change
the interface, update every caller, and delete the old path.

Do not count tests, workstream text, logs, generated diagnostics, or Quire code
growth as Propstore shrinkage. The shrink gate is measured only against tracked
files under `propstore/`.

## Starting Evidence

Largest Propstore growth areas from `11ce4e42^..HEAD`:

| Path | Insertions | Deletions | Net |
| --- | ---: | ---: | ---: |
| `propstore/sidecar/projection.py` | 535 | 0 | +535 |
| `propstore/sidecar/claims.py` | 473 | 86 | +387 |
| `propstore/sidecar/concepts.py` | 315 | 61 | +254 |
| `propstore/sidecar/build.py` | 252 | 94 | +158 |
| `propstore/sidecar/contexts.py` | 157 | 0 | +157 |
| `propstore/sidecar/embedding_store.py` | 248 | 124 | +124 |
| `propstore/sidecar/world_projection.py` | 114 | 0 | +114 |
| `propstore/sidecar/diagnostics.py` | 80 | 0 | +80 |
| `propstore/sidecar/relations.py` | 81 | 0 | +81 |

Important reductions already achieved:

| Path | Insertions | Deletions | Net |
| --- | ---: | ---: | ---: |
| `propstore/sidecar/schema.py` | 99 | 412 | -313 |
| `propstore/world/model.py` | 38 | 219 | -181 |
| `propstore/sidecar/claim_utils.py` | 0 | 154 | -154 |
| `propstore/source/promote.py` | 129 | 249 | -120 |
| `propstore/sidecar/stages.py` | 67 | 148 | -81 |

The next work must continue deletion from the new growth areas instead of adding
another layer around them.

## Hard Completion Gates

The final state must satisfy every gate below.

1. Propstore shrink gate:
   - Record the starting commit before Phase 1 implementation.
   - At completion, run:
     - `git diff --shortstat <starting-commit>..HEAD -- propstore`
     - `git diff --numstat <starting-commit>..HEAD -- propstore`
   - The net tracked change under `propstore/` must be at least `-1500` lines.
   - If the final net reduction is smaller than `-1500`, the workstream is not
     complete even if tests pass.

2. Previous-growth paydown gate:
   - Re-run:
     - `git diff --shortstat 11ce4e42^..HEAD -- propstore`
   - The net tracked result for `propstore/` must be `<= 0`.
   - This proves the prior `+1331` line increase was actually paid down.

3. No custom table regression gate:
   - `rg -n -F "CREATE TABLE" propstore`
   - `rg -n -F "CREATE VIRTUAL TABLE" propstore`
   - `rg -n -F "values: tuple[Any" propstore`
   - Remaining production hits must be generic Quire calls or deleted. Propstore
     must not regain hand-authored sidecar DDL or positional insert wrappers.

4. No Propstore-owned generic projection machinery gate:
   - `propstore/sidecar/projection.py` is deleted or reduced to Propstore
     semantic declarations only.
   - `propstore/sidecar/build.py` does not own generic projection ordering,
     schema hashing, generated DDL, generated insert dispatch, atomic publish,
     or cache lifecycle.
   - `propstore/sidecar/embedding_store.py` does not own generic sqlite-vec
     declaration/materialization machinery.

5. Quire ownership gate:
   - Generic APIs are implemented and tested in `../quire`.
   - Propstore imports and uses those public Quire APIs.
   - Propstore does not inspect Quire private internals to recover missing
     behavior.

6. Dependency pin gate:
   - Quire changes are pushed to a shared remote before Propstore pins them.
   - `pyproject.toml`, `uv.lock`, or equivalent dependency metadata never point
     at a local filesystem path, local git repository, `file://` URL, Windows
     drive path, WSL path, or editable local dependency.

7. Test gates:
   - In `../quire`: run the focused tests added or changed for each Quire phase,
     then `uv run pytest`.
   - In `propstore`: run `uv run pyright propstore`.
   - In `propstore`: run targeted sidecar/source/query tests through
     `scripts/run_logged_pytest.ps1`.
   - In `propstore`: run the full suite through `scripts/run_logged_pytest.ps1`.

## Execution Discipline

This workstream is deletion-first.

For every implementation slice:

1. Reread this workstream and identify the exact current phase.
2. Check tracked status in the repository being edited.
3. If the slice is speculative or benchmark-driven, create an experiment branch
   before editing.
4. Delete the old production surface for the current target before adding a
   replacement.
5. Use type, test, and search failures as the repair queue.
6. Run the focused gate for the slice.
7. Commit the slice atomically with explicit paths.
8. Reread this workstream immediately after every commit before choosing the
   next slice.

Passing tests is not completion. A phase is complete only when its deletion and
line-count gates pass.

## Dependency Order

The phases below are topologically ordered.

1. Record baseline and classify generic machinery
2. Quire projection metamodel extraction
3. Quire generated SQLite schema and insert/read primitives
4. Quire FTS5 projection primitives
5. Quire sqlite-vec projection primitives
6. Quire derived-store lifecycle and diagnostics
7. Propstore dependency pin
8. Delete Propstore projection metamodel
9. Delete Propstore generated DDL/insert/read ownership
10. Delete Propstore FTS machinery
11. Delete Propstore sqlite-vec machinery
12. Delete Propstore build/lifecycle ownership
13. Collapse remaining Propstore declaration boilerplate
14. Final reduction, search, and test gates

## Phase 1: Record Baseline and Classify Generic Machinery

Repository: `propstore`

Record the starting commit for this workstream in this file before code
changes. Also record:

- `git diff --shortstat 11ce4e42^..HEAD -- propstore`
- `git diff --numstat 11ce4e42^..HEAD -- propstore`
- `git diff --shortstat <starting-commit>..HEAD -- propstore`

Create an inventory table for these files:

- `propstore/sidecar/projection.py`
- `propstore/sidecar/build.py`
- `propstore/sidecar/claims.py`
- `propstore/sidecar/concepts.py`
- `propstore/sidecar/contexts.py`
- `propstore/sidecar/relations.py`
- `propstore/sidecar/diagnostics.py`
- `propstore/sidecar/embedding_store.py`
- `propstore/sidecar/world_projection.py`

For each exported type/function, classify it as exactly one of:

- `generic-derived-store`
- `propstore-semantic-declaration`
- `propstore-semantic-extractor`
- `propstore-query-behavior`
- `delete-without-replacement`

Phase gate:

- No `unknown` classifications remain.
- Every `generic-derived-store` item is assigned to a Quire phase below.
- Every `delete-without-replacement` item has a named search/test proof.

## Phase 2: Quire Projection Metamodel Extraction

Repository: `../quire`

Move generic projection declaration concepts into Quire.

Candidate ownership:

- projection identity and versioning
- table/virtual-table declarations
- column declarations
- primary keys, foreign keys, indexes, uniqueness
- JSON encoding/decoding declarations
- generated schema digest inputs
- declaration validation errors

Requirements:

- Names and tests use neutral examples such as books, notes, events, or pages.
- No Propstore family names appear in Quire tests or docs.
- Declarations are typed enough that Propstore does not need local dictionaries
  for generic schema metadata.

Focused gates:

- `uv run pytest tests/test_derived_store.py`
- `uv run pytest tests/test_families.py`
- `uv run pytest`

## Phase 3: Quire Generated SQLite Schema and Insert/Read Primitives

Repository: `../quire`

Add generic SQLite generation and row materialization from the Quire projection
metamodel.

Quire owns:

- ordinary table DDL generation
- deterministic column ordering
- insert/upsert SQL generation
- generated row encoders
- generated row decoders where a declaration supplies the output type
- schema hash contribution
- validation that declared foreign keys and indexes reference real columns

Phase gate:

- Quire tests prove at least one multi-table projection with a foreign key,
  JSON column, generated insert, and decoded read path.
- No Propstore vocabulary in Quire.

## Phase 4: Quire FTS5 Projection Primitives

Repository: `../quire`

Add generic FTS5 declaration support.

Quire owns:

- FTS virtual table declaration
- generated FTS DDL
- content/source table association where applicable
- generated FTS row insertion/update
- schema hash contribution

Propstore still owns:

- which semantic text fields feed concept search
- which semantic text fields feed claim search
- ranking/query semantics used by Propstore world queries

Focused gate:

- Quire tests prove ordinary table plus FTS table materialization and querying
  without Propstore-specific vocabulary.

## Phase 5: Quire sqlite-vec Projection Primitives

Repository: `../quire`

Add generic sqlite-vec declaration support.

Quire owns:

- vector table declaration
- dimension validation
- generated sqlite-vec DDL
- vector table naming from projection/model identity
- vector row insertion/update
- schema hash contribution

Propstore still owns:

- embedding model identity policy
- claim/concept embedding text construction
- stale-content detection policy if it depends on Propstore semantics

Focused gate:

- Quire tests prove dynamic vector table creation, insertion, and read/search
  behavior behind a generic declaration.

## Phase 6: Quire Derived-Store Lifecycle and Diagnostics

Repository: `../quire`

Move generic build/lifecycle behavior into Quire.

Quire owns:

- commit-bound derived-store identity
- cache root and materialized location selection
- projection version/cache key calculation
- atomic publish
- lock discipline
- stale cache cleanup and GC hooks
- generic build diagnostics structure
- projection dependency ordering

Propstore still owns:

- when to request a world projection
- semantic build diagnostics content
- source-promotion/status interpretation of diagnostics

Focused gates:

- Quire tests prove materialization is commit-bound and atomically published.
- Quire tests prove failed projection builds report structured diagnostics.
- `uv run pytest`

## Phase 7: Propstore Dependency Pin

Repository: `propstore`

Only start after Quire changes are pushed to a shared remote.

Before editing dependency files, verify the Quire reference is a pushed tag or
immutable pushed commit SHA. Reject local paths, editable paths, local git
paths, Windows drive paths, WSL paths, and `file://` URLs.

Update only the dependency metadata required for Propstore to consume the new
Quire APIs.

Focused gate:

- `uv run pyright propstore`

## Phase 8: Delete Propstore Projection Metamodel

Repository: `propstore`

Delete Propstore-owned generic declaration types from
`propstore/sidecar/projection.py` before repairing callers.

Keep only Propstore semantic declarations if they cannot be represented directly
as data passed to Quire. Prefer deleting the file entirely.

Phase gate:

- `propstore/sidecar/projection.py` is deleted or net-reduced by at least 80%.
- Search shows Propstore imports Quire projection types instead of local generic
  projection types.
- `uv run pyright propstore`

## Phase 9: Delete Propstore Generated DDL/Insert/Read Ownership

Repository: `propstore`

Delete Propstore-owned generated schema, insert, and read machinery now covered
by Quire.

Primary targets:

- `propstore/sidecar/claims.py`
- `propstore/sidecar/concepts.py`
- `propstore/sidecar/contexts.py`
- `propstore/sidecar/relations.py`
- `propstore/sidecar/diagnostics.py`
- `propstore/sidecar/world_projection.py`

Propstore code may remain only when it is a semantic extractor, semantic
declaration, or Propstore query behavior.

Phase gate:

- The combined net tracked change across the primary targets is at least
  `-600` lines from the workstream starting commit.
- `rg -n -F "CREATE TABLE" propstore/sidecar`
- `rg -n -F "INSERT INTO" propstore/sidecar`
- Remaining hits are semantic query SQL or Quire-owned calls, not generated
  table plumbing.

Focused tests:

- sidecar build tests
- world query tests
- source promotion/status tests

## Phase 10: Delete Propstore FTS Machinery

Repository: `propstore`

Delete Propstore-owned FTS DDL and row plumbing now covered by Quire.

Propstore keeps only semantic search text declarations and query behavior.

Phase gate:

- `rg -n -F "CREATE VIRTUAL TABLE" propstore/sidecar`
- `rg -n -F "fts5" propstore/sidecar`
- Remaining production hits are declarations passed to Quire or semantic query
  behavior.

Focused tests:

- concept search tests
- claim FTS/search tests
- world query search tests

## Phase 11: Delete Propstore sqlite-vec Machinery

Repository: `propstore`

Delete generic vector table creation and vector row materialization now covered
by Quire.

Propstore keeps only:

- embedding text construction
- model selection/identity semantics
- claim/concept freshness policy if semantic
- high-level similarity query API

Phase gate:

- `propstore/sidecar/embedding_store.py` is net-reduced by at least 50% from the
  workstream starting commit.
- No Propstore code hand-authors sqlite-vec DDL.

Focused tests:

- embedding store tests
- sqlite-vec dependent tests, skipped only when sqlite-vec is unavailable for
  the same reason they skip today

## Phase 12: Delete Propstore Build/Lifecycle Ownership

Repository: `propstore`

Delete generic build/lifecycle behavior from `propstore/sidecar/build.py`.

Quire owns build orchestration mechanics. Propstore keeps only semantic inputs:

- requested projection
- semantic projection declarations
- semantic diagnostics emitted by Propstore extractors
- Propstore-specific build report rendering if needed

Phase gate:

- `propstore/sidecar/build.py` is net-reduced by at least 50% from the
  workstream starting commit.
- Propstore does not own atomic publish, lock, cache-root, derived-store path,
  schema-hash, or projection-ordering mechanics.

Focused tests:

- sidecar build tests
- source status tests
- CLI source lifecycle tests

## Phase 13: Collapse Remaining Propstore Declaration Boilerplate

Repository: `propstore`

Review every remaining sidecar module after Phases 8-12.

For each remaining helper, ask:

- Does this encode Propstore semantics?
- Does this remove meaningful duplication?
- Could this be a data declaration passed directly to Quire?
- Is this a wrapper around a Quire API?

Delete wrappers and local helper families that do not add Propstore semantic
policy.

Phase gate:

- No sidecar helper remains solely to rename, forward, normalize, or wrap a
  Quire generic derived-store API.
- Every remaining sidecar helper has a one-line semantic ownership note in the
  Phase 13 completion ledger.

## Phase 14: Final Reduction, Search, and Test Gates

Repository: `propstore`

Run the hard completion gates exactly.

Required commands:

- `git diff --shortstat <starting-commit>..HEAD -- propstore`
- `git diff --numstat <starting-commit>..HEAD -- propstore`
- `git diff --shortstat 11ce4e42^..HEAD -- propstore`
- `rg -n -F "CREATE TABLE" propstore`
- `rg -n -F "CREATE VIRTUAL TABLE" propstore`
- `rg -n -F "values: tuple[Any" propstore`
- `uv run pyright propstore`
- `powershell -File scripts/run_logged_pytest.ps1 -Label sidecar-quire-owned <focused sidecar/source/query tests>`
- `powershell -File scripts/run_logged_pytest.ps1 -Label full-suite`

Completion report must include:

- the starting commit
- final Propstore net line-count delta from the starting commit
- final Propstore net line-count delta from `11ce4e42^`
- files deleted
- files reduced by more than 50%
- remaining Propstore sidecar files and why each is semantic rather than
  generic derived-store machinery
- Quire commit/tag pinned by Propstore
- test logs for focused and full-suite Propstore runs
