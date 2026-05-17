# Generic Document Batch Envelope Cutover Workstream

Date: 2026-05-17

Status: executable.

This is a new workstream. It does not replace or overwrite
`workstreams/semantic-artifact-family-cutover-workstream-2026-05-11.md`.

## Goal

Delete bespoke per-family aggregate document schemas and replace them with one
Quire-owned generic document batch/envelope mechanism.

Canonical semantic storage is already one artifact per semantic object for the
families covered here. The remaining problem is duplicated batch schema:
source-local, local validation, and import files still define family-specific
`*FileDocument` or source batch classes that restate item-list structure and
keep expansion helpers beside the canonical document path.

The target state:

- canonical storage remains one artifact per semantic object;
- local/import/source batch files are IO envelopes only;
- every batch envelope expands immediately to typed item documents;
- no batch envelope owns item semantic fields, identity, validation,
  artifact-code stamping, reference semantics, or canonical payload logic;
- Quire owns generic envelope decode/encode/load/expand mechanics;
- Propstore owns item document types, source-local policy, promotion policy,
  and envelope placement in source-local families.

## Current Inventory

Read-only searches on 2026-05-17 found exactly two bespoke `*FileDocument`
classes:

```powershell
rg -n "class .*FileDocument" propstore tests
```

Current hits:

- `propstore/families/claims/documents.py:689`: `ClaimsFileDocument`
- `propstore/families/documents/micropubs.py:60`:
  `MicropublicationsFileDocument`

Current source-local batch document classes:

- `propstore/families/documents/sources.py:235`:
  `SourceConceptsDocument`
- `propstore/families/documents/sources.py:370`: `SourceClaimsDocument`
- `propstore/families/documents/sources.py:456`:
  `SourceJustificationsDocument`
- `propstore/families/documents/sources.py:512`: `SourceStancesDocument`

Current non-batch source document/report classes that remain out of this
workstream:

- `SourceDocument`
- `SourceFinalizeReportDocument`

Current canonical aggregate status:

- `PROPSTORE_FAMILY_REGISTRY` uses `ClaimDocument` for
  `PropstoreFamily.CLAIMS`.
- `PROPSTORE_FAMILY_REGISTRY` uses `MicropublicationDocument` for
  `PropstoreFamily.MICROPUBS`.
- `SameAsAssertionDocument` is already the same-as family document type.
- No `SameAsFileDocument` production or test hit exists.
- No `StanceFileDocument`, `RulesFileDocument`, `PredicatesFileDocument`,
  `RuleFileRef`, `PredicateFileRef`, `RULE_FILE_FAMILY`, or
  `PREDICATE_FILE_FAMILY` production hit remains.

## Non-Goals

- Do not change canonical claim, stance, justification, micropublication,
  same-as, rule, or predicate artifact identity.
- Do not change source promotion semantics.
- Do not delete source-local authoring workflows.
- Do not move Propstore source-local policy into Quire.
- Do not add compatibility readers, fallback readers, aliases, bridge
  normalizers, or old/new dual paths.
- Do not introduce a Propstore-local batch framework parallel to Quire.

## Target Quire API

Add generic batch-envelope mechanics to Quire documents.

Owner module:

- `../quire/quire/documents/batch.py`

Public names:

```python
@dataclass(frozen=True)
class DocumentBatchSpec[TDocument]:
    batch_name: str
    item_type: type[TDocument]
    items_field: str
    inherited_item_fields: tuple[str, ...] = ()

@dataclass(frozen=True)
class LoadedBatchItem[TDocument]:
    filename: str
    item_index: int
    artifact_path: TreePath | None
    store_root: TreePath | None
    document: TDocument

def decode_document_batch_bytes(
    payload: bytes,
    spec: DocumentBatchSpec[TDocument],
    *,
    source: str,
) -> tuple[TDocument, ...]: ...

def load_document_batch(
    path: TreePath | Path,
    spec: DocumentBatchSpec[TDocument],
    *,
    store_root: TreePath | Path | None = None,
) -> tuple[LoadedBatchItem[TDocument], ...]: ...

def load_document_batch_dir(
    directory: TreePath | Path | None,
    spec: DocumentBatchSpec[TDocument],
) -> list[LoadedBatchItem[TDocument]]: ...

def render_document_batch(
    items: Sequence[TDocument],
    spec: DocumentBatchSpec[TDocument],
    *,
    inherited_item_values: Mapping[str, object] = {},
) -> str: ...
```

Required Quire behavior:

