"""Reference types used by the situated assertion substrate."""

from __future__ import annotations

from dataclasses import dataclass

from propstore.core.conditions.checked import (
    UNCONDITIONAL_CONDITION_ID,
    UNCONDITIONAL_CONDITION_REGISTRY_FINGERPRINT,
)
from propstore.core.id_types import (
    ConditionId,
    ContextId,
    ProvenanceGraphId,
)

_CONDITION_ID_PREFIX = "ps:condition:"
_GRAPH_NAME_PREFIXES = ("urn:", "ni://", "http://", "https://")


@dataclass(frozen=True, order=True)
class ContextReference:
    """Stable context identity reference for situated assertions."""

    id: ContextId

    def __post_init__(self) -> None:
        if not isinstance(self.id, str):
            raise TypeError("context id must be a string")
        if str(self.id).strip() != str(self.id) or str(self.id) == "":
            raise ValueError("context id must be non-empty")


@dataclass(frozen=True, order=True)
class ConditionRef:
    """Stable reference to a checked condition artifact.

    The situated-assertion substrate stores the reference and registry
    fingerprint, not authored CEL source. This keeps CEL as a frontend surface
    for later WS3 compiler work.
    """

    id: ConditionId
    registry_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.id, str):
            raise TypeError("condition id must be a string")
        if str(self.id).strip() != str(self.id) or not str(self.id).startswith(
            _CONDITION_ID_PREFIX
        ):
            raise ValueError("condition id must start with ps:condition:")
        if (
            self.registry_fingerprint.strip() != self.registry_fingerprint
            or self.registry_fingerprint == ""
        ):
            raise ValueError("condition registry fingerprint must be non-empty")

    @classmethod
    def unconditional(cls) -> ConditionRef:
        return cls(
            id=UNCONDITIONAL_CONDITION_ID,
            registry_fingerprint=UNCONDITIONAL_CONDITION_REGISTRY_FINGERPRINT,
        )


@dataclass(frozen=True, order=True)
class ProvenanceGraphRef:
    """Stable reference to a Carroll-style named graph.

    Carroll et al. 2005 define a named graph as a URIref naming a graph. The
    assertion substrate stores that name only; graph content and trust status
    stay in the provenance carrier.
    """

    graph_name: ProvenanceGraphId

    def __post_init__(self) -> None:
        if not isinstance(self.graph_name, str):
            raise TypeError("provenance graph name must be a string")
        if str(self.graph_name).strip() != str(self.graph_name) or not str(
            self.graph_name
        ).startswith(_GRAPH_NAME_PREFIXES):
            raise ValueError("provenance graph reference must be a URI")


UNCONDITIONAL_CONDITION_REF = ConditionRef.unconditional()
