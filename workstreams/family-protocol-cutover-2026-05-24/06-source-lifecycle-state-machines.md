# 06 Source Lifecycle State Machines

## Prerequisites

- `01-deleted-file-fallout-repair.md`
- `02-quire-generated-family-protocols.md`
- `03-generic-family-lookup-cleanup.md`
- `04-family-document-deletion.md`
- `05-registry-contracts-batch-specs.md`

## Target

Source-local authoring, finalization, promotion, status, and alignment are
lifecycle transitions over typed family records. Root source helper modules do
not own document shape, payload rewriting, relationship rewrites, or per-family
loader fanout.

## Deletion Targets

- `ClaimConceptSource = ClaimDocument | SourceClaimDocument | Mapping[str, Any]`
- `rewrite_claim_concept_refs`, `_claim_payload`, and
  `_place_source_local_concept`
- `normalize_source_claims_payload` dict reconstruction
- source relation payload normalization for justifications and stances
- source concept dict projection records and primary-branch match payload
  rewriting
- source-loader fanout in `propstore/source/common.py`
- concrete document-class fields in `SourcePromotionPlan`
- root concept alignment workflow shape after concept/source lifecycle owns it
- direct `claim_core` source-status lookup

## Kept Behavior

- Source branch initialization, notes, metadata, and slug policy.
- Stable source-local claim identity and logical-id policy.
- Source claim CEL, concept, and bounds validation.
- Source-local reference resolution against source and canonical indexes.
- Finalize checks, required context/micropub coverage, artifact stamping, and
  finalize report semantics.
- Promote partial promotion, blocked diagnostics, source trust calibration,
  provenance notes, concept promotion resolution, and canonical writes.
- Concept alignment argument/decision/promotion semantics.

## Execution

1. Delete source status direct table lookup first.
2. Delete hardcoded claim concept rewrite helpers.
3. Move source-local claim identity into claim-family identity/lifecycle policy.
4. Move relation normalization into relation/justification/stance lifecycle
   callbacks over declared reference fields.
5. Move concept preview and parameterization merge preview into concept-family
   lifecycle/reference metadata.
6. Replace finalize and promote concrete document plans with typed
   family-record transition plans.
7. Delete source loader fanout after family generated document APIs are in use.

## Search Gates

```powershell
rg -n -F -- "ClaimDocument | SourceClaimDocument | Mapping" propstore/source propstore tests
rg -n -F -- "convert_document_value(" propstore/source propstore/families tests
rg -n -F -- "SourceClaimDocument" propstore/source propstore tests
rg -n -F -- "SourceConceptEntryDocument" propstore/source propstore tests
rg -n -F -- "SourceJustificationDocument" propstore/source propstore tests
rg -n -F -- "SourceStanceEntryDocument" propstore/source propstore tests
rg -n -F -- "from propstore.families.documents" propstore/source
rg -n -F -- 'derived.schema.table("claim_core")' propstore/source propstore tests
rg -n -F -- "quality_json" propstore tests
rg -n -F -- "derived_from_json" propstore tests
```

## Gates

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label source-lifecycle tests/test_cli_source_status.py tests/test_finalize_micropub_required.py tests/test_source_promotion_alignment.py tests/test_source_promote_dangling_refs.py
```

## Completion

- Source-local and canonical source states are explicit lifecycle states.
- Source modules keep source semantics only; document/field/reference mechanics
  come from charters and generic family APIs.
