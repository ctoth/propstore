"""RFC 4151 tagging-entity validation for propstore tag URIs.

A *tagging authority* is the ``authorityName,date`` half of an RFC 4151 ``tag:``
URI (Kindberg & Hawke 2005). propstore mints stable, human-meaningful identifiers
for concepts and sources as tag URIs; this module is the one canonical spelling of
the authority and its parser, so every URI helper validates against the same form.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

_AUTHORITY_RE = re.compile(
    r"^(?P<name>[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?"
    r"(?:@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?)?),"
    r"(?P<date>[0-9]{4}(?:-[0-9]{2}(?:-[0-9]{2})?)?)$"
)


class MalformedTaggingAuthority(ValueError):
    """Raised when an RFC 4151 tagging entity is malformed."""


@dataclass(frozen=True)
class TaggingAuthority:
    """A validated RFC 4151 tagging entity (``authorityName,date``)."""

    value: str

    def __str__(self) -> str:
        return self.value


def parse_tagging_authority(value: str | TaggingAuthority) -> TaggingAuthority:
    """Return ``value`` as a validated :class:`TaggingAuthority`.

    Accepts an already-parsed authority unchanged so callers can pass either a raw
    string or a :class:`TaggingAuthority` interchangeably.
    """

    if isinstance(value, TaggingAuthority):
        return value
    if len(value) > 255 or _AUTHORITY_RE.fullmatch(value) is None:
        raise MalformedTaggingAuthority(
            "tagging authority must match RFC 4151 tagging entity form "
            "'authorityName,date'"
        )
    return TaggingAuthority(value)
