# Semantic Family Schema Centralization And Placement Policy Workstream

Date: 2026-04-18

## Purpose

Centralize repository schema ownership without confusing logical artifact identity
with physical storage paths.

The earlier version of this workstream aimed to move every root string, suffix,
and filename codec into `propstore/artifacts/semantic_families.py`. That was a
useful cleanup direction, but it was still path-centric: it assumed a semantic
family owns a stable `root/filename.yaml` shape. Quire will need hash scattering
as artifact families grow, so the durable abstraction must be:

- logical artifact identity: family plus typed ref
- storage placement policy: how that logical artifact is located in git
- backend address: branch plus an opaque locator, usually but not always a path
- enumeration/index policy: how refs are listed without materializing a working
  tree or linearly scanning an unbounded directory

The acceptance condition is still deletion of duplicate helper surfaces and path
literals from propstore production code. The difference is that callers must move
to Quire placement APIs, not to a temporary `root_path()` / `relpath()` API that
would need another full rewrite when hash scattering lands.

## Status At Revision

Two commits already exist in this workstream:

- `6785bd6 Centralize semantic family path helpers`
- `e28af05 Route repository roots through semantic families`

After those commits, additional uncommitted edits were started in propstore to
remove remaining path helpers and non-canonical layout literals. Those edits were
interrupted before test verification. The next execution pass must stabilize this
partial state first: keep only changes that move toward placement-policy
ownership, and revert or reshape path-centric changes that deepen the wrong
abstraction.

Do not declare this work complete while old production paths coexist with the new
path, or while the active abstraction is still "semantic family returns a
relpath" instead of "placement policy returns an address".

## Core Design Correction

A path is not identity.

`claims/paper.yaml`, `claims/9f/2a/paper.yaml`, a git ref, a git note, or an
index-backed object can all store the same logical artifact. The logical handle is
the typed ref under an artifact family. The storage address is an implementation
detail governed by a placement policy.

Current Quire surface:

- `ResolvedArtifact(branch, relpath, commit=None)`
- `ArtifactFamily.resolve_ref(owner, ref) -> ResolvedArtifact`
- `ArtifactFamily.ref_from_path(path) -> ref`
- `ArtifactFamily.list_refs(owner, branch, commit) -> list[ref]`

This is too path-shaped. Hash scattering breaks the assumption that
`ref_from_path()` is authoritative. Reverse lookup may require reading a document
header, consulting an index, or not being supported at all.

Target Quire concepts:

- `ArtifactAddress`: branch plus opaque backend locator.
- `ArtifactLocator`: discriminated backend locator, initially path-based but not
  semantically a path.
- `ArtifactPlacementPolicy`: maps typed refs to addresses, lists refs, and
  optionally recovers refs from addresses or loaded documents.
- `FlatYamlPlacement`: current `root/stem.yaml` behavior.
- `HashScatteredYamlPlacement`: future large-family behavior with fanout and a
  stable hash key.
- `FixedFilePlacement`: source branch files such as `source.yaml`, `notes.md`,
  and `claims.yaml`.
- `SingletonYamlPlacement`: merge manifests or other one-file artifacts.
- `BranchPolicy`: primary, current, fixed branch, source branch, and future git
  refs/notes policies.

The word `path` can still appear at filesystem or git backend boundaries. It must
not be the semantic-family interface.

## Target Architecture

### Quire

`quire.artifacts` owns the generic artifact address model.

Required additions:

- `ArtifactAddress`
  - `branch: str`
  - `locator: ArtifactLocator`
  - `commit: str | None`
- `PathArtifactLocator`
  - `path: str`
- `ArtifactPlacementPolicy[Owner, Ref]`
  - `address_for(owner, ref) -> ArtifactAddress`
  - `list_refs(owner, branch=None, commit=None) -> list[Ref]`
  - `ref_from_locator(locator) -> Ref` only when the placement is reversible
  - `ref_from_loaded(loaded) -> Ref` for document-header recovery where needed
  - `contract_body() -> dict[str, object]`
- `ArtifactFamily.placement`
  - The family may keep `resolve_ref` only as a temporary internal adapter while
    all callers are updated in the same workstream. It must not remain the
    public center of the model.

Required placement implementations:

- `FlatYamlPlacement(namespace, ref_field, extension, codec, branch_policy)`
- `HashScatteredYamlPlacement(namespace, ref_field, extension, codec, hash, fanout)`
- `FixedFilePlacement(filename, branch_policy)`
- `TemplateFilePlacement(template, ref_field, codec, branch_policy)`
- `SingletonFilePlacement(filename, branch_policy)`

