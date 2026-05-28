from __future__ import annotations

from pathlib import Path
from typing import Any

import msgspec.yaml
import pytest
from quire.documents import convert_document_value, document_to_payload

from propstore.families.claims.declaration import ClaimDocument, SourceClaimDocument


FIXTURE_ROOT = Path(__file__).parent / "data" / "claim_roundtrip"

FIXTURES: tuple[tuple[str, type[Any], frozenset[str]], ...] = (
    (
        "canonical_numeric_measurement.yaml",
        ClaimDocument,
        frozenset({"numeric"}),
    ),
    (
        "canonical_text_observation.yaml",
        ClaimDocument,
        frozenset({"text", "concept-link"}),
    ),
    (
        "canonical_algorithm.yaml",
        ClaimDocument,
        frozenset({"algorithm", "concept-link"}),
    ),
    (
        "canonical_concept_link_equation.yaml",
        ClaimDocument,
        frozenset({"concept-link"}),
    ),
    (
        "canonical_contextual_ist.yaml",
        ClaimDocument,
        frozenset({"contextual"}),
    ),
    (
        "source_local_claim.yaml",
        SourceClaimDocument,
        frozenset({"source-local", "numeric"}),
    ),
)


def _load_fixture(filename: str, document_type: type[Any]) -> Any:
    path = FIXTURE_ROOT / filename
    payload = msgspec.yaml.decode(path.read_bytes(), type=dict[str, Any], strict=True)
    return convert_document_value(
        payload,
        document_type,
        source=path.relative_to(FIXTURE_ROOT.parent.parent).as_posix(),
    )


@pytest.mark.parametrize(("filename", "document_type", "_shape_tags"), FIXTURES)
def test_claim_yaml_fixture_round_trips(
    filename: str,
    document_type: type[Any],
    _shape_tags: frozenset[str],
) -> None:
    document = _load_fixture(filename, document_type)

    reparsed_payload = convert_document_value(
        document_to_payload(document),
        document_type,
        source=f"{filename}:payload-roundtrip",
    )
    assert reparsed_payload == document

    encoded = msgspec.yaml.encode(document)
    reparsed_yaml = convert_document_value(
        msgspec.yaml.decode(encoded),
        document_type,
        source=f"{filename}:yaml-roundtrip",
    )
    assert reparsed_yaml == document


def test_claim_yaml_fixture_set_covers_phase_4_precondition_shapes() -> None:
    observed = frozenset().union(*(shape_tags for _, _, shape_tags in FIXTURES))

    assert observed >= {
        "numeric",
        "text",
        "algorithm",
        "concept-link",
        "source-local",
        "contextual",
    }
    assert len(FIXTURES) >= 5
