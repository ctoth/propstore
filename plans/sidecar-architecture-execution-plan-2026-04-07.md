# Sidecar Architecture Execution Plan

**Date:** 2026-04-07
**Scope:** full refactor plan for the compiled sidecar architecture in `propstore`
**Status:** Proposed
**Primary surfaces:**
- `propstore/build_sidecar.py`
- `propstore/world/model.py`
- `propstore/source_ops.py`
- `propstore/cli/compiler_cmds.py`
- `tests/test_build_sidecar.py`
- `tests/test_world_model.py`
- `tests/test_claim_notes.py`
- `tests/test_source_cli.py`
- `tests/test_source_relations.py`

---

## Goal

Turn the sidecar into a first-class compiled semantic store rather than a monolithic build script plus a second-class source/provenance appendage.

End state:

1. sidecar compilation lives under a real `propstore/sidecar/` package
2. `source` is a first-class compiled entity with stable claim-to-source joins
3. the sidecar schema is versioned and asserted on open
4. `WorldModel` reads a stable schema instead of probing for whatever columns happen to exist
5. authored semantics compile at build time; derived argumentation projections no longer bloat the build path without need
6. claim notes remain first-class
7. raw `notes.md` stays out of the reasoning store
8. the old `build_sidecar.py` file stops being the architectural center

This is an execution plan, not a design sketch. It is not complete until every listed slice is either completed or explicitly deferred by the user.

---

## Fixed Architectural Decisions

These decisions are locked for this plan.

1. The sidecar is a compiled read model, not the source of truth.
2. Git/YAML remains canonical.
3. `source` is a first-class semantic entity in the sidecar.
4. Claim-level notes stay in sidecar storage.
5. Raw source notes from `notes.md` do not get compiled into claim rows.
6. This plan does not add a compiled `source_document` or source-note index table.
7. Authored justifications compile into the sidecar.
8. Stance-derived justifications move out of the build-time persistence path unless a slice proves they must remain persisted.
9. The end state is a `propstore/sidecar/` package with a thin compatibility wrapper or no wrapper at all.

---

## Non-Negotiable Rules

1. Work one slice at a time.
2. Do not widen scope mid-slice because the current module is messy.
3. Every slice must leave the repo in a coherent measurable state.
4. Every pytest run must be `uv run pytest -vv` and must tee full output to `logs/test-runs/`.
5. After every passing targeted or broader test run, reread this plan and continue to the next unchecked slice.
6. Do not declare the plan complete while `propstore/build_sidecar.py` remains the real implementation center.
7. Do not claim source is first-class while claim-to-source joins still depend primarily on the stringly `source_paper` convention.
8. Do not add raw `notes.md` to reasoning-facing claim or relation tables.
9. Do not remove compatibility shims until tests and callers have moved.
10. Preserve public behavior unless a failing test proves the current behavior is wrong.

---

## Current Reality

The current state is:

- [build_sidecar.py](C:/Users/Q/code/propstore/propstore/build_sidecar.py) is the gravitational center for schema creation, data loading, row preparation, conflict persistence, FTS, and sidecar lifecycle.
- The file is large enough to be an architectural smell on its own.
- The sidecar already stores a `source` table, claim notes, authored justifications, contexts, form algebra, conflicts, FTS, and embedding state.
- The source lifecycle already treats notes and metadata as real source-branch artifacts via [source_ops.py](C:/Users/Q/code/propstore/propstore/source_ops.py#L357).
- [world/model.py](C:/Users/Q/code/propstore/propstore/world/model.py#L265) still joins `source` through `core.source_paper`, which is the main “source as second-class citizen” seam.
- The docs still understate the actual entity set and sidecar role.

Implication:

- this is primarily a structural refactor plus a source-model correction
- it is not a greenfield rebuild
- the correct plan is extract, stabilize, and then simplify

---

## Desired Package Shape

Target package:

- `propstore/sidecar/__init__.py`
- `propstore/sidecar/build.py`
- `propstore/sidecar/schema.py`
- `propstore/sidecar/sources.py`
- `propstore/sidecar/concepts.py`
- `propstore/sidecar/claims.py`
- `propstore/sidecar/embeddings.py`

Responsibilities:

- `build.py`
  Public orchestration entry point. Build lifecycle, content hash, rebuild skipping, snapshot/restore, transaction handling.
- `schema.py`
  DDL, schema version constant, `meta` table, schema assertions.
- `sources.py`
  Source-table population and source-related row helpers.
- `concepts.py`
  Concepts, aliases, relationships, parameterizations, parameterization groups, forms, form algebra, concept FTS.
- `claims.py`
  Claim row preparation, typed payload persistence, stances, authored justifications, conflicts, claim FTS.
- `embeddings.py`
  Embedding snapshot/restore and any schema helpers for vector tables.

---

## Test Logging Contract

PowerShell pattern for every pytest run:

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
uv run pytest -vv <target> 2>&1 | Tee-Object "logs/test-runs/$ts-<label>.log"
```

Examples:

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
uv run pytest -vv tests/test_build_sidecar.py tests/test_world_model.py 2>&1 | Tee-Object "logs/test-runs/$ts-sidecar-schema.log"
```

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
uv run pytest -vv tests/test_source_cli.py tests/test_source_relations.py 2>&1 | Tee-Object "logs/test-runs/$ts-sidecar-source-links.log"
```

---

## Commit Discipline

Commit after every green slice. No squashing during execution.

Expected commit sequence:

1. `propstore: specify sidecar architecture contract`
2. `propstore: add sidecar schema versioning`
3. `propstore: extract sidecar build orchestrator`
4. `propstore: make sidecar sources first class`
5. `propstore: extract sidecar concept compilation`
6. `propstore: extract sidecar claim compilation`
7. `propstore: move derived justifications out of build path`
8. `propstore: simplify worldmodel around versioned sidecar schema`
9. `propstore: update sidecar docs and remove compatibility cruft`

If a slice must split further to stay reviewable, do so, but keep the same execution order.

---

## Slice 1: Write The Architecture Contract

**Intent:**
Freeze the sidecar package boundaries and non-negotiable scope decisions in repo form before code motion starts.

**Primary files:**
- `plans/sidecar-architecture-execution-plan-2026-04-07.md`
- optionally `docs/data-model.md`

**Tasks:**

1. Land this execution plan.
2. Ensure the fixed decisions are explicit:
   - source is first-class
   - claim notes stay
   - raw `notes.md` stays out
   - `propstore/sidecar/` is the target package
3. If needed, add one short doc note clarifying that the current data-model doc is incomplete relative to implementation.

**Tests first:**

- none required for the plan file itself

**Acceptance:**

- one execution plan exists that can drive the entire refactor without reopening scope

**Commit when green:**

- `propstore: specify sidecar architecture contract`

---

## Slice 2: Add Schema Versioning And Meta Table

**Intent:**
Stop treating schema shape as something to infer ad hoc at runtime.

**Primary files:**
- `propstore/sidecar/schema.py`
- `propstore/build_sidecar.py`
- `propstore/world/model.py`
- `tests/test_build_sidecar.py`
- `tests/test_world_model.py`

**Tests first:**

1. failing test: sidecar build creates a `meta` table with a schema version
2. failing test: `WorldModel` opens when schema version matches
3. failing test: `WorldModel` fails clearly when schema version is unsupported

**Implementation:**

1. create `propstore/sidecar/schema.py`
2. move DDL there without changing table definitions yet
3. add `SCHEMA_VERSION`
4. create and populate `meta`
5. update `WorldModel` to assert schema version on open

**Targeted tests:**

- `tests/test_build_sidecar.py`
- `tests/test_world_model.py`

**Broader tests:**

- `tests/test_build_sidecar.py`
- `tests/test_world_model.py`
- `tests/test_contexts.py`

**Acceptance:**

- schema version is explicit
- `WorldModel` no longer treats runtime schema probing as the primary contract

**Commit when green:**

- `propstore: add sidecar schema versioning`

---

## Slice 3: Extract The Build Orchestrator

**Intent:**
Separate lifecycle orchestration from semantic compilation logic.

**Primary files:**
- `propstore/sidecar/build.py`
- `propstore/build_sidecar.py`
- `tests/test_build_sidecar.py`
- `tests/test_embed_operational_error.py`
- `tests/test_cli.py`

**Tests first:**

1. failing test: public `build_sidecar()` behavior remains unchanged through the compatibility surface
2. failing test: rebuild skipping still works
3. failing test: embedding snapshot/restore still survives rebuilds

**Implementation:**

1. create `propstore/sidecar/build.py`
2. move content-hash, rebuild-skip, transactional creation, and embedding snapshot/restore there
3. keep `propstore/build_sidecar.py` as a thin wrapper initially

**Targeted tests:**

- `tests/test_build_sidecar.py`
- `tests/test_cli.py`
- `tests/test_embed_operational_error.py`

**Broader tests:**

- `tests/test_build_sidecar.py`
- `tests/test_claim_notes.py`
- `tests/test_cli.py`

**Acceptance:**

- orchestration code lives outside the monolith
- public build entry point remains stable

**Commit when green:**

- `propstore: extract sidecar build orchestrator`

---

## Slice 4: Make Sources First-Class In Compilation

**Intent:**
Fix the main architectural smell: source identity should not feel bolted on.

**Primary files:**
- `propstore/sidecar/sources.py`
- `propstore/build_sidecar.py` or `propstore/sidecar/build.py`
- `propstore/world/model.py`
- `tests/test_build_sidecar.py`
- `tests/test_world_model.py`
- `tests/test_source_cli.py`
- `tests/test_source_relations.py`

**Tests first:**

1. failing test: claims compile with an explicit source reference that joins to the `source` table
2. failing test: `WorldModel.get_claim()` exposes source metadata through the stable join
3. failing test: source lifecycle promotion still lands source rows correctly in `sources/*.yaml`
4. failing test: old `source_paper`-based behavior remains compatible during migration

**Implementation:**

1. create `propstore/sidecar/sources.py`
2. move source population there
3. introduce a real claim-to-source reference in sidecar compilation
4. keep compatibility with `source_paper` while callers migrate

**Targeted tests:**

- `tests/test_build_sidecar.py`
- `tests/test_world_model.py`
- `tests/test_source_cli.py`
- `tests/test_source_relations.py`

**Broader tests:**

- source CLI tests
- sidecar build tests
- world model tests

**Acceptance:**

- source is a first-class compiled entity in both storage and read paths
- the “source as second-class citizen” seam is materially reduced

**Commit when green:**

- `propstore: make sidecar sources first class`

---

## Slice 5: Extract Concept Compilation

**Intent:**
Move concept/form compilation out of the monolith with no semantic drift.

**Primary files:**
- `propstore/sidecar/concepts.py`
- `propstore/build_sidecar.py` or `propstore/sidecar/build.py`
- `tests/test_build_sidecar.py`
- `tests/test_contexts.py`
- `tests/test_parameterization_groups.py`

**Tests first:**

1. failing characterization tests for concept rows, aliases, relationships, parameterizations, groups, forms, form algebra, and concept FTS if any are not already pinned
2. failing test: extracted module path preserves existing outputs

**Implementation:**

1. move concept-related `_populate_*` helpers into `propstore/sidecar/concepts.py`
2. keep signatures small and data-oriented
3. ensure no behavior changes in inserted rows

**Targeted tests:**

- `tests/test_build_sidecar.py`
- `tests/test_parameterization_groups.py`
- `tests/test_contexts.py`

**Broader tests:**

- `tests/test_build_sidecar.py`
- `tests/test_form_algebra.py`
- `tests/test_world_model.py`

**Acceptance:**

- concept/form compilation is no longer implemented inside the monolith

**Commit when green:**

- `propstore: extract sidecar concept compilation`

---

## Slice 6: Extract Claim Compilation

**Intent:**
Move claim-side compilation into its own module and keep claim notes first-class.

**Primary files:**
- `propstore/sidecar/claims.py`
- `propstore/build_sidecar.py` or `propstore/sidecar/build.py`
- `tests/test_build_sidecar.py`
- `tests/test_claim_notes.py`
- `tests/test_contexts.py`
- `tests/test_relate_opinions.py`

**Tests first:**

1. failing characterization tests for:
   - claim core rows
   - typed payload tables
   - claim notes
   - stance edges
   - authored justification rows
   - conflict persistence
   - claim FTS
2. failing test: extracted claim module preserves current stored values

**Implementation:**

1. move claim row preparation and claim persistence helpers into `propstore/sidecar/claims.py`
2. keep claim-note handling unchanged
3. move stance and authored-justification compilation there
4. keep conflict persistence there for now

**Targeted tests:**

- `tests/test_build_sidecar.py`
- `tests/test_claim_notes.py`
- `tests/test_contexts.py`
- `tests/test_relate_opinions.py`

**Broader tests:**

- `tests/test_build_sidecar.py`
- `tests/test_claim_notes.py`
- `tests/test_world_model.py`
- `tests/test_graph_build.py`

**Acceptance:**

- claim-side compilation is no longer implemented in the monolith
- claim notes still roundtrip through build and query

**Commit when green:**

- `propstore: extract sidecar claim compilation`

---

## Slice 7: Remove Derived Justifications From The Build Path

**Intent:**
Keep the build focused on authored semantic compilation, not extra derived reasoning projections.

**Primary files:**
- `propstore/sidecar/claims.py`
- `propstore/core/justifications.py`
- `propstore/aspic_bridge.py`
- `tests/test_build_sidecar.py`
- `tests/test_structured_argument.py`
- `tests/test_argumentation_integration.py`

**Tests first:**

1. failing test: authored justifications are still available from the compiled store
2. failing test: stance-derived justifications are still available to reasoning/query consumers after the move
3. failing test: removing build-time persistence does not regress argumentation behavior

**Implementation:**

1. stop persisting stance-derived justifications at build time
2. keep authored justifications persisted
3. move derived-justification projection to query-time or analyzer-time code

**Targeted tests:**

- `tests/test_build_sidecar.py`
- `tests/test_structured_argument.py`
- `tests/test_argumentation_integration.py`

**Broader tests:**

- argumentation and bridge tests
- sidecar build tests

**Acceptance:**

- build only persists authored semantics
- consumers still get the justifications they need

**Commit when green:**

- `propstore: move derived justifications out of build path`

---

## Slice 8: Simplify WorldModel Around The Stable Schema

**Intent:**
Make the read side match the cleaned build side.

**Primary files:**
- `propstore/world/model.py`
- `propstore/world/bound.py`
- `tests/test_world_model.py`
- `tests/test_contexts.py`
- `tests/test_graph_build.py`

**Tests first:**

1. failing test: `WorldModel` reads claims, source metadata, contexts, and relationships through the new stable schema contract
2. failing test: old optional-column probing is no longer needed on the mainline path
3. failing test: graph build and bound-world behavior remain unchanged

**Implementation:**

1. centralize read SQL around the new schema contract
2. reduce or eliminate `_has_column` and `_has_table` probing from the steady-state path
3. keep only explicit schema-version branches where necessary

**Targeted tests:**

- `tests/test_world_model.py`
- `tests/test_contexts.py`
- `tests/test_graph_build.py`

**Broader tests:**

- `tests/test_world_model.py`
- `tests/test_contexts.py`
- `tests/test_graph_build.py`
- `tests/test_argumentation_integration.py`

**Acceptance:**

- `WorldModel` is visibly simpler
- runtime schema poking is no longer the normal model

**Commit when green:**

- `propstore: simplify worldmodel around versioned sidecar schema`

---

## Slice 9: Documentation And Final Cleanup

**Intent:**
Make the docs and remaining code match the final architecture.

**Primary files:**
- `docs/data-model.md`
- `docs/integration.md`
- `docs/python-api.md`
- `docs/cli-reference.md`
- `propstore/build_sidecar.py`
- `tests/test_cli.py`

**Tasks:**

1. update docs to describe source as first-class
2. update docs to describe the sidecar as a compiled read model
3. explicitly document that raw `notes.md` is source-branch material, not sidecar claim data
4. reduce `propstore/build_sidecar.py` to a compatibility shim or delete it if callers are fully moved
5. remove stale comments or docs that describe the old shape

**Targeted tests:**

- `tests/test_cli.py`
- any import-path tests affected by wrapper removal

**Broader tests:**

- `tests/test_cli.py`
- `tests/test_build_sidecar.py`
- `tests/test_world_model.py`

**Acceptance:**

- docs match implementation
- the monolithic file is no longer the implementation center

**Commit when green:**

- `propstore: update sidecar docs and remove compatibility cruft`

---

## Full Regression Pass

This plan is not complete without a final regression run covering the build, source lifecycle, world model, contexts, and argumentation surfaces touched by the refactor.

Minimum final suite:

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
uv run pytest -vv `
  tests/test_build_sidecar.py `
  tests/test_world_model.py `
  tests/test_claim_notes.py `
  tests/test_contexts.py `
  tests/test_cli.py `
  tests/test_source_cli.py `
  tests/test_source_relations.py `
  tests/test_argumentation_integration.py `
  tests/test_structured_argument.py `
  tests/test_graph_build.py 2>&1 | Tee-Object "logs/test-runs/$ts-sidecar-architecture-final.log"
```

If that passes cleanly, run the broader full suite and log it.

---

## Completion Criteria

This plan is complete only when all of the following are true:

1. `propstore/sidecar/` exists and owns the real sidecar implementation.
2. `source` is first-class in storage and read joins.
3. schema versioning is explicit and enforced.
4. `WorldModel` no longer relies on general runtime schema probing as its main contract.
5. claim notes still roundtrip.
6. raw `notes.md` has not been pushed into claim/relation reasoning tables.
7. authored justifications compile cleanly.
8. derived justification persistence has been removed from the build path or explicitly justified by tests and retained on purpose.
9. docs describe the real architecture.
10. the broader regression pass is green.

---

## Forbidden Failure Modes

The plan fails if we do any of the following:

1. leave the old monolith in place and merely move helpers cosmetically
2. call source first-class while still treating it as a provenance string convention
3. stuff raw source notes into claim rows because it feels convenient
4. preserve build-time derived-justification persistence just because it already exists
5. stop after a successful extraction milestone while unchecked slices remain
6. treat passing tests as plan completion before the final architecture is actually in place

