"""Phase 7a-world-A: store -> compiled graph -> active graph -> AF / PrAF assembly.

Ported from the reference ``test_core_analyzers`` / ``test_praf_integration`` /
``test_argumentation_integration`` / ``test_ws_f_aspic_bridge`` analyzer slices
over an in-memory compiled-graph feed (Phase 7a-world-A builds the store-reading
half over the ``WorldStore`` protocol; the concrete repo store is Phase 9).
"""

from __future__ import annotations

import pytest
from argumentation.core.bipolar import BipolarArgumentationFramework
from argumentation.core.dung import ArgumentationFramework

from propstore.aspic_bridge import build_aspic_projection
from propstore.claim_graph import (
    build_argumentation_framework,
    compute_claim_graph_justified_claims,
)
from propstore.core.analyzers import (
    SharedAnalyzerInput,
    analyze_claim_graph,
    analyze_praf,
    shared_analyzer_input_from_graph,
    shared_analyzer_input_from_store,
)
from propstore.core.graph_types import (
    ActiveWorldGraph,
    ClaimNode,
    CompiledWorldGraph,
    ConflictWitness,
    RelationEdge,
)
from propstore.grounding.bundle import GroundedRulesBundle
from propstore.praf import PropstorePrAF, build_praf
from propstore.probabilistic_relations import ClaimGraphRelations
from propstore.stances import StanceType
from tests.world_store_feed import CompiledGraphStore

_OPINION_STRONG = {
    "confidence": 0.95,
    "opinion_belief": 0.9,
    "opinion_disbelief": 0.03,
    "opinion_uncertainty": 0.07,
    "opinion_base_rate": 0.5,
}
_OPINION_WEAK = {
    "confidence": 0.3,
    "opinion_belief": 0.2,
    "opinion_disbelief": 0.1,
    "opinion_uncertainty": 0.7,
    "opinion_base_rate": 0.15,
}


def _claim(claim_id: str, value: float, *, sample_size: int = 50) -> ClaimNode:
    return ClaimNode(
        claim_id=claim_id,
        claim_type="parameter",
        value_concept_id="temp",
        scalar_value=value,
        attributes={"sample_size": sample_size, "confidence": 1.0},
    )


def _edge(source: str, target: str, relation: str, **opinion: float) -> RelationEdge:
    return RelationEdge(source_id=source, target_id=target, relation_type=relation, attributes=opinion)


def _store(compiled: CompiledWorldGraph) -> CompiledGraphStore:
    return CompiledGraphStore(compiled=compiled)


def _accepted(result) -> set[frozenset[str]]:
    return {frozenset(extension.accepted_claim_ids) for extension in result.extensions}


# --- claim-graph backend ----------------------------------------------------


def test_shared_claim_graph_grounded_matches_compute() -> None:
    store = _store(
        CompiledWorldGraph(
            claims=(_claim("c1", 100.0), _claim("c2", 200.0)),
            relations=(_edge("c1", "c2", "rebuts"), _edge("c2", "c1", "rebuts")),
        )
    )
    shared = shared_analyzer_input_from_store(store, {"c1", "c2"})

    result = analyze_claim_graph(shared, semantics="grounded", target_claim_ids=("c1", "c2"))
    expected = compute_claim_graph_justified_claims(store, {"c1", "c2"}, semantics="grounded")

    assert _accepted(result) == {frozenset(expected)}
    assert result.projection is not None
    assert result.projection.survivor_claim_ids == ()
    assert shared.active_graph is not None


def test_build_argumentation_framework_carries_attacks_and_defeats() -> None:
    store = _store(
        CompiledWorldGraph(
            claims=(_claim("c1", 100.0), _claim("c2", 200.0)),
            relations=(_edge("c1", "c2", "rebuts"), _edge("c2", "c1", "rebuts")),
        )
    )
    framework = build_argumentation_framework(store, {"c1", "c2"})
    assert framework.arguments == frozenset({"c1", "c2"})
    assert framework.defeats == frozenset({("c1", "c2"), ("c2", "c1")})


