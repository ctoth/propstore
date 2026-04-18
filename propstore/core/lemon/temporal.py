from __future__ import annotations

from enum import StrEnum

from quire.documents import DocumentStruct
from propstore.cel_checker import ConceptInfo, KindType
from propstore.cel_types import CelExpr
from propstore.provenance import Provenance
from propstore.z3_conditions import Z3ConditionSolver


class AllenRelation(StrEnum):
    BEFORE = "before"
    MEETS = "meets"
    OVERLAPS = "overlaps"
    DURING = "during"
    STARTS = "starts"
    FINISHES = "finishes"
    EQUALS = "equals"
    AFTER = "after"
    MET_BY = "met_by"
    OVERLAPPED_BY = "overlapped_by"
    CONTAINS = "contains"
    STARTED_BY = "started_by"
    FINISHED_BY = "finished_by"


class DescriptionTemporalAnchor(DocumentStruct):
    claim_id: str
    valid_from: float
    valid_until: float
    provenance: Provenance

    def __post_init__(self) -> None:
        if self.valid_from > self.valid_until:
            raise ValueError("description temporal anchor requires valid_from <= valid_until")


_RELATION_EXPRESSIONS: dict[AllenRelation, CelExpr] = {
    AllenRelation.BEFORE: CelExpr("left_until < right_from"),
    AllenRelation.MEETS: CelExpr("left_until == right_from"),
    AllenRelation.OVERLAPS: (
        CelExpr(
            "left_from < right_from && right_from < left_until && left_until < right_until"
        )
    ),
    AllenRelation.DURING: CelExpr(
        "right_from < left_from && left_until < right_until"
    ),
    AllenRelation.STARTS: CelExpr(
        "left_from == right_from && left_until < right_until"
    ),
    AllenRelation.FINISHES: CelExpr(
        "right_from < left_from && left_until == right_until"
    ),
    AllenRelation.EQUALS: CelExpr(
        "left_from == right_from && left_until == right_until"
    ),
    AllenRelation.AFTER: CelExpr("right_until < left_from"),
    AllenRelation.MET_BY: CelExpr("right_until == left_from"),
    AllenRelation.OVERLAPPED_BY: (
        CelExpr(
            "right_from < left_from && left_from < right_until && right_until < left_until"
        )
    ),
    AllenRelation.CONTAINS: CelExpr(
        "left_from < right_from && right_until < left_until"
    ),
    AllenRelation.STARTED_BY: CelExpr(
        "left_from == right_from && right_until < left_until"
    ),
    AllenRelation.FINISHED_BY: CelExpr(
        "left_from < right_from && left_until == right_until"
    ),
}


def _description_temporal_registry() -> dict[str, ConceptInfo]:
    return {
        name: ConceptInfo(
            id=f"ps:concept:{name}",
            canonical_name=name,
            kind=KindType.TIMEPOINT,
        )
        for name in ("left_from", "left_until", "right_from", "right_until")
    }


def description_temporal_relation(
    left: DescriptionTemporalAnchor,
    right: DescriptionTemporalAnchor,
    relation: AllenRelation,
) -> bool:
    """Evaluate an Allen relation between description-claim temporal anchors."""

    solver = Z3ConditionSolver(_description_temporal_registry())
    bindings = {
        "left_from": left.valid_from,
        "left_until": left.valid_until,
        "right_from": right.valid_from,
        "right_until": right.valid_until,
    }
    return solver.is_condition_satisfied(_RELATION_EXPRESSIONS[relation], bindings)
