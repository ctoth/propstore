# Quire FTS And Vector Workstream

Date: 2026-05-18

## Goal

Implement Quire-owned SQLAlchemy FTS and vector support before any Propstore
build-orchestration or family cutover starts.

Final state:

- FTS is implemented through SQLAlchemy extension machinery, not Quire
  projection classes and not Propstore raw SQL.
- `sqlalchemy-fts5` can express the concept-like and claim-like FTS tables and
  queries Propstore needs.
- Quire vector support covers create, insert, search, snapshot, and restore
  behavior for derived stores.
- `quire/sqlite_vec_store.py` keeps the useful generic entity/snapshot API
  while replacing raw connection/table plumbing that belongs to the
  SQLAlchemy charter engine.
- Quire exposes charter/index/cache declarations for FTS and vector storage.
- Propstore family work does not need FTS or vector workarounds.

## Scope And Repositories

Repositories:

- `C:\Users\Q\code\quire`
- `C:\Users\Q\code\sqlalchemy-fts5`

Owned surfaces:

- `C:\Users\Q\code\sqlalchemy-fts5`
- `C:\Users\Q\code\quire\quire\sqlite_vec_store.py`
- Quire SQLAlchemy charter/schema/index/cache machinery
- Quire derived-store session/catalog integration touched by FTS/vector support

Do not edit Propstore production code in this workstream.

## Prerequisites

Before implementation:

Required phase file prerequisites: `00-index.md`, `inventory-matrix.md`,
`helper-ledger.md`, `01-quire-capability-and-charter.md`,
`02-quire-sqlalchemy-engine.md`.

1. Confirm the Quire SQLAlchemy dependency and capability workstream is
   complete.
2. Confirm the Quire charter/schema IR workstream is complete.
3. Confirm the Quire SQLAlchemy table, mapping, session, and catalog
   workstream is complete.
4. Confirm current worktree state in Propstore, Quire, and `sqlalchemy-fts5`.
5. Confirm dependency references are not local filesystem pins.
6. Confirm the Python floor decision: Propstore and Quire remain
   `requires-python = ">=3.11"`, and `sqlalchemy-fts5` must support Python
   3.11 before Quire may depend on it.

Required dependency-pin searches:

```powershell
Set-Location C:\Users\Q\code\quire
rg -n -F -- "file://" pyproject.toml uv.lock
rg -n -F -- "path =" pyproject.toml
rg -n -F -- "workspace = true" pyproject.toml
rg -n -F -- "C:" pyproject.toml uv.lock

Set-Location C:\Users\Q\code\sqlalchemy-fts5
rg -n -F -- "file://" pyproject.toml uv.lock
rg -n -F -- "path =" pyproject.toml
rg -n -F -- "workspace = true" pyproject.toml
rg -n -F -- "C:" pyproject.toml uv.lock
```

Any dependency entry that resolves only from the local filesystem fails the
prerequisite gate.

Required Python-floor checks:

```powershell
Set-Location C:\Users\Q\code\propstore
rg -n -F -- 'requires-python = ">=3.11"' pyproject.toml

Set-Location C:\Users\Q\code\quire
rg -n -F -- 'requires-python = ">=3.11"' pyproject.toml

Set-Location C:\Users\Q\code\sqlalchemy-fts5
rg -n -F -- 'requires-python = ">=3.11"' pyproject.toml
```

If `sqlalchemy-fts5` still requires Python 3.12 or higher, update
`sqlalchemy-fts5` to support Python 3.11 and run its gates before editing
Quire.

## Execution Rules

- Execute this workstream before Propstore build orchestration.
- Prove extension capability in `sqlalchemy-fts5` before adding Quire
  production usage.
- Fix `sqlalchemy-fts5` when it cannot express the required FTS5 behavior.
- Fix `sqlalchemy-fts5` to keep the stack Python floor at 3.11; do not raise
  Propstore or Quire to Python 3.12 for this workstream.