def test_compute_claim_graph_justified_preferred_and_stable() -> None:
    store = _store(
        CompiledWorldGraph(
            claims=(_claim("c1", 100.0), _claim("c2", 200.0)),
            relations=(_edge("c1", "c2", "rebuts"), _edge("c2", "c1", "rebuts")),
        )
    )
    for semantics in ("preferred", "stable"):
        accepted = compute_claim_graph_justified_claims(store, {"c1", "c2"}, semantics=semantics)
        assert frozenset({"c1"}) in accepted
        assert frozenset({"c2"}) in accepted


def test_shared_projection_independent_of_active_id_order() -> None:
    compiled = CompiledWorldGraph(
        claims=(_claim("c1", 100.0), _claim("c2", 200.0)),
        relations=(_edge("c1", "c2", "rebuts"), _edge("c2", "c1", "rebuts")),
    )
    forward = ActiveWorldGraph(compiled=compiled, active_claim_ids=("c1", "c2"))
    reverse = ActiveWorldGraph(compiled=compiled, active_claim_ids=("c2", "c1"))

    forward_result = analyze_claim_graph(
        shared_analyzer_input_from_graph(forward),
        semantics="preferred",
        target_claim_ids=("c1", "c2"),
    )
    reverse_result = analyze_claim_graph(
        shared_analyzer_input_from_graph(reverse),
        semantics="preferred",
        target_claim_ids=("c1", "c2"),
    )
    assert forward_result.projection == reverse_result.projection


# --- conflict synthesis -----------------------------------------------------


def test_conflict_synthesizes_rebuts_and_fabricates_no_opinions() -> None:
    store = _store(
        CompiledWorldGraph(
            claims=(_claim("cA", 100.0), _claim("cB", 200.0), _claim("cC", 300.0)),
            relations=(_edge("cA", "cB", "supports"),),
            conflicts=(ConflictWitness(left_claim_id="cA", right_claim_id="cC", kind="CONFLICT"),),
        )
    )
    shared = shared_analyzer_input_from_store(store, {"cA", "cB", "cC"})

    synthetic = {
        (row["claim_id"], row["target_claim_id"])
        for row in shared.stance_rows
        if row["stance_type"] == "rebuts"
    }
    assert ("cA", "cC") in synthetic
    assert ("cC", "cA") in synthetic
    for row in shared.stance_rows:
        if (row["claim_id"], row["target_claim_id"]) in {("cA", "cC"), ("cC", "cA")}:
            assert "confidence" not in row
            assert "opinion_belief" not in row


# --- PrAF -------------------------------------------------------------------


def test_build_praf_deterministic() -> None:
    store = _store(
        CompiledWorldGraph(
            claims=(_claim("c1", 100.0, sample_size=50), _claim("c2", 200.0, sample_size=10)),
            relations=(_edge("c1", "c2", "rebuts", **_OPINION_STRONG),),
        )
    )
    praf = build_praf(store, {"c1", "c2"})

    assert isinstance(praf, PropstorePrAF)
    assert praf.framework.arguments == frozenset({"c1", "c2"})
    assert set(praf.p_args) == {"c1", "c2"}
    for opinion in praf.p_args.values():
        assert 0.0 <= opinion.expectation() <= 1.0
    assert ("c1", "c2") in praf.framework.defeats
    assert len(praf.attack_relations) == 1
    assert praf.attack_relations[0].edge == ("c1", "c2")
    assert praf.attack_relations[0].provenance is not None
    assert praf.attack_relations[0].provenance.stance_type is StanceType.REBUTS
    assert praf.direct_defeat_relations[0].edge == ("c1", "c2")


def test_build_praf_no_stances() -> None:
    store = _store(CompiledWorldGraph(claims=(_claim("c1", 100.0), _claim("c2", 200.0))))
    praf = build_praf(store, {"c1", "c2"})
    assert praf.framework.arguments == frozenset({"c1", "c2"})
    assert len(praf.framework.defeats) == 0
    assert set(praf.p_args) == {"c1", "c2"}


