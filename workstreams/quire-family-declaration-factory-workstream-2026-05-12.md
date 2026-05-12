# Quire Family Declaration Factory Workstream

## Goal

Add a generic Quire declaration builder that collapses Propstore's repeated
`Placement -> ArtifactFamily -> FamilyDefinition` boilerplate without moving
Propstore semantic declarations into Quire.

The target architecture is:

- Quire owns a small typed builder/spec for common family declaration shapes.
- Propstore owns the list of families, document types, reference fields,
  placements, branch policies, foreign keys, identity policies, and semantic
  metadata values.
- Propstore's registry file shrinks because simple families are declared once,
  not as separate placement constants, artifact-family constants, and
  `FamilyDefinition` entries.

The workstream is deletion-first on the Propstore side. If a Propstore constant
exists only to feed a one-use declaration, delete it and use compiler/test/search
failures as the caller queue.

This is a two-repository workstream. Quire changes land first. Propstore must
never pin Quire to a local path; pin only to a pushed tag or immutable pushed
commit SHA.

## Non-Goals

Do not move these into Quire:

- `PropstoreFamily`
- Propstore family names, branch names, namespaces, filenames, or document types
- semantic metadata keys or values
- `CLAIM_IDENTITY_POLICY` or `CONCEPT_IDENTITY_POLICY`
- Propstore FK declarations
- source promotion, proposal promotion, import normalization, or sidecar policy

Do not create Propstore compatibility aliases such as renamed placement
constants or wrapper factory functions. The kept code should be smaller.

## Workstream Order

The phases below are topologically ordered.

1. Quire family declaration spec tests
2. Quire generic declaration builder
3. Propstore dependency pin
4. Propstore simple-family declaration collapse
5. Propstore source/proposal-family declaration collapse
6. Contract and final gates

## Phase 1 - Quire Family Declaration Spec Tests

Repository: `../quire`

Write failing tests for a generic declaration builder.

Required cases:

- flat YAML family with explicit ref field
- flat YAML family with non-default codec
- hash-scattered YAML family
- fixed-file family
- subdir fixed-file family
- nested flat YAML family
- singleton family
- custom document callbacks pass through to `ArtifactFamily`
- identity field, reference keys, foreign keys, and metadata pass through to
  `FamilyDefinition`

Consumer-neutral examples only. Do not mention Propstore terms.

Target tests:

- `../quire/tests/test_families.py`
- `../quire/tests/test_artifacts.py`

Required gates:

- `uv run pytest tests/test_families.py tests/test_artifacts.py`

## Phase 2 - Quire Generic Declaration Builder

Repository: `../quire`

Add the smallest generic API that lets consumers declare a family once.

Candidate shape:

```python
FamilyDeclaration(
    key=FamilyKey.BOOKS,
    name="books",
    contract_version=VersionId("1"),
    artifact_name="book",
    doc_type=BookDocument,
    placement=FlatYamlPlacement(...),
    identity_field="id",
    reference_keys=(ReferenceKey.field("slug"),),
    foreign_keys=(...),
    metadata={"importable": True},
).to_definition()
```

Acceptable alternative:

- `FamilyDefinition.from_artifact(...)`
- `declare_family(...)` free function

Required behavior:

- no loss of type information for bound families
- all existing `ArtifactFamily` callback fields are supported
- no hidden defaults that encode application policy
- contract bodies remain equivalent to explicitly authored declarations
- declaration validation remains in Quire, not duplicated in Propstore

Required gates:

- `uv run pytest tests/test_families.py tests/test_family_store.py tests/test_artifacts.py`
- `uv run pytest`

## Phase 3 - Propstore Dependency Pin

Repository: `propstore`

Only start after Quire changes are pushed to a shared remote.

Before editing dependency metadata:

- verify the Quire reference is a pushed tag or immutable pushed commit SHA
- reject local paths, editable paths, local git paths, Windows drive paths, WSL
  paths, and `file://` URLs

Update:

- `pyproject.toml`
- `uv.lock`

Required gate:

- `uv run pyright propstore`

