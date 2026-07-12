"""Source-origin vocabulary for authored knowledge sources.

A *source* is an external origin of authored knowledge (a paper, a manual
entry). :class:`SourceKind` names what the source is; :class:`SourceOriginType`
names how it was located. Both are closed enums — the coercers reject anything
outside the vocabulary so an authoring edge never silently invents a kind.
"""

from __future__ import annotations

from enum import StrEnum


class SourceKind(StrEnum):
    ACADEMIC_PAPER = "academic_paper"
    MAILING_LIST_MESSAGE = "mailing_list_message"


class SourceOriginType(StrEnum):
    DOI = "doi"
    FILE = "file"
    MANUAL = "manual"


VALID_SOURCE_KINDS = frozenset(kind.value for kind in SourceKind)
VALID_SOURCE_ORIGIN_TYPES = frozenset(
    origin_type.value for origin_type in SourceOriginType
)


def coerce_source_kind(value: object) -> SourceKind:
    if isinstance(value, SourceKind):
        return value
    if isinstance(value, str):
        try:
            return SourceKind(value)
        except ValueError as exc:
            raise ValueError(
                f"Unsupported source kind {value!r}. Expected one of: "
                f"{', '.join(sorted(VALID_SOURCE_KINDS))}"
            ) from exc
    raise TypeError(f"Unsupported source kind type: {type(value).__name__}")


def coerce_source_origin_type(value: object) -> SourceOriginType:
    if isinstance(value, SourceOriginType):
        return value
    if isinstance(value, str):
        try:
            return SourceOriginType(value)
        except ValueError as exc:
            raise ValueError(
                "Unsupported source origin type "
                f"{value!r}. Expected one of: "
                f"{', '.join(sorted(VALID_SOURCE_ORIGIN_TYPES))}"
            ) from exc
    raise TypeError(f"Unsupported source origin type: {type(value).__name__}")
