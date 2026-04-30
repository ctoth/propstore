"""Trusty-URI byte primitives for provenance identities.

Kuhn and Dumontier 2014 describe artifact codes as verifiable identifiers;
propstore's current provenance boundary uses the RFC 6920 ``ni`` form as the
byte-level hash carrier and emits only SHA-256 identifiers.
"""

from __future__ import annotations

from propstore.uri import compute_ni_uri as _compute_ni_uri
from propstore.uri import verify_ni_uri as _verify_ni_uri


def compute_ni_uri(content: bytes, *, algorithm: str = "sha-256") -> str:
    return _compute_ni_uri(content, algorithm=algorithm)


def verify_ni_uri(uri: str, content: bytes) -> bool:
    return _verify_ni_uri(uri, content)
