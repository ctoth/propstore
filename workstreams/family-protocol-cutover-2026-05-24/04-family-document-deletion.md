# 04 Family Document Deletion

## Prerequisites

- `01-deleted-file-fallout-repair.md`
- `02-quire-generated-family-protocols.md`
- `03-generic-family-lookup-cleanup.md`

## Target

Delete handwritten family document classes. Documents remain; handwritten
field-list classes do not. Family documents are generated from charters.

## Deletion Targets

- `propstore/families/claims/documents.py`
- `propstore/families/concepts/documents.py`
- `propstore/families/contexts/documents.py`
- `propstore/families/forms/documents.py`
- `propstore/families/sameas/documents.py`
- `propstore/families/documents/justifications.py`
- `propstore/families/documents/merge.py`
- `propstore/families/documents/micropubs.py`
- `propstore/families/documents/predicates.py`
- `propstore/families/documents/rules.py`
- `propstore/families/documents/source_alignment.py`
- `propstore/families/documents/sources.py`
- `propstore/families/documents/stances.py`
- `propstore/families/documents/worldlines.py`

## Kept Behavior

- Claim type requirements, value groups, unit policy, and concept-link roles
  move to claim-family metadata/callbacks.
- Context lifting semantics move to the context family owner; persisted
  lifting document shape is generated from context charter fields.
- SameAs relation vocabulary moves under the sameas family semantic owner.
- Source, proposal, worldline, rule, predicate, stance, justification, and
  micropublication semantics remain in family/domain owners.

## Execution

1. Start with a small bounded family: `sameas` or `forms`.
2. Delete its handwritten document file first.
3. Repair import/type/test failures by asking the family/charter for generated
   document type/codecs.
4. Commit that family slice.
5. Repeat family by family.
6. Do not replace deleted document classes with local DTOs.

## Search Gates

```powershell
rg -n -F -- "from propstore.families.documents" propstore tests
rg -n -F -- "from propstore.families.claims.documents" propstore tests
rg -n -F -- "from propstore.families.concepts.documents" propstore tests
rg -n -F -- "from propstore.families.contexts.documents" propstore tests
rg -n -F -- "from propstore.families.forms.documents" propstore tests
rg -n -F -- "from propstore.families.sameas.documents" propstore tests
rg -n -F -- "propstore.families.documents." propstore tests
rg -n -F -- "DocumentStruct" propstore/families propstore/source propstore/worldline propstore/support_revision propstore/core
```

## Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label family-doc-deletion tests/test_contract_manifest.py tests/test_claim_roundtrip_fixtures.py tests/test_source_claims.py tests/test_source_relations.py tests/test_worldline.py
```

## Completion

- No handwritten family document class repeats charter fields.
- Every family document is available through the generated family document API.