- decode the top-level YAML mapping;
- require `items_field` to contain a sequence;
- convert each item through `spec.item_type`;
- copy each declared `inherited_item_fields` value from the envelope into each
  item payload only when that item lacks the field;
- preserve item ordering;
- label loaded items as `<batch-filename>#<1-based-index>`;
- reject unknown envelope fields unless they are listed in
  `inherited_item_fields` or are the `items_field`;
- export the public names from `quire.documents`;
- use no Propstore vocabulary.

## Propstore Batch Specs

After the Quire dependency is pinned, Propstore defines these batch specs in
one owner module:

- `propstore/families/batch_specs.py`

Required specs:

| Spec | Item Type | Items Field | Inherited Item Fields | Current Class Deleted |
| --- | --- | --- | --- | --- |
| `CLAIM_BATCH_SPEC` | `ClaimDocument` | `claims` | `source` | `ClaimsFileDocument` |
| `SOURCE_CONCEPT_BATCH_SPEC` | `SourceConceptDocument` | `concepts` | none | `SourceConceptsDocument` |
| `SOURCE_CLAIM_BATCH_SPEC` | `SourceClaimDocument` | `claims` | `source` | `SourceClaimsDocument` |
| `SOURCE_JUSTIFICATION_BATCH_SPEC` | `SourceJustificationDocument` | `justifications` | `source` | `SourceJustificationsDocument` |
| `SOURCE_STANCE_BATCH_SPEC` | `SourceStanceEntryDocument` | `stances` | `source` | `SourceStancesDocument` |
| `SOURCE_MICROPUBLICATION_BATCH_SPEC` | `MicropublicationDocument` | `micropublications` | `source` | `MicropublicationsFileDocument` |

The specs are not semantic schemas. They are IO envelope configuration for
Quire's generic batch loader.

## Dependency Order

Execute in this order:

1. Quire batch envelope tests.
2. Quire batch envelope implementation.
3. Propstore dependency pin.
4. Propstore batch spec module.
5. Delete `ClaimsFileDocument`.
6. Delete source-local concept batch class.
7. Delete source-local claim batch class.
8. Delete source-local justification batch class.
9. Delete source-local stance batch class.
10. Delete source-local micropublication batch class.
11. Artifact-code and source helper cleanup.
12. Contracts, docs, and final gates.

This dependency order is complete. No discovery phase remains.

## Phase 1: Quire Batch Envelope Tests

Repository: `../quire`.

Add tests in `tests/test_document_batches.py`.

Required tests:

- `test_batch_spec_decodes_items_field_to_typed_items`
- `test_batch_spec_inherits_declared_field_into_each_item`
- `test_batch_spec_item_field_wins_over_inherited_field`
- `test_batch_spec_rejects_unknown_envelope_field`
- `test_batch_spec_rejects_missing_items_field`
- `test_batch_spec_rejects_non_sequence_items_field`
- `test_load_document_batch_labels_items_with_batch_index`
- `test_load_document_batch_dir_orders_yaml_children_then_items`
- `test_render_document_batch_round_trips_items`
- `test_quire_documents_exports_batch_api`

Gate:

```powershell
Push-Location ..\quire
uv run pytest tests/test_documents.py tests/test_document_batches.py
uv run pyright quire
Pop-Location
```

## Phase 2: Quire Batch Envelope Implementation

Repository: `../quire`.

Implement:

- `quire/documents/batch.py`
- exports from `quire/documents/__init__.py`
- tests from Phase 1.

Rules:

- no Propstore vocabulary;
- no source/promotion/artifact-code semantics;
- no item-field declarations beyond the caller-supplied `item_type`;
- no untyped catchall for item payloads after conversion.

Full Quire gate:

```powershell
Push-Location ..\quire
uv run pytest
uv run pyright quire
Pop-Location
```

Commit and push Quire. Record the pushed immutable SHA in the Propstore commit
message for Phase 3.

## Phase 3: Propstore Dependency Pin

Repository: `propstore`.

Before editing dependency metadata:

```powershell
rg -n -F 'path = "../' pyproject.toml uv.lock
rg -n -F 'file://' pyproject.toml uv.lock
rg -n -F 'editable = true' pyproject.toml uv.lock
```

All three commands must return no dependency pin hits.

Update Propstore to the pushed Quire SHA from Phase 2.

Gate:

```powershell
uv run pyright propstore
```

## Phase 4: Propstore Batch Spec Module

Repository: `propstore`.

Add:

- `propstore/families/batch_specs.py`

