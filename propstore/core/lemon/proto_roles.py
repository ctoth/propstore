"""Dowty graded proto-role bundles for participant slots and senses.

Dowty (1991) replaces discrete thematic roles with two *proto-roles* whose
contributing entailments are matters of degree. A :class:`ProtoRoleBundle`
collects graded, provenance-bearing proto-agent and proto-patient entailments;
:func:`predicted_subject_role` implements Dowty's Argument Selection Principle —
the participant accumulating the greatest proto-agent weight is realized as
subject (with no prediction on a tie).

Grades are bounded to ``[0, 1]`` and every entailment REQUIRES provenance, in
keeping with the honest-ignorance discipline.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum

import msgspec

from propstore.provenance import Provenance


class ProtoAgentProperty(StrEnum):
    """Dowty's contributing proto-agent properties (1991, list 27, p.572)."""

    VOLITION = "volition"
    SENTIENCE = "sentience"
    CAUSATION = "causation"
    MOVEMENT = "movement"
    INDEPENDENT_EXISTENCE = "independent_existence"


class ProtoPatientProperty(StrEnum):
    """Dowty's contributing proto-patient properties (1991, list 28, p.572)."""

    CHANGE_OF_STATE = "change_of_state"
    INCREMENTAL_THEME = "incremental_theme"
    CAUSALLY_AFFECTED = "causally_affected"
    STATIONARY = "stationary"
    NONEXISTENCE = "nonexistence"


class GradedEntailment(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """A single graded proto-role entailment in ``[0, 1]`` with provenance."""

    property: str
    value: float
    provenance: Provenance

    def __post_init__(self) -> None:
        if not self.property:
            raise ValueError("graded entailment requires a property")
        object.__setattr__(self, "property", str(self.property))
        if self.value < 0.0 or self.value > 1.0:
            raise ValueError("graded entailment value must be in [0, 1]")


class ProtoRoleBundle(msgspec.Struct, frozen=True, forbid_unknown_fields=True):
    """A participant's graded proto-agent and proto-patient entailments."""

    proto_agent_entailments: tuple[GradedEntailment, ...] = ()
    proto_patient_entailments: tuple[GradedEntailment, ...] = ()

    def __post_init__(self) -> None:
        for entailment in self.proto_agent_entailments:
            ProtoAgentProperty(entailment.property)
        for entailment in self.proto_patient_entailments:
            ProtoPatientProperty(entailment.property)


def proto_agent_weight(bundle: ProtoRoleBundle) -> float:
    """Sum of a bundle's proto-agent entailment grades."""

    return sum(entailment.value for entailment in bundle.proto_agent_entailments)


def proto_patient_weight(bundle: ProtoRoleBundle) -> float:
    """Sum of a bundle's proto-patient entailment grades."""

    return sum(entailment.value for entailment in bundle.proto_patient_entailments)


def predicted_subject_role(role_bundles: Mapping[str, ProtoRoleBundle]) -> str | None:
    """Dowty's Argument Selection: greatest proto-agent weight predicts subject.

    Returns ``None`` for an empty mapping or a tie on the maximum weight.
    """

    if not role_bundles:
        return None
    weights = {
        role_name: proto_agent_weight(bundle)
        for role_name, bundle in role_bundles.items()
    }
    best_role, best_weight = max(weights.items(), key=lambda item: item[1])
    if list(weights.values()).count(best_weight) > 1:
        return None
    return best_role
