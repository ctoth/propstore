from __future__ import annotations

import pytest

from propstore.canonical_namespaces import (
    RESERVED_CANONICAL_NAMESPACES,
    ReservedNamespaceViolation,
    assert_alias_does_not_target_reserved_namespace,
)
from propstore.families.documents.sources import SourceClaimDocument, SourceClaimsDocument
from propstore.source.claims import normalize_source_claims_payload


@pytest.mark.parametrize("namespace", sorted(RESERVED_CANONICAL_NAMESPACES))
def test_source_claim_writer_rejects_reserved_namespaces(namespace: str) -> None:
    payload = SourceClaimsDocument(
        claims=(SourceClaimDocument(id="c1", statement="example claim"),)
    )

    with pytest.raises(ReservedNamespaceViolation):
        normalize_source_claims_payload(
            payload,
            source_uri="tag:example.com,2026:source/example",
            source_namespace=namespace,
        )


def test_source_claim_writer_accepts_unreserved_namespace() -> None:
    payload = SourceClaimsDocument(
        claims=(SourceClaimDocument(id="c1", statement="example claim"),)
    )

    normalized, mapping = normalize_source_claims_payload(
        payload,
        source_uri="tag:example.com,2026:source/example",
        source_namespace="mypaper",
    )

    assert mapping == {"c1": normalized.claims[0].id}
    assert {logical_id.namespace for logical_id in normalized.claims[0].logical_ids} == {
        "mypaper"
    }


@pytest.mark.parametrize("alias", ["ps:concept:42", "propstore:concept42"])
def test_alias_targets_cannot_use_reserved_namespaces(alias: str) -> None:
    with pytest.raises(ReservedNamespaceViolation):
        assert_alias_does_not_target_reserved_namespace(alias)


def test_alias_targets_accept_unreserved_namespaces() -> None:
    assert_alias_does_not_target_reserved_namespace("mypaper:concept:42")
