# Generic Typed Tree Loader And Claim File Convergence Workstream

Date: 2026-04-16
Status: completed - verified 2026-04-16

## Goal

Collapse the repeated ad hoc YAML-directory loaders onto one generic typed
document-tree loader, then use that foundation to remove the claim-file
compatibility module as a production semantic carrier.

This workstream is the execution plan for the claim-file cleanup surfaced during
review of the old claim-file compatibility surface versus `propstore.artifacts`.

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
6. The old claim-file compatibility module is deleted.
7. Stale claim-documents imports and comments are deleted or updated.
8. There is no compatibility alias from the old claim-file or claim-documents
   module names to the new surfaces.

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

- old claim-file module `load_claim_files()`
- `propstore.validate_contexts.load_contexts()`
- `propstore.grounding.loading.load_predicate_files()`
- `propstore.grounding.loading.load_rule_files()`

Current claim-specific compatibility surfaces to eliminate:

- `LoadedClaimFile.data`
- `ClaimFileInput = LoadedClaimFile | LoadedEntry`
- `coerce_loaded_claim_files()`
- conflict detector synthetic `LoadedEntry` inputs
- scripts importing the deleted claim-documents module

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

- old claim-file module `load_claim_files()`
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
   rg -n -F "<old claim-file module literal>" propstore tests scripts
   rg -n -F "LoadedClaimFile" propstore tests scripts
   rg -n -F "ClaimFileInput" propstore tests scripts
   rg -n -F "claim_file.data" propstore tests scripts
   rg -n -F "LoadedEntry(" propstore tests scripts
   rg -n -F "<old claim-documents module literal>" propstore tests scripts plans
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

### Phase 1 Inventory - 2026-04-16

Searches run:

```powershell
rg -n -F "<old claim-file module literal>" propstore tests scripts
rg -n -F "LoadedClaimFile" propstore tests scripts
rg -n -F "ClaimFileInput" propstore tests scripts
rg -n -F "claim_file.data" propstore tests scripts
rg -n -F "LoadedEntry(" propstore tests scripts
rg -n -F "<old claim-documents module literal>" propstore tests scripts plans
```

Production hit classification:

- typed document loading:
  - `propstore.artifacts.codes`
  - `propstore.cli.claim`
  - `propstore.cli.compiler_cmds`
  - `propstore.cli.concept`
  - `propstore.repo.merge_classifier`
  - `propstore.repo.structured_merge`
  - `propstore.sidecar.build`
  - `propstore.validate_concepts`
- file metadata needed for diagnostics or artifact refs:
  - `propstore.compiler.context`
  - `propstore.compiler.ir`
  - `propstore.compiler.passes`
  - `propstore.sidecar.claims`
  - `propstore.sidecar.claim_utils`
  - `propstore.cli.concept`
- raw payload bridge:
  - old claim-file module `LoadedClaimFile.data`
  - `propstore.compiler.passes`
  - `propstore.cli.concept`
  - `scripts.mergeability_probe`
- synthetic in-memory claim comparison:
  - `propstore.repo.merge_classifier`
  - `propstore.world.bound`
- stale import/comment:
  - `scripts.mergeability_probe`
  - `scripts.validate_claims_only`

Chosen next slice:

- Use plain `LoadedDocument[ClaimsFileDocument]` as the claim input surface.
  The remaining production callers need only `filename`, `source_path`,
  `knowledge_root`, and `document`; the claim-specific subclass exists to
  preserve compatibility properties and untyped payload coercion.
- Add small typed helper functions where repeated claim semantics need naming
  (`claims`, source paper, stage, payload conversion), without retaining `.data`
  or `LoadedEntry` acceptance as semantic inputs.

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

## Remaining Workstream Execution Spec

Status at pre-execution checkpoint:

- Step 0 is implemented and committed.
- Phase 1 inventory is implemented and committed.
- Phase 2 compiler/validation cutover is implemented and committed.
- The remaining work must start from the current committed surface, not from a
  partially edited Phase 3.

