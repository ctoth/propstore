from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from propstore.merge.merge_claims import MergeClaim


@dataclass(frozen=True)
class ProvenanceWitness:
    source_artifact_id: str
    source_paper: str | None
    source_page: int | None
    branch_origin: str | None
    rule_chain: tuple[str, ...] = ()

    @classmethod
    def from_merge_claim(cls, claim: MergeClaim) -> ProvenanceWitness:
        provenance = claim.provenance_payload()
        page = provenance.get("page")
        return cls(
            source_artifact_id=claim.artifact_id,
            source_paper=_optional_string(provenance.get("paper")),
            source_page=page if isinstance(page, int) else None,
            branch_origin=_optional_string(provenance.get("branch_origin")),
        )

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"source_artifact_id": self.source_artifact_id}
        if self.source_paper is not None:
            payload["source_paper"] = self.source_paper
        if self.source_page is not None:
            payload["source_page"] = self.source_page
        if self.branch_origin is not None:
            payload["branch_origin"] = self.branch_origin
        if self.rule_chain:
            payload["rule_chain"] = list(self.rule_chain)
        return payload


def _optional_string(value: object) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None
