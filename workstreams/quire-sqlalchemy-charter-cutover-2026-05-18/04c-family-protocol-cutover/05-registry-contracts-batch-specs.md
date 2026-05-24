# 05 Registry Contracts Batch Specs

## Prerequisites

- `01-deleted-file-fallout-repair.md`
- `02-quire-generated-family-protocols.md`
- `03-generic-family-lookup-cleanup.md`
- `04-family-document-deletion.md`

## Target

Reduce registry and contracts to composition over family charters. Delete
registry-owned field/reference/placement/batch/document facts.

## Deletion Targets

- Concrete document imports in `propstore/families/registry.py`.
- `CLAIM_FOREIGN_KEYS`, `CONCEPT_FOREIGN_KEYS`, `STANCE_FOREIGN_KEYS`,
  `JUSTIFICATION_FOREIGN_KEYS`, and `MICROPUBLICATION_FOREIGN_KEYS` as registry
  field/reference tables.
- `CLAIM_REFERENCE_KEYS` and `CONCEPT_REFERENCE_KEYS` as registry-owned field
  facts.
- Source batch decode/render/payload helpers in `registry.py`.
- `propstore/families/batch_specs.py`.
- `propstore/contracts.py::iter_document_schema_types`.
- `DOCUMENT_SCHEMA_CONTRACT_VERSION_OVERRIDES` keyed by handwritten document
  class paths.

## Required Owners

- Family charters own references, relationships, placements, document fields,
  lifecycle metadata, batch envelope metadata, and contract version metadata.
- Registry composes family declarations and exposes the complete registry.
- Contract generation enumerates generated charter-backed document schemas.

## Execution

1. Delete one registry-owned fact group after the corresponding family charter
   owns it.
2. Replace contract module scanning with registry/charter enumeration.
3. Replace source batch specs with generated batch metadata.
4. Regenerate contract manifests only after generated contract code is the
   source of truth.

## Search Gates

```powershell
rg -n -F -- "DOCUMENT_SCHEMA_CONTRACT_VERSION_OVERRIDES" propstore tests
rg -n -F -- "iter_document_schema_types" propstore tests
rg -n -F -- "DocumentBatchSpec" propstore/families propstore/source tests
rg -n -F -- "SOURCE_CLAIM_BATCH_SPEC" propstore tests
rg -n -F -- "SOURCE_CONCEPT_BATCH_SPEC" propstore tests
rg -n -F -- "SOURCE_JUSTIFICATION_BATCH_SPEC" propstore tests
rg -n -F -- "SOURCE_STANCE_BATCH_SPEC" propstore tests
rg -n -F -- "SOURCE_MICROPUBLICATION_BATCH_SPEC" propstore tests
rg -n -F -- "doc_type=" propstore/families/registry.py
rg -n -F -- "ForeignKeySpec(" propstore/families/registry.py
rg -n -F -- "ReferenceKey.field" propstore/families/registry.py
```

## Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label registry-contracts-batches tests/test_semantic_family_registry.py tests/test_quire_consumer_contracts.py tests/test_contract_manifest.py
```

## Completion

- Registry is composition only.
- Contracts derive schema entries from generated family documents.
- Batch behavior is charter metadata plus generic Quire batch IO.