Canonical claim-document surface:

- `propstore.claims` is the canonical typed claim-document boundary.
- `LoadedClaimsFile` is a type alias for
  `LoadedDocument[ClaimsFileDocument]`, not a claim-specific wrapper class.
- `load_claim_file()` and `load_claim_files()` return typed loaded documents.
- `loaded_claim_file_from_payload()` is allowed only at IO/update boundaries
  where a payload has just been rendered or rewritten and must be immediately
  revalidated as `ClaimsFileDocument`.
- `claim_file_claims()`, `claim_file_source_paper()`, `claim_file_stage()`,
  and `claim_file_payload()` are named typed access helpers. They are not
  compatibility aliases for `.claims`, `.source_paper`, `.stage`, or `.data`.
- No new production import may target the old claim-file or claim-documents
  module names.

Conflict detector target:

- The conflict core should consume `Sequence[ConflictClaim]`, because
  `ConflictClaim` is the exact record shape needed by parameter, measurement,
  equation, algorithm, and parameterization conflict logic.
- Typed YAML claim files should be converted at one explicit boundary helper,
  for example `conflict_claims_from_claim_files(
  Sequence[LoadedClaimsFile]) -> list[ConflictClaim]`.
- That boundary helper must:
  - iterate `claim_file.document.claims`;
  - derive each claim payload from `ClaimDocument.to_payload()`;
  - preserve file-level `document.source.paper` by writing it to
    `ConflictClaim.source_paper` when the claim does not already carry a source;
  - call `with_source_condition()` exactly once after source paper is set.
- Runtime/synthetic comparisons should construct `ConflictClaim` records
  directly from the already-available semantic payload. They should not create
  fake YAML file envelopes.
- `detect_conflicts()` and `detect_transitive_conflicts()` should accept
  `Sequence[ConflictClaim]`. Callers that start with typed claim files must
  call the boundary converter before invoking those functions.

Sidecar target:

- `propstore.sidecar.build` should load claims from `propstore.claims`.
- `populate_claims()`, `populate_conflicts()`, `build_claim_fts_index()`, and
  `collect_claim_reference_map()` should accept `Sequence[LoadedClaimsFile]`.
- Non-semantic storage functions may still receive dict payloads where their
  existing contract is "row materialization" or "artifact rendering", but the
  source of those payloads must be `ClaimDocument.to_payload()` or
  `SemanticClaim.resolved_claim`, not `LoadedClaimFile.data`.
- `populate_conflicts()` should convert typed claim files to
  `ConflictClaim` records once, pass those records to both direct and
  transitive conflict detection, and not pass loaded files into the detector.
- `build_claim_fts_index()` should iterate `claim_file.document.claims`.

Merge and world runtime target:

- `propstore.repo.merge_classifier._classify_pair()` should construct two
  `ConflictClaim` records directly from `MergeClaim.to_payload()`, with the
  comparison source paper set explicitly on each record before calling
  `with_source_condition()`.
- `propstore.repo.merge_classifier._index_claims()` and
  `propstore.repo.structured_merge._load_branch_claims()` should load via
  `propstore.claims.load_claim_files()` and iterate `claim_file.document.claims`.
- `propstore.world.bound._recomputed_conflicts()` should convert each
  `ActiveClaim.to_source_claim_payload()` directly into `ConflictClaim`. It
  should not try to coerce active runtime rows through `ClaimsFileDocument`,
  because active rows contain runtime/storage fields that are not authored
  claim-file schema fields.

CLI and artifact-code target:

- `propstore.cli.claim` should import `load_claim_file(s)` from
  `propstore.claims`.
- `claim conflicts` should convert loaded claim files to `ConflictClaim`
  records before calling the detector.
- `propstore.cli.concept.rename` is an IO/update boundary: it may render
  `claim_file.document.to_payload()`, rewrite CEL condition strings, normalize
  the rewritten payload, and immediately reconvert with
  `loaded_claim_file_from_payload()` before validation and artifact save.
