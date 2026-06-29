"""Semantic ID newtypes for the value/honesty layer.

These are ``NewType`` brands over ``str`` so the type checker keeps a situated
*assertion* identity distinct from a bare string without introducing a runtime
wrapper. Only the identities the Phase-5a value layer needs live here; the wider
id family is grown by later phases as their callers arrive.
"""

from __future__ import annotations

from typing import NewType

AssertionId = NewType("AssertionId", str)


def to_assertion_id(value: object) -> AssertionId:
    """Brand an arbitrary value's string form as an :data:`AssertionId`."""

    return AssertionId(str(value))