def test_build_praf_uncertain_defeat_probabilities() -> None:
    store = _store(
        CompiledWorldGraph(
            claims=(_claim("c1", 100.0, sample_size=50), _claim("c2", 200.0, sample_size=50)),
            relations=(
                _edge("c1", "c2", "rebuts", **_OPINION_WEAK),
                _edge("c2", "c1", "rebuts", **_OPINION_STRONG),
            ),
        )
    )
    praf = build_praf(store, {"c1", "c2"})
    assert ("c1", "c2") in praf.framework.defeats
    assert ("c2", "c1") in praf.framework.defeats
    assert 0.0 < praf.p_defeats[("c1", "c2")].expectation() < 1.0
    assert praf.p_defeats[("c2", "c1")].expectation() > 0.8


def test_analyze_praf_metadata_exposes_query_contract() -> None:
    store = _store(
        CompiledWorldGraph(
            claims=(_claim("c1", 100.0, sample_size=50), _claim("c2", 200.0, sample_size=50)),
            relations=(
                _edge("c1", "c2", "rebuts", **_OPINION_WEAK),
                _edge("c2", "c1", "rebuts", **_OPINION_STRONG),
            ),
        )
    )
    shared = shared_analyzer_input_from_store(store, {"c1", "c2"})
    result = analyze_praf(
        shared,
        semantics="preferred",
        strategy="exact_enum",
        query_kind="argument_acceptance",
        inference_mode="skeptical",
        target_claim_ids=("c1", "c2"),
    )
    metadata = dict(result.metadata)
    assert metadata["query_kind"] == "argument_acceptance"
    assert metadata["inference_mode"] == "skeptical"
    assert metadata["strategy_used"] == "exact_enum"


def test_analyze_praf_paper_td_routes_to_extension_probability() -> None:
    prior = {"b": 0.0, "d": 0.0, "u": 1.0, "a": 0.5}
    active_graph = ActiveWorldGraph(
        compiled=CompiledWorldGraph(
            claims=(ClaimNode(claim_id="claim_a", claim_type="observation"),)
        ),
        active_claim_ids=("claim_a",),
    )
    shared = SharedAnalyzerInput(
        comparison="elitist",
        claims_by_id={"claim_a": {"id": "claim_a", "source_prior_base_rate": prior}},
        stance_rows=(),
        relations=ClaimGraphRelations(
            arguments=frozenset({"claim_a"}),
            attacks=frozenset(),
            direct_defeats=frozenset(),
            supports=frozenset(),
        ),
        argumentation_framework=ArgumentationFramework(
            arguments=frozenset({"claim_a"}), defeats=frozenset(), attacks=frozenset()
        ),
        bipolar_framework=BipolarArgumentationFramework(
            arguments=frozenset({"claim_a"}), defeats=frozenset(), supports=frozenset()
        ),
        active_graph=active_graph,
    )
    result = analyze_praf(
        shared,
        semantics="praf-paper-td-complete",
        strategy="exact_enum",
        query_kind="argument_acceptance",
        inference_mode="credulous",
        target_claim_ids=("claim_a",),
    )
    metadata = dict(result.metadata)
    assert result.semantics == "praf-paper-td-complete"
    assert metadata["strategy_used"] == "paper_td"
    assert metadata["query_kind"] == "extension_probability"
    assert metadata["extension_probability"] == pytest.approx(0.5)
    assert result.projection is not None
    assert result.projection.survivor_claim_ids == ("claim_a",)


# --- ASPIC+ projection via the store path -----------------------------------


def test_build_aspic_projection_from_active_graph() -> None:
    compiled = CompiledWorldGraph(
        claims=(_claim("premise", 1.0), _claim("goal", 2.0)),
        relations=(_edge("premise", "goal", "supports"),),
    )
    active_graph = ActiveWorldGraph(compiled=compiled, active_claim_ids=("premise", "goal"))
    active_claims = [{"id": "premise"}, {"id": "goal"}]

    projection = build_aspic_projection(
        CompiledGraphStore(compiled=compiled),
        active_claims,
        bundle=GroundedRulesBundle.empty(),
        active_graph=active_graph,
    )

    assert set(projection.claim_to_argument_ids) >= {"premise", "goal"}
    assert projection.framework.arguments
