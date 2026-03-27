# Semantic Core Unification Plan

Date: 2026-03-26

Status: In Progress

This plan was written against the current codebase and is binding; do not audit, reinterpret, simplify, substitute, or “validate it against the repo” before execution, and if you believe a blocker exists, stop and report the exact blocker before making any edits.

Goal: Refactor `propstore` toward one canonical semantic core without losing current functionality, using TDD, self-contained phases, and one commit per completed phase.

## North Star

Make the system revolve around one canonical semantic object:

- a compiled claim graph
- activated under one environment/context model
- annotated with provenance, relations, parameterizations, labels, and deltas
- consumed by all analyzers (`claim_graph`, `praf`, `atms`, worldlines, hypotheticals)

The intended end state is:

- one policy type
- one environment type
- one canonical graph IR
- one activation pipeline
- multiple analyzers over the same active graph

This plan explicitly avoids leading with storage/schema rewrites. The sidecar remains a source of rows until the runtime architecture is unified.

## Global Rules

- [ ] Every phase is TDD-first.
- [ ] Every phase is self-contained and leaves the repo in a green state.
- [ ] Every phase ends with a dedicated commit.
- [ ] No phase starts until its predecessor is fully green.
- [ ] No user-facing functionality is intentionally removed before a replacement path exists.
- [ ] Existing CLI behavior is treated as compatibility truth unless it is already internally inconsistent.

## Global Invariants

These are the invariants the refactor must preserve or strengthen:

- [ ] Binding order does not change activation or query results.
- [ ] Row order in the sidecar does not change semantic results.
- [ ] Empty hypothetical overlays are identity transforms.
- [ ] Add/remove inverse overlays return to the same semantic state.
- [ ] Label environments remain minimal antichains after every merge.
- [ ] Analyzer target projection is independent of active-claim ordering.
- [ ] Worldline serialization remains stable under round-trip.
- [ ] Policy/environment serialization is lossless across runtime surfaces.

## Functional Risk Register

These are the places most likely to regress:

- [ ] `BoundWorld` activation and filtering
- [ ] `resolved_value()` behavior across backends
- [ ] hypothetical overlays
- [ ] worldline materialization
- [ ] ATMS label/nogood behavior
- [ ] conflict recomputation in active views
- [ ] structured projection compatibility behavior

## Leaf Modules To Preserve

These should remain mostly leaf-like unless a phase gives a strong reason otherwise:

- [ ] `propstore/dung.py`
- [ ] `propstore/dung_z3.py`
- [ ] `propstore/bipolar.py`
- [ ] `propstore/opinion.py`
- [ ] `propstore/cel_checker.py`
- [ ] `propstore/form_utils.py`
- [ ] `propstore/unit_dimensions.py`
- [ ] `propstore/sympy_generator.py`

## Modules To Converge

These are the architectural center and should move toward one shared core:

- [ ] `propstore/world/model.py`
- [ ] `propstore/world/bound.py`
- [ ] `propstore/world/hypothetical.py`
- [ ] `propstore/world/resolution.py`
- [ ] `propstore/world/types.py`
- [ ] `propstore/argumentation.py`
- [ ] `propstore/structured_argument.py`
- [ ] `propstore/worldline.py`
- [ ] `propstore/worldline_runner.py`

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

- [ ] Commit: `feat: introduce canonical semantic graph and result dataclasses`

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

- [ ] Commit: `feat: build canonical world graph from existing sidecar`

## Phase 4: Activation Layer Over the Graph

Intent: make activation and context restriction graph-native.

### TDD Tasks

- [ ] Write failing tests asserting activated graph claim sets match current `BoundWorld.active_claims()`.
- [ ] Write failing tests asserting inactive sets match current behavior.
- [ ] Write failing tests for context visibility parity.
- [ ] Write failing tests for binding-order invariance over active graph construction.

### Implementation Tasks

- [ ] Create `propstore/core/activation.py`.
- [ ] Make `WorldModel.bind()` produce or internally cache an `ActiveWorldGraph`.
- [ ] Refactor `BoundWorld` into a graph-backed facade.
- [ ] Keep current public methods intact while reducing direct row-centric logic.

### Files Likely Touched

- [ ] `propstore/core/activation.py`
- [ ] `propstore/world/model.py`
- [ ] `propstore/world/bound.py`