The initial propstore cutover can use `FlatYamlPlacement` for canonical families.
The hash-scattered policy must be implemented and tested in Quire now, even if no
propstore family switches to it in the first propstore commit. That prevents the
schema centralization from encoding flat paths as the only design.

### Propstore

`propstore/artifacts/semantic_families.py` owns semantic family declarations.
Each family declares:

- family name
- contract version
- artifact family
- document type
- collection field, when the document is a collection
- typed ref
- foreign keys
- import policy
- placement policy

It should not declare `root`, `extension`, and `filename_codec` as first-class
fields except as data inside a placement policy contract body.

Non-canonical artifacts also use placement policies:

- canonical sources: flat YAML namespace under `sources`
- justifications: flat YAML namespace under `justifications`
- micropubs: flat YAML namespace under `micropubs`
- source branch files: fixed files on a source branch
- stance proposals: flat YAML namespace on fixed branch `proposal/stances`
- concept alignments: flat YAML namespace on fixed branch `proposal/concepts`
- merge manifest: singleton file on primary branch

If these are not semantic families, they still need placement declarations. They
must not be loose helper functions or free dictionaries of strings.

## Verified Duplicate Helpers To Delete

### `propstore/artifacts/refs.py`

Delete path-construction helpers and remove their exports:

- `worldline_relpath`
- `canonical_source_relpath`
- `claims_file_relpath`
- `micropubs_file_relpath`
- `concept_file_relpath`
- `justifications_file_relpath`
- `predicate_file_relpath`
- `rule_file_relpath`
- `stance_file_relpath`
- `source_claim_from_stance_path`
- `source_finalize_relpath`
- `concept_alignment_relpath`
- `merge_manifest_relpath`
- free `STANCE_PROPOSAL_BRANCH` if it is still exported as schema

Keep typed ref dataclasses. Refs are logical identity, not placement.

### `propstore/artifacts/families.py`

Delete per-family path builders and one-off ref/list helpers:

- `_context_artifact`
- `_form_artifact`
- `_worldline_artifact`
- `_canonical_source_artifact`
- `_claims_file_artifact`
- `_micropubs_file_artifact`
- `_concept_file_artifact`
- `_justifications_file_artifact`
- `_predicate_file_artifact`
- `_rule_file_artifact`
- `_stance_file_artifact`
- `_proposal_stance_artifact`
- `_concept_alignment_artifact`
- `_merge_manifest_artifact`
- `_list_yaml_refs_in_directory`
- `_list_stance_refs_in_directory`
- `_yaml_path_ref`
- `_ref_from_loaded_source_path`
- per-family wrappers such as `_claims_file_refs`,
  `_concept_file_ref_from_path`, `_rule_file_ref_from_loaded`, and
  `_worldline_refs`
- source fixed-file helpers such as `_source_document_artifact`,
  `_source_claims_artifact`, and `_source_finalize_report_artifact`

Replacement must be placement objects, not another set of helper functions.

## Production Surfaces To Convert

Canonical semantic roots currently or recently appeared in these areas:

- repository initialization and discovery: `project_init.py`, `repository.py`
- direct artifact loading and artifact-code checks: `artifacts/codes.py`
- compiler context/workflows and validators: `compiler/context.py`,
  `compiler/workflows.py`, `validate_concepts.py`, `form_utils.py`
- context and micropub workflows: `context_workflows.py`, `micropubs.py`
- sidecar population: `sidecar/build.py`, `sidecar/sources.py`,
  `sidecar/micropublications.py`
- source registry and promotion/finalization: `source/registry.py`,
  `source/finalize.py`, `source/promote.py`, `source/alignment.py`
- merge paths: `merge/structured_merge.py`, `merge/merge_classifier.py`
- CLI adapters that construct roots directly

Payload field strings such as claim data field `concepts` are not placement
schema. File, directory, branch, suffix, namespace, and source strings are
placement schema.

## Execution Phases

### Phase 0: Stabilize Interrupted Propstore State

Before changing Quire, inspect the propstore worktree and classify each
uncommitted edit:

- keep if it deletes a duplicate helper or already routes through a future
  placement-friendly owner
- reshape if it deepens `root_path()` / `relpath()` as the target public API
- revert only the interrupted path-centric pieces that cannot be safely reshaped

Run a focused smoke test through the logged pytest wrapper after stabilization.
Commit this stabilization as its own propstore commit if it leaves meaningful
kept changes. Do not use this as evidence that the full workstream is complete.

### Phase 1: Quire Red Tests

Add Quire tests first:

- flat placement maps logical refs to the same path addresses Quire uses today
- hash-scattered placement produces deterministic fanout addresses
- hash-scattered placement does not require the physical path to be the semantic
  ref
