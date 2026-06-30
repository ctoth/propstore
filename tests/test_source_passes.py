"""Phase 8-5 semantic-import normalization pipeline tests.

The pipeline turns typed import rows into the canonical source-branch shape:
type coercion, dedup-to-handle warnings, content-stable identity assignment, and
reference lowering of source-local claim handles. These tests exercise the
coercion passes directly and the end-to-end pipeline over a real repository.
"""

from __future__ import annotations

from pathlib import Path

from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.claims import ClaimType
from propstore.importing.contract import (
    ImportClaimRow,
    ImportConceptRow,
    ImportManifest,
    ImportStanceRow,
)
from propstore.provenance import ProvenanceStatus
from propstore.repository import Repository
from propstore.source.common import (
    init_source_branch,
    load_source_claims_document,
    load_source_stances_document,
)
from propstore.source.passes import (
    coerce_claim_rows,
    coerce_concept_rows,
    run_import_pipeline,
)
from propstore.stances import StanceType

_SOURCE = "External KB"


def _seed_branch(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "knowledge")
    init_source_branch(
        repo,
        _SOURCE,
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=SourceOriginType.MANUAL,
        origin_value="manual",
    )
    return repo


def test_coerce_concept_rows_flags_duplicate_handle() -> None:
    rows = (
        ImportConceptRow(local_name="temp", definition="d1", form="structural"),
        ImportConceptRow(local_name="temp", definition="d2", form="structural"),
    )
    document, warnings = coerce_concept_rows(rows)
    assert len(document.concepts) == 2
    assert any("duplicate imported concept handle 'temp'" in w for w in warnings)


def test_coerce_claim_rows_flags_duplicate_handle_without_dropping() -> None:
    rows = (
        ImportClaimRow(local_id="c1", claim_type=ClaimType.OBSERVATION, context="ctx"),
        ImportClaimRow(local_id="c1", claim_type=ClaimType.OBSERVATION, context="ctx"),
    )
    document, warnings = coerce_claim_rows(rows, paper="external_kb")
    # Non-commitment: both rivals are kept, the collision is surfaced as a warning.
    assert len(document.claims) == 2
    assert any("duplicate imported claim handle 'c1'" in w for w in warnings)


def test_pipeline_assigns_content_stable_identity(tmp_path: Path) -> None:
    repo = _seed_branch(tmp_path)
    manifest = ImportManifest(
        source_name=_SOURCE,
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=SourceOriginType.MANUAL,
        origin_value="manual",
        provenance_status=ProvenanceStatus.STATED,
        claims=(
            ImportClaimRow(
                local_id="claim_one",
                claim_type=ClaimType.OBSERVATION,
                context="ctx",
                statement="A stated observation",
            ),
        ),
    )

    result = run_import_pipeline(repo, _SOURCE, manifest)

    assert result.claim_count == 1
    claims = load_source_claims_document(repo, _SOURCE)
    assert claims is not None
    (claim,) = claims.claims
    assert claim.source_local_id == "claim_one"
    assert claim.artifact_id is not None and claim.artifact_id.startswith("ps:claim:")
    assert claim.version_id is not None and claim.version_id.startswith("sha256:")
    assert claim.logical_ids[0].value == claim.id


def test_pipeline_lowers_stance_handles_to_claim_ids(tmp_path: Path) -> None:
    repo = _seed_branch(tmp_path)
    manifest = ImportManifest(
        source_name=_SOURCE,
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=SourceOriginType.MANUAL,
        origin_value="manual",
        provenance_status=ProvenanceStatus.STATED,
        claims=(
            ImportClaimRow(local_id="claim_one", claim_type=ClaimType.OBSERVATION, context="ctx", statement="A"),
            ImportClaimRow(local_id="claim_two", claim_type=ClaimType.OBSERVATION, context="ctx", statement="B"),
        ),
        stances=(
            ImportStanceRow(source_claim="claim_one", target="claim_two", stance_type=StanceType.REBUTS),
        ),
    )

    result = run_import_pipeline(repo, _SOURCE, manifest)

    assert result.stance_count == 1
    claims = load_source_claims_document(repo, _SOURCE)
    stances = load_source_stances_document(repo, _SOURCE)
    assert claims is not None and stances is not None
    artifact_ids = {claim.artifact_id for claim in claims.claims}
    (stance,) = stances.stances
    # The source-local handles have been lowered to canonical claim ids.
    assert stance.source_claim in artifact_ids
    assert stance.target in artifact_ids
    assert stance.source_claim != stance.target
