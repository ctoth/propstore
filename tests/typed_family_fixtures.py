from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from propstore.families.claims.types import ClaimType
from propstore.core.graph_types import ClaimNode
from propstore.families.claims.graph import claim_node_from_claim
from propstore.families.claims.declaration import (
    Claim,
    ClaimAlgorithmPayload,
    ClaimNumericPayload,
    ClaimTextPayload,
)
from propstore.families.relations.declaration import Stance
from propstore.opinion import Opinion
from propstore.provenance import Provenance, ProvenanceStatus

_CLAIM_GRAPH_METADATA_KEYS = ()


def _test_provenance(operation: str) -> Provenance:
    return Provenance(
        status=ProvenanceStatus.STATED,
        witnesses=(),
        operations=(operation,),
    )
