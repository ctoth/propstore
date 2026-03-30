# Knowledge Path Workstream

Date: 2026-03-29

## Purpose

Turn the read-side knowledge-tree abstraction into a single coherent model and use that cleanup to eliminate the current loader/sidecar path split without confusing it with the other failing-test clusters.

This workstream is deliberately broader than a single abstraction note and narrower than a whole-repo refactor. It is the execution plan for one architectural slice.

## Problem Statement

The current repo has three incompatible read-side models:

- concrete filesystem `Path`
- `TreeReader`
- `LoadedEntry.filepath: Path | None`

That produces:

- dual-signature loaders
- direct path-vs-reader mismatches
- filesystem-only assumptions in code that also needs git-history reads
- optional-path leakage into typed loaded artifacts

The latest cleanup commit:

- `e722ef42c1d5c62ff7d010cce00ffe36027d380a`
- `refactor(repo): add Repository.collection() for optional-path access`

improves call-site ergonomics, but it does not fix the model. It still returns `Path | None`, is still stringly typed, and still cannot unify worktree and git-tree reads.

## Goal

Create one canonical read-side abstraction:

- `KnowledgePath`

and make it the standard input for:

- semantic loaders
- validators
- sidecar build input reads
- git-history semantic reads
- merge/revision readers that currently rely on `TreeReader`

while keeping:

- real mutable `Path`

for:

- CLI edits
- file creation
- worktree writes
- sidecar output writes
- worldline output writes

## Non-Goals

This workstream does not, by itself, solve every currently failing test.

It does not directly fix:

- parameterization lookup-vs-catalog row confusion
- `HypotheticalWorld` graph-capability mismatches
- private helper narrowing regressions

Those remain separate workstreams, though this workstream should remove one entire failure class and simplify later cleanup.

## Current Failure Inventory

The last full suite run reported:

- `7 failed, 2028 passed`

Current failing tests:

1. `tests/test_exception_narrowing_group3.py::TestValueResolverZ3::test_runtime_error_propagates_through_value_resolver`
2. `tests/test_labelled_core.py::test_derived_value_combines_input_labels`
3. `tests/test_relate_opinions.py::TestSidecarPopulatesOpinionColumns::test_opinion_columns_from_stance_yaml`
4. `tests/test_relate_opinions.py::TestSidecarHandlesOldFormatYaml::test_missing_opinion_fields_become_null`
5. `tests/test_semantic_core_phase0.py::test_binding_order_does_not_change_active_or_resolved_semantics`
6. `tests/test_semantic_core_phase0.py::test_empty_hypothetical_overlay_is_identity_transform`
7. `tests/test_semantic_core_phase0.py::test_remove_and_add_inverse_overlay_returns_same_semantic_state`

This workstream directly targets failures `3` and `4`, and the design defects behind them.

## Architecture Decision

Use:

- a small custom read-only virtual path abstraction
- conceptually aligned with `importlib.resources.abc.Traversable`
- not a `pathlib.Path` subclass

Expose it through:

- `Repository.tree(commit: str | None = None) -> KnowledgePath`

### Why This Is The Right Split

`Path` is still correct for mutable filesystem operations.

`KnowledgePath` is correct for read-only semantic knowledge-tree access because:

- the semantic tree may come from the worktree
- or from a git snapshot at an arbitrary commit
- both need the same caller semantics
- neither should force `Path | None` into loaded semantic artifacts

## Desired End State

### Repository Layer

Repository exposes two different kinds of path:

- mutable filesystem paths
- read-only semantic tree paths

Examples:

- `repo.concepts_dir` remains a real `Path`
- `repo.sidecar_path` remains a real `Path`
- `repo.tree() / "claims"` becomes the canonical read input
- `repo.tree(commit=sha) / "concepts" / "foo.yaml"` becomes the canonical historical read input

### Loaded Artifact Layer

Replace:

- `LoadedEntry.filepath: Path | None`

with:

- `LoadedEntry.source_path: KnowledgePath`

That removes the current leak where git-backed loaded files have no real path.

### Loader Layer

Replace dual signatures like:

- `load_concepts(concept_dir: Path | None, *, reader: TreeReader | None = None)`

with:

- `load_concepts(concepts_root: KnowledgePath)`

and similarly for claims and contexts.

### Sidecar / Merge / Validation Reads

All read-only semantic traversal should come from `KnowledgePath`, not `TreeReader`.

## Workstreams

This effort has four concrete streams.

### Stream A: Core Abstraction

Deliverables:

- `propstore/knowledge_path.py`
- `KnowledgePath` protocol or abstract base
- `FilesystemKnowledgePath`
- `GitKnowledgePath`
- `Repository.tree(...)`

Acceptance:

- same path-like traversal works for live worktree and git-history reads
- no semantic reader needs `TreeReader` once migrated

### Stream B: Loader Unification

Deliverables:

- loader signatures rewritten to `KnowledgePath` subtree roots
- helper utilities for YAML traversal moved from `TreeReader` helpers to path-based traversal helpers
- removal of dual `Path`/`reader` signatures

Primary files:

- `propstore/validate.py`
- `propstore/validate_claims.py`
- `propstore/validate_contexts.py`
- `propstore/loaded.py`

Acceptance:

- no loader takes both raw `Path` and `TreeReader`
- no loaded artifact carries `Path | None`

