# Render Layer Architecture Plan

Date: 2026-03-23

## Execution Status

- R0: Completed
- R1: Completed
- R1.5: Completed
- R2: Completed
- R3: Completed
- R4: Completed
- R4.5: Completed
- R5: In progress

Baseline verification before implementation:

- `uv run pytest tests/test_world_model.py tests/test_argumentation_integration.py tests/test_bipolar_argumentation.py tests/test_render_time_filtering.py tests/test_sensitivity.py tests/test_graph_export.py tests/test_cli.py -q`
- Result: `219 passed, 192 warnings`

R1/R1.5 verification:

- `uv run pytest tests/test_render_contracts.py tests/test_world_model.py tests/test_cli.py tests/test_claim_notes.py tests/test_contexts.py -q`
- Result: `209 passed, 176 warnings`
- Cleanup checks:
  - no remaining `ClaimView` references in `propstore/` or `tests/`
  - no remaining imports from `propstore.world_model` in `propstore/` or `tests/`

R2/R3 verification:

- `uv run pytest tests/test_render_contracts.py tests/test_world_model.py tests/test_contexts.py -q`
- Result: `148 passed, 182 warnings`
- Bound/hypothetical views now satisfy the `BeliefSpace` contract and carry `RenderPolicy`

R4/R4.5 verification:

- `uv run pytest tests/test_argumentation_integration.py tests/test_bipolar_argumentation.py tests/test_render_time_filtering.py tests/test_sensitivity.py tests/test_graph_export.py -q`
- Result: `66 passed, 16 warnings`
- `propstore/world_model.py` deleted
- argumentation now targets store methods instead of raw SQLite connection input
- graph export now uses public store methods instead of `_conn`

R5 verification so far:

- `uv run pytest -q`
- Current result: `789 passed, 200 warnings`
- Cleanup checks:
  - no `ClaimView` references
  - no imports from `propstore.world_model`
  - no `_world._`, `_base._world`, `sqlite3.Connection`, or `wm._conn` references in the targeted render/analyzer files

## Purpose

This plan defines the next architectural phase for propstore.

The immediate goal is to make the render layer explicit and first-class without prematurely collapsing the deeper semantic model. The render layer should become the declared place where policy is applied to a non-committal repository in order to produce a usable belief space.

This is a boundary refactor first, not a full semantic rewrite.

## Why This Now

The current codebase already has the pieces of a render layer, but they are scattered:

- `propstore/world/model.py` provides the read/query surface
- `propstore/world/bound.py` binds conditions and contexts
- `propstore/world/resolution.py` applies resolution strategies
- `propstore/argumentation.py` acts as one renderer/analyzer
- `propstore/sensitivity.py`, `graph_export.py`, `chain_query`, and `hypothetical` all operate over world-like views
- CLI policy is currently spread across flags and function arguments

At the same time, important policy choices are still smeared across storage, build-time compilation, world queries, and analyzer code.

The result is:

- no single definition of "a way of seeing the world"
- too much leakage of SQLite and current sidecar schema into analysis layers
- no clean place to keep resolution/render policy separate from source truth
- too much risk that the current `claim` shape gets mistaken for the final ontology

## Guiding Principles

These rules are load-bearing.

1. Source storage remains non-committal.
   Source artifacts may preserve rival claims, rival stances, proposals, contexts, derivations, and incompatible alternatives.

2. Render is policy application, not truth mutation.
   A rendered answer is always "under policy P and environment E", never "the repository now believes X".

3. Build may compile and index, but not canonize.
   Sidecars are compiled projections and caches, not the semantic authority.

4. Explanations must survive resolution.
   Any render that selects, filters, or defeats alternatives must retain enough trace to explain what was considered and why it was excluded.

5. This phase does not settle the final semantic core.
   Proposition-vs-evidence separation, proposal-artifact discipline, and ATMS-style environments must remain possible after this phase.

6. No public compatibility shims.
   We are not optimizing for backward compatibility in this phase. Old public entrypoints and alias modules should be migrated off and then deleted, not preserved indefinitely behind forwarding layers.

## Explicit Non-Goals

This plan does not attempt to complete:

- a full proposition/evidence/derivation split
- a full ATMS implementation
- migration support for legacy `knowledge/`
- a new on-disk repo format
- complete cleanup of all build-time semantic issues
- final resolution of proposal artifacts vs accepted source artifacts

This phase should make those later moves easier, not harder.

This phase also does not preserve old public import paths for their own sake. Migration is direct.

## Current Architectural Problems

### 1. Policy is scattered instead of represented

Resolution strategy, argumentation semantics, confidence threshold, override behavior, and comparison mode are threaded through function signatures and CLI flags rather than represented as one object.

### 2. Render logic is coupled to storage internals

`argumentation.py` currently consumes raw `sqlite3.Connection`, and `BoundWorld` reaches into `WorldModel` internals instead of programming to a stable interface.

### 3. The current view protocol must be fully migrated, not merely sidelined

`ClaimView` covers only a small subset of what the world/render surface actually does. Important operations like explanation, conflicts, resolution, graph export, and analyzer behavior live outside the contract.

The right move is not to keep `ClaimView` around as a legacy side interface. The right move is to replace it directly with the new full render/view contract and migrate call sites onto that contract.

### 4. Build-time conflict state is treated too much like truth

The sidecar stores conflicts detected at build time, but render-time activation can change what is jointly live. This creates a stale-shadow problem unless the render layer owns the final say.

### 5. The current model risks blessing `claim` too early

The current system still uses `claim` as the unit around which too many APIs are organized. If we turn that directly into the permanent render abstraction, we may accidentally lock in the wrong semantic center.

## Target Architectural Shape

The core idea is:

`Repository artifacts` + `Environment` + `RenderPolicy` => `BeliefSpace`

Then analyzers operate over `BeliefSpace`.

The render layer should become the explicit bridge between a rich, rival-preserving repository and user-facing answers.

## Proposed Abstractions

### `ArtifactStore`

The storage access boundary.

Responsibilities:

- provide compiled access to source and proposal artifacts
- expose claims/assertions/artifacts relevant to a concept or environment
- expose stance and relation artifacts
- expose parameterizations, groups, concept metadata, and stored indexes
- avoid leaking raw database handles into render/analyzer code

Important note:

`ArtifactStore` is a better name than `ClaimStore` because it does not quietly declare `claim` to be the permanent atom of the system.

### `Repository.store`

The repository should likely expose a lazy `.store` property.

That would make the architecture read naturally:

- `repo` is the knowledge repository and path root
- `repo.store` is the compiled access boundary over that repository
- `repo.store.bind(environment, policy)` produces a `BeliefSpace`

This is a good fit for the current code because `Repository` already centralizes path knowledge, including `sidecar_path`. Adding `.store` makes the storage/render boundary feel like part of the repository model instead of an unrelated helper object callers must construct manually.

### `Environment`

The binding and visibility boundary.

First version responsibilities:

- represent condition bindings
- represent context visibility
- represent optional environment qualifiers needed by render

Future-compatible responsibilities:

- assumptions
- queryables
- nogoods
- ATMS-style labels or local-theory semantics

The first version may be thin, but the type should exist early so we do not mistake "bindings + one context filter" for the final model.

### `RenderPolicy`

The declared way of seeing.

First version fields should include:

- resolution strategy
- argumentation semantics
- preference comparison mode
- confidence threshold
- explicit overrides
- proposal inclusion policy
- per-concept strategy overrides if needed

This object should be serializable, testable, and explainable.

### `BeliefSpace`

The rendered belief space.

Responsibilities:

- expose active artifacts under an environment
- expose value lookup and derived lookup under the current policy
- expose resolved values under the current policy
- expose active conflicts under the current environment
- expose explanation/provenance traces
- act as the common surface for analyzers

This should be the center of the next phase.

### `Analyzer`

Optional common interface for downstream reasoning tools.

Candidate analyzers:

- argumentation
- sensitivity analysis
- graph export
- chain derivation tracing
- hypothetical differencing

We should not over-design this on day one, but the render-centered model should make it natural.

## Minimal Contract For Phase 1

The narrowest viable first contract is:

