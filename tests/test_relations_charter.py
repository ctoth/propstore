"""Phase 5a stance-charter tests: ONE Stance type, author -> store -> sidecar ->
render, with the non-commitment proof (every stance projected, no pre-render gate)
and the render-time stance summary.

Behavioral tests over the real quire substrate (in-memory git store + on-disk
sqlite sidecar), mirroring the claim charter.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from doxa import Opinion

from propstore.families.relations import (
    Stance,
    StanceRepository,
    stance_summary,
)
from propstore.stances import StanceType


@pytest.fixture
def repo() -> StanceRepository:
    return StanceRepository()


def test_stance_columns_fall_out_of_the_charter() -> None:
    schema_object = Stance.__charter__.to_schema_object()
    column_names = {field.name for field in schema_object.fields}
    assert {
        "stance_id",
        "source_claim_id",
        "target_claim_id",
        "stance_type",
        "opinion_belief",
        "opinion_disbelief",
        "opinion_uncertainty",
        "opinion_base_rate",
    } <= column_names


def test_author_then_get_round_trips_the_raw_stance(repo: StanceRepository) -> None:
    stance = Stance(
        stance_id="s1",
        source_claim_id="c1",
        target_claim_id="c2",
        stance_type=StanceType.REBUTS,
        opinion_belief=0.7,
        opinion_disbelief=0.1,
        opinion_uncertainty=0.2,
        opinion_base_rate=0.5,
    )
    repo.author(stance, message="author s1")
    assert repo.get("s1") == stance


def test_stance_opinion_rebuilds_doxa_opinion() -> None:
    stance = Stance(
        stance_id="s1",
        stance_type=StanceType.SUPPORTS,
        opinion_belief=0.6,
        opinion_disbelief=0.2,
        opinion_uncertainty=0.2,
        opinion_base_rate=0.5,
    )
    assert stance.opinion() == Opinion(0.6, 0.2, 0.2, 0.5)


def test_partial_opinion_is_treated_as_absent() -> None:
    stance = Stance(stance_id="s1", stance_type=StanceType.SUPPORTS, opinion_belief=0.6)
    assert stance.opinion() is None


def test_build_sidecar_projects_every_stance_including_non_attack(
    repo: StanceRepository, tmp_path: Path
) -> None:
    """Non-commitment: a SUPPORTS/ABSTAIN/vacuous stance is a row like any other."""

    repo.author(Stance(stance_id="atk", stance_type=StanceType.REBUTS), message="a")
    repo.author(Stance(stance_id="sup", stance_type=StanceType.SUPPORTS), message="b")
    repo.author(Stance(stance_id="abs", stance_type=StanceType.ABSTAIN), message="c")
    repo.author(
        Stance(
            stance_id="vac",
            stance_type=StanceType.UNDERCUTS,
            opinion_belief=0.0,
            opinion_disbelief=0.0,
            opinion_uncertainty=1.0,
            opinion_base_rate=0.5,
        ),
        message="d",
    )

    sidecar = tmp_path / "stance.sqlite"
    schema = repo.build_sidecar(sidecar)
    ids = {s.stance_id for s in repo.render_stances(sidecar, schema)}
    assert ids == {"atk", "sup", "abs", "vac"}


def test_stance_summary_counts_attacks_without_pruning(
    repo: StanceRepository, tmp_path: Path
) -> None:
    repo.author(
        Stance(
            stance_id="atk",
            stance_type=StanceType.REBUTS,
            resolution_model="model-x",
            opinion_uncertainty=0.2,
        ),
        message="a",
    )
    repo.author(
        Stance(
            stance_id="vac",
            stance_type=StanceType.UNDERCUTS,
            resolution_model="model-x",
            opinion_uncertainty=1.0,
        ),
        message="b",
    )
    repo.author(Stance(stance_id="sup", stance_type=StanceType.SUPPORTS), message="c")

    sidecar = tmp_path / "stance.sqlite"
    schema = repo.build_sidecar(sidecar)
    summary = stance_summary(repo.render_stances(sidecar, schema))

    assert summary.total_stances == 3
    assert summary.included_as_attacks == 2  # rebuts + undercuts; supports excluded
    assert summary.excluded_non_attack == 1
    assert summary.vacuous_count == 1  # the u=1.0 attack edge is counted, not pruned
    assert summary.models == ("model-x",)
    assert summary.mean_uncertainty == pytest.approx((0.2 + 1.0) / 2.0)
