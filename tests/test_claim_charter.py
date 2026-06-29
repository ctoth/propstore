"""Phase 3 claim-charter tests: ONE Claim type, author -> store -> sidecar ->
render, with the non-commitment proof (every status projected, render filters).

Behavioral tests over the real quire substrate (in-memory git store + on-disk
sqlite sidecar). They prove the charter-driven architecture for claims, mirroring
the concept/form skeletons.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.families.claims import (
    Claim,
    ClaimRepository,
    ClaimStatus,
    ClaimType,
)


@pytest.fixture
def repo() -> ClaimRepository:
    return ClaimRepository()


def test_claim_columns_fall_out_of_the_charter() -> None:
    """The sidecar columns ARE the charter fields — no hand-authored DTO/Row."""

    schema_object = Claim.__charter__.to_schema_object()
    column_names = {field.name for field in schema_object.fields}
    assert {
        "claim_id",
        "claim_type",
        "status",
        "conditions",
        "conditions_ir",
        "value",
        "unit",
        "output_concept",
    } <= column_names
    # The SQLAlchemy model name is derived from the one charter, not authored.
    assert Claim.__charter_model__.__name__ == "ClaimModel"


def test_author_then_get_round_trips_the_raw_claim(repo: ClaimRepository) -> None:
    claim = Claim(
        claim_id="c1",
        claim_type=ClaimType.PARAMETER,
        output_concept="freq",
        value=200.0,
        unit="Hz",
        conditions=("freq > 10",),
    )
    repo.author(claim, message="author c1")
    loaded = repo.get("c1")
    assert loaded == claim


def test_build_sidecar_projects_every_claim_including_blocked(
    repo: ClaimRepository, tmp_path: Path
) -> None:
    """Non-commitment: a BLOCKED/DRAFT claim is a row just like an AUTHORED one."""

    repo.author(Claim(claim_id="ok", status=ClaimStatus.AUTHORED), message="ok")
    repo.author(Claim(claim_id="draft", status=ClaimStatus.DRAFT), message="draft")
    repo.author(Claim(claim_id="blocked", status=ClaimStatus.BLOCKED), message="blk")

    sidecar = tmp_path / "claim.sqlite"
    schema = repo.build_sidecar(sidecar)
    ids = {c.claim_id for c in repo.render_claims(sidecar, schema)}
    assert ids == {"ok", "draft", "blocked"}


def test_render_round_trips_the_one_claim_type(
    repo: ClaimRepository, tmp_path: Path
) -> None:
    claim = Claim(
        claim_id="c1",
        claim_type=ClaimType.OBSERVATION,
        statement="frequencies fall",
        concepts=("freq",),
        conditions=("freq > 10",),
        value=12.5,
        unit="Hz",
    )
    repo.author(claim, message="author")
    sidecar = tmp_path / "claim.sqlite"
    schema = repo.build_sidecar(sidecar)
    rendered = {c.claim_id: c for c in repo.render_claims(sidecar, schema)}
    assert rendered["c1"] == claim