- fixed-file placement resolves source-branch artifacts without ad hoc helpers
- singleton placement resolves manifest-style artifacts
- placement contract bodies include kind, namespace or filename, extension,
  codec, hash algorithm, fanout, and branch policy
- listing refs delegates to the placement policy and does not materialize a
  working tree

### Phase 2: Implement Quire Placement Policies

Implement the address and placement abstractions in Quire.

Required behavior:

- `DocumentFamilyStore.prepare/load/save/delete/move/list` operate through
  `ArtifactAddress`
- path-backed stores convert only `PathArtifactLocator` to backend paths at the
  backend boundary
- old `ResolvedArtifact.relpath` is removed or reduced to a local compatibility
  adapter inside the same commit series; it must not remain the primary API
- no caller needs to know whether a family is flat or hash-scattered

Commit Quire changes frequently:

- address model and flat placement
- hash-scattered placement
- store integration
- contract body/version tests

### Phase 3: Propstore Semantic Families Declare Placement

Change `SemanticFamilyDefinition` to hold a Quire placement policy.

Canonical families should initially use flat placement with the same repository
layout as today:

- `claim`: namespace `claims`, collection field `claims`
- `concept`: namespace `concepts`
- `context`: namespace `contexts`
- `form`: namespace `forms`
- `predicate`: namespace `predicates`, collection field `predicates`
- `rule`: namespace `rules`, collection field `rules`
- `stance`: namespace `stances`, source-claim codec
- `worldline`: namespace `worldlines`

The contract body must expose placement details under `placement`, not duplicate
them as separate root/suffix fields.

### Phase 4: Replace Artifact-Family Wiring

Convert `ArtifactFamily` declarations to use family placement policies. Delete
the helper functions listed above.

No canonical family in `families.py` should carry its own root, suffix, branch,
or filename codec. It should receive the semantic family definition or placement
policy directly.

### Phase 5: Convert Production Callers

Convert callers in this order:

1. repository init/discovery and packaged seed resource lookup
2. compiler and validators
3. sidecar build/population
4. source finalization, promotion, status, and alignment
5. merge code paths
6. CLI adapters

Callers should ask a family/placement owner for logical artifact addresses,
namespace roots where enumeration is genuinely needed, or list APIs where
enumeration can be abstracted. They should not spell `claims`, `concepts`,
`.yaml`, `source.yaml`, or proposal branch names as storage schema.

### Phase 6: Non-Canonical Artifact Placements

Bring source-branch, proposal, merge, `sources`, `justifications`, and `micropubs`
under placement ownership.

Expected results:

- source branch names are produced by source branch placement policy
- source fixed file names live in fixed-file placements
- stance proposal branch and placement live in one proposal placement
- concept proposal branch and alignment placement live in one placement
- merge manifest lives in singleton placement
- sidecar and artifact-code loaders use placement/list APIs, not direct suffix
  scans where a placement can enumerate

### Phase 7: Contract And Versioning

Bump Quire contract versions when placement contracts are introduced.

Bump propstore semantic family contract versions when family contract bodies move
from root/suffix fields to placement bodies.

Regenerate checked-in manifests and ensure tests fail if a contract body changes
without a version bump.

### Phase 8: Verification

Use the repo's logged pytest wrappers for propstore tests.

Quire targeted tests:

- placement policy tests
- family store tests
- contract/version tests

Propstore targeted tests:

- `tests/test_semantic_family_registry.py`
- `tests/test_artifact_store.py`
- `tests/test_import_repo.py`
- `tests/test_contract_manifest.py`
- `tests/test_init.py`
- `tests/test_git_backend.py`
- `tests/test_build_sidecar.py`
- `tests/test_claim_compiler.py`
- `tests/test_merge_classifier.py`
- `tests/test_structured_merge_projection.py`
- source promotion/finalization/alignment tests

Then run the full propstore suite with `scripts/run_logged_pytest.ps1`.

## Completion Criteria

This workstream is not complete until all of these are true:

- Quire has first-class placement policies, including hash-scattered placement.
- Propstore semantic families declare placement policies instead of open-coded
  roots and relpaths.
- `propstore/artifacts/refs.py` has no functions that return repository paths.
- `propstore/artifacts/families.py` has no per-family path/list/ref helpers for
  canonical semantic families.
- Non-canonical source/proposal/merge artifacts use placement declarations, not
  loose helper functions.
- Production callers do not spell storage roots, fixed filenames, suffixes, or
  proposal branch names as schema.
- Repository import remains committed-snapshot based and does not materialize the
  source working tree.
- Linear scans are not introduced where placement listing or snapshot prefix
  enumeration is available.
- Contract tests prove there is exactly one declaration for each semantic family
  placement and each non-canonical artifact placement.
- Hash scattering can be enabled for a family by changing its placement policy,
  without changing production callers.