### Completion Criteria

- [ ] Activation is expressed in terms of the graph core.
- [ ] `BoundWorld` remains compatible but is substantially thinner.

### Commit

- [ ] Commit: `refactor: move activation onto active world graph`

## Phase 5: Shared Analyzer Pipeline

Intent: stop writing one-off resolution plumbing per backend.

### TDD Tasks

- [ ] Write failing tests for analyzer pipeline parity with current `claim_graph`.
- [ ] Write failing tests for analyzer pipeline parity with current `praf`.
- [ ] Write failing tests for target projection independence from active-id ordering.
- [ ] Write failing tests for stable extension/grounded/preferred result parity.

### Implementation Tasks

- [ ] Create a shared pipeline abstraction such as:
  - relation collection
  - framework construction
  - semantics computation
  - projection back to target claims
- [ ] Migrate `claim_graph` first.
- [ ] Migrate `praf` second.
- [ ] Keep leaf solvers unchanged where possible.

### Files Likely Touched

- [ ] `propstore/argumentation.py`
- [ ] `propstore/world/resolution.py`
- [ ] possibly a new `propstore/core/analyzers/` package
- [ ] `propstore/praf.py` only as needed for cleaner inputs

### Completion Criteria

- [ ] `claim_graph` and `praf` consume the same active graph abstraction.
- [ ] Survivor projection logic is no longer duplicated across multiple functions.

### Commit

- [ ] Commit: `refactor: route claim graph and praf through shared analyzer pipeline`

## Phase 6: Hypothetical Overlays As Graph Deltas

Intent: make overlays compose with all analyzers instead of bypassing the core.

### TDD Tasks

- [ ] Write failing tests for empty-delta identity.
- [ ] Write failing tests for add/remove inverse identity.
- [ ] Write failing tests asserting overlay parity for current `claim_graph`.
- [ ] Write failing tests asserting overlay parity for current `praf`.
- [ ] Write failing tests exposing and then eliminating the current `ATMS` downgrade behavior.

### Implementation Tasks

- [ ] Replace synthetic-claim dict overlay logic with a `GraphDelta`.
- [ ] Apply deltas to `ActiveWorldGraph`.
- [ ] Remove analyzer-specific overlay downgrades.
- [ ] Preserve current public hypothetical interfaces if possible.

### Files Likely Touched

- [ ] `propstore/world/hypothetical.py`
- [ ] `propstore/core/graph_types.py`
- [ ] graph application helpers in core

### Completion Criteria

- [ ] Hypotheticals operate over the semantic core.
- [ ] No backend silently downgrades because of overlays.

### Commit

- [ ] Commit: `refactor: implement hypothetical overlays as graph deltas`

## Phase 7: Worldlines On The Shared Core

Intent: make worldlines a first-class consumer of the same semantic pipeline.

### TDD Tasks

- [ ] Write failing tests for worldline parity after core migration.
- [ ] Write failing tests for stable worldline serialization.
- [ ] Write failing tests for dependency capture parity.
- [ ] Add a property test that worldline materialization is stable under repeated execution on unchanged semantic inputs.

### Implementation Tasks

- [ ] Refactor `worldline_runner.py` to consume `ActiveWorldGraph` and shared analyzer results.
- [ ] Eliminate policy/environment duplication already reduced in Phase 1.
- [ ] Keep file format compatible where possible.
- [ ] If practical, improve dependencies from flat consulted-claim bags toward witness subgraphs, but only if compatibility can be preserved or versioned safely.

### Files Likely Touched

- [ ] `propstore/worldline.py`
- [ ] `propstore/worldline_runner.py`
- [ ] core analyzer/result modules

### Completion Criteria

- [ ] Worldlines are no longer a parallel runtime path.
- [ ] Worldlines reuse the same semantic center as world queries.

### Commit

- [ ] Commit: `refactor: run worldlines against shared semantic core`

## Phase 8: ATMS On The Shared Core

Intent: preserve the good ATMS machinery while removing its dependence on `BoundWorld` internals.

### TDD Tasks

- [ ] Write failing tests for ATMS parity over the new graph-backed activation path.
- [ ] Write failing tests for label minimality and antichain preservation.
- [ ] Write failing tests for nogood subsumption pruning.
- [ ] Write failing tests for future/relevance/intervention parity.
- [ ] Add property tests for label merge associativity where valid under the current algebra.

