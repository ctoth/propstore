"""Trusty-URI byte primitives for provenance identities.

Kuhn and Dumontier 2014 describe artifact codes as verifiable identifiers;
propstore's current provenance boundary uses the RFC 6920 ``ni`` form as the
byte-level hash carrier and emits only SHA-256 identifiers.
"""

from __future__ import annotations
