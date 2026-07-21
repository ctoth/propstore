"""Owner-layer world reasoning-report tier (Phase 10-0b).

Exercises the typed report builders over a repo-backed ``WorldQuery``:
status / concept-query / bind / explain / algorithms / derive / resolve / chain /
hypothetical-diff. Charter-shaped (no ``*Row`` projection), built over
``Repository.init`` -> author charters -> ``materialize_world_sidecar`` ->
``WorldQuery`` (the same recipe as ``test_world_query``).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.families.relations import Stance
from propstore.repository import Repository
from propstore.stances import StanceType
from propstore.world import RenderPolicy, WorldQuery
from propstore.world.reasoning_reports import (
    UnknownClaimError,
    UnknownConceptError,
    WorldAlgorithmsRequest,
    WorldBindActiveReport,
    WorldBindConceptReport,
    WorldBindRequest,
    WorldChainRequest,
    WorldConceptQueryRequest,
    WorldDeriveRequest,
    WorldExplainRequest,
    WorldHypotheticalRequest,
    WorldHypotheticalSyntheticClaimSpec,
    WorldResolveRequest,
    WorldStatusRequest,
    derive_world_value,
    diff_hypothetical_world,
    explain_world_claim,
    get_world_status,
    list_world_algorithms,
    query_bound_world,
    query_world_chain,
    query_world_concept,
    resolve_world_value,
)
from propstore.world.types import ResolutionStrategy


def _repo(tmp_path: Path) -> Repository:
    repo = Repository.init(tmp_path / "kn")
    for concept_id in ("A", "B", "C", "D", "speed"):
        repo.families.concept.save(
            concept_id,
            Concept(concept_id=concept_id, canonical_name=concept_id),
            message="m",
        )
    repo.families.context.save(
        "ctx1", Context(context_id="ctx1", name="ctx"), message="m"
    )
    # Parameter-claim ids sort before the equation-claim id so the value layer's
    # collect_known_values (which reads the first claim) picks the valued claim.
    repo.families.claim.save(
        "aa_pa",
        Claim(
            claim_id="aa_pa",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="A",
            value=2.0,
        ),
        message="m",
    )
    repo.families.claim.save(
        "ab_pb",
        Claim(
            claim_id="ab_pb",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="B",
            value=3.0,
        ),
        message="m",
    )
    repo.families.claim.save(
        "zz_eq",
        Claim(
            claim_id="zz_eq",
            context_id="ctx1",
            claim_type=ClaimType.EQUATION,
            output_concept="C",
            concepts=("A", "B"),
            expression="A + B",
            sympy="A + B",
        ),
        message="m",
    )
    repo.families.claim.save(
        "alg1",
        Claim(
            claim_id="alg1",
            context_id="ctx1",
            claim_type=ClaimType.ALGORITHM,
            output_concept="D",
            name="algo one",
            body="def f(x):\n    return x\n",
        ),
        message="m",
    )
    # Two conflicting parameter claims for `speed`, with a rebutting stance.
    repo.families.claim.save(
        "s1",
        Claim(
            claim_id="s1",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="speed",
            value=10.0,
        ),
        message="m",
    )
    repo.families.claim.save(
        "s2",
        Claim(
            claim_id="s2",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="speed",
            value=20.0,
        ),
        message="m",
    )
    repo.families.stance.save(
        "st1",
        Stance(
            stance_id="st1",
            source_claim_id="s1",
            target_claim_id="s2",
            stance_type=StanceType.REBUTS,
        ),
        message="m",
    )
    return repo


@pytest.fixture
def world(tmp_path: Path) -> WorldQuery:
    return WorldQuery(_repo(tmp_path))


def test_get_world_status(world: WorldQuery) -> None:
    report = get_world_status(world, WorldStatusRequest(policy=RenderPolicy()))
    assert report.concept_count == 5
    assert report.visible_claim_count == 6
    assert report.stance_count == 1
    assert report.to_json()["concept_count"] == 5


def test_query_world_concept(world: WorldQuery) -> None:
    report = query_world_concept(
        world, WorldConceptQueryRequest(target="A", policy=RenderPolicy())
    )
    assert report.canonical_name == "A"
    assert report.concept_display_id == "A"
    # claims_for("A") matches pa (value-concept A) and eq (A is an equation input).
    display_ids = {line.display_id for line in report.claims}
    assert "aa_pa" in display_ids
    assert "zz_eq" in display_ids


def test_query_world_concept_unknown_raises(world: WorldQuery) -> None:
    with pytest.raises(UnknownConceptError):
        query_world_concept(
            world, WorldConceptQueryRequest(target="nope", policy=RenderPolicy())
        )


def test_query_bound_world_target(world: WorldQuery) -> None:
    report = query_bound_world(world, WorldBindRequest(bindings={}, target="A"))
    assert isinstance(report, WorldBindConceptReport)
    assert report.status == "determined"
    # The value layer reports every active claim associated with A (the parameter
    # claim that determines it and the equation that references it as an input).
    assert "aa_pa" in {line.display_id for line in report.claims}


def test_query_bound_world_active(world: WorldQuery) -> None:
    report = query_bound_world(world, WorldBindRequest(bindings={}))
    assert isinstance(report, WorldBindActiveReport)
    assert report.active_claim_count == 6


def test_explain_world_claim(world: WorldQuery) -> None:
    report = explain_world_claim(world, WorldExplainRequest(claim_id="s1"))
    assert report.claim_display_id == "s1"
    assert report.concept_display_id == "speed"
    assert report.value == 10.0
    assert any(line.target_display_id == "s2" for line in report.stances)


def test_explain_world_claim_unknown_raises(world: WorldQuery) -> None:
    with pytest.raises(UnknownClaimError):
        explain_world_claim(world, WorldExplainRequest(claim_id="nope"))


def test_list_world_algorithms(world: WorldQuery) -> None:
    report = list_world_algorithms(world, WorldAlgorithmsRequest())
    assert [a.claim_id for a in report.algorithms] == ["alg1"]
    assert report.algorithms[0].name == "algo one"
    assert report.algorithms[0].concept_id == "D"


def test_derive_world_value(world: WorldQuery) -> None:
    report = derive_world_value(
        world, WorldDeriveRequest(concept_id="C", bindings={}, policy=RenderPolicy())
    )
    assert report.concept_id == "C"
    assert report.status == "derived"
    assert report.value == 5.0


def test_resolve_world_value_conflicted(world: WorldQuery) -> None:
    report = resolve_world_value(
        world,
        WorldResolveRequest(
            concept_id="speed",
            bindings={},
            policy=RenderPolicy(strategy=ResolutionStrategy.ARGUMENTATION),
        ),
    )
    assert report.concept_display_id == "speed"
    # s1 rebuts s2, so grounded argumentation accepts s1 as the winner.
    assert report.status == "resolved"
    assert report.winning_claim_display_id == "s1"
    assert report.value == 10.0


def test_query_world_chain(world: WorldQuery) -> None:
    report = query_world_chain(world, WorldChainRequest(concept_id="C", bindings={}))
    assert report.target.display_id == "C"
    assert report.status == "derived"
    assert report.value == 5.0
    assert any(
        step.concept.display_id == "C" and step.source == "derived"
        for step in report.steps
    )


def test_diff_hypothetical_world(world: WorldQuery) -> None:
    report = diff_hypothetical_world(
        world,
        WorldHypotheticalRequest(
            bindings={},
            add_claims=(
                WorldHypotheticalSyntheticClaimSpec(
                    claim_id="syn_a",
                    concept_id="A",
                    claim_type="parameter",
                    value=100.0,
                ),
            ),
        ),
    )
    # Adding a second value for A makes it conflicted where it was determined.
    changed = {line.concept_display_id for line in report.changes}
    assert "A" in changed
    assert report.extension_diff.before.active >= 1
    # JSON-ready end to end.
    assert "changes" in report.to_json()
