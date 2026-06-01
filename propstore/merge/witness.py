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