### Implementation Tasks

- [ ] Keep `world/labelled.py` as the label algebra.
- [ ] Make `world/atms.py` consume canonical graph nodes and justifications.
- [ ] Remove implicit dependence on `BoundWorld` implementation details where possible.
- [ ] Keep current ATMS CLI behavior compatible.

### Files Likely Touched

- [ ] `propstore/world/labelled.py`
- [ ] `propstore/world/atms.py`
- [ ] `propstore/world/bound.py`
- [ ] core graph/justification modules

### Completion Criteria

- [ ] ATMS becomes another analyzer over the same semantic center.
- [ ] Label behavior remains exact.

### Commit

- [ ] Commit: `refactor: migrate atms engine onto canonical graph`

## Phase 9: Structured Projection Decision

Intent: stop carrying a misleading abstraction.

### TDD Tasks

- [ ] Write failing tests that capture the chosen direction:
  - real structured arguments with premises/subarguments
  - or explicit demotion/rename with compatibility aliases

### Implementation Options

Option A: Make it real.

- [ ] Build actual justifications/subarguments from the semantic core.
- [ ] Add tests for non-empty premises and subargument graphs.

Option B: Make it honest.

- [ ] Rename/demote `structured_projection`.
- [ ] Keep compatibility shims if needed.
- [ ] Ensure errors/docs clearly reflect capability.

### Files Likely Touched

- [ ] `propstore/structured_argument.py`
- [ ] `propstore/world/resolution.py`
- [ ] related tests

### Completion Criteria

- [ ] The code no longer implies stronger structured capability than it actually provides.

### Commit

- [ ] Commit: `refactor: make structured projection honest`

## Phase 10: Storage Normalization

Intent: normalize the sidecar only after the runtime architecture is unified.

### TDD Tasks

- [ ] Write failing migration-parity tests asserting old and new sidecar layouts build identical canonical graphs.
- [ ] Write failing tests for sidecar build determinism.
- [ ] Write failing tests for backward compatibility if dual-read support is needed temporarily.

### Implementation Tasks

- [ ] Consider splitting the current wide `claim` table into:
  - `claim_core`
  - typed payload tables
  - `relation_edge`
  - `justification`
  - possibly compiled activation or support metadata tables
- [ ] Keep the graph builder as the semantic boundary.
- [ ] Do not let raw schema become the new center.

### Files Likely Touched

- [ ] `propstore/build_sidecar.py`
- [ ] `propstore/world/model.py`
- [ ] graph builder and migration tests

### Completion Criteria

- [ ] Storage is cleaner without changing semantics.
- [ ] The graph builder remains the sole semantic adapter boundary.

### Commit

- [ ] Commit: `refactor: normalize sidecar schema behind canonical graph builder`

## Suggested PR Sequence

- [ ] PR 1: Phase 0
- [ ] PR 2: Phase 1
- [ ] PR 3: Phase 2
- [ ] PR 4: Phase 3
- [ ] PR 5: Phase 4
- [ ] PR 6: Phase 5
- [ ] PR 7: Phase 6
- [ ] PR 8: Phase 7
- [ ] PR 9: Phase 8
- [ ] PR 10: Phase 9
- [ ] PR 11: Phase 10

## Commands To Run At The End Of Every Phase

- [ ] run the targeted tests added in that phase
- [ ] run the surrounding subsystem tests
- [ ] run the full test suite if phase scope touched the architectural center
- [ ] inspect diff for accidental semantic drift
- [ ] commit with the phase-specific message

## Stop Conditions

Pause the rollout and reassess if any of these happen:

- [ ] parity tests expose conflicting semantics that cannot both be preserved
- [ ] hypothetical overlays require a deeper ATMS design decision before Phase 6
- [ ] worldline file format compatibility becomes too constraining
- [ ] structured projection turns out to be needed for a near-term workflow and cannot simply be demoted

## Definition Of Done

- [ ] world queries, worldlines, hypotheticals, and analyzers all share one semantic center
- [ ] policy and environment are single-source concepts
- [ ] activation is graph-native
- [ ] overlays are graph deltas
- [ ] ATMS and non-ATMS analyzers compose over the same active graph
- [ ] the remaining leaf modules stay leaf-like
- [ ] any remaining “structured” capability claims are honest