The module contains only the six specs listed in `Propstore Batch Specs`.

Gate:

```powershell
uv run pyright propstore
```

## Phase 5: Delete `ClaimsFileDocument`

Repository: `propstore`.

Delete first:

- `ClaimsFileDocument` from `propstore/families/claims/documents.py`;
- `LoadedClaimBatch` from `propstore/claims.py`;
- `expand_loaded_claim_batch` from `propstore/claims.py`;
- `ClaimsFileDocument` re-export from `propstore/families/claims/__init__.py`;
- contract-manifest schema entries for `ClaimsFileDocument`.

Repair callers to use `CLAIM_BATCH_SPEC` with Quire batch loaders.

Known callers:

- `propstore/app/claims.py`
- `propstore/families/concepts/passes.py`
- `tests/family_helpers.py`
- `tests/test_algorithm_stage_types.py`
- `tests/test_contract_manifest.py`

Old-path gate:

```powershell
rg -n -F "ClaimsFileDocument" propstore tests
rg -n -F "expand_loaded_claim_batch" propstore tests
rg -n -F "LoadedClaimBatch" propstore tests
```

All three commands must return no hits.

Tests:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label claim-batch-envelope tests/test_claim_roundtrip_fixtures.py tests/test_claim_views.py tests/test_concept_views.py tests/test_algorithm_stage_types.py tests/test_contract_manifest.py
uv run pyright propstore
```

## Phase 6: Delete Source Concept Batch Class

Repository: `propstore`.

Delete first:

- `SourceConceptsDocument` from
  `propstore/families/documents/sources.py`.

Repair callers to use `SOURCE_CONCEPT_BATCH_SPEC`.

Known callers:

- `propstore/source/concepts.py`
- `propstore/source/registry.py`
- `propstore/source/common.py`
- `propstore/source/alignment.py`
- `propstore/families/registry.py`
- source concept tests.

Old-path gate:

```powershell
rg -n -F "SourceConceptsDocument" propstore tests
```

Expected final hits: none.

Tests:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label source-concept-batch tests/test_source_promotion_alignment.py tests/test_source_propose.py tests/test_concept_workflows.py
uv run pyright propstore
```

## Phase 7: Delete Source Claim Batch Class

Repository: `propstore`.

Delete first:

- `SourceClaimsDocument` from `propstore/families/documents/sources.py`.

Repair callers to use `SOURCE_CLAIM_BATCH_SPEC`.

Known callers:

- `propstore/artifact_codes.py`
- `propstore/source/claims.py`
- `propstore/source/common.py`
- `propstore/source/finalize.py`
- `propstore/source/promote.py`
- `propstore/source/reference_indexes.py`
- `propstore/families/registry.py`
- source claim and promotion tests.

Old-path gate:

```powershell
rg -n -F "SourceClaimsDocument" propstore tests
```

Expected final hits: none.

Tests:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label source-claim-batch tests/test_source_claims.py tests/test_source_claim_concept_rewrite.py tests/test_source_promote_dangling_refs.py tests/test_source_promotion_alignment.py tests/test_verify_cli.py
uv run pyright propstore
```

## Phase 8: Delete Source Justification Batch Class

Repository: `propstore`.

Delete first:

- `SourceJustificationsDocument` from
  `propstore/families/documents/sources.py`.

Repair callers to use `SOURCE_JUSTIFICATION_BATCH_SPEC`.

Known callers:

- `propstore/artifact_codes.py`
- `propstore/source/relations.py`
- `propstore/source/promote.py`
- `propstore/source/common.py`
- `propstore/source/finalize.py`
- `propstore/families/registry.py`
- verification and source relation tests.

Old-path gate:

```powershell
rg -n -F "SourceJustificationsDocument" propstore tests
```

Expected final hits: none.

Tests:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label source-justification-batch tests/test_source_relations.py tests/test_source_promotion_alignment.py tests/test_verify_cli.py tests/test_ws_f_aspic_bridge.py
uv run pyright propstore
```

## Phase 9: Delete Source Stance Batch Class

Repository: `propstore`.

Delete first:

- `SourceStancesDocument` from `propstore/families/documents/sources.py`.

Repair callers to use `SOURCE_STANCE_BATCH_SPEC`.

Known callers:

- `propstore/artifact_codes.py`
- `propstore/source/relations.py`
- `propstore/source/promote.py`
- `propstore/source/common.py`
- `propstore/source/finalize.py`
- `propstore/families/registry.py`
- source stance and verification tests.

