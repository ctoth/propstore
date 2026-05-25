"""Calibration count typed query contract."""

from __future__ import annotations

from sqlalchemy import select

from quire.artifacts import ArtifactFamily, FlatYamlPlacement
from quire.charters import CharterField, FamilyCharter
from quire.charters import FamilyModel
from quire.families import FamilyDefinition
from quire.sqlalchemy_store import DerivedSession

from propstore.families.meta.declaration import _WORLD_CONTRACT_VERSION


class CalibrationCount(FamilyModel):
    pass


def calibration_charter() -> FamilyCharter:
    return FamilyCharter(
        family=FamilyDefinition(
            key="calibration_counts",
            name="calibration_counts",
            contract_version=_WORLD_CONTRACT_VERSION,
            artifact_family=ArtifactFamily(
                name="propstore-world-calibration_counts",
                contract_version=_WORLD_CONTRACT_VERSION,
                doc_type=CalibrationCount,
                placement=FlatYamlPlacement(".derived/calibration_counts", str),
            ),
            identity_field="pass_number",
        ),
        model=CalibrationCount,
        fields=(
            CharterField("pass_number", int, primary_key=True, nullable=False),
            CharterField("category", str, primary_key=True, nullable=False),
            CharterField("correct_count", int, nullable=False),
            CharterField("total_count", int, nullable=False),
        ),
        semantic_metadata={"semantic": "propstore.world"},
    )


def calibration_counts_by_key(
    derived: DerivedSession,
) -> dict[tuple[int, str], tuple[int, int]] | None:
    """Return calibration evidence keyed by pass number and category."""

    rows = derived.session.execute(select(CalibrationCount)).scalars()
    counts: dict[tuple[int, str], tuple[int, int]] = {}
    for row in rows:
        counts[
            (int(getattr(row, "pass_number")), str(getattr(row, "category")))
        ] = (
            int(getattr(row, "correct_count")),
            int(getattr(row, "total_count")),
        )
    return counts or None
