from __future__ import annotations

import pytest

from propstore.canonical_namespaces import (
    RESERVED_CANONICAL_NAMESPACES,
    ReservedNamespaceViolation,
    assert_alias_does_not_target_reserved_namespace,
)
from propstore.families.claims.lifecycle import normalize_source_claims_payload
from propstore.families.claims.declaration import SourceClaimDocument


@pytest.mark.parametrize("alias", ["ps:concept:42", "propstore:concept42"])
def test_alias_targets_cannot_use_reserved_namespaces(alias: str) -> None:
    with pytest.raises(ReservedNamespaceViolation):
        assert_alias_does_not_target_reserved_namespace(alias)


def test_alias_targets_accept_unreserved_namespaces() -> None:
    assert_alias_does_not_target_reserved_namespace("mypaper:concept:42")
