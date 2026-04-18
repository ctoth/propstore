from __future__ import annotations

from enum import StrEnum
from typing import Mapping

from quire.documents import DocumentStruct
from propstore.provenance import Provenance


class ProtoAgentProperty(StrEnum):
    VOLITION = "volition"
    SENTIENCE = "sentience"
    CAUSATION = "causation"
    MOVEMENT = "movement"
    CHANGE_OF_STATE = "change_of_state"


class ProtoPatientProperty(StrEnum):
    AFFECTED = "affected"
    INCREMENTAL_THEME = "incremental_theme"
    STATIONARY = "stationary"
    CAUSALLY_AFFECTED = "causally_affected"
    CHANGE_OF_STATE = "change_of_state"


class GradedEntailment(DocumentStruct):
    property: str
    value: float
    provenance: Provenance

    def __post_init__(self) -> None:
        if not self.property:
            raise ValueError("graded entailment requires a property")
        object.__setattr__(self, "property", str(self.property))
        if self.value < 0.0 or self.value > 1.0:
            raise ValueError("graded entailment value must be in [0, 1]")


class ProtoRoleBundle(DocumentStruct):
    proto_agent_entailments: tuple[GradedEntailment, ...] = ()
    proto_patient_entailments: tuple[GradedEntailment, ...] = ()

    def __post_init__(self) -> None:
        for entailment in self.proto_agent_entailments:
            ProtoAgentProperty(entailment.property)
        for entailment in self.proto_patient_entailments:
            ProtoPatientProperty(entailment.property)


def proto_agent_weight(bundle: ProtoRoleBundle) -> float:
    return sum(entailment.value for entailment in bundle.proto_agent_entailments)


def proto_patient_weight(bundle: ProtoRoleBundle) -> float:
    return sum(entailment.value for entailment in bundle.proto_patient_entailments)


def predicted_subject_role(role_bundles: Mapping[str, ProtoRoleBundle]) -> str | None:
    """Dowty-style ASP: greatest proto-agent weight predicts subject."""

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
