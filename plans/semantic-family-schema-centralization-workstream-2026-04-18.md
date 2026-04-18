# Semantic Family Schema Centralization Workstream

Date: 2026-04-18

## Purpose

Centralize repository schema ownership in semantic family definitions. A family root
such as `concepts`, path suffix such as `.yaml`, collection field such as `claims`,
and family-specific filename codec must be declared once and consumed everywhere
through that family definition.

This is not a helper shuffle. The acceptance condition is deletion of old helper
surfaces and path literals from production code, with tests that fail if schema
knowledge is reintroduced outside the family declaration.

## Current Source Of Truth

`propstore/artifacts/semantic_families.py` already declares the canonical family
roots:

- `claim`: root `claims`, collection field `claims`
- `concept`: root `concepts`
- `context`: root `contexts`
- `form`: root `forms`
- `predicate`: root `predicates`, collection field `predicates`
- `rule`: root `rules`, collection field `rules`
- `stance`: root `stances`, collection field `stances`
- `worldline`: root `worldlines`

That file is currently only a partial source of truth. Path construction,
path parsing, ref listing, initialization, and several loaders still encode the
same schema elsewhere.

## Verified Duplicate Helpers To Delete

These were found by reading `propstore/artifacts/refs.py` and
`propstore/artifacts/families.py`, then searching production callers.

### `propstore/artifacts/refs.py`

Delete these relpath helpers and remove them from `propstore/artifacts/__init__.py`
exports:

- `worldline_relpath(name)` at line 24
- `canonical_source_relpath(name)` at line 28
- `claims_file_relpath(name)` at line 32
- `micropubs_file_relpath(name)` at line 36
- `concept_file_relpath(name)` at line 40
- `justifications_file_relpath(name)` at line 44
- `predicate_file_relpath(name)` at line 48
- `rule_file_relpath(name)` at line 52
- `stance_file_relpath(source_claim)` at line 56
- `source_claim_from_stance_path(path)` at line 60

Keep the ref dataclasses unless the family definition can own ref construction
cleanly enough to make them unnecessary. The first pass should remove path
knowledge from `refs.py`; it does not need to remove typed refs.

The non-canonical source/proposal/merge helpers are also schema declarations and
must be moved to a family/layout definition, not left as free helpers:

- `STANCE_PROPOSAL_BRANCH = "proposal/stances"` at line 7
- `source_branch_name(name)` at line 16
- `source_finalize_relpath(name)` at line 20
- `concept_alignment_relpath(slug)` at line 68
- `merge_manifest_relpath()` at line 72

### `propstore/artifacts/families.py`

Delete per-family artifact path builders and replace them with family-derived
resolution:

- `_context_artifact` at line 172
- `_form_artifact` at line 185
- `_worldline_artifact` at line 192
- `_canonical_source_artifact` at line 199
- `_claims_file_artifact` at line 206
- `_micropubs_file_artifact` at line 213
- `_concept_file_artifact` at line 220
- `_justifications_file_artifact` at line 227
- `_predicate_file_artifact` at line 234
- `_rule_file_artifact` at line 241
- `_stance_file_artifact` at line 248
- `_proposal_stance_artifact` at line 255
- `_concept_alignment_artifact` at line 263
- `_merge_manifest_artifact` at line 270

Delete generic helpers that still take schema strings from callers:

- `_list_yaml_refs_in_directory` at line 278
- `_list_stance_refs_in_directory` at line 306
- `_yaml_path_ref` at line 331
- `_ref_from_loaded_source_path` at line 339

Delete per-family ref parsing/listing wrappers:

- `_context_ref_from_path` at line 352
- `_form_ref_from_path` at line 356
- `_claims_file_refs` at line 360
- `_claims_file_ref_from_path` at line 374
- `_claims_file_ref_from_loaded` at line 378
- `_micropubs_file_refs` at line 386
- `_micropubs_file_ref_from_path` at line 400
- `_micropubs_file_ref_from_loaded` at line 404
- `_concept_file_refs` at line 412
- `_concept_file_ref_from_path` at line 426
- `_concept_file_ref_from_loaded` at line 430
- `_predicate_file_refs` at line 438
- `_predicate_file_ref_from_path` at line 452
- `_predicate_file_ref_from_loaded` at line 456
- `_rule_file_refs` at line 464
- `_rule_file_ref_from_path` at line 478
- `_rule_file_ref_from_loaded` at line 482
- `_stance_file_ref_from_path` at line 490
- `_proposal_stance_refs` at line 494
- `_worldline_ref_from_path` at line 503
- `_worldline_refs` at line 507

Delete source-branch filename helpers or derive them from source artifact family
definitions:

- `_source_document_artifact` at line 81: `source.yaml`
- `_source_notes_artifact` at line 85: `notes.md`
- `_source_metadata_artifact` at line 89: `metadata.json`
- `_source_concepts_artifact` at line 93: `concepts.yaml`
- `_source_claims_artifact` at line 97: `claims.yaml`
- `_source_micropubs_artifact` at line 101: `micropubs.yaml`
- `_source_justifications_artifact` at line 105: `justifications.yaml`
- `_source_stances_artifact` at line 109: `stances.yaml`
- `_source_finalize_report_artifact` at line 113: `merge/finalize/{slug}.yaml`

## Production Literal Inventory To Convert

The first conversion pass must handle these production path literals. Payload
field strings such as claim data field `concepts` are not automatically path
schema, but path usages must disappear.

### Canonical semantic roots

`concepts` path usages:

- `propstore/concept_ids.py`: lines 58-59
- `propstore/compiler/workflows.py`: lines 102, 203, 283, 298
- `propstore/compiler/context.py`: line 136
- `propstore/core/aliases.py`: line 24
- `propstore/cli/claim.py`: lines 105, 162, 214
- `propstore/cli/concept/__init__.py`: line 160
- `propstore/cli/concept/mutation.py`: lines 287, 509
- `propstore/cli/concept/display.py`: line 140
- `propstore/form_utils.py`: lines 302, 350
- `propstore/grounding/loading.py`: line 78
- `propstore/sidecar/build.py`: line 229
- `propstore/source/registry.py`: lines 32, 64
- `propstore/repository.py`: lines 36, 101, 144, 154, 173
- `propstore/repository_history.py`: line 268
- `propstore/project_init.py`: lines 31, 53

`claims` path usages:

- `propstore/artifacts/codes.py`: line 142
- `propstore/compiler/workflows.py`: lines 133, 140, 242, 288, 290
- `propstore/cli/claim.py`: lines 103, 213
- `propstore/cli/concept/__init__.py`: line 333
- `propstore/cli/concept/mutation.py`: lines 316, 536
- `propstore/merge/structured_merge.py`: line 263
- `propstore/merge/merge_classifier.py`: lines 304-306
- `propstore/sidecar/build.py`: lines 231-232
- `propstore/world/consistency.py`: line 77
- `propstore/repository.py`: line 40
- `propstore/project_init.py`: line 54

`contexts` path usages:

- `propstore/context_workflows.py`: line 119
- `propstore/compiler/workflows.py`: lines 157, 161, 258, 260
- `propstore/micropubs.py`: line 67
- `propstore/sidecar/build.py`: lines 239-240
- `propstore/repository.py`: line 56
- `propstore/project_init.py`: line 55

`forms` path usages:

- `propstore/cli/claim.py`: lines 115, 117, 120, 169, 171, 174
- `propstore/compiler/context.py`: line 137
- `propstore/compiler/workflows.py`: lines 128, 134, 233, 243, 284, 299
- `propstore/cli/concept/mutation.py`: lines 104, 168, 320, 348, 537
- `propstore/cli/concept/__init__.py`: line 334
- `propstore/form_utils.py`: lines 128, 199, 337
- `propstore/sidecar/build.py`: lines 228, 252, 258
- `propstore/source/concepts.py`: line 20
- `propstore/validate_concepts.py`: line 311
- `propstore/repository.py`: line 44
- `propstore/project_init.py`: line 56