### Stream C: Semantic Reader Migration

Deliverables:

- sidecar build reads migrated
- merge/revision/git-reader consumers migrated
- direct tests moved to the new semantic-tree API

Primary files:

- `propstore/build_sidecar.py`
- `propstore/repo/merge_classifier.py`
- `propstore/repo/structured_merge.py`
- `propstore/cli/compiler_cmds.py`
- `propstore/cli/__init__.py`

Acceptance:

- sidecar no longer distinguishes path-callers from tree-readers
- historical semantic reads use the same abstraction as current reads

### Stream D: TreeReader Deletion

Deliverables:

- remove `TreeReader`
- remove `FilesystemReader`
- remove `GitTreeReader`
- delete temporary compatibility shims

Acceptance:

- read-side semantic code no longer imports `propstore.tree_reader`

## Execution Order

### Phase 0: Baseline and contract capture

Tasks:

- preserve the failing-test inventory in this workstream note
- identify exact `TreeReader` and dual-loader call sites
- identify every remaining `LoadedEntry.filepath` consumer

Done when:

- we have a complete write-up of affected modules and test surfaces

### Phase 1: Add `KnowledgePath`

Tasks:

- create `propstore/knowledge_path.py`
- implement worktree-backed and git-backed variants
- add `Repository.tree(commit=None)`
- add focused tests for traversal equivalence

Done when:

- there is a stable abstraction with parity across worktree and git-tree reads

### Phase 2: Move loaders

Tasks:

- refactor `load_concepts`
- refactor `load_claim_files`
- refactor `load_contexts`
- replace `LoadedEntry.filepath` with `source_path`

Done when:

- loaders accept only `KnowledgePath`
- loaded entries never need `Path | None`

### Phase 3: Migrate sidecar and git-read consumers

Tasks:

- migrate `build_sidecar`
- migrate merge/revision readers
- migrate CLI semantic build/validate paths
- remove `reader.exists(...)` checks in semantic read flows

Done when:

- sidecar can consume a subtree path directly
- worktree and git history use the same read-side interface

### Phase 4: Delete old abstraction

Tasks:

- remove `TreeReader`
- remove compatibility overloads
- update tests

Done when:

- read-only semantic code has one model

## Compatibility Strategy

Use temporary compatibility only when it shortens the migration, not as a permanent design.

Allowed temporarily:

- thin wrapper from old loader signatures into new subtree-path loaders
- temporary compatibility constructors for loaded entries

Not allowed:

- long-lived support for both `TreeReader` and `KnowledgePath`
- preserving `Path | None` on loaded semantic artifacts

## Testing Strategy

### New focused tests

Add focused tests for:

- `KnowledgePath` traversal parity across filesystem and git snapshots
- loader parity across filesystem and git-backed reads
- loaded artifact path identity semantics
- sidecar input traversal via subtree path

### Regression targets for this workstream

At minimum rerun:

- `tests/test_git_backend.py`
- `tests/test_git_properties.py`
- `tests/test_build_sidecar.py`
- `tests/test_claim_notes.py`
- `tests/test_form_algebra.py`
- `tests/test_graph_build.py`
- `tests/test_graph_export.py`
- `tests/test_semantic_repairs.py`
- `tests/test_sensitivity.py`
- `tests/test_worldline.py`
- `tests/test_worldline_properties.py`
- `tests/test_world_model.py`
- `tests/test_relate_opinions.py`

### Full-suite expectation

This workstream should eliminate the sidecar path/reader failure class.

It should not be considered blocked if the remaining non-path failures still exist after the migration.

Those should be tracked explicitly as separate follow-on work.

## Interaction With Other Workstreams

### Follow-on Workstream 1: Parameterization contracts

Need:

- explicit distinction between lookup rows and catalog rows

Current failing tests affected:

- `test_derived_value_combines_input_labels`
- `test_binding_order_does_not_change_active_or_resolved_semantics`

### Follow-on Workstream 2: Semantic-vs-graph capability split

Need:

- explicit graph-capable store protocol
- explicit semantic-query store protocol

Current failing tests affected:

- `test_empty_hypothetical_overlay_is_identity_transform`
- `test_remove_and_add_inverse_overlay_returns_same_semantic_state`

### Follow-on Workstream 3: Helper boundary normalization

Need:

- private helper input normalization or explicit helper contract cleanup

Current failing tests affected:

- `test_runtime_error_propagates_through_value_resolver`

## Milestones

### Milestone 1

`KnowledgePath` exists and repository can provide it.

### Milestone 2

All semantic loaders consume subtree paths.

### Milestone 3

Sidecar and git-history readers use `KnowledgePath`.

### Milestone 4

`TreeReader` is deleted.

## Exit Criteria

This workstream is complete when all of the following are true:

- there is one read-only semantic-tree abstraction
- loaders no longer accept both `Path` and reader inputs
- loaded semantic artifacts no longer carry `Path | None`
- sidecar and git-history semantic reads use the same interface
- `TreeReader` is gone
- the sidecar path/reader regression class is gone

## Recommendation Summary

The correct path forward is not:

- more `exists()` helpers
- more `Path | None`
- more `TreeReader` compatibility

The correct workstream is:

- introduce `KnowledgePath`
- migrate semantic readers onto it
- delete the old split model
- then tackle the remaining non-path failure clusters separately
