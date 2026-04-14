# Artifact Document Schema Convergence Workstream

Date: 2026-04-14
Status: In progress

## Goal

Converge the repo to one correct answer for authored artifact document schemas:

- all pure authored-artifact schema types live under the artifact boundary
- the generic artifact store stays schema-agnostic
- workflow and runtime modules stop owning schema definitions
- mixed modules are split rather than carried forward as "good enough"

This workstream is narrower than the general artifact-boundary convergence
plan. It covers one target surface only: authored document schema placement and
module purity.

## Exact End State

The correct package shape is:

- `propstore/artifacts/`
  - generic artifact boundary code: refs, families, store, transaction,
    codecs, identity, resolution, indexes
- `propstore/artifacts/documents/`
  - pure schema modules for authored repo artifacts only
- `propstore/artifacts/schema.py`
  - shared schema base and strict decode/convert helpers used by artifact
    document modules
- workflow/runtime modules
  - no authored artifact `msgspec.Struct` definitions
  - only runtime/domain logic, orchestration, and conversions

At completion:

1. There is no `propstore/artifact_documents/` package.
2. There are no pure authored-artifact schema modules at top level.
3. `ArtifactStore` remains generic and does not accumulate concrete document
   class definitions.
4. Family declarations import artifact schema types only from
   `propstore.artifacts.documents`.
5. If a former `*_documents.py` module mixed schema with loading/runtime
   helpers, the schema moves under `artifacts/documents/` and the non-schema
   logic is either deleted or moved to a clearly non-schema module.

## Why A Separate Workstream Exists

The broader artifact-boundary plan is directionally correct, but it still
allows this surface to drift because it bundles several targets together:

- artifact verification placement
- remaining YAML exceptions
- write-path cleanup
- schema extraction

That makes it too easy to "make progress" while leaving the schema split
half-finished. This workstream exists to freeze just the document-schema
surface until it reaches the correct state.

## Current Split To Eliminate

Current authored-schema ownership is incoherent:

- extracted artifact schema modules:
  - `propstore/artifact_documents/concepts.py`
  - `propstore/artifact_documents/forms.py`
  - `propstore/artifact_documents/worldlines.py`
- top-level authored schema modules:
  - `propstore/claim_documents.py`
  - `propstore/source_documents.py`
  - `propstore/stance_documents.py`
  - `propstore/source_alignment_documents.py`
  - `propstore/merge_documents.py`
  - `propstore/predicate_documents.py`
  - `propstore/rule_documents.py`
- mixed schema/runtime module:
  - `propstore/context_types.py`
- shared schema helper outside the boundary:
  - `propstore/document_schema.py`

This is the surface to collapse.

## Scope

In scope:

- authored artifact schema module placement
- shared schema-base placement
- import convergence onto one schema package
- splitting mixed schema/runtime modules where needed
- deleting obsolete schema packages and old schema-only modules

Out of scope unless directly required to complete an import cut:

- artifact verification placement
- YAML output cleanup outside schema imports
- repo-import adapter cleanup
- identity-policy redesign
- semantic redesign of claims, concepts, sources, rules, predicates, or
  worldlines

## Architectural Rules

- The store is generic. It loads, saves, renders, and transacts artifacts. It
  does not own concrete schema definitions.
- A schema module is pure if its job is only authored-document shape
  definition plus schema-local helpers.
- Runtime conversion helpers belong outside the schema package.
- Loaded-file wrappers are not justification for leaving schema types in mixed
  modules. Split them or delete them.
- If we control all imports, we do a direct cutover and delete old paths.
- Do not add re-export bridges from old module names to new module names.
- Do not preserve both `artifact_documents` and `artifacts.documents`.

## Target Module Layout

Target package:

- `propstore/artifacts/schema.py`
- `propstore/artifacts/documents/__init__.py`
- `propstore/artifacts/documents/claims.py`
- `propstore/artifacts/documents/concepts.py`
- `propstore/artifacts/documents/contexts.py`
- `propstore/artifacts/documents/forms.py`
- `propstore/artifacts/documents/merge.py`
- `propstore/artifacts/documents/predicates.py`
- `propstore/artifacts/documents/rules.py`
- `propstore/artifacts/documents/source_alignment.py`
- `propstore/artifacts/documents/sources.py`
- `propstore/artifacts/documents/stances.py`
- `propstore/artifacts/documents/worldlines.py`

If a module is not actually an authored artifact schema, it should not be moved
into this package.

## Required Inventory Decisions

Before cutting each module, classify it as exactly one of:

1. Pure schema
2. Mixed schema plus runtime helpers
3. Not an artifact schema and therefore out of this workstream

Expected decisions from current repo state:

- pure schema:
  - `source_documents.py`
  - `stance_documents.py`
  - `source_alignment_documents.py`
  - `merge_documents.py`
  - `artifact_documents/concepts.py`
  - `artifact_documents/forms.py`
  - `artifact_documents/worldlines.py`
- mixed:
  - `claim_documents.py`
  - `predicate_documents.py`
  - `rule_documents.py`
  - `context_types.py`

If any of those classifications turn out to be wrong during execution, record
the corrected classification in this plan before changing scope.

## Execution Order

### Phase 1: Freeze Shared Schema Base

- Move `propstore/document_schema.py` to `propstore/artifacts/schema.py`.
- Update all schema modules to import from the new location.
- Delete `propstore/document_schema.py`.

Success condition:

- there is exactly one shared schema base module
- it lives under `propstore/artifacts/`

### Phase 2: Rename The Extracted Schema Package To The Final Name

- Move `propstore/artifact_documents/` to `propstore/artifacts/documents/`.
- Update all imports.
- Delete the old package.

Success condition:

- no production import of `propstore.artifact_documents` remains

### Phase 3: Move Pure Top-Level Artifact Schema Modules

For each pure module:

- move it into `propstore/artifacts/documents/`
- update imports directly to the new path
- delete the old module in the same slice

Initial pure-module target list:

- `source_documents.py`
- `stance_documents.py`
- `source_alignment_documents.py`
- `merge_documents.py`

Success condition:

- no pure authored-artifact schema module remains at repo top level

### Phase 4: Split Mixed Modules And Extract Schema

For each mixed module:

- extract authored schema structs into `propstore/artifacts/documents/...`
- move remaining runtime/loading helpers into a clearly named non-schema module
  or delete them if artifact-store APIs supersede them
- update all imports directly
- delete the mixed module if nothing valid remains in it

Initial mixed-module target list:

- `claim_documents.py`
- `predicate_documents.py`
- `rule_documents.py`
- `context_types.py`

Success condition:

- no workflow/runtime module defines authored artifact schema structs

### Phase 5: Families And Boundary Cleanup

- update `propstore/artifacts/families.py` and related boundary modules so all
  artifact doc imports come from `propstore.artifacts.documents`
- verify no boundary module imports old schema paths

Success condition:

- the artifact boundary points only at the final schema package

### Phase 6: Zero-Exception Verification

Run and keep the results in this plan:

- `rg -n -F "from propstore.artifact_documents" propstore`
- `rg -n "class .*Document\\(" propstore`
- `rg -n -F "from propstore.document_schema" propstore`
- `rg -n "^import msgspec$|^from msgspec import" propstore`

Expected end-state interpretation:

- `propstore.artifact_documents` imports: zero
- `propstore.document_schema` imports: zero
- `class .*Document(` definitions outside `propstore/artifacts/documents/`:
  zero for authored artifact schemas
- `msgspec` imports outside schema/boundary files: zero

## Anti-Diversion Rules

- This workstream does not widen to verification, YAML CLI cleanup, repo-import
  cleanup, or other artifact-boundary debt just because those are nearby.
- One module family at a time. Do not switch to another surface until the
  current module cut is either kept or fully reverted.