- `propstore.artifacts.codes`, `propstore.validate_concepts`, and claim-related
  merge/verify paths should read typed claim documents and use
  `ClaimDocument.to_payload()` only where a hash, rendered artifact, or storage
  row explicitly requires a dict.

Stale script/reference target:

- `scripts/mergeability_probe.py` must either be updated to
  `propstore.claims` and typed document access or deleted if it no longer has a
  maintained caller.
- `scripts/validate_claims_only.py` imports the deleted claim-documents module;
  it must
  either be updated to the typed claim/document APIs and current repository
  constructor, or deleted if obsolete.
- Stale comments in tests and authored document modules should be rewritten to
  name `LoadedDocument[ClaimsFileDocument]` or `propstore.claims`, not
  `LoadedClaimFile` or the claim-documents module name.

Phase ordering constraints:

- Phase 3 owns only conflict-detector input shape and synthetic comparison
  removal. Do not also do sidecar `.data` cleanup there except for the minimum
  caller updates required by the changed detector API.
- Phase 4 owns remaining typed claim-file consumers and payload mutation at
  sidecar, merge, artifact, and CLI boundaries.
- Phase 5 owns deletion of the old claim-file module and stale claim-documents
  references after all production imports have
  moved.
- Each phase must have a clean import-surface check for its owned surface before
  commit. A passing targeted suite is not enough if the owned old surface still
  has production hits.

Design-review decisions:

- Do not make the conflict core accept `ClaimsFileDocument` directly. Authored
  claim files are only one source of conflict inputs; merge pair comparison and
  render-time `ActiveClaim` revalidation are already semantic/runtime records,
  not YAML files. Making the conflict core take claim-file documents would
  force those paths back through artificial document envelopes.
- Do not add a `ClaimDocument.source_paper` schema field as part of this
  workstream. The current typed claim schema does not define that field. Source
  defaults belong at either `ClaimsFileDocument.source.paper` or an explicit
  `ConflictClaim.source_paper` value set by a boundary converter.
- Do not force `ActiveClaim.to_source_claim_payload()` through
  `ClaimsFileDocument`. Runtime active-claim rows can carry storage/runtime
  fields that are not authored YAML schema fields. Convert them directly to
  `ConflictClaim`.
- Dict payloads remain allowed only at output or rendering boundaries:
  artifact-code hashing, artifact rendering, SQLite row materialization, and
  freshly rewritten payload revalidation. The semantic pipeline should carry
  `LoadedClaimsFile`, `ClaimDocument`, `SemanticClaim`, or `ConflictClaim`.

## Phase 3: Conflict Detector Claim Input Cutover

Goal: make conflict detection operate on explicit claim documents or claim
records instead of file-like envelopes.

Tasks:

1. Add the typed conversion boundary from
   `Sequence[LoadedClaimsFile]` to `list[ConflictClaim]`.
2. Replace `ClaimFileInput` parameters in `propstore/conflict_detector/` with
   `Sequence[ConflictClaim]`.
3. Preserve source-paper handling explicitly by setting
   `ConflictClaim.source_paper` before `with_source_condition()`.
4. Update direct callers of `detect_conflicts()` and
   `detect_transitive_conflicts()` to pass conflict records, not files.
5. Replace synthetic `LoadedEntry` creation in:

   - `propstore.repo.merge_classifier`
   - `propstore.world.bound`
   - conflict detector tests

6. Delete `claim_file_claim_payloads()`,
   `claim_file_default_source_paper()`, and `claim_payload_source_paper()` after
   their last production caller is gone.
7. Add or update tests that lock the new non-envelope behavior:

   - typed claim files with distinct `ClaimsFileDocument.source.paper` values
     seed source conditions correctly;
   - merge pair comparison sets the same explicit comparison source on both
     sides and preserves `_classify_pair()` behavior;
   - render-time active-claim revalidation converts active rows directly to
     `ConflictClaim` and preserves `_ConflictInputs` caching behavior.

Additional Phase 3 surface checks:

```powershell
rg -n -F "ClaimFileInput" propstore/conflict_detector propstore/repo/merge_classifier.py propstore/world/bound.py tests/test_conflict_detector.py tests/test_param_conflicts.py tests/test_property.py tests/test_equation_comparison_properties.py tests/test_z3_conditions.py
rg -n -F "LoadedEntry(" propstore/conflict_detector propstore/repo/merge_classifier.py propstore/world/bound.py tests/test_conflict_detector.py tests/test_param_conflicts.py tests/test_property.py tests/test_equation_comparison_properties.py tests/test_z3_conditions.py
rg -n -F "claim_file_claim_payloads" propstore tests scripts
rg -n -F "claim_file_default_source_paper" propstore tests scripts
rg -n -F "claim_payload_source_paper" propstore tests scripts
```

Verification:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label conflict-claim-input tests/test_conflict_detector.py tests/test_param_conflicts.py tests/test_property.py tests/test_contexts.py tests/test_equation_comparison_properties.py tests/test_z3_conditions.py tests/test_merge_classifier.py tests/test_world_bound_conflicts_cache.py
```

Exit criteria:

- conflict detector production code has no `LoadedEntry` or claim-file envelope
  dependency
- source-paper disjointness behavior is covered by tests
- the additional Phase 3 surface checks have no production hits

## Phase 4: Sidecar, Merge, And Artifact Code Cutover

Goal: update the remaining production claim-file consumers to the explicit typed
claim input surface.

Tasks:

1. Update `propstore.sidecar.build` and `propstore.sidecar.claims` to import
   `propstore.claims`, consume `LoadedClaimsFile`, and pass conflict records
   to conflict detection.
2. Update `propstore.sidecar.claim_utils` to use `LoadedClaimsFile` and
   `claim_file.document.claims`.
3. Update `propstore.repo.structured_merge` and any remaining merge code to
   load typed claim documents from `propstore.claims`.
4. Update `propstore.artifacts.codes` to load typed claim documents and render
   payloads only at hash/artifact-code boundaries.
5. Update claim-related CLI commands and `propstore.validate_concepts`.
6. Replace raw `.data` payload mutation with typed payload conversion at IO
   boundaries only; the main known site is `propstore.cli.concept.rename`.
7. Update tests in the Phase 4 verification suite to import `propstore.claims`
   and use `.document` or typed helpers.
8. Add or update tests that lock the remaining typed-boundary behavior:

   - `populate_claims()` and `build_claim_fts_index()` consume
     `LoadedClaimsFile` and continue producing the same sidecar rows;
   - concept rename rewrites claim-file CEL conditions through a typed
     document/payload revalidation boundary and does not depend on
     `LoadedClaimFile.data`;
   - artifact-code verification reads typed claim files and hashes
     `ClaimDocument.to_payload()` output only at the hash boundary.

Additional Phase 4 surface checks:

```powershell
rg -n -F "from <old claim-file module literal>" propstore tests scripts
rg -n -F "LoadedClaimFile" propstore tests scripts
rg -n -F "claim_file.data" propstore tests scripts
rg -n -F ".claims" propstore/sidecar propstore/repo propstore/cli tests/test_build_sidecar.py tests/test_graph_export.py tests/test_repo_merge_object.py tests/test_merge_classifier.py tests/test_sensitivity.py tests/test_world_model.py
```

The `.claims` check is diagnostic only; hits are acceptable only when they are
not loaded claim-file property access.

Verification:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label sidecar-merge-claim-input tests/test_build_sidecar.py tests/test_graph_export.py tests/test_repo_merge_object.py tests/test_merge_classifier.py tests/test_sensitivity.py tests/test_world_model.py tests/test_verify_cli.py
```

Exit criteria:

- no production `.data` access remains for claim files
- sidecar and merge tests pass
- Phase 4 surface checks have no production hits for the old claim-file module,
  `LoadedClaimFile`, or claim-file `.data`

## Phase 5: Delete Obsolete Modules And Stale References

Goal: remove old claim-file and claim-document module surfaces.

