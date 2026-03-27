from __future__ import annotations

import sqlite3

import pytest

from propstore.argumentation import build_praf, compute_claim_graph_justified_claims
from propstore.core.graph_types import ActiveWorldGraph, ClaimNode, CompiledWorldGraph, RelationEdge
from propstore.praf import compute_praf_acceptance
from tests.conftest import create_argumentation_schema, insert_claim, insert_stance
from tests.sqlite_argumentation_store import SQLiteArgumentationStore


def _insert_claim(
    conn: sqlite3.Connection,
    claim_id: str,
    concept_id: str,
    value: float,
    *,
    sample_size: int,
) -> None:
    insert_claim(
        conn,
        claim_id,
        claim_type="parameter",
        concept_id=concept_id,
        value=value,
        sample_size=sample_size,
    )


def _insert_stance(
    conn: sqlite3.Connection,
    claim_id: str,
    target_claim_id: str,
    stance_type: str,
    *,
    confidence: float = 0.9,
    opinion_belief: float | None = None,
    opinion_disbelief: float | None = None,
    opinion_uncertainty: float | None = None,
    opinion_base_rate: float | None = None,
) -> None:
    insert_stance(
        conn,
        claim_id,
        target_claim_id,
        stance_type,
        confidence=confidence,
        opinion_belief=opinion_belief,
        opinion_disbelief=opinion_disbelief,
        opinion_uncertainty=opinion_uncertainty,
        opinion_base_rate=opinion_base_rate,
    )


@pytest.fixture
def conn() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_argumentation_schema(connection)
    return connection


def _accepted_extensions(result) -> set[frozenset[str]]:
    return {
        frozenset(extension.accepted_claim_ids)
        for extension in result.extensions
    }


def test_shared_claim_graph_analyzer_matches_current_grounded(conn: sqlite3.Connection) -> None:
    _insert_claim(conn, "c1", "temp", 100.0, sample_size=50)
    _insert_claim(conn, "c2", "temp", 200.0, sample_size=50)
    _insert_stance(conn, "c1", "c2", "rebuts")
    _insert_stance(conn, "c2", "c1", "rebuts")
    conn.commit()

    from propstore.core.analyzers import analyze_claim_graph, shared_analyzer_input_from_store

    store = SQLiteArgumentationStore(conn)
    shared = shared_analyzer_input_from_store(store, {"c1", "c2"})

    result = analyze_claim_graph(
        shared,
        semantics="grounded",
        target_claim_ids=("c1", "c2"),
    )
    expected = compute_claim_graph_justified_claims(
        store,
        {"c1", "c2"},
        semantics="grounded",
    )

    assert _accepted_extensions(result) == {frozenset(expected)}
    assert result.projection is not None
    assert result.projection.survivor_claim_ids == ()


def test_shared_claim_graph_analyzer_matches_current_preferred_and_stable(
    conn: sqlite3.Connection,
) -> None:
    _insert_claim(conn, "c1", "temp", 100.0, sample_size=50)
    _insert_claim(conn, "c2", "temp", 200.0, sample_size=50)
    _insert_stance(conn, "c1", "c2", "rebuts")
    _insert_stance(conn, "c2", "c1", "rebuts")
    conn.commit()

    from propstore.core.analyzers import analyze_claim_graph, shared_analyzer_input_from_store

    store = SQLiteArgumentationStore(conn)
    shared = shared_analyzer_input_from_store(store, {"c1", "c2"})

    for semantics in ("preferred", "stable"):
        result = analyze_claim_graph(
            shared,
            semantics=semantics,
            target_claim_ids=("c1", "c2"),
        )
        expected = compute_claim_graph_justified_claims(
            store,
            {"c1", "c2"},
            semantics=semantics,
        )

        assert _accepted_extensions(result) == set(expected)
        assert result.projection is not None
        assert result.projection.survivor_claim_ids == ()
        assert set(result.projection.witness_claim_ids) == {"c1", "c2"}


def test_shared_praf_analyzer_matches_current_acceptance(conn: sqlite3.Connection) -> None:
    _insert_claim(conn, "c1", "temp", 100.0, sample_size=50)
    _insert_claim(conn, "c2", "temp", 200.0, sample_size=50)
    _insert_stance(
        conn,
        "c1",
        "c2",
        "rebuts",
        confidence=0.3,
        opinion_belief=0.2,
        opinion_disbelief=0.1,
        opinion_uncertainty=0.7,
        opinion_base_rate=0.15,
    )
    _insert_stance(
        conn,
        "c2",
        "c1",
        "rebuts",
        confidence=0.95,
        opinion_belief=0.9,
        opinion_disbelief=0.03,
        opinion_uncertainty=0.07,
        opinion_base_rate=0.5,
    )
    conn.commit()

    from propstore.core.analyzers import analyze_praf, shared_analyzer_input_from_store

    store = SQLiteArgumentationStore(conn)
    shared = shared_analyzer_input_from_store(store, {"c1", "c2"})

    result = analyze_praf(
        shared,
        semantics="grounded",
        strategy="exact_enum",
        target_claim_ids=("c1", "c2"),
    )
    expected_result = compute_praf_acceptance(
        build_praf(store, {"c1", "c2"}),
        semantics="grounded",
        strategy="exact_enum",
    )

    metadata = dict(result.metadata)
    assert metadata["strategy_used"] == expected_result.strategy_used
    assert metadata["acceptance_probs"] == pytest.approx(expected_result.acceptance_probs)
    assert result.projection is not None
    assert result.projection.survivor_claim_ids == ("c2",)


def test_shared_projection_is_independent_of_active_claim_id_order() -> None:
    compiled = CompiledWorldGraph(
        claims=(
            ClaimNode(
                claim_id="c1",
                concept_id="temp",
                claim_type="parameter",
                scalar_value=100.0,
                attributes={"sample_size": 50},
            ),
            ClaimNode(
                claim_id="c2",
                concept_id="temp",
                claim_type="parameter",
                scalar_value=200.0,
                attributes={"sample_size": 50},
            ),
        ),
        relations=(
            RelationEdge(source_id="c1", target_id="c2", relation_type="rebuts"),
            RelationEdge(source_id="c2", target_id="c1", relation_type="rebuts"),
        ),
    )
    forward = ActiveWorldGraph(
        compiled=compiled,
        active_claim_ids=("c1", "c2"),
    )
    reverse = ActiveWorldGraph(
        compiled=compiled,
        active_claim_ids=("c2", "c1"),
    )

    from propstore.core.analyzers import (
        analyze_claim_graph,
        shared_analyzer_input_from_active_graph,
    )

    forward_result = analyze_claim_graph(
        shared_analyzer_input_from_active_graph(forward),
        semantics="preferred",
        target_claim_ids=("c1", "c2"),
    )
    reverse_result = analyze_claim_graph(
        shared_analyzer_input_from_active_graph(reverse),
        semantics="preferred",
        target_claim_ids=("c1", "c2"),
    )

    assert forward_result.projection == reverse_result.projection