- Diagnostics do not count as progress. A slice counts only when the repo keeps
  a concrete reduction in old schema locations.
- If two consecutive attempts fail to keep a reduction on the same module,
  stop and record the blocker instead of widening scope.
- Do not stop at "good enough". The workstream ends only at the exact end state
  above.

## Non-Negotiable Deletes

The workstream is not complete while any of these still exist:

- `propstore/artifact_documents/`
- `propstore/document_schema.py`
- top-level pure authored artifact schema modules
- re-export bridges preserving old schema import paths

## Verification Approach

During execution:

- use targeted tests for each moved module family
- after each passing targeted run, reread this plan and continue with the next
  unchecked phase
- finish with the grep checks in Phase 6 and one broad targeted convergence run

Use the project test wrapper:

- `powershell -File scripts/run_logged_pytest.ps1 -Label artifact-document-schema ...`

## Success Bar

This workstream is done only when the repo has one obvious answer to each of
these questions:

1. Where do authored artifact schema types live?
2. Where does the shared schema base live?
3. Why would a workflow module define `*Document` structs?
4. Why would any production code still import the old schema paths?

If any answer is still "it depends", this workstream is not done.

## Progress Log

- 2026-04-14: Workstream plan created.
- 2026-04-14: Phase 1 completed.
  - Moved the shared schema base from `propstore/document_schema.py` to
    `propstore/artifacts/schema.py`.
  - Updated production and test imports to the new path.
  - Deleted `propstore/document_schema.py`.
  - Replaced eager re-exports in `propstore/artifacts/__init__.py` with a lazy
    export surface so `propstore.artifacts.schema` does not create a package
    import cycle through `families.py`.
  - Verification: `powershell -File scripts/run_logged_pytest.ps1 -Label artifact-schema-phase1-green tests/test_document_schema.py tests/test_worldline.py::TestWorldlineDefinition tests/test_source_claims.py tests/test_validate_claims.py tests/test_validator.py tests/test_source_promotion_alignment.py tests/test_claim_and_stance_document_enums.py tests/test_build_sidecar.py`
- 2026-04-14: Phase 2 completed.
  - Moved `propstore/artifact_documents/` to
    `propstore/artifacts/documents/`.
  - Updated production and test imports directly to
    `propstore.artifacts.documents`.
  - Verification: `powershell -File scripts/run_logged_pytest.ps1 -Label artifact-schema-phase2 tests/test_artifact_store.py tests/test_artifact_identity_policy.py tests/test_artifact_reference_resolver.py tests/test_source_promotion_alignment.py tests/test_validator.py tests/test_validate_claims.py tests/test_document_schema.py tests/test_worldline.py::TestWorldlineDefinition`
- 2026-04-14: Phase 3 source slice completed.
  - Moved `propstore/source_documents.py` to
    `propstore/artifacts/documents/sources.py`.
  - Updated all direct imports to the new path.
  - Deleted the old top-level module in the same slice.
  - Verification: `powershell -File scripts/run_logged_pytest.ps1 -Label artifact-schema-phase3-sources tests/test_source_claims.py tests/test_source_promotion_alignment.py tests/test_artifact_store.py tests/test_artifact_reference_resolver.py tests/test_repo_snapshot.py tests/test_algorithm_stage_types.py tests/test_claim_and_stance_document_enums.py`
- 2026-04-14: Phase 3 stances slice completed.
  - Moved `propstore/stance_documents.py` to
    `propstore/artifacts/documents/stances.py`.
  - Updated all direct imports to the new path.
  - Deleted the old top-level module in the same slice.
  - Verification: `powershell -File scripts/run_logged_pytest.ps1 -Label artifact-schema-phase3-stances tests/test_source_promotion_alignment.py tests/test_source_relations.py tests/test_claim_and_stance_document_enums.py tests/test_artifact_store.py tests/test_structured_merge_projection.py`
