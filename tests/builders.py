from __future__ import annotations

from dataclasses import dataclass

from quire.documents import document_to_payload

from tests.conftest import TEST_CONTEXT_ID


@dataclass(frozen=True)
class SourceClaimSpec:
    local_id: str
    claim_type: str
    page: int
    statement: str | None = None
    concept: str | None = None
    concepts: tuple[str, ...] = ()
    value: float | None = None
    unit: str | None = None


@dataclass(frozen=True)
class SourceJustificationSpec:
    local_id: str
    conclusion: str
    premises: tuple[str, ...]
    rule_kind: str
    page: int


@dataclass(frozen=True)
class SourceStanceSpec:
    source_claim: str
    target: str
    stance_type: str
    note: str | None = None
    strength: str | None = None


def source_claims_document(
    claims: list[SourceClaimSpec],
    *,
    paper: str = "demo",
) -> dict[str, object]:
    return {
        "source": {"paper": paper},
        "claims": [claim.to_payload() for claim in claims],
    }


def source_justifications_document(
    justifications: list[SourceJustificationSpec],
    *,
    paper: str = "demo",
) -> dict[str, object]:
    return {
        "source": {"paper": paper},
        "justifications": [
            justification.to_payload() for justification in justifications
        ],
    }


def source_stances_document(
    stances: list[SourceStanceSpec],
    *,
    paper: str = "demo",
) -> dict[str, object]:
    return {
        "source": {"paper": paper},
        "stances": [document_to_payload(stance) for stance in stances],
    }
