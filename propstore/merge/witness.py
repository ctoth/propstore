from __future__ import annotations

from dataclasses import dataclass

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
        return cls(
            source_artifact_id=claim.artifact_id,
            source_paper=claim.source_paper,
            source_page=claim.source_page,
            branch_origin=claim.branch_origin,
        )