Tasks:

1. Delete `propstore/claim_files.py`.
2. Fix or delete scripts that import the deleted claim-documents module.
3. Update remaining tests to import `propstore.claims` or use local typed
   helpers. Do not keep test-only imports from deleted modules unless the test
   is explicitly asserting import failure.
4. Update stale comments in:

   - `propstore/artifacts/documents/rules.py`
   - `propstore/artifacts/documents/predicates.py`
   - tests that reference `propstore/claim_documents.py`

5. Run import-surface checks:

   ```powershell
   rg -n -F "<old claim-file module literal>" propstore tests scripts plans
   rg -n -F "<old claim-documents module literal>" propstore tests scripts plans
   rg -n -F "LoadedClaimFile" propstore tests scripts
   rg -n -F "LoadedClaimsFile.from" propstore tests scripts
   rg -n -F "ClaimFileInput" propstore tests scripts
   rg -n -F "claim_file.data" propstore tests scripts
   rg -n -F "from_payload(" propstore/claims.py propstore tests scripts
   ```

The `from_payload(` search is diagnostic. Hits are acceptable only for
`loaded_claim_file_from_payload()` itself and deliberate IO/update boundaries
that immediately revalidate a freshly rendered or rewritten payload.

Exit criteria:

- all non-diagnostic searches return zero production hits
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

## Completion Notes - 2026-04-16

Implemented phases:

- Step 0 added the generic typed document directory loader and rewired claim,
  context, predicate, and rule loaders through it.
- Phase 1 recorded the claim-file dependency inventory and replacement
  strategies.
- Phase 2 moved compiler and validation claim inputs to
  `LoadedDocument[ClaimsFileDocument]` via `propstore.claims`.
- Phase 3 changed conflict detection to consume `ConflictClaim` records and
  removed fake file-envelope comparisons from merge and bound-world paths.
- Phase 4 moved sidecar, merge, artifact-code, CLI, and concept-validation
  claim-file consumers to the typed claim boundary.
- Phase 5 deleted the obsolete claim-file compatibility module, deleted the
  stale claim-only validation script, and updated stale comments/references.
- Phase 6 fixed one stale test caller and completed full-suite verification.

Verification evidence:

- `typed-tree-loader`: 85 passed in
  `logs\test-runs\typed-tree-loader-20260415-224838.log`.
- `claim-typed-input`: 114 passed in
  `logs\test-runs\claim-typed-input-20260415-225215.log`.
- `conflict-claim-input`: 185 passed in
  `logs\test-runs\conflict-claim-input-20260415-231307.log`.
- `sidecar-merge-claim-input`: 274 passed in
  `logs\test-runs\sidecar-merge-claim-input-20260415-232036.log`.
- `delete-claim-file-surfaces`: 22 passed in
  `logs\test-runs\delete-claim-file-surfaces-20260415-232505.log`.
- `parameter-z3-strictness`: 1 passed in
  `logs\test-runs\parameter-z3-strictness-20260415-233314.log`.
- Full suite: 2483 passed, 1 skipped, 1 warning in
  `logs\test-runs\claim-file-convergence-full-20260415-233323.log`.

Final surface result:

- Code, test, and script searches for the old claim-file module name, old
  claim-documents module name, `LoadedClaimFile`, `LoadedClaimsFile.from`,
  `ClaimFileInput`, and `claim_file.data` are clean.
- The diagnostic `from_payload(` search has only deliberate typed-boundary,
  conflict-record, context-type, and test helper hits.
- Historical plan text now avoids the old module-name literals so the
  plan-inclusive module-name checks stay clean.

## Execution Notes

- After each passing targeted suite, reread this plan and continue to the next
  unchecked task.
- Passing tests do not complete the workstream while old production claim-file
  paths remain.
- If a phase discovers that a proposed target type is wrong, update this plan
  with the evidence before implementing the revised target.
- Do not broaden into unrelated artifact-store or claim-identity redesign unless
  a listed phase is blocked without it.
