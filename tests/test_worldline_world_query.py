"""Worldline / PrAF / bound-conflicts over the concrete repo-backed reader.

Closes the Phase-9 deferral rows that needed "a concrete repo-backed store beyond
the in-memory feed" (``docs/rewrite/deferred-tests.md`` §7a-worldline:
``test_worldline`` / ``test_worldline_properties`` / ``test_worldline_praf``, and
§7a-world-B2: ``test_world_bound_conflicts_cache``). The reference suites drive a
``FakeWorld`` of pre-charter dicts; these run the same render-time machinery
(``run_worldline`` / ``build_praf`` / ``BoundWorld`` conflict resolution) over a
real :class:`~propstore.world.WorldQuery` built from authored charters.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from propstore.core.environment import Environment
from propstore.families.claims import Claim, ClaimType
from propstore.families.concepts import Concept
from propstore.families.contexts import Context
from propstore.families.relations import Stance
from propstore.repository import Repository
from propstore.stances import StanceType
from propstore.world import RenderPolicy, WorldQuery
from propstore.world.types import ResolutionStrategy, ValueStatus
from propstore.worldline.definition import WorldlineDefinition, WorldlineInputs
from propstore.worldline.runner import run_worldline
from propstore.worldline.interfaces import WorldlineStore


def _conflict_repo(tmp_path: Path) -> Repository:
    """A concept with two rival unconditional parameter claims, plus a rebuttal."""

    repo = Repository.init(tmp_path / "kn")
    repo.families.concept.save(
        "c1", Concept(concept_id="c1", canonical_name="Speed"), message="m"
    )
    repo.families.context.save(
        "ctx1", Context(context_id="ctx1", name="ctx"), message="m"
    )
    repo.families.claim.save(
        "cl1",
        Claim(
            claim_id="cl1",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="c1",
            value=10.0,
        ),
        message="m",
    )
    repo.families.claim.save(
        "cl2",
        Claim(
            claim_id="cl2",
            context_id="ctx1",
            claim_type=ClaimType.PARAMETER,
            output_concept="c1",
            value=20.0,
        ),
        message="m",
    )
    repo.families.stance.save(
        "s1",
        Stance(
            stance_id="s1",
            source_claim_id="cl1",
            target_claim_id="cl2",
            stance_type=StanceType.REBUTS,
            confidence=0.9,
        ),
        message="m",
    )
    return repo


@pytest.fixture
def world(tmp_path: Path) -> WorldQuery:
    return WorldQuery(_conflict_repo(tmp_path))


def test_world_query_satisfies_worldline_store(world: WorldQuery) -> None:
    assert isinstance(world, WorldlineStore)


def test_bound_world_reports_conflict_over_repo_backed_reader(
    world: WorldQuery,
) -> None:
    # Two rival unconditional parameter claims about one concept ⇒ the bound world
    # surfaces the conflict (the conflict-inputs cache is built once per bind).
    bound = world.bind(Environment())
    result = bound.value_of("c1")
    assert result.status is ValueStatus.CONFLICTED
    assert {str(claim.claim_id) for claim in result.claims} == {"cl1", "cl2"}


def test_run_worldline_over_repo_backed_reader(world: WorldQuery) -> None:
    definition = WorldlineDefinition(
        id="w1",
        inputs=WorldlineInputs(environment=Environment()),
        policy=RenderPolicy(strategy=ResolutionStrategy.RECENCY),
        targets=["Speed"],
    )
    result = run_worldline(definition, world)
    assert "Speed" in result.values
    assert result.content_hash
    # The target resolved over the concrete reader (a status was assigned).
    assert result.values["Speed"].status


def test_run_worldline_argumentation_strategy(world: WorldQuery) -> None:
    definition = WorldlineDefinition(
        id="w1",
        inputs=WorldlineInputs(environment=Environment()),
        policy=RenderPolicy(strategy=ResolutionStrategy.ARGUMENTATION),
        targets=["Speed"],
    )
    result = run_worldline(definition, world)
    # Argumentation capture runs over the real store without error.
    assert result.argumentation is not None
    assert "Speed" in result.values


def test_build_praf_over_repo_backed_reader(world: WorldQuery) -> None:
    from propstore.praf.engine import PropstorePrAF
    from propstore.praf.projection import build_praf

    active_ids = {str(claim.claim_id) for claim in world.claims_for("c1")}
    praf = build_praf(world, active_ids)
    assert isinstance(praf, PropstorePrAF)
