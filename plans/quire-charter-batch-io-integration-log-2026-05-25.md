# Cleanup Refactor Fixed-Point Log - 2026-05-25

Target architecture:
- Quire owns generic batch artifact IO through a charter-backed document batch
  codec and artifact-family helper.
- Propstore family declaration modules own semantic batch specs.
- Propstore registry composes source artifact families from Quire metadata and
  does not handwrite source batch decode/render/payload helpers.

Forbidden surfaces:
- `propstore/families/batch_specs.py`
- `propstore.families.batch_specs` imports
- Registry source batch helper functions:
  `decode_source_*_document`, `encode_source_*_document`,
  `render_source_*_document`, `source_*_document_payload`
- Registry helper internals `_shared_batch_field` and `_batch_field_payload`
- Propstore-specific batch codec wrappers in Quire

Search gates:
- `rg -n -F -- "propstore.families.batch_specs" propstore tests`
- `rg -n -F -- "decode_source_claims_document" propstore tests`
- `rg -n -F -- "render_source_claims_document" propstore tests`
- `rg -n -F -- "source_claims_document_payload" propstore tests`
- `rg -n -F -- "_shared_batch_field" propstore tests`

Runtime gates:
- `uv run pytest -vv tests/test_document_batches.py`
- `uv run pyright`
- `uv run pytest -vv`
- `uv run pyright propstore`
- `powershell -File scripts/run_logged_pytest.ps1 -Label registry-contracts-batches tests/test_semantic_family_registry.py tests/test_quire_consumer_contracts.py tests/test_contract_manifest.py`
- `powershell -File scripts/run_logged_pytest.ps1 -Label source-batch-io tests/test_cli_source_status.py tests/test_source_claims.py tests/test_source_promotion_alignment.py tests/test_verify_cli.py`

## Iteration 1 - `quire.documents.batch`

Slice read:
- `quire/documents/batch.py`
- `quire/documents/__init__.py`
- `quire/__init__.py`
- `tests/test_document_batches.py`
- `quire/documents/codecs.py`

Surfaces:
- `DocumentBatchCodec`
  - Disposition: create
  - Owner after cleanup: `quire.documents.batch`
  - Action: Added a generic batch codec backed by `DocumentBatchSpec`,
    `decode_document_batch_bytes`, `render_document_batch`, and
    `document_to_payload`.
  - Evidence: Quire already owned low-level batch parsing/rendering; the codec
    binds that owner surface to artifact-family callback shape without
    Propstore-specific names.

Gate results:
- Pass: `uv run pytest -vv tests/test_document_batches.py`
- Pass: `uv run pyright`
- Pass: `uv run pytest -vv`

Commit:
- `0218cda Add document batch codec`

Next slice:
- Quire artifact family helper.

## Iteration 2 - `quire batch_artifact_family`

Slice read:
- `quire/artifacts.py`
- `quire/__init__.py`
- `tests/test_family_store.py`

Surfaces:
- `batch_artifact_family`
  - Disposition: create
  - Owner after cleanup: `quire.artifacts`
  - Action: Added a generic `ArtifactFamily` constructor that wires
    `DocumentBatchCodec` callbacks and sets `scan_type` from the batch spec.
  - Evidence: The helper uses Quire-owned `DocumentBatchSpec` and
    `document_batch_codec`, with no Propstore-specific policy or wrapper.

Gate results:
- Pass: `uv run pytest -vv tests/test_document_batches.py tests/test_families.py tests/test_family_store.py`
- Pass: `uv run pyright`
- Pass: `uv run pytest -vv`

Commit:
- `e8eb5dc Add batch artifact family helper`

Next slice:
- Propstore Quire pin.

## Iteration 3 - `propstore Quire pin`

Slice read:
- Pending

Surfaces:
- `pyproject.toml` Quire dependency
  - Disposition: rewrite
  - Owner after cleanup: `pyproject.toml`
  - Action: Pending
  - Evidence: Pending
- `uv.lock` Quire dependency
  - Disposition: rewrite
  - Owner after cleanup: `uv.lock`
  - Action: Pending
  - Evidence: Pending

Gate results:
- Pending

Commit:
- Pending

Next slice:
- Propstore deletion-first batch cutover.