- Push `sqlalchemy-fts5` changes and tag or otherwise identify an immutable
  pushed commit before Quire pins the dependency.
- Quire may consume a modified `sqlalchemy-fts5` only from a published package
  version or immutable pushed commit/tag. Local path, workspace, and file URL
  pins are forbidden.
- Keep FTS out of Quire projection classes.
- Keep FTS out of Propstore raw string SQL.
- Keep vector behavior in Quire instead of pushing it into Propstore family
  cutovers.
- Delete or replace Quire `FtsProjection` and `VecProjection` production
  usage for this slice; before the final Quire projection-module deletion
  phase, remaining hits are an inventory that must not be imported by new
  Propstore cutover code.

## FTS Implementation

Required path:

1. Inspect `C:\Users\Q\code\sqlalchemy-fts5`.
2. Confirm `C:\Users\Q\code\sqlalchemy-fts5` exists.
3. Run the existing `sqlalchemy-fts5` gates.
4. Use or fix `sqlalchemy-fts5` for FTS5 virtual tables.
5. Add proof coverage for concept-like FTS:
   - table creation through SQLAlchemy extension APIs;
   - indexed concept id, label/name/symbol text, alias text, and searchable
     normalized text fields required by Propstore concept search;
   - query behavior that returns stable entity identifiers and ranks.
6. Add proof coverage for claim-like FTS:
   - table creation through SQLAlchemy extension APIs;
   - indexed claim id, text payload, algorithm or equation text, provenance
     text, and searchable rendered text fields required by Propstore claim
     search;
   - query behavior that returns stable entity identifiers and ranks.
7. Expose the Quire charter/index declaration needed to bind FTS virtual tables
   to generated SQLAlchemy tables and mapped domain classes.
8. Ensure Quire derived-store create/rebuild opens the extension and creates
   FTS artifacts through the same catalog lifecycle as generated tables.
9. Ensure Quire read-only runtime sessions can execute FTS queries without raw
   Propstore SQL.

Completion state for FTS:

- `sqlalchemy-fts5` owns FTS5 virtual-table expression for SQLAlchemy.
- Quire owns generic FTS declaration, creation, and query adapters.
- Propstore can declare concept and claim search intent through charters.
- No new Propstore search path depends on `FtsProjection` or hand-written FTS
  SQL.

## Vector Implementation

Vector behavior:

1. Inspect current `quire/sqlite_vec_store.py`.
2. Preserve the useful generic entity/snapshot API.
3. Replace raw connection/table setup with SQLAlchemy-backed vector cache
   machinery where it overlaps the charter engine.
4. Express vector stores as charter/index/cache declarations.
5. Support vector table create, insert, search, snapshot, and restore.
6. Integrate vector caches with Quire derived-store writable build sessions.
7. Integrate vector search with Quire read-only runtime sessions.
8. Preserve embedding model identity and snapshot/restore policy hooks needed
   by Propstore.

Completion state for vector support:

- Quire owns vector cache schema creation and validation.
- Quire owns vector insert/search APIs over SQLAlchemy-derived stores.
- Quire owns vector snapshot/restore APIs.
- Propstore embedding families supply entity policy and text-source policy
  through charters and domain code, not raw vector table plumbing.

## Required Gates

Run in `sqlalchemy-fts5`:

```powershell
Set-Location C:\Users\Q\code\sqlalchemy-fts5
uv run pyright
uv run pytest -vv
```

After any `sqlalchemy-fts5` fix, push the repository and record the pushed tag
or immutable commit SHA used by Quire. Quire dependency metadata must point to
that published package version, pushed tag, or immutable pushed commit SHA.

Run in Quire:

```powershell
Set-Location C:\Users\Q\code\quire
uv run pyright
uv run pytest -vv
```

Required proof results:

- concept-like FTS proof query passes;
- claim-like FTS proof query passes;
- vector table create proof passes;
- vector insert proof passes;
- vector search proof passes;
- vector snapshot proof passes;
- vector restore proof passes;
- no local path dependency pins.
- `sqlalchemy-fts5` advertises and passes tests for Python 3.11.
- Quire consumes `sqlalchemy-fts5` from a published package version, pushed
  tag, or immutable pushed commit SHA.

## Quire-First Completion Gate

This gate must pass before
`04-propstore-build-orchestration.md` starts.

Quire must have:

- SQLAlchemy dependency declared from a published package source;
- charter/schema IR;
- generated SQLAlchemy tables;
- imperative mappings;
- generated relationships;
- association object mapping;
- enum conversion;
- JSON value object conversion;
- schema catalog/hash/version validation;
- writable build sessions;
- read-only runtime sessions;
- derived-store handle integration;
- FTS through `sqlalchemy-fts5` or a fixed owned SQLAlchemy extension;
- vector create/insert/search/snapshot support;
- passing Quire type and test gates.

Required commands in Quire:

```powershell
Set-Location C:\Users\Q\code\quire
uv run pyright
uv run pytest -vv
rg -n -F -- "ProjectionTable" quire tests
rg -n -F -- "ProjectionModel" quire tests
rg -n -F -- "FtsProjection" quire tests
rg -n -F -- "VecProjection" quire tests
```

Before the final Quire projection-module deletion workstream, the search
output is an inventory of remaining old paths, not a passing gate. Copy that
inventory into the workstream report. New Propstore cutover work must not
import those old paths.

## Completion Criteria

This workstream is complete only when:

- `sqlalchemy-fts5` passes its type and test gates.
- `sqlalchemy-fts5` supports Python 3.11, matching Propstore and Quire.
- Modified `sqlalchemy-fts5` changes have been pushed and Quire is pinned to a
  published package version, pushed tag, or immutable pushed commit SHA.
- Quire passes its type and test gates.
- Quire has FTS declarations, creation, and query support through SQLAlchemy
  extension machinery.
- Quire has vector declarations, create/insert/search, and snapshot/restore
  support.
- Quire derived-store handles integrate FTS/vector support with writable build
  sessions and read-only runtime sessions.
- Quire schema catalog/hash/version validation accounts for FTS and vector
  artifacts.
- The required old-path inventory searches have been run and recorded.
- No local dependency pin is present.

## Phase 4 Execution Record

Recorded 2026-05-20.

Prerequisites:

- Phase 1-2 and Phase 3 are complete in the preceding child workstreams.
- Propstore current branch: `master`; task-owned files clean before Phase 4 prerequisite edits; unrelated untracked files present.
- Quire current branch: `master`; tracked files clean; unrelated untracked notes/reports/output paths present.
- `sqlalchemy-fts5` exists at `C:\Users\Q\code\sqlalchemy-fts5`; current branch `master`; tracked files clean before the Python-floor edit; untracked `.hypothesis/` present.
- Quire dependency-pin searches for `file://`, `path =`, `workspace = true`, and `C:` returned no hits.
- `sqlalchemy-fts5` dependency-pin searches for `file://`, `path =`, `workspace = true`, and `C:` returned no hits.
- Propstore Python floor check: `pyproject.toml:5:requires-python = ">=3.11"`.
- Quire Python floor check: `pyproject.toml:6:requires-python = ">=3.11"`.
- Initial `sqlalchemy-fts5` Python floor check did not find `>=3.11`; `pyproject.toml` had `requires-python = ">=3.12"` and Pyright `pythonVersion = "3.12"`.

`sqlalchemy-fts5` prerequisite fix:

- Commit `04eab80 Support Python 3.11` changes `requires-python` to `>=3.11`, adds the Python 3.11 classifier, changes Pyright `pythonVersion` to `3.11`, and refreshes `uv.lock`.
- Commit `9af77f4 Type FTS5 SQLAlchemy constructs` fixes strict Pyright typing for the SQLAlchemy DDL/expression/table hooks and property tests.
- Commit `e50ebd2 Add Propstore-shaped FTS proofs` adds concept-like and claim-like FTS5 proof coverage for stable ids and ranks.
- Focused proof gate: `uv run pytest -vv tests/test_propstore_shapes.py` passed with 2 passed.
- Commit `ac6d059 Constrain generated FTS identifiers` fixes the existing Hypothesis DDL property gate by excluding FTS5-reserved generated table names and passing insert payloads as mappings.
- Full `sqlalchemy-fts5` gates after the fixes:
  - `uv run pyright` passed with 0 errors.
  - `uv run pytest -vv` passed with 48 passed.
- Pushed immutable `sqlalchemy-fts5` commit for Quire consumption: `ac6d05968f2f3bcf61c20a09efa41de4a605560d` (`origin/master`, `git@github.com:ctoth/sqlalchemy-fts5.git`).

Quire FTS/vector implementation:

- Commit `2eeb43a Pin sqlalchemy FTS extension` pins Quire to pushed `sqlalchemy-fts5` commit `ac6d05968f2f3bcf61c20a09efa41de4a605560d` through `https://github.com/ctoth/sqlalchemy-fts5`.
- Commit `6ff5b82 Add SQLAlchemy FTS and vector caches` adds Quire charter/schema declarations for FTS indexes and vector caches, SQLAlchemy FTS table generation/query/population adapters, SQLAlchemy store lifecycle/validation hooks for FTS/vector artifacts, and vector create/insert/search/snapshot/restore APIs over SQLAlchemy connections.
- Commit `1d67026 Retain sqlite vector projection APIs` keeps the existing sqlite3 embedding model/entity/snapshot API that current Propstore imports while the later Propstore embeddings phase deletes those imports and moves callers to the SQLAlchemy vector cache path.
- Focused Quire proof gate: `uv run pytest -vv tests/test_sqlalchemy_engine.py tests/test_derived_store.py::test_vec_projection_materializes_rowids_and_searches_vectors` passed with 6 passed.
- Full Quire gates after the retained-vector commit:
  - `uv run pyright` passed with 0 errors.
  - `uv run pytest -vv` passed with 359 passed in 281.13s.
- Quire dependency-pin searches for `file://`, `path =`, `workspace = true`, and `C:` returned no hits after adding `sqlalchemy-fts5` and runtime `sqlite-vec`.
- Quire old-path inventory after Phase 4:
  - `ProjectionTable` remains in `quire/projections.py`, `quire/derived_runtime.py`, `quire/projection_mapping.py`, `quire/sqlite_vec_store.py`, `quire/__init__.py`, and projection tests.
  - `ProjectionModel` remains in `quire/projection_mapping.py`, `quire/__init__.py`, and projection mapping tests.
  - `FtsProjection` remains in `quire/projections.py`, `quire/__init__.py`, and projection tests.
  - `VecProjection` remains in `quire/projections.py`, `quire/sqlite_vec_store.py`, `quire/__init__.py`, and projection tests.
- Pushed immutable Quire commit for Propstore consumption: `1d670267eba752a615122c26fdc551c466b06601` (`origin/master`, `git@github.com:ctoth/quire.git`).
- Propstore pin refreshed to pushed Quire commit `1d670267eba752a615122c26fdc551c466b06601`; `uv.lock` resolves Quire, `sqlalchemy-fts5`, and `sqlite-vec` from non-local sources.
- Propstore dependency-pin searches for `quire @ file`, `quire @ ..`, `quire @ C:`, `path =`, and `workspace = true` returned no hits; `uv lock --check` passed.
- Propstore package type gate: `uv run pyright propstore` passed with 0 errors.

Phase 4 and the Quire-first completion gate are complete. Phase 5 may start.