`predicates`, `rules`, `stances`, and `worldlines` path usages:

- `propstore/project_init.py`: lines 58, 59, 62, 63
- `propstore/artifacts/codes.py`: line 185 for `stances`
- `propstore/artifacts/families.py`: lines 319, 447, 453, 459, 473, 479, 485, 504, 516
- `propstore/merge/structured_merge.py`: line 264 for `stances`
- `propstore/sidecar/build.py`: lines 376-377 for `stances` and `justifications`
- `propstore/repository.py`: lines 60 and 72

### Non-canonical artifact roots still requiring one-source ownership

These roots are not all in `SEMANTIC_FAMILIES` today, but they still must not be
free literals:

- `justifications`: `propstore/artifacts/codes.py` line 170,
  `propstore/sidecar/build.py` line 377, `propstore/repository.py` line 64,
  `propstore/project_init.py` line 57
- `micropubs`: `propstore/sidecar/build.py` line 359 and
  `propstore/artifacts/families.py` lines 395, 401, 407
- `sources`: `propstore/artifacts/codes.py` line 159,
  `propstore/sidecar/sources.py` line 15, `propstore/repository.py` line 68,
  `propstore/project_init.py` line 61
- source-branch fixed files: `source.yaml`, `notes.md`, `metadata.json`,
  `concepts.yaml`, `claims.yaml`, `micropubs.yaml`, `justifications.yaml`,
  `stances.yaml` in `propstore/artifacts/families.py` lines 81-113 and
  source finalize call-site strings in `propstore/source/finalize.py`

## Target Design

`SemanticFamilyDefinition` becomes the actual schema owner, not just a metadata
record. It should expose:

- `root`
- `extension`
- `collection_field`
- `ref_type`
- `branch_policy`
- `filename_codec`
- `relpath(ref)`
- `resolve(repo, ref)`
- `ref_from_path(path)`
- `ref_from_loaded(loaded)`
- `list_refs(repo, branch=None, commit=None)`
- `root_path(tree_or_repo)`
- `matches_path(path)`

The `ArtifactFamily` declarations should either be produced from
`SemanticFamilyDefinition` or wired by a single generic adapter that receives the
family definition object. They should not receive repeated strings such as
`subdir="concepts"`.

Stance filename encoding belongs to the stance family definition. The
`source_claim.replace(":", "__")` and reverse decoding are schema behavior, so
they must move out of `refs.py` and `families.py`.

Source-branch artifacts, merge artifacts, proposal artifacts, and packaged seed
resources need the same treatment. They can be represented as semantic families
only if they are semantic repository families. If not, define them as artifact
family layouts using the same family-definition machinery, not as an unrelated
dictionary of strings.

## Execution Phases

### Phase 1: Red architecture tests

Add tests before implementation:

- Assert that canonical root literals `claims`, `concepts`, `contexts`, `forms`,
  `predicates`, `rules`, `stances`, and `worldlines` appear as path-schema roots
  only in `propstore/artifacts/semantic_families.py`.
- Assert that `propstore/artifacts/refs.py` exports no canonical relpath helpers.
- Assert that `propstore/artifacts/families.py` contains none of the helper names
  listed in this document.
- Assert that family path parsing, listing, and loaded-document ref recovery work
  through `SEMANTIC_FAMILIES.by_name(...).ref_from_path(...)` or equivalent.
- Assert that the semantic contract body includes root, extension, ref type,
  branch policy, collection field, and filename codec identifier.

Scope the literal test to production path schema. Do not block payload field
names inside document models, demo data, old plans, or test fixtures.

### Phase 2: Move path behavior into family definitions

Extend `SemanticFamilyDefinition` with the target API. Add generic filename
codecs:

- plain stem codec: `claims/demo.yaml` <-> `ClaimsFileRef("demo")`
- stance source-claim codec: `stances/claim__id.yaml` <-> `StanceFileRef("claim:id")`
- singleton codec for manifest-like files if merge artifacts are folded in

Add typed accessors on `SemanticFamilyRegistry` for common roots:

- `root_path(name, tree_or_repo)`
- `relpath(name, ref)`
- `list_refs(name, repo, branch=None, commit=None)`
- `ref_from_path(name, path)`

No production caller should need to spell a root literal after this phase except
inside family declarations.

### Phase 3: Replace artifact-family helper wiring

Convert canonical `ArtifactFamily` declarations to use family-derived adapters.
Delete all canonical helpers from `families.py` listed above.

Convert or delete `refs.py` relpath helpers and update `artifacts/__init__.py`
exports. The only remaining contents of `refs.py` should be typed references and
non-schema normalization functions that are still genuinely independent.

### Phase 4: Convert production callers

Update path consumers in this order:

1. `project_init.py` and `repository.py`, because they currently seed root
   directories and convenience properties.
2. `artifacts/codes.py`, because it has direct linear directory scans over
   semantic roots and suffix checks.
3. `compiler/workflows.py`, `compiler/context.py`, `validate_concepts.py`,
   `form_utils.py`, `context_workflows.py`, `micropubs.py`.
4. `sidecar/build.py`, `sidecar/sources.py`, `grounding/loading.py`,
   `world/consistency.py`.
5. CLI modules that build roots directly.
6. Merge code paths that read branch snapshots.

Use family APIs that can operate against `KnowledgePath` and git-backed
snapshots without materializing the working tree.

### Phase 5: Bring non-canonical layouts under family ownership

Handle source-branch, proposal, merge, `sources`, `justifications`, and
`micropubs` path schema. The target is still one family/layout owner, not loose
helpers.

Expected deletions:

- remove source file-name helpers from `families.py`
- remove `source_finalize_relpath`, `concept_alignment_relpath`,
  `merge_manifest_relpath`, and `STANCE_PROPOSAL_BRANCH` as free schema symbols
  from `refs.py`
- update source/finalize/promote/status code to ask the family/layout definition
  for paths and branch names

### Phase 6: Contract and versioning

Bump semantic family contract versions after the contract body changes. The
version bump is mandatory because the exposed family contract is changing, even
if repository data remains readable.

Regenerate the semantic contract manifest and ensure tests check that the
declared version changed with the schema contract body.

### Phase 7: Verification

Run targeted tests first:

- `uv run pytest tests/test_semantic_family_registry.py`
- `uv run pytest tests/test_artifact_store.py`
- `uv run pytest tests/test_import_repo.py`
- `uv run pytest tests/test_contract_manifest.py`

Then run impacted integration areas:

- `uv run pytest tests/test_init.py tests/test_git_backend.py`
- `uv run pytest tests/test_build_sidecar.py tests/test_claim_compiler.py`
- `uv run pytest tests/test_merge_classifier.py tests/test_structured_merge_projection.py`

Then run the full suite with the existing logged test wrapper used in this repo.

## Completion Criteria

This workstream is not complete until all of these are true:

- `rg -n -F 'claims_file_relpath' propstore tests` has no production export or
  production caller.
- `rg -n -F 'concept_file_relpath' propstore tests` has no production export or
  production caller.
- `rg -n -F '_yaml_path_ref' propstore tests` returns nothing.
- `rg -n -F '_list_yaml_refs_in_directory' propstore tests` returns nothing.
- `propstore/artifacts/refs.py` has no functions that return canonical
  repository paths.
- `propstore/artifacts/families.py` has no per-family path/list/ref helpers for
  canonical semantic families.
- Production path consumers ask a family or layout definition for roots and
  relpaths.
- Repository import remains committed-snapshot based and does not materialize
  the source working tree.
- Linear directory scans are not introduced where snapshot root enumeration or
  family listing is available.
- Contract tests prove there is exactly one canonical declaration for each
  semantic family root.
