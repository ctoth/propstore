# Generic Typed Tree Loader And Claim File Convergence Workstream

Date: 2026-04-16
Status: active

## Goal

Collapse the repeated ad hoc YAML-directory loaders onto one generic typed
document-tree loader, then use that foundation to remove `propstore.claim_files`
as a production semantic carrier.

This workstream is the execution plan for the claim-file cleanup surfaced during
review of `propstore.claim_files` versus `propstore.artifacts`.

## Exact End State

At completion:

1. The repo has one generic helper for loading all direct child `*.yaml`
   documents from a `KnowledgePath | Path | None` directory into typed
   `LoadedDocument[T]` objects.
2. Claim, context, predicate, and rule directory loading use that helper.
3. The compiler, sidecar, conflict detector, merge code, and CLIs do not depend
   on `LoadedEntry` or `.data` as claim semantics.
4. Claim semantic APIs consume explicit typed claim inputs: either
   `LoadedDocument[ClaimsFileDocument]`, `ClaimsFileDocument`, or a deliberately
   named semantic input type.
5. Synthetic in-memory claim comparisons are represented as explicit typed
   documents or claim sequences, not fake YAML files.
6. `propstore.claim_files` is deleted.
7. Stale `propstore.claim_documents` imports and comments are deleted or updated.
8. There is no compatibility alias from `propstore.claim_files` or
   `propstore.claim_documents` to the new surfaces.

## Why This Starts With Step 0

The claim-file module currently does two different jobs:

- generic typed directory loading
- claim-specific loaded-file and payload compatibility glue

Deleting the module before separating those jobs would mix mechanical loader
convergence with semantic API redesign. Step 0 removes the mechanical duplicate
loading first. Later phases can then address the real claim API shape directly.

## Current Evidence

Current generic pieces:

- `propstore/artifacts/schema.py::load_document()` loads one typed document.
- `propstore/artifacts/codecs.py::load_yaml_dir()` loads an untyped filesystem
  directory into `(stem, path, dict)` tuples.
- `ArtifactStore.list/load` is generic for artifact families, but it is
  repository/ref based and not a generic arbitrary `KnowledgePath` tree loader.

Current duplicated typed-directory loaders:

- `propstore.claim_files.load_claim_files()`
- `propstore.validate_contexts.load_contexts()`
- `propstore.grounding.loading.load_predicate_files()`
- `propstore.grounding.loading.load_rule_files()`

Current claim-specific compatibility surfaces to eliminate:

- `LoadedClaimFile.data`
- `ClaimFileInput = LoadedClaimFile | LoadedEntry`
- `coerce_loaded_claim_files()`
- conflict detector synthetic `LoadedEntry` inputs
- scripts importing deleted `propstore.claim_documents`

## Architectural Rules

- Do not add compatibility shims, re-export aliases, fallback readers, or old/new
  dual paths.
- If a production interface changes, update every caller in the same slice.
- Boundary IO may decode YAML, but core claim semantics must be typed before
  entering compiler, sidecar, conflict, merge, or world runtime paths.
- Generic loading code must stay schema-agnostic.
- Artifact-family store operations remain ref/repo operations; the new tree
  loader is for loading typed documents from a concrete tree directory.
- Synthetic test/runtime claims must use a first-class typed input surface, not
  fake file envelopes.
- Each phase must end with either a kept reduction or a revert of that phase.

## Step 0: Generic Typed Document Tree Loader

Goal: introduce the generic loader and make existing directory loaders thin
wrappers over it without changing semantic APIs.

Target API:

```python
def load_document_dir(
    directory: KnowledgePath | Path | None,
    document_type: type[TDocument],
    *,
    wrapper: Callable[[LoadedDocument[TDocument]], TLoaded] | None = None,
) -> list[LoadedDocument[TDocument]] | list[TLoaded]:
    ...
```

Implementation requirements:

1. Place the helper at the typed document boundary, preferably
   `propstore/artifacts/schema.py` unless a clearer small module is introduced
   under `propstore/artifacts/`.
2. Accept `KnowledgePath | Path | None`.
3. Return `[]` when the input is `None` or not a directory.
4. Derive `knowledge_root` as `directory.parent if directory.name else
   directory`, matching existing loaders.
5. Load only direct child files with suffix `.yaml`.
6. Sort entries deterministically by filename or POSIX path before loading.
7. Decode each file with existing strict `load_document()`.
8. If `wrapper` is provided, return wrapper instances; otherwise return
   `LoadedDocument[TDocument]`.
9. Do not special-case claim files.

Required rewrites in this step:

- `propstore.claim_files.load_claim_files()`
- `propstore.validate_contexts.load_contexts()`
- `propstore.grounding.loading.load_predicate_files()`
- `propstore.grounding.loading.load_rule_files()`

Required tests:

- missing directory returns `[]`
- `None` returns `[]`
- empty directory returns `[]`
- non-YAML files and directories are skipped
- direct child YAML files are loaded in deterministic order
- source metadata is preserved: filename, source path, knowledge root
- wrapper callback receives the loaded document and controls return type
- existing git-backed `KnowledgePath` loading still works

Verification:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label typed-tree-loader tests/test_document_schema.py tests/test_git_backend.py::test_load_claim_files_from_git_tree tests/test_contexts.py tests/test_predicate_documents.py tests/test_rule_documents.py tests/test_grounding_loading.py
```

Exit criteria:

- the four existing loaders are wrappers over the generic helper
- no behavior change outside deterministic ordering
- targeted tests pass

## Phase 1: Inventory Claim-File Consumers

Goal: freeze the exact remaining claim-file dependency surface before changing
claim semantics.

Tasks:

1. Run:

   ```powershell
   rg -n -F "propstore.claim_files" propstore tests scripts
   rg -n -F "LoadedClaimFile" propstore tests scripts
   rg -n -F "ClaimFileInput" propstore tests scripts
   rg -n -F "claim_file.data" propstore tests scripts
   rg -n -F "LoadedEntry(" propstore tests scripts
   rg -n -F "propstore.claim_documents" propstore tests scripts plans
   ```

2. Classify every production hit into one of these buckets:

   - typed document loading
   - file metadata needed for diagnostics or artifact refs
   - raw payload bridge
   - synthetic in-memory claim comparison
   - stale import/comment

3. Update this workstream with the inventory and the chosen next slice.

Exit criteria:

- every production use has an assigned replacement strategy
- no implementation changes unless they are direct stale-script fixes

## Phase 2: Introduce Explicit Claim Input Surface

Goal: replace fake file envelopes and `LoadedEntry` claim inputs with a direct
typed semantic surface.

Candidate target:

```python
@dataclass(frozen=True)
class LoadedClaimsFile:
    filename: str
    source_path: KnowledgePath | None
    knowledge_root: KnowledgePath | None
    document: ClaimsFileDocument
```

or, if no claim-specific subclass is needed:

```python
LoadedDocument[ClaimsFileDocument]
```

Decision rule:

- Use plain `LoadedDocument[ClaimsFileDocument]` if all callers only need
  metadata plus `.document`.
- Add a claim-specific dataclass only if it removes real repeated logic without
  preserving `.data` compatibility.

Tasks:

1. Change compiler context and compiler passes to accept the chosen typed input.
2. Replace `.claims`, `.source_paper`, `.stage`, and `.data` access with
   explicit `document` access or small pure functions.
3. Make validation accept only the chosen typed input surface.
4. Delete `ClaimFileInput` and `LoadedEntry` coercion from validation paths.

Verification:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label claim-typed-input tests/test_claim_compiler.py tests/test_validate_claims.py tests/test_claim_notes.py tests/test_algorithm_stage_types.py
```

Exit criteria:

