"""WS-J Step 2: equivalent capture failures hash identically."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from propstore.world import Environment
from propstore.world.types import ReasoningBackend, RenderPolicy, ResolutionStrategy
from propstore.worldline import WorldlineDefinition, WorldlineInputs, run_worldline
from propstore.worldline.result_types import WorldlineTargetValue


class _FakeWorld:
    _bound: _FakeBound | None = None

    def bind(self, environment, *, policy=None):
        return self._bound or _FakeBound()

    def resolve_concept(self, name):
        return f"concept:{name}"

    def get_concept(self, concept_id):
        return {"id": concept_id, "canonical_name": str(concept_id).removeprefix("concept:")}

    def has_table(self, name):
        return name == "relation_edge"

    def parameterizations_for(self, concept_id):
        return []


class _FakeBound:
    def active_claims(self):
        return []

    def value_of(self, concept_id):
        return _FakeValueResult()

    def derived_value(self, concept_id, **kwargs):
        return object()


class _FakeValueResult:
    status = "no_claims"
    claims = []


def _argumentation_definition() -> WorldlineDefinition:
    return WorldlineDefinition(
        id="typed-argumentation-error",
        inputs=WorldlineInputs(environment=Environment(), overrides={}),
        policy=RenderPolicy(
            strategy=ResolutionStrategy.ARGUMENTATION,
            reasoning_backend=ReasoningBackend.CLAIM_GRAPH,
            semantics="grounded",
        ),
        targets=("target",),
    )


def _run_argumentation_failure(message: str):
    fake_bound = _FakeBound()
    fake_bound.active_claims = MagicMock(side_effect=RuntimeError(message))
    world = _FakeWorld()
    world._bound = fake_bound

    with (
        patch("propstore.worldline.runner._resolve_concept_name", return_value="concept:target"),
        patch(
            "propstore.worldline.runner._resolve_target",
            return_value=WorldlineTargetValue(
                status="determined",
                value=1.0,
                source="claim",
            ),
        ),
    ):
        return run_worldline(_argumentation_definition(), world)


def test_ws_j_equivalent_argumentation_failures_have_same_content_hash() -> None:
    """J-H1: exception messages are not part of worldline content identity."""

    left = _run_argumentation_failure("backend died at 0xaaa")
    right = _run_argumentation_failure("backend died at 0xbbb")

    from propstore.worldline.result_types import WorldlineCaptureError

    assert left.argumentation is not None
    assert right.argumentation is not None
    assert left.argumentation.error == WorldlineCaptureError.ARGUMENTATION
    assert right.argumentation.error == WorldlineCaptureError.ARGUMENTATION
    assert left.argumentation.to_dict()["error"] == "argumentation"
    assert left.content_hash == right.content_hash
