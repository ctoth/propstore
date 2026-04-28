"""Canonical namespace reservations for source-local boundary checks.

Source-local input cannot mint into reserved canonical namespaces. Aliases
cannot collide with reserved canonical namespaces. Both rules are enforced
at the IO boundary.
"""

from __future__ import annotations


RESERVED_CANONICAL_NAMESPACES: frozenset[str] = frozenset({"ps", "propstore"})


class ReservedNamespaceViolation(ValueError):
    """Raised when source-local input attempts to mint a canonical namespace."""


def assert_namespace_not_reserved(namespace: str, *, context: str) -> None:
    if namespace in RESERVED_CANONICAL_NAMESPACES:
        raise ReservedNamespaceViolation(
            f"{context} cannot use reserved canonical namespace {namespace!r}"
        )


def assert_alias_does_not_target_reserved_namespace(alias: str) -> None:
    prefix, separator, _rest = alias.partition(":")
    if separator:
        assert_namespace_not_reserved(prefix, context="concept alias")
