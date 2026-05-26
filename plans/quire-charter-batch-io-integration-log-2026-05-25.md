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
- `pyproject.toml`
- `uv.lock`

Surfaces:
- `pyproject.toml` Quire dependency
  - Disposition: rewrite
  - Owner after cleanup: `pyproject.toml`
  - Action: Pinned Quire to pushed commit
    `e8eb5dc31163316bd59d1abd0e7c6a890763baab`.
  - Evidence: `git ls-remote origin refs/heads/master` in Quire returned the
    pinned SHA.
- `uv.lock` Quire dependency
  - Disposition: rewrite
  - Owner after cleanup: `uv.lock`
  - Action: Refreshed the lockfile with `uv lock`.
  - Evidence: Lock entries resolve the remote Quire Git dependency at the
    same pushed SHA.

Gate results:
- Pass: `rg -n -F -- "file://" pyproject.toml uv.lock`
- Pass: `rg -n -F -- "path =" pyproject.toml uv.lock`
- Pass: `rg -n -F -- "C:\\" pyproject.toml uv.lock`
- Pass: `rg -n -F -- "C:/" pyproject.toml uv.lock`
- Pass: `uv run pyright propstore`

Commit:
- `e1176324 Pin Quire batch artifact helper`

Next slice:
- Propstore deletion-first batch cutover.

## Iteration 4 - `propstore source batch helpers`

Slice read:
- `propstore/families/registry.py`
- `propstore/families/batch_specs.py`
- `propstore/claims.py`
- `propstore/source/claims.py`
- `propstore/source/concepts.py`
- `propstore/source/relations.py`
- `propstore/source/alignment.py`
- source batch tests importing `propstore.families.batch_specs`

Surfaces:
- `propstore/families/batch_specs.py`
  - Disposition: delete
  - Owner after cleanup: source family declaration modules
  - Action: Deleted the compatibility re-export module and moved callers to
    owning declaration modules.
  - Evidence: `rg -n -F -- "propstore.families.batch_specs" propstore tests`
    returned zero hits.
- Registry source batch decode/render/payload helpers
  - Disposition: delete
  - Owner after cleanup: Quire `batch_artifact_family`
  - Action: Deleted handwritten source batch helpers and rewired source batch
    family definitions to Quire `batch_artifact_family`.
  - Evidence: Helper-name search gates returned zero hits; contract manifest
    was regenerated after required family and artifact-family version bumps.