- `ArtifactStore`
- `Environment`
- `RenderPolicy`
- `BeliefSpace`

With these minimal operations:

### `ArtifactStore`

- get artifacts for a concept or all concepts
- get relation artifacts among active items
- get parameterizations for an output concept
- get concept metadata
- get precomputed conflict hints

### `Environment`

- bindings
- visible contexts
- helper methods for condition compatibility and context visibility

### `BeliefSpace`

- `active_artifacts(...)`
- `inactive_artifacts(...)`
- `value_of(...)`
- `derived_value(...)`
- `resolved_value(...)`
- `active_conflicts(...)`
- `explain(...)`

The system can start with claim-shaped rows underneath this contract, but the contract must avoid implying that claim rows are the final ontology.

## What Survives Largely Intact

These modules are valuable and should mostly survive:

- `propstore/cel_checker.py`
- `propstore/z3_conditions.py`
- `propstore/propagation.py`
- `propstore/sensitivity.py`
- `propstore/dung.py`
- `propstore/dung_z3.py`
- `propstore/preference.py`
- `propstore/form_utils.py`
- `propstore/unit_dimensions.py`
- `propstore/value_comparison.py`
- most of `graph_export.py` after interface adaptation

The current solver, symbolic, and analyzer machinery is real value. The redesign should preserve it.

## What Should Be Reworked First

### `propstore/world/types.py`

Add the new render contract types and replace the current thin `ClaimView` with the full migrated view/store contract.

### `propstore/world/model.py`

Turn `WorldModel` into an `ArtifactStore` implementation with public methods instead of analyzer code reaching into internals.

### `propstore/world/bound.py`

Turn `BoundWorld` into a `BeliefSpace` implementation over `ArtifactStore + Environment + RenderPolicy`.

### `propstore/world/resolution.py`

Stop passing loose policy knobs through free functions. Resolution should take a `RenderPolicy` and operate over `BeliefSpace` and `ArtifactStore`.

### `propstore/argumentation.py`

Replace raw SQLite coupling with render/store interfaces. Argumentation should be an analyzer over a view plus relation access, not a DB-bound special case.

### `propstore/world/hypothetical.py`

Rebuild it as a view wrapper, not a wrapper around private internals of `BoundWorld` or `WorldModel`.

### `propstore/world_model.py`

Delete it after imports are migrated. It is a backward-compatibility shim and should not survive this phase.

## Sequencing Plan

### Phase R0: Write the contract

Deliverables:

- this plan
- a short architecture note defining `ArtifactStore`, `Environment`, `RenderPolicy`, `BeliefSpace`
- explicit statement of non-goals and deferred semantic work

Acceptance:

- team agreement that this is a boundary refactor, not a claim-ontology freeze

### Phase R1: Introduce the types with minimal behavior change

Deliverables:

- add new types/protocols in `propstore/world/types.py`
- adapt `WorldModel` to implement the store protocol
- add `Repository.store` as the repository-owned entry point
- keep current behavior stable

Acceptance:

- existing world tests still pass
- no CLI behavior change

### Phase R1.5: Migrate the old view surface directly

Deliverables:

- replace `ClaimView` usages with the new `BeliefSpace` contract
- remove the idea that the old thin view remains a parallel public abstraction
- migrate imports off `propstore.world_model`

Acceptance:

- there is one public view contract, not two overlapping ones
- world-facing code no longer needs to choose between legacy and new interfaces
- `propstore/world_model.py` is either gone or marked for immediate deletion in the next patch with no remaining imports

### Phase R2: Move resolution under `RenderPolicy`

Deliverables:

- create `RenderPolicy`
- update resolution functions to consume one policy object
- stop spreading policy knobs through multiple signatures

Acceptance:

- `world resolve` and chain-style flows produce the same answers as before for current fixtures
- policy state can be logged/explained from one object

### Phase R3: Turn `BoundWorld` into an explicit `BeliefSpace`

Deliverables:

- `BoundWorld` becomes a view over store + environment + policy
- add `resolved_value(...)`
- make explanation and conflict access part of the view contract

Acceptance:

- `value_of`, `derived_value`, `resolved_value`, `explain`, and conflict inspection all run through the same view object

