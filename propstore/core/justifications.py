"""Canonical justification records for structured argument construction.

A :class:`CanonicalJustification` is the propstore-side value describing one
inference licence: a conclusion claim, its premise claims, and the kind/strength
of the rule that links them. The ASPIC+ bridge turns these into ``Rule`` objects
(``reported_claim`` justifications contribute a premise, not a rule). This is the
ONE spelling of a justification record; there is no parallel document mirror.

Non-commitment (CLAUDE.md): this type does not validate ``rule_kind`` /
``rule_strength`` — authoring validation is the source subsystem's job (a later
phase). A justification with an unrecognized kind is still a representable record;
filtering is never a build-time concern here.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import msgspec

from propstore.provenance import Provenance


def _normalize_attrs(
    value: Mapping[str, Any] | tuple[tuple[str, Any], ...] | None,
) -> tuple[tuple[str, Any], ...]:
    if value is None:
        return ()
    items = value.items() if isinstance(value, Mapping) else value
    return tuple(sorted((str(key), item) for key, item in items))


@dataclass(frozen=True, order=True)
class CanonicalJustification:
    """One inference licence: premises, conclusion, and rule kind/strength."""

    justification_id: str
    conclusion_claim_id: str
    premise_claim_ids: tuple[str, ...] = ()
    rule_kind: str = "reported_claim"
    rule_strength: str = "defeasible"
    provenance: Provenance | None = None
    attributes: tuple[tuple[str, Any], ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "premise_claim_ids",
            tuple(str(item) for item in self.premise_claim_ids),
        )
        object.__setattr__(self, "attributes", _normalize_attrs(self.attributes))

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "justification_id": self.justification_id,
            "conclusion_claim_id": self.conclusion_claim_id,
            "premise_claim_ids": list(self.premise_claim_ids),
            "rule_kind": self.rule_kind,
            "rule_strength": self.rule_strength,
        }
        if self.provenance is not None:
            data["provenance"] = msgspec.to_builtins(self.provenance)
        if self.attributes:
            data["attributes"] = dict(self.attributes)
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> CanonicalJustification:
        provenance_data = data.get("provenance")
        return cls(
            justification_id=str(data["justification_id"]),
            conclusion_claim_id=str(data["conclusion_claim_id"]),
            premise_claim_ids=tuple(str(item) for item in data.get("premise_claim_ids") or ()),
            rule_kind=str(data.get("rule_kind") or "reported_claim"),
            rule_strength=str(data.get("rule_strength") or "defeasible"),
            provenance=(
                None
                if provenance_data is None
                else msgspec.convert(provenance_data, Provenance)
            ),
            attributes=tuple(_normalize_attrs(data.get("attributes"))),
        )


__all__ = ["CanonicalJustification"]
