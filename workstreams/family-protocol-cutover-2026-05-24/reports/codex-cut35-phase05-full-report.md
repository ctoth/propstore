# Codex Cut 35 Phase 05 Full Report

## Workflow actually used

Executed `workstreams/family-protocol-cutover-2026-05-24/prompts/codex-cut35-phase05-full.md` against HEAD `6b2ee445` on `master`.

Result: **PARTIAL under H-A**. Quire projects `FamilyCharter.batch_specs`, but local Quire does not yet provide generic `ArtifactFamily` batch encode/decode/payload dispatch from those specs. I kept the registry-owned source batch callbacks and `propstore/families/batch_specs.py` with NOTE comments.

## Completed

- Moved registry-owned semantic FK specs for claims, concepts, stances, justifications, and micropublications onto owning `CharterField.foreign_key` / `CharterField.foreign_keys`.
- Used the multi-FK pattern for `concept.parameterization_relationships` with both input concept and canonical claim FKs.
- Moved claim, concept, context, and justification reference keys onto owning family charter `FamilyDefinition.reference_keys`.
- Removed registry FK and reference-key tables.
- Replaced `contracts.py::iter_document_schema_types` with charter/registry-derived document schema enumeration.
- Deleted `DOCUMENT_SCHEMA_CONTRACT_VERSION_OVERRIDES`.
- Moved batch spec objects onto owning charters where available.
- Regenerated `propstore/_resources/contract_manifests/semantic-contracts.yaml`.

## H-A retained surfaces

- `propstore/families/registry.py` still owns source batch decode/render/payload callback functions.
- `propstore/families/batch_specs.py` remains as a temporary compatibility re-export surface.
- Source batch constants remain referenced by source modules and tests until Quire generic batch IO can replace the handwritten callbacks directly.

## Search gates

Zero-hit gates:

```powershell
rg -n -F -- "DOCUMENT_SCHEMA_CONTRACT_VERSION_OVERRIDES" propstore tests
rg -n -F -- "iter_document_schema_types" propstore tests
rg -n -F -- "doc_type=" propstore/families/registry.py
rg -n -F -- "ForeignKeySpec(" propstore/families/registry.py
rg -n -F -- "ReferenceKey.field" propstore/families/registry.py
rg -n -F -- "CLAIM_FOREIGN_KEYS" propstore tests
```

Expected H-A nonzero gates:

```powershell
rg -n -F -- "DocumentBatchSpec" propstore/families propstore/source tests
rg -n -F -- "SOURCE_CLAIM_BATCH_SPEC" propstore tests
rg -n -F -- "SOURCE_CONCEPT_BATCH_SPEC" propstore tests
rg -n -F -- "SOURCE_JUSTIFICATION_BATCH_SPEC" propstore tests
rg -n -F -- "SOURCE_STANCE_BATCH_SPEC" propstore tests
rg -n -F -- "SOURCE_MICROPUBLICATION_BATCH_SPEC" propstore tests
```

## Gates

Passed:

```powershell
uv run pyright propstore
```

Result: `0 errors, 0 warnings, 0 informations`.

Passed:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label registry-contracts-batches tests/test_semantic_family_registry.py tests/test_quire_consumer_contracts.py tests/test_contract_manifest.py
```

Result: `31 passed in 33.54s`.

Log: `logs\test-runs\registry-contracts-batches-20260525-160838.log`
