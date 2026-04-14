# Artifact Boundary Convergence Workstream

Date: 2026-04-13

## Goal

Finish the architectural cut that the artifact-store workstream started.

The target is not just store-backed persistence. The target is one coherent
artifact boundary where:

- artifact schemas live together
- artifact refs, relpaths, branches, and codecs live together
- artifact verification and artifact-code logic live together
- workflow code does not decode YAML, render YAML, compute relpaths, or import
  `msgspec` directly

This workstream is successful only if the remaining "acceptable exceptions"
go to zero.

## End State

Production code should converge to:

1. `propstore/artifacts/` owns artifact persistence, addressing, schema-level
   artifact codecs, and artifact verification.
2. Schema definitions that exist only to describe authored artifacts are no
   longer smeared across workflow modules.
3. CLI and workflow code orchestrate typed operations only.
4. There are zero remaining production `yaml` importers outside the artifact
   boundary.
5. There are zero remaining production git write callsites outside the artifact
   boundary or `repo/git_backend.py`.
6. There are zero remaining caller-local `local_to_artifact` /
   `logical_to_artifact` adapter seams outside the resolver layer.
7. Non-schema workflow code does not import `msgspec`.

## Why The Previous Workstream Was Not Enough

The artifact-store workstream correctly centralized:

- typed artifact persistence
- identity policy
- reference resolution
- transactions

But it still left the package split incoherent:

- `artifact_codes.py` stayed outside `artifacts/`
- authored-document schemas still live in workflow-heavy modules
- CLI/config/output surfaces still own YAML in places
- one raw-file write helper stayed outside the artifact boundary
- one repo-import adapter seam still sat outside the resolver

That leaves the boundary conceptually right but physically incomplete.

## Architectural Direction

Use three layers only:

### 1. Schema Layer

Owns strict authored-document shapes only.

Examples:

- source authored docs
- canonical concept/claim docs
- stance/justification docs
- worldline docs
- merge manifest docs

This layer may import `msgspec`.

### 2. Artifact Boundary

Owns:

- refs
- families
- relpath and branch resolution
- codecs
- prepared artifacts
- transactions
- artifact-code computation
- artifact verification over artifact trees
- indexes and resolvers

This layer may import schema modules and codec helpers.

### 3. Workflow Layer

Owns:

- source authoring workflows
- CLI orchestration
- promotion/import/alignment workflows
- sidecar compilation workflows

This layer should not import `yaml`.
This layer should not import `msgspec`.
This layer should not build relpaths for persisted artifacts.

## Zero-Exception Criteria

Hard criteria:

- `rg -l "^import yaml$|^from yaml import" propstore`
  - result should be only artifact-boundary files
- `rg -n "commit_batch\\(|commit_files\\(" propstore | rg -v "propstore\\\\artifacts\\\\|propstore\\\\repo\\\\git_backend.py"`
  - result count should be `0`
- `rg -n "local_to_artifact|logical_to_artifact|primary_logical_to_artifact" propstore | rg -v "propstore\\\\artifacts\\\\"`
  - result count should be `0`
- `rg -l "^import msgspec$|^from msgspec import" propstore`
  - results should be limited to schema/codec/boundary files

## Execution Order

### Phase 1: Freeze The Boundary In The Plan

Add:

- this workstream plan

Commit immediately.

### Phase 2: Move Artifact Verification Into The Boundary

Move:

- `propstore/artifact_codes.py`

To:

- `propstore/artifacts/codes.py`
- or `propstore/artifacts/verification.py`

Update:

- `source/promote.py`
- `source/finalize.py`
- `cli/verify.py`
- tests

Delete the old top-level module.

### Phase 3: Remove Remaining YAML CLI/Config Exceptions

Targets:

- `cli/repository.py`
- `cli/verify.py`
- `cli/merge_cmds.py`
- `cli/__init__.py`
- `cli/compiler_cmds.py`
- `data_utils.py`

Use:

- typed schema decode for config
- artifact render helpers for YAML output
- artifact-boundary helpers for merge-manifest reads
- `msgspec.yaml` in boundary utilities instead of caller-local `yaml`

### Phase 4: Remove Remaining Non-Boundary Write And Map Exceptions

Targets:

- `source/common.py`
- `repo/repo_import.py`

Do:

- introduce a raw artifact or file family if needed for `notes.md` /
  `metadata.json`
- move the final repo-import local-handle adapter seam into the resolver layer

### Phase 5: Pull Authored Schemas Out Of Workflow-Heavy Modules

Targets likely include:

- `worldline/definition.py`
- `core/concepts.py`
- `form_utils.py`
- source/canonical document modules if their schema types are tangled with
  workflow code

Goal:

- non-schema runtime/workflow modules stop importing `msgspec`
- schema definitions live in boundary-adjacent modules

This is a delete-and-update slice, not a compatibility layer.

### Phase 6: Final Verification And Push

Run:

- targeted suites during each slice
- one broad convergence suite at the end

Then:

- re-run the zero-exception grep checks
- commit each kept slice
- push all convergence commits to `origin/master`

## Failure Modes

- moving files without actually shrinking the boundary surface
- introducing re-export bridges and calling that convergence
- leaving schema classes in mixed workflow modules just because imports still work
- keeping raw write helpers because they are "small"

## Success Bar

The workstream is done only when the repo has an obvious answer to:

1. Where do artifact schemas live?
2. Where do artifact refs/relpaths/codecs live?
3. Where does artifact verification live?
4. Why would workflow code ever import `msgspec` or `yaml`?

If any of those answers are still "well, sort of in several places", the
workstream is not done.
