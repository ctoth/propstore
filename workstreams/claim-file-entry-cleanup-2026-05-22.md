# Claim File Entry Cleanup Fixed-Point Log - 2026-05-22

Target architecture:
- Quire `LoadedDocument.artifact_path` is the loaded-document path owner.
- Claim family documents carry claim fields.
- Claim file-level metadata must be explicit, not attached to generic loaded
  documents by ad hoc attributes.

Forbidden surfaces:
- `setattr(..., "source_path", ...)` on claim loaded documents.
- `setattr(..., "stage", ...)` on claim loaded documents.
- `ClaimFileEntry` hiding `LoadedDocument[ClaimDocument]` and
  `ArtifactHandle[Any, ClaimRef, ClaimDocument]`.
- `loaded_claim_file_from_payload` / `claim_batch_files_from_payload` as loose
  payload helpers outside a proven IO boundary.
- `claim_file_*` helper accessors that hide multiple representations.

Search gates:
- `rg -n -F -- 'setattr(claim_file, "source_path"' propstore tests`
- `rg -n -F -- 'setattr(claim_file, "stage"' propstore tests`
- `rg -n -F -- "ClaimFileEntry" propstore tests`
- `rg -n -F -- "loaded_claim_file_from_payload" propstore tests`
- `rg -n -F -- "claim_batch_files_from_payload" propstore tests`
- `rg -n -F -- "claim_file_" propstore tests`

Runtime gates:
- `powershell -File scripts/run_logged_pytest.ps1 tests/test_algorithm_stage_types.py tests/test_world_query.py::TestTransitiveConsistency::test_no_transitive_when_compatible`
- `uv run pyright propstore`

## Iteration 1 - `claim loaded-document duplicate source path`

Slice read:
- `propstore/claims.py`
- `quire/documents/loaded.py`
- direct `ClaimFileEntry`, `claim_file_*`, `loaded_claim_file_from_payload`,
  and `claim_batch_files_from_payload` references from `propstore` and `tests`
- relevant claim family stage/declaration/pass/reference surfaces

Surfaces:
- `setattr(claim_file, "source_path", source_path)`
  - Classification: compatibility attribute hiding Quire `LoadedDocument`.
  - Disposition: delete.
  - Owner after cleanup: `LoadedDocument.artifact_path`.
  - Action: removed the ad hoc attribute write and updated the only caller to
    read `cf.artifact_path`.
  - Evidence: `.source_path` production search had no claim-file consumers;
    the only claim-file consumer was a test constructing another loaded claim.

Gate results:
- Pass: `rg -n -F -- 'setattr(claim_file, "source_path"' propstore tests`
  returned zero matches.
- Pass:
  `powershell -File scripts/run_logged_pytest.ps1 tests/test_algorithm_stage_types.py tests/test_world_query.py::TestTransitiveConsistency::test_no_transitive_when_compatible`
  returned `4 passed`; `LOG_PATH=logs\test-runs\pytest-20260522-002644.log`.
- Pass: `uv run pyright propstore` returned
  `0 errors, 0 warnings, 0 informations`.

Commit:
- `90b0c8a9 Delete duplicate claim loaded source path`

Next slice:
- Delete or replace file-level `stage` attachment after proving the correct
  owner for claim file-level stage metadata.

## Iteration 2 - `claim loaded-document file stage`

Slice read:
- `propstore/claims.py`
- `quire/documents/loaded.py`
- `propstore/families/batch_specs.py`
- `propstore/families/claims/documents.py`
- `propstore/families/claims/passes/__init__.py`
- `propstore/families/claims/declaration.py`
- `propstore/merge/structured_merge.py`
- `tests/test_algorithm_stage_types.py`

Surfaces:
- `setattr(claim_file, "stage", stage)`
  - Classification: IO boundary carrier metadata, not a claim document field.
  - Disposition: rewrite.
  - Owner after cleanup: explicit `LoadedClaimsFile.stage`.
  - Action: converted `LoadedClaimsFile` from a type alias into an explicit
    loaded claim document carrier with a `stage` field; updated claim loading,
    claim batch decoding, claim stage access, the stage split test, and
    structured merge's synthetic claim entry construction.
  - Evidence: top-level batch `stage` is distinct from `ClaimDocument.stage`,
    which is algorithm stage; `tests/test_algorithm_stage_types.py` asserts
    that split.

Gate results:
- Pass: `rg -n -F -- 'setattr(claim_file, "stage"' propstore tests`
  returned zero matches.
- Pass: `rg -n -F -- 'getattr(claim_file, "stage"' propstore tests`
  returned zero matches.
- Pass:
  `powershell -File scripts/run_logged_pytest.ps1 tests/test_algorithm_stage_types.py tests/test_world_query.py::TestTransitiveConsistency::test_no_transitive_when_compatible tests/test_merge_symmetry_non_claim_files.py`
  returned `5 passed`; `LOG_PATH=logs\test-runs\pytest-20260522-003019.log`.
- Pass: `uv run pyright propstore` returned
  `0 errors, 0 warnings, 0 informations`.

Commit:
- `87af2150 Make claim file stage explicit`

Next slice:
- Delete or replace `ClaimFileEntry` and the `claim_file_*` helper family after
  classifying which callers should accept `LoadedClaimsFile` and which should
  accept Quire `ArtifactHandle` directly.
