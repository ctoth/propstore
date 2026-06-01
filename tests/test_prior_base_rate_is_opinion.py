from __future__ import annotations

from quire.documents import convert_document_value, document_to_payload

from propstore.families.claims.types import ClaimType
from propstore.core.graph_types import ClaimNode
from propstore.core.id_types import ClaimId
from propstore.families.sources.declaration import (
    SourceDocument,
    compile_source_models,
    source_document_payload,
)
from propstore.opinion import Opinion
from propstore.praf.engine import p_arg_from_claim
from propstore.provenance import ProvenanceStatus


PRIOR_PAYLOAD = {"b": 0.2, "d": 0.1, "u": 0.7, "a": 0.4}


def test_source_document_prior_base_rate_is_opinion() -> None:
    source_doc = convert_document_value(
        _source_payload(),
        SourceDocument,
        source="source prior opinion test",
    )

    assert source_doc.trust.prior_base_rate == Opinion(**PRIOR_PAYLOAD)
    assert (
        source_document_payload(source_doc)["trust"]["prior_base_rate"] == PRIOR_PAYLOAD
    )


def test_praf_uses_prior_opinion_without_float_coercion() -> None:
    opinion = p_arg_from_claim(
        ClaimNode(
            claim_id=ClaimId("test_claim"),
            claim_type=ClaimType.OBSERVATION,
            source_prior_opinion=Opinion(**PRIOR_PAYLOAD),
        )
    )

    assert isinstance(opinion, Opinion)
    assert opinion == Opinion(**PRIOR_PAYLOAD)
