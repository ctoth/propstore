from __future__ import annotations

from enum import StrEnum


class ConceptStatus(StrEnum):
    ACCEPTED = "accepted"
    DEPRECATED = "deprecated"
    PROPOSED = "proposed"


VALID_CONCEPT_STATUSES = frozenset(status.value for status in ConceptStatus)
_CONCEPT_STATUS_ALIASES = {
    "active": ConceptStatus.ACCEPTED,
}


def coerce_concept_status(value: object) -> ConceptStatus:
    if isinstance(value, ConceptStatus):
        return value
    if isinstance(value, str):
        if value in _CONCEPT_STATUS_ALIASES:
            return _CONCEPT_STATUS_ALIASES[value]
        try:
            return ConceptStatus(value)
        except ValueError as exc:
            raise ValueError(
                "Unsupported concept status "
                f"{value!r}. Expected one of: {', '.join(sorted(VALID_CONCEPT_STATUSES))}"
            ) from exc
    raise TypeError(f"Unsupported concept status type: {type(value).__name__}")
