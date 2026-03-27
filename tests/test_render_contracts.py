from __future__ import annotations

from propstore.cli.repository import Repository
from propstore.world import (
    ArtifactStore,
    BeliefSpace,
    Environment,
    ReasoningBackend,
    RenderPolicy,
    ResolutionStrategy,
)


def test_render_policy_defaults():
    policy = RenderPolicy()

    assert policy.reasoning_backend == ReasoningBackend.CLAIM_GRAPH
    assert policy.strategy is None
    assert policy.semantics == "grounded"
    assert policy.comparison == "elitist"
    assert not hasattr(policy, "confidence_threshold")


def test_environment_defaults():
    env = Environment()

    assert dict(env.bindings) == {}
    assert env.context_id is None


def test_render_policy_serialization_roundtrip():
    policy = RenderPolicy.from_dict({
        "reasoning_backend": "praf",
        "strategy": "argumentation",
        "semantics": "preferred",
        "comparison": "democratic",
        "decision_criterion": "hurwicz",
        "pessimism_index": 0.7,
        "show_uncertainty_interval": True,
        "praf_strategy": "mc",
        "praf_mc_epsilon": 0.02,
        "praf_mc_confidence": 0.9,
        "praf_treewidth_cutoff": 8,
        "praf_mc_seed": 123,
        "future_queryables": ["y == 2"],
        "future_limit": 4,
    })

    restored = RenderPolicy.from_dict(policy.to_dict())

    assert restored == policy


def test_environment_serialization_roundtrip():
    env = Environment.from_dict({
        "bindings": {"location": "earth"},
        "context_id": "ctx_physics",
        "effective_assumptions": ["framework == 'physics'"],
        "assumptions": [{
            "assumption_id": "binding:location:abc",
            "kind": "binding",
            "source": "location",
            "cel": "location == 'earth'",
        }],
    })

    restored = Environment.from_dict(env.to_dict())

    assert restored == env


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