## Phase 4 - Propstore Simple-Family Declaration Collapse

Repository: `propstore`

Delete first from `propstore/families/registry.py` the one-use placement and
artifact-family constants for simple canonical families.

Initial deletion candidates:

- `CONTEXT_PLACEMENT` and `CONTEXT_FAMILY`
- `FORM_PLACEMENT` and `FORM_FAMILY`
- `PREDICATE_PLACEMENT` and `PREDICATE_FAMILY`
- `RULE_PLACEMENT` and `RULE_FAMILY`
- `RULE_SUPERIORITY_PLACEMENT` and `RULE_SUPERIORITY_FAMILY`
- `STANCE_PLACEMENT` and `STANCE_FAMILY`
- `SAMEAS_PLACEMENT` and `SAMEAS_ASSERTION_FAMILY`
- `WORLDLINE_PLACEMENT` and `WORLDLINE_FAMILY`
- `JUSTIFICATION_PLACEMENT` and `JUSTIFICATION_FAMILY`

Then update `PROPSTORE_FAMILY_REGISTRY` entries to use the Quire declaration
builder directly.

Keep as explicit constants only if they are used by production code outside the
registry and removing them would not shrink Propstore. If a constant is kept,
record the caller that requires it in the commit message or PR notes.

Search gates:

- `rg -F "_PLACEMENT =" propstore/families/registry.py`
- `rg -F "_FAMILY =" propstore/families/registry.py`

The remaining matches must be justified by multi-use callbacks, source/proposal
families not yet migrated, or identity-special cases.

Required gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label family-declare-simple tests/test_semantic_family_registry.py tests/test_artifact_store.py tests/test_contract_manifest.py`
- `uv run pyright propstore`

## Phase 5 - Propstore Source/Proposal-Family Declaration Collapse

Repository: `propstore`

After Phase 4 is green, repeat the deletion-first collapse for source and
proposal families.

Deletion candidates:

- `SOURCE_DOCUMENT_PLACEMENT` through `SOURCE_FINALIZE_REPORT_PLACEMENT`
- `SOURCE_DOCUMENT_FAMILY` through `SOURCE_FINALIZE_REPORT_FAMILY`
- `PROPOSAL_STANCE_PLACEMENT` and `PROPOSAL_STANCE_FAMILY`
- `PROPOSAL_PREDICATE_PLACEMENT` and `PROPOSAL_PREDICATES_FAMILY`
- `PROPOSAL_RULE_PLACEMENT` and `PROPOSAL_RULES_FAMILY`
- `CONCEPT_ALIGNMENT_PLACEMENT` and `CONCEPT_ALIGNMENT_FAMILY`
- `MERGE_MANIFEST_PLACEMENT` and `MERGE_MANIFEST_FAMILY`

Do not move source/proposal branch names or filenames into Quire. They remain
arguments in the Propstore declarations.

Required gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label family-declare-source-proposal tests/test_artifact_store.py tests/test_proposal_predicates_family.py tests/test_proposal_rules_family.py tests/test_semantic_family_registry.py tests/test_contract_manifest.py`
- `uv run pyright propstore`

## Phase 6 - Contract and Final Gates

Repository: both

Contract handling:

- If Quire contract output is equivalent, do not bump Propstore family contract
  versions merely because the authoring style changed.
- Regenerate `propstore/_resources/contract_manifests/semantic-contracts.yaml`
  only if contract output changes intentionally.

Final Quire gates:

- `uv run pytest`

Final Propstore gates:

- `powershell -File scripts/run_logged_pytest.ps1 -Label family-declaration-factory-full tests/test_semantic_family_registry.py tests/test_artifact_store.py tests/test_contract_manifest.py tests/test_repository_artifact_boundary_gates.py`
- `uv run pyright propstore`

Completion evidence:

- `propstore/families/registry.py` has materially fewer one-use placement and
  artifact-family constants
- family declarations remain readable and still name Propstore semantics in
  Propstore
- Quire contains no Propstore vocabulary in the builder implementation
- no local Quire dependency pin is committed
