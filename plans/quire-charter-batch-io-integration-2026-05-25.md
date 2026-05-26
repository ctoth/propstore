# Quire Charter Batch IO Integration Plan

Date: 2026-05-25

## Audit Result

Quire already has the core batch mechanics:

- `DocumentBatchSpec`
- `decode_document_batch_bytes`
- `load_document_batch`
- `load_document_batch_dir`
- `render_document_batch`
- `FamilyCharter.batch_specs`
- schema projection for `batch_specs`

The missing piece is not batch parsing. The missing piece is a generic binding
from a charter-owned batch spec to an `ArtifactFamily` codec surface.

Propstore still owns handwritten callbacks in `propstore/families/registry.py`
because Quire does not yet expose a first-class way to say:

> this artifact family is a tuple document encoded by this charter batch spec

and have Quire provide:

- `decode_bytes`
- `encode_document`
- `render_document`
- `document_payload`
- optional `scan_type`

## Target

Quire owns generic artifact-family batch IO. Propstore charters own the batch
specs. Propstore registry composes families from charter metadata and does not
handwrite source batch decode/render/payload helpers.

## Quire Target API

Add a generic batch codec/binding API under `quire.documents.batch`:

```python
@dataclass(frozen=True)
class DocumentBatchCodec(Generic[TDocument]):
    spec: DocumentBatchSpec[TDocument]

    def decode_bytes(self, payload: bytes, source: str) -> tuple[TDocument, ...]: ...
    def encode_document(self, document: tuple[TDocument, ...]) -> bytes: ...
    def render_document(self, document: tuple[TDocument, ...]) -> str: ...
    def document_payload(self, document: tuple[TDocument, ...]) -> dict[str, object]: ...
```

Add a factory:

```python
def document_batch_codec(
    spec: DocumentBatchSpec[TDocument],
    *,
    inherited_item_payload: Callable[[tuple[TDocument, ...]], Mapping[str, object]] | None = None,
) -> DocumentBatchCodec[TDocument]: ...
```

The default codec must:

- decode through `decode_document_batch_bytes`
- render through `render_document_batch`
- encode as UTF-8 rendered YAML
- produce payload `{spec.items_field: [document_to_payload(item) ...]}`
- support inherited envelope fields by deriving inherited values from the item
  tuple when every non-`None` item value is equal

The inherited-field behavior must be generic and data-driven:

- For each `field` in `spec.inherited_item_fields`, inspect `getattr(item, field)`.
- If all present values are equal, put that value in the envelope via
  `document_to_payload` when available.
- If values differ, leave the field on each item; do not invent a policy.

## Quire Integration Point

Add an `ArtifactFamily` constructor/helper, not consumer wrappers:

```python
def batch_artifact_family(
    *,
    name: str,
    contract_version: VersionId,
    placement: ArtifactPlacementPolicy[TOwner, TRef],
    batch_spec: DocumentBatchSpec[TDocument],
) -> ArtifactFamily[TOwner, TRef, tuple[TDocument, ...]]: ...
```

This helper constructs an `ArtifactFamily` with:

- `doc_type=tuple`
- `decode_bytes=codec.decode_bytes`
- `encode_document=codec.encode_document`
- `render_document=codec.render_document`
- `document_payload=codec.document_payload`
- `scan_type=batch_spec.item_type`

Do not add Propstore-specific names or policies to Quire.

## Propstore Target

After Quire is pushed and pinned:

1. Delete `propstore/families/batch_specs.py`.
2. Delete source batch helper functions from `propstore/families/registry.py`:
   - `decode_source_concepts_document`
   - `encode_source_concepts_document`
   - `render_source_concepts_document`
   - `source_concepts_document_payload`
   - `decode_source_claims_document`
   - `encode_source_claims_document`
   - `render_source_claims_document`
   - `source_claims_document_payload`
   - `decode_source_justifications_document`
   - `encode_source_justifications_document`
   - `render_source_justifications_document`
   - `source_justifications_document_payload`
   - `decode_source_stances_document`
   - `encode_source_stances_document`
   - `render_source_stances_document`
   - `source_stances_document_payload`
   - `decode_source_micropubs_document`
   - `encode_source_micropubs_document`
   - `render_source_micropubs_document`
   - `source_micropubs_document_payload`
   - `_shared_batch_field`
   - `_batch_field_payload`