Old-path gate:

```powershell
rg -n -F "SourceStancesDocument" propstore tests
```

Expected final hits: none.

Tests:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label source-stance-batch tests/test_source_relations.py tests/test_source_promotion_alignment.py tests/test_verify_cli.py tests/test_relate_opinions.py
uv run pyright propstore
```

## Phase 10: Delete Source Micropublication Batch Class

Repository: `propstore`.

Delete first:

- `MicropublicationsFileDocument` from
  `propstore/families/documents/micropubs.py`.

Repair callers to use `SOURCE_MICROPUBLICATION_BATCH_SPEC`.

Known callers:

- `propstore/source/finalize.py`
- `propstore/source/promote.py`
- `propstore/source/common.py`
- `propstore/families/registry.py`
- micropublication tests.

Old-path gate:

```powershell
rg -n -F "MicropublicationsFileDocument" propstore tests
```

Expected final hits: none.

Tests:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label source-micropub-batch tests/test_micropub_identity_not_logical_handle.py tests/test_micropublications_phase4.py tests/test_source_promotion_alignment.py tests/test_world_query.py
uv run pyright propstore
```

## Phase 11: Artifact-Code And Source Helper Cleanup

Repository: `propstore`.

Delete any source-local artifact-code or source helper branch that exists only
because batch classes were concrete document types.

Old-path gates:

```powershell
rg -n -F "ClaimsFileDocument" propstore tests
rg -n -F "SourceConceptsDocument" propstore tests
rg -n -F "SourceClaimsDocument" propstore tests
rg -n -F "SourceJustificationsDocument" propstore tests
rg -n -F "SourceStancesDocument" propstore tests
rg -n -F "MicropublicationsFileDocument" propstore tests
rg -n "class .*FileDocument" propstore tests
```

Expected final hits: none for every command.

Tests:

```powershell
powershell -File scripts/run_logged_pytest.ps1 -Label batch-artifact-code tests/test_verify_cli.py tests/test_source_promotion_alignment.py tests/test_source_claims.py tests/test_source_relations.py
uv run pyright propstore
```

## Phase 12: Contracts, Docs, And Final Gates

Repository: `propstore`.

Update:

- semantic contract manifests;
- architecture tests that currently pin concrete batch classes;
- docs mentioning `ClaimsFileDocument`, `SourceClaimsDocument`,
  `SourceJustificationsDocument`, `SourceStancesDocument`,
  `SourceConceptsDocument`, or `MicropublicationsFileDocument`.

Final old-path gates:

```powershell
rg -n -F "ClaimsFileDocument" propstore tests docs AGENTS.md
rg -n -F "SourceConceptsDocument" propstore tests docs AGENTS.md
rg -n -F "SourceClaimsDocument" propstore tests docs AGENTS.md
rg -n -F "SourceJustificationsDocument" propstore tests docs AGENTS.md
rg -n -F "SourceStancesDocument" propstore tests docs AGENTS.md
rg -n -F "MicropublicationsFileDocument" propstore tests docs AGENTS.md
rg -n "class .*FileDocument" propstore tests
```

Final gates:

```powershell
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label generic-batch-envelope-targeted tests/test_claim_roundtrip_fixtures.py tests/test_source_claims.py tests/test_source_relations.py tests/test_source_promotion_alignment.py tests/test_verify_cli.py tests/test_contract_manifest.py tests/test_world_query.py
powershell -File scripts/run_logged_pytest.ps1 -Label generic-batch-envelope-full
```

## Completion Definition

This workstream is complete only when:

- Quire owns generic document batch/envelope loading, expansion, rendering, and
  loaded-item labeling;
- Propstore has exactly one batch-spec module and no Propstore-local generic
  batch framework;
- `ClaimsFileDocument` is deleted;
- `SourceConceptsDocument` is deleted;
- `SourceClaimsDocument` is deleted;
- `SourceJustificationsDocument` is deleted;
- `SourceStancesDocument` is deleted;
- `MicropublicationsFileDocument` is deleted;
- `rg -n "class .*FileDocument" propstore tests` returns no hits;
- canonical family registry entries still use one semantic document type per
  semantic artifact;
- source-local families use Quire batch specs and not bespoke batch document
  classes;
- batch loaders expand immediately to typed item documents;
- artifact-code, validation, import, finalize, and promotion code operate on
  typed item documents after IO decode;
- contract manifests and tests no longer pin bespoke aggregate document schemas;
- Pyright, targeted tests, and full logged pytest pass.
