from __future__ import annotations

from propstore.world import Environment
from propstore.world.labelled import Label


def test_compiled_world_graph_normalizes_order_and_supporting_records() -> None:
    from propstore.core.graph_types import (
        ClaimNode,
        CompiledWorldGraph,
        ConflictWitness,
        ParameterizationEdge,
        ProvenanceRecord,
        RelationEdge,
    )

    provenance = ProvenanceRecord.from_mapping(
        {
            "paper": "alpha_2025",
            "page": 7,
            "note": "table 2",
        }
    )

    graph_a = CompiledWorldGraph(
        claims=(
            ClaimNode(
                claim_id="claim_b",
                concept_id="concept2",
                claim_type="parameter",
                scalar_value=2.0,
                provenance=provenance,
                attributes={"unit": "m/s^2"},
            ),
            ClaimNode(
                claim_id="claim_a",
                concept_id="concept1",
                claim_type="parameter",
                scalar_value=1.0,
                attributes={"unit": "m"},
            ),
        ),
        relations=(
            RelationEdge(
                source_id="claim_b",
                target_id="claim_a",
                relation_type="rebuts",
                attributes={"confidence": 0.8},
            ),
        ),
        parameterizations=(
            ParameterizationEdge(
                output_concept_id="concept3",
                input_concept_ids=("concept1", "concept2"),
                formula="z = x + y",
                sympy="Eq(concept3, concept1 + concept2)",
                exactness="exact",
            ),
        ),
        conflicts=(
            ConflictWitness(
                left_claim_id="claim_b",
                right_claim_id="claim_a",
                kind="rebuts",
            ),
        ),
    )
    graph_b = CompiledWorldGraph(
        conflicts=(
            ConflictWitness(
                left_claim_id="claim_a",
                right_claim_id="claim_b",
                kind="rebuts",
            ),
        ),
        parameterizations=(
            ParameterizationEdge(
                output_concept_id="concept3",
                input_concept_ids=("concept1", "concept2"),
                formula="z = x + y",
                sympy="Eq(concept3, concept1 + concept2)",
                exactness="exact",
            ),
        ),
        relations=(
            RelationEdge(
                source_id="claim_b",
                target_id="claim_a",
                relation_type="rebuts",
                attributes={"confidence": 0.8},
            ),
        ),
        claims=(
            ClaimNode(
                claim_id="claim_a",
                concept_id="concept1",
                claim_type="parameter",
                scalar_value=1.0,
                attributes={"unit": "m"},
            ),
            ClaimNode(
                claim_id="claim_b",
                concept_id="concept2",
                claim_type="parameter",
                scalar_value=2.0,
                provenance=ProvenanceRecord.from_mapping(
                    {
                        "note": "table 2",
                        "page": 7,
                        "paper": "alpha_2025",
                    }
                ),
                attributes={"unit": "m/s^2"},
            ),
        ),
    )

    assert graph_a == graph_b
    assert tuple(node.claim_id for node in graph_a.claims) == ("claim_a", "claim_b")
    assert tuple(sorted(graph_a.claims)) == graph_a.claims


def test_provenance_record_normalizes_known_fields_and_extras() -> None:
    from propstore.core.graph_types import ProvenanceRecord

    record = ProvenanceRecord.from_mapping(
        {
            "page": "7",
            "paper": "alpha_2025",
            "source_table": "claim",
            "source_id": "claim_a",
            "section": "results",
            "table": "table 2",
        }
    )

    assert record.page == 7
    assert record.paper == "alpha_2025"
    assert record.source_table == "claim"
    assert record.source_id == "claim_a"
    assert record.extras == (("section", "results"), ("table", "table 2"))


def test_graph_delta_identity_preserves_graph_exactly() -> None:
    from propstore.core.graph_types import ClaimNode, CompiledWorldGraph, GraphDelta

    graph = CompiledWorldGraph(
        claims=(
            ClaimNode(
                claim_id="claim_a",
                concept_id="concept1",
                claim_type="parameter",
                scalar_value=1.0,
            ),
        ),
    )
    delta = GraphDelta()

    assert delta.is_identity
    assert delta.apply(graph) == graph


def test_graph_delta_add_remove_inverse_returns_to_same_graph() -> None:
    from propstore.core.graph_types import ClaimNode, CompiledWorldGraph, GraphDelta

    base = CompiledWorldGraph()
    claim = ClaimNode(
        claim_id="claim_a",
        concept_id="concept1",
        claim_type="parameter",
        scalar_value=1.0,
    )
    add_then_remove = GraphDelta(add_claims=(claim,)).then(GraphDelta(remove_claim_ids=("claim_a",)))

    assert add_then_remove.apply(base) == base


def test_active_world_graph_roundtrip_is_stable() -> None:
    from propstore.core.graph_types import ActiveWorldGraph, ClaimNode, CompiledWorldGraph

    compiled = CompiledWorldGraph(
        claims=(
            ClaimNode(
                claim_id="claim_a",
                concept_id="concept1",
                claim_type="parameter",
                scalar_value=1.0,
            ),
        ),
    )
    active = ActiveWorldGraph(
        compiled=compiled,
        environment=Environment(bindings={"task": "speech"}, context_id="ctx_demo"),
        active_claim_ids=("claim_a",),
        inactive_claim_ids=(),
    )

    restored = ActiveWorldGraph.from_dict(active.to_dict())

    assert restored == active


def test_analyzer_result_roundtrip_is_stable() -> None:
    from propstore.core.results import AnalyzerResult, ClaimProjection, ExtensionResult

    result = AnalyzerResult(
        backend="claim_graph",
        semantics="grounded",
        extensions=(
            ExtensionResult(
                name="grounded",
                accepted_claim_ids=("claim_a",),
                rejected_claim_ids=("claim_b",),
                undecided_claim_ids=(),
            ),
        ),
        projection=ClaimProjection(
            target_claim_ids=("claim_a", "claim_b"),
            survivor_claim_ids=("claim_a",),
            witness_claim_ids=("claim_a", "claim_b"),
        ),
        support_label=Label.empty(),
        metadata={"comparison": "elitist"},
    )

    restored = AnalyzerResult.from_dict(result.to_dict())

    assert restored == result