3. Replace the affected source family definitions with the Quire batch helper
   and the batch specs already owned by charters:
   - `SOURCE_CONCEPT_BATCH_SPEC`
   - `SOURCE_CLAIM_BATCH_SPEC`
   - `SOURCE_JUSTIFICATION_BATCH_SPEC`
   - `SOURCE_STANCE_BATCH_SPEC`
   - `SOURCE_MICROPUBLICATION_BATCH_SPEC`
4. Update importers to pull batch specs from owning family declaration modules,
   not `propstore.families.batch_specs`.

## Execution Order

### Phase 1: Quire Batch Codec

1. Add Quire tests for `DocumentBatchCodec`:
   - decodes bytes through `DocumentBatchSpec`
   - renders and encodes batch YAML
   - creates payload from item payloads
   - lifts equal inherited item fields to the envelope
   - leaves differing inherited fields on items
2. Implement `DocumentBatchCodec` and `document_batch_codec`.
3. Export the public API from `quire.documents` and `quire.__init__`.
4. Run:

```powershell
uv run pytest -vv tests/test_document_batches.py
uv run pyright
uv run pytest -vv
```

5. Commit and push Quire.

### Phase 2: Quire Artifact Family Helper

1. Add Quire tests proving `batch_artifact_family` wires an `ArtifactFamily`
   with the generic batch callbacks and `scan_type`.
2. Implement `batch_artifact_family`.
3. Export it.
4. Run:

```powershell
uv run pytest -vv tests/test_document_batches.py tests/test_families.py tests/test_family_store.py
uv run pyright
uv run pytest -vv
```

5. Commit and push Quire.

### Phase 3: Propstore Pin

1. Verify the pushed Quire SHA with `git ls-remote origin refs/heads/master`.
2. Pin Propstore to the pushed commit in `pyproject.toml`.
3. Refresh `uv.lock` with `uv lock`.
4. Run:

```powershell
rg -n -F -- "file://" pyproject.toml uv.lock
rg -n -F -- "path =" pyproject.toml uv.lock
rg -n -F -- "C:\\" pyproject.toml uv.lock
uv run pyright propstore
```

5. Commit only `pyproject.toml` and `uv.lock`.

### Phase 4: Propstore Deletion-First Batch Cutover

1. Delete `propstore/families/batch_specs.py`.
2. Delete the registry source batch helper functions listed above.
3. Run the search gates and use failures as the work queue.
4. Replace source artifact family definitions with Quire `batch_artifact_family`.
5. Update source/test imports to owning declaration modules.
6. Run:

```powershell
rg -n -F -- "propstore.families.batch_specs" propstore tests
rg -n -F -- "decode_source_claims_document" propstore tests
rg -n -F -- "render_source_claims_document" propstore tests
rg -n -F -- "source_claims_document_payload" propstore tests
rg -n -F -- "_shared_batch_field" propstore tests
uv run pyright propstore
powershell -File scripts/run_logged_pytest.ps1 -Label registry-contracts-batches tests/test_semantic_family_registry.py tests/test_quire_consumer_contracts.py tests/test_contract_manifest.py
powershell -File scripts/run_logged_pytest.ps1 -Label source-batch-io tests/test_cli_source_status.py tests/test_source_claims.py tests/test_source_promotion_alignment.py tests/test_verify_cli.py
```

7. Commit only the batch cutover paths.

## Completion

- Quire owns generic batch artifact IO.
- Propstore batch specs remain in family declaration modules.
- Propstore registry no longer owns source batch decode/render/payload helpers.
- `propstore/families/batch_specs.py` is gone.
- No source module imports `propstore.families.batch_specs`.
- Phase 05 can be marked complete for the batch IO portion, unblocking the
  deletion-first Phase 06 source lifecycle cutover.
