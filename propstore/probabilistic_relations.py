"""Primitive probabilistic relation records for argumentation.

These records preserve uncertainty and provenance on primitive relations between
arguments without forcing derived semantic relations to become canonical inputs.
Each relation carries a ``doxa.Opinion`` directly — the one canonical opinion
spelling (CLAUDE.md substrate-boundary rule) — alongside a stable
:class:`RelationProvenance` recording the stance row it came from.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from doxa import Opinion

from propstore.families.relations import Stance
from propstore.stances import StanceType, coerce_stance_type

RelationKind = Literal["attack", "support", "direct_defeat", "derived_defeat"]


@dataclass(frozen=True)
class RelationProvenance:
    """Stable provenance for a probabilistic relation."""

    source_table: str | None = None
    stance_type: StanceType | None = None
    row_identity: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "stance_type", coerce_stance_type(self.stance_type))


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


def relation_from_stance(
    *,
    kind: RelationKind,
    opinion: Opinion,
    stance: Stance,
    derived_from: tuple[tuple[str, str], ...] = (),
) -> ProbabilisticRelation:
    """Create a probabilistic relation record from its authored stance."""

    if stance.source_claim_id is None or stance.target_claim_id is None:
        raise ValueError("probabilistic relation stance requires claim endpoints")
    return ProbabilisticRelation(
        kind=kind,
        source=stance.source_claim_id,
        target=stance.target_claim_id,
        opinion=opinion,
        provenance=RelationProvenance(
            source_table="stance",
            stance_type=stance.stance_type,
            row_identity=(("stance_id", stance.stance_id),),
        ),
        derived_from=derived_from,
    )


def relation_map(
    relations: tuple[ProbabilisticRelation, ...] | list[ProbabilisticRelation],
) -> dict[tuple[str, str], Opinion]:
    """Convert relation records to an edge -> opinion mapping."""

    return {relation.edge: relation.opinion for relation in relations}
