"""Phase 7a-world-C3: the WorldQuery query/bind glue over a ``WorldStore``.

These exercise the render-time glue in :mod:`propstore.world.model` — bind,
active_graph, compiled_graph, intervene/observe (via the ``causal_models``
substrate), and chain_query — over the in-memory charter feed. The concrete
repo-backed ``WorldQuery`` reader (sqlite/sidecar/embeddings/diagnostics) is
Phase 9; it satisfies the same ``WorldStore`` protocol and reuses this glue.
"""

from __future__ import annotations

from propstore.world import model
from propstore.world.bound import BoundWorld
from propstore.core.environment import Environment
from propstore.core.graph_types import ActiveWorldGraph, CompiledWorldGraph
from propstore.world.types import ChainResult, ResolutionStrategy, ValueStatus

from tests.atms_feed import ClaimSpec, ParamSpec, build_bound


def _store_with(*, claims: tuple[ClaimSpec, ...], params: tuple[ParamSpec, ...] = ()):
    # build_bound assembles the charters and the in-memory store; reuse its store.
    bound = build_bound(claims=claims, parameterizations=params)
    return bound.store


def test_compiled_graph_lowers_store_to_graph() -> None:
    store = _store_with(
        claims=(ClaimSpec(claim_id="c1", concept_id="A", value=2.0),),
    )
    compiled = model.compiled_graph(store)
    assert isinstance(compiled, CompiledWorldGraph)
    assert {str(node.claim_id) for node in compiled.claims} == {"c1"}


def test_active_graph_partitions_under_environment() -> None:
    store = _store_with(
        claims=(
            ClaimSpec(claim_id="c1", concept_id="A", value=2.0, conditions=("region == 'eu'",)),
            ClaimSpec(claim_id="c2", concept_id="A", value=3.0),
        ),
    )
    active = model.active_graph(store, Environment(bindings={"region": "us"}))
    assert isinstance(active, ActiveWorldGraph)
    assert "c2" in {str(claim_id) for claim_id in active.active_claim_ids}
    # c1's eu-only condition is incompatible with region==us → inactive.
    assert "c1" in {str(claim_id) for claim_id in active.inactive_claim_ids}


def test_bind_returns_bound_world_with_active_graph() -> None:
    store = _store_with(claims=(ClaimSpec(claim_id="c1", concept_id="A", value=2.0),))
    bound = model.bind(store, Environment(bindings={}))
    assert isinstance(bound, BoundWorld)
    assert bound.value_of("A").status is ValueStatus.DETERMINED


def test_bind_merges_keyword_conditions() -> None:
    store = _store_with(
        claims=(
            ClaimSpec(claim_id="c1", concept_id="A", value=2.0, conditions=("region == 'eu'",)),
        ),
    )
    bound = model.bind(store, region="eu")
    assert bound.value_of("A").status is ValueStatus.DETERMINED
    bound_us = model.bind(store, region="us")
    assert bound_us.value_of("A").status is ValueStatus.NO_CLAIMS


def test_chain_query_derives_target_through_parameterization() -> None:
    store = _store_with(
        claims=(
            ClaimSpec(claim_id="a", concept_id="A", value=2.0),
            ClaimSpec(claim_id="b", concept_id="B", value=3.0),
        ),
        params=(ParamSpec(output="C", inputs=("A", "B"), sympy="A + B"),),
    )
    result = model.chain_query(store, "C")
    assert isinstance(result, ChainResult)
    assert result.result.status is ValueStatus.DERIVED
    assert result.result.value == 5.0
    sources = {step.concept_id: step.source for step in result.steps}
    assert sources["A"] == "claim"
    assert sources["C"] == "derived"


def test_chain_query_records_unresolved_conflict_without_strategy() -> None:
    store = _store_with(
        claims=(
            ClaimSpec(claim_id="a1", concept_id="A", value=2.0),
            ClaimSpec(claim_id="a2", concept_id="A", value=9.0),
        ),
    )
    result = model.chain_query(store, "A")
    assert result.result.status is ValueStatus.CONFLICTED
    assert "A" in {str(concept_id) for concept_id in result.unresolved_dependencies}


def test_chain_query_resolves_conflict_with_strategy() -> None:
    store = _store_with(
        claims=(
            ClaimSpec(claim_id="a1", concept_id="A", value=2.0, sample_size=10),
            ClaimSpec(claim_id="a2", concept_id="A", value=9.0, sample_size=200),
        ),
    )
    result = model.chain_query(store, "A", strategy=ResolutionStrategy.SAMPLE_SIZE)
    resolved_steps = [step for step in result.steps if step.source == "resolved"]
    assert resolved_steps and resolved_steps[0].value == 9.0
    assert result.unresolved_dependencies == []


def test_intervene_builds_pearl_world_over_compiled_graph() -> None:
    store = _store_with(
        claims=(
            ClaimSpec(claim_id="a", concept_id="A", value=2.0),
            ClaimSpec(claim_id="b", concept_id="B", value=3.0),
        ),
        params=(ParamSpec(output="C", inputs=("A", "B"), sympy="A + B"),),
    )
    world = model.intervene(store, {"A": 1.0, "B": 2.0})
    assert world.derived_value("C").value == 3.0


def test_observe_builds_observation_world_over_compiled_graph() -> None:
    store = _store_with(
        claims=(
            ClaimSpec(claim_id="a", concept_id="A", value=2.0),
            ClaimSpec(claim_id="b", concept_id="B", value=3.0),
        ),
        params=(ParamSpec(output="C", inputs=("A", "B"), sympy="A + B"),),
    )
    world = model.observe(store, {"C": 9.0}, exogenous_assignment={"A": 4.0, "B": 5.0})
    assert world.derived_value("C").value == 9.0


def test_chain_query_echoes_bindings_in_the_type_they_were_passed() -> None:
    """A binding comes back as the binding you gave, not a rewrite of it.

    ``bindings_used`` used to be ``dict[str, Any]`` holding the result of the
    narrowing that exists for ``ChainStep.value`` (``float | str | None``), so a
    bool binding echoed back as the string ``"True"`` and an int as a float. A
    binding scalar has one spelling — the one ``Environment.bindings`` and
    ``chain_query`` itself already declare.
    """
    store = _store_with(
        claims=(ClaimSpec(claim_id="a", concept_id="A", value=2.0),),
        params=(),
    )

    result = model.chain_query(store, "A", flag=True, count=3, label="x", ratio=1.5)

    assert result.bindings_used == {
        "flag": True,
        "count": 3,
        "label": "x",
        "ratio": 1.5,
    }
