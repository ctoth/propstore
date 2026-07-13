"""The typed input one journal operator replays from.

A transition journal entry records *what was done* so it can be re-dispatched
deterministically. The input to each operator is a tagged union — the operators
take genuinely different arguments — and it was stored as a bare
``dict[str, Any]`` whose shape ``dispatch()`` reconstructed by hand: branch on the
operator, then ``payload.get(...)`` each field, raising ``ValueError`` deep inside
a replay when something was missing. Tagging the union moves that failure to
decode time, where a corrupt journal belongs.

Every variant is tagged on ``operator``, the same discriminator the entry's own
``operator`` field carries, so an entry whose recorded operator disagrees with the
shape of its input cannot be decoded at all.

``formula`` rides as :data:`~propstore.support_revision.state.BeliefAtom`, which
is *already* a tagged union (``AssertionAtom``/``AssumptionAtom`` carry msgspec
tags): the journal never needed a hand-written atom parse, and the producer never
needed to lower a typed atom into builtins for the replay to re-parse.
"""

from __future__ import annotations

import msgspec

from propstore.support_revision.integrity_constraints import IntegrityConstraintSpec
from propstore.support_revision.state import BeliefAtom


class ExpandInput(
    msgspec.Struct, frozen=True, forbid_unknown_fields=True, tag_field="operator", tag="expand"
):
    formula: BeliefAtom
    max_candidates: int


class ContractInput(
    msgspec.Struct, frozen=True, forbid_unknown_fields=True, tag_field="operator", tag="contract"
):
    targets: tuple[str, ...]
    max_candidates: int


class ReviseInput(
    msgspec.Struct, frozen=True, forbid_unknown_fields=True, tag_field="operator", tag="revise"
):
    formula: BeliefAtom
    max_candidates: int
    conflicts: dict[str, tuple[str, ...]] = msgspec.field(
        default_factory=dict[str, tuple[str, ...]]
    )

    def targets_for(self, atom_id: str) -> tuple[str, ...]:
        return self.conflicts.get(atom_id, ())


class IteratedReviseInput(
    msgspec.Struct,
    frozen=True,
    forbid_unknown_fields=True,
    tag_field="operator",
    tag="iterated_revise",
):
    formula: BeliefAtom
    revision_operator: str
    max_candidates: int
    targets: tuple[str, ...] = ()


class ICMergeInput(
    msgspec.Struct, frozen=True, forbid_unknown_fields=True, tag_field="operator", tag="ic_merge"
):
    profile_atom_ids: tuple[tuple[str, ...], ...]
    integrity_constraint: IntegrityConstraintSpec
    max_alphabet_size: int
    merge_operator: str = "sigma"
    merge_parent_commits: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.profile_atom_ids:
            raise ValueError("IC merge requires at least one profile")


OperatorInput = (
    ExpandInput | ContractInput | ReviseInput | IteratedReviseInput | ICMergeInput
)
"""What one journal operator replays from, discriminated on its ``operator`` tag."""


__all__ = [
    "ContractInput",
    "ExpandInput",
    "ICMergeInput",
    "IteratedReviseInput",
    "OperatorInput",
    "ReviseInput",
]
