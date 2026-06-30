"""Reserved canonical namespaces.

The ``ps`` / ``propstore`` namespaces are reserved for canonical, store-minted
identities (``ps:claim:…``, ``ps:concept:…``). Source-local authoring input may
never mint into them: a source branch proposes handles in its own namespace and
the canonical identity is assigned only at promote time. These guards enforce
that boundary at the authoring edge.
"""

from __future__ import annotations

RESERVED_CANONICAL_NAMESPACES: frozenset[str] = frozenset({"ps", "propstore"})


class ReservedNamespaceViolation(ValueError):
    """Raised when source-local input attempts to mint a canonical namespace."""


def assert_namespace_not_reserved(namespace: str, *, context: str) -> None:
    """Reject *namespace* if it is a reserved canonical namespace."""

    if namespace in RESERVED_CANONICAL_NAMESPACES:
        raise ReservedNamespaceViolation(
            f"{context} cannot use reserved canonical namespace {namespace!r}"
        )


def assert_alias_does_not_target_reserved_namespace(alias: str) -> None:
    """Reject a ``namespace:value`` alias whose namespace is reserved."""

    prefix, separator, _rest = alias.partition(":")
    if separator:
        assert_namespace_not_reserved(prefix, context="concept alias")
