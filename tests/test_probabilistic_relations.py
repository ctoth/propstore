"""Probabilistic relations carry doxa.Opinion directly with row provenance."""

from __future__ import annotations

from doxa import Opinion

from propstore.probabilistic_relations import (
    ProbabilisticRelation,
    RelationProvenance,
    relation_from_row,
    relation_map,
)
from propstore.stances import StanceType


def _row() -> dict[str, object]:
    return {
        "id": "edge1",
        "claim_id": "c1",
        "target_claim_id": "c2",
        "stance_type": "rebuts",
        "resolution_model": "model-x",
        "opinion_belief": 0.7,
        "opinion_disbelief": 0.1,
        "opinion_uncertainty": 0.2,
        "opinion_base_rate": 0.5,
    }


def test_relation_from_row_carries_doxa_opinion_and_provenance() -> None:
    opinion = Opinion(0.7, 0.1, 0.2, 0.5)
    relation = relation_from_row(
        kind="attack",
        source="c1",
        target="c2",
        opinion=opinion,
        row=_row(),
    )

    assert isinstance(relation, ProbabilisticRelation)
    assert relation.opinion is opinion
    assert isinstance(relation.opinion, Opinion)
    assert relation.edge == ("c1", "c2")
    assert relation.provenance is not None
    assert relation.provenance.stance_type is StanceType.REBUTS
    assert relation.provenance.source_table == "relation_edge"


def test_relation_provenance_coerces_stance_type() -> None:
    prov = RelationProvenance(source_table="relation_edge", stance_type="supports")
    assert prov.stance_type is StanceType.SUPPORTS


def test_relation_without_row_has_no_provenance() -> None:
    relation = relation_from_row(
        kind="support",
        source="a",
        target="b",
        opinion=Opinion.vacuous(0.5),
    )
    assert relation.provenance is None


def test_relation_map_keys_edges_to_opinions() -> None:
    r1 = relation_from_row(
        kind="attack", source="a", target="b", opinion=Opinion(0.6, 0.2, 0.2, 0.5)
    )
    r2 = relation_from_row(
        kind="support", source="b", target="c", opinion=Opinion.vacuous(0.5)
    )
    mapping = relation_map((r1, r2))

    assert mapping[("a", "b")] == Opinion(0.6, 0.2, 0.2, 0.5)
    assert mapping[("b", "c")] == Opinion.vacuous(0.5)
