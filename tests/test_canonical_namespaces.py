"""Reserved canonical namespace guards."""

from __future__ import annotations

import pytest

from propstore.canonical_namespaces import (
    RESERVED_CANONICAL_NAMESPACES,
    ReservedNamespaceViolation,
    assert_alias_does_not_target_reserved_namespace,
    assert_namespace_not_reserved,
)


def test_reserved_set() -> None:
    assert RESERVED_CANONICAL_NAMESPACES == frozenset({"ps", "propstore"})


@pytest.mark.parametrize("namespace", ["ps", "propstore"])
def test_reserved_namespace_rejected(namespace: str) -> None:
    with pytest.raises(ReservedNamespaceViolation):
        assert_namespace_not_reserved(namespace, context="source claim")


def test_unreserved_namespace_allowed() -> None:
    assert_namespace_not_reserved("smith2020", context="source claim")


def test_alias_targeting_reserved_namespace_rejected() -> None:
    with pytest.raises(ReservedNamespaceViolation):
        assert_alias_does_not_target_reserved_namespace("ps:mass")


def test_alias_without_reserved_prefix_allowed() -> None:
    # A non-reserved namespace, and a bare alias with no namespace, both pass.
    assert_alias_does_not_target_reserved_namespace("smith2020:mass")
    assert_alias_does_not_target_reserved_namespace("mass")
