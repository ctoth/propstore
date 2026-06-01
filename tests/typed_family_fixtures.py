from __future__ import annotations


from propstore.provenance import Provenance, ProvenanceStatus

_CLAIM_GRAPH_METADATA_KEYS = ()


def _test_provenance(operation: str) -> Provenance:
    return Provenance(
        status=ProvenanceStatus.STATED,
        witnesses=(),
        operations=(operation,),
    )
