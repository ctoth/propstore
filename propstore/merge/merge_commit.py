"""Merge commit creation for propstore knowledge repositories."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING


from propstore.merge.merge_classifier import MergeArgument

if TYPE_CHECKING:
    pass


@dataclass(frozen=True)
class NonClaimMergeConflict(RuntimeError):
    path: str
    family: str
    left_sha: str
    right_sha: str

    def __str__(self) -> str:
        return (
            f"non-claim merge conflict at {self.path!r} in family {self.family!r}: "
            f"{self.left_sha} != {self.right_sha}"
        )


def _safe_ref_part(value: str) -> str:
    safe = "".join(character if character.isalnum() else "_" for character in value)
    return safe.strip("_") or "branch"


def _family_for_path(path: str) -> str:
    return path.replace("\\", "/").split("/", 1)[0]
