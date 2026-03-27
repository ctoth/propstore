"""Primitive probabilistic relation records for argumentation.

These records preserve uncertainty and provenance on primitive relations
without forcing derived semantic relations to become canonical inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from propstore.opinion import Opinion

RelationKind = Literal["attack", "support", "direct_defeat", "derived_defeat"]

_PROVENANCE_KEYS = (
    "id",
    "claim_id",
    "target_claim_id",
    "stance_type",
    "resolution_model",
    "confidence",
    "opinion_belief",
    "opinion_disbelief",
    "opinion_uncertainty",
    "opinion_base_rate",
)


@dataclass(frozen=True)
class RelationProvenance:
    """Stable provenance for a probabilistic relation."""

    source_table: str | None = None
    stance_type: str | None = None
    row_identity: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class ProbabilisticRelation:
    """A primitive or derived probabilistic relation between two arguments."""

    kind: RelationKind
    source: str
    target: str
    opinion: Opinion
    provenance: RelationProvenance | None = None
    derived_from: tuple[tuple[str, str], ...] = ()

    @property
    def edge(self) -> tuple[str, str]:
        return (self.source, self.target)


@dataclass(frozen=True)
class ClaimGraphRelations:
    """Primitive and direct semantic relations collected from active claims."""

    arguments: frozenset[str]
    attacks: frozenset[tuple[str, str]]
    direct_defeats: frozenset[tuple[str, str]]
    supports: frozenset[tuple[str, str]]
    attack_relations: tuple[ProbabilisticRelation, ...] = ()
    support_relations: tuple[ProbabilisticRelation, ...] = ()
    direct_defeat_relations: tuple[ProbabilisticRelation, ...] = ()


def provenance_from_row(row: dict, *, source_table: str = "relation_edge") -> RelationProvenance:
    """Build stable provenance from a stance-like mapping."""
    row_identity = tuple(
        (key, repr(row[key]))
        for key in _PROVENANCE_KEYS
        if key in row and row[key] is not None
    )
    return RelationProvenance(
        source_table=source_table,
        stance_type=row.get("stance_type"),
        row_identity=row_identity,
    )


def relation_from_row(
    *,
    kind: RelationKind,
    source: str,
    target: str,
    opinion: Opinion,
    row: dict | None = None,
    derived_from: tuple[tuple[str, str], ...] = (),
) -> ProbabilisticRelation:
    """Create a probabilistic relation record from a stance row."""
    provenance = provenance_from_row(row) if row is not None else None
    return ProbabilisticRelation(
        kind=kind,
        source=source,
        target=target,
        opinion=opinion,
        provenance=provenance,
        derived_from=derived_from,
    )


def relation_map(
    relations: tuple[ProbabilisticRelation, ...] | list[ProbabilisticRelation],
) -> dict[tuple[str, str], Opinion]:
    """Convert relation records to an edge -> opinion mapping."""
    return {relation.edge: relation.opinion for relation in relations}
