"""Typed explanation shapes for a support revision.

These are the *reasons* a revision accepted, rejected, or incised an atom. They
are constructed by the revision engine from typed values and consumed as typed
values: the worldline charter stores a ``RevisionExplanation`` directly and
Quire's codec owns the encode/decode, so there is no ``from_mapping``/``to_dict``
pair here and no second spelling to keep in sync.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import msgspec

from propstore.core.id_types import AssumptionId, to_assumption_ids


class RevisionAtomDetail(
    msgspec.Struct, frozen=True, forbid_unknown_fields=True, omit_defaults=True
):
    reason: str | None = None
    incision_set: tuple[str, ...] = ()
    support_sets: tuple[tuple[AssumptionId, ...], ...] = ()
    selection_rule: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "incision_set", tuple(str(atom_id) for atom_id in self.incision_set))
        object.__setattr__(
            self,
            "support_sets",
            tuple(to_assumption_ids(support_set) for support_set in self.support_sets),
        )


class EntrenchmentReason(
    msgspec.Struct, frozen=True, forbid_unknown_fields=True, omit_defaults=True
):
    override_priority: int | str | None = None
    override_key: str | None = None
    support_count: int | None = None
    essential_support: tuple[AssumptionId, ...] = ()
    iterated_operator: str | None = None
    revised_in: bool | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "essential_support", to_assumption_ids(self.essential_support))


def coerce_override_priority(value: Any) -> int | str | None:
    """Narrow an authored override priority to the one canonical spelling.

    Authored priorities arrive as ints, bools, floats, or strings; the ranking
    only distinguishes integer order from named keys, so a whole float collapses
    to its int and everything else to its string.
    """

    if value is None:
        return None
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return str(value)


@dataclass(frozen=True)
class RevisionAtomExplanation:
    status: str
    reason: str
    ranking: EntrenchmentReason | None = None
    incision_set: tuple[str, ...] = ()
    support_sets: tuple[tuple[AssumptionId, ...], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "incision_set", tuple(str(atom_id) for atom_id in self.incision_set))
        object.__setattr__(
            self,
            "support_sets",
            tuple(to_assumption_ids(support_set) for support_set in self.support_sets),
        )


@dataclass(frozen=True)
class RevisionExplanation:
    accepted_atom_ids: tuple[str, ...]
    rejected_atom_ids: tuple[str, ...]
    incision_set: tuple[str, ...] = ()
    atoms: Mapping[str, RevisionAtomExplanation] = field(
        default_factory=dict[str, RevisionAtomExplanation]
    )

    def __post_init__(self) -> None:
        object.__setattr__(self, "accepted_atom_ids", tuple(str(atom_id) for atom_id in self.accepted_atom_ids))
        object.__setattr__(self, "rejected_atom_ids", tuple(str(atom_id) for atom_id in self.rejected_atom_ids))
        object.__setattr__(self, "incision_set", tuple(str(atom_id) for atom_id in self.incision_set))
        object.__setattr__(self, "atoms", dict(self.atoms))
