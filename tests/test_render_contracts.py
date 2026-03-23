from __future__ import annotations

from propstore.cli.repository import Repository
from propstore.world import ArtifactStore, BeliefSpace, Environment, RenderPolicy, ResolutionStrategy


def test_render_policy_defaults():
    policy = RenderPolicy()

    assert policy.strategy is None
    assert policy.semantics == "grounded"
    assert policy.comparison == "elitist"
    assert policy.confidence_threshold == 0.5


def test_environment_defaults():
    env = Environment()

    assert dict(env.bindings) == {}
    assert env.context_id is None


def test_repository_store_is_cached_property(monkeypatch, tmp_path):
    knowledge = tmp_path / "knowledge"
    repo = Repository.init(knowledge)
    calls: list[object] = []

    class FakeStore:
        def __init__(self, repository):
            calls.append(repository)

    monkeypatch.setattr("propstore.world.WorldModel", FakeStore)

    first = repo.store
    second = repo.store

    assert first is second
    assert calls == [repo]


def test_protocol_shapes():
    assert isinstance(RenderPolicy(), RenderPolicy)
    assert isinstance(Environment(), Environment)
    assert hasattr(ArtifactStore, "__mro__")
    assert hasattr(BeliefSpace, "__mro__")


def test_render_policy_override_fields():
    policy = RenderPolicy(
        strategy=ResolutionStrategy.OVERRIDE,
        overrides={"concept1": "claim1"},
        concept_strategies={"concept2": ResolutionStrategy.RECENCY},
    )

    assert policy.overrides["concept1"] == "claim1"
    assert policy.concept_strategies["concept2"] == ResolutionStrategy.RECENCY
