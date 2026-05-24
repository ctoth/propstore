# 04 Family Document Class Deletion

## Final State

Every family still has a document surface, but the document struct and codec are
generated from the family charter. Handwritten family document classes and
document field lists are gone.

Registry composition remains. Registry code does not import concrete document
classes, own reference keys, own foreign-key tables, own source batch codecs, or
repeat placement facts.

## Delete First

Delete handwritten document class files family by family after Quire generated
documents are pinned:

- `propstore/families/sameas/documents.py`
- `propstore/families/forms/documents.py`
- `propstore/families/claims/documents.py`
- `propstore/families/concepts/documents.py`
- `propstore/families/contexts/documents.py`
- `propstore/families/documents/*.py`

Use `sameas` or `forms` as the first deletion slice, then continue by family.

## Repair Owners

- Family charter: document fields, storage fields, references, lifecycle,
  document inclusion, batch fields, contract version metadata.
- Family model/semantic owner: methods and validators only.
- Quire: generated document types, codecs, family batch mechanics, and registry
  document resolution.
- `propstore/contracts.py`: enumerates family charters/generated document
  schemas, not module paths.

## Search Gates

```powershell
rg -n -F -- "from propstore.families.documents" propstore tests
rg -n -F -- "from propstore.families.claims.documents" propstore tests
rg -n -F -- "from propstore.families.concepts.documents" propstore tests
rg -n -F -- "from propstore.families.contexts.documents" propstore tests
rg -n -F -- "from propstore.families.forms.documents" propstore tests
rg -n -F -- "from propstore.families.sameas.documents" propstore tests
rg -n -F -- "DocumentStruct" propstore/families propstore/source propstore/worldline propstore/support_revision propstore/core
rg -n -F -- "DocumentBatchSpec" propstore/families propstore/source tests
rg -n -F -- "DOCUMENT_SCHEMA_CONTRACT_VERSION_OVERRIDES" propstore tests
rg -n -F -- "iter_document_schema_types" propstore tests
rg -n -F -- "doc_type=" propstore/families/registry.py
rg -n -F -- "ForeignKeySpec(" propstore/families/registry.py
rg -n -F -- "ReferenceKey.field" propstore/families/registry.py
rg -n -F -- "metadata={\"payload\"" propstore tests
rg -n -F -- "payload_rest" propstore tests
```

All gates are zero-hit gates outside notes, workstreams, docs, and reports.

## Type And Test Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label family-doc-deletion tests/test_semantic_family_registry.py tests/test_quire_consumer_contracts.py tests/test_contract_manifest.py tests/test_fixture_schema_parity.py tests/test_required_schema_completeness.py
```

## Completion

- [ ] Each handwritten document module is deleted.
- [ ] Registry is composition only.
- [ ] Contracts come from charters/generated document schemas.
- [ ] Generated contract manifests are refreshed through the new contract path.
- [ ] Search, type, and test gates pass.
