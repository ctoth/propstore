"""Probabilistic relations carry doxa.Opinion with stance provenance."""

from __future__ import annotations

from doxa import Opinion

from propstore.probabilistic_relations import (
    ProbabilisticRelation,
    RelationProvenance,
    relation_from_stance,
    relation_map,
)
from propstore.stances import StanceType
from propstore.families.relations import Stance


def _stance(source: str = "c1", target: str = "c2") -> Stance:
    return Stance(
        stance_id=f"{source}:{target}",
        source_claim_id=source,
        target_claim_id=target,
        stance_type=StanceType.REBUTS,
        resolution_model="model-x",
        opinion_belief=0.7,
        opinion_disbelief=0.1,
        opinion_uncertainty=0.2,
        opinion_base_rate=0.5,
    )


def test_relation_from_stance_carries_doxa_opinion_and_provenance() -> None:
    opinion = Opinion(0.7, 0.1, 0.2, 0.5)
    relation = relation_from_stance(
        kind="attack",
        opinion=opinion,
        stance=_stance(),
    )

    assert isinstance(relation, ProbabilisticRelation)
    assert relation.opinion is opinion
    assert isinstance(relation.opinion, Opinion)
    assert relation.edge == ("c1", "c2")
    assert relation.provenance is not None
    assert relation.provenance.stance_type is StanceType.REBUTS
    assert relation.provenance.source_table == "stance"


def test_relation_provenance_coerces_stance_type() -> None:
    prov = RelationProvenance(source_table="relation_edge", stance_type="supports")
    assert prov.stance_type is StanceType.SUPPORTS


def test_derived_relation_can_have_no_provenance() -> None:
    relation = ProbabilisticRelation(
        kind="support",
        source="a",
        target="b",
        opinion=Opinion.vacuous(0.5),
    )
    assert relation.provenance is None


def test_relation_map_keys_edges_to_opinions() -> None:
    r1 = relation_from_stance(
        kind="attack", stance=_stance("a", "b"), opinion=Opinion(0.6, 0.2, 0.2, 0.5)
    )
    r2 = relation_from_stance(
        kind="support", stance=_stance("b", "c"), opinion=Opinion.vacuous(0.5)
    )
    mapping = relation_map((r1, r2))

    assert mapping[("a", "b")] == Opinion(0.6, 0.2, 0.2, 0.5)
    assert mapping[("b", "c")] == Opinion.vacuous(0.5)
