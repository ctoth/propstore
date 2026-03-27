# Semantic Core Unification Plan Completed Phases

Date: 2026-03-26

Status: Archived Completed Phases

Source plan: `plans/semantic-core-unification-plan-2026-03-26.md`

These are the completed phases moved out of the active plan so the active plan only tracks remaining work.

## Phase 0: Behavior Net

Intent: lock current externally meaningful behavior before refactoring internals.

### TDD Tasks

- [x] Add or expand parity tests for `bind -> active_claims -> value_of -> derived_value -> resolved_value`.
- [x] Add parity tests for `claim_graph`, `praf`, and `atms` over the same fixture family.
- [x] Add parity tests for hypothetical overlays under each currently supported backend path.
- [x] Add parity tests for worldline materialization and round-trip.
- [x] Add parity tests for active-view conflict recomputation.
- [x] Add property tests for binding-order invariance.
- [x] Add property tests for environment/label normalization and antichain minimality.

### Likely Test Files

- [x] `tests/test_world_model.py`
- [x] `tests/test_worldline.py`
- [x] `tests/test_worldline_properties.py`
- [x] `tests/test_worldline_error_visibility.py`
- [x] `tests/test_argumentation_integration.py`
- [x] `tests/test_praf_integration.py`
- [x] `tests/test_atms_engine.py`
- [x] `tests/test_conflict_detector.py`
- [x] add a new properties-focused test file if the current suite needs separation

### Completion Criteria

- [x] New tests fail before implementation adjustments.
- [x] All tests pass after only compatibility-preserving fixes.
- [x] The suite clearly exposes the current hypothetical `ATMS` downgrade behavior as a documented compatibility fact.

### Commit

- [x] Commit: `test: lock world, backend, overlay, and worldline semantics`

## Phase 1: Unify Policy and Environment

Intent: remove duplicate policy/environment concepts before introducing the graph core.

### TDD Tasks

- [x] Write failing tests asserting one canonical policy definition is shared by world and worldline code paths.
- [x] Write failing tests for policy serialization round-trip.
- [x] Write failing tests for environment serialization round-trip.
- [x] Write failing tests for worldline parity using the shared policy/environment type.

### Implementation Tasks

- [x] Make `worldline.py` use the same `RenderPolicy` concept as `world/types.py`.
- [x] Make `worldline.py` use the same `Environment` concept as `world/types.py`.
- [x] Remove string-vs-enum drift where practical, keeping compatibility adapters only where required.
- [x] Minimize duplicate field definitions across `worldline.py` and `world/types.py`.

### Files Likely Touched

- [x] `propstore/world/types.py`
- [x] `propstore/worldline.py`
- [x] `propstore/worldline_runner.py`
- [x] CLI or serializer tests as needed

### Completion Criteria

- [x] There is one runtime definition of render policy.
- [x] There is one runtime definition of environment.
- [x] Worldline behavior remains compatible.

### Commit

- [x] Commit: `refactor: unify render policy and environment across world and worldline`

## Phase 2: Introduce Canonical Semantic Types

Intent: add a new core without migrating behavior yet.

### TDD Tasks

- [x] Write failing tests for deterministic equality/ordering of graph objects.
- [x] Write failing tests for provenance normalization.
- [x] Write failing tests for graph delta identity behavior.
- [x] Write failing tests for analyzer result dataclass stability and round-trip where relevant.

### Implementation Tasks

- [x] Create `propstore/core/graph_types.py` for typed claim nodes, relation edges, parameterization edges, provenance records, labels, justifications, and graph deltas.
- [x] Create `propstore/core/results.py` for analyzer result dataclasses if needed.
- [x] Keep types runtime-oriented and independent of SQLite.
- [x] Do not migrate callers yet.

### Suggested New Types

- [x] `CompiledWorldGraph`
- [x] `ActiveWorldGraph`
- [x] `ClaimNode`
- [x] `RelationEdge`
- [x] `ParameterizationEdge`
- [x] `ConflictWitness`
- [x] `GraphDelta`
- [x] analyzer output records

### Completion Criteria

- [x] Core graph types exist and are tested.
- [x] No external behavior changes yet.

### Commit

- [x] Commit: `feat: introduce canonical semantic graph and result dataclasses`

## Phase 3: Build Canonical Graph From Existing Sidecar

Intent: bridge the old storage world into the new in-memory semantic core.

### TDD Tasks

- [x] Write failing tests asserting the graph builder preserves all current claims, concepts, stances, conflicts, and parameterizations from fixture sidecars.
- [x] Write failing tests for row-order independence.
- [x] Write failing tests for stable graph build output over repeated loads.

### Implementation Tasks

- [x] Create `propstore/core/graph_build.py`.
- [x] Add sidecar-row to graph-node/edge mapping.
- [x] Preserve current semantics exactly, including any oddities that are part of compatibility.
- [x] Expose graph construction hooks from `WorldModel`.

### Files Likely Touched

- [x] `propstore/core/graph_build.py`
- [x] `propstore/world/model.py`
- [x] test fixtures/helpers as needed

### Completion Criteria

- [x] A canonical graph can be built entirely from the existing sidecar.
- [x] Existing runtime paths still work unchanged.

### Commit

- [x] Commit: `feat: build canonical world graph from existing sidecar`
