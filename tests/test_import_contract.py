"""Phase 8-5 import-contract validation tests.

The import contract enforces provenance honesty at the boundary: an imported row
is a defeasible claim the external source *asserts* (``stated``) or a *fallback*
(``defaulted``) — never a value the system measured or calibrated. These tests
pin that an :class:`ImportManifest` refuses to be constructed with a laundered
provenance status, and that the typed candidate rows reject empty handles.
"""

from __future__ import annotations

import pytest

from propstore.core.source_types import SourceKind, SourceOriginType
from propstore.families.claims import ClaimType
from propstore.importing.contract import (
    ImportClaimRow,
    ImportConceptRow,
    ImportManifest,
    ImportStanceRow,
)
from propstore.provenance import ProvenanceStatus
from propstore.stances import StanceType


def _manifest(status: ProvenanceStatus) -> ImportManifest:
    return ImportManifest(
        source_name="External KB",
        kind=SourceKind.ACADEMIC_PAPER,
        origin_type=SourceOriginType.MANUAL,
        origin_value="manual",
        provenance_status=status,
    )


@pytest.mark.parametrize(
    "status",
    [ProvenanceStatus.STATED, ProvenanceStatus.DEFAULTED],
)
def test_manifest_accepts_honest_import_statuses(status: ProvenanceStatus) -> None:
    assert _manifest(status).provenance_status is status


@pytest.mark.parametrize(
    "status",
    [
        ProvenanceStatus.MEASURED,
        ProvenanceStatus.CALIBRATED,
        ProvenanceStatus.VACUOUS,
    ],
)
def test_manifest_rejects_laundered_import_statuses(status: ProvenanceStatus) -> None:
    with pytest.raises(ValueError, match="not honest"):
        _manifest(status)


def test_manifest_requires_source_name_and_origin() -> None:
    with pytest.raises(ValueError, match="source_name"):
        ImportManifest(
            source_name="   ",
            kind=SourceKind.ACADEMIC_PAPER,
            origin_type=SourceOriginType.MANUAL,
            origin_value="manual",
            provenance_status=ProvenanceStatus.STATED,
        )


def test_concept_row_requires_fields() -> None:
    with pytest.raises(ValueError, match="concept definition"):
        ImportConceptRow(local_name="temp", definition="  ", form="structural")


def test_claim_row_requires_local_id() -> None:
    with pytest.raises(ValueError, match="claim local_id"):
        ImportClaimRow(local_id="", claim_type=ClaimType.OBSERVATION, context="ctx")


def test_stance_row_requires_handles() -> None:
    with pytest.raises(ValueError, match="stance target"):
        ImportStanceRow(source_claim="a", target="   ", stance_type=StanceType.REBUTS)


def test_stance_row_keeps_known_type() -> None:
    row = ImportStanceRow(source_claim="a", target="b", stance_type=StanceType.REBUTS)
    assert row.stance_type is StanceType.REBUTS
