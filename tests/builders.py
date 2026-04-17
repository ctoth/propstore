from __future__ import annotations

from dataclasses import dataclass

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

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "id": self.local_id,
            "type": self.claim_type,
            "provenance": {"page": self.page},
            "context": TEST_CONTEXT_ID,
        }
        if self.statement is not None:
            payload["statement"] = self.statement
        if self.concept is not None:
            payload["concept"] = self.concept
        if self.concepts:
            payload["concepts"] = list(self.concepts)
        if self.value is not None:
            payload["value"] = self.value
        if self.unit is not None:
            payload["unit"] = self.unit
        return payload


@dataclass(frozen=True)
class SourceJustificationSpec:
    local_id: str
    conclusion: str
    premises: tuple[str, ...]
    rule_kind: str
    page: int

    def to_payload(self) -> dict[str, object]:
        return {
            "id": self.local_id,
            "conclusion": self.conclusion,
            "premises": list(self.premises),
            "rule_kind": self.rule_kind,
            "provenance": {"page": self.page},
        }


@dataclass(frozen=True)
class SourceStanceSpec:
    source_claim: str
    target: str
    stance_type: str
    note: str | None = None
    strength: str | None = None

    def to_payload(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "source_claim": self.source_claim,
            "target": self.target,
            "type": self.stance_type,
        }
        if self.note is not None:
            payload["note"] = self.note
        if self.strength is not None:
            payload["strength"] = self.strength
        return payload


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
        "justifications": [justification.to_payload() for justification in justifications],
    }


def source_stances_document(
    stances: list[SourceStanceSpec],
    *,
    paper: str = "demo",
) -> dict[str, object]:
    return {
        "source": {"paper": paper},
        "stances": [stance.to_payload() for stance in stances],
    }
