"""Reference types used by the situated assertion substrate."""

from __future__ import annotations

from dataclasses import dataclass

from propstore.core.id_types import (
    ConditionId,
    ProvenanceGraphId,
    to_condition_id,
    to_provenance_graph_id,
)

_CONDITION_ID_PREFIX = "ps:condition:"
_GRAPH_NAME_PREFIXES = ("urn:", "ni://", "http://", "https://")
_UNCONDITIONAL_ID = ConditionId("ps:condition:unconditional")
_UNCONDITIONAL_FINGERPRINT = "registry:unconditional"


@dataclass(frozen=True, order=True)
class ConditionRef:
    """Stable reference to a checked condition artifact.

    The situated-assertion substrate stores the reference and registry
    fingerprint, not authored CEL source. This keeps CEL as a frontend surface
    for later WS3 compiler work.
    """

    id: ConditionId | str
    registry_fingerprint: str

    def __post_init__(self) -> None:
        if not isinstance(self.id, str):
            raise TypeError("condition id must be a string")
        ref_id = to_condition_id(self.id.strip())
        if not str(ref_id).startswith(_CONDITION_ID_PREFIX):
            raise ValueError("condition id must start with ps:condition:")
        fingerprint = str(self.registry_fingerprint).strip()
        if fingerprint == "":
            raise ValueError("condition registry fingerprint must be non-empty")
        object.__setattr__(self, "id", ref_id)
        object.__setattr__(self, "registry_fingerprint", fingerprint)

    @classmethod
    def unconditional(cls) -> ConditionRef:
        return cls(
            id=_UNCONDITIONAL_ID,
            registry_fingerprint=_UNCONDITIONAL_FINGERPRINT,
        )

    def identity_payload(self) -> tuple[str, str, str]:
        return ("condition", str(self.id), self.registry_fingerprint)


@dataclass(frozen=True, order=True)
class ProvenanceGraphRef:
    """Stable reference to a Carroll-style named graph.

    Carroll et al. 2005 define a named graph as a URIref naming a graph. The
    assertion substrate stores that name only; graph content and trust status
    stay in the provenance carrier.
    """

    graph_name: ProvenanceGraphId | str

    def __post_init__(self) -> None:
        if not isinstance(self.graph_name, str):
            raise TypeError("provenance graph name must be a string")
        graph_name = to_provenance_graph_id(self.graph_name.strip())
        if not str(graph_name).startswith(_GRAPH_NAME_PREFIXES):
            raise ValueError("provenance graph reference must be a URI")
        object.__setattr__(self, "graph_name", graph_name)

    def identity_payload(self) -> tuple[str, str]:
        return ("provenance_graph", str(self.graph_name))


UNCONDITIONAL_CONDITION_REF = ConditionRef.unconditional()