### Phase R4: Decouple analyzers

Deliverables:

- adapt argumentation to consume store/view interfaces
- adapt sensitivity and graph export to consume the view surface
- confirm hypothetical reasoning still composes cleanly

Acceptance:

- analyzers can run without direct access to `sqlite3.Connection`
- tests can use in-memory fakes for the store boundary

### Phase R4.5: Remove dead and transitional code

Deliverables:

- delete `propstore/world_model.py`
- delete `ClaimView`
- remove any compatibility exports in `propstore/world/__init__.py`
- remove any obsolete transitional helpers introduced only for migration

Acceptance:

- no repo code imports deleted compatibility surfaces
- search confirms no references remain to removed shim names

### Phase R5: Clarify build-time vs render-time conflict responsibility

Deliverables:

- decide whether sidecar conflict tables are hints, caches, or authoritative precomputations
- add render-time revalidation if needed

Acceptance:

- the unbound default world agrees with build-time conflict output
- conditioned/rendered worlds can explain any divergence

## Implementation Discipline

This plan should be executed as strict TDD plus cleanup, not as an open-ended refactor.

Rules:

1. Before changing behavior, add or update tests that define the intended interface.
2. For pure boundary-refactor phases, require no-behavior-change proof through existing tests and, where useful, golden CLI output comparisons.
3. Do not leave transitional surfaces in place once their callers are migrated.
4. Each phase ends with both green tests and grep-based cleanup checks.
5. Prefer small, phase-scoped patches that can be reverted or reworked independently.

## Test-First Execution Plan

These tests already exist and should be treated as the starting safety net:

- `tests/test_world_model.py`
- `tests/test_argumentation_integration.py`
- `tests/test_bipolar_argumentation.py`
- `tests/test_render_time_filtering.py`
- `tests/test_sensitivity.py`
- `tests/test_graph_export.py`
- `tests/test_cli.py`
- `tests/test_claim_notes.py`
- `tests/test_contexts.py`

Each phase should add focused tests before or alongside implementation changes.

### Phase R1 tests

Add:

- protocol/shape tests for `ArtifactStore`, `Environment`, `RenderPolicy`, and `BeliefSpace`
- repository entrypoint tests for `Repository.store`

Keep green:

- `tests/test_world_model.py`
- `tests/test_cli.py`

Suggested command:

- `uv run pytest tests/test_world_model.py tests/test_cli.py -q`

### Phase R1.5 tests

Add:

- import-surface tests that prove the new public imports are the only supported path
- direct tests that `Repository.store.bind(...)` returns a `BeliefSpace`

Keep green:

- `tests/test_world_model.py`
- `tests/test_claim_notes.py`
- `tests/test_contexts.py`

Cleanup proof:

- `rg -n "from propstore\\.world_model|import propstore\\.world_model|ClaimView" propstore tests`

### Phase R2 tests

Add:

- tests that `RenderPolicy` fully determines resolution behavior
- tests for serialization/comparison/defaults of `RenderPolicy`
- tests that `resolved_value(...)` and direct resolution agree

Keep green:

- `tests/test_world_model.py`
- `tests/test_cli.py`

Suggested command:

- `uv run pytest tests/test_world_model.py tests/test_cli.py -q`

### Phase R3 tests

Add:

- explicit `BeliefSpace` behavior tests for activation, derivation, resolution, explanation, and conflict lookup
- tests that `BoundWorld` no longer relies on private `WorldModel` internals

Keep green:

- `tests/test_world_model.py`
- `tests/test_contexts.py`

### Phase R4 tests

Add:

- in-memory fake store tests for argumentation analyzer entrypoints
- analyzer contract tests for sensitivity and graph export over `BeliefSpace`

Keep green:

- `tests/test_argumentation_integration.py`
- `tests/test_bipolar_argumentation.py`
- `tests/test_render_time_filtering.py`
- `tests/test_sensitivity.py`
- `tests/test_graph_export.py`

Suggested command:

- `uv run pytest tests/test_argumentation_integration.py tests/test_bipolar_argumentation.py tests/test_render_time_filtering.py tests/test_sensitivity.py tests/test_graph_export.py -q`