Gate results:
- Pass: `rg -n -F -- "propstore.families.batch_specs" propstore tests`
- Pass: `rg -n -F -- "decode_source_claims_document" propstore tests`
- Pass: `rg -n -F -- "render_source_claims_document" propstore tests`
- Pass: `rg -n -F -- "source_claims_document_payload" propstore tests`
- Pass: `rg -n -F -- "_shared_batch_field" propstore tests`
- Pass: `uv run pyright propstore`
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label registry-contracts-batches tests/test_semantic_family_registry.py tests/test_quire_consumer_contracts.py tests/test_contract_manifest.py`
- Initial fail: `powershell -File scripts/run_logged_pytest.ps1 -Label source-batch-io tests/test_cli_source_status.py tests/test_source_claims.py tests/test_source_promotion_alignment.py tests/test_verify_cli.py`
  - Failure: 13 tests fail with SQLAlchemy `NoReferencedTableError` while
    creating the world SQLite schema through `world_schema()`.
  - Evidence: `logs/test-runs/source-batch-io-20260525-195703.log`.
  - Scope note: The failure occurs in `create_sqlalchemy_store(...,
    world_schema())`, after source batch add/finalize paths have already run.
    It was not a source batch codec failure; it exposed Quire SQLAlchemy
    over-emitting SQL constraints for schema-level semantic foreign keys.

Commit:
- `ce702224 Cut source batches to Quire helper`

Next slice:
- Repair Quire SQLAlchemy FK projection and repin Propstore.

## Iteration 5 - `quire SQLAlchemy semantic FK projection`

Slice read:
- `quire/sqlalchemy_schema.py`
- `tests/test_sqlalchemy_engine.py`
- `propstore/families/concepts/declaration.py`

Surfaces:
- JSON-boundary foreign keys
  - Disposition: narrow SQL projection
  - Owner after cleanup: Quire SQLAlchemy schema projection
  - Action: Kept JSON-boundary semantic FKs in schema metadata but skipped SQL
    `ForeignKey` constraints for those JSON columns.
  - Evidence: `authored_concept.relationships` and
    `authored_concept.parameterization_relationships` stopped producing missing
    table errors after Quire commit `a895d11`.
- Foreign keys to families outside the active catalog
  - Disposition: narrow SQL projection
  - Owner after cleanup: Quire SQLAlchemy schema projection
  - Action: Kept semantic FKs in schema metadata but emitted SQL constraints
    only when the target family is present in the active SQLAlchemy catalog.
  - Evidence: `authored_concept.replaced_by` targets canonical `concepts`,
    which is not part of the source-side partial world schema; Quire commit
    `99bf5a2` added the partial-catalog rule and regression coverage.

Gate results:
- Pass: `uv run pytest -vv tests/test_sqlalchemy_engine.py::test_json_boundary_foreign_keys_are_metadata_not_sql_constraints tests/test_sqlalchemy_engine.py::test_foreign_key_can_target_declared_non_id_field`
- Pass: `uv run pytest -vv tests/test_sqlalchemy_engine.py::test_foreign_key_to_family_outside_catalog_is_metadata_not_sql_constraint tests/test_sqlalchemy_engine.py::test_json_boundary_foreign_keys_are_metadata_not_sql_constraints tests/test_sqlalchemy_engine.py::test_foreign_key_can_target_declared_non_id_field`
- Pass: `uv run pyright`
- Pass: `uv run pytest -vv`

Commits:
- `a895d11 Keep JSON foreign keys out of SQL constraints`
- `99bf5a2 Skip SQL FKs outside active catalog`

Next slice:
- Repin Propstore to Quire `99bf5a2`.

## Iteration 6 - `propstore final Quire pin and fixed point`

Slice read:
- `pyproject.toml`
- `uv.lock`
- `plans/quire-charter-batch-io-integration-2026-05-25.md`

Surfaces:
- `pyproject.toml` Quire dependency
  - Disposition: rewrite
  - Owner after cleanup: `pyproject.toml`
  - Action: Pinned Quire to pushed commit
    `99bf5a228af20e94b67a8b7db48fc04bc88893a7`.
  - Evidence: `git ls-remote https://github.com/ctoth/quire refs/heads/master`
    returned the pinned SHA.
- `uv.lock` Quire dependency
  - Disposition: rewrite
  - Owner after cleanup: `uv.lock`
  - Action: Refreshed the lockfile with `uv lock`.
  - Evidence: Lock entries resolve the remote Quire Git dependency at the
    same pushed SHA.

Gate results:
- Pass: `rg -n -F -- "file://" pyproject.toml uv.lock`
- Pass: `rg -n -F -- "path =" pyproject.toml uv.lock`
- Pass: `rg -n -F -- "C:\\" pyproject.toml uv.lock`
- Pass: `rg -n -F -- "C:/" pyproject.toml uv.lock`
- Pass: `uv run pyright propstore`
- Pass: `rg -n -F -- "propstore.families.batch_specs" propstore tests`
- Pass: `rg -n -F -- "decode_source_claims_document" propstore tests`
- Pass: `rg -n -F -- "render_source_claims_document" propstore tests`
- Pass: `rg -n -F -- "source_claims_document_payload" propstore tests`
- Pass: `rg -n -F -- "_shared_batch_field" propstore tests`
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label source-batch-io tests/test_cli_source_status.py tests/test_source_claims.py tests/test_source_promotion_alignment.py tests/test_verify_cli.py`
  - Evidence: `logs/test-runs/source-batch-io-20260525-202302.log`, 28 passed.
- Pass: `powershell -File scripts/run_logged_pytest.ps1 -Label registry-contracts-batches tests/test_semantic_family_registry.py tests/test_quire_consumer_contracts.py tests/test_contract_manifest.py`
  - Evidence: `logs/test-runs/registry-contracts-batches-20260525-202406.log`, 31 passed.

Commit:
- `8edf5704 Pin Quire partial catalog FK fix`

Fixed point:
- Quire owns generic batch artifact IO through `DocumentBatchCodec` and
  `batch_artifact_family`.
- Propstore source batch artifact families are wired through Quire
  `batch_artifact_family`.
- `propstore/families/batch_specs.py` is deleted.
- Registry source batch decode/render/payload helpers are deleted.
- The final forbidden-surface searches return zero hits.
