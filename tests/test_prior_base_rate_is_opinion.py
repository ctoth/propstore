from __future__ import annotations

import json

from quire.documents import convert_document_value

from propstore.core.claim_values import SourceTrust
from propstore.families.documents.sources import SourceDocument
from propstore.opinion import Opinion
from propstore.praf.engine import p_arg_from_claim
from propstore.provenance import ProvenanceStatus
from propstore.sidecar.passes import compile_source_sidecar_rows


PRIOR_PAYLOAD = {"b": 0.2, "d": 0.1, "u": 0.7, "a": 0.4}


def _source_payload() -> dict:
    return {
        "id": "tag:example.test,2026:source/demo",
        "kind": "academic_paper",
        "origin": {"type": "doi", "value": "10.0000/example"},
        "trust": {
            "status": ProvenanceStatus.STATED.value,
            "prior_base_rate": PRIOR_PAYLOAD,
            "derived_from": ["rule:demo"],
        },
        "metadata": {"name": "demo"},
    }


def test_source_document_prior_base_rate_is_opinion() -> None:
    source_doc = convert_document_value(
        _source_payload(),
        SourceDocument,
        source="source prior opinion test",
    )

    assert source_doc.trust.prior_base_rate == Opinion(**PRIOR_PAYLOAD)
    assert source_doc.to_payload()["trust"]["prior_base_rate"] == PRIOR_PAYLOAD


def test_source_sidecar_serializes_prior_base_rate_as_opinion_json() -> None:
    source_doc = convert_document_value(
        _source_payload(),
        SourceDocument,
        source="source prior sidecar test",
    )

    rows = compile_source_sidecar_rows([("demo", source_doc)])
    prior_json = rows.source_rows[0].values[7]

    assert isinstance(prior_json, str)
    assert json.loads(prior_json) == PRIOR_PAYLOAD


def test_claim_row_source_trust_round_trips_prior_opinion() -> None:
    trust = SourceTrust.from_mapping(
        {
            "prior_base_rate": json.dumps(PRIOR_PAYLOAD),
            "derived_from": json.dumps(["rule:demo"]),
        }
    )

    assert trust is not None
    assert trust.prior_base_rate == Opinion(**PRIOR_PAYLOAD)
    assert trust.to_dict()["prior_base_rate"] == PRIOR_PAYLOAD


def test_praf_uses_prior_opinion_without_float_coercion() -> None:
    opinion = p_arg_from_claim(
        {
            "source": {
                "trust": {
                    "prior_base_rate": PRIOR_PAYLOAD,
                }
            }
        }
    )

    assert isinstance(opinion, Opinion)
    assert opinion == Opinion(**PRIOR_PAYLOAD)