### Phase R4.5 tests

Add:

- no new behavior tests; this phase is mostly deletion and cleanup

Must pass:

- full targeted suite from earlier phases

Cleanup proof:

- `rg -n "world_model\\.py|ClaimView|Backward-compatibility shim|compatibility shim" propstore tests`

### Phase R5 tests

Add:

- tests comparing stored conflict hints to render-time conflict determination in the unbound case
- tests proving conditioned worlds can diverge from stored hints with explanation

Keep green:

- `tests/test_world_model.py`
- conflict-detector tests
- context-related tests

## Cleanup And Deletion Checklist

The following items must receive an explicit disposition during implementation.

### Delete during this plan

- `propstore/world_model.py`
- `ClaimView` in `propstore/world/types.py`
- compatibility exports in `propstore/world/__init__.py` that exist only to preserve old import shapes

### Reclassify or delete

- `propstore/maxsat_resolver.py`
  Decision required: either promote it to a real analyzer with tests, or remove it from the active architecture.
- `propstore/parameterization_groups.py`
  Decision required: keep as a build/helper module with explicit render-facing contract, or inline/replace it if it is only legacy plumbing.

### Search-based cleanup checks

Run these before considering the phase complete:

- `rg -n "ClaimView" propstore tests`
- `rg -n "from propstore\\.world_model|import propstore\\.world_model" propstore tests`
- `rg -n "_world\\._|_base\\._world|sqlite3\\.Connection" propstore/world propstore/argumentation.py propstore/graph_export.py propstore/sensitivity.py`
- `rg -n "Backward-compatibility shim|compatibility shim" propstore tests`

## Completion Criteria

The plan is only complete when all of the following are true:

- the public naming stack is `Repository.store`, `Environment`, `RenderPolicy`, `BeliefSpace`
- no public shim modules remain
- no caller depends on `ClaimView`
- analyzers do not require raw `sqlite3.Connection`
- the targeted phase suites pass
- cleanup grep checks pass
- the resulting surface is simple enough that further semantic work can build on it without another interface rewrite

## Guardrails Against Premature Collapse

These rules should be enforced throughout the refactor.

1. Do not rename current claim rows into the final semantic truth.
   The new interfaces should be neutral enough to support later assertion/proposition separation.

2. Do not encode proposal inclusion as an ad hoc confidence filter only.
   Proposal inclusion must become an explicit policy dimension.

3. Do not treat current contexts as the final environment model.
   The `Environment` type must exist early to reserve space for assumptions and local theories.

4. Do not let render discard explanation.
   If a value is resolved, the system must still be able to say what alternatives were active and why they lost.

5. Do not let analyzers mutate source truth.
   Argumentation, embeddings, relation inference, and proposal generation remain downstream of repository truth.

6. Do not keep transitional code past the phase that needed it.
   If a shim or alias is introduced for migration convenience, it must be deleted before the phase is considered complete.

## What This Unlocks Later

If this phase is done well, the following become easier:

- proposition/evidence/derivation separation
- proposal-artifact discipline
- ATMS-style assumption environments
- multiple competing renderers over one repository
- non-SQLite backends or in-memory stores
- cleaner research-papers-plugin integration
- paper-native knowledge bootstrapping without source mutation

## Open Questions To Track

These are deliberately deferred, but should remain visible:

- What is the eventual semantic unit: proposition, assertion, evidence record, or layered combination?
- How should proposal artifacts be stored on disk relative to accepted source artifacts?
- How much ATMS machinery belongs in the first environment version?
- Should build-time conflict detection remain as hints, caches, or be recomputed more aggressively at render time?
- When should the knowledge repo be reinitialized relative to this refactor?

## Recommendation

Proceed with the render-first plan, but only under these conditions:

- use neutral names like `ArtifactStore`
- introduce `Environment` early
- make proposal inclusion policy explicit
- preserve analyzer power while moving it behind the new view surface
- document clearly that this phase does not settle the deeper semantic core

That path matches the project’s non-commitment philosophy, preserves the impressive current machinery, and does not foreclose the more principled semantic architecture still to come.