- compiler and validation no longer import `LoadedClaimFile`, `ClaimFileInput`,
  or `LoadedEntry`
- no `.data` access remains in compiler or validation production code

## Phase 3: Conflict Detector Claim Input Cutover

Goal: make conflict detection operate on explicit claim documents or claim
records instead of file-like envelopes.

Tasks:

1. Replace `ClaimFileInput` parameters in `propstore/conflict_detector/` with a
   typed input that represents exactly what conflict detection needs.
2. Preserve source-paper handling explicitly. If source defaults are needed,
   carry them as a named field rather than by reading file-level YAML payloads.
3. Replace synthetic `LoadedEntry` creation in:

   - `propstore.repo.merge_classifier`
   - `propstore.world.bound`
   - conflict detector tests

4. Delete `claim_file_claim_payloads()`,
   `claim_file_default_source_paper()`, and `claim_payload_source_paper()`.

Verification:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label conflict-claim-input tests/test_conflict_detector.py tests/test_param_conflicts.py tests/test_property.py tests/test_contexts.py tests/test_equation_comparison_properties.py tests/test_z3_conditions.py tests/test_merge_classifier.py tests/test_world_bound_conflicts_cache.py
```

Exit criteria:

- conflict detector production code has no `LoadedEntry` or claim-file envelope
  dependency
- source-paper disjointness behavior is covered by tests

## Phase 4: Sidecar, Merge, And Artifact Code Cutover

Goal: update the remaining production claim-file consumers to the explicit typed
claim input surface.

Tasks:

1. Update `propstore.sidecar.build` and `propstore.sidecar.claims`.
2. Update `propstore.sidecar.claim_utils`.
3. Update `propstore.repo.structured_merge`.
4. Update `propstore.artifacts.codes`.
5. Update claim-related CLI commands.
6. Replace raw `.data` payload mutation with typed payload conversion at IO
   boundaries only.

Verification:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label sidecar-merge-claim-input tests/test_build_sidecar.py tests/test_graph_export.py tests/test_repo_merge_object.py tests/test_merge_classifier.py tests/test_sensitivity.py tests/test_world_model.py tests/test_verify_cli.py
```

Exit criteria:

- no production `.data` access remains for claim files
- sidecar and merge tests pass

## Phase 5: Delete Obsolete Modules And Stale References

Goal: remove old claim-file and claim-document module surfaces.

Tasks:

1. Delete `propstore/claim_files.py`.
2. Fix or delete scripts that import `propstore.claim_documents`.
3. Update stale comments in:

   - `propstore/artifacts/documents/rules.py`
   - `propstore/artifacts/documents/predicates.py`
   - tests that reference `propstore/claim_documents.py`

4. Run import-surface checks:

   ```powershell
   rg -n -F "propstore.claim_files" propstore tests scripts plans
   rg -n -F "propstore.claim_documents" propstore tests scripts plans
   rg -n -F "LoadedClaimFile" propstore tests scripts
   rg -n -F "ClaimFileInput" propstore tests scripts
   rg -n -F "claim_file.data" propstore tests scripts
   ```

Exit criteria:

- all five searches return zero production hits
- no compatibility module replaces the deleted module

## Phase 6: Full Verification

Goal: prove the direct cutover is complete.

Run:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label claim-file-convergence-full
```

Then rerun the import-surface checks from Phase 5.

Completion criteria:

- full suite passes
- import-surface checks are clean
- this workstream is updated with dated completion notes
- every phase is completed or explicitly deferred by the user

## Execution Notes

- After each passing targeted suite, reread this plan and continue to the next
  unchecked task.
- Passing tests do not complete the workstream while old production claim-file
  paths remain.
- If a phase discovers that a proposed target type is wrong, update this plan
  with the evidence before implementing the revised target.
- Do not broaden into unrelated artifact-store or claim-identity redesign unless
  a listed phase is blocked without it.
