from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Generic, TypeVar


RefT = TypeVar("RefT")


@dataclass(frozen=True)
class ProposalPromotionItem(Generic[RefT]):
    ref: RefT
    artifact_id: str
    source_relpath: str
    target_path: Path
    filename: str
    source_claim: str = ""
    source_paper: str = ""
    rule_id: str = ""
    predicate_id: str = ""


@dataclass(frozen=True)
class ProposalPromotionPlan(Generic[RefT]):
    branch: str
    proposal_tip: str | None
    items: tuple[ProposalPromotionItem[RefT], ...]

    @property
    def has_branch(self) -> bool:
        return self.proposal_tip is not None


@dataclass(frozen=True)
class ProposalPromotionResult(Generic[RefT]):
    moved: int
    branch: str
    promoted_items: tuple[ProposalPromotionItem[RefT], ...]


class UnknownProposalPath(ValueError):
    def __init__(self, requested_path: str, available_filenames: tuple[str, ...]) -> None:
        self.requested_path = requested_path
        self.available_filenames = available_filenames
        available = ", ".join(available_filenames) if available_filenames else "<none>"
        super().__init__(
            f"Unknown proposal path {requested_path!r}; available: {available}"
        )


class ProposalAlreadyPromoted(ValueError):
    def __init__(self, artifact_id: str, promoted_from_sha: str) -> None:
        self.artifact_id = artifact_id
        self.promoted_from_sha = promoted_from_sha
        super().__init__(
            f"Proposal {artifact_id!r} was already promoted from {promoted_from_sha}"
        )
