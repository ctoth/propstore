"""Phase 8-5 import-discipline proof: imports are defeasible, never truth.

The load-bearing invariant of the import subsystem (CLAUDE.md;
[[feedback_imports_are_opinions]]): every imported row is a defeasible claim
with honest provenance, indistinguishable in privilege from any other claim. It
goes through the source-authoring path (no direct canonical write to ``master``),
carries a ``stated``/``defaulted`` provenance status (never ``measured`` /
``calibrated``), and is then subject to the ordinary finalize -> promote
lifecycle.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.claims import ClaimType
from propstore.importing.contract import (
    ImportClaimRow,
    ImportConceptRow,
    ImportManifest,
    ImportStanceRow,
)
from propstore.importing.repository_import import import_manifest
from propstore.provenance import ProvenanceStatus, read_provenance_note
from propstore.repository import Repository
from propstore.source.common import (
    load_source_claims_document,
    load_source_document,
    source_branch_name,
)
from propstore.stances import StanceType

_SOURCE = "BFO Upper Ontology"


def _manifest(status: ProvenanceStatus) -> ImportManifest:
    return ImportManifest(
        source_name=_SOURCE,
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=SourceOriginType.MANUAL,
        origin_value="bfo.owl",
        provenance_status=status,
        concepts=(
            ImportConceptRow(local_name="continuant", definition="A BFO continuant.", form="structural"),
            ImportConceptRow(local_name="occurrent", definition="A BFO occurrent.", form="structural"),
        ),
        claims=(
            ImportClaimRow(
                local_id="claim_one",
                claim_type=ClaimType.OBSERVATION,
                context="ctx",
                statement="A continuant persists.",
                concepts=("continuant",),
            ),
            ImportClaimRow(
                local_id="claim_two",
                claim_type=ClaimType.OBSERVATION,
                context="ctx",
                statement="An occurrent unfolds.",
                concepts=("occurrent",),
            ),
        ),
        stances=(
            ImportStanceRow(source_claim="claim_one", target="claim_two", stance_type=StanceType.REBUTS),
        ),
    )


def test_measured_import_is_rejected_at_the_contract() -> None:
    # An import can never launder an external row into a measured/calibrated origin.
    with pytest.raises(ValueError, match="not honest"):
        _manifest(ProvenanceStatus.MEASURED)


def test_import_lands_on_source_branch_not_master(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    result = import_manifest(repo, _manifest(ProvenanceStatus.STATED))

    # The rows landed on the source branch...
    assert result.source_branch == source_branch_name(_SOURCE)
    claims = load_source_claims_document(repo, _SOURCE)
    assert claims is not None
    assert {claim.source_local_id for claim in claims.claims} == {"claim_one", "claim_two"}
    # ...and NOT as canonical facts on master (no direct canonical write).
    assert list(repo.families.claim.iter_handles()) == []
    assert list(repo.families.concept.iter_handles()) == []


def test_imported_rows_carry_honest_stated_provenance(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    result = import_manifest(repo, _manifest(ProvenanceStatus.STATED))

    # The source manifest trust records the honest stated status, never measured.
    assert result.provenance_status is ProvenanceStatus.STATED
    source_doc = load_source_document(repo, _SOURCE)
    assert source_doc.trust.status is ProvenanceStatus.STATED

    # A git provenance note rides on the import commit with a stated status.
    provenance = read_provenance_note(repo.require_git().raw_repo, result.commit_sha)
    assert provenance is not None
    assert provenance.status is ProvenanceStatus.STATED
    assert provenance.operations == ("import",)
    assert provenance.witnesses[0].method == "import"


def test_defaulted_import_stays_defaulted(tmp_path: Path) -> None:
    repo = Repository.init(tmp_path / "knowledge")

    result = import_manifest(repo, _manifest(ProvenanceStatus.DEFAULTED))

    assert result.provenance_status is ProvenanceStatus.DEFAULTED
    assert load_source_document(repo, _SOURCE).trust.status is ProvenanceStatus.DEFAULTED
    provenance = read_provenance_note(repo.require_git().raw_repo, result.commit_sha)
    assert provenance is not None
    assert provenance.status is ProvenanceStatus.DEFAULTED


def test_imported_claim_has_no_privileged_identity(tmp_path: Path) -> None:
    # An imported claim is shaped exactly like a hand-authored source claim:
    # content-stable artifact id + version id, no truth marker.
    repo = Repository.init(tmp_path / "knowledge")

    import_manifest(repo, _manifest(ProvenanceStatus.STATED))

    claims = load_source_claims_document(repo, _SOURCE)
    assert claims is not None
    for claim in claims.claims:
        assert claim.artifact_id is not None and claim.artifact_id.startswith("ps:claim:")
        assert claim.version_id is not None and claim.version_id.startswith("sha256:")
