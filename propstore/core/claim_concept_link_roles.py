from __future__ import annotations

from enum import StrEnum


class ClaimConceptLinkRole(StrEnum):
    ABOUT = "about"
    OUTPUT = "output"
    TARGET = "target"
    INPUT = "input"


def coerce_claim_concept_link_role(
    value: object | None,
) -> ClaimConceptLinkRole | None:
    if value is None:
        return None
    return ClaimConceptLinkRole(str(value))
